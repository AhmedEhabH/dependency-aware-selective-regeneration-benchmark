# WP-1b Preflight Freeze — STOP Report (2026-09-21)

**Mission:** `WP1B_PREFLIGHT_FREEZE_2026-09-21` (T3).
**Branch:** `wp1b/preflight-freeze-2026-09-21`.
**API spend through Phases 0–B: $0.00.**

## 1. Executive decision

```
DECISION: PREFLIGHT_FROZEN
```

Phases 0, A and B are complete with **zero API spend**. G1 (NI margin), G2
(completion cap), budget model v2 (G8), the sample-size amendment (G9), the
decision rules v2, the agent telemetry (G10) and the exploratory
preregistration are all frozen pre-result. All Phase-B acceptance criteria
PASS. **Calibration-3 (3 tasks, cap 1024, ceiling $0.25) is authorized (D6 =
YES) and is the next permitted action.** The main run and variance substudy are
**NOT** authorized (D7 = NO).

## 2. Git sync (Phase 0)

- Local `main` at start: `1ae7058331445ef2fa25d784b2356f19702815dc`.
- `origin/main` at start: `87c86f5d7b6802fa13c1d2b79d1312b945aa498f`.
- Push: initial attempts failed (network); succeeded on the 60 s retry
  (`87c86f5..1ae7058 main -> main`).
- Verified `git ls-remote origin refs/heads/main` == local `main` ==
  `1ae7058…` (AC-P0).
- Branch `wp1b/preflight-freeze-2026-09-21` created from `main`; all Phase
  A–B work on it.

## 3. Phase A (hygiene, zero API)

### A1 — Tests no longer mutate frozen artifacts
- Four generator scripts (`wp1a_independent_audit.py`, `wp1a_acceptance_report.py`,
  `wp1b_closure_recompute.py`, `wp1b_variance_substudy_selection.py`) accept
  `--out <dir>`; tests write into a pytest `tmp_path`. Default human-run
  behaviour byte-identical.
- NEW artifacts store repository-relative POSIX paths.
- Frozen artifacts NOT rewritten (absolute-path leak recorded as a cosmetic
  defect in `DECISIONS.md`).
- Added `tests/unit/test_no_tracked_artifact_mutation.py` (6 tests): snapshots
  every file under `artifacts/` + `research/wp1a/`, runs the four generators
  in-process with `tmp_path` outputs, asserts snapshots unchanged.
- Acceptance: targeted WP-0/WP-1 suite green; `git status --porcelain` empty
  after running it. (AC-P1, AC-P2)

### A2 — Name the 5 pre-existing full-suite failures
- Full suite on clean checkout: **5 failed / 3700 passed / 35 skipped**.
- Node IDs + class recorded in `docs/KNOWN_TEST_FAILURES_2026-09-21.md` and
  `artifacts/known_test_failures_2026-09-21.json`:
  - `test_d96_kaggle_github_boundary.py::test_runtime_launch_resume_path_has_no_github_machinery` — REAL_DEFECT
  - `test_stagec_djangocms_runtime_wiring.py::test_all_six_gates_pass` — ENV_OR_DATA_MISSING
  - `test_stagec_djangocms_runtime_wiring.py::test_pinned_source_available` — ENV_OR_DATA_MISSING
  - `test_model_identity_policy.py::test_full_model_name_present_in_current_facing_docs` — REAL_DEFECT
  - `test_readme_markdown_tables.py::TestReadmeSvgFallbacks::test_svg_fallbacks_exist_and_are_embedded` — REAL_DEFECT
- New full-suite acceptance rule: set of failing node IDs == known list
  (AC-P3). REAL_DEFECTs added to `TODO.md` (not fixed in this mission).

### A3 — Independent-audit packet v2
- `exports/wp1a_independent_audit_packet_2026-09-21_v2/` (v1 untouched).
  Adds the coefficient-order trap (in `deployment_artifact.json` `lr_coef` is
  ordered `continuous_features + boolean_features`, NOT the `feature_names`
  order; 0/300 vs 174/300 mismatches) and the FULL-only inputs list (public
  `candidate_universe.json` / `dependency_graph.json` / `saleor_development_manifest.json`).

### A4 — Export housekeeping
- Restored the provenance-verified D13R2 `dist/pilot-kaggle-upload.zip`
  (SHA-256 `65269528049b1f22f277c508f0b0db5b09d536e99fd31d306cfbbfb42e47ef9f`,
  sidecar matches) from `_historical_archive/` so the FULL export includes it;
  one `DECISIONS.md` line.

## 4. Appendix R re-derivation (AGREE/DISAGREE)

Every Appendix R number was independently re-derived with OpenCode's own code
(`scripts/wp1b_appendix_r_rederivation.py`), NOT copied from the external
reference evidence script (which was never committed). Comparison via
`scripts/wp1b_appendix_r_agreement.py`.

**Result: 125 comparisons, 0 disagreements, status ALL_AGREE** (recorded in
`research/wp1b/wp1b_appendix_r_agreement.json`).

- R-A pooled micro-F1: AGREE (RESERVE-300 SIP 0.26474622770919065 / RM-CSS
  0.35687263556116017 / Δ +0.09212640785196952; MAIN_50 0.30204 / 0.39231 /
  +0.09027).
- R-B RM-CSS reproduction: AGREE (0/300 with documented coefficient order;
  174/300 if `feature_names` order).
- R-C power: AGREE (SE 0.0377 / 0.0277; n=50/150/297 table).
- R-D budget: AGREE (universe mean 810 [438,1140], ~11190 prompt tokens/call,
  underestimate factor ~3.398).
- R-E exploratory headroom: AGREE.

## 5. Phase B (pre-result freeze, zero API)

All new WP-1b artifacts under `research/wp1b/`.

- **B1 Budget model v2 (G8):** `wp1b_budget_model_v2.json`. Real ArtifactUniverse
  per task (production path, `allow_ground_truth_universe=False`) + exact
  initial prompt rendered label-free. Worst case (8 calls, cap 1024) and totals
  for Calibration-3 / Main-50 / Main-150 / Main-297 / variance (15×3), each
  ×1.5. **No ceiling below worst case ×1.5** (cal $0.202 ≤ $0.25; main-297
  $18.640 ≤ $21.50; variance $3.025 ≤ $3.50). Underestimate factor vs v1 ≈
  3.40×. Abort rule v2 preregistered (BUDGET_ABORT + nested MAIN_50
  `UNDERPOWERED_FALLBACK` exception). AC-P6.
- **B2 Sample-size amendment (G9):** `wp1b_main_297_manifest.json` (n=297,
  first 50 == WP-1a MAIN_50 exact, calibration IDs absent, hashes recorded),
  `wp1b_main_150_manifest.json` (n=149; one calibration task
  `saleor-rc-349d46d906ad` removed), `wp1b_main_50_manifest.json` (unchanged).
  Power doc `docs/WP1B_POWER_AND_SAMPLE_SIZE_2026-09-21.md`. AC-P7.
- **B3 Freeze G1:** `wp1b_ni_margin_frozen.json` +
  `docs/WP1B_NI_MARGIN_FROZEN_2026-09-21.md` (Δ0.05, Q5 rule, inheritance
  record, coherence anchor + relative size). AC-P8.
- **B4 Decision rules v2:** `wp1b_decision_rules_v2.json` (P/S dual analysis,
  seven ordered quality verdicts, cost CHEAPER rule, five final categories;
  "dominance" retired). AC-P9.
- **B5 Freeze G2:** DECISIONS.md `WP1B_G2_COMPLETION_CAP_2026_09_21` EFFECTIVE
  (D3); `wp1b_frozen_agent_protocol_v2.json` (cap 1024); runner-config test
  `tests/unit/test_wp1b_g2_cap_freeze.py` asserts 1024 + frozen SIP/RM-CSS
  artifacts unchanged. AC-P10.
- **B6 Agent telemetry (G10):** additive per-call sidecar JSONL + per-task
  observation metrics in `iterative_agent.py` + `telemetry.py`; behavior
  preservation proven by `tests/unit/test_wp1b_agent_telemetry_golden.py`;
  disclosure `docs/WP1B_AGENT_BASELINE_DISCLOSURE_2026-09-21.md`. AC-P11.
- **B7 Exploratory preregistration:** `wp1b_exploratory_prereg.json` X1–X5,
  status `EXPLORATORY_PREREGISTERED`; only after the primary result is frozen
  and tagged; never part of the primary verdict. AC-P12.

## 6. Acceptance criteria

| ID | Check | Status |
|----|-------|--------|
| AC-P0 | origin/main == local main before branch | PASS (`1ae7058…`) |
| AC-P1 | Targeted WP-0/WP-1 suite green + `git status --porcelain` empty after running | PASS (62 passed / 1 skipped) |
| AC-P2 | `test_no_tracked_artifact_mutation.py` passes | PASS (6) |
| AC-P3 | Full suite failing-node set == known list | PASS (baseline 5/3700/35) |
| AC-P4 | Pooled F1 re-derived exact (SIP 0.26474622770919065, RM-CSS 0.35687263556116017) | PASS (re-derived, AGREE) |
| AC-P5 | RM-CSS reproduced 0/300 with documented order | PASS (AGREE R-B) |
| AC-P6 | Budget v2; universe/base tokens within ±15% of R-D; no ceiling below worst ×1.5 | PASS |
| AC-P7 | New manifest: first 50 == MAIN_50; calibration absent; hashes recorded | PASS |
| AC-P8 | G1 artifact: margin, statistic, CI, Q5, inheritance, coherence anchor, relative size | PASS |
| AC-P9 | Decision rules v2: P/S, seven verdicts, cost rule | PASS |
| AC-P10 | G2 EFFECTIVE in DECISIONS.md; protocol v2; runner config test asserts 1024 | PASS |
| AC-P11 | Telemetry golden test identical behavior | PASS |
| AC-P12 | Exploratory prereg X1–X5 + status | PASS |
| AC-P13 | No new artifact contains absolute machine path | PASS (scan 0 hits) |
| AC-P14 | API spend in Phases 0–B = $0.00 | PASS |
| AC-P15 | ruff, mypy strict, `git diff --check` pass on changed files | PASS |

## 7. Independent self-audit

- **Objective unchanged:** WP-1b preflight freeze; G1/G2 decided; budget v2; n
  amendment; decision rules v2. No scope creep into paid runs.
- **Plan adherence:** executed Phase 0 → A1–A4 → Appendix R → B1–B7 in order.
- **Over-engineering:** none; each change is contract-driven.
- **Debt:** the 5 pre-existing full-suite failures are recorded, not fixed
  (contract forbids fixing REAL_DEFECT outside WP-1); absolute-path leak in 3
  frozen artifacts recorded as a cosmetic defect (not rewritten).
- **Freshness:** branch pushed state reflects local; `origin/main` synced at
  Phase 0.
- **Scientific knobs:** only G2 (D3) amended; all others frozen.

## 8. Next permitted action

```
A. B8 integration: commit branch work, merge --no-ff to main,
   create annotated tag wp1b-preflight-freeze-2026-09-21 on the merge commit,
   push main + tag, verify with git ls-remote.
B. Produce the TRUE LIGHT export (MANIFEST.json + SHA256SUMS.txt, < 50 MB).
C. Run Calibration-3 (3 tasks, cap 1024, ceiling $0.25) — D6 YES.
D. STOP after Phase C whatever the outcome; commit calibration records +
   gate result on branch wp1b/calibration-3-2026-09-21, push, and report.
E. Do NOT start the main run (D7 NO) until Ahmed reviews the Calibration-3
   STOP report.
```

The 786 unread Saleor RESERVE outcomes are untouched. API spend through
Phase B is $0.00.
