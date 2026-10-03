#!/usr/bin/env python3
"""M17 P01 - MAIN frame census audit (selector-blind, read-only).

Builds `research/wp2/m17_v1/m17_main_frame_audit.json` from frozen inputs only.
Records ONLY selector-blind metadata. Never opens selector prediction files,
never computes selector F1 / coverage class / OPWS fields, and never invokes
Docker, WSL or a model/API.

Frozen sources:
- research/wp2/wp2_oracle_confirmation_selection_2026-09-22.json  (the 220 frame)
- research/wp2/wp2_saleor_main297_census_2026-09-22.json          (commits, candidacy)
- research/wp2/oracle_confirmation_linux_v2_2026-09-23/per_task_v2.jsonl (era, lockfile, V2 evidence)
- research/wp2/oracle_confirmation_linux_v2_2026-09-23/summary_v2.json    (V2 summary)
- dist/pilot-repo-cache/saleor  (read-only git; target-manifest facts)

Every unknown/missing schema field is explicitly classified; there is no
silent default for install mode or closure provenance.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "research/wp2/m17_v1/m17_main_frame_audit.json"
SELECTION = PROJECT / "research/wp2/wp2_oracle_confirmation_selection_2026-09-22.json"
CENSUS = PROJECT / "research/wp2/wp2_saleor_main297_census_2026-09-22.json"
PER_TASK_V2 = PROJECT / "research/wp2/oracle_confirmation_linux_v2_2026-09-23/per_task_v2.jsonl"
SUMMARY_V2 = PROJECT / "research/wp2/oracle_confirmation_linux_v2_2026-09-23/summary_v2.json"
SALEOR_CACHE = PROJECT / "dist/pilot-repo-cache/saleor"

MANIFEST_CANDIDATES = (
    "pyproject.toml",
    "uv.lock",
    "poetry.lock",
    "requirements.txt",
    "requirements_dev.txt",
    "requirements-test.txt",
)


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def target_manifest_facts(commit: str) -> dict[str, Any]:
    """Selector-blind facts derived from the target-commit manifests (read-only git)."""
    present: dict[str, bool] = {}
    for f in MANIFEST_CANDIDATES:
        r = subprocess.run(
            ["git", "-C", str(SALEOR_CACHE), "cat-file", "-e", f"{commit}:{f}"],
            capture_output=True,
        )
        present[f] = r.returncode == 0
    if present["uv.lock"]:
        mechanism = "uv"
    elif present["poetry.lock"]:
        mechanism = "poetry"
    elif present["requirements.txt"] or present["requirements_dev.txt"] or present["requirements-test.txt"]:
        mechanism = "requirements"
    else:
        mechanism = "none"
    pyproject = ""
    if present["pyproject.toml"]:
        r2 = subprocess.run(
            ["git", "-C", str(SALEOR_CACHE), "show", f"{commit}:pyproject.toml"],
            capture_output=True,
            encoding="utf-8",
        )
        if r2.returncode == 0:
            pyproject = r2.stdout
    declares_dev_group = bool(
        pyproject
        and (
            "[tool.poetry.group.dev.dependencies]" in pyproject
            or "[tool.poetry.dev-dependencies]" in pyproject
            or "[dependency-groups]" in pyproject
            or "dev = [" in pyproject
            or "test = [" in pyproject
            or "[project.optional-dependencies]" in pyproject
        )
    )
    return {
        "lockfile_present": {
            "uv.lock": present["uv.lock"],
            "poetry.lock": present["poetry.lock"],
            "requirements.txt": present["requirements.txt"],
            "requirements_dev.txt": present["requirements_dev.txt"],
            "requirements-test.txt": present["requirements-test.txt"],
        },
        "mechanism_derived": mechanism,
        "declares_dev_group_derived": declares_dev_group,
        "pyproject_present": present["pyproject.toml"],
        "derivation": "target_commit_manifests_via_saleor_cache_read_only_git",
    }


def commit_exists_windows(commit: str) -> bool:
    r = subprocess.run(
        ["git", "-C", str(SALEOR_CACHE), "cat-file", "-e", f"{commit}^{{commit}}"],
        capture_output=True,
    )
    return r.returncode == 0


def main() -> int:
    sel: dict[str, Any] = load_json(SELECTION)
    census_rows = {t["task_id"]: t for t in load_json(CENSUS)["tasks"]}
    per_task = {}
    for line in PER_TASK_V2.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            per_task[r["task_id"]] = r

    if sel.get("status") != "FROZEN_BEFORE_ORACLE_EXECUTION":
        print("FATAL: oracle selection is not frozen", file=sys.stderr)
        return 2
    frame = [r["task_id"] for r in sel["selection"]["tasks"]]

    if len(frame) != 220 or len(set(frame)) != 220:
        print(f"FATAL: frame is not exactly 220 unique ids (got {len(frame)})", file=sys.stderr)
        return 2
    for t in frame:
        if t not in census_rows:
            print(f"FATAL: {t} missing from MAIN census", file=sys.stderr)
            return 2
        if t not in per_task:
            print(f"FATAL: {t} missing from per_task_v2", file=sys.stderr)
            return 2

    tasks: list[dict[str, Any]] = []
    for t in sorted(frame):
        c = census_rows[t]
        v2 = per_task[t]
        prov = v2.get("provenance", {})
        facts = target_manifest_facts(c["target_commit"])
        tasks.append(
            {
                "task_id": t,
                "target_commit": c["target_commit"],
                "parent_commit": c["parent_commit"],
                "era_key": v2.get("era_key"),
                "historical_install_mode": {
                    "value": "NOT_RECORDED_IN_FROZEN_V2",
                    "note": "per_task_v2.jsonl carries no install-mode field; only "
                    "lockfile identity + manifest facts are recorded selector-blind",
                    "manifest_mechanism_derived": facts["mechanism_derived"],
                    "lockfile_present": facts["lockfile_present"],
                },
                "lockfile_identity": {
                    "lockfile_sha256": prov.get("lockfile_sha256"),
                    "installer_version": prov.get("installer_version"),
                    "source": "per_task_v2.jsonl provenance",
                },
                "historical_schema_signature": {
                    "schema": prov.get("schema"),
                    "harness_version": prov.get("harness_version"),
                    "python_version": prov.get("python_version"),
                    "test_patch_rule_sha256": prov.get("test_patch_rule_sha256"),
                    "classifier_bundle_sha256": prov.get("classifier_bundle_sha256"),
                },
                "dev_test_group_declared": {
                    "derived_from_target_manifest": facts["declares_dev_group_derived"],
                    "pyproject_present": facts["pyproject_present"],
                },
                "historical_closure_provenance": {
                    "value": "NOT_RECORDED",
                    "note": "per_task_v2.jsonl carries no dev_test_closure for MAIN; "
                    "never backfilled from selector-dependent evidence",
                },
                "evaluator_evidence_identifiers": {
                    "v2_status": v2.get("status"),
                    "v2_classification": v2.get("classification"),
                    "v2_primary_behavioral_f2p_eligible": v2.get("eligibility", {}).get(
                        "PRIMARY_BEHAVIORAL_F2P_ELIGIBLE"
                    ),
                    "v2_n_behavioral_f2p": v2.get("eligibility", {}).get("n_behavioral_f2p"),
                    "v2_n_symbol_absence_f2p": v2.get("eligibility", {}).get("n_symbol_absence_f2p"),
                    "v2_n_nodes": v2.get("n_nodes"),
                    "v2_n_test_files": v2.get("n_test_files"),
                    "v2_container_image_tag": prov.get("container_image_tag"),
                    "v2_environment_fingerprint": prov.get("environment_fingerprint"),
                    "v2_provenance_sha256": prov.get("provenance_sha256"),
                    "source": "oracle_confirmation_linux_v2_2026-09-23/per_task_v2.jsonl",
                },
                "known_environment_status": {
                    "value": "NOT_RECORDED_IN_FROZEN_V2",
                    "note": "no frozen V3 MAIN environment status exists (M16-v1 did not "
                    "reach Docker phases); V2 executed under WSL-local Docker per its harness",
                    "v2_status": v2.get("status"),
                },
                "commit_existence": {
                    "windows": commit_exists_windows(c["target_commit"]),
                    "wsl": "NOT_CHECKED_WITHOUT_EXECUTING_WSL",
                    "note": "Windows checked via read-only git in the frozen saleor cache; "
                    "WSL not executed in Phase 0",
                },
                "f2p_candidacy": c.get("f2p_candidacy"),
                "test_command": c.get("test_command"),
                "changed_file_counts": {
                    "n_changed": c.get("n_changed"),
                    "n_production": c.get("n_production"),
                    "n_test": c.get("n_test"),
                    "n_test_added": c.get("n_test_added"),
                    "n_test_modified": c.get("n_test_modified"),
                    "n_migration": c.get("n_migration"),
                    "n_config_or_infra": c.get("n_config_or_infra"),
                },
            }
        )

    ids = [t["task_id"] for t in tasks]
    audit: dict[str, Any] = {
        "artifact": "m17_main_frame_audit",
        "mission": "M17_P01",
        "date": "2026-10-02",
        "frame": {
            "source": "research/wp2/wp2_oracle_confirmation_selection_2026-09-22.json",
            "status": sel.get("status"),
            "n_tasks": len(tasks),
            "n_unique_ids": len(set(ids)),
            "n_duplicate_ids": len(ids) - len(set(ids)),
            "n_tasks_without_target_commit": sum(1 for t in tasks if not t["target_commit"]),
        },
        "schema_contract_note": (
            "Selector-blind only. Install mode is NOT_RECORDED in the frozen V2 record; "
            "the historical-schema contract (P02) defines its resolution path. Closure "
            "provenance is NOT_RECORDED and never backfilled. No field has a silent default."
        ),
        "tasks": tasks,
    }
    audit["frame"]["manifest_sha256"] = sha_text(json.dumps(audit, sort_keys=True, separators=(",", ":")))
    audit["frame"]["frame_sha256"] = sha_text(
        json.dumps({"ids": ids, "status": sel.get("status")}, sort_keys=True, separators=(",", ":"))
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(audit, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    print(f"M17_P01_CENSUS_PASS tasks={len(tasks)} unique={len(set(ids))} "
          f"dupes={audit['frame']['n_duplicate_ids']} "
          f"no_target_commit={audit['frame']['n_tasks_without_target_commit']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
