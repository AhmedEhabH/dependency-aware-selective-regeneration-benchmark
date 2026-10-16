<#
.SYNOPSIS
  R4 Full-D7 144-unit population-qualification launcher
  (M17_D7_R4_POPULATION_QUALIFICATION_144_HARNESS).

.DESCRIPTION
  Runs the deterministic, resumable, zero-network population-qualification
  harness over all 144 frozen Full-D7 units, exercising the exact frozen Phase4
  per-unit execution path.

  This launcher NEVER contacts a model/network and NEVER pulls/builds/acquires
  anything.  Every qualification container runs with --network=none.  The
  qualification root is NON-SCIENTIFIC (separate from the frozen scientific run
  roots); this launcher does NOT start the scientific Full144 run.

  Gates before Unit 1 (all fail closed, exit != 0 on mismatch):
    * branch == frozen branch; git HEAD == frozen HEAD; tracked worktree clean
    * effective execution-code-set aggregate hash == frozen
    * population identity / order hash / binding hash == frozen
    * artifact static closure 144/144 (offline)
    * 11/11 local execution images with exact frozen immutable IDs
    * Docker daemon available; source repository (/opt/wp2_v2/saleor-cache) present
    * free space on D: >= hard-stop threshold (120 GiB)

  Sweep semantics:
    * sequential, workers=1, deterministic frozen 144-unit order
    * resumable: already-completed qualification units are skipped on resume
    * atomic checkpoint after every unit (QUALIFICATION_MANIFEST.json)
    * a unit failure does NOT stop the sweep (result UNIT_GATE_FAILURE or
      UNIT_HARNESS_FAILURE); global integrity failures fail closed immediately
    * unit timeout remains the frozen runner timeout (5400 s)
    * qualification-owned Docker volumes (r4qual144_*) verified removed after
      each unit; per-unit temporary wheelhouse data cleaned after evidence is
      safely persisted; shared era caches preserved

.PARAMETER QualRoot
  Qualification (NON-SCIENTIFIC) run root.  Defaults to the canonical root.

.PARAMETER PreflightOnly
  Run only the global preflight gates (never executes a unit).

.EXAMPLE
  powershell -File scripts\r4_full144_qualification_launcher.ps1
.EXAMPLE
  powershell -File scripts\r4_full144_qualification_launcher.ps1 -PreflightOnly
#>
[CmdletBinding()]
param(
    [string]$QualRoot = "D:\WP2\runs\r4-full-d7-144-qualification-2026-10-16",
    [switch]$PreflightOnly
)

$ErrorActionPreference = "Stop"
$script:Project = Split-Path -Parent $PSScriptRoot
$Harness = Join-Path $script:Project "scripts\r4_full144_qualification_harness.py"

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

function Invoke-Preflight {
    $env:R4_FULL144_RUN_ROOT = $QualRoot
    $out = & $Python.App $Python.Args (Join-Path $script:Project "scripts\r4_full144_qualification_harness.py") --preflight 2>&1
    $rc = $LASTEXITCODE
    if ($rc -ne 0) {
        Write-Host "PREFLIGHT_FAIL_CLOSED rc=$rc"
        $out | ForEach-Object { Write-Host "  $_" }
        exit 1
    }
    Write-Host "PREFLIGHT_PASS"
    $out | ForEach-Object { Write-Host "  $_" }
}

try {
    $Python = Resolve-Python
    Write-Host "LAUNCHER_START qual_root=$QualRoot"
    Write-Host "WORKTREE=$script:Project"

    Invoke-Preflight
    if ($PreflightOnly) {
        Write-Host "PREFLIGHT_ONLY_DONE"
        exit 0
    }

    $env:R4_FULL144_RUN_ROOT = $QualRoot
    & $Python.App $Python.Args $Harness --run 2>&1
    $rc = $LASTEXITCODE
    if ($rc -ne 0) {
        Write-Host "QUALIFICATION_RUN_STOPPED rc=$rc"
        exit 1
    }
    Write-Host "QUALIFICATION_RUN_DONE"
    exit 0
}
catch {
    Write-Host "LAUNCHER_STOPPED $_"
    exit 1
}
