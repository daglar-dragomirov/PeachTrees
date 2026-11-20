import sys
sys.path.insert(0, "/tmp/fable_out")
from fa_lib import *
print("cell | n | rigid liquid assembled vote3 oracle | default(lite) full(judge) reported | gate | modes")
agg = {}
for c in CELLS:
    dev = c["roles"]["DEV"]
    m = {f: mean(sc(it, f) for it in dev) for f in FORMS + ("vote3", "oracle")}
    lite = mean(it["s"][it["ref"]] for it in dev)
    full = mean(it["s"][it["form"]] for it in dev)
    rep = mean(reported(c, it) for it in dev)
    modes = {}
    for it in dev:
        k = it["mode"].split()[0]
        modes[k] = modes.get(k, 0) + 1
    sw = [it for it in dev if it["form"] != it["ref"]]
    won = sum(1 for it in sw if it["s"][it["form"]] > it["s"][it["ref"]])
    lost = sum(1 for it in sw if it["s"][it["form"]] < it["s"][it["ref"]])
    # the judge's suppressed proposals
    bc = [it for it in dev if it["mode"] == "below_confidence" and it.get("prop")]
    bwon = sum(1 for it in bc if it["s"][it["prop"]] > it["s"][it["ref"]])
    blost = sum(1 for it in bc if it["s"][it["prop"]] < it["s"][it["ref"]])
    dflt = c["summary_default"]["DEV"]
    print(f"{cid(c):16s} {len(dev):3d} | {m['rigid']:.3f} {m['liquid']:.3f} {m['assembled']:.3f} {m['vote3']:.3f} {m['oracle']:.3f} | "
          f"{dflt:9s} {lite:.3f} {full:.3f} {rep:.3f} | gate={int(c['_gate'])} thr={(c['judge_threshold'] or {}).get('min_confidence')} "
          f"sw={len(sw)} w/l={won}/{lost} supp={len(bc)} w/l={bwon}/{blost} | {modes}")
    a = agg.setdefault(c["opt"], {})
    for k, v in (("liquid", m["liquid"]), ("assembled", m["assembled"]), ("vote3", m["vote3"]), ("oracle", m["oracle"]),
                 ("lite", lite), ("full", full), ("reported", rep)):
        a.setdefault(k, []).append(v - m["rigid"])
print()
for o, a in agg.items():
    print(o, "n_cells", len(a["lite"]), " ".join(f"{k}: mean {100*mean(v):+.2f} worst {100*min(v):+.2f}" for k, v in a.items()))

