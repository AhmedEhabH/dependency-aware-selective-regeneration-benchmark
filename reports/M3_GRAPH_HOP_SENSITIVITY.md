# M3 Graph Hop Sensitivity

**Study ID:** `scientific-djangocms-graph-c0-c1-c2-01`
**Date:** 2026-09-13

The hop distance is the minimum undirected distance from a candidate to the
scenario's deterministic seed set in the automatic AST import graph
(562 edges, 144 nodes). Distances were computed ZERO-API from the frozen
graph and frozen seeds (see `research/graph-c0-c1-c2-01/seed_zone_identity.json`).

## 1. Zone sizes by hop (frozen, before any call)

| Scenario | Seeds | 1-hop zone | 2-hop zone | 3-hop zone |
|---|---|---|---|---|
| 002 | 2 | 28 | 112 | 130 |
| 004 | 2 | 28 | 112 | 130 |
| 005 | 2 | 25 | 111 | 129 |
| 006 | 5 | 37 | 116 | 130 |
| 007 | 2 | 29 | 111 | 130 |
| 008 | 5 | 41 | 119 | 130 |

- 1-hop zones cover **17–28%** of the universe.
- 2-hop zones cover **77–83%** of the universe.
- 3-hop zones cover **90%** of the universe → pre-registered rule
  (|zone3| ≤ 115) → **3-hop NOT run**.

## 2. Hop-distance distribution of missed gold files

**C0 (Sparse-v2, M1B reuse):** all 14 FN come from S006 — both missed gold
files (`cms/admin/placeholderadmin.py`, `cms/utils/plugins.py`) are at
**distance 1** from the seed set. Missed-gold distance mean = 1.0.

**C1 (Graph Hints):** the 24 FN pool:

| Distance bucket | Missed-gold events | Scenarios |
|---|---|---|
| 0 (seed itself) | 4 | S005 `cms/admin/pageadmin.py` |
| 1 (in 1-hop zone) | 14 | S006 (9), S007 `page_permissions.py` (5) |
| 2 (outside 1-hop zone) | 6 | S007 `api.py` (2), `permissionmodels.py` (4) |

**C2 1-hop (valid n=2):** on the single valid S006 run the missed-gold
distance set became empty (recall 1.0) — the mandated in-zone decisions
recovered both distance-1 gold files. On the single valid S007 run, 4 FN
remained (all distance-2 gold: `api.py`, `permissionmodels.py` — **outside
the 1-hop zone** → `graph-coverage-gap` for the mandate).

## 3. Hop-distance distribution of selected (write-set) files

**C1 (Graph Hints):** pooled over 30 runs.

| Scenario | mean selected dist | median selected dist |
|---|---|---|
| 002 | 0.89 | 1 |
| 004 | 1.29 | 2 |
| 005 | 1.00 | 1 |
| 006 | 0.93 | 1 |
| 007 | 1.15 | 2 |
| 008 | 1.20 | 1 |

Selections concentrate within 1–2 hops of the seeds (mean 0.9–1.3): the model
used the graph context to keep selections graph-local, which is exactly the
mechanism behind both the FP reduction (fewer distant non-gold files) and the
recall loss (distance-2 gold such as S007's `api.py`/`permissionmodels.py`
falls outside the effectively-used neighborhood).

## 4. Compliance vs hop (the decisive sensitivity)

| Zone | In-zone ids demanded | Compliance |
|---|---|---|
| 1-hop | 25–41 | **2/30 (6.7%)** |
| 2-hop | 111–119 | **0/30 (0%)** |
| 3-hop | 129–130 | not run (pre-registered infeasible) |

The disclosure mechanism's viability is a steep, negative function of hop:
doubling the zone from 1-hop to 2-hop drove compliance to zero. With 90% of
the universe in-zone at 3-hop, mandatory disclosure at 3-hop would be
indistinguishable from full serialization — the reason the protocol froze the
ceiling at 80% (115/144).

## 5. Conclusion

- Graph Hints keeps selections near the seeds (median ≤ 2 hops) — a strong
  behavioral signal, but one that costs recall on distance-2 gold.
- Graph-Gated Disclosure's reach is bounded by the model's sparse output
  capacity: 1-hop is near the edge of feasibility (6.7% compliance) and any
  larger zone is infeasible as designed.
- The distance-2 gold cluster in S007 is the **coverage gap** for both
  treatments: C1 sees the full graph yet does not propagate; C2 1-hop cannot
  mandate distance-2 files by construction.

Companion: `reports/M3_GRAPH_RESULTS.md`,
`reports/M3_GRAPH_SCENARIO_FAILURE_TAXONOMY.md`,
`reports/M3_GRAPH_COST_RECALL_TRADEOFF.md`.