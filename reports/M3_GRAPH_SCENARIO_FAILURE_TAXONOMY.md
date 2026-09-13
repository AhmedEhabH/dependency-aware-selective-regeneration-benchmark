# M3 Graph Scenario Failure Taxonomy

**Study ID:** `scientific-djangocms-graph-c0-c1-c2-01`
**Date:** 2026-09-13
**Classification:** POST-HOC EXPLORATORY DEVELOPMENT-SET GRAPH ABLATION

The categories below were **pre-registered in
`reports/M3_GRAPH_PROTOCOL.md` §5 before any scientific call**. No new
categories were created after observing results. Each failed/weak cell is
classified with evidence; cells that cannot be cleanly attributed are labeled
`other-with-rationale` with an explicit rationale.

Frozen taxonomy: `missed-neighbor`, `over-expansion`, `wrong-edge-direction`,
`graph-evidence-ignored`, `mandatory-disclosure-failure`,
`unrelated-module-attraction`, `graph-coverage-gap`, `semantic-misreasoning`,
`operational/schema failure`, `other-with-rationale`.

---

## 1. C2 (Graph-Gated Disclosure) — the dominant failure class

| Condition | Cells | Failed | Failure category | Share |
|---|---|---|---|---|
| C2 1-hop | 30 | 28 | `mandatory-disclosure-failure` | 93.3% |
| C2 2-hop | 30 | 30 | `mandatory-disclosure-failure` | 100% |

**Per-scenario (1-hop):**

| Scenario | Zone size | Seeds | Compliant | Violated | Valid |
|---|---|---|---|---|---|
| 002 | 28 | 2 | 0 | 5 | 0 |
| 004 | 28 | 2 | 0 | 5 | 0 |
| 005 | 25 | 2 | 0 | 5 | 0 |
| 006 | 37 | 5 | 1 | 4 | 1 |
| 007 | 29 | 2 | 1 | 4 | 1 |
| 008 | 41 | 5 | 0 | 5 | 0 |

**Diagnosis (with rationale, not a new category):** all 58 C2 failures are
`mandatory-disclosure-failure`. The model emitted far fewer explicit
decisions than the in-zone mandate required: median 21.5 of 25–41 in-zone ids
omitted per failed run at 1-hop, and (by construction of the larger 2-hop
zones) all 30 2-hop runs violated. Root cause: the frozen sparse schema
"emit only non-PRESERVE decisions" and the model's natural sparse output
length (~5–20 decisions) are structurally far below the mandated in-zone
cardinality (25–41 / 111–119). This is **not** evidence that the model
"ignored" the graph — it is a serialization-capacity mismatch between the
disclosure mandate and the sparse action policy. The single S006 and S007
compliant runs show the mandate is satisfiable in principle.

## 2. C1 (Graph Hints) — missed-gold classification (FN)

C1 had 30/30 valid cells but 24 pooled FN across 6 scenarios (C0: 14). The
missed gold files per scenario (union over 5 reps) with their graph distance
to the seed set:

| Scenario | Missed gold file | Reps missed | dist to seed | In 1-hop zone | Classification |
|---|---|---|---|---|---|
| 005 | `cms/admin/pageadmin.py` | 4/5 | 0 (**seed**) | yes | `missed-neighbor` (a gold file that IS a seed was not selected) |
| 006 | `cms/admin/placeholderadmin.py` | 5/5 | 1 | yes | `missed-neighbor` (structural neighbor of seed `pluginmodel.py`; soft evidence did not flip the decision) |
| 006 | `cms/utils/plugins.py` | 4/5 | 1 | yes | `missed-neighbor` (the pre-registered S006 poster case: graph HINTS alone do not recover it) |
| 007 | `cms/utils/page_permissions.py` | 5/5 | 1 | yes | `missed-neighbor` |
| 007 | `cms/api.py` | 2/5 | 2 | no | `graph-coverage-gap` (outside the 1-hop zone; full graph IS visible in C1, so also partially `semantic-misreasoning` — the model did not propagate the change through the API facade) |
| 007 | `cms/models/permissionmodels.py` | 4/5 | 2 | no | `graph-coverage-gap` / `semantic-misreasoning` (distance-2 dependency not reached) |
| 002 / 004 / 008 | none | — | — | — | no FN |

**S006 note.** In C0 (Sparse-v2) the same two files were missed
(placeholderadmin 5/5, plugins 4/5, plus 10 pooled FN). In C1 the misses
persist (5/5 and 4/5) but pooled FN fell 10 → 9 because FP collapsed
(16 → 8). The graph hints **did not repair the S006 structural miss**; they
improved the scenario by precision. The only recovery of
`cms/utils/plugins.py` occurred in the single compliant C2-1hop S006 run
(`mandatory-disclosure-failure` everywhere else).

## 3. C1 (Graph Hints) — FP classification

C1 pooled FP = 22 (C0: 41; −46%). The reduction is the headline positive.

| Class | Interpretation | Evidence |
|---|---|---|
| `over-expansion` (reduced) | C0's FP was driven by broad over-selection (S006 16 FP, S007 27 FP); C1's conservative shift removed 19 FP | FP 41 → 22; selections 147 → 118 |
| `unrelated-module-attraction` | residual FP are files the model still pulled in without requirement support (S002 4 FP — likely the graph context caused over-weighting of neighbor imports) | S002 FP 1 → 4 |
| `wrong-edge-direction` | no evidence — no cell shows selection explained by a reversed import edge | none |

## 4. C0 (Graph OFF, M1B reuse) — baseline classification

C0 failures: 0 operational. Baseline FN (14) and FP (41) are the reference;
FP dominated by `over-expansion` (S006 16 FP, S007 27 FP), FN dominated by
S006's `missed-neighbor` misses (10 of 14).

## 5. Category totals across M3 (all 90 new cells + 30 reused C0)

| Category | Count | Condition |
|---|---|---|
| `mandatory-disclosure-failure` | 58 | C2 (28 @ 1-hop, 30 @ 2-hop) |
| `missed-neighbor` | 20 FN-cell-events | C1 (S005, S006, S007) vs C0 baseline |
| `graph-coverage-gap` / `semantic-misreasoning` | 11 FN-cell-events | C1 S007 (distance-2 gold) |
| `operational/schema failure` | 0 | all conditions |
| `wrong-edge-direction` | 0 | none observed |
| `other-with-rationale` | 0 | none needed |

Caveat: FN/FP "cell-events" are pooled selections across the 5 repetitions,
not independent categories per cell; the taxonomy is a descriptive
attribution, not a statistical test (n=6 scenarios).

Companion: `reports/M3_GRAPH_RESULTS.md`, `reports/M3_GRAPH_HOP_SENSITIVITY.md`,
`reports/M3_GRAPH_COST_RECALL_TRADEOFF.md`.