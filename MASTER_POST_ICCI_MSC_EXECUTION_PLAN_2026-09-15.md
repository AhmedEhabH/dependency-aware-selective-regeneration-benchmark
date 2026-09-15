# MASTER POST-ICCI MSC EXECUTION PLAN — 2026-09-15

**Author:** openrouter/deepseek/deepseek-v4-flash-0731
**Phase:** POST_ICCI_ZERO_API_CLOSURE
**Zero new scientific model/API calls in this phase.**
**Submitted science is FROZEN — no submitted experiment is modified or rerun.**

---

## 1. Phase objective

Close the post-submission engineering/evidence window around the ICCI
submission (repository artifact: `paper/v20-final/V20_FINAL_SUBMISSION.zip`)
with **ZERO new scientific model/API calls**, producing:

1. An immutable submission record (hashes, commits, ZIP integrity).
2. A single authoritative `00_CURRENT_RESEARCH_STATE.md` that supersedes
   (without deleting) the historical handoffs.
3. A formalized LocAgent common-evaluator normalization contract + deterministic
   regression tests.
4. Two-way LocAgent recomputation (A headline fail-closed all-10; B diagnostic
   survivor-conditioned usable-5).
5. Four-action FN breakdown over the existing Full/Sparse raw outputs.
6. A per-task error-analysis table for the ten historical held-out tasks.
7. Permanent HELD_OUT_TEST exposure marking (do-not-tune).
8. DRAFTED (not executed) next-experiment protocols A/B/C.
9. MSc proposal handoff update separating ICCI evidence / P5 descriptive
   evidence / proposed selective-escalation work.
10. Tests, recomputation, contradiction scan, independent audit.
11. A clear post-ICCI closure commit/tag (no historical tag rewrite).

## 2. Non-negotiable constraints

- **NO LLM/API call for scientific inference** (no new model calls, no
  reruns, no new matrices).
- **NO Saleor / LocBench runs; NO new LocAgent inference.**
- **NO tuning on the exposed ten-task HELD_OUT_TEST split.**
- **NO alteration of frozen P1/P5 outputs.**
- **Selective escalation is NOT claimed as validated** — proposed only.

## 3. Submitted-science identity (frozen)

| Item | Value |
|---|---|
| Submission ZIP | `paper/v20-final/V20_FINAL_SUBMISSION.zip` |
| ZIP SHA-256 | `9CB5BDCCFCE8542E5A936136B60E01471FB917EF18B5B537220966421425E138` |
| ZIP entries | 10 (blind + supervisor TEX/PDF, `v20_body.tex`, `references.bib`, change log, claims matrix, reviewer-risk audit, status report) |
| Science candidate commit | `42755df0cb53a60be1c8a2a3c3322d34ef3d8155` (2026-09-15T09:30:59+00:00) |
| Submission archive commit | `0a5928ce615340262ca3697615eee55fb8847ed6` (2026-09-15T09:36:44+00:00) |
| Corrected main base | `884ba7982f283b2e78c48d768d34f2f5a726a862` (P5 corrections merged) |
| Conference paper/submission ID | NOT recorded in repo (no fabrication) |
| Submission timestamp | NOT recorded in repo (no fabrication) |

## 4. Current-truth summary (authoritative state after this closure)

See `00_CURRENT_RESEARCH_STATE.md` (single front door, supersedes historical
handoffs without deleting them).

## 5. Evidence inventory used in this closure (all existing / frozen)

- P1 real-commit held-out evaluation: `research/real-commit-p1-01/`
  (run_records.jsonl, runs/raw/*.txt, final_metrics.json, manifest_60.json).
- LocAgent P5-B/P5-C: `research/locagent-p5b/` (out_c/, ledger, shared
  comparison, two-way recomputation JSON).
- Dataset: `benchmark_data/real_commit_impact_v1/scientific/` +
  `split_freeze.json`.
- Scorers/auditors: `scripts/locagent_shared_comparison.py`,
  `scripts/audit_locagent_p5c.py`, `src/benchmark/locagent/`.

## 6. Deliverable locations

| Deliverable | Path |
|---|---|
| Submission record | `paper/v20-final/ICCI_SUBMISSION_RECORD_2026-09-15.json` |
| Authoritative state | `00_CURRENT_RESEARCH_STATE.md` |
| Normalization contract | `reports/LOCAGENT_COMMON_EVALUATOR_NORMALIZATION.md` |
| Two-way recompute script | `scripts/recompute_locagent_two_way.py` |
| Two-way recompute JSON | `research/locagent-p5b/locagent_two_way.json` |
| FN breakdown script | `scripts/post_icci_four_action_fn_breakdown.py` |
| FN breakdown outputs | `research/post-icci-zero-api-closure/four_action_fn_breakdown.{json,csv}` |
| Per-task analysis script | `scripts/post_icci_per_task_error_analysis.py` |
| Per-task outputs | `research/post-icci-zero-api-closure/per_task_error_analysis.{csv,md}` |
| Regression tests | `tests/unit/test_post_icci_closure.py` |
| Protocol drafts | `docs/POST_ICCI_NEXT_EXPERIMENTS_DRAFT.md` |
| Closure report | `reports/POST_ICCI_ZERO_API_CLOSURE_REPORT.md` |

## 7. Next experiment (ONLY after supervisor authorization and a fresh
non-exposed split)

Selective-escalation line: sparse first pass → omission-risk detection →
bounded graph-guided escalation → false-negative verification, evaluated on
TRAIN/VALIDATION (non-LLM baselines) and later on a FRESH held-out split
(NOT the exposed HELD_OUT_TEST ten). See
`docs/POST_ICCI_NEXT_EXPERIMENTS_DRAFT.md`.