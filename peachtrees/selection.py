"""Model-free decision rules of PeachTrees: the task-level default form, the judge's confidence threshold and the
check-set gate. Each takes per-item scores and returns a decision; none of them calls a model."""
import json
import random
import re

FORMS = ("rigid", "liquid", "assembled")


def bootstrap_ci(diffs, seed, n=4000):
    """95 % percentile bootstrap interval of the mean of paired differences."""
    rng = random.Random(seed)
    k = len(diffs)
    means = sorted(sum(diffs[rng.randrange(k)] for _ in range(k)) / k for _ in range(n))
    return means[int(0.025 * n)], means[int(0.975 * n) - 1]


def comparable_key(record, hidden=("check", "score", "reward", "gold", "label", "verdict")):
    """The comparable output of a form's record (answer / response, else every visible field), lightly normalized.
    Grading fields never decide whether two outputs agree."""
    out = next((record[k] for k in ("answer", "response") if record.get(k) not in (None, "")), None)
    if out is None:
        out = json.dumps({k: v for k, v in record.items() if k not in hidden}, sort_keys=True, ensure_ascii=False)
    out = re.sub(r"[^\w\s]", " ", str(out).lower())
    out = re.sub(r"\b(a|an|the)\b", " ", out)
    return " ".join(out.split())


def vote3_form(records, forms=FORMS):
    """The form whose output the majority shares (rigid preferred inside the majority); all different -> rigid."""
    groups = {}
    for f in forms:
        r = records.get(f)
        if r is None or r.get("error"):
            continue
        groups.setdefault(comparable_key(r["output"]), []).append(f)
    if not groups:
        return "rigid"
    big = max(groups.values(), key=lambda g: (len(g), "rigid" in g))
    alive = [f for g in groups.values() for f in g]
    if len(big) >= 2:
        return "rigid" if "rigid" in big else big[0]
    return "rigid" if "rigid" in alive else alive[0]


def choose_default(scores, votes=None, seed=0):
    """Task-level default form on the validation set: leave the optimizer's program (rigid) only if an alternative is
    better with a paired 95 % bootstrap lower bound > 0; among those, the highest mean wins.
    scores: {form: [score per item]} (same item order); votes: optional per-item vote3 scores."""
    per = {f: list(v) for f, v in scores.items()}
    if votes is not None:
        per["vote3"] = list(votes)
    means = {f: sum(v) / len(v) for f, v in per.items()}
    evidence = {}
    for f in ("liquid", "assembled", "vote3"):
        if f in per:
            d = [b - a for a, b in zip(per["rigid"], per[f])]
            lo, hi = bootstrap_ci(d, seed + 31)
            evidence[f] = {"delta": sum(d) / len(d), "ci95": [lo, hi]}
    significant = [f for f, e in evidence.items() if e["ci95"][0] > 0]
    order = ("rigid", "liquid", "assembled", "vote3")
    chosen = max(significant, key=lambda f: (means[f], -order.index(f))) if significant else "rigid"
    return {"chosen": chosen, "means": means, "evidence_vs_rigid": evidence}


def calibrate_threshold(picks, candidates=(0, 3, 4, 5)):
    """The judge's minimum confidence, fixed on the validation set: the threshold with the highest gain over the default
    (ties -> the stricter one); 99 switches the judge off when no threshold gains.
    picks: dicts with 'ref', 'proposed' (the judge's choice before the threshold), 'confidence' and 'scores'."""
    gain = {}
    for th in candidates:
        g = 0.0
        for p in picks:
            f = p.get("proposed", p["ref"])
            if f != p["ref"] and (p.get("confidence") or 0) >= th:
                g += p["scores"][f] - p["scores"][p["ref"]]
        gain[th] = g / max(1, len(picks))
    best = max(gain.values())
    th = max(k for k, v in gain.items() if v >= best - 1e-12) if best > 1e-12 else 99
    return {"min_confidence": th, "gain_by_threshold": gain}


def gate(picks, min_gain=0.005):
    """Check-set gate: the judge is trusted only if its selection beats the default by more than min_gain on the check
    set AND it won more switches than it lost. Otherwise only the default form is used."""
    sel = sum(p["scores"][p["form"]] for p in picks) / max(1, len(picks))
    ref = sum(p["scores"][p["ref"]] for p in picks) / max(1, len(picks))
    sw = [p for p in picks if p["form"] != p["ref"]]
    won = sum(1 for p in sw if p["scores"][p["form"]] > p["scores"][p["ref"]] + 1e-12)
    lost = sum(1 for p in sw if p["scores"][p["form"]] < p["scores"][p["ref"]] - 1e-12)
    return {"trusted": (sel - ref) > min_gain and won > lost, "selected_minus_default": sel - ref,
            "switches_won": won, "switches_lost": lost}
