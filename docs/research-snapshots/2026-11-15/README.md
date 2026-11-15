# MSc Research Evidence Snapshot — 2026-11-15

**Status:** Documentation-only review proposal. **Not a new experiment.** No change to any frozen source or previous decision. This directory is a dated cross-track locator, not a replacement for `docs/EXPERIMENT_LEDGER.md`, `docs/RESULTS_SUMMARY.md`, or `docs/CLAIM_REGISTRY.md`.

**Navigation:** [Exact numbers, interpretation and lineage](METRICS_AND_CLAIMS.md) · [Track ownership, blockers and next gates](TRACKS_AND_NEXT_GATES.md) · [Machine-readable provenance](PROVENANCE.json).

## Start here — verified research claims

1. **Saleor RESERVE-300:** RM-CSS file-set F1 `0.3568726` vs SIP `0.2647462`; paired delta `+0.0921264` (95% CI `[0.0690794, 0.1156339]`, `n=300`). Source is the committed original `reports/saleor_reserve_300_rmcss_result.json`.
2. **Saleor MAIN_297, selection stage only:** RM-CSS F1 `0.3568254`; bounded Agent F1 `0.3630692`. Preregistered NI margin `0.05` supported; margin `0.03` inconclusive. Mean *selection-stage* total tokens, marginal view A: RM-CSS `17,011.3232` vs Agent `79,531.4747` (78.61% fewer); mean marginal model calls `2.0` vs `7.2828`. No E2E quality inference. Source `reports/wp1b_main297_result.json`.
3. **External SWE-bench Verified controls, n=10:** C-BM25 `3/10 RESOLVED` and C-GOLD `3/10 RESOLVED`, one generation POST per task per arm, `20` original POSTs and `$0.2751398` combined model-inference cost. C-GOLD is an *oracle scope*, not RM-CSS, and its lower token use is **not** deployable/empirical RM-CSS savings. This November evidence is derived from separately supplied analysis files, not revalidated against the full immutable `D:\WP2\swe_lane_work` original within this snapshot.
4. **Cross-repo RM-CSS limitation:** The attached 2026-11-14 handoff for `django__django-13658` documents a hard STOP: the frozen RM-CSS recipe lacked task-visible SIP, dense scores and repository memory for Django. No extra experiment was run; this is not a performance result.
5. **NEED_FILE escalation integration:** Policy/integration tests **26/26 PASS** reported and code/test files inspected; `2/3` `NO_EDITS + NEED_FILE` historical requests admitted a file. `4` additional paid continuation POSTs are **planned only**; `0` executed, `0` new E2E resolutions. The planner is **not** proven wired into an operational live POST path. Its risk controls must be audited and executed before approving any spend.

## Distinguish three levels of support

- **REPOSITORY-ORIGINAL VERIFIED:** source JSON fetched from canonical repository `main` by path and blob SHA; numbers quoted directly.
- **ATTACHMENT-DERIVED / SOURCE-LIMITED:** independently inspected supplied report/CSV/ZIP, but not freshly compared to original frozen raw attempt/evaluator files on the user's machine.
- **REPORTED / NOT YET AUDITED:** previous track handoffs/progress/status; the latest exact repository commit or result requires a local custody recheck.

## Hard boundaries

- No merges into `main` without review; the docs branch is proposed as a **Draft PR**.
- Preserve frozen tasks, original requests/responses, protocols, labels, baselines, results and hashes exactly; append corrections as derived views.
- Keep Saleor RM-CSS selection results separate from external BM25/Gold generation results; do not conflate the 78.61% selection saving with the 62.20% oracle-scope generation-token difference.
- Positive benchmark tests for individual tasks do not prove contamination-free generalization. Parent-only author inputs avoid **direct oracle/reference leakage**, but cannot rule out model training-data contamination.
- No secret keys, complete raw HTTP payloads, unreviewed raw data or proprietary blobs added to a public repo here. Store exact locator + digest instead.

**As-of:** 2026-11-15 (Africa/Cairo). This is a documentation snapshot, *not* an assertion that all five ongoing research tracks are fully published. See [missing evidence and explicit pending actions](TRACKS_AND_NEXT_GATES.md).
