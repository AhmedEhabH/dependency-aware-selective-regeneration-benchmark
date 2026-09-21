# WP-1b Agent-Loop Termination Semantics (G3)

**Date:** 2026-09-21
**Status:** DETERMINED FROM CODE (`src/benchmark/strategies/iterative_agent.py`)
and frozen protocol (`research/wp1a/wp1a_frozen_agent_protocol.json`,
`research/wp1a/wp1a_failure_semantics.json`). The code is the authoritative
state machine for the WP-1b selection-only arm; the frozen protocol documents
the same semantics. No contradiction between code and protocol was found;
the only gap is telemetry classification, now closed by additive
instrumentation (see section 6).

---

## 1. State machine (selection-only `analyze_impact`)

Constants: `MAX_AGENT_CALLS = 8`, control cap = frozen agent-control cap
(default 512; G2 under review). `begin_run` sets `remaining_agent_calls = 8`.

Loop: while `remaining_agent_calls > 0` and completion allowance `> 0`:

```
FOR each control call c in 1..8:
  remaining_agent_calls -= 1
  IF remaining_agent_calls == 1 BEFORE the call:          # call 8
      force_final = True  (schema = AGENT_FINAL_SCHEMA + control message
                           "This is call 8, the reserved final call. You MUST
                           return action=final now")
  ELSE:
      force_final = False (schema = AGENT_ACTION_SCHEMA)

  response = backend.generate_structured(...)

  IF finish_reason == "length":    -> truncation
      mark _last_control_truncation = True; BREAK
  IF workflow deadline guard false (pre or post call):
      mark model_call_budget_exhausted; raise ModelCallBudgetExhaustedError
      -> caught -> BREAK

  parse response text as single JSON object
  IF parse fails (malformed):
      _control_malformed_count += 1
      append "[error] Invalid JSON response"
      IF remaining_agent_calls <= 0: BREAK  ELSE CONTINUE
  ELSE action_name = action["action"]

  IF action_name == "final":
      validate selected_paths:
        - must be a list          -> else error, retry/break
        - must be non-empty       -> else error, retry/break
        - every item a string     -> else error, retry/break
        - must be unique          -> else error, retry/break
        - must be a subset of the editable universe
                                   -> else error, retry/break
      (each validation failure: _control_schema_invalid_count += 1,
       _last_control_error = "schema_invalid"; IF remaining<=0 BREAK ELSE CONTINUE)
      IF valid:
          selected_paths = raw_paths; _valid_final_count += 1; BREAK  # ACCEPT
  ELIF action_name in (list_files, read_file, search_text):
      IF repeated identical request: append control warning; CONTINUE
      ELSE: invoke tool; append "[result] <tool>: <output>"; CONTINUE
  ELSE:
      append "[error] Unknown action"; IF remaining<=0 BREAK ELSE CONTINUE
END FOR

IF selected_paths non-empty: return regenerated-set prediction (valid final)
ELSE: return EMPTY prediction (fail-closed) with empty_reason classified as:
      truncation | infrastructure | parser_failure | round_cap
```

## 2. Answers to the ten contract questions

1. **Calls 1–7:** explore. The agent may call tools (`list_files`,
   `read_file`, `search_text`) or submit `final` early. A valid early `final`
   is accepted (loop stops).
2. **Call 8:** the reserved final call. `force_final=True`: the schema becomes
   `AGENT_FINAL_SCHEMA` (only `action=final` allowed) and a control instruction
   forces `action=final`.
3. **Is call 8 the final allowed call?** Yes. `remaining_agent_calls` is 1
   before call 8; after it, 0. The loop cannot make a 9th call.
4. **Call 8 valid final → accepted?** Yes. If `selected_paths` passes all
   validation, the prediction is accepted and returned.
5. **Call 8 `finish_reason=length`:** the response is truncated at the cap;
   the loop breaks; if no paths selected → EMPTY prediction with
   `empty_reason = "truncation"` and error
   `"finish_reason=length: iterative agent control response truncated at cap
   <cap>"`.
6. **Call 8 malformed structured output:** `"[error] Invalid JSON response"`
   is appended; `remaining_agent_calls <= 0` → break → EMPTY with
   `empty_reason = "parser_failure"` (new classification; previously the
   generic message `"no paths selected after exploration"`).
7. **No final by the end of call 8:** the next loop iteration calls
   `_generate_agent_response`, which raises `AgentCallsExhaustedError`
   (`remaining <= 0`) → EMPTY with `empty_reason = "round_cap"` and error
   `"iterative_agent: no remaining agent calls"`.
8. **Prediction collected before the cap survives?** Yes. A valid `final`
   breaks the loop immediately with `selected_paths` retained; any later
   exhaustion/truncation cannot overwrite it.
9. **Which condition produces EMPTY:** no valid `selected_paths` by the time
   the loop ends (truncation break, deadline break, allowance exhaustion,
   parser/schema failure on the last call, or round-cap exhaustion).
10. **Failure logging:** per-run errors are recorded in
    `ImpactPrediction.errors` (tuple). Truncation and round-cap have distinct
    messages; parser/schema failures on the final call previously collapsed
    into `"no paths selected after exploration"`. The new additive telemetry
    exposes `selection_empty_reason` (`truncation | round_cap | parser_failure
    | infrastructure | none`), `selection_truncation_count`,
    `selection_malformed_count`, `selection_schema_invalid_count`,
    `selection_valid_final_count`, and
    `selection_finish_reason_distribution` so every EMPTY is classified and
    persisted per task (mission section 10).

## 3. Precedence

```
IF finish_reason == length:                        -> EMPTY (truncation)
ELIF workflow deadline exhausted:                  -> EMPTY (infrastructure)
ELIF malformed JSON or schema-invalid final on the
     last allowed call:                            -> EMPTY (parser_failure)
ELIF remaining agent calls exhausted without final -> EMPTY (round_cap)
ELSE (no EMPTY): return valid prediction
```

## 4. Final-answer schema order (mission section 11)

[VERIFIED] The emitted final schema is `AGENT_FINAL_SCHEMA`:
`{"action": {"const": "final"}, "selected_paths": {...}, "rationale": {...},
"requires_iteration": {...}}`, `required: ["action", "selected_paths",
"rationale"]`, `additionalProperties: false`. The control message on call 8
instructs: "You MUST return action=final now; no tool action is permitted."
The initial prompt requires: "selected_paths must be a non-empty subset of the
editable paths."

[VERIFIED] No prompt/schema orders a large free-form `rationale` BEFORE
`selected_paths`; both are required fields, and `selected_paths` is the
scientifically essential field. The schema does not encourage lengthy free-form
text ahead of the selection.

[INFERRED] Residual risk is low but not zero: `rationale` is required and
free-form; on very large Saleor tasks a verbose rationale could in principle
compete with `selected_paths` for completion tokens near the cap. This is one
motivation for the G2 cap decision (512 vs 1024) and for first-class
truncation telemetry. No schema/parser change was made.

## 5. Transport retry semantics

[VERIFIED] Transport retries are implemented inside the LLM backend
(`src/benchmark/llm/openrouter_backend.py`, `max_transient_retries`, default
1), NOT in the strategy. A backend-internal retry does NOT increment the
strategy's `model_call_count` or consume an additional scientific call budget
(one strategy-level call per returned response). Covered by
`tests/unit/test_wp1b_loop_termination.py`.

[VERIFIED] Gap vs frozen protocol: `research/wp1a/wp1a_failure_semantics.json`
states "max 3 byte-identical retries (SIP precedent)". The current backend
default is `max_transient_retries = 1`. This is an OPERATIONAL knob (transport
retry), but the WP-1b execution MUST configure/confirm
`max_transient_retries = 3` (or a documented equivalent) so the executed
protocol matches the frozen rule. Recorded as a finding, not silently fixed.

## 6. Instrumentation added (behavior-preserving)

Additive telemetry in `IterativeRepositoryAgentStrategy` and the new
`src/benchmark/wp1b/telemetry.py` schema. No selection behavior changed.
See `tests/unit/test_wp1b_loop_termination.py` and
`tests/unit/test_wp1b_truncation_telemetry.py`.

## 7. Falsifiers

- This description is wrong if the actual code path differs from the state
  machine above (re-audit by diffing against `iterative_agent.py`).
- The parser_failure classification is wrong if a malformed final answer is
  ever classified as something other than `parser_failure`.