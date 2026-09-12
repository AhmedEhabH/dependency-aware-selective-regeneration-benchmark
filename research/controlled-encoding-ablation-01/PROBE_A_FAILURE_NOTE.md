# M1 Capability Probe Failure — Full-v2 vs Sparse-v2

STUDY_ID: scientific-djangocms-controlled-encoding-ablation-01
Branch: research/controlled-encoding-ablation-01
Date: 2026-09-12

## Status

**Probe B (Sparse-v2): PASS**
**Probe A (Full-v2): FAIL — completion-cap truncation at the frozen 4096 cap**

Per mission M1.6 ("If either fails: STOP."), the controlled encoding ablation
stops at the capability-probe gate. No scientific cells were run.

## Frozen scientific configuration

| Input | Value |
|---|---|
| Model | qwen/qwen3-coder (Qwen3-Coder-480B-A35B-Instruct) |
| Provider | DeepInfra pinned through OpenRouter (`deepinfra/turbo`, fp4) |
| Fallback | OFF |
| Temperature | 0.0 |
| Completion cap | 4096 |
| Graph | OFF |
| response_format | json_schema (common ablation schema) |
| Candidate universe | 144 frozen djangoCMS paths |
| Common schema | 1 schema shared by both arms (variable-length decisions array) |

## Probe A failure evidence

- `finish_reason` = `length` (hard stop at the 4096 completion cap)
- `completion_tokens` = 4096
- The model emitted **76 decision rows** (ids 1..76, explicit PRESERVE rows
  with rationale/confidence/reason_codes/evidence per the common schema)
  before the cap; the JSON was left unterminated (truncated mid-row at id 76).
- Observed density: 4096 tokens / 76 rows ≈ **53.9 tokens/row**.
- Full 144-row serialization at that density would require ≈ **7,760 tokens**,
  i.e. ~1.9× the frozen 4096 cap.
- Even at the absolute-minimum row shape permitted by the common schema
  (~104 chars/row ≈ 31 tokens/row at 3.36 chars/token), 144 rows ≈ **4,457
  tokens**, still above the cap.

## Probe B (Sparse-v2) evidence

- `finish_reason` = `stop`
- `completion_tokens` = 419
- 3 non-PRESERVE decisions emitted; omitted ids deterministically decoded to
  PRESERVE -> valid 144-candidate complete policy (semantic validator PASS).

## Interpretation

The failure is a **deterministic feasibility boundary** of the FULL-v2
representation (explicit PRESERVE for every candidate) under the frozen
common schema (which requires rationale/confidence/reason_codes/evidence on
every row) and the frozen 4096 completion cap. It is NOT a transient
transport error and NOT a model-call bug: the same model/provider/schema
passes the Sparse-v2 probe on the first attempt.

Consequence: with the common schema as frozen, the FULL-v2 arm cannot emit a
schema-valid 144-row serialization within 4096 completion tokens. Continuing
the 60-cell study under the current schema would produce a systematically
truncated Full-v2 arm (validity ~0%), i.e. the controlled comparison would be
confounded by the cap rather than by serialization policy.

## Artifacts

- `capability_probes.json` — full probe records (usage, finish_reason, raw SHA)
- `probes/raw/probe_a_full_v2.txt` + `.sha256` — truncated raw response (76 rows)
- `probes/raw/probe_b_sparse_v2.txt` + `.sha256` — valid sparse response
- `endpoint_freeze.json` — live DeepInfra metadata (fp4, 262144 ctx, 65536 max completion)

## Why this is a STOP per protocol

M1.6 requires for both probes: exact model, exact provider, fallback OFF,
temperature 0, 4096 cap, response_format=json_schema, valid JSON, schema
PASS, semantic validator PASS, usage captured, finish_reason captured, raw
persisted, SHA persisted. "If either fails: STOP." Probe A failed the
semantic validator because the model cannot satisfy the FULL-v2 contract
(144 unique ids) inside the frozen completion budget.

## Options for the user (no silent schema/cap change was made)

1. Accept the finding and record it as an operational result (Full-v2 not
   executable at 4096 with this schema); close M1 without the 60-cell run.
2. Relax the common schema (e.g. make rationale/evidence optional) — changes
   frozen scientific inputs; requires a new protocol freeze.
3. Raise the completion cap — violates the frozen 4096 cap in M1.3.
4. Rework the probe input so the synthetic universe is smaller — changes the
   probe's meaning (probe must use the actual common schema + policy).
