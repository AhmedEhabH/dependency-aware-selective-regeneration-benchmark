# Phase 4E — Impact Strategies Report

**Date:** 2026-07-22
**Protocol Version:** 1.0 (FROZEN)
**Status:** COMPLETE

## Summary

Phase 4E implements the 7 impact strategy patterns, dependency graph construction and traversal, artifact selection and regeneration planning. All strategies conform to the frozen `ImpactStrategy` protocol. Quality gates pass: 332/332 tests, 0 ruff violations, 0 mypy errors.

## Production Files Created

### `src/benchmark/strategies/` (9 files)
| File | Class | Purpose |
|------|-------|---------|
| `__init__.py` | — | Package exports |
| `registry.py` | `StrategyRegistry` | Register/create/freeze strategies |
| `monolithic.py` | `MonolithicRegenerationStrategy` | Baseline: regenerate all artifacts |
| `agent.py` | `RepositoryAgentStrategy` | LLM-powered analysis |
| `compiled_ai.py` | `StaticOnlyStrategy` | Static dependency graph only |
| `delta_mcp.py` | `SemanticOnlyStrategy` | Semantic similarity only |
| `incr_rtl.py` | `TraceabilityOnlyStrategy` | Test coverage traceability only |
| `selective.py` | `HybridSelectiveStrategy` | Graph + semantic + traceability |
| `code_plan.py` | `FullContextStrategy` | All signals combined |

### `src/benchmark/graph/` (3 files)
| File | Classes | Purpose |
|------|---------|---------|
| `__init__.py` | — | Package exports |
| `models.py` | `DependencyNode`, `DependencyEdge`, `DependencyGraphModel` | Graph data structures |
| `builder.py` | `PythonImportExtractor`, `ImpactPropagator`, `ScopeReducer` | Graph construction and traversal |

### `src/benchmark/selection/` (2 files)
| File | Classes | Purpose |
|------|---------|---------|
| `__init__.py` | — | Package exports |
| `planner.py` | `ArtifactSelector`, `RegenerationPlanner` | Artifact selection and ordering |

## Test Files Created (3 files, 43 tests)

| File | Tests |
|------|-------|
| `tests/unit/strategies/test_strategies.py` | 21 (7 strategies + 8 registry + 3 protocol + 3 edge cases) |
| `tests/unit/graph/test_graph.py` | 16 (models + extractors + propagator + reducer) |
| `tests/unit/selection/test_planner.py` | 6 (selector + planner) |

## Quality Gates

| Gate | Result |
|------|--------|
| pytest | **332/332 passed** (2.53s) |
| ruff | **0 violations** |
| mypy --strict | **0 errors** (93 files) |
| pip check | **Clean** |

## Design Decisions

1. **Dependency injection throughout** — strategies accept injectable components (graph, coverage map, LLM backend) rather than constructing them internally
2. **No global singletons** — `StrategyRegistry` is instantiated and injected
3. **Protocol conformance** — all strategies implement `ImpactStrategy` protocol structurally
4. **ARG002 suppressed for strategy files** — protocol-mandated parameters are not always used by every strategy
5. **Graph models are separate from core** — `graph/models.py` extends (does not modify) the minimal `DependencyGraph` in core
