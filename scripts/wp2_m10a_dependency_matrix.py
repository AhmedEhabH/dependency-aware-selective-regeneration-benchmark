#!/usr/bin/env python3
"""WP-2 Mission-10A Phase B/C: declared-vs-installed dependency matrix.

ZERO API. For each affected task (error-bearing nodes with MISSING_FIXTURE /
MODULE_NOT_FOUND / IMPORT_ERROR causes), resolve the candidate provider package
and classify the frozen V2 install state against the target-commit declaration.

Classification (Mission-10A section 10):
  A. DECLARED_AND_INSTALLED
  B. DECLARED_BUT_NOT_INSTALLED
  C. DECLARED_INSTALLED_BUT_PLUGIN_NOT_LOADED
  D. NOT_DECLARED_BY_PROJECT
  E. DECLARATION_AMBIGUOUS
  F. INSTALL_STATE_AMBIGUOUS

Usage:
    python scripts/wp2_m10a_dependency_matrix.py [--out DIR]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.m10a_audit import (  # noqa: E402
    DECLARATION_FILES,
    FIXTURE_TO_PACKAGE,
    resolve_declared_version,
)

SALEOR_CACHE = PROJECT / "dist" / "pilot-repo-cache" / "saleor"
V2_ROOT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23"
DEV_CENSUS = V2_ROOT / "dev_census_2026-09-23.json"
PER_TASK_DEV = V2_ROOT / "per_task_dev_v2.jsonl"
ERROR_RECORDS = PROJECT / "research" / "wp2" / "mission10a_env_audit_2026-09-26" / "error_records.jsonl"
OUT_ROOT = PROJECT / "research" / "wp2" / "mission10a_env_audit_2026-09-26"

# Frozen V2 installer facts (read from scripts/wp2_linux_dryrun.py, frozen).
V2_INSTALLER = {
    "mechanism": "container-start uv pip install (frozen Mission-07/08/09)",
    "tooling_install": [
        "pytest", "pytest-django==4.11.1", "pytest-socket", "pytest-xdist",
        "billiard<4.3", "setuptools<81", "wheel",
    ],
    "py38_py39_deps": "-r requirements.txt (PRODUCTION only)",
    "py312_deps": "-e . freezegun fakeredis (editable; project runtime deps only, no dev group)",
    "dev_test_group_installed": False,
    "pytest_mock_installed": False,
    "pytest_django_queries_installed": False,
}


def git_show(cache: Path, commit: str, path: str) -> str | None:
    """Return file text at commit from the saleor cache repo, or None."""
    r = subprocess.run(
        ["git", "-C", str(cache), "show", f"{commit}:{path}"],
        capture_output=True, text=True, encoding="utf-8", timeout=120, check=False,
    )
    if r.returncode != 0:
        return None
    return r.stdout


def list_manifest_files(cache: Path, commit: str) -> list[str]:
    r = subprocess.run(
        ["git", "-C", str(cache), "ls-tree", "--name-only", commit],
        capture_output=True, text=True, encoding="utf-8", timeout=120, check=False,
    )
    if r.returncode != 0:
        return []
    return [ln for ln in r.stdout.splitlines() if ln in DECLARATION_FILES]


def era_from_python_requirement(req: str) -> str:
    req = (req or "").strip()
    if req in ("~3.8", ">=3.8,<3.9", "3.8"):
        return "py38"
    if req in ("~3.9", ">=3.9,<3.10", "3.9"):
        return "py39"
    if req in ("~3.12", ">=3.12,<3.13", "3.12"):
        return "py312"
    return "UNKNOWN"


def load_task_meta() -> tuple[dict[str, dict], dict[str, str]]:
    """Return (task->{parent,target,python_requirement}, task->era_key).

    Merges DEV census (parent/target/python) with era_key from DEV and MAIN
    per-task evidence so C2-only affected tasks resolve their era too.
    """
    census = json.loads(DEV_CENSUS.read_text(encoding="utf-8"))
    tasks: dict[str, dict] = {}
    for t in census["tasks"]:
        tasks[t["task_id"]] = dict(t)
    era: dict[str, str] = {}
    for path in (PER_TASK_DEV, V2_ROOT / "per_task_v2.jsonl"):
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                r = json.loads(line)
                era[r["task_id"]] = r.get("era_key", "")
                tasks.setdefault(r["task_id"], {})
                tasks[r["task_id"]].setdefault("python_requirement", r.get("python_requirement", ""))
    # MAIN census fallback for parent/target/py of C2-only affected tasks
    main_census = PROJECT / "research" / "wp2" / "wp2_saleor_main297_census_2026-09-22.json"
    if main_census.exists():
        mc = json.loads(main_census.read_text(encoding="utf-8"))
        for t in mc.get("tasks", []):
            tid = t.get("task_id")
            if not tid:
                continue
            tasks.setdefault(tid, {})
            for k in ("parent_commit", "target_commit"):
                if t.get(k) and not tasks[tid].get(k):
                    tasks[tid][k] = t[k]
            if not tasks[tid].get("python_requirement"):
                tasks[tid]["python_requirement"] = t.get("python_requirement", "")
    return tasks, era


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out_root = Path(args.out) if args.out else OUT_ROOT
    out_root.mkdir(parents=True, exist_ok=True)

    tasks_meta, era_map = load_task_meta()

    # Affected tasks: those with MISSING_FIXTURE / MODULE_NOT_FOUND in records
    affected: dict[str, Counter] = defaultdict(Counter)
    with ERROR_RECORDS.open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["taxonomy"].startswith(("MISSING_FIXTURE", "MODULE_NOT_FOUND")):
                affected[r["task_id"]][r["taxonomy"]] += 1

    rows: list[dict] = []
    for task_id in sorted(affected):
        meta = tasks_meta.get(task_id, {})
        target = meta.get("target_commit")
        parent = meta.get("parent_commit")
        era_key = era_map.get(task_id) or era_from_python_requirement(meta.get("python_requirement", ""))
        manifests: dict[str, str] = {}
        if target:
            for path in list_manifest_files(SALEOR_CACHE, target):
                txt = git_show(SALEOR_CACHE, target, path)
                if txt is not None:
                    manifests[path] = txt
        causes = dict(affected[task_id])
        row = {
            "task_id": task_id,
            "era_key": era_key,
            "target_commit": target,
            "parent_commit": parent,
            "python_requirement": meta.get("python_requirement", ""),
            "commit_year": meta.get("commit_year"),
            "dependency_management": sorted({p.split(".")[-1] for p in manifests}),
            "lockfile_present": any(p in ("poetry.lock", "uv.lock", "Pipfile.lock") for p in manifests),
            "manifest_files": sorted(manifests),
            "causes": causes,
            "fixture_map": {},
        }
        # Per missing fixture/module, resolve candidate package + declaration.
        for cause, cnt in causes.items():
            kind, _, name = cause.partition(":")
            if kind == "MISSING_FIXTURE":
                pkg = FIXTURE_TO_PACKAGE.get(name)
                if not pkg:
                    row["fixture_map"][cause] = {
                        "candidate_package": None, "confidence": "AMBIGUOUS",
                        "declared": False, "install_state": "UNKNOWN_PROVIDER", "count": cnt,
                    }
                    continue
            elif kind == "MODULE_NOT_FOUND":
                pkg = name
            else:
                continue
            decl = resolve_declared_version(pkg, manifests) if manifests else None
            # Install state classification under frozen V2 logic.
            if decl is None or not decl.declared:
                install_state = "D_NOT_DECLARED_BY_PROJECT"
            elif era_key == "py312":
                # -e . installs runtime deps only; dev group not installed.
                installed = decl.group == "main"
                install_state = "A_DECLARED_AND_INSTALLED" if installed else "B_DECLARED_BUT_NOT_INSTALLED"
            else:
                # -r requirements.txt production only.
                installed = decl.mechanism == "pip-requirements" and "dev" not in (decl.file or "")
                install_state = "A_DECLARED_AND_INSTALLED" if installed else "B_DECLARED_BUT_NOT_INSTALLED"
            if decl is None or not decl.declared:
                install_state = "D_NOT_DECLARED_BY_PROJECT"
            elif installed:
                install_state = "A_DECLARED_AND_INSTALLED"
            else:
                install_state = "B_DECLARED_BUT_NOT_INSTALLED"
            row["fixture_map"][cause] = {
                "candidate_package": pkg,
                "confidence": "PROVEN" if decl and decl.declared else "AMBIGUOUS",
                "declared": bool(decl and decl.declared),
                "declaration_file": decl.file if decl else None,
                "mechanism": decl.mechanism if decl else None,
                "group": decl.group if decl else None,
                "version_spec": decl.version_spec if decl else None,
                "locked_version": decl.locked_version if decl else None,
                "install_state": install_state,
                "count": cnt,
            }
        rows.append(row)

    # Aggregate
    state_counter: Counter[str] = Counter()
    for row in rows:
        for m in row["fixture_map"].values():
            state_counter[m["install_state"]] += 1

    out = {
        "artifact": "dependency_declaration_matrix",
        "schema_version": "mission10a-declaration-matrix-v1",
        "created_utc": _now_utc(),
        "v2_installer": V2_INSTALLER,
        "install_state_aggregate": dict(state_counter),
        "tasks_affected": len(rows),
        "tasks": rows,
    }
    (out_root / "dependency_declaration_matrix.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[matrix] tasks_affected={len(rows)}")
    for k, v in sorted(state_counter.items()):
        print(f"  {k}: {v}")
    return 0


def _now_utc() -> str:
    import datetime

    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


if __name__ == "__main__":
    raise SystemExit(main())
