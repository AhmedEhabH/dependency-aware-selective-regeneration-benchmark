# R4 Independent Re-Audit and Freeze Report

**Audit model:** GPT-5.6 Thinking
**Audit date:** 2026-07-31
**Repository branch:** `experiment/three-arm-smoke-v2`
**Audited HEAD:** `a46213c`
**Status:** **ACCEPTED AND FROZEN FOR PROGRESSION TO R5**
**Release status:** Internal engineering milestone only — not a public release and not taggable yet.

---

## 1. Audit decision

R4 is accepted after the audit corrections in:

```text
c928bd9 fix(validation): pin evaluator assets to canonical LF
cc32b17 fix(metrics): preserve exhausted workflow token budgets
a46213c docs(audit): record R4 audit corrections
```

The corrected implementation closes the two defects identified by the previous independent audit:

1. A configured workflow-token budget could be reopened as unlimited after being consumed exactly to zero.
2. Canonical evaluator integrity depended on Windows line-ending behavior.

No additional R4 production correction is required before R5.

---

## 2. Repository evidence

The audited repository was on:

```text
branch: experiment/three-arm-smoke-v2
HEAD:   a46213c
```

The working tree was clean.

The correction commits are narrowly scoped:

- `c928bd9`: `.gitattributes` only.
- `cc32b17`: four production files and two R4 test files.
- `a46213c`: five documentation files only.

No evaluator source file or `.sha256` file was committed as part of the LF portability correction.

The branch currently has no configured upstream. Push remains governed by the project plan and must not be confused with a release or tag.

---

## 3. Defect A — exact exhaustion

The corrected runtime representation is:

```text
None     = no configured workflow-total limit
0        = configured workflow-total limit is exhausted
positive = configured workflow tokens remaining
```

The public configuration meaning of zero remains unlimited. The distinction is introduced only at the runtime allowance boundary.

Reviewed production paths:

```text
src/benchmark/execution/budgets.py
src/benchmark/execution/regeneration.py
src/benchmark/strategies/iterative_agent.py
src/benchmark/execution/runner.py
```

Verified properties:

- `BudgetManager.runtime_remaining_total_tokens` returns `None`, zero, or a positive integer with unambiguous meaning.
- `resolve_completion_allowance` returns the per-call limit only for `None`.
- A runtime zero returns zero allowance.
- Executor and Agent retain `has_limit` from the original configured runtime state.
- All five Runner call sites forward `runtime_remaining_total_tokens`.
- Public unlimited workflows remain unlimited.
- Exact exhaustion blocks later model calls.

### Independent direct-path evidence

Executor:

```text
captured completion limits: [20]
executed model calls:       1
reported workflow tokens:   20
artifact statuses:          generated, rejected
termination evidence:       Token budget exhausted before src/b.py
```

Agent `analyze_impact`:

```text
captured completion limits: [20]
executed model calls:       1
reported workflow tokens:   20
termination evidence:       no paths selected after exploration
```

Agent `revise_plan`:

```text
captured completion limits: [20]
executed model calls:       1
reported workflow tokens:   20
termination evidence:       revision failed to select paths
```

The original audit defect is no longer reproducible.

---

## 4. Defect B — evaluator byte stability

The following files are explicitly pinned to LF by `.gitattributes`:

```text
tests/evaluator_assets/todo_smoke_001_checks.py
tests/evaluator_assets/todo_smoke_002_checks.py
tests/evaluator_assets/todo_smoke_003_checks.py
```

Independent byte-level checks proved:

| Asset | Raw worktree SHA-256 | Expected `.sha256` | CR bytes | Index/worktree blob |
|---|---|---|---:|---|
| `todo_smoke_001_checks.py` | `eeb95c8757b1db12e401e3085b4dde0bf3d7025acb13eccd8fe67c4797ab7f53` | same | 0 | identical |
| `todo_smoke_002_checks.py` | `74b6b14188f9194dd614cafaf0344c851826b80420ee29ed5a68b44f24eca7a2` | same | 0 | identical |
| `todo_smoke_003_checks.py` | `c0cd38916d242040f395ef2332b9358262cc0da72648ce1561b1dea9a3cb8471` | same | 0 | identical |

`git check-attr` reports `text eol=lf` for all three files.

The evaluator sources and fingerprints remain scientifically unchanged.

---

## 5. Test evidence

### User environment — Windows / Python 3.11.5

The supplied final run collected 1616 tests and reported:

```text
1584 passed
32 skipped
0 failed
```

### Independent audit environment

The independent environment ran the R4 focused test files:

```text
tests/unit/execution/test_r4_token_and_metrics.py
tests/integration/test_r4_metric_contract.py
```

Result:

```text
105 passed
0 failed
```

The same run exercised Linux/Python 3.13 collection and execution, providing additional compatibility evidence outside the project's supported Python 3.11 environment.

The evaluator integration runtime could not be independently repeated in the audit container because Django was not installed there. This does not invalidate acceptance because:

- evaluator bytes and hashes were independently verified;
- the supplied Windows full suite executed the evaluator integration tests successfully;
- no evaluator logic changed in the correction.

Ruff and mypy were not installed in the independent audit container. The supplied correction report records zero new Ruff findings against baseline and zero mypy errors on the changed production files. Static AST parsing, compileall, clean diff, and direct semantic checks were independently performed.

---

## 6. Quality and scope judgment

The correction is minimal and not over-engineered.

It introduces:

- one runtime property;
- one unambiguous `int | None` contract;
- narrow forwarding changes;
- focused exact-boundary regression tests;
- one platform line-ending rule.

It does not introduce a new budget subsystem, backend, strategy, persistence format, or compatibility layer.

No R4 TD-0 or TD-1 issue remains known after this audit.

Non-blocking TD-2 observations remain scheduled for RF-4:

- `asyncio.get_event_loop()` deprecation warning in the regeneration executor under newer Python versions;
- `datetime.utcnow()` deprecation warning in reporting;
- documentation duplication and oversized phase specifications;
- possible consolidation of repeated test-support source strings.

These must not reopen R4.

---

## 7. Documentation judgment

The correction documentation accurately records both defects and the evidence.

The repository freeze record (`docs/R4_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md`) is this file, created at the start of R5 and updated with the principal navigation state:

```text
docs/PROJECT_HANDOFF.md
reports/latest_phase_report.md
docs/START_HERE.md
SYSTEM_STATE.md
selective_updates/CHANGE_INDEX.md
selective_updates/records/R4-TOKEN-AND-METRIC-CONTRACT.md
docs/V2_R3B_TO_KAGGLE_NO_DISCRETION_EXECUTION_SPEC.md
```

`README.md` remains intentionally deferred to R6 because R5 is still an internal production-path proof, not a stable user-facing release.

---

## 8. Authorization

The following is now authorized:

```text
R5 — nine non-dry scripted production records
```

The following remains blocked:

```text
R6
Kaggle execution
Pilot
merge to main
stable release tag
v2.0.0-scientific-smoke
```

R5 must remain a local engineering proof. It must not be represented as Qwen model-quality evidence.

---

## 9. Immediate plan

```text
Record R4 freeze in documentation
→ build the R5 scripted backend and harness
→ prove one scenario across all three arms
→ expand to the complete 3 × 3 matrix
→ prove persistence, isolation, and negative controls
→ produce exactly nine non-dry records
→ run full gates
→ commit code/tests
→ update handoff/report/debt
→ stop for independent R5 audit
```

No broad refactor is authorized during R5. Genuine production defects exposed by a production-path test receive their own focused test, minimal fix, and separate commit.

---

## 10. Final decision

```text
R4 status: ACCEPTED AND FROZEN
R5 status: AUTHORIZED / IN PROGRESS
R6 status: BLOCKED
Kaggle status: BLOCKED
Push status: governed by R6 plan unless separately authorized
Tag status: BLOCKED
```

**R4_ACCEPTED_R5_AUTHORIZED**
