param(
  [string]$Project = "C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project",
  [int]$MaxHours = 36
)
$ErrorActionPreference = "Stop"
Set-Location $Project
$py = "C:\Users\Ahmed\AppData\Local\anaconda3\python.exe"
if (!(Test-Path $py)) { $py = "python" }
$logDir = Join-Path $Project "logs\m17_autopilot"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$heartbeat = Join-Path $logDir "HEARTBEAT.json"
$stopFlag = Join-Path $Project "logs\M17_STOP.flag"
$deadline = (Get-Date).AddHours($MaxHours)

function Heartbeat([string]$stage,[string]$state) {
  @{local=(Get-Date).ToString("o");stage=$stage;state=$state;pid=$PID} |
    ConvertTo-Json | Set-Content -Encoding utf8 $heartbeat
}
function ProgressCount([string]$stage) {
  if ($stage -eq "qualification") {
    $g = "research\wp2\m17_v1\qualification\saleor-rc-*.json"
  }
  else {
    $g = "research\wp2\m17_v1\oracle\*\record.json"
  }

  return @(
    Get-ChildItem `
      -Path (Join-Path $Project $g) `
      -ErrorAction SilentlyContinue
  ).Count
}
function RunCtl([string]$plan,[string]$stage) {
  $consecutiveNoProgressStops = 0
  while ((Get-Date) -lt $deadline) {
    if (Test-Path $stopFlag) { Heartbeat $stage "USER_STOP_FLAG"; return 90 }

    $beforeProgress = ProgressCount $stage
    Heartbeat $stage "RUN noProgressStops=$consecutiveNoProgressStops"

    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $log = Join-Path $logDir "$stamp-$stage.log"
    & $py scripts\wp2_ctl_v224.py run --plan $plan 2>&1 | Tee-Object $log
    $rc = $LASTEXITCODE
    $txt = Get-Content $log -Raw
    $afterProgress = ProgressCount $stage
    $madeProgress = $afterProgress -gt $beforeProgress

    if ($rc -eq 0) {
      Heartbeat $stage "COMPLETE"
      return 0
    }

    # Retry only explicitly resumable controller stops.
    # Count consecutive resumable stops WITHOUT evidence progress.
    if ($txt -match "EVAL_ERROR|NO_PROGRESS|HOLD_ACTIVE") {
      if ($madeProgress) {
        $consecutiveNoProgressStops = 0
      }
      else {
        $consecutiveNoProgressStops++
      }

      if ($consecutiveNoProgressStops -ge 6) {
        Heartbeat $stage "RETRY_CAP"
        return $rc
      }

      Start-Sleep -Seconds ([Math]::Min(900,60*[Math]::Max(1,$consecutiveNoProgressStops)))
      continue
    }

    Heartbeat $stage "NON_RESUMABLE_STOP rc=$rc"
    return $rc
  }

  Heartbeat $stage "DEADLINE"
  return 91
}

# Stage 1: REAL qualification controller.
$rc = RunCtl "controller\plan_m17_v1_qualification.json" "qualification"
if ($rc -ne 0) { exit $rc }

# Defensive independent gate verification.
& $py scripts\wp2_m17_exec.py qualification-gate
if ($LASTEXITCODE -ne 0) { Heartbeat "qualification-gate" "FAIL"; exit $LASTEXITCODE }
Heartbeat "qualification-gate" "PASS"

# Stage 2: selector-blind oracle + eligibility only. Hard boundary: this plan has no selector phases.
$rc = RunCtl "controller\plan_m17_v1_oracle_authorized.json" "oracle"
Heartbeat "final" ("DONE rc="+$rc)
exit $rc
