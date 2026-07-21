# Final Research Protocol — v1.0 (FROZEN)

## Dependency-Aware Selective Regeneration Benchmark

```yaml
protocol_version: 1.0
protocol_status: FROZEN
approved_for_phase_3: true
approval_date: 2026-07-22
authoritative_source: inputs/paper/MSc_Proposal_Selective_Regeneration_Revised.tex
```

---

## 1. Research Scope

- **Language:** Python
- **Primary framework ecosystem:** Django
- **Real-model execution platform:** Kaggle
- **Primary model:** Qwen2.5-Coder (attached as a Kaggle Model)
- **Local machine:** Engineering validation only; no local LLM download or inference

### Primary Repositories

| Size | Repository | Status |
|------|-----------|--------|
| Small | Controlled Django Todo application | Confirmatory |
| Medium | django CMS | Confirmatory |
| Large | Saleor Core | Confirmatory |

ERPNext is excluded from the confirmatory protocol and retained only as an optional future stress case.

### Scenario Distribution

Per repository: 8 scenarios = 3 localized, 3 moderate, 2 cross-cutting.
Total confirmatory target: 24 scenarios.

---

## 2. Research Questions

| ID | Question | Primary Hypothesis | Eval Phase |
|----|----------|-------------------|------------|
| RQ1 | How accurately can dependency-aware approaches identify heterogeneous software artifacts affected by a natural-language requirement change? | H1 | Eval Phase 1 (impact analysis only) |
| RQ2 | Can selective regeneration implement changed requirements while preserving behaviour that should remain unchanged? | H2 | Eval Phase 2 (controlled evolution) |
| RQ3 | To what extent can architecture-aware selective regeneration preserve declared architectural and design constraints during evolution? | H3 | Eval Phase 3 (architecture evaluation) |
| RQ4 | Under equivalent correctness conditions, how much regeneration work, token consumption, model calls, latency, and estimated cost can selective regeneration avoid relative to repository-retrieval agent workflows? | H4 | Eval Phase 2 + 4 |
| RQ5 | How do repository architecture, project size, change type, dependency strategy, and LLM choice influence impact accuracy and selective-regeneration benefit? | H5 | Eval Phase 4 (sensitivity) |

---

## 3. Hypotheses

### H1 — Hybrid Impact Superiority
- **Comparison:** Hybrid graph vs. static-only, semantic-only, traceability-only, and retrieval-only impact analysis
- **Primary measures:** Recall, false-negative rate, precision, F1, action-classification macro F1, impact-set inflation
- **Criterion:** Supported if hybrid improves recall and reduces FNR. FPR no more than 0.10 above the best non-hybrid comparator. Median predicted impact set no more than 2x ground-truth impacted-set size without explicit justification. Full precision-recall trade-off must be reported.

### H2 — Preservation Non-Inferiority
- **Comparison:** Selective execution vs. repository-agent baseline on matched changes
- **Primary measures:** Changed-requirement success, regression pass rate, NI result, unintended out-of-scope source changes
- **Criterion:** Non-inferior with Δ = 0.05 for regression pass rate (one-sided 95% CI lower bound > -0.05). Also report two-sided 95% CI and sensitivity at Δ = 0.03 and 0.10.

### H3 — Architecture Validation Gap
- **Comparison:** Functional tests alone vs. functional plus architecture validation
- **Primary measures:** Verified architecture-only detections, architecture-rule pass rate, boundary violations
- **Criterion:** Supported if architecture checks reveal violations not detected by functional tests. One isolated violation is evidence of possibility, not strong general support. Report counts and proportions.

### H4 — Selective Efficiency
- **Comparison:** Successful selective runs vs. equivalently correct baseline runs (localized + moderate changes)
- **Primary measures:** Regenerated artifacts, input/output tokens, model calls, wall-clock time
- **Criterion:** Efficiency reported only under equivalent correctness conditions. Effect size with confidence interval.

### H5 — Blast Radius Boundary
- **Comparison:** Changes grouped by blast radius and change type
- **Primary measures:** Strategy × blast-radius interaction, savings trend, repository-level sensitivity
- **Criterion:** Evaluate interaction, trend estimates with confidence intervals, per-repository curves. Perfect monotonicity not required.

---

## 4. Strategy Set

### Impact Evaluation
- `repository_agent` (as retrieval/impact predictor)
- `static_only`
- `semantic_only`
- `traceability_only`
- `hybrid_selective`
- `full_context` (only when meaningful and feasible)

### Full Evolution
- `repository_agent` — agentic baseline
- `hybrid_selective` — proposed method
- `static_only`
- `semantic_only`

`traceability_only` full generation is optional/exploratory. `full_regeneration` and `full_context` are reference strategies, not mandatory for every repository.

### Ablations (Impact-Only)
- hybrid minus semantic
- hybrid minus static
- hybrid minus traceability
- hybrid minus architecture

Generation ablations use a balanced pre-specified subset only.

---

## 5. Primary Outcomes per RQ

### RQ1/H1
- recall
- false-negative rate
- precision
- F1
- action-classification macro F1
- impact-set inflation

### RQ2/H2
- changed-requirement success
- regression pass rate
- NI result (Δ = 0.05)
- unintended out-of-scope source changes

### RQ3/H3
- verified architecture-only detections
- architecture-rule pass rate
- boundary violations

### RQ4/H4
Among equivalently correct runs: regenerated artifacts, input/output tokens, model calls, wall-clock time.

### RQ5/H5
Strategy × blast-radius interaction, savings trend, repository-level sensitivity.

Secondary measures include first-pass success, repair count, context size, explainability, quality deltas, validation latency, and peak GPU memory. No composite "software quality score" is approved.

---

## 6. Execution Budget (Three Stages)

### Smoke
One controlled scenario; mock backend locally; one real Qwen Kaggle orchestration run. Non-publication evidence.

### Pilot
Three repositories, four scenarios each, two strategies (`repository_agent`, `hybrid_selective`), two repetitions. Descriptive only.

### Main
All 24 scenarios. Impact-only strategies run without generation where possible. Full evolution uses `repository_agent`, `hybrid_selective`, `static_only`, `semantic_only`. Three repetitions per stochastic scenario-strategy cell.

Freeze per-run budgets (input tokens, output tokens, model calls, repair calls, timeouts) after the pilot. If the balanced confirmatory design is infeasible, stop and approve a balanced reduced design before main execution.

---

## 7. Sequential and Failure Policy

Each strategy starts from the same clean snapshot. Scenarios applied sequentially. Only an accepted state becomes the next scenario's base state. If a scenario fails after the repair budget, stop that sequential chain for that strategy. Also run remaining scenarios independently from predefined base snapshots for per-scenario analysis. Report sequential-chain and independent-scenario results separately.

Failure classes: infrastructure, model output, build, changed requirement, regression, architecture, timeout, benchmark-harness defect. Harness defects are corrected and rerun under pilot rules or a protocol amendment; they are not strategy failures.

Failed strategies remain in results. Do not remove a strategy from repository aggregates merely because all runs fail. Include failures in attempted-run success rate, failure taxonomy, and robustness analysis. Conditional metrics among successful runs must be labelled conditional.

---

## 8. Researcher-Approved Decisions (DA-01 through DA-14)

| ID | Topic | Approved Decision |
|----|-------|-------------------|
| DA-01 | Repository eligibility | Eligible only if it has a runnable automated test suite or a scientifically defensible scenario-relevant subset plus a fixed regression suite. Exclude and replace only when no defensible validation configuration is possible. |
| DA-02 | Licence changes | Record the licence and exact commit at protocol freeze. If redistribution is restricted, publish a commit reference and acquisition script instead of source. Replace only if the pinned version cannot legally be used or executed. |
| DA-03 | Repository version | Use a tagged stable release or stable-branch commit at least 90 days old, with reproducible dependencies and a functioning test setup. Record the exact SHA before scenario construction. |
| DA-04 | Inter-annotator agreement | Cohen's κ ≥ 0.80 strong, 0.70–0.79 acceptable with adjudication, <0.70 refine and re-annotate. Report pre-adjudication agreement overall, per repository, and per action class. |
| DA-05 | Unresolved disagreement | Two independent annotations → documented adjudication → third qualified adjudicator → human_review only as last resort. Retain all original labels and rationales. |
| DA-06 | Annotators | Researcher/author + one independent Python/Django-capable software engineer or researcher + supervisor for adjudication. Independent annotator needs ≥1 year practical/research experience and must complete a pilot exercise. |
| DA-07 | Scenario replacement | Allowed before main execution only for infeasibility, duplication, ambiguity, licensing, or infrastructure reasons. Must preserve repository, change type, and blast-radius class where possible. No replacement after seeing poor model/strategy performance. |
| DA-08 | Non-inferiority margin | Δ = 0.05 for regression pass rate. Selective is non-inferior when lower bound of one-sided 95% CI for selective minus baseline > -0.05. Also report two-sided 95% CI and sensitivity at 0.03 and 0.10. |
| DA-09 | Execution budget | Three stages (smoke, pilot, main). 8.6M token estimate is not a hard budget. Freeze per-run budgets after pilot. If balanced design infeasible, stop and approve reduced design. |
| DA-10 | Hosting | GitHub for source/docs/configs/scenarios/cleared notebook. Zenodo for immutable archived release and DOI. Kaggle Datasets for executable bundles. Use OSF or institutional repository if Zenodo unavailable. |
| DA-11 | Licences | MIT for original benchmark code and scripts. CC BY 4.0 for original documentation, scenarios, guides, and research metadata. Original upstream licences for third-party content. Create component-level licence manifest. |
| DA-12 | Model outputs | Redistribute raw outputs only where licences and platform terms permit. Scan for secrets, personal data, credentials, and local path disclosure. Classify outputs as public raw, public sanitized, metadata only, or unavailable. |
| DA-13 | FPR threshold | FPR no more than 0.10 above best non-hybrid comparator. Median predicted impact set no more than 2x ground-truth impacted-set size without explicit justification. Report full precision-recall trade-off. |
| DA-14 | Multiple comparisons | No blanket correction across the five pre-specified primary hypotheses. Benjamini-Hochberg within secondary/exploratory families. Holm for small confirmatory pairwise families. Report raw and adjusted p-values. |

---

## 9. Mandatory Corrections Applied (AC-01 through AC-11)

| ID | Correction |
|----|-----------|
| AC-01 | Candidate artifact universe frozen per repository and scenario before strategy execution. Document exclusions. Report TN/FPR only when universe is complete. |
| AC-02 | Regression pass rate = passed regression tests / total regression tests. Regression failure rate = newly failing regression tests / total regression tests. Report counts and rates. |
| AC-03 | Hidden changed-requirement and regression tests mandatory per scenario, inaccessible to strategies. Held-out scenarios (2 per repo) optional but not a substitute for hidden tests. Cross-validation is not a substitute. |
| AC-04 | Failed strategies remain in repository aggregates. Conditional metrics labelled. Failure taxonomy reported. |
| AC-05 | Uniform repair budget across comparable generative strategies: one initial generation, maximum two LLM repair attempts, deterministic normalization only when strategy-independent and logged. Freeze after pilot. |
| AC-06 | Sequential scenarios in predefined evolution order. Randomize or counterbalance strategy order and repository order across repetitions. Fresh run directories. Record order seeds. |
| AC-07 | Temperature zero and fixed seeds do not guarantee identical GPU LLM outputs. Record hardware, CUDA, kernels, quantization, packages, parameters, and seeds. Best-effort reproducibility. Retain repeated runs. |
| AC-08 | Report tokens, GPU time, wall-clock time, and Kaggle resource use. Do not invent API monetary cost for the attached Kaggle model. Any estimated compute cost must state assumptions and must not be presented as an observed charge. |
| AC-09 | Report count and proportion of verified architecture violations detected by architecture checks but missed by functional tests. Paired scenario outcomes and repository consistency. One isolated violation is not strong general support. |
| AC-10 | Evaluate strategy × blast-radius interaction with trend estimates and confidence intervals. Per-repository curves. Perfect monotonicity not required. |
| AC-11 | After first main result observed, no repository, scenario, primary metric, baseline, threshold, exclusion rule, NI margin, or statistical test may change silently. Every amendment must record ID, date, trigger, already-observed results, old rule, new rule, rationale, approval, and affected analyses. |

---

## 10. Repository Selection Criteria

A repository is eligible only if it has a runnable automated test suite or a scientifically defensible scenario-relevant subset plus a fixed regression suite. Exclude and replace only when no defensible validation configuration is possible.

Selection criteria (from paper): availability of automated tests and build instructions, identifiable architecture and module boundaries, realistic size feasible for repeated controlled runs, diversity of domains/architectures/change types, permissive licences, and reproducible historical states.

Use a tagged stable release or stable-branch commit at least 90 days old. Record the exact SHA before scenario construction.

Architectural diversity target: layered REST (Todo), modular CMS with plugin architecture (django CMS), e-commerce modular monolith (Saleor).

---

## 11. Amendment Rules

After the first main result is observed, no repository, scenario, primary metric, baseline, threshold, exclusion rule, NI margin, or statistical test may change silently. Every amendment must record:

- ID, date, trigger
- Already-observed results
- Old rule, new rule, rationale
- Approval and affected analyses
