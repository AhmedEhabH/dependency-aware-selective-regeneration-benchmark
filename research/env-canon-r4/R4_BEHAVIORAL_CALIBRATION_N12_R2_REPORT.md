# R4 Behavioral Calibration N12 — Attempt-6 Report

**Mission:** `M17_D7_R4_BEHAVIORAL_CALIBRATION_N12_ATTEMPT6`
**Date:** 2026-10-14
**Class:** T3 real behavioral environment calibration (canonical Attempt-6)
**Verdict:** `PASS_READY_FOR_FULL144_PREEXECUTION_FREEZE`
**Exact next gate:** `M17_D7_R4_FULL144_PREEXECUTION_FREEZE`

## Summary

The full frozen stratified N12 executed under one frozen Attempt-6 driver and
the qualified runtime-toolhouse-clean execution-image binding:

- **N_EXECUTED = 12 · N_PASS = 12 · N_FAIL = 0**
- Total wall time: 2082.03 s (sequential, one unit at a time)
- Every scientific container ran with `--network=none`; no pull, no build, no download.

## Authorities

| item | value |
|---|---|
| Starting HEAD | `6f6dcf6f09a6e43bcde0dafc30e0cd748ce63254` |
| Attempt-6 preexecution freeze HEAD | `18d2527daeb236e9053ba78870b3894928ceed89` |
| Execution-image binding | `research/env-canon-r4/R4_EXECUTION_IMAGE_BINDING_RUNTIME_CLEAN.json` |
| Binding semantic hash | `5169c69d45f0761c85792ec182c9e949f58d8c9f5a29355d5a371944293d2ef2` |
| Runtime-toolhouse repair authority | `f6ce802b33bcf3c21f611941801c563eb2d913dd` |
| R4-C symlink successor | `30d0abfa5323e93d5438a6665fa2529b6e2555e5` |
| External run root | `D:\WP2\runs\r4-behavioral-calibration-n12-r2-attempt6-2026-10-14` (3-way agreement) |

## Per-unit results

| # | unit | result | elapsed | execution image | image provenance |
|---|---|---|---|---|---|
| 1 | vu-b9808f19ace4 | PASS | 166.00s | nat-34c1a3756742:latest | EXISTING |
| 2 | vu-692af9112c6d | PASS | 153.02s | nat-f65b9bf250fd-py312-bookworm:r4-composite-20261013 | R4_COMPOSITE_REPAIR |
| 3 | vu-e4998719ee01 | PASS | 238.45s | nat-34c1a3756742:latest | EXISTING |
| 4 | vu-db74b3640c98 | PASS | 136.61s | nat-a39687f3d19c:latest | EXISTING |
| 5 | vu-422bca69f329 | PASS | 137.00s | nat-cc2f641e9e04:latest | EXISTING |
| 6 | vu-13c1de1de71e | PASS | 139.21s | nat-02b9bb45ba01:latest | EXISTING |
| 7 | vu-b78ebcf3e530 | PASS | 531.99s | nat-591718dce38a:latest | EXISTING |
| 8 | vu-bfe987de6e53 | PASS | 126.64s | nat-0728db662cde:latest | EXISTING |
| 9 | vu-eda4e9f82401 | PASS | 96.68s | nat-62bc3631c27d-runtimeclean:r4-toolhouse-clean-20261014 | R4_RUNTIME_TOOLHOUSE_CLEAN |
| 10 | vu-457f26c93ff1 | PASS | 155.14s | nat-d35546f097f4-runtimeclean:r4-toolhouse-clean-20261014 | R4_RUNTIME_TOOLHOUSE_CLEAN |
| 11 | vu-ffe68ddec229 | PASS | 131.93s | nat-f65b9bf250fd-runtimeclean:r4-toolhouse-clean-20261014 | R4_RUNTIME_TOOLHOUSE_CLEAN |
| 12 | vu-0e0ef31c7634 | PASS | 69.36s | nat-d7d5ae76a87f-runtimeclean:r4-toolhouse-clean-20261014 | R4_RUNTIME_TOOLHOUSE_CLEAN |

Every unit: `NETWORK_UNAVAILABLE`, `install_rc=0`, `pipcheck_rc=0`,
`native_failures=[]`, `import/manage/pytest = 0`.

## Special evidence

- **Source fidelity (units 1–2):** `PyXB==1.2.5` and `authorizenet==1.1.4` consumed (version probes + pipfreeze).
- **Composite image (unit 2):** `nat-f65b9bf250fd-py312-bookworm:r4-composite-20261013`; in-container `special_pyver=3.12`.
- **Symlink materialization (units 6–7):** executed via the qualified R4-C symlink successor (Git-faithful symlinks materialized before behavioral gates); both PASS.
- **Runtime-toolhouse cleanliness (units 9–12):** each used its qualified runtime-clean successor; `toolhouse_present=[]` (wheel and all `BUILD_TOOLHOUSE_ONLY_DISTS` absent); the unchanged frozen R3 gate PASSed.
- **Recovery overlay (unit 10):** `pylint==2.9.6` consumed from the R4-E recovery overlay (version probe `pylint=2.9.6`).

## Network / download / pull / build counts

pull = 0 · build = 0 · download = 0 · network = disabled for every unit.

## Frozen scientific invariance

R4-D plan, population, exact N12, R3 gate semantics, `BUILD_TOOLHOUSE_ONLY_DISTS`,
source-fidelity, recovery overlay, R4-C symlink successor, Python versions,
dependency closures, native-profile contracts, and all original qualified Docker
image IDs — **UNCHANGED** (byte-for-byte verified from `f6ce802b` to HEAD).

## Evidence

- `research/env-canon-r4/R4_BEHAVIORAL_CALIBRATION_N12_R2_RECEIPT.json`
- `research/env-canon-r4/R4_BEHAVIORAL_CALIBRATION_N12_R2_REPORT.md` (this file)
- `research/env-canon-r4/R4_BEHAVIORAL_CALIBRATION_N12_R2_INVARIANCE_AUDIT.json`
- `research/env-canon-r4/R4_EXECUTION_IMAGE_BINDING_RUNTIME_CLEAN.json`

## Exact next gate

`M17_D7_R4_FULL144_PREEXECUTION_FREEZE` (not started automatically).