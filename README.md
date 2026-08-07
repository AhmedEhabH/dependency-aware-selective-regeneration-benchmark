# Dependency-Aware Selective Regeneration Benchmark

> Research infrastructure for the working paper  
> **“Don't Regenerate What Hasn't Changed: Selective Regeneration for Token-Efficient LLM-Driven Software Evolution.”**

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Protocol](https://img.shields.io/badge/Research%20Protocol-v1.0%20Frozen-success.svg)](PROTOCOL_VERSION.md)
[![Tests](https://img.shields.io/badge/tests-1%2C928%20passing-success.svg)](reports/PROJECT_HEALTH_REPORT.md)
[![Legacy](https://img.shields.io/badge/Legacy%20orchestration%20smoke-v0.7.0-blue.svg)](https://github.com/AhmedEhabH/dependency-aware-selective-regeneration-benchmark/releases)

## Overview

This repository provides a research-grade benchmark for studying **selective regeneration in LLM-driven software evolution**.

The central idea is simple:

> When a requirement changes, regenerate only the software artifacts that are truly affected—while preserving unchanged behavior and architecture.

The benchmark prioritizes **impact correctness** before efficiency. Token savings are not considered successful if the approach misses affected artifacts, breaks regression behavior, or violates architectural constraints.

The project is designed for:

- repository-level software evolution;
- natural-language requirement changes;
- dependency-aware impact analysis;
- selective artifact regeneration;
- controlled comparison with baseline strategies;
- reproducible execution using open-weight code LLMs;
- Kaggle-based real-model experiments.

## Working Paper

**Title:**  
*Don't Regenerate What Hasn't Changed: Selective Regeneration for Token-Efficient LLM-Driven Software Evolution*

**Status:** Research in progress. The title is frozen as the working title for the current research cycle.

## Research Questions

The frozen protocol studies five dimensions:

1. **Impact identification:** How accurately are affected artifacts identified?
2. **Evolution correctness:** Can changed requirements be implemented while preserving unchanged behavior?
3. **Architecture consistency:** Can architectural constraints be preserved?
4. **Efficiency:** Can regeneration reduce artifacts, tokens, calls, and time under equivalent correctness?
5. **Sensitivity:** How do results vary by repository, change type, and blast radius?

The authoritative protocol is available in [`docs/FINAL_RESEARCH_PROTOCOL.md`](docs/FINAL_RESEARCH_PROTOCOL.md).

## Three-Arm Core Experiment

The confirmatory benchmark compares three strategies:

| Strategy | How Scope Is Determined | Model Calls |
|----------|------------------------|-------------|
| `full_scope_reference` (monolithic) | All eligible source artifacts | 1 per artifact |
| `dependency_aware_selective` (selective) | Repository graph + anchors + BFS | 1 per selected artifact |
| `repository_agent` (iterative) | Bounded LLM loop (list/read/search) | ≤8 total iterations |

All arms share the same LLM, temperature (0.0), per-call max_tokens (4096), code-writing executor, validation pipeline, and isolated workspace.

See [`selective_updates/records/THREE-ARM-CORE-EXPERIMENT.md`](selective_updates/records/THREE-ARM-CORE-EXPERIMENT.md) for the full amendment.

## Core Principles

- **Correctness before efficiency**
- **Frozen experimental protocol**
- **No post-hoc scenario or metric changes**
- **Ground-truth is evaluator-only and post-hoc**
- **Failed runs remain visible**
- **Equivalent-model and equivalent-budget comparisons**
- **Local engineering validation without local LLM inference**
- **Real Qwen execution only on Kaggle**
- **Complete provenance for publication results**

## Benchmark Scope

### Language and ecosystem

The confirmatory benchmark focuses on **Python**, primarily the **Django ecosystem**, to reduce language and framework confounding.

### Repositories

| Scale | Repository | Role |
|---|---|---|
| Small | Controlled Django Todo | Fully controlled reference repository |
| Medium | django CMS 5.0.0 | Modular CMS with plugin architecture |
| Large | Saleor Core 3.23.0 | Django/GraphQL modular monolith |

The study treats these repositories as examples of increasing scale and architectural complexity. It does not claim that source-code size is the only changing variable.

### Scenarios

The frozen design contains **24 scenarios**:

| Repository | Localized | Moderate | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Controlled Django Todo | 3 | 3 | 2 | 8 |
| django CMS | 3 | 3 | 2 | 8 |
| Saleor Core | 3 | 3 | 2 | 8 |
| **Total** | **9** | **9** | **6** | **24** |

The scenario taxonomy covers:

- schema and field changes;
- API changes;
- validation and business rules;
- permissions and authorization;
- cross-entity relationships;
- workflow changes;
- architecture-sensitive changes;
- broad cross-cutting changes.

## Architecture

```mermaid
flowchart TD
    C[Domain Models and Contracts]
    CFG[Configuration]
    R[Repository and Scenario Loaders]
    LLM[LLM Backends]
    EX[Execution Core]
    G[Dependency Graph and Impact Strategies]
    EV[Evaluation and Metrics]
    ST[Statistics]
    NB[Kaggle Notebook]

    C --> CFG
    C --> R
    C --> LLM
    CFG --> EX
    R --> EX
    LLM --> EX
    EX --> G
    G --> EV
    EV --> ST
    ST --> NB
```

The architecture uses:

- immutable typed domain models;
- `typing.Protocol` interfaces;
- explicit dependency injection;
- instantiated registries rather than global singletons;
- lazy Kaggle-only model imports;
- isolated run workspaces;
- typed failure classification;
- deterministic local mock and dry-run backends.

See [`docs/SOFTWARE_ARCHITECTURE.md`](docs/SOFTWARE_ARCHITECTURE.md) and [`docs/DEPENDENCY_RULES.md`](docs/DEPENDENCY_RULES.md).

## Comparison Arms

### Monolithic / Full-Scope Regeneration
Condition identifier: `monolithic`, `full_scope_reference`
Purpose: Baseline full-scope regeneration — every artifact is regenerated.
Budget semantics: Selection + regeneration tokens count toward `max_tokens`.

### Agent (Single-Shot LLM)
Condition identifier: `agent`
Purpose: Single LLM call for impact analysis; no regeneration.
Budget semantics: Not budget-constrained (no regeneration enabled).

### Selective / Hybrid Selective Regeneration
Condition identifier: `selective`, `hybrid_selective`
Purpose: Selective regeneration using dependency graph and semantic analysis.
Budget semantics: Selection + regeneration tokens count toward `max_tokens`.

### Compiled AI (Static Analysis)
Condition identifier: `compiled_ai`
Purpose: Dependency graph only — no LLM calls.
Budget semantics: Not budget-constrained (no LLM calls).

### Delta MCP (Semantic Analysis)
Condition identifier: `delta_mcp`
Purpose: Repository diff and semantic trace analysis.
Budget semantics: Not budget-constrained (no LLM calls).

### Incremental RTL (Traceability)
Condition identifier: `incr_rtl`
Purpose: Lightweight traceability analysis.
Budget semantics: Not budget-constrained (no LLM calls).

### Code Plan (Full Context)
Condition identifier: `code_plan`
Purpose: Full-repository-context LLM analysis.
Budget semantics: Not budget-constrained (no regeneration enabled).

### Iterative Repository Agent
Condition identifier: `iterative_repository_agent`
Purpose: Plan → regenerate → validate → revise. The agent iteratively analyzes
the repository, selects artifacts for regeneration, regenerates them, validates
the result, and revises its plan based on validation feedback.
Stop conditions: Validation passes, token budget exhausted (`max_tokens`),
attempt budget exhausted (`max_attempts`), timeout, `requires_iteration=false`,
backend error.
Budget semantics: Agent reasoning tokens + regeneration tokens count toward
`max_tokens`. Shared meaning across all regeneration-enabled arms.
Scientific Smoke and Pilot: Not yet authorized for this arm.

## Current Status

> **Legacy Seven-Arm V1 vs current Three-Arm V2:** The legacy Seven-Arm V1
> benchmark (`seven_arm_benchmark.py`, arms `monolithic`, `agent`, `selective`,
> `compiled_ai`, `delta_mcp`, `incr_rtl`, `code_plan`) is **historical** and
> superseded. The **current** experiment is the **Three-Arm Scientific Smoke
> V2** (`scientific-smoke-v2` profile): 3 frozen scenarios
> (todo-smoke-001/002/003) × 3 arms (monolithic, selective,
> iterative_repository_agent) × 1 repetition = 9 runs. Smoke evidence is
> **non-publication**. Real 14B engineering preflight = PASS; accepted real
> 14B selective canary = 1 succeeded / 0 failed (`exp-20260807-131819`,
> todo-smoke-001/selective); milestone tag = `v0.8.0-canary.1`
> (annotated, created/pushed, non-stable, targets `31a6198` — first accepted
> real Qwen 14B NF4 selective-canary milestone); full 9-record Scientific
> Smoke V2 = NOT RUN; main merge = pending Full-9 audit; stable Smoke tag =
> `v0.8.0-smoke-v2-complete`, not yet created; Pilot = not authorized;
> next = fresh Full-9; local scripted evidence = 9/9; bundled CLI dry-run = 9/9. The legacy `v0.7.0-smoke-passed`
> tag and the 7/7-arm Kaggle smoke are **historical orchestration evidence
> only** — not V2 evidence.

| Phase | Status |
|---|---|
| Bootstrap and environment | Complete |
| Input audit | Complete |
| Research protocol and freeze | Complete |
| Repository and scenario preparation | Complete |
| Architecture audit and path remediation | Complete |
| Phase 4A — Domain models and contracts | Complete |
| Phase 4B — Loaders and validation | Complete |
| Phase 4C — Model backends | Complete |
| Phase 4D — Execution core | Complete |
| Phase 4E — Impact strategies and dependency graph | Complete |
| Phase 4F — Evaluation, metrics, and statistics | Complete |
| Phase 4F.1 — Scientific remediation | Complete |
| R3B/R3C/R3D closures | Complete |
| R4 token/metric contract | Accepted and frozen (`f5ae826`) |
| R5 nine scripted production records | Accepted and frozen (`7761c48`) |
| R6 deployment closure | Accepted and frozen (`949e9c2`) |
| R6 milestone-branch publication | Published (upstream set, local/remote equal) |
| Kaggle attempts (2) | Failed pre-model — preserved (`exp-20260801-024041`, `exp-20260801-024624`) |
| Kaggle runtime fix | Committed (`de3163f`) and pinned (`fb60972`) — core accepted by independent audit |
| R7A pre-rerun hardening | Complete (`d50e89e` + `4c73db6`) — four audit findings closed |
| R7B Smoke Finish | Complete (`bff0a82` + `17207bf`) — observable Qwen Smoke; independent audit required |
| R7C real-run root closure | Complete + corrected twice (`7a80e53` + `f01b8f0`; first correction `ffa179a` + `6d6aa36`; independent post-gate correction `6f88823` + `5797fc0`, HEAD `5797fc0`) — repair eligibility + preflight bootstrap corrected; final independent full-gate audit required |
| Deterministic interpreter closure | Complete (`aac9914` + `311e084`) — bare interpreter tokens bound to the active runtime at the post-generation execution boundary |
| Pre-benchmark reproducibility closure | Complete and green (`769d84e` + `e5d9430` declarations; deployment-only correction `f8d00d7`, HEAD `f8d00d7`, pushed) — dependencies fully declared in `pyproject.toml [dev]` + `requirements-dev.txt`; clean env recreated from declarations only; the previous `76a6b16` gate had 1 failure (structural notebook-pin identity test, reported truthfully, not forced green — root cause: declaration change to `pyproject.toml` after the `aac9914`/`311e084` pin; no runtime/prompt/metric/scenario/evaluator/data change needed); `f8d00d7` re-pins the deployment (SOURCE_COMMIT=`e5d9430`, DEPLOYED_BUILD_ID=`e5d9430`, bundled pyproject.toml byte-identical to canonical); complete clean suite now green: 1,834 passed / 32 skipped / 0 failed |
| Qwen 14B BNB-NF4 canary preparation | Complete (`0ece665` Commit A + `0a596b8` Commit B, pushed, local = remote, tree clean) — model-aware identity `qwen:<checkpoint-basename>:<quantization>:cfg-<12hex>` replaces the frozen `qwen:1:int8` (blocking auto-resume cross-model contamination); explicit `bnb-nf4` profile (`load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True` on T4); canonical modes `bnb-int8`/`bnb-nf4`/`fp16` via `--qwen-quantization`; prequantized-checkpoint fail-fast before model load; notebook pinned to the unquantized `14b-instruct/1` base checkpoint with `QWEN_QUANTIZATION = "bnb-nf4"`, an isolated `qwen14b_bnb_nf4_selective_canary` output dir, a fail-closed canary preflight gate, and `RUN_GENERIC_ONE_RUN = False`; the failed 14B GPTQ attempt (`exp-20260804-195126`, 0 records / 0 calls / 0 tokens, preflight failed before probe — GPTQConfig vs BitsAndBytesConfig conflict) and the `qwen:1:int8` auto-resume contamination are preserved as engineering evidence; full suite **1,877 passed / 32 skipped / 0 failed**; zero new Ruff/mypy findings; notebook source identity `SOURCE_COMMIT=0ece665` / `DEPLOYED_BUILD_ID=0ece665`; next action = Kaggle engineering preflight only for 14B bnb-nf4 |
| Qwen 14B NF4 transformers v4 loader closure | Complete (`41e9ad7` Commit A + `920ab9b` Commit B, pushed, local = remote, tree clean) — the independent OOM audit reproduced the real preflight OOM: unpinned transformers drifted to **5.0.0** and its loader materialized the 14B BF16 weights on GPU before BNB-NF4 quantization (OOM after 232.412 s, GPU 1 free 46.81 MiB / allocated 14.38 GiB; runtime Python 3.12.13 / transformers 5.0.0 / torch 2.10.0+cu128); fixed by pinning `transformers==4.57.6` in `requirements-smoke-kaggle.lock` + `requirements-kaggle.txt` (torch stays unpinned — Kaggle-provided GPU torch preserved), fail-closed preflight `_REQUIRED_IMPORTS` version check + notebook `EXPECTED_RUNTIME` entry, `low_cpu_mem_usage=True` for BNB int8/NF4 loads in `kaggle_qwen_backend._load_model`, and `_static_model_metadata` preserving identity/GPU metadata when the load fails; full suite **1,898 passed / 32 skipped / 0 failed**; regression proofs: preflight FAILs on transformers 5.0.0/absent before load, BNB loads pass `low_cpu_mem_usage=True` (fp16 does not), static metadata preserved on failed probe; next action = independent audit then Kaggle engineering preflight cell only |
| Qwen 14B NF4 loader official gate | Complete (2026-08-05; docs/deploy commit pushed, local = remote, tree clean) — the stale **int8** markdown cell immediately before `preflight-cell` was corrected to truthful **Qwen 14B BNB-NF4** wording (`Qwen2.5-Coder-14B-Instruct` base checkpoint via BitsAndBytes NF4: `load_in_4bit=True`, `bnb_4bit_quant_type="nf4"`, `bnb_4bit_compute_dtype=float16`, `bnb_4bit_use_double_quant=True`, `device_map="auto"`, Transformers 4.57.6); no executable code cell, `SOURCE_COMMIT`/`DEPLOYED_BUILD_ID` (`41e9ad7`), command, quantization setting, model path, timeout, token limit, or auth flag changed; the missing official clean-environment gate was run in a fresh disposable env created from project declarations only (`_workspace\cache\prebenchmark-py311-v4-loader`, Python 3.11.5 / **pytest 8.4.2 exactly**; Django 5.2.16, DRF 3.17.1, pytest-django 4.12.0, pytest-asyncio 1.2.0, ruff 0.15.22, mypy 1.20.2): full suite **1,898 passed / 32 skipped / 0 failed** (517.97 s); Dataset 281/4; Prompt 126/4; Pipeline Smoke 177; Scripted dry run 9 planned / 9 terminal / 9 succeeded / 0 failed / exit 0; Metric Verification 169; Ruff 0 new (91 pre-existing baseline); mypy strict Success (77 files); compileall clean; notebook compile canonical + bundled; bundle rebuilt twice via `scripts/build_upload_bundle.py` — second run content-identical (147 files / 965,015 bytes), manifests verified, no cache files; `git diff --check` clean; next action = independent audit then Kaggle engineering preflight cell only |
| Qwen 14B multi-GPU VRAM preflight closure | Complete (`f7b1ebb` Commit A + `c8f5685` Commit B, pushed, local = remote, tree clean) — the independent audit found the preflight read VRAM from **GPU 0 only** (`torch.cuda.memory_allocated(0)` etc.), so a 2x Tesla T4 `device_map="auto"` 14B bnb-nf4 load could pass while GPU 1 had <2.0 GiB free; fixed by adding the immutable `GpuVramSnapshot` value type and `_collect_gpu_vram_snapshots()` (synchronize + read allocated/reserved/free/total on **every** visible GPU, three-decimal rounding, never swallow a per-GPU failure), `free_vram_after_probe_gib = min(snapshot.free_gib)` with summed allocated/reserved scalars, a minimum-free gate requiring **every visible GPU >= 2.0 GiB** (`vram_headroom: FAIL (GPU 1 free=0.12 GiB < 2.0 GiB)`), ordered per-GPU evidence in the `kaggle_smoke_preflight.v1` JSON (`gpu_vram_by_device`) and the human preflight table, and per-GPU snapshot preservation on failed model loads via `_static_model_metadata`; official clean-env gate (`prebenchmark-py311-v4-loader`, Python 3.11.5 / pytest 8.4.2): full suite **1,915 passed / 32 skipped / 0 failed** (500.22 s); Metric Verification 169; Ruff 0 new (86 pre-existing baseline); mypy strict Success (77 files); compileall clean; notebook + bundle pin identity PASS (`SOURCE_COMMIT=f7b1ebb`); bundle integration 32 passed; builder content-identical (147 files / 968,722 bytes); mandatory adversarial case reproduced: **GPU0 3.0 GiB / GPU1 0.125 GiB → FAIL**; next action = independent audit then Kaggle engineering preflight cell only |
| Qwen 14B selective canary success | **ACCEPTED** (independent GPT-5.6 Thinking audit, 2026-08-07, documentation HEAD `5561f918`) — first successful real Qwen implementation through every functional validation stage: real engineering preflight **PASS** on 2×Tesla T4 (Python 3.12.13 / transformers 4.57.6 / bnb-nf4, minimum free VRAM 8.417 GiB, GPU-only device map); `exp-20260807-131819` (`todo-smoke-001 / selective`) **succeeded**: 3 selected / 2 preserved / 3 regenerated, one migration `0004_task_priority.py`, 3 model calls / 2,527+720=3,247 tokens / 295.944 s / 0 repair attempts; functional validation PASS; scenario evaluator **PASS 10/10**; accepted real 14B canary records = 1; **full 9-record Scientific Smoke V2 = NOT RUN** (isolated selective-only plan, do NOT call it 1/9); vs latest 7B selective: 25.0% fewer calls / 44.1% fewer tokens / repair eliminated / 14.9% slower — functional viability proven, not strategy superiority; generated `views.py` has an unused `Q` import (non-blocking, evidence NOT to be repaired); continuous cell failed closed with zero model calls (generic experiment empty — not a failure); HF local evidence `recovery_uploaded`; no merge/tag/Pilot; no stable release claimed; **milestone tag `v0.8.0-canary.1` created and pushed** (annotated, non-stable, points to `31a6198`); stable Smoke tag naming = `v0.8.0-smoke-v2-complete` (create only after Full-9 audit + main merge); **next action = one fresh Full-9 Scientific Smoke V2 using the frozen runbook** (`docs/KAGGLE_QWEN14B_FULL9_SCIENTIFIC_SMOKE_RUNBOOK.md`); record `selective_updates/records/QWEN14B-SELECTIVE-CANARY-SUCCESS-2026-08-07.md` |
| Full-9 workspace isolation closure | Complete (`7f2a450` Commit A + `e29c017` Commit B, pushed, local = remote, tree clean) — the rejected Full-9 `exp-20260807-205422` (2 succeeded / 7 failed / 62 calls / 76,858 tokens, runtime source `f7b1ebb`) was caused by **overlay source restaging leaking generated files across scenarios**: `_populate_workspace_source` reused each strategy workspace across scenarios and overlaid the snapshot without deleting stale generated files, so `0004_task_priority.py` from scenario 001 survived into 002 and produced `0005_remove_task_priority_task_deleted_at` — contaminating the selective/agent 002 and 003 records (Full-9 scientific acceptance = **rejected**, preserved as evidence only, NOT the accepted aggregate; the isolated selective canary remains accepted; `v0.8.0-canary.1` unchanged). Fixed by replacing overlay with an **exact reset from the immutable snapshot before every matrix run**: `_WORKSPACE_INFRASTRUCTURE_DIRS = {runs, tmp, snapshots}`, `_reset_workspace_source_from_snapshot` (delete source tree incl. stale generated files, then restage), `make_isolation` calls it for every arm workspace on every run. Unit edge cases 33 passed / 1 skipped (symlink skipped on Windows); sequential 001→002→003 migration proof (4 passed; 002 clean, no `0004_task_priority`, depends on canonical `0003`); nine-run zero-residue matrix proof. Official pre-benchmark gate (pytest 8.4.2, `_workspace\cache\prebenchmark-py311`): **1,928 passed / 33 skipped / 0 failed**; Dataset 161/1 (27 scenarios unchanged, scopes intact); Prompt 200/12; Pipeline Smoke 45 (incl. sequential regression); Dry Run 9 planned / 9 terminal / 9 succeeded / 0 failed / exit 0; Metric Verification 187; Ruff 0 new (5 pre-existing); mypy 0 new (4 pre-existing); compileall clean; notebook cells compile; bundle rebuilt content-identical (147 files / 969,713 bytes), manifests verified; notebook re-pinned `SOURCE_COMMIT=7f2a4509482dc7e62c2b243374592e9a88e2ff48` / `DEPLOYED_BUILD_ID=7f2a450`. Next action = fresh Full-9 with the corrected source/build |
| Kaggle relaunch + nine real Qwen records | Authorized next action = **one fresh Full-9 Scientific Smoke V2** (3 scenarios × 3 arms = 9 records) using the frozen runbook `docs/KAGGLE_QWEN14B_FULL9_SCIENTIFIC_SMOKE_RUNBOOK.md` — one engineering preflight + one benchmark process in a fresh isolated experiment; never merge the selective canary; then independent results audit |
| Pilot experiment | Not authorized |
| Research experiment | Planned |

The repository is **not yet publication-result complete**. Pilot and research
experiments remain pending. Smoke evidence is non-publication. Local scripted
records = 9/9; bundled CLI dry-run = 9/9; real 14B engineering preflight = PASS;
accepted real 14B selective canary = 1 succeeded / 0 failed
(`exp-20260807-131819`, todo-smoke-001/selective, isolated selective-only plan —
not a `1/9`); full 9-record Scientific Smoke V2 = NOT RUN; two real
Kaggle attempts failed before any model call (preserved, not deleted); a later
attempt reached 81 model calls / 47,694 tokens with 0 succeeded / 0
regenerated files (0/9, not scientific evidence); the latest attempt
(`exp-20260801-123125`) failed at runtime root (FP16 OOM + dependency drift),
which the R7C root closure addresses (exact runtime pins, int8 default, frozen
scenario context, infrastructure-nonrepairable repair classification, and a
`--kaggle-preflight-only` gate). The prior R7C report incorrectly called a
1,451-test subset the full suite; the true first full suite was 23 failed /
1,759 passed / 32 skipped, root cause = blanket `baseline_validation =>
infrastructure_nonrepairable`. A first independent GPT-5.6 Thinking correction
(`ffa179a` + `6d6aa36`) was imported via bundle fast-forward and made the exact
23 former failures pass. A second independent post-gate audit on `5e47a1e`
found the remaining issues and its exact correction was imported as
`6f88823` (fix(kaggle): align repair eligibility and script bootstrap) +
`5797fc0` (chore(deploy): pin audited preflight and live gate): the project-local
`ImportError` was incorrectly bypassing repair (now repairable via the canonical
classifier), the bundled preflight could not import `benchmark` without ambient
`PYTHONPATH` (the bundled script now bootstraps its own `src/`), and preflight
output was buffered (now streamed and persisted). Notebook source identity is
now `6f88823`. Current full gate = 1,796 passed / 32 skipped / 0 failed. Valid
real Qwen remains 0/9; no scientific evidence exists yet; Kaggle remains
blocked pending the final independent full-gate audit, after which the only
authorized Kaggle action is the engineering preflight cell — not the scientific
One-Run cell.
The **pre-benchmark final reproducibility closure** (branch
`fix/kaggle-smoke-v2-model-output-closure`, HEAD `f8d00d7`, pushed) declares the
complete pre-benchmark test environment (Django==5.2.16,
djangorestframework==3.17.1, pytest-django==4.12.0, pytest-asyncio==1.2.0,
tabulate==0.10.0, httpx==0.28.1, Jinja2==3.1.6, huggingface_hub==0.24.0,
types-pyyaml, pytest) in `pyproject.toml [dev]` + `requirements-dev.txt`
(runtime `[project.dependencies]` and `requirements-smoke-kaggle.lock`
untouched), recreated the clean environment from declarations only, and
repeated the complete clean gate. The previous `76a6b16` gate had **1 failure,
not a green full suite** (1,833 passed / 32 skipped / 1 failed): the notebook-pin
identity test failed, structural because the mandated `pyproject.toml`
declaration change breaks byte-identity with the `aac9914` SOURCE_COMMIT
(frozen artifacts were not modified to force green). Root cause was dependency
declarations changing `pyproject.toml` after the `aac9914`/`311e084` deployment
pin; **no runtime, prompt, metric, scenario, evaluator, or data change was
needed**. The exact independently reviewed deployment-only correction `f8d00d7`
(imported via bundle fast-forward, exactly one commit) re-pins the deployment
to the current source snapshot: bundled `pyproject.toml` becomes byte-identical
to canonical, and both notebooks re-pin `SOURCE_COMMIT =
e5d943065c6f4158c30a1cbbba39436ab2a7a898` / `DEPLOYED_BUILD_ID = e5d9430`
(deployment source snapshot = `e5d9430`; deployment correction = `f8d00d7`).
The complete clean suite is now **green: 1,834 passed / 32 skipped / 0 failed**;
Dataset Validation 285 passed / 5 skipped (data unchanged); Prompt Validation
158 passed; Pipeline Smoke 220 passed / 12 skipped; Dry Run 9/9; Integration
PASS; Metric Verification 169 passed; mypy strict Success (77 files); ruff 93 =
93 baseline (0 new); compileall clean; all notebook code cells compile; bundle
build content-identical; manifests verified; no cache files in `kaggle_upload`.
Historical `exp-20260801-210443` produced one failed model-output terminal
record under source `6f88823` — preserved, excluded from the current `e5d9430`
aggregation; current accepted real records = 0/9; no scientific evidence;
no tag; no Pilot; no Kaggle launch.
Current branch: `fix/kaggle-smoke-v2-model-output-closure` (HEAD `f8d00d7`;
runtime commit `aac9914`, bundle pin `311e084`, declaration commits `769d84e` +
`e5d9430`, deployment correction `f8d00d7`).
> **SELECTIVE CALIBRATION CANARY EXECUTED (2026-08-04):** the dedicated
> selective calibration canary cell ran under source/build `50ec2c1` and
> produced `exp-20260804-133523` (`todo-smoke-001 / selective`): **failed /
> `model_output`**, 4 calls / 5,804 tokens / 257.596 s, 3 selected / 2 preserved /
> 0 written; the first repair was byte-identical → `repair_no_progress`;
> atomic application wrote zero files. Model output defects were in
> `models.py` (`max_length=5` vs MEDIUM length 6) and duplicated
> `Priority(models.TextChoices)` in `serializers.py` + `views.py`. Vs the
> previous selective run: 41.6% fewer tokens, 33.3% fewer calls, 22.4% faster —
> but initial generation tokens (3,372) and output hashes were identical, so
> **harness safety controls worked while Qwen code quality did not improve**.
> The incidental monolithic run `exp-20260804-133016` (6 calls / 7,927 tokens /
> 300.165 s, `scientific_budget_exhausted`) is diagnostic evidence only, not an
> accepted comparison. The continuous cell correctly blocked fail-closed with
> `CALIBRATION_REVIEW_REQUIRED`. Accepted current dedicated canary records = 1,
> successful = 0; the full 9-record experiment is NOT run; no merge/tag/Pilot/
> Kaggle authorized; no stable release claimed. Record:
> `selective_updates/records/SELECTIVE-CANARY-RESULTS-2026-08-04.md`.
> **QWEN 14B BNB-NF4 CANARY PREPARATION COMPLETE (2026-08-05):** model-aware
> identity `qwen:<checkpoint-basename>:<quantization>:cfg-<12hex>` (derived from
> `config.json` fields + requested mode + checkpoint quantization method, no
> weight loading) replaces the frozen `qwen:1:int8`, so auto-resume can no
> longer cross-contaminate 7B and 14B executions. The 14B checkpoint is the
> official unquantized `Qwen2.5-Coder-14B-Instruct` loaded with
> `bnb-nf4` (`load_in_4bit=True, bnb_4bit_quant_type="nf4",
> bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True`, T4).
> A prequantized checkpoint (e.g. GPTQ) fails fast before model load with
> `PREQUANTIZED_CHECKPOINT_INCOMPATIBLE`; no fallback. The failed 14B GPTQ
> attempt (`exp-20260804-195126`: 0 records / 0 calls / 0 tokens, preflight
> failed before the probe — GPTQConfig + BitsAndBytesConfig conflict) and the
> auto-resume contamination (downloaded `exp-20260804-133016` because 7B and
> attempted 14B were both `qwen:1:int8`) are preserved engineering evidence.
> The notebook is pinned to `14b-instruct/1` with `QWEN_QUANTIZATION = "bnb-nf4"`,
> an isolated `qwen14b_bnb_nf4_selective_canary` output dir, a fail-closed
> canary preflight assertion, `RUN_GENERIC_ONE_RUN = False`, and no
> `--auto-resume-hf`. Full suite **1,877 passed / 32 skipped / 0 failed**;
> zero new Ruff/mypy findings; notebook identity `SOURCE_COMMIT=0ece665` /
> `DEPLOYED_BUILD_ID=0ece665`. Record:
> `selective_updates/records/QWEN14B-BNB-NF4-CANARY-READINESS.md`. Sentinel:
> `QWEN14B_NF4_CANARY_READINESS_AUDIT_REQUIRED`.

## Implemented Components

### Domain and configuration

- stable string enums;
- typed exception hierarchy;
- immutable domain records;
- runtime-checkable protocol interfaces;
- generic typed registry;
- controlled execution context;
- Pydantic v2 configuration models;
- YAML configuration loading.

### Repository and scenario infrastructure

- repository manifest loading;
- pinned version validation;
- repository profiles;
- scenario loading and structural validation;
- deterministic scenario sequencing;
- snapshot metadata;
- workspace path safety and isolation.

### Model backends

- `MockLLMBackend`;
- `DryRunLLMBackend`;
- safe `KaggleQwenBackend` skeleton;
- backend factory and registry integration;
- lazy imports preventing local `torch` or `transformers` requirements.

### Execution core

- budget enforcement;
- run state machine;
- repair lifecycle: one initial attempt plus up to two LLM repairs;
- workspace isolation;
- benchmark runner;
- single, batch, and dry-run pipeline modes;
- typed failure preservation in run records.

## Repository Structure

```text
.
├── benchmark_data/       # Public manifests, profiles, and scenario definitions
├── docs/                 # Frozen protocol and architecture documentation
├── notebooks/            # Local/Kaggle notebook adapters
├── reports/              # Phase reports and engineering evidence
├── scripts/              # Validation and packaging utilities
├── src/benchmark/
│   ├── config/
│   ├── core/
│   ├── execution/
│   ├── llm/
│   ├── repositories/
│   └── scenarios/
├── tests/                # Unit, contract, integration, and isolation tests
├── environment.yml
├── pyproject.toml
├── PROTOCOL_VERSION.md
└── SYSTEM_STATE.md
```

The canonical project map is documented in [`docs/PROJECT_STRUCTURE_MAP.md`](docs/PROJECT_STRUCTURE_MAP.md).

## Local Development

### Requirements

- Windows, Linux, or macOS;
- Conda;
- Python 3.11;
- Git.

### Create the environment

```bash
conda env create -f environment.yml
conda activate selective-regen-benchmark
python -m pip install -e .
```

If the environment already exists:

```bash
conda activate selective-regen-benchmark
```

### Install development dependencies

The project environment and locked dependency snapshot are defined by:

- [`environment.yml`](environment.yml)
- [`requirements-dev.txt`](requirements-dev.txt)
- [`requirements-lock.txt`](requirements-lock.txt)

Do not install development dependencies globally or into Conda `base`.

### Efficient local verification

Use OpenCode commands or the standalone script for fast changed-file checks:

```
/check-changed     # Fast mode: changed-file diagnostics + targeted tests
/verify            # Final mode: full validation gate
```

Direct fallback:

```bash
python scripts/check_fast.py
```

- `/check-changed` is for iterative development — runs only on changed files.
- `/verify` is the pre-commit/pre-merge gate — runs the full suite once.
- The full test suite is not rerun after every small edit.
- These commands do not replace final scientific execution on Kaggle.

## Quality Gates

Run the full local validation suite:

```bash
python -m pytest
ruff check src tests
mypy --strict src tests
python -m pip check
```

Current validated state:

- **1,898 tests passing / 32 skipped / 0 failed** (official clean-env gate, 2026-08-05, Python 3.11.5 / pytest 8.4.2)
- **Ruff: 0 new violations** (pre-existing baseline unchanged)
- **Mypy strict: 0 new errors** (base 5 pre-existing only)
- **pip check: no broken requirements** (pre-existing conda issues unrelated)
- **No local import dependency on Qwen, torch, or transformers**

## Local Execution Boundary

Local execution is limited to engineering validation.

Allowed locally:

- unit, contract, integration, and architecture tests;
- mock and dry-run execution;
- manifest and scenario validation;
- packaging and static analysis.

Not allowed locally:

- downloading Qwen model weights;
- running real LLM inference;
- executing publication benchmark runs;
- claiming Kaggle validation without genuine Kaggle evidence.

## Kaggle Execution

Real-model experiments will use the Kaggle-hosted **Qwen2.5-Coder** model.

The intended workflow is:

```text
Local engineering validation
        ↓
Kaggle smoke run
        ↓
Pilot experiment
        ↓
Protocol-calibrated main experiment
        ↓
Evaluation and statistical analysis
        ↓
Publication artifacts
```

The smoke run verifies infrastructure only. Pilot findings are descriptive. Confirmatory claims require the frozen main-study protocol.

See [`reports/KAGGLE_FEASIBILITY_REPORT.md`](reports/KAGGLE_FEASIBILITY_REPORT.md).

## Public and Private Evaluation Data

Public strategy-facing data includes:

- repository manifests;
- repository profiles;
- scenario descriptions;
- permitted acceptance criteria;
- public architecture constraints.

Private evaluation data includes:

- ground-truth action labels;
- hidden-test content;
- scoring oracle;
- restricted adjudication records.

Execution and strategy modules must not access private evaluation assets.

See [`docs/PUBLIC_PRIVATE_DATA_BOUNDARY.md`](docs/PUBLIC_PRIVATE_DATA_BOUNDARY.md) and [`docs/LEAKAGE_PREVENTION_PROTOCOL.md`](docs/LEAKAGE_PREVENTION_PROTOCOL.md).

## Reproducibility

Each research run is designed to preserve:

- protocol version;
- repository and commit;
- scenario and strategy;
- model/backend identity;
- generation parameters;
- random seeds where supported;
- prompt and content hashes;
- token usage;
- model-call counts;
- timing;
- failure classification;
- environment metadata;
- output checksums.

Real GPU inference is treated as best-effort reproducible rather than guaranteed bit-for-bit deterministic.

See [`docs/REPRODUCIBILITY_PROTOCOL.md`](docs/REPRODUCIBILITY_PROTOCOL.md).

## Research Integrity

The project follows a frozen Research Protocol v1.0.

Changes after main-result observation require a documented amendment containing:

- amendment ID and date;
- observed results before the change;
- old and new rules;
- rationale;
- researcher approval;
- affected analyses.

The benchmark must never remove a baseline, scenario, or failed run because it produces an unfavorable result.

## Documentation

Key documents:

| Document | Purpose |
|---|---|
| [`FINAL_RESEARCH_PROTOCOL.md`](docs/FINAL_RESEARCH_PROTOCOL.md) | Frozen scientific protocol |
| [`GROUND_TRUTH_PROTOCOL.md`](docs/GROUND_TRUTH_PROTOCOL.md) | Annotation and adjudication |
| [`SCENARIO_TAXONOMY.md`](docs/SCENARIO_TAXONOMY.md) | Scenario distribution and schema |
| [`STATISTICAL_ANALYSIS_PLAN.md`](docs/STATISTICAL_ANALYSIS_PLAN.md) | Confirmatory and exploratory analysis |
| [`EXECUTION_AND_FAILURE_POLICY.md`](docs/EXECUTION_AND_FAILURE_POLICY.md) | Runs, repairs, and failures |
| [`LEAKAGE_PREVENTION_PROTOCOL.md`](docs/LEAKAGE_PREVENTION_PROTOCOL.md) | Hidden-test and oracle isolation |
| [`SOFTWARE_ARCHITECTURE.md`](docs/SOFTWARE_ARCHITECTURE.md) | Layered design and interfaces |
| [`PROJECT_STRUCTURE_MAP.md`](docs/PROJECT_STRUCTURE_MAP.md) | Canonical repository map |
| [`SYSTEM_STATE.md`](SYSTEM_STATE.md) | Current implementation state |

## OpenRouter API Backend

The benchmark supports an optional OpenRouter API backend for real LLM inference
without requiring a local GPU or model download.

### Usage

```bash
# Set your OpenRouter API key (do not commit this value)
export OPENROUTER_API_KEY="sk-or-v1-YOUR-KEY-HERE"

# Run with OpenRouter backend (default free model):
python seven_arm_benchmark.py --backend openrouter --profile smoke

# Run with a specific model:
python seven_arm_benchmark.py --backend openrouter \
  --openrouter-model "nvidia/nemotron-3-super-120b-a12b:free" \
  --profile smoke

# Custom timeout:
python seven_arm_benchmark.py --backend openrouter \
  --openrouter-timeout 60 \
  --profile smoke
```

### CLI options

| Argument | Default | Description |
|----------|---------|-------------|
| `--backend` | `kaggle-qwen` (non-dry-run) / `mock` (dry-run) | Backend selection: `mock`, `kaggle-qwen`, `openrouter` |
| `--openrouter-model` | `nvidia/nemotron-3-super-120b-a12b:free` | Model identifier for OpenRouter API |
| `--openrouter-timeout` | `120.0` | Request timeout in seconds |

### Requirements

- `OPENROUTER_API_KEY` environment variable
- No GPU or model download required
- Free model availability and rate limits are provider-controlled

### Compatibility

- `--dry-run` continues using `MockLLMBackend` (no API calls)
- Without `--backend`, non-dry-run preserves `KaggleQwenBackend`
- `--backend openrouter` selects `OpenRouterBackend` explicitly

### Security

- API key must come from `OPENROUTER_API_KEY` environment variable only
- No `--api-key` CLI argument exists
- The key is never printed, logged, or included in exceptions
- Scientific Smoke remains blocked until this branch is merged and audited

## Git Workflow

New work is developed on protected phase branches:

```text
phase/<phase-id>-<description>
```

A phase is merged into `main` only after:

1. all tests pass;
2. Ruff passes;
3. strict mypy passes;
4. dependency checks pass;
5. the diff is reviewed;
6. no secret, model file, hidden test, or ground truth is exposed;
7. post-merge tests pass.

Force-pushing to `main` is prohibited.

## Roadmap

Immediate next milestones:

- [x] Phase 4E — dependency graph and impact strategies
- [x] Phase 4F — evaluation, metrics, statistics, and result export
- [x] Phase 4F.1 — scientific remediation (5 gaps closed)
- [x] Legacy Seven-Arm orchestration smoke (historical, non-publication; not V2 evidence)
- [x] Checkpoint/resume support
- [x] R5 local scripted production proof 9/9
- [x] R6 byte-reproducible deployment bundle
- [x] R6 final independent re-audit — ACCEPTED AND FROZEN
- [x] R6 milestone-branch publication (push, local/remote equality)
- [x] First real Kaggle attempts (2) — failed pre-model, preserved, root causes fixed
- [x] Kaggle runtime fix — committed (`de3163f`) and pinned (`fb60972`)
- [ ] Independent runtime-fix audit
- [x] Independent post-gate audit of R7C correction — performed on `5e47a1e`; exact correction imported (`6f88823` + `5797fc0`)
- [ ] Final independent full-gate audit of `5797fc0`
- [ ] Kaggle engineering preflight cell only (authorized action after final audit; not the scientific One-Run cell)
- [ ] Kaggle environment preflight + relaunch
- [ ] Real Three-Arm Qwen Smoke 9/9 (fresh Full-9 Scientific Smoke V2 using the frozen runbook; canary success recorded 2026-08-07)
- [ ] Stable v0.8.0-smoke-v2-complete tag after Full-9 result audit + main merge (replaces the stale v2.0.0-scientific-smoke future-tag naming; milestone tag v0.8.0-canary.1 already created/pushed, non-stable)
- [ ] Pilot freeze
- [ ] Pilot experiment
- [ ] Research (main confirmatory) experiment
- [ ] Arm-to-protocol alignment review
- [ ] Reproducibility archive and DOI
- [ ] Paper submission artifacts

## Citation

The paper and benchmark are still under development. Until a formal citation is released, cite the repository URL and the release/tag used in your work.

Working paper:

> **Don't Regenerate What Hasn't Changed: Selective Regeneration for Token-Efficient LLM-Driven Software Evolution**

A formal `CITATION.cff` file will be added when author, institution, and publication metadata are finalized.

## License

Original benchmark source code is licensed under the [MIT License](LICENSE).

Third-party repositories, dependencies, model assets, and derived materials remain governed by their original licenses. This repository does not relicense third-party source code or model weights.

## Author

**Ahmed Ehab H.**

GitHub: [AhmedEhabH](https://github.com/AhmedEhabH)

## Acknowledgements

This project uses open-source software and research infrastructure from the Python, Django, Kaggle, and open-weight code-model communities.

---

**Project status:** R4, R5, and R6 accepted and frozen. R6 deployment closure
is frozen at `949e9c2` and the milestone branch `experiment/three-arm-smoke-v2`
is published (freeze `4b2dd27`). Post-R6, two real Kaggle attempts failed
pre-model (`exp-20260801-024041`, `exp-20260801-024624`; preserved), the
runtime blockers were fixed and pinned (`de3163f`, `fb60972`), the R7A
hardening closed the four audit findings (`d50e89e`, `4c73db6`), and a later
real attempt reached 81 model calls / 47,694 tokens with 0 succeeded / 0
regenerated files (0/9). The **R7B Smoke Finish**
(`fix/kaggle-smoke-v2-finish`, `bff0a82` + `17207bf`) makes the Qwen Smoke run
observable and executable. The **R7C real-run root closure**
(`fix/kaggle-smoke-v2-real-run-root`, `7a80e53` + `f01b8f0`) closes the root
contracts the failed real attempt exposed: exact runtime pins installed and
verified in the notebook, int8 model default with VRAM headroom checks, frozen
scenario context in strategy prompts, infrastructure-nonrepairable failure
classification, and a `--kaggle-preflight-only` gate that fails fast before any
model call. The prior R7C report incorrectly called a 1,451-test subset the
full suite; the true first full suite was 23 failed / 1,759 passed / 32 skipped
(root cause = blanket `baseline_validation => infrastructure_nonrepairable`).
The independent GPT-5.6 Thinking correction (`ffa179a` + `6d6aa36`, HEAD
`6d6aa36`, pushed) makes the exact 23 former failures pass and corrects DRF
import mapping, exact version verification, fail-fast preflight, driver-level
VRAM, CPU-offload rejection, the Python 3.12 runtime contract, and stale source
identity (`SOURCE_COMMIT=ffa179a`). Current full gate = 1,790 passed / 32
skipped / 0 failed; valid real Qwen remains 0/9. The **pre-benchmark
reproducibility closure** (branch `fix/kaggle-smoke-v2-model-output-closure`,
HEAD `f8d00d7`, pushed) then declared the complete pre-benchmark dependencies
and recreated the clean environment from declarations only; the previous
`76a6b16` repeated clean gate = **1,833 passed / 32 skipped / 1 failed** (sole
failure = the notebook-pin identity test, structural — the mandated
`pyproject.toml` declaration change breaks byte-identity with the pinned
`aac9914` SOURCE_COMMIT — reported truthfully, frozen artifacts not modified to
force green). The exact deployment-only correction `f8d00d7` re-pins the
deployment to the current source snapshot (`e5d9430`), and the complete clean
suite is now **1,834 passed / 32 skipped / 0 failed** with the identity test
green. Historical
`exp-20260801-210443` produced one failed model-output terminal record under
`6f88823` — preserved, excluded from the current `e5d9430` aggregation; current
accepted real records = 0/9 at that time. The **Qwen 14B selective canary
success** (2026-08-07, accepted by independent audit) then established the
first accepted real 14B result (preflight PASS + 1 succeeded selective canary).
Real-model benchmark execution (nine real Qwen Smoke V2 records) now proceeds
to one fresh Full-9 Scientific Smoke V2 using the frozen runbook
`docs/KAGGLE_QWEN14B_FULL9_SCIENTIFIC_SMOKE_RUNBOOK.md`. Smoke evidence is
non-publication. The **selective calibration canary** (2026-08-04,
`exp-20260804-133523`, source/build `50ec2c1`) ran and failed with
`model_output`: 4 calls / 5,804 tokens / 257.596 s, 0 files written; harness
safety controls (no-progress detection, atomic writes, continuation gate)
worked while Qwen code quality did not improve (identical initial generation
tokens and output hashes vs the previous selective run). The incidental
monolithic run `exp-20260804-133016` is diagnostic evidence only. The full
9-record real experiment remains **not run**; no scientific evidence; no tag; no
Pilot; no Kaggle relaunch. See
`selective_updates/records/SELECTIVE-CANARY-RESULTS-2026-08-04.md`.

**QWEN 14B SELECTIVE CANARY SUCCESS (2026-08-07):** the first successful real
Qwen implementation reached and passed every functional validation stage. Real
engineering preflight = **PASS** on 2×Tesla T4 (bnb-nf4, minimum free VRAM
8.417 GiB, GPU-only device map). Canary `exp-20260807-131819`
(`todo-smoke-001 / selective`) = **succeeded**: 3 selected / 2 preserved / 3
regenerated, one migration `todo/migrations/0004_task_priority.py`, 3 model
calls / 2,527+720=3,247 tokens / 295.944 s / 0 repair attempts; functional
validation PASS; scenario evaluator PASS 10/10. Accepted real 14B canary
records = 1; **full 9-record Scientific Smoke V2 = NOT RUN** (the canary is an
isolated selective-only plan, not `1/9`). Interpretation: 14B crossed the
model-quality floor seen with 7B on the same task (25.0% fewer calls, 44.1%
fewer tokens, repair eliminated, 14.9% slower) — functional viability, not
strategy superiority. The generated `views.py` has an unused `Q` import
(non-blocking evidence quality note; the accepted evidence workspace must NOT
be modified or regenerated). The continuous cell failed closed with zero model
calls because the generic experiment was empty — not a failure; do NOT patch
the continuous workflow before Full-9. HF local evidence =
`recovery_uploaded`. Next action = **one fresh Full-9 Scientific Smoke V2**
(3 scenarios × 3 arms = 9 records) using the frozen runbook
`docs/KAGGLE_QWEN14B_FULL9_SCIENTIFIC_SMOKE_RUNBOOK.md` (runtime source
`f7b1ebba73b52868a95c47ef3806d3b09da16d93`, build `f7b1ebb`, profile
`scientific-smoke-v2`, protocol 1.0, one engineering preflight + one benchmark
process in a fresh isolated experiment; never merge the canary). No merge / no
tag / no Pilot; no stable release claimed. Record:
`selective_updates/records/QWEN14B-SELECTIVE-CANARY-SUCCESS-2026-08-07.md`.
