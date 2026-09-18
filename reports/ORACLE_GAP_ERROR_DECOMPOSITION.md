# Oracle-Gap Error Decomposition

**Date:** 2026-09-18
**Tier:** T3 (ZERO API, ZERO model calls)
**Mission:** OPENCODE_ORACLE_GAP_BIDIRECTIONAL_REPAIR_MISSION_2026-09-18
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731
**Data:** djangoCMS DEVELOPMENT (174 tasks) + Saleor DEVELOPMENT (149 tasks) as
PRIMARY; the spent djangoCMS INTERNAL_TEST (80 tasks) is reported ONLY as
POST-HOC sanity. Machine-readable companions:
`reports/oracle_gap_decomposition.json`, `reports/oracle_gap_decomposition_f1.json`,
`reports/oracle_gap_confirmatory_verifier_posthoc.json`.

---

## 1. Sparse baseline per repo (first-succeeded-rep aggregate)

| Repo | n | TP | FP | FN | P | R | F1 | FNR | positives |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| djangoCMS DEV | 174 | 125 | 155 | 382 | 0.4464 | 0.2465 | **0.3177** | 0.7535 | 507 |
| Saleor DEV | 149 | 99 | 193 | 369 | 0.3390 | 0.2115 | **0.2605** | 0.7885 | 468 |
| Pooled DEV | 323 | 224 | 348 | 751 | 0.3916 | 0.2297 | 0.2895 | 0.7703 | 975 |

**Finding:** Sparse recalls only ~21–25% of proxy positives on DEVELOPMENT; the
first-pass set is majority-FP (P 0.34–0.45). Both recall AND precision are weak
at the file level.

## 2. Route-B add-only (composite-ranked) final-F1 effect

| Repo | Sparse F1 | B=5 add-only F1 | B=10 add-only F1 | Δ(B=5 − Sparse) |
|---|---:|---:|---:|---:|
| djangoCMS DEV | 0.3177 | 0.2257 | 0.1789 | **−0.0920** |
| Saleor DEV | 0.2605 | 0.2365 | 0.1867 | **−0.0240** |

**Finding:** Route-B add-only (composite-ranked top-B unioned into the Sparse
set) **lowers** file-level F1 at every B on both repos — the composite ranker
adds far more FPs than TPs (djangoCMS B=5: TP 187 / FP 963). This matches the
frozen confirmatory pattern (composite ORR > verifier ORR at every B) and the
curve-level AURC post-hoc. Add-only Route B improves *omitted-candidate
recovery* but not *file-level F1*.

## 3. Oracle-Add ceiling (perfect add, zero FP)

Start from Sparse set, perfectly add omitted true positives with per-task
budget A ∈ {0,1,2,3,5,10,ALL}, add zero FPs.

| A | djangoCMS P/R/F1 | Saleor P/R/F1 |
|---|---:|---:|
| 0 (Sparse) | 0.4464 / 0.2465 / 0.3177 | 0.3390 / 0.2115 / 0.2605 |
| 1 | 0.5590 / 0.4004 / 0.4666 | 0.4363 / 0.3526 / 0.3900 |
| 2 | 0.6284 / 0.5227 / 0.5705 | 0.5125 / 0.4529 / 0.4812 |
| 3 | 0.6732 / 0.6124 / 0.6415 | 0.5665 / 0.5321 / 0.5488 |
| 5 | 0.7213 / 0.7258 / 0.7236 | 0.6248 / 0.6553 / 0.6396 |
| 10 | 0.7614 / 0.9083 / 0.8284 | 0.6744 / 0.8707 / 0.7600 |
| ALL | **0.7659 / 1.0 / 0.8674** | **0.7080 / 1.0 / 0.8291** |

**Finding:** Oracle-Add ALL caps F1 at **0.8674 (djangoCMS)** / **0.8291
(Saleor)** — perfect recall still leaves the Sparse FP tail (155 / 193 files),
which caps precision at 0.766 / 0.708. **On Saleor, even perfect add-only cannot
reach F1 = 0.85.**

## 4. Oracle-Drop ceiling (perfect drop, zero TP removed)

Start from Sparse set, perfectly remove Sparse FPs with per-task budget
D ∈ {0,1,2,3,5,10,ALL}, remove zero TPs.

| D | djangoCMS P/R/F1 | Saleor P/R/F1 |
|---|---:|---:|
| 1 | 0.5650 / 0.2465 / 0.3433 | 0.4406 / 0.2115 / 0.2859 |
| 2 | 0.6674 / 0.2465 / 0.3601 | 0.5264 / 0.2115 / 0.3019 |
| 3 | 0.7610 / 0.2465 / 0.3721 | 0.6059 / 0.2115 / 0.3136 |
| 5 | 0.8964 / 0.2465 / 0.3867 | 0.7427 / 0.2115 / 0.3293 |
| 10 | 0.9661 / 0.2465 / 0.3927 | 0.8631 / 0.2115 / 0.3397 |
| ALL | **1.0 / 0.2465 / 0.3956** | **1.0 / 0.2115 / 0.3492** |

**Finding:** Oracle-Drop can fully clean precision but recall is pinned at the
Sparse first-pass value (0.2465 / 0.2115). Drop-only F1 ceiling is ~0.35–0.40 —
**insufficient alone.**

## 5. Oracle bidirectional F1 surface (A × D, DEVELOPMENT)

Perfect add + perfect drop over the Cartesian A×D grid. Representative cells:

| A\D | 0 | 1 | 3 | 5 | ALL |
|---|---:|---:|---:|---:|---:|
| **djangoCMS DEV** | | | | | |
| 1 | 0.4666 | 0.4983 | 0.5444 | 0.5761 | 0.6108 |
| 3 | 0.6415 | 0.6875 | 0.7626 | 0.8222 | 0.8921 |
| 5 | 0.7236 | 0.7747 | 0.8636 | 0.9281 | 0.9790 |
| 10 | 0.8284 | 0.8789 | 0.9520 | 0.9899 | 0.9963 |
| ALL | 0.8674 | 0.9099 | 0.9609 | 0.9899 | 1.0 |
| **Saleor DEV** | | | | | |
| 1 | 0.3900 | 0.4140 | 0.4571 | 0.4897 | 0.5340 |
| 3 | 0.5488 | 0.5842 | 0.6527 | 0.7111 | 0.7899 |
| 5 | 0.6396 | 0.6814 | 0.7646 | 0.8352 | 0.9153 |
| 10 | 0.7600 | 0.8120 | 0.9021 | 0.9552 | 0.9852 |
| ALL | 0.8291 | 0.8771 | 0.9519 | 0.9808 | 1.0 |

**Finding:** Bidirectional repair reaches F1 > 0.9 on both repos once A ≥ 5 and
D ≥ 3 (oracle). **F1 = 0.85 is mathematically reachable** on djangoCMS by
add-only (A=10) and on Saleor only bidirectionally (e.g. A=3,D=5 or A=5,D=3).

## 6. F1-target reachability (minimal oracle budget region)

| Target F1 | djangoCMS add-only | djangoCMS drop-only | djangoCMS bidirectional (min mean inspections) | Saleor add-only | Saleor drop-only | Saleor bidirectional |
|---|---:|---:|---:|---:|---:|---:|
| 0.50 | A=1 | unreachable | A=1,D=0 (0.88/task) | A=1 | unreachable | A=1,D=0 (0.85/task) |
| 0.60 | A=2 | unreachable | A=1,D=1 (1.37/task) | A=2 | unreachable | A=2,D=0 (1.41/task) |
| 0.70 | A=2 | unreachable | A=2,D=0 (1.47/task) | A=3 | unreachable | A=3,D=0 (1.78/task) |
| 0.80 | A=5 | unreachable | A=5,D=0 (2.04/task) | A=10 | unreachable | A=10,D=0 (2.46/task) |
| 0.85 | A=10 | unreachable | A=10,D=0 (2.20/task) | **UNREACHABLE add-only** | unreachable | A=3,D=5 (2.91/task) |
| 0.90 | unreachable add-only | unreachable | A=5,D=1 (2.53/task) | unreachable add-only | unreachable | A=5,D=3 (3.15/task) |

**Finding:** On Saleor, **F1 = 0.85 is NOT reachable by add-only** (Oracle-Add
ALL caps at 0.8291); it requires bidirectional correction. On djangoCMS it is
add-only-reachable only at A=10. F1 = 0.90 requires bidirectional on both repos.

## 7. Dominant bottlenecks (Section 3)

| Loss component | djangoCMS DEV | Saleor DEV | Verdict |
|---|---:|---:|---|
| First-pass recall loss (FN/positives) | 0.7535 | 0.7885 | **DOMINANT** |
| First-pass precision loss (FP/predicted) | 0.5536 | 0.6610 | large |
| Ranking loss @B=5 (oracle rec − composite rec) | 293 (355−62) | 246 (325−79) | large |
| Verifier false-rejection (POST-HOC INTERNAL_TEST @B5) | 15/35 (0.43) | n/a | moderate |
| Verifier false-acceptance (POST-HOC INTERNAL_TEST @B5) | 170/190 (0.89) | n/a | **large** |
| Budget loss @B=5 (positives outside top-B even perfect) | 27 | 44 | small |
| Budget loss @B=10 | 0 | 2 | negligible |

**Which ONE/TWO bottlenecks dominate?**

1. **FIRST-PASS RECALL LOSS is the dominant bottleneck** (75–79% of proxy
   positives are missed before any correction). Oracle-Add ALL alone adds
   +0.55–0.57 F1 (0.318→0.867 / 0.261→0.829).
2. **VERIFIER/REVIEW FALSE-ACCEPTANCE (precision of additions) is the second
   bottleneck.** Even under a cheap ranker the add queue is dominated by FPs
   (Route-B add-only lowers F1; the frozen verifier accepted only 10.5% of its
   B=5 additions). Add-only headroom is capped by the FP tail that corrections
   bring in (Oracle-Add ALL caps at 0.87/0.83, not 1.0).
3. Ranking loss is also large (composite recovers only 17–24% of oracle at
   B=5) but is secondary to first-pass recall.

The bottleneck is **NOT adaptive budget** (budget loss ≈ 0 at B=10) and **NOT
drop-side precision** alone (drop-only ceiling is recall-limited). The path to
F1 0.85+ is: first fix first-pass recall (the add side), then repair the
precision of additions (verifier/review quality or bidirectional DROP of FPs).

Machine-readable: `reports/oracle_gap_decomposition.json`,
`reports/oracle_gap_decomposition_f1.json`,
`reports/oracle_gap_confirmatory_verifier_posthoc.json`.