# MISSION M14R V1: HUMAN RUN

Run everything in PowerShell from the repository root, with the project Python and with sleep disabled.

Do not run AG16 or any other controller while an M14R stage is running.

**Stage 1: zero-API readiness (about 2.5–3 h; no model calls)**

    C:\Users\Ahmed\AppData\Local\anaconda3\python.exe scripts/wp2_ctl_v224.py run --plan controller/plan_m14r_v1.json --until R04_MEMBERSHIP

- `PAUSED_AT_R04_MEMBERSHIP`: go to Stage 2.
- `STOP READINESS_ENV_FAIL` (resumable): fix Docker or WSL, then run the same command again. The same task resumes.
- `STOP POOL_INSUFFICIENT` or any non-resumable STOP: send the STOP report and the LIGHT to the brain. Nothing paid has run.

**Stage 2: human authorization (cap ≤ $3.00; expected spend about $1.1)**

    C:\Users\Ahmed\AppData\Local\anaconda3\python.exe scripts/wp2_m14r_authorize.py --approve "I_AUTHORIZE_WP2_M14R_V1=YES" --by "Ahmed Ehab" --max-usd 3.0

EXPECT `M14R_HUMAN_AUTH_COMPLETE`.

**Stage 3: paid probe and evaluation (about 10–12 h, resumable)**

    C:\Users\Ahmed\AppData\Local\anaconda3\python.exe scripts/wp2_ctl_v224.py run --plan controller/plan_m14r_v1.json

- Exit 20 (yield): run the same command again.
- A resumable STOP (`E2E_PROVIDER_OUTAGE`, `HOLD_ACTIVE`, `EVAL_ERROR`, `PAID_PREFLIGHT_FAIL`): fix the external cause, then run the same command again.
- A `PAID_PREFLIGHT_FAIL` that says pyflakes is missing: run `C:\Users\Ahmed\AppData\Local\anaconda3\python.exe -m pip install pyflakes`, then run the same command again.
- Any other STOP: send the STOP report and the LIGHT to the brain. Do not repair anything manually.
- `WP2_CONTROLLER_COMPLETE`: send `project-LIGHT-M14R_RESULT-*.zip` to the brain.

The result token does not start M15.
