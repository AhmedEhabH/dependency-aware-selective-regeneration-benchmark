# WP2 execution map M13 -> M16 (task -> subtask -> atomic)

An atomic step advances ONLY when (1) its declared inputs exist and match their hashes/roles, (2) exactly its declared outputs were written, (3) its checks pass, (4) no forbidden pool/file was touched, (5) the controller state records PASS. Otherwise the controller STOPs with the atomic's on_fail token. No AI repair, no alternative path, no fallback. Subtask S advances when its last atomic passes; task T advances when its last subtask passes and its gate token is emitted. Resumable tokens resume the SAME atomic.

## M13 — Pilot design/readiness freeze (zero API)  (EXECUTABLE_NOW)

close Smoke accounting, forensics, protected selection, calibrated Pilot design, map; STOP for human authorization

### S13.0 — Install (build only)

| Atomic | Executor | Does | Output | On PASS | On FAIL |
|---|---|---|---|---|---|
| I00_INSTALL | OPENCODE | Install M13B kit | kit files, kit tag wp2-m13b-kit-2026-09-29 | P00_KIT_SELFTEST | M13B_INSTALL_STOP (STOP; paste the block to the brain; installer already rolled back) |

### S13.1 — Evidence closure

| Atomic | Executor | Does | Output | On PASS | On FAIL |
|---|---|---|---|---|---|
| P00_KIT_SELFTEST | CONTROLLER | Kit self-tests | — | P01_GUARD | KIT_SELFTEST_FAIL (STOP non-resumable -> brain) |
| P01_GUARD | CONTROLLER | Smoke closure guard | research/wp2/pilot_v1_design/m13_guard.json | P02_USAGE | M13_GUARD_FAIL (STOP non-resumable -> brain) |
| P02_USAGE | CONTROLLER | Authoritative token/cost accounting | research/wp2/pilot_v1_design/smoke_v22_usage_accounting.json | P03_FORENSICS | M13_USAGE_FAIL (STOP non-resumable -> brain) |
| P03_FORENSICS | CONTROLLER | Failure/variance taxonomy | research/wp2/pilot_v1_design/smoke_v22_failure_taxonomy.json | P04_POOL | M13_FORENSICS_FAIL (STOP non-resumable -> brain) |

### S13.2 — Protected pool and selection

| Atomic | Executor | Does | Output | On PASS | On FAIL |
|---|---|---|---|---|---|
| P04_POOL | CONTROLLER | Pool census | research/wp2/pilot_v1_design/pool_census.json | P05_SELECT | M13_POOL_FAIL (STOP non-resumable -> brain) |
| P05_SELECT | CONTROLLER | Deterministic A/B/reserve selection | research/wp2/pilot_v1_design/pilot_selection.json | P06_DESIGN | M13_SELECT_FAIL (STOP non-resumable -> brain) |

### S13.3 — Design and map freeze

| Atomic | Executor | Does | Output | On PASS | On FAIL |
|---|---|---|---|---|---|
| P06_DESIGN | CONTROLLER | Pilot design freeze | research/wp2/pilot_v1_design/pilot_design_freeze_v1.json, research/wp2/pilot_v1_design/PILOT_DESIGN_FREEZE_V1.md | P07_MAP | M13_DESIGN_FAIL (STOP non-resumable -> brain) |
| P07_MAP | CONTROLLER | Task map validation | research/wp2/pilot_v1_design/task_map_validation.json, research/wp2/pilot_v1_design/TASK_MAP_M13_M16.md | P08_FREEZE | M13_MAP_FAIL (STOP non-resumable -> brain) |
| P08_FREEZE | CONTROLLER | Hash freeze + authorization template | research/wp2/pilot_v1_design/m13_freeze.json, research/wp2/pilot_v1_design/PILOT_A_HUMAN_AUTH_TEMPLATE.json | P09_VERIFY | M13_FREEZE_FAIL (STOP non-resumable -> brain) |

### S13.4 — Independent verification and provenance

| Atomic | Executor | Does | Output | On PASS | On FAIL |
|---|---|---|---|---|---|
| P09_VERIFY | CONTROLLER | Independent re-derivation | research/wp2/pilot_v1_design/m13_verify.json, tag wp2-pilot-v1-design-freeze-2026-09-29 | P10_CLOSE | M13_VERIFY_FAIL (STOP non-resumable -> brain) |
| P10_CLOSE | CONTROLLER | LIGHT export + push | project-LIGHT-M13B_DESIGN_FREEZE-*.zip | H13_AUTH | CLOSE_FAIL (STOP resumable after fixing network) |

### S13.5 — Human gate

| Atomic | Executor | Does | Output | On PASS | On FAIL |
|---|---|---|---|---|---|
| H13_AUTH | HUMAN | Human paid authorization | PILOT_A_HUMAN_AUTH filled + committed | M14A | NOT_AUTHORIZED (wait; nothing runs) |

## M14A — Pilot-A Gold vs Placebo calibration (paid)  (SPEC_ONLY_KIT_TO_BE_BUILT)

assay sensitivity + variance on 12 protected tasks x 2 replicates

### S14A.0 — Oracle readiness (zero API)

| Atomic | Executor | Does | Output | On PASS | On FAIL |
|---|---|---|---|---|---|
| M14A.S0.A1 | CONTROLLER | V3.1 readiness of all 26 eligible tasks | readiness_v31.json | M14A.S0.A2 | READINESS_ENV_FAIL (STOP resumable (env)) |
| M14A.S0.A2 | CONTROLLER | Apply frozen replacement rule | pilot_final_membership.json | M14A.S1.A1 | POOL_INSUFFICIENT (STOP -> human decision; no paid run) |

### S14A.1 — Freeze + paid preflight

| Atomic | Executor | Does | Output | On PASS | On FAIL |
|---|---|---|---|---|---|
| M14A.S1.A1 | CONTROLLER | Authorization check | auth_check.json | M14A.S1.A2 | NOT_AUTHORIZED (STOP -> human) |
| M14A.S1.A2 | CONTROLLER | Doctor offline+paid, canary, freeze | pilot_a_freeze.json | M14A.S2.A1 | FREEZE_FAIL (STOP) |

### S14A.2 — Generation (paid)

| Atomic | Executor | Does | Output | On PASS | On FAIL |
|---|---|---|---|---|---|
| M14A.S2.A1 | CONTROLLER | Generate r1 then r2 (48 episodes) | episodes r1/r2 | M14A.S2.A2 | E2E_PROVIDER_OUTAGE (STOP resumable; rerun) |
| M14A.S2.A2 | CONTROLLER | Generation freeze + push | generation_freeze.json | M14A.S3.A1 | GENERATION_FREEZE_FAIL (STOP) |

### S14A.3 — Evaluation (zero API)

| Atomic | Executor | Does | Output | On PASS | On FAIL |
|---|---|---|---|---|---|
| M14A.S3.A1 | CONTROLLER | Plan (task_id, full diff sha) | evaluations/plan.json | M14A.S3.A2 | EVAL_PLAN_FAIL (STOP) |
| M14A.S3.A2 | CONTROLLER | Evaluate in chunks | evaluation records | M14A.S4.A1 | EVAL_ERROR (STOP resumable) |

### S14A.4 — Summary + gate

| Atomic | Executor | Does | Output | On PASS | On FAIL |
|---|---|---|---|---|---|
| M14A.S4.A1 | CONTROLLER | Gates A0-A5 (gates_for(n)) | pilot_a_summary.json | M15 | PILOT_A_GENERATOR_FLOOR_HOLD (HUMAN_DECISION (M14R on ENG only)) |

## M14R — Generator/interface review (ENG only)  (SPEC_ONLY_CONDITIONAL)

only if Pilot-A generator floor hold

### S14R.1 — Interface probe on DEV_TRAIN_ENG only

| Atomic | Executor | Does | Output | On PASS | On FAIL |
|---|---|---|---|---|---|
| M14R.S1.A1 | HUMAN | Human decision recorded | decision record | M14A | NO_DECISION (wait) |

## M15 — Pilot-B selector behavior (paid)  (SPEC_ONLY_KIT_TO_BE_BUILT)

RM-CSS vs Agent descriptive E2E + stability + end-to-end cost

### S15.0 — Selector inputs

| Atomic | Executor | Does | Output | On PASS | On FAIL |
|---|---|---|---|---|---|
| M15.S0.A1 | CONTROLLER | RM-CSS scopes for final B tasks | rmcss_scopes_b.json | M15.S0.A2 | RMCSS_SCOPE_BUILD_FAIL (STOP -> brain) |
| M15.S0.A2 | CONTROLLER | Agent localization r1+r2 (paid) | agent_scopes_b_r1.json, agent_scopes_b_r2.json | M15.S0.A3 | AGENT_OUTAGE (STOP resumable) |
| M15.S0.A3 | CONTROLLER | Freeze selector inputs + push | selector_freeze.json | M15.S1.A1 | SELECTOR_FREEZE_FAIL (STOP) |

### S15.1 — Generation + evaluation

| Atomic | Executor | Does | Output | On PASS | On FAIL |
|---|---|---|---|---|---|
| M15.S1.A1 | CONTROLLER | Generate 72 episodes (RMCSS, AGENT, GOLD x r1,r2) | episodes | M15.S1.A2 | E2E_PROVIDER_OUTAGE (STOP resumable) |
| M15.S1.A2 | CONTROLLER | Freeze, evaluate, summarize | pilot_b_summary.json | M16 | PILOT_B_INSTRUMENT_FIX (STOP) |

## M16 — Research Run freeze  (SPEC_ONLY)

population, replicates, estimands, cost boundary

### S16.1 — Research Run freeze

| Atomic | Executor | Does | Output | On PASS | On FAIL |
|---|---|---|---|---|---|
| M16.S1.A1 | CONTROLLER | Apply replicate rule (2 or 3) | research_design.json | M16.S1.A2 | DESIGN_FAIL (STOP) |
| M16.S1.A2 | HUMAN | Human authorization of Research Run | auth | RESEARCH_RUN | NOT_AUTHORIZED (wait) |
