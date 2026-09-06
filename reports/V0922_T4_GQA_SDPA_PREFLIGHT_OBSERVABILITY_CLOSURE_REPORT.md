# V0922 T4 GQA SDPA + Preflight Observability Closure Report

**Date:** 2026-08-26
**Branch:** `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`
**Built on:** v0.9.22 candidate-consistency merge `ba08392552545baa15c10ae5db2e95ce7496a720` (which already carries the long-context attention memory closure)
**Source commit (frozen):** `de0c5bd8bcc7d499246292f515207ce1d10baba7`
**Artifact:** `dist/pilot-kaggle-upload.zip` SHA-256 `bfbc935f762b484482eee411c5ea7996412b1e47f759f6dca81fa58b0ab9a850` (+ sidecar verified)
**Trust/provenance:** 0 mismatches; `reports/pilot_notebook_trust_freeze.json` FROZEN

## 1. Root cause (reproduced on real 2x T4)

T4 = sm75 → Flash SDPA unavailable. Native GQA reaches fused SDPA as
**40/8/8**, but the memory-efficient fused kernel rejects unequal heads, and
mathematics attention is disabled (v0.9.21 quadratic-OOM closure). With no
allowed kernel remaining, attention raises during generation. The long-context
probe is where it surfaced, but the defect is the GQA head-shape mismatch on
T4, not the probe length.

## 2. Closure (no scientific input changed)

- **Task A — repeat-KV compatibility shim.** `kaggle_qwen_backend.py` adds
  `_install_sm75_sdpa_gqa_compatibility()` which wraps
  `transformers.integrations.sdpa_attention.use_gqa_in_sdpa` to return `False`
  on compute capability `(7,5)`, delegating otherwise. This forces pinned
  Transformers 4.57.6 to use its repeat-KV path on T4 so native GQA
  **40/8/8 → 40/40/40**, reaching the fused SDPA kernel with equal heads.
  Idempotent; `gqa_compatibility_mode` surfaced on the backend + long-context
  probe evidence.
- **Task B — cheap CUDA GQA microprobe.** `probe_sdpa_gqa_kernel_compatibility()`
  builds Q/K/V for heads 40/8/8, expands KV via `F.repeat_kv` to 40/40/40, and
  runs SDPA on every visible CUDA device. Runs in seconds and fails closed, so
  incompatible kernels are caught BEFORE the ~16.5-min repository preflight.
- **Task C1 — observable repository preflight.** `scripts/pilot_repo_snapshot.py`
  `_run_command` now emits a live heartbeat (`START`/`RUNNING`/`END`) via a
  background thread (default sink `print`, `heartbeat_interval=30s`), and the
  Saleor capability-gate outcome is persisted to `result_record["saleor_capability_gate"]`.
- **Task C2/C3 — notebook cell 8.** Runs the GQA microprobe first (fail-closed),
  then streams preflight output through a new `_run_tee` (live to
  `PREFLIGHT_CONSOLE`), replacing the old capture-only `_run`.
- **Task D — truthful preflight reporting.** `preflight.py` reports the
  short-generation probe honestly: on short-probe FAIL the 12k long-context
  probe is `SKIP` (not falsely green). `gqa_compatibility_mode` is persisted in
  the result/JSON/table and enforced by `validate_pilot_launch_authorization`
  (lenient: absent → pass; present-and-wrong → fail).

## 3. Verification

- `git diff --check`: clean.
- Ruff on changed Python files: clean.
- Mypy on changed production files: only 4 pre-existing errors in
  `preflight.py` (lines 362/1077/1086/1095), confirmed present in `HEAD` before
  this change — not introduced here.
- Python compile on changed files: clean.
- Targeted Pytest (relevant suites): **867 passed / 23 skipped / 0 failed**.
  New tests: `tests/unit/llm/test_kaggle_qwen_gqa_compat.py` (8),
  `tests/unit/execution/test_preflight.py` (short-probe truthful reporting +
  launch-auth gqa), `tests/unit/test_pilot_repo_snapshot.py` (heartbeat +
  Saleor gate evidence).
- Full `pytest tests/`: not completed locally (exceeds 600s budget); the
  candidate-consistency merge's full suite (2407 passed / 33 skipped) remains
  the authoritative baseline and is unchanged by this closure.
- Dry-run pilot profile: **48/48** (unique IDs, 0 model calls, 0 tokens).
- Finalizer (`finalize_pilot_notebook_trust.py --verify-source-provenance`):
  FROZEN, 0 provenance mismatches; artifact rebuilt from committed source.

## 4. Independent self-audit

- Objective unchanged: only the T4 GQA kernel path + preflight observability
  were added; the frozen scientific protocol (model, BNB-NF4, 12 scenarios, 3
  pins, 2 strategies, 2 reps, 48 cells, prompts, metrics, timeouts, 12000/64
  gate, no-math fused SDPA policy) is untouched.
- No v0.9.23 spawned; the work continues on the SAME v0.9.22 candidate branch.
- No stable `v0.9.22` tag created (real T4 proof still pending).

## 5. What remains (ordered)

1. Fresh real 2x T4 Kaggle model preflight (repo preflight + heartbeat,
   Qwen 14B BNB-NF4 load, GQA microprobe, short probe, then the 12k target with
   the same 64-token probe) using the exact artifact `bfbc935f…`.
2. If the 12k probe PASSES: annotate `v0.9.22-pilot-exec-ready` on source commit
   `de0c5bd8bcc7d499246292f515207ce1d10baba7`, push tag, refresh docs.
3. If it FAILS: return to the SAME v0.9.22 task (do not spawn v0.9.23).
4. Launch accepted 48-cell Pilot only after the stable tag exists and all target
   gates pass.
