# Supervisor Decision Memo

**Date:** 2026-09-11
**Purpose:** decision document for the supervisor. Rows come from separate
studies; denominators are NEVER pooled. Details in the cited reports.

---

## 0. Unified comparison table (MANDATORY)

| Model | Study status | Arm | Valid | Trunc. | P | R | F1 | Total tokens | Calls |
|---|---|---|---|---|---|---|---|---|---|
| Qwen3-Coder-480B-A35B-Instruct | Primary | Agent | 25/30 | 0 | 0.6463 | 0.8407 | 0.7308 | 449,792 | 206 |
| Qwen3-Coder-480B-A35B-Instruct | Primary | ImpactPlan-v1 | 6/30 | 19 | 0.6765 | 0.9200 | 0.7797 | 184,401 | 28 |
| Qwen3-Coder-480B-A35B-Instruct | Post-hoc / exploratory | ImpactPlan-v2 | 29/30 | 0 | 0.7410 | 0.8655 | 0.7985 | 144,353 | 30 |
| Qwen3-32B | Post-hoc cross-model | ImpactPlan-v1 | 2/30 | 24 | 0.0000 | 0.0000 | 0.0000 | >= 198,979 | 30 req (29 usage-known) |
| Qwen3-32B | Post-hoc cross-model | ImpactPlan-v2 | 21/30 | 6 | 0.3600 | 0.6207 | 0.4557 | >= 122,273 | 30 req (23 usage-known) |
| Qwen3-Coder-30B-A3B-Instruct | Post-hoc cross-model / cross-provider | ImpactPlan-v1 | 17/30 | 11 | 0.6567 | 0.8000 | 0.7213 | 162,276 | 30 req (30 usage-known) |
| Qwen3-Coder-30B-A3B-Instruct | Post-hoc cross-model / cross-provider | ImpactPlan-v2 | 28/30 | 0 | 0.5556 | 0.6881 | 0.6148 | >= 138,870 | 30 req (29 usage-known) |

> **Notes.**
> - Rows come from **separate studies**; denominators must not be pooled.
> - The historical **Agent and ImpactPlan-v1 rows are the primary** evidence;
>   historical ImpactPlan-v2 is a separate post-hoc/exploratory study.
> - **Qwen3-32B** is a separate post-hoc cross-model robustness replication
>   (DeepInfra). Its v2 truncation value is the **corrected** value (6, not 0;
>   see `reports/scientific-stagec-djangocms-qwen3-32b-crossmodel-01/ACCOUNTING_CORRECTION_NOTE.md`).
> - **Qwen3-Coder-30B-A3B-Instruct** is a separate post-hoc
>   cross-model / cross-provider robustness replication (SiliconFlow).
> - Unknown usage is represented as a **lower bound** (`>=`), never silently
>   converted to zero. Qwen3-32B tokens are lower bounds (8 usage-unrecoverable
>   cells); 30B v2 tokens are a lower bound (1 transport-failure cell).
> - Full model names / slugs: `docs/MODEL_IDENTITIES.md`. Cost (secondary):
>   historical Agent $0.140850, v1 $0.123298, v2 $0.064634; Qwen3-32B total
>   >= $0.054028; 30B total >= $0.041518 (SiliconFlow live rates).

## 1. Current state in one paragraph

The selection-stage benchmark is complete and audited. The primary djangoCMS
study (Qwen3-Coder-480B-A35B-Instruct, DeepInfra) established sparse
ImpactPlan-v2 / Preserve-by-Omission as an operationally viable representation
(29/30 valid) with selection fidelity P 0.741 / R 0.866 / F1 0.798. A post-hoc
cross-model replication (Qwen3-32B) and a new post-hoc cross-model /
cross-provider coder replication (Qwen3-Coder-30B-A3B-Instruct, SiliconFlow)
were executed (60 cells each). The 30B coder model replicated the directional
validity pattern (v2 28/30 valid, 0 truncations vs v1 17/30, 11 truncations)
descriptively. A dependency-graph audit confirmed the automatic AST graph is
hash-reproducible, and a ONE-DAY graph-evidence ablation is feasible
(GRAPH_ONE_DAY_FEASIBILITY: YES). A real historical-commit benchmark is
recommended to reduce author-created requirement/gold bias.

On 2026-09-12 the **M1A controlled 4096-cap feasibility boundary** was closed
and audited: under the frozen 4096 completion budget and the common
semantic-rich Full-v2/Sparse-v2 schema, the Full-v2 capability probe
terminated at the completion cap (decision id 76) before emitting all 144
required decisions, whereas the Sparse-v2 probe completed (419 completion
tokens) and deterministically reconstructed a valid 144-candidate policy.
This is an operational feasibility boundary — **not** a completed 60-cell
ablation and **not** causal proof that Preserve-by-Omission is superior.
A separately preregistered cap-relaxed study (M1B, completion cap 16384 for
both arms, same schema/prompt design) is planned but NOT run.

## 2. Supervisor options

### OPTION A — Keep the paper centered on sparse impact-plan serialization / Preserve-by-Omission
- **Scientific benefit:** focused mechanism paper on token-efficient sparse
  selection representation.
- **Claim enabled:** sparse representation is operationally viable with
  descriptive selection-fidelity evidence on six curated cases.
- **Remaining limitation:** author-curated cases; no cross-project or
  real-commit evidence; selection-only (no regeneration correctness).
- **Estimated engineering time:** minimal (paper/figures only).
- **Estimated scientific API time:** 0.
- **Estimated API cost:** $0.
- **Risk:** reviewer may question generalization from 6 curated cases.
- **Paper-page impact:** small; keeps scope tight.

### OPTION B — Reconnect to Selective Regeneration + Dependency Graph (30-cell Graph-ON ablation)
- **Scientific benefit:** first controlled step toward the original research
  direction; single-factor graph-evidence ablation.
- **Claim enabled:** descriptive evidence on whether adding automatic
  dependency-graph evidence changes selection behavior (TP/FP/FN changes).
- **Remaining limitation:** still 6 curated cases; exploratory; no downstream
  regeneration evaluation.
- **Estimated engineering time:** ~1 day (driver variant + gates + verifier).
- **Estimated scientific API time:** ~15–30 min.
- **Estimated API cost:** ~$0.07 expected (worst case ~$0.16), historical
  model @ DeepInfra.
- **Risk:** low; but limited generalization value.
- **Paper-page impact:** small-to-moderate (a results section).

### OPTION C — Real historical-commit benchmark (20–30 djangoCMS changes)
- **Scientific benefit:** directly attacks author-created requirement/gold
  bias; stronger external validity for the impact-selection claim.
- **Claim enabled:** impact selection generalizes across independent real
  requirement changes (with OBSERVED CHANGE-SET PROXY as the evaluation set).
- **Remaining limitation:** proxy ground truth is not perfect semantic gold;
  significant construction effort.
- **Estimated engineering time:** ~3–5 days.
- **Estimated scientific API time:** hours (20–30 cells, possibly × arms).
- **Estimated API cost:** low tens of cents per cell at DeepInfra/Qwen3 rates.
- **Risk:** moderate effort; commit-filtering edge cases.
- **Paper-page impact:** moderate-to-large (stronger evaluation section).

### OPTION D — Add Saleor for cross-project external validity
- **Scientific benefit:** a materially different repository strengthens
  cross-project generalization (only if scenarios are real-commit-derived).
- **Claim enabled:** cross-project selection evidence.
- **Remaining limitation:** does not fix manual scenario construction by
  itself; large repo adds engineering cost.
- **Estimated engineering time:** ~2–4 days.
- **Estimated scientific API time:** hours.
- **Estimated API cost:** similar per-cell to djangoCMS.
- **Risk:** medium (Saleor size/complexity).
- **Paper-page impact:** small-to-moderate.

Do NOT decide for the supervisor — see questions below.

## 3. Questions for supervisor

1. What should be the final core research question for the submission?
2. Should the current submission reconnect explicitly to Selective
   Regeneration + Dependency Graph?
3. Should the 30-cell Graph-ON ablation be executed before submission?
4. Is a real historical-commit evaluation required before submission?
5. Is adding Saleor necessary now, or should it remain future work?
6. Should the current sparse-plan paper remain a focused mechanism paper,
   while broader Selective Regeneration becomes the MSc-level continuation?

Do NOT rewrite the manuscript's main claim until supervisor guidance.

## 4. Pointers

- Model identities: `docs/MODEL_IDENTITIES.md`
- **M1A controlled 4096-cap feasibility boundary (2026-09-12):**
  `reports/CONTROLLED_ENCODING_4096_FEASIBILITY_RESULT.md`,
  `research/controlled-encoding-ablation-01/`,
  `scripts/verify_controlled_encoding_4096_claims.py`
- 30B study: `reports/scientific-stagec-djangocms-qwen3-coder-30b-a3b-crossmodel-01/`,
  `reports/QWEN3_CODER_30B_A3B_CROSSMODEL_PROTOCOL.md`
- Qwen3-32B study: `reports/scientific-stagec-djangocms-qwen3-32b-crossmodel-01/`
- Graph readiness: `reports/GRAPH_ONE_DAY_EXPERIMENT_PROTOCOL.md`,
  `reports/SELECTIVE_REGENERATION_GRAPH_RECONNECTION.md`
- Real-commit plan: `reports/REAL_COMMIT_BENCHMARK_PLAN.md`
- Decisions: `reports/MERKLE_HASH_DECISION.md`, `reports/SALEOR_DECISION.md`
- Evidence map: `reports/PAPER_CLAIM_EVIDENCE_MAP.md`
- Handoff: `docs/PAPER_WRITING_HANDOFF.md`