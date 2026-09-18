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
**Task:** PRECISION-SAFE ACCEPTANCE FEASIBILITY + PROTOCOL FREEZE (2026-09-18;
T3 DEVELOPMENT; ZERO API) — post-Stage-4 failure anatomy of the frozen 300-call
record (13 analyses) → POST-HOC feasibility (RANK → VERIFY → VARIABLE ACCEPT;
family justified, specific frozen verifier not) → exactly ONE frozen next
protocol + budget draft + audit/tests/docs — **COMPLETE**

---

## Now executing

- **MILESTONE COMPLETE (ZERO API).** Precision-safe acceptance feasibility
  (post-Stage-4, DEVELOPMENT, 2026-09-18): frozen Stage-4 negative verified
  unchanged (300 calls / 106,325 tokens / $0.0444 / 553.6 s; ORR@5 recomputed
  dc 0.1111/0.2500, saleor 0.3344/0.3574 == frozen). 13-item failure anatomy:
  Arm-B FP tail is an acceptance-layer failure split across BOTH pool sources
  (dc 68/51, saleor 71/48); cap C=40 loses 10+29 FNs; 6/6 schema-invalid =
  non-pool-path + partial credit; B=10 5/5 folds both repos (motivation only).
  POST-HOC feasibility (one principled family): AND-rule precision dc
  0.105→0.146 / saleor 0.179→0.222 but F1 does NOT beat frozen Route-B verifier
  (dc 0.407 vs 0.414; saleor 0.263 vs 0.287) — frozen verifier uncalibrated
  (8.6–14% approval precision); consumer-only candidates never verifier-seen
  (explicit insufficiency). Verdict: family justified, specific verifier not.
  Exactly ONE frozen next protocol (RANK → VERIFY → VARIABLE ACCEPT, cap 80,
  K=10, strict boolean-vector verifier, 0..K accepted, fresh sample seed
  20260919, gate c1–c7 both repos) + budget draft (expected ~360 calls / ~$0.055;
  ceilings 400 / 300k tok / $0.15 / 60 min) — **NOT EXECUTED**.
- **Remaining:** none for this mission. Execution of the frozen pilot requires
  the exact authorization sentence (budget draft §7). Stage 5 (confirmatory)
  stays gated on a successful DEVELOPMENT pilot.

## Last completed task

- Precision-safe acceptance feasibility (2026-09-18): failure anatomy +
  feasibility + exactly one frozen protocol + budget freeze draft + independent
  audit (11/11) + 13/13 new tests + docs synchronized. Scripts
  `scripts/precision_safe_feasibility_{anatomy,audit}.py`; metrics under
  `reports/precision_safe_feasibility_metrics.json`.

## Immediate next step

- Await review. If the user authorizes (exact sentence, budget draft §7), the
  frozen precision-safe DEVELOPMENT pilot is ready to execute. If rejected, the
  feasibility conclusion is frozen as development evidence.

## Blockers

- No API authorization exists for the frozen precision-safe pilot (by design;
  ZERO API mandate).
- Semantic-proxy human audit remains **AWAITING_HUMAN_RATINGS** (human-work
  blocker; the AI-assisted track is descriptive only, not gold).
- Human minimal spot-check (119 rows) awaits a human reviewer.
- Pre-existing environmental (2 full-suite failures, identical on clean base):
  pinned djangocms git cache absent at benchmark_data/repositories/djangocms.
- Saleor parent-visible history cache absent (dist/real-commit-cache/saleor) —
  no Saleor co-change arm; recorded UNAVAILABLE in the taxonomy/ceilings.

## Full-suite state (Precision-safe acceptance feasibility gate, 2026-09-18)

- **Affected suites PASS** (`test_precision_safe_feasibility.py` 13/13 +
  previously green Stage-4 suites `test_recall_bottleneck.py` 19/19 +
  `test_quant_ranking_bridge.py` 12/12).
- Ruff clean; py_compile clean; `git diff --check` clean.
- Independent audit recomputes headline numbers from raw records without
  importing the analyzer — **11/11 PASS**
  (`reports/precision_safe_feasibility_audit.json`); macro ORR matches frozen
  Stage-4 metrics at every B.

## Closure block (Precision-safe acceptance feasibility + protocol freeze, 2026-09-18)

- ZERO-API DEVELOPMENT analysis; Stage-4 artifacts untouched
  (`BOUNDED_SEMANTIC_NEGATIVE_FROZEN` + P65 immutable).
- Branch `research/precision-safe-acceptance-feasibility-2026-09-18` merged to
  `main` (merge commit in the final stop report).
- DEV-evidence tag `precision-safe-acceptance-feasibility-2026-09-18` — peel ==
  merge == `main` (audited DEVELOPMENT evidence; NOT a stable-tag move). Pushed
  to origin; origin/main == HEAD == tag peel.
- LIGHT export at scientific closure (filename/hash in the final stop report).
- Next scientific task (NOT started, requires explicit authorization): the
  frozen precision-safe DEVELOPMENT pilot.