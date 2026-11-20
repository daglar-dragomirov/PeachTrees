"""C2: what did the recorded J6* judge cost, and what would a judge replay over the SAVED outputs cost if it only looks
at contested items (no majority after verify -> vote) - per cell and in total; also the cost of one TEST pass of the
proposed forms. All from the runs' own per-item cost records; no model calls."""
import json, sys
sys.path.insert(0, "/tmp/fable_out")
from fa_lib3 import *
COST = json.load(open("/tmp/fable_out/costs.json"))


def contested(it):
    """No majority among the surviving forms and at least two distinct answers."""
    alive = vf_alive(it)
    g = [[f for f in grp if f in alive] for grp in it["sg"]]
    g = [x for x in g if x]
    return len(g) >= 2 and max(len(x) for x in g) < 2


tot_rec = tot_all = tot_sel = tot_test = tot_test_lazy = tot_asm = 0.0
rows = []
print("cell | recorded judge USD (P+F+DEV) | judged share | contested share (new rule) P+F / DEV | est. replay USD P+F, DEV (same J6* unit cost)")
for c in MAIN:
    ui = c["usd_item"]
    rec = sum(len(c["roles"][r]) * ((ui[r] or {}).get("judge") or 0.0) for r in ("PARETO", "FIT", "DEV"))
    judged = {r: mean(0 if it["mode"].split()[0] in ("identical", "no_trajectory", "default_failed") else 1 for it in c["roles"][r]) for r in ("PARETO", "FIT", "DEV")}
    unit = {}
    for r in ("PARETO", "FIT", "DEV"):
        j = (ui[r] or {}).get("judge") or 0.0
        unit[r] = j / judged[r] if judged[r] > 0 else 0.0
    cs = {r: mean(1 if contested(it) else 0 for it in c["roles"][r]) for r in ("PARETO", "FIT", "DEV")}
    u = max(unit.values())
    est_pf = sum(len(c["roles"][r]) * cs[r] * unit["DEV"] for r in ("PARETO", "FIT"))
    est_dev = len(c["roles"]["DEV"]) * cs["DEV"] * unit["DEV"]
    tot_rec += rec; tot_all += est_pf + est_dev; tot_sel += est_pf
    k = COST[cid(c)]
    n = len(c["roles"]["DEV"])
    need = mean(0 if ("rigid" in it["alive"] and "assembled" in it["alive"] and (it.get("ft") or {}).get("k", {}).get("rigid") is not None
                      and it["ft"]["k"]["rigid"] == it["ft"]["k"].get("assembled")) else 1 for it in c["roles"]["DEV"]) if c["name"] != "u8j" else 1.0
    t3 = n * ((k.get("rigid") or 0) + (k.get("assembled") or 0) + (k.get("liquid") or 0))
    tl = n * ((k.get("rigid") or 0) + (k.get("assembled") or 0) + need * (k.get("liquid") or 0))
    ta = n * (k.get("assembled") or 0)
    tot_test += t3; tot_test_lazy += tl; tot_asm += ta
    rows.append((cid(c), rec, est_pf, est_dev))
    print(f"{cid(c):16s} {rec:6.2f} | judged {judged['DEV']:.2f} unit {unit['DEV']:.4f} | contested {mean([cs['PARETO'], cs['FIT']]):.2f} / {cs['DEV']:.2f} | {est_pf:5.2f} {est_dev:5.2f} | TEST-like pass: 3 forms {t3:5.2f} lazy {tl:5.2f} asm-only {ta:5.2f}")
print(f"\nTOTAL recorded J6* judge spend over the 36 cells: {tot_rec:.1f} USD")
print(f"TOTAL est. judge replay on contested items, same unit cost: P+F {tot_sel:.1f} USD, P+F+DEV {tot_all:.1f} USD")
by = {}
for name, rec, a, b in rows:
    ds = name.split(":")[1]
    by.setdefault(ds, [0, 0, 0])
    by[ds][0] += rec; by[ds][1] += a; by[ds][2] += b
print("by dataset (3 optimizers): recorded | est. P+F | est. DEV")
for ds, v in sorted(by.items(), key=lambda x: -x[1][0]):
    print(f"  {ds:10s} {v[0]:6.2f} | {v[1]:5.2f} | {v[2]:5.2f}")
print(f"\none TEST-sized pass (n = n_DEV) of the forms over the 36 cells: rigid+assembled+liquid {tot_test:.1f} USD; with lazy liquid {tot_test_lazy:.1f} USD; assembled only {tot_asm:.1f} USD")

