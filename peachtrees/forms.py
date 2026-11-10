"""The three forms of a task: the optimizer's program as-is (rigid), a universal free agent (liquid) and the program's
draft checked and repaired by a universal reviewer (assembled). Agents are built from the program's own signature."""
import json
import re

import dspy

from .templates import form_instructions, purpose_of
from .tools import run_python


def _signature(inputs, outputs, instructions, extra_inputs=()):
    fields = {name: (str, dspy.InputField()) for name in inputs}
    for name, desc in extra_inputs:
        fields[name] = (str, dspy.InputField(desc=desc))
    for name in outputs:
        fields[name] = (str, dspy.OutputField())
    return dspy.make_signature(fields, instructions)


def _clean(pred, outputs):
    """Strip DSPy field markers and stray leading quote marks from an agent's string outputs."""
    for k in outputs:
        v = pred.get(k) if hasattr(pred, "get") else getattr(pred, k, None)
        if isinstance(v, str):
            v = re.sub(r"\s*\[\[\s*##[^\]]*\]\]\s*", " ", v).strip()
            pred[k] = re.sub(r"^(>\s*)+", "", v)
    return pred


def _trajectory_text(pred):
    traj = getattr(pred, "trajectory", None)
    if isinstance(traj, dict):
        return "\n".join(f"{k}: {str(v)[:1500]}" for k, v in traj.items())
    return str(getattr(pred, "reasoning", "") or "")


def record_of(pred, outputs):
    """The per-item record a judge sees: every output field of the prediction as text (no grading fields)."""
    try:
        items = list(pred.items())
    except Exception:
        items = [(k, getattr(pred, k, None)) for k in outputs]
    return {k: (None if v is None else str(v)[-8000:]) for k, v in items}


def learned_guidance(program, outputs=None):
    """The optimizer's learned instructions: every predictor's instructions (for the assembled reviewer) and those of
    the predictors that write the task's outputs (for the free agent)."""
    preds = list(program.named_predictors())
    every = "\n\n".join(p.signature.instructions.strip() for _, p in preds)
    final = [p for _, p in preds if outputs and set(p.signature.output_fields) & set(outputs)]
    return every, ("\n\n".join(p.signature.instructions.strip() for p in final) if final else every)


def build_forms(program, inputs, outputs, tools=(), examples=None, max_iters=4):
    """Returns {"rigid", "liquid", "assembled"}: callables (**inputs) -> dspy.Prediction."""
    _, guide = learned_guidance(program, outputs)
    instr = form_instructions(purpose_of(program), guide, examples)
    agent_tools = list(tools) + [run_python]

    liquid = dspy.ReAct(_signature(inputs, outputs, instr["liquid"]), tools=agent_tools, max_iters=max_iters)
    reviewer = dspy.ReAct(_signature(inputs, outputs, instr["assembled"],
                                     extra_inputs=[("draft", "the output and record of the fixed pipeline")]),
                          tools=agent_tools, max_iters=max_iters)

    def rigid(**kw):
        return program(**kw)

    def liquid_form(**kw):
        p = liquid(**kw)
        out = dspy.Prediction(**{k: getattr(p, k, None) for k in outputs}, reasoning=_trajectory_text(p))
        return _clean(out, outputs)

    def assembled_form(**kw):
        d = program(**kw)
        draft = json.dumps(record_of(d, outputs), ensure_ascii=False)[-6000:]
        p = reviewer(**kw, draft=draft)
        out = dspy.Prediction(**{k: getattr(p, k, None) for k in outputs},
                              draft=json.dumps({k: str(getattr(d, k, "")) for k in outputs}, ensure_ascii=False),
                              reasoning=_trajectory_text(p))
        return _clean(out, outputs)

    return {"rigid": rigid, "liquid": liquid_form, "assembled": assembled_form}
