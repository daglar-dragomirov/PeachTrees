# PeachTrees

A never-worse layer over the program produced by **any** prompt optimizer (GEPA, MIPROv2, SIMBA, ... or a hand-written
DSPy program).

After prompt optimization, the dominant remaining lever is often not *what the prompt says* but *which form executes the
task*. PeachTrees gives every task three forms and decides between them conservatively:

| Form | What it is |
|---|---|
| `rigid` | the optimizer's program, unchanged |
| `liquid` | a universal tool-using agent built from the program's own signature and the optimizer's learned guidance |
| `assembled` | the program's draft, checked and repaired by a universal reviewer agent |

Decisions, taken once per task on labeled data you do not report on:

1. **Default form** — keep the optimizer's program unless an alternative is better on the validation set with a paired
   bootstrap lower bound > 0.
2. **Judge threshold** — a universal asymmetric judge (keeps the default unless it names a specific, checkable defect an
   alternative avoids; swapped-order consistency; 3 votes) gets a confidence threshold calibrated on the validation set.
3. **Gate** — on a separate check set the judge is trusted only if it beats the default and wins more switches than it
   loses. Otherwise PeachTrees answers with the default form only.

The texts of the agents and the judge are fixed and identical for every task (`peachtrees/templates.py`).

## Usage

```python
import dspy
import peachtrees as pt

dspy.configure(lm=dspy.LM("openrouter/z-ai/glm-5.3-flash"))
program = optimized_program          # any dspy.Module, e.g. the output of dspy.GEPA(...).compile(...)

better = pt.wrap(program, metric=my_metric, valset=valset, checkset=checkset,
                 tools=[search],          # the task's tools for the agents (optional)
                 judge_tools=[search],    # READ-ONLY tools for the judge (never state-changing ones)
                 mode="lite")             # "lite": default form only (cheap); "full": + the per-item judge
print(better(question="..."))
print(better.decisions)                   # the default form, the judge threshold and the gate, with their evidence
```

`metric(example, prediction) -> float` in [0, 1]. `valset` should be the optimizer's validation set; `checkset` another
labeled set. Neither may overlap the data you report.

## Modes and cost

- `lite` answers with the task's default form only: about 1x the program's cost when the default stays `rigid`, a small
  multiple when an agentic form is chosen.
- `full` runs all three forms and the judge on every item (only if the gate trusted the judge): several times the cost.

## Status

Research code accompanying a paper in preparation. The `run_python` tool runs code in a subprocess with a 10 s limit; on
Linux it also drops network access when user namespaces are available. It is not a security sandbox.

## Credits

PeachTrees is a layer on top of existing optimizers and is built on [DSPy](https://github.com/stanfordnlp/dspy).
The experiments use [GEPA](https://arxiv.org/abs/2507.19457), MIPROv2 and SIMBA as the underlying optimizers.

License: to be decided by the authors.
