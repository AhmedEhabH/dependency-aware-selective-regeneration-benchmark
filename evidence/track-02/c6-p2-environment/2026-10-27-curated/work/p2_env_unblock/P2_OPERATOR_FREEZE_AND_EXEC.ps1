# P2_OPERATOR_FREEZE_AND_EXEC.ps1  — TRACK02 C6 P2 first-pilot operator runbook
# PowerShell 7 ONLY. 2026-10-27. Prepared by mission TRACK02-C6-P2-ENV-UNBLOCK.
# Usage:
#   pwsh -ExecutionPolicy Bypass -File P2_OPERATOR_FREEZE_AND_EXEC.ps1 -Phase 0
#        0 = read-only sanity (runner version, isolation, plan sha)
#        1 = freeze protocol + images, author+sign authorization (NO execution)
#        2 = preflight P2 with the CURRENT runner v0.4.0 (expected PASS
#            preflight; actual execution is BLOCKED without the DB service —
#            fail-closed, never PASS/FAIL)
#        3 = (AFTER the operator approves the v0.5.0 delta) execute the first
#            real P2 pilot with the DB service (authorized run)
# Safety: no candidate executes unless -Authorized 'YES' is passed for Phase 3.

param(
  [ValidateSet("0","1","2","3")][string]$Phase = "0",
  [string]$Authorized = "NO"
)

$ErrorActionPreference = "Stop"
$ws        = "D:\WP2\active\TRACK02_C6_IMPLEMENT_20261027"
$py        = "C:\Users\Ahmed\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\python.exe"
$env:PYTHONPATH = Join-Path $ws "c6_runner"
$protocol  = Join-Path $ws "C6_FINAL_PROTOCOL_V4_ORACLE.md"
$freezeF   = Join-Path $ws "C6_PROTOCOL_FREEZE.json"
$authF     = Join-Path $ws "C6_AUTHORIZATION_RECEIPT.json"
$planF     = Join-Path $ws "plans\P2.json"
$planVF    = Join-Path $ws "plans\P2_v050.json"   # post-delta plan (env+postgres fields)
$outDir    = "runs"
$T         = "06d25ce29c984d9af0f8759044cd80aa8a835e83"

# FROZEN (this mission): immutable local digests verified offline
$imgBase   = "envcanon/saleor-env-r4b-py39-native@sha256:3220486db0d8f7649b29bfe01875a1ef794c860539e2713587d9d32f5bd91b89"
$imgR3     = "envcanon/saleor-c6-p2-py39-era@sha256:4b41010cadabc8e5b9d09c1207f32ebbc59dbad72662e01c91f415f6a4ee6919"
$pgBase    = "postgres:15-alpine@sha256:9b4593c6de443299b46098151fc1ec154c882339b77a56334c7ce612c8a7be6a"
$planSha   = "382E9280998B3B18BEED9B2FB95320CE9125C0DD4C7B830F6DD0FA4E91B53C88"

function Check-Runner {
  Write-Host "[phase $Phase] runner:"
  & $py -c "import c6runner; print('RUNNER_VERSION =', c6runner.RUNNER_VERSION)" | Out-String | Write-Host
  & $py -m c6runner.cli --isolation-check | Out-String | Write-Host
  Write-Host "[plan] canonical sha recomputed by the runner:"
  & $py -m c6runner.cli --plan-sha $planF
  Write-Host "frozen binding expected: $planSha"
}

if ($Phase -eq "0") { Check-Runner; exit 0 }

# ---------------- Phase 1: freeze + authorize (operator artifacts) ---------
if ($Phase -eq "1") {
  Check-Runner
  $ph = (Get-FileHash -Algorithm SHA256 -LiteralPath $protocol).Hash.ToUpperInvariant()
  Write-Host "protocol sha256: $ph"
  $freezeUtc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
  @{
    protocol_sha256        = $ph
    utc                    = $freezeUtc
    operator               = $env:USERNAME
    protocol_document_path = $protocol.Replace('\','\\')
  } | ConvertTo-Json | Set-Content -Encoding utf8 $freezeF
  Write-Host "wrote $freezeF  (verify content, then run Phase 2)"

  # --- image digests (offline, immutable) ---
  docker image inspect envcanon/saleor-c6-p2-py39-era:r3   --format "r3 {{.Id}}"
  docker image inspect postgres:15-alpine                  --format "pg {{.Id}}"
  docker image inspect envcanon/saleor-env-r4b-py39-native:latest --format "base {{.Id}}"
  Write-Host "freeze images: record these ids; plan expects r3 = sha256:4b41010c…ee6919"

  # --- authorization receipt (write-then-hash, canonical self-hash) ---
  $op = $env:USERNAME
  $doc = [ordered]@{
    utc            = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    operator       = $op
    protocol_sha256= $ph
    scope          = @("TASK:$T")
    task_bindings  = @{ $T = @{ plan_sha256 = $planSha } }
    resource_caps  = @{
      timeout_s = 1800.0; ram_mb = 16384.0; disk_mb = 5120.0
      scratch_mb = 5120.0; global_floor_gb = 20.0; network_bytes = 0
      pids_limit = 512; cpu_quota = 1.0
    }
  }
  $tmp = Join-Path $env:TEMP "auth_noself.json"
  $doc | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 $tmp
  # canonical serialization MUST match c6runner.authorization: json.dumps(stripped, indent=1, sort_keys=True) + "\n"
  $sh = & $py -c @"
import json
d=json.load(open(r'$tmp',encoding='utf-8-sig'))
c=json.dumps(d,indent=1,sort_keys=True)+'\n'
import hashlib; print(hashlib.sha256(c.encode()).hexdigest().upper())
"@
  Write-Host "authorization self-hash (authorization_sha256): $sh"
  $doc2 = @{
    authorization_sha256 = $sh.Trim()
    utc            = $doc.utc
    operator       = $op
    protocol_sha256= $ph
    scope          = @("TASK:$T")
    task_bindings  = @{ $T = @{ plan_sha256 = $planSha } }
    resource_caps  = $doc.resource_caps
  }
  $doc2 | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 $authF
  Write-Host "wrote $authF — the runner re-verifies authorization_sha256 + protocol binding on every run."
  Write-Host "NEXT: Phase 2 (preflight, no execution)."
  exit 0
}

# ---------------- Phase 2: preflight with CURRENT runner v0.4.0 -------------
if ($Phase -eq "2") {
  & $py -m c6runner.cli --freeze $freezeF --authorization $authF --plan $planF --preflight --out-dir $outDir
  Write-Host "NOTE(v0.4.0): preflight validates inputs/eligibility/identity/env binding (expected PASS)."
  Write-Host "Actual EXECUTION on v0.4.0 is expected BLOCKED (no DB service) — fail-closed, never PASS/FAIL."
  exit 0
}

# ---------------- Phase 3: authorized first real P2 pilot (v0.5.0) ----------
if ($Phase -eq "3") {
  if ($Authorized -ne "YES") {
    Write-Host "REFUSED: pass -Authorized YES to execute candidates (operator decision only)."
    exit 3
  }
  Check-Runner
  if ((& $py -c "import c6runner; print(c6runner.RUNNER_VERSION)") -notmatch "0\.5\.0") {
    Write-Host "STOP: runner must be v0.5.0 (approved delta with postgres service + env injection), got:"
    & $py -c "import c6runner; print(c6runner.RUNNER_VERSION)"
    Write-Host "LAST_STEP: runner delta ratification"
    exit 3
  }
  Write-Host "STEPS BEFORE RUN (post-delta):"
  Write-Host "  1. author plans\P2_v050.json from plans\P2_v050.example.json"
  Write-Host "  2. & $py -m c6runner.cli --plan-sha plans\P2_v050.json   -> NEW plan_sha256"
  Write-Host "  3. re-sign C6_AUTHORIZATION_RECEIPT.json task_bindings with the new sha"
  & $py -m c6runner.cli --freeze $freezeF --authorization $authF --plan $planVF --out-dir $outDir
  Write-Host "Verify receipt: oracle_report.ran>=1 (P2P), negative_baseline_f2p.outcome,"
  Write-Host "environment.image_ref == sha256:4b41010c…ee6919, postgres_service.clean (no orphans)."
  exit 0
}

Write-Host "unknown phase"; exit 2
