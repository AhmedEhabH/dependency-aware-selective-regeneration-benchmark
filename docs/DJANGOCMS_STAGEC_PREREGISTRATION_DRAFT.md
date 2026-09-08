# djangoCMS External-Validity Preregistration Draft
Generated: 2026-09-07T17:44:10.084238+00:00
Repository: djangocms 5.0.0
Pinned commit: 0f633fc9fa213357f4202482aab2b0edad680f95
Candidate universe: 144 files
Dependency graph: 144 nodes, 562 edges
Eligibility: True

## Validation Gates
1. Dataset Validation: PASS (commit matches)
2. Prompt Validation: PASS (6 leak-free drafts)
3. Pipeline Smoke Test: PASS (implementation works)
4. Dry Run: PASS (no scientific imports)
5. Integration Test: PASS (graph built, edges traceable)
6. Metric Verification: PASS (eligibility criteria met)

## Graph Statistics
- Nodes: 144
- Edges: 562
- Parse success: 144/144 (100.0%)
- Isolated nodes: 12
- Non-isolated nodes: 132
- Weakly connected components: 13

## Edge Traceability
- Sampled edges: 10
- False edges: 0
- All edges traceable to source imports

## Readiness
PREP PASS — READY FOR INDEPENDENT AUDIT BEFORE SCIENTIFIC RUNS

## Scenario Selection (source-adjudicated)
djangoCMS yields **6 scenarios** (1 localized, 3 moderate, 2 cross-cutting):
- 1 localized: `djangocms-loc-002` (REUSE)
- 3 moderate: `djangocms-mod-004`, `djangocms-mod-005`, `djangocms-mod-006`
- 2 cross-cutting: `djangocms-cross-007`, `djangocms-cross-008`

**Rejected:** `djangocms-loc-001` and `djangocms-loc-003` — the requested feature is
already present in pinned source v5.0.0 (`PageContent.meta_description` and
`CMSPlugin.position` already exist), so execution would be a no-op with no defensible
before/after contrast.

Selection is derived programmatically from the 8-record audit
(`historical_scenario_audit.json`): confidence in {HIGH, MEDIUM} AND decision in
{REUSE, REWRITE_VISIBLE_TEXT}, yielding exactly these six. Every hidden-gold path is
an exact member of the frozen 144-file candidate universe (pinned commit
`0f633fc9fa213357f4202482aab2b0edad680f95`) — see
`djangocms_hidden_gold_adjudication.json`.
