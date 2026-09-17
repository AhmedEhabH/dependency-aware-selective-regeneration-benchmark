# P2 Phase-1 Major Science Mission — FINAL REPORT

**Date:** 2026-09-18
**Mission:** OPENCODE_P2_PHASE1_MAJOR_SCIENCE_MISSION_2026-09-18
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731
**Verdict:** **P2 Phase-1 = NEGATIVE (frozen, valid scientific result); fixed
Route-B reviewer closure COMPLETE; ZERO new model calls; sealed sets sealed.**

---

## 1. Exact model

`openrouter/deepseek/deepseek-v4-flash-0731`.

## 2. Fixed Route-B closure findings

- **Curve-level POST-HOC characterization**
  (`reports/ROUTE_B_CURVE_LEVEL_POSTHOC_CHARACTERIZATION.md` + JSON): AURC
  (normalized over B∈{0,1,3,5,10}) composite **0.1553** / verifier **0.0971** /
  analytic Random **0.0277**; simultaneous task-bootstrap band (4000 resamples
  of the frozen task unit); per-task recovery distributions; zero-FN tasks
  **10/80 (12.5%)** with explicit denominator handling; macro+micro at every B.
  Frozen macro reproduces the frozen confirmatory numbers EXACTLY (B=5
  composite 0.165). POST-HOC label prominent; never called preregistered.
- Frozen confirmatory decision **CONFIRMS** unchanged.

## 3. Causal parity audit result

**PARITY_VERIFIED** (`reports/SPARSE_FULL_CAUSAL_PARITY_AUDIT.md`): Full-v2 vs
Sparse-v2 match on model/version, provider/route, parent snapshot/candidate
universe, context, temperature/decoding, reasoning mode, completion cap, tools,
repetitions; the ONLY intended treatment difference is the serialization-policy
block (frozen `PROMPT_CONTROLLED_DIFF` PASS 10/10). No invented evidence.

## 4. Operational-definition audit result

**COMPLETE** (`reports/DATASET_OPERATIONAL_DEFINITIONS.md`): exact rules for
"meaningful intent", production-source eligibility, exclusions (canonical code
set), dedup R1/R2/R3, failure/evaluable-task rules, 3-repetition aggregation,
zero-FN handling. Documentation-only; no new dataset.

## 5. P2 harness status

**COMPLETE** — `src/benchmark/p2/` (tasks/cost_model/policies/evaluate) +
`scripts/p2_phase1_run.py` + `scripts/p2_phase1_gates.py`. Frozen anchors
(fixed B={1,3,5,10} composite, BM25, Analytic Random, Oracle, InspectAll);
measured verifier cost model (prompt_tokens≈204.5+7.4·B, cost≈0.000065+
0.000005·B from the 320 frozen confirmatory verifier calls); constants derived
on djangoCMS DEV_TRAIN only; harness reproduces the frozen route_b_v2 / Saleor
transfer fixed-B composite macro ORR within 0.02.

## 6. P2-P1..P4 results per repo

| Policy | djangoCMS B_t / ORR | Saleor B_t / ORR | Classification |
|---|---:|---:|---|
| P2-P1 score-gap | 1.61 / 0.0775 | 1.52 / 0.1151 | NEGATIVE |
| P2-P2 marginal-score | 8.47 / 0.2389 | 9.95 / 0.3173 | NEGATIVE |
| P2-P3 cost-ratio (tau=0.5) | 1.00 / 0.0464 | 9.03 / 0.2918 | NEGATIVE / REJECTED_BY_DESIGN |
| P2-P4 learning-k analogue | 8.45 / 0.2389 | 9.94 / 0.3139 | NEGATIVE |

Anchors for reference: fixed-B5 ORR 0.1633 (djangoCMS) / 0.2369 (Saleor);
fixed-B10 ORR 0.2512 / 0.3173.

## 7. Stronger methods run/not run and why

**NOT RUN.** The pre-registered strong-method gate (lower mean cost than
fixed-B5 AND macro ORR within 5% of fixed-B5 on BOTH repositories) was FALSE
for every policy — each either saved cost but lost >50% of recovery, or matched
recovery at no cost saving. Per mission §4 the negative is frozen and stronger
methods are not implemented (valid scientific result). No neural / RL /
contextual-bandit / active-search system was built.

## 8. P2 Phase-1 gate decision

**NEGATIVE CLOSURE** (frozen). The fixed-B thesis (CONFIRMED) stands intact.

## 9. Selected max-two Phase-2 candidates

**NONE.** Per the P2 common evaluation contract §8, no P2-P1..P4 policy
Pareto-dominates or matches recovery at lower cost on BOTH repos with
uncertainty accounting. Saleor INTERNAL_TEST remains sealed (a possible future
P2 confirmation set ONLY after a policy is frozen — not the case).

## 10. Literature landscape additions

**+15 serious verified entries** (P2-025..P2-039) appended to
`research/literature/p2_algorithm_landscape.csv` (24→39): adaptive computation
(ACT), selective prediction/abstention (SelectiveNet, El-Yaniv & Wiener, Chow),
early-exit cascades (DeeBERT), learning-to-defer, budgeted learning,
Confidence-Budget Matching, fixed-budget ranking & selection, adaptive-kNN
graph (latest Zhang-line), VOI/active search, Wald SPRT. Primary sources
verified via the arXiv API where accessible; classical works marked CLASSICAL;
nothing fabricated; verification status explicit. Landscape report §7 + ledger
updated.

## 11. Semantic-audit human blocker

**AWAITING_HUMAN_RATINGS** (`reports/SEMANTIC_AUDIT_ACTION_REQUIRED_FROM_HUMANS.md`).
Package re-verified (PACKET_INTEGRITY PASS + SYNTHETIC_DRYRUN PASS); 25 blinded
packets, instructions, forms, kappa workflow ready. No fabrication; no coding
time spent rebuilding ready forms.

## 12. NestJS readiness status

**NOT READY TO RUN** (`reports/NESTJS_READINESS_ZERO_API_2026-09-18.md`): repo
reachable, stable tags pinnable (e.g. v10.0.2 `78285da6…`), >=60 eligible-case
rule frozen, TS import extractor NOT implemented, no local cache. No inference.

## 13. Sealed sets untouched (verified)

djangoCMS RESERVE (59), Saleor INTERNAL_TEST (80), Saleor RESERVE (1086) never
loaded (integration-tested). The opened djangoCMS INTERNAL_TEST (80) was used
ONLY for the frozen Route-B reporting (read-only recomputation) — never for P2
tuning/selection. The spent djangoCMS INTERNAL_TEST was never reused as a fresh
P2 test.

## 14. Tests / audits

- 31 new P2 tests (15 policy unit + 10 evaluator unit + 6 integration) PASS.
- Six T3 validation gates PASS (`reports/p2_phase1_gates_validation.json`) +
  independent audit PASS (`reports/P2_PHASE1_INDEPENDENT_AUDIT.md`).
- Full suite: **3334 passed / 33 skipped / 2 pre-existing environmental
  failures** (missing pinned djangocms cache; identical on clean base).
- Ruff clean; mypy strict clean on `src/benchmark/p2`; py_compile clean.
- `git diff --check` clean.

## 15. Git / tag / export

- Scientific closure merge: `248491d` on `main` (branch
  `research/p2-phase1-fixed-routeb-closure-2026-09-18`).
- Tag **`p2-phase1-negative-closure-2026-09-18`** — peel == `248491d` == merge
  commit; **DEVELOPMENT-evidence milestone tag, NOT a stable-tag move**.
- Post-tag tooling/docs merges on `main`: `bbf5005` (LIGHT export script),
  `9007b60` (PROGRESS finalize). HEAD == `origin/main` == `9007b60`.
- LIGHT export: `project-2026-09-18-0141.zip`
  SHA-256 `8851d269b1b71497535dc82cf50047232c806394591bdfc560bfeeef9cf552de`
  (required members `.git/HEAD`, `dist/pilot-kaggle-upload.zip`, `.sha256`
  present).

## 16. ONE next scientific action

Approve/freeze the P2 Phase-1 negative closure with the supervisor, then (a)
decide whether any expanded-landscape Phase-2 candidate (P2-025..P2-039)
deserves further DEVELOPMENT evidence, and (b) unblock the semantic-audit
human ratings (two raters + adjudicator) so the proxy-validity audit can
proceed.