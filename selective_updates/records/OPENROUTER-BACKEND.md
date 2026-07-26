# OpenRouter API Backend — Minimal Real-Model Integration

**ID:** OPENROUTER-BACKEND  
**Date:** 2026-07-27  
**Status:** VALIDATED  
**Branch:** `feature/openrouter-api-backend`  
**Base commit:** 4bcf533

## Requirement

Add the smallest production-quality OpenRouter LLM backend required to unblock
a local real Scientific Smoke.

## What was done

### New file

- `src/benchmark/llm/openrouter_backend.py` — `OpenRouterBackend` class

### Modified production files

- `src/benchmark/llm/__init__.py` — added `OpenRouterBackend` export
- `seven_arm_benchmark.py` — added `--backend`, `--openrouter-model`,
  `--openrouter-timeout` CLI arguments; updated `make_backend()`,
  `_get_model_identity()`, `_preflight_check()`, `_validate_cli_args()`,
  `run_arm()`, `_run_single_scenario_strategy()`, `main()`

### Tests

- `tests/unit/llm/test_llm_openrouter_backend.py` — 43 tests
- `tests/unit/llm/test_llm_factory.py` — 13 tests (includes 4 make_backend tests)
- `tests/unit/test_cli.py` — 31 tests

### Documentation

- `selective_updates/records/OPENROUTER-BACKEND.md`
- `selective_updates/CHANGE_INDEX.md`
- `selective_updates/metrics/change_metrics.jsonl`
- `README.md`
- `docs/MASTER_IMPLEMENTATION_PLAN.md`
- `docs/PROJECT_HANDOFF.md`

## Audit corrections (2026-07-27)

### 1. Explicit `--backend mock` behavior

`make_backend()` now returns `MockLLMBackend` when `backend_name == "mock"`,
regardless of `dry_run` flag. Previously, explicit `--backend mock` without
`--dry-run` fell through to `KaggleQwenBackend`.

### 2. API-key redaction

`_safe_error_from_http_error()` and all error paths in `_do_request()` now
call `_redact()` on error messages using the resolved API key. The secret is
replaced with `[REDACTED]` in exception strings, logs, and repr. Security
regression tests exercise the real `HTTPError` parsing path with a body
containing `sk-or-v1-DO-NOT-LEAK-12345`.

### 3. Strict token validation

`_validate_token_value()` requires all three keys (`prompt_tokens`,
`completion_tokens`, `total_tokens`) to be present, real `int` (not bool, not
float, not string, not None), and >= 0. Missing fields and invalid types are
rejected with specific error messages. Zero values are preserved.

## Design decisions

- **No external dependency:** Uses `urllib.request` (Python 3.11 standard library only)
- **Async non-blocking:** Blocking HTTP work via `asyncio.to_thread()`
- **Lazy key resolution:** API key read from environment on `generate()`, not in constructor
- **No streaming:** Single-shot non-streaming chat completions
- **No retries:** Error propagation for higher-level retry orchestration
- **No API key in errors/logs/repr:** Security boundary enforced via `_redact()`

## Endpoint

```
POST https://openrouter.ai/api/v1/chat/completions
```

## Environment variable

```
OPENROUTER_API_KEY
```

## Default model

```
nvidia/nemotron-3-super-120b-a12b:free
```

## CLI

```bash
# OpenRouter backend (API-based, no GPU or model download needed):
export OPENROUTER_API_KEY="sk-or-v1-..."
python seven_arm_benchmark.py --backend openrouter \
  --openrouter-model "nvidia/nemotron-3-super-120b-a12b:free" \
  --profile smoke

# Explicit mock backend (no API key needed):
python seven_arm_benchmark.py --backend mock --profile smoke

# Dry-run (also uses mock):
python seven_arm_benchmark.py --dry-run
```

## Backward compatibility

- `--dry-run` continues using `MockLLMBackend`
- `--backend mock` selects `MockLLMBackend` (new)
- Non-dry-run with no explicit `--backend` preserves `KaggleQwenBackend`
- `--backend openrouter` selects `OpenRouterBackend`

## Test results (audit correction)

- 43/43 OpenRouter backend unit tests pass (13 new: real HTTPError parsing,
  secret redaction via real parsing path, strict token validation for missing,
  bool, float, string, negative, None, zero)
- 13/13 LLM factory tests pass (4 new: make_backend mock, dry-run, default)
- 31/31 CLI tests pass
- 1018/1023 full suite pass (5 skipped, pre-existing)
- Zero network calls, zero external dependencies

## Next

- Scientific Smoke remains blocked until this branch is merged and audited
- Pilot remains unauthorized
