#!/usr/bin/env python3
"""WP-2 DEV unchanged-test P2P candidate inventory V1 (Mission-08) - ZERO API.

Deterministic association phase using the IDENTICAL frozen P2P Preservation
Rule V1 over the frozen DEV pool (DEV_TRAIN 120 + DEV_VALIDATION 30):

1. ``--associate``  : per-task deterministic association of unchanged test
   files (same top-level Saleor app as touched production files; file
   unchanged by the target commit) from the read-only Saleor git cache. Node
   discovery is marked PENDING for the 47 oracle-valid tasks.
2. ``--finalize``   : merge the node-discovery JSONL (from
   scripts/wp2_p2p_inventory_dev_nodes.py) into the association artifact and
   emit the frozen DEV inventory with cap=400, SHA-256 hashes, membership and
   coverage.

No outcome inspection happens here: node stability (parent 3/3 AND target 3/3)
is determined only by the later frozen evaluator run. The candidate set is
evaluator-only and invisible to generation/repair.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.oracle_semantics_v2 import is_test_path_v2  # noqa: E402
from benchmark.wp2.p2p_inventory_dev_v1 import (  # noqa: E402
    NODE_DISCOVERY_COLLECTED,
    NODE_DISCOVERY_NOT_APPLICABLE,
    P2P_DEV_INVENTORY_VERSION,
    P2P_RULE_VERSION,
    P2P_SAMPLE_SALT_FROZEN,
    build_task_record,
    dev_inventory_sha256,
    membership_sha256,
)
from benchmark.wp2.p2p_inventory_v1 import associate_unchanged_test_files  # noqa: E402

CACHE = PROJECT / "dist" / "pilot-repo-cache" / "saleor"
DEV_CENSUS = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23" / "dev_census_2026-09-23.json"
DEV_SPLIT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23" / "dev_split_v2_2026-09-23.json"
PER_TASK_DEV = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23" / "per_task_dev_v2.jsonl"
OUT_ARTIFACT = PROJECT / "research" / "wp2" / "wp2_dev_unchanged_p2p_candidate_inventory_v1_2026-09-25.json"
DISCOVERY_JSONL = (
    PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23"
    / "dev_unchanged_p2p_node_discovery_2026-09-25.jsonl"
)

DEV_POOL_SCOPE = "DEV_TRAIN(120) + DEV_VALIDATION(30)"


def git(cache: Path, *args: str) -> subprocess.CompletedProcess[str]:
    cmd = ["git", "-C", str(cache), *args]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=False)


def changed_paths(parent: str, target: str) -> dict:
    r = git(CACHE, "diff", "--name-status", parent, target)
    test_paths: list[str] = []
    prod_paths: list[str] = []
    for line in r.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        path = parts[1]
        (test_paths if is_test_path_v2(path) else prod_paths).append(path)
    return {
        "test_files": sorted(test_paths),
        "prod_files": sorted(prod_paths),
        "all": set(test_paths) | set(prod_paths),
    }


_ls_cache: dict[str, list[str]] = {}


def all_test_files_at_target(target: str) -> list[str]:
    if target in _ls_cache:
        return _ls_cache[target]
    r = git(CACHE, "ls-tree", "-r", "--name-only", target)
    files = [p for p in r.stdout.splitlines() if is_test_path_v2(p)]
    _ls_cache[target] = files
    return files


_TEST_SUPPORT_RE = __import__("re").compile(
    r"(?:^|/)conftest\.py$|(?:^|/)fixtures\.py$|(?:^|/)cassettes?/"
)


def is_test_support_path(path: str) -> bool:
    """Test-support artifact per the frozen test-path rule categories
    (conftest / fixtures / cassette dirs)."""
    return bool(_TEST_SUPPORT_RE.search(path))


def changed_test_support_audit(changed_test_paths: list[str], associated_files: list[str]) -> dict:
    """Q1: whether any associated unchanged test file shares/uses a test-support
    artifact changed by the frozen test patch (conftest/fixtures/cassettes)."""
    support = sorted(p for p in changed_test_paths if is_test_support_path(p))
    dirs = set()
    for s in support:
        if "/cassettes/" in s or s.rsplit("/", 1)[-1].startswith("cassette"):
            dirs.add(s)
        else:
            dirs.add(s.rsplit("/", 1)[0])
    sharing = 0
    for f in associated_files:
        fdir = f.rsplit("/", 1)[0] if "/" in f else ""
        if any(d == fdir or fdir.startswith(d + "/") or d.startswith(fdir + "/") for d in dirs):
            sharing += 1
    return {
        "changed_test_support_present": len(support) > 0,
        "changed_test_support_paths": support,
        "n_associated_files_sharing_changed_test_support": sharing,
    }


def load_census_and_roles() -> tuple[list[dict], dict[str, str], dict[str, dict]]:
    census = json.loads(DEV_CENSUS.read_text(encoding="utf-8"))
    split = json.loads(DEV_SPLIT.read_text(encoding="utf-8"))
    role: dict[str, str] = {}
    for role_name, ids in split["membership"].items():
        for tid in ids:
            role[tid] = role_name
    per_task: dict[str, dict] = {}
    for line in PER_TASK_DEV.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            per_task[rec["task_id"]] = rec
    return census["tasks"], role, per_task


def oracle_valid_task_ids(per_task: dict[str, dict]) -> set[str]:
    result: set[str] = set()
    for tid, rec in per_task.items():
        if rec.get("status") != "DONE":
            continue
        counts = rec.get("counts", {})
        if counts.get("BEHAVIORAL_F2P", 0) >= 1 or counts.get("SYMBOL_ABSENCE_F2P", 0) >= 1:
            result.add(tid)
    return result


def env_failed_task_ids(per_task: dict[str, dict]) -> set[str]:
    return {tid for tid, rec in per_task.items() if rec.get("status") != "DONE"}


def build_association_rows(
    tasks: list[dict], role: dict[str, str], per_task: dict[str, dict]
) -> list[dict]:
    oracle_valid = oracle_valid_task_ids(per_task)
    env_failed = env_failed_task_ids(per_task)
    rows: list[dict] = []
    for t in sorted(tasks, key=lambda x: x["task_id"]):
        tid = t["task_id"]
        cp = changed_paths(t["parent_commit"], t["target_commit"])
        all_tests = all_test_files_at_target(t["target_commit"])
        associated = associate_unchanged_test_files(
            touched_production_files=cp["prod_files"],
            all_test_files=all_tests,
            target_diff_paths=cp["all"],
        )
        from benchmark.wp2.era_resolver import ERA_TABLE

        req = t.get("python_requirement", "UNKNOWN")
        era_key = ERA_TABLE[req].era_key if req in ERA_TABLE else "UNKNOWN"
        support_audit = changed_test_support_audit(cp["test_files"], associated)
        row = build_task_record(
            task_id=tid,
            split_role=role.get(tid, "NOT_IN_SPLIT"),
            parent_commit=t["parent_commit"],
            target_commit=t["target_commit"],
            era_key=era_key,
            python_requirement=req,
            oracle_valid=tid in oracle_valid,
            no_changed_test_evidence=bool(t.get("no_changed_test_evidence")),
            env_failed=tid in env_failed,
            touched_production_files=cp["prod_files"],
            associated_unchanged_test_files=associated,
            candidate_nodes=None,
            changed_test_support_present=support_audit["changed_test_support_present"],
        )
        if tid in oracle_valid:
            row["node_discovery_status"] = "PENDING"
        rows.append(row)
    return rows


def unknown_app_audit(rows: list[dict]) -> dict:
    """Q10: audit touched-production / associated-test paths whose frozen
    ``top_level_app`` result is UNKNOWN (identical to frozen MAIN V1 behavior;
    report, never silently fix)."""
    unk_tasks = [r["task_id"] for r in rows if "UNKNOWN" in r["touched_production_apps"]]
    return {
        "n_tasks_with_unknown_touched_app": len(unk_tasks),
        "task_ids": sorted(unk_tasks),
        "note": (
            "UNKNOWN comes from root-level touched files (CHANGELOG.md, README.md, "
            "SECURITY.md) and root conftest.py under the frozen top_level_app rule; "
            "identical to the frozen MAIN V1 implementation. Root conftest.py "
            "contributes zero collectible nodes."
        ),
    }


def load_discovery() -> dict[str, dict]:
    result: dict[str, dict] = {}
    if not DISCOVERY_JSONL.exists():
        return result
    for line in DISCOVERY_JSONL.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            result[rec["task_id"]] = rec
    return result


def compute_discovery_distribution(tasks: list[dict]) -> dict:
    """Deterministic raw-node discovery distribution over the 47 union."""

    rows = [r for r in tasks if r["oracle_valid"]]
    counts = sorted(r["n_discovered_candidate_nodes"] or 0 for r in rows)

    def pct(p: float) -> int:
        idx = int(p / 100.0 * (len(counts) - 1))
        return counts[idx]

    per_era: dict[str, list[int]] = {}
    per_split: dict[str, list[int]] = {}
    for r in rows:
        n = r["n_discovered_candidate_nodes"] or 0
        per_era.setdefault(r["era_key"], [0, 0])
        per_era[r["era_key"]][0] += 1
        per_era[r["era_key"]][1] += n
        per_split.setdefault(r["split_role"], [0, 0])
        per_split[r["split_role"]][0] += 1
        per_split[r["split_role"]][1] += n
    return {
        "n_tasks": len(rows),
        "total_raw_nodes": sum(counts),
        "min": counts[0],
        "max": counts[-1],
        "median": pct(50),
        "p75": pct(75),
        "p90": pct(90),
        "per_era": {k: {"tasks": v[0], "raw_nodes": v[1]} for k, v in sorted(per_era.items())},
        "per_split": {k: {"tasks": v[0], "raw_nodes": v[1]} for k, v in sorted(per_split.items())},
        "tasks_gt_400": sum(1 for c in counts if c > 400),
        "tasks_gt_1000": sum(1 for c in counts if c > 1000),
        "tasks_gt_5000": sum(1 for c in counts if c > 5000),
        "tasks_gt_10000": sum(1 for c in counts if c > 10000),
        "zero_node_tasks": sorted(r["task_id"] for r in rows if (r["n_discovered_candidate_nodes"] or 0) == 0),
        "note": (
            "RAW discovered node counts (metadata). Under frozen V1 "
            "post-stability cap semantics every raw node requires parent 3/3 + "
            "target 3/3 execution before cap=400 is applied (addendum Q7)."
        ),
    }


def associate_main() -> int:
    tasks, role, per_task = load_census_and_roles()
    rows = build_association_rows(tasks, role, per_task)
    oracle_valid = oracle_valid_task_ids(per_task)
    artifact = {
        "artifact": "wp2_dev_unchanged_p2p_candidate_inventory_v1",
        "artifact_version": P2P_DEV_INVENTORY_VERSION,
        "p2p_rule_version": P2P_RULE_VERSION,
        "p2p_sample_salt": P2P_SAMPLE_SALT_FROZEN,
        "date": "2026-09-25",
        "scope": DEV_POOL_SCOPE,
        "rule": (
            "unchanged test file, same top-level Saleor app as touched "
            "production file, test file unchanged by target; deterministic "
            "association (P2P Preservation Rule V1 applied to DEV); "
            "deterministic node discovery at target (raw, uncapped); "
            "CAP=400 applied POST-STABILITY only (addendum Q7); frozen V1 "
            "sample salt reused (addendum Q8); coverage-based association is "
            "NOT primary V1; no outcome inspection during construction"
        ),
        "parent_p2p_condition": (
            "parent commit + SAME frozen test patch as Linux V2 F2P oracle "
            "(TEST_PATCH_APPLIED_ON_PARENT=true)"
        ),
        "target_p2p_condition": "target commit",
        "n_tasks_considered": len(rows),
        "n_oracle_valid_union": len(oracle_valid),
        "node_discovery_status": "PENDING_47_ORACLE_VALID",
        "unknown_app_audit": unknown_app_audit(rows),
        "evaluator_only": True,
        "invisible_to_generation_and_repair": True,
        "preservation_validation_complete": False,
        "tasks": rows,
    }
    OUT_ARTIFACT.write_text(json.dumps(artifact, indent=1, ensure_ascii=False), encoding="utf-8")
    n_valid = sum(1 for r in rows if r["oracle_valid"])
    n_with_assoc = sum(1 for r in rows if r["n_associated_unchanged_test_files"] > 0)
    n_support = sum(1 for r in rows if r["changed_test_support_present"])
    print(
        "tasks considered: " + f"{len(rows)}; oracle-valid: {n_valid}; "
        f"with >=1 assoc file: {n_with_assoc}; with changed test support: {n_support}"
    )
    print("wrote", OUT_ARTIFACT.name)
    return 0


def finalize_main() -> int:
    if not OUT_ARTIFACT.exists():
        print("run --associate first")
        return 2
    payload = json.loads(OUT_ARTIFACT.read_text(encoding="utf-8"))
    discovery = load_discovery()
    oracle_ids = [r["task_id"] for r in payload["tasks"] if r["oracle_valid"]]
    missing = sorted(set(oracle_ids) - set(discovery))
    if missing:
        print(f"missing discovery for {len(missing)} oracle-valid tasks: {missing[:10]}")
        return 2
    for row in payload["tasks"]:
        if not row["oracle_valid"]:
            row["node_discovery_status"] = NODE_DISCOVERY_NOT_APPLICABLE
            continue
        disc = discovery[row["task_id"]]
        before = sorted(disc["candidate_node_ids_before_cap"])
        row["n_discovered_candidate_nodes"] = len(before)
        row["candidate_node_ids"] = before
        row["zero_candidate_nodes"] = len(before) == 0
        row["node_discovery_status"] = NODE_DISCOVERY_COLLECTED
        row["node_discovery"] = {
            "discovery_wall_s": disc.get("discovery_wall_s"),
            "collect_only_returncode": disc.get("returncode"),
            "n_files_associated": row["n_associated_unchanged_test_files"],
            "discovery_error": disc.get("error"),
            "n_files_excluded_from_collect_args": disc.get(
                "n_files_excluded_from_collect_args"
            ),
        }
    payload["node_discovery_status"] = "COLLECTED_47"
    payload.pop("hashes", None)
    payload["membership"] = {
        "DEV_TRAIN_ENG": sorted(
            r["task_id"] for r in payload["tasks"]
            if r["split_role"] == "DEV_TRAIN_ENG" and r["oracle_valid"]
        ),
        "DEV_TRAIN_ASSAY_HOLDOUT": sorted(
            r["task_id"] for r in payload["tasks"]
            if r["split_role"] == "DEV_TRAIN_ASSAY_HOLDOUT" and r["oracle_valid"]
        ),
        "DEV_VALIDATION": sorted(
            r["task_id"] for r in payload["tasks"]
            if r["split_role"] == "DEV_VALIDATION" and r["oracle_valid"]
        ),
    }
    payload["discovery_distribution"] = compute_discovery_distribution(payload["tasks"])
    # Canonical inventory hash computed over the payload WITHOUT the hashes
    # block (self-referential hashing would break determinism).
    payload["hashes"] = {
        "inventory_sha256": dev_inventory_sha256(
            {k: v for k, v in payload.items() if k != "hashes"}
        ),
        "membership_eng_sha256": membership_sha256(payload["membership"]["DEV_TRAIN_ENG"]),
        "membership_assay_holdout_sha256": membership_sha256(payload["membership"]["DEV_TRAIN_ASSAY_HOLDOUT"]),
        "membership_dev_validation_sha256": membership_sha256(payload["membership"]["DEV_VALIDATION"]),
        "membership_union_47_sha256": membership_sha256(
            [r["task_id"] for r in payload["tasks"] if r["oracle_valid"]]
        ),
    }
    payload["coverage"] = {
        "DEV_TRAIN_ENG": {
            "oracle_valid": len(payload["membership"]["DEV_TRAIN_ENG"]),
            "n_discovered_candidate_nodes": sum(
                r["n_discovered_candidate_nodes"] or 0
                for r in payload["tasks"]
                if r["split_role"] == "DEV_TRAIN_ENG" and r["oracle_valid"]
            ),
        },
        "DEV_TRAIN_ASSAY_HOLDOUT": {
            "oracle_valid": len(payload["membership"]["DEV_TRAIN_ASSAY_HOLDOUT"]),
            "n_discovered_candidate_nodes": sum(
                r["n_discovered_candidate_nodes"] or 0
                for r in payload["tasks"]
                if r["split_role"] == "DEV_TRAIN_ASSAY_HOLDOUT" and r["oracle_valid"]
            ),
        },
        "DEV_VALIDATION": {
            "oracle_valid": len(payload["membership"]["DEV_VALIDATION"]),
            "n_discovered_candidate_nodes": sum(
                r["n_discovered_candidate_nodes"] or 0
                for r in payload["tasks"]
                if r["split_role"] == "DEV_VALIDATION" and r["oracle_valid"]
            ),
        },
        "oracle_valid_union_47": {
            "oracle_valid": len(payload["membership"]["DEV_TRAIN_ENG"])
            + len(payload["membership"]["DEV_TRAIN_ASSAY_HOLDOUT"])
            + len(payload["membership"]["DEV_VALIDATION"]),
            "n_discovered_candidate_nodes": sum(
                r["n_discovered_candidate_nodes"] or 0 for r in payload["tasks"] if r["oracle_valid"]
            ),
        },
    }
    OUT_ARTIFACT.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    print("FINAL inventory_sha256:", payload["hashes"]["inventory_sha256"])
    print("coverage:", json.dumps(payload["coverage"], sort_keys=True))
    print("wrote", OUT_ARTIFACT.name)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--associate", action="store_true")
    ap.add_argument("--finalize", action="store_true")
    args = ap.parse_args()
    if args.associate:
        return associate_main()
    if args.finalize:
        return finalize_main()
    print("use --associate or --finalize")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
