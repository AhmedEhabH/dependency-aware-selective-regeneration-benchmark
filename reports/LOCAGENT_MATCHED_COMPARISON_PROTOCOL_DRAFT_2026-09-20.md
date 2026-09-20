# LocAgent / Agentless / Loc-Bench — Future Matched-Comparison Protocol DRAFT (2026-09-20)

**Status:** DRAFT ONLY. NOT executed. No competitor run, no API budget, no
comparison claim. Prepared by the CALIBRATED_SET_SELECTION_V1 mission (T3,
ZERO API) per mission §30.

---

## 1. Why a matched protocol is required (and why no claim is made now)

- The old **LocAgent F1 ≈ 0.333** result comes from a **DIFFERENT exposed
  10-task population** (the ICCI/P5 exposed HELD_OUT split) and is **NOT
  directly comparable** with the current **323-task DEVELOPMENT** numbers
  (djangoCMS DEV 174 + Saleor DEV 149) or with any future confirmatory set.
- The current method's numbers are DEVELOPMENT evidence (or future
  confirmatory evidence); LocAgent's number is a shared-protocol pilot on an
  exposed split. Cross-population head-to-head ranking is prohibited.
- **No claim is made that the current method beats LocAgent.** None of the
  project's reports assert this.

## 2. Required equality conditions for any valid future comparison

A future comparison is valid ONLY IF it uses, for BOTH arms (the frozen policy
AND the competitor):

1. **Same tasks** (identical case IDs, same parent commits, same split role);
2. **Same evaluator** (same metric code, same TP/FP/FN/P/R/F1/FNR definitions,
   same pooled + task-level aggregation);
3. **Same production-file universe** (same candidate universe definition and
   same exclusion rules per repository);
4. **Same target proxy** (the historical changed-file proxy, joined identically
   AFTER predictions are frozen);
5. **Same file-level metrics** (file-level P/R/F1/FNR; ORR/candidate precision
   as mechanism diagnostics; token/call/cost/latency reported separately);
6. **Fail-closed result** (the competitor's unusable/empty/timeout/crash
   outputs are scored fail-closed — never silently excluded or given partial
   credit);
7. **Usable-only result reported SEPARATELY** (a "usable-only" table in
   addition to the fail-closed table; denominators never mixed);
8. **Tokens, calls, cost, latency** (matched-information reporting for the
   efficiency dimension; the frozen policy is ZERO-API, the competitor is not,
   so cost must be reported per-arm, not assumed equal);
9. **Same split discipline** (DEVELOPMENT vs confirmatory labels never blurred;
   the competitor must not be tuned on the evaluation tasks);
10. **Same budget ceiling / reservation ledger** when API calls are involved.

## 3. Competing systems documented (NOT run)

| System | Status | Note |
|---|---|---|
| LocAgent | NOT run | Acc@k-style publication metric + 10-task shared-protocol pilot (F1≈0.333); needs the matched protocol above |
| Agentless | NOT run | documented competitor; needs matched protocol |
| Loc-Bench | future external-validity benchmark | AFTER the final policy is frozen (Stage 5 confirmatory first) |

## 4. Placement in the roadmap (unchanged)

1. final calibrated policy on Python DEVELOPMENT (THIS mission — closed FAIL,
   negative frozen);
2. freeze ONE final policy (NOT reached);
3. Stage-5 untouched Python confirmation;
4. TypeScript — NestJS;
5. Java — JabRef;
6. Go — Prometheus;
7. true polyglot — Grafana;
8. **matched competitor / Loc-Bench studies** (this draft);
9. downstream regeneration correctness.

## 5. Revisit trigger

Convert this draft into a frozen protocol ONLY after a final policy exists
(i.e., after the V1 successor that passes its own frozen gate AND the Stage-5
confirmatory decision). Any execution requires explicit authorization +
frozen budget + the equality conditions in §2.