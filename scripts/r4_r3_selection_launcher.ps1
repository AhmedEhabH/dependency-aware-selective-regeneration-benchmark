#requires -Version 7
<#
.SYNOPSIS
  M17_D7_R4_PHASE1C Harness R3 operator launcher (m17-d7-r4-population-
  qualification-harness-r3-2026-10-16).  Invokes the FINAL tagged R3 release
  sitting at the current HEAD.  ZERO external-agent / model / network dependency.
  All scientific units run with --network=none.

.DESCRIPTION
  Operator commands for the frozen R3 selection harness.  Every command fails
  closed on authority drift (HEAD != peeled R3 tag, dirty tracked tree, code-set
  or closure or population/order/image drift, wrong branch).  Dependency chain:
  TARGETED3 -> CAL12 -> FULL144.  CAL12 refuses to start unless a fresh
  TARGETED3 receipt (same R3 release) says 3 completed / 3 PASS / 0 non-PASS.
  FULL144 refuses unless a fresh CAL12 receipt says 12 completed / 12 PASS /
  0 non-PASS.  This launcher has ZERO external-agent / model / network dependency;
  all scientific units run with --network=none.

.PARAMETER Selection
  TARGETED3 | CAL12 | FULL144

.PARAMETER Status
  Print compact status of the selection run root (safe at any time).

.PARAMETER Preflight
  Run the authority + selection + zero-exec preflight (never executes units).

.PARAMETER Exec
  Fail-closed operator execution gate for the selection.  Materializes the
  per-unit path via the frozen driver under the selection run root.

.EXAMPLE
  powershell -File scripts\r4_r3_selection_launcher.ps1 -Selection TARGETED3 -Preflight
.EXAMPLE
  powershell -File scripts\r4_r3_selection_launcher.ps1 -Selection TARGETED3 -Exec
#>
[CmdletBinding()]
param(
    [ValidateNotNullOrEmpty()]
    [string]$Selection = "TARGETED3",
    [switch]$Status,
    [switch]$Preflight,
    [switch]$Exec
)

$ErrorActionPreference = "Stop"
$script:Project = Split-Path -Parent $PSScriptRoot
$Harness = Join-Path $script:Project "scripts\r4_r3_selection_harness.py"

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

function Invoke-Harness {
    param([string[]]$Args)
    & $Python.App $Python.Args $Harness @Args 2>&1
    $rc = $LASTEXITCODE
    if ($rc -ne 0) {
        Write-Host "R3_FAIL_CLOSED rc=$rc"
        exit 1
    }
    Write-Host "R3_COMMAND_OK rc=$rc"
}

try {
    $Python = Resolve-Python
    Write-Host "R3_LAUNCHER selection=$Selection worktree=$script:Project"

    if ($Status) {
        Invoke-Harness @("--status", $Selection)
        exit 0
    }
    if ($Preflight) {
        Invoke-Harness @("--preflight", $Selection)
        exit 0
    }
    if ($Exec) {
        Invoke-Harness @("--exec", $Selection)
        exit 0
    }

    # default: preflight
    Invoke-Harness @("--preflight", $Selection)
    exit 0
}
catch {
    Write-Host "R3_LAUNCHER_STOPPED $_"
    exit 1
}