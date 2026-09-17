# Saleor Identity/Provenance Migration Report

**Date:** 2026-09-17
**Tier:** T3 data (ZERO scientific model calls)
**Model:** openrouter/deepseek/deepseek-v4-flash-0731
**Status:** **COMPLETE — 150/150 scientific-payload equivalence PASS; dataset
identity corrected; fresh Saleor scientific manifest frozen.**

---

## 1. Problem

The Saleor real-commit bundles were built with the frozen djangoCMS miner
constants, so every bundle carried **djangoCMS identity**:
- case ID `djangocms-rc-<sha>` (the case ID is rendered into the inference
  prompt: `Frozen real historical change (djangocms-rc-012472eb8482)`);
- `repository: "djangocms"`, `repository_url:
  https://github.com/django-cms/django-cms`, license ref `…#djangocms`;
- graph `repo_id: "djangocms"`; provenance `anchor_commit: 0f633fc9…`.

A Saleor Sparse run under this identity would leak the WRONG repository
provenance to the model — a scientific contamination risk.

## 2. Fix — deterministic identity migration (SCIENCE PRESERVED)

`scripts/saleor_identity_migration.py`:
1. **Deterministic rename** of all 150 case dirs `djangocms-rc-<sha>` →
   `saleor-rc-<sha>` (pure prefix swap; `<sha>` is the target-commit short sha,
   unchanged).
2. **Corrected identity fields** in the 5 JSON artifacts per bundle:
   `case_id`, `repository=saleor`, `repository_url=https://github.com/saleor/saleor`,
   `repository_license_or_manifest_ref=BSD-3-Clause; …#saleor`,
   graph `repo_id=saleor`, provenance `anchor_commit=2c48391b…`.
3. **Recomputed** `canonical_record_sha256` and the graph canonical hash for the
   corrected identity (edges/universes/proxies untouched).
4. Migrated the 1,316-case metadata, the split proposal (case IDs + recomputed
   per-role and all-pool SHAs), the dev manifest (case IDs + records + canonical
   hash), and the split freeze.
5. Wrote `research/transparency/saleor_case_id_migration.json` (old→new map,
   1316 entries).

## 3. Equivalence — 150/150 PASS

`scripts/saleor_identity_equivalence.py` compared every post-migration bundle
against the pre-migration snapshot
(`research/transparency/saleor_pre_migration_payload_snapshot.json`):

| Check | Result |
|---|---|
| parent_commit identical | **MATCH (150/150)** |
| target_commit identical | **MATCH (150/150)** |
| split membership identical | **MATCH (150/150)** |
| candidate universe records identical | **MATCH (150/150)** |
| hidden proxy paths identical | **MATCH (150/150)** |
| graph edges identical | **MATCH (150/150)** |
| new ID deterministic (saleor-rc-<target sha>) | **MATCH (150/150)** |
| identity corrected (repo/url/license/graph repo_id/anchor) | **MATCH (150/150)** |

Full per-case results: `research/transparency/saleor_identity_equivalence_150.json`.

## 4. Prompt verification

Post-migration prompt for `saleor-rc-012472eb8482`:
`Frozen real historical change (saleor-rc-012472eb8482): …` — **no `djangocms`
leak**; bundle `repository=saleor`, `repository_url=https://github.com/saleor/saleor`.

## 5. Pre-fix smoke call — ARCHIVED (not scientific)

The single pre-fix call (`saleor-…-012472eb8482-sparse_v2-r1`) is re-marked
`PRE_FIX_OPERATIONAL_SMOKE_NOT_SCIENTIFIC` with
`excluded_from_scientific_evidence: True` in the run records; it is retained
only as operational evidence of the live path (14,560 tokens, $0.0047) and is
NOT counted toward any scientific metric.

## 6. Fresh Saleor scientific manifest (frozen)

- `benchmark_data/real_commit_impact_saleor/saleor_development_manifest.json`
  canonical SHA-256 `b23cc67e05c6aeff2273…` (150 DEVELOPMENT cases,
  `saleor-rc-*` IDs, repository=saleor, anchor `2c48391b…`).
- Split: seed 20260916, DEV_TRAIN 120 / DEV_VALIDATION 30 / INTERNAL_TEST 80 /
  RESERVE 1086; all-pool SHA `6b5371c3…` (recomputed over migrated IDs;
  membership identical to pre-migration).

## 7. Authorization

A **clean 150×3 DEVELOPMENT sparse run** is authorized (2026-09-17) with hard
ceilings: **450 cells / 9,000,000 total tokens / $3.00**. No INTERNAL_TEST /
RESERVE; no result-dependent reruns; no Saleor-specific tuning. After the run
closes, the frozen Route-B transfer replication is executed and classified.

## 8. Files

- Migration: `scripts/saleor_identity_migration.py`
- Pre-migration snapshot: `scripts/saleor_snapshot_pre_migration.py` +
  `research/transparency/saleor_pre_migration_payload_snapshot.json`
- Equivalence: `scripts/saleor_identity_equivalence.py` +
  `research/transparency/saleor_identity_equivalence_150.json`
- Mapping: `research/transparency/saleor_case_id_migration.json`
- Bundles: `benchmark_data/real_commit_impact_saleor/scientific/saleor-rc-*/`