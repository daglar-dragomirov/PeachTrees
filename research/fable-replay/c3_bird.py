"""C3: BIRD with label-free execution signals computed offline from the saved SQL (no model calls, gold never run):
P(correct | the query runs / returns rows), agreement by RESULT SET instead of by SQL text, and the policies built on it."""
import sys
sys.path.insert(0, "/tmp/fable_out")
from fa_lib3 import *
import fa_lib3
B = [c for c in CELLS if c["ds"] == "bird"]
for c in B:
    print("==", cid(c))
    for f in FORMS:
        d = {"error": [], "empty": [], "allnull": [], "rows": []}
        for role in ("PARETO", "FIT", "DEV"):
            for it in c["roles"][role]:
                e = (it["ft"].get("exec") or {}).get(f)
                if e is None:
                    continue
                k = "error" if not e["ok"] else "empty" if e["n"] == 0 else "allnull" if e.get("allnull") else "rows"
                d[k].append(it["s"][f])
        print(f"  {f:9s} " + " | ".join(f"{k}: n={len(v)} acc={mean(v):.3f}" for k, v in d.items()))
    for role in ("PARETO", "FIT", "DEV"):
        items = c["roles"][role]
        pats = {}
        for it in items:
            pats[spattern(it)] = pats.get(spattern(it), 0) + 1
        line = f"  {role:6s} n={len(items)} patterns {dict(sorted(pats.items()))} |"
        for p in ("rigid", "liquid+", "assembled+", "SV:rigid", "SV:assembled", "VSV:assembled", "oracle"):
            line += f" {p}={mean(psc(it, p) for it in items):.3f}"
        print(line)
    fa_lib3.OPT["bird_empty"] = True; fa_lib3.reset_cache()
    for role in ("PARETO", "FIT", "DEV"):
        items = c["roles"][role]
        print(f"  {role:6s} with the non-empty filter: " + " ".join(f"{p}={mean(psc(it, p) for it in items):.3f}" for p in ("Vassembled+", "VSV:assembled", "VSV:rigid")))
    fa_lib3.OPT["bird_empty"] = False; fa_lib3.reset_cache()
    # by-pattern accuracy on DEV with execution keys
    dev = c["roles"]["DEV"]
    for p in ("ALL", "RL|A", "RA|L", "LA|R", "R|L|A", "DEAD"):
        its = [it for it in dev if spattern(it) == p]
        if its:
            print(f"    DEV {p:6s} share {len(its)/len(dev):.2f}: r {mean(it['s']['rigid'] for it in its):.2f} l {mean(it['s']['liquid'] for it in its):.2f} a {mean(it['s']['assembled'] for it in its):.2f} oracle {mean(max(it['s'].values()) for it in its):.2f}")

