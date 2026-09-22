# WP-1b Agent Context Loop — 2026-09-22

**Amendment:** `WP1B_G12_AGENT_CONTEXT_HYGIENE_2026_09_22` (D1 = APPROVED).
**Scope:** zero-API scaffold change to the repository agent's selection loop.
**Related:** Calibration-3 / Calibration-3b / Calibration-3c (not scored).

## Evidence

Calibration-3b passed gate v2: the tools now work (3 successful reads, 0
instrument errors). The raw calls expose a **second harness problem** — a
deterministic context loop. Source:
`research/wp1b/calibration-3b-2026-09-21/wp1b_call_sidecar.jsonl`, audited by
`scripts/wp1b_loop_audit.py` (reproduces the table below).

| Task | Calls | Useful tool calls | Rejected repeats | Longest run of consecutive rejections |
|---|---|---|---|---|
| 349d46d906ad | 5 | 3 | 1 | 1 |
| b05633dae118 | 8 | 1 | 6 | 6 |
| d52a55471bfc | 8 | 3 | 4 | 4 |
| **Total** | **21** | **7** | **11** | — |

- **$0.036727** of the **$0.070028** (52%) was spent on rejected repeats
  (`wp1b_loop_audit.json` aggregate.rejected_spend_usd).
- The prompt grows by **exactly 18 tokens per rejected call**. The only thing
  appended is the fixed sentence
  `Repeated identical tool request rejected; use new evidence or submit final.`
  (uniform `rejected_prompt_growth_tokens == 18` across both repeating tasks).
- The transcript appends `[result] <tool name>:` and the output, but **never
  the agent's own request** (query or path). There is **no call counter**
  before call 8.
- A truncated read (`dataloaders.py`, 4,512 chars, 2,000 shown) is **not
  marked as truncated**. Task 3 then asked for the same file 4 more times.

**Result:** at temperature 0, an almost identical prompt produces the same
reply. That is a **deterministic loop created by the harness**, not a strategy
choice by the model.

## Why fixing it is not tuning

1. **It is label-blind.** No calibration task has been scored; Calibration-3c
   is unscored too.
2. **It strengthens the competitor**, which is the conservative direction for
   our non-inferiority claim (the agent is the paid arm compared against
   SIP / RM-CSS).
3. **It restores information the harness already has and withholds**: the
   agent's own actions, the call count, and a truncation flag. This is the
   standard ReAct action → observation format.
4. **It is bounded**: exactly one amendment, preregistered, and no further
   scaffold change whatever Calibration-3c shows (D5).

## G12 (the four changes, selection loop only)

1. **Action echo** prepended to every tool result:
   `[call {k}/8] you requested: {action} path="{path}" query="{query}"`
   (empty fields omitted).
2. **Call counter** appended before every non-final call:
   `[control] Call {k} of 8. Calls left before the forced final: {8-k}.`
   Early `action=final` availability is ALREADY visible to the model in the
   frozen schema (`TOOL_SCHEMA` item 4, `AGENT_ACTION_SCHEMA` enum, and the
   reserved-call-8 note in `INITIAL_SYSTEM_PROMPT`), so per Ahmed's
   clarification it is NOT repeated in the counter message.
3. **Named rejection**:
   `[control warning] Rejected: identical to your previous request ({action}
   path="{path}" query="{query}"). Its result is shown above. Choose a
   different action or return action=final.`
   The rejection rule itself does not change.
4. **Truncation note** appended when the tool output exceeds 2,000 chars:
   `[note] Output truncated: showing the first 2000 of {N} characters.
   Re-reading the same path returns the same text.`

## D5 — one-amendment rule

No scaffold or agent change after D1, whatever Calibration-3c or MAIN_297
shows. A CG-12 failure in Calibration-3c is **reported, not fixed**.