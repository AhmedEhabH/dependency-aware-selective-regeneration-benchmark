# M4A-1 Protocol — RealCommitImpactDataset-v1 Miner Freeze

**Date:** 2026-09-13
**Milestone:** M4A-1 — RealCommitImpactDataset-v1 miner + schema + leakage barrier + MINER_DEV cases
**Branch:** `research/real-commit-impact-dataset-v1-miner-01`
**Mode:** implementation + deterministic data construction only; **ZERO scientific LLM/API calls**.

---

## 1. Scientific boundary (frozen)

For every target commit T with single parent P:

| Item | Rule |
|---|---|
| `parent_commit` P | the single parent of T (merge commits excluded) |
| **visible intent** | normalized commit message (`intent_source = commit_message` in M4A-1) |
| **inference repository state** | P ONLY |
| **candidate universe** | production Python files present at P ONLY (`cms/**`, `menus/**`, excluding `tests`/`test_utils`/`migrations`/`__pycache__`) |
| **dependency graph** | derived from source present at P ONLY (AST import edges) |
| **hidden evaluation proxy** | production files observed changed by diff P -> T (status M only in v1) |

The diff is an **OBSERVED CHANGE-SET PROXY**, never perfect semantic ground
truth. No P/R/V/H semantic gold is fabricated from Git diffs. The hidden proxy
is physically separated into `hidden/observed_change_set_proxy.json` and is
NEVER present in the public inference bundle (`public/`).

## 2. Upstream repository handling

- Repository: django CMS, URL frozen in `benchmark_data/manifests/repositories.yaml`
  (`https://github.com/django-cms/django-cms`).
- Historical anchor: pinned commit `0f633fc9fa213357f4202482aab2b0edad680f95`
  (tag `5.0.0`), the same anchor frozen in M3.
- Miner-development discovery scans **ancestors** of the anchor only
  (newest-first deterministic topo order); no future commits after the anchor.
- Cache: ignored directory `dist/real-commit-cache/djangocms` (full clone,
  `--no-checkout`). Acquired with the system `git` CLI via `subprocess`; no
  GitPython. All checkout/verify operations fail closed on SHA mismatch.
- Only provenance is committed (URL, anchor, parent/target SHAs, hashes,
  filters, miner version), never the upstream tree.

## 3. v1 eligibility / exclusion rules (frozen)

A target commit is eligible only when all of these are true:

- exactly one parent (no merge commit);
- non-empty meaningful human-readable commit message;
- at least one production Python file under `cms/` or `menus/`;
- all proxy production paths existed in the parent candidate universe;
- all proxy production changes are ordinary modifications (`M`) for v1;
- no production add/delete/rename/copy in v1;
- observed production proxy size in `[1, 12]` inclusive;
- total diff size ≤ 40 changed paths (frozen operational ceiling);
- not tests-only / migrations-only / generated-vendor-only;
- not whitespace-only for the production diff (`git diff -w` check);
- not a release/version-bump/bot-only/changelog-only commit;
- intent does not trivially reveal the exact changed production path(s),
  for scientific cases (MINER_DEV may keep **at most one** leak case to test
  the detector; permanently excluded from held-out).

Exclusion reason codes (persisted, never silently dropped):

`merge_commit`, `no_meaningful_intent`, `no_production_source_change`,
`tests_only`, `migrations_only`, `generated_or_vendor_only`,
`whitespace_only`, `production_add_delete_rename_copy_v1_unsupported`,
`proxy_not_subset_of_parent_universe`, `proxy_too_large`, `diff_too_large`,
`intent_path_leakage`, `duplicate_or_related_change`.

## 4. Record schema

Versioned deterministic JSON schema (see
`benchmark_data/real_commit_impact_v1/schema.json`). Every record includes:
`schema_version`, `case_id`, `repository`, `repository_url`,
`repository_license_or_manifest_ref`, `parent_commit`, `target_commit`,
`target_commit_time`, `intent_text`, `intent_source`, `intent_sha256`,
`candidate_universe_artifact/count/sha256`, `dependency_graph_artifact/sha256`,
`observed_change_set_proxy_artifact/count/sha256`, `change_statuses`,
`rename_delete_metadata`, `change_type`, `eligibility_decision`,
`eligibility_reason_codes`, `intent_mentions_changed_path`, `partition_role`,
`split`, `miner_version`, `provenance_hashes`, `created_utc`,
`canonical_record_sha256`.

Canonical hashes ignore **only** explicitly declared timestamp-only metadata
(`created_utc` and the self-referential `canonical_record_sha256`).

## 5. Split policy (schema support now, no final split today)

Allowed values: `MINER_DEV`, `TRAIN`, `VALIDATION`, `HELD_OUT_TEST`.

- `MINER_DEV` is permanently excluded from all final metrics.
- `HELD_OUT_TEST` is immutable once assigned and never used for tuning.
- Related commits / same PR group must not cross splits.
- Future split assignment frozen before observing model results.

## 6. Source-graph reuse (frozen identities preserved)

Reuses `src/benchmark/external_validity/source_graph.py` with
backwards-compatible parameterization only:
`build_candidate_universe(..., package_roots=("cms","menus"))` and
`build_dependency_graph(..., repo_id="djangocms", version="5.0.0")` retain
defaults identical to the frozen behavior. Regression-verified:

- candidate universe count **144**, canonical hash **`43f4279b...`**
- graph edge count **562**, canonical hash **`0a6bf0f7...`**

## 7. Reference files

- Builder: `scripts/build_real_commit_dataset.py`
- Independent verifier: `scripts/verify_real_commit_dataset.py`
- Source: `src/benchmark/real_commits/{models,miner,validation}.py`
- Tests: `tests/unit/test_real_commit_{models,filters,provenance}.py`,
  `tests/integration/test_real_commit_{miner_pipeline,leakage_barrier,source_graph_regression}.py`
- Data: `benchmark_data/real_commit_impact_v1/`
- Six gates: `reports/REAL_COMMIT_M4A1_VALIDATION.md`,
  `reports/real_commit_m4a1_gates.json`
- Audit: `reports/REAL_COMMIT_M4A1_AUDIT.md`