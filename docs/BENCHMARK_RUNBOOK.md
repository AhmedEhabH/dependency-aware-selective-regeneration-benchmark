# Benchmark Runbook

> **Last reviewed:** 2026-09-14 (prospective refactor milestone).
>
> One documented workflow for dry-run, capability probe, live benchmark, and
> ordinary use. Historical study-specific launchers remain the reproducible
> source of truth; the unified CLI is a thin wrapper over them.

---

## 1. Prerequisites

- Python 3.11
- The repository checked out (see README install section).
- API tokens referenced by environment-variable name:
  - `OPENROUTER_API_KEY` (OpenRouter);
  - `DEEPSEEK_API_KEY` (DeepSeek direct — future profile);
  - `HF_TOKEN` (Hugging Face Inference Providers — future profile).

Dry-run and verify require **no** token. Probe and live require the token for
the selected profile.

## 2. Workflow overview

```
models -> dry-run -> probe -> [six gates + audit] -> live -> verify -> metrics
```

| Step | Command | Token required? | Calls |
|---|---|---|---|
| List profiles | `python scripts/benchmark_cli.py models` | no | 0 |
| Dry run | `python scripts/benchmark_cli.py dry-run --study <study>` | no | 0 |
| Capability probe | `python scripts/benchmark_cli.py probe --study <study> --model-profile <id>` | yes | few real (non-held-out) |
| Verify (six gates + audit) | `python scripts/benchmark_cli.py verify --study <study>` | no | 0 |
| Live run | `python scripts/benchmark_cli.py live --study <study> --model-profile <id>` | yes | study cells |

## 3. Registered studies

| study id | launcher | verify | notes |
|---|---|---|---|
| `real-commit-p1` | `scripts/execute_real_commit_p1.py` | `scripts/verify_real_commit_p1_gates.py` | REAL-COMMIT FULL-v2 vs SPARSE-v2 held-out (10 tasks × 2 arms × 3 reps = 60 cells) |
| `controlled-encoding-16k` | `scripts/controlled_encoding_ablation_16k_execute.py` | `scripts/verify_controlled_encoding_16k_claims.py` | Controlled 16K cap-relaxed encoding ablation (6 scenarios × 2 arms × 5 reps = 60 cells) |

## 4. Study-specific launchers (historical, frozen)

These launchers were used to produce the completed evidence and remain the
reproducible source of truth. Do not change their frozen constants.

### P1 — real-commit held-out evaluation

```powershell
python scripts/execute_real_commit_p1.py prevalidate
python scripts/execute_real_commit_p1.py endpoint-freeze   # requires OPENROUTER_API_KEY
python scripts/execute_real_commit_p1.py probe             # requires OPENROUTER_API_KEY
python scripts/execute_real_commit_p1.py gates             # ZERO API
python scripts/execute_real_commit_p1.py freeze-manifest
python scripts/execute_real_commit_p1.py run               # requires OPENROUTER_API_KEY
python scripts/execute_real_commit_p1.py metrics
python scripts/execute_real_commit_p1.py close
```

The 2026-09-14 serialized-record correction is recomputed with:

```powershell
python scripts/recompute_real_commit_p1_serialization_metric.py
```

### Controlled 16K encoding ablation

```powershell
python scripts/controlled_encoding_ablation_16k_execute.py prevalidate
python scripts/controlled_encoding_ablation_16k_execute.py parity
python scripts/controlled_encoding_ablation_16k_execute.py prompt-control
python scripts/controlled_encoding_ablation_16k_execute.py probe
python scripts/controlled_encoding_ablation_16k_execute.py gates
python scripts/controlled_encoding_ablation_16k_execute.py freeze-manifest
python scripts/controlled_encoding_ablation_16k_execute.py run
python scripts/controlled_encoding_ablation_16k_execute.py metrics
python scripts/controlled_encoding_ablation_16k_execute.py interpret
python scripts/controlled_encoding_ablation_16k_execute.py close
```

## 5. Six pre-benchmark gates

1. **Dataset Validation** — data identity and split correctness.
2. **Prompt Validation** — prompt parity and leakage.
3. **Pipeline Smoke Test** — code path works end-to-end on fixtures.
4. **Dry Run** — exact run plan without API calls (freeze the manifest).
5. **Integration Test** — components interoperate correctly.
6. **Metric Verification** — scoring is mathematically correct.

Then an **independent audit** checks persisted evidence and protocol invariants.

## 6. Scientific discipline for live runs

- Freeze the fully resolved model profile **before call #1** and persist it in
  the manifest (profile_id, exact model, provider, endpoint/base URL,
  capability probe, price snapshot, completion cap, temperature, fallback
  policy, schema mode, profile/config SHA-256).
- A live run **refuses to continue** if the resolved profile differs from the
  frozen manifest (`assert_resolved_matches_frozen`).
- No silent provider fallback; deterministic bounded retries only; persist retry
  count/error category; never result-dependent rerun.
- The historical diff is an **OBSERVED CHANGE-SET PROXY**, never semantic ground
  truth. Independent task = historical change; repeated model calls are nested
  observations.

## 7. Cost control

- `budget_abort_ceiling_usd` — pre-run safety threshold.
- `estimated_api_cost_usd` — token usage × frozen endpoint prices.
- `provider_billed_cost_usd` — actual billing (nullable).

A budget ceiling is **not** a scientific result.

## 8. Post-run verification

```powershell
python scripts/benchmark_cli.py verify --study real-commit-p1
python scripts/verify_paper_claims.py          # headline manuscript metrics
python scripts/recompute_real_commit_p1_serialization_metric.py   # P1 serialized-record correction
```

## 9. Troubleshooting

- **Missing token** → set the env var named by `api_key_env` for the profile;
  probe/live fail clearly when it is missing.
- **Shared-pool overload (429/timeout)** → deterministic bounded retry; never
  silently switch providers inside a frozen arm.
- **Windows `fork` blocker (LocAgent)** → P5 real pilot requires a POSIX host or
  a documented patch layer; see `reports/LOCAGENT_P5B_VALIDATION_BLOCKER_REPORT.md`.