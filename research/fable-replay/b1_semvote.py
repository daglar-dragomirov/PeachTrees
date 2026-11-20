"""B1: free item-level policies (semantic vote, liveness fallback) and task-level rules choosing among them on PARETO/FIT.
DEV numbers are post hoc; the rule variant is also chosen leave-one-dataset-out."""
import sys
sys.path.insert(0, "/tmp/fable_out")
from fa_lib2 import *

POL = ["rigid", "liquid", "assembled", "rigid+", "liquid+", "assembled+", "vote3", "SV:rigid", "SV:liquid", "SV:assembled", "oracle"]
print("DEV accuracy by policy (pattern shares with task-aware keys)")
print("cell".ljust(17) + " ".join(p[:9].rjust(9) for p in POL) + "   ALL  2v1  DIFF DEAD")
for c in CELLS:
    dev = c["roles"]["DEV"]
    pats = [spattern(it) for it in dev]
    sh = lambda p: sum(1 for x in pats if x == p) / len(pats)
    print(cid(c).ljust(17) + " ".join(f"{mean(psc(it, p) for it in dev):9.3f}" for p in POL) +
          f"  {sh('ALL'):.2f} {sh('RL|A')+sh('RA|L')+sh('LA|R'):.2f} {sh('R|L|A'):.2f} {sh('DEAD'):.2f}")

print("\nalways-X policies: gepa mean/worst/#neg | mipro | simba | ALL36")
for p in POL:
    summarize({cid(c): p for c in MAIN}, "always " + p)

DATA = {"P": ("PARETO",), "F": ("FIT",), "PF": ("PARETO", "FIT")}
CSETS = {
    "v02": ("liquid", "assembled", "vote3"),
    "forms+": ("liquid+", "assembled+"),
    "sv": ("liquid+", "assembled+", "SV:rigid", "SV:liquid", "SV:assembled"),
    "sv-noliq": ("assembled+", "SV:rigid", "SV:assembled"),
    "svonly": ("SV:rigid", "SV:liquid", "SV:assembled"),
    "svonly-noliq": ("SV:rigid", "SV:assembled"),
}
ZS = (1.96, 1.28, 0.84, 0.52, 0.0)
res = {}
print("\nrule(data, z, candidate set): gepa mean/worst/#neg | mipro | simba | ALL36")
for cs, cands in CSETS.items():
    for dn, d in DATA.items():
        for z in ZS:
            name = f"{cs}|{dn}|z{z}"
            sel = {cid(c): choose(c, d, z, cands) for c in CELLS}
            res[name] = sel
            summarize(sel, name)

dss = sorted({c["ds"] for c in CELLS})
lodo = {}
for ds in dss:
    def score(vn):
        v = [dev_delta(c, res[vn][cid(c)]) for c in MAIN if c["ds"] != ds]
        return (min(v) >= -1e-9, mean(v))
    lodo[ds] = max(res, key=score)
print("\nLODO variant per held-out dataset:", lodo)
sel = {cid(c): res[lodo[c["ds"]]][cid(c)] for c in CELLS}
summarize(sel, "LODO-chosen rule")
print("\nper cell: chosen policy and DEV delta (pp) for a few variants")
keys = ["v02|P|z1.96", "sv|PF|z0.0", "sv|PF|z0.52", "sv|PF|z0.84", "sv-noliq|PF|z0.0", "svonly|PF|z0.0", "sv|P|z0.0"]
print("cell".ljust(17) + " ".join(k.rjust(22) for k in keys))
for c in CELLS:
    print(cid(c).ljust(17) + " ".join(f"{res[k][cid(c)]:>13s} {100*dev_delta(c, res[k][cid(c)]):+6.1f}  " for k in keys))

