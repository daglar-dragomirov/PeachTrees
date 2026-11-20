# PeachTrees: deep analysis before submission (2026-11-10)

Two independent reviews (a methodologist/reviewer audit and a verified related-work search, both Opus 5.5 xhigh) plus our
own DEV numbers. Decision-ready summary.

## Findings from our own data (DEV, 9 datasets, vs GEPA)
- Full PeachTrees +8.6 pp mean (median +3.4), worst dataset 0. PeachTrees-lite (task-level default form only, no judge):
  +7.2 pp = 83 % of the gain at 1-6x the GEPA program's cost (full: 1-22x; IFBench 17.6x for +0.8 pp).
- "Always assembled" averages +7.0 pp but regresses on BFCL (-8.2 pp); "always liquid" +3.9 pp, -13 pp on HoVer. The value
  of the selection rule is NO REGRESSION, not the mean.
- Oracle of forms +14.9 pp: the task-level choice closes ~54 % of the gap, the judge 23-28 % of the rest; the judge never
  hurt on DEV.

## Integrity issues to fix or disclose
- TEST was opened once for v0.2 (HotpotQA, HoVer, IFBench, PUPA); AIME and LiveBench have no TEST (DEV was looked at by
  several versions) -> a pre-registered fresh TEST (TEST2 from unused pools; sealed GPQA / LCB / tau2; AIME 2026 as new
  TEST) and disclosure.
- AIME DEV = 30 problems x 5 repeats: bootstrap must cluster by problem (CIs ~1.8x too narrow now); the judge's +.027 on
  AIME may become n.s.
- IFBench DEV comes from IFTrain (GEPA .900 DEV vs .648 TEST).
- Disclose: BFCL judge leak (withdrawn, repaired), providers per dataset, 429 re-evaluation counts (+ sensitivity).

## Most dangerous reviewer objections (and the cheapest neutraliser)
1. "It's just more compute / tools": compute-matched baselines (SC@k of the GEPA program; same judge over 3 rigid samples;
   liquid-SC@3) on AIME, LCB, LiveBench, GPQA, HotpotQA (~$7 DEV).
2. Tuning on DEV / TEST hygiene: freeze config hash, pre-registration, one fresh TEST (~$25-35).
3. Weak baselines: failure audit per variant (empty / parse / truncation), no-program baseline, optimizer budget table,
   GPQA-MIPROv2 rerun or exclusion.
4. Novelty (risk MEDIUM): closest Adaptive-GEPA (2609.38762, router + program library co-evolved inside GEPA),
   Select-then-Solve (2604.06753, paradigm routing; oracle +17.1 pp), COMED / Signed Rescue Routing / Workflow Portfolios
   (asymmetric keep-the-anchor, selector theory). Contribution = optimizer-agnostic post-hoc protocol with no regression.
5. Statistics: one pre-specified primary metric (unweighted mean PeachTrees - GEPA on TEST), Holm per dataset, clustered
   bootstrap, MDE for small n, 2nd seed on 2-3 datasets.

## MUST / SHOULD / SKIP
MUST (~$75-85): finish main table (tau2 judge, PUPA GMp2, LCB MIPROv2); free analyses (always-X, vote3, oracle, rescue-harm
decomposition, gap-to-oracle shares, rule variants, sensitivity, clustered bootstrap, cost table, leak/failure audit,
winner's-curse val->test check); compute-matched baselines; PeachTrees over MIPROv2 and SIMBA on AIME, GPQA, LiveBench,
HotpotQA; 2nd seed (existing seed-1 programs: HotpotQA, LiveBench, IFBench); pre-registered TEST once.
SHOULD (~$40-55): over MIPROv2 also on HoVer, LCB, IFBench; kNN/embedding router baseline (free from logs); PeachTrees over
the unoptimized seed program; other backbone (user decides; stronger of GPT-6 Luna / Claude Haiku 5.5); 1-2 untouched
datasets (MuSiQue or 2Wiki reusing the BM25 index; HMMT Feb 2026); SIMBA LCB only if < $8 / 24 h.
SKIP: competitors on tau2 (~$12 per optimization), PeachTrees over GEPA+Merge, paid two-form judge ablations (at most one
on AIME+LCB), TEST of PeachTrees on BFCL / PUPA (= GEPA by construction), Adaptive-GEPA reimplementation (discuss only).

## Framing
Headline: PeachTrees-lite (task-level form selection, no regression) + PeachTrees+J (max accuracy), both pre-registered.
Position: "after prompt optimization the dominant remaining lever is which FORM executes the program; an optimizer-agnostic,
conservative post-hoc layer". Do not claim novelty of the per-item judge; say "no significant regression on N benchmarks".
Candidate titles: "Optimize, Then Choose the Form: A Never-Worse Inference Layer over Prompt Optimizers"; "Beyond the
Compiled Prompt: Form Selection as the Missing Step after Prompt Optimization".

