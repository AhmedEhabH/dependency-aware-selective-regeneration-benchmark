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
**Task:** QWEN3 TWO-REALIZATION REPLICATION + FULL SCORE PERSISTENCE
(2026-09-19; T3 scientific continuation of the contamination-bridge line) —
**COMPLETE: `INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`**; A and B both pass the
frozen gate on djangoCMS AND Saleor @B=5; full label-free file-score tables
persisted for the future calibrated ADD+DROP study; Stage 5 stays PAUSED/SEALED.

---

## Now executing

- **MILESTONE COMPLETE (T3, authorized paid run ≤ $0.50).** The
  contamination-robustness bridge line is CLOSED WITH A RESULT. Two complete
  independent realizations (A and B) of `qwen/qwen3-embedding-8b` @ DeepInfra
  ($0.01/M live-reverified, fallback disabled) were run over the FULL legal
  DEV population (49,703 units + 323 queries per realization; whitespace-only
  excluded; caches on E:). Actual cost A ≈ $0.1971 / B ≈ $0.2188; cumulative
  incl. prior probes ≈ **$0.439 < $0.50**. 0 permanent failures.
  **Verdict = `INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`** (A and B both PASS
  djangoCMS and Saleor @B=5; all file-level CIs exclude zero). A-vs-B
  reproducibility: 97.21% exact same set, mean Jaccard 0.9907, 9 one-file
  flips all FP-for-FP. Full label-free file-score Parquet tables persisted
  (143,852 rows/realization) for the future calibrated ADD+DROP study.
  CALIBRATED_SET_SELECTION_V1 DRAFTED (NOT executed). Lipton 2014 literature
  note added. Competitors documented, NOT run.
- **Remaining:** none for this mission (closure follows: commit/merge/push/
  tag/export/STOP report).

## Last completed task

- QWEN3 two-realization replication (2026-09-19, T3): two independent full
  realizations of the hosted Qwen embeddings on DEV; per-realization metrics +
  paired bootstrap CIs + frozen gate (PASS everywhere); A/B reproducibility;
  full-file label-free score persistence; set-selection diagnosis verified;
  CALIBRATED_SET_SELECTION_V1 draft; Lipton literature note; competitor note.
  Scripts `scripts/qwen3_two_realization_{run,analyze,reports,audit}.py`;
  evidence under `research/contamination-bridge/qwen_embed/`;
  reports `reports/QWEN3_TWO_REALIZATION_REPLICATION_REPORT_2026-09-19.md`.

## Immediate next step

- Closure: full validation, commit/merge/push/tag, verify HEAD ==
  origin/main, clean tree, TRUE LIGHT export, STOP report.

## Blockers

- Semantic-proxy human audit remains **AWAITING_HUMAN_RATINGS** (human-work
  blocker; the AI-assisted track is descriptive only, not gold).
- Human minimal spot-check (119 rows) awaits a human reviewer.
- Pre-existing environmental (2 full-suite failures, identical on clean base):
  pinned djangocms git cache absent at benchmark_data/repositories/djangocms.
- Stage 5 confirmatory stays PAUSED/SEALED pending a fresh frozen protocol +
  authorization; the dense-replication result does NOT unlock it by itself
  (provenance verdict C unchanged).

## Full-suite state (QWEN3 two-realization replication, 2026-09-19)

- New unit tests `tests/unit/test_qwen3_two_realization.py` **6/6 PASS**
  (whitespace-unit rule, ChunkCache round-trip, budget projection guard,
  analyzer contributions, reproducibility stats, label-free schema).
- Affected suites PASS (signal metrics, or_embeddings).
- Independent audit **13/13 PASS** (`reports/qwen3_two_realization_audit.json`):
  corpus index 50,026 entries/realization, cumulative spend < ceiling,
  pooled F1 recomputed ≥ 0.25 on both repos both realizations, label-free
  Parquet (143,852 rows), reproducibility ≥ 95%.
- Ruff clean; py_compile clean; `git diff --check` clean.

## Closure block (QWEN3 two-realization replication, 2026-09-19)

- T3 authorized paid run (≤ $0.50; actual ≈ $0.439 cumulative).
- DEV-evidence tag (peel == merge == main-at-tag-time; audited DEVELOPMENT
  evidence; NOT a stable-tag move). Pushed to origin; origin/main == HEAD ==
  tag peel.
- LIGHT export at scientific closure (filename/hash in the final stop report).
- Next scientific task (NOT started, requires its own authorization):
  **CALIBRATED_SET_SELECTION_V1** (DEV only; draft at
  `docs/CALIBRATED_SET_SELECTION_V1_DRAFT.md`), then a Stage-5 confirmatory
  decision.