# WP2 M14A: independent review of the ChatGPT candidate

**Verdict: M14A_REVIEW_FAIL.** This kit is the corrected replacement. It was reviewed and built with zero paid or model calls, and it was not executed.

## Inputs audited

| Item | SHA-256 |
|---|---|
| WP2_M14A_KIT_2026-09-29.zip | 85d40a747bc34486a83409912346443c2c82b37bf3204973cc36aaf1433ead7c (matches) |
| WP2_M14A_INSTALL_2026-09-29.py | 0dbca9c3fc4556ab0f5301b85e4f08c018cd1897d37e3ef551a53f9b86a48bb4 (matches) |
| project-LIGHT-M13B_DESIGN_FREEZE-2026-09-29-1033.zip | 4b65f65c9030cf1f190478ce56f9749713107959a316443dd4de5de6e1f229df |

## A. M13B re-derived from the LIGHT

All 10 M13B artifacts pass their self-hash check. Key values:

- **Artifact hashes:**
  - design `c4c28d58…`
  - selection `85e238af…`
  - verify `2dbc2851…`, all 9 checks true
- **m13_freeze:** every file hash matches the LIGHT copy.
- **Pool:** 26 eligible tasks (py39 16, py312 8, py38 2).
- **Selection:**
  - A and B are each 12 tasks and disjoint.
  - Reserve, in order: `saleor-rc-f383043e4be3`, `saleor-rc-102e4e5b25e8`.
- **Pilot-A:**
  - Arms GOLD_HARD and PLACEBO_HARD, replicates r1 and r2, ceiling $1.00.
  - `gates_for(12)` = A2≥14, A3≥3, A4≤1, A5≥2.
  - Interface unchanged from Smoke v2.2.
- **Frozen readiness atomic, M14A.S0.A1 (task map):** "materialize parent+test patch; gold diff must PASS F2P; empty must FAIL F2P; P2P defined".

## Defects in the candidate

Each defect is marked **SD** (scientific design) or **ID** (implementation).

| # | Type | Defect | Evidence |
|---|---|---|---|
| D1 | SD | P2P-U readiness uses the superseded **V1** post-stability rule: every rediscovered candidate is executed and the stable set is then capped. The frozen rule is **P2P-U V2/V3**: an outcome-blind, proximity-ordered cap200 selection, then execution of those 200 nodes ×3 on parent and target, keeping STABLE_P2P. V2/V3 is the rule that produced the Smoke evaluator sets (`eng_evaluator_sets_v3.json` is built from `p2pu_v3_eng_*_cap200.json`). | DECISIONS 2026-09-25 ("P2P-U V2 … freeze"); `WP2_DEV_P2P_PHASE_A_STOP_REPORT` §23 records that V1 was STOPPED as infeasible. The 26 tasks have **132,213** raw candidates, which is about **70 h** at the measured V3 rate, and arg lists of 12k nodes risk exceeding ARG_MAX. The Pilot instrument would also differ from the one validated in Smoke. |
| D2 | SD | Readiness leaves out the frozen per-task **gold / empty E2E check** from M14A.S0.A1. | The candidate derives sets from C4 only. It never checks that parent + test patch + gold diff rebuilds the target tree, passes F2P and keeps preservation, or that the empty diff fails F2P. |
| D3 | SD | Infrastructure failures become **membership evidence**. C4 `ERROR`/`CLOCK_BLOCKED`, a P2P-U environment failure and a single-attempt P2P-U run all mark the task not-ready, which triggers reserve replacement. That consumes protected-pool membership on infrastructure noise, the same class of error as 429 → GENERATION_FAIL. | `run_one`: `reasons.append('C4_'+status)` and `'P2PU_ENV_FAIL'`. |
| D4 | ID | **Every loop phase crashes the controller.** `progress` is a string, but the controller indexes `spec["glob"]`. | Reproduced: `TypeError: string indices must be integers` in P02, P09 and P12. The result is an uncaught exception with no STOP report and no LIGHT. |
| D5 | ID | Two hazards in the frozen evaluator are not guarded. (a) An empty group (a task whose P2P-U is undefined) passes an empty `"${NODES[@]}"`, so pytest collects the **whole suite** ×3. (b) A container failure turns into missing JUnit, which becomes a **silent scientific FAIL**. | `evaluate.py::evaluate_state` never checks the container return code. Smoke never had an empty group, but Pilot-A can. |
| D6 | ID | A corrupt committed evaluation record is re-evaluated and overwritten silently. It should STOP. | `evaluate`: `if valid_eval(p): continue`; otherwise the record is recomputed. |
| D7 | ID | The LIGHT include order puts `research/wp2/pilot_a_v1/**` (JUnit, caches) first under the 45 MB cap, so the final result document can be dropped. | `light_profile_m14a.json` |
| D8 | ID | The M13 freeze is checked with raw hashes, not CRLF-normalized ones, so it breaks on a Windows autocrlf checkout. The authorization is not bound to the frozen M13B template and is not self-hashed. | `guard()` / `validate_auth()` |
| D9 | ID | The 22 tests grep source text. None of them runs the controller loop, readiness, the driver, authorization or the summary, so D4 passed as 22/22. | `test_m14a_offline.py` |

## The candidate's readiness definition

The candidate defines readiness as C4 DONE + non-empty behavioral F2P + at least one preservation family. This is **not exactly** the frozen semantics. It matches the "P2P defined" clause, but it omits "gold diff must PASS F2P; empty must FAIL F2P", and its P2P-U family is built with the wrong rule (D1).

The minimal correction, implemented in this kit:

**ready ⇔**
- C4 DONE, **and**
- behavioral F2P ≠ ∅, **and**
- (P2P-S ≠ ∅ **or** P2P-U V3 cap200-stable ≠ ∅), **and**
- the gold diff rebuilds the target tree, passes F2P, and gives P2P-S and P2P-U200 ∈ {PASS, UNDEFINED}, **and**
- the empty diff fails F2P, and gives P2P-S and P2P-U200 ∈ {PASS, UNDEFINED}.

These are the Smoke positive and negative canary criteria, applied per task. A lock-exact install block is retried once and then accepted as task-specific. Every other environment failure STOPs as READINESS_ENV_FAIL (resumable, no record written).

## Kept from the candidate

These parts were verified correct and are kept:

- **Controller v2.2.4:** byte-identical. It pushes the exact tag, includes the STOP log tail, runs a LIGHT on STOP, and persists `complete=true` before the final commit, tag and LIGHT.
- **Authorization:** a new committed `human_authorization.json` rather than mutating the frozen template. The corrected kit also binds the template hash and self-hashes the file.
- **Generation:** cache namespace `(task_id, arm, replicate)`; v2.2 transport and circuit breaker; outage becomes pending, never an outcome.
- **Order and identity:** outcome-blind order (generation freeze, then tag, then evaluation); `(task_id, full diff_sha256)` identity.
- **Gates and cost:** the A0–A5 logic reuses `gates_for(n)`, and fresh cost and tokens come from the ledger.
- **Canary:** the ENG canary is redirected to the Pilot root.

## Runtime estimate from repository measurements

| Stage | Basis | Estimate |
|---|---|---|
| Readiness, 26 tasks | C4 V3 median 258 s (max 747); V3 rediscovery about 1–4 min; V3 cap200 unit median 382 s (max 638); gold + empty = 2 × 4.14 min | ≈ 22 min/task, **7–14 h** total (central about 10 h) |
| The same with the candidate's V1 full-candidate rule | 132,213 nodes at the V3 per-node rate | **≈ 70 h for P2P-U alone** |
| Canary | Smoke P03 | about 7 min |
| Generation, 48 episodes | Smoke: 62 episodes in about 20 min | **15–25 min** |
| Evaluation, ≤48 identities | Smoke: 44 identities in 3 h 02 m | **2.5–3.5 h** |

## Remaining limitations (not blocking)

- **Could not run here:** Docker, WSL and the model path, so the heavy steps are unit-tested with fakes. Real-module imports and signatures were checked, and so was `guard()` against the real M13B artifacts.
- **Frozen evaluator `score()`:** it reports an empty P2P set as PASS rather than UNDEFINED in the descriptive counts. RESOLVED is unaffected, and the evaluator is left frozen.
- **Portability:** cross-machine portability checks are deferred, as agreed.
