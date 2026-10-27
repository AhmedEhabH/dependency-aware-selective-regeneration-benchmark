# T12 M02-D1 — Read-Only 13-Arm Comparator Adapter (Hardened) + Driver Feasibility

**Mission:** `T12_M02_ARM_ADAPTER_READINESS_20261027` → `T12_M02_D1_20261027` ·
**Zero benchmark API · Zero live experiments · Zero API USD**
Branch: `research/track-1-2-opws-comparators-2026-10-27`

## What this is

A minimal, stdlib-only, **fail-closed** adapter set that plans, gates and audits
the 13 frozen change-scope arms of the Track 1.2 comparator benchmark under
**Option B (REUSE_NOT_PERMITTED)**, hardened by M02-D1 per the independent
review (``C:\Users\Ahmed\Downloads\T12_M02_REVIEW_AND_NEXT_GATE_20261027.md``):

| Review finding | M02-D1 resolution |
| --- | --- |
| Preflight missing-input bypass | `preflight --admission-required` + `gate` fail closed with typed stops (`REQUIRED_*_MISSING`, `FROZEN_WORKTREE_DRIFT`, `*_HASH_MISMATCH`); diagnostic mode is labelled `INCOMPLETE_NOT_ADMISSION`, never execution-ready |
| Partial JUnit can PASS | new per-run receipt schema + validator (`scripts/t12_m02_receipts.py`): 9/9 JUnit, declared==actual classification, monotonic times, teardown, DB/execution identity; historical R7 checker kept as explicit scoped diagnostic |
| Constant-True leakage claim | removed `results_are_outcome_domain_only()`; replaced by `structural_assertion_only()` policy report with `runtime_isolation_verified: PENDING` + `prompt_leakage_audit: PENDING` |
| Auth schema holes | `validate_authorization` v2: exact frozen tasks, duplicate/unknown arms rejected, bounded USD/token/duration caps, ISO-UTC window pair, explicit `generation_api_budget_usd=0` declaration for the reference phase, `DECLARATIVE_SCHEMA_ONLY` (no live grant) |
| Stats not frozen / driver gap | `SCIENTIFIC_DECISIONS.md` labels remaining decisions REQUESTED_DECISION; minimal per-arm driver `scripts/t12_m02_driver.py` (pre-flight + dry-run ONLY) with per-arm scope-source byte pins |

It does **not** execute anything. It can never substitute old R7/R8 receipts
for prospective M02-E observations.

## Files

| File | Purpose |
| --- | --- |
| `scripts/t12_m02_arm_adapter.py` | hardened adapter (stdlib only) |
| `scripts/t12_m02_receipts.py` | per-run receipt schema + validator + R7 historical diagnostic |
| `scripts/t12_m02_driver.py` | minimal per-arm driver — pre-flight + dry-run only |
| `tests/unit/wp2/test_t12_m02_arm_adapter.py` | adapter tests incl. M02-D1 adversarial cases |
| `tests/unit/wp2/test_t12_m02_receipts.py` | receipt completeness + Option B identity tests |
| `tests/unit/wp2/test_t12_m02_driver.py` | driver fail-closed + pin tests |

## Commands (all read-only)

```
python scripts/t12_m02_arm_adapter.py preflight [--worktree <path>] [--matrix <csv>] [--plan <json>] [--route <json>] [--admission-required]
python scripts/t12_m02_arm_adapter.py dry-run   [--worktree <path>] [--out <manifest.csv>]
python scripts/t12_m02_arm_adapter.py manifest  [--out <manifest.csv>]
python scripts/t12_m02_arm_adapter.py receipts-check <run_dir>          # legacy single-node classifier diagnostic
python scripts/t12_m02_arm_adapter.py gate      [--auth <json>] [--out M02_GO_STOP.json]
python scripts/t12_m02_arm_adapter.py run --authorization <json>        # FAIL-CLOSED (exit 5: design gap)

python scripts/t12_m02_receipts.py validate-run <arm_run_dir>            # 9/9 JUnit + schema (exit 0/1/2)
python scripts/t12_m02_receipts.py validate-bundle <run_dirs...>         # cross-arm physical identity scan
python scripts/t12_m02_receipts.py r7-diagnostic <r7_state_dir>          # HISTORICAL, not evidence

python scripts/t12_m02_driver.py preflight [--matrix] [--plan] [--admission-required]
python scripts/t12_m02_driver.py dry-run [--source-repo] [--out DRY_RUN_MANIFEST.csv]
```

Exit codes: `0 PASS` · `1 STOP` · `2 PENDING/NOT_RUN` · `3 usage` · `4 HASH/ADMISSION STOP` · `5 RUN_DESIGN_GAP`.

## Frozen pins embedded (verbatim from the M01D kit / R7 package)

- 13 arm identities (arm_id, order, tree OID, scope hash, reference patch
  sha256/bytes, test contract hash, five-field provisional id, alias pair).
- Matrix pin `c7a81b06…` (EXECUTION_IDENTITY_MATRIX.csv), plan pin
  `62ef7358…` (EFFECTIVE_PATCH_PLAN_219.json), route pin `974eaf1f…`
  (BENCHMARK_ROUTE_REFERENCE.json).
- Frozen worktree HEAD `22d56946…` and R7 stage hashes for
  `wp2_m3b_runner_smoke.py`, `harness_v3.py`, `opws_isolated_runtime_v1.py`,
  `runtime_image_compat_v1.py`.
- **NEW (M02-D1)** per-arm scope-source byte pins recovered from the frozen
  plan `arm_status` block: 10 of 13 byte-verified on this machine
  (`research/wp1a/sip_rmcss_per_task_predictions.json`, `wp1b` agent
  predictions, agentless freeze, competitor-baselines r2, reserve-300 proxies),
  SELECT_ALL pilot `candidate_universe.json` pinned, NEG/FULL_REFERENCE derived
  controls. The per-arm `--classification-json` file remains UNRESOLVED (no
  frozen byte-pinned artifact on disk) → typed RUNNER_INTEGRATION_GAP on the
  driver preflight.
- 3 frozen F2P nodes + the R7 `f2p_nodes_sha256` pin (`aa12d546…`),
  serialization not disclosed in the kit → enforced by exact node-list match.
- 3 F2P nodes × 3 invocations = **9 JUnit receipts per arm-run**, 1 task,
  `scientific_independent_repetitions = FALSE` (no pseudo-replication).

## Identity convention (documented, don't conflate with the matrix label)

`four_field_id = sha256(scope_hash | patch_sha256 | patch_bytes | test_contract_hash)`
→ 12 classes for 13 arms; alias pair `AGENTLESS_STYLE_ADAPTATION` / `BM25_K3`
shares one class but requires **two physical executions** under Option B.

## Option-B receipt contract (M02-D1)

Each future arm run dir must contain `run_receipt.json` (schema
`t12_m02_run_receipt_v1`) plus `junit/*.xml` (9 receipts named
`<task8>_<armtag8>_r<rep>_f<node>.xml`), recording: exact task/arm, frozen tree
OID, scope/patch/contract hashes, frozen node ids, 3 repetitions, separate
process/execution id, isolated DB identity + teardown receipt, monotonic
start/end, stdout/stderr/exit, host/environment/pinned image, CPU/RAM/disk/net
samplers and cost/request receipts. Missing proof ⇒ STOP/NOT_MEASURED.
`validate-bundle` forbids the same physical receipt or DB/run identity across
arms and never infers reuse from identical bytes (signal only).

## Known integration gap (why no arm ever runs here)

| Stage | Frozen ingredient | 13-arm orchestration |
| --- | --- | --- |
| Materialize reference patch | `opws_phase3b_patch_materialize.py` (flags verified; `--dry-run` writes nothing) | driver dry-run composes it; scope sources pinned 12/13 |
| F2P execute (3 nodes × 3) | `harness_v3.run_state_v3` (fresh unique DB per state, 3x per changed test file) via m3b smoke | MISSING 13-arm orchestrator; driver is pre-flight/dry-run only |
| P2P execute | `wp2_p2p_u_v2_exec.py --task <TID> --cap 200\|400` | EXISTS (budget-gated; cap choice is a researcher decision) |
| Receipts/isolation | per-arm JUnit + run_receipt.json | `scripts/t12_m02_receipts.py` |

Remaining BLOCKER for a real M02-E run: no frozen byte-pinned per-arm
**classification JSON** (`--classification-json`) exists on disk (verified
10/27) — `RUNNER_INTEGRATION_GAP`, reported, never invented away — plus a
separately authorized execution, exclusive resource window, and the
classification-input provenance decision.

## Honesty limits

- Historical R7/R8 receipts classify correctly (27/27) but are **never**
  prospective evidence; the R7 checker is explicitly scoped as
  `HISTORICAL_DIAGNOSTIC_ONLY`.
- No invented flags; every planned command uses flags verified by source
  inspection. Driver has NO run mode and no mock.
- No leakage claim stronger than structural: `structural_assertion_only()`
  marks runtime isolation PENDING; prompts/labels from private tasks are never
  exposed in public deliverables.
