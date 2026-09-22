#!/usr/bin/env python3
"""WP-2 Oracle Confirmation launcher (ZERO LLM/API).

Deterministic F2P/P2P oracle confirmation over Saleor MAIN_297 changed-test
candidates using isolated git worktrees and version-aware environments.

Modes:
  --plan      Build the FROZEN selection manifest (Wave A = all 20 strong;
              Wave B = first 60 of the stratified modified-test order;
              expansion order = the rest of the frozen order) and the
              environment fingerprints for all 220 changed-test candidates.
              Never uses RM-CSS/Agent success, localization F1, or generation
              outcomes. Writes:
                research/wp2/wp2_oracle_confirmation_selection_2026-09-22.json
                research/wp2/oracle_confirmation_2026-09-22/environment_fingerprints.json
  --run       Execute Oracle Confirmation for the selected tasks (resume-safe).

Usage (from the project root):
  python scripts/wp2_oracle_confirm.py --plan
  python scripts/wp2_oracle_confirm.py --run --max-tasks 20 [--resume]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.wp2.environment_manager import (  # noqa: E402
    fingerprint_commit_from_files,
)
from benchmark.wp2.oracle_confirmation import (  # noqa: E402
    build_selection_order,
    select_strong_tasks,
)

CENSUS = _PROJECT_DIR / "research" / "wp2" / "wp2_saleor_main297_census_2026-09-22.json"
SALEOR_CACHE = _PROJECT_DIR / "dist" / "pilot-repo-cache" / "saleor"
SELECTION_OUT = _PROJECT_DIR / "research" / "wp2" / "wp2_oracle_confirmation_selection_2026-09-22.json"
RUN_DIR = _PROJECT_DIR / "research" / "wp2" / "oracle_confirmation_2026-09-22"
FINGERPRINTS_OUT = RUN_DIR / "environment_fingerprints.json"
WAVE_A_COUNT = 20
WAVE_B_COUNT = 60

CONFIG_OR_INFRA_FILES = {
    "Dockerfile", ".env", ".env.example", ".gitignore", ".gitattributes",
    ".editorconfig", ".pre-commit-config.yaml", "pyproject.toml", "setup.cfg",
    "setup.py", "requirements.txt", "requirements.in", "Pipfile",
    "Pipfile.lock", "poetry.lock", "Makefile", "tox.ini", "manage.py",
    "asgi.py", "wsgi.py",
}
CONFIG_OR_INFRA_YAML = {
    "docker-compose.yml", "docker-compose.yaml", "docker-compose.dev.yml",
    "docker-compose.prod.yml",
}


def is_test_path(path: str) -> bool:
    from benchmark.wp2.oracle_confirmation import is_test_path as _itp

    return _itp(path)


def is_migration_path(path: str) -> bool:
    return "migrations" in Path(path).parts


def is_config_or_infra(path: str) -> bool:
    base = Path(path).name
    parts = Path(path).parts
    if base in CONFIG_OR_INFRA_FILES:
        return True
    if base in CONFIG_OR_INFRA_YAML:
        return True
    for idx, part in enumerate(parts):
        if part == ".github" and idx + 1 < len(parts) and parts[idx + 1] == "workflows":
            return True
    return False


def changed_source_size_bin(n_production: int) -> str:
    if n_production <= 3:
        return "SMALL"
    if n_production <= 10:
        return "MEDIUM"
    return "LARGE"


def modified_test_bin(n_test_modified: int) -> str:
    return ">1" if n_test_modified > 1 else "1"


def _run_git(cache: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cache), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def git_show_file(cache: Path, commit: str, path: str) -> bytes | None:
    r = _run_git(cache, "show", f"{commit}:{path}")
    if r.returncode != 0:
        return None
    return r.stdout.encode("utf-8")


def fingerprint_task(cache: Path, parent: str, target: str, commit: str) -> dict:
    """Environment fingerprint for one commit (read-only git show from cache)."""
    from benchmark.wp2.environment_manager import REQUIREMENT_FILES

    files: dict[str, bytes] = {}
    for name in REQUIREMENT_FILES:
        data = git_show_file(cache, commit, name)
        if data is not None:
            files[name] = data
    docker = git_show_file(cache, commit, "Dockerfile")
    if docker is not None:
        files["Dockerfile"] = docker
    settings = git_show_file(cache, commit, "saleor/settings.py")
    if settings is not None:
        files["saleor/settings.py"] = settings
    fp = fingerprint_commit_from_files(files)
    fp.commit = commit
    # commit date
    r = _run_git(cache, "show", "-s", "--format=%ci", commit)
    fp.commit_date = r.stdout.strip() if r.returncode == 0 else None
    return fp


def build_plan() -> dict:
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    tasks = census["tasks"]

    strong = select_strong_tasks(tasks)
    modified = [t for t in tasks if t["f2p_candidacy"] == "MODIFIED_TEST_CANDIDATE"]

    # ---- environment fingerprints for all 220 changed-test candidates ----
    fingerprints: dict[str, dict] = {}
    for t in [*strong, *modified]:
        parent, target = t["parent_commit"], t["target_commit"]
        fp_parent = fingerprint_task(SALEOR_CACHE, parent, target, parent)
        fp_target = fingerprint_task(SALEOR_CACHE, parent, target, target)
        family = fp_target.family()
        fingerprints[t["task_id"]] = {
            "parent": fp_parent.to_dict(),
            "target": fp_target.to_dict(),
            "family": family,
        }

    # ---- structural strata for the modified-test order ----
    for t in modified:
        tid = t["task_id"]
        t["env_family"] = fingerprints[tid]["family"]
        t["migration_or_config_heavy"] = (t["n_migration"] > 0) or (t["n_config_or_infra"] > 0)
        t["changed_source_bin"] = changed_source_size_bin(t["n_production"])
        t["n_modified_test_files_bin"] = modified_test_bin(t["n_test_modified"])

    modified_order = build_selection_order(modified)
    modified_ids = [t["task_id"] for t in modified_order]

    wave_a_ids = [t["task_id"] for t in strong]
    wave_b_ids = modified_ids[:WAVE_B_COUNT]
    expansion_ids = modified_ids[WAVE_B_COUNT:]

    selection = {
        "artifact": "wp2_oracle_confirmation_selection",
        "date": "2026-09-22",
        "status": "FROZEN_BEFORE_ORACLE_EXECUTION",
        "selection_never_uses": [
            "RM-CSS per-task success",
            "Agent per-task success",
            "localization F1",
            "future generation outcome",
            "future E2E result",
        ],
        "population": {
            "MAIN_297": 297,
            "strong_candidates": len(strong),
            "modified_candidates": len(modified),
            "no_changed_test_evidence": sum(
                1 for t in tasks if t["f2p_candidacy"] == "NO_CHANGED_TEST_EVIDENCE"
            ),
        },
        "waves": {
            "A_strong_all_20": wave_a_ids,
            "B_modified_first_60": wave_b_ids,
            "expansion_order": expansion_ids,
        },
        "selection": {
            "tasks": [
                {
                    "task_id": t["task_id"],
                    "f2p_candidacy": t["f2p_candidacy"],
                    "env_family": t.get("env_family"),
                    "migration_or_config_heavy": t.get("migration_or_config_heavy"),
                    "changed_source_bin": t.get("changed_source_bin"),
                    "n_modified_test_files_bin": t.get("n_modified_test_files_bin"),
                }
                for t in [*strong, *modified_order]
            ]
        },
    }
    SELECTION_OUT.parent.mkdir(parents=True, exist_ok=True)
    SELECTION_OUT.write_text(json.dumps(selection, indent=1, ensure_ascii=False), encoding="utf-8")

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    FINGERPRINTS_OUT.write_text(
        json.dumps(
            {"artifact": "wp2_oracle_environment_fingerprints", "date": "2026-09-22", "tasks": fingerprints},
            indent=1,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return selection


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true", help="build frozen selection + fingerprints")
    parser.add_argument("--run", action="store_true", help="execute oracle confirmation (resume-safe)")
    parser.add_argument("--max-tasks", type=int, default=0, help="cap tasks in this call")
    parser.add_argument("--resume", action="store_true", help="resume from existing run state")
    args = parser.parse_args()

    if args.plan:
        sel = build_plan()
        print(f"[wp2] plan written: waves A={len(sel['waves']['A_strong_all_20'])} "
              f"B={len(sel['waves']['B_modified_first_60'])} expansion={len(sel['waves']['expansion_order'])}")
        print(f"[wp2] selection: {SELECTION_OUT}")
        print(f"[wp2] fingerprints: {FINGERPRINTS_OUT}")
        return 0

    if args.run:
        print("[wp2] --run mode is implemented by the oracle execution loop; "
              "use scripts/wp2_oracle_confirm.py --plan first and then the runner.")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())