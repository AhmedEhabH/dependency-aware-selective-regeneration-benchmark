#!/usr/bin/env python3
"""WP-2 zero-API Saleor MAIN_297 E2E census (deterministic, ZERO API).

For each of the exact 297 MAIN_297 task IDs this script:
  1. reads only that task's already-opened scientific case manifest;
  2. recovers parent and target commits;
  3. verifies both commits exist in the local Saleor repository cache;
  4. runs a read-only ``git diff --name-status parent target``;
  5. classifies every changed path with deterministic predicates;
  6. labels F2P *candidacy* only (never F2P_CONFIRMED);
  7. records whether an obvious test command can be statically inferred.

It never runs tests, never installs dependencies, never starts services and
never modifies the Saleor cache. It never touches the 786 sealed outcomes.

Usage:
  python scripts/wp2_saleor_e2e_census.py [--out-dir research/wp2]

Outputs:
  research/wp2/wp2_saleor_main297_census_2026-09-22.json
  research/wp2/wp2_saleor_main297_census_2026-09-22.csv
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent

MAIN297_MANIFEST = _PROJECT_DIR / "research" / "wp1b" / "wp1b_main_297_manifest.json"
SCIENTIFIC_CASE_DIR = (
    _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor" / "scientific"
)
SALEOR_CACHE = _PROJECT_DIR / "dist" / "pilot-repo-cache" / "saleor"
CALIBRATION_SUMMARY = (
    _PROJECT_DIR
    / "research"
    / "wp1b"
    / "calibration-3c-2026-09-22"
    / "wp1b_calibration_run_summary.json"
)

OUT_JSON = _PROJECT_DIR / "research" / "wp2" / "wp2_saleor_main297_census_2026-09-22.json"
OUT_CSV = _PROJECT_DIR / "research" / "wp2" / "wp2_saleor_main297_census_2026-09-22.csv"

CONFIG_OR_INFRA_PREDICATES = [
    "basename == Dockerfile",
    "basename in {.env, .env.example, .gitignore, .gitattributes, .editorconfig, .pre-commit-config.yaml}",
    "basename in {pyproject.toml, setup.cfg, setup.py, requirements.txt, requirements.in, "
    "Pipfile, Pipfile.lock, poetry.lock, Makefile, tox.ini}",
    "basename in {docker-compose.yml, docker-compose.yaml, docker-compose.dev.yml, docker-compose.prod.yml}",
    "any path segment == .github and next segment == workflows",
    "basename in {manage.py, asgi.py, wsgi.py}",
]


def is_test_path(path: str) -> bool:
    parts = Path(path).parts
    base = Path(path).name
    return "tests" in parts or base.startswith("test_") or base.endswith("_test.py")


def is_migration_path(path: str) -> bool:
    return "migrations" in Path(path).parts


def is_config_or_infra_path(path: str) -> bool:
    parts = Path(path).parts
    base = Path(path).name
    if base in {
        "Dockerfile",
        ".env",
        ".env.example",
        ".gitignore",
        ".gitattributes",
        ".editorconfig",
        ".pre-commit-config.yaml",
        "pyproject.toml",
        "setup.cfg",
        "setup.py",
        "requirements.txt",
        "requirements.in",
        "Pipfile",
        "Pipfile.lock",
        "poetry.lock",
        "Makefile",
        "tox.ini",
        "manage.py",
        "asgi.py",
        "wsgi.py",
    }:
        return True
    if base in {"docker-compose.yml", "docker-compose.yaml", "docker-compose.dev.yml", "docker-compose.prod.yml"}:
        return True
    for idx, part in enumerate(parts):
        if part == ".github" and idx + 1 < len(parts) and parts[idx + 1] == "workflows":
            return True
    return False


def classify_status(status_char: str) -> str:
    mapping = {"A": "added", "M": "modified", "D": "deleted", "R": "renamed", "C": "copied"}
    return mapping.get(status_char, "other")


def _run_git(cache: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cache), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def commit_exists(cache: Path, commit: str) -> bool:
    return _run_git(cache, "cat-file", "-e", f"{commit}^{{commit}}").returncode == 0


def load_manifest() -> list[str]:
    data = json.loads(MAIN297_MANIFEST.read_text(encoding="utf-8"))
    return list(data["task_ids"])


def load_calibration_ids() -> list[str]:
    data = json.loads(CALIBRATION_SUMMARY.read_text(encoding="utf-8"))
    return list(data.get("tasks", []))


def infer_test_command(changed_paths: list[dict]) -> dict:
    """Static inference only. Returns {'inferred': bool, 'commands': [...]}."""
    runnable = [
        p["path"]
        for p in changed_paths
        if p["test_file"] and p["status"] in ("added", "modified") and p["path"].endswith(".py")
    ]
    if not runnable:
        return {"inferred": False, "reason": "no added/modified python test path", "commands": []}
    commands = [f"pytest {p}" for p in runnable]
    return {"inferred": True, "reason": "pytest file-path inference (setup.cfg testpaths=saleor)", "commands": commands}


def census_one(cache: Path, task_id: str) -> dict:
    case_dir = SCIENTIFIC_CASE_DIR / task_id
    manifest_path = case_dir / "case_manifest.json"
    if not manifest_path.is_file():
        return {
            "task_id": task_id,
            "status": "ERROR",
            "error": "case_manifest.json missing",
            "parent_commit": None,
            "target_commit": None,
            "parent_available": False,
            "target_available": False,
            "n_changed": 0,
            "n_production": 0,
            "n_test": 0,
            "n_test_added": 0,
            "n_test_modified": 0,
            "n_test_deleted": 0,
            "n_migration": 0,
            "n_config_or_infra": 0,
            "f2p_candidacy": "METADATA_MATERIALIZATION_PROBLEM",
            "test_command": None,
        }
    record = json.loads(manifest_path.read_text(encoding="utf-8"))["record"]
    parent = record["parent_commit"]
    target = record["target_commit"]
    parent_ok = commit_exists(cache, parent)
    target_ok = commit_exists(cache, target)
    if not (parent_ok and target_ok):
        return {
            "task_id": task_id,
            "status": "ERROR",
            "error": "commit(s) missing in local Saleor cache",
            "parent_commit": parent,
            "target_commit": target,
            "parent_available": parent_ok,
            "target_available": target_ok,
            "n_changed": 0,
            "n_production": 0,
            "n_test": 0,
            "n_test_added": 0,
            "n_test_modified": 0,
            "n_test_deleted": 0,
            "n_migration": 0,
            "n_config_or_infra": 0,
            "f2p_candidacy": "METADATA_MATERIALIZATION_PROBLEM",
            "test_command": None,
        }
    diff = _run_git(cache, "diff", "--name-status", parent, target)
    if diff.returncode != 0:
        return {
            "task_id": task_id,
            "status": "ERROR",
            "error": f"git diff failed: {diff.stderr.strip()[:200]}",
            "parent_commit": parent,
            "target_commit": target,
            "parent_available": parent_ok,
            "target_available": target_ok,
            "n_changed": 0,
            "n_production": 0,
            "n_test": 0,
            "n_test_added": 0,
            "n_test_modified": 0,
            "n_test_deleted": 0,
            "n_migration": 0,
            "n_config_or_infra": 0,
            "f2p_candidacy": "METADATA_MATERIALIZATION_PROBLEM",
            "test_command": None,
        }
    changed_paths: list[dict] = []
    for line in diff.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status_char = parts[0][0]
        status = classify_status(status_char)
        path = parts[1] if len(parts) > 1 else "?"
        changed_paths.append(
            {
                "path": path,
                "status": status,
                "test_file": is_test_path(path),
                "migration_file": is_migration_path(path),
                "config_or_infra": is_config_or_infra_path(path),
            }
        )
    n_changed = len(changed_paths)
    n_test = sum(1 for p in changed_paths if p["test_file"])
    n_test_added = sum(1 for p in changed_paths if p["test_file"] and p["status"] == "added")
    n_test_modified = sum(1 for p in changed_paths if p["test_file"] and p["status"] == "modified")
    n_test_deleted = sum(1 for p in changed_paths if p["test_file"] and p["status"] == "deleted")
    n_migration = sum(1 for p in changed_paths if p["migration_file"])
    n_config_or_infra = sum(1 for p in changed_paths if p["config_or_infra"])
    n_production = sum(
        1 for p in changed_paths if not p["test_file"] and not p["migration_file"] and not p["config_or_infra"]
    )
    if n_test_added >= 1:
        f2p = "STRONG_F2P_CANDIDATE"
    elif n_test_modified >= 1:
        f2p = "MODIFIED_TEST_CANDIDATE"
    else:
        f2p = "NO_CHANGED_TEST_EVIDENCE"
    cmd = infer_test_command(changed_paths)
    test_command = cmd["commands"] if cmd["inferred"] else None
    return {
        "task_id": task_id,
        "status": "OK",
        "error": None,
        "parent_commit": parent,
        "target_commit": target,
        "parent_available": parent_ok,
        "target_available": target_ok,
        "n_changed": n_changed,
        "n_production": n_production,
        "n_test": n_test,
        "n_test_added": n_test_added,
        "n_test_modified": n_test_modified,
        "n_test_deleted": n_test_deleted,
        "n_migration": n_migration,
        "n_config_or_infra": n_config_or_infra,
        "f2p_candidacy": f2p,
        "test_command": test_command,
        "changed_paths": changed_paths,
    }


def self_checks(rows: list[dict], manifest_ids: set[str], calibration_ids: set[str]) -> list[str]:
    problems: list[str] = []
    if len(manifest_ids) != 297:
        problems.append(f"manifest does not contain exactly 297 unique IDs ({len(manifest_ids)})")
    overlap_cal = manifest_ids & calibration_ids
    if overlap_cal:
        problems.append(f"manifest contains calibration IDs: {sorted(overlap_cal)}")
    out_ids = {r["task_id"] for r in rows}
    if len(out_ids) != 297:
        problems.append(f"census output has {len(out_ids)} task IDs, expected 297")
    outside = out_ids - manifest_ids
    if outside:
        problems.append(f"census output has task IDs outside MAIN_297: {sorted(outside)[:5]}")
    missing = manifest_ids - out_ids
    if missing:
        problems.append(f"census output is missing MAIN_297 IDs: {sorted(missing)[:5]}")
    if any(r.get("f2p_candidacy") == "F2P_CONFIRMED" for r in rows):
        problems.append("a task was labelled F2P_CONFIRMED (forbidden)")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=str, default=str(_PROJECT_DIR / "research" / "wp2"))
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    task_ids = load_manifest()
    calibration_ids = load_calibration_ids()
    manifest_ids = set(task_ids)

    if not SALEOR_CACHE.is_dir():
        print(f"[wp2] ERROR: Saleor cache missing: {SALEOR_CACHE}")
        return 1

    rows = [census_one(SALEOR_CACHE, tid) for tid in task_ids]

    problems = self_checks(rows, manifest_ids, set(calibration_ids))
    for p in problems:
        print(f"[wp2] SELF-CHECK FAIL: {p}")
    if problems:
        print("[wp2] census aborted: self-checks failed")
        return 2

    counts: dict[str, int] = {}
    for r in rows:
        key = r["f2p_candidacy"]
        counts[key] = counts.get(key, 0) + 1
    summary = {
        "n_tasks": len(rows),
        "n_unique_ids": len({r["task_id"] for r in rows}),
        "counts_by_f2p_candidacy": counts,
        "totals": {
            "n_changed": sum(r["n_changed"] for r in rows),
            "n_production": sum(r["n_production"] for r in rows),
            "n_test": sum(r["n_test"] for r in rows),
            "n_test_added": sum(r["n_test_added"] for r in rows),
            "n_test_modified": sum(r["n_test_modified"] for r in rows),
            "n_test_deleted": sum(r["n_test_deleted"] for r in rows),
            "n_migration": sum(r["n_migration"] for r in rows),
            "n_config_or_infra": sum(r["n_config_or_infra"] for r in rows),
            "n_tasks_with_migration_or_config": sum(
                1 for r in rows if r["n_migration"] > 0 or r["n_config_or_infra"] > 0
            ),
        },
        "n_errors": sum(1 for r in rows if r["status"] != "OK"),
        "test_command_inferred_count": sum(1 for r in rows if r.get("test_command")),
    }
    payload = {
        "artifact": "wp2_saleor_main297_census",
        "date": "2026-09-22",
        "scope": "exact 297 MAIN_297 task IDs; already-opened Saleor case metadata; "
        "local cache only; 786 sealed outcomes untouched",
        "saleor_cache": str(SALEOR_CACHE),
        "method": "read-only git diff parent..target; deterministic path predicates; "
        "F2P candidacy only (never F2P_CONFIRMED)",
        "config_or_infra_predicates": CONFIG_OR_INFRA_PREDICATES,
        "test_file_predicate": "any path segment == tests OR basename starts with test_ OR basename ends with _test.py",
        "migration_file_predicate": "any path segment == migrations",
        "self_checks": {"passed": True, "problems": []},
        "summary": summary,
        "tasks": rows,
    }
    out_json = out_dir / "wp2_saleor_main297_census_2026-09-22.json"
    out_json.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")

    with open(out_dir / "wp2_saleor_main297_census_2026-09-22.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "task_id", "status", "parent_commit", "target_commit",
                "parent_available", "target_available", "n_changed", "n_production",
                "n_test", "n_test_added", "n_test_modified", "n_test_deleted",
                "n_migration", "n_config_or_infra", "f2p_candidacy", "test_command",
            ]
        )
        for r in rows:
            writer.writerow(
                [
                    r["task_id"], r["status"], r.get("parent_commit") or "",
                    r.get("target_commit") or "", r.get("parent_available", ""),
                    r.get("target_available", ""), r["n_changed"], r["n_production"],
                    r["n_test"], r["n_test_added"], r["n_test_modified"],
                    r["n_test_deleted"], r["n_migration"], r["n_config_or_infra"],
                    r["f2p_candidacy"], "; ".join(r["test_command"]) if r.get("test_command") else "",
                ]
            )

    manifest_sha = hashlib.sha256(MAIN297_MANIFEST.read_bytes()).hexdigest()
    print(f"[wp2] census complete: {len(rows)} tasks")
    print(f"[wp2] manifest sha256: {manifest_sha}")
    print(f"[wp2] f2p candidacy: {counts}")
    print(f"[wp2] wrote {out_json}")
    print("[wp2] wrote CSV")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
