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
from benchmark.wp2.paths import (  # noqa: E402
    envs_root,
    saleor_cache_venv_python,
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


def fingerprint_task(cache: Path, commit: str) -> dict:
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
        fp_parent = fingerprint_task(SALEOR_CACHE, parent)
        fp_target = fingerprint_task(SALEOR_CACHE, target)
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
    parser.add_argument("--task-id", type=str, default="", help="run a single task id (dry run)")
    args = parser.parse_args()

    if args.plan:
        sel = build_plan()
        print(f"[wp2] plan written: waves A={len(sel['waves']['A_strong_all_20'])} "
              f"B={len(sel['waves']['B_modified_first_60'])} expansion={len(sel['waves']['expansion_order'])}")
        print(f"[wp2] selection: {SELECTION_OUT}")
        print(f"[wp2] fingerprints: {FINGERPRINTS_OUT}")
        return 0

    if args.run:
        from benchmark.wp2.oracle_runner import OracleConfirmationRunner

        runner = OracleConfirmationRunner(cache=SALEOR_CACHE)
        rc = run_oracle(runner, args=args)
        return rc

    parser.print_help()
    return 1


def run_oracle(runner, args) -> int:
    """Execute Oracle Confirmation for the selected tasks (resume-safe).

    Runs Wave A (all 20 strong), then Wave B (first 60 of the frozen
    modified-test order). Per task: isolated worktrees, test-only patch on
    parent, 3x target + 3x parent+testpatch runs, taxonomy classification,
    persisted to per_task.jsonl / per_test.jsonl.
    """
    from benchmark.wp2.oracle_runner import (
        collect_test_files,
    )

    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    by_id = {t["task_id"]: t for t in census["tasks"]}
    selection = json.loads(SELECTION_OUT.read_text(encoding="utf-8"))
    waves = selection["waves"]

    if args.task_id:
        wave_tasks = [args.task_id]
    else:
        wave_tasks = list(waves["A_strong_all_20"]) + list(waves["B_modified_first_60"])
        if args.max_tasks > 0:
            wave_tasks = wave_tasks[: args.max_tasks]

    RUN_DIR.mkdir(parents=True, exist_ok=True)
    per_task_path = RUN_DIR / "per_task.jsonl"
    per_test_path = RUN_DIR / "per_test.jsonl"
    run_state_path = RUN_DIR / "run_state.json"

    done: dict[str, str] = {}
    if per_task_path.exists():
        for line in per_task_path.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            done[rec["task_id"]] = rec.get("classification", rec.get("status", ""))
    if args.resume and args.task_id and args.task_id in done:
        print(f"[wp2] resume: {args.task_id} already done ({done[args.task_id]})")
        return 0

    total = len(wave_tasks)
    counts: dict[str, int] = {}
    n_behavioral = 0
    started = time.monotonic()
    with open(per_task_path, "a", encoding="utf-8") as pt, open(per_test_path, "a", encoding="utf-8") as ptest:
        for idx, tid in enumerate(wave_tasks, 1):
            if tid in done:
                continue
            print(f"[wp2] oracle {idx}/{total} {tid}")
            t = by_id.get(tid)
            if t is None:
                rec = {"task_id": tid, "status": "NOT_IN_CENSUS"}
                pt.write(json.dumps(rec) + "\n")
                continue
            parent, target = t["parent_commit"], t["target_commit"]
            test_files = collect_test_files(SALEOR_CACHE, parent, target)
            try:
                result = confirm_one(
                    runner,
                    tid,
                    parent,
                    target,
                    test_files,
                    per_test_path=ptest,
                )
            except Exception as exc:
                result = {
                    "task_id": tid,
                    "status": "ERROR",
                    "classification": "OTHER_REVIEW_REQUIRED",
                    "error": str(exc)[:500],
                    "n_behavioral_f2p": 0,
                    "n_symbol_absence_f2p": 0,
                    "n_p2p": 0,
                }
            cls = result.get("classification", result.get("status", "UNKNOWN"))
            counts[cls] = counts.get(cls, 0) + 1
            if cls == "BEHAVIORAL_F2P":
                n_behavioral += 1
            result["wave"] = "A" if tid in waves["A_strong_all_20"] else "B"
            pt.write(json.dumps(result, ensure_ascii=False) + "\n")
            done[tid] = cls
            print(
                f"[wp2] ORACLE: attempted {idx}/{total} selected | "
                f"behavioral F2P {n_behavioral} | {cls}"
            )
            if time.monotonic() - started > 12 * 3600:
                print("[wp2] ORACLE_CONFIRMATION_TIMEBOX_COMPLETE")
                break

    state = {
        "artifact": "wp2_oracle_confirmation_run_state",
        "date": "2026-09-22",
        "status": "COMPLETE",
        "counts": counts,
        "n_behavioral_f2p": n_behavioral,
        "n_attempted": len(wave_tasks),
        "wave_a": list(waves["A_strong_all_20"]),
        "wave_b": list(waves["B_modified_first_60"]),
    }
    run_state_path.write_text(json.dumps(state, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[wp2] run state: {run_state_path}")
    return 0


def confirm_one(
    runner,
    tid: str,
    parent: str,
    target: str,
    test_files: list[str],
    per_test_path,
) -> dict:
    """Confirm one task: 3x target + 3x parent+testpatch, classify nodes."""
    from benchmark.wp2.oracle_runner import (
        OracleRunError,
        _apply_patch,
        _patch_applies,
        derive_test_only_patch_from_cache,
    )

    wt_target = f"{tid}_target"
    wt_parent = f"{tid}_parent"
    patch_bytes = derive_test_only_patch_from_cache(SALEOR_CACHE, parent, target)
    patch_sha = hashlib.sha256(patch_bytes).hexdigest()

    try:
        target_wt = runner._add_worktree(wt_target, target)
        parent_wt = runner._add_worktree(wt_parent, parent)
    except OracleRunError as exc:
        return {
            "task_id": tid,
            "status": "ERROR",
            "classification": "ENV_BROKEN",
            "error": f"worktree: {exc}",
            "test_patch_sha256": patch_sha,
            "n_behavioral_f2p": 0,
            "n_symbol_absence_f2p": 0,
            "n_p2p": 0,
        }

    try:
        # Build/select the per-family python (commit-era venv when available).
        family_python = build_family_python(tid, target_wt)
        if family_python is None:
            return {
                "task_id": tid,
                "status": "ENV_UNAVAILABLE",
                "classification": "ENV_BROKEN",
                "error": "no compatible interpreter/venv could be constructed for this commit era",
                "test_patch_sha256": patch_sha,
                "n_behavioral_f2p": 0,
                "n_symbol_absence_f2p": 0,
                "n_p2p": 0,
            }

        # test discovery on target
        discovery = runner.discover_test_nodes(target_wt, test_files, family_python)
        node_ids = discovery["nodes"]
        if not node_ids:
            return {
                "task_id": tid,
                "status": "COLLECTION_FAILED",
                "classification": "ENV_BROKEN",
                "error": f"no test nodes collected: "
                f"{discovery['stderr_tail'][-1000:] or discovery['stdout_tail'][-1000:]}",
                "test_patch_sha256": patch_sha,
                "n_behavioral_f2p": 0,
                "n_symbol_absence_f2p": 0,
                "n_p2p": 0,
            }

        # apply test-only patch to parent
        patch_path = runner.worktrees_root / f"{tid}_test_only.patch"
        if not _patch_applies(parent_wt, patch_bytes, patch_path):
            return {
                "task_id": tid,
                "status": "TEST_PATCH_APPLY_FAIL",
                "classification": "TEST_PATCH_APPLY_FAIL",
                "error": "test-only patch does not apply to parent",
                "test_patch_sha256": patch_sha,
                "n_behavioral_f2p": 0,
                "n_symbol_absence_f2p": 0,
                "n_p2p": 0,
            }
        _apply_patch(parent_wt, patch_path)

        # 3x target runs
        target_runs = []
        for i in range(3):
            res = runner.run_evaluator(target_wt, node_ids, family_python, runner.worktrees_root / f"{tid}_t{i}.xml")
            target_runs.append(res)

        # 3x parent+testpatch runs
        parent_runs = []
        for i in range(3):
            res = runner.run_evaluator(parent_wt, node_ids, family_python, runner.worktrees_root / f"{tid}_p{i}.xml")
            parent_runs.append(res)

        return classify_task(
            tid, node_ids, target_runs, parent_runs, patch_sha, test_files, per_test_path
        )
    finally:
        runner._remove_worktree(wt_target)
        runner._remove_worktree(wt_parent)


def build_family_python(tid: str, target_wt: Path):
    """Return the python executable for this task's env family.

    Uses the isolated per-family venv (built once per fingerprint family by
    scripts; uv creates it lazily). The interpreter is resolved from the
    fingerprint's Python requirement (era-aware). Falls back to the cache venv
    for HEAD-era tasks. Returns None if no environment can be constructed.
    """
    from benchmark.wp2.environment_manager import (
        build_venv,
    )
    from benchmark.wp2.paths import resolve_python

    fingerprints = json.loads(FINGERPRINTS_OUT.read_text(encoding="utf-8"))["tasks"]
    fp = fingerprints.get(tid)
    if fp is not None:
        family = fp["family"].split("::")[-1]
        env_root = ENVS_ROOT
        py_req = fp["target"].get("python_requirement") or "UNKNOWN"
        interpreter = resolve_python(_minor_from_requirement(py_req))
        if interpreter is None:
            print(f"[wp2] no interpreter for {tid} python requirement '{py_req}'")
            return None
        try:
            venv = build_venv(env_root, family, target_wt, interpreter)
            return venv / "Scripts" / "python.exe"
        except Exception as exc:
            print(f"[wp2] env build failed for {tid}: {str(exc)[:300]}")
            return None
    if ORACLE_PYTHON.exists():
        return ORACLE_PYTHON
    return None


def _minor_from_requirement(req: str) -> str:
    """Extract major.minor from a PEP-508 python requirement, defaulting to 3.12."""
    import re

    m = re.search(r"(3\.\d{1,2})", req)
    if m:
        return m.group(1)
    return "3.12"


def classify_task(
    tid: str,
    node_ids: list[str],
    target_runs: list[dict],
    parent_runs: list[dict],
    patch_sha: str,
    test_files: list[str],
    per_test_path,
) -> dict:
    """Classify per-node and per-task under the frozen taxonomy."""
    from benchmark.wp2.oracle_confirmation import (
        classify_failure_reason,
        task_eligibility,
    )

    # Build per-node outcome vectors.
    node_outcomes: dict[str, dict] = {}
    for nid in node_ids:
        t_out = []
        p_out = []
        for tr in target_runs:
            t_out.append(tr["junit"].get(nid, "missing"))
        for pr in parent_runs:
            p_out.append(pr["junit"].get(nid, "missing"))
        node_outcomes[nid] = {"target": t_out, "parent": p_out}

    n_behavioral = 0
    n_symbol = 0
    n_p2p = 0
    n_flaky = 0
    n_target_invalid = 0
    n_other = 0
    target_oracle_stable = True
    env_valid = True

    for nid, out in node_outcomes.items():
        if "missing" in out["target"] or "missing" in out["parent"]:
            # a node missing from JUnit on either side -> cannot classify cleanly
            reason = "OTHER_REVIEW_REQUIRED"
        else:
            reason = classify_failure_reason(
                out["target"],
                out["parent"],
                parent_failure_text="",
            )
        if reason == "BEHAVIORAL_F2P":
            n_behavioral += 1
        elif reason == "SYMBOL_ABSENCE_F2P":
            n_symbol += 1
        elif reason == "P2P_ONLY":
            n_p2p += 1
        elif reason == "FLAKY":
            n_flaky += 1
            target_oracle_stable = False
        elif reason == "TARGET_ORACLE_INVALID":
            n_target_invalid += 1
            target_oracle_stable = False
        elif reason == "ENV_BROKEN":
            env_valid = False
        else:
            n_other += 1
            target_oracle_stable = False

        per_test_path.write(
            json.dumps(
                {
                    "task_id": tid,
                    "node_id": nid,
                    "target_outcomes": out["target"],
                    "parent_outcomes": out["parent"],
                    "classification": reason,
                },
                ensure_ascii=False,
            )
            + "\n"
        )

    flags = task_eligibility(
        n_behavioral_f2p=n_behavioral,
        n_symbol_absence_f2p=n_symbol,
        n_p2p=n_p2p,
        target_oracle_stable=target_oracle_stable,
        environment_valid=env_valid,
    )
    if n_behavioral >= 1 and flags["PRIMARY_BEHAVIORAL_F2P_ELIGIBLE"]:
        classification = "BEHAVIORAL_F2P"
    elif n_symbol >= 1 and flags["EXTENDED_F2P_ELIGIBLE"]:
        classification = "SYMBOL_ABSENCE_F2P"
    elif n_p2p >= 1 and not n_behavioral and not n_symbol and target_oracle_stable:
        classification = "P2P_ONLY"
    elif n_flaky > 0:
        classification = "FLAKY"
    elif not target_oracle_stable:
        classification = "TARGET_ORACLE_INVALID"
    elif not env_valid:
        classification = "ENV_BROKEN"
    else:
        classification = "OTHER_REVIEW_REQUIRED"

    return {
        "task_id": tid,
        "status": "DONE",
        "classification": classification,
        "test_patch_sha256": patch_sha,
        "n_nodes": len(node_ids),
        "n_behavioral_f2p": n_behavioral,
        "n_symbol_absence_f2p": n_symbol,
        "n_p2p": n_p2p,
        "n_flaky": n_flaky,
        "n_target_oracle_invalid": n_target_invalid,
        "n_other": n_other,
        "target_oracle_stable": target_oracle_stable,
        "environment_valid": env_valid,
        "test_files": test_files,
    }


ORACLE_PYTHON = saleor_cache_venv_python()

ENVS_ROOT = envs_root()


if __name__ == "__main__":
    raise SystemExit(main())
