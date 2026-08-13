# PILOT-EXEC-01 — Execution Contract (pre-registered)

**Status:** PRE-REGISTERED BEFORE ANY REAL PILOT MODEL RESULT (Gate B).
**Task:** `PILOT-EXEC-01`
**Pre-registration date:** 2026-08-10
**Recorded by:** OpenCode (executor)
**Authoritative source:** `03_BUDGET_PREREGISTRATION.md`, frozen Pilot protocol
(`configs/pilot.yaml`, `tests/unit/test_pilot_readiness.py` parity contract).

This contract is recorded BEFORE the first real Pilot model cell. It is
frozen for the entire Pilot stage. Do not tune anything from observed Pilot
outcomes (00_READ_FIRST.md, 09_PRODUCTIVITY_AND_STOP_RULES.md).

---

## 1. Scientific matrix

Repositories (3, exact frozen refs in `benchmark_data/manifests/repository_versions.yaml`):

- todo
- djangocms
- saleor

Scenarios (12 exact IDs, frozen in `configs/pilot.yaml`):

- todo-loc-001, todo-loc-002, todo-mod-004, todo-cross-007
- djangocms-mod-005, djangocms-loc-002, djangocms-mod-004, djangocms-cross-007
- saleor-loc-001, saleor-loc-002, saleor-mod-004, saleor-cross-007

Strategies (2, frozen mapping protocol -> implementation):

- iterative_repository_agent (protocol repository_agent)
- selective (protocol hybrid_selective)

Repetitions: 2

Total scientific cells: 48.

No extra scientific cells may be added based on observed performance.

## 2. Model

- Exact model: `Qwen/Qwen2.5-Coder-14B-Instruct`
- Quantization: `bnb-nf4`
- Temperature: 0

No silent substitution of 7B, INT8, FP16, another Qwen checkpoint, another
provider, or another model.

## 3. Per-run budget (frozen AC-05 / pilot.yaml)

- Timeout: 600 seconds uniform.
- Attempts: initial generation + maximum 2 LLM repairs = maximum 3 attempts.
- Per-call completion ceiling: 4096 tokens.
- Workflow-total token ceiling: 0 = unlimited for Pilot (deliberate, DA-09:
  per-run budgets are frozen AFTER the Pilot; the Pilot must measure realistic
  token/call/time distributions before the Main-study budget is frozen).

## 4. Stage budget

The stage budget is the frozen 48-cell matrix. No additional
performance-driven reruns.

- Infrastructure retry policy (frozen protocol): up to 3 retries for genuine
  infrastructure failure using identical scientific inputs.
- A scientific/model/build/regression/architecture failure is measured data.
  Do not rerun it merely to improve the result.
- A harness defect is not a strategy failure: stop, preserve evidence, fix
  under an explicit engineering correction, audit, and rerun only the
  affected cells under the documented correction rule.

## 5. Resource reporting

For every cell and aggregate, record:

- input/prompt tokens if available
- output/completion tokens
- total model tokens
- model calls
- repair calls
- wall-clock duration
- model/generation duration
- validation duration
- GPU/runtime metadata
- timeout
- failure classification

Do not invent monetary API cost for the Kaggle-hosted model.

## 6. Post-Pilot decision

After all valid Pilot cells are terminal: use the observed Pilot distributions
to freeze the Main-study per-run budgets. Do not make the Main budget decision
before the Pilot results audit. Main benchmark execution is NOT part of
PILOT-EXEC-01.

## 7. Execution identity

- Source tag: `v0.9.2-pilot-exec-ready`
- Source commit: the exact 40-char SHA the tag dereferences to (recorded in
  `reports/PILOT_EXEC_01_DEPLOYMENT_FREEZE.md` after the tagged-source rebuild).
- Deployment bundle: `dist/pilot-kaggle-upload/` (archive
  `dist/pilot-kaggle-upload.zip`), built ONLY from the tagged source.
- Historical `kaggle_upload/` (Scientific Smoke bundle) is NOT the Pilot
  deployment bundle and must not be modified or uploaded as Pilot input.
- Every Pilot preflight/real/resume command MUST pass
  `--qwen-quantization bnb-nf4` explicitly (generic CLI default is `bnb-int8`).

## 8. Launch flags frozen

- `--profile pilot`
- `--backend kaggle-qwen` (real; `--dry-run` mock only)
- `--qwen-quantization bnb-nf4`
- `--max-attempts 3`
- `--max-completion-tokens-per-call 4096`
- `--max-total-workflow-tokens 0`
- `--timeout 600`
- `--source-commit <40-char SHA>`
- `--source-tag v0.9.2-pilot-exec-ready`
- `--hf-sync` with exact HF results repository ID (recorded before launch)
- fresh `--output-dir` per experiment; `--new-experiment` on initial launch;
  do NOT pass `--new-experiment` on resume.

## 9. Decision-log entry

Recorded in `DECISION_LOG.md` (Decision D025) with this contract as the
referenced pre-registration.
