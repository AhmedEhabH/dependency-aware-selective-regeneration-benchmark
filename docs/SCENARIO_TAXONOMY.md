# Scenario Taxonomy — v1.0 (FROZEN)

**Part of:** Research Protocol v1.0
**Approval Date:** 2026-07-22

---

## 1. Distribution

Per repository: **8 scenarios** = 3 localized, 3 moderate, 2 cross-cutting.
Total confirmatory target: **24 scenarios** (3 repositories × 8).

## 2. Change Types (from paper)

1. Schema and field changes
2. API additions or modifications
3. Validation and business-rule changes
4. Permissions and authorization changes
5. Cross-entity relationships
6. Workflow changes
7. Architecture-sensitive changes
8. Selected broad changes to test the limits of selectivity

## 3. Blast Radius Classification

| Category | Definition | Expected artifacts affected | Count per repo |
|----------|-----------|---------------------------|----------------|
| Localized | Single module, few files | 1–5 | 3 |
| Moderate | Crosses module boundaries but contained | 5–15 | 3 |
| Cross-cutting | Spans multiple layers/modules | 15+ | 2 |

## 4. Scenario Schema

```yaml
scenario_id: STR          # e.g., "todo-local-001"
repository: STR           # todo | djangocms | saleor
change_type: STR          # from §2
blast_radius: STR         # localized | moderate | cross_cutting
requirement_before: STR
requirement_after: STR
rationale: STR
acceptance_criteria: [STR]
expected_affected_artifacts: [artifact_id]
expected_actions: {artifact_id: action}
regression_obligations: [test_id or artifact_id]
architecture_constraints: [STR]
```

## 5. Naming Convention

```
{repo}-{blast}-{NN}
```

- `repo`: todo | djangocms | saleor
- `blast`: loc | mod | cross
- `NN`: sequential 01–08

Examples: `todo-loc-001`, `djangocms-mod-004`, `saleor-cross-008`

## 6. Repository Versions (per DA-03)

Use a tagged stable release or stable-branch commit at least 90 days old, with reproducible dependencies and a functioning test setup. Record the exact SHA before scenario construction.

## 7. Replacement Policy (per DA-07)

Replacement allowed before main execution only for: infeasibility, duplication, ambiguity, licensing, or infrastructure reasons. Must preserve repository, change type, and blast-radius class where possible.

**Forbidden:** No scenario may be replaced after seeing poor model or strategy performance. If no valid replacement exists, retain the record and report reduced N.

## 8. Hidden Tests and Held-Out Scenarios (per AC-03)

**Hidden tests (mandatory):** For every scenario, hidden changed-requirement and regression tests must remain inaccessible to strategies and used only for final scoring.

**Held-out scenarios (optional):** Where feasible, reserve two scenarios per repository for final held-out validation. Scenario holding out may be omitted if all eight are needed, but hidden tests remain mandatory. Cross-validation is not a substitute.
