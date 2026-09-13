# M3 Graph Cost–Recall Trade-off

**Study ID:** `scientific-djangocms-graph-c0-c1-c2-01`
**Date:** 2026-09-13

This report answers: what does each graph treatment cost (tokens, latency,
USD) and what does it buy (recall / precision / FN / FP)? All numbers are
recorded usage at the frozen DeepInfra pricing from `endpoint_freeze.json`
($0.30/$1.00 per 1M prompt/completion); recomputed by
`scripts/verify_graph_ablation_claims.py` (40/40 PASS).

## 1. Per-condition economics

| Condition | mean prompt tok | mean completion tok | mean total tok | latency (30 cells, s) | cost USD (30 cells) | recall | precision | F1 | FN | FP |
|---|---|---|---|---|---|---|---|---|---|---|
| **C0** (Graph OFF) | 2,640 | 809 | 3,449 | 609 | 0.0480 | **0.8833** | 0.7211 | 0.7940 | **14** | 41 |
| **C1** (Graph Hints) | 8,052 | 855 | **8,907** | 265 | 0.0981 | 0.8000 | **0.8136** | **0.8067** | 24 | **22** |
| **C2 1-hop** (Gated, valid n=2) | 3,262 | 1,365 | 4,627 | 418 | 0.0703 | 0.6000 | 0.2727 | 0.3750 | 4 | 16 |
| **C2 2-hop** (Gated, valid n=0) | 4,492 | 859 | 5,352 | 133 | 0.0662 | — | — | — | — | — |

Study totals (90 new cells): 566,623 total tokens, **$0.234673**, 90 model
calls, 32 valid / 58 failed (all C2 disclosure failures).

## 2. The C0 → C1 exchange rate

- **Tokens per point of recall lost**: C1 trades recall 0.8833 → 0.8000
  (−8.33pp) for precision 0.7211 → 0.8136 (+9.25pp) and F1 +0.013. The cost:
  **+5,458 mean total tokens/cell (+158%)**, i.e. recall fell 8.3pp for a
  ~2.6× token bill.
- **FN price**: FN rose 14 → 24 (**+10 missed gold files**) while FP fell
  41 → 22 (−19). The graph-hints arm paid for false positives with true
  positives — the opposite of M3's primary objective (reduce FN).
- **Latency paradox**: C1 total latency (265 s) is LOWER than C0 (609 s)
  because completion length stayed tiny (855 vs 809) and prompt-token
  overhead is cheap per call; the cost increase is purely prompt-driven
  (Δprompt +5,412, Δcompletion +46).

## 3. The C2 price of disclosure

- C2 1-hop: +1,178 mean total tokens/cell vs C0 for a disclosure contract
  that the model met 2/30 times (6.7%). The 28 failed cells cost
  **$0.0703** and produced zero usable semantic signal (fail-closed).
- C2 2-hop: +1,903 mean total tokens/cell vs C0, compliance **0/30**,
  cost $0.0662, zero valid cells.
- Combined C2 spend: **$0.1365** (58% of the new-cell budget) returned 2
  valid cells — a poor cost-efficiency outcome for the disclosure mechanism
  as implemented.

## 4. Token composition by treatment

| Condition | prompt share | completion share | driver |
|---|---|---|---|
| C0 | 76.6% | 23.4% | candidate list + policy |
| C1 | 90.4% | 9.6% | **full 562-edge graph block in the prompt** |
| C2 1-hop | 70.5% | 29.5% | zone list (25–41 ids) + seed list |
| C2 2-hop | 83.9% | 16.1% | zone list (111–119 ids) |

The graph treatments shift cost to the **prompt side** (C1 by +5,412
prompt tokens/cell), while completions stay sparse because the model does not
expand its output to cover the mandated zone. This asymmetry is the
mechanistic reason the C2 arms are both costly and non-compliant.

## 5. Recommendation-relevant summary

1. **Graph Hints is a precision product with a recall tax.** Any downstream
   use must accept FP→TP substitution and a ~2.6× token bill; it does NOT
   advance the FN objective.
2. **Graph-Gated Disclosure is not cost-effective at 1-hop and infeasible at
   2-hop** under the sparse schema: 58 cells / $0.1365 for 2 valid cells.
   To make it viable, the zone mandate must match the model's output
   capacity (e.g., smaller zones, an explicit in-zone serialization policy,
   or a separate high-cap allocation for in-zone candidates) — all changes
   are future-design options, not retroactive edits to this frozen study.
3. **S006 economics**: C1 improves S006 F1 0.278 → 0.414 for +~5.4k prompt
   tokens/cell; the single compliant C2-1hop S006 run reached recall 1.0
   with FN 0, but at a compliance rate of 1/5 in that scenario.

Companion: `reports/M3_GRAPH_RESULTS.md`,
`reports/M3_GRAPH_SCENARIO_FAILURE_TAXONOMY.md`,
`reports/M3_GRAPH_HOP_SENSITIVITY.md`.