# ImpactPlan Completion-Cap Ablation Proposal (DOCUMENTATION ONLY — NOT RUN)

**Status:** POST-HOC EXPLORATORY ABLATION PROPOSAL · **NOT PART OF THE PREREGISTERED 60-RUN PRIMARY STUDY** · **NOT EXECUTED**.

**Proposed identifier:** `scientific-stagec-djangocms-impactplan-cap-ablation-01`

## 1. Purpose

Separate two confounded factors observed in the primary study:

- **A.** ImpactPlan selection quality (the model's ability to choose the correct write set), from
- **B.** single-response output-cap truncation (whether the frozen 4096 completion-token cap prematurely cuts the structured plan).

The primary study recorded 19/30 ImpactPlan cells truncated at exactly 4096 completion tokens (`finish_reason=length`), while the minimal schema-valid 144-path serialization alone measures ~17,364 bytes / ~4.3k heuristic-estimated tokens. This ablation would test whether raising the cap to 8192 materially changes operational completion and selection quality.

## 2. Proposed design (identical frozen inputs)

- Same frozen djangoCMS source (pin `0f633fc9…`)
- Same six visible scenarios (`djangocms-external-validity-002/004/005/006/007/008`)
- Same hidden gold (`djangocms_hidden_gold_draft.json`, evaluation-only)
- Same 144-file candidate universe
- Same model `qwen/qwen3-coder`, same DeepInfra-pinned-through-OpenRouter provider, same temperature 0
- **ImpactPlan only** (no Agent rerun required for this specific cap ablation)
- **Completion cap: 8192** (only change)
- 5 repetitions × 6 scenarios = **30 runs**

## 3. Explicit non-claims

- This proposal is **not** a preregistered primary-study component and must not be retroactively presented as one.
- It is **not** run in this closure task (ZERO new scientific API calls authorized).
- Nothing in this proposal constitutes advance confirmation of any outcome.

## 4. Cost estimate (from existing raw evidence only, zero calls)

- Primary-study all-cell ImpactPlan recorded cost: $0.123298 across 30 cells (mean 0.004110/cell).
- A 30-run cap-8192 ablation at the same observed per-cell cost profile would project to roughly the same magnitude as the primary ImpactPlan arm (≈ $0.12–$0.15). This is a planning estimate from raw evidence, not a quote.

## 5. Decision gate

Execute ONLY after GPT-5.6 SOL independently audits the primary 60-run evidence and explicitly authorizes the ablation. Do not run during this closure.
