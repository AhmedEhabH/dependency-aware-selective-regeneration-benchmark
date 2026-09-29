#!/usr/bin/env python3
"""WP-2 E2E v2.2 environment doctor (brain-authored kit; hash-verified).

--offline : local environment only (no OpenRouter request of any kind)
--paid    : offline checks + API key present + credit >= $5 + pricing <= 2x frozen
            (credit/pricing use read-only OpenRouter endpoints; zero model calls)
Exit 0 = every check PASS; 1 = at least one FAIL. Evidence: <v22>/doctor/doctor_<mode>_<stamp>.json
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.e2e_v22.common import (  # noqa: E402
    EVALUATOR_SETS,
    V1_ROOT,
    V22_ROOT,
    WSL_DISTRO,
    env_identity,
)

MIN_FREE_GIB = 20.0
MIN_CREDIT_USD = 5.0
MAX_PRICE_RATIO = 2.0
FROZEN_PROMPT, FROZEN_COMPLETION = 0.30, 1.00
WSL_CACHE = "/opt/wp2_v2/saleor-cache"


def _run(cmd: list[str], timeout: int = 180) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout)


def live_pricing(fetch=None) -> dict[str, Any]:
    """Read-only OpenRouter endpoint metadata for the pinned provider. Fail-closed."""
    import urllib.request
    if fetch is None:
        def fetch(url: str) -> dict:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
    data = fetch("https://openrouter.ai/api/v1/models/qwen/qwen3-coder/endpoints")
    endpoints = (data.get("data") or {}).get("endpoints") or []
    ep = next((e for e in endpoints if e.get("tag") == "deepinfra/turbo"), None)
    if ep is None:
        return {"ok": False, "value": "deepinfra/turbo endpoint not listed",
                "tags": [e.get("tag") for e in endpoints]}
    pr = ep.get("pricing") or {}
    pp = float(pr.get("prompt", "nan")) * 1e6
    cp = float(pr.get("completion", "nan")) * 1e6
    ratio = max(pp / FROZEN_PROMPT, cp / FROZEN_COMPLETION)
    return {"prompt_per_1m": pp, "completion_per_1m": cp, "ratio": round(ratio, 4),
            "status": ep.get("status"), "uptime_last_30m": ep.get("uptime_last_30m"),
            "quantization": ep.get("quantization"),
            "ok": ratio == ratio and ratio <= MAX_PRICE_RATIO}


def offline_checks() -> dict[str, Any]:
    c: dict[str, Any] = {}
    c["python_version"] = {"value": sys.version.split()[0],
                           "ok": sys.version_info[:2] in ((3, 11), (3, 12))}
    free = shutil.disk_usage(PROJECT).free / 2**30
    c["disk_free_gib"] = {"value": round(free, 1), "ok": free >= MIN_FREE_GIB}
    try:
        r = _run(["wsl", "-d", WSL_DISTRO, "--", "docker", "version", "--format",
                  "{{.Server.Version}}"])
        c["docker_in_wsl"] = {"value": r.stdout.strip(), "ok": r.returncode == 0}
    except Exception as exc:
        c["docker_in_wsl"] = {"value": str(exc), "ok": False}
    try:
        from benchmark.wp2.harness_v3 import ensure_postgres_running
        ensure_postgres_running()
        c["postgres_ready"] = {"ok": True}
    except Exception as exc:
        c["postgres_ready"] = {"value": str(exc)[:300], "ok": False}
    try:
        env = env_identity()
        c["images_present"] = {"value": env, "ok": not env["errors"]}
    except Exception as exc:
        c["images_present"] = {"value": str(exc)[:300], "ok": False}
    try:
        from benchmark.wp2.harness_v3 import clock_preflight
        clk = clock_preflight()
        c["clock"] = {"value": clk.get("verdict"), "ok": clk.get("verdict") != "CLOCK_BLOCKED"}
    except Exception as exc:
        c["clock"] = {"value": str(exc)[:300], "ok": False}
    try:
        r = _run(["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
                  f"test -d {WSL_CACHE}/.git && echo OK"])
        c["saleor_cache"] = {"ok": "OK" in r.stdout}
    except Exception as exc:
        c["saleor_cache"] = {"value": str(exc), "ok": False}
    c["evaluator_sets_present"] = {"ok": EVALUATOR_SETS.exists()}
    c["v1_scopes_present"] = {"ok": all((V1_ROOT / "scopes" / f).exists() for f in (
        "scopes_GOLD_HARD.json", "scopes_RMCSS_HARD.json", "scopes_AGENT_HARD.json",
        "scopes_PLACEBO_HARD.json"))}
    return c


def paid_checks() -> dict[str, Any]:
    c: dict[str, Any] = {}
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    c["api_key_present"] = {"ok": bool(key)}
    out = PROJECT / "_workspace" / "tmp" / "v22_key_usage.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        _run([sys.executable, "scripts/wp1b_openrouter_key_usage.py", "--out", str(out)])
        usage = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
        credit = usage.get("remaining_usd_min_of_sources") or usage.get("limit_remaining_usd")
        c["credit_usd"] = {"value": credit,
                           "ok": credit is not None and float(credit) >= MIN_CREDIT_USD}
    except Exception as exc:
        c["credit_usd"] = {"value": str(exc)[:200], "ok": False}
    try:
        c["pricing"] = live_pricing()
    except Exception as exc:
        c["pricing"] = {"value": f"{type(exc).__name__}: {exc}"[:200], "ok": False}
    return c


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--offline", action="store_true")
    g.add_argument("--paid", action="store_true")
    a = ap.parse_args(argv)
    checks = offline_checks()
    if a.paid:
        checks.update(paid_checks())
    mode = "paid" if a.paid else "offline"
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    rep = {"artifact": "doctor_v22", "mode": mode, "utc": stamp, "checks": checks,
           "pass": all(v.get("ok") for v in checks.values())}
    (V22_ROOT / "doctor").mkdir(parents=True, exist_ok=True)
    (V22_ROOT / "doctor" / f"doctor_{mode}_{stamp}.json").write_text(
        json.dumps(rep, indent=1, default=str), encoding="utf-8")
    for k, v in checks.items():
        print(f"DOCTOR {'PASS' if v.get('ok') else 'FAIL'} {k} {v.get('value', '')!s:.160}")
    return 0 if rep["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
