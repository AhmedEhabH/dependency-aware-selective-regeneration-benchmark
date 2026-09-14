# Paper Claim → Evidence Map

Every headline result in the manuscript V7 (and the claims below it) is traced
to a frozen, immutable repository artifact. **Frozen artifacts are evidence;
the README is navigation only.** No value below was regenerated with a model or
an API call; all are recomputed deterministically from structured frozen files
by `scripts/verify_paper_claims.py` (exit 0 = internally consistent).

> Recompute command (no API key required):
>
> ```bash
> python scripts/verify_paper_claims.py
> ```

Evidence directories (canonical, frozen, do not modify):

- Primary djangoCMS study: `reports/scientific-stagec-djangocms-study-01/`
- ImpactPlan-v2 study: `reports/scientific-stagec-djangocms-impactplan-v2-01/`
- 16K diagnostic: `reports/scientific-stagec-djangocms-impactplan-16k-diagnostic-01/`
- 8192 cap ablation probe: `reports/scientific-stagec-djangocms-impactplan-cap-ablation-01/`

---

## 1. Primary study — Agent arm

| Claim | Value | Canonical artifact | Exact field / aggregation | Verifier check |
|---|---|---|---|---|
| Recorded cells | 30 | `reports/scientific-stagec-djangocms-study-01/run_records.jsonl` | rows with `arm == "iterative_repository_agent"` | §[1] |
| Valid cells | 25 | `run_records.jsonl` | count `terminal_status == "succeeded"` | §[1] |
| Failed cells | 5 | `run_records.jsonl` | count `terminal_status == "failed"` | §[1] |
| Truncations | 0 | `run_records.jsonl` | count `truncation_status == true` | §[1] |
| TP / FP / FN | 95 / 52 / 18 | `run_records.jsonl` + `final_metrics.json` | sum over valid runs vs `overall.iterative_repository_agent.{tp,fp,fn}` | §[1] |
| Precision | 0.646259 | `final_metrics.json` | `overall.iterative_repository_agent.precision` | §[1] |
| Recall | 0.840708 | `final_metrics.json` | `overall.iterative_repository_agent.recall` | §[1] |
| F1 | 0.730769 | `final_metrics.json` | `overall.iterative_repository_agent.f1` | §[1] |
| Prompt tokens (all-cell) | 441,348 | `run_records.jsonl` | sum `prompt_tokens` over all 30 rows | §[1] |
| Completion tokens (all-cell) | 8,444 | `run_records.jsonl` | sum `completion_tokens` over all 30 rows | §[1] |
| **Total tokens (all-cell)** | **449,792** | `run_records.jsonl` | sum `total_tokens` over all 30 rows (= prompt + completion) | §[4] |
| Calls (all-cell) | 206 | `run_records.jsonl` | sum `model_calls` | §[1] |
| Recorded cost | $0.140850 | `run_records.jsonl` | sum `api_cost` | §[1] |

## 2. Primary study — ImpactPlan-v1 arm

| Claim | Value | Canonical artifact | Exact field / aggregation | Verifier check |
|---|---|---|---|---|
| Recorded cells | 30 | `run_records.jsonl` | rows with `arm == "impact_plan"` | §[2] |
| Valid cells | 6 | `run_records.jsonl` | count `terminal_status == "succeeded"` | §[2] |
| Failed cells | 24 | `run_records.jsonl` | count `terminal_status == "failed"` | §[2] |
| **Truncations** | **19** | `run_records.jsonl` | count `truncation_status == true` | §[2] |
| TP / FP / FN | 23 / 11 / 2 | `run_records.jsonl` + `final_metrics.json` | sum over valid runs vs `overall.impact_plan.{tp,fp,fn}` | §[2] |
| Precision | 0.676471 | `final_metrics.json` | `overall.impact_plan.precision` | §[2] |
| Recall | 0.920000 | `final_metrics.json` | `overall.impact_plan.recall` | §[2] |
| F1 | 0.779661 | `final_metrics.json` | `overall.impact_plan.f1` | §[2] |
| Prompt tokens (all-cell) | 87,287 | `run_records.jsonl` | sum `prompt_tokens` over all 30 rows | §[2] |
| Completion tokens (all-cell) | 97,114 | `run_records.jsonl` | sum `completion_tokens` over all 30 rows | §[2] |
| **Total tokens (all-cell)** | **184,401** | `run_records.jsonl` | sum `total_tokens` over all 30 rows (= prompt + completion) | §[4] |
| Calls (all-cell) | 28 | `run_records.jsonl` | sum `model_calls` | §[2] |
| Recorded cost | $0.123298 | `run_records.jsonl` | sum `api_cost` | §[2] |

## 3. ImpactPlan-v2 (sparse) study

| Claim | Value | Canonical artifact | Exact field / aggregation | Verifier check |
|---|---|---|---|---|
| Recorded cells | 30 | `reports/scientific-stagec-djangocms-impactplan-v2-01/run_records.jsonl` | all rows (`arm == "impact_plan_v2"`) | §[3] |
| Valid cells | 29 | `run_records.jsonl` | count `terminal_status == "succeeded"` | §[3] |
| Failed cells | 1 | `run_records.jsonl` | count `terminal_status == "failed"` | §[3] |
| **Truncations** | **0** | `run_records.jsonl` | count `truncation_status == true` | §[3] |
| TP / FP / FN | 103 / 36 / 16 | `run_records.jsonl` + `final_metrics.json` | sum over valid runs vs `overall.{tp,fp,fn}` | §[3] |
| Precision | 0.741007 | `final_metrics.json` | `overall.precision` | §[3] |
| Recall | 0.865546 | `final_metrics.json` | `overall.recall` | §[3] |
| F1 | 0.798450 | `final_metrics.json` | `overall.f1` | §[3] |
| FNR | 0.134454 | `final_metrics.json` | `overall.fnr` | §[3] |
| Full-recall count / rate | 18 / 29 = 0.620690 | `run_records.jsonl` | count `full_recall == true` over valid runs; `final_metrics.overall.full_recall_rate` | §[3] |
| Prompt tokens (all-cell) | 113,880 | `run_records.jsonl` | sum `prompt_tokens` over all 30 rows | §[3] |
| Completion tokens (all-cell) | 30,473 | `run_records.jsonl` | sum `completion_tokens` over all 30 rows | §[3] |
| **Total tokens (all-cell)** | **144,353** | `run_records.jsonl` | sum `total_tokens` over all 30 rows (= prompt + completion) | §[4] |
| Calls | 30 | `run_records.jsonl` | sum `model_calls` | §[3] |
| Recorded cost | $0.064634 | `run_records.jsonl` | sum `api_cost` | §[3] |

## 3a. M1A — Controlled 4096-cap feasibility boundary (2026-09-12)

This is a **preregistered capability/feasibility boundary**, NOT a completed
60-cell controlled ablation, and NO semantic superiority claim is made.
Evidence directory: `research/controlled-encoding-ablation-01/`. Zero-API
verifier: `scripts/verify_controlled_encoding_4096_claims.py` (27/27 PASS).

| Claim | Value | Canonical artifact | Exact field / aggregation | Verifier check |
|---|---|---|---|---|
| PROMPT_CONTROLLED_DIFF | PASS | `prompt_control.json` | `PROMPT_CONTROLLED_DIFF == "PASS"` + per-scenario checks | §M1A |
| Representation equivalence (`D_s(E_s(π)) == π`) | PASS | module recompute | `representation_equivalence_checks()["REPRESENTATION_EQUIVALENCE"]` | §M1A |
| Six pre-benchmark gates + audit | ALL PASS (zero calls) | `prestudy_gates.json` | `all_passed` + `audit.passed` | §M1A |
| Probe A (Full-v2) finish_reason | `length` | `capability_probes.json` | `probes.probe_a_full_v2.finish_reason` | §M1A |
| Probe A completion_tokens | 4096 (== frozen cap) | `capability_probes.json` | `probes.probe_a_full_v2.usage.completion_tokens` | §M1A |
| Probe A truncated decision id | 76 | `probes/raw/probe_a_full_v2.txt` | last complete `"id"` before unterminated JSON | §M1A |
| Probe A schema-valid | False | `capability_probes.json` | `probes.probe_a_full_v2.schema_valid` | §M1A |
| Probe B (Sparse-v2) finish_reason | `stop` | `capability_probes.json` | `probes.probe_b_sparse_v2.finish_reason` | §M1A |
| Probe B completion_tokens | 419 | `capability_probes.json` | `probes.probe_b_sparse_v2.usage.completion_tokens` | §M1A |
| Probe B decoded candidate count | 144 | `capability_probes.json` | `probes.probe_b_sparse_v2.decoded_candidate_count` | §M1A |
| Probe B semantic validation | PASS | `capability_probes.json` | `probes.probe_b_sparse_v2.schema_valid` | §M1A |
| Raw SHA-256 (both probes) | verified | `probes/raw/*.sha256` | file == sidecar == recorded `raw_response_sha256` | §M1A |
| Scientific study cells executed | 0 | absence | no `manifest_60.json`; no `run_records.jsonl` | §M1A |
| Probe cost | ≈ $0.00593 | `capability_probes.json` usage | prompt×$0.30/1M + completion×$1.00/1M | §M1A |

## 3b. M1B — Controlled 16K cap-relaxed encoding ablation (2026-09-12)

POST-HOC CONTROLLED CAP-RELAXED ABLATION (NOT a preregistered
between-model or universal-superiority claim). Evidence directory:
`research/controlled-encoding-ablation-16k-01/`. Zero-API verifier:
`scripts/verify_controlled_encoding_16k_claims.py` (42/42 PASS).

| Claim | Value | Canonical artifact | Exact field / aggregation | Verifier check |
|---|---|---|---|---|
| Frozen M1A parity (only cap changed) | PASS | `FROZEN_M1A_PARITY.json` | `parity == "PASS"`, `only_study_level_change == "completion_cap 4096 -> 16384"` | §M1B |
| Manifest cells | 60 | `manifest_60.json` | `total_cells` + per-cell `max_completion_tokens == 16384` | §M1B |
| Recorded / Valid / Failed | 60 / 60 / 0 | `run_records.jsonl` | counts over all rows | §M1B |
| Truncations | 0 | `run_records.jsonl` | count `truncation_status == true` | §M1B |
| Requests / Responses / usage-known | 60 / 60 / 60 | `run_records.jsonl` | `request_issued` / `provider_response_received` / `usage_known` | §M1B |
| Total tokens (all-cell) | 433,741 | `run_records.jsonl` | sum `total_tokens` (157,980 prompt + 275,761 completion) | §M1B |
| Recorded cost | $0.323156 | `run_records.jsonl` | sum `api_cost` (recomputes at live DeepInfra rates) | §M1B |
| Full-v2 valid / trunc / P / R / F1 | 30/30 / 0 / 0.4515 / 0.7750 / 0.5706 | `final_metrics.json` | `arms.full_v2.{valid,truncations,overall.*}` | §M1B |
| Full-v2 mean completion / records | 8,383 / 144 | `final_metrics.json` | `arms.full_v2.completion_tokens.mean` / `serialized_records.mean` | §M1B |
| Sparse-v2 valid / trunc / P / R / F1 | 30/30 / 0 / 0.7211 / 0.8833 / 0.7940 | `final_metrics.json` | `arms.sparse_v2.{valid,truncations,overall.*}` | §M1B |
| Sparse-v2 mean completion / records | 809 / 4.9 | `final_metrics.json` | `arms.sparse_v2.completion_tokens.mean` / `serialized_records.mean` | §M1B |
| Primary effects (Sparse vs Full) | Δvalidity 0.0pp, Δtrunc 0.0pp, Δmean completion −7,573.9, Δmean records −139.1 | `interpretation.json` | `interpretation.primary_controlled_effects.*` | §M1B |
| Result label | CONTROLLED ENCODING COST EFFECT: SUPPORTED | `reports/CONTROLLED_ENCODING_16K_RESULT.md` | §M1B (descriptive; no universal semantic superiority) | §M1B |
| Raw SHA-256 sidecars | 60/60 verified | `runs/raw/*.sha256` | file == sidecar == recorded `raw_response_sha256` | §M1B |
| Six closure gates + audit | ALL PASS (zero calls) | `closure_gates.json` | `gates_all_passed` + `audit.passed` | §M1B |

## 3c. M1 defensive closure (2026-09-13)

Zero scientific API calls; frozen M1A/M1B evidence unchanged. This section
maps the **claims-limitation statements** produced by the closure to their
persisted artifacts. Verifier: `scripts/m1_defensive_closure_stats.py`
(zero API; recomputes `reports/m1_defensive_closure_stats.json`).

| Statement | Value | Canonical artifact | Exact field / aggregation |
|---|---|---|---|
| Independent task units = 6 scenarios; 5 repetitions nested (no n=30 claim) | FROZEN CONVENTION | `reports/M1_STATISTICAL_ANALYSIS.md` §1; `m1_defensive_closure_stats.json` `unit_statement` | analysis unit statement |
| Cross-scenario mean paired ΔF1 (Sparse − Full, n=6 scenario means) | +0.1413 | `m1_defensive_closure_stats.json` | `cross_scenario_paired_effects.f1.mean_of_scenario_means` |
| Cross-scenario mean paired ΔRecall | +0.0556 | `m1_defensive_closure_stats.json` | `cross_scenario_paired_effects.recall.mean_of_scenario_means` |
| Cross-scenario mean paired ΔPrecision | +0.1679 | `m1_defensive_closure_stats.json` | `cross_scenario_paired_effects.precision.mean_of_scenario_means` |
| Cross-scenario mean paired Δcompletion tokens (uniform 6/6 negative) | −7,573.9 | `m1_defensive_closure_stats.json` | `cross_scenario_paired_effects.completion_tokens.mean_of_scenario_means` + `sign_consistency.negative_count == 6` |
| Cross-scenario mean paired ΔAPI cost (uniform 6/6 negative) | −$0.007569 | `m1_defensive_closure_stats.json` | `cross_scenario_paired_effects.api_cost.mean_of_scenario_means` + `sign_consistency` |
| Bootstrap over SCENARIOS (10k, n=6) ΔF1 95% CI | [−0.0220, +0.2932] | `m1_defensive_closure_stats.json` | `bootstrap_over_scenarios.f1.ci95_*` (resampling unit = scenario) |
| Bootstrap over SCENARIOS Δcompletion tokens 95% CI | [−7,695, −7,462] | `m1_defensive_closure_stats.json` | `bootstrap_over_scenarios.completion_tokens.ci95_*` |
| Survivor-bias funnel (M1A @4096: Full-v2 0 valid semantic observations vs Sparse-v2 1) | QUANTIFIED | `m1_defensive_closure_stats.json` | `sensitivity_and_survivor_bias.m1a_survivor_funnel` |
| S006 counterexample (Sparse-v2 R 0.333 / F1 0.278 vs Full-v2 R 0.800 / F1 0.444) | DOCUMENTED | `reports/M1_SCENARIO_LEVEL_ANALYSIS.md` §1 S006 + §2 | pooled micro from `final_metrics.json` per-scenario |
| 15 threats matrix | COMPLETE | `reports/M1_THREATS_TO_VALIDITY_MATRIX.md` | 15 threats, each with 8 fields |
| Raw M1 evidence unchanged | VERIFIED | `git diff` empty for `research/controlled-encoding-ablation-*/` | byte-identical committed evidence |

## 3d. M3 — Graph ablation C0 / C1 / C2 (2026-09-13)

POST-HOC EXPLORATORY DEVELOPMENT-SET GRAPH ABLATION (NOT held-out
confirmation). Evidence directory: `research/graph-c0-c1-c2-01/`. Zero-API
verifier: `scripts/verify_graph_ablation_claims.py` (40/40 PASS).

| Claim | Value | Canonical artifact | Exact field / aggregation |
|---|---|---|---|
| Automatic graph | 144 nodes / 144/144 AST parsed / 562 edges | `graph_verification.json` | all checks pass |
| Graph canonical hash parity | `0a6bf0f7…` | `graph_verification.json` + `canonical_build_hashes.json` | recomputed == recorded |
| Seed algorithm / zones frozen | v1, per-scenario hashes | `seed_zone_identity.json` | seed_ids + zones.{1,2,3} |
| C2 3-hop eligibility | NOT eligible | `three_hop_eligibility.json` | `eligible == false` |
| C0 = audited M1B Sparse-v2 reuse | 30 cells, byte-identical prompts | `c0_reuse.json` | `passed` (6/6 scenario prompt hashes match M1B records) |
| New cells / valid / failed | 90 / 32 / 58 (0 trunc) | `run_records.jsonl` + `final_metrics.json` | totals |
| C1 (Graph Hints) P / R / F1 | 0.8136 / 0.8000 / 0.8067 (30/30 valid) | `final_metrics.json` | `conditions.c1.overall` |
| C1 vs C0 Δprecision / Δrecall / ΔFN | +0.0925 / −0.0833 / +10 | `interpretation.json` | `delta_tables.deltas.c0_to_c1` |
| C2 1-hop compliance / valid | 2/30 / 2 valid (28 mandatory-disclosure-failure) | `final_metrics.json` | `conditions.c2_1hop.per_scenario[*].disclosure_compliance` |
| C2 2-hop compliance / valid | 0/30 / 0 valid | `final_metrics.json` | `conditions.c2_2hop.*` |
| S006 C1 vs C0 F1 / recall | 0.414 vs 0.278 / 0.400 vs 0.333 | `final_metrics.json` | `conditions.c1.per_scenario.*006.pooled_micro` |
| Total tokens / cost | 566,623 / $0.234673 | `final_metrics.json` | `totals.{total_tokens,cost_usd}` |
| Raw SHA-256 sidecars | 90/90 verified | `runs/raw/*.sha256` | file == sidecar == recorded `raw_response_sha256` |
| Six closure gates + audit + graph verification | ALL PASS (zero calls) | `closure_gates.json` | `gates_all_passed`, `audit.passed`, `graph_verification.passed` |
| Classification | GRAPH HINT SIGNAL: MIXED; GRAPH-GATED DISCLOSURE: NOT PROMISING | `reports/M3_GRAPH_RESULTS.md` §8 | interpretation block |

## 4. Token semantics (V7 Table III correction)

| Arm | Paper value | Canonical field | Semantic meaning |
|---|---|---|---|
| Agent | 449,792 | `total_tokens` (sum over 30 rows) | **TOTAL tokens (all-cell)** = prompt 441,348 + completion 8,444 |
| ImpactPlan-v1 | 184,401 | `total_tokens` (sum over 30 rows) | **TOTAL tokens (all-cell)** = prompt 87,287 + completion 97,114 |
| Sparse-v2 | 144,353 | `total_tokens` (sum over 30 rows) | **TOTAL tokens (all-cell)** = prompt 113,880 + completion 30,473 |

**Conclusion:** all three manuscript values are valid recorded **total** tokens
(all-cell), **not** completion tokens. Table III's column/caption must read
**TOTAL TOKENS (all-cell)**.

## 5. Scenario-004 same-cap observation (cap = 4096)

| Claim | Value | Canonical artifact | Verifier check |
|---|---|---|---|
| v1 completions | 5/5 truncated at exactly 4096 | `reports/scientific-stagec-djangocms-study-01/run_records.jsonl` (rows scenario `...-004`, arm `impact_plan`) | §[5] |
| v2 completions | 5/5 completed, 0 truncations | `reports/scientific-stagec-djangocms-impactplan-v2-01/run_records.jsonl` (rows scenario `...-004`) | §[5] |
| v2 completion range | 874 – 1,525 (mean 1133.20) | `final_metrics.json` `per_scenario.djangocms-external-validity-004.completion_tokens.{min,max,mean}` | §[5] |

## 6. Scenario-006 reconciliation (5 valid cells)

Gold set: `cms/models/pluginmodel.py`, `cms/admin/placeholderadmin.py`, `cms/utils/plugins.py`.

| File | Gold? | Selection frequency | Verifier check |
|---|---|---|---|
| `cms/admin/forms.py` | no | 5/5 | §[6] |
| `cms/models/pluginmodel.py` | yes | 5/5 | §[6] |
| `cms/plugin_rendering.py` | no | 5/5 | §[6] |
| `cms/admin/placeholderadmin.py` | yes | 2/5 | §[6] |
| `cms/utils/placeholder.py` | no | **1/5 (sporadic FP)** | §[6] |
| `cms/utils/plugins.py` | yes | 0/5 (missed) | §[6] |

Pooled: TP/FP/FN = 7/11/8, P = 0.388889, R = 0.466667, F1 = 0.424242, full
recall = 0/5. The additional sporadic FP beyond the five persistent rows
(`forms` 5 + `plugin_rendering` 5 = 10) is **`cms/utils/placeholder.py`**
(1/5), which is why pooled FP = 11.

## 7. Failed v2 cell

| Claim | Value | Canonical artifact |
|---|---|---|
| Run | `stgc-v2-djangocms-external-validity-002-impact_plan_v2-r3` (scenario 002, rep 3) | `reports/scientific-stagec-djangocms-impactplan-v2-01/run_records.jsonl` |
| Reason | `impact_plan_invariant_failure: v_missing_validation_reason: cms/models/__init__.py` — `cms/models/__init__.py` emitted as VALIDATE with no cited supporting evidence, so the frozen semantic invariant failed closed | `run_records.jsonl` `failure_category`; raw response `runs/raw/stgc-v2-...-r3.txt` |

## 8. Serialized-record reduction (record count, not tokens)

| Claim | Value | Canonical artifact |
|---|---|---|
| Candidate universe | 144 | `manifest_30.json` `universe_count` |
| Mean explicit decisions | 6.344828 | `run_records.jsonl` `emitted_decisions` (29 valid cells) |
| Fraction emitted | 4.41% (6.344828 / 144) | recomputed |
| **Record-count reduction** | **95.6%** (1 − fraction) | recomputed |

This is a **serialized file-decision record count reduction**, not a token
reduction.

## 9. Raw-response hash verification

| Claim | Value | Canonical artifact |
|---|---|---|
| Sparse-v2 raw SHA-256 | 30/30 PASS | `runs/raw/*.txt` vs `runs/raw/*.sha256` vs `run_records.jsonl` `raw_response_sha256` |

## 10. 16K / 8192 diagnostics (single-case, post-hoc)

| Claim | Value | Canonical artifact |
|---|---|---|
| 16K diagnostic (scenario 004, 1 run) | completion 10,650; latency 179.172 s; cost $0.01148; `CASE_A_TERMINATES` | `reports/scientific-stagec-djangocms-impactplan-16k-diagnostic-01/diagnostic.json` |
| 8192 probe (scenario 004, 1 run, non-study) | truncated at cap 8192, failed | `reports/scientific-stagec-djangocms-impactplan-cap-ablation-01/costprobe_8192.json` |

Do **not** generalize the 16K result beyond this single scenario/case.

## 11. 4096 cap provenance

Classification: **B** — the protocol freezes 4096 as the ImpactPlan completion
budget; no stronger contemporaneous rationale (e.g., a provider maximum) is
documented. Sources: `docs/PREMAIN_FEASIBILITY_PREREGISTRATION.md`,
`reports/RESEARCH_DECISION_ARCHIVE.md` (entry 3),
`src/benchmark/selection/impact_planner.py` (`IMPACT_PLAN_MAX_COMPLETION_TOKENS = 4096`).

---

## 12. Qwen3-32B cross-model robustness replication (POST-HOC)

Evidence directory: `reports/scientific-stagec-djangocms-qwen3-32b-crossmodel-01/`
(immutable; `run_records.jsonl`, `manifest_60.json`, `final_metrics.json`,
`cross_model_agreement.json`, `runs/raw/*` + `.sha256`).

| Claim | Value | Canonical artifact | Verifier |
|---|---|---|---|
| Recorded cells | 60/60 | `run_records.jsonl` | `verify_qwen3_32b_crossmodel_claims.py` |
| v1 valid / truncations | 2/30 / 24 | `run_records.jsonl` (`arm=="impact_plan"`) | same |
| v2 valid / truncations | 21/30 / **6** | `run_records.jsonl` (`arm=="impact_plan_v2"`); truncation classifier (2026-09-11 accounting audit) | same |
| v2 pooled P / R / F1 / FNR | 0.360 / 0.621 / 0.456 / 0.379 | `final_metrics.json` | same |
| v2 full-recall rate | 0.238 | `final_metrics.json` | same |
| Live cost (all 60) | $0.054028 | `final_metrics.json` (`totals.live_api_cost_usd`) | same |
| API requests issued | 60 (52 usage-bearing) | `final_metrics.json` (`totals.requests_issued`) | same |
| Cross-model Sparse-v2 Jaccard | 102 pairs; mean 0.284 / median 0.231 | `cross_model_agreement.json` + `reports/QWEN3_32B_CROSSMODEL_AGREEMENT.{md,csv}` | same |
| Reasoning disabled | `reasoning.enabled=false`; `reasoning_tokens==0` | `endpoint_freeze.json`, `capability_probes.json`, every RunRecord | same |
| Raw SHA verification | 60/60 (where raw exists) | `runs/raw/*` vs `raw_response_sha256` | same |

> **Accounting correction (2026-09-11):** v2 truncations corrected 0 → **6**
> (S004 r1–r5, S008 r2; `finish_reason=length` + unterminated raw). Valid-run
> P/R/F1 unchanged (those cells were already failed). `model_calls` (52) is
> usage-bearing; all 60 cells issued exactly one request
> (`totals.requests_issued == 60`). Details:
> `reports/scientific-stagec-djangocms-qwen3-32b-crossmodel-01/ACCOUNTING_CORRECTION_NOTE.md`.

Recompute: `python scripts/verify_qwen3_32b_crossmodel_claims.py` (exit 0 =
PASS). This is a **descriptive** post-hoc replication; no equivalence or
significance claim is supported. Historical Qwen3-Coder-480B-A35B-Instruct evidence is unchanged
and remains the primary manuscript evidence.


## 13. Qwen3-Coder-30B-A3B-Instruct cross-model / cross-provider robustness replication (POST-HOC)

Model: **Qwen3-Coder-30B-A3B-Instruct** (OpenRouter slug
\qwen/qwen3-coder-30b-a3b-instruct\) @ OpenRouter / SiliconFlow
(\siliconflow/fp8\), model-native non-thinking, temperature 0, cap 4096,
graph OFF. Study \scientific-stagec-djangocms-qwen3-coder-30b-a3b-crossmodel-01\.
Evidence:
eports/scientific-stagec-djangocms-qwen3-coder-30b-a3b-crossmodel-01/(manifest_60.json, run_records.jsonl, runs/raw/*.txt + .sha256,
endpoint_freeze.json, provider_capability_snapshot.json,
capability_probes.json, FROZEN_INPUT_PARITY.json, final_metrics.json,
cross_model_agreement.json, ACCOUNTING_CORRECTION_NOTE.md, RESULTS.md).

- 60 cells recorded / 60 unique run IDs / 2 arms / 6 scenarios / 5 reps.
- 45 valid / 15 failed / 11 truncations (all v1); v1 17/30 valid, v2 28/30
  valid (0 truncations).
- v2 pooled P 0.5556 / R 0.6881 / F1 0.6148 / FNR 0.3119; full-recall 10/28.
- Requests issued 60, responses 59, usage-known 59 / usage-unknown 1,
  transport failures 1. Recorded 301,146 total tokens and \.041518 live
  cost are LOWER BOUNDS (one transport-failure cell has unknown billed usage;
  never silently zeroed).
- DIRECTIONALLY REPLICATED (descriptive): v2 validity 0.933 > v1 0.567 and
  v2 truncation 0.000 < v1 0.367.
- Cross-model Sparse-v2 agreement vs historical
  Qwen3-Coder-480B-A35B-Instruct: 135 pairs, mean 0.491 / median 0.429
  (descriptive; eports/QWEN3_CODER_30B_A3B_CROSSMODEL_AGREEMENT.{md,csv}\).

Recompute: \python scripts/verify_qwen3_coder_30b_a3b_crossmodel_claims.py(exit 0 = PASS). This is a **descriptive** post-hoc cross-model /
cross-provider replication; no equivalence, significance, or superiority
claim is supported. Historical Qwen3-Coder-480B-A35B-Instruct evidence is
unchanged and remains the primary manuscript evidence.

## 14. M4A-3/P1 — Real-commit FULL-v2 vs SPARSE-v2 held-out evaluation

Model: **Qwen3-Coder-480B-A35B-Instruct** (`qwen/qwen3-coder`) @ OpenRouter /
DeepInfra (`deepinfra/turbo`, fp4), temperature 0, **completion cap 16384 for
BOTH arms** (controlled M1B replication), Graph OFF, native `json_schema`.
Study `real-commit-p1-full-v2-vs-sparse-v2-01`. Evidence:
`research/real-commit-p1-01/` (manifest_60.json, run_records.jsonl,
runs/raw/*.txt + .sha256, endpoint_freeze.json, capability_probes.json,
final_metrics.json, closure.json), `reports/REAL_COMMIT_M4A3_P1_RESULT.md`.

- 10 independent HELD_OUT_TEST tasks × 2 arms × 3 nested repetitions = **60
  cells**; independent n = 10 (repetitions are nested observations, NOT
  independent examples).
- 60/60 valid / 0 failed / 0 truncations; 60 calls; 295,410 prompt + 271,345
  completion = **566,755 total tokens**; 1,916 s; recorded cost
  **$0.359964** (< $1.50 frozen ceiling).
- full_v2 micro P 0.338843 / R 0.369369 / F1 0.353448 / FNR 0.630631;
  sparse_v2 micro P 0.386667 / R 0.261261 / F1 0.311828 / FNR 0.738739.
- Task-level paired deltas + bootstrap over **10 tasks** (10k, seed
  20260914): delta F1 −0.008822 [−0.129720, +0.118938], delta precision
  +0.034241 [−0.046795, +0.120882], delta recall −0.064160 [−0.196111,
  +0.064444], delta completion −7,847.9 [−8,136.0, −7,596.8], delta cost
  −$0.023531 [−0.024396, −0.022778].
- **Serialized decision records (corrected 2026-09-14):** Full-v2 mean
  **144.0**, Sparse-v2 mean **4.07**, paired delta **−139.9 [−143.3,
  −137.0]** — recomputed from the persisted raw responses
  (`research/real-commit-p1-01/final_metrics_serialization_corrected.json`).
  The originally published "Records mean" (4.03 / 2.50) and delta (−1.540)
  were the predicted REGENERATE **write-set size** (`len(decoded_write_set_ids)`),
  NOT serialized decision counts. Correction:
  `reports/REAL_COMMIT_M4A3_P1_SERIALIZATION_METRIC_CORRECTION.md`.
- The controlled encoding-cost effect replicates **directionally** (completion
  and cost deltas exclude zero); selection-quality deltas straddle zero — **no
  semantic arm-superiority claim**. The historical diff is an **OBSERVED
  CHANGE-SET PROXY**, never semantic ground truth; no comparison with any
  published LocAgent Acc@K.

Recompute: `python scripts/execute_real_commit_p1.py metrics` (after the run)
and `python scripts/verify_real_commit_p1_gates.py` (ZERO-API gates + audit).

## Closing notes

- All verifier checks above are implemented in \scripts/verify_paper_claims.py\,
  \scripts/verify_qwen3_32b_crossmodel_claims.py\, and
  \scripts/verify_qwen3_coder_30b_a3b_crossmodel_claims.py\; each exits 0 only
  when its evidence is internally consistent.
- No frozen artifact, metric, prompt, or schema was modified by this task.
- Verification: \python scripts/verify_paper_claims.py\ (exit 0 = PASS).
