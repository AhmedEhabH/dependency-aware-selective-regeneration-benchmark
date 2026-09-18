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

- **MILESTONE COMPLETE (AUTHORIZED PILOT).** Bounded semantic expansion pilot
  (Stage 4, DEVELOPMENT, AUTHORIZED 2026-09-18): frozen registration written
  BEFORE call 1 (60 tasks: 30 djangoCMS + 30 Saleor; pool = Route-B top-10 ∪
  reverse-1hop consumers, cap 40); **real run: 300 calls (Arm A 240 + Arm B 60),
  106,325 tokens, $0.0444, 553.6 s — all ceilings respected**. Arm A = frozen
  Route-B verifier (4 calls/task); Arm B = expanded-pool bounded semantic
  rerank/verify (1 call/task). **Preregistered gate = FAIL →
  BOUNDED_SEMANTIC_NEGATIVE_FROZEN**: Arm B raises ORR on djangoCMS (+0.139 at
  B=5) but NOT materially on Saleor (+0.023), and on djangoCMS naive final F1
  falls materially (−0.069) — exactly the "ORR up but F1 down" failure the
  protocol forbids claiming as success. No prompt/schema tuning. 6 Arm B
  schema-invalid calls recorded fail-closed (no retries). Independent audit
  8/8 PASS; affected suites 31/31.
- **Remaining:** none for this mission. Stage 4 is closed NEGATIVE; the
  gap-reduction ladder's Stage 5 (freeze method + fresh confirmatory) is NOT
  reached. Any future semantic instrument needs a precision-safe acceptance
  rule and its own explicit authorization.

## Last completed task

- Bounded semantic expansion pilot (2026-09-18): frozen registration +
  300 real calls + metrics/gate/audit + closure report; scripts
  `bounded_semantic_expansion_{pilot,analyze,audit}.py`; raw evidence under
  `research/bounded-semantic-expansion/`.

## Immediate next step

- Await review. Freeze the negative; no further API spend. If the user later
  wants a different bounded semantic protocol, it must be pre-registered
  (precision-safe acceptance) and explicitly authorized with its own budget.

## Blockers

- Semantic-proxy human audit remains **AWAITING_HUMAN_RATINGS** (human-work
  blocker; the AI-assisted track is descriptive only, not gold).
- Human minimal spot-check (119 rows) awaits a human reviewer.
- Pre-existing environmental (2 full-suite failures, identical on clean base):
  pinned djangocms git cache absent at benchmark_data/repositories/djangocms.
- Saleor parent-visible history cache absent (dist/real-commit-cache/saleor) —
  no Saleor co-change arm; recorded UNAVAILABLE in the taxonomy/ceilings.

## Full-suite state (Bounded semantic expansion pilot gate, 2026-09-18)

- **Affected suites PASS** (`test_recall_bottleneck.py` 19/19 +
  `test_quant_ranking_bridge.py` 12/12 = 31/31).
- Ruff clean; py_compile clean; `git diff --check` clean.
- Independent audit recomputes headline metrics from raw per-run records
  without importing the analyzer — **8/8 checks PASS**
  (`reports/bounded_semantic_expansion_audit.json`).
- Budget ledger verified: 300/300 calls, 106,325 tokens, $0.0444, 553.6 s,
  sidecars 300/300 with 0 hash mismatches.

## Closure block (Bounded semantic expansion pilot, 2026-09-18)

- AUTHORIZED real DEVELOPMENT pilot; `research/bounded-semantic-expansion/`
  raw evidence + reports. Branch `research/bounded-semantic-expansion-pilot-2026-09-18`
  merged to `main` as merge commit `09979c7` (immutable scientific fact).
- DEV-evidence tag `bounded-semantic-expansion-pilot-2026-09-18` — peel
  `09979c7` == merge == `main` (audited DEVELOPMENT evidence; NOT a stable-tag
  move). Pushed to origin; origin/main == HEAD == tag peel.
- LIGHT export at scientific closure (filename/hash in the final stop report).
- Next scientific task (NOT started, requires its own authorization): any
  future bounded semantic instrument with a precision-safe acceptance rule.