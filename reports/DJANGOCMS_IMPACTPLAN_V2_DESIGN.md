# DJANGOCMS IMPACTPLAN-V2 DESIGN

**Status:** POST-HOC / EXPLORATORY REDESIGN
**Date (UTC):** 2026-09-08
**Branch:** `research/djangocms-external-validity-prep-01`
**Treatment ID:** `impact_plan_v2`
**Probe ID:** `scientific-stagec-djangocms-impactplan-v2-costprobe-01`

---

## 1. Objective

Remove the repository-wide explicit PRESERVE serialization bottleneck of the
primary ImpactPlan representation while preserving:

- the full ImpactPlan semantics (every candidate classified exactly once;
  `write_set == {R}`; P/V/H not writable; action sets pairwise disjoint;
  rationale/confidence/reason_codes/evidence retained for non-PRESERVE
  decisions);
- auditability;
- the SAME 144-file candidate universe;
- correctness evaluation;
- single-call explicit planning.

ImpactPlan-v2 is a **representation redesign**, NOT a schema-only ablation and
NOT a prompt-only ablation.

## 2. V1 -> V2 change is one representation redesign

v1 instructed the model to classify EVERY candidate explicitly (full
repository-wide action serialization). v2 necessarily instructs the model to
emit ONLY non-PRESERVE decisions. Therefore:

- v2 changes the output representation contract AND the corresponding planner
  instruction **together**;
- these changes are inseparable by construction (a sparse output representation
  requires a sparse instruction);
- prompt effects and schema effects are **NOT independently isolated**;
- ImpactPlan-v2 is treated as ONE representation redesign.

## 3. V2 representation

Let `V` = the frozen 144-path candidate universe
(`benchmark_data/external_validity/djangocms_5_0_0_candidate_universe.json`,
canonical hash `43f4279bdf228745b1f6b289c81cda141b089ab5be4f4af63bb8f39f837c4410`).

### 3.1 Deterministic frozen numeric candidate IDs

`candidate_id -> repository_path` mapping (IDs `1..144`):

- derived deterministically from the frozen universe records (path-sorted);
- exactly 144 entries;
- scenario-independent and hidden-gold-independent;
- frozen before inference;
- persisted as an artifact
  (`benchmark_data/external_validity/impactplan_v2_candidate_id_map.json`)
  together with its SHA-256
  (`9d33e163505722e2cfe602ca165777d3d5accbaf5b9f7a82d1b30068ca9d1ca6`);
- identical for every future v2 run (the harness derives the mapping at run
  time from the frozen universe and fail-closes on any artifact mismatch).

The candidate universe is NOT reduced.

### 3.2 Sparse output semantics

The model emits ONLY candidates whose action is NOT PRESERVE.

Allowed explicit actions:

- `REGENERATE`
- `VALIDATE`
- `HUMAN_REVIEW`

For every candidate omitted from the model output, the harness decodes
deterministically:

```
omitted candidate => PRESERVE
```

The final reconstructed action policy classifies every candidate exactly once:

```
pi : V -> {R, P, V, H}
```

The final decoded policy contains EXACTLY 144 candidate decisions even though
the model emits only a sparse subset. After decoding:

```
R union P union V union H = V
```

and `R, P, V, H` are pairwise disjoint; decoded candidate count == 144 exactly;
no candidate invented; no candidate lost.

### 3.3 Structured output

v2 uses the project's EXISTING structured-output / JSON-schema mechanism
(OpenRouter native `response_format.type=json_schema`). Structured output is
NOT a new v2 contribution — v1 already used structured output. v2 supplies a
v2-specific sparse schema.

V2 sparse schema (approximate):

```json
{
  "decisions": [
    {
      "id": <integer>,
      "action": <"REGENERATE" | "VALIDATE" | "HUMAN_REVIEW">,
      "rationale": <string>,
      "confidence": <number>,
      "reason_codes": [...],
      "evidence": [...]
    }
  ],
  "validation_obligations": [...],
  "architecture_checks": [...],
  "escalation_reason": ""
}
```

No explicit PRESERVE decisions are emitted; 144 serialized decision objects are
NOT required. `context_set` is not carried into v2 (not scientifically
necessary for the decoded action policy).

### 3.4 Numeric ID validation (fail-closed)

The JSON Schema constrains `id.minimum = 1` and `id.maximum = 144`. The harness
additionally enforces invariants JSON Schema alone may not guarantee and
rejects fail-closed when:

- `id < 1`;
- `id > 144`;
- `id` does not exist in the frozen mapping;
- duplicate ID;
- the same candidate receives multiple decisions (conflict);
- unsupported action;
- malformed structured output;
- mapping hash mismatch;
- ambiguous decoding.

## 4. Prompt / schema identity (persisted + hashed)

Both the exact v1 and exact v2 planner prompts and schemas are persisted and
hashed in the probe evidence:

| Item | SHA-256 |
|---|---|
| v1 planner prompt (`impact_planner.py` `PLANNER_PROMPT_TEMPLATE`) | `d6f8798d2c131afdf8289b01d4b4d826eb5fa997e1f1d748303f3d1a362312fb` |
| v1 structured schema (`IMPACT_PLAN_SCHEMA`) | `12152c5947319fdc85313e0024542c7ea63301c62ebea847f005d71dc8dc87ee` |
| v2 planner prompt (`impact_planner_v2.py` `IMPACT_PLAN_V2_PROMPT_TEMPLATE`) | `69c2e44d9408d9db95334bafe62cfc706475b2838bffa85e59da543bdbd7cea0` |
| v2 structured schema (`IMPACT_PLAN_V2_SCHEMA`) | `98f7eb91774c29867b09a3d4af21cdbb2f65a05e073efe430531a5f3b0fe9392` |

v1 default completion cap remains **4096**. v2 completion cap is **4096** (the
original frozen ImpactPlan-v1 primary cap). Actual consumed completion tokens
remain an efficiency metric.

## 5. Graph assistance is NOT part of v2

ImpactPlan-v2 does NOT inject dependency-graph assistance:

- the v2 module (`src/benchmark/selection/impact_planner_v2.py`) contains no
  dependency-graph import or usage;
- the v2 probe strategy is instantiated with the same empty
  `DependencyGraph()` default as the primary djangoCMS ImpactPlan strategy;
- candidates are neither graph-pruned nor graph-ranked;
- graph-assisted planning is a separate possible future treatment.

## 6. Primary djangoCMS ImpactPlan graph limitation (documented fact)

The primary djangoCMS ImpactPlan strategy was instantiated WITHOUT the frozen
dependency graph. Therefore the primary djangoCMS study
(`scientific-stagec-djangocms-01`) characterizes **explicit-plan selection
WITHOUT dependency-graph assistance**: the frozen 144-node / 562-edge AST
graph was NOT strategy-visible evidence in the primary ImpactPlan treatment.
This is stated in `reports/BENCHMARK_VALIDITY_AND_LIMITATIONS.md` and
`reports/RESEARCH_TRUTH_MATRIX.md`.

## 7. Interpretive constraints (frozen)

- The single 16K observation where the unchanged v1 planner fallback
  deterministically classified the one omitted candidate
  (`cms/toolbar/utils.py`) as PRESERVE and that happened to be correct is an
  **illustrative empirical observation** that deterministic omitted=>P decoding
  is operationally feasible. It does NOT prove omitted=>P is universally safe.
- The persisted 16K raw response shows the majority of explicit v1 decision
  entries were PRESERVE. Derived token-per-entry estimates are NOT universal
  constants.
- Any projected v2 token savings from the 16K response are labeled
  **PRE-EXPERIMENT ESTIMATE** until measured by v2.

## 8. Implementation artifacts

| Artifact | Path |
|---|---|
| v2 module (schema, prompt, mapping, decode, planners) | `src/benchmark/selection/impact_planner_v2.py` |
| v2 deterministic tests | `tests/unit/selection/test_impact_plan_v2.py` |
| candidate ID mapping artifact | `benchmark_data/external_validity/impactplan_v2_candidate_id_map.json` |
| v2 cost/smoke probe runner | `scripts/stagec_djangocms_impactplan_v2_costprobe_execute.py` |
| probe evidence | `reports/scientific-stagec-djangocms-impactplan-v2-costprobe-01/` |
| probe report | `reports/DJANGOCMS_IMPACTPLAN_V2_COSTPROBE.md` |

## 9. What v2 does NOT do

- Does NOT modify or rerun the frozen primary 60-run study.
- Does NOT run the future 30 v2 cells.
- Does NOT start Saleor.
- Does NOT inject dependency-graph assistance.
- Does NOT claim to isolate prompt effects from schema effects.
- Does NOT reduce the candidate universe.