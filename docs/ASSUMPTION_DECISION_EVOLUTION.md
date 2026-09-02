# Assumption, Decision, Obstacle, and Lesson Evolution

**Project:** Dependency-Aware Selective Regeneration Benchmark  
**Scientific version:** v0.9.22 (current)  
**Purpose:** Preserve the reasoning history behind the benchmark so a future maintainer or AI can understand not only *what* the project does, but *why* each major choice was made, what evidence invalidated earlier assumptions, and why the replacement decision is better.

> This file is an **assumption/decision learning ledger**, not a replacement for `DECISION_LOG.md`.
> `DECISION_LOG.md` records formal decisions. This file connects those decisions causally:
>
> `Assumption → Why it seemed reasonable → Obstacle/evidence → Revised decision → Lesson`.

---

## 1. Long-term and near-term goal

### Long-term scientific goal

Produce scientifically usable evidence comparing:

- a representative **iterative repository-agent workflow**, and
- the proposed **dependency-aware hybrid selective regeneration workflow**

under matched:

- repository state,
- requirement change,
- LLM,
- generation parameters,
- repair policy,
- validation policy,
- quality criteria,
- and end-to-end measurement boundary.

The intended result is not merely “fewer tokens”. Efficiency claims are valid only when correctness and quality are comparable.

### Current near-term goal

Before spending another full 48-cell Pilot:

1. prove the exact frozen artifact on the real Kaggle target;
2. run a small **real 6-cell Saleor-inclusive pilot-canary**;
3. reject deadline-censored or engineering-blocked canaries;
4. only after a real canary PASS make the candidate's stable-tag decision;
5. then run the full 48-cell Pilot.

---

# 2. Scientific invariants that must not drift silently

Current full Pilot:

```text
repositories = todo, djangocms, saleor
scenarios = 12
strategies = iterative_repository_agent, selective
repetitions = 2
cells = 48
model = Qwen2.5-Coder-14B-Instruct
quantization = BNB-NF4
attention = SDPA, no math/eager fallback
GQA compatibility = repeat_kv_sm75
max attempts = 3
max completion tokens/call = 4096
Pilot workflow timeout = 1200 s
```

The 6-cell canary is an **operational gate**, not a scientific-matrix change.

---

# 3. Material assumption and decision evolution

The entries below cover the material assumptions that changed architecture, experiment design, deployment, release policy, or interpretation. Trivial implementation assumptions are intentionally excluded.

---

## A001 — The paper and frozen protocol should be the source of truth

### Initial assumption
The project should not be implemented ad hoc from code ideas. The research paper/protocol must define the experiment first.

### Why it was reasonable
Without a pre-registered protocol, implementation outcomes could influence experimental design and create post-hoc tuning.

### Obstacle
The original protocol draft contained contradictions in formulas, repair budgets, failure handling, determinism claims, monetary-cost reporting, and timing/cutoff rules.

### Revised decision
Freeze Protocol v1.0 only after researcher-approved decisions and explicit corrections (D006-D007).

### Lesson
**Freeze the scientific question before optimizing the software that answers it.**

Status: **KEPT, with corrections before freeze.**

---

## A002 — Local development and Kaggle execution should be intentionally separated

### Initial assumption
The local machine should implement/test the benchmark without installing the heavy Kaggle model stack or running local LLM inference.

### Why it was reasonable
Local CUDA/model downloads were expensive and unnecessary; real target behavior belongs on Kaggle.

### Obstacle
Local tests cannot prove:
- Kaggle GPU behavior,
- model loading,
- long-context attention behavior,
- real repository environment behavior,
- or service provisioning.

### Revised decision
Keep the local/Kaggle separation, but require target-shaped Kaggle/CI gates before launch readiness (D004, D020, D027+).

### Lesson
**Environment isolation is good, but local green is never evidence for target-runtime behavior.**

Status: **KEPT, strengthened with target proof.**

---

## A003 — Three repositories give a useful spectrum of repository complexity

### Initial assumption
Use:
1. controlled Django Todo,
2. django CMS,
3. a larger production repository.

ERPNext was considered for the third repository.

### Why it was reasonable
The experiment needed controlled, medium, and larger real-world repositories.

### Obstacle
ERPNext did not fit the intended architectural-boundary design as well as alternatives.

### Revised decision
Replace ERPNext with **Saleor Core**, and freeze:
- Todo,
- django CMS 5.0.0,
- Saleor Core 3.23.0.

This became 24 prepared scenarios initially, with the confirmatory Pilot using a frozen 12-scenario subset.

### Lesson
**Repository selection must serve the research construct, not merely maximize repository size.**

Status: **CHANGED: ERPNext → Saleor.**

---

## A004 — A single canonical project root is necessary

### Initial assumption
Existing directory copies could coexist during development.

### Why it seemed harmless
Early work was documentation-heavy and duplicate directories did not immediately break code.

### Obstacle
Phase 3.5 found stale duplicate `docs/` and `benchmark_data/` trees outside the Git repository.

### Revised decision
`project/` became the canonical source of truth; stale outer copies were removed or migrated (D009-D010).

### Lesson
**Multiple writable sources of truth create silent experimental drift.**

Status: **CHANGED to single canonical root.**

---

## A005 — Layered implementation before execution is worth the upfront structure

### Initial assumption
Domain models, loaders, backends, execution, evaluation, and statistics should be built in dependency order.

### Why it was reasonable
The benchmark has scientific contracts that are easier to test when the architecture separates them.

### Obstacle
This added planning/documentation overhead.

### Revised decision
Keep the layered architecture, but later adopt bounded feature closures instead of repeatedly expanding architecture work.

### Lesson
**Architecture is useful when it protects scientific contracts; architecture work becomes over-engineering when it no longer removes a concrete blocker.**

Status: **KEPT with stricter scope control.**

---

## A006 — The original “agent” arm was an adequate repository-agent baseline

### Initial assumption
The existing LLM “agent” strategy could serve as the main baseline for token-efficiency comparison.

### Why it seemed reasonable
It used an LLM to choose impact scope and was labeled as an agent.

### Obstacle
The arm-to-protocol audit showed:
- it was effectively single-shot scope prediction,
- several arms had LLM-design/wiring mismatches,
- and the measurement boundary excluded regeneration/repair.

This made the original token-efficiency comparison scientifically invalid.

### Revised decision
Research Design V2 (D023):
- main baseline = **iterative repository agent**,
- treatment = **hybrid selective**,
- matched shared regeneration executor,
- end-to-end accounting includes selection + regeneration + repair + validation,
- efficiency claims require comparable correctness/quality.

### Lesson
**A name is not an experimental construct. Audit what the code actually does.**

Status: **CHANGED materially.**

---

## A007 — One dependency graph could represent a mixed-repository Pilot plan

### Initial assumption
A graph built for the plan could be reused while executing multiple repositories.

### Why it seemed reasonable
The execution plan was treated as one benchmark batch.

### Obstacle
Pilot readiness dry-runs proved that a graph from one repository could not represent another repository's editable universe correctly.

### Revised decision
Build and select **one dependency graph per repository**; fail closed on mixed-repository misuse (D024).

### Lesson
**Repository identity is part of the dependency universe. Never share repository-local graph state across repos.**

Status: **CHANGED.**

---

## A008 — Dry-run/mock success was sufficient evidence that the execution path was wired correctly

### Initial assumption
A deterministic dry-run proving planned cells, IDs, strategy counts, and zero model calls was a strong readiness signal.

### Why it was reasonable
Dry-run catches matrix, configuration, identity, serialization, and many path errors cheaply.

### Obstacle
Real Kaggle execution repeatedly exposed failures impossible for a mock to prove:
- real Qwen failure propagation,
- graph/backend wiring,
- repository environments,
- GPU memory,
- target subprocess argv,
- services,
- and notebook runtime state.

### Revised decision
Dry-run remains mandatory, but is only one gate among:
- Dataset Validation,
- Prompt Validation,
- Pipeline Smoke,
- Dry Run,
- Integration,
- Metric Verification,
- target preflight,
- real canary.

### Lesson
**Dry-run proves topology, not viability.**

Status: **KEPT but demoted from “readiness proof” to one gate.**

---

## A009 — Component-mocked local tests were enough for Saleor preflight command correctness

### Initial assumption
Mocks that recognized expected command fragments adequately tested the Saleor preflight command.

### Why it seemed reasonable
The component under test appeared to be argument construction, not pytest itself.

### Obstacle
Real Kaggle v0.9.19 failed with pytest exit 5 because a second `-m pytest` was appended.  
The local fake runner was **false-green** because it matched substrings rather than exact argv.

### Revised decision
D027:
- exact command-vector contracts,
- exact node IDs,
- fail-closed duplicated `-m` detection,
- target-shaped Linux preflight before an `exec-ready` tag.

### Lesson
**Mocks must validate semantics, not merely recognize substrings.**

Status: **CHANGED testing policy.**

---

## A010 — The benchmark/model Python interpreter could validate all generated repositories

### Initial assumption
Using `sys.executable` for per-cell validation was sufficient.

### Why it seemed reasonable
Todo validation worked and using one interpreter simplified execution.

### Obstacle
Saleor and django CMS dependencies were intentionally isolated in repository-specific environments. Saleor also required frozen environment variables and its real validation runtime was far longer than 180 seconds.

### Revised decision
D028:
- explicit `--validation-python repo=path`,
- per-repository validation environments,
- `--validation-timeout 1800`,
- parent environment remains unmodified.

### Lesson
**Execution-runtime parity must include interpreter, environment, services, and time budget.**

Status: **CHANGED.**

---

## A011 — Successful model load + short generation was enough GPU proof

### Initial assumption
If Qwen 14B BNB-NF4 loaded on 2x T4 and generated a short probe, the model runtime was viable.

### Why it seemed reasonable
Load and short inference are the usual first memory checks.

### Obstacle
v0.9.21 failed on the 12,044-token long-context probe with an allocation matching the full quadratic float32 attention matrix.

### Revised decision
D029-D030:
- explicit `attn_implementation="sdpa"`,
- no math/eager fallback,
- attention-policy evidence,
- GQA T4 microprobe,
- `repeat_kv_sm75`,
- keep the real long-context probe.

### Lesson
**Short-context viability does not imply long-context viability. Test the actual scientific context regime.**

Status: **CHANGED runtime policy.**

---

## A012 — Passing real target preflight plus a 48-cell dry-run implied the Pilot was viable

### Initial assumption
After:
- all repository preflights PASS,
- model preflight PASS,
- long-context PASS,
- exact artifact dry-run 48/48,
- stable tag creation,

the real Pilot should be safe to launch.

### Why it was reasonable
Every known static/environment/runtime gate had passed.

### Obstacle
The 2026-08-30 real Pilot (`exp-20260830-134232`) produced:

```text
48 terminal
0 succeeded
48 failed
33 scientific_budget_exhausted
8 model_output
7 build
```

33 runs hit the 600-second workflow deadline. Resume also had a standalone `NameError`.

### Revised decision
D034:
- reject the run as scientific evidence,
- preserve it verbatim,
- retire (do not move/delete) the old stable tag as a launch candidate,
- separate terminality from viability,
- increase Pilot workflow timeout 600 → 1200,
- require a small **real canary before another 48-cell spend**.

### Lesson
**Preflight proves environment readiness; it does not prove end-to-end workflow viability.**

Status: **CHANGED strongly.**

---

## A013 — The 600-second Pilot timeout was adequate because it was pre-registered

### Initial assumption
Uniform 600 s per run was a reasonable preregistered Pilot workflow timeout.

### Why it was reasonable
A bounded uniform timeout avoids performance-driven tuning.

### Obstacle
The real Pilot showed 33/48 deadline-censored runs. Saleor alone had 15/16 budget-censored cells.

### Revised decision
Use 1200 s for the internal Pilot runtime contract while preserving the scientific version at v0.9.22 and documenting why the old run is rejected.

### Why changing it is scientifically defensible
The previous timeout prevented observing the workflow outcome at all; it acted as an engineering censoring defect rather than a meaningful experimental condition.

### Lesson
**Pre-registration protects against outcome-driven tuning, but a demonstrably censoring infrastructure limit must be corrected transparently, not worshipped.**

Status: **CHANGED 600 → 1200 with explicit provenance.**

---

## A014 — A two-repository canary was sufficient

### Initial assumption
A small canary using Todo + django CMS could cheaply exercise both strategies.

### Why it seemed reasonable
The canary was intended as a reduced operational sub-matrix, not a mini benchmark.

### Obstacle
Historical real evidence showed Saleor was the most timeout-sensitive repository: **15/16 cells budget-censored**.

The first D10 canary also contained an internal contradiction:
- `blast_radii=["localized"]`,
- while `djangocms-cross-007` is `cross_cutting`,
so the scenario was filtered out before execution.

### Revised decision
D035:
- include **all three repos**,
- one canonical scenario per repo,
- both strategies,
- one repetition,
- total = **6 cells**,
- blast radii include localized + cross-cutting.

### Lesson
**A viability canary must represent the highest-risk production path, not only the cheapest paths.**

Status: **CHANGED 2 repos/4 cells → 3 repos/6 cells.**

---

## A015 — Setting CLI default protocol to 1.1 was a safe way to update the Pilot

### Initial assumption
Changing the global CLI protocol default to 1.1 would naturally move the Pilot to the corrected runtime contract.

### Why it seemed reasonable
Pilot and canary were the active execution targets.

### Obstacle
The default leaked into smoke/research profiles whose protocol remained 1.0.

### Revised decision
D035:
- protocol is profile-derived:
  - pilot / pilot-canary → 1.1,
  - smoke / research / scientific-smoke-v1/v2 → 1.0,
- explicit CLI override always wins.

### Lesson
**A local contract change must not silently become a global default.**

Status: **CHANGED.**

---

## A016 — A CLI-level executable canary integration test was enough to prove the Kaggle canary path

### Initial assumption
If an integration test invokes the real benchmark CLI with `--profile pilot-canary` and gets the correct 6-cell topology, then the canary is executable.

### Why it seemed reasonable
This fixed the D10 failure where profile configuration itself could not resolve the requested scenarios.

### Obstacle
The 2026-09-01 Kaggle run proved a different layer could still fail:

```text
NameError: name 'SCRIPT_PATH' is not defined
```

All of these had already passed:
- artifact verification,
- repository snapshots,
- Saleor PostgreSQL/Redis bootstrap,
- Todo/django CMS/Saleor repo preflight,
- T4 GQA microprobe,
- Qwen 14B BNB-NF4 load,
- long-context probe,
- generation-deadline probe,
- HF secret retrieval.

The failure occurred while *constructing* `canary_cmd`, before the canary subprocess or first canary model call.

### Root cause
D10 inserted `pilot-canary-cell` **before** the existing `dryrun-cell`.

The new cell used:

```python
str(SCRIPT_PATH)
```

but the definition remained downstream inside `dryrun-cell`:

```python
SCRIPT_PATH = CODE_DIR / "seven_arm_benchmark.py"
```

So the notebook had a hidden **execution-order dependency**.

### Why 2585 tests did not catch it
The test suite checked different layers separately:

1. notebook code cells compile with `ast.parse`;
2. expected notebook cell order exists;
3. canary cell contains the expected argv/validator markers;
4. the benchmark CLI itself can execute a dry-run canary.

None of those tests executed or modeled the **state produced by earlier notebook cells before entering `pilot-canary-cell`**.

Thus:
- CLI integration = green,
- notebook syntax = green,
- notebook structure = green,
- real notebook orchestration = broken.

### Revised decision (required D12)
Critical operational notebook cells must not depend on variables first defined in later cells.

For this bug, define/validate the benchmark script path **before the canary** (single canonical definition), and add a regression test proving the definition occurs before first canary use.

Do **not** redesign the notebook framework.

### Lesson
**Integration tests must cover the orchestration layer, not only the executable being orchestrated.**

Status: **INVALIDATED on 2026-09-01; D12 blocker.**

---

# 4. Latest real Kaggle attempt — 2026-09-01

## What passed

Real target evidence from the uploaded run:

```text
Repository preflight: PASS
  Todo: PASS
  django CMS: PASS
  Saleor: PASS

Saleor PostgreSQL: PASS
Saleor Redis-compatible service: PASS

T4 SDPA GQA microprobe: PASS on both GPUs

Qwen 14B BNB-NF4 model load: PASS
device_map GPU-only: PASS
short generation probe: PASS
generation-deadline probe: PASS
long-context probe:
  prompt_tokens=12044
  elapsed=29.182s
  PASS

HF_TOKEN retrieval: PASS
```

## What failed

The first real canary notebook cell:

```text
NameError: name 'SCRIPT_PATH' is not defined
```

## Scientific contamination

None.

The error occurred before `_run_live(canary_cmd, ...)`.

Therefore:

```text
real canary model calls = 0
real canary RunRecords = 0
real canary scientific result = NOT STARTED
```

This is an engineering orchestration failure, not a failed scientific canary.

---

# 5. Obstacle → correction summary

| Obstacle | Incorrect/insufficient assumption | Correction |
|---|---|---|
| Duplicate project trees | Multiple copies can coexist | Single canonical Git root |
| Original agent not true iterative baseline | Label implies construct | RD-V2 iterative repository-agent baseline |
| Measurement excluded regen/repair | Scope-selection tokens enough | End-to-end measurement boundary |
| One graph for mixed repos | Plan-level graph is reusable | Per-repository dependency graphs |
| Real Qwen wiring failures | Mock smoke enough | Real Kaggle smoke |
| Saleor pytest exit 5 | Substring mock validates argv | Exact argv + target-shaped gate |
| Wrong per-cell interpreter/env | `sys.executable` enough | Per-repo interpreters/env |
| Saleor >180s validation | Generic validation timeout enough | Explicit 1800s validation budget |
| 12k prompt CUDA OOM | Short generation implies memory viability | Explicit SDPA no-math + long-context gate |
| T4 GQA concerns | Generic SDPA proof enough | Real per-GPU GQA microprobe |
| 48/48 real Pilot failed | Preflight + dry-run imply viability | Real canary before full Pilot |
| 600s censored 33/48 | Pre-registered timeout must never change | Transparent 1200s internal correction |
| Canary omitted Saleor | Reduced matrix need not include all repos | 6-cell all-repo canary |
| Canary blast radius contradiction | Profile unit assertions enough | Executable CLI topology test |
| Protocol 1.1 leaked globally | Global default is harmless | Profile-derived protocol |
| `SCRIPT_PATH` NameError | CLI integration proves notebook path | Notebook execution-order regression test |

---

# 6. Testing doctrine learned from the project

A high test count is useful but not sufficient.

Every launch-critical feature should have four layers:

```text
1. Unit contract
2. Executable component integration
3. Orchestration/integration in the exact deployment surface
4. Real target canary when the target cannot be reproduced locally
```

For notebooks specifically:

```text
Syntax-valid cell
    !=
Correct notebook execution state
```

A new operational cell must either:
- be self-contained for critical paths, or
- have an explicit tested upstream-variable contract.

---

# 7. Anti-over-engineering rule

A new task is justified only if it does one of the following:

1. removes a demonstrated blocker;
2. protects scientific validity;
3. makes exact target execution reproducible;
4. fixes evidence/provenance integrity.

Do **not** open a new phase merely to:
- rename,
- refactor unrelated code,
- increase test count,
- rewrite historical documentation,
- generalize a one-line notebook dependency into a new framework.

For the current `SCRIPT_PATH` bug, the correct fix is a **small notebook orchestration correction + regression test + truth-only documentation update**.

---

# 8. Current Go/No-Go state

```text
D11 code/config scientific contract:     PASS
D11 exact artifact topology:             PASS
Real target repository/model preflight:  PASS
Real pilot-canary execution:             BLOCKED before start
Cause:                                    notebook SCRIPT_PATH ordering bug
Scientific canary evidence:              NONE
Full 48-cell Pilot authorization:        NO-GO
```

Required next action:

```text
D12 minimal notebook orchestration fix
→ targeted regression tests
→ Gates 1-6 (reuse unaffected gates only with explicit evidence; rerun affected integration)
→ full suite once
→ fresh exact artifact + provenance
→ Kaggle real preflight
→ real 6-cell canary
```

Do not launch the 48-cell Pilot until the real 6-cell canary passes and is independently audited.

---

# 9. Formal decision-log mapping

This learning ledger is grounded in the project's formal decisions:

- D001-D005: bootstrap/environment/input truth
- D006-D007: protocol draft/freeze
- D008: repository and scenario selection
- D009-D010: architecture and canonical structure
- D011-D019: benchmark core/evaluation implementation
- D020: real Kaggle smoke
- D021-D022: canonical bundle + early CLI NameError lesson
- D023: Research Design V2
- D024: multi-repository Pilot readiness
- D025: Pilot execution preregistration
- D027: Saleor exact-argv/target-preflight lesson
- D028: per-cell validation runtime parity
- D029-D030: long-context SDPA/GQA runtime closure
- D031-D033: Kaggle/GitHub boundary, notebook navigation, real T4 preflight and old stable tag
- D034: all-failed real Pilot rejection and viability correction
- D035: Saleor-inclusive 6-cell canary + protocol correction
- **Next formal entry should record the 2026-09-01 notebook execution-order failure and D12 correction.**

---

# 10. Maintenance rule for future AI/operators

Whenever an assumption is invalidated, do not only patch code.

Update this file with:

```text
Assumption:
Why it was reasonable:
Evidence that broke it:
Old decision:
New decision:
Why the new decision is better:
Scientific impact:
Regression test added:
Evidence required before closure:
```

That makes project history reusable knowledge instead of a sequence of unexplained patches.
