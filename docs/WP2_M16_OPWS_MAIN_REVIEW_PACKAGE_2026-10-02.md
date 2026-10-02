# WP2 M16 — OPWS-MAIN Review Package (design only, nothing executed)

> **SUPERSEDED by v2 (`WP2_M16_OPWS_MAIN_REVIEW_PACKAGE_v2_2026-10-02.md`) and the frozen design (`WP2_M16_DESIGN_FREEZE_2026-10-02.md`).** Kept unchanged below as the review record. Its H2 non-inferiority hypothesis, margin and NI/EQUIVALENT tokens were WITHDRAWN by review v2 (Q4b) and are never issued by the kit.

Date: 2026-10-02 · Author: brain (Claude) · Status: **REVIEW DRAFT — not frozen, not installable**

Scope of this document: a feasibility audit from existing artifacts plus a proposed design, a go/no-go recommendation and the scientific questions that must be settled before any freeze. **No experiment, no Docker, no model/API call, no installer and no controller was built or run** to produce this package. M15-R is treated as closed with `M15R_GOLD_FLOOR_FAIL_NO_GENERATION_CLAIM`; none of its artifacts is modified or re-interpreted here.

> Brain attestation (leakage): while preparing this package I did **not** compute any selector-vs-gold overlap (coverage class, recall, F1, P_S) on any MAIN task subset. Only selector-blind quantities (set sizes, empties, era, gold-patch structure, oracle node counts) were computed. The WP1b 297-task aggregate F1 was already public in the WP1B claim sheet.

All counts below were computed on the brain-side repository snapshot (`/tmp/claude-0/s/PAW`). The installer must re-verify every hash against the real repository (section 13).

---

## 0. Executive summary

* **The 71 "eligible" MAIN tasks are a harness-V2 product; M16 must evaluate with the frozen harness V3.** On ENG, moving from V2 to V3 changed primary eligibility from 8 to 14 (7 kept, 1 lost to install blocking, 7 newly eligible). This happened because V2 omitted dev/test dependencies and ignored lockfiles.
  * The V2 MAIN env failures are concentrated in 2024–2025: 23/32 and 30/43 attempted tasks failed. The phase-1b install-failure audit classifies all 60 C2 env failures as `LOCKFILE_INCOMPATIBILITY` with `v3_repair_plausible = true`. This is a projection from frozen metadata, not execution evidence, and 27 of the 60 also cite a native weasyprint/pango dependency chain.
  * Using the V2-71 list would therefore bake a known instrument defect into the sampling frame.
* **Recommendation: CONDITIONAL GO (Route B).**
  * Re-derive MAIN eligibility under V3 on the full frozen, selector-blind oracle selection (220 tasks).
  * Run selector-blind readiness.
  * Evaluate the **entire** READY census, with no sampling and no cherry-picking.
  * Estimate the paired difference in OPWS_ROBUST sufficiency between the **frozen WP1 RM-CSS selection** and the **frozen WP1 Agent main-run selection**.
  * Zero model API throughout.
* **Classical power is not the right frame.** n is fixed by the census (projected ~45–110 READY tasks). Under plausible discordance, the 95% CI half-width is about ±0.06 to ±0.14. The design is therefore **estimation-first**: a pre-declared CI-position decision rule against margins 0 and ±0.10, with power-style operating characteristics reported honestly (section 6).
* **What makes M16 new rather than "M15-R on more tasks"** (section 16):
  * it uses the exact selections behind the WP1 NI claim;
  * it is a census of an independent pool;
  * it uses inferential paired statistics;
  * it pre-registers a coverage decomposition, OPWS = P(FULL) + P(PARTIAL ∧ pass), with partial-coverage rescue estimated with CIs;
  * it pre-registers a transportability link back to the 297-task WP1 result.
* **Decisions needed before freeze:** 11 open questions (section 18). Q1–Q4 are blocking.

---

## 1. Feasibility audit — available → eligible → evaluable → sampled

### 1.1 Available (selections that exist and are frozen)

| Selector | Source artifact | Tasks with a selection | Empty selections | Replicates | Frozen when |
|---|---|---|---|---|---|
| RM-CSS (realization A, threshold 0.2) | `research/wp1a/sip_rmcss_per_task_predictions.json`, field `rmcss_predicted_set`; deployment `research/stage5-v2-final/deployment_artifact.json` (config sha `8925d29a…`) | 297/297 | 29/297 | 1 (deterministic L2-LR over stored SIP predictions; replicates are meaningless) | generated 2026-09-21, before any MAIN oracle execution |
| Agent (qwen/qwen3-coder, T = 0.0, `wp1b_frozen_agent_protocol_v3`) main run | `research/wp1b/main-297-2026-09-22/agent_run_records.jsonl` (`selected_paths`) and `wp1b_agent_predictions.json` | 297/297 | 2/297 (`parser_failure`: `094b1ec0f610`, `37a3a7bbec31`); 0 infra | 1 (`replicate = 0`) | 2026-09-22T08:52Z |
| Agent variance substudy | `research/wp1b/variance-15x3-2026-09-22/` | 15 (all among the first 50 of MAIN) | 0 | r1–r3. The WP1b prereg states that the main run is **not** replicate 1 | 2026-09-22 |
| SIP (qwen) | same WP1a file, `sip_predicted_set` | 297 | n/a | 1 | not an M16 arm (optional descriptive) |

* OOF_A (`final_oof_predictions_A.json`, 323 DEV/holdout tasks) has **0** MAIN overlap and is not usable as an M16 source.
* Protected pools (INTERNAL_TEST 80, RESERVE) are untouched and not used. Pilot-A/B tasks have 0 overlap with MAIN.

### 1.2 Eligible (oracle exists — current evidence is harness V2)

```
MAIN_297
 ├─ 77  NO_CHANGED_TEST_EVIDENCE        → structurally excluded (no changed-test F2P possible)
 └─ 220 attempted (frozen oracle selection: FROZEN_BEFORE_ORACLE_EXECUTION; 20 STRONG + 200 MODIFIED)
     ├─ 60  ENV_INSTALL_FAILED (V2)
     └─ 160 executable
         ├─ 71  PRIMARY_BEHAVIORAL_F2P_ELIGIBLE   ← V2 "eligible" (5 of these also carry symbol-absence nodes)
         ├─ 12  symbol-absence-only F2P            → excluded (consistent with M14R/M15-R behavioral-only oracle)
         └─ 77  no F2P (neither behavioral nor symbol)
```

Profile of the V2-eligible 71. All quantities are selector-blind.

* **Era:** py39 39, py312 31, py38 1.
* **Target year** (from the 220 attempted strata):

  | Year | Eligible / attempted |
  |---|---|
  | 2020 | 1/21 |
  | 2021 | 1/42 |
  | 2022 | 19/26 |
  | 2023 | 19/34 |
  | 2024 | 3/32 |
  | 2025 | 11/43 |
  | 2026 | 17/22 |

* **F2P nodes per task:** median 2 (range 1–169); 25 tasks have exactly 1 node and 35 have ≥ 3.
* 67/71 tasks have P2P_ONLY nodes (P2P-S source), 5/71 have FLAKY nodes and 21/71 have TARGET_ORACLE_INVALID nodes.
* **Gold structure, eligible 71 vs complement 226:**

  | Property | Eligible 71 | Complement 226 |
  |---|---|---|
  | Mean GOLD_HARD size | 3.04 | 3.93 |
  | Tasks with added non-test files | 4/71 | 32/226 |
  | Tasks with migration files | 4/71 | 33/226 |

  **The eligible set is structurally easier** (smaller gold, fewer added files).
* **Selector-blind selection sizes on the 71:**
  * RM-CSS: mean 2.52, **4 empty**.
  * Agent: mean 2.37, 0 empty.
* **Overlap with the Agent variance subset:** 7/15 tasks (`032b98afff20`, `07c8859c0ac3`, `0f16ed78b02b`, `11756ee6b65a`, `14f2176b5d8c`, `1f9b5c53a63a`, `22a30bf2e4cc`).

**Why the V2 list cannot be the frame for a V3 evaluator** (evidence from `research/wp2/mission10a_env_audit_2026-09-26/` and `research/wp2/harness_v3_2026-09-26/`):

* V2 installed production dependencies only. `pytest-mock` and `pytest-django-queries` were missing, which produced `MISSING_FIXTURE:mocker` and `count_queries` error nodes.
* V2 ignored `poetry.lock` (`LOCKFILE_INCOMPATIBILITY`).
* The V3 probe showed a V2 BEHAVIORAL_F2P node turning into P2P_ONLY.
* The ENG C4-V3 rerun gave: 8 V2-primary → 7 kept + 1 `ENV_INSTALL_BLOCKED`; 7 V2-NOT_PRIMARY → BEHAVIORAL_F2P.
* V3 still blocks some installs (7/29 on ENG).

### 1.3 Evaluable (unknown until V3 oracle construction + readiness — **not assumed**)

* Evaluable = V3-eligible ∧ READY. READY means both:
  * the negative control (empty diff) fails strict F2P and preservation is PASS/UNDEFINED;
  * the positive control (gold restricted to GOLD_HARD) is RESOLVED_ROBUST.
* Readiness yield precedents (different pools, indicative only): Pilot 20/26 = 0.77, ENG 13/14 = 0.93.
* Projections (not claims):
  * **Route A** (V2-71 re-confirmed under V3): about 71 × 0.875 (V3 retention, ENG 7/8) × 0.77–0.93 ≈ **48–58 READY** (envelope 45–60).
  * **Route B** (V3 on the 220): V3-eligible is unknown. If the ENG ratio (14/8) transferred it could reach ~110–125 eligible, but MAIN's 2020–2021 tasks are low-yield for reasons that may not be dependency-related. A plausible range is **60–110 READY**.

### 1.4 Actually sampled

**All READY tasks (a census).**

* There is no random subsampling, no stratified selection and no manual inclusion or exclusion.
* Every exclusion before scope freezing is selector-blind: oracle and readiness use only gold, empty diff and tests.
* Exclusions are reported with reasons.

---

## 2. Research question and estimand

**RQ.** On Saleor MAIN tasks with a valid behavioral oracle: when the developer's own non-test patch is restricted to the files a **frozen** selector allowed, how often does it still pass the hidden tests robustly? Does that execution-grounded sufficiency differ between the WP1 RM-CSS selection and the WP1 Agent selection?

**Population.** T* = MAIN_297 tasks that are V3-primary-behavioral-eligible and READY. This is a finite census. CIs are interpreted under a superpopulation model: comparable Saleor tasks whose eligibility mechanism is the same.

**Unit.** Task t. Arms: S ∈ {RMCSS, AGENT_MAIN}, plus GOLD as the reference.

**Outcome.** Y_S(t) = OPWS_ROBUST ∈ {0, 1} (section 4).

**Primary estimand.**
* θ_S = (1/|T*|) Σ_t Y_S(t)
* **δ = θ_RMCSS − θ_AGENT_MAIN** (paired, same tasks)

**Structural decomposition** (pre-registered; exact, not modeled):
* θ_S = P(FULL_S) + P(PARTIAL_S ∧ Y_S = 1)
* FULL → Y = 1 by construction (P_S equals the scoped gold, so the readiness positive is reused).
* NONE → Y = 0 by construction (P_S is empty).
* Only PARTIAL items carry new execution information. **π_S = P(Y_S = 1 | PARTIAL_S)** is the "partial-coverage rescue rate".

**Known limitation of the Agent arm.** It is a single stochastic run (T = 0 but provider-nondeterministic: M15-R replicate agreement was 7/10). The δ CI does not include Agent run-to-run variance. This is quantified only descriptively on the replicate overlap (section 8).

---

## 3. Hypotheses (declared before any MAIN coverage or OPWS outcome is seen)

**H1 (primary, estimation).**
* Estimate δ with a 95% CI.
* There is no directional prior. WP1 found pooled F1 D = −0.0062 [−0.0449, 0.0308]; M15-R (n = 10, a different pool) found RMCSS 3/10 vs Agent r1–r3 2, 3, 2 out of 10.
* The decision token follows the CI-position rule in section 6.

**H2 (secondary, confirmatory under the same CI).** RM-CSS is non-inferior to the Agent on OPWS_ROBUST at **Δ = 0.10**: the lower 95% bound of δ is > −0.10. This is the CI-inclusion principle, so no extra multiplicity is introduced.

**H3 (secondary, proxy validity).**
* For each selector, π_S > 0, i.e. file-level "full coverage" understates execution sufficiency. Report π_S with a Clopper–Pearson 95% CI.
* M15-R observed 8/22 PARTIAL items passing, but that is on a different pool and is used here only as motivation, not as a threshold.

**H4 (secondary, transportability of WP1).**
* The sign of the WP1 per-task F1 difference (RMCSS − Agent) on T* agrees with the sign of δ.
* The F1 difference on T* lies within the WP1 297-task CI.
* Both quantities are computed post-freeze by the controller.

**E1–E3 (exploratory, no claims).**
* E1: strict-vs-robust discordance.
* E2: Agent replicate behaviour on the overlap subset.
* E3: sufficiency per editable file / character (over-selection is not penalized by OPWS; cost is reported separately).

---

## 4. Exact definitions

These definitions are inherited unchanged from M15-R/M14R. The only change is the MAIN evaluator sets.

* **E_S(t), the editable set of selector S.**
  * RMCSS: `rmcss_predicted_set`.
  * AGENT_MAIN: `selected_paths` of the WP1b main-run record.
  * Both are normalized by the frozen scope builder used in M15-R (`benchmark.wp2.e2e.scopes`), applied unchanged.
* **G(t) = GOLD_HARD raw.** Non-test files with status modified or deleted between parent and target. **Added and renamed files are excluded**, as in Smoke, Pilot-A, M14R and M15-R (limitation, section 17).
* **P_S(t)** = the gold non-test diff restricted to E_S(t) ∩ G(t).
* **Coverage class.**
  * FULL ⇔ G ⊆ E_S.
  * NONE ⇔ E_S ∩ G = ∅. This includes an empty E_S, which is a selector outcome, not an exclusion.
  * PARTIAL otherwise.
* **Evaluation.**
  * Apply P_S plus the target test changes to the parent.
  * Use the frozen evaluator (materialize + evaluate, 3 repetitions, fresh DB, workers = 1) with **M14A-E1 + M15R-E1A1 startup semantics**.
  * Use the MAIN V3 evaluator sets: F2P behavioral, P2P-S, and P2P-U200 (if Q3 = yes).
* **OPWS_ROBUST = 1** iff:
  * every behavioral F2P node passes in all 3 repetitions; **and**
  * no P2P-S/P2P-U200 node is non-passing in ≥ 2 of 3 repetitions (preservation PASS or UNDEFINED).
* **OPWS_STRICT = 1** iff every F2P node passes 3/3 **and** no P2P node is non-passing in any repetition (Smoke v2.2, D50–D52).
* **Reuse rules.**
  * Empty P_S → 0 without evaluation.
  * P_S byte-identical (core identity) to the readiness scoped gold → reuse the readiness positive result.
  * Identical P_S across selectors on the same task → one evaluation shared by identity.

---

## 5. Paired analysis

**Primary table** (one row per task in T*):

|  | AGENT = 1 | AGENT = 0 |
|---|---|---|
| **RMCSS = 1** | a | b |
| **RMCSS = 0** | c | d |

* δ̂ = (b − c)/n.
* **CI: Tango asymptotic score interval** for paired differences (Tango 1998), one of the three intervals recommended by Fagerland et al. (2014), together with the Bonett–Price Wald and Newcombe square-and-add intervals.
* **Sensitivity:** Newcombe hybrid-score interval (method 10; Newcombe 1998).
* **Test:**
  * exact conditional McNemar, two-sided (binomial b | b + c; McNemar 1947), as the conservative primary;
  * **mid-p McNemar** co-reported, since Fagerland, Lydersen & Laake (2013) show that the exact conditional test is overly conservative.
* **Coverage cross-table** (3 × 3: RMCSS class × Agent class), with the OPWS pass count in each cell.
* **Disagreement table:** a per-task listing of every discordant task (b and c cells), with E_S sizes, coverage classes, F2P node count, era and taxonomy of the failing side (ZERO_F2P / PARTIAL_F2P / PATCH_STARTUP / PRESERVATION).
* **Per selector:**
  * θ_S with a Clopper–Pearson CI (Clopper & Pearson 1934);
  * P(FULL), P(PARTIAL), P(NONE);
  * π_S with a CP CI;
  * mean file-level P/R/F1 against G;
  * editable files and characters.
* **GOLD reference:** must be |T*|/|T*| by construction. Any deviation is an instrument STOP.
* **Strict vs robust:** report both primaries and the discordance count (M15-R: 0/34).

---

## 6. Sample size, power, and why the design is estimation-first

n is not a design choice: it is the READY census of a fixed, frozen pool. A classical a-priori power calculation would have to pick n, which we cannot do without cherry-picking or touching protected pools. Operating characteristics are reported instead.

Normal approximation, SE = √(ψ/n), where ψ is the discordant-pair rate. **This is an approximation, not a claim.** M15-R suggests ψ ≈ 0.1–0.3 (RMCSS vs Agent majority discordant on 1/10; vs single replicates r1/r2/r3 on 1/0/3 of 10).

| n READY | ψ | 95% CI half-width (δ = 0) | P(show NI at 0.10 \| δ = 0) | P(show NI at 0.10 \| δ = +0.05) | MDE at 80% power, two-sided |
|---|---|---|---|---|---|
| 40 | 0.10 / 0.20 / 0.30 | 0.098 / 0.139 / 0.170 | 0.52 / 0.29 / 0.21 | 0.86 / 0.57 / 0.41 | 0.14 / 0.20 / 0.24 |
| 60 | 0.10 / 0.20 / 0.30 | 0.080 / 0.113 / 0.139 | 0.69 / 0.41 / 0.29 | 0.96 / 0.74 / 0.57 | 0.11 / 0.16 / 0.20 |
| 80 | 0.10 / 0.20 / 0.30 | 0.069 / 0.098 / 0.120 | 0.81 / 0.52 / 0.37 | 0.99 / 0.86 / 0.69 | 0.10 / 0.14 / 0.17 |
| 100 | 0.10 / 0.20 / 0.30 | 0.062 / 0.088 / 0.107 | 0.89 / 0.61 / 0.45 | 1.00 / 0.92 / 0.79 | 0.09 / 0.13 / 0.15 |
| 120 | 0.10 / 0.20 / 0.30 | 0.057 / 0.080 / 0.098 | 0.93 / 0.69 / 0.52 | 1.00 / 0.96 / 0.85 | 0.08 / 0.11 / 0.14 |

A Monte-Carlo check of exact-McNemar power (1500 simulations per cell) agreed: for example, n = 60, ψ = 0.2, δ = 0.10 gives power ≈ 0.30.

Consequences:

1. **NI at Δ = 0.05 (the WP1 margin) is infeasible** for a binary endpoint at any achievable n: it needs n ≈ 300–600 at ψ = 0.1–0.2.
2. Δ = 0.10 is attainable only with low discordance and/or n ≥ 80. This is a further reason to prefer Route B.
3. **Pool gate.** If n_READY < 40, the outcome is `M16_POOL_INSUFFICIENT_DESCRIPTIVE_ONLY`: all statistics are reported but no CI-position token is issued.

**CI-position decision rule** (single 95% Tango CI [L, U]; tokens are mutually exclusive; evaluated in this order):

| Condition | Token |
|---|---|
| L > 0 | `M16_RMCSS_MORE_SUFFICIENT` |
| U < 0 | `M16_AGENT_MORE_SUFFICIENT` |
| −0.10 < L and U < 0.10 | `M16_EQUIVALENT_WITHIN_0.10` |
| L > −0.10 (and U ≥ 0.10) | `M16_RMCSS_NONINFERIOR_0.10` |
| otherwise | `M16_INCONCLUSIVE` |

Notes:
* The equivalence token deliberately uses the 95% CI, which is stricter than the usual 90% CI / TOST convention.
* H2 (L > −0.10) can hold together with the EQUIVALENT, RMCSS_MORE or even AGENT_MORE token. The H2 status is therefore always reported alongside the token.

---

## 7. Eligibility criteria (all selector-blind, all fixed before scope materialization)

1. t ∈ MAIN_297 manifest (`task_ids_sha256 1678dbaa…`), excluding the 3 Calibration-3 tasks (already absent).
2. t ∈ the frozen oracle selection (220; changed-test evidence).
3. The V3 environment installs (C4-V3 status not `ENV_INSTALL_BLOCKED`).
4. V3 classification is `PRIMARY_BEHAVIORAL_F2P_ELIGIBLE` (≥ 1 behavioral F2P node; symbol-absence-only excluded).
5. READY: the negative and positive controls pass (section 1.3).
6. Not in any protected pool (re-verified), and not in Pilot-A/B, ENG or M14R.

No criterion may reference E_S, P_S, coverage, WP1 F1 or any selector output.

---

## 8. Agent replicates

* **Primary Agent arm = the WP1b main run (replicate 0).** This is the selection on which the WP1 NI claim rests, and it exists for all 297 tasks at zero additional API cost.
* **Replicates r1–r3** exist only for the 15-task variance subset. Overlap with T*: 7 under V2. Under Route B it can reach 13, because 6 of the 15 variance tasks are in the 220 but were not V2-eligible (4 NOT_PRIMARY, 2 env-failed); 2 are outside the 220. On that overlap only:
  * each replicate is evaluated separately (OPWS for r1, r2, r3);
  * **outcome-majority** (≥ 2 of 3 replicates OPWS-pass), the same definition as M15-R;
  * **expected sufficiency** = mean over r1–r3;
  * agreement (k/n tasks where all 3 agree) and mean pairwise Jaccard of E_S.
* Main-run vs r1–r3 comparisons are descriptive. The WP1b prereg forbids treating the main run as replicate 1, so the main run is **not** pooled into the majority.
* **Scope-consensus** (files chosen by ≥ 2/3 replicates) would be a new selector that WP1 never froze. It is not computed.
* Fresh Agent replicates on all of T* would cost roughly 3 × $0.024 × n ≈ $5–8. That would break zero-API and the "frozen WP1 selection" link, so it is out of scope for M16 (an optional later M16b; Q6).

---

## 9. Infra, flaky and unresolvable policies (fixed before running)

| Situation | Policy |
|---|---|
| Env install blocked under V3 | Task ineligible (criterion 3); reported by era and year. Not an oracle negative. |
| Flaky nodes at oracle construction | Excluded from F2P by the frozen C4 classification (FLAKY). |
| F2P intermittent under the **positive** control | Task NOT_READY (selector-blind). No node pruning after readiness. |
| Negative control passes F2P | Task NOT_READY (oracle not behavioral under V3). |
| Positive scoped gold fails (e.g. needs an added file) | Task NOT_READY; reported with gold structure (added files / migrations). |
| F2P intermittent under a selector's P_S | Scored by the frozen rule (F2P requires 3/3, so robust = 0). No reruns. |
| Evaluation infrastructure error | Resumable STOP; retry the same identity; **never scored as FAIL**. |
| Infra unresolved after 2 resumptions | Human decision. If dropped, the task is removed **for all selectors** (listwise, preserving pairing) and listed. |
| Dropped tasks > 10% of READY | `M16_INSTRUMENT_REVIEW`: no CI-position token. |
| `INFRA_UNCLASSIFIED` startup failure not covered by E1/E1A1 | STOP. An amendment may only map INFRA → FAIL classes, never FAIL → PASS; it must be selector-agnostic; every amended item is listed and a sensitivity analysis excludes amended items. |
| Selector empty set | NONE coverage → Y = 0 (a selector outcome, not an exclusion). |

---

## 10. Stopping rules

1. **No outcome-based interim looks.** The controller must not print or persist per-selector pass counts before the final analysis phase. Progress output shows only item counts.
2. **Instrument stops:**
   * the GOLD OPWS identity differs from the readiness scoped gold;
   * a GOLD OPWS outcome ≠ 1;
   * frozen-hash drift;
   * protected-pool access;
   * the quarantine decision record is missing.
3. **Pool gate** after the readiness freeze: n_READY < 40 → descriptive-only (section 6).
4. **Resource HOLD:** C free < 15 GB, or the D: cold root unavailable → HOLD, resumable.
5. **No early termination for efficacy or futility.** The census always completes.

---

## 11. Leakage barriers

* RM-CSS predictions were generated 2026-09-21 and the Agent main run finished 2026-09-22T08:52Z, i.e. before the V2 MAIN oracle execution (2026-09-23). The Windows v1 MAIN oracle run (`oracle_confirmation_2026-09-22`) carries no intra-day timestamps, so ordering against it is unverified. Selections never had access to oracle outputs. M16 creates **no** new selection.
* The RM-CSS training/OOF universe (OOF_A, 323 tasks) has 0 MAIN overlap. Guard check: the deployment artifact's training task list ∩ MAIN = ∅. On the brain snapshot, the `deployment_artifact.json` fold_map (323 tasks = `n_dev_tasks`) has an empty intersection with MAIN_297, and so does OOF_A. **Re-verify at freeze.**
* Eligibility and readiness are selector-blind (section 7). Scope materialization (E_S, P_S, coverage class) happens **only after** the READY membership is committed, tagged and pushed.
* The gold diff is read only by evaluator-side code. The controller does not echo coverage classes per task until the analysis phase.
* M16 per-task outcomes may **not** be used to choose tasks, selectors, thresholds or prompts for any later MAIN E2E study. Any later MAIN study must take the full V3-READY census (decision record, Q1).
* M15-R results motivated the decomposition (section 2) but set no threshold. M15-R is not pooled with M16.
* The brain did not compute MAIN coverage/recall on any subset before the freeze (attestation, top).

---

## 12. Comparison with M15-R OPWS — what is genuinely new

| Aspect | M15-R OPWS | M16 OPWS-MAIN |
|---|---|---|
| Pool | Pilot-B, n = 10 | MAIN READY census, projected 45–110 |
| Agent selections | 3 **fresh** runs (paid) | **The WP1 selections that produced the WP1 NI claim** (zero API) |
| RM-CSS | same frozen artifact | same frozen artifact (WP1a MAIN predictions) |
| Statistics | descriptive only | paired estimation + CI-position rule; McNemar exact + mid-p |
| Estimand structure | post-hoc decomposition (16 NONE / 22 PARTIAL / 2 FULL) | **pre-registered** θ = P(FULL) + P(PARTIAL ∧ pass); π_S with CIs |
| Link to WP1 | none | H4 transportability: WP1 F1 on T* vs on 297; representativeness table |
| Generator | G0 stages (failed floor) | none (generator-independent by design) |
| Oracle | ENG/Pilot V3 sets | MAIN V3 sets constructed in M16 (selector-blind) |

M16 does not repeat M15-R evidence: it answers whether WP1's selection-stage conclusion survives an execution-grounded endpoint on the same tasks and selections, which M15-R could not do.

---

## 13. Frozen inputs and hashes to pin

Values are SHA-256 over the brain snapshot; **re-verify against the real repository at freeze**.

| Path | sha256 |
|---|---|
| research/wp1b/wp1b_main_297_manifest.json | d858316667c4a3e28f7bf759001dc1fd8746b93c710592ff646f3f91584811eb |
| research/wp1a/sip_rmcss_per_task_predictions.json | 76f16217f11043338ebfeb2c402bc4eaef8e6673394d93232fc41ddb21123e8f |
| research/stage5-v2-final/deployment_artifact.json | 7e9f82bc4d0a4acba114e80000a4246cb05e9f9b01a1ca2ce3c7c0a672dc4171 |
| research/wp1b/main-297-2026-09-22/wp1b_agent_predictions.json | c0b85dc7170327f283c977116e46d0deec0a2907d172137349b9b3dac3abc743 |
| research/wp1b/main-297-2026-09-22/agent_run_records.jsonl | 0000435a92bdd6540c532e572bf70faaab19d11435c2169b53cf20680e20a017 |
| research/wp1b/variance-15x3-2026-09-22/wp1b_agent_predictions.json | 29df49d33d698be8ab187e3ece13d38d0f873068c8b404a84512fb2c11ceeb7b |
| research/wp1b/variance-15x3-2026-09-22/agent_run_records.jsonl | eabc7a0bbe8dae9774b7c6a3e29d8d7f08d318966c5d54aac26cb76a0f00f648 |
| docs/WP1B_CLAIM_SHEET_2026-09-22.md | 41e7d560f9ffbf8d9fc589ab8b62922634451426acab0fb976b9df2918614a58 |
| research/wp2/wp2_saleor_main297_census_2026-09-22.json | 6146237d353376632d729e159761470b46fc5eb300fa9def971d5faf7b1f60c0 |
| research/wp2/wp2_oracle_confirmation_selection_2026-09-22.json | 8e7ba9df495496ede8747b356b8cd3b39fa93d16c4f51a4ef08da705af15b79d |
| research/wp2/oracle_confirmation_linux_v2_2026-09-23/summary_v2.json | c94a5f77edc4d24ba8ee2fe69fe4c712b0edd7fede321f951958ea070de8470e |
| research/wp2/oracle_confirmation_linux_v2_2026-09-23/per_task_v2.jsonl | 7fdeeb936ea84e7ef47a461e940671ee628114d9a1d960f29a0be008eddce021 |
| research/wp2/main_generation_quarantine_2026-09-23.json | 4de0833958ec1b54bb4307f7ee34d3ffdbe4b9029a31c78975e0a1c130019766 |
| research/wp2/protected_pools_untouched_proof_2026-09-23.json | 53ebdf0c499d663dd13dbb0cab381f0020ad8ef00cc359a54d47d5dd88dbf378 |
| research/wp2/wp2_p2p_u_v2_rule_freeze_2026-09-25.json | f33e74479b991c269a574498934f1d93ddf1921625aa249c2ef0c28df8c129a7 |
| research/wp2/harness_v3_2026-09-26/harness_v3_spec.json | 5d0ec5e70c11cd4ab4f2e30687b6327738f037a2b94ef8ee5c0ac34c674d73f2 |
| research/wp2/m14r_v1/m14r_design_freeze_v1.json | 9e3fd438c9fa2f69264ba887565fc8804d5d06a3fe3dd25561629d01c7f5ce60 |
| research/wp2/m15r_v1/m15r_design_freeze_v1.json | 1fd68354005709f99b22f08c636287466c54252bf2401bf93144987f9be8258e |
| research/wp2/m15r_v1/m15r_e1a1_amendment.json | 47b0a178fae5a590ffa5bd4010cbbed1911827b449c0f847f1661614eb8ce49c |
| scripts/wp2_m14a_evalcore.py | f9ba65ff3d453b5d620ce6f5ac1a58d2d3659ef7f7aab734867d6ec21fd6ddff |
| scripts/wp2_m14a_evalcore_e1.py | 6f028ad4eb99a19cc7c3b3a1d6defa51e1e5f7e72f76a2deeffffa51609365db |
| scripts/wp2_m15r_e1a1.py | a8bfb3ee6c7a7c6c6719279811b2e565e85c6839a286010313410fe28a63f9ca |
| scripts/wp2_m14a_readiness.py | 155cc1f3faecd0171e6f0438198d54af0a49d49489b9224f7df52a1d8c2dc389 |
| scripts/wp2_m10b_phase5_c4_v3.py | 7689d4a83a89fc5359c8f939c3d9eda0a162ef3d9d9ef263a88f2be4ca2ddf66 |

Also pin:
* the M15-R result LIGHT (`a598780b…6c7`, read-only reference);
* the V3 era image IDs;
* the uv cache volume identity;
* the git tag of the M16 design freeze.

Produced-and-pinned during the run (each commit, tag and push gates the next phase):
* the V3 MAIN oracle evidence;
* the eligibility freeze;
* the P2P-S/P2P-U memberships;
* the READY membership;
* the scope/OPWS plan.

---

## 14. Proposed controller phases (proposal only — nothing built)

All phases are zero model API. Docker phases are sequential, workers = 1, and nothing else runs concurrently (no AG16, no other controller).

| Phase | Content | Docker | Gate |
|---|---|---|---|
| Q00 | Kit self-tests | no | — |
| Q01 | Guard: hashes, quarantine decision record, protected pools, no M16 outcome files, storage check | no | HOLD/STOP |
| Q02 | MAIN evaluator adapter: census/era lookup for MAIN without changing frozen semantics; regression = reproduce 2 existing ENG V3 records' identities and decisions from stored evidence | no | STOP on mismatch |
| Q03 | **C2-MAIN-V3**: C4-V3 oracle construction on the frozen 220 (Route B), or on the 71 (Route A) | yes | resumable |
| Q04 | Eligibility freeze (V3 classifications) → commit + tag + push | no | push-verified |
| Q05 | P2P-S extraction (P2P_ONLY) + P2P-U v2 cap200 membership (frozen rule `78a089bb…`, salt `wp2-p2p-u-v2-2026-09-25`) + discovery | yes | resumable |
| Q06 | Readiness (negative + positive) for each eligible task | yes | resumable |
| Q07 | READY membership freeze + pool gate → commit + tag + push | no | n ≥ 40 or descriptive-only |
| Q08 | Scope freeze: materialize E_S for RMCSS, AGENT_MAIN and r1–r3 (overlap); build the OPWS plan (EMPTY / REUSE / EVALUATE, dedup by identity) → commit + tag + push | no | push-verified |
| Q09 | OPWS evaluate (EVALUATE items only), `--max-items` chunks | yes | resumable |
| Q10 | Completeness check (every planned identity has a valid record) | no | STOP |
| Q11 | Analysis: tables, Tango/Newcombe CIs, McNemar exact + mid-p, decomposition, H4, representativeness → token | no | — |
| Q12 | Summary + result tag (exact refspec) + LIGHT | no | — |

---

## 15. Runtime, storage, Docker load (estimates; measured V3 rates)

V3 measured rates come from `research/wp2/harness_v3_2026-09-26/later_work_estimates_v3.json`:
* C4: 3 / 5 / 8 min per task (optimistic / central / conservative);
* P2P-U: 10 / 13 / 20 min per unit;
* readiness: ~2 evaluations × ~5 min;
* OPWS evaluation: ~5 min (M15-R observed).

OPWS EVALUATE items ≈ 2 × n_READY × ~0.55 (M15-R PARTIAL share), minus identity dedup, plus ~12 replicate items. That gives ≈ 55–125 evaluations, about 5–10 h.

| Route | Oracle (Q03) | P2P-U + readiness (Q05–Q06) | OPWS (Q09) | **Total Docker (central)** |
|---|---|---|---|---|
| A (V2-71 reconfirmed) | 71 × 5 min ≈ 6 h | 71 × ~18 min ≈ 21 h | ~5–7 h | **≈ 33 h** (range ~25–50 h) |
| B (V3 on 220) | 220 × 5 min ≈ 18 h (11–29) | n_elig (70–125) × ~18 min ≈ 21–38 h | ~6–10 h | **≈ 45–66 h** (range ~35–90 h) |

Without P2P-U (Q3 = no), subtract about 13 min per eligible task (−15 to −27 h). The ~18 min/task figure for Q05–Q06 is the Pilot precedent (26 tasks in about 10.1 h ≈ 23 min/task, which included C4) minus the ~5 min C4 share already counted in Q03. The range bounds are hand-set envelopes, not computed.

* **Storage.**
  * Evidence (JUnit, records, plans): about 0.5–1.5 GB.
  * **Environments are the risk.** The V2 oracle envs were 23.95 GB for 160 executable tasks (≈ 0.15 GB/task). If V3 persists per-task envs, Route B could need about 30 GB.
  * Pre-declare: the V3 env root goes on `D:\wp2_cold` (the junction pattern already proven), or per-task env cleanup runs after each task's evidence is hashed.
  * Current C free is 33.3 GB; HOLD threshold 15 GB (section 10).
* **Docker load:** 1 postgres + 1 redis + 1 era container at a time; workers = 1; no parallelism (consistent with the frozen evaluator).
* **Cost: $0** (zero model API). Electricity and time only.

---

## 16. Claims

**Allowed if M16 completes (wording template):**

* "On n Saleor MAIN tasks with a valid V3 behavioral oracle (census of READY tasks), restricting the developer's own non-test patch to the files chosen by the frozen WP1 RM-CSS selection passed the hidden tests robustly on θ̂_R [CI] of tasks, vs θ̂_A [CI] for the frozen WP1 Agent selection (single run); paired difference δ̂ [Tango 95% CI], <token>."
* "Partial file coverage was sufficient on π̂_S [CI] of partially covering selections; file-level recall therefore under-/over-states execution sufficiency by …"
* "The WP1 selection-stage comparison does / does not transport to this execution-grounded endpoint on T* (H4)."

**Not allowed:**

* Any end-to-end or repair claim, e.g. "RM-CSS helps a generator solve tasks". OPWS uses the developer's patch, not generated code.
* Generalization beyond Saleor, beyond the READY subpopulation (excludes the 77 no-test tasks, env-blocked tasks, symbol-only tasks and NOT_READY tasks), or to added-file-dependent changes.
* Claims about Agent stochasticity beyond the replicate-overlap subset (7–13 tasks).
* "Over-selection is free". OPWS does not penalize extra files; cost is reported separately.
* Statements about alternative fixes. OPWS credits only the developer's patch, so it is a **lower bound** on "a passing patch exists within the scope", for this oracle.
* Pooling with M15-R, Pilot-A/B or ENG.
* Re-stating WP1's NI at Δ = 0.05 on this endpoint.
* Any WP1B forbidden sentence (claim sheet).

---

## 17. Threats to validity

1. **Survivorship and selection (external validity).**
   * Eligibility requires changed tests, an installable environment, behavioral F2P and a scoped-gold pass.
   * Under V2 the survivors are structurally easier: gold mean 3.04 vs 3.93 HARD files; added non-test files 4/71 vs 32/226; migrations 4/71 vs 33/226.
   * They are also temporally skewed (2020–2021 yield 2/63; 2024 3/32).
   * Pairing protects the **internal** RMCSS-vs-Agent comparison, because exclusion is selector-blind. Level estimates θ_S are likely **optimistic** for MAIN overall.
   * Mitigations:
     * Route B (same instrument for eligibility and evaluation);
     * a pre-registered representativeness table (WP1 F1 D on T* vs on the complement vs on 297, plus era/year/gold-size distributions);
     * a sensitivity analysis reweighting T* to the 220 by selector-blind strata (era × gold-size tercile). This is descriptive, not a claim.
2. **The eligibility filter could interact with the selectors.** Small-gold tasks may be easier for both selectors in different degrees. The cross-table and the per-stratum δ (descriptive) expose this.
3. **Instrument version.** The V2 → V3 change can flip node classes. Route A would mix a V2 frame with a V3 evaluator; Route B removes this.
4. **GOLD_HARD excludes added and renamed files.**
   * Tasks that need new files fail readiness and drop out; this is selector-blind but shrinks the population.
   * Sensitivity (optional, Q8): an "added-file allowance" variant where P_S always includes gold-added files. No selector could pick those files anyway.
5. **Single Agent run.** The δ CI omits Agent run variance. The overlap substudy only bounds it descriptively. The M15-R pairwise Jaccard was 0.5, so this is not negligible.
6. **RM-CSS empty sets** (4/71 under V2) count as NONE → 0. This is part of RM-CSS's operating point, not an artifact. It is reported.
7. **Finite census vs superpopulation.** The CIs assume exchangeability with comparable Saleor tasks. Single-repository scope.
8. **Construct.** OPWS measures sufficiency for the developer's fix, not difficulty for a generator. M15-R showed that a sufficient scope (436f) did not translate into generator success.
9. **Quarantine.** A MAIN outcome set now exists, so the risk of later implicit tuning is controlled by the barrier in section 11 and the decision record (Q1).
10. **Multiplicity.** One primary CI with nested tokens; H3/H4 are secondary; E-analyses carry no claims.

---

## 18. Open scientific questions to settle before freeze

**Blocking:**

* **Q1 — Quarantine decision record.** Is gold-only OPWS on MAIN permitted under "evaluator/oracle construction", or is it an "amendment L-OPWS"?
  * Proposed wording: MAIN stays closed to generation, prompt tuning and repair tuning.
  * M16 outcomes cannot select tasks, selectors or thresholds for any later MAIN study.
  * Any later MAIN E2E must use the full V3-READY census.
* **Q2 — Route A (V2-71 reconfirmed, ~33 h) vs Route B (V3 on all 220, ~45–66 h).** Brain recommends **B**: it uses the same instrument for the frame and the outcome, mitigates the 2024–2025 lockfile survivorship, and gives larger expected n.
* **Q3 — Include P2P-U200 in robust preservation?** Yes keeps exact M14R/M15-R comparability (+15–27 h). No is cheaper but changes the endpoint. Brain recommends **yes**.
* **Q4 — Primary endpoint and margins.** OPWS_ROBUST primary with the CI-position rule at 0 / ±0.10 (brain recommendation), or estimation-only with no tokens. Δ = 0.05 is shown infeasible (section 6).

**Non-blocking (defaults proposed):**

* **Q5 — CI/test methods.** Tango score CI primary; Newcombe sensitivity; exact McNemar primary with mid-p co-reported. Alternative: mid-p (or asymptotic) McNemar as the primary test, which is what Fagerland et al. 2013 and 2014 recommend over the exact conditional test.
* **Q6 — Agent arm.** WP1 main run only (default). Fresh replicates would be a later paid M16b, not M16.
* **Q7 — Symbol-absence-only tasks.** Exclude (default, consistent with the behavioral oracle).
* **Q8 — Added-file allowance sensitivity.** Include as descriptive-only (default: include).
* **Q9 — Startup semantics.** E1 + E1A1 frozen together, with the INFRA → FAIL-only amendment rule (section 9).
* **Q10 — Pool gate.** n_READY ≥ 40 (default).
* **Q11 — Env storage.** V3 env root on `D:\wp2_cold` via junction (default) vs per-task cleanup.

---

## 19. Go / no-go

**CONDITIONAL GO**, with Route B, zero API, a census of READY tasks and estimation-first paired analysis. Next steps:

1. Settle Q1–Q4.
2. Write the design-freeze JSON and the decision record.
3. Only then build the kit (installer, controller plan, tests, dry-run simulation).

**NO-GO** for building or running anything until Q1 is recorded. Without it, M16 would violate the standing MAIN quarantine as written.

---

## References (statistical methods; all verified to exist)

* McNemar, Q. (1947). Note on the sampling error of the difference between correlated proportions or percentages. *Psychometrika* 12(2):153–157.
* Clopper, C. J., & Pearson, E. S. (1934). The use of confidence or fiducial limits illustrated in the case of the binomial. *Biometrika* 26(4):404–413.
* Tango, T. (1998). Equivalence test and confidence interval for the difference in proportions for the paired-sample design. *Statistics in Medicine* 17(8):891–908. https://onlinelibrary.wiley.com/doi/abs/10.1002/(SICI)1097-0258(19980430)17:8%3C891::AID-SIM780%3E3.0.CO;2-B
* Newcombe, R. G. (1998). Improved confidence intervals for the difference between binomial proportions based on paired data. *Statistics in Medicine* 17(22):2635–2650. https://onlinelibrary.wiley.com/doi/10.1002/(SICI)1097-0258(19981130)17:22%3C2635::AID-SIM954%3E3.0.CO;2-C
* Fagerland, M. W., Lydersen, S., & Laake, P. (2013). The McNemar test for binary matched-pairs data: mid-p and asymptotic are better than exact conditional. *BMC Medical Research Methodology* 13:91. https://link.springer.com/article/10.1186/1471-2288-13-91
* Fagerland, M. W., Lydersen, S., & Laake, P. (2014). Recommended tests and confidence intervals for paired binomial proportions. *Statistics in Medicine* 33(16):2850–2875. https://onlinelibrary.wiley.com/doi/10.1002/sim.6148
