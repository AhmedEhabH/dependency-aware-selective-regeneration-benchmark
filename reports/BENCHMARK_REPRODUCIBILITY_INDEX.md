# BENCHMARK REPRODUCIBILITY INDEX — djangoCMS External-Validity Study

**STUDY_ID:** `scientific-stagec-djangocms-01`  
**Generated (UTC):** 2026-09-08T01:49:59.327506+00:00

## 1. Frozen inputs (HARD FROZEN, not modified)

| Input | Path |
| --- | --- |
| Hidden gold (evaluation-only) | `benchmark_data/external_validity/djangocms_hidden_gold_draft.json` |
| Candidate universe (144) | `benchmark_data/external_validity/djangocms_5_0_0_candidate_universe.json` |
| Dependency graph | `benchmark_data/external_validity/djangocms_5_0_0_dependency_graph.json` |
| Final visible drafts | `benchmark_data/external_validity/visible_drafts/` (6 YAML) |
| Pinned source | `benchmark_data/repositories/djangocms` @ `0f633fc9fa213357f4202482aab2b0edad680f95` |
| Wiring runtime | `src/benchmark/external_validity/study_runtime.py` |

## 2. Scientific configuration (frozen)

| Setting | Value |
| --- | --- |
| Model | `qwen/qwen3-coder` |
| Provider | DeepInfra pinned through OpenRouter (`deepinfra/turbo`) |
| Fallback | OFF |
| Temperature | 0 |
| Caps | agent 1024 / impact_plan 4096 |
| Retry policy | frozen: max 1 transient retry (`max_transient_retries=1`) |
| Scope | SELECTION ONLY |
| Workflow timeout | 600 s per cell |

## 3. Evidence locations

| Evidence | Path |
| --- | --- |
| Pre-run validation (B) | `reports/scientific-stagec-djangocms-01/prevalidation.json` |
| Six gates + audit (pre) | `reports/scientific-stagec-djangocms-01/runtwiring_gates.json` |
| Frozen 60-cell manifest | `reports/scientific-stagec-djangocms-01/manifest_60.json` |
| Raw per-run records (append-only) | `reports/scientific-stagec-djangocms-01/run_records.jsonl` |
| Per-run raw JSON | `reports/scientific-stagec-djangocms-01/runs/*.json` |
| Checkpoints | `reports/scientific-stagec-djangocms-01/checkpoint_10.json … checkpoint_60.json` |
| Final metrics | `reports/scientific-stagec-djangocms-01/final_metrics.json` |
| Closure gates + audit (post) | `reports/scientific-stagec-djangocms-01/closure_gates.json` |

## 4. Repro steps

1. `python scripts/stagec_djangocms_study_execute.py prevalidate`
2. `python scripts/stagec_djangocms_study_execute.py gates`
3. `python scripts/stagec_djangocms_study_execute.py freeze-manifest`
4. `python scripts/stagec_djangocms_study_execute.py run --limit 10 --inter-cell-delay 15` (repeat until 60/60)
5. `python scripts/stagec_djangocms_study_execute.py metrics`
6. `python scripts/stagec_djangocms_study_execute.py close`

## 5. Determinism notes

- Gates/audit/metrics are deterministic and make zero scientific calls.
- Scientific inference uses temperature 0, but DeepInfra provider responses showed non-deterministic token counts across identical inputs (observed in this study); per-run raw response SHA-256 hashes are recorded so each response is independently verifiable.
- 60 raw records; every run_id maps 1:1 to a manifest cell.
