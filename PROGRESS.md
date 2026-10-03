# PROGRESS.md — Single Current Source of Truth

**As of:** 2026-10-02
**Project:** Dependency-Aware Selective Regeneration Benchmark
**Primary scientific object:** repository-level affected-file / editable change-scope correctness
**Primary metric:** file-level impact correctness (file-level F1)
**Execution roles:** ChatGPT = scientific brain; OpenCode + DeepSeek = builder/executor; Claude = independent reviewer.

> This file is the current operational source of truth. Historical experiment detail remains in frozen artifacts, `docs/EXPERIMENT_LEDGER.md`, `docs/RESULTS_SUMMARY.md`, and `DECISIONS.md`; it is not duplicated here.

---

<!-- LIVE_STATUS:BEGIN -->

## LIVE STATUS — single current-state source of truth

**Position:** M17 Phase0B-v2 (2026-10-03): executable M17 qualification kit FROZEN with the brain-approved corrected 12-task membership; ZERO Docker/WSL/API; qualification NOT run. M16-v1 closed pre-experiment. Primary claim-bearing evidence is WP1 selection correctness/efficiency; WP2 supporting/downstream.

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
| WP-2 E2E Smoke v2.2 | DONE | 62 generation episodes; APPLIED 50; invalid-after-repair 11; no-scope 1; engineering pipeline only |
| WP-2 Pilot-A / M14R generator probes | DONE (SUPPORTING NEGATIVE) | generator floor not removed; GOLD/PLACEBO RESOLVED 0; robust episodes 8/9/8/8 |
| WP-2 M15-R OPWS Pilot-B | DONE (DESCRIPTIVE) | GOLD 10/10; RM-CSS 3/10; Agent r1/r2/r3 2/10,3/10,2/10; n=10 |
| M16-v1 OPWS-MAIN instrument | CLOSED (PRE-EXPERIMENT) | R02_ADAPTER_VERIFY STOP M16_ADAPTER_FAIL; R00 kit 102/102 PASS; no MAIN outcome |
| C0->C6 documentation/closure | DONE | ledger/results/claims/methods/threats/README landing/research-status/repro-audit/LIGHT convention |
| G0_BRAIN_REVIEW | DONE | brain decision: finalize durable baseline before new science |
| M17 Phase0B-v2 executable qualification kit | KIT_FROZEN (zero-Docker, zero-API) | runner/adapter/manifest/real-controller integration; qualification NOT run; membership corrected (f76d out, bcd9f6 in) + brain-approved; next: brain review then real 12-task qualification |

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
| M15-R OPWS + generation (Pilot-B n=10) | 228 agent-localization calls (30 runs) | agent localization $0.6448 frozen list price; generation provider-reported $0.2478 / 715,438 tokens; descriptive only |

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
| C0->C6 closure + G0_BRAIN_REVIEW | DONE | documentation/evidence consolidation only; brain decision: finalize durable baseline before new science |
| M16-v1 MAIN OPWS run | NOT AUTHORIZED / CLOSED | closed pre-experiment adapter failure; no MAIN outcome; a future attempt requires a separately designed, brain-approved M16-v2 |

**Next action:** Await ChatGPT brain review of the M17 qualification kit before the REAL 12-task qualification. Do NOT run the 12 tasks, MAIN, OPWS, Docker, WSL, or any model/API call until then.

**End-to-end status:** M17 executable qualification kit frozen (zero-Docker, zero-API); qualification NOT run. WP-2 supporting evidence closed/consolidated; M16-v1 closed pre-experiment; no active scientific run.

*Source: `docs/LIVE_STATUS.json` (schema `live_status_v1`), rendered by `scripts/render_live_status.py`. As of 2026-10-03 (Africa/Cairo).*
<!-- LIVE_STATUS:END -->

---

## أين نحن الآن

- The documentation/closure mission **C0→C6 is complete** and correctly stopped at `G0_BRAIN_REVIEW`.
- The 2026-10-02 **T2 closure-finalization task** is the current authorized work: LIVE status brought current, the future LIGHT filename convention corrected, then commit/push/tag of the durable baseline, a fresh corrected-convention LIGHT, and STOP at `G1_SCIENCE_DECISION`.
- Reported Git identity at that gate:
  - branch: `main`
  - HEAD: `3280a658ac488dc64f44fef050c1f8ea993a58c9`
  - origin/main: same commit
- The closure mission produced **4 modified tracked files + 10 new files**, but they are still **uncommitted** because the task graph did not authorize a commit.
- The mandatory project export `project-2026-10-02-1855.zip` does **not** contain the new uncommitted closure documents; the closure LIGHT does. This is an important durability finding.
- `docs/LIVE_STATUS.json` / rendered LIVE block is stale (as-of 2026-09-28) and no longer represents the actual WP2 closure state.
- M16-v1 is **closed** as a pre-experiment adapter/instrument qualification failure:
  - R00 self-tests: PASS
  - R01 guard: PASS
  - R02 adapter verification: FAIL-CLOSED
  - no R03 selection
  - no real dry-run Docker execution
  - no MAIN OPWS outcome
  - no R2B/R2C continuation
- Primary thesis evidence is already in WP1; WP2 is supporting/downstream evidence.

**Current evidence picture:**
- Saleor RESERVE-300: RM-CSS F1 `0.3569` vs SIP `0.2647`; Δ `+0.0921`, 95% CI `[0.0691, 0.1156]`.
- MAIN_297 selection-only: Agent `0.3631`, RM-CSS `0.3568`, SIP `0.2652`.
- MAIN_297: non-inferiority at preregistered margin `0.05` supported; margin `0.03` inconclusive. This is **not** equivalence or superiority.
- Efficiency vs Agent: RM-CSS ≈ `0.2746×` model calls and ≈ `0.2134×` generation tokens.
- E2E Smoke v2.2: 62 generation episodes; APPLIED 50; invalid-after-repair 11; no-scope 1. This validates the engineering pipeline, not selector superiority.
- Pilot-A: GOLD RESOLVED 0; PLACEBO RESOLVED 0 → generator floor.
- M14R: tested G0/G1/G2/G3 variants did not remove the generator floor.
- M15-R OPWS Pilot-B (n=10): GOLD 10/10; RM-CSS 3/10; Agent r1/r2/r3 = 2/10, 3/10, 2/10. Descriptive only.
- M15-R generation: Gold-solvable 1/10; robust episodes 3; no valid generation-based selector comparison.
- M16-v1: no MAIN scientific outcome; method/instrument closure only.

**LIGHT naming decision, effective for future exports only:**
- Filename format is now:
  `project-light-YYYY-MM-DD-HHMM.zip`
- Example:
  `project-light-2026-10-02-1855.zip`
- The timestamp is the machine's timezone-aware local creation time at minute precision.
- Historical LIGHT files are never renamed.
- The exporter `scripts/wp2_export_light.py` and its tests now implement this
  convention (T2 finalization); a same-minute collision fails closed.

---

## آخر إنجاز (2026-10-02 · Tier T3 closure/documentation mission)

Completed C0→C6:

- archived the final M16-v1 STOP evidence;
- created the M16-v1 closure document;
- consolidated the experiment ledger, results summary, and claim registry;
- converted README into a research landing page;
- added methods, threats-to-validity, research-status, and reproducibility-audit documents;
- implemented and tested a future LIGHT naming mechanism (now superseded by the filename correction recorded above);
- produced a closure LIGHT and project export;
- stopped correctly at the human/ChatGPT review gate.

Validation reported by OpenCode:
- `py_compile`: PASS
- Ruff: PASS
- Mypy: PASS
- `git diff --check`: PASS
- exporter tests: 4/4 PASS
- M16 kit tests: 102/102 PASS
- live-status tests: 3/3 PASS
- README model/SVG tests: PASS
- full suite: 4486 passed, 34 skipped, 6 initially failed
  - 3 mission-caused failures were fixed and re-verified
  - 3 remaining failures are pre-existing/environmental and already documented

**What we learned:**
1. The thesis is **not blocked by generation**. Generation is a downstream bottleneck and supporting negative result; the primary thesis contribution is change-scope selection.
2. RM-CSS already has its strongest evidence in the frozen WP1 selection-only studies.
3. OPWS is useful for scope-sufficiency evidence, but M16-v1 showed that a larger MAIN OPWS study needs a cleaner separately designed instrument if it is ever revisited.
4. We should not continue an amendment chain merely to force M16 through preflight.
5. The repository had a truth/durability gap: current documentation was uncommitted, LIVE_STATUS was stale, and the large project export omitted the new uncommitted closure files.
6. Documentation and governance now matter as much as another experiment: claims must be frozen before we decide whether another study is scientifically necessary.

**What we conclude:**
- The central comparison is **RM-CSS vs bounded Repository Agent at the selection stage**, with SIP as the simpler baseline.
- We do **not** claim RM-CSS is E2E-superior to Agent.
- We do **not** claim generator correctness is solved.
- We do **not** claim language-agnostic generalization.
- A polyglot/Grafana study is optional external-validity work, not the next automatic step.

---

## الخطوة القادمة المباشرة (Next)

**No new experiment starts here.**

The 2026-10-02 **T2 closure-finalization task** is the current authorized work. It makes the repository durable and internally consistent before any new science:

1. `docs/LIVE_STATUS.json` and the rendered LIVE block updated to the true 2026-10-02 state (C0→C6 done, G0_BRAIN_REVIEW done, M16-v1 closed pre-experiment);
2. the **future** LIGHT filename convention corrected from
   `project-light-YYYYMMDDTHHMMSSZ.zip`
   to the user-approved
   `project-light-YYYY-MM-DD-HHMM.zip`
   (timezone-aware local time, minute precision, same-minute collision fails closed);
3. only the directly affected exporter test/spec/README references updated;
4. historical LIGHT names verified untouched;
5. targeted validation plus the required regression suite rerun;
6. the complete C0→C6 closure + this finalization committed and pushed as a durable milestone;
7. an evidence tag `msc-research-baseline-2026-10-02` frozen by this mission's explicit authorization;
8. a new LIGHT produced whose name follows the corrected convention;
9. STOP at `G1_SCIENCE_DECISION` for ChatGPT review.

**Immediate next after this T2:**
`Brain decision: seminar/proposal first vs exactly one optional targeted external-validity pilot.`

**No polyglot repository, no M16-v2, no new generation run, and no selector retuning before that gate.**

---

## الهدف القريب (الساعات / الأيام القادمة)

Freeze a **clean, committed, pushed, reproducible thesis evidence baseline**.

Definition of done:

- one current `PROGRESS.md`;
- current LIVE_STATUS matches the actual WP1/WP2 state;
- README, claim registry, results summary, and experiment ledger agree;
- the new LIGHT naming is exactly `project-light-YYYY-MM-DD-HHMM.zip`;
- historical LIGHTs remain immutable;
- all mission changes are committed and pushed;
- tests and reproducibility checks are recorded;
- a fresh LIGHT contains everything needed for ChatGPT/Claude review;
- no new scientific result is introduced during this cleanup.

After that baseline is frozen, the immediate scientific decision is:
**Brain decision: seminar/proposal first vs exactly one optional targeted external-validity pilot.**

---

## الهدف المتوسط (أكتوبر 2026)

Produce a seminar/proposal-ready research package in which every claim is traceable and defensible.

Target outputs:

- final RQs and thesis story;
- concise Methods section;
- canonical Results tables/figures;
- Threats to Validity;
- systematic-mapping / novelty evidence sufficient to defend the contribution;
- reproducibility package;
- proposal/seminar deck and private defense notes;
- explicit decision on whether one more experiment is worth its cost.

Possible scientific extension after that decision:

**WP3 polyglot feasibility pilot**, not a full study.

Candidate: Grafana only if it passes a 10-commit feasibility gate without becoming another infrastructure project. A smaller mixed-language repository is preferred if Grafana requires disproportionate engineering.

The pilot, if authorized, should measure feasibility only:
- checkout/build reproducibility;
- test availability;
- changed-test evidence;
- mining quality;
- selector-input compatibility;
- runtime/resource cost;
- cross-language vs single-language changes.

Go to a 30–50 commit study only if the pilot passes the predeclared gate.

---

## الهدف البعيد

A thesis and benchmark artifact that are publishable, reproducible, and scientifically narrow enough to defend.

The final research story should answer:

1. **Impact Correctness:** how accurately can we select the repository files affected by a requested change?
2. **Efficiency:** can RM-CSS achieve selection quality close to a bounded repository Agent with materially fewer model interactions/tokens?
3. **Functional / Preservation support:** when the selected scope is used downstream, what evidence exists that required behavior is preserved or that missing files matter?
4. **Architecture Compliance:** can the selected scope and artifacts obey the frozen repository/schema contracts?
5. **Generalization:** only if additional evidence justifies it, how well do the findings transfer beyond Saleor/Python?

The end goal is **not** “make every E2E generator succeed.”
The end goal is a defensible contribution around **resource-efficient repository change-scope selection for LLM-assisted software evolution**, with downstream execution evidence used to bound—not replace—the primary selection claim.

---

## Blockers الحالية

### Immediate blocker
The repository closure is being made durable by the 2026-10-02 **T2
closure-finalization task**:
- C0→C6 changes are committed and pushed on `main`;
- `docs/LIVE_STATUS.json` and the rendered LIVE block are current to 2026-10-02;
- the mandatory project export is recreated after commit so it contains the committed closure files;
- the future LIGHT filename format is corrected to `project-light-YYYY-MM-DD-HHMM.zip`.

This was the **single critical bottleneck** before new science; after the T2
freezes the baseline (tag `msc-research-baseline-2026-10-02`), the next
scientific decision is the brain's G1 call: **seminar/proposal first vs exactly
one optional targeted external-validity pilot.**

### Not blockers to the thesis
- M16-v1 failure is not a blocker; it is closed pre-experiment method evidence.
- Generator floor is not a blocker to the primary thesis claim.
- Lack of a polyglot study is not currently a blocker.
- Three known environmental test failures are not caused by the closure mission, but must remain disclosed.

### Big picture
The research already has a primary claim-bearing comparison:
**RM-CSS vs bounded Agent on file-level selection quality and efficiency.**
Everything now should strengthen the credibility, reproducibility, scope, and external validity of that claim—not create a second thesis by accident.

### Small picture
The next code/document delta should touch only:
- `PROGRESS.md` now;
- in the next authorized T2: LIVE status, LIGHT exporter naming, directly affected tests/docs, and Git/release metadata.

### Critical unlock
Once the repository is current, committed, pushed, and export-complete, the brain can make a clean scientific decision:
**stop experimenting and write/present, or authorize exactly one targeted generalization study.**
