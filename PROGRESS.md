# PROGRESS.md — Execution Source of Truth

**Role:** Execution source of truth (what is being executed now, last completed
task, immediate next step, blockers). Scientific truth lives in
`00_CURRENT_RESEARCH_STATE.md`; decisions are recorded append-only in
`DECISIONS.md`.

**Branch:** `research/overnight-routeb-v2-saleor-2026-09-17` (overnight mission; to be merged into `main`)
**HEAD base:** `7dbd028` (main, evening mission closed + DEV tag)
**Model:** openrouter/deepseek/deepseek-v4-flash-0731
**Task:** CONTINUATION MISSION (2026-09-17) — Saleor portability fix + 150/150
bundles; Saleor sparse inference (budget-blocked); Route-B confirmatory-freeze
packet; P2 prereg; semantic audit machine-prep.

---

## Now executing

- **ALL CONTINUATION BLOCKS COMPLETE (or blocked-documented).** A: state
  verified. B: Saleor production-only materializer — equivalence 98/98 PASS,
  150/150 DEV bundles built, canonical hashes identical (ZERO model calls).
  C: Saleor sparse inference **FAIL-CLOSED on budget** (1/450 smoke $0.0047;
  450-cell projects 2.4-2.7x ceiling) — full run NOT run; no silent protocol
  change. D: Saleor Route-B replication BLOCKED (requires C). E: djangoCMS
  Route-B confirmatory-freeze packet (ready-to-approve, INTERNAL_TEST sealed,
  choice B). F: P2 adaptive-budget pre-registration (conditional). G: semantic
  audit machine-prep finished (integrity, kappa tests, synthetic dry-run).
  H: Proposal V1.3 stays print candidate (V1.4 NOT created).
- **Remaining:** traceability commit, full tests, merge main, DEV tag, LIGHT
  export, final report.

## Last completed task

- Block G (semantic audit machine-prep) + H (proposal decision).

## Immediate next step

- Traceability (Block I) commit → full suite → merge + DEV tag + LIGHT export
  → final report.

## Blockers

- Pre-existing environmental: pinned djangocms git cache absent
  (benchmark_data/repositories/djangocms) — parent-commit corpus not
  re-materializable; documented in the repository evidence audit.