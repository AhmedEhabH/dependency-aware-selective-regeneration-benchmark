# STOP REPORT — djangoCMS External-Validity RUNTIME WIRING CLOSURE + COST PROBE-02

**Date (local):** 2026-09-08
**PROBE_ID:** `scientific-stagec-djangocms-costprobe-02`
**Type:** NON-STUDY COST PROBE (NOT part of the scientific 60-run result set; MUST NOT be reused as study results).

---

## 1. Execution Identity

- Provider/model: `openrouter:qwen/qwen3-coder@deepinfra/turbo` (DeepInfra pinned through OpenRouter, fallback OFF, temperature 0)
- Branch: `research/djangocms-external-validity-prep-01`
- HEAD: `39f7b3bad558fb4752b935b64fcbcc7a353f0d83`
- origin/main: `5d8029b26154d215daa8ca4d3ac8325bf79641cc` (research branch not merged into main; expected)
- Tree state at stop: wiring commit `39f7b3b` clean; probe evidence + modified driver staged in a follow-up commit (tag NOT moved)
- Wiring tag: `stagec-djangocms-study-wiring-verified-01` → peel `39f7b3b…` (created + pushed; does NOT modify `stagec-djangocms-prep-verified-01` → peel `a0ac7dc6…`)

## 2. Why I Am Stopping

**COMPLETE** — the runtime wiring closure is finished, the six deterministic gates + independent audit PASS, the wiring tag was created, and the two cost-probe runs (costprobe-02) SUCCEEDED with COST_LOCK=PASS. Per the task, the final 60-run study is **NOT** started. The failed `scientific-stagec-djangocms-costprobe-01` remains DIAGNOSTIC ONLY (never counted as a study result, never used for COST_LOCK).

## 3. What I Completed

| File | Symbol | Old | New | Why |
| --- | --- | --- | --- | --- |
| `src/benchmark/external_validity/study_runtime.py` | NEW module | — | study-specific runtime wiring | Universe derived directly from `djangocms_5_0_0_candidate_universe.json` (144), probe scenario loaded only from `visible_drafts/`, hidden gold only from `djangocms_hidden_gold_draft.json`; implements RUNTIME_WIRING_PREFLIGHT + the six deterministic gates + independent audit |
| `scripts/stagec_djangocms_runtime_wiring_closure.py` | NEW driver | — | preflight/gates/audit/probes subcommands | Deterministic gate runner + cost-probe executor (selection-only, exact costprobe-02 config) |
| `tests/integration/test_stagec_djangocms_runtime_wiring.py` | NEW tests | — | 12 wiring-contract tests | Deterministic regression coverage for the wiring contract |
| `reports/scientific-stagec-djangocms-costprobe-02/*` | NEW evidence | — | preflight/gates/audit/probe JSONs | Persisted ledger evidence |
| `reports/scientific-stagec-djangocms-costprobe-01/*` | carried evidence | — | diagnostic probe-01 ledger truth | Persisted diagnostic-only evidence (9 calls, $0.008706, 0 valid study runs) |

Dependencies: none (no scientific input, AST graph, hidden gold, visible scenario semantics, executor/regeneration/repair, Todo or Saleor modified).

## 4. Verification Performed

- Compile (`py_compile`): PASS (3 changed files)
- Ruff: PASS (0 errors, changed files)
- Mypy (changed production files): PASS for both new files; `source_graph.py:180` is a PRE-EXISTING error on the base commit (frozen prep module, out of scope)
- Integration tests: `tests/integration/test_stagec_djangocms_runtime_wiring.py` **12 passed**
- Full suite: NOT run (shared interfaces unchanged; per working rule full Pytest only at final gate — this closure is scope-bounded runtime wiring)

## 5. Pre-Benchmark Validation (the EXACT six gates + Audit)

All deterministic, zero scientific calls:

1. **Dataset Validation — PASS** (exactly 6 hidden-gold records, exactly 6 final scenario IDs, runtime universe == frozen 144-path universe, every hidden-gold path ∈ runtime universe)
2. **Prompt Validation — PASS** (scenario_id == `djangocms-external-validity-008`, source is the final visible draft, old `djangocms-cross-008` not loaded, no `.py`/exact-path/module-hint leaks, no hidden-gold leakage)
3. **Pipeline Smoke Test — PASS** (mock backend only, zero scientific calls, selection-only, final scenario, 144-path universe)
4. **Dry Run — PASS** (exact costprobe-02 configuration, both arms, zero scientific calls)
5. **Integration Test — PASS** (both Agent and ImpactPlan receive the SAME visible requirement and the SAME exact 144-path selectable universe; neither receives hidden gold; pinned djangoCMS source available)
6. **Metric Verification — PASS** (scoring uses `djangocms_hidden_gold_draft.json`, never historical `expected_actions` / old historical scenario gold; precision/recall/F1/FNR/full-recall support the six final IDs)

Independent Audit: **PASS** (11/11 OK — no scientific input modified, hidden gold evaluation-only, old historical scenario not model-facing, zero scientific calls in gates).

Evidence: `reports/scientific-stagec-djangocms-costprobe-02/runtwiring_preflight.json`, `runtwiring_gates.json`, `runtwiring_audit.json`.

## 6. Independent Self-Audit

- Objective unchanged: runtime wiring closure only; no scientific input touched
- Plan adherence: preflight → six gates → audit → commit+push → wiring tag → probes → STOP (followed exactly)
- Over-engineering: none (scoped wiring module + driver + tests)
- Debt: pre-existing `source_graph.py:180` mypy error documented, not fixed (frozen prep module)
- Durability: all evidence persisted to `reports/scientific-stagec-djangocms-costprobe-02/`
- Freshness: evidence generated this session
- Tag state: `stagec-djangocms-study-wiring-verified-01` created + pushed @ `39f7b3b`; `stagec-djangocms-prep-verified-01` untouched

## 7. Exact Current State

- Costprobe-02 both probe runs SUCCEEDED (valid terminal selection output, all selected paths valid members of the 144-path universe):

| Arm | Calls | Prompt tok | Completion tok | Total tok | Tool calls | Latency (s) | API cost (USD) | Regenerate paths | Success |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| iterative_repository_agent | 8 | 15,922 | 358 | 16,280 | 4 | 131.594 | 0.005135 | 10 (all valid) | TRUE |
| impact_plan | 1 | 3,476 | 1,817 | 5,293 | 0 | 67.250 | 0.002860 | 6 (all valid) | TRUE |

- Scenario: `djangocms-external-validity-008` @ `benchmark_data/external_validity/visible_drafts/` (sha256 `d2076d5bf092ac8a96566c88f413deb1090ab61ebe85733a41174e8aac283021`)
- Universe: 144 paths, canonical hash `43f4279bdf228745b1f6b289c81cda141b089ab5be4f4af63bb8f39f837c4410`
- Model/provider: `qwen/qwen3-coder` @ `deepinfra/turbo`, fallback OFF, temperature 0.0
- Caps: Agent 1024 / ImpactPlan 4096; selection-only; 2 scientific calls total
- Both arms: finish_reason=stop, no truncation, no validity errors, `invalid_selected_paths=[]`
- `raw_projected_60_cost = 30*agent + 30*impact = 30*0.005135 + 30*0.002860 = $0.239850`
- `conservative_projected_60_cost = 0.239850 * 1.25 = $0.299813`
- **`COST_LOCK=PASS`** ($0.299813 ≤ $0.50)

## 8. What Remains

- The final 60-run study is **NOT authorized to run from this STOP** — the next REAL launch requires a fresh exact candidate + its own pilot-canary/tag decision (per repo release rules). Do NOT resume costprobe-01 (DIAGNOSTIC ONLY). `exp-20260828-151335` and `exp-20260830-134232` remain non-resumable/rejected.

## 9. What I Need From User

`Nothing — I can continue automatically.` (evidence persisted; Stop Report + evidence ZIP + project export ZIP created; evidence commit pushed.)

## 10. Recommended Next Action

Review `reports/scientific-stagec-djangocms-costprobe-02/STOP_REPORT.md` + `cost_probe_report.json`, then decide whether to authorize the full 60-run study from a fresh exact candidate with its own pilot-canary pass and tag decision.

---

### Ledger truth (carried)
- Diagnostic probe-01 (FAILED, DIAGNOSTIC ONLY): 9 model calls spent, spend ≈ $0.008706, valid scientific study runs = 0
- Costprobe-02 (this closure): 2 successful probe runs, spend = $0.005135 + $0.002860 = $0.007995; COST_LOCK=PASS