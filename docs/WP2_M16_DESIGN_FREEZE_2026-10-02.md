# WP2 M16 OPWS-MAIN — design freeze (candidate until installed)

- **Machine-readable record:** `research/wp2/m16_v1/m16_design_freeze_v1.json`. Its `artifact_sha256` is pinned in `scripts/wp2_m16_run.py`.
- **Approved design:** Review Package v2 (`docs/WP2_M16_OPWS_MAIN_REVIEW_PACKAGE_v2_2026-10-02.md`), plus the reviewer's settlement of R1, R2, S1 and S3 on 2026-10-02.
- **Status:** candidate. It becomes frozen when the installer commits it, tags `wp2-m16-v1-kit-2026-10-02` and pushes it.
- **Model API calls:** zero in every phase.

## 1. Decisions implemented

| Item | Decision | Where |
|---|---|---|
| Q1 | Formal quarantine amendment `M16/L-OPWS` before any run | `m16_l_opws_quarantine_amendment.json` (full text, self-hashed, design-pinned, in the kit tag); DECISIONS.md entry |
| Q2 | Route B: V3 eligibility on all 220 frozen changed-test-evidence tasks, then selector-blind readiness, then the full READY census | Q03–Q07 |
| Q3 | P2P-S + P2P-U200 both in `OPWS_ROBUST` | §4 |
| Q4 | `OPWS_ROBUST` is primary. δ = θ_RMCSS − θ_AGENT_MAIN, estimated with the Tango 95% CI. Newcombe-10 is the sensitivity interval; exact and mid-p McNemar are supporting tests. No NI/equivalence margin; ±0.10 is descriptive only | `wp2_m16_stats.py`, §6 |
| R1 | Versioned M16 repetition-retaining wrapper around the **unchanged** frozen `run_state_v3` and the frozen classifier. Historical ENG/M14R/M15-R are not touched or re-interpreted | `wp2_m16_r1.py`, `m16_r1_repetition_amendment.json` |
| R2 | MAIN input adapter (commits, era, locked dev/test closure, P2P-U inventory), fail-closed | `wp2_m16_adapter.py`, Q02 / R02 |
| S1 | WSL/Docker/VHDX stay on C: (SSD). `D:\wp2_cold` holds only cold mirrors of pushed freezes, LIGHT backups and verified cold caches. WARN < 25 GiB, HOLD < 20 GiB, plus a projected-headroom gate before Q03 | `wp2_m16_resource.py`, R05, Q01 |
| S3 | Conditional maintenance: frozen inventory, then an explicit allow-list, deleted one volume at a time. Never a prune. Compaction instructions come from a capability probe, and a human runs them | `wp2_m16_maint.py`, S3 mission |

## 2. Population, stage by stage

| Stage | Definition | Artifact |
|---|---|---|
| Available | 297 MAIN tasks with the frozen RM-CSS selection (WP1a) and the Agent main run (WP1b). Agent r1–r3 exist only for the 15-task variance subset | WP1 artifacts (pinned; opened only from Q08) |
| Frame | The 220 tasks of `wp2_oracle_confirmation_selection_2026-09-22.json` (`FROZEN_BEFORE_ORACLE_EXECUTION`) | adapter `frame_220` |
| Eligible | Status `DONE` and `PRIMARY_BEHAVIORAL_F2P_ELIGIBLE` under harness V3 + R1 + R2 | `m16_v3_eligibility.json` (tag `wp2-m16-v1-eligibility`) |
| Evaluable | READY: valid empty-diff negative control **and** scoped-gold positive `RESOLVED_ROBUST` | `m16_ready_membership.json` (tag `wp2-m16-v1-ready`) |
| Sampled | All READY tasks (a census) | same |

## 3. Frozen rules (exact)

### 3.1 Eligibility (Q03/Q04)

The procedure is the frozen `phase5.run_task`. The only differences are:

- inputs come through R2;
- the R1 wrapper retains the per-repetition outcomes;
- the output is written under `research/wp2/m16_v1/oracle/`.

Details:

- **Test files:** frozen `changed_test_files`.
- **States:** parent = parent + the frozen test patch; target = target.
- **Execution:** one container per state through the frozen `run_state_v3` (lock-first install; `nofile` 65536; fresh DB; 3 repetitions per file).
- **Classification:** frozen `classify_node_v2` (FLAKY > TARGET_ORACLE_INVALID > P2P_ONLY > PARENT_COLLECTION_ERROR > SYMBOL_ABSENCE_F2P > BEHAVIORAL_F2P > OTHER_REVIEW_REQUIRED), followed by `task_eligibility_v2(environment_valid=True, task_collection_failure=False)` exactly as frozen.

Status mapping:

| Status | Rule |
|---|---|
| `ENV_INSTALL_BLOCKED` | Frozen `INSTALL_FAIL` on 2 consecutive attempts |
| Infrastructure | Container incomplete (no `ALL_RUNS_DONE` and no install marker), a script-write failure, or a JUnit parse error. Retried. After 3 attempts spanning ≥ 2 engine invocations (each infra STOP 79 ends the engine process and the controller run) it becomes `ORACLE_INFRA_UNRESOLVED` (ineligible, listed) |
| `CLOCK_BLOCKED` | Resumable STOP; no attempt is consumed |
| JUnit file missing although the container finished | Keeps the frozen pseudo-node semantics (a deterministic state outcome) |

V4 check: `eligibility-verify` re-derives every class from the stored per-repetition evidence.

### 3.2 R1 — repetition retention

- The frozen `run_state_v3` is called **unchanged**, using its own `raw_junit_dir` argument.
- The per-repetition files are parsed by the frozen parser into per-node lists `[r0, r1, r2]`:
  - a node absent in a repetition gets `"missing"`;
  - a missing file gives the frozen pseudo-node `<file> = "error"` for that repetition.
- Failure texts and node membership are the frozen merged values.
- The classification loop is a verbatim copy of `phase5.run_task`.
- Tests (run against the real frozen functions, with in-memory IO):
  - identical triples reproduce `phase5.run_task` byte for byte;
  - PPF, PFP and FPP on either state reach FLAKY;
  - the frozen path saw only the last repetition.

### 3.3 P2P-S and P2P-U200 (Q05A/Q05B)

- **P2P-S:** the P2P_ONLY nodes of the R1 oracle (stable PASS 3/3 on both states).
- **P2P-U200:**
  - Start from the frozen MAIN unchanged-test inventory (`associated_unchanged_test_files`).
  - Run the frozen `ensure_discovery` / `rediscover_v3`: collect-only at the target under V3, over `.py` files only, excluding conftest, `__init__` and bracketed paths.
  - Apply the frozen v2 selection rule (`rule_sha256 78a089bb…`, salt `wp2-p2p-u-v2-2026-09-25`, cap 200, composition 150/50, `P,P,P,D` order).
  - Run the frozen `execute_cap` (3 parent + 3 target repetitions, taxonomy FLAKY > COLLECTION_ERROR > STABLE_P2P > …).
  - The set is the STABLE_P2P nodes.
- **Redirection:** the frozen module's `OUT_ROOT` points to `research/wp2/m16_v1/evalsets/p2pu/`, so nothing is ever written under the historical directory.
- **Infrastructure:** a rediscovery container rc ≠ 0, `ENV_FAIL_P2PU` or `INTEGRITY_FAIL` is infrastructure. After 3 attempts the task is `NOT_READY_EVALUATOR_SET_INFRA_UNRESOLVED` and is listed.
- **Empty sets:** an empty set is `UNDEFINED`, which counts as passing for `resolved`. Tasks with an `UNDEFINED` P2P-S or P2P-U200 are listed in `m16_evalsets_freeze.json`.

### 3.4 Readiness (Q06/Q07)

This is M15-R `readiness_task` semantics with the MAIN V3 sets.

- **Negative control** (empty diff, frozen `evaluate_state_safe`): valid iff strict F2P is `FAIL` **and** robust P2P-S and P2P-U200 are each `PASS` or `UNDEFINED`.
- **Positive control:** the gold non-test diff restricted to the GOLD_HARD editable set (D35), evaluated with E1 + E1A1 and `parent_starts_ok=True`.
- **Decision:** `decide_ready` is a pure function. Outcomes: READY or one of `NOT_READY_{NEGATIVE_CONTROL_INVALID, EMPTY_SCOPED_GOLD, SCOPED_GOLD_DOES_NOT_APPLY, SCOPED_GOLD_NOT_RESOLVED, INFRA_UNRESOLVED}`.
- **V3 check:** `ready-verify` recomputes every score from the stored groups.
- **Pool gate:** n_READY < 40 means descriptive only.
- **GOLD-only scope adapter:** the gold side uses only `gold_raw_scope` + `editable_filter`. The selector branches of `build_arm_scopes` are never called before Q08.

### 3.5 OPWS (Q08–Q10)

- **Editable sets:** the frozen D35 `editable_filter`, applied to:
  - RMCSS: `rmcss_predicted_set`;
  - AGENT_MAIN: WP1b main-run `selected_paths`;
  - AGENT_r1..r3: variance runs, overlap tasks only.
- **G_raw:** frozen `gold_raw_scope` (M/D non-test files; renamed, added, type-changed and copied files are excluded).
- **P_S:** the restricted gold diff over editable_S ∩ G_raw.
- **Coverage and routing:**

  | Coverage | Condition | Treatment |
  |---|---|---|
  | NONE | P_S is empty | FAIL by construction |
  | FULL | P_S identity equals the readiness scoped gold | Readiness positive reused |
  | PARTIAL | Otherwise (this also includes supersets of a budget-truncated scoped gold) | Evaluated with the frozen evaluator + E1 + E1A1 |

- **OPWS_ROBUST** = `wp2_m14r_core.score_robust(...).resolved`: every behavioral F2P node passes 3/3, and no P2P-S or P2P-U200 node is non-passing in ≥ 2 of 3 repetitions (or has fewer than 2 outcomes). An empty set is `UNDEFINED`, which counts as passing.
- **OPWS_STRICT** = `score_strict(...).resolved`.
- **GOLD invariant:** GOLD = 1 on every task. A violation is `M16_STOP_GOLD_IDENTITY`.

### 3.6 Infrastructure and listwise rule

- A resumable STOP is retried on the same identity and is never scored.
- After 3 attempts spanning ≥ 2 engine invocations the identity is `INFRA_UNRESOLVED`.
- Its task is dropped **listwise** from every analysis (RMCSS, AGENT_MAIN, r1–r3, GOLD).
- Adversarial bounds (drops imputed both ways) are always reported.
- Drops > 10% of READY give `M16_INSTRUMENT_REVIEW`.
- An unclassified startup failure (not covered by E1/E1A1) is a STOP for an amendment. The amendment may only map INFRA → FAIL, must be selector-agnostic, and must be committed, tagged and pushed. Amended items above 10% give `M16_INSTRUMENT_REVIEW`.

## 4. Proof: scope materialization happens only after a unique, pushed READY tag

### P — runtime enforcement

| Check | What it enforces |
|---|---|
| P1 | `scopes` first calls `ready_pushed()`. That requires exactly one local and one origin tag matching `wp2-m16-v1-ready*`, the origin object equal to the local object, `m16_ready_membership.json` + evaluator sets + eligibility present in the tag byte-for-byte, the tag commit an ancestor of HEAD, and ancestry kit → dryrun → eligibility → evalsets → READY (each tag also unique and on origin). Any failure is exit 37 (STOP `M16_TAG_GATE`) |
| P2 | The OPWS plan records the READY tag, its commit, its tag objects and the `ls-remote` output at Q08. Q08V, every Q09 invocation and Q11 re-check these against origin |
| P3 | Every selector-blind process installs an audit-hook firewall that refuses (a) `open()` of the WP1 selector files, the Agent run directories, the census selector-metadata file, `scopes/`/`opws/` and any copy of them anywhere (cold mirror, extractions) or any `.zip` export next to the project; (b) subprocess argv mentioning those paths; (c) non-loopback sockets (AF_UNIX exempt). Q08–Q12 install the network rule only. A violation is exit 36, non-resumable, including one that frozen code swallowed (checked at exit). The engine never spawns a child Python in those phases (static test) |
| P4 | `scopes/` and `opws/` must not exist before Q08 (checked by the guard) |

### V — post-hoc verification (does not require trusting the controller)

| Check | What it verifies |
|---|---|
| V1 | No commit reachable from the READY commit touches `scopes/` or `opws/`, and every commit that does is a descendant of it (`scopes-verify`) |
| V2 | Origin holds the READY tag at the bound commit. Git cannot attest push *time*; P1 enforced it at runtime and P2 recorded the evidence |
| V3 | READY membership is recomputed from the stored readiness evidence. Each readiness attempt is logged append-only |
| V4 | Eligibility is recomputed from the stored per-repetition oracle evidence |

**Residual risk.** No software check can exclude an out-of-band human computation. V3 and V4 neutralise its consequence: membership is a deterministic function of selector-blind evidence, and that evidence is hash-pinned, tagged and pushed.

## 5. No-API guarantee (verifiable)

- No M16 module imports a model client or HTTP library. This is checked statically.
- Provider credential variables are removed from every engine process.
- The firewall refuses every non-loopback Python socket in every M16 engine process (full hook in selector-blind phases, network-only hook in Q08–Q12).
- The design freeze, both amendments, the guard records, the adapter report and the summary carry `model_api_calls: 0`; no M16 code path can make one (static import test + runtime socket hook).
- No ledger or authorization step exists, because nothing is paid.

## 6. Tokens and claims

The run reports these fields:

- **`run_status`** (exactly one, by precedence): STOP > `M16_INSTRUMENT_REVIEW` > `M16_POOL_INSUFFICIENT_DESCRIPTIVE_ONLY` > `M16_OPWS_COMPLETE`.
- **`ci_position`**: `DIFFERENCE_CI_EXCLUDES_ZERO_POSITIVE`, `DIFFERENCE_CI_EXCLUDES_ZERO_NEGATIVE` or `DIFFERENCE_CI_INCLUDES_ZERO`.
- **`band_position`**: `CI_INSIDE_DESCRIPTIVE_BAND`, `CI_CROSSES_BAND_EDGE`, `CI_WIDER_THAN_BAND` or `CI_OUTSIDE_BAND`. The four values are exhaustive and exclusive (unit-tested).
- **`method_agreement`**: `CONCORDANT` or `DISCORDANT`.

The last three are issued only with `M16_OPWS_COMPLETE`. The run never issues a winner, non-inferiority or equivalence label.

Claims are generated from frozen templates. Each one includes the mandatory scope sentence and passes a forbidden-wording check. The only permitted negations are "does not show … equivalent" and "not a non-inferiority or equivalence margin".

## 7. Resources

### Storage gate

- **Dry-run:** 3 tasks, one per era, chosen as the minimum of sha256(`wp2-m16-dryrun-v1-2026-10-02|task_id`) over the frozen frame, using era only. The selection is selector-blind:

  | Era | Task |
  |---|---|
  | py38 | `saleor-rc-99041211cf9e` |
  | py39 | `saleor-rc-c6220233ccb1` |
  | py312 | `saleor-rc-eb61406cecc5` |

- **What it measures:** per state, consumption = max(VHDX allocated growth, C: free drop, in-guest used-bytes delta); C: free, uv-cache bytes, Docker disk usage, wall time, transient leftovers, closure mechanism and install status.
- **Projection:** `new lock sets × g_cold + all containers (upper bound 2,019) × g_warm + evidence + 2 GiB`.
- **Gate:**
  - Route B starts only if the projected C: free at the end of Q09 is ≥ 25 GiB.
  - Otherwise S3 runs and the gate is re-run.
  - Q01 re-checks the gate against the current free space.
- The dry-run evidence is **not** reused by Q03.

### Time and load

| Item | Estimate |
|---|---|
| Docker time, central | ≈ 42–63 h (Review v2) |
| Wall time | 3–4 days |
| Docker concurrency | One era container at a time, plus `wp2-pg` |
| Other controllers | None run concurrently |

## 8. Deviations from Review v2 (please confirm)

1. When JUnit is missing but the container finished, the frozen pseudo-node semantics apply. Review v2 called this infrastructure.
2. A JUnit parse error, and a P2P-U rediscovery rc ≠ 0, count as infrastructure. This is detection only.
3. `INFRA_UNRESOLVED` needs 3 attempts across ≥ 2 engine invocations, so a host outage cannot drop tasks.
4. `CLOCK_BLOCKED` does not consume attempts.
5. **O3 (added-file allowance sensitivity) is not implemented in this kit.** It needs extra Docker evaluations and is listed as open.
6. Dry-run oracle evidence is not reused.
7. The shadow root for R2 is regenerated deterministically under `_workspace/tmp/`. It is hash-pinned in the adapter report, not committed, because it is 41 MB.
8. Pins are LF-normalised SHA-256 (CRLF-insensitive). The raw-byte hashes in Review v2 §11 refer to the Windows bytes.

## 9. Historical disclosure (thesis/report)

Historical ENG V3 oracle construction, as used by M14R and M15-R, collapsed the three repetitions to the last one. It is not recomputed or re-interpreted. Only M16 uses R1.
