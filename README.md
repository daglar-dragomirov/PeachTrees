<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/daglar-dragomirov/PeachTrees/main/assets/lockup-dark.png">
    <img src="https://raw.githubusercontent.com/daglar-dragomirov/PeachTrees/main/assets/lockup-light.png" alt="PeachTrees" width="460">
  </picture>
</p>

<p align="center">
Inference-time answer selection for optimized DSPy programs
</p>

<p align="center">
  <a href="https://daglar-dragomirov.github.io/PeachTrees/"><b>Website</b></a> &nbsp;|&nbsp;
  <a href="https://daglar-dragomirov.github.io/PeachTrees/guides/quickstart/"><b>Quick Start</b></a> &nbsp;|&nbsp;
  <a href="https://daglar-dragomirov.github.io/PeachTrees/results/"><b>Results</b></a> &nbsp;|&nbsp;
  <a href="research/"><b>Research</b></a> &nbsp;|&nbsp;
  <a href="https://pypi.org/project/peachtrees/"><b>PyPI</b></a>
</p>

<p align="center">
  <a href="https://pypi.org/project/peachtrees/"><img src="https://img.shields.io/pypi/v/peachtrees?logo=pypi&logoColor=white&label=pypi" alt="PyPI"></a>
  <a href="https://pypi.org/project/peachtrees/"><img src="https://img.shields.io/pypi/pyversions/peachtrees?logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/daglar-dragomirov/PeachTrees/stargazers"><img src="https://img.shields.io/github/stars/daglar-dragomirov/PeachTrees?logo=github&label=stars" alt="Stars"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License MIT"></a>
</p>

---

## What is PeachTrees?

A prompt optimizer such as GEPA, MIPROv2 or SIMBA turns your data into one fixed [DSPy](https://github.com/stanfordnlp/dspy)
program. That program is good, but it is also brittle: it cannot look anything up, cannot run code to check itself, and
every answer is a single sample. PeachTrees does not touch the optimization. It wraps the finished program with a
reviewer of its draft and an independent agent, picks one answer per input with a label-free rule, and switches itself
off on any task where it is not at least as good as the program.

## Install

```bash
pip install peachtrees
```

## Quickstart

```python
import dspy
from peachtrees import PeachTrees

dspy.configure(lm=dspy.LM("openrouter/z-ai/glm-5.3-flash"))

program = dspy.GEPA(metric=metric, ...).compile(student, trainset=train, valset=val)   # or MIPROv2, SIMBA, ...

pt = PeachTrees(program, mode="full", examples=train)
pt.fit(train + val, metric)        # decides once whether the layer helps this task
print(pt.report["use_layer"], pt.report["mean_gain"])

prediction = pt(question="...")    # same call signature as your program
```

`fit` only needs labeled data the optimizer already saw; nothing is tuned per dataset.

## How it works

### Three forms

| form | what it is |
|---|---|
| **rigid** | the optimized program itself, unchanged |
| **assembled** | the program writes a draft; a ReAct reviewer checks it against the task and fixes it only if it finds a concrete defect |
| **liquid** | a ReAct agent that solves the task from scratch |

Both agents get the same task-agnostic instructions: the program's own instructions (the task's purpose plus what the
optimizer learned), a few correct outputs from your examples, and one fixed template per form. They have `run_python`
and any task tools you pass. There is no task-specific prompt text anywhere.

### One answer per input

1. Drop forms whose output is missing or unparsable.
2. If you pass a deterministic, label-free `checker` (public unit tests, a SQL query that must run, a plan validator), drop
   forms that fail it. If all fail, keep all.
3. If two forms give the same answer, return it. Answers are compared with `answer_key` (default: normalized text).
4. Otherwise return the reviewer's answer, then the program's, then the agent's.

In `full` mode the agent only runs when the program and the reviewer disagree. `lite` mode runs the reviewer only.

### Never worse than the program

`fit` runs the forms on labeled selection data and compares PeachTrees with the program item by item. The layer is used
only if its mean gain is not below zero by more than one (clustered) standard error. Otherwise the wrapped object is
exactly the program, at exactly its cost.

## Results

GLM 5.3 Flash as the task model; each optimizer run with its official settings; every number is PeachTrees minus that
optimizer's own program on the same items.

**Sealed test** — opened once, after the rule and every per-task decision were frozen (PeachTrees 1.0-lite):

| benchmark (test items) | over GEPA | over MIPROv2 | over SIMBA |
|---|---|---|---|
| NATURAL PLAN (200) | **+13.5** | **+17.0** | **+10.5** |
| LiveCodeBench (82) | **+11.0** | **+14.6** | **+13.4** |
| BIRD (200) | +2.5 | **+9.0** | +3.5 |
| GPQA (80) | +3.8 | 0.0 | +3.8 |
| ToolHop (200) | +2.5 | +2.0 | −0.5 (1 item of 200) |
| **mean** | **+6.7** | **+8.5** | **+6.1** |

Bold: 95 % confidence interval above zero. No cell has its interval below zero.

**Development** — 13 benchmarks (AIME, GPQA, LiveBench, LiveCodeBench, HotpotQA, HoVer, IFBench, PUPA, BFCL, τ²-bench,
NATURAL PLAN, BIRD, ToolHop) × 3 optimizers = 36 cells:

Per benchmark (PeachTrees 1.0 full; bold: 95 % interval above zero; — : not run):

| benchmark | over GEPA | over MIPROv2 | over SIMBA |
|---|---|---|---|
| AIME | **+30.0** | **+23.3** | **+22.0** |
| NATURAL PLAN | **+24.0** | **+18.0** | **+21.0** |
| LiveCodeBench | **+17.0** | **+17.0** | **+18.0** |
| LiveBench | **+14.8** | **+19.3** | **+13.5** |
| BIRD | **+18.5** | +2.5 | **+6.5** |
| HoVer | **+6.7** | +3.7 | **+10.0** |
| GPQA | +5.1 | **+8.5** | +5.1 |
| ToolHop | **+8.0** | +0.5 | **+4.5** |
| HotpotQA | **+4.0** | +3.0 | **+5.7** |
| IFBench | **+2.2** | 0.0 | **+2.9** |
| PUPA | +1.7 | 0.0 | **+1.8** |
| τ²-bench | 0.0 | — | — |
| BFCL | 0.0 | — | 0.0 |

Averages:

| | full | lite |
|---|---|---|
| over GEPA | +10.2 pp | +9.4 pp |
| over MIPROv2 | +8.7 pp | +8.4 pp |
| over SIMBA | +9.2 pp | +8.7 pp |
| **all 36 cells** | **+9.4 pp** | **+8.8 pp** |

No cell below the program; 24 of 36 significantly above. The rule was designed after the development data was seen,
which is why the sealed-test numbers are the ones to quote.

**Research record**: how the rule was found, frozen and tested, with every number per cell, is in [`research/`](research/).

**Cost**: about 2.6× the program's inference cost in `lite` mode and 4.6× in `full` mode. There is no optimization
cost.

## API

```python
PeachTrees(program, *, mode="full", tools=(), answer_key=None, checker=None, examples=None,
           input_fields=None, output_field=None, z=1.0, max_iters=8, retries=3)
```

| argument | meaning |
|---|---|
| `program` | any `dspy.Module`, usually an optimizer's output |
| `mode` | `"full"`: program + reviewer, agent on disagreement, vote · `"lite"`: reviewer only |
| `tools` | task tools for both agents (`run_python` is always included) |
| `answer_key` | `callable(prediction) -> hashable`: how two answers are compared (a math normalizer, the result set of a SQL query, ...) |
| `checker` | `callable(inputs, prediction) -> bool \| None`: a deterministic, label-free check |
| `examples` | a few labeled examples whose correct outputs are shown to the agents |
| `input_fields`, `output_field` | inferred from the program's first and last predictors |
| `z` | non-inferiority margin in standard errors |
| `max_iters`, `retries` | agent steps; re-runs of a form whose output cannot be parsed |

`fit(selection_set, metric, num_threads=8, cluster=None)` makes the task decision; `report` holds the evidence
(`use_layer`, `mean_gain`, `se`, `program_score`, `peachtrees_score`, `picks`, per-item rows).

## FAQ

**Does it need a judge model?** No. Earlier versions used an LLM judge; it added +0.8 pp for most of the cost and was
removed. Agreement between independent forms and cheap deterministic checks do the job.

**Which optimizers?** Anything that produces a DSPy program. It was evaluated on GEPA, MIPROv2 and SIMBA.

**Is `run_python` a sandbox?** No. It runs code in a subprocess with a 10-second limit. Run untrusted workloads in an
isolated environment.

**What if it does not help my task?** Then `fit` says so (`use_layer = False`) and you get the program back, unchanged.

## Citation

```bibtex
@software{dragomirov2026peachtrees,
  author = {Dragomirov, Daglar},
  title  = {PeachTrees: Inference-time answer selection for optimized DSPy programs},
  year   = {2026},
  url    = {https://github.com/daglar-dragomirov/PeachTrees}
}
```

## License

MIT
