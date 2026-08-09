# V2 R2 Root-Cause Audit and Correction Specification

**Document status:** HISTORICAL — preserved for audit traceability only, not binding  

> This record has been migrated from `docs/V2_R2_ROOT_CAUSE_AND_CORRECTION_SPEC.md`.
> It documents the R2 root-cause analysis and correction specification as of 2026-07-28.
> The findings are historical: the corrections described herein have been superseded
> by the final R2 audit-closure microtask. Do not treat this document as an active
> specification or binding contract.

**Original status (archived):** Mandatory correction contract  
**Target branch:** `experiment/three-arm-smoke-v2`  
**Audited HEAD:** `b129d42` with uncommitted R2 changes  
**Implementation model:** DeepSeek V4 Flash Free through OpenCode Zen, Build mode  
**Audit model:** GPT-5.6 Thinking  
**Purpose:** Explain the current failure precisely, distinguish OpenCode execution mistakes from specification mistakes, restore a truthful green baseline, and correct Selective scope before proceeding to migrations, evaluators, metrics, or Kaggle.

---

## 1. Executive verdict

Phase R2 is **not complete**.

The focused Selective tests pass, but the full suite fails:

```text
FAILED tests/integration/test_su0010a_regeneration.py::
TestFairTokenBudget::test_same_max_tokens_stops_iterative_before_call

Expected strategy backend calls: 1
Actual strategy backend calls: 8
```

The failure is not caused by the new Selective implementation. It exposes an uncorrected compatibility test left behind by Phase R1.

There is also a more important scientific defect: the current Selective result for `todo-smoke-002` is only:

```text
todo/models.py
```

That scope cannot implement the public requirement, because soft deletion also requires `TaskViewSet` behavior for DELETE, normal listing exclusion, the `deleted` action, the `restore` action, and detail retrieval behavior. Therefore the current R2 acceptance tests prove only that Selective chooses a subset; they do not prove that the subset can satisfy the public change request.

Do not commit R2, do not start R3, and do not claim Kaggle readiness until both defects are corrected and the full suite is green.

---

## 2. Exact cause of the failing full-suite test

The failing test backend in:

```text
tests/integration/test_su0010a_regeneration.py
```

still returns the obsolete strategy response:

```json
{
  "decisions": [
    {
      "path": "src/a.py",
      "action": "regenerate",
      "rationale": "only"
    }
  ]
}
```

The current production Agent parser intentionally accepts only JSON objects containing a top-level `action`, such as:

```json
{
  "action": "final",
  "selected_paths": ["src/a.py"],
  "rationale": "only"
}
```

This strict protocol is correct. Phase R1 explicitly removed production support for top-level `decisions`.

Because the test backend returns the obsolete format, `_parse_action_response()` rejects every response. Invalid responses consume calls by design. The backend returns the same invalid response repeatedly, so the Agent consumes all eight allowed calls. That is why:

```text
sb.call_count == 8
```

instead of:

```text
sb.call_count == 1
```

The correct repair is to update the test stub to the final-action protocol. Do **not** restore legacy parsing in production.

After the first valid final action, the backend reports 50 tokens. The existing legacy workflow budget in this test is also 50, so the Runner should stop before regeneration. The original assertions can remain:

```python
assert sb.call_count == 1
assert rb.call_count == 0
```

This test will later be rewritten in the dedicated token-semantics phase, but it must remain green now.

---

## 3. What OpenCode did wrong

### 3.1 It declared R2 complete without running the required full suite

The R2 contract required:

1. focused tests;
2. full suite;
3. Ruff;
4. mypy;
5. compileall;
6. diff check.

OpenCode reported only focused and quality gates, then said R2 was complete. The user’s manual full-suite run immediately found one failure.

From now on, a phase completion report must include the literal final line of `python -m pytest -q`. If that line is absent, the phase is not complete.

### 3.2 It failed to detect all legacy Agent response fixtures

OpenCode updated some old test backends to the new tool protocol, but missed the backend in `test_su0010a_regeneration.py`.

A repository-wide negative check should have been used:

```powershell
rg -n '"decisions"\s*:' tests
```

Every positive-path Agent fixture returned by a mock backend must use `action`. Only tests that explicitly verify legacy rejection may contain top-level `decisions`.

### 3.3 It previously reported behavior that the code does not implement

OpenCode previously claimed the Agent parser accepted both the new action protocol and the legacy decisions protocol. The actual parser returns a value only when `action` exists.

The code is correct relative to the current protocol; the report was false. Future reports must cite the actual function or test proving each compatibility claim.

### 3.4 It wrote a fake Ground Truth isolation test

The R2 test named like Ground Truth mutation calls `select_dependency_scope()` twice with the same `RequirementChange`. It does not mutate `Scenario.expected_affected_artifacts` at all.

That test proves deterministic repeatability, not Ground Truth isolation.

A real isolation test must execute the production strategy construction path with two scenarios that have identical public requirements but different Ground Truth fields and assert identical selections.

### 3.5 It optimized for “less than five” instead of requirement coverage

The tests require each scenario to select a non-empty subset smaller than five. That allowed scenario 002 to pass with only `models.py`.

A smaller scope is not automatically a better scope. A scope that cannot implement the requirement is scientifically invalid.

---

## 4. What was wrong in the instructions

The current failure is not solely an OpenCode mistake. Several instructions were incomplete or conceptually wrong.

### 4.1 Phase R1 did not require the full suite

The R1 gate listed only selected Agent tests. It omitted:

```text
tests/integration/test_su0010a_regeneration.py
```

and omitted the complete suite.

Therefore the legacy fixture survived R1 and was discovered only during R2.

**Future rule:** every phase runs focused tests first and always ends with `python -m pytest -q`. No exception.

### 4.2 The R1 authorized-file list omitted a test that had to change

R1 required removal of legacy decisions parsing but did not authorize editing every existing positive-path fixture that returned decisions. This created a hidden contradiction: production behavior had to change while one old test was expected to stay untouched.

**Future rule:** when a protocol changes, first run repository-wide search and list every affected test file in the authorized scope.

### 4.3 The R2 “repository-independent” low-information set contains `todo`

The contract called the set generic and repository-independent, but included:

```text
todo
```

`todo` is the current repository/domain name. That is contradictory.

The corrected generic set must remove `todo`. Repository-specific words belong in profile metadata, not a global generic stop list.

### 4.4 The R2 graph traversal direction is wrong for impact propagation

The graph defines:

```text
A -> B means A depends on B
```

For example:

```text
todo/views.py -> todo/models.py
```

If `models.py` changes, the potentially impacted consumer is `views.py`, which is reached by reverse traversal. The contract instead required only outgoing traversal from a seed.

That outgoing traversal adds dependencies of an already selected file. It does not identify consumers affected by a changed provider.

This is why a model-only seed for soft deletion remains model-only.

### 4.5 The contract conflated edit targets with context dependencies

Current decisions marked every graph-expanded path as `regenerate`.

For priority, `views.py` is a seed and its outgoing dependency includes `permissions.py`. That makes `permissions.py` a regeneration target even though the public priority requirement does not change permissions.

Dependency files may be useful as read-only context, but that does not mean they should be rewritten. The current SharedRegenerationExecutor regenerates every selected path, so unconditional forward expansion creates unnecessary modifications.

The correct V2 design must distinguish:

```text
edit targets
```

from:

```text
read-only context dependencies
```

If the existing executor cannot carry separate context paths yet, R2 must conservatively select only justified edit targets. It must not label dependencies as regenerated merely to claim dependency awareness.

### 4.6 R2 acceptance criteria were too weak

The contract required:

- deterministic;
- non-empty;
- smaller than all five;
- URLs excluded;
- serializers excluded for scenario 002.

It did not require the selected scope to cover every explicitly public layer.

This allowed a scientifically unusable result.

### 4.7 The profile cleanup was incomplete

The URL trigger was corrected, but no equivalent truthful triggers were required for `views.py`, such as:

- queryset filtering;
- soft-deletion behavior;
- DELETE behavior;
- DRF custom actions;
- list/detail endpoint behavior.

Without those profile terms, the public soft-deletion request cannot seed `views.py`.

---

## 5. Correct scientific meaning of the three R2 scopes

These obligations come from public requirement text and repository architecture, not from `expected_affected_artifacts`.

### 5.1 Priority change

The public requirement explicitly changes:

- the Task model;
- TaskSerializer;
- TaskViewSet list filtering.

Therefore the scope must include categories:

```text
model
serializer
view
```

There is no public authorization change and no router registration change.

Permissions and URLs should not become edit targets merely because views import them or URLs import views.

### 5.2 Soft deletion

The public requirement explicitly changes:

- Task schema/query behavior;
- DELETE behavior;
- normal list behavior;
- detail retrieval behavior;
- two DRF actions.

Therefore the scope must include:

```text
model
view
```

The public requirement explicitly states serializers and URLs do not require modification, so those paths must remain excluded.

A one-file model-only selection is invalid.

### 5.3 Project ownership authorization

The public requirement explicitly changes:

- Project model ownership;
- ProjectSerializer owner representation;
- permission policy;
- view wiring and owner assignment.

Therefore the selected categories must include:

```text
model
serializer
permission
view
```

No URL modification is required.

---

## 6. Corrected deterministic selection design

Do not use Ground Truth, scenario IDs, embeddings, LLM selection, or per-scenario branches.

### 6.1 Public requirement signals

Use only:

- `before`;
- `after`;
- public acceptance criteria.

Separate positive and explicit negative statements. Negative statements must not contribute positive terms.

Remove `todo` from `LOW_INFORMATION_SOFTWARE_TERMS`.

### 6.2 Direct edit seeds

A descriptor becomes a direct edit seed when:

1. a complete provided symbol appears in positive text;
2. its path stem/category appears with another meaningful descriptor term;
3. one truthful trigger phrase satisfies the existing strict ratio rule.

Add truthful repository-level triggers to `todo/views.py`:

```yaml
- queryset filtering changes
- soft deletion behavior
- delete request behavior
- DRF custom actions
- list and detail endpoint behavior
- permissions and authorization changes
- workflow changes
```

These are reusable repository facts, not scenario answers.

### 6.3 Dependency-aware expansion

Do not add all outgoing dependencies as regeneration targets.

Use the graph only to consider reverse dependents of direct seeds:

- if `A -> B`, then A is a consumer of B;
- when B is a direct seed, A may be impacted;
- add A only when A’s descriptor has at least one meaningful overlap with the public requirement;
- explicit negative paths always win;
- continue only one hop for Smoke V2;
- do not add unrelated consumers.

This allows the graph to influence impact without forcing every dependency to be rewritten.

### 6.4 Final edit targets

The result returned to `HybridSelectiveStrategy` is the edit-target set only.

Every selected path is `regenerate`.
Every other editable-universe path is `preserve`.

Do not claim that graph dependencies are supplied as context unless the executor actually receives them as read-only context.

---

## 7. Required corrected tests

### 7.1 Restore the full suite compatibility test

Update only the strategy backend response in:

```text
tests/integration/test_su0010a_regeneration.py
```

to:

```json
{
  "action": "final",
  "selected_paths": ["src/a.py"],
  "rationale": "only",
  "requires_iteration": false
}
```

Do not change production parsing and do not change the two assertions.

### 7.2 Public-layer coverage tests

Use real public scenario text and the real repository profile.

Assert by descriptor category, not by reading Ground Truth:

- priority selects model, serializer, and view categories;
- soft deletion selects model and view categories;
- project ownership selects model, serializer, permission, and view categories;
- none selects URL configuration;
- soft deletion excludes serializer because the public requirement explicitly says it is not required;
- every result remains a strict subset of the five-file editable universe.

### 7.3 Real Ground Truth mutation test

Load or construct two full Scenario objects with:

- identical requirement fields;
- identical repository and public acceptance fields;
- different `expected_affected_artifacts` and expected actions.

Construct the strategy through the same production factory/profile path and assert identical predictions.

Also run:

```powershell
rg -n "expected_affected_artifacts|expected_actions" `
  src/benchmark/selection `
  src/benchmark/strategies/selective.py
```

Expected: zero matches.

### 7.4 Protocol negative search

Run:

```powershell
rg -n '"decisions"\s*:' tests
```

Review every result. Legacy decisions may remain only in tests whose name and assertions explicitly verify rejection. Positive-path mock Agent responses must use `action`.

### 7.5 Full phase gate

The phase is not complete until all of these pass:

```powershell
python -m pytest `
  tests/integration/test_su0010a_regeneration.py::TestFairTokenBudget::test_same_max_tokens_stops_iterative_before_call `
  tests/unit/selection/test_dependency_scope.py `
  tests/contract/test_three_arm_core.py `
  -q

python -m pytest -q

ruff check `
  src/benchmark/selection/dependency_scope.py `
  src/benchmark/strategies/selective.py `
  benchmark_data/repository_profiles/todo.yaml `
  tests/unit/selection/test_dependency_scope.py `
  tests/integration/test_su0010a_regeneration.py

mypy --strict `
  src/benchmark/selection/dependency_scope.py `
  src/benchmark/strategies/selective.py

python -m compileall `
  src/benchmark/selection/dependency_scope.py `
  src/benchmark/strategies/selective.py

git diff --check
```

The final report must quote the literal full-suite summary.

---

## 8. Process changes that prevent future misunderstandings

### 8.1 One phase means one behavior boundary

A phase should change one production contract and all directly affected tests. It must not leave known compatibility updates for a later phase.

### 8.2 Search before editing

Every interface/protocol change begins with repository-wide searches for:

- old method names;
- old JSON keys;
- old config fields;
- old response fixtures;
- old assertions.

The search results define the authorized test files.

### 8.3 Full suite after every checkpoint

Focused tests diagnose quickly. They never authorize completion alone.

The mandatory order is:

```text
focused tests
static checks
full suite
diff scope
checkpoint commit
```

### 8.4 Fail closed on missing evidence

OpenCode must not say “complete” without showing:

- focused result;
- full-suite result;
- changed files;
- exact behavior evidence;
- commit hash when required.

### 8.5 Separate implementation evidence from research evidence

A smaller selected set is engineering evidence only.

Research readiness requires:

- scope can implement public requirements;
- real generation succeeds;
- scenario evaluator passes;
- baseline regression passes;
- metrics are truthful.

### 8.6 Never fix a failing old test by weakening production policy

When strict production protocol rejects a legacy fixture, update the fixture. Do not restore obsolete compatibility unless the scientific protocol requires it.

### 8.7 Tests must match their names

A test called Ground Truth mutation must actually mutate Ground Truth.
A test called production path must execute production classes.
A test called budget must assert which budget semantics it covers.

---

## 9. Immediate execution order

1. Update the one obsolete Agent response fixture.
2. Run the single failing test.
3. Run the full suite and confirm green before touching R2.
4. Correct the R2 algorithm and view triggers.
5. Replace weak/fake R2 tests with public-layer and real Ground Truth isolation tests.
6. Run all gates.
7. Inspect actual selections.
8. Commit the corrected R2 phase.
9. Stop for independent audit.
10. Do not start migrations/evaluators until approval.

---

## 10. Current project status

```text
Data truth                              complete
Safe editable ArtifactUniverse          complete
Monolithic reference                    complete
Bounded Repository Agent                implemented, full-suite fixture correction required
Selective R2                            not accepted
Migration generation                    not started
Scenario evaluators                     not started
Per-call token semantics                not started
Nine non-dry scripted records           not started
Kaggle authorization                    blocked
Stable tag                              blocked
Pilot                                   blocked
```

The project is progressing, but the correct response is not “Smoke ready.” The next milestone is a green full suite plus a Selective scope that covers the public behavior of all three changes without using Ground Truth.
