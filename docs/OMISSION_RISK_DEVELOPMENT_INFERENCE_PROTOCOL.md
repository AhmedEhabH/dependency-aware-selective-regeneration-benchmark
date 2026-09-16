# DEVELOPMENT-INFERENCE PROTOCOL — Omission-Risk Feature Study V1 (TRAIN/VALIDATION Sparse-v2)

**Status:** EXECUTED 2026-09-16 (approved 90-cell run COMPLETE, 90/90 valid,
490,747 tokens / $0.184 within the frozen 600,000-token AND $0.30 hard-stop;
labels computed; registered Sparse-v2-label feature analysis rerun; report
`reports/OMISSION_RISK_SPARSE_V2_INFERENCE_REPORT.md`).
**Date:** 2026-09-16
**Amendment basis:** Phase-B mandatory preflight (A–G) confirmed TRAIN/VALIDATION
Sparse-v2 predictions are UNAVAILABLE. Per the amendment, the registered
Sparse-v2-label feature analysis is **DEFERRED**; this protocol defines the
frozen development-inference run that would produce those labels, with an
explicit budget. No call happens without approval.

---

## 1. Why this is needed (Gate A decision)

| Split | Sparse-v2 predictions | Full-v2 predictions | reps | label usable |
|---|---|---|---|---|
| TRAIN (24) | NO | NO | 0 | NO |
| VALIDATION (6) | NO | NO | 0 | NO |
| HELD_OUT_TEST (10) | YES (P1) | YES (P1) | 3 | YES but PERMANENTLY EXPOSED — never used for feature/threshold decisions |

The registered primary label `has_fn(t) = 1 iff Sparse-v2 prediction misses
>= 1 proxy-positive file` cannot be computed on TRAIN/VALIDATION from existing
evidence. The exposed HELD_OUT_TEST Sparse-v2 outputs are NOT a substitute
(amendment A). Therefore the registered scientific feature analysis is
deferred until a development-inference run produces Sparse-v2 predictions on
TRAIN/VALIDATION under this frozen protocol.

## 2. What the deterministic work already covers (preserved, not discarded)

The zero-LLM development analysis (metadata-corpus BM25@K first pass, feature
extraction, routing metrics, adaptive-K, cost sensitivity) has been computed,
gated (six gates PASS) and audited. It is **development evidence for the
deterministic first-pass variant ONLY**. It is NOT the registered Sparse-v2
omission-risk analysis and must not be reported as such. Results are
interpreted strictly as descriptive development evidence with wide
uncertainty (n=30).

## 3. Frozen inference configuration

| Field | Value |
|---|---|
| Split(s) | TRAIN (24) + VALIDATION (6) — HELD_OUT_TEST NEVER in this run |
| Arm | sparse_v2 ONLY (plan actions carry VALIDATE/HUMAN_REVIEW/action-entropy features) |
| Model | qwen/qwen3-coder (Qwen3-Coder-480B-A35B-Instruct) |
| Provider | deepinfra/turbo (OpenRouter), same frozen P1 pricing snapshot |
| Temperature | 0.0 |
| Completion cap | 16384 (P1 frozen) |
| Graph | OFF (P1 frozen) |
| Repetitions | 3 (nested observations per task; label aggregation pre-registered as any-FN-over-reps with task-level unit) |
| Protocol version | real-commit-p1-v1.0.0 (same prompt contract; serialization policy = SPARSE) |
| Seed | none needed (temp 0) |

## 4. Expected cost (from frozen P1 sparse evidence)

P1 sparse cells (30 cells): mean prompt 4,930 tokens, mean completion 599
tokens, total 165,885 tokens, total $0.0623.

| Plan | Cells | Expected tokens | Expected cost (frozen pricing) | Notes |
|---|---|---|---|---|
| 3 reps x 30 tasks (recommended) | 90 | ~497,600 | ~$0.19 | matches P1 nested design; task-level bootstrap over 30 tasks |
| 1 rep x 30 tasks (budget-min) | 30 | ~165,900 | ~$0.06 | no repetition averaging; smaller n per task |
| 2 reps x 30 tasks | 60 | ~331,700 | ~$0.12 | intermediate |

Budget ceiling (frozen): 600,000 tokens / $0.30. Any overrun stops the run.

## 5. Gates for the inference run (frozen before approval)

1. Dataset validation: TRAIN 24 / VALIDATION 6 only; HELD_OUT_TEST access fails closed.
2. Prompt/input validation: P1 prompt contract byte-checks; policy block = SPARSE.
3. Pipeline smoke: 1 synthetic case end-to-end (mock backend).
4. Dry run: 2-case slice, 0 model calls, row-shape contract.
5. Integration: 30-case manifest + run_records schema + persisted raw+sha256.
6. Metric verification: synthetic TP/FP/FN P/R/F1/FNR.
Plus: leakage audit (proxy never in prompt), determinism, task-level statistical
unit, and the Phase-B preflight gates (A–G) re-run on the new evidence.

## 6. Outputs of the inference run (then the feature study continues)

- research/omission-risk-feature-study-v1/sparse_v2_trainval_run_records.jsonl
  (+ raw responses + sha256 sidecars)
- Recompute task-level has_fn labels from Sparse-v2 predictions (any-FN rule,
  task unit, pre-registered).
- Re-run single-feature / baselines / combination / adaptive-K / cost analysis
  with the registered Sparse-v2 label; deterministic features unchanged.
- Update this protocol status and the living review.

## 7. Decision requested from Ahmed

1. Approve the recommended 90-cell Sparse-v2 development-inference run
   (TRAIN/VALIDATION, ~$0.19 ceiling) — OR a 30-cell budget-min variant;
2. OR reject new LLM calls and accept the deterministic first-pass development
   analysis as the delivered evidence for this block (with the registered
   Sparse-v2-label study deferred to a later milestone).

No scientific LLM/API call will be made without this decision.

---

**Approve / reject and which variant (90 / 60 / 30 cells):** **APPROVED 2026-09-16 —
90-cell Sparse-v2 development-inference run EXECUTED** (30 tasks × 3 reps;
results in `research/omission-risk-feature-study-v1/sparse_v2_trainval_run_records.jsonl`;
analysis in `research/omission-risk-feature-study-v1/sparse_v2_label_analysis/`;
report `reports/OMISSION_RISK_SPARSE_V2_INFERENCE_REPORT.md`; audit
`reports/OMISSION_RISK_INFERENCE_AUDIT.md`).
