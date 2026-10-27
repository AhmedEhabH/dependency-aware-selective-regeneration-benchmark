# OPERATOR_COMMANDS.md — C6 FINAL pilot operator runbook (v0.4.0, PowerShell 7)

> Status: PILOT_AUTHORIZATION_READY — execution requires the operator freeze +
> authorization + per-task plan bindings. Nothing below executes candidates
> before step 4. The operative protocol document is
> `C6_FINAL_PROTOCOL_V4_ORACLE.md` (the v0.3.0 `C6_FINAL_PROTOCOL.md` is
> preserved as history).

## 0. Prerequisites (PowerShell 7 only)

```powershell
$py  = "C:\Users\Ahmed\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\python.exe"
$env:PYTHONPATH = (Get-Location).Path
Set-Location D:\WP2\active\TRACK02_C6_IMPLEMENT_20261027\c6_runner
# Sanity: report the runner version and isolation backends (read-only)
& $py -c "import c6runner; print(c6runner.RUNNER_VERSION)"
& $py -m c6runner.cli --isolation-check
```

## 1. Freeze the protocol

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath D:\WP2\active\TRACK02_C6_IMPLEMENT_20261027\C6_FINAL_PROTOCOL_V4_ORACLE.md
```
Record the digest in `C6_PROTOCOL_FREEZE.json`:
`{ "protocol_sha256": "<SAME-DIGEST>", "utc": "<ISO-8601>", "operator": "<YOU>",
   "protocol_document_path": "D:\\WP2\\active\\TRACK02_C6_IMPLEMENT_20261027\\C6_FINAL_PROTOCOL_V4_ORACLE.md" }`

## 2. Freeze the three pilot images (explicit, era-correct)

| Pilot | Required runtime | Action |
|---|---|---|
| P1 | python-3.6.x era saleor + pytest + era wheels | build/freeze a 3.6 image; record its sha256 id |
| P2 | python 3.9 (3.9.14 declared) | extend `sha256:3220486db0d8f7649b29bfe01875a1ef794c860539e2713587d9d32f5bd91b89` with pytest + era wheels; freeze the new id |
| P3 | python ~3.9 (pyproject) | same base action as P2; freeze the new id |

```powershell
docker image inspect <REF> --format "{{.Id}}"    # offline; the frozen image_digest
```

## 3. Author per-task plans and bind the hashes

Plans follow `C6_TASK_PLAN.schema.json` (command must enumerate the M/A
contract; `image_digest`, `interpreter*`, `junitxml_path`, resources frozen).
Compute each binding value:

```powershell
& $py -m c6runner.cli --plan-sha plans\P1.json
& $py -m c6runner.cli --plan-sha plans\P2.json
& $py -m c6runner.cli --plan-sha plans\P3.json
```

Author `C6_AUTHORIZATION_RECEIPT.json` (write-then-hash):
```json
{
  "utc": "<ISO-8601>", "operator": "<YOU>",
  "protocol_sha256": "<1>",
  "scope": ["TASK:a28f79819aa261000a3352dcd5770ed1d1afa3fc",
            "TASK:06d25ce29c984d9af0f8759044cd80aa8a835e83",
            "TASK:9235b0af3f8a223fd40c6d7e004eb8150c79f553"],
  "task_bindings": {
    "TASK-SHA-P1": {"plan_sha256": "<plan-sha P1>"},
    "TASK-SHA-P2": {"plan_sha256": "<plan-sha P2>"},
    "TASK-SHA-P3": {"plan_sha256": "<plan-sha P3>"}
  }
}
```
`authorization_sha256` = SHA-256 over the canonical document WITHOUT the
self-field (the runner recomputes identically). Keep the file in an audit
directory; the runner re-verifies the self-hash and protocol binding on every run.

## 4. Preflight all three (no candidate execution)

```powershell
& $py -m c6runner.cli --freeze C6_PROTOCOL_FREEZE.json --authorization C6_AUTHORIZATION_RECEIPT.json --plan plans\P1.json --preflight --out-dir runs
& $py -m c6runner.cli --freeze C6_PROTOCOL_FREEZE.json --authorization C6_AUTHORIZATION_RECEIPT.json --plan plans\P2.json --preflight --out-dir runs
& $py -m c6runner.cli --freeze C6_PROTOCOL_FREEZE.json --authorization C6_AUTHORIZATION_RECEIPT.json --plan plans\P3.json --preflight --out-dir runs
```

## 5. Execute the pilot serially (authorized only)

```powershell
& $py -m c6runner.cli --freeze C6_PROTOCOL_FREEZE.json --authorization C6_AUTHORIZATION_RECEIPT.json --plan plans\P1.json --out-dir runs
& $py -m c6runner.cli --freeze C6_PROTOCOL_FREEZE.json --authorization C6_AUTHORIZATION_RECEIPT.json --plan plans\P2.json --out-dir runs
& $py -m c6runner.cli --freeze C6_PROTOCOL_FREEZE.json --authorization C6_AUTHORIZATION_RECEIPT.json --plan plans\P3.json --out-dir runs
```
Each run prints `VERDICT: <PASS|FAIL|BLOCKED>` and the receipt path; receipts
carry the junit oracle evidence, environment identity, cleanup evidence and
BOTH reference-role blocks (`oracle_evaluation` = P2P positive reference,
`negative_baseline_f2p` = F2P negative baseline) plus the P/P diagnostic in
`reference_definition.roles`. Per-task execution budget is THREE command runs:
1 diagnostic (P code + P tests) + 2 evaluation-only references (F2P: P code +
T tests; P2P: T code + T tests). Verify each receipt's `.sha256` sidecar
before reviewing. Any `C6_STOP:` halts the batch — preserve receipts, report
the trigger, do not repair.

P2/P3 provisioned images MUST install the era wheelhouse (offline, see
`C6_P2_FEASIBILITY_OFFLINE.md`): django~3.2.x, graphene/graphene-django,
pytest~7.x, before_after==1.0.1, freezegun, prices, measurement, pytz,
graphql_relay, psycopg2_binary (cp39 wheels); a reachable Postgres service is
an additional operator provisioning item for DB-backed saleor tests (P2 uses
`transaction`/`Sum`/`FlatConcatSearchVector`).

## 6. Gate review before any larger batch

Review the 3 receipts (verdict + both reference-role evidence blocks +
`environment` + `cleanup`), confirm the expected F2P failure is recorded as
`negative_baseline_f2p.outcome == expected_failure` (never a broken
environment) and the P2P positive reference carries `ran >= 1` genuinely
executed non-skipped tests, then decide on batch scope. C7 and generated-code
E2E are distinct later gates.