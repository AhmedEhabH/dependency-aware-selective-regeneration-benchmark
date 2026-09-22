# Mission Template (WP-1b line)

Skeleton for WP-1b mission contracts. Future contracts state only the deltas
against this template. Keep the standing rules (AGENTS.md, preflight contract,
append-only `DECISIONS.md`) in force unless a delta says otherwise.

## Why

- What problem the previous stage exposed (evidence file + one table).
- Why this fix is NOT tuning (label-blind / strengthens the competitor /
  restores information the harness already has / bounded).

## §0 Decision block (copied verbatim into `DECISIONS.md`)

> | ID | Decision | Value |
> |----|----------|-------|
> | D1 | <amendment name + scope> | **APPROVED** / REJECTED |
> | D2 | <next calibration run + ceiling> | **YES** / NO |
> | D3 | <main run + variance + scoring> | **MANUAL = stop after calibration** / AUTO_IF_CLEAN / YES |
> | D4 | Ceilings | per-stage ceilings, unchanged unless a delta |
> | D5 | One-amendment rule | **APPROVED** / superseded |
> | — | Decided by | <name>, <date>. Supervisor informed: yes / no |

Stop and report `DECISION_BLOCK_INCOMPLETE` if any field still reads
`[CHOOSE]`.

## §1 FROZEN — must not change

Model and route; temperature 0; `MAX_AGENT_CALLS`; completion cap; the
`INITIAL_SYSTEM_PROMPT` text; the tool set and arguments; the observation
window; `MAX_READ_CHARS`; `MAX_SEARCH_RESULTS`; search order; the read budget;
the editable-path list; JSON schemas; the rejection rule; predictions; NI
rules; manifests; budget ceilings.

## §2 Phase A — zero API

- A1 — Record (audit script + evidence doc).
- A2 — RED tests (stub backend). Record the RED output.
- A3 — Implement exactly N changes (name the file and loop). Tests turn GREEN.
- A4 — Gate vX artifact + gate evaluator; RED proof on the previous run.
- A5 — Review card (standing tool) on the affected runs; AGENTS.md line.
- A6 — Mission template delta (only if the skeleton itself changed).
- A7 — Integrate: ACs, merge `--no-ff` to `main`, tag, push, LIVE_STATUS.

## §3 Phase B — calibration (paid, ceiling)

- Same tasks as the paired regression, protocol vX, gate vX, NOT scored.
- **Clean criteria** (all required):
  1. CG-1..CG-N PASS;
  2. ≥ 2 of 3 tasks with ≥ 1 successful `read_file`;
  3. rejected-repeat share ≤ 25% of calls;
  4. cost ratio to the budget worst case ≤ 1.0 on every task;
  5. zero BLOCKING Review Card anomalies (INFORMATIONAL flags do not fail).
- STOP: D3 = MANUAL; any criterion fails; anything unexpected appears.
- On STOP: commit records + review card on the calibration branch, push,
  update LIVE_STATUS. Under D5, a gate failure is reported, not fixed.

## §4 Phase C — MAIN + variance + scoring

Only if D3 = AUTO_IF_CLEAN and all clean criteria hold, or a later message
says `D3 = YES`. Freeze predictions before any label load (tag pushed first).
Score with decision rules exactly. Name the arm. No "dominance", no E2E claim.

## §5 Acceptance criteria

| ID | Check |
|----|-------|
| AC-1 | audit reproduces the prior table |
| AC-2 | tests RED before and GREEN after |
| AC-3 | diff contains only the amendment changes |
| AC-4 | gate vX on the prior run FAILs (RED) |
| AC-5 | review card flags the affected runs |
| AC-6 | LIVE_STATUS has every key; blocks test passes |
| AC-7 | full-suite failing set == the known-failures artifact |
| AC-8 | ruff, mypy strict, `git diff --check`; `git status` clean |
| AC-9 | Phase A spend = $0.00 |
| AC-10 | (Phase C) predictions freeze tag pushed before any label load |
| AC-11 | (Phase C) verdict follows decision rules mechanically |

## §6 Final response format

```
DECISION: <READY | CAL_CLEAN | CAL_STOP(<criterion>) | MAIN_DONE(<verdict>) | BLOCKED(<reason>)>
<calibration>: calls, successful reads/task, rejected share, longest rejection run, cost, review-card flags
MAIN (if run): n, D pooled, Q5, [Q2.5,Q97.5] for P and S, cost ratios, EMPTY rate, spend
CHANGED: commits, tags, branches
API SPEND: $
LIVE_STATUS: position_short / next_short
NEXT: one line
```