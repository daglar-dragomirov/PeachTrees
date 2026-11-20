"""A2: task-level default-form rules replayed on saved outputs. Rule(data, z): candidates {liquid, assembled, vote3} whose
clustered paired lower bound mean - z*se (vs rigid) on `data` is > 0; choose the candidate with the highest mean on `data`;
none -> rigid. z=1.96 on PARETO ~ the v0.2 rule. DEV numbers are post hoc; LODO picks the variant on the other datasets."""
import sys, math
sys.path.insert(0, "/tmp/fable_out")
from fa_lib import *
CAND = ("liquid", "assembled", "vote3")


def stats(items, f):
    by = {}
    for it in items:
        by.setdefault(cluster(it["uid"]), []).append(sc(it, f) - sc(it, "rigid"))
    n = sum(len(v) for v in by.values())
    m = sum(sum(v) for v in by.values()) / n
    # clustered se of the ratio mean
    K = len(by)
    if K < 2:
        return m, 0.0
    var = sum((sum(v) - m * len(v)) ** 2 for v in by.values()) * K / (K - 1) / n ** 2
    return m, math.sqrt(var)


def choose(c, data, z, cands=CAND):
    items = [it for r in data for it in c["roles"][r]]
    best, bm = "rigid", None
    for f in cands:
        m, se = stats(items, f)
        if m - z * se > 1e-12 and m > 1e-12:
            if bm is None or m > bm + 1e-12:
                best, bm = f, m
    return best


DATA = {"P": ("PARETO",), "F": ("FIT",), "PF": ("PARETO", "FIT")}
ZS = (1.96, 1.645, 1.28, 0.84, 0.52, 0.25, 0.0)
variants = {}
for dn, d in DATA.items():
    for z in ZS:
        variants[f"{dn}:z{z}"] = (d, z, CAND)
        variants[f"{dn}:z{z}:noliq"] = (d, z, ("assembled", "vote3"))
res = {}  # variant -> cell -> (choice, dev delta)
for vn, (d, z, cands) in variants.items():
    res[vn] = {}
    for c in CELLS:
        f = choose(c, d, z, cands)
        dev = c["roles"]["DEV"]
        res[vn][cid(c)] = (f, mean(sc(it, f) - sc(it, "rigid") for it in dev))
# the recorded v0.2 choice
res["v0.2(recorded)"] = {cid(c): (c["summary_default"]["DEV"], mean(it["s"][it["ref"]] - it["s"]["rigid"] for it in c["roles"]["DEV"])) for c in CELLS}
res["reported"] = {cid(c): ("-", mean(reported(c, it) - it["s"]["rigid"] for it in c["roles"]["DEV"])) for c in CELLS}
for f in CAND + ("oracle",):
    res["always_" + f] = {cid(c): (f, mean(sc(it, f) - sc(it, "rigid") for it in c["roles"]["DEV"])) for c in CELLS}
# best single policy per cell on DEV (task-level oracle)
res["task_oracle"] = {cid(c): max(((f, mean(sc(it, f) - sc(it, "rigid") for it in c["roles"]["DEV"])) for f in ("rigid",) + CAND), key=lambda x: x[1]) for c in CELLS}

print("check: P:z1.96 vs recorded v0.2 choice")
for c in CELLS:
    a, b = res["P:z1.96"][cid(c)][0], res["v0.2(recorded)"][cid(c)][0]
    if a != b:
        print("  differs", cid(c), a, b)


def agg(vn, opts=("gepa", "mipro", "simba")):
    out = []
    for o in opts:
        v = [res[vn][cid(c)][1] for c in CELLS if c["opt"] == o]
        out.append((100 * mean(v), 100 * min(v), sum(1 for x in v if x < -1e-9)))
    allv = [res[vn][cid(c)][1] for c in CELLS if c["opt"] in opts]
    return out, 100 * mean(allv), 100 * min(allv), sum(1 for x in allv if x < -1e-9)


print("\nvariant | gepa mean/worst/#neg | mipro | simba | ALL36 mean worst #neg")
for vn in res:
    o, m, w, k = agg(vn)
    print(f"{vn:18s} | " + " | ".join(f"{a:+5.2f} {b:+6.2f} {n}" for a, b, n in o) + f" | {m:+5.2f} {w:+6.2f} {k}")

print("\nper-cell choices and DEV delta (pp) for key variants")
keys = ["v0.2(recorded)", "PF:z1.96", "PF:z1.28", "PF:z0.84", "PF:z0.0", "P:z0.0", "F:z0.0", "PF:z0.0:noliq", "task_oracle", "always_oracle"]
print("cell".ljust(17) + " ".join(k[:14].rjust(15) for k in keys))
for c in CELLS:
    print(cid(c).ljust(17) + " ".join(f"{res[k][cid(c)][0][:5]:>6s} {100*res[k][cid(c)][1]:+6.1f}  " for k in keys))

# leave-one-dataset-out choice of the variant: maximise mean gain on the other datasets subject to no negative cell
dss = sorted({c["ds"] for c in CELLS})
vs = list(variants)
lodo = {}
for ds in dss:
    def score(vn):
        v = [res[vn][cid(c)][1] for c in CELLS if c["ds"] != ds and c["opt"] != "gepa1"]
        return (min(v) >= -1e-9, mean(v))
    best = max(vs, key=score)
    lodo[ds] = best
print("\nLODO variant per held-out dataset:", lodo)
v = {cid(c): res[lodo[c["ds"]]][cid(c)][1] for c in CELLS}
for o in ("gepa", "mipro", "simba", "gepa1"):
    x = [v[cid(c)] for c in CELLS if c["opt"] == o]
    print(f"LODO {o}: mean {100*mean(x):+.2f} worst {100*min(x):+.2f}")
x = [v[cid(c)] for c in CELLS if c["opt"] != "gepa1"]
print(f"LODO ALL36: mean {100*mean(x):+.2f} worst {100*min(x):+.2f}")
# LODO without the no-negative constraint (pure mean)
lodo2 = {ds: max(vs, key=lambda vn: mean([res[vn][cid(c)][1] for c in CELLS if c["ds"] != ds and c["opt"] != "gepa1"])) for ds in dss}
print("LODO (mean only) variants:", lodo2)
x = [res[lodo2[c["ds"]]][cid(c)][1] for c in CELLS if c["opt"] != "gepa1"]
print(f"LODO-mean ALL36: mean {100*mean(x):+.2f} worst {100*min(x):+.2f}")

