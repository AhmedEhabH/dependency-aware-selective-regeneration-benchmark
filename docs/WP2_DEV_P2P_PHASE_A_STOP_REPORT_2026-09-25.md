# WP-2 DEV Unchanged-Test P2P — Mission-08 Phase A STOP REPORT (2026-09-25)

Decision token: **`P2P_DEV_INVENTORY_BLOCKED`**

Mission 08 Phase A executed: MAIN-only inventory correction (Section B), DEV
unchanged-test P2P inventory build + freeze (Section C), 2-ENG pilot selection
and SMALL serial pilot (Sections D + addendum), runtime/storage estimates
(Sections E/J), perf-gate decision (Sections F/G + addendum Q5), and a DRAFT
DEV Smoke design (Section K). Zero model/API/generation/repair/Smoke/E2E work.
The Phase-A execution STOPPED before the LARGE pilot and before any full 47-task
P2P evaluation, per the Q7 runtime guard.

## 1. MAIN-only inventory correction (Section B)

The existing unchanged-test P2P inventory covers **MAIN only**. Verified:
`inventory(297) ∩ MAIN = 220`, `inventory(297) ∩ DEV = 0`. It gives NO
unchanged-test preservation measurement for DEV; changed-test P2P_ONLY counts
from C2/C4 are NOT the dedicated preservation oracle;
`preservation_validation_complete` remains FALSE.

An explicit current-facing clarification was added to BOTH MAIN inventory
artifacts (`c4_clarification` block, hash-preserving):
- `research/wp2/oracle_confirmation_linux_v2_2026-09-23/wp2_unchanged_p2p_candidate_inventory_v1_final_2026-09-25.json`
- `research/wp2/wp2_unchanged_p2p_candidate_inventory_v1_2026-09-23.json`

`n_tasks_with_c4_exact_stable_p2p_nodes = 0` is zero **BY CONSTRUCTION** (C4 is
DEV; the inventory is MAIN-only). It does NOT imply P2P failure.
Script: `scripts/wp2_main_inventory_c4_clarification.py` (idempotent).

## 2. DEV inventory path / version / SHA-256

- **Path:** `research/wp2/wp2_dev_unchanged_p2p_candidate_inventory_v1_2026-09-25.json`
- **Artifact version:** `p2p-unchanged-inventory-dev-v1-2026-09-25`
- **P2P rule version (frozen V1):** `p2p-unchanged-inventory-v1-2026-09-23`
- **P2P sample salt (frozen, reused):** `wp2-p2p-unchanged-sample-v1-2026-09-23`
- **Inventory SHA-256:** `0ae5699b890ed3fe7a18cdbfb59bcb53d31d21f091102bef87f15b241ce2bf61`
  (stable across repeated finalize; canonical hash over payload without the
  `hashes` block)
- **Scope:** all 150 DEV census tasks considered; 47 oracle-valid.
- **Parent/Target P2P condition:** parent commit + SAME frozen test patch as the
  Linux V2 F2P oracle (`TEST_PATCH_APPLIED_ON_PARENT=true`); target commit.

## 3. Coverage (47-task oracle-valid union)

| Split | tasks | raw candidate nodes |
|---|---|---|
| DEV_TRAIN_ENG | 9 | 50,595 |
| DEV_TRAIN_ASSAY_HOLDOUT | 29 | 132,825 |
| DEV_VALIDATION | 9 | 46,761 |
| **47 union** | **47** | **230,181** |

Per era: py39 114,287 (32 tasks) · py312 110,346 (13) · py38 5,548 (2).

## 4. Candidate node totals

- **230,181 raw candidate nodes** across 47 tasks; **14,908 file groups**.
- Distribution: min 0 · max 12,213 · median 4,809 · p75 6,338 · p90 10,726.
- Tasks >400 nodes: 39 · >1,000: 32 · >5,000: 22 · >10,000: 9.
- Zero-node tasks (4): `0491163b00ea`, `4f70686fa303`, `9258154b8a0b`,
  `c4f01d449c62` — deterministic frozen-environment collection failure
  (webhook/observability conftest imports `fakeredis`, absent from the frozen
  py39 deps). Reported, not silently excluded.

## 5. cap=400 effects

- Cap is applied **POST-STABILITY** (addendum Q7): ALL discovered nodes are
  executed 3/3 parent + 3/3 target; only STABLE_P2P nodes are retained; the
  deterministic fixed-seed cap=400 is applied to the STABLE_P2P set only.
- Fields `n_stable_p2p_nodes_before_cap` / `n_stable_p2p_nodes_after_cap` /
  `capped_stable` / `preservation_nodes` are populated by the evaluator run.
  No pre-cap of raw nodes was introduced.

## 6. 2-task serial pilot selection

Selection from the 9 oracle-valid ENG tasks, inventory metadata ONLY (addendum
Q3): SMALL = smallest NON-ZERO discovered count; LARGE = largest discovered
count. Ties → task-id order.

| role | task_id | raw nodes | era |
|---|---|---|---|
| SMALL | `saleor-rc-2d45b76a52f2` | 176 | py39 |
| LARGE | `saleor-rc-d220843b5418` | 10,726 | py312 |

Zero-node ENG tasks reported (none of the 9 ENG are zero; all 4 zero-node
tasks are ASSAY_HOLDOUT/DEV_VALIDATION).

## 7. Serial pilot measurements (SMALL task, workers=1)

Evidence: `research/wp2/p2p_serial_pilot_2026-09-25/saleor-rc-2d45b76a52f2/A/`
(manifest.json, node_outcomes.json, node_classes.json, 114 JUnit files,
per-run logs).

- 176 nodes · 19 file groups · 21 associated files · py39
- class distribution: **STABLE_P2P 176 / TARGET_BROKEN 0 / PARENT_BROKEN 0 /
  BOTH_FAIL 0 / FLAKY 0 / COLLECTION_ERROR 0** → `stable/discovered = 1.0`
- target wall 595.1s (reps 254/138/181) · parent wall 703.4s (reps 316/188/181)
- worktree/env setup 0.5s · total wall 1299s · peak WSL RAM 13 GiB
- evidence integrity: 176 expected / 176 records / 0 missing / 0 dup / 0 orphan
  → OK
- DB lifecycle: `saleor_2d45b76a52f2_{t,p}` created per state, dropped after
  verification (0.55–0.88s each)
- worktrees removed after evidence verification (179→76 MiB worktree dir);
  reclaimed disk reported in manifest
- An initial run under a flawed node-arg mechanism (repr-joined args) produced
  44 spurious COLLECTION_ERROR nodes; the corrected sidecar-node-file runner
  gives 176/176 STABLE_P2P. Initial evidence preserved as
  `A_initial_v0runner/` and labeled as runner-artifact, NOT scientific.

## 8–9. Serial estimated runtime / storage for the 47 DEV tasks

Model calibrated to the SMALL pilot (0.6 s/node, 2.5 s/invocation, ~120 s
setup/state; range OPT/CON).

| estimate | 47-task serial | LARGE task only |
|---|---|---|
| optimistic | 206 h (8.6 d) | 9.4 h |
| central | 295 h (12.3 d) | 13.6 h |
| conservative | 398 h (16.6 d) | 18.3 h |

Central per split: ENG 66 h · ASSAY_HOLDOUT 169 h · VALIDATION 60 h.
Storage: evidence ≈ 115 MiB total; worktree peak ≈ 0.1 GiB (serial); C: stays
≈ 55 GiB (not a storage constraint). An intermediate maintenance boundary is
likely (wall-time bound; C4 precedent at 72/111), so the run would need
checkpointing/resume.

## 10. Perf-gate trigger

Conservative 398 h > 8 h threshold → nominally triggered. **The perf gate was
NOT run**: (a) the Q7 runtime guard forbids LARGE-task execution; (b) the
minimum valid gate (w1 A + w1 B + w2 comparison) requires a bounded gate set
whose members are already computationally infeasible under frozen V1 semantics;
(c) worker scaling cannot fix the frozen-semantics infeasibility. Per Q5 the
budget pre-check fails → freeze workers=1, no gate.

## 11. Workers benchmark table

Not produced — perf gate not run (workers=1 frozen by default; no parallel
comparison executed).

## 12. Natural-noise baseline

Not produced. The w1-repeat noise baseline is only needed for the parallel
equivalence gate, which was not triggered. The SMALL pilot is a single measured
lower-bound run (addendum point 6: not representative; lower-bound only).

## 13. Selected worker count

`workers = 1` (frozen by default; no parallel profile selected).

## 14. Measured/estimated speedup

No parallel speedup measured (perf gate not run). Serial SMALL-pilot wall:
1,299 s for 176 nodes.

## 15. Frozen P2P execution-profile identity

NOT frozen this phase (Phase-A STOP before execution-profile freeze). The
draft profile: workers=1; parent = parent + frozen test patch; target = target
commit; 3/3 + 3/3 repetitions; sidecar-node-file execution; per-state isolated
DBs dropped after verification; frozen V1 salt; post-stability cap=400;
evidence schema per pilot manifest. It MUST be reused unchanged across Smoke /
assay / E2E arms (Q12) once a V2 amendment resolves the Q7 scaling blocker.

## 16. Future MAIN P2P runtime/storage estimate (ESTIMATE ONLY — not executed)

MAIN unchanged-test node discovery has NOT run. Using the existing MAIN
inventory's associated-file counts and the corrected DEV ratio (10.19
nodes/file):

| population | n_tasks | est. nodes | central serial |
|---|---|---|---|
| 71 behavioral-only | 71 | ~355k | ~427 h (17.8 d) |
| behavioral ∪ symbol (83) | 83 | ~419k | ~504 h (21.0 d) |

**Population authority is UNRESOLVED**: no frozen decision exists for whether
future MAIN P2P preservation applies to the 71 behavioral-only, the
behavioral∪symbol union (83), or another population. Reported explicitly; NOT
decided here. MAIN P2P NOT executed.

## 17. Draft DEV Smoke design

`docs/WP2_DEV_SMOKE_DESIGN_DRAFT_2026-09-25.md` — DRAFT ONLY (no freeze, no
execution). Primary population: the 8 ENG BEHAVIORAL_F2P tasks (the 1 ENG
symbol-only task `9258154b8a0b` is NOT mixed in). Covers arms, visible/forbidden
inputs, output schema, generation/token/monetary budgets, repair/retries/
stopping, failure taxonomy, F2P + true unchanged-test P2P evaluation, the five
dimensions (Impact Correctness, Functional Correctness, Preservation,
Architecture Compliance, Efficiency), provenance, and the Q7 dependency (ENG-8
preservation alone ≈ 50,595 nodes / ~66 h central under frozen V1).

## 18–20. Metric / data-confirmation

18. **Primary F2P metric is TASK-LEVEL** — a task succeeds only if ALL frozen
    required BEHAVIORAL_F2P nodes pass; node-level rate is secondary.
19. **Primary Preservation metric will be TASK-LEVEL** once unchanged-test P2P
    is available (post-amendment); node-level P2P rate secondary.
20. **No HOLDOUT/VALIDATION outcomes used for tuning.** Frozen split membership
    unchanged (ENG 9 / ASSAY_HOLDOUT 29 / VALIDATION 9); ASSAY_HOLDOUT and
    DEV_VALIDATION node outcomes were never inspected for any tuning.

## 21. No generation / Smoke / E2E confirmation

Confirmed: no model/API/generation/repair/Smoke/assay/E2E/RM-CSS-vs-Agent
execution. INTERNAL_TEST and RESERVE untouched. MAIN generation quarantine
intact.

## 22. Discovery-correction note (integrity)

The initial deterministic discovery had a mechanism defect: inline
`mapfile` through the `bash -lc "<long string>"` argv layer silently read
0 lines for 43/47 tasks → whole-suite node sets; cassette `.yaml` paths with
`[]` made pytest error the whole session; `__init__.py` args triggered
package collection that leaked CHANGED-file nodes. All three were fixed
(script-file execution; `.py`-only collect args; exclude `__init__.py` /
`conftest.py` / `[]`-paths). Final discovery is validated: **0/47 tasks have
node files outside the associated unchanged-test set**, and a forced re-run
produced an identical node set (determinism spot-check). All reported numbers
in this report use the corrected discovery. Revision history recorded in the
feasibility artifact.

## 23. Q7 STOP finding and decision

Frozen V1's POST-STABILITY cap requires executing every raw candidate node
(230,181) 3/3 per state → ~8.6–16.6 days serial for the 47 DEV tasks; the LARGE
pilot alone is 9.4–18.3 h. This is the "major runtime problem" of Q7.
**No pre-stability cap or raw-node sampling was introduced.** Phase-A execution
STOPPED before LARGE pilot and before any 47-task P2P run. A scientifically
defensible **P2P V2 scaling amendment** is required (options V2-A two-stage
preservation oracle, V2-B stratified cap at discovery, V2-C task-subsampled
preservation, V2-D single-shot + stability spot-check — detailed in
`research/wp2/p2p_dev_feasibility_analysis_2026-09-25.json`).

## Exact current state

- DEV inventory frozen (`0ae5699b…`); discovery evidence persisted
  (`dev_unchanged_p2p_node_discovery_2026-09-25.jsonl`, 47 records);
  SMALL pilot evidence persisted + recorded in the inventory
  (176/176 STABLE_P2P); feasibility analysis persisted; Smoke draft written.
- The 47-task P2P evaluation and Smoke are NOT started.

## Next recommended action

Brain/authorization decision on a P2P V2 scaling amendment (choose among
V2-A..V2-D or an explicit alternative), which unblocks (1) the 47-task DEV
preservation evaluation under an amended rule, and (2) the DEV Smoke
Preservation dimension. Until then, workers=1 serial remains the frozen default
and no large-task or 47-task P2P execution may start.

---

## Validation summary

- Inventory finalize idempotent (hash stable over repeated runs).
- Split membership exact join with frozen dev-split-v2 (47 = 9+29+9; disjoint;
  zero role mismatches).
- No changed test file in any associated unchanged-test set (0 violations).
- Node discovery: 47/47 node-file ⊆ associated set; determinism spot-check
  identical; JSONL clean (47 unique records, no dupes/orphans).
- Pilot evidence integrity OK (0 missing/dup/orphan; 114 JUnit; logs).
- DB lifecycle (create per state / drop) verified; worktrees removed after
  verification.
- JSON/JSONL validity: all artifacts parse.
- Lint: ruff clean on all changed files. Mypy strict: clean on changed
  production module. Compile: clean. Targeted wp2 tests: 21 passed.
- Full project suite NOT run (no shared-interface change; per working rule,
  only targeted validation required for this mission scope).

---

# MISSION-09 ERRATA — APPEND-ONLY (2026-09-25)

These errata correct the record WITHOUT rewriting any Mission-08 historical
artifact and WITHOUT any Mission-08 rerun (Mission-09 §3).

## ERRATUM A — RAM field correction

The Mission-08 code used `free -g` and returned `parts[1]`:

- `wsl_mem_before_gib = 13.0` is the WSL **TOTAL** memory (MemTotal), not used
  memory.
- `peak_wsl_ram_gib = 13.0` was therefore **mislabeled**: it reported the same
  TOTAL value, not a measured peak.
- True Mission-08 peak RAM was **NOT measured**.
- The 176/176 STABLE_P2P scientific outcome is **unaffected** by this
  instrumentation defect.

Consequences (stated explicitly per Mission-09 §3):
- Do **NOT** claim Mission-08 used 13 GiB peak RAM.
- Do **NOT** claim workers=2 is impossible from Mission-08 RAM evidence.
- The feasibility artifact `research/wp2/p2p_dev_feasibility_analysis_2026-09-25.json`
  field `serial_pilot.peak_wsl_ram_gib = 13.0` is historical evidence of the
  mislabeled value and is NOT a valid peak-RAM measurement.

## ERRATUM B — GraphQL wording correction

Report the GraphQL association numbers accurately (Mission-09 §3):
- **~92.1%** refers to task–test-file association **occurrences** under GraphQL
  (count of (task, associated test file) pairs).
- **~54.7%** refers to **unique** associated test files under GraphQL.
- The two statistics answer different questions and must not be conflated.