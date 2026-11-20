"""B7: compute-matched baselines from the KM runs (the GEPA program sampled k times): SC@k on DEV with cost, and the
B2 judge-over-3-samples numbers, for comparison with the proposed policies at equal cost."""
import glob, json, re, sys
sys.path.insert(0, "/tmp/fable_out")
from fa_lib import cluster, mean
LR = "/root/.local/share/openresearch/local-runs/"


def math_norm(a):
    s = str(a or "").strip()
    m = re.findall(r"\\boxed\{(.*)\}", s)
    if m:
        s = m[-1]
    s = s.replace("$", "").replace("\\left", "").replace("\\right", "").replace("\\!", "").replace(" ", "").strip().rstrip(".")
    s = re.sub(r"\\[dt]?frac", r"\\frac", s)
    if re.fullmatch(r"-?\d+", s):
        s = str(int(s))
    return s.lower()


def gl(a):
    s = str(a or "").strip()
    s = re.sub(r"^(final\s+)?answer\s*[:=]?\s*", "", s, flags=re.I)
    m = re.match(r"^[\s(\[*]*([ABCD])(?:[\s).\]:*]|$)", s)
    return m.group(1) if m else s.lower()


for name, key in (("kma", math_norm), ("kmg", gl), ("kml", math_norm)):
    w = glob.glob(LR + f"*/repo/runs/fieldsuite-v04-{name}/worker")[0]
    summ = json.load(open(w + "/../summary.json"))["worker"]
    u = summ["rider_select_universal"]["DEV"]
    files = sorted(glob.glob(w + "/eval-selu-DEV-rigid*.jsonl"), key=lambda p: int(re.search(r"rigid(\d*)\.jsonl", p).group(1) or 1))
    samples = []
    for p in files:
        samples.append({json.loads(l)["uid"]: json.loads(l) for l in open(p)})
    uids = list(samples[0])
    cost1 = mean([v for k, v in u["usd_per_item_marginal"].items()])
    line = f"{name}: k={len(samples)} usd/item per sample {cost1:.5f} | "
    for k in range(1, len(samples) + 1):
        acc = []
        for uid in uids:
            votes = {}
            for s in samples[:k]:
                x = s[uid]
                if x.get("error") or not x.get("trajectory"):
                    continue
                kk = key((x.get("trajectory") or {}).get("answer"))
                votes.setdefault(kk, []).append(x["score"])
            if not votes:
                acc.append(0.0)
                continue
            best = max(votes.values(), key=len)  # first-seen answer wins ties (dict order)
            acc.append(best[0])
        line += f"SC@{k} {mean(acc):.3f}  "
    print(line)
for name in ("b2a", "b2g", "b2l"):
    w = glob.glob(LR + f"*/repo/runs/fieldsuite-v04-{name}/worker")[0]
    summ = json.load(open(w + "/../summary.json"))["worker"]
    u = summ["rider_select_universal"]["DEV"]
    print(name, "states", {k: v["score_mean"] for k, v in u["states"].items()}, "selected", u["selected"]["score_mean"], "oracle", u["oracle_best_of_forms"], "usd/item", u["usd_per_item_marginal"])

