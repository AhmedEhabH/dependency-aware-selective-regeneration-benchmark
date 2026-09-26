# MISSION-11 STOP: HARNESS_V3_DEV_DEPS_GAP

- **TOKEN:** `HARNESS_V3_DEV_DEPS_GAP`
- **DATE/STAMP:** 2026-09-27 / 0145 (Africa/Cairo)
- **STOP AT:** Mission-11 A4 addendum (zero-API dev-deps coverage audit)
- **RESUME FROM:** Mission-11 A5 (Evaluator sets + ENG_SMOKE_READY) — AFTER Ahmed
  decides on the proposed V3.1 dependency fix (authorize or reject).
- **NEXT STEP ID on resume:** A5.1

## What happened

1. **A1–A3 complete:** Mission-10B P2P-U V3 ENG executed to 32/32 units terminal
   (30 DONE + 2 UNDEFINED `9258154b8a0b` cap200/cap400). Every unit
   `verify_unit()` OK (evidence_sha256 + raw JUnit SHA-256). Summary + A4.2
   invariants PASS; D19 cap200-vs-first200(cap400) agreement >= 0.99 (no C07).
2. **A4 addendum audit (zero API) run** as required before A5 / ENG_SMOKE_READY:
   - Persisted: `research/wp2/harness_v3_2026-09-26/dev_deps_gap_audit.json`
   - Cause taxonomy of non-STABLE P2P-U V3 nodes (both caps, from persisted JUnit):
     MISSING_FIXTURE:count_queries **144**, MISSING_FIXTURE:mocker **20**,
     SOCKET_BLOCKED 132, ASSERTION_OR_TRUE_TEST_FAILURE 25,
     COLLECTION/SETUP_OTHER 3, OTHER 27, FLAKY 19.
   - **HARNESS_V3_DEP_POLICY_COMPLIANCE = FAIL** for **7 oracle-valid ENG tasks**:
     `22ec4dab0154`, `644f33094857`, `6abb53f3407b`, `823b899757ab`,
     `82c56bde0e34`, `93b20d78c011`, `e03ee76d2b89`.
     - These tasks' target-commit `poetry.lock` **declares**
       `pytest-django-queries` (1.1.0/1.2.0) and/or `pytest-mock`
       (3.1.1/3.3.1/3.6.1), verified by `git show <target>:poetry.lock` in the
       read-only Saleor cache.
     - The V3 install path `has_poetry and has_req` installs only the
       `requirements.txt` main pins and does NOT install the poetry.lock dev
       group; these tasks are outside `LOCKED_DEV_DEPS`, so the declared dev/test
       packages were **not installed** in the V3 container.
   - **P2P coverage loss confirmed:** the 164 MISSING_FIXTURE nodes are P2P-U
     candidates that classify `BOTH_FAIL` instead of `STABLE_P2P`. M10A probe
     proved recovery (18/18 count_queries nodes of `74538ea00ce9` -> P2P_ONLY);
     `74538ea00ce9` is in `LOCKED_DEV_DEPS` so V3 now installs it and shows **0**
     missing-fixture losses, corroborating the cause.
   - **VCR/socket:** SocketBlockedError nodes use `@pytest.mark.vcr`; pytest-recording
     is NOT historically declared for those tasks -> not a declared-but-missing gap.
   - **C4_DEP_GAP_IMPACT = INCONCLUSIVE:** `phase5_c4v3_<task>.json` persists
     per-node outcomes but not failure text; M10A `error_records.jsonl`
     attributed 234 count_queries + 12 mocker across ENG C4, M10A token was
     ENV_AUDIT_INCONCLUSIVE (SET B non-regression failed).
   - **Chunk-2 record correction:** the interrupted chunk-2 invocation used
     timeout=10,800,000 ms (3 h) and was tool-call aborted after ~23.4 minutes
     (NOT a 2-minute default timeout). Verified resume preserved the completed
     hash-valid unit and reran the incomplete unit from scratch.

## Why STOP

Per the Mission-11 addendum §6 A5 READINESS GATE: the audit found
**systematically historically-declared dev/test dependencies missing** from
7 oracle-valid ENG tasks, and those omissions **caused loss of P2P coverage**
(164 nodes lost from STABLE_P2P). Therefore `HARNESS_V3_DEV_DEPS_GAP` is emitted
and I STOP before A5 / ENG_SMOKE_READY / any paid Smoke call. No repair was
performed (addendum §7).

## Proposed minimal fix (NOT applied; awaiting Ahmed)

**Fix (infrastructure only, no scientific change):** extend the frozen
`LOCKED_DEV_DEPS` mechanism (or the `lock_install_script` poetry+requirements.txt
branch) so that the exact locked dev/test group from the target `poetry.lock` is
installed for every executed task. The audit already extracted the exact
historical pins from the target poetry.lock (e.g. `22ec4dab0154`:
pytest-django-queries==1.1.0, pytest-mock==3.1.1).

**Exact rerun scope if authorized:** the affected (task, cap) units =
`{22ec4dab0154, 644f33094857, 6abb53f3407b, 823b899757ab, 82c56bde0e34,
93b20d78c011, e03ee76d2b89} × {200, 400}` = up to 14 units (those whose
MISSING_FIXTURE losses occur), then re-derive preservation sets, re-run the
summary/agreement and this audit. Everything else (harness V3 flags, oracle
semantics, P2P-U rule/salt/caps, splits, workers=1) unchanged.

## Evidence paths

- P2P-U V3 unit results + raw JUnit: `research/wp2/harness_v3_2026-09-26/p2pu_v3_eng_*.json`
  and `research/wp2/harness_v3_2026-09-26/p2pu_v3_junit/`
- Progress: `research/wp2/harness_v3_2026-09-26/p2pu_v3_progress.json`
- Summary + invariants: `research/wp2/harness_v3_2026-09-26/p2pu_v3_eng_summary.json`
- **This audit:** `research/wp2/harness_v3_2026-09-26/dev_deps_gap_audit.json`
- M10A prior proof: `research/wp2/mission10a_env_audit_2026-09-26/`
- Chunk logs: `logs/m11_p2pu_chunk1..8.log`

## Paid state

No model/API call has been made in this run. Total paid spend = $0.00
(ceiling $5.50).