# Oracle-Gap Decomposition + Bidirectional Bounded Set Repair — FINAL REPORT

**Date:** 2026-09-18
**Mission:** OPENCODE_ORACLE_GAP_BIDIRECTIONAL_REPAIR_MISSION_2026-09-18
**Status:** EXPLORATORY DEVELOPMENT — complete, negative-for-heuristic-BBSR,
ZERO API/ZERO model calls, sealed sets untouched
**Verdict:** **BIDIRECTIONAL_HEADROOM_ONLY** (see §10)
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731

---

## 1. Exact model

`openrouter/deepseek/deepseek-v4-flash-0731` (analysis authoring). ZERO model/API
calls; all results are deterministic Python over frozen records + datasets.

## 2. Sparse baseline error decomposition per repo (DEVELOPMENT)

| Repo | n | TP | FP | FN | P | R | F1 | FNR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| djangoCMS DEV | 174 | 125 | 155 | 382 | 0.4464 | 0.2465 | **0.3177** | 0.7535 |
| Saleor DEV | 149 | 99 | 193 | 369 | 0.3390 | 0.2115 | **0.2605** | 0.7885 |

Confirmatory POST-HOC sanity (spent djangoCMS INTERNAL_TEST, verified against
frozen records): Sparse TP=51 FP=104 FN=199 F1=0.2519; verifier B=5 TP=71
FP=274 FN=179 F1=0.2387 — **matches** the mission's working diagnostic exactly.

## 3. Current add-only Route-B final-F1 effect

Route-B add-only (composite-ranked top-B unioned into the Sparse set) **lowers
file-level F1** at every B: djangoCMS B=5 0.2257 (Δ −0.092), Saleor B=5 0.2365
(Δ −0.024). The composite ranker adds far more FPs than TPs.

## 4. Oracle-Add F1 ceiling

Perfect adds (zero FP) on DEVELOPMENT: djangoCMS **0.8674** @A=ALL; Saleor
**0.8291** @A=ALL. Even perfect recall leaves the Sparse FP tail capping
precision at 0.766/0.708.

## 5. Oracle-Drop F1 ceiling

Perfect drops (zero TP removed): djangoCMS **0.3956** @D=ALL; Saleor **0.3492**
@D=ALL. Recall is pinned at the Sparse first-pass value.

## 6. Oracle bidirectional surface and F1=0.85 reachability

- Bidirectional repair reaches F1>0.9 once A≥5, D≥3 (oracle). Full surface:
  `reports/ORACLE_F1_CEILING_AND_BUDGET_SURFACE.md` + JSON.
- **F1=0.85 mathematically reachable:** djangoCMS add-only A=10 (2.20
  inspections/task); Saleor **add-only UNREACHABLE** (ceiling 0.8291) — requires
  bidirectional (e.g. A=3,D=5, 2.91/task). F1=0.90 requires bidirectional on
  both repos.
- **Bottleneck preventing 0.85 add-only on Saleor:** the Sparse first-pass FP
  tail (193 files, precision 0.339) — the DROP side is required once recall is
  perfect.

## 7. Dominant measured bottleneck(s)

1. **FIRST-PASS RECALL LOSS (dominant):** 75–79% of proxy positives missed;
   Oracle-Add ALL adds +0.55–0.57 F1.
2. **REVIEW/VERIFIER FALSE-ACCEPTANCE (precision of additions):** Route-B
   add-only lowers F1; frozen verifier accepted only 10.5% of B=5 additions.
3. Ranking loss is large (composite recovers only 17–24% of oracle @B=5) but
   secondary; budget loss ≈ 0 @B=10 → **not adaptive budget.**

## 8. Simple FP-pruning results

Observable rankers (bm25/composite/graph/path-token) flag FPs at precision
barely above random control (djangoCMS 0.562 vs 0.558; Saleor 0.636 vs 0.613),
with high TP-loss risk (36–44%). Even an oracle DROP cannot exceed F1 0.39/0.34.
**Cheap observable signals are insufficient for a safe DROP queue.**

## 9. Bidirectional candidate result (BBSR, ZERO-LLM simulation)

Heuristic BBSR (add composite-top-A + drop lowest-composite-D) **does NOT
improve on Sparse or add-only Route-B** on either repo (best F1 0.207/0.210 vs
Sparse 0.318/0.261). Oracle BBSR reaches only 0.385/0.346 at K=2; matched-budget
analysis shows bidirectional only beats add-only at K≥5 and only under perfect
oracle review. No new verifier calls were made.

## 10. Progression gate / scientific decision

**Progression gate = FAIL on both repos** (heuristic BBSR does not beat Sparse
or add-only Route-B; recall degrades). No later LLM verifier experiment is
authorized by this mission.

**Decision: `BIDIRECTIONAL_HEADROOM_ONLY` (B).** The development oracle surface
shows substantial F1 headroom (bidirectional reaches 0.85–0.90 on both repos,
1.0 at A=ALL,D=ALL), but current cheap observable signals are insufficient to
realize the DROP side, and the simple heuristic candidate fails the gate.
Recommended next bottleneck (per measured decomposition): **first-pass recall**
(the add side) — the Oracle-Add ALL gap of +0.55–0.57 F1 dwarfs everything else.

## 11. Fair LocAgent comparison status

No LocAgent spend. Plan delivered (`reports/LOCAGENT_FAIR_COMPARISON_PLAN_V2.md`):
the prior shared-protocol run is NOT a faithful reproduction of the published
fine-tuned setup; a Pareto-dominance statement requires identical task sets and
strict ≤ on F1/cost/tokens/latency/failure rate under one frozen protocol. No
dominance claim made.

## 12. Focused literature / novelty status

No verified primary source for "bounded ADD+DROP set repair around a first-pass
localization set" was found in the 41-entry ledger; nearest families are
ADD-only verifier-on-top-k (Repoformer/FastCoder line) and one-sided selective
abstention. **No novelty claim made.** Two verified-adjacent entries
(P2-040, P2-041) added to the ledger.

## 13. Semantic-audit status

Used correctly: inter-model agreement 0.6981 / κ 0.5579 and the descriptive
top-ranked>random relevance direction are recorded as AI-assisted descriptive
evidence, NOT human semantic gold. Human ratings remain an explicit
limitation/blocker (`reports/AI_SEMANTIC_AUDIT_AGREEMENT_REPORT.md`); no new
semantic model calls.

## 14. Sealed sets untouched (verified)

djangoCMS RESERVE, Saleor INTERNAL_TEST + RESERVE never loaded. The spent
djangoCMS INTERNAL_TEST was used ONLY as labelled POST-HOC sanity
(`reports/ORACLE_GAP_ERROR_DECOMPOSITION.md` §1–§2), never for selection.
`test_sealed_sets_guard` asserts the DEV load contains 174+149 case ids and no
INTERNAL_TEST/RESERVE roles.

## 15. Tests / audits

- 16 new unit tests PASS (`tests/unit/test_oracle_gap.py`): oracle math,
  no-hidden-proxy, set semantics, zero-FN/FP, tiny sets, budget clipping,
  frozen-evidence parity, sealed-set guard, BBSR/FPr bounds.
- Ruff clean on all 10 scripts + test; py_compile clean; `git diff --check`
  clean.
- Six validation gates PASS + independent audit PASS
  (`reports/oracle_gap_gates_validation.json`,
  `reports/ORACLE_GAP_INDEPENDENT_AUDIT.md`): headline numbers recomputed from
  raw frozen records without importing the analysis scripts.

## 16. Git / tag / export

See `PROGRESS.md` closure block (branch, merge, tag peel == merge == origin/main,
LIGHT export).

## 17. ONE next scientific action

Pursue the **first-pass recall bottleneck** on DEVELOPMENT: the measured
Oracle-Add headroom (+0.55–0.57 F1) is the largest single lever. Concretely,
the next candidate is a higher-recall first pass (or a bounded ADD queue with a
better precision-controlled reviewer) evaluated under the same development
gates — NOT the DROP side, which the cheap observable signals cannot support.
The human semantic-audit ratings also remain an open blocker for gold-level
claims.