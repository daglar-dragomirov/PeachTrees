"""B5: cost per item of every form and of the judge (DEV), from the runs' own summaries; cost multiples of policies."""
import glob, json, sys
sys.path.insert(0, "/tmp/fable_out")
from fa_lib2 import *
LR = "/root/.local/share/openresearch/local-runs/"
SRC = {"j6h": "b717bff1*/repo/runs/fieldsuite-v04-v5h", "j6v": "4e2148f3*/repo/runs/fieldsuite-v04-v5v", "j6i": "f6848839*/repo/runs/fieldsuite-v04-v7i",
       "j6p": "3dbb0640*/repo/runs/fieldsuite-v04-v7p", "j6a": "a80cb339*/repo/runs/fieldsuite-v04-v6a", "j6g": "103bd160*/repo/runs/fieldsuite-v04-v7g",
       "j6l": "aa9030ff*/repo/runs/fieldsuite-v04-v7l", "j6c": "89883441*/repo/runs/fieldsuite-v04-v7c", "j7b": "4fe546a3*/repo/runs/fieldsuite-v04-v5b",
       "u8j": "c944e12d*/repo/runs/fieldsuite-v04-u8a"}
COST = {}
print("cell | n(P,F,D) | usd/item DEV: rigid liquid assembled judge | multiples of rigid: asm, liq, judge | run usd")
tot_forms = tot_judge = 0.0
for c in CELLS:
    ui = dict(c["usd_item"]["DEV"] or {})
    src = None
    if c["name"] in SRC:
        p = glob.glob(LR + SRC[c["name"]] + "/summary.json")
        if p:
            s = json.load(open(p[0]))["worker"]
            u = s.get("rider_select_universal") or s.get("rider_select_math") or s.get("rider_select") or {}
            if "DEV" in u and u["DEV"].get("usd_per_item_marginal"):
                src = u["DEV"]["usd_per_item_marginal"]
                for k in ("rigid", "liquid", "assembled"):
                    if src.get(k):
                        ui[k] = src[k]
            if c["name"] == "u8j":
                p2 = glob.glob(LR + "f529c751*/repo/runs/fieldsuite-v04-u8b/summary.json")
                if p2:
                    u2 = json.load(open(p2[0]))["worker"].get("rider_select_universal", {})
                    for k in ("rigid", "liquid", "assembled"):
                        v = (u2.get("DEV", {}).get("usd_per_item_marginal") or {}).get(k)
                        if v:
                            ui[k] = v
    COST[cid(c)] = ui
    n = [len(c["roles"][r]) for r in ("PARETO", "FIT", "DEV")]
    r, l, a, j = (ui.get(k) or 0 for k in ("rigid", "liquid", "assembled", "judge"))
    mult = (f"{a/r:5.1f} {l/r:5.1f} {j/r:5.1f}" if r else "   -     -     -")
    print(f"{cid(c):16s} {n} | {r:.5f} {l:.5f} {a:.5f} {j:.5f} | {mult} | {c['usd']}")
json.dump(COST, open("/tmp/fable_out/costs.json", "w"))
print("\nmacro cost multiples vs the optimizer program alone (cells with a rigid cost > 0)")
ok = [c for c in MAIN if (COST[cid(c)].get("rigid") or 0) > 0]
for o in ("gepa", "mipro", "simba", "all"):
    cs = [c for c in ok if o == "all" or c["opt"] == o]
    def mm(fn):
        v = [fn(COST[cid(c)]) / COST[cid(c)]["rigid"] for c in cs]
        return sum(v) / len(v), sorted(v)[len(v) // 2]
    a = mm(lambda u: u["assembled"])
    b = mm(lambda u: u["assembled"] + u["liquid"])
    f = mm(lambda u: u["rigid"] + u["assembled"] + u["liquid"])
    g = mm(lambda u: u["rigid"] + u["assembled"] + u["liquid"] + u.get("judge", 0))
    print(f"{o:6s} n={len(cs)} assembled-only mean {a[0]:.1f}x median {a[1]:.1f}x | assembled+liquid (draft shared) {b[0]:.1f}x / {b[1]:.1f}x | 3 forms as run {f[0]:.1f}x / {f[1]:.1f}x | + judge {g[0]:.1f}x / {g[1]:.1f}x")
print("\ntotal USD of the 36 main runs (stock client):", round(sum(c["usd"] or 0 for c in MAIN), 2))

