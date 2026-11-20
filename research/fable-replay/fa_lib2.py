"""Fable analysis library 2: item-level policies built from the saved outputs and the label-free features
(feats.json). Every policy maps an item to ONE of the three saved forms; its score is that form's saved score."""
import json, math, sys
sys.path.insert(0, "/tmp/fable_out")
from fa_lib import *
FEATS = json.load(open("/tmp/fable_out/feats.json"))
PRIO = ("assembled", "rigid", "liquid")  # liveness fallback order


def attach():
    for c in CELLS:
        fc = FEATS.get(c["name"])
        for role, items in c["roles"].items():
            for it in items:
                ft = fc[role][it["uid"]] if fc else None
                it["ft"] = ft
                if ft:
                    keys = ft["k"]
                    alive = [f for f in FORMS if ft["alive"].get(f) and keys.get(f) is not None]
                    groups = {}
                    for f in alive:
                        groups.setdefault(keys[f], []).append(f)
                    it["sg"] = list(groups.values())
                    it["alive"] = alive
                else:  # tau2: the worker's own groups
                    it["sg"] = it["g"] or []
                    it["alive"] = [f for g in it["sg"] for f in g]


attach()


def spattern(it):
    g = it["sg"]
    if len(it["alive"]) < 3:
        return "DEAD"
    if len(g) == 1:
        return "ALL"
    if len(g) == 3:
        return "R|L|A"
    s = set(max(g, key=len))
    return "RL|A" if s == {"rigid", "liquid"} else "RA|L" if s == {"rigid", "assembled"} else "LA|R"


def live(it, f, alive=None):
    """The form f, or the first alive form by priority if f produced no output."""
    alive = it["alive"] if alive is None else alive
    if f in alive or not alive:
        return f
    return next(x for x in PRIO if x in alive)


def sv(it, d, alive=None):
    """Semantic vote with fallback d: the answer shared by >= 2 alive forms, else d (else any alive form)."""
    alive = it["alive"] if alive is None else alive
    g = [[f for f in grp if f in alive] for grp in it["sg"]]
    g = [x for x in g if x]
    big = max(g, key=len) if g else []
    if len(big) >= 2:
        return d if d in big else big[0]
    return live(it, d, alive)


def pol(it, name):
    """Policy name -> form. Names: rigid/liquid/assembled (with liveness fallback: 'X+'), 'vote3' (worker's text-key
    vote, rigid fallback), 'SV:<d>' semantic vote with fallback d."""
    if name in FORMS:
        return name
    if name.endswith("+"):
        return live(it, name[:-1])
    if name == "vote3":
        return vote3_form(it)
    if name.startswith("SV:"):
        return sv(it, name[3:])
    raise KeyError(name)


def psc(it, name):
    if name == "oracle":
        return max(it["s"][f] for f in FORMS)
    return it["s"][pol(it, name)]


def pstats(items, a, b="rigid"):
    """Clustered mean and se of (policy a - policy b)."""
    by = {}
    for it in items:
        by.setdefault(cluster(it["uid"]), []).append(psc(it, a) - psc(it, b))
    n = sum(len(v) for v in by.values())
    m = sum(sum(v) for v in by.values()) / n
    K = len(by)
    if K < 2:
        return m, 0.0
    var = sum((sum(v) - m * len(v)) ** 2 for v in by.values()) * K / (K - 1) / n ** 2
    return m, math.sqrt(var)


def items_of(c, roles):
    return [it for r in roles for it in c["roles"][r]]


def choose(c, roles, z, cands, base="rigid", margin=0.0):
    """Leave `base` for the candidate with the highest mean on `roles` among those whose lower bound mean - z*se
    (paired vs base, clustered) exceeds `margin`; ties keep the earlier candidate."""
    items = items_of(c, roles)
    best, bm = base, None
    for f in cands:
        m, se = pstats(items, f, base)
        if m - z * se > margin + 1e-12:
            if bm is None or m > bm + 1e-12:
                best, bm = f, m
    return best


def dev_delta(c, name):
    dev = c["roles"]["DEV"]
    return mean(psc(it, name) - it["s"]["rigid"] for it in dev)


MAIN = [c for c in CELLS if c["opt"] != "gepa1"]


def summarize(sel, label, cells=None):
    """sel: {cid: policy name}. Prints mean / worst / #negative per optimizer and overall (36 cells)."""
    cells = MAIN if cells is None else cells
    out = []
    for o in ("gepa", "mipro", "simba"):
        v = [dev_delta(c, sel[cid(c)]) for c in cells if c["opt"] == o]
        out.append(f"{100*mean(v):+5.2f} {100*min(v):+6.2f} {sum(1 for x in v if x < -1e-9)}")
    v = [dev_delta(c, sel[cid(c)]) for c in cells]
    print(f"{label:34s} | " + " | ".join(out) + f" | {100*mean(v):+5.2f} {100*min(v):+6.2f} {sum(1 for x in v if x < -1e-9)}")
    return mean(v)

