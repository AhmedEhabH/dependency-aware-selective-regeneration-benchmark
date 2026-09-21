# START HERE — Current Research (2026-09-21b)

This file is the entry map. Read it first, then open the referenced documents.
**Terminology:** SIP = Sparse Impact Plan (baseline); RM-CSS =
Repository-Memory Calibrated Set Selection (= SIP + Qwen dense ranking +
parent-only Repository Memory + calibrated ADD/KEEP/DROP). See
`docs/GLOSSARY.md`.

## What this research is

**Question.** Given a real GitHub issue and the repository state at the issue's
parent commit, which files would a developer change? We evaluate the selected
file set against the observed change-set (the actual diff) as an evaluation
proxy. Functional correctness / preservation are deferred until downstream
regeneration.

**Phase.** `Repository change localization / impact selection` — **method
selection CLOSED** (`IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`).

## Current position (one paragraph)

WP-1b Calibration-3 ran with protocol v2 (cap 1024) and **passed the frozen v1
gate (CG-1..CG-9, $0.081142, 24 calls, 0 cap hits, 0 EMPTY)** — but the agent's
tools were defective: 0 of 3 tasks read any file
(`GATE_V1_PASS / INSTRUMENT_INVALID`). The tool-budget defect is now fixed
(D2, amendment `WP1B_G11_TOOL_BUDGET_2026_09_21`): `search_text` no longer
consumes the 30-file distinct-file budget; `read_file` keeps
`MAX_DISTINCT_FILES = 30`. Calibration gate v2 (CG-10 instrument-validity +
CG-11 read-validity) is written and **FAILS on the old Calibration-3 records**
(RED evidence). **Calibration-3b (same 3 tasks, not scored, ceiling $0.25) is
authorized (D4 = YES).** MAIN_297 and the variance substudy are **NOT**
authorized (D5/D7 = NO) until Ahmed reviews the Calibration-3b STOP report.

<!-- LIVE_STATUS:BEGIN -->

## LIVE STATUS — single current-state source of truth

**Position:** WP-1b Calibration-3 passed its frozen v1 gate (CG-1..CG-9) but the agent's tools were defective: 0 of 3 tasks read any file (INSTRUMENT_INVALID). The tool-budget defect is now fixed (D2: search_text no longer consumes the 30-file read budget), gate v2 (CG-10/CG-11) is written and FAILS on the old Calibration-3 records, and Calibration-3b is authorized (D4 = YES, ceiling $0.25). MAIN_297 remains blocked until a clean Calibration-3b and a separate D7 decision.

**Research pipeline:**

| Step | Status | Note |
| :---|:---|:---|
| Localization method selection | CLOSED | RM-CSS frozen; Saleor-300 PASS (+0.0921 F1) |
| WP-0 leakage fix (G7) | DONE | ArtifactUniverse built from the parent repository |
| WP-1a preparation | DONE | zero API; frozen predictions, manifests, agent protocol |
| WP-1b preflight freeze | DONE | G1 Δ=0.05 · G2 cap 1024 · n=297 · budget v2 · rules v2 |
| WP-1b Calibration-3 | DEFECT | v1 gate PASS, $0.081, 24 calls — 0 successful reads; INSTRUMENT_INVALID |
| Tool-budget fix + gate v2 | DONE | D2: search_text does not consume the 30-file budget; CG-10/CG-11 written; RED on Calibration-3 |
| WP-1b Calibration-3b | NEXT | authorized (D4 YES), ceiling $0.25, paired instrument revalidation of D2 |
| WP-1b MAIN_297 + variance 15×3 | BLOCKED | needs a clean 3b and D7 = YES |
| WP-2 shared E2E instrument | NOT STARTED | same generator/validator/repair for every arm |
| E2E-G6 F2P/P2P oracle | NOT STARTED | fail-to-pass + pass-to-pass tests per task |
| E2E Smoke → Pilot → Research Run | NOT STARTED | staged; each stage can stop the run |

**LLM-call accounting:**

| Workflow | Calls | Note |
| :---|:---|:---|
| SIP on Saleor-300 | 300 coder calls (1/task) | 315 HTTP attempts incl. retries · 5.09 M tokens · $1.593 |
| RM-CSS on top of SIP | 0 extra coder calls | local logistic regression + repository memory |
| Qwen embeddings (RM-CSS) | 33 batched calls | 2,076 file units + 299 queries · $0.026 |
| WP-1b Calibration-3 agent | 24 calls (8/task) | $0.081 · 7 of 24 were rejected repeats · 0 successful reads (INSTRUMENT_INVALID) |
| WP-1b Calibration-3b agent (authorized) | ≤ 24 calls | 3 × 8, ceiling $0.25, paired revalidation of the D2 fix |
| MAIN_297 agent (ceiling) | ≤ 2,376 calls | 297 × 8; not authorized |
| Variance substudy (ceiling) | ≤ 360 calls | 15 tasks × 3 runs × 8 |
| E2E generation + repair | not frozen yet | defined by WP-2 |

**Authorized / not authorized:**

| Item | Status | Note |
| :---|:---|:---|
| Calibration-3b (Phase C) | AUTHORIZED | D4 = YES, ceiling $0.25, paired revalidation of the D2 tool fix |
| MAIN_297 + variance 15×3 | NOT AUTHORIZED | requires D7 = YES after Ahmed reviews Calibration-3b |
| 786 Saleor RESERVE outcomes | SEALED | never opened/read/scored/sampled |
| Calibration-3 / Calibration-3b F1 claims | NOT PERMITTED | instrument checks only; no labels loaded or scored |

**Next action:** Phase C (authorized, ceiling $0.25): Calibration-3b with the D2 fix, same 3 tasks, not scored. Gate v2 (CG-1..CG-11) must pass; report per-task tool telemetry. STOP after 3b regardless of outcome.

**End-to-end status:** WP-2 has **not started**; E2E-G6 F2P/P2P oracle has **not started**; **no** E2E Smoke, Pilot or Research Run exists yet.

*Source: `docs/LIVE_STATUS.json` (schema `live_status_v1`), rendered by `scripts/render_live_status.py`. As of 2026-09-21 21:30 (Africa/Cairo).*
<!-- LIVE_STATUS:END -->

## Key facts

- **Tool-budget defect + fix (D2):**
  `docs/WP1B_AGENT_TOOL_BUDGET_DEFECT_2026-09-21.md`,
  `docs/WP1B_KNOB_REGISTRY_2026-09-21_v2.md`.
- **Mechanical call audit:** `scripts/wp1b_sidecar_tool_audit.py` →
  `research/wp1b/calibration-3-2026-09-21/wp1b_tool_audit.json`
  (3 final / 5 tool-ok / 9 limit errors / 7 rejected repeats / 0 reads).
- **Gate v2:** `artifacts/wp1b_calibration_gate_v2.json` (CG-1..CG-11),
  evaluator `scripts/wp1b_calibration_gate.py --gate v2`; RED result
  `research/wp1b/calibration-3-2026-09-21/wp1b_calibration_gate_v2_result.json`
  (CG-10 FAIL).
- **Frozen margin (G1):** `research/wp1b/wp1b_ni_margin_frozen.json`,
  `docs/WP1B_NI_MARGIN_FROZEN_2026-09-21.md`.
- **Completion cap 1024 (G2):** `research/wp1b/wp1b_frozen_agent_protocol_v2.json`.
- **Budget v2:** `research/wp1b/wp1b_budget_model_v2.json`.
- **Sample-size amendment:** `research/wp1b/wp1b_main_297_manifest.json` (n=297).
- **Decision rules v2:** `research/wp1b/wp1b_decision_rules_v2.json`.
- **Agent telemetry:** `src/benchmark/wp1b/telemetry.py` (A4 per-call
  `tool_ok`/`tool_error` + search telemetry).

## Authorized / not authorized

- **AUTHORIZED now (D4 YES):** Calibration-3b (3 tasks, protocol v2 cap 1024,
  provider/pricing frozen, USD guard ≤ $0.25). Only after every Phase A/B
  acceptance criterion passes, zero-API work is committed/integrated, the
  tool-fix tag is pushed/verified, the working tree is clean, the scientific
  model/provider/route and 1024 cap match the frozen protocol, and spend before
  Phase C is exactly $0.00.
- **NOT authorized (D5/D7 NO):** MAIN_297, MAIN_50, MAIN_150, the variance
  substudy, and any other paid main experiment. MAIN_297 requires a new
  explicit Ahmed authorization after he reviews the Calibration-3b STOP report.
- **Never:** read/open/score/sample the 786 unread Saleor RESERVE outcomes.

## Where to go next

1. `docs/WP1B_TOOLFIX_LIVESTATUS_STOP_REPORT_2026-09-21.md` (this mission's STOP report).
2. `DECISIONS.md` (D1..D6 + `WP1B_CALIBRATION_3_RECLASSIFIED`).
3. `PROGRESS.md` (execution source of truth).