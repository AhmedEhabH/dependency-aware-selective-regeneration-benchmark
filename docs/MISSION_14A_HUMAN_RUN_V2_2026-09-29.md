# MISSION 14A (corrected), HUMAN RUN

Run everything in PowerShell from the repository root, with the project Python and with sleep disabled.

**Stage 1: readiness (zero model API; about 7–14 h, one task per iteration)**

    C:\Users\Ahmed\AppData\Local\anaconda3\python.exe scripts/wp2_ctl_v224.py run --plan controller/plan_m14a_pilot_a_v1.json --until P03_MEMBERSHIP

- Exit 20 (yield): run the same command again.
- Exit 10 with READINESS_ENV_FAIL: fix Docker or WSL, then run it again. The same task resumes.
- POOL_INSUFFICIENT: send the LIGHT to the brain. Nothing paid runs.

**Stage 2: authorization (only if membership is FULL or REDUCED_n)**

    C:\Users\Ahmed\AppData\Local\anaconda3\python.exe scripts/wp2_m14a_authorize.py --approve "I_AUTHORIZE_WP2_PILOT_A_V1=YES" --by "Ahmed Ehab" --max-usd 1.0

**Stage 3: paid Pilot-A (about 3–4 h)**

    C:\Users\Ahmed\AppData\Local\anaconda3\python.exe scripts/wp2_ctl_v224.py run --plan controller/plan_m14a_pilot_a_v1.json

On any STOP that is not resumable, send the STOP report and the LIGHT to the brain. Do not repair anything manually.
