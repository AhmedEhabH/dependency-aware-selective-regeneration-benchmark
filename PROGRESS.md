# PROGRESS.md — Execution Source of Truth

**Role:** Execution source of truth (what is being executed now, last completed
task, immediate next step, blockers). Scientific truth lives in
`00_CURRENT_RESEARCH_STATE.md`; decisions are recorded append-only in
`DECISIONS.md`.

**Branch:** `main` (continuation mission work committed directly)
**HEAD base:** `f7c6fa1` (S7 traceability commit, Saleor transfer REPLICATES)
**Model:** openrouter/deepseek/deepseek-v4-flash-0731
**Task:** PRE-CONFIRMATORY HARDENING V14 — ranker-identity audit + incremental
ablation + confirmatory freeze packet V2 + API budget freeze + Proposal V1.4
(2026-09-17)

---

## Now executing

- **ALL BLOCKS COMPLETE (ZERO API).** A. Ranker-identity audit: the frozen arm
  historically labelled `Classical-CIA` is exactly `normalized BM25 + binary
  graph-neighbor`; CIA and Hybrid are mathematically rank-equivalent (Hybrid =
  0.5 × CIA key), confirmed at top-B identity on 174 djangoCMS + 149 Saleor
  DEVELOPMENT tasks (0 differing cells, full-rank identical). Hybrid classified
  a redundant alias/control. B. Incremental-evidence ablation: cross-repo signal
  predominantly lexical (BM25); composite−BM25 paired deltas small with CIs
  including zero at most B; Saleor graph arm ≈ binary-neighbor floor.
  C. Confirmatory freeze packet V2 (supersedes V1; truthful ranker name,
  redundancy, Saleor=REPLICATES, exact repetition/failure/verifier semantics).
  D. Confirmatory API budget freeze (560 calls / ≤2,100,000 tokens / ≤$1.00;
  per-call reservation rule). E. Proposal V1.4 (.tex/.pdf 7 pages + audit),
  V1.3 immutable.
- **Remaining:** traceability commit, full test suite, merge/tag/light export,
  final report.

## Last completed task

- E: Proposal V1.4 created (Saleor DEV transfer replication + ranker identity
  correction + lexical-dominance statement) + audit; changelog + claims matrix
  updated.

## Immediate next step

- Traceability (DECISIONS/PROGRESS/state/roadmap/ledgers) -> full suite ->
  branch/commit/push/merge/tag/LIGHT export -> final report.

## Blockers

- Pre-existing environmental: pinned djangocms git cache absent
  (benchmark_data/repositories/djangocms) — parent-commit corpus not
  re-materializable; documented in the repository evidence audit.
- Saleor parent-visible history cache absent (dist/real-commit-cache/saleor) —
  no Saleor co-change arm; recorded UNAVAILABLE in the ablation.