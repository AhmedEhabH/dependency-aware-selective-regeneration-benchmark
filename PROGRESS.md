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
**Task:** PRECISION-SAFE ACCEPTANCE PILOT (2026-09-18; T3 DEVELOPMENT; AUTHORIZED
real run) — frozen RANK→VERIFY→VARIABLE-ACCEPT pilot executed (357 calls,
$0.0648) → preregistered gate FAIL (djangoCMS c1 ORR −0.0702, c2 folds 2/5;
Saleor c1 +0.0751) → **PRECISION_SAFE_ACCEPTANCE_FAIL** (negative frozen; no
tuning) → audit/tests/docs — **COMPLETE**

---

## Now executing

- **MILESTONE COMPLETE (AUTHORIZED PILOT).** Precision-safe acceptance pilot
  (Stage 4b, DEVELOPMENT, AUTHORIZED 2026-09-18): registration frozen BEFORE
  call 1 (60 fresh DEV tasks, seed 20260919, Stage-4's 60 case_ids excluded;
  pool cap 80; K=10; candidate-ID enum rank schema; fixed-length boolean
  verify schema). **Real run: 357 dispatched calls (240 Arm A + 60 rank + 57
  verify; 3 rank abstentions), 176,060 tokens, $0.0648, 655.7 s — all ceilings
  respected; 0/357 schema-invalid (vs Stage-4 6/60); resume 357 no double
  spend**. **Preregistered gate = FAIL → PRECISION_SAFE_ACCEPTANCE_FAIL**:
  djangoCMS ORR fell materially (−0.0702; 2/5 folds) — the conservative
  verifier over-rejects the easy M=1 recoveries; Saleor ORR materially up
  (+0.0751; 5/5 folds); F1 and candidate precision improve on BOTH repos (the
  Stage-4 "ORR up, F1 down" failure is eliminated). No prompt/schema tuning.
  Independent audit 11/11 PASS; affected suites 53/53.
- **Remaining:** none for this mission. Stage 4b closed NEGATIVE; Stage 5
  (freeze method + fresh confirmatory) NOT reached. Any future instrument that
  keeps the precision/F1 gains while restoring djangoCMS ORR requires a new
  freeze + explicit authorization.

## Last completed task

- Precision-safe acceptance pilot (2026-09-18): frozen registration + 357 real
  calls + metrics/gate/audit + closure report; scripts
  `precision_safe_acceptance_{pilot,analyze,audit}.py`; raw evidence under
  `research/precision-safe-acceptance-pilot/`.

## Immediate next step

- Await review. The negative is frozen; no further API spend without a new
  protocol + explicit authorization. If the user wants to pursue the
  precision/F1 gains while restoring djangoCMS ORR, a NEW protocol (e.g., a
  calibrated acceptance criterion) must be pre-registered and authorized.

## Blockers

- Semantic-proxy human audit remains **AWAITING_HUMAN_RATINGS** (human-work
  blocker; the AI-assisted track is descriptive only, not gold).
- Human minimal spot-check (119 rows) awaits a human reviewer.
- Pre-existing environmental (2 full-suite failures, identical on clean base):
  pinned djangocms git cache absent at benchmark_data/repositories/djangocms.
- Saleor parent-visible history cache absent (dist/real-commit-cache/saleor) —
  no Saleor co-change arm; recorded UNAVAILABLE in the taxonomy/ceilings.

## Full-suite state (Precision-safe acceptance pilot gate, 2026-09-18)

- **Affected suites PASS** (`test_precision_safe_acceptance.py` 9/9 +
  `test_precision_safe_feasibility.py` 13/13 + `test_recall_bottleneck.py`
  19/19 + `test_quant_ranking_bridge.py` 12/12 = 53/53).
- Ruff clean; py_compile clean; `git diff --check` clean.
- Independent audit recomputes ORR@5, gate decision, schema rate, zero partial
  credit, sealed+disjoint sample, and prompt determinism from raw records
  without importing the analyzer — **11/11 PASS**
  (`reports/precision_safe_acceptance_audit.json`).
- Budget ledger verified: 357 dispatched calls, 176,060 tokens, $0.0648,
  718.8 s total wall (655.7 s execution + resume reloads), sidecars 357/357
  with 0 hash mismatches.

## Closure block (Precision-safe acceptance pilot, 2026-09-18)

- AUTHORIZED real DEVELOPMENT pilot; `research/precision-safe-acceptance-pilot/`
  raw evidence + reports. Branch
  `research/precision-safe-acceptance-pilot-2026-09-18` merged to `main`
  (merge commit in the final stop report).
- DEV-evidence tag `precision-safe-acceptance-pilot-2026-09-18` — peel ==
  merge == `main` (audited DEVELOPMENT evidence; NOT a stable-tag move). Pushed
  to origin; origin/main == HEAD == tag peel.
- LIGHT export at scientific closure (filename/hash in the final stop report).
- Next scientific task (NOT started, requires its own authorization): any new
  precision-safe instrument with a calibrated acceptance criterion, gated on
  BOTH repositories.