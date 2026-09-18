# PROGRESS.md — Execution Source of Truth

**Role:** Execution source of truth (what is being executed now, last completed
task, immediate next step, blockers). Scientific truth lives in
`00_CURRENT_RESEARCH_STATE.md`; decisions are recorded append-only in
`DECISIONS.md`.

**Branch:** `main`
**HEAD:** `9dd9797` (merge of `docs/p2-final-report-2026-09-18`) → post-merge
HEAD recorded in the closure report
**Model:** openrouter/deepseek/deepseek-v4-flash-0731
**Task:** AI-ASSISTED SEMANTIC AUDIT — INGEST + AGREEMENT + POST-HOC
SENSITIVITY + HUMAN SPOT-CHECK (2026-09-18) — the 10 frozen rater outputs
(5 ChatGPT + 5 Claude) were validated (2 syntax-only repairs, content
preserved, originals untouched), ingested against the sealed mapping, and
agreement + post-hoc sensitivity + semantic-relevance analyses run (ZERO API):
exact row agreement **0.6981** (252/361), Cohen's kappa **0.5579**,
historical-changed agreement 0.8468 vs omitted 0.6320, case-level proxy 0.56;
post-hoc omitted-role partition (15 in-hist vs 235 outside-hist);
top-ranked-vs-random relevance descriptive per rater (ChatGPT 0.193 vs 0.099;
Claude 0.053 vs 0.008); 119-row human minimal spot-check form generated;
**19/19 unit tests PASS**; report delivered — **COMPLETE**

---

## Now executing

- **MILESTONE COMPLETE.** The independent AI-assisted semantic-plausibility
  audit analysis is delivered: the 10 frozen rater outputs were validated
  exactly as received (chatgpt_02 + chatgpt_04 repaired syntax-only — unescaped
  quotes in evidence strings — normalized copies created, originals untouched,
  full content-preservation verified), staged under
  `research/semantic_audit/ai_blinded_v1/rater_outputs/`, and analyzed against
  the sealed mapping: exact agreement **0.6981**, Cohen's kappa **0.5579**,
  confusion matrix, agreement-by-label, abstention 0/0, role split
  (historical 0.8468 / omitted 0.6320), case-level (proxy 0.56, omitted impact
  0.48, tangled 0.68), 109 disagreements, deterministic 10-row agreement
  sample. POST-HOC sensitivity separated `sparse_omitted_and_historical_changed`
  (n=15, κ=0.17) from `sparse_omitted_and_outside_historical_diff` (n=235,
  κ=0.26). Descriptive top-ranked-vs-random relevance (outside historical diff)
  reported per rater (ChatGPT 0.193 vs 0.099; Claude 0.053 vs 0.008); ChatGPT
  and Claude kept separate, never pooled as gold. 119-row human minimal
  spot-check form generated (109 disagreements + 10 deterministic agreement
  rows). Explicitly recorded as an independent AI-assisted semantic-plausibility
  audit / model-based semantic sensitivity analysis, NOT human semantic gold.
- **Remaining:** none for this analysis. The human minimal spot-check form is
  ready for the human reviewer; the human two-rater + adjudicator audit remains
  **AWAITING_HUMAN_RATINGS**.

## Last completed task

- AI-assisted semantic-audit agreement + post-hoc sensitivity + human
  spot-check (2026-09-18): 10 frozen outputs validated/ingested, agreement +
  post-hoc analyses run, 19/19 unit tests PASS, report + ledgers updated,
  ZERO model/API calls.

## Immediate next step

- Deliver `research/semantic_audit/ai_blinded_v1/human_spotcheck_form.csv`
  (119 rows) to the human reviewer as the first bounded check of inter-model
  disagreement; the human semantic audit remains the gold.

## Blockers

- Semantic-proxy human audit remains **AWAITING_HUMAN_RATINGS** (human-work
  blocker; machine-preparation complete and verified; the AI-assisted
  descriptive track does NOT unblock it).
- Human minimal spot-check (119 rows) awaits a human reviewer (no human
  judgments fabricated in this closure).
- Pre-existing environmental (2 full-suite failures, identical on clean base):
  pinned djangocms git cache absent at benchmark_data/repositories/djangocms
  (legacy parent-commit corpus not re-materializable; INTERNAL_TEST bundles
  were materialized from dist/real-commit-cache/djangocms instead).
- Saleor parent-visible history cache absent (dist/real-commit-cache/saleor) —
  no Saleor co-change arm; recorded UNAVAILABLE in the ablation.

## Full-suite state (AI-audit analysis gate, 2026-09-18)

- **19/19 AI-audit unit tests PASS** (`tests/unit/test_semantic_ai_audit.py`):
  16 prepare/agreement/spot-check + 3 new post-hoc tests; agreement + post-hoc
  statistics independently recomputed (sklearn + pure-stdlib) and matching.
- **Full suite (2026-09-18, AI-audit analysis gate): 3307 passed / 33 skipped /
  2 pre-existing environmental failures** (missing pinned djangocms repo
  checkout at benchmark_data/repositories/djangocms; identical on clean base).
- Ruff clean on all changed Python files; mypy strict clean on the new post-hoc
  script; py_compile clean.
- LIGHT export (P2 closure, carried): `project-2026-09-18-0139.zip`
  SHA-256 `c11fb734ee0267ca9b08874ee179062ac9124f55d6aec45898e9c3e58f4f2c5b`.