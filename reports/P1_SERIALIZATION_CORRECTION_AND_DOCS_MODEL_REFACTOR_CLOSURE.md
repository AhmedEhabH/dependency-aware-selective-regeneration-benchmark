# P1 Serialization Correction + Reader-First README + Model/Provider Refactor — Closure

**Date:** 2026-09-14
**Branch:** `main`
**Type:** Priority-0 metric correction + Priority-1 docs/model/provider refactor milestone.
**Scientific calls:** ZERO (no model/API calls; no new DeepSeek scientific experiment).

---

## 1. Priority 0 — P1 serialized-record metric correction (COMPLETE, audited)

### Defect

`scripts/execute_real_commit_p1.py` computed `serialized_records` (and
task-level `*_records_mean`) from `len(decoded_write_set_ids)`. That field
contains ONLY decoded `REGENERATE` ids — the **predicted write-set size** — NOT
the number of serialized decision records. The P1 report therefore showed
Full-v2 "Records mean = 4.03", which is impossible as a serialized decision
count for a Full-v2 contract that must emit exactly one decision per candidate
(140–152 candidates, mean 144) and equals the mean REGENERATE write-set size.

### Corrected values (recomputed from persisted raw responses, ZERO API)

| Quantity | Former (write-set size) | Corrected (serialized decisions) |
|---|---:|---:|
| Full-v2 mean | 4.03 | **144.0** |
| Sparse-v2 mean | 2.50 | **4.07** |
| Paired delta | −1.540 [−2.833, −0.367] | **−139.9 [−143.3, −137.0]** |

Independent assertions (every valid cell):
- Full-v2: `serialized_decision_count == candidate_count` — 30/30 PASS.
- Sparse-v2: no explicit `PRESERVE` rows AND `serialized_decision_count ==`
  explicit non-PRESERVE decision count — 30/30 PASS.
- Raw response SHA-256 sidecars re-verified for all 60 cells.

### Artifacts

- `reports/REAL_COMMIT_M4A3_P1_SERIALIZATION_METRIC_CORRECTION.md`
- `research/real-commit-p1-01/final_metrics_serialization_corrected.json`
- `research/real-commit-p1-01/serialization_metric_corrected.json`
- Runner fixed (future records persist `serialized_decision_count` +
  `predicted_write_set_size`); backward-compatible fallback.
- Regression tests: `tests/unit/test_real_commit_p1_serialization_metric.py`
  (9), `tests/integration/test_real_commit_p1_serialization_correction.py` (7).

### Unchanged

P/R/F1/FNR, TP/FP/FN, validity, truncation, token usage, cost, latency.
Raw response bytes unchanged. Historical tags unchanged.

### Related findings (separate decision; frozen evidence preserved)

The M1B (16K) and M3 graph runners use the same `len(decoded_write_set_ids)`
pattern. Audit-quantified M1B Sparse-v2: serialized-decision mean **5.9** vs
reported write-set mean **4.9**. Runners fixed prospectively; frozen
`final_metrics.json` / result reports preserved. Registered TD-011/TD-012/
TD-013.

---

## 2. Priority 1 — Reader-first README + model/provider refactor (COMPLETE)

### Deliverables

- Reader-first `README.md` (results-first; historical detail moved to
  `docs/HISTORICAL_EXPERIMENT_LEDGER.md`; nothing deleted).
- `docs/HISTORICAL_EXPERIMENT_LEDGER.md`
- `docs/MODEL_PROVIDER_GUIDE.md`
- `docs/BENCHMARK_RUNBOOK.md`
- `docs/TECHNICAL_DEBT_REGISTER.md` (seeded; 14 items)
- `config/model_profiles.yaml` (5 profiles: historical Qwen primary, DeepSeek
  Flash/Pro via OpenRouter, DeepSeek direct, HF example)
- `src/benchmark/model_profiles/` — immutable `ModelProfile` /
  `ResolvedModelConfig`, profile SHA-256, fail-closed frozen-manifest matching,
  env-var-only secrets.
- `src/benchmark/model_profiles/cost.py` — `budget_abort_ceiling_usd` /
  `estimated_api_cost_usd` / `provider_billed_cost_usd` separation +
  backward-compatible legacy reader.
- `scripts/benchmark_cli.py` — `models` / `dry-run` / `probe` / `live` /
  `verify` thin wrapper (no study-logic duplication).
- Current-state docs updated: SYSTEM_STATE, TODO, PROJECT_HANDOFF,
  PAPER_WRITING_HANDOFF, MSC_ROADMAP, MODEL_IDENTITIES, START_HERE,
  PROTOCOL_VERSION, PAPER_CLAIM_EVIDENCE_MAP, AGENTS.md.
- `.gitignore` scratch hygiene (TD-009).

### Scientific discipline

- No new DeepSeek scientific run; DeepSeek profiles are future-only.
- Historical primary Qwen result not made dynamic retroactively.
- Live run must freeze resolved profile before call #1 and fail closed if the
  resolved profile differs from the frozen manifest.

---

## 3. Verification

- Targeted tests during implementation: all pass.
- Full suite once at stable closure (deterministic shards): **3090 passed /
  33 skipped / 2 pre-existing environment-gated failures** (the same two
  documented `test_stagec_djangocms_runtime_wiring` tests that require an
  absent gitignored djangocms checkout — TD-008; previous closure recorded the
  same environment conflict).
- `git diff --check` clean; Ruff clean on all changed files; mypy strict clean
  on new modules (model_profiles, cost, benchmark_cli, recompute script);
  zero new mypy errors on edited launchers (baseline 26 == after 26).
- ZERO-API P1 gates + audit: PASS. M1B 16K claims verifier: PASS (43/43).

## 4. Audit checklist (independent)

- Objective unchanged: correct P1 serialized-record metric; reader-first README;
  prospective model/provider refactor. ✔
- Raw evidence, tags, frozen M1B/M3 evidence untouched. ✔
- No over-engineering: profile layer is a small immutable dataclass set, no
  framework. ✔
- Technical debt registered (TD-001…TD-014) with review cadence. ✔
- Historical study launchers remain the reproducible source of truth. ✔