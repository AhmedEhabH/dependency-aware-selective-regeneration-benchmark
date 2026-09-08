# Paper Writing Handoff

**Purpose:** start the manuscript phase from the frozen benchmark evidence
without reconstructing earlier sessions. The benchmark is **COMPLETE** at
`v0.11.0-benchmark-complete`; current phase is **paper / figures / supervisor
review**; **zero scientific runs remain**.

## 1. Exact research scope

- **Selection stage only.** What was measured: which repository-relative `.py`
  paths each treatment predicts must change, scored against
  source-adjudicated hidden gold applied after inference.
- **NOT measured in these treatments:** Functional Correctness, Preservation,
  Architecture Compliance, or end-to-end regeneration outcomes. Do not claim
  them.
- Model: `qwen/qwen3-coder` pinned to DeepInfra through OpenRouter
  (`deepinfra/turbo`), fallback OFF, temperature 0.

## 2. Study inventory

| Study | Cells | Status |
|---|---|---|
| Todo Stage-C smoke (`scientific-stagec-selection-01`) | 30 | Frozen, exploratory component study |
| Todo Stage-C held-out (`scientific-stagec-heldout-01`) | 60 | Frozen, follow-up |
| Todo v1.1 end-to-end (`exp-20260906-v11`) | 30 | Frozen, NO-GO (0/30 functional passes) |
| djangoCMS primary (`scientific-stagec-djangocms-01`) | 60 | Frozen, primary selection study |
| djangoCMS ImpactPlan-v2 (`scientific-stagec-djangocms-impactplan-v2-01`) | 30 | Frozen, POST-HOC / EXPLORATORY (audited) |

Studies are kept separate; **no 90-cell pooling**.

## 3. Final frozen metrics

### djangoCMS primary (valid-run micro; severe missing-data asymmetry)

| Arm | Valid / 30 | Precision | Recall | F1 |
|---|---|---|---|---|
| iterative_repository_agent | 25 | 0.6463 | 0.8407 | 0.7308 |
| impact_plan (v1) | 6 | 0.6765 | 0.9200 | 0.7797 |

### djangoCMS ImpactPlan-v2 (30 cells; POST-HOC / EXPLORATORY)

| Metric | Value |
|---|---|
| Recorded / Valid / Failed | 30 / 29 / 1 |
| Truncations | 0 |
| TP / FP / FN | 103 / 36 / 16 |
| Precision / Recall / F1 | 0.741007 / 0.865546 / 0.798450 |
| FNR | 0.134454 |
| Full-recall rate | 18 / 29 = 0.620690 |
| Total tokens / calls / cost | 144,353 / 30 / $0.064634 |
| Latency (all-30) | 391.437 s (mean 13.270 s) |

### Same-cap scenario-004 (cap = 4096)

- Historical ImpactPlan-v1: **5/5 truncated**.
- ImpactPlan-v2: **5/5 completed**, 874–1,525 completion tokens.

### Weakest v2 scenario

- Scenario 006: precision ≈ 0.389, recall ≈ 0.467, full recall 0/5.

## 4. Todo findings / caveats

- Smoke: 30/30 valid, full recall 15/15 per arm, P/R/F1 ceiling.
- Held-out: 60/60 valid, recall 30/30 per arm; precision Agent 0.8778 vs
  ImpactPlan 0.7694; F1 0.9200 vs 0.8540; ImpactPlan tokens −72.98%, calls
  −86.36%, cost −47.51%, total latency −51.81% (median caveat: Agent median
  8.211 s vs ImpactPlan 6.891 s, two large Agent outliers).
- `TODO_SELECTION_SATURATED=NO`: recall saturated on the 5-file universe,
  per-file precision not.
- v1.1 end-to-end Todo study: 0/30 functional passes; first-failure taxonomy
  dominated by downstream exact-patch (C=10) and source-validity (D=8)
  classes, not the impact selector (A=1). Preserved as historical NO-GO.

## 5. djangoCMS primary findings / caveats

- 60/60 cells recorded; 31 valid / 29 failed. Agent 25/30 valid; ImpactPlan-v1
  only 6/30 valid (19 × 4096-cap truncation + 3 unknown-path + 1 provider-429
  + 1 harness defect).
- **Primary v1 valid-run correctness rests on only 6 valid cells.** No
  between-arm accuracy claim is made.
- All-cell operational: Agent 449,792 tokens / 206 calls / $0.140850;
  v1 184,401 tokens / 28 calls / $0.123298 (tokens −59.0%, calls −86.4%,
  cost −12.5%, time +17.4%).
- **The dependency graph was NOT injected** into djangoCMS v1 (or v2). The
  primary study characterizes explicit-plan selection WITHOUT graph assistance.

## 6. v1 diagnostic story

- Full explicit ImpactPlan-v1 serialization over the 144-path universe
  exceeded the frozen 4096 completion cap (minimal 144-path plan ≈ 17,364
  bytes / ~4,341 estimated tokens). 19/30 v1 cells truncated at exactly 4096
  (`finish_reason=length`).
- A one-run 16K diagnostic terminated (10,650 completion tokens, 179.172 s,
  $0.01148) — termination at high serialization cost, no accuracy claim.
- An 8192 ablation probe truncated (not run as a study). Do not claim a
  measured repository-size threshold.

## 7. ImpactPlan-v2 results

- Sparse representation (explicit non-PRESERVE decisions + deterministic
  PRESERVE-by-omission + frozen numeric candidate IDs 1..144) achieved
  29/30 operational validity with 0 truncations in the frozen exploratory
  study (selection-only).
- Valid-only micro: P 0.741007 / R 0.865546 / F1 0.798450 / FNR 0.134454;
  full-recall 18/29.
- **v2 is SELECTION ONLY** and **POST-HOC / EXPLORATORY**; do not present it
  as a preregistered arm or as pooled with the primary study.
- v2 changes schema and planner instruction together — their effects are NOT
  independently isolated.

## 8. Efficiency results (descriptive only)

- v2 vs Agent (all-cell, djangoCMS): tokens −67.91%, calls −85.44%, latency
  −82.72%, recorded cost −54.11% (descriptive; NOT statistically significant;
  no prespecified analysis supports a superiority claim).
- Todo held-out: ImpactPlan tokens −72.98%, calls −86.36%, cost −47.51%,
  latency −51.81% (median caveat).

## 9. Defensible claims

1. Selection-stage evidence is complete, frozen, and audited at
   `v0.11.0-benchmark-complete` and `stagec-djangocms-impactplan-v2-study-01-audited`.
2. At scenario 004 / cap 4096, v1 truncated 5/5 while v2 completed 5/5
   (874–1,525 tokens) — v2 resolves the observed scenario-004
   output-serialization bottleneck (feasibility / mechanism evidence).
3. v2 achieved 29/30 operational validity with zero truncations in the frozen
   30-cell exploratory study, with measurable write-set correctness
   (P 0.741 / R 0.866 / F1 0.798, valid-only micro).
4. ImpactPlan showed strong selection-stage efficiency potential in the small
   (Todo) setting at equal recall, with median-caveated latency.

## 10. Forbidden / unsupported claims

- No end-to-end Functional Correctness, Preservation, or Architecture
  Compliance results (not measured).
- No "v2 statistically beats Agent", "universal superiority", or "no
  trade-off".
- No graph benefit (graph NOT injected into v1 or v2).
- No Saleor results (Saleor was not started).
- No measured repository-size threshold; no claim that v2 solves impact
  identification universally (scenario 006).
- No full R/P/V/H correctness.

## 11. Validity threats (must appear in Limitations / Threats to Validity)

1. Severe missing-data asymmetry in the primary study (Agent 25 vs v1 6 valid).
2. Output-budget asymmetry (Agent 8 × 1024 vs v1 1 × 4096).
3. Provider instability (DeepInfra `engine_overloaded` → 5 infrastructure
   failures).
4. v1/v2 schema+instruction changed together (not isolated).
5. v2 candidate universe still exposed in the prompt — larger-repository input
   scaling remains Future Work.
6. Scenario 006 weakness (P ≈ 0.389, R ≈ 0.467, full recall 0/5).

## 12. Canonical report / evidence paths

| Item | Path |
|---|---|
| Final results | `reports/FINAL_BENCHMARK_RESULTS.{md,csv}` |
| Validity / limitations | `reports/BENCHMARK_VALIDITY_AND_LIMITATIONS.md` |
| Reproducibility index | `reports/BENCHMARK_REPRODUCIBILITY_INDEX.md` |
| Cross-repo synthesis | `reports/CROSS_REPO_SYNTHESIS.md` |
| v2 results / design | `reports/DJANGOCMS_IMPACTPLAN_V2_RESULTS.{md,csv}` / `reports/DJANGOCMS_IMPACTPLAN_V2_DESIGN.md` |
| Todo selection | `reports/STAGEC_SELECTION_01_RESULTS.{md,csv}` / `reports/STAGEC_HELDOUT_01_RESULTS.{md,csv}` |
| Todo v1.1 NO-GO | `reports/SCIENTIFIC_MICROSTUDY_V11_RESULTS.{md,csv}` / `reports/V11_ROOT_CAUSE_TAXONOMY.{md,csv}` |
| Primary evidence dir | `reports/scientific-stagec-djangocms-study-01/` |
| v2 evidence dir | `reports/scientific-stagec-djangocms-impactplan-v2-01/` |

## 13. Current Git / tag milestones

- Final benchmark tag: `v0.11.0-benchmark-complete` (peels to `5ffc662…`).
- Audited v2 study tag: `stagec-djangocms-impactplan-v2-study-01-audited`
  (peels to `f8e7aa8…`).
- Current branch: `paper/msc-manuscript-01` (paper phase).
- Do not move or recreate either benchmark tag; do not create new benchmark
  treatments.

## 14. Immediate paper tasks

1. Finalize research questions.
2. Freeze contribution claims (use sections 9–10 above).
3. Final Results table (sections 3, 5, 7).
4. Figure 1 (e.g., v1 vs v2 scenario-004 output distribution and the v2
   per-scenario P/R/F1).
5. Related Work (grounded in the selection-only framing above).
6. Limitations / Threats to Validity (section 11).
7. ≤4-page IEEE manuscript refinement.

**Do NOT generate new scientific findings.** Everything must trace to the
frozen evidence paths in section 12.