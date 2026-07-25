# End-to-End Measurement Boundary

**Date:** 2026-07-25
**Branch:** docs/research-design-v2
**Protocol Version:** 1.0 (FROZEN)
**Source Commit:** 3a16596
**Status:** SPECIFICATION — Research Design V2 Decision (RD-V2-04)

---

## 1. Purpose

This document formally defines the **measurement boundary** for confirmatory end-to-end cost accounting per RD-V2-04. All token efficiency, latency, and model-call claims are valid **only** under comparable correctness and quality outcomes.

---

## 2. Confirmatory End-to-End Cost Includes

The following stages are **inside** the measurement boundary for Experiments B, C, D:

| Stage | Description |
|-------|-------------|
| **Scope Selection** | `ImpactStrategy.analyze_impact()` — impact prediction |
| **Context Construction** | Retrieval (agent), graph build (selective), artifact filtering |
| **Regeneration** | LLM generation per artifact in scope |
| **Repair** | Bounded repair loop (error context → regeneration → re-validate) |
| **Validation** | Functional, regression, architecture validation |

**Outside boundary (excluded from confirmatory cost):**
- Scenario loading / repository setup
- Checkpoint persistence
- Report generation
- Statistical analysis

---

## 3. Required Per-Stage Token Accounting

### 3.1 Selection Stage (Impact Analysis)

| Field | Type | Source |
|-------|------|--------|
| `selection_prompt_tokens` | int | Sum of prompt tokens across all `analyze_impact()` calls |
| `selection_completion_tokens` | int | Sum of completion tokens across all `analyze_impact()` calls |
| `selection_total_tokens` | int | `prompt + completion` |
| `selection_model_calls` | int | Count of `LLMBackend.generate()` calls during selection |
| `selection_duration_seconds` | float | Wall-clock time in `analyze_impact()` |

### 3.2 Regeneration Stage

| Field | Type | Source |
|-------|------|--------|
| `regeneration_prompt_tokens` | int | Sum of prompt tokens for all artifact regenerations |
| `regeneration_completion_tokens` | int | Sum of completion tokens for all artifact regenerations |
| `regeneration_total_tokens` | int | `prompt + completion` |
| `regeneration_model_calls` | int | Count of `generate()` calls during regeneration |
| `regeneration_duration_seconds` | float | Wall-clock time in `SharedLLMExecutor.execute()` |

### 3.3 Repair Stage

| Field | Type | Source |
|-------|------|--------|
| `repair_prompt_tokens` | int | Prompt tokens during repair attempts |
| `repair_completion_tokens` | int | Completion tokens during repair attempts |
| `repair_total_tokens` | int | `prompt + completion` |
| `repair_model_calls` | int | `generate()` calls during repair |
| `repair_duration_seconds` | float | Wall-clock time in `BoundedRepairLoop` (LLM portion only) |

### 3.4 Validation Stage

| Field | Type | Source |
|-------|------|--------|
| `validation_duration_seconds` | float | Wall-clock time in `ValidationPipeline` (no LLM) |

### 3.5 Totals (Derived)

| Field | Computation |
|-------|-------------|
| `total_workflow_tokens` | `selection_total + regeneration_total + repair_total` |
| `total_workflow_model_calls` | `selection_calls + regeneration_calls + repair_calls` |
| `total_workflow_duration_seconds` | `selection_dur + regeneration_dur + repair_dur + validation_dur` |

---

## 4. Attribution Rules

### 4.1 Stage Attribution

| Code Location | Attributed To |
|---------------|---------------|
| `ImpactStrategy.analyze_impact()` | **Selection** (all tokens/calls/duration) |
| `SharedLLMExecutor.execute()` | **Regeneration** (all tokens/calls/duration) |
| `BoundedRepairLoop` internal `generate()` | **Repair** (all tokens/calls/duration) |
| `ValidationPipeline.validate()` | **Validation** (duration only) |

### 4.2 Multi-Call Aggregation

- **Selection:** Some strategies (e.g., `repository_agent`) may call `generate()` multiple times per scenario — **sum all**
- **Regeneration:** One `generate()` per artifact (batched or sequential) — **sum all**
- **Repair:** Each repair attempt may call `generate()` for multiple artifacts — **sum all**

### 4.3 Dry-Run vs Real-Run

| Mode | Accounting |
|------|------------|
| `--dry-run` | All token fields = 0; `duration_seconds` = 0; `model_calls` = 0 |
| Real run | All fields populated from `LLMBackend` response `token_usage` |

---

## 5. TokenUsage Data Model Extension

```python
@dataclass(frozen=True)
class TokenUsage:
    # Selection stage
    selection_prompt_tokens: int = 0
    selection_completion_tokens: int = 0
    selection_total_tokens: int = 0
    selection_model_calls: int = 0
    selection_duration_seconds: float = 0.0

    # Regeneration stage
    regeneration_prompt_tokens: int = 0
    regeneration_completion_tokens: int = 0
    regeneration_total_tokens: int = 0
    regeneration_model_calls: int = 0
    regeneration_duration_seconds: float = 0.0

    # Repair stage
    repair_prompt_tokens: int = 0
    repair_completion_tokens: int = 0
    repair_total_tokens: int = 0
    repair_model_calls: int = 0
    repair_duration_seconds: float = 0.0

    # Validation stage
    validation_duration_seconds: float = 0.0

    # Totals (properties)
    @property
    def total_workflow_tokens(self) -> int:
        return (self.selection_total_tokens +
                self.regeneration_total_tokens +
                self.repair_total_tokens)

    @property
    def total_workflow_model_calls(self) -> int:
        return (self.selection_model_calls +
                self.regeneration_model_calls +
                self.repair_model_calls)

    @property
    def total_workflow_duration_seconds(self) -> float:
        return (self.selection_duration_seconds +
                self.regeneration_duration_seconds +
                self.repair_duration_seconds +
                self.validation_duration_seconds)
```

**Implementation:** Add fields to `src/benchmark/core/models.py` `TokenUsage` class.

---

## 6. RunRecord Extension

```python
@dataclass(frozen=True)
class RunRecord:
    # ... existing fields ...
    token_usage: TokenUsage  # EXTENDED with per-stage fields
    # New convenience fields for reporting
    patch_sizes: tuple[int, ...] = ()           # lines changed per artifact
    unintended_diffs: tuple[str, ...] = ()      # paths changed outside scope
    unchanged_preserved: int = 0                # count of preserve artifacts byte-identical
```

---

## 7. Fair Comparison Requirements

For any token efficiency claim (H4), **all** must hold:

1. **Same measurement boundary** — both arms use identical stage definitions
2. **Same shared executor** — `hybrid_selective` and `repository_agent` use same `SharedLLMExecutor`
3. **Same validation pipeline** — identical functional/regression/architecture validators
4. **Same repair policy** — max 2 attempts, same error-context injection
5. **Comparable correctness** — statistical non-inferiority on task success (Δ=0.05)
6. **Comparable quality** — no significant difference in regression/architecture violations

**Efficiency results MUST NOT be interpreted independently of correctness and quality outcomes.**

---

## 8. Reporting Requirements

### 8.1 Per-Run JSON Output

```json
{
  "run_id": "...",
  "strategy": "hybrid_selective",
  "token_usage": {
    "selection": {"prompt": 1200, "completion": 200, "total": 1400, "calls": 1, "duration_s": 1.2},
    "regeneration": {"prompt": 5000, "completion": 3000, "total": 8000, "calls": 5, "duration_s": 12.4},
    "repair": {"prompt": 800, "completion": 400, "total": 1200, "calls": 2, "duration_s": 3.1},
    "validation": {"duration_s": 4.5},
    "totals": {"tokens": 10600, "calls": 8, "duration_s": 21.2}
  }
}
```

### 8.2 Aggregate Tables

| Arm | Selection Tokens | Regen Tokens | Repair Tokens | Total Tokens | Model Calls | Total Duration (s) |
|-----|------------------|--------------|---------------|--------------|-------------|-------------------|
| `repository_agent` | ... | ... | ... | ... | ... | ... |
| `hybrid_selective` | ... | ... | ... | ... | ... | ... |

---

## 9. Implementation Checklist

- [ ] Extend `TokenUsage` in `src/benchmark/core/models.py`
- [ ] Extend `RunRecord` with new fields
- [ ] `ImpactStrategy.analyze_impact()` → record selection tokens/calls/duration
- [ ] `SharedLLMExecutor.execute()` → record regeneration tokens/calls/duration
- [ ] `BoundedRepairLoop` → record repair tokens/calls/duration
- [ ] `ValidationPipeline.validate()` → record validation duration
- [ ] `BenchmarkRunner` → aggregate into `RunRecord.token_usage`
- [ ] `CheckpointManager` → persist extended schema
- [ ] `ReportGenerator` → per-stage tables
- [ ] Tests: `test_token_accounting_per_stage.py`

---

## 10. Status

| Item | Status |
|------|--------|
| Stage definitions | FROZEN |
| Field specifications | FROZEN |
| Attribution rules | FROZEN |
| Data model extension | DESIGN |
| Implementation | PENDING (SU-0010) |
| Test coverage | PENDING |

---

**This boundary is frozen for RD-V2. No silent edits to protocol documents.**