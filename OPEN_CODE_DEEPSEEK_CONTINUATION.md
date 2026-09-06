# Continuation instruction for OpenCode DeepSeek

Continue and finish RESULTS-RECOVERY-02 in this same repository. Do not restart the task, redesign the protocol, or repeat completed work.

## Required first actions

1. Print your exact implementation model identity.
2. Run only:
   - `git status --short`
   - `git diff --stat`
   - `git diff --name-only`
3. Read `AGENTS.md` and the complete authoritative pack, in numeric order, at:
   `../_workspace/active/RESULTS_RECOVERY_02_PRODUCTION_READY_PACK/`
4. Verify the pack manifest before acting.
5. Preserve all user-owned untracked files. In particular, do not add, edit, delete, or clean:
   - `GIT_STATE.txt`
   - `reports/dryrun_scientific_microstudy/`
   - `reports/dryrun_wip_impactplan/`
   - `uv.lock`

## Current exact state

- Branch: `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`
- HEAD and upstream: `5acf0e366a457fed57e710e34a9d92f1e508a469`
- Required pushed checkpoints already exist:
  - `565d11ccfbbc3009f0e1ba01a4925de3364dc5ba` — freeze scientific interface v1.1 documentation
  - `fa16410852f51e0abdbfd3c5c3cafe057d06d875` — native structured interfaces and focused tests
  - `da09cf5a7826fc26b23017011c61150b10f8b7c6` — v1.1 exactly-six-gate wiring
  - `5acf0e366a457fed57e710e34a9d92f1e508a469` — local batch-resume durability and result artifact writer
- All four commits are pushed. No paid/model generation call has been made in this recovery task.
- Historical experiment `exp-20260905-225518` remains immutable.
- Its raw record is `reports/scientific_microstudy/run_records.jsonl`.
- Required preservation witness at handoff:
  - bytes: `136621`
  - SHA-256: `222A63E91F91369F38A201A4F3ED00A6EF2FF39FC7BF52E7A9262F32F9AA5871`
- Recompute that hash before final reporting and require an exact match.
- Older active instruction packs were already moved recoverably to:
  `../_workspace/archive/2026-09-06-before-results-recovery-02/`
- Only `RESULTS_RECOVERY_02_PRODUCTION_READY_PACK` should remain active.

## Completed implementation

The following v1.1 work is already implemented and pushed. Inspect narrowly and fix only demonstrated defects:

- OpenRouter native `response_format.type=json_schema` transport.
- Strict native `PatchEnvelope` schema/parser; trailing prose and empty patch lists fail closed.
- Patch and repair cap 8192; `finish_reason=length` fails visibly without writes.
- `search_text` accepts a safe file or directory.
- Agent control cap 1024 for v1.1; calls 1-7 may explore; call 8 is forced final; no ninth call; repeated identical tool requests are not re-invoked.
- Native structured Agent action/final schemas.
- ImpactPlan native schema and 4096 cap.
- ImpactPlan v1-to-v2 bounded expansion is the only plan repair path; final version/hash/parent provenance is persisted through the runner.
- v1.1 CLI profile: three Todo scenarios x Agent/ImpactPlan x five repetitions = 30.
- Agent/planner/patch/repair caps are persisted in model metadata.
- Two real non-study E2E acceptance probes use the actual runner and require functional-validation reach and pass.
- DeepInfra capability probe occurs first. NovitaAI is authorized exactly once only for a DeepInfra provider/API-level JSON-schema rejection, never for semantic failure or ordinary availability.
- Exactly-six-gate validator is wired for v1.1.
- Local `--resume` preserves normalized checkpoint state, permitting required 10/20/30 batches.
- Results builder rejects mixed historical protocols and writes:
  - `reports/SCIENTIFIC_MICROSTUDY_V11_RESULTS.csv`
  - `reports/SCIENTIFIC_MICROSTUDY_V11_RESULTS.md`
  - `reports/SCIENTIFIC_MICROSTUDY_V11_DECISION.md`

## Completed validation

- Focused implementation set: `197 passed, 4 skipped`.
- Checkpoint/result focused set: `138 passed`.
- Additional focused regression: `109 passed`.
- Ruff passed on all changed Python files.
- Mypy strict passed on the seven changed source modules.
- `git diff --check` passed.
- The full suite has NOT been run. It must be run exactly once, only at the prescribed final gate after real acceptance, six gates, and Audit.

## Current blocker

The host process, Windows user environment, and Windows machine environment all lacked `OPENROUTER_API_KEY`. Do not print or persist the key. Before continuing, require the user to inject it into the OpenCode execution environment, then check presence only. This missing credential—not a provider/model failure—is the only known blocker.

## Mandatory remaining sequence

Follow the authoritative pack exactly. The remaining work is:

1. Confirm `OPENROUTER_API_KEY` is present without displaying it.
2. Confirm HEAD equals upstream before model calls.
3. Run `scripts/run_model_acceptance_gate.py` using `qwen/qwen3-coder` pinned to DeepInfra.
   - First make the cheap native JSON-schema capability call.
   - Only if DeepInfra rejects JSON Schema at provider/API capability level, try NovitaAI once.
   - Then run both real non-study E2E probes: Agent and ImpactPlan.
   - Both must produce valid structured output, reach functional validation, and pass it.
   - On genuine semantic/provider incompatibility, preserve raw/redacted evidence and STOP. Add no parser heuristic.
4. If acceptance passes, commit and push the acceptance report and model/provider/pricing freeze. Verify HEAD equals upstream.
5. Run exactly the six v1.1 Pre-Benchmark gates through `scripts/validate_scientific_wip_prebenchmark.py`:
   - Dataset Validation
   - Prompt Validation
   - Pipeline Smoke Test
   - Dry Run
   - Integration Test
   - Metric Verification
6. Perform and record the independent Audit required by the pack:
   - gold leakage
   - context/action separation
   - write guard
   - bounded expansion
   - repair provenance
   - cap freeze
   - provider pin
   - historical-run preservation
   - over-engineering check
7. Run the complete pytest suite exactly once. Record exact pass/skip/fail counts. Do not rerun the full suite.
8. Estimate the additional 30-run OpenRouter cost using actual probe usage, frozen role caps, and current pinned-provider prices.
   - If estimate is `<= $1.50`, continue automatically.
   - If `> $1.50`, STOP before scientific calls.
9. Create a new v1.1 experiment directory and ID. Never write into `reports/scientific_microstudy/` and never reuse `exp-20260905-225518`.
10. Run all 30 real cells in three durable batches of 10 with the same output directory and `--resume` for batches 2 and 3.
    - Model: `qwen/qwen3-coder`
    - Provider: the provider frozen by acceptance
    - Protocol/profile: `scientific-wip-impactplan-v1.1`
    - Strategies: `iterative_repository_agent`, `impact_plan`
    - Repetitions: 5
    - Exact patch: true
    - Agent cap: 1024
    - Planner cap: 4096
    - Patch cap: 8192
    - Repair cap: 8192
    - Timeout: 900
    - No provider fallback
    - Persist every attempt; do not rerun an unattractive but valid scientific failure.
11. After attempted run 10, commit and push the new evidence, then verify upstream.
12. After attempted run 20, commit and push, then verify upstream.
13. After attempted run 30, commit and push, then verify upstream.
14. Run `scripts/build_todo_microstudy_results.py` on the new v1.1 run directory to create the three prescribed result files. Verify the report covers functional reach, Agent finalization, ImpactPlan action precision/recall/F1/FNR/support, functional correctness, preservation/regression, prohibited writes, expansion/H, provenance, truncations by role, actual usage vs caps, cost, qualified-run efficiency, and frozen GO/NO-GO.
15. Update current-truth/state documentation narrowly with actual results. Commit and push all final evidence.
16. If the v1.1 evidence is complete, non-vacuous, and auditable, create annotated tag `wip-impactplan-v1.1-evidence`, push it, and verify local/remote peeled targets. Otherwise state precisely why there is no evidence tag.
17. Create the required LIGHT ZIP outside the project named `project-YYYY-MM-DD-HHmm.zip`, containing only `src`, `tests`, `scripts`, `benchmark_data`, `configs`, `docs`, `reports`, root research/state files, and `GIT_STATE.txt`. Exclude `.git`, `dist`, Kaggle archives, `node_modules`, caches, old ZIPs, and dry-run bulk output. Print exact bytes and SHA-256.
18. Recompute and verify the historical raw-record SHA-256 and size.
19. Produce the stop report using `08_STOP_REPORT_TEMPLATE.md`, including every mandatory final line verbatim in the required key/value form.
20. STOP after results.

## Operational cautions

- Do not use or stage the untracked `uv.lock` unless the user explicitly authorizes it.
- The normal test command may require host access to the managed uv Python installation. Use the existing workspace-local cache path and request escalation only when needed.
- Preserve all unrelated user changes.
- Use `apply_patch` for edits.
- Do not run the full suite before its one authorized point.
- Do not browse for technical implementation guidance; use primary provider metadata/documentation only if current price verification needs it.
- Do not add a model, repository, metric, gate, framework, parser fallback, or dynamic token-cap increase.
- If actual native schemas are rejected semantically because they violate provider strict-schema rules, that is a demonstrated implementation defect only if the provider supports the feature. Fix the schema narrowly and rerun focused tests before repeating the acceptance sequence. Do not reinterpret a semantic model failure as provider capability failure.

The goal is not another readiness report. The goal is complete v1.1 evidence, the frozen GO/NO-GO decision, durability, tag decision, LIGHT export, and then STOP.
