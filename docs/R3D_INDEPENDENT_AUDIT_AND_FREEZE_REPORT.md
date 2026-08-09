# R3D Independent Audit and Freeze Report

**Project:** Dependency-Aware Selective Regeneration Benchmark  
**Branch:** `experiment/three-arm-smoke-v2`  
**Audited HEAD:** `b8724cc`  
**R3D final code checkpoint:** `11f88f5`  
**R3D final documentation checkpoint:** `b8724cc`  
**Independent audit model:** GPT-5.6 Thinking  
**OpenCode execution model shown in the final run:** DeepSeek V4 Flash Free — OpenCode Zen — Build  
**Real experiment model later:** Qwen2.5-Coder-7B-Instruct on Kaggle  
**Audit decision:** **R3D accepted and frozen**  
**R4 permission:** planning may begin; implementation requires a complete single-pass phase specification first  
**Stable release tag:** not authorized  

---

# 1. Executive decision

R3D is accepted and frozen at `b8724cc`.

No more R3D code, test, evaluator, persistence, or documentation tasks should be sent to OpenCode unless a later R4/R5 production-path execution produces a reproducible failure that contradicts the frozen R3D contract.

The final R3D cycle was longer than acceptable. It included an initial implementation, root correction, RF-2 consolidation, evidence correction, and documentation correction. The final state is technically sound enough to freeze, but the process must not be repeated for R4 onward.

The project will therefore use a strict one-pass phase lifecycle:

```text
complete specification
→ implementation with tests and incremental compile
→ one internal correction window before commit
→ code commit
→ detailed report and documentation commit
→ independent audit
→ at most one root-correction pass if a blocker exists
→ re-audit
→ freeze
```

No series of small post-audit patches is allowed.

---

# 2. Repository identity and scope

The audited repository reports:

```text
Branch: experiment/three-arm-smoke-v2
HEAD: b8724cce0533e7af7b27df272d7317eff2b16ebe
Working tree: clean
```

Relevant history:

```text
b8724cc docs(audit): record R3D final freeze candidate
11f88f5 fix(validation): close final R3D evidence gaps
35506f0 docs(audit): record R3D correction pending audit
9e28790 fix(validation): complete R3D scientific wiring contract
e61eb9a docs(state): record R3D completion pending audit
e8d5eb4 feat(validation): wire migrations and evaluators into Runner
c8c8213 docs(state): synchronize R3C freeze handoff
```

The final R3D code closure changed exactly:

```text
src/benchmark/execution/runner.py
tests/unit/execution/test_r3d_wiring.py
```

The final documentation closure changed exactly:

```text
docs/PROJECT_HANDOFF.md
docs/R3D_FINAL_EVIDENCE_AND_REPORT_CLOSURE.md
reports/latest_phase_report.md
selective_updates/CHANGE_INDEX.md
selective_updates/records/R3D-PRODUCTION-WIRING.md
selective_updates/records/TECHNICAL-DEBT-AND-REFACTOR-SCHEDULE.md
```

The working tree is clean and code/documentation commit scopes are separated.

---

# 3. R3D production contract now implemented

R3D owns the production scientific-validation path between model generation and persisted experiment records.

The frozen sequence is:

```text
scientific configuration preflight
→ strategy selection or Repository Agent planning
→ model-backed regeneration
→ post-generation migration validation
→ baseline validation
→ isolated scenario evaluator
→ bounded repair or Agent revision when eligible
→ final RunRecord
→ RunRecordData
→ JSONL persistence
→ reporting serialization
```

## 3.1 Configuration preflight

The Runner validates scientific configuration before strategy analysis or model generation.

Configuration defects include:

```text
missing baseline command when regeneration is enabled;
missing required migration command;
missing evaluator metadata for a V2 scientific scenario;
missing canonical project root;
empty Python executable.
```

A configuration defect is recorded as:

```text
stage = configuration
failure_kind = harness_defect
```

It is not repairable through another model call.

## 3.2 Scientific validation result

The internal `_ScientificValidationResult` owns typed stage results:

```text
PostGenerationResult
FunctionalValidationResult
ScenarioEvaluatorResult
passed
failed_stage
failure_kind
feedback
duration_seconds
```

This removes the earlier baseline-only state and allows migration, baseline, and evaluator failures to be classified independently.

## 3.3 Exact stage ordering

The common scientific-validation method executes:

```text
generation_guard
→ migration_generation
→ baseline_validation
→ scenario_evaluator
```

Later stages do not execute after an untrusted earlier failure.

## 3.4 Record mapping

A single scientific-to-record mapper produces:

```text
migration_generation_passed
migration_duration_seconds
generated_migration_paths
baseline_validation_passed
baseline_validation_duration_seconds
scenario_evaluator_passed
scenario_evaluator_duration_seconds
scenario_evaluator_checks
functional_validation_passed
functional_validation_duration_seconds
```

The compatibility fields mirror baseline validation only:

```text
functional_validation_passed == baseline_validation_passed
functional_validation_duration_seconds == baseline_validation_duration_seconds
```

They no longer represent overall scientific success.

## 3.5 Public RunRecord preservation

The public `BenchmarkRunner.run()` wrapper uses `dataclasses.replace` rather than manually rebuilding a record. This preserves current and future stage, tool, transcript, and evidence fields.

## 3.6 Repair eligibility

Repair eligibility is based on exact failure stages and failure kinds, not the compatibility baseline mirror.

Repairable stages include:

```text
generation_guard
regeneration
migration_generation
baseline_validation
scenario_evaluator
```

Configuration, infrastructure, timeout, isolation, protocol, and budget failures remain non-repairable.

## 3.7 Repair and Repository Agent feedback

One feedback mapper produces bounded channels for the exact failed stage.

Evaluator feedback includes:

```text
evaluator stdout
evaluator stderr
semantic error
public check names
```

The channel is bounded and does not include evaluator source, Ground Truth, or hidden check descriptions.

Repository Agent revision uses this same failed-stage feedback. Executor failures are also preserved for the following revision.

## 3.8 Repository Agent evidence

The final record preserves:

```text
selection_tool_calls
selection_tool_duration_seconds
selection_inspected_file_count
selection_tool_transcript
```

The same fields are forwarded through entry conversion, persistence, and reporting.

---

# 4. Independent test evidence

## 4.1 Windows full suite supplied by the researcher

```text
1510 collected
1478 passed
32 skipped
0 failed
```

This is the broad project regression evidence.

## 4.2 Independent Linux R3D focused suite

Command:

```text
PYTHONPATH=src python -m pytest tests/unit/execution/test_r3d_wiring.py -q
```

Result:

```text
54 passed
0 failed
0 skipped
```

## 4.3 Independent Linux adjacent unit and contract suite

Command group:

```text
tests/unit/execution/test_runner.py
tests/unit/execution/test_pipeline.py
tests/unit/test_checkpoint.py
tests/unit/statistics/test_reporting.py
tests/contract/test_three_arm_core.py
```

Result:

```text
123 passed
0 failed
```

## 4.4 Independent Linux regeneration integration

```text
tests/integration/test_su0010a_regeneration.py
61 passed
0 failed
```

## 4.5 Independent Linux Repository Agent integration

```text
tests/integration/test_su0011_iterative_agent.py
25 passed
0 failed
```

## 4.6 Selected public-path closure tests

The seven final closure tests were executed together:

```text
real entry configuration
Monolithic migration fail-to-repair-to-success
Selective evaluator fail-to-repair-to-success
Repository Agent evaluator revision and transcript
evaluator feedback completeness
repair duration aggregation
record conversion/persistence/reporting evidence
```

Result:

```text
7 passed
0 failed
```

## 4.7 Static evidence

Independent environment:

```text
compileall: passed
git diff --check: clean
```

Ruff and mypy were not installed as executable Python modules in the independent audit environment. Their clean results are taken from the Windows/OpenCode gate evidence and supported by the successful full suite and compilation. This limitation is recorded rather than hidden.

---

# 5. Direct behavior conclusions

The audited code and tests support these conclusions.

## Configuration defects

```text
fail before strategy/model execution
```

## Migration failure

```text
first attempt fails
→ bounded repair context
→ second generation attempt
→ migration passes
→ final run succeeds
```

## Evaluator failure

```text
first attempt fails
→ feedback contains stdout, stderr, semantic error, and public checks
→ second generation attempt
→ evaluator passes
→ final run succeeds
```

## Repository Agent evaluator failure

```text
first evaluator fails
→ revise_plan receives failed evaluator evidence
→ evaluator source remains hidden
→ revised attempt succeeds
→ tool transcript remains present
```

## Persistence

```text
Runner evidence
→ entry record dictionary
→ RunRecordData
→ JSONL save/load
→ NotebookExporter
```

The fields survive this chain.

---

# 6. Report quality finding

OpenCode did not visibly print the required detailed report in the final response. It printed only the final marker and gate summary.

A 2,276-word report exists at:

```text
reports/latest_phase_report.md
```

It is much better than earlier reports and accurately separates public-path tests from private-helper tests. It still contains a self-reference limitation:

```text
the report was written before the documentation commit that contains it,
so its displayed Final HEAD is not the final repository HEAD.
```

The authoritative final identity is therefore this independent report:

```text
code checkpoint: 11f88f5
documentation checkpoint: b8724cc
frozen HEAD: b8724cc
```

No extra R3D documentation patch will be created solely to rewrite the commit hash. That would continue the patch cycle without improving production behavior.

---

# 7. Technical debt at freeze

## 7.1 Blocking debt

```text
Open TD-0 in R3D: 0
Open TD-1 in R3D: 0
```

No known scientific-correctness or production-path blocker remains in R3D.

## 7.2 Scheduled non-blocking debt

### TD-RUNTIME-001

```text
asyncio.get_event_loop() deprecation
```

Observed in regeneration and iterative-agent integration tests on Python 3.13.

Severity:

```text
TD-2
```

Checkpoint:

```text
RF-4 after R5, unless Python 3.14 compatibility becomes an earlier blocker
```

### TD-REPORT-001

```text
datetime.utcnow() deprecation
```

Observed in reporting tests.

Severity:

```text
TD-2
```

Checkpoint:

```text
RF-3 after R4 or RF-4 after R5
```

### TD-PROCESS-008

```text
report commit self-reference cannot contain its own final hash
```

Resolution:

```text
reports use “this documentation commit” internally;
visible OpenCode response prints the actual hash;
independent freeze report records final truth.
```

This is a process rule, not a reason to modify R3D again.

---

# 8. Over-engineering assessment

The final R3D closure did not introduce over-engineering.

Final production change:

```text
one bounded evaluator feedback branch
```

Final test work:

```text
replace nominal evidence with public-path evidence
```

No new public API, dependency, workflow engine, plugin system, or generic framework was introduced.

The previous R3D cycles were process-heavy, but the frozen implementation is cohesive:

```text
one preflight
one scientific orchestrator
one field mapper
one failure mapper
one feedback mapper
one replace-based wrapper
```

This is an appropriate internal architecture for the next phases.

---

# 9. Freeze decision

R3D is frozen at:

```text
b8724cc
```

Component checkpoints:

```text
R3D production correction: 9e28790
R3D final evidence correction: 11f88f5
R3D final documentation: b8724cc
```

No R3D tag is created.

The project-level stable scientific tag remains:

```text
v2.0.0-scientific-smoke
```

and is authorized only after nine real Qwen Kaggle records and independent result audit.

---

# 10. Official project state

```text
R1 Repository Agent                  accepted
R2 Dependency-aware Selective        accepted
R3A Scenario metadata               accepted
R3B Migration runner                accepted and frozen
R3C Isolated evaluator system       accepted and frozen
R3D Production scientific wiring    accepted and frozen
R4 Token and metric semantics       next
R5 Nine local non-dry records       pending
R6 Bundle, documentation, and push  pending
Real Qwen Kaggle Smoke              blocked
Stable scientific tag              blocked
Pilot                               blocked
```

---

# 11. Next-phase rule

Do not send OpenCode a short generic R4 prompt.

Before R4 starts, create one complete R4 single-pass specification containing:

```text
exact read order;
exact authorized artifacts;
dependency map;
frozen names;
metric identities;
token-budget semantics;
failure matrix;
property tests;
persistence and reporting round trip;
integration path;
incremental compile order;
bounded RF-3 refactor;
commit scopes;
detailed report template;
stop conditions.
```

R4 implementation must follow the One-Pass Phase Execution Protocol.

---

# R4 Completion Status (2026-07-31)

R4 (token limits and truthful workflow metrics) was implemented in a single pass on `experiment/three-arm-smoke-v2` and committed:

```text
code commit:  e87d4ad  fix(metrics): separate per-call limits and workflow totals
docs commit:  docs(state): record R4 completion pending audit
```

Evidence: R4 unit 66 passed; R4 integration 31 passed; R3D-adjacent regression 177 passed; evaluator integrity 50 passed, 1 pre-existing skip; full suite 1576 passed, 32 skipped, 0 failed; direct scripts A/B/C1/C2/D met §7 acceptance; Script D showed `2048 / 9000` at every metadata boundary; ruff 0 new; mypy --strict 0 new (baseline verified against HEAD worktree `b8724cc`); compileall 0; `git diff --check` clean; remaining R4 TD-0 = 0, TD-1 = 0.

Status: R4 **implemented — independent audit required**; not accepted, not frozen; R5 unauthorized until audit. Detailed report: `reports/latest_phase_report.md` (2299 words).

`R4_TOKEN_AND_METRIC_CONTRACT_AUDIT_REQUIRED`

---

**Final independent decision: R3D accepted and frozen.**
