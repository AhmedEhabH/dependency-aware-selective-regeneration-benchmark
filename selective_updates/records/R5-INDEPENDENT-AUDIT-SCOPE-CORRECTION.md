# R5 Independent Audit — Scope Correction Record

**ID:** R5-INDEPENDENT-AUDIT-SCOPE-CORRECTION
**Date:** 2026-07-31
**Status:** CORRECTION COMPLETE — PENDING INDEPENDENT RE-AUDIT
**Branch:** experiment/three-arm-smoke-v2
**Original audited HEAD:** c3ecad2
**Backup branch:** backup/r5-pre-audit-c3ecad2 (preserved; do not delete before re-audit)
**Audit source:** `..\R5_INDEPENDENT_AUDIT_SCOPE_AND_EVIDENCE_2026-07-31.md`
**Directive source:** `..\OPENCODE_R5_SCOPE_CLEANUP_DIRECTIVE.md`
**R6 debt recorded:** TD-R6-BUNDLE-MANIFEST-001

---

## Requirement

The independent R5 audit found canonical production was not broadly damaged, but
commit `6650b00` accidentally included 31 premature `kaggle_upload/` files and
introduced a committed notebook-manifest mismatch. R5 could not be accepted or
advanced to R6 in that state. Because the branch had not been pushed and had no
upstream, the local R5 tail was rebuilt cleanly without any Kaggle bundle
change, three R5 evidence boundaries were tightened, the stale handoff
documents were corrected, all gates were run, and the branch was stopped for
independent re-audit.

## What was preserved

- `8fafb50` — `fix(validation): reconcile Smoke V2 baseline contracts`
  (pre-results benchmark correction, untouched).
- `a24a9cd` — `docs(protocol): record pre-results Smoke V2 baseline amendment`
  (amendment documentation, untouched).
- `f5ae826` — the explicit R4 acceptance/freeze commit
  (`docs(audit): accept and freeze R4 token metric contract`).

## What was rebuilt (local R5 tail)

The commits after `a24a9cd` were rebuilt as three clean commits:

```text
875e4d1  fix(execution): preserve generated file bytes on Windows
ee148fa  test(smoke): prove nine scripted production records
docs(audit)  docs(audit): record R5 completion pending re-audit (this commit)
```

- The execution-fix commit contains exactly two files:
  `src/benchmark/execution/regeneration.py` and
  `tests/unit/execution/test_regeneration.py`.
- The test commit contains exactly the three R5 files:
  `tests/support/scripted_llm_backend.py`,
  `tests/support/scripted_smoke_v2.py`,
  `tests/integration/test_scientific_smoke_v2_production_path.py`.
- The documentation commit contains no code, no tests, no bundle files, no
  README, and no notebooks.
- The accidental `6650b00` bundle content is recorded here for traceability.
  That commit carried 33 files (2 execution-fix files + 31 `kaggle_upload/`
  derivative files); the 31 bundle files were explicitly deferred to R6. Local
  history was rebuilt before any push (the branch has no upstream).

## Actual R5 file line counts (calculated, not quoted)

```text
tests/support/scripted_llm_backend.py                         268
tests/support/scripted_smoke_v2.py                           699
tests/integration/test_scientific_smoke_v2_production_path.py 717
```

These replace the stale `216 / 597 / 577` values in the old documentation.

## Evidence tightening applied

### Exact selected/generated path contract

The positive cell assertion now asserts exact equality for all nine cells using
both the record and the backend transcript:

```text
backend.generation_paths_requested == expected generation paths
record.selected_artifact_count      == len(expected)
record.regeneration_model_calls     == len(expected)
record.regenerated_artifact_count   == len(expected)
record.preserved_artifact_count     == len(editable) - len(expected)
```

Expected generation paths are derived from the sorted artifact universe
(`resolve_allowed_artifacts` sorts alphabetically):

```text
monolithic = tuple(sorted(SMOKE_V2_EDITABLE_PATHS))
selective  = tuple(sorted(SMOKE_V2_EXPECTED_SELECTION[scenario]))
agent      = tuple(sorted(SMOKE_V2_EXPECTED_SELECTION[scenario]))
```

Exact count table (matches the audit):

| scenario | monolithic | selective | agent |
|---|---|---|---|
| todo-smoke-001 | 5 | 3 | 3 |
| todo-smoke-002 | 5 | 2 | 2 |
| todo-smoke-003 | 5 | 4 | 4 |

An extra selected path with baseline-identical output would now be caught by
`generation_paths_requested` even if it disappears from the workspace-diff set.

### Snapshot mutation negative control

`snapshot_hash_before` is now calculated before the deliberate
`mutate_snapshot` action removes `todo/views.py`, so the negative control proves
a transition from an accepted snapshot hash to a mutated hash:

```text
snapshot_hash_before != snapshot_hash_after
record.status == failed
failure stage == runner
failure message identifies the invalid active snapshot path (views.py)
```

No new snapshot subsystem was added.

### Truthful persisted timestamps

`started_at` is captured immediately before `pipeline.run_scenario_by_id` and
`ended_at` immediately after it returns, and both are passed into the real
`_to_run_record_data` conversion. They are no longer created after the run. One
exact test proves, for all nine persisted records:

```text
started_at <= ended_at
both values parse as timezone-aware ISO timestamps
```

No timing tolerance or sleep was added.

## Negative-control wording correction

The old documentation presented all ten controls as fail-closed failures. The
tests assert the truth:

```text
dry_run=True and enable_regeneration=False are valid guarded no-op modes
no-new-migration (pre-applied migration) is a failed validation control
the remaining failure controls fail at their exact intended stage
```

The code was not forced to fail to match the old wording; the documentation was
corrected to match the tests.

## Bundle-scope verification

```text
git diff --name-only a24a9cd..HEAD -- kaggle_upload   -> empty
git diff --name-only f5ae826..HEAD -- kaggle_upload   -> empty
```

The final R5 branch contains no R5 `kaggle_upload` diff.

## Git-tree manifest audit (read-only, `git show HEAD:<path>` bytes)

```text
code_manifest.json:     total=77, mismatched=0, missing=0
data_manifest.json:     total=48, mismatched=10, missing=0 (all pre-existing, unchanged by R5)
notebook_manifest.json: total=1,  mismatched=0, missing=0
```

- Git-tree data-manifest mismatches are pre-existing and are an R6 blocker, not
  an R5 failure.
- The notebook-manifest mismatch introduced by the old `6650b00` bundle content
  is removed by the history rebuild; the final branch's bundle matches the
  pre-R5 state.
- `scripts/build_upload_bundle.py` was NOT modified in R5. Root cause
  (code text normalized before manifest generation; data files and notebooks
  not normalized; manifests hash worktree bytes) is recorded as an R6 blocker.

## R6 debt recorded

### TD-R6-BUNDLE-MANIFEST-001 — committed bundle manifests can mismatch committed blobs
- **Severity:** TD-0 (deployment integrity / traceability)
- **Closure:** bounded RF-4/R6 bundle-builder correction — normalize data and
  notebook files before manifest generation (or hash committed blobs), then
  rebuild and verify the Kaggle bundle from committed bytes.
- **Checkpoint:** R6 closure (blocked until R5 re-audit acceptance)
- **Evidence:** Git-tree code-manifest mismatches = 0; Git-tree
  data-manifest mismatches = 10 pre-existing; Git-tree notebook-manifest
  mismatch introduced by old `6650b00` = 1 (removed by the history rebuild);
  final R5 branch contains no R5 `kaggle_upload` diff.

## Commit boundaries

```text
f5ae826  R4 explicit acceptance/freeze commit (preserved)
8fafb50  R5 benchmark correction (preserved)
a24a9cd  R5 amendment documentation (preserved)
875e4d1  rewritten R5 execution-fix commit (2 files)
ee148fa  rewritten R5 test-proof commit (3 files)
docs(audit)  R5 audit documentation commit (documentation only, this commit)
```

## Status

```text
R5 status: CORRECTION COMPLETE — PENDING INDEPENDENT RE-AUDIT
R6 status: BLOCKED
Kaggle status: BLOCKED
Push status: NOT PERFORMED
Tag status: BLOCKED
Next action: independent R5 re-audit before accept/freeze R5
```

**R5_SCOPE_CLEANUP_REAUDIT_REQUIRED**
