# WP-2 Smoke Selection V2 (2026-09-22)

Status: **SMOKE_V2_PROPOSAL_ONLY** — requires brain/Ahmed review before
execution. This supersedes the structural-only v1 proposal for Smoke selection
basing, using confirmed oracle evidence.

## Why V2 differs from V1

The V1 proposal (`research/wp2/wp2_smoke_candidate_proposal_2026-09-22.json`)
was a deterministic, outcome-blind structural proposal made before any
executable Oracle Confirmation. It is preserved and reviewed in
`docs/WP2_SMOKE_PROPOSAL_REVIEW_2026-09-22.md`.

V2 replaces the selection basis with **confirmed evaluator-valid F2P tasks**
from the Oracle Confirmation (8 primary behavioral + 1 symbol-absence eligible),
because a Smoke run must exercise the full F2P/P2P chain on tasks whose tests
actually fail-on-parent and pass-on-target.

## Selection hierarchy (deterministic, outcome-blind with respect to selectors)

1. Prefer `PRIMARY_BEHAVIORAL_F2P_ELIGIBLE`.
2. Include at least one SMALL, one MEDIUM, one larger task (if executable), one
   migration/config-heavy task (if environment-valid).
3. Include one `SYMBOL_ABSENCE_F2P` as an explicit secondary-oracle stress case,
   labelled as such.
4. Do not include P2P-only as a core F2P Smoke task.
5. Tie-break deterministically with fixed salt
   (`wp2-smoke-v2-2026-09-22`).
6. Never use RM-CSS / Agent / generation performance.

## Proposed 8-task Smoke set

| Task | Oracle class | Size | Notes |
|---|---|---|---|
| saleor-rc-30fe250747ae | BEHAVIORAL_F2P | SMALL | 1 behavioral node |
| saleor-rc-c6220233ccb1 | BEHAVIORAL_F2P | SMALL | 2 behavioral nodes |
| saleor-rc-9057e82cea23 | BEHAVIORAL_F2P | SMALL | 4 behavioral nodes |
| saleor-rc-2a59d31fc839 | BEHAVIORAL_F2P | MEDIUM | — |
| saleor-rc-305415e0f8b7 | BEHAVIORAL_F2P | MEDIUM / migration-heavy | environment stress |
| saleor-rc-a7a2bf4146ba | BEHAVIORAL_F2P | SMALL | 176 P2P nodes (preservation) |
| saleor-rc-05bdc7feb9ac | BEHAVIORAL_F2P | larger | 9 behavioral + 6 symbol nodes |
| saleor-rc-c7207e71e0d3 | SYMBOL_ABSENCE_F2P | MEDIUM | secondary-oracle stress case |

Coverage: 4 SMALL, 3 MEDIUM (incl. migration-heavy), 1 larger; 1 explicit
symbol-absence stress case; no P2P-only core task.

## Guardrails

- The final Smoke sample is frozen only after brain/Ahmed review.
- Smoke must be a small engineering feasibility run (full F2P/P2P chain on the
  confirmed oracles), not a scientific sample.
- No post-outcome tuning of Smoke tasks after results are observed.