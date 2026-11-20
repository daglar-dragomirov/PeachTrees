"""C8: task-level ceiling of the verification-filtered family (best single policy per cell on DEV) and the cost in USD
of one TEST-sized pass for the auto-lite configuration."""
import json, sys
sys.path.insert(0, "/tmp/fable_out")
from fa_lib3 import *
import fa_lib2
COST = json.load(open("/tmp/fable_out/costs.json"))
FAM = ("rigid", "Vassembled+", "Vliquid+", "VSV:rigid", "VSV:assembled", "VSV:liquid")
summarize({cid(c): max(FAM, key=lambda p: fa_lib2.dev_delta(c, p)) for c in MAIN}, "task-oracle V family")
summarize({cid(c): max(FAM[:2] + FAM[3:5], key=lambda p: fa_lib2.dev_delta(c, p)) for c in MAIN}, "task-oracle V family, no liquid default")
tot = 0.0
for c in MAIN:
    k = COST[cid(c)]
    dev = c["roles"]["DEV"]
    n = len(dev)
    full = ni_choice(c, "VSV:assembled", 1.0)
    if full == "rigid":
        tot += n * (k.get("rigid") or 0)
        continue
    pf = items_of(c, ("PARETO", "FIT"))
    fire = mean(1 if pol(it, "VSV:assembled") != pol(it, "Vassembled+") else 0 for it in pf)
    if fire < 0.02:
        tot += n * (k.get("assembled") or 0)
    else:
        need = mean(0 if ("rigid" in it["alive"] and "assembled" in it["alive"] and it["ft"]["k"].get("rigid") is not None
                          and it["ft"]["k"]["rigid"] == it["ft"]["k"].get("assembled")) else 1 for it in dev)
        tot += n * ((k.get("rigid") or 0) + (k.get("assembled") or 0) + need * (k.get("liquid") or 0))
print(f"one TEST-sized pass (n = n_DEV), auto-lite configuration, 36 cells: {tot:.1f} USD")

