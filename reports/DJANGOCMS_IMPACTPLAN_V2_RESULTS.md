# djangoCMS ImpactPlan-v2 — 30-Cell POST-HOC / EXPLORATORY RESULTS

**STUDY_ID:** `scientific-stagec-djangocms-impactplan-v2-01`
**Status:** POST-HOC / EXPLORATORY REDESIGN — **NOT** a primary experiment replacement
**Date (UTC):** 2026-09-08
**Branch:** `research/djangocms-external-validity-prep-01`
**Evidence dir:** `reports/scientific-stagec-djangocms-impactplan-v2-01/`
**CSV:** `reports/DJANGOCMS_IMPACTPLAN_V2_RESULTS.csv`

---

## 1. Identity

| Field | Value |
|---|---|
| Arm | `impact_plan_v2` ONLY (sparse non-PRESERVE serialization) |
| Scientific model | `qwen/qwen3-coder` |
| Provider | DeepInfra pinned through OpenRouter (`deepinfra/turbo`) |
| Fallback | OFF |
| Temperature | 0.0 |
| Completion cap | 4096 (identical to the primary v1 ImpactPlan cap) |
| Scope | SELECTION ONLY |
| Candidate universe | exact frozen 144-path djangoCMS universe (SHA-256 `43f4279b...`) |
| Candidate-ID mapping SHA-256 | `9d33e163...` |
| Design | 6 scenarios x 5 repetitions = EXACTLY 30 frozen manifest cells |
| Recorded | 30/30 — 29 valid (succeeded) / 1 failed (recorded) |

## 2. Design contract (recap)

ImpactPlan-v2 is **one representation redesign** (frozen, not tunable here):

- v1 instructed the model to serialize an explicit decision for every one of
  the 144 candidates (full explicit repository-wide policy serialization).
- v2 instructs the model to emit ONLY non-PRESERVE decisions
  (`REGENERATE` / `VALIDATE` / `HUMAN_REVIEW`) keyed by deterministic frozen
  numeric candidate IDs (1..144); every omitted candidate decodes
  deterministically to PRESERVE.
- Prompt and schema effects are **NOT independently isolated** (a sparse
  output representation requires a sparse instruction by construction).
- NO dependency-graph assistance is injected (the primary v1 djangoCMS
  ImpactPlan was also instantiated WITHOUT the frozen graph).

Losslessness of the representation under the encoder/decoder contract:

```
I(pi) = {v in V : pi(v) != P}      (the model emits exactly I(pi))
D(E_s(pi)) = pi                     (omitted => PRESERVE reconstructs the policy)
```

This establishes losslessness of the REPRESENTATION under the contract; it does
NOT establish that the LLM identifies every truly impacted candidate.

## 3. Prompt-evidence parity (provenance verification, zero scientific calls)

Result: **Scenario-004 v1 and v2 rendered inputs contain the same
strategy-visible evidence block; semantic-seed evidence was not newly
introduced by v2.**

| Item | SHA-256 / value |
|---|---|
| rendered v1 scenario-004 prompt | `b97bc1b578da37c921689b317310a4e06971907b47cd434dafb3e66dc825c856` |
| rendered v2 scenario-004 prompt | `2196af95a0ab26654033ce6c87be1a6580442849fc1c1b55b78c3afc46b48ae6` |
| v1/v2 evidence block (identical) | `38c6d04115ad9c2d9635a6e4e8f68004103270ca070611b84f5c869cd85373b6` |
| evidence-item count | 32 (all `semantic-seed-*`, deterministic) |
| candidate-ID mapping SHA-256 | `9d33e163505722e2cfe602ca165777d3d5accbaf5b9f7a82d1b30068ca9d1ca6` |
| universe SHA-256 | `43f4279bdf228745b1f6b289c81cda141b089ab5be4f4af63bb8f39f837c4410` |

Historical reported prompt tokens (scenario-004): v1 = 2768 (16K diagnostic),
v2 = 3447 (cost probe). The increase is NOT attributed solely to numeric
candidate IDs — v2 changes candidate representation, sparse planner/output
instructions, and the structured-output schema together.

## 4. Headline results

### 4.1 Operational validity (all 30 cells)

| Metric | Value |
|---|---|
| Manifest cells | 30 |
| Recorded | 30/30 |
| Valid (succeeded) | 29 |
| Failed | 1 |
| Operational validity | 29 / 30 = 96.6667% |
| Truncations | 0 |
| Invalid-ID failures | 0 |
| Duplicate / conflict failures | 0 |
| Model calls | 30 (one per cell) |
| Total tokens | 144,353 |
| Prompt tokens | 113,880 |
| Completion tokens | 30,473 |
| Latency total (ALL 30 cells) | 391.437 s |
| Recorded API cost | **$0.064634** (ceiling $0.20 — COST_LOCK=PASS) |

The single failed cell is `stgc-v2-djangocms-external-validity-002-impact_plan_v2-r3`
(scenario-002, repetition 3). Its scientific failure is **precise and narrow**:

- The persisted raw response **is syntactically valid JSON and independently
  validates against the frozen `IMPACT_PLAN_V2_SCHEMA`** (structured-output
  conformance holds).
- The raw response **correctly identified the scenario-002 gold write target
  `cms/api.py` as `REGENERATE`** (candidate ID 12, with cited semantic-seed
  evidence).
- The failure occurs at the **ImpactPlan semantic / invariant layer that
  follows JSON decoding**: the model also emitted a `VALIDATE` action for
  `cms/models/__init__.py` (candidate ID 63) with **`evidence = []`**. The
  frozen ImpactPlan invariant requires every `VALIDATE` decision to cite at
  least one supporting validation/architecture evidence item.
- Therefore the plan correctly **failed closed** with:
  `impact_plan_invariant_failure: v_missing_validation_reason:
  cms/models/__init__.py`.

The failure is **NOT** malformed JSON. It is **NOT** a missing
`validation_reason` JSON field — **no such required field exists in the frozen
v2 schema**. The precise issue is that a `VALIDATE` action lacked the cited
supporting evidence required by the semantic ImpactPlan invariant. Although the
model did identify the gold write target in the raw response, the entire plan
remains **scientifically FAILED under the frozen fail-closed contract**. This
run is not salvaged, re-scored, or re-run; it is preserved verbatim and reported
as a separate operational failure (never pooled into the valid-only correctness
denominators below).

> **Reproducibility note — `schema_valid` terminology.** The study runner's
> persisted `schema_valid` field is **not** pure JSON-Schema conformance. It is
> a **composite** condition computed as: terminal success AND successful decode
> AND no invalid selected paths AND no truncation (see
> `stagec_djangocms_impactplan_v2_study_execute.py`). It therefore conflates two
> distinct layers:
>
> **A. Native / JSON structured-output conformance** — the raw response parses
> as JSON and validates against the frozen `IMPACT_PLAN_V2_SCHEMA`.
>
> **B. ImpactPlan semantic / invariant validity (terminal plan validity)** —
> the decoded plan satisfies the frozen ImpactPlan semantic invariants
> (e.g., every `VALIDATE` decision cites ≥ 1 supporting evidence item) and the
> cell terminates successfully.
>
> For `002-r3`: **A = valid** (JSON schema conformance), **B = failed**
> (ImpactPlan semantic invariant). The original persisted `schema_valid` field
> (composite, `false` for the failed cell) is preserved verbatim for provenance;
> no frozen execution code was changed post hoc.

### 4.2 Correctness — VALID-ONLY micro (pooled across the 29 valid cells)

| Metric | Value |
|---|---|
| Denominator | VALID-ONLY, 29 cells |
| Selected | 139 |
| TP | 103 |
| FP | 36 |
| FN | 16 |
| Micro Precision | 0.741007 |
| Micro Recall | 0.865546 |
| Micro F1 | 0.798450 |
| Micro FNR | 0.134454 |
| Full-recall rate (fraction of valid runs with recall = 1.0) | 0.620690 |

### 4.3 Correctness — VALID-ONLY macro (mean over the 29 valid cells)

| Metric | Value |
|---|---|
| Denominator | VALID-ONLY, 29 cells |
| Mean Precision | 0.716667 |
| Median Precision | 0.800000 |
| Mean Recall | 0.862972 |
| Median Recall | 1.000000 |
| Mean F1 | 0.766824 |
| Median F1 | 0.800000 |
| Mean FNR | 0.137028 |
| Median FNR | 0.000000 |
| Full-recall rate | 0.620690 |

### 4.4 Latency (VALID-ONLY, 29 cells)

| Metric | Value |
|---|---|
| Denominator | VALID-ONLY, 29 cells |
| Total | 384.827 s |
| Mean | 13.269897 s |
| Median | 11.953000 s |
| Min | 5.266000 s |
| Max | 48.843000 s |

Do not mix denominators: the **all-30-cell** operational latency total in
section 4.1 is **391.437 s** (includes the failed cell's 6.61 s); the
**valid-only** descriptive statistics above use the 29 valid cells
(total **384.827 s**). All-cell totals and valid-only descriptive statistics are
kept separately labeled and are never mixed.

Defensible latency outliers (> mean + 2·σ): `005-r5` (48.843 s) and `005-r4`
(31.578 s). Both are single-call provider latency observations on scenario-005,
not workflow-deadline events (all cells used 1 model call; the 600 s workflow
deadline was never approached).

## 5. Per-scenario results (pooled micro over that scenario's valid cells)

| Scenario | Valid/5 | Selected | TP | FP | FN | Precision | Recall | F1 | FNR | Full-recall rate |
|---|---|---|---|---|---|---|---|---|---|---|
| djangocms-external-validity-002 | 4 | 9 | 4 | 5 | 0 | 0.444444 | 1.000000 | 0.615385 | 0.000000 | 1.0 |
| djangocms-external-validity-004 | 5 | 26 | 20 | 6 | 0 | 0.769231 | 1.000000 | 0.869565 | 0.000000 | 1.0 |
| djangocms-external-validity-005 | 5 | 27 | 24 | 3 | 1 | 0.888889 | 0.960000 | 0.923077 | 0.040000 | 0.8 |
| djangocms-external-validity-006 | 5 | 18 | 7 | 11 | 8 | 0.388889 | 0.466667 | 0.424242 | 0.533333 | 0.0 |
| djangocms-external-validity-007 | 5 | 34 | 29 | 5 | 6 | 0.852941 | 0.828571 | 0.840580 | 0.171429 | 0.2 |
| djangocms-external-validity-008 | 5 | 25 | 19 | 6 | 1 | 0.760000 | 0.950000 | 0.844444 | 0.050000 | 0.8 |

Scenario-006 is the weakest (recall 0.467): the model consistently missed gold
files (`cms/models/pluginmodel.py`, `cms/admin/placeholderadmin.py`,
`cms/utils/plugins.py`) and over-selected. This is a scientific observation,
NOT a tuning trigger.

## 6. Selected-set / sparsity statistics (VALID-ONLY, 29 cells)

| Statistic | Mean | Median | Min | Max |
|---|---|---|---|---|
| Selected-set size | 4.793 | 5.0 | 1 | 8 |
| Explicit emitted decisions | 6.344828 | 6.0 | 3 | 10 |
| Decoded PRESERVE | 137.655172 | 138.0 | 134 | 141 |

The sparse representation never emits more than 10 explicit decisions per cell
while the decoded policy always contains exactly 144 decisions. This is the
core representation property being evaluated: explicit output size is tied to
the number/verbosity of emitted non-PRESERVE decisions rather than to
repository-wide explicit decision serialization.

## 7. Comparison discipline (descriptive only)

### 7.1 Same-cap scenario-004 observation (v1 @4096 vs v2 @4096)

- Historical primary v1 at cap 4096, scenario-004: **5/5 repetitions hit the
  4096 completion cap and failed** (`finish_reason=length`, truncation, 4096
  completion tokens each).
- v2 at cap 4096, scenario-004: **5/5 succeeded** (`finish_reason=stop`,
  completion tokens 874–1525, no truncation).

This is the clean **same-cap** proof-of-mechanism observation for the sparse
representation on this scenario. It is feasibility evidence, NOT an accuracy
claim and NOT a universal scaling law.

### 7.2 Descriptive v1 16K diagnostic comparison

The historical one-run v1 16K diagnostic on scenario-004 (cap 16384) terminated
at 10,650 completion tokens (`finish_reason=stop`) with Precision 0.444444 /
Recall 1.0 / F1 0.615385, latency 179.172 s, cost $0.01148. The v1-16K vs
v2-4K comparison is **NOT a same-cap comparison**. The single-run accuracy
difference does NOT establish that v2 improves F1 or Precision.

### 7.3 Descriptive primary-study comparison (all-cell and valid-run)

The primary djangoCMS study (`scientific-stagec-djangocms-01`) remains the
authoritative 6-scenario x 2-arm x 5-rep = 60-cell experiment:

| Arm | Valid / 30 | Micro Precision | Micro Recall | Micro F1 |
|---|---|---|---|---|
| iterative_repository_agent | 25 | 0.646259 | 0.840708 | 0.730769 |
| impact_plan (v1) | 6 | 0.676471 | 0.920000 | 0.779661 |
| impact_plan_v2 (this study) | 29 | 0.741007 | 0.865546 | 0.798450 |

**Warnings:**
- These are NOT a single homogeneous "90-run experiment". The v2 study is a
  distinct POST-HOC / EXPLORATORY 30-cell study.
- v1 had only 6 valid cells versus Agent's 25; v2's valid subset (29/30) is
  far more complete, but the comparison is still descriptive and confounded by
  the representation redesign (prompt + schema changed together).
- Do NOT say v2 "repairs" or replaces failed v1 cells; they are separate
  treatments with separate denominators.
- No statistical significance is claimed (no prespecified analysis supports it).
- The historical 42.5% pilot result remains historical motivation only and is
  not current benchmark evidence.

## 8. What v2 does NOT claim

- NOT universal ImpactPlan superiority; NOT universal superiority of sparse
  planning; NOT solved end-to-end selective regeneration.
- NOT arbitrary large-repository scalability; NOT Saleor feasibility; NOT a
  universal 26-file output threshold; NOT O(|I|) empirical token scaling from
  one probe.
- NOT calibrated R/P/V/H classification quality; NOT graph benefit (neither
  v1 nor v2 used graph assistance); NOT broad novelty over repository-level
  change-impact analysis; NOT statistical significance.
- The sparse encoding property D(E_s(pi)) = pi is a representation-level
  losslessness property, not a model-correctness proof.

## 9. Input-side scalability limitation (qualitative, Future Work)

ImpactPlan-v2 removes the need to explicitly output a PRESERVE decision for
every candidate, but the v2 inference prompt still exposes the frozen candidate
universe and associated strategy-visible evidence. A sufficiently larger
repository may therefore encounter an **input-side** scalability bottleneck
even while sparse output remains compact. No repository-size threshold is
derived from this single djangoCMS point, and graph scoping is not claimed to
be uniquely necessary. Possible future candidate-scoping mechanisms (soft
dependency-graph evidence, retrieval-based candidate generation, hierarchical
localization, repository summaries, learned/ranked retrieval) must be evaluated
carefully because hard exclusion of a true gold candidate before LLM selection
imposes an upper bound on achievable Recall. This study uses NO graph
assistance.

## 10. Mathematical design note (future v3, DESIGN-ONLY)

See `docs/RISK_AWARE_SPARSE_IMPACT_SELECTION_MODEL.md`. It formalizes a
risk-aware selection model (binary and four-action generalizations) with
token-cost pricing. It is DESIGN / THEORY for a possible future v3, was written
with ZERO scientific calls, and did NOT modify v2 code or results.

## 11. Post-study closure

- Six closure gates + independent audit: **PASS** (zero scientific calls).
- Primary evidence immutable: **71/71** unchanged; 8192 probe, 16K diagnostic,
  and v2 cost-probe evidence unchanged.
- Manifest immutable: exactly 30 cells; exactly 30 records; no run 31.
- Completion cap stayed 4096; model/provider/fallback/temperature frozen;
  graph absent; raw responses persisted (30/30 SHA-verified).
- Hidden gold remained evaluation-only; metrics trace to raw evidence.
- Provenance parity evidence did not alter the treatment.