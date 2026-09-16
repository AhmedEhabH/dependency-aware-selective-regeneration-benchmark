# Saleor Pre-Inference Gate Report — Stage-2 ready-to-run

**Date:** 2026-09-16 evening
**Tier:** T3 data / ZERO scientific LLM calls
**Status:** `SALEOR READY-TO-RUN` (frame + split proposed; case-bundle build is
the next audited data step before any inference).

---

## Gate status (frozen rules; ZERO API until split audited)

| Gate | Requirement | Status |
|---|---|---|
| 1 Dataset validation | Saleor split counts; INTERNAL_TEST/RESERVE untouched | PASS (split proposed, seed 20260916; TEST/RESERVE never inferred) |
| 2 Input validation | parent-only inputs; intent-path-leakage off | PASS (frozen M4A rules; adapter only changes PRODUCTION_ROOTS) |
| 3 Smoke | 1 synthetic case | READY (frozen builder; not run here — requires case bundle) |
| 4 Dry run | manifest shape | READY (frame + split JSON produced) |
| 5 Integration | 30-case manifest + run-records schema | READY (build step pending) |
| 6 Metric verification | synthetic TP/FP/FN | PASS (frozen metric machinery) |

Permanent constraints: V2 djangoCMS INTERNAL_TEST/RESERVE untouched; no Saleor
TEST inspection; no model inference tonight; repetitions nested; raw responses
+ hashes persisted; API ceilings fail-closed; no replacement reruns.

## Readiness evidence

- **History:** full Saleor history cached (22,615 commits, non-shallow).
- **Frame:** 6000 → 2409 → 1352 → **1316** independent eligible
  (`research/transparency/saleor_sampling_frame_reconstructed.json`).
- **Split proposal:** DEV_TRAIN 120 / DEV_VALIDATION 30 / INTERNAL_TEST 80 /
  RESERVE 1086; all-pool SHA-256 `6be5c994…`
  (`research/transparency/saleor_split_proposal.json`).
- **Sample size:** `reports/SALEOR_SAMPLE_SIZE_ANALYSIS.md`.
- **Suitability:** `reports/SALEOR_REPOSITORY_SUITABILITY_AUDIT.md`
  (SUITABLE-WITH-DEVIATIONS → now effectively SUITABLE for a quantitative
  Stage-2 given the 1316 pool).
- **Sparse inference config:** identical to the registered djangoCMS study
  (qwen3-coder @ deepinfra/turbo, temp 0, cap 16384, Graph OFF, Sparse-v2,
  3 reps/task) per `docs/SALEOR_REAL_COMMIT_PROTOCOL_V1.md`.

## Blocker

- Case-bundle materialization + frozen split manifest for Saleor is the next
  audited data step (mirrors the djangoCMS V2 builder). It is NOT a scientific
  model call; do NOT run Saleor inference until it is complete and audited.

## Do NOT

- Do not inspect any future Saleor TEST model outcomes.
- Do not tune the djangoCMS method on Saleor TEST.
- Do not run Saleor LLM inference tonight.