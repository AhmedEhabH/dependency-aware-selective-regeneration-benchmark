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
**Task:** FIRST-PASS RECALL BOTTLENECK (2026-09-18; T3 DEVELOPMENT; ZERO API) —
FN taxonomy → S006-like pattern test → source-specific recall ceilings →
complementarity → ≤3 ADD queues → matched-budget eval → oracle-reviewer
simulation → progression gate = **RECALL_SIGNAL_HEADROOM_ONLY**; sealed sets
untouched; 19/19 tests + independent audit PASS — **COMPLETE**

---

## Now executing

- **MILESTONE COMPLETE.** First-pass recall bottleneck study (DEVELOPMENT
  only, T3, ZERO API): baseline freeze reproduced the frozen Route-B numbers
  exactly; FN taxonomy (deterministic, parent-visible) per repo; S006-like
  indirect-utility/downstream misses = **GENERAL_PATTERN** (consumer flag on
  58.9%/82.1% of FNs; 98.6%/100% of direct-1hop FNs lexically silent);
  source-specific oracle ceilings (reverse-1hop = 0.558/0.724 ORR @K=5;
  UNION_ALL 0.725/0.870); three simple ADD queues defined (BM25+ReverseDep,
  +ProviderConsumerSupport, +ComplementaryUnion) but **none beats Route-B at
  matched budget**; oracle-reviewer F1 ≈ 0.44/0.43 @B=5 vs Oracle-Add
  0.72/0.64 ⇒ dominant remaining loss = **RANKING**; progression gate =
  **RECALL_SIGNAL_HEADROOM_ONLY** → no verifier calls authorized.
- **Remaining:** none for this mission. The bounded verifier-ranked expansion
  (Route-B top-B + reverse-1hop pool) on DEVELOPMENT is the next instrument but
  requires a separate authorized mission.

## Last completed task

- First-pass recall bottleneck (2026-09-18): reports + JSON,
  `src/benchmark/recall/`, 6 scripts, `tests/unit/test_recall_bottleneck.py`
  (19/19), independent audit (19/19 checks PASS); docs updated.

## Immediate next step

- Await review; a future follow-up mission may run a **bounded verifier-ranked
  expansion** (existing frozen verifier protocol/budget) on DEVELOPMENT to test
  whether verifier-ranked recovery converts the measured 0.73/0.87 availability
  ceilings into realized recall — NOT authorized in this mission.

## Blockers

- Semantic-proxy human audit remains **AWAITING_HUMAN_RATINGS** (human-work
  blocker; the AI-assisted track is descriptive only, not gold).
- Human minimal spot-check (119 rows) awaits a human reviewer.
- Pre-existing environmental (2 full-suite failures, identical on clean base):
  pinned djangocms git cache absent at benchmark_data/repositories/djangocms.
- Saleor parent-visible history cache absent (dist/real-commit-cache/saleor) —
  no Saleor co-change arm; recorded UNAVAILABLE in the taxonomy/ceilings.

## Full-suite state (First-pass recall mission gate, 2026-09-18)

- **19/19 new unit tests PASS** (`tests/unit/test_recall_bottleneck.py`);
  related `test_oracle_gap.py` 16/16 green (35 total).
- Ruff clean on all changed Python; mypy clean on `src/benchmark/recall`;
  py_compile clean; `git diff --check` clean.
- Independent audit recomputes the headline numbers from frozen records
  without importing the analysis scripts — **19/19 checks PASS**
  (`reports/fn_independent_audit.json`).

## Closure block (First-pass recall mission, 2026-09-18)

- Branch: `research/first-pass-recall-bottleneck-2026-09-18` → merged to
  `main`; DEV-evidence milestone tag (no stable-tag move) only if the milestone
  is fully audited and reproducible.
- Prior scientific closure commit `8b2d1b6` / tag
  `oracle-gap-bidirectional-repair-2026-09-18` remain immutable.
- Next scientific task (NOT started, requires its own authorization): bounded
  verifier-ranked expansion on DEVELOPMENT.