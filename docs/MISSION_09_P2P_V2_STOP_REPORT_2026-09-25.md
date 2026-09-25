# MISSION-09 — P2P V2 GOLD FREEZE + ENG EXECUTION — STOP REPORT (2026-09-25)

Decision token: **`P2P_V2_ENG_READY`**

Mission-09 executed the two-tiered preservation design (P2P-S primary + P2P-U V2
extended) on the 8 executable oracle-valid ENG tasks × 2 caps (cap200 primary +
cap400 sensitivity), workers=1, with real resource instrumentation and full
integrity verification. Zero model/API/generation/repair/Smoke/assay/E2E/
HOLDOUT/VALIDATION/MAIN work. This report follows the Protocol v2 §9.2 detailed
closure format and Mission-09 §27 content requirements.

---

## 1. Executive verdict

**PASS — `P2P_V2_ENG_READY`.** The P2P-U V2 rule and membership were frozen
BEFORE any V2 outcome execution (rule SHA `78a089bb…`, membership SHA
`8325747f…`). P2P-S was frozen (46/47 defined). ENG cap200 + cap400 were executed
independently on all 8 executable ENG tasks with evidence integrity PASS
everywhere (0 missing / 0 duplicate / 0 orphan, valid JUnit refs). Independent
200-vs-400 overlap class agreement was **1.0** for all 8 tasks (Jaccard(STABLE_P2P)
= 1.0), and the cap400/cap200 wall multiplier was ≈1.37×. No material scientific
or repeatability issue blocks the next phase.

## 2. Scientific question answered

Does a pre-execution, outcome-blind, proximity-aware selection rule (P2P-U V2)
yield a deterministic, reproducible, feasible extended-preservation oracle over
the frozen unchanged-test candidate pool, and do the cap200 (primary) and cap400
(sensitivity) sets agree when executed independently on the ENG tasks?

## 3. Dataset / split and forbidden data

- **Used:** 8 executable oracle-valid ENG tasks (DEV_TRAIN_ENG) × 2 caps.
- **Forbidden and stayed unused:** `saleor-rc-9258154b8a0b` (P2P-U UNDEFINED,
  zero unchanged candidates) — not executed. No ASSAY_HOLDOUT, DEV_VALIDATION,
  MAIN, HOLDOUT, or INTERNAL_TEST outcomes used for any tuning. All candidate
  node IDs, gold touched paths, proximity scores, proximal/distal labels, cap
  memberships, test patch, and target outcomes are evaluator-only and invisible
  to generation/repair.
- **Development evidence only:** Mission-09 ENG execution is development/pilot
  evidence for the V2 oracle design; it is NOT confirmatory and does NOT make
  scientific claims about preservation success rates.

## 4. Validation-gate table

| Gate | Result | Evidence |
|---|---|---|
| Dataset (frozen Mission-08 inventory) | PASS | inventory SHA `0ae5699b…` verified at freeze |
| P2P-S exact extraction | PASS | `research/wp2/wp2_dev_p2p_s_v1_2026-09-25.json`; 46/47 defined, SHA repeatable |
| P2P-U V2 deterministic regeneration | PASS | membership artifact SHA stable across reruns |
| No changed-test contamination | PASS | 0 violations across all 47 tasks |
| No outcome dependence in selection | PASS | selection is a pure function (candidates+paths+salt) |
| first_200 ⊂ first_400 nesting | PASS | verified for every task |
| UNKNOWN handling | PASS | all-UNKNOWN → proximity 0 + flag (reproducible) |
| selected ∈ frozen raw inventory | PASS | 0 foreign nodes |
| Execution parent/target/3+3 | PASS | parent+frozen test patch; target; 3+3 reps, workers=1 |
| Evidence integrity | PASS | 0 missing/dup/orphan per task/cap; JUnit refs valid |
| Independent 200/400 | PASS | executed separately |
| Resource sampler vs raw | PASS | aggregates recomputed from raw samples; used≠total |
| Code (compile/ruff/mypy/tests) | PASS | 28 targeted WP2 tests pass; ruff/mypy/compile clean |

## 5. Main result table (ENG cap200 / cap400)

| metric | cap200 (PRIMARY) | cap400 (sensitivity) |
|---|---|---|
| executed tasks | 8 | 8 |
| selected nodes | 1,576 | 2,976 |
| STABLE_P2P nodes | 1,527 | 2,867 |
| STABLE_P2P overall rate | 0.9689 | 0.9634 |
| STABLE_P2P rate per-task avg | 0.9694 | 0.9659 |
| TARGET_BROKEN | 0 | 0 |
| PARENT_BROKEN | 0 | 0 |
| BOTH_FAIL | 7 | 16 |
| FLAKY | 1 | 3 |
| COLLECTION_ERROR | 40 | 90 |
| total wall (s) | 4,346.9 | 5,955.8 |
| cap400/200 wall multiplier | — | 1.37× |

Overlap repeatability (first-200 identities, independent runs): class agreement
**1.0** for all 8 tasks; stable-agreement **1.0**; Jaccard(STABLE_P2P) **1.0**;
0 class changes.

## 6. Development vs confirmatory label

All Mission-09 ENG evidence is **development** (design-validation for the V2
preservation oracle). It is not confirmatory and makes no preservation-success
scientific claims.

## 7. Fair-comparison warning

No cross-split head-to-head ranking is performed. cap200 vs cap400 comparison is
a sensitivity/repeatability analysis of the SAME frozen rule on the SAME tasks,
not a method comparison.

## 8. Interpretation

- P2P-U V2 is feasible where V1 was not: DEV-47 cap200 estimated ≈4.9–8.1 h
  serial (central 6.7 h) vs V1's ~8.6–16.6 days, because V2 caps BEFORE
  execution instead of after stability filtering.
- The 200/400 overlap agreement of 1.0 (identical class for every overlapping
  node across two INDEPENDENT executions) demonstrates high determinism and low
  flakiness at the node level for the selected set.
- STABLE_P2P rate is high (~0.96–0.97 overall). The residual non-stable nodes
  are dominated by COLLECTION_ERROR (deterministic environment/collection
  limitation, same nodes failing in both 200 and 400 runs) plus a few
  BOTH_FAIL/FLAKY — no TARGET_BROKEN/PARENT_BROKEN (unchanged tests behave as
  expected).

## 9. What this does NOT mean

- Does NOT mean generated patches pass preservation — no generated patch was
  evaluated.
- Does NOT mean the full 47-task DEV run is complete — only ENG 8 executed.
- Does NOT mean cap400 is "better"; cap200 remains PRIMARY by preregistration.
- Does NOT establish a preservation success rate claim for the population.
- Does NOT mean workers=2 is validated (no perf gate ran).

## 10. Competitor / baseline implication

The frozen P2P-S + P2P-U V2 evaluator is now available for all future
generation/repair arms under identical conditions (leakage firewall). No
arm-specific evaluator advantage exists. No effect on the RM-CSS vs Agent
localization claim (WP-1b unchanged, localization-only).

## 11. Threats / caveats

- **Resource instrumentation gap (INFORMATIONAL):** during the 16 ENG runs the
  sampler queried only `wp2-pg` for per-container metrics; the active `wp2-test-*`
  test container ran without a stable `--name` and its per-container RAM was NOT
  separately captured. WSL used (MemTotal−MemAvailable) peak ≈1.6 GiB is the
  conservative binding upper bound for all WSL-internal consumers. The sampler
  and runner were fixed to auto-discover/name `wp2-test-*` containers; future
  DEV-47 / MAIN runs capture per-test-container RAM directly. This is a documented
  instrumentation limitation, not a scientific integrity failure.
- Small n (8 ENG tasks) — pilot/development evidence only.
- Single repository (Saleor), single host.
- Some collection-error nodes reflect the frozen-era environment (e.g. fakeredis
  webhook conftest) and are UNDEFINED-like for those nodes; never silently
  excluded.

## 12. Tests / audit

- 28 targeted WP2 unit tests pass (`test_p2p_s_freeze_v1`, `test_p2p_u_v2`,
  `test_p2p_u_v2_exec`, `test_resource_sampler`).
- ruff clean; mypy strict clean on changed production modules; py_compile clean.
- `test_live_status_blocks.py` PASS (byte-for-byte LIVE_STATUS sync).
- Evidence integrity PASS for all 16 executed task/cap runs.

## 13. Documentation changed

- `docs/MISSION_09_P2P_V2_IMPACT_DECLARATION_2026-09-25.md` (new).
- `docs/WP2_DEV_P2P_PHASE_A_STOP_REPORT_2026-09-25.md` (Mission-08 errata A/B).
- `docs/WP2_DEV_SMOKE_DESIGN_DRAFT_2026-09-25.md` (errata C + Mission-09 update).
- `DECISIONS.md` (Mission-09 decisions appended).
- `docs/LIVE_STATUS.json` + `README.md` / `START_HERE_CURRENT_*` / `PROGRESS.md` /
  `00_CURRENT_RESEARCH_STATE.md` (via `render_live_status.py --write`).

## 14–16. Git / merge / tag

See ENGINEERING section below.

---

# SCIENTIFIC DETAIL

## P2P-S (primary preservation)

- Definition: node in changed/test-patch test scope; parent + frozen test patch =
  STABLE_PASS 3/3; target = STABLE_PASS 3/3 (frozen C2/C4 P2P_ONLY).
- Artifact: `research/wp2/wp2_dev_p2p_s_v1_2026-09-25.json`, SHA
  `4d8fc95961ab87ca58b362fc7e52780dfd84734d74111c83032366432cbe7966`.
- 47 tasks: **46 defined / 1 undefined** (ENG `saleor-rc-39b4138e8550`); **8
  sparse** (<10 nodes). Zero-node task = UNDEFINED, never PASS.
- Coverage: ENG 8/9 defined (622 nodes), ASSAY_HOLDOUT 29/29 (3,073),
  DEV_VALIDATION 9/9 (1,339); union 46/47 (5,034 nodes). Median 53 (defined);
  min 1 / p25 13 / p75 117 / max 710.
- Evidence source: `per_test_dev_v2.jsonl` (SHA `b04c0adc…`), final Mission-07/C4.

## P2P-U V2 rule (frozen before execution)

- Artifact: `research/wp2/wp2_p2p_u_v2_rule_freeze_2026-09-25.json`, rule SHA
  `78a089bb3cea599b2d4040e92388f3e011860da07e4522670c260ec61f8d63e1`.
- Salt: `wp2-p2p-u-v2-2026-09-25` (frozen before outcomes; never changed).
- Proximity = max over KNOWN touched production files of longest common leading
  component count after `saleor/`. UNKNOWN paths contribute no score;
  all-UNKNOWN → proximity 0 + `all_touched_paths_unknown=true`.
- PROXIMAL (≥2) / DISTAL (≤1 incl. 0/UNKNOWN); P,P,P,D interleave; round-robin
  one node per file per round; first_200 ⊂ first_400 exactly.
- Caps: PRIMARY 200 (target 150/50); sensitivity 400 (target 300/100); pool
  shortage backfills deterministically; never invent candidates.
- Classification precedence: FLAKY > COLLECTION_ERROR > STABLE_P2P >
  TARGET_BROKEN > PARENT_BROKEN > BOTH_FAIL; only STABLE_P2P freeze.

## P2P-U V2 membership (frozen)

- Artifact: `research/wp2/wp2_p2p_u_v2_membership_2026-09-25.json`, SHA
  `8325747f7967729e544de4dacb76ac69fde187b7dc05d59e1f24fdef7d20daac`.
- ordered-candidate SHA `0b027352…`; cap200 `7d9cdecb…`; cap400 `7ce46952…`.
- 47 tasks; 4 zero-node UNDEFINED (`0491163b00ea`, `4f70686fa303`,
  `9258154b8a0b`, `c4f01d449c62`). All 47 verify: first200 ⊂ first400, disjoint
  proximal/distal, no duplicates, all candidates used once.

## ENG execution (evidence)

- Evidence root: `research/wp2/p2p_u_v2_eng_2026-09-25/` (per-task/cap manifests,
  node_outcomes, node_classes, JUnit, logs, resource_samples.jsonl).
- Consolidated: `consolidated_results_2026-09-25.json`.
- Sensitivity: `SENSITIVITY_REPORT_200_vs_400_2026-09-25.md`.
- Resources: `resource_summary_2026-09-25.json`.
- Estimates: `dev47_and_main_estimate_2026-09-25.json`.

## Quality metrics

- STABLE_P2P rates per task (cap200): 1.0, 0.975, 0.905, 0.975, 0.97, 0.965,
  0.985, 0.98; overall 0.9689.
- No TARGET_BROKEN/PARENT_BROKEN in any run. FLAKY ≤3, BOTH_FAIL ≤7 per run.
- COLLECTION_ERROR 40 (cap200) / 90 (cap400) across tasks — deterministic
  collection/environment nodes (identical identities across independent runs).

## Speed

- Total mission execution (8 tasks × 2 caps): ~10,303 s ≈ 2.86 h wall.
- cap200 total 4,346.9 s (1576 nodes); cap400 5,955.8 s (2976 nodes).
- Measured per-node wall (cap200) 2.07–3.43 s/node incl. setup.
- DEV-47 cap200 estimate: optimistic 4.9 h / central 6.7 h / conservative 8.1 h
  (43 executable tasks; 8,402 selected nodes).
- MAIN future cap200: 71 behavioral ≈11.1 h; behavioral∪symbol (83) ≈12.8 h.

## RAM (real, corrected)

- Host visible total 27.9 GiB; host peak used 24.9 GiB; host minimum available
  3.0 GiB (all-runs aggregate).
- WSL MemTotal (VM ceiling) 13.6 GiB; WSL peak USED 1.6 GiB; WSL min available
  ~12.5 GiB; WSL swap peak used 0.0 GiB.
- PostgreSQL peak RAM 0.31 GiB; test-container RAM not separately captured in ENG
  (bounded by WSL used peak 1.6 GiB); sampler fixed for future runs.
- Mission-08 peak RAM (13.0 GiB) explicitly NOT claimed; errata recorded.

## CPU

- Host CPU: avg 29.8%, p95 50.1%, max 97.9% (all runs).
- WSL load 1m: avg 1.1, p95 1.75, max 3.32 (12 vCPU).
- PostgreSQL CPU: avg 10.2%, p95 25.0%, max 80.0%.
- Docker cpu% is core-normalized (100% = 1 core), not whole-machine.

## DISK

- C: free: start ~53.3 GiB; minimum during runs 42.36 GiB; after cleanup 42.1 GiB
  (above 40 GiB warning threshold throughout; no HARD STOP).
- WSL fs used ≈44.8→46.3 GiB; ext4.vhdx host 57.2→58.8 GiB.
- Worktrees: 0 leftover (removed after each verification); DBs dropped.
- Evidence total ≈59.3 MiB (16 runs).

## EFFICIENCY

- 16 executed task/cap runs; each 6 pytest invocations (3 parent + 3 target;
  1 chunk each) → 96 pytest invocations total (chunk count 1 because WSL
  ARG_MAX 2 MB ≫ max ~55 KB node set).
- Node-state-runs requested = selected_nodes × 6 = 1,576×6 + 2,976×6 = 27,312.
- Seconds/node ≈ 2.76 (cap200 wall / selected); ≈13 KB evidence per node-state.
- Setup fraction small (≈3.7 s central per state); execution dominates.

## INTEGRITY

- missing = 0, duplicates = 0, orphans = 0 for all 16 runs; JUnit refs valid.
- Deterministic hashes stable (freeze regenerated identical SHAs).
- Nesting first_200 ⊂ first_400 PASS all tasks.
- Environment provenance: era images py38/py39/py312 frozen digests; WSL
  Ubuntu-24.04; postgres:15-alpine; workers=1; no `.wslconfig` change.

## SCOPE

- No generation, no repair, no Smoke execution, no assay, no E2E.
- No HOLDOUT/VALIDATION outcome execution/tuning.
- No MAIN P2P-U execution.
- INTERNAL_TEST untouched; RESERVE (786) untouched/sealed.
- No cap/salt tuning after results; no workers=2; no `.wslconfig` change.

---

# ENGINEERING

- Branch: `main`; HEAD at start == origin/main (`eb5e21d`). Tree was the
  uncommitted Mission-08 checkpoint; Mission-09 adds new artifacts/scripts/tests
  and documentation. No Mission-07/08 history rewritten.
- Commit: `f2416d8302a51316fc1bccf0e5286a4534f62029` — "feat(wp2): Mission-09
  P2P V2 gold freeze + ENG cap200/cap400 execution".
- Tag: `wp2-p2p-v2-eng-freeze-2026-09-25` (annotated) on the same commit,
  pushed to origin.
- Push: `origin/main` updated `eb5e21d..f2416d83` (warning only: the 60.35 MB
  membership artifact exceeds GitHub's 50 MB size recommendation; it is a
  deterministic freeze artifact by design and its SHA is pinned for audit).
- Working tree after commit: only pre-existing untracked `logs/`
  (Mission-07/08 operational logs) and `scripts/watch_c4_reliable.ps1`
  (Mission-08 helper) remain untracked — intentionally not part of Mission-09.
- Exports: FULL + TRUE LIGHT (see EXPORTS section above).
- Release provenance invariant: artifact source commit `f2416d83` == tag peel
  `f2416d83`. Post-tag docs evidence is committed in the same commit (tag target
  is the single accepted source commit).

## NEXT (recommended next mission)

1. **Whether ENG is ready for Smoke freeze:** YES with approval — P2P-S + P2P-U
   V2 evaluator frozen; ENG executed with integrity PASS.
2. **Whether full 47-task P2P-U cap200 is ready for overnight execution:** YES —
   estimated central ≈6.7 h serial, overnight-feasible with checkpoint/resume;
   requires explicit approval (not authorized in Mission-09).
3. **Whether workers=2 merits a future MAIN-only perf gate:** POSSIBLY — ENG shows
   execution-dominated (not setup-dominated) cost, so a bounded MAIN-only
   workers=2 gate may be worth testing; NOT run in Mission-09.
4. **Exact next recommended mission:** Mission-10 — full 47-task P2P-U cap200
   execution (overnight, resumable) + DEV Smoke freeze, pending Ahmed's decisions
   on Smoke freeze, DEV-47 execution, and MAIN population authority.

---

# EXPORTS

## FULL AUDIT EXPORT

```
PROJECT_EXPORT_READY
PROJECT_EXPORT_NAME=project-2026-09-26-0205.zip
PROJECT_EXPORT_PATH=C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project-2026-09-26-0205.zip
PROJECT_EXPORT_SIZE_BYTES=247791372
PROJECT_EXPORT_SHA256=e340d412980e2541cbb4e43ff9443a36e2f43ff5140f26903cfeff2976eb285c
UPLOAD_THIS_FILE=project-2026-09-26-0205.zip
```

Verified: `.git/HEAD` present; `dist/pilot-kaggle-upload.zip` + `.sha256` present
(they exist locally, so the "archived member" exception does NOT apply);
ZIP opens successfully; 12,665 entries.

## TRUE LIGHT EXPORT

```
LIGHT_EXPORT_READY
LIGHT_EXPORT_NAME=project-LIGHT-2026-09-26-0212.zip
LIGHT_EXPORT_PATH=C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project-LIGHT-2026-09-26-0212.zip
LIGHT_EXPORT_SIZE_BYTES=54331759
LIGHT_EXPORT_SHA256=3d18b1325f02cc7081b245e9ab3b39b4d118e0e05e6cecb6f79d7dcb76e6074b
WITHIN_50MB=False
```

**Why TRUE LIGHT exceeds 50 MB (54.33 MB):** the standard TRUE LIGHT filter plus
exclusion of the deterministically-reproducible P2P-U membership artifact
(63.79 MB raw, regenerable via `scripts/wp2_p2p_u_v2_freeze.py`, SHA-anchored
`8325747f…`) leaves 54.33 MB. The residual bulk is the **frozen Mission-08 DEV
inventory** (34.20 MB) and the **raw unchanged-test node-discovery JSONL**
(28.69 MB), which are the direct frozen inputs to the Mission-09 P2P-S / P2P-U
freeze and are NOT cheaply reproducible (raw discovery requires the frozen
WSL/Docker node-discovery environment). Per Mission-09 §26, required evidence is
NOT deleted just to hit the number; the audit-essential evidence (P2P-S artifact,
P2P-U rule, consolidated results, sensitivity report, per-task manifests,
resource summary, estimates, STOP report, freeze script) is confirmed present in
the LIGHT export (`AUDIT_EVIDENCE_PRESENT=True`).

## Tag

- Tag: `wp2-p2p-v2-eng-freeze-2026-09-25` (annotated), created on commit
  `f2416d8302a51316fc1bccf0e5286a4534f62029` (== HEAD; == tag peel). Pushed to
  origin.
