# WP2 M16 — STOP/resume/output contracts and predicted artifact/commit/tag chain

There are two controller plans, both run by the human with `scripts/wp2_ctl_v224.py`:

| Plan file | Name | Purpose |
|---|---|---|
| `controller/plan_m16_v1_dryrun.json` | `WP2_M16_V1_DRYRUN` | Resource dry-run |
| `controller/plan_m16_v1.json` | `WP2_M16_V1` | Route B |

`scripts/wp2_m16_maint.py` (S3 maintenance) is human-run only and never runs under a controller.

## 1. Controller exit codes

| Exit | Meaning | Human action |
|---|---|---|
| 0 | `WP2_CONTROLLER_COMPLETE` | Send the LIGHT to the brain |
| 20 | YIELD or `PAUSED_AT_<phase>` | Run the same command again |
| 10 | STOPPED, resumable (see §2) | Fix the external cause, then run the same command again |
| 11 | NEEDS_ACK (non-resumable STOP) | Do nothing. Send the STOP report and the LIGHT to the brain |
| 2 | KIT_TAMPERED | Do nothing. Send the output to the brain |

## 2. STOP tokens

| Engine exit | Controller token | Resumable | Typical cause | What to do |
|---|---|---|---|---|
| 3 | `HOLD_ACTIVE` | yes | C: free < 20 GiB, or the cold mirror (D:) is unreachable | Free space, or reconnect D:, then rerun |
| 4 | `USER_STOP_FLAG` | yes | `logs/M16_STOP.flag` present | Remove the flag, then rerun |
| 33 | `M16_PREFLIGHT` | yes | Host↔WSL clock blocked | Resync the clock, then rerun |
| 34 | `M16_RESOURCE_GATE` (main) / `M16_S3_REQUIRED` (dry-run R05) | yes | Projected C: free at the end of Q09 < 25 GiB | Run the S3 mission, then rerun |
| 35 | `M16_ADAPTER_FAIL` | **no** | R2 fail-closed violation (e.g. `mechanism=none` while a dev group is declared) | Send `adapter/adapter_report.json` |
| 36 | `M16_FIREWALL` | **no** | Selector-input firewall violation | Send the report |
| 37 | `M16_TAG_GATE` | yes | A tag is not on origin / a tag is not unique / a file differs from the tag / origin is unreachable | If origin was unreachable, rerun. Otherwise send the report |
| 78 | `M16_INVARIANT` | **no** | Frozen drift, a corrupt record, a GOLD identity violation, a restricted diff that does not apply | Send the report |
| 79 | `EVAL_ERROR` | yes | Docker/WSL/evaluation infrastructure (the identity is retried on resume) | Check Docker/WSL, then rerun |
| — | `NO_PROGRESS` / `MAX_ITERATIONS` | yes / no | Loop stalled | Send the report |
| — | `KIT_SELFTEST_FAIL` | no | A unit test fails on this machine | Send the output |
| — | `POST_ACTION_FAILED` / `FINAL_ACTION_FAILED` | yes | Push or tag failed (network) | Rerun. Tags never move |

## 3. Resume semantics (no double work, no double counting)

- **Records.** Every unit writes one self-hashed record atomically (temp file + `os.replace`). A loop skips VALID records. A CORRUPT record STOPs (exit 78); it is never overwritten.
- **Attempt ledgers.** Each stage (`oracle/`, `evalsets/`, `readiness/`, `opws/`) appends one line per attempt to an `attempts.jsonl` (key, attempt, invocation, outcome, reason). Infra limits are computed from the ledger, so a resumed controller continues the same count.
- **Infra.** Within one engine invocation (one process; each infra STOP 79 ends it and the controller run) an attempt is retried once. A second failure STOPs (79). The third attempt happens after the resume. If it also fails, the key becomes `*_INFRA_UNRESOLVED`.
- **OPWS dedup.** OPWS evaluations are keyed by `(task, identity)`, so one evaluation serves every selector item with the same restricted diff. The analysis reads exactly one result record per plan item (completeness check, Q10).
- **Freezes are idempotent.** Every freeze (`eligibility`, `evalsets`, `READY`, `scopes`, `opws_complete`) is write-once: if the file exists with a valid self-hash and equal content (ignoring `utc`/`artifact_sha256`), nothing is written, so the bytes stay identical and a resume after a failed tag push re-tags the same commit. Different content is STOP 78. Tags have fixed names and never move. On resume the controller accepts a tag that is only behind by controller bookkeeping files.
- **P2P-U resume.** It reuses a verified unit (`verify_unit`). An unverified unit is deleted and rerun (frozen behaviour).

## 4. Predicted artifact / commit / tag chain

Every path below is under `research/wp2/m16_v1/` unless stated otherwise.

| # | Actor | Artifacts | Commit message | Tag (exact refspec push) |
|---|---|---|---|---|
| 0 | installer | `scripts/wp2_m16_*.py`, `tests/unit/wp2/m16/**`, `controller/plan_m16_v1*.json`, `controller/light_profile_m16.json`, `controller/KIT_MANIFEST_M16.json`, `m16_design_freeze_v1.json`, `m16_l_opws_quarantine_amendment.json`, `m16_r1_repetition_amendment.json`, docs (design, contracts, missions, reviews v1/v2); DECISIONS.md appended | `feat(wp2): M16 OPWS-MAIN kit ...` | `wp2-m16-v1-kit-2026-10-02` |
| 1 | dry-run R01 | `m16_guard_dryrun.json` | `evidence(wp2): M16 guard (dry-run)` | — |
| 2 | dry-run R02 | `adapter/adapter_report.json` (shadow root regenerated under `_workspace/tmp/`, not committed) | `... R2 adapter verification` | — |
| 3 | dry-run R03 | `dryrun/selection.json` | `... dry-run selection` | — |
| 4 | dry-run R04 (loop) | `dryrun/<task>/{record.json, junit_raw.tar.gz}`, `dryrun/attempts.jsonl` | `... dry-run progress (n)` | — |
| 5 | dry-run R05 | `dryrun/resource_gate.json` (PASS or STOP `M16_S3_REQUIRED`) | `... resource gate` | — |
| 6 | dry-run final | all of the above + LIGHT `M16_DRYRUN` | `evidence(wp2): M16 resource dry-run` | `wp2-m16-v1-dryrun` |
| 6s | S3 (only if required) | `maintenance/{capability_probe.json, COMPACTION_INSTRUCTIONS.md, volume_inventory.json, deletions.jsonl, measure_*.json, post_check.json}` | committed by the human per the S3 mission | — |
| 7 | main Q00M | `mirror/wp2-m16-v1-dryrun.json` (+ copy in `D:\wp2_cold\m16_v1\`) | `... cold mirror (dry-run)` | — |
| 8 | Q01 | `m16_guard.json` (includes the resource-gate recheck) | `... guard (main)` | — |
| 9 | Q02 | `adapter/adapter_report.json` | `... R2 adapter verification (main)` | — |
| 10 | Q03 (loop, about 55 iterations) | `oracle/<task>/{record.json, junit_raw.tar.gz}`, `oracle/attempts.jsonl` | `... oracle progress (n)` | — |
| 11 | Q04 | `m16_v3_eligibility.json` | `evidence(wp2): M16 eligibility freeze` | `wp2-m16-v1-eligibility` |
| 12 | Q04M | `mirror/wp2-m16-v1-eligibility.json` | `... cold mirror (eligibility)` | — |
| 13 | Q05A (loop) | `evalsets/<task>/evalset.json`, `evalsets/p2pu/**` (rediscovery, unit results, JUnit), `evalsets/attempts.jsonl` | `... evaluator-set progress (n)` | — |
| 14 | Q05B | `evaluator_only/m16_main_evaluator_sets_v3.json`, `m16_evalsets_freeze.json` | `evidence(wp2): M16 evalsets freeze` | `wp2-m16-v1-evalsets` |
| 15 | Q05M | `mirror/wp2-m16-v1-evalsets.json` | `... cold mirror (evalsets)` | — |
| 16 | Q06 (loop) | `readiness/<task>/{record.json, negative_groups.json, positive_groups.json, *diagnostics*}`, `junit/<task>/{rneg,rpos}/*`, `readiness/attempts.jsonl` | `... readiness progress (n)` | — |
| 17 | Q07 | `m16_ready_membership.json` | `evidence(wp2): M16 ready freeze` | **`wp2-m16-v1-ready`** (must be unique) |
| 18 | Q07M | `mirror/wp2-m16-v1-ready.json` | `... cold mirror (ready)` | — |
| 19 | Q08 | `scopes/frozen_scopes.json`, `opws/plan.json` (P2 binding), `opws/<task>/<selector>/opws_diff.patch` — **the first commit touching scopes/ or opws/** | `evidence(wp2): M16 scopes freeze` | `wp2-m16-v1-scopes` |
| 20 | Q08V | — (verification only) | — | — |
| 21 | Q08M | `mirror/wp2-m16-v1-scopes.json` | `... cold mirror (scopes)` | — |
| 22 | Q09 (loop) | `opws/unique/<task>/<identity>/evaluation.json`, `opws/<task>/<selector>/opws.json`, `opws/diagnostics/**`, `junit/<task>/u_*/*`, `opws/attempts.jsonl` | `... OPWS progress (n)` | — |
| 23 | Q10 | `m16_opws_complete.json` | `... OPWS complete` | — |
| 24 | Q11 | `analysis/m16_analysis.json` | `... analysis` | — |
| 25 | Q12 | `m16_summary.json`, `docs/WP2_M16_V1_RESULT.md` | `... summary` | — |
| 26 | final | LIGHT `M16_RESULT` (human copies it to `D:\wp2_cold` and verifies the hash) | `evidence(wp2): close M16 OPWS-MAIN V1` | `wp2-m16-v1-result` |

**LIGHT is a convenience copy, not the evidence.** It is capped at 5 MiB per file and 45 MiB in total, and files beyond the cap are skipped (the export lists them). Per-task oracle records come last in the profile, so a large run may leave some of them out. The authoritative evidence is the pushed git history (tags above) plus the hash-verified cold mirrors written after every freeze.

**Tag order:** `kit` → `dryrun` → `eligibility` → `evalsets` → **`ready`** → `scopes` → `result`. What the code enforces:

- Q08 (P1, `ready_pushed`) enforces kit → dryrun → eligibility → evalsets → READY → HEAD, each tag unique and on origin.
- Q08V/Q09/Q11 re-check the READY binding (commit and tag objects) against origin; Q09 also requires the scopes tag on origin.
- V1 requires every commit touching `scopes/` or `opws/` to descend from READY.
- `result` is created by the final action on HEAD, which descends from all of the above. The simulation checks the full chain.

## 5. Allowed writes per phase (controller-enforced)

| Phases | Allowed prefixes |
|---|---|
| R01 / Q01 | the guard file |
| R02 / Q02 | `adapter/` |
| R03–R05 | `dryrun/` |
| Q03 | `oracle/` |
| Q04 | eligibility file |
| Q05A | `evalsets/` |
| Q05B | `evaluator_only/` + freeze file |
| Q06 | `readiness/`, `junit/` |
| Q07 | membership file |
| Q08 | `scopes/`, `opws/` |
| Q09 | `opws/`, `junit/`, complete file |
| Q11 | `analysis/` |
| Q12 | summary + `docs/WP2_M16_V1_RESULT.md` |
| `*M` mirror phases | `mirror/` |

`logs/`, `_workspace/tmp/` and the controller state are always allowed. Any other write is a STOP `UNEXPECTED_WRITE`. Historical roots are therefore never written. `historical-verify` additionally compares their git tree ids with the kit commit.
