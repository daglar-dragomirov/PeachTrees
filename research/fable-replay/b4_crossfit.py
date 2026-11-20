"""B4: (a) task-level oracle of the free policy family; (b) cross-fitted estimate of 'select the policy on clean held-out
data' (random halves of DEV: choose on one half, score on the other) vs selecting on PARETO+FIT; (c) non-inferiority rules
with assembled as the prior; (d) the recorded judge's precision/recall; (e) residual oracle gap by agreement pattern."""
import sys, random
sys.path.insert(0, "/tmp/fable_out")
from fa_lib2 import *

FAM = ("rigid", "assembled+", "liquid+", "SV:rigid", "SV:assembled", "SV:liquid")
FAM_NL = ("rigid", "assembled+", "SV:rigid", "SV:assembled")

print("(a) task-level oracle (best single policy per cell on DEV; an upper bound for any task-level rule)")
for fam, nm in ((("rigid", "liquid", "assembled", "vote3"), "v0.2 family"), (FAM, "free family"), (FAM_NL, "free family, no liquid default")):
    summarize({cid(c): max(fam, key=lambda p: dev_delta(c, p)) for c in MAIN}, "task-oracle " + nm)
summarize({cid(c): "oracle" for c in MAIN}, "item oracle")


def pick(items, fam, z=0.0):
    best, bm = "rigid", None
    for f in fam:
        if f == "rigid":
            continue
        m, se = pstats(items, f, "rigid")
        if m - z * se > 1e-12 and (bm is None or m > bm + 1e-12):
            best, bm = f, m
    return best


print("\n(b) cross-fit on DEV: select on a random subset of size n_sel, score on the rest (200 splits), family = free family")
rng = random.Random(7)
for frac, label in ((0.5, "half of DEV"), (0.25, "quarter of DEV")):
    for fam, nm in ((FAM, "all"), (FAM_NL, "no-liquid")):
        per = {}
        for c in MAIN:
            dev = c["roles"]["DEV"]
            # cluster-respecting split
            cl = {}
            for it in dev:
                cl.setdefault(cluster(it["uid"]), []).append(it)
            keys = list(cl)
            tot = 0.0
            neg = 0
            R = 200
            for _ in range(R):
                rng.shuffle(keys)
                k = max(1, int(len(keys) * frac))
                a = [it for kk in keys[:k] for it in cl[kk]]
                b = [it for kk in keys[k:] for it in cl[kk]]
                p = pick(a, fam)
                tot += mean(psc(it, p) - it["s"]["rigid"] for it in b)
            per[cid(c)] = tot / R
        out = []
        for o in ("gepa", "mipro", "simba"):
            v = [per[cid(c)] for c in MAIN if c["opt"] == o]
            out.append(f"{100*mean(v):+5.2f} {100*min(v):+6.2f}")
        v = list(per.values())
        print(f"select on {label:15s} [{nm:9s}] | " + " | ".join(out) + f" | {100*mean(v):+5.2f} {100*min(v):+6.2f}")
        if frac == 0.5 and nm == "all":
            keep = per

print("\n    per cell: select on PARETO+FIT (z=0) vs cross-fit on half of DEV vs task-oracle (pp)")
for c in MAIN:
    a = dev_delta(c, choose(c, ("PARETO", "FIT"), 0.0, FAM[1:]))
    t = max(dev_delta(c, p) for p in FAM)
    print(f"    {cid(c):16s} PF {100*a:+6.1f}   DEV-half {100*keep[cid(c)]:+6.1f}   task-oracle {100*t:+6.1f}   item-oracle {100*dev_delta(c,'oracle'):+6.1f}")

print("\n(c) non-inferiority rules: use PRIOR policy unless it is worse than rigid on PARETO+FIT by more than z*se")
for prior in ("assembled+", "SV:assembled"):
    for z in (0.0, 0.5, 1.0, 1.28, 1.645, 99):
        sel = {}
        for c in MAIN:
            m, se = pstats(items_of(c, ("PARETO", "FIT")), prior, "rigid")
            sel[cid(c)] = prior if m + z * se >= 0 else "rigid"
        summarize(sel, f"NI prior={prior} z={z}")
# hybrid: argmax among the family, but if the argmax is rigid and the prior is not significantly worse -> prior
for z in (0.5, 1.0, 1.28):
    sel = {}
    for c in MAIN:
        p = choose(c, ("PARETO", "FIT"), 0.0, FAM[1:])
        if p == "rigid":
            m, se = pstats(items_of(c, ("PARETO", "FIT")), "SV:assembled", "rigid")
            if m + z * se >= 0:
                p = "SV:assembled"
        sel[cid(c)] = p
    summarize(sel, f"argmax, rigid->SV:asm if NI z={z}")
    print("      changed cells:", {k: (v, round(100 * dev_delta(next(c for c in MAIN if cid(c) == k), v), 1)) for k, v in sel.items()
                                    if v == "SV:assembled" and choose(next(c for c in MAIN if cid(c) == k), ("PARETO", "FIT"), 0.0, FAM[1:]) == "rigid"})

print("\n(d) the recorded J6* judge on DEV, all proposals regardless of threshold / gate (ref = the v0.2 default)")
tw = tl = tn = 0
resc = harm_base = 0
for c in MAIN:
    dev = c["roles"]["DEV"]
    w = l = n = 0
    can = got = 0
    for it in dev:
        f = it.get("prop") if it["mode"] == "below_confidence" else it["form"]
        ref = it["ref"]
        if it["s"][ref] < max(it["s"].values()) - 1e-9:
            can += 1
        if f and f != ref:
            d = it["s"][f] - it["s"][ref]
            if d > 1e-9:
                w += 1
            elif d < -1e-9:
                l += 1
            else:
                n += 1
    tw += w; tl += l; tn += n; resc += can
    print(f"    {cid(c):16s} proposals won {w:3d} lost {l:3d} neutral {n:3d} | items where a better form existed: {can:3d} ({can/len(dev):.2f}) recall {w/can if can else 0:.2f}")
print(f"    TOTAL won {tw} lost {tl} neutral {tn}; precision among decisive {tw/(tw+tl):.3f}; recall of improvable items {tw/resc:.3f}")

print("\n(e) residual gap to the item oracle after the free policy SV:assembled, by pattern (pp of DEV, macro over 36 cells)")
agg = {}
for c in MAIN:
    dev = c["roles"]["DEV"]
    for it in dev:
        p = spattern(it)
        agg.setdefault(p, [0.0, 0.0])
        agg[p][0] += (psc(it, "oracle") - psc(it, "SV:assembled")) / len(dev) / len(MAIN)
        agg[p][1] += 1 / len(dev) / len(MAIN)
for p, (g, s) in sorted(agg.items(), key=lambda x: -x[1][0]):
    print(f"    {p:6s} share {s:.3f} residual gap {100*g:5.2f} pp")
by_ds = {}
for c in MAIN:
    dev = c["roles"]["DEV"]
    by_ds.setdefault(c["ds"], []).append(mean(psc(it, "oracle") - psc(it, "SV:assembled") for it in dev))
print("    residual by dataset (mean over optimizers):", {k: round(100 * mean(v), 1) for k, v in sorted(by_ds.items(), key=lambda x: -mean(x[1]))})

