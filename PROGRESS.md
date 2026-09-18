# PROGRESS.md — Execution Source of Truth

**Role:** Execution source of truth (what is being executed now, last completed
task, immediate next step, blockers). Scientific truth lives in
`00_CURRENT_RESEARCH_STATE.md`; decisions are recorded append-only in
`DECISIONS.md`.

**Branch:** `main`
**HEAD:** `8b2d1b6` (merge of `research/oracle-gap-bidirectional-repair-2026-09-18`)
**origin/main:** `8b2d1b6` (at Oracle-gap closure; post-tag docs commit
`f5366aa` advanced origin/main afterward — T2 state reconciliation)
**Tag:** `oracle-gap-bidirectional-repair-2026-09-18` — peel `8b2d1b6` == merge
== origin/main at closure (unchanged; post-tag docs commits never move a tag;
DEV evidence milestone tag, NOT a stable-tag move)
**Model:** openrouter/deepseek/deepseek-v4-flash-0731
**Task:** ORACLE-GAP DECOMPOSITION + BIDIRECTIONAL BOUNDED SET REPAIR
(2026-09-18) — exploratory DEVELOPMENT line after the frozen P2 Phase-1
negative closure: verified error budget from frozen records; computed
Oracle-Add/Drop/Bidirectional F1 ceilings on djangoCMS DEV + Saleor DEV;
decomposed the Oracle gap; tested observable FP-pruning; simulated a simple
bidirectional candidate (BBSR). Result: **BIDIRECTIONAL_HEADROOM_ONLY** — the
oracle surface shows F1 0.85–0.90 reachable bidirectionally (F1 0.85 NOT
add-only-reachable on Saleor, ceiling 0.8291), but cheap observable DROP
signals are insufficient and the heuristic BBSR fails the progression gate on
both repos. ZERO API/model calls; **16/16 new tests PASS**; sealed sets
untouched — **COMPLETE**

---

## Now executing

- **MILESTONE COMPLETE.** Oracle-gap decomposition + bidirectional bounded set
  repair (EXPLORATORY DEVELOPMENT, ZERO API): (1) confirmatory error budget
  verified from frozen records (Sparse TP=51/FP=104/FN=199 F1=0.252; verifier
  B=5 TP=71/FP=274/FN=179 F1=0.239 — matches the working diagnostic); (2)
  DEVELOPMENT oracle ceilings computed (Oracle-Add ALL 0.8674 djangoCMS /
  0.8291 Saleor; Oracle-Drop ALL 0.3956 / 0.3492; bidirectional reaches F1 1.0
  at A=ALL,D=ALL; **F1=0.85 NOT add-only-reachable on Saleor**); (3) gap
  decomposition shows **first-pass recall loss dominates** (75–79% of proxy
  positives missed) with review false-acceptance second and ranking loss third;
  budget loss ≈0 → not adaptive budget; (4) observable FP-pruning signal is
  weak (flagged precision ≈ random control); (5) heuristic BBSR fails the
  progression gate on both repos → **no new verifier calls authorized**.
- **Remaining:** none for this mission. The next bottleneck (first-pass recall)
  is documented; human semantic-audit ratings remain an open blocker.

## Last completed task

- Oracle-gap decomposition + bidirectional set-repair exploration (2026-09-18):
  10 analysis scripts + 16 unit tests + 9 reports + independent audit + gates;
  ZERO model/API calls; decision BIDIRECTIONAL_HEADROOM_ONLY.

## Immediate next step

- Pursue the **first-pass recall** bottleneck on DEVELOPMENT (the measured
  largest lever: Oracle-Add headroom +0.55–0.57 F1), or unblock the human
  semantic-audit ratings.

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
  `main` (`8b2d1b6`, scientific merge commit).
- Tag `oracle-gap-bidirectional-repair-2026-09-18` — peel `8b2d1b6` == merge
  == origin/main at closure (unchanged; post-tag docs commit `f5366aa`
  advanced origin/main afterward but does NOT move the tag; DEV evidence
  milestone tag, NOT a stable-tag move).
- LIGHT export (at scientific closure): `project-2026-09-18-0807.zip`
  SHA-256 `aea499406fecf6af37510e276fc272ed8025886b1640c7f6392569db560d192f`
  (required members `.git/HEAD`, `dist/pilot-kaggle-upload.zip`, `.sha256`
  present).
- Next scientific task (NOT started): FIRST-PASS RECALL BOTTLENECK on
  DEVELOPMENT only.