# T12 M02-D3 — REAL per-arm F2P execution bridge (engineering-only)

Mission: `T12_M02_D3_EXECUTABLE_F2P_GATE_20261027` · Track 1.2 · 2026-10-27

## What this adds on top of D2

`scripts/t12_m02_execute_f2p.py` — the first REAL, provable per-arm F2P
execution entrypoint:

| mode | behavior |
| --- | --- |
| `preflight` | read-only fail-closed admission (branch/HEAD, matrix/plan FULL SHA pins, engine stage pin hashes, RD-8/RD-9 artifact state, eligibility NOT_RUN). exit 4 with typed stops. |
| `dry-run` | 13-arm NOT_RUN plan + a CONCRETE fully-resolved prospective physical run plan for the frozen first pilot (4 arms, 3 nodes x 3 reps = 9 JUnit/arm, 36 total, USD 0.00, requests 0). Never executes. |
| `run` | fail-CLOSED. Refuses unless a typed signed RD-8 `ADOPT_PILOT_ONLY` decision, a separate RD-9 authorization (exclusivity window + arm set + wall cap), a zero-API budget, and per-arm worktree inputs exist. In D3 the outcome is always `STOP_NOT_AUTHORIZED`, executed=false. |

All three modes read the SAME immutable plan and frozen source paths
(frozen worktree `opws-runtime-compat-2026-10-26`; no fake CLI flags).

## Real bridge (proved against frozen sources; see DRIVER_REAL_BRIDGE.md in the
mission evidence)

materialize (frozen `opws_phase3b_patch_materialize.py` argv, engineering
record) → per-arm execution tree at `effective_tree_oid` (REQUIRED INPUT,
verified read-only) → `harness_v3.run_state_v3(era_key='py312', …,
test_files=3 frozen F2P nodes, …, isolated=OpwsIsolatedRuntime(...))` → 9
JUnit/arm (3 nodes x 3 reps) → `t12_m02_receipts` per-arm + bundle validation →
teardown proof (zero `opws_m3b_*` DBs). The m3b smoke is single-node and is
NOT the 3-node runner. Classification/test-authority bytes go to the
materializer ONLY (oracle boundary); no selector or generation prompt ever
receives them (unit-tested).

## Fail-closed guarantees

- No partial PASS: an arm is PASS only when every stage verified; NEG's
  expected assertion-failure is a typed control event, never ordinary FAIL
  and never PASS.
- No retries; fresh out dir per execution; run requires artifacts that do not
  exist yet in D3, so it cannot self-authorize.
- Mocks appear only in unit tests; the execution path imports the real frozen
  engine functions.

## Verification (D3)

`python -m unittest tests.unit.wp2/test_t12_m02_*` → 189 passed (py 3.13);
`python -m pytest tests/unit/wp2/test_t12_m02_*.py` → 189 passed (py 3.11);
ruff check 0 findings; mypy strict Success; py_compile PASS; git diff --check
clean. New module `tests/unit/wp2/test_t12_m02_execute_f2p.py` (33 tests):
RD-8 gate, RD-9 grant/window, budget zero-API, unknown arm, alias-pair
physical identity, oracle boundary, wrong-node pin, tampered matrix/plan
hashes, partial engine failure, CLI exit codes, out-dir reuse refusal.

## Status

ENGINEERING PASS — `REAL_F2P_BRIDGE_READY_FOR_RESEARCHER_GATES`. SCIENCE
NOT_RUN: all 13 prospective arms `NOT_RUN`, 0 model requests, USD 0.00. The
only two remaining blockers are researcher decisions: RD-8
(ADOPT_PILOT_ONLY/REJECT with pinned hashes) and RD-9 execution
authorization (exclusivity + wall cap). P2P stays NOT qualified (RD-3).
Proposal artifacts: `RD8_PILOT_DECISION_PROPOSAL.md`,
`AUTHORIZATION_SCHEMA_PILOT.json` (EMPTY template), `FIRST_PILOT_DESIGN.md`,
`FIRST_PILOT_GATE.json` in the mission evidence directory.
