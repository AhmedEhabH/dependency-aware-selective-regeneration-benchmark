# OMISSION-RISK DEVELOPMENT INFERENCE — SPARSE-v2 LABEL ANALYSIS (TRAIN/VALIDATION)

**Date:** 2026-09-16
**Protocol:** docs/OMISSION_RISK_DEVELOPMENT_INFERENCE_PROTOCOL.md (frozen, approved)
**Model:** qwen/qwen3-coder (Qwen3-Coder-480B-A35B-Instruct) @ deepinfra/turbo (OpenRouter)
**Assistant model (analysis/execution):** openrouter/deepseek/deepseek-v4-flash-0731
**Branch basis:** main @ `15d1b3f` (clean tree; full-suite green carried from the deterministic milestone).
**Scope:** TRAIN (24) + VALIDATION (6) = 30 tasks; Sparse-v2 ONLY; 3 nested reps = 90 cells.
**HELD_OUT_TEST:** NEVER used in this run (10/10 untouched; access fails closed).

---

## 1. Executive verdict

**The 90-cell Sparse-v2 development-inference run is 90/90 valid at
490,747 total tokens / $0.184 — inside the frozen 600,000-token AND $0.30
hard-stop budget.** The task-level Sparse-v2 `has_fn` label is computable and
has **prevalence 26/30 = 86.7%** (26 positive / 4 negative). **The class-balance
gate FAILED (n_negative=4 < 10)**, so per the frozen protocol **NO multivariable
RiskScorer is fitted** and the analysis is **descriptive / single-feature only**.

On the real Sparse-v2 labels the cheap signals still do **not** separate
omission-risk tasks at n=30: only **3 of 97 features** exceed the random-risk
95% AUROC band (4.85 expected by chance), and all three are the **same
retrieval-peakiness cluster** (bm25_zero_count / bm25_nonzero_frac /
bm25_relthresh_count) whose direction is now **consistent** with the
pre-registered hypothesis (sharply peaked retrieval → more omissions) — a
qualitative change from the deterministic first pass, but **not statistically
above chance**. Sparse–BM25 disagreement (R4) is **anti-predictive (AUROC 0.303,
inside band)**; graph features are inside the band; adaptive-K does not beat
fixed K=10; the cost-sensitive decision analysis shows **always-escalate
dominates** at every C_FN/C_VERIFY ratio. **A RiskScorer v1 is NOT
statistically justified** on this evidence.

---

## 2. Run execution record (90 cells)

| Metric | Value |
|---|---|
| Cells | 90 (30 tasks × 3 reps) |
| Valid / Failed | **90 / 0** (validity 100%) |
| Schema-valid | 90 / 90 |
| Truncations (cap 16384 hit) | 0 |
| Provider-reported provider | DeepInfra × 90 (deepinfra/turbo, fallback OFF) |
| Model identity | openrouter:qwen/qwen3-coder@deepinfra/turbo, fp4 |
| Temperature / cap / graph | 0.0 / 16384 / OFF |
| Prompt tokens | 438,078 (mean 4,867.5 / median 4,861) |
| Completion tokens | 52,669 (mean 585.2 / median 454.5) |
| **Total tokens** | **490,747** (ceiling 600,000 → 81.8% of ceiling) |
| **API cost** | **$0.184088** (ceiling $0.30 → 61.4% of ceiling) |
| Model calls | 90 |
| Raw responses persisted | 90 / 90 with sha256 sidecars (all recomputed match) |
| Latency | mean 6.39 s / max 175.95 s (one long VALIDATE-heavy cell) |

Run evidence: `research/omission-risk-feature-study-v1/sparse_v2_trainval_run_records.jsonl`,
`sparse_v2_trainval_runs/raw/*.txt` + `*.sha256`, `sparse_v2_trainval_manifest.json`,
`sparse_v2_trainval_endpoint_freeze.json`, `sparse_v2_trainval_checkpoint_*.json`,
`sparse_v2_trainval_closure.json`. Closure PASS (token + cost ceilings respected,
no replacement reruns, no result-dependent reruns).

One outlier cell: `omission-djangocms-rc-f2c367ddc7b1-sparse_v2-r2` serialized
121 decisions (117 VALIDATE), completion 14,579 tokens, latency 176 s, cost
$0.016 — valid (finish_reason=stop), within the frozen contract, retained as-is
(no replacement reruns).

---

## 3. Pre-run gates + leakage (all PASS, before the first API call)

`reports/omission_risk_inference_gates.json` + `reports/OMISSION_RISK_INFERENCE_GATES.md`:

| Gate | Result |
|---|---|
| 1 Dataset Validation (TRAIN 24 / VALIDATION 6 only; HELD_OUT fails closed; proxy ⊆ universe) | PASS |
| 2 Prompt/Input Validation (P1 SPARSE contract, prompt-control proof, no proxy markers, ids 1..N) | PASS |
| 3 Pipeline Smoke (1 synthetic case, deterministic mock, zero model calls) | PASS |
| 4 Dry Run (2-case slice, 0 model calls, row-shape contract) | PASS |
| 5 Integration (90-cell manifest, run_records schema, raw+sha256 sidecar contract) | PASS |
| 6 Metric Verification (synthetic TP/FP/FN P/R/F1/FNR, sparse preserve-rejection) | PASS |
| Leakage audit (proxy never in prompt; determinism; task unit; Phase-B Gate A precondition) | PASS |

Phase-B data availability updated post-run (`data_availability.json`):
TRAIN/VALIDATION now `sparse_v2_prediction_available=True`, 3 reps, source
artifact = the run_records.jsonl. Repository evidence capability (Phase-B B–G)
unchanged: graph available (14 features valid), history UNAVAILABLE
(no git cache → history/co-change features remain DEFERRED, not evaluated).

---

## 4. Task-level Sparse-v2 has_fn labels (before fitting)

Label definition (frozen): `has_fn(t) = 1` iff the Sparse-v2 prediction
(REGENERATE write set) omits ≥1 proxy-positive file; pre-registered aggregation
= **any-FN-over-reps**, task-level unit (N=30, not 90).

- **N positive (has_fn=1) = 26** (TRAIN 20, VALIDATION 6)
- **N negative (has_fn=0) = 4** (TRAIN 4, VALIDATION 0)
- **Prevalence = 26/30 = 86.7%** (vs deterministic BM25@10 first pass 73.3%)
- Severity: none 4 / partial 2 / complete 24; FN count 1–8 per task (max 8)
- Rep agreement: 27/30 tasks have all 3 reps agreeing on the label; 3 tasks
  have a mix (all were labeled positive via any-FN).
- Class-balance gate: **min(26,4)=4 < 10 → FAILED** →
  **multivariable RiskScorer NOT fitted**; descriptive/single-feature only.

---

## 5. Single-feature results on the real Sparse-v2 label (N=30)

Random AUROC band (2000 seeds): **[0.183, 0.817]** (radius 0.317) — wider than
the deterministic band because the label is more imbalanced (86.7% prevalence).

**Features above the random 95% band: 3 of 97 (4.85 expected by chance).**

| Feature | AUROC | AUPRC | AUPRC 95% CI | Direction |
|---|---|---|---|---|
| `bm25_zero_count` | **0.837** | 0.965 | [0.888, 1.000] | positive (more zero-score candidates → omission) |
| `bm25_nonzero_frac` | 0.168* | 0.747 | [0.576, 0.981] | anti (low nonzero-fraction → omission) |
| `bm25_relthresh_count` | 0.173* | 0.790 | [0.617, 0.973] | anti (few candidates above 10% top-1 → omission) |

*These are the same retrieval-peakiness cluster: `bm25_zero_count`,
`bm25_nonzero_frac`, `bm25_relthresh_count` are monotonically related. All
three now point in the PRE-REGISTERED direction (a sharply peaked BM25
retrieval — few nonzero-scoring candidates — is associated with MORE Sparse-v2
omissions), unlike the deterministic first pass where the only above-band
feature was anti-correlated.

Top 10 by AUPRC: bm25_zero_count (0.965), intent_hit_frac (0.965), bm25_
concentration_herfindahl (0.964), graph_2hop_frontier_size (0.959),
sparse_bm25_jaccard_k10 (0.937), disagree_jaccard_pt_k10 (0.935),
graph_density (0.930), graph_conn_components (0.913), graph_isolated_count
(0.913), disagree_jaccard_graph_k10 (0.912). **None of these exceed the band**
except the three peakiness features above.

Family summary (mean signed AUROC / max |AUC−0.5|):
- A retrieval uncertainty: 0.399 / 0.337 (bm25_zero_count)
- B sparse-disagreement (deterministic): 0.455 / 0.202
- C graph: 0.501 / 0.298 (graph_2hop_frontier_size)
- E task complexity: 0.423 / 0.284 (intent_hit_frac)
- F sparse-plan density: 0.625 / 0.125 (fp_density — K/N, near-constant)
- G sparse-plan actions (new): 0.427 / 0.048
- H Sparse–BM25 disagreement (new): 0.501 / 0.197

### Newly available Sparse-plan action features (family G) — mostly null
| Feature | AUROC | AUPRC | Direction |
|---|---|---|---|
| fp_regenerate_count | 0.548 | 0.908 | positive (weak) |
| fp_validate_count | 0.240* | 0.819 | anti (more VALIDATE flags → fewer omissions) |
| fp_human_review_count | 0.500 | 0.867 | null (HUMAN_REVIEW never used) |
| fp_preserve_count | 0.394 | 0.871 | null |
| fp_action_entropy | 0.442 | 0.898 | null |
| fp_mean_confidence | 0.365 | 0.859 | null |
| fp_serialized_decision_count | 0.433 | 0.888 | null |
| fp_mean_completion_tokens | 0.490 | 0.903 | null |

No family-G feature exceeds the random band. HUMAN_REVIEW was never emitted by
the model (0 across all cells); VALIDATE was emitted on ~205 serialized
decisions and is (weakly, inside band) anti-correlated with omission — i.e., the
model flags validation boundaries on tasks where it omits fewer files.

---

## 6. Required sub-analyses on the real Sparse-v2 labels

1. **Sparse–BM25 disagreement (R4 = 1 − Jaccard(Sparse write set, BM25@10)):**
   AUROC 0.303 (anti-predictive), inside band. The raw `sparse_bm25_jaccard_k10`
   is positively associated (AUROC 0.697, inside band) — tasks where Sparse-v2
   agrees with BM25@10 are slightly more likely to omit files, the opposite of
   the disagreement-as-risk hypothesis. **Sparse–BM25 disagreement does NOT
   work** as a risk signal on this evidence.
2. **Retrieval uncertainty (family A):** `bm25_zero_count` is the single
   strongest signal and now direction-consistent, but the 3 above-band features
   are one cluster and their count is within the chance expectation.
3. **Adaptive-K:** unchanged from the deterministic run (retrieval-depth rules
   are label-independent). fixed_10 remains the best VALIDATION operating point
   (F1 0.212 / FNR 0.640); adaptive_margin/elbow/entropy do not beat it.
   **Adaptive-K does not help.**
4. **Graph features:** graph available and non-trivial (14 features); none above
   the band (best: graph_2hop_frontier_size AUROC 0.798, inside band).
   **Graph adds no reliable signal.**
5. **History/co-change features:** NOT evaluated — capability invalid (no git
   cache, Phase-B F; cold-start condition).
6. **Risk-coverage / escalation budgets:** top feature (bm25_zero_count)
   recall@20/40/60% = 0.23 / 0.42 / 0.65 vs random ≈ 0.18–0.36 — inside the
   noise envelope. No reliable capture above random.
7. **Cost-sensitivity (VALIDATION n=6, r=C_FN/C_VERIFY ∈ {2..100}):**
   escalation rate = 100% and risky-recall = 100% at every ratio;
   always-escalate cost = 6.0 < never-escalate (17.99 → 899.37). **Always
   escalate dominates** — a risk gate cannot reduce cost because it cannot
   separate the 86.7% high-risk class.
8. **Combination** (frozen equal-weight: retrieval uncertainty + disagreement +
   graph frontier): TRAIN AUROC 0.638, VALIDATION (n=6) AUROC 0.500 — unstable,
   no value.
9. **Calibration (dev-only, n=6 VALIDATION):** Platt Brier 0.028 / ECE 0.167;
   isotonic Brier 0.044 / ECE 0.241. Not meaningful at n=6.

---

## 7. Sparse-v2 vs deterministic first-pass — separated comparison

| Dimension | Deterministic first pass (BM25@K, K_ref=10) | Sparse-v2 (real LLM first pass, this run) |
|---|---|---|
| Label source | metadata-corpus BM25@K selection | Sparse-v2 REGENERATE write set |
| Prevalence | 73.3% | **86.7%** |
| Random band (k10/global) | [0.267, 0.739] | [0.183, 0.817] |
| Features above band | 1 / 83 (anti: bm25_top1_top2_margin) | 3 / 97 (peakiness cluster, now direction-consistent) |
| Chance expectation | ~4.15 | ~4.85 |
| Strongest direction | ANTI (confident retrieval → MORE omissions) | POSITIVE (peaked retrieval → MORE omissions) |
| Sparse–BM25 disagreement | n/a (surrogate: BM25-vs-graph/pt/hybrid) | real, anti-predictive (0.303) |
| Graph | inside band | inside band (best 0.798) |
| Adaptive-K | fixed_10 best | fixed_10 best (unchanged) |
| Cost | always-escalate dominates | always-escalate dominates (unchanged) |
| RiskScorer | not fitted | **not fitted (class-balance gate failed)** |

**Reading:** the real Sparse-v2 first pass omits files MORE often than the
deterministic BM25@10 first pass (86.7% vs 73.3%). The only signal family that
moves is retrieval peakiness, and it is now direction-consistent with the
pre-registered hypothesis; however its above-band count (3) is still below the
4.85 expected by chance, so **no reliable risk signal survives uncertainty at
n=30 with 4 negatives**.

---

## 8. Answers to the mandated report questions

- **90/90 validity/failures:** 90/90 valid, 0 failed, 0 truncations, 90/90 raw persisted+verified.
- **Actual tokens/cost:** 490,747 tokens; $0.184088 (both under the 600,000 / $0.30 hard stop).
- **Sparse-v2 has_fn prevalence:** 26/30 = **86.7%**.
- **Class balance:** 26 positive / 4 negative → **gate FAILED** (neg < 10).
- **Strongest single risk signals:** `bm25_zero_count` (AUROC 0.837, AUPRC 0.965,
  direction-consistent) and its anti-correlated siblings
  `bm25_nonzero_frac` / `bm25_relthresh_count` — one retrieval-peakiness cluster.
- **Does Sparse–BM25 disagreement work?** **No** — R4 AUROC 0.303 (anti-predictive), inside band.
- **Do graph/history add signal?** Graph: **no** (inside band). History: **not evaluated** (no git cache).
- **Does adaptive-K help?** **No** — fixed K=10 remains best.
- **Does any signal survive uncertainty?** **No** — 3 above-band features vs
  4.85 expected by chance; all are one cluster.
- **Is a RiskScorer v1 statistically justified?** **No** — class-balance gate
  failed (4 negatives) AND no signal survives the random band.
- **Exact next recommendation:** (1) keep the Sparse-v2 label as the registered
  development label; (2) do NOT build RiskScorer v1 on n=30/4-negatives;
  (3) the only hypothesis-generating lead is retrieval peakiness → pre-register
  it as the single candidate for a confirmatory, balanced (or negative-enriched)
  corpus; (4) treat always-escalate as the current default (cost analysis);
  (5) any future scorer work requires ≥10 negatives and a fresh confirmatory
  split — HELD_OUT_TEST (10 tasks, 3 reps) is available only for confirmation,
  never for feature selection.

---

## 9. Constraints honored

- No configuration changes after seeing results (manifest/config frozen before run).
- No final RiskScorer trained; no HELD_OUT_TEST used; Saleor not started;
  LocAgent not run; no selective escalation implemented; feature definitions
  unchanged (frozen deterministic set + pre-registered Sparse-plan/BM25-disagreement families).
- Repetitions nested — N = 30 tasks, never 90.
- Independent audit and git/export steps follow in the closure section.

## 10. Artifacts

- Run: `research/omission-risk-feature-study-v1/sparse_v2_trainval_*` (+ runs/raw sidecars)
- Analysis: `research/omission-risk-feature-study-v1/sparse_v2_label_analysis/`
  (sparse_v2_labels.json, feature_table.csv, single_feature_results.json,
  baselines.json, combination.json, calibration.json, cost_sensitive.json,
  adaptive_k.json, random_band.json, comparison.json, summary.json)
- Gates: `reports/omission_risk_inference_gates.json`, `reports/OMISSION_RISK_INFERENCE_GATES.md`
- Phase-B data availability: `research/omission-risk-feature-study-v1/data_availability.json` (updated)