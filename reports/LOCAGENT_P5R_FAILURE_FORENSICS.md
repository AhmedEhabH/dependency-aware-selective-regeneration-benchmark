# LocAgent P5R — Failure Forensics (Block B1, ZERO API)

**Date:** 2026-09-16 evening
**Purpose:** determine whether the original P5 5/10 non-usable outcomes were
primarily caused by operational limits (timeout / context capacity) or by the
framework behavior. P5 is immutable historical evidence; this is a pre-flight
forensic read of the persisted P5 evidence (zero new calls).

**Source evidence:**
- `research/locagent-p5b/out_c/loc_outputs.jsonl`
- `research/locagent-p5b/out_c/loc_trajs.jsonl`
- `research/locagent-p5b/out_c/localize.log`
- `research/locagent-p5b/out_c/usage_ledger_final.jsonl` (authoritative 402-call ledger)
- `research/locagent-p5b/out_c/wrapper_manifest.json`, `args.json`
- `reports/LOCAGENT_P5C_HELDOUT_RUN.md`

**Frozen P5 config (from args.json):** model `openrouter/qwen/qwen3-coder`,
ranking MRR, `max_attempt_num=1`, `num_samples=1`, `num_processes=1`,
timeout 900 s, `rerun_empty_location=false`, function calling on.

---

## 1. Per-case forensic record (the 5 non-usable tasks)

| Case | Failure type | Wall time (sum latency) | Calls | Prompt tokens | Context limit (route) | Last state | Valid partial ranking? | "empty" meaning |
|---|---|---:|---:|---:|---:|---|---|---|
| 4307e1b8c2e2 | timeout | 844.1 s | 43 | 5,358,303 | 262,144 (OpenRouter) | reconstruction loop | no | fail-closed empty (timeout) |
| fdda30c271f0 | timeout | 486.2 s | 7 | 265,914 | 262,144 | `execution flow reconstruction exceeded timeout. Terminating.` (log) | no | fail-closed empty (timeout) |
| 66c70394c9e1 | context-length | 825.1 s | 71 | 7,719,291 | 262,144 | `BadRequestError: maximum context length is 262144` (Venice upstream) | no | fail-closed empty (context) |
| 9e33db4f4660 | completed-but-empty | 130.7 s | 25 | 1,451,982 | 262,144 | `localizing ... succeed, process multiple loc outputs`; empty `found_files`; raw_output_loc has partial prose only | no | structurally-valid empty answer (framework produced no parseable file set) |
| b39799f9fc1c | completed-but-empty | 78.1 s | 21 | 1,011,762 | 262,144 | `localizing ... succeed`; empty `found_files`; raw_output_loc describes analysis but no code block | no | structurally-valid empty answer |

## 2. Forensic diagnosis

- **The two timeout cases (4307e1b8c2e2, fdda30c271f0):** both hit the
  workflow-deadline/timeout mechanism (900 s). Case 4307e1b8c2e2 consumed 43
  calls / 5.36M prompt tokens before termination; fdda30c271f0 only 7 calls /
  0.27M tokens yet still timed out — indicating the deadline was reached during
  a single long reconstruction/verification phase, not simply "too many calls".
  These are plausibly OPERATIONAL (timeout) artifacts; raising the timeout to
  1800 s (P5R-1) is the test.
- **The context-length case (66c70394c9e1):** 71 calls / 7.72M prompt tokens;
  the agent accumulated context toward the 262,144-token ceiling and the
  OpenRouter/Venice upstream rejected a call with `maximum context length is
  262144`. This is OPERATIONAL (context capacity) — P5R-1 raises the configured
  context ceiling to the same route's maximum if supported.
- **The two completed-but-empty cases (9e33db4f4660, b39799f9fc1c):** the
  upstream flow logged "succeed" but yielded no parseable file set. Both are
  structurally-valid empty answers (raw_output_loc contains only partial prose,
  no code block / no found_files). These are NOT timeouts and NOT context
  errors; they are most consistent with FRAMEWORK/parser behavior (the agent
  finished but its final answer was not a valid parsed location list), possibly
  combined with the upstream LLM returning prose without a final structured
  ranking. Relaxing timeout/context (P5R-1) is NOT expected to fix these; each
  will be allowed exactly one P5R-1 rerun, and if still empty they are kept as
  genuine non-usable framework outcomes.

## 3. Operational-vs-framework attribution (preliminary, zero API)

- Timeout failures: **2** → operational (testable by timeout relaxation).
- Context-length failure: **1** → operational (testable by context relaxation).
- Completed-but-empty: **2** → framework/system behavior (NOT fixed by
  timeout/context relaxation; each gets one P5R-1 rerun to confirm).

## 4. What this implies for P5R

- P5R-1 relaxes ONLY operational limits (timeout 900→1800 s; context to the
  same route's max), keeping the algorithm / tools / ranking / model family /
  provider route / temperature constant. This can address at most the 3
  operational failures (2 timeout + 1 context).
- The 2 completed-but-empty tasks may remain empty under P5R-1; that is a
  genuine framework finding, not a repair failure.
- No prompt compression, history summarization, tool, ranking, or algorithm
  change is made in P5R-1 (that would be a modified LocAgent variant).
- Do NOT blend P5 successes with P5R rescued runs; any clean full 10-task rerun
  uses ONE frozen P5R-1 configuration for all 10.

## 5. Evening budget constraints (frozen)

- Pilot: <=5 outer executions, <=20M total tokens, <=$6.00; fail-closed.
- Full clean rerun (if triggered): 10 outer executions; overall evening
  LocAgent (pilot + full) <=50M tokens and <=$15.00; only the already-exposed
  original P5 ten tasks; no replacement rerun after a valid/fail-closed outcome.
## 6. P5R-1 pilot outcome (live, 2026-09-16 evening)

Executed 5/5 non-usable tasks under P5R-1 (timeout 1800; all else identical).
**Result: 0 usable.** See eports/LOCAGENT_P5R1_PILOT_REPORT.md.

- 9e33db4f4660 (P5 empty) -> context-length (197,006 input tokens).
- b39799f9fc1c (P5 empty) -> completed-but-empty (unchanged).
- 4307e1b8c2e2 (P5 timeout) -> worker crash (exit code 1).
- fdda30c271f0 (P5 timeout) -> context-length (~315,993 requested).
- 66c70394c9e1 (P5 context) -> upstream hard-coded "Processing time exceeded 15 minutes".

**Critical finding:** the upstream uto_search_main.py enforces its OWN
hard-coded 900 s (15-minute) processing deadline independently of the wrapper
--timeout; raising the wrapper timeout to 1800 did NOT extend the effective
deadline. Context capacity cannot be raised on the same route (262,144 max).
Full clean 10-task P5R-1 rerun NOT triggered (0/5 < 3/5 gate; timeout lever
ineffective; context is a hard route limit). P5 remains immutable; no blended
P5R metric.
