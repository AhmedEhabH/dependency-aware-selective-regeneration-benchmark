# CROSS-REPOSITORY SYNTHESIS — Todo + djangoCMS (Primary v1/Agent + ImpactPlan-v2 Exploratory)

**Canonical synthesis of the Stage-C selection-stage benchmark evidence.**
**Compiled (UTC):** 2026-09-08 (FINAL BENCHMARK CLOSURE)
**Branch:** `research/djangocms-external-validity-prep-01` (HEAD `f8e7aa8…`)
**Audited v2 study tag:** `stagec-djangocms-impactplan-v2-study-01-audited`
**Final benchmark tag:** `v0.11.0-benchmark-complete`
**Scope:** SELECTION ONLY — impact identification correctness and selection-stage
efficiency. This document does NOT report Functional Correctness, Preservation,
Architecture Compliance, or end-to-end regeneration outcomes (those were not
experimentally measured in these treatments).

---

## 0. Standing discipline (read first)

- **The studies are kept SEPARATE.** This is NOT a single homogeneous 90-cell
  experiment. Denominators from incompatible treatments are NEVER pooled.
- **Todo** evidence (smoke + held-out selection, 5-file universe) is frozen and
  preserved with its original design caveats; no new Todo experiments were run.
- **djangoCMS primary** (`scientific-stagec-djangocms-01`) = 60 cells
  (6 scenarios × 2 arms × 5 reps): `iterative_repository_agent` (Agent) and
  `impact_plan` (v1). The dependency graph was **NOT injected** into the primary
  djangoCMS v1 treatment.
- **djangoCMS ImpactPlan-v2** (`scientific-stagec-djangocms-impactplan-v2-01`)
  = a distinct POST-HOC / EXPLORATORY 30-cell redesign study (6 scenarios ×
  5 reps, arm `impact_plan_v2` ONLY). It is NOT a preregistered arm of the
  primary study and is NOT pooled with it.
- Every number below traces to frozen raw evidence; all documentation is
  internally consistent with the evidence directories.

---

## 1. Todo evidence (frozen; selection-stage efficiency potential)

**Original design caveats preserved.** Todo is a small, fully controlled
reference repository with a five-file source universe; results are
selection-only component-study evidence, not end-to-end correctness.

| Study | Cells | Validity | Headline selection result | Efficiency result | Status |
|---|---|---|---|---|---|
| Stage-C smoke (`scientific-stagec-selection-01`) | 30/30 | 30/30 valid (3 scenarios × 2 arms × 5 reps) | Full recall 15/15 per arm; P/R/F1 1.0 ceiling BOTH arms | ImpactPlan fewer tokens/calls/cost; API cost $0.052696 | EXPLORATORY component study |
| Stage-C held-out (`scientific-stagec-heldout-01`) | 60/60 | 60/60 valid (6 held-out scenarios × 2 arms × 5 reps) | Full recall 30/30 per arm (1.0); precision Agent 0.8778 vs ImpactPlan 0.7694; F1 Agent 0.9200 vs ImpactPlan 0.8540; FNR 0.0 | ImpactPlan tokens −72.98%, calls −86.36% (30 vs 220), API cost −47.51% ($0.104760); total latency −51.81% (236.162 s vs 490.108 s) BUT median Agent 8.211 s vs ImpactPlan 6.891 s with two large Agent outliers | FOLLOW-UP |

**Frozen Todo conclusions:**

1. `TODO_SELECTION_SATURATED=NO` — recall is saturated on the five-file universe
   (100% both arms) but per-file selection precision is NOT saturated
   (held-out Agent 0.8778 vs ImpactPlan 0.7694 — a measurable between-arm
   difference; ImpactPlan over-selects).
2. ImpactPlan showed strong **selection-stage efficiency potential** in the
   smaller repository/task setting (large token/call/cost reductions at equal
   recall, with a median-caveated latency story).
3. The v1.1 end-to-end Todo NO-GO (0/30 functional passes) is preserved as
   historical evidence: its first-failure taxonomy is dominated by downstream
   exact-patch (C=10) and source-validity (D=8) classes, not by the impact
   selector (A=1). No new Todo experiments were run.

---

## 2. djangoCMS primary study (60 cells: Agent + ImpactPlan-v1)

**STUDY_ID:** `scientific-stagec-djangocms-01` (branch
`research/djangocms-external-validity-prep-01`)
**Design:** 6 scenarios × 2 arms × 5 reps = 60 frozen cells; model
`qwen/qwen3-coder` @ DeepInfra pinned through OpenRouter (`deepinfra/turbo`),
fallback OFF, temperature 0, selection-only. Caps: Agent 1024 / v1 4096.

### 2.1 Valid-run micro correctness (valid-only denominators)

| Arm | Valid / 30 | Selected | TP | FP | FN | Precision | Recall | F1 | FNR |
|---|---|---|---|---|---|---|---|---|---|
| iterative_repository_agent | 25 | 147 | 95 | 52 | 18 | 0.6463 | 0.8407 | 0.7308 | 0.1593 |
| impact_plan (v1) | 6 | 34 | 23 | 11 | 2 | 0.6765 | 0.9200 | 0.7797 | 0.0800 |

### 2.2 All-cell operational (valid + failed resource consumption)

| Arm | Valid / 30 | Failed / 30 | Tokens | Model calls | Measured time | Recorded cost |
|---|---|---|---|---|---|---|
| iterative_repository_agent | 25 | 5 | 449792 | 206 | 2265.517 s | $0.140850 |
| impact_plan (v1) | 6 | 24 | 184401 | 28 | 2658.733 s | $0.123298 |

### 2.3 ⚠ WARNING — SEVERE MISSING-DATA ASYMMETRY (MUST be retained)

**Agent = 25 valid cells; ImpactPlan-v1 = only 6 valid survivor cells**
(19 × 4096-cap truncations + 3 unknown-path + 1 provider-429 + 1 harness
defect). **Never use that survivor comparison as evidence of v1 accuracy
superiority.** The v1 headline rests on 6 survivors and is not equal-evidence
comparable to Agent's 25-run aggregate.

### 2.4 Dependency graph

The dependency graph was **NOT injected** into the primary djangoCMS v1
ImpactPlan. The primary djangoCMS study therefore characterizes explicit-plan
selection **WITHOUT dependency-graph assistance**. (ImpactPlan-v2 also does not
inject graph assistance.)

---

## 3. djangoCMS ImpactPlan-v2 exploratory study (POST-HOC / EXPLORATORY REDESIGN)

**STUDY_ID:** `scientific-stagec-djangocms-impactplan-v2-01`
**Label prominently: POST-HOC / EXPLORATORY REDESIGN — NOT a primary-experiment
replacement; NOT pooled with the primary 60-cell study.**

**Treatment:** v2 removes explicit PRESERVE serialization. The model emits ONLY
non-PRESERVE decisions (`REGENERATE` / `VALIDATE` / `HUMAN_REVIEW`) keyed by
frozen numeric candidate IDs (1..144); every omitted candidate decodes
deterministically to PRESERVE (deterministic PRESERVE-by-omission). This is ONE
representation redesign — schema and planner instruction changed together; their
effects are NOT independently isolated.

### 3.1 Operational summary (all 30 cells)

| Metric | Value |
|---|---|
| Recorded | 30/30 |
| Valid (succeeded) | 29 |
| Failed | 1 |
| Truncations | 0 |
| Invalid-ID failures | 0 |
| Duplicate / conflict failures | 0 |
| Prompt tokens | 113,880 |
| Completion tokens | 30,473 |
| Total tokens | 144,353 |
| Calls | 30 |
| Recorded cost | $0.064634 (< $0.20 ceiling, COST_LOCK=PASS) |
| Latency total (ALL-30) | 391.437 s |

### 3.2 Correctness — VALID-ONLY micro (pooled over 29 valid cells)

| Metric | Value |
|---|---|
| TP | 103 |
| FP | 36 |
| FN | 16 |
| Precision | 0.741007 |
| Recall | 0.865546 |
| F1 | 0.798450 |
| FNR | 0.134454 |
| Full-recall rate | 18 / 29 = 0.620690 |

### 3.3 Correctness — VALID-ONLY macro (mean over 29 valid cells)

Precision 0.716667 · Recall 0.862972 · F1 0.766824 · FNR 0.137028.

### 3.4 Do not hide — scenario 006 is the weakest case

| Scenario | Valid/5 | Precision | Recall | Full-recall rate |
|---|---|---|---|---|
| djangocms-external-validity-006 | 5 | ≈ 0.389 | ≈ 0.467 | 0/5 |

Scenario-006 is a genuine limitation (model consistently missed gold files
`cms/models/pluginmodel.py`, `cms/admin/placeholderadmin.py`,
`cms/utils/plugins.py` and over-selected). It is retained as a scientific
observation; it is NOT tuned or explained away post hoc.

### 3.5 Failed cell (preserved, NOT rerun / NOT salvaged)

**`002-r3`** (`stgc-v2-djangocms-external-validity-002-impact_plan_v2-r3`)
remains **FAILED** under the frozen contract:

- The raw output **is valid JSON** and structurally conforms to the frozen
  `IMPACT_PLAN_V2_SCHEMA`.
- But it emitted a **`VALIDATE` action for `cms/models/__init__.py` with no
  cited supporting evidence** (`evidence = []`), violating the frozen
  ImpactPlan semantic invariant (every `VALIDATE` decision must cite ≥ 1
  supporting validation/architecture evidence item). This correctly triggers
  fail-closed behavior:
  `impact_plan_invariant_failure: v_missing_validation_reason:
  cms/models/__init__.py`.
- The raw response **did identify `cms/api.py` as `REGENERATE`** (the gold
  write target), but the complete plan remains **scientifically failed** under
  the frozen fail-closed contract. It is not salvaged, re-scored, or re-run.

---

## 4. Same-cap proof-of-mechanism (scenario 004, completion cap = 4096)

| Treatment | Cap | Scenario-004 outcome |
|---|---|---|
| Historical ImpactPlan-v1 | 4096 | **5/5 truncated at 4096** (`finish_reason=length`, 4096 completion tokens each) |
| ImpactPlan-v2 | 4096 | **5/5 completed without truncation** (`finish_reason=stop`; completion output range 874–1525 tokens) |

**Interpretation (careful):** this is strong proof that the frozen v2
representation redesign resolves the observed **scenario-004 output-serialization
bottleneck**. It is feasibility / mechanism evidence, NOT an accuracy claim and
NOT a universal scaling law. **Do NOT claim that schema and planner-instruction
effects were independently isolated** — the v2 treatment changes the sparse
representation/schema and the corresponding planner instruction together.

---

## 5. Descriptive Agent comparison (descriptive only — see warnings)

### 5.1 Valid-run correctness (descriptive)

| Treatment | Valid cells | Precision | Recall | F1 |
|---|---|---|---|---|
| Agent (historical valid-run) | 25 | ≈ 0.6463 | ≈ 0.8407 | ≈ 0.7308 |
| ImpactPlan-v2 (valid-run) | 29 | ≈ 0.7410 | ≈ 0.8655 | ≈ 0.7985 |

### 5.2 Operational totals (all-cell)

| Treatment | Tokens | Calls | Latency | Recorded cost |
|---|---|---|---|---|
| Agent | 449,792 | 206 | 2265.517 s | $0.140850 |
| ImpactPlan-v2 | 144,353 | 30 | 391.437 s | $0.064634 |

### 5.3 Directional deltas (v2 vs Agent, all-cell)

- tokens ≈ **−67.91%**
- calls ≈ **−85.44%**
- latency ≈ **−82.72%**
- recorded API cost ≈ **−54.11%**

### 5.4 Warnings (MUST be retained)

- **v2 was POST-HOC / EXPLORATORY** and was NOT a concurrent preregistered arm
  of the same primary study.
- Therefore DO NOT state: "v2 statistically beats Agent", "no trade-off", or
  "universal superiority".
- Use cautious descriptive language only. No statistical significance is
  claimed (no prespecified analysis supports it).

---

## 6. Final claim discipline — defensible overall narrative

1. **Todo** demonstrated strong selection-stage efficiency potential for
   explicit ImpactPlan in the smaller repository/task setting.
2. **Scaling to djangoCMS** exposed a major limitation of full explicit
   ImpactPlan-v1 serialization under the frozen single-response cap.
3. At **scenario 004 and cap 4096, v1 truncated 5/5 times**.
4. Increasing the cap diagnostically (16K diagnostic) showed the
   representation could eventually terminate but at **high serialization cost**
   (10,650 completion tokens on one scenario).
5. **ImpactPlan-v2 removed explicit PRESERVE serialization** through
   deterministic PRESERVE-by-omission.
6. In the frozen exploratory 30-cell study, **v2 achieved 29/30 operational
   validity with zero truncations** while retaining measurable write-set
   correctness (valid-only micro P 0.741 / R 0.866 / F1 0.798).
7. **v2 still has correctness limitations, especially scenario 006** — sparse
   serialization solves the observed output bottleneck but does NOT solve
   impact identification universally.
8. **Input-side repository scaling remains a Future Work concern** — the
   candidate universe is still presented to the model in full.

### Do NOT claim

- end-to-end selective regeneration is solved;
- arbitrary repository scalability;
- graph benefit (no graph assistance in v1 or v2);
- Saleor results (Saleor was not started in these studies);
- full R/P/V/H correctness;
- universal superiority;
- statistically significant superiority (unless justified by a separately
  valid analysis).

---

## 7. Research framework / scope limitation

The project's canonical research framework distinguishes **Impact
Correctness** from broader **Functional Correctness**, **Preservation**,
**Architecture Compliance**, and **Efficiency**. The current Stage-C djangoCMS
study (primary and v2) is **SELECTION ONLY** (impact identification + write-set
correctness + selection-stage efficiency). **No Functional Correctness,
Preservation, or Architecture Compliance results are claimed** — they were not
experimentally measured in this treatment. Where a claim would require one of
those dimensions, the scope limitation is stated explicitly.

---

## 8. Evidence index (all values trace here)

| Study | Evidence directory | Key reports |
|---|---|---|
| Todo smoke | `reports/scientific_stagec_selection_01/` | `reports/STAGEC_SELECTION_01_RESULTS.{md,csv}` |
| Todo held-out | `reports/scientific_stagec_heldout_01/` | `reports/STAGEC_HELDOUT_01_RESULTS.{md,csv}` |
| v1.1 end-to-end NO-GO | `reports/scientific_microstudy_v11/` | `reports/SCIENTIFIC_MICROSTUDY_V11_RESULTS.{md,csv}`, `reports/V11_ROOT_CAUSE_TAXONOMY.{md,csv}` |
| djangoCMS primary (60) | `reports/scientific-stagec-djangocms-study-01/` | `reports/FINAL_BENCHMARK_RESULTS.{md,csv}`, `reports/BENCHMARK_VALIDITY_AND_LIMITATIONS.md`, `reports/BENCHMARK_REPRODUCIBILITY_INDEX.md` |
| djangoCMS ImpactPlan-v2 (30) | `reports/scientific-stagec-djangocms-impactplan-v2-01/` | `reports/DJANGOCMS_IMPACTPLAN_V2_RESULTS.{md,csv}`, `reports/DJANGOCMS_IMPACTPLAN_V2_DESIGN.md` |
| Cross-study truth matrix | — | `reports/RESEARCH_TRUTH_MATRIX.md` |