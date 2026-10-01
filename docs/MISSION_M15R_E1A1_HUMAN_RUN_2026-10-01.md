# MISSION M15R-E1A1-H: HUMAN RUN (continue M15-R from S2 evaluation)

Run in PowerShell from the repository root, with the project Python and with sleep disabled. Do not run AG16 or any other controller at the same time.

**Do not run the old plan** (`controller/plan_m15r_v1.json`) again. It stays stopped at Q16 as a historical record.

    C:\Users\Ahmed\AppData\Local\anaconda3\python.exe scripts/wp2_ctl_v224.py run --plan controller/plan_m15r_v1_e1a1.json

What it does, in order:

1. A00: self-tests.
2. A01: verifies the amendment, the frozen files and the freezes (zero API).
3. A02: evaluates the remaining 19 S2 identities (zero API, about 2–2.5 h).
4. A03: the S2 gate.
5. A04–A07: S3 (paid, about $0.35, about 4–5 h). If the gate fails, these phases are recorded no-ops.
6. A08: the summary, then the result tag and the LIGHT.

How to react:

- **Exit 20 (yield):** run the same command again.
- **A resumable STOP** (`EVAL_ERROR`, `E2E_PROVIDER_OUTAGE`, `HOLD_ACTIVE`, `PAID_PREFLIGHT_FAIL`): fix the external cause, then run the same command again.
- **A new `EVAL_ERROR` whose E1 diagnostics show some other startup failure:** do not fix it by hand. Send the STOP report, the `e1_diagnostics.json` and the LIGHT to the brain.
- **`M15R_GOLD_FLOOR_FAIL_NO_GENERATION_CLAIM`:** this is not a STOP. S3 is skipped by design.
- **Any other STOP:** send the STOP report and the LIGHT to the brain.
- **`WP2_CONTROLLER_COMPLETE`:** send `project-LIGHT-M15R_RESULT-*.zip` to the brain.
