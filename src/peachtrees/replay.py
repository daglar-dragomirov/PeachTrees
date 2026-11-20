"""Offline replay: apply the PeachTrees rules to saved per-item outputs, with no model call.

This is how the 1.0 rule was found and checked in the research: every run saves, per item, the answer key and the
score of each form; a rule is then a pure function of those rows. Input rows (JSON lines or a list of dicts)::

    {"cluster": "q17",                                  # optional; items sharing it are one unit for the SE
     "keys":   {"rigid": "42", "assembled": "42", "liquid": "41"},   # null = no usable output
     "scores": {"rigid": 1.0, "assembled": 1.0, "liquid": 0.0},
     "checks": {"rigid": true, "assembled": null, "liquid": false},  # optional, label-free checker results
     "verifier": "liquid"}                              # optional: the form a verifier chose on this item

``PeachTrees.save_fit(path, items=True)`` writes rows in this format.
"""
from __future__ import annotations

import json
import random
from typing import Any, Iterable, Mapping, Sequence

from .select import FORMS, contested, pick, task_switch


def load_rows(path: str) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    try:  # a save_fit file ({"items": [...]}) or a JSON list
        data = json.loads(text)
    except json.JSONDecodeError:  # JSON lines
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    if isinstance(data, dict):
        if "items" not in data:
            raise ValueError("a JSON object needs an 'items' list (save_fit(path, items=True) writes one)")
        return list(data["items"])
    return list(data) if isinstance(data, list) else [data]


def _choose(row: Mapping[str, Any], mode: str, use_checks: bool, use_verifier: bool) -> str:
    keys = {f: row.get("keys", {}).get(f) for f in FORMS}
    checks = row.get("checks") if use_checks else None
    form = pick(keys, checks, use_vote=mode == "full")
    v = row.get("verifier")
    if use_verifier and isinstance(v, str) and v in FORMS and contested(keys, checks) and keys.get(v) is not None:
        return v
    return form


def bootstrap_ci(deltas: Sequence[tuple[Any, float]], reps: int = 2000, seed: int = 0,
                 level: float = 0.95) -> tuple[float, float]:
    """Cluster bootstrap percentile interval of the mean difference."""
    by: dict[Any, list[float]] = {}
    for c, d in deltas:
        by.setdefault(c, []).append(float(d))
    groups = list(by.values())
    if len(groups) < 2:
        m = sum(d for _, d in deltas) / max(1, len(deltas))
        return m, m
    rng = random.Random(seed)
    means = []
    for _ in range(reps):
        sample = [groups[rng.randrange(len(groups))] for _ in groups]
        n = sum(len(g) for g in sample)
        means.append(sum(sum(g) for g in sample) / n)
    means.sort()
    lo = means[int((1 - level) / 2 * reps)]
    hi = means[min(reps - 1, int((1 + level) / 2 * reps))]
    return lo, hi


def replay(rows: Iterable[Mapping[str, Any]], mode: str = "full", z: float | None = None, use_checks: bool = True,
           use_verifier: bool = True, ci: bool = True, switch: str = "do_no_harm",
           margin: float = 0.02) -> dict[str, Any]:
    """Scores of the program, each form, PeachTrees and the per-item oracle; the non-inferiority decision."""
    rows = list(rows)
    n = len(rows)
    if n == 0:
        return {"n": 0}
    chosen = [_choose(r, mode, use_checks, use_verifier) for r in rows]
    sc = [r.get("scores", {}) for r in rows]
    deltas = [(r.get("cluster", i), float(s.get(f, 0.0)) - float(s.get("rigid", 0.0)))
              for i, (r, s, f) in enumerate(zip(rows, sc, chosen))]
    use, m, se = task_switch(deltas, switch, z, margin)
    out: dict[str, Any] = {
        "n": n, "mode": mode, "z": z, "switch": switch,
        "program": sum(float(s.get("rigid", 0.0)) for s in sc) / n,
        "forms": {f: sum(float(s.get(f, 0.0)) for s in sc) / n for f in FORMS},
        "peachtrees": sum(float(s.get(f, 0.0)) for s, f in zip(sc, chosen)) / n,
        "oracle": sum(max([float(v) for v in s.values()] or [0.0]) for s in sc) / n,
        "gain": m, "se": se, "use_layer": use,
        "deployed": (sum(float(s.get(f, 0.0)) for s, f in zip(sc, chosen)) / n) if use
        else sum(float(s.get("rigid", 0.0)) for s in sc) / n,
        "picks": {f: chosen.count(f) for f in FORMS},
        "contested": sum(1 for r in rows if contested({f: r.get("keys", {}).get(f) for f in FORMS},
                                                         r.get("checks") if use_checks else None)),
    }
    if ci:
        out["ci95"] = bootstrap_ci(deltas)
    return out


def format_report(r: Mapping[str, Any]) -> str:
    if not r.get("n"):
        return "no rows"
    lines = [f"items            {r['n']}  (mode {r['mode']}, switch {r.get('switch', 'do_no_harm')}, z {r['z']})",
             f"program          {r['program']:.4f}",
             *(f"  {f:<14} {v:.4f}" for f, v in r["forms"].items()),
             f"peachtrees       {r['peachtrees']:.4f}   gain {r['gain']:+.4f} +- {r['se']:.4f}"
             + (f"   95% CI [{r['ci95'][0]:+.4f}, {r['ci95'][1]:+.4f}]" if "ci95" in r else ""),
             f"oracle           {r['oracle']:.4f}",
             f"use layer        {r['use_layer']}   -> deployed {r['deployed']:.4f}",
             "picks            " + ", ".join(f"{f} {c}" for f, c in r["picks"].items()),
             f"contested items  {r['contested']}"]
    return "\n".join(lines)
