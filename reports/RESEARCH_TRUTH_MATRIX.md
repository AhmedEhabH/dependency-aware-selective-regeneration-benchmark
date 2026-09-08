# RESEARCH TRUTH MATRIX — FROZEN 2026-09-07

Cross-study truth matrix for the Todo research line. Every empirical statement
points to an exact evidence/report path. Frozen by
`RESEARCH_CONSOLIDATION_MAINLINE_01` (consolidation branch
`research/stagec-consolidation-01`).

| # | Study / protocol | Research question tested | Model / provider | Tasks / runs | Correctness result | Efficiency result | Latency result | Evidence SUPPORTS | Evidence DOES NOT support | Status |
| 5 | djangoCMS external-validity selection (`scientific-stagec-djangocms-01`) | Stage-C selection-only accuracy on 6 frozen djangoCMS visible scenarios (144-path universe) | qwen/qwen3-coder @ DeepInfra (pinned, fallback OFF) | 60/60 recorded (6 scenarios x 2 arms x 5 reps); 31 valid / 29 failed (CORRECTED CLOSURE: ImpactPlan 19x 4096-cap truncation + 3x unknown-path + 1x 429 + 1x harness; Agent 4x 429 + 1x empty-selection; no reruns) | Agent 25/30 valid: micro P 0.6463 / R 0.8407 / F1 0.7308, FNR 0.1593; ImpactPlan 6/30 valid: micro P 0.6765 / R 0.9200 / F1 0.7797, FNR 0.0800 (survivor subset only — no between-arm accuracy claim) | VALID-RUN: Agent 432,057 tokens / 198 calls / 2216.0 s / $0.135316; ImpactPlan 32,560 tokens / 6 calls / 382.4 s / $0.018714. ALL-CELL OPERATIONAL: Agent 449,792 tok / 206 calls / 2265.517 s / $0.140850; ImpactPlan 184,401 tok / 28 calls / 2658.733 s / $0.123298 (IP vs A: tok -59.00%, calls -86.41%, cost -12.46%, time +17.36%) | ImpactPlan operational valid rate 20% vs Agent 83.33%; ImpactPlan strong selection-stage inference-work reduction but poor operational completion under frozen 4096 single-response cap; per-run latency recorded; output-budget asymmetry (8x1024 vs 1x4096) + minimal 144-path serialization 17,364 bytes / ~4,341 heuristic-est tokens documented as a validity limitation | Agent reliably selects (25/30 valid, 60% full-recall rate) on hard djangoCMS requirements; impact_plan cap/unknown-path failures are recorded; ImpactPlan efficient when compact | That ImpactPlan is more accurate (24/30 cells failed operationally; 6-run survivor subset not comparable); any end-to-end claim; any general large-repo superiority claim; that truncation is inherent to ImpactPlan rather than partly cap-induced (8192-cap ablation proposed, NOT run) | follow-up |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Historical selective-regeneration pilot (pre-v0.9.22 line) | End-to-end selective regeneration feasibility (motivation/history) | Qwen2.5-Coder-14B-Instruct variants / earlier providers | Historical multi-repo pilot | Old ~42.5% headline result | (historical) | (historical) | Prior motivation for the research line | A current acceptance target; nothing current | historical |
| 2 | v1.1 end-to-end Todo (`scientific-wip-impactplan-v1.1`) | Full end-to-end selective-regeneration pipeline functional correctness on Todo | qwen/qwen3-coder @ DeepInfra (pinned, fallback OFF) | 30/30 attempted, 0 changed-requirement functional passes — end-to-end NO-GO | 0/30 functional passes | ~$0.1789 API cost, tokens/calls per raw records | Per raw records | Downstream exact-patch + source-validity dominance of the first-failure taxonomy (C=10, D=8, E=4, F=7, A=1); NO-GO is preserved | That the impact selector caused 0/30 (selector class A=1 only); any end-to-end success claim | diagnostic |
| 3 | Stage-C smoke selection (`scientific-stagec-selection-01`) | Selection-only impact-selection accuracy on visible-requirement smoke scenarios | qwen/qwen3-coder @ DeepInfra (pinned, fallback OFF) | 30/30 valid (3 scenarios x 2 arms x 5 reps) | Full recall 15/15 per arm; precision/recall/F1 1.0 both arms (ceiling) | ImpactPlan fewer tokens/calls/cost; API cost $0.052696 | ImpactPlan total latency 252.094s vs Agent 147.644s (~70.7% higher); median 13.531s vs 10.281s | Both arms solve smoke selection perfectly on visible requirements; selection-only is NOT the end-to-end bottleneck on these scenarios | That accuracy differs between arms (ceiling); that selection works on hard hidden requirements (not tested here) | exploratory |
| 4 | Stage-C held-out selection (`scientific-stagec-heldout-01`) | Selection-only impact-selection accuracy on hidden user-level requirements without visible file names | qwen/qwen3-coder @ DeepInfra (pinned, fallback OFF) | 60/60 valid (6 held-out scenarios x 2 arms x 5 reps) | Full recall 30/30 per arm (1.0); precision mean Agent 0.8778 vs ImpactPlan 0.7694; F1 Agent 0.9200 vs ImpactPlan 0.8540; FNR 0.0; ImpactPlan over-selects more (write-set 2.60 vs 2.27) | ImpactPlan tokens -72.98%, calls -86.36% (30 vs 220), API cost -47.51%; exact cost $0.104760 | Total latency -51.81% (236.162s vs 490.108s) BUT median Agent 8.211s vs ImpactPlan 6.891s; two Agent outliers (149.468s + 111.406s = 260.874s > 53% of Agent total) materially drive the total | ImpactPlan matches recall with far fewer tokens/calls/cost; ImpactPlan is LESS precise (over-selects); full recall is saturated on the frozen five-file Todo universe; Todo selection precision is NOT saturated | A stable algorithmic latency speedup (median caveat + outliers); any end-to-end correctness claim; any four-class R/P/V/H accuracy claim (gold strongly evaluates R/write-set) | follow-up |

## Interpretation (frozen)

1. The v1.1 end-to-end NO-GO is **preserved**; its first-failure taxonomy shows
   the failures were dominated by downstream exact-patch (C=10) and
   source-validity (D=8) classes, not by the impact selector (A=1).
2. Selection-only accuracy is saturated on **recall** (100% both arms in both
   studies on the five-file Todo universe) but **not** on precision (held-out
   Agent 0.8778 vs ImpactPlan 0.7694 — a measurable between-arm difference).
3. ImpactPlan is substantially cheaper (tokens/calls/cost) at equal recall, but
   less precise; the held-out total-latency advantage (-51.81%) must be reported
   with the median/outlier caveat.
4. `TODO_SELECTION_SATURATED=NO` (per-file selection precision not saturated);
   no further Todo selection scenarios will be added.

Evidence paths: `reports/SCIENTIFIC_MICROSTUDY_V11_RESULTS.md`,
`reports/SCIENTIFIC_MICROSTUDY_V11_DECISION.md`,
`reports/V11_ROOT_CAUSE_TAXONOMY.md`, `reports/STAGEC_SELECTION_01_RESULTS.md`,
`reports/STAGEC_HELDOUT_01_RESULTS.md`,
`reports/STAGEC_LATENCY_DECOMPOSITION.md`,
`docs/STAGEC_FORMAL_MODEL.md`.