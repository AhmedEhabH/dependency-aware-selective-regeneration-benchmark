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
**Task:** STRONG LOCALIZATION SIGNAL BRIDGE (2026-09-19; T3 DEVELOPMENT; ZERO API) —
Stage-4b statistical closure + `BOUNDED_CHEAP_SEMANTIC_CLOSED_FOR_NOW` +
SweRankEmbed-Small DEV evaluation (**SWERANK_EMBED_PASS**, external pretrained
diagnostic baseline) + competitor review + repository-memory/cross-language/
polyglot readiness — **COMPLETE**

---

## Now executing

- **MILESTONE COMPLETE (ZERO API, T3).** Strong-localization-signal mission
  (2026-09-19): (1) **Stage-4b statistical closure** — POST-HOC descriptive
  uncertainty analysis with task-paired bootstrap (10,000 resamples, seed
  20260919, task unit) at B=5; frozen point estimates reproduce EXACTLY;
  djangoCMS ORR-down/F1-up phenomenon explained (macro-vs-pooled weighting +
  conservative verifier over-rejecting three M=1 recoveries); **frozen verdict
  `PRECISION_SAFE_ACCEPTANCE_FAIL` unchanged**. (2) **`BOUNDED_CHEAP_SEMANTIC_
  CLOSED_FOR_NOW`** recorded (generic-Qwen prompt/verifier/threshold family
  closed on the tested bounded semantic evidence). (3) **SweRankEmbed-Small
  DEV evaluation on the FULL legal populations (djangocms 174 + saleor 149)**:
  pinned revision `745d2a06…`, frozen MAX-file adapter, parent-only queries,
  Route-B-matched; **SWERANK_EMBED_PASS** — every metric improves at every B on
  both repos; all paired-bootstrap CIs @B=5 exclude zero (F1 +0.054 dc / +0.052
  saleor vs frozen Route-B); **0 API calls / $0**; labeled EXTERNAL PRETRAINED
  DIAGNOSTIC BASELINE (provenance verdict C). Method frozen as the
  candidate-ranking signal; next step A (embed replacement) selected, option B
  (SweRankLLM reranker) budget-planned not executed. (4) Competitor review
  (SweRank/SweRank+/LocAgent/RepoGraph/OrcaLoca/CoSIL/Agentless/repo-memory),
  repository-memory feasibility (Saleor history blocker RESOLVED:
  `dist/pilot-repo-cache/saleor` has the full 22,615-commit history, anchor
  matches the dataset), cross-language readiness (TS/Java/Go) + grafana
  polyglot feasibility frozen criteria. (5) Independent audit 11/11; 36 new
  unit tests PASS; ruff/py_compile/git diff --check clean.
- **Remaining:** none for this mission. Next scientific action: the frozen
  embed method is the candidate-ranking signal; a confirmatory protocol (Stage
  5) or a budgeted SweRankLLM reranker (option B) each require a new freeze +
  explicit authorization.

## Last completed task

- Strong-localization-signal mission (2026-09-19, ZERO API): Stage-4b
  statistical closure + SweRankEmbed-Small DEV evaluation + competitor/
  readiness studies; scripts
  `stage4b_statistical_closure.py`,
  `swerank_dev_eval.py`, `swerank_write_report.py`,
  `swerank_independent_audit.py`; evidence under
  `research/strong-localization-signal/`.

## Immediate next step

- Await review. The embed method is frozen as a candidate-ranking signal
  (diagnostic). Any confirmatory run or reranker experiment requires a NEW
  frozen protocol + explicit authorization.

## Blockers

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
  caches for NestJS/JabRef/prometheus (readiness only).

## Full-suite state (Strong-localization-signal mission, 2026-09-19)

- **Affected suites PASS**: new `test_signal_metrics.py` (13),
  `test_signal_adapter.py` (13), `test_signal_leakage.py` (7),
  `test_stage4b_closure.py` (5) = 38 new tests + prior affected suites
  (test_precision_safe_acceptance, test_recall_bottleneck,
  test_quant_ranking_bridge).
- Ruff clean; py_compile clean; `git diff --check` clean.
- Independent audit recomputes formulas, macro ORR, gate A–E, folds, bootstrap
  CIs, leakage, pin, efficiency from raw JSONs without importing the analyzer:
  **11/11 PASS** (`reports/swerank_independent_audit.json`).

## Closure block (Strong-localization-signal, 2026-09-19)

- ZERO-API T3 DEVELOPMENT mission; branch
  `research/strong-localization-signal-2026-09-19` merged to `main` (merge
  commit in the final stop report).
- DEV-evidence tag `strong-localization-signal-2026-09-19` — peel == merge ==
  `main` (audited DEVELOPMENT evidence; NOT a stable-tag move). Pushed to
  origin; origin/main == HEAD == tag peel.
- LIGHT export at scientific closure (filename/hash in the final stop report).
- Next scientific task (NOT started, requires its own authorization): freeze a
  confirmatory protocol for the embed method OR a budgeted SweRankLLM
  reranker experiment.