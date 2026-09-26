# START HERE — Current Research (2026-09-21b)

This file is the entry map. Read it first, then open the referenced documents.
**Terminology:** SIP = Sparse Impact Plan (baseline); RM-CSS =
Repository-Memory Calibrated Set Selection (= SIP + Qwen dense ranking +
parent-only Repository Memory + calibrated ADD/KEEP/DROP). See
`docs/GLOSSARY.md`.

## What this research is

**Question.** Given a real GitHub issue and the repository state at the issue's
parent commit, which files would a developer change? We evaluate the selected
file set against the observed change-set (the actual diff) as an evaluation
proxy. Functional correctness / preservation are deferred until downstream
regeneration.

**Phase.** `Repository change localization / impact selection` — **method
selection CLOSED** (`IMPACT_LOCALIZATION_METHOD_SELECTION_CLOSED`).

## Current position (one paragraph)

WP-1b MAIN_297 (selection-only comparison of a budget-bounded repository
Agent vs SIP vs RM-CSS, protocol v3) is **complete and frozen**:
`RMCSS_NONINFERIOR_AT_LOWER_COST` (decision rules v2, `NI_SUPPORTED`; P n=297
D −0.0062 [−0.0449,+0.0308] Q5 −0.0383; Agent pooled F1 0.363 vs RM-CSS 0.357).
This is a **selection-stage** result, NOT end-to-end correctness. The
post-MAIN_297 scientific closure is done (claim sheet, robustness/limitations,
README/FAQ), the AG16 budget-sensitivity arm is **preregistered but NOT
runnable** (a brain-built/tested harness bundle is required first), and the
WP-2 zero-API MAIN_297 census is complete (297/297 tasks materializable; 20
STRONG / 200 MODIFIED / 77 no-test-evidence F2P candidates; 0 errors). **No E2E
execution has started** — WP-2, E2E-G6 F2P/P2P oracle, Smoke, Pilot and Research
Run remain not started.

<!-- LIVE_STATUS:BEGIN -->

## LIVE STATUS — single current-state source of truth

**Position:** Mission-10A environment test-dependency audit COMPLETE (zero-API). PROVEN declared-but-not-installed: pytest-django-queries + pytest-mock omitted from frozen V2; explains 41/41 P2P-U cap200 COLLECTION_ERROR and 98.7% of py312 C4 error-TOI records. Scratch probe task 1 recovered 18/18 SET A nodes to P2P_ONLY, but SET B non-regression FAILED (1 V2 BEHAVIORAL_F2P node flipped to P2P_ONLY, V2 JWT iat clock-skew flake). DECISION TOKEN = ENV_AUDIT_INCONCLUSIVE; probe stopped per preregistered S2. No generation/Smoke/DEV-47/HOLDOUT/VALIDATION/MAIN execution. MAIN quarantined; INTERNAL_TEST untouched; 786 RESERVE sealed.

**Research pipeline:**

| Step | Status | Note |
| :---|:---|:---|
| Localization method selection | CLOSED | RM-CSS frozen; Saleor-300 PASS (+0.0921 F1) |
| WP-0 leakage fix (G7) | DONE | ArtifactUniverse built from the parent repository |
| WP-1a preparation | DONE | zero API; frozen predictions, manifests, agent protocol |
| WP-1b preflight freeze | DONE | G1 delta=0.05 · G2 cap 1024 · n=297 · budget v2 · rules v2 |
| WP-1b Calibration-3 | DEFECT | v1 gate PASS, $0.081, 24 calls — 0 successful reads; INSTRUMENT_INVALID |
| Tool-budget fix + gate v2 | DONE | D2: search_text does not consume the 30-file budget; CG-10/CG-11 written; RED on Calibration-3 |
| WP-1b Calibration-3b | PASS | gate v2 PASS · $0.070 · 3 reads · 0 instrument errors · 11/21 calls rejected repeats (loop) |
| G12 agent context hygiene | DONE | D1 APPROVED, zero API: echo, call counter, named rejection, truncation note; gate v3 CG-12 FAILS 3b (runs 1/6/4); protocol v3 |
| WP-1b Calibration-3c | PASS | gate v3 CG-1..CG-12 PASS · $0.063205 · 4 reads · 1/18 rejected (5.6%) · longest run 1 · 0 blocking review-card flags · NOT scored |
| WP-1b MAIN_297 + variance 15x3 | DONE | RMCSS_NONINFERIOR_AT_LOWER_COST (NI_SUPPORTED); main $7.15 + variance $1.19; scored with decision rules v2; X1-X11 exploratory |
| WP-1b post-MAIN_297 docs closure + claim sheet | DONE | claim sheet, robustness/limitations, README/FAQ updated; zero API |
| AG16 budget sensitivity (MAIN_50) | PREREGISTERED, NOT RUNNABLE | brain-built/tested bundle required first (iterative_agent_budget.py + golden parity + dry-run); ceilings $0.80 cal / $12.20 MAIN_50 |
| WP-2 zero-API MAIN_297 census | DONE | 297/297 materializable; 20 STRONG / 200 MODIFIED / 77 no-test-evidence F2P candidates; proposal-only Smoke candidates 8; zero API |
| WP-2 Oracle Confirmation + Design v1 | DONE (zero-API) | harness validated; 220/220 changed-test candidates attempted; 8 primary behavioral F2P + 1 symbol-absence eligible; causal Design v1, power planning, Smoke v2 emitted; environment-dominant blocker on this host |
| WP-2 shared E2E instrument | NOT STARTED | same generator/validator/repair for every arm |
| E2E Smoke → Pilot → Research Run | NOT STARTED | staged; each stage can stop the run |
| WP-2 preservation oracle (P2P-S + P2P-U V2) | FROZEN (Mission-09) | P2P-S 46/47 defined; P2P-U V2 rule+membership frozen; ENG cap200+cap400 executed, repeatability 1.0 |
| Mission-10A environment test-dependency audit | DONE (ENV_AUDIT_INCONCLUSIVE) | proven pytest-django-queries/pytest-mock declared-but-not-installed in V2; 41/41 P2P-U cap200 COLLECTION_ERROR explained; probe recovered 18/18 SET A but SET B non-regression failed (1 V2 node flip, JWT iat clock-skew); STOP probe; no V3 |
| Full DEV-47 P2P-U cap200 execution | NOT STARTED (awaits approval) | est ~4.9-8.1 h serial central 6.7 h; overnight-feasible with resume; zero-node tasks UNDEFINED |

**LLM-call accounting:**

| Workflow | Calls | Note |
| :---|:---|:---|
| SIP on Saleor-300 | 300 coder calls (1/task) | 315 HTTP attempts incl. retries · 5.09 M tokens · $1.593 |
| RM-CSS on top of SIP | 0 extra coder calls | local logistic regression + repository memory |
| Qwen embeddings (RM-CSS) | 33 batched calls | 2,076 file units + 299 queries · $0.026 |
| WP-1b Calibration-3 agent | 24 calls (8/task) | $0.081 · 7 of 24 were rejected repeats · 0 successful reads (INSTRUMENT_INVALID) |
| WP-1b Calibration-3b agent | 21 calls (5/8/8) | $0.070028 · 3 successful reads · 0 instrument errors · gate v2 PASS · loop: 11/21 rejected repeats |
| WP-1b G12 (zero API) | 0 | agent context hygiene amendment D1 APPROVED: echo, call counter, named rejection, truncation note; gate v3 CG-12 FAILS 3b |
| WP-1b Calibration-3c agent | 18 calls (4/8/6) | $0.063205 · 4 successful reads · 1/18 rejected repeats (5.6%) · longest run 1 · gate v3 CG-1..CG-12 PASS · NOT scored |
| MAIN_297 agent | 2,164 logical / 2,178 HTTP attempts | ledger $7.147 · 23.55M prompt / 81.7K completion tokens · 147 forced finals · 2 EMPTY (parser_failure) · 8 transport retries |
| Variance substudy 15x3 | 331 logical / 341 HTTP attempts | ledger $1.194 · pooled F1 0.389/0.438/0.479 · pairwise exact match 0.444 · 0 EMPTY |
| WP-2 zero-API MAIN_297 census | 0 | deterministic read-only git diff over already-opened case metadata; $0.00 |
| E2E generation + repair | not frozen yet | defined by WP-2 |

**Authorized / not authorized:**

| Item | Status | Note |
| :---|:---|:---|
| Calibration-3c | DONE (CLEAN) | gate v3 CG-1..CG-12 PASS; $0.063205; NOT scored |
| MAIN_297 + variance 15×3 + scoring | DONE (D3 = YES) | RMCSS_NONINFERIOR_AT_LOWER_COST (NI_SUPPORTED); main $7.15 + variance $1.19; predictions frozen/tagged before any label load |
| Agent budget-sensitivity arm (AG16, MAIN_50) | PREREGISTERED, NOT AUTHORIZED; runner NOT built | design frozen before MAIN_297 outputs; needs brain-built/tested bundle + decision D6 |
| WP-2 zero-API MAIN_297 census | DONE | deterministic planning evidence only; no E2E execution; no F2P/P2P oracle |
| WP-2 Oracle Confirmation (zero-API) + Design v1 | DONE | 8 primary behavioral F2P + 1 symbol-absence eligible confirmed; causal Design v1 + power planning + Smoke v2 proposal; NO E2E execution |
| 786 Saleor RESERVE outcomes | SEALED | never opened/read/scored/sampled; guarded by the label-access audit hook |
| Calibration-3 / 3b / 3c F1 claims | NOT PERMITTED | instrument checks only; no labels loaded or scored |
| Mission-09 P2P-S + P2P-U V2 freeze | DONE | zero-API; P2P-S (46/47) + P2P-U V2 rule/membership frozen before any V2 outcome execution |
| Mission-09 ENG P2P-U V2 execution (cap200 + cap400) | DONE | 8 executable ENG tasks x 2 caps, workers=1, 3+3 reps, integrity PASS; no Smoke/full-DEV/MAIN execution |
| Mission-10A environment test-dependency audit (zero-API, Tier T3) | DONE (ENV_AUDIT_INCONCLUSIVE) | proven declared-but-not-installed dev/test group in frozen V2; ENG-only scratch probe (task 1) recovered 18/18 SET A; SET B non-regression FAILED (1 V2 BEHAVIORAL_F2P node flip) -> STOP per preregistered S2; no V3 build, no generation, no Smoke |
| Full DEV-47 P2P-U cap200 + Smoke freeze | NOT AUTHORIZED | requires Ahmed decision; estimates ready (DEV ~6.7 h central) |

**Next action:** Ahmed decision (ENV_AUDIT_INCONCLUSIVE): approve targeted follow-up = (1) V2 BEHAVIORAL_F2P node flakiness audit (JWT iat clock-skew class), (2) complete probe task 2 + SET B under clock-skew-robust harness, (3) re-decide V3/V2/INCONCLUSIVE. No generation, Smoke, DEV-47, HOLDOUT, VALIDATION, or MAIN execution.

**End-to-end status:** WP-2 has **not started**; E2E-G6 F2P/P2P oracle has **not started**; **no** E2E Smoke, Pilot or Research Run exists yet.

*Source: `docs/LIVE_STATUS.json` (schema `live_status_v1`), rendered by `scripts/render_live_status.py`. As of 2026-09-26 (Africa/Cairo).*
<!-- LIVE_STATUS:END -->

## Key facts

- **MAIN_297 result (frozen):** `reports/wp1b_main297_result.json` +
  `reports/WP1B_MAIN297_RESULT.md` →
  `RMCSS_NONINFERIOR_AT_LOWER_COST` (NI_SUPPORTED; tag
  `wp1b-main297-result-2026-09-22`).
- **Claim sheet:** `docs/WP1B_CLAIM_SHEET_2026-09-22.md` (allowed/forbidden
  sentences + caveats).
- **AG16 readiness:** `docs/WP1B_AG16_READINESS_2026-09-22.md` +
  `exports/WP1B_AG16_BRAIN_HANDOFF_2026-09-22/` (prereg verified; runner NOT
  built; brain bundle required).
- **WP-2 census:** `docs/WP2_MAIN297_ZERO_API_CENSUS_2026-09-22.md` +
  `research/wp2/` (297/297; zero API).
- **Impact declaration:** `docs/WP1B_POSTMAIN_WP2_CENSUS_IMPACT_DECLARATION_2026-09-22.md`.

## Authorized / not authorized

- **AUTHORIZED now:** WP-2 zero-API MAIN_297 census (DONE); WP-1b docs closure
  and claim sheet (DONE); AG16 readiness/preparation only.
- **NOT authorized:** AG16 paid execution (preregistered; needs brain-built
  tested bundle + decision D6); WP-2 execution; F2P/P2P oracle; E2E
  Smoke/Pilot/Research Run; any new post-hoc statistical invention.
- **Never:** read/open/score/sample the 786 unread Saleor RESERVE outcomes.

## Where to go next

1. `docs/WP1B_POSTMAIN_WP2_CENSUS_STOP_REPORT_2026-09-22.md` (this mission's STOP report).
2. `DECISIONS.md` (D1..D8 decision block, 2026-09-22).
3. `PROGRESS.md` (execution source of truth).