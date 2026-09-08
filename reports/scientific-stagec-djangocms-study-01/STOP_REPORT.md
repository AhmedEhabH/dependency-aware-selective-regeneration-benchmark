# STOP REPORT — djangoCMS External-Validity FINAL 60-RUN SCIENTIFIC STUDY
# (POST-STUDY EVIDENCE CLOSURE + REPORT CORRECTION)

**STUDY_ID:** `scientific-stagec-djangocms-01`
**Date (UTC):** 2026-09-08
**Type:** FINAL SCIENTIFIC STUDY (recorded; NOT a release; NO stable tag move)
**Closure type:** REPORTING / EVIDENCE / DOCUMENTATION closure ONLY — ZERO new scientific API calls; raw evidence immutable.

---

## 1. Execution Identity

- Implementation/OpenCode model: the OpenCode execution environment reports `deepseek/deepseek-v4-flash-0731`; the task authorization header declared `openrouter/deepseek/deepseek-v3.2` (DEFAULT). **The two are inconsistent; both recorded truthfully; neither is asserted as authoritative for scientific inference.**
- Scientific model: `qwen/qwen3-coder`
- Scientific provider: DeepInfra pinned through OpenRouter (`deepinfra/turbo`), fallback OFF, temperature 0
- Branch: `research/djangocms-external-validity-prep-01`
- HEAD (full): `ddb5f67268e5a62d625af3e903e6ad98074cf297` (pre-correction); corrected closure commit printed at the end
- Remote HEAD (full): `ddb5f67268e5a62d625af3e903e6ad98074cf297` (pre-correction parity YES)
- Tree state: CLEAN (0 uncommitted changes) at start
- Wiring tag: `stagec-djangocms-study-wiring-verified-01` (verified ancestor of HEAD; not moved)

### Git provenance (historical vs live — Section 1)

| Claim | Commit | What it contains |
| --- | --- | --- |
| Older STOP_REPORT claim | `0c110bb…` | Stale STOP_REPORT written before the final two commits; `0c110bb` IS the **frozen scientific-results commit** (60 raw records + manifest + initial reports). |
| Embedded branch ref / intermediate | `06d1dd5…` | Post-study evidence/report commit (STOP_REPORT + evidence ZIP + zip builder). |
| Later console report claim | `ddb5f67…` | Project-export script commit; was live HEAD at closure start. |
| **Current verified live state** | `ddb5f67268e5a62d625af3e903e6ad98074cf297` | Verified via `git rev-parse HEAD` / `origin/…` (parity YES) before this closure. The corrected-closure commit is created and pushed at the end of this task; the terminal Stop Report prints the actual post-commit HEAD. |

Frozen scientific results (manifest + 60 raw records) live in commit `0c110bb1e42788ea68f0c23e70a729e695153a46`. Post-study report corrections: `06d1dd5` (first STOP_REPORT+ZIP), `ddb5f67` (export script), and the new corrected-closure commit produced by this task. No hash was invented for any historical artifact.

## 2. Why I Am Stopping

**STOP FOR GPT-5.6 SOL FINAL INDEPENDENT AUDIT.** The frozen 60-run scientific study is complete and unchanged; documentation/report corrections are complete; the same six closure gates + audit PASS; ZERO new scientific API calls were made.

## 3. Scientific study frozen state (immutability)

- **60/60 manifest cells unchanged** (records set == manifest run_ids, 60 unique).
- Raw scientific evidence hashes recomputed and **verified identical** before and after this closure (71 files: manifest_60.json, run_records.jsonl, 60 raw run JSONs, 6 scenario YAMLs, hidden gold, candidate universe, dependency graph) — persisted in `reports/scientific-stagec-djangocms-study-01/raw_evidence_hashes.json`.

## 4. Pre-Run Validation + Gates

- Pre-run validation PASS (8/8): wiring tag ancestor; universe == 144 frozen (hash `43f4279b…`); missing/extra empty; gold ⊂ universe; six final scenarios; hidden-gold isolation.
- EXACT six deterministic gates + Independent Audit PASS pre (`runtwiring_gates.json`) and post (`closure_gates.json`); zero scientific calls.
- Frozen manifest before first call; never changed.

## 5. Valid/Failed Accounting (recomputed from raw evidence — Section 2/3)

- Total: **60 recorded** = **31 valid** + **29 failed**
- `iterative_repository_agent`: **25 / 30 valid**, 5 / 30 failed (valid rate 0.8333)
- `impact_plan`: **6 / 30 valid**, 24 / 30 failed (valid rate 0.2000)

### Failure taxonomy (exact, from raw evidence)

| Arm | Failure Type | Count |
| --- | --- | ---: |
| impact_plan | 4096-cap completion truncation (`finish_reason=length`, `completion_tokens=4096` — verified in raw evidence) | **19** |
| impact_plan | unknown/non-universe path rejection (fail-closed) | 3 |
| impact_plan | provider HTTP 429 | 1 |
| impact_plan | harness defect (`ValidationObligation.kind` out-of-enum → ValueError) | 1 |
| iterative_repository_agent | provider HTTP 429 | 4 |
| iterative_repository_agent | empty-selection fail-closed | 1 |
| **Total failed** | | **29** |

> Correction: the previous report incorrectly stated 20 ImpactPlan truncations. Raw evidence confirms **19** (recomputed; every one has `finish_reason=length` and `completion_tokens=4096`).

## 6. VALID-RUN HEADLINE TABLE (MICRO-AGGREGATED over VALID runs)

| Arm | Selected | TP | FP | FN | Precision | Recall | F1 | FNR | Tokens | Model Calls | Time | Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| iterative_repository_agent | 147 | 95 | 52 | 18 | 0.6463 | 0.8407 | 0.7308 | 0.1593 | 432057 | 198 | 2216.0 | 0.135316 |
| impact_plan | 34 | 23 | 11 | 2 | 0.6765 | 0.9200 | 0.7797 | 0.0800 | 32560 | 6 | 382.4 | 0.018714 |

> Agent valid = 25 cells; ImpactPlan valid = 6 cells. **Severe missing-data asymmetry — DO NOT claim ImpactPlan has higher overall accuracy based on this table.**

## 7. OPERATIONAL RELIABILITY + ALL-CELL OPERATIONAL TABLE

| Arm | Valid | Failed | Valid Rate | All-Cell Tokens | All-Cell Model Calls | All-Cell Time | Recorded Cost |
|---|---:|---:|---:|---:|---:|---:|---:|
| iterative_repository_agent | 25 | 5 | 0.8333 | 449792 | 206 | 2265.517 | 0.140850 |
| impact_plan | 6 | 24 | 0.2000 | 184401 | 28 | 2658.733 | 0.123298 |

ImpactPlan relative to Agent (all-cell): tokens **−59.00%** · model calls **−86.41%** · recorded cost **−12.46%** · measured total latency **+17.36%**.

## 8. Macro (VALID-run macro statistics; separate from all-cell)

- **Agent:** mean/median P 0.6747/0.8333; R 0.8095/1.0; F1 0.7121/0.7692; **full-recall rate 0.60**; selected mean/median 5.88/5 (min 2, max 10); tokens mean 17282 / median 17675; calls mean 7.92 / median 8; latency mean 88.64 s / median 47.27 s (min 11.09, max 252.0); cost mean $0.005413 / median $0.005476. Outlier (valid): 006-agent-r2 (252.0 s).
- **ImpactPlan:** mean/median P 0.6591/0.6667; R 0.9429/1.0; F1 0.7657/0.8; **full-recall rate 0.6667**; selected mean/median 5.67/6 (min 2, max 8); tokens mean 5427 / median 5436; calls mean/median 1.0; latency mean 63.73 s / median 51.48 s (min 16.58, max 165.70); cost mean $0.003119 / median $0.003003.

## 9. Per-scenario (valid repetitions pooled; N/A where 0/5 valid)

| Scenario | Agent valid | ImpactPlan valid | Agent F1 (valid micro) | ImpactPlan F1 |
| --- | ---: | ---: | ---: | ---: |
| djangocms-external-validity-002 | 1/5 | 1/5 | 0.0000 | 0.6667 |
| djangocms-external-validity-004 | 5/5 | 0/5 (N/A) | 0.9524 | N/A |
| djangocms-external-validity-005 | 5/5 | 1/5 | 1.0000 | 0.8000 |
| djangocms-external-validity-006 | 4/5 | 0/5 (N/A) | 0.3333 | N/A |
| djangocms-external-validity-007 | 5/5 | 1/5 | 0.7692 | 0.8000 |
| djangocms-external-validity-008 | 5/5 | 3/5 | 0.5714 | 0.7742 |

Full per-scenario tables in `reports/FINAL_BENCHMARK_RESULTS.md` §7.

## 10. Output-budget limitation

- **Agent:** up to 8 calls × 1024 = **8192 completion tokens across sequential calls**.
- **ImpactPlan:** 1 call × 4096 = **4096 completion tokens in one structured response**.
- Budgets are NOT directly interchangeable; the frozen 4096 cap may confound representational scalability with completion-budget sufficiency.
- **Serialization measurement (ZERO API):** minimal schema-valid ImpactPlan JSON over the 144 paths = **17,364 bytes / 17,364 chars**; rough token estimate (project heuristic, ESTIMATE ONLY) ~**4,341** tokens — already on the order of the 4096 cap before rationales/evidence. All 19 truncated responses: `finish_reason=length`, `completion_tokens=4096`. Successful ImpactPlan completions: min 920 / median 2165 / max 3750 tokens. Exact qwen3-coder tokenizer not locally available; NOT downloaded; no API call.

## 11. Cost

- Recorded API cost across persisted study records: **$0.264148**.
- Actual spend is slightly higher: one harness-defect scientific model call (007-impact-r1) lacks complete cost provenance (≈ $0.003 by per-token rate; not presented as measured fact).
- Ceiling $0.50 → **COST_LOCK=PASS** (recorded + missing ≈ $0.267 << $0.50).

## 12. Scientific interpretation

**Supported:** ImpactPlan strongly reduces selection-stage inference work (all-cell calls 206→28, tokens −59%); poor operational completion under the frozen 4096 single-response cap (19/30 truncated; ImpactPlan operational valid rate 20% vs Agent 83.33%); when ImpactPlan completed, valid-run recall high but severe imbalance prevents between-arm accuracy-superiority claim; all-cell savings coexist with worse total latency (+17.4%); the study cannot disentangle representation scalability from the cap.
**Not claimed:** ImpactPlan universally more accurate/faster; end-to-end selective-regeneration proven; arbitrary large-repo generalization; truncation proven inherent (vs partly cap-induced).

## 13. Ablation proposal

`reports/DJANGOCMS_IMPACTPLAN_CAP_ABLATION_PROPOSAL.md` — POST-HOC EXPLORATORY ABLATION (cap 8192, ImpactPlan only, 30 runs) documented, **NOT RUN**.

## 14. Documentation updated (this closure)

- reports/FINAL_BENCHMARK_RESULTS.md (corrected: 19 truncations; valid/all-cell separation; failure table; output-budget section; serialization analysis; N/A per-scenario; VALID/FAILED definitions)
- reports/FINAL_BENCHMARK_RESULTS.csv (recomputed)
- reports/BENCHMARK_VALIDITY_AND_LIMITATIONS.md (dedicated output-budget + serialization sections)
- reports/BENCHMARK_REPRODUCIBILITY_INDEX.md
- reports/scientific-stagec-djangocms-study-01/STOP_REPORT.md (this file)
- reports/RESEARCH_TRUTH_MATRIX.md
- reports/DJANGOCMS_IMPACTPLAN_CAP_ABLATION_PROPOSAL.md (new)
- reports/scientific-stagec-djangocms-study-01/closure_recompute.json, serialization_size_analysis.json, raw_evidence_hashes.json (new verification artifacts)
- DECISION_LOG.md, SYSTEM_STATE.md, TODO.md, README.md

## 15. Closure gates + Audit

- Gate 1 Dataset Validation: PASS (60 raw records + manifest integrity)
- Gate 2 Prompt Validation: PASS (frozen scenario/prompt hashes unchanged)
- Gate 3 Pipeline Smoke Test: PASS (mock/deterministic only)
- Gate 4 Dry Run: PASS (zero scientific API calls)
- Gate 5 Integration Test: PASS (aggregate reports trace back to raw records)
- Gate 6 Metric Verification: PASS (key totals independently recomputed; reports match raw records)
- Independent Audit: PASS (19-vs-20 truncation corrected to 19; valid/failed arm counts confirmed; valid-only vs all-cell separation; cost wording; output-budget limitation; Git provenance documented; no raw scientific evidence modification)

## 16. Git

- Branch: `research/djangocms-external-validity-prep-01`
- Corrected-closure commit: printed at the end of the terminal Stop Report (created + pushed this closure)
- Parity: YES (verified post-push) | Tree: CLEAN
- No merge to main; no new tags; `v0.11.0-benchmark-complete` NOT created.

## 17. Evidence ZIP

Corrected compact evidence ZIP rebuilt after this closure (see terminal Stop Report for filename/size/SHA-256).

## 18. Next Action

**STOP FOR GPT-5.6 SOL FINAL INDEPENDENT AUDIT.** Do NOT run the 8192 ablation; do NOT merge main; do NOT create `v0.11.0-benchmark-complete`; do NOT start another experiment.