# System State

## Current Phase
**Phase 3.6 — Structure Remediation and Baseline Commit** (COMPLETE — Phase 4A authorized)

## Current Task
Phase 3.6 complete. Structural conflicts resolved, scenario blast_radius fixed, .gitignore updated, baseline commit created. Phase 4A is the exact next task.

## Completed Work
- [x] Phase 0 — Bootstrap and Environment (LOCAL_ENGINEERING_VALIDATED)
- [x] Phase 1 — Input Audit (LOCAL_ENGINEERING_VALIDATED)
- [x] Phase 2A — Research Protocol Draft (DRAFT — superseded by v1.0)
- [x] Phase 2B — Protocol Freeze (FROZEN)
- [x] Phase 3 — Repository and Scenario Preparation (COMPLETE)
- [x] Phase 3.5 — Static Architecture Audit and Project Map (COMPLETE)
- [x] Phase 3.6 — Structure Remediation and Baseline Commit (COMPLETE)
- [x] Inspect full repository layout and identify structural conflicts
- [x] Document duplicate root `docs/` and `benchmark_data/` outside Git
- [x] Define canonical project root and path policy
- [x] Create complete proposed project structure map
- [x] Define 13-layer software architecture with dependency rules
- [x] Specify 11 interface protocols (ImpactStrategy, LLMBackend, etc.)
- [x] Document plugin/registry design with extension guide
- [x] Define public/private data boundary
- [x] Split Phase 4 into 6 implementation milestones (4A–4F)
- [x] Create architecture validation plan with 11 checks
- [x] Copy outer reference docs (`OPENCODE_EXECUTION_GUIDE.md`, `MASTER_IMPLEMENTATION_PLAN.md`) into `project/docs/`
- [x] Delete stale outer `FINAL_RESEARCH_PROTOCOL_DECISIONS.md` and `HUMAN_DECISIONS_REQUIRED.md`
- [x] Delete stale outer `benchmark_data/` (incomplete duplicate)
- [x] Preserve `inputs/paper/` as immutable external data
- [x] Fix blast_radius in 14 scenario YAMLs to match taxonomy standard
- [x] Deduplicate `.gitignore` and add `runs/` entry
- [x] Validate full project tree (79 files, 15 dirs, scaffold-only src)
- [x] Create baseline commit `845ba49` (57 files, 7652 insertions)
- [x] Create `reports/PHASE3_6_STRUCTURE_REMEDIATION_REPORT.md`
- [x] Update `DECISION_LOG.md` (added D010)
- [x] Update `SYSTEM_STATE.md`
- [x] Update `TODO.md` (added Phase 3.6 tasks)
- [x] Update `reports/latest_phase_report.md` (Phase 3.6 report)

## Files Created
18 under `docs/`:
- 8 frozen protocol (Phase 2B)
- 8 architecture (Phase 3.5)
- 2 reference copies (Phase 3.6): `OPENCODE_EXECUTION_GUIDE.md`, `MASTER_IMPLEMENTATION_PLAN.md`
29 under `benchmark_data/`:
- `benchmark_data/manifests/repositories.yaml`
- `benchmark_data/manifests/repository_versions.yaml`
- `benchmark_data/repository_profiles/todo.yaml`
- `benchmark_data/repository_profiles/djangocms.yaml`
- `benchmark_data/repository_profiles/saleor.yaml`
- 24 scenario YAMLs under `benchmark_data/scenarios/` (8 per repo)
14 under `reports/`:
- Phase 2B: `PHASE2B_PROTOCOL_FREEZE_REPORT.md`
- Phase 3: `REPOSITORY_SELECTION_REPORT.md`, `REPOSITORY_ARCHITECTURE_BOUNDARIES.md`, `SCENARIO_DESIGN_REPORT.md`, `LICENSING_AND_REDISTRIBUTION.md`, `KAGGLE_FEASIBILITY_REPORT.md`, `PHASE3_REPOSITORY_SCENARIO_REPORT.md`
- Phase 3.5: `PHASE3_5_ARCHITECTURE_AUDIT.md`, `PROJECT_STRUCTURE_CONFLICT_REPORT.md`
- Phase 3.6: `PHASE3_6_STRUCTURE_REMEDIATION_REPORT.md`

## Files Modified (Phase 3.6)
- `.gitignore` (deduplicated, added `runs/`, added report exceptions)
- `benchmark_data/scenarios/djangocms-*.yaml` (8 files, blast_radius corrected)
- `benchmark_data/scenarios/saleor-*.yaml` (8 files, blast_radius corrected)
- `DECISION_LOG.md` (added D010)
- `SYSTEM_STATE.md` (this file)
- `TODO.md` (added Phase 3.6 tasks)
- `reports/latest_phase_report.md` (Phase 3.6 report)

## Frozen Protocol Checksums (SHA-256)

| Document | Checksum |
|----------|----------|
| `docs/FINAL_RESEARCH_PROTOCOL.md` | `9D4A140C1CBA19C3076AF8C71AD859F243C31836FECD6026C2CD86CFC271B148` |
| `docs/GROUND_TRUTH_PROTOCOL.md` | `83F1ADB28CD99B6859BD7BE8189B22C2D272538CBB19B386D921F9DC728DD9E5` |
| `docs/SCENARIO_TAXONOMY.md` | `5FA4D7114E1993E2D8FB570EC9BAC4129F3956B09E7555C200C118E206D9BB62` |
| `docs/STATISTICAL_ANALYSIS_PLAN.md` | `FA8B76C41FF05462E80675B297917A904ECD4605CA5AD54C84740A38B6AB1D4C` |
| `docs/EXECUTION_AND_FAILURE_POLICY.md` | `FB3072880A6EBDD259707F9F64F50D56DF6DD4B04DBDE80E1E2867C80295F49E` |
| `docs/LEAKAGE_PREVENTION_PROTOCOL.md` | `F78AF1F57C8A59EA324E1996B4B172F7A02EF9D0D8EB66DD1D02F9EFD2B53910` |
| `docs/REPRODUCIBILITY_PROTOCOL.md` | `A59A666CC740BF2F9F9D9D193422892C1E064D99F6D264250C5625CFB35DB02E` |
| `docs/RESEARCHER_DECISIONS_DA_AC.md` | `1884352AF8813E794A25A1BAE947269BB343C788A22A933F59754B7DEE607BD3` |

## Environment Status
- **Platform:** Windows (win32)
- **Python (project env):** 3.11.15
- **Conda:** 23.10.0
- **Git:** 2.49.0
- **Project env:** `selective-regen-benchmark` — ACTIVATED AND VALIDATED
- **Package resolver:** conda (defaults channel) + pip
- **Dependency conflicts:** None

## Local Checks Passed
- All 14 DA decisions applied and verified: ✅
- All 11 AC corrections applied and verified: ✅
- 9 contradictions reconciled: ✅
- No unresolved REQUIRES_RESEARCHER_APPROVAL items: ✅
- Regression pass-rate formula corrected: ✅
- Hidden tests separated from held-out scenarios: ✅
- Failed strategies remain in analysis: ✅
- Repair budgets uniform (max 2): ✅
- Candidate artifact universe freeze policy explicit: ✅
- Kaggle monetary cost not fabricated: ✅
- Protocol amendment rules explicit: ✅
- Authoritative proposal unchanged: ✅
- All 8 frozen documents SHA-256 checksums generated: ✅
- DA-03 compliance verified (all versions ≥ 90 days): ✅
- DA-01 compliance verified (automated test suites): ✅
- DA-02 compliance verified (permissive licenses): ✅
- 24 scenarios designed across 3 repositories: ✅
- All 8 change types covered per repository: ✅
- All 3 blast radii represented: ✅
- Hidden tests defined per scenario (AC-03): ✅
- Canonical project root explicitly identified: ✅
- Duplicate root/project directories documented: ✅
- 13-layer architecture defined with dependency rules: ✅
- 11 interface protocols specified: ✅
- Plugin/registry design documented: ✅
- Public/private data boundary defined: ✅
- Phase 4 split into 6 milestones (4A–4F): ✅
- Architecture validation plan with 11 checks: ✅
- No benchmark implementation started: ✅
- No Qwen model downloaded or executed: ✅
- Outer reference docs copied into project/docs/: ✅
- Stale outer docs deleted (2 superseded files): ✅
- Stale outer benchmark_data/ deleted: ✅
- External inputs preserved as immutable: ✅
- All 24 scenario blast_radius values taxonomy-compliant: ✅
- .gitignore deduplicated with runs/ added: ✅
- Project tree validated (79 files, scaffold-only src): ✅
- Baseline commit created (845ba49, 57 files): ✅
- Working tree clean after commit: ✅

## Local Checks Failed
- None

## Kaggle Checks Pending
- Real model loading or inference
- Qwen model discovery
- GPU/torch availability
- Real benchmark runs
- Runtime metrics

## Current Branch
`main` (baseline commit created — all Phase 3, 3.5, 3.6 work committed)

## Latest Commit
`845ba49` — "Phase 3 + 3.5 + 3.6: repo/scenario prep, architecture audit, structure remediation"

## Known Risks
1. **LR-2 — No notebook isolation:** `notebooks/` empty; need local vs. Kaggle separation convention.
2. **LR-3 — No test data boundary:** Test fixtures need a defined home outside `inputs/` and `src/`.
3. **LR-4 — Phase boundary confusion:** `src/benchmark/` exists as scaffold; must not be expanded before Phase 4.
4. **LR-5 — Paper vs. implementation drift:** Must document any conflict rather than silently resolving.
5. Full `jupyter` metapackage not installed. Core notebook tools present.
6. Torch/transformers intentionally not installed locally (Kaggle-only).
7. **LR-7 — django CMS and Saleor not yet cloned locally:** Test suite runnability not verified locally beyond manifest documentation.
8. **LR-8 — Scenario content quality:** YAML files generated by automated agents; manual review recommended before Phase 4.

## Exact Next Task
**Phase 4A — Domain Models and Contracts**: Implement immutable data models in `src/benchmark/core/` (enums, models, exceptions, protocols, registry, context) and configuration models in `src/benchmark/config/` (models, loader, validation). No strategy or execution code. Use frozen dataclasses, typed protocols, Pydantic config models. Include unit tests for all models and protocols.

## Handoff Notes
Phase 3.6 is complete. All structural conflicts resolved: stale outer copies deleted, reference docs preserved, all 24 scenario blast_radius values taxonomy-compliant, `.gitignore` deduplicated, baseline commit created. Architecture is frozen with 13 layers, 11 interface protocols, and strict dependency rules. Phase 4 is split into 6 milestones (4A–4F). Phase 4A is authorized but has not started. Do not implement Phase 4A during this session. Do not download or run any LLM locally. Do not modify frozen protocol documents. Do not modify anything under `inputs/`. Canonical project root is `project/` (where `.git` lives). Working tree is clean after commit `845ba49`.

Environment activation:
```bash
conda activate selective-regen-benchmark
```
