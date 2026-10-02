# WP2 M16 Amendment R2A: R2 adapter-verifier historical-schema rule (2026-10-02)

- **Record:** `research/wp2/m16_v1/m16_r2a_adapter_verifier_amendment.json` (self-hashed)
- **Rule:** `M16_R2A_ENG_IDENTITY_HIST_SCHEMA_V1`
- **Code:** `scripts/wp2_m16_r2a.py`
- **Tag:** `wp2-m16-v1-r2a-2026-10-02`. It is a descendant of the unchanged kit tag `wp2-m16-v1-kit-2026-10-02` (commit `753e391932679d9d321021675684d0fd48308f07`).
- **Model/API calls:** zero. Installing the amendment made zero Docker, WSL or controller calls.

## 1. Trigger (factual)

- **Plan:** the first resource dry-run, `WP2_M16_V1_DRYRUN`, from `controller/plan_m16_v1_dryrun.json`.
  - R00 passed (81/81).
  - R01 guard passed.
  - R02_ADAPTER_VERIFY stopped with `M16_ADAPTER_FAIL`, `RESUMABLE=False`.
- **Error:** `KeyError: 'dev_test_closure'` at `scripts/wp2_m16_run.py:586`, on `rec = hist[t]["manifest"]["dev_test_closure"]`.
- **Not reached:** R03 selection, R04 Docker execution, R05, and all M16 MAIN work. No historical file was touched.
- **LIGHT:** `project-LIGHT-STOP_M16_ADAPTER_FAIL-2026-10-02-1511.zip`, sha256 `7521b192cd2d7b251c05ee2cdb71818330599d709844a5d2d8e5fd5c82036f9c`.

## 2. Cause

The R2 verifier of the kit assumed one schema for every record of the frozen ENG Phase-5 file `research/wp2/harness_v3_2026-09-26/phase5_c4_v3_per_task.jsonl` (LF sha256 `fe7a94ef…35d5e3`, pinned by the design freeze).

The project ledger (`PROGRESS.md`) shows the file comes from two eras:
- **Phase-5 ENG V3, 2026-09-26.** 29 ENG candidates: 22 DONE and 7 ENV_INSTALL_BLOCKED.
- **Environment Closure V3.1, 2026-09-27.** This added the rule-derived historical dev/test closure (`v31_dev_closure`), and reran C4 for 14 affected tasks of the 16-task oracle-valid union.

`dev_test_closure` belongs to the V3.1 schema. Records that predate V3.1, or that V3.1 never touched, do not carry it.

The kit's zero-Docker simulation wrote a synthetic history file in which **every** record had the field, so the assumption was never exercised.

The exact per-record schema of the real file can only be read on the real machine. The amendment installer measures it read-only: run `--diagnose`, or the installer's PRECHECK. The result is committed in `research/wp2/m16_v1/r2a/m16_r2a_failed_dryrun_archive.json`. Every R02 run also reports it in `adapter_report.json` under `r2a.historical_schema`: the per-line schema, the closure state per status, the duplicates, and the tasks with and without a recorded closure.

## 3. Rule M16_R2A_ENG_IDENTITY_HIST_SCHEMA_V1

**1. Required for every historical ENG record. No status is exempt.**
- Frozen closure equals adapted closure (canonical sha). This is the reviewer-approved R2 ENG test (Review Package v2, §12 R2: "Q02 asserts both that ENG outputs are identical and that MAIN closure ≠ `none` wherever a dev group is declared").
- Frozen lookup equals adapted lookup (parent, target, era).
- The install mode of the target manifests equals the recorded `manifest.install_mode`.
- The lock signature of the target manifests equals the recorded `manifest.lockfile_sha256`.

**2. Additional provenance, only where the historical record itself carries `manifest.dev_test_closure`.**
- Every recorded brief key (`mechanism`, `n_pins`, `pins_sha256`, `n_unsupported`) must equal the adapted closure.
- A record without the field is `NOT_RECORDED_ABSENT`; a null field is `NOT_RECORDED_NULL`. Nothing is backfilled, inferred or written to history.

**3. Fail-closed schema.** Each of these is a violation: STOP 35, with the adapter report written first.
- an unparsable line or a non-object line;
- a missing `task_id`, `target_commit`, `manifest`, `manifest.install_mode` or `manifest.lockfile_sha256`;
- a recorded closure with an unknown shape;
- an empty file.

The amendment installer applies the same parser as a PRECHECK. It refuses to install if the real file falls outside the rule. Only the evidenced V3.1 field was made conditional.

**4. Unchanged MAIN checks:**
- all 220 rows;
- lookup equals the frozen row (commits, era);
- `check_main_closure` (era, notes, declared dev group means `mechanism != none`, known mechanism);
- commits present on Windows and in WSL;
- zero selector access (the firewall is installed for `adapter-verify`);
- zero model/API calls.

## 4. Should closure evidence come from the later V3/P2P-U records instead? (audit)

**From the ledger: no, at most a subset.**
- V3.1 closure reruns covered the 14 affected tasks of the 16-task oracle-valid union.
- P2P-U V3 ran only on that union (32 units).
- No later record covers the 7 ENV_INSTALL_BLOCKED tasks or the DONE tasks outside the union.

So later records can give provenance for **at most 16 of 29** ENG tasks. They cannot replace the identity test.

**What R2A does instead:**
- It uses the direct frozen-vs-adapted identity, which covers **all** ENG records.
- It uses recorded closures only as additional provenance, where the record carries one.
- It does not read later files inside the verifier, because their schemas are not part of the frozen design.

**Coverage report:** `--diagnose` (and the PRECHECK archive) also survey every JSON/JSONL file under `research/wp2/harness_v3_2026-09-26/` for task-keyed `dev_test_closure` values. They report the coverage over the ENG tasks, and mechanism agreement with any recorded Phase-5 closure. This is report-only; no evidence is created.

## 5. What changed: minimum set, all named in the record with before/after LF sha256

| File | Change |
|---|---|
| `scripts/wp2_m16_run.py` | `adapter_verify` uses the rule. `guard` verifies the amended files against the R2A tag and every other kit file against the kit tag (`r2a_gate`). `ready_pushed` requires kit → R2A → dryrun when the record exists. |
| `scripts/wp2_m16_r2a.py` (new) | Pure rule module: no I/O, no frozen imports. |
| `tests/unit/wp2/m16/test_m16_r2a.py` (new) | The 5 required regression tests, the preserved checks, schema fail-closed, the guard gate on a real git repo with a bare origin, and record/plan consistency. |
| `tests/unit/wp2/m16/sim/simulate.py` | Copies the new module. Its synthetic history now mixes records with and without the closure field. |
| `controller/plan_m16_v1_dryrun_r2a.json` (new) | Restart plan: the phases are identical; it has a new id, state file and report dir. |
| `controller/KIT_MANIFEST_M16.json` | Integrity hash list updated. The original stays in the kit tag. |
| `research/wp2/m16_v1/m16_r2a_adapter_verifier_amendment.json` (new) | Static, self-hashed amendment record. |
| `research/wp2/m16_v1/r2a/**` (new, written at install) | Byte copies of the failed dry-run evidence, plus the archive record (STOP facts, LIGHT hash, historical schema census). |
| `DECISIONS.md` | One append-only entry. |

**Unchanged:**
- the design freeze `959a23f1…6982` and every constant and threshold in it;
- Route B, the OPWS endpoint and estimand;
- the quarantine amendment, the R1 amendment, `ADAPTER_VERSION`, `wp2_m16_adapter.py`, the firewall, stats and resource gate;
- both original plans;
- all frozen pins and historical evidence;
- selector predictions, and any selector-vs-gold reading.

## 6. Restart

The original STOP is `RESUMABLE=False`, and its R00/R01 PASS were obtained with the pre-amendment code. It is therefore **not** acked or resumed. Its state file and STOP report stay in place, and are archived, as permanent evidence.

The dry-run restarts from R00 under `controller/plan_m16_v1_dryrun_r2a.json`, with its own state file `controller_state_dryrun_r2a.json` and report dir `controller_reports_dryrun_r2a`. On PASS it ends with the same `wp2-m16-v1-dryrun` tag and `M16_DRYRUN` LIGHT that the design requires (`ready_pushed` then checks kit → R2A → dryrun).
