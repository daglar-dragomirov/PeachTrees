"""The fit / answer path with stub forms and a stub judge (no model)."""
import dspy

import peachtrees.core as core
from peachtrees import PeachTrees


class Echo(dspy.Module):
    def __init__(self):
        super().__init__()
        self.step = dspy.Predict("question -> answer")

    def forward(self, question):
        return dspy.Prediction(answer="rigid:" + question)


def metric(ex, pred):
    return float(pred.answer.split(":")[-1] == ex.answer)


def data(n, rigid_ok, liquid_ok):
    out = []
    for i in range(n):
        q = f"q{i}"
        out.append((dspy.Example(question=q, answer=q).with_inputs("question"), i < rigid_ok, i < liquid_ok))
    return out


def stub_forms(table):
    def form(name):
        def f(question):
            ok = table[question][name]
            return dspy.Prediction(answer=(name + ":" + question) if ok else (name + ":wrong"))
        return f
    return {n: form(n) for n in ("rigid", "liquid", "assembled")}


def test_lite_switches_default_and_answers_with_it(monkeypatch):
    rows = data(80, rigid_ok=20, liquid_ok=70)
    table = {ex.question: {"rigid": r, "liquid": l, "assembled": r} for ex, r, l in rows}
    pt = PeachTrees(Echo(), metric, mode="lite", inputs=["question"], outputs=["answer"], threads=4)
    monkeypatch.setattr(core, "build_forms", lambda *a, **k: stub_forms(table))
    monkeypatch.setattr(core, "make_judge", lambda *a, **k: None)
    pt.fit([ex for ex, _, _ in rows], [])
    assert pt.decisions["default"]["chosen"] == "liquid"
    assert pt(question="q5").answer == "liquid:q5"


def test_full_falls_back_to_default_when_the_gate_rejects_the_judge(monkeypatch):
    rows = data(60, rigid_ok=50, liquid_ok=30)
    table = {ex.question: {"rigid": r, "liquid": l, "assembled": r} for ex, r, l in rows}
    pt = PeachTrees(Echo(), metric, mode="full", inputs=["question"], outputs=["answer"], threads=4)
    monkeypatch.setattr(core, "build_forms", lambda *a, **k: stub_forms(table))
    monkeypatch.setattr(core, "make_judge", lambda *a, **k: None)

    def bad_judge(judge, uid, task, purpose, recs, ref, *a, **k):  # always switches to the worse liquid form
        return {"form": "liquid", "ref": ref, "proposed": "liquid", "confidence": 5, "mode": "judged"}
    monkeypatch.setattr(core, "judge_item", bad_judge)
    exs = [ex for ex, _, _ in rows]
    pt.fit(exs[:30], exs[30:])
    assert pt.decisions["default"]["chosen"] == "rigid"
    assert not pt.decisions["judge_trusted"]
    assert pt(question="q1").answer == "rigid:q1"
