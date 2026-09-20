# STAGE5_V2_FINAL - T3 Impact Declaration + Frozen Configuration (2026-09-20)

**Status:** FROZEN BEFORE UNSEALING. Records the complete Stage-5 confirmatory
protocol BEFORE any Stage-5 outcome is read. All config/artifact hashes are
frozen, committed, pushed, and tagged BEFORE the one-shot opening of the
defined confirmatory populations.

**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**Mission:** FINAL THESIS IMPACT-LOCALIZATION FREEZE + ONE-SHOT STAGE-5
CONFIRMATORY EVALUATION
**Tier:** T3 (one-shot untouched confirmatory evaluation of the single best
frozen DEVELOPMENT-selected candidate)
**Authorization:** provided by Ahmed in the mission prompt — ONE and ONLY ONE
opening of the Stage-5 confirmatory populations AFTER preregistration is
frozen/committed/pushed/tagged. Do NOT ask again unless the frozen
prerequisites fail.

---

## 0. Preserved frozen scientific history (NOT rewritten, NOT reinterpreted)

- `INDEPENDENT_DENSE_RETRIEVAL_REPLICATED` — preserved exactly.
- `CALIBRATED_SET_SELECTION_V1_FAIL` — preserved exactly (frozen negative).
- `PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL` — preserved exactly (frozen
  negative; DO NOT upgrade; pooled DEV post-hoc descriptive only).
- `ISSUE_GROUNDED_INTENT_SIGNAL_NOT_SUPPORTED` — preserved; may be CLARIFIED as
  "not supported under the frozen strict temporally-clean rule; the clean
  population was very small / underpowered." No rerun, no upgrade to PASS.
- ALL prior decisions P1–P83 preserved append-only.
- Stage 5 has been PAUSED/SEALED until this mission. The current best DEV
  candidate is NOT confirmed superior on both repos.

## 1. Current best DEVELOPMENT candidate (score-selection evidence only)

```
BEST_FROZEN_DEV_CANDIDATE_NOT_CONFIRMED_SUPERIOR_ON_BOTH_REPOS
Candidate: PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2
```
DEV point estimates (realization A):
- djangoCMS: Sparse F1 ≈ 0.3177; V1 ≈ 0.3341; V2 ≈ 0.3451; V2 Delta vs Sparse
  ≈ +0.0274 (per-repo paired CI crosses zero).
- Saleor: Sparse F1 ≈ 0.2605; V1 ≈ 0.3356; V2 ≈ 0.3476; V2 Delta vs Sparse
  ≈ +0.0871 (per-repo paired CI positive).
These DEV facts are SELECTION EVIDENCE, not confirmatory proof. The historical
`PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2_FAIL` verdict remains UNCHANGED.

## 2. Why method shopping stops

`NO_FURTHER_LOCALIZATION_METHOD_SHOPPING_FOR_CURRENT_THESIS` holds after this
mission regardless of PASS/FAIL/MIXED. Five days of method-search produced one
directionally-consistent DEV candidate; the thesis question is now "does the
single best frozen candidate survive ONE untouched evaluation", not "find
another DEV method". Future ideas go to Future Work / follow-up publications.

## 3. LocAgent-native metric-compatibility facts (integrity, NOT gating)

Integrated and audited from persisted DEV artifacts (reports/
LOCAGENT_NATIVE_METRIC_COMPATIBILITY_2026-09-20.md). These are POST-HOC
compatibility metrics. They MUST NOT change method selection, the Stage-5
endpoint, or the frozen V2 policy. Definitions (frozen):
- Acc@K_i = 1[ |TopK(R_i) ∩ G_i| == min(|G_i|, K) ]; Acc@K = mean over tasks.
- Hit@K = mean_i 1[ |TopK(R_i) ∩ G_i| >= 1 ].
- Recall@K = mean_i |TopK(R_i) ∩ G_i| / |G_i|.
Distinct from set-F1. No direct comparison to published LocAgent/SWE-bench
headline numbers as winner/loser.

Verified DEV table (V2 ranking = frozen V2 OOF-probability ranking over the
frozen V2 candidate universe; all 323 DEV tasks; realization A):
- Acc@1 ≈ 0.4737, Acc@3 ≈ 0.2508, Acc@5 ≈ 0.2663, Hit@5 ≈ 0.7492.
Single-target slice (|G|=1, n=80): V2 Acc@5 ≈ 0.600.
Historical P5-C LocAgent exposed 10-task run (dataset/reference only):
Acc@1 = 4/10, Acc@3 = 4/10, Acc@5 = 2/10; Hit@1/Hit@3/Hit@5 = 4/10.

## 4. Power-design interpretation (DESIGN JUSTIFICATION only)

- djangoCMS DEV n=174, delta F1 ≈ +0.0274, MDE@~80% power ≈ +0.053.
- Saleor DEV n=149, delta F1 ≈ +0.0871.
- Pooled repo-stratified DEV delta ≈ +0.0568 with positive descriptive CI
  (POST-HOC DESCRIPTIVE; does NOT rewrite V2_FAIL).
This motivates a repo-stratified pooled confirmatory endpoint instead of the
underpowered per-repo independent-CI rule.

## 5. Governance decision (to append to DECISIONS.md)

`P84 — APPROVED BY AHMED`:
"Stage 5 is a one-shot untouched evaluation of the best frozen
DEVELOPMENT-selected candidate, V2. The primary endpoint is ONE pre-registered
pooled, repository-stratified Delta-F1 vs Sparse. Per-repository point
estimates and confidence intervals are mandatory secondary analyses. The
historical DEV per-repository FAIL verdicts remain unchanged."
Also record `NO_FURTHER_METHOD_SHOPPING_BEFORE_FINAL_THESIS_DECISION`.

## 6. Population (frozen; NO extension)

`SALEOR_RESERVE_POWER_EXTENSION = NO`. Do NOT consume Saleor RESERVE extra
random 150 or any larger Saleor RESERVE pool. Stage-5 population is EXACTLY:
- djangoCMS RESERVE: n = 59
- Saleor INTERNAL_TEST: n = 80
- TOTAL: n = 139. No other confirmatory task.

## 7. Primary Qwen realization

`QWEN_REALIZATION = A` (chronologically primary throughout the development
program). Do NOT choose B based on result; do NOT average A+B. B remains prior
robustness evidence only.

## 8. Frozen final V2 policy (EXACTLY the frozen Memory-Rescue-V2)

Candidate universe (frozen):
1. Sparse files (ALL);
2. Qwen dense top-20 NON-SPARSE files;
3. parent-only structural memory top-10;
4. parent-only episodic memory top-10.

Features EXACTLY 11 (frozen V2):
1. dense_file_score   2. log_rank   3. gap_to_top1   4. in_sparse
5. log_sparse_set_size   6. sparse_empty   7. sparse_rank_interaction
8. cochange_sparse   9. cochange_top1   10. log_history_change_count
11. episode_similarity.
No new feature, no deletion, no graph feature, no class weighting, no issue
text, no adaptive K.

## 9. Final model refit — DEV ONLY (before opening Stage 5)

Fit ONE final deployment V2 model using ALL 323 DEVELOPMENT tasks:
- L2 LogisticRegression, C=1.0, solver=liblinear, max_iter=1000,
  random_state=0.
- StandardScaler on the frozen continuous features, fit on training rows only
  (here: all 323 DEV rows).
- Threshold selection: SAME deterministic 5-fold task-grouped OOF procedure
  over all 323 DEV tasks; grid 0.01..0.99 step 0.01; criterion argmax pooled
  micro-F1; tie-break HIGHER threshold.
- No Stage-5 label may influence scaler/coefficients/threshold/candidates/
  memory/config.

## 10. Frozen deployment artifacts (BEFORE unsealing)

reports/stage5_final_preregistration.json shall contain: feature schema, model
coefficients, intercept, scaler parameters, threshold, fold assignments for
threshold selection, Qwen model/provider/config, Repository Memory config,
candidate-generator constants, code commit SHA, Python/package versions, all
artifact hashes. Human-readable copy:
reports/STAGE5_FINAL_PREREGISTRATION_2026-09-20.md.

## 11. Pre-unsealing validation (BEFORE reading any Stage-5 outcome)

Run: targeted unit tests; leakage tests; feature-schema tests; final-model
serialization/reload test; threshold reproducibility test; candidate-generator
determinism; Sparse baseline determinism; Qwen config/provider check;
parent-only history guard; ruff; py_compile; git diff --check. Independent
audit recomputes the final DEV refit configuration WITHOUT importing the
primary analyzer.

## 12. Pre-registration commit + tag (MANDATORY, BEFORE unsealing)

Commit the complete preregistration; push; verify HEAD == origin/main and
clean tree. Create + push immutable tag `stage5-v2-final-preregistered-2026-09-20`.
Record commit SHA, tag SHA, timestamp, config SHA256. ONLY after this tag
exists remotely may Stage 5 be opened.

## 13. Irreversible checkpoint

Print `STAGE5_IRREVERSIBLE_CHECKPOINT_REACHED`, record preregistration
commit/tag, exact population, model hash, threshold, primary endpoint, API
budget. Ahmed's authorization is the mission prompt; do NOT ask again unless
frozen prerequisites fail.

## 14. Stage-5 input / history semantics

EXACT frozen parent-only Repository Memory semantics (V2). No target diff, no
changed-path labels, no future commit relative to the task parent, no
issue-grounded experimental text, no target-aware feature. If the frozen V2
implementation cannot be applied exactly: STOP; do NOT create a substitute.

## 15. Paid execution budget

Only the already-frozen Qwen model/provider required by V2. Verify live price
before the first paid call. Estimate total Stage-5 inference cost. Hard
incremental ceiling: **$1.00**. If projected > $1.00: STOP before paid calls
and report. No fallback provider, no model substitution, no extra realization.

## 16. Execute Stage 5 ONCE

Run EXACTLY once on the 59 + 80 populations. Fail closed. Individual
prediction failures recorded per the frozen pipeline; no manual repair; no
rerun with a different configuration. Technical resume after interruption only
if config is byte-identical, no design change, cached outputs unchanged.

## 17. Primary confirmatory endpoint (EXACTLY ONE)

`repo-stratified pooled micro-F1 difference` V2 minus Sparse. Per bootstrap
replicate b: sample 59 djangoCMS tasks with replacement from the 59; sample 80
Saleor with replacement from the 80; aggregate TP/FP/FN across BOTH sampled
strata for V2 then Sparse; compute F1_V2b and F1_Sparseb; DeltaF1_b =
F1_V2b - F1_Sparseb. Use 10,000 resamples, seed 20260920. 95% CI =
[Q2.5%(DeltaF1), Q97.5%(DeltaF1)].

## 18. Primary success rule (frozen; do NOT change after unsealing)

CONFIRMATORY SUCCESS requires BOTH:
- A: pooled stratified Delta F1 point > 0 AND 95% CI lower bound > 0.
- B: direction consistency: djangoCMS Stage-5 point Delta F1 > 0 AND Saleor
  Stage-5 point Delta F1 > 0.
Per-repo CIs are NOT gating (mandatory secondary). This replaces the
underpowered historical per-repo independent-CI rule while preventing one repo
from hiding an actual negative effect.

## 19. Secondary metrics (per repo + pooled descriptive)

TP/FP/FN; P = TP/(TP+FP); R = TP/(TP+FN); FNR = FN/(TP+FN); F1 = 2TP/(2TP+FP+FN).
Point estimates, V2-minus-Sparse delta, task-paired CI. Set-size stats: mean,
median, empty rate, additions, drops.

## 20. Acc@K compatibility (descriptive, NOT gating)

Report Acc@1/3/5, Hit@1/3/5, Recall@1/3/5 for the frozen V2 Stage-5 ranking
using the exact audited definitions. Do NOT make them gate criteria. Do NOT
compare Stage-5 percentages directly to external SWE-bench headlines.

## 21. Efficiency

Report Qwen input tokens, calls, API cost, index/build wall time, per-task
ranking time, memory retrieval time, final-policy inference time, total wall
time, peak RAM where practical, disk artifacts. Separate one-time/cold cost
from cached per-change inference cost.

## 22. Result labels (frozen)

- A+B pass: `STAGE5_V2_FINAL_CONFIRMATION_PASS` +
  `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`. Do NOT claim
  "individually statistically superior on djangoCMS" unless its own CI shows it.
- Pooled CI not excluding zero: `STAGE5_V2_FINAL_CONFIRMATION_FAIL` +
  `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`.
- Pooled passes but either repo point Delta F1 <= 0:
  `STAGE5_V2_FINAL_CONFIRMATION_MIXED` + `IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`.
No redesign.

## 23. NO second chance

After the outcome is visible: no threshold/feature/model changes, no A->B
switch, no Saleor RESERVE addition, no bootstrap/endpoint change, no V3, no
retest of Stage-5 tasks. One look only.

## 24. Future-work freeze

Retain as FUTURE WORK (NOT executed here): Energy-Based Change-Set Completion;
adaptive-k candidate/motif retrieval; negative association rules; JEPA /
Repository World Model; temporal hypergraph / commit-set prediction;
provenance-by-construction; richer archival issue reconstruction; matched
Loc-Bench evaluation; additional embedding/model families; broader
cross-language/polyglot expansion.

## 25. Post-mission

PASS -> current false-negative/Sparse-recovery research question CLOSED; prepare
a NEXT-PHASE handoff (`EXTERNAL_VALIDITY_AND_END_TO_END_REGENERATION`, NOT run
now). FAIL/MIXED -> method-search phase still CLOSED; thesis reports Sparse,
dense recovery, V1, V2, untouched confirmation outcome, limitations;
`THESIS_AND_PAPER_EVIDENCE_CLOSURE`.

## 26. Governance updates

00_CURRENT_RESEARCH_STATE.md, PROGRESS.md, DECISIONS.md,
docs/RESEARCH_JOURNEY.md, numbers cheatsheet, human-readable status,
Oracle-gap report, roadmap. Preserve all historical results.

## 27. Validation / independent audit

Independent audit MUST NOT import the primary Stage-5 analyzer; recompute:
task counts, Sparse TP/FP/FN, V2 TP/FP/FN, per-repo P/R/F1/FNR, pooled
stratified Delta F1, 10,000-resample CI, direction-consistency, Acc@K/Hit@K/
Recall@K, final PASS/FAIL/MIXED. Run targeted pytest, leakage tests,
preregistration-hash verification, ruff, py_compile, git diff --check.

## 28. Evidence tag + export

After final results + independent audit: commit, push, create ONE evidence tag
`stage5-v2-final-evaluation-2026-09-20`, record peeled commit SHA, verify
HEAD == origin/main and clean tree. TRUE LIGHT export <= 50 MB (exclude .git,
external repos, model caches, venvs, uv caches, giant temp files).

## 29. Expected artifacts

- docs/STAGE5_V2_FINAL_IMPACT_DECLARATION_2026-09-20.md (THIS FILE)
- reports/LOCAGENT_NATIVE_METRIC_COMPATIBILITY_2026-09-20.md + audit
- reports/STAGE5_DESIGN_POWER_CHECK_2026-09-20.md
- reports/THESIS_METHOD_FREEZE_READINESS_2026-09-20.md
- reports/STAGE5_FINAL_PREREGISTRATION_2026-09-20.md + .json
- reports/STAGE5_V2_FINAL_CONFIRMATORY_REPORT_2026-09-20.md (final)
- research/stage5-v2-final/* artifacts
- src/benchmark/issue_grounded-independent scripts/tests (audit must not import
  the primary analyzer)