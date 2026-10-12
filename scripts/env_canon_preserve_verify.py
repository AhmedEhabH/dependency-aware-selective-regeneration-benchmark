"""Deterministic verifier for the M17 D7 R3 remote-evidence preservation snapshot.

This module (a) performs the byte-for-byte copy of the authoritative D7 R3
evidence from the read-only source store into the repository worktree and
writes EVIDENCE_MANIFEST.json, (b) writes EVIDENCE_INDEX.md, and (c) verifies
the snapshot with P2P (positive) and F2P (fail-closed negative) checks.

The source store is READ-ONLY for this module; it never writes to the store.
F2P negatives are exercised against temporary fixtures in the unit tests, never
against the source store.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

DEST_DIR_REL = Path("research") / "env-canon-evidence" / "d7-r3"
MAX_EVIDENCE_BYTES = 50 * 1024 * 1024
MANIFEST_NAME = "EVIDENCE_MANIFEST.json"
INDEX_NAME = "EVIDENCE_INDEX.md"

HARNESS = "HARNESS"
MANIFEST = "MANIFEST"
RECEIPT = "RECEIPT"
REPORT = "REPORT"
SUPPORTING = "SUPPORTING_AUTHORITY"

# (source rel path under store, destination rel path under evidence dir, classification)
PRESERVATION_SET: list[tuple[str, str, str]] = [
    # D7 R3 harness tree
    ("harness/d7_r3/d7_r3_closure.py", "harness/d7_r3_closure.py", HARNESS),
    ("harness/d7_r3/D7_R3_HARNESS_CONTRACT.md", "harness/D7_R3_HARNESS_CONTRACT.md", HARNESS),
    ("harness/d7_r3/D7_R3_HARNESS_MANIFEST.json", "harness/D7_R3_HARNESS_MANIFEST.json", HARNESS),
    ("harness/d7_r3/d7_r3_light_pack.py", "harness/d7_r3_light_pack.py", HARNESS),
    ("harness/d7_r3/d7_r3_native_specs.py", "harness/d7_r3_native_specs.py", HARNESS),
    ("harness/d7_r3/d7_r3_probes.py", "harness/d7_r3_probes.py", HARNESS),
    ("harness/d7_r3/d7_r3_validation_driver.py", "harness/d7_r3_validation_driver.py", HARNESS),
    ("harness/d7_r3/d7_r3_wheeltags.py", "harness/d7_r3_wheeltags.py", HARNESS),
    ("harness/d7_r3/tests/pytest.ini", "harness/tests/pytest.ini", HARNESS),
    ("harness/d7_r3/tests/test_d7_r3_harness.py", "harness/tests/test_d7_r3_harness.py", HARNESS),
    # D7 R3 manifests / receipts / reports
    ("manifests/D7_R3_HARNESS_FREEZE.json", "manifests/D7_R3_HARNESS_FREEZE.json", MANIFEST),
    ("receipts/D7_R3_HARNESS_P2P_F2P.json", "receipts/D7_R3_HARNESS_P2P_F2P.json", RECEIPT),
    ("receipts/D7_R2_TO_R3_DEFECT_RESOLUTION.json", "receipts/D7_R2_TO_R3_DEFECT_RESOLUTION.json", RECEIPT),
    ("reports/D7_R3_HARNESS_FREEZE_REPORT.md", "reports/D7_R3_HARNESS_FREEZE_REPORT.md", REPORT),
    # Supporting authority files needed to interpret R3
    ("manifests/D7_CALIBRATION_12_PLAN.json", "manifests/D7_CALIBRATION_12_PLAN.json", SUPPORTING),
    ("manifests/DOCKER_PROFILE_MANIFEST.json", "manifests/DOCKER_PROFILE_MANIFEST.json", SUPPORTING),
    (
        "manifests/R4B_FINAL_SOURCE_BUILD_CANON_FREEZE.json",
        "manifests/R4B_FINAL_SOURCE_BUILD_CANON_FREEZE.json",
        SUPPORTING,
    ),
    ("receipts/R4B_FINAL_215_BUILD_ACCOUNTING.json", "receipts/R4B_FINAL_215_BUILD_ACCOUNTING.json", SUPPORTING),
    ("reports/R4B_FINAL_ENVIRONMENT_CANON_REPORT.md", "reports/R4B_FINAL_ENVIRONMENT_CANON_REPORT.md", SUPPORTING),
]

REQUIRED_HARNESS_FILES: tuple[str, ...] = tuple(
    dest_rel for _, dest_rel, classification in PRESERVATION_SET if classification == HARNESS
)

FORBIDDEN_PATH_SEGMENTS = frozenset(
    {
        "wheel",
        "wheelhouse",
        "built_wheelhouse",
        "docker",
        "image_exports",
        "build_cache",
        "cache",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".git",
        "node_modules",
        "build_toolhouse",
    }
)
FORBIDDEN_PATH_SUFFIXES = (".whl", ".tar.gz", ".pyc", ".tgz", ".img", ".sqsh", ".squashfs")

INDEX_NARRATIVE = """# D7 R3 Evidence — Remote Preservation Index

Mission: `M17_ENV_CANON_D7_R3_REMOTE_EVIDENCE_PRESERVATION`
Date: 2026-10-12
Mission class: T2 — EVIDENCE PRESERVATION / REMOTE BACKUP ONLY
Scientific changes: NONE
Calibration touched: FALSE
Source store (read-only): `D:\\wp2_env_store`
This Git snapshot root: `research/env-canon-evidence/d7-r3/`
Verifier: `scripts/env_canon_preserve_verify.py`
Per-file SHA-256 + provenance: `EVIDENCE_MANIFEST.json`

## What this snapshot is

1. R2 was immutable failed calibration evidence. `harness/d7_r2` froze before
   the calibration-12 run, and R2 calibration failed at the first real unit
   (`N_EXECUTED=1, N_PASS=0, N_FAIL=1`) on a native-profile SONAME mismatch.
   R2 is unchanged and remains immutable failed evidence
   (`receipts/D7_R2_TO_R3_DEFECT_RESOLUTION.json`).
2. R3 is additive corrected harness evidence. A new harness tree
   (`harness/d7_r3/`) was created alongside R2; R2 was never modified. The
   correction is engineering metadata only, aligning harness probe truth with
   the already-frozen environment artifacts.
3. Known R3 engineering corrections (defect-mapped):
   - libopenjp2 loader-visible SONAME: `libopenjp2-7.so.7` -> `libopenjp2.so.7`
   - pipx executable-on-PATH semantics: absolute `/usr/local/bin/pipx` ->
     `command -v pipx` -> `/usr/bin/pipx`
   - libxslt loader-visible SONAME: `libxslt.so.1.1` -> `libxslt.so.1`
4. Frozen R3 verification already established before this preservation mission:
   - 43/43 unit tests PASS (frozen R3 harness test suite)
   - P2P 7/7
   - F2P 9/9
   - WT (wheel-tag controls) 9/9
   - dry closure 12/12
5. No real Calibration-12 result is claimed by THIS preservation mission. The
   R3 freeze explicitly records `real_12_unit_execution_started=false` and
   `calibration_12_not_run=true`. This snapshot preserves evidence; it does not
   add, run, or re-interpret calibration.
6. Source-of-truth remains the original store evidence at `D:\\wp2_env_store`;
   this Git copy is a byte-identical remote-preservation snapshot
   (source SHA-256 == destination SHA-256 for every preserved artifact).

## Preserved artifact index

| classification | destination path | sha256 (destination) |
|---|---|---|
"""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_forbidden_path(rel_path: str) -> bool:
    normalized = rel_path.replace("\\", "/")
    parts = normalized.split("/")
    if any(part.lower() in FORBIDDEN_PATH_SEGMENTS for part in parts):
        return True
    return normalized.lower().endswith(FORBIDDEN_PATH_SUFFIXES)


def tree_size(root: Path) -> int:
    total = 0
    if root.is_dir():
        for path in root.rglob("*"):
            if path.is_file():
                total += path.stat().st_size
    return total


def evidence_root(repo_root: Path) -> Path:
    return repo_root / DEST_DIR_REL


def copy_preservation_set(store_root: Path, repo_root: Path) -> dict[str, Any]:
    """Copy the preservation set byte-for-byte and write EVIDENCE_MANIFEST.json."""
    dest_root = evidence_root(repo_root)
    artifacts: list[dict[str, Any]] = []
    for src_rel, dest_rel, classification in PRESERVATION_SET:
        src = store_root / src_rel
        dest = dest_root / dest_rel
        if not src.is_file():
            raise FileNotFoundError(f"source artifact missing: {src}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        src_sha = sha256_file(src)
        dest_sha = sha256_file(dest)
        if src_sha != dest_sha:
            raise AssertionError(f"copy not byte-identical: {dest_rel}")
        artifacts.append(
            {
                "source_abs": str(src),
                "dest_rel": dest_rel.replace("\\", "/"),
                "sha256_source": src_sha,
                "sha256_dest": dest_sha,
                "size_bytes": dest.stat().st_size,
                "classification": classification,
                "immutable_copy": True,
            }
        )
    manifest: dict[str, Any] = {
        "mission": "M17_ENV_CANON_D7_R3_REMOTE_EVIDENCE_PRESERVATION",
        "mission_class": "T2_EVIDENCE_PRESERVATION_REMOTE_BACKUP_ONLY",
        "scientific_changes": "NONE",
        "source_store": str(store_root),
        "dest_root": DEST_DIR_REL.as_posix(),
        "immutable_copy": True,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    manifest_path = dest_root / MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def load_manifest(repo_root: Path) -> dict[str, Any]:
    manifest_path = evidence_root(repo_root) / MANIFEST_NAME
    with manifest_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def verify_p1_source_copy_hash(manifest: dict[str, Any], repo_root: Path) -> tuple[bool, list[str]]:
    dest_root = evidence_root(repo_root)
    problems: list[str] = []
    for artifact in manifest["artifacts"]:
        src = Path(artifact["source_abs"])
        dest = dest_root / artifact["dest_rel"]
        if not src.is_file():
            problems.append(f"source missing: {src}")
            continue
        if not dest.is_file():
            problems.append(f"copy missing: {dest}")
            continue
        if sha256_file(src) != artifact["sha256_source"]:
            problems.append(f"source hash changed: {artifact['dest_rel']}")
        if sha256_file(dest) != artifact["sha256_dest"]:
            problems.append(f"copy hash mismatch: {artifact['dest_rel']}")
    return (not problems, problems)


def verify_p2_harness_tree(manifest: dict[str, Any]) -> tuple[bool, list[str]]:
    harness_dests = {
        artifact["dest_rel"]
        for artifact in manifest["artifacts"]
        if artifact["classification"] == HARNESS
    }
    missing = [rel for rel in REQUIRED_HARNESS_FILES if rel not in harness_dests]
    return (not missing, [f"harness file not represented in manifest: {rel}" for rel in missing])


def verify_p3_index_links(manifest: dict[str, Any], repo_root: Path) -> tuple[bool, list[str]]:
    index_path = evidence_root(repo_root) / INDEX_NAME
    if not index_path.is_file():
        return (False, [f"index missing: {index_path}"])
    index_text = index_path.read_text(encoding="utf-8")
    problems: list[str] = []
    for artifact in manifest["artifacts"]:
        if artifact["classification"] in {MANIFEST, RECEIPT, REPORT} and artifact["dest_rel"] not in index_text:
            problems.append(f"index does not resolve {artifact['dest_rel']}")
    return (not problems, problems)


def verify_p4_defect_receipt(manifest: dict[str, Any]) -> tuple[bool, list[str]]:
    present = any(
        artifact["dest_rel"] == "receipts/D7_R2_TO_R3_DEFECT_RESOLUTION.json"
        for artifact in manifest["artifacts"]
    )
    return (present, [] if present else ["D7_R2_TO_R3_DEFECT_RESOLUTION.json missing from manifest"])


def verify_p5_no_source_changed(manifest: dict[str, Any]) -> tuple[bool, list[str]]:
    problems: list[str] = []
    for artifact in manifest["artifacts"]:
        src = Path(artifact["source_abs"])
        if not src.is_file():
            problems.append(f"source missing: {src}")
        elif sha256_file(src) != artifact["sha256_source"]:
            problems.append(f"mission-owned source changed: {artifact['dest_rel']}")
    return (not problems, problems)


def verify_required_present(manifest: dict[str, Any], repo_root: Path) -> tuple[bool, list[str]]:
    dest_root = evidence_root(repo_root)
    problems = [
        f"required artifact missing: {artifact['dest_rel']}"
        for artifact in manifest["artifacts"]
        if not (dest_root / artifact["dest_rel"]).is_file()
    ]
    return (not problems, problems)


def verify_size_cap(repo_root: Path, max_bytes: int = MAX_EVIDENCE_BYTES) -> tuple[bool, list[str]]:
    total = tree_size(evidence_root(repo_root))
    if total <= max_bytes:
        return (True, [])
    return (False, [f"evidence tree exceeds cap: {total} > {max_bytes}"])


def verify_no_forbidden_paths(manifest: dict[str, Any]) -> tuple[bool, list[str]]:
    bad = [artifact["dest_rel"] for artifact in manifest["artifacts"] if is_forbidden_path(artifact["dest_rel"])]
    return (not bad, [f"forbidden path in preservation list: {path}" for path in bad])


def verify_byte_match(manifest: dict[str, Any], repo_root: Path) -> tuple[bool, list[str]]:
    dest_root = evidence_root(repo_root)
    problems: list[str] = []
    for artifact in manifest["artifacts"]:
        dest = dest_root / artifact["dest_rel"]
        if not dest.is_file():
            problems.append(f"required artifact missing: {artifact['dest_rel']}")
        elif sha256_file(dest) != artifact["sha256_dest"]:
            problems.append(f"destination byte mismatch: {artifact['dest_rel']}")
    return (not problems, problems)


def verify_all(manifest: dict[str, Any], repo_root: Path) -> list[dict[str, Any]]:
    checks: list[tuple[str, tuple[bool, list[str]]]] = [
        ("P1_source_exists_copy_exists_sha_exact", verify_p1_source_copy_hash(manifest, repo_root)),
        ("P2_harness_tree_fully_represented", verify_p2_harness_tree(manifest)),
        ("P3_manifest_receipt_report_links_resolvable", verify_p3_index_links(manifest, repo_root)),
        ("P4_r2_to_r3_defect_resolution_receipt_included", verify_p4_defect_receipt(manifest)),
        ("P5_no_mission_owned_source_changed", verify_p5_no_source_changed(manifest)),
        ("F2_required_preserved_artifacts_present", verify_required_present(manifest, repo_root)),
        ("F3_no_unexpected_large_payload", verify_size_cap(repo_root)),
        ("F4_no_wheel_docker_cache_paths", verify_no_forbidden_paths(manifest)),
        ("F5_source_dest_byte_match", verify_byte_match(manifest, repo_root)),
    ]
    return [
        {"name": name, "passed": passed, "problems": problems} for name, (passed, problems) in checks
    ]


def write_index(repo_root: Path) -> None:
    manifest = load_manifest(repo_root)
    rows = [
        f"| {artifact['classification']} | `{artifact['dest_rel']}` | `{artifact['sha256_dest']}` |"
        for artifact in sorted(manifest["artifacts"], key=lambda item: item["dest_rel"])
    ]
    index_path = evidence_root(repo_root) / INDEX_NAME
    index_path.write_text(INDEX_NARRATIVE + "\n".join(rows) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Copy/verify D7 R3 preservation snapshot.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="repository worktree root")
    parser.add_argument("--store-root", type=Path, default=Path(r"D:\wp2_env_store"), help="read-only source store")
    parser.add_argument(
        "--copy",
        action="store_true",
        help="perform byte-for-byte copy and write EVIDENCE_MANIFEST.json",
    )
    parser.add_argument("--write-index", action="store_true", help="write EVIDENCE_INDEX.md from the manifest")
    args = parser.parse_args(argv)

    store_root = args.store_root.resolve()
    repo_root = args.repo_root.resolve()

    if args.copy:
        copy_preservation_set(store_root, repo_root)
        print("COPY_OK")
        return 0
    if args.write_index:
        write_index(repo_root)
        print("INDEX_OK")
        return 0

    manifest = load_manifest(repo_root)
    checks = verify_all(manifest, repo_root)
    failed = [check for check in checks if not check["passed"]]
    for check in checks:
        tag = "PASS" if check["passed"] else "FAIL"
        print(f"{tag} {check['name']}")
        for problem in check["problems"]:
            print(f"    - {problem}")
    if failed:
        print("VERIFICATION_FAILED")
        return 1
    print("VERIFICATION_PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
