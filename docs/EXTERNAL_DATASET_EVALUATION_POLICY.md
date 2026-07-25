# External Dataset Evaluation Policy

**Date:** 2026-07-25
**Branch:** docs/research-design-v2
**Protocol Version:** 1.0 (FROZEN)
**Source Commit:** 3a16596
**Status:** POLICY — Research Design V2 Decision (RD-V2-06)

---

## 1. Purpose

This policy governs **Experiment D — Optional External Transfer** (per RD-V2-06). It defines eligibility criteria for external datasets, mandates local execution of all conditions, and prohibits invalid cross-study statistical comparisons.

---

## 2. Eligibility Criteria

An external dataset is **eligible** for Experiment D **only if** it provides **all** of the following:

| Criterion | Requirement | Verification |
|-----------|-------------|--------------|
| **Usable license** | Permissive (MIT, Apache-2.0, BSD) or academic research license allowing redistribution and modification | License file inspection; legal review if ambiguous |
| **Input changes** | Natural-language requirement changes (before/after) or equivalent diff specifications | Schema validation; manual spot-check of 10% sample |
| **Artifact corpus** | Complete repository snapshot at specific commit with identifiable artifact paths | `git clone` verification; path mapping to `ArtifactUniverse` |
| **Ground truth** | Human-annotated or mechanically verified affected artifact sets per change | Annotation quality assessment; inter-rater agreement if human |
| **Compatible unit of analysis** | Artifact-level impact prediction (path → regenerate/preserve) matching our `ImpactDecision` schema | Schema mapping documented; no semantic gaps |
| **No answer leakage** | Ground truth not derivable from input change text alone (e.g., no trivial naming overlaps) | Leakage analysis: compute string-similarity baseline; must achieve < 0.7 F1 |
| **Reproducible preprocessing** | Deterministic scripts to convert raw dataset → our scenario format | Scripts provided; hash-verified outputs |
| **Metrics comparable** | Can compute our primary metrics (precision, recall, F1, FNR, impact-set size) on local execution | Metric computation verified on sample |

---

## 3. Mandatory Local Execution

**All local conditions MUST be run on the same external dataset.**

| Condition | Local Arms Required |
|-----------|---------------------|
| Baseline | `repository_agent` (or `single_shot_llm_scope` if iterative not ready) |
| Treatment | `hybrid_selective` |
| Ablations | `static_only`, `semantic_only`, `traceability_only` |
| Reference | `full_scope_reference` |

**No exceptions.** Published scores from the original paper are **contextual only**.

---

## 4. Prohibited Comparisons

The following are **explicitly forbidden** in any scientific document:

| Prohibited Comparison | Reason |
|----------------------|--------|
| Local `hybrid_selective` F1 vs. published `Compiled AI` F1 | Different environment, model, data splits, preprocessing |
| Local `repository_agent` recall vs. published `RepoCoder` recall | Uncontrolled confounders (model, prompt, budget, repo version) |
| Statistical test (t-test, Wilcoxon) between local and published scores | Not paired, not same distribution, not same conditions |
| Effect size (Cohen's d) between local and published results | Incomparable measurement boundaries |
| Ranking table mixing local and published scores | Apples-to-oranges; invalidates scientific claims |

---

## 5. Permitted Contextual Reporting

Published scores from incompatible environments may be reported **only as**:

1. **Contextual cross-study evidence** — clearly labeled: *"Published result from [Paper], different environment/model/data — not directly comparable"*
2. **Qualitative discussion** — *"Our hybrid_selective achieves X F1; for context, Compiled AI reported Y F1 on a similar but incompatible setup"*
3. **External validity discussion** — *"Results align qualitatively with trends observed in [Paper]"*

**Format requirement:** Any table/figure including published scores MUST:
- Use visual separation (different panel, color, or line style)
- Include footnote: *"Published scores from different experimental conditions — contextual only"*
- NOT appear in the same statistical aggregation

---

## 6. Candidate Evaluation Criteria (Not Selection)

The following criteria should be used to **evaluate** candidate datasets. **No dataset is selected yet.**

| Criterion | Weight | Assessment Method |
|-----------|--------|-------------------|
| License permissiveness | High | Legal review |
| Annotation quality (F1, agreement) | High | Spot-check + kappa |
| Repository diversity (languages, sizes, domains) | Medium | Profile analysis |
| Change type coverage (localized, cross-cutting) | Medium | Taxonomy mapping |
| Scale (number of scenarios) | Low | Count |
| Prior use in literature (comparability) | Low | Citation check |
| Preprocessing effort | Low | Engineering estimate |

**Decision process:** When a dataset is proposed, evaluate against all criteria. Require researcher approval before download/execution.

---

## 7. Implementation Requirements

### 7.1 Dataset Adapter

```python
class ExternalDatasetAdapter:
    def load_scenarios(self) -> list[Scenario]: ...
    def load_ground_truth(self) -> dict[str, set[str]]: ...
    def verify_license(self) -> bool: ...
    def verify_no_leakage(self) -> LeakageReport: ...
```

### 7.2 Execution Script

```bash
# Must produce identical output format as local benchmark
python seven_arm_benchmark.py \
  --profile research \
  --data-dir /path/to/external/dataset \
  --output-dir /path/to/external/results \
  --strategy ALL
```

### 7.3 Reporting

Separate report: `reports/EXPERIMENT_D_EXTERNAL_TRANSFER.md`
- Local results table (all 7 arms)
- Published scores table (with contextual disclaimers)
- Qualitative comparison only
- No statistical tests vs. published

---

## 8. Policy Enforcement

| Checkpoint | Validation |
|------------|------------|
| Dataset proposal | Researcher signs off on eligibility checklist |
| Pre-execution | Automated leakage scan; license verification |
| Post-execution | Report review for prohibited comparisons |
| Publication | Co-author checklist: "No invalid cross-study claims" |

---

## 9. Status

**No external dataset selected.** This policy establishes the gate. Experiment D is **not authorized** until:
1. Dataset proposed and evaluated
2. Researcher approves
3. Local execution complete
4. Report reviewed for policy compliance

---

**Policy Status:** FROZEN for RD-V2
**Authority:** Researcher decision required for dataset selection
**Related:** `docs/EXPERIMENTAL_DESIGN_V2.md` (Experiment D definition)