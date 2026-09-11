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
- **Model:** **Qwen3-Coder-480B-A35B-Instruct** (OpenRouter slug
  `qwen/qwen3-coder`) pinned to DeepInfra through OpenRouter,
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

### Historical Qwen3-Coder-480B-A35B-Instruct evidence (frozen, unchanged)

**Qwen3-Coder-480B-A35B-Instruct** (OpenRouter slug `qwen/qwen3-coder`) @
DeepInfra, cap Agent 1024 / ImpactPlan-v1 4096 / ImpactPlan-v2 4096.
Selection-stage correctness on valid cells
(micro-aggregated); token/call/cost totals over ALL cells (valid + failed):

| Model | Study status | Arm | Valid | Trunc. | P | R | F1 | Total tokens | Calls | Cost |
|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3-Coder-480B-A35B-Instruct | Primary | Agent | 25/30 | 0 | 0.6463 | 0.8407 | 0.7308 | 449,792 | 206 | $0.140850 |
| Qwen3-Coder-480B-A35B-Instruct | Primary | ImpactPlan-v1 | 6/30 | 19 | 0.6765 | 0.9200 | 0.7797 | 184,401 | 28 | $0.123298 |
| Qwen3-Coder-480B-A35B-Instruct | Post-hoc/exploratory | ImpactPlan-v2 | 29/30 | 0 | 0.7410 | 0.8655 | 0.7985 | 144,353 | 30 | $0.064634 |

> **ImpactPlan-v2 was a separate post-hoc/exploratory 30-cell study.** It is
> displayed beside the primary arms for descriptive readability only. The rows
> are **not** one preregistered or pooled three-arm experiment.
>
> **Severe missing-data asymmetry:** the v1 headline rests on only **6 valid
> survivor cells** (19 truncations at the 4096 cap + unknown-path / transport /
> harness failures). **No between-arm accuracy claim is made.**

### Cross-Model Robustness Replication (Qwen3-32B)

POST-HOC CROSS-MODEL ROBUSTNESS REPLICATION — same repositories, cases,
treatments, gateway and provider, **different Qwen model**. Model
`qwen/qwen3-32b` @ OpenRouter / DeepInfra (`deepinfra/fp8`), **reasoning
explicitly disabled**, fallback off, temperature 0, cap 4096. 60 cells
(6 scenarios × 2 arms × 5 reps); see
[`reports/QWEN3_32B_CROSSMODEL_PROTOCOL.md`](reports/QWEN3_32B_CROSSMODEL_PROTOCOL.md)
(preregistered before cell 1). Denominators are per-row and **not** merged with
the historical rows above.

| Model | Study status | Arm | Valid | Trunc. | P | R | F1 | Total tokens | Calls | Cost (live) |
|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3-32B | Replication | ImpactPlan-v1 | 2/30 | 24 | 0.0000 | 0.0000 | 0.0000 | 198,979 | 29 | $0.037617 |
| Qwen3-32B | Replication | ImpactPlan-v2 | 21/30 | 6 | 0.3600 | 0.6207 | 0.4557 | 122,273 | 23 | $0.016411 |

> **Directional pattern:** Qwen3-32B v1 (full explicit-policy serialization)
> truncates at the frozen 4096 cap in **24/30** cells — the verbose output does
> not fit the frozen cap; recorded verbatim, no reruns. The sparse v2
> representation remains operational (**21/30 valid**); v2 truncations = **6**
> (S004 r1–r5 and S008 r2 hit the frozen 4096 completion cap,
> `finish_reason=length`; accounting audit 2026-09-11 — see
> [`reports/scientific-stagec-djangocms-qwen3-32b-crossmodel-01/ACCOUNTING_CORRECTION_NOTE.md`](reports/scientific-stagec-djangocms-qwen3-32b-crossmodel-01/ACCOUNTING_CORRECTION_NOTE.md)).
> The directional replication label (`DIRECTIONALLY REPLICATED`) requires only
> (1) v2 validity rate > v1 and (2) v2 truncation rate < v1 — both hold
> (0.700 > 0.067 and 0.200 < 0.800). All
> agreement statistics are **descriptive only**; no equivalence/significance
> or causal claim. Cross-model Sparse-v2 Jaccard agreement (historical
> Qwen3-Coder-480B-A35B-Instruct × new Qwen3-32B, 102 cross-product pairs): mean 0.284, median
> 0.231 — see
> [`reports/QWEN3_32B_CROSSMODEL_AGREEMENT.md`](reports/QWEN3_32B_CROSSMODEL_AGREEMENT.md)
> (+ `.csv`). Verify with
> [`scripts/verify_qwen3_32b_crossmodel_claims.py`](scripts/verify_qwen3_32b_crossmodel_claims.py).
>
> **Call accounting:** all 60 manifest cells issued exactly one API request
> (`requests_issued = 60`). `model_calls` (52 usage-bearing) undercounts the
> 8 failed cells that ran before usage capture was wired in; 7 of those 8 have
> persisted raw responses but their exact provider usage is unrecoverable, and
> 1 (S006 v1 r3) is a transport failure with no response. Details in the
> correction note.

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

## Reproduce the Paper's Headline Results

**NO API KEY REQUIRED.** Recompute every headline manuscript metric directly
from the frozen run evidence:

```bash
python scripts/verify_paper_claims.py
```

The verifier recomputes the primary Agent / ImpactPlan-v1 headline metrics
(valid cells, TP/FP/FN, P/R/F1, tokens, calls, cost), the sparse-v2 metrics
(29/30 valid, 0 truncations, TP/FP/FN = 103/36/16, P/R/F1/FNR, full-recall
18/29), the scenario-004 and scenario-006 observations, the single failed v2
cell, the serialized-record reduction, and verifies the 30/30 sparse raw-response
SHA-256 sidecars. Exit code 0 means the frozen evidence is internally consistent.

Canonical frozen evidence:

- Manifest: [`reports/scientific-stagec-djangocms-impactplan-v2-01/manifest_30.json`](reports/scientific-stagec-djangocms-impactplan-v2-01/manifest_30.json) / [`reports/scientific-stagec-djangocms-study-01/manifest_60.json`](reports/scientific-stagec-djangocms-study-01/manifest_60.json)
- Run records: [`reports/scientific-stagec-djangocms-impactplan-v2-01/run_records.jsonl`](reports/scientific-stagec-djangocms-impactplan-v2-01/run_records.jsonl) / [`reports/scientific-stagec-djangocms-study-01/run_records.jsonl`](reports/scientific-stagec-djangocms-study-01/run_records.jsonl)
- Final metrics: [`reports/scientific-stagec-djangocms-impactplan-v2-01/final_metrics.json`](reports/scientific-stagec-djangocms-impactplan-v2-01/final_metrics.json) / [`reports/scientific-stagec-djangocms-study-01/final_metrics.json`](reports/scientific-stagec-djangocms-study-01/final_metrics.json)
- Raw responses: [`reports/scientific-stagec-djangocms-impactplan-v2-01/runs/raw/`](reports/scientific-stagec-djangocms-impactplan-v2-01/runs/raw/)
- Closure gates: [`reports/scientific-stagec-djangocms-impactplan-v2-01/closure_gates.json`](reports/scientific-stagec-djangocms-impactplan-v2-01/closure_gates.json) / [`reports/scientific-stagec-djangocms-study-01/closure_gates.json`](reports/scientific-stagec-djangocms-study-01/closure_gates.json)
- Claim → evidence map: [`reports/PAPER_CLAIM_EVIDENCE_MAP.md`](reports/PAPER_CLAIM_EVIDENCE_MAP.md)
- V7 audit reconciliation: [`reports/PAPER_V7_AUDIT_RECONCILIATION.md`](reports/PAPER_V7_AUDIT_RECONCILIATION.md)

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