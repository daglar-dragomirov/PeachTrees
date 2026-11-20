"""E1: what the reported 'judge gain' (reported minus the v0.2 default form) consisted of on DEV: liveness rescue
(the default form had no output -> another form; mode default_failed) vs genuine judge switches; the PARETO threshold
and the FIT gate per cell; the dollars spent on the judge where it was finally switched off."""
import sys
sys.path.insert(0, "/tmp/fable_out")
from fa_lib import *
on = off = 0
g_live = g_judge = 0.0
spent_off = spent_on = 0.0
thr_off = 0
for c in CELLS:
    if c["opt"] == "gepa1":
        continue
    dev = c["roles"]["DEV"]
    n = len(dev)
    ui = c["usd_item"]
    spend = sum(len(c["roles"][r]) * ((ui[r] or {}).get("judge") or 0.0) for r in ("PARETO", "FIT", "DEV"))
    thr = (c["judge_threshold"] or {}).get("min_confidence")
    thr_off += thr == 99
    if c["_gate"]:
        on += 1
        spent_on += spend
        live = sum(it["s"][it["form"]] - it["s"][it["ref"]] for it in dev if it["mode"].startswith("default_failed")) / n
        judge = sum(it["s"][it["form"]] - it["s"][it["ref"]] for it in dev if not it["mode"].startswith("default_failed")) / n
        g_live += live
        g_judge += judge
        print(f"{cid(c):16s} gate ON  thr={thr} | judge part {100*judge:+5.1f} pp | liveness-rescue part {100*live:+5.1f} pp | judge spend {spend:.2f} USD")
    else:
        off += 1
        spent_off += spend
print(f"\ngate on in {on} cells, off in {off}; PARETO threshold = off (99) in {thr_off} cells")
print(f"macro over 36 cells: genuine judge switches {100*g_judge/36:+.2f} pp, liveness rescue {100*g_live/36:+.2f} pp (sum = reported - v0.2 lite)")
print(f"judge dollars: {spent_on:.1f} USD in gate-on cells, {spent_off:.1f} USD in cells where the judge was finally not used")

