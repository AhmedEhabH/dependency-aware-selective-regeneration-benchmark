# STAGE-C-HELDOUT-CHALLENGE-01 (D053) — Independent Audit

- **Basis:** `_workspace/active/STAGE_C_HELDOUT_CHALLENGE_01_PACK/01_INDEPENDENT_AUDIT_OF_CURRENT_RESULT.md` + `04_TESTS_SIX_GATES_AND_AUDIT.md` — this is the LAST Todo selection experiment: a frozen held-out challenge with no explicit source-file names in visible requirements, isolating whether the 100% smoke ceiling was caused by visible-requirement leakage.
- **Audited source commit:** `7be94fb` (profile + selection-only wiring + results builder + six-gate validator + focused tests).
- **Date:** 2026-09-07.

## Audit checklist

| # | Item | Verdict | Evidence |
|---|------|---------|----------|
| 1 | no gold leakage into prompts/evidence/tools | PASS | gate G2 (Agent + ImpactPlan templates carry no `expected_actions`/`GOLD_SENTINEL`/heldout marker); G5 probe records + tool transcripts contain no `expected_actions`/`GOLD_SENTINEL`; `selection_tool_transcript` shows only list/read/search evidence |
| 2 | no scenario mutation after freeze | PASS | all six `benchmark_data/scenarios/todo-heldout-*.yaml` SHA-256 byte-identical to pack `07_MANIFEST_SHA256.json` (`5f8a1953…`, `794c93fa…`, `5ea3d587…`, `68f9ca80…`, `a2913614…`, `d210a1d4…`); `git diff HEAD` empty for the six scenario files |
| 3 | same scientific model/provider | PASS | G5 probe records `model_metadata.model=openrouter:qwen/qwen3-coder@DeepInfra` (both arms); temperature 0, caps Agent 1024 / ImpactPlan 4096; `--openrouter-provider DeepInfra` pinned, fallback OFF |
| 4 | selection-only path only | PASS | gate G3 (AnalyzeImpact once -> selection_study -> metrics), gate G4 60/60 dry-run with 0 calls/0 tokens; focused CLI tests prove no regen/repair contributions; runner has no `revise_plan`/executor/repair/migration/evaluator branch in selection-only mode |
| 5 | old results untouched | PASS | `git diff HEAD` shows no modifications to `reports/STAGEC_SELECTION_01_RESULTS.csv`, `reports/SCIENTIFIC_MICROSTUDY_V11_DECISION.md`, `reports/scientific_stagec_selection_01/run_records.jsonl`, `reports/scientific_microstudy_v11/run_records.jsonl` (focused tests 12 all green); v1.1 NO-GO preserved |
| 6 | raw record append-only persistence | PASS | `RunRecordStore.append` idempotent-skip (existing contract); study writes to a fresh output dir `reports/scientific_stagec_heldout_01/`; prior study records verbatim |
| 7 | exact cost guard | PASS | `reports/STAGEC_HELDOUT_01_COST_ESTIMATE.md`: 60-run estimate $0.108094 from real G5 probe calibration <= $0.20 hard stop |
| 8 | no executor work | PASS | `git diff --name-only HEAD` over `src/benchmark/execution`, `src/benchmark/llm`, `src/benchmark/strategies`, `src/benchmark/selection`, `scripts/exact_patch.py`, `benchmark_data/repository_profiles/todo.yaml`, `configs/` = empty; only additive profile + builder + validator + tests |
| 9 | no Todo scenario expansion after this study | PASS | frozen stop rule (pack `00_DECISION_LOCK.md`): this is the last Todo selection scenario set; if both arms remain at/near ceiling conclude `TODO_SELECTION_SATURATED=YES`; if a measurable difference appears report it without rerunning/tuning |

## Verdict

**AUDIT = PASS** — the implementation matches the frozen held-out design: six
user-level scenarios with no visible source-file names, same pinned
qwen/qwen3-coder @ DeepInfra with fallback OFF, selection-only execution, no
gold leakage into any prompt/evidence/tool surface, prior Stage-C exploratory
and v1.1 NO-GO evidence untouched, and a cost guard (<= $0.20) enforced before
any of the 60 study calls.