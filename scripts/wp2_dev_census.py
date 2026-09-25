#!/usr/bin/env python3
"""WP-2 DEV 150 zero-model census + DEV split freeze (amendment F) - ZERO API.

Zero-model census across the frozen DEV pool (DEV_TRAIN=120 + DEV_VALIDATION=30):
- added tests / modified tests / no-changed-test evidence;
- migration/config complexity;
- commit year / environment family (python requirement).

Also freezes the deterministic salted split of DEV_TRAIN into
DEV_TRAIN_ENG (~40) and DEV_TRAIN_ASSAY_HOLDOUT (~80). DEV_VALIDATION=30 stays
separate. No generation/Smoke/Pilot. INTERNAL_TEST=80 and the sealed RESERVE
are never referenced.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.dev_split_v2 import build_dev_split_artifact  # noqa: E402
from benchmark.wp2.oracle_semantics_v2 import is_test_path_v2  # noqa: E402

CACHE = PROJECT / "dist" / "pilot-repo-cache" / "saleor"
SCIENTIFIC = PROJECT / "benchmark_data" / "real_commit_impact_saleor" / "scientific"
SPLIT = PROJECT / "benchmark_data" / "real_commit_impact_saleor" / "split_freeze_saleor.json"
OUT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23"


def git(cache: Path, *args: str) -> subprocess.CompletedProcess[str]:
    cmd = ["git", "-C", str(cache), *args]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=False)


def commit_year(cache: Path, commit: str) -> int | None:
    r = git(cache, "log", "-1", "--format=%ct", commit)
    if r.returncode != 0 or not r.stdout.strip():
        return None
    import datetime
    return datetime.datetime.utcfromtimestamp(int(r.stdout.strip())).year


def python_requirement(cache: Path, commit: str) -> str:
    from benchmark.wp2.environment_manager import parse_python_requirement

    files: dict[str, str] = {}
    for name in ("pyproject.toml", "setup.py"):
        r = git(cache, "show", f"{commit}:{name}")
        if r.returncode == 0:
            files[name] = r.stdout
    return parse_python_requirement(files) if files else "UNKNOWN"


def census_task(cache: Path, tid: str, manifest: dict) -> dict:
    rec = manifest["record"]
    parent = rec["parent_commit"]
    target = rec["target_commit"]
    r = git(cache, "diff", "--name-status", parent, target)
    rows = []
    for line in r.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            rows.append((parts[0], parts[-1]))
    n_added = n_modified = 0
    n_migration = n_config = 0
    for status, path in rows:
        if is_test_path_v2(path):
            if status.startswith("A"):
                n_added += 1
            else:
                n_modified += 1
        if "migrations" in path.split("/"):
            n_migration += 1
        if any(seg in path.split("/") for seg in ("docker", "ci", ".github")):
            n_config += 1
    py = python_requirement(cache, target)
    return {
        "task_id": tid,
        "parent_commit": parent,
        "target_commit": target,
        "n_test_added": n_added,
        "n_test_modified": n_modified,
        "n_changed_test": n_added + n_modified,
        "n_migration": n_migration,
        "n_config_or_infra": n_config,
        "migration_or_config_heavy": n_migration + n_config > 0,
        "no_changed_test_evidence": (n_added + n_modified) == 0,
        "commit_year": commit_year(cache, target),
        "python_requirement": py,
    }


def main() -> int:
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    assign = split["assignment"]
    dev_ids = sorted(t for t, a in assign.items() if a in ("DEV_TRAIN", "DEV_VALIDATION"))
    dev_train_ids = sorted(t for t, a in assign.items() if a == "DEV_TRAIN")
    dev_val_ids = sorted(t for t, a in assign.items() if a == "DEV_VALIDATION")
    assert len(dev_train_ids) == 120 and len(dev_val_ids) == 30 and len(dev_ids) == 150

    tasks = []
    for tid in dev_ids:
        mp = SCIENTIFIC / tid / "case_manifest.json"
        if not mp.exists():
            raise SystemExit(f"missing manifest {mp}")
        manifest = json.loads(mp.read_text(encoding="utf-8"))
        tasks.append(census_task(CACHE, tid, manifest))

    year_dist = {}
    for t in tasks:
        y = str(t["commit_year"] or "UNKNOWN")
        year_dist.setdefault(y, 0)
        year_dist[y] += 1
    env_fam = {}
    for t in tasks:
        k = t["python_requirement"]
        env_fam[k] = env_fam.get(k, 0) + 1

    artifact = {
        "artifact": "wp2_dev_census",
        "date": "2026-09-23",
        "scope": "frozen Saleor DEV pool (DEV_TRAIN=120 + DEV_VALIDATION=30); zero-model; no generation/Smoke/Pilot",
        "counts": {
            "DEV_TRAIN": len(dev_train_ids),
            "DEV_VALIDATION": len(dev_val_ids),
            "with_changed_test_evidence": sum(1 for t in tasks if not t["no_changed_test_evidence"]),
            "no_changed_test_evidence": sum(1 for t in tasks if t["no_changed_test_evidence"]),
            "migration_or_config_heavy": sum(1 for t in tasks if t["migration_or_config_heavy"]),
            "n_test_added_total": sum(t["n_test_added"] for t in tasks),
            "n_test_modified_total": sum(t["n_test_modified"] for t in tasks),
        },
        "commit_year_distribution": year_dist,
        "environment_family_distribution": env_fam,
        "tasks": tasks,
        "split_freeze_sha256": split.get("canonical_split_freeze_sha256"),
    }
    out_path = OUT / "dev_census_2026-09-23.json"
    out_path.write_text(json.dumps(artifact, indent=1, ensure_ascii=False), encoding="utf-8")

    dev_split = build_dev_split_artifact(
        dev_train_ids=dev_train_ids, dev_validation_ids=dev_val_ids
    )
    split_path = OUT / "dev_split_v2_2026-09-23.json"
    split_path.write_text(json.dumps(dev_split, indent=1, ensure_ascii=False), encoding="utf-8")

    print("census:", json.dumps(artifact["counts"], indent=1))
    print("years:", json.dumps(year_dist, indent=1))
    print("env_families:", json.dumps(env_fam, indent=1))
    print("dev_split:", json.dumps(dev_split["counts"], indent=1))
    print("wrote", out_path.name, "and", split_path.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
