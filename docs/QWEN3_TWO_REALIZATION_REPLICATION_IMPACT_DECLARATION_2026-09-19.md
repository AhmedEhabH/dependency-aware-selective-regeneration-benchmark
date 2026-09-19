# Impact Declaration — Qwen3 Two-Realization Replication + Full-Score Persistence (T3)

**Date:** 2026-09-19
**Mission:** QWEN3 TWO-REALIZATION REPLICATION + FULL SCORE PERSISTENCE (T3
scientific continuation of the contamination-robustness bridge line).
**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731
**Tier:** **T3** — independent dense-retrieval control evaluated under the
frozen SweRank matched protocol via TWO complete independent realizations of
the hosted Qwen embeddings.
**Status:** WRITTEN BEFORE CALL 1. Live provider price re-verified immediately
before this declaration: DeepInfra serves `qwen/qwen3-embedding-8b` at
**$0.01 / 1M prompt tokens** (pricing.prompt = 0.00000001), context 32,768,
uptime 100%/5m, fallback disabled per request.
**Budget:** cumulative Qwen bridge hard ceiling **$0.50**; expected two
realizations ≈ **$0.4377** (21,882,529 tokens × 2 × $0.01/M); prior technical
probes ≈ $0.023 already spent.

---

## 1. Scientific question (unchanged by this amendment)

"Does an independently pretrained, code-capable dense embedding model reproduce
the direction and magnitude of SweRankEmbed-Small's DEVELOPMENT ranking /
omission-recovery signal under the EXACT same parent-only file-localization
protocol?" This is the contamination-robustness CONTROL question — not a
competition to find a new winner, not a Stage-5 execution, not an opening of
sealed data.

## 2. Why this mission exists (the determinism STOP is preserved)

P73 (2026-09-19) remains a VALID historical technical finding: the hosted
endpoint is nondeterministic at ~1e-4 cosine (normal hosted float noise), and
that noise CAN flip a B=5 file set on a task with a near-tie (1/5 sampled
djangoCMS DEV tasks). The strict bitwise/determinism STOP was correct under the
then-frozen probe criterion.

**Protocol amendment (append-only; recorded in DECISIONS.md before any
target-aware Qwen P/R/F1 inspection):** this mission does NOT require hosted
floating-point outputs to be bit-identical. Instead it evaluates
**CONCLUSION REPRODUCIBILITY** by running **TWO complete independent
realizations** (A and B) of the full DEVELOPMENT embedding population under the
same frozen model/provider/settings, analyzing each realization separately
(no averaging, no cherry-picking, no combined metrics). The frozen matched
protocol (parent-only state, same universe, same extraction, same query text,
same MAX-file aggregation, same path tie-break, B=5 primary, Route-B
comparator, same metrics, same paired task bootstrap) is unchanged.

## 3. Affected artifacts

| Category | Artifact | Kind | Role |
|---|---|---|---|
| A. Scientific replication outputs | `research/contamination-bridge/qwen_embed/realization_a/` + `realization_b/` (task_rankings, metrics, gate, ci, ledger) | NEW | Qwen A / Qwen B DEV metrics + paired-bootstrap CIs + frozen replication gate (per realization) |
| A. Scientific replication outputs | `reports/QWEN3_TWO_REALIZATION_REPLICATION_REPORT_2026-09-19.md` | NEW report | human-readable A/B tables, verdict, reproducibility analysis, interpretation |
| A. Scientific replication outputs | `reports/qwen3_two_realization_{metrics,gate,reproducibility,audit}.json` | NEW evidence | machine-readable per-realization metrics, gate, A-vs-B analysis, independent audit |
| B. Engineering-only full-score persistence | `research/contamination-bridge/qwen_embed/full_scores/realization_{a,b}.parquet` | NEW artifact | per-file dense score/rank table (label-free; for the FUTURE calibrated ADD+DROP study only) |
| C. Human-readable documentation | `00_CURRENT_RESEARCH_STATE.md`, `PROGRESS.md`, `DECISIONS.md`, cheatsheet, oracle-gap explainer | UPDATED | truthful closure state; append-only decision + amendment |
| C. Human-readable documentation | `docs/QWEN3_TWO_REALIZATION_REPLICATION_IMPACT_DECLARATION_2026-09-19.md` | NEW doc | this declaration |

## 4. Affected implementation components

| Component | Change |
|---|---|
| `src/benchmark/signal/or_embeddings.py` | READ-ONLY reuse (frozen client: pinned model, DeepInfra, no fallback, batch 64, transport retry, cost ledger, sealed guard) |
| `src/benchmark/signal/{code_units,metrics,swrank_adapter}.py` | READ-ONLY reuse (frozen DEV pipeline) |
| `src/benchmark/recall/{data,rankers}.py`, `scripts/route_b_v2_robustness.py` | READ-ONLY reuse (task loading, Route-B composite, BM25, load_case) |
| `research/strong-localization-signal/swerank/*.json` | READ-ONLY (frozen SweRank DEV results untouched) |
| NEW `scripts/qwen3_two_realization_run.py` | NEW runner: two independent full realizations + full-file-score persistence (Parquet) + per-realization metrics/CI/gate + A-vs-B reproducibility |
| NEW `tests/unit/test_qwen3_two_realization.py` | NEW tests for the runner's deterministic, label-free, budget-guarded parts |

## 5. Boundaries (frozen, unchanged)

- **DEVELOPMENT only:** djangoCMS DEV 174 + Saleor DEV 149. No subsampling.
- **SEALED SETS NEVER OPENED:** djangoCMS RESERVE (59), Saleor INTERNAL_TEST
  (80), Saleor RESERVE (1086), spent djangoCMS INTERNAL_TEST (80). No sealed
  outcome is read. **Stage 5 is NOT executed.**
- **Model/provider:** ONLY `qwen/qwen3-embedding-8b` @ DeepInfra; fallback
  disabled; NO provider switch based on results; NO other embedding model.
- **No Jina / BGE-M3 / Qwen 4B / 0.6B / other providers / LocAgent /
  Agentless / NestJS / JabRef / Prometheus / Grafana.**
- **Do NOT tune B or query wording.** B={1,3,5,10} reported from the SAME
  ranking for diagnosis; B=5 is the preregistered primary point.
- **No calibrated set selection now.** CALIBRATED_SET_SELECTION_V1 is a DRAFT
  only.
- The full-file-score table is an ENGINEERING artifact for a future DEV-only
  study; it does NOT alter the primary Qwen scientific result; it contains NO
  target labels (evaluation joins labels only after ranking is frozen).

## 6. Storage discipline

- All embedding caches / model caches / transient batches → **E:** drive
  (outside the repository). NO raw embedding vectors are committed to Git.
- The LIGHT export stays ≤ 50 MB if scientifically possible; full-file-score
  Parquet tables are compressed; no nested ZIPs, no `.git`, no model caches,
  no venvs, no downloaded external repos inside the export.

## 7. Verification plan (per the validation order)

1. `git diff --check`; 2. ruff on changed Python; 3. mypy on changed
production Python; 4. py_compile; 5. targeted pytest; 6. independent audit
(recomputes metrics/CI/gate/reproducibility from raw artifacts without
importing the analyzer); 7. state docs updated truthfully; 8. commit/merge/
push/tag + HEAD==origin/main + clean tree + TRUE LIGHT export + STOP report.

## 8. Planned decisions (append-only)

- **P74** — protocol amendment: two independent realizations replace the
  bitwise determinism requirement for the Qwen bridge conclusion
  (recorded BEFORE target-aware Qwen P/R/F1 inspection).
- **P75** — Qwen bridge budget freeze v2: cumulative ceiling $0.50;
  expected $0.4377 for A+B (live $0.01/M re-verified); fail-closed projection
  guard (STOP before exceeding $0.50 cumulative).
- **P76+** — the bridge verdict label
  (`INDEPENDENT_DENSE_RETRIEVAL_REPLICATED` only if A and B BOTH pass on
  djangoCMS AND Saleor @B=5; else
  `INDEPENDENT_DENSE_RETRIEVAL_REPRODUCIBILITY_INCONCLUSIVE`).