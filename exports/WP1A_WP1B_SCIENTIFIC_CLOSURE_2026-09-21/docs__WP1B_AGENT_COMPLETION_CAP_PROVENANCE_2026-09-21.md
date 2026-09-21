# WP-1b Agent Completion-Cap Provenance (G2)

**Date:** 2026-09-21
**Status:** BLOCKER G2 — PROVENANCE DOCUMENTED. The 512 vs 1024 selection
cannot be resolved from valid prospective evidence alone; the final choice
requires an authorization decision (proposed amendment prepared in
`docs/WP1B_AGENT_COMPLETION_CAP_AMENDMENT_2026-09-21.md`).

---

## 1. Completion-cap provenance timeline

| # | Experiment / protocol | Provider / model | Agent-control cap | Purpose | Truncation evidence | Commit / source |
|---|------------------------|-------------------|-------------------|---------|---------------------|-----------------|
| 1 | Kaggle Pilot config (`configs/pilot.yaml`) | Kaggle 2×T4, Qwen2.5-Coder-14B | 512 | Control-plane bound for the Kaggle pilot | Pilot dry-run only (no live truncation study) | `a4606a5` (D13 B2, 2026-09-03) |
| 2 | Code default + V11 constant (`src/benchmark/strategies/iterative_agent.py`) | — | 512 default; `V11_AGENT_CONTROL_MAX_COMPLETION_TOKENS = 1024` | "the agent only returns small structured JSON, so a full 4096-cap here would let a runaway control loop burn the whole workflow budget before any source edit happens" | `tests/unit/strategies/test_agent_control_cap.py` asserts V11 == 1024 | `37fa31c` (2026-09-06) |
| 3 | `scientific-wip-impactplan-v1.1` microstudy (`configs/scientific_microstudy_todo.yaml` `agent_control_completion_cap: 1024`) | OpenRouter/DeepInfra, `qwen/qwen3-coder` | 1024 | 30-run Todo selection+E2E microstudy | 30/30 records cap=1024; 0 control-plane truncation messages (recomputed, see section 2) | `28a00e9` (source), `exp-20260906-v11` |
| 4 | `docs/PROTOCOL_VERSION.md` v1.1 amendment | OpenRouter/DeepInfra, `qwen/qwen3-coder` | Agent control 1024 (ImpactPlan 4096, PatchEnvelope 8192) | frozen scientific execution amendment | — | 2026-09-06 |
| 5 | WP-1a frozen agent protocol (`research/wp1a/wp1a_frozen_agent_protocol.json`) | OpenRouter/DeepInfra, `qwen/qwen3-coder` | 512 | future selection-only comparison; note: "WP-1b should use the frozen 512 control cap; any cap change requires a protocol amendment" | — | `c53d918` (2026-09-21) |
| 6 | WP-1a budget model (`research/wp1a/wp1a_budget_model.json`) | OpenRouter/DeepInfra, `qwen/qwen3-coder` | 512 | cost projection | — | `c53d918` (2026-09-21) |

## 2. Recomputed historical truncation evidence (from raw records)

Source: `reports/scientific_microstudy_v11/run_records.jsonl`
(SHA-256 `fadc6d63846046083d6c3737968a174a67531b50db88eb87f80250cecd317435`),
30 records, all with `model_metadata.agent_control_max_completion_tokens =
"1024"`.

- `finish_reason=length` control-truncation messages: **0 / 30** (message scan
  of `failure_details` for
  `"finish_reason=length: iterative agent control response truncated at cap"`).
- `malformed_json` control errors: **0**.
- `no_paths_selected` errors: **0**.
- `no_remaining_agent_calls` errors: **0**.
- `revision failed to select paths` errors: **15**.
- Records reaching 8 selection calls: **15**.
- Selection-phase completion tokens (aggregate over a run's control calls):
  n=30, min 0, max 3513, mean 1589.1. Aggregate totals imply small typical
  per-call responses (~200 tokens mean), but a per-call finish_reason was not
  persisted by the v1.1 run schema, so per-call cap-hit counts cannot be
  reconstructed from these records.

Machine-readable: `artifacts/wp1b_completion_cap_truncation_evidence.json`.

## 3. Interpretation

- **512 provenance:** the 512 value originated as the Kaggle pilot control-plane
  cap (D13 B2) and became the code default with an operational rationale
  (bounded JSON control responses; prevent a runaway control loop burning the
  workflow budget). It was then carried into the WP-1a freeze. There is NO
  WP-1b-specific prospective scientific justification for 512 over 1024; it is
  pilot-derived.
- **1024 provenance:** 1024 is the value actually used in the closest prior real
  scientific run of this agent (v1.1, OpenRouter/DeepInfra, qwen/qwen3-coder).
  In that run zero control-plane truncations occurred. The v1.1 amendment
  (`PROTOCOL_VERSION.md`) documents Agent control = 1024.
- **Instrument-harm risk:** the WP-1b agent arm runs on Saleor tasks with larger
  repositories and longer `editable_paths` lists. The forced-final answer
  (`selected_paths` + `rationale`) must fit in the cap. A 512 cap risks
  truncating the agent arm's final answer, producing instrument-failure EMPTY
  predictions that would lower the agent arm's F1 for an instrumental reason,
  not a method reason (mission section 28). The v1.1 Todo evidence (max control
  responses under 1024) does not settle the Saleor case.

## 4. Status / decision required

- The choice between 512 and 1024 cannot be resolved from valid prospective
  evidence alone: both values have provenance; neither has a WP-1b-specific
  frozen scientific justification that governs the other.
- Per the mission contract: **STOP BEFORE PAID WP-1b** while this is
  unresolved. Do NOT silently choose a value, and do NOT choose whichever makes
  the agent perform better.
- A proposed prospective amendment (512 → 1024) with evidence, reason,
  affected experiments, and falsifiers is prepared in
  `docs/WP1B_AGENT_COMPLETION_CAP_AMENDMENT_2026-09-21.md`. It becomes effective
  ONLY with explicit authorization.
- Regardless of the final cap, the WP-1b protocol now instruments truncation
  and cap-hit metrics as first-class telemetry (mission section 10; see
  `docs/WP1B_AGENT_LOOP_TERMINATION_SEMANTICS_2026-09-21.md` and
  `src/benchmark/wp1b/telemetry.py`).

## 5. Falsifiers

- This provenance is wrong if an authoritative frozen artifact predating the
  WP-1a freeze defines a WP-1b-specific justification for 512 that this audit
  missed (then 512 stands on that justification).
- The amendment proposal is wrong if the v1.1 run used a different agent-cap
  than recorded in its run records, or if the WP-1b Saleor control responses
  are shown to fit comfortably within 512 without truncation under the frozen
  prompt/schema.