# RealCommitImpactDataset-v2 Protocol

**Date:** 2026-09-16
**Tier:** T3 (scientific-design; ZERO model calls until a split is frozen)
**Owner:** Ahmed Ehab (MSc)
**Status:** PROTOCOL FROZEN (2026-09-16). Split manifest freeze requires the
frozen sampling frame (reconstructed; see
`reports/REAL_COMMIT_V2_SAMPLING_FRAME_AUDIT.md`) and is proposed here.
**Precedence:** this protocol supersedes the v1-only planning in
`docs/POST_ICCI_NEXT_EXPERIMENTS_DRAFT.md` for the V2 dataset question.

---

## 1. Purpose

The v1 omission-risk development evidence is **negative for a task-level
RiskScorer** (n=30; 4 negatives; no reliable feature above the random band).
The next scientific step is to **enlarge development evidence** and to
**protect an untouched internal confirmatory set** that v1 can no longer
provide (all 40 v1 cases are `LEGACY_EXPOSED_V1`).

RealCommitImpactDataset-v2 therefore provides:

- a **larger V2 development set** (DEV_TRAIN + DEV_VALIDATION) from eligible
  djangoCMS cases that were never part of v1;
- an **untouched internal test** set (never-inferred, never-used) for the final
  confirmatory correctness–cost comparison;
- a **reserve** set for future/confirmatory use.

## 2. Population definition (frozen)

- Repository: djangoCMS (`https://github.com/django-cms/django-cms`).
- Anchor: `0f633fc9fa213357f4202482aab2b0edad680f95` (tag `5.0.0`).
- Window: newest **6000** ancestors of the anchor (modern PR-era history).
- Eligibility: the **identical frozen v1 M4A-2 rules** (no loosening):
  single-parent only; meaningful intent; production Python source change only
  (`cms/**`, `menus/**`, excluding tests/test_utils/migrations/`__pycache__`);
  proxy ≤ 12; total diff ≤ 40; `allow_intent_path_leakage=False`;
  whitespace-only excluded; `MINER_DEV` targets excluded
  (`miner_dev_target`). See `reports/REAL_COMMIT_M4A2_PROTOCOL.md` §3–§4.
- Dedup: the frozen R1/R2/R3 related-change rules
  (`reports/REAL_COMMIT_M4A2_PROTOCOL.md` §5).
- Reconstructed frame (2026-09-16, deterministic, zero API):
  **6000 scanned → 916 eligible → 334 after R1/R2 → 329 independent eligible →
  40 selected for v1** → **289 untouched eligible cases remain** for V2.

## 3. V2 architecture

```text
V2 DEVELOPMENT
    ├─ DEV_TRAIN
    └─ DEV_VALIDATION

UNTOUCHED INTERNAL TEST
RESERVE / FUTURE
```

Rules:

- **Untouched internal test** uses ONLY never-inferred cases **outside the
  exposed v1 40**.
- **Reserve** uses never-inferred cases outside the exposed v1 40.
- **Development may reuse the old v1 TRAIN/VALIDATION 30** as
  compatibility/development cases (their Sparse-v2 labels already exist).
- **Old v1 HELD_OUT_TEST (10)** stay exposed/reporting-only and must NOT become
  v2 test.
- Split is frozen **before any new V2 model result**; metadata-only
  stratification; deterministic seed; frozen hashes.
- No stratification on future model results.

## 4. Metadata strata (proposed, frozen rules)

Available metadata strata (from the reconstructed frame and case manifests):

- year/time of the target commit;
- proxy-size bucket (small ≤2 / medium 3–6 / large 7–12, the frozen v1
  `_shape_bucket` boundaries);
- candidate-universe size (available for built cases; computed at build time);
- conservative public-intent category (`change_type`): bugfix / feature /
  chore / docs / build / refactor / test / unknown.

Stratification is metadata-only and deterministic.

## 5. Sample-size basis (see reports/REAL_COMMIT_V2_SAMPLE_SIZE_ANALYSIS.md)

Observed development negative prevalence: 13.3% (4/30). Sensitivity analyzed
over 5%–25%. Key conclusions:

- At 13.3%, **N=120 new V2 development tasks (360 cells)** yields ~16 expected
  negatives, P(neg ≥ 10) high, within all ceilings
  (360 ≤ 450 cells; ~1.96M ≤ 2.5M tokens; ~$0.74 ≤ $1.00).
- N=150 (450 cells, ~2.45M tokens, ~$0.92) is the ceiling-limited maximum.
- Under 10% prevalence, N=150 gives ~15 negatives; under 5% no N ≤ 450 is
  sufficient for ≥ 20 negatives.
- **N is chosen from the frame, never because it is round.**

## 6. V2-LARGE vs V2-CENSUS

- **V2-LARGE (preferred default):** a large development sample + untouched
  internal test + reserve. Consumes a subset of the 329; preserves internal
  untouched confirmation.
- **V2-CENSUS (descriptive only):** all 329 describe the protocol-defined
  eligible djangoCMS population. Choosing census consumes all cases during
  development and destroys internal untouched confirmation; it is only for a
  clearly separate descriptive question (population description), never for the
  confirmatory correctness–cost claim.

## 7. Authorized development-inference ceilings (mission C3)

- NEW V2 development cells ≤ 450;
- NEW tokens ≤ 2,500,000;
- NEW API/frozen-pricing cost ≤ USD 1.00;
- no V2 TEST/RESERVE calls;
- no result-dependent reruns;
- no provider/model family change.

If the sample-size design requires more than these ceilings, do NOT call the
model; freeze the design and continue with proposal/cross-repo work.

## 8. Pre-call freeze checklist (before any new V2 cell)

1. V2 development case IDs frozen (from the reconstructed frame, excluding
   `LEGACY_EXPOSED_V1`);
2. DEV_TRAIN / DEV_VALIDATION assignment frozen (metadata-only, deterministic
   seed, hashes);
3. prompt/model/provider/config frozen (identical to the registered study:
   qwen/qwen3-coder @ deepinfra/turbo, temperature 0, cap 16384, Graph OFF,
   Sparse-v2 contract, protocol real-commit-p1-v1.0.0);
4. three nested reps/task unless the sample-size report gives a stronger
   reason otherwise;
5. graph setting frozen (OFF);
6. exact endpoint/provider/fallback policy frozen (deepinfra/turbo, no
   fallback);
7. all six gates PASS;
8. leakage audit PASS;
9. estimated tokens and cost documented.

## 9. Gates / audit

The standard six gates (Dataset, Input, Smoke, Dry Run, Integration, Metric) +
independent audit, all ZERO-API until the frozen split is audited, then the
live development inference is gated as in the 90-cell v1 run.

## 10. Relation to v1 and exposure

- `LEGACY_EXPOSED_V1 = true` on all 40 v1 case IDs (machine-readable list in
  `research/transparency/legacy_exposed_v1_case_ids.json`).
- None of the 40 may be used as an untouched V2 confirmatory test.
- This is a **cross-time development enlargement within one repository**
  (Stage 1 of the generalization ladder); it is NOT cross-repository
  confirmation.

## 11. Version / manifest

- Proposed v2 manifest: `research/transparency/v2_sampling_frame_reconstructed.json`
  (frame) + a split manifest to be frozen in `benchmark_data/real_commit_impact_v2/`
  when the frame is built.
- The protocol itself is frozen by this document; the split freeze is a
  separate, audited step before any model call.