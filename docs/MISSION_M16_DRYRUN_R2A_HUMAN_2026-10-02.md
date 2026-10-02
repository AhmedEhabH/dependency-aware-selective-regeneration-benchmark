# MISSION M16-D-R2A: restart of the 3-task resource dry-run after amendment R2A (human run)

**Prerequisites:**
- The R2A installer printed `M16_R2A_INSTALL_COMPLETE`.
- Tag `wp2-m16-v1-r2a-2026-10-02` is on origin.
- The brain has reviewed the installer output.

**Before you start:** run it in PowerShell from the repository root with the project Python, and keep the machine from sleeping. Do not run any other controller at the same time.

**Do not run the old plan.** `controller/plan_m16_v1_dryrun.json` stays in its STOP (`NEEDS_ACK`) as evidence. Do not ack it, and do not delete its state.

Command:

    C:\Users\Ahmed\AppData\Local\anaconda3\python.exe scripts/wp2_ctl_v224.py run --plan controller/plan_m16_v1_dryrun_r2a.json

**Phases** (identical to the original dry-run; every phase reruns from R00):
1. R00: unit tests, including the R2A tests.
2. R01: guard (kit tag + R2A tag).
3. R02: R2 adapter verification under rule R2A (WSL git only, no Docker).
4. R03: selection.
5. R04: 3 tasks with Docker.
6. R05: resource gate.
7. On PASS: commit, tag `wp2-m16-v1-dryrun`, LIGHT `M16_DRYRUN`.

**How to react:**
- **Exit 20:** run the same command again.
- **`WP2_CONTROLLER_COMPLETE`:** send `project-LIGHT-M16_DRYRUN-*.zip` to the brain. Do not start the main plan.
- **STOP `M16_ADAPTER_FAIL`** (non-resumable): send `research/wp2/m16_v1/adapter/adapter_report.json` (it now carries `r2a.historical_schema`) and the STOP report. Change nothing.
- **STOP `M16_TAG_GATE`** at R01: send the STOP report. The guard checks both the kit tag and the R2A tag on origin.
- **STOP `M16_S3_REQUIRED`, `HOLD_ACTIVE`, `EVAL_ERROR`:** react as in `MISSION_M16_DRYRUN_HUMAN_2026-10-02.md`.
- **Any other STOP:** send the STOP report and the LIGHT.
