# R6 Independent Audit — Final Technical and Handoff Review

**Audit model:** GPT-5.6 Thinking  
**Audit date:** 2026-08-01  
**Repository branch:** `experiment/three-arm-smoke-v2`  
**Audited HEAD:** `da6ccf3537022e62ea2ee7445e26a19fb226aa9d`  
**Decision:** **Technical R6 deployment implementation passes. R6 freeze is withheld only for one missing deployed-entrypoint regression and a bounded documentation-truth correction.**

---

## 1. Executive decision

The R6 code and generated Kaggle deployment bundle are technically credible.

Independent verification proved:

```text
Git HEAD manifest mismatches:
  code      = 0
  data      = 0
  notebook  = 0

Canonical/generated normalized parity problems = 0
Builder rerun working-tree changes             = 0
Bundle evaluator files                         = exact 3 + 3 fingerprints
Bundle Todo tests                              = exact five files
Sensitive/absolute-path scan findings          = 0
```

Independent focused tests on Linux/Python 3.13:

```text
tests/unit/test_build_upload_bundle.py
tests/unit/test_config_models.py
tests/unit/test_cli.py

70 passed
0 failed
```

The supplied Windows/Python 3.11.5 full suite reported:

```text
1,647 passed
32 skipped
0 failed
```

No canonical execution, selection, strategy, metric, regeneration, or evaluator behavior changed in R6.

R6 is not frozen yet because the repository handoff is not fully truthful and one high-value deployment regression is absent. Both can be closed in one small pass.

---

## 2. Commit-scope audit

### `5784a4f docs(audit): accept and freeze R5 production path proof`

```text
7 documentation files
```

Judgment: correct scope.

### `cb25e9f fix(deploy): preserve Smoke V2 runtime evidence in bundles`

```text
7 files
400 insertions
29 deletions
```

Primary contents:

```text
scripts/build_upload_bundle.py
tests/unit/test_build_upload_bundle.py
tests/unit/test_config_models.py
tests/unit/test_cli.py
configs/smoke.yaml
seven_arm_benchmark.py
.gitattributes
```

The `.gitattributes` manifest-LF rule was not listed in the original authorized artifact table, but it is a small, directly relevant cross-platform deployment safeguard. The audit accepts it as a justified scope extension. It must be disclosed in the final file ledger rather than omitted.

### `54a0462 chore(deploy): pin and build Scientific Smoke V2 bundle`

```text
47 files
5,561 insertions
940 deletions
```

The size is dominated by the generated `kaggle_upload/` mirror.

Canonical non-generated changes are limited to:

```text
notebooks/seven_arm_benchmark.ipynb
tests/unit/test_cli.py
tests/integration/test_kaggle_bundle_smoke_v2_preflight.py
```

Judgment: expected deployment-bundle scope; no parallel production architecture.

### `da6ccf3 docs(state): prepare Three-Arm Smoke V2 pre-Kaggle audit`

```text
12 documentation/state files
```

Judgment: correct commit type, but several documents remain internally stale or contradictory.

---

## 3. Builder and manifest audit

The builder uses one text contract for:

```text
.py .pyw .toml .txt .yaml .yml .md .cfg .ini .ipynb .sha256
```

It:

- normalizes code, data, and notebook text;
- preserves binary bytes;
- copies controlled repository tests;
- deploys only the six evaluator allowlist files;
- writes POSIX manifest keys;
- writes UTF-8/LF deterministic manifests;
- hashes final emitted bytes;
- clears and rebuilds only `kaggle_upload/`;
- does not invoke Git;
- leaves the working tree clean on an identical second build.

Independent Git-blob audit at `da6ccf3`:

| Manifest | Entries | Missing | Raw SHA-256 mismatches |
|---|---:|---:|---:|
| `code_manifest.json` | 87 | 0 | 0 |
| `data_manifest.json` | 56 | 0 | 0 |
| `notebook_manifest.json` | 1 | 0 | 0 |

Independent canonical/generated normalized comparison:

```text
0 mismatches
```

---

## 4. Bundle-content audit

Generated category inventory:

| Category | Files | Bytes |
|---|---:|---:|
| code | 87 | 619,346 |
| data | 56 | 172,210 |
| notebooks | 1 | 14,078 |
| category total | 144 | 805,634 |

The three manifest files add 15,659 bytes and are intentionally outside their own category manifests.

Verified evaluator deployment:

```text
todo_smoke_001_checks.py
todo_smoke_001_checks.py.sha256
todo_smoke_002_checks.py
todo_smoke_002_checks.py.sha256
todo_smoke_003_checks.py
todo_smoke_003_checks.py.sha256
```

Verified controlled Todo tests:

```text
__init__.py
test_models.py
test_permissions.py
test_serializers.py
test_views.py
```

No bundle hits were found for:

```text
C:\Users\...
/home/<user>/...
OpenRouter key values
HF token values
AWS access-key patterns
tests/support
scripted backend/harness files
cache/database artifacts
```

---

## 5. Notebook and identity audit

The canonical and generated notebooks are code-cell identical.

They use:

```text
profile                          scientific-smoke-v2
backend                          kaggle-qwen
protocol                         1.0
max attempts                     3
max completion tokens per call  4096
max total workflow tokens        0
timeout                          300
resume max-runs                  1
continuous max-runs              absent
```

Pinned identity:

```text
SOURCE_COMMIT     = cb25e9fb3e6cb5eecead4dc640aedda30d4625b0
DEPLOYED_BUILD_ID = cb25e9f
```

The full source commit exists and is an ancestor of R6 HEAD.

Using the runtime-source commit as deployed build identity is compatible with the current checkpoint implementation, which defaults deployed identity to source identity. The separate generated bundle commit remains recorded as `54a0462`.

No fabricated future commit is used.

---

## 6. Independent generated-entrypoint execution

The audit directly executed:

```text
kaggle_upload/code/seven_arm_benchmark.py
```

with:

```text
PYTHONPATH=kaggle_upload/code/src
--dry-run
--profile scientific-smoke-v2
--data-dir kaggle_upload/data
--source-commit cb25e9fb3e6cb5eecead4dc640aedda30d4625b0
--deployed-build-id cb25e9f
--max-attempts 3
--max-completion-tokens-per-call 4096
--max-total-workflow-tokens 0
--timeout 300
```

Observed:

```text
27 bundled scenarios loaded
3 exact Smoke V2 scenarios selected
9-run execution plan created
9 run records persisted
3 exact strategy IDs
3 exact scenario IDs
9 statuses = succeeded
checkpoint total_planned = 9
process exit code = 0
```

This proves the generated CLI and generated data can execute together outside the canonical source tree.

This evidence is currently manual audit evidence only. It must be converted into one regression test before R6 freeze.

---

## 7. Missing regression — TD-R6-ENTRYPOINT-001

Current deployment integration tests prove:

```text
bundled baseline tests
bundled evaluator assets
three correct scenario implementations
migration creation
baseline validation
evaluator validation
leakage exclusions
```

They do not execute the generated CLI entrypoint itself.

Add one test to the existing file:

```text
tests/integration/test_kaggle_bundle_smoke_v2_preflight.py
```

Required test:

```text
test_bundled_cli_dry_run_executes_exact_nine_cell_plan
```

It must run all nine dry-run cells through the generated script and assert exact persisted matrix and identity.

This is a focused addition, not a new test framework.

---

## 8. Documentation-truth defects

### D1 — README legacy release presentation

The top badge still presents:

```text
v0.7.0-smoke-passed
```

as an unqualified release.

The roadmap also says:

```text
[x] Kaggle real smoke (7/7 arms, Qwen confirmed)
[ ] Checkpoint/resume support
```

This conflicts with the current Three-Arm status:

```text
legacy Seven-Arm smoke = historical
current V2 real Qwen = 0/9
checkpoint/resume = implemented
```

Required: clearly label the badge and 7/7 item as legacy orchestration evidence, and make the current V2 roadmap authoritative.

### D2 — SYSTEM_STATE latest identity

`SYSTEM_STATE.md` correctly states R6 status at the top, but later says:

```text
Latest Commit = docs(audit): accept and freeze R5 production path proof
```

This is false at audited HEAD `da6ccf3`.

The old Seven-Arm Kaggle smoke is also listed without a legacy qualifier.

### D3 — latest_phase_report is not actually latest-first

`reports/latest_phase_report.md` begins as an R4 report and says R5 is in progress. R6 information is appended near the end.

A new AI reading from the beginning can make the wrong decision.

Required: replace the file with one concise current R6 report. Historical phase details already exist in dedicated records and must not be repeated.

### D4 — START_HERE metadata drift

Its current-state section is good, but the key-document table describes:

```text
latest_phase_report = R5 acceptance / R6 in progress
```

It also treats an external package path as execution authority. Future sessions/accounts may not have that external directory.

Repository-contained audit and handoff documents must be sufficient.

### D5 — MASTER_IMPLEMENTATION_PLAN is stale and duplicated

It still presents old approved strategies, old repository statuses, and a pre-R3 phase map as current. A duplicate historical block is present.

Required:

- add a short authoritative current execution track at the top;
- mark the old phase map as historical;
- remove the duplicated copy;
- state the exact path from R6 correction to push, 9 real Smoke runs, tag, and Pilot freeze.

Do not redesign the scientific protocol in this document.

### D6 — PROJECT_HANDOFF historical status leakage

The top current state is mostly correct, but older embedded sections still state:

```text
R5 in progress
R6 blocked
```

They must be explicitly marked historical/superseded or removed from the current-decision path.

The handoff must not require external prompt packages to understand current state.

---

## 9. Over-engineering assessment

### Canonical production

No R6 production over-engineering was found.

`src/benchmark/**` was not modified.

`seven_arm_benchmark.py` received help-text changes only.

### Builder/test layer

New canonical test code:

```text
test_build_upload_bundle.py                     252 lines
test_kaggle_bundle_smoke_v2_preflight.py        204 lines
```

This is proportionate to the deployment risks closed:

```text
cross-platform bytes
manifest integrity
controlled tests
evaluator deployment
scenario preflight
bundle leakage
```

Do not refactor these tests in the correction pass.

### Generated diff

The large bundle diff is expected derived output, not 5,000 lines of new production design.

---

## 10. Required minimal correction

One bounded correction pass:

```text
one integration regression
one test-only commit
documentation truth cleanup
one docs-only commit
full gates once
stop for re-audit
```

Prohibited:

```text
production changes
builder changes
bundle rebuild logic changes
notebook/config changes
scenario/evaluator changes
R5 changes
push
tag
Kaggle launch
broad documentation expansion
```

---

## 11. Status and progress

```text
R4 = accepted/frozen
R5 = accepted/frozen
R6 technical implementation = passed
R6 phase freeze = blocked by small audit correction
Local scripted Smoke = 9/9
Real Qwen Smoke = 0/9
Push = not performed
Tag = not created
Pilot = not authorized
```

Estimated local closure:

```text
R6 implementation ≈ 97% complete
remaining = one regression + documentation-truth commit + re-audit
```

Immediate path:

```text
R6 final correction
→ independent re-audit
→ push branch
→ verify local/remote equality
→ Kaggle environment preflight
→ nine real Qwen Smoke records
```

Far path:

```text
real Smoke result audit
→ v2.0.0-scientific-smoke tag
→ freeze Pilot matrix
→ Pilot execution
→ research experiment
→ statistical analysis
→ paper evidence package
```

---

# R6 Final Correction Addendum (2026-08-01)

**Executing model:** DeepSeek V4 Flash Free through OpenCode Zen (Build mode)
**Branch:** `experiment/three-arm-smoke-v2`
**Starting HEAD:** `da6ccf3537022e62ea2ee7445e26a19fb226aa9d`
**Backup branch:** `backup/r6-pre-final-audit-da6ccf3` (no tag)
**Scope:** one integration regression + documentation-truth cleanup only

## Test correction commit

```text
40c7a47  test(deploy): prove bundled V2 CLI execution plan
tests/integration/test_kaggle_bundle_smoke_v2_preflight.py
1 file changed, 143 insertions(+)
```

`test_bundled_cli_dry_run_executes_exact_nine_cell_plan` runs the real
generated CLI (`kaggle_upload/code/seven_arm_benchmark.py`) with the bundled
data via subprocess (`PYTHONPATH=kaggle_upload/code/src`,
`PYTHONDONTWRITEBYTECODE=1`, no HF/OpenRouter keys, `cwd=tmp_path`) and asserts:

```text
return code == 0
output contains "Selected 3 scenario(s) for profile=scientific-smoke-v2"
output contains "Execution plan: 9 pending"
output contains "Benchmark complete: 9/9 runs"
working tree unchanged (git status before == after)
run_records.jsonl: 9 records, all succeeded, profile, repetition 1,
  model_metadata.dry_run "True", model_calls 0, total_workflow_tokens 0
scenario set = todo-smoke-001/002/003
strategy set = monolithic, selective, iterative_repository_agent
exact scenario × strategy Cartesian product = 9 unique pairs
checkpoint.json: total_planned 9, total_completed 9,
  completion_status "completed", exact scenario_ids/strategy_names,
  source_commit cb25e9f...4625b0, deployed_build_id cb25e9f
source_identity.json: exact source/build/profile/dry_run
benchmark_summary.json: 3 strategy keys, run_count 3 / success_count 3 /
  failed_count 0 per strategy, total records 9
```

**TD-R6-ENTRYPOINT-001 = closed.**

## Focused gate results (test stage)

```text
compileall  preflight file                  clean
pytest      preflight file                  9 passed
pytest      build_upload + config + cli + preflight   79 passed
ruff        preflight file                  clean
git diff --check                            clean
```

## Documentation-truth corrections (D1–D6)

```text
D1 README badge/roadmap relabeled legacy; current V2 milestones authoritative
D2 SYSTEM_STATE latest identity = test commit 40c7a47 / current docs HEAD; 7/7 qualified legacy
D3 latest_phase_report replaced with concise current R6 report (latest-first)
D4 START_HERE lists R6 correction state; repository-contained files required;
   external packages = historical provenance only
D5 MASTER_IMPLEMENTATION_PLAN: Authoritative Current Execution Track at top;
   old phase map/strategy lists marked historical
D6 PROJECT_HANDOFF: exact audited HEAD, exact test commit, current docs HEAD,
   .gitattributes disclosed, bundled CLI 9/9 recorded, historical sections marked
```

## Final gate results (documentation stage)

Reported in the final OpenCode report; full suite, Ruff, Mypy, compileall,
builder rerun, `git diff --check`, and `git status --short` are run once after
the documentation changes.

## Correction status

```text
R6 = FINAL CORRECTION COMPLETE PENDING INDEPENDENT RE-AUDIT
TD-R6-ENTRYPOINT-001 = closed
documentation truth defects D1–D6 = closed
.gitattributes manifest-LF rule = audit-approved scope extension
production/builder/bundle/notebook/config changes = none
Real Smoke = 0/9
Push = blocked
Tag = blocked
Working tree = clean
```

**R6_FINAL_CORRECTION_REAUDIT_REQUIRED**
