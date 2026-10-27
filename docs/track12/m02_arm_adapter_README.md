# T12 M02 — Read-Only 13-Arm Competition Adapter (Track 1.2)

**Mission:** `T12_M02_ARM_ADAPTER_READINESS_20261027` ·
**Zero benchmark API · Zero live experiments · Zero API USD**
Branch: `research/track-1-2-opws-comparators-2026-10-27`

## What this is

A minimal, stdlib-only, **fail-closed** adapter that plans, gates and audits the
13 frozen change-scope arms of the Track 1.2 comparator benchmark under
**Option B (REUSE_NOT_PERMITTED)** — the layer M01D identified as missing
(`arm_runner_13_frozen_interface: UNVERIFIED`).

It does **not** execute anything. It can never substitute old R7/R8 receipts
for prospective M02-E observations. Its `run` path is a documented
integration-gap stub that refuses to execute (exit 5) even with a valid
authorization, because no frozen multi-node per-arm F2P driver exists.

## Files

| File | Purpose |
| --- | --- |
| `scripts/t12_m02_arm_adapter.py` | adapter (standard library only; never imports the harness) |
| `tests/unit/wp2/test_t12_m02_arm_adapter.py` | isolated stdlib tests (a)–(i); `python -m unittest` or pytest |
| this README | design, usage, honesty limits |

## Commands (all read-only)

```
python scripts/t12_m02_arm_adapter.py preflight [--worktree <path>] [--matrix <csv>] [--plan <json>] [--route <json>]
python scripts/t12_m02_arm_adapter.py dry-run   [--worktree <path>] [--out <manifest.csv>]
python scripts/t12_m02_arm_adapter.py manifest  [--out <manifest.csv>]
python scripts/t12_m02_arm_adapter.py receipts-check <run_dir>          # offline JUnit outcome audit
python scripts/t12_m02_arm_adapter.py gate      [--auth <json>] [--out M02_GO_STOP.json]
python scripts/t12_m02_arm_adapter.py run --authorization <json>        # FAIL-CLOSED (exit 5: design gap)
```

Exit codes: `0 PASS` · `1 STOP` · `2 PENDING/NOT_RUN (no execution authorized)` ·
`3 usage` · `4 HASH_MISMATCH` · `5 RUN_DESIGN_GAP`.

## Frozen pins embedded (verbatim from the M01D kit / R7 package)

- 13 arm identities (arm_id, order, tree OID, scope hash, reference patch
  sha256/bytes, test contract hash, five-field provisional id, alias pair).
- Matrix pin `c7a81b06…` (EXECUTION_IDENTITY_MATRIX.csv), plan pin
  `62ef7358…` (EFFECTIVE_PATCH_PLAN_219.json), route pin `974eaf1f…`
  (BENCHMARK_ROUTE_REFERENCE.json).
- Frozen worktree HEAD `22d56946…` and R7 stage hashes for
  `wp2_m3b_runner_smoke.py`, `harness_v3.py`, `opws_isolated_runtime_v1.py`,
  `runtime_image_compat_v1.py`.
- 3 frozen F2P nodes + the R7 `f2p_nodes_sha256` pin
  (`aa12d546…`), whose serialization is **not disclosed in the kit** — the
  adapter enforces the node list by exact matching and records the pin as
  externally verified.
- 3 F2P nodes × 3 invocations = **9 JUnit receipts per arm-run**, 1 task, and
  `scientific_independent_repetitions = FALSE` (no pseudo-replication).

## Identity convention (documented, don't conflate with the matrix label)

The M01D CSV `four_field_class` column is a **class label, not an identifier**.
This adapter defines its own deterministic four-field identity:

`four_field_id = sha256(scope_hash | patch_sha256 | patch_bytes | test_contract_hash)`

gives 12 classes for 13 arms, with the alias pair
`AGENTLESS_STYLE_ADAPTATION` / `BM25_K3` sharing one class → **two physical
executions** under Option B. The prior readiness ledger's `identity_*` hash
columns used an undisclosed serialization and are **not** reproduced here.

## Known integration gap (why `run` exits 5)

| Stage | Frozen ingredient | 13-arm orchestration |
| --- | --- | --- |
| Materialize reference patch | `opws_phase3b_patch_materialize.py` (git, read-only, `--dry-run`) | MISSING driver |
| F2P execute (3 nodes × 3) | `harness_v3.run_state_v3` via `wp2_m3b_runner_smoke.py` (single-node smoke) | MISSING multi-node per-arm driver |
| P2P execute | `wp2_p2p_u_v2_exec.py --task <TID> --cap 200\|400` | EXISTS (budget-gated) |
| Receipts/isolation | per-arm JUnit + Option B run dirs | adapter provides manifest/receipt checking |

Per-arm scope **path lists** for 11 non-R7 arms are not in the kit; the
adapter therefore marks materialize inputs `UNRESOLVED` until the frozen
prediction sources are re-pinned before any authorized M02 execution.

## Honesty limits

- Historical R7/R8 receipts classify correctly (27/27) with this adapter, but
  that **never** makes them prospective evidence; controls always require
  fresh M02-E runs.
- No invented flags: every planned command uses a flag verified by source
  inspection in M01D.
- No leakage path: selector inputs are frozen scope/classification JSON only;
  JUnit receipts are outcome evidence produced after scope selection.
