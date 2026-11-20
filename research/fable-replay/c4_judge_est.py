"""C4: what a per-item judge can still add AFTER the free verify -> vote rule. Uses only the recorded J6* decisions:
on contested items (no majority) where the judge's reference form equals the new policy's choice, count proposals won /
lost and the improvable items; extrapolate to full coverage. Split into verifiable datasets (a tool can check an answer)
and rubric / retrieval datasets (hover, ifbench, pupa, tau2, bfcl)."""
import sys
sys.path.insert(0, "/tmp/fable_out")
from fa_lib3 import *
import fa_lib2
VERIF = ("natplan", "lcb", "bird", "aime", "gpqa", "livebench", "toolhop", "hotpotqa")
BASE = sys.argv[1] if len(sys.argv) > 1 else "VSV:assembled"


def contested(it):
    alive = vf_alive(it)
    g = [[f for f in grp if f in alive] for grp in it["sg"]]
    g = [x for x in g if x]
    return len(g) >= 2 and max(len(x) for x in g) < 2


def prop_of(it):
    return it.get("prop") if it["mode"] == "below_confidence" else it["form"]


tot = {}
print(f"base policy: NI rule, prior {BASE}; DEV; contested = no majority after verify -> vote")
print("cell | base gain | contested share | improvable within contested (pp of DEV) | judge coverage | won lost (covered, contested) | est. net gain at full coverage (pp)")
for c in MAIN:
    base = ni_choice(c, BASE, 1.0)
    dev = c["roles"]["DEV"]
    n = len(dev)
    cont = [it for it in dev if contested(it)] if base != "rigid" else [it for it in dev if len(it["sg"]) >= 2]
    imp = sum(max(it["s"].values()) - psc(it, base) for it in cont)
    cov_items = [it for it in cont if it["ref"] == pol(it, base)]
    w = sum(1 for it in cov_items if prop_of(it) and prop_of(it) != it["ref"] and it["s"][prop_of(it)] > it["s"][it["ref"]] + 1e-9)
    l = sum(1 for it in cov_items if prop_of(it) and prop_of(it) != it["ref"] and it["s"][prop_of(it)] < it["s"][it["ref"]] - 1e-9)
    net_cov = sum(it["s"][prop_of(it)] - it["s"][it["ref"]] for it in cov_items if prop_of(it) and prop_of(it) != it["ref"])
    cov = len(cov_items) / len(cont) if cont else 0.0
    est = (net_cov / cov / n) if cov > 0 else 0.0
    grp = "verifiable" if c["ds"] in VERIF else "rubric"
    t = tot.setdefault(grp, {"imp": 0.0, "est": 0.0, "w": 0, "l": 0, "n": 0, "cells": 0, "estpos": 0.0})
    t["imp"] += imp / n; t["est"] += est; t["w"] += w; t["l"] += l; t["cells"] += 1; t["estpos"] += max(est, 0.0)
    print(f"{cid(c):16s} {100*fa_lib2.dev_delta(c, base):+6.1f} | {len(cont)/n:.2f} | {100*imp/n:5.1f} | {cov:.2f} | {w:3d} {l:3d} | {100*est:+5.1f}   [{grp}]")
print()
for g, t in tot.items():
    print(f"{g:10s} cells {t['cells']:2d}: improvable (contested) mean {100*t['imp']/t['cells']:.2f} pp/cell; recorded judge won {t['w']} lost {t['l']} (precision {t['w']/max(1,t['w']+t['l']):.2f}); "
          f"est. net at full coverage: mean {100*t['est']/t['cells']:+.2f} pp/cell; if harmful cells are gated off: {100*t['estpos']/t['cells']:+.2f} pp/cell")
allc = sum(t["cells"] for t in tot.values())
print(f"macro over 36 cells if the judge runs only on verifiable datasets (gated): {100*tot['verifiable']['estpos']/allc:+.2f} pp; ungated {100*tot['verifiable']['est']/allc:+.2f} pp")
print(f"macro over 36 cells, upper bound (all improvable contested items recovered, verifiable datasets): {100*tot['verifiable']['imp']/allc:+.2f} pp; all datasets: {100*(tot['verifiable']['imp']+tot['rubric']['imp'])/allc:+.2f} pp")

