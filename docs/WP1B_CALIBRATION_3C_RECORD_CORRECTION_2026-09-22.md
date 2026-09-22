# WP-1b Calibration-3c — record correction (append-only, zero API)

**Date:** 2026-09-22 · **Scope:** wording of the Calibration-3c record only. The
CLEAN verdict, the gate result and every number in the gate artifacts are
unchanged. Source of truth: `research/wp1b/calibration-3c-2026-09-22/wp1b_call_sidecar.jsonl`.

| Record | Original wording | Correct statement (from the sidecar) |
|---|---|---|
| `docs/WP1B_CALIBRATION_3C_STOP_REPORT_2026-09-22.md`; LIVE_STATUS `calibration_3.finding` | "task 2 used 7 distinct searches" | Task `b05633dae118` made 7 search calls, **6 distinct**: call 6 repeats call 2 exactly (`"external shipping method currency"`). Calls 3 and 5 differ by one letter and returned the same 7 matches. The frozen rejection rule rejects only CONSECUTIVE identical requests, so a non-adjacent repeat is executed. |
| same | task 2 "decided search snippets were enough" (interpretation used in review) | Task 2 did **not** stop voluntarily: call 7 still set `requires_iteration: true`, and call 8 was the **forced final** (`force_final: true`). The 8-call budget was binding on 1 of 3 tasks. |
| same | "3 multi-word searches" (not recorded) | 3 of task 2's search calls returned 0 results; all were multi-word queries. `search_text` is a case-insensitive SUBSTRING match of the whole query, so multi-word queries rarely match. |
| same | "useful tool calls 14" | 14 executed tool calls; 2 of them repeat an earlier non-adjacent request (task 2 call 6; task 3 call 5), so **12** carried new information. |

**Why this matters:** none of it changes the CLEAN verdict (CG-12 concerns
consecutive rejected repeats). It matters for interpretation: it shows the agent
is budget-bounded and that its search tool is weak for multi-word queries. Both
facts are now (a) disclosed in the README lessons (1c), (b) measured on MAIN_297 by
the label-free X11 tool-quality descriptive, and (c) addressed by the
preregistered budget-sensitivity arm (`research/wp1b/wp1b_agent_budget_sensitivity_prereg.json`).
No agent change follows from this note (one-amendment rule closed).
