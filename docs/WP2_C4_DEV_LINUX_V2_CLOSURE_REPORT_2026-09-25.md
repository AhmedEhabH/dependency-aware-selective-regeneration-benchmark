# WP-2 C4 DEV Linux V2 — Closure Report (2026-09-25)

Status: **C4 COMPLETE 111/111.** Closure audit PASS. This report closes the
DEV changed-test Linux V2 oracle confirmation. No downstream generation,
Smoke, Pilot, or E2E was started.

## 1. Final state

- **111/111** terminal task records (outer-runner DONE), **111 unique** task
  ids, **duplicates = 0**.
- Candidate set = the frozen DEV changed-test candidates (111 of 150 DEV tasks
  with changed-test evidence), same ordering as the frozen DEV census.
- **No rerun** of the 72 tasks completed before the maintenance boundary
  (resume skipped the persisted completed set; 39 new tasks executed).

## 2. Closure audit (Section P) — PASS

- Expected candidates 111 = terminal records 111 = unique ids 111; expected
  omitted 0; unexpected included 0; set equality TRUE.
- Every terminal task has provenance.
- `per_test_dev_v2.jsonl`: **10,155** records, 0 invalid/partial lines,
  0 orphan task ids, 0 duplicate (task,node) records.
- JUnit manifest: **111 rows**, 111 unique, none missing; 86 junit dirs with
  XML (25 tasks without junit = 24 env-failed + 1 executable-no-junit).
- Environment/install failures reported **separately** from executable tasks
  (task-level `DONE` does not imply environment success).

## 3. Task-level summary (Section Q)

| Metric | Count |
|---|---|
| Total attempted | 111 |
| Terminal / completed | 111 |
| Environment/install failed (all-zero + collection failure) | 24 |
| Executable | 87 |
| Tasks with ≥1 BEHAVIORAL_F2P | 43 |
| Tasks with ≥1 SYMBOL_ABSENCE_F2P | 6 |
| Primary behavioral eligible | 43 |

## 4. Node-level totals

- BEHAVIORAL_F2P: **538**
- SYMBOL_ABSENCE_F2P: **25**
- PARENT_COLLECTION_ERROR: **0**
- FLAKY: **510**
- TARGET_ORACLE_INVALID: **3,727**
- P2P_ONLY: **5,355**
- OTHER_REVIEW_REQUIRED: **0**

## 5. Era breakdown

| Era | attempted | env-failed | executable | primary-beh tasks | BEH nodes | SYM nodes | P2P nodes | TARGET_INVALID |
|---|---|---|---|---|---|---|---|---|
| py38 | 10 | 0 | 10 | 2 | 108 | 2 | 490 | 863 |
| py39 | 67 | 9 | 58 | 28 | 280 | 19 | 3371 | 2777 |
| py312 | 34 | 15 | 19 | 13 | 150 | 4 | 1494 | 87 |

Era behavioral-task rates: py38 0.20, py39 0.42, py312 0.38.

## 6. Amendment-M hard-stop check (era yield)

py38 yield (0.20) is lower than py39/py312 (~0.4). Evidence that this is NOT a
harness artifact: the same frozen harness demonstrably produced behavioral F2P
on a py38 task in the B3 dry run (`05bdc7feb9ac`, py38, 24-25 BEHAVIORAL);
py38's 863 TARGET_INVALID nodes show tests attempt execution but fail on the
2020-era native dependency chain (weasyprint/pango), consistent with the
documented dry-run finding. The difference is era-dependency attrition, not a
harness artifact. **Hard stop NOT triggered.**

## 7. Evidence / provenance

- Semantic freeze identity: `01c3430f221e70fb75ff4dbf1c0e5093a3c1305f2c870e1b20e2b6c4b64dd337`
  (classifier files only; unchanged).
- Persistence revision: `c4-persistence-v2-2026-09-23`.
- Frozen era images (unchanged): py38 `1cc60658b6a2`, py39 `ddc08d7e6855`,
  py312 `0c185699947d`. No rebuild, no pull.
- PostgreSQL: `postgres:15-alpine` digest
  `f7d23353e1b15400d22ebe31189f4d314b87a4c129cc400c8c2d8d4ca127bf81`,
  container `wp2-pg`, port 5433, `saleor/saleor/saleor`,
  `fsync=off, synchronous_commit=off, full_page_writes=off`; `pg_isready` PASS.
- Worker count: **1**; early exit DISABLED; 3/3 policy unchanged; timeout
  policy unchanged.
- Test-patch rule SHA: `f64ff583daea4b8bdec7f40293069cb009494a569a75c92d34819cd10030a969`.

## 8. Maintenance boundary

- C4 stopped at 72/111 for storage maintenance; 144 completed-C4 worktrees
  removed; WSL shutdown + fstrim + VHDX compact (59.80 → 52.54 GiB);
  post-maintenance resume at 72 → 111. Page cache was reset by the shutdown;
  post-maintenance task wall-times may reflect cold caches (transparent note,
  not a reweighting reason).

## 9. Storage final state

- Windows C: **free 42.96 GiB** / used 433.06 GiB (of ~476 GiB).
- ext4: `/dev/sdd` 47G used / 909G available.
- `/opt/wp2_v2/worktrees`: **4.0 GB** (39 post-resume tasks' completed
  worktrees remain; evidence fully persisted; left in place as least-invasive;
  the established evidence-safe `git worktree remove` cleanup is available if
  disk management is later required).
- `wp2-uv-cache` present; era images present; no volume/system prune.

## 10. Guards / untouched pools

- MAIN generation **QUARANTINED** (no generation/Smoke/Pilot/tuning on MAIN).
- `INTERNAL_TEST` **UNTOUCHED**.
- Sealed `RESERVE` (786) **UNTOUCHED**.
- No LLM/API/embedding/AG16 call; $0.00 scientific budget.

## 11. C2 historical honesty (unchanged)

- MAIN 220 / outer DONE 220 / env-install-failed 60 / executable 160 /
  ≥1 BEHAVIORAL 71 / ≥1 SYMBOL 17. Node totals as recorded. C2 JUnit rescue
  covered 159/220 tasks. C2 was NOT rewritten; C2 identity histories are kept
  separate from C4.

## 12. Artifacts produced (this phase)

- `research/wp2/oracle_confirmation_linux_v2_2026-09-23/per_task_dev_v2.jsonl` (111)
- `research/wp2/oracle_confirmation_linux_v2_2026-09-23/per_test_dev_v2.jsonl` (10,155)
- `research/wp2/oracle_confirmation_linux_v2_2026-09-23/junit/` + `junit_manifest_2026-09-23.tsv`
- `research/wp2/oracle_confirmation_linux_v2_2026-09-23/summary_dev_v2.json`
- `research/wp2/oracle_confirmation_linux_v2_2026-09-23/c4_progress.json` (COMPLETE)
- `research/wp2/oracle_confirmation_linux_v2_2026-09-23/c4_post_maintenance_pre_resume_snapshot_2026-09-25.json`
- `logs/c4_orchestrator.log` (C4-specific; WP2_MASTER_LOG now honored)
- `docs/WP2_C4_PROVENANCE_HARDENING_2026-09-23.md`

## 13. Exact next scientific action (NOT executed)

DEV split assignment (amendment F): apply the frozen salted split
(`DEV_TRAIN_ENG` vs `DEV_TRAIN_ASSAY_HOLDOUT`, `DEV_VALIDATION` separate) to
the 43 primary-eligible + 6 symbol-absence DEV oracle tasks, and finalize D1/D2
node-level outcomes from the completed C2+C4 sweeps. This is planning only; no
generation, Smoke, Pilot, Gold/Placebo, or selector E2E is authorized in this
phase.