# C6_P2_ENV_QUALIFICATION.md — TRACK02-C6-P2-ENV-UNBLOCK (mission report)

UTC: 2026-10-27 08:30Z–11:30Z approx · Workspace:
`D:\WP2\active\TRACK02_C6_IMPLEMENT_20261027` · NEW Pi session, no C4/C5/90-test
re-runs, no old repairs, zero candidate executions.

## Frozen state re-verified (unchanged)
- 22,699 commits (D0_COMMITS count + ledger rows), **174** frozen candidates
  (C4_PASS ∩ TEST_CHANGE), all **6 frozen hashes byte-identical** (F1–F6,
  incl. ledger `67C47930…`), runner **v0.4.0**, real C6 candidate executions
  **0**, P2 T/P commits present in the frozen bare store.
- P2: `T=06d25ce2…5e83`, `P=5b0e5206…8a85`, `runtime.txt=python-3.9.14`
  (verified at P and T), contract `saleor/graphql/product/tests/test_product.py`
  (P-available; no T-only), T–P diff = `filters.py` + `test_product.py` only.

## Verdict
**P2_ENV_QUALIFIED — execution gated on ONE operator decision.**
- The historical P2 runtime (Python closure + era pins + PostgreSQL) is
  **provisioned and proven offline**; the immutable task image digest is
  frozen.
- The FIRST REAL PILOT **cannot start under runner v0.4.0** because the runner
  has no database-service or env-injection capability and the P2 contract is
  DB-backed. That capability gap is the **single next decision**:
  ratify the minimal, scoped runner delta v0.4.0 → v0.5.0
  (`C6_P2_RUNNER_DELTA_PROPOSAL.md`); approve → first real pilot next step;
  reject → `STOP` blocker `runner_db_service_capability_absent`.
- This is NOT a historical mismatch: the era environment genuinely required a
  Postgres service; the offline mechanism (alpine sidecar + unix socket on a
  shared named volume, both `--network none`) is **experimentally proven**.

## Atomic task results
| # | Task | Result | Evidence |
|---|---|---|---|
| 1 | Images/wheelhouse/manifests inventory | **PASS** | base `sha256:3220486db0…b89` (Debian 12, py 3.9.25, pip 23.0.1, gcc+pg_config, NO pg server, apt cache empty); `wheelhouse/py39` 2,533 wheels; reqs@P 170 pins (150 exact, 16 sdist, 3 patch, 1 win32-only); poetry.lock=240 pkgs; all closure wheels present |
| 2 | Python 3.9.25 vs declared 3.9.14 | **RESOLVED (evidence)** | CPython 3.9 bugfix line; `cp39`/`py3` wheels are patch-agnostic; full contract closure + `django.setup()` + ORM PASS on 3.9.25; exact identity NOT claimed; plan freezes concrete 3.9.25 (`C6_P2_PYTHON_COMPAT.md`) |
| 3 | Reproducible pinned historical image | **PASS** | `envcanon/saleor-c6-p2-py39-era:r3` = **`sha256:4b41010cadabc8e5b9d09c1207f32ebbc59dbad72662e01c91f415f6a4ee6919`**; 237 packages baked 100% offline (django 4.0.8, graphene 2.1.9, pytest 7.1.3, pytest-django 4.5.2, psycopg2 **exact 2.9.4** cp39 wheel, promise 2.3, before-after 1.0.1, petl 1.7.11-compatible-build); Dockerfile(r3) + hash-pinned `offwh/` subset; failure ledgers recorded (lint tooling only) |
| 4 | PostgreSQL under `--network none` | **RESOLVED** | Same-container: **not feasible offline** (no Debian pg binaries, empty apt cache, no store artifacts, alpine musl vs glibc wheels). **Proven alternative**: `postgres:15-alpine` (digest `sha256:9b4593c6…`) sidecar + named volume + unix socket; both containers `--network none`; psycopg2 + `dj_database_url` (`DATABASE_URL=…?host=/pg-sock`) connect **PASS**; loopback works under `--network none` (finding); drvfs cannot carry sockets — named volume does |
| 5 | Non-candidate env probes | **PASS** | network BLOCKED (OSError), rootfs read-only (errno 30), memory cap rc=137, pids cap enforced, scratch writable, closure+integration PASS, cleanup orphans 0 (`T5_PROBES_RECEIPT.json`) |
| 6 | P2 TaskPlan + SHA256 binding | **PASS** | `plans/P2.json` (c6-task-plan-v1, schema-valid) → canonical **`382E9280998B3B18BEED9B2FB95320CE9125C0DD4C7B830F6DD0FA4E91B53C88`** via the runner CLI; resources/limits frozen; v2 example with env+postgres drafted |
| 7 | PowerShell 7 operator commands | **PASS** | `P2_OPERATOR_FREEZE_AND_EXEC.ps1` (phases 0–3; PS-syntax verified): freeze protocol+images, author+sign authorization, preflight v0.4.0, post-delta pilot |

## Exact frozen identities
| Item | Value |
|---|---|
| Task image | `envcanon/saleor-c6-p2-py39-era:r3` → `sha256:4b41010cadabc8e5b9d09c1207f32ebbc59dbad72662e01c91f415f6a4ee6919` |
| Base image | `sha256:3220486db0d8f7649b29bfe01875a1ef794c860539e2713587d9d32f5bd91b89` (interpreter 3.9.25 probed) |
| DB service image | `postgres:15-alpine` → `sha256:9b4593c6de443299b46098151fc1ec154c882339b77a56334c7ce612c8a7be6a` (PostgreSQL 15.18) |
| Plan canon sha | `382E9280998B3B18BEED9B2FB95320CE9125C0DD4C7B830F6DD0FA4E91B53C88` |
| Wheelhouse identity (era py39 dir) | `707542BF660FEC149390367B54606D30BB10A237BD2BD808B8E3CA30160184BB` |
| Offline subset `offwh/` | 243 files, SHA256SUMS.txt inside; identity `7F9E9404…D5E` |
| Plan resources | timeout_s 1800 / ram_mb 16384 / disk_mb 5120 / scratch_mb 5120 / global_floor_gb 20 / **network_bytes 0** / pids_limit 512 / cpu_quota 1.0 |

## What ran / did not run
RAN (non-candidate only): offline pin resolution; derived image builds r1→r2→r3
(offline pip, `--no-index`); base/derived/pg probes; django.setup + contract
module imports; ORM+Postgres integration probe; isolation/limits probes;
cleanup sweeps; plan-sha + isolation-check via the runner CLI; read-only
frozen-state verification.
DID NOT RUN: any candidate/pilot execution (0); C7/generated-code E2E (out of
scope); operator freeze/authorization signing (operator-owned artifacts);
runner modification; census/eligibility changes; any downloads/pulls of Python
packages; the 90-test suite and old repairs (mission rule).

## Accounting (honest)
| Item | Value |
|---|---|
| Active wall time | ≈ 3.0 h (08:30Z–11:30Z) |
| New artifacts on disk | ≈ 135 MB (build subset 127 MB + outputs) — includes the 3 derived images in Docker (≈4.3 GB combined, local) |
| Free disk after | 366 GiB free (budget floor 20 GiB ≫) |
| Network | **NOT 0 this mission — reported honestly**: (1) `docker build` bootstrap pulled `moby/buildkit:buildx-stable-1` once (build engine driver); (2) one build attempt with a digest-form FROM triggered a `docker.io` metadata resolution that FAILED access-denied (no image bytes transferred); (3) an alpine image already local was reused (no pull). `pip` made **zero** network calls (`--no-index`); probes used `--network none`; no PyPI/GitHub/HTTP API activity; no model/paid API calls (0 USD). First build attempt also triggered 2 registry auth tokens (0-byte transfers). All subsequent builds reused the local engine. |
| Docker events | builds r1(≈16 min)/r2(≈16 min)/r3(<1 min); ~12 disposable probe containers, all removed; 0 orphans at end (`c6.*/label c6.task` = 0); 1 named volume created+removed |
| API cost | 0 |
| Candidate executions | 0 |
| Frozen inputs | 0 mutations (hashes byte-identical) |

## Single next operator decision
1. **Approve** `C6_FINAL_PROTOCOL_V4_ORACLE.md` (unchanged) and **ratify the
   runner delta v0.4.0→v0.5.0** scoped in `C6_P2_RUNNER_DELTA_PROPOSAL.md`
   (plan fields `env`+`postgres`, docker service orchestration, new tests, one
   suite re-run as delta-integrity evidence; no scientific-semantics change).
2. Then run: `pwsh -ExecutionPolicy Bypass -File P2_OPERATOR_FREEZE_AND_EXEC.ps1
   -Phase 1` (freeze+authorize) → `-Phase 2` (preflight) → author
   `plans\P2_v050.json` (from the example) → re-sign binding → `-Phase 3
   -Authorized YES` → **FIRST REAL C6 PILOT**.
3. If the delta is rejected → STOP blocker
   `runner_db_service_capability_absent` (fail-closed; the pilot cannot
   connect its mandated PostgreSQL under v0.4.0).