# Phase 4C — Model Backends Reference

**Protocol Version:** 1.0 (FROZEN)
**Date:** 2026-07-22
**Status:** COMPLETE

---

## 1. Package Structure

```
src/benchmark/llm/
  __init__.py              # Public exports
  base.py                  # BackendFactory (Registry wrapper)
  mock_backend.py          # MockLLMBackend
  dry_run_backend.py       # DryRunLLMBackend
  kaggle_qwen_backend.py   # KaggleQwenBackend skeleton
```

## 2. Backend Classes

### MockLLMBackend
- **Location:** `src/benchmark/llm/mock_backend.py`
- **Constructor:** `MockLLMBackend(response_text="mock response")`
- **Behavior:** Returns `LLMResponse` with configured text, token count derived from prompt/response length, `finish_reason="stop"`
- **Determinism:** Same input always produces same output
- **Conforms to:** `LLMBackend` protocol

### DryRunLLMBackend
- **Location:** `src/benchmark/llm/dry_run_backend.py`
- **Constructor:** `DryRunLLMBackend(fixture_dir=None)`
- **Behavior:**
  - If `fixture_dir` is `None` or directory does not exist: returns default `"dry-run default response"`
  - If `fixture_dir/fixture_response.json` exists: loads response text, token counts, and finish_reason from JSON
  - Ignores non-fixture JSON files in the directory
- **Conforms to:** `LLMBackend` protocol

### KaggleQwenBackend
- **Location:** `src/benchmark/llm/kaggle_qwen_backend.py`
- **Constructor:** `KaggleQwenBackend(model_name="Qwen/Qwen2.5-72B-Instruct")`
- **Lazy imports:** `torch` and `transformers` only imported inside `_lazy_import()` method, never at module level
- **Local behavior:** `generate()` calls `_lazy_import()` which raises `ModelBackendError` if torch/transformers are not available (i.e., in local environment)
- **Kaggle behavior:** `generate()` raises `ModelBackendError("skeleton for Kaggle execution only")` — actual inference code deferred to Kaggle
- **Conforms to:** `LLMBackend` protocol
- **Safety:** Importing `KaggleQwenBackend` does NOT import torch or transformers

## 3. BackendFactory

- **Location:** `src/benchmark/llm/base.py`
- **Wraps** `Registry[LLMBackend]` from `benchmark.core.registry`
- **Methods:** `register(name, backend_cls)`, `create(name, **kwargs)`, `list_names()`, `freeze()`, `__contains__`, `__len__`
- **Error handling:** Unknown backend name raises `UnknownRegistrationError`; frozen registry raises `RuntimeError`

## 4. Dependency Rules

- `llm/` imports: `benchmark.core.protocols`, `benchmark.core.models`, `benchmark.core.exceptions`, `benchmark.core.registry`
- `llm/` does NOT import: `repositories/`, `scenarios/`, `config/`, `strategies/`, `evaluation/`
- Kaggle-only dependencies (`torch`, `transformers`) are lazily imported inside method bodies only

## 5. Test Coverage

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `tests/unit/llm/test_llm_mock_backend.py` | 6 | Mock backend deterministic output, protocol conformance |
| `tests/unit/llm/test_llm_dry_run_backend.py` | 5 | Default response, fixture loading, missing dir, non-fixture files |
| `tests/unit/llm/test_llm_kaggle_qwen_backend.py` | 3 | Local execution raises, lazy import safety, protocol conformance |
| `tests/unit/llm/test_llm_factory.py` | 8 | Register+create, unknown raises, freeze, contains, len |
| `tests/test_import_isolation.py` | 1 | `import benchmark.llm` does not import torch/transformers |
