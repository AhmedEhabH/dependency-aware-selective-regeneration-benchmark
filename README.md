# Repository-Level LLM Impact Selection Benchmark

> The repository slug is retained for historical/link stability.
> The completed djangoCMS studies are selection-only and did not inject
> dependency-graph assistance.

> Research infrastructure for the working paper
> **Provisional working title: "The Cost of Saying 'Unchanged': Sparse Impact Plans for Token-Efficient Repository-Level Impact Selection"**

---

## Status

| Item | Value |
|---|---|
| **Benchmark** | **COMPLETE** |
| **Release** | `v0.11.0-benchmark-complete` |
| **Current phase** | **Paper / figures / supervisor review** |
| **Scientific runs remaining** | **ZERO** |
| Saleor | FUTURE WORK / NOT CURRENT |
| Graph-aware v3 | FUTURE WORK |
| Fine-tuning | FUTURE WORK |
| djangoCMS ImpactPlan-v2 study | POST-HOC / EXPLORATORY |

The selection-stage benchmark research is **closed and audited** (external
GPT-5.6 Sol audit PASS, 2026-09-08). The benchmark tag means the benchmark
research is complete and frozen — it does **not** mean successful end-to-end
executor regeneration. No further scientific model calls, experiments, or
benchmark runs are planned. The current task is academic-output preparation.

---

## What Is This?

A research-grade benchmark for **repository-level LLM impact selection** in
software evolution. Given a requirement change, the completed benchmark
evaluates which repository artifacts the model predicts must change and the
inference efficiency of that selection process.

The frozen protocol prioritizes **impact correctness before efficiency**:
token savings are not a success if the approach misses affected artifacts.
Selective regeneration is the broader motivation and future direction, not a
completed end-to-end measured result of these studies.

## What Was Evaluated?

- **Repositories:** controlled Django Todo (small), django CMS 5.0.0 (medium),
  and Saleor Core 3.23.0 (large — defined but **not executed**).
- **COMPLETED DJANGOCMS SCOPE: SELECTION ONLY** — which repository paths the
  model predicts must change, scored against source-adjudicated hidden gold
  applied after inference.
- **Not measured in the completed djangoCMS treatments:** Functional
  Correctness, Preservation, Architecture Compliance, or end-to-end
  regeneration correctness.
- **Treatment arms:** `iterative_repository_agent` (Agent) vs
  `impact_plan` (ImpactPlan-v1, full explicit plan serialization).
- **ImpactPlan-v2 (post-hoc / exploratory):** a sparse representation redesign
  (explicit non-PRESERVE decisions + deterministic PRESERVE-by-omission).
- **Model:** `qwen/qwen3-coder` pinned to DeepInfra through OpenRouter,
  fallback OFF, temperature 0.

## What Is Finished?

- The Todo selection component studies (smoke + held-out).
- The primary djangoCMS selection study (60 cells).
- The post-hoc / exploratory djangoCMS ImpactPlan-v2 study (30 cells), audited.
- All closure gates, evidence freezing, the audited v2 study tag, and the final
  benchmark tag `v0.11.0-benchmark-complete`.
- A documentation package that lets a fresh researcher start the paper phase
  without reconstructing earlier sessions — see
  [`docs/PAPER_WRITING_HANDOFF.md`](docs/PAPER_WRITING_HANDOFF.md).

## Headline Results

### Primary djangoCMS study (`scientific-stagec-djangocms-01`, 60 cells)

Selection-stage correctness on valid cells (micro-aggregated), model
`qwen/qwen3-coder` @ DeepInfra, cap Agent 1024 / ImpactPlan-v1 4096:

| Arm | Valid / 30 | Precision | Recall | F1 | Tokens (all-cell) | Calls (all-cell) | Recorded cost |
|---|---|---|---|---|---|---|---|
| iterative_repository_agent | 25 | 0.6463 | 0.8407 | 0.7308 | 449,792 | 206 | $0.140850 |
| impact_plan (v1) | 6 | 0.6765 | 0.9200 | 0.7797 | 184,401 | 28 | $0.123298 |

> **Severe missing-data asymmetry:** the v1 headline rests on only **6 valid
> survivor cells** (19 truncations at the 4096 cap + 3 unknown-path + 1
> provider-429 + 1 harness defect). **No between-arm accuracy claim is made.**

### djangoCMS ImpactPlan-v2 study (`scientific-stagec-djangocms-impactplan-v2-01`, 30 cells)

**POST-HOC / EXPLORATORY** — a distinct 30-cell redesign study, **not** a
preregistered arm of the primary study and **not** pooled with it.

| Metric | Value |
|---|---|
| Recorded / Valid / Failed | 30 / 29 / 1 |
| Truncations | 0 |
| TP / FP / FN | 103 / 36 / 16 |
| Precision | 0.741007 |
| Recall | 0.865546 |
| F1 | 0.798450 |
| FNR | 0.134454 |
| Full-recall rate | 18 / 29 = 0.620690 |
| Total tokens / calls / recorded cost | 144,353 / 30 / $0.064634 |

Same-cap observation (scenario 004, cap 4096): historical ImpactPlan-v1
**5/5 truncated**; ImpactPlan-v2 **5/5 completed** (874–1,525 completion
tokens). This proves the frozen v2 representation redesign resolves the
observed **scenario-004 output-serialization bottleneck** — feasibility /
mechanism evidence only, **not** an accuracy claim or a universal scaling law.

### Todo component studies (frozen, selection-stage)

- Stage-C smoke: 30/30 valid, full recall 15/15 per arm, P/R/F1 ceiling.
- Stage-C held-out: 60/60 valid, recall 30/30 per arm, precision Agent 0.8778
  vs ImpactPlan 0.7694; ImpactPlan tokens −72.98%, calls −86.36%.
- v1.1 end-to-end Todo study: **0/30 functional passes (NO-GO)** — preserved
  as historical evidence; the failures were dominated by downstream
  exact-patch / source-validity classes, not the impact selector.

## Known Limitations

1. **Scenario 006 is the weakest v2 case:** precision ≈ 0.389, recall ≈ 0.467,
   full-recall 0/5. The model consistently missed gold files
   (`cms/models/pluginmodel.py`, `cms/admin/placeholderadmin.py`,
   `cms/utils/plugins.py`) and over-selected.
2. **The djangoCMS dependency graph was NOT injected** into ImpactPlan-v1 or
   v2. The primary djangoCMS study characterizes explicit-plan selection
   **without dependency-graph assistance**.
3. **The primary v1 valid-run correctness rests on only 6 valid cells**
   (severe missing-data asymmetry vs Agent's 25). Any v1-vs-Agent comparison
   is provisional.
4. **v2 solves the observed output-serialization bottleneck, but does NOT
   solve impact identification universally** — scenario 006 demonstrates
   residual correctness limits.
5. **v2 still exposes the candidate universe in the prompt.** Larger-repository
   input scaling remains Future Work. No measured repository-size threshold is
   claimed, and **no Saleor feasibility is claimed** (Saleor was not started).

## Final Reports

| Report | Path |
|---|---|
| Final benchmark results | [`reports/FINAL_BENCHMARK_RESULTS.md`](reports/FINAL_BENCHMARK_RESULTS.md) (+ `.csv`) |
| Validity and limitations | [`reports/BENCHMARK_VALIDITY_AND_LIMITATIONS.md`](reports/BENCHMARK_VALIDITY_AND_LIMITATIONS.md) |
| Reproducibility index | [`reports/BENCHMARK_REPRODUCIBILITY_INDEX.md`](reports/BENCHMARK_REPRODUCIBILITY_INDEX.md) |
| Cross-repo synthesis | [`reports/CROSS_REPO_SYNTHESIS.md`](reports/CROSS_REPO_SYNTHESIS.md) |
| ImpactPlan-v2 results | [`reports/DJANGOCMS_IMPACTPLAN_V2_RESULTS.md`](reports/DJANGOCMS_IMPACTPLAN_V2_RESULTS.md) (+ `.csv`) |
| ImpactPlan-v2 design | [`reports/DJANGOCMS_IMPACTPLAN_V2_DESIGN.md`](reports/DJANGOCMS_IMPACTPLAN_V2_DESIGN.md) |
| Paper-writing handoff | [`docs/PAPER_WRITING_HANDOFF.md`](docs/PAPER_WRITING_HANDOFF.md) |

Historical engineering records (the earlier deployment / execution phases) are
preserved in the Git history, `reports/`, and `DECISION_LOG.md`; they are
historical and do not describe current work.

## Quickstart (no API key required)

Reproduce the deterministic smoke-profile dry run (mock backend — zero model
calls, zero tokens, no frozen evidence touched):

```bash
python seven_arm_benchmark.py --dry-run --profile smoke
```

Expected output: a deterministic dry-run report showing planned runs, terminal
status, `dry-run:mock` model identity, and zero model calls / zero tokens.
No API key, GPU, or model download is required.

## Reproducibility

Each research run preserves protocol version, repository and commit, scenario
and strategy, model/backend identity, generation parameters, prompt and content
hashes, token usage, model-call counts, timing, failure classification, and
environment metadata. Raw evidence is persisted append-only and hashed. See
[`docs/REPRODUCIBILITY_PROTOCOL.md`](docs/REPRODUCIBILITY_PROTOCOL.md) and
[`reports/BENCHMARK_REPRODUCIBILITY_INDEX.md`](reports/BENCHMARK_REPRODUCIBILITY_INDEX.md).

## Repository Layout

```text
.
├── benchmark_data/       # Public manifests, profiles, and scenario definitions
├── docs/                 # Frozen protocol, architecture, and handoff documentation
├── notebooks/            # Local execution notebook adapters
├── reports/              # Evidence, results, validity, and audit reports
├── scripts/              # Validation, study-execution, and packaging utilities
├── src/benchmark/        # Source: config, core, execution, llm, repositories, scenarios
├── tests/                # Unit, contract, integration, and isolation tests
├── seven_arm_benchmark.py  # CLI entry point (dry-run supported, no API key)
└── CITATION.cff          # Citation metadata
```

The canonical project map is [`docs/PROJECT_STRUCTURE_MAP.md`](docs/PROJECT_STRUCTURE_MAP.md).

## Working Paper

**Provisional working title:** *The Cost of Saying "Unchanged": Sparse Impact
Plans for Token-Efficient Repository-Level Impact Selection*

**Status:** Benchmark complete; manuscript in preparation
(paper / figures / supervisor review).

The frozen protocol is in
[`docs/FINAL_RESEARCH_PROTOCOL.md`](docs/FINAL_RESEARCH_PROTOCOL.md); current
state and next actions for the paper phase are in
[`docs/PAPER_WRITING_HANDOFF.md`](docs/PAPER_WRITING_HANDOFF.md).

## License

Original benchmark source code is licensed under the [MIT License](LICENSE).
Third-party repositories, dependencies, model assets, and derived materials
remain governed by their original licenses.

## Citation

See [`CITATION.cff`](CITATION.cff) (benchmark version 0.11.0).

## Author

**Ahmed Ehab** — GitHub: [AhmedEhabH](https://github.com/AhmedEhabH)