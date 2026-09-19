# Impact Declaration — Strong Localization Signal Bridge (T3)

**Date:** 2026-09-19
**Mission:** `STRONG LOCALIZATION SIGNAL BRIDGE` (statistical closure + cross-language readiness)
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**Tier:** **T3** — introduces a NEW evaluation-strategy family / baseline
(`Salesforce/SweRankEmbed-Small`, a specialized issue-localization embedding
signal) plus a descriptive statistical-closure analysis of the frozen Stage-4b
pilot. Requires the six T3 validation gates + independent audit + leakage tests
+ deterministic reproducibility.

---

## 1. Scientific question

The current repository-change-localization line has a measured RANKING
bottleneck (P63/P64): cheap deterministic rankers (BM25, structural counts,
Route-B composite) do not realize the high availability headroom; the bounded
generic-Qwen semantic family (Stage 4 / 4b) is NEGATIVE/FROZEN. This mission
asks ONE new question: **does a fundamentally different, specialized,
issue-localization embedding signal (SweRankEmbed-Small, an external
pretrained bi-encoder) break the ranking/localization bottleneck at near-zero
marginal cost — and if not, what does the accumulated evidence say about the
bounded cheap-semantic family?**

ZERO paid scientific LLM/API spend is authorized. Local off-the-shelf model
inference (SweRankEmbed-Small on CPU) is allowed after licensing / provenance /
environment checks pass. No OpenRouter / Anthropic / OpenAI / Qwen calls.

## 2. Preserved frozen findings (NOT reopened, NOT reinterpreted)

- `CHEAP_RANKING_CLOSED_FOR_NOW` (P64) — immutable.
- `BOUNDED_SEMANTIC_NEGATIVE_FROZEN` (P65) — immutable.
- `PRECISION_SAFE_ACCEPTANCE_FAIL` (P67) — immutable. Stage-4b gate NOT modified.
- Sealed sets: djangoCMS RESERVE, Saleor INTERNAL_TEST, Saleor RESERVE stay
  sealed; spent djangoCMS INTERNAL_TEST never reused for selection.
- The Stage-4b verdict (P67) is NOT changed by the descriptive statistical
  closure; the closure is POST-HOC DESCRIPTIVE DEVELOPMENT ANALYSIS only.

## 3. Affected scientific artifacts (modified / created)

### New scientific evaluation family (T3)
| Artifact | Kind | Role |
|---|---|---|
| `src/benchmark/signal/metrics.py` | NEW module | TP/FP/FN/P/R/F1/FNR/ORR/candidate-precision + paired task bootstrap CI (>=10k resamples, fixed seed, task-level) |
| `src/benchmark/signal/code_units.py` | NEW module | deterministic parent-revision code-unit extraction (official-SweRank-style: top-level functions, classes, methods; whole-file fallback) |
| `src/benchmark/signal/swrank_adapter.py` | NEW module | frozen file-level adapter: score(file)=MAX over code-unit cosine; tie-break path ascending; no target labels |
| `src/benchmark/signal/swerank_model.py` | NEW module | pinned SweRankEmbed-Small loader (revision `745d2a06…`), deterministic embeddings, disk cache |
| `scripts/stage4b_statistical_closure.py` | NEW script | Stage-4b paired-task bootstrap closure (djangoCMS + Saleor @B=5) |
| `scripts/swerank_dev_eval.py` | NEW script | end-to-end DEV evaluation: blob materialization at parent, embedding, ranking, metrics, frozen gate |
| `scripts/swerank_independent_audit.py` | NEW script | independent audit (no imports of the analyzer modules) |
| `tests/unit/test_signal_metrics.py` | NEW tests | synthetic TP/FP/FN verification, P/R/F1/FNR/ORR, bootstrap CI |
| `tests/unit/test_signal_adapter.py` | NEW tests | MAX aggregation, deterministic ranking, tie-break, no-target-label |
| `tests/unit/test_signal_leakage.py` | NEW tests | parent-revision indexing, query hash, no proxy/child/target leakage |
| `tests/unit/test_swerank_pin.py` | NEW tests | fixed model revision + env record |

### Durable outputs (created under `reports/`, `docs/`, `research/`)
- `reports/STAGE4B_STATISTICAL_CLOSURE_2026-09-19.md` + `reports/stage4b_bootstrap_ci.json`
- `reports/STRONG_LOCALIZATION_COMPETITOR_REVIEW_2026-09-19.md`
- `docs/SWERANK_EMBED_BASELINE_PROTOCOL_FROZEN.md`
- `reports/SWERANK_TRAINING_PROVENANCE_AUDIT.md`
- `reports/SWERANK_EMBED_DEVELOPMENT_REPORT.md`
- machine-readable SweRank metrics + bootstrap CI JSONs
- independent audit report + JSON
- `reports/REPOSITORY_MEMORY_FEASIBILITY_2026-09-19.md`
- `reports/CROSS_LANGUAGE_READINESS_2026-09-19.md`
- `reports/POLYGLOT_REPOSITORY_FEASIBILITY_2026-09-19.md`
- `_workspace/active/CLAUDE_LOCALIZATION_BOTTLENECK_REVIEW_PROMPT_2026-09-19.md`
- `research/strong-localization-signal/*` raw evidence

### Documentation (updated)
- `00_CURRENT_RESEARCH_STATE.md` (append CURRENT TRUTH block)
- `PROGRESS.md` (rewrite current task block)
- `DECISIONS.md` (append P68+; preserve all prior decisions)
- `docs/RESEARCH_JOURNEY.md` (append rows)
- `reports/GAP_REDUCTION_ROADMAP.md` (fix stale Stage-4b wording; append Stage-4b statistical closure row)
- `research/literature/idea_ledger.md` + `review_matrix.csv` (competitor refresh)

## 4. Affected implementation components

| Component | Change |
|---|---|
| `src/benchmark/recall/data.py` | READ-ONLY reuse (`load_dev_tasks`, `RecallTask`) — no modification planned |
| `src/benchmark/recall/rankers.py` | READ-ONLY reuse (`rank_composite`, `rank_bm25`, `recovery`) for matched baselines |
| `scripts/route_b_v2_robustness.py` | READ-ONLY reuse (`load_case`, `_load_run`) |
| Local git caches (read-only `git show`) | `dist/real-commit-cache/djangocms` (djangoCMS parents) and `dist/pilot-repo-cache/saleor` (Saleor parents — this also resolves the documented "Saleor parent-visible history cache absent" blocker: full 22,615-commit history IS available locally) |
| Isolated SweRank venv (OUTSIDE repo, temp) | torch-CPU + sentence-transformers + pinned transformers 4.52.x — does NOT touch the project's frozen env |

## 5. Dependencies

- `benchmark.recall.data` (frozen DEV tasks), `scripts.route_b_v2_robustness` (case loader),
  `benchmark.cheap_baselines.*` (tokenizer/corpus reused transitively).
- Local git repos for parent-revision file content (git show — no checkout, no
  working-tree mutation).
- SweRankEmbed-Small from Hugging Face (pinned revision) — CC-BY-NC-4.0
  (non-commercial) license, checked before download/use; isolated venv.
- No new paid LLM/API calls. HF model download is not a paid scientific API.

## 6. Edge cases / boundaries

- Files whose `ast.parse` fails or that have no functions/classes → whole-file
  text = single unit (deterministic).
- Empty universe paths (missing file at parent) → record and exclude with an
  audit trace; never silent.
- Tasks with `n_missed == 0` → ORR contribution 0 (frozen macro convention);
  bootstrap resamples the TASK unit exactly.
- Candidate universe = frozen production-file universe from case bundles;
  tests/vendor/generated excluded by existing dataset protocol (already applied
  in the bundles). No target labels enter parsing/embedding/scoring/ranking.
- Query = parent-visible intent_text ONLY (same as existing benchmark); hashed
  per case for audit. No child revision / target patch / changed paths / proxy
  positives / future commit messages.
- Saleor file content comes from the local full-history repo; provenance
  (origin, anchor commit) recorded in the report.

## 7. Verification plan

1. Ruff on changed Python files; 2. mypy (new production modules);
3. py_compile; 4. git diff --check; 5. targeted pytest (new + affected:
   test_recall_bottleneck, test_quant_ranking_bridge, test_precision_safe_*);
6. full suite only at the final gate if the repo protocol requires it (current
   protocol: affected suites only; full suite known to have 2 pre-existing
   environmental failures); 7. independent audit (no analyzer imports).

## 8. Planned decisions (append-only in DECISIONS.md)

- `BOUNDED_CHEAP_SEMANTIC_CLOSED_FOR_NOW` (if no audit defect found).
- SweRank provenance verdict (A/B/C) + SweRank gate PASS/FAIL recorded as
  independent new decisions after the evidence is in.