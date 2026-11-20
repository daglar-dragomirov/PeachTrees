# PeachTrees - elite analysis result (Fable 5.2), 2026-11-19

Scope: all saved PeachTrees runs (13 datasets x GEPA / MIPROv2 / SIMBA, GEPA seed 1, the SC@k / B2 baselines, the J6* /
J7b judge replays). Method: offline replay of the saved per-item outputs only. No model call was made, no run was
launched, the sealed TEST splits were never opened, nothing in the repository or the run directories was changed.
Main axis (user, 2026-11-19): the "golden ratio" = maximum honest gain for the minimum re-run cost.

All gains are in percentage points (pp) of the task score over the optimizer's own program ("rigid") on the same DEV
items, macro-averaged over cells (cell = dataset x optimizer). "36 cells" = GEPA 13 + MIPROv2 11 + SIMBA 12 (seed 0).
Every DEV number for a NEW rule is post hoc (DEV was seen); the selection of the rule is described next to it.

---------------------------------------------------------------------------------------------------------------------

## 0. Bottom line

### 0.1 The Pareto front (cheap -> expensive)

| # | Option | Re-run cost | Wall time | Gain over the program, 36 cells (DEV) | vs reported | Inference cost (x program) | Gain per re-run dollar |
|---|---|---|---|---|---|---|---|
| P0 | v0.2 rule + J6* judge, as reported | - | - | +6.59 (GEPA +7.59, MIPROv2 +6.09, SIMBA +5.95), worst 0 | 0 | x9.1 (median x7.6) | - |
| P1 | 1.0-lite: non-inferiority rule + reviewer form with liveness / checker fallback | 0 USD | 0 (replay) | +8.91 (+9.78 / +8.17 / +8.65), worst 0 | +2.3 | x2.6 | free |
| P2 | 1.0-full: non-inferiority rule + "verify -> vote -> reviewer" over the three saved forms | 0 USD (25-40 min CPU: SQL execution, public tests) | < 1 h | +9.47 (+10.57 / +8.40 / +9.24), worst 0; honest range +9.1..+9.5 (see 3.1) | +2.9 | x4.6 (x3.5 with auto-lite, +9.38) | free |
| P3 | P2 + parse-failure repair (re-run ONLY the rows where a form returned no parsable output; every arm incl. the program) | ~6 USD | 2-3 h | integrity fix, not a gain: +8.8 (only the baseline benefits) .. +9.6 (rows without any failure) | +2.9 on the same basis | same | n/a (removes the strongest reviewer objection) |
| P4 | P3 + BIRD: give the two agent forms (and the verifier) a read-only run_sql tool; re-run liquid + assembled on BIRD only (3 optimizers, PARETO/FIT/DEV) | ~3-4 USD | 1.5-2 h | est. +0.4..+0.8 more (BIRD cells +5..+10) | +3.3..+3.7 | same | ~0.1-0.25 pp / USD |
| P5 | + verifier judge v2, replayed over SAVED outputs, only contested items of the 8 verifiable datasets | ~7-10 USD (P+F first: ~3 USD, then DEV only where the gate passes) | 3-5 h | est. +0.7..+1.2 more (hard upper bound +2.4) | +3.6..+4.9 | + ~0.5-1.5x on exact-match tasks | ~0.1-0.15 pp / USD |
| P6 | pass the optimizer's demos to the agents (MIPROv2 / SIMBA cells), re-run liquid + assembled there | ~35-45 USD | 1-2 days | est. +0.1..+0.4 | - | same | < 0.01 pp / USD |
| P7 | full re-run of all forms | 60-100 USD | 1-2 days | nothing that P1-P5 do not give | - | - | ~0 |

For comparison: the v0.2 judge (J6*) cost 46.9 USD of replay and added +0.77 pp of genuine judge switches (0.016 pp / USD);
38.9 USD of it was spent in cells where the judge was finally switched off.

### 0.2 The one recommended option

**P2 + P3: freeze "PeachTrees 1.0-full" from the saved outputs (0 USD) and run the parse-failure repair (~6 USD, 2-3 h).**

Why this is the knee of the curve:
- it takes 95 % of what ANY task-level choice among these label-free policies could give (+6.59 -> +9.47; the ceiling
  of the family is +9.97; the per-item oracle, +14.87, needs a per-item verifier or better forms) for zero model dollars;
- it is at the same time ~2x cheaper at inference than v0.2-full (x4.6 instead of x9.1; x3.5 with auto-lite), because
  the LLM judge is removed and liquid is run lazily;
- no cell regresses (0 of 36 below the program; 24 of 36 significantly above; 9 cells significantly above the reported
  v0.2 number, none significantly below);
- every hyper-parameter was chosen without DEV (PARETO <-> FIT cross-validation), and the leave-one-dataset-out choice
  gives the same number (+9.47);
- P3 costs 6 USD and closes the one hole that would otherwise cost the paper its credibility (12-14 % of the baseline
  program's LiveCodeBench rows over MIPROv2 / SIMBA are parse failures scored 0).

P4 (BIRD SQL tool, ~4 USD) and P5 (verifier replay, ~7-10 USD) are the next two steps in gain per dollar; both are
optional, both are gated on PARETO / FIT, and both can be decided after P2/P3 without touching DEV-based selection
(P5: replay PARETO + FIT first for ~3 USD; continue to DEV only where the gate passes). P6 and P7 are not worth it.

Expected honest result on the sealed TEST (macro over the same 36 cells): about +8.5 .. +9.5 pp over the optimizer
programs (v0.2 as reported: +6.6 on DEV), with no significant regression in any cell.

---------------------------------------------------------------------------------------------------------------------

## 1. Data inventory

Used (run directory = ~/.local/share/openresearch/local-runs/<run>/repo/runs/fieldsuite-v04-<name>/worker):

| Group | Cells (name: run) |
|---|---|
| PeachTrees over GEPA, seed 0 (13) | hotpotqa j6h 51f29d0c, hover j6v 7a550e54, ifbench j6i ef08a4e2, pupa j6p cacfcdb6, aime j6a 1fb09bf6, gpqa j6g f3d7e532, livebench j6l 3b5470ab, lcb j6c 8cb145ba, bfcl j7b 0e8a1486, tau2 u8j 4106cc88, natplan ptnp 723fdbec, bird ptbr ba3fcfa7, toolhop ptth 05b62d8b |
| form outputs of the judge replays (select.replay_from) | v5h b717bff1, v5v 4e2148f3, v7i f6848839, v7p 3dbb0640, v6a a80cb339, v7g 103bd160, v7l aa9030ff, v7c 89883441, v5b 4fe546a3 (tau2: u8a c944e12d + u8b f529c751, picks only) |
| GEPA seed 1 (3) | livebench pt1l e74667a4, ifbench pt1i e9566f93, hotpotqa pt1h 933b613b |
| over MIPROv2 (11) | aime ptma 373ebb35, gpqa ptmg fc9a9518, livebench ptml b8094693, hotpotqa ptmh cfb4ee33, lcb ptmc 2b7cf7ca, natplan ptmnp 233c3473, bird ptmbr 27396660, toolhop ptmth 07ea0e7a, ifbench ptmi 9efb36d0, hover ptmv 17cc3d65, pupa ptmp ac87499a |
| over SIMBA (12) | aime ptsa 53d9b7c6, gpqa ptsg 18545a67, livebench ptsl2 362b84eb, hotpotqa ptsh fd41b786, lcb ptsc eaaee5df, natplan ptsnp 2f5acff5, bird ptsbr 0d82291e, toolhop ptsth c293dc3f, ifbench ptsi 5cf5f7f8, hover ptsv ef8aade0, pupa ptsp b6699861, bfcl ptsb cc9dd01f |
| compute-matched | KMa b86d7e5b, KMg 36047627, KMl 20ece236 (SC@k); B2a / B2g / B2l (judge over 3 program samples) |

Per cell: picks-{PARETO,FIT,DEV}.jsonl (scores of the three forms, the judge's decision incl. suppressed proposals and
confidence), eval-selu-<ROLE>-<form>.jsonl (answer, trajectory, error), summary.json (per-item costs).
Sanity: the scores in the eval files equal the scores in the picks for every row (0 mismatches).

Excluded: ptmb (BFCL over MIPROv2 - technical fault); the 402-stopped runs d62dede0, 7a33a69a, 2f04f401, 59f8142f; the
incomplete v4c / v5a / v5c / v6c / u5t; the older judge versions j5*. Never read: anything under sealed-test / TEST.

Label-free signals computed offline for this analysis (no model calls, gold never used):
- task-aware answer keys = the task metric's own canonicalisation of an answer (math normaliser, option letter,
  ToolHop normaliser, parsed trip / meeting plan, canonical BFCL call list, and for BIRD the hash of the RESULT SET of
  the executed query: 3,600 saved queries executed read-only, 3,408 ran);
- liveness (the form returned a parsable output), "the reviewer changed its draft";
- NATURAL PLAN: a validator of the constraints stated in the problem (unit check: all 300 reference plans of
  PARETO / FIT / DEV pass it); LCB: the last public-test result found in the agents' own trajectories; BIRD: the query
  runs / returns at least one non-NULL row.

---------------------------------------------------------------------------------------------------------------------

## 2. Reproduction and diagnosis

### 2.1 The reported numbers reproduce

| | cells | reported (v0.2 + J6* + FIT gate) | v0.2 lite | always assembled | always vote3 | per-item oracle |
|---|---|---|---|---|---|---|
| GEPA | 13 | +7.59 | +5.76 | +8.11 (worst -8.2) | +5.15 (worst -2.0) | +15.63 |
| MIPROv2 | 11 | +6.09 | +5.43 | +6.88 (worst -1.2) | +4.17 | +14.88 |
| SIMBA | 12 | +5.95 | +3.76 | +5.75 (worst -4.1) | +3.23 | +14.03 |
| all | 36 | +6.59 | +4.99 | +6.95 (3 cells negative) | +4.21 | +14.87 |

14 of the 36 cells report exactly the program (tie by construction: default rigid and the judge off).

### 2.2 Why the v0.2 default rule lost gain

1. It asks for significance (paired 95 % lower bound > 0) on PARETO alone, i.e. on 45-50 items in 17 cells. Half of the
   cells (18 / 36) kept rigid. NATURAL PLAN over GEPA and SIMBA is the clearest miss: liquid / assembled were +2..+12 pp
   on PARETO and +10..+14 pp on FIT, not "significant" at n = 50, and +15..+17 pp on DEV.
2. It ignores FIT (another 45-300 labeled items with all three forms already computed) for the default.
3. It can only choose among four fixed policies (rigid, liquid, assembled, vote3 with a RIGID fallback). The best
   label-free policy - majority, else the reviewer - was not a candidate.
4. A form that returns no output is not replaced unless the judge is enabled (then: mode default_failed).
5. The winner's curse is real but is NOT the main story. Difference-in-differences (how much better rigid looks on the
   selection data than on DEV, relative to the assembled form), 36 cells: PARETO +0.98 +- 1.00 pp, FIT +1.88 +- 1.02 pp.
   It is large only where a big optimizer budget met a small valset: BIRD-GEPA +22.5 / +20.5 pp (PARETO / FIT),
   NATURAL PLAN-GEPA +16.5 / +2.5. Rigid's own drop from selection data to DEV: GEPA +2.3 (PARETO) / +3.9 (FIT),
   MIPROv2 +0.4 / +3.2, SIMBA +1.2 / +3.0 pp. Conclusion: a rule that demands "significantly better than rigid on the
   optimizer's own data" is biased against switching by ~1-2 pp on average and by 10-20 pp in the worst cells; the fix
   is to turn the burden of proof around (3.1), not to estimate the bias.

### 2.3 Why the judge was rarely enabled, and what it really did

- PARETO threshold = "off" in 19 of 36 cells; FIT gate passed in 14.
- "reported - v0.2 lite" = +1.60 pp macro, of which only +0.77 pp are genuine judge switches; +0.83 pp are liveness
  rescue (the default form had no output and another form was taken) - a free operation that needs no judge.
- All proposals of the judge on DEV, regardless of threshold and gate: 210 won, 85 lost, 484 neutral; precision 71 %,
  recall 29 % of the items where a better form existed.
- It is two different judges. On the datasets where an answer can be checked (AIME, GPQA, LiveBench, HotpotQA, LCB,
  NATURAL PLAN, BIRD, ToolHop) all its proposals are 173 won / 34 lost (149 / 9 without ToolHop, where it had no
  call_tool); on the rubric / retrieval datasets (HoVer, IFBench, PUPA, BFCL, tau2) 37 won / 51 lost. Restricted to the
  items that are still contested after the new free rule (and where its reference equals that rule's choice):
  12 won / 1 lost vs 25 won / 43 lost.
- Money: 46.9 USD of judge replay in total; HoVer 14.6 + IFBench 12.2 + PUPA 7.8 = 34.6 USD (74 %) went to the three
  datasets where it never helped; 38.9 USD were spent in cells where the gate then switched it off. Per item the judge
  costs up to 12-14x the program (HoVer, IFBench, BIRD).
- On the added datasets the judge was blind: generic_shells returns no _judge_tools, so on NATURAL PLAN / BIRD / ToolHop
  it had run_python only (no SQL execution, no call_tool). ToolHop over MIPROv2 / SIMBA: 4 won / 13 lost, 12 / 9.

### 2.4 Form failures are infrastructure failures

Almost every "error" row is `AdapterParseError` of the DSPy JSONAdapter (GLM answers `{"": ...}` with an empty field
name, or an empty reply) - the same symptom as the excluded MIPROv2-BFCL "load fault". Shares of DEV rows without a
parsable output (rigid / liquid / assembled): LCB over MIPROv2 12 / 28 / 27 %, LCB over SIMBA 14 / 28 / 29 %, AIME over
SIMBA 0 / 15 / 17 %, ToolHop over GEPA 6.5 / 0.5 / 4 %, NATURAL PLAN over GEPA 3 / 3 / 5 %, 4-8 % of the agent rows on
AIME / GPQA / LiveBench over MIPROv2 / SIMBA. Two consequences:
- the forms lose accuracy for a reason unrelated to the method (fixed for free by a liveness fallback, 3.2);
- the BASELINE loses too: 12-14 % of the program's LCB rows over MIPROv2 / SIMBA and 6.5 % of its ToolHop rows over GEPA
  score 0 for a parse failure, and PeachTrees "wins" those rows by answering with another form. Conservative
  adjustment (impute the program's failed rows with its accuracy on its other rows, leave PeachTrees unchanged):
  reported +6.59 -> +5.94; new rule +9.47 -> +8.82. On the rows where no form failed at all the gains are +6.97 and
  +9.64. So the effect roughly cancels in the macro, but it moves single cells a lot (LCB over MIPROv2 +17.0 -> +9.4
  conservative, +18.3 on clean rows; ToolHop over GEPA +13.0 -> +9.8 / +7.9) and must be removed before TEST (P3).

### 2.5 What the agreement between forms says (the basis of the new item rule)

With the worker's text keys the three forms all differ on 49.5 % of the items; with task-aware keys BIRD goes from
83 % "all different" to 7 % (45-48 % all three queries return the same result set). When the two agents agree against
the program, the program is right 29 %, the agents 88-90 % (macro, DEV).

Agreement table learned on PARETO + FIT only (pooled over the 36 cells; A = reviewer's answer, D = its draft = one
sample of the program, R = the program's own, independent output, L = liquid agent; accuracy of choosing A / R / L):

| pattern | n (P+F) | A | R | L | reading |
|---|---|---|---|---|---|
| A=D=R=L | 2188 | .890 | .890 | .890 | unanimous |
| A=D, R=L differ (reviewer kept its draft; program sample and agent agree on something else) | 114 | .433 | .615 | .615 | take the majority |
| A=D=R, L differs | 287 | .613 | .616 | .328 | keep |
| A=D=L, R differs | 222 | .773 | .224 | .770 | keep |
| A=L, D=R (reviewer changed the draft, the agent agrees with the reviewer) | 40 | .725 | .150 | .725 | reviewer |
| A alone, D=R, L alone (reviewer changed the draft, nobody agrees) | 21 | .619 | .238 | .238 | reviewer |
| all four differ | 601 | .849 | .733 | .803 | reviewer |
| reviewer has no output, R and L differ | 52 | - | .303 | .666 | (LCB-heavy; an artefact of 2.4) |

The same patterns hold on DEV (not used for the table), e.g. "A=D, R=L differ": A .332, R = L .579 (n = 136);
"A=L, D=R": A .860, R .053 (n = 57).
One counter-intuitive fact that matters for the design: when the reviewer CHANGED its draft and the liquid agent
reproduces the draft, the reviewer is right 19 / 25 times (DEV; 17 / 28 on PARETO + FIT) and the draft 8 / 25. A naive
"2 against 1 for the draft" vote is wrong there; the vote helps only when the second vote for the other answer comes
from an INDEPENDENT sample of the program. Hence the item rule in 3.2 votes over R (independent), A and L, and a
shared-draft "lazy" variant was rejected (it loses 13 items and wins 2 against the reviewer alone).

### 2.6 Notes per dataset (seed 0; numbers in section 9)

- HotpotQA: forms agree on 79 %; small gains everywhere (+3..+6). v0.2 kept rigid over MIPROv2 (PARETO not significant).
- HoVer: the output is a document set, no agreement signal exists; assembled +6.7 / +3.7 / +10.0; the judge was harmful
  (7 / 19, 0 / 3, 11 / 11) and cost 14.6 USD; liquid is far below (0.28 over MIPROv2). The residual 5 pp cannot be
  reached by selection.
- IFBench, PUPA: near the ceiling; assembled is +1..+3 pp where it helps and -1.2 pp (IFBench over MIPROv2) where it
  does not; PARETO + FIT separate these cases correctly (-2.3 +- 1.0, -2.7 +- 1.4). The judge is useless here.
- AIME, LiveBench: the largest gains (+13..+30); the vote adds +1..+5 pp over the reviewer; agent parse failures are
  frequent over SIMBA / MIPROv2.
- GPQA: PARETO / FIT are GPQA-main, DEV is Diamond - the program scores 0.60-0.71 on the selection data and 0.74-0.81
  on DEV, and the forms' advantage on PARETO / FIT (+7..+9 pp) shrinks to +1 pp for assembled alone; the vote is what
  works (+5.1 / +8.5 / +5.1).
- LCB: +17..+18 pp; 40 % of the rows over MIPROv2 / SIMBA have a failed form (2.4); the public tests are a strong
  checker (last public-test result in the agent trajectory: pass -> 83-96 % correct, fail -> 1 of 51 correct, GEPA cell).
- BFCL (n = 49): assembled is worse than the program on PARETO and FIT (-6.1 +- 3.2, -3.0 +- 2.2); every sound rule
  keeps the program.
- tau2: ceiling (0.993).
- NATURAL PLAN: the largest v0.2 miss (reported +11.0 / +11.0 / +4.0, available +24.5 / +18.0 / +21.0 = the oracle).
  A plan that passes the statement's constraints is correct 97-100 % of the time, a failing one 0-12 %.
- BIRD: the agents have NO database access (run_python only), so the reviewer cannot execute the draft query. Still
  assembled is +19.5 pp over the GEPA program on DEV; v0.2 kept rigid (PARETO 0.50 / 0.48 / 0.48). Queries that return
  no rows or only NULLs: 111 outputs, 0 correct. Oracle +30 / +18.5 / +18.
- ToolHop: over GEPA +13.0 (+9.8 after the parse-failure adjustment); over the demo-carrying MIPROv2 / SIMBA programs
  the liquid agent (instructions but no demos) is at 0.505 / 0.49 vs 0.735 / 0.73 and only the reviewer + vote help
  (+0.5 / +4.5).
- A correction to the analysis inputs: in all 36 saved runs the agents DO receive the optimizer's instructions
  (summary.json, universal_agent_instructions: "Guidance learned for this task by an optimizer ...", inherit_rigid
  true), plus five label examples in 22 cells; what they do not receive is the optimizer's DEMOS.

---------------------------------------------------------------------------------------------------------------------

## 3. Improvements, ranked by gain per re-run dollar

### 3.1 [free] The task-level rule: non-inferiority around a fixed prior policy (largest single effect)

Rule text. Let pi1 be the item policy of 3.2 and S the selection data (PARETO + FIT pooled; for TEST: + DEV).
d = mean over S of (score of pi1 - score of the program), se = its standard error (clustered where items repeat).
**Use pi1 if d + 1.0 * se >= 0; otherwise use the program alone.** Nothing else is selected per task.

Logic. v0.2 keeps the optimizer's program unless an alternative is proven better on the optimizer's own data - data on
which the program is optimistically scored (2.2). pi1 is a superset of the program by construction (the reviewer is
told to return the draft unless it finds a fixable defect; the vote can only overrule it with two independent
agreeing answers), so the burden of proof is reversed: leave pi1 only on evidence that it hurts. One standard error is
both the natural tolerance and about the size of the measured optimism.

How it was selected (no DEV): 60 rule variants (argmax rules with 5 significance levels, with / without liquid;
non-inferiority rules with 2 priors x 5 margins; the same with an "upgrade" step) were scored by PARETO <-> FIT
cross-validation (fit on one, score on the other). Best: NI with prior pi1, margin 1.0 se (CV +8.17 pp with the
checkers, +7.77 without) - tied within 0.02 pp with its "upgrade" variant NIU (z2 = 1.0); the simpler rule is kept.
Leave-one-dataset-out on DEV (choose the variant on the other 12 datasets) selects the NI rule with this prior for
every held-out dataset (its margins 0 .. 1.28 se give identical decisions, see below).

Replay (36 cells, DEV, post hoc):

| rule (item policy = verify -> vote -> reviewer) | GEPA | MIPROv2 | SIMBA | all | worst cell | cells < 0 |
|---|---|---|---|---|---|---|
| v0.2 rule, lite | +5.76 | +5.43 | +3.76 | +4.99 | 0 | 0 |
| argmax on PARETO + FIT, 95 % lower bound > 0 | +8.48 | +7.67 | +7.69 | +7.97 | 0 | 0 |
| argmax on PARETO + FIT, mean > 0 | +10.27 | +8.08 | +8.59 | +9.04 | 0 | 0 |
| **NI, margin 0 .. 1.28 se (recommended: 1.0)** | **+10.57** | **+8.40** | **+9.24** | **+9.47** | 0 | 0 |
| NI, margin 1.645 se | +10.57 | +8.40 | +8.90 | +9.35 | -4.08 | 1 |
| no rule (always pi1) | +10.10 | +8.40 | +8.90 | +9.18 | -6.12 | 3 |
| NIU (the CV co-winner) | +10.25 | +8.40 | +8.62 | +9.14 | 0 | 0 |
| leave-one-dataset-out choice | +10.57 | +8.40 | +9.24 | +9.47 | 0 | 0 |
| ceiling of any task-level rule over this family (best policy per cell, chosen on DEV) | +11.08 | +9.19 | +9.48 | +9.97 | | |

Without the deterministic checkers of 3.3 the same rule gives +9.16 (+10.30 / +8.08 / +8.91).
Robustness: the rule rejects pi1 in 4 cells (BFCL x 2, IFBench and PUPA over MIPROv2; z = -1.4 .. -2.3) and accepts it in
32 (z >= 0); no cell lies between -1.36 and 0, so every margin from 0 to 1.3 se gives identical decisions.
GEPA seed 1: LiveBench +13.2, IFBench +1.5, HotpotQA +1.0 (reported +12.8 / 0.0 / +0.7).
Honest estimate: +9.1 (CV co-winner) .. +9.5 (CV winner = LODO choice) post hoc on DEV; +8.8 after the conservative
parse-failure adjustment of 2.4.
Cost: none; it removes the judge (inference x9.1 -> x4.6).

### 3.2 [free] The item rule pi1: liveness -> checker -> vote -> reviewer

1. Liveness: a form without a parsable output is dropped.
2. Checker (only for tasks that have a deterministic, label-free one; see 3.3): forms whose output fails are dropped;
   if all fail, all are kept.
3. Vote: answers are compared with the task metric's own canonicalisation (never with gold). If at least two
   surviving forms give the same answer, that answer is returned.
4. Otherwise the reviewer's answer (assembled); if it is missing: the program's; then the agent's.

"R" must be the program's own output from a separate call, not the reviewer's draft (2.5) - exactly what the saved
runs contain.

Contribution of the parts (36 cells, with the NI rule): reviewer alone with liveness fallback +8.49; + task-aware vote
+9.16; + checkers +9.47 (reviewer + checkers without the vote: +8.91). v0.2's vote3 (text keys, rigid fallback) as a
fixed policy: +4.21 with 5 negative cells.

### 3.3 [free] Deterministic checkers where the task has one

| task | checker (label-free) | evidence in the saved outputs | effect |
|---|---|---|---|
| NATURAL PLAN | the plan satisfies the constraints stated in the problem (trip: cities, stays, direct flights, day windows; meeting: the valid-meeting count of the official validator, keep the maximum among the forms) | valid -> 97-100 % correct, invalid -> 0-12 % | +3.5 / +3.5 / +4.0 pp on the three cells (to +24.5 / +18.0 / +21.0 = oracle +25.5 / +18.5 / +22.0) |
| LCB | the statement's public tests (the tool the agents and the judge already have) | pass -> 83-96 %, fail -> ~0-5 % (agents only; the program's code was not tested offline) | small in the replay (agents rarely end on a failing program); running the public tests on all three final programs is a 0-USD, ~15 min CPU step |
| BIRD | the query executes and returns at least one non-NULL row; equality = same result set | empty or NULL-only result: 0 of 111 outputs correct; not executed offline (incl. 30 s timeouts): 6-21 % correct | small: the result-set vote is -2.0 / -1.5 / +1.0 pp vs the reviewer alone (GEPA / MIPROv2 / SIMBA); the non-empty filter adds 0..+1.5 pp (not in the headline numbers) |

They are the tasks' own tools, not new judges; the paper can report the rule with and without them (+9.47 / +9.16).

### 3.4 [free] Cost: lazy liquid, auto-lite, no judge

| configuration (NI rule) | gain, 36 cells | cost x program (mean / median) | pp per extra x |
|---|---|---|---|
| v0.2 lite | +4.99 | 2.2 / 1.6 | 4.1 |
| v0.2 + J6* (reported) | +6.59 | 9.1 / 7.6 | 0.8 |
| 1.0-lite (reviewer + fallback + checkers; liquid never run) | +8.91 | 2.6 / 2.5 | 5.6 |
| 1.0 auto-lite (full rule only where the vote changes >= 2 % of the answers on PARETO + FIT; reviewer only in 13 cells) | +9.38 | 3.5 / 3.4 | 3.7 |
| 1.0-full (liquid only when program and reviewer disagree) | +9.47 | 4.6 / 4.4 | 2.6 |

Liquid is worth its cost on exact-match tasks (AIME, GPQA, LiveBench, HotpotQA, ToolHop, NATURAL PLAN, BIRD: +0.5..+4 pp
through the vote) and worth nothing where outputs are free text / code / document sets (HoVer, IFBench, PUPA, LCB,
BFCL, tau2: no two outputs are ever equal, pi1 = the reviewer).
Against self-consistency of the GEPA program at equal or higher cost (KM runs, DEV): AIME SC@5 0.747, SC@7 0.793 vs
1.0-lite 0.860 (x2.3) and 1.0-full 0.873 (x4.0); GPQA SC@4 0.788, SC@8 0.805 vs 0.822 (x2.9) and 0.864 (x4.4);
LiveBench SC@4 0.686, SC@7 0.710 vs 0.727 (x3.9) and 0.761 (x6.1). (The KM program draws are slightly lower than the
PeachTrees-run draws: SC@1 0.540 / 0.763 / 0.602 vs 0.573 / 0.814 / 0.613.) B2 (the judge over three program samples):
+2.0 / +5.1 / +7.7 pp vs +30.0 / +5.1 / +14.8 for 1.0-full.
A stronger single model at equal cost: no saved data; not analysed.

### 3.5 [free at TEST time] Selection data = PARETO + FIT + DEV

For the sealed TEST the NI rule should be fitted on PARETO + FIT + DEV: DEV is the only split on which the program is
not optimistically scored, its form outputs exist already, and it triples the selection data in the small cells. With
DEV added the decision changes in one cell only (PUPA over MIPROv2: rigid -> pi1; DEV +1.1). Cross-fitting inside DEV
(select on half, score on the other half, 200 splits, argmax rule) gives +8.4..+8.7 - i.e. clean selection data alone
does not beat the NI rule on PARETO + FIT; the two together are the TEST protocol.

### 3.6 [~6 USD] Parse-failure repair (integrity; P3)

Re-run only the rows where a form returned no parsable output, for every form and every role, with retry-on-parse-
failure (<= 3 attempts); the same for the competitor baselines' own DEV rows. Rows: e.g. LCB over MIPROv2 32 / 66 / 70
(rigid / liquid / assembled), LCB over SIMBA 33 / 71 / 73, AIME over SIMBA 0 / 28 / 35; estimated 5.9 USD in total, 4.7 of
it on the two LCB cells; 2-3 h. Expected effect on the macro gain: between -0.65 pp and +0.2 pp; on single cells large
(2.4). This also unblocks PeachTrees over MIPROv2 on BFCL (the excluded ptmb shows the same `{"": ...}` symptom).

### 3.7 [~3-4 USD] BIRD: the task's database as a tool for the agents (P4, a form change on ONE dataset)

Add `run_sql(query)` (read-only, row-limited, 30 s) to the tools of liquid, assembled (and of the verifier) on BIRD
- the same status as call_tool on ToolHop, search on HotpotQA and run_public_tests on LCB. Re-run liquid + assembled on
BIRD only: 3 optimizers x (50 + 50 + 200) items, ~1.5 USD at today's step counts, ~3-4 USD with tool steps, ~1.5 h.
The rigid outputs, every other dataset and the rule stay untouched. Expected: +5..+10 pp on the BIRD cells (today
+18.5 / +2.5 / +6.5, oracle +30 / +18.5 / +18), i.e. +0.4..+0.8 pp macro; the gain is not measured - it must show on
PARETO + FIT before it is used. Caveat for the paper: the program itself has no database access, so this widens the
"it is just tools" objection (as LCB's public tests already do).

### 3.8 [~7-10 USD] Verifier judge v2, replayed over saved outputs (P5) - design in section 4

### 3.9 [not recommended] Demos for the agents (~35-45 USD), full re-run (60-100 USD)

The liquid agent is the weakest form over demo-carrying programs, but the rule never selects it there and the reviewer
already matches or beats those programs; the only path to gain is more correct votes on ToolHop / HotpotQA / NATURAL
PLAN (+0.1..+0.4 pp macro at best), while the re-runs include the expensive HoVer / IFBench / PUPA cells.

---------------------------------------------------------------------------------------------------------------------

## 4. The stronger judge ("verifier"), precisely

What is left for a per-item judge after pi1 (DEV, 36 cells): the gap to the oracle is 5.4 pp, of which 3.6 pp per cell
sit in contested items (no majority) of the 8 verifiable datasets = at most +2.4 pp macro; the rest is in the rubric
datasets (where the judge has 37 % precision) and in wrong 2:1 majorities.

Scope. Datasets: AIME, GPQA, LiveBench, HotpotQA, ToolHop, BIRD, LCB (NATURAL PLAN is solved by the deterministic
validator). Items: only contested ones (after liveness and checker at least two different answers survive and no two
agree) - 3-33 % of the items on exact-match tasks, ~70-80 % on LCB, ~10 % on BIRD with result-set keys. Never on
HoVer / IFBench / PUPA / BFCL / tau2 (off by design).

Protocol per contested item. Model: GLM 5.3 Flash, ReAct, <= 6 tool steps.
1. Input: the task inputs and purpose; the reference (pi1's answer = the reviewer's) and the other surviving answers
   with their trajectories; for each answer the deterministic evidence sheet (below).
2. The verifier must design and RUN one discriminating check - a computation or tool call whose outcome differs
   between the candidate answers - and only then answer KEEP / A / B, quoting the observation.
3. Evidence gate (code, not the model): a switch counts only if the trajectory contains a tool observation produced
   after the candidates were shown and the answer cites it; otherwise KEEP.
4. Votes: one call; KEEP ends the item (most items). A proposed switch triggers two more independent calls with the
   alternatives swapped; the switch needs 2 of 3 on the same candidate.
5. Calibration on PARETO + FIT pooled, never DEV: confidence threshold in {none, 3, 4, 5} maximising the gain; the
   verifier is enabled in a cell only if gain > 0.005, switches won > lost and won - lost >= 2.

Evidence sheets and tools per task type:

| task | deterministic evidence shown | tools | the discriminating check |
|---|---|---|---|
| LCB | public-test results of every candidate program | run_public_tests, run_program(code, stdin) | 5-10 extra inputs from the statement's edge cases, a brute-force reference where feasible; candidates are run on them (differential testing) |
| BIRD | each query's columns, row count, first rows; error / empty flags | run_sql (read-only) | auxiliary queries on the filter literals, join keys and value formats the candidates disagree on |
| ToolHop | the tool-call chain of each trajectory | call_tool | re-execute the hops on which the trajectories diverge; check the answer's exact form |
| AIME / LiveBench / GPQA | - | run_python | brute force / simulation / substituting each candidate answer back into the conditions |
| HotpotQA | - | search | retrieve the bridging fact the candidates disagree on |

Cost of the replay over saved outputs, at the J6* unit price per judged item (0.002-0.005 USD, three votes with tools):
PARETO + FIT 2.1 USD, DEV 2.1 USD for the 7 datasets x 3 optimizers; with richer tool use x1.5-2: **~7-10 USD in all**
(PARETO + FIT first, ~3 USD; DEV only for cells whose gate passes). The same replay on HoVer / IFBench / PUPA would
cost 36 USD more - excluded. Wall time 3-5 h at 3-4 concurrent replays. Inference cost when enabled: + ~0.5-1.5x the
program on exact-match tasks.

Expected gain: +0.7 pp macro if it only matches the recorded judge on these items (12 won / 1 lost, extrapolated to
full coverage), up to ~+1.2 with task tools on BIRD / ToolHop; hard ceiling +2.4. Overlaying the RECORDED J6* decisions
where they are applicable (the judge's reference equals pi1's choice) already gives +0.2 pp (to +9.67) with the same
gate: AIME-GEPA +3.3, GPQA-GEPA +1.7, HotpotQA +0.7 / +1.0, LiveBench-GEPA +0.6.

---------------------------------------------------------------------------------------------------------------------

## 5. Are form changes needed?

No form has to change to reach +9.5. Three targeted changes are worth their price, none needs a full re-run:
1. retry on parse failure in every arm (P3; failed rows only);
2. run_sql for the BIRD agents (P4; two forms, one dataset);
3. at TEST time only: the reviewer's draft and the program's own output stay two separate calls (as in the saved runs).

Not worth it now: demos for the agents; a merged-document form for HoVer; more program samples as extra voters (only
measurable in the three KM cells).

---------------------------------------------------------------------------------------------------------------------

## 6. Costs of the remaining steps

| step | USD | wall time |
|---|---|---|
| implement 1.0 as a selection mode over saved outputs; replay PARETO / FIT / DEV for all 39 cells | 0 | 25-40 min CPU (BIRD execution ~25 min, LCB public tests ~15 min) |
| P3 parse-failure repair | ~6 | 2-3 h |
| P4 BIRD run_sql re-run (2 forms x 3 optimizers) | ~3-4 | 1.5-2 h |
| P5 verifier replay (PARETO + FIT, then gated DEV) | ~7-10 | 3-5 h |
| sealed TEST once, forms only, if n_TEST ~ n_DEV: all 36 cells with 1.0-full | ~41 (auto-lite ~25; 1.0-lite ~21; the 13 GEPA cells alone ~12 with 1.0-full) | 1-2 days at the 48-worker ceiling |

---------------------------------------------------------------------------------------------------------------------

## 7. Proposed frozen specification: PeachTrees 1.0

Forms (unchanged): R = the optimizer's saved program; A = "assembled" (the program's draft, then the ReAct reviewer
with the task's tools); L = "liquid" (the ReAct agent with the task's tools). Universal instructions and inherited
guidance as in worker v86. Infrastructure: every LM call of every arm (the baselines included) is retried on an adapter
parse failure, at most 3 attempts; a row that still has no output scores 0.

Item rule pi1 (label-free):
1. drop forms without a parsable output;
2. if the task has a deterministic checker, drop forms whose output fails it; if all fail, keep all
   (LCB: the statement's public tests; BIRD: the query executes and returns at least one non-NULL row; NATURAL PLAN: the
   plan satisfies the stated constraints / reaches the largest number of valid meetings among the forms);
3. key(answer) = the task metric's canonical form of the answer (free-form outputs have no key); if at least two
   surviving forms have the same key, return that answer;
4. else return A's answer; if A is gone R's; then L's.

Task rule (decided once per task on S = PARETO + FIT + DEV, before TEST):
d = mean over S of [score(pi1) - score(R)], se = clustered standard error.
PeachTrees 1.0 = pi1 if d + 1.0 * se >= 0, else R (then no extra call is made at inference).

Cost switch (decided on S): if the vote of step 3 changes pi1's answer on fewer than 2 % of the items of S, L and the
separate R call are not run; the output is A's answer, R's if A is gone ("1.0-lite" is this branch for every task).

Optional module (only if P5 passes its gate on PARETO + FIT): the verifier of section 4 on contested items.

Reported: PeachTrees 1.0 and 1.0-lite minus the optimizer's program on the same items; the per-item cost multiple.
Nothing else is tuned per dataset. The four cells where the rule returns the program (BFCL x 2, IFBench and PUPA over
MIPROv2 on today's S) are reported as ties.

---------------------------------------------------------------------------------------------------------------------

## 8. Risks, and what the sealed TEST must validate

1. Post hoc design. The policy family was designed after DEV had been seen; PARETO <-> FIT cross-validation and LODO
   protect the choice inside the family, not the family. The TEST number is the only clean estimate; expect +8.5..+9.5,
   not +9.47, and state the primary metric in advance (unweighted mean over datasets of 1.0 minus the program, per
   optimizer; Holm per dataset; clustered bootstrap; worst cell).
2. "No regression" is statistical. With n = 100 selection items (se ~4.5 pp) a policy that is truly 5 pp worse passes
   the NI test with probability ~0.46, 10 pp worse ~0.11; with n = 300 (PARETO + FIT + DEV) ~0.18 and < 0.01. The claim
   is "no significant regression", and the small cells (BFCL n = 49, AIME / GPQA selection sets of 45) are the exposed
   ones.
3. Task-specific code. Canonical keys and checkers are per-task code (they reuse the scorers' normalisers and the
   tasks' tools). A reviewer may call the NATURAL PLAN validator hand-engineering: report with and without checkers
   (+9.47 / +9.16), and state that no gold field is read (unit check: 300 / 300 reference plans validate).
4. Parse failures (2.4) move single cells by up to 9 pp in either direction; P3 before TEST, identical retry policy
   for competitors.
5. Splits that are not i.i.d. with DEV / TEST: GPQA (main -> Diamond), AIME (30 problems x 5 repeats on DEV), IFBench
   (DEV from IFTrain). The NI rule tolerates optimism but not a sign flip; GPQA's selection-data advantage of the forms
   (+7..+9 pp) did not transfer for assembled alone.
6. Offline BIRD execution ran under a loaded host with a 30 s limit (192 of 3,600 queries not executed; 6-21 % of those
   were scored correct in the original runs): the final implementation must use the worker's own executor and limits.
7. The item rule needs the program's own output and the reviewer's draft as two independent calls; sharing one call
   (cheaper) removes the vote's only useful case and was measured to be worse (2.5).
8. The verifier (P5) and the BIRD tool (P4) are estimates, not measurements, until replayed; both enter 1.0 only
   through their PARETO / FIT gates.
9. Literature (unverified, not opened with orx paper): self-consistency voting, execution-based agreement for code
   and text-to-SQL selection, and routing / "keep-the-anchor" selectors are close prior ideas; the contribution to
   claim is the optimizer-agnostic, never-worse layer and its cost profile, not the vote itself.

---------------------------------------------------------------------------------------------------------------------

## 9. Per-cell table (DEV; 1.0 numbers post hoc)

reported = v0.2 + J6* with the FIT gate; 1.0-lite / 1.0-full = NI rule (margin 1.0 se, fitted on PARETO + FIT) with the
reviewer-only / full item rule; CI = 95 % clustered bootstrap of 1.0-full minus the program; retry-adj = 1.0-full after
imputing the program's parse-failure rows (2.4); PF = mean / se of pi1 minus the program on PARETO + FIT;
agreement = shares of DEV items with all three equal / two equal / none equal / a form without output (task-aware keys).

| cell | n P/F/DEV | rigid | liquid | asm | v0.2 default (judge gate) | reported | 1.0-lite | 1.0-full | 95 % CI | retry-adj | oracle | PF mean/se | agreement |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gepa:hotpotqa | 300/150/300 | 0.757 | 0.777 | 0.783 | assembled (on) | +3.3 | +2.7 | +4.0 | [+1.7, +6.7] | +4.0 | +7.3 | +4.4/1.2 | .79/.15/.06/.00 |
| gepa:hover | 300/150/300 | 0.707 | 0.577 | 0.773 | assembled (off) | +6.7 | +6.7 | +6.7 | [+2.7, +10.7] | +6.7 | +12.0 | +8.7/1.8 | .00/.00/1.0/.00 |
| gepa:ifbench | 300/300/300 | 0.900 | 0.869 | 0.922 | rigid (on) | +0.8 | +2.2 | +2.2 | [+0.3, +4.5] | +2.2 | +3.6 | +0.5/0.7 | .03/.02/.95/.00 |
| gepa:pupa | 111/111/221 | 0.970 | 0.972 | 0.987 | rigid (off) | +0.0 | +1.7 | +1.7 | [-0.0, +3.5] | +1.7 | +3.0 | +0.9/0.7 | .00/.01/.98/.00 |
| gepa:aime | 45/45/150 | 0.573 | 0.840 | 0.860 | assembled (on) | +31.3 | +28.7 | +30.0 | [+20.7, +40.7] | +29.6 | +38.0 | +26.7/4.7 | .49/.34/.14/.03 |
| gepa:gpqa | 45/45/118 | 0.814 | 0.814 | 0.822 | rigid (on) | +3.4 | +0.8 | +5.1 | [+0.0, +10.2] | +5.1 | +11.0 | +3.3/4.3 | .74/.23/.03/.00 |
| gepa:livebench | 121/121/126 | 0.613 | 0.765 | 0.727 | assembled (on) | +12.7 | +11.4 | +14.8 | [+8.0, +22.0] | +14.8 | +19.0 | +9.0/2.0 | .48/.31/.20/.01 |
| gepa:lcb | 80/80/100 | 0.540 | 0.690 | 0.710 | liquid (on) | +19.0 | +17.0 | +17.0 | [+9.0, +26.0] | +17.0 | +25.0 | +21.2/3.5 | .03/.11/.85/.01 |
| gepa:bfcl | 49/50/49 | 0.755 | 0.673 | 0.673 | rigid (off) | +0.0 | +0.0 | +0.0 (rigid) | - | +0.0 | +8.2 | -6.1/3.2 | .10/.18/.71/.00 |
| gepa:tau2 | 100/100/150 | 0.993 | 1.000 | 0.993 | rigid (off) | +0.0 | +0.0 | +0.0 | [-2.0, +2.0] | +0.0 | +0.7 | +0.0/0.0 | .00/.00/1.0/.00 |
| gepa:natplan | 50/50/200 | 0.720 | 0.890 | 0.875 | rigid (on) | +11.0 | +24.5 | +24.5 | [+18.5, +30.5] | +22.3 | +25.5 | +17.0/4.0 | .47/.24/.19/.09 |
| gepa:bird | 50/50/200 | 0.400 | 0.490 | 0.595 | rigid (off) | +0.0 | +20.5 | +18.5 | [+12.0, +24.5] | +18.5 | +30.0 | +4.0/4.2 | .45/.33/.07/.15 |
| gepa:toolhop | 50/50/200 | 0.465 | 0.550 | 0.540 | vote3 (off) | +10.5 | +11.0 | +13.0 | [+8.0, +18.5] | +9.8 | +20.0 | +11.0/3.5 | .39/.20/.30/.11 |
| mipro:aime | 45/45/150 | 0.653 | 0.773 | 0.807 | assembled (off) | +15.3 | +16.7 | +20.0 | [+12.7, +28.0] | +20.0 | +28.7 | +18.9/5.2 | .50/.25/.14/.11 |
| mipro:gpqa | 45/45/118 | 0.737 | 0.695 | 0.831 | vote3 (off) | +5.9 | +9.3 | +8.5 | [+2.5, +15.3] | +8.5 | +15.3 | +11.1/3.3 | .65/.25/.02/.08 |
| mipro:livebench | 121/121/126 | 0.576 | 0.739 | 0.755 | assembled (on) | +19.0 | +19.0 | +19.3 | [+12.9, +26.3] | +19.3 | +23.0 | +12.5/2.0 | .43/.29/.18/.10 |
| mipro:hotpotqa | 300/150/300 | 0.773 | 0.793 | 0.790 | rigid (off) | +0.0 | +1.7 | +3.0 | [+0.0, +6.0] | +3.0 | +8.3 | +2.0/1.0 | .79/.16/.05/.00 |
| mipro:lcb | 80/80/100 | 0.560 | 0.620 | 0.670 | liquid (on) | +12.0 | +17.0 | +17.0 | [+9.0, +26.0] | +9.4 | +21.0 | +14.4/3.4 | .04/.08/.48/.40 |
| mipro:natplan | 50/50/200 | 0.790 | 0.900 | 0.920 | liquid (off) | +11.0 | +18.0 | +18.0 | [+13.0, +23.5] | +18.0 | +18.5 | +18.0/3.9 | .51/.24/.26/.01 |
| mipro:bird | 50/50/200 | 0.475 | 0.445 | 0.510 | rigid (off) | +0.0 | +4.0 | +2.5 | [-3.0, +8.0] | +2.5 | +18.5 | +1.0/3.6 | .48/.32/.06/.14 |
| mipro:toolhop | 50/50/200 | 0.735 | 0.505 | 0.740 | rigid (off) | +0.0 | +0.5 | +0.5 | [-4.5, +5.0] | +0.5 | +9.0 | +6.0/3.4 | .49/.32/.15/.04 |
| mipro:ifbench | 300/300/300 | 0.907 | 0.874 | 0.895 | rigid (off) | +0.0 | +0.0 | +0.0 (rigid) | - | -0.3 | +5.8 | -2.3/1.0 | .01/.04/.95/.01 |
| mipro:hover | 300/150/300 | 0.713 | 0.280 | 0.750 | assembled (off) | +3.7 | +3.7 | +3.7 | [+0.0, +7.7] | +3.7 | +8.3 | +5.6/1.6 | .00/.00/1.0/.00 |
| mipro:pupa | 111/111/221 | 0.881 | 0.829 | 0.892 | rigid (off) | +0.0 | +0.0 | +0.0 (rigid) | - | +0.0 | +7.2 | -2.7/1.4 | .00/.03/.97/.00 |
| simba:aime | 45/45/150 | 0.620 | 0.707 | 0.733 | liquid (on) | +15.3 | +20.7 | +22.0 | [+14.0, +30.7] | +22.0 | +30.0 | +30.0/5.3 | .41/.26/.07/.26 |
| simba:gpqa | 45/45/118 | 0.763 | 0.763 | 0.771 | vote3 (off) | +3.4 | +0.8 | +5.1 | [+0.0, +10.2] | +5.1 | +11.0 | +5.6/3.7 | .71/.23/.02/.04 |
| simba:livebench | 121/121/126 | 0.612 | 0.704 | 0.716 | assembled (on) | +14.0 | +13.3 | +13.5 | [+7.9, +19.8] | +13.5 | +19.3 | +9.4/1.8 | .50/.19/.20/.11 |
| simba:hotpotqa | 300/150/300 | 0.743 | 0.780 | 0.800 | assembled (on) | +6.7 | +5.7 | +5.7 | [+3.3, +8.3] | +5.7 | +10.7 | +4.2/1.0 | .79/.17/.05/.00 |
| simba:lcb | 80/80/100 | 0.590 | 0.620 | 0.660 | assembled (on) | +18.0 | +18.0 | +18.0 | [+11.0, +26.0] | +8.4 | +22.0 | +17.5/3.1 | .00/.10/.49/.41 |
| simba:natplan | 50/50/200 | 0.775 | 0.930 | 0.940 | rigid (on) | +4.0 | +21.5 | +21.0 | [+15.5, +27.0] | +21.0 | +22.0 | +19.0/3.9 | .54/.17/.26/.03 |
| simba:bird | 50/50/200 | 0.420 | 0.420 | 0.455 | rigid (off) | +0.0 | +5.5 | +6.5 | [+1.5, +11.5] | +6.5 | +18.0 | +5.0/4.1 | .47/.35/.07/.10 |
| simba:toolhop | 50/50/200 | 0.730 | 0.490 | 0.770 | rigid (off) | +0.0 | +4.0 | +4.5 | [+0.5, +9.0] | +4.5 | +8.0 | +3.0/3.3 | .49/.33/.15/.03 |
| simba:ifbench | 300/300/300 | 0.887 | 0.868 | 0.908 | rigid (off) | +0.0 | +2.6 | +2.9 | [+0.3, +5.4] | +2.9 | +5.3 | +0.3/0.6 | .02/.04/.94/.01 |
| simba:hover | 300/150/300 | 0.693 | 0.633 | 0.793 | assembled (off) | +10.0 | +10.0 | +10.0 | [+6.0, +14.3] | +10.0 | +15.3 | +8.2/1.8 | .00/.00/1.0/.00 |
| simba:pupa | 111/111/221 | 0.970 | 0.871 | 0.987 | rigid (off) | +0.0 | +1.8 | +1.8 | [+0.4, +3.3] | +1.8 | +2.6 | +0.5/0.8 | .00/.04/.96/.00 |
| simba:bfcl | 49/50/49 | 0.796 | 0.714 | 0.755 | rigid (off) | +0.0 | +0.0 | +0.0 (rigid) | - | +0.0 | +4.1 | -3.0/2.2 | .10/.24/.65/.00 |
| gepa1:livebench | 121/121/126 | 0.658 | 0.767 | 0.753 | liquid (on) | +12.8 | +13.4 | +13.2 | [+7.5, +20.0] | +11.1 | +17.6 | +13.6/2.3 | .48/.27/.13/.12 |
| gepa1:ifbench | 300/300/300 | 0.861 | 0.816 | 0.866 | rigid (off) | +0.0 | +1.5 | +1.5 | [-1.4, +4.4] | +1.5 | +6.6 | +0.5/0.9 | .01/.02/.96/.01 |
| gepa1:hotpotqa | 300/150/300 | 0.780 | 0.763 | 0.787 | assembled (off) | +0.7 | +0.7 | +1.0 | [-1.0, +3.3] | +1.0 | +4.3 | +1.8/0.9 | .82/.15/.03/.00 |

| group | cells | reported | v0.2 lite | 1.0-lite | 1.0-full | 1.0-full retry-adj | oracle | worst cell |
|---|---|---|---|---|---|---|---|---|
| GEPA | 13 | +7.59 | +5.76 | +9.78 | +10.57 | +10.12 | +15.63 | 0 |
| MIPROv2 | 11 | +6.09 | +5.43 | +8.17 | +8.40 | +7.68 | +14.88 | 0 |
| SIMBA | 12 | +5.95 | +3.76 | +8.65 | +9.24 | +8.44 | +14.03 | 0 |
| all | 36 | +6.59 | +4.99 | +8.91 | +9.47 | +8.82 | +14.87 | 0 |
| GEPA seed 1 | 3 | +4.50 | +3.85 | +5.17 | +5.23 | +4.51 | +9.50 | +1.0 |

| dataset (mean over optimizers) | reported | 1.0-lite | 1.0-full | oracle |
|---|---|---|---|---|
| aime | +20.7 | +22.0 | +24.0 | +32.2 |
| bfcl (2) | +0.0 | +0.0 | +0.0 | +6.1 |
| bird | +0.0 | +10.0 | +9.2 | +22.2 |
| gpqa | +4.2 | +3.7 | +6.2 | +12.4 |
| hotpotqa | +3.3 | +3.3 | +4.2 | +8.8 |
| hover | +6.8 | +6.8 | +6.8 | +11.9 |
| ifbench | +0.3 | +1.6 | +1.7 | +4.9 |
| lcb | +16.3 | +17.3 | +17.3 | +22.7 |
| livebench | +15.3 | +14.6 | +15.8 | +20.4 |
| natplan | +8.7 | +21.3 | +21.2 | +22.0 |
| pupa | +0.0 | +1.1 | +1.1 | +4.3 |
| tau2 (1) | +0.0 | +0.0 | +0.0 | +0.7 |
| toolhop | +3.5 | +5.2 | +6.0 | +12.3 |

1.0-full is significantly above the program in 24 of 36 cells and below it in none. Against the reported v0.2 it is
significantly higher in 9 cells (NATURAL PLAN x 3, BIRD over GEPA and SIMBA, AIME over MIPROv2, ToolHop / IFBench / PUPA
over SIMBA) and lower by point estimate in 4 (AIME-GEPA -1.3, LCB-GEPA -2.0, LiveBench-SIMBA -0.5, HotpotQA-SIMBA -1.0;
none significant) - the cells where the J6* judge had helped; the verifier of section 4 targets exactly these.

---------------------------------------------------------------------------------------------------------------------

## 10. Replay scripts and outputs (next to this file)

Server: /tmp/fable_out/ ; local copy: the fable scratch folder. All scripts are read-only on the run directories.

| file | purpose |
|---|---|
| extract_cells.py -> cells.json | per-item scores, groups and judge decisions of the 39 cells |
| bird_exec.py -> bird_exec.json | offline read-only execution of the saved BIRD queries (never gold) |
| features.py -> feats.json | task-aware keys, liveness, draft-changed, NATURAL PLAN validity, LCB public-test evidence |
| fa_lib.py, fa_lib2.py, fa_lib3.py | loaders, policies (forms, vote, checkers), NI rule, clustered statistics |
| a1_baseline.py, a2_rules.py, a3_patterns.py | reproduction of the reported numbers; v0.2-family rule variants; agreement patterns |
| b1_semvote.py, b2_signals.py, b3_optimism.py, b4_crossfit.py | vote policies; checker precision; winner's-curse difference-in-differences; cross-fitting on DEV; judge precision / recall |
| b5_costs.py -> costs.json, b7_sc.py, b8_frontier.py | per-item costs; SC@k; the cost / gain frontier and the recorded-judge overlay |
| b6_rules_final.py [V] | the 60 rule variants: PARETO <-> FIT cross-validation, DEV replay, leave-one-dataset-out |
| c1_table.py [V] | the agreement table learned on PARETO + FIT |
| c2_judgecost.py, c4_judge_est.py, e1_judge_decomp.py | judge spend, replay cost on contested items, remaining judge potential, decomposition of the reported judge gain |
| c3_bird.py, c5_retryadj.py, c6_noinfra.py, c7_np_check.py | BIRD execution signals; parse-failure adjustment; clean-row gains; validator unit check |
| d1_tables.py -> d1_rows.json | the per-cell table of section 9 |
| logs/*.log (local), *.log (server) | the outputs quoted in this report |

