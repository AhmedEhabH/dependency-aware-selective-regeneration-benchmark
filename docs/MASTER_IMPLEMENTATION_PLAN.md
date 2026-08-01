# Master Implementation Plan

## Dependency-Aware Selective Regeneration for LLM-Assisted Software Evolution

## Authoritative Current Execution Track

```text
R4 = accepted and frozen (f5ae826)
R5 = accepted and frozen (7761c48)
R6 = ACCEPTED AND FROZEN (949e9c2) — freeze record and milestone-branch publication authorized
Push = next (publish with upstream, verify local/remote equality)
Real Smoke = 0/9 (local scripted 9/9; bundled CLI dry-run 9/9)
Tag = v2.0.0-scientific-smoke after real-result audit
Pilot = denominator not frozen; not authorized
```

Exact path from R6 freeze to Pilot freeze:

```text
record R6 freeze
→ push branch and set upstream, verify local/remote equality
→ record publication status and push again
→ Kaggle environment preflight
→ nine real Qwen Scientific Smoke V2 records (3 scenarios × 3 arms × 1 rep)
→ independent real-result audit
→ stable v2.0.0-scientific-smoke tag
→ freeze Pilot matrix and authorize Pilot
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
- **Execute Scientific Smoke V2 on Kaggle** — 3 arms × 3 changes × 1 rep = 9 real runs
- Pilot (remains unauthorized until Scientific Smoke V2 passes audit)
- **Complete:** 0a1c603 baseline verified (1063 pass, 5 skip), three-arm core experiment documented, 3 smoke scenarios created, evaluator tests isolated, contract tests added

## Known Boundary

- neutral empty graph when no profile graph exists
- real repository dependency inference remains deferred
- OpenRouter API backend is provider-integration only; no retries, streaming, or fallback routing
- Scientific Smoke V2 and Pilot remain unauthorized until Kaggle execution

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

R6_ACCEPTED_FREEZE_AND_PUBLISH_AUTHORIZED
