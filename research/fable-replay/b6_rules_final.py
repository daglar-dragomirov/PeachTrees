"""B6: the candidate PeachTrees 1.0 task-level rules, tuned WITHOUT DEV (PARETO <-> FIT cross-validation), then
replayed on DEV (post hoc) and checked leave-one-dataset-out.
Rule families:
  AM(z)            argmax over the family, a candidate needs paired lower bound mean - z*se > 0 vs rigid
  NI(prior, z1)    use the prior policy unless it is worse than rigid beyond noise (mean + z1*se < 0) -> rigid
  NIU(prior,z1,z2) NI, then upgrade from the prior to another family member only if it beats the PRIOR with
                   mean - z2*se > 0 (paired vs the prior)
usage: python3 b6_rules_final.py [V]   (V = verification-filtered family)"""
import sys
sys.path.insert(0, "/tmp/fable_out")
from fa_lib3 import *
import fa_lib2

V = len(sys.argv) > 1 and sys.argv[1] == "V"
px = "V" if V else ""
FAM = [px + "assembled+", px + "liquid+", px + "SV:rigid", px + "SV:assembled", px + "SV:liquid"]
FAM_NL = [px + "assembled+", px + "SV:rigid", px + "SV:assembled"]
PRIORS = [px + "SV:assembled", px + "assembled+"]


def rule_AM(items, z, fam):
    best, bm = "rigid", None
    for f in fam:
        m, se = fa_lib2.pstats(items, f, "rigid")
        if m - z * se > 1e-12 and (bm is None or m > bm + 1e-12):
            best, bm = f, m
    return best


def rule_NIU(items, prior, z1, z2, fam):
    m, se = fa_lib2.pstats(items, prior, "rigid")
    if m + z1 * se < 0:
        # the prior is harmful here: fall back to rigid unless another member is clearly better than rigid
        return rule_AM(items, 1.0, [f for f in fam if f != prior]) if z2 is not None else "rigid"
    if z2 is None:
        return prior
    best, bm = prior, None
    for f in fam:
        if f == prior:
            continue
        d, se2 = fa_lib2.pstats(items, f, prior)
        if d - z2 * se2 > 1e-12 and (bm is None or d > bm + 1e-12):
            best, bm = f, d
    return best


VARIANTS = {}
for z in (0.0, 0.5, 1.0, 1.28, 1.96):
    VARIANTS[f"AM z={z}"] = lambda items, z=z: rule_AM(items, z, FAM)
    VARIANTS[f"AM-noliq z={z}"] = lambda items, z=z: rule_AM(items, z, FAM_NL)
for prior in PRIORS:
    for z1 in (0.0, 0.5, 1.0, 1.28, 1.645):
        VARIANTS[f"NI {prior} z1={z1}"] = lambda items, p=prior, z1=z1: rule_NIU(items, p, z1, None, FAM)
        for z2 in (0.0, 0.5, 1.0, 1.645):
            VARIANTS[f"NIU {prior} z1={z1} z2={z2}"] = lambda items, p=prior, z1=z1, z2=z2: rule_NIU(items, p, z1, z2, FAM)


def gain(items, p):
    return mean(psc(it, p) - it["s"]["rigid"] for it in items)


# ---- DEV-free tuning: fit on PARETO, score on FIT, and the reverse
cv = {}
for vn, fn in VARIANTS.items():
    g = []
    for c in MAIN:
        P, F = c["roles"]["PARETO"], c["roles"]["FIT"]
        g.append(0.5 * (gain(F, fn(P)) + gain(P, fn(F))))
    cv[vn] = (mean(g), min(g), sum(1 for x in g if x < -1e-9))
# ---- DEV replay (post hoc): fit on PARETO+FIT
dev = {}
sel = {}
for vn, fn in VARIANTS.items():
    sel[vn] = {cid(c): fn(items_of(c, ("PARETO", "FIT"))) for c in CELLS}
    g = [dev_delta(c, sel[vn][cid(c)]) for c in MAIN]
    dev[vn] = (mean(g), min(g), sum(1 for x in g if x < -1e-9))
print(f"family: {FAM}")
print("variant                                   | P<->F CV: mean worst #neg | DEV (fit on P+F): mean worst #neg | by optimizer DEV mean (gepa mipro simba)")
for vn in sorted(VARIANTS, key=lambda v: -cv[v][0]):
    byo = [mean(dev_delta(c, sel[vn][cid(c)]) for c in MAIN if c["opt"] == o) for o in ("gepa", "mipro", "simba")]
    print(f"{vn:41s} | {100*cv[vn][0]:+5.2f} {100*cv[vn][1]:+6.2f} {cv[vn][2]:2d} | {100*dev[vn][0]:+5.2f} {100*dev[vn][1]:+6.2f} {dev[vn][2]:2d} | " + " ".join(f"{100*x:+5.2f}" for x in byo))

best_cv = max(VARIANTS, key=lambda v: cv[v][0])
safe = [v for v in VARIANTS if cv[v][2] == 0] or list(VARIANTS)
best_cv_safe = max(safe, key=lambda v: cv[v][0])
print("\nDEV-free choice (max P<->F CV mean):", best_cv, "-> DEV", [round(100 * x, 2) for x in dev[best_cv][:2]], "neg", dev[best_cv][2])
print("DEV-free choice among variants with no negative CV cell:", best_cv_safe, "-> DEV", [round(100 * x, 2) for x in dev[best_cv_safe][:2]], "neg", dev[best_cv_safe][2])

# ---- leave-one-dataset-out on DEV
dss = sorted({c["ds"] for c in CELLS})
lodo_sel = {}
for ds in dss:
    def score(vn):
        v = [dev_delta(c, sel[vn][cid(c)]) for c in MAIN if c["ds"] != ds]
        return (min(v) >= -1e-9, mean(v))
    lodo_sel[ds] = max(VARIANTS, key=score)
print("\nLODO variants:", {k: v for k, v in lodo_sel.items()})
summarize({cid(c): sel[lodo_sel[c["ds"]]][cid(c)] for c in CELLS}, "LODO-chosen (DEV)")
for vn in dict.fromkeys([best_cv, best_cv_safe, f"NI {PRIORS[0]} z1=1.0", f"NIU {PRIORS[0]} z1=1.0 z2=1.0", "AM z=0.0", "AM z=1.96"]):
    summarize(sel[vn], vn)
    summarize(sel[vn], vn + " [gepa seed 1]", cells=[c for c in CELLS if c["opt"] == "gepa1"]) if False else None

show = list(dict.fromkeys([best_cv, f"NI {PRIORS[0]} z1=1.0", f"NIU {PRIORS[0]} z1=1.0 z2=1.0", "AM z=0.0"]))
print("\nper cell (DEV delta pp, n, chosen policy, 95% clustered CI) for:", show)
import json
out = {}
for c in CELLS:
    line = f"{cid(c):16s} n={len(c['roles']['DEV']):3d}"
    for vn in show:
        p = sel[vn][cid(c)]
        d = dev_delta(c, p)
        lo, hi = boot_ci(c["roles"]["DEV"], lambda it, p=p: psc(it, p) - it["s"]["rigid"], n=1000)
        line += f" | {p:>14s} {100*d:+6.1f} [{100*lo:+5.1f},{100*hi:+5.1f}]"
        out.setdefault(vn, {})[cid(c)] = {"policy": p, "delta": d, "ci": [lo, hi]}
    print(line)
json.dump(out, open(f"/tmp/fable_out/b6_result{'_V' if V else ''}.json", "w"))

