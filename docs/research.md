# Research record

How the 1.0 rule was found, frozen and tested. The files are in
[`research/`](https://github.com/daglar-dragomirov/PeachTrees/tree/main/research) on GitHub.

| step | what happened |
|---|---|
| v0.2 | forms + an LLM judge with a calibrated threshold and a gate: +6.6 pp over the programs (36 cells, development) |
| offline analysis | a replay of every saved per-item output, with no model calls, found a simpler rule that beats the judge |
| 1.0 frozen | the rule as code, replayed independently: +9.47 pp on the saved outputs, +9.41 pp after re-running only the outputs that had failed to parse |
| decisions frozen | the per-task decision fixed on FIT + PARETO + DEV before the test was opened |
| sealed test | 15 cells opened once: +7.1 pp, 7 significantly above the program, none significantly below |
| FNXL | GEPA vs GEPA + PeachTrees: macro-F1 0.376 → 0.437 |

## Protocol

- **Splits.** FIT (the optimizer's train set), PARETO (its validation set), DEV (development), TEST (sealed). Rules and
  thresholds were chosen on FIT and PARETO; DEV was used to report; TEST was opened once per cell after freezing.
- **Statistics.** Paired per-item differences; 95 % bootstrap intervals clustered by problem where items repeat.
- **Failures.** An output that could not be parsed was re-run with step-level retries in every arm, the program included,
  before the final numbers.
- **Cost accounting.** Every model call is priced; PeachTrees costs about 2.6× (lite) to 4.6× (full) the program.

## Why test is lower than development

The family of rules was designed after development outputs were seen. FIT ↔ PARETO cross-validation and a
leave-one-benchmark-out check protect the choice *within* the family, not the family itself. The largest drop is BIRD
over GEPA (+20.5 → +2.5), the cell with the strongest winner's curse in the analysis.
