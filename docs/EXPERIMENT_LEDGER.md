# EXPERIMENT LEDGER — Canonical Experiment/Evidence Registry

**Role:** Canonical, frozen, machine-checkable registry of every major WP1/WP2
experiment. Numbers are traced to repository artifacts; negative evidence is
included with the same weight as positive evidence. This ledger is generated as
part of the 2026-10-02 research-closure phase and does not alter any source
experiment record.

Sources of authority (in order): (1) frozen experiment artifacts in the
repository, (2) this ledger, (3) older prose.

---

## WP1 — Primary evidence (selection / representation)

### E-1 djangoCMS explicit-v1 vs sparse-v2 representation study

| Field | Value |
|---|---|
| ID | E-1 |
| Experiment | Sparse Impact Plan (v2) vs explicit full-repository impact plan (v1) |
| Population | djangoCMS 30 tasks |
| Result | explicit valid 6/30, 19 truncated; sparse valid 29/30; sparse P/R/F1 = .741/.866/.798 |
| Status | Closed |
| Allowed interpretation | Sparse serialization solves the output-feasibility/truncation problem of explicit full-repository plans |
| Artifact | `reports/scientific_microstudy*/`, `reports/scientific-stagec-djangocms-study-01/final_metrics.json` (serialization/truncation failure evidence) |
| Evidence matrix | `02_EVIDENCE_MATRIX.md` row 1 |

### E-2 Graph ablation (C0/C1/C2)

| Field | Value |
|---|---|
| ID | E-2 |
| Experiment | Graph-context hint ablation on repository graph (144 nodes / 562 edges) |
| Population | djangoCMS external-validity tasks, 30 runs per condition |
| Result | OFF (c0) F1 .7940; Hints (c1) F1 .8067; precision +9.2 pp; FP -19; tokens ×2.6 |
| Status | Closed |
| Allowed interpretation | Graph hints may improve precision at material token cost; no universal graph claim |
| Artifact | `research/graph-c0-c1-c2-01/final_metrics.json`, `research/graph-c0-c1-c2-01/interpretation.json` |
| Evidence matrix | `02_EVIDENCE_MATRIX.md` row 2 |

### E-3 Oracle-gap bidirectional repair (closed negative)

| Field | Value |
|---|---|
| ID | E-3 |
| Experiment | Oracle-gap bidirectional repair feasibility |
| Population | djangoCMS n=174; Saleor n=149 |
| Result | F1 .3177 (djangoCMS) / .2605 (Saleor); gate FAIL |
| Status | Closed negative |
| Allowed interpretation | Post-hoc repair not adopted; first-pass recall/ranking remained the bottleneck |
| Artifact | `reports/oracle_gap_gates_validation.json` (gate PASS on pipeline; F1 gate FAIL in mission records), `reports/ORACLE_GAP_INDEPENDENT_AUDIT.md` |
| Evidence matrix | `02_EVIDENCE_MATRIX.md` row 3 |

### E-4 Saleor RESERVE-300 (primary)

| Field | Value |
|---|---|
| ID | E-4 |
| Experiment | RM-CSS vs SIP on the clean Saleor RESERVE sample |
| Population | n=300 (clean reserve) |
| Result | SIP F1 .2647; RM-CSS F1 .3569; delta +.0921, 95% CI [.0691, .1156] |
| Status | Primary |
| Allowed interpretation | RM-CSS improves selection quality over SIP on the clean reserve |
| Artifact | `reports/saleor_reserve_300_rmcss_result.json` (verdict SALEOR_RESERVE_300_RMCSS_PASS), `reports/saleor_reserve_300_rmcss_result_audit.json` (15/15 checks) |
| Evidence matrix | `02_EVIDENCE_MATRIX.md` row 4 |

### E-5 MAIN_297 selection (primary)

| Field | Value |
|---|---|
| ID | E-5 |
| Experiment | WP-1b selection-only comparison: Agent vs RM-CSS vs SIP |
| Population | n=297 |
| Result | Agent .3631; RM-CSS .3568; SIP .2652 (pooled file-level F1) |
| Status | Primary |
| Allowed interpretation | RM-CSS is close to the Agent under the frozen selection-only protocol |
| Artifact | `reports/wp1b_main297_result.json` (final_category RMCSS_NONINFERIOR_AT_LOWER_COST; quality_verdict NI_SUPPORTED) |
| Evidence matrix | `02_EVIDENCE_MATRIX.md` row 5 |

### E-6 MAIN_297 efficiency (primary)

| Field | Value |
|---|---|
| ID | E-6 |
| Experiment | Interaction/cost comparison of MAIN_297 |
| Population | n=297 |
| Result | RM-CSS ≈ 0.2746× calls and ≈ 0.2134× generation tokens vs Agent |
| Status | Primary |
| Allowed interpretation | Large interaction/cost reduction under the matched selection protocol |
| Artifact | `reports/wp1b_main297_result.json` → `cost_view_A_marginal.model_calls.ratio_point` (0.2746), `cost_sensitivity_not_decisive.generative_tokens_only.ratio_point` (0.2134) |
| Evidence matrix | `02_EVIDENCE_MATRIX.md` row 6 |

### E-7 MAIN_297 non-inferiority (primary)

| Field | Value |
|---|---|
| ID | E-7 |
| Experiment | Preregistered non-inferiority test |
| Population | n=297 |
| Result | Margin 0.05 supported (NI_SUPPORTED); narrower 0.03 inconclusive at this n |
| Status | Primary |
| Allowed interpretation | Selection-only non-inferiority at the preregistered 0.05 margin; NOT equivalence or superiority |
| Artifact | `reports/wp1b_main297_result.json` → `margin` 0.05, `sensitivity_margins_not_decisive` |
| Evidence matrix | `02_EVIDENCE_MATRIX.md` row 7 |

---

## WP2 — Supporting downstream evidence

### E-8 Smoke v2.2 (supporting)

| Field | Value |
|---|---|
| ID | E-8 |
| Experiment | E2E pipeline smoke (generation + evaluation) |
| Population | DEV_TRAIN_ENG n=14 |
| Result | 62 generation episodes; APPLIED 50; invalid-after-repair 11; no-scope 1 |
| Status | Supporting |
| Allowed interpretation | E2E pipeline works as an engineering pipeline; no selector ranking |
| Artifact | `research/wp2/e2e_smoke_eng_v22/`, `docs/WP2_E2E_SMOKE_ENG_V22_REPORT_2026-09-29.md` |
| Evidence matrix | `02_EVIDENCE_MATRIX.md` row 8 |

### E-9 Pilot-A (supporting negative)

| Field | Value |
|---|---|
| ID | E-9 |
| Experiment | Generator-floor diagnosis pilot |
| Population | 40 episodes |
| Result | GOLD RESOLVED 0; PLACEBO RESOLVED 0 |
| Status | Supporting negative |
| Allowed interpretation | Generator floor blocks meaningful downstream selector comparison |
| Artifact | `research/wp2/pilot_a_v1/`, `reports/WP2_PILOT_A_V1_RESULT.md` |
| Evidence matrix | `02_EVIDENCE_MATRIX.md` row 9 |

### E-10 M14R generator-capability probe (supporting negative)

| Field | Value |
|---|---|
| ID | E-10 |
| Experiment | Generator variant capability probe |
| Population | 13 members / 4 variants (G0–G3) |
| Result | robust episodes 8/9/8/8 across G0–G3; token M14R_FLOOR_NOT_MET; winner G0 (fallback) |
| Status | Supporting negative |
| Allowed interpretation | Tested variants did not remove the generator floor |
| Artifact | `research/wp2/m14r_v1/m14r_summary.json` (gold_robust per variant; decision.token M14R_FLOOR_NOT_MET) |
| Evidence matrix | `02_EVIDENCE_MATRIX.md` row 10 |

### E-11 M15-R OPWS (supporting descriptive)

| Field | Value |
|---|---|
| ID | E-11 |
| Experiment | OPWS Pilot-B scope sufficiency |
| Population | Pilot-B n=10 |
| Result | GOLD 10/10; RM-CSS 3/10; Agent r1/r2/r3 = 2/10, 3/10, 2/10 (OPWS_ROBUST) |
| Status | Supporting descriptive |
| Allowed interpretation | Selected scopes show limited reference-patch sufficiency on a small pilot; descriptive only |
| Artifact | `research/wp2/m15r_v1/opws_summary.json` (per_selector opws_robust counts; token M15R_OPWS_COMPLETE) |
| Evidence matrix | `02_EVIDENCE_MATRIX.md` row 11 |

### E-12 M15-R generation (supporting negative)

| Field | Value |
|---|---|
| ID | E-12 |
| Experiment | M15-R generation S2/S3 |
| Population | 10 tasks |
| Result | Gold-solvable 1/10; robust episodes 3; S2 gate FAIL (M15R_GOLD_FLOOR_FAIL_NO_GENERATION_CLAIM); S3 not executed |
| Status | Supporting negative |
| Allowed interpretation | No valid generation-based selector comparison; S3 correctly skipped |
| Artifact | `research/wp2/m15r_v1/m15r_summary.json` (s2_gate; s3_executed false) |
| Evidence matrix | `02_EVIDENCE_MATRIX.md` row 12 |

### E-13 M16-v1 (closed pre-experiment / method)

| Field | Value |
|---|---|
| ID | E-13 |
| Experiment | M16-v1 attempted OPWS-MAIN instrument qualification |
| Population | pre-experiment (adapter preflight) |
| Result | Adapter preflight failed before R03; no MAIN OPWS outcome |
| Status | Closed negative / method |
| Allowed interpretation | Instrument was not qualified for MAIN; no MAIN OPWS result exists |
| Artifact | `docs/M16_V1_CLOSURE_2026-10-02.md`, `research/wp2/m16_v1/adapter/adapter_report.json`, STOP report `STOP_M16_ADAPTER_FAIL_20261002T160619.md` |
| Evidence matrix | `02_EVIDENCE_MATRIX.md` row 13 |

---

## Registry invariants

1. Every row traces numbers to a repository artifact (path listed).
2. Negative evidence is represented with the same status weight as positive.
3. No row's interpretation exceeds the "Allowed interpretation" column; the
   claim freeze in `docs/CLAIM_REGISTRY.md` is the binding interpretation.
4. This ledger is not a source experiment; it is the canonical index. Historical
   experiment records are never rewritten.