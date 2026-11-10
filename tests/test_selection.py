"""Model-free tests of the decision rules."""
from peachtrees.selection import calibrate_threshold, choose_default, comparable_key, gate, vote3_form


def test_default_stays_rigid_without_significant_evidence():
    s = {"rigid": [1, 0] * 50, "liquid": [0, 1] * 50, "assembled": [1, 0] * 50}
    assert choose_default(s)["chosen"] == "rigid"


def test_default_switches_on_clear_evidence():
    s = {"rigid": [0] * 60 + [1] * 40, "liquid": [1] * 90 + [0] * 10, "assembled": [0] * 60 + [1] * 40}
    assert choose_default(s)["chosen"] == "liquid"


def test_threshold_ties_take_the_stricter_one_and_no_gain_turns_judge_off():
    picks = [{"ref": "rigid", "proposed": "liquid", "confidence": 5, "scores": {"rigid": 0, "liquid": 1}},
             {"ref": "rigid", "proposed": "liquid", "confidence": 2, "scores": {"rigid": 1, "liquid": 0}}]
    assert calibrate_threshold(picks)["min_confidence"] == 5
    bad = [{"ref": "rigid", "proposed": "liquid", "confidence": 5, "scores": {"rigid": 1, "liquid": 0}}]
    assert calibrate_threshold(bad)["min_confidence"] == 99


def test_gate_needs_gain_and_more_wins_than_losses():
    won = {"ref": "rigid", "form": "liquid", "scores": {"rigid": 0, "liquid": 1}}
    lost = {"ref": "rigid", "form": "liquid", "scores": {"rigid": 1, "liquid": 0}}
    keep = {"ref": "rigid", "form": "rigid", "scores": {"rigid": 1, "liquid": 1}}
    assert gate([won, won, lost] + [keep] * 7)["trusted"]
    assert not gate([won, lost] + [keep] * 8)["trusted"]


def test_grading_fields_never_decide_agreement():
    a = {"calls": "f(x=1)", "check": {"valid": True}}
    b = {"calls": "f(x=1)", "check": {"valid": False}}
    assert comparable_key(a) == comparable_key(b)


def test_vote3_prefers_the_majority_and_rigid_inside_it():
    recs = {"rigid": {"output": {"answer": "Paris"}}, "liquid": {"output": {"answer": "paris"}},
            "assembled": {"output": {"answer": "Lyon"}}}
    assert vote3_form(recs) == "rigid"
    recs["rigid"]["output"]["answer"] = "Rome"
    assert vote3_form(recs) == "rigid"  # all different -> rigid
    recs["assembled"]["output"]["answer"] = "Paris"
    assert vote3_form(recs) == "liquid"  # majority without rigid
