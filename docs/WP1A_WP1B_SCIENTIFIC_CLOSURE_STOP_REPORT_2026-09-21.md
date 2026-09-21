# WP-1a / WP-1b Scientific Closure — STOP Report (2026-09-21)

# 1. Executive decision

```
DECISION: BLOCKED
```

WP-1b is **NOT ready for authorization**. Two prospective scientific decisions
are required before any paid WP-1b call: **(G1)** a frozen F1
non-inferiority margin, and **(G2)** the agent-control completion cap
(512 vs 1024). WP-1a preparation is integration-complete (AC-1A.1..12 PASS)
and has been merged to `main`. No margin was invented, no cap was silently
changed, no Saleor RESERVE outcomes were opened, and no paid inference ran
(API spend $0.00).

# 2. Repository state

- Branch at start: `feat/wp1a-selection-baseline-preparation` @
  `c53d918a885ba9d506cc8cad9833406dc617d04c`
- origin/main at start: `f25950f7a673e135bbb2c40d447a2265a6b73180` (main == origin/main)
- Working tree at start: clean
- Commits created this mission (branch then main): `f526a47`, `8005c4a`,
  `3bc65d3`, `b366778`, `4d83858`, `5e15ab0`, `2eeb69b`, `b680c2e`, `0bff03b`,
  `be54160`, `73bcf4b`, `79c702c`, `1755f01`, `a9a5c2f` on the feature
  branch; merge `18652d6` ("chore(wp1a): close integration and preregister
  WP1b blockers") on `main`; followed by `32d7933` (closure machine-readable
  output + governance).
- **Merge state:** merged (--no-ff). main HEAD = `32d7933` at report write
  time. origin/main still `f25950f` — **PUSH PENDING** (github.com was
  unreachable during this session; see section 16).
- Working tree at STOP: clean.

# 3. Verified evidence

Each item was independently inspected/recomputed in this session; evidence
paths included.

- [VERIFIED] Sample ordering hash
  `445b5e9d0aeeab9551e8feeb3e59e6b5bcfee793f029810a6efe0cbc8f126447`
  recomputed from `research/saleor-reserve-300-rmcss/saleor_reserve_300_sample.json`
  (script `scripts/wp1b_closure_recompute.py`, output
  `artifacts/wp1a_wp1b_closure_recomputation.json`).
- [VERIFIED] main-50 `task_ids_sha256`
  `9b26ad5965f6f6a134c7defe50e20c5811df46f7d703ce7fdf954e572db8ee32` and
  `manifest_sha256` `299c045f…` recomputed; calibration-3
  `task_ids_sha256` `23f520d8…` and `manifest_sha256` `d14388a8…` recomputed
  (same source).
- [VERIFIED] main-50 ∩ calibration-3 = empty (recomputed intersection size 0).
- [VERIFIED] Pooled SIP F1 `0.26474622770919065`, RM-CSS F1
  `0.35687263556116017`, DeltaF1 `+0.09212640785196952` recomputed from
  `research/wp1a/sip_rmcss_per_task_predictions.json` +
  `research/saleor-reserve-300-rmcss/saleor_reserve_300_proxies.json` WITHOUT
  importing `benchmark.wp1a.*` helpers; 300 per-task prediction hashes all
  re-derived and matched.
- [VERIFIED] v1.1 microstudy (`reports/scientific_microstudy_v11/run_records.jsonl`,
  SHA-256 `fadc6d63…`): 30/30 records `agent_control_max_completion_tokens=1024`;
  0 control-truncation messages; aggregate selection completion tokens min 0 /
  max 3513 / mean 1589 (see `artifacts/wp1b_completion_cap_truncation_evidence.json`).
- [VERIFIED] Live OpenRouter metadata (2026-09-21T02:59:03Z): model
  `qwen/qwen3-coder`, route `deepinfra/turbo`, $0.30/$1.00 per 1M, context
  262144, structured-output + tools supported, route available — matches the
  frozen protocol (`artifacts/wp1b_provider_pricing_preflight_2026-09-21.json`).
- [VERIFIED] `IterativeRepositoryAgentStrategy` call-8 forced-final semantics
  from `src/benchmark/strategies/iterative_agent.py` (MAX_AGENT_CALLS=8;
  force_final when remaining==1; AGENT_FINAL_SCHEMA; truncation/round-cap/
  parser/infrastructure EMPTY classification). Additive telemetry verified by
  `tests/unit/test_wp1b_loop_termination.py` (8 passed + 1 documented gap-skip)
  and `tests/unit/test_wp1b_truncation_telemetry.py` (7 passed).
- [VERIFIED] Post-merge re-audit from `main` (`18652d6`): recompute OVERALL
  PASS, cross-check 19/19 PASS, targeted suite **146 passed / 1 skipped**,
  full suite **3700 passed / 35 skipped / 5 failed** where the 5 failures are
  PRE-EXISTING baseline failures reproduced at `f25950f`
  (`test_d96_…_no_github_machinery`, `test_stagec_…_all_six_gates_pass`,
  `test_stagec_…_pinned_source_available`,
  `test_model_identity_policy…_current_facing_docs`,
  `test_readme_markdown_tables…_svg_fallbacks`).

# 4. Claims not independently verified

- [CLAIMED] Historical per-record token totals beyond the recomputed
  truncation evidence (recorded in the v1.1 report).
- [CLAIMED] All "independent audit" statements in historical, non-WP-1a
  reports (out of scope for this mission).
- [CLAIMED] The 5 pre-existing full-suite failures are unrelated to WP-1a/WP-1b
  (established by baseline reproduction at `f25950f`, not by reading each
  failing assertion's root cause beyond the reproduced trace).

# 5. G1 — NI margin / statistical decision rule

- **Status:** BLOCKED — DECISION REQUIRED.
- **Evidence:** `docs/WP1B_NI_MARGIN_DECISION_REQUIRED_2026-09-21.md`
  (provenance table of every NI-margin source: DA-08 Δ=0.05 for regression
  pass rate only; `EXPERIMENTAL_DESIGN_V2.md` H1 F1 NI Δ=0.05 candidate for
  `hybrid_selective` vs `repository_agent` whose authority for this experiment
  is not established; WP-1a scorer "no silent margin"; point-estimate
  cost-quality categories). `artifacts/wp1b_ci_decision_rule_preregistration_2026-09-21.json`.
- **Margin exists:** NO frozen F1 margin for the WP-1b selection-only
  comparison. No margin invented.
- **CI rule:** preregistered — D = F1(RM-CSS) − F1(Agent), paired task
  bootstrap, 95% percentile CI; distinguishes non-inferiority / statistical
  superiority / descriptive point advantage / inconclusive; activated only
  together with a frozen margin.
- **Remaining decision:** Ahmed/supervisor must prospectively freeze a margin
  (options A–D in the decision-required document) before WP-1b.

# 6. G2 — completion cap

- **Status:** BLOCKED — DECISION REQUIRED.
- **512 provenance:** Kaggle pilot control-plane cap (D13 B2, `a4606a5`),
  code default with an operational "bounded structured JSON" rationale
  (`37fa31c`), carried into the WP-1a freeze. No WP-1b-specific scientific
  justification.
- **1024 provenance:** v1.1 scientific-run value (`PROTOCOL_VERSION.md`
  "Agent control 1024"; `configs/scientific_microstudy_todo.yaml`
  `agent_control_completion_cap: 1024`; run records 30/30 cap 1024; code
  constant `V11_AGENT_CONTROL_MAX_COMPLETION_TOKENS = 1024`).
- **Historical truncation recomputation:** 0 control-truncations across the
  30 v1.1 records at 1024 (see section 3).
- **Final frozen status:** 512 remains the frozen value in
  `research/wp1a/wp1a_frozen_agent_protocol.json`; a proposed prospective
  amendment 512→1024 exists at `docs/WP1B_AGENT_COMPLETION_CAP_AMENDMENT_2026-09-21.md`
  (NOT effective; requires authorization).
- **Amendment status:** PROPOSED, pre-result, pending authorization.

# 7. G3 — forced-final semantics

- State machine documented in `docs/WP1B_AGENT_LOOP_TERMINATION_SEMANTICS_2026-09-21.md`.
- Calls 1–7 explore; call 8 is forced final (AGENT_FINAL_SCHEMA + control
  message); a valid final is accepted; truncation → EMPTY (truncation);
  malformed/schema-invalid on the last call → EMPTY (parser_failure); no
  final by end of call 8 → EMPTY (round_cap); deadline → EMPTY
  (infrastructure). Prediction collected before the cap survives.
- Instrumented (behavior-preserving): `selection_empty_reason`,
  `selection_truncation_count`, `selection_malformed_count`,
  `selection_schema_invalid_count`, `selection_valid_final_count`,
  `selection_finish_reason_distribution`; telemetry schema in
  `src/benchmark/wp1b/telemetry.py`.
- Tests: `tests/unit/test_wp1b_loop_termination.py` (8 passed, 1 documented
  transport-retry-gap skip) + `tests/unit/test_wp1b_truncation_telemetry.py`
  (7 passed). Final-answer schema risk: [VERIFIED] schema requires
  `selected_paths` alongside `rationale` (no large free-form text ordered
  before the selection); [INFERRED] residual token pressure is handled by the
  G2 cap decision + truncation telemetry.

# 8. G4 — audit independence

- The WP-1a 19/19 "independent audit" was authored in the same execution
  context as the WP-1a implementation. It is relabelled a **same-session
  alternate-implementation cross-check** (transparent terminology correction in
  `research/wp1a/wp1a_independent_audit.json`,
  `research/wp1a/wp1a_acceptance_report.json` AC-1A.10,
  `research/wp1a/wp1a_frozen_agent_protocol.json`, WP-1 draft, WP-1a impact
  declaration, PROGRESS.md, test docstrings).
- A blind independent-audit packet is prepared at
  `exports/wp1a_independent_audit_packet_2026-09-21/`
  (README_AUDITOR.md, acceptance_criteria.json, artifact_manifest.json,
  sha256sums.txt, recompute_instructions.md) with explicit
  do-not-assume-PASS instructions.

# 9. WP-1a integration

- Pre-merge: targeted tests pass; protocol validation (25 frozen-protocol
  sections) pass; manifest validation (recomputed hashes) pass; scorer
  reproduction pass; artifact hash validation pass.
- Merged to `main` (`--no-ff`, merge `18652d6`) because all integration
  criteria pass and the G1/G2 ambiguities are FAIL-CLOSED (WP-1b cannot start
  under an ambiguous protocol). Merge commit message per contract:
  "chore(wp1a): close integration and preregister WP1b blockers".
- Post-merge re-audit from `main`: pre-merge branch HEAD `a9a5c2f`,
  post-merge `18652d6`; targeted 146 passed / 1 skipped; recomputed manifest
  hashes unchanged; scoring reproduction exact; cross-check 19/19; full suite
  3700/35/5 with 5 PRE-EXISTING baseline failures (reproduced at `f25950f`) —
  **no material post-merge difference, no FAIL CLOSED**.
- Integration closure table: `docs/WP1A_INTEGRATION_CLOSURE_2026-09-21.md`.

# 10. WP-1b variance substudy

- Preregistered (frozen before outcomes): 15 of the frozen main-50 tasks,
  3 fresh executions each, temperature unchanged, all scientific knobs
  identical to main; the first main execution is NOT counted as replicate 1.
- Selection: `sha256(salt + task_id)`, salt
  `wp1b-variance-substudy-v1-2026-09-21`, sorted ascending, first 15;
  selection-manifest SHA-256 `2c4ac5b1…`.
- Artifacts: `artifacts/wp1b_variance_substudy_preregistration_2026-09-21.json`,
  `docs/WP1B_VARIANCE_SUBSTUDY_PREREGISTRATION_2026-09-21.md`, selection
  script + 3 tests.

# 11. Pricing and budget

- Live preflight (no paid inference): model/route/prices match the frozen
  protocol; no drift.
- Estimated (label-free, frozen budget-model basis): Calibration-3 ≈ $0.06,
  Main-50 ≈ $1.04, variance-substudy additional ≈ $0.62, expected total ≈
  $1.73, conservative ceiling ≈ $2.00; upper-bound completion-cap exposure
  ≈ $1.46 (all with the 1.5× safety factor where applied). These are
  estimates, not actual spend.
- **Actual API spend for this closure mission: $0.00.**

# 12. Calibration gate

- Frozen before inference: `artifacts/wp1b_calibration_gate.json`
  (CG-1..CG-9; FROZEN_BEFORE_INFERENCE), evaluator
  `scripts/wp1b_calibration_gate.py` (ZERO API, deterministic), 5 tests.
- No F1-based continuation rule; calibration F1 does not gate the main run;
  cap hits during calibration are reported, not a stop trigger (the frozen
  pre-run protocol defines no such trigger).

# 13. Acceptance table

| AC | Status | Mechanical evidence |
|----|--------|---------------------|
| AC-1A.1 | PASS | `research/wp1a/sip_scientific_model_provenance.json`; recomputed from run records |
| AC-1A.2 | PASS | cross-check A6; `src/benchmark/wp1a/schema.py` boundary |
| AC-1A.3 | PASS | `wp1_rederivation_verification.json` + independent recomputation |
| AC-1A.4 | PASS | manifests + recomputed intersection 0 |
| AC-1A.5 | PASS | `wp1a_intent_parity.json` 53/53 |
| AC-1A.6 | PASS | `wp1a_frozen_agent_protocol.json` 25 sections; mock tests |
| AC-1A.7 | PASS | `src/benchmark/wp1a/scorer.py`; cross-check A12 |
| AC-1A.8 | PASS | `wp1a_accounting_schema.json`; cross-check A13 |
| AC-1A.9 | PASS | `wp1a_budget_model.json`; cross-check A14 |
| AC-1A.10 | PASS | `wp1a_independent_audit.json` 19/19 cross-check (relabelled); audit packet prepared |
| AC-1A.11 | PASS | source scan; $0.00 spend |
| AC-1A.12 | PASS | cross-check A16; no 786 access |
| AC-01 | PASS | authority inventory + hashes |
| AC-02 | PASS | independent recomputation (3+ values) |
| AC-03 | PASS | main/cal intersection = 0 |
| AC-04 | PASS | no margin invented; decision-required blocker raised |
| AC-05 | PASS | CI rule preregistered; no point-estimate dominance |
| AC-06 | PASS | cap provenance documented; proposed amendment, not silent change |
| AC-07 | PASS | truncation telemetry instrumented + tested |
| AC-08 | PASS | forced-final precedence unambiguous + tested |
| AC-09 | PASS | same-session verification not labeled independent |
| AC-10 | PASS | blind audit packet with manifest + hashes |
| AC-11 | PASS | variance subset frozen prospectively |
| AC-12 | PASS | live route/model/pricing recorded, no paid inference |
| AC-13 | PASS | calibration gate frozen before inference |
| AC-14 | PASS | no paid inference; no spend authorization |
| AC-15 | PASS | post-merge ZERO-API validation from main; no material difference |

# 14. Unknowns and limitations

WHAT WE VERIFIED: see section 3.
WHAT WAS ONLY CLAIMED: see section 4.
WHAT WE INFERRED: no frozen WP-1b F1 margin (per the WP-1a authoritative
artifacts); 512 cap poses a-priori instrument-harm risk on large Saleor final
answers; CI crossing zero = inconclusive at this n.
WHAT REMAINS UNKNOWN:
- method-level inference reproducibility of the repository-agent arm (scoring
  reproducibility proven; method reproducibility untested);
- the exact F1 non-inferiority margin (G1 decision);
- the final completion cap (G2 decision);
- variance outside the 15-task substudy; cross-provider/cross-model
  generalization;
- the external independent-audit result (packet prepared, not yet executed by
  an independent auditor);
- disposition of the 5 pre-existing full-suite baseline failures (unrelated to
  WP-1a/WP-1b);
- origin/main push completion (github.com unreachable at STOP).
WHAT WOULD INVALIDATE THE CURRENT INTERPRETATION:
- discovery of a frozen authoritative F1 margin for this experiment that this
  audit missed (would unblock G1 with that value);
- evidence that the WP-1b Saleor control responses fit 512 without truncation
  AND supervisor confirms 512 scientifically (would unblock G2 with 512);
- a materially different post-merge result from a re-run of the acceptance
  suite.

# 15. Falsifiers

- G1 recommendation (do not invent a margin) is wrong if an authoritative
  frozen margin exists for the selection-only comparison.
- G2 recommendation (decision required) is wrong if a WP-1b-specific frozen
  justification for 512 or 1024 exists that this audit missed.
- The "no material post-merge difference" verdict is wrong if the 5
  pre-existing failures are shown to be caused by the merged state (they were
  reproduced at the pre-mission baseline `f25950f`).
- The $0.00-spend claim is wrong if any paid endpoint was invoked (source
  scan + no paid run).

# 16. Next permitted action

```
A. Resolve the NI-margin decision (G1).
```
Concretely: Ahmed/supervisor reviews `docs/WP1B_NI_MARGIN_DECISION_REQUIRED_2026-09-21.md`,
freezes a margin prospectively, then resolves G2
(`docs/WP1B_AGENT_COMPLETION_CAP_AMENDMENT_2026-09-21.md`), then provides an
explicit WP-1b spend authorization. Until the margin and cap are frozen, paid
WP-1b must not run. Separately, origin/main must be pushed once github.com is
reachable (see below).

---

## Required scientific unknowns (contract section 34)

Covered in section 14.

## Push status

`git push` of main and the feature branch was attempted but github.com was
unreachable (connect timeout on port 443) at STOP time. All closure evidence is
committed locally on `main` (`32d7933`). **PUSH PENDING — not a scientific
blocker; the next session/step should push origin/main + the feature branch.**
The feature branch was previously pushed (origin/feat/wp1a-selection-baseline-preparation
@ `c53d918`); the new branch commits since then are local.