# WP-2 Windows V1 → Linux V2 Reconciliation (2026-09-23)

Status: **RECONCILIATION.** Windows v1 evidence is preserved
(`research/wp2/oracle_confirmation_2026-09-22/`); V2 evidence is new
(`research/wp2/oracle_confirmation_linux_v2_2026-09-23/`). V1 is platform-limited
evidence, not "wrong".

## 1. Headline

| Metric | Windows V1 | Linux V2 |
|---|---|---|
| Attempted (changed-test MAIN candidates) | 220 | 220 |
| Environment-valid / executable | 13 | 160 |
| Primary behavioral F2P eligible tasks | 8 | **71** |
| Symbol-absence F2P tasks | 1 | 17 |
| Extended F2P eligible tasks | 9 | 71 |
| Env-broken / env-install-failed | 207 | 60 |

V2 node-level totals: 731 BEHAVIORAL_F2P, 64 SYMBOL_ABSENCE_F2P, 1636 FLAKY,
7946 TARGET_ORACLE_INVALID, 10517 P2P_ONLY, 0 PARENT_COLLECTION_ERROR.

## 2. Why V1 was environment-limited on Windows

V1 attrition on this Windows host: 207/220 ENV_BROKEN, dominated by:
- historical cassette filenames containing `?` (invalid NTFS paths → worktree add
  failures);
- Unix-only `resource` module imports;
- native library failures (e.g. gobject-2.0 / weasyprint pango chain) in
  2020-era commits;
- Poetry-era build/install failures.

## 3. What Linux V2 changes

- Historical checkouts live on a Linux ext4 filesystem (WSL Ubuntu-24.04), so
  `?` cassette filenames check out correctly (verified for `24f9b244d6bc`).
- `resource` works (verified: `65643ec7c37f` now yields 2 SYMBOL_ABSENCE + 10
  P2P nodes).
- Era-controlled container images (per Python era) with an evidence-informed
  system-library superset (libmagic, pango/cairo/pixbuf, etc.) recover most
  2020-era collections.
- 2026-era (Python 3.12) tasks install via the commit's own metadata
  (runtime deps + declared test deps), yielding confirmed behavioral F2P.

## 4. Residual Linux environment attrition (V2)

60/220 tasks remain environment-install-failed (all-zero node counts,
`task_collection_failure=True`): py312 × 33, py39 × 25, py38 × 2. These are
genuine commit-era dependency resolution / native-lib issues (e.g. 2026-era
dev-group conflicts, 2020-era native chains), not a harness defect. They are
excluded task-wise; they do not invalidate the 71 eligible tasks.

## 5. Reclassification examples (old label → new V2 outcome)

- `saleor-rc-05bdc7feb9ac`: V1 BEHAVIORAL_F2P → V2 BEHAVIORAL_F2P (eligible,
  24 behavioral + 1 symbol nodes, 268 nodes).
- `saleor-rc-65643ec7c37f`: V1 ENV_BROKEN (resource module) → V2 executable
  (2 SYMBOL_ABSENCE + 10 P2P).
- `saleor-rc-24f9b244d6bc`: V1 ENV_BROKEN (`?` worktree add) → V2 executable
  (FLAKY single node; `?` checkout now works on ext4).
- `saleor-rc-ab6c29ba265d`: V1 ENV_BROKEN (gobject) → V2 collection recovered
  (276 nodes) but execution infeasible (native chain) — documented.
- `saleor-rc-3cac33590b90` (2026/Py3.12): V1 not-executable → V2 BEHAVIORAL_F2P
  eligible (4 behavioral + 142 P2P).

## 6. Attrition flow (V2)

```
Census 297 -> changed-test candidates 220 -> attempted 220
-> environment-install-failed 60
-> executable 160
-> target stable (>=1 behavioral node) 71 tasks / 731 nodes
-> symbol-absence tasks 17 / 64 nodes
-> P2P nodes 10517 across executable tasks
```

## 8. C2 test-artifact rescue (2026-09-23)

Before any worktree cleanup, all recoverable C2 test artifacts were rescued into
one compressed archive OUTSIDE the worktrees, next to the C2 evidence root:

- Archive: `research/wp2/oracle_confirmation_linux_v2_2026-09-23/c2_junit_rescue_2026-09-23.tar.gz`
- SHA-256: `ebf749c1599929def30a29395d784f1ce3cf56cb2f3136f91d1d6f6dcef2884b`
- Entries: 3312 (2994 junit XML/log files, 519.8 MB raw → 8.0 MB gz)
- Manifest: `c2_artifact_manifest_2026-09-23.tsv` (317 worktree rows → 159/220 tasks)
- **C2_TASKS_WITH_JUNIT = 159/220.** The 61 tasks without JUnit are exactly the
  60 environment-install-failed tasks plus 1 additional task whose runs
  produced no JUnit. JUnit/per-test gap: CLOSED for 159 tasks; CONFIRMED ABSENT
  (no artifacts exist) for the remaining 61.
- `per_test` node-level records (per-node classification outcomes) remain
  NOT-persisted for C2 (counts-only); the rescued JUnit XML provides the
  per-file/per-run outcomes at the JUnit level. This is stated as the honest
  protocol gap; it is NOT regenerated and C2 semantics are unchanged.

## 9. Caveats

- Per-run flakiness remains high (1636 FLAKY nodes) with `--reuse-db` across 3
  reps; stability semantics are intact (3 target + 3 parent runs) but flaky-node
  counts should be read as environment/DB-related variance to investigate in
  the full sweep, not as oracle signal.
- V2 results were produced under the frozen V2 harness (see
  `harness_v2_freeze_2026-09-23_REVISED.json`). No final V2 results mix semantic
  harness versions.