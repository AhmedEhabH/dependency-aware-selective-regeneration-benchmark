# START HERE - Current Research (2026-09-20)

This file is the entry map. Read it first, then open the referenced documents.

## What this research is

**Question.** Given a real GitHub issue and the repository state at the issue's
parent commit, which files would a developer change? We evaluate the selected
file set against the observed change-set (the actual diff) as an evaluation
proxy. Functional correctness / preservation are deferred until downstream
regeneration.

**Phase.** `Repository change localization / impact selection`.

## Current position (one paragraph)

The dominant, measured bottleneck is **ranking** of omitted files. Cheap
structural and generic-semantic rankers failed frozen gates; the specialized
SweRankEmbed signal passed on DEV (`SWERANK_EMBED_PASS`, external pretrained
diagnostic, verdict C) and was independently reproduced by Qwen3-Embedding-8B
(`INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`), but the final-set decision policy
is NOT frozen (V1/V2 both negative on djangoCMS). The latest test asked
whether a **real pre-change GitHub issue description** fixes the information
bottleneck: under the strict temporal rule the clean paired population is only
**djangocms 12 / saleor 0**, and on those 12 tasks issue text does NOT
materially improve the dense signal (Recall@20 0.6875->0.7188 but paired CI
crosses zero; median rank worsens) -> **`ISSUE_GROUNDED_INTENT_SIGNAL_NOT_SUPPORTED`**
(frozen negative). Stage-5 confirmatory is **PAUSED and SEALED**.

## Read order

| # | File | Why |
|---|---|---|
| 1 | `reports/ISSUE_GROUNDED_INTENT_HEADROOM_2026-09-20.md` | the latest mission (12 plain-language answers) |
| 2 | `reports/LOCALIZATION_COMPARABILITY_MAP_2026-09-20.md` | why headline Acc@k/F1 numbers are not comparable |
| 3 | `00_CURRENT_RESEARCH_STATE.md` | authoritative scientific truth (top CURRENT TRUTH blocks) |
| 4 | `reports/HUMAN_READABLE_RESEARCH_STATUS_2026-09-19.md` | 30-second + 5-minute overview |
| 5 | `reports/CURRENT_NUMBERS_CHEATSHEET_2026-09-19.md` | the exact numbers |
| 6 | `DECISIONS.md` (P82/P83) | the issues-headroom governance + result |
| 7 | `docs/RESEARCH_JOURNEY.md` | chronological history (negatives = search-space reductions) |

## Do NOT (hard boundaries)

- Do not open djangoCMS RESERVE, Saleor INTERNAL_TEST/RESERVE, or reuse the
  spent djangoCMS INTERNAL_TEST.
- Do not claim SweRank is clean unseen generalization (verdict C).
- Do not treat the Qwen bridge stop as a scientific negative.
- Do not call the embedding result final-set superiority (it is a
  ranking/recovery improvement).
- Do not interpret `ISSUE_GROUNDED_INTENT_SIGNAL_NOT_SUPPORTED` as "issues are
  useless" - it means the strict-temporal clean population is near-empty and
  no improvement was demonstrated on it. Do not rerun V1/V2 with issue text.
- Do not run Stage 5 without explicit authorization.

## ONE next scientific action

With explicit authorization: decide the deliberate temporal rule and
pre-register a larger clean issue-grounded corpus if issue-based intent is to
be re-tested; otherwise continue the frozen gap-reduction ladder. Until a
frozen successful final policy exists, Stage 5 stays sealed.