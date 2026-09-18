# PROGRESS.md — Execution Source of Truth

**Role:** Execution source of truth (what is being executed now, last completed
task, immediate next step, blockers). Scientific truth lives in
`00_CURRENT_RESEARCH_STATE.md`; decisions are recorded append-only in
`DECISIONS.md`.

**Branch:** `main`
**Scientific closure commit:** `8b2d1b6` (merge of
`research/oracle-gap-bidirectional-repair-2026-09-18`; immutable scientific
fact)
**Scientific closure tag peel:** `8b2d1b6` (tag
`oracle-gap-bidirectional-repair-2026-09-18`; immutable scientific fact)
**Live HEAD / origin/main:** runtime git facts — a tracked file cannot embed
its own final live HEAD SHA (committing metadata changes HEAD again). Query
at read time: `git rev-parse HEAD`, `git rev-parse origin/main`,
`git status --porcelain`.
**Model:** openrouter/deepseek/deepseek-v4-flash-0731
**Task:** RANKING BRIDGE + BOUNDED SEMANTIC FREEZE (2026-09-18; T3 DEVELOPMENT;
ZERO API) — Section-1 ranking-gap reconfirmation freeze EXACT →
Section-2 three transparent quantitative-structural rankers
(R1/R2/R3, no formula material on both repos) → **CHEAP_RANKING_CLOSED_FOR_NOW**
(negative frozen) → bounded semantic rerank/verify protocol + API budget
PREPARED NOT EXECUTED → P2/adaptive-k gated → cross-language vs polyglot
correction + Grafana FUTURE candidate → gap-reduction roadmap ladder —
**COMPLETE**

---

## Now executing

- **MILESTONE COMPLETE.** Ranking bridge + bounded semantic freeze (DEVELOPMENT
  only, T3, ZERO API): Section-1 reconfirmation reproduced the frozen ranking
  gap EXACTLY (Route-B 0.0464/0.1177/0.1633/0.2512 and 0.0775/0.1576/0.2369/
  0.3173; reverse-1hop 0.558/0.724; UNION_ALL 0.725/0.870; Oracle-Add
  0.841/0.782; oracle-reviewer 0.441/0.424 — all verification flags PASS).
  Section-2 ran exactly three transparent quantitative-structural rankers
  (R1 BM25+RevSupport, R2 BM25+BidirSupport, R3 BM25+BidirNorm) over the
  high-coverage reverse-1hop pool at matched budget: best is R1 with
  djangoCMS +0.034 but Saleor −0.020 at B=5; **NO formula materially beats
  Route-B on BOTH repos** (c1/c2 fail on all three) →
  **CHEAP_RANKING_CLOSED_FOR_NOW** (negative frozen; no fourth formula).
  The bounded semantic rerank/verify protocol
  (`docs/BOUNDED_SEMANTIC_RERANK_VERIFY_PROTOCOL_FROZEN.md`) + API budget
  draft (`reports/BOUNDED_SEMANTIC_EXPANSION_BUDGET_FREEZE_DRAFT.md`) were
  PREPARED but NOT EXECUTED (≤300 calls / ≤300k tokens / ≤$0.30 / ≤60 min
  hard stop). P2/adaptive-k status gated (not active). Future-work
  terminology corrected to cross-language + polyglot-repository
  generalization; `grafana/grafana` added as FUTURE feasibility candidate
  only. Gap-reduction roadmap ladder documented (Stages 1–8).
- **Remaining:** none for this mission. The Stage-4 bounded semantic pilot
  requires explicit user authorization (exact sentence in the budget draft).

## Last completed task

- Ranking bridge + bounded semantic freeze (2026-09-18): Section-1 baseline
  freeze artifact + Section-2 three-formula bridge + gate
  `CHEAP_RANKING_CLOSED_FOR_NOW`; `src/benchmark/recall/quant_rankers.py`,
  `scripts/fn_quant_ranking_bridge.py`, `scripts/fn_quant_ranking_bridge_audit.py`,
  `tests/unit/test_quant_ranking_bridge.py` (12/12), independent audit
  (25/25 PASS); docs updated.

## Immediate next step

- Await review/authorization. If the user authorizes the frozen Stage-4
  protocol + budget, run the bounded semantic rerank/verify DEVELOPMENT pilot
  (≤300 calls / ≤300k tokens / ≤$0.30 / ≤60 min); otherwise the cheap-ranking
  negative and the frozen protocol/budget are the mission's deliverable.

## Blockers

- Semantic-proxy human audit remains **AWAITING_HUMAN_RATINGS** (human-work
  blocker; the AI-assisted track is descriptive only, not gold).
- Human minimal spot-check (119 rows) awaits a human reviewer.
- Pre-existing environmental (2 full-suite failures, identical on clean base):
  pinned djangocms git cache absent at benchmark_data/repositories/djangocms.
- Saleor parent-visible history cache absent (dist/real-commit-cache/saleor) —
  no Saleor co-change arm; recorded UNAVAILABLE in the taxonomy/ceilings.

## Full-suite state (Ranking bridge mission gate, 2026-09-18)

- **12/12 new unit tests PASS** (`tests/unit/test_quant_ranking_bridge.py`);
  affected suites green (`test_recall_bottleneck.py` 19/19 +
  `test_oracle_gap.py` 16/16 = 35/35).
- Ruff clean on all changed Python; mypy strict clean on
  `src/benchmark/recall`; py_compile clean; `git diff --check` clean.
- Independent audit recomputes the headline numbers from frozen records
  without importing the analysis scripts — **25/25 checks PASS**
  (`reports/fn_quant_ranking_bridge_audit.json`).

## Closure block (Ranking bridge + bounded semantic freeze mission, 2026-09-18)

- Branch: `research/ranking-bridge-bounded-semantic-freeze-2026-09-18` → merged
  to `main` as merge commit `2744f6f` (immutable scientific fact).
- DEV-evidence tag `ranking-bridge-bounded-semantic-freeze-2026-09-18` — peel
  `2744f6f` == merge == `main` (audited DEVELOPMENT evidence; NOT a
  stable-tag move). Pushed to origin; origin/main == HEAD == tag peel.
- Live HEAD / origin/main are runtime git facts (query with `git rev-parse`).
- LIGHT export (at scientific closure): `project-2026-09-18-1923.zip`
  SHA-256 `7cf1f5594f006543d934e29dbf4a4a89980cfc8f489af9dbbe4dfb0d5195891d`
  (95,607,842 bytes; required members `.git/HEAD`,
  `dist/pilot-kaggle-upload.zip`, `.sha256` present; 9,101 entries).
- Next scientific task (NOT started, requires its own authorization): bounded
  semantic rerank/verify pilot on DEVELOPMENT (Route-B top-B + reverse-1hop
  consumer pool), using the frozen protocol + budget draft.