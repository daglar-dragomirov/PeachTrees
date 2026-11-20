"""B3: is the optimizer's program (rigid) optimistically scored on the data it was optimized on (PARETO = valset, FIT =
trainset) relative to the agent forms? Difference-in-differences per cell:
DiD(form) = (rigid_sel - rigid_DEV) - (form_sel - form_DEV), sel in {PARETO, FIT}. Positive = rigid looks better on the
selection data than it is on fresh data, relative to the form."""
import sys, math
sys.path.insert(0, "/tmp/fable_out")
from fa_lib2 import *


def m(c, role, f):
    return mean(psc(it, f) for it in c["roles"][role])


rows = []
print("cell              | rigid P / F / DEV    | DiD liquid P, F | DiD assembled P, F | DiD SV:assembled P, F")
for c in CELLS:
    r = {role: m(c, role, "rigid") for role in ("PARETO", "FIT", "DEV")}
    out = {}
    for f in ("liquid+", "assembled+", "SV:assembled"):
        for role in ("PARETO", "FIT"):
            out[(f, role)] = (r[role] - r["DEV"]) - (m(c, role, f) - m(c, "DEV", f))
    rows.append((c, out))
    print(f"{cid(c):17s} | {r['PARETO']:.3f} {r['FIT']:.3f} {r['DEV']:.3f} | " +
          " | ".join(f"{100*out[(f,'PARETO')]:+6.1f} {100*out[(f,'FIT')]:+6.1f}" for f in ("liquid+", "assembled+", "SV:assembled")))
print()
for o in ("gepa", "mipro", "simba", "all"):
    sel = [x for x in rows if (x[0]["opt"] == o or (o == "all" and x[0]["opt"] != "gepa1"))]
    line = f"{o:6s} n={len(sel)}"
    for f in ("liquid+", "assembled+", "SV:assembled"):
        for role in ("PARETO", "FIT"):
            v = [x[1][(f, role)] for x in sel]
            mu = mean(v)
            sd = math.sqrt(sum((a - mu) ** 2 for a in v) / (len(v) - 1))
            line += f" | {f[:5]} {role[0]}: {100*mu:+5.2f} (se {100*sd/math.sqrt(len(v)):.2f}, pos {sum(1 for a in v if a > 0)}/{len(v)})"
    print(line)
print()
print("rigid optimism alone: rigid_sel - rigid_DEV (includes any distribution shift between the splits)")
for o in ("gepa", "mipro", "simba"):
    sel = [x[0] for x in rows if x[0]["opt"] == o]
    for role in ("PARETO", "FIT"):
        v = [m(c, role, "rigid") - m(c, "DEV", "rigid") for c in sel]
        w = [m(c, role, "liquid+") - m(c, "DEV", "liquid+") for c in sel]
        a = [m(c, role, "assembled+") - m(c, "DEV", "assembled+") for c in sel]
        print(f"{o} {role}: rigid {100*mean(v):+.2f}  liquid {100*mean(w):+.2f}  assembled {100*mean(a):+.2f}")

