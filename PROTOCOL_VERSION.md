# Protocol Version

## Current pre-main scientific execution amendment

- **Label:** `scientific-wip-impactplan-v1.1`
- **Frozen:** 2026-09-06, before any v1.1 model call (D051/A032)
- **Historical run:** `exp-20260905-225518` remains immutable diagnostic evidence and is excluded from the v1.1 comparison.
- **Model/provider:** `qwen/qwen3-coder` on pinned DeepInfra through OpenRouter; fallback off; NovitaAI is permitted once only for provider/API JSON-schema incompatibility.
- **Maximum completion budgets:** Agent control 1024; ImpactPlan 4096; initial PatchEnvelope 8192; repair PatchEnvelope 8192.
- **Interface contract:** provider-native JSON-schema ImpactPlan, PatchEnvelope, and Agent actions; Agent calls 1-7 explore and call 8 is forced final; `search_text` accepts one file or directory; repair/failure preserves ImpactPlan and planner provenance.
- **Scope:** Todo 3 scenarios x 2 strategies x 5 repetitions. Production Tier M/L scaling is documentation only and is not active.

**Protocol Version:** 1.0
**Status:** FROZEN
**Approval Date:** 2026-07-22
**Approved for Phase 3:** true

## Governance

This repository follows the OpenCode Execution Guide v1.0.0 as defined in `docs/OPENCODE_EXECUTION_GUIDE.md`. The research protocol is defined in `docs/FINAL_RESEARCH_PROTOCOL.md` and its companion documents:

| Document | Path |
|----------|------|
| Final Research Protocol | `docs/FINAL_RESEARCH_PROTOCOL.md` |
| Ground Truth Protocol | `docs/GROUND_TRUTH_PROTOCOL.md` |
| Scenario Taxonomy | `docs/SCENARIO_TAXONOMY.md` |
| Statistical Analysis Plan | `docs/STATISTICAL_ANALYSIS_PLAN.md` |
| Execution and Failure Policy | `docs/EXECUTION_AND_FAILURE_POLICY.md` |
| Leakage Prevention Protocol | `docs/LEAKAGE_PREVENTION_PROTOCOL.md` |
| Reproducibility Protocol | `docs/REPRODUCIBILITY_PROTOCOL.md` |
| Researcher Decisions (DA + AC) | `docs/RESEARCHER_DECISIONS_DA_AC.md` |

## Change History

| Version | Date       | Status  | Author  | Change |
|---------|------------|---------|---------|--------|
| 1.0     | 2026-07-22 | FROZEN  | Researcher | Initial protocol definition and freeze from Phase 2A draft + researcher decisions DA-01–DA-14 + mandatory corrections AC-01–AC-11 |
| 0.1     | 2026-07-22 | DRAFT   | OpenCode | Phase 2A protocol draft (superseded) |

## Amendment Rules

After the first main result is observed, no repository, scenario, primary metric, baseline, threshold, exclusion rule, NI margin, or statistical test may change silently. Every amendment must be recorded with ID, date, trigger, already-observed results, old rule, new rule, rationale, approval, and affected analyses.
