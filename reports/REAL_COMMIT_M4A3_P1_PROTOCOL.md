# M4A-3 / P1 — Real-Commit FULL-v2 vs SPARSE-v2 Evaluation Protocol (FROZEN)

**Date:** 2026-09-14
**Branch:** `main` (M4A-2 merged; this protocol is a pre-registration)
**Study ID:** `real-commit-p1-full-v2-vs-sparse-v2-01`
**Status:** FROZEN BEFORE ANY MODEL RESULT — this milestone is ZERO scientific
LLM/API calls. Real held-out inference is a separate later step under this
frozen protocol.

---

## 1. Research question

Does the controlled sparse-representation cost advantage (M1: FULL-v2 vs
SPARSE-v2) survive on **independent real historical changes**?

## 2. Scientific boundary (unchanged)

- Independent task = **historical change** (one HELD_OUT_TEST case). Repeated
  model calls are **nested observations**, never independent tasks.
- Inference repository state = **parent commit only**.
- Candidate universe + dependency graph = **parent commit only**
  (`public/candidate_universe.json`, `public/dependency_graph.json`).
- Visible intent = normalized commit message (`public/intent.json`).
- Hidden evaluation proxy = **observed-change-set proxy**
  (`hidden/observed_change_set_proxy.json`) — evaluation-only, NEVER exposed to
  any prompt, never used during inference.
- The proxy is an **OBSERVED CHANGE-SET PROXY**, never semantic ground truth.

## 3. Arms (frozen)

| Arm | Serialization policy |
|---|---|
| `full_v2` | Emit EXACTLY ONE decision per candidate id (1..N), including explicit `PRESERVE` rows. |
| `sparse_v2` | Emit ONLY non-`PRESERVE` decisions; omitted ids decode deterministically to `PRESERVE`. |

Both arms use the SAME semantic contract (action vocab, reason codes, evidence
schema, prompt skeleton). The ONLY intended treatment difference is the
serialization-policy block, proven by the deterministic prompt-control proof.

## 4. Model / provider freeze (before any result)

- Model: `qwen/qwen3-coder` (Qwen3-Coder-480B-A35B-Instruct)
- Provider: DeepInfra pinned through OpenRouter (`deepinfra/turbo`), fallback OFF
- Temperature `0.0`, completion cap `4096`, Graph OFF (no graph hint injection)
- Same model/provider/budget for BOTH arms.

## 5. Run allocation

- `N_heldout = 10` (frozen split `HELD_OUT_TEST`)
- `2` arms × `3` nested repetitions per held-out task
- Total planned cells = `10 × 2 × 3 = 60`
- No result-dependent reruns; cells are not added after results exist.

## 6. Metrics

Primary (per task, then aggregate over tasks only):
- validity / truncation (fail-closed decode rate per arm)
- Precision, Recall, F1, FNR over the predicted `REGENERATE` file set vs the
  hidden observed-change proxy.

Efficiency (nested observations aggregated to task level):
- completion tokens, total tokens, serialized records, model calls, cost, latency.

Analysis:
- aggregate only after task-level results exist;
- paired task-level differences (FULL-v2 vs SPARSE-v2 on the SAME tasks);
- bootstrap over **tasks**, not repetitions.

## 7. Failure taxonomy (frozen)

- `malformed_json`, `schema_invalid`, `decode_failed`, `truncation`,
  `transport_failure`, `budget_exceeded`. Each cell is classified fail-closed;
  failed cells are reported, never silently dropped.

## 8. Claim discipline

- "Real changed files" = **OBSERVED CHANGE-SET PROXY**, not perfect semantic
  ground truth.
- No P/R/V/H semantic gold is fabricated from diffs.
- Do NOT compare these results with any published LocAgent `Acc@K` number.

## 9. Zero-API gates in THIS milestone

1. Dataset Validation (frozen HELD_OUT_TEST membership, public/hidden
   separation, per-case bundle + map hashes)
2. Prompt Validation (prompt-control proof per case; no proxy in prompts)
3. Pipeline Smoke Test (deterministic fixture payloads decode for both arms)
4. Dry Run (frozen 60-cell manifest shape, zero calls/tokens)
5. Integration Test (fixture → decode → metrics → proxy)
6. Metric Verification (independent metric recomputation + fail-closed cases)

Independent audit reads persisted artifacts only.

## 10. Stop boundary

Real held-out model inference is **NOT** executed in this milestone. This
protocol is frozen BEFORE any result; the next step (a real P1 launch) requires
a real model/provider with its own frozen budget and evidence — never a
scientific call from this local milestone.