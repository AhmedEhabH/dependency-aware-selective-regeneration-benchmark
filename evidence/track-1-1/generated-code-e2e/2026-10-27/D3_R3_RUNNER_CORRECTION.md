# Track 1.1 — D3 R3 evaluator-only correction (28 October 2026)

## Root cause and preserved history

- D3 first run: `STOP_HASH_DRIFT` before candidate materialization; its STOP and R2 hash correction were committed separately.
- D3 R2 run: `git -C <disposable snapshot> diff --check` returned status 129 because the snapshot is not a Git repository. This is an evaluator infrastructure failure **before any pytest**, not evidence against D3's intended behavior.
- The R2 result publication stopped at `STOP_PATCH_SCOPE_OR_HASH`: builder left a partial `D3_OVER_D2.patch`, but no final `D3_REPAIR_RECEIPT.json` existed, so the sanitized summary correctly did not qualify it. R2's publish tool erroneously tried to publish the orphan artifact anyway.
- D3 R3: checks applicability of a *two-file exact-scope* patch via repository-independent `git apply --check`, then applies it to the disposable D2 copy, checks resulting source hashes and reverse applicability, and writes the repair receipt only on success. Original D2 source SHA guards remain unchanged; all project and frozen test inputs are unchanged.
- R3 publication only considers a D3 patch if the final sanitized receipt includes its SHA-256; orphan intermediate patches remain private to the host. Previous public milestones are immutable; R3 correction and result get separate new filenames and PROGRESS.md entries.

## Classification

D3 is a **test-informed human-designed repair control**: it is not a model-generated success, blind pass@1, or prospective A6 authorization. Original A5-R1 remains STOP. D2 stays frozen at F2P 1/3 and P2P 103/103 stable. No new paid model calls in R3. Prepared offline package cache from `PREP_PASS.json` remains unchanged.

## Gate criteria

1. Pre-publish evaluator correction *before* attempting R3 host behavior.
2. Verify 239 hashed pins, 237 Linux pins, 2 inactive Windows-only pins, 106 frozen nodes, parent/D2 source hashes and Docker image digest.
3. Build candidate in a **fresh disposable copy** (no mutation of frozen D2), verify exact patch/source hashes, and run F2P three times per node with JUnit.
4. If F2P < 3/3 stable, publish functional STOP and **do not run P2P**. Otherwise run 103 P2P nodes x 3, audit 318 physical invocations and code-quality metrics.
5. No JUnit or complete behavioral claim is implied until the researcher-host Docker run and its raw evidence have been checked. Shared DB repetitions are not independent statistical replicates.

## Evidence handling

The original raw logs may contain synthetic credentials/tokens and must remain local. Publish only allowlisted SHA-bound summaries, quality report and final qualified two-file patch. R3 no longer publishes partially created patches when a builder fails.
