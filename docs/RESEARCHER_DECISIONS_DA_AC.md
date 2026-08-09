# Researcher Decision Records — Phase 2B Protocol Freeze

**Date:** 2026-07-22
**Source:** `docs/FINAL_RESEARCH_PROTOCOL_DECISIONS.md`

---

## DA-01 — Repository Eligibility

- **Decision:** A repository is eligible only if it has a runnable automated test suite or a scientifically defensible scenario-relevant subset plus a fixed regression suite. Exclude and replace only when no defensible validation configuration is possible.
- **Rationale:** Avoids premature exclusion while maintaining scientific defensibility.
- **Applied to:** `docs/FINAL_RESEARCH_PROTOCOL.md §10`, `docs/SCENARIO_TAXONOMY.md §6`

## DA-02 — Licence Changes

- **Decision:** Record the licence and exact commit at protocol freeze. If redistribution is restricted, publish a commit reference and acquisition script instead of source. Replace a repository only if the pinned version cannot legally be used or executed.
- **Rationale:** Ensures legal compliance without unnecessary repository churn.
- **Applied to:** `docs/REPRODUCIBILITY_PROTOCOL.md §3`

## DA-03 — Repository Version

- **Decision:** Use a tagged stable release or stable-branch commit at least 90 days old, with reproducible dependencies and a functioning test setup. Record the exact SHA before scenario construction. Do not use an arbitrary six-month rule.
- **Rationale:** Corrects the draft's imprecise "6 months" to a precise 90-day minimum.
- **Applied to:** `docs/SCENARIO_TAXONOMY.md §6`

## DA-04 — Inter-Annotator Agreement

- **Decision:** Cohen's κ ≥ 0.80 strong; 0.70–0.79 acceptable with adjudication; <0.70 refine guide, recalibrate, and re-annotate. Report pre-adjudication agreement overall, per repository, and per action class.
- **Rationale:** Establishes clear quality tiers instead of a single threshold.
- **Applied to:** `docs/GROUND_TRUTH_PROTOCOL.md §5`

## DA-05 — Unresolved Disagreement

- **Decision:** Two independent annotations → documented adjudication discussion → third qualified adjudicator if unresolved → `human_review` only when evidence remains genuinely insufficient. Retain all original labels and rationales.
- **Rationale:** Adds a structured escalation before falling back to `human_review`.
- **Applied to:** `docs/GROUND_TRUTH_PROTOCOL.md §6`

## DA-06 — Annotators

- **Decision:** Researcher/author + one independent Python/Django-capable software engineer or researcher + supervisor for adjudication. Independent annotator needs ≥1 year experience and must complete a pilot exercise.
- **Rationale:** Defines minimum qualifications and training requirement.
- **Applied to:** `docs/GROUND_TRUTH_PROTOCOL.md §4.1`

## DA-07 — Scenario Replacement

- **Decision:** Allowed before main execution only for infeasibility, duplication, ambiguity, licensing, or infrastructure. Must preserve repository, change type, and blast-radius class where possible. No replacement after seeing poor model/strategy performance. If no valid replacement exists, retain and report reduced N.
- **Rationale:** Prevents post-hoc selection bias.
- **Applied to:** `docs/SCENARIO_TAXONOMY.md §7`

### DA-07 Amendment 001 (PILOT-READY-01, applied before any Pilot result)

- **ID:** DA-07-A001
- **Date:** 2026-08-09
- **Trigger:** Infeasibility of `djangocms-loc-001` at the frozen repository revision.
- **Already-observed results:** None (amendment recorded before any Pilot execution; no strategy/model results observed).
- **Old rule / set:** Pilot set contained `djangocms-loc-001` (add `meta_description` to `PageContent`).
- **Finding:** At pinned django-cms `0f633fc9fa213357f4202482aab2b0edad680f95` (v5.0.0), `PageContent` already defines `meta_description` in `cms/models/contentmodels.py` (~line 58, `TextField(blank=True, null=True)`). The requirement is therefore already satisfied; executing it would be a no-op with no defensible before/after contrast. (For completeness, `djangocms-loc-003` — add `position` ordering to `CMSPlugin` — is also infeasible: `CMSPlugin` already has `position` with `unique_together=("placeholder", "language", "position")` in `cms/models/pluginmodel.py`.)
- **New rule / set:** Replace `djangocms-loc-001` with `djangocms-mod-005` (new `page reviewer` permission level: `can_review` on `PagePermission`/`GlobalPermission`, `has_review_permission`, admin review action, toolbar item). Preserves repository (djangocms), preserves all three blast-radius classes per repository (djangocms now: localized `loc-002`, moderate `mod-004` + `mod-005`, cross-cutting `cross-007`), and is coherent with `djangocms-cross-007`, which explicitly references "leveraging djangocms-mod-005". Scenario ID was verified feasible against the pinned revision (no existing `can_review` field; permission-check functions live in `cms/utils/page_permissions.py`).
- **Affected config/artifacts:** `configs/pilot.yaml` `scenario_selection.scenario_ids`; `PROFILES["pilot"]` in `seven_arm_benchmark.py`; `PILOT_SCENARIO_IDS` in `tests/unit/test_pilot_readiness.py` and `tests/integration/test_scenarios_integration.py`; `tests/unit/test_cli.py` pilot-profile assertion.
- **Approval:** Recorded in the decision/change ledger before any Pilot execution, per AC-11 / DA-07.

## DA-08 — Non-Inferiority Margin

- **Decision:** Δ = 0.05 for regression pass rate. One-sided 95% CI lower bound > -0.05. Also report two-sided 95% CI and sensitivity at 0.03 and 0.10.
- **Rationale:** Confirms the proposed margin and adds sensitivity analysis requirement.
- **Applied to:** `docs/STATISTICAL_ANALYSIS_PLAN.md §3`

## DA-09 — Execution Budget

- **Decision:** Three stages (smoke, pilot, main). 8.6M token estimate is not a hard budget. Freeze per-run budgets after pilot. If balanced design infeasible, stop and approve reduced design before main execution.
- **Rationale:** Replaces draft's hard token estimate with stage-gated approach.
- **Applied to:** `docs/EXECUTION_AND_FAILURE_POLICY.md §1`

## DA-10 — Hosting

- **Decision:** GitHub for source/docs/configs/scenarios/cleared notebook. Zenodo for immutable archived release and DOI. Kaggle Datasets for executable bundles. OSF or institutional repository if Zenodo unavailable.
- **Rationale:** Confirms hosting strategy with fallback.
- **Applied to:** `docs/REPRODUCIBILITY_PROTOCOL.md §2`

## DA-11 — Licences

- **Decision:** MIT for original code/scripts. CC BY 4.0 for original documentation/scenarios/guides/metadata. Original upstream licences for third-party content. Component-level licence manifest required.
- **Rationale:** Resolves the draft's ambiguity between MIT and CC-BY.
- **Applied to:** `docs/REPRODUCIBILITY_PROTOCOL.md §3`

## DA-12 — Model Outputs

- **Decision:** Redistribute raw outputs only where licences and platform terms permit. Scan for secrets, personal data, credentials, and local path disclosure. Classify outputs as public raw, public sanitized, metadata only, or unavailable.
- **Rationale:** Adds classification scheme and security scanning requirement.
- **Applied to:** `docs/REPRODUCIBILITY_PROTOCOL.md §4`

## DA-13 — FPR Threshold

- **Decision:** FPR no more than 0.10 above best non-hybrid comparator. Median predicted impact set no more than 2x ground-truth impacted-set size without explicit justification. Report full precision-recall trade-off.
- **Rationale:** Adds impact-set inflation guardrail to prevent trivial near-whole-repository selection.
- **Applied to:** `docs/FINAL_RESEARCH_PROTOCOL.md §3 (H1)`, `docs/STATISTICAL_ANALYSIS_PLAN.md`

## DA-14 — Multiple Comparisons

- **Decision:** No blanket correction across H1–H5. Benjamini-Hochberg within secondary/exploratory families. Holm for small confirmatory pairwise families. Report raw and adjusted p-values.
- **Rationale:** Refines the draft's mixed Bonferroni/BH proposal to precise rules.
- **Applied to:** `docs/STATISTICAL_ANALYSIS_PLAN.md §4`

---

## Mandatory Corrections

### AC-01 — Candidate Artifact Universe
- **Correction:** Freeze candidate universe per repository and scenario before strategy execution. Include tracked source, tests, migrations, API/schema, documentation, configuration, architecture artifacts. Document exclusions. Report TN/FPR only when universe complete.
- **Applied to:** `docs/GROUND_TRUTH_PROTOCOL.md §3`, `docs/LEAKAGE_PREVENTION_PROTOCOL.md §3`

### AC-02 — Preservation Formula
- **Correction:** Regression pass rate = passed / total. Regression failure rate = newly failing / total. Report counts and rates. Remove "regressed / total, inverted" wording.
- **Contradiction corrected:** Draft §9.3 had the incorrect inverted formula. The frozen version uses the corrected formula.
- **Applied to:** `docs/STATISTICAL_ANALYSIS_PLAN.md §9`, `docs/FINAL_RESEARCH_PROTOCOL.md §9`

### AC-03 — Hidden Tests vs. Held-Out Scenarios
- **Correction:** Hidden tests mandatory for every scenario and inaccessible to strategies. Held-out scenarios optional (2 per repo). Cross-validation is not a substitute.
- **Contradiction corrected:** Draft §16.2 offered cross-validation as an alternative. Frozen version makes clear cross-validation is not a substitute.
- **Applied to:** `docs/SCENARIO_TAXONOMY.md §8`, `docs/LEAKAGE_PREVENTION_PROTOCOL.md §2`

### AC-04 — Failed Strategies
- **Correction:** Do not remove a strategy from repository aggregates merely because all runs fail. Include failures in attempted-run success rate, failure taxonomy, and robustness analysis.
- **Contradiction corrected:** Draft §15.4 said "marked as excluded from that repository's aggregate." Frozen version requires failures to remain.
- **Applied to:** `docs/EXECUTION_AND_FAILURE_POLICY.md §5`

### AC-05 — Uniform Repairs
- **Correction:** One initial generation, maximum two LLM repair attempts, deterministic normalization only when strategy-independent and logged. Freeze after pilot.
- **Contradiction corrected:** Draft §15.2 said "Maximum repair iterations: 3." Frozen version reduces to maximum 2.
- **Applied to:** `docs/EXECUTION_AND_FAILURE_POLICY.md §4`

### AC-06 — Execution Order
- **Correction:** Sequential scenarios in predefined evolution order. Randomize or counterbalance strategy order and repository order. Fresh run directories. Record order seeds.
- **Applied to:** `docs/EXECUTION_AND_FAILURE_POLICY.md §2`

### AC-07 — Determinism
- **Correction:** Temperature 0 and fixed seeds do not guarantee identical GPU outputs. Record hardware, CUDA, kernels, quantization, packages, parameters, seeds. Best-effort reproducibility.
- **Contradiction corrected:** Draft §13.4 stated "temperature=0" produced identical outputs. Frozen version corrects this for GPU execution.
- **Applied to:** `docs/LEAKAGE_PREVENTION_PROTOCOL.md §9`, `docs/REPRODUCIBILITY_PROTOCOL.md §7`

### AC-08 — Kaggle Cost
- **Correction:** Report tokens, GPU time, wall time. Do not invent API monetary cost. Any estimated cost must state assumptions and not be presented as an observed charge.
- **Contradiction corrected:** Draft §9.5 listed "Estimated monetary cost: USD." Frozen version requires this field to state assumptions explicitly.
- **Applied to:** `docs/EXECUTION_AND_FAILURE_POLICY.md §8`

### AC-09 — H3 Evidence
- **Correction:** Report count and proportion of verified architecture-only detections. One isolated violation is evidence of possibility, not strong general support.
- **Applied to:** `docs/FINAL_RESEARCH_PROTOCOL.md §3 (H3)`

### AC-10 — H5 Trend
- **Correction:** Evaluate strategy × blast-radius interaction, trend estimates with CI, per-repository curves. Perfect monotonicity not required.
- **Contradiction corrected:** Draft §20.5 required monotonic decrease. Frozen version allows non-monotonic local deviations.
- **Applied to:** `docs/FINAL_RESEARCH_PROTOCOL.md §3 (H5)`

### AC-11 — Protocol Amendments
- **Correction:** After first main result observed, no silent changes. Every amendment must record ID, date, trigger, already-observed results, old rule, new rule, rationale, approval, affected analyses.
- **Applied to:** `docs/FINAL_RESEARCH_PROTOCOL.md §11`, `docs/REPRODUCIBILITY_PROTOCOL.md §9`
