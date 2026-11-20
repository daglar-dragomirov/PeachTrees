"""Sealed TEST result of PeachTrees 1.0-lite (the 15 cells of docs/analysis-test-20261120/frozen_decisions.json).
Per cell: the TEST forms run (rigid = the optimizer's program, assembled); the frozen 1.0-lite item rule (assembled, after
liveness and the task checker; the program if assembled has no usable output) where the frozen task decision says so.
Gain = mean over TEST items of score(1.0-lite) - score(program), clustered 95 % bootstrap CI. No model call.
Usage: test_v1.py OUT.json"""
import glob, json, sys
from pathlib import Path
ROOT = Path("/root/projects/rider-4d")
sys.path.insert(0, str(ROOT / "src"))
from rider4d.peachtrees_v1 import item_view, lite, paired, boot_ci

LR = "/root/.local/share/openresearch/local-runs/"
DEC = json.load(open(ROOT / "docs/analysis-test-20261120/frozen_decisions.json"))
NP = {}
for l in open(ROOT / ".external/fieldsuite-natplan-data-v1/sealed-test-v1/TEST.jsonl"):
    r = json.loads(l)
    NP[r["id"]] = r
res = []
for cell, d in DEC.items():
    opt, ds = cell.split(":")
    ws = [w for p in ("t", "tb", "tc", "td") for w in glob.glob(LR + f"*/repo/runs/fieldsuite-v04-{p}{d['name']}/worker")
          if Path(w + "/eval-selu-DEV-assembled.jsonl").exists() and Path(w + "/eval-selu-DEV-rigid.jsonl").exists()]  # tb = rerun after the 01:10 reset, tc = rerun after a budget stop
    if len(ws) != 1:
        res.append({"cell": cell, "status": "missing" if not ws else "ambiguous", "dirs": ws})
        continue
    rows = {f: {json.loads(l)["uid"]: json.loads(l) for l in open(ws[0] + f"/eval-selu-DEV-{f}.jsonl")} for f in ("rigid", "assembled")}
    assert set(rows["rigid"]) == set(rows["assembled"])
    deltas, dead = [], {"rigid": 0, "assembled": 0}
    for u, r in rows["rigid"].items():
        a = rows["assembled"][u]
        v = item_view(ds, {"rigid": r, "assembled": a}, NP.get(u.split(":", 1)[-1]) if ds == "natplan" else None)
        f = lite(v) if d["lite_use"] else "rigid"
        f = f if f in ("rigid", "assembled") else "rigid"
        deltas.append((u, {"rigid": r, "assembled": a}[f]["score"] - r["score"]))
        dead["rigid"] += bool(r.get("error") or not r.get("trajectory"))
        dead["assembled"] += bool(a.get("error") or not a.get("trajectory"))
    n = len(deltas)
    g, _ = paired(deltas)
    rig = sum(x["score"] for x in rows["rigid"].values()) / n
    res.append({"cell": cell, "status": "ok", "n": n, "program": round(rig, 4), "peachtrees_lite": round(rig + g, 4),
                "gain_pp": round(100 * g, 2), "ci95_pp": [round(100 * x, 2) for x in boot_ci(deltas)], "dead": dead,
                "run_dir": ws[0]})
ok = [r for r in res if r["status"] == "ok"]
summary = {"cells_ok": len(ok), "cells_total": len(res)}
for o in ("gepa", "mipro", "simba"):
    v = [r["gain_pp"] for r in ok if r["cell"].startswith(o + ":")]
    summary[o] = {"cells": len(v), "mean_gain_pp": round(sum(v) / len(v), 2) if v else None}
v = [r["gain_pp"] for r in ok]
summary["all"] = {"cells": len(v), "mean_gain_pp": round(sum(v) / len(v), 2) if v else None, "worst_pp": min(v) if v else None,
                  "ci_above_0": sum(1 for r in ok if r["ci95_pp"][0] > 0), "ci_below_0": sum(1 for r in ok if r["ci95_pp"][1] < 0)}
for r in res:
    print(r["cell"], r["status"], r.get("n"), r.get("program"), r.get("peachtrees_lite"), r.get("gain_pp"), r.get("ci95_pp"), r.get("dead"))
print(json.dumps(summary))
json.dump({"summary": summary, "cells": res}, open(sys.argv[1], "w"), indent=1)
