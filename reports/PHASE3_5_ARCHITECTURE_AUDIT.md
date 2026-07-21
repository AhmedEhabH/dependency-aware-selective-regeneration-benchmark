# Phase 3.5 — Static Architecture Audit and Project Map Report

**Phase:** 3.5  
**Date:** 2026-07-22  
**Status:** COMPLETE  
**Next Phase:** Phase 4A — Domain Models and Contracts (authorized)

---

## 1. Summary

Phase 3.5 performed a static architecture audit, created a canonical project map, defined the software architecture with 13 layers and 11 interface specifications, documented dependency rules, and created a Phase 4 implementation blueprint split into 6 milestones. The project has a critical structural conflict (duplicate root-level and project-level directories) which is documented with a remediation plan.

## 2. Current Actual Tree

```
master-2026-07-21-2355/                          ← OUTER DIRECTORY (no .git)
├── benchmark_data/        (stale duplicate — outside git)
│   ├── repository_profiles/
│   └── scenarios/
├── docs/                  (4 files, outside git)
│   ├── OPENCODE_EXECUTION_GUIDE.md
│   ├── FINAL_RESEARCH_PROTOCOL_DECISIONS.md
│   ├── HUMAN_DECISIONS_REQUIRED.md
│   └── MASTER_IMPLEMENTATION_PLAN.md
├── inputs/                (source inputs, outside git — correct)
│   └── paper/
│       ├── MSc_Proposal_Selective_Regeneration_Revised.pdf
│       └── MSc_Proposal_Selective_Regeneration_Revised.tex
└── project/               ← CANONICAL GIT ROOT (contains .git/)
    ├── .git/
    ├── .gitignore, .gitattributes
    ├── environment.yml, requirements-*.txt, requirements-lock.txt
    ├── SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, PROTOCOL_VERSION.md
    ├── docs/               (8 frozen protocol + 8 Phase 3.5 architecture docs)
    ├── benchmark_data/
    │   ├── manifests/
    │   ├── repository_profiles/
    │   └── scenarios/    (24 YAML files)
    ├── src/benchmark/     (scaffold only — __init__.py)
    ├── tests/             (scaffold only — __init__.py)
    ├── reports/           (11 reports)
    ├── notebooks/         (empty)
    ├── scripts/           (empty)
    ├── .mypy_cache/       (generated — gitignored)
    └── .ruff_cache/       (generated — gitignored)
```

## 3. Architecture Decisions

| ID | Decision | Detail |
|----|----------|--------|
| AD-01 | Protocol over ABC | Use typing.Protocol for all interfaces; ABC only when shared default implementation is needed |
| AD-02 | Instantiated registries | No module-level singleton registries; registries are instantiated and injected |
| AD-03 | Dependency injection | All dependencies injected via constructors; no global state |
| AD-04 | Lazy Kaggle imports | torch/transformers imported only inside methods of KaggleQwenBackend, not at module level |
| AD-05 | Core isolation | Core package imports nothing from infrastructure (strategies, LLM, execution, evaluation) |
| AD-06 | Immutable run records | All run records are frozen dataclasses; no mutation after creation |
| AD-07 | Pydantic for config | Configuration models use Pydantic for runtime validation |
| AD-08 | Atomic file writes | Provenance and output writing uses atomic file operations |
| AD-09 | Not import hidden tests | No private_evaluation/ import allowed in strategies/, execution/, or llm/ |
| AD-10 | No repo-specific branches | No `if repo == ...` branching in generic execution logic |

## 4. Interfaces Defined

11 interfaces specified in `SOFTWARE_ARCHITECTURE.md`:

| Interface | File | Key Method |
|-----------|------|-----------|
| ImpactStrategy | `core/protocols.py` | analyze_impact(repo, change, universe) -> ImpactPrediction |
| LLMBackend | `core/protocols.py` | async generate(prompt, ...) -> LLMResponse |
| RepositoryAdapter | `core/protocols.py` | clone(url, ref) -> RepositorySnapshot |
| ScenarioProvider | `core/protocols.py` | get_scenario(id) -> Scenario |
| DependencyExtractor | `core/protocols.py` | build_graph(snapshot) -> DependencyGraph |
| ExecutionRunner | `core/protocols.py` | run_strategy(strategy, scenario) -> RunRecord |
| Validator | `core/protocols.py` | validate(snapshot, result) -> ValidationReport |
| Metric | `core/protocols.py` | compute(prediction, ground_truth) -> float |
| StatisticsAnalyzer | `core/protocols.py` | analyze(results) -> AnalysisReport |
| ResultWriter | `core/protocols.py` | write_run(record) -> None |
| ProvenanceRecorder | `core/protocols.py` | record(event) -> None |

## 5. Dependency Rules

Dependency direction is strictly inward-pointing:

```
CLI / Notebooks
  → Execution / Strategies / Validation
    → Graph / LLM / Scenarios / Repositories
      → Config
        → Core (everything depends on Core; Core depends on nothing)
```

Full dependency matrix documented in `docs/DEPENDENCY_RULES.md`.

## 6. Public/Private Boundary

| Boundary | Public | Private |
|----------|--------|---------|
| Data | Manifests, profiles, scenarios, public tests | Hidden tests, ground truth, scoring oracle |
| Access | Visible to strategies | Inaccessible during execution |
| Paths | `benchmark_data/` | `private_evaluation/` |

## 7. Phase 4 Milestones

| Milestone | Focus | Files | Dependencies | Complexity |
|-----------|-------|-------|--------------|------------|
| 4A | Domain models + contracts | ~12 | None | Medium |
| 4B | Loaders + validation | ~16 | 4A | Medium |
| 4C | Model backends | ~5 | 4A | Medium |
| 4D | Execution core | ~8 | 4A, 4B, 4C | High |
| 4E | Provenance + results | ~6 | 4A | Low |
| 4F | Architecture + contract tests | ~8 | 4A-4E | Medium |

## 8. Files Created (Phase 3.5)

| File | Description |
|------|-------------|
| `docs/PROJECT_ROOT_AND_PATH_POLICY.md` | Canonical root, duplicate remediation, path convention |
| `docs/PROJECT_STRUCTURE_MAP.md` | Complete proposed tree with directory responsibilities |
| `docs/SOFTWARE_ARCHITECTURE.md` | 13-layer architecture, 11 interface specs |
| `docs/DEPENDENCY_RULES.md` | Allowed/prohibited dependency directions |
| `docs/EXTENSION_GUIDE.md` | Plugin lifecycle, registry design, protocol skeletons |
| `docs/PUBLIC_PRIVATE_DATA_BOUNDARY.md` | Public vs private data classification, data flow, audit |
| `docs/PHASE4_IMPLEMENTATION_BLUEPRINT.md` | 6 milestones with files, tests, acceptance criteria |
| `docs/ARCHITECTURE_VALIDATION_PLAN.md` | 11 validation checks with recommended approaches |

## 9. Risks and Unresolved Issues

| Risk | Severity | Detail |
|------|----------|--------|
| **Critical:** Root-level stale duplicates | HIGH | docs/ and benchmark_data/ exist both outside and inside Git repo. Must be cleaned before commit |
| Phase 3 benchmark_data/ files not committed | MEDIUM | 35 files in project/benchmark_data/ exist in working tree only |
| django CMS and Saleor not cloned locally | MEDIUM | Test suite runnability not verified; Phase 4B loader tests will require test repositories |
| Scenario YAML format inconsistencies | LOW | Some fields use different naming conventions (e.g., `blast_radius: single_model_layer` vs `blast_radius: localized`) |
| No pyproject.toml | LOW | Project uses requirements.txt; pyproject.toml proposed for Phase 4 |
| `.gitignore` missing `__pycache__/` and `runs/` entries | LOW | Should be added before significant implementation |

## 10. Exact Next Task

**Phase 4A — Domain Models and Contracts**: Implement immutable data models in `src/benchmark/core/` (enums, models, exceptions, protocols, registry, context) and configuration models in `src/benchmark/config/` (models, loader, validation). No strategy or execution code.

---

## Validation Checklist

- [x] One canonical project root explicitly identified: `project/`
- [x] Every existing important directory mapped
- [x] Duplicate root/project directories documented
- [x] Every proposed package has one clear responsibility
- [x] Every interface has an owner and contract
- [x] Dependency directions are acyclic
- [x] Local package imports do not require Qwen dependencies
- [x] Hidden assets are outside strategy-facing paths
- [x] Notebook and CLI are adapters only
- [x] Adding a strategy does not require changing core
- [x] Adding an LLM backend does not require changing core
- [x] Adding a repository adapter does not require changing core
- [x] Phase 4 is split into manageable milestones
- [x] No benchmark implementation was started
- [x] No Qwen model was downloaded or executed
- [x] Phase 4A is recorded as the exact next task
