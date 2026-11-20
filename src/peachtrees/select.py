"""PeachTrees 1.0 selection rules (label-free at inference).

Item rule (``pick``): 1. drop forms without a usable output; 2. if a task checker is given, drop forms whose output fails
it (keep all if all fail); 3. if at least two surviving forms give the same answer key, return that answer; 4. otherwise
the reviewer ("assembled"), then the program ("rigid"), then the agent ("liquid").

Task rule (``non_inferior``): the PeachTrees policy is used for a task only if, on labeled selection data, its mean score
minus the program's is not below zero by more than ``z`` standard errors (default 1.0); otherwise the program alone runs.
"""
from __future__ import annotations

import json
import math
import re
from typing import Any, Callable, Hashable, Iterable, Mapping, Sequence

FORMS = ("rigid", "liquid", "assembled")
FALLBACK = ("assembled", "rigid", "liquid")


def text_key(value: Any) -> str:
    """Generic answer key: lower-cased text without punctuation and articles, whitespace collapsed."""
    o = value if isinstance(value, str) else json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    o = re.sub(r"[^\w\s]", " ", o.lower())
    o = re.sub(r"\b(a|an|the)\b", " ", o)
    return " ".join(o.split())


def _live(alive: Sequence[str], form: str) -> str:
    if form in alive or not alive:
        return form
    return next(f for f in FALLBACK if f in alive)


def pick(keys: Mapping[str, Hashable | None], checks: Mapping[str, bool | None] | None = None,
         use_vote: bool = True) -> str:
    """Choose one form for one input.

    keys: form name -> answer key of that form's output, or None if the form produced no usable output.
    checks: form name -> result of a deterministic, label-free task checker (True / False / None = unknown).
    use_vote: False gives the "lite" rule (the reviewer, with the liveness / checker fallback).
    """
    alive = [f for f in FORMS if keys.get(f) is not None]
    if checks:
        ok = [f for f in alive if checks.get(f) is not False]
        alive = ok or alive
    if use_vote:
        groups: dict[Hashable, list[str]] = {}
        for f in alive:
            groups.setdefault(keys[f], []).append(f)
        big = max(groups.values(), key=len) if groups else []
        if len(big) >= 2:
            return "assembled" if "assembled" in big else big[0]
    return _live(alive, "assembled")


def paired_stats(deltas: Iterable[tuple[Hashable, float]]) -> tuple[float, float]:
    """Mean and clustered standard error of per-item differences; items sharing a cluster id are one unit."""
    by: dict[Hashable, list[float]] = {}
    for cluster, d in deltas:
        by.setdefault(cluster, []).append(float(d))
    n = sum(len(v) for v in by.values())
    if n == 0:
        return 0.0, 0.0
    m = sum(sum(v) for v in by.values()) / n
    k = len(by)
    if k < 2:
        return m, 0.0
    var = sum((sum(v) - m * len(v)) ** 2 for v in by.values()) * k / (k - 1) / n ** 2
    return m, math.sqrt(var)


def non_inferior(deltas: Iterable[tuple[Hashable, float]], z: float = 1.0) -> tuple[bool, float, float]:
    """The task rule: (use PeachTrees?, mean difference, standard error)."""
    m, se = paired_stats(deltas)
    return m + z * se >= 0, m, se


Checker = Callable[[Mapping[str, Any], Any], "bool | None"]
