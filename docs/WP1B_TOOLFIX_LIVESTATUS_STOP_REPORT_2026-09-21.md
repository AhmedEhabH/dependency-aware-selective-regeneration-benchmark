# WP-1b Tool-Fix + Live-Status — STOP Report (2026-09-21)

**Mission:** `WP1B_TOOLFIX_LIVESTATUS_2026-09-21` (T3).
**Authorized:** D1 `GATE_V1_PASS / INSTRUMENT_INVALID`; D2 tool-budget amendment
APPROVED; D3 gate v2 APPROVED; D4 = YES (Calibration-3b, ceiling $0.25);
D5/D7 = NO (MAIN_297 + variance substudy NOT authorized); D6 = YES
(LIVE_STATUS single source of truth). Supervisor informed: **no**.
**Branches:** `wp1b/toolfix-livestatus-2026-09-21` (merged to `main` `f6c858b`,
tag `wp1b-toolfix-2026-09-21`) → `wp1b/calibration-3b-2026-09-21` (Phase C).

## 1. Executive decision

```
DECISION: CALIBRATION_3B_DONE(CG-1..CG-11 PASS)
```

Calibration-3b — the paired instrument revalidation of the D2 tool-budget fix on
the SAME 3 calibration tasks, protocol v2 (cap 1024), frozen
`qwen/qwen3-coder @ deepinfra/turbo` (temp 0.0), not scored — **PASSES gate v2
(CG-1..CG-11)**. Cumulative cost **$0.070028 ≤ $0.25**. Per-task cost /
budget-v2 worst-case ratios **0.405 / 0.626 / 0.547** — all within 1.2×
(BUDGET_MODEL_V2_OK). **STOP after Phase C** (contract §6 step 7). MAIN_297 and
the variance substudy remain **NOT authorized** (D5/D7 NO) until Ahmed issues a
separate explicit decision after reviewing this evidence.

## 2. What changed (Phases 0–B, ZERO API)

- **D1 reclassification:** Calibration-3 preserved historically and reclassified
  prospectively as **`GATE_V1_PASS / INSTRUMENT_INVALID`**. Its STOP report and
  frozen artifacts are NOT rewritten.
- **D2 fix (`WP1B_G11_TOOL_BUDGET_2026_09_21`):** `search_text` no longer
  consumes the distinct-file budget; `read_file` keeps `MAX_DISTINCT_FILES =
  30`. Only diff in agent behaviour is D2 (AC-T6).
- **Gate v2 (D3):** `artifacts/wp1b_calibration_gate_v2.json` (CG-1..CG-11),
  evaluator `scripts/wp1b_calibration_gate.py --gate v2`. On the old
  Calibration-3 records: **CG-10 FAIL (9 instrument errors), CG-11 FAIL** —
  the RED evidence (AC-T4).
- **A4 telemetry:** per-call `tool_ok`/`tool_error`/`tool_duration_seconds` +
  report-only search telemetry (`search_files_scanned`, `search_results_returned`,
  `search_result_cap_hit`); per-task `successful_reads`, `search_calls_with_hits`,
  `tool_error_counts`, `rejected_repeat_count`, `unique_paths_surfaced`;
  `paths_read` success-only; `paths_surfaced` paths-only (AC-T5).
- **LIVE_STATUS (D6):** `docs/LIVE_STATUS.json` is the single current-state
  source of truth; `scripts/render_live_status.py` renders the block into FOUR
  current-facing files (README, START_HERE_CURRENT_2026-09-21b, PROGRESS,
  00_CURRENT_RESEARCH_STATE); `tests/unit/test_live_status_blocks.py` enforces
  byte-for-byte sync (AC-T7/T8).
- **README current-state rewrite** (B2): RM-CSS / Saleor-300 / Phase-5 current
  state; Route-B-era rows moved under "Earlier milestones (history)"; model
  identity line + SVG fallbacks; WP-2 / E2E-G6 / no-E2E-run stated explicitly
  (AC-T9/T10). **GLOSSARY namespaces** WP1B-G*/E2E-G* + G6 collision (AC-T11);
  **AGENTS.md** end-of-mission rule (AC-T12).

## 3. Verification (Phases 0–B)

- **AC-T1** sidecar audit reproduces 3 final / 5 tool-ok / 9 limit errors /
  7 rejected repeats / 0 successful reads exactly
  (`scripts/wp1b_sidecar_tool_audit.py` → `wp1b_tool_audit.json`).
- **AC-T2** v1.1 check re-derived: 0 `Max distinct files limit`; max
  `selection_inspected_file_count` = 4 (distribution {0:15, 2:3, 3:7, 4:5}).
- **AC-T3** A2 test 1 was RED before the fix (search hit the 30-file limit) and
  is GREEN after.
- **AC-T9** both README tests pass; **full suite 3 failed / 3730 passed / 34
  skipped** — failing node IDs == `artifacts/known_test_failures_2026-09-21_v2.json`
  (the two README node IDs fixed and removed).
- **AC-T13** spend in Phases 0–B = **$0.00**; targeted suite green;
  `git status --porcelain` clean.
- **AC-T14** ruff, mypy strict, `git diff --check`, `py_compile` PASS on all
  changed files.

## 4. Phase C — Calibration-3b (paid; D4 = YES)

**Run:** same 3 tasks in `research/wp1a/wp1_calibration_3_manifest.json`,
protocol v2 (cap 1024), frozen `qwen/qwen3-coder @ deepinfra/turbo` (temp
0.0), USD guard ≤ $0.25, NOT scored against labels. Records under
`research/wp1b/calibration-3b-2026-09-21/`.

### 4.1 Gate v2 evaluation (CG-1..CG-11)

| Check | Result |
|-------|--------|
| CG-1 | PASS — 3/3 records, complete protocol metadata |
| CG-2 | PASS — protocol fields match frozen values (model/route/temp/cap/MAX_AGENT_CALLS) |
| CG-3 | PASS — 3/3 telemetry classified (all valid finals) |
| CG-4 | PASS — 0 silent parser failures |
| CG-5 | PASS — 0 unclassified EMPTY |
| CG-6 | PASS — no route/model drift |
| CG-7 | PASS — 0 scientific-knob drift |
| CG-8 | PASS — token accounting identity |
| CG-9 | PASS — $0.070028 ≤ $0.25 |
| **CG-10** | **PASS — 0 instrument-class tool errors** |
| **CG-11** | **PASS — 3 successful read_file (tasks 1 and 3)** |

**GATE PASS (CG-1..CG-11) = true. INSTRUMENT VALID = true.**

### 4.2 Per-task report (CG-1..CG-11 + report-only; §6 / instruction 11)

| Metric | task 1 (349d46d906ad) | task 2 (b05633dae118) | task 3 (d52a55471bfc) |
|---|---|---|---|
| LLM calls | 5 | 8 | 8 |
| Successful read_file | 2 | 0 | 1 |
| Search calls with hits | 1 | 1 | 2 |
| Instrument errors | 0 | 0 | 0 |
| Agent-misuse errors | 0 | 0 | 0 |
| Frozen-policy-limit events | 0 | 0 | 0 |
| Rejected repeated requests | 1 | 6 | 4 |
| Search files scanned | 1,099 | 1,029 | 1,106 |
| Search results returned | 2 | 7 | 11 |
| Search-result cap hits (50) | 0 | 0 | 0 |
| Unique surfaced paths | 1 | 4 | 5 |
| Observation truncation rate | 0.000 | 0.000 | 0.453 |
| Finish-reason distribution | stop:5 | stop:8 | stop:8 |
| Prompt tokens | 71,230 | 104,881 | 54,315 |
| Completion tokens | 174 | 421 | 305 |
| Total tokens | 71,404 | 105,302 | 54,620 |
| Actual USD | 0.021543 | 0.031885 | 0.016599 |
| Worst-case USD (budget v2) | 0.053253 | 0.050923 | 0.030339 |
| **Actual/worst-case ratio** | **0.405** | **0.626** | **0.547** |

Aggregate: 21 calls, $0.070028, 3 successful reads, 0 instrument errors,
11 rejected repeats, 0 search-result cap hits, 0 frozen-policy-limit events.

**GATE PASS vs INSTRUMENT VALID:** the gate PASS is the frozen check-set
result (CG-1..CG-11). The INSTRUMENT VALID conclusion is the raw per-call
evidence: 0 instrument-class errors and 3 successful reads from
`wp1b_call_sidecar.jsonl` / `wp1b_tool_audit.json` — the agent's tools return
information again after the D2 fix.

### 4.3 Stop conditions — NONE triggered

- CG-10 / CG-11: **PASS** (no stop).
- Cost ratio > 1.2 on any task: **no** (max 0.626) — no `BUDGET_MODEL_V2_WRONG`.
- New instrument-class error: **none**.
- Scientific configuration drift: **none** (CG-2/CG-6/CG-7 PASS; model,
  provider/route, cap 1024 match the frozen protocol).
- Behavior-changing fix required to complete: **no**.

### 4.4 Limitations

- **Search-result-cap saturation: NONE** — 0 cap hits; the alphabetical
  first-50 result policy did NOT saturate on these 3 Saleor tasks
  (max 11 results returned, 1,106 files scanned per task). The 50-cap and the
  alphabetical order were NOT changed (instruction 12); any such change would
  require a separate prospective protocol decision before MAIN_297.
- **Task 2 agent repetition:** 6 rejected repeated requests (the agent
  persisted on the same search query). This is AGENT behavior, not an
  instrument defect (the search returned real data; 0 instrument errors), and
  is reported, not gating.
- **Observation truncation (task 3):** 0.453 — a read_file of a 4,512-char file
  was shown in the frozen 2,000-char window. Expected frozen behavior.

## 5. Not scored against labels

Calibration-3b is a paired instrument revalidation, NOT a fresh independent
performance sample (instruction 5). No labels were loaded or scored; no prompt
or Agent behavior was tuned from prior trajectories; no F1/performance claim is
made from Calibration-3 or Calibration-3b.

## 6. Sealed outcomes

The 786 unread Saleor RESERVE outcomes remain sealed — never opened, read,
scored, sampled, or hash-inspected for outcomes (instruction 13).

## 7. Independent self-audit

- **Objective unchanged:** D2 tool-budget fix + gate v2 + LIVE_STATUS +
  Calibration-3b (D4 YES), STOP after Phase C. No scope creep.
- **Plan adherence:** Phases 0/A/B zero-API; RED→GREEN preserved; smallest
  defensible diff (only D2 in agent behaviour); targeted tests first; one
  full-suite run at the final gate.
- **Over-engineering:** none — no knob beyond D2 changed; telemetry is
  report-only; gate v2 reuses the audit classification.
- **Debt:** none introduced. The `kaggle_upload/` pinned bundle is unchanged
  (it is a historical pinned deployment artifact, not the WP-1b source path).
- **Durability:** all evidence is committed and pushed (3b branch), tag pushed
  and verified, tree clean.
- **Tag state:** `wp1b-toolfix-2026-09-21` created on merge commit `f6c858b`
  (local + remote tag objects match; peel = `f6c858b` = origin/main).
- **MAIN (local = origin):** `f6c858b`.

## 8. Final response

```
DECISION: CALIBRATION_3B_DONE(CG-1..CG-11 PASS)
VERIFIED: 3/5/9/7 + 0 reads (AC-T1); v1.1 max inspected 4 (AC-T2);
  A2 test 1 RED→GREEN (AC-T3); gate v2 on old Calibration-3 CG-10 FAIL (AC-T4);
  golden test identical (AC-T5); only D2 in repository_tools diff (AC-T6);
  LIVE_STATUS keys preserved (AC-T7); sync test 4/4 (AC-T8); full suite
  3 failed = known v2 list (AC-T9); no assistant name, full model name (AC-T10);
  GLOSSARY namespaces + G6 collision (AC-T11); AGENTS.md rule (AC-T12);
  spend 0-B = $0.00, tree clean (AC-T13); ruff/mypy/diff-check (AC-T14)
CALIBRATION-3b: 21 calls; reads/task 2/0/1; search hit rate 4/4 calls with hits;
  rejected repeats 11 (1/6/4); cost $0.070028; ratios 0.405/0.626/0.547
BLOCKERS: none
CHANGED: commits b084151..f6c858b (merged to main); tag wp1b-toolfix-2026-09-21;
  branch wp1b/calibration-3b-2026-09-21 (Phase C records); pushed
API SPEND: $0.070028 (Phase C only; Phases 0-B $0.00)
MAIN: local f6c858b | origin f6c858b
LIVE_STATUS: position_short = "Calibration-3b PASS (gate v2); agent instrument-valid; MAIN_297 awaits D7" ;
  next_short = "Ahmed reviews 3b → D7 for MAIN_297"
NEXT PERMITTED ACTION: Ahmed reviews Calibration-3b evidence and issues a
  separate explicit D7-style authorization for MAIN_297. No further paid run
  in this mission.
```

## 9. Files

- Defect: `docs/WP1B_AGENT_TOOL_BUDGET_DEFECT_2026-09-21.md`
- Gate v2 artifact: `artifacts/wp1b_calibration_gate_v2.json`
- Gate v2 (RED): `research/wp1b/calibration-3-2026-09-21/wp1b_calibration_gate_v2_result.json`
- Gate v2 (GREEN): `research/wp1b/calibration-3b-2026-09-21/wp1b_calibration_gate_v2_result.json`
- Audits: `research/wp1b/calibration-3-2026-09-21/wp1b_tool_audit.json`,
  `research/wp1b/calibration-3b-2026-09-21/wp1b_tool_audit.json`
- Live status: `docs/LIVE_STATUS.json`, `scripts/render_live_status.py`,
  `tests/unit/test_live_status_blocks.py`
- Decisions: `DECISIONS.md` (D1..D6, WP1B_CALIBRATION_3_RECLASSIFIED,
  known-test-failures v2)