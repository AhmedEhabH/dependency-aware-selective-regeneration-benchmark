# WP2 M14A-E1: evaluator amendment for patch-caused pytest startup failure (2026-09-30)

Status: preregistered before any E1 evaluation ran. Evaluation-only. Zero model API.

## Trigger

- Pilot-A P12 stopped with `STOP:EVAL_ERROR` (resumable) on 2026-09-30T11:15:51Z.
- The stopping message was `JUnit missing: saleor-rc-b1_u_07_C_r0.xml`.
- The identity was `saleor-rc-b14def73518c / 073711c62862…` (GOLD_HARD r2). 17 of the 29 unique evaluations had already completed. None of them had a missing JUnit file.

## Brain static finding (zero API, from the committed LIGHT)

- The generated GOLD r2 patch deletes `class TranslationProxy` from `saleor/core/utils/translations.py`.
- The same patch leaves `translated = TranslationProxy()` in `saleor/product/models.py`, a file it also edits. That code is at lines 716 and 954 of the patched file, and the import is removed.
- `pyflakes` on the patched files reports `undefined name 'TranslationProxy'`. GOLD r1 has the same defect, at lines 97, 709 and 947.
- Loading the Django app registry imports `saleor.product.models`. That import raises `NameError`, so pytest-django cannot start and pytest never writes the JUnit file.
- The same task's parent (empty diff) and gold trees started pytest in this environment during readiness (`gold_empty_ok = true`).
- No other unevaluated Pilot-A patch has an undefined name.

## Defect in the M14A kit

Guard G2 in `wp2_m14a_evalcore.py` was documented as "outcome-identical", and it is not. It turns every missing JUnit file into an infrastructure STOP, and that includes a patch whose own tree cannot start pytest. Such a patch is deterministic, so resuming would stop again on the same identity, and then again on GOLD r1. The frozen Smoke v2.2 evaluator scored this case as `missing` on every node, which counts as not passed.

## Rule M14A_E1_PATCH_STARTUP_FAILURE_V1

All of the following conditions are required:

- **R1.** The evaluation container finished (`E2E_DONE`).
- **R2.** Every active run (each group × repetition) has no JUnit file.
- **R3.** For every run, all of these hold:
  - the pytest return code is between 1 and 127;
  - the run log exists;
  - the log contains a Python traceback marker and an exception line;
  - the log names at least one file that the patch edits.
- **R4.** The task's self-hashed readiness record has `gold_empty_ok = true`.

If R1–R4 all hold, every node of every active group is recorded as `["missing"] × 3`, and the frozen `score` is applied unchanged. The result is F2P FAIL, P2P-S FAIL and P2P-U200 FAIL. If any condition fails, the evaluation raises `EvalInfraError` exactly as before.

In both cases, a diagnostics file is written before the worktree is removed. It contains the return codes, the log sha256 and redacted log tails, and it is written to `research/wp2/pilot_a_v1/evaluations/diagnostics/<task>/<label>/e1_diagnostics.json`.

## What does not change

The following are all unchanged:

- generation evidence;
- the generation and evaluation plans;
- membership;
- evaluator sets;
- scopes;
- the pytest command, the repetitions and the DB handling;
- JUnit parsing;
- `score`;
- the A0–A5 gates and thresholds;
- the summary engine (`wp2_m14a_run.py summary`).

No frozen file is edited. E1 adds new files only:

- `scripts/wp2_m14a_evalcore_e1.py`
- `scripts/wp2_m14a_e1.py`
- `controller/plan_m14a_pilot_a_v1_e1.json`
- `controller/light_profile_m14a_e1.json`
- `controller/KIT_MANIFEST_M14A_E1.json`
- `tests/unit/wp2/m14a/test_m14a_e1.py`
- `research/wp2/pilot_a_v1/m14a_e1_amendment.json`
- this document, and two mission documents

The original controller state stays at `STOP:EVAL_ERROR` as immutable history. P12 and P13 are completed by the E1 plan, which keeps its own state file.

## Reporting

The rule applies to both arms alike. `E04_ADDENDUM` writes `docs/WP2_M14A_E1_RESULT_ADDENDUM.md`, which lists every identity scored under E1 together with its evidence. The addendum is descriptive only.
