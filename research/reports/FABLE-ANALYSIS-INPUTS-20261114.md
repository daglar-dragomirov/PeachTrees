# Inputs for the PeachTrees elite analysis (Fable 5.2, xhigh) - 2026-11-14

User decision (2026-11-14): finish every PeachTrees run first, then Fable 5.2 (xhigh) analyses all saved logs to improve
PeachTrees; the improved method is frozen as PeachTrees 1.0 and evaluated ONCE on the sealed TEST splits.

## Scope (user, 2026-11-14): everything, not only the new datasets
All 13 datasets (HotpotQA, HoVer, IFBench, PUPA, AIME, GPQA-Diamond, LiveBench, LiveCodeBench, BFCL, tau2, NATURAL PLAN,
BIRD, ToolHop), all optimizers PeachTrees wraps (GEPA, MIPROv2, SIMBA; GEPA+Merge as a competitor), both GEPA seeds,
the compute-matched baselines (SC@k, B2) and the judge replays (J5*/J6*/J7b). Goal: the largest honest gain - per form,
per rule, per judge signal, cost - with no regression on any dataset or optimizer.

## Cost goal (user, 2026-11-14)
PeachTrees must be cost-effective. Per item it always runs the optimizer's program, so it cannot be cheaper than that
program alone; the analysis should minimise the extra cost: escalation (extra forms / judge only on items where the
cheap signals disagree or are uncertain), which forms are worth their cost per dataset type, lite vs full, and fewer
judge votes; and report gain per extra dollar against the compute-matched baselines (SC@k, B2) and against a stronger
single model at equal cost. Known: full ~7.7x, lite ~2.3x the program's cost; lite keeps ~83 % of the gain.

## Protocol for the analysis (binding)
1. A proposed change must be argued from general logic and from PARETO / FIT evidence, not tuned to one dataset's DEV.
2. It is applied to ALL datasets at once by replaying the saved per-item outputs (eval-selu-<ROLE>-<form>.jsonl, picks-*.jsonl);
   DEV numbers after the change are reported as post hoc (DEV was seen), never as the estimate.
3. Freeze PeachTrees 1.0 (rule text, thresholds, forms) and pre-register it; then run the sealed TEST once per dataset
   (TEST files: .external/fieldsuite-<name>-data-v1/sealed-test-v1/TEST.jsonl for the new datasets; see PROTOCOL.md).

## Priority (user, 2026-11-17): maximum gain WITHOUT re-running the forms
Order of work for the analysis:
1. Rule changes replayed offline on the saved per-item outputs of every form (default-form rule, thresholds, when to trust
   the judge, vote3): free, no model calls.
2. A much stronger judge, replayed over the SAVED form outputs (only judge calls; past judge replays cost 0.2-3.6 USD per
   dataset, ~15-30 USD for everything). Aim toward the per-item oracle (e.g. +17 pp mean on the added datasets vs +1.75
   reported): label-free verification signals where a task allows them (run the code on the statement's examples for LCB,
   execute the SQL for BIRD, check plan constraints for NATURAL PLAN, re-call tools for ToolHop), several votes, calibrated
   abstention. Judge model stays GLM 5.3 Flash (Chinese models only, <= 1 USD / M output).
3. Changes to the forms themselves (e.g. passing the optimizer's instructions and demos to the agents) only if 1-2 cannot
   reach the goal; they require re-running the PeachTrees form runs (~30-35 runs, ~60-100 USD, 1-2 days) and need the
   user's go-ahead with the cost stated first.
   User clarification (2026-11-17): partial re-runs are fine (the judge, a single new or changed form, only the datasets
   or optimizers that need it); avoid a full re-run of everything.

## Observations to start from (examples; the analysis covers every dataset above)
- BIRD (PTbr, run ba3fcfa7): DEV rigid 0.400, liquid 0.490, assembled 0.595, oracle 0.700; the v0.2 rule kept rigid because
  the GEPA program's PARETO score is inflated (GEPA selected it on PARETO: 0.50 PARETO vs 0.40 DEV, winner's curse on a
  50-item valset). Candidate fix: choose the default form on data the optimizer did not select on (e.g. FIT, or a
  winner's-curse correction of the rigid score); check the effect on every dataset by replay.
- BIRD competitor (2026-11-16): GEPA+Merge GMbr DEV 0.530 vs GEPA program 0.400 = PeachTrees as reported; the
  default-rule failure costs PeachTrees its lead over a competitor here (assembled 0.595 would lead).
- Forms on the added datasets (worker v85/v86 generic_shells, checked 2026-11-16): liquid and assembled get only the
  universal rev9 instructions + run_python (+ the task's tools for ToolHop); they do NOT receive the optimizer's
  instructions or demos, although the PeachTrees contract text says the agents inherit the program's guidance. On
  ToolHop over MIPROv2 (PTmth) liquid 0.505 vs the demo-carrying program 0.735. Candidate general change: pass the
  optimizer program's instructions and demos to the agents (check the original-dataset shells, which may differ).
- Wave 2 (2026-11-16, PROGRESS): competitors on the added datasets; GEPA+Merge .885 on NATURAL PLAN and .530 on BIRD
  beat PeachTrees-over-GEPA as reported (.830 / .400); PeachTrees over SIMBA NATURAL PLAN +0.040 while assembled alone
  would give +0.165: the default rule is too conservative on 50-item PARETO sets.
- ToolHop (PTth, run 05b62d8b): +0.105 [0.065, 0.150] via vote3 (judge not enabled); oracle 0.665 vs reported 0.570.
- NATURAL PLAN (NPa0): the seed program is already 0.94 on PARETO; little headroom (PTnp running).
- LiveCodeBench: PeachTrees +0.19 over GEPA; competitors SIMBA (24 h wall) and GEPA+Merge (GMc2 running) incomplete.
- 2nd seed: LiveBench +0.128 (replicates), IFBench 0.000, HotpotQA +0.007 n.s.
- Over MIPROv2 / SIMBA: about +10 pp on AIME, GPQA, LiveBench, HotpotQA; no regression anywhere.
- Earlier analysis notes: docs/ANALYSIS-PEACHTREES-20261110.md (oracle +14.1 pp vs +7.7 pp reported; lite 83 % of the gain).

## Where the data is
- Run directories: ~/.local/share/openresearch/local-runs/<runId>/repo/runs/<output>/worker/ (picks-*.jsonl, eval-*.jsonl,
  summary.json); run ids per round in PROGRESS.md; index of runs up to 2026-11-11 in s3://rider-4d/pause-20261111/INDEX-runs.csv.
- Comparison scripts: scripts/research_session_tmp_v2/pt_cmp.py (reported / lite vs the optimizer program, clustered CIs),
  scripts/peachtrees_free_analyses_v1.py (forms, oracle, judge rescue/harm).
