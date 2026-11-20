"""B8: the cost / gain frontier of free policies (NI rule, z1 = 1.0, fitted on PARETO+FIT; DEV post hoc), with the
cost per item as a multiple of the optimizer program's own cost, plus the recorded-judge overlay."""
import json, sys
sys.path.insert(0, "/tmp/fable_out")
from fa_lib3 import *
import fa_lib2
COST = json.load(open("/tmp/fable_out/costs.json"))


def cost_mult(c, policy, sel):
    """Expected cost per DEV item / the program's cost, for the policy actually selected in this cell."""
    u = COST[cid(c)]
    r, l, a, j = (u.get(k) or 0.0 for k in ("rigid", "liquid", "assembled", "judge"))
    if not r:
        return None
    dev = c["roles"]["DEV"]
    p = sel
    if p == "rigid":
        return 1.0
    base = p[1:] if p.startswith("V") and p != "vote3" else p
    use_v = p.startswith("V") and p != "vote3"
    if base in ("assembled+", "assembled"):
        return a / r  # the draft is the fallback
    if base in ("liquid+", "liquid"):
        return (l + r * mean(0 if "liquid" in it["alive"] else 1 for it in dev)) / r
    if base == "SVD":
        sh = mean(1 if svd_needs_liquid(it, vf_alive(it) if use_v else it["alive"]) else 0 for it in dev)
        return (a + sh * l) / r
    if base.startswith("SV:") or base == "vote3":
        # as replayed: an independent rigid sample + assembled (own draft) + liquid only when rigid and assembled differ
        def need(it):
            k = (it.get("ft") or {}).get("k") or {}
            al = it["alive"]
            return not ("rigid" in al and "assembled" in al and k.get("rigid") is not None and k.get("rigid") == k.get("assembled"))
        sh = mean(1 if need(it) else 0 for it in dev) if c["name"] != "u8j" else 1.0
        return (r + a + sh * l) / r
    raise KeyError(p)


def row(label, selmap, extra_cost=None):
    out = []
    for o in ("gepa", "mipro", "simba"):
        v = [dev_delta(c, selmap[cid(c)]) for c in MAIN if c["opt"] == o]
        out.append(f"{100*mean(v):+5.2f} {100*min(v):+6.2f}")
    v = [dev_delta(c, selmap[cid(c)]) for c in MAIN]
    cm = [cost_mult(c, None, selmap[cid(c)]) for c in MAIN]
    cm = [x for x in cm if x is not None]
    neg = sum(1 for x in v if x < -1e-9)
    print(f"{label:38s} | " + " | ".join(out) + f" | {100*mean(v):+5.2f} {100*min(v):+6.2f} neg {neg} | cost x{mean(cm):.2f} (median x{sorted(cm)[len(cm)//2]:.2f}) | pp per extra x: {100*mean(v)/max(mean(cm)-1, 1e-9):.2f}")
    return mean(v), mean(cm)


print("policy (NI rule z1=1.0 on P+F unless noted)    | gepa mean worst | mipro | simba | ALL36 mean worst | cost multiple of the program")
row("always rigid", {cid(c): "rigid" for c in MAIN})
row("v0.2 lite (recorded default)", {cid(c): (c["summary_default"]["DEV"] if c["summary_default"]["DEV"] != "vote3" else "vote3") for c in MAIN})
for prior in ("assembled+", "SVD", "SV:assembled", "Vassembled+", "VSVD", "VSV:assembled"):
    for z1 in (1.0,):
        row(f"NI prior={prior}", {cid(c): ni_choice(c, prior, z1) for c in MAIN})
for prior in ("assembled+", "SVD", "SV:assembled", "VSVD", "VSV:assembled"):
    row(f"always {prior} (no rule)", {cid(c): prior for c in MAIN})

# reported v0.2 full: cost = 3 forms + judge on every non-identical item (as run)
v = [mean(reported(c, it) - it["s"]["rigid"] for it in c["roles"]["DEV"]) for c in MAIN]
cm = []
for c in MAIN:
    u = COST[cid(c)]
    if u.get("rigid"):
        cm.append((u["rigid"] + u["liquid"] + u["assembled"] + (u.get("judge") or 0)) / u["rigid"])
print(f"{'reported v0.2 + J6* (as run)':38s} | ALL36 {100*mean(v):+5.2f} worst {100*min(v):+6.2f} | cost x{mean(cm):.2f} (median x{sorted(cm)[len(cm)//2]:.2f}) | pp per extra x: {100*mean(v)/max(mean(cm)-1, 1e-9):.2f}")

print("\nper-cell liquid usage of the lazy policies on DEV and cost multiples")
for c in MAIN:
    dev = c["roles"]["DEV"]
    sh = mean(1 if svd_needs_liquid(it, it["alive"]) else 0 for it in dev)
    print(f"  {cid(c):16s} SVD liquid share {sh:.2f} | cost: asm x{cost_mult(c, None, 'assembled+') or 0:.1f} SVD x{cost_mult(c, None, 'SVD') or 0:.1f} SV x{cost_mult(c, None, 'SV:assembled') or 0:.1f}")

# ---- recorded-judge overlay on top of a base policy, gated on PARETO+FIT
print("\nrecorded J6* judge as an overlay: applied only where the judge's reference form equals the policy's choice")


def overlay(it, base, t):
    f0 = pol(it, base)
    prop = it.get("prop") if it["mode"] == "below_confidence" else it["form"]
    if it["ref"] == f0 and prop and prop != f0 and (it.get("conf") or 0) >= t:
        return prop
    return f0


for prior in ("SV:assembled", "VSV:assembled", "SVD"):
    tot_base, tot_j, tot_all = [], [], []
    det = []
    for c in MAIN:
        base = ni_choice(c, prior, 1.0)
        sel_items = items_of(c, ("PARETO", "FIT"))
        best_t, best_g = None, 0.0
        for t in (5, 4, 3, 0):
            g = mean(it["s"][overlay(it, base, t)] - psc(it, base) for it in sel_items)
            won = sum(1 for it in sel_items if it["s"][overlay(it, base, t)] > psc(it, base) + 1e-9)
            lost = sum(1 for it in sel_items if it["s"][overlay(it, base, t)] < psc(it, base) - 1e-9)
            if g > 0.005 and won > lost and g > best_g + 1e-12:
                best_t, best_g = t, g
        dev = c["roles"]["DEV"]
        b = mean(psc(it, base) - it["s"]["rigid"] for it in dev)
        j = b if best_t is None else mean(it["s"][overlay(it, base, best_t)] - it["s"]["rigid"] for it in dev)
        a = mean(it["s"][overlay(it, base, 0)] - it["s"]["rigid"] for it in dev)
        cov = mean(1 if it["ref"] == pol(it, base) else 0 for it in dev)
        tot_base.append(b); tot_j.append(j); tot_all.append(a)
        det.append(f"{cid(c)}:{'off' if best_t is None else 't'+str(best_t)}:{100*(j-b):+.1f}")
    print(f"  base NI {prior:14s}: base {100*mean(tot_base):+.2f} | + gated recorded judge {100*mean(tot_j):+.2f} (worst cell change {100*min(a-b for a,b in zip(tot_j,tot_base)):+.2f}) | judge always on {100*mean(tot_all):+.2f}")
    print("     ", " ".join(d for d in det if not d.endswith(":+0.0")))

# ---- hybrid: skip liquid (and the separate program sample) where the vote never fires on the selection data
print("\nauto-lite hybrid: full rule where the vote changes >= 2% of the answers on PARETO+FIT, reviewer-only elsewhere")
sel, cm = {}, []
for c in MAIN:
    full = ni_choice(c, "VSV:assembled", 1.0)
    if full != "rigid":
        pf = items_of(c, ("PARETO", "FIT"))
        fire = mean(1 if pol(it, "VSV:assembled") != pol(it, "Vassembled+") else 0 for it in pf)
        if fire < 0.02:
            full = "Vassembled+"
    sel[cid(c)] = full
row("auto-lite hybrid (NI, VSV / Vasm)", sel)
print("   reviewer-only cells:", [k for k, v in sel.items() if v == "Vassembled+"])

