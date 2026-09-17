# Dataset Operational Definitions — RealCommitImpact (V1 + V2) and Saleor

**Date:** 2026-09-18
**Type:** POST-HOC / documentation audit of the FROZEN operational rules (ZERO API)
**Purpose:** thesis/reviewer clarity. This documents the EXACT operational rules
implemented by the frozen miner (`src/benchmark/real_commits/miner.py`,
`scientific.py`, `models.py`) and the frozen Route-B confirmatory protocol. It
does NOT define a new dataset and does NOT change any frozen evidence.
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731

---

## 1. "Meaningful intent" — operational rule

A commit intent (normalized commit message) is MEANINGFUL iff ALL of:

1. Non-empty after normalization (`normalize_intent`: collapse whitespace,
   drop empty lines, join with spaces).
2. `len(intent.strip()) >= 5`.
3. Does NOT match any `_BOT_OR_RELEASE_PATTERNS` (regex, case-insensitive):
   - `(chore:)?(release|bump|version)` prefix;
   - `bump` prefix;
   - `dependabot`, `renovate`;
   - `[ci skip]`;
   - `update changelog`, `changelog`;
   - `merge (branch|back|pull|request)`, `merge back`.

Failure → exclusion code `no_meaningful_intent`.

## 2. Production-source eligibility — operational rule

A commit is a **production-source candidate** iff:

- It has exactly ONE parent (single-parent commit; merge commits excluded →
  `merge_commit`).
- Its `name_status` (git diff name-status vs parent) contains ≥1 path that is
  **production Python**:
  - ends with `.py`;
  - its first path part ∈ `PRODUCTION_ROOTS` (`("cms", "menus")` for djangoCMS;
    `("saleor",)` for Saleor);
  - no path part ∈ `EXCLUDED_DIR_SEGMENTS = {tests, test_utils, migrations,
    __pycache__}`.
- The proxy (set of production changed paths) is non-empty and satisfies
  `proxy_min <= |proxy| <= proxy_max` (1..12 for scientific) and
  `total_changed <= total_diff_ceiling` (40).
- Every proxy path status == `"M"` (modified only; add/delete/rename/copy →
  `production_add_delete_rename_copy_v1_unsupported`).
- The production diff is NOT whitespace-only under `git diff -w` →
  `whitespace_only` exclusion.
- For SCIENTIFIC enumeration, intent-path leakage is forbidden:
  `allow_intent_path_leakage=False` → any proxy path mentioned in the intent
  (exact path / basename / stem) → `intent_path_leakage`.
- MINER_DEV targets are excluded (`miner_dev_target`).

`evaluate_eligibility` returns `eligible=True` only if `reason_codes == []`.

## 3. Exclusions — exact code set

`EXCLUSION_REASON_CODES` (canonical order, `models.py:44`):
`merge_commit`, `no_meaningful_intent`, `no_production_source_change`,
`tests_only`, `migrations_only`, `generated_or_vendor_only`, `whitespace_only`,
`production_add_delete_rename_copy_v1_unsupported`,
`proxy_not_subset_of_parent_universe`, `proxy_too_large`, `diff_too_large`,
`intent_path_leakage`, `duplicate_or_related_change`, `miner_dev_target`.
`enumerate_scientific_candidates` applies the scientific subset (with
`allow_intent_path_leakage=False` so `intent_path_leakage` is INELIGIBLE),
plus `whitespace_only` and `miner_dev_target`.

## 4. Deduplication — operational rules

`deduplicate_candidates` keeps a deduplicated list + adjudication records:

- **R1 (exact duplicate):** identical `frozenset(proxy_paths)` → keep the
  NEWEST commit.
- **R2 (shared PR/issue):** commits sharing a `#NNNN` PR/issue reference →
  keep the newest of the group.
- **R3 (suspected related):** overlapping proxy paths AND
  `intent_jaccard >= 0.5` AND non-identical proxy set → SUSPECTED related;
  resolved by inspection (adjudicated), keep the adjudicated winner.

## 5. Failure / evaluable-task rules (frozen, Route-B confirmatory)

- A Sparse first-pass cell that is transport-failed, schema-invalid, truncated
  (`finish_reason=length`), or otherwise non-succeeded is a **FAILED cell**
  (fn = proxy_size, recall 0), NEVER silently retried, NEVER partially
  credited.
- If a task has **no succeeded repetition**, the task is **EXCLUDED** from the
  Route-B analysis (recorded; not a zero-write-set substitute). E.g. Saleor
  `saleor-rc-012472eb8482` → 149 tasks.
- No result-dependent reruns.

## 6. 3-repetition aggregation — exact rule

- The Sparse first pass runs **3 nested repetitions per task**.
- The write-set used by Route B per task = the `predicted_write_set` of the
  **FIRST SUCCEEDED repetition in record-file order** (frozen dedupe
  semantics; `by_case` keeps the first record with
  `terminal_status == "succeeded"`). NOT a majority vote, NOT a union.
- Failed reps are skipped (not retried).

## 7. Zero-FN task handling — exact rule

- A task with `M = n_missed == 0` (Sparse omitted nothing that the proxy
  changed) contributes **0.0 to the macro ORR mean** (denominator undefined
  → contributes no recovery and no missed count to micro totals).
- The count/share of zero-FN tasks is reported explicitly
  (`curve_level_posthoc.json`: n_zero_fn, zero_fn_share) and a
  positive-denominator-only sensitivity is provided.
- This is the same rule as the frozen confirmatory metric script
  (`scripts/djangocms_confirmatory_metrics_run.py`), which sets
  `orr = 0.0` when `M == 0`.

## 8. Candidate / proxy / universe definitions (frozen)

- **Candidate universe (per task):** production `.py` files present at the
  PARENT commit under the production roots, minus
  `EXCLUDED_DIR_SEGMENTS`/suffixes (deterministic;
  `candidate_universe.json`).
- **Proxy (evaluation-only):** production files observed changed by the diff
  parent→target (`observed_change_set_proxy.json`); used ONLY for evaluation,
  never in any prompt or method feature.
- **Omitted candidate:** candidate universe minus the Sparse write-set.
- **Sparse-observed FN (evaluation-only positive):** file in the proxy AND
  omitted by Sparse.

## 9. Split freeze (seed 20260916 / 20260913)

- djangoCMS V2 (seed 20260916): DEV_TRAIN 120 / DEV_VALIDATION 30 /
  INTERNAL_TEST 80 / RESERVE 59 (289 total in v2 split; V1 30 DEV carried as
  V1_DEV for Route-B V2).
- Saleor (seed 20260916): DEV_TRAIN 120 / DEV_VALIDATION 30 / INTERNAL_TEST
  80 / RESERVE 1086 (1316 total).
- Frozen before any model result; scientific corpus selection = year-capped
  (≤5/year) newest→oldest, target 40 (V1).

## 10. Scope of this document

- Applies to the RealCommitImpact V1/V2 (djangoCMS) and Saleor datasets.
- Documents the code as frozen; no new dataset, no rule change, no evidence
  recomputation other than the read-only confirmatory characterization.