# Results

GLM 5.3 Flash as the task model; each optimizer with its official settings; every number is PeachTrees minus that
optimizer's own program on the same items, in percentage points.

## Sealed test

Opened once, after the rule and every per-task decision were frozen (PeachTrees 1.0-lite).

| benchmark (test items) | over GEPA | over MIPROv2 | over SIMBA |
|---|---|---|---|
| NATURAL PLAN (200) | **+13.5** | **+17.0** | **+10.5** |
| LiveCodeBench (82) | **+11.0** | **+14.6** | **+13.4** |
| BIRD (200) | +2.5 | **+9.0** | +3.5 |
| GPQA (80) | +3.8 | 0.0 | +3.8 |
| ToolHop (200) | +2.5 | +2.0 | −0.5 (1 item of 200) |
| **mean** | **+6.7** | **+8.5** | **+6.1** |

Bold: 95 % confidence interval above zero. No cell has its interval below zero. Mean over the 15 cells: **+7.1 pp**.

## Development

13 benchmarks (AIME, GPQA, LiveBench, LiveCodeBench, HotpotQA, HoVer, IFBench, PUPA, BFCL, τ²-bench, NATURAL PLAN, BIRD,
ToolHop) × 3 optimizers = 36 cells.

Per benchmark (PeachTrees 1.0 full; bold: 95 % interval above zero; — : not run):

| benchmark | over GEPA | over MIPROv2 | over SIMBA |
|---|---|---|---|
| AIME | **+29.3** | **+23.3** | **+26.0** |
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
| over GEPA | +10.1 | +9.3 |
| over MIPROv2 | +8.7 | +8.4 |
| over SIMBA | +9.6 | +8.9 |
| **all 36 cells** | **+9.5** | **+8.9** |

No cell below the program; 24 of 36 significantly above. The rule was designed after these outputs were seen, so the
sealed-test numbers are the ones to quote.

## FNXL (financial token labeling)

GEPA vs GEPA + PeachTrees 1.0 on the FLARE FNXL test (318 sentences):

| | item score | macro-F1 | micro-F1 |
|---|---|---|---|
| GEPA | 0.600 | 0.376 | 0.393 |
| GEPA + PeachTrees (full) | 0.605 | **0.437** | **0.459** |
