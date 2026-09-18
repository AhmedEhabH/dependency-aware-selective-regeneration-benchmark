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
**Task:** README REORGANIZATION + RESEARCH JOURNEY (2026-09-18; T2 docs-only) —
README rebuilt as a concise ~5-minute entry point (problem → idea → status
table → lessons → key numbers → bottleneck → datasets → governance → map →
reproduce → claim labels); `docs/RESEARCH_JOURNEY.md` created (17 chronological
milestones: tried/learned/ruled-out with revisit triggers); stale claims
removed (Saleor "future", LocAgent "adapter pending", Route-B "development
only", P2 "conditional", semantic audit "preparation", old 2026-09-16/17
header); documentation-architecture decision recorded in DECISIONS.md; all
links + headline numbers validated against authoritative reports; ZERO API —
**COMPLETE**

---

## Now executing

- **MILESTONE COMPLETE.** README reorganization + research journey (T2
  docs-only, ZERO API): README rebuilt as the concise entry point with the
  mandated 11-section structure; `docs/RESEARCH_JOURNEY.md` created with 17
  chronological milestones (each negative framed as a search-space reduction
  with an explicit revisit trigger); stale-phrase audit clean; all 38 README
  links + 28 journey links resolve; every headline number cross-checked
  against authoritative reports; no scientific result changed.
- **Remaining:** none for this docs mission. The next scientific task
  (First-Pass Recall Bottleneck, DEVELOPMENT only) remains NOT started.

## Last completed task

- README reorganization + research journey (2026-09-18): README.md rebuilt;
  docs/RESEARCH_JOURNEY.md created; PROGRESS/DECISIONS updated; links +
  numbers validated; ZERO model/API calls.

## Immediate next step

- Begin the **first-pass recall bottleneck** study on DEVELOPMENT only
  (FN taxonomy → source-specific ceilings → ADD queues → matched-budget DEV
  comparison → gate; ZERO-API first).

## Blockers

- Semantic-proxy human audit remains **AWAITING_HUMAN_RATINGS** (human-work
  blocker; the AI-assisted track is descriptive only, not gold).
- Human minimal spot-check (119 rows) awaits a human reviewer.
- Pre-existing environmental (2 full-suite failures, identical on clean base):
  pinned djangocms git cache absent at benchmark_data/repositories/djangocms.
- Saleor parent-visible history cache absent (dist/real-commit-cache/saleor) —
  no Saleor co-change arm; recorded UNAVAILABLE in the ablation.

## Full-suite state (Oracle-gap mission gate, 2026-09-18)

- **16/16 new oracle-gap unit tests PASS** (`tests/unit/test_oracle_gap.py`);
  related suites green (test_semantic_ai_audit 19, test_semantic_audit 7).
- Ruff clean on all changed Python; py_compile clean; `git diff --check` clean.
- Six T3 validation gates + independent audit PASS
  (`reports/oracle_gap_gates_validation.json`,
  `reports/ORACLE_GAP_INDEPENDENT_AUDIT.md`).
- Prior AI-audit gate (2026-09-18, carried): full suite 3307 passed / 33
  skipped / 2 pre-existing environmental failures.

## Closure block (Oracle-gap mission, 2026-09-18)

- Branch: `research/oracle-gap-bidirectional-repair-2026-09-18` → merged to
  `main` as **scientific closure commit `8b2d1b6`** (immutable scientific
  fact).
- Tag `oracle-gap-bidirectional-repair-2026-09-18` — **peel `8b2d1b6`** ==
  scientific closure commit (unchanged; post-tag docs commits advance main but
  never move the tag; DEV evidence milestone tag, NOT a stable-tag move).
- Live HEAD / origin/main are runtime git facts (query with `git rev-parse`);
  they are NOT embedded here because committing metadata changes HEAD.
- LIGHT export (at scientific closure): `project-2026-09-18-0807.zip`
  SHA-256 `aea499406fecf6af37510e276fc272ed8025886b1640c7f6392569db560d192f`
  (required members `.git/HEAD`, `dist/pilot-kaggle-upload.zip`, `.sha256`
  present).
- Next scientific task (NOT started): FIRST-PASS RECALL BOTTLENECK on
  DEVELOPMENT only.