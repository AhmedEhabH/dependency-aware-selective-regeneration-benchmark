# C6_FINAL_PROTOCOL.md — Track02 WP-B C6 Execution Protocol v0.3.0 (2026-10-27)

> **STATUS: PILOT_AUTHORIZATION_READY — NOT FROZEN, NOT AUTHORIZED.**
> Supersedes `C6_PROTOCOL_FREEZE_READY_V2.md` for execution semantics (the V2
> file is preserved as history). This version incorporates the seven
> independently confirmed execution-blockers (F1–F7): the reference
> evaluation, machine-readable oracle evidence, runtime identity binding,
> deterministic container cleanup, input binding and C6/reference/C7
> separation are now explicit protocol requirements with regression tests
> (74/74). Executing any candidate STILL requires the operator freeze of these
> bytes + a separate authorization receipt with per-task plan bindings.
> **C6 has not been executed; C7 has not been started; 0 candidate executions.**

## 1. Scope (unchanged frozen population)

- Exactly **174** candidates: `C4 == "C4_PASS"` ∩ `C5 == "TEST_CHANGE"` from the
  V2 ledger (read-only re-verified 2026-10-27: 174/174, all C4_PASS /
  TEST_CHANGE / SINGLE_PARENT, years 2018–2026; ledger hash `67C47930…`
  byte-identical). No eligibility change, no re-census, no cohort expansion.
- C6 evaluates each candidate's changed-test evidence as a *runnable,
  reproducible test execution in an isolated historical environment*. C7
  (generated-code E2E) remains a distinct later gate.

## 2. Semantics of P, T/reference, T-only (finding F7 — THE core correction)

| Tree | Content | Purpose | Never |
|---|---|---|---|
| **P** (prospective input) | pre-change bytes; mounted read-only | the input the candidate "saw" | never receives T code, T tests, or oracle answers |
| **T/reference** (evaluation-only) | P source bytes + T test bytes of the FULL M/A contract overlaid at repo-relative paths | the scientific oracle (test contract AS OF T) | never mixed into P; never visible to a prospective selector/generator |
| **T-only tests** | quarantine bytes under `oracle/` (repo-relative) | reference-evaluation-only evidence | never into `src/`, never mounted into a task container |

- The task **input run** executes the P-available subset of the contract in the
  P tree. A green input run ALONE never yields PASS (finding F2/F7).
- The **verdict comes from the reference evaluation**: the frozen test command
  runs in a SEPARATE evaluator (own directory, own container) against the
  reference tree, exercising the FULL M/A contract.
  - `POSITIVE_REFERENCE`: PASS iff reference report valid ∧ failures==errors==0
    ∧ exit 0; executed semantic failure → FAIL.
  - `NEG_TESTS_EXPECTED_FAIL`: PASS iff report valid ∧ semantic failures ∧
    exit ≠ 0; unexpectedly green → FAIL.
  - Missing/errored/vacuous reference → **BLOCKED**, never PASS (finding F2).
- Receipts record `scope: "C6"`, `reference_definition`, the effective argv of
  both runs, and `oracle_evidence` so C6 environment/test qualification stays
  clearly separate from C7 and generated-code E2E.

## 3. Oracle evidence (finding F3 — machine-readable only)

- A valid behavioral oracle exists ONLY when the executed pytest process writes
  a **junit-xml report inside the sandbox** (`--junitxml` is injected by the
  runner at the frozen plan's `junitxml_path`, under the writable scratch bind).
- Validity requires ALL of: file exists ∧ well-formed ∧ ≥1 executed testcase ∧
  every testcase traces to the frozen M/A contract (source path identity) ∧
  junit counts == same-process pytest terminal summary ∧
  (failures+errors==0) ⟺ (exit==0).
- `assertions_ok` derives from the junit report only; it defaults to None
  (unverified) and is never defaulted True.
- Forged stdout (`pretend result: 1 passed`), truncated or zero-test reports,
  and report-less commands are **vacuous → BLOCKED**, never PASS.

## 4. Runtime identity and drift (finding F4)

- `ENVIRONMENT_ID` = versioned formula over manifest snapshot at P +
  **resolved interpreter@version** + **wheelhouse identity** + **immutable
  image digest**.
- Every docker task plan freezes `image_digest` (64-hex OCI sha256). The runner
  resolves `plan.image` locally (offline `docker image inspect`, never pulls)
  and requires equality — mutable tags (`:latest`) are NEVER the runtime
  identity; containers are launched by the immutable digest.
- The interpreter version is resolved INSIDE the pinned image (cached probe);
  a declared `interpreter_version`/`wheelhouse_id` that drifts → **GLOBAL STOP
  ENV_DRIFT**; an unresolvable image/interpreter → **BLOCKED** (infra).
- C6 runs are OS-isolated: docker `--network none`, `--memory/--memory-swap`
  caps, `--pids-limit`, `--cpus`, read-only rootfs, read-only P mount,
  scratch tmpfs + bounded scratch delta. The sitecustomize python gate remains
  defense-in-depth only, recorded as `python_gate_active` (never as OS
  enforcement).

## 5. Container lifecycle and cleanup (finding F5 — proven)

- Every container starts with `--cidfile <scratch>/container.cid` and
  `--label c6.task=<task12>`.
- On timeout the runner kills/wait/rm -f the **container id from the cidfile**
  (fallback: label query), then sweeps any remaining container carrying the
  task label. Proof requirement: `orphans_detected == 0` and
  `orphans_remaining == 0` in the receipt. Real probe 2026-10-27: PASS
  (0/0/0 before, after, after-settle).
- Timeout → BLOCKED(timeout); rc 137 → BLOCKED(container_killed/resource).

## 6. Input binding (finding F6)

- The CLI executes only with a `c6-frozen-inputs-v2` manifest declaring
  `roles`: `git_store`, `ledger`, `h2_events`, `protected_cache`,
  `frozen_manifest`. Every supplied source must equal its frozen role path
  (normalized absolute); substitution → **C6_STOP INPUT_BINDING_MISMATCH**
  before any input is trusted; `inputs_verified=True` in a receipt always means
  the bound paths were verified.
- Frozen input sha-256 re-verification runs before every task (F1–F8 in
  §7); any drift → GLOBAL STOP.

## 7. Frozen input identities (unchanged; re-verified this session)

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

- **PASS** — reference oracle valid per §2/§3 (never from P tests alone).
- **FAIL** — executed semantic failure under a valid reference (valid outcome).
- **BLOCKED** — vacuous/forged/no-report, no_os_isolation, image not pinned,
  interpreter probe failure, timeout, overflow, R1–R3 fail, reference
  evaluator error.
- **GLOBAL STOP** — NOT_AUTHORIZED, PLAN_UNBOUND/MISMATCHED, FROZEN_INPUT_DRIFT
  (F1–F8), LEAKAGE_DETECTED, ENV_DRIFT, INPUT_BINDING_MISMATCH,
  BUDGET_EXCEEDED (floor checked immediately before every task), orphaned
  containers after forced cleanup, COVERAGE_INCOMPLETE.

## 9. Pilot plan (freeze these task SHAs; R3 re-verified 2026-10-27)

| Pilot | T (SHA-256) | Year | Old6000 | P-available | T-only | Interpreter required |
|---|---|---|---|---|---|---|
| P1 | `a28f79819aa261000a3352dcd5770ed1d1afa3fc` | 2018 | No | `tests/test_impersonation.py` | — | python-3.6.3 (runtime.txt) |
| P2 | `06d25ce29c984d9af0f8759044cd80aa8a835e83` | 2022 | Yes | `saleor/graphql/product/tests/test_product.py` | — | python-3.9.14 (runtime.txt) |
| P3 | `9235b0af3f8a223fd40c6d7e004eb8150c79f553` | 2024 | Yes | `saleor/product/tests/test_fetch_variants_for_promotion_rules.py` | `saleor/discount/tests/test_utils/test_update_rule_variant_relation.py` | python ~3.9 (pyproject) |

**Historical image resolution (explicit, no silent Track01 reuse):**
- P1: a python-3.6.x-era saleor image with pytest + era wheels is REQUIRED and
  is **NOT present** on this host → operator must provision and freeze its
  digest before P1 preflight (otherwise BLOCKED `docker_image_not_pinned`).
- P2/P3: immutable base `sha256:3220486db0d8f7649b29bfe01875a1ef794c860539e2713587d9d32f5bd91b89`
  (python3.9.25, created 2026-10-10, probe-only base) matches the ~3.9 family
  but **lacks pytest/django** → operator must freeze a derived image id with
  pytest + era dependencies provisioned (offline wheelhouse), then pin that
  digest. Any other image family (e.g. an unrelated Track01 image) is
  rejected by `image_digest` binding — never silently reused.

## 10. Operator freeze + authorization procedure (execute in this order)

1. Accept this document; compute the freeze:
   ```powershell
   Get-FileHash -Algorithm SHA256 -LiteralPath C6_FINAL_PROTOCOL.md
   ```
   Record `{protocol_sha256, utc, operator, protocol_document_path}` in
   `C6_PROTOCOL_FREEZE.json`.
2. Provision + freeze the pilot images (per §9) — record each immutable digest.
3. Author per-task plan files per `C6_TASK_PLAN.schema.json` (command enumerates
   the contract; `image_digest`, `interpreter[_version]`, `junitxml_path`,
   resources). Compute the binding values:
   ```powershell
   & $py -m c6runner.cli --plan-sha plans\P1.json   # prints plan_sha256
   ```
4. Issue `C6_AUTHORIZATION_RECEIPT.json` (write-then-hash): scope
   `["TASK:<sha>", …]`, `task_bindings: {task: {plan_sha256: …}}`,
   `authorization_sha256` over the document without the self-field.
5. Preflight, then run serially (PowerShell 7; full commands in
   `OPERATOR_COMMANDS.md`):
   ```powershell
   & $py -m c6runner.cli --freeze <FREEZE> --authorization <AUTH> --plan plans\P1.json --preflight
   & $py -m c6runner.cli --freeze <FREEZE> --authorization <AUTH> --plan plans\P1.json --out-dir runs
   ```
6. Review the three receipts (junit evidence, cleanup evidence, env binding)
   before any larger batch. C7 remains a distinct later gate.

## 11. Accounting (this session)

- ~60 min wall of active work; outputs ≈ 8 MB; **0 network bytes** (no pulls;
  probes ran `--network none` on the cached image); **0 API cost**; 1+1
  disposable probe containers; 0 candidate executions; 0 frozen-input
  mutations (all hashes byte-identical).