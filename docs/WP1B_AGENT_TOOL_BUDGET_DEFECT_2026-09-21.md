# WP-1b Agent Tool-Budget Defect — 2026-09-21

**Mission:** `WP1B_TOOLFIX_LIVESTATUS_2026-09-21` (T3). **Branch:**
`wp1b/toolfix-livestatus-2026-09-21`.
**Classification (D1):** `GATE_V1_PASS / INSTRUMENT_INVALID`. The frozen
Calibration-3 gate (CG-1..CG-9) passed, but the agent's tools were defective:
0 of 3 tasks successfully read a file, and most searches returned the frozen
30-file-limit error.

## 1. Evidence (re-derived mechanically, not copied from prose)

Re-derived by `scripts/wp1b_sidecar_tool_audit.py` from
`research/wp1b/calibration-3-2026-09-21/wp1b_call_sidecar.jsonl`; machine
artifact: `research/wp1b/calibration-3-2026-09-21/wp1b_tool_audit.json`.

| Outcome of the 24 agent calls | Count |
|---|---|
| Final answers (call 8, forced) | 3 |
| Tool calls that returned data (3 `list_files`, 2 `search_text`) | 5 |
| Tool calls that returned the 37-char error `Max distinct files limit (30) reached` (7 `search_text`, 2 `read_file`) | 9 |
| Calls rejected as a repeated identical tool request | 7 |
| **Successful `read_file` calls** | **0** |

Per-task (from the audit):

| Task | final | tool_ok | tool_error | rejected_repeat | successful_reads |
|---|---|---|---|---|---|
| saleor-rc-349d46d906ad | 1 | 2 | 1 | 4 | 0 |
| saleor-rc-b05633dae118 | 1 | 1 | 4 | 2 | 0 |
| saleor-rc-d52a55471bfc | 1 | 2 | 4 | 1 | 0 |

The sidecar's `tool_output_chars_raw == 37` exactly matches the frozen error
string `Max distinct files limit (30) reached` (37 characters), produced by
`RepositoryTools._reserve_inspected_file()`.

## 2. Code path (file and line numbers)

- `src/benchmark/strategies/repository_tools.py`:
  - `search_text()` (line 144) calls `self._reserve_inspected_file(resolved_entry)`
    (line 167) for **every scanned file**. `_reserve_inspected_file()` (line 78)
    increments `self._inspected` and returns the error string
    `Max distinct files limit ({max}) reached` (line 85) once
    `len(self._inspected) >= self._max_distinct_files`.
  - `read_file()` (line 122) also calls `_reserve_inspected_file()` (line 133),
    so it is bound by the same budget.
- `src/benchmark/strategies/iterative_agent.py`: `begin_run()` (line 284)
  constructs `RepositoryTools(workspace_root=root, max_distinct_files=30)`
  (line 317–320).

Because the workspace is the materialized `saleor/` tree, the first
`search_text` over it reserves the whole 30-file budget. Every later
`read_file`, and every search that needs a 31st file, fails with the frozen
error. The agent then repeats the same request, and the repeats are rejected
by `_is_repeated_tool_request()` (line 440). The final answers therefore came
from the editable-path list and at most one search result — the agent arm was
blind in all 3 tasks.

## 3. Classification and why it is not outcome-driven

The classification `GATE_V1_PASS / INSTRUMENT_INVALID` is a **prospective
instrument correction**, not an outcome-driven change:

- No calibration label was loaded or scored (Calibration-3 is an
  instrumentation / protocol sanity check; see
  `artifacts/wp1b_calibration_gate.json`).
- The fix (amendment `WP1B_G11_TOOL_BUDGET_2026_09_21`, D2) restores tool
  function (`search_text` no longer consumes the distinct-file budget) without
  touching any decision logic: prompts, schemas, `MAX_AGENT_CALLS`,
  temperature, the 2,000-char observation window, `MAX_READ_CHARS`,
  `MAX_SEARCH_RESULTS`, `MAX_LIST_ENTRIES`, search order, the repeated-request
  rule and the 1,024-token cap are unchanged.
- `read_file` keeps `MAX_DISTINCT_FILES = 30`.

## 4. v1.1 microstudy check (re-derived)

The external review stated that the v1.1 microstudy
(`reports/scientific_microstudy_v11/run_records.jsonl`) contains **0**
occurrences of `Max distinct files limit` and that `inspected_file_count` was
never above 4 (distribution 0:15, 2:3, 3:7, 4:5 over 30 runs). Re-derived
from the 30 run records:

- Records containing `Max distinct files limit`: **0**.
- `selection_inspected_file_count` distribution over 30 runs: **{0: 15, 2: 3,
  3: 7, 4: 5}**, max **4**.

On the small Todo repository the 30-file budget never bound, so D2 restores on
Saleor the behaviour the v1.1 agent actually had.

## 5. Consumers of the affected state (grep)

`grep -rn "inspected_files\|distinct_file_count" src/`:

- `src/benchmark/strategies/repository_tools.py` — `inspected_files` property,
  `distinct_file_count` property (source of truth for the budget). D2 changes
  `search_text` so it no longer increments these; `read_file` still does.
- `src/benchmark/strategies/iterative_agent.py` — `_inspected_files`,
  `inspected_file_count` property (line 1008). This is a STRATEGY-side counter
  of distinct `read_file` TARGETS requested by the agent (line 499), NOT the
  tool-side budget. D2 does not touch it.
- `src/benchmark/execution/runner.py` line 1395 — `agent_inspected_files` from
  `strategy.inspected_file_count` (read-file targets; unchanged by D2).

None of these consumers feed scientific accounting THROUGH the search path.
The strategy-side `inspected_file_count` feeds `selection_inspected_file_count`
in run records (scientific accounting, e.g. the v1.1 microstudy
distribution), but that counter counts `read_file` targets and is untouched by
D2: only the tool-side `RepositoryTools` budget consumption by `search_text`
is removed. The WP-1b telemetry field `paths_read` (A4) is separate and is
corrected to record only SUCCESSFUL reads.

## 6. Budget note (A6)

The budget-v2 worst case already assumes 2,000-char tool outputs, so it stays
valid. The Calibration-3 observed cost / worst-case ratios were 0.52–0.64
**only because the tools returned tiny error strings** (37 chars) instead of
real search results. With the D2 fix, observed cost per task will rise toward
the worst case. The ≤ 1.2× rule still applies in Phase C
(`BUDGET_MODEL_V2_WRONG` stop).

## 7. Pointer

Decision record: `DECISIONS.md`
(`WP1B_CALIBRATION_3_RECLASSIFIED — GATE_V1_PASS / INSTRUMENT_INVALID`).
Historical STOP report (unchanged): `docs/WP1B_CALIBRATION_3_STOP_REPORT_2026-09-21.md`.
Gate v2: `artifacts/wp1b_calibration_gate_v2.json`,
`scripts/wp1b_calibration_gate.py --gate v2`.