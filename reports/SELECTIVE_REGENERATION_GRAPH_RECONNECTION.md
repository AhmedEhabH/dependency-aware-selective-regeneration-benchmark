# Selective Regeneration + Dependency Graph — Reconnection

**Date:** 2026-09-11
**Purpose:** explain the research architecture and how graph evidence could
become the next controlled step toward the broader Selective Regeneration idea
— without pretending that downstream regeneration has already been evaluated.

---

## 1. Research architecture

```
Requirement change
        ↓
Impact selection
        ↓
Sparse impact policy / Preserve-by-Omission
        ↓
Dependency evidence / graph-assisted scope reasoning
        ↓
Selective regeneration
        ↓
Preservation verification
```

## 2. What the completed studies evaluate

The completed djangoCMS studies evaluate the **IMPACT SELECTION** layer:

- which repository paths a model predicts must change given a requirement
  change, and
- the inference efficiency of that selection (sparse serialization via
  ImpactPlan-v2 / Preserve-by-Omission).

They are **selection-only** and do **NOT** evaluate downstream code
regeneration correctness (no functional-correctness, preservation,
architecture-compliance, or end-to-end regeneration measurement). The
repositories were **not** modified; only selection policies were predicted and
scored against source-adjudicated hidden gold applied after inference.

The completed studies therefore establish **selection fidelity of a sparse
impact-plan representation** on six djangoCMS requirement changes — not that
selectively regenerating the predicted files preserves behavior.

## 3. Where dependency-graph evidence fits

The graph-assisted step is a **scope-reasoning aid inside the impact-selection
layer**: when the model predicts an impact set, dependency edges are provided
as **SOFT EVIDENCE** so the model can reason about which files a change to a
given file might propagate to. It does not replace the selection scorer, the
sparse representation, or the gold evaluation.

A controlled next step would be a **POST-HOC EXPLORATORY GRAPH-EVIDENCE
ABLATION** (see `reports/GRAPH_ONE_DAY_EXPERIMENT_PROTOCOL.md`): the same six
djangoCMS scenarios, the same model
(Qwen3-Coder-480B-A35B-Instruct, OpenRouter slug `qwen/qwen3-coder`, DeepInfra),
the same ImpactPlan-v2 / Preserve-by-Omission arm, with the **only** change
being the addition of the complete frozen dependency-graph block to the prompt
(Graph-OFF historical baseline already exists: 30 cells).

## 4. What a graph ablation would and would not establish

- Would establish: descriptive evidence on whether adding the automatic
  dependency graph to the prompt changes selection behavior (validity,
  truncation, TP/FP/FN changes, full recall, per-scenario).
- Would NOT establish: that selective regeneration is end-to-end correct, that
  graph evidence "improves recall" in a causal sense, or any statistical
  equivalence/superiority claim. It is exploratory, single-factor, and on the
  same six author-curated cases.

## 5. Honest position

Downstream **selective regeneration correctness remains unevaluated**. The
graph ablation is a step toward the broader idea, but reaching
"Selective Regeneration works" requires additional controlled evaluation
(e.g., a real historical-commit benchmark for requirement/gold independence —
see `reports/REAL_COMMIT_BENCHMARK_PLAN.md` — and, eventually, regeneration +
preservation verification). This document does not claim that downstream
regeneration has been evaluated.