"""PeachTrees: an optimizer-agnostic, never-worse layer on top of an optimized DSPy program."""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Hashable, Mapping, Sequence

import dspy

from .forms import ASSEMBLED_TEMPLATE, LIQUID_TEMPLATE, Assembled, Liquid, label_examples, task_text
from .select import FORMS, non_inferior, pick, text_key

log = logging.getLogger("peachtrees")


def _fields(program: dspy.Module) -> tuple[list[str], str]:
    preds = [p for _, p in program.named_predictors()]
    if not preds:
        raise ValueError("the program has no predictors; pass input_fields and output_field")
    inputs = list(preds[0].signature.input_fields)
    outs = [k for k in preds[-1].signature.output_fields if k != "reasoning"]
    if len(outs) != 1:
        raise ValueError(f"cannot infer the output field from {outs}; pass output_field")
    return inputs, outs[0]


class PeachTrees(dspy.Module):
    """Wrap an optimized DSPy program in the three PeachTrees forms and the 1.0 selection rule.

    Typical use::

        pt = PeachTrees(optimized_program)
        pt.fit(selection_examples, metric)      # labeled data the optimizer saw (train + val) is fine
        prediction = pt(question="...")

    mode="full" runs the program and the reviewer, and the agent only when the two disagree (then a vote);
    mode="lite" runs the reviewer only (its draft is the program's output) and returns the reviewer's answer.
    ``fit`` decides once per task whether the layer is used at all (non-inferiority on the selection data, ``z`` standard
    errors); if not, the wrapped object behaves exactly like the program.
    """

    def __init__(self, program: dspy.Module, *, input_fields: Sequence[str] | None = None,
                 output_field: str | None = None, tools: Sequence[Callable] = (), mode: str = "full",
                 answer_key: Callable[[Any], Hashable | None] | None = None,
                 checker: Callable[[Mapping[str, Any], Any], bool | None] | None = None,
                 z: float = 1.0, max_iters: int = 8, retries: int = 3, examples: Sequence[dspy.Example] | None = None,
                 forms: Mapping[str, Callable[..., Any]] | None = None):
        super().__init__()
        if mode not in ("full", "lite"):
            raise ValueError("mode must be 'full' or 'lite'")
        if input_fields is None or output_field is None:
            i, o = _fields(program)
            input_fields, output_field = input_fields or i, output_field or o
        self.program, self.mode, self.z, self.retries = program, mode, z, retries
        self.input_fields, self.output_field = list(input_fields), output_field
        self.answer_key, self.checker = answer_key, checker
        head = task_text(program, label_examples(examples, output_field) if examples else None)
        if forms is None:  # built lazily-cheap: ReAct modules hold no state until called
            forms = {"rigid": program,
                     "assembled": Assembled(program, self.input_fields, output_field, head + "\n\n" + ASSEMBLED_TEMPLATE,
                                            tools, max_iters),
                     "liquid": Liquid(self.input_fields, output_field, head + "\n\n" + LIQUID_TEMPLATE, tools, max_iters)}
        self.forms = dict(forms)
        self.use_layer: bool | None = None  # None until fit(); then the task decision
        self.report: dict[str, Any] = {}

    # ------------------------------------------------------------------ one form, one input
    def _run(self, form: str, inputs: Mapping[str, Any]) -> Any:
        for attempt in range(self.retries + 1):
            try:
                return self.forms[form](**inputs)
            except Exception as e:  # an output that cannot be parsed counts as no output after the retries
                log.debug("form %s failed (attempt %d): %s", form, attempt + 1, e)
        return None

    def _answer(self, pred: Any) -> Any:
        return None if pred is None else getattr(pred, self.output_field, None)

    def _key(self, pred: Any) -> Hashable | None:
        a = self._answer(pred)
        if a in (None, ""):
            return None
        return self.answer_key(pred) if self.answer_key else text_key(a)

    def _check(self, inputs: Mapping[str, Any], pred: Any) -> bool | None:
        if self.checker is None or pred is None:
            return None
        try:
            return self.checker(inputs, pred)
        except Exception:
            return None

    def _decide(self, inputs: Mapping[str, Any], preds: dict[str, Any]) -> str:
        keys = {f: self._key(preds.get(f)) for f in FORMS}
        checks = {f: self._check(inputs, preds.get(f)) for f in FORMS} if self.checker else None
        return pick(keys, checks, use_vote=self.mode == "full")

    def _layer(self, inputs: Mapping[str, Any], lazy: bool = True) -> tuple[str, dict[str, Any]]:
        preds: dict[str, Any] = {"assembled": self._run("assembled", inputs)}
        if self.mode == "lite":  # the reviewer; its draft (= one program run) if the reviewer has no usable output
            a = preds["assembled"]
            if self._key(a) is not None:
                return "assembled", preds
            draft = getattr(a, "draft_prediction", None) if a is not None else None
            preds["rigid"] = draft if draft is not None else self._run("rigid", inputs)
            return "rigid", preds
        preds["rigid"] = self._run("rigid", inputs)
        ka, kr = self._key(preds["assembled"]), self._key(preds["rigid"])
        if not lazy or ka is None or kr is None or ka != kr:
            preds["liquid"] = self._run("liquid", inputs)
        return self._decide(inputs, preds), preds

    def forward(self, **inputs):
        if self.use_layer is False:
            return self.program(**inputs)
        form, preds = self._layer(inputs)
        out = preds.get(form)
        if out is None:  # every form failed: fall back to the program's own behaviour (it may raise)
            return self.program(**inputs)
        return out

    # ------------------------------------------------------------------ the task decision
    def fit(self, selection_set: Sequence[dspy.Example], metric: Callable[..., Any], num_threads: int = 8,
            cluster: Callable[[dspy.Example], Hashable] | None = None) -> "PeachTrees":
        """Run the forms on labeled selection data and decide once whether the layer is used for this task."""
        def score(ex, pred):
            if pred is None:
                return 0.0
            try:
                return float(metric(ex, pred))
            except Exception:
                return 0.0

        def one(i_ex):
            i, ex = i_ex
            inputs = {k: ex[k] for k in self.input_fields}
            form, preds = self._layer(inputs, lazy=False)
            s = {f: score(ex, preds.get(f)) for f in FORMS if f in preds}
            if self.mode == "lite" and preds.get("rigid") is None:
                draft = getattr(preds["assembled"], "draft_prediction", None)
                s["rigid"] = score(ex, draft) if draft is not None else score(ex, self._run("rigid", inputs))
            return {"i": i, "cluster": cluster(ex) if cluster else i, "form": form, "scores": s}

        with ThreadPoolExecutor(max(1, num_threads)) as pool:
            rows = list(pool.map(one, enumerate(selection_set)))
        use, m, se = non_inferior([(r["cluster"], r["scores"][r["form"]] - r["scores"]["rigid"]) for r in rows], self.z)
        self.use_layer = use
        n = len(rows)
        self.report = {"n": n, "use_layer": use, "mean_gain": m, "se": se, "z": self.z, "mode": self.mode,
                       "program_score": sum(r["scores"]["rigid"] for r in rows) / n if n else 0.0,
                       "peachtrees_score": sum(r["scores"][r["form"]] for r in rows) / n if n else 0.0,
                       "picks": {f: sum(1 for r in rows if r["form"] == f) for f in FORMS}, "items": rows}
        return self
