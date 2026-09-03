IMPLEMENTATION_MODEL_USED=openrouter/deepseek/deepseek-v4-flash-0731

# v0.9.22 D13R2 — LAST CANARY HOTFIX CLOSURE REPORT (PILOT-EXEC-01)

**Report Date:** 2026-09-03
**Project:** Dependency-Aware Selective Regeneration Benchmark
**Branch:** `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`
**Task Pack:** `_workspace/active/00_D13R2_LAST_CANARY_HOTFIX.md` + `_workspace/active/01_ACCEPTANCE_CHECKLIST.md`
**Closure gating:** no stable-tag move, no real Pilot launch, **no Kaggle run** in this closure.

---

## 1. Executive summary

D13R2 is the LAST canary hotfix on the same D13 line (no D14). It closes the
four audited defects H1-H4 WITHOUT touching a single scientific input (model
Qwen2.5-Coder-14B-Instruct, BNB-NF4, sdpa `flash_or_efficient_no_math`, GQA
`repeat_kv_sm75`, 12 scenarios, 3 repo pins Todo/django CMS/Saleor, 2
strategies, 2 reps = 48 cells, prompts, Ground Truth, metrics, timeout 1200).

| Fix | Audit defect | Closure |
|---|---|---|
| **Fix 1** | H1 — the 3 canary scenarios loaded with `post_generation_command=()` and `require_new_migration=False`, so the runner never executed migration generation (could reproduce the previous Todo build failure) | `todo-loc-001`, `djangocms-cross-007`, `saleor-loc-001` now carry the frozen `post_generation_command` (`python manage.py makemigrations todo/cms/product --noinput`) + `require_new_migration: true`; `migration_directory` retained. No other non-smoke scenario declares migration execution metadata. |
| **Fix 2** | H2 — the semantic gate returned PASS for the 3 canaries even with empty commands/False flags (pinned-base sentinels only) | The gate now ALSO proves migration executability for the 3 canary scenarios via an explicit frozen map (`_CANARY_MIGRATION_FIXTURES`): `require_new_migration is True` + exact frozen command + exact frozen `migration_directory`, failing closed on any mismatch (never inferred from English text). |
| **Fix 3** | H3 — the migration subprocess missed the frozen repository validation environment (Saleor needs DATABASE_URL/CACHE_URL/SECRET_KEY/TZ) | `run_post_generation_command(..., env=...)` merges the frozen `validation_env` into the child env exactly like `FunctionalValidator` (`run_env = os.environ.copy(); run_env.update(validation_env)`), never mutating the parent `os.environ`; the Runner passes `self._config.validation_env` to migration generation. |
| **Fix 4** | H4 — `_compute_config_hash` stayed identical when `exact_patch` or the agent-control cap changed (contradicts D13r1 F5) | `_compute_config_hash` now includes `exact_patch` + `agent_control_max_completion_tokens`; changing either changes the hash. All existing fields retained; `max_runs` behavior unchanged. |

**Do-Not items honored:** no Qwen/Kaggle/timeout change; no Selective tuning; no
all-12 semantic registry expansion (the 3 canary scenarios are the ONLY
migration-executability entries); no D14; no real Kaggle run; D13r1 stays frozen
immutable historical evidence.

---

## 2. Fix 1 — complete executable migration metadata (3 canary scenarios)

```yaml
todo-loc-001:
  migration_directory: "todo/migrations"
  post_generation_command: [python, manage.py, makemigrations, todo, --noinput]
  require_new_migration: true

djangocms-cross-007:
  migration_directory: "cms/migrations"
  post_generation_command: [python, manage.py, makemigrations, cms, --noinput]
  require_new_migration: true

saleor-loc-001:
  migration_directory: "saleor/product/migrations"
  post_generation_command: [python, manage.py, makemigrations, product, --noinput]
  require_new_migration: true
```

The runner executes migration generation only when `post_generation_command` is
non-empty; all three canaries now satisfy that gate. The other 9 Pilot
scenarios are untouched. New regression tests assert the exact command/flag on
the 3 canaries and that NO other non-smoke scenario declares
`post_generation_command` / `require_new_migration`.

## 3. Fix 2 — semantic gate proves migration executability

`src/benchmark/execution/semantic_executability.py` gains an explicit frozen
map `_CANARY_MIGRATION_FIXTURES` keyed by scenario id:
`(command, require_new_migration, migration_directory)`. `check_scenario_executability`
now fails closed unless each canary scenario carries the exact frozen migration
metadata. Migration requirements are NEVER inferred from English text at
runtime. This propagates automatically into the pre-model launch path
(`validate_pilot_semantic_executability` inside `validate_pilot_launch_authorization`).

Tests prove: canonical 3 scenarios PASS against staged pinned bases; each of
`require_new_migration=False`, empty command, wrong app label, wrong migration
directory independently FAILS closed; the pre-model launch gate fails without
any backend/model initialization on migration-metadata failure.

## 4. Fix 3 — frozen repository environment to post-generation commands

`benchmark/execution/post_generation.py`:
- `run_post_generation_command(..., env: dict[str, str] | None = None)` — validated (dict of str→str, no NUL), threaded through `_ValidatedPostGenerationRequest`;
- `_run_command` builds `run_env = os.environ.copy()` then `run_env.update(env)` — the exact `FunctionalValidator` semantics; the parent `os.environ` is never mutated.

`benchmark/execution/runner.py` Stage-2 migration generation now passes
`env=self._config.validation_env`. No service-provisioning change.

Tests prove: command sees a test env override; parent environment unchanged;
Saleor-shaped env (DATABASE_URL/CACHE_URL/SECRET_KEY/TZ) reaches the command;
the resolved repository `validation_python` remains the command executable.

## 5. Fix 4 — Protocol-1.2 execution controls in config_hash

`seven_arm_benchmark._compute_config_hash` adds exactly:
`exact_patch` and `agent_control_max_completion_tokens` (getattr defaults
`False` / `512`). All existing fields retained. RED/GREEN tests prove same-args →
same hash; `exact_patch` True vs False → different hash; agent cap 512 vs 256 →
different hash; unrelated `max_runs` behavior unchanged (never part of the hash).

## 6. Verification performed (six gates + full suite)

| Gate | Result |
|---|---|
| G1 Dataset validation | **276 passed / 4 skipped** — 3 canary YAMLs parse; exact migration command/flag/directory correct; semantic gate validates pinned-base capability AND migration executability |
| G2 Prompt validation | **77 passed** — exact-patch + repair stay green; no prompt changes |
| G3 Pipeline smoke | **992 passed / 27 skipped** — migration stage executes with repo validation_python + validation_env; migration-only scenario does not require evaluator_asset |
| G4 Source dry-runs | Pilot **48/48** + canary **6/6** (0 calls, 0 tokens, protocol 1.2, canonical `validate_pilot_dryrun_evidence` PASS; source semantic gate correctly FAILS CLOSED locally because the pinned repos are not staged in this working copy — expected fail-closed) |
| G4 Exact-artifact dry-runs (fresh extraction of the frozen archive) | Pilot **48/48** + canary **6/6**; every record + `source_identity.json` == `fc1c7c8…` + `v0.9.22-d13r2-candidate`; exact_patch True, agent_control 512; 0 calls/tokens |
| G4 Bundled exact semantic gate | canary scenarios **PASS** 3/3 (executable + verifiable) against the bundled pinned repo trees |
| G6 Metrics | **194 passed** (161 unit + 33 metric contract) |
| G5 Full pytest suite | **2671 passed / 33 skipped / 0 failed** |
| Compile (changed Python) | PASS |
| Ruff (changed files) | PASS on changed hunks (5 pre-existing seven_arm_benchmark.py findings unchanged from HEAD) |
| Mypy (changed production source) | PASS — 0 new; seven_arm_benchmark.py pre-existing 16 baseline errors unchanged from HEAD |
| Notebook cells compile | PASS (setup, dryrun, canary, launch, resume) |

### Audit before freeze

```
Qwen changed? NO
Kaggle path changed? NO
timeout changed? NO
Selective tuned? NO
canary scenarios changed semantically? NO
migration execution metadata completed? YES
semantic gate now checks migration executability? YES
post-generation env parity fixed? YES
config_hash distinguishes exact_patch? YES
config_hash distinguishes agent cap? YES
```

Over-engineering audit: no new framework, no new dependency, no all-12
expansion, no extra model analysis.

## 7. Freeze + provenance

- **Artifact:** `dist/pilot-kaggle-upload.zip`
- **Archive SHA-256:** **`65269528049b1f22f277c508f0b0db5b09d536e99fd31d306cfbbfb42e47ef9f`** (+ sidecar verified)
- **Source commit:** `fc1c7c86cd3a0ab5ee771fd343459784cccb3044`
- **Source tag:** `v0.9.22-d13r2-candidate`
- **Freeze report:** `reports/pilot_notebook_trust_freeze.json` (status FROZEN)
- **Provenance:** two-pass finalizer with `--verify-source-provenance` → **0 mismatches**
- **Identity fields:** task `PILOT-EXEC-01`, protocol_version `1.2`,
  `exact_patch: true`, `agent_control_max_completion_tokens: 512`,
  scenario_count 12, strategy_count 2, repetitions 2, expected_cells 48,
  model Qwen2.5-Coder-14B-Instruct, quantization bnb-nf4, timeout 1200,
  max_attempts 3, max_completion_tokens_per_call 4096.
- **Commits:** `5daf88d` (Fix 1-4 code + tests) → `87da8f3` (release-tag
  constants aligned) → `fc1c7c8` (notebook anchor refresh + freeze report) →
  `b7ebb22` (provenance-verified freeze report).

## 8. Required truthful status

- **CANARY_LAUNCH_BASIS = YES** — the frozen `v0.9.22-d13r2-candidate` is a
  valid canary launch basis: exact-artifact dry-run canary 6/6 (protocol 1.2,
  0 calls/tokens, exact_patch + agent_control enforced), bundled-exact canary
  SEMANTIC PRE-MODEL gate **PASS** on the 3 canary scenarios, and the next REAL
  Pilot launch requires a real pilot-canary pass on this or a fresh exact
  candidate with its own tag decision.
- **FULL_48_LAUNCH_BASIS = NO** — the full 48-cell Pilot is NOT a launch basis:
  the pre-model semantic gate FAILS CLOSED on `saleor-loc-002` (`is_featured`
  known-absent) and the 7 unregistered Pilot scenarios. No real 48-cell launch
  may start from this candidate.
- **NEXT_ACTION = Run exactly one REAL 6-cell Kaggle canary if and only if
  CANARY_LAUNCH_BASIS=YES.**
- No Kaggle run and no stable release tag in this closure.
- The retired `v0.9.22-pilot-exec-ready` tag (peel `478261ff…`) and the
  `edae1b7e…8c4a` artifact are NOT reused; the D13r1 candidate
  (`v0.9.22-d13r1-candidate`, archive `9f120412…`) is SUPERSEDED by this D13R2
  candidate and remains immutable historical evidence.