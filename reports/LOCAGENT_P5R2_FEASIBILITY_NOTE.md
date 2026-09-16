# LocAgent P5R-2 — Feasibility Note (ZERO new live calls)

**Date:** 2026-09-17
**Tier:** T2/T3 zero-API feasibility analysis
**Status:** DIAGNOSTIC ONLY — no new P5R live call tonight unless the conditions
below are proven.

---

## 1. Background

P5R-1 rescue pilot: 0/5 usable (2026-09-16). Original P5 stays immutable.
After the P5R-1 report correction (PF-013), the operational picture is:

- The wrapper `--timeout 1800` WAS honored (`args.timeout=1800`; the case ran
  ~33 min wall time before the `process.join(timeout=args.timeout)` deadline).
- The log line `Processing time exceeded 15 minutes` is a STALE fixed string in
  the upstream `TimeoutError` handler, not a 900 s hard cap.
- Failure mix at P5R-1: 2 context-length (262,144 ceiling), 1 workflow-deadline
  (1800 s join after long search), 1 worker crash, 1 completed-but-empty.

## 2. What a genuine P5R-2 would need

### 2.1 Minimal code/config change to extend the workflow deadline
- **Not needed:** the wrapper `--timeout` already controls
  `process.join(timeout=args.timeout)`. No upstream edit is required to extend
  the deadline.
- **Optional:** silence the misleading log string
  (`Processing time exceeded 15 minutes` → `Processing time exceeded
  {args.timeout}`) — a cosmetic upstream edit, forbidden for P5-series
  reproduction unless done in a clearly-marked P5R-2 variant.
- Therefore there is **no clean operational fix to chase** for the
  workflow-deadline case: the deadline is already configurable.

### 2.2 Larger-context route for the SAME model weights
- The two context-length cases need >262,144 context on the SAME model weights
  (qwen3-coder / Qwen3-Coder-480B-A35B-Instruct).
- Verified same-route max = 262,144 (OpenRouter qwen3-coder).
- Whether a DIFFERENT provider serves the same weights with a larger context
  ceiling is NOT verified from a primary source tonight. **P5R-2 must NOT run
  until that is verified** (a provider-deviation diagnostic would otherwise be
  a model/route change).

### 2.3 Remaining failures
- Worker crash (4307e1b8c2e2): infra; a clean P5R-2 would need a reproduced
  stack trace (zero-API: from the persisted localize.log) before deciding.
- Completed-but-empty (b39799f9fc1c): framework/parser behavior; not fixable
  by timeout/context.

## 3. Feasibility verdict

- **P5R-2 is NOT run tonight.** Reasons:
  1. No verified same-weights larger-context route exists in the evidence
     (a P5R-2 provider deviation cannot be justified without that verification);
  2. the remaining failures (worker crash, completed-but-empty) are not
     operational-capacity artifacts;
  3. per the mission, P5R-2 would only be a one-shot diagnostic with a proven
     fix, and none is proven.

- **LocAgent P5 robustness: CLOSED WITH LIMITATION** (2026-09-17). The original
  P5 remains the immutable system-level shared-protocol comparison; the P5R-1
  pilot documents that the 5 non-usable outcomes were a mix of context-capacity,
  long-running search, worker-crash, and completed-but-empty behavior — not a
  single fixable operational defect.

## 4. Future trigger (for a later session, not tonight)

- Verify (from a primary source) whether a provider serves Qwen3-Coder-480B
  with context > 262,144 while preserving the same weights; if yes, run ONLY
  the context-failing task under a clearly-marked `P5R-2 PROVIDER-DEVIATION
  DIAGNOSTIC` with <=$2.00 / <=10M tokens, one-shot.

## 5. Traceability

- Corrected finding: reports/LOCAGENT_P5R1_PILOT_REPORT.md §3; PF-013.
- P5 immutable; no blended P5R metric.