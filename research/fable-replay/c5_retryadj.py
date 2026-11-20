"""C5: how much of the gain is 'rescue of the program's own parse failures' (rows where the optimizer's program returned
no parsable output and scored 0)? A baseline with a simple retry would recover most of those rows. Conservative
adjustment: impute the program's dead rows with its accuracy on its alive rows in the same cell, leave the policy as is.
Also: the number of failed rows per form (the cost of a parse-failure repair run)."""
import json, sys
sys.path.insert(0, "/tmp/fable_out")
from fa_lib3 import *
import fa_lib2
COST = json.load(open("/tmp/fable_out/costs.json"))
PRIOR = "VSV:assembled"
tot = {"rep": [], "rep_adj": [], "new": [], "new_adj": []}
byo = {}
rep_cost = 0.0
print("cell | rigid dead share DEV | rigid, rigid imputed | reported gain -> adj | new rule gain -> adj | dead rows P+F+DEV r/l/a | repair USD")
for c in MAIN:
    dev = c["roles"]["DEV"]
    n = len(dev)
    dead = [it for it in dev if not it["ft"]["alive"].get("rigid")] if c["name"] != "u8j" else []
    alive = [it for it in dev if it not in dead]
    r = mean(it["s"]["rigid"] for it in dev)
    ra = mean(it["s"]["rigid"] for it in alive) if alive else 0.0
    r_imp = r + len(dead) / n * ra  # dead rows scored 0 now
    pol_ = ni_choice(c, PRIOR, 1.0)
    new = mean(psc(it, pol_) for it in dev)
    rep = mean(reported(c, it) for it in dev)
    d = {f: sum(1 for role in ("PARETO", "FIT", "DEV") for it in c["roles"][role] if not it["ft"]["alive"].get(f)) for f in FORMS} if c["name"] != "u8j" else {f: 0 for f in FORMS}
    k = COST[cid(c)]
    usd = sum(d[f] * (k.get(f) or 0) for f in FORMS) * 1.5
    rep_cost += usd
    tot["rep"].append(rep - r); tot["rep_adj"].append(rep - r_imp); tot["new"].append(new - r); tot["new_adj"].append(new - r_imp)
    b = byo.setdefault(c["opt"], {"new": [], "new_adj": [], "rep": [], "rep_adj": []})
    b["new"].append(new - r); b["new_adj"].append(new - r_imp); b["rep"].append(rep - r); b["rep_adj"].append(rep - r_imp)
    if dead or max(d.values()) > 0:
        print(f"{cid(c):16s} {len(dead)/n:.3f} | {r:.3f} {r_imp:.3f} | {100*(rep-r):+5.1f} -> {100*(rep-r_imp):+5.1f} | {100*(new-r):+5.1f} -> {100*(new-r_imp):+5.1f} | {d['rigid']}/{d['liquid']}/{d['assembled']} | {usd:.2f}")
print()
for k in ("rep", "rep_adj", "new", "new_adj"):
    print(f"{k:8s} mean {100*mean(tot[k]):+.2f} worst {100*min(tot[k]):+.2f}")
for o, b in byo.items():
    print(o, " ".join(f"{k} {100*mean(v):+.2f}" for k, v in b.items()))
print(f"estimated cost of re-running only the failed rows (x1.5 for repeated retries): {rep_cost:.2f} USD")

