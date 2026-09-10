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

## Closing notes

- All verifier checks above are implemented in `scripts/verify_paper_claims.py`
  and exit 0 only when evidence is internally consistent.
- No frozen artifact, metric, prompt, or schema was modified by this task.
- Verification: `python scripts/verify_paper_claims.py` (exit 0 = PASS).