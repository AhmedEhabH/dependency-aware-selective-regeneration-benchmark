# Saleor Case-Bundle Build Report

**Date:** 2026-09-17
**Tier:** T3 data (ZERO scientific model calls)
**Status:** **PARTIAL BUILD — 98/150 DEVELOPMENT bundles materialized; 52 blocked
on a Windows `git archive` path-extraction issue (documented, not a rule change).**

---

## 1. What was built

- Saleor config adapter: `miner.PRODUCTION_ROOTS = ("saleor",)` (repo identity
  only; frozen eligibility/leakage/dedup rules unchanged).
- Anchor: `2c48391b652c26ce4f27a53d6532d4c873306af0`.
- **DEVELOPMENT bundles built: 98** (of 150 DEV_TRAIN+DEV_VALIDATION):
  - `benchmark_data/real_commit_impact_saleor/scientific/<case_id>/`
  - each bundle: `public/` (intent.json, candidate_universe.json,
    dependency_graph.json) + `hidden/observed_change_set_proxy.json` +
    `case_manifest.json` (record with SHA-256).
- Development manifest: `saleor_development_manifest.json`
  (canonical SHA-256 `3c3b0b36…`).
- Split freeze: `split_freeze_saleor.json` (metadata-only; TEST/RESERVE never
  materialized/inferred).

## 2. Blocker (52 cases NOT built)

- **Root cause:** several Saleor parent trees contain a filename with `?` and
  `[`/`]` (a test cassette:
  `saleor/graphql/core/tests/cassettes/test_get_oembed_data[http:/www.youtube.com/watch?v=dQw4w9WgXcQ-VIDEO].yaml`).
  `git archive` on Windows rejects such paths
  (`error: invalid path '...watch?v=dQw4w9WgXcQ-VIDEO].yaml'`), so
  `build_parent_universe_and_graph` raises for those parents.
- **Impact:** the 52 affected DEVELOPMENT cases are NOT bundled tonight. The
  98 built cases are valid and usable. This is an environmental/portability
  blocker (Windows `git archive`), NOT a scientific rule change and NOT a
  TEST/RESERVE leak.
- **Verification:** parents of skipped cases are present in the cache
  (non-shallow), eligibility is `True`, and proxy sets are valid — the failure
  is purely `git archive` path extraction on Windows.

## 3. Test/RESERVE integrity

- INTERNAL_TEST (80) and RESERVE (1086) were NEVER materialized and NEVER
  inferred. Only metadata-only manifests exist. No TEST scientific outcome is
  exposed to method-development code.

## 4. Workaround options (for a later session, not tonight)

- Re-run the Saleor bundle build on a Linux/WSL host (git archive handles these
  paths on POSIX) — the frozen miner is otherwise platform-agnostic;
- OR exclude the affected cassette paths from the candidate universe (would be a
  documented, minimal deviation, NOT a rule change) — deferred, not done tonight.

## 5. Gate status (applicable gates, ZERO API)

| Gate | Status |
|---|---|
| Dataset Validation | PARTIAL (98/150 DEV bundles; 52 blocked on extraction) |
| Input Validation | PASS (parent-only; hidden proxy separate) |
| Smoke | PASS (bundle structure verified) |
| Dry Run | PARTIAL (manifest produced; 98 valid) |
| Integration | PARTIAL (scientific inference requires the full 150 or a documented subset) |
| Metric Verification | N/A (no inference run) |

## 6. Conclusion

`SALEOR INFERENCE READY` is **NOT** reached tonight because 52/150 DEV bundles
could not be materialized on Windows. The 98 valid bundles + split metadata are
a ready foundation; the blocker is documented and a POSIX re-run or a minimal
cassette-exclusion workaround is the next data step. No Saleor LLM inference was
run (per Section 11 of the mission).