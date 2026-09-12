# M1B — Controlled 16K Cap-Relaxed Encoding Ablation (Results)

**Study ID:** `scientific-djangocms-controlled-encoding-ablation-16k-01`
**Classification:** POST-HOC CONTROLLED CAP-RELAXED ENCODING ABLATION
**Date:** 2026-09-12
**Branch:** `research/controlled-encoding-ablation-16k-01`

## Purpose

Remove the 4096 completion budget as the dominant feasibility confound (that
boundary is M1A's result) so that Full-v2 (explicit PRESERVE serialization of
all 144 candidates) and Sparse-v2 (Preserve-by-Omission) can be compared under
the SAME non-binding completion budget.

## Frozen contract (reuses the audited M1A inputs)

| Input | Value |
|---|---|
| Model | Qwen3-Coder-480B-A35B-Instruct (`qwen/qwen3-coder`) @ DeepInfra (`deepinfra/turbo`, fp4) |
| Fallback | OFF |
| Temperature | 0.0 |
| Completion cap | **16384 (BOTH arms)** — the ONLY study-level change from M1A |
| Graph | OFF |
| Common schema / prompt / policies / scorer | byte-identical to audited M1A |
| Scenarios | 002, 004, 005, 006, 007, 008 (CURATED DEVELOPMENT / MECHANISM SET) |
| Arms | full_v2, sparse_v2 |
| Repetitions | 5 |
| Total cells | 60 |

Frozen parity artifact `FROZEN_M1A_PARITY.json`: **PASS** — nothing except the
completion cap changed from M1A at the study level; nothing except the
serialization policy differs between the M1B arms (all six scenario hashes,
schema/template/policy hashes, candidate map, universe, model, provider,
temperature, graph all identical).

## Capability probes @16384 (before any study cell)

| Probe | finish_reason | completion_tokens | decoded candidates | semantic valid |
|---|---|---|---|---|
| Probe A (Full-v2) | stop | 7,937 | 144 | PASS |
| Probe B (Sparse-v2) | stop | 413 | 144 | PASS |

Both probes PASS (Full-v2 no longer truncates at 16k). Proceeded.

## Execution

**60/60 cells recorded, 60 valid, 0 failed, 0 truncations, 0 transport
failures.** 60 requests issued / 60 responses received / 60 usage-known /
0 usage-unknown. Total 157,980 prompt + 275,761 completion = 433,741 tokens.
Recorded API cost **$0.323156** (ceiling $0.75; live DeepInfra rates).
Full-v2 30/30 valid, Sparse-v2 30/30 valid.

## Per-arm results (valid-run micro-aggregation; all 30 cells valid per arm)

| Metric | Full-v2 | Sparse-v2 |
|---|---|---|
| Recorded / Valid / Failed | 30 / 30 / 0 | 30 / 30 / 0 |
| Truncations | 0 | 0 |
| Validity rate | 1.0 | 1.0 |
| Serialized decision records (mean / median / min / max) | 144 / 144 / 144 / 144 | 4.9 / 5.0 / 1 / 8 |
| Completion tokens (mean / median / min / max) | 8,383 / 8,375 / 7,511 / 9,428 | 809 / 811 / 465 / 1,198 |
| Prompt tokens (mean) | 2,626 | 2,640 |
| Total tokens (mean) | 11,009 | 3,449 |
| Selected / TP / FP / FN | 206 / 93 / 113 / 27 | 147 / 106 / 41 / 14 |
| Precision | 0.451456 | 0.721088 |
| Recall | 0.775000 | 0.883333 |
| F1 | 0.570552 | 0.794007 |
| FNR | 0.225000 | 0.116667 |
| Full-recall count / 30 | 12 | 17 |
| Calls | 30 | 30 |
| Latency (sum, s) | 1,659.125 | 609.029 |
| API cost (USD) | $0.275124 | $0.048032 |

## Primary controlled effects (Sparse-v2 vs Full-v2)

- Δ validity (percentage points): **0.0** (both 1.0)
- Δ truncation (percentage points): **0.0** (both 0)
- Δ mean completion tokens: **−7,573.9** (Sparse 809 vs Full 8,383)
- Δ median completion tokens: **−7,564.5**
- Δ mean serialized decision records: **−139.1** (Sparse 4.9 vs Full 144)
- Δ median serialized records: **−139.0**
- Cost: Sparse $0.048 vs Full $0.275 (≈ −82.5%)

## Result label

> **CONTROLLED ENCODING COST EFFECT: SUPPORTED**

Rationale: under the controlled common contract with a non-binding 16k budget,
both arms achieve 100% operational validity (0 truncations), and Sparse-v2 uses
substantially fewer completion tokens (mean 809 vs 8,383) and serialized
records (mean 4.9 vs 144) for the same decoded 144-candidate policies. This
supports a controlled serialization cost effect of Preserve-by-Omission.

This is a **descriptive controlled observation**, NOT an inference of universal
semantic superiority. The six scenarios remain a CURATED DEVELOPMENT /
MECHANISM SET, not an unbiased held-out evaluation set. The semantic metrics
above (TP/FP/FN/P/R/F1) are secondary descriptive outcomes on these six
curated cases only.

## Scenario-level note (descriptive)

- Scenario 006 is the weakest case in BOTH arms (Full P 0.308 / R 0.800 / F1
  0.444; Sparse P 0.238 / R 0.333 / F1 0.278) — consistent with the historical
  finding that 006 is a hard mechanism case regardless of serialization.
- Scenarios 002/004/005/007/008: Sparse-v2 recall ≥ Full-v2 recall on every
  one; Sparse-v2 precision ≥ Full-v2 precision on every one.

## Verifier

`scripts/verify_controlled_encoding_16k_claims.py` (ZERO API): **42/42 PASS**
(parity, topology, prompt control, representation equivalence, operational
counts, accounting, tokens/cost, serialized records, TP/FP/FN/P/R/F1/FNR
recompute, raw SHA sidecars, closure gates, audit, immutability).

## Six closure gates + Independent Audit: ALL PASS (zero calls)

Closure persisted in `research/controlled-encoding-ablation-16k-01/closure_gates.json`.

## Artifacts

- `research/controlled-encoding-ablation-16k-01/` (endpoint_freeze, parity,
  prompt_control, prevalidation, prestudy_gates, manifest_60, run_records,
  runs/*.json, runs/raw/*.{txt,sha256}, final_metrics, interpretation,
  closure_gates, checkpoints)
- `scripts/controlled_encoding_ablation_16k_execute.py`
- `scripts/verify_controlled_encoding_16k_claims.py`

## Tag / merge

See `reports/audit_light/AUDIT_GIT_STATE.md` for study tag
`controlled-encoding-ablation-16k-study-01-audited` and immutable snapshot
`paper-replication-artifact-controlled-encoding-ablation-16k-01`.
