# MISSION 14A-E1: HUMAN RUN

Run every command in PowerShell from the repository root, using the project Python. Keep sleep disabled.

Do NOT run the original plan (`plan_m14a_pilot_a_v1.json`) again. Its state stays at STOP:EVAL_ERROR as history.

**Run the E1 plan: remaining 12 unique evaluations, summary and addendum (zero model API, about 1.5–2 h).**

    C:\Users\Ahmed\AppData\Local\anaconda3\python.exe scripts/wp2_ctl_v224.py run --plan controller/plan_m14a_pilot_a_v1_e1.json

- Exit 20 (yield): run the same command again.
- STOP:EVAL_ERROR: do not change anything. Send the STOP report and the LIGHT to the brain. The LIGHT now contains `evaluations/diagnostics/.../e1_diagnostics.json`.
- Any other STOP: send the STOP report and the LIGHT to the brain. Do not repair anything manually.
- On success, the controller commits the result, pushes it, tags `wp2-pilot-a-v1-e1-result-<date>` and exports `project-LIGHT-PILOT_A_RESULT-*.zip`. Send that LIGHT to the brain.
