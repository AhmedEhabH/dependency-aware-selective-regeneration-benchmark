# Track 1.1 — D3 evaluator integrity correction R2 — 27 October 2026

## Incident and exact root cause

The first D3 host attempt after protocol publication stopped at `STOP_HASH_DRIFT` **before producing D3 source or running pytest**. Its sanitized STOP evidence was already published under Git commit `d982051649b9b29d734877ebef42d48e12a870b4`. Preserve that record without overwriting or changing its verdict.

The published runner mistakenly used a stale hard-coded SHA-256 for `T11_D3_CREATE_CONTROL.py`:

- Old erroneous embedded SHA-256: `0f0aaee03ce3058ee9098d0db6f543a5fad56412258c7edf3bf0368735592d31`
- **Correct SHA-256 of unchanged original repair builder:** `2736b630c55f465d3de0d879e0540b74c1e9412855c05764537b3663a8078966`
- Source correction: **one pinned string substitution in runner**, no change to D3 repair builder, frozen F2P/P2P, D2 sources, frozen lock, model outputs or OCI image.
- The repaired evaluator is named `T11_D3_E2E_R2_FROM_HASHED_CACHE.sh` (new file, does not replace prior GitHub copy).

## Pre-run research controls

- Original A5-R1 STOP is unchanged. D2 diagnostic stays frozen: 1/3 F2P, 103/103 P2P in 3 shared-runtime repetitions.
- D3 is an engineered **test-informed repair control** designed after D2 failures, not an independently model-generated pass@1 result.
- The earlier protocol and its infrastructure STOP remain recorded. This correction is timestamped and published **before** resuming D3 behavioral tests.
- Reuse existing qualifying offline prep receipt `4094dc06e834daadc309544de1e7fa2baebbc1f35fb8fcd626f6106239a96611`; no new model calls or package download.
- Require 3/3 stable F2P before any P2P; if passed, 103/103 stable P2P and 318 JUnit files. Preserve all STOP/JUnit in local evidence.
- New result publications must use `D3_R2_*` filenames and a distinct `PROGRESS.md` milestone; do not overwrite the previous D3 STOP.

## Validation boundary

Local tests cover full-kit SHA consistency, Bash outer+inner parse, Python compilation, extracted repair builder and frozen test runner selftests, negative original D2 F2P gate, and synthetic JUnit/report processing. These do not constitute real Saleor E2E results. Docker behavioral results only exist after running on the researcher host.
