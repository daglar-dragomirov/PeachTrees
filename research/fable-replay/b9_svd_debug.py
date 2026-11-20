import sys
sys.path.insert(0, "/tmp/fable_out")
from fa_lib3 import *
tw = tl = 0
for c in MAIN:
    dev = c["roles"]["DEV"]
    n = w = l = 0
    for it in dev:
        a, b = pol(it, "SVD"), pol(it, "assembled+")
        if a != b:
            n += 1
            d = it["s"][a] - it["s"][b]
            w += d > 0
            l += d < 0
    tw += w; tl += l
    if n:
        print(f"{cid(c):16s} SVD differs from assembled+ on {n} items: won {w} lost {l}")
print("total won", tw, "lost", tl)
# the 2:1 revert case in detail: reviewer changed the draft, the agent reproduces the draft
agg = [0, 0, 0]
for c in MAIN:
    for it in c["roles"]["DEV"]:
        ft = it.get("ft") or {}
        if ft.get("changed") == 1 and "liquid" in it["alive"] and "assembled" in it["alive"] and ft["k"].get("liquid") == ft.get("draft_k"):
            agg[0] += 1
            agg[1] += it["s"]["liquid"]
            agg[2] += it["s"]["assembled"]
print("revert cases (changed & liquid == draft):", agg[0], "liquid(=draft) correct", agg[1], "assembled correct", agg[2])
# same on PARETO+FIT
agg = [0, 0, 0]
for c in MAIN:
    for it in items_of(c, ("PARETO", "FIT")):
        ft = it.get("ft") or {}
        if ft.get("changed") == 1 and "liquid" in it["alive"] and "assembled" in it["alive"] and ft["k"].get("liquid") == ft.get("draft_k"):
            agg[0] += 1
            agg[1] += it["s"]["liquid"]
            agg[2] += it["s"]["assembled"]
print("PARETO+FIT revert cases:", agg[0], "liquid(=draft) correct", agg[1], "assembled correct", agg[2])

