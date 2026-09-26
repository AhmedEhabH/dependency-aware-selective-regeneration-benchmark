#!/usr/bin/env python3
"""WP-2 Mission-10B Phase 1E: historical lockfile/dependency audit (ZERO API).

For each era/probe task, inspect the TARGET-commit dependency manifests from
the WSL Saleor cache (read-only) and record:
- V2 install mechanism;
- exact lockfile/pin authority available;
- main / dev / test dependencies;
- relevant exact locked versions;
- V2 extras;
- py312 ``-e .`` behavior vs the commit's lockfile (differing packages).

Output: research/wp2/harness_v3_2026-09-26/phase1e_lockfile_audit.json

Usage:
    python scripts/wp2_m10b_phase1e_lockfile_audit.py [--out DIR]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
OUT_ROOT = PROJECT / "research" / "wp2" / "harness_v3_2026-09-26"
V2_ROOT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23"

WSL_DISTRO = "Ubuntu-24.04"
WSL_CACHE = "/opt/wp2_v2/saleor-cache"

PROBE_TASKS = [
    "saleor-rc-c3b9e396b07d",
    "saleor-rc-e25cf9b4a837",
    "saleor-rc-74538ea00ce9",
    "saleor-rc-8f76ddc6267f",
]


def _now_utc() -> str:
    import datetime

    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def wsl(script: str, timeout_s: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc", script],
        capture_output=True, text=True, encoding="utf-8", timeout=timeout_s, check=False,
    )


def git_show(commit: str, path: str) -> str:
    r = wsl(f"git -C {WSL_CACHE} show {commit}:{path} 2>/dev/null || echo __NO__")
    if "__NO__" in r.stdout or r.returncode != 0:
        return ""
    return r.stdout


def _parse_poetry_lock(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    cur: dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith("[[package]]"):
            cur = {}
            continue
        m = re.match(r'name\s*=\s*"([^"]+)"', line)
        if m:
            cur["name"] = m.group(1)
            continue
        m = re.match(r'version\s*=\s*"([^"]+)"', line)
        if m:
            cur["version"] = m.group(1)
            continue
        m = re.match(r'category\s*=\s*"([^"]+)"', line)
        if m:
            cur["category"] = m.group(1)
            continue
        if cur.get("name") and cur.get("version"):
            out[cur["name"]] = cur["version"]
            cur = {}
    if cur.get("name") and cur.get("version"):
        out[cur["name"]] = cur["version"]
    return out


def _parse_uv_lock(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    cur: dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(r'^name\s*=\s*"([^"]+)"', line)
        if m:
            cur["name"] = m.group(1)
            continue
        m = re.match(r'^version\s*=\s*"([^"]+)"', line)
        if m:
            cur["version"] = m.group(1)
        if cur.get("name") and cur.get("version"):
            out[cur["name"]] = cur["version"]
            cur = {}
    return out


def audit_task(task_id: str, target_commit: str, era_key: str) -> dict:
    manifests: dict[str, str] = {}
    for name in ("pyproject.toml", "poetry.lock", "uv.lock", "requirements.txt",
                 "requirements_dev.txt", "requirements-test.txt", "setup.cfg"):
        text = git_show(target_commit, name)
        if text:
            manifests[name] = text

    pyproj = manifests.get("pyproject.toml", "")
    locked: dict[str, str] = {}
    lock_kind = "none"
    if "poetry.lock" in manifests:
        locked = _parse_poetry_lock(manifests["poetry.lock"])
        lock_kind = "poetry.lock"
    elif "uv.lock" in manifests:
        locked = _parse_uv_lock(manifests["uv.lock"])
        lock_kind = "uv.lock"

    main_deps: dict[str, str] = {}
    dev_deps: dict[str, str] = {}
    # poetry main
    m = re.search(r"\[tool\.poetry\.dependencies\](.*?)(?=\n\[|\Z)", pyproj, re.S)
    if m:
        for name, ver in re.findall(r"^\s*([a-zA-Z0-9_\-]+)\s*=\s*\"([^\"]+)\"", m.group(1), re.M):
            main_deps[name] = ver
    m = re.search(r"\[tool\.poetry\.dev-dependencies\](.*?)(?=\n\[|\Z)", pyproj, re.S)
    if m:
        for name, ver in re.findall(r"^\s*([a-zA-Z0-9_\-]+)\s*=\s*\"([^\"]+)\"", m.group(1), re.M):
            dev_deps[name] = ver
    # modern poetry group syntax [tool.poetry.group.<group>.dependencies]
    for gm in re.finditer(r"\[tool\.poetry\.group\.([\w\-]+)\.dependencies\](.*?)(?=\n\[|\Z)", pyproj, re.S):
        for name, ver in re.findall(r"^\s*([a-zA-Z0-9_\-]+)\s*=\s*\"([^\"]+)\"", gm.group(2), re.M):
            dev_deps[name] = ver
    # PEP735 dependency-groups
    m = re.search(r"\[dependency-groups\]\s*\n(.*?)(?=\n\[|\Z)", pyproj, re.S)
    if m:
        for name in re.findall(r"^\s*([a-zA-Z0-9_\-]+)\s*=\s*\[", m.group(1), re.M):
            dev_deps.setdefault(name, "")

    key_dev = [n for n in ("pytest-django-queries", "pytest-mock", "before_after",
                           "pytest-recording", "pytest-celery", "pytest-asyncio") if n in locked]

    v2_install = ("uv pip install -e . freezegun fakeredis" if era_key == "py312"
                  else "uv pip install -r requirements.txt")
    py312_diff = None
    if era_key == "py312" and lock_kind in ("poetry.lock", "uv.lock"):
        # V2 `-e .` resolves pyproject ranges against today's index; the locked
        # set is the historical authority. Record the locked key deps and note
        # the mechanism (a full diff requires a live resolver; not fabricated).
        py312_diff = {
            "mechanism": "V2 -e . resolves pyproject ranges at runtime; historical "
                         "lock is authoritative but was NOT used by V2",
            "locked_key_dev_deps": {n: locked[n] for n in key_dev},
        }

    return {
        "task_id": task_id,
        "era_key": era_key,
        "target_commit": target_commit,
        "v2_install_mechanism": v2_install,
        "lockfile_kind": lock_kind,
        "main_deps_n": len(main_deps),
        "main_deps_sampled": sorted(main_deps)[:15],
        "dev_deps_declared": sorted(dev_deps)[:15],
        "locked_dev_key": {n: locked.get(n) for n in key_dev},
        "locked_main_key": {n: locked.get(n) for n in
                            ("django", "cryptography", "pytest-django", "weasyprint")
                            if n in locked},
        "py312_vs_lock": py312_diff,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out_root = Path(args.out) if args.out else OUT_ROOT
    out_root.mkdir(parents=True, exist_ok=True)

    census = json.loads((V2_ROOT / "dev_census_2026-09-23.json").read_text(encoding="utf-8"))
    census_map = {t["task_id"]: t for t in census.get("tasks", [])}

    per_task = {}
    for line in (V2_ROOT / "per_task_dev_v2.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        per_task[r["task_id"]] = r

    tasks = []
    for tid in PROBE_TASKS:
        meta = census_map.get(tid, {})
        pt = per_task.get(tid, {})
        tasks.append(audit_task(tid, meta.get("target_commit", "UNKNOWN"),
                                pt.get("era_key", "UNKNOWN")))

    result = {
        "artifact": "m10b_phase1e_lockfile_audit",
        "created_utc": _now_utc(),
        "probe_tasks": tasks,
        "notes": "Lockfile-first rule: exact historical lock/pin, then historical "
                 "constraint, range only when NO lock/pin exists. V2 never installed "
                 "the project-declared dev/test group. V3 INSTALL_MODE candidates: "
                 "LOCK_EXACT_MAIN_PLUS_DEV (uv sync --frozen --group dev / poetry "
                 "exact lock main+dev) or fallback V2_MAIN_PLUS_EXACT_LOCKED_DEV.",
    }
    (out_root / "phase1e_lockfile_audit.json").write_text(
        json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    for t in tasks:
        print(f"[1E] {t['task_id']} {t['era_key']} lock={t['lockfile_kind']} "
              f"main={t['main_deps_n']} dev={t['dev_deps_declared']} "
              f"locked_dev_key={t['locked_dev_key']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
