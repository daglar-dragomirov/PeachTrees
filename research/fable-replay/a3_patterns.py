"""A3: agreement patterns among the three forms (from the saved answer-equivalence groups) and what they predict.
Pattern names: ALL (all three equal), RL|A, RA|L, LA|R (two agree), R|L|A (all differ), DEAD (a form failed)."""
import sys
sys.path.insert(0, "/tmp/fable_out")
from fa_lib import *


def pattern(it):
    g = it["g"] or []
    alive = sorted(f for x in g for f in x)
    if len(alive) < 3:
        return "DEAD"
    if len(g) == 1:
        return "ALL"
    if len(g) == 3:
        return "R|L|A"
    big = max(g, key=len)
    s = set(big)
    return "RL|A" if s == {"rigid", "liquid"} else "RA|L" if s == {"rigid", "assembled"} else "LA|R"


PATS = ("ALL", "RL|A", "RA|L", "LA|R", "R|L|A", "DEAD")
print("DEV pattern shares and accuracy r/l/a/oracle per pattern")
tot = {p: [0, 0, 0, 0, 0] for p in PATS}
for c in CELLS:
    dev = c["roles"]["DEV"]
    line = f"{cid(c):16s}"
    for p in PATS:
        its = [it for it in dev if pattern(it) == p]
        if not its:
            line += f" | {p}: -"
            continue
        r, l, a, o = (mean(sc(it, f) for it in its) for f in ("rigid", "liquid", "assembled", "oracle"))
        line += f" | {p} {len(its)/len(dev):.2f}: {r:.2f}/{l:.2f}/{a:.2f}/{o:.2f}"
        if c["opt"] != "gepa1":
            t = tot[p]
            t[0] += len(its) / len(dev)
            for i, v in enumerate((r, l, a, o)):
                t[i + 1] += v * len(its) / len(dev)
    print(line)
print("\nmacro over 36 cells: share, acc r/l/a/oracle (weighted by share)")
for p in PATS:
    t = tot[p]
    if t[0]:
        print(f"{p:6s} share {t[0]/36:.3f}  r {t[1]/t[0]:.3f} l {t[2]/t[0]:.3f} a {t[3]/t[0]:.3f} oracle {t[4]/t[0]:.3f}  gap(oracle-best) {(t[4]-max(t[1:4]))/36*100:.2f} pp")

