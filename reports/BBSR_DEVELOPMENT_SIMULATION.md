# Bidirectional Bounded Set Repair (BBSR) — DEVELOPMENT Simulation

**Date:** 2026-09-18
**Tier:** T3 (ZERO API; ZERO LLM; ZERO model calls)
**Mission:** OPENCODE_ORACLE_GAP_BIDIRECTIONAL_REPAIR_MISSION_2026-09-18
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731
**Internal working label only; no novelty claim** (literature check in
`reports/LOCAGENT_FAIR_COMPARISON_PLAN_V2.md` §2 / Section 7 of the final
report).
**Data:** djangoCMS DEV (174) + Saleor DEV (149). Machine-readable:
`reports/bbsr_simulation_result.json`, `reports/oracle_matched_budget_drop_value.json`.

---

## 1. Candidate architecture (development-frozen, ZERO-LLM simulation)

```
Sparse first pass
  -> ADD queue  : top-A omitted candidates by composite (observable)
  -> DROP queue : D lowest-composite currently-selected files (observable)
  -> bounded review (simulated two ways below)
  -> final set
```

Budget: total review K per task, split A + D = K by a deterministic frozen rule
(`half_half`, `add_weighted`, `drop_weighted`). K ∈ {2,4,6,8,10,12}.

Two review modes:
- **Heuristic review (diagnostic, NOT deployment):** add ALL ADD-queue files and
  drop ALL DROP-queue files with no model judgment.
- **Oracle review (upper bound):** add exactly the ADD-queue TPs and drop exactly
  the DROP-queue FPs.

## 2. Results

### Sparse and add-only Route-B references

| Repo | Sparse F1 | Route-B add-only F1 @K=2 | @K=4 | @K=6 | @K=8 | @K=10 | @K=12 |
|---|---:|---:|---:|---:|---:|---:|---:|
| djangoCMS | 0.3177 | 0.2767 | 0.2401 | 0.2152 | 0.1927 | 0.1789 | 0.1642 |
| Saleor | 0.2605 | 0.2665 | 0.2419 | 0.2297 | 0.2059 | 0.1867 | 0.1743 |

### BBSR heuristic (best point per repo)

| Repo | best heuristic | F1 | R | mean inspections/task |
|---|---:|---:|---:|---:|
| djangoCMS | half_half_K2 | 0.2071 | 0.1716 | 1.6954 |
| Saleor | half_half_K2 | 0.2097 | 0.1795 | 1.7248 |

**The heuristic BBSR does NOT improve on Sparse (F1 0.32/0.26) or on add-only
Route-B at matched cost.** Dropping the lowest-composite selected files removes
more TPs than FPs (the observable DROP signal is too weak, Section 4 report),
and adding the composite-top-A omitted files imports more FPs than TPs.

### BBSR oracle (upper bound)

| Repo | best oracle | F1 | R | mean inspections/task |
|---|---:|---:|---:|---:|
| djangoCMS | half_half_K2 | 0.3848 | 0.2465 | 1.6954 |
| Saleor | half_half_K2 | 0.3459 | 0.2115 | 1.7248 |

Even the *oracle* BBSR at low K only reaches ~0.35–0.38, far below the
add-only oracle ceiling (0.87/0.83). The DROP queue adds little value at small
budgets (the matched-budget analysis shows bidirectional only beats add-only at
K ≥ 5, and only under perfect oracle review).

## 3. Matched-budget DROP-value diagnostic (oracle)

| K | djangocms add-only F1 | djangocms best-bi F1 (A,D) | bi>add? | Saleor add-only F1 | Saleor best-bi F1 (A,D) | bi>add? |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 0.5915 | 0.5915 (1,0) | no | 0.5096 | 0.5096 (1,0) | no |
| 2 | 0.7294 | 0.7294 (2,0) | no | 0.6371 | 0.6371 (2,0) | no |
| 3 | 0.7964 | 0.7964 (3,0) | no | 0.7102 | 0.7102 (3,0) | no |
| 5 | 0.8406 | 0.8994 (3,2) | yes | 0.7816 | 0.8135 (4,1) | yes |
| 8 | 0.8674 | 0.9600 (5,3) | yes | 0.8186 | 0.9021 (5,3) | yes |
| 10 | 0.8674 | 0.9834 (7,3) | yes | 0.8270 | 0.9350 (6,4) | yes |

**Finding:** Bidirectional (DROP) only starts to beat add-only at **K ≥ 5**,
and only under **perfect oracle review**. At K ≤ 3 the optimal oracle split is
A=K, D=0 (drop is worthless). This confirms the DROP side is only valuable once
the ADD side has captured most positives AND the reviewer can distinguish FPs
— which the cheap observable rankers cannot.

## 4. Progression gate (pre-registered rule from the mission)

A candidate must, on BOTH djangoCMS DEV and Saleor DEV:
- improve final F1 over Sparse and over add-only fixed Route B;
- not materially degrade recall (≥ 95% of Sparse recall);
- use matched or lower inspection budget;
- show positive direction in most development folds;
- not depend on repo identity or omitted/universe-size artifact.

| Repo | best heuristic | beats Sparse? | beats Route-B? | recall ok? | budget ok? | **gate** |
|---|---|---:|---:|---:|---:|---:|
| djangoCMS | half_half_K2 | no (0.207<0.318) | no | no (0.17<0.25) | yes | **FAIL** |
| Saleor | half_half_K2 | no (0.210<0.261) | no | no (0.18<0.21) | yes | **FAIL** |

**Gate = FAIL on both repos.** No ZERO-LLM heuristic BBSR candidate passes. Per
the mission, no later LLM verifier experiment is authorized.

## 5. Conclusion

- The simple heuristic BBSR is **negative** on DEVELOPMENT: it cannot improve
  file-level F1 over Sparse or over add-only Route-B at matched cost.
- Oracle headroom exists but requires perfect ADD **and** perfect DROP
  discrimination that cheap observable signals do not provide (Sections 2–4).
- Decision classification: **BIDIRECTIONAL_HEADROOM_ONLY** — the oracle surface
  says bidirectional could reach F1 0.85–0.90, but the current cheap observable
  signals are insufficient to realize it. No new verifier calls.

Machine-readable: `reports/bbsr_simulation_result.json`,
`reports/oracle_matched_budget_drop_value.json`.