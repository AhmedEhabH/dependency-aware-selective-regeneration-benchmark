# WP-1b Agent Baseline Disclosure — 2026-09-21

**Status:** FROZEN (G10 disclosure). The WP-1b repository-agent arm is a
**budget-bounded iterative repository agent**: 8 calls, 1,024-token control
completion cap (G2 amendment, authority D3), 2,000-char observation window, no
paging. This is a frozen v1.1 design choice and is NOT changed by this
disclosure; the disclosure makes it measurable and explicit.

## 1. The agent as implemented

- Loop: `IterativeRepositoryAgentStrategy` (`src/benchmark/strategies/iterative_agent.py`),
  `MAX_AGENT_CALLS = 8`; calls 1–7 explore, call 8 is forced final.
- Completion cap: `agent_control_max_completion_tokens = 1024` (amendment
  `WP1B_G2_COMPLETION_CAP_2026_09_21`; see `DECISIONS.md`).
- Observation window: each tool result is truncated to the first **2,000
  characters** (`iterative_agent.py`, `result.output[:2000]`). No paging: the
  agent never requests page 2 of a result.
- For a Saleor file this window is roughly the first 50–60 lines.

## 2. Why the observation window matters

The agent sees at most the first 2,000 characters of each tool result. Any
relevant evidence later in the file is invisible to the selection decision. This
is an instrument property shared by every WP-1b agent task (identical window
for all tasks and all arms' agent executions), so it does not bias the
RM-CSS-vs-Agent comparison, but it bounds what the agent can know.

## 3. Made measurable and disclosed (G10)

Additive, behavior-preserving telemetry (proven by the stub-backend golden test
`tests/unit/test_wp1b_agent_telemetry_golden.py`):

- **Per-call sidecar JSONL** (`src/benchmark/wp1b/telemetry.py`
  `call_sidecar_records`): `task_id, call_index, force_final, action, path,
  query, tool_output_chars_raw, tool_output_chars_shown, observation_truncated,
  finish_reason, prompt_tokens, completion_tokens, usd, latency_s,
  raw_response_text, raw_response_sha256`.
- **Per-task additions** (`strategy_telemetry`): `observation_truncation_rate`
  (fraction of tool-output characters cut by the 2000-char window),
  `paths_read` (targets of `read_file`), `paths_surfaced` (paths appearing in
  `search_text` / `list_files` output), raw/shown tool-output char totals.
- The observation window itself is NOT changed; only its effects are now
  measured and reported.

## 4. Threats to validity

- **Observation truncation:** a large Saleor file may have relevant evidence
  beyond the first 2,000 characters; `observation_truncation_rate` reports how
  much material was cut, so an instrument finding can be separated from a
  method finding.
- **Budget bound:** the agent is bounded at 8 calls and 1,024 completion
  tokens per call; `finish_reason == "length"` at ANY call breaks the loop
  (this is exactly why G2 moved 512 → 1024; see `DECISIONS.md`).
- **No paging:** the agent cannot paginate; `paths_surfaced` reflects only what
  the bounded output showed.

## 5. Context (not comparable)

The P5 LocAgent run (`$9.93 for 10 tasks`) is cited as context only: different
exposed population, different protocol, not comparable to the WP-1b comparison.