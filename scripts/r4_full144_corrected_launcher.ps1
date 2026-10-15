<#
.SYNOPSIS
  R4 corrected Full144 local unattended launcher (M17_D7_R4_FRAMEWORK_GATE_PHASE3_REPAIR).

.DESCRIPTION
  Runs the frozen Full144 driver sequentially (concurrency = 1) from this exact
  frozen Phase-3 worktree, using the fresh CORRECTED run root.  Deterministic,
  unattended, offline.  This launcher performs NO external model/network call
  and NO network acquisition (it only invokes the frozen local driver).

  Gates before Unit 1 (all fail closed, exit != 0 on mismatch):
    * canonical corrected freeze record present + branch correct
    * current git HEAD == freeze HEAD (Phase-3 frozen repair commit)
    * tracked worktree clean
    * effective execution-code-set hash (corrected code set)
    * population/order/binding hashes
    * run root == fresh corrected root (never the failed successor root)
    * 11/11 local execution images with exact immutable IDs

  Loop semantics:
    * execute exactly the next frozen unit sequentially (order preserved)
    * concurrency = 1
    * continue automatically after PASS
    * STOP immediately on first mandatory FAIL (nonzero exit)
    * never skip / reorder / rerun a completed PASS unit
    * never overwrite immutable unit evidence (driver is authoritative)
    * preserves atomic checkpoint/restart and partial-unit STOP_OWNER_REVIEW
      semantics (enforced by the frozen driver)
    * scientific execution uses --network=none (frozen in the driver/runner)
    * never pull/build/download/acquire anything

  The corrected run RESTARTS FROM UNIT 1 on a fresh corrected root.  It MUST
  NOT import/adopt any evidence from the failed successor run.

.PARAMETER RunRoot
  Fresh corrected run root.  Defaults to the canonical corrected root.

.PARAMETER MaxSteps
  Upper bound on units to run in this invocation (useful for manual chunking).
  If omitted the launcher runs until COMPLETE (all 144 PASS) or FAIL.

.PARAMETER LogFile
  Local launcher log path (defaults to <RunRoot>\logs\launcher.log).

.PARAMETER PreflightOnly
  Run only the pre-Unit-1 gates and exit.

.EXAMPLE
  powershell -File scripts/r4_full144_corrected_launcher.ps1 -PreflightOnly
.EXAMPLE
  powershell -File scripts/r4_full144_corrected_launcher.ps1
#>
[CmdletBinding()]
param(
    [string]$RunRoot = "D:\WP2\runs\r4-full-d7-144-framework-corrected-2026-10-15",
    [int]$MaxSteps = 0,
    [string]$LogFile = "",
    [switch]$PreflightOnly
)

$ErrorActionPreference = "Stop"
$script:Project = Split-Path -Parent $PSScriptRoot
if (-not $LogFile) {
    $LogFile = Join-Path $RunRoot "logs\launcher.log"
}
$LogDir = Split-Path -Parent $LogFile
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-LauncherLog([string]$Message) {
    $line = "$(Get-Date -Format o)  $Message"
    Add-Content -LiteralPath $LogFile -Value $line
    Write-Host $line
}

function Invoke-Preflight {
    $env:R4_FULL144_RUN_ROOT = $RunRoot
    $out = & python (Join-Path $script:Project "scripts\r4_full144_corrected_preflight.py") `
        --run-root $RunRoot --preflight --static 2>&1
    $rc = $LASTEXITCODE
    if ($rc -ne 0) {
        Write-LauncherLog "PREFLIGHT_FAIL_CLOSED rc=$rc"
        $out | ForEach-Object { Write-LauncherLog "  $_" }
        throw "FROZEN_INVARIANT_MISMATCH preflight failed"
    }
    Write-LauncherLog "PREFLIGHT_PASS"
    $out | ForEach-Object { Write-LauncherLog "  $_" }
    return $out
}

function Invoke-OneStep {
    param([string]$NextRoot)
    $env:R4_FULL144_RUN_ROOT = $NextRoot
    $out = & python (Join-Path $script:Project "scripts\r4_full144_preexecution.py") --next 2>&1
    $rc = $LASTEXITCODE
    $text = $out -join "`n"
    if ($rc -ne 0) {
        Write-LauncherLog "UNIT_STEP_FAIL_CLOSED rc=$rc"
        $out | ForEach-Object { Write-LauncherLog "  $_" }
        throw "SCIENTIFIC_FAIL unit step failed"
    }
    Write-LauncherLog "STEP_RC=0"
    $out | ForEach-Object { Write-LauncherLog "  $_" }
    return @{ rc = $rc; text = $text }
}

try {
    Write-LauncherLog "LAUNCHER_START run_root=$RunRoot max_steps=$MaxSteps"
    Write-LauncherLog "WORKTREE=$script:Project"
    Write-LauncherLog "CORRECTED_RUN_RESTART_FROM_UNIT_1=1"
    Write-LauncherLog "NO_PRIOR_SCIENTIFIC_EVIDENCE_IMPORTED=1"

    # --- Pre-Unit-1 gates ---------------------------------------------------
    $preflight = Invoke-Preflight
    if ($PreflightOnly) {
        Write-LauncherLog "PREFLIGHT_ONLY_DONE"
        exit 0
    }

    # --- Sequential unattended loop ----------------------------------------
    $steps = 0
    $done = $false
    while (-not $done) {
        if ($MaxSteps -gt 0 -and $steps -ge $MaxSteps) {
            Write-LauncherLog "MAX_STEPS_REACHED steps=$steps (resumable; next resume runs next unit)"
            exit 0
        }
        $res = Invoke-OneStep -NextRoot $RunRoot
        $steps++
        if ($res.text -match "RUN_COMPLETE") {
            $done = $true
        }
    }
    Write-LauncherLog "LAUNCHER_COMPLETE all 144 PASS"
    exit 0
}
catch {
    Write-LauncherLog "LAUNCHER_STOPPED $_"
    exit 1
}
