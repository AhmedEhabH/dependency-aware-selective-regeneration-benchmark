# SU-0013 — Repository-Agent Selection Baseline Preparation (WP-1a)

**Change ID:** SU-0013
**Title:** WP-1a zero-API preparation for the Repository-Agent vs SIP vs RM-CSS
selection-only baseline
**Date:** 2026-09-21
**Branch:** `feat/wp1a-selection-baseline-preparation`
**Tier:** T3 (freezes scientific harness semantics, data-flow leakage
boundaries, accounting and future experiment invariants)
**Scientific API spend:** $0.00 (no paid scientific model/API call; no
repository-agent scientific execution; no scoring of future main n=50 agent
predictions; WP-1b NOT started)
**Requirement / defect:** WP-1 (Repository-Agent Selection-Only Baseline) must
be prepared scientifically and mechanically so a later paid WP-1b can run a
same-protocol comparison without hidden model mismatch, label leakage,
re-derivation drift, biased sample selection, or ambiguous accounting. The WP-1
draft claimed the SIP scientific model as DeepSeek; the frozen Saleor-300 SIP
run was later reported to have used Qwen3-Coder — parity must be mechanically
established before any paid run.
**Reason for change:** freezes the WP-1b execution contract (model identity,
label-free prediction boundary, exact 300 re-derivation, main-50/calibration-3
sample freeze, intent parity, agent protocol, failure semantics, shared scorer,
accounting, budget, outcome categories, independent audit) BEFORE any paid
WP-1b call.

## Scope

WP-1a ONLY. Files touched are restricted to:
`docs/WP1A_IMPACT_DECLARATION_2026-09-21.md` (new),
`docs/WP1_REPOSITORY_AGENT_SELECTION_ONLY_BASELINE_DRAFT.md` (model correction
+ status note only),
`research/wp1a/*` (new frozen artifacts),
`src/benchmark/wp1a/*` (new zero-API helper package: schema / rederive / scorer
/ accounting / budget / semantics),
`scripts/wp1a_*.py` (new generation/verification scripts),
`tests/unit/test_wp1a_*.py` (new targeted tests),
`selective_updates/records/SU-0013-repository-agent-selection-baseline-preparation.md`
(this record),
`DECISIONS.md` (append-only entry),
`PROGRESS.md` (current state).

No production runtime file was required to change: the existing iterative
repository agent already satisfies the label-free parent-state boundary
(WP-0/G7); the WP-1a protocol freezes it and proves mock-executability.

## Corrections / findings

### A. Scientific model parity (AC-1A.1)

Mechanically recovered from `research/saleor-reserve-300-rmcss/sip_300_run_records.jsonl`
(300/300 records):
- `scientific_model`: `qwen/qwen3-coder`
- `provider_tag`: `deepinfra/turbo`
- `exact_model`: `openrouter:qwen/qwen3-coder@deepinfra/turbo`
- `temperature`: 0.0
- `completion_cap`: 16384
- `graph`: OFF
- `serialization_policy`: `sparse_v2`
- per-task `prompt_sha256` recorded (300 unique)
- frozen prompt-template source: `src/benchmark/real_commits/p1_evaluation.py`
  SHA-256 `65eb7e9a…`

The WP-1 draft's DeepSeek model claim is FALSE and corrected. The future
WP-1b repository-agent generative arm MUST use the same Qwen3-Coder identity.
Artifact: `research/wp1a/sip_scientific_model_provenance.json`.

### B. Label isolation (AC-1A.2)

`research/saleor-reserve-300-rmcss/candidate_rows_saleor300.parquet` contains a
`label` column (all-zero placeholder). Prediction-side loaders now drop/deny
label/outcome columns at the boundary
(`src/benchmark/wp1a/schema.py` `load_prediction_view`); tests fail if
prediction-side code receives forbidden columns. The repository-agent candidate
universe comes from parent-state/public sources
(`public/candidate_universe.json`), never labeled candidate rows.

### C. Exact 300 re-derivation (AC-1A.3)

Deterministic zero-API re-derivation reconstructs per-task SIP and RM-CSS
predicted sets from the frozen artifacts only (stored SIP run records + frozen
deployment artifact + frozen threshold 0.20 + label-free candidate view). The
full-300 re-scoring reproduces the authoritative headline values EXACTLY:
SIP TP/FP/FN 193/344/728 (P 0.3594040968 / R 0.2095548317 / F1 0.2647462277);
RM-CSS 283/382/638 (P 0.4255639098 / R 0.3072747014 / F1 0.3568726356);
DeltaF1 +0.09212640785196952. Persisted:
`research/wp1a/sip_rmcss_per_task_predictions.json` (SHA-256 manifest) +
`wp1_rederivation_verification.json`. The historical Saleor-300 result artifact
is NOT replaced.

### D. Sample freeze (AC-1A.4)

Main n=50 = first 50 of the frozen Saleor-300 deterministic ordering
(`research/wp1a/wp1_main_50_manifest.json`, task list SHA-256
`9b26ad59…`). Calibration n=3 = deterministic complement draw with
`numpy.random.default_rng(20260921)` (`saleor-rc-349d46d906ad`,
`saleor-rc-b05633dae118`, `saleor-rc-d52a55471bfc`; SHA-256 `23f520d8…`)
(`research/wp1a/wp1_calibration_3_manifest.json`). Intersection empty;
both from the already-opened 300 only; 786 RESERVE outcomes untouched.

### E. Intent parity (AC-1A.5)

Authoritative intent source = frozen public intent bundle
(`benchmark_data/real_commit_impact_saleor/scientific/<case_id>/public/intent.json`).
53/53 main+calibration tasks have canonical hash match
(`research/wp1a/wp1a_intent_parity.json`, status WP1A_INTENT_PARITY_PASS).
Future agent input intent MUST be byte-identical / canonical-hash-identical to
the stored SIP intent.

### F. Frozen agent protocol (AC-1A.6)

`research/wp1a/wp1a_frozen_agent_protocol.json` freezes the authoritative
iterative repository-agent protocol (initial prompt, tools, schemas, parent
snapshot source, candidate-universe boundary, file/search policy, context
retention/truncation, round definition, MAX_AGENT_CALLS=8, control cap 512,
stop/timeout/retry/malformed/empty rules, path-outside-universe handling,
duplicate normalization, `allow_ground_truth_universe=False`, RunRecord audit
field, final file-set JSON schema, fail-closed semantics). Mock-executable with
a stub backend (`tests/unit/test_wp1a_frozen_protocol.py`).

### G. Failure semantics / shared scorer / accounting / budget / categories

Pre-registered in `research/wp1a/wp1a_failure_semantics.json`,
`wp1a_shared_scorer_schema.json`, `wp1a_accounting_schema.json`,
`wp1a_budget_model.json` (recommended future ceiling ~$1.10 for Ahmed review;
BUDGET_ABORT_INVALID_FOR_PRIMARY_COMPARISON pre-registered),
`wp1a_cost_quality_categories.json`. Implementation in
`src/benchmark/wp1a/{semantics,scorer,accounting,budget}.py`.

## POST-CHANGE EVIDENCE

### Independent audit (AC-1A.10)

`research/wp1a/wp1a_independent_audit.json`: 19/19 PASS (recomputed WITHOUT
importing the audited helpers): sample hash, main-50, calibration-3,
disjointness, intent parity, label-free schema, parent-only universe, exact
reproduction, per-task hashes, model provenance, protocol completeness, scorer
formula, accounting identities, budget inputs, allow_ground_truth_universe
False, no 786-RESERVE access.

### Acceptance report (AC-1A.1..AC-1A.12)

`research/wp1a/wp1a_acceptance_report.json`: ALL_PASS.

### Tests / static checks

- New WP-1a unit tests: 50/50 PASS.
- WP-0 leakage regression: `test_artifact_universe_no_ground_truth.py` 14/14.
- Calibrated + Saleor-300 regressions: 35/35.
- Iterative-agent integration: `test_su0011_iterative_agent.py` 25/25.
- ruff: PASS (changed files).
- mypy --strict on `src/benchmark/wp1a/`: PASS.
- py_compile: PASS (all changed files).
- `git diff --check`: PASS.

## LIMITATIONS

- WP-1b (calibration n=3 + main n=50 repository-agent run) is NOT executed and
  requires Ahmed authorization.
- 3 calibration tasks cannot prove a worst case; WP-1b hard protection = fixed
  max rounds + fixed response cap + context cap + cumulative USD guard before
  each paid request + main-run ceiling frozen before main task 1.
- Latency is descriptive only (no same-machine matched re-measurement).
- No E2E / WP-2 / G6 / Smoke / Pilot work is started.

## Code/Data/Notebook status

- Code Dataset: `src/benchmark/wp1a/**` NEW (no production runtime change).
- Data Dataset: `research/wp1a/**` NEW frozen artifacts; historical Saleor-300
  artifacts unchanged (read-only inputs).
- Notebook: unchanged.

## Next step

WP-1b Calibration + Main n=50 Selection Run — AWAITING AHMED AUTHORIZATION. Do
NOT run it in this work package.