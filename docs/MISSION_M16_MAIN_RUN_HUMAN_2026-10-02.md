# MISSION M16-R: Route B main run (human run, ONLY after the brain approves the dry-run result)

Run this in PowerShell from the repository root, using the project Python, with sleep disabled.
Do not run AG16 or any other controller at the same time. Keep D: connected, because the cold mirror phases write to `D:\wp2_cold\m16_v1`.

Command (repeat it until the controller reports `WP2_CONTROLLER_COMPLETE`):

    C:\Users\Ahmed\AppData\Local\anaconda3\python.exe scripts/wp2_ctl_v224.py run --plan controller/plan_m16_v1.json

What it covers, with central Docker time (it runs over several days):

| Phase(s) | Work | Central Docker time |
|---|---|---|
| Q03 | Oracle construction, 220 tasks | about 16 h |
| Q05A | P2P-U for eligible tasks | about 8–15 h |
| Q06 | Readiness | about 12–21 h |
| Q07 | READY freeze (unique tag) | — |
| Q08 | First access to the selections | — |
| Q09 | OPWS | about 6–12 h |
| Q11–Q12 | Analysis and summary | — |

Exit codes and STOP tokens: see `docs/WP2_M16_CONTRACTS_2026-10-02.md` §1–§2.

Short version:

- **Exit 20:** run the same command again.
- **A resumable STOP** (HOLD_ACTIVE, EVAL_ERROR, M16_PREFLIGHT, M16_TAG_GATE caused by a network problem, POST_ACTION_FAILED): fix the external cause, then run the same command again.
- **A non-resumable STOP** (M16_ADAPTER_FAIL, M16_FIREWALL, M16_INVARIANT, KIT_*): change nothing. Send the STOP report and the LIGHT.
- **`WP2_CONTROLLER_COMPLETE`:**
  1. Copy `project-LIGHT-M16_RESULT-*.zip` to `D:\wp2_cold\`.
  2. Verify that its SHA-256 is identical on both drives.
  3. Send the LIGHT to the brain.
