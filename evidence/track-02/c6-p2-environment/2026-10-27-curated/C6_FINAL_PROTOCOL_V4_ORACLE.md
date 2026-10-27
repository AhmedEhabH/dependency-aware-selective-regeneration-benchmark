# C6_FINAL_PROTOCOL_V4_ORACLE.md — Track02 WP-B C6 Execution Protocol v0.4.0 (2026-10-27)

> **STATUS: PILOT_AUTHORIZATION_READY — NOT FROZEN, NOT AUTHORIZED.**
> Supersedes `C6_FINAL_PROTOCOL.md` (v0.3.0, preserved as history) for execution
> semantics. This version incorporates the FINAL ORACLE CORRECTIONS mission:
> (I1) an all-skipped / all-xfail / all-xpass / zero-execution junit report can
> NEVER produce a C6 PASS — a valid oracle requires >=1 genuinely executed,
> non-skipped test; (I2) the FOUR separate evaluation roles (P/P diagnostic,
> F2P negative baseline, P2P positive reference, generated-code E2E) are
> enforced by the runner, an expected F2P failure is recorded as the negative
> baseline outcome (never a broken environment), and T code / T tests /
> reference patch / evaluation answers never leak into the prospective input.
> Regression-tested: **90/90** (`work/phase4_full_suite_corrections.log`).
> C6 has NOT been executed; C7 has NOT been started; 0 candidate executions.

## 1. Scope (unchanged frozen population)

- Exactly **174** candidates: `C4 == "C4_PASS"` ∩ `C5 == "TEST_CHANGE"` from
  the V2 ledger (read-only re-verified 2026-10-27: 174/174, all C4_PASS /
  TEST_CHANGE / SINGLE_PARENT, years 2018–2026; ledger hash `67C47930…`
  byte-identical). No eligibility change, no re-census, no cohort expansion.
- C6 evaluates each candidate's changed-test evidence as a *runnable,
  reproducible test execution in an isolated historical environment*. C7
  (generated-code E2E) remains a distinct later gate.

## 2. THE FOUR EVALUATION ROLES (issue 2 — core correction)

| Role | Tree content | Purpose | Verdict contribution | Never |
|---|---|---|---|---|
| **P/P diagnostic** | P code + P tests | starting-environment diagnostic | evidence only; **never PASS** (runner mode `NONE` and the input run are BLOCKED for PASS purposes) | never receives T code, T tests, patch, oracle answers |
| **F2P negative baseline** | P code + T test bytes (eval-only tree `eval_f2p`) | negative control — the new/updated tests must FAIL against the unfixed P code | recorded as `negative_baseline_f2p.outcome`: `expected_failure` | an expected F2P failure is NEVER BLOCKED/"broken environment"; T bytes never enter `src/` |
| **P2P positive reference** | T code + T test bytes (eval-only tree `eval_work`) | positive control — the candidate's own code + tests must genuinely run GREEN | **the candidate verdict basis** (`POSITIVE_REFERENCE`) | never mixed into `src/`; never visible to a selector/generator |
| **Generated code + evaluation tests** | — | separate future E2E gate | NOT implemented (plan/receipt record `generated_code_e2e: not implemented`) | not part of any C6 receipt conclusion |

- Each task executes THREE command runs: (1) the diagnostic input run in the P
  tree (P-available subset of the contract), (2) the F2P baseline, (3) the P2P
  reference — each in a SEPARATE directory and SEPARATE container/process.
- Verdict rules (fail-closed):
  - Infra failure (timeout / resource overflow / vacuous oracle / blocked) of
    ANY of the three runs → **BLOCKED**, never PASS/FAIL for that cause.
  - `POSITIVE_REFERENCE` (C6 default): PASS iff the P2P report is valid (I1:
    >=1 genuinely executed non-skipped test), failures==errors==0 and exit 0;
    executed semantic failure → FAIL. The F2P run must ALSO be valid (either
    control unestablished → BLOCKED) and its outcome is recorded.
  - `NEG_TESTS_EXPECTED_FAIL`: PASS iff the F2P run is valid with semantic
    failures and exit != 0 (the negative baseline failed as expected); an
    unexpectedly green F2P run → FAIL.
  - `NONE`: diagnostic-only, always BLOCKED (no reference contract ⇒ no PASS).
- I1 oracle degeneracies (real pytest 8.3.4 junit encoding):
  - `pytest.skip` and `pytest.xfail` both render as `<skipped>` testcases →
    NOT genuinely executed; xfail tracked explicitly (`xfailed`).
  - XPASS renders as plain passed testcases → `xpassed` is taken from the
    same-process terminal summary; an all-xpass report is vacuous
    (`only_xpass`), never PASS.
  - Zero-execution (`tests=0`, e.g. pytest exit 5) → vacuous `no_tests` → BLOCKED.

## 3. Oracle evidence (finding F3 + issue 1)

- A valid behavioral oracle exists ONLY when the executed pytest process writes
  a **junit-xml report inside the sandbox** (`--junitxml` injected by the
  runner at the frozen plan's `junitxml_path`).
- Validity requires ALL of: file exists ∧ well-formed ∧ **>=1 genuinely
  executed, non-skipped testcase** ∧ at least one of those is NOT an XPASS ∧
  every testcase traces to the frozen M/A contract ∧ junit counts ==
  same-process pytest terminal summary ∧ (failures+errors==0) ⟺ (exit==0).
- Explicit counters accompany every report: `tests`, `executed`, `skipped`,
  `xfailed`, `xpassed`, `failures`, `errors`, `reason`
  (`all_skipped` / `only_xfail` / `only_xpass` / `no_tests` / `okay`).
- `assertions_ok` derives from the junit report only, never defaulted True.
- Forged stdout (`pretend result: 1 passed`), truncated / zero-test / skipped-
  only / xfail-only / xpass-only reports → vacuous → BLOCKED, never PASS.

## 4. Runtime identity and drift (unchanged finding F4)

- `ENVIRONMENT_ID` = versioned formula over manifest snapshot at P +
  resolved interpreter@version + wheelhouse identity + immutable image digest.
- Every docker task plan freezes `image_digest`; the runner resolves
  `plan.image` locally (offline `docker image inspect`, never pulls) and
  requires equality; mutable tags are NEVER runtime identity; containers
  launch by the immutable digest; interpreter probed INSIDE the pinned image.
  Drift → GLOBAL STOP ENV_DRIFT; unresolvable → BLOCKED.
- C6 runs are OS-isolated: docker `--network none`, memory/pids/cpu caps,
  read-only rootfs and P mount, scratch tmpfs + bounded delta. The
  sitecustomize gate is defense-in-depth only (`python_gate_active`).

## 5. Container lifecycle and cleanup (unchanged finding F5 — proven)

- Every container starts with `--cidfile <scratch>/container.cid` and
  `--label c6.task=<task12>`; on timeout the runner kills/wait/rm -f the
  container id (fallback: label query), then sweeps remnants. Receipt proves
  `orphans_detected == 0` and `orphans_remaining == 0`. Real docker probe
  (2026-10-27): PASS 0/0/0. Timeout → BLOCKED(timeout).

## 6. Input binding (unchanged finding F6) and T isolation

- The CLI runs only with a `c6-frozen-inputs-v2` manifest declaring `roles`
  binding git store / ledger / H2 events / protected cache / manifest itself;
  substitution → C6_STOP INPUT_BINDING_MISMATCH before any input is trusted.
- T-only test bytes are quarantined under `oracle/` (never `src/`); the
  reference trees exist only under `eval_f2p` (F2P) and `eval_work` (P2P);
  the T CODE bytes exist only in the P2P tree. T tests, the reference patch
  and evaluation answers never become selector/generator-visible inputs
  (verified by `test_red_t_bytes_never_prospective_input` and the existing
  quarantine/isolation suite).

## 7. Frozen input identities (unchanged; byte re-verified 2026-10-27)

| # | Path | SHA-256 |
|---|---|---|
| F1 | `D0_COMMITS.jsonl` | `8CC43BFA92BBA71D5616E4E0236B746DC17C5E9FE739F97F725FD5B9F8E8D62E` |
| F2 | `D0_FILE_EVENTS.jsonl` | `6F3722DCD86E9BE6FDA7AD6735BF4B53E50C6E86BE72D33FD6F52D6FEE5F9FB0` |
| F3 | `D0_GRAPH_TOPO_DESC.txt` | `BF589410FF5FE537114392C16DDAFF4D30844EB8110DDD0A50ECE7DB4C052614` |
| F4 | `PROOF_AUDIT_174.csv` | `711B3039D56182B9104D74D0E82E1E96F9F9F7D6DF760E549AEFFC2FFEECBC14` |
| F5 | `C1_C5_PER_SHA.jsonl` | `67C4793060FC9A7E73A5AF85C3BE67A975855B9DFCC57DAADE429AAA22308C19` |
| F6 | `RAW_API_MANIFEST.jsonl` | `4F9C15A695A3D218CE228C405D7CB263B5FE8A35A38F8EF50123AFE37B9060A6` |
| F7 | frozen bare store `saleor.git` | per-task OID verification |
| F8 | protected body cache | per-task byte verification vs ledger |

## 8. Verdicts and STOP gate (unchanged taxonomy)

- **PASS** — P2P positive reference valid per §2/§3 ≥1 genuinely executed
  non-skipped test (or, in NEG mode, the F2P baseline failed as expected).
- **FAIL** — executed semantic failure under a valid reference (valid outcome).
- **BLOCKED** — vacuous/forged/all-skipped/all-xfail/all-xpass/no-report,
  no_os_isolation, image not pinned, interpreter probe failure, timeout,
  overflow, R1–R3 fail, reference evaluator error, NONE mode.
- **GLOBAL STOP** — NOT_AUTHORIZED, PLAN_UNBOUND/MISMATCHED, FROZEN_INPUT_DRIFT,
  LEAKAGE_DETECTED, ENV_DRIFT, INPUT_BINDING_MISMATCH, BUDGET_EXCEEDED,
  orphaned containers after forced cleanup, COVERAGE_INCOMPLETE.

## 9. Pilot plan (unchanged SHAs; R3 re-verified 2026-10-27)

| Pilot | T (SHA-256) | Year | Old6000 | P-available | T-only | Interpreter required |
|---|---|---|---|---|---|---|
| P1 | `a28f79819aa261000a3352dcd5770ed1d1afa3fc` | 2018 | No | `tests/test_impersonation.py` | — | python-3.6.3 (runtime.txt) |
| P2 | `06d25ce29c984d9af0f8759044cd80aa8a835e83` | 2022 | Yes | `saleor/graphql/product/tests/test_product.py` | — | python-3.9.14 (runtime.txt) |
| P3 | `9235b0af3f8a223fd40c6d7e004eb8150c79f553` | 2024 | Yes | `saleor/product/tests/test_fetch_variants_for_promotion_rules.py` | `saleor/discount/tests/test_utils/test_update_rule_variant_relation.py` | python ~3.9 (pyproject) |

**Image resolution (offline, explicit):**
- P1: a python-3.6.x-era saleor image with pytest + era wheels is REQUIRED and
  NOT present on this host → operator must provision and freeze its digest.
- P2/P3: base `sha256:3220486db0d8f7649b29bfe01875a1ef794c860539e2713587d9d32f5bd91b89`
  (`envcanon/saleor-env-r4b-py39-native:latest`, python-3.9.25) IS present
  locally but lacks pytest/django → operator must freeze a derived image with
  the OFFLINE era wheelhouse per `C6_P2_FEASIBILITY_OFFLINE.md` (170 pins:
  150 exact-version wheels present, the test-relevant import closure fully
  covered; psycopg2 via `psycopg2_binary` cp39 wheels) + a reachable Postgres
  service for DB-backed tests. No image family is silently reused.

## 10. Operator freeze + authorization procedure (execute in this order)

1. Accept this document; freeze:
   ```powershell
   Get-FileHash -Algorithm SHA256 -LiteralPath C6_FINAL_PROTOCOL_V4_ORACLE.md
   ```
   Record `{protocol_sha256, utc, operator, protocol_document_path}` in
   `C6_PROTOCOL_FREEZE.json`.
2. Provision + freeze the pilot images (per §9) — record each immutable digest.
3. Author per-task plans per `C6_TASK_PLAN.schema.json` (command enumerates the
   contract; `oracle_mode: "POSITIVE_REFERENCE"`, `image_digest`,
   `interpreter[_version]`, `junitxml_path`, resources). Bind:
   ```powershell
   & $py -m c6runner.cli --plan-sha plans\P1.json   # prints plan_sha256
   ```
4. Issue `C6_AUTHORIZATION_RECEIPT.json` (write-then-hash) with
   `task_bindings`; `authorization_sha256` over the doc without the self-field.
5. Preflight, then run serially (PowerShell 7; `OPERATOR_COMMANDS.md`):
   ```powershell
   & $py -m c6runner.cli --freeze <FREEZE> --authorization <AUTH> --plan plans\P1.json --preflight
   & $py -m c6runner.cli --freeze <FREEZE> --authorization <AUTH> --plan plans\P1.json --out-dir runs
   ```
6. Review the three receipts: P2P `oracle_report.ran >= 1` (genuine executed
   non-skipped), `negative_baseline_f2p.outcome` (`expected_failure` or
   `unexpected_green` — NEVER a broken-environment classification), environment
   binding + cleanup evidence. C7 / generated-code E2E remain distinct gates.

## 11. Accounting (this mission)

- ~45 min wall of active work (08:02Z→08:45Z). Full suite once: 90/90 (126 s). RED-vs-v0.3.0 check: 14 failed / 15 passed (75 s).
- Outputs ≈ 1.5 MB new artifacts (excl. preserved v0.3.0 snapshot 238 KB).
- Network: **0 bytes** (no pulls; all probes offline on cached images; 1
  disposable interpreter probe, `--network none`).
- API cost: **0**. Candidate executions: **0**. Frozen-input mutations: **0**
  (all hashes byte-identical).