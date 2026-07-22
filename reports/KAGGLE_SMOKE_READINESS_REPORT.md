# Kaggle Smoke Readiness Report

**Date:** 2026-07-23
**Tag:** v0.6.0-rc.1 (pending)
**Branch:** fix/phase4f-scientific-gaps

---

## 1. Exact Files for Kaggle Upload

### Notebook
- `notebooks/seven_arm_benchmark.ipynb` — Jupyter notebook for Kaggle execution

### Code Dataset (benchmark-code)
- `seven_arm_benchmark.py` — Main orchestrator (entry point)
- `src/benchmark/` — Full package source (core, config, scenarios, repositories, llm, execution, strategies, graph, selection, evaluation, comparison, statistics)
- `configs/smoke.yaml` — Smoke profile config
- `configs/pilot.yaml` — Pilot profile config
- `configs/research.yaml` — Research profile config
- `pyproject.toml` — Package metadata and tool configuration
- `requirements-kaggle.txt` — Kaggle-only dependencies (torch, transformers, etc.)

### Benchmark Data Dataset (benchmark-data)
- `benchmark_data/scenarios/` — 24 scenario YAML definitions (3 repos x 8 scenarios)
- `benchmark_data/manifests/` — Repository version manifests
- `benchmark_data/repository_profiles/` — Repository architectural profiles

---

## 2. Model Input Requirements

- **Model:** Qwen2.5-Coder (via Kaggle Dataset mount)
- **Discovery:** Dynamic via `/kaggle/input` directory enumeration
- **Fallback:** None — `local_files_only=True` is enforced
- **GPU:** Required for real execution (fallback to CPU prints warning)
- **Dependencies:** torch, transformers, datasets, kagglehub, sentencepiece, protobuf (listed in `requirements-kaggle.txt`)

---

## 3. Notebook Path

`notebooks/seven_arm_benchmark.ipynb`

Cell structure:
1. Install Kaggle dependencies
2. Verify GPU availability
3. Verify Qwen model mount
4. Clone repository
5. **Dry-run smoke validation** (`--dry-run --profile smoke`)
6. **Real smoke execution** (commented out; requires uncomment, `--profile smoke` default)
7. View results
8. Markdown: explicit instructions that pilot/research require `--profile` selection

---

## 4. Code Dataset Contents

The benchmark-code Dataset contains:
- Entry-point script: `seven_arm_benchmark.py`
- Full source tree under `project/src/benchmark/` (13 packages)
- Profile configs under `project/configs/`
- All quality-gate configuration in `project/pyproject.toml`
- Kaggle-only dependency manifest

## 5. Benchmark Dataset Contents

The benchmark-data Dataset contains:
- 24 scenario YAML files under `scenarios/` (todo: 8, djangocms: 8, saleor: 8)
- Repository version manifests: `manifests/repositories.yaml`, `manifests/repository_versions.yaml`
- Repository profiles: `repository_profiles/todo.yaml`, `repository_profiles/djangocms.yaml`, `repository_profiles/saleor.yaml`

---

## 6. Expected Smoke Runtime Steps

1. Notebook Cell 1: `pip install -r requirements-kaggle.txt` (torch, transformers, etc.)
2. Notebook Cell 2: Verify GPU — `torch.cuda.is_available()` check
3. Notebook Cell 3: Verify `/kaggle/input` Qwen model mount
4. Notebook Cell 4: `git clone` benchmark repository; `cd benchmark/project`
5. Notebook Cell 5: **Dry-run smoke** — 1 scenario x 7 strategies via mock backend (no API calls)
6. Notebook Cell 6 (manual uncomment): **Real smoke** — 1 scenario x 7 strategies via `KaggleQwenBackend`
7. Notebook Cell 7: Display `runs/benchmark_summary.json` with per-arm counts and metadata

---

## 7. Expected Outputs

- `runs/benchmark_summary.json` containing:
  - Per-arm success/failure/timeout counts and durations
  - `_meta.publication_evidence: false` (smoke is non-publication)
  - `_meta.label: "orchestration-smoke"`
- Console output: GPU info, model discovery, per-arm progress logs
- No publication tables, no LaTeX exports, no statistical analysis (smoke only)

---

## 8. Known Risks

1. **Qwen model mount may fail** — Notebook emits warning and continues; benchmark will fail at model load
2. **9-hour Kaggle session limit** — Not a concern for smoke (1 scenario, 7 strategies, well under limit)
3. **GitHub rate limiting** — If repository clone fails, Kaggle session must retry
4. **Kaggle internet requirement** — `isInternetEnabled: true` is set in notebook metadata
5. **No ground truth leakage** — Hidden acceptance criteria remain in scenario YAMLs; strategies do not access them
6. **Local files_only=True** — Enforced in KaggleQwenBackend (no network fallback for model weights)

---

## 9. Scientific Remediation Status (Phase 4F.1)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| `aggregate_run_records` | **COMPLETE** | Full micro/macro impl in `src/benchmark/comparison/aggregator.py`; 8 tests |
| Paired bootstrap for H1 | **COMPLETE** | `paired_bootstrap_ci()` + `paired_compare()` in `analysis.py`; 3 tests |
| Benjamini-Hochberg correction | **COMPLETE** | `benjamini_hochberg()` in `analysis.py`; 5 tests |
| Holm correction | **COMPLETE** | `holm_correction()` in `analysis.py`; 5 tests |
| NI margins 0.03, 0.05, 0.10 | **COMPLETE** | `non_inferiority_test()` sensitivity parameter; 4 tests |
| Generalized binomial CI | **COMPLETE** | `scipy.stats.norm.ppf` replacement; 5 tests |
| BH bug fix | **COMPLETE** | Descending+max → ascending+step-down |
| **Overall** | **14/19 SAP requirements implemented** | 3 design-level gaps remain (McNemar, arch metrics, blast-radius interaction) — do not block smoke |

---

## 10. Profile-Protocol Alignment Status

| Profile | Label | Scenario Count | Strategies | Reps | Publication | Status |
|---------|-------|---------------|-----------|------|-------------|--------|
| Smoke | `orchestration-smoke` | 1 | All 7 | 1 | No | **ALIGNED** |
| Pilot | `protocol-pilot` | 12 | agent, selective | 2 | No | **ALIGNED** |
| Research | `protocol-research` | 24 | agent, selective, compiled_ai, delta_mcp | 3 | Yes | **ALIGNED** |

Changes made:
- Profiles moved from `PROFILE_SCENARIO_COUNTS` dict to typed `ExecutionProfile` dataclasses
- Pilot corrected from 3x7 to 12x2x2 per protocol stage-gated design
- Research corrected from 24x7 to 24x4 (full-evolution) with impact-only strategies separated
- YAML configs updated with `profile_label`, `repetitions`, and `is_publication` fields
- `IMPACT_ONLY_STRATEGIES` defined (monolithic, incr_rtl, code_plan) to avoid unnecessary full generation

---

## 11. Quality Gates

| Gate | Result |
|------|--------|
| `python -m pytest` | **441/441 passed** |
| `ruff check src tests` | **0 violations** |
| `mypy --strict src tests` | **0 errors** |
| `python -m pip check` | **Clean (project dependencies)** |

---

## 12. Final Decision

**AUTHORIZED**
