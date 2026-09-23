# WP-2 Oracle Confirmation Report (2026-09-22)

Status: **ZERO API**. Deterministic Oracle Confirmation over the 220
changed-test candidates of the MAIN_297 Saleor census, using isolated worktrees,
per-(task,state) test databases, per-file evaluator runs, and a frozen failure
taxonomy. The 786 sealed Saleor RESERVE outcomes were never accessed.

## Summary counts (all 220 changed-test candidates attempted)

| Category | Count |
|---|---:|
| Attempted (20 strong + 200 modified) | **220** |
| Primary behavioral F2P eligible (`BEHAVIORAL_F2P`) | **8** |
| Symbol-absence F2P eligible (`SYMBOL_ABSENCE_F2P`) | **1** |
| Extended F2P eligible | **9** |
| `P2P_ONLY` nodes (across tasks) | 1,505 nodes / 13 tasks |
| `FLAKY` | 2 |
| `TARGET_ORACLE_INVALID` | 2 |
| `ENV_BROKEN` / `ENV_UNAVAILABLE` | 207 |
| Path-length failures (WinError 206) | 0 (fixed) |

## By original 20/200 class

| Class | behavioral | symbol | p2p-only | env-broken | flaky | target-invalid | other |
|---|---:|---:|---:|---:|---:|---:|---:|
| STRONG (20) | 1 | 0 | 0 | 19 | 0 | 0 | 0 |
| MODIFIED first 60 | 4 | 0 | 0 | 55 | 0 | 1 | 0 |
| EXPANSION 140 | 3 | 1 | 0 | 133 | 2 | 1 | 0 |

## Confirmed behavioral F2P pool

- saleor-rc-05bdc7feb9ac (9 behavioral + 6 symbol nodes)
- saleor-rc-30fe250747ae (1)
- saleor-rc-9057e82cea23 (4)
- saleor-rc-2a59d31fc839 (4)
- saleor-rc-c6220233ccb1 (2)
- saleor-rc-305415e0f8b7 (5 + 8 symbol)
- saleor-rc-367b8038f6b9 (1)
- saleor-rc-a7a2bf4146ba (1)

Symbol-absence eligible: saleor-rc-c7207e71e0d3.

## Attrition flow

```
Census 297
-> changed-test candidates 220
-> attempted 220
-> environment valid 13
-> target stable 9
-> parent discriminative (behavioral) 8
-> parent discriminative (symbol) 1
-> P2P-only 13 tasks / 1505 nodes
```

## Environment breakdown (dominant blocker on this Windows host)

- 207/220 `ENV_BROKEN`: genuine Windows/platform incompatibilities dominate:
  - 13 worktree-add failures because a Saleor cassette filename contains `?`
    (invalid Windows path);
  - native library failures (e.g. `gobject-2.0` from pycairo/pyGObject-era
    deps) on 2020-era commits;
  - Unix-only `resource` module imports in some 2024-2026 commits;
  - Poetry-era build-system / dependency-resolution failures;
  - a few transient network failures during `uv pip install`.
- Every attrition reason is counted and preserved; no task silently dropped.

## Environment-validity gate findings

The audit (`research/wp2/wp2_oracle_environment_validity_audit_2026-09-22.json`)
distinguished genuine unavailability from harness defects. Five harness defects
were found and fixed (per-state DB, per-file evaluator, failure-text
classification, OTHER_REVIEW_REQUIRED flag handling, negative-cache versioning,
path-length). Recovery re-runs confirmed 4 of 5 previously-TARGET_ORACLE_INVALID
tasks as BEHAVIORAL_F2P.

## P2P preparation

`research/wp2/wp2_p2p_candidate_inventory_2026-09-22.json` retains changed-test
P2P-only nodes (pass 3/3 parent and target) as potential preservation tests. The
final P2P oracle is defined later by E2E-G6, not here.

## Interpretation

- The **oracle/data substrate is validated**: executable F2P oracles exist for 8
  tasks (behavioral) + 1 (symbol).
- The confirmed pool (n=8) is far below the n=60 planning target, so
  `WP2_F2P_POOL_SMALL` applies.
- The environment is the dominant blocker on this Windows host; a
  version-aware Saleor environment bundle is the recommended next build step.
- This mission does NOT establish any E2E result; it validates the oracle/data
  substrate only.