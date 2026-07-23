# Kaggle Smoke Pass — Phase 4F.X

**Date:** 2026-07-23  
**Status:** COMPLETE  
**Tag:** `v0.7.0-smoke-passed` at commit `0c58250`  
**Evidence:** Non-publication (engineering validation only)

---

## Summary

Kaggle real smoke executed successfully — twice. All 7 strategy arms completed with real Qwen2.5-Coder-7B-Instruct inference confirmed (325 prompt + 19 completion tokens). Smoke evidence is non-publication: intended to validate deployment, not produce publishable results.

---

## What Was Fixed (This Session)

### Fix 1 — Real Qwen Failure Propagation (branch `fix/real-qwen-failure-propagation`)
- **Root cause:** `agent.py` had a blanket `except Exception` that swallowed real Qwen errors; token_usage field was missing from `RunRecord` and `KaggleQwenBackend`; smoke strategies were not tagged `stage=smoke` causing full-pilot execution; runner did not preserve prediction-errors for failed strategies.
- **Files changed:** `models.py` (token_usage fields, stage), `agent.py` (no blanket except), `runner.py` (prediction errors → failed), `repair.py` (preserve failures), `kaggle_qwen_backend.py` (lifecycle logging, GPU preflight).
- **Outcome:** Failures propagated correctly; Kaggle smoke passed.

### Fix 2 — Graph Wiring for Graph-Dependent Strategies (branch `fix/kaggle-graph-strategy-wiring`)
- **Root cause:** Graph-dependent strategies (selective, compiled_ai) received `None` graph because ProfileGraphBuilder was not wired; `STRATEGY_CAPABILITIES_DESIGN` was not used; `describe_capabilities()` returned `{}`.
- **Files changed:** `graph/builder.py` (ProfileGraphBuilder), `pipeline.py` (nullable backend → NullLLMBackend), `runner.py` (nullable backend type), `mock_backend.py` (NullLLMBackend), strategies (agent, compiled_ai, selective, code_plan accept graph), `seven_arm_benchmark.py` (capabilities design, build_dependency_graph, backend only for LLM-dependent strategies).
- **Outcome:** 7/7 arms succeeded; Qwen inference confirmed.

---

## Quality Gates

| Gate | Result |
|------|--------|
| Ruff | 0 violations |
| Mypy strict | 0 errors (src) |
| Pytest | 504/505 passed (1 skipped: torch import) |
| pip check | Clean (pre-existing conda issues only) |

---

## Evidence

- **Kaggle real smoke passed:** 2 runs, 7/7 arms, real Qwen2.5-Coder inference
- **Smoke evidence:** Non-publication (engineering validation before pilot/research)
- **Tag:** `v0.7.0-smoke-passed` at `0c58250`

---

## Next Task

Implement Kaggle checkpoint/resume support for long-running profiles (pilot: ~2-3h, research: ~6-9h).