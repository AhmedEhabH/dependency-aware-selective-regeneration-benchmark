# FIRST-PASS RECALL BOTTLENECK — FINAL REPORT

**Date:** 2026-09-18
**Mission:** OPENCODE_FIRST_PASS_RECALL_BOTTLENECK_2026-09-18
**Status:** DEVELOPMENT only — COMPLETE; ZERO new model/API calls; sealed sets untouched
**Verdict:** **RECALL_SIGNAL_HEADROOM_ONLY** (no ADD queue passes the progression gate)
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731

---

## 1. Exact model

`openrouter/deepseek/deepseek-v4-flash-0731` (analysis authoring). ZERO new
scientific model/API calls; every result is a deterministic Python
computation over frozen records + case bundles (Tier T3).

## 2. Repo/split coverage

- djangoCMS DEV = **174** tasks (V1 30 + V2 DEV_TRAIN 117 + DEV_VALIDATION 27).
- Saleor DEV = **149** evaluable tasks.
- djangoCMS RESERVE, Saleor INTERNAL_TEST + RESERVE: **sealed, never loaded**.
- The spent djangoCMS INTERNAL_TEST was NOT used for any selection/tuning.

## 3. FN taxonomy counts by repo (primary reason)

| Primary | djangoCMS DEV | % | Saleor DEV | % |
|---|---:|---:|---:|---:|
| DIRECT_LEXICAL | 95 | 24.9 | 264 | 71.5 |
| HISTORY_COCHANGE | 86 | 22.5 | 0 | 0.0 (UNAVAILABLE) |
| NO_OBSERVABLE_SIGNAL | 87 | 22.8 | 6 | 1.6 |
| DOWNSTREAM_CONSUMER | 64 | 16.8 | 68 | 18.4 |
| INDIRECT_DEPENDENCY_2HOP | 43 | 11.3 | 21 | 5.7 |
| UPSTREAM_PROVIDER | 6 | 1.6 | 9 | 2.4 |
| DIRECT_DEPENDENCY | 1 | 0.3 | 0 | 0.0 |
| STRUCTURAL_NEIGHBOR | 0 | 0.0 | 1 | 0.3 |
| CROSS_LAYER | 0 | 0.0 | 0 | 0.0 |
| **Total FN** | **382** | | **369** | |

Multi-label overlap is large (270/382 djangocms FNs carry >1 label). Full
machine-readable: `reports/fn_taxonomy_development.json`.

## 4. Is S006-like indirect-utility/downstream miss general?

**Decision: GENERAL_PATTERN.**

- % FN with downstream-consumer flag: 58.9% (djangoCMS) / 82.1% (Saleor).
- % FN with upstream-provider flag: 43.7% / 71.5%.
- % FN consumer OR provider (raw): 64.7% / 91.1%.
- Direct-1-hop FNs that are lexically silent: **98.6% / 100%** — i.e. nearly every
  FN that is a graph neighbor of a seed is lexically distant (no intent/path
  token overlap). The S006 pattern (`plugins.py`-style downstream utility miss)
  is a **recurring, cross-repo structural miss**, not a one-off.

Important nuance (see §7): these FNs are already **inside Route-B's graph-1-hop
neighborhood** (the frozen composite carries a binary graph-neighbor flag).
The miss is therefore a *ranking* miss within the already-available
neighborhood, not a candidate-availability miss.

## 5. Source-specific recall ceilings (oracle, K=5 reference)

| Source (K=5 oracle) | djangoCMS ORR ceil | Saleor ORR ceil | djangoCMS unique beyond Route-B | Saleor unique beyond Route-B |
|---|---:|---:|---:|---:|
| BM25 (budget headroom) | 0.929 | 0.881 | 293 | 246 |
| PATH_TOKEN | 0.929 | 0.881 | 293 | 246 |
| GRAPH_REVERSE_1HOP (consumers) | 0.558 | 0.724 | 161 | 197 |
| GRAPH_FORWARD_1HOP (providers) | 0.424 | 0.642 | 113 | 166 |
| GRAPH_1HOP (undirected) | 0.186 | 0.203 | 66 | 75 |
| GRAPH_2HOP | 0.113 | 0.051 | 43 | 19 |
| HISTORY_COCHANGE (djangocms only) | 0.293 | 0.000 | 89 | 0 |
| STRUCTURAL_SIBLING | 0.579 | 0.732 | 165 | 191 |
| UNION_CONSUMER_PROVIDER | 0.605 | 0.802 | 170 | 218 |
| UNION_2HOP+COCHANGE+SIBLING | 0.670 | 0.778 | 199 | 208 |
| **UNION_ALL** | **0.725** | **0.870** | 216 | 242 |

Key structural fact: BM25's oracle ceiling is the **budget ceiling** (its pool =
all candidates), so candidate availability is NOT the bottleneck for BM25; the
gap to the actual BM25 recovery (0.149/0.209 @K=5) is pure **ranking loss**.

## 6. Best complementary source(s)

- **GRAPH_REVERSE_1HOP (downstream consumers)** is the single largest genuinely
  complementary pool (55.8%/72.4% of FNs), matching the taxonomy (D).
- **STRUCTURAL_SIBLING** and **GRAPH_FORWARD_1HOP (providers)** are the next two.
- **GRAPH_2HOP** is weak and repo-asymmetric (djangoCMS 11.3% vs Saleor 5.1%).
- **HISTORY_COCHANGE** is djangoCMS-only (Saleor history UNAVAILABLE), so it
  fails the repo-portability rule as a standalone queue feature.
- Diminishing-return build-up (K=5): Route-B 1-hop pool 0.186/0.203 →
  +REVERSE_1HOP 0.573/0.748 → +FORWARD_1HOP 0.605/0.802 → +2HOP 0.712/0.854 →
  +HISTORY 0.712/0.854 → +SIBLING 0.725/0.870. Reverse-1hop dominates the
  marginal gain; history adds 0 after 2-hop on djangoCMS.

## 7. Up to 3 candidate queues (frozen formulas)

| ID | Formula (score, desc) | Rationale |
|---|---|---|
| Q1 `BM25+ReverseDependency` | bm25 + consumer | S006-like downstream consumers (taxonomy D) |
| Q2 `BM25+ProviderConsumerSupport` | bm25 + consumer + provider | directed dependency support (D+E) |
| Q3 `BM25+ComplementaryUnion` | bm25 + (dist==2) + co-change + sibling | INDIRECT_2HOP + HISTORY + SIBLING |

All are deterministic, use only parent-visible binary flags, tie-break by path.

## 8. Matched-budget comparison vs Route-B (B=5 reference)

| Ranker | djangoCMS ORR | Saleor ORR | djangoCMS Δ | Saleor Δ |
|---|---:|---:|---:|---:|
| Route-B composite (frozen) | **0.163** | **0.237** | — | — |
| BM25-only | 0.161 | 0.234 | −0.002 | −0.003 |
| Q1 BM25+ReverseDependency | 0.152 | 0.238 | −0.011 | +0.001 |
| Q2 BM25+ProviderConsumerSupport | 0.139 | 0.235 | −0.025 | −0.001 |
| Q3 BM25+ComplementaryUnion | 0.077 | 0.027 | −0.086 | −0.209 |

**No queue materially beats Route-B at matched budget.** Q1 is statistically
≈ Route-B on both repos (Δ −0.011 / +0.001); Q3 is much worse (its sibling
flag fires on ~52% of non-FN candidates, diluting the ranking). The unique FN
recovery beyond Route-B is 10–22 per queue per repo at K=5/10 — small.

## 9. Naive final union F1 (View B — files simply added to Sparse)

| Ranker @B=5 | djangoCMS F1 | Saleor F1 | vs Sparse (0.318/0.261) |
|---|---:|---:|---:|
| Route-B add-only | 0.226 | 0.236 | −0.092 / −0.025 |
| Q1 BM25+ReverseDependency | 0.227 | 0.239 | −0.091 / −0.022 |
| Q2 BM25+ProviderConsumerSupport | 0.220 | 0.239 | −0.098 / −0.022 |
| Q3 BM25+ComplementaryUnion | 0.188 | 0.141 | −0.130 / −0.120 |

All ADD queues **lower** file-level F1 when naively unioned (FP tail from
additions), exactly like Route-B add-only. No claim of superiority on F1.

## 10. Oracle-reviewer simulation (perfect reviewer accepts only true FNs)

| Ranker @B=5 | djangoCMS F1 | Saleor F1 | gap to Oracle-Add (0.724/0.640) |
|---|---:|---:|---:|
| Route-B | 0.441 | 0.424 | 0.283 / 0.216 |
| Q1 | 0.442 | 0.428 | 0.282 / 0.212 |
| Q2 | 0.431 | 0.428 | 0.293 / 0.212 |
| Q3 | 0.381 | 0.276 | 0.343 / 0.364 |

Even under a perfect reviewer, the queues recover only 0.44–0.43 F1 at B=5.
**Dominant remaining loss = RANKING** (which FNs are placed in top-B), not
reviewer acceptance: the gap between naive-union F1 (≈0.23) and oracle-reviewer
F1 (≈0.44) is reviewer acceptance; the gap between oracle-reviewer F1 (≈0.44)
and Oracle-Add (≈0.72) is ranking.

## 11. Fair LocAgent / community-value interpretation

No new LocAgent spend was made. The shared-protocol findings (P5/P5C) remain
immutable. What this DEVELOPMENT result means:

- **Scientific community:** the S006-style downstream/utility miss is not a
  one-off — it generalises across two repositories (58.9%/82.1% of FNs are
  downstream consumers of a seed; direct-1-hop FNs are ≈100% lexically
  silent). Candidate *availability* is therefore not the first-pass problem;
  *ranking* is. This redirects future work from "add more candidate sources"
  to "order the available candidates better" (e.g., verifier-ranked
  expansion), which is a cheaper, more reproducible target than expensive
  agentic reasoning.
- **Industrial use:** a simple reproducible recall-recovery step (source
  pools + bounded ranking) is measurable BEFORE committing to expensive agent
  inference. This study shows exactly which pools are worth inspecting and
  which are not (2-hop and pure sibling signals add little; reverse-1hop
  consumers carry most of the missed files), giving an actionable
  zero-model pre-screen.
- **Future researchers:** the negative is as valuable as the positive —
  simple binary-flag queues do not beat Route-B at matched budget, so
  repeating that recipe is unlikely to help. The frozen taxonomy, ceilings,
  per-task FN sets (`research/first-pass-recall-bottleneck/fn_universe.json`)
  and the reproducible toolchain (`src/benchmark/recall/`,
  `scripts/fn_*.py`) are reusable for any follow-up.
- **Boundary:** this is DEVELOPMENT evidence only; no universal superiority
  claim over LocAgent or any LLM planner is made. A fair LocAgent comparison
  remains pending a shared fresh confirmatory protocol
  (`reports/LOCAGENT_FAIR_COMPARISON_PLAN_V2.md`).

## 12. Dominant remaining loss

1. **RANKING within the candidate universe** — the largest measured loss:
   BM25's oracle ceiling is 0.929/0.881 @K=5, actual recovery 0.149/0.209;
   Oracle-Add (perfect ranking + perfect reviewer) reaches 0.724/0.640 F1.
2. **Candidate availability is NOT the binding constraint** — the reverse-1hop
   consumer pool alone carries 55.8%/72.4% of FNs, but simple binary-flag
   queues cannot order it better than BM25 does.
3. **Reviewer acceptance** — second, bounded by ranking (oracle-reviewer F1
   0.44 vs Oracle-Add 0.72).

## 13. Progression gate result

**`RECALL_SIGNAL_HEADROOM_ONLY`.**

All three queues FAIL the gate (C1: no material FN recovery above Route-B on
both repos; Q3 additionally fails direction/fold consistency). No bounded
LLM-verifier experiment is authorized by this mission. The headroom (Oracle-Add
0.72/0.64; union-pool ceilings 0.73/0.87) is real but requires a stronger
ranking signal than the simple binary-flag queues tested — the frozen verifier
line remains the correct instrument for that, under its own frozen budget.

## 14. Sealed sets untouched (verified)

djangoCMS RESERVE, Saleor INTERNAL_TEST + RESERVE never loaded. `load_dev_tasks`
contains exactly 174 + 149 DEVELOPMENT case ids; `test_sealed_sets_guard`
asserts no INTERNAL_TEST/RESERVE roles. The spent djangoCMS INTERNAL_TEST was
not read for any selection decision.

## 15. Tests / audits

- 16 new unit tests PASS (`tests/unit/test_recall_bottleneck.py`): taxonomy
  determinism, graph-direction correctness, no-hidden-proxy feature
  generation, duplicate handling, zero-FN tasks, tiny universes, budget
  clipping, tie-breaking, repository portability, Route-B reproduction.
- Route-B reproduction: djangocms composite macro ORR 0.0464/0.1177/0.1633/
  0.2512 == frozen `route_b_v2_results.json` exactly (all 4 B-points).
- Independent audit recomputes the headline numbers from frozen records
  without importing the analysis scripts (see
  `reports/FN_INDEPENDENT_AUDIT.md` + JSON).
- Full-suite state and six T3 gates recorded in the audit/report.

## 16. Docs / research-journey updates

- `00_CURRENT_RESEARCH_STATE.md` (new CURRENT TRUTH block),
- `PROGRESS.md` (execution truth),
- `DECISIONS.md` (P63 append-only),
- `docs/RESEARCH_JOURNEY.md` (new milestone row + negative-preservation note),
- experiment/idea + problems/failures ledgers (`reports/EXPERIMENT_AND_IDEA_LEDGER.md`,
  `reports/PROBLEMS_AND_FAILURES_LEDGER.md`),
- README: concise current-status refresh only if the headline state changed.

## 17. Git / tag / export

- Branch `research/first-pass-recall-bottleneck-2026-09-18`; merge commit
  `7a251f0` on `main` (immutable scientific fact).
- DEV-evidence tag `first-pass-recall-bottleneck-2026-09-18` — annotated tag
  object `4b649c4`, peel `7a251f0` == merge == main-at-tag-time (audited
  DEVELOPMENT evidence; NOT a stable-tag move).
- Post-tag docs commit `9bb6478` pushed (never moves the tag).
- LIGHT export `project-2026-09-18-1725.zip` SHA-256
  `3d13b9c00684c9db123cd7682fbc303917b10cb4a116e1523c3652f4911a4b9e`
  (95,340,878 bytes; required members checked).

## 18. ONE next scientific action

The frozen **Route-B verifier line is the correct instrument for ranking
recovery**: the oracle-reviewer simulation shows a perfect reviewer can turn
B=5 queues into F1 ≈ 0.44, and Oracle-Add caps at 0.72. The next scientific
step is **not** a new queue; it is a bounded, pre-registered experiment that
uses the existing verifier (frozen protocol/budget) on the union of
Route-B's top-B plus the reverse-1hop consumer pool, evaluated on DEVELOPMENT,
to test whether a *verifier-ranked* (not binary-flag) expansion converts the
measured 0.73/0.87 availability ceilings into realized recall — with djangoCMS
RESERVE / Saleor INTERNAL_TEST+RESERVE remaining sealed until a frozen
confirmatory protocol is approved.