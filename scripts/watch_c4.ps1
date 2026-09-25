# WP-2 C4 live monitor (watch_c4.ps1) - UX v2
# MONITOR-ONLY. Never alters C4 execution, classifier, selection, ordering,
# workers, persistence, PostgreSQL, Docker, evidence, or stop thresholds.
# Ctrl+C stops ONLY this monitor.
# Creates logs\C4_STOP.flag only when C: free < 32 GB and C4 incomplete.
param([switch]$Once)
$ProgressPreference = 'silent'
$PER_TASK = "research\wp2\oracle_confirmation_linux_v2_2026-09-23\per_task_dev_v2.jsonl"
$PER_TEST = "research\wp2\oracle_confirmation_linux_v2_2026-09-23\per_test_dev_v2.jsonl"
$PROGRESS = "research\wp2\oracle_confirmation_linux_v2_2026-09-23\c4_progress.json"
$STOP_FLAG = "logs\C4_STOP.flag"
$TOTAL = 111
$WARN_GB = 40
$STOP_GB = 32
$REFRESH_S = 60

function Get-CDrive {
  return Get-PSDrive C
}

function Get-CFreeGB {
  return [math]::Round((Get-PSDrive C).Free / 1GB, 2)
}

function Get-CUsedGB {
  return [math]::Round((Get-PSDrive C).Used / 1GB, 2)
}

function Get-CTotalGB {
  $d = Get-PSDrive C
  return [math]::Round(($d.Free + $d.Used) / 1GB, 1)
}

function Get-PyProcs {
  param([string]$pattern)
  $found = @()
  try {
    $procs = Get-CimInstance -Class Process -Filter "Name='python.exe' OR Name='pythonw.exe'" -ErrorAction SilentlyContinue
    foreach ($p in $procs) {
      if ($p.CommandLine -like "*$pattern*") { $found += $p.ProcessId }
    }
  } catch {}
  return $found
}

function Format-Min {
  param([double]$seconds)
  if ($seconds -lt 0) { return "n/a" }
  if ($seconds -lt 60) { return ([math]::Round($seconds, 1)).ToString("0.0") + " s" }
  return ([math]::Round($seconds / 60.0, 2)).ToString("0.00") + " min"
}

function New-ProgressBar {
  param([int]$done, [int]$total, [int]$width = 30)
  if ($total -le 0) { return "" }
  $filled = [math]::Floor($done * $width / $total)
  $empty = $width - $filled
  if ($empty -lt 0) { $empty = 0 }
  return ("[" + ("#" * $filled) + ("-" * $empty) + "]")
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ("C4 LIVE MONITOR" + (" " * 22) + (Get-Date -Format "yyyy-MM-dd HH:mm:ss")) -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "UX v2 | refresh $REFRESH_S s | warn $WARN_GB GiB | graceful-stop $STOP_GB GiB | Ctrl+C stops monitor only"
$startFree = Get-CFreeGB
$startTime = Get-Date

try {
  while ($true) {
    $now = Get-Date

    # ---------- per_task (partial-JSONL-safe) ----------
    $taskIds = New-Object System.Collections.Generic.List[string]
    $walls = New-Object System.Collections.Generic.List[double]
    $lastWall = 0.0; $lastTask = ""; $maxWall = 0.0; $maxTask = ""
    $minWall = 1e18; $minTask = ""
    $topSlow = @()
    if (Test-Path $PER_TASK) {
      foreach ($line in (Get-Content $PER_TASK -ErrorAction SilentlyContinue)) {
        $line = $line.Trim()
        if ($line -eq "") { continue }
        try { $rec = $line | ConvertFrom-Json } catch { continue }
        if ($null -eq $rec) { continue }
        $taskIds.Add($rec.task_id)
        if ($rec.PSObject.Properties.Name -contains "wall_s" -and $null -ne $rec.wall_s) {
          $w = [double]$rec.wall_s
          $walls.Add($w)
          $lastWall = $w; $lastTask = $rec.task_id
          if ($w -gt $maxWall) { $maxWall = $w; $maxTask = $rec.task_id }
          if ($w -lt $minWall) { $minWall = $w; $minTask = $rec.task_id }
          $topSlow += "$($rec.task_id):$w"
        }
      }
    }
    $unique = @($taskIds | Sort-Object -Unique)
    $completed = $unique.Count
    $dupes = $taskIds.Count - $completed
    $remaining = $TOTAL - $completed
    $pct = 0.0
    if ($TOTAL -gt 0) { $pct = [math]::Round($completed * 100.0 / $TOTAL, 1) }
    $bar = New-ProgressBar $completed $TOTAL

    # ---------- progress file ----------
    $status = "NO_PROGRESS_FILE"; $heartbeat = ""; $hbAge = -1; $lastResult = ""
    if (Test-Path $PROGRESS) {
      try {
        $pr = (Get-Content $PROGRESS -Raw) | ConvertFrom-Json
        $status = $pr.status
        $heartbeat = $pr.last_heartbeat
        $lastResult = $heartbeat
        if ($null -ne $heartbeat) { $hbAge = [int](New-TimeSpan -Start (Get-Date $heartbeat) -End $now).TotalSeconds }
      } catch { $status = "UNPARSEABLE" }
    }

    # ---------- rolling stats (last 10) ----------
    $n = [Math]::Min(10, $walls.Count)
    $recent = @()
    if ($n -gt 0) { for ($i = $walls.Count - $n; $i -lt $walls.Count; $i++) { $recent += $walls[$i] } }
    $avg10 = 0.0; $med10 = 0.0
    if ($recent.Count -gt 0) { $avg10 = ($recent | Measure-Object -Average).Average }
    $sorted = $recent | Sort-Object
    if ($sorted.Count -gt 0) {
      $m = $sorted.Count
      if ($m % 2 -eq 1) { $med10 = $sorted[($m - 1) / 2] } else { $med10 = ($sorted[$m / 2 - 1] + $sorted[$m / 2]) / 2.0 }
    }
    # session speed (all walls this monitor session) - secondary, only if meaningful
    $sessionAvg = 0.0
    if ($walls.Count -ge 3) { $sessionAvg = ($walls | Measure-Object -Average).Average }

    # ---------- ETA (primary: rolling avg 10; never erased by one quiet refresh) ----------
    $etaH = -1.0; $etaClock = "n/a"
    if ($avg10 -gt 0 -and $remaining -gt 0) {
      $etaH = ($remaining * $avg10) / 3600.0
      $etaClock = (Get-Date).AddSeconds($remaining * $avg10).ToLocalTime().ToString("yyyy-MM-dd HH:mm")
    }
    $sessionEtaH = -1.0; $sessionEtaClock = "n/a"
    if ($sessionAvg -gt 0 -and $remaining -gt 0) {
      $sessionEtaH = ($remaining * $sessionAvg) / 3600.0
      $sessionEtaClock = (Get-Date).AddSeconds($remaining * $sessionAvg).ToLocalTime().ToString("yyyy-MM-dd HH:mm")
    }

    # ---------- per_test ----------
    $perTest = 0
    if (Test-Path $PER_TEST) { $perTest = (Get-Content $PER_TEST | Measure-Object -Line).Lines }

    # ---------- PIDs ----------
    $orch = Get-PyProcs "wp2_linux_main_orchestrator"
    $sweep = Get-PyProcs "wp2_linux_dev_sweep"
    $orchLabel = if ($orch.Count -gt 0) { "RUNNING (pid $($orch -join ','))" } else { "NOT DETECTED" }
    $sweepLabel = if ($sweep.Count -gt 0) { "RUNNING (pid $($sweep -join ','))" } else { "NOT DETECTED" }

    # ---------- storage ----------
    $freeGB = Get-CFreeGB
    $usedGB = Get-CUsedGB
    $totalGB = Get-CTotalGB
    $consumeGB = $startFree - $freeGB
    $growthGBH = 0.0
    $elapsedS = [int](New-TimeSpan -Start $startTime -End $now).TotalSeconds
    if ($elapsedS -gt 900 -and $consumeGB -gt 0.05) { $growthGBH = $consumeGB * 3600.0 / $elapsedS }
    $runwayH = -1.0
    if ($growthGBH -gt 0.05) { $runwayH = ($freeGB - $STOP_GB) / $growthGBH }

    # ---------- status coloring ----------
    $storageStatus = "OK"
    $storageColor = "Green"
    if ($freeGB -lt $STOP_GB) { $storageStatus = "CRITICAL"; $storageColor = "Red" }
    elseif ($freeGB -lt $WARN_GB) { $storageStatus = "WARNING"; $storageColor = "Yellow" }
    $runStatus = "STOPPED"
    $runColor = "Yellow"
    if ($orch.Count -gt 0 -or $sweep.Count -gt 0) { $runStatus = "RUNNING"; $runColor = "Green" }
    if ($status -eq "COMPLETE") { $runStatus = "COMPLETE"; $runColor = "Green" }

    $slowWarn = $false
    $running = ($orch.Count -gt 0 -or $sweep.Count -gt 0) -and (-not (Test-Path $STOP_FLAG))
    if ($running -and $med10 -gt 0 -and $hbAge -gt (2 * $med10)) { $slowWarn = $true }

    Write-Host ""
    Write-Host "C4 PROGRESS" -ForegroundColor Cyan
    Write-Host "==========="
    Write-Host ("Completed:            {0,3} / {1}   ({2,5}%)" -f $completed, $TOTAL, $pct)
    Write-Host ("                      {0}" -f $bar)
    Write-Host ("Remaining:            {0}" -f $remaining)
    Write-Host ("Status:               {0}" -f $runStatus) -ForegroundColor $runColor
    Write-Host ("Duplicates:           {0}" -f $dupes)
    Write-Host ("Per-test records:     {0}" -f $perTest)
    $stopFlagLabel = if (Test-Path $STOP_FLAG) { "PRESENT" } else { "absent" }
    Write-Host ("Stop flag:            {0}" -f $stopFlagLabel)

    Write-Host ""
    Write-Host "RECENT PERFORMANCE" -ForegroundColor Cyan
    Write-Host "=================="
    Write-Host ("Last task wall:       {0}" -f (Format-Min $lastWall))
    Write-Host ("Last task:            {0}" -f $lastTask)
    Write-Host ("Rolling avg (10):     {0}/task" -f (Format-Min $avg10))
    Write-Host ("Rolling median (10):  {0}/task" -f (Format-Min $med10))
    Write-Host ("Recent-10 remaining:  {0}" -f $(if ($etaH -ge 0) { ([math]::Round($etaH,2)).ToString("0.00") + " h" } else { "n/a" }))
    Write-Host ("Recent-10 finish:     {0}" -f $etaClock)
    if ($sessionAvg -gt 0) {
      Write-Host ("Session ETA (avg all): {0}" -f $(if ($sessionEtaH -ge 0) { ([math]::Round($sessionEtaH,2)).ToString("0.00") + " h (" + $sessionEtaClock + ")" } else { "n/a" }))
    }
    Write-Host ("Fastest so far:       {0}" -f (Format-Min $minWall))
    Write-Host ("Fastest task:         {0}" -f $minTask)
    Write-Host ("Slowest so far:       {0}" -f (Format-Min $maxWall))
    Write-Host ("Slowest task:         {0}" -f $maxTask)

    Write-Host ""
    Write-Host "TOP 3 SLOWEST TASKS" -ForegroundColor Cyan
    Write-Host "==================="
    $topSlow = $topSlow | Sort-Object { [double]($_ -Split ":" | Select-Object -Last 1) } -Descending
    $idx = 0
    foreach ($entry in ($topSlow | Select-Object -First 3)) {
      $idx++
      $parts = $entry -Split ":"
      $tid = $parts[0]; $w = [double]$parts[-1]
      $short = $tid
      if ($tid.Length -gt 12) { $short = $tid.Substring($tid.Length - 12) }
      Write-Host ("{0}. {1}   {2}" -f $idx, $short, (Format-Min $w))
    }
    if ($idx -eq 0) { Write-Host "   (no completed tasks yet)" }

    Write-Host ""
    Write-Host "CURRENT ACTIVITY" -ForegroundColor Cyan
    Write-Host "================"
    Write-Host ("Last result:          {0}" -f $lastResult)
    if ($slowWarn) {
      Write-Host ("Current wait age:     {0}" -f (Format-Min $hbAge)) -ForegroundColor Yellow
      Write-Host ("Current task may be unusually slow (>2x recent median).") -ForegroundColor Yellow
    } else {
      Write-Host ("Current wait age:     {0}" -f (Format-Min $hbAge))
    }
    Write-Host ("Heartbeat:            {0}" -f $heartbeat)
    Write-Host ("Heartbeat age:        {0}" -f (Format-Min $hbAge))
    Write-Host ("Orchestrator:         {0}" -f $orchLabel)
    Write-Host ("Sweep/pytest:         {0}" -f $sweepLabel)

    Write-Host ""
    Write-Host "C: STORAGE" -ForegroundColor Cyan
    Write-Host "=========="
    Write-Host ("Used:                 {0} GiB / {1} GiB" -f ([math]::Round($usedGB,1)), $totalGB)
    Write-Host ("Free:                 {0} GiB" -f ([math]::Round($freeGB,1)))
    Write-Host ("Consumed (monitor):   {0} GiB" -f ([math]::Round($consumeGB,2)))
    Write-Host ("Disk growth rate:     {0} GiB/hour" -f ([math]::Round($growthGBH,2)))
    if ($runwayH -ge 0) { Write-Host ("Storage runway:       ~{0} h to {1} GiB" -f ([math]::Round($runwayH,1)), $STOP_GB) }
    else { Write-Host ("Storage runway:       n/a" ) }
    Write-Host ("Storage status:       {0}" -f $storageStatus) -ForegroundColor $storageColor
    Write-Host ("Stop threshold:       <{0} GiB" -f $STOP_GB)
    Write-Host ("Warning threshold:    <{0} GiB" -f $WARN_GB)
    Write-Host ("Refresh:              every {0} seconds" -f $REFRESH_S)
    Write-Host ("Ctrl+C:               stops THIS monitor only, not C4")

    # ---------- guard ----------
    if ($freeGB -lt $STOP_GB -and $completed -lt $TOTAL) {
      if (-not (Test-Path $STOP_FLAG)) {
        New-Item -ItemType File -Path $STOP_FLAG -Force | Out-Null
        Write-Host ("CRITICAL: created $STOP_FLAG (graceful stop requested). Nothing was killed.") -ForegroundColor Red
      } else {
        Write-Host ("CRITICAL: stop flag already present; C4 stops after current chunk. Nothing was killed.") -ForegroundColor Red
      }
    }

    if ($Once) { break }

    Sleep $REFRESH_S
  }
} finally {
  Write-Host ""
  Write-Host "C4 monitor stopped (only the monitor)." -ForegroundColor Yellow
}