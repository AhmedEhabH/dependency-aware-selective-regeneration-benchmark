# Saleor Portability Fix + 150/150 DEVELOPMENT Bundle Build Report

**Date:** 2026-09-17
**Tier:** T3 data (ZERO scientific model calls)
**Model:** openrouter/deepseek/deepseek-v4-flash-0731
**Status:** **`SALEOR DEVELOPMENT DATASET READY`** — portability blocker resolved;
equivalence proven 98/98; all 150 DEVELOPMENT bundles built and verified.

---

## 1. The blocker

The frozen `miner.extract_parent_tree` used whole-tree `git archive` to
materialize each Saleor parent. Several Saleor parents contain a NON-PRODUCTION
test cassette whose filename includes `?`, `[`, `]`:

```
saleor/graphql/core/tests/cassettes/test_get_oembed_data[http:/www.youtube.com/watch?v=dQw4w9WgXcQ-VIDEO].yaml
```

`git archive` on Windows rejects such paths, raising for the 52 affected parents.

## 2. The fix — production-only parent materializer (SCIENCE UNCHANGED)

`scripts/saleor_portability_fix.py` implements a platform-independent,
production-only parent materializer:

1. `git ls-tree -r --name-only <parent>` enumerates the tree objects.
2. The **EXACT existing frozen Saleor production-file predicate** is applied
   (`saleor/**/*.py` under `PRODUCTION_ROOTS=("saleor",)`, minus
   `_is_excluded` segments — identical to what `build_candidate_universe`
   globs).
3. Required production Python blobs are materialized via `git cat-file --batch`
   (one persistent process; platform-independent).
4. Repository-relative paths are preserved under the temporary snapshot root.
5. Candidate universe + AST/dependency graph are built from these files ONLY.
6. Irrelevant test/cassette paths are never extracted (the `?`/`[`/`]`
   cassette is excluded by the frozen predicate anyway).
7. No hidden target-state information can enter the parent snapshot (only
   `parent` tree objects are read).

This is a **pure extraction-mechanism change**: no eligibility rule changed; no
scientific file was deleted or skipped; the downstream builders
(`build_candidate_universe`, `build_dependency_graph`, `build_case`) are
byte-identical frozen code.

## 3. Equivalence gate — 98/98 PASS

`scripts/saleor_equivalence_gate.py` re-ran the new materializer on ALL 98
previously-valid bundles and verified:

| Check | Result |
|---|---|
| Candidate-universe paths identical | **MATCH (98/98)** |
| File blob hashes identical (embedded in universe records) | **MATCH (98/98)** |
| Universe records identical | **MATCH (98/98)** |
| Dependency-graph scientific projection identical | **MATCH (98/98)** via `canonical_graph_hash` |
| Hidden observed-change proxy | **MATCH** (materializer-independent, byte-verified present) |
| Case manifest semantic content | **MATCH** (materializer-independent, byte-verified present) |

**Excluded (documented):** `generated_utc` is the ONLY nondeterministic
serialization field (a timestamp); the frozen `canonical_graph_hash` already
strips it. The `repo_id` label is preserved as `"djangocms"` (the frozen
original builder's label) so the rebuilt graph is byte-equivalent; it is a
non-scientific label.

**Definitive proof:** all rebuilt 98 bundles' canonical universe hashes and
canonical graph hashes are **identical** to the pre-portability `git archive`
snapshot (`research/transparency/saleor_98_bundle_hashes_preportability.json`):
**0 mismatches** on universe hash, **0 mismatches** on graph hash.

## 4. Rebuild — 150/150 DEVELOPMENT bundles

`scripts/build_saleor_case_bundles.py` (patched to use the production-only
materializer via `miner.extract_parent_tree = _production_only_extract`) rebuilt
all DEVELOPMENT cases:

- DEV_TRAIN + DEV_VALIDATION: **150 built / 0 skipped**
- 150/150 structurally complete (public + hidden + manifest present)
- INTERNAL_TEST (80) / RESERVE (1086): **never materialized** (0 on disk)

## 5. Fresh canonical manifest / historical evidence

- **Old partial manifest** (98-case): preserved as
  `research/transparency/saleor_development_manifest_20260916_partial_98.json`
  (canonical SHA-256 `3c3b0b369c1bf9…`).
- **Old partial split freeze**: preserved as
  `research/transparency/split_freeze_saleor_20260916_partial_98.json`.
- **New canonical manifest**: `benchmark_data/real_commit_impact_saleor/saleor_development_manifest.json`
  (canonical SHA-256 `220665abe20eb233…`).
- **Pre-portability hash snapshot**: `research/transparency/saleor_98_bundle_hashes_preportability.json`.
- **Fix evidence**: `research/transparency/saleor_portability_fix_evidence.json`.

## 6. Why the implementation changed but the scientific protocol did not

The frozen scientific protocol specifies: candidate = production `.py` files
under `saleor/`, parent-only inputs, hidden proxy separate, leakage-free
graph. The materializer only changes HOW those production blobs are fetched
(`git archive` whole-tree → `git ls-tree` + `git cat-file --batch` filtered to
the same production files). Every downstream rule, predicate, graph algorithm,
hash, and proxy is unchanged and byte-verified by the equivalence gate.

## 7. Gate status (applicable gates, ZERO API)

| Gate | Status |
|---|---|
| 1 Dataset Validation | **PASS** (150/150 DEV; split counts; TEST/RESERVE untouched) |
| 2 Input Validation | **PASS** (parent-only; hidden proxy separate) |
| 3 Pipeline Smoke | **PASS** (bundle structure 150/150; targeted real-commit tests 18/18) |
| 4 Dry Run | **PASS** (manifest + split freeze produced, fresh canonical hash) |
| 5 Integration | **PASS** (150 bundles + manifest + records schema) |
| 6 Metric Verification | N/A (no inference run yet) |
| Equivalence (portability) | **PASS 98/98** |
| Independent audit | see below |

**Independent audit (performed):** re-checked rebuilt-vs-pre-portability hashes
(0 mismatches); verified TEST/RESERVE never materialized; verified blocked-case
parents are present in cache and build OK through the new materializer;
confirmed no frozen source file was modified (only runtime monkeypatch in the
build script).

## 8. Conclusion

`SALEOR DEVELOPMENT DATASET READY`. The portability blocker is resolved without
changing any frozen scientific rule. All 150 DEVELOPMENT bundles are built,
byte-equivalent to the prior 98, and verified. Block C (Saleor DEVELOPMENT
sparse inference) is now authorized.