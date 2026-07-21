# Phase 3.5 — Static Architecture Audit and Project Map: Completion Report

**Date:** 2026-07-22
**Protocol Version:** 1.0 (FROZEN)
**Status:** COMPLETE
**Approved for Phase 4A:** true

## Summary

Phase 3.5 (Static Architecture Audit and Project Map) is complete. The full repository layout was inspected, revealing a critical duplicate directory structure (root-level `docs/` and `benchmark_data/` outside the Git repo). The canonical project root was identified as `project/`. A 13-layer software architecture was defined with 11 interface protocols, strict dependency rules, and a Phase 4 implementation blueprint split into 6 milestones (4A–4F). Eight new architecture documents and two reports were created.

## Structural Issues Found

| Issue | Severity | Detail |
|-------|----------|--------|
| Duplicate `docs/` | CRITICAL | 4 stale files outside Git; 16 authoritative files inside Git |
| Duplicate `benchmark_data/` | HIGH | Partial stale duplicate outside Git; full set inside Git |
| Stale decision files | MEDIUM | `FINAL_RESEARCH_PROTOCOL_DECISIONS.md` and `HUMAN_DECISIONS_REQUIRED.md` superseded |
| Scenario blast_radius inconsistency | LOW | 2 YAML files use non-standard values |
| Missing pyproject.toml | LOW | Proposed for Phase 4 |
| Missing .gitignore entries | LOW | `__pycache__/` and `runs/` not in .gitignore |

## Tasks Completed

| ID | Description | Status |
|----|-------------|--------|
| T350 | Inspect Repository Layout and Identify Conflicts | COMPLETE |
| T351 | Define Canonical Project Root and Path Policy | COMPLETE |
| T352 | Create Project Structure Map | COMPLETE |
| T353 | Define Software Architecture and Interfaces | COMPLETE |
| T354 | Define Dependency Rules | COMPLETE |
| T355 | Create Extension Guide | COMPLETE |
| T356 | Define Public/Private Data Boundary | COMPLETE |
| T357 | Create Phase 4 Implementation Blueprint | COMPLETE |
| T358 | Create Architecture Validation Plan | COMPLETE |
| T359 | Create Architecture Audit Reports | COMPLETE |
| T360 | Update State Files for Phase 3.5 | COMPLETE |

## Files Created (Phase 3.5)

### docs/ (8 files)
- `docs/PROJECT_ROOT_AND_PATH_POLICY.md` — Canonical root, directory classification, remediation
- `docs/PROJECT_STRUCTURE_MAP.md` — Complete proposed tree, directory responsibility tables
- `docs/SOFTWARE_ARCHITECTURE.md` — 13 layers, 11 interface specs, model backend separation
- `docs/DEPENDENCY_RULES.md` — Allowed/prohibited imports, 10 prohibited patterns
- `docs/EXTENSION_GUIDE.md` — Plugin lifecycle, registry design, protocol skeletons
- `docs/PUBLIC_PRIVATE_DATA_BOUNDARY.md` — Data classification, import isolation, audit checklist
- `docs/PHASE4_IMPLEMENTATION_BLUEPRINT.md` — 6 milestones with files, tests, acceptance criteria
- `docs/ARCHITECTURE_VALIDATION_PLAN.md` — 11 validation checks

### reports/ (2 files)
- `reports/PHASE3_5_ARCHITECTURE_AUDIT.md` — Full audit with architecture decisions, risks, validation
- `reports/PROJECT_STRUCTURE_CONFLICT_REPORT.md` — Documented conflicts with remediation plan

## Architecture Decisions

| AD | Decision |
|----|----------|
| AD-01 | Protocol over ABC (typing.Protocol for interfaces) |
| AD-02 | Instantiated registries (no global singletons) |
| AD-03 | Dependency injection (constructor-based) |
| AD-04 | Lazy Kaggle imports (torch/transformers only in methods) |
| AD-05 | Core isolation (Core imports nothing from infrastructure) |
| AD-06 | Immutable run records (frozen dataclasses) |
| AD-07 | Pydantic for configuration models |
| AD-08 | Atomic file writes |
| AD-09 | No hidden test imports in strategies/execution |
| AD-10 | No repo-specific branches in generic execution |

## Phase 4 Milestones

| Milestone | Focus | Complexity |
|-----------|-------|------------|
| 4A | Domain Models + Contracts (core + config) | Medium |
| 4B | Loaders + Validation (repositories + scenarios) | Medium |
| 4C | Model Backends (mock, dry-run, Kaggle skeleton) | Medium |
| 4D | Execution Core (pipeline, repair, budgets) | High |
| 4E | Provenance + Result Storage | Low |
| 4F | Architecture + Contract Tests | Medium |

## Files Modified
- `SYSTEM_STATE.md` (Phase 3.5 complete)
- `TODO.md` (added Phase 3.5 tasks T350–T360)
- `DECISION_LOG.md` (added D009)
- `reports/latest_phase_report.md` (this file)

## Exact Next Task
**Phase 4A — Domain Models and Contracts**: Implement immutable data models in `src/benchmark/core/` (enums, models, exceptions, protocols, registry, context) and configuration models in `src/benchmark/config/` (models, loader, validation). No strategy or execution code.
