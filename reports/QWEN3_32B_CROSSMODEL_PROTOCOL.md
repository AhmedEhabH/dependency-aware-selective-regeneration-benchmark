# Qwen3-32B Cross-Model Robustness Replication — Protocol (Preregistered)

**Study ID:** `scientific-stagec-djangocms-qwen3-32b-crossmodel-01`

**Label:** POST-HOC CROSS-MODEL ROBUSTNESS REPLICATION

**Frozen before scientific cell 1.** This document is the preregistration. No
cell, metric, or inference policy may change after this freeze without a new
registered protocol.

---

## 1. Design

| Dimension | Value |
| --- | --- |
| Historical model | `qwen/qwen3-coder` (OpenRouter / DeepInfra) |
| New model | `qwen/qwen3-32b` (OpenRouter / DeepInfra) |
| Gateway | OpenRouter |
| Provider | DeepInfra (endpoint tag `deepinfra/fp8`, quantization fp8) |
| Study label | Post-hoc cross-model robustness replication |
| Arms | `impact_plan`, `impact_plan_v2` |
| Scenarios | djangocms-external-validity-{002,004,005,006,007,008} |
| Repetitions | 1..5 |
| Total cells | 6 scenarios × 2 arms × 5 reps = **60** (no run 61) |
| Temperature | 0 |
| Completion cap | 4096 |
| Reasoning / thinking | **DISABLED** (`reasoning.enabled=false`; verified via
  `usage.completion_tokens_details.reasoning_tokens == 0` and absence of any
  reasoning field in the message) |
| Graph | OFF / NOT INJECTED |
| Fallback | OFF (`provider.allow_fallbacks=false`,
  `provider.require_parameters=true`) |
| Gold | evaluation only, applied AFTER inference |
| Result-based reruns | FORBIDDEN |
| Cell replacement | FORBIDDEN |
| Retry policy | max 1 transient retry (429/5xx/transport); 4xx never retried |

## 2. Intentional changed dimensions (ONLY)

1. Model: `qwen/qwen3-coder` → `qwen/qwen3-32b`.
2. Explicit reasoning-mode configuration: Qwen3-32B is a hybrid reasoning
   model; reasoning is explicitly disabled so the replication matches the
   historical direct/non-thinking Qwen3-Coder contract and cannot consume an
   untracked hidden thinking budget.

Everything else (repositories, cases, prompts, schemas, numeric-ID map,
hidden gold, universe, ordering, scorer, failure semantics, temperature, cap,
gateway, provider, graph absence) is byte-for-byte the frozen historical
treatment.

## 3. Preregistered metrics

### CM1 — Operational robustness (per arm)
Recorded / valid / failed / truncations / failure taxonomy / prompt tokens /
completion tokens / total tokens / calls / latency / cost.

### CM2 — Selection fidelity (per arm, valid cells only)
TP, FP, FN, Precision, Recall, F1, FNR, full-recall rate.

### CM3 — Scenario 006
P/R/F1, TP/FP/FN, full recall, all selected-file frequencies (gold/non-gold).

### CM4 — Cross-model Sparse-v2 agreement (DESCRIPTIVE)
For each scenario: ALL valid historical Qwen3-Coder Sparse-v2 runs × ALL valid
new Qwen3-32B Sparse-v2 runs, full cross-product Jaccard of selected-file
sets. **Do NOT pair r1 with r1.** Report pair count, mean/median/min/max, and
per-file selection frequencies. No equivalence/significance claim.

## 4. Directional robustness label (DESCRIPTIVE)

`DIRECTIONALLY REPLICATED` iff new Sparse-v2 has BOTH
(1) higher operational-validity rate than new v1 AND
(2) lower truncation rate than new v1.
Otherwise `NOT DIRECTIONALLY REPLICATED`. No statistical significance.

## 5. Gates (exact, no seventh)

1. Dataset Validation · 2. Prompt Validation · 3. Pipeline Smoke Test ·
4. Dry Run (60 cells / 60 unique IDs / 6 scenarios / 2 arms / 5 reps / 0
scientific calls / 0 tokens) · 5. Integration Test · 6. Metric Verification ·
then Independent Audit. All must PASS before cell 1 and again at closure.

## 6. Cost / time lock

- Hard ceiling: **$0.50** total scientific spend (probes tracked separately).
- Runtime ceiling: **4 hours** serial.
- STOP before cell 1 if projected cost > ceiling or runtime > ceiling.

## 7. Evidence persistence

- `run_records.jsonl` append-only, persisted immediately after every cell.
- Per-run JSON + raw response text + SHA-256 persisted immediately.
- Checkpoint every 5 recorded cells.
- Never rerun an already recorded cell.

## 8. Verification

- `scripts/verify_qwen3_32b_crossmodel_claims.py` (zero API; recomputes all
  headline metrics from frozen RunRecords; verifies raw hashes; non-zero exit
  on inconsistency).
- `python scripts/verify_paper_claims.py` must still PASS.

## 9. Provenance

- FROZEN_INPUT_PARITY.json persisted before cell 1.
- endpoint_freeze.json (live OpenRouter/DeepInfra metadata) persisted.
- capability_probes.json (two non-study schema probes) persisted.

Preregistered at UTC: 2026-09-11 (study freeze).