# WP2 M16 — OPWS-MAIN Review Package **v2** (design only, nothing executed)

Date: 2026-10-02 · Author: brain (Claude) · Status: **REVIEW DRAFT v2 — not frozen, not installable**
Supersedes: `WP2_M16_OPWS_MAIN_REVIEW_PACKAGE_2026-10-02.md` (v1). v1 stays as the review record.

No experiment, no Docker/WSL command, no model/API call, and no installer or controller were run or built to produce v2. M15-R remains closed with `M15R_GOLD_FLOOR_FAIL_NO_GENERATION_CLAIM`; none of its artifacts is modified or re-interpreted.

> **Brain attestation (unchanged from v1):** no selector-vs-gold overlap (coverage class, recall, F1, P_S) was computed on any MAIN subset. Only selector-blind quantities were computed.

---

## 0. What changed from v1

### Reviewer decisions adopted

| # | Reviewer decision (2026-10-02) | Where in v2 |
|---|---|---|
| Q1 | Formal pre-run `M16/L-OPWS` quarantine amendment | §1 (exact text) |
| Q2 | Route B: V3 eligibility on all 220 frozen changed-test-evidence tasks, then selector-blind readiness, then the full READY census; V2-71 not used as frame | §5, §7 |
| Q3 | P2P-U200 included with P2P-S in `OPWS_ROBUST` | §5.3, §5.4 |
| Q4 | `OPWS_ROBUST` primary; δ = θ_RMCSS − θ_AGENT_MAIN primary paired estimand; Tango primary, Newcombe sensitivity, McNemar exact + mid-p supporting | §2, §4 |
| Q4b | **Estimation-first. No confirmatory NI/equivalence margin. ±0.10 is a descriptive interpretation band only. No `NONINFERIOR` / `EQUIVALENT` tokens.** | §2, §3, §4 |
| H4 | Transportability downgraded to descriptive | §2 |

### Corrections to v1 (found while writing v2 — please re-check)

- **C1 — storage premise was wrong.**
  - v1 said V3 might persist per-task environments of about 0.15 GB/task (~30 GB). That figure came from the **V2** Windows-side envs.
  - **Harness V3 persists no per-task environment.** Each state runs in `docker run --rm` and installs into `/opt/venv` inside the ephemeral container (`benchmark/wp2/harness_v3.py::run_state_v3`).
  - What persists is:
    - the shared uv wheel cache volume `wp2-uv-cache` (21 GB, PROTECTED_EVIDENCE per `POST_RUN_STORAGE_AUDIT`);
    - the Docker/WSL data inside the Ubuntu-24.04 `ext4.vhdx` on C: (63.12 GiB on 2026-09-28);
    - the JUnit/record evidence on the Windows side.
  - The `D:\wp2_cold` plan is restated on this corrected basis in §6.
- **C2 — the existing C4-V3 runner hard-stops at 32 GiB free on C:.**
  - `scripts/wp2_m10b_phase5_c4_v3.py` has `C_FREE_HARD_STOP_GIB = 32.0`.
  - The V2 P2P-U executor `scripts/wp2_p2p_u_v2_exec.py` also stops below 32.0. The V3 P2P-U runner `scripts/wp2_m10b_p2pu_v3_eng.py` has no free-space guard.
  - Current C: free is about 33.3 GiB (user-reported).
  - So Route B cannot run with the old threshold unless headroom is created or M16 declares its own infrastructure thresholds (§6).
- **C3 — runtime basis now uses measured ENG V3 wall times.**
  - C4-V3: median 4.3 min/task (max 12.4). This median covers all 29 ENG tasks, including 7 install-blocked ones; the DONE-only median is 5.2 min. ENG ran 2 tasks in parallel.
  - P2P-U200: median 6.4 min (max 10.6).
  - V3 rediscovery: 0.8 min.
  - These replace v1's planning rates where they differ (§6).
- **C4 — the "editable" filter (D35) is part of the frozen scope definition.**
  - Rule: the file exists at parent; it is non-test; it is ≤ 120,000 decoded characters; files are then added greedily in alphabetical order, skipping any file that would push the cumulative total over 300,000.
  - The "text" check is a no-op, because decoding uses `errors='replace'`.
  - It applies identically to GOLD and to every selector, so coverage classes are now defined on the filtered sets (§5.4).

### New instrument findings from the independent code audit of v2 (both need a reviewer decision)

- **C5 — the frozen C4-V3 oracle construction collapses its 3 repetitions to the last one** (`run_state_v3` merges with `dict.update`; `phase5.run_task` uses `[outcome]*3`).
  - Consequence: "FLAKY" and "stable 3/3" are not actually checked on changed-test nodes.
  - The same holds for the historical ENG V3 sets. That is a limitation to disclose, not something to re-interpret.
  - The OPWS/readiness evaluator and the P2P-U V3 executor keep per-repetition outcomes.
  - Decision **R1** is in §12.
- **C6 — several frozen V3 functions are hard-wired to DEV inputs.**
  - Affected: census, era and the **locked dev/test closure**. `v31_dev_closure` returns `mechanism = none` for every MAIN task.
  - Without an explicit MAIN adapter, MAIN poetry-era tasks would silently install **without** their dev/test group, repeating the V2 defect that motivated Route B.
  - Decision **R2** is in §12; the rule is in §5 (intro).

---

## 1. Exact quarantine amendment text (Q1)

The text below is committed verbatim as `research/wp2/m16_v1/m16_l_opws_quarantine_amendment.json` (field `text`) and appended to `DECISIONS.md`. It is tagged and pushed **before** phase Q00 of M16 may start (gate in §7). Its sha256 is pinned in the M16 design freeze.

```text
M16/L-OPWS — MAIN QUARANTINE AMENDMENT (pre-run, pre-outcome)

Status: adopted before any M16 phase runs; recorded, tagged and pushed to origin
before the first M16 Docker phase. It amends, and does not replace,
research/wp2/main_generation_quarantine_2026-09-23.json
(sha256 4de0833958ec1b54bb4307f7ee34d3ffdbe4b9029a31c78975e0a1c130019766).

1. Scope. MAIN = the 297 task ids of research/wp1b/wp1b_main_297_manifest.json
   (task_ids_sha256 1678dbaa…, file sha256 d8583166…). Nothing in this amendment
   applies to INTERNAL_TEST or RESERVE, which remain sealed and untouched.

2. What remains prohibited on MAIN (unchanged and extended):
   code generation; prompt design or tuning; repair or retry-policy tuning;
   generator debugging; Smoke; assay Pilot; selector training, re-fitting,
   re-thresholding or re-running; Agent re-localization; any threshold, cap,
   margin or rule tuning informed by MAIN outcomes.

3. What M16 is permitted to do on MAIN (and nothing else):
   (a) zero-model-API evaluator/oracle construction under frozen harness V3
       (C4-V3 classification, P2P-S, P2P-U200 rediscovery and execution);
   (b) zero-model-API, selector-blind readiness (empty-diff negative control,
       scoped-gold positive control);
   (c) zero-model-API OPWS: applying the developer's own non-test patch,
       restricted to the editable files of selections that were already frozen
       in WP1 (RM-CSS realization A, threshold 0.2, from
       research/wp1a/sip_rmcss_per_task_predictions.json; Agent protocol v3 main
       run and the 15x3 variance replicates, from research/wp1b/), and scoring it
       with the frozen evaluator.
   No new selection of any kind is produced by M16.

4. Binding constraints on the use of M16 outcomes. "M16 outcomes" means every
   M16 artifact that depends on a selector's editable set: P_S, coverage class,
   OPWS records and every summary statistic. These outcomes must not be used to
   alter: task membership of any study; selector parameters or thresholds;
   prompts; caps, margins or decision rules; or the design of any later MAIN
   study. M16 outcomes may be reported, analysed as pre-registered, and cited.

5. Later MAIN studies. Any later end-to-end (generation) evaluation on MAIN must
   use either (i) the full frozen M16 V3-READY census, with no subsetting by any
   M16 outcome, or (ii) a separately protected pool untouched by M16. The
   V3-READY census itself is selector-blind and may be reused as a frame.

6. Irrevocability. This amendment cannot be relaxed after any M16 outcome
   artifact exists. Any later change to the MAIN quarantine requires a new
   decision record that states explicitly that M16 outcomes were known, and it
   cannot retroactively validate a use prohibited in section 4.

7. Violation. Any use prohibited in sections 2 or 4 invalidates the affected
   later claim, and the violation is recorded in DECISIONS.md. M16's own claims
   remain those of its frozen design.
```

---

## 2. Revised research question, estimands, hypotheses (estimation-first)

**RQ.** On Saleor MAIN tasks that have a valid V3 behavioral oracle and pass selector-blind readiness: when the developer's own non-test patch is restricted to the editable files of a frozen WP1 selection, how often does it still pass the hidden tests robustly? By how much does that execution-grounded sufficiency differ between the WP1 RM-CSS selection and the WP1 Agent main-run selection?

**Population.** T* = the V3-READY census (§5.1–§5.2). It is finite and fully enumerated. CIs are read under a superpopulation model: comparable Saleor tasks with the same eligibility mechanism.

**Outcome.** Y_S(t) = `OPWS_ROBUST` ∈ {0, 1} (§5.4).

### Estimands

| ID | Estimand | Role | Interval |
|---|---|---|---|
| **E-P** | δ = θ_RMCSS − θ_AGENT_MAIN, where θ_S = mean over T* of Y_S(t) | **primary** | Tango asymptotic score 95% CI; Newcombe hybrid-score 95% CI (sensitivity) |
| E-S1 | θ_RMCSS and θ_AGENT_MAIN; θ_GOLD is an invariant equal to 1 | secondary | Clopper–Pearson 95% (none for θ_GOLD) |
| E-S2 | Decomposition θ_S = P(FULL_S) + P(PARTIAL_S ∧ Y_S = 1), with rescue rate π_S = P(Y_S = 1 \| PARTIAL_S) | secondary | Clopper–Pearson 95% for each term |
| E-S3 | δ_STRICT, the same contrast on `OPWS_STRICT` | secondary | Tango 95% |
| E-D1 | Transportability (H4 downgraded): WP1 per-task F1 difference on T* vs on its complement vs on all 297; sign agreement with δ̂ | **descriptive only** | bootstrap percentile, labelled descriptive |
| E-D2 | Agent replicate behaviour on the replicate-overlap subset (§8) | descriptive only | none (counts) |
| E-D3 | Sufficiency per editable file and per editable character (over-selection cost) | descriptive only | none |

### Hypotheses

**There is no confirmatory hypothesis that gates a claim.** The study is designed to estimate.

The only pre-declared statistical test is a **supporting** test of H0: δ = 0, run two-sided as the exact conditional McNemar test (primary supporting) with the mid-p McNemar co-reported. It is reported alongside the CI and never replaces it.

### Why there is no NI/equivalence margin

- An NI margin needs an outcome-independent, substantive argument that losing up to Δ sufficiency is acceptable. We have none.
- The WP1 margin (0.05) was on a different construct (file-level F1). Any loss in OPWS sufficiency propagates into an unknown loss in downstream repair success, which M15-R could not measure (its gold floor failed).
- The ±0.10 band (§3) is therefore only a **descriptive yardstick**, adopted for interpretation before any outcome is seen. It confers no claim.

### Why H4 is descriptive

F1 (a file-overlap construct) and OPWS (an execution-sufficiency construct) measure different things. Sign agreement between them is not evidence for a hypothesis about either. E-D1 is reported only to show whether the WP1 contrast on T* resembles the WP1 contrast on all 297 (representativeness).

---

## 3. Revised decision-token scheme (no winner labels)

The final summary carries exactly **three** fields. None of them names a winner.

**Field 1 — `run_status`** (instrument and pool). Exactly one token is issued, by precedence: `M16_STOP_<reason>` > `M16_INSTRUMENT_REVIEW` > `M16_POOL_INSUFFICIENT_DESCRIPTIVE_ONLY` > `M16_OPWS_COMPLETE`.

| Token | Condition |
|---|---|
| `M16_OPWS_COMPLETE` | every planned identity has a valid record or is listed `INFRA_UNRESOLVED`; listwise drops ≤ 10% of READY; E1/E1A1 amended items ≤ 10%; n_READY ≥ 40 |
| `M16_POOL_INSUFFICIENT_DESCRIPTIVE_ONLY` | n_READY < 40 (all estimates reported; Fields 2–3 set to `NOT_ISSUED`) |
| `M16_INSTRUMENT_REVIEW` | listwise drops > 10% of READY, or E1/E1A1 amendment items > 10% of evaluated items |
| `M16_STOP_<reason>` | resumable or terminal stop (§5.5); this includes `M16_STOP_GOLD_IDENTITY` for any GOLD OPWS ≠ 1 |

**Field 2 — `ci_position`** (Tango 95% CI [L, U] for δ; issued only with `M16_OPWS_COMPLETE`):

| Value | Condition |
|---|---|
| `DIFFERENCE_CI_EXCLUDES_ZERO_POSITIVE` | L > 0 |
| `DIFFERENCE_CI_EXCLUDES_ZERO_NEGATIVE` | U < 0 |
| `DIFFERENCE_CI_INCLUDES_ZERO` | L ≤ 0 ≤ U |

**Field 3 — `band_position`** (relation of [L, U] to the descriptive band [−0.10, +0.10]; issued only with `M16_OPWS_COMPLETE`):

| Value | Condition |
|---|---|
| `CI_INSIDE_DESCRIPTIVE_BAND` | −0.10 < L and U < 0.10 |
| `CI_CROSSES_BAND_EDGE` | exactly one of L ≤ −0.10 or U ≥ 0.10 holds, **and** −0.10 < U **and** L < 0.10 |
| `CI_WIDER_THAN_BAND` | L ≤ −0.10 and U ≥ 0.10 |
| `CI_OUTSIDE_BAND` | U ≤ −0.10 or L ≥ 0.10 |

For any L ≤ U, exactly one `band_position` value applies.

**Supporting flag — `method_agreement`.** Records whether Tango, Newcombe, exact McNemar (α = 0.05) and mid-p McNemar agree on whether zero is excluded. Values: `CONCORDANT` or `DISCORDANT`. If `DISCORDANT`, the claim template adds the sentence: "Inference about whether the difference is zero is method-sensitive."

**Why not `RMCSS_HIGHER_ESTIMATE` / `AGENT_HIGHER_ESTIMATE`.** A token named after the sign of the point estimate turns noise into a label when the CI includes zero. The sign and size of δ̂ are always reported as numbers, never as a token.

**Claim templates** (filled mechanically; the bracketed scope sentence is mandatory in every template):

- **`DIFFERENCE_CI_INCLUDES_ZERO`:** "On n MAIN tasks [scope], the difference in robust OPWS sufficiency (RM-CSS minus Agent single run) was δ̂ = x points (Tango 95% CI L to U). The data are compatible with no difference and with differences anywhere in that interval. M16 does not show that either selection is more sufficient, and it does not show that they are equivalent."
- **`…EXCLUDES_ZERO_POSITIVE` / `…NEGATIVE`:** "On n MAIN tasks [scope], RM-CSS selections were sufficient more often / less often than the Agent's single-run selections: δ̂ = x points (Tango 95% CI L to U; exact McNemar p = p). This is a statement about this census and these frozen selections, not about selector quality in general."
- **Band sentence** (appended in every case): "Relative to the pre-declared ±10-point descriptive band, the interval lies <inside / across one edge of / wider than / outside> the band. The band is an interpretive yardstick, not a non-inferiority or equivalence margin."
- **Mandatory scope sentence `[scope]`:** "Saleor only; tasks with changed-test evidence, a V3-installable environment, ≥ 1 V3 behavioral F2P node and a passing selector-blind readiness check; gold restricted to modified/deleted non-test files (added and renamed files excluded); one Agent run per task."

**Forbidden in any M16 text:**
- "non-inferior(ity)" or "equivalent/equivalence" in any affirmative or claim-bearing form. The only permitted occurrences are the fixed negations in the claim templates above;
- "RM-CSS is as good as / better than the Agent" without the CI and scope;
- any end-to-end or repair claim;
- generalisation beyond T*;
- pooling with M15-R;
- re-statement of WP1's NI at 0.05 on this endpoint;
- every WP1B claim-sheet forbidden sentence.

---

## 4. Statistics and operating characteristics

### Paired 2×2 table on T* (after listwise drops)

|  | AGENT_MAIN = 1 | AGENT_MAIN = 0 |
|---|---|---|
| **RMCSS = 1** | a | b |
| **RMCSS = 0** | c | d |

- **Point estimate:** δ̂ = (b − c)/n.
- **Primary interval:** Tango score CI (Tango 1998). This is one of the intervals recommended by Fagerland et al. (2014).
- **Sensitivity interval:** Newcombe method 10 (Newcombe 1998).
- **Supporting tests:**
  - exact conditional McNemar, two-sided (McNemar 1947);
  - mid-p McNemar (Fagerland, Lydersen & Laake 2013).

### Also reported

- the 3×3 coverage cross-table (RMCSS class × Agent class) with OPWS passes in each cell;
- a per-task disagreement listing (cells b and c) with editable sizes, classes, F2P count, era and the failing side's taxonomy;
- per-selector file-level P/R/F1 against G_raw, and editable files and characters;
- per-era and per-gold-size-tercile δ̂ (descriptive).

### Operating characteristics

These are reported because n is fixed by the census, so a power calculation cannot choose n. ψ is the discordant-pair rate.

- The 95% half-width uses the normal approximation 1.96·√(ψ/n), with the variance taken at δ = 0.
- MDE = (1.96 + 0.84)·√(ψ/n).
- Because |δ| ≤ ψ, an MDE ≥ ψ cannot be reached.

These are approximations for planning, not claims.

| n READY | ψ = 0.10 | ψ = 0.20 | ψ = 0.30 | MDE (80%, two-sided) at ψ = 0.10 / 0.20 / 0.30 |
|---|---|---|---|---|
| 40 | ±0.098 | ±0.139 | ±0.170 | unattainable (> ψ) / ≈ ψ (0.20) / 0.24 |
| 60 | ±0.080 | ±0.113 | ±0.139 | unattainable (> ψ) / 0.16 / 0.20 |
| 80 | ±0.069 | ±0.098 | ±0.120 | ≈ ψ (0.10) / 0.14 / 0.17 |
| 100 | ±0.062 | ±0.088 | ±0.107 | 0.09 / 0.13 / 0.15 |
| 120 | ±0.057 | ±0.080 | ±0.098 | 0.08 / 0.11 / 0.14 |

M15-R (a different pool, n = 10) observed ψ between 0 and 0.3. RMCSS vs the Agent majority was discordant on 1/10 tasks; vs single replicates r1/r2/r3, on 1/0/3 of 10.

**Interpretation:** at the projected n of 60–110, the study can detect only differences of roughly 10–20 points. Smaller true differences will usually produce `DIFFERENCE_CI_INCLUDES_ZERO`. The claim templates in §3 are worded so that this outcome is reported as uncertainty, not as sameness.

---

## 5. Exact frozen rules

Every rule below reuses frozen code paths. Where MAIN needs an adapter, the adapter changes **inputs only**, never semantics. Each adapter is verified by an identity regression (Q02, §7).

The inputs that are currently hard-wired to DEV are:
- **commits:** `scopes.commits_of` and `phase5.task_commits` (DEV census);
- **era key:** `evaluate_state_safe`, `harness_v3._era_for` and `rediscover_v3.inventory_row` (DEV inventory). The MAIN inventory has no `era_key`; the MAIN era source is `per_task_v2.jsonl` (`era_key`, all 220 tasks);
- **locked dev/test closure:** `harness_v3.v31_dev_closure` looks the target commit up in the **DEV** census. For every MAIN task it currently returns `mechanism = none`, so the install fragment becomes `NO_LOCKED_DEV_GROUP`. MAIN poetry-era tasks would then silently run **without** their dev/test group, which is exactly the V2 defect;
- **evaluator sets and predictions files.**

Q02 must therefore assert two things:
- ENG dev-closure outputs are byte-identical through the adapter;
- for every MAIN task whose target manifests declare a dev group, the MAIN closure `mechanism` is not `none`.

### 5.1 Eligibility (selector-blind; fixed before Q03)

A task t is **V3-ELIGIBLE** iff **all** of the following hold:

1. t ∈ MAIN_297 (manifest sha256 `d8583166…`; `task_ids_sha256 1678dbaa…`).
2. t ∈ the frozen oracle selection `wp2_oracle_confirmation_selection_2026-09-22.json` (sha256 `8e7ba9df…`): the 220 tasks = 20 STRONG_F2P_CANDIDATE + 200 MODIFIED_TEST_CANDIDATE. The 77 NO_CHANGED_TEST_EVIDENCE tasks are excluded by construction.
3. **Oracle construction ran under harness V3.**
   - Spec: `harness_v3_spec.json`, sha256 `5d0ec5e7…`; library `benchmark/wp2/harness_v3.py`.
   - Method: the per-task procedure of `scripts/wp2_m10b_phase5_c4_v3.py`, unchanged.
     - Parent worktree = parent commit + the frozen test patch (`derive_test_patch_linux`; test paths by the frozen V2 regex, `test-path-rule-v1`).
     - Target worktree = target commit.
     - One container per state (`run_state_v3`): fresh DB, lock-exact install (LOCKFILE-FIRST; `LOCK_EXACT_MAIN_PLUS_DEV` preferred), `--ulimit nofile=65536`, 3 repetitions per changed-test file, workers = 1.
   - Status == `DONE`.
     - `ENV_INSTALL_BLOCKED` means the task is ineligible.
     - `CLOCK_BLOCKED` or `ERROR`, a nonzero docker rc without `ALL_RUNS_DONE`, or any `JUNIT_MISSING_*` is **infrastructure**. It is retried under the infra rule and is never an oracle negative.
     - The frozen `run_state_v3` returns `error = None` for a docker failure that lacks an `INSTALL` marker. The M16 engine therefore adds an infra classifier that inspects rc and `ALL_RUNS_DONE`. This is detection only; no semantic change.
     - A uv download or network failure during install is classed as infra (retried), not `ENV_INSTALL_BLOCKED`. `ENV_INSTALL_BLOCKED` requires the frozen deterministic resolver/lock failure markers on 2 consecutive attempts.
   - **Disclosure: repetitions are collapsed in the frozen C4-V3 path.**
     - `run_state_v3` merges repetitions with `dict.update`, so the last repetition wins.
     - `phase5.run_task` then passes `[outcome]*3` to `classify_node_v2`.
     - The 3 repetitions are executed, but classification uses repetition 3 only. FLAKY arises only for nodes that are skipped or missing. In ENG evidence, 0 of 2,031 node records have non-identical triples. PARENT_COLLECTION_ERROR is in practice unreachable.
     - This also applies to the historical ENG V3 sets used by M14R and M15-R. They are not re-interpreted here.
     - The frozen OPWS/readiness evaluator (`wp2_m14a_evalcore`) and the P2P-U V3 executor **do** keep per-repetition outcomes.
     - **Reviewer decision R1** (§12): either accept as frozen, or amend oracle construction to retain per-repetition outcomes, which restores the declared `3_plus_3_stability_policy`. The amendment would be applied identically to all 220 tasks before Q03.
4. **Node classification** by `benchmark.wp2.oracle_semantics_v2.classify_node_v2` (semantics `oracle-semantics-v2-2026-09-23`), with frozen precedence:
   FLAKY > TARGET_ORACLE_INVALID > P2P_ONLY > PARENT_COLLECTION_ERROR > SYMBOL_ABSENCE_F2P > BEHAVIORAL_F2P > OTHER_REVIEW_REQUIRED.
5. **Task eligibility** by `task_eligibility_v2`: `PRIMARY_BEHAVIORAL_F2P_ELIGIBLE` = (n_behavioral_f2p ≥ 1) ∧ environment_valid ∧ ¬task_collection_failure.
   - In the frozen C4-V3 runner, `environment_valid` and `task_collection_failure` are constants (True and False), so the rule reduces to n_behavioral_f2p ≥ 1 on a DONE task.
   - Symbol-absence-only tasks are not eligible (consistent with M14R/M15-R).
6. t ∉ INTERNAL_TEST, RESERVE, Pilot-A, Pilot-B, ENG or M14R memberships (`assert_task_allowed` plus explicit set checks).

**Infra handling at this stage.** A resumable infrastructure failure (`INFRA_EXC`/`OSError`, Docker/WSL unavailable, `CLOCK_BLOCKED`) is retried as the same task, up to 3 attempts in total. After that the task is recorded as `ORACLE_INFRA_UNRESOLVED`: ineligible and listed. It is never treated as an oracle negative.

**Freeze.** The output `m16_v3_eligibility.json` holds per-task classification, counts, node records hash and evidence sha256. It is committed and tagged `wp2-m16-v1-eligibility-*`, then pushed.

### 5.2 Readiness (selector-blind; per V3-ELIGIBLE task)

The function is identical to `wp2_m15r_run.readiness_task`. Only the evaluator sets differ: the MAIN V3 sets from §5.1 and §5.3.

**Negative control.** Materialize the empty diff, then run `evaluate_state_safe` (3 repetitions, fresh DB, workers = 1). The control is valid iff `score_strict.f2p_task == "FAIL"` **and** `score_robust.p2p_s_task ∈ {PASS, UNDEFINED}` **and** `score_robust.p2p_u200_task ∈ {PASS, UNDEFINED}`. Otherwise the task is `NOT_READY_NEGATIVE_CONTROL_INVALID`.

**Positive control.**
- `diff` = `scoped_gold_diff(t, GOLD_HARD.editable)`: the gold non-test diff restricted to GOLD_HARD editable files (§5.4).
- If `diff` is empty → `NOT_READY_EMPTY_SCOPED_GOLD`.
- If it does not apply → `NOT_READY_SCOPED_GOLD_DOES_NOT_APPLY`.
- Otherwise evaluate with `evaluate_state_e1(…, parent_starts_ok=True)` plus E1A1 semantics (§5.5). If `score_robust.resolved` is false → `NOT_READY_SCOPED_GOLD_NOT_RESOLVED`.

**Decision.** `READY` iff none of the above applies. The decision is a **pure function** of the stored evidence (`decide_ready(record)`). A verifier can recompute membership from evidence with no human discretion (§7, proof step V3).

**Infra.** Same as §5.1: 3 attempts, then `NOT_READY_INFRA_UNRESOLVED` (listed).

**Freeze.** `m16_ready_membership.json` holds READY ids sorted, every non-READY task with its reason, the evidence hashes and `ready_membership_sha256`. It is committed and tagged `wp2-m16-v1-ready-*`, then pushed. The **pool gate** is evaluated here: n_READY ≥ 40, or `M16_POOL_INSUFFICIENT_DESCRIPTIVE_ONLY` is fixed in advance.

### 5.3 P2P-S and P2P-U200 evaluator sets (per V3-ELIGIBLE task, before readiness)

**P2P-S.**
- Nodes in the changed/test-patch scope classified P2P_ONLY by the frozen C4-V3 path in §5.1.
  - Definition: stable PASS 3/3 on both states.
  - As executed: PASS in the final repetition, unless R1 is amended (see §5.1).
- This is the same definition as `wp2_dev_p2p_s_v1` and `p2p_s_v3_eng`. There is no cap.
- If there are 0 nodes, `p2p_s_task` is UNDEFINED, which is passish under the frozen scoring.
  - UNDEFINED is passish only for the `resolved` flag. The P2P-S artifacts' "never automatic PASS" refers to metric denominators.
  - The number of tasks with an UNDEFINED P2P-S or P2P-U200 set is reported.

**P2P-U200.**
- **Candidate files:** the frozen MAIN unchanged-test inventory `wp2_unchanged_p2p_candidate_inventory_v1_final_2026-09-25.json` (file sha256 `87d20d5e…`; `inventory_sha256 f405144c…`), field `associated_unchanged_test_files`. The association rule is: unchanged test file, same top-level Saleor app as a touched production file.
- **Node discovery:** V3 rediscovery exactly as ENG `p2p-u-v3-eng-rediscovery-2026-09-26` (`scripts/wp2_m10b_p2pu_v3_eng.py::rediscover_v3`).
  - It runs `pytest --collect-only` at **target** under the V3 environment over the associated files.
  - Only `.py` files are used; `conftest.py`, `__init__.py` and bracketed paths are excluded.
  - The authority for rediscovery is the V3 rediscovery amendment, not the v2 rule text, which says "no rediscovery".
- **Selection:** the frozen P2P-U v2 rule (`wp2_p2p_u_v2_rule_freeze_2026-09-25.json`, `rule_sha256 78a089bb…`, salt `wp2-p2p-u-v2-2026-09-25`):
  - proximity = longest common leading component count after `saleor/`;
  - PROXIMAL ≥ 2 / DISTAL ≤ 1;
  - sha256(salt | path) ordering, round-robin, P,P,P,D interleave;
  - **cap 200** with target composition 150/50 and deterministic backfill.
  - The cap400 sensitivity arm was ENG-only and is **not** run.
- **Execution:** 3 repetitions at parent + frozen test patch and 3 at target, workers = 1, no early stopping.
- **Taxonomy precedence:** FLAKY > COLLECTION_ERROR > STABLE_P2P > TARGET_BROKEN > PARENT_BROKEN > BOTH_FAIL.
- **Only STABLE_P2P nodes** form `p2p_u_cap200_stable_ids`. If there are 0 nodes, `p2p_u200_task` is UNDEFINED (passish).
- **Infra:** 3 attempts, then the task is `NOT_READY_EVALUATOR_SET_INFRA_UNRESOLVED`. It stays in the frozen eligibility set, is excluded from readiness, and is listed.

**Freeze.** The per-task evaluator sets go into `m16_main_evaluator_sets_v3.json` (self-hashed). It is loaded only through an evaluator-only loader with the same caller guard as `benchmark/wp2/e2e/evaluator_sets.py`. It is committed and tagged `wp2-m16-v1-evalsets-*`, then pushed, **before** readiness.

### 5.4 OPWS_ROBUST and OPWS_STRICT (per READY task × selector; only after §7 step Q08)

**Editable sets** use the frozen scope builder `benchmark/wp2/e2e/scopes.py` semantics. A MAIN adapter supplies only the inputs:
- commits come from the MAIN census;
- RMCSS raw = `rmcss_predicted_set`;
- AGENT_MAIN raw = WP1b main-run `selected_paths`;
- AGENT_r1..r3 raw = variance `selected_paths`.

The filter for every arm is the frozen D35 filter:
- the file exists at parent (`git show`);
- it is non-test (V2 regex);
- it is ≤ 120,000 decoded characters;
- files are then added greedily in alphabetical order, skipping any file that would push the cumulative total over 300,000.

The output is `editable_S`.

**Gold.**
- **G_raw** = `gold_raw_scope(t)`: name-status `M` or `D` non-test paths.
  - Renamed (`R<score>`), added, type-changed and copied paths are excluded. The code's `'R'` branch never matches git's `R<score>` output.
  - This matches Smoke, Pilot-A, M14R and M15-R.
- **G_edit** = GOLD_HARD `editable`, i.e. D35 applied to G_raw.

**Restricted patch.** P_S = the gold non-test diff restricted to (editable_S ∩ G_raw), produced by `scoped_gold_diff` (identity semantics `core_diff_sha`).

**Coverage class** (operational; it determines the evaluation route):

| Class | Definition | Route |
|---|---|---|
| NONE | editable_S ∩ G_raw = ∅ (includes an empty selection) | Y = 0, no evaluation |
| FULL | the core identity of P_S equals the readiness scoped-gold identity | Y = readiness positive (= 1), reuse |
| PARTIAL | otherwise (this also covers a P_S that contains gold files GOLD's own budget dropped from G_edit, i.e. not only subsets of the scoped gold) | evaluated |

**Evaluation of PARTIAL items.**
- `materialize(t, id, P_S)`, then `evaluate_state_e1` (3 repetitions, fresh DB, workers = 1) with E1 + E1A1 startup semantics.
- Items with identical P_S identity on the same task are evaluated once and shared.

**Scoring** (`scripts/wp2_m14r_core.py`, sha256 `2e19975d…`, unchanged):
- **`OPWS_STRICT`** = `score_strict(...).resolved`:
  - every behavioral F2P node (V3 set) passed in all 3 repetitions; **and**
  - every P2P-S node passed 3/3 (or the set is empty → UNDEFINED); **and**
  - every P2P-U200 node passed 3/3 (or empty → UNDEFINED).
- **`OPWS_ROBUST`** = `score_robust(...).resolved`:
  - F2P exactly as in strict; **and**
  - no P2P-S node and no P2P-U200 node is non-passing (failed/error/skipped/missing) in ≥ 2 of 3 repetitions, or has fewer than 2 recorded outcomes (`len(o) < 2`; unreachable with the frozen evaluator);
  - an empty set → UNDEFINED, which is passish.

**GOLD invariant.** `OPWS_ROBUST(GOLD, t) = 1` on every READY task. This holds by construction via reuse; any mismatch is an instrument STOP.

**File-level metrics** (reported, not used for scoring): P/R/F1 of editable_S against G_raw.

### 5.5 Infra, flaky, unresolvable and listwise rules (OPWS stage)

| Situation | Rule |
|---|---|
| Evaluation infrastructure error (`INFRA_EXC`, `OSError`, `EXIT_EVAL_INFRA` (exit 79), Docker/WSL down) | Resumable STOP; the same identity is retried on resume; **never scored**. |
| Same identity fails on infra 3 times in total | The identity is `INFRA_UNRESOLVED`; its **task is dropped listwise** from every paired and per-selector analysis (RMCSS, AGENT_MAIN, r1–r3, GOLD) and listed with the error class. |
| Listwise drops > 10% of n_READY | `run_status = M16_INSTRUMENT_REVIEW`; Fields 2–3 `NOT_ISSUED`. |
| Bounds for drops | Always report δ bounds with dropped tasks imputed adversarially both ways: RMCSS = 0/AGENT = 1, and RMCSS = 1/AGENT = 0. |
| `INFRA_UNCLASSIFIED` startup failure not covered by E1 or E1A1 (`M15R_E1A1_GRAPHQL_DUPLICATE_TYPE_STARTUP_V1`) | STOP for amendment, subject to all of: (i) it can only map INFRA → a FAIL class, never to PASS; (ii) it is selector-agnostic, written from the failure text alone and applied to all items; (iii) it is committed, tagged and pushed before resuming; (iv) amended items are listed, and a sensitivity analysis excludes them. If amended items exceed 10% of evaluated items → `M16_INSTRUMENT_REVIEW`. |
| F2P intermittent under P_S | Robust = 0 under the frozen rule (F2P requires 3/3). No reruns. |
| Flaky nodes | Unless R1 is amended, changed-test node instability is **not** detected at oracle construction (§5.1). It surfaces only at evaluation, under the robust/strict rules. After the evaluator-set freeze no node is ever removed. |
| Empty selection | NONE → Y = 0 (selector outcome, not an exclusion). |

**Stopping rules.**
- **No outcome-based interim looks.** The controller prints only item counts until Q11.
- **Instrument STOPs:** frozen-hash drift; GOLD reuse identity mismatch; protected-pool access; quarantine amendment missing or not pushed; evaluator-set or READY tag not on origin.
- **No early termination for efficacy or futility.** The census always completes unless a STOP is terminal.

---

## 6. Route-B phase, time and storage plan

### 6.1 Time

Basis:
- C4-V3: median 4.3 min/task (ENG n = 29, including 7 install-blocked; the DONE-only median is 5.2; max 12.4; ENG ran 2 tasks in parallel, so the sequential M16 rate may be higher).
- P2P-U200: median 6.4 min (ENG n = 16, max 10.6).
- Rediscovery: 0.8 min.
- Frozen evaluation: about 5 min (M15-R); readiness = 2 evaluations.
- The planning envelope uses `later_work_estimates_v3.json` (C4 3/5/8 min; P2P-U 10/13/20 min).

Projections assume n_elig = 70–125 V3-eligible tasks (unknown; ENG flipped 8 → 14) and n_READY = 60–110. OPWS items ≈ 2·n_READY·0.55 PARTIAL share + ≤ 13·3·0.55 replicate items, minus dedup ≈ 70–140 evaluations.

| Phase | Work | Central (measured) | Envelope |
|---|---|---|---|
| Q03 | C4-V3 oracle on 220 | 220 × 4.3 min ≈ **15.8 h** | 11–29 h |
| Q05 | Rediscovery + P2P-U200 on n_elig | n_elig × 7.2 min ≈ **8.4–15.0 h** | 15–27 h at 13 min |
| Q06 | Readiness on n_elig (2 evaluations) | n_elig × 10 min ≈ **11.7–20.8 h** | up to ~31 h (125 × 15 min) |
| Q09 | OPWS PARTIAL evaluations | 70–140 × 5 min ≈ **5.8–11.7 h** | up to ~18 h (140 × 7.7 min) |
| | **Total Docker** | **≈ 42–63 h** | ≈ 44–105 h |

Wall-clock: Docker runs sequentially in controller chunks (yield/resume). With about 16 h/day of machine availability, that is about 3–4 days central and up to about 7 days in the envelope. Zero model API, so $0.

### 6.2 Storage — corrected basis and the role of `D:\wp2_cold`

**Where V3 actually consumes space.**

| Item | Location | Persisted? | Expected growth in M16 |
|---|---|---|---|
| Per-task Python environments | inside `docker run --rm` containers (`/opt/venv`) | **no**: destroyed after each state | 0 (transient only) |
| uv wheel cache `wp2-uv-cache` (21 GB, PROTECTED_EVIDENCE) | Docker volume in Ubuntu-24.04 `ext4.vhdx` on **C:** | yes | new wheels for MAIN lock sets not seen on DEV/ENG; **unknown, estimated 2–10 GB**; measured in the kit dry-run |
| Worktrees (`/opt/wp2_v2/worktrees/<tid>_v3_{t,p}`) | WSL vhdx on C: | removed per task | ≤ 1 GB transient |
| Postgres DBs | `wp2-pg` | dropped per state | ~0 |
| Evidence (JUnit, records, plans) | project tree on C: | yes | ≈ 0.5–2 GB. Basis: the V2 `junit` dir is 244 MiB but DEV-only (86 tasks, 0 MAIN); the ENG V3 dir is 161 MiB, of which about 78 MiB is env-closure/superseded material; C4-V3 persists no raw JUnit. |

**Problem.** The WSL vhdx grows on C: and does not shrink by itself. The existing C4-V3 runner stops below 32 GiB free on C:, and C: has about 33.3 GiB free now. Projected end state without action: about 21–30 GiB free.

**`D:\wp2_cold` plan (as requested, on the corrected basis).**

1. **V3 environments.** V3 has no persistent per-task environment to place on D:. The only persistent runtime store (uv cache plus Docker data) lives in the WSL vhdx. Moving that vhdx to D: is technically possible (`wsl --manage <distro> --move`, available in WSL ≥ 2.3). **We do not recommend it:** D: is the HDD (storage audit), and every lock-exact install, postgres write and pytest run would go through it. That contradicts the standing "no speed loss" constraint. The decision is the reviewer's (S1 below).
2. **D:\wp2_cold is used for:**
   - (a) the **cold mirror** of each phase's frozen evidence after its tag is pushed (copy, verify, hash; ≈ 0.5–2 GB total);
   - (b) LIGHT backups, with hashes compared on both drives as done for M15-R;
   - (c) **pre-run headroom (S2):** relocating Windows-side rebuildable caches from the storage audit (`_workspace/cache` 2.06 GiB, `dist/locagent-venv` 1.25 GiB, `.uv-task-cache` 1.69 GiB, superseded parent zips 1.16 GiB; ≈ 6.2 GiB). This happens only after a guard verifies that none of them is on any V3/M16 code path. `.venv`, `pgdata`, `worktrees`, `dist/pilot-repo-cache` and `wp2-uv-cache` are **not** moved.
3. **M16 resource thresholds** (infrastructure parameters, pre-declared, never tuned on outcomes). M16 calls the V3 library functions from its own engine, not the old phase scripts' `main`, so these are M16's own thresholds:
   - WARN at C: free < 25 GiB;
   - **HOLD (resumable, exit 3) at C: free < 20 GiB** (the M15-R doctor threshold);
   - HOLD when WSL MemAvailable < 2 GiB;
   - HOLD when `D:\wp2_cold` is unreachable during a mirror step.
4. **Dry-run measurement** (part of the later kit stage, not now): 3 tasks, one per era, measure vhdx growth per task. If projected free space at Q09 end is < 25 GiB, the human runs maintenance window S3 before Q03 (never during a phase).

### 6.3 Docker load

Exactly one era container at a time, plus `wp2-pg` and redis. workers = 1, no parallelism, and no other controller (AG16 or any other) runs concurrently.

---

## 7. Controller phases (proposal) and the proof that scope materialization follows the pushed READY freeze

### 7.1 Phases (all zero model API)

| Phase | Content | Docker | Gate to next phase |
|---|---|---|---|
| Q00 | Kit self-tests | no | PASS |
| Q01 | Guard: frozen hashes; quarantine amendment present and on origin; protected pools; **absence check** (no `m16_v1/scopes/`, `opws/` or any file derived from selector inputs); resource thresholds | no | HOLD/STOP |
| Q02 | MAIN adapter identity regression: reproduce stored ENG/Pilot-B scope and identity records through the adapter with ENG inputs; must be byte-identical | no | STOP on mismatch |
| Q03 | C4-V3 oracle construction on the 220 (§5.1) | yes | resumable |
| Q04 | Eligibility freeze → commit, tag `wp2-m16-v1-eligibility-*`, push | no | pushed |
| Q05 | P2P-S extraction + P2P-U200 rediscovery and execution (§5.3) → evaluator-set freeze, tag `…-evalsets-*`, push | yes | pushed |
| Q06 | Readiness (§5.2) | yes | resumable |
| Q07 | READY membership freeze + pool gate → commit, tag `wp2-m16-v1-ready-*`, push | no | **pushed (P1–P4 below)** |
| Q08 | **Scope materialization**: editable sets for RMCSS, AGENT_MAIN and r1–r3 (overlap); P_S; coverage routes; OPWS plan → commit, tag `…-scopes-*`, push | no | pushed |
| Q09 | OPWS evaluation of PARTIAL items (`--max-items` chunks) | yes | resumable |
| Q10 | Completeness (every planned identity has a valid record or is listed `INFRA_UNRESOLVED`) | no | STOP |
| Q11 | Analysis: estimands, CIs, tests, tables, three-field token, claim text | no | — |
| Q12 | Summary + result tag (exact refspec) + LIGHT + `D:\wp2_cold` mirror | no | — |

### 7.2 Proposition

*No M16 selector-derived quantity (editable_S, P_S, coverage class, OPWS record) is created, or can influence READY membership, before the READY membership is committed, tagged and present on origin.*

WP1 per-task metrics and the census scope flags already exist. Checks V3 and V4 neutralise any use of them.

### 7.3 Enforcement mechanisms (built into the kit)

- **P1 — Pushed-tag precondition in code.** `scope_materialize()` begins with `ready_pushed()`, which requires all of the following. Any failure raises STOP, with no override flag.
  - a local tag `wp2-m16-v1-ready-*` exists;
  - `git_gate.remote_tag_objects(PROJECT, tag)["object"]` equals the local tag object (`verify_tag_on_origin(PROJECT, tag)`);
  - `git_gate.verify_file_in_tag(PROJECT, tag, path)` matches the working-tree READY membership file byte-for-byte (LF-hash);
  - the tag's commit is an ancestor of HEAD (`git merge-base --is-ancestor`);
  - **exactly one** tag matches `wp2-m16-v1-ready-*`, both locally and on origin (more than one → STOP);
  - the eligibility tag commit and the evalsets tag commit are both ancestors of the READY commit.
- **P2 — Binding.** The scope plan records `ready_tag`, `ready_tag_object`, `ready_commit`, `ready_membership_sha256` and the `git ls-remote` result observed at Q08. Q09 refuses to run unless these equal the pushed tag values (re-checked against origin at Q09 start).
- **P3 — Selector-input firewall during the selector-blind phases.**
  - Q03–Q07 run in processes that install a Python audit hook (`sys.addaudithook`, event `"open"`). The hook raises STOP if any of these paths is opened:
    - `research/wp1a/sip_rmcss_per_task_predictions.json`;
    - `research/wp1b/main-297-2026-09-22/*`;
    - `research/wp1b/variance-15x3-2026-09-22/*`;
    - `research/stage5-v2-final/deployment_artifact.json`;
    - `research/wp2/wp2_main_census_metadata_v2_2026-09-23.json` (it holds per-task selector empty-scope/size flags);
    - `exports/WP1A_WP1B_SCIENTIFIC_CLOSURE_2026-09-21/research__wp1a__sip_rmcss_per_task_predictions.json`;
    - all zip/LIGHT exports;
    - the `D:\wp2_cold` mirror.
  - **Subprocess reads.** The hook also inspects the `subprocess.Popen`, `os.system`, `os.exec*` and `os.posix_spawn` audit events and rejects any argv that contains a blocked path. Paths are normalised (fspath, abspath, normcase, resolve). Child Python processes install the same hook.
  - **Scope builder.** Q06 uses a **GOLD_HARD-only** scope adapter. `build_arm_scopes` and its selector branches are not imported in Q03–Q07, because importing it loads selector predictions at import time. A static unit test asserts this.
  - **Limit.** Software can only block reads made from this machine's processes; this is stated in §7.5.
- **P4 — Absence checks.** Q01 and the start of each of Q03–Q07 assert that the directories `research/wp2/m16_v1/scopes/` and `research/wp2/m16_v1/opws/` do not exist. Q08 is the only code that creates them.

### 7.4 Independent verification after the run (no trust in the controller needed)

- **V1 — Ancestry.** Both of the following must hold:
  - `git log --format=%H <ready_commit> -- research/wp2/m16_v1/scopes research/wp2/m16_v1/opws` is **empty**, i.e. nothing reachable from the READY commit touches those paths;
  - `git merge-base --is-ancestor <ready_commit> <c>` succeeds for **every** commit c that touches those paths.

  Commit hashes chain cryptographically, so the scope and OPWS files entered history only after the READY freeze.
- **V2 — Origin state.** The READY tag exists on origin and points at `ready_commit`; the scope tag points at a descendant of it.
  - Git cannot attest push *time*. That the READY tag was on origin before Q08 is enforced at runtime by P1, and evidenced by the `ls-remote` result recorded in the scope plan (P2).
- **V3 — Recomputability.** A verifier runs `decide_ready(record)` on every stored readiness record. The resulting set must equal `m16_ready_membership.json` exactly. This shows that membership has no human discretion and no selector input, because `decide_ready` reads only readiness evidence.
  - Every readiness attempt, including infra retries, is logged **append-only** and committed with the READY freeze. Selective re-runs would therefore be visible.
- **V4 — Eligibility recomputability.** The same check for `m16_v3_eligibility.json`, from stored node records via `classify_node_v2` and `task_eligibility_v2`.

### 7.5 Residual risk (stated honestly)

Software cannot rule out that a human computed selector overlaps out-of-band before Q07. V3 and V4 neutralise the *consequence* of such a computation: membership is a deterministic function of selector-blind evidence, so it could not have been steered without altering evidence. Altered evidence would break the evidence hashes that are frozen and pushed at each tag.

---

## 8. Agent replicates (unchanged in substance)

- **Primary arm:** AGENT_MAIN, the WP1b main run (replicate 0). This is the selection behind the WP1 claim.
- **Replicate-overlap subset:** the variance tasks (15) ∩ T*. The V2 overlap was 7. Under Route B it can be up to 13: 6 variance tasks are in the 220 but were not V2-eligible, and 2 are outside the 220.
- On the overlap subset only, report descriptively (E-D2):
  - OPWS for each of r1, r2 and r3 separately;
  - outcome-majority (≥ 2 of 3 pass; M15-R definition);
  - mean sufficiency over r1–r3;
  - all-3 agreement count;
  - mean pairwise Jaccard of editable sets.
- The main run is **not** pooled with r1–r3. The WP1b prereg states that the main run is not replicate 1.
- Scope-consensus selections (files chosen by ≥ 2/3 replicates) are **not** created, because they would be a new selector.
- Fresh replicates (an optional later paid M16b) are out of scope.

---

## 9. Feasibility audit (from v1, verified; corrected numbers)

**Available**
- RM-CSS: 297/297 tasks (29 empty).
- Agent main run: 297/297 (2 empty, `parser_failure`).
- Variance r1–r3: 15 tasks, all within the first 50 of MAIN.

**V2 evidence — context only, not the M16 frame**
- 220 attempted:
  - 60 environment install failed. The phase-1b audit labels all 60 `LOCKFILE_INCOMPATIBILITY` with `v3_repair_plausible = true`. This is a projection, and 27 of the 60 also cite weasyprint/pango.
  - 160 executable:
    - 71 primary-behavioral (5 of them also carry symbol-absence nodes);
    - 12 symbol-absence-only;
    - 77 with no F2P.

**ENG precedent, V2 → V3**
- 8 → 14 primary: 7 kept, 1 install-blocked, 7 newly eligible.
- 7/29 install-blocked under V3.

**Selector-blind V2 profile of the 71 (context for threats)**

| Property | Eligible 71 | Complement 226 |
|---|---|---|
| Mean GOLD_HARD size | 3.04 | 3.93 |
| Tasks with added non-test files | 4/71 | 32/226 |
| Tasks with migration files | 4/71 | 33/226 |

- Year yield: 2020–2021 2/63; 2022 19/26; 2023 19/34; 2024 3/32; 2025 11/43; 2026 17/22.
- RM-CSS empty on 4/71; Agent empty on 0/71.

**Evaluable:** unknown until Q06. Projection 60–110 READY. **Sampled:** the full READY census.

---

## 10. Threats to validity (condensed; changes from v1 in bold)

1. **Selection and survivorship.** The eligibility filters are selector-blind, so the *paired* comparison is internally valid on T*. Level estimates θ_S are likely optimistic for MAIN overall: the V2 survivors had smaller gold, fewer added files and fewer migrations. **Route B removes the V2 instrument defect from the frame; it does not remove structural filters** (changed tests, installability, behavioral F2P, GOLD_HARD scoped-gold pass). Reported:
   - representativeness (E-D1, era/year/gold-size distributions of T* vs the 220 vs 297);
   - descriptive per-stratum δ̂;
   - a strata-reweighted θ_S (era × gold-size tercile) as sensitivity.
2. **GOLD_HARD excludes added and renamed files.** Tasks needing them drop out at readiness, selector-blind. An "added-file allowance" variant is an optional descriptive sensitivity (open question O3).
3. **Single Agent run.** The δ CI omits Agent run-to-run variance. The overlap subset (7–13 tasks) bounds it only descriptively.
4. **Construct.** OPWS credits only the developer's patch, which is a lower bound on whether any passing patch exists in scope. It does not penalize over-selection. It says nothing about generator success (M15-R: 436f).
5. **Instrument.** Every phase uses V3, and every node set is frozen before readiness. The E1/E1A1 startup semantics are frozen, and the amendment rule is restricted to INFRA → FAIL.
6. **Quarantine.** Handled by the amendment (§1) and the ordering proof (§7).
7. **Multiplicity.** There is one primary estimand and a single supporting test; everything else is estimation or descriptive.
8. **Storage and infra.** Handled by the HOLD thresholds and listwise rules with adversarial bounds (§5.5, §6.2).

---

## 11. Frozen inputs to pin at freeze

All v1 §13 hashes stand (24/24 independently verified). Added in v2:

| Path | sha256 (brain snapshot) |
|---|---|
| research/wp2/oracle_confirmation_linux_v2_2026-09-23/wp2_unchanged_p2p_candidate_inventory_v1_final_2026-09-25.json | 87d20d5e3eb6caab9c3e6ca9a08335e57070c41d1493ce3d4e8bd3dbb8a352ca |
| scripts/wp2_m14r_core.py | 2e19975df631f0a9f6e0888e800480819ca2bb5fe5244722fd19b617b2920491 |
| scripts/wp2_m15r_run.py (readiness_task, opws_paths source) | 51f961c2dc27681031530dde5c4cbd2ff73e014ca569e35633aa9176d0a3b7d7 |
| scripts/wp2_m10b_p2pu_v3_eng.py (rediscover_v3 source) | 72e153d5687ffe4914ecd39fa70c0515d0a038c48949331a81250d598d5270c4 |
| research/wp2/harness_v3_2026-09-26/later_work_estimates_v3.json | a7d94facaacc4e22f9d61b8029216502ccf56ea99f92f9eb67a2dd60f945ee22 |
| POST_RUN_STORAGE_AUDIT.json | 7dcde1e90d448662b9f6f1268608f48bd19c0b3c7fb8d3d45543807fafbd457c |
| `src/benchmark/wp2/{harness_v3.py, oracle_semantics_v2.py, e2e/scopes.py, e2e/evaluate.py, e2e/spec.py}` | computed by the installer on the real repository (not present in the brain snapshot) |
| research/wp2/m16_v1/m16_l_opws_quarantine_amendment.json | computed when written (§1) |

---

## 12. Open items for the reviewer before freeze

**Blocking:**
- **R1 — Repetition collapse in C4-V3 oracle construction (§0 C5, §5.1).** The options are:
  - **(a)** Accept the frozen path as is (comparable with ENG/M15-R oracle construction), and disclose that changed-test node stability is checked on the final repetition only.
  - **(b)** Amend oracle construction to retain per-repetition outcomes before Q03, applied identically to all 220 tasks. This restores the declared `3_plus_3_stability_policy`; `classify_node_v2` already expects 3 outcomes. It changes no classification rule, but some nodes will move into FLAKY, so the M16 sets are not byte-comparable with ENG sets. Comparability is not needed, because M16 is never pooled with ENG.
  - **Brain recommendation: (b)**, with the amendment frozen, tagged and pushed before Q03, and the ENG limitation disclosed in the thesis.
- **R2 — MAIN adapter for census, era and dev/test closure (§0 C6, §5 intro).** Accept the rule: the same `derive_dev_test_closure` on MAIN target manifests; era from `per_task_v2.jsonl`; and Q02 asserts both that ENG outputs are identical and that MAIN closure ≠ `none` wherever a dev group is declared. Without R2, Route B does not achieve its purpose.
- **S1 — Storage.** This **deviates from the literal request** to put V3 environments on `D:\wp2_cold`, because V3 has no persistent per-task environment; its only persistent runtime store is the WSL vhdx. Accept the recommended setup:
  - keep the WSL vhdx on C: (SSD);
  - use `D:\wp2_cold` for the evidence mirror, LIGHT backups and the S2 cache relocation;
  - use the M16 HOLD at 20 GiB.

  The alternative is moving the whole distro with `wsl --manage <distro> --move` (WSL ≥ 2.3), at the cost of HDD speed on every install and test run.
- **S3 — Conditional maintenance window.** If the dry-run projects < 25 GiB free at the end of Q09, a pre-Q03 maintenance window is allowed. It would remove anonymous Docker volumes that the 2026-09-28 audit classifies as REBUILDABLE_CACHE, never `wp2-uv-cache` or `wp2-pg`, and compact the vhdx.
  - Realistic size: **≈ 14 GB** = 35.31 GB total volumes − 21 GB `wp2-uv-cache`. The audit's "34.06 GB reclaimable" counts the unreferenced uv cache and must not be acted on. The reviewer previously asked for no prune or compaction in the current state. This only asks for permission conditional on the measurement.

**Non-blocking (defaults shown):**
- **O1 — Pool gate:** n_READY ≥ 40.
- **O2 — Listwise-drop threshold:** 10%. Amended-item threshold: 10%.
- **O3 — Added-file allowance sensitivity:** include, descriptive only.
- **O4 — Supporting test:** exact McNemar as primary supporting, mid-p co-reported. Fagerland 2013/2014 recommend mid-p or asymptotic over exact; exact is kept as the conservative choice.

**Go / no-go: CONDITIONAL GO.**
1. The reviewer approves v2 and settles R1, R2, S1 and S3.
2. The brain then writes the design-freeze JSON, the amendment artifact and the kit (installer, plan, tests, dry-run simulation) for independent review.
3. Only after that does the human run the 3-task resource dry-run and then Route B.

Nothing is built until v2 is approved.

---

## References (statistical methods; verified to exist)

- McNemar, Q. (1947). Note on the sampling error of the difference between correlated proportions or percentages. *Psychometrika* 12(2):153–157.
- Clopper, C. J., & Pearson, E. S. (1934). The use of confidence or fiducial limits illustrated in the case of the binomial. *Biometrika* 26(4):404–413.
- Tango, T. (1998). Equivalence test and confidence interval for the difference in proportions for the paired-sample design. *Statistics in Medicine* 17(8):891–908.
- Newcombe, R. G. (1998). Improved confidence intervals for the difference between binomial proportions based on paired data. *Statistics in Medicine* 17(22):2635–2650.
- Fagerland, M. W., Lydersen, S., & Laake, P. (2013). The McNemar test for binary matched-pairs data: mid-p and asymptotic are better than exact conditional. *BMC Medical Research Methodology* 13:91.
- Fagerland, M. W., Lydersen, S., & Laake, P. (2014). Recommended tests and confidence intervals for paired binomial proportions. *Statistics in Medicine* 33(16):2850–2875.
