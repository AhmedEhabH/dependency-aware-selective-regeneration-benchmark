# SweRankEmbed-Small Baseline Protocol — FROZEN (2026-09-19)

**Tier:** T3 (new evaluation-strategy / baseline family)
**Status:** FROZEN BEFORE outcomes (registration frozen before any model
inference on the DEV populations).
**Mission:** STRONG LOCALIZATION SIGNAL BRIDGE (statistical closure +
cross-language readiness).
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**Scientific spend:** ZERO paid LLM/API calls. API calls = 0, API cost = $0.
Local CPU inference only on a pinned CC-BY-NC-4.0 model.

This protocol defines a NEW method/baseline. It does NOT amend P65/P66/P67 or
any frozen decision. It does NOT reopen Stage 4 or Stage 4b.

---

## 1. Research question

Can a specialized, off-the-shelf issue-localization embedding signal
(`Salesforce/SweRankEmbed-Small`) break the current ranking/localization
bottleneck on OUR parent-only real-commit DEVELOPMENT protocol, at near-zero
marginal cost, without any paid inference?

## 2. Model + environment (pinned)

| Item | Value |
|---|---|
| Model id | `Salesforce/SweRankEmbed-Small` |
| **Pinned revision** | `745d2a06103a66d3cfa600aa52fc0d3523010daa` (main tip, 2025-06-24) — NEVER `main` at runtime |
| Params | 137M (0.1B) bi-encoder |
| Architecture | NomicBertModel (12 layers / 768 hidden / 12 heads / 8192 context), CLS pooling, 768-dim |
| Artifact | `model.safetensors` 273,474,944 bytes; SHA-256 recorded by the run |
| License | CC-BY-NC-4.0 (non-commercial) — checked before download/use |
| Training scope | public Python GitHub repos (top ~11k PyPI; see provenance audit) |
| Interface | `SentenceTransformer(trust_remote_code=True)`; `max_seq_length=1024` (official SweRank eval default) |
| Query prompt | `Represent this query for searching relevant code: ` (applied via `prompt_name="query"`) |
| Packages | sentence-transformers, transformers==4.52.4, torch (CPU), einops, safetensors, numpy, scipy — versions frozen in the venv requirements record |
| Compute | local CPU only (no GPU used) |

## 3. Data discipline

- **DEVELOPMENT ONLY**: djangoCMS DEV (174 tasks) and Saleor DEV (149 tasks),
  the FULL currently permissible DEVELOPMENT populations.
- **SEALED sets stay sealed**: djangoCMS RESERVE, Saleor INTERNAL_TEST, Saleor
  RESERVE. The spent djangoCMS INTERNAL_TEST is never used for any decision.
- Gold = observed change-set proxy (evaluation only), as in the frozen
  protocol.
- External pretraining caveat: because SweLoc training provenance cannot rule
  out overlap (see `reports/SWERANK_TRAINING_PROVENANCE_AUDIT.md`), results are
  labelled **EXTERNAL PRETRAINED DIAGNOSTIC BASELINE**, NOT clean unseen
  generalization.

## 4. Leakage rule (strict)

Only PARENT-visible information is exposed to the model:

- query = the same parent-visible change/issue intent text used by the existing
  benchmark (`intent_text` in the case bundle);
- code = production files in the frozen candidate universe at the PARENT
  revision only (`git show <parent>:<path>`);
- NEVER exposed: child revision, target patch, changed paths, proxy positives,
  future issue/commit information.

Each query input is hashed (SHA-256) for audit. No target label enters
parsing, embeddings, score, ranking, or top-K selection.

## 5. Code units (deterministic)

For every production file in the candidate universe at the parent revision:
parse with `ast.parse` and extract source spans of top-level functions,
classes (including their methods inline), and class methods. If `ast.parse`
fails OR the file yields no units, the whole file text is a single unit.

**Unit-rule clarification (2026-09-19, frozen with the executed run):** the
indexed units are **top-level SYNC functions, classes (with their sync methods
included in the class span), and sync methods** — matching the official SweRank
parser's `function_names` semantics, which excludes `AsyncFunctionDef`. A file
containing ONLY async functions therefore falls back to the whole-file unit.
This rule was explicitly encoded to be independent of the Python-version
`ast.AsyncFunctionDef` subclassing quirk, and it is the rule under which the
DEV evaluation (Section 10 results) was executed.

## 6. Frozen adapter (ONE aggregation rule, frozen before outcomes)

```
score(unit f) = cosine(issue_embedding, code_embedding_f)     # L2-normalized
score(file F) = MAX over score(f) for f in F                  # ONE rule only
```

Rationale (frozen): one strongly relevant symbol should be enough to make the
file suspicious. No mean/top3/weighted alternatives are evaluated.

Tie-break: normalized repository path ascending (identical to the frozen
Route-B tie-break convention).

## 7. Ranking + add-budget mapping (Route-B matched)

- candidate pool = omitted files (universe minus Sparse write set);
- rank pool by `score(file)` descending, path ascending;
- additions at budget B = first B ranked files; final set = write_set ∪
  additions; B ∈ {1, 3, 5, 10}.

This is the "replacement candidate-ranking signal inside our bounded
architecture" shape — the same protocol semantics as the frozen Route-B
composite, so the comparison is apples-to-apples on the same task population.

## 8. Matched baselines (same task population, ZERO API)

| Baseline | Source |
|---|---|
| Sparse first pass | write_set alone (no additions) |
| BM25 | `rank_bm25` (frozen) |
| frozen Route-B composite | `rank_composite` = normalized BM25 + binary graph-neighbor (frozen) |
| best previously frozen cheap structural method (context only) | R1 = BM25 + normalized reverse-seed support (P64) |

The primary matched baseline for the gate is the **frozen Route-B composite**.

## 9. Metrics (definitions used in every relevant report from 2026-09-19 on)

```
Precision            P  = TP / (TP + FP)
Recall               R  = TP / (TP + FN)
False Negative Rate  FNR = FN / (TP + FN) = 1 - R
F1                   F1 = 2TP / (2TP + FP + FN)
Candidate precision  = correct recovered omitted positives / all accepted recovery candidates
ORR per task i       ORR_i = recovered omitted positives_i / omitted positives_i
                        (0 when a task has no omitted positives — frozen macro convention)
Macro ORR            mean_i(ORR_i)
```

Paired task bootstrap (the TASK is the unit): >=10,000 resamples, fixed seed
20260919, CI95 = [q2.5, q97.5] of Delta_b = Metric_SweRank_b - Metric_routeB_b.

Efficiency recorded: model load time, materialization time, encode+rank time,
total runtime, memory (cache bytes), API calls = 0, API cost = $0.

## 10. Frozen progression gate (required on BOTH repositories at B=5)

The primary scientific objective is **file-level Impact Correctness**
(P/R/F1/FNR per the authoritative protocol). ORR is a mechanism diagnostic,
not the sole primary objective.

| Condition | Rule (frozen, conservative) |
|---|---|
| A. F1 direction | `F1(SweRank) > F1(Route-B)` |
| B. Recall non-inferior | `Recall(SweRank) >= Recall(Route-B) - 0.05` (conservative margin: 5 file-level points; rationale: an operating point within 5 pooled-recall points of the frozen baseline is not a material regression at these F1 levels ~0.2-0.4) |
| C. FNR non-inferior | `FNR(SweRank) <= FNR(Route-B) + 0.05` |
| D. Precision | `Precision(SweRank) >= Precision(Route-B)` OR (precision loss <= 0.02 AND F1 gain >= 0.02 AND B holds) |
| E. Folds | >= 3/5 seeded task-grouped folds non-negative on the PRIMARY metric (final F1 delta SweRank - Route-B) |
| F. Uncertainty | paired-bootstrap 95% CIs reported (in the gate output) |
| G. Leakage | zero leakage (audited) |
| H. Determinism | deterministic reproducible ranking (tested) |
| I. Efficiency | substantially below multi-call semantic/agentic localization (0 calls / $0 — recorded) |

Decision: `SWERANK_EMBED_PASS` only if A–E hold on BOTH repositories; else
`SWERANK_EMBED_FAIL` (freeze the negative; no tuning of aggregation, K, query
wording, normalization, or thresholds).

## 11. If PASS

Freeze the method, then select ONE zero-API planned next step:
(A) SweRankEmbed as the replacement candidate-ranking signal inside our
bounded architecture; OR (B) official SweRank listwise reranker on top of the
embedding candidates (cost/compute plan only — NO reranker/API call in this
mission). Stage 5 confirmatory remains gated.

## 12. If FAIL

Freeze the negative. Do NOT tune aggregation/K/query/normalization/threshold.
Rank the next fundamentally different families by scientific justification:
(1) repository-history memory; (2) specialized listwise reranker;
(3) priority/action search (OrcaLoca-style); (4) fair LocAgent/CoSIL agentic
search. Choose ONE, do not execute automatically.

## 13. Addendum — comparator / operating-point clarification (2026-09-19)

This addendum arrived from the mission controller BEFORE any target-aware
SweRank metric was computed or inspected:

- **Primary comparator:** frozen Route-B composite (already §8/§10 above).
  BM25 = secondary cheap retrieval baseline. Sparse first pass and previously
  frozen structural methods (R1) = contextual baselines only. Comparator is
  NOT chosen after seeing SweRank results.
- **Primary operating point:** the frozen ranking curve is evaluated at
  K ∈ {1, 3, 5, 10} (already the case); **K = 5 is the PRIMARY reference
  operating point** for the progression gate (consistent with the benchmark's
  B=5 reporting convention). K = 1, 3, 10 are secondary curve/diagnostic
  points. No K is selected after seeing target labels.
- **Primary scientific decision:** `SweRankEmbed-Small @ K=5` versus
  `Frozen Route-B @ matched B=5` on the SAME eligible task population per
  repository, with the metrics in §9 and paired task-bootstrap 95% CIs.
  Macro ORR remains a mechanism diagnostic, not the sole primary gate.

**Temporal guard record:** no target-aware SweRank result for djangoCMS or
Saleor has been computed or inspected as of the arrival of this addendum. The
only prior computation was a 4-task pipeline smoke test that CRASHED at the
metrics stage (no `metrics.json` / `gate.json` produced) and whose partial
ranking artifacts were deleted without inspection before the full evaluation.
The comparator/K choices above were therefore frozen before any result
inspection and are registered as preregistered.