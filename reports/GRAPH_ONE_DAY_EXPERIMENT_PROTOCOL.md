# One-Day Dependency-Graph Experiment — Readiness Protocol and Feasibility

**Date:** 2026-09-11
**Scope:** reconnect the completed work to the broader original research
direction — **Selective Regeneration + Dependency Graph** — with a precise,
executable ONE-DAY experiment protocol.
**Executed in this task:** graph audit and feasibility ONLY. **NO graph
scientific cells were executed** (zero graph API calls in this task).

---

## D1 — Audit of the existing automatic graph

Inspected `src/benchmark/external_validity/source_graph.py` and the frozen
artifact `benchmark_data/external_validity/djangocms_5_0_0_dependency_graph.json`.

**Verification results (rebuilt locally from the pinned djangoCMS source with
ZERO LLM calls):**

| Check | Result |
|---|---|
| Graph generated automatically from pinned source code | **YES** — `graph_source = python_ast_source_extractor`; no fallback path |
| Python AST/import analysis used | **YES** — `ast.parse` import-statement resolution only |
| NO graph edge manually authored for a scenario | **YES** — edges are AST-derived; scenario files never enter the builder |
| NO hidden gold enters graph generation | **YES** — builder imports no gold/expected-actions data |
| NO expected-actions file enters graph generation | **YES** |
| Candidate universe == frozen 144-file universe | **YES** — rebuilt 144 files; canonical universe hash `43f4279b…` MATCHES |
| All 144 candidate Python files parse | **YES** — parse_success 144/144, parse_failure 0 |
| Edge count == currently expected frozen value | **YES** — 562 edges (rebuilt == frozen) |
| Graph construction deterministic | **YES** — canonical hash identical across rebuilds with different timestamps |

- Rebuilt canonical graph hash: `0a6bf0f758c9cd7de79adb72138c549a2b0aee3cfd62841496cb455d1ce7cd58`
- Frozen artifact canonical hash: `0a6bf0f758c9cd7de79adb72138c549a2b0aee3cfd62841496cb455d1ce7cd58`

**GRAPH_BUILD_AUTOMATIC: YES**
**GRAPH_GOLD_INDEPENDENT: YES**
**GRAPH_HASH_PARITY: PASS**

---

## D2 — Minimal ONE-FACTOR graph-evidence ablation (design)

**Historical Graph-OFF baseline (already exists, DO NOT rerun):**
- Model: Qwen3-Coder-480B-A35B-Instruct (OpenRouter slug `qwen/qwen3-coder`)
- Provider: DeepInfra (`deepinfra/turbo`)
- Arm: ImpactPlan-v2 / Preserve-by-Omission
- Graph: OFF
- Existing cells: 6 scenarios × 5 repetitions = **30**

**New Graph-ON cells (required later, NOT executed in this task):**
- Same 6 scenarios × 5 repetitions = **30 new cells**
- Same model, same provider, same v2 prompt EXCEPT graph-evidence addition,
  same v2 JSON schema, same candidate IDs, same temperature (0), same 4096
  cap, same scoring, same hidden gold, same failure semantics.
- **ONE factor changes: the frozen dependency-graph evidence block is added to
  the prompt.**

---

## D3 — Complete graph evidence first (preferred treatment)

Use the **COMPLETE frozen dependency graph** (562 edges). Do NOT tune graph
scope against the six scenarios. Compact numeric candidate IDs (the frozen
1..144 candidate-ID map) keep the block small.

Example conceptual encoding (direction explicit):

```json
{"dependency_edges": [[12,47],[47,91],...]}
```

- Direction: `[source_candidate_id, imported_local_candidate_id]`
- Prompt instruction (frozen): "Dependency information is SOFT EVIDENCE. An
  edge alone is NOT sufficient reason to mark a file REGENERATE. Use
  requirement intent, repository evidence, architecture information, and
  dependency structure together."

Forbidden: hand-selecting S006 neighbours, filtering edges using gold,
learning weights from these six cases, choosing thresholds from observed S006
behavior, automatically forcing graph neighbours to REGENERATE, or hard-
pruning candidate files.

---

## D4 — Classification

Label the future study: **POST-HOC EXPLORATORY GRAPH-EVIDENCE ABLATION**

Do NOT call it: confirmatory, independent graph validation, "proof that
dependency graphs improve recall", or end-to-end selective-regeneration
validation. Existing results (especially S006) helped motivate graph
evaluation, so the study is exploratory.

---

## D5 — Graph metrics

Compare historical Graph-OFF Sparse-v2 vs new Graph-ON Sparse-v2:
validity, failures, truncations, TP/FP/FN, Precision/Recall/F1/FNR,
full recall, prompt/completion/total tokens, calls, latency, cost.

**Most important graph diagnostics:** change in FALSE NEGATIVES and, separately,
change in FALSE POSITIVES (not only F1). Report every scenario independently.
S006 is reported but receives NO special tuning.

---

## D6 — Graph token overhead (measured, not estimated from edge count)

Actual serialized compact graph block for the complete 562-edge frozen graph:

| Metric | Value |
|---|---|
| Serialized block (`{"dependency_edges":[[...]]}`) | 4,781 characters / 4,781 bytes (UTF-8) |
| Approx tokens (len//4 heuristic) | **1,195** |
| Tokenizer note | exact Qwen3 provider tokenizer not locally available; len//4 is the backend heuristic. The provider-reported prompt tokens at execution would give the authoritative count. |
| Base v2 prompt tokens (measured scenario-004) | ~3,027 |
| Graph-on v2 prompt tokens | ~4,222 |
| Absolute overhead | ~1,195 tokens |
| Percentage overhead | **~39.5%** |

---

## D7 — Graph cost and time feasibility

**Live pricing (queried 2026-09-11)** for the historical route
Qwen3-Coder-480B-A35B-Instruct / OpenRouter slug `qwen/qwen3-coder` /
DeepInfra (`deepinfra/turbo`): **$0.30 / 1M input, $1.00 / 1M output**,
context 262,144, max completion 65,536.

**30 Graph-ON call projection (prompt ≈ 4,222 tokens measured; completion**
**historical v2 mean ≈ 950, worst case 4,096):**

| Estimate | Value |
|---|---|
| Expected input cost | 30 × 4,222 × $0.30/1M ≈ $0.0380 |
| Expected completion cost | 30 × 950 × $1.00/1M ≈ $0.0285 |
| **Expected total API cost** | **≈ $0.067** |
| Worst-case 4096-output cost | 30 × 4,222 × $0.30/1M + 30 × 4,096 × $1.00/1M ≈ **$0.162** |
| Estimated serial runtime | ~15–30 min (historical v2 latency ~13 s/cell, graph-on prompts ~39% larger) |
| Implementation effort | driver variant of the completed cross-model framework (~2–3 h) |
| Validation effort | six gates + audit + zero-API verifier (~2–3 h) |
| Audit effort | independent audit + export (~1–2 h) |

Targets: API cost ≤ $0.30 ✓ (≈$0.067 expected, ≈$0.162 worst case); scientific
execution ≤ 2 hours ✓; total implementation + validation + execution + audit
≤ one working day ✓.

**GRAPH_ONE_DAY_FEASIBILITY: YES**

Why: the automatic graph is verified and hash-reproducible; the complete
graph block adds only ~39% prompt overhead; 30 calls are projected to cost
≈$0.07 (worst case ≈$0.16) and run in well under an hour; the implementation
reuses the already-corrected cross-model framework. No graph scientific cells
were executed in this task.