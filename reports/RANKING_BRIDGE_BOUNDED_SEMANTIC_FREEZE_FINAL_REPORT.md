# Ranking Bridge + Bounded Semantic Freeze — FINAL REPORT

**Date:** 2026-09-18
**Mission:** OPENCODE_RANKING_BRIDGE_AND_BOUNDED_SEMANTIC_FREEZE_2026-09-18
**Status:** DEVELOPMENT only — COMPLETE; ZERO new model/API calls; sealed sets untouched
**Verdict:** **CHEAP_RANKING_CLOSED_FOR_NOW** (quantitative-structural ranking bridge
negative frozen); bounded semantic rerank/verify protocol + API budget **PREPARED,
NOT EXECUTED**
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731

---

## 1. Exact model

`openrouter/deepseek/deepseek-v4-flash-0731` (analysis authoring). ZERO new
scientific model/API calls; every result is a deterministic Python computation
over frozen records + case bundles (Tier T3).

## 2. Ranking-gap reconfirmation freeze (Section 1)

On djangoCMS DEV (174) + Saleor DEV (149), recomputed and frozen (all
verification flags PASS; `reports/fn_quant_ranking_bridge_baseline_freeze.json`):

| Quantity | djangoCMS | Saleor | Frozen |
|---|---:|---:|---:|
| Sparse F1 | 0.318 | 0.261 | 0.3177 / 0.2605 |
| Route-B composite macro ORR @{1,3,5,10} | 0.046 / 0.118 / 0.163 / 0.251 | 0.077 / 0.158 / 0.237 / 0.317 | EXACT |
| BM25-only ORR @5 | 0.161 | 0.234 | OK |
| reverse-1hop oracle availability @K=5 | 0.558 | 0.724 | OK |
| consumer+provider availability @K=5 | 0.605 | 0.802 | OK |
| UNION_ALL availability @K=5 | 0.725 | 0.870 | OK |
| Oracle-Add F1 @B=5 | 0.841 | 0.782 | OK |
| oracle-reviewer (Route-B) F1 @B=5 | 0.441 | 0.424 | OK |

The key diagnosis is verified: Route-B B=5 ORR ≈ 0.163/0.237; reverse-1hop
consumer pool ≈ 0.558/0.724 of FNs at K=5 oracle; UNION_ALL ≈ 0.725/0.870;
dominant remaining loss = ORDERING/RANKING inside an already useful pool.

## 3. The three (or fewer) quantitative-structural rankers (Section 2)

EXACTLY three transparent formulas, frozen BEFORE outcome inspection, all
parent-visible inference-time features (documented in
`src/benchmark/recall/quant_rankers.py`):

| ID | Formula | Feature provenance |
|---|---|---|
| R1 BM25+RevSupport | bm25 + rev_norm | bm25 + normalized count of distinct seeds the candidate consumes (downstream) |
| R2 BM25+BidirSupport | bm25 + rev_norm + fwd_norm | + normalized count of distinct seeds that import the candidate (upstream) |
| R3 BM25+BidirNorm | bm25 + bidir_norm | single combined bidirectional normalized term |

Typed-edge support is NOT available (the frozen dependency graph exposes only
untyped `[src,dest]` edges — verified in `dependency_graph.json`), so no
formula uses a typed edge; provenance recorded, no hidden proxy, no repository
identity, no learned weights, no future state.

## 4. Matched-budget results (B=5 reference)

| Ranker | djangoCMS ORR | Δ vs Route-B | Saleor ORR | Δ vs Route-B | dc folds+ | sc folds+ |
|---|---:|---:|---:|---:|---:|---:|
| Route-B (frozen) | 0.163 | — | 0.237 | — | — | — |
| BM25-only | 0.161 | −0.002 | 0.234 | −0.003 | — | — |
| R1 BM25+RevSupport | **0.197** | **+0.034** | 0.217 | −0.020 | 2/5 | 0/5 |
| R2 BM25+BidirSupport | 0.193 | +0.030 | 0.217 | −0.020 | 1/5 | 0/5 |
| R3 BM25+BidirNorm | 0.185 | +0.022 | 0.209 | −0.028 | 0/5 | 0/5 |

- **Unique recovered FNs beyond Route-B @B=5:** R1 38/30, R2 29/31, R3 22/20
  (small, mirroring the ADD-queue finding).
- **Candidate precision @B=5:** R1 0.092/0.109 vs Route-B 0.081/0.100 — no
  material change.
- **Naive union F1 @B=5:** R1 0.247/0.239 vs Route-B 0.226/0.236 — R1 is not
  clearly worse (c3 PASS).
- **Oracle-reviewer F1 @B=5:** R1 0.473/0.428 vs Route-B 0.441/0.424 — small
  positive on djangoCMS only.
- **Artifact check:** all rankers artifact-free (|corr| < 0.4) on both repos.
- **Deterministic compute cost:** microsecond-level per task (no IO).

## 5. Cheap-ranker gate decision

**`CHEAP_RANKING_CLOSED_FOR_NOW`** (negative frozen; NOT `QUANT_STRUCTURAL_RANKER_READY`,
NOT `BLOCKED_BY_DATA`).

Gate result per formula (all FAIL):
| Ranker | c1 ORR>+0.05 both | c2 folds both | c3 naive-F1 ok | c4 artifact-free | c5 no-leak | c6 simpler |
|---|---:|---:|---:|---:|---:|---:|
| R1 | F | F | T | T | T | T |
| R2 | F | F | T | T | T | T |
| R3 | F | F | T | T | T | T |

The strongest formula (R1) helps djangoCMS (+0.034) but hurts Saleor (−0.020)
and is not fold-positive; no formula materially improves matched-budget ORR over
Route-B on BOTH repos. **No fourth formula was invented in this mission.**

## 6. Bounded semantic expansion — frozen design (Section 3, NOT executed)

`docs/BOUNDED_SEMANTIC_RERANK_VERIFY_PROTOCOL_FROZEN.md`:
- Middle layer, NOT a full repository agent; reuses the EXISTING verifier
  protocol (`docs/ROUTE_B_VERIFIER_PILOT_PROTOCOL.md`).
- Pool: Route-B top-10 ∪ reverse-1hop downstream-consumer pool, deduped,
  deterministic pre-order, **hard pool cap C=40**; forward-provider pool
  excluded by default (DEV evidence shows low marginal value).
- Arms (matched inspection/API budget): A = frozen Route-B verifier (4
  calls/task), B = expanded-pool bounded rerank/verify (1 call/task), C =
  analytic Random / Oracle references.
- Frozen: model qwen3-coder/OpenRouter temp 0 cap 512; strict JSON; fail-closed;
  no result-based retries; ≤30 tasks/repo DEVELOPMENT sampling (seeded); primary
  (ORR, P/R/F1/FNR, Oracle-Add-gap-closed, cost/latency) + safety metrics
  (no material F1 regression); pre-registered stop rule.

## 7. Projected API budget (Section 4; ZERO calls made)

`reports/BOUNDED_SEMANTIC_EXPANSION_BUDGET_FREEZE_DRAFT.md`:
- Per-call prompt ≈ 204.5 + 7.4·|pool| (measured cost model) ≤ ~500 prompt
  tokens at cap 40; completion ≤ 512; ≈ 1,012 total tokens/call.
- Arm B: 60 calls ≈ 60,720 tokens ≈ $0.017 (ceiling 90k / $0.024).
- Arm A: 240 calls ≈ 54,000 tokens ≈ $0.018 (ceiling 96k / $0.036).
- **Proposed hard stop: ≤300 calls / ≤300,000 tokens / ≤$0.30 / ≤60 min**;
  fail-closed per-call reservation ledger.

## 8. Exact authorization needed for the later API pilot

The DEVELOPMENT bounded-semantic pilot is **NOT executed** by this mission. The
exact authorization sentence required (also in the budget draft §7):

> "Authorize the bounded semantic rerank/verify DEVELOPMENT pilot under the
> frozen protocol + budget draft (≤300 calls / ≤300,000 tokens / ≤$0.30 / ≤60
> min, qwen3-coder, DEV only, sealed sets sealed)."

## 9. P2 / adaptive-k status (Section 5)

- P2 Phase-1 = **COMPLETE, NEGATIVE, frozen** (unchanged).
- **Adaptive budget is NOT the current bottleneck and is NOT active work.**
- Shichao-Zhang / adaptive-k / demand-driven-k = **FUTURE WORK, GATED** (revisit
  only after a stable ranking/recovery signal exists; choosing k cannot rescue a
  poorly ordered candidate list). Line gated, NOT deleted (roadmaps + literature
  ledger annotated).

## 10. Cross-language vs polyglot future-work correction (Section 6)

- **A. CROSS-LANGUAGE / CROSS-REPOSITORY:** different repositories from
  different ecosystems (Python, TypeScript, Java, Go).
- **B. POLYGLOT SINGLE-REPOSITORY:** one repository containing substantial
  production code in multiple languages with real cross-language change coupling.
- Ambiguous "multi-language benchmark" roadmap wording renamed to
  **`cross-language + polyglot-repository generalization`** in the MSc roadmap,
  P2 roadmap, and current-state docs.

## 11. Grafana feasibility status

**FUTURE CANDIDATE only — NOT scientifically accepted.** `grafana/grafana` added
as the primary polyglot feasibility-audit candidate (Go backend + TypeScript
frontend, documented backend/frontend parity paths). Required before acceptance:
repository feasibility audit, per-language production-source universe, cross-
language dependency/coupling representation, ≥60 eligible real commits if
feasible, explicit mixed-language commit strata, no generated/vendor/test
leakage, same proxy/leakage rules. No feasibility audit was run in this mission.

## 12. Sealed sets untouched (verified)

djangoCMS RESERVE, Saleor INTERNAL_TEST + RESERVE never loaded. `load_dev_tasks`
contains exactly 174 + 149 DEVELOPMENT case ids; `test_dev_counts_and_sealed`
and audit A8 assert no INTERNAL_TEST/RESERVE roles. The spent djangoCMS
INTERNAL_TEST was not read for any selection decision.

## 13. Tests / audits

- **12/12 new unit tests PASS** (`tests/unit/test_quant_ranking_bridge.py`):
  three-and-only-three identity, determinism, graph-direction consistency,
  normalization bounds, no-hidden-proxy features, parent-visible ranking keys,
  synthetic metric recomputation (candidate precision / naive union F1 / oracle
  reviewer), unique-FN non-negativity, fold/artifact helpers, repo portability.
- Affected suites green: `test_recall_bottleneck.py` 19/19 +
  `test_oracle_gap.py` 16/16 = **35/35 PASS**.
- **Independent audit 25/25 PASS** (`reports/fn_quant_ranking_bridge_audit.json`,
  `reports/FN_QUANT_RANKING_BRIDGE_AUDIT.md`): recomputes Route-B ORR @4 B-points
  (both repos), sparse F1, reverse-1hop/union-all availability, R1/R2/R3 ORR @5,
  gate decision, leakage, sealed-set guard, determinism, folds — without
  importing the analysis script.
- Ruff clean; mypy strict clean on `src/benchmark/recall`; py_compile clean;
  `git diff --check` clean.

## 14. Git / tag / export

- Branch `research/ranking-bridge-bounded-semantic-freeze-2026-09-18`; merge
  commit on `main` (see the closure block in `PROGRESS.md`).
- DEV-evidence tag `ranking-bridge-bounded-semantic-freeze-2026-09-18` — peel ==
  merge == `main` (audited DEVELOPMENT evidence; NOT a stable-tag move).
- LIGHT export at scientific closure (filename/hash in `PROGRESS.md` closure
  block + the stop report).

## 15. ONE next scientific action

Run the frozen **Stage-4 bounded semantic rerank/verify DEVELOPMENT pilot** under
the exact authorization sentence in §8 (Arm A Route-B verifier vs Arm B
expanded-pool bounded rerank/verify vs analytic references at matched budget),
converting the measured 0.73/0.87 availability ceilings into realized FN
recovery — with djangoCMS RESERVE / Saleor INTERNAL_TEST+RESERVE remaining
sealed until a frozen confirmatory protocol is approved.