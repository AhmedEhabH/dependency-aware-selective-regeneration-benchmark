# R6 Bundle Parity and Pre-Kaggle Handoff

**Phase:** R6 deployment closure
**Date:** 2026-08-01
**Branch:** `experiment/three-arm-smoke-v2`
**Status:** **R6 ACCEPTED AND FROZEN — MILESTONE BRANCH PUBLISHED**
**Accepted HEAD:** `949e9c2`
**Freeze commit:** `4b2dd27` (docs(audit): accept and freeze R6 deployment closure) — exact first publication HEAD
**Publication:** branch published to origin; upstream `origin/experiment/three-arm-smoke-v2`; local/remote equality verified before publication-status commit
**Next:** Kaggle environment preflight / real Qwen launch
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
Final accepted full suite = 1,648 passed, 32 skipped, 0 failed (final independent re-audit)
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
R6 ACCEPTED AND FROZEN
local scripted = 9/9
bundled CLI dry-run = 9/9
real Qwen = 0/9
Kaggle not launched
push PUBLISHED (upstream set, local/remote equal)
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
Accepted HEAD      = 949e9c2
Backup branches    = backup/r5-pre-audit-c3ecad2, backup/r6-pre-execution-7761c48,
                     backup/r6-pre-final-audit-da6ccf3 (all preserved, no tags)
R5 acceptance      = 5784a4f
Runtime source     = cb25e9f
Bundle commit      = 54a0462
R6 test commit     = 40c7a47
Documentation      = 949e9c2 (docs(audit): close R6 handoff truth gaps)
R6 freeze commit   = 4b2dd27 (first publication HEAD)
Working tree       = clean
Upstream           = origin/experiment/three-arm-smoke-v2
Local/remote       = equal (verified before and after publication-status commit)
R6 status          = ACCEPTED AND FROZEN (949e9c2)
Real Smoke         = 0/9
Pilot              = NOT AUTHORIZED
Push               = PUBLISHED
Tag                = BLOCKED
```

## 8. Next action

```text
1. Record publication status (this pass)
2. Push normally and verify final local/remote equality
3. Kaggle environment preflight and nine real Qwen Smoke records
4. Independent result audit, then v2.0.0-scientific-smoke tag
5. Pilot authorization under the frozen protocol
```

Do not tag, merge, force-push, or launch Kaggle now.

## 9. R6 final correction (2026-08-01)

The independent audit (GPT-5.6 Thinking, `docs/R6_INDEPENDENT_AUDIT_AND_CORRECTION_REPORT.md`)
passed the R6 technical deployment implementation and withheld freeze for one
missing deployed-entrypoint regression plus documentation-truth cleanup. The
bounded correction closed both:

```text
test commit 40c7a47  test(deploy): prove bundled V2 CLI execution plan
  test_bundled_cli_dry_run_executes_exact_nine_cell_plan runs the real
  generated CLI with the bundled data via subprocess and asserts the exact
  3×3×1 persisted matrix and identity; TD-R6-ENTRYPOINT-001 closed.
docs HEAD            docs(audit): close R6 handoff truth gaps
  D1 README legacy badge/roadmap relabeled, current V2 milestones authoritative
  D2 SYSTEM_STATE latest identity = current docs HEAD; 7/7 qualified legacy
  D3 latest_phase_report = concise current R6 report (latest-first)
  D4 START_HERE current R6 correction state; repo-contained docs sufficient
  D5 MASTER_IMPLEMENTATION_PLAN current track + historical markers
  D6 PROJECT_HANDOFF exact commits + .gitattributes disclosure + bundled CLI 9/9
```

Final correction gates: preflight file 9/9; grouped gate 79 passed; ruff clean
on changed file; `git diff --check` clean. The final independent re-audit
(GPT-5.6 Thinking, 2026-08-01, HEAD `949e9c2`) **accepted R6** and authorized
freeze and milestone-branch publication (recorded in
`docs/R6_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md`); final accepted full
suite = 1,648 passed / 32 skipped / 0 failed. `.gitattributes` manifest-LF rule
= audit-approved scope extension, disclosed in `docs/PROJECT_HANDOFF.md` and
this ledger.

## Post-R6 update (2026-08-01) — Kaggle runtime fix

The R6-published deployment was launched twice for real on Kaggle; both runs
failed before any model call (`exp-20260801-024041`, `exp-20260801-024624`;
both 9 planned / 0 succeeded / 9 failed / 0 model calls / 0 tokens; first
failure = workspace isolation). The real runtime blockers were closed on branch
`fix/kaggle-smoke-v2-runtime-blockers` (fix commit `de3163f`, bundle pin commit
`fb60972`) and are recorded in
`selective_updates/records/KAGGLE-SMOKE-V2-RUNTIME-FIX.md`. The corrected bundle
is pinned to runtime source `de3163f12d51c31d3f488897ed2047821da3b190` and was
rebuilt only via `scripts/build_upload_bundle.py` (144 files / 815,004 bytes).
The two failed attempt outputs are preserved on the results dataset and must
not be deleted. R6 itself is unchanged and remains ACCEPTED AND FROZEN.

KAGGLE_RUNTIME_FIX_AUDIT_REQUIRED
