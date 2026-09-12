# NEXT GRAPH EXPERIMENT PROTOCOL DRAFT (M3) — DO NOT EXECUTE

**Status:** DRAFT — prepared for the next scientific sprint. **No Graph
scientific calls are executed in this task.**

## Study design

The NEXT experiment compares:

- **C0:** Sparse-v2, Graph OFF
- **C1:** Sparse-v2, Graph Hints

The **ONLY intended treatment difference** is the **GRAPH_EVIDENCE block** in
the prompt.

## Frozen-unchanged inputs (reuse the audited M1B Sparse-v2 contract)

- M1 Sparse-v2 encoding
- common JSON schema
- model: Qwen3-Coder-480B-A35B-Instruct (`qwen/qwen3-coder`)
- provider: DeepInfra through OpenRouter (`deepinfra/turbo`)
- temperature: 0
- completion cap: 16384 (as in M1B)
- candidate universe: frozen 144-path djangoCMS 5.0.0 universe
- scenario text: the six curated development/mechanism scenarios
  (002, 004, 005, 006, 007, 008)
- scorer: hidden-gold evaluation-only after inference

## Graph source

The automatically generated frozen djangoCMS graph:

- 144 nodes
- 562 edges
- 144/144 AST parsed
- no manual scenario edges
- no gold-derived edges
- hash parity PASS (the automatic-build graph is hash-reproducible)

## Graph is SOFT EVIDENCE ONLY

The Graph_Hints treatment must NOT:

- prune candidates
- force neighbour selection
- change candidate universe
- change schema
- change encoding

## Why Graph-Pruned (C2) is deferred

Graph-Pruned (a hard candidate-pruning arm) is deferred because hard pruning
introduces a **second intervention** and directly changes the
recall/efficiency trade-off — it cannot be cleanly attributed to the graph
evidence alone. C0-vs-C1 (Graph OFF vs Graph Hints) isolates exactly one
intervention (the GRAPH_EVIDENCE block).

## Primary future Graph metrics

- FN
- Recall
- FP
- Precision
- F1
- full recall

## Secondary future Graph metrics

- input tokens
- output tokens
- total tokens
- latency
- cost

## Classification

POST-HOC EXPLORATORY DEVELOPMENT-SET GRAPH ABLATION.

The six scenarios remain a **CURATED DEVELOPMENT / MECHANISM SET** — NOT an
unbiased held-out evaluation set. Do not claim confirmatory Graph evidence.

## Do NOT execute

This is a draft only. No Graph scientific calls are made in the current task.
