import glob, json, os
LR = "/root/.local/share/openresearch/local-runs/"
names = ["j6h","j6v","j6i","j6p","j6a","j6g","j6l","j6c","j7b","u8j","ptnp","ptbr","ptth","pt1l","ptma","ptsa","ptmth","ptmc","ptsc","ptmv"]
for n in names:
    ws = sorted(glob.glob(LR + f"*/repo/runs/fieldsuite-v04-{n}"))
    ws = [w for w in ws if os.path.exists(w + "/worker/picks-DEV.jsonl")]
    w = ws[-1]
    run = w[len(LR):].split("/")[0]
    repo = LR + run + "/repo"
    # find the contract used: configs/operational/*<name>*.json in the run's repo copy
    cs = [p for p in glob.glob(repo + "/configs/operational/*.json") if f"-{n}-" in os.path.basename(p) or os.path.basename(p).endswith(f"-{n}.json") or f"v04-{n}" in os.path.basename(p)]
    print("==", n, run[:8], [os.path.basename(p) for p in cs][:3])
    for p in cs[:1]:
        c = json.load(open(p))
        sel = c.get("select", {})
        print("   select:", json.dumps({k: (v if k != "judge_instructions" else "<text>") for k, v in sel.items()})[:900])
        print("   rev9:", json.dumps({k: (v if not isinstance(v, str) or len(v) < 80 else v[:60] + "...") for k, v in c.get("rev9", {}).items()})[:500])
        print("   benchmark:", json.dumps({k: v for k, v in c.get("benchmark", {}).items() if k in ("name", "roles_dir", "db_dir", "samples_dir", "data_dir")})[:500])
        print("   models/worker:", json.dumps(c.get("models", c.get("lm", {})))[:400])
        print("   rigid_from:", json.dumps(c.get("rigid_from"))[:300], "| stock:", c.get("stock_client"), "| threads:", c.get("threads") or c.get("max_workers"))

