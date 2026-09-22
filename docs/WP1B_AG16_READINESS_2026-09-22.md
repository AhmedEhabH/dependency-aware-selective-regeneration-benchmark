# WP-1b AG16 (Agent-Generous) Readiness — 2026-09-22

Status: **PREREGISTERED, NOT RUNNABLE, ZERO PAID CALLS**. This document is a
requirements/evidence handoff for the brain; it is NOT an executable bundle.

## 1. Frozen design (verified from `research/wp1b/wp1b_agent_budget_sensitivity_prereg.json`)

- **Study name:** AG16 / Agent-Generous.
- **Status:** preregistered before any MAIN_297 output (`date: 2026-09-22`,
  `status: PREREGISTERED_BEFORE_MAIN_297_OUTPUTS; EXECUTION REQUIRES AHMED
  DECISION D6`).
- **Sample:** nested MAIN_50 = first 50 IDs of
  `research/wp1b/wp1b_main_297_manifest.json`
  (== `research/wp1a/wp1_main_50_manifest.json`).
- **Changed knobs (exactly two):**
  - `MAX_AGENT_CALLS: 8 -> 16` (calls 1..15 explore, call 16 forced final);
  - `observation_window_chars: 2000 -> 8000` (`MAX_READ_CHARS` stays 12000).
- **Unchanged:** model/provider/route, temperature 0, completion cap 1024,
  tools and arguments, search order and 50-result cap, read budget 30, list cap
  200, editable paths, schemas, rejection rule, G12 echo/counter/named
  rejection/truncation note (numbers adapted to 16), prompts otherwise
  byte-identical.
- **Implementation rule:** a separate parameterized path/module
  (`src/benchmark/strategies/iterative_agent_budget.py`, a parameterized copy);
  `iterative_agent.py` and `repository_tools.py` MUST NOT be modified; a golden
  parity test must show byte-identical prompts and call sequences to the frozen
  class at `(8 calls, 2000 chars)` on scripted stub runs before any paid call.
- **Calibration:** same 3 calibration tasks, NOT scored, gate v3 CG-1..CG-12 +
  the 3c clean criteria; ceiling **$0.80**; D5-style one-amendment rule applies
  to this arm independently.
- **Ceilings (if authorized):** calibration **$0.80**; MAIN_50 AG16 **$12.20**.
- **No factorial extension** (D6b = NO): no `(16,2000)` / `(8,8000)` arms.
- **No MAIN_150 extension** (D6c = NO).
- **Primary analysis:** `D_AG16 = F1_pooled(RM-CSS) − F1_pooled(AG16)` on MAIN_50
  with the frozen P/S analyses, paired bootstrap (10,000, seed 20260920), the
  same 7-row verdict table with margin 0.05; labelled **SENSITIVITY** (MAIN_50
  is underpowered: NI power ≈0.24–0.56); never replaces the MAIN_297 primary.
- **Also:** AG16 − Agent(v3) on MAIN_50 (does budget buy quality?); cost ratios
  RM-CSS/AG16 and Agent(v3)/AG16; a 3-point cost-quality frontier RM-CSS,
  Agent(v3), AG16.
- **Reading:** `ROBUST_TO_AGENT_BUDGET` if the MAIN_297 quality verdict class is
  unchanged when AG16 replaces Agent(v3) on MAIN_50; `BUDGET_SENSITIVE`
  otherwise.
- **Labels:** opened RESERVE-300 proxies only; 786 sealed outcomes untouched.

## 2. Current-code readiness audit (mechanical, 2026-09-22)

| # | Question | Answer | Evidence |
|---|---|---|---|
| 1 | Does a separate AG16 strategy implementation already exist? | **NO** | `src/benchmark/strategies/iterative_agent_budget.py` does not exist; no file named `*ag16*` in `src/`, `scripts/`, `tests/`. |
| 2 | Can the current runner select 16 calls and 8000-char window without changing frozen Agent files? | **NO** | `src/benchmark/wp1b/main_runner.py`: `FROZEN_MAX_AGENT_CALLS = 8`, `FROZEN_OBSERVATION_WINDOW = 2000`; knob check at line ~303 requires `calls == FROZEN_MAX_AGENT_CALLS` (protocol v3), and `iterative_agent.py` hard-codes `MAX_AGENT_CALLS: int = 8` and `OBSERVATION_WINDOW_CHARS: int = 2000`. |
| 3 | Is there a dedicated AG16 paid runner path? | **NO** | `scripts/wp1b_main_run.py` and `src/benchmark/wp1b/main_runner.py` are frozen for protocol v3 (MAIN_297). |
| 4 | Are parity/golden tests present? | **NO** | `tests/unit/test_wp1b_*`, `tests/unit/strategies/test_agent_control_cap.py`, `tests/unit/test_agent_context_hygiene.py`, `tests/integration/test_su0011_iterative_agent.py` — none parameterize AG16 or check `(8,2000)` parity against a budget variant. |
| 5 | Is there a dry-run path? | **YES (for protocol v3 only)** | `scripts/wp1b_main_run.py --kind dry_run` over the MAIN_297 manifest (see `research/wp1b/dry-run-zero-api-2026-09-22/`); not wired for AG16 knobs. |
| 6 | Is calibration gating wired for AG16? | **NO** | `scripts/wp1b_calibration_gate.py` / gate v3 CG-1..CG-12 target protocol v3 (8 calls, 2000 chars). |
| 7 | Are cost accounting / resume / freeze / tag / scoring available for AG16? | **YES for the MAIN runner (protocol v3); AG16-specific wiring absent** | `resilient_backend.py`, spend ledger, resume-safe `main_runner.py`, `scripts/wp1b_freeze_predictions.py`, `scripts/wp1b_score_main.py`, `scripts/wp1b_main_review_card.py`. These can be reused once a parameterized AG16 runner is supplied. |
| 8 | What exact files/symbols need a brain-built bundle? | see §3 below | — |

## 3. Missing implementation pieces (brain handoff)

A brain-built, independently tested bundle must supply:

1. `src/benchmark/strategies/iterative_agent_budget.py` — a parameterized copy of
   `IterativeRepositoryAgentStrategy` with knobs for `MAX_AGENT_CALLS` and
   `OBSERVATION_WINDOW_CHARS` (defaults (8, 2000) to preserve frozen behaviour,
   AG16 uses (16, 8000)). It must reuse `repository_tools.py` unchanged.
2. A golden parity test proving byte-identical prompts and call sequences vs the
   frozen class at `(8 calls, 2000 chars)` on scripted stub runs (zero API).
3. A dry-run path for AG16 knobs over the MAIN_50 manifest (zero API).
4. Calibration gating wired for AG16: same 3 tasks, gate v3 CG-1..CG-12 + 3c
   clean criteria, ceiling $0.80, NOT scored, one-amendment rule for this arm.
5. A parameterized paid runner (modeled on `scripts/wp1b_main_run.py` /
   `src/benchmark/wp1b/main_runner.py`) that reuses the resilient backend, spend
   ledger, resume, instrument-only halting, prediction freeze, and MAIN-mode
   review card — with knobs (16, 8000) and MAIN_50 manifest, ceiling $12.20.
6. AG16 scoring: `D_AG16 = F1_pooled(RM-CSS) − F1_pooled(AG16)` on MAIN_50 with
   the frozen P/S analyses, paired bootstrap (10,000, seed 20260920), margin
   0.05 verdict table, labelled SENSITIVITY (never replaces MAIN_297 primary).

What must remain **byte-unchanged**: `src/benchmark/strategies/iterative_agent.py`,
`src/benchmark/strategies/repository_tools.py`, SIP/RM-CSS predictions,
MAIN_297 frozen results, decision rules v2, all manifests, and the 786 sealed
outcomes.

## 4. Boundary

- Zero paid calls occurred in this mission. The brain bundle must be reviewed
  and tested (golden parity + dry run) before Ahmed authorizes D6.
- Primary AG16 analysis is sensitivity only; it never replaces MAIN_297 primary.
- Same 3 calibration tasks are NOT scored.

## 5. Handoff package

`exports/WP1B_AG16_BRAIN_HANDOFF_2026-09-22/` (README_BRAIN.md, MANIFEST.json,
SHA256SUMS.txt) — requirements/evidence only, not an executable AG16 bundle.
See also `research/wp1b/wp1b_ag16_harness_requirements_2026-09-22.json`.