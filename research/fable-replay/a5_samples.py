import glob, json, os
LR = "/root/.local/share/openresearch/local-runs/"
SRC = {"hotpotqa": "b717bff1*/repo/runs/fieldsuite-v04-v5h", "hover": "4e2148f3*/repo/runs/fieldsuite-v04-v5v", "ifbench": "f6848839*/repo/runs/fieldsuite-v04-v7i",
       "pupa": "3dbb0640*/repo/runs/fieldsuite-v04-v7p", "aime": "a80cb339*/repo/runs/fieldsuite-v04-v6a", "gpqa": "103bd160*/repo/runs/fieldsuite-v04-v7g",
       "livebench": "aa9030ff*/repo/runs/fieldsuite-v04-v7l", "lcb": "89883441*/repo/runs/fieldsuite-v04-v7c", "bfcl": "4fe546a3*/repo/runs/fieldsuite-v04-v5b",
       "natplan": "723fdbec*/repo/runs/fieldsuite-v04-ptnp", "toolhop": "05b62d8b*/repo/runs/fieldsuite-v04-ptth"}
for ds, pat in SRC.items():
    w = glob.glob(LR + pat + "/worker")[0]
    print("=====", ds, sorted(os.path.basename(p) for p in glob.glob(w + "/eval-selu-DEV-*.jsonl")))
    for f in ("rigid", "liquid", "assembled"):
        rows = [json.loads(l) for l in open(w + f"/eval-selu-DEV-{f}.jsonl")]
        x = rows[3]
        tr = x.get("trajectory") or {}
        print(f"  [{f}] keys={list(x.keys())} score={x['score']} err={str(x.get('error'))[:80]} answer={json.dumps(x.get('answer'))[:260]}")
        print("      traj:", {k: (len(v) if isinstance(v, (str, list, dict)) else v) for k, v in tr.items()})
        for k, v in tr.items():
            if k in ("answer", "reasoning") or v in (None, ""):
                continue
            print(f"      traj[{k}]: {json.dumps(v)[:300]}")
        if f != "rigid":
            r = str(tr.get("reasoning") or "")
            print("      reasoning tail:", json.dumps(r[-500:]))

