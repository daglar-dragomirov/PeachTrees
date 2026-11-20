"""PeachTrees 1.0 - the frozen selection layer (docs/FABLE-ANALYSIS-RESULT-20261119.md, section 7), label-free.

Forms (unchanged): R = the optimizer's program, A = "assembled" (R's draft + ReAct reviewer), L = "liquid" (ReAct agent).
Item rule pi1: 1. drop forms without a parsable output; 2. task checker (if any) drops failing forms, all kept if all
fail; 3. if >= 2 surviving forms share the task-canonical answer key, return it; 4. else A, then R, then L.
Task rule: d = mean over S of score(pi1) - score(R), se clustered; use pi1 iff d + 1.0 se >= 0, else R.
"lite": A with liveness and checker fallback (no L, no separate R call), same task rule.
The answer keys and checkers are the task scorers' own normalisers and the tasks' own tools (no gold field is read);
the helper functions are the ones of the Fable analysis (features.py), unchanged."""
import datetime, hashlib, json, math, random, re

FORMS = ("rigid", "liquid", "assembled")
PRIO = ("assembled", "rigid", "liquid")
HIDDEN = ("check",)


# ---------------------------------------------------------------- answer keys (task-canonical, never gold)
def ukey(tr):
    o = next((tr[k] for k in ("answer", "response") if tr.get(k) not in (None, "")), None)
    o = json.dumps({k: v for k, v in tr.items() if k not in HIDDEN}, sort_keys=True, ensure_ascii=False) if o is None else str(o)
    o = re.sub(r"[^\w\s]", " ", o.lower())
    o = re.sub(r"\b(a|an|the)\b", " ", o)
    return " ".join(o.split())


def math_norm(a):
    s = str(a or "").strip()
    m = re.findall(r"\\boxed\{(.*)\}", s)
    if m:
        s = m[-1]
    s = s.replace("$", "").replace("\\left", "").replace("\\right", "").replace("\\!", "").replace(" ", "").strip().rstrip(".")
    s = re.sub(r"\\[dt]?frac", r"\\frac", s)
    if re.fullmatch(r"-?\d+", s):
        s = str(int(s))
    return s.lower()


def gpqa_letter(a):
    s = str(a or "").strip()
    s = re.sub(r"^(final\s+)?answer\s*[:=]?\s*", "", s, flags=re.I)
    m = re.match(r"^[\s(\[*]*([ABCD])(?:[\s).\]:*]|$)", s)
    return m.group(1) if m else None


def th_norm(s):
    s = str(s or "").strip().lower()
    s = re.sub(r"[^\w\s\.\-:/]", " ", s)
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    s = " ".join(s.split()).strip(" .")
    try:
        return "num:%.6f" % float(s.replace(",", ""))
    except ValueError:
        return s


def np_trip_parse(response):
    pattern_visit, pattern_flight = r"\d+-\d+", r".*Day (\d+).*from (\w+) to (\w+)"
    pattern_days = r"European cities for (\d+) days"
    days, flights, flight_days = [], [], []
    total_days = None
    for piece in response.split("\n"):
        days_match = re.findall(pattern_days, piece)
        if days_match:
            total_days = int(days_match[0])
        visit_match = re.findall(pattern_visit, piece)
        if visit_match:
            days.append(visit_match[0])
            end_day = int(visit_match[0].split("-")[1])
            if end_day == total_days:
                break
        flight_match = re.findall(pattern_flight, piece)
        if flight_match:
            flights.append(flight_match[0])
    visit_cities, parsed_plan = [], []
    for flight_day, begin_city, end_city in flights:
        flight_days.append(int(flight_day))
        if not visit_cities:
            visit_cities.append(begin_city)
            visit_cities.append(end_city)
        else:
            visit_cities.append(end_city)
    if not days or not flights or not visit_cities:
        return []
    last_day = int(days[-1].split("-")[1])
    flight_days = [1] + flight_days + [last_day]
    for i, visit_city in enumerate(visit_cities):
        parsed_plan.append((visit_city, flight_days[i + 1] - flight_days[i] + 1))
    return parsed_plan


def trip_spec(prompt):
    t = prompt[prompt.rfind("TASK:"):]
    total = int(re.search(r"for (\d+) days in total", t).group(1))
    stays = {}
    for pat in (r"stay in (\w+) for (\d+) days", r"visit (\w+) for (\d+) days"):
        for c, k in re.findall(pat, t):
            stays[c] = int(k)
    for k, c in re.findall(r"spend (\d+) days in (\w+)", t):
        stays[c] = int(k)
    events = []
    for sent in re.split(r"(?<=[.!?])\s+", t):
        m = re.search(r"in (\w+) between day (\d+) and day (\d+)", sent)
        if m:
            events.append((m.group(1), int(m.group(2)), int(m.group(3))))
        m = re.search(r"[Ff]rom day (\d+) to day (\d+).* in (\w+)", sent)
        if m:
            events.append((m.group(3), int(m.group(1)), int(m.group(2))))
    fl = t[t.find("direct flights:"):]
    fl = fl[:fl.find("\n\n")] if "\n\n" in fl else fl
    edges = set()
    for a, b in re.findall(r"from (\w+) to (\w+)", fl):
        edges.add((a, b))
    for a, b in re.findall(r"(\w+) and (\w+)", fl):
        edges.add((a, b))
        edges.add((b, a))
    return total, stays, events, edges


def trip_valid(prompt, text):
    try:
        total, stays, events, edges = trip_spec(prompt)
        plan = np_trip_parse(text)
        if not plan:
            return 0
        cities = [c for c, _ in plan]
        if sorted(cities) != sorted(stays) or len(set(cities)) != len(cities):
            return 0
        if any(stays[c] != d for c, d in plan):
            return 0
        if any((cities[i], cities[i + 1]) not in edges for i in range(len(cities) - 1)):
            return 0
        day, span = 1, {}
        for c, d in plan:
            span[c] = (day, day + d - 1)
            day = day + d - 1
        if day != total:
            return 0
        for c, a, b in events:
            if c not in span:
                return 0
            s, e = span[c]
            if not ((s <= a and b <= e) or (a <= s and e <= b)):
                return 0
        return 1
    except Exception:
        return None


def meet_steps(plan):
    prefix = "SOLUTION:"
    if prefix in plan:
        plan = plan[plan.find(prefix) + len(prefix):].strip()
    return [s.strip() for s in plan.split(".") if s.strip()]


def meet_valid(plan, constraints, dist_matrix):
    t = lambda s: datetime.datetime.strptime(s, "%I:%M%p")
    start_location, initial_time = constraints[0]
    cons = {}
    for name, location, times, meeting_time in constraints[1:]:
        cons[name] = {"location": location, "start_time": t(times.split("to")[0].strip()),
                      "end_time": t(times.split("to")[1].strip()), "meeting_time": meeting_time}
    met_with, score, cur_location, cur_time, clean = {}, 0, start_location, t(initial_time), 1
    for step in plan:
        try:
            if step.startswith("You start"):
                continue
            elif step.startswith("You travel"):
                destination = step.split("travel to ")[1].split(" in")[0].strip()
                cur_time = cur_time + datetime.timedelta(minutes=dist_matrix[cur_location][destination])
                cur_location = destination
            elif step.startswith("You wait"):
                end_time = t(step.split("wait until ")[1].split(".")[0].strip())
                if end_time <= cur_time:
                    raise ValueError
                cur_time = end_time
            elif step.startswith("You meet"):
                person = step.split("meet ")[1].split(" for")[0].strip()
                if person in met_with:
                    raise ValueError
                met_with[person] = 1
                new_time = cur_time + datetime.timedelta(minutes=cons[person]["meeting_time"])
                if cur_location == cons[person]["location"] and cur_time >= cons[person]["start_time"] and new_time <= cons[person]["end_time"]:
                    score += 1
                    cur_time = new_time
                else:
                    raise ValueError
            else:
                raise ValueError
        except (ValueError, KeyError, IndexError):
            clean = 0
            break
    return score, clean


def answer_key(ds, x, task_row=None, bird_exec=None):
    """Task-canonical key of a saved row; None = no comparable answer (a BIRD query that does not run)."""
    tr = x.get("trajectory") or {}
    ans = tr.get("answer")
    if ds in ("aime", "livebench"):
        k = "m:" + math_norm(ans)
    elif ds == "gpqa":
        k = "g:" + str(gpqa_letter(ans) or ukey({"answer": ans}))
    elif ds == "toolhop":
        k = "t:" + th_norm(ans)
    elif ds == "natplan":
        if task_row and task_row["task"] == "trip":
            p = np_trip_parse(str(ans or ""))
            k = "trip:" + (repr(p) if p else ukey({"answer": ans}))
        else:
            k = "meet:" + "|".join(" ".join(s.split()).lower() for s in meet_steps(str(ans or "")))
    elif ds == "bird":
        if bird_exec is None:
            k = "u:" + ukey({"answer": ans})
        elif not bird_exec.get("ok"):
            return None
        else:
            k = "h:" + bird_exec["h"]
    elif ds == "bfcl":
        k = "b:" + json.dumps(tr.get("decoded"), sort_keys=True)
    else:
        k = "u:" + ukey(tr)
    return hashlib.sha1(k.encode("utf-8", "replace")).hexdigest()[:12]


# ---------------------------------------------------------------- the item rule
def item_view(ds, rows, task_row=None, bird=None):
    """rows: {form: saved row}. Returns {alive, keys, checker} (label-free)."""
    v = {"alive": [], "k": {}, "valid": {}, "pub": {}}
    for f in FORMS:
        x = rows.get(f)
        if x is None or x.get("error") or not x.get("trajectory"):
            continue
        k = answer_key(ds, x, task_row, (bird or {}).get(f))
        if k is None:
            continue
        v["alive"].append(f)
        v["k"][f] = k
        tr = x["trajectory"]
        if ds == "natplan" and task_row is not None:
            ans = str(tr.get("answer") or "")
            if task_row["task"] == "trip":
                v["valid"][f] = trip_valid(task_row["prompt"], ans)
            else:
                n, clean = meet_valid(meet_steps(ans), task_row["constraints"], task_row["dist_matrix"])
                v["valid"][f] = n if clean else n - 0.5
            v["task"] = task_row["task"]
        if ds == "lcb" and f != "rigid":
            m = re.findall(r'"all_public_tests_passed":\s*(true|false)', str(tr.get("reasoning") or ""))
            v["pub"][f] = None if not m else int(m[-1] == "true")
    return v


def checked(v):
    alive = v["alive"]
    keep = alive
    if v["valid"]:
        if v.get("task") == "trip":
            keep = [f for f in alive if v["valid"].get(f) != 0]
        else:
            mx = max((x for x in v["valid"].values() if x is not None), default=None)
            keep = [f for f in alive if v["valid"].get(f) is None or v["valid"][f] == mx]
    elif v["pub"]:
        keep = [f for f in alive if v["pub"].get(f) != 0]
    return keep or alive


def live(alive, f):
    if f in alive or not alive:
        return f
    return next(x for x in PRIO if x in alive)


def pi1(v, groups=None):
    """The full item rule; groups overrides the keys (tau2: the worker's own groups)."""
    alive = checked(v)
    if groups is None:
        g = {}
        for f in alive:
            g.setdefault(v["k"][f], []).append(f)
        groups = list(g.values())
    g = [[f for f in grp if f in alive] for grp in groups]
    g = [x for x in g if x]
    big = max(g, key=len) if g else []
    if len(big) >= 2:
        return "assembled" if "assembled" in big else big[0]
    return live(alive, "assembled")


def lite(v):
    return live(checked(v), "assembled")


# ---------------------------------------------------------------- the task rule and statistics
def cluster(uid):
    return uid.rsplit(":", 1)[0] if uid.startswith("aime25:") else uid  # AIME DEV = problems x repeats


def paired(deltas):
    """[(uid, delta)] -> clustered mean and se."""
    by = {}
    for u, d in deltas:
        by.setdefault(cluster(u), []).append(d)
    n = sum(len(v) for v in by.values())
    m = sum(sum(v) for v in by.values()) / n
    K = len(by)
    if K < 2:
        return m, 0.0
    var = sum((sum(v) - m * len(v)) ** 2 for v in by.values()) * K / (K - 1) / n ** 2
    return m, math.sqrt(var)


def ni_use(deltas, z=1.0):
    m, se = paired(deltas)
    return m + z * se >= 0, m, se


def boot_ci(deltas, seed=11, n=2000):
    by = {}
    for u, d in deltas:
        by.setdefault(cluster(u), []).append(d)
    sums = [(sum(v), len(v)) for v in by.values()]
    rng, K, ms = random.Random(seed), len(sums), []
    for _ in range(n):
        s = c = 0
        for _ in range(K):
            a, b = sums[rng.randrange(K)]
            s += a
            c += b
        ms.append(s / c)
    ms.sort()
    return ms[int(0.025 * n)], ms[min(n - 1, int(0.975 * n))]
