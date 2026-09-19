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
**Task:** CONTAMINATION-ROBUSTNESS BRIDGE (2026-09-19; T3 DEVELOPMENT; scope
change from the paused Stage-5 preparation) — **STAGE 5 CONFIRMATORY EXECUTION
PAUSED — pending DEVELOPMENT-only contamination-robustness bridge.**
SweRankEmbed result (`SWERANK_EMBED_PASS`) immutable; sealed confirmatory
populations NOT opened; bridge STOPPED BEFORE CALL 1 (requested
`qwen/qwen3-embedding-8b` unavailable on OpenRouter — 0 embedding models in the
447-model catalog; documented; no paid call made).

---

## Now executing

- **MILESTONE COMPLETE (ZERO paid API, T3, scope change).** The Stage-5
  confirmatory freeze/preparation mission was superseded by an explicit user
  scope change: run a DEVELOPMENT-only contamination-robustness bridge
  (`qwen/qwen3-embedding-8b` through the OpenRouter embeddings interface) to
  test whether the SweRank DEV gain is a general dense-retrieval mechanism.
  **Preflight result: the exact model is NOT available on OpenRouter** (full
  447-model catalog contains zero embedding-capable models; 404 on all three
  Qwen3-Embedding identifiers). Per the frozen stop conditions, **NO scientific
  call was made** (0 calls, $0.00) and the bridge is frozen as
  **`QWEN3_EMBED_BRIDGE_TECHNICALLY_INCONCLUSIVE`**. Delivered: deepened
  SweRank provenance audit V2, budget freeze (NOT EXECUTED), frozen bridge
  protocol (NOT EXECUTED), mock-tested OpenRouter embeddings client, sealed-data
  guard, tests and independent audit. Stage 5 confirmatory remains **PAUSED and
  SEALED** (`STAGE5_REMAINS_BLOCKED_BY_PROVENANCE_OR_NONREPLICATION`); the
  recommended alternative control (local open-weight embedding model) is NOT
  executed without new authorization.
- **Remaining:** none for this mission. Next actions (each requires explicit
  authorization): (a) run the contamination bridge IF a Qwen3-Embedding model
  becomes available on OpenRouter or a substitute is authorized; (b) resume the
  Stage-5 confirmatory protocol after a scientifically justified bridge
  outcome.

## Last completed task

- Strong-localization-signal mission (2026-09-19, ZERO API): Stage-4b
  statistical closure + SweRankEmbed-Small DEV evaluation + competitor/
  readiness studies; scripts `stage4b_statistical_closure.py`,
  `swerank_dev_eval.py`, `swerank_write_report.py`,
  `swerank_independent_audit.py`; evidence under
  `research/strong-localization-signal/`.
- Contamination-robustness bridge preflight (2026-09-19, ZERO paid API): model
  availability verified absent on OpenRouter; bridge STOPPED BEFORE CALL 1 and
  frozen `QWEN3_EMBED_BRIDGE_TECHNICALLY_INCONCLUSIVE`; provenance audit V2 +
  budget freeze + frozen protocol + client + tests + independent audit; docs
  under `docs/QWEN3_EMBED_CONTAMINATION_*`, `reports/*_2026-09-19.md`,
  `reports/CONTAMINATION_ROBUSTNESS_BRIDGE_CLOSURE_2026-09-19.md`.

## Immediate next step

- Await review. Stage 5 confirmatory is PAUSED and sealed; the contamination
  bridge could not run (model unavailable on the required interface). Any
  bridge execution (with a substitute model) or Stage-5 confirmatory execution
  requires a NEW explicit authorization.

## Blockers

- **QWEN3 EMBEDDING BRIDGE BLOCKED (2026-09-19):** `qwen/qwen3-embedding-8b`
  is not offered by OpenRouter (0 embedding models in the catalog). No
  substitute was executed per the frozen stop conditions. Recommended
  alternative (NOT executed): a local open-weight dense embedding model under a
  new authorization.
- Semantic-proxy human audit remains **AWAITING_HUMAN_RATINGS** (human-work
  blocker; the AI-assisted track is descriptive only, not gold).
- Human minimal spot-check (119 rows) awaits a human reviewer.
- Pre-existing environmental (2 full-suite failures, identical on clean base):
  pinned djangocms git cache absent at benchmark_data/repositories/djangocms.
- **Saleor history blocker RESOLVED (2026-09-19):** the documented
  `dist/real-commit-cache/saleor` path is absent, but the full Saleor history
  (22,615 commits, anchor `2c48391b` == dataset anchor) IS available locally at
  `dist/pilot-repo-cache/saleor` — a parent-visible history cache can be built
  deterministically (see `reports/REPOSITORY_MEMORY_FEASIBILITY_2026-09-19.md`).
- Cross-language engineering gaps: no TS/Java/Go import extractors; no local
  caches for NestJS/JabRef/prometheus (readiness only; P1 deferred).

## Full-suite state (Contamination-robustness bridge, 2026-09-19)

- **Affected suites PASS**: prior signal suites (38 tests:
  test_signal_metrics 13, test_signal_adapter 13, test_signal_leakage 7,
  test_stage4b_closure 5) + new `test_or_embeddings.py` (client request
  formatting, no fallback, batching determinism, hashing, cost accounting,
  failure policy, sealed-data guard).
- Ruff clean; py_compile clean; `git diff --check` clean.
- Independent audit recomputes the availability finding, budget JSON, sealed
  set guard and protocol hygiene WITHOUT importing the analyzer
  (`reports/QWEN3_EMBED_INDEPENDENT_AUDIT.json`).

## Closure block (Strong-localization-signal, 2026-09-19)

- ZERO-API T3 DEVELOPMENT mission; branch
  `research/strong-localization-signal-2026-09-19` merged to `main` (merge
  commit `0c12223`).
- DEV-evidence tag `strong-localization-signal-2026-09-19` — peel == merge ==
  main-at-tag-time (audited DEVELOPMENT evidence; NOT a stable-tag move).
  Pushed to origin; post-tag docs commits `5326c3a`, `ba98854` advanced main.
- LIGHT export at scientific closure (filename/hash in the final stop report).
- Next scientific task (NOT started, requires its own authorization): freeze a
  confirmatory protocol for the embed method OR a budgeted SweRankLLM
  reranker experiment — now PAUSED pending the contamination-robustness bridge.

## Closure block (Contamination-robustness bridge, 2026-09-19)

- ZERO-paid-API T3 DEVELOPMENT scope change; branch
  `research/qwen3-embed-contamination-bridge-2026-09-19` merged to `main`
  (merge commit in the final stop report).
- DEV-evidence tag `qwen3-embed-contamination-bridge-2026-09-19` — peel ==
  merge == main (audited DEVELOPMENT evidence; NOT a stable-tag move). Pushed
  to origin; origin/main == HEAD == tag peel.
- LIGHT export at scientific closure (filename/hash in the final stop report).
- Next scientific task (NOT started, requires its own authorization): the
  contamination bridge with an available control model, then the Stage-5
  confirmatory decision.