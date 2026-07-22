# Phase 4C — Model Backends: Completion Report

**Date:** 2026-07-22
**Protocol Version:** 1.0 (FROZEN)
**Status:** COMPLETE
**Approved for Phase 4D:** true

## Summary

Phase 4C implemented three LLM backends (MockLLMBackend, DryRunLLMBackend, KaggleQwenBackend skeleton) plus the BackendFactory registry integration under `src/benchmark/llm/`. 23 new tests (229 total suite) pass all quality gates. Phase 4D (Execution Core) is the exact next task.

## Files Created (5 production + 5 test + 2 doc = 12 new files)

### Source — 5 files
- `src/benchmark/llm/__init__.py` — Public exports
- `src/benchmark/llm/base.py` — BackendFactory wrapping Registry[LLMBackend]
- `src/benchmark/llm/mock_backend.py` — MockLLMBackend (deterministic)
- `src/benchmark/llm/dry_run_backend.py` — DryRunLLMBackend (fixture loading)
- `src/benchmark/llm/kaggle_qwen_backend.py` — KaggleQwenBackend skeleton (lazy imports)

### Tests — 5 files (23 tests)
- `tests/unit/llm/__init__.py` — Package init
- `tests/unit/llm/test_llm_mock_backend.py` — 6 tests
- `tests/unit/llm/test_llm_dry_run_backend.py` — 5 tests
- `tests/unit/llm/test_llm_kaggle_qwen_backend.py` — 3 tests
- `tests/unit/llm/test_llm_factory.py` — 8 tests
- `tests/test_import_isolation.py` — Modified: added 1 LLM-specific import test

### Documentation — 2 files
- `docs/PHASE4C_MODEL_BACKENDS_REFERENCE.md`
- `reports/PHASE4C_MODEL_BACKENDS_REPORT.md` (this file)

## Quality Gate Results

| Gate | Command | Result |
|------|---------|--------|
| Ruff lint | `ruff check src tests` | 0 violations |
| Mypy strict | `mypy --strict src/benchmark/llm/` | 0 errors |
| Pytest | `python -m pytest tests/` | 229/229 passed (2.01s) |
| pip check | `python -m pip check` | No broken requirements |
| Import isolation | Subprocess: `import benchmark.llm` | torch, transformers NOT in sys.modules |

## Design Decisions

1. **Lazy imports for Kaggle backend**: `torch` and `transformers` are imported inside `_lazy_import()` called from `generate()`, never at module level. Importing `KaggleQwenBackend` does not trigger torch/transformers download.
2. **BackendFactory wraps Registry**: Not a new registry type — delegates to the generic `Registry[LLMBackend]` for registration, creation, freeze.
3. **DryRunLLMBackend fixture format**: Expects `fixture_response.json` with keys: `text`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `finish_reason`. Falls back to default response if no fixture available.
4. **MockLLMBackend deterministic**: Same `response_text` always produces same `LLMResponse` including token counts.
5. **ARGG002 suppressed via per-file-ignores**: Backend `generate()` methods have unused parameters required by the `LLMBackend` protocol signature; suppressed with `pyproject.toml` per-file-ignore.

## Deviations from Blueprint

None. All implementations follow the specifications in `docs/SOFTWARE_ARCHITECTURE.md`, `docs/PROJECT_STRUCTURE_MAP.md`, and `docs/PHASE4_IMPLEMENTATION_BLUEPRINT.md`.

## Remaining Risks

| Risk | Notes |
|------|-------|
| LR-3 (No test data boundary) | Test fixtures created but not populated |
| LR-5 (Paper vs. implementation drift) | Ongoing monitoring |
| LR-7 (django CMS and Saleor not cloned) | Deferred |
| LR-8 (Scenario content quality) | Manual review recommended |

## Exact Next Task

**Phase 4D — Execution Core**: Implement BenchmarkRunner, BenchmarkPipeline, RepairLoop, BudgetManager, IsolationContext. Pipeline processes scenario through strategy; repair loop respects budget; isolation prevents cross-run contamination.
