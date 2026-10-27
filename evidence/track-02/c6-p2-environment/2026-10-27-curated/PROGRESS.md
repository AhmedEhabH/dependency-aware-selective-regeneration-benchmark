# PROGRESS.md — TRACK02 C6 P2 HISTORICAL ENVIRONMENT UNBLOCK

Workspace: `D:\WP2\active\TRACK02_C6_IMPLEMENT_20261027`
UTC (this session): 2026-10-27 08:30Z–11:30Z · NEW Pi session (mission file
`C6_P2_ENVIRONMENT_UNBLOCK.md`). Prior missions (v0.3.0 repairs, v0.4.0 oracle
corrections 80 tests/90-test suite) are preserved and UNTOUCHED; C4/C5 and the
90 tests were NOT repeated.

## Frozen state (re-verified, unchanged)

| Item | Value | Evidence |
|---|---|---|
| Commits examined | 22,699 | D0_COMMITS count == ledger rows |
| Frozen candidates | 174 (C4_PASS ∩ TEST_CHANGE, SINGLE_PARENT; Old6000 136/38) | ledger hash `67C47930…` byte-identical |
| Runner | v0.4.0, 90/90 PASS record preserved | `c6runner/__init__.py`; prior suite log untouched |
| Frozen input hashes | F1–F6 all MATCH | `frozen_inputs.json` + fresh SHA-256 re-verify |
| Real C6 executions | 0 | — |
| P2 pilot | T `06d25ce2…5e83`, P `5b0e5206…8a85`, runtime.txt `python-3.9.14` | bare store + manifests at P/T verified |

## Status summary (this mission)

| Phase | Status | Evidence |
|---|---|---|
| T1 inventory (images/wheelhouse/manifests) | **PASS** | base `sha256:3220486db0…b89` present (Deb 12, py3.9.25); wheelhouse/py39 2,533 wheels; reqs@P 170 pins (150 exact / 16 sdist / 3 patch / 1 win32-only); poetry.lock 240 pkgs |
| T2 Python compat (3.9.25 vs 3.9.14) | **RESOLVED** | CPython 3.9 bugfix line, patch-agnostic `cp39`/`py3` wheels, closure+setup PASS on 3.9.25; exact identity NOT claimed; plan freezes 3.9.25 (`C6_P2_PYTHON_COMPAT.md`) |
| T3 pinned historical image | **PASS** | **r3 = `sha256:4b41010cadabc8e5b9d09c1207f32ebbc59dbad72662e01c91f415f6a4ee6919`**; 237 pkgs offline (django 4.0.8, pytest 7.1.3, psycopg2 EXACT 2.9.4, promise 2.3); Dockerfile(r3)+hash-pinned offwh subset; ledgers recorded |
| T4 PostgreSQL under `--network none` | **RESOLVED** | same-container NOT offline-feasible (evidence); sidecar `postgres:15-alpine` (digest `9b4593c6…`) + named volume + unix socket, both `--network none`, psycopg2/dj_database_url connect **PASS**; loopback works under `--network none`; drvfs can't carry sockets |
| T5 non-candidate probes | **PASS** | closure: django.setup OK, contract module import OK; integration (ORM+searchvector+plugins) PASS; isolation: network BLOCKED, rootfs RO(30), mem rc137, pids cap, scratch rw; cleanup orphans 0 (`T5_PROBES_RECEIPT.json`) |
| T6 P2 TaskPlan + SHA256 | **PASS** | `plans/P2.json` (schema-valid) → canonical `382E9280998B3B18BEED9B2FB95320CE9125C0DD4C7B830F6DD0FA4E91B53C88` via runner CLI; resources frozen |
| T7 PowerShell operator runbook | **PASS** | `P2_OPERATOR_FREEZE_AND_EXEC.ps1` phases 0–3 (syntax verified); v2 example plan with env+postgres |
| Final verdict | **P2_ENV_QUALIFIED — gated** | env + image + DB mechanism PROVEN; first pilot requires operator ratification of the scoped runner delta v0.4.0→v0.5.0 (`C6_P2_RUNNER_DELTA_PROPOSAL.md`); if rejected → STOP `runner_db_service_capability_absent` |

## Deliverables (this mission)
`C6_P2_ENV_QUALIFICATION.md`, `C6_P2_PYTHON_COMPAT.md`,
`C6_P2_RUNNER_DELTA_PROPOSAL.md`, `P2_OPERATOR_FREEZE_AND_EXEC.ps1`,
`plans/P2.json`, `plans/P2_v050.example.json`,
`work/p2_env_unblock/T5_PROBES_RECEIPT.json`, probe scripts + build context
(`work/p2_env_unblock/build_img/` incl. `offwh/SHA256SUMS.txt`),
`RESEARCH_HANDOFF.md`, `SHA256SUMS.txt`, `local transfer note (not published)`,
`local handoff archive (not published)` (path/sha printed in `local transfer note (not published)`).

## Accounting
| Item | Value |
|---|---|
| Time | ≈ 3.0 h wall active |
| Disk | ≈ 135 MB new artifacts; 366 GiB free |
| Network | reported honestly: docker build bootstrap pulled the buildkit driver once; one digest-FROM attempt hit docker.io metadata (access denied, no bytes); pip 0 network (`--no-index`); all probes `--network none`; no model/paid APIs (0 cost) |
| Docker | builds r1/r2/r3; ~12 disposable probe containers (all removed); 0 orphans; 1 named volume (removed) |
| Candidate executions | 0 |
| Frozen inputs | 0 mutations |

## NEXT decision (single gate)
Ratify `C6_P2_RUNNER_DELTA_PROPOSAL.md` (v0.4.0→v0.5.0: plan `env`+`postgres`
fields, docker service orchestration, new tests, one suite re-run) and the
unchanged `C6_FINAL_PROTOCOL_V4_ORACLE.md`, then
`pwsh -File P2_OPERATOR_FREEZE_AND_EXEC.ps1 -Phase 1` → `-Phase 2` → author
`plans\P2_v050.json` → re-sign → `-Phase 3 -Authorized YES` → **FIRST REAL C6
PILOT**.