# Saleor Sampling-Frame Audit — Stage-2 ready-to-run

**Date:** 2026-09-16 evening
**Tier:** T3 data (ZERO scientific LLM calls)
**Repo:** https://github.com/saleor/saleor
**Anchor:** `2c48391b652c26ce4f27a53d6532d4c873306af0` (pinned snapshot HEAD,
matches `benchmark_data/repository_profiles/saleor.yaml` version 3.23.0)
**Adapter:** `miner.PRODUCTION_ROOTS = ("saleor",)` only; all frozen rules
(eligibility, leakage, dedup R1/R2/R3, selection) unchanged.

---

## 1. History acquisition

- Cache: `dist/pilot-repo-cache/saleor`.
- Was shallow (depth 1); **unshallowed 2026-09-16 evening** via
  `git fetch --unshallow origin`.
- Now **non-shallow, 22,615 commits**, tags present (3.23.0 etc.).

## 2. Funnel (reconstructed, zero API)

| Stage | Count |
|---|---:|
| window scanned (6000 newest ancestors) | 6000 |
| eligible after frozen filters + leakage | 2409 |
| after R1/R2 duplicate removal | 1352 |
| after R3 adjudication (independent eligible pool) | **1316** |

The independent eligible pool (1316) is **~4× the djangoCMS pool (329)**.

## 3. Distribution of the independent eligible pool (1316)

- **Year (target commit):** 2020: 128, 2021: 257, 2022: 222, 2023: 211,
  2024: 189, 2025: 197, 2026: 112. Modern PR-era history is dense and current.
- **Proxy size:** 1: 366, 2: 342, 3: 203, 4: 122, 5: 81, 6: 59, 7: 46,
  8: 35, 9: 20, 10: 14, 11: 16, 12: 12. Bucket mix: small (≤2) ≈ 54%,
  medium (3–6) ≈ 35%, large (7–12) ≈ 11%.
- **Candidate-universe:** not persisted in the enumerator output (computed at
  case-build time); Saleor universes are expected larger than djangoCMS
  (several hundred files per parent).
- **Change type (conservative intent taxonomy):** recorded in the frame JSON.

## 4. Production-universe semantics (adapter)

- `miner.PRODUCTION_ROOTS = ("saleor",)` selects only top-level `saleor/`
  production Python (excludes `saleor/tests/`, migrations, generated files,
  `__pycache__`) — consistent with the frozen profile's `artifact_universe`.
- Same frozen exclusions (tests/migrations/generated/vendor/whitespace-only).

## 5. Parent/target + proxy

- Same frozen M4A machinery: parent-commit-only inputs, hidden observed-change
  proxy, intent-path-leakage off.

## 6. Graph / history capability

- Dependency graph: parent-only AST import graph buildable (frozen builder).
- History/co-change: **full history now cached** → parent-visible co-change
  features are feasible for Saleor (unlike djangoCMS v1).

## 7. Sample size

- `reports/SALEOR_SAMPLE_SIZE_ANALYSIS.md`: at observed 13.3% negative
  prevalence, N=150 Saleor development tasks → ~20 negatives; P(neg ≥ 20)≈0.8
  requires N≈200. Saleor's 1316 pool supports a large development set + an
  untouched internal test + reserve without exhausting the pool.

## 8. Verdict

**SUITABLE / READY-TO-RUN** for a quantitative Stage-2 (reconstruction done;
eligible pool 1316; split proposal follows). No Saleor TEST inspected; no
model inference tonight.

## 9. Blocker (if any)

- None for the frame. Case-bundle materialization + split freeze require a
  Saleor-specific build step (mirroring the djangoCMS V2 builder) before any
  inference; that is a separate audited data step, not a scientific call.