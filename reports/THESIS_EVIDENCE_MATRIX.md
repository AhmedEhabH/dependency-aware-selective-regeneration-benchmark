# Thesis Evidence Matrix

**Dependency-aware selective regeneration benchmark.** This matrix maps each
research claim to its current status, canonical evidence, verifier, coverage,
and remaining threat. It is current-facing and tool-neutral. Evidence links are
relative to the repository root; study dirs referenced below are the frozen
evidence directories.

| # | Research claim | Current status | Canonical evidence | Verifier | Independent data? | Repository coverage | Model coverage | Remaining threat | Next experiment |
|---|---|---|---|---|---|---|---|---|---|
| 1 | The sparse impact-policy representation is representationally equivalent to the full explicit policy (deterministic omitted→PRESERVE reconstruction) | **PROVEN (property check, M1A)** | `research/controlled-encoding-ablation-01/` — representation-equivalence checks 14/14 (`D_s(E_s(π)) == π`, incl. all-PRESERVE, one non-PRESERVE, mixed R/V/H, random, duplicate/unknown/explicit-PRESERVE rejection) | `scripts/verify_controlled_encoding_4096_claims.py` (zero API, 27/27 PASS) | No (internal frozen evidence; property check is deterministic) | Todo + djangoCMS scenario universe (144-candidate map) | Qwen3-Coder-480B-A35B-Instruct (schema-level, model-independent where deterministic) | Equivalence is shown on the frozen candidate map; a different candidate universe could in principle expose edge cases | M2 density stress; then M3 |
| 2 | Under the frozen 4096 completion cap, Full-v2 explicit serialization truncates while Sparse-v2 completes | **COMPLETE / AUDITED (feasibility boundary, NOT a 60-cell ablation)** | `research/controlled-encoding-ablation-01/` — capability probes: Probe A `finish_reason=length`, completion_tokens=4096, truncated at decision 76; Probe B `finish_reason=stop`, completion_tokens=419, decodes 144 | `scripts/verify_controlled_encoding_4096_claims.py` (zero API, 27/27 PASS) | No (single model, single provider, two probes) | 1 scenario (djangoCMS external-validity-004) | Qwen3-Coder-480B-A35B-Instruct @ DeepInfra | Single-scenario, single-model, descriptive; not causal proof that Preserve-by-Omission is superior | M1B closed it under cap-relaxation; M2/M3 for generalization |
| 3 | Sparse-v2 yields a controlled cost reduction vs Full-v2 at equal 100% validity when the completion cap is relaxed (16K, both arms) | **COMPLETE / AUDITED (descriptive; CONTROLLED ENCODING COST EFFECT SUPPORTED)** | `research/controlled-encoding-ablation-16k-01/` — 60/60 cells valid, 0 failed, 0 truncations; Full-v2 mean 8,383 completion / 144 records / P 0.4515 / R 0.7750 / F1 0.5706; Sparse-v2 mean 809 / 4.9 records / P 0.7211 / R 0.8833 / F1 0.7940; reductions completion ≈ −90.35%, records ≈ −96.60%, cost ≈ −82.54%, latency ≈ −63.29% | `scripts/verify_controlled_encoding_16k_claims.py` (zero API, 42/42 PASS) | No (6 curated development/mechanism scenarios × 2 arms × 5 reps, one model/provider) | djangoCMS 5.0.0 (6 scenarios, 144-candidate universe) | Qwen3-Coder-480B-A35B-Instruct @ DeepInfra | Descriptive only; no universal semantic superiority claim; scenario set is curated, not an unbiased sample | M2 serialization-density stress (isolates density); cross-repo/cross-model generalization |
| 4 | Semantic-selection quality is NOT claimed to be superior for the sparse representation (semantic-selection caveat) | **EXPLICIT CAVEAT (positive claim = none)** | `reports/CONTROLLED_ENCODING_16K_RESULT.md`, `reports/CONTROLLED_ENCODING_4096_FEASIBILITY_RESULT.md` — "No universal semantic superiority claim"; M1B arm P/R/F1 reported but not compared causally | n/a (policy statement enforced in reports + verifiers) | n/a | all | all | Risk that a reader over-interprets P/R/F1 differences across arms | Keep the caveat wording in all thesis-facing outputs |
| 5 | S006 is the weakest sparse-v2 case (over-selection + persistent gold misses) | **COMPLETE (observed, frozen)** | Primary djangoCMS study + v2 30-cell study + cross-model replications — scenario 006 `djangocms-external-validity-006`: v2 P ≈ 0.389, R ≈ 0.467, full-recall 0/5 (historical model); S006 weak also for Qwen3-32B and Qwen3-Coder-30B-A3B (P 0.053 / R 0.067 / F1 0.059) | `scripts/verify_paper_claims.py`, `scripts/verify_qwen3_32b_crossmodel_claims.py`, `scripts/verify_qwen3_coder_30b_a3b_crossmodel_claims.py` (all zero API) | No (all internal evidence) | djangoCMS | Qwen3-Coder-480B-A35B-Instruct, Qwen3-32B, Qwen3-Coder-30B-A3B-Instruct | S006 structural weakness may be scenario-specific; cause (over-selection) not fully diagnosed | M3 (graph hints could change S006 behavior); diagnostic of over-selection causes |
| 6 | Graph-assisted selection is not yet tested (graph OFF in all completed selection studies) | **NOT TESTED (explicitly out of scope)** | `reports/NEXT_GRAPH_EXPERIMENT_PROTOCOL_DRAFT.md` (design only); README "Graph-aware v3: FUTURE WORK" | n/a | n/a | djangoCMS (all completed studies graph OFF) | all | No graph evidence of any kind; any graph benefit claim is unsupported | **M3 — Sparse-v2 Graph-OFF vs Graph-Hints (NOT STARTED; next scientific milestone)** |
| 7 | Real-commit evaluation is not yet executed (curated scenarios only) | **NOT EXECUTED** | `reports/REAL_COMMIT_BENCHMARK_PLAN.md`, `research/FINE_TUNING_READINESS.md` (design only) | n/a | n/a | Todo + djangoCMS (curated) | all | Curated scenarios may not represent real historical change distribution | Build RealCommitImpactDataset-v1 (TRAIN/VALIDATION/HELD-OUT TEST); evaluate on held-out test |
| 8 | Fine-tuning for impact selection is not yet executed | **NOT EXECUTED (PLAN ONLY)** | `research/FINE_TUNING_READINESS.md` — training-ready schema + mandatory held-out reservation | n/a | n/a | n/a | n/a | Split leakage; evaluation on training distribution; compute cost | Only after RealCommitImpactDataset-v1 exists; fine-tune on TRAIN, evaluate on HELD-OUT TEST only |
| 9 | End-to-end selective regeneration correctness is not yet established | **NOT ESTABLISHED** | Selection-stage evidence only; historical v1.1 end-to-end Todo study = NO-GO (0/30 functional passes), preserved | `scripts/verify_paper_claims.py` (selection claims only) | No | Todo (v1.1 NO-GO), djangoCMS (selection only) | Qwen3-Coder-480B-A35B-Instruct | Executor/repair/validation machinery confounds; timeouts; evaluator coverage | Pillar 6 bounded end-to-end study (select→regenerate→repair→validate) with hard cost ceiling; not authorized this cycle without supervisor direction |
| 10 | Cross-model directional replication of the sparse-v2 operational advantage | **COMPLETE / AUDITED (descriptive, directional only)** | `reports/scientific-stagec-djangocms-qwen3-32b-crossmodel-01/`, `reports/scientific-stagec-djangocms-qwen3-coder-30b-a3b-crossmodel-01/` (+ AGREEMENT + ACCOUNTING_CORRECTION_NOTE) — both models: v2 validity > v1 and v2 truncation < v1 | `scripts/verify_qwen3_32b_crossmodel_claims.py`, `scripts/verify_qwen3_coder_30b_a3b_crossmodel_claims.py` (zero API) | No | djangoCMS (6 scenarios × 2 arms × 5 reps each) | Qwen3-32B @ DeepInfra; Qwen3-Coder-30B-A3B-Instruct @ SiliconFlow | Directional only; unknown-usage lower bounds; one transport failure; no significance testing | M2/M3; independent third-party replication on separate infrastructure |

## How to read this matrix

- **Current status** uses only the frozen evidence labels. "COMPLETE /
  AUDITED" means the study was executed and independently audited (internal
  artifact-level consistency audit); it does not imply external third-party
  reproducibility.
- **Independent data?** is "No" for every row: all evidence was produced by
  this project. This is a first-party research artifact; external replication
  is an open item for the thesis.
- **Verifier** columns list the zero-API scripts that recompute claims from the
  frozen evidence (exit 0 = internally consistent).
- **Remaining threat / Next experiment** columns are the honest gap statements;
  the roadmap (`docs/MSC_RESEARCH_ROADMAP_2026_2027.md`) expands each into a
  full pillar with success/failure interpretation.

## Related documents

- Roadmap: [`docs/MSC_RESEARCH_ROADMAP_2026_2027.md`](../docs/MSC_RESEARCH_ROADMAP_2026_2027.md)
- Study status summary: [`README.md`](../README.md) (Status table + explicit study
  status block)
- Validity & limitations: [`reports/BENCHMARK_VALIDITY_AND_LIMITATIONS.md`](../reports/BENCHMARK_VALIDITY_AND_LIMITATIONS.md)
- Reproducibility index: [`reports/BENCHMARK_REPRODUCIBILITY_INDEX.md`](../reports/BENCHMARK_REPRODUCIBILITY_INDEX.md)
- Truth matrix: [`reports/RESEARCH_TRUTH_MATRIX.md`](../reports/RESEARCH_TRUTH_MATRIX.md)