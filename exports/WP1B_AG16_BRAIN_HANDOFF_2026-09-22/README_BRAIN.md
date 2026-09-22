# AG16 (Agent-Generous) Brain Handoff — README for the Brain

> Status: **PREREGISTERED, NOT RUNNABLE**. This package is a
> requirements/evidence handoff for the brain (Ahmed + ChatGPT + Claude).
> It is **NOT** an executable AG16 bundle. Zero paid calls were made to create
> it. OpenCode (DeepSeek V4 Flash) is explicitly forbidden from implementing
> the AG16 runner/scorer from scratch.

## What you (the brain) must implement

Build and independently test an AG16 executable bundle. Minimum pieces:

1. **`src/benchmark/strategies/iterative_agent_budget.py`** — a parameterized
   copy of `IterativeRepositoryAgentStrategy` with knobs `MAX_AGENT_CALLS` and
   `OBSERVATION_WINDOW_CHARS`. Defaults `(8, 2000)` preserve frozen protocol-v3
   behaviour; AG16 uses `(16, 8000)` (calls 1..15 explore, call 16 forced
   final). Reuse `repository_tools.py` unchanged.
2. **Golden parity test (zero API, mandatory, before any paid call):** prove
   byte-identical prompts and call sequences vs the frozen class at
   `(8 calls, 2000 chars)` on scripted stub runs.
3. **Dry-run path (zero API):** run AG16 knobs over the MAIN_50 manifest
   (`research/wp1b/wp1b_main_50_manifest.json`).
4. **Calibration gating:** same 3 calibration tasks as protocol v3, gate v3
   CG-1..CG-12 + 3c clean criteria, ceiling **$0.80**, NOT scored, one-amendment
   rule applies to this arm independently.
5. **Parameterized paid runner** modeled on `scripts/wp1b_main_run.py` +
   `src/benchmark/wp1b/main_runner.py`: resilient backend, spend ledger,
   resume-safe, instrument-only halting, prediction freeze, MAIN-mode review
   card. Knobs `(16, 8000)`, MAIN_50 manifest, ceiling **$12.20**.
6. **AG16 scoring:** `D_AG16 = F1_pooled(RM-CSS) − F1_pooled(AG16)` on MAIN_50,
   frozen P/S analyses, paired bootstrap (10,000, seed 20260920), margin 0.05
   verdict table, labelled **SENSITIVITY** — never replaces the MAIN_297
   primary. Also report AG16 − Agent(v3) on MAIN_50, cost ratios
   RM-CSS/AG16 and Agent(v3)/AG16, and a 3-point cost-quality frontier
   (RM-CSS, Agent(v3), AG16).

## What must remain byte-unchanged

- `src/benchmark/strategies/iterative_agent.py`
- `src/benchmark/strategies/repository_tools.py`
- SIP / RM-CSS predictions; MAIN_297 frozen results; decision rules v2
  (`research/wp1b/wp1b_decision_rules_v2.json`); ALL manifests.
- The 786 sealed Saleor RESERVE outcomes — never accessed.

## Required zero-API tests

- Golden parity `(8, 2000)` between the budget variant and the frozen class.
- Dry-run over MAIN_50 with AG16 knobs (0 model calls, deterministic mocks).
- Calibration gate v3 CG-1..CG-12 re-evaluated on the AG16 calibration records
  (same 3 tasks, not scored).
- Cost ledger / resume / freeze / review-card paths exercised with the new knobs.

## Required dry-run behavior

- Exactly `(16 calls, 8000-char window)`; prompts otherwise byte-identical to
  protocol v3 (G12 numbers adapted 8→16).
- 0 model calls; deterministic; exits cleanly; writes the expected records.

## Paid authorization boundary

- The brain builds and tests the bundle FIRST. Only after golden parity + dry
  run pass may Ahmed authorize D6 for AG16 calibration ($0.80) and MAIN_50
  sensitivity ($12.20).
- AG16 is sensitivity only; it never replaces the MAIN_297 primary. No factorial
  extension (`(16,2000)` / `(8,8000)`), no MAIN_150 extension.

## Contents layout

```
frozen_prereg/         wp1b_agent_budget_sensitivity_prereg.json
frozen_protocol/       wp1b_frozen_agent_protocol_v3.json
frozen_agent_code/     iterative_agent.py, repository_tools.py
runner_cli/            scripts/wp1b_main_run.py
runner_core/           main_runner.py, resilient_backend.py, label_guard.py
freeze_scoring/        wp1b_freeze_predictions.py, wp1b_score_main.py, wp1b_main_review_card.py
calibration/           wp1b_calibration_gate.py, wp1b_calibration_run.py
existing_tests/        the current agent/runner test files (none parameterize AG16)
manifests/             wp1b_main_50_manifest.json
ag16_requirements/     wp1b_ag16_harness_requirements_2026-09-22.json, WP1B_AG16_READINESS_2026-09-22.md
MANIFEST.json          package manifest with per-file SHA-256
SHA256SUMS.txt         per-file SHA-256 (sha256sum format)
```

## Verification

`SHA256SUMS.txt` verifies every packaged file against the source commit. This
package is documentation/evidence only; no code in it runs AG16.