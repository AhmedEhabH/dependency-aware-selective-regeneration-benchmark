# TODO

> **CURRENT BOARD (2026-08-24).** Authoritative snapshot:
> `docs/AI_ACCOUNT_TRANSFER_HANDOFF.md`. Everything below the board is the
> historical task ledger (valuable history — do not delete; headings marked
> HISTORICAL are superseded and never override the board).

| # | Item | Status |
|---|---|---|
| 1 | **v0.9.22 CANDIDATE — long-context attention memory closure** on branch `fix/pilot-v0922-long-context-attention-memory-closure`: Task A `attn_implementation="sdpa"` at from_pretrained, Task B fail-closed CUDA generation inside `sdpa_kernel([FLASH_ATTENTION, EFFICIENT_ATTENTION])`, Task C canonical attention evidence + fail-closed `attention_policy` check + launch authorization enforcement, Task D corrected OOM diagnosis (long-prompt OOM reports prompt-prefill evidence, never advises completion-cap reduction), Tasks E/F regression-guard prior memory fixes + unchanged 12000/64 gate; RED/GREEN proven (12 backend + 18 preflight contract tests failed against v0.9.21); full suite 2407 passed / 33 skipped / 0 failed; dry-run pilot 48/48 | DONE |
| 2 | **RELEASED `v0.9.21-pilot-exec-ready`** @ annotated tag peel == artifact source commit == merge `e308047c9c05f38316d80ce565bac1b51d105bfa`; archive SHA-256 `62e377467e225d336cbcaa70a2c610b5080e329e1a4e6578fbcbdc1af7dbee40`; trust/provenance 0 mismatches; target-shaped Gates 1-3 + full preflight GREEN (runs 32692489617 / 32694137255); dry-run 48/48 — **Real Pilot rejected before launch at the real 12k attention-prefill OOM; repository/per-cell fixes remain valid and carried forward** | DONE |
| 3 | Per-cell validation runtime closure: B1 explicit --validation-python routing (no sys.executable fallback), B2 frozen env into FunctionalValidator, B3 explicit --validation-timeout 1800 on launch+resume; RED/GREEN recorded | DONE |
| 4 | Phase 2 release mechanics: non-ff merge branch → main `4827045fce96eb4caa3645e3cf3c8434dca2a1a8` (pushed); anchors frozen for planned `v0.9.22-pilot-exec-ready` via two-pass finalizer + `--verify-source-provenance` (0 mismatches, `reports/pilot_notebook_trust_freeze.json`); exact candidate artifact built from the merge commit — SHA-256 `9182ea2bb091f785ff325a1355caa5bb0f57283764215059092970bbd8014974` (+ sidecar verified); exact-artifact dry-run 48/48 / 48 unique IDs / 0 model calls / 0 tokens. **The stable tag was NOT created** | DONE |
| 4b | **Candidate consistency closure (PILOT-EXEC-01)**: four stale v0.9.21 release-test constants aligned to `v0.9.22-pilot-exec-ready`; order-independent missing-SDPA-API test isolation (pre-populated `torch.nn.attention` regression condition, RED/GREEN proven); untracked generated dry-run dirs removed; full suite **2407 passed / 33 skipped / 0 failed** (2440 collected, expanded-artifact simulation re-enabled and passing); non-ff merge → main `ba08392552545baa15c10ae5db2e95ce7496a720` (pushed); anchors re-frozen at the new merge via two-pass finalizer + `--verify-source-provenance` (0 mismatches); exact candidate artifact rebuilt — SHA-256 `3fd986262936972a6f12adbae21e844adef488dfd76ef0e4b2e6e434b2aa65b3` (+ sidecar verified); exact-artifact dry-run 48/48 with the new source commit in every record. NO scientific/runtime code delta | DONE |
| 5 | Fresh Kaggle v0.9.22 candidate model preflight ONLY (repo preflight PASS, Qwen 14B BNB-NF4 load PASS, short probe PASS, **12k probe PASS with attention policy evidence**) using the exact candidate artifact (`3fd98626…`); no 48-cell launch while untagged | **NEXT ACTION** |
| 6 | If Kaggle 12k probe PASSES: annotate `v0.9.22-pilot-exec-ready` at the tested merge commit `ba08392552545baa15c10ae5db2e95ce7496a720`, push tag, update docs; if it FAILS: return to the SAME v0.9.22 task (never spawn v0.9.23) | PENDING (gated on #5) |
| 7 | Launch accepted 48-cell Pilot in a fresh session after the stable tag exists and all target gates pass | PENDING (gated on #6) |

Frozen matrix reminder: Qwen2.5-Coder-14B-Instruct / bnb-nf4 / 600 s uniform
timeout / 12 scenarios / 2 strategies / 2 repetitions = 48 cells.

---

## HISTORICAL LEDGER (superseded task history — read-only)

## Historical - PILOT-EXEC-01 (2026-08-13, KAGGLE SERVICE BOOTSTRAP LAST-MILE CORRECTION)

### PILOT-EXEC-01 - Pilot freeze and execution
- **Priority:** HIGH
- **Category:** Scientific Evidence
- **Description:** The authorized task after PILOT-READY-01 CLOSED. Frozen Pilot matrix: model Qwen2.5-Coder-14B-Instruct, quantization bnb-nf4, timeout 600s uniform, 12 scenarios, 2 strategies (iterative_repository_agent, selective), 2 repetitions = 48 cells; repositories Todo / django CMS / Saleor. Do NOT raise the timeout above 600. **Last-mile correction COMPLETE + MERGED + TAGGED `v0.9.3-pilot-exec-ready` (2026-08-13, branch `fix/pilot-kaggle-service-bootstrap`):** the frozen Pilot notebook (`notebooks/pilot_exec_01.ipynb`) now includes a fail-closed, idempotent `service-bootstrap-cell` that provisions the Saleor validation OS services on a fresh Kaggle session — PostgreSQL `127.0.0.1:5433` (role/db `saleor/saleor@saleor`, private data dir under `/kaggle/working/pilot_services/postgres`, prefer `pg_config --bindir`) and Valkey/Redis `127.0.0.1:6379` (persistence disabled) — placed between repository snapshot verification and the repo-specific preflight, i.e. BEFORE any repository validation or model load. Topology mirrors `benchmark_data/manifests/pilot_validation_commands.yaml`. OS install is non-interactive via apt-get and fails loudly if Internet is unavailable; no benchmark/model Python environment modification; no secrets printed beyond the frozen non-secret test credentials. **No scientific inputs changed** (scenarios, prompts, metrics, model, quantization, timeout 600, repair budget, repository pins, validation scope). Gates: notebook contract 20/20 (incl. 5 new service-bootstrap tests), deployment bundle contract 14/14, targeted pilot gates 77/77, full suite **2,098 passed / 33 skipped / 0 failed**, `git diff --check`/ruff/mypy/compile clean. Bundle rebuilt from the exact tagged source: `dist/pilot-kaggle-upload.zip` + `dist/pilot-kaggle-upload.zip.sha256` (authoritative frozen upload artifacts; do NOT manually re-zip). **Remaining: exact Kaggle launch prep (upload zip + sidecar as ONE Dataset, attach Pilot notebook + Qwen 14B, Internet ON, HF_TOKEN) -> target preflight -> real Pilot (ONLY after all preflights pass). Pilot = NOT STARTED** (real launch deferred until the researcher confirms the actual Kaggle mounted model path and HF results repository ID). Historical execution-ready point before this correction: `v0.9.2-pilot-exec-ready` @ `e030be5` (immutable, NOT moved).
- **Status:** IN PROGRESS (Pilot execution NOT STARTED; deployment + pre-execution gates COMPLETE)

## Previous - PILOT-READY-01 (CLOSED, 2026-08-10)

### PILOT-READY-01 - Prepare repository for Pilot readiness (docs/config/path reconciliation)
- **Priority:** HIGH
- **Category:** Documentation / Readiness
- **Description:** The Pilot readiness closure is COMPLETE. Scientific Smoke V2 = COMPLETE AND ACCEPTED; MAIN-GREEN-01 = CLOSED; HANDOFF-CONSISTENCY-01 = CLOSED. Branch `feat/pilot-ready-01`; code/test commit `34ecf78` (fix(pilot): close multi-repo selective input contracts, pushed, local = remote). Fixed the selective arm's repository-level input contracts (per-repository dependency graphs via `build_repository_dependency_graphs`, per-repository editable universes, file-granular descriptors for django CMS/Saleor), corrected the stale real-smoke expectation (`STRATEGIES_WITH_MISSING_PREREQS = {"agent"}`), added the focused multi-repo production-path contract (`tests/integration/test_pilot_multi_repo_production_path.py`, 12 tests). Gates: unit contract 14 passed; real-smoke 9 passed; production-path 12 passed (twice); `git diff --check`/compile/ruff/mypy clean (feature-caused only); exact fresh 48-cell Pilot dry-run 48/48 succeeded / 0 failed / 0 pending (deterministic unique run IDs, config_hash `7ef6ffc7a2c0d369`, source_commit `34ecf78`, per-repo 16/16/16, per-strategy 24/24, per-rep 24/24, checkpoint completed, no residue); isolation/evidence/export gates 142 passed; final full suite **2,026 passed / 33 skipped / 0 failed**. Per-run workflow timeout stays frozen at 600 s uniformly; no further Kaggle Full-9 authorized. **Pilot execution NOT STARTED; next = `PILOT-EXEC-01`; stable tag `v0.9.0-pilot-ready` after main merge.**
- **Status:** CLOSED (2026-08-10)

## Previous - Scientific Smoke V2 Closure (SMOKE-V2-CLOSE-01, 2026-08-09) — HISTORICAL SNAPSHOT

### SMOKE-V2-CLOSE-01 - Close Scientific Smoke V2 permanently (docs/results closure)
- **Priority:** HIGH
- **Category:** Documentation / Milestone Closure
- **Description:** Scientific Smoke V2 is complete and accepted: the accepted clean 300-second Full-9 baseline and the accepted 600-second confirmatory Full-9 (`exp-20260808-222843`, uniform `--timeout 600`, 9/9 terminal / 2 successes / 7 scientific failures / 0 engineering blockers / 0 budget-exhausted / 63 model calls / 77,929 tokens / max run ≈373 s, same 2/9 result, timeout sensitivity confirmed, NOT an improvement claim). Freeze per-run workflow timeout = 600s uniformly. Close the milestone: update all authoritative docs (SYSTEM_STATE.md, README.md, TODO.md, START_HERE.md, PROJECT_HANDOFF.md, MASTER_IMPLEMENTATION_PLAN.md, runbook, reports, ledgers, debt schedule) to the accepted state; audit the closure; commit/push (prove local = remote); non-fast-forward merge to main; create/push stable tag `v0.8.0-smoke-v2-complete`; leave the repo ready for a weaker AI to continue directly with `PILOT-READY-01` (do NOT start Pilot). **HISTORICAL (planned next action at the time, since completed): independent delta audit of this closure; after acceptance, main merge + stable tag, then `PILOT-READY-01`.**
- **Status:** CLOSED (2026-08-09) — milestone closed; docs merged to main; stable tag `v0.8.0-smoke-v2-complete` created at `193d889`; post-merge regression hotfix MAIN-GREEN-01 CLOSED; preferred recovery tag `v0.8.1-smoke-v2-complete` at main `d875c72`; next = `PILOT-READY-01` (see Current section)

## Previous - Full-9 Workspace Isolation Closure (2026-08-08)

### FULL9-T600-01 - 600s Confirmatory Timeout-Sensitivity Full-9 Contract (executable + docs closure)
- **Priority:** HIGH
- **Category:** Scientific Evidence / Documentation
- **Description:** The accepted clean 300-second Full-9 baseline (runtime source/build `7f2a450`, `--timeout 300`) showed three runs at or beyond the scientific per-run workflow ceiling (~307–337 s). To reduce timeout censoring while preserving equal computational opportunity across strategies, the uniform scientific per-run workflow timeout was raised **300 → 600** for ONE confirmatory Full-9 (T600). **The 300-second baseline remains valid and preserved** (9/9 terminal / 2 successes / 7 scientific failures / 0 engineering blockers); **T600 was EXECUTED AND ACCEPTED** — run `exp-20260808-222843`, uniform `--timeout 600` on frozen runtime source/build `7f2a450`, fail-closed `_t600` output namespace, evidence prefix `corrected-full9-t600-wsfix-7f2a450-`: **9/9 terminal / 2 successes / 7 scientific failures / 0 engineering blockers / 0 budget-exhausted / 63 model calls / 77,929 tokens / max run ≈373 s / Full-9 verification PASS / HF synchronization PASS** — the **same 2/9 result** as the accepted 300-second baseline. **Timeout sensitivity confirmed: the 600-second ceiling did NOT change the accepted result; the 300-second baseline signal was not distorted by timeout censoring. This is NOT an improvement claim.** The 600s timeout applies uniformly to monolithic / selective / iterative_repository_agent (one shared Full-9 command; no strategy receives extra time); the uniform per-run workflow timeout is now frozen at **600s**. **Do NOT raise the timeout above 600** — if Pilot runs accumulate near 600 s, analyze the duration/repair distribution and pre-register the Pilot budget instead. New fail-closed output namespace `/kaggle/working/runs/qwen14b_bnb_nf4_full9_scientific_smoke_wsfix_7f2a450_t600`; evidence archive prefix `corrected-full9-t600-wsfix-7f2a450-`. Executable commit `e6dbd3e` `chore(smoke): raise confirmatory Full-9 timeout to 600s` (5 files: canonical + bundled notebook, notebook_manifest.json, tests/integration/test_kaggle_bundle_smoke_v2_preflight.py, tests/unit/test_cli.py), pushed, local = remote. Pre-benchmark validation recorded at contract time: Dataset PASS/carried-forward (zero drift); Prompt PASS/carried-forward (zero drift); Pipeline Smoke PASS (T600 command + fail-closed `_t600` namespace contract); Dry Run PASS (exact 3x3 no-model/bundled dry-run contract with scientific timeout 600); Integration Test PASS (final executable full suite **1947 passed / 33 skipped / 0 failed**); Metric Verification PASS/carried-forward (zero metric/evaluator drift). Audit: executable implementation PASS; over-engineering PASS (one protocol value, one isolated namespace, contract tests only); scientific identity PASS (runtime source/build remains the frozen `7f2a450` deployment identity — runtime source did not change). Non-destructive RED proof: committed HEAD notebook (`--timeout 300`) FAILS the new 600-second contract; working notebook satisfies it. **Task CLOSED (SMOKE-V2-CLOSE-01).** HISTORICAL (completed): the next authorized action at the time was an independent delta audit of the Scientific Smoke V2 closure, then main merge + stable tag `v0.8.0-smoke-v2-complete`, then `PILOT-READY-01` — all executed (closure audited and merged `193d889`; stable tag created; MAIN-GREEN-01 merged `d875c72`; preferred recovery `v0.8.1-smoke-v2-complete`). Pilot execution is NOT STARTED; fine-tune unauthorized. The accepted T600 run is the final Smoke evidence; no further Kaggle Full-9 authorized.
- **Status:** CLOSED (2026-08-09) — EXECUTED, ACCEPTED (SMOKE-V2-CLOSE-01 CLOSED); Scientific Smoke V2 milestone complete; main merged at `d875c72`; preferred recovery tag `v0.8.1-smoke-v2-complete`

### FULL9-EXEC-01 - Canonical Corrected Full-9 Notebook Execution Closure (runtime/fix)
- **Priority:** HIGH
- **Category:** Runtime / Execution Artifact
- **Description:** The canonical Kaggle notebook is now the single, tested, fail-closed execution artifact for exactly one fresh corrected Full-9. Fixed the F9 bootstrap runtime regression in the canonical `notebooks/seven_arm_benchmark.ipynb` setup-cell: `src_dir` guard + `sys.path.insert` after assignment; `MODEL_CANDIDATES` initialized from `KNOWN_MODEL` with `MODEL_PATH` derived from it (the previously deleted `MODEL_DIR` NameError — old code `MODEL_DIR = MODEL_PATH.parent` referenced an undefined name — is fixed); `SCRIPT_PATH.is_file()` guard. Removed all stale execution routes: setup order = setup-cell → install-lock-cell → preflight-cell → secrets-cell → full9-execution-cell → full9-verification-cell → export-evidence-cell; no generic/canary/continuous cells. Latest Kaggle attempt truth: source/build `7f2a450`; runtime install/preflight PASS; a redundant corrected-source selective canary ran and succeeded — **that attempt is NOT a Full-9**; corrected Full-9 evidence remained **0/9** at that time; the evidence ZIP downloaded from that session must NOT be labeled accepted Full-9 evidence. Commit A `c4aee03` `feat(kaggle): make corrected Full-9 notebook executable` (5 files: canonical + bundled notebook, manifest, 2 new F9 preflight tests, pre-existing CLI test), pushed, local = remote, tree clean. Validation: full suite **1,947 passed / 33 skipped / 0 failed**; targeted notebook/CLI/bundle 137 passed; related production-path/isolation regression 45 + 33 passed / 1 skipped; FULL9-EXEC-01 gate set 22 passed; notebook JSON parse OK; all canonical code cells compile; bootstrap symbol-closure clean; bundle rebuilt via `python scripts/build_upload_bundle.py` (exit 0, code/data/notebook parity, no forbidden artifacts); canonical/bundled notebook parity proven; zero data/prompt/metric/runtime drift. **HISTORICAL (superseded by the executed and accepted T600 Full-9): independent delta audit of FULL9-EXEC-01; after acceptance, exactly one fresh corrected Full-9.** Main merge / stable tag / Pilot / fine-tune remain unauthorized; no Kaggle run performed in this task.
- **Status:** COMPLETE (HISTORICAL — superseded by the executed and accepted T600 Full-9, see FULL9-T600-01)


- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Record the rejected Full-9 `exp-20260807-205422` (physically completed 9/9; raw result 2 succeeded / 7 failed; raw total 62 calls / 76,858 tokens; runtime source `f7b1ebb`) and its closure. Full-9 scientific acceptance = **rejected**. Root cause = **overlay source restaging leaked generated files across scenarios** — `_populate_workspace_source` overlaid the snapshot onto reused per-strategy workspaces without deleting stale generated files, so `0004_task_priority.py` from scenario 001 survived into 002 and produced `0005_remove_task_priority_task_deleted_at`; affected direct records = selective/agent 002 and 003. Fix: exact reset from the immutable snapshot before every matrix run — Commit A `7f2a450` (`fix(smoke): reset workspace source before every matrix run`; `_WORKSPACE_INFRASTRUCTURE_DIRS={runs,tmp,snapshots}`, `_reset_workspace_source_from_snapshot` deletes the source tree then restages, `make_isolation` calls it for every arm workspace on every run) + Commit B `e29c017` (`chore(deploy): repin isolated Full-9 Smoke bundle`; `SOURCE_COMMIT=7f2a4509482dc7e62c2b243374592e9a88e2ff48` / `DEPLOYED_BUILD_ID=7f2a450`). Unit edge cases 33 passed / 1 skipped; sequential 001→002→003 migration proof (002 clean, no `0004_task_priority`, depends on canonical `0003`) + nine-run zero-residue matrix proof. Official pre-benchmark gate (pytest 8.4.2): **1,928 passed / 33 skipped / 0 failed**; Dataset 161/1 (27 scenarios unchanged); Prompt 200/12; Pipeline Smoke 45; Dry Run 9/9/9/0 exit 0; Metric 187; ruff 0 new (5 baseline); mypy 0 new (4 baseline); compileall clean; notebooks compile; bundle content-identical (147 files / 969,713 bytes). Isolated canary remains accepted; `v0.8.0-canary.1` unchanged; main merge not authorized; `v0.8.0-smoke-v2-complete` not created; Pilot not authorized. Update README.md, SYSTEM_STATE.md, TODO.md, docs/START_HERE.md, docs/PROJECT_HANDOFF.md, docs/MASTER_IMPLEMENTATION_PLAN.md, reports/latest_phase_report.md, reports/PROJECT_HEALTH_REPORT.md, selective_updates/CHANGE_INDEX.md, selective_updates/metrics/change_metrics.jsonl, selective_updates/records/TECHNICAL-DEBT-AND-REFACTOR-SCHEDULE.md; create `selective_updates/records/FULL9-WORKSPACE-ISOLATION-DEFECT-2026-08-08.md`. Commit exactly `docs(audit): record Full-9 workspace isolation defect`; push; verify clean + local = remote + tag unchanged.
- **Status:** COMPLETE (this documentation commit, pushed)

### FULL9-WS-02A - Fail-Close Corrected Full-9 Launch Instructions (docs/runbook only)
- **Priority:** HIGH
- **Category:** Launch Safety / Documentation
- **Description:** Independent GPT-5.6 Sol audit accepted the runtime workspace-isolation fix but blocked a new Full-9 because the canonical runbook still launched source/build f7b1ebb and did not fail closed on a non-empty local output directory. Correct the runbook to SOURCE_COMMIT=7f2a4509482dc7e62c2b243374592e9a88e2ff48 / DEPLOYED_BUILD_ID=7f2a450; enforce setup -> install-lock -> preflight -> secrets -> Full-9; use /kaggle/working/runs/qwen14b_bnb_nf4_full9_scientific_smoke_wsfix_7f2a450; fail closed if that directory is already non-empty; reconcile current-state docs so the first Full-9 is RUN BUT REJECTED and the fresh corrected Full-9 is NOT YET RUN. No runtime/test/data/prompt/metric/notebook/bundle change. No Kaggle run. After this closure: independent delta audit, then one fresh Full-9 only if accepted.
- **Status:** COMPLETE (HISTORICAL — superseded by the executed and accepted T600 Full-9)

### FULL9-WS-02 - Run One Fresh Full-9 Scientific Smoke V2 (corrected source/build)
- **Priority:** HIGH
- **Category:** Scientific Evidence
- **Description:** The next scientific action, BLOCKED ONLY on the independent delta audit of FULL9-EXEC-01 (canonical corrected Full-9 notebook execution closure, which supersedes the FULL9-WS-02A docs/runbook closure as the execution artifact). After that audit accepts the closure, run one fresh isolated 9-record experiment (3 frozen todo scenarios × 3 strategies × 1 repetition = 9 records) with the corrected deployment source `7f2a4509482dc7e62c2b243374592e9a88e2ff48` / build `7f2a450`, profile `scientific-smoke-v2`, protocol 1.0, into the corrected fail-closed output directory `/kaggle/working/runs/qwen14b_bnb_nf4_full9_scientific_smoke_wsfix_7f2a450`. NEVER resume or reuse the rejected `exp-20260807-205422` records or their contaminated workspaces; never merge the accepted canary `exp-20260807-131819`. After completion: independent results audit. No merge/tag/Pilot/fine-tune.
- **Status:** COMPLETE (superseded by FULL9-T600-01; the fresh Full-9 was executed and accepted as `exp-20260808-222843` — the T600 contract — and is the final Smoke evidence)

### QSC-01 - Record Accepted Qwen 14B Selective Canary Success (docs only)
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Independent GPT-5.6 Thinking audit **ACCEPTED SUCCESSFUL REAL CANARY** (2026-08-07, documentation HEAD `5561f918`). Record truthfully: real engineering preflight PASS (2×Tesla T4, bnb-nf4, identity `qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25`, footprint 9,721,981,184 bytes, 174.016 s, probe 68+17, min free VRAM 8.417 GiB, GPU-only); canary `exp-20260807-131819` (`todo-smoke-001 / selective`, runtime source `f7b1ebba73b52868a95c47ef3806d3b09da16d93` / build `f7b1ebb`) **succeeded**: 3 selected / 2 preserved / 3 regenerated, migration `todo/migrations/0004_task_priority.py`, 3 model calls / 2,527+720=3,247 tokens / 295.944 s / 0 repair attempts; functional validation PASS; scenario evaluator PASS 10/10; HF `recovery_uploaded`; accepted real 14B canary records = 1 succeeded / 0 failed (isolated selective-only plan, NOT `1/9`); full 9-record Scientific Smoke V2 = NOT RUN; vs 7B: 25.0% fewer calls / 44.1% fewer tokens / repair eliminated / 14.9% slower → functional viability, not strategy superiority; unused `Q` import in generated `views.py` = non-blocking, evidence NOT to be repaired; continuous cell failed closed with zero model calls (generic experiment empty). Update README.md, SYSTEM_STATE.md, TODO.md, docs/START_HERE.md, docs/PROJECT_HANDOFF.md, docs/MASTER_IMPLEMENTATION_PLAN.md, reports/latest_phase_report.md, reports/PROJECT_HEALTH_REPORT.md, selective_updates/CHANGE_INDEX.md, selective_updates/metrics/change_metrics.jsonl, selective_updates/records/TECHNICAL-DEBT-AND-REFACTOR-SCHEDULE.md; create `selective_updates/records/QWEN14B-SELECTIVE-CANARY-SUCCESS-2026-08-07.md` + `docs/KAGGLE_QWEN14B_FULL9_SCIENTIFIC_SMOKE_RUNBOOK.md` (copied from the frozen workspace runbook). Commit exactly `docs(results): record successful Qwen 14B selective canary`; push; verify clean + local = remote.
- **Status:** COMPLETE (this documentation commit, pushed)

### QSC-02 - Run One Fresh Full-9 Scientific Smoke V2
- **Priority:** HIGH
- **Category:** Scientific Evidence
- **Description:** The only next scientific action — NOW SUPERSEDED IN SOURCE BY FULL9-WS-02 (the first Full-9 `exp-20260807-205422` under source `f7b1ebb` was RUN but REJECTED as a stable scientific matrix due to the workspace-isolation defect; the fresh Full-9 must use the corrected deployment source `7f2a4509482dc7e62c2b243374592e9a88e2ff48` / build `7f2a450`, not `f7b1ebb`). One fresh isolated 9-record experiment (3 frozen todo scenarios × 3 strategies × 1 repetition = 9 records) via the frozen runbook `docs/KAGGLE_QWEN14B_FULL9_SCIENTIFIC_SMOKE_RUNBOOK.md` (updated for the corrected build), profile `scientific-smoke-v2`, protocol 1.0, expected identity `qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25`. One engineering preflight + one benchmark process in a fresh isolated output dir (`/kaggle/working/runs/qwen14b_bnb_nf4_full9_scientific_smoke`); no `--strategy`, no `--max-runs`, no `--auto-resume-hf`. NEVER resume/merge the accepted canary and NEVER reuse the rejected `exp-20260807-205422` records or workspaces. After completion: independent results audit. No merge/tag/Pilot/fine-tune.
- **Status:** PENDING

### QSC-03 - Record Canary Milestone Tag and Freeze Full-9 Launch (docs only)
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Documentation-only truth update after the annotated milestone tag `v0.8.0-canary.1` was created and pushed. **Milestone tag:** `v0.8.0-canary.1` — created and pushed; annotated; points to `31a619857ce07eb09ab5e206fbc9dc792782c99c`. **Meaning:** first accepted real Qwen 14B NF4 selective-canary milestone. **Stable release = NO.** **Full 9-record Scientific Smoke V2 = NOT RUN.** **Merge to main = NOT YET** (pending Full-9 audit). **Pilot = NOT AUTHORIZED.** **Next action:** one fresh Full-9 Scientific Smoke V2 using `docs/KAGGLE_QWEN14B_FULL9_SCIENTIFIC_SMOKE_RUNBOOK.md`. Canonical tag naming: `v0.8.0-canary.N` = isolated calibration milestones; `v0.8.0-smoke-v2-complete` = create only after Full-9 result audit + main merge (stale `v2.0.0-scientific-smoke` future-tag wording replaced in the authoritative current plan). Update README.md, SYSTEM_STATE.md, TODO.md, docs/START_HERE.md, docs/PROJECT_HANDOFF.md, docs/MASTER_IMPLEMENTATION_PLAN.md, reports/latest_phase_report.md, reports/PROJECT_HEALTH_REPORT.md. Commit exactly `docs(state): record canary milestone tag and freeze Full-9 launch`; push; verify clean + local = remote + tag target unchanged. Do NOT modify code/tests/runtime/datasets/prompts/notebook/bundle/frozen runbook. Do NOT run pytest/Kaggle. Do NOT merge main. Do NOT create another tag.
- **Status:** COMPLETE (this documentation commit, pushed)

## Historical - Qwen 14B BNB-NF4 Canary Preparation

### Q14-01 - Model-Aware Qwen Identity
- **Priority:** HIGH
- **Category:** Controls
- **Description:** Commit A `0ece665` (pushed) replaced the frozen, model-blind `qwen:1:int8` identity with `qwen:<checkpoint-basename>:<quantization>:cfg-<12hex>`, derived before auto-resume from `config.json` fields (model_type, hidden_size, num_hidden_layers, num_attention_heads) + requested mode + checkpoint quantization method + SHA-256 (first 12 hex). 7B bnb-int8 / 14B bnb-int8 / 14B bnb-nf4 now always produce distinct identities; auto-resume and checkpoint validation reject any mismatch; historical `qwen:1:int8` records preserved. This closes the auto-resume contamination that downloaded `exp-20260804-133016` for an attempted 14B run.
- **Status:** COMPLETE (commit 0ece665, pushed)

### Q14-02 - Explicit BNB-NF4 Profile
- **Priority:** HIGH
- **Category:** Controls
- **Description:** Commit A `0ece665` (pushed) added canonical modes `bnb-int8` / `bnb-nf4` / `fp16` with CLI `--qwen-quantization` (default `bnb-int8`, unknown values exit 2). NF4 = `load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True` (Tesla T4). A prequantized non-bitsandbytes checkpoint (e.g. GPTQ) fails fast before tokenizer/model load with `PREQUANTIZED_CHECKPOINT_INCOMPATIBLE`; no automatic fallback. The failed 14B GPTQ attempt (`exp-20260804-195126`, 0 records / 0 calls / 0 tokens, preflight failed before the probe — GPTQConfig + BitsAndBytesConfig conflict) is preserved engineering evidence; GPTQ support is deferred.
- **Status:** COMPLETE (commit 0ece665, pushed)

### Q14-03 - 14B BNB-NF4 Canary Notebook
- **Priority:** HIGH
- **Category:** Deployment
- **Description:** Commit B `0a596b8` (pushed) pinned the notebook to the unquantized `/kaggle/input/models/qwen-lm/qwen2.5-coder/transformers/14b-instruct/1` (never `14b-instruct-gptq-int4`) with `QWEN_QUANTIZATION = "bnb-nf4"`, `RUN_GENERIC_ONE_RUN = False`, isolated output `/kaggle/working/runs/qwen14b_bnb_nf4_selective_canary`, a fail-closed canary preflight assertion (preflight passed, expected 14B identity, bnb-nf4, checkpoint not prequantized, GPU-only device map, free-VRAM threshold), `--strategy selective --max-runs 1 --new-experiment`, and no `--auto-resume-hf`. Notebook identity `SOURCE_COMMIT = 0ece665ef25e1b0ca3aa14f5f25977cadbd06d0c` / `DEPLOYED_BUILD_ID = 0ece665`; bundle rebuilt (147 files / 962,188 bytes), rerun content-identical, manifests verified.
- **Status:** COMPLETE (commit 0a596b8, pushed)

### Q14-04 - Full Gate and Readiness Record
- **Priority:** HIGH
- **Category:** Validation
- **Description:** Full suite **1,877 passed / 32 skipped / 0 failed**; Dataset Validation PASS (27 scenarios / 27 unique IDs / zero closure dataset changes); Prompt Validation 380 passed; Pipeline Smoke 189 passed; Scripted 9-record dry run 9/9 exit 0; Metric Verification 169 passed; Ruff 0 new (21 pre-existing); strict mypy 0 new (5 pre-existing, identical rule set to a self-contained HEAD baseline); compileall clean; notebook cells compile 8/8 canonical + 8/8 bundled; no cache files. Recorded at `selective_updates/records/QWEN14B-BNB-NF4-CANARY-READINESS.md`.
- **Status:** COMPLETE (commit <new> — this documentation commit, pushed)

### Q14-05 - Kaggle Engineering Preflight
- **Priority:** HIGH
- **Category:** Scientific Evidence
- **Description:** The Kaggle engineering preflight for the 14B bnb-nf4 profile was the authorized next action after readiness/loader/multi-GPU-VRAM closures. **PASSED on the real target environment (2026-08-07)**: Python 3.12.13 / Django 5.2.16 / DRF 3.17.1 / pytest 8.4.2 / accelerate 1.14.0 / bitsandbytes 0.49.2 / torch 2.10.0+cu128 / transformers 4.57.6; identity `qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25`; 2×Tesla T4; minimum free VRAM 8.417 GiB (≥2.0 GiB gate); GPU-only device map; preflight 174.016 s; probe 68+17. This preflight closure is superseded by the accepted successful selective canary (see QSC-01). No scientific canary/9-record run, merge, tag, or Pilot then authorized; now the only next scientific action = one fresh Full-9 run (QSC-02).
- **Status:** COMPLETE (real preflight PASS, 2026-08-07)

## Historical - Selective Calibration Canary Result

### SCC-01 - Execute Dedicated Selective Calibration Canary
- **Priority:** HIGH
- **Category:** Scientific Evidence
- **Description:** The dedicated selective calibration canary cell ran on Kaggle under source/build `50ec2c1`. Result `exp-20260804-133523` (`todo-smoke-001 / selective`): **failed / `model_output`**, 4 model calls / 5,804 tokens / 257.596 s / 3 selected / 2 preserved / **0 written**; initial 3 calls / 3,372 tokens; repair 1 call / 2,432 tokens (first repair byte-identical → `repair_no_progress` stopped the round); atomic application wrote zero files; HF `recovery_uploaded`; checkpoint 1 completed / 2 pending. Defects: `todo/models.py` `max_length=5` (MEDIUM length 6); duplicated `Priority(models.TextChoices)` in `todo/serializers.py` and `todo/views.py`. Vs previous selective run: 41.6% fewer tokens / 33.3% fewer calls / 22.4% faster, but initial generation tokens (3,372) and output hashes **identical** → harness safety controls worked; Qwen code quality unchanged. Incidental monolithic `exp-20260804-133016` (6 calls / 7,927 tokens / 300.165 s / `scientific_budget_exhausted`) is diagnostic only, NOT an accepted comparison. Continuous cell blocked fail-closed by `CALIBRATION_REVIEW_REQUIRED`. Full 9-record experiment NOT run; no merge/tag/Pilot/Kaggle authorized; no stable release claimed.
- **Status:** COMPLETE (2026-08-04)

### SCC-02 - Independent Audit of Canary Results
- **Priority:** HIGH
- **Category:** Audit
- **Description:** Independent audit of the canary results (truth of exp-20260804-133523, harness-control verification, harness-vs-model conclusion). After the audit, a deliberate decision: repeat the dedicated selective canary OR proceed to the full 9-record run. Do not merge/tag/Pilot/fine-tune.
- **Status:** PENDING (sentinel `SELECTIVE_CANARY_RESULT_AUDIT_REQUIRED`)

### SCC-03 - Document Canary Result (docs + ledgers only)
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Record truthfully: dedicated canary exp-20260804-133523; source/build 50ec2c1; 4 calls / 5,804 tokens / 257.596 s; 3 selected / 2 preserved / 0 written; failure `model_output`; defects in models/serializers/views; `repair_no_progress` after first identical repair; comparison vs previous selective run (41.6% / 33.3% / 22.4%); incidental monolithic run diagnostic only; continuous cell fail-closed; accepted dedicated canary records = 1, successful = 0. Update README.md, SYSTEM_STATE.md, TODO.md, docs/START_HERE.md, docs/PROJECT_HANDOFF.md, docs/MASTER_IMPLEMENTATION_PLAN.md, reports/latest_phase_report.md, reports/PROJECT_HEALTH_REPORT.md, selective_updates/CHANGE_INDEX.md, selective_updates/metrics/change_metrics.jsonl, selective_updates/records/SELECTIVE-CANARY-RESULTS-2026-08-04.md (new), selective_updates/records/TECHNICAL-DEBT-AND-REFACTOR-SCHEDULE.md; commit as `docs(results): record selective calibration canary outcome`
- **Status:** COMPLETE (commit <new>, pushed)

## Historical - Final Selective Canary Readiness Closure

### FSR-01 - Close Blocker 1: Per-Call Cooperative Deadline
- **Priority:** HIGH
- **Category:** Controls
- **Description:** Independent audit (GPT-5.6 Thinking) reproduced 3 model calls and false success after a 1s deadline because the deadline was checked only before the whole regeneration attempt. Commit 50ec2c1 (pushed): the workflow budget deadline is now checked before every selection/generation/repair model call; an in-flight call returning beyond the deadline consumes/records its tokens, makes no next call, writes none of the staged attempt, returns the failed scientific terminal `scientific_budget_exhausted` (truthful elapsed time and budget retained). Same guard on every internal Iterative Agent call, not only before `analyze_impact()`. Direct adversarial proofs: TestRunner.test_generation_deadline_stops_after_first_model_call (1 call, count 0, 15 tokens), TestRepairDeadline.test_repair_deadline_stops_after_first_repair_call (2 calls, repair_model_calls 1, repair tokens retained), TestIterativeAgentDeadline.test_agent_selection_deadline_stops_after_first_call (1 call, model_call_budget_exhausted, 50 tokens preserved)
- **Status:** COMPLETE (commit 50ec2c1, pushed)

### FSR-02 - Close Blocker 2: Atomic Metric Truth
- **Priority:** HIGH
- **Category:** Metrics
- **Description:** Independent audit reproduced 0 writes but `regenerated_artifact_count = 1` when an artifact was rejected. Commit 50ec2c1 (pushed): on atomic attempt abort all staged `generated` statuses become `aborted` or `rejected`, `regenerated_artifact_count = 0`, preserved response hashes/evidence remain available; all-valid attempt still commits every artifact exactly once. Metric/evidence truth, not a scientific formula change. Test alignment commit 356722b (pushed): test_r4_token_and_metrics.py assertions updated to the truthful staged statuses (`["aborted", "aborted", "rejected"]` / `["aborted", "rejected"]`); MagicMock exec_ret gains `model_call_budget_exhausted=False` in test_r3d_wiring.py
- **Status:** COMPLETE (commits 50ec2c1 + 356722b, pushed)

### FSR-03 - Close Blocker 3: Dedicated Selective Canary Cell
- **Priority:** HIGH
- **Category:** Deployment
- **Description:** Independent audit: the generic one-run cell selects `todo-smoke-001 / monolithic` (execution-plan order is scenario first, then strategies), NOT selective. Commit 28ecc5a (pushed): added dedicated, separately named Selective Calibration Canary cell (`selective-calibration-canary-cell`) with `--strategy selective --max-runs 1 --new-experiment --backend kaggle-qwen --profile scientific-smoke-v2 --max-attempts 3 --max-completion-tokens-per-call 1024 --max-total-workflow-tokens 0 --timeout 300 --hf-sync`, isolated output `runs/selective_calibration_canary`, NO `--auto-resume-hf`, `AUTHORIZE_CONTINUOUS_AFTER_CALIBRATION_REVIEW = False`. `_verify_selective_canary()` asserts exactly one current-source RunRecord `todo-smoke-001 / selective`, model identity `qwen:1:int8`, model calls > 0, terminal scientific success/failure outcome, HF `recovery_uploaded`, checkpoint `total_planned = 3 / completed = 1 / pending = 2`. Bundle pinned: `SOURCE_COMMIT = 50ec2c1ca43c230aed4538be32ca7dab2ccc22e5`, `DEPLOYED_BUILD_ID = 50ec2c1`; rebuilt 147 files / 948,250 bytes; content-identical rerun (tree hash 3b8d5b0ebf5e3ab8)
- **Status:** COMPLETE (commit 28ecc5a, pushed)

### FSR-04 - Complete Full Gate
- **Priority:** HIGH
- **Category:** Validation
- **Description:** Full suite 1,856 passed / 32 skipped / 0 failed (571.57s); grouped per-category 629 passed / 1 skipped (530.96s); scripted dry run --profile scientific-smoke-v2 into a fresh dir = 9/9 exit 0 (default runs dir held a stale checkpoint causing ReportRebuildError, not a code defect); mypy --strict src Success (77 files); ruff 0 new findings (175 pre-existing repo-wide; 19 pre-existing E501 in test_r4_token_and_metrics.py); compileall clean; notebook code cells compile (8/8 bundle incl. the canary cell); bundle content-identical; manifests verified; git diff --check clean; tree clean; local = remote = 356722b
- **Status:** COMPLETE

### FSR-05 - Correct Operational Documentation
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Record truthfully: f727b3e full suite was green but the independent audit rejected canary readiness; direct timeout repro (3 calls and false success after deadline); direct atomic metric repro (0 writes but count 1); generic one-run cell selected monolithic, not selective; exact Commit A/B hashes (50ec2c1, 28ecc5a); actual complete test totals (1,856 passed / 32 skipped / 0 failed); calibration exp-20260803-002741 remains preserved, 0/9 success; next action after independent audit = run the dedicated selective canary cell only. Do not claim a stable release. Update SYSTEM_STATE.md, README.md, TODO.md, docs/START_HERE.md, docs/PROJECT_HANDOFF.md, reports/latest_phase_report.md, reports/PROJECT_HEALTH_REPORT.md, selective_updates/CHANGE_INDEX.md, selective_updates/records/SELECTIVE-CANARY-READINESS-CLOSURE.md (new); commit as `docs(audit): record final selective-canary readiness closure`
- **Status:** COMPLETE (commit 25bfe04, pushed)

### FSR-06 - Independent Selective Canary Readiness Re-Audit
- **Priority:** HIGH
- **Category:** Audit
- **Description:** Independent re-audit of the three closed blockers, the deployment pin, and the green gate; after the re-audit the ONLY next action = run the dedicated selective calibration canary cell (not the generic one-run cell, not the continuous cell, not a full relaunch, not a fine-tune, not a tag/merge)
- **Status:** PENDING (sentinel `FINAL_SELECTIVE_CANARY_READINESS_AUDIT_REQUIRED`)

## Previous - Post-Smoke Calibration Closure

### PSC-01 - Close Four Proven Calibration Control Defects
- **Priority:** HIGH
- **Category:** Controls
- **Description:** Commit 27c1693 (pushed) closed: Closure A per-attempt atomic regeneration (normalize + validate every selected artifact, stage accepted bytes, write zero files of the attempt on any guard failure; per-attempt, not cross-iteration); Closure B repair no-progress detection (identical repair response hash after validation feedback → `repair_no_progress`, stop remainder of round before additional model calls, no new round; consumed calls/tokens retained; temperature/prompts never altered); Closure C fail-closed calibration continuation gate (`AUTHORIZE_CONTINUOUS_AFTER_CALIBRATION_REVIEW = False`; `scientific_failure` prints `CALIBRATION_REVIEW_REQUIRED`, no continuous execution without deliberate human change to True; `engineering_blocker` stops and raises); Closure D cooperative deadline semantics (deadline checked before every selection/generation/repair call; workflow budget exhaustion = scientific terminal `scientific_budget_exhausted` with `configured_budget`/`actual_elapsed_seconds` recorded; preflight/env/harness/HF timeouts stay engineering blockers). Unit + integration tests added
- **Status:** COMPLETE (commit 27c1693, pushed)

### PSC-02 - Pin Calibration-Controlled Smoke V2 Bundle
- **Priority:** HIGH
- **Category:** Deployment
- **Description:** Commit 56772fe (pushed): canonical notebook re-pins `SOURCE_COMMIT = 27c1693e22b1a68be0b299fb146d9ff1e500908b`, `DEPLOYED_BUILD_ID = 27c1693`; kaggle_upload bundle rebuilt via scripts/build_upload_bundle.py (147 files / 934,495 bytes; code 90, data 56, notebook 1); manifests verified; no __pycache__/*.pyc; canonical + generated notebooks compile 7/7 code cells
- **Status:** COMPLETE (commit 56772fe, pushed)

### PSC-03 - Reconcile Stale Constant-Output Test Fixtures
- **Priority:** HIGH
- **Category:** Tests
- **Description:** First full gate exposed 9 failures in tests/integration/test_r4_metric_contract.py + tests/integration/test_su0010a_regeneration.py: deterministic backends returned identical text every call, accidentally activating the new no-progress early-stop and lowering observed counts below max-attempt expectations. NOT validly proven pre-existing (ec9ba0b lacked the early-stop; a detached worktree using the main editable installation can import the current branch instead of the worktree source — cross-worktree comparison only valid with isolated env or worktree-local PYTHONPATH). Commit 231b0a5 (pushed, test-fixture-only): `_FixedTokenBackend` gains opt-in `vary_output=True` (3 duration tests), `_SentinelBackend` returns a unique valid Python string per indexed response preserving exact TokenUsage, 5 bounded-repair fixtures return `value = <call_number>`; all expectations preserved (max_attempts 3, calls 3/6, repair_attempts, repair_model_calls 2/4, durations 1.5/2.1, tokens 41/59/90, JSONL/reporting identity); dedicated identical-output no-progress tests unchanged; new boundary test `test_no_progress_and_max_attempts_are_separate_contracts` proves constant output → 2 calls + repair_no_progress vs distinct outputs → 3 calls / 2 repairs
- **Status:** COMPLETE (commit 231b0a5, pushed)

### PSC-04 - Complete Final Gate
- **Priority:** HIGH
- **Category:** Validation
- **Description:** Full suite 1,849 passed / 32 skipped / 0 failed; mypy --strict src/benchmark Success (77 files); ruff 93 = 93 baseline (0 new, line-set identical); compileall clean; bundle build content-identical; all notebook cells compile; manifests verified; git diff --check clean; tree clean; local = remote = 231b0a5
- **Status:** COMPLETE

### PSC-05 - Correct Operational Documentation
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Update README.md, SYSTEM_STATE.md, TODO.md, docs/START_HERE.md, docs/PROJECT_HANDOFF.md, docs/MASTER_IMPLEMENTATION_PLAN.md, reports/latest_phase_report.md, reports/PROJECT_HEALTH_REPORT.md, selective_updates/CHANGE_INDEX.md, selective_updates/metrics/change_metrics.jsonl, selective_updates/records/TECHNICAL-DEBT-AND-REFACTOR-SCHEDULE.md, selective_updates/records/KAGGLE-SMOKE-V2-MODEL-OUTPUT-CLOSURE.md; record calibration evidence exp-20260803-002741 (9 records / 0 succeeded / 8 failed / 1 timed_out / 81 calls / 118,211 tokens, preserved, not accepted scientific evidence) and the 9-failure reconciliation truth; commit as docs(audit): record calibration results and safety closure
- **Status:** COMPLETE (commit f727b3e, pushed)

### PSC-06 - Independent Calibration Closure Audit
- **Priority:** HIGH
- **Category:** Audit
- **Description:** Independent audit of the four closed controls, the test-fixture reconciliation, and the green gate; after the audit the ONLY next action = one selective calibration canary (not a full relaunch, not a fine-tune, not a tag/merge)
- **Status:** PERFORMED at f727b3e — audit REJECTED canary readiness on three blockers (per-call deadline, atomic metric truth, no selective canary cell); blockers closed under the Final Selective Canary Readiness Closure (see Current section; sentinel `FINAL_SELECTIVE_CANARY_READINESS_AUDIT_REQUIRED`)

## Previous - Pre-Benchmark Final Reproducibility Audit Closure

### PBF-01 - Recover Exact Passing Dependency Versions
- **Priority:** HIGH
- **Category:** Reproducibility
- **Description:** Recover the exact versions from the previously passing environment: tabulate 0.10.0, httpx 0.28.1, Jinja2 3.1.6, pytest 8.4.2, ruff 0.15.22, mypy 1.20.2
- **Status:** COMPLETE

### PBF-02 - Declare Complete Pre-Benchmark Dependencies
- **Priority:** HIGH
- **Category:** Reproducibility
- **Description:** Declare the full pre-benchmark test environment in `pyproject.toml [dev]` + `requirements-dev.txt`: Django==5.2.16, djangorestframework==3.17.1, pytest-django==4.12.0, pytest-asyncio==1.2.0 (required by --asyncio-mode=auto), tabulate==0.10.0, httpx==0.28.1, Jinja2==3.1.6, huggingface_hub==0.24.0 (1.x broke positional hf_hub_download/local_dir_use_symlinks + strict mypy), types-pyyaml>=6.0,<7, pytest>=8.0,<9. Runtime [project.dependencies] and requirements-smoke-kaggle.lock untouched. Commits 769d84e + e5d9430 (both pushed)
- **Status:** COMPLETE

### PBF-03 - Recreate Clean Environment From Declarations Only
- **Priority:** HIGH
- **Category:** Reproducibility
- **Description:** Delete + recreate `_workspace\cache\prebenchmark-py311` (Python 3.11.9) using only `py -3.11 -m venv` + `pip install -e ".[dev]" "pytest==8.4.2" "ruff==0.15.22" "mypy==1.20.2"`; verified pytest 8.4.2 / Django 5.2.16 / DRF 3.17.1 / pytest-django 4.12.0 / tabulate 0.10.0 / httpx 0.28.1 / Jinja2 3.1.6 / ruff 0.15.22 / mypy 1.20.2
- **Status:** COMPLETE

### PBF-04 - Repeat the Complete Clean Gate
- **Priority:** HIGH
- **Category:** Validation
- **Description:** Full suite 1,833 passed / 32 skipped / 1 failed (sole failure = test_notebook_source_commit_matches_deployed_runtime_tree, structural - mandated pyproject.toml declaration change breaks byte-identity with pinned aac9914 SOURCE_COMMIT; frozen artifacts not modified to force green, reported truthfully); Dataset 285/5; Prompt 158; Pipeline Smoke 220/12; Dry Run 9/9; Integration PASS; Metric Verification 169; mypy strict Success (77 files); ruff 93 = 93 baseline (0 new); compileall clean; bundle build verified then kaggle_upload restored
- **Status:** COMPLETE

### PBF-05 - Correct Operational Documentation
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Update README.md, SYSTEM_STATE.md, TODO.md, docs/START_HERE.md, docs/PROJECT_HANDOFF.md, docs/MASTER_IMPLEMENTATION_PLAN.md, reports/latest_phase_report.md, reports/PROJECT_HEALTH_REPORT.md, selective_updates/CHANGE_INDEX.md, selective_updates/metrics/change_metrics.jsonl, selective_updates/records/TECHNICAL-DEBT-AND-REFACTOR-SCHEDULE.md; create selective_updates/records/KAGGLE-SMOKE-V2-MODEL-OUTPUT-CLOSURE.md; record historical exp-20260801-210443 (one failed model-output terminal record under 6f88823, preserved, excluded from current aac9914 aggregation) and current aac9914 records = 0/9
- **Status:** COMPLETE

### PBF-06 - Independent Pre-Benchmark Reproducibility Audit
- **Priority:** HIGH
- **Category:** Audit
- **Description:** Independent audit performed; its exact deployment-only correction was imported via bundle fast-forward (f8d00d7, exactly one commit from e5d9430). Sentinel updated to `PRE_BENCHMARK_FINAL_SOURCE_REPIN_AUDIT_REQUIRED`. Next (only) action after this independent audit = Kaggle engineering preflight only (not the scientific One-Run cell)
- **Status:** COMPLETE (sentinel `PRE_BENCHMARK_FINAL_SOURCE_REPIN_AUDIT_REQUIRED`)

### PBF-07 - Apply Deployment-Only Correction (f8d00d7) and Re-Run Complete Gate
- **Priority:** HIGH
- **Category:** Deployment
- **Description:** Previous 76a6b16 gate had 1 failure, not a green full suite: test_notebook_source_commit_matches_deployed_runtime_tree failed because the mandated pyproject.toml declaration change broke byte-identity with the pinned aac9914 SOURCE_COMMIT (root cause = dependency declarations changing pyproject.toml after the aac9914/311e084 deployment pin; no runtime/prompt/metric/scenario/evaluator/data change needed). Apply the exact deployment-only correction f8d00d7 (bundle PRE_BENCHMARK_FINAL_REPIN_EXACT.bundle): kaggle_upload/code/pyproject.toml gains the six declaration lines (byte-identical to canonical); notebooks re-pin SOURCE_COMMIT=e5d943065c6f4158c30a1cbbba39436ab2a7a898, DEPLOYED_BUILD_ID=e5d9430; manifests re-verified. Complete clean gate now green: full suite 1,834 passed / 32 skipped / 0 failed; Dataset 285/5 (data unchanged); Prompt 158; Pipeline Smoke 220/12; Dry Run 9/9; Integration PASS; Metric Verification 169; mypy strict Success (77 files); ruff 93 = 93 baseline (0 new); compileall clean; all notebook cells compile; bundle build content-identical (147 files / 928,329 bytes); no cache files in kaggle_upload; tree clean. Historical exp-20260801-210443 failed model-output record under 6f88823 remains excluded from the current e5d9430 aggregation; current accepted real records = 0/9
- **Status:** COMPLETE (commit f8d00d7, pushed)

## Historical — R7C Real-Run Root Closure (superseded)

### R7C-01 — Close Environment Memory Contract
- **Priority:** HIGH
- **Category:** Runtime Contract
- **Description:** Pin exact Kaggle runtime in `requirements-smoke-kaggle.lock` (Django==5.2.16, djangorestframework==3.17.1, pytest==8.4.2, pytest-django==4.12.0, accelerate==1.14.0, bitsandbytes==0.49.2; torch/transformers unpinned), install + verify in the notebook `install-lock-cell` (`EXPECTED_RUNTIME` via `RUNTIME_ATTR`), write `runtime_environment.json` (schema `kaggle_runtime_environment.v1`)
- **Status:** COMPLETE (commit 7a80e53)

### R7C-02 — Close Int8 Memory Contract
- **Priority:** HIGH
- **Category:** Runtime Contract
- **Description:** int8 default (`qwen:1:int8`), `PYTORCH_ALLOC_CONF=expandable_segments:True`, seeded 64-token `run_probe`, preflight ≥2.0 GiB VRAM headroom; no 4-bit fallback
- **Status:** COMPLETE (commit 7a80e53)

### R7C-03 — Close Frozen Scenario-Context Prompt Contract
- **Priority:** HIGH
- **Category:** Prompt Contract
- **Description:** Freeze `RegenerationScenarioContext` into strategy prompts; preserve-only byte-identity enforcement when `expected_actions` is non-empty
- **Status:** COMPLETE (commit 7a80e53)

### R7C-04 — Close Infrastructure-Nonrepairable Repair Contract
- **Priority:** HIGH
- **Category:** Repair Contract
- **Description:** `FailureKind.infrastructure_nonrepairable` first-failure classification, one execution, zero LLM repair
- **Status:** COMPLETE (commit 7a80e53)

### R7C-05 — Add Preflight Gate and Pin Bundle
- **Priority:** HIGH
- **Category:** Deployment
- **Description:** `src/benchmark/execution/preflight.py` + `--kaggle-preflight-only` (schema `kaggle_smoke_preflight.v1`, 6 checks; exit 0/1; no run side effects); notebook gate cell before secrets + exec; reorder notebook setup → install-lock → preflight → secrets → run; rebuild bundle (147 files / 894,735 bytes)
- **Status:** COMPLETE (commit f01b8f0)

### R7C-06 — Independent Real-Run Root Closure Audit
- **Priority:** HIGH
- **Category:** Audit
- **Description:** Independent audit of the four closed contracts + preflight gate; then update Kaggle code dataset + notebook, run one real cell (require 1/9), continue to 9/9
- **Status:** SUPERSEDED — see R7C-07 (full-gate audit of the correction)

### R7C-07 — Import Independent Root Correction and Run Full Gate
- **Priority:** HIGH
- **Category:** Audit Correction
- **Description:** Prior R7C report incorrectly called a 1,451-test subset the full suite; true first full suite = 23 failed / 1,759 passed / 32 skipped (root cause: blanket `baseline_validation => infrastructure_nonrepairable` in `src/benchmark/execution/runner.py`). Import the independent GPT-5.6 Thinking correction via bundle fast-forward (`ffa179a` + `6d6aa36`, HEAD `6d6aa36`, pushed): exact 23 former failures pass; DRF import mapping, exact version verification, fail-fast preflight, driver-level VRAM, CPU-offload rejection, Python 3.12 contract, stale source identity corrected. Run the full Windows gate (full suite now 1,790 passed / 32 skipped / 0 failed; mypy 0; compileall clean; builder rerun clean; identity test passes SOURCE_COMMIT=ffa179a / DEPLOYED_BUILD_ID=ffa179a). Valid real Qwen remains 0/9; Kaggle blocked.
- **Status:** COMPLETE (ffa179a + 6d6aa36 imported, pushed; full gate green)

### R7C-08 — Independent Full-Gate Audit of Corrected R7C Branch
- **Priority:** HIGH
- **Category:** Audit
- **Description:** Independent audit of the corrected branch HEAD `6d6aa36` (repair classifier, preflight dependency/version/VRAM/device-map contracts, Python 3.12 runtime contract, notebook source identity, exact 23 former failures passing, current full gate); then update Kaggle code dataset + notebook, run one real cell (require 1/9), continue to 9/9
- **Status:** SUPERSEDED — see R7C-09 (post-gate audit) and R7C-10 (final full-gate audit)

### R7C-09 — Import Independent Post-Gate Correction and Run Full Gate
- **Priority:** HIGH
- **Category:** Audit Correction
- **Description:** An independent post-gate audit performed on `5e47a1e` found (a) the project-local `ImportError` was incorrectly bypassing repair (blanket marker match); (b) the bundled preflight could not import `benchmark` without ambient `PYTHONPATH`; (c) preflight output was buffered. Import the exact audited correction via bundle fast-forward (`6f88823` fix(kaggle): align repair eligibility and script bootstrap + `5797fc0` chore(deploy): pin audited preflight and live gate, HEAD `5797fc0`, pushed): project-local `ModuleNotFoundError` / `cannot import name` now repairable via the canonical classifier; missing declared Django + CUDA OOM stay `infrastructure_nonrepairable`; bundled script bootstraps its own `src/`; preflight output streamed + persisted. Notebook source identity = `SOURCE_COMMIT 6f88823` / `DEPLOYED_BUILD_ID 6f88823`. Full gate = 1,796 passed / 32 skipped / 0 failed; ruff 0 new (93 = 93); mypy 0; compileall clean; builder rerun content-identical. Valid real Qwen remains 0/9; no scientific evidence; Kaggle blocked.
- **Status:** COMPLETE (6f88823 + 5797fc0 imported, pushed; full gate green)

### R7C-10 — Final Independent Full-Gate Audit of `5797fc0`
- **Priority:** HIGH
- **Category:** Audit
- **Description:** Final independent full-gate audit of the corrected branch HEAD `5797fc0` (repair eligibility, bundled clean-subprocess preflight bootstrap, preflight live streaming, boundary regressions, complete full suite); after it passes, the only authorized Kaggle action is the engineering preflight cell — not the scientific One-Run cell; then update Kaggle code dataset + notebook, run one real cell (require 1/9), continue to 9/9
- **Status:** PENDING (sentinel `R7C_POST_AUDIT_FULL_GATE_REQUIRED`)

## Phase 0 — Bootstrap and Environment

### T001 — Create Repository Structure
- **Priority:** HIGH
- **Category:** Structure
- **Description:** Create directories: src/benchmark, tests, notebooks, scripts, reports
- **Acceptance Criteria:** All directories exist with __init__.py files
- **Dependencies:** None
- **Status:** COMPLETE_STATICALLY
- **Owner:** OpenCode
- **Evidence:** Directories verified via Get-ChildItem

### T002 — Create State Files
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, PROTOCOL_VERSION.md, docs/MASTER_IMPLEMENTATION_PLAN.md, docs/HUMAN_DECISIONS_REQUIRED.md
- **Acceptance Criteria:** All files present with required content
- **Dependencies:** T001
- **Status:** COMPLETE_STATICALLY
- **Owner:** OpenCode
- **Evidence:** Files written to disk

### T003 — Create Environment Files
- **Priority:** HIGH
- **Category:** Environment
- **Description:** Create environment.yml, requirements-dev.txt, requirements-kaggle.txt
- **Acceptance Criteria:** All three files present with correct package lists
- **Dependencies:** T001
- **Status:** COMPLETE_STATICALLY
- **Owner:** OpenCode
- **Evidence:** Files written to disk

### T004 — Create Conda Environment
- **Priority:** HIGH
- **Category:** Environment
- **Description:** Create `selective-regen-benchmark` with Python 3.11 via conda
- **Acceptance Criteria:** Environment exists and is activatable
- **Dependencies:** T003
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** conda env list output, environment.yml resolution

### T005 — Install Local Engineering Dependencies
- **Priority:** HIGH
- **Category:** Environment
- **Description:** Install packages from requirements-dev.txt inside the project Conda environment via pip
- **Acceptance Criteria:** All packages installed without conflicts
- **Dependencies:** T004
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** pip list output, pip check passing

### T006 — Validate Environment
- **Priority:** HIGH
- **Category:** Validation
- **Description:** Run pip check, import smoke tests, version checks, duplicate inspection, optional dependency checks
- **Acceptance Criteria:** All checks pass; no unresolved conflicts
- **Dependencies:** T005
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** Check outputs, LOCAL_ENVIRONMENT_REPORT.md

### T007 — Create Environment Report
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create reports/LOCAL_ENVIRONMENT_REPORT.md with all required sections
- **Acceptance Criteria:** Report contains all sections listed in Section 4.3 of the guide
- **Dependencies:** T006
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** File exists with complete content

### T008 — Create Phase Report
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create reports/latest_phase_report.md summarizing Phase 0
- **Acceptance Criteria:** Report lists completed tasks, created files, checks passed, next task
- **Dependencies:** T007
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** File exists with complete content

### T009 — Initialize Git Repository
- **Priority:** MEDIUM
- **Category:** VCS
- **Description:** Initialize Git repo, create .gitignore, make initial bootstrap commit
- **Acceptance Criteria:** Git repo exists with initial commit on main branch
- **Dependencies:** T001-T008
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** git log output

### T010 — Final Review and Handoff
- **Priority:** HIGH
- **Category:** Process
- **Description:** Review all files, verify environment, produce final message
- **Acceptance Criteria:** All files reviewed; environment activation command verified
- **Dependencies:** T009
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** Final message with handoff statement

## Phase 1 — Input Audit

### T101 — Inspect inputs/ Directory
- **Priority:** HIGH
- **Category:** Audit
- **Description:** Inspect all files under inputs/; verify immutability
- **Acceptance Criteria:** Complete inventory of inputs/ with file types, sizes, and descriptions
- **Dependencies:** T010
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** INPUT_AUDIT_REPORT.md Section 2

### T102 — Classify Existing Benchmark Outputs
- **Priority:** HIGH
- **Category:** Audit
- **Description:** Classify all existing benchmark outputs as legacy_pilot per preapproved decision
- **Acceptance Criteria:** Classification documented; zero legacy outputs verified
- **Dependencies:** T101
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** INPUT_AUDIT_REPORT.md Section 3

### T103 — Identify Reusable Components
- **Priority:** HIGH
- **Category:** Audit
- **Description:** Catalog all reusable components from Phase 0
- **Acceptance Criteria:** Comprehensive inventory with status and notes for each component
- **Dependencies:** T101
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** INPUT_AUDIT_REPORT.md Section 5

### T104 — Identify Errors, Leakage Risks, Metric Problems
- **Priority:** HIGH
- **Category:** Audit
- **Description:** Scan source material for errors, data leakage risks, metric design issues
- **Acceptance Criteria:** All findings documented with severity and recommendations
- **Dependencies:** T102, T103
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** INPUT_AUDIT_REPORT.md Sections 6, 7

### T105 — Create Migration Documentation
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create reports/INPUT_AUDIT_REPORT.md with full audit findings
- **Acceptance Criteria:** Report covers all Phase 1 requirements; missing inputs explicitly recorded
- **Dependencies:** T104
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** reports/INPUT_AUDIT_REPORT.md

### T106 — Update State Files
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Update SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, reports/latest_phase_report.md for Phase 1
- **Acceptance Criteria:** All state files consistent; exact next task recorded
- **Dependencies:** T105
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** Git diff showing updates to all four files

## Phase 2A — Research Protocol Draft

### T201 — Draft Research Questions Traceability
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Produce full RQ-to-hypothesis-to-evaluation-phase traceability table
- **Acceptance Criteria:** All 5 RQs mapped to hypotheses, measures, and evaluation phases
- **Dependencies:** T106
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** PHASE2_PROTOCOL_DRAFT.md §1

### T202 — Draft Hypothesis Specification
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Specify all 5 hypotheses with measures, comparisons, and decision criteria
- **Acceptance Criteria:** Each hypothesis has primary comparison, measures, and interpretation criterion
- **Dependencies:** T201
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** PHASE2_PROTOCOL_DRAFT.md §2

### T203 — Draft Repository Selection Criteria
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Define selection criteria, acquisition policy, and architectural diversity targets
- **Acceptance Criteria:** Preapproved repos documented; selection criteria formalized
- **Dependencies:** T202
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** PHASE2_PROTOCOL_DRAFT.md §3

### T204 — Draft Candidate Artifact Universe
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Define artifact node types, edge types, granularity, and universe boundary
- **Acceptance Criteria:** All 10 node types, 7 edge types, attributes, and exclusions documented
- **Dependencies:** T202
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** PHASE2_PROTOCOL_DRAFT.md §4

### T205 — Draft Ground-Truth and Annotation Protocol
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Define ground-truth construction, annotation process, adjudication, and quality thresholds
- **Acceptance Criteria:** Full protocol from source materials to published annotations
- **Dependencies:** T204
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** PHASE2_PROTOCOL_DRAFT.md §5–6

### T206 — Draft Scenario Taxonomy
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Define change types, blast radius categories, scenario schema, and naming convention
- **Acceptance Criteria:** 8 change types, 3 blast radii, 8 scenarios per repo schema fully defined
- **Dependencies:** T203, T204
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** PHASE2_PROTOCOL_DRAFT.md §7

### T207 — Draft Baseline Definitions
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Define all 6+ baselines including ablation variants
- **Acceptance Criteria:** Every strategy named, described, and categorized (baseline/ablation/reference)
- **Dependencies:** T202
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** PHASE2_PROTOCOL_DRAFT.md §8

### T208 — Draft Metrics Suite
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Define primary and secondary metrics with formal definitions
- **Acceptance Criteria:** 6 primary metric categories + 5 secondary metric categories fully specified
- **Dependencies:** T201, T207
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** PHASE2_PROTOCOL_DRAFT.md §9–10

### T209 — Draft Statistical Analysis Plan
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Define tests, NI margin, corrections, power analysis, outlier policy
- **Acceptance Criteria:** Per-hypothesis test selection; reporting formats specified
- **Dependencies:** T208
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** PHASE2_PROTOCOL_DRAFT.md §11

### T210 — Draft Policies (Randomization, Seeds, Budget, Failure, Leakage)
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Define randomization, seed, execution budget, failure, and leakage prevention policies
- **Acceptance Criteria:** All 5 policies fully defined
- **Dependencies:** T209
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** PHASE2_PROTOCOL_DRAFT.md §12–16

### T211 — Draft Validity and Reproducibility Sections
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Document threats to validity and reproducibility protocol
- **Acceptance Criteria:** Construct/internal/external/conclusion validity + reproducibility plan
- **Dependencies:** T210
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** PHASE2_PROTOCOL_DRAFT.md §17–18

### T212 — Compile Full Protocol Draft
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Assemble all sections into reports/PHASE2_PROTOCOL_DRAFT.md with status tags
- **Acceptance Criteria:** All 21 sections present; every item tagged PREAPPROVED/PROPOSED/REQUIRES_RESEARCHER_APPROVAL
- **Dependencies:** T201–T211
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** reports/PHASE2_PROTOCOL_DRAFT.md

### T213 — Update State Files for Phase 2A
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Update SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, reports/latest_phase_report.md for Phase 2A
- **Acceptance Criteria:** All state files consistent; 14 researcher decision items documented; exact next task recorded
- **Dependencies:** T212
- **Status:** LOCAL_ENGINEERING_VALIDATED
- **Owner:** OpenCode
- **Evidence:** Git diff showing updates to all four files

## Phase 2B — Protocol Freeze

### T301 — Apply Researcher Decisions DA-01 through DA-14
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Apply all 14 researcher-approved decisions to the draft protocol
- **Acceptance Criteria:** Every DA item from FINAL_RESEARCH_PROTOCOL_DECISIONS.md applied; contradictory draft wording overwritten
- **Dependencies:** T213
- **Status:** FROZEN
- **Owner:** Researcher + OpenCode
- **Evidence:** docs/RESEARCHER_DECISIONS_DA_AC.md

### T302 — Apply Mandatory Corrections AC-01 through AC-11
- **Priority:** HIGH
- **Category:** Protocol
- **Description:** Apply all 11 mandatory corrections from the researcher
- **Acceptance Criteria:** Every AC item applied; 9 contradictions corrected
- **Dependencies:** T301
- **Status:** FROZEN
- **Owner:** OpenCode
- **Evidence:** docs/RESEARCHER_DECISIONS_DA_AC.md (contradictions section)

### T303 — Create Frozen Protocol Documents
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create 7 protocol docs under docs/ and decision records
- **Acceptance Criteria:** All 8 docs/ files present with FROZEN status, v1.0
- **Dependencies:** T302
- **Status:** FROZEN
- **Owner:** OpenCode
- **Evidence:** SHA-256 checksums for all 8 documents

### T304 — Update State Files for Phase 2B
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Update PROTOCOL_VERSION.md, SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, reports/PHASE2B_PROTOCOL_FREEZE_REPORT.md, reports/latest_phase_report.md
- **Acceptance Criteria:** All state files consistent; protocol_status: FROZEN; Phase 3 authorized
- **Dependencies:** T303
- **Status:** FROZEN
- **Owner:** OpenCode
- **Evidence:** Git diff showing updates to all files

### T305 — Validation of Frozen Protocol
- **Priority:** HIGH
- **Category:** Validation
- **Description:** Validate all frozen documents for internal consistency; no unresolved REQUIRES_RESEARCHER_APPROVAL; SHA-256 checksums
- **Acceptance Criteria:** 10 validation checks pass; checksums recorded
- **Dependencies:** T304
- **Status:** FROZEN
- **Owner:** OpenCode
- **Evidence:** SYSTEM_STATE.md local checks passed list

## Phase 3 — Repository and Scenario Preparation

### T401 — Select and Pin Repository Versions
- **Priority:** HIGH
- **Category:** Repository
- **Description:** Select 3 confirmatory repositories (todo, djangocms, saleor); pin versions with commit SHAs
- **Acceptance Criteria:** DA-01, DA-02, DA-03 compliance verified for all 3 repos
- **Dependencies:** T305
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** benchmark_data/manifests/repository_versions.yaml; REPOSITORY_SELECTION_REPORT.md

### T402 — Create Repository Profiles
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create architectural profiles for all 3 repositories with boundary analysis
- **Acceptance Criteria:** 3 profiles covering overview, architecture, artifact catalog, test suite, boundaries, limitations
- **Dependencies:** T401
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** benchmark_data/repository_profiles/{todo,djangocms,saleor}.yaml

### T403 — Create Scenario Definitions (24 YAML files)
- **Priority:** HIGH
- **Category:** Scenario
- **Description:** Design 8 scenarios per repository (3 localized, 3 moderate, 2 cross-cutting) covering all 8 change types
- **Acceptance Criteria:** All 24 YAML files with scenario_id, requirements, acceptance criteria, expected artifacts, hidden_tests
- **Dependencies:** T402
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 24 files under benchmark_data/scenarios/

### T404 — Create Documentation Reports
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create 6 reports covering selection, architecture, scenario design, licensing, Kaggle feasibility, phase summary
- **Acceptance Criteria:** All reports present with complete content
- **Dependencies:** T403
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 6 reports under reports/

### T405 — Create Manifests
- **Priority:** HIGH
- **Category:** Manifest
- **Description:** Create repositories.yaml and repository_versions.yaml manifests
- **Acceptance Criteria:** Both files present with frozen version metadata
- **Dependencies:** T401
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** benchmark_data/manifests/{repositories,repository_versions}.yaml

### T406 — Update State Files for Phase 3
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Update SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, reports/latest_phase_report.md for Phase 3
- **Acceptance Criteria:** All state files consistent; Phase 3 recorded as COMPLETE; Phase 4 as next
- **Dependencies:** T404, T405
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Git diff showing updates to all files

## Phase 3.5 — Static Architecture Audit and Project Map

### T350 — Inspect Repository Layout and Identify Conflicts
- **Priority:** HIGH
- **Category:** Audit
- **Description:** Inspect full repository tree; identify duplicate directories, stale files, misplaced docs, naming inconsistencies, Git boundary issues
- **Acceptance Criteria:** Complete inventory of structural issues; documented root vs project conflicts
- **Dependencies:** T406
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** reports/PROJECT_STRUCTURE_CONFLICT_REPORT.md

### T351 — Define Canonical Project Root and Path Policy
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create docs/PROJECT_ROOT_AND_PATH_POLICY.md with canonical root, directory classification, remediation plan
- **Acceptance Criteria:** Policy states exact canonical root, classifies every directory, includes remediation for duplicates
- **Dependencies:** T350
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** docs/PROJECT_ROOT_AND_PATH_POLICY.md

### T352 — Create Project Structure Map
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create docs/PROJECT_STRUCTURE_MAP.md with complete proposed tree and directory responsibility tables
- **Acceptance Criteria:** Every proposed package has one responsibility documented; import rules per package
- **Dependencies:** T351
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** docs/PROJECT_STRUCTURE_MAP.md

### T353 — Define Software Architecture and Interfaces
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create docs/SOFTWARE_ARCHITECTURE.md with 13 layers, 11 interface specifications, model backend separation, import isolation
- **Acceptance Criteria:** All layers documented; all interfaces have responsibility, inputs, outputs, failure behavior, extension rules
- **Dependencies:** T352
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** docs/SOFTWARE_ARCHITECTURE.md

### T354 — Define Dependency Rules
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create docs/DEPENDENCY_RULES.md with allowed/prohibited dependency directions, import policies
- **Acceptance Criteria:** Every package has explicit import rules; 10 prohibited patterns documented
- **Dependencies:** T353
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** docs/DEPENDENCY_RULES.md

### T355 — Create Extension Guide (Plugin/Registry Design)
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create docs/EXTENSION_GUIDE.md with plugin lifecycle, registry design, protocol skeletons, factory pattern
- **Acceptance Criteria:** Adding a strategy/LLM/validator/metric does not require core changes; registry is not global singleton
- **Dependencies:** T354
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** docs/EXTENSION_GUIDE.md

### T356 — Define Public/Private Data Boundary
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create docs/PUBLIC_PRIVATE_DATA_BOUNDARY.md with classification, import isolation, data flow, audit checklist
- **Acceptance Criteria:** Private data inaccessible to strategies; data flow from execution to evaluation is unidirectional
- **Dependencies:** T355
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** docs/PUBLIC_PRIVATE_DATA_BOUNDARY.md

### T357 — Create Phase 4 Implementation Blueprint
- **Priority:** HIGH
- **Category:** Planning
- **Description:** Create docs/PHASE4_IMPLEMENTATION_BLUEPRINT.md with 6 milestones (4A–4F), files, tests, acceptance criteria
- **Acceptance Criteria:** Each milestone has dependencies, forbidden work, estimated complexity
- **Dependencies:** T353
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** docs/PHASE4_IMPLEMENTATION_BLUEPRINT.md

### T358 — Create Architecture Validation Plan
- **Priority:** HIGH
- **Category:** Planning
- **Description:** Create docs/ARCHITECTURE_VALIDATION_PLAN.md with 11 validation checks, tools, approaches
- **Acceptance Criteria:** Covers import boundaries, circular imports, layer isolation, no torch locally, no leakage
- **Dependencies:** T357
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** docs/ARCHITECTURE_VALIDATION_PLAN.md

### T359 — Create Architecture Audit Reports
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create reports/PHASE3_5_ARCHITECTURE_AUDIT.md and reports/PROJECT_STRUCTURE_CONFLICT_REPORT.md
- **Acceptance Criteria:** Reports document current tree, proposed tree, duplicate issues, remediation plan, architecture decisions
- **Dependencies:** T350–T358
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** reports/PHASE3_5_ARCHITECTURE_AUDIT.md, reports/PROJECT_STRUCTURE_CONFLICT_REPORT.md

### T360 — Update State Files for Phase 3.5
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Update SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, reports/latest_phase_report.md for Phase 3.5
- **Acceptance Criteria:** All state files consistent; Phase 3.5 recorded as COMPLETE; Phase 4A as next
- **Dependencies:** T359
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Edits to all four state files

## Phase 3.6 — Structure Remediation and Baseline Commit

### T361 — Resolve Duplicate Documentation and Delete Stale Files
- **Priority:** HIGH
- **Category:** Structure
- **Description:** Copy outer OPENCODE_EXECUTION_GUIDE.md and MASTER_IMPLEMENTATION_PLAN.md into project/docs/. Delete stale outer FINAL_RESEARCH_PROTOCOL_DECISIONS.md and HUMAN_DECISIONS_REQUIRED.md. Delete stale outer benchmark_data/. Preserve inputs/ as immutable.
- **Acceptance Criteria:** Outer reference docs preserved in project/docs/; stale superseded files deleted; external inputs untouched
- **Dependencies:** T360
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Files copied, deleted, and verified via Test-Path

### T362 — Fix Scenario Taxonomy Inconsistencies
- **Priority:** HIGH
- **Category:** Scenario
- **Description:** Correct blast_radius in all 14 djangocms and saleor scenario YAMLs to use taxonomy-standard values (localized, moderate, cross_cutting)
- **Acceptance Criteria:** All 24 scenarios have blast_radius matching naming convention and SCENARIO_TAXONOMY.md
- **Dependencies:** T361
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** grep of blast_radius across all 24 scenario YAMLs shows only standard values

### T363 — Update .gitignore and Validate Project Tree
- **Priority:** HIGH
- **Category:** Structure
- **Description:** Deduplicate .gitignore, add runs/, add report exceptions. Validate full project tree structure.
- **Acceptance Criteria:** .gitignore clean; project tree has 18 docs, 29 benchmark_data, scaffold-only src/benchmark
- **Dependencies:** T362
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** git status clean; tree validated via Get-ChildItem

### T364 — Create Baseline Commit and Update State Files
- **Priority:** HIGH
- **Category:** VCS
- **Description:** Create git commit for all Phase 3, 3.5, 3.6 work. Create reports/PHASE3_6_STRUCTURE_REMEDIATION_REPORT.md. Update SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, reports/latest_phase_report.md.
- **Acceptance Criteria:** Baseline commit created (845ba49); all state files consistent; working tree clean
- **Dependencies:** T363
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** git log, git status, state file diffs

## Phase 3.7 — Canonical Structure Remediation and Selective-Update Ledger

### T371 — Merge Audit Documentation to Main
- **Priority:** HIGH
- **Category:** VCS
- **Description:** Merge `audit/canonical-project-architecture` into `main` using `--no-ff`. Validate merge contains only documentation/reports.
- **Acceptance Criteria:** Merge commit on main; 10 audit docs merged
- **Dependencies:** T364
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Merge commit `9dbd49f` on main

### T372 — Create Bundle Build Script
- **Priority:** HIGH
- **Category:** Structure
- **Description:** Create `scripts/build_upload_bundle.py` that builds `kaggle_upload/` from canonical sources only, excludes forbidden items, generates SHA-256 manifests, verifies all derivatives.
- **Acceptance Criteria:** Script runs successfully; produces valid bundle
- **Dependencies:** T371
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** `scripts/build_upload_bundle.py` exists and passes verification

### T373 — Populate and Validate Inner Data Bundle
- **Priority:** HIGH
- **Category:** Structure
- **Description:** Build bundle with 24 scenarios, 2 manifests, 3 repository profiles (29 files). Verify all SHA-256 match canonical sources.
- **Acceptance Criteria:** 29 files in `kaggle_upload/data/`; all checksums match
- **Dependencies:** T372
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Bundle verification passed

### T374 — Clean Inner Code Bundle
- **Priority:** HIGH
- **Category:** Structure
- **Description:** Verify no `.git/`, `__pycache__/`, `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`, `*.egg-info/` in `kaggle_upload/code/`. Package tree is `kaggle_upload/code/src/benchmark/`.
- **Acceptance Criteria:** No forbidden items; correct package structure
- **Dependencies:** T373
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Forbidden check passed; tree validated

### T375 — Remove Disposable Artifacts
- **Priority:** MEDIUM
- **Category:** Structure
- **Description:** Add `_auto_resume_temp/`, `benchmark-results.zip`, `**/__pycache__/`, `*.pyc`, `*.egg-info/` to `.gitignore`. Remove `_auto_resume_temp/` and `benchmark-results.zip` from working tree.
- **Acceptance Criteria:** .gitignore updated; temp files deleted
- **Dependencies:** T374
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Files deleted; .gitignore updated

### T376 — Update Architecture Documentation
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Update PROPOSED_CANONICAL_PROJECT_STRUCTURE.md (IMPLEMENTED), IMPLEMENTED_ARCHITECTURE_BASELINE.md (bundle automation), SELECTIVE_PROJECT_UPDATE_POLICY.md (ADOPTED + ledger), SOURCE_OF_TRUTH_MATRIX.md (new classifications), SYSTEM_STATE.md, START_HERE.md, PROJECT_HANDOFF.md.
- **Acceptance Criteria:** All docs reflect remediated state
- **Dependencies:** T375
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Documentation updated

### T377 — Establish Selective-Update Ledger
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create `project/selective_updates/` with README.md, CHANGE_INDEX.md, ARTIFACT_IMPACT_MAP.md, templates/CHANGE_RECORD_TEMPLATE.md, records/SU-0001-*.md, metrics/change_metrics.jsonl. Record SU-0001 for this remediation.
- **Acceptance Criteria:** Ledger created; SU-0001 recorded
- **Dependencies:** T376
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Ledger files created

### T378 — Verify and Delete Outer Duplicates
- **Priority:** HIGH
- **Category:** Structure
- **Description:** Verify outer `kaggle_upload/` and `docs/` match inner canonical sources. Delete outer duplicates. Provide PowerShell commands if auto-delete fails.
- **Acceptance Criteria:** Outer duplicates deleted or commands provided
- **Dependencies:** T377
- **Status:** PENDING
- **Owner:** OpenCode
- **Evidence:** Verification complete

### T379 — Run Quality Gates and Finalize
- **Priority:** HIGH
- **Category:** Validation
- **Description:** Run bundle builder, CLI help, pytest, ruff, mypy, pip check. Validate bundle imports, scenario loading, manifests, ledger links, frozen protocol checksums.
- **Acceptance Criteria:** All quality gates pass
- **Dependencies:** T378
- **Status:** PENDING
- **Owner:** OpenCode
- **Evidence:** Gate results recorded

### T380 — Merge Remediation Branch and Report
- **Priority:** HIGH
- **Category:** VCS
- **Description:** Commit all changes on `chore/canonical-project-remediation`. Merge to `main` with `--no-ff`. Create final remediation report.
- **Acceptance Criteria:** Merge commit on main; final report generated
- **Dependencies:** T379
- **Status:** PENDING
- **Owner:** OpenCode
- **Evidence:** Final commit hash

### K001 — Selective runs_dir NameError Fix (SU-0002)
- **Priority:** HIGH
- **Category:** Bugfix
- **Description:** Fix NameError in `seven_arm_benchmark.py` where `runs_dir` was used but not defined in START_NEW path (line 957). Correct variable is `output_dir`. Minimal scope: affected file, regression tests in test_cli.py, bundle rebuild, ledger record.
- **Acceptance Criteria:** Defect fixed; regression tests pass; bundle rebuilt; SU-0002 record created
- **Dependencies:** T380
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** test_start_new_path_no_nameerror and test_resume_path_no_nameerror pass; bundle rebuilt

### T401 — Implement Enums
- **Priority:** HIGH
- **Category:** Core
- **Description:** Implement 6 StrEnum classes (ActionKind, ArtifactType, BlastRadius, RunStatus, FailureKind, EvidenceTier)
- **Acceptance Criteria:** All enums have stable string values; JSON/YAML serializable
- **Dependencies:** T364
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/core/enums.py, tests/unit/test_enums.py (8 tests)

### T402 — Implement Exception Hierarchy
- **Priority:** HIGH
- **Category:** Core
- **Description:** Implement typed exception hierarchy rooted at BenchmarkError with context dict support
- **Acceptance Criteria:** All 12 classes properly subclassed; context preserved in repr
- **Dependencies:** T401
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/core/exceptions.py, tests/unit/test_exceptions.py (15 tests)

### T403 — Implement Domain Models
- **Priority:** HIGH
- **Category:** Core
- **Description:** Implement 24 frozen dataclass models with post-init validation
- **Acceptance Criteria:** All models frozen; validation rejects empty strings/negative values/duplicates
- **Dependencies:** T401, T402
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/core/models.py, tests/unit/test_models.py (34 tests)

### T404 — Implement Protocol Interfaces
- **Priority:** HIGH
- **Category:** Core
- **Description:** Implement 11 runtime-checkable typing.Protocol interfaces
- **Acceptance Criteria:** All protocols have correct method signatures; conformance checkable via isinstance
- **Dependencies:** T403
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/core/protocols.py, tests/contract/test_protocol_conformance.py (11 tests)

### T405 — Implement Registry
- **Priority:** HIGH
- **Category:** Core
- **Description:** Implement generic Registry[T] with register, create, get, list_names, freeze
- **Acceptance Criteria:** Duplicate/unknown raise typed errors; freeze prevents registration
- **Dependencies:** T402
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/core/registry.py, tests/unit/test_registry.py (9 tests)

### T406 — Implement ExecutionContext
- **Priority:** HIGH
- **Category:** Core
- **Description:** Implement ExecutionContext with controlled immutability
- **Acceptance Criteria:** Defaults correct; private_evaluation_access defaults to False; empty strings rejected
- **Dependencies:** T403
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/core/context.py, tests/unit/test_context.py (9 tests)

### T407 — Implement Config Models
- **Priority:** HIGH
- **Category:** Config
- **Description:** Implement 7 Pydantic v2 config models with cross-field validation
- **Acceptance Criteria:** Kaggle backend rejected in local mode; budgets positive; YAML round-trip works
- **Dependencies:** T403
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/config/models.py, tests/unit/test_config_models.py (16 tests)

### T408 — Implement Config Loader and Validation
- **Priority:** HIGH
- **Category:** Config
- **Description:** Implement YAML config loader and structural validation
- **Acceptance Criteria:** Valid configs load; invalid configs raise typed errors
- **Dependencies:** T407
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/config/loader.py, src/benchmark/config/validation.py

### T409 — Create Package Setup
- **Priority:** HIGH
- **Category:** Build
- **Description:** Create pyproject.toml with project metadata, ruff/mypy/pytest configuration
- **Acceptance Criteria:** Package installable via pip install -e .; all linters runnable
- **Dependencies:** T401–T408
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** pyproject.toml

### T410 — Write Import Isolation Tests
- **Priority:** HIGH
- **Category:** Tests
- **Description:** Write subprocess test verifying torch/transformers not imported by benchmark package
- **Acceptance Criteria:** All 3 isolation tests pass
- **Dependencies:** T409
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** tests/test_import_isolation.py (3 tests)

### T411 — Run Quality Gates
- **Priority:** HIGH
- **Category:** Validation
- **Description:** Run ruff, mypy, pytest, pip check; fix all issues
- **Acceptance Criteria:** All quality gates pass
- **Dependencies:** T410
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** All 111 tests pass; ruff 0 violations; mypy 0 errors; pip check clean

### T412 — Create Documentation and Reports
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create docs/PHASE4A_DOMAIN_MODEL_REFERENCE.md and reports/PHASE4A_DOMAIN_MODELS_REPORT.md
- **Acceptance Criteria:** Both files present with complete content
- **Dependencies:** T411
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Both files written to disk

### T413 — Update State Files
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Update SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, reports/latest_phase_report.md for Phase 4A
- **Acceptance Criteria:** All state files consistent; Phase 4B as exact next task
- **Dependencies:** T412
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Edits to all four state files

## Phase 4B — Loaders and Validation

### T4B01 — Implement RepositoryLoaderBase
- **Priority:** HIGH
- **Category:** Repositories
- **Description:** Implement abstract base with resolve_identity and resolve_snapshot in src/benchmark/repositories/base.py
- **Acceptance Criteria:** Base class defines interface; subclasses can override resolve_identity and resolve_snapshot
- **Dependencies:** T413
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/repositories/base.py

### T4B02 — Implement Manifest Models
- **Priority:** HIGH
- **Category:** Repositories
- **Description:** Implement RepositoryManifest, RepositoryVersionEntry, RepositoryProfile, ManifestCollection (frozen dataclasses) in src/benchmark/repositories/manifest.py
- **Acceptance Criteria:** All models frozen; validation rejects empties; duplicate detection in collection
- **Dependencies:** T4B01
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/repositories/manifest.py

### T4B03 — Implement RepositoryLoader
- **Priority:** HIGH
- **Category:** Repositories
- **Description:** Implement YAML loading from manifests/ and repository_profiles/ in src/benchmark/repositories/loader.py
- **Acceptance Criteria:** Loads real YAML files; builds ManifestCollection; raises typed errors on missing/invalid files
- **Dependencies:** T4B02
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/repositories/loader.py

### T4B04 — Implement Snapshot Metadata and Validation
- **Priority:** HIGH
- **Category:** Repositories
- **Description:** Implement SnapshotMetadata, create_snapshot_metadata(), validate_snapshot() in src/benchmark/repositories/snapshot.py
- **Acceptance Criteria:** Metadata creation validates fields; snapshot validation reports issues without raising
- **Dependencies:** T4B03
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/repositories/snapshot.py

### T4B05 — Implement Workspace Isolation
- **Priority:** HIGH
- **Category:** Repositories
- **Description:** Implement WorkspacePath, validate_workspace_path(), check_isolation() in src/benchmark/repositories/workspace.py
- **Acceptance Criteria:** Isolation check prevents same-path and nested-path violations; nonexistent paths allowed
- **Dependencies:** T4B04
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/repositories/workspace.py

### T4B06 — Implement Repositories Package Init
- **Priority:** HIGH
- **Category:** Repositories
- **Description:** Create src/benchmark/repositories/__init__.py with public exports
- **Acceptance Criteria:** All public classes and functions exported
- **Dependencies:** T4B05
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/repositories/__init__.py

### T4B07 — Implement ScenarioModel
- **Priority:** HIGH
- **Category:** Scenarios
- **Description:** Implement ScenarioModel dataclass with to_core_scenario() and dual-format expected_actions parsing in src/benchmark/scenarios/models.py
- **Acceptance Criteria:** Both standard and action-grouped YAML formats parsed; deduplication; conversion to core Scenario
- **Dependencies:** T413
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/scenarios/models.py

### T4B08 — Implement ScenarioLoader
- **Priority:** HIGH
- **Category:** Scenarios
- **Description:** Implement ScenarioLoader with load_all() and load_by_repository() in src/benchmark/scenarios/loader.py
- **Acceptance Criteria:** Loads all 24 real scenario YAMLs; raises typed errors on missing/invalid files
- **Dependencies:** T4B07
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/scenarios/loader.py

### T4B09 — Implement ScenarioValidator
- **Priority:** HIGH
- **Category:** Scenarios
- **Description:** Implement ScenarioValidator with required field checks and duplicate action detection in src/benchmark/scenarios/validator.py
- **Acceptance Criteria:** Validates required fields; detects duplicate expected_actions; validate_all returns all errors
- **Dependencies:** T4B08
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/scenarios/validator.py

### T4B10 — Implement ScenarioSequencer
- **Priority:** HIGH
- **Category:** Scenarios
- **Description:** Implement ScenarioSequencer ordering scenarios by blast_radius (localized → moderate → cross_cutting) in src/benchmark/scenarios/sequencing.py
- **Acceptance Criteria:** Ordering correct; ties broken by scenario_id; empty list handled; by-repository filtering works
- **Dependencies:** T4B09
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/scenarios/sequencing.py

### T4B11 — Implement Scenarios Package Init
- **Priority:** HIGH
- **Category:** Scenarios
- **Description:** Create src/benchmark/scenarios/__init__.py with public exports
- **Acceptance Criteria:** All public classes and functions exported
- **Dependencies:** T4B10
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/scenarios/__init__.py

### T4B12 — Write Repository Tests
- **Priority:** HIGH
- **Category:** Tests
- **Description:** Write unit tests for manifest (15), loader (8), snapshot (12), workspace (9); integration test (6)
- **Acceptance Criteria:** All 50 repository tests pass
- **Dependencies:** T4B06
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 4 unit + 1 integration test files (50 tests)

### T4B13 — Write Scenario Tests
- **Priority:** HIGH
- **Category:** Tests
- **Description:** Write unit tests for models (11), loader (9), validator (7), sequencing (5); integration test (5)
- **Acceptance Criteria:** All 37 scenario tests pass
- **Dependencies:** T4B11
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 4 unit + 1 integration test files (37 tests)

### T4B14 — Write Loaders Contract Tests
- **Priority:** HIGH
- **Category:** Tests
- **Description:** Write contract tests verifying RepositoryLoader and ScenarioLoader conform to RepositoryAdapter and ScenarioProvider protocols
- **Acceptance Criteria:** All 4 contract tests pass
- **Dependencies:** T4B12, T4B13
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** tests/contract/test_loaders_contract.py (4 tests)

### T4B15 — Run Quality Gates
- **Priority:** HIGH
- **Category:** Validation
- **Description:** Run ruff, mypy, pytest, pip check; fix all issues
- **Acceptance Criteria:** All quality gates pass; 206 total tests
- **Dependencies:** T4B14
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 206/206 tests pass; ruff 0 violations; mypy 0 errors; pip check clean

### T4B16 — Create Documentation and Reports
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create docs/PHASE4B_LOADERS_AND_VALIDATION_REFERENCE.md and reports/PHASE4B_LOADERS_AND_VALIDATION_REPORT.md
- **Acceptance Criteria:** Both files present with complete content
- **Dependencies:** T4B15
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Both files written to disk

### T4B17 — Update State Files
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Update SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, reports/latest_phase_report.md for Phase 4B
- **Acceptance Criteria:** All state files consistent; Phase 4C as exact next task
- **Dependencies:** T4B16
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Edits to all four state files

## Phase 4C — Model Backends

### T4C01 — Create LLM Package Structure
- **Priority:** HIGH
- **Category:** LLM
- **Description:** Create src/benchmark/llm/ package with __init__.py, base.py, mock_backend.py, dry_run_backend.py, kaggle_qwen_backend.py
- **Acceptance Criteria:** Package imports without torch or transformers
- **Dependencies:** T4B17
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Package exists; import isolation verified

### T4C02 — Implement Backend Base and Registry Integration
- **Priority:** HIGH
- **Category:** LLM
- **Description:** Implement BackendFactory class that registers MockLLMBackend, DryRunLLMBackend, KaggleQwenBackend in a Registry and creates them by name
- **Acceptance Criteria:** Factory creates correct backend given name; unknown names raise typed errors
- **Dependencies:** T4C01
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/llm/ and associated tests

### T4C03 — Implement MockLLMBackend
- **Priority:** HIGH
- **Category:** LLM
- **Description:** Implement deterministic mock backend returning fixture responses
- **Acceptance Criteria:** Returns configured response; LLMResponse with correct token_usage; deterministic
- **Dependencies:** T4C01
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/llm/mock_backend.py

### T4C04 — Implement DryRunLLMBackend
- **Priority:** HIGH
- **Category:** LLM
- **Description:** Implement dry-run backend that loads fixture responses from files
- **Acceptance Criteria:** Reads responses from JSON files; falls back to default response; never calls an API
- **Dependencies:** T4C01
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/llm/dry_run_backend.py

### T4C05 — Implement KaggleQwenBackend Skeleton
- **Priority:** HIGH
- **Category:** LLM
- **Description:** Implement safe skeleton with lazy torch/transformers imports; raises informative error if called outside Kaggle
- **Acceptance Criteria:** Imports without torch (lazy); generates sensible error message when called locally; actual inference code deferred to Kaggle
- **Dependencies:** T4C01
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** src/benchmark/llm/kaggle_qwen_backend.py; import test passes without torch

### T4C06 — Write Backend Tests
- **Priority:** HIGH
- **Category:** Tests
- **Description:** Write tests for mock backend deterministic output; dry-run fixture loading; import test that Kaggle backend does NOT require torch; factory integration tests
- **Acceptance Criteria:** All tests pass; import isolation verified
- **Dependencies:** T4C02, T4C03, T4C04, T4C05
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Test files

### T4C07 — Run Quality Gates
- **Priority:** HIGH
- **Category:** Validation
- **Description:** Run ruff, mypy, pytest, pip check; fix all issues
- **Acceptance Criteria:** All quality gates pass
- **Dependencies:** T4C06
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 229/229 tests pass; ruff 0 violations; mypy 0 errors; pip check clean

### T4C08 — Create Documentation and Reports
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create docs/PHASE4C_MODEL_BACKENDS_REFERENCE.md and reports/PHASE4C_MODEL_BACKENDS_REPORT.md
- **Acceptance Criteria:** Both files present with complete content
- **Dependencies:** T4C07
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Both files written to disk

### T4C09 — Update State Files
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Update SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, reports/latest_phase_report.md for Phase 4C
- **Acceptance Criteria:** All state files consistent; Phase 4D as exact next task
- **Dependencies:** T4C08
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Edits to all four state files

### T4C10 — Branch Workflow (Commit, Push, Merge)
- **Priority:** HIGH
- **Category:** VCS
- **Description:** Create phase/4c-model-backends branch; commit all Phase 4C work; push branch; safe merge to main; push main
- **Acceptance Criteria:** Branch created, committed, pushed, merged; main clean and synced with origin
- **Dependencies:** T4C07
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Git log shows branch/merge/push

## Phase 4D — Execution Core (COMPLETE)

### T4D01 — Create Execution Package Structure
- **Priority:** HIGH
- **Category:** Execution
- **Description:** Create `src/benchmark/execution/` package with `__init__.py`, `budgets.py`, `state_machine.py`, `repair.py`, `isolation.py`, `runner.py`, `pipeline.py`
- **Acceptance Criteria:** Package imports without torch or transformers
- **Dependencies:** T4C10
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** `src/benchmark/execution/` exists with 7 files

### T4D02 — Implement BudgetManager
- **Priority:** HIGH
- **Category:** Execution
- **Description:** Implement BudgetManager with injectable Clock, max_attempts/max_tokens/timeout enforcement, per-attempt tracking
- **Acceptance Criteria:** Cannot exceed max_attempts; token budget enforced; timeout detection works; reset clears state
- **Dependencies:** T4D01
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 14 tests in `test_budgets.py`

### T4D03 — Implement RunStateMachine
- **Priority:** HIGH
- **Category:** Execution
- **Description:** Implement RunStateMachine with 6 states (prepared→running→succeeded/failed/timed_out/cancelled) and terminal-state protection
- **Acceptance Criteria:** All valid transitions accepted; invalid transitions raise InvalidTransitionError; terminal states block further transitions
- **Dependencies:** T4D01
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 13 tests in `test_state_machine.py`

### T4D04 — Implement RepairLoop
- **Priority:** HIGH
- **Category:** Execution
- **Description:** Implement RepairLoop with 1+2 attempt lifecycle, configurable FailureClassifier, BudgetManager integration
- **Acceptance Criteria:** First-attempt success returns immediately; failures retry up to budget; BenchmarkError handling; custom classifier support
- **Dependencies:** T4D02, T4D03
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 8 tests in `test_repair.py`

### T4D05 — Implement IsolationContext
- **Priority:** HIGH
- **Category:** Execution
- **Description:** Implement IsolationContext wrapping Phase 4B workspace utilities with private data detection
- **Acceptance Criteria:** Workspace isolation verified; private paths detected; run/temp directories created
- **Dependencies:** T4D01
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 9 tests in `test_isolation.py`

### T4D06 — Implement BenchmarkRunner
- **Priority:** HIGH
- **Category:** Execution
- **Description:** Implement BenchmarkRunner coordinating ImpactStrategy + LLMBackend + IsolationContext into RunRecord
- **Acceptance Criteria:** Full run lifecycle; dry_run returns success with 0 duration; isolation failure returns failure record; budgets honored
- **Dependencies:** T4D02, T4D03, T4D04, T4D05
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 7 tests in `test_runner.py`

### T4D07 — Implement BenchmarkPipeline
- **Priority:** HIGH
- **Category:** Execution
- **Description:** Implement BenchmarkPipeline with single/batch/dry-run modes, PipelineResult aggregation
- **Acceptance Criteria:** Single scenario runs; batch runs all; dry_run skips strategy; failure tracking works
- **Dependencies:** T4D06
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 6 tests in `test_pipeline.py`

### T4D08 — Run Quality Gates
- **Priority:** HIGH
- **Category:** Validation
- **Description:** Run ruff, mypy, pytest, pip check; fix all issues
- **Acceptance Criteria:** All quality gates pass; 288 total tests
- **Dependencies:** T4D01–T4D07
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 288/288 tests pass; ruff 0 violations; mypy 0 errors; pip check clean

### T4D09 — Create Documentation and Reports
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create docs/PHASE4D_EXECUTION_CORE_REFERENCE.md and reports/PHASE4D_EXECUTION_CORE_REPORT.md
- **Acceptance Criteria:** Both files present with complete content
- **Dependencies:** T4D08
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Both files written to disk

### T4D10 — Update State Files
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Update SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, reports/latest_phase_report.md for Phase 4D
- **Acceptance Criteria:** All state files consistent; Phase 4E as exact next task
- **Dependencies:** T4D09
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Edits to all four state files

### T4D11 — Branch Workflow (Commit, Push, Merge)
- **Priority:** HIGH
- **Category:** VCS
- **Description:** Create phase/4d-execution-core branch; commit all Phase 4D work; push branch; safe merge to main; push main
- **Acceptance Criteria:** Branch created, committed, pushed, merged; main clean and synced with origin
- **Dependencies:** T4D08
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Git log shows branch/merge/push

## TD-1 — Runner Protocol Alignment (COMPLETE)

### TD1-01 — Fix BenchmarkRunner Protocol Violation
- **Priority:** HIGH
- **Category:** Engineering
- **Description:** Fix `BenchmarkRunner._run_attempt` to construct `RepositorySnapshot`, `RequirementChange`, and `ArtifactUniverse` from `Scenario` before calling `strategy.analyze_impact()`. Remove all `# type: ignore[arg-type]` from runner path.
- **Acceptance Criteria:** No `type: ignore` in runner.py; correct domain objects passed to strategy; all quality gates pass
- **Dependencies:** T4D11
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 289/289 tests pass; ruff 0 violations; mypy 0 errors; pip check clean

### TD1-02 — Add Domain Object Extraction Test
- **Priority:** HIGH
- **Category:** Tests
- **Description:** Add test verifying `_run_attempt` constructs correct domain objects (RepositorySnapshot, RequirementChange, ArtifactUniverse) from Scenario
- **Acceptance Criteria:** Test verifies type correctness and field mapping
- **Dependencies:** TD1-01
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** `test_run_extracts_correct_domain_objects` passes

### TD1-03 — Create Remediation Report
- **Priority:** MEDIUM
- **Category:** Documentation
- **Description:** Create `reports/TD1_REMEDIATION_REPORT.md` documenting root cause, files changed, and protocol alignment
- **Acceptance Criteria:** Report covers all required sections
- **Dependencies:** TD1-01
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** `reports/TD1_REMEDIATION_REPORT.md`

## Phase 4E — Impact Strategies (COMPLETE)

### T4E01 — Create Strategies Package Structure
- **Priority:** HIGH
- **Category:** Strategies
- **Description:** Create `src/benchmark/strategies/` package with `__init__.py`, `registry.py`, `validation.py`, and concrete strategy modules for all 7 arms: monolithic, agent, selective, compiled_ai, delta_mcp, incr_rtl, code_plan
- **Acceptance Criteria:** Package imports cleanly; each strategy module implements ImpactStrategy protocol; registry supports freeze/lookup
- **Dependencies:** T4D11
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 9 files created in `src/benchmark/strategies/`

### T4E02 — Create Graph Package
- **Priority:** HIGH
- **Category:** Graph
- **Description:** Create `src/benchmark/graph/` package with `__init__.py`, `models.py`, `builder.py` for dependency graph construction and traversal
- **Acceptance Criteria:** Graph builds correctly from scenarios; traversal produces correct impacted artifacts
- **Dependencies:** T4E01
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 3 files created in `src/benchmark/graph/`

### T4E03 — Create Selection Package
- **Priority:** HIGH
- **Category:** Selection
- **Description:** Create `src/benchmark/selection/` package with `__init__.py`, `planner.py` for artifact selection and regeneration planning
- **Acceptance Criteria:** Artifact selection returns correct impacted files; regeneration plan follows correct ordering
- **Dependencies:** T4E02
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 2 files created in `src/benchmark/selection/`

### T4E04 — Write Strategy Tests
- **Priority:** HIGH
- **Category:** Tests
- **Description:** Write tests for all 7 strategy implementations: protocol conformance, registry lifecycle, strategy validation, edge cases
- **Acceptance Criteria:** All strategy tests pass; coverage for all 7 arms
- **Dependencies:** T4E01
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 21 tests in `tests/unit/strategies/test_strategies.py`

### T4E05 — Write Graph and Selection Tests
- **Priority:** HIGH
- **Category:** Tests
- **Description:** Write tests for graph construction, traversal, artifact selection, regeneration planning
- **Acceptance Criteria:** All graph and selection tests pass
- **Dependencies:** T4E02, T4E03
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 16 graph tests + 6 selection tests; 22 total in graph/selection

### T4E06 — Run Quality Gates
- **Priority:** HIGH
- **Category:** Validation
- **Description:** Run ruff, mypy, pytest, pip check; fix all issues
- **Acceptance Criteria:** All quality gates pass
- **Dependencies:** T4E04, T4E05
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 332/332 tests pass; ruff 0 violations; mypy 0 errors; pip check clean

### T4E07 — Create Documentation and Reports
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create `reports/PHASE4E_IMPACT_STRATEGIES_REPORT.md`
- **Acceptance Criteria:** Report file present with complete content
- **Dependencies:** T4E06
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** `reports/PHASE4E_IMPACT_STRATEGIES_REPORT.md` written to disk

### T4E08 — Update State Files
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Update SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, reports/latest_phase_report.md for Phase 4E
- **Acceptance Criteria:** All state files consistent; Phase 4F as exact next task
- **Dependencies:** T4E07
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Edits to SYSTEM_STATE.md, TODO.md, DECISION_LOG.md (D017)

### T4E09 — Branch Workflow (Commit, Push, Merge)
- **Priority:** HIGH
- **Category:** VCS
- **Description:** Commit all Phase 4E work; push branch; safe merge to main; push main
- **Acceptance Criteria:** Branch committed, pushed, merged; main clean and synced with origin
- **Dependencies:** T4E06
- **Status:** PENDING
- **Owner:** OpenCode
- **Evidence:** Git log shows commit/merge/push

## Phase 4F — Evaluation Engine (COMPLETE)

### T4F01 — Create Evaluation Package
- **Priority:** HIGH
- **Category:** Evaluation
- **Description:** Create `src/benchmark/evaluation/` package with `__init__.py`, `engine.py`, `metrics.py` for metric computation and evaluation orchestration
- **Acceptance Criteria:** Package imports cleanly; evaluation engine processes run records; all metrics computed correctly
- **Dependencies:** T4E09
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** `src/benchmark/evaluation/` exists with all modules

### T4F02 — Create Comparison Package
- **Priority:** HIGH
- **Category:** Comparison
- **Description:** Create `src/benchmark/comparison/` package with `__init__.py`, `ground_truth.py`, `aggregator.py` for ground truth comparison and result aggregation
- **Acceptance Criteria:** Ground truth comparison matches expectations; results aggregated across scenarios and repositories
- **Dependencies:** T4F01
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** `src/benchmark/comparison/` exists with all modules

### T4F03 — Create Statistics Package
- **Priority:** HIGH
- **Category:** Statistics
- **Description:** Create `src/benchmark/statistics/` package with `__init__.py`, `analysis.py`, `reporting.py` for statistical analysis, confidence intervals, effect sizes, and publication-ready export
- **Acceptance Criteria:** Statistical analysis produces valid confidence intervals; effect sizes computed correctly; notebook-ready and publication-table output formats work
- **Dependencies:** T4F02
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** `src/benchmark/statistics/` exists with all modules

### T4F04 — Write Evaluation Tests
- **Priority:** HIGH
- **Category:** Tests
- **Description:** Write tests for metric computation, ground truth comparison, result aggregation, statistical analysis, confidence intervals, effect sizes, notebook export, publication tables
- **Acceptance Criteria:** All evaluation tests pass
- **Dependencies:** T4F01, T4F02, T4F03
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Test files under `tests/unit/evaluation/`, `tests/unit/comparison/`, `tests/unit/statistics/`

### T4F05 — Run Quality Gates
- **Priority:** HIGH
- **Category:** Validation
- **Description:** Run ruff, mypy, pytest, pip check; fix all issues
- **Acceptance Criteria:** All quality gates pass
- **Dependencies:** T4F04
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** All tests pass (405/405); ruff 0 violations; mypy 0 errors; pip check clean

### T4F06 — Create Documentation and Reports
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Create `docs/PHASE4F_EVALUATION_ENGINE_REFERENCE.md` and `reports/PHASE4F_EVALUATION_ENGINE_REPORT.md`
- **Acceptance Criteria:** Both files present with complete content
- **Dependencies:** T4F05
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Both files written to disk

### T4F07 — Update State Files
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Update SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, reports/latest_phase_report.md for Phase 4F
- **Acceptance Criteria:** All state files consistent; Phase 4F recorded as COMPLETE
- **Dependencies:** T4F06
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Edits to all four state files (this update)

### T4F08 — Branch Workflow (Commit, Push, Merge)
- **Priority:** HIGH
- **Category:** VCS
- **Description:** Create `phase/4f-evaluation-engine` branch; commit all Phase 4F work; push branch; safe merge to main; push main
- **Acceptance Criteria:** Branch created, committed, pushed, merged; main clean and synced with origin
- **Dependencies:** T4F05
- **Status:** PENDING
- **Owner:** OpenCode
- **Evidence:** Git log shows branch/merge/push

## Phase 4F.1 — Scientific Evaluation Remediation (COMPLETE)

### T4F1-01 — Implement `aggregate_run_records`
- **Priority:** HIGH
- **Category:** Aggregation
- **Description:** Replace stub `aggregate_run_records` with full micro/macro aggregation
- **Acceptance Criteria:** Micro preserves identifiers; macro uses equal-weight repo averaging; conditional notes for failed runs; deterministic ordering
- **Dependencies:** T4F08
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** `src/benchmark/comparison/aggregator.py`, 8 tests in `TestAggregateRunRecords`

### T4F1-02 — Implement Paired Analysis for H1
- **Priority:** HIGH
- **Category:** Statistics
- **Description:** Implement `paired_bootstrap_ci()` and `paired_compare()` matching on (repository, scenario, repetition)
- **Acceptance Criteria:** Paired CI matches on cells; unmatched pairs reported; paired vs pooled gives different results
- **Dependencies:** T4F1-01
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** `src/benchmark/statistics/analysis.py`, 3 tests in `TestPairedAnalysis`

### T4F1-03 — Implement BH and Holm Corrections
- **Priority:** HIGH
- **Category:** Statistics
- **Description:** Implement `benjamini_hochberg()` and `holm_correction()` for DA-14
- **Acceptance Criteria:** BH produces correct adjusted p-values; Holm uses step-down Bonferroni; both preserve ordering
- **Dependencies:** T4F1-02
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** `src/benchmark/statistics/analysis.py`, 10 tests (5 BH + 5 Holm)

### T4F1-04 — Implement NI Sensitivity Margins
- **Priority:** HIGH
- **Category:** Statistics
- **Description:** Extend `non_inferiority_test()` with `sensitivity_margins` parameter (0.03, 0.10)
- **Acceptance Criteria:** Returns sensitivity dict; boundary detection correct; rejects unequal lengths
- **Dependencies:** T4F1-03
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** `src/benchmark/statistics/analysis.py`, 4 tests in `TestNonInferioritySensitivity`

### T4F1-05 — Generalize Binomial CI
- **Priority:** HIGH
- **Category:** Statistics
- **Description:** Replace hardcoded z-scores in `binomial_ci` with `scipy.stats.norm.ppf`
- **Acceptance Criteria:** Works at any confidence level (90%, 95%, 99%); rejects invalid confidence levels
- **Dependencies:** T4F1-04
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** `src/benchmark/statistics/confidence_intervals.py`, 5 tests in `TestBinomialCIGeneralized`

### T4F1-06 — Run Quality Gates
- **Priority:** HIGH
- **Category:** Validation
- **Description:** Run ruff, mypy, pytest, pip check; fix all issues
- **Acceptance Criteria:** All quality gates pass; 441 total tests
- **Dependencies:** T4F1-05
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 441/441 tests pass; ruff 0 violations; mypy 0 errors (src); pip check clean

### T4F1-07 — Create Documentation
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Update audit report coverage matrix; write remediation report
- **Acceptance Criteria:** Audit report updated; remediation report present
- **Dependencies:** T4F1-06
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** `reports/PHASE4F_INDEPENDENT_SCIENTIFIC_AUDIT.md`, `reports/PHASE4F_1_SCIENTIFIC_REMEDIATION_REPORT.md`

### T4F1-08 — Update State Files
- **Priority:** HIGH
- **Category:** Documentation
- **Description:** Update SYSTEM_STATE.md, TODO.md, DECISION_LOG.md, latest_phase_report.md, PROJECT_HEALTH_REPORT.md
- **Acceptance Criteria:** All state files consistent; Phase 4F.1 recorded as COMPLETE
- **Dependencies:** T4F1-07
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Edits to all state files

### T4F1-09 — Branch Workflow (Commit, Push, Merge)
- **Priority:** HIGH
- **Category:** VCS
- **Description:** Commit all Phase 4F.1 work; push branch; safe merge to main; verify gates on main; push main
- **Acceptance Criteria:** Branch merged; main clean and synced with origin; all gates pass
- **Dependencies:** T4F1-06
- **Status:** PENDING
- **Owner:** OpenCode
- **Evidence:** Git log shows branch/merge/push

## Kaggle Smoke Pass (Engineering Validation)

### K001 — Fix Real Qwen Failure Propagation
- **Priority:** HIGH
- **Category:** Engineering Fix
- **Description:** Fix `agent.py` blanket except, add `token_usage` fields to models, tag smoke strategies `stage=smoke`, preserve prediction errors in runner.
- **Acceptance Criteria:** Qwen errors propagated; token_usage tracked; smoke strategies execute only smoke scenarios.
- **Dependencies:** None
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 8 files changed; failure propagation fix merged at `b08bb55`

### K002 — Fix Graph Wiring for Graph-Dependent Strategies
- **Priority:** HIGH
- **Category:** Engineering Fix
- **Description:** Wire ProfileGraphBuilder, use capabilities design, create NullLLMBackend, inject graph into selective/compiled_ai strategies.
- **Acceptance Criteria:** All 7 arms succeed; graph-dependent strategies receive valid graph.
- **Dependencies:** K001
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** 12+ files changed; graph wiring fix merged at `e8aefc5`

### K003 — Kaggle Real Smoke Execution
- **Priority:** HIGH
- **Category:** Deployment
- **Description:** Execute real smoke on Kaggle with Qwen2.5-Coder-7B-Instruct. All 7 arms × 1 scenario.
- **Acceptance Criteria:** All 7 arms complete; Qwen inference confirmed; token usage recorded.
- **Dependencies:** K002
- **Status:** COMPLETE
- **Owner:** OpenCode
- **Evidence:** Tag `v0.7.0-smoke-passed` at `0c58250`; smoke passed twice

### K004 — Implement Checkpoint/Resume for Long-Running Profiles
- **Priority:** HIGH
- **Category:** Engineering
- **Description:** Implement checkpoint/resume support in pipeline/runner so long profiles (pilot ~2-3h, research ~6-9h) survive Kaggle 9h session limits.
- **Acceptance Criteria:** Pipeline can save intermediate state and resume from last completed run.
- **Dependencies:** K003
- **Status:** PENDING
- **Owner:** OpenCode
- **Evidence:** Not yet implemented

### K005 — Run Pilot Experiment
- **Priority:** MEDIUM
- **Category:** Scientific
- **Description:** Execute pilot profile on Kaggle: 12 scenarios, agent+selective, 2 reps. Descriptive findings only.
- **Acceptance Criteria:** Pilot completes; results are non-publication.
- **Dependencies:** K004
- **Status:** PENDING
- **Owner:** OpenCode
- **Evidence:** Not started

### K006 — Run Research Experiment
- **Priority:** MEDIUM
- **Category:** Scientific
- **Description:** Execute research profile on Kaggle: 24 scenarios, 4 strategies, 3 reps. Publication-quality evidence.
- **Acceptance Criteria:** Research completes; results are publication-ready.
- **Dependencies:** K005
- **Status:** PENDING
- **Owner:** OpenCode
- **Evidence:** Not started

