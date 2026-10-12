#!/usr/bin/env python3
"""D7_R3 LIGHT packer -- builds project-light-year-2026-10-12-r3-<HHmm>.zip.

Mission: M17_ENV_CANON_D7_R3_HARNESS_DEFECT_CORRECTION_AND_FREEZE / LIGHT
Contents (R3 authority / evidence only):
  - R3 harness source (harness\\d7_r3\\*)
  - harness manifest
  - P2P/F2P receipt
  - freeze manifest + freeze report
  - native-spec audit evidence (defect reproduction)
  - R2 failed-calibration evidence (receipt/report/quarantine) for R2->R3 audit
  - small authority references (R4B authority files, D7_CALIBRATION_12_PLAN,
    DOCKER_PROFILE_MANIFEST, MARKER_FILTER_AUDIT)
Excluded: wheels, Docker layers, worktrees, caches, build outputs.
Deterministic ordering (sorted paths); UTF-8; <= 50 MiB (target: a few MiB).
"""
import hashlib
import json
import os
import zipfile
from datetime import datetime, timezone

STORE = r"D:\wp2_env_store"
HARNESS = os.path.join(STORE, "harness", "d7_r3")
OUT = os.path.join(STORE, "project-light-year-2026-10-12-r3-0330.zip")

AUTHORITY_FILES = [
    r"D:\wp2_env_store\manifests\D7_R3_HARNESS_FREEZE.json",
    r"D:\wp2_env_store\receipts\D7_R3_HARNESS_P2P_F2P.json",
    r"D:\wp2_env_store\reports\D7_R3_HARNESS_FREEZE_REPORT.md",
    r"D:\wp2_env_store\receipts\D7_R2_TO_R3_DEFECT_RESOLUTION.json",
    r"D:\wp2_env_store\harness\d7_r3\D7_R3_HARNESS_MANIFEST.json",
    r"D:\wp2_env_store\tmp\d7_r3_out\probes\D7_R3_NATIVE_SPEC_AUDIT.json",
    # R2 failed calibration evidence (immutable, for R2->R3 audit)
    r"D:\wp2_env_store\receipts\D7_R2_CALIBRATION_12_RECEIPT.json",
    r"D:\wp2_env_store\reports\D7_R2_CALIBRATION_12_REPORT.md",
    r"D:\wp2_env_store\receipts\D7_R2_NATIVE_PROBE_QUARANTINE.json",
    r"D:\wp2_env_store\manifests\D7_R2_HARNESS_FREEZE.json",
    r"D:\wp2_env_store\receipts\D7_R2_HARNESS_P2P_F2P.json",
    r"D:\wp2_env_store\reports\D7_R2_HARNESS_FREEZE_REPORT.md",
    r"D:\wp2_env_store\harness\d7_r2\D7_R2_HARNESS_MANIFEST.json",
    # frozen authority files
    r"D:\wp2_env_store\manifests\R4B_FINAL_SOURCE_BUILD_CANON_FREEZE.json",
    r"D:\wp2_env_store\manifests\R4B_FINAL_BUILD_TOOLHOUSE.json",
    r"D:\wp2_env_store\manifests\R4B_FINAL_NATIVE_ENVIRONMENT.json",
    r"D:\wp2_env_store\manifests\D7_CALIBRATION_12_PLAN.json",
    r"D:\wp2_env_store\manifests\DOCKER_PROFILE_MANIFEST.json",
    r"D:\wp2_env_store\manifests\MARKER_FILTER_AUDIT.json",
]


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def collect() -> list[tuple[str, str]]:
    # returns [(arcname, srcpath)] sorted by arcname.
    # The harness portion is bound to the FROZEN manifest's authoritative file
    # set (not a directory glob), so unaffiliated files can never leak in.
    manifest_path = os.path.join(HARNESS, "D7_R3_HARNESS_MANIFEST.json")
    manifest = json.load(open(manifest_path, encoding="utf-8"))
    manifest_entries = {
        rel: os.path.join(HARNESS, rel.replace("/", os.sep))
        for rel in manifest.get("files", {})
        if rel != "D7_R3_HARNESS_MANIFEST.json"
    }
    items: dict[str, str] = {}
    for rel, src in manifest_entries.items():
        if os.path.isfile(src):
            items[f"harness/d7_r3/{rel}"] = src
    # the manifest itself is carried verbatim
    items["harness/d7_r3/D7_R3_HARNESS_MANIFEST.json"] = manifest_path
    for src in AUTHORITY_FILES:
        if os.path.isfile(src):
            arc = os.path.relpath(src, STORE).replace("\\", "/")
            items[arc] = src
    return sorted(items.items())


def main() -> int:
    if os.path.exists(OUT):
        os.remove(OUT)
    items = collect()
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for arc, src in items:
            z.write(src, arc)
    size = os.path.getsize(OUT)
    sha = sha256_file(OUT)
    print("PROJECT_EXPORT_READY")
    print("PROJECT_EXPORT_NAME=" + os.path.basename(OUT))
    print("PROJECT_EXPORT_PATH=" + OUT)
    print("PROJECT_EXPORT_SIZE_BYTES=%d" % size)
    print("PROJECT_EXPORT_SHA256=" + sha)
    print("UPLOAD_THIS_FILE=" + os.path.basename(OUT))
    print("N_ENTRIES=%d" % len(items))
    info = {
        "artifact": "project-light-year-2026-10-12-r3",
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "n_entries": len(items),
        "size_bytes": size,
        "sha256": sha,
        "excludes": ["wheels", "docker layers", "worktrees", "caches", "build outputs", "real calibration results"],
        "real_12_unit_results_included": False,
    }
    with open(os.path.join(STORE, "tmp", "d7_r3_light_info.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, sort_keys=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
