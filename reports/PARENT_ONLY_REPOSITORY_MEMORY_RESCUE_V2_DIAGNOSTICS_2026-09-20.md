# Parent-Only Repository Memory Rescue V2 — Diagnostics (2026-09-20)

**Status:** descriptive DEVELOPMENT diagnostics (ZERO API; frozen generator;
evaluation labels used ONLY retrospectively). **Not** inference features.

## 1. Verified V1 rank-selection diagnostic (Full-Universe V2 cancellation basis)

From the exposed V1 artifacts (`research/calibrated-set-selection-v1/`):

| V1 non-Sparse selected additions by dense rank | count |
|---|---:|
| 1 | 172 |
| 2 | 93 |
| 3 | 20 |
| 4 | 3 |
| 5–20 | 0 |

Non-Sparse candidate pool at ranks 5–20: n = 4,981 rows, 0 selected. Max
outer-OOF probability among non-Sparse candidates: ranks 5–20 = 0.1880
(p95 0.0886); ranks 15–20 = **0.0650** (p95 0.0428). All five V1 inner-CV
thresholds: 0.18 / 0.19 / 0.19 / 0.17 / 0.21 — strictly above every non-Sparse
rank-5+ probability. Empirical proxy-positive rate by non-Sparse dense-rank
band: r1 0.2562, r2 0.1660, r3 0.1254, r4 0.0519, r5–10 0.0616,
r11–15 0.0447, r16–20 0.0261, r>20 0.0193.

**Decision:** `FULL_UNIVERSE_V2_CANCELLED_AS_NON_BINDING_ABLATION` — the top-20
boundary was never active at the decision boundary; removing it while keeping
the rank-monotone signal would be a near-null rerun with forking-path risk.

## 2. Deep dense miss counts + dense-rank distribution

`DEEP_DENSE_MISS` = V1 false-negative proxy positive outside the V1 frozen
candidate universe (Sparse ∪ dense-top-20).

| Repo | count | median dense rank | mean | p25 | p75 |
|---|---:|---:|---:|---:|---:|
| djangoCMS | 199 | 62 | 75.6 | 37 | 100.5 |
| Saleor | 177 | 70 | 130.1 | 42 | 163 |

## 3. Dependency-cluster diagnostic (descriptive oracle-style)

Uses evaluation labels ONLY for retrospective headroom; never inference seeds;
NO graph features added to V2.

| Repo | A. direct relation to another proxy positive | B. adjacent to a V1 TP | C. within 2 hops of a V1 TP |
|---|---:|---:|---:|
| djangoCMS | 109 / 199 (0.548) | 25 (0.126) | 56 (0.281) |
| Saleor | 130 / 177 (0.735) | 49 (0.277) | 76 (0.429) |

## 4. Deep-FN coverage report (before classifier; frozen generator, realization A)

| Channel | djangoCMS (199) | Saleor (177) |
|---|---:|---:|
| structural only | 14 | 20 |
| episodic only | 23 | 24 |
| both | 6 | 4 |
| **union recovered** | **43 (0.216)** | **48 (0.271)** |
| unrecovered | 156 | 129 |
| Sparse-empty tasks (deep misses / recovered / rate) | 105 / 22 / 0.210 | 69 / 16 / 0.232 |

NO arbitrary 15% threshold; the preregistered V2 continued regardless.

## 5. Mechanism baselines (same candidate budget, top-10 non-sparse)

| Baseline | djangoCMS covered | Saleor covered |
|---|---:|---:|
| Historical popularity (history_change_count) | 41 / 199 (0.206) | 18 / 177 (0.102) |
| Seeded deterministic random (seed 20260920, 1,000 resamples) | mean 11.1 (0.056), CI95 5–18 | mean 2.45 (0.014), CI95 0–6 |
| **Memory candidate set (union)** | **43 / 199 (0.216)** | **48 / 177 (0.271)** |

Neither baseline was used to tune memory.

## 6. Channel ablations (descriptive; NOT used to redefine V2)

Realization A, same frozen model/threshold:

| Ablation | djangoCMS F1 (Δ vs Sparse, CI) | Saleor F1 (Δ, CI) |
|---|---:|---:|
| structural removed | 0.3459 (+0.0282 [−0.0085, +0.0650]) | 0.3333 (+0.0728 [+0.0363, +0.1099]) |
| episodic removed | 0.3462 (+0.0286 [−0.0053, +0.0630]) | 0.3326 (+0.0721 [+0.0403, +0.1047]) |
| FULL V2 | 0.3451 (+0.0274 [−0.0102, +0.0636]) | 0.3476 (+0.0871 [+0.0515, +0.1229]) |

Both channels contribute a small descriptive amount on Saleor; neither changes
the verdict on djangoCMS (CI crosses zero in every variant).

## 7. Efficiency

- History index (D:, outside Git): djangoCMS 7.4 MB + Saleor 10.2 MB;
  memory bundles 15.8 MB (total 33.5 MB).
- Build wall: index load 2.6/1.7 s (first) / 0.06/0.16 s (cached); task build
  52 s (174) / 73 s (149); total ≈ 183 s one-time.
- Classifier: full nested CV ≈ 25–40 s per realization; deterministic.
- API calls: 0; cost $0.00.