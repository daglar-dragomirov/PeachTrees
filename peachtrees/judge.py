"""The universal asymmetric judge: keeps the default form's output unless it names a specific, checkable defect that
an alternative avoids; swapped-order consistency, k votes, a calibrated confidence threshold. Never sees gold or scores."""
import hashlib
import json
from contextlib import nullcontext
from typing import Literal

import dspy

from .selection import FORMS, comparable_key
from .templates import HIDDEN_FIELDS, JUDGE_TEMPLATE
from .tools import run_python


def make_judge(task_tools=(), use_tools=True, iters=6):
    sig = dspy.make_signature({
        "task": (str, dspy.InputField(desc="the task inputs")),
        "purpose": (str, dspy.InputField(desc="what the task's program is meant to do, from its own definition")),
        "reference": (str, dspy.InputField(desc="the reference output with the record of how it was produced")),
        "alternatives": (str, dspy.InputField(desc="alternative outputs A and B for the same task")),
        "defect": (str, dspy.OutputField(desc="the specific, checkable defect of the reference, or 'none'")),
        "choice": (Literal["KEEP", "A", "B"], dspy.OutputField(
            desc="KEEP unless the reference has that defect and one alternative avoids it")),
        "confidence": (int, dspy.OutputField(desc="1-5: how certain you are that the switch is right (5 = certain)"))},
        JUDGE_TEMPLATE)
    if use_tools:  # read-only task tools only: never tools that change state
        return dspy.ReAct(sig, tools=[run_python] + list(task_tools), max_iters=iters)
    return dspy.Predict(sig)


def render(record, max_chars):
    x = {k: v for k, v in (record or {}).items() if v not in (None, "", [], {}) and k not in HIDDEN_FIELDS}
    if not x:
        return "(no output)"
    per = max(400, max_chars // len(x))
    return "\n".join(f"[{k}]\n{(v if isinstance(v, str) else json.dumps(v, ensure_ascii=False))[-per:]}"
                     for k, v in x.items())


def judge_item(judge, uid, task_inputs, purpose, records, default, votes=3, max_chars=9000, min_confidence=0):
    """records: {form: {"output": record dict, "error": str|None}}. Returns the pick dict:
    form (chosen), ref (default), proposed (choice before the threshold), confidence, mode."""
    groups = {}
    for f in FORMS:
        r = records.get(f)
        if r is None or r.get("error") or not r.get("output"):
            continue
        groups.setdefault(comparable_key(r["output"]), []).append(f)
    if not groups:
        return {"form": default, "ref": default, "mode": "no_output"}
    if not any(default in g for g in groups.values()):
        return {"form": next(iter(groups.values()))[0], "ref": default, "mode": "default_failed"}
    if len(groups) == 1:
        return {"form": default, "ref": default, "mode": "identical"}
    rk = comparable_key(records[default]["output"])
    alts = sorted([g[0] for k, g in groups.items() if k != rk],
                  key=lambda f: hashlib.sha256((str(uid) + "|" + f).encode()).hexdigest())[:2]
    letters = dict(zip("AB", alts))
    task = "\n".join(f"{k}: {v}" for k, v in task_inputs.items())[:6000]
    ref = render(records[default]["output"], max_chars)
    conf = [5]

    def ask(lt, sample):
        alt = "\n\n".join(f"=== Alternative {L} ===\n" + render(records[f]["output"], max_chars) for L, f in lt.items())
        lm = dspy.settings.lm  # an independent sample per vote: a distinct rollout id bypasses the LM cache
        ctx = dspy.context(lm=lm.copy(rollout_id=sample)) if lm is not None and hasattr(lm, "copy") else nullcontext()
        with ctx:
            r = judge(task=task, purpose=purpose, reference=ref, alternatives=alt)
        d = " ".join(str(r.defect or "").lower().split()).strip(" .'\"")
        if str(r.choice).strip() == "KEEP" or d in ("", "none", "no defect", "n/a", "no"):
            return None
        try:
            conf[0] = min(conf[0], int(r.confidence))
        except Exception:
            conf[0] = 0
        return lt.get(str(r.choice).strip()[:1])

    tally, mode = {}, "judged"
    try:
        for v in range(votes):
            f1 = ask(letters, 2 * v)
            if f1 is None:
                continue
            if len(letters) == 2:  # the same question with the alternatives swapped must agree
                f2 = ask({"A": letters["B"], "B": letters["A"]}, 2 * v + 1)
                if f2 != f1:
                    continue
            tally[f1] = tally.get(f1, 0) + 1
        best = max(tally, key=tally.get) if tally else None
        proposed = best if best is not None and tally[best] * 2 > votes else default
    except Exception as e:  # a failing judge keeps the default
        return {"form": default, "ref": default, "proposed": default, "mode": f"judge_error {type(e).__name__}"}
    confidence = conf[0] if proposed != default else None
    if proposed != default and conf[0] < min_confidence:
        return {"form": default, "ref": default, "proposed": proposed, "confidence": confidence, "mode": "below_confidence"}
    return {"form": proposed, "ref": default, "proposed": proposed, "confidence": confidence, "mode": mode,
            "votes": tally}
