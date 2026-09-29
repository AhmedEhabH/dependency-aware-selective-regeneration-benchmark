# WP-2 E2E Smoke ENG v2.2: deterministic controller runbook

The controller (`scripts/wp2_ctl.py`) decides every transition. It does not rely on an
LLM executor. It reads `controller/plan_smoke_v22.json`, keeps one state file, runs the
exact commands, maps exit codes to outcomes, checks that files were written only where
allowed, and handles commits, tags and pushes itself. When it stops, it writes a STOP
report and a LIGHT zip automatically.

## Kit integrity

- Every kit file is hashed in `controller/KIT_MANIFEST.json`. Line endings (CRLF vs LF)
  are normalized before hashing.
- `python scripts/wp2_ctl.py verify-kit` must print `KIT_OK`.
- The controller refuses to run (exit 2, `KIT_TAMPERED`) if any kit file has been edited.
- Nobody edits kit files. A defect in the kit gets fixed by the brain, which issues a new
  kit version.

## Run (human, PowerShell, repository root, project Python environment)

    powercfg /change standby-timeout-ac 0
    python scripts/wp2_ctl.py run

- Run the same command again after any stop. The controller resumes from its state file.
- Exported LIGHT zips are written to the parent folder of the repository.

## Exit codes and the only allowed reaction

| exit | block printed | reaction |
|---|---|---|
| 0 | WP2_CONTROLLER_COMPLETE | Send the LIGHT zip (`project-LIGHT-SMOKE_V22_RESULT-*.zip`) to the brain. |
| 20 | WP2_CONTROLLER_YIELD | Run the same command again. |
| 10 | WP2_CONTROLLER_STOPPED, RESUMABLE=True | Fix the named external cause (table below), then run again. |
| 10 | WP2_CONTROLLER_STOPPED, RESUMABLE=False | Send the STOP report and the LIGHT zip to the brain. Change nothing. |
| 11 | WP2_CONTROLLER_NEEDS_ACK | Send the brain the report. Resume only with the brain's `ack-stop` command. |
| 2 | KIT_TAMPERED | Restore the kit with `git checkout -- <files>`, or send the output to the brain. |

## Resumable tokens (external causes)

| token | cause | fix, then run again |
|---|---|---|
| E2E_PROVIDER_OUTAGE | provider 429/5xx lasted longer than 3 × 15-minute cooldowns | Wait at least 60 minutes. |
| HOLD_ACTIVE | a HOLD file exists in the v22 root | Remove it only if you created it on purpose. |
| USER_STOP_FLAG | `logs/E2E_STOP.flag` exists | Delete the flag. |
| ENV_DOCTOR_FAIL | Docker/WSL/Postgres/disk/clock check failed | Start Docker Desktop and WSL, and free disk space. |
| PAID_PREFLIGHT_FAIL | API key missing, credit below $5, or price more than 2x | Set the key or top up credit. |
| EVAL_ERROR | an evaluator container error | Run again once. If it repeats, send the LIGHT zip. |

## Graceful stop

To stop at the next safe point, create the flag file:

    New-Item logs/E2E_STOP.flag

Ctrl+C is also safe. An interrupted episode writes no record and is redone on the next run.

## Scientific invariants (enforced in code)

- A provider failure is never a scientific outcome. The only terminal statuses are
  `NO_SCOPE`, `INVALID_AFTER_REPAIR` and `APPLIED`.
- A `GENERATION_FAIL` record in the v22 root is an invariant violation (driver exit 78).
- Code, scopes, evaluator sets, policy and the era/Postgres image IDs are frozen (P05) and
  re-verified before every generation and evaluation chunk.
- Generation is frozen and pushed (P08) before any evaluation begins, which keeps
  generation blind to outcomes.
- Exact reproducibility means replaying the frozen raw responses and diffs through the
  frozen evaluator. A fresh API generation run is a replication, not a reproduction.
