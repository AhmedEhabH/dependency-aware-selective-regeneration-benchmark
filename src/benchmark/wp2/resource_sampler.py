"""WP-2 real resource sampler (Mission-09) - ZERO API.

Fixes the Mission-08 instrumentation gap (ERRATUM A): a separate resource
sampler records raw samples at a 5 s interval with monotonic timestamps so
aggregates can be recomputed later, and NEVER confuses ``used`` with
``total``/capacity.

Captured per sample (Mission-09 section 15):
- 15A Windows host RAM (total/available/used via psutil; committed + pagefile
  via psutil swap);
- 15B WSL /proc/meminfo (MemTotal / MemAvailable / SwapTotal / SwapFree) and
  load;
- 15C Docker stats (CPU %, memory usage/limit/percent, PIDs) for the active
  test container and the PostgreSQL container;
- 15D CPU (host total, WSL load, per-container CPU %);
- 15E disk (C: free GiB, WSL filesystem used/available, ext4.vhdx host bytes);

All raw samples are appended to a JSONL file; aggregate metrics are derived
from raw samples only.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import time
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

SAMPLER_VERSION = "wp2-resource-sampler-v1-2026-09-25"
SAMPLING_INTERVAL_S = 5

WSL_DISTRO = "Ubuntu-24.04"

GIB = 1024**3


def _gib(value: float) -> float:
    return value / GIB


def wsl(script: str, timeout_s: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=timeout_s,
        check=False,
    )


@dataclass
class Sample:
    ts_mono: float
    ts_wall: float
    payload: dict


def _parse_mem(value: str) -> float | None:
    """Parse a docker mem string ('123.4MiB' | '1.2GiB') to GiB float."""
    try:
        if "MiB" in value:
            return float(value.replace("MiB", "")) / 1024
        if "GiB" in value:
            return float(value.replace("GiB", ""))
    except ValueError:
        return None
    return None


def sample_host() -> dict:
    """15A Windows host RAM + 15D host CPU."""
    try:
        import psutil

        vm = psutil.virtual_memory()
        sw = psutil.swap_memory()
        cpu = psutil.cpu_percent(interval=0.5)
    except Exception as exc:  # pragma: no cover
        return {"error": f"psutil: {exc}"}
    return {
        "host_total_gib": round(_gib(vm.total), 3),
        "host_available_gib": round(_gib(vm.available), 3),
        "host_used_gib": round(_gib(vm.total - vm.available), 3),
        "host_percent": round(vm.percent, 2),
        "committed_gib": round(_gib(vm.total - vm.available), 3),  # committed approx = used
        "pagefile_swap_total_gib": round(_gib(sw.total), 3),
        "pagefile_swap_used_gib": round(_gib(max(sw.used, 0)), 3),
        "host_cpu_percent": round(cpu, 2),
    }


def sample_wsl() -> dict:
    """15B WSL /proc/meminfo + load."""
    r = wsl("grep -E 'MemTotal|MemAvailable|SwapTotal|SwapFree' /proc/meminfo; echo ---; cut -d' ' -f1-3 /proc/loadavg")
    out: dict = {"wsl_error": None}
    if r.returncode != 0:
        out["wsl_error"] = (r.stderr or r.stdout)[-300:]
        return out
    lines = r.stdout.splitlines()
    mem: dict[str, int] = {}
    for line in lines[:4]:
        parts = line.split(":")
        if len(parts) == 2:
            kb = parts[1].strip().split()[0]
            with suppress(ValueError):
                mem[parts[0]] = int(kb)
    memtotal = mem.get("MemTotal", 0)
    memavail = mem.get("MemAvailable", 0)
    swaptotal = mem.get("SwapTotal", 0)
    swapfree = mem.get("SwapFree", 0)
    load_parts = []
    for line in lines:
        if "---" not in line and len(line.split()) >= 3:
            try:
                load_parts = [float(x) for x in line.split()[:3]]
                break
            except ValueError:
                pass
    out.update(
        {
            "wsl_mem_total_gib": round(_gib(memtotal * 1024), 3),
            "wsl_mem_available_gib": round(_gib(memavail * 1024), 3),
            "wsl_used_gib": round(_gib((memtotal - memavail) * 1024), 3),
            "wsl_swap_total_gib": round(_gib(swaptotal * 1024), 3),
            "wsl_swap_free_gib": round(_gib(swapfree * 1024), 3),
            "wsl_swap_used_gib": round(_gib((swaptotal - swapfree) * 1024), 3),
            "wsl_load_1m": load_parts[0] if load_parts else None,
            "wsl_load_5m": load_parts[1] if len(load_parts) > 1 else None,
            "wsl_load_15m": load_parts[2] if len(load_parts) > 2 else None,
        }
    )
    return out


def sample_docker(container_names: list[str]) -> dict:
    """15C/15D Docker stats for the named containers (test container + pg)."""
    result: dict = {}
    if not container_names:
        return result
    names = " ".join(container_names)
    r = wsl(
        "docker stats --no-stream --format "
        '"{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}|{{.MemPerc}}|{{.PIDs}}" '
        + names,
        timeout_s=30,
    )
    if r.returncode != 0:
        result["_docker_error"] = (r.stderr or r.stdout)[-300:]
        return result
    for line in r.stdout.splitlines():
        parts = line.split("|")
        if len(parts) < 5:
            continue
        name, cpu, mem_usage, mem_perc, pids = parts[:5]
        mem_used_gib = None
        mem_limit_gib = None
        if "/" in mem_usage:
            mem_used, mem_limit = mem_usage.split("/")[0].strip(), mem_usage.split("/")[1].strip()
            mem_used_gib = _parse_mem(mem_used)
            mem_limit_gib = _parse_mem(mem_limit)
        try:
            cpu_pct = float(cpu.rstrip("%"))
        except ValueError:
            cpu_pct = None
        result[name] = {
            "cpu_percent": cpu_pct,
            "mem_used_gib": mem_used_gib,
            "mem_limit_gib": mem_limit_gib,
            "mem_percent": mem_perc,
            "pids": pids,
        }
    return result


def sample_disk() -> dict:
    """15E disk: C: free GiB + WSL fs used/available + ext4.vhdx host bytes."""
    try:
        c_free = shutil.disk_usage("C:/").free
        c_error = None
    except Exception as exc:  # pragma: no cover
        c_free = None
        c_error = str(exc)
    r = wsl("df -B1 / | tail -1")
    wsl_used = wsl_avail = None
    if r.returncode == 0:
        parts = r.stdout.split()
        if len(parts) >= 4:
            try:
                wsl_used = int(parts[2])
                wsl_avail = int(parts[3])
            except ValueError:
                pass
    vhdx = None
    # vhdx host file size via WSL (C: is mounted read-only at /mnt/c).
    r2 = wsl(
        "stat -c %s "
        "'/mnt/c/Users/Ahmed/AppData/Local/wsl/{0c13781c-f355-4fad-95f7-ad01df935d7c}/ext4.vhdx' "
        "2>/dev/null || echo __NO_VHDX__",
        timeout_s=30,
    )
    if r2.returncode == 0 and "__NO_VHDX__" not in r2.stdout and r2.stdout.strip().isdigit():
        vhdx = int(r2.stdout.strip())
    return {
        "c_free_gib": round(_gib(c_free), 3) if c_free is not None else None,
        "c_error": c_error,
        "wsl_fs_used_gib": round(_gib(wsl_used), 3) if wsl_used is not None else None,
        "wsl_fs_available_gib": round(_gib(wsl_avail), 3) if wsl_avail is not None else None,
        "wsl_ext4_vhdx_bytes": vhdx,
        "wsl_ext4_vhdx_gib": round(_gib(vhdx), 3) if vhdx is not None else None,
    }


def _discover_running_containers() -> list[str]:
    """Discover running test containers (wp2-test-*) plus the postgres container."""
    r = wsl("docker ps --format '{{.Names}}' 2>/dev/null")
    names = [line.strip() for line in (r.stdout or "").splitlines() if line.strip()]
    discovered = [n for n in names if n.startswith("wp2-test-")]
    if "wp2-pg" in names:
        discovered.append("wp2-pg")
    return discovered


def make_sample(test_container: str | None = None, include_disk: bool = True) -> Sample:
    """One 5 s-interval sample."""
    payload: dict = {
        "sampler_version": SAMPLER_VERSION,
    }
    payload.update(sample_host())
    payload.update(sample_wsl())
    containers = (
        list({test_container, "wp2-pg"}) if test_container else _discover_running_containers()
    )
    payload["docker"] = sample_docker(containers)
    if include_disk:
        payload.update(sample_disk())
    return Sample(ts_mono=time.monotonic(), ts_wall=time.time(), payload=payload)


def run_sampler_loop(
    out_path: Path,
    *,
    interval_s: int = SAMPLING_INTERVAL_S,
    duration_s: float | None = None,
    stop_file: Path | None = None,
    test_container: str | None = None,
) -> int:
    """Sample every ``interval_s`` seconds until ``duration_s`` elapses or the
    stop-file appears. Appends raw JSONL samples (monotonic + wall ts)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    n = 0
    with out_path.open("a", encoding="utf-8") as fh:
        while True:
            sample = make_sample(test_container=test_container)
            fh.write(
                json.dumps(
                    {"ts_mono": round(sample.ts_mono, 3), "ts_wall": round(sample.ts_wall, 3), **sample.payload},
                    ensure_ascii=False,
                )
                + "\n"
            )
            fh.flush()
            n += 1
            if duration_s is not None and time.monotonic() - t0 >= duration_s:
                break
            if stop_file is not None and stop_file.exists():
                break
            time.sleep(interval_s)
    return n


def aggregate_samples(path: Path) -> dict:
    """Derive aggregate metrics from raw samples (never from prose)."""
    samples: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            samples.append(json.loads(line))
    if not samples:
        return {"n_samples": 0}

    def _vals(key: str) -> list[float]:
        return [s[key] for s in samples if s.get(key) is not None and isinstance(s[key], (int, float))]

    def _agg(key: str) -> dict:
        vals = _vals(key)
        if not vals:
            return {"n": 0}
        vals_sorted = sorted(vals)
        n = len(vals_sorted)
        p95 = vals_sorted[int(0.95 * (n - 1))]
        p50 = vals_sorted[int(0.50 * (n - 1))]
        return {
            "n": n,
            "min": round(vals_sorted[0], 3),
            "avg": round(sum(vals_sorted) / n, 3),
            "p50": round(p50, 3),
            "p95": round(p95, 3),
            "max": round(vals_sorted[-1], 3),
        }

    agg = {
        "n_samples": len(samples),
        "t_start_mono": samples[0]["ts_mono"],
        "t_end_mono": samples[-1]["ts_mono"],
        "wall_span_s": round(samples[-1]["ts_mono"] - samples[0]["ts_mono"], 3),
    }
    for key in (
        "host_total_gib",
        "host_available_gib",
        "host_used_gib",
        "committed_gib",
        "pagefile_swap_used_gib",
        "host_cpu_percent",
        "wsl_mem_total_gib",
        "wsl_mem_available_gib",
        "wsl_used_gib",
        "wsl_swap_used_gib",
        "wsl_load_1m",
        "c_free_gib",
        "wsl_fs_used_gib",
        "wsl_ext4_vhdx_gib",
    ):
        agg[key] = _agg(key)
    # docker container aggregates
    docker_names = sorted({k for s in samples for k in (s.get("docker") or {}) if not k.startswith("_")})
    agg["docker"] = {}
    for cname in docker_names:
        cpu = [
            s["docker"][cname]["cpu_percent"]
            for s in samples
            if cname in (s.get("docker") or {})
            and s["docker"][cname].get("cpu_percent") is not None
        ]
        mem = [
            s["docker"][cname]["mem_used_gib"]
            for s in samples
            if cname in (s.get("docker") or {})
            and s["docker"][cname].get("mem_used_gib") is not None
        ]
        agg["docker"][cname] = {
            "cpu_percent": _agg_from(cpu),
            "mem_used_gib": _agg_from(mem),
        }
    return agg


def _agg_from(vals: list[float]) -> dict:
    if not vals:
        return {"n": 0}
    vals_sorted = sorted(vals)
    n = len(vals_sorted)
    return {
        "n": n,
        "min": round(vals_sorted[0], 3),
        "avg": round(sum(vals_sorted) / n, 3),
        "p50": round(vals_sorted[int(0.5 * (n - 1))], 3),
        "p95": round(vals_sorted[int(0.95 * (n - 1))], 3),
        "max": round(vals_sorted[-1], 3),
    }
