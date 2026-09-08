# STOP REPORT — djangoCMS External-Validity FINAL 60-RUN SCIENTIFIC STUDY

**STUDY_ID:** `scientific-stagec-djangocms-01`
**Date (UTC):** 2026-09-08
**Type:** FINAL SCIENTIFIC STUDY (recorded; NOT a release; NO stable tag move)

---

## 1. Execution Identity

- Implementation/OpenCode model: authorization declares `openrouter/deepseek/deepseek-v3.2` (DEFAULT); the OpenCode execution environment reports `deepseek/deepseek-v4-flash-0731` (openrouter/deepseek/deepseek-v4-flash-0731). **The two are inconsistent; both recorded truthfully.**
- Scientific model: `qwen/qwen3-coder`
- Scientific provider: DeepInfra pinned through OpenRouter (`deepinfra/turbo`), fallback OFF, temperature 0
- Branch: `research/djangocms-external-validity-prep-01`
- HEAD (full): `0c110bb1e42788ea68f0c23e70a729e695153a46`
- Remote HEAD (full): `0c110bb1e42788ea68f0c23e70a729e695153a46`
- Parity: **YES**
- Tree state: **CLEAN** (0 uncommitted changes)
- Wiring tag: `stagec-djangocms-study-wiring-verified-01` (verified ancestor of HEAD; not moved)

## 2. Why I Am Stopping

**STOP FOR GPT-5.6 SOL INDEPENDENT AUDIT.** The frozen 60-run scientific study completed; all evidence, reports, and documentation committed and pushed; the same six closure gates + audit PASS. Per the authorization, do NOT start any new scientific study and do NOT tag `v0.11.0-benchmark-complete` until GPT-5.6 Sol independently audits the 60-run evidence.

## 3. Pre-Run Validation (Section B) + Gates (Section B/R)

- Pre-run validation: PASS (8/8) — wiring tag ancestor; runtime universe == frozen 144-path universe (canonical hash `43f4279bdf228745b1f6b289c81cda141b089ab5be4f4af63bb8f39f837c4410`); missing/extra paths empty; all gold paths in universe; final scenarios exactly `djangocms-external-validity-002/004/005/006/007/008`; hidden gold evaluation-only; old historical scenarios never model-facing.
- EXACT six deterministic gates + Independent Audit: **PASS** before the study (`runtwiring_gates.json`) and again after closure (`closure_gates.json`). Zero scientific calls in all gates/audits.
- Frozen 60-cell manifest (`manifest_60.json`) persisted BEFORE the first scientific call and never changed.

## 4. Scientific Configuration

- Model `qwen/qwen3-coder` @ `deepinfra/turbo` (DeepInfra pinned through OpenRouter), fallback OFF, temperature 0.
- Caps: `iterative_repository_agent` = 1024; `impact_plan` = 4096 completion tokens.
- Scope: SELECTION ONLY (no regeneration / patching / repair / migration / functional execution).
- Retry policy: frozen `max_transient_retries=1` (unchanged).
- Workflow timeout: 600 s/cell; operational pacing 15 s inter-cell (scheduling only, not a scientific input).

## 5. Study Completion

- Manifest cells: **60 / 60** recorded (6 scenarios × 2 arms × 5 repetitions).
- Valid (succeeded) cells: **31**
- Failed cells: **29** (recorded; none rerun; no replacement runs; no run 61)

### Failed-run accounting

| Class | Count | Detail |
| --- | ---: | --- |
| ImpactPlan `finish_reason=length` @ frozen 4096 cap (truncated JSON) | 20 | `impact_plan_planner_error: planner response not JSON (finish_reason=length)` |
| ImpactPlan unknown-path hallucination (fail-closed) | 3 | `planner produced unknown paths: [cms/migrations/..., cms/tests/...]` |
| Provider 429 (DeepInfra shared-pool rate limit) | 5 | `OpenRouter HTTP 429: Provider returned error` (4 agent + 1 impact) |
| Agent empty selection after exploration | 1 | `iterative_agent: no paths selected after exploration` |
| Harness defect (model returned out-of-enum obligation kind) | 1 | `ValueError: ValidationObligation.kind unknown: ui_state_reflection` (1 model call consumed, ~$0.003 not recorded) |

## 6. MANDATORY HEADLINE TABLE (MICRO-AGGREGATED over VALID runs)

| Arm | Selected | TP | FP | FN | Precision | Recall | F1 | FNR | Tokens | Model Calls | Time | Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| iterative_repository_agent | 147 | 95 | 52 | 18 | 0.6463 | 0.8407 | 0.7308 | 0.1593 | 432057 | 198 | 2216.0 | 0.135316 |
| impact_plan | 34 | 23 | 11 | 2 | 0.6765 | 0.9200 | 0.7797 | 0.0800 | 32560 | 6 | 382.4 | 0.018714 |

> Agent = 25 valid runs; ImpactPlan = 6 valid runs. **Severe missing-data asymmetry: ImpactPlan's 24/30 failed cells mean its micro-metrics describe only the survivor subset and are NOT comparable to Agent's as equal-evidence estimates. No between-arm accuracy claim is made.**

## 7. Macro per-run statistics (valid runs; separate from MICRO)

- Agent: mean P 0.6747 / median P 0.8333; mean R 0.8095 / median R 1.0; mean F1 0.7121 / median F1 0.7692; full-recall rate 0.60; selected-set mean 5.88 / median 5 / min 2 / max 10; tokens mean 17282 / median 17675; calls mean 7.92 / median 8; latency mean 88.6 s / median 47.3 s / min 11.1 / max 252.0; cost mean $0.005413 / median $0.005476.
- ImpactPlan: mean P 0.6591 / median P 0.6667; mean R 0.9429 / median R 1.0; mean F1 0.7657 / median F1 0.8; full-recall rate 0.6667; selected-set mean 5.67 / median 6 / min 2 / max 8; tokens mean 5427 / median 5436; calls mean 1.0; latency mean 63.7 s / median 51.5 s / min 16.6 / max 165.7; cost mean $0.003119 / median $0.003003.

## 8. Per-scenario tables (pooled across valid repetitions)

See `reports/FINAL_BENCHMARK_RESULTS.md` §3. Highlights: Agent perfect on 005 (5/5 F1=1.0) and near-perfect on 004 (F1 0.9524); Agent F1 0.7692 (007), 0.5714 (008), 0.3333 (006), 0.0 (002, 1 valid run); ImpactPlan valid cells only on 002 (1), 005 (1), 007 (1), 008 (3).

## 9. Scientific totals

- Total recorded scientific model calls: **234**
- Total recorded scientific tokens: **634,193**
- Total recorded API cost: **$0.264148** (plus ~$0.003 unrecorded harness-defect call in 007-impact-r1)
- Total measured latency (recorded cells): **4,924.3 s** (valid runs 2,598.4 s)
- Cost ceiling: **$0.50** → **COST_LOCK=PASS** (actual recorded $0.264148)

## 10. Cost lock (Section G)

- costprobe-02 raw projected $0.239850 / conservative $0.299813 (≤ $0.50) → COST_LOCK=PASS (probe evidence, NON-STUDY)
- Actual study recorded cost **$0.264148** ≤ $0.50 ceiling → **COST_LOCK=PASS** (maintained via per-run ledger; no mid-study cost stop needed)

## 11. Previous probes (Section E)

- `scientific-stagec-djangocms-costprobe-01` and `-02` remain **NON-STUDY** diagnostic/cost-planning evidence only; excluded from the 60 scientific results.

## 12. Interpretation (Section N honored)

- Correctness before efficiency. ImpactPlan efficiency is not claimed as an advantage: its valid subset is small and its operational failure rate (24/30) dominates.
- Lower precision/recall, failed cells, large selected sets, and latency outliers are all reported, not hidden.
- No claim that ImpactPlan is more accurate. No general large-repository superiority claim. No end-to-end selective-regeneration claim.
- This study measures Stage-C selection behavior only.

## 13. Evidence (Section S / ZIP)

- Result evidence ZIP: `reports/STAGEC_DJANGOCMS_STUDY_01_RESULT_EVIDENCE.zip`
- Raw evidence: `reports/scientific-stagec-djangocms-study-01/` (manifest_60.json, run_records.jsonl, runs/*.json × 60, checkpoints 10–60, prevalidation.json, runtwiring_gates.json, closure_gates.json, final_metrics.json)
- Reports: `reports/FINAL_BENCHMARK_RESULTS.{md,csv}`, `reports/BENCHMARK_VALIDITY_AND_LIMITATIONS.md`, `reports/BENCHMARK_REPRODUCIBILITY_INDEX.md`, `reports/RESEARCH_TRUTH_MATRIX.md`
- Docs: `DECISION_LOG.md` (D055), `SYSTEM_STATE.md`, `TODO.md`, `README.md`

## 14. Git (Section Q)

- Branch: `research/djangocms-external-validity-prep-01`
- Full HEAD: `0c110bb1e42788ea68f0c23e70a729e695153a46`
- Full remote HEAD: `0c110bb1e42788ea68f0c23e70a729e695153a46`
- Parity: **YES** | Tree: **CLEAN**
- No merge to main; `v0.11.0-benchmark-complete` NOT created.

## 15. Next Action

**STOP FOR GPT-5.6 SOL INDEPENDENT AUDIT of the 60-run evidence.**
Do NOT start any new scientific study. Do NOT tag `v0.11.0-benchmark-complete`.