# WP-1b MAIN_297 — STOP Report (2026-09-22)

**DECISION: MAIN_DONE(RMCSS_NONINFERIOR_AT_LOWER_COST)**

Overnight mission `OPENCODE_OVERNIGHT_WP1B_MAIN297_FULL_2026-09-22` executed
end-to-end: Phase A (zero API) → MAIN_297 → variance 15×3 → scoring → X1–X11 →
docs → exports. All gates passed; no hard-stop condition fired.

```
DECISION: MAIN_DONE(RMCSS_NONINFERIOR_AT_LOWER_COST)
MAIN_297: n=297, D pooled -0.0062, Q5 -0.0383, [Q2.5,Q97.5]=[-0.0449,+0.0308] for P;
          S (n dropped=2): D -0.0115, [-0.0502,+0.0255], Q5 -0.0434; verdict row
          NI_SUPPORTED / RMCSS_NONINFERIOR_AT_LOWER_COST; cost ratios (View A:
          calls 0.27x [0.27,0.28], generative tokens 0.21x [0.21,0.22]);
          EMPTY by reason {parser_failure: 2} (0.67%); forced finals 147; calls
          2,164 logical / 2,178 HTTP attempts; ledger USD 7.147415; billed USD
          3.430 (OpenRouter usage delta, descriptive, likely lagging); halts 0 /
          resumes 8 sessions; MAIN card verdict NO_BLOCKING_INSTRUMENT_ANOMALIES
VARIANCE: pooled F1 by replicate {1:0.389, 2:0.438, 3:0.479}; pairwise exact match
          0.444; mean pairwise Jaccard 0.642; EMPTY runs 0; spend $1.194112
EXPLORATORY (labelled): X6 reading ESCALATION_NO_GAIN; X3 reading
          NO_TEACHER_HEADROOM; X10 dense-anchor size-matched F1 0.278; X11 shares
          {multi-word search 0.385, zero-result search 0.427, non-consecutive
          duplicate 0.127}
DRY RUN: D3 max diff 62 chars; D4 projected 0.44-2.66 h (actual main ~2.2 h +
          variance ~0.7 h of sessions); D5 projected $4.11-$8.02 (actual main
          $7.147 within range; variance $1.194)
CHANGED: branches wp1b/main297-harness-2026-09-22, wp1b/main-297-2026-09-22;
          tags wp1b-main297-harness-prereg-2026-09-22,
          wp1b-main297-predictions-frozen-2026-09-22,
          wp1b-variance-predictions-frozen-2026-09-22,
          wp1b-main297-result-2026-09-22 (all verified on origin)
API SPEND: total $8.341527 (main $7.147415 + variance $1.194112), Phase A $0.00
LIVE_STATUS: MAIN_297 DONE: RM-CSS non-inferior at lower cost (NI_SUPPORTED) / Ahmed reviews MAIN_297 -> D6 (AG16) -> WP-2
NEXT: Ahmed decides D6 (AG16 budget-sensitivity on MAIN_50, ceiling $12.20) and WP-2 start
```

## Run facts

- **MAIN_297** (protocol v3, frozen order, ceiling $21.50): 297/297, ledger
  **$7.147415**, 2,164 logical calls / 2,178 HTTP attempts, 23,552,440 prompt
  tokens, 81,683 completion tokens, 147 forced finals, 2 EMPTY (parser_failure),
  0 instrument errors, 8 transport retries, 0 halts, 8 resume-safe sessions.
- **Variance 15×3** (ceiling $3.50): 45/45, ledger **$1.194112**, 331 logical
  calls / 341 HTTP attempts, 0 EMPTY, 26 forced finals.
- **Attempt-aware ledger reconciliation (AC-14):** kept $7.143418 + abandoned
  attempt $0.003997 = ledger $7.147415; per-record mismatches = [] (M6 absent).
- **Freeze-before-labels:** `wp1b-main297-predictions-frozen-2026-09-22` and
  `wp1b-variance-predictions-frozen-2026-09-22` on origin before any label load.
- **Scorer sanity:** re-scored RESERVE-300 SIP/RM-CSS = EXACT_REPRODUCTION
  (RM-CSS F1 0.3569, SIP F1 0.2647, Δ +0.0921); no `SCORER_DRIFT`. The 786
  sealed RESERVE outcomes were never opened (label-access audit hook active).

## Claims and boundaries

- The verdict is mechanical from decision rules v2 (scorer output unedited;
  `dominance_word_retired: true`). No "dominance" claim.
- The comparison is localization-only under one protocol; WP-2 (E2E) and
  E2E-G6 (F2P/P2P) have not started; no Smoke/Pilot/Research Run.
- The agent is a **budget-bounded baseline** (8 calls, 1024 cap, 2000-char
  window, substring search); AG16 budget-sensitivity is preregistered, NOT run
  (D6).

## What was delivered

- `reports/WP1B_MAIN297_RESULT.md`, `reports/wp1b_main297_result.json`,
  `reports/WP1B_VARIANCE_15X3_RESULT.md`, `reports/wp1b_variance_15x3_result.json`,
  `reports/WP1B_MAIN297_EXPLORATORY.md`, `reports/wp1b_main297_exploratory.json`,
  `docs/assets/wp1b_cost_quality_frontier.svg`,
  `paper/wp1b_tables/wp1b_main297_table.tex`,
  `paper/wp1b_tables/wp1b_results_paragraph.tex`.
- README lesson `1e.` + FAQ "What did MAIN_297 show?"; LIVE_STATUS post-run
  (blocks test pass); DECISIONS.md `WP1B_MAIN297 - EXECUTED` and
  `WP1B_MAIN297_RESULT - RMCSS_NONINFERIOR_AT_LOWER_COST`.

## Test side effects restored

After the full suite (A7) the following tracked files were rewritten by tests and
restored with `git checkout --` (never committed): `reports/REAL_COMMIT_M4A3_P1_VALIDATION.md`,
`reports/real_commit_m4a3_p1_gates.json`,
`research/djangocms-confirmatory-route-b/dryrun/confirmatory_dryrun_summary.json`,
`research/djangocms-confirmatory-route-b/dryrun/confirmatory_manifest.json`.
(TODO.md tech-debt line added.)

## Acceptance criteria

AC-1 bundle hash ✓ · AC-2 90 tests + frozen files byte-unchanged ✓ · AC-3
ruff/mypy/diff-check ✓ · AC-4 prereg tag on origin before call 1 ✓ · AC-5
LIVE_STATUS keys + blocks test (pre/post) ✓ · AC-7 full suite 3 failed == known
set ✓ · AC-9 Phase A $0.00 ✓ · AC-10 both freeze tags on origin before labels ✓
· AC-11 verdict mechanical ✓ · AC-12 DRY_RUN_PASS ✓ · AC-13 review cards exit 0
(main + variance) ✓ · AC-14 ledger reconciliation OK + billed/list ratio
recorded ✓ · AC-15 spend $7.15 ≤ $21.50 and $1.19 ≤ $3.50 ✓.

## What remains (not authorized tonight)

- D6 (AG16 budget-sensitivity arm on MAIN_50, ceiling $12.20) — preregistered,
  execution needs a decision.
- WP-2 shared E2E instrument, E2E-G6 F2P/P2P oracle, Smoke → Pilot → Research Run.

## NEXT

`Ahmed decides D6 (AG16 budget-sensitivity on MAIN_50, ceiling $12.20) and the WP-2 start.`