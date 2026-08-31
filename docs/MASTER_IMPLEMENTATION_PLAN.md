# Master Implementation Plan

## Dependency-Aware Selective Regeneration for LLM-Assisted Software Evolution

## Authoritative Current Execution Track

```text
CURRENT TRUTH (2026-08-31, v0.9.22 D10 ALL-FAILED PILOT VIABILITY CLOSURE (PILOT-EXEC-01) - REAL 48-CELL PILOT `exp-20260830-134232` FINISHED 48/48 TERMINAL FAILURES (0 SUCCEEDED, 0 EVALUATOR-PASSED) AND IS REJECTED; STABLE ANNOTATED TAG `v0.9.22-pilot-exec-ready` UNCHANGED BUT RETIRED AS A LAUNCH CANDIDATE; INTERNAL RUNTIME CONTRACT CORRECTED (PROTOCOL 1.1, TIMEOUT 1200, PILOT-CANARY GATE, STANDALONE FAIL-CLOSED RESUME, TERMINALITY/VIABILITY SPLIT); NO REAL PILOT LAUNCH AND NO TAG MOVE IN THIS CLOSURE): branch fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure. The one permitted real 48-cell Pilot launched from the exact D9.6 artifact edae1b7e5be7ebab642d1e3c068dda3842a8061b8b04ab84c027d43a38dc8c4a (source commit 478261ff595d3d64ed9d5bab32d1cc90d7dabd77, tag v0.9.22-pilot-exec-ready) on 2026-08-30 completed with 48/48 terminal failures / 0 succeeded / 0 evaluator-passed (exp-20260830-134232; protocol 1.0; config hash 4b5bbcb2abcf62af; ~23,610 s; 293 model calls; 731,678 prompt + 88,953 completion = 820,631 total tokens; classifications scientific_budget_exhausted=33, model_output=8, build=7; 33 runs killed at the 600 s workflow deadline; iterative agent ran out to "no paths selected" on several Saleor/djangoCMS/Todo scenarios). It is REJECTED and preserved verbatim, never resumed or counted. The stable annotated tag v0.9.22-pilot-exec-ready still exists and still peels to 478261ff... but it is retired as a launch candidate (the only permitted launch from that artifact was 100%-failed). Scientific version remains v0.9.22 (never v0.9.23); scientific inputs unchanged (model Qwen2.5-Coder-14B-Instruct, BNB-NF4, sdpa flash_or_efficient_no_math, GQA repeat_kv_sm75, 12 scenarios, 3 repo pins Todo/django CMS/Saleor, 2 strategies, 2 reps = 48 cells, prompts, Ground Truth, metrics, max attempts 3, completion cap 4096, 12000/64 gate). D10 (D10.1-D10.7) corrects the internal runtime/operability contract WITHOUT touching scientific inputs: D10.1 truth-only report+docs+commit+push; D10.2 protocol_version 1.0 -> 1.1 and Pilot profile timeout_seconds 600 -> 1200 uniformly for BOTH strategies (the 600 s ceiling censored 33/48 runs; selective mean was 540 s with zero headroom); D10.3 a real end-to-end pilot-canary mode + canonical fail-closed validate_pilot_canary_evidence gate wired as a notebook stage; D10.4 the resume cell made standalone (PILOT_OUTPUT_DIR recomputed independently - the D9.6 resume cell raised NameError: name 'PILOT_OUTPUT_DIR' is not defined when run standalone) and fail-closed against rejected experiment IDs; D10.5 validator separates terminality from scientific viability; D10.6 all fixes tests-first (RED then GREEN); D10.7 freeze, docs, push, verified project-2026-08-31-*.zip export, Stop Report. The next REAL Pilot launch requires a NEW freshly-finalized artifact (protocol 1.1, 1200 s, corrected resume + terminality/viability) with its own real pilot-canary pass and its own tag decision - the retired tag and the edae1b7e...8c4a artifact are NOT reused as a launch basis. Report: reports/V0922_D10_ALL_FAILED_PILOT_VIABILITY_CLOSURE_REPORT.md.
PRIOR TRUTH (2026-08-30, SUPERSEDED by the D10 all-failed relaunch closure - v0.9.22 D9.6 REAL 2x T4 PASS + STABLE-TAG CLOSURE (PILOT-EXEC-01) - REAL EXACT-ARTIFACT 2x T4 PREFLIGHT PASSED ON 2026-08-30; STABLE ANNOTATED TAG EXISTS AND PEELS TO 478261ff...; REAL PILOT NOT STARTED): branch fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure. Independent audit of the exact D9.6 artifact edae1b7e5be7ebab642d1e3c068dda3842a8061b8b04ab84c027d43a38dc8c4a (source commit 478261ff595d3d64ed9d5bab32d1cc90d7dabd77, build id 478261f) real 2x T4 Kaggle evidence PASSED every Gate B requirement (expanded-mode sidecar proof matches the artifact SHA; deployment identity 478261ff.../v0.9.22-pilot-exec-ready/48 cells/Qwen 14B/BNB-NF4 and all five code/data/repository/notebook/transport manifest hashes recompute and match; repository preflight overall == PASS with Todo, django CMS, Saleor all PASS and Saleor PostgreSQL + Valkey/Redis reachable; T4 SDPA GQA microprobe passes on both cuda:0 and cuda:1 (Tesla T4 compute capability 7.5, Q/K/V + output on the intended device, repeat_kv_sm75); model_preflight.json.passed == true with exactly 2 Tesla T4, model_identity == qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25, requested/effective attention sdpa, kernel policy flash_or_efficient_no_math, GQA repeat_kv_sm75, short generation PASS (17 completion tokens), generation-deadline canary PASS (deadline_fired==true, finish_reason==timeout, 4 completion tokens), long-context probe PASS (12,044 prompt tokens / 64 completion tokens); the bundled canonical validate_pilot_dryrun_evidence PASSED (48 records / 48 unique IDs / statuses all succeeded / repo 16-16-16 / strategies 24-24 / reps 24-24 / all model-call + token counters integer zero / source identity 478261ff.../v0.9.22-pilot-exec-ready/build 478261f/dry-run:mock); notebook cells 0-7 have no error outputs, the pilot-launch/resume/verify/export cells remain UNEXECUTED, the only run_records.jsonl is the 48-record dry-run file, and the HF token value never appears (only "retrieved and set in environment" is printed). On PASS, the annotated stable tag v0.9.22-pilot-exec-ready now EXISTS and peels to 478261ff595d3d64ed9d5bab32d1cc90d7dabd77 (tag object fdcb409670e040a287811840ddbcab475816a7e5; git cat-file -t = tag; local + remote peeled target == 478261ff...; pushed to origin and verified with the configured authenticated origin credentials - no anonymous/public readability probe). The artifact REMAINS edae1b7e...8c4a; no rebuild and no finalizer run. The real 48-cell Pilot has NOT started; the ONLY remaining operational step is, in the same still-live Kaggle session, to run Step 8 "Pilot Launch - STOP Until Stable Tag Is Confirmed" / pilot-launch-cell. Never resume exp-20260828-151335 - it has zero accepted RunRecords. GitHub privacy is irrelevant to Kaggle execution; GitHub is owner-controlled source/release storage only. Full suite remains the previously accepted 2538 passed / 33 skipped / 0 failed (carried; runtime code unchanged). Report: reports/V0922_D9_6_REAL_T4_PASS_STABLE_TAG_CLOSURE_REPORT.md.
PRIOR TRUTH (2026-08-29, SUPERSEDED by the D9.6 real 2x T4 PASS + stable-tag closure, v0.9.22 D9.6 NOTEBOOK-MARKDOWN CELL-LABELS CLOSURE (PILOT-EXEC-01) - NOTEBOOK-NAVIGATION REFINEMENT ON TOP OF THE D9.6 KAGGLE/GITHUB BOUNDARY CORRECTION; REAL T4 PROOF PENDING; NO STABLE TAG YET): branch fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure; D1-D9.6 complete locally. NOTHING scientific, NOTHING in production/runtime code, and NOT the Kaggle/GitHub boundary changed: 11 exact Markdown navigation cells (pilot-step-00..10-*md, e.g. Step 04 model-preflight, Step 08 STOP boundary, Step 09 launch, Step 10 resume) were inserted between the (byte-identical, unchanged) 16 executable code cells in notebooks/pilot_exec_01.ipynb so Kaggle's Table of Contents names every operational stage and a visible pre-launch STOP boundary guards pilot-launch. New regression tests: TestMarkdownNavigation / TestCodeCellsUnchangedFromBaseline / TestBundledNotebookParity (tests/integration/test_pilot_notebook_contract.py) and TestPilotBundleKeepsMarkdownNavigation (tests/integration/test_pilot_deployment_bundle.py); notebook diff 126 insertions / 0 deletions; code cells compile 16/16; RED-to-GREEN established. D9.1-D9.4 (decode-step workflow-deadline stopping criterion with 30 s liveness heartbeats, mandatory real-Qwen generation-deadline canary, eager shared-model init, per-run cooperative guard install on strategy AND shared backend), the D9.6 Kaggle/GitHub boundary correction (the D9.5 remote tag-peel gate is REMOVED — launch and resume NEVER contact GitHub (no git ls-remote, no token); validate_pilot_launch_authorization (pure local evidence: preflight JSON, sdpa kernel policy, mandatory generation-deadline canary) is the ONLY pre-command gate, wired into BOTH pilot-launch-cell AND pilot-resume-cell), and the owner-side-only stable tag (the annotated v0.9.22-pilot-exec-ready tag is created and locally verified against the owner-controlled, locally verified source commit after real preflight passes - no runtime gate ever contacts GitHub) all carry forward unchanged; _run_live keeps process-group terminate->kill->reap with bounded grace. DEGREE GREEN: the new notebook-nav tests + focused boundary + notebook/finalizer/provenance suites green; full acceptance 2538 passed / 33 skipped / 0 failed. FROZEN via the two-pass finalizer (--source-commit 478261f..., --verify-source-provenance): 0 mismatches, idempotent; the stable code/data/repository-snapshot/transport manifest hashes are UNCHANGED from D9.6 (37e79950.../8b859ecc.../49d91d39.../07036a36..., only notebook markdown changed); notebook_manifest_sha256 NEW 9d3edac4c20c00ab73a1ecda10d52322a5c57756820ed03f3a6162615e19adb6, deployed bundle notebook SHA 6720293b922e06a80ecdc44a6d16e5eb12cc777d23c24a7076d005872d7aba68 == canonical blob at 478261f... -> SOURCE COMMIT 478261ff595d3d64ed9d5bab32d1cc90d7dabd77 (build id 478261f; supersedes the D9.6 boundary-correction source 6ff1c93...). Canonical+bundled notebooks compile 16/16. Exact fresh-extraction bundled dry-run (bundled CLI, explicit --source-commit 478261ff595d3d64ed9d5bab32d1cc90d7dabd77) 48/48: 48 unique IDs, repos 16/16/16, strategies 24/24, reps 24/24, 0 calls/tokens; canonical validate_pilot_dryrun_evidence PASS - every record + source_identity.json == 478261f... and its build id 478261f. Exact artifact dist/pilot-kaggle-upload.zip SHA-256 edae1b7e5be7ebab642d1e3c068dda3842a8061b8b04ab84c027d43a38dc8c4a; sidecar matches; finalizer FROZEN 0 mismatches, idempotent; freeze report source == 478261f..., FROZEN. Scientific contract UNCHANGED. REQUIRED TRUTHFUL STATUS: the prior D9.6 artifact 03d8d0ae37b995a362ee90c53a1851588ad024f13ead033814399210ce54dfc4 (source 6ff1c93...) is SUPERSEDED by this notebook-nav artifact - do not upload the old artifact; D8 (02d16ca2...) REJECTED for Pilot launch (the real Pilot exposed the in-flight timeout/heartbeat defect D9 closes) and remains superseded; exp-20260828-151335 has 0 accepted RunRecords and must never be resumed; this remains v0.9.22 (never v0.9.23). NO stable tag during this local closure: next external step is ONE exact-new-artifact real 2x T4 GQA microprobe + generation-deadline canary + short + 12k preflight only; annotate v0.9.22-pilot-exec-ready at 478261f... ONLY after PASS; on FAIL return to the SAME v0.9.22 task (never v0.9.23). Report: reports/V0922_D9_6_NOTEBOOK_MARKDOWN_NAVIGATION_CLOSURE_REPORT.md.
PRIOR TRUTH (2026-08-29, SUPERSEDED by the D9.6 notebook-markdown cell-labels closure): the D9.6 Kaggle/GitHub boundary-correction artifact 03d8d0ae37b995a362ee90c53a1851588ad024f13ead033814399210ce54dfc4 from source 6ff1c93... (runtime launch/resume never contacts GitHub - no git ls-remote, no token; validate_pilot_launch_authorization pure-local-only wired into both cells; 2538/33/0; dry-run 48/48; FROZEN with 0 provenance mismatches, idempotent) is superseded for upload by the notebook-markdown cell-labels closure; do not upload it. The boundary correction itself is carried forward unchanged in the new closure.
PRIOR TRUTH (2026-08-29, SUPERSEDED by the D9.6 boundary correction, then by the D9.6 notebook-markdown cell-labels closure): the D9 artifact 913e8065... from source 9ea02b3... (in-flight workflow-deadline heartbeat + eager model init + a remote tag-peel pre-launch gate + freeze recovery closure; 2532/33/0; dry-run 48/48; FROZEN with 0 provenance mismatches) is superseded for upload by D9.6 because the runtime launch/resume path never contacts GitHub; do not upload it. Instead only the exact D9.6 notebook-markdown cell-labels artifact edae1b7e5be7ebab642d1e3c068dda3842a8061b8b04ab84c027d43a38dc8c4a from source 478261ff595d3d64ed9d5bab32d1cc90d7dabd77 (build id 478261f) may be uploaded.
PRIOR TRUTH (2026-08-28, SUPERSEDED by D9): the D8 artifact 02d16ca2... from source 8f0b119... (dry-run token-schema + launch-auth evidence closure; canonical validate_pilot_dryrun_evidence + _collect_dryrun_evidence_errors with strict _expect_zero_int; bundled dryrun-cell calls the validator; GQA per-device display reads real fields; 2492/33/0; exact dry-run 48/48; FROZEN with 0 provenance mismatches) is superseded for upload by D9; do not upload it. D8 is REJECTED for Pilot launch (the real Pilot exposed the in-flight timeout/heartbeat defect D9 closes). Instead only the exact D9 artifact 913e8065... from source 9ea02b3... may be uploaded.
PRIOR TRUTH (2026-08-27, SUPERSEDED by D7): the D1-D6 artifact ce40b330... from f72ecda... is rejected for upload because its validation argv was not executable in launch/resume.
PRIOR TRUTH (2026-08-24, HISTORICAL; SUPERSEDED by the D1-D6 closure above): v0.9.22 long-context attention memory closure - branch fix/pilot-v0922-long-context-attention-memory-closure (from clean main 58d1be533c98ca9bafc9a344f2a73f8a140b9540, v0.9.21 reconciled) implements the long-context attention memory closure. Real Kaggle v0.9.21 model preflight evidence: repository preflight PASS / dependencies PASS / Qwen 14B BNB-NF4 load PASS (qwen_model_load[bnb-nf4]: PASS) / GPU-only device map PASS / 2x Tesla T4 PASS / per-GPU headroom PASS (min free 7.764 GiB) / short generation probe PASS, then FAILED at the long-context probe with CUDA OOM: 12,044 prompt tokens / 64-token output budget / failed allocation 21.62 GiB == exactly 12044*12044*40*4 bytes = 21.6153 GiB, the full float32 40-head quadratic attention score matrix - the effective runtime attention path materialized the math/eager fallback during prompt prefill (offloaded KV cache does not cover prefill attention; device_map=auto is not tensor parallelism). v0.9.21 Real Pilot REJECTED BEFORE LAUNCH (no Experiment ID / no RunRecord created; no stable tag moved; the v0.9.21 repository/per-cell fixes remain VALID and are carried forward). v0.9.22 closes it WITHOUT touching any scientific input (model Qwen2.5-Coder-14B-Instruct, BNB-NF4, 12 scenarios, 3 repo pins, 2 strategies, 2 reps = 48 cells, prompts, Ground Truth, metrics, --timeout 600, --validation-timeout 1800, max attempts 3, completion cap 4096, the 12000-token long-context gate, the 64-token probe): Task A explicit attn_implementation="sdpa" at from_pretrained; Task B fail-closed CUDA generation inside sdpa_kernel([FLASH_ATTENTION, EFFICIENT_ATTENTION]) (no math/eager fallback; missing torch.nn.attention API on CUDA fails closed); Task C canonical attention evidence (requested/effective_attn_implementation, sdpa_kernel_policy=flash_or_efficient_no_math) persisted in preflight JSON, rendered in the human table, enforced by the fail-closed attention_policy check and pilot launch authorization; Task D corrected OOM diagnosis (long-prompt OOM reports prompt-prefill evidence + free GiB and never advises completion-cap reduction); Tasks E/F regression-guard every prior memory fix and the unchanged 12000/64 gate. RED/GREEN proven: 12 backend + 18 preflight contract tests failed against v0.9.21 code before the fix; full suite 2407 passed / 33 skipped / 0 failed; dry-run pilot profile 48/48 (unique IDs, 0 model calls, 0 tokens). NO STABLE TAG YET: build the exact candidate artifact from the merge commit, run the fresh Kaggle model preflight ONLY (same 12k target, same 64-token probe), create v0.9.22-pilot-exec-ready ONLY on PASS; if it FAILS return to the SAME v0.9.22 task (never spawn v0.9.23); no 48-cell launch while untagged. Report: reports/V0922_LONG_CONTEXT_ATTENTION_MEMORY_CLOSURE_REPORT.md.
HISTORICAL NOTE (2026-08-24, SUPERSEDED by the v0.9.22 attention closure candidate above it - at that time): PILOT-EXEC-01 v0.9.21 RELEASED AND ACCEPTED FOR THE NEXT KAGGLE TARGET PREFLIGHT - accepted release = v0.9.21-pilot-exec-ready @ annotated tag peel == artifact source commit == merge e308047c9c05f38316d80ce565bac1b51d105bfa; archive dist/pilot-kaggle-upload.zip SHA-256 62e377467e225d336cbcaa70a2c610b5080e329e1a4e6578fbcbdc1af7dbee40 (+ sidecar); trust/provenance 0 mismatches; exact-artifact dry-run independently repeated 48/48 succeeded / 48 unique / 0 model calls / 0 tokens; full suite 2370 passed / 33 skipped / 0 failed; target-shaped Gates 1-3 + complete no-model preflight GREEN on the released source state (CI runs 32692489617 / 32694137255; Saleor full primary exit 0 in 941.42s < the explicit 1800s per-cell validation budget). Release chain: v0.9.19 REJECTED FOR PILOT LAUNCH (real Kaggle Saleor fast-gate Pytest exit 5); v0.9.20 closed that root cause (internally trustworthy @ merge febda7938db1284da4090d35e980db472149c3ad, archive 56b1c2a9019a03892ce627321b9a415795ac95836ac415694bbc0995263c8024, no-model preflight GREEN run 32676588800) but was superseded for Real Pilot launch after the independent audit found B1 sys.executable validation routing / B2 frozen validation env discarded by FunctionalValidator / B3 hardcoded 180s validation timeout below measured runtime - ALL THREE CLOSED in v0.9.21 with --validation-python per-repository mappings, frozen-env propagation through PipelineConfig/RunnerConfig into FunctionalValidator, and explicit --validation-timeout 1800 on Pilot launch AND resume. Timeout semantics (frozen, documented): --timeout 600 is the cooperative workflow/model-call deadline; --validation-timeout 1800 is a separate bounded subprocess validation budget; validation may finish after the 600s deadline elapses and no new model/repair call starts once the cooperative deadline has elapsed. NO KNOWN ENGINEERING BLOCKER. Real Pilot = NOT STARTED; EXACT NEXT ACTION = fresh Kaggle v0.9.21 target preflight with the exact released artifact, then launch the accepted 48-cell Pilot in the SAME session if every gate passes. Authoritative snapshot = docs/AI_ACCOUNT_TRANSFER_HANDOFF.md.
ALL LINES BELOW THIS ONE ARE THE CHRONOLOGICAL EXECUTION TRAIL — each was "current" when written and is SUPERSEDED by the CURRENT TRUTH line above (kept for traceability).
SCIENTIFIC SMOKE V2 = COMPLETE AND ACCEPTED (SMOKE-V2-CLOSE-01, 2026-08-09) - 600-second confirmatory timeout-sensitivity Full-9 (T600, FULL9-T600-01) EXECUTED AND ACCEPTED: run exp-20260808-222843, uniform --timeout 600 on frozen runtime source/build 7f2a450, fail-closed _t600 output namespace, evidence prefix corrected-full9-t600-wsfix-7f2a450-; 9/9 terminal / 2 successes / 7 scientific failures / 0 engineering blockers / 0 budget-exhausted / 63 model calls / 77,929 tokens / max run ~373 s / Full-9 verification PASS / HF synchronization PASS - SAME 2/9 result as the accepted clean 300-second baseline (runtime 7f2a450, --timeout 300, valid and preserved, NOT invalidated or replaced); timeout sensitivity confirmed (600s ceiling did NOT change the accepted result; 300s baseline signal not distorted by censoring; NOT an improvement claim); uniform per-run workflow timeout frozen at 600s for monolithic / selective / iterative_repository_agent (one shared Full-9 command, no strategy extra time); do NOT raise above 600 (if Pilot runs accumulate near 600 s, analyze duration/repair distribution and pre-register the Pilot budget); SMOKE-V2-CLOSE-01 = CLOSED (closure audited and merged to main 193d889; stable tag v0.8.0-smoke-v2-complete created); MAIN-GREEN-01 = CLOSED (main d875c72; preferred recovery tag v0.8.1-smoke-v2-complete; full suite 1,958 passed / 33 skipped / 0 failed / 0 errors carried forward); HANDOFF-CONSISTENCY-01 = CLOSED (docs reconciliation merged to main 403977b; preferred recovery tag now v0.8.2-smoke-v2-complete); current task = PILOT-READY-01 (do NOT start Pilot); Pilot / fine-tune unauthorized; no further Kaggle Full-9 authorized
HISTORICAL NOTE (2026-08-10): the above "current task = PILOT-READY-01" is superseded — PILOT-READY-01 = CLOSED (see lines 25-26); current task = PILOT-EXEC-01; Pilot execution NOT STARTED
HISTORICAL NOTE (2026-08-13): the pre-execution gate state below (branch experiment/pilot-exec-01, v0.9.1 target) is superseded by the real-launch closure (v0.9.2-pilot-exec-ready @ e030be5) and then by the service-bootstrap correction (v0.9.3-pilot-exec-ready).
CURRENT EXECUTION (2026-08-13) = PILOT-EXEC-01 KAGGLE SERVICE BOOTSTRAP LAST-MILE CORRECTION, merged to main + tagged v0.9.3-pilot-exec-ready (branch fix/pilot-kaggle-service-bootstrap; historical execution-ready point v0.9.2-pilot-exec-ready @ e030be5 immutable, NOT moved): added ONE fail-closed, idempotent service-bootstrap-cell to the frozen Pilot notebook (notebooks/pilot_exec_01.ipynb) between repository snapshot verification and the repo-specific preflight — BEFORE any repository validation and model load — provisioning the Saleor validation OS services on a fresh Kaggle session: PostgreSQL 127.0.0.1:5433 (role/db saleor/saleor@saleor, private data dir /kaggle/working/pilot_services/postgres, pg_config --bindir preferred) and Valkey/Redis 127.0.0.1:6379 (persistence disabled), topology mirroring benchmark_data/manifests/pilot_validation_commands.yaml; OS installs non-interactive (apt-get; Kaggle Internet ON required, fail loudly offline); no benchmark/model Python environment modification; no secrets printed beyond the frozen non-secret test credentials. NO scientific inputs changed (scenarios, prompts, metrics, model, quantization, timeout 600, repair budget, repository pins, validation scope). Notebook contract 20/20 (incl. 5 new service-bootstrap tests), deployment bundle contract 14/14, targeted pilot gates 77/77, full suite 2,098 passed / 33 skipped / 0 failed, diff-check/ruff/mypy/compile clean. Deployment archive rebuilt from the exact tag: dist/pilot-kaggle-upload.zip + dist/pilot-kaggle-upload.zip.sha256 (authoritative frozen upload artifacts; never manually re-zip). Pilot = NOT STARTED. Next: exact Kaggle launch prep (upload zip + sidecar as ONE Dataset, attach Pilot notebook + Qwen 14B, Internet ON, HF_TOKEN) -> target preflight -> real Pilot (only after all preflights pass). Real launch deferred until the user confirms the actual Kaggle mounted model path and HF results repository ID.
R4 = accepted and frozen (f5ae826)
R5 = accepted and frozen (7761c48)
R6 = ACCEPTED AND FROZEN (949e9c2) - freeze record and milestone-branch publication authorized
Push = published (upstream set, local/remote equality verified)
Selective calibration canary = EXECUTED (exp-20260804-133523, source/build 50ec2c1) - failed model_output, 0 files written; harness controls verified, Qwen quality unchanged
Qwen 14B BNB-NF4 canary preparation = COMPLETE (2026-08-05) - Commit A 0ece665 + Commit B 0a596b8, pushed, local = remote, tree clean; model-aware identity qwen:<basename>:<mode>:cfg-<12hex> replaces qwen:1:int8 (blocks auto-resume cross-model contamination); bnb-nf4 profile added; notebook pinned to unquantized 14b-instruct/1 with fail-closed canary preflight gate; full suite 1,877 passed / 32 skipped / 0 failed
Qwen 14B SELECTIVE CANARY SUCCESS = ACCEPTED (2026-08-07) - real engineering preflight PASS (2x Tesla T4, bnb-nf4, identity qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25, min free VRAM 8.417 GiB, GPU-only); canary exp-20260807-131819 (todo-smoke-001 / selective, source/build f7b1ebb) SUCCEEDED - 3 selected / 2 preserved / 3 regenerated, migration 0004_task_priority.py, 3 calls / 3,247 tokens / 295.944 s / 0 repairs; functional validation PASS; evaluator PASS 10/10; accepted real 14B canary records = 1 succeeded / 0 failed (isolated selective-only plan, NOT 1/9)
Full 9-record Scientific Smoke V2 = RUN BUT REJECTED (exp-20260807-205422, source f7b1ebb; 9/9 completed, 2 succeeded / 7 failed, 62 calls / 76,858 tokens) - root cause = overlay source restaging leaked generated files across scenarios (0004_task_priority survived into 002 and produced 0005_remove_task_priority_task_deleted_at; affected selective/agent 002 and 003); preserved as evidence only, NOT the accepted aggregate
FULL-9 WORKSPACE ISOLATION CLOSURE = COMPLETE (2026-08-08) - Commit A 7f2a450 (fix(smoke): reset workspace source before every matrix run; _reset_workspace_source_from_snapshot deletes the source tree then restages; make_isolation resets every arm workspace per run) + Commit B e29c017 (chore(deploy): repin isolated Full-9 Smoke bundle; SOURCE_COMMIT=7f2a4509482dc7e62c2b243374592e9a88e2ff48 / DEPLOYED_BUILD_ID=7f2a450); unit edge cases 33 passed / 1 skipped; sequential 001→002→003 migration proof + nine-run zero-residue matrix proof green; OFFICIAL PRE-BENCHMARK GATE (pytest 8.4.2) GREEN = 1,928 passed / 33 skipped / 0 failed; Dataset 161/1, Prompt 200/12, Pipeline Smoke 45, Dry Run 9/9/9/0 exit 0, Metric 187, ruff 0 new (5 baseline), mypy 0 new (4 baseline); canary remains accepted; v0.8.0-canary.1 unchanged; Kaggle NOT rerun; sentinel FULL9_WORKSPACE_ISOLATION_CLOSURE_AUDIT_REQUIRED
FULL9-WS-02A LAUNCH-SAFETY DOCS/RUNBOOK CLOSURE = COMPLETE (2026-08-08) - docs/runbook only; runtime workspace-isolation fix ACCEPTED (7f2a450, deployment re-pinned by e29c017) but a new Full-9 was blocked because the runbook still launched f7b1ebb and did not fail closed on a non-empty output directory; corrected runbook identity = SOURCE_COMMIT=7f2a4509482dc7e62c2b243374592e9a88e2ff48 / DEPLOYED_BUILD_ID=7f2a450; setup = setup-cell -> install-lock-cell -> preflight-cell -> secrets-cell -> Full-9; fresh output = /kaggle/working/runs/qwen14b_bnb_nf4_full9_scientific_smoke_wsfix_7f2a450 with fail-closed non-empty guard; initial command = no --strategy / --max-runs / --auto-resume-hf; first Full-9 = RUN BUT REJECTED; corrected fresh Full-9 = NOT YET RUN at that time (HISTORICAL — later executed and accepted as exp-20260808-222843); next (historical) = independent delta audit of this closure, then one fresh Full-9 only if accepted
FULL9-T600-01 600S CONFIRMATORY TIMEOUT-SENSITIVITY FULL-9 CONTRACT = PUBLISHED (2026-08-08) AND CLOSED (2026-08-09, SMOKE-V2-CLOSE-01) - executable commit e6dbd3e (chore(smoke): raise confirmatory Full-9 timeout to 600s), pushed, local = remote; accepted clean 300-second Full-9 baseline (runtime source/build 7f2a450, --timeout 300) = 9/9 terminal / 2 successes / 7 scientific failures / 0 engineering blockers with three runs at or beyond the ~300-second workflow ceiling (~307-337 s) - REMAINS VALID AND PRESERVED (NOT invalidated or replaced); uniform scientific per-run workflow timeout raised 300 -> 600 for exactly one confirmatory Full-9 (T600); T600 WAS EXECUTED AND ACCEPTED (run exp-20260808-222843): uniform --timeout 600 = 9/9 terminal / 2 successes / 7 scientific failures / 0 engineering blockers / 0 budget-exhausted / 63 model calls / 77,929 tokens / max run ~373 s / Full-9 verification PASS / HF synchronization PASS - SAME 2/9 result as the accepted clean 300-second baseline (timeout sensitivity confirmed, NOT an improvement claim); changed ONLY the timeout - all other frozen scientific inputs (model, prompts, strategies, scenarios, evaluator, metrics, max attempts, token budgets, deployment identity 7f2a450) unchanged; 600s applies uniformly to monolithic / selective / iterative_repository_agent (one shared Full-9 command, no strategy extra time); DO NOT raise above 600 (if Pilot runs accumulate near-600s runs, analyze duration/repair distribution and pre-register the Pilot budget); new fail-closed output = /kaggle/working/runs/qwen14b_bnb_nf4_full9_scientific_smoke_wsfix_7f2a450_t600; evidence archive prefix = corrected-full9-t600-wsfix-7f2a450-; pre-benchmark validation recorded (Dataset/Prompt/Metric PASS carried-forward zero drift; Pipeline Smoke PASS T600 command + namespace contract; Dry Run PASS exact 3x3 no-model/bundled dry-run contract with scientific timeout 600; Integration Test PASS 1,947 passed / 33 skipped / 0 failed); audit = implementation PASS / over-engineering PASS / scientific identity PASS (runtime source/build remains frozen 7f2a450); non-destructive RED proof recorded (committed HEAD notebook with --timeout 300 FAILS the new 600-second contract); task CLOSED; next (HISTORICAL — completed) = independent delta audit of the Scientific Smoke V2 closure (SMOKE-V2-CLOSE-01), then main merge + stable tag v0.8.0-smoke-v2-complete, then PILOT-READY-01 — all executed (closure merged 193d889, stable tag created; MAIN-GREEN-01 merged d875c72, preferred recovery v0.8.1-smoke-v2-complete; next task PILOT-READY-01); Pilot execution NOT STARTED (fine-tune unauthorized); no further Kaggle Full-9 authorized
FULL9-EXEC-01 CANONICAL CORRECTED FULL-9 NOTEBOOK EXECUTION CLOSURE = COMPLETE (2026-08-08) - Commit A c4aee03 (feat(kaggle): make corrected Full-9 notebook executable), pushed, local = remote, tree clean; status COMPLETE - pending independent delta audit before Kaggle Full-9; canonical notebook = single tested fail-closed execution artifact for exactly one fresh corrected Full-9; setup-cell bootstrap fixed (MODEL_CANDIDATES from KNOWN_MODEL, MODEL_PATH derived, MODEL_DIR NameError regression gone, src_dir + sys.path guard, SCRIPT_PATH.is_file guard); stale execution routes removed (setup-cell -> install-lock-cell -> preflight-cell -> secrets-cell -> full9-execution-cell -> full9-verification-cell -> export-evidence-cell); latest Kaggle attempt truth = source/build 7f2a450, runtime install/preflight PASS, redundant corrected-source selective canary succeeded but is NOT a Full-9, corrected Full-9 evidence 0/9 at that time (later executed and accepted as exp-20260808-222843), evidence ZIP from that session must not be labeled accepted Full-9 evidence; full suite 1,947 passed / 33 skipped / 0 failed; next (historical — superseded by the executed and accepted T600 Full-9) = independent delta audit of FULL9-EXEC-01, then exactly one fresh corrected Full-9; main merge / stable tag / Pilot / fine-tune unauthorized (all since completed except Pilot)
Real Smoke = canary succeeded 1 / failed 0 (local scripted 9/9; bundled CLI dry-run 9/9); first Full-9 exp-20260807-205422 rejected (evidence only); corrected fresh Full-9 under 7f2a450 = EXECUTED AND ACCEPTED as exp-20260808-222843 (T600, uniform --timeout 600, 9/9 terminal / 2 successes / 7 scientific failures / 0 engineering blockers / SAME 2/9 result as the accepted clean 300-second baseline)
Milestone tag = v0.8.0-canary.1 (created and pushed 2026-08-07; annotated; NON-STABLE; points to 31a619857ce07eb09ab5e206fbc9dc792782c99c) - first accepted real Qwen 14B NF4 selective-canary milestone; UNCHANGED
Tag naming = v0.8.0-canary.N (isolated calibration milestones) | v0.8.0-smoke-v2-complete (create ONLY after a fresh Full-9 result audit + main merge; replaces the stale v2.0.0-scientific-smoke future-tag wording)
Stable release = YES (v0.8.0-smoke-v2-complete created at 193d889; v0.8.1-smoke-v2-complete at d875c72; preferred recovery v0.8.2-smoke-v2-complete at 403977b); Full 9-record Scientific Smoke V2 = COMPLETE AND ACCEPTED (SMOKE-V2-CLOSE-01 CLOSED); main merge = COMPLETE; HANDOFF-CONSISTENCY-01 = CLOSED
Pilot = NOT STARTED (execution not authorized); PILOT-READY-01 = CLOSED (2026-08-10); next task = PILOT-EXEC-01
PILOT-READY-01 = CLOSED (2026-08-10) - branch feat/pilot-ready-01, code/test commit 34ecf78 (fix(pilot): close multi-repo selective input contracts, pushed, local = remote): per-repository dependency graphs, per-repository editable universes, file-granular descriptors for django CMS/Saleor, stale real-smoke expectation corrected (STRATEGIES_WITH_MISSING_PREREQS = {"agent"}), focused multi-repo production-path contract added (12 tests); full suite 2,026 passed / 33 skipped / 0 failed; exact fresh 48-cell Pilot dry-run 48/48 succeeded / 0 failed / 0 pending (deterministic unique run IDs, config_hash 7ef6ffc7a2c0d369, protocol 1.0, source_commit 34ecf78; per-repo 16/16/16; per-strategy 24/24; per-rep 24/24; checkpoint completed; no residue); isolation/evidence/export gates 142 passed; frozen Pilot matrix = Qwen2.5-Coder-14B-Instruct / bnb-nf4 / 600s / 12 scenarios / 2 strategies / 2 repetitions = 48 cells (Todo / django CMS / Saleor); stable tag v0.9.0-pilot-ready after main merge; no accepted Smoke evidence or frozen source history changed
```

Exact path from R6 freeze to Pilot freeze:

```text
record R6 freeze
→ push branch and set upstream, verify local/remote equality
→ record publication status and push again
→ Kaggle environment preflight (PASS 2026-08-07, 2x Tesla T4 bnb-nf4, min free VRAM 8.417 GiB)
→ one successful real 14B selective canary (exp-20260807-131819) accepted by independent audit
→ independent GPT-5.6 Sol delta audit of the FULL9-T600-01 600-second confirmatory timeout-sensitivity contract (executable commit e6dbd3e; supersedes the FULL9-EXEC-01 execution gate — runtime source/build remains frozen 7f2a450; timeout raised 300 -> 600 for exactly one confirmatory Full-9; accepted clean 300-second baseline preserved), then one fresh 600-second confirmatory Full-9 Scientific Smoke V2 (3 scenarios x 3 arms x 1 rep; SOURCE_COMMIT=7f2a4509482dc7e62c2b243374592e9a88e2ff48 / DEPLOYED_BUILD_ID=7f2a450; fail-closed fresh output dir /kaggle/working/runs/qwen14b_bnb_nf4_full9_scientific_smoke_wsfix_7f2a450_t600; --timeout 600) via the canonical notebook, compared cell-by-cell against the accepted clean 300-second baseline — EXECUTED AND ACCEPTED as exp-20260808-222843 (9/9 terminal / 2 successes / 7 scientific failures / 0 engineering blockers / SAME 2/9 result)
→ nine real Qwen Scientific Smoke V2 records (3 scenarios x 3 arms x 1 rep)
→ independent real-result audit
→ main merge, then stable v0.8.0-smoke-v2-complete tag — EXECUTED (closure audited and merged to main 193d889; stable tag v0.8.0-smoke-v2-complete created; MAIN-GREEN-01 merged d875c72; preferred recovery tag v0.8.1-smoke-v2-complete; milestone v0.8.0-canary.1 unchanged, non-stable)
→ freeze Pilot matrix and authorize Pilot (NOT YET — authorized next task after PILOT-READY-01, which is CLOSED; next = PILOT-EXEC-01)
```

## Historical implementation plan — non-authoritative for current execution

The pre-R3 phase map, the legacy approved-repository and approved-strategy
lists below describe earlier implementation history. They are retained for
traceability only and are NOT authoritative for current execution. The current
authoritative track is the section above.

### Phase Map

| Phase | Name                            | Status      |
|-------|---------------------------------|-------------|
| 0     | Bootstrap and Environment       | COMPLETE    |
| 1     | Input Audit                     | COMPLETE    |
| 2     | Research Protocol               | COMPLETE    |
| 3     | Repository and Scenario Preparation | COMPLETE |
| 4     | Benchmark Core                  | COMPLETE    |
| 4A    | Domain Models and Contracts     | COMPLETE    |
| 4B    | Loaders and Validation          | COMPLETE    |
| 4C    | Model Backends                  | COMPLETE    |
| 4D    | Execution Core                  | COMPLETE    |
| 4E    | Impact Strategies               | COMPLETE    |
| 4F    | Evaluation Engine               | COMPLETE    |
| 5     | Strategies                      | SUPERSEDED  |
| 6     | Validation and Leakage          | PENDING     |
| 7     | Metrics and Statistics          | SUPERSEDED  |
| 8     | Kaggle Notebook                 | COMPLETE    |
| 9     | Packaging and Documentation     | COMPLETE    |
| 10    | Static and Local Engineering Audit | COMPLETE |

## Completed

- SU-0010A shared regeneration
- SU-0010B1 repository-derived ArtifactUniverse
- SU-0010B1A active snapshot staging
- SU-0010B1B Ground-Truth-free graph construction
- SU-0010B2 metrics persistence/reporting
- SU-0010B3 functional validation and bounded repair (correction: token budget enforcement, failure history preservation, timeout test fix)
- SU-0011 iterative repository agent (audit corrections applied: cumulative token accounting, budget check between reasoning/regeneration, fair token-budget semantics, requires_iteration control state, backend exception propagation, type-ignore removal)
- SU-0011 on feature/su-0011-iterative-repository-agent awaiting merge
- Efficient Agent Verification Setup (AGENTS.md, skill, commands, check_fast.py on chore/efficient-opencode-verification)
- OPENROUTER-BACKEND on feature/openrouter-api-backend — minimal OpenRouter API backend
- **SCIENTIFIC-SMOKE-V1 EXECUTED + FAILED** — 6 root-cause failures identified and fixed; retry required on experiment/scientific-smoke-v1
- **SCIENTIFIC-SMOKE-V1 RETRY1 DEPLOYMENT PINNED** — commit 76ef349, deployed build ID 76ef349, output `/kaggle/working/runs/scientific_smoke_v1_retry1`
- **SCIENTIFIC-SMOKE-V1 RETRY2 FIXES APPLIED** — active_snapshot_root propagation, filtered HF resume identity (commit 8a1948f+)
- **THREE-ARM-CORE-EXPERIMENT** — Recovered from broken methodology-conformance WIP; frozen three-arm design; create branch experiment/three-arm-smoke-v2 from 0a1c603

## Next

- ~~Scientific Smoke V1~~ — Superseded by THREE-ARM-CORE-EXPERIMENT
- **Qwen 14B SELECTIVE CANARY SUCCESS (2026-08-07): ACCEPTED AND RECORDED** — real preflight PASS + canary `exp-20260807-131819` succeeded; accepted real 14B canary records = 1 succeeded / 0 failed (NOT 1/9); record `selective_updates/records/QWEN14B-SELECTIVE-CANARY-SUCCESS-2026-08-07.md`; sentinel `QWEN14B_CANARY_SUCCESS_DOCUMENTED_FULL9_READY`
- **Scientific Smoke V2 = COMPLETE AND ACCEPTED (SMOKE-V2-CLOSE-01, 2026-08-09)** — 600-second confirmatory Full-9 `exp-20260808-222843` EXECUTED AND ACCEPTED (uniform `--timeout 600`, frozen runtime `7f2a450`, `_t600` namespace, 9/9 terminal / 2 successes / 7 scientific failures / 0 engineering blockers / 0 budget-exhausted / 63 calls / 77,929 tokens / max run ≈373 s, Full-9 verification PASS, HF synchronization PASS, SAME 2/9 result as the accepted clean 300-second baseline — timeout sensitivity confirmed, NOT an improvement claim); uniform per-run workflow timeout frozen at 600s; milestone closed
- **Close Scientific Smoke V2 permanently (SMOKE-V2-CLOSE-01)** — CLOSED (2026-08-09): docs updated to the accepted state; closure audited; non-ff merged to main `193d889`; stable tag `v0.8.0-smoke-v2-complete` created; repo left ready for `PILOT-READY-01`; MAIN-GREEN-01 (main `d875c72`, preferred recovery `v0.8.1-smoke-v2-complete`) also closed
- **Independent delta audit of the Scientific Smoke V2 closure** — COMPLETED (accepted; main merge `193d889` + stable tag `v0.8.0-smoke-v2-complete` done; MAIN-GREEN-01 merged `d875c72`)
- **PILOT-READY-01 = CLOSED (2026-08-10)** — multi-repo selective input contracts fixed (`34ecf78` pushed on `feat/pilot-ready-01`), stale real-smoke expectation corrected, focused 12-test multi-repo production-path contract added, full suite 2,026 passed / 33 skipped / 0 failed, exact fresh 48-cell Pilot dry-run 48/48 deterministic green, isolation/evidence/export gates 142 passed; frozen Pilot matrix Qwen2.5-Coder-14B-Instruct / bnb-nf4 / 600s / 12 scenarios / 2 strategies / 2 repetitions / 48 cells
- Pilot (NOT STARTED; execution not authorized — next task `PILOT-EXEC-01`)
- **Complete:** 0a1c603 baseline verified (1063 pass, 5 skip), three-arm core experiment documented, 3 smoke scenarios created, evaluator tests isolated, contract tests added

## Known Boundary

- neutral empty graph when no profile graph exists
- real repository dependency inference remains deferred
- OpenRouter API backend is provider-integration only; no retries, streaming, or fallback routing
- Scientific Smoke V2 = COMPLETE AND ACCEPTED (SMOKE-V2-CLOSE-01 CLOSED); PILOT-READY-01 = CLOSED; Pilot execution NOT STARTED (next task `PILOT-EXEC-01`); no further Kaggle Full-9 authorized

### Dependencies

- Phase 0 must complete before Phase 1.
- Phase 1 must complete before Phase 2.
- Phases 2–3 can be partially parallelized.
- Phase 4 (subphases A–D) requires Phase 3 scenario definitions.
- Phase 4E requires Phase 4D execution core.
- Phase 4F requires Phase 4E strategies.
- Phase 6 requires Phase 4F evaluation engine.
- Phase 8 requires Phases 4–7.
- Phase 9 requires Phase 8.
- Phase 10 runs at the end.

### Approved Repositories (historical — pre-R6 plan)

| Size   | Repository            | Status |
|--------|-----------------------|--------|
| Small  | Controlled Django Todo| PENDING|
| Medium | django CMS            | PENDING|
| Large  | Saleor Core           | PENDING|
| Stress | ERPNext (optional)    | PENDING|

### Approved Strategies (historical — pre-R6 plan)

- repository_agent (baseline)
- static_only
- semantic_only
- hybrid_selective
- traceability_only (additional impact strategy)
- full_context (only when feasible)

### Key Constraints

- No local model download or inference.
- Real LLM runs on Kaggle (Qwen) or OpenRouter API (free/paid models).
- OpenRouter backend uses Python standard library only (no external SDK).
- Correctness > efficiency.
- Python 3.11, Conda environment.

## R6 Status (2026-08-01)

R6 deployment closure is **ACCEPTED AND FROZEN** by the final independent re-audit (GPT-5.6 Thinking, 2026-08-01, audited HEAD `949e9c2`), recorded in `docs/R6_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md`. The bounded final correction closed TD-R6-ENTRYPOINT-001 (test commit `40c7a47`, bundled CLI dry-run 9/9) and documentation-truth defects D1–D6 (`949e9c2`). Runtime source commit `cb25e9f`; deployed bundle commit `54a0462`; manifest committed-tree counts 0/0/0; Todo baseline tests deployed = 47; evaluator assets deployed = 3 + 3 fingerprints. Local scripted records = 9/9; bundled CLI dry-run = 9/9; real Qwen records = 0/9; Kaggle not launched; push authorized and pending at this commit; tag not created; Pilot not authorized. Final accepted full suite = 1,648 passed / 32 skipped / 0 failed. Next: publish the branch with upstream, verify local/remote equality, then Kaggle environment preflight and nine real Qwen records.

## Deterministic Interpreter Closure (2026-08-02)

The clean-environment reproducibility defect at the project execution boundary was closed on branch `fix/kaggle-smoke-v2-model-output-closure`. Runtime commit `aac9914` (fix(exec): bind Python scenario commands to active runtime) normalizes bare interpreter tokens (`python`, `python.exe`, `python3`, `python3.exe`, case-insensitive, directory-less) to `sys.executable` before executing `post_generation_command`, preserving the original command in diagnostics (`PostGenerationResult.original_command`) and recording the resolved executable (`resolved_executable`). Deployment commit `311e084` pins the bundle (notebook SOURCE_COMMIT=`aac9914c6dcda054736539a0d0ed649cf9865128`, DEPLOYED_BUILD_ID=`aac9914`); bundle = 147 files / 928,175 bytes; identity tests pass (build ID length 7, == SOURCE_COMMIT[:7], canonical==generated notebook, HEAD==SOURCE_COMMIT at pin time).

Recreated clean Python 3.11.9 validation environment (`_workspace\cache\prebenchmark-py311`, pytest 8.4.2, Django 5.2.16, DRF 3.17.1) full gate: **1,834 passed / 32 skipped / 0 failed** (first clean-env attempt exposed missing optional test deps — tabulate, httpx, jinja2 — installed in the clean env only; no repo change). Dataset Validation 285 passed / 5 skipped; Prompt Validation 158 passed; Pipeline Smoke 220 passed / 12 skipped; Metric Verification 169 passed; mypy strict src/benchmark Success (77 files); ruff clean on changed files; compileall clean; bundle rebuild idempotent; notebook valid; all manifest SHA-256 verified (code 87 + 3 .sha256 = 90, data 56, notebook 1). Bundled CLI dry-run `--profile scientific-smoke-v2`: 9 planned / 9 terminal / 9 succeeded / exit 0; source_identity = source_commit 311e084, deployed_build_id 311e084. Real Qwen records remain 0/9; no scientific evidence exists; tag not created; Pilot not authorized; independent audit required before any Kaggle relaunch.

## Pre-Benchmark Final Reproducibility Audit Closure (2026-08-03)

The pre-benchmark reproducibility-and-truth closure on branch `fix/kaggle-smoke-v2-model-output-closure` declares the complete pre-benchmark test environment so it can be recreated purely from project declarations, and records the observed truth. Runtime commit `aac9914` (fix(exec): bind Python scenario commands to active runtime) and deployment commit `311e084` (bundle pin; notebook SOURCE_COMMIT=`aac9914c6dcda054736539a0d0ed649cf9865128`, DEPLOYED_BUILD_ID=`aac9914`) are unchanged. Declaration commits `769d84e` + `e5d9430` extend `pyproject.toml [dev]` + `requirements-dev.txt` with the complete pre-benchmark set: Django==5.2.16, djangorestframework==3.17.1, pytest-django==4.12.0, pytest-asyncio==1.2.0 (required by `--asyncio-mode=auto`), tabulate==0.10.0, httpx==0.28.1, Jinja2==3.1.6, huggingface_hub==0.24.0 (the 1.x line broke positional `hf_hub_download`/`local_dir_use_symlinks` and strict mypy), types-pyyaml>=6.0,<7 (mypy strict yaml stubs), pytest>=8.0,<9. Runtime `[project.dependencies]` and `requirements-smoke-kaggle.lock` untouched.

The environment was deleted and recreated from declarations only (Python 3.11.9, pytest 8.4.2, Django 5.2.16, DRF 3.17.1, pytest-django 4.12.0, tabulate 0.10.0, httpx 0.28.1, Jinja2 3.1.6, ruff 0.15.22, mypy 1.20.2). Complete clean gate on the recreated environment: full suite = **1,833 passed / 32 skipped / 1 failed** (sole failure = `test_notebook_source_commit_matches_deployed_runtime_tree`, structural because the mandated `pyproject.toml` declaration change breaks byte-identity with the pinned `aac9914` SOURCE_COMMIT; frozen artifacts were not modified to force green — reported truthfully); Dataset Validation 285 passed / 5 skipped; Prompt Validation 158 passed; Pipeline Smoke 220 passed / 12 skipped; Dry Run 9/9 succeeded (exit 0); Integration PASS; Metric Verification 169 passed; mypy strict src/benchmark Success (77 files); ruff 93 findings = 468a23a baseline (0 new); compileall clean; bundle build verified (147 files / 928,329 bytes) then `kaggle_upload` restored unchanged; git diff --check clean; tree clean. Historical experiment `exp-20260801-210443` produced **one failed model-output terminal record** under source `6f88823` — preserved, excluded from the current `aac9914` aggregation; current accepted `aac9914` records = **0/9**; no scientific evidence; no tag; no Pilot; no Kaggle launch. Next action after this independent audit: Kaggle engineering preflight only (update the Kaggle code dataset + notebook to the corrected `e5d9430` deployment, then the preflight cell, not the scientific One-Run cell). Superseded by the deployment-only correction `f8d00d7` below: complete clean suite is green (1,834 passed / 32 skipped / 0 failed); aggregation is now `e5d9430`.


## Pre-Benchmark Final Source Repin (2026-08-03) — Deployment-Only Correction

The previous `76a6b16` gate had **1 failure, not a green full suite**: full suite =
**1,833 passed / 32 skipped / 1 failed**. The sole failure was
`test_notebook_source_commit_matches_deployed_runtime_tree`, structural because the
mandated `pyproject.toml` declaration change broke byte-identity with the pinned
`aac9914` SOURCE_COMMIT. **Root cause:** dependency declarations changed
`pyproject.toml` after the `aac9914`/`311e084` deployment pin. **No runtime, prompt,
metric, scenario, evaluator, or data change was needed.**

The exact independently reviewed **deployment-only correction** `f8d00d7`
(`chore(deploy): repin reproducible pre-benchmark source snapshot`, imported via
bundle fast-forward `PRE_BENCHMARK_FINAL_REPIN_EXACT.bundle`, exactly one commit)
re-pins the deployment to the current source snapshot:

1. `kaggle_upload/code/pyproject.toml` gains the six declaration lines
   (`tabulate==0.10.0`, `httpx==0.28.1`, `Jinja2==3.1.6`, `pytest-asyncio==1.2.0`,
   `huggingface_hub==0.24.0`, `types-pyyaml>=6.0,<7`) and is now **byte-identical**
   to the canonical `pyproject.toml` (verified: identical, 1,948 bytes).
2. Both canonical and generated notebooks re-pin
   `SOURCE_COMMIT = e5d943065c6f4158c30a1cbbba39436ab2a7a898` /
   `DEPLOYED_BUILD_ID = e5d9430`. Deployment source snapshot = `e5d9430`;
   deployment correction = `f8d00d7`.
3. Manifests re-verified.

The complete clean gate on the declarations-only environment is now **green**:
full suite = **1,834 passed / 32 skipped / 0 failed** (identity test passes);
Dataset Validation 285 passed / 5 skipped (data unchanged); Prompt Validation 158
passed; Pipeline Smoke 220 passed / 12 skipped; Dry Run 9/9; Integration PASS;
Metric Verification 169 passed; mypy strict Success (77 files); ruff 93 = 93
baseline (0 new); compileall clean; all notebook code cells compile (7/7 + 7/7);
bundle build content-identical (147 files / 928,329 bytes); manifests verified;
no cache files in `kaggle_upload`; tree clean. Historical `exp-20260801-210443`
failed model-output record under `6f88823` remains excluded from the current
 `e5d9430` aggregation; current accepted real records = **0/9**; no scientific
evidence; no tag; no Pilot; no Kaggle launch. Next action after this independent
audit: **Kaggle engineering preflight only** (update the Kaggle code dataset +
notebook to the corrected `e5d9430` deployment, then the preflight cell, not the
scientific One-Run cell).

## Post-Smoke Calibration Closure (2026-08-03)

The post-smoke calibration closure on branch `fix/kaggle-smoke-v2-model-output-closure`
(HEAD `231b0a5`, pushed, local = remote, tree clean) closed the four proven
control defects the real calibration run `exp-20260803-002741` exposed, then
pinned and reconciled the gate:

- **Commit `27c1693`** (runtime + tests): per-attempt atomic regeneration
  (normalize + validate every selected artifact, stage accepted bytes, write
  zero files of the attempt on any guard failure); repair no-progress detection
  (`repair_no_progress` early-stop on an identical repair response hash after
  validation feedback, no new round, consumed calls/tokens retained);
  fail-closed calibration continuation gate
  (`AUTHORIZE_CONTINUOUS_AFTER_CALIBRATION_REVIEW = False`;
  `scientific_failure` prints `CALIBRATION_REVIEW_REQUIRED`, only a deliberate
  human change to `True` authorizes the continuous cell); cooperative deadline
  semantics (deadline checked before every selection/generation/repair call;
  workflow budget exhaustion = scientific terminal
  `scientific_budget_exhausted` with `configured_budget` /
  `actual_elapsed_seconds`; preflight/env/harness/HF timeouts stay engineering
  blockers).
- **Commit `56772fe`** (deployment): notebook re-pin
  `SOURCE_COMMIT = 27c1693e22b1a68be0b299fb146d9ff1e500908b` /
  `DEPLOYED_BUILD_ID = 27c1693`; bundle rebuilt (147 files / 934,495 bytes;
  code 90 / data 56 / notebook 1); manifests verified; both notebooks compile
  7/7 code cells.
- **Commit `231b0a5`** (test-fixture reconciliation): the nine failures of the
  first full gate were **stale constant-output integration fixtures**
  (`test_r4_metric_contract.py`, `test_su0010a_regeneration.py`) that
  accidentally activated the new no-progress early-stop. They were **not
  validly proven pre-existing**: `ec9ba0b` lacked the early-stop, and a detached
  worktree using the main editable installation can import the current branch
  instead of the worktree source. The fixtures now return distinct valid Python
  per call (`_FixedTokenBackend(vary_output=True)` for the three duration tests,
  unique per-index `_SentinelBackend` output, `value = <call_number>` for the
  five bounded-repair fixtures); every expectation was preserved (max_attempts
  3, calls 3/6, `repair_attempts`, `repair_model_calls` 2/4, durations 1.5/2.1,
  tokens 41/59/90, JSONL/reporting identity); dedicated identical-output
  no-progress tests unchanged; new boundary test
  `test_no_progress_and_max_attempts_are_separate_contracts` proves constant
  output → 2 calls + `repair_no_progress` vs distinct outputs → 3 calls /
  2 repairs. Runtime semantics, prompts, scenarios, datasets, evaluators,
  strategies, and metrics were never changed.

Final gate: full suite = **1,849 passed / 32 skipped / 0 failed**; mypy strict
`src/benchmark` Success (77 files); ruff 93 = 93 baseline (identical line-set,
0 new); compileall clean; bundle content-identical; `git diff --check` clean;
tree clean. Calibration evidence `exp-20260803-002741` (9 terminal records /
0 succeeded / 8 failed / 1 timed_out / 81 model calls / 118,211 tokens) is
**preserved and not an accepted scientific comparison**; latest real
calibration = **0/9**. No Kaggle rerun; no tag; no merge; Pilot not authorized.
Next action after this independent audit: **one selective calibration canary
only** (not a full relaunch, not a fine-tune, not a tag/merge).
Sentinel: `POST_SMOKE_CALIBRATION_CLOSURE_AUDIT_REQUIRED`.

## Final Selective Canary Readiness Closure (2026-08-04)

The independent GPT-5.6 Thinking audit at `f727b3e` **rejected canary readiness**
even though the full suite was green, based on three independently reproduced
blockers. All three are closed on branch `fix/kaggle-smoke-v2-model-output-closure`
(HEAD `356722b`, pushed, local = remote, tree clean):

- **Blocker 1 — per-call cooperative deadline.** Direct reproduction: 1s
  timeout, 3 selected artifacts, budget advanced after call 1 → **3 model calls
  and false success**. Commit `50ec2c1` checks the workflow deadline before every
  selection/generation/repair model call; an in-flight call returning beyond the
  deadline consumes/records its tokens, makes no next call, writes none of the
  staged attempt, and returns the failed scientific terminal
  `scientific_budget_exhausted` with truthful elapsed time and budget. The same
  guard applies to every internal Iterative Agent call, not only before
  `analyze_impact()`. Direct adversarial proofs: generation (1 call, count 0,
  15 tokens), repair (2 calls, `repair_model_calls == 1`, repair tokens
  retained), iterative agent (1 call, `model_call_budget_exhausted`, 50 tokens
  preserved).
- **Blocker 2 — atomic metric truth.** Direct reproduction: **0 writes but
  `regenerated_artifact_count = 1`** when an artifact was rejected. On atomic
  attempt abort, all staged `generated` statuses become `aborted` or `rejected`,
  `regenerated_artifact_count = 0`, preserved response hashes/evidence remain
  available; an all-valid attempt still commits every artifact exactly once.
  Metric/evidence truth, not a scientific formula change. Commit `356722b`
  aligns the affected tests with the truthful staged statuses.
- **Blocker 3 — dedicated selective canary cell.** The generic one-run cell
  selects `todo-smoke-001 / monolithic` (execution-plan order is scenario first,
  then strategies), NOT selective. Commit `28ecc5a` adds a dedicated, separately
  named Selective Calibration Canary cell (`selective-calibration-canary-cell`):
  `--strategy selective --max-runs 1 --new-experiment --backend kaggle-qwen
  --profile scientific-smoke-v2 --max-attempts 3 --max-completion-tokens-per-call
  1024 --max-total-workflow-tokens 0 --timeout 300 --hf-sync`, isolated output
  `runs/selective_calibration_canary`, NO `--auto-resume-hf`,
  `AUTHORIZE_CONTINUOUS_AFTER_CALIBRATION_REVIEW = False`.
  `_verify_selective_canary()` asserts exactly one current-source RunRecord
  `todo-smoke-001 / selective`, model identity `qwen:1:int8`, model calls > 0,
  terminal scientific success/failure outcome, HF `recovery_uploaded`, checkpoint
  `total_planned = 3 / completed = 1 / pending = 2`.

Deployment pinned: `SOURCE_COMMIT = 50ec2c1ca43c230aed4538be32ca7dab2ccc22e5`,
`DEPLOYED_BUILD_ID = 50ec2c1`; bundle rebuilt (147 files / 948,250 bytes; code
90 / data 56 / notebook 1); content-identical rerun (tree hash
`3b8d5b0ebf5e3ab8`); all 8 bundle notebook code cells compile.

Final gate: full suite = **1,856 passed / 32 skipped / 0 failed**; grouped
per-category 629 passed / 1 skipped; scripted dry run `--profile
scientific-smoke-v2` into a fresh dir = 9/9 exit 0 (the default `runs` dir held
a stale checkpoint causing `ReportRebuildError`, not a code defect); mypy strict
`src` Success (77 files); ruff 0 new findings (175 pre-existing repo-wide, 19
pre-existing E501 in `test_r4_token_and_metrics.py`); compileall clean; `git
diff --check` clean; tree clean. Calibration evidence `exp-20260803-002741`
remains **preserved, 0/9 success, not accepted scientific evidence**. No Kaggle
rerun; no tag; no merge; Pilot not authorized; **no stable release claimed**.
Next action after this independent re-audit: **run the dedicated selective
calibration canary cell only** (not the generic one-run cell, not the continuous
cell, not a full relaunch, not a fine-tune, not a tag/merge).
Sentinel: `FINAL_SELECTIVE_CANARY_READINESS_AUDIT_REQUIRED`.

## Selective Calibration Canary Result (2026-08-04)

The dedicated selective calibration canary was executed on Kaggle under the
pinned bundle (source/build `50ec2c1`) and its result is recorded in
`selective_updates/records/SELECTIVE-CANARY-RESULTS-2026-08-04.md`.

- **Canary result `exp-20260804-133523`** (`todo-smoke-001 / selective`):
  **failed / `model_output`**, 4 model calls / 5,804 tokens / 257.596 s,
  3 selected / 2 preserved / **0 written**; initial 3 calls / 3,372 tokens;
  repair 1 call / 2,432 tokens; HF `recovery_uploaded`; checkpoint 1 completed /
  2 pending.
- **Qwen output defects:** `todo/models.py` `max_length=5` (the `MEDIUM` value
  has length 6); duplicated `Priority(models.TextChoices)` in
  `todo/serializers.py` and `todo/views.py`. The first repair was byte-identical
  to the initial response, so `repair_no_progress` stopped the round and the
  atomic application wrote zero files.
- **Harness vs model:** versus the previous selective run the canary used 41.6%
  fewer tokens, 33.3% fewer calls, and was 22.4% faster — but the initial
  generation tokens (3,372) and the three output SHA-256 hashes were identical.
  The harness safety controls (per-call deadline, no-progress detection, atomic
  writes, fail-closed continuation gate) worked exactly as designed, while
  **Qwen code quality did not improve**.
- **Incidental monolithic run `exp-20260804-133016`** (6 calls / 7,927 tokens /
  300.165 s / `scientific_budget_exhausted`, 0 written) is diagnostic evidence
  only — NOT the authorized canary and NOT an accepted comparison.
- **Continuous cell:** correctly blocked fail-closed with
  `CALIBRATION_REVIEW_REQUIRED`; it made no additional scientific calls.
- **Current scientific truth:** accepted current dedicated canary records = 1,
  successful = 0; the full current 9-record experiment is **not run**;
  merge/tag/Pilot/Kaggle **not authorized**; **no stable release claimed**.

Decision from the independent audit: harness safety controls worked; Qwen code
quality did not improve. Next action: independent result audit
(`SELECTIVE_CANARY_RESULT_AUDIT_REQUIRED`), then a deliberate decision between
repeating the dedicated selective canary and proceeding to the full 9-record run.

R6_ACCEPTED_FREEZE_AND_PUBLISH_AUTHORIZED

## Final Qwen 14B NF4 Preflight Closure (2026-08-05)

The independent audit reproduced three preflight blockers on the `5ef6438`
state (full suite was green there, but the audit rejected real preflight). All
three are closed on branch `fix/kaggle-smoke-v2-model-output-closure`:

1. **Canary used `SELECTIVE_CANARY_OUTPUT_DIR` before assignment.** The
   definition lived inside the `selective-calibration-canary` cell while
   `CANARY_PREFLIGHT_DIR = SELECTIVE_CANARY_OUTPUT_DIR / "preflight"` referenced
   it earlier — a `NameError` at canary run time. Fix A moved the definition to
   the `setup-cell` (right after `OUTPUT_DIR`) and removed the duplicate
   assignment.
2. **Preflight required exactly one visible GPU.** `EXPECTED_VISIBLE_GPU_COUNTS
   = (1, 2)` now accepts real 2×Tesla T4 environments and reports
   `FAIL (N; expected 1 or 2)` otherwise (Fix B).
3. **Numeric version dirs produced a `qwen:1:*` readable identity.**
   `_checkpoint_identity_slug` maps e.g. `.../14b-instruct/1` → `14b-instruct-v1`
   → `qwen:14b-instruct-v1:bnb-nf4:cfg-<12hex>` in `compute_model_identity` and
   `checkpoint_basename` (Fix C).

Commit A `0aa705d` (runtime + tests + notebook) and Commit B `cc7846b`
(deployment repin) are pushed, local = remote, tree clean. Official gate =
declared clean environment (Python 3.11.9 / pytest 8.4.2): full suite
**1,890 passed / 32 skipped / 0 failed**; Dataset 285/5; Prompt 174; Pipeline
Smoke 223/12; Dry Run 9/9 (exit 0); Metric Verification 169; Ruff 0 new (91
pre-existing baseline); mypy strict Success (77 files); compileall clean;
notebook 8/8 + 8/8 compile; builder content-identical (147 files /
963,067 bytes). Regression proofs: **2-GPU preflight = PASS** and **canary
reaches subprocess construction without NameError**. No Kaggle run, no canary,
no continuous, no model/quantization/prompt/data/scenario/evaluator/metric
change, no GPTQ/AWQ/GGUF/vLLM, no merge/tag/Pilot. **No real 14B result and no
stable release claimed**; accepted real records remain 0/9. Next action after
independent audit = **Kaggle engineering preflight cell only**.
Sentinel: `QWEN14B_FINAL_PREFLIGHT_CLOSURE_AUDIT_REQUIRED`.

## Qwen 14B NF4 Transformers v4 Loader Closure (2026-08-05)

The independent OOM audit reproduced the real preflight OOM on the `9fd4eee`
state (full suite was green there, but the real load OOM'd on Kaggle). Root
cause: transformers was unpinned in the Kaggle runtime, image drift installed
**5.0.0**, and the 5.0.x loader materialized the **14B BF16 weights on GPU
before BNB-NF4 quantization** — OOM after 232.412 s at ~75% of 579 checkpoint
params (tried 136 MiB; GPU 1 free 46.81 MiB / allocated 14.38 GiB; runtime
Python 3.12.13 / transformers 5.0.0 / bitsandbytes 0.49.2 / accelerate 1.14.0 /
torch 2.10.0+cu128). All fixes are closed on branch
`fix/kaggle-smoke-v2-model-output-closure`:

1. **Transformers pinned to `==4.57.6`** in `requirements-smoke-kaggle.lock` and
   `requirements-kaggle.txt`; torch stays unpinned (Kaggle image provides its
   GPU torch build — no torch pin in the lock).
2. **Fail-closed preflight version check**: `_REQUIRED_IMPORTS` now requires the
   exact `"4.57.6"`, so `dependency_import_verification` FAILs with
   `transformers=5.0.0 (expected 4.57.6)` before staging/model load; absent
   transformers also FAILs.
3. **Notebook install-lock-cell**: `EXPECTED_RUNTIME` gains
   `"transformers": ("transformers", "transformers", "4.57.6")` with the
   fail-closed mismatch check; setup-cell repinned to `SOURCE_COMMIT =
   41e9ad70c86ac696ce6ceaacd6b6892889bcc48a` / `DEPLOYED_BUILD_ID = 41e9ad7`.
4. **BNB loads pass `low_cpu_mem_usage=True`** in
   `kaggle_qwen_backend._load_model` for `bnb-int8` and `bnb-nf4` (fp16
   unchanged), so the 4.57.x loader streams/quantizes in place instead of
   materializing the full-precision temporary copy.
5. **Static preflight metadata on load failure**: `_static_model_metadata`
   reads `config.json` + CUDA discovery (no weight load) and fills
   `model_identity` / `checkpoint_basename` / `checkpoint_quantization_method` /
   `gpu_count` / `gpu_name` even when the probe OOMs or fails.

Commit A `41e9ad7` (runtime + tests + notebook) and Commit B `920ab9b`
(deployment repin) are pushed, local = remote, tree clean. Gate = ambient
Python 3.11.5 / pytest 9.1.1 (declared clean env `_workspace\cache\
prebenchmark-py311` is NOT present locally — independent audit must recreate it
for the official gate): full suite **1,898 passed / 32 skipped / 0 failed**;
Ruff 0 new (86 pre-existing baseline); mypy strict Success (77 files);
compileall clean; notebook cells compile canonical + bundled; bundle pin
identity PASS; bundle integration 32 passed; builder content-identical (147
files / 964,859 bytes). Regression proofs: **preflight FAILs on transformers
5.0.0 / NOT_INSTALLED before load**, **BNB int8 + NF4 loads pass
`low_cpu_mem_usage=True` (fp16 does not)**, **static model/GPU metadata
preserved on failed probe**. No Kaggle run / canary / continuous / merge / tag /
Pilot; no model, quantization, prompt, data, scenario, evaluator, or metric
change; no GPTQ/AWQ/GGUF/vLLM (no new backend); **no real 14B result and no
stable release claimed**; accepted real records remain 0/9. Next action after
independent audit = **Kaggle engineering preflight cell only**.
Sentinel: `QWEN14B_V4_LOADER_OFFICIAL_GATE_AUDIT_REQUIRED`.

## Qwen 14B NF4 v4 Loader Official Gate (2026-08-05)

The missing official clean-environment gate for the loader closure was run, and
one stale Notebook markdown statement was corrected (docs/deploy only — no
runtime code, tests, requirements, data, prompts, scenarios, strategies,
evaluator logic, metrics, model settings, or runtime limits changed).

1. **Notebook markdown truth (the only file edit).** The markdown cell
   immediately before `preflight-cell` described the load as `int8`
   (`load_in_8bit=True` + `device_map="auto"` with `expandable_segments`). It
   now truthfully reads: **Qwen 14B BNB-NF4 load** — `Qwen2.5-Coder-14B-Instruct`
   base checkpoint via BitsAndBytes NF4: `load_in_4bit=True`,
   `bnb_4bit_quant_type="nf4"`, `bnb_4bit_compute_dtype=float16`,
   `bnb_4bit_use_double_quant=True`, `device_map="auto"`, Transformers 4.57.6.
   No executable code cell, `SOURCE_COMMIT`/`DEPLOYED_BUILD_ID` (`41e9ad7`),
   command, quantization setting, model path, timeout, token limit, or auth flag
   changed.
2. **Official clean-environment gate.** Fresh disposable env
   `_workspace\cache\prebenchmark-py311-v4-loader` created from project
   declarations only (`pip install -e ".[dev]" pytest==8.4.2 ruff==0.15.22
   mypy==1.20.2`); Python 3.11.5 / pytest 8.4.2 exactly; Django 5.2.16, DRF
   3.17.1, pytest-django 4.12.0, pytest-asyncio 1.2.0.
3. **Gate results.** Dataset Validation 281 passed / 4 skipped; Prompt
   Validation 126 passed / 4 skipped; Pipeline Smoke 177 passed; Scripted dry
   run `--profile scientific-smoke-v2` 9 planned / 9 terminal / 9 succeeded /
   0 failed / exit 0; Complete Integration **1,898 passed / 32 skipped / 0
   failed** (517.97 s); Metric Verification 169 passed; Ruff 0 new (91
   pre-existing baseline); mypy strict Success (77 files); compileall clean;
   notebook code cells compile canonical + bundled; bundle rebuilt twice via
   `scripts/build_upload_bundle.py` — second run content-identical (147 files /
   965,015 bytes; tree hash 26EA934F16A25C14788484CE1A75EFF4FB453E6C346F5FDCEE72D3004EC5B7D1),
   manifests verified, no cache files; `git diff --check` clean.

Commit `docs(deploy): finalize Qwen 14B NF4 loader gate truth` pushed, local =
remote, tree clean. No Kaggle run, no preflight, no canary, no continuous, no
merge/tag/Pilot; **no real 14B result and no stable release claimed**; accepted
real records remain 0/9. Next action after independent audit = **Kaggle
engineering preflight cell only**.
Sentinel: `QWEN14B_V4_LOADER_OFFICIAL_GATE_AUDIT_REQUIRED`.

## Qwen 14B Multi-GPU VRAM Preflight Closure (2026-08-06)

The independent audit (QWEN14B_MULTI_GPU_VRAM_PREFLIGHT_INDEPENDENT_AUDIT_2026-08-06.md) accepted that the 897e323 state was full-suite green but found one missing preflight invariant: **VRAM headroom was measured and enforced on GPU 0 only**. On a 2x Tesla T4 Kaggle runtime with device_map="auto", the Qwen 14B bnb-nf4 model is distributed across both GPUs, and the old gate read 	orch.cuda.memory_allocated(0) / memory_reserved(0) / mem_get_info(0) / synchronize(0) and checked a single
ree_vram_after_probe_gib — so GPU 1 with <2.0 GiB free was invisible and the preflight could pass while the second GPU was about to OOM. All fixes are closed on branch
ix/kaggle-smoke-v2-model-output-closure:

1. **Immutable per-GPU snapshot type** — GpuVramSnapshot (device_index, gpu_name, llocated_gib,
eserved_gib,
ree_gib, 	otal_gib).
2. **_collect_gpu_vram_snapshots()** — iterates
ange(torch.cuda.device_count()), synchronizes **every** device, reads memory_allocated(i) / memory_reserved(i) / mem_get_info(i) per GPU, rounds GiB to three decimals, returns () when CUDA unavailable, and **never swallows** a per-GPU failure; no tensors allocated.
3. **Probe metrics semantics** — after the probe the helper is called once; gpu_vram_by_device persisted;
ree_vram_after_probe_gib = min(snapshot.free_gib), llocated_vram_gib/
eserved_vram_gib = sums (three decimals); gpu_name stays device 0 name; gpu_count stays visible GPU count; preflight FAILs when gpu_count > 0 but no snapshots exist.
4. **Minimum-free gate on every visible GPU** —
ram_headroom: PASS (minimum free across 2 GPU(s)=X.XX GiB); failure lists every failing device deterministically by index (FAIL (GPU 1 free=0.12 GiB < 2.0 GiB)); free memory is never averaged/summed for the gate.
5. **Failure-path evidence** — _static_model_metadata includes gpu_vram_by_device, so a failed model load/probe still preserves real per-GPU count, names, and memory (tokens/footprint may stay zero; preflight still fails). No forced CUDA imports when dependency verification fails first.
6. **Result + JSON schema** — KaggleSmokePreflightResult.gpu_vram_by_device: tuple[GpuVramSnapshot, ...] = (); ordered per-GPU objects in kaggle_smoke_preflight.v1 JSON; one human-readable line per GPU; no existing JSON field removed/renamed.

Commit A
7b1ebb (code + tests) and Commit B c8f5685 (deployment repin, SOURCE_COMMIT=f7b1ebb / DEPLOYED_BUILD_ID=f7b1ebb) are pushed, local = remote, tree clean. Official clean-env gate (_workspace\cache\prebenchmark-py311-v4-loader, Python 3.11.5 / pytest 8.4.2 exactly): full suite **1,915 passed / 32 skipped / 0 failed** (500.22 s; +17 net new tests); Metric Verification 169 passed; Ruff 0 new (86 pre-existing baseline); mypy strict Success (77 files); compileall clean; notebook + bundle pin identity PASS; bundle integration 32 passed; builder content-identical (147 files / 968,722 bytes). Mandatory adversarial reproduction: **GPU0 free 3.0 GiB / GPU1 free 0.125 GiB → FAIL**. No Kaggle run, no preflight on Kaggle, no canary, no continuous, no merge/tag/Pilot; no model, quantization, prompt, data, scenario, evaluator, or metric change; no GPTQ/AWQ/GGUF/vLLM; **no real 14B result and no stable release claimed**; accepted real records remain 0/9. Next action after independent audit = **Kaggle engineering preflight cell only**. Sentinel: QWEN14B_MULTI_GPU_VRAM_CLOSURE_AUDIT_REQUIRED. Record: selective_updates/records/QWEN14B-MULTI-GPU-VRAM-PREFLIGHT-CLOSURE.md.


## Qwen 14B Selective Canary Success (2026-08-07)

The independent GPT-5.6 Thinking audit **ACCEPTED SUCCESSFUL REAL CANARY** on branch `fix/kaggle-smoke-v2-model-output-closure` (documentation HEAD `5561f918`). Docs-only closure - no code, tests, data, prompts, configs, notebook executable cells, or kaggle_upload changes.

**Real engineering preflight PASS** on 2x Tesla T4 (Python 3.12.13 / transformers 4.57.6 / bnb-nf4): identity `qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25`; footprint 9,721,981,184 bytes; preflight 174.016 s; probe 68+17 tokens; minimum free VRAM **8.417 GiB** - GPU-only device map, no offload.

**Canary `exp-20260807-131819`** (`todo-smoke-001 / selective`, runtime source `f7b1ebba73b52868a95c47ef3806d3b09da16d93` / build `f7b1ebb`): **succeeded** - 3 selected / 2 preserved / 3 regenerated; one migration `todo/migrations/0004_task_priority.py`; 3 model calls / 2,527 prompt + 720 completion = 3,247 tokens / 295.944 s / 0 repair attempts; functional validation PASS; scenario evaluator **PASS 10/10**; HF `recovery_uploaded`.

Accepted real 14B canary records = **1 succeeded / 0 failed** (isolated selective-only plan - NOT `1/9`). At the time this canary was accepted, Full 9-record Scientific Smoke V2 had not yet been run; subsequently the first Full-9 `exp-20260807-205422` was run under `f7b1ebb` and REJECTED for workspace contamination; a fresh corrected Full-9 under `7f2a450` was pending (HISTORICAL — later executed and accepted as `exp-20260808-222843`).

Interpretation: 14B crossed the 7B model-quality floor on the same task (25.0% fewer calls / 44.1% fewer tokens / repair eliminated / 14.9% slower) - functional viability, not strategy superiority. Generated `views.py` has an unused `Q` import (non-blocking; evidence workspace must NOT be repaired). The continuous cell failed closed with zero model calls because the generic experiment was empty - not a failure; do NOT patch the continuous workflow before Full-9.

No merge/tag/Pilot; no fine-tune; no Kaggle rerun. **Next action = independent delta audit of the FULL9-WS-02A runbook/docs closure**; only if accepted, exactly one fresh corrected Full-9 Scientific Smoke V2 (3 scenarios x 3 arms = 9 records; SOURCE_COMMIT=7f2a4509482dc7e62c2b243374592e9a88e2ff48 / DEPLOYED_BUILD_ID=7f2a450) using the corrected runbook `docs/KAGGLE_QWEN14B_FULL9_SCIENTIFIC_SMOKE_RUNBOOK.md` - one engineering preflight + one benchmark process, fresh isolated experiment, never resume/merge the canary or the rejected `exp-20260807-205422`, then independent results audit. Record: `selective_updates/records/QWEN14B-SELECTIVE-CANARY-SUCCESS-2026-08-07.md`. Sentinel: `QWEN14B_CANARY_SUCCESS_DOCUMENTED_FULL9_READY`.
