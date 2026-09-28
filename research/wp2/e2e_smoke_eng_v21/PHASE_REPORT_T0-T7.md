PHASE_REPORT — T0-T7 (v21 build complete)
Mission: MISSION-12B V2.1 AUTONOMOUS_UNATTENDED

T0 PASS: v21 namespace + HOLD + design_v21.json (14 tasks, 4 arms, scopes,
model/route/sampling, transport_v21, $2 ceiling, workers=1, d220 rule).

T1 PASS: TRANSPORT_V21 module + 12 tests (4 attempts, 5/20/60, HOLD gate,
pacing, byte-identical retries, retryable/non-retryable classification).
Committed.

T2 PASS: generation driver + 6 tests (max-new counts new terminal only, resume
never deletes, v21 cache only, ledger fsync, GENERATION_FAIL preserves calls).
Committed.

T3 PASS: variance runner + 6 tests (3 GOLD x 2 replicates, distinct evidence
paths, per-replicate cache namespace, no overwrite, HOLD honored, ledger merge).
Committed.

T4 PASS: fail-closed freeze builder + 5 tests (null Harness SHA hard FAIL,
missing HOLD FAIL, scope hash mismatch FAIL, model mismatch FAIL, v2 root
guard). Real build produced smoke_v21_freeze.json (56 planned, 1 NO_SCOPE).
Committed.

T5 PASS: unique-diff evaluation planner/runner + 6 tests (per-task dedup,
cross-task no-dedup, variance included, plan hash stable, no provider deps).
Committed.

T6 PASS: mechanical summarizer/gates + 5 tests (per-arm accounting, primary
NEXT rule, secondary d220 never changes NEXT). Committed.

T7 PASS:
- v21 unit tests 34/34; existing v1/v2 instrument tests 45/45; total 79.
- ruff clean; py_compile clean; git diff --check clean.
- secret scan clean; import/dependency audit OK.
- v1/v2 immutability restored and verified (T4 test isolation fix recorded in
  DECISIONS.md; v1 scope hashes 4/4 match v1 freeze).
- build_ready.json verdict BUILD_V21_READY.
- Committed T0-T7 allowed files and pushed. HEAD==origin/main==5060f7fe.

NEXT: C1/C2/C3 prospective controls (zero API) under frozen control inputs.
