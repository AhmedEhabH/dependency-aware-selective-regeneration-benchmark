# OpenCode Execution Guide
## Dependency-Aware Selective Regeneration Benchmark

> **Purpose:** This file is the single source of operational instructions for OpenCode agents working on this repository.
>
> **Current repository state:** The working folder may initially be empty.
>
> **Primary implementation model:** DeepSeek V4 Flash Free through OpenCode.
>
> **Fallback implementation model:** BigPickle after the DeepSeek free quota is exhausted.

---

# 1. Project Objective

Prepare a research-grade benchmark for:

**Dependency-Aware Selective Regeneration for LLM-Assisted Software Evolution**

The benchmark will evaluate whether a dependency-aware strategy can:

1. Correctly identify affected software artifacts.
2. Modify only artifacts that genuinely require modification.
3. Preserve unchanged behavior.
4. Preserve architectural constraints.
5. Reduce unnecessary regeneration work.
6. Reduce token use, model calls, and latency only under equivalent correctness.

Correctness is more important than efficiency.

The core study will use Python, preferably Django-based repositories, to reduce language and framework confounding.

Preapproved repository plan:

- Small: Controlled Django Todo application.
- Medium: django CMS.
- Large/complex: Saleor Core.
- Optional future stress case: ERPNext.

These repositories represent increasing scale and architectural complexity within the Python ecosystem. Do not claim that source-code size is the only changing variable.

---

# 2. Binding Research Decisions

The following decisions are preapproved and do not require the agent to ask again:

```yaml
decision_status: PREAPPROVED_BY_RESEARCHER
language: Python
primary_framework_ecosystem: Django
local_environment: Conda
local_model_download: forbidden
local_llm_inference: forbidden
remote_benchmark_platform: Kaggle
kaggle_model: qwen-lm/qwen2.5-coder
small_repository: Controlled Django Todo
medium_repository: django CMS
large_repository: Saleor Core
optional_stress_repository: ERPNext
primary_scenario_count_per_repository: 8
scenario_distribution:
  localized: 3
  moderate: 3
  cross_cutting: 2
core_strategies:
  - repository_agent
  - static_only
  - semantic_only
  - hybrid_selective
additional_impact_strategy:
  - traceability_only
full_context_reference: only_when_feasible
legacy_results_classification: legacy_pilot
```

Do not redesign these decisions unless a genuine blocking technical, legal, or methodological problem is found.

If a change is necessary, document:

- the problem
- evidence
- available alternatives
- expected impact
- recommended decision

Then stop only if the change materially affects research validity.

---

# 3. Local Execution Policy

The local computer may be used for engineering validation, but must never download or run Qwen2.5-Coder.

## 3.1 Allowed locally

The agent is allowed to:

- Create the repository structure.
- Create a dedicated Conda environment.
- Install Python development and benchmark-harness dependencies inside that environment.
- Resolve dependency conflicts inside the isolated environment.
- Run unit tests for the benchmark framework.
- Run contract tests.
- Run static type checks.
- Run linting and formatting checks.
- Run schema validation.
- Run CLI smoke tests that use mocks or deterministic fake model backends.
- Execute scripts that prepare manifests, schemas, fixtures, and upload bundles.
- Validate notebook JSON structure.
- Execute notebook-independent Python modules.
- Run notebook cells only when they do not load or invoke an LLM and do not require Kaggle-only assets.
- Run a local smoke profile using a mock model backend.
- Inspect package versions and dependency conflicts.
- Generate documentation.
- Use safe Git commands.

## 3.2 Forbidden locally

The agent must not:

- Download Qwen model weights.
- Download any replacement large language model.
- Load Qwen or another LLM.
- Run local LLM inference.
- use Ollama, vLLM, llama.cpp, Transformers generation, or any model server locally.
- Attempt GPU inference.
- install CUDA specifically for model inference.
- run the real generative benchmark locally.
- claim that Kaggle execution passed.
- expose secrets or personal files.
- install packages into the base Conda environment.
- install packages globally.
- use `pip install --user`.
- modify unrelated Conda environments.
- silently upgrade system Python.
- silently replace major scientific packages outside the project environment.

## 3.3 Local validation boundary

The local environment validates:

- project structure
- Python imports
- schemas
- configuration
- tests for benchmark logic
- mock-model orchestration
- metrics
- manifests
- notebook structure
- documentation
- packaging

Kaggle validates:

- Qwen model discovery
- Qwen loading
- tokenizer compatibility
- dtype and quantization
- GPU memory
- real LLM inference
- real benchmark runs
- runtime token counts
- model latency
- publication results

The agent must clearly distinguish:

```text
LOCAL_ENGINEERING_VALIDATED
```

from:

```text
VALIDATED_ON_KAGGLE
```

---

# 4. Conda Environment Requirements

Create a dedicated Conda environment named:

```text
selective-regen-benchmark
```

Preferred Python version:

```text
Python 3.11
```

Use Python 3.12 only if all selected dependencies are compatible and the reason is documented.

## 4.1 Required environment files

Create:

```text
environment.yml
requirements-dev.txt
requirements-kaggle.txt
requirements-lock.txt
```

Responsibilities:

- `environment.yml`: reproducible local engineering environment.
- `requirements-dev.txt`: development, tests, linting, typing, notebook validation.
- `requirements-kaggle.txt`: minimal Kaggle runtime additions only.
- `requirements-lock.txt`: exact resolved local package versions after successful installation.

Do not put Qwen, model weights, or model-cache paths in any environment file.

## 4.2 Installation strategy

Use this order:

1. Detect whether `conda`, `mamba`, or `micromamba` is available.
2. Prefer `mamba` or `micromamba` for resolution if already available.
3. Otherwise use `conda`.
4. Create an isolated environment.
5. Install only inside that environment.
6. Use Conda packages for core compiled dependencies where practical.
7. Use pip only after activating the project environment.
8. Run `python -m pip check`.
9. Export the exact package list.
10. Record conflicts, warnings, and resolutions.

Never install into `base`.

## 4.3 Dependency conflict checks

After installation, run inside the project environment:

```bash
python -m pip check
python -m pip list
conda list
```

Also perform:

- import smoke tests
- version compatibility checks
- duplicate package inspection
- notebook kernel verification
- optional dependency checks
- environment reproducibility review

Create:

```text
reports/LOCAL_ENVIRONMENT_REPORT.md
```

It must include:

- environment name
- Python version
- Conda implementation
- package resolver used
- installation commands
- installed package versions
- dependency conflicts found
- how conflicts were resolved
- remaining warnings
- activation command
- deactivation command
- environment removal command
- local tests executed
- Kaggle-only checks not executed

## 4.4 Commands to report to the user

At the end, explicitly report:

```bash
conda activate selective-regen-benchmark
```

or the correct equivalent if `mamba` or `micromamba` is used.

Also report:

```bash
conda deactivate
```

and:

```bash
conda env remove -n selective-regen-benchmark
```

Do not assume the shell was automatically configured. If `conda activate` requires initialization, explain the exact command.

---

# 5. Model Abstraction Requirement

The benchmark must not require a real model for local tests.

Implement a model backend interface with at least:

- `MockModelBackend`
- `KaggleQwenBackend`

## 5.1 MockModelBackend

The mock backend must:

- be deterministic
- require no network
- require no model download
- produce fixture-based responses
- support success cases
- support malformed responses
- support timeout/failure simulations
- support token and call accounting with clearly synthetic values
- mark all resulting records as non-publication evidence

Every mock result must contain:

```yaml
execution_mode: local_mock
evidence_tier: engineering_validation
publication_eligible: false
```

## 5.2 KaggleQwenBackend

The Kaggle backend must:

- discover the Kaggle-mounted Qwen2.5-Coder path at runtime
- use local Kaggle assets only
- avoid network model downloads
- use `local_files_only=True` where supported
- record exact model path
- record model configuration
- record dtype
- record quantization
- record tokenizer
- record GPU information
- fail clearly if the model is unavailable or incompatible

The Kaggle backend must never be instantiated during ordinary local tests.

---

# 6. Required Persistent Files

Create and maintain:

```text
SYSTEM_STATE.md
TODO.md
DECISION_LOG.md
PROTOCOL_VERSION.md
docs/MASTER_IMPLEMENTATION_PLAN.md
docs/HUMAN_DECISIONS_REQUIRED.md
reports/latest_phase_report.md
```

## 6.1 SYSTEM_STATE.md

Must include:

- current phase
- current task
- completed work
- files created
- files modified
- environment status
- local checks passed
- local checks failed
- Kaggle checks pending
- current branch
- latest commit if available
- known risks
- exact next task
- handoff notes

## 6.2 TODO.md

Each item must include:

- ID
- priority
- category
- description
- acceptance criteria
- dependencies
- status
- owner
- evidence

## 6.3 Status vocabulary

Use only:

- `COMPLETE_STATICALLY`
- `LOCAL_ENGINEERING_VALIDATED`
- `PREPARED_NOT_RUN`
- `REQUIRES_KAGGLE`
- `REQUIRES_RESEARCHER_APPROVAL`
- `REQUIRES_HUMAN_REVIEW`
- `BLOCKED`
- `VALIDATED_ON_KAGGLE`

Never use `VALIDATED_ON_KAGGLE` without genuine Kaggle output.

---

# 7. Implementation Phases

Execute one phase at a time.

## Phase 0 — Bootstrap and Environment

Tasks:

- inspect the empty or existing folder
- create initial repository structure
- initialize Git if appropriate
- create `docs/`
- preserve this guide
- create Conda environment
- install local engineering dependencies
- resolve conflicts
- create environment reports
- create initial state files
- do not download or run a model

## Phase 1 — Input Audit

Tasks:

- inspect supplied paper, notebooks, result archives, and examples
- preserve originals
- classify current results as legacy pilot
- identify reusable components
- identify errors, leakage risks, and metric problems
- create migration documentation

## Phase 2 — Research Protocol

Tasks:

- create RQ/hypothesis/metric traceability
- define ground-truth protocol
- define candidate artifact universe
- define scenario schema
- define primary and secondary outcomes
- define statistical plan
- record any remaining human decisions

## Phase 3 — Repository and Scenario Preparation

Tasks:

- prepare Controlled Django Todo
- assess django CMS
- assess Saleor Core
- prepare manifests
- prepare scenario definitions
- prepare acquisition or snapshot strategy
- document licenses
- do not run real repository evolution using an LLM

## Phase 4 — Benchmark Core

Tasks:

- implement package structure
- implement configuration
- implement schemas
- implement provenance
- implement model backend abstraction
- implement mock backend
- implement run directories
- implement result schemas
- run local unit and contract tests

## Phase 5 — Strategies

Tasks:

- implement repository agent baseline
- implement static-only strategy
- implement semantic-only strategy
- implement traceability-only strategy
- implement hybrid selective strategy
- implement action classification
- implement impact-only ablations
- test using fixtures and mock backend

## Phase 6 — Validation and Leakage

Tasks:

- hidden/public test separation
- annotation isolation
- immutable repository snapshots
- file classification
- cache exclusions
- architecture checks
- regression checks
- leakage assertions
- local tests with fixtures only

## Phase 7 — Metrics and Statistics

Tasks:

- impact metrics
- functional correctness
- preservation metrics
- architecture metrics
- efficiency metrics
- software-quality deltas
- statistical-analysis implementation
- local deterministic metric tests

## Phase 8 — Kaggle Notebook

Tasks:

- create clean notebook
- import package logic
- add environment checks
- add Kaggle model discovery
- add Kaggle-only execution
- add smoke/pilot/research profiles
- clear outputs before Git commit
- do not execute Qwen locally

## Phase 9 — Packaging and Documentation

Tasks:

- README
- how-to-run
- Kaggle setup
- upload manifests
- code Dataset package
- benchmark Dataset package
- checksums
- release candidate documentation

## Phase 10 — Static and Local Engineering Audit

Tasks:

- run allowed local tests
- run type checks
- run linting
- run schema checks
- run mock-model smoke tests
- verify notebook structure
- verify no Qwen files were downloaded
- verify no secrets
- prepare final static report
- mark all real model checks as requiring Kaggle

---

# 8. Git Policy

If Git is available:

- initialize the repository if it is genuinely empty
- create atomic commits
- preserve user files
- review staged diffs
- use clear commit messages
- do not force-push
- do not push without explicit authorization
- do not create a stable release before Kaggle validation

Suggested initial branches:

```text
main
develop
feature/bootstrap-environment
feature/benchmark-core
feature/strategies
feature/kaggle-notebook
audit/local-validation
release/v0.1.0-rc.1
```

Do not create unnecessary branches merely to satisfy a list. Prefer a smaller clean history if that is more appropriate.

Suggested RC tag after local engineering validation:

```text
v0.1.0-rc.1
```

The tag must state:

```text
Research preview.
Local engineering validation completed.
Qwen execution and benchmark validation pending on Kaggle.
```

If Git operations are unavailable, create the exact command plan and do not claim execution.

---

# 9. Agent Handoff Protocol

Work may move from DeepSeek V4 Flash Free to BigPickle.

Every new session must first read:

1. `docs/MASTER_IMPLEMENTATION_PLAN.md`
2. this file
3. `SYSTEM_STATE.md`
4. `TODO.md`
5. `PROTOCOL_VERSION.md`
6. `DECISION_LOG.md`
7. `docs/HUMAN_DECISIONS_REQUIRED.md`
8. `reports/latest_phase_report.md`

The new model must:

- continue from the persisted state
- preserve completed work
- preserve approved decisions
- inspect Git status and diffs
- avoid restarting the project
- avoid replacing prior work for stylistic reasons
- complete the exact next task
- update state before stopping

Use this opening statement:

> Continuing from the persisted project state. Previously approved scientific and engineering decisions remain binding.

Use this closing statement:

> State persisted for safe continuation by the same or another OpenCode model.

---

# 10. Prompt 1 — First OpenCode Run

Copy and send this prompt to OpenCode:

```text
You are working inside a new or nearly empty project folder.

Read `docs/OPENCODE_EXECUTION_GUIDE.md` completely before doing anything.

Execute Phase 0 only: Bootstrap and Environment.

Important requirements:

1. Create the project structure and required state files.
2. Create an isolated Conda environment named `selective-regen-benchmark`.
3. Prefer Python 3.11.
4. Install only local engineering and testing dependencies.
5. Resolve dependency conflicts inside the isolated environment.
6. Run allowed local validation and import checks.
7. Do not download Qwen or any other language model.
8. Do not run LLM inference.
9. Do not execute the real benchmark.
10. Do not install into Conda base or globally.
11. Create `reports/LOCAL_ENVIRONMENT_REPORT.md`.
12. Tell me exactly how to activate and use the environment.
13. Update `SYSTEM_STATE.md`, `TODO.md`, and `reports/latest_phase_report.md`.
14. Do not start Phase 1.

If Git is available and the folder is appropriate for initialization, initialize it and create an atomic bootstrap commit. Do not push.

At the end, clearly report:
- environment name
- Python version
- installation commands used
- conflicts found and resolved
- tests/checks executed
- exact activation command
- files created
- exact next task

End with:

State persisted for safe continuation by the same or another OpenCode model.
```

---

# 11. Prompt 2 — Continue Current Phase

Use this prompt for later DeepSeek sessions:

```text
Continue the existing project from its persisted state.

Read:
- `docs/OPENCODE_EXECUTION_GUIDE.md`
- `docs/MASTER_IMPLEMENTATION_PLAN.md`
- `SYSTEM_STATE.md`
- `TODO.md`
- `PROTOCOL_VERSION.md`
- `DECISION_LOG.md`
- `docs/HUMAN_DECISIONS_REQUIRED.md`
- `reports/latest_phase_report.md`

Continue the current phase only.

All decisions marked `PREAPPROVED_BY_RESEARCHER` are binding.

Do not redesign the project.
Do not begin a later phase.
Do not download or run Qwen locally.
Do not run local LLM inference.
Use the Conda environment `selective-regen-benchmark`.
You may run engineering tests, type checks, linting, schema checks, and mock-backend smoke tests inside that environment.

Complete the highest-priority unblocked tasks for the current phase.

Before stopping:

1. Review every modified file.
2. Run all allowed checks relevant to your changes.
3. Update `SYSTEM_STATE.md`.
4. Update `TODO.md`.
5. Update `reports/latest_phase_report.md`.
6. Record failures and unresolved conflicts honestly.
7. Record the exact next task.
8. Preserve the environment activation instructions.

End with:

State persisted for safe continuation by the same or another OpenCode model.
```

---

# 12. Prompt 3 — Move to the Next Phase

Use only after reviewing the previous phase report:

```text
Read the complete persisted project state and the previous phase report.

The previous phase is approved to close.

Start the next phase listed in `SYSTEM_STATE.md`.

Follow `docs/OPENCODE_EXECUTION_GUIDE.md`.

Do not work on more than one phase.
Do not change preapproved scientific decisions.
Do not download or run any language model locally.
Use the existing Conda environment.
Run all permitted local engineering checks relevant to this phase.

At the end:

- update all state files
- produce the new phase report
- list files created and modified
- list local checks and results
- list Kaggle-only checks
- record the exact next task
- stop before starting another phase

End with:

State persisted for safe continuation by the same or another OpenCode model.
```

---

# 13. Prompt 4 — BigPickle Handoff

Use when the DeepSeek free quota ends:

```text
Continue the existing project from its persisted state.

DeepSeek V4 Flash Free stopped because its free quota ended. This is an interrupted implementation session, not permission to restart or redesign the project.

Before editing anything, read:

- `docs/OPENCODE_EXECUTION_GUIDE.md`
- `docs/MASTER_IMPLEMENTATION_PLAN.md`
- `SYSTEM_STATE.md`
- `TODO.md`
- `PROTOCOL_VERSION.md`
- `DECISION_LOG.md`
- `docs/HUMAN_DECISIONS_REQUIRED.md`
- `reports/latest_phase_report.md`

Inspect Git status and existing diffs.

Preserve all completed work and preapproved decisions.

Continue the exact next task recorded in `SYSTEM_STATE.md`.

Use the existing Conda environment `selective-regen-benchmark`.
Do not download or run Qwen locally.
Do not run any local LLM inference.
You may run engineering tests and mock-backend validation.

Do not start a later phase.

At the end, persist the updated state and record the next exact task.

End with:

State persisted for safe continuation by the same or another OpenCode model.
```

---

# 14. Prompt 5 — When OpenCode Asks a Question

If the agent asks a minor engineering question, it should choose the safest reasonable option and document it.

It must ask the user only when:

- the decision changes an RQ or hypothesis
- the decision changes the approved repository set
- the decision changes primary metrics
- the decision changes baseline fairness
- the decision changes scenario exclusion rules
- the decision changes the statistical protocol
- a license prevents the intended use
- local installation could damage or modify the user's system outside the isolated environment
- required source material is missing
- two approved requirements directly conflict

When asking, it must use:

```text
Decision ID:
Blocking reason:
Current phase:
Question:
Recommended answer:
Alternative:
Impact of each option:
Work that can continue without this answer:
```

The agent must not ask the user to choose:

- ordinary file names
- ordinary module structure
- formatting tools
- test folder names
- logging format
- harmless implementation details
- standard clean-code decisions

---

# 15. Required Final Local Report

Before Kaggle execution, produce:

```text
FINAL_LOCAL_PREPARATION_REPORT.md
```

It must include:

- repository structure
- Conda environment details
- package versions
- dependency-conflict status
- allowed tests executed
- mock-backend results
- notebook structural validation
- Git status
- files for GitHub
- files for Kaggle Notebook
- files for Kaggle Code Dataset
- files for Kaggle Benchmark Dataset
- unresolved decisions
- known risks
- Kaggle-only validation checklist
- exact environment activation command

The report must end with:

> Local engineering preparation and validation completed without downloading or running Qwen. Real model execution and benchmark validation require Kaggle.
