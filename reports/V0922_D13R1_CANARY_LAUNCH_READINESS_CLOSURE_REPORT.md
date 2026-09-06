IMPLEMENTATION_MODEL_USED=openrouter/deepseek/deepseek-v4-flash-0731

# v0.9.22 D13r1 — CANARY LAUNCH-READINESS FINALIZER CLOSURE REPORT (PILOT-EXEC-01)

**Report Date:** 2026-09-03
**Project:** Dependency-Aware Selective Regeneration Benchmark
**Branch:** `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`
**Task Pack:** `_workspace/active/00_D13_CANARY_READY_FINALIZER.md` (D13 context)
**Closure gating:** no stable-tag move, no real Pilot launch, **no Kaggle run** in this closure.

---

## 1. Executive summary

D13r1 **FINISHES canary launch-readiness** on top of the D13 candidate
(`v0.9.22-d13-candidate`) WITHOUT touching a single scientific input (model
Qwen2.5-Coder-14B-Instruct, BNB-NF4, sdpa `flash_or_efficient_no_math`, GQA
`repeat_kv_sm75`, 12 scenarios, 3 repo pins Todo/django CMS/Saleor, 2
strategies, 2 reps = 48 cells, prompts, Ground Truth, metrics, timeout 1200).

The five finalizer items F1-F5 are implemented exactly as specified:

| Item | Closure |
|---|---|
| **F1** wire semantic executability into the real pilot/pilot-canary PRE-MODEL launch path | `validate_pilot_launch_authorization` runs `validate_pilot_semantic_executability` when a `scenario_dir` is supplied; new `validate_pilot_semantic_executability(scenario_ids, scenario_dir, repository_roots)`; the canary cell gates the 3 canary scenarios BEFORE any model call; the CLI `--require-launch-authorization` passes `scenario_dir`/`scenario_ids` to the validator. The FULL 48-cell Pilot is **NOT a launch basis** while any scenario is semantically unexecutable (saleor-loc-002 `is_featured` known-absent; 7 unregistered scenarios fail closed). |
| **F2** migration metadata ONLY on the 3 canary scenarios | `todo-loc-001` → `migration_directory: todo/migrations`; `saleor-loc-001` → `saleor/product/migrations`; `djangocms-cross-007` → `cms/migrations`. No other scenario declares `migration_directory` (verified by test). |
| **F3** decouple migration execution from `evaluator_asset` | `_requires_scenario_evaluator` now keys ONLY on `evaluator_asset`; a migration-only scenario (`post_generation_command`/`require_new_migration` without `evaluator_asset`) is a VALID configuration (the pre-F3 harness-defect "Scenario metadata requires evaluator" path is removed). |
| **F4** remove the exact-patch repair-prompt contradiction | `REPAIR_CONTEXT_PROMPT_TEMPLATE` no longer instructs "return the complete replacement file" in patch mode; it defers to the stated per-mode output contract. |
| **F5** `exact_patch` + agent-control cap in frozen config/provenance identity | `source_identity.json` (exact_patch), bundle identity (`FROZEN_EXACT_PATCH`, `FROZEN_AGENT_CONTROL_MAX_COMPLETION_TOKENS`), notebook `FROZEN_DEPLOYMENT` (`"exact_patch": True`, `"agent_control_max_completion_tokens": 512`), `configs/pilot.yaml`; ENFORCED by the dry-run + canary evidence validators. |

**Do-Not items honored:** no all-12 semantic registry expansion (7 unregistered
scenarios fail closed = the desired non-launch-basis property); no
saleor-cross create support; no Selective tuning; no Qwen/Kaggle/timeout change.

---

## 2. F1 — semantic executability wired into the real launch path

### 2.1 Source changes
- `src/benchmark/execution/preflight.py`:
  - new `validate_pilot_semantic_executability(*, scenario_ids, scenario_dir, repository_roots)` — loads the requested scenarios from the bundled scenario dir, runs the fail-closed `check_scenario_set_executability` registry check, returns the verdict summary or raises `LaunchAuthorizationError`;
  - `validate_pilot_launch_authorization` gains optional `scenario_dir` + `scenario_ids`; when `scenario_dir` is supplied it runs the pre-model semantic gate AFTER the dry-run evidence and BEFORE the HF-token check (i.e. still before any model call);
  - `_semantic_repository_roots(scenarios_dir)` maps `data/repositories/{todo,djangocms,saleor}` → staged root (None when not locally staged → fail-closed).
- `seven_arm_benchmark.py` `--require-launch-authorization` now passes
  `scenario_dir=scenarios_dir` and `scenario_ids=tuple(profile.scenario_ids)`.
- `notebooks/pilot_exec_01.ipynb`:
  - `pilot-canary-cell` imports + calls `validate_pilot_semantic_executability` on the 3 canary scenarios BEFORE constructing/executing `canary_cmd` (tilde a genuine PRE-MODEL gate on target);
  - `pilot-launch-cell` and `pilot-resume-cell` pass `scenario_dir` + `scenario_ids=PILOT_SCENARIOS` into `validate_pilot_launch_authorization` (pre-model).

### 2.2 Bundled-exact canary semantic pre-model gate — PASS
Running the bundled exact artifact (`code/`, `data/` with the real pinned repo
trees), the exact gate the target canary cell runs passes 3/3:

```
todo-loc-001        executable=True verifiable=True
djangocms-cross-007 executable=True verifiable=True
saleor-loc-001      executable=True verifiable=True
```

The FULL 48-cell Pilot launch is **NOT** a launch basis: calling the same gate
with `PILOT_SCENARIOS` (12) fails closed on `saleor-loc-002` (`is_featured`
known-absent) and the 7 unregistered Pilot scenarios (no probes → fail closed).
This is the required truthful state.

---

## 3. F2/F3 — repository-aware migrations (canary only) + migration/evaluator decoupling

- **F2:** exactly three YAML files declare `migration_directory`:
  `todo-loc-001.yaml` (`todo/migrations`), `saleor-loc-001.yaml`
  (`saleor/product/migrations`), `djangocms-cross-007.yaml` (`cms/migrations`).
  Tests assert both the exact three values AND that no other scenario declares
  the field (`TestCanaryMigrationMetadata`).
- **F3:** `BenchmarkRunner._requires_scenario_evaluator` is now
  `bool(scenario.evaluator_asset)` and the `_validate_scientific_configuration`
  harness-defect branch that demanded an evaluator for any migration-bearing
  scenario was removed. `require_new_migration=True` without
  `post_generation_command` still fails closed (unchanged invariant). Tests in
  `test_runner.py` (`TestMigrationEvaluatorDecoupling`) and the updated
  `test_r3d_wiring.py` cover the decoupling.

Scientific inputs unchanged — the migration_directory metadata is operational
(run-stage targeting), not a scientific change.

---

## 4. F4 — exact-patch repair-prompt contradiction removed

`REPAIR_CONTEXT_PROMPT_TEMPLATE` in `src/benchmark/execution/regeneration.py`
now reads (mode-neutral):

```
Correct the existing artifact using the evidence above. Do not repeat the same
invalid output. Follow the output contract already stated above for this
artifact (in EXACT PATCH mode emit SEARCH/REPLACE blocks; otherwise emit the
complete replacement file), without explanation or markdown fences.
```

The legacy "...Return the complete replacement file content..." instruction no
longer contradicts the exact-patch `EXACT_PATCH_OUTPUT_CONTRACT` appended right
above it. `TestRepairPromptExactPatchContract` (4 tests) pins this:
- exact-patch mode + repair context contains NO complete-file instruction;
- the exact-patch contract precedes the repair instruction;
- complete-file mode still instructs complete-file output;
- the repair context stays appended after the output contract.

---

## 5. F5 — exact_patch + agent-control cap in frozen identity

- **`source_identity.json`** (written by `seven_arm_benchmark.py`): adds
  `"exact_patch": <args.exact_patch>` next to the existing
  `agent_control_max_completion_tokens`.
- **Bundle identity** (`scripts/build_pilot_upload_bundle.py`): new frozen
  constants `FROZEN_EXACT_PATCH = True`,
  `FROZEN_AGENT_CONTROL_MAX_COMPLETION_TOKENS = 512`; `build_identity` emits
  `exact_patch` + `agent_control_max_completion_tokens`.
- **Notebook `FROZEN_DEPLOYMENT`**: `"exact_patch": True`,
  `"agent_control_max_completion_tokens": 512` (setup cell).
- **`configs/pilot.yaml`**: `execution.agent_control_max_completion_tokens: 512`.
- **Enforcement** in `preflight.py`:
  - `_collect_dryrun_evidence_errors` (pilot dry-run gate) now requires
    `source_identity.json exact_patch is True` and
    `agent_control_max_completion_tokens == 512`; the canary evidence gate
    requires the same two fields in the canary `source_identity.json`.
- Verified in the exact-artifact dry-run `source_identity.json`:
  `exact_patch: True`, `agent_control_max_completion_tokens: 512`, protocol 1.2,
  source_commit == `6bc946a…`, source_tag == `v0.9.22-d13r1-candidate`.

---

## 6. Verification performed (six gates + full suite)

| Gate | Result |
|---|---|
| G1 Dataset validation | **333 passed / 4 skipped** |
| G2 Prompt validation | **132 passed / 4 skipped** |
| G3 Pipeline smoke | **930 passed / 23 skipped** |
| G4 Source dry-runs | Pilot **48/48** (repos 16/16/16, strategies 24/24, reps {1:24,2:24}); canary **6/6** (repos 2/2/2, strategies 3/3, rep 1:6); 0 calls, 0 tokens, protocol 1.2; canonical `validate_pilot_dryrun_evidence` **PASS** |
| G4 Exact-artifact dry-runs (fresh extraction of the frozen archive) | Pilot **48/48** + canary **6/6**; every record + `source_identity.json` == `6bc946a…` + `v0.9.22-d13r1-candidate`; exact_patch True, agent_control 512; 0 calls/tokens |
| G4 Bundled exact semantic gate | canary scenarios **PASS** 3/3 (executable + verifiable) |
| G6 Metrics | **194 passed** |
| G5 Full pytest suite | **2650 passed / 34 skipped / 0 failed** |
| Compile (changed Python) | PASS |
| Ruff (changed files) | PASS |
| Mypy (changed production source) | PASS (0 new; seven_arm_benchmark.py pre-existing 15 baseline errors unchanged) |
| Notebook cells compile | PASS (setup, dryrun, canary, launch, resume) |

### Freeze + provenance
- **Artifact:** `dist/pilot-kaggle-upload.zip`
- **Archive SHA-256:** **`9f120412cfef5dfb7f66a57c03380fc5149b45b20d53c60d623d1e81bc203461`** (+ sidecar verified)
- **Source commit:** `6bc946abbb4f2ef08151b4285fe498ad8d03cc7f`
- **Source tag:** `v0.9.22-d13r1-candidate`
- **Freeze report:** `reports/pilot_notebook_trust_freeze_d13r1.json` (status FROZEN)
- **Provenance:** `--verify-source-provenance` → **0 mismatches**; idempotent
  same-input rerun → archive SHA unchanged.
- **Identity fields:** task `PILOT-EXEC-01`, protocol_version `1.2`,
  `exact_patch: true`, `agent_control_max_completion_tokens: 512`,
  scenario_count 12, strategy_count 2, repetitions 2, expected_cells 48,
  model Qwen2.5-Coder-14B-Instruct, quantization bnb-nf4, timeout 1200,
  max_attempts 3, max_completion_tokens_per_call 4096.

---

## 7. Required truthful status

- **CANARY_LAUNCH_BASIS = YES** — the frozen `v0.9.22-d13r1-candidate` is a
  valid canary launch basis: exact-artifact dry-run canary 6/6 (protocol 1.2,
  0 calls/tokens, exact_patch + agent_control enforced), bundled exact canary
  SEMANTIC PRE-MODEL gate PASS on the 3 canary scenarios, and the next REAL
  Pilot launch requires a real pilot-canary pass on this candidate (its own tag
  decision).
- **FULL_48_LAUNCH_BASIS = NO** — the full 48-cell Pilot is NOT a launch basis:
  the pre-model semantic gate FAILS CLOSED on `saleor-loc-002` (`is_featured`
  known-absent) and the 7 unregistered Pilot scenarios. No real 48-cell launch
  may start from this candidate.
- No Kaggle run and no stable release tag in this closure.
- The retired `v0.9.22-pilot-exec-ready` tag (peel `478261ff…`) and the
  `edae1b7e…8c4a` artifact are NOT reused.
- The D13 candidate (`v0.9.22-d13-candidate`, archive `6edd487a…`) is
  **SUPERSEDED** by the D13r1 candidate (`v0.9.22-d13r1-candidate`, archive
  `9f120412…`).
- Never resume `exp-20260828-151335` (zero accepted RunRecords);
  `exp-20260830-134232` remains REJECTED (48/48 terminal failures).
- Scientific version stays **v0.9.22** (never v0.9.23); scientific inputs
  unchanged.

---

## 8. Decision log

Appended **Decision D038** to `DECISION_LOG.md` and updated the CURRENT TRUTH /
prior-truth blocks in `AGENTS.md`.