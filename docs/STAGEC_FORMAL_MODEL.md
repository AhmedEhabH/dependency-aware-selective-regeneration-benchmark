# STAGE-C Lightweight Formal Model — FROZEN

Status: **FROZEN 2026-09-07** (consolidation `research/stagec-consolidation-01`,
pack `RESEARCH_CONSOLIDATION_MAINLINE_01`). This document defines the formal
notation for the Stage-C impact-selection construct. It is a documentation-only
formalization of the already-measured system. It makes **no** claim about the
implemented Agent's algorithmic runtime complexity beyond ordinary reachability
traversal.

## 1. Artifact graph

Let

```
G = (V, E, tau, w)
```

- `V` — repository artifacts (files/artifacts).
- `E` — dependency/evidence edges between artifacts.
- `tau(e)` — typed edge relation (e.g. imports, references, test-links).
- `w(e)` — optional evidence/confidence weight on an edge.

## 2. Requirement delta and action space

Requirement delta: `r`.

Action space:

```
A = {R, P, V, H}
```

- `R` — regenerate/write.
- `P` — preserve.
- `V` — validate-only.
- `H` — human review.

## 3. ImpactPlan

`pi_r : V -> A`

Predicted write set:

```
W_r = { v in V | pi_r(v) = R }
```

Context/read set: `C_r`, explicitly independent of `W_r`:
`C_r` is the set of artifacts read as context and is **not** a function of
`W_r` in the construct definition (the measured system may recompute evidence,
but the formal construct keeps context and write sets separate).

Hidden gold write set: `G*_r`.

## 4. Primary write-set correctness

- Precision: `|W_r ∩ G*_r| / |W_r|`
- Recall: `|W_r ∩ G*_r| / |G*_r|`
- F1: harmonic mean of precision and recall.
- FNR: `1 - Recall`.
- FullRecall: `1` iff `G*_r ⊆ W_r`.

## 5. Graph-bounded reasoning

Requirement/evidence seeds: `S(r)`.

Graph-bounded candidate set:

```
B_r = Reach_G(S(r), policy)
```

An ordinary graph reachability traversal is bounded by `O(|V| + |E|)`.

> **Constraint (no O(2^n) claim).** The implemented Agent is NOT claimed to be
> `O(2^n)`. The following is optional conceptual intuition only:
> *if* arbitrary write subsets were considered, narrowing a universe from
> `|V| = n` to a candidate set `|B_r| = m` reduces the number of *possible*
> subsets from `2^n` to `2^m`. This is NOT an algorithmic runtime theorem for
> the Agent implementation.

## 6. Correctness-conditioned efficiency

Do not collapse correctness and efficiency into one opaque primary score.

Define qualification indicator `Q` according to the frozen correctness
requirement. Report:

- qualification rate
- tokens | Q=1
- calls | Q=1
- latency | Q=1
- cost | Q=1

Optional secondary descriptive metric (qualified runs only):

```
NormalizedSelectionTokens = tokens / |G*_r|
```

## 7. Empirical-scope limitation

Current Todo gold strongly evaluates `R`/write-set. `P` is inferred relative to
the frozen candidate source universe in the selection study. `V` and `H` are
descriptive unless a separately frozen/adjudicated gold set is later created.

> **Never claim four-class R/P/V/H accuracy from current Todo evidence.**

## 8. Empirical grounding (frozen, from Stage-C studies)

| Quantity | Smoke study | Held-out study |
|---|---|---|
| Arm | Agent / ImpactPlan | Agent / ImpactPlan |
| Full recall | 15/15 both | 30/30 both |
| Precision mean | 1.0 / 1.0 (ceiling) | 0.8778 / 0.7694 |
| F1 mean | 1.0 / 1.0 (ceiling) | 0.9200 / 0.8540 |
| Write-set size mean | 3.0 / 3.0 | 2.27 / 2.60 |
| Total tokens | 98,512 / 34,084 | 210,883 / 56,971 |
| Model calls | 89 / 15 | 220 / 30 |
| Total latency (s) | 147.644 / 252.094 | 490.108 / 236.162 |

Evidence: `reports/STAGEC_SELECTION_01_RESULTS.md`,
`reports/STAGEC_HELDOUT_01_RESULTS.md`,
`reports/STAGEC_LATENCY_DECOMPOSITION.md`.