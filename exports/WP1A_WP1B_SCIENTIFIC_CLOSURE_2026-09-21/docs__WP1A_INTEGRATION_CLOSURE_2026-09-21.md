# WP-1a Integration Closure — 2026-09-21

**Status:** WP-1a is integration-ready as a preparation work package. The
G1 (NI margin) and G2 (completion cap) decisions remain OPEN and are explicit
blockers that FAIL-CLOSE paid WP-1b; the integration artifacts make WP-1b
unable to start under an ambiguous protocol.

Every PASS below points to a file, hash, test exit code, recomputed number, or
explicit protocol statement — not prose.

## WP-1a acceptance criteria (AC-1A.1..12)

| ID | Requirement | Evidence | Status |
|----|-------------|----------|--------|
| AC-1A.1 | Model/provider provenance | `research/wp1a/sip_scientific_model_provenance.json`: 300/300 `qwen/qwen3-coder` @ `deepinfra/turbo`; recomputed from `research/saleor-reserve-300-rmcss/sip_300_run_records.jsonl` (SHA-256 `fadc6d6…`) | PASS |
| AC-1A.2 | Label isolation | `research/wp1a/wp1a_acceptance_report.json` AC-1A.2 PASS; cross-check A6 `raw_artifact_forbidden_present` + `prediction_view_label_free` PASS; `src/benchmark/wp1a/schema.py` drops `label` at boundary | PASS |
| AC-1A.3 | Exact 300 re-derivation | `research/wp1a/wp1_rederivation_verification.json` verification=EXACT_REPRODUCTION; independently recomputed SIP F1 0.26474622770919065 / RM-CSS F1 0.35687263556116017 / DeltaF1 +0.09212640785196952 (matches, `artifacts/wp1a_wp1b_closure_recomputation.json`) | PASS |
| AC-1A.4 | Main-50 + calibration-3 freeze + disjointness | manifests `research/wp1a/wp1_main_50_manifest.json` (`9b26ad59…`), `wp1_calibration_3_manifest.json` (`23f520d8…`); recomputed intersection size 0 (`artifacts/wp1a_wp1b_closure_recomputation.json`) | PASS |
| AC-1A.5 | Intent parity | `research/wp1a/wp1a_intent_parity.json` status WP1A_INTENT_PARITY_PASS, 53/53 canonical hash match | PASS |
| AC-1A.6 | Agent protocol frozen + mock-executable | `research/wp1a/wp1a_frozen_agent_protocol.json` status FROZEN_FOR_FUTURE_EXECUTION, 25 required sections (cross-check A11); `tests/unit/test_wp1a_frozen_protocol.py` 3/3 | PASS |
| AC-1A.7 | Shared scorer | `src/benchmark/wp1a/scorer.py`; cross-check A12 synthetic tp=1 fp=1 fn=1 f1=0.5; `tests/unit/test_wp1a_scorer_accounting_budget.py` | PASS |
| AC-1A.8 | Efficiency accounting identities | `research/wp1a/wp1a_accounting_schema.json`; cross-check A13 `tokens = prompt + completion` identity present | PASS |
| AC-1A.9 | Budget feasibility / pre-request guard | `research/wp1a/wp1a_budget_model.json` (main 50, cal 3, cap 512, ceiling $1.103733 RECOMMENDED, BUDGET_ABORT rule); cross-check A14 | PASS |
| AC-1A.10 | Same-session cross-check (relabelled) | `research/wp1a/wp1a_independent_audit.json` 19/19 PASS (run `python scripts/wp1a_independent_audit.py`, exit 0); terminology corrected 2026-09-21; blind audit packet `exports/wp1a_independent_audit_packet_2026-09-21/` | PASS |
| AC-1A.11 | No scientific API calls / $0.00 | source scan in `scripts/wp1a_acceptance_report.py`; all WP-1a scripts local recomputation; mission API spend $0.00 | PASS |
| AC-1A.12 | 786 RESERVE untouched | cross-check A16 source scan; WP-1a artifacts use only the opened 300 proxies | PASS |

## Blocker / readiness items (G1–G6)

| ID | Requirement | Evidence | Status |
|----|-------------|----------|--------|
| G1 | NI-margin provenance + CI rule | `docs/WP1B_NI_MARGIN_DECISION_REQUIRED_2026-09-21.md` (full provenance table); `artifacts/wp1b_ci_decision_rule_preregistration_2026-09-21.json` | BLOCKED — DECISION REQUIRED (no margin invented; paid WP-1b fail-closed) |
| G2 | Completion-cap provenance + truncation metrics | `docs/WP1B_AGENT_COMPLETION_CAP_PROVENANCE_2026-09-21.md` (timeline); `docs/WP1B_AGENT_COMPLETION_CAP_AMENDMENT_2026-09-21.md` (PROPOSED, not effective); `artifacts/wp1b_completion_cap_truncation_evidence.json` (v1.1: 30/30 cap 1024, 0 truncations) | BLOCKED — DECISION REQUIRED |
| G3 | Forced-final semantics + tests | `docs/WP1B_AGENT_LOOP_TERMINATION_SEMANTICS_2026-09-21.md`; `tests/unit/test_wp1b_loop_termination.py` 8 passed + 1 documented gap-skip; `tests/unit/test_wp1b_truncation_telemetry.py` 7 passed | PASS (instrumented; telemetry additive) |
| G4 | Audit terminology + independent-audit handoff | relabelled `research/wp1a/wp1a_independent_audit.json` / `wp1a_acceptance_report.json` AC-1A.10; `exports/wp1a_independent_audit_packet_2026-09-21/` (README_AUDITOR.md, acceptance_criteria.json, artifact_manifest.json, sha256sums.txt, recompute_instructions.md) | PASS |
| G5 | Variance-substudy preregistration | `artifacts/wp1b_variance_substudy_preregistration_2026-09-21.json` (salt frozen, 15 of 50, digest-sorted, selection sha `2c4ac5b1…`); `docs/WP1B_VARIANCE_SUBSTUDY_PREREGISTRATION_2026-09-21.md`; `tests/unit/test_wp1b_variance_substudy.py` 3 passed | PASS |
| G6 | Pricing preflight | `artifacts/wp1b_provider_pricing_preflight_2026-09-21.json` (live OpenRouter metadata, generated 2026-09-21T02:59:03Z, no_drift=True); `docs/WP1B_PROVIDER_PRICING_PREFLIGHT_2026-09-21.md`; `tests/unit/test_wp1b_pricing_preflight.py` 2 passed | PASS |
| Cal-3 gate | Frozen before inference | `artifacts/wp1b_calibration_gate.json` (CG-1..9, FROZEN_BEFORE_INFERENCE); `scripts/wp1b_calibration_gate.py` evaluator; `tests/unit/test_wp1b_calibration_gate.py` 5 passed | PASS (frozen; not evaluated) |

## Verification performed at this gate

- Targeted WP-1a/WP-1b tests: **79 passed / 1 skipped** (`python -m pytest tests/unit/test_wp1a_* tests/unit/test_wp1b_* -q`).
- Iterative-agent integration: `tests/integration/test_su0011_iterative_agent.py` **25 passed**.
- Ruff clean on all changed Python files; `mypy --strict` clean on changed production files; `py_compile` clean.
- Scorer reproduction: independent recomputation (`scripts/wp1b_closure_recompute.py`, exit 0) reproduces all headline values.
- Manifest + artifact hash validation: sample ordering hash, main-50/cal-3 task-id + manifest hashes, per-task prediction hashes all recomputed and match.
- Protocol validation: WP-1a frozen-agent-protocol 25 required sections (cross-check A11).

## WP-1a scientific state (unchanged)

- Frozen scientific result SALEOR_RESERVE_300_RMCSS unchanged (RM-CSS F1 0.3569 vs SIP 0.2647, Delta F1 +0.0921 CI [+0.0691,+0.1156]).
- WP-1b NOT executed. No main n=50 result exists.

## Integration decision

WP-1a preparation is integration-ready: all AC-1A.1..12 PASS, G3/G4/G5/G6
closed, and G1/G2 are explicitly FAIL-CLOSED for paid WP-1b (no margin frozen,
cap decision pending). Merging this closure work to `main` does NOT authorize
WP-1b spend.

## Falsifiers

- This closure is wrong if any AC evidence hash/recomputation above does not
  re-derive from the committed artifacts.
- The G1/G2 blocker framing is wrong if an authoritative pre-existing decision
  (margin or cap) exists that this audit missed.