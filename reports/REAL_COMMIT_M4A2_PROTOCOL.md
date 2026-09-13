# M4A-2 Protocol — RealCommitImpactDataset-v1 Scientific Corpus

**Date:** 2026-09-13
**Milestone:** M4A-2 — mine + adjudicate + split-freeze the **scientific**
real-commit corpus (30–40 clean independent djangoCMS historical changes)
**Branch:** `research/real-commit-impact-dataset-v2-corpus-01`
**Mode:** deterministic data construction only; **ZERO scientific LLM/API calls**.
**Boundary:** this milestone builds and freezes the corpus + splits ONLY.
M4A-3 (held-out evaluation: Full-v2 / Sparse-v2 / Graph@K / Random@K / LocAgent)
belongs to a separately frozen protocol AFTER this dataset + splits are audited.

---

## 1. Pre-registration statement

This protocol is written and pushed **BEFORE** any split is assigned and
**BEFORE** any model result exists. The split procedure, seed, and rules below
are frozen by this document and by the machine-readable split manifest produced
from it. No split decision uses any model output (none exist).

## 2. Scientific boundary (unchanged from M4A-1, applied to scientific cases)

For every accepted target commit T with single parent P:

| Item | Rule |
|---|---|
| `parent_commit` P | the single parent of T (merge commits excluded) |
| **visible intent** | normalized commit message (`intent_source = commit_message`) |
| **inference repository state** | P ONLY |
| **candidate universe** | production Python files at P ONLY (`cms/**`, `menus/**`, excluding tests/test_utils/migrations/`__pycache__`) |
| **dependency graph** | AST import edges derived from P ONLY |
| **hidden evaluation proxy** | production files observed changed by diff P → T (status `M` only in v1) |

The historical diff is an **OBSERVED CHANGE-SET PROXY** — it is NEVER described
as perfect semantic ground truth, and no P/R/V/H semantic gold is fabricated
from it. The proxy is physically separated into
`hidden/observed_change_set_proxy.json` and NEVER present in `public/`.

## 3. Exclusion rules (frozen M4A-1, with scientific strictness)

The M4A-1 frozen v1 eligibility/exclusion rules are applied **without
loosening** and with **`allow_intent_path_leakage=False`** (any scientific
candidate whose intent mentions a changed path is INELIGIBLE via
`intent_path_leakage`; the 6 MINER_DEV cases remain permanently excluded via a
new additive code `miner_dev_target`). Exclusion reason codes persisted:

`merge_commit`, `no_meaningful_intent`, `no_production_source_change`,
`tests_only`, `migrations_only`, `generated_or_vendor_only`,
`whitespace_only`, `production_add_delete_rename_copy_v1_unsupported`,
`proxy_not_subset_of_parent_universe`, `proxy_too_large`, `diff_too_large`,
`intent_path_leakage`, `duplicate_or_related_change`, **`miner_dev_target`**
(M4A-2 additive; never loosens an existing rule).

## 4. Scan window and candidate enumeration

- **Window:** the newest **6000** ancestors of the frozen anchor
  `0f633fc9fa213357f4202482aab2b0edad680f95` (tag `5.0.0`), newest-first
  deterministic topo order — the modern PR-era djangoCMS history (≈2015–2025).
  Older commits (svn-era, pre-PR) are intentionally outside the scientific
  window; this is a **quality decision**, not a rule loosening.
- **MINER_DEV exclusion:** the 6 MINER_DEV target SHAs are never scientific
  candidates (reason `miner_dev_target`).
- **Leakage:** `allow_intent_path_leakage=False` — a scientific case with
  `intent_mentions_changed_path=true` is ineligible.

## 5. Duplicate / related-change detection (pre-registered)

All are deterministic; every hit is reported in the adjudication report.

- **R1 exact-proxy-set duplicate:** identical `frozenset(proxy_paths)` as an
  earlier-accepted candidate → keep the newest, exclude the rest
  (`duplicate_or_related_change`).
- **R2 shared-PR-reference:** intents share a `#NNNN` PR/issue reference →
  same PR/issue group → keep the newest, exclude the rest
  (`duplicate_or_related_change`).
- **R3 suspected-related (manual adjudication):** candidates share ≥1 proxy
  path AND differ in proxy set AND normalized-intent token Jaccard ≥ 0.5 →
  flagged as suspected related; adjudicated by inspection (keep the newest if
  the messages describe the same change; otherwise both are kept). Every R3
  pair and its decision is listed in the adjudication report.

Related or duplicate historical changes **never appear as independent
examples** in the accepted corpus.

## 6. Deterministic selection (temporal spread + quality)

From the deduplicated, eligibility-clean pool, select **TARGET=40** cases via
**year-capped selection**:

- Group candidates by calendar year of `target_commit_time` (UTC).
- Iterate years newest → oldest; within each year take candidates newest →
  oldest up to **CAP=5** per year; stop when TARGET=40 is reached.

This yields a defensible temporal spread (≈2016–2025) while preferring recent,
PR-referenced, conventional-commit intents. If fewer than 30 survive all
filters, the corpus is smaller and the shortfall is reported — **rules are
never loosened to reach 40**.

## 7. Split freeze (BEFORE any model result)

- **Split roles:** `TRAIN`, `VALIDATION`, `HELD_OUT_TEST`; `MINER_DEV` remains
  separate and is permanently excluded from final metrics.
- **Target ratio (pre-registered):** TRAIN 60% / VALIDATION 15% /
  HELD_OUT_TEST 25% (≈ 24 / 6 / 10 for 40 cases). If metadata balance makes
  this ratio scientifically poor, the simplest defensible metadata-only split
  is chosen, documented in this protocol's split addendum, and frozen before
  any model call.
- **Seed (frozen):** `20260913`.
- **Procedure (metadata-only, deterministic, no model output):**
  1. Bucket accepted cases by proxy-size bucket
     (`small` ≤2, `medium` 3–6, `large` 7–12 — the frozen `_shape_bucket`
     boundaries).
  2. Within each bucket, sort by `(target_commit_time, case_id)`.
  3. Use `random.Random(seed)` to deterministically shuffle each bucket.
  4. Allocate each bucket's members to TRAIN → VALIDATION → HELD_OUT_TEST in
     seeded order, proportional to the target ratio, rounding to whole cases
     so the overall counts hit the target as closely as possible.
  5. **Relatedness guard:** because R1/R2/R3 already removed related changes,
     each accepted case is independent; the split freeze additionally verifies
     no accepted pair shares a proxy path AND a PR reference, and it asserts
     `MINER_DEV ∩ scientific == ∅`.
- **Persisted outputs:** machine-readable
  `benchmark_data/real_commit_impact_v1/split_freeze.json` containing the seed,
  procedure description, per-case split assignment, per-split counts + hashes
  (split list SHA-256, overall manifest SHA-256), and the frozen ratio.

## 8. Records and artifacts (per accepted scientific case)

Same versioned deterministic record schema as M4A-1, with
`partition_role="SCIENTIFIC"` and `split ∈ {TRAIN, VALIDATION, HELD_OUT_TEST}`.
Every record preserves: repository identity, `parent_commit`, `target_commit`,
`target_commit_time`, `intent_text` + `intent_source`, candidate universe
(PARENT only, artifact + count + SHA-256), dependency graph (PARENT only,
artifact + SHA-256), hidden observed change-set proxy (artifact + count +
SHA-256), `change_statuses`, `eligibility_decision` + `eligibility_reason_codes`,
`intent_mentions_changed_path`, provenance hashes, `case_id`, and the
deterministic `canonical_record_sha256`.

## 9. Adjudication report (deliverable)

`reports/REAL_COMMIT_M4A2_ADJUDICATION.md` + machine-readable
`reports/real_commit_m4a2_adjudication.json`:

- number of commits scanned;
- exclusion counts by reason code;
- accepted count;
- proxy-size distribution;
- change-type distribution (intent-derived conservative taxonomy);
- temporal distribution;
- intent-source quality notes;
- suspected related/duplicate changes (R3 list) and every adjudication
  decision with rationale;
- accepted-case table with parent/target/proxy size.

## 10. Validation (unchanged six gates + scientific gates + audit)

The EXACT M4A-1 six Pre-Benchmark Validation gates remain green (frozen
regression). A scientific-corpus six-gate set is added (Dataset / Prompt /
Pipeline Smoke / Dry Run / Integration / Metric) plus split-freeze + leakage
checks, all ZERO-API. Independent audit via
`scripts/verify_real_commit_dataset_scientific.py`. Full unit/integration/
leakage/split-leakage/parent-only/M1-M3 regression suites + ruff + mypy +
compileall + full pytest.

## 11. Reference files

- Scientific builder: `scripts/build_real_commit_dataset_scientific.py`
- Scientific verifier: `scripts/verify_real_commit_dataset_scientific.py`
- Scientific logic: `src/benchmark/real_commits/scientific.py`
- Tests: `tests/unit/test_real_commit_scientific_*.py`,
  `tests/integration/test_real_commit_scientific_*.py`
- Data: `benchmark_data/real_commit_impact_v1/scientific/`,
  `.../scientific_manifest.json`, `.../split_freeze.json`
- Reports: `reports/REAL_COMMIT_M4A2_PROTOCOL.md`,
  `reports/REAL_COMMIT_M4A2_ADJUDICATION.md`,
  `reports/REAL_COMMIT_M4A2_VALIDATION.md`,
  `reports/REAL_COMMIT_M4A2_AUDIT.md`, `reports/real_commit_m4a2_gates.json`

## 12. Scientific boundary reminder

ZERO scientific model calls in this milestone. No Full-v2 / Sparse-v2 /
Graph@K / Random@K / LocAgent execution and no held-out evaluation yet.