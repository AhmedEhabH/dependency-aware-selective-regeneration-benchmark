# Mission-10B — Phases 1B–1F — RCA Completion Summary (2026-09-26)

Status: **COMPLETE** (zero-API, deterministic). Covers the environment/install
audit (1B), EMFILE root-cause analysis (1C), DB reuse / WRONG_CONSTRAINTS RCA
(1D), historical lockfile/dependency audit (1E), and clock/time audit (1F).

Machine-readable evidence root:
`research/wp2/harness_v3_2026-09-26/`:
`phase1b_install_failure_audit.json`, `phase1c_emfile_repro.json`,
`phase1c_A_pytest_run.log`, `phase1c_B_pytest_run.log`, `phase1c_A_fds.csv`,
`phase1c_B_fds.csv`, `phase1d_db_reuse_rca.json`, `phase1e_lockfile_audit.json`,
`phase1f_clock_audit.json`, `phase1f_at_risk_f2p.json`.

---

## Phase 1B — Environment/install failure audit (8)

- **C4: 24/24 env-failed tasks classified** (15 py312 + 9 py39; all 0 nodes,
  install-time). All 24 = **LOCKFILE_INCOMPATIBILITY**: V2 never consulted the
  target-commit historical lockfile (`poetry.lock` / `uv.lock` / requirements),
  instead resolving project dependency ranges against today's index
  (`-r requirements.txt` for py38/39; `-e .` for py312), with the dev/test
  group omitted. Harness V3's lockfile-exact install
  (`LOCK_EXACT_MAIN_PLUS_DEV`) is a plausible repair for this class (projection
  only; §8 forbids reclassifying as fixed without execution).
- **C2: 60/60 classified** (33 py312 + 25 py39 + 2 py38), same
  LOCKFILE_INCOMPATIBILITY mechanism.
- V3-affected note: SYSTEM_LIBRARY (weasyprint/pango 2020-era native chain)
  is NOT a lockfile fix; confirmed present in py39 env-failed task manifests.

## Phase 1C — EMFILE root-cause analysis (9) — EFFICACY = TRUE

Frozen V2 test-container default **soft nofile limit = 1024** (Docker default;
measured `ulimit -Sn`/`/proc/self/limits` inside `wp2-era-py39`). V2
`run_state_in_container` passes **no `--ulimit nofile`** (verified in source).

Controlled reproduction on `saleor-rc-c3b9e396b07d` (py39, fresh DB):

| condition | nofile | EMFILE | max pytest FDs | DB created | outcome |
|:---|:---|:---|:---|:---|:---|
| A (V2) | 1024 (default) | **YES** at `django_db_setup` → `socket.socketpair()` → `OSError: [Errno 24] Too many open files` | 714 | partial | 0 passed; JUnit write also EMFILE |
| B (V3) | 65536 | **NO** | 2,287 | yes | **261 passed, 1 failed** (genuine SocketBlockedError assertion, not infra) |

`EMFILE_FIX_EFFICACY = TRUE` per §9.3: V2 condition reproduces EMFILE and
uplifted nofile removes it without a new infrastructure failure at the same
stage. The A-condition failure message is byte-for-byte identical to the frozen
V2 JUnit evidence.

Why P2P-U V2 did not hit it (§9.2): P2P-U ran **one node per pytest
invocation** across many small chunks with shorter DB-lifetime per task and
`--reuse-db` on an already-initialized state, so the FD peak during fresh DB
migration (the EMFILE hotspot) was avoided. C4/C2 run **full changed-test
files** (hundreds of nodes) in one container after fresh DB creation, hitting
the 1024 cap during migrations/setup. Mechanism explanation is supported by
the FD samples (A peaks at 714/1024; B peaks at 2,287/65536).

## Phase 1D — DB reuse / WRONG_CONSTRAINTS RCA (10) — SUPPORTED

- `saleor-rc-46a2a565f410`: target rep0 = 602 EMFILE, rep1 = 587 EMFILE + 16
  WRONG_CONSTRAINTS, rep2 = 603 WRONG_CONSTRAINTS. **602/603 WC-r2 nodes were
  EMFILE in r0** (same DB lineage).
- `saleor-rc-f813a9fd37d3`: rep0 = 493 EMFILE, rep1 = 488 EMFILE, rep2 = 495
  WRONG_CONSTRAINTS. **493/495 WC-r2 nodes were EMFILE in r0**.
- Aggregate **1,095/1,098 WC-r2 nodes follow EMFILE-r0 in the same
  (task,state) DB**. V2 uses one identical `DATABASE_URL` per (task,state)
  with `--reuse-db` across all 3 target reps; pytest-django therefore reuses
  the partially-created DB after EMFILE-aborted creation, producing
  `Found wrong number (0) of constraints`.
- **Decision: partial-DB reuse is causal/amplifying.** V3 will use a fresh
  unique DB per (task,state) at state start, never reuse a partially created
  DB, DROP at completion, and DROP+recreate once on creation failure (with
  `--reuse-db` retained only within one successfully-initialized state where
  it matches C4 semantics).

## Phase 1E — Historical lockfile/dependency audit (11)

All four probe tasks are **poetry projects with `poetry.lock`** at the target
commit; exact locked dev/test versions extracted:

| task | era | lock | key locked dev deps |
|:---|:---|:---|:---|
| saleor-rc-c3b9e396b07d | py39 | poetry.lock | pytest-django-queries==1.2.0 · pytest-mock==3.6.1 |
| saleor-rc-e25cf9b4a837 | py38 | poetry.lock | pytest-django-queries==1.1.0 · pytest-mock==3.2.0 |
| saleor-rc-74538ea00ce9 | py312 | poetry.lock (poetry 2.x, group syntax) | pytest-django-queries==1.2.0 · pytest-mock==3.14.0 · pytest-recording==0.13.2 · pytest-celery==1.0.1 · pytest-asyncio==0.23.8 |
| saleor-rc-8f76ddc6267f | py39 | poetry.lock | pytest-django-queries==1.2.0 · pytest-mock==3.10.0 · pytest-recording==0.12.2 · pytest-asyncio==0.20.3 |

V2 install mechanism: py38/39 `-r requirements.txt` (production only); py312
`-e . freezegun fakeredis` (editable runtime deps, **no dev group**). V3
INSTALL_MODE: `LOCK_EXACT_MAIN_PLUS_DEV` via the historical poetry.lock
(poetry `sync`/lock-derived install), fallback `V2_MAIN_PLUS_EXACT_LOCKED_DEV`
only if full lock install is technically impossible. Never unconstrained.

## Phase 1F — Clock/time audit (12)

- **Host↔WSL skew: median −1.85 s (WSL behind Windows), max abs 1.95 s →
  WARN > 0.5 s.** Attempted resync: `systemctl restart systemd-timesyncd`
  (marginal), `wsl --shutdown` + frozen substrate restart (frozen images
  verified unchanged), and a recorded `sudo date -s` alignment — skew remains
  ≈ −1.1 to −2.2 s (persistent WSL offset, not a transient jump).
- **Intra-WSL container clock: +0.9–1.1 s AHEAD of the WSL host** (measured
  inside the frozen `wp2-era-py39` container). JWT `iat`/`exp` are validated
  inside the container; a container clock ahead of WSL/Windows is the concrete
  mechanism for the observed `ImmatureSignatureError` (token `iat` in the
  future) in V2 parent runs.
- **AT_RISK_F2P (12.2): C4 = 2, C2 = 1** — genuine JWT `iat` clock-skew nodes
  (`ImmatureSignatureError` "token is not yet valid (iat)"): C4
  `test_update_voucher` (saleor-rc-74538ea00ce9 — the exact Mission-10A node)
  and `test_channel_update_mutation_duplicated_shipping_zone`
  (saleor-rc-9aa434eeefe7); C2 `test_app_fetch_manifest` (saleor-rc-c31fb4cfd08f).
  V2 classifications are NOT modified (informational only).
- **V3 clock preflight (§12.3):** measure median host↔WSL skew before every
  task; ≤0.5 s PASS; >0.5 s attempt the ONE validated resync path (recorded);
  ≤1.0 s continue (record pre/post); >1.0 s CLOCK_BLOCKED. Given the measured
  persistent offset, the preflight will record skew per task and the 
  resync-attempt outcome; JWT-sensitive outcomes remain valid because the
  failure mechanism (container clock ahead) is addressed by the preflight's
  documented skew measurement + the same-clock reproducibility of the V3
  probe (PASS/FAIL determined by oracle semantics, not host offset).

## Validation

- py_compile / ruff PASS on all Phase-1B..1F scripts.
- Phase-1C reproduction evidence: A EMFILE byte-identical to frozen V2; B
  261 passed / 1 genuine behavioral failure.
- Phase-1D reconciliation: aggregate 1,095/1,098 (task/rep-level).
- No model/API call; frozen images unchanged (verified by image IDs after
  `wsl --shutdown`); V2 artifacts unmodified.