# Model / Provider Guide

> **Last reviewed:** 2026-09-14 (prospective refactor milestone).
>
> **Scientific rule:** the historical primary Qwen result is **not** made dynamic
> retroactively. Historical study launchers keep their frozen constants and
> reproduce the old evidence exactly. This guide describes the *future*
> model/provider layer: dynamic selection is allowed only BEFORE a protocol
> freeze; a scientific run must freeze the fully resolved profile before call #1
> and refuse to continue if the resolved profile differs from the frozen
> manifest.

---

## 1. Supported gateways

The project standardizes on the **OpenAI-compatible chat-completions transport**
because every supported gateway exposes it:

| Gateway | Base URL | Auth header | Notes |
|---|---|---|---|
| OpenRouter | `https://openrouter.ai/api/v1` | `Authorization: Bearer $OPENROUTER_API_KEY` | provider pin via `provider.order`, fallback control via `provider.allow_fallbacks` |
| DeepSeek direct | `https://api.deepseek.com/v1` | `Authorization: Bearer $DEEPSEEK_API_KEY` | OpenAI-compatible; confirm structured-output support per model |
| Hugging Face Inference Providers | `https://router.huggingface.co/v1` | `Authorization: Bearer $HF_TOKEN` | model must be exact `<repo-id>:<provider>` when provider identity must be frozen |

Only add provider-specific adapters for true incompatibilities.

## 2. Model profiles

Profiles are declared in
[`config/model_profiles.yaml`](../config/model_profiles.yaml) and loaded by
[`src/benchmark/model_profiles/__init__.py`](../src/benchmark/model_profiles/__init__.py).

### Current profiles

| id | gateway | model | provider_pin | api_key_env | structured_output |
|---|---|---|---|---|---|
| `qwen3-coder-openrouter-deepinfra` | openrouter | `qwen/qwen3-coder` | `deepinfra/turbo` | `OPENROUTER_API_KEY` | json_schema |
| `deepseek-v4-flash-openrouter` | openrouter | `deepseek/deepseek-v4-flash-0731` | — | `OPENROUTER_API_KEY` | json_schema |
| `deepseek-v4-flash-direct` | deepseek | `deepseek-chat` | — | `DEEPSEEK_API_KEY` | prompt_only_json |
| `deepseek-v4-pro-openrouter` | openrouter | `deepseek/deepseek-v4-pro-0813` | — | `OPENROUTER_API_KEY` | json_schema |
| `hf-example` | huggingface | `<repo-id>:<provider>` | — | `HF_TOKEN` | json_schema |

### Profile fields

- `id` — unique short identifier.
- `gateway` — one of `openrouter | deepseek | huggingface | openai_compatible`.
- `base_url` — endpoint base.
- `model` — provider model id.
- `provider_pin` — optional exact provider tag when provider identity is part of
  the experimental control (e.g. `deepinfra/turbo`).
- `api_key_env` — environment-variable NAME of the secret; never a literal value.
- `temperature` — sampling temperature (0.0 for scientific runs).
- `max_completion_tokens` — completion cap.
- `reasoning` — optional reasoning settings (e.g. thinking budget). P1 used
  direct/non-thinking (no reasoning control parameter sent).
- `structured_output` — one of `json_schema | json_object | prompt_only_json |
  unsupported`.
- `fallbacks` — `false` for scientific runs; only `true` when a user explicitly
  enables routing/fallback for ordinary non-scientific use.
- `timeout_seconds`, `retry_policy` — bounded, deterministic.
- `budget_abort_ceiling_usd` — pre-run safety threshold (NOT a scientific result).

## 3. Resolution and frozen identity

`resolve_profile(profile)` returns an immutable `ResolvedModelConfig` and
persists:

- `profile_id`, `gateway`, `base_url`, `model`, `provider_pin`, `exact_model`;
- `api_key_env` + `api_key_present` (boolean only — the token value is never
  read, logged, or persisted);
- `temperature`, `max_completion_tokens`, `reasoning`, `structured_output`,
  `fallbacks`, `timeout_seconds`, `retry_policy`;
- `budget_abort_ceiling_usd`;
- `profile_sha256` (stable profile fingerprint).

`assert_resolved_matches_frozen(resolved, frozen_manifest)` **fails closed** if
the live-resolved profile differs from the frozen manifest identity. A live
scientific run must call this before call #1.

## 4. Capability probe (structured-output contract)

Same-study comparisons must use compatible output contracts. Capability states:

- `json_schema_strict` — native strict JSON schema (preferred for P1-class arms);
- `json_object` — JSON-object mode (non-strict schema);
- `prompt_only_json` — prompt-instructed JSON;
- `unsupported`.

Do **NOT** silently downgrade a scientific arm from strict JSON schema to
prompt-only JSON. The capability probe determines whether a model/provider is
eligible for a given study.

## 5. DeepSeek recommendation

Do **not** replace the Qwen primary result. Add DeepSeek as a **future
cross-model replication profile**:

- Priority candidate: `deepseek/deepseek-v4-flash-0731` through OpenRouter —
  inexpensive and currently advertises structured outputs.
- Optional stronger/costlier profile: DeepSeek V4 Pro 0813.

Scientific question:
> "Does the representation-cost effect replicate across model families?"

not:
> "Can we find a model that makes our F1 look better?"

**No new DeepSeek scientific experiment was run in the 2026-09-14 refactor
milestone.**

## 6. Hugging Face

Before admitting an HF profile into a scientific matrix:

1. capability probe the exact model/provider;
2. confirm JSON-schema support;
3. confirm completion cap;
4. freeze provider selection (`:provider` or explicit policy);
5. disable silent failover when provider identity is part of the experimental
   control.

Required tests (covered in `tests/`):
- no token value logged;
- dry run requires no token;
- probe fails clearly when token missing;
- structured-output capability recorded;
- provider/model identity persisted.

## 7. Rate-limit / retry handling

Classify:
- account quota;
- upstream shared-pool overload;
- provider concurrency;
- transient 5xx/network;
- permanent request/schema error.

For scientific runs:
- frozen provider identity;
- no silent provider fallback;
- deterministic bounded retry policy;
- persist retry count/error category;
- never result-dependent rerun.

For ordinary non-scientific use: the user may explicitly enable fallback/routing.

## 8. Cost accounting

Three quantities must never be conflated (see
[`src/benchmark/model_profiles/cost.py`](../src/benchmark/model_profiles/cost.py)):

| Name | Meaning |
|---|---|
| `budget_abort_ceiling_usd` | pre-run safety threshold; aborts a run before uncontrolled spending |
| `estimated_api_cost_usd` | token usage × frozen endpoint prices |
| `provider_billed_cost_usd` | actual provider/account billing (nullable) |

Historical records keep the legacy `api_cost` field and remain readable through
`split_legacy_cost(...)`. Historical raw records are never rewritten.

## 9. Unified CLI

```powershell
python scripts/benchmark_cli.py models
python scripts/benchmark_cli.py dry-run --study <study> --model-profile <id>
python scripts/benchmark_cli.py probe --study <study> --model-profile <id>
python scripts/benchmark_cli.py live --study <study> --model-profile <id>
python scripts/benchmark_cli.py verify --study <study>
```

Optional future matrix command:

```powershell
python scripts/benchmark_cli.py matrix --study <study> --model-profile a --model-profile b
```

The CLI is a thin wrapper and does NOT duplicate study logic. Study-specific
launchers remain the reproducible source of truth.

## 10. Secret handling

- Secrets are referenced by environment-variable name only.
- Never write a literal token into YAML/JSON or commit it.
- The model layer only records `api_key_present` (boolean), never the value.
- OpenCode/system prompt: use secure PowerShell `Read-Host -AsSecureString`
  flows for interactive entry.