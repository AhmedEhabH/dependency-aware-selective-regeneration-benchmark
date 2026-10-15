# R4 Poetry Closure Successor — Authority Decision

**Mission:** `M17_D7_R4_POETRY_CLOSURE_SUCCESSOR_QUALIFICATION`
**Classification:** `C_LOCK_CLOSURE_PARSER_DIVERGENCE`
**Session:** `ses_ec4f3fb4fffew8o1pZ5RqlS38H`

This document records the internally-consistent authority decision required by
S1 of the mission. Production implementation is prohibited until this decision
is consistent, which it now is.

---

## 1. Authority precedence (exact)

| # | Authority | Source | Binding rule |
|---|-----------|--------|--------------|
| 1 | **Owner ruling (this mission)** | mission authorization | For D7 behavioral execution the frozen install-route authority governs runtime dependency semantics. `LOCK_FRAGMENT_MAIN_PLUS_DEV` requires the **COMPLETE applicable main+dev** dependency set. `V2_EDITABLE_PLUS_LOCK_DEV` shares the frozen complete-main+dev authority and must be audited for the same divergence. `UV_EXPORT` / `REQ_MAIN_PLUS_LOCK_DEV` unchanged unless their own authority proves a violation. |
| 2 | **D7_R3_HARNESS_CONTRACT** | `D:\wp2_env_store\harness\d7_r3\D7_R3_HARNESS_CONTRACT.md` (SHA `fd06ebb2…dfa5`) | Runtime closure = the unit's frozen lock fragment **FULLY**. Both `LOCK_FRAGMENT_MAIN_PLUS_DEV` and `V2_EDITABLE_PLUS_LOCK_DEV` include the **complete main+dev** dependency set recorded in the frozen lock. **Exactly two** platform exclusions: `pywin32` → MARKER_EXCLUDED_ON_LINUX; `python-magic-bin` → `platform="win32"`. |
| 3 | **D7_R3 closure implementation** | `d7_r3_closure.py` (SHA `88eec826…b54f58`) | `poetry_pins` = complete lock closure (python-versions filtered). `derive_runtime_closure` applies exactly the two frozen platform exclusions. No pruning of dev-only tools. |
| 4 | **D7_REQUIRED_CLOSURE_AUDIT** (+ R1 superseding) | `manifests\D7_REQUIRED_CLOSURE_AUDIT.json` / `_R1.json` | Machine-readable expected main/dev closure identity + count per unit (144 units). For unit `vu-0d8ddec94417`: expected = 254 (150 main + 104 dev). |
| 5 | **R4 shared interface** | `R4_SHARED_INTERFACE.md` + `env_r4/contracts.py` (frozen, immutable) | R4-B parser behind the interface is a **generic** lock parser. Must stay marker-aware for other consumers. Not the owner of D7 install-route semantics; must not be globally weakened. |
| 6 | **36A9 owner review** | `session-ses_ec83.md` (full144 preexecution worktree, read-only) | Established `C_LOCK_CLOSURE_PARSER_DIVERGENCE`: R3 vs R4-B produce materially different closures on the exact frozen artifact. |

## 2. Exact semantic divergence

For the frozen lock `saleor-rc-36a9a14e8d12_poetry.toml`
(SHA-256 `4f027ba1…a398b80`, 254 `[[package]]` entries, Poetry lock-version 2.1):

* **R4-B generic poetry parser** (`uv_adapter._parse_poetry_lock`) evaluates
  package-level `markers` metadata against the target. Packages such as
  `django`, `pillow-avif-plugin`, `celery`, `pytest` carry
  `markers = 'platform_python_implementation == "PyPy"'`, which evaluates
  **False** on CPython → R4-B drops them. Result: **18** requirements.
* **Frozen R3 behavioral authority** (`d7_r3_closure.py`) ignores package
  markers and derives the **complete main+dev** closure (all 254 entries,
  python-versions filtered), applying only the exactly-two frozen platform
  exclusions → **252** install pins.
* Counts on the exact artifact: 254 entries; R3 runtime closure 253 (owner
  review, quick check) / **252** (actual R3 calibration with both frozen
  platform exclusions, incl. python-magic-bin); R4-B = 18; intersection 18;
  R3-only 235; R4-B-only 0.

The successor reproduces the **frozen R3 closure semantics exactly**
(reuse `d7_r3_closure.py`), which yields **252** install pins for 36A9 —
identical to the R3 harness that passed the real D7_R3_CALIBRATION_12
(`progress.json` unit 9: `n_runtime=252`).

## 3. Correct code ownership layer

**Layer:** D7 **install-route semantics** — `runtime_pins()` in the qualified
Attempt-6 runner (`scripts/r4_behavioral_calibration_n12_r2.py`), which the
Full144 driver reuses unchanged.

**Why:** the frozen R3 install-route authority defines what closure each
install route must install. The runner's `runtime_pins()` is the D7
install-route projection layer. R4-B is a generic lock parser that MUST remain
marker-aware for UV_EXPORT, source-fidelity and the I6 census. Therefore the
correction is a **route-aware behavioral closure projection** at the runner
layer, not a global weakening of R4-B. `contracts.py` and `uv_adapter.py`
stay byte-for-byte unchanged.

## 4. Generic successor rule

> For install route **LOCK_FRAGMENT_MAIN_PLUS_DEV** with a poetry lock, the
> D7 behavioral closure projection derives the closure from the **frozen R3
> closure semantics** (complete main+dev lock closure, python-versions
> filtered, then exactly the frozen R3 platform exclusions). All other routes
> (**UV_EXPORT**, **REQ_MAIN_PLUS_LOCK_DEV**, **V2_EDITABLE_PLUS_LOCK_DEV**)
> keep their existing R4-B closure projection unchanged. Unknown install
> routes fail closed.

No task-ID conditionals, no commit-ID conditionals, no package-name
allowlist, no Poetry-version heuristic, no special case for the three affected
tasks. The rule is keyed to the **frozen install-route authority** and reuses
the **qualified frozen R3 closure implementation** (`d7_r3_closure.py`) rather
than a second independent parser.

## 5. Routes changed

* **LOCK_FRAGMENT_MAIN_PLUS_DEV** — closure projection switches to frozen R3
  complete main+dev semantics (for poetry locks). This is the route the frozen
  authority requires to be the complete main+dev closure.

## 6. Routes unchanged

* **V2_EDITABLE_PLUS_LOCK_DEV** — audit proves the existing implementation
  already yields the complete main+dev closure (V2 locks carry no
  marker-gated packages; R4-B parse == full lock for all 19 V2 units). Per
  the owner ruling, do not change V2 unless the audit proves a violation; no
  violation exists.
* **UV_EXPORT** — uv.lock single-environment semantics; R4-B uv parse matches
  the audit expected closure minus legitimately target-excluded win32-only
  packages (`pywin32`, `python-magic-bin`), consistent with the frozen I6
  install-route authority. No violation of UV_EXPORT's own route semantics.
* **REQ_MAIN_PLUS_LOCK_DEV** — R4-B parse returns the complete lock closure
  for all REQ units (no marker gating in those locks); codecov 2.1.11
  inclusion matches the D4 R5 amendment (affected_versions ≤ 2.1.10; codecov
  2.1.11/2.1.12 recovered as ARCHIVED_EXACT_ARTIFACT). No violation of REQ's
  own route semantics.

## 7. Why this is not result-driven patching

1. The successor encodes a **general install-route rule** keyed to the frozen
   authority of the route, never to a task/unit/package/commit identity.
2. It is derived from frozen authorities (`D7_R3_HARNESS_CONTRACT` +
   `d7_r3_closure.py` + `D7_REQUIRED_CLOSURE_AUDIT`), not from the observed
   Full-D7 failure.
3. R4-B is preserved for all other consumers; only the D7 install-route
   projection layer changes.
4. The **population impact is measured** in S4 across all 144 units / 219
   tasks — never assumed to be the three known tasks.

**Status:** internally consistent → proceed to S2 (tests first).