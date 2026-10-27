# C6_FINAL_ORACLE_CORRECTIONS_ACCEPTANCE.md — TRACK02 C6 FINAL ORACLE CORRECTIONS (v0.4.0)

**Workspace:** `D:\WP2\active\TRACK02_C6_IMPLEMENT_20261027`
**Runner:** `c6_runner` **v0.4.0** (v0.3.0 preserved byte-for-byte in `work/c6_runner_v0.3.0_preserved/`)
**Mission:** close EXACTLY TWO scientific issues (all-skipped false pass; negative/positive reference semantics)
**UTC generation:** 2026-10-27T08:45Z (session window 08:02Z–08:45Z, local +03)
**Status: PILOT_AUTHORIZATION_READY — 0 candidate executions. No operator freeze/authorization/plan bindings issued.**

---

## 1. Gate result

| Issue | Invariant | v0.3.0 (RED) | v0.4.0 (GREEN) |
|---|---|---|---|
| I1 all-skipped false pass | a junit report with ONLY skipped/xfail/xpass/zero tests can never produce C6 PASS; PASS requires >=1 genuinely executed, non-skipped test | all-skipped junit → `valid=True, ran=2` → **PASS** (repro: real pytest 8.3.4) | `executed=0` → `valid=False, reason=all_skipped` → **BLOCKED**; xfail → `only_xfail` BLOCKED; xpass-only → `only_xpass` BLOCKED; zero → `no_tests` BLOCKED; mixed pass+skip+xfail → `ran=1` PASS |
| I2 negative/positive reference roles | FOUR separate roles: P/P diagnostic (never PASS), P code+T tests = F2P negative baseline (expected failure is evidence, NOT broken env), T code+T tests = P2P positive reference (evaluation-only), generated-code E2E NOT implemented; T code/tests/patch/answers never selector-visible | single reference ran **P code + T tests** yet was called POSITIVE_REFERENCE; F2P-unexpectedly-green → PASS; NONE mode P/P green → PASS; no T-code evaluation existed | F2P run on P code (eval_f2p) + P2P run on **T code** (eval_work); verdict from P2P; F2P recorded `outcome=expected_failure` (never BLOCKED/FAIL for the expected fail); NONE → BLOCKED; roles enumerated in the receipt; T bytes confined to oracle/eval trees |

## 2. Exact counts

- **Full suite after repair: 90 passed, 0 failed** (74 v0.3.0 tests preserved and green + 16 new RED→GREEN: 9 Issue-1 + 7 Issue-2). Log: `work/phase4_full_suite_corrections.log`.
- **RED phase:** 14 failed, 2 passed on v0.3.0 for the new tests (exactly the two defects; the 2 already-green are guards: zero-execution unit + T-byte quarantine).
- **GREEN phase:** 29 passed for the two new files + updated `test_final_red.py`; then full suite 90/90.
- **Issue-1 repro (real pytest 8.3.4 junit):** all-skipped previously `valid=True → PASS`; now `executed=0, reason=all_skipped → BLOCKED`. all-xfail → `only_xfail → BLOCKED`. all-xpass → `only_xpass → BLOCKED`. zero-execution → `no_tests → BLOCKED`. Mixed (1 pass+1 skip+1 xfail) → `executed=1 → PASS` (one genuine test).
- **Issue-2 repro E2E (synthetic env, defect-detecting test):** P2P tree now contains T code (`VALUE = 2`), F2P tree P code (`VALUE = 1`), src P-only; F2P recorded `expected_failure`; NONE mode BLOCKED; NEG mode grounded on a real, labeled F2P run with expected failure → PASS.
- **174-cohort read-only verification: PASS** (`work/c6_final_174_verify_phase4.json`): exactly 174 C4_PASS∩TEST_CHANGE, 174/174 SINGLE_PARENT, years 2018–2026, Old6000 136/38, all five frozen input hashes byte-identical, pilot C5 hashes recomputed from H2 and matching, P3 T-only path confirmed.
- **Real C6 candidate executions: 0.** No docker pulls (one offline probe used the cached pinned base), no GitHub/HTTP, no model/paid APIs, no authorization issued, no C7.

## 3. What changed (minimal, defect-only)

| File | Change |
|---|---|
| `c6runner/oracle.py` | `JunitReport` classifies testcases: `executed` = testcases WITHOUT a `<skipped/>` child; explicit `skipped`/`xfailed` (`<skipped type="pytest.xfail">`)/`xpassed` (terminal summary) counters; `ran` = executed-only; `valid` requires `executed >= 1` and NOT all-executed-was-xpass; explicit reasons `all_skipped`/`only_xfail`/`only_xpass`/`no_tests`/`okay` |
| `c6runner/workspace.py` | `materialize_reference_tree(git_dir, code_rev, oracle_paths, dst)` builds a reference tree from an explicit code revision; new `eval_f2p` dir (P code + T tests) beside `eval_work` (T code + T tests) |
| `c6runner/evaluator.py` | `evaluate_t_only(..., role, code_rev, dst)`: role `f2p` (P code, `ws.eval_f2p`) vs `p2p` (T code, `ws.eval_work`); evidence carries `role` + `tree_semantics` |
| `c6runner/runner.py` | executes BOTH evaluation-only references with the frozen plan passthrough; verdict from P2P (`POSITIVE_REFERENCE`), F2P expected-failure recorded as `negative_baseline_f2p.outcome=expected_failure` (never BLOCKED/FAIL for the expected fail); `NONE` → BLOCKED (diagnostic never PASS); receipt gains `negative_baseline_f2p` + `reference_definition.roles{diagnostic,f2p,p2p}` + `generated_code_e2e: not implemented`; version 0.4.0 |
| `c6runner/verdicts.py` | docstring: roles bound to modes (POSITIVE = P2P T-code tree; NEG = F2P P-code tree); decision logic unchanged |
| `tests/test_final_red.py` | `test_f7_reference_tree_separation` updated to the corrected role contract (P2P tree = T code; F2P tree = P code) |
| `tests/test_final_oracle_corrections.py` (new, 9) | Issue 1 RED→GREEN |
| `tests/test_final_reference_semantics.py` (new, 7) | Issue 2 RED→GREEN |
| `C6_TASK_PLAN.schema.json`, `OPERATOR_COMMANDS.md` | description/runbook updated to the v0.4.0 role semantics |

Untouched: eligibility rules, cohort, C1–C5/Evidence V2, authorization/freeze formats, all other runner logic, all other tests (74/74 still green).

## 4. What did NOT run

No candidate/pilot execution, no docker pull (all probes used cached images; `resolve_image_digest` is offline), no GitHub/HTTP, no model/paid APIs, no C7, no generated-code E2E (explicitly out of scope), no modification of frozen census/ledger (all hashes byte-identical), no operator authorization.

## 5. Next gate (operator; the runner is fail-closed until then)

1. Review + accept `C6_FINAL_PROTOCOL_V4_ORACLE.md`; freeze its bytes in `C6_PROTOCOL_FREEZE.json`.
2. Provision + freeze pilot images: P1 python-3.6-era saleor image with pytest + era wheels (NOT present — ref `C6_PILOT_PRECHECK_3.csv`); P2/P3 extend `sha256:3220486db0d8…b89` with the offline era wheelhouse per `C6_P2_FEASIBILITY_OFFLINE.md` (django~3.2, graphene/graphene-django, pytest~7.x, before_after==1.0.1, freezegun, prices, measurement, pytz, graphql_relay, psycopg2_binary cp39 wheels) + a reachable Postgres service for DB-backed tests.
3. Author `plans/P1.json..P3.json` (`oracle_mode: POSITIVE_REFERENCE`), bind `plan_sha256`, issue the authorization receipt, preflight, then run serially (`OPERATOR_COMMANDS.md`).
4. Review receipts: confirm `oracle_report.ran >= 1` (genuinely executed non-skipped), `negative_baseline_f2p.outcome == expected_failure` (or `unexpected_green` recorded), P2P-based verdict.

**At this point the runner is PILOT_AUTHORIZATION_READY. Nothing in this mission issued execution authority.**