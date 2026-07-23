# Experiment Profiles — 7 Strategy Arms

**Date:** 2026-07-23
**Status:** All 7 implemented, tested, and protocol-conformant

---

## Overview

The benchmark evaluates 7 experimental arms (strategies) for dependency-aware selective regeneration. They span baselines, ablations, hybrid approaches, and a literature reference. All implement the `ImpactStrategy` protocol defined in `src/benchmark/core/protocols.py`.

---

## Arm 1 — Monolithic (Full-Code Baseline)

| Field | Value |
|-------|-------|
| **ID** | monolithic |
| **Category** | Baseline |
| **Protocol role** | Worst-case reference — always regenerates all artifacts |
| **analyze_impact()** | Returns ALL artifacts as impacted (no selection) |
| **Complexity** | Trivial |
| **Dependencies** | None |
| **File** | `src/benchmark/strategies/monolithic.py` |
| **Tests** | Strategy conformance in `test_strategies.py` |
| **Used in profiles** | smoke, pilot (reference only), research (impact-only) |

---

## Arm 2 — Agent (Repository-Retrieval Baseline)

| Field | Value |
|-------|-------|
| **ID** | agent |
| **Category** | Baseline |
| **Protocol role** | State-of-practice comparison — repository-retrieval agent workflow |
| **analyze_impact()** | Uses LLM to identify impacted artifacts based on requirement change |
| **Complexity** | High (LLM-dependent) |
| **Dependencies** | LLMBackend |
| **File** | `src/benchmark/strategies/agent.py` |
| **Tests** | Strategy conformance, mock LLM responses |
| **Used in profiles** | smoke, pilot, research |

---

## Arm 3 — Selective (Hybrid Dependency-Aware)

| Field | Value |
|-------|-------|
| **ID** | selective |
| **Category** | Primary treatment |
| **Protocol role** | Core experimental arm — hybrid graph + LLM impact analysis |
| **analyze_impact()** | Combines static dependency graph with LLM-based semantic filtering |
| **Complexity** | High (graph + LLM) |
| **Dependencies** | LLMBackend, DependencyGraphModel, ImpactPropagator, ScopeReducer |
| **File** | `src/benchmark/strategies/selective.py` |
| **Tests** | Strategy conformance, graph integration |
| **Used in profiles** | smoke, pilot, research |

---

## Arm 4 — Compiled AI (Static Analysis Only)

| Field | Value |
|-------|-------|
| **ID** | compiled_ai |
| **Category** | Ablation — no semantic understanding |
| **Protocol role** | Isolates graph-only contribution (ablation of LLM component from selective) |
| **analyze_impact()** | Pure static dependency propagation; no LLM |
| **Complexity** | Medium (graph only) |
| **Dependencies** | DependencyGraphModel, ImpactPropagator |
| **File** | `src/benchmark/strategies/compiled_ai.py` |
| **Tests** | Strategy conformance, graph propagation |
| **Used in profiles** | smoke, research |

---

## Arm 5 — Delta MCP (Semantic-Only)

| Field | Value |
|-------|-------|
| **ID** | delta_mcp |
| **Category** | Ablation — no graph analysis |
| **Protocol role** | Isolates LLM-only contribution (ablation of graph from selective) |
| **analyze_impact()** | Pure LLM-based impact assessment; no dependency graph |
| **Complexity** | Medium (LLM only) |
| **Dependencies** | LLMBackend |
| **File** | `src/benchmark/strategies/delta_mcp.py` |
| **Tests** | Strategy conformance, LLM response parsing |
| **Used in profiles** | smoke, research |

---

## Arm 6 — Incr RTL (Traceability-Only)

| Field | Value |
|-------|-------|
| **ID** | incr_rtl |
| **Category** | Ablation — traceability links only |
| **Protocol role** | Isolates traceability contribution; no graph or LLM |
| **analyze_impact()** | Follows pre-defined traceability links |
| **Complexity** | Low (traceability lookup) |
| **Dependencies** | None (traceability data from ground truth) |
| **File** | `src/benchmark/strategies/incr_rtl.py` |
| **Tests** | Strategy conformance, traceability mapping |
| **Used in profiles** | smoke, research (impact-only) |

---

## Arm 7 — Code Plan (Retrieval-Only)

| Field | Value |
|-------|-------|
| **ID** | code_plan |
| **Category** | Literature reference |
| **Protocol role** | Replicates code-plan approach from literature |
| **analyze_impact()** | Uses retrieval-based planning; no graph, no fine-grained LLM analysis |
| **Complexity** | Medium (retrieval + planning) |
| **Dependencies** | LLMBackend |
| **File** | `src/benchmark/strategies/code_plan.py` |
| **Tests** | Strategy conformance, planning output validation |
| **Used in profiles** | smoke, research (impact-only) |

---

## Strategy Registry

All strategies are registered via `StrategyRegistry` in `src/benchmark/strategies/registry.py`:

```python
registry = StrategyRegistry()
registry.register("monolithic", MonolithicStrategy)
registry.register("agent", AgentStrategy)
registry.register("selective", SelectiveStrategy)
registry.register("compiled_ai", CompiledAIStrategy)
registry.register("delta_mcp", DeltaMCPStrategy)
registry.register("incr_rtl", IncrRTLStrategy)
registry.register("code_plan", CodePlanStrategy)
registry.freeze()  # Prevents further modification
```

---

## Impact-Only Strategies

Per the execution profile design, some strategies (monolithic, incr_rtl, code_plan) are classified as impact-only — they analyze impact but do not perform full regeneration. They are used only for H1 (impact accuracy) comparison, not for H2/H3 (preservation quality, architecture preservation).

---

## Profile-Strategy Mapping

| Profile | Strategies | Rationale |
|---------|-----------|-----------|
| smoke | All 7 | Validate all arms execute without error |
| pilot | agent, selective | Focus on primary comparison (baseline vs. treatment) |
| research | agent, selective, compiled_ai, delta_mcp | Full factorial: baseline + treatment + both ablations |
