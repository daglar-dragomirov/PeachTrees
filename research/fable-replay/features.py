"""Fable analysis: label-free per-item features from the SAVED form outputs (no model calls, gold never used):
task-aware answer keys (for agreement), liveness, 'assembled changed its draft', NATURAL PLAN constraint validity
(parsed from the problem statement only), LCB public-test evidence found in the agents' own trajectories.
Writes /tmp/fable_out/feats.json : {cell_name: {role: {uid: {...}}}}."""
import datetime, glob, json, os, re, sys
sys.path.insert(0, "/tmp/fable_out")
from fa_lib import CELLS
LR = "/root/.local/share/openresearch/local-runs/"
SRC = {"j6h": "b717bff1*/repo/runs/fieldsuite-v04-v5h", "j6v": "4e2148f3*/repo/runs/fieldsuite-v04-v5v", "j6i": "f6848839*/repo/runs/fieldsuite-v04-v7i",
       "j6p": "3dbb0640*/repo/runs/fieldsuite-v04-v7p", "j6a": "a80cb339*/repo/runs/fieldsuite-v04-v6a", "j6g": "103bd160*/repo/runs/fieldsuite-v04-v7g",
       "j6l": "aa9030ff*/repo/runs/fieldsuite-v04-v7l", "j6c": "89883441*/repo/runs/fieldsuite-v04-v7c", "j7b": "4fe546a3*/repo/runs/fieldsuite-v04-v5b"}
HIDDEN = ("check",)


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
    """Constraints of the LAST task in the prompt (the statement only; no gold fields)."""
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
    """Official validator: number of valid meetings; clean = every step executed without a violation."""
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


nprows = {}
for role in ("FIT", "PARETO", "DEV"):  # never TEST
    for l in open(f"/root/projects/rider-4d/.external/fieldsuite-natplan-data-v1/roles-v1/{role}.jsonl"):
        r = json.loads(l)
        nprows[r["id"]] = r
bird = {}
if os.path.exists("/tmp/fable_out/bird_exec.json"):
    for r in json.load(open("/tmp/fable_out/bird_exec.json")):
        bird[(r["name"], r["role"], r["form"], r["uid"])] = r


def skey(c, role, f, x, text=None, form_for_bird=None):
    import hashlib
    k = skey0(c, role, f, x, text, form_for_bird)
    return None if k is None else hashlib.sha1(k.encode("utf-8", "replace")).hexdigest()[:12]


def skey0(c, role, f, x, text=None, form_for_bird=None):
    ds = c["ds"]
    tr = x.get("trajectory") or {}
    ans = tr.get("answer") if text is None else text
    if ds in ("aime", "livebench"):
        return "m:" + math_norm(ans)
    if ds == "gpqa":
        return "g:" + str(gpqa_letter(ans) or ukey({"answer": ans}))
    if ds == "toolhop":
        return "t:" + th_norm(ans)
    if ds == "natplan":
        row = nprows.get(x["uid"])
        if row and row["task"] == "trip":
            p = np_trip_parse(str(ans or ""))
            return "trip:" + (repr(p) if p else ukey({"answer": ans}))
        return "meet:" + "|".join(" ".join(s.split()).lower() for s in meet_steps(str(ans or "")))
    if ds == "bird":
        b = bird.get((c["name"], role, form_for_bird or f, x["uid"]))
        if b is None:
            return "u:" + ukey({"answer": ans})
        return ("h:" + b["h"]) if b.get("ok") else None  # a query that fails to run has no answer
    if ds == "bfcl":
        return ("b:" + json.dumps(tr.get("decoded"), sort_keys=True)) if text is None else None
    if text is not None:
        return "u:" + ukey({"answer": text})
    return "u:" + ukey(tr)


out = {}
for c in CELLS:
    if c["name"] in SRC:
        w = glob.glob(LR + SRC[c["name"]] + "/worker")[0]
    elif c["name"] == "u8j":
        continue
    else:
        w = LR + c["run"] + f"/repo/runs/fieldsuite-v04-{c['name']}/worker"
    cell = out.setdefault(c["name"], {})
    for role in ("PARETO", "FIT", "DEV"):
        res = {}
        for f in ("rigid", "liquid", "assembled"):
            p = w + f"/eval-selu-{role}-{f}.jsonl"
            for l in open(p):
                x = json.loads(l)
                res.setdefault(x["uid"], {})[f] = x
        uids = {it["uid"] for it in c["roles"][role]}
        assert uids == set(res), (c["name"], role, len(uids), len(res))
        feats = {}
        for uid, by in res.items():
            ft = {"k": {}, "alive": {}, "score": {}}
            for f, x in by.items():
                alive = not x.get("error") and bool(x.get("trajectory"))
                ft["alive"][f] = int(alive)
                ft["score"][f] = x["score"]
                ft["k"][f] = skey(c, role, f, x) if alive else None
                tr = x.get("trajectory") or {}
                if f == "assembled" and alive and tr.get("draft") not in (None, ""):
                    dk = skey(c, role, f, x, text=tr["draft"], form_for_bird="draft")
                    ft["draft_k"] = dk
                    ft["changed"] = int(dk != ft["k"][f])
                if c["ds"] == "natplan" and alive:
                    row = nprows[uid]
                    ans = str(tr.get("answer") or "")
                    if row["task"] == "trip":
                        ft.setdefault("valid", {})[f] = trip_valid(row["prompt"], ans)
                    else:
                        n, clean = meet_valid(meet_steps(ans), row["constraints"], row["dist_matrix"])
                        ft.setdefault("valid", {})[f] = n if clean else n - 0.5
                    ft["task"] = row["task"]
                if c["ds"] == "lcb" and alive and f != "rigid":
                    m = re.findall(r'"all_public_tests_passed":\s*(true|false)', str(tr.get("reasoning") or ""))
                    ft.setdefault("pub", {})[f] = None if not m else int(m[-1] == "true")
                if c["ds"] == "bird":
                    b = bird.get((c["name"], role, f, uid))
                    if b is not None:
                        ft.setdefault("exec", {})[f] = {"ok": int(bool(b.get("ok"))), "n": b.get("n"), "allnull": b.get("allnull")}
            feats[uid] = ft
        cell[role] = feats
json.dump(out, open("/tmp/fable_out/feats.json", "w"))
print("cells", len(out), "bytes", os.path.getsize("/tmp/fable_out/feats.json"), "bird rows", len(bird))
bad = 0
for c in CELLS:
    if c["name"] not in out:
        continue
    for role in ("PARETO", "FIT", "DEV"):
        for it in c["roles"][role]:
            for f in ("rigid", "liquid", "assembled"):
                if abs(out[c["name"]][role][it["uid"]]["score"][f] - it["s"][f]) > 1e-9:
                    bad += 1
print("score mismatches between eval files and picks:", bad)

