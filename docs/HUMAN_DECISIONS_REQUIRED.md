# Human Decisions Required

## Status
**NONE** — All Phase 0 decisions fall within standard engineering scope.

## Notes

The following decisions are PREAPPROVED_BY_RESEARCHER (see Section 2 of OPENCODE_EXECUTION_GUIDE.md):
- Language: Python
- Framework ecosystem: Django
- Local environment: Conda
- Local model download: forbidden
- Local LLM inference: forbidden
- Remote platform: Kaggle
- Kaggle model: qwen-lm/qwen2.5-coder
- Repository set: Controlled Django Todo, django CMS, Saleor Core, ERPNext (optional)
- Scenario distribution per repo: 3 localized, 3 moderate, 2 cross-cutting
- Core strategies: repository_agent, static_only, semantic_only, hybrid_selective
- Additional strategy: traceability_only
- Full context: only when feasible
- Legacy results classification: legacy_pilot

A human decision will be requested only if:
1. A decision changes an RQ or hypothesis
2. A decision changes the approved repository set
3. A decision changes primary metrics
4. A decision changes baseline fairness
5. A decision changes scenario exclusion rules
6. A decision changes the statistical protocol
7. A license prevents intended use
8. Local installation could damage the user's system outside the isolated environment
9. Required source material is missing
10. Two approved requirements directly conflict
