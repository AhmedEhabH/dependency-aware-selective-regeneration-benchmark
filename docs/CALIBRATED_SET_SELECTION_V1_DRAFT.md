# CALIBRATED_SET_SELECTION_V1 — DRAFT (NOT EXECUTED)

**Status:** DRAFT ONLY. Prepared 2026-09-19 by the Qwen3 two-realization
replication mission. **NOT authorized, NOT executed, no API budget.**
**Gate to justify:** this draft becomes a frozen mission ONLY IF Qwen A and B
both replicate the dense signal (which they DID —
`INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`). This draft is the next
DEVELOPMENT-only mission proposal; it requires its own explicit authorization
+ freeze + budget before any execution.

---

## 1. Purpose

A fixed addition budget (B=5) with a decaying rank-conditional candidate
precision creates an increasing FP tail (documented in the two-realization
report §8). The dense ranking signal is useful (rank-1 omitted positives at
24–26% of tasks) but the ACCEPTANCE rule should be **calibrated**, not a fixed
cardinality. CALIBRATED_SET_SELECTION_V1 replaces the fixed-budget ADD with a
thresholded, calibrated ADD **and** DROP policy learned on DEVELOPMENT.

## 2. Scope discipline (frozen in the draft)

- **DEVELOPMENT only** (djangoCMS DEV 174 + Saleor DEV 149). No sealed data.
- **Minimal interpretable feature set FIRST** (no feature shopping):
  1. dense file score (Qwen/SweRank file-level MAX-cosine score);
  2. dense rank (1..N among the task universe);
  3. gap to top-ranked score (score_rank1 − score_file);
  4. in_sparse (boolean: file already in the Sparse write set);
  5. |Sparse| (write-set cardinality of the task).
- **ONE model family:** L2 logistic regression (penalized LR, no kernels, no
  trees, no ensembles, no neural).
- **NOT initially added** (only a later separately frozen ablation may justify
  them): graph features, co-change, BM25, historical frequency, multiple
  classifiers, multiple calibration algorithms.
- The future study must **score Sparse + omitted files together** and permit
  both ADD and DROP decisions.
- **No "minimum one file per task" constraint** unless separately justified —
  it is NOT implied by the F1-threshold theorem (Lipton et al. 2014; see the
  literature note in the two-realization report §9).

## 3. Proposed protocol shape (for the future mission)

1. Build the DEV training matrix from the persisted label-free full-file-score
   artifacts (this mission persisted them precisely so NO extra embedding run
   is needed) joined with the evaluation-only labels.
2. **Grouped task-level out-of-fold probabilities:** assign tasks to groups
   (e.g., 5 seeded task folds); for each fold, fit L2 LR on the other folds'
   task-groups and predict out-of-fold P(positive) for every file in the held
   group. Keep file scores within a task group together (task-grouped CV).
3. **Evaluate calibration** of the OOF probabilities (e.g., reliability /
   expected calibration error; bin checks), on DEV only.
4. **Derive the F1 threshold ONLY inside training folds** (Lipton t = F1*/2 or
   an equivalent within-fold derivation), never on the held-out fold.
5. **Apply** the frozen threshold to held-out folds; construct the final file
   set = {f : P̂(f) ≥ t} ∪ Sparse − dropped; permit ADD and DROP.
6. **Freeze ONE final policy** (features + model + calibration + threshold +
   decision rule) BEFORE any Stage-5 confirmatory execution.

## 4. Metrics / evaluation (same definitions as the frozen protocol)

TP/FP/FN, P/R/FNR/F1, candidate precision, macro ORR; task-paired bootstrap
CIs; the primary operating decision is file-level F1 with the ORR mechanism
diagnostic. Compare against Sparse, Route-B, SweRank, Qwen A/B at matched
population (DEV), then a fresh confirmatory protocol (separate authorization).

## 5. Budget (informational; NOT frozen)

No API calls needed for feature construction (all from the persisted score
artifacts). LR + calibration + CV are local and free. A future mission may
spend $0 on inference; any spent run (e.g., an LLM threshold/acceptance
component) would need its own frozen budget. ZERO API assumed by default.

## 6. Dependencies

- `research/contamination-bridge/qwen_embed/realization_{A,B}/full_file_scores.parquet`
  (label-free scores; this mission's engineering artifact).
- `research/strong-localization-signal/swerank/task_rankings.json` (SweRank
  rankings) if the policy should compare both dense families.
- `load_dev_tasks()` labels (evaluation join only, after feature freeze).
- sklearn (L2 LR; calibration utilities).

## 7. Gates (to be frozen by the future mission before execution)

Proposed (NOT frozen): (a) calibrated OOF probabilities pass a calibration
check on DEV; (b) final-set F1 on DEV ≥ best fixed-budget comparator at matched
inspection budget; (c) FP tail materially reduced vs fixed B=5; (d) no sealed
data; (e) no leakage (features parent-visible; labels joined after freeze);
(f) budget respected.

## 8. NOT executed here

This document is a DRAFT. No model was fit, no threshold derived, no OOF fold
computed, no API call made. The two-realization mission stops at drafting this
policy.