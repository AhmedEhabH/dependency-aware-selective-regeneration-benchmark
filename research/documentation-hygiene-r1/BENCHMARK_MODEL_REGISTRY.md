# BENCHMARK MODEL REGISTRY — M17 Documentation Hygiene R1 (2026-10-12)

Single human-readable registry of model identities used in actual
benchmark/evaluation arms, their roles, and their frozen provenance sources.

**Status values:**
- `EXECUTED_BENCHMARK` — a model actually executed as a benchmark treatment.
- `EXECUTED_EMBEDDING` — a model actually executed for embedding realization.
- `PLANNED_NOT_EXECUTED` — declared/config only; never executed as an arm.
- `ORCHESTRATION_ONLY` — used for repository/orchestration execution only; NOT
  a benchmark arm and MUST NOT appear in benchmark methodology/results.
- `RELATED_WORK_ONLY` — appears as a rater/reviewer/related-work entity only.

---

## 1. EXECUTED_BENCHMARK

| role | model_id | provider_or_route | experiment/arm | frozen_source_artifact | frozen_source_hash | temperature | budget | status |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| historical primary scientific model + Sparse-v2 study model | Qwen3-Coder-480B-A35B-Instruct (`qwen/qwen3-coder`) | OpenRouter -> DeepInfra (`deepinfra/turbo`) | djangoCMS selection study (Agent + ImpactPlan-v1), ImpactPlan-v2, microstudies, WP-1b MAIN_297 agent arm | `docs/MODEL_IDENTITIES.md`; `research/wp1b/main-297-2026-09-22/run_state.json` (route `openrouter:qwen/qwen3-coder@deepinfra/turbo`) | n/a (route persisted in run_state.json) | 0 | cap 4096/16384 by arm | EXECUTED_BENCHMARK |
| completed cross-model robustness replication | Qwen3-32B (`qwen/qwen3-32b`) | OpenRouter -> DeepInfra (`deepinfra/fp8`) | `scientific-stagec-djangocms-qwen3-32b-crossmodel-01` (60 cells) | `docs/MODEL_IDENTITIES.md`; `reports/QWEN3_32B_CROSSMODEL_AGREEMENT.md` | n/a | 0 (reasoning disabled) | per frozen study | EXECUTED_BENCHMARK |
| new cross-model / cross-provider coder robustness replication | Qwen3-Coder-30B-A3B-Instruct (`qwen/qwen3-coder-30b-a3b-instruct`) | OpenRouter (provider frozen from live metadata) | `scientific-stagec-djangocms-qwen3-coder-30b-a3b-crossmodel-01` | `docs/MODEL_IDENTITIES.md`; `reports/QWEN3_CODER_30B_A3B_CROSSMODEL_AGREEMENT.md` | n/a | model-native non-thinking | per frozen study | EXECUTED_BENCHMARK |

## 2. EXECUTED_EMBEDDING

| role | model_id | provider_or_route | experiment/arm | frozen_source_artifact | frozen_source_hash | temperature | budget | status |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| RM-CSS dense retrieval embedding realization | Qwen3-Embedding-8B (`qwen/qwen3-embedding-8b`, alias `qwen/n-8b`) | OpenRouter embeddings interface -> DeepInfra (`$0.01/M` live-verified) | RM-CSS (Saleor-300, MAIN_297) + contamination-robustness bridge (DEV only) | `src/benchmark/signal/or_embeddings.py` (`OPENROUTER_EMBED_MODEL`); `reports/CONTAMINATION_ROBUSTNESS_BRIDGE_CLOSURE_2026-09-19.md` | n/a (client-constant) | n/a (embeddings) | `$0.01/M`; bridge ceiling `$0.50` | EXECUTED_EMBEDDING |

## 3. PLANNED_NOT_EXECUTED

| role | model_id | provider_or_route | experiment/arm | frozen_source_artifact | frozen_source_hash | temperature | budget | status |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| future cross-model candidate | DeepSeek V4 Flash 0731 (`deepseek/deepseek-v4-flash-0731`) | OpenRouter | NOT run in milestone | `docs/MODEL_IDENTITIES.md` (profile `deepseek-v4-flash-openrouter`); `config/model_profiles.yaml` | n/a | n/a | n/a | PLANNED_NOT_EXECUTED |
| future robustness candidate | DeepSeek V4 Pro 0813 | OpenRouter | NOT run | `docs/MODEL_IDENTITIES.md` (profile `deepseek-v4-pro-openrouter`) | n/a | n/a | n/a | PLANNED_NOT_EXECUTED |

## 4. ORCHESTRATION_ONLY

| role | model_id | provider_or_route | experiment/arm | frozen_source_artifact | frozen_source_hash | temperature | budget | status |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| repository/orchestration execution model (NOT a benchmark arm) | DeepSeek V4 Flash (`deepseek/deepseek-v4-flash-0731`, and GLM-5.3-Flash during one mission) | OpenCode environment | n/a — orchestration only | `docs/EXECUTION_AGENT_PROVENANCE_2026-09-20.md` | n/a | n/a | n/a | ORCHESTRATION_ONLY |

## 5. RELATED_WORK_ONLY

| role | model_id | provider_or_route | experiment/arm | frozen_source_artifact | frozen_source_hash | temperature | budget | status |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| blinded semantic-plausibility raters (frozen rater outputs) | ChatGPT and Claude (external assistants) | external chat sessions | AI semantic plausibility audit (descriptive, NOT human semantic gold) | `reports/AI_SEMANTIC_AUDIT_AGREEMENT_REPORT.md`; `research/semantic_audit/ai_blinded_v1/` | per-file SHA-256 recorded in report | n/a | n/a | RELATED_WORK_ONLY |

---

## Classification rules applied

- `qwen/qwen3-coder` is an executed benchmark model and MUST remain named in
  public benchmark methodology.
- DeepSeek V4 Flash appears only as the OpenCode orchestration model
  (`ORCHESTRATION_ONLY`) or as a declared-but-not-run future candidate
  (`PLANNED_NOT_EXECUTED`); it is NOT copied into executed benchmark results.
- ChatGPT / Claude are NOT benchmark treatments; they appear only as rater
  entities in the semantic-plausibility audit (`RELATED_WORK_ONLY`).
- No model name in this registry was added from memory; every entry is
  traceable to the frozen artifact listed in `frozen_source_artifact`.