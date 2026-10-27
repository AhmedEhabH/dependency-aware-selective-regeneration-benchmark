# C6_FINAL_ACCEPTANCE.md — TRACK02 C6 Execution-Blocker Repair (v0.3.0)

**Workspace:** `D:\WP2\active\TRACK02_C6_IMPLEMENT_20261027`
**Runner:** `c6_runner` **v0.3.0** (v0.2.0 preserved as versioned history; diff = this mission only)
**UTC generation:** 2026-10-27T07:43Z
**Status: PILOT_AUTHORIZATION_READY — C6 EXECUTION NOT AUTHORIZED (no operator freeze, no authorization receipt, no operator-issued plan bindings yet). 0 candidate executions this session.**

---

## 1. Gate result

| Gate | Result | Evidence |
|---|---|---|
| F1 broken T-only evaluation | **REPAIRED** | RED: `AttributeError: 'NoneType' ... 'image'` → GREEN: plan passed through; docker_run fail-closed |
| F2 false-PASS risk | **REPAIRED** | evaluator_error → BLOCKED; genuine reference failure → FAIL; verdict computed AFTER reference |
| F3 spoofable pytest result | **REPAIRED** | machine-readable junit-xml oracle only; forged `pretend result: 1 passed` → BLOCKED |
| F4 environment identity incomplete | **REPAIRED** | resolved interpreter@version + wheelhouse id + immutable image digest bound into ENVIRONMENT_ID; drift → GLOBAL STOP ENV_DRIFT |
| F5 docker timeout cleanup | **REPAIRED + PROVEN** | cidfile/label identity, kill/wait/rm -f, orphan sweep; REAL docker probe: 0 orphans before/after/settle |
| F6 input binding | **REPAIRED** | frozen manifest roles; any source substitution → C6_STOP INPUT_BINDING_MISMATCH |
| F7 reference & oracle semantics | **REPAIRED** | reference tree = P code + FULL M/A contract T bytes (evaluation-only); src = P bytes only; no PASS from legacy P tests alone |

## 2. Exact counts (what ran and what was verified this session)

- **RED reproduction (Phase 1):** 13/13 deterministic regression tests reproduced the seven findings on v0.2.0 (61 pre-existing tests stayed green alongside).
- **Full suite after repair (Phase 3):** **74 passed, 0 failed** (61 pre-existing + 13 RED→GREEN). Log: `work/phase3_full_suite_final.log` (74 PASSED entries, 0 FAILED/ERROR).
- **Real-Docker timeout/cleanup probe:** 1 disposable probe container (`probe-nocandidate-*`, local cached image, `--network none`, 0 network bytes, 0 candidate bytes): kind=timeout, rc=137, container_id recorded via cidfile, killed/waited/removed all true, **orphans 0 / 0 / 0**. Receipt: `work/c6_final_docker_timeout_receipt.json`.
- **174-cohort read-only verification:** PASS — exactly 174 C4_PASS∩TEST_CHANGE rows; all C4=C4_PASS, C5=TEST_CHANGE; 174/174 SINGLE_PARENT; years 2018–2026; 136 Old6000 / 38 non; all five frozen input hashes byte-verified (ledger `67C47930…` unchanged). Receipt: `work/c6_final_174_verify.json`.
- **Adversarial checklist (Phase 3):** forged stdout cannot PASS ✓, T-only evaluator error cannot PASS ✓, T-only genuine failure cannot PASS (→FAIL) ✓, real evaluator invocation receives the exact frozen plan ✓, P/T reference + oracle separation ✓, image/interpreter drift stops execution (ENV_DRIFT) ✓, timeout kills the actual container with no orphan (unit + real probe) ✓, CLI input substitution cannot bypass frozen hashes ✓, missing/invalid authorization stops execution ✓ (existing suite), valid synthetic positive/negative controls ✓, 174/174 identities and C1–C5 decisions unchanged ✓.
- **No real candidate test was executed.** Number of candidate executions: **0**.

## 3. Deliverable inventory

1. `C6_FINAL_RED_GREEN.csv` — 13 RED→GREEN rows with observed failure modes and green evidence.
2. `C6_FINAL_ACCEPTANCE.md` — this file.
3. `C6_FINAL_PROTOCOL.md` — next versioned protocol (v0.3.0) + operator freeze/plan-hash/authorization procedure.
4. `C6_PILOT_PRECHECK_3.csv` — P1/P2/P3 environment and image resolution (explicit, no silent Track01 reuse).
5. `C6_FINAL_RISK_DELTA.md` — risk delta vs the V2 register.
6. `PROGRESS.md`.
7. `c6_runner/` v0.3.0 (code + 74-test suite + `frozen_inputs.json` v2 roles manifest).
8. `work/phase3_full_suite_final.log`, `work/c6_final_docker_timeout_receipt.json`, `work/c6_final_174_verify.json`, `work/PHASE_A_RED_OBSERVATIONS_FINAL.md` (new), `work/c6_final_docker_timeout_probe.py`, `work/c6_final_174_verify.py`.
9. `research review_HANDOFF_FINAL.zip` + `SHA256SUMS.txt` + `PASTE_TO_research review_FINAL.txt`.

## 4. What did NOT run

- No C6 pilot/batch candidate execution (STOP held: operator freeze + authorization + bound plans not issued).
- No Docker pull (all probes used the 13-day-cached local image; `resolve_image_digest` is offline-only).
- No GitHub/HTTP requests. No model/paid APIs. No C7. No modification of any frozen census/ledger evidence (all five frozen hashes byte-identical).

## 5. Next gate (operator only; runner is fail-closed until then)

1. Review + accept `C6_FINAL_PROTOCOL.md`; freeze its bytes (sha256) in `C6_PROTOCOL_FREEZE.json`.
2. Provision the pilot images (P1: python-3.6.x-era image with pytest + era wheels; P2/P3: extend `sha256:3220486db0…b89` with pytest + era wheels), freeze each `image_digest`.
3. Author per-task `plans/P1.json,P2.json,P3.json` (schema `C6_TASK_PLAN.schema.json`), compute each `plan_sha256` (`python -m c6runner.cli --plan-sha plans\PN.json`).
4. Issue `C6_AUTHORIZATION_RECEIPT.json` with `task_bindings` (write-then-hash).
5. Run preflights then the 3-task pilot serially (`OPERATOR_COMMANDS.md`). Review receipts; larger batches only after.

At this point the runner is **PILOT_AUTHORIZATION_READY**. It is NOT authorized itself; nothing in this mission issued execution authority.