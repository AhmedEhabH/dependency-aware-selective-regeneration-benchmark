# START HERE — Current Research (2026-09-19)

This file is the entry map. Read it first, then open the referenced documents.

## What this research is

**Question.** Given a real GitHub issue and the repository state at the issue's
parent commit, which files would a developer change? We evaluate the selected
file set against the observed change-set (the actual diff) as an evaluation
proxy. Functional correctness / preservation are deferred until downstream
regeneration.

**Phase.** `Repository change localization / impact selection`.

## Current position (one paragraph)

The dominant, measured bottleneck is **ranking** of omitted files (not
availability, not reviewer acceptance, not budget). Cheap structural rankers
and bounded generic-Qwen semantic layers each failed a frozen gate
(`CHEAP_RANKING_CLOSED_FOR_NOW`, `BOUNDED_SEMANTIC_NEGATIVE_FROZEN`,
`PRECISION_SAFE_ACCEPTANCE_FAIL`, `BOUNDED_CHEAP_SEMANTIC_CLOSED_FOR_NOW`). A
specialized pretrained issue-localization embedding
(`Salesforce/SweRankEmbed-Small`) improved every metric at every budget on both
DEVELOPMENT repositories with all paired-bootstrap CIs excluding zero at B=5
(**`SWERANK_EMBED_PASS`**) — but it is an **external pretrained diagnostic
baseline** (training-overlap cannot be ruled out, verdict C). An independent
Qwen3-Embedding control was authorized and probed, but the full run was
STOPPED on material embedding nondeterminism at the file-level margin
(**`QWEN3_EMBED_BRIDGE_TECHNICALLY_INCONCLUSIVE`**). Stage-5 confirmatory is
**PAUSED and SEALED**.

## Read order

| # | File | Why |
|---|---|---|
| 1 | `reports/HUMAN_READABLE_RESEARCH_STATUS_2026-09-19.md` | 30-second + 5-minute overview |
| 2 | `reports/CURRENT_NUMBERS_CHEATSHEET_2026-09-19.md` | the exact numbers |
| 3 | `reports/CURRENT_ORACLE_GAP_EXPLAINED_2026-09-19.md` | why the gap exists |
| 4 | `00_CURRENT_RESEARCH_STATE.md` | authoritative scientific truth (top CURRENT TRUTH blocks) |
| 5 | `DECISIONS.md` (P63–P73) | append-only decisions |
| 6 | `reports/CONTAMINATION_ROBUSTNESS_BRIDGE_CLOSURE_2026-09-19.md` | the Qwen bridge arc |
| 7 | `docs/RESEARCH_JOURNEY.md` | chronological history (negatives = search-space reductions) |

## Do NOT (hard boundaries)

- Do not open djangoCMS RESERVE, Saleor INTERNAL_TEST/RESERVE, or reuse the
  spent djangoCMS INTERNAL_TEST.
- Do not claim SweRank is clean unseen generalization (verdict C).
- Do not treat the Qwen bridge stop as a scientific negative.
- Do not call the embedding result final-set superiority (it is a
  ranking/recovery improvement).
- Do not run Stage 5 without explicit authorization.

## ONE next scientific action

With explicit authorization: run the contamination-robustness control with a
**determinism-controllable local** open-weight dense embedding model (e.g.,
`BAAI/bge-m3` local inference) under a new frozen protocol, then decide whether
Stage 5 is justified. Until a bridge outcome exists, Stage 5 stays sealed.