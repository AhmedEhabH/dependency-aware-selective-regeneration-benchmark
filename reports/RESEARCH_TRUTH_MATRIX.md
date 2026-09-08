# RESEARCH TRUTH MATRIX — FROZEN 2026-09-07

Cross-study truth matrix for the Todo research line. Every empirical statement
points to an exact evidence/report path. Frozen by
`RESEARCH_CONSOLIDATION_MAINLINE_01` (consolidation branch
`research/stagec-consolidation-01`).

| # | Study / protocol | Research question tested | Model / provider | Tasks / runs | Correctness result | Efficiency result | Latency result | Evidence SUPPORTS | Evidence DOES NOT support | Status |
| # | Study / protocol | Research question tested | Model / provider | Tasks / runs | Correctness result | Efficiency result | Latency result | Evidence SUPPORTS | Evidence DOES NOT support | Status |
| 8 | djangoCMS ImpactPlan-v2 SPARSE COST/SMOKE PROBE (POST-HOC / EXPLORATORY / ONE-SCENARIO) (`scientific-stagec-djangocms-impactplan-v2-costprobe-01`) | Can a SPARSE ImpactPlan-v2 representation (only non-PRESERVE decisions + deterministic omitted=>PRESERVE reconstruction + frozen numeric candidate IDs 1..144) produce a technically valid 144-candidate policy within the original 4096-completion cap, and at what cost/serialization? | qwen/qwen3-coder @ DeepInfra (pinned, fallback OFF), temp 0 | 1/1 v2 probe on djangocms-external-validity-004 (cap 4096; NO Agent; future 30 v2 cells NOT run) | VALID — terminal succeeded, finish_reason=stop, schema-valid, no truncation, 7 explicit decisions decoded to exactly 144 (137 PRESERVE), invalid/duplicate/conflict ids all empty; selection TP4/FP2/FN0, precision 0.666667, recall 1.0, F1 0.8, FNR 0.0, full_recall | 3447 prompt / 1107 completion / 4554 total tokens, 1 call, api cost $0.002141; raw response 4,783 bytes; completion tokens -89.6% vs the 16K diagnostic (1107 vs 10650) on the same scenario | 17.532 s (single call) vs 179.172 s for the 16K full-plan diagnostic on the same scenario | Sparse v2 representation is operationally feasible at the original 4096 cap (no truncation, exactly 144 decoded decisions, schema-valid); deterministic omitted=>P reconstruction works; future 30-run v2 cost lock PASS_FOR_FUTURE_V2_30 ($0.080288 <= $0.20); primary evidence immutable (71/71); six gates + audit PASS pre/post | Any statistical accuracy claim vs v1 (one run, NOT statistically meaningful); any claim that v2 is universally safe via omitted=>P; any claim that prompt/schema effects are isolated (v2 is ONE representation redesign); any claim that the future 30-run v2 evaluation is complete (NOT run) | stopped-for-audit |
| 7 | djangoCMS ImpactPlan FULL-PLAN OUTPUT-SCALABILITY 16K DIAGNOSTIC (POST-HOC / EXPLORATORY / ONE-SCENARIO) (`scientific-stagec-djangocms-impactplan-16k-diagnostic-01`) | Can the current FULL 144-path ImpactPlan representation terminate within a single 16384-completion-token response on one previously truncation-prone scenario (djangocms-external-validity-004)? | qwen/qwen3-coder @ DeepInfra (pinned, fallback OFF), temp 0 | 1/1 diagnostic run (cap 16384; NO 30-run study; NO Agent) | VALID — finish_reason=stop, completion_tokens 10650 (< 16384), schema-valid, no invalid paths; selection metrics TP4/FP5/FN0, precision 0.444444, recall 1.0, F1 0.615385, FNR 0.0, full_recall | Actual completion 10650 tokens (best observed empirical lower bound for THIS scenario); raw response 42,773 bytes/1,314 lines; emitted_entry_count 143/144 (cms/toolbar/utils.py defaulted to PRESERVE); api cost $0.01148 | 179.172 s (single call, 1 model call) | `FULL_PLAN_16K_DIAGNOSTIC=TERMINATES` (CASE A); the full explicit 144-node representation CAN serialize a 144-path plan within a 16384-token single response on this scenario; primary 4096 study unchanged (71/71); 8192 probe evidence unchanged; six gates + audit PASS pre and post | Any claim that 16K fixes ImpactPlan generally, any accuracy claim vs the primary study, any claim that 4096 was cap-only-confounded, any confirmatory-evidence claim | stopped-for-audit |
| 6 | djangoCMS ImpactPlan 8192-cap ablation (POST-HOC / EXPLORATORY) (`scientific-stagec-djangocms-impactplan-cap-ablation-01`) | Did the frozen ImpactPlan 4096 single-response cap materially cause poor operational completion? (budget-matched 8192 arm) | qwen/qwen3-coder @ DeepInfra (pinned, fallback OFF), temp 0 | 1/1 non-study 8192 cost/validity probe on djangocms-external-validity-004; 30-cell ablation NOT launched (probe TRUNCATED) | NOT APPLICABLE — no 30-run ablation evidence; the 8192 probe TRUNCATED at exactly 8192 completion tokens (`finish_reason=length`, unterminated JSON), so no accuracy/completion claim at 8192 | Probe: 2768 prompt / 8192 completion / 10960 total tokens, 1 call, 202.843 s, $0.009022; conservative projected 30-run cost $0.338325 > $0.25 ceiling (COST_LOCK=FAIL) | Probe latency 202.843 s (single call) | `CAP_8192_PROBE_TRUNCATION`; the full 144-path schema-valid serialization still cannot be emitted in one 8192-token response; primary 4096 result NOT shown to be cap-only-confounded; six gates + audit PASS; primary evidence immutable (71/71) | Any claim that 8192 removes truncation or improves completion/accuracy (unanswered); the primary 4096 study is unchanged | stopped-for-audit |
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

## djangoCMS primary-study graph limitation (documented fact)

- The primary djangoCMS ImpactPlan strategy was instantiated **without** the
  frozen dependency graph; the primary djangoCMS study
  (`scientific-stagec-djangocms-01`) characterizes **explicit-plan selection
  WITHOUT dependency-graph assistance**.
- The frozen 144-node / 562-edge AST graph was **NOT strategy-visible evidence**
  in the primary ImpactPlan treatment.
- ImpactPlan-v2 also does NOT inject graph assistance; graph-assisted planning
  is a separate possible future treatment.

Evidence paths: `reports/SCIENTIFIC_MICROSTUDY_V11_RESULTS.md`,
`reports/SCIENTIFIC_MICROSTUDY_V11_DECISION.md`,
`reports/V11_ROOT_CAUSE_TAXONOMY.md`, `reports/STAGEC_SELECTION_01_RESULTS.md`,
`reports/STAGEC_HELDOUT_01_RESULTS.md`,
`reports/STAGEC_LATENCY_DECOMPOSITION.md`,
`docs/STAGEC_FORMAL_MODEL.md`,
`reports/DJANGOCMS_IMPACTPLAN_V2_DESIGN.md`,
`reports/DJANGOCMS_IMPACTPLAN_V2_COSTPROBE.md`.