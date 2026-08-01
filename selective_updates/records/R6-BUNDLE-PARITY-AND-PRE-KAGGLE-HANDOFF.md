# R6 Bundle Parity and Pre-Kaggle Handoff

**Phase:** R6 deployment closure
**Date:** 2026-08-01
**Branch:** `experiment/three-arm-smoke-v2`
**Status:** **R6 COMPLETE PENDING INDEPENDENT AUDIT**
**Next:** independent R6 audit before push / Kaggle launch / tag creation

---

## 1. Authorized scope

R6 implemented exactly the corrected single-pass directive
(`..\R6_OpenCode_Package_CORRECTED\02_OPENCODE_R6_CORRECTED_EXECUTION_DIRECTIVE.md`,
which supersedes every earlier R6 prompt/directive).

| Feature | Status |
|---|---|
| R6-F01 R5 acceptance record | COMPLETE (Commit A `5784a4f`) |
| R6-F02 deterministic builder | COMPLETE (`scripts/build_upload_bundle.py`) |
| R6-F03 controlled Todo tests in data bundle | COMPLETE (exact five files, 47 methods) |
| R6-F04 exact evaluator allowlist in code bundle | COMPLETE (3 `.py` + 3 `.sha256`) |
| R6-F05 valid V2 smoke config | COMPLETE (`configs/smoke.yaml`) |
| R6-F06 current CLI help | COMPLETE (`seven_arm_benchmark.py`, help/description only) |
| R6-F07 V2 notebook pinned to existing runtime commit | COMPLETE (`notebooks/seven_arm_benchmark.ipynb`) |
| R6-F08 generated bundle | COMPLETE (`kaggle_upload/`) |
| R6-F09 deployment preflight integration | COMPLETE (`tests/integration/test_kaggle_bundle_smoke_v2_preflight.py`) |
| R6-F10 worktree/index/tree manifest audits | COMPLETE (0 / 0 / 0 mismatches) |
| R6-F11 README/handoff/report update | COMPLETE (this record plus section 19 docs) |

## 2. Commits

| Commit | Message | Contents |
|---|---|---|
| `5784a4f` | `docs(audit): accept and freeze R5 production path proof` | R5 acceptance record + status docs |
| `cb25e9f` | `fix(deploy): preserve Smoke V2 runtime evidence in bundles` | Commit B — runtime source commit |
| `54a0462` | `chore(deploy): pin and build Scientific Smoke V2 bundle` | Commit C — pinned/generated deployment |
| Commit D | `docs(state): prepare Three-Arm Smoke V2 pre-Kaggle audit` | documentation only (created after this record; hash recorded in git history) |

```text
RUNTIME_SOURCE_COMMIT = cb25e9fb3e6cb5eecead4dc640aedda30d4625b0
RUNTIME_BUILD_ID      = cb25e9f
DEPLOYED_BUNDLE_COMMIT = 54a0462
```

## 3. Bundle parity and deployment facts

```text
manifest committed-tree counts = code 0 / data 0 / notebook 0
worktree manifest counts       = code 0 / data 0 / notebook 0
git-index manifest counts      = code 0 / data 0 / notebook 0
Todo baseline tests deployed   = exact five files, 47 test methods
evaluator assets deployed      = 3 + 3 SHA-256 fingerprints
tests/support files            = 0
scripted/harness files         = 0
forbidden artifacts (caches, DBs, .env, .pyc) = 0
bundle totals                  = code 87 files / data 56 files / notebooks 1 / total 144 files, 805,634 bytes
```

The bundle was built only through `python scripts/build_upload_bundle.py`;
`kaggle_upload/` was never manually edited. No Git call exists in the builder.
Manifest relative paths use POSIX separators; values are raw SHA-256 of the
final emitted bytes; manifests are written with `sort_keys=True`,
`indent=2`, trailing newline, and LF line endings.

## 4. Deployment preflight evidence

Three scenario cases (`todo-smoke-001`, `todo-smoke-002`, `todo-smoke-003`)
were executed against the generated bundle: baseline copy from
`kaggle_upload/data/repositories/todo`, exact five test files / 47 methods
proven, `get_correct_sources_for_scenario` applied, `makemigrations todo
--noinput` produced exactly one new migration with old migration hashes
unchanged, `manage.py test todo --verbosity 1` returned code 0 and reported
`Ran 47 tests`, and the real scenario evaluator ran with
`canonical_project_root=kaggle_upload/code` and a workspace outside the code
root, returning pass with a non-empty expected check list and no
`tests/evaluator_assets` inside the generated workspace. Global contract:
exact six evaluator files, each `.py` hash equals its `.sha256`, no
`tests/support`, no scripted backend/harness, no caches, DBs, absolute local
paths, or secret values.

## 5. Validation

```text
Full suite        = 1,647 passed, 32 skipped, 0 failed (R5 baseline 1,625 passed)
Ruff              = 94 findings at both starting HEAD 7761c48 and R6 HEAD; identical set, zero new
Mypy --strict     = 0 errors (unchanged from baseline)
Compileall        = clean
git diff --check  = clean
Final builder run = byte-identical rebuild; working tree clean
```

## 6. Required status statements

```text
R4 accepted/frozen
R5 accepted/frozen
R6 complete pending independent audit
local scripted = 9/9
real Qwen = 0/9
Kaggle not launched
push not performed
tag not created
Pilot not authorized
```

Pilot wording:

```text
exact final run denominator not frozen;
minimum 7–12 changes across at least 3 real repositories;
current descriptive 48-run config is not authorization.
```

Smoke evidence is non-publication. No real Qwen results are claimed.

## 7. Final project state

```text
Branch             = experiment/three-arm-smoke-v2
Starting HEAD      = 7761c48
R5 acceptance      = 5784a4f
Runtime source     = cb25e9f
Bundle commit      = 54a0462
Documentation      = Commit D
Working tree       = clean
Upstream           = none
R6 status          = COMPLETE PENDING INDEPENDENT AUDIT
Real Smoke         = 0/9
Pilot              = NOT AUTHORIZED
Push               = BLOCKED PENDING AUDIT
Tag                = BLOCKED
```

## 8. Next action

```text
1. Independent R6 audit (GPT-5.6 Thinking) before push
2. Push and local/remote equality
3. Kaggle preflight and nine real Qwen Smoke records
4. Independent result audit, then scientific-smoke tag
5. Pilot authorization under the frozen protocol
```

Do not push, tag, merge, or launch Kaggle during the pending audit.

R6_DEPLOYMENT_CLOSURE_AUDIT_REQUIRED
