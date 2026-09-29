# WP2 M13B: pilot design and readiness freeze (brain-authored)

M13B supersedes the M13 v1 kit (ChatGPT, 2026-09-29), which was reviewed and not installed.
M13B makes zero API calls, zero Docker/WSL calls and no paid generation.

## 1. What M13B fixes relative to M13 v1

| # | M13 v1 defect | M13B fix |
|---|---|---|
| F1 | The reserve held only 2 tasks (26 eligible − 24 selected), and nothing said what happens if more than 2 tasks fail oracle readiness. | A frozen rule, `finalize_after_readiness`, is applied in M14A.S0 before any paid call. Readiness is checked on all 26 eligible tasks, including B and the reserve. The outcome is FULL, REDUCED_n (n ≥ 10, A and B kept symmetric), or POOL_INSUFFICIENT (human decision). |
| F2 | Pilot-B assumed Agent selections exist. None do for any holdout task (0/26). | The census records the gap. M15.S0 runs a paid Agent localization with the frozen protocol-v3: one run per task per replicate. The cost (~$0.56) is budgeted, and the cost boundary includes the selector. |
| F3 | Gate A3 (GOLD RESOLVED ≥ 4/24) passes with only P ≈ 0.74 at the Smoke rate of 0.20, so roughly 1 run in 4 fails by chance. | Gates are A2 ≥ 14, A3 ≥ 3, A4 ≤ 1 and A5 ≥ 2, scaled by `gates_for(n)`. A3 now passes with P ≈ 0.89. Its calibration is written into the design. A failing floor gate leads to HUMAN_DECISION, never to an automatic branch. |
| F4 | No LIGHT export on STOP or on completion. | Controller v2.2.3 exports on every STOP, and P10 requires the LIGHT export. |
| F5 | The commit step was not idempotent: a failed push left the run stuck on STAGED_SET_MISMATCH. | Commit is a no-op when nothing is staged, and pushes are retried. POST_ACTION_FAILED is resumable. On resume, a tag found one STOP-commit behind HEAD is accepted only when the commits in between changed nothing but controller bookkeeping. |
| F6 | STOP reports did not say why a step failed. | The last 40 lines of the failing command's log are embedded in the state and in the report. |
| F7 | Tags were pushed with `--tags` (the cause of the Smoke P05 incident). | Every tag is pushed by exact refspec, with a regression test that uses a divergent unrelated tag. |
| F8 | The summary's per-arm `billed_tokens` value included cache reuse. | The usage artifact separates fresh (billed) tokens from cache-reuse tokens per arm. The Smoke summary itself is not modified. |
| F9 | M13 v1 wrote its new artifacts into the closed Smoke root. | All M13B outputs go to `research/wp2/pilot_v1_design/`. The Smoke root is read-only and its files are hash-guarded. |

## 2. Audited facts M13B relies on

Each fact is re-derived at run time. If any value differs, the run STOPs.

- **Smoke v2.2 closure:**
  - Token `E2E_SMOKE_V22_PIPELINE_VALID`, NEXT `PILOT_DESIGN`, all 13 phases PASS.
  - Generation freeze `29a4e1f1…`.
  - Smoke freeze `4c41fdfe…`.
  - 7 source-guard hashes.
- **Tokens and cost:**
  - 949,529 provider-reported tokens: 865,733 prompt + 83,796 completion.
  - $0.2769655 across 77/77 HTTP 200 calls.
  - AGENT_HARD includes 21,226 cache-reuse tokens.
- **Forensics:**
  - GOLD: 11 APPLIED, 3 INVALID (SEARCH_ERROR ×6), 3 RESOLVED.
  - RM-CSS: 11 APPLIED, 2 INVALID, 1 NO_SCOPE, 2 RESOLVED.
  - Variance: 5/6 APPLIED, 1/6 same status, 0/6 same diff.
- **Pool:**
  - ASSAY_HOLDOUT has 80 members; 62 appear in per-task data and 26 are eligible (py39 16, py312 8, py38 2).
  - RM-CSS OOF predictions exist for 25 of the 26 eligible tasks. The missing one is a Pilot-A task, which does not matter because Pilot-A does not use RM-CSS.
  - Agent selections exist for 0 of the 26.

## 3. Task → subtask → atomic map

The authoritative source is `controller/task_map_m13_m16_v1.json`. It is validated by P07, rendered to `TASK_MAP_M13_M16.md`, and hash-frozen.

- **M13** (zero API, executable now):
  - S13.0 install
  - S13.1 evidence closure: P00–P03
  - S13.2 pool and selection: P04–P05
  - S13.3 design and map freeze: P06–P08
  - S13.4 independent verification and provenance: P09–P10
  - S13.5 human gate: H13
- **M14A** Pilot-A (paid, specification only):
  - S0 oracle readiness + replacement rule
  - S1 authorization + freeze
  - S2 generation (48 episodes)
  - S3 evaluation
  - S4 gates
- **M14R**: interface review, only after a floor-gate hold, and on ENG only.
- **M15** Pilot-B (paid, specification only):
  - S0 RM-CSS scopes, then Agent localization (r1 and r2), then selector freeze
  - S1 generation of 72 episodes (RMCSS, AGENT, GOLD × 2), then evaluation and summary
- **M16**: Research Run freeze. The replicate rule chooses 2 or 3 replicates, never 1. Human authorization is required.

Transition contract: an atomic step advances only when its inputs match, exactly its declared outputs exist, its checks pass, no forbidden file or pool was touched, and the state records PASS. In every other case the controller STOPs with that atomic's token. There is no AI repair and no fallback.

## 4. Deterministic executable

- `scripts/wp2_m13.py` holds the atomic steps. Each step writes one self-hashed artifact.
- `scripts/wp2_ctl_v223.py` is the controller, driven by `controller/plan_m13_pilot_prep_v1.json`.
- `controller/KIT_MANIFEST_M13B.json` holds the kit hashes, and the controller refuses to run if any kit file was edited.
- The installer is one file that OpenCode runs. It checks everything, writes the kit, runs the tests, commits, tags the kit, and rolls back on failure.

## 5. After M13B

The human sends the LIGHT zip (`project-LIGHT-M13B_DESIGN_FREEZE-*.zip`) to the brain. The brain then builds the M14A kit, which refuses to start unless `PILOT_A_HUMAN_AUTH_TEMPLATE.json` has been filled in and committed with a matching design hash.
