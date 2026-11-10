"""PeachTrees: a layer over the program produced by any prompt optimizer (or written by hand).

fit(valset, checkset) decides, once per task and without touching any test data:
  1. the default form: the optimizer's program unless an alternative form is significantly better on valset;
  2. the judge's confidence threshold, calibrated on valset;
  3. whether the judge is trusted at all (check-set gate).
Then: mode "lite" answers with the default form only (cheap); mode "full" runs every form and lets the judge pick
per item - only if the gate trusted the judge, otherwise it falls back to the default form."""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import dspy

from .forms import build_forms, learned_guidance, record_of
from .judge import judge_item, make_judge
from .selection import FORMS, calibrate_threshold, choose_default, gate, vote3_form
from .templates import purpose_of


class PeachTrees:
    def __init__(self, program, metric, *, inputs=None, outputs=None, tools=(), judge_tools=(), trainset=None,
                 mode="full", judge_votes=3, judge_iters=6, max_chars=9000, max_iters=4, threads=8, seed=0):
        """program: a dspy.Module (any optimizer's output); metric(example, prediction) -> float in [0, 1];
        tools: the task's tools for the agents; judge_tools: READ-ONLY task tools for the judge (never state-changing);
        trainset: optional labeled examples whose outputs show the agents the expected output form."""
        assert mode in ("lite", "full")
        self.program, self.metric, self.mode = program, metric, mode
        self.inputs, self.outputs, self.tools, self.judge_tools = inputs, outputs, tuple(tools), tuple(judge_tools)
        self.trainset, self.judge_votes, self.judge_iters = trainset, judge_votes, judge_iters
        self.max_chars, self.max_iters, self.threads, self.seed = max_chars, max_iters, threads, seed
        self.decisions, self.forms, self.judge = None, None, None

    # ---------------------------------------------------------------- setup
    def _prepare(self, example):
        if self.inputs is None:
            self.inputs = list(example.inputs().keys())
        if self.outputs is None:
            labels = [k for k in example.toDict() if k not in self.inputs]
            pred = self.program(**example.inputs())
            keys = [k for k in pred.keys() if k != "reasoning"]
            self.outputs = [k for k in keys if k in labels] or keys
        examples = None
        if self.trainset:
            lines = []
            for ex in self.trainset[:5]:
                lab = {k: ex.get(k) for k in self.outputs if ex.get(k) not in (None, "")}
                if lab:
                    lines.append("; ".join(f"{k}: {str(v)[:150]}" for k, v in lab.items()))
            examples = "\n".join(f"- {x}" for x in lines) or None
        self.forms = build_forms(self.program, self.inputs, self.outputs, self.tools, examples, self.max_iters)
        _, self._guidance = learned_guidance(self.program, self.outputs)
        self._purpose = purpose_of(self.program) + "\n\nGuidance learned for this task by an optimizer:\n" + self._guidance
        self.judge = make_judge(self.judge_tools, use_tools=True, iters=self.judge_iters)

    def _run(self, form, example, score=True):
        kw = {k: example[k] for k in self.inputs}
        err = None
        for attempt in (0, 1):  # one item-level retry, as a fresh attempt
            try:
                pred = self.forms[form](**kw)
                break
            except Exception as e:
                pred, err = None, f"{type(e).__name__}: {str(e)[:300]}"
        if pred is None:
            return {"output": None, "pred": None, "score": 0.0, "error": err}
        s = float(self.metric(example, pred)) if score else None  # no labels at answer time
        return {"output": record_of(pred, self.outputs), "pred": pred, "score": s, "error": None}

    def _evaluate(self, dataset, forms=FORMS):
        with ThreadPoolExecutor(self.threads) as pool:
            return {f: list(pool.map(lambda ex, f=f: self._run(f, ex), dataset)) for f in forms}

    def _judge_all(self, dataset, res, default, min_confidence):
        def one(i):
            recs = {f: res[f][i] for f in FORMS}
            ref = vote3_form(recs) if default == "vote3" else default
            p = judge_item(self.judge, i, {k: dataset[i][k] for k in self.inputs}, self._purpose, recs, ref,
                           self.judge_votes, self.max_chars, min_confidence)
            p["scores"] = {f: res[f][i]["score"] for f in FORMS}
            return p
        with ThreadPoolExecutor(self.threads) as pool:
            return list(pool.map(one, range(len(dataset))))

    # ---------------------------------------------------------------- fit
    def fit(self, valset, checkset):
        """valset: the optimizer's validation examples (default form, threshold); checkset: other labeled examples
        (judge gate). Neither may overlap the data you report on."""
        self._prepare(valset[0])
        res = self._evaluate(valset)
        votes = [res[vote3_form({f: res[f][i] for f in FORMS})][i]["score"] for i in range(len(valset))]
        choice = choose_default({f: [r["score"] for r in res[f]] for f in FORMS}, votes, self.seed)
        default = choice["chosen"]
        self.decisions = {"inputs": self.inputs, "outputs": self.outputs, "default": choice, "threshold": None,
                          "gate": None, "judge_trusted": False}
        if self.mode == "lite":
            return self
        picks = self._judge_all(valset, res, default, min_confidence=0)
        th = calibrate_threshold(picks)
        self.decisions["threshold"] = th
        if th["min_confidence"] >= 99:
            return self
        chk = self._evaluate(checkset)
        g = gate(self._judge_all(checkset, chk, default, th["min_confidence"]))
        self.decisions["gate"], self.decisions["judge_trusted"] = g, g["trusted"]
        return self

    # ---------------------------------------------------------------- answer
    def __call__(self, **kw):
        assert self.decisions is not None, "call fit(valset, checkset) first"
        default = self.decisions["default"]["chosen"]
        ex = dspy.Example(**kw).with_inputs(*self.inputs)
        if self.mode == "full" and self.decisions["judge_trusted"]:
            recs = {f: self._run(f, ex, score=False) for f in FORMS}
            ref = vote3_form(recs) if default == "vote3" else default
            p = judge_item(self.judge, json.dumps(kw, sort_keys=True, default=str)[:200], kw, self._purpose, recs, ref,
                           self.judge_votes, self.max_chars, self.decisions["threshold"]["min_confidence"])
            return recs[p["form"]]["pred"] or recs[ref]["pred"]
        if default == "vote3":
            recs = {f: self._run(f, ex, score=False) for f in FORMS}
            return recs[vote3_form(recs)]["pred"]
        return self.forms[default](**kw)

    def save(self, path):
        Path(path).write_text(json.dumps(self.decisions, indent=1, default=str))


def wrap(program, metric, valset, checkset, **kw):
    """One call: build the forms, take the task-level decisions on valset / checkset and return the wrapped program."""
    return PeachTrees(program, metric, **kw).fit(valset, checkset)
