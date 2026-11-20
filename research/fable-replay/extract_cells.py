"""Fable analysis: build one compact file with every PeachTrees cell (optimizer x dataset): per role, per item scores of
each form, answer-equivalence groups, the judge's recorded decision. Read-only on run dirs; writes /tmp/fable_out/cells.json."""
import glob, json, os
LR = "/root/.local/share/openresearch/local-runs/"
CELLS = [  # (optimizer, dataset, output, run-id prefix or None)
 ("gepa","hotpotqa","j6h",None),("gepa","hover","j6v",None),("gepa","ifbench","j6i",None),("gepa","pupa","j6p",None),
 ("gepa","aime","j6a",None),("gepa","gpqa","j6g",None),("gepa","livebench","j6l",None),("gepa","lcb","j6c",None),
 ("gepa","bfcl","j7b",None),("gepa","tau2","u8j",None),("gepa","natplan","ptnp",None),("gepa","bird","ptbr",None),
 ("gepa","toolhop","ptth",None),
 ("gepa1","livebench","pt1l",None),("gepa1","ifbench","pt1i",None),("gepa1","hotpotqa","pt1h",None),
 ("mipro","aime","ptma",None),("mipro","gpqa","ptmg",None),("mipro","livebench","ptml",None),("mipro","hotpotqa","ptmh",None),
 ("mipro","lcb","ptmc",None),("mipro","natplan","ptmnp",None),("mipro","bird","ptmbr",None),("mipro","toolhop","ptmth",None),
 ("mipro","ifbench","ptmi",None),("mipro","hover","ptmv",None),("mipro","pupa","ptmp","ac87499a"),
 ("simba","aime","ptsa",None),("simba","gpqa","ptsg",None),("simba","livebench","ptsl2",None),("simba","hotpotqa","ptsh",None),
 ("simba","lcb","ptsc",None),("simba","natplan","ptsnp",None),("simba","bird","ptsbr",None),("simba","toolhop","ptsth",None),
 ("simba","ifbench","ptsi",None),("simba","hover","ptsv",None),("simba","pupa","ptsp","b6699861"),("simba","bfcl","ptsb","cc9dd01f"),
]
out = []
for opt, ds, name, rid in CELLS:
    ws = sorted(glob.glob(LR + f"{rid or ''}*/repo/runs/fieldsuite-v04-{name}/worker"))
    ws = [w for w in ws if os.path.exists(w + "/picks-DEV.jsonl")]
    assert len(ws) == 1, (name, ws)
    w = ws[0]
    run = w[len(LR):].split("/")[0]
    summ = json.load(open(os.path.dirname(w) + "/summary.json"))
    wk = summ["worker"]
    u = wk["rider_select_universal"]
    cell = {"opt": opt, "ds": ds, "name": name, "run": run, "roles": {}, "judge_threshold": wk.get("judge_threshold"),
            "v02_choice": wk.get("v02_choice"), "usd": (wk.get("stock_client") or {}).get("usd"),
            "ledger": {k: wk.get("ledger", {}).get(k) for k in ("spent_billed_usd", "spent_table_usd")},
            "usd_item": {r: u[r].get("usd_per_item_marginal") for r in u},
            "summary_default": {r: u[r].get("default") for r in u},
            "inherit": "Guidance learned for this task by an optimizer" in json.dumps(wk.get("universal_agent_instructions", {})),
            "has_examples": "Correct final outputs for other inputs" in json.dumps(wk.get("universal_agent_instructions", {}))}
    for role in ("PARETO", "FIT", "DEV"):
        items = []
        for l in open(w + f"/picks-{role}.jsonl"):
            p = json.loads(l)
            items.append({"uid": p["uid"], "s": p["scores"], "g": p.get("groups"), "ref": p.get("ref"), "form": p["form"],
                          "mode": p["mode"], "prop": p.get("proposed"), "conf": p.get("confidence"), "ch": p.get("choice"),
                          "ch2": p.get("choice_swapped"), "letters": p.get("letters"), "votes": p.get("votes")})
        cell["roles"][role] = items
    out.append(cell)
json.dump(out, open("/tmp/fable_out/cells.json", "w"))
print("cells", len(out), "bytes", os.path.getsize("/tmp/fable_out/cells.json"))
for c in out:
    line = f"{c['opt']:6s} {c['ds']:9s} {c['name']:6s} {c['run'][:8]} inh={int(c['inherit'])} ex={int(c['has_examples'])} usd={c['usd']} thr={(c['judge_threshold'] or {}).get('min_confidence')}"
    for role in ("PARETO", "FIT", "DEV"):
        it = c["roles"][role]
        forms = list(it[0]["s"])
        m = {f: sum(x["s"][f] for x in it) / len(it) for f in forms}
        orc = sum(max(x["s"].values()) for x in it) / len(it)
        line += f" | {role[0]} n={len(it)} " + " ".join(f"{f[0]}={m[f]:.3f}" for f in forms) + f" o={orc:.3f} ref={it[0]['ref']}"
    print(line)

