# MISSION M16-D: 3-task resource dry-run (human run)

Run this in PowerShell from the repository root, using the project Python, with sleep disabled.
Do not run AG16 or any other controller at the same time.

- **Prerequisite:** the M16 kit is installed (`M16_INSTALL_COMPLETE`), and `wp2-m16-v1-kit-2026-10-02` is on origin.
- **What it does:** a resource and instrument preflight only. It does **not** measure selector performance.
  - It runs the R1 oracle construction on 3 tasks (one per era, chosen selector-blind and deterministically).
  - It measures C: free, VHDX growth, wp2-uv-cache growth, Docker disk usage, wall time, and leftover worktrees/containers/DBs.
  - It records the dev/test closure mechanism and the install classification.
  - It projects C: free at the end of Q09.
- **Model API calls:** zero. Docker: 3 tasks × 2 states.

Command:

    C:\Users\Ahmed\AppData\Local\anaconda3\python.exe scripts/wp2_ctl_v224.py run --plan controller/plan_m16_v1_dryrun.json

Phases:

1. R00: self-tests.
2. R01: guard.
3. R02: R2 adapter verification (WSL git only, no Docker; about 10–20 min).
4. R03: selection.
5. R04: 3 tasks (about 15–40 min).
6. R05: resource gate.
7. On PASS: commit, tag `wp2-m16-v1-dryrun`, LIGHT.

How to react:

- **Exit 20:** run the same command again.
- **`WP2_CONTROLLER_COMPLETE`** (gate PASS): send `project-LIGHT-M16_DRYRUN-*.zip` to the brain. **Do not start the main plan yet.**
- **STOP `M16_S3_REQUIRED`:** projected free space is below 25 GiB. Send the LIGHT or STOP report, together with `research/wp2/m16_v1/dryrun/resource_gate.json`, to the brain. Then follow `MISSION_M16_S3_MAINTENANCE_HUMAN_2026-10-02.md` only after the brain confirms.
- **STOP `M16_ADAPTER_FAIL`** (non-resumable): send `research/wp2/m16_v1/adapter/adapter_report.json` and the report. Change nothing.
- **STOP `HOLD_ACTIVE`** (C: < 20 GiB): free space without touching Docker/WSL data, then rerun.
- **STOP `EVAL_ERROR`:** check that Docker Desktop/WSL is up, then rerun once. If it repeats, send the report.
- **Any other STOP:** send the STOP report and the LIGHT.
