# WP-2 DEV Smoke Design — DRAFT (2026-09-25, Mission-08 Phase A §K)

**Status: DRAFT ONLY — NOT FROZEN, NOT AUTHORIZED FOR EXECUTION.**

This document drafts the DEV Smoke design. It is pipeline-validation only; it
makes NO comparative scientific claims. No Smoke execution may start until a
separate frozen authorization exists, AND until the Q7 scaling question
(Section 12) is resolved by a scientific amendment.

---

## 1. Purpose

PIPELINE VALIDATION ONLY for the DEV generation→F2P→P2P evaluation pipeline.
Not a comparison of methods. No headline scientific conclusions.

## 2. Primary smoke population (frozen)

The **8 ENG BEHAVIORAL_F2P tasks** (DEV_TRAIN_ENG oracle-valid, behavioral
primary):

| task_id | era | C4 behavioral nodes |
|---|---|---|
| saleor-rc-2d45b76a52f2 | py39 | 2 |
| saleor-rc-39b4138e8550 | py312 | 26 |
| saleor-rc-74538ea00ce9 | py312 | 5 |
| saleor-rc-82c56bde0e34 | py39 | 11 |
| saleor-rc-8f76ddc6267f | py39 | 1 |
| saleor-rc-d220843b5418 | py312 | 1 |
| saleor-rc-dfe77ac1c5dc | py312 | 1 |
| saleor-rc-e03ee76d2b89 | py39 | 1 |

The 1 ENG **symbol-only** task (`saleor-rc-9258154b8a0b`) is NOT mixed into the
primary behavioral smoke. It may be listed as a separate secondary stress item
only if explicitly authorized; it never joins the primary behavioral population.

## 3. Experimental arms (draft)

- **Arm A — RM-CSS selective regeneration** (impact-selection driven).
- **Arm B — Agent selective regeneration**.
- Optional **Arm P — Placebo** (files that exist at parent; sized by Gold files
  that exist at parent, per frozen amendment-K rules) — only if authorized.

All arms run on the SAME 8-task population, SAME visible inputs per arm, SAME
frozen P2P execution profile (once a V2 amendment resolves Q7), SAME evaluator.
No arm-specific evaluation advantage (Q12).

## 4. Visible inputs per arm

- FULL developer change description (primary specification, frozen K rule).
- Arm-selected production files (the predicted write set).
- Commit-era repository state (parent commit worktree), era metadata.

## 5. Forbidden target-derived inputs

- Target source code signatures/docstrings as primary inputs (frozen K).
- Target test-file contents, target diffs, oracle classifications, F2P node
  identities, P2P candidate sets (evaluator-only and invisible to
  generation/repair).
- ASSAY_HOLDOUT / DEV_VALIDATION outcome information.

## 6. Output schema (draft)

Per (task, arm, replicate):
- generated patch (diff) + JSON manifest
- token accounting record
- monetary cost record
- per-stage wall-clock timings
- generation status (SUCCESS / FAILED / SKIPPED)
- repair log (if repair authorized)
- F2P evaluation result (task-level pass/fail + secondary node pass-rate)
- P2P preservation result (task-level + node-level, if the V2 amendment is in force)
- impact correctness metrics (precision/recall/F1 on predicted write set vs observed change-set proxy)
- architecture compliance flags
- provenance block (generator SHA, prompts hash, environment fingerprint)

## 7. Generation budget / token accounting / monetary cost

- Generation budget: fixed per-task cap (e.g. N attempts) frozen at
  authorization time; measured, never tuned on HOLDOUT/VALIDATION.
- Token accounting: every request/response token counted per arm; zero-LLM
  components report 0.
- Monetary cost: per-provider price × tokens + retries; recorded per
  (task, arm, replicate); total reported.

## 8. Repair policy / retries / stopping rules

- Repair policy: draft — a bounded repair loop (max R repairs/task) defined at
  freeze; each repair is a generation event (token/cost counted).
- Retries: transport-level retries with backoff; recorded.
- Stopping rules: stop a task's generation after the repair budget is
  exhausted OR a generated patch passes the task-level F2P gate; stop Smoke
  entirely on any instrumentation-level anomaly (M1–M5-style review card).

## 9. Failure taxonomy

- GENERATION_FAIL (no patch), PATCH_APPLY_FAIL, COLLECTION_FAIL,
  TASK_LEVEL_F2P_FAIL, F2P_ATTENTION (any node fails), ENV_FAIL,
  INSTRUMENT_ANOMALY (STOP). Each mapped to evidence.

## 10. F2P evaluation (functional correctness)

PRIMARY metric is TASK-LEVEL: a task succeeds only if ALL frozen required
BEHAVIORAL_F2P nodes pass (target state). Report `successful tasks / eligible
tasks`. Node-level pass rate is SECONDARY/descriptive only (metric rules L).

## 11. True unchanged-test P2P evaluation (preservation)

PRIMARY metric is TASK-LEVEL once unchanged-test P2P is available: a task's
preservation passes if all frozen preservation nodes (capped STABLE_P2P set)
remain stable 3/3 parent AND 3/3 target under the generated patch. Node-level
P2P rate is SECONDARY. This evaluation reuses the frozen P2P execution profile
unchanged (Q12) — parent + frozen test patch; target = parent + generated
patch.

## 12. DEPENDENCY: Q7 scaling blocker (critical for Smoke)

The frozen V1 post-stability cap requires executing every discovered raw
candidate node 3/3 per state. The 8 ENG behavioral tasks alone carry
**50,595 raw candidate nodes** (~66 h central serial) for preservation
evaluation. A Smoke that evaluates preservation on all of them is infeasible
under frozen V1 semantics. Smoke's Preservation dimension therefore DEPENDS on
a scientifically defensible P2P V2 scaling amendment (see
`research/wp2/p2p_dev_feasibility_analysis_2026-09-25.json` amendment options
V2-A..V2-D). Smoke execution must not start until this is resolved. (Corrected
discovery: see feasibility analysis revision 2.)

## 13. Architecture compliance

Generated patches must stay within the arm's selected scope (allowed file
list), not modify test paths (frozen K: edits to test paths forbidden in all
future generation arms), and not introduce undeclared files. Flags recorded
per patch.

## 14. Impact correctness

For each arm: predicted write set vs observed change-set proxy (Gold) →
precision, recall, F1 (micro and task-level). No arm comparison claims from
Smoke; directional only.

## 15. Efficiency

Wall-clock per task/arm, generation vs evaluation split, LLM tokens/cost (zero
for non-LLM components), peak RAM/disk.

## 16. Provenance

Every Smoke artifact records: generator/orchestrator/evaluator SHAs, DEV
inventory SHA (`0ae5699b890ed3fe7a18cdbfb59bcb53d31d21f091102bef87f15b241ce2bf61`),
P2P profile identity (post-amendment), era image
digests, PostgreSQL condition, worktree lifecycle, evidence schema.

## 17. Five required evaluation dimensions

1. **Impact Correctness** — §14.
2. **Functional Correctness** — §10 (task-level primary).
3. **Preservation** — §11 (task-level primary; blocked pending Q7 amendment).
4. **Architecture Compliance** — §13.
5. **Efficiency** — §15.

## 18. Guards

- No HOLDOUT/VALIDATION tuning. No MAIN generation. No INTERNAL_TEST / RESERVE
  access. No Smoke execution without separate authorization.

---

# MISSION-09 UPDATE — P2P-S + P2P-U V2 (2026-09-25) — STILL DRAFT, NOT FROZEN

Mission-09 resolved the Q7 scaling blocker with the two-tiered preservation
design (P2P-S primary + P2P-U V2 extended) and executed it on ENG. This section
updates the Smoke draft accordingly. Smoke itself is STILL NOT FROZEN and NOT
authorized for execution.

## 19. Q7 blocker RESOLVED by V2 (Mission-09)

- **P2P-S (primary):** SWE-bench-aligned changed-test PASS_TO_PASS preservation
  using the existing frozen C2/C4 `P2P_ONLY` classification, strengthened with
  3/3 stability on both parent+frozen-test-patch and target. Frozen artifact:
  `research/wp2/wp2_dev_p2p_s_v1_2026-09-25.json` (46/47 defined; 1 undefined;
  8 sparse). NO new oracle construction execution was needed.
- **P2P-U V2 (extended):** outcome-blind, proximity-aware, deterministic
  PRE-execution cap over the frozen Mission-08 unchanged-test candidate pool.
  Rule + salt + membership frozen BEFORE any V2 outcome execution
  (`research/wp2/wp2_p2p_u_v2_rule_freeze_2026-09-25.json`,
  `research/wp2/wp2_p2p_u_v2_membership_2026-09-25.json`).
- V1 remains immutable historical evidence; V2 is an explicitly versioned
  amendment.

## 20. Smoke preservation dimensions (updated)

Preservation is now THREE-part, all task-level PRIMARY for their own scope:

1. **P2P-S task-level = PRIMARY** — denominator = tasks where P2P-S is DEFINED
   (n_p2p_s_nodes > 0). Generated-patch PASS iff ALL frozen P2P-S nodes pass.
   Zero-node task = UNDEFINED, excluded from denominator, never automatic PASS.
   Node-level rate secondary.
2. **P2P-U cap200 task-level = EXTENDED** — denominator = tasks where cap200
   P2P-U is DEFINED. PASS iff ALL frozen cap200 STABLE_P2P nodes pass. Zero-node
   = UNDEFINED.
3. **P2P-U cap400 = ENG sensitivity only** — the 400-membership set is a
   deterministic superset of 200; executed independently; report disagreement,
   never retune K. cap200 remains PRIMARY.

Every generated ENG Smoke patch is evaluated against:
- P2P-S frozen set;
- P2P-U cap200 PRIMARY set;
- P2P-U cap400 SENSITIVITY set.

## 21. Evaluator leakage firewall (unchanged, reaffirmed)

Gold touched-production paths, P2P-S node IDs, P2P-U candidate node IDs, cap
memberships, proximity scores, proximal/distal labels, test patch, target
diff/outcomes all remain invisible to EVERY generation/repair arm. Same frozen
evaluator for all arms; no arm-specific advantage.

## 22. Collateral-edit scope metrics (descriptive; future arms)

For each generated patch, record (evaluator-only, must not leak gold paths to
generation):
- number of files edited;
- files edited outside the gold touched-production set;
- proportion outside gold set;
- directories/apps touched outside gold scope.

## 23. ENG V2 execution summary (Mission-09, evidence)

- 8 executable ENG tasks × 2 caps (cap200 + cap400), workers=1, 3+3 reps.
  `saleor-rc-9258154b8a0b` P2P-U UNDEFINED (zero candidates) — no execution.
- Evidence: `research/wp2/p2p_u_v2_eng_2026-09-25/` (integrity PASS everywhere;
  0 missing/duplicate/orphan; JUnit refs valid).
- Overlap repeatability (first-200 identities, independent 200/400 runs):
  class agreement = 1.0 for all 8 tasks; Jaccard(STABLE_P2P) = 1.0.
- cap400/cap200 wall multiplier ≈ 1.37x; stable-rate overall 0.9689 vs 0.9634.
- Resource sampler corrected (host/WSL/container/CPU/disk/time; no
  total-as-peak). ENG WSL peak used ≈ 1.6 GiB; host peak used ≈ 24.9 GiB.

## 24. Remaining open decisions needing Ahmed's approval before Smoke freeze

1. **Smoke freeze authorization** — Mission-09 does NOT authorize Smoke freeze
   or execution.
2. **Full 47-task P2P-U cap200 execution authorization** — Mission-09 executed
   ENG only; DEV-47 cap200 estimated ≈ 4.9–8.1 h serial (central 6.7 h),
   overnight-feasible with checkpointing/resume. Needs explicit approval.
3. **P2P-S for Smoke** — confirm P2P-S (46/47 defined) is the PRIMARY
   preservation dimension for Smoke (recommended) vs P2P-U cap200 only.
4. **MAIN population authority** — future MAIN P2P-U cap200 population remains
   UNRESOLVED: 71 behavioral-only vs behavioral∪symbol (83). Both estimated
   (≈11.1 h vs ≈12.8 h central). Decide before MAIN execution.
5. **workers=2 future MAIN-only perf gate** — Mission-09 kept workers=1 and did
   not run a perf gate; recommend deciding whether a workers=2 MAIN-only gate is
   worth testing (not authorized here).
6. **Arm set** — confirm Arm A (RM-CSS) + Arm B (Agent) + optional Arm P
   (Placebo) for Smoke.