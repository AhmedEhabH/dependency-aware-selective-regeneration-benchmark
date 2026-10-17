#requires -Version 7
<#
.SYNOPSIS
  M17_D7_R4 successor scientific Full144 operator launcher (mission
  M17_D7_R4_POSTQUAL_SUCCESSOR_PREEXECUTION_FREEZE).  Invokes the committed
  successor preflight module at the current HEAD.  ZERO external-agent / model /
  network dependency.  All scientific units run with --network=none through the
  frozen Full144 driver; THIS launcher never executes a scientific unit for
  Status / Preflight.

.DESCRIPTION
  Operator commands for the frozen successor scientific Full144 run:
    -Status     compact status of the scientific run root (safe at any time).
    -Preflight  fail-closed authority + receipt + fresh-root gate (never
                executes units).
    -Exec       operator execution gate: runs exactly the next frozen unit via
                the frozen driver (scripts/r4_full144_preexecution.py --next)
                under R4_FULL144_RUN_ROOT=scientific root.  Operator-only future gate; never invoked remotely.

  Every command fails closed on: wrong branch/HEAD/tag peel, scientific
  authority drift, code-set drift, closure drift, population/order/image drift,
  R3.1 drift, invalid/missing TARGETED3/CAL12/qualification144 receipts,
  non-fresh scientific root, network fallback, missing Docker/runtime/image
  prerequisite, disk below frozen safety threshold, dirty tracked tree.

.EXAMPLE
  pwsh -NoProfile -ExecutionPolicy Bypass -File scripts\r4_full144_successor_scientific_launcher.ps1 -Status
.EXAMPLE
  pwsh -NoProfile -ExecutionPolicy Bypass -File scripts\r4_full144_successor_scientific_launcher.ps1 -Preflight
#>
[CmdletBinding()]
param(
    [switch]$Status,
    [switch]$Preflight,
    [switch]$Exec
)

$ErrorActionPreference = "Stop"
$script:Project = Split-Path -Parent $PSScriptRoot
$PreflightPy = Join-Path $script:Project "scripts\r4_full144_successor_scientific_preflight.py"

function Resolve-Python {
    $candidates = @(
        @{ App = "py"; Args = @("-3.11") },
        @{ App = "python"; Args = @() }
    )
    foreach ($c in $candidates) {
        $test = & $c.App $c.Args @("-c", "import sys; print(sys.version_info[:2])") 2>$null
        if ($LASTEXITCODE -eq 0 -and ($test -join "" ) -match "\(3, 11\)") {
            return $c
        }
    }
    return $candidates[1]
}

function Invoke-PreflightModule {
    param([string[]]$ModuleArgs)
    & $Python.App $Python.Args $PreflightPy @ModuleArgs 2>&1
    $rc = $LASTEXITCODE
    if ($rc -ne 0) {
        Write-Host "SCIENTIFIC_FAIL_CLOSED rc=$rc"
        exit $rc
    }
    Write-Host "SCIENTIFIC_COMMAND_OK rc=$rc"
}

try {
    $Python = Resolve-Python
    Write-Host "SCIENTIFIC_LAUNCHER command worktree=$script:Project"

    if ($Status) {
        Invoke-PreflightModule -ModuleArgs @("--status")
        exit $LASTEXITCODE
    }
    if ($Preflight) {
        Invoke-PreflightModule -ModuleArgs @("--preflight")
        exit $LASTEXITCODE
    }
    if ($Exec) {
        $env:R4_FULL144_RUN_ROOT = "D:\WP2\runs\r4-scientific-full144-successor-2026-10-17"
        $out = & $Python.App $Python.Args (Join-Path $script:Project "scripts\r4_full144_preexecution.py") --next 2>&1
        $rc = $LASTEXITCODE
        if ($rc -ne 0) {
            Write-Host "SCIENTIFIC_EXEC_FAIL_CLOSED rc=$rc"
            $out | ForEach-Object { Write-Host "  $_" }
            exit $rc
        }
        Write-Host "SCIENTIFIC_UNIT_OK rc=$rc"
        exit 0
    }

    # default: preflight
    Invoke-PreflightModule -ModuleArgs @("--preflight")
    exit $LASTEXITCODE
}
catch {
    Write-Host "SCIENTIFIC_LAUNCHER_STOPPED $_"
    exit 1
}