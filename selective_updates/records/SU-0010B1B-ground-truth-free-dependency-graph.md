# SU-0010B1B — Ground-Truth-Free Dependency Graph

**Date:** 2026-07-26
**Branch:** `fix/su-0010b1b-ground-truth-free-graph`
**Commit:** (to be inserted after merge)

## Requirement

Remove all use of `scenario.expected_affected_artifacts` from dependency-graph
construction used during prediction. Ground Truth must only enter the execution
path during evaluation, never during graph construction.

## Previous Ground Truth Leakage Path

`seven_arm_benchmark.py:build_dependency_graph()` (lines 266-322):

```
for s in scenarios:
    for a in s.expected_affected_artifacts:   ← Ground Truth
        artifacts.add(a.path)                  ← Ground Truth paths collected

if not artifacts:
    return None
minimal = DependencyGraph(
    nodes=tuple(sorted(artifacts)),            ← Ground Truth enters graph
    edges=(),
    metadata={"source": "artifact_fallback"},
)
```

This leaked Ground Truth artifact paths into the `DependencyGraph` that was
subsequently passed to `strategy.analyze_impact()` for `selective`,
`compiled_ai`, and `code_plan` strategies.

## New Dependency Graph Construction Path

```
active_snapshot_root
    ↓
repository profile graph if available (profile with edges)
    OR
profile architecture node fallback (edgeless, from profile layers/boundaries/graph)
    OR
neutral repository-derived edgeless fallback (zero nodes, zero edges, no GT)
    ↓
DependencyGraph
    ↓
strategy.analyze_impact()
```

Ground Truth (`expected_affected_artifacts`, `expected_actions`) never enters
this path.

## Exact Files Changed

| File | Change |
|------|--------|
| `src/benchmark/graph/builder.py` | Added `_extract_architecture_paths()` and `build_nodes_from_architecture()` methods to `ProfileGraphBuilder` |
| `seven_arm_benchmark.py` | Rewrote `build_dependency_graph()` to remove Ground Truth fallback; added architecture node extraction fallback; always returns a `DependencyGraph` |
| `tests/unit/graph/test_graph.py` | Added 19 unit tests covering architecture extraction, neutral fallback, leakage regression (10 critical tests) |

## Exact Tests Added/Modified

All in `tests/unit/graph/test_graph.py`:

**ProfileGraphBuilder tests (10):**
- `test_extract_architecture_paths_from_layer_list`
- `test_extract_architecture_paths_from_layer_dict`
- `test_extract_architecture_paths_from_dependency_graph`
- `test_extract_architecture_paths_from_boundaries`
- `test_extract_architecture_paths_skips_annotations`
- `test_extract_architecture_paths_empty_returns_empty`
- `test_build_nodes_from_architecture_returns_edgeless_graph`
- `test_build_nodes_from_architecture_none_when_no_paths`
- `test_build_nodes_from_architecture_deterministic`
- `test_build_nodes_from_architecture_no_fabricated_edges`

**Critical Leakage-Regression tests (9):**
- `test_graph_contains_repo_artifacts_not_ground_truth`
- `test_real_profile_graph_remains_preferred`
- `test_neutral_fallback_is_edgeless_and_deterministic`
- `test_neutral_fallback_has_zero_fabricated_edges`
- `test_empty_repository_returns_empty_graph`
- `test_repeated_construction_produces_equal_graph`
- `test_expected_actions_do_not_alter_graph`
- `test_ground_truth_only_paths_never_become_nodes`
- `test_graph_construction_does_not_mutate_artifact_universe`

## Limitations

1. **Real dependency inference when profile graph is absent: not implemented.**
   The neutral fallback is intentionally edgeless and conservative.
   Real dependency edges require a profile with a declared dependency graph.
2. **Architecture node extraction is heuristic.** Paths are extracted from
   profile architecture data (layers, module_boundaries, dependency_graph).
   Quality depends on profile completeness. Saleor layers use dict format
   with directory-level paths; djangocms has no layers.
3. **No Python AST import analysis.** Existing `PythonImportExtractor` exists
   but is not integrated into the graph construction pipeline. Integration
   would require access to repository source files at graph-build time.

## Scientific Interpretation

The `build_dependency_graph()` function now guarantees Ground-Truth-free graph
construction. When a real profile dependency graph exists, it is used with full
node and edge data. When absent, the fallback produces an edgeless graph with
either architecture-derived nodes (from profile) or zero nodes. This may reduce
signal quality for graph-consuming strategies (`selective`, `compiled_ai`,
`code_plan`) on repositories without declared dependency edges, but no
fabricated or Ground Truth data enters the prediction boundary.

## Status

- Candidate ArtifactUniverse Ground Truth leakage: **removed** (previously
  fixed in SU-0010B1)
- DependencyGraph Ground Truth leakage: **removed** (this task)
- Prediction input boundary: **Ground-Truth-free**
- Real dependency inference when profile graph is absent: **not implemented**
- Neutral fallback: **edgeless and conservative**

## Code/Data/Notebook Update Status

- Code Dataset: **updated** (3 production files + 1 test file changed)
- Data Dataset: **unchanged** (no benchmark_data changes)
- Notebook: **unchanged**
