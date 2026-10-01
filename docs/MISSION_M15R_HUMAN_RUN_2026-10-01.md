# MISSION M15R-H: HUMAN RUN (M15-R V1, Pilot-B scope sufficiency)

Run everything in PowerShell from the repository root, with the project Python and with sleep disabled.

Do not run AG16 or any other controller while an M15-R stage is running. Nothing in M15-R starts M16.

**Stage 1: guard + S0 readiness (zero API, Docker; about 1.5–2 h)**

    C:\Users\Ahmed\AppData\Local\anaconda3\python.exe scripts/wp2_ctl_v224.py run --plan controller/plan_m15r_v1.json --until Q03_MEMBERSHIP

- `PAUSED_AT_Q03_MEMBERSHIP`: go to Stage 2.
- `STOP READINESS_ENV_FAIL` (resumable): fix Docker or WSL, then run the same command again. The same task resumes.
- `STOP M15R_POOL_INSUFFICIENT` (fewer than 6 READY Pilot-B tasks): a terminal fact. Send the STOP report and the LIGHT to the brain. Nothing paid has run. The frozen fallback is WP2 Option B.
- `STOP M15R_GUARD_FAIL` or any other non-resumable STOP: send the STOP report and the LIGHT to the brain.

**Stage 2: human authorization (cap between $2.00 and $3.00 for Agent localization + S2 + S3 together; expected spend about $1.2; $3.00 recommended)**

    C:\Users\Ahmed\AppData\Local\anaconda3\python.exe scripts/wp2_m15r_authorize.py --approve "I_AUTHORIZE_WP2_M15R_V1=YES" --by "Ahmed Ehab" --max-usd 3.0

EXPECT `M15R_HUMAN_AUTH_COMPLETE`.

**Stage 3: Agent localization, S1 OPWS, S2, gated S3 (resumable)**

    C:\Users\Ahmed\AppData\Local\anaconda3\python.exe scripts/wp2_ctl_v224.py run --plan controller/plan_m15r_v1.json

What it does, in order:

1. Doctors.
2. Agent prefreeze, which is tagged and pushed.
3. Agent localization: frozen protocol v3, 3 runs per member, paid, about $0.75, about 1 h.
4. Scope freeze, which is tagged and pushed.
5. S1 OPWS: zero API, about 2–3 h. Its result is tagged.
6. S2 GOLD G0: paid, about $0.15, generation plus about 2–2.5 h of evaluation.
7. S2 gate.
8. S3: only if the gate passes; paid, about $0.35, about 4–5 h.
9. Summary and LIGHT.

How to react:

- Exit 20 (yield): run the same command again.
- A resumable STOP (`E2E_PROVIDER_OUTAGE`, `HOLD_ACTIVE`, `EVAL_ERROR`, `PAID_PREFLIGHT_FAIL`, `NOT_AUTHORIZED`, `USER_STOP_FLAG`): fix the external cause, then run the same command again.
- `M15R_GOLD_FLOOR_FAIL_NO_GENERATION_CLAIM` is not a STOP. It is recorded and S3 is skipped by design; the run continues to the summary.
- Any other STOP (`M15R_INVARIANT`, `E2E_BUDGET_STOP`, `E2E_REQUEST_REJECTED`, `NO_PROGRESS`, `UNEXPECTED_WRITE`): send the STOP report and the LIGHT to the brain. Do not repair anything manually.
- `WP2_CONTROLLER_COMPLETE`: send `project-LIGHT-M15R_RESULT-*.zip` to the brain.

To stop safely between items, create `logs/M15R_STOP.flag`. Delete it before resuming.
