# OPWS Protocol R1 — Frozen Semantic Contract (M17_OPWS_PROTOCOL_FREEZE_R1)

**Freeze date:** 2026-10-12
**Branch:** `parallel/opws-protocol-r1-2026-10-12`
**Mission start HEAD:** `83399ff875c7793286d66311afb6c62071ea04b3`
**Status:** FROZEN BEFORE Full-D7 population binding and BEFORE any OPWS execution.

This document is the authoritative human-readable statement of the Oracle Patch
Within Scope (OPWS) evaluation protocol for RQ3. The machine-readable twin is
`OPWS_PROTOCOL_R1.json`. In a disagreement the `.json` contract governs for
machine validation; this `.md` governs for reading. They must describe the same
contract; the validator enforces that the `.json` exists and is self-consistent.

---

## 0. Scientific authority

- main.pdf is **HISTORICAL ONLY**. It does not override any newer frozen
  repository scientific authority. No OPWS R1 semantic in this document is
  derived from main.pdf. (Owner correction #1.)
- Operative authorities (frozen, in this worktree or the listed read-only
  authorities):
  - `research/wp2/m17_v1/m17_design_freeze_v1.json` (M17 OPWS-MAIN design freeze)
  - `controller/plan_m17_v1_main.json` (M17 execution order)
  - `research/wp2/m15r_v1/m15r_design_freeze_v1.json` (Pilot-B OPWS design freeze)
  - `scripts/wp2_m15r_run.py`, `scripts/wp2_m14r_run.py`,
    `scripts/wp2_m14a_evalcore.py`, `scripts/wp2_m14a_evalcore_e1.py`,
    `scripts/wp2_m14a_readiness.py` (frozen instrument implementations)
  - `scripts/wp2_m17_contract.py` (F2P/P2P terminal vocabulary)
  - `docs/WP2_RESHAPE_INDEPENDENT_REVIEW_2026-10-01.md` (OPWS rationale and limits)
  - `D:/wp2_comp_baselines/research/competitor-baselines-r2/BASELINE_PROTOCOL_FREEZE_R2.json`
    (frozen universe/gold/normalization semantics)
  - `D:/wp2_agentless_main297/research/competitor-agentless-r1/AGENTLESS_STYLE_ADAPTATION_PROTOCOL_FREEZE.json`
    (Agentless label boundary)

## 1. Scientific definition

OPWS = **Oracle Patch Within Scope**.

For one frozen task and one frozen selector scope:

1. **Clean start state:** materialize the frozen task's **parent commit** state
   (the exact historical *pre-change* repository state) inside Linux from git
   objects (owner correction #7: Windows/NTFS-materialized trees are invalid for
   OPWS execution). The mission statement's phrase "exact historical target
   repository state" is interpreted here with the frozen precedent exactly
   (`scoped_gold_diff` = `git diff <parent> <target> -- <selected files>`,
   applied onto the parent worktree): the *post-change* reference content is
   defined by the frozen **target-commit git objects**, and the OPWS worktree is
   the parent state **plus only** the reference patch content restricted to the
   selected scope. This is the only reading under which scope sufficiency is a
   well-posed question, and it matches the frozen M15-R/M14-R instrument.
2. **Reference non-test patch:** the known developer/ground-truth change set
   restricted to **non-test files** (the observed changed file set from the
   frozen gold proxies, evaluation-only).
3. **Scope restriction:** apply **only** reference patch content for files
   permitted by the selector's selected scope. Reference-changed files outside
   the selected scope are left **unmodified** (remain at the parent state).
4. **Behavior contract:** run the frozen task behavior contract (frozen F2P node
   set via the frozen evaluator + E1). See §4.
5. **Preservation contract:** run the frozen preservation contract (frozen
   P2P-S/P2P-U STABLE identities, selector-blind). See §5.
6. **Classify** the joint result via the frozen outcome taxonomy (§9).

OPWS **intentionally removes code-generation quality as a variable.** It asks:

> Assuming a perfect generator that could reproduce the known reference change
> for files selected by this scope, is the selected scope behaviorally
> sufficient under the frozen test contract?

## 2. Interpretation boundary (non-negotiables)

An **OPWS PASS** means:

- the selected scope was sufficient for the observed frozen behavior +
  preservation contract when the known reference patch was used inside that
  scope (perfect-generator assumption).

An **OPWS PASS does NOT mean**:

- LLM-generated code would be correct;
- arbitrary future edits would succeed;
- the selector identified every historically changed file;
- the selector is a complete causal oracle;
- production correctness is proven;
- functional correctness of generated code has been demonstrated (never use the
  phrase "generated-code correctness" for OPWS).

Required wording when summarizing OPWS results: **"behavioral sufficiency under
the reference-patch / perfect-generator assumption."**

## 3. Reference-patch file-status semantics (MODIFIED / ADDED / DELETED / RENAMED)

Frozen **before** any outcomes (owner correction #2).

Status is read from `git diff --name-status <parent> <target>` for the frozen
task's changed non-test file set.

| Status | Selectable by parent-commit selector? | Reference patch semantics (PRIMARY treatment) |
|---|---|---|
| MODIFIED (M) | YES — file exists at parent | `git diff <parent> <target> -- <path>` hunk applied onto parent file |
| DELETED (D) | YES — file exists at parent | deletion hunk applied; file absent after OPWS patch |
| RENAMED (R) | OLD path: YES (exists at parent); NEW path: NO (not present at parent) | treating the pair per `git diff --name-status`: old-path deletion + new-path addition; if only the old path is selected, apply the deletion side; if only the new path is selected (reference-derived arms only), apply the addition side |
| ADDED (A) | NO — file does not exist at parent | reference-derived arms only (GOLD / SELECT_ALL) may include it: full-file creation from the target-commit git blob |

**Rule:** a parent-commit-selector scope can never contain a newly ADDED file:
the file is absent from the parent-visible selectable universe. If a frozen
prediction artifact ever lists a path that does not exist at the parent commit,
that path is **not silently dropped**; it is counted
(`invalid_prediction_path_count`) and the path is excluded from the OPWS patch
with the reason recorded per task/arm. (Prediction artifacts are already
normalized onto the parent-visible universe by their producers; this rule is a
fail-closed guard.)

**Sensitivity analysis (pre-registered):** besides the PRIMARY treatment above,
compute the same per-task/arm OPWS result under a **secondary treatment** in
which reference ADDED and RENAMED-new-path files are **excluded from every
scope** (so no arm differs merely by ability to express newly added files), and
report both the primary and this sensitivity reconstruction. If the two
treatments disagree on any arm-level conclusion, that is reported as a
sensitivity-limit note, not hidden.

**Reference test-file changes:** test-file changes are **not** part of any
selector's editable scope (the selectable universe is production `.py` only).
All reference **test-file** changes belong to the **common behavior contract**
and are applied **identically across every arm** for a given task; an arm's
OPWS result difference can never come from a test-side difference. (Owner
correction #2.)

## 4. Frozen behavior contract (per task)

- **F2P node set:** the frozen failing-to-passing node set
  (`BEHAVIORAL_F2P` and `SYMBOL_ABSENCE_F2P` classes) established by the frozen
  evaluator artifacts, bounded by the frozen per-task count. Selector-blind.
- **Execution:** run the frozen evaluator (same command, environment, and
  per-node status recording used by the frozen Full-D7 readiness instrument) on
  the OPWS-patched worktree. An F2P node whose status is not `passed` blocks
  behavior resolution (fail-closed).
- **behavior_sufficient = 1** iff every required frozen F2P node is present and
  passes (strict semantics), per frozen `task_resolvable` / `terminal_classify`
  rules.

## 5. Frozen preservation contract (per task)

- **P2P-S:** frozen SWE-bench-aligned changed-test PASS_TO_PASS identities.
- **P2P-U:** frozen unchanged-test STABLE_P2P identities (outcome-blind
  cap-200 selection, STABLE over 3 reps).
- Either source may define a task's preservation set (existing M17 rule:
  `p2p_s_defined OR p2p_u_cap200_defined`; P2P-S frozen identities are
  combined with P2P-U identities and both are evaluated on the OPWS worktree).
- **preservation_pass = 1** iff every frozen stable-pass preservation identity
  still passes on the OPWS worktree. A P2P node failure is never silently
  reclassified as infrastructure success; infra-masked regressions are recorded
  (frozen `p2p_failure_reclassified`).

## 6. Per-task metrics

- `behavior_sufficient` ∈ {0,1}
- `preservation_pass` ∈ {0,1}
- `opws_joint_pass = behavior_sufficient AND preservation_pass`
- `scope_size_files` = |canonical normalized selected file list|
- `historical_recall` = |scope ∩ gold non-test files| / |gold non-test files|
- `recall_gap` (owner correction #5): `historical_recall < 1 AND opws_joint_pass`
  is a predeclared, reportable state. Interpretation is **limited** to:
  "some historically changed non-test file was not needed for the frozen
  observed behavior + preservation contract under the perfect-generator
  assumption." It is **not** evidence that the selector is complete, and it is
  not a failure.
- optional execution diagnostics: `wall_time_seconds`, `patch_apply_seconds`,
  `test_seconds`. None is treated as LLM token efficiency.

## 7. Taxonomy note

Full taxonomy is in P6 (`OPWS_OUTCOME_TAXONOMY_R1.json`). Infrastructure
failures are never converted into behavioral insufficiency; failures are never
silently discarded; uncertain states fail closed to `UNKNOWN_FAIL_CLOSED`.

## 8. Statistical/claiming guardrails (summary)

- Primary inference is **paired effect estimates + 95% CI** (paired task
  bootstrap, `N_BOOTSTRAP = 10000`, `BOOTSTRAP_SEED = 20261012`).
- **No non-inferiority or equivalence margin is chosen in this freeze.** A
  margin will not be introduced later to compensate for small n or for any
  post-outcome reason. If a future amendment re-introduces an NI margin, it
  must carry an independent pre-outcome justification recorded in DECISIONS.md
  (owner correction #4).
- The **sufficiency–scope frontier** is the primary scientific object for RQ3,
  not a single "best arm" headline.
- Suite scope: RQ3 core protocol. RQ6 perturbation is **design-only** and
  deferred to a separate future amendment; it is **not executed** in this
  mission and does not gate RQ3 (owner correction #6).

## 9. Execution vs binding boundary

- This freeze binds **nothing** about the Full-D7 READY population.
- `FULL_D7_READY_POPULATION_HASH = UNBOUND_PENDING_FULL_D7`
- `FULL_D7_READY_TASK_COUNT = UNBOUND_PENDING_FULL_D7`
- `OPWS_BOUND_POPULATION_HASH = UNBOUND_PENDING_FULL_D7`
- Population binding may occur **only after** the Full-D7 scope/census issue is
  resolved and a **valid** population hash is frozen (owner correction #3), and
  only by writing the population-binding schema file; it may not alter any
  protocol semantic in this freeze.
- **OPWS execution is forbidden in this mission.** (Owner correction #8.)

## 10. Shoulder inputs

| Input | Source |
|---|---|
| task | frozen task identity (MAIN_297 manifest order at binding time) |
| selected file scope | frozen per-arm prediction artifact (arm registry) |
| reference non-test patch | frozen gold proxies + parent/target git objects |
| frozen test contract | frozen evaluator F2P node set + behavior contract |
| environment | Full-D7 frozen environment identity (bound later) |