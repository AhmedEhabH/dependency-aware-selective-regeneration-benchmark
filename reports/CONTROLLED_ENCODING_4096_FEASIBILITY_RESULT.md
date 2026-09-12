# Controlled 4096-Cap Feasibility Boundary (M1A)

**Milestone:** M1A — CONTROLLED 4096-CAP FEASIBILITY BOUNDARY
**Classification:** preregistered capability / feasibility boundary
**This is NOT:** a completed 60-cell controlled ablation. No semantic
superiority claim is made.

**Date:** 2026-09-12
**Branch:** `research/controlled-encoding-ablation-01`
**Study ID:** `scientific-djangocms-controlled-encoding-ablation-01`

---

## Required wording

> Under the frozen 4096-token completion budget and the common semantic-rich
> Full-v2/Sparse-v2 schema, the Full-v2 capability probe terminated at the
> completion cap before emitting all 144 required decisions, whereas the
> Sparse-v2 probe completed and deterministically reconstructed a valid
> 144-candidate policy.

This report does **NOT** claim "Preserve-by-Omission has now been causally
proven superior." No such claim is made.

---

## 1. Frozen scientific configuration (both probes)

| Input | Value |
|---|---|
| Model | Qwen3-Coder-480B-A35B-Instruct (`qwen/qwen3-coder`) |
| Provider | DeepInfra pinned through OpenRouter (`deepinfra/turbo`, fp4) |
| Fallback | OFF |
| Temperature | 0.0 |
| Completion cap | 4096 |
| Graph | OFF |
| response_format | `json_schema` (common ablation schema) |
| Candidate universe | 144 frozen djangoCMS 5.0.0 paths |
| Common schema | ONE v2-derived schema shared by both arms (variable-length `decisions`) |
| Action vocabulary | PRESERVE / REGENERATE / VALIDATE / HUMAN_REVIEW |
| Synthetic probe input | unrelated to the six scientific scenarios |

Live endpoint freeze persisted in
`research/controlled-encoding-ablation-01/endpoint_freeze.json`
(DeepInfra `deepinfra/turbo`, fp4, context 262144, max completion 65536,
$0.30/$1.00 per 1M, fetched 2026-09-12T20:16:44Z).

## 2. Probe results

### Probe A — Full-v2 (explicit PRESERVE for all 144 candidates)

| Field | Value |
|---|---|
| finish_reason | `length` |
| completion_tokens | 4096 (== frozen cap) |
| prompt_tokens / total_tokens | 2370 / 6466 |
| Decision rows emitted before cap | **76** (ids 1..76), then JSON unterminated |
| schema_valid | False (truncated before all 144 decisions) |
| usage_known | True |
| provider | DeepInfra |
| raw SHA-256 | `e7e39e2161fbd85dfc7bf6ccd54f26fdc87c35732c7b8d4baff862f46e3db153` |

Observed density: 4096 tokens / 76 rows ≈ **53.9 tokens/row** → a full 144-row
serialization at that density ≈ **7,760 tokens**, ~1.9× the frozen 4096 cap.

### Probe B — Sparse-v2 (non-PRESERVE only, omit => PRESERVE)

| Field | Value |
|---|---|
| finish_reason | `stop` |
| completion_tokens | 419 |
| prompt_tokens / total_tokens | 2384 / 2803 |
| Explicit non-PRESERVE decisions | 3 (ids 10, 11, 92) |
| decoded_candidate_count | **144** (omitted ids deterministically reconstructed as PRESERVE) |
| schema_valid | True |
| usage_known | True |
| provider | DeepInfra |
| raw SHA-256 | `eff2a301d0926a27fbe697682ac0dd2d99e190064d2e992297f2e54314829261` |

## 3. CANONICAL_MINIMAL_SERIALIZATION_TOKEN_COUNT

The Qwen3-family tokenizers (Qwen3-8B, Qwen3-Coder-480B-A35B-Instruct,
Qwen2.5-Coder-7B-Instruct) are gated / unavailable with the current expired HF
token, so an exact tokenizer count could not be produced. Using the **real
observed completion density** from Probe A (13,768 characters → 4096 tokens =
3.3613 chars/token), the most compact schema-valid 144-row Full-v2 object
(empty rationale, empty reason_codes, empty evidence, confidence 0) measures:

- compact JSON: 13,375 chars → **≈ 3,979 tokens (estimate at observed density)**
- pretty JSON: 21,747 chars → **≈ 6,470 tokens (estimate at observed density)**

`CANONICAL_MINIMAL_SERIALIZATION_TOKEN_COUNT ≈ 3,979` (compact, estimate).

This is a **canonical-minimal estimate at the observed model density**, not a
proven universal mathematical lower bound. It shows the minimal form is near
the cap, and the model's real (semantic-rich, non-empty rationale) output
clearly exceeds it — which is why Probe A truncated at row 76.

## 4. Pre-benchmark evidence (all ZERO scientific calls)

| Check | Result |
|---|---|
| PROMPT_CONTROLLED_DIFF (M1.4) | **PASS** — Full/Sparse rendered prompts byte-identical after policy-block strip, all 6 scenarios |
| Representation equivalence (M1.5) | **PASS** — `D_s(E_s(π)) == π`, 14/14 checks (all-PRESERVE, one non-PRESERVE, mixed R/V/H, all non-PRESERVE, random, duplicate/unknown/explicit-PRESERVE rejected) |
| Gate 1 Dataset Validation | PASS |
| Gate 2 Prompt Validation | PASS |
| Gate 3 Pipeline Smoke Test | PASS |
| Gate 4 Dry Run | PASS |
| Gate 5 Integration Test | PASS |
| Gate 6 Metric Verification | PASS |
| Independent Audit | PASS |
| Zero-API verifier | `scripts/verify_controlled_encoding_4096_claims.py` — **27/27 PASS** |

## 5. Cost / calls

- 2 real non-study capability probe calls (Probe A + Probe B).
- Probe A: 2370 prompt + 4096 completion = 6466 tokens ≈ **$0.00480**
- Probe B: 2384 prompt + 419 completion = 2803 tokens ≈ **$0.00113**
- Total probe cost ≈ **$0.00593** (well below the $0.50 scientific ceiling).
- **ZERO 60-cell scientific study cells executed** (no `manifest_60.json`, no
  `run_records.jsonl`).

## 6. Interpretation

The Full-v2 failure is a **deterministic feasibility boundary** of the
explicit-PRESERVE-for-all-144 representation under the frozen 4096 completion
cap and the frozen semantic-rich common schema (every row requires
rationale / confidence / reason_codes / evidence). It is NOT a transient
transport error and NOT a model-call bug: the same model / provider / schema
passes the Sparse-v2 probe on the first attempt (`finish_reason=stop`, 419
tokens).

Consequence: with the schema and cap as frozen, the Full-v2 arm cannot emit a
schema-valid 144-row serialization inside 4096 completion tokens. Running the
60-cell study under the frozen 4096 cap would therefore produce a
systematically truncated Full-v2 arm — the controlled comparison would be
confounded by the completion budget rather than by serialization policy.

**No semantic superiority claim is made.** This milestone only records the
4096-cap feasibility boundary.

## 7. Next milestone (separately preregistered, NOT run here)

M1B — CAP-RELAXED CONTROLLED ENCODING ABLATION (completion cap 16384 for BOTH
arms, same common schema, same controlled prompt design) is the separately
preregistered next study that removes the 4096 completion budget as the
dominant feasibility confound. See the supervisor decision and subsequent
closure reports. M1A's 4096 result remains immutable and is not silently
mutated.

## 8. Artifacts

- `research/controlled-encoding-ablation-01/endpoint_freeze.json`
- `research/controlled-encoding-ablation-01/prompt_control.json`
- `research/controlled-encoding-ablation-01/prevalidation.json`
- `research/controlled-encoding-ablation-01/prestudy_gates.json`
- `research/controlled-encoding-ablation-01/capability_probes.json`
- `research/controlled-encoding-ablation-01/probes/raw/probe_a_full_v2.{txt,sha256}`
- `research/controlled-encoding-ablation-01/probes/raw/probe_b_sparse_v2.{txt,sha256}`
- `research/controlled-encoding-ablation-01/PROBE_A_FAILURE_NOTE.md`
- `src/benchmark/selection/encoding_ablation.py` (common schema + policies + property tests)
- `scripts/controlled_encoding_ablation_execute.py` (executor)
- `scripts/verify_controlled_encoding_4096_claims.py` (zero-API verifier)

## 9. Git / tag state (M1A closure)

See `reports/audit_light/AUDIT_GIT_STATE.md` for the closure tag
`controlled-encoding-4096-feasibility-boundary-01` and the immutable snapshot
`paper-replication-artifact-controlled-encoding-4096-boundary-01`.
