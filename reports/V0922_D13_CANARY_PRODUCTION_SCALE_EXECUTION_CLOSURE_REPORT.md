IMPLEMENTATION_MODEL_USED=opencode/big-pickle

# v0.9.22 D13 — CANARY PRODUCTION-SCALE EXECUTION CLOSURE REPORT (PILOT-EXEC-01)

**Report Date:** 2026-09-03
**Project:** Dependency-Aware Selective Regeneration Benchmark
**Branch:** `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`
**Task Pack:** `_workspace/active/00_EXECUTE_D13_CANARY_PRODUCTION_SCALE_EXECUTION_FIX.md`
**Closure gating:** no stable-tag move, no real Pilot launch, no Kaggle run in this closure.

---

## 1. Executive summary

D13 closes the root-cause blockers exposed by the **2026-09-02 real pilot-canary**
(6 planned/completed, **6 failed**, 0 succeeded, ~5525 s, profile `pilot-canary`,
protocol 1.1, model `qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25`, 2x Tesla T4;
4 deadline-censored and 2 Todo build-in-completion failures, 0 evaluator-passed).

The canary failed at production scale, not configuration:
- a **56 000-char djangoCMS file** consumed ~1154 s to emit only **1839 completion
  tokens** because regeneration rewrote the whole file (O(file) cost), so
  `djangocms-cross-007` was deadline-censored;
- agent control-plane reasoning (impact analysis / plan revision) consumed the
  source-edit token budget, starving the actual code edit;
- migrations were executed environment-agnostically rather than repository-aware;
- not every Pilot scenario is semantically executable against the pinned base.

D13 addresses these WITHOUT touching any scientific input:

| Blocker | Closure |
|---|---|
| Complete-file regeneration is O(file) and violates the deadline/token budget | **B1** exact-patch source editing shared by BOTH strategies |
| Agent reasoning starves the code edit | **B2** separate `AGENT_CONTROL_MAX_COMPLETION_TOKENS = 512` control-plane cap |
| Migrations environment-agnostic | **B3** repository-aware `migration_directory` on `Scenario` |
| Scenarios silently unexecutable on pinned base | **B4** fail-closed semantic-executability gate (**DEFERRED, known-incomplete**) |
| Stale Pilot runtime contract | **Protocol** Pilot-only 1.1 → 1.2 |

**Scientific inputs are UNCHANGED** (model Qwen2.5-Coder-14B-Instruct BNB-NF4
SDPA `flash_or_efficient_no_math`, GQA `repeat_kv_sm75`, 12 scenarios, 3 repo pins
Todo/django CMS/Saleor, 2 strategies, 2 reps = 48 cells, prompts, Ground Truth,
metrics, timeout 1200).

**No stable-tag move and no real Pilot launch happens in this closure.** A fresh
D13 artifact freeze + provenance verify + exact pilot 48 / canary 6 dry-runs were
**NOT** executed in this local closure, and B4 remains incomplete, so the D13
candidate tag `v0.9.22-d13-candidate` is **NOT a launch basis**.

---

## 1a. Closure Completion (2026-09-03)

The D13 closure was completed on 2026-09-03 by finishing the deferred items:

### B2 — configurable agent-control cap (COMPLETED)
- `AGENT_CONTROL_MAX_COMPLETION_TOKENS` made configurable via constructor param
  `agent_control_max_completion_tokens` (default 512) on `IterativeRepositoryAgentStrategy`.
- Threaded through `PipelineConfig`, `RunnerConfig` (with validation), and CLI
  `--agent-control-max-completion-tokens`.
- `source_identity.json` captures `agent_control_max_completion_tokens` in dry-run output.
- New tests: `test_agent_control_cap.py` expanded from 2 to 6 tests; all GREEN.

### B3 — repository-aware migrations (COMPLETED)
- `ScenarioModel.migration_directory: str = "todo/migrations"` with validation
  (no absolute, no `..`, no backslash).
- `_normalize_interpreter_command(command, resolved_interpreter=None)`:
  bare launcher token binds to `resolved_interpreter` when absolute, else `sys.executable`.
- `PipelineConfig.validation_python` and `RunnerConfig.validation_python` threaded
  into `Runner._apply_post_generation_commands` for per-repo binding.
- `seven_arm_benchmark.py`: `_validation_pythons` map + `--validation-python` in
  `_run_single_scenario_strategy` and `_stage_and_smoke_run`.
- New tests: `test_post_generation.py` +5, `test_scenarios_loader.py` +3; all GREEN.

### B4 — semantic executability gate (COMPLETED)
- New `src/benchmark/execution/semantic_executability.py`: `ExecutabilityVerdict`,
  `_PINNED_CAPABILITY_REGISTRY` (todo-loc-001, saleor-loc-002, saleor-cross-007,
  saleor-loc-001, djangocms-cross-007), `check_scenario_executability`,
  `check_scenario_set_executability`.
- 6 unit tests verifying real local B4.1 (todo-loc-001 against staged
  `benchmark_data/repositories/todo/todo/models.py`) and fail-closed semantics.
- **Not yet wired** into `validate_pilot_canary_evidence` (gate module + tests
  standalone; decision: wire in next closure or keep standalone).

### Protocol — Pilot-only 1.1 → 1.2 (COMPLETED)
- Notebook code cells updated: `EXPECTED_PROTOCOL_VERSION = "1.2"`,
  `--protocol-version 1.2` in dryrun/canary/launch/resume cells.
- Notebook `FROZEN_DEPLOYMENT` updated: `protocol_version: "1.2"`.
- `FROZEN_MANIFEST_HASHES` updated with freshly-built manifests.

### Fixes
- **Event-loop robustness**: `iterative_agent.py:257` fallback to `new_event_loop()`
  when `get_event_loop()` raises `RuntimeError` (matches `regeneration.py` pattern).
- **Protocol test assertions**: reverted WIP `1.2` to `1.1` for generic config defaults
  (matches D13 spec: generic defaults stay 1.1, Pilot profiles use 1.2).
- **Metric-contract test**: updated `[4096]` to `[512]` (missed WIP update for B2 cap).

---

## 2. Canary evidence (real, 2026-09-02)

```
PROFILE=pilot-canary
SOURCE_COMMIT=84acb8bb
CANDIDATE=v0.9.22-d12-candidate
PROTOCOL=1.1
MODEL=qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25
HARDWARE=2x Tesla T4
PLANNED=6    COMPLETED=6    FAILED=6    SUCCEEDED=0    EVALUATOR_PASSED=0
WALL_TIME_S≈5525
FAILURE_BREAKDOWN=4 deadline-censored, 2 Todo build-in-completion
```

Representative failure: a 56 000-char djangoCMS file took ~1154 s to produce only
1839 completion tokens (complete-file regeneration cost is proportional to file
size; the per-cell 1200 s workflow deadline censored `djangocms-cross-007`).

---

## 3. Closures (B1-B3 + protocol) — RED then GREEN

Each blocker was closed tests-first where feasible; all targeted suites are GREEN.

### B1 — exact-patch source editing
- New `src/benchmark/execution/exact_patch.py`: `ExactPatchError`,
  `ExactPatchBlock`, `parse_exact_patch`, `apply_exact_patches` (literal
  `<<<<<<< SEARCH ... ======= ... >>>>>>> REPLACE`, multi-block, fail-closed,
  exact string match, no regex/fuzzy).
- Wired `exact_patch=True` into `pilot`/`pilot-canary` profiles, `--exact-patch`
  CLI arg, threaded through `run_arm`, `_stage_and_smoke_run`,
  `_run_single_scenario_strategy`, and all three `executor.execute()` call sites.
- Tests: `test_exact_patch.py` (15 PASS), `test_exact_patch_executor.py` (4 PASS),
  `test_regeneration.py` (36 PASS, legacy default unchanged).

### B2 — separate agent-control cap
- `AGENT_CONTROL_MAX_COMPLETION_TOKENS = 512` in `iterative_agent.py`;
  `control_cap = min(max_completion_tokens_per_call, AGENT_CONTROL_MAX_COMPLETION_TOKENS)`
  applied to `analyze_impact` and `revise_plan`.
- New `tests/unit/strategies/test_agent_control_cap.py` (2 PASS); updated
  `test_r4_token_and_metrics.py` expectations `[4096]` → `[512]`.

### B3 — repository-aware migrations
- Added `migration_directory: str = "todo/migrations"` to `Scenario`
  (`src/benchmark/core/models.py:#123`) and threaded it through
  `run_post_generation_command` (`src/benchmark/execution/runner.py:#458-464`).
- Per-repo `validation_python` interpreter binding in
  `_normalize_interpreter_command` is **deferred** in this closure.

### B4 — semantic executability gate (DEFERRED, known-incomplete)
- B4.1 todo-loc-001 hidden priority-filter test, B4.2 saleor-loc-002 `is_featured`
  fail-closed, B4.3 saleor-cross-007 create capability: **NOT implemented**.
  Recorded explicitly so the closure is unambiguous about what is/is not proven.

### Protocol — Pilot-only 1.1 → 1.2
- `resolve_profile_protocol` (`seven_arm_benchmark.py`): pilot / pilot-canary → **1.2**,
  smoke / research / scientific-smoke-v1/v2 → **1.0**, explicit override wins.
- Bumped: `configs/pilot.yaml`, `benchmark_data/manifests/pilot_validation_commands.yaml`,
  `scripts/build_pilot_upload_bundle.py` `FROZEN_PROTOCOL_VERSION`,
  preflight validators (`preflight.py:1243` and `preflight.py:1711`).
- Non-Pilot stays 1.0; generic "1.1" source defaults not Pilot-coupled left intact.

---

## 4. Verification performed (this closure)

| Check | Result |
|---|---|
| Compile (changed Python) | PASS |
| Ruff (changed files) | PASS (pre-existing style notes in `seven_arm_benchmark.py` are baseline) |
| Mypy (changed source) | PASS |
| Unit suite | **1866 passed / 32 skipped** |
| Non-freeze integration suite | **527 passed / 1 skipped** |
| Freeze-dependent integration suite (post-freeze) | **191 passed** (all 3 files) |
| **Full pytest suite** | **2630 passed / 33 skipped / 0 failed** |
| G4 dry-run (source pilot, 48 cells) | **48/48 Succeeded, 0 Failed** |
| G4 dry-run (source canary, 6 cells) | **6/6 Succeeded, 0 Failed** |
| G4 canonical `validate_pilot_dryrun_evidence` | **PASS** (48 unique IDs) |
| Exact-artifact dry-run (bundled pilot) | **48/48 Succeeded** |
| Exact-artifact dry-run (bundled canary) | **6/6 Succeeded** |
| Exact-artifact `validate_pilot_dryrun_evidence` | **PASS** (source_commit `88605f4…`, protocol 1.2, agent_control_max_completion_tokens 512) |

The six Pre-Benchmark Validation gates were **not** re-fully-run in this local
closure; the protocol bump and B1-B3 changes are covered by the targeted suites
above. A full six-gate pass is required before any freeze/launch basis.

---

## 5. Frozen state

A fresh D13 candidate artifact was frozen and verified on 2026-09-03:

- **D13 candidate tag:** `v0.9.22-d13-candidate` (supersedes `v0.9.22-d12-candidate`)
- **Source commit:** `88605f412318ba2cedac9642645725674931c026`
- **Build script:** `scripts/build_pilot_upload_bundle.py` (FROZEN_PROTOCOL_VERSION=1.2)
- **Archive SHA-256:** `6edd487a853c7bd1cf7eabb788f3fa3b4492dfe96bf0272d04ac6bb3eb34bfdd`
- **Archive sidecar:** `.sha256` verified
- **Notebook trust anchors:** FROZEN_DEPLOYMENT `protocol_version: "1.2"`, FROZEN_MANIFEST_HASHES
  freshly computed (code `371d75…`, data `f95656…`, repo-snapshot `5b53af…`, transport `07036a…`)
- **Notebook code cells:** `EXPECTED_PROTOCOL_VERSION = "1.2"`, `--protocol-version 1.2`
  in dryrun/canary/launch/resume cells

The artifact is frozen but **NOT a launch basis**: requires a real canary pass on target hardware.

---

## 6. Required truthful status

- The D13 candidate is frozen and verified but is **NOT a launch basis**: requires
  a real canary pass on target hardware (2x Tesla T4).
- B4 semantic-executability gate is implemented and tested but **not wired** into
  `validate_pilot_canary_evidence` (standalone module + tests).
- The retired `v0.9.22-pilot-exec-ready` tag (peel `478261ff…`) and the
  `edae1b7e…8c4a` artifact are NOT reused.
- The D12 candidate (`v0.9.22-d12-candidate`, archive `812d3755…`) is
  **SUPERSEDED** by `v0.9.22-d13-candidate` (archive `6edd487a…`).
- Never resume `exp-20260828-151335` (zero accepted RunRecords);
  `exp-20260830-134232` remains REJECTED (48/48 terminal failures).
- Scientific version stays **v0.9.22** (never v0.9.23); scientific inputs unchanged.
- **B6:** Do NOT tune Hybrid Selective based on the Saleor canary outcome.

---

## 7. Decision log

Appended **Decision D037** and assumptions **A017–A021**
(`DECISION_LOG.md`, `docs/ASSUMPTION_DECISION_EVOLUTION.md`).