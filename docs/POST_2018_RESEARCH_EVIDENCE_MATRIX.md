# Post-2018 Research Evidence Matrix

**Status:** ACCEPTED / FROZEN alongside the 2026-09-04 scientific decision
(`docs/SCIENTIFIC_RESET_DECISION_2026-09-04.md`).

This matrix records the verified evidence that supports the pivot from a
Qwen14B/Kaggle-2×T4 engineering Pilot track to a pre-main Todo
correctness-first micro-study. Every row is traceable to tracked repository
evidence or to the frozen decision pack under `_workspace/active/`. It is an
**evidence matrix**, not a claim of accepted scientific results: the last real
calls in this project produced **no accepted scientific outcome**, and the
matrix says so.

## 1. Reading rule

- **ENGINEERING FEASIBILITY** evidence shows the harness can execute a real
  model end-to-end. It is not scientific correctness evidence.
- **SCIENTIFIC EVIDENCE** requires accepted, frozen scientific runs of the
  study design. As of the freeze date there is **none** for the new Todo
  micro-study (no scientific model call has happened yet).
- Rows are marked E (engineering), S (scientific), or O (operational/decision).

## 2. Verified evidence matrix

| ID | Evidence fact (verified) | Source / verification | Type | What it supports |
|---|---|---|---|---|
| M1 | Real 48-cell Pilot `exp-20260830-134232` finished 48/48 terminal failures, 0 succeeded, 0 evaluator-passed (33 killed at the 600 s workflow deadline). | `reports/V0922_D10_ALL_FAILED_PILOT_VIABILITY_CLOSURE_REPORT.md`; `DECISION_LOG.md` D034 | E | Terminal engineering execution is not a substitute for scientific correctness; the old 48-cell matrix is not a launch basis. |
| M2 | Real 6-cell pilot-canary on 2026-09-02 (from D12 candidate) finished 6 planned / 6 failed / 0 succeeded (~5525 s; 4 deadline-censored, 2 Todo build-in-completion). | `DECISION_LOG.md` D037; `docs/ASSUMPTION_DECISION_EVOLUTION.md` §4b | E | Production-scale execution defects root-caused in D13 (B1 exact patch, B2 agent-control cap, B3 repo-aware migrations, B4 semantic executability). |
| M3 | Real long-context SDPA/GQA 12 044-token prompt probe PASSED (12044/64 prompt/output tokens, no CUDA OOM after the SDPA fix). | `reports/V0922_LONG_CONTEXT_ATTENTION_MEMORY_CLOSURE_REPORT.md`; D029–D030 | E | Memory/single-prefill PASS does NOT imply realistic sustained long-output throughput viability (see lesson A022). |
| M4 | Real 2×T4 preflight PASS (count 08-30): repo preflight overall PASS, GQA microprobe PASS on both GPUs, short probe 17 tokens, generation-deadline canary PASS (4 tokens, `finish_reason=timeout`), long-context PASS. | `reports/V0922_D9_6_REAL_T4_PASS_STABLE_TAG_CLOSURE_REPORT.md`; D033 | E | The Kaggle engineering stack itself was not the only blocker; scientific viability still not established. |
| M5 | Large-repo inference runtime problem persisted even with exact-patch editing (D13B1): complete-file regeneration of a 56k-char djangoCMS file consumed ~1154 s for only 1839 completion tokens. | `DECISION_LOG.md` D037 (D13 B1); tests/unit/execution/test_exact_patch.py | E | Representation fix alone did not solve large-repo inference throughput; correctness-first Todo study removes the large-repo confound. |
| M6 | Todo repository has a real dependency graph with edges; djangoCMS/Saleor strategy-visible graphs were empty or edge-poor (fallback-style construct). | `_workspace/active/05_SUPERVISOR_BRIEF_AR.md`; `_workspace/active/07_CLAUDE_FEEDBACK_INTEGRATION.md` | O | Repository profile != meaningful dependency graph; graph eligibility split (verified-empty vs fallback-empty) is required. |
| M7 | Todo end-to-end path (model generation → exact patch → migration → validation) succeeded in a real canary even while other repos failed. | `_workspace/active/05_SUPERVISOR_BRIEF_AR.md`; D036/D037 evidence | E | The harness is not wholly broken; Todo is a valid pre-main correctness-first venue. |
| M8 | Revision history shows the frozen Qwen14B/T4 track consumed multiple engineering closures (D7–D13R2) without producing an accepted scientific result. | `DECISION_LOG.md` D021–D039; this repo's git log | E | Free GPU / Kaggle time is not the lowest total research cost when the marginal cost of each scientific observation stays high. |
| M9 | temperature=0 was used throughout the Pilot runs; outcomes were still not acceptably reproducible at the study level (48/48 failure, 6/6 canary failure). | `DECISION_LOG.md` D034, D037; `docs/FINAL_RESEARCH_PROTOCOL.md` AC-07 | E | temperature=0 != guaranteed deterministic research outcome; multiple independent repetitions are still required. |
| M10 | `todo-smoke-001/002/003` are pre-existing Todo scenarios with independent evaluator assets, one per blast-radius class (localized/moderate/cross_cutting). | `benchmark_data/` scenario + `tests/evaluator_assets/todo_smoke_00*_checks.py`; `_workspace/active/02_TODO_SCENARIO_PREREGISTRATION.md` | O | Frozen scenario IDs are selection-rationale backed (not outcome-selected). |
| M11 | Model/provider operational gate preregistered with numeric eligibility thresholds before any scientific call. | `_workspace/active/01_MODEL_PROVIDER_ACCEPTANCE_GATE.md`; `docs/PREMAIN_FEASIBILITY_PREREGISTRATION.md` §2 | O | Model/provider must be operationally accepted and frozen before scientific results. |
| M12 | Empty-graph semantics split (verified-empty != fallback-empty) accepted in the audit. | `_workspace/active/07_CLAUDE_FEEDBACK_INTEGRATION.md` (amendment); preregistration §5 | O | Correct graph-eligibility for the dependency-aware treatment claim. |
| M13 | No scientific model call has been made under the frozen preregistration; zero real model calls occurred during this decision-freeze task. | This task (documentation-only); freeze commit | S | Thresholds were frozen before outcomes (anti-cherry-picking). |
| M14 | No accepted scientific result exists yet for the new path; efficiency reporting restricted to descriptive stats among qualified runs (n=5). | `_workspace/active/03_MICROSTUDY_GO_NOGO_RULES.md`; `docs/PREMAIN_FEASIBILITY_PREREGISTRATION.md` §4 | S | No significance claim from n=5; the first scientific results table is the next deliverable. |

## 3. What this matrix deliberately does NOT claim

- It does NOT claim the Qwen14B/T4 track "failed science" — it contributed
  engineering feasibility evidence (E rows) only.
- It does NOT claim DeepSeek or Qwen32B will win the gate.
- It does NOT claim Todo GO is likely.
- It does NOT outrank `docs/PREMAIN_FEASIBILITY_PREREGISTRATION.md` or the
  decision log. It is supporting evidence, not an additional decision source.