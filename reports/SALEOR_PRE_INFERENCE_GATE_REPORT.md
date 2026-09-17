# Saleor Pre-Inference Gate Report — Stage-2 ready-to-run

**Date:** 2026-09-16 evening; **UPDATED 2026-09-17** (identity correction +
re-authorization)
**Tier:** T3 data / ZERO scientific LLM calls
**Status:** `SALEOR DEVELOPMENT DATASET READY` (frame + split + 150/150 DEV
bundles + identity correction; a clean DEVELOPMENT sparse run is authorized
under the frozen 450-cell / 9M-token / $3.00 budget).

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

- ~~Case-bundle materialization + frozen split manifest for Saleor is the next
  audited data step~~ **RESOLVED 2026-09-17:** 150/150 DEVELOPMENT bundles
  materialized via the production-only materializer (98/98 equivalence PASS)
  and the identity/provenance correction (case IDs `saleor-rc-<sha>`,
  repository identity, 150/150 scientific-payload equivalence PASS). See
  `reports/SALEOR_PORTABILITY_FIX_AND_150_BUILD_REPORT.md` and
  `reports/SALEOR_IDENTITY_MIGRATION_REPORT.md`.

## Do NOT

- Do not inspect any future Saleor TEST model outcomes.
- Do not tune the djangoCMS method on Saleor TEST.
- Do NOT open Saleor INTERNAL_TEST (80) or RESERVE (1086).
- Saleor DEVELOPMENT sparse inference IS authorized (2026-09-17) under the
  frozen 450-cell / 9M-token / $3.00 budget; the pre-fix single smoke call is
  archived as operational smoke and NOT counted as scientific evidence.