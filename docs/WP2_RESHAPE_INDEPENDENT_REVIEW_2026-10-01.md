# WP2 reshape after M14R: independent review and M15 freeze (2026-10-01)

**Reviewer:** brain (Claude). Review only: no kit was built or executed, and no model/API calls were made.

**Inputs reviewed (hashes verified):**
- `WP2_RESHAPE_DECISION_FOR_CLAUDE_2026-10-01.md` (`b11ee895…5158`)
- `project-LIGHT-M14R_RESULT-2026-10-01-0614.zip` (`fa7b0533…ce6a`)
- the Pilot-A LIGHT (`49d31ba4…7da5`)
- repository reports on NestJS and the polyglot feasibility study

## 1. VERDICT

**`WP2_RESHAPE_REVIEW_PASS_WITH_CHANGES`**

I accept the direction: freeze G0, do not loop on the generator, keep WP1 primary, defer Grafana, and stage NestJS. **I reject Option A as written.** A second analysis of the M14R data, the BQBI headroom simulation in §3, shows three things:

- The generator's success is a stable property of each task (4 of 13 ENG tasks).
- Selection-type improvements have zero breadth headroom.
- On Pilot-B (G0 succeeded on 0–1 of 10 Pilot-A tasks), the GOLD gate is likely to fail, which would spend the last protected pool for no selector evidence.

The frozen replacement is **M15-R**. Its primary end-to-end endpoint is **oracle-patch-within-scope sufficiency (OPWS)**: the developer's own patch, restricted to the files the selector allowed, run against the hidden tests. This isolates the selector from the generator, has no generator variance, and needs no generation calls. It is followed by a cheap, gated generation stage with G0.

## 2. M14R_FINAL_INTERPRETATION

**Verified from the LIGHT:**
- All phases R00–R14 passed.
- Readiness: 14 candidates. 13 members; `82c56bde0e34` was excluded (`NOT_READY_SCOPED_GOLD_NOT_RESOLVED`).
- Episodes: 104 base + 104 static = 208.
- Unique evaluations: 85.
- Spend: 1,852,982 tokens, $0.5726227.
- The variant table matches the summary exactly. Token `M14R_FLOOR_NOT_MET`; winner G0 (fallback).
- Strict and robust gave identical counts in every variant.

**Corrections and additions to the draft:**

1. **Success is a task property, not noise.** Robust resolutions per task, G0:
   - 2d45 1/3, 8f76 1/3, e03ee 3/3, e25cf 3/3; every other task 0/3.
   - Across all 4 variants (12 GOLD outcomes per task, from 6 independent base generations), the same 4 tasks are the only ones ever resolved.
   - These are the same tasks Smoke v2.2 resolved.
   - The other 9 tasks were never resolved by any variant or replicate.
2. **The dominant failure is ZERO_F2P_PROGRESS (G0: 18 of 39):** syntactically valid patches that implement none of the tested behaviour. Tasks 39b4, 644f, 6abb, 74538, 823b, d220 and dc6ac have zero F2P progress in every variant.
   - Near misses: 93b20 (partial progress, every replicate in G2/G3).
   - c3b9 (F2P PASS with a *deterministic* P2P-S regression, in 2/3 of the replicates of every variant).
3. **G2 is not neutral; it redistributes successes.** It fixed format (INVALID 4 → 1) and 8f76 (1 → 3), but it hurt e03ee (3 → 1) and added startup failures (4 → 5).
4. **G1 behaved exactly as its coverage predicted.** Startup failures fell 4 → 1, giving +1 resolve on 8f76, and the task count did not move.
5. **The evaluator noise reappeared on ENG.** 2 of 14 readiness negative controls (39b4 P2P-U, d220 P2P-S) failed strict preservation on an unchanged tree through single-repetition failures. The robust endpoint stays justified.
6. **PLACEBO resolved robust = 0 in every variant.** G0 PLACEBO had 3 startup failures, so placebo edits can break startup.

**Conclusion:** G0 is retained as the simplest frozen generator. The generator floor is a *between-task capability ceiling* (about 31% of ENG tasks, about 0–10% of Pilot-A tasks). It is not a mechanical defect. Only an intervention that changes what the model knows or can do on the 9 failing tasks could move it.

## 3. REPEATED_NO_GAIN_ROOT_CAUSE

The same pattern shows up in localization and in the generator. It has three causes, with evidence:

1. **Fixes targeted non-binding constraints.**
   - On M14R data, a zero-API simulation of "best-of-k sampling + filtering by *visible* unchanged tests (P2P-U) and startup" was run with k=3 (G0) and k=12 (all variants).
   - Expected resolved tasks stay **4 of 4**, with no breadth gain.
   - Selection cannot create a correct candidate on the 9 tasks that never produced one. Format, static and selection fixes all act downstream of the binding constraint, which is *semantic candidate generation*.
2. **Low-information inputs on both sides.**
   - Selectors and generator receive the same rendered commit-title intents, which are sometimes nearly empty (for example "New payload structure").
   - The issue-resolution literature reports the same problem. Agentless (FSE 2025) found SWE-bench Lite problems with "insufficient/misleading issue descriptions" and built a filtered subset (SWE-bench Lite-S) to evaluate rigorously.
   - Interventions that reweight the same text rarely move the frontier. The one clear localization gain came from an orthogonal source, a code-localization embedding model.
3. **Small n with breadth and statistical gates.** With 13 tasks, a gate of +3 resolves or ≥5 tasks can only detect large effects. Small real improvements are structurally "not enough".

## 4. BQBI_GOVERNANCE_REVIEW

**Accept, with four changes.** BQBI is good governance. It should not be presented as a scientific contribution.

1. **Make BQBI-1 and BQBI-2 retrospective and quantitative.** Before any new run, simulate the intervention's best case on already-frozen evidence, as in §3, and apply the actual frozen decision rule to that simulated best case. If even the oracle version cannot pass the rule, do not run it.
   - Applied to the past: G1's coverage (4 startup failures, concentrated on already-solvable tasks) predicted that it could not reach +3 resolves or 5 tasks.
2. **Add BQBI-0, a power check.** The minimal detectable effect at the planned n must be no larger than the plausible effect implied by the coverage figure.
3. **Classify interventions by the information they add:** SAME_SIGNAL, NEW_SIGNAL, NEW_CAPABILITY, NEW_FEEDBACK. A family whose two SAME_SIGNAL attempts failed is frozen.
4. **Prefer estimands that isolate the component under study.** This is the reason for OPWS in §11: it removes the generator from the selector question.

## 5. GENERICITY_AUDIT

| Layer | Status today |
|---|---|
| Task formulation (intent → editable file set), hard scope, parent-only info, P/R/F1/FNR, GOLD/PLACEBO, freeze/ledger/controller/transport, SEARCH/REPLACE patch protocol, D50–D52 + robust scoring, OPWS, failure taxonomy | **Generic.** Language-independent logic, given test node outcomes. |
| Agent tools (list_files / read_file / search_text) | **Generic** (text tools) |
| SIP/sparse lexical signals | **Mostly generic.** Tokenization is tuned on Python code. |
| RM-CSS features from the Python import graph, the D35 test-path predicate (`is_test_path_v2`), the production universe | **Python/Saleor-specific** |
| Evaluator runtime: era Docker images, uv/pip locks, pytest node ids, pytest-django startup (E1 signature), `py_compile`, `pyflakes`, IMPORT_OUTLINE_V1 (Python `ast`) | **Python/Django-specific** |

## 6. NESTJS_TRANSFER_PLAN

The repository confirms `SUITABLE-WITH-DEVIATIONS`, with these blockers:
- no pinned cache;
- no TypeScript import extractor;
- anchor not frozen;
- the yield of at least 60 eligible commits not yet counted.

**Stages:**
- **X0 (zero API):** pin the clone and anchor, build the TS production universe and the test-path predicate, count eligible cases against the frozen ≥60 rule, freeze the split. If the count is below 60, record NestJS as UNSUITABLE (frozen rule) and stop.
- **X1 (selection only):** SIP/sparse and the Agent (its tools are language-agnostic), plus RM-CSS only with language-agnostic features. The TS graph extractor is built only if a chosen method needs it.
- **X2 (optional, small):**
  - build a Jest/JUnit runner adapter, a TS startup-failure signature (frozen before any outcome), and a pinned Node environment;
  - run OPWS on about 10 tasks with readiness controls;
  - generation E2E only after OPWS works.

**Minimum evidence for "methodology generic":** X1 on NestJS meeting the frozen protocol. A claim about end-to-end genericity additionally needs X2 OPWS on NestJS. NestJS is sufficient as the first non-Python target.

## 7. GRAFANA_TRANSFER_PLAN

**Defer.** It is post-thesis-core or future work. The repository's report says the polyglot yield is unverified, the cross-language semantics are not implemented, and the extractor is Python-only.

The only allowed pre-work is the zero-API mixed-language yield count (Go+TS in the same commit) against the ≥60 rule. Grafana must not block thesis closure.

## 8. WP2_OPTION_A_REVIEW

**Rejected as written.**
- With G0, Pilot-A solved 0 of 10 tasks strictly (1 of 10 robust) and ENG solved 4 of 13. The expected number of Pilot-B tasks GOLD can solve is about 1–3 of 10.
- A selector comparison restricted to tasks the generator can solve would therefore have about 0–3 tasks.
- Running all three arms (≥60 episodes, about 6–8 h of evaluation) would most likely end in `GOLD_FLOOR_FAIL` and consume the last protected pool.
- Its sound parts (frozen G0, a GOLD gate, no winner tokens, descriptive only) are kept inside M15-R as a staged, gated secondary.

## 9. WP2_OPTION_B_REVIEW

**Defensible but unnecessarily weak.** It drops the downstream question entirely, even though OPWS answers it cheaply and with no dependence on the generator. Keep B as the **fallback** if M15-R S1 fails its instrument gate.

## 10. WP2_OPTION_C_REVIEW

**Rejected now.** The BQBI simulation shows zero breadth headroom for selection, validation and mechanics families. Only NEW_SIGNAL or NEW_CAPABILITY families could help:
- richer public intent (PR text);
- a stronger model;
- reproduction-test feedback.

All three change the thesis object. Allowed later, outside the thesis core: one ENG-only BQBI diagnostic of intent headroom (G0 + public PR description), never on protected tasks.

## 11. M15_RESHAPE_FREEZE — M15-R "Pilot-B scope sufficiency"

**Population.** The frozen Pilot-B list from `research/wp2/pilot_a_v1/pilot_final_membership.json` (sha `72d935e6…`, `REDUCED_10`): 436f52ee3d0c, 34511f977388, 0a39d039049d, 60c8722863c1, 05df3bec57e2, 99d963aed3e5, eacffa70e721, ded69f9c7097, f383043e4be3, 102e4e5b25e8.
- The guard checks the list is disjoint from Pilot-A, M14R ENG and E1 identities.
- The guard checks each task has Pilot-A readiness `gold_empty_ok = true`.
- No Pilot-B generation or evaluation output may exist before the freeze.

**Arms (selector scopes; all pass the identical D35 editable filter):**
- `GOLD_HARD` (reference)
- `RMCSS_HARD` (frozen realization-A predictions; an empty prediction becomes NO_SCOPE, which is the method's outcome)
- `AGENT_HARD` r1, r2, r3: three fresh localizations with frozen protocol-v3 (D5, unchanged); replicate r uses run r. All Agent scopes are frozen and pushed before S1.
- SIP stays WP1-only. PLACEBO is not repeated.

**S0 — readiness (zero API, Docker).**
- Per task: a scoped-gold positive control (gold non-test diff restricted to the frozen GOLD_HARD editable set, robust RESOLVED) and an empty-diff negative control, as in M14R.
- Members are tasks passing both. If fewer than 6 members: `M15R_POOL_INSUFFICIENT`, which leads to Option B.

**S1 — OPWS, primary.**
- For each task × selector scope (RMCSS, AGENT r1–r3): P_S = gold non-test diff restricted to (selector editable ∩ gold-changed files).
- If P_S is empty: OPWS = FAIL by construction.
- If P_S is identical to the scoped-gold diff, reuse the S0 positive evaluation (identity = diff sha).
- Otherwise evaluate with the frozen evaluator and E1 semantics (3 reps).
- **Primary:** OPWS_ROBUST.
- **Co-reported:** OPWS_STRICT; file-level P/R/F1 vs gold; editable-scope files and characters; G0 prompt characters (deterministic, no call); Agent replicate agreement on OPWS.
- **Primary descriptive contrast:** paired per task, RMCSS vs each Agent replicate.
- Zero model calls except the Agent localization.

**S2 — G0 GOLD viability (secondary, paid, cheap).**
- `GOLD_HARD` × r1–r3 with **G0 identical to M14R G0**: `run_base_episode` with context C0. The M14R source hashes for `wp2_m14r_run.py`, `wp2_m14r_core.py` and BORROWED must match exactly. Equivalent to `run_episode_v21` by test.
- **Gate:** GOLD-solvable tasks (≥1 robust resolve) ≥ 4 **and** GOLD robust episodes ≥ 6/30, both scaled as ceil(0.4·n) and ceil(0.2·3n).
- Fail → `M15R_GOLD_FLOOR_FAIL_NO_GENERATION_CLAIM`. S3 is skipped and the S1 OPWS stands.

**S3 — selector generation (conditional on S2 PASS).**
- RMCSS and AGENT × r1–r3 with G0. The analysis set for any generation-based contrast is **the GOLD-solvable tasks only**, predeclared; all tasks are reported descriptively.

**Endpoints:** RESOLVED_ROBUST is primary and RESOLVED_STRICT is always co-reported (definitions as M14R core). Also reported:
- taxonomy;
- F2P node progress;
- tokens, calls and $ for selector + generation + repair (ledger).

**Cost cap:** authorization ≤ $3.00. Expected about $0.7 for the Agent runs, $0.25 for S2 and about $0.6 for S3.

**STOP tokens:**
- Resumable: `READINESS_ENV_FAIL`, `EVAL_ERROR`, `E2E_PROVIDER_OUTAGE`, `HOLD_ACTIVE`, `PAID_PREFLIGHT_FAIL`, `NOT_AUTHORIZED`.
- Non-resumable: `M15R_GUARD_FAIL`, `M15R_INVARIANT`, `E2E_BUDGET_STOP`.
- Terminal facts: `M15R_POOL_INSUFFICIENT`, `M15R_OPWS_COMPLETE`, `M15R_GOLD_FLOOR_FAIL_NO_GENERATION_CLAIM`, `M15R_COMPLETE_DESCRIPTIVE`.
- There are no winner tokens.

**Leakage checks:**
- The gold diff is used only on the evaluator side.
- Selectors and generator never see gold, tests or outcomes.
- The RM-CSS predictions file hash is frozen before S0, with no tuning.
- Agent scopes are frozen before S1.
- Generation prompts are scanned for F2P/P2P ids and changed-test paths, as at the M14R freeze.
- Pilot-A, ENG and Pilot-B evidence roots are separated.

**Transition:** M15-R result → human review → M16 design freeze. Nothing starts automatically.

## 12. M16_ENTRY_CRITERIA

All of the following:
- M15-R S1 completed with at least 6 members.
- The OPWS instrument is valid: scoped-gold positives pass, negatives fail F2P, no unresolved EVAL_ERROR.
- The robust/strict discordance is reported.
- A frozen M16 design exists.

**Recommended M16 Research Run: OPWS-MAIN.** OPWS on a preregistered random sample of MAIN_297 tasks.
- It uses the **existing frozen WP1 RM-CSS and Agent selections**, so it needs zero new model calls.
- The sample is restricted to tasks that pass oracle confirmation and readiness.
- The size is chosen from the Docker budget and the S1 discordance rate. This is an internal-pilot variance estimate only.

G0 generation in M16 runs only if M15-R S2 passed.

## 13. CLAIM_WORDING

> "The change-scope methodology is language- and repository-parameterizable. Its current realization (selection and end-to-end assay) is validated on Python repositories (Saleor, djangoCMS) and requires language-specific adapters (production universe, test-path rules, test runner, startup semantics) for other ecosystems. We report end-to-end consequences of scope selection primarily as oracle-patch scope sufficiency, which is independent of the downstream generator's capability, and repair outcomes with a fixed generator only where that generator demonstrably solves the task under gold scope."

Forbidden until the NestJS stages pass:
- "language-agnostic system";
- any cross-language E2E claim;
- any pooled cross-repository superiority claim without the repository treated as a factor.

## 14. RISKS

- **OPWS does not penalize over-selection.** Cost is reported separately (scope characters and prompt size). Over-selection's effect on a real generator appears only in S3.
- **OPWS assumes the developer's patch is the reference solution.** Alternative valid fixes are not credited, a known limitation of oracle analyses.
- **Pilot-B is small (n ≤ 10).** All results are descriptive.
- **Agent stochasticity** is captured by 3 runs.
- **Readiness can exclude tasks.**
- **Evaluator flakiness** is handled by the robust rule, with strict always shown.

## 15. EXACT_NEXT_MISSION

**Mission M15R-K: brain builds the kit.**
- **Executor:** brain, zero API/Docker.
- **Inputs:** this review, the M14R LIGHT (`fa7b0533…`), the Pilot-A LIGHT (`49d31ba4…`), the frozen Pilot-B membership (`72d935e6…`).
- **Outputs:** M15-R design JSON, engine, plan, tests, installer.
- **DO:** implement S0–S3 as frozen, reusing the M14R core/engine and E1 unchanged.
- **CHECK:**
  - unit tests, including a G0 request-identity test against M14R `run_base_episode`;
  - the OPWS restriction is unit-tested;
  - simulated install and controller run up to the S0 pause.
- **IF-FAIL:** fix before delivery.
- **STOP:** none to the human.

**Mission M15R-I: OpenCode install.** Executor OpenCode, build only.
- **DO:** verify the installer hash, then run the installer.
- **CHECK:** `M15R_KIT_INSTALL_COMPLETE`.
- **IF-FAIL:** STOP block (rolled back).
- **Permissions:** Git commit/push/exact tag; no API; no Docker.

**Mission M15R-H: human runs the controller.**

| Phase | Executor | Notes |
|---|---|---|
| S0 readiness | controller | Docker, zero API, `--until` membership pause |
| Authorization | human | cap ≤ $3 |
| Agent localization | controller | paid, ~$0.7; resumable outage |
| Agent freeze + tag | controller | — |
| S1 OPWS | controller | Docker, loop; resumable EVAL_ERROR |
| S2 GOLD generation + evaluation + gate | controller | — |
| S3 | controller | only if S2 PASS |
| Summary, commit, tag, LIGHT | controller | — |

All Git actions are performed by the controller. No other controller (for example AG16) runs concurrently.

## 16. FILES_TO_CREATE

**At kit time:**
- `research/wp2/m15r_v1/m15r_design_freeze_v1.json`
- `scripts/wp2_m15r_run.py` (reuses `wp2_m14r_core.py` unchanged)
- `scripts/wp2_m15r_authorize.py`
- `controller/plan_m15r_v1.json`
- `controller/light_profile_m15r.json`
- `controller/KIT_MANIFEST_M15R.json`
- `tests/unit/wp2/m15r/test_m15r.py`
- `docs/WP2_RESHAPE_INDEPENDENT_REVIEW_2026-10-01.md` (this file)
- `docs/MISSION_M15R_INSTALL_*.md`
- `docs/MISSION_M15R_HUMAN_RUN_*.md`

**Later, separately:**
- NestJS X0 artifacts under `research/crosslang/nestjs_x0/`

**Never modified:** Pilot-A, M14A, E1, M14R evidence and design.
