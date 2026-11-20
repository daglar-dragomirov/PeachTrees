"""D1: the per-cell table for the report (DEV; post hoc for the new rule) and aggregates. Markdown output."""
import json, sys
sys.path.insert(0, "/tmp/fable_out")
from fa_lib3 import *
import fa_lib2
COST = json.load(open("/tmp/fable_out/costs.json"))
PRIOR, LITE = "VSV:assembled", "Vassembled+"
rows = []
for c in CELLS:
    dev = c["roles"]["DEV"]
    n = len(dev)
    m = {f: mean(it["s"][f] for it in dev) for f in FORMS}
    rep = mean(reported(c, it) for it in dev)
    lite02 = mean(it["s"][it["ref"]] for it in dev)
    pf = items_of(c, ("PARETO", "FIT"))
    mm, se = fa_lib2.pstats(pf, PRIOR, "rigid")
    full = ni_choice(c, PRIOR, 1.0)
    lite = ni_choice(c, LITE, 1.0)
    full_all = ni_choice(c, PRIOR, 1.0, roles=("PARETO", "FIT", "DEV"))
    d_full = mean(psc(it, full) - it["s"]["rigid"] for it in dev)
    d_lite = mean(psc(it, lite) - it["s"]["rigid"] for it in dev)
    lo, hi = boot_ci(dev, lambda it: psc(it, full) - it["s"]["rigid"], n=2000)
    lo2, hi2 = boot_ci(dev, lambda it: psc(it, full) - reported(c, it), n=2000)
    pats = [spattern(it) for it in dev]
    sh = lambda p: sum(1 for x in pats if x == p) / n
    dead_r = mean(0 if (it.get("ft") or {"alive": {"rigid": 1}})["alive"].get("rigid") else 1 for it in dev)
    alive_acc = mean(it["s"]["rigid"] for it in dev if (it.get("ft") or {"alive": {"rigid": 1}})["alive"].get("rigid"))
    r_imp = m["rigid"] + dead_r * alive_acc
    rows.append({"cell": cid(c), "opt": c["opt"], "ds": c["ds"], "n": [len(c["roles"][r]) for r in ("PARETO", "FIT", "DEV")],
                 "rigid": m["rigid"], "liquid": m["liquid"], "assembled": m["assembled"], "v02_default": c["summary_default"]["DEV"],
                 "gate": c["_gate"], "thr": (c["judge_threshold"] or {}).get("min_confidence"), "reported": rep - m["rigid"],
                 "lite02": lite02 - m["rigid"], "pf_mean": mm, "pf_se": se, "full": full, "d_full": d_full, "ci": [lo, hi],
                 "lite": lite, "d_lite": d_lite, "vs_rep_ci": [lo2, hi2], "oracle": mean(max(it["s"].values()) for it in dev) - m["rigid"],
                 "pat": [sh("ALL"), sh("RL|A") + sh("RA|L") + sh("LA|R"), sh("R|L|A"), sh("DEAD")], "full_all": full_all,
                 "d_adj": mean(psc(it, full) for it in dev) - r_imp, "rep_adj": rep - r_imp, "dead_r": dead_r,
                 "usd": c["usd"]})
json.dump(rows, open("/tmp/fable_out/d1_rows.json", "w"))
print("| cell | n P/F/DEV | rigid | liquid | asm | v0.2 default (gate) | reported | 1.0-lite | 1.0-full | 95% CI | vs reported CI | retry-adj | oracle | PF evidence (mean/se) | agree ALL/2v1/none/dead |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for r in rows:
    print(f"| {r['cell']} | {r['n'][0]}/{r['n'][1]}/{r['n'][2]} | {r['rigid']:.3f} | {r['liquid']:.3f} | {r['assembled']:.3f} | {r['v02_default']} ({'on' if r['gate'] else 'off'}) | {100*r['reported']:+.1f} | "
          f"{100*r['d_lite']:+.1f} | {100*r['d_full']:+.1f}{'' if r['full'] != 'rigid' else ' (rigid)'} | [{100*r['ci'][0]:+.1f}, {100*r['ci'][1]:+.1f}] | [{100*r['vs_rep_ci'][0]:+.1f}, {100*r['vs_rep_ci'][1]:+.1f}] | {100*r['d_adj']:+.1f} | {100*r['oracle']:+.1f} | "
          f"{100*r['pf_mean']:+.1f}/{100*r['pf_se']:.1f} | {r['pat'][0]:.2f}/{r['pat'][1]:.2f}/{r['pat'][2]:.2f}/{r['pat'][3]:.2f} |")
print()
print("| group | cells | reported | v0.2 lite | 1.0-lite | 1.0-full | 1.0-full retry-adj | oracle | worst cell (1.0-full) |")
print("|---|---|---|---|---|---|---|---|---|")
for o in ("gepa", "mipro", "simba", "ALL36", "gepa1"):
    rs = [r for r in rows if (r["opt"] == o) or (o == "ALL36" and r["opt"] != "gepa1")]
    f = lambda k: 100 * mean(r[k] for r in rs)
    print(f"| {o} | {len(rs)} | {f('reported'):+.2f} | {f('lite02'):+.2f} | {f('d_lite'):+.2f} | {f('d_full'):+.2f} | {f('d_adj'):+.2f} | {f('oracle'):+.2f} | {100*min(r['d_full'] for r in rs):+.2f} |")
print()
print("| dataset | optimizers | reported | 1.0-lite | 1.0-full | oracle |")
print("|---|---|---|---|---|---|")
for ds in sorted({r["ds"] for r in rows}):
    rs = [r for r in rows if r["ds"] == ds and r["opt"] != "gepa1"]
    f = lambda k: 100 * mean(r[k] for r in rs)
    print(f"| {ds} | {len(rs)} | {f('reported'):+.1f} | {f('d_lite'):+.1f} | {f('d_full'):+.1f} | {f('oracle'):+.1f} |")
print()
print("cells where the choice changes if DEV joins the selection data (the TEST-time protocol):", [(r["cell"], r["full"], r["full_all"]) for r in rows if r["full"] != r["full_all"]])
sig = [r["cell"] for r in rows if r["opt"] != "gepa1" and r["ci"][0] > 0]
print("1.0-full significantly above the program (CI lower > 0):", len(sig), "of 36")
sig2 = [r["cell"] for r in rows if r["opt"] != "gepa1" and r["vs_rep_ci"][0] > 0]
neg2 = [r["cell"] for r in rows if r["opt"] != "gepa1" and r["vs_rep_ci"][1] < 0]
print("1.0-full significantly above the reported v0.2:", sig2, "| significantly below:", neg2)
below = [(r["cell"], round(100 * (r["d_full"] - r["reported"]), 1)) for r in rows if r["d_full"] < r["reported"] - 1e-9]
print("cells where 1.0-full is below reported (point estimate):", below)

