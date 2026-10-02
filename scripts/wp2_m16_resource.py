#!/usr/bin/env python3
"""WP2 M16 resource probes, dry-run measurement and the projected-headroom gate.

ZERO model API. Probes only read state (disk usage, file sizes, `docker system df`, `du` of the
uv-cache volume, worktree/container/DB listings); nothing here deletes or moves anything.

Gate (design freeze, S1): Route B (Q03) may start only if the conservative projection of C:
free space at Q09 completion is >= PLAN_FLOOR_GIB (25), computed from the frozen 3-task
resource dry-run. During any Docker phase the engine HOLDs (resumable) below HOLD_GIB (20)
and warns below WARN_GIB (25).
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

GIB = 1024 ** 3
HOLD_GIB, WARN_GIB, PLAN_FLOOR_GIB, SAFETY_GIB = 20.0, 25.0, 25.0, 2.0
DISTRO = "Ubuntu-24.04"
UV_VOLUME = "wp2-uv-cache"
WSL_CACHE = "/opt/wp2_v2/saleor-cache"
WSL_WT = "/opt/wp2_v2/worktrees"
# Conservative workload model for the projection (upper bounds, frozen in the design):
WORKLOAD = {
    "oracle_containers": 2 * 220,          # Q03: target + parent state per task
    "p2pu_containers": 3 * 220,            # Q05A: rediscovery + 2 states, every task assumed eligible
    "readiness_containers": 2 * 220,       # Q06: negative + positive
    "opws_containers": 2 * 220 + 3 * 13,   # Q09: every RMCSS/AGENT item + replicate items, no dedup
    "evidence_tasks": 220,
}


def c_drive() -> str:
    return os.environ.get("M16_C_DRIVE", "C:/" if os.name == "nt" else "/")


def c_free_gib(path: str | None = None) -> float:
    return shutil.disk_usage(path or c_drive()).free / GIB


def _run(cmd: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=timeout)


def wsl(script: str, timeout: int = 300) -> subprocess.CompletedProcess:
    return _run(["wsl", "-d", DISTRO, "--", "bash", "-lc", script], timeout)


def vhdx_path() -> str | None:
    """Locate the distro's ext4.vhdx from the Lxss registry (Windows only)."""
    if os.name != "nt":
        return os.environ.get("M16_VHDX_PATH")
    try:
        import winreg
        base = r"Software\Microsoft\Windows\CurrentVersion\Lxss"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, base) as k:
            i = 0
            while True:
                try:
                    sub = winreg.EnumKey(k, i)
                except OSError:
                    return None
                i += 1
                with winreg.OpenKey(k, sub) as s:
                    try:
                        name = winreg.QueryValueEx(s, "DistributionName")[0]
                        bp = winreg.QueryValueEx(s, "BasePath")[0]
                    except OSError:
                        continue
                    if name == DISTRO:
                        bp = bp.replace("\\\\?\\", "")
                        return str(Path(bp) / "ext4.vhdx")
    except OSError:
        return None


def file_size_info(path: str | None) -> dict:
    if not path or not Path(path).exists():
        return {"path": path, "size_bytes": None, "allocated_bytes": None}
    st = os.stat(path)
    alloc = None
    if os.name == "nt":
        try:
            import ctypes
            k32 = ctypes.WinDLL("kernel32", use_last_error=True)
            fn = k32.GetCompressedFileSizeW
            fn.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_ulong)]
            fn.restype = ctypes.c_ulong                      # DWORD: unsigned (no +/-4 GiB wrap)
            hi = ctypes.c_ulong(0)
            ctypes.set_last_error(0)
            lo = fn(str(path), ctypes.byref(hi))
            if lo == 0xFFFFFFFF and ctypes.get_last_error() != 0:
                alloc = None                                 # INVALID_FILE_SIZE with a real error
            else:
                alloc = (int(hi.value) << 32) + int(lo)
        except Exception:  # noqa: BLE001 - diagnostic only
            alloc = None
    else:
        alloc = getattr(st, "st_blocks", 0) * 512
    return {"path": path, "size_bytes": st.st_size, "allocated_bytes": alloc}


def guest_used_bytes() -> int | None:
    """Used bytes of the WSL guest root filesystem (in-guest view of VHDX consumption)."""
    r = wsl("df -B1 --output=used / | tail -1", 120)
    try:
        return int((r.stdout or "").strip().splitlines()[-1])
    except (ValueError, IndexError):
        return None


def uv_cache_bytes() -> int | None:
    r = wsl(f"docker volume inspect {UV_VOLUME} --format '{{{{.Mountpoint}}}}'", 120)
    mp = (r.stdout or "").strip()
    if r.returncode or not mp:
        return None
    r = wsl(f"du -sb {mp} 2>/dev/null | cut -f1", 1800)
    try:
        return int((r.stdout or "").strip().split()[0])
    except (ValueError, IndexError):
        return None


def docker_df() -> list[dict] | None:
    r = wsl("docker system df --format '{{json .}}'", 300)
    if r.returncode:
        return None
    out = []
    for line in (r.stdout or "").splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    return out


def transient_leftovers(tid: str) -> dict:
    """Worktrees, containers and DBs left behind for one task id prefix (must all be empty)."""
    wt = wsl(f"git -C {WSL_CACHE} worktree list --porcelain | grep -c '{tid}' || true", 120)
    ct = wsl(f"docker ps -a --format '{{{{.Names}}}} {{{{.Image}}}}' | grep -c '{tid}' || true", 120)
    db = wsl("docker exec wp2-pg psql -U saleor -d postgres -Atc "
             f"\"select count(*) from pg_database where datname like '%{tid}%'\" || true", 120)
    def _n(r: subprocess.CompletedProcess) -> int | None:
        try:
            return int((r.stdout or "").strip().splitlines()[-1])
        except (ValueError, IndexError):
            return None
    return {"worktrees": _n(wt), "containers": _n(ct), "databases": _n(db)}


def snapshot(label: str, *, heavy: bool = True) -> dict:
    """One resource snapshot. heavy=False skips the uv-cache du and docker df (the in-guest used
    bytes are always taken, so state_use can compare every pair of states)."""
    snap: dict[str, Any] = {"label": label, "c_free_gib": round(c_free_gib(), 4),
                            "vhdx": file_size_info(vhdx_path()), "host": platform.platform()}
    snap["guest_used_bytes"] = guest_used_bytes()            # cheap; needed by state_use on every state
    if heavy:
        snap["uv_cache_bytes"] = uv_cache_bytes()
        snap["docker_df"] = docker_df()
    return snap


def hold_status() -> dict:
    free = c_free_gib()
    return {"c_free_gib": round(free, 3), "hold": free < HOLD_GIB, "warn": free < WARN_GIB,
            "hold_gib": HOLD_GIB, "warn_gib": WARN_GIB}


# ------------------------------------------------------------------ projection (pure)
def state_use(before: dict, after: dict) -> tuple[float, str]:
    """GiB consumed between two snapshots = the MAXIMUM of every available measure (conservative):
    VHDX allocated growth, drop in C: free space, and the in-guest used-bytes delta (the VHDX can
    absorb growth into internal free blocks, so its growth alone may read ~0). Never negative.
    Returns (gib, name of the measure that gave the maximum; ties keep the listed order)."""
    def _d(key: str, sub: str | None = None) -> float | None:
        b = (before.get(key) or {}).get(sub) if sub else before.get(key)
        a = (after.get(key) or {}).get(sub) if sub else after.get(key)
        return (a - b) / GIB if isinstance(a, int) and isinstance(b, int) else None
    measures = [("vhdx_allocated", _d("vhdx", "allocated_bytes")),
                ("c_free_drop", before["c_free_gib"] - after["c_free_gib"]),
                ("guest_used", _d("guest_used_bytes"))]
    best = ("c_free_drop", 0.0)
    for name, v in measures:
        if v is not None and v > best[1]:
            best = (name, v)
    if best[1] == 0.0:
        avail = [n for n, v in measures if v is not None]
        best = (avail[0] if avail else "c_free_drop", 0.0)
    return max(0.0, best[1]), best[0]


def project(rows: list[dict], *, c_free_now_gib: float, n_new_lock_sets: int,
            evidence_bytes_per_task: float) -> dict:
    """Conservative end-of-Q09 C: free projection (pure; unit-tested).

    rows: per dry-run task {"use_t_gib", "use_p_gib", "source"} = consumption of the target
    state (cold install of that task's lock set) and of the parent state (same lock set, warm).
      g_cold = max over tasks of max(0, use_t - use_p)  -> charged once per NEW lock set
      g_warm = max over tasks of use_p                  -> charged to EVERY container (upper bound)
    plus Windows-side evidence (4 evidence stages x 220 tasks x measured bytes) and 2 GiB safety.
    """
    if not rows:
        raise ValueError("no dry-run measurements")
    g_cold = max(max(0.0, r["use_t_gib"] - r["use_p_gib"]) for r in rows)
    g_warm = max(r["use_p_gib"] for r in rows)
    containers = sum(v for k, v in WORKLOAD.items() if k.endswith("_containers"))
    evidence = WORKLOAD["evidence_tasks"] * evidence_bytes_per_task / GIB * 4
    parts = {"new_lock_sets": n_new_lock_sets * g_cold, "warm_containers": containers * g_warm,
             "evidence": evidence, "safety": SAFETY_GIB}
    consumption = sum(parts.values())
    end = c_free_now_gib - consumption
    return {"g_cold_gib_per_new_lock_set": round(g_cold, 6), "g_warm_gib_per_container": round(g_warm, 6),
            "measurement_source": sorted({r.get("source", "?") for r in rows}),
            "containers_upper_bound": containers, "n_new_lock_sets": n_new_lock_sets,
            "components_gib": {k: round(v, 4) for k, v in parts.items()},
            "projected_consumption_gib": round(consumption, 3), "c_free_now_gib": round(c_free_now_gib, 3),
            "projected_c_free_at_q09_end_gib": round(end, 3), "plan_floor_gib": PLAN_FLOOR_GIB,
            "verdict": "PASS" if end >= PLAN_FLOOR_GIB else "S3_REQUIRED", "workload": WORKLOAD}
