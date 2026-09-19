# Strong Localization Competitor / Algorithm Landscape Review (2026-09-19)

**Date:** 2026-09-19
**Mission:** STRONG LOCALIZATION SIGNAL BRIDGE
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**ZERO API** (primary papers + official repositories/model cards only).

External paper numbers in this document are **LITERATURE CONTEXT ONLY**. They
are NOT placed beside our measurements as if directly comparable: our metrics
are file-level P/R/F1/FNR/ORR on our own parent-only real-commit DEVELOPMENT
protocol (djangoCMS DEV 174 + Saleor DEV 149), while the external numbers are
function-level Func@10 / Top-1 / MRR on SWE-Bench-Lite / LocBench / SWE-bench
Verified, computed on entirely different datasets and protocols.

---

## 1. SweRank / SweLoc — VERIFIED (primary: arXiv 2505.07849, ICLR 2026;
official repo github.com/gangiswag/SweRank; model cards Salesforce/SweRankEmbed-*)

| Attribute | Value |
|---|---|
| Localization unit | function (also file-level evaluation in their harness) |
| Retrieval | dense bi-encoder embedding retriever over code snippets |
| Ranking | retriever cosine + optional LLM listwise reranker (SweRankLLM) |
| Specialized training | YES — SweLoc contrastive training (issues ↔ modified functions) |
| Repository history | NO (single-snapshot at PR base commit) |
| Graph | NO |
| Agent loop | NO (single-pass retrieve; optional one-pass rerank) |
| LLM calls | 0 for retriever; 1 (listwise) per query for SweRankLLM rerank |
| Compute/API burden | retriever ≈0 API; reranker = LLM (7B/32B or GPT) per query |
| Languages | Python (SweLoc); multilingual in SweRank+ |
| Benchmark | SWE-Bench-Lite, LocBench (function-level Func@10) |
| Fairly transferable | (a) bi-encoder retriever as a ranking signal; (b) function-level snippet indexing; (c) query prompt `Represent this query for searching relevant code: ` |
| Not comparable | Func@10 on SWE-Bench-Lite vs our file-level F1/ORR on djangoCMS/Saleor |

Model card headline numbers (context only): SWE-Bench-Lite Func@10 —
SweRankEmbed-Small 74.45, +SweRankLLM-Small 86.13; LocBench Func@15 63.39.
Our DEV experiment in this mission is on OUR dataset and MUST NOT be compared
to these.

## 2. SweRank+ — VERIFIED (primary: arXiv 2512.20482, Dec 2025)

| Attribute | Value |
|---|---|
| Localization unit | function (multilingual) |
| Retrieval | SweRankMulti = cross-lingual code embedding retriever + listwise LLM reranker |
| Ranking | retriever → listwise reranker |
| Specialized training | YES — multilingual issue-localization dataset |
| Repository history | NO for SweRankMulti; SweRankAgent adds an agentic search loop with a memory buffer |
| Graph | NO |
| Agent loop | SweRankAgent = iterative multi-turn agentic search with memory |
| LLM calls | reranker + agent turns (multiple) |
| Languages | multiple popular programming languages (Python-centric criticism addressed) |
| Benchmark | multilingual issue-localization benchmarks |
| Fairly transferable | the cross-lingual retriever is a candidate multilingual baseline for Stage 7; the listwise reranker could be evaluated under a budgeted protocol |
| Not comparable | end-to-end agentic numbers are apples-to-oranges vs our single-pass ranking |

**Practical obtainability:** SweRankEmbed-Large / SweRankLLM models are
released on HF under the Salesforce org (CC-BY-NC-4.0 family); SweRank+
specific weights availability should be re-checked at model-card time. Our
mission records: we DID NOT download or run any SweRank+ component.

## 3. LocAgent — VERIFIED (project P5 evidence; pinned upstream 4935b557)

| Attribute | Value |
|---|---|
| Localization unit | file/function (agent walks a repo graph) |
| Retrieval | repository graph + LLM-guided traversal |
| Ranking | LLM reasoning over graph |
| Specialized training | NO (prompted LLM) |
| Repository history | NO (graph built from the snapshot) |
| Graph | YES — repo-level dependency graph |
| Agent loop | YES — iterative traversal with tools |
| LLM calls | many (402 calls / ~$9.93 normalized in our P5 run for 10 tasks) |
| Languages | Python (extensible) |
| Benchmark | SWE-bench family, LocBench |
| Fairly transferable | shared-protocol comparison under matched budget (already done: P5/P5C — F1 0.333 vs Sparse 0.312/Full 0.353 on 10 held-out, 5/10 usable) |
| Not comparable | our 10-task shared-protocol run vs published agentic numbers |

## 4. RepoGraph — VERIFIED (primary: arXiv 2410.14684, ICLR 2025)

| Attribute | Value |
|---|---|
| Localization unit | repository-level code graph for context feeding |
| Retrieval | repo graph + LLM |
| Ranking | LLM over graph context |
| Specialized training | NO |
| Repository history | NO |
| Graph | YES |
| Agent loop | LLM planning over graph |
| LLM calls | multiple |
| Languages | Python primarily |
| Benchmark | SWE-bench family |
| Fairly transferable | graph-structured context feeding ideas (our frozen graph is untyped edges only) |
| Not comparable | its context-feeding numbers vs our single-pass ranker |

## 5. OrcaLoca — VERIFIED (primary: arXiv 2502.00350, ICML 2025)

| Attribute | Value |
|---|---|
| Localization unit | function match rate on SWE-bench-Lite |
| Retrieval | code search + relevance scoring |
| Ranking | priority-based scheduling for LLM-guided action; action decomposition with relevance scoring; distance-aware context pruning |
| Specialized training | NO (LLM agent) |
| Repository history | NO |
| Graph | NO (uses code search / structure) |
| Agent loop | YES — priority-scheduled action search |
| LLM calls | many (agentic) |
| Languages | Python (SWE-bench Lite) |
| Benchmark | SWE-bench Lite (function match 65.33% — open-source SOTA at ICML 2025) |
| Fairly transferable | action-decomposition + priority scheduling ideas for a later agentic stage; relevance scoring over code units |
| Not comparable | function match rate vs our file-level metrics |

## 6. Agentless — VERIFIED (primary: Xia et al. 2024, arXiv:2407.01489)

| Attribute | Value |
|---|---|
| Localization unit | file (localization step) then repair |
| Retrieval | BM25-style + repo file list + test-based re-ranking |
| Ranking | hierarchical: repo → file → class/function via LLM inspection |
| Specialized training | NO |
| Repository history | NO |
| Graph | NO |
| Agent loop | bounded "agentless" pipeline (few deterministic stages) |
| LLM calls | ~2-4 per instance (localize + repair) — far cheaper than agents |
| Languages | Python |
| Benchmark | SWE-bench Lite / Verified |
| Fairly transferable | the localization-first pipeline shape (matches our Sparse → ranked-additions architecture); cheap LLM localization stages |
| Not comparable | its resolution rates vs our ranking metrics |

## 7. Improving Code Localization with Repository Memory — VERIFIED (primary:
arXiv 2510.01003, ICLR 2026)

| Attribute | Value |
|---|---|
| Localization unit | file/function (agent) |
| Retrieval | non-parametric memory over the repo's COMMIT HISTORY: recent historical commits + linked issues + functionality summaries of actively evolving parts (identified via commit patterns) |
| Ranking | retrieval over the memory store |
| Specialized training | NO (non-parametric memory) |
| Repository history | YES — commit history is the core mechanism |
| Graph | NO |
| Agent loop | YES (augments LocAgent) |
| LLM calls | agentic (many) |
| Languages | Python |
| Benchmark | SWE-bench Verified, SWE-bench-live |
| Fairly transferable | **the repository-memory mechanism is DIRECTLY relevant to our Stage-15 feasibility study**: parent-only commit-history memory, linked issue/commit retrieval, module summaries, evolution frequency. It uses exactly the parent-visible historical signals our protocol allows. |
| Not comparable | its SWE-bench numbers vs our ranking metrics |

## 8. CoSIL — VERIFIED (primary: arXiv 2503.22424, ASE 2025)

| Attribute | Value |
|---|---|
| Localization unit | function (Top-1 accuracy) |
| Retrieval | two-phase code-graph search: file-level via dynamically built module call graphs → function-level via function call graphs |
| Ranking | iterative search + pruner to filter unrelated directions/contexts |
| Specialized training | NO training, NO indexing |
| Repository history | NO |
| Graph | YES — dynamic call graphs |
| Agent loop | YES — iterative LLM-driven search with a pruner + reflection mechanism |
| LLM calls | many (Qwen2.5-Coder-32B in paper) |
| Languages | Python |
| Benchmark | SWE-bench Lite (Top-1 43.3%), SWE-bench Verified (44.6%) |
| Fairly transferable | pruner + reflection ideas for a future bounded agentic stage; dynamic call-graph construction |
| Not comparable | Top-1 accuracy vs our file-level metrics |

## 9. Summary positioning for OUR line

| Family | Zero-API? | Specialized training? | History? | Graph? | Agentic? | Verdict for our protocol |
|---|---|---|---|---|---|---|
| SweRankEmbed (retriever) | YES (local) | YES (external) | NO | NO | NO | **TESTED in this mission — PASS (diagnostic)** |
| SweRankLLM reranker | NO (LLM) | YES | NO | NO | NO | next candidate (budgeted) |
| SweRank+ | NO (reranker/agent) | YES | NO | NO | partial | future multilingual baseline |
| LocAgent | NO | NO | NO | YES | YES | shared-protocol comparison done (P5) |
| RepoGraph | NO | NO | NO | YES | YES | graph-context ideas only |
| OrcaLoca | NO | NO | NO | NO | YES | later agentic stage |
| Agentless | NO (cheap LLM) | NO | NO | NO | bounded | pipeline shape aligned |
| Repo-Memory (2510.01003) | depends (history is free) | NO | **YES** | NO | YES | **mechanism for Stage-15 feasibility** |
| CoSIL | NO | NO | YES | YES | YES | later agentic stage |

## 10. SweRank+ cost/compute plan (for option B, if ever chosen)

The official reranker (SweRankLLM-Small, 7B) on top of the embedding
candidates:

- 1 listwise LLM call per task over the top-K embed candidates (K ≈ 10–20).
- Local 7B inference on available hardware is not feasible (30GB RAM / CPU
  only, no GPU); a hosted run would be ~1 call × ~2–4k tokens per task →
  ~323 calls / ~1M tokens for the full DEV population (order-of-magnitude
  estimate; exact pricing depends on provider).
- Under the thesis's ZERO-API discipline this requires a NEW frozen budget +
  explicit authorization; it was NOT executed in this mission.

## 11. Literature ledger update

- New verified entries added to `research/literature/idea_ledger.md` and
  `research/literature/review_matrix.csv`: SweRank (2505.07849), SweRank+
  (2512.20482), OrcaLoca (2502.00350), CoSIL (2503.22424), Repo-Memory
  localization (2510.01003), CommitDistill (2605.18284, repository-memory
  deterministic regex prototype — relevant to Stage-15 feasibility),
  HyperFL (2608.02967, query-adaptive fault-localization embeddings).

## 12. SweRank+ multilingual transfer — how it could be evaluated under OUR protocol

**Practical obtainability (checked 2026-09-19):** under the Salesforce org on
Hugging Face the released models are `SweRankEmbed-Small`, `SweRankEmbed-Large`
(7B), `SweRankLLM-Small` (7B) and `SweRankLLM-Large` (32B). **No SweRank+
specific weights/code were located under that org at audit time** (the
SweRank+ paper arXiv:2512.20482 describes SweRankMulti + SweRankAgent). If the
SweRank+ models are released under a different id/org later, this must be
re-verified from the primary source.

**Multilingual scope:** SweRank+ is Python-centric-critique-motivated and
trained on a multilingual issue-localization dataset. Our OWN method is
currently Python-only (the embed signal is evaluated on djangoCMS/Saleor
Python; the frozen pipeline is Python code-unit extraction). **We do NOT claim
our method supports TypeScript/Java/Go merely because SweRank+ does.**

**How a multilingual transfer could be evaluated under our parent-only
real-commit protocol (frozen design, NOT executed):**
1. Build the per-language DEV datasets (cross-language readiness report:
   NestJS/TypeScript, JabRef/Java, prometheus/Go — parent-only miner, observed
   change-set proxy, `>=60` rule).
2. Index the parent revision of each repo with the SAME code-unit extraction
   + MAX file aggregation adapter (language-appropriate parsers).
3. Query = parent-visible issue intent only (the frozen leakage rule).
4. Evaluate with the SAME metric definitions and paired-task-bootstrap CI at
   B=5, reporting TP/FP/FN/P/R/F1/FNR/ORR.
5. Compare SweRankEmbed (English-issue, Python-trained) against a
   multilingual retriever (SweRank+ or a cross-lingual embed) ONLY as a
   matched-protocol head-to-head — external paper numbers remain context only.
6. Treat any external multilingual model as an EXTERNAL PRETRAINED DIAGNOSTIC
   BASELINE with the same contamination caveat as SweRankEmbed-Small.