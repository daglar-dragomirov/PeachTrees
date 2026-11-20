"""PeachTrees 1.0 P2: replay of the frozen 1.0 rule (src/rider4d/peachtrees_v1.py) over the saved form outputs of the 39
cells; with --repaired, the rows of the P3 parse-failure repair runs replace the saved rows of their cells (per
role and form, the newest repair run that wrote the merged file: p3<name>, then the narrowed p3r<name>). Selection
on PARETO + FIT only; DEV is reported once per cell. No model call; TEST never read.
With --with-dev the NI task decision uses PARETO + FIT + DEV (the TEST protocol, Fable 3.5).
Usage: p2_replay.py [--repaired] [--with-dev] OUT.json"""
import glob, json, sys
from pathlib import Path
sys.path.insert(0, "/root/projects/rider-4d/src")
SROLES = ("PARETO", "FIT", "DEV") if "--with-dev" in sys.argv else ("PARETO", "FIT")
from rider4d.peachtrees_v1 import FORMS, item_view, pi1, lite, ni_use, paired, boot_ci

LR = "/root/.local/share/openresearch/local-runs/"
ROOT = Path("/root/projects/rider-4d")
repaired = "--repaired" in sys.argv
OUT = sys.argv[-1]
SRC = {"j6h": "b717bff1*/repo/runs/fieldsuite-v04-v5h", "j6v": "4e2148f3*/repo/runs/fieldsuite-v04-v5v",
       "j6i": "f6848839*/repo/runs/fieldsuite-v04-v7i", "j6p": "3dbb0640*/repo/runs/fieldsuite-v04-v7p",
       "j6a": "a80cb339*/repo/runs/fieldsuite-v04-v6a", "j6g": "103bd160*/repo/runs/fieldsuite-v04-v7g",
       "j6l": "aa9030ff*/repo/runs/fieldsuite-v04-v7l", "j6c": "89883441*/repo/runs/fieldsuite-v04-v7c",
       "j7b": "4fe546a3*/repo/runs/fieldsuite-v04-v5b"}
CELLS = [("gepa", "hotpotqa", "j6h", ""), ("gepa", "hover", "j6v", ""), ("gepa", "ifbench", "j6i", ""), ("gepa", "pupa", "j6p", ""),
         ("gepa", "aime", "j6a", ""), ("gepa", "gpqa", "j6g", ""), ("gepa", "livebench", "j6l", ""), ("gepa", "lcb", "j6c", ""),
         ("gepa", "bfcl", "j7b", ""), ("gepa", "tau2", "u8j", ""), ("gepa", "natplan", "ptnp", ""), ("gepa", "bird", "ptbr", ""),
         ("gepa", "toolhop", "ptth", ""),
         ("gepa1", "livebench", "pt1l", ""), ("gepa1", "ifbench", "pt1i", ""), ("gepa1", "hotpotqa", "pt1h", ""),
         ("mipro", "aime", "ptma", ""), ("mipro", "gpqa", "ptmg", ""), ("mipro", "livebench", "ptml", ""), ("mipro", "hotpotqa", "ptmh", ""),
         ("mipro", "lcb", "ptmc", ""), ("mipro", "natplan", "ptmnp", ""), ("mipro", "bird", "ptmbr", ""), ("mipro", "toolhop", "ptmth", ""),
         ("mipro", "ifbench", "ptmi", ""), ("mipro", "hover", "ptmv", ""), ("mipro", "pupa", "ptmp", "ac87499a"),
         ("simba", "aime", "ptsa", ""), ("simba", "gpqa", "ptsg", ""), ("simba", "livebench", "ptsl2", ""), ("simba", "hotpotqa", "ptsh", ""),
         ("simba", "lcb", "ptsc", ""), ("simba", "natplan", "ptsnp", ""), ("simba", "bird", "ptsbr", ""), ("simba", "toolhop", "ptsth", ""),
         ("simba", "ifbench", "ptsi", ""), ("simba", "hover", "ptsv", ""), ("simba", "pupa", "ptsp", "b6699861"),
         ("simba", "bfcl", "ptsb", "cc9dd01f")]
NP = {}
for role in ("PARETO", "FIT", "DEV"):  # never TEST
    for l in open(ROOT / f".external/fieldsuite-natplan-data-v1/roles-v1/{role}.jsonl"):
        r = json.loads(l)
        NP[r["id"]] = r
BIRD = {}
for r in json.load(open("/tmp/fable_out/bird_exec.json")):
    BIRD[(r["name"], r["role"], r["form"], r["uid"])] = r


def picks_dir(name, rp):
    ws = [w for w in glob.glob(LR + f"{rp}*/repo/runs/fieldsuite-v04-{name}/worker") if Path(w + "/picks-DEV.jsonl").exists()]
    assert len(ws) == 1, (name, ws)
    return ws[0]


def load(path):
    return {json.loads(l)["uid"]: json.loads(l) for l in open(path, encoding="utf-8") if l.strip()}


res, used = [], {}
for opt, ds, name, rp in CELLS:
    pk = picks_dir(name, rp)
    src = glob.glob(LR + SRC[name] + "/worker")[0] if name in SRC else pk
    reps = sorted((w for p in (f"p3{name}", f"p3r{name}", f"p3a{name}") for w in glob.glob(LR + f"*/repo/runs/fieldsuite-v04-{p}/worker")),
                  key=lambda w: Path(w).stat().st_mtime) if repaired else []

    def source(role, f):
        for w in reversed(reps):  # newest first
            if Path(w + f"/eval-selu-{role}-{f}.jsonl").exists():
                used.setdefault(name, {})[f"{role}-{f}"] = w
                return w + f"/eval-selu-{role}-{f}.jsonl"
        return src + f"/eval-selu-{role}-{f}.jsonl"
    items = {}
    for role in ("PARETO", "FIT", "DEV"):
        picks = load(pk + f"/picks-{role}.jsonl")
        if name == "u8j":  # tau2: the worker's own groups and scores (no per-form rows were kept)
            by = {u: ({f: p["scores"][f] for f in FORMS}, None, p.get("groups") or []) for u, p in picks.items()}
        else:
            rows = {f: load(source(role, f)) for f in FORMS}
            assert all(set(rows[f]) == set(picks) for f in FORMS), (name, role)
            by = {u: ({f: rows[f][u]["score"] for f in FORMS}, {f: rows[f][u] for f in FORMS}, None) for u in picks}
        items[role] = []
        for u, (s, rws, groups) in by.items():
            if rws is None:
                v = {"alive": [f for g in groups for f in g], "k": {}, "valid": {}, "pub": {}}
                full, lt = pi1(v, groups), lite(v)
            else:
                bird = {f: BIRD.get((name, role, f, u)) for f in FORMS} if ds == "bird" else None
                v = item_view(ds, rws, NP.get(u) if ds == "natplan" else None, bird)
                full, lt = pi1(v), lite(v)
            items[role].append({"uid": u, "s": s, "full": full, "lite": lt})
    sel = [i for r in SROLES for i in items[r]]
    out = {"opt": opt, "ds": ds, "name": name, "repaired": len(used.get(name, {}))}
    dev = items["DEV"]
    out["rigid_dev"] = sum(i["s"]["rigid"] for i in dev) / len(dev)
    for pol in ("full", "lite"):
        use, m, se = ni_use([(i["uid"], i["s"][i[pol]] - i["s"]["rigid"]) for i in sel])
        d = [(i["uid"], (i["s"][i[pol]] if use else i["s"]["rigid"]) - i["s"]["rigid"]) for i in dev]
        g, _ = paired(d)
        out[pol] = {"use_pi": use, "pf_mean": round(m, 5), "pf_se": round(se, 5), "dev_gain": round(g, 5),
                    "ci95": [round(x, 5) for x in boot_ci(d)]}
    res.append(out)


def macro(rows, pol):
    return 100 * sum(r[pol]["dev_gain"] for r in rows) / len(rows)


main = [r for r in res if r["opt"] != "gepa1"]
print(f"{'cell':18s} rep rigid  | full: use  gain   CI            | lite: use gain")
for r in res:
    f, l = r["full"], r["lite"]
    print(f"{r['opt']+':'+r['ds']:18s} {r['repaired']}  {r['rigid_dev']:.3f} | {int(f['use_pi'])} {100*f['dev_gain']:+6.2f} "
          f"[{100*f['ci95'][0]:+.1f},{100*f['ci95'][1]:+.1f}] | {int(l['use_pi'])} {100*l['dev_gain']:+6.2f}")
for o in ("gepa", "mipro", "simba"):
    rr = [r for r in main if r["opt"] == o]
    print(f"{o:6s} cells {len(rr):2d} full {macro(rr, 'full'):+.2f} lite {macro(rr, 'lite'):+.2f}")
print(f"ALL    cells {len(main):2d} full {macro(main, 'full'):+.2f} lite {macro(main, 'lite'):+.2f} "
      f"worst {100*min(r['full']['dev_gain'] for r in main):+.2f} sig>0 {sum(1 for r in main if r['full']['ci95'][0] > 0)}")
json.dump({"repaired": repaired, "sources": used, "cells": res}, open(OUT, "w"), indent=1)
