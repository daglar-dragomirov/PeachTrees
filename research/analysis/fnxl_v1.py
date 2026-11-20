"""FNXL: GEPA vs GEPA + PeachTrees 1.0 from the saved forms run (FNXp). The frozen 1.0 rule (src/rider4d/peachtrees_v1.py):
task rule NI on PARETO + FIT (margin 1.0 se), item rule liveness -> task-agnostic vote (generic text key; FNXL has no
task checker) -> assembled. Reported on DEV (= the FLARE test 318): mean per-item FNXL score and the apo macro-F1.
No model call. Usage: fnxl_v1.py OUT.json"""
import glob, json, sys
from pathlib import Path
ROOT = Path("/root/projects/rider-4d")
sys.path.insert(0, str(ROOT / "src"))
from rider4d.peachtrees_v1 import FORMS, item_view, pi1, lite, ni_use, paired, boot_ci

src = (ROOT / "src/rider4d/fieldsuite_worker_v90.py").read_text()
ns = {}
exec(src[src.index("def fnxl_parse_labels"):src.index("class Fnxl:")], ns)
LR = "/root/.local/share/openresearch/local-runs/"
w = [p for p in glob.glob(LR + "*/repo/runs/fieldsuite-v04-fnxq/worker") if Path(p + "/eval-selu-DEV-assembled.jsonl").exists()]
assert len(w) == 1, w
w = w[0]
labels = {}
for role in ("PARETO", "FIT", "DEV"):
    for l in open(ROOT / f".external/fieldsuite-fnxl-data-v1/roles-v1/{role}.jsonl"):
        r = json.loads(l)
        labels["fnxl:" + r["id"]] = r["labels"]
items = {}
for role in ("PARETO", "FIT", "DEV"):
    rows = {f: {json.loads(l)["uid"]: json.loads(l) for l in open(w + f"/eval-selu-{role}-{f}.jsonl")} for f in FORMS}
    items[role] = []
    for u in rows["rigid"]:
        rw = {f: rows[f][u] for f in FORMS}
        v = item_view("fnxl", rw)
        items[role].append({"uid": u, "s": {f: rw[f]["score"] for f in FORMS},
                            "a": {f: str((rw[f].get("trajectory") or {}).get("answer") or "") for f in FORMS},
                            "dead": {f: bool(rw[f].get("error") or not rw[f].get("trajectory")) for f in FORMS},
                            "full": pi1(v), "lite": lite(v)})
sel = items["PARETO"] + items["FIT"]
dev = items["DEV"]
out = {"run_dir": w, "n": {r: len(v) for r, v in items.items()}}
for role, its in items.items():
    out.setdefault("forms_mean", {})[role] = {f: round(sum(i["s"][f] for i in its) / len(its), 5) for f in FORMS}
    out.setdefault("dead", {})[role] = {f: sum(i["dead"][f] for i in its) for f in FORMS}
lab = [labels[i["uid"]] for i in dev]
out["gepa_dev"] = {"item_mean": round(sum(i["s"]["rigid"] for i in dev) / len(dev), 5),
                   **{k: round(v, 5) for k, v in ns["fnxl_macro_f1"]([i["a"]["rigid"] for i in dev], lab).items()}}
for pol in ("full", "lite"):
    use, m, se = ni_use([(i["uid"], i["s"][i[pol]] - i["s"]["rigid"]) for i in sel])
    ch = [i[pol] if use else "rigid" for i in dev]
    d = [(i["uid"], i["s"][c] - i["s"]["rigid"]) for i, c in zip(dev, ch)]
    g, _ = paired(d)
    mf = ns["fnxl_macro_f1"]([i["a"][c] for i, c in zip(dev, ch)], lab)
    out["peachtrees_" + pol] = {"use_pi": use, "pf_mean": round(m, 5), "pf_se": round(se, 5),
                                "item_mean": round(sum(i["s"][c] for i, c in zip(dev, ch)) / len(dev), 5),
                                "gain_item_pp": round(100 * g, 2), "ci95_pp": [round(100 * x, 2) for x in boot_ci(d)],
                                "picks": {f: ch.count(f) for f in FORMS},
                                **{k: round(v, 5) for k, v in mf.items()}}
out["forms_dev_macro_f1"] = {f: round(ns["fnxl_macro_f1"]([i["a"][f] for i in dev], lab)["macro_f1"], 5) for f in FORMS}
print(json.dumps(out, indent=1))
json.dump(out, open(sys.argv[1], "w"), indent=1)
