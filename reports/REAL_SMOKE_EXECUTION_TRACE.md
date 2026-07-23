# Real-Smoke Execution Trace Report

**Date:** 2026-07-23  
**Scope:** Full execution path from `seven_arm_benchmark.py` through `KaggleQwenBackend.generate()`  
**Objective:** Determine whether real Qwen inference actually executes during a non-dry-run smoke run.

---

## 1. Entry Point: `seven_arm_benchmark.py`

```
main() -> run_arm() -> pipeline.run_all() -> pipeline.run_scenario() -> runner.run()
```

**Dry-run guard** (`pipeline.py:50`, `pipeline.py:66`):

```python
def run_scenario(self, scenario):
    if self._config.dry_run:
        return self._dry_run_scenario(scenario)
    runner = self._make_runner(scenario)
    return runner.run(scenario)
```

- **Dry-run**: calls `runner.dry_run()` → returns `RunRecord(status=succeeded, duration=0.0)` — **never calls `analyze_impact()`**.
- **Real mode**: calls `runner.run()` → `_run_attempt()` → `strategy.analyze_impact()`.

### Trace evidence (dry-run)

```
Strategy: monolithic  Uses LLM: NO
Strategy: agent       Uses LLM: YES
...
RESULT: arm=agent uses_llm=YES gen_called=False status=succeeded tokens=0/0/0 duration=0.0s
```

`gen_called=False` is **correct** in dry-run — the agent strategy is never invoked.

---

## 2. Runner: `_run_attempt()` (`runner.py:125`)

The core attempt loop:

```python
def _run_attempt(self, scenario, start_time):
    try:
        # ... build snapshot, requirement, artifacts ...
        prediction = self._strategy.analyze_impact(...)

        return RunRecord(
            status=RunStatus.succeeded,   # ALWAYS succeeded
            prediction=prediction,        # errors in prediction are IGNORED
            token_usage=TokenUsage(),     # always defaults to (0,0,0)
            duration_seconds=...,
        )
    except BudgetExhaustedError: ...
    except ModelBackendError as e: return e   # only reached if strategy re-raises
    except ProtocolViolationError: ...
    except BenchmarkError: ...
```

### Critical bugs in `_run_attempt`

| Bug | Location | Impact |
|-----|----------|--------|
| **False-positive success** | Line 158 | Always `RunStatus.succeeded` — never checks `prediction.errors`. A strategy can silently fail and the runner reports SUCCESS. |
| **Token leakage** | Line 157–161 | `token_usage` is never set. `RunRecord.token_usage` defaults to `TokenUsage(0,0,0)`. Even if the backend returns real usage, it is discarded. |
| **Dead `except` clause** | Line 172–173 | `except ModelBackendError` is unreachable for the agent strategy because **the strategy swallows the exception** (see §3). |

---

## 3. Agent Strategy: `RepositoryAgentStrategy` (`agent.py:39`)

```python
def analyze_impact(self, repository, requirement_change, artifact_universe):
    prompt = self._build_prompt(...)
    try:
        _GENERATION_CALLED = True
        response = asyncio.get_event_loop().run_until_complete(
            self._backend.generate(prompt=prompt, ...)
        )
        return self._parse_response(response.text, artifact_universe)
    except Exception as exc:                      # <-- catches EVERYTHING
        return ImpactPrediction(                  # <-- returns error as data, not exception
            errors=(f"agent strategy failed: {exc}",),
        )
```

### What happens on failure (local without torch)

| Step | Trace event | Description |
|------|-------------|-------------|
| 1 | `RUNNER_TRACE: Calling RepositoryAgentStrategy.analyze_impact()` | `_run_attempt` calls `analyze_impact()` |
| 2 | `AGENT_TRACE: Calling backend.generate()` | `_GENERATION_CALLED = True` is set |
| 3 | `BACKEND_CREATED` → `GENERATION_STARTED` → `MODEL_LOADING_STARTED` | `KaggleQwenBackend.generate()` begins |
| 4 | `AGENT_TRACE: backend.generate() raised ModelBackendError: ...` | `_lazy_import()` raises `ModelBackendError` (no torch) — **genuine failure** |
| 5 | `ImpactPrediction(errors=(...))` returned | Agent strategy catches the exception, returns error-as-data |
| 6 | `RUNNER_TRACE: analyze_impact returned generation_was_called=True prediction_errors=1` | Runner sees `ImpactPrediction` with errors but **does not check** |
| 7 | `RunRecord(status=succeeded, token_usage=(0,0,0), ...)` | **False positive**: success reported despite backend failure |

### Key bug in agent strategy

| Bug | Location | Impact |
|-----|----------|--------|
| **Swallows `ModelBackendError`** | `agent.py:57` | `except Exception` catches `ModelBackendError` and wraps it in `ImpactPrediction(errors=...)` instead of re-raising. This prevents the runner's `except ModelBackendError` handler from ever executing. |
| **No token propagation** | `agent.py:56` | `response.token_usage` from `LLMResponse` is **never extracted or forwarded** — the strategy only passes `response.text` to `_parse_response()`, which returns an `ImpactPrediction` with no `token_usage` field. |

---

## 4. Backend: `KaggleQwenBackend.generate()` (`kaggle_qwen_backend.py:47`)

```python
async def generate(self, prompt, temperature=0.0, max_tokens=4096):
    self._ensure_loaded()           # imports torch, loads model
    assert self._model is not None
    # ... tokenize, call model.generate(), decode ...
    return LLMResponse(
        text=output_text,
        token_usage=TokenUsage(prompt_tokens, completion_tokens, total_tokens),
        finish_reason="stop",
    )
```

The backend itself is **correct** — it returns `LLMResponse` with accurate `token_usage`. The issue is that the **caller never uses it**.

---

## 5. Data Model: Token-Usage Gap

```
KaggleQwenBackend.generate()
    ↓
LLMResponse(text=..., token_usage=TokenUsage(p, c, t))
    ↓  (agent.py:52-54  — only response.text is used)
    ↓
ImpactPrediction(decisions=..., errors=...)
    ↑ NO token_usage field in ImpactPrediction
    ↓
RunRecord(status=..., prediction=..., token_usage=TokenUsage(0,0,0))
    ↑ default TokenUsage() — never populated
```

The token‑usage chain is **completely disconnected**. Even if Qwen generates 4,096 tokens successfully on Kaggle, `RunRecord.token_usage` will always be `(0, 0, 0)`.

---

## 6. Local Execution Trace (Real Mode, No torch)

**Command:** `python -c "..."` (direct `BenchmarkPipeline` with `KaggleQwenBackend`, dry_run=False)

```
Loaded 24 scenarios
RUNNER_TRACE: Calling RepositoryAgentStrategy.analyze_impact() scenario=djangocms-cross-007
AGENT_TRACE: Calling backend.generate() via asyncio.run_until_complete
KAGGLE_TRACE: BACKEND_CREATED
KAGGLE_TRACE: GENERATION_STARTED
KAGGLE_TRACE: MODEL_LOADING_STARTED
AGENT_TRACE: backend.generate() raised ModelBackendError:
    KaggleQwenBackend requires torch and transformers.
    These are Kaggle-only dependencies and must not be installed locally.
RUNNER_TRACE: analyze_impact returned generation_was_called=True prediction_errors=1

Result: status=succeeded tokens=0/0/0 duration=0.0940s errors=1
```

**Key finding: `generation_was_called()` = True — the code path DOES reach `backend.generate()`.**  
But the backend fails (no torch locally), the error is swallowed, and `succeeded` is reported.

---

## 7. Expected Kaggle Behaviour

On Kaggle (torch available, Qwen model attached):

1. `run_all()` → `run_scenario()` → `runner.run()` → `_run_attempt()`  
2. `analyze_impact()` called → `_GENERATION_CALLED = True`  
3. `backend.generate()` → `_ensure_loaded()` → model loads → tokens generated  
4. `LLMResponse` returned with real `token_usage`  
5. **`response.token_usage` is discarded** — only `response.text` is parsed  
6. `ImpactPrediction` returned with `decisions` from parsed text  
7. `RunRecord(status=succeeded, token_usage=TokenUsage(0,0,0))`  

**Result: Real Qwen generation would execute, but token usage STILL reports 0/0/0.**  
Duration would show a non-zero value (model loading + inference time).

---

## 8. Root Causes (No Guesses — All Confirmed by Trace)

| # | Bug | Verified By | Confirmed |
|---|-----|-------------|-----------|
| 1 | Agent strategy (`except Exception`) swallows `ModelBackendError` | Trace step 4→5 | Yes |
| 2 | Runner ignores `prediction.errors` → false `succeeded` | Code review of `_run_attempt` lines 156–161 | Yes |
| 3 | Token usage never propagated from `LLMResponse` → `RunRecord` | Model review: `ImpactPrediction` has no `token_usage` field; `RunRecord` defaults to zero | Yes |
| 4 | `except ModelBackendError` in runner is dead code for agent path | Bug #1 prevents it from ever triggering | Yes |

---

## 9. Conclusion

**Real Qwen generation never produces visible token usage in the results.** This is confirmed at two levels:

1. **Locally (no torch)** — `backend.generate()` is reached (`gen_called=True`) but raises `ModelBackendError`. The error is swallowed by the agent strategy. The run is reported as SUCCESS with 0/0/0 tokens — a **false positive**.

2. **On Kaggle (with torch)** — `backend.generate()` would execute successfully, but the returned `token_usage` is discarded by the strategy's `analyze_impact()` return path. The run would still show 0/0/0 tokens — a **silent data loss**.

**The primary actionable finding**: `ImpactPrediction` needs a `token_usage` field, the agent strategy must populate it from `LLMResponse`, and the runner must propagate it to `RunRecord`. Additionally, the agent strategy should not swallow `ModelBackendError` — it should either re-raise it or the runner should check `prediction.errors` and mark the run as failed.

---

*Instrumentation added: `_GENERATION_CALLED` flag in `agent.py`, `_TRACE_EVENTS` in `kaggle_qwen_backend.py`, `RUNNER_TRACE` logging in `runner.py`, `RESULT` logging in `seven_arm_benchmark.py`.*  
*All instrumentation is temporary and will be removed after this report.*
