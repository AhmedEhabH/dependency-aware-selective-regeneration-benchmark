# R4 Poetry Closure Successor — Mission Report

**Mission:** `M17_D7_R4_POETRY_CLOSURE_SUCCESSOR_QUALIFICATION`
**Verdict:** `PASS_POETRY_CLOSURE_SUCCESSOR_READY_FOR_FULL144_REFREEZE`
**Branch:** `parallel/d7-r4-poetry21-closure-successor-2026-10-14`
**Starting HEAD:** `783903d0fc22d1378291cf791c175d39eaa500be`
**Session:** `ses_ec4f3fb4fffew8o1pZ5RqlS38H`

## Summary

A general, authority-backed correction for the Poetry dependency-closure
divergence discovered by the real Full-D7 execution was established,
implemented, tested, audited population-wide, and behaviourally qualified.
Full D7 was NOT relaunched. No OPWS. No download / pull / build.

## 1. Exact authority ruling implemented

`C_LOCK_CLOSURE_PARSER_DIVERGENCE` — for D7 behavioral execution the frozen
install-route authority governs runtime dependency semantics. For
`LOCK_FRAGMENT_MAIN_PLUS_DEV` the required behavioral closure is the COMPLETE
applicable main+dev dependency set defined by the frozen R3 behavioral
authority and `D7_REQUIRED_CLOSURE_AUDIT`. The successor must not silently
reduce that route to a package-marker-gated subset.

## 2. Correct implementation ownership layer

D7 install-route semantics layer — `runtime_pins()` in the qualified Attempt-6
runner (`scripts/r4_behavioral_calibration_n12_r2.py`), reused unchanged by the
Full144 driver. The successor projection lives in
`src/benchmark/wp2/env_r4/route_closure.py` and reuses the frozen R3 closure
implementation (`d7_r3_closure.py`). The generic R4-B parser
(`uv_adapter.py`) and the frozen R4 shared interface (`contracts.py`) remain
byte-for-byte unchanged.

## 3. Production files changed

| File | Change |
|---|---|
| `src/benchmark/wp2/env_r4/route_closure.py` | NEW — successor route-aware closure projection (reuses frozen R3 closure semantics) |
| `scripts/r4_behavioral_calibration_n12_r2.py` | `runtime_pins()` branches for `LOCK_FRAGMENT_MAIN_PLUS_DEV` poetry to the successor complete main+dev closure; other routes unchanged |

## 4. R3 vs old-R4 vs successor result for 36A9

| authority | runtime closure |
|---|---|
| frozen R3 (owner review) | 253 |
| frozen R3 (actual calibration, both platform exclusions) | 252 |
| old R4 (R4-B marker-gated) | 18 |
| **successor** | **252** |

## 5. Population audit — 144 units / 219 tasks

* exactly 144 units accounted; exactly 219 tasks accounted; zero silent skips;
  no unknown route; **0 semantic disagreements**.
* **actual changed scope = 3 units** (measured, not assumed):
  `vu-0d8ddec94417`, `vu-8228f26085f6`, `vu-3a7ebc8e23c7`.
* all other units unchanged or reconciled via frozen authorities
  (R3 platform exclusions / D4-R5 codecov recovery).

## 6. Delta artifact readiness

235 unique added requirements across the 3 changed units; **0 unresolved**
newly-required runtime artifacts (qualified local R4-A resolution).

## 7. Real behavioral qualification

New root `D:\WP2\runs\r4-poetry-closure-successor-qualification-2026-10-14`
(never reused old Full-D7 evidence). 6 units, sequential, exact frozen gates:

| idx | unit | route | result | pins |
|---|---|---|---|---|
| 1 | vu-0d8ddec94417 | LOCK_FRAGMENT_MAIN_PLUS_DEV | **PASS** | 252 |
| 2 | vu-8228f26085f6 | LOCK_FRAGMENT_MAIN_PLUS_DEV | **PASS** | 248 |
| 3 | vu-3a7ebc8e23c7 | LOCK_FRAGMENT_MAIN_PLUS_DEV | **PASS** | 248 |
| 4 | vu-e4998719ee01 | LOCK_FRAGMENT_MAIN_PLUS_DEV (control) | **PASS** | 233 |
| 5 | vu-b68ee1b3ad18 | LOCK_FRAGMENT_MAIN_PLUS_DEV (control) | **PASS** | 232 |
| 6 | vu-117d7bd068d5 | V2_EDITABLE_PLUS_LOCK_DEV (control) | **PASS** | 232 |

All frozen gates verified: exact image immutable IDs (998e20c5… / 24b7945d…),
`--network=none` → NETWORK_UNAVAILABLE, install rc=0, pip check rc=0, no
toolhouse contamination, no native failures, `import saleor` rc=0, manage.py
rc=0, pytest collection rc=0.

## 8. Targeted tests / tooling

* 20/20 successor tests (P1–P10) pass.
* R4-B adapter + R4 contract suites still pass (94 total).
* `py_compile` PASS; Ruff PASS; mypy `--strict` PASS; `git diff --check` PASS.
* Full suite NOT run (out of scope per mission).

## 9. Frozen invariance

`FROZEN_INVARIANCE_PASS` — population identity/order, Python assignment,
native profiles, execution-image IDs, runtime-clean binding, R4-C semantics,
source-fidelity, R4-E recovery, historical lock bytes, failed Full-D7
evidence, N12 accepted evidence all unchanged.

## 10. Exact next gate

`M17_D7_R4_FULL144_SUCCESSOR_REFREEZE` (NOT executed in this mission).

## 11. Full D7

**Full D7 was NOT relaunched.** The failed Full-D7 evidence
(`D:\WP2\runs\r4-full-d7-144-2026-10-14`) is byte-unchanged.