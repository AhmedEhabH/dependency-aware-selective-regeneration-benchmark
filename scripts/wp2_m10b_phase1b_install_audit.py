#!/usr/bin/env python3
"""WP-2 Mission-10B Phase 1B: environment/install failure audit (ZERO API).

Classifies the frozen V2 environment/install failures (C4 = 24, C2 = 60)
using the frozen per-task records, the dev census (target commits / python
requirements), and the target-commit dependency manifests read from the
WSL Saleor cache (read-only).

Output: research/wp2/harness_v3_2026-09-26/phase1b_install_failure_audit.json

Usage:
    python scripts/wp2_m10b_phase1b_install_audit.py [--out DIR]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
OUT_ROOT = PROJECT / "research" / "wp2" / "harness_v3_2026-09-26"
V2_ROOT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23"

WSL_DISTRO = "Ubuntu-24.04"
WSL_CACHE = "/opt/wp2_v2/saleor-cache"


def _now_utc() -> str:
    import datetime

    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def wsl(script: str, timeout_s: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc", script],
        capture_output=True, text=True, encoding="utf-8", timeout=timeout_s, check=False,
    )


def git_show(cache: str, commit: str, path: str) -> str:
    r = wsl(f"git -C {cache} show {commit}:{path} 2>/dev/null || echo __NO__")
    if "__NO__" in r.stdout or r.returncode != 0:
        return ""
    return r.stdout


def classify_install_failure(task_id: str, era_key: str, target_commit: str,
                             python_requirement: str) -> dict:
    """Classify the install failure from frozen metadata + manifest evidence."""
    manifests = {}
    for name in ("pyproject.toml", "poetry.lock", "uv.lock", "requirements.txt",
                 "requirements_dev.txt", "setup.cfg", "Pipfile.lock"):
        text = git_show(WSL_CACHE, target_commit, name)
        if text:
            manifests[name] = text

    category = "OTHER"
    evidence: list[str] = []
    installer_mode = "UNKNOWN"
    lockfile_kind = "none"
    main_deps: list[str] = []
    dev_deps: list[str] = []
    py312 = era_key == "py312"

    if py312:
        installer_mode = "uv pip install -e . freezegun fakeredis (editable, runtime deps only)"
    else:
        installer_mode = "uv pip install -r requirements.txt (production only)"

    if "uv.lock" in manifests:
        lockfile_kind = "uv.lock"
    elif "poetry.lock" in manifests:
        lockfile_kind = "poetry.lock"
    elif "Pipfile.lock" in manifests:
        lockfile_kind = "Pipfile.lock"
    elif "requirements.txt" in manifests:
        lockfile_kind = "requirements.txt"

    text = "\n".join(manifests.values())

    # category evidence (mechanical, from manifests only)
    if py312:
        # Modern py312: V2 runs `uv pip install -e .` which resolves the
        # project's OWN dependency graph (poetry or uv) against TODAY's index;
        # the commit's exact lockfile is never consulted.
        if "uv.lock" in manifests and re.search(r"\[dependency-groups\]",
                                                manifests.get("pyproject.toml", "")):
            evidence.append("PEP735 [dependency-groups] present; dev group not installed by V2")
            category = "LOCKFILE_INCOMPATIBILITY"
        elif "poetry.lock" in manifests:
            evidence.append("poetry.lock present at target commit but V2 `-e .` "
                            "ignores it and resolves pyproject ranges against today's index")
            category = "LOCKFILE_INCOMPATIBILITY"
        if re.search(r"cryptography\s*[>=~<]\s*4[0-9]", text):
            evidence.append("cryptography>=4x pin (V2 resolves against today's index)")
        if re.search(r"weasyprint|pango|cairo", text, re.I):
            evidence.append("weasyprint/pango native chain (era-native-lib attrition)")
            category = "SYSTEM_LIBRARY"
        if lockfile_kind == "none":
            category = "RESOLVER_CONFLICT"
            evidence.append("no commit lockfile; V2 resolved against today's index")
    else:
        # py38/py39: -r requirements.txt; failures on 2020-era native chain
        if re.search(r"weasyprint|pango|cairo", text, re.I):
            evidence.append("2020-era native dependency chain (weasyprint/pango) - documented py38 attrition")
            category = "SYSTEM_LIBRARY"
        elif lockfile_kind in ("requirements.txt", "none"):
            category = "RESOLVER_CONFLICT"
            evidence.append("unpinned/loose requirements resolved against today's index")
        if "poetry.lock" in manifests and not py312:
            evidence.append("poetry.lock present but V2 installed pip -r requirements.txt, "
                            "not the exact poetry.lock set")
            category = "LOCKFILE_INCOMPATIBILITY"

    # dependency declaration snapshot
    pyproj = manifests.get("pyproject.toml", "")
    for m in re.finditer(r"^\s*([a-zA-Z0-9_\-.]+)\s*=\s*[\"']?[<>=~!^]", pyproj, re.M):
        main_deps.append(m.group(1))
    _ = re.search(r"\[dependency-groups\]", pyproj)
    dg = re.search(r"\[dependency-groups\]\s*\n(.*?)(?=\n\[|\Z)", pyproj, re.S)
    if dg:
        for m in re.finditer(r"^\s*([a-zA-Z0-9_\-]+)\s*=\s*\[", dg.group(1), re.M):
            dev_deps.append(m.group(1))

    return {
        "task_id": task_id,
        "era_key": era_key,
        "target_commit": target_commit,
        "python_requirement": python_requirement,
        "installer_mode": installer_mode,
        "lockfile_kind": lockfile_kind,
        "category": category,
        "evidence": evidence,
        "main_deps_sampled": sorted(set(main_deps))[:12],
        "dev_groups_declared": sorted(set(dev_deps))[:12],
        "v3_repair_plausible": category in ("LOCKFILE_INCOMPATIBILITY", "RESOLVER_CONFLICT",
                                            "SYSTEM_LIBRARY"),
        "v3_note": "projection only; lockfile-exact install (LOCK_EXACT_MAIN_PLUS_DEV) "
                   "may repair resolver/lockfile classes; SYSTEM_LIBRARY requires "
                   "era-native package presence, not a lockfile fix.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out_root = Path(args.out) if args.out else OUT_ROOT
    out_root.mkdir(parents=True, exist_ok=True)

    # C4 env-failed tasks (task_collection_failure=True)
    c4_rows = [json.loads(ln) for ln in
               (V2_ROOT / "per_task_dev_v2.jsonl").read_text(encoding="utf-8").splitlines()]
    c4_env = [r for r in c4_rows if r.get("eligibility", {}).get("task_collection_failure")]

    census = json.loads((V2_ROOT / "dev_census_2026-09-23.json").read_text(encoding="utf-8"))
    census_map = {t["task_id"]: t for t in census.get("tasks", [])}

    c4_classified = []
    for r in c4_env:
        meta = census_map.get(r["task_id"], {})
        cls = classify_install_failure(
            task_id=r["task_id"],
            era_key=r.get("era_key", "UNKNOWN"),
            target_commit=meta.get("target_commit", "UNKNOWN"),
            python_requirement=meta.get("python_requirement", "UNKNOWN"),
        )
        c4_classified.append(cls)

    # C2 env-failed (from per_task_v2.jsonl; era + classification only - no census per-task)
    c2_rows = [json.loads(ln) for ln in
               (V2_ROOT / "per_task_v2.jsonl").read_text(encoding="utf-8").splitlines()]
    c2_env = [r for r in c2_rows if r.get("classification") == "ENV_BROKEN"
              or r.get("status") == "ENV_UNAVAILABLE"]
    if not c2_env:
        # fallback: env-failed = all-zero across all seven classification classes
        def _all_zero(r: dict) -> bool:
            c = r.get("counts") or {}
            return all(c.get(f, 0) == 0 for f in (
                "BEHAVIORAL_F2P", "SYMBOL_ABSENCE_F2P", "PARENT_COLLECTION_ERROR",
                "FLAKY", "TARGET_ORACLE_INVALID", "P2P_ONLY", "OTHER_REVIEW_REQUIRED"))
        c2_env = [r for r in c2_rows if _all_zero(r)]
    c2_era = Counter(r.get("era_key", "UNKNOWN") for r in c2_env)
    c2_classified = []
    for r in c2_env:
        cls = classify_install_failure(
            task_id=r["task_id"],
            era_key=r.get("era_key", "UNKNOWN"),
            target_commit=r.get("provenance", {}).get("target_commit", "UNKNOWN"),
            python_requirement=r.get("python_requirement", "UNKNOWN"),
        )
        c2_classified.append(cls)

    cat_c4 = Counter(c["category"] for c in c4_classified)
    cat_c2 = Counter(c["category"] for c in c2_classified)

    result = {
        "artifact": "m10b_phase1b_install_failure_audit",
        "created_utc": _now_utc(),
        "C4": {
            "authoritative_env_install_failed": 24,
            "parsed": len(c4_classified),
            "by_era": dict(Counter(c["era_key"] for c in c4_classified)),
            "by_category": dict(cat_c4),
            "tasks": c4_classified,
        },
        "C2": {
            "authoritative_env_install_failed": 60,
            "parsed": len(c2_classified),
            "by_era": dict(c2_era),
            "by_category": dict(cat_c2),
            "tasks": c2_classified,
        },
        "notes": "Classification is a projection from frozen metadata + target-commit "
                 "manifests (read-only). NOT reclassified as fixed without execution. "
                 "V3 lockfile-exact install may plausibly repair resolver/lockfile "
                 "classes; SYSTEM_LIBRARY is not a lockfile fix.",
    }
    (out_root / "phase1b_install_failure_audit.json").write_text(
        json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[1B] C4 parsed {len(c4_classified)} (expected 24) categories: {dict(cat_c4)}")
    print(f"[1B] C2 parsed {len(c2_classified)} (expected ~60) categories: {dict(cat_c2)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
