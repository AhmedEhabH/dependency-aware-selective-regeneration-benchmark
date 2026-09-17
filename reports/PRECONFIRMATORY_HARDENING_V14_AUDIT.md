# Pre-Confirmatory Hardening V14 — Independent Audit

**Date:** 2026-09-17
**Auditor:** independent verification pass (zero API) over the V14 deliverables.
**Mission:** OPENCODE_PRECONFIRMATORY_HARDENING_V14_2026-09-17.md
**Gates:** Dataset / Input / Smoke / Dry Run / Integration / Metric + independent
audit (T3 discipline), scoped to a ZERO-API characterization/ablation + freeze
milestone (no new evaluation strategy on new data; the frozen Route-B V2
method is unchanged).

---

## 1. Scope

- A. Ranker-identity audit (CIA vs Hybrid, name audit).
- B. Incremental-evidence ablation (djangoCMS + Saleor DEVELOPMENT).
- C. Confirmatory freeze packet V2 (supersedes V1).
- D. Confirmatory API budget freeze.
- E. Proposal V1.4.
- F. Traceability ledgers.
- G. Gates / git / tag / export.

## 2. ZERO-API verification

- No model/API call was made. All computation is deterministic recomputation
  from committed run records + public case bundles (BM25/path-token/graph
  features, hypergeometric analytic Random, task-level bootstrap).
- No INTERNAL_TEST/RESERVE case was loaded: djangoCMS audit tasks (174) have
  0 overlap with INTERNAL_TEST (80) and 0 with RESERVE (59); Saleor audit used
  the 149 DEV tasks only.

## 3. Gate table

| Gate | Status | Evidence |
|---|---|---|
| Dataset (DEV only; INTERNAL_TEST sealed) | PASS | run records are DEV; 0 INTERNAL_TEST/RESERVE overlap |
| Input / feature construction (parent-visible only) | PASS | reuses frozen `build_task` (no gold in features) |
| Pipeline smoke (audit + ablation run end-to-end) | PASS | `scripts/route_b_ranker_identity_audit.py` ran clean |
| Dry run (deterministic, no API) | PASS | same code path as frozen V2/transfer |
| Integration (both repos) | PASS | 174 djangoCMS + 149 Saleor tasks processed |
| Metric (synthetic known TP/FP/FN) | PASS | ORR/recovered per task recomputed via frozen `recovery_at`; matches frozen JSONs |
| Independent audit | PASS | this report + scalar-relation re-derivation |
| Leakage (no gold feature; no future state) | PASS | reused frozen pipeline; hidden proxy only at evaluation |
| INTERNAL_TEST/RESERVE untouched | PASS | verified 0 overlap |
| No frozen historical output modified | PASS | git diff shows only additive/new files + ledgers |

## 4. Key audit findings (re-derived independently)

1. **CIA ≡ Hybrid mathematically.** From `scripts/route_b_v2_robustness.py`:
   `hybrid = 0.5*bm + 0.5*nb` with `bm` = normalized BM25 and `nb` = binary
   graph-neighbor; the CIA ordering key is `-(bm + nb)`. Since
   `hybrid = 0.5*(bm + nb)` and 0.5 > 0, the two descending sorts are
   identical (same path tie-break). Rank-equivalence proven by construction.
2. **Empirical confirmation:** frozen `route_b_v2_results.json` and
   `saleor_route_b_transfer_results.json` show identical CIA and Hybrid
   macro/micro ORR + recovered counts at every B on both repos. The audit
   recomputation found **0 differing task-budget cells** at B={1,3,5,10}
   (696 djangoCMS + 596 Saleor cells) and full-rank identity on all 323 tasks.
3. **Name audit:** the frozen arm is exactly `normalized BM25 + binary
   graph-neighbor`; it is NOT dependency-propagation CIA. The genuinely
   classical CIA baseline (`classical_cia_baseline_v1.py`) is a different
   script. Terminology corrected to `BM25+Graph-Neighbor Composite (historical
   label: CIA)`; Hybrid reclassified redundant alias/control.
4. **Incremental evidence:** composite−BM25 paired deltas are small with
   bootstrap CIs including zero at most B (djangoCMS B=5 +0.003
   [−0.015,+0.019]; Saleor B=5 +0.003 [−0.017,+0.024]); signal predominantly
   lexical; Saleor graph arm ≈ binary-neighbor floor; history available only
   for djangoCMS (94 tasks).
5. **Budget freeze:** 560 calls / expected ~1,443,395 tokens / ~$0.50; hard
   ceilings 2,100,000 tokens / $1.00; per-call reservation rule derived from
   DEVELOPMENT p99 (sparse) and B=10-safe (verifier) only.

## 5. Proposal V1.4

- 7 pages, `pdflatex -halt-on-error` clean; V1.3 immutable; audit
  `PROPOSAL_V1_4_AUDIT.md`; changelog + claims matrix updated.

## 6. Tests / static checks

- Full suite: **3297 passed / 33 skipped / 2 failed** — the 2 failures are the
  pre-existing environmental failures (missing pinned djangocms repo checkout
  `benchmark_data/repositories/djangocms`; identical on clean base per
  00_CURRENT_RESEARCH_STATE.md). No test failure is related to this milestone.
- Ruff on new script: PASS. `py_compile`: PASS.
- Mypy strict on the new script inherits the same untyped-import pattern as the
  existing frozen `scripts/route_b_v2_robustness.py` / `saleor_route_b_transfer.py`
  (scripts are analysis tools, not production `src/`); no new production code.

## 7. Verdict

**PASS.** The V14 deliverables are internally consistent, zero-API, and
leakage-free; the frozen confirmatory method is unchanged; INTERNAL_TEST/RESERVE
are sealed. A DEV/pre-confirmatory freeze tag may be created.