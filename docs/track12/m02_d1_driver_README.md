# T12 M02-D1 — Minimal Per-Arm Driver (Pre-Flight + Dry-Run Only)

**Mission:** `T12_M02_D1_20261027` (Track 1.2), Task 5.
**Zero benchmark API · Zero live experiments · Zero API USD**

## What this is

A provable, minimal orchestration driver composed EXCLUSIVELY from real,
frozen, source-verified interfaces (read-only):

| Engine | Frozen script / callable | Contract verified by source read (2026-10-27) |
| --- | --- | --- |
| Patch materializer | `scripts/opws_phase3b_patch_materialize.py` | `--repo --parent --target --task-id --scope-json --classification-json [--test-authority-json] [--allow-added] [--dry-run] [--out-dir]`; `--dry-run` writes nothing |
| F2P engine (3 nodes × 3) | `src/benchmark/wp2/harness_v3.py :: run_state_v3` | keyword-only `(era_key, worktree_linux, tid, state, test_files, install_fragment, ...)`; "One V3 container per state: **fresh unique DB** ... then **3x per changed-test-file**" |
| F2P smoke (single node) | `scripts/wp2_m3b_runner_smoke.py` | positional args; `--dry-run` prints preflight evidence and exits 0 without side effects; fresh `out_dir` per run (no reuse); per-run DB `opws_m3b_<task>_<stamp>_<nonce>` |
| P2P engine | `scripts/wp2_p2p_u_v2_exec.py` | `--task (req) --cap 200\|400 (choices) [--run-label] [--evidence-root] [--dry-run]` |

**THE DRIVER RUNS NOTHING** — there is intentionally no `run` subcommand and
no mock. It provides `preflight` (fail-closed typed STOPs) and `dry-run`
(deterministic per-arm NOT_RUN manifest), which is all the mission permits.

## Frozen per-arm scope/classification input pins (NEW in M02-D1)

Recovered from the frozen `EFFECTIVE_PATCH_PLAN_219.json` `arm_status` block
(`scope_source` + `source_sha256`) and byte-verified against this machine
(2026-10-27):

| arm | scope_source | pin status |
| --- | --- | --- |
| SIP, RM_CSS | `research/wp1a/sip_rmcss_per_task_predictions.json` | MATCH `76f16217…` |
| AGENT | `research/wp1b/main-297-2026-09-22/wp1b_agent_predictions.json` | MATCH `c0b85dc7…` |
| AGENTLESS_STYLE_ADAPTATION | `D:/wp2_agentless_main297/research/competitor-agentless-r1/agentless_r1_prediction_freeze.json` | MATCH `90495bbb…` |
| DENSE_K3/K10, BM25_K3/K10, BM25_TO_CIA_1HOP | `D:/wp2_comp_baselines/research/competitor-baselines-r2/per_task_predictions_r2.json` | MATCH `601e9c19…` |
| GOLD | `research/saleor-reserve-300-rmcss/saleor_reserve_300_proxies.json` | MATCH `d4ecdb7d…` |
| SELECT_ALL | `benchmark_data/.../scientific/<task>/public/candidate_universe.json` (pilot) | PINNED `38b4db0e…` |
| NEG | derived-control:empty-scope | DERIVED |
| FULL_REFERENCE | materialize_full_reference | DERIVED |

The materializer's **`--classification-json` remains UNRESOLVED**: no frozen
byte-pinned per-arm classification JSON exists on disk (verified 2026-10-27).
This is a real, reported `RUNNER_INTEGRATION_GAP` — never invented away — and
blocks full M02-E execution until the classification-input provenance decision
is made (see `SCIENTIFIC_DECISIONS.md` REQUESTED_DECISION items).

## Commands

```
python scripts/t12_m02_driver.py preflight [--source-repo <path>] [--matrix <csv>] [--plan <json>] [--admission-required]
python scripts/t12_m02_driver.py dry-run   [--source-repo <path>] [--out DRY_RUN_MANIFEST.csv]
```

Typed STOPs: `REQUIRED_WORKTREE_MISSING`, `FROZEN_WORKTREE_DRIFT`,
`ENGINE_SCRIPT_MISSING`, `ENGINE_HASH_DRIFT`, `SOURCE_REPO_MISSING_OR_OID_UNRESOLVED`,
`SCOPE_SOURCE_MISSING`, `SCOPE_PIN_DRIFT`, `REQUIRED_MATRIX/PLAN_MISSING`,
`MATRIX/PLAN_HASH_MISMATCH`, `RUNNER_INTEGRATION_GAP_CLASSIFICATION_INPUT_UNRESOLVED`.

Exit codes: `0` preflight/dry-run complete · `4` typed STOP · `3` usage.

## Test gate

`pytest tests/unit/wp2/test_t12_m02_driver.py` (13 tests) — fail-closed
admission, no-run-mode, verified-flag dry-run, 13 NOT_RUN rows, real-interface
byte-verification when the frozen worktree is present.
