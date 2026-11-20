"""Fable analysis library: loads /tmp/fable_out/cells.json (built by extract_cells.py) and offers replay helpers.
No model calls; pure replay of saved per-item scores."""
import json, random
FORMS = ("rigid", "liquid", "assembled")
CELLS = json.load(open("/tmp/fable_out/cells.json"))
OPTS = ("gepa", "mipro", "simba", "gepa1")


def cid(c):
    return f"{c['opt']}:{c['ds']}"


def cluster(uid):
    return uid.rsplit(":", 1)[0] if uid.startswith("aime25:") else uid  # AIME DEV = problems x repeats


def vote3_form(it):
    """Same logic as the worker's vote3_form, from the saved answer-equivalence groups."""
    g = it["g"] or []
    if not g:
        return "rigid"
    big = max(g, key=lambda x: (len(x), "rigid" in x))
    alive = [f for x in g for f in x]
    if len(big) >= 2:
        return "rigid" if "rigid" in big else big[0]
    return "rigid" if "rigid" in alive else alive[0]


def sc(it, form):
    """Score of a policy name on an item: a form, 'vote3', 'oracle'."""
    if form == "vote3":
        return it["s"][vote3_form(it)]
    if form == "oracle":
        return max(it["s"][f] for f in FORMS)
    return it["s"][form]


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def boot_ci(items, fn, seed=11, n=2000, lo=0.025, hi=0.975):
    """Clustered bootstrap CI of mean(fn(item))."""
    by = {}
    for it in items:
        by.setdefault(cluster(it["uid"]), []).append(fn(it))
    keys = list(by)
    sums = [(sum(by[k]), len(by[k])) for k in keys]
    rng = random.Random(seed)
    ms = []
    K = len(keys)
    for _ in range(n):
        s = c = 0
        for _ in range(K):
            a, b = sums[rng.randrange(K)]
            s += a
            c += b
        ms.append(s / c)
    ms.sort()
    return ms[int(lo * n)], ms[min(n - 1, int(hi * n))]


def boot_lower(items, fn, level, seed=42, n=2000):
    """One-sided lower bound at the given level (e.g. 0.975 -> the 2.5 % quantile)."""
    by = {}
    for it in items:
        by.setdefault(cluster(it["uid"]), []).append(fn(it))
    sums = [(sum(v), len(v)) for v in by.values()]
    rng = random.Random(seed)
    K = len(sums)
    ms = []
    for _ in range(n):
        s = c = 0
        for _ in range(K):
            a, b = sums[rng.randrange(K)]
            s += a
            c += b
        ms.append(s / c)
    ms.sort()
    return ms[int((1 - level) * n)]


def fit_gate(c):
    """The reported FIT gate: judge enabled iff FIT selected-default > 0.005 and switches won > lost."""
    fit = c["roles"]["FIT"]
    d = mean(it["s"][it["form"]] - it["s"][it["ref"]] for it in fit)
    won = sum(1 for it in fit if it["form"] != it["ref"] and it["s"][it["form"]] > it["s"][it["ref"]] + 1e-12)
    lost = sum(1 for it in fit if it["form"] != it["ref"] and it["s"][it["form"]] < it["s"][it["ref"]] - 1e-12)
    return d > 0.005 and won > lost


def reported(c, it):
    return it["s"][it["form"]] if c["_gate"] else it["s"][it["ref"]]


for _c in CELLS:
    _c["_gate"] = fit_gate(_c)

