# Sparse-vs-Full Causal Parity Audit

**Date:** 2026-09-18
**Type:** POST-HOC / verification audit of FROZEN artifacts (ZERO API; read-only)
**Audited arms:** `full_v2` vs `sparse_v2` of study `real-commit-p1-full-v2-vs-sparse-v2-01`
(P1 M4A-3, 10 held-out tasks x 2 arms x 3 reps = 60 cells; executed 2026-09-14).
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731

---

## 1. Purpose

The P1 comparison treats the sparse representation as the ONLY intended
treatment difference between the two arms. This audit verifies, from frozen
configs/artifacts, that every other causal dimension matches between the
Full and Sparse arms. The audit does NOT change any frozen result; it is for
thesis/reviewer clarity.

## 2. Verdict

**PARITY_VERIFIED** — the arms match on every audited dimension except the
serialization/schema block of the prompt, which is the INTENDED treatment
difference (the arm definition itself). The controlled-diff proof confirms the
prompts are identical once the serialization-policy block is stripped.

## 3. Dimension-by-dimension evidence (from frozen run records + endpoint freeze)

| Dimension | Full-v2 value | Sparse-v2 value | Match |
|---|---|---:|---:|---|
| Model / version | `qwen/qwen3-coder` (Qwen3-Coder-480B-A35B-Instruct) | identical | MATCH |
| Quantization | `fp4` | identical | MATCH |
| Provider / route | DeepInfra pinned through OpenRouter, `deepinfra/turbo`, fallback OFF | identical | MATCH |
| Exact model id | `openrouter:qwen/qwen3-coder@deepinfra/turbo` | identical | MATCH |
| Parent snapshot / candidate universe | same case_id → same public bundle (deterministic candidate map; identical `decoded_candidate_count` per case) | identical | MATCH |
| Context | parent-only intent + candidate universe + dependency graph (no hidden proxy in any prompt) | identical | MATCH |
| Temperature / decoding | 0.0; `model_calls = 1` | identical | MATCH |
| Reasoning mode | direct/non-thinking (no reasoning control parameter sent) | identical | MATCH |
| Completion cap | 16384 | identical | MATCH |
| Tools | none (no `tools`/`tool_choice` in the frozen endpoint params) | identical | MATCH |
| Repetitions | 3 nested reps per task | 3 nested reps per task | MATCH |
| Prompt content (except the necessary schema difference) | `PROMPT_CONTROLLED_DIFF` = **PASS on 10/10 tasks** (`reports/REAL_COMMIT_M4A3_P1_VALIDATION.md`): the FULL and SPARSE prompts share the SAME semantic contract (action vocab, reason codes, evidence schema, prompt skeleton) and are byte-identical after stripping the serialization-policy block (`stripped_full_sha256 == stripped_sparse_sha256`). The ONLY intended treatment difference is the serialization-policy block: FULL emits exactly one decision per candidate id (incl. explicit `PRESERVE` rows); SPARSE emits only non-`PRESERVE` decisions with omitted ids decoded deterministically to `PRESERVE`. | controlled difference | MATCH (intended) |

## 4. Evidence locations

- Frozen protocol (arms + controlled-diff statement):
  `reports/REAL_COMMIT_M4A3_P1_PROTOCOL.md` §3–§4.
- Frozen endpoint / model freeze:
  `research/real-commit-p1-01/endpoint_freeze.json`.
- Frozen run records (60 cells; per-cell config fields):
  `research/real-commit-p1-01/run_records.jsonl`.
- Validation gates incl. `PROMPT_CONTROLLED_DIFF` PASS 10/10:
  `reports/REAL_COMMIT_M4A3_P1_VALIDATION.md`, `reports/real_commit_m4a3_p1_gates.json`.
- Raw responses + SHA-256 sidecars:
  `research/real-commit-p1-01/runs/raw/*.{txt,sha256}`.

## 5. What this audit does and does NOT establish

- **Does establish:** the Full-vs-Sparse outcome difference (cost / token use /
  F1) is attributable to the serialization representation under an otherwise
  matched causal setting, at the level of a controlled-representation design
  (not a claim of a fully randomized experiment).
- **Does NOT establish:** (1) that the representation effect generalizes beyond
  this single model/provider; (2) that the observed-change proxy is semantic
  gold; (3) any superiority of one arm as a "better" impact policy — the P1
  paired ΔF1 CI crosses zero, and the cost effect is descriptive. Both arms are
  frozen; nothing here changes the submitted science.

## 6. Limits / caveats (truthful)

- The controlled-diff proof is a deterministic string-stripping proof over the
  frozen prompt templates; it does not re-run any model.
- Temperature 0 with 1 call per cell gives a single deterministic draw per
  cell; the 3 nested reps provide cell-level replication, not posterior
  sampling.
- The audit is verification of recorded configuration identity, not an
  end-to-end interception of the provider's internal routing state.