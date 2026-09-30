# WP2 Pilot-A closure → M14R: independent review (2026-09-30)

- Reviewer: brain (Claude). Mode: review, correction and design freeze, then kit build.
- Model/API calls made by this review: 0.
- Evidence: `project-LIGHT-PILOT_A_RESULT-2026-09-30-1940.zip` (sha256 `49d31ba4…6c47da5`, 1,314,425 bytes, hash verified).
- Every number below was recomputed from the raw episode, evaluation, ledger and diagnostics files, not from `pilot_a_summary.json`.

## 1. VERDICT

**`M14R_REVIEW_PASS_WITH_CHANGES`**

The Pilot-A result is correct as frozen: `PILOT_A_GENERATOR_FLOOR_HOLD`. The M14R direction (ENG only, generator/interface probe, hard scopes kept) is sound. The draft needs the following changes before any M14R API call. All of them are implemented in the frozen design `research/wp2/m14r_v1/m14r_design_freeze_v1.json` (sha `4d3e73fa…bc68f`).

1. **Measurement fix first (new finding).** Pilot-A shows *unchanged parent trees* (empty diffs) failing strict preservation because of single-repetition test failures. The strict 3/3 preservation rule therefore produces measured false regressions. M14R uses a pre-declared RESOLVED_ROBUST development endpoint: a preservation node counts as broken only if it fails in ≥2 of 3 reps, and F2P stays at 3/3. The frozen strict endpoint is always co-reported.
2. **Scoped-gold readiness per task.**
   - A positive control is run on the gold diff restricted to the frozen GOLD_HARD editable set. This is the ceiling a perfect generator could reach.
   - A negative control is run on the empty diff.
   - A task enters M14R only if both controls behave; at least 10 of the 14 ENG tasks must qualify.
3. **The static factor is paired.** G1 and G3 are post-processing of the same G0 and G2 generations. They are not independent re-generations. This halves the cost and removes generation noise from the static comparison.
4. **Concrete, auditable G2 rule (`IMPORT_OUTLINE_V1`).**
   - It covers one hop of imports and uses verbatim parent lines only (signatures and class-level attribute lines).
   - It is capped at 6k chars per module and 40k chars in total.
   - At freeze it is audited for verbatim derivation and for test-path and node-id leakage.
5. **Contemporaneous G0.** G0 is re-run with 3 GOLD replicates rather than reusing the Smoke outputs.
6. **Frozen, unit-tested decision rule.** It is computed by `wp2_m14r_core.decide`; details are in §6.
7. **Two draft statements corrected:**
   - "the two GOLD F2P passes broke preservation / were not regression-safe" is not supported (§4);
   - the P2P-S/P2P-U PASS counts include PASS_BY_CONSTRUCTION episodes (§2).

## 2. PILOT_A_REDERIVATION

| Fact | Verdict | Evidence |
|---|---|---|
| 1. Protected development-holdout assay, not RM-CSS-vs-Agent | ✅ | Design `c4c28d58…`; arms GOLD_HARD/PLACEBO_HARD only |
| 2. 10 tasks × 2 arms × 2 reps = 40 | ✅ | Membership `REDUCED_10` (`72d935e6…`); 40 plan items |
| 3. Generation completed and froze before evaluation | ✅ | `generation_freeze.json` `10f6d577…` hashes 287 files; P10 10:01Z precedes P12; freeze verify PASS on the LIGHT |
| 4. 29 task-scoped unique identities | ✅ | The plan rebuilds identically from the episodes |
| 5. Arm numbers, spend, gates, token | ✅ with a wording correction | See below |
| 6. E1: 2 identities, both GOLD b14def, F/F/F | ✅ | §3 |
| 7. Original STOP immutable; E1 has its own state | ✅ | `controller_state.json` still STOP EVAL_ERROR at P12; `controller_state_e1.json` complete |
| 8. Closed after all 29 evaluations | ✅ (state) | E1 state complete at 16:40:42Z. The commit `890c981` cannot be verified from the LIGHT, which has no git metadata. |

**Fact 5, recomputed from raw records.**

- Every applied episode's diff identity was recomputed as `sha256(json.dumps([diff]))`.
- Each of the 29 evaluation records was re-scored with the frozen D50–D52 rule, and all were identical.

| | GOLD_HARD | PLACEBO_HARD |
|---|---|---|
| Planned / APPLIED / INVALID_AFTER_REPAIR | 20 / 15 / 5 | 20 / 17 / 3 |
| F2P PASS | 2 | 0 |
| P2P-S PASS (engine count) | 14 = **9 of 15 APPLIED** + 5 PASS_BY_CONSTRUCTION | 18 = **15 of 17** + 3 |
| P2P-U200 PASS (engine count) | 15 = **10 of 15 APPLIED** + 5 PBC | 19 = **16 of 17** + 3 |
| RESOLVED (strict, frozen) | 0 | 0 |
| Architecture-scope violations | 0 | 0 |
| Replicate endpoint agreement | 0.4 | 0.8 |

- Ledger: 53 calls (40 initial + 13 repairs: GOLD 5, PLACEBO 8); 806,634 provider tokens; $0.2362465.
- Gates recomputed: A0 ✅, A1 ✅, A2 ✅ (15 ≥ 12), A3 ❌ (0 < 3), A4 ✅, A5 ❌. The token is `PILOT_A_GENERATOR_FLOOR_HOLD`.
- **Wording correction:** "P2P-S PASS 14" is a correct engine output but is not preservation evidence. It counts invalid episodes as passing by construction.

**What Pilot-A supports:**

- Under the frozen interface, the GOLD floor fails on this protected pool: 0/20 strict.
- The floor still fails under the robust preservation rule (descriptively 2/20, below A3's 3).
- At node level, GOLD gains F2P nodes in 7/20 episodes and PLACEBO in 0/20. This is a descriptive sign that the assay is scope-sensitive.

**What Pilot-A does NOT support:**

- any selector ranking;
- any RM-CSS-vs-Agent claim;
- any causal statement about why the generator fails;
- any tuned parameter.

## 3. E1_AMENDMENT_AUDIT

- **Provenance.** E1 is a post-hoc evaluator amendment. It was made after the P12 STOP, and after 17 of the 29 outcomes (all FAIL) were visible. The original STOP, the pre-amendment evaluation hashes (25 records) and every frozen file are untouched; E1 only added files. It is fully disclosed in `WP2_M14A_E1_AMENDMENT_2026-09-30.md` and in the addendum.
- **Cause (it was a defect in the brain's M14A kit).** Guard G2 was documented as "outcome-identical", but it turned patch-caused pytest startup failure into an infrastructure STOP.
- **Confirmation.** The E1 diagnostics logs show `NameError: name 'TranslationProxy' is not defined`:
  - raised from `saleor/product/models.py` line 716 (r2) and line 97 (r1);
  - inside `django.setup()` / pytest-django;
  - with rc=1 on all 6 runs of both identities;
  - with readiness `gold_empty_ok = true` for the task.

  This is exactly the static prediction made before E1 ran.
- **Direction.** The rule can only turn an unscorable STOP into FAIL/FAIL/FAIL. It cannot create a PASS. It applies to both arms alike. It restores the frozen Smoke v2.2 "missing = not passed" semantics.
- **Verdict.** Scientifically defensible, and conservative. It must always be reported as a post-hoc, outcome-conservative evaluator amendment. It changes no gate outcome: without it, those 2 identities would have stayed unscored, and A3 would still fail.

## 4. FAILURE_TAXONOMY

**Precedence** (mutually exclusive, first match wins):

1. `FORMAT_INVALID` (not APPLIED after the permitted repair)
2. `NO_SCOPE`
3. `NO_OP` (empty diff identity `16ec7951…`)
4. `PATCH_STARTUP_FAILURE` (E1 decision, or every node missing)
5. `RESOLVED` (frozen strict)
6. `F2P_PASS_PRESERVATION_FAIL`
7. `PARTIAL_F2P_PROGRESS` (0 < F2P nodes passed 3/3 < all)
8. `ZERO_F2P_PROGRESS`

**Details:**

- Preservation is split into *deterministic* failures (0/3 passed, or missing) and *intermittent* failures (1–2 of 3 passed).
- This split replaces the misleading `flaky_under_patch` list, which lumps the deterministically failing F2P nodes together with genuine flakes. The change is reporting-only and changes no gate.
- The taxonomy is recomputed in the repository by M14R phase R02, which stops if the result differs from this table.

| Task | Arm | Rep | Label | Detail | F2P nodes 3/3 | S det/int | U det/int | Strict tuple (F2P/S/U/R) |
|---|---|---|---|---|---|---|---|---|
| 012472eb8482 | GOLD | r1 | FORMAT_INVALID |  | — | — | — | FAIL/PBC/PBC/F |
| 012472eb8482 | GOLD | r2 | ZERO_F2P_PROGRESS |  | 0/5 | 0/0 | 0/0 | FAIL/PASS/PASS/F |
| 5b0e5206c5fd | GOLD | r1 | PARTIAL_F2P_PROGRESS | +DETERMINISTIC_PRESERVATION_BREAK | 3/8 | 2/0 | 0/0 | FAIL/FAIL/PASS/F |
| 5b0e5206c5fd | GOLD | r2 | ZERO_F2P_PROGRESS |  | 0/8 | 0/0 | 0/0 | FAIL/PASS/PASS/F |
| 6459dd2d9135 | GOLD | r1 | PARTIAL_F2P_PROGRESS |  | 1/2 | 0/0 | 0/0 | FAIL/PASS/PASS/F |
| 6459dd2d9135 | GOLD | r2 | PARTIAL_F2P_PROGRESS |  | 1/2 | 0/0 | 0/0 | FAIL/PASS/PASS/F |
| 6f37bd256e12 | GOLD | r1 | PARTIAL_F2P_PROGRESS | +DETERMINISTIC_PRESERVATION_BREAK | 61/62 | 0/0 | 1/0 | FAIL/PASS/FAIL/F |
| 6f37bd256e12 | GOLD | r2 | PARTIAL_F2P_PROGRESS |  | 61/62 | 0/0 | 0/0 | FAIL/PASS/PASS/F |
| a3c478408852 | GOLD | r1 | ZERO_F2P_PROGRESS |  | 0/2 | 0/0 | 0/0 | FAIL/PASS/PASS/F |
| a3c478408852 | GOLD | r2 | ZERO_F2P_PROGRESS |  | 0/2 | 0/0 | 0/0 | FAIL/PASS/PASS/F |
| a91ea48a60a7 | GOLD | r1 | FORMAT_INVALID |  | — | — | — | FAIL/PBC/PBC/F |
| a91ea48a60a7 | GOLD | r2 | FORMAT_INVALID |  | — | — | — | FAIL/PBC/PBC/F |
| b14def73518c | GOLD | r1 | PATCH_STARTUP_FAILURE |  | 0/1 | 92/0 | 200/0 | FAIL/FAIL/FAIL/F |
| b14def73518c | GOLD | r2 | PATCH_STARTUP_FAILURE |  | 0/1 | 92/0 | 200/0 | FAIL/FAIL/FAIL/F |
| b497f8d82426 | GOLD | r1 | FORMAT_INVALID |  | — | — | — | FAIL/PBC/PBC/F |
| b497f8d82426 | GOLD | r2 | ZERO_F2P_PROGRESS |  | 0/1 | 0/0 | 0/0 | FAIL/PASS/PASS/F |
| bbba01a02725 | GOLD | r1 | ZERO_F2P_PROGRESS | +DETERMINISTIC_PRESERVATION_BREAK | 0/101 | 6/0 | 1/0 | FAIL/FAIL/FAIL/F |
| bbba01a02725 | GOLD | r2 | FORMAT_INVALID |  | — | — | — | FAIL/PBC/PBC/F |
| d3847fa5f518 | GOLD | r1 | F2P_PASS_PRESERVATION_FAIL | PRESERVATION_INTERMITTENT_ONLY | 1/1 | 0/1 | 0/1 | PASS/FAIL/FAIL/F |
| d3847fa5f518 | GOLD | r2 | F2P_PASS_PRESERVATION_FAIL | PRESERVATION_INTERMITTENT_ONLY | 1/1 | 0/1 | 0/0 | PASS/FAIL/PASS/F |
| 012472eb8482 | PLACEBO | r1 | ZERO_F2P_PROGRESS |  | 0/5 | 0/0 | 0/0 | FAIL/PASS/PASS/F |
| 012472eb8482 | PLACEBO | r2 | NO_OP |  | 0/5 | 0/0 | 0/0 | FAIL/PASS/PASS/F |
| 5b0e5206c5fd | PLACEBO | r1 | NO_OP |  | 0/8 | 0/0 | 0/0 | FAIL/PASS/PASS/F |
| 5b0e5206c5fd | PLACEBO | r2 | NO_OP |  | 0/8 | 0/0 | 0/0 | FAIL/PASS/PASS/F |
| 6459dd2d9135 | PLACEBO | r1 | NO_OP |  | 0/2 | 0/0 | 0/0 | FAIL/PASS/PASS/F |
| 6459dd2d9135 | PLACEBO | r2 | ZERO_F2P_PROGRESS |  | 0/2 | 0/0 | 0/0 | FAIL/PASS/PASS/F |
| 6f37bd256e12 | PLACEBO | r1 | FORMAT_INVALID |  | — | — | — | FAIL/PBC/PBC/F |
| 6f37bd256e12 | PLACEBO | r2 | FORMAT_INVALID |  | — | — | — | FAIL/PBC/PBC/F |
| a3c478408852 | PLACEBO | r1 | ZERO_F2P_PROGRESS |  | 0/2 | 0/0 | 0/0 | FAIL/PASS/PASS/F |
| a3c478408852 | PLACEBO | r2 | ZERO_F2P_PROGRESS |  | 0/2 | 0/0 | 0/0 | FAIL/PASS/PASS/F |
| a91ea48a60a7 | PLACEBO | r1 | FORMAT_INVALID |  | — | — | — | FAIL/PBC/PBC/F |
| a91ea48a60a7 | PLACEBO | r2 | NO_OP |  | 0/2 | 0/0 | 0/0 | FAIL/PASS/PASS/F |
| b14def73518c | PLACEBO | r1 | NO_OP |  | 0/1 | 0/1 | 0/0 | FAIL/FAIL/PASS/F |
| b14def73518c | PLACEBO | r2 | NO_OP |  | 0/1 | 0/1 | 0/0 | FAIL/FAIL/PASS/F |
| b497f8d82426 | PLACEBO | r1 | NO_OP |  | 0/1 | 0/0 | 0/0 | FAIL/PASS/PASS/F |
| b497f8d82426 | PLACEBO | r2 | NO_OP |  | 0/1 | 0/0 | 0/0 | FAIL/PASS/PASS/F |
| bbba01a02725 | PLACEBO | r1 | ZERO_F2P_PROGRESS |  | 0/101 | 0/0 | 0/0 | FAIL/PASS/PASS/F |
| bbba01a02725 | PLACEBO | r2 | ZERO_F2P_PROGRESS |  | 0/101 | 0/0 | 0/0 | FAIL/PASS/PASS/F |
| d3847fa5f518 | PLACEBO | r1 | NO_OP |  | 0/1 | 0/0 | 0/1 | FAIL/PASS/FAIL/F |
| d3847fa5f518 | PLACEBO | r2 | ZERO_F2P_PROGRESS |  | 0/1 | 0/0 | 0/0 | FAIL/PASS/PASS/F |

**Aggregates:**

- GOLD: FORMAT_INVALID 5, PATCH_STARTUP_FAILURE 2, ZERO 6, PARTIAL 5, F2P_PASS_PRESERVATION_FAIL 2 (both intermittent-only), RESOLVED 0.
- PLACEBO: NO_OP 10, FORMAT_INVALID 3, ZERO 7.
- Robust-preservation RESOLVED (descriptive): GOLD 2 (d3847 r1, r2), PLACEBO 0.

**Key observations** (observed failure modes, not causes):

- The two GOLD F2P passes on d3847fa5f518 failed preservation only through **single-repetition** failures: `[failed, passed, passed]` and `[passed, failed, passed]`.
- The **empty diff of the same task** (PLACEBO r1) also fails P2P-U through a single-repetition failure. The empty diff of b14def73518c fails P2P-S the same way. So 2 of the 7 empty-diff identities in Pilot-A fail strict preservation on an unchanged tree.
- On ENG Smoke v2.2 this was 0 of 7 empty diffs; 4 of 44 evaluations there had intermittent nodes.
- **Conclusion:** "the solutions were not regression-safe" is not established. The data are consistent with evaluator nondeterminism.
- Near misses: 6f37bd256e12 61/62 F2P nodes (both replicates); 6459dd2d9135 1/2 (both); 5b0e5206c5fd 3/8.

## 5. ROOT_CAUSE_EVIDENCE

| Hypothesis | Classification | Evidence |
|---|---|---|
| H1: descriptions under-specified vs hidden tests | **Plausible, unproven** | Intents are commit titles. Pilot-A cannot isolate this cause. On ENG, some intents carry almost no information (for example dc6ac9d252df "New payload structure"). Partial F2P progress shows the model often finds the direction. |
| H2: editable-only context deprives the generator of definitions | **Plausible, unproven; not supported by Pilot-A** | b14def's defect was *inside* an editable file (a stale reference to a deleted class), so it is not a context gap. On ENG 823b the model invented model-field names that are defined in a non-editable module (anecdote only). |
| H3: one-shot generation + format-only repair limits capability | **Verified design fact; effect unproven** | The repair is triggered only by validation/format/apply/py_compile errors. Behavioural feedback would require hidden tests, which is leakage, so it is not proposed. |
| H4: py_compile misses undefined names; pyflakes catches a real class without leakage | **Directly supported (mechanism); small magnitude** | 2/20 GOLD (b14def r1, r2). pyflakes flags exactly the `TranslationProxy` NameError, which E1 logs confirm. Also seen on ENG (823b). |
| H5: strict all-or-nothing hides partial progress | **Directly supported** | 6f37 61/62 ×2, 6459 1/2 ×2, 5b0e 3/8 |
| H6 (new): strict 3/3 preservation creates false regressions | **Directly supported** | Unchanged trees fail preservation (b14def, d3847 empty diffs); both GOLD F2P passes are lost this way |

No detailed parameter was tuned on Pilot-A outcomes. The 2-of-3 rule, the caps and the thresholds were chosen *a priori*.

## 6. M14R_DESIGN_REVIEW

The factorization is clean in the frozen form below; a 4-cell independent factorial is not needed.

| Item | Frozen choice |
|---|---|
| Population | All 14 DEV_TRAIN_ENG tasks with an ENG v3 behavioural F2P set. They are guard-checked to be disjoint from all 26 Pilot-A/B/reserve tasks. |
| Readiness | Per task: a negative control (empty diff) and a positive control (scoped gold within the frozen GOLD_HARD editable set). Only READY tasks are members, at least 10. |
| Arms | GOLD_HARD with r1–r3 (primary); PLACEBO_HARD with r1 only (separation and ceiling check). |
| Factor A, context | C0 = frozen prompt; C2 = C0 + `IMPORT_OUTLINE_V1` plus one system sentence. The editable set is unchanged and hard: out-of-scope FILE blocks are rejected. |
| Factor B, static | `STATIC_UNDEFINED_V1`: after an APPLIED candidate, pyflakes UndefinedName/UndefinedLocal/UndefinedExport findings that are *new* relative to the parent file trigger exactly one extra repair. The repair message contains only those findings. An invalid repair keeps the APPLIED base, so APPLIED never goes down. |
| Variants | G0 = C0/off, G1 = C0/on (paired with G0), G2 = C2/off, G3 = C2/on (paired with G2) |
| Primary development metric | GOLD RESOLVED_ROBUST episodes per variant (3 × members). Strict RESOLVED, F2P, invalid, partial nodes, startup failures, no-ops, tokens and $ are co-reported. |
| Winner rule | A variant is eligible only if robust gain vs G0 ≥ 3, invalid ≤ G0 + 3, and #tasks better ≥ #tasks worse. Choose the maximum robust count; break ties by lower mean tokens per GOLD episode, then by G0 < G1 < G2 < G3. If no variant is eligible, the winner is G0. |
| Floor for M15 recommendation | Winner robust ≥ ceil(0.20 × 3n) **and** tasks with ≥1 robust resolve ≥ ceil(n/3) **and** every PLACEBO robust count ≤ 1 |
| Tokens | `M14R_FLOOR_MET`, `M14R_FLOOR_NOT_MET`, `M14R_PLACEBO_LEAK_REVIEW`, `M14R_INSTRUMENT_FIX` (none auto-starts anything) |
| Budget | Authorization cap ≤ $3.00; worst-episode reserve $0.12; expected about $1.1 |
| Time | Readiness about 2.5–3 h, generation about 1.5 h, evaluation about 8–10 h, all resumable |
| Stops | Provider outage, HOLD and rejection are resumable STOPs, never outcomes. An evaluation infrastructure failure gives a resumable EVAL_ERROR with diagnostics. An invariant or drift gives a non-resumable STOP to the brain. Model failures are outcomes. |

**Answers to E1–E10:**

1. Which tasks? All ENG tasks with F2P, gated by readiness.
2. Which arms? GOLD for capability, plus PLACEBO r1 per context for the separation check.
3. How many replicates? 3 GOLD replicates, because agreement was 0.4.
4. Is G0 reused? No: G0 is re-run contemporaneously.
5. Which primary metric? RESOLVED_ROBUST, with strict co-reported.
6. Tie-breakers: as in the table above.
7. What spend cap? $3.
8. Which stop semantics? As in the table above.
9. How is tuning on Pilot-A avoided? Pilot-A is used only for:
   - the existence of the floor;
   - the evaluator-noise observation;
   - the generic undefined-name failure class.

   Everything else is chosen on ENG with a priori constants.
10. **FLOOR_MET** → human decision, then an M15 amendment. **FLOOR_NOT_MET** → keep the frozen generator and take a human decision on reshaping WP2 (for example, reporting WP2 as a documented assay limitation, or a separately preregistered model change). **PLACEBO_LEAK/INSTRUMENT** → brain review.

## 7. M15_AFTER_M14R

**Options considered:**

- **Option "use the M14R winner directly with an internal GOLD floor gate" (recommended).** M15 freezes the winner's code and hashes, and keeps Pilot-B's GOLD_HARD reference arm with a pre-declared floor gate: GOLD RESOLVED_ROBUST ≥ gates_for(n), the A3 analogue, which is 3/20 for the REDUCED_10 Pilot-B. If that gate fails, M15 declares the selector comparison uninformative and makes no selector claim.
- **A new protected calibration set is not recommended.** The protected pool is exhausted: 26 tasks have been through readiness.
- **Pilot-A is never reused as confirmatory evidence.**

**Endpoint:** the M15 amendment should freeze RESOLVED_ROBUST as primary and strict as co-reported, *before* any Pilot-B generation.

**SIP** stays WP1-only. Adding it as an E2E arm would need its own preregistered decision.

## 8. AG16_AGENT_V2_INTERACTION

- **No shared code or evidence.** M14R changes only the repair generator. AG16 and Agent-v2 change only the WP1 file-selector agent. They share no code path and no evidence root.
- **M15 is not affected.** M15 keeps the frozen protocol-v3 Agent (D5), whatever AG16 shows.
- **They can run independently**, but not at the same time on the same repository: two controllers committing and pushing concurrently can collide. Run AG16 before or after an M14R session, not during it.
- **Agent-v2**, if pursued, is a separate preregistered WP1 study. It must not enter M15 without a new design freeze.

## 9. RISKS_AND_LEAKAGE_BARRIERS

**Leakage barriers:**

- No hidden-test feedback.
- No F2P/P2P ids, changed-test paths, target diff or target-only lines in any prompt.
- The read-only context is built from the parent snapshot only. Every line is audited as verbatim, and a blocking scan runs at freeze.
- Editable scopes stay hard.
- Evaluator sets are read only by evaluator-side code (the frozen loader refuses generator-side callers).
- No protected task is ever generated or evaluated.

**Residual risks:**

- **Host dependence.** pyflakes and the host Python version determine G1 findings and which py3.12 modules can be parsed for G2. Both are recorded in the freeze.
- **Task dependence of evaluator flakiness.** ENG may be less flaky than Pilot-B.
- **ENG floor may not transfer.** An ENG floor does not guarantee a Pilot-B floor, which is why the internal M15 gate exists.
- **Low power.** With 3 × n episodes per variant, M14R is a development selection, not a confirmatory claim.
- **Prompt cost.** C2 adds up to about 10k prompt tokens per call; this is measured and reported.

## 10. EXACT_NEXT_MISSION

**Mission M14R-V1.**

- **Executors:** OpenCode builds only; the human runs the controller; the controller makes every transition.
- **Kit:** `WP2_M14R_INSTALL_2026-09-30.py`.
- **Git permissions:** the controller commits and pushes evidence, and pushes exact tags only (never `--tags`).
- **Docker/WSL:** used in R03 and R13 (and the doctor). **API:** used only in R09 and R10.

**Task T1 — install (OpenCode, zero API/Docker).**

| Atomic | Executor | Inputs | Outputs | Checks | PASS → | FAIL/STOP |
|---|---|---|---|---|---|---|
| T1.A1 Verify installer hash | OpenCode | installer file | printed sha | equals the value in the human message | T1.A2 | `MISSION_M14R_STOPPED` |
| T1.A2 Run installer | OpenCode | repository at HEAD == origin/main, Pilot-A closed | 12 kit files, commit, tag `wp2-m14r-v1-kit-2026-09-30` | frozen M14A/E1 file hashes, Pilot-A summary pin, kit tests, verify-kit, dry-run | T2 (human) | `M14R_INSTALL_STOP` (rolled back) |

**Task T2 — zero-API readiness (human runs `--until R04_MEMBERSHIP`).**

| Atomic | Does | Output | PASS → | STOP token (resumable?) |
|---|---|---|---|---|
| R00 | kit self-tests | — | R01 | KIT_SELFTEST_FAIL (no) |
| R01 | guard: design sha, Pilot-A immutability, E1 pin, protected-pool disjointness, ENG sets hash | m14r_guard.json | R02 | M14R_GUARD_FAIL (no) |
| R02 | Pilot-A taxonomy, cross-checked against §4 | analysis/pilot_a_taxonomy.json, docs taxonomy | R03 | M14R_INVARIANT (no) |
| R03 | per task: negative + scoped-gold positive controls (loop) | readiness/<task>/record.json | R04 | READINESS_ENV_FAIL (yes) |
| R04 | membership (≥10 READY) | m14r_membership.json | pause | POOL_INSUFFICIENT (no → human) |

**Task T3 — authorization (human):** `scripts/wp2_m14r_authorize.py`. The token is `I_AUTHORIZE_WP2_M14R_V1=YES`, the cap is ≤ $3.00, and the authorization is bound to the design and membership hashes. The script commits and pushes the file.

**Task T4 — paid probe and evaluation (human runs the plan to completion).**

| Atomic | Does | Output | PASS → | STOP token (resumable?) |
|---|---|---|---|---|
| R05 | auth-check | auth_check.json | R06 | NOT_AUTHORIZED (yes) |
| R06/R07 | offline doctor (+pyflakes) and paid doctor (credit ≥ $5, read-only) | doctor/*.json | R08 | PAID_PREFLIGHT_FAIL (yes) |
| R08 | freeze: scopes, contexts + audits, plans, hashes; tag freeze | m14r_freeze.json… | R09 | FREEZE_FAIL / M14R_INVARIANT (no) |
| R09 | base generation: GOLD 3 reps + PLACEBO 1 rep, each × contexts C0/C2 (8 episodes per member task) | episodes/…__C0__/__C2__ | R10 | E2E_PROVIDER_OUTAGE / HOLD_ACTIVE / USER_STOP_FLAG (yes); E2E_BUDGET_STOP, E2E_REQUEST_REJECTED, M14R_INVARIANT (no) |
| R10 | paired static stage | episodes/…__C0S__/__C2S__ | R11 | same as R09 |
| R11 | generation freeze + tag | generation_freeze.json | R12 | GENERATION_FREEZE_FAIL (no) |
| R12 | unique-diff evaluation plan | evaluations/plan.json | R13 | EVAL_PLAN_FAIL (no) |
| R13 | evaluate (loop, E1 semantics; the empty diff comes from the readiness negative control) | evaluations/unique/… | R14 | EVAL_ERROR (yes) |
| R14 | summary + frozen decision | m14r_summary.json, docs/WP2_M14R_V1_RESULT.md | final: commit, push, tag, LIGHT | SUMMARY_FAIL (no) |

## 11. FILES_TO_CREATE

- **Created by the installer:**
  - `scripts/wp2_m14r_core.py`
  - `scripts/wp2_m14r_run.py`
  - `scripts/wp2_m14r_authorize.py`
  - `controller/plan_m14r_v1.json`
  - `controller/light_profile_m14r.json`
  - `controller/KIT_MANIFEST_M14R.json`
  - `research/wp2/m14r_v1/m14r_design_freeze_v1.json`
  - `tests/unit/wp2/m14r/test_m14r.py`
  - `docs/WP2_M14R_INDEPENDENT_REVIEW_2026-09-30.md` (this file)
  - `docs/WP2_M14R_DESIGN_FREEZE_2026-09-30.md`
  - `docs/MISSION_M14R_INSTALL_2026-09-30.md`
  - `docs/MISSION_M14R_HUMAN_RUN_2026-09-30.md`
- **Created later by the controller:** everything under `research/wp2/m14r_v1/`, plus `docs/WP2_M14R_PILOT_A_TAXONOMY.md` and `docs/WP2_M14R_V1_RESULT.md`.
- **Never modified:** every Pilot-A, M14A, E1, Smoke and design artifact.
