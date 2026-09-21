# WP-1b Agent Completion-Cap — Proposed Prospective Amendment (G2)

**Date:** 2026-09-21
**Status:** PROPOSED / NOT EFFECTIVE. This is a prospective preregistration
created BEFORE any WP-1b main result. It becomes effective ONLY upon explicit
Ahmed authorization. Paid WP-1b remains blocked until either this amendment is
approved or 512 is confirmed.

---

## Amendment ID

`WP1B_G2_COMPLETION_CAP_2026_09_21`

## Date

2026-09-21 (created before any WP-1b calibration/main result; zero WP-1b
outcomes observed)

## Pre-result / post-result status

PRE-RESULT. No WP-1b prediction, scoring, or outcome has been produced. The
amendment is not outcome-driven.

## Reason

The WP-1a freeze carried the pilot-derived 512 cap into the WP-1b selection-only
comparison without a WP-1b-specific prospective scientific justification.
The closest prior real scientific run of this agent (v1.1,
`qwen/qwen3-coder` @ OpenRouter/DeepInfra) used **1024** and recorded **zero**
control-plane truncations across 30 runs. The WP-1b agent arm will run on
larger Saleor tasks with longer `editable_paths`; the forced-final answer
(`selected_paths` + `rationale`) must fit inside the cap or the agent arm
suffers instrument-failure EMPTY predictions that would unfairly lower its F1
(instrument finding, not method finding). 512 leaves no demonstrated headroom
for that final answer on Saleor tasks.

## Old value

`agent_control_max_completion_tokens = 512`
(sources: `research/wp1a/wp1a_frozen_agent_protocol.json`,
`research/wp1a/wp1a_budget_model.json`, `configs/pilot.yaml`).

## Proposed new value

`agent_control_max_completion_tokens = 1024`
(matching the v1.1 scientific-run value; still far below the source-edit
4096/8192 caps, preserving the "bounded control plane" property that motivated
the cap).

## Evidence

- v1.1 microstudy run records (`reports/scientific_microstudy_v11/run_records.jsonl`,
  SHA-256 `fadc6d63846046083d6c3737968a174a67531b50db88eb87f80250cecd317435`):
  30/30 records cap=1024; **0** control-truncation messages; aggregate
  selection completion tokens max 3513 (mean 1589) across up to 8 control calls.
- `docs/PROTOCOL_VERSION.md` v1.1 amendment: "Agent control 1024".
- `configs/scientific_microstudy_todo.yaml`: `agent_control_completion_cap: 1024`.
- `tests/unit/strategies/test_agent_control_cap.py`: the codebase explicitly
  preserves `V11_AGENT_CONTROL_MAX_COMPLETION_TOKENS == 1024` as the frozen
  v1.1 value.
- Full provenance timeline: `docs/WP1B_AGENT_COMPLETION_CAP_PROVENANCE_2026-09-21.md`.

## Affected experiments

- WP-1b Calibration-3 (3 tasks) and WP-1b Main-50 repository-agent arm.
- SIP and RM-CSS arms are unaffected (stored predictions; no generative call).
- No other experiment is affected: the v1.1 experiment already used 1024; the
  Kaggle pilot profile keeps its own 512 value in `configs/pilot.yaml` unless a
  separate decision changes it.

## Why this is prospective rather than outcome-driven

The amendment is created before any WP-1b calibration or main inference, and
before any WP-1b F1 delta is known. It is justified solely by provenance (the
v1.1 scientific value), truncation evidence (zero truncations at 1024), and the
a-priori instrument-harm risk of 512 on large Saleor final answers.

## What remains unchanged

- Model identity, provider/route, temperature, prompts, tools, schemas,
  MAX_AGENT_CALLS=8, forced-final call-8 semantics, sample membership, scorer,
  bootstrap, failure semantics, EMPTY semantics, budget guard, calibration
  gate, all other scientific knobs (see `docs/WP1B_KNOB_REGISTRY_2026-09-21.md`).
- SIP and RM-CSS predictions, thresholds, and frozen artifacts.
- The 786 unread Saleor RESERVE outcomes remain sealed.

## Scientific consequence

If approved, the repository-agent arm's control-plane responses are bounded at
1024 completion tokens instead of 512. Truncation telemetry is instrumented in
both cases, so cap-hit / truncation rates remain measurable and reported as
first-class metrics; any residual truncation is an instrument finding, not a
method finding.

## Reversibility

Fully reversible before WP-1b inference: revert the frozen protocol value to
512 with a single documented amendment. After WP-1b, the value is immutable for
that run (changing it mid-run would invalidate comparability).

## Falsifiers

- This amendment is wrong if the WP-1b Saleor control responses are
  demonstrated (under the frozen prompt/schema) to fit within 512 without
  truncation AND 512 is confirmed as scientifically adequate by the
  supervisor.
- It is wrong if the v1.1 run records are shown to be inapplicable (different
  prompt/schema/population) to the WP-1b comparison such that 1024 carries no
  evidentiary weight.
- It is wrong if adopting 1024 increases the risk of the agent arm burning
  workflow budget in a way that changes which outputs are accepted (no such
  mechanism is known, but any such effect would invalidate it).

## Authorizing evidence required

An explicit Ahmed/supervisor instruction approving `WP1B_G2_COMPLETION_CAP_2026_09_21`,
recorded in `DECISIONS.md`, before the first WP-1b paid call.