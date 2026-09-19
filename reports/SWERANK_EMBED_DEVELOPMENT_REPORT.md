# SweRankEmbed-Small DEVELOPMENT Report (EXTERNAL PRETRAINED DIAGNOSTIC BASELINE)

**Date:** 2026-09-19  **Tier:** T3  **ZERO API** (API calls = 0, API cost = $0)
**Model:** `Salesforce/SweRankEmbed-Small` revision `745d2a06103a66d3cfa600aa52fc0d3523010daa` (pinned; license CC-BY-NC-4.0)
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731

**Frozen protocol:** `docs/SWERANK_EMBED_BASELINE_PROTOCOL_FROZEN.md` (frozen before any target-aware metric inspection).
**Provenance label:** `TRAINING_PROVENANCE_INSUFFICIENT_TO_RULE_OUT_OVERLAP` → SweRankEmbed-Small is an **EXTERNAL PRETRAINED DIAGNOSTIC BASELINE**, NOT clean unseen generalization (`reports/SWERANK_TRAINING_PROVENANCE_AUDIT.md`).

## 1. Research question

Can a specialized, off-the-shelf issue-localization embedding signal break the current ranking/localization bottleneck on our parent-only real-commit DEVELOPMENT protocol, at near-zero marginal cost, with ZERO paid inference?

## 2. Model + environment (pinned)

| Item | Value |
|---|---|
| Model id | `Salesforce/SweRankEmbed-Small` |
| Pinned revision | `745d2a06103a66d3cfa600aa52fc0d3523010daa` |
| Params / size | 137M bi-encoder; `model.safetensors` 273,474,944 bytes |
| Architecture | NomicBertModel 12L/768H/12heads/8192 ctx; CLS pooling; 768-dim; `trust_remote_code=True` |
| License | CC-BY-NC-4.0 |
| Query prompt | `Represent this query for searching relevant code: ` (`prompt_name="query"`) |
| max_seq_length | 1024 (official SweRank eval default) |
| Python | 3.11 (isolated venv) |
| Packages | torch==2.14.0+cpu, transformers==4.52.4, sentence-transformers==5.7.0, einops==0.8.2, safetensors==0.8.0, numpy==2.4.6, scipy==1.17.1 |
| Compute | local CPU only (12 cores), no GPU |

## 3. Data discipline

- **DEVELOPMENT only**: djangoCMS DEV (174 tasks) + Saleor DEV (149 tasks) — the FULL currently permissible DEV populations (no arbitrary subsample).
- Sealed sets (djangoCMS RESERVE, Saleor INTERNAL_TEST/RESERVE) untouched; spent djangoCMS INTERNAL_TEST unused.
- Gold = observed change-set proxy (evaluation only), identical to the frozen protocol.
- Parent-revision file content materialized via `git show <parent>:<path>` from the read-only local caches: `dist/real-commit-cache/djangocms` and `dist/pilot-repo-cache/saleor`.

## 4. Leakage rules (strict, audited)

- Query = parent-visible issue intent ONLY (same as the existing benchmark); hashed (SHA-256) per task; verified == sha256(intent_text) for a 40-task sample (audit S6).
- Code = production files in the frozen candidate universe at the PARENT revision only.
- Never exposed: child revision, target patch, changed paths, proxy positives, future issue/commit information.
- No target label enters parsing, embeddings, scoring, ranking, or top-K selection.

## 5. Frozen adapter (ONE aggregation rule)

```
score(unit f) = cosine(issue_embedding, code_embedding_f)   # L2-normalized
score(file F) = MAX over score(f) for f in F                # ONE rule only
rank pool    = omitted files (universe minus Sparse write set), desc score, asc path
```

Code units = top-level sync functions + classes (with sync methods inline) + sync methods; whole-file fallback (matches the official SweRank parser; §5 of the frozen protocol).

## 6. Efficiency (recorded)

| Quantity | Value |
|---|---:|
| API calls | **0** |
| API cost | **$0.00** |
| Model load time | 17.59 s |
| Blob materialization (14,807 blobs) | 901.39 s |
| Unit encoding (49,705 distinct units, one-time) | 23907.77 s |
| Per-task scoring (precomputed embeddings) | 32.42 s total (0.10 s/task) |
| Total wall | 24877.09 s |
| Distinct blobs / units | 14807 / 49705 |
| Missing blobs | 0 |
| Embedding cache | 152.7 MB (regenerable, deterministic) |

The 49,705-unit corpus encode dominates the wall time and is a ONE-TIME cost that amortizes over all tasks of a repository state (the same blobs recur). Marginal per-task cost after the corpus is embedded is ~0.1 s (scoring) + ~0.2 s (query encode).

## 7. Main results (pooled file-level; TP/FP/FN/P/R/F1/FNR per arm)

### djangocms DEV (n=174; Sparse baseline F1 0.3177)

| B | Method | ORR | P | R | F1 | FNR | candP | TP | FP | FN |
|---:|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 1 | Frozen Route-B composite (BM25 + graph-neighbor) | 0.0464 | 0.3128 | 0.2801 | 0.2955 | 0.7199 | 0.0977 | 142 | 312 | 365 |
| 1 | BM25 | 0.0459 | 0.3106 | 0.2781 | 0.2934 | 0.7219 | 0.0920 | 141 | 313 | 366 |
| 1 | R1 BM25+RevSupport (context) | 0.0600 | 0.3260 | 0.2919 | 0.3080 | 0.7081 | 0.1322 | 148 | 306 | 359 |
| 1 | SweRankEmbed-Small | 0.1369 | 0.3678 | 0.3294 | 0.3476 | 0.6706 | 0.2414 | 167 | 287 | 340 |
| 3 | Frozen Route-B composite (BM25 + graph-neighbor) | 0.1177 | 0.2095 | 0.3314 | 0.2567 | 0.6686 | 0.0824 | 168 | 634 | 339 |
| 3 | BM25 | 0.1132 | 0.2032 | 0.3215 | 0.2490 | 0.6785 | 0.0728 | 163 | 639 | 344 |
| 3 | R1 BM25+RevSupport (context) | 0.1387 | 0.2232 | 0.3531 | 0.2735 | 0.6469 | 0.1034 | 179 | 623 | 328 |
| 3 | SweRankEmbed-Small | 0.2371 | 0.2606 | 0.4122 | 0.3193 | 0.5878 | 0.1609 | 209 | 593 | 298 |
| 5 | Frozen Route-B composite (BM25 + graph-neighbor) | 0.1633 | 0.1626 | 0.3688 | 0.2257 | 0.6312 | 0.0713 | 187 | 963 | 320 |
| 5 | BM25 | 0.1606 | 0.1583 | 0.3590 | 0.2197 | 0.6410 | 0.0655 | 182 | 968 | 325 |
| 5 | R1 BM25+RevSupport (context) | 0.1972 | 0.1783 | 0.4043 | 0.2474 | 0.5957 | 0.0920 | 205 | 945 | 302 |
| 5 | SweRankEmbed-Small | 0.2908 | 0.2017 | 0.4576 | 0.2800 | 0.5424 | 0.1230 | 232 | 918 | 275 |
| 10 | Frozen Route-B composite (BM25 + graph-neighbor) | 0.2512 | 0.1119 | 0.4458 | 0.1789 | 0.5542 | 0.0580 | 226 | 1794 | 281 |
| 10 | BM25 | 0.2259 | 0.1064 | 0.4241 | 0.1702 | 0.5759 | 0.0517 | 215 | 1805 | 292 |
| 10 | R1 BM25+RevSupport (context) | 0.3057 | 0.1243 | 0.4951 | 0.1987 | 0.5049 | 0.0724 | 251 | 1769 | 256 |
| 10 | SweRankEmbed-Small | 0.3941 | 0.1376 | 0.5483 | 0.2200 | 0.4517 | 0.0879 | 278 | 1742 | 229 |

### saleor DEV (n=149; Sparse baseline F1 0.2605)

| B | Method | ORR | P | R | F1 | FNR | candP | TP | FP | FN |
|---:|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 1 | Frozen Route-B composite (BM25 + graph-neighbor) | 0.0775 | 0.2812 | 0.2650 | 0.2728 | 0.7350 | 0.1678 | 124 | 317 | 344 |
| 1 | BM25 | 0.0724 | 0.2766 | 0.2607 | 0.2684 | 0.7393 | 0.1544 | 122 | 319 | 346 |
| 1 | R1 BM25+RevSupport (context) | 0.0729 | 0.2766 | 0.2607 | 0.2684 | 0.7393 | 0.1544 | 122 | 319 | 346 |
| 1 | SweRankEmbed-Small | 0.1149 | 0.3129 | 0.2949 | 0.3036 | 0.7051 | 0.2617 | 138 | 303 | 330 |
| 3 | Frozen Route-B composite (BM25 + graph-neighbor) | 0.1576 | 0.2097 | 0.3312 | 0.2568 | 0.6688 | 0.1253 | 155 | 584 | 313 |
| 3 | BM25 | 0.1576 | 0.2097 | 0.3312 | 0.2568 | 0.6688 | 0.1253 | 155 | 584 | 313 |
| 3 | R1 BM25+RevSupport (context) | 0.1566 | 0.2097 | 0.3312 | 0.2568 | 0.6688 | 0.1253 | 155 | 584 | 313 |
| 3 | SweRankEmbed-Small | 0.2266 | 0.2476 | 0.3910 | 0.3032 | 0.6090 | 0.1879 | 183 | 556 | 285 |
| 5 | Frozen Route-B composite (BM25 + graph-neighbor) | 0.2369 | 0.1716 | 0.3803 | 0.2365 | 0.6197 | 0.1060 | 178 | 859 | 290 |
| 5 | BM25 | 0.2335 | 0.1697 | 0.3761 | 0.2339 | 0.6239 | 0.1034 | 176 | 861 | 292 |
| 5 | R1 BM25+RevSupport (context) | 0.2171 | 0.1736 | 0.3846 | 0.2392 | 0.6154 | 0.1087 | 180 | 857 | 288 |
| 5 | SweRankEmbed-Small | 0.3266 | 0.2093 | 0.4637 | 0.2884 | 0.5363 | 0.1584 | 217 | 820 | 251 |
| 10 | Frozen Route-B composite (BM25 + graph-neighbor) | 0.3173 | 0.1178 | 0.4487 | 0.1867 | 0.5513 | 0.0745 | 210 | 1572 | 258 |
| 10 | BM25 | 0.3148 | 0.1178 | 0.4487 | 0.1867 | 0.5513 | 0.0745 | 210 | 1572 | 258 |
| 10 | R1 BM25+RevSupport (context) | 0.3168 | 0.1246 | 0.4744 | 0.1973 | 0.5256 | 0.0826 | 222 | 1560 | 246 |
| 10 | SweRankEmbed-Small | 0.4260 | 0.1470 | 0.5598 | 0.2329 | 0.4402 | 0.1094 | 262 | 1520 | 206 |

## 8. Frozen progression gate @B=5 (vs frozen Route-B composite)

| Repo | A F1>B | B Rec≥B−.05 | C FNR≤B+.05 | D Prec | E folds≥3/5 | PASS |
|---|---:|---:|---:|---:|---:|---:|
| djangocms | True (Δ+0.0543) | True (Δ+0.0888) | True (Δ-0.0888) | True (Δ+0.0391) | True [0.61, 0.5, 0.63, 0.4, 0.51] | True |
| saleor | True (Δ+0.0519) | True (Δ+0.0834) | True (Δ-0.0834) | True (Δ+0.0377) | True [0.55, 0.43, 0.38, 0.67, 0.55] | True |

**Decision: `SWERANK_EMBED_PASS`** — the frozen gate (A–E) PASSES on BOTH repositories. Leakage (G), determinism (H) and efficiency (I) are verified by the independent audit (`reports/swerank_independent_audit.json`, 11/11).

### Paired task-bootstrap 95% CIs @B=5 (SweRankEmbed minus Route-B; 10,000 resamples, seed 20260919)

| Repo | Metric | Route-B | SweRank | Δ | CI95 lower | CI95 upper | excludes 0 |
|---|---|--:|--:|--:|--:|--:|:--:|
| djangocms | macro_orr | 0.1633 | 0.2908 | +0.1274 | 0.0684 | 0.1880 | True |
| djangocms | final_precision | 0.1626 | 0.2017 | +0.0391 | 0.0202 | 0.0586 | True |
| djangocms | final_recall | 0.3688 | 0.4576 | +0.0888 | 0.0463 | 0.1329 | True |
| djangocms | final_f1 | 0.2257 | 0.2800 | +0.0543 | 0.0283 | 0.0811 | True |
| djangocms | final_fnr | 0.6312 | 0.5424 | -0.0888 | -0.1329 | -0.0463 | True |
| djangocms | candidate_precision | 0.0713 | 0.1230 | +0.0517 | 0.0264 | 0.0770 | True |
| saleor | macro_orr | 0.2369 | 0.3266 | +0.0897 | 0.0242 | 0.1578 | True |
| saleor | final_precision | 0.1716 | 0.2093 | +0.0376 | 0.0174 | 0.0588 | True |
| saleor | final_recall | 0.3803 | 0.4637 | +0.0833 | 0.0398 | 0.1263 | True |
| saleor | final_f1 | 0.2365 | 0.2884 | +0.0518 | 0.0243 | 0.0800 | True |
| saleor | final_fnr | 0.6197 | 0.5363 | -0.0833 | -0.1263 | -0.0398 | True |
| saleor | candidate_precision | 0.1060 | 0.1584 | +0.0523 | 0.0242 | 0.0819 | True |

## 9. Interpretation

1. **SweRankEmbed-Small improves EVERY metric at EVERY budget on BOTH repositories**, and all six paired-bootstrap CIs at the primary operating point B=5 exclude zero for macro ORR, final P, final R, final F1, final FNR, and candidate precision on BOTH repos. This is the first signal in this research line that realizes the measured ranking/recall headroom (P63/P64) with a single deterministic, zero-API mechanism.
2. **F1 (the primary Impact-Correctness objective) rises** on djangoCMS 0.226→0.280 (+0.054; CI [0.028, 0.081]) and Saleor 0.237→0.288 (+0.052; CI [0.024, 0.080]). Recall rises ~+0.09 and FNR falls ~−0.09 on both repos. Precision also rises (~+0.04 both). The FP tail does NOT grow: candidate precision roughly doubles.
3. **Macro ORR (mechanism diagnostic) rises on both repos** (dc 0.163→0.291; saleor 0.237→0.327) — unlike the bounded semantic family, the embed signal recovers FNs without trading precision/F1.
4. **Efficiency**: 0 API calls, $0, local CPU. One-time corpus encode dominates wall time; marginal per-task cost after indexing is sub-second.
5. **Cross-repo consistency**: the signal transfers from djangoCMS (small, ~150 files/task) to Saleor (large, ~670 files/task), which is the external-validity direction this thesis values.

## 10. What this does NOT mean

- **NOT clean unseen generalization**: `TRAINING_PROVENANCE_INSUFFICIENT_TO_RULE_OUT_OVERLAP` — SweRankEmbed-Small may have seen djangoCMS/Saleor-like code during pretraining. The PASS is a *diagnostic* result on DEVELOPMENT, not a confirmatory claim.
- **NOT a confirmation that reranking (SweRankLLM) helps**: the LLM reranker was NOT run (ZERO API).
- **NOT an end-to-end method**: this is the candidate-ranking signal inside the bounded Sparse + ranked-additions architecture; functional correctness/preservation remain deferred to downstream regeneration.
- **NOT a claim that the generic-Qwen semantic family was wrong to close**: the bounded cheap-semantic family closure (`BOUNDED_CHEAP_SEMANTIC_CLOSED_FOR_NOW`) stands on its own DEVELOPMENT evidence.
- **NOT a head-to-head with external paper numbers**: SWE-Bench-Lite/LocBench Func@10 figures in the model card are literature context only and are NOT comparable to our file-level metrics on our dataset.

## 11. Next scientific step (frozen selection)

Because the frozen gate PASSES on both repos, the embed method is frozen as the candidate-ranking signal. ONE next step is selected (per the frozen protocol §11):

**Chosen: A — use SweRankEmbed-Small as the replacement candidate-ranking signal inside the bounded architecture** (Sparse write set + ranked additions), because it is the direct zero-API continuation of the now-passing signal, needs NO paid inference, and keeps the existing verifier/budget machinery intact.

**Not chosen now: B — official SweRankLLM listwise reranker on top of the embed candidates.** SweRankLLM-Small is a 7B instruction LLM (reranker); running it requires paid inference or a heavy local load, so it needs its own frozen budget and authorization. A cost/compute plan for B is drafted in `reports/STRONG_LOCALIZATION_COMPETITOR_REVIEW_2026-09-19.md` (literature shows SWE-Bench-Lite Func@10 74.45→86.13 with the 7B reranker; expected on our protocol: ~1 LLM call per task over the top-K embed candidates).

Stage 5 confirmatory remains gated until a method is frozen under a fresh confirmatory protocol with explicit authorization.

## 12. Artifacts

- `research/strong-localization-signal/swerank/` — `task_rankings.json`, `metrics.json`, `gate.json`, `efficiency.json`, `model_pin.json`, `blob_manifest.json`, `unit_manifest.json`.
- `reports/swerank_independent_audit.json` + `SWERANK_INDEPENDENT_AUDIT.md` (11/11).
- `docs/SWERANK_EMBED_BASELINE_PROTOCOL_FROZEN.md` (frozen protocol + addendum).
- `reports/SWERANK_TRAINING_PROVENANCE_AUDIT.md` (verdict C).
