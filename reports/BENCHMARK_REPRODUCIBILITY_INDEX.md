# BENCHMARK REPRODUCIBILITY INDEX — djangoCMS External-Validity Study

**STUDY_ID:** `scientific-stagec-djangocms-01`
**Report corrected (UTC):** 2026-09-08T03:12:51.922429+00:00

## 1. Frozen inputs (HARD FROZEN, not modified)

| Input | Path | SHA-256 (verified unchanged) |
|---|---|---|
| Hidden gold (evaluation-only) | benchmark_data/external_validity/djangocms_hidden_gold_draft.json | 260bbeacd53efcab6b99366941c64b667f9f227467b70350fcb7c248b6f00882 |
| Candidate universe (144) | benchmark_data/external_validity/djangocms_5_0_0_candidate_universe.json | 61e06910555d2be352a6e10d7ef171a8a87e6acdab8a73ba16eb7fe498481fb5 |
| Dependency graph | benchmark_data/external_validity/djangocms_5_0_0_dependency_graph.json | 59a3400842da03471efeb3499b238eb714cf9978215166d7d11afb1da55af0f7 |
| Final visible drafts | benchmark_data/external_validity/visible_drafts/ (6 YAML) | a7e72f7af23541407180d490f5dd03e9df281efb514ab4c4f92f4a59deb4c730; 0b25d27452ceff3fae08eecd42b15da8d6788c4af162455f71c2db5cf3450430; 836f42fbbf00cd097b52a928f12e01e463857f4a9fe01aa122729696b223a57b; c724fff84d0757e4182e3b127a296b6876964a267be5e3584f1aafcf9aefa0e3; 1caf61e7a4db2b887e8c14d02f349ef3771e7f19a27ecab2f69e6aa686e5e88c; d2076d5bf092ac8a96566c88f413deb1090ab61ebe85733a41174e8aac283021 |
| Frozen manifest | reports/scientific-stagec-djangocms-study-01/manifest_60.json | ab60a0276d4660bee42d32fbaeb828cd107866d421d5500437fa2053973055e0 |
| Aggregated raw records | reports/scientific-stagec-djangocms-study-01/run_records.jsonl | 8301c07debd59eaa2ae1c0571a833271b1de62e73959cb35a22d97af14c04e3e |
| 60 raw run JSONs | reports/scientific-stagec-djangocms-study-01/runs/*.json | 60 files hashed |

## 2. Scientific configuration (frozen)

| Setting | Value |
|---|---|
| Model | `qwen/qwen3-coder` |
| Provider | DeepInfra pinned through OpenRouter (`deepinfra/turbo`) |
| Fallback | OFF |
| Temperature | 0 |
| Caps | agent 1024 / impact_plan 4096 |
| Retry policy | frozen: max 1 transient retry |
| Scope | SELECTION ONLY |
| Workflow timeout | 600 s per cell |

## 3. Evidence locations

| Evidence | Path |
|---|---|
| Pre-run validation (B) | reports/scientific-stagec-djangocms-01/prevalidation.json |
| Six gates + audit (pre) | reports/scientific-stagec-djangocms-01/runtwiring_gates.json |
| Frozen 60-cell manifest | reports/scientific-stagec-djangocms-01/manifest_60.json |
| Raw per-run records (append-only) | reports/scientific-stagec-djangocms-01/run_records.jsonl |
| Per-run raw JSON | reports/scientific-stagec-djangocms-01/runs/*.json (60) |
| Checkpoints | reports/scientific-stagec-djangocms-01/checkpoint_10.json … checkpoint_60.json |
| Final metrics | reports/scientific-stagec-djangocms-01/final_metrics.json |
| Closure recompute (this pass) | reports/scientific-stagec-djangocms-01/closure_recompute.json |
| Serialization-size analysis | reports/scientific-stagec-djangocms-01/serialization_size_analysis.json |
| Raw-evidence hashes (immutability proof) | reports/scientific-stagec-djangocms-01/raw_evidence_hashes.json |
| Closure gates + audit (post) | reports/scientific-stagec-djangocms-01/closure_gates.json |

## 4. Repro steps

1. `python scripts/stagec_djangocms_study_execute.py prevalidate`
2. `python scripts/stagec_djangocms_study_execute.py gates`
3. `python scripts/stagec_djangocms_study_execute.py freeze-manifest`
4. `python scripts/stagec_djangocms_study_execute.py run --limit 10 --inter-cell-delay 15` (repeat until 60/60)
5. `python scripts/stagec_djangocms_study_execute.py metrics`
6. `python scripts/stagec_djangocms_study_execute.py close`

## 5. Determinism notes

- Gates/audit/metrics are deterministic and make zero scientific calls.
- Scientific inference uses temperature 0, but DeepInfra responses showed non-deterministic token counts across identical inputs; per-run raw response SHA-256 hashes are recorded so each response is independently verifiable.
- 60 raw records; every run_id maps 1:1 to a manifest cell (True).
