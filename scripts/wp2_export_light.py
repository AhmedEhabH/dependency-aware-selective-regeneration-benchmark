#!/usr/bin/env python3
"""TRUE LIGHT export by profile (brain-authored kit; hash-verified).

Profile JSON: {"include": [glob, ...] (priority order), "exclude": [fnmatch, ...],
               "max_file_bytes": int, "max_total_bytes": int, "name_prefix": str}
Files are added in include order until the total cap; anything skipped is listed with
its reason inside LIGHT_MANIFEST.json (in the zip). Always produces a zip, verifies it
(testzip) and prints the LIGHT_EXPORT_READY block.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import sys
import time
import zipfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
SECRET_RE = re.compile(rb"sk-or-v1-[0-9a-f]{16,}|Bearer\s+sk-[A-Za-z0-9_-]{16,}")
ALWAYS_EXCLUDED = (".env", "*/.env", ".env.*", "*/.env.*", "*.pem", "*.key")


def collect(project: Path, profile: dict) -> tuple[list[tuple[str, int]], list[dict]]:
    chosen: list[tuple[str, int]] = []
    skipped: list[dict] = []
    seen: set[str] = set()
    total = 0
    cap_file = int(profile.get("max_file_bytes", 5 * 2**20))
    cap_total = int(profile.get("max_total_bytes", 45 * 2**20))
    excludes = profile.get("exclude", [])
    for pattern in profile["include"]:
        for p in sorted(project.glob(pattern)):
            if not p.is_file():
                continue
            rel = p.relative_to(project).as_posix()
            if rel in seen:
                continue
            seen.add(rel)
            if any(fnmatch.fnmatch(rel, ex) for ex in (*excludes, *ALWAYS_EXCLUDED)):
                continue
            size = p.stat().st_size
            if size > cap_file:
                skipped.append({"path": rel, "bytes": size, "reason": "file_over_cap"})
                continue
            if SECRET_RE.search(p.read_bytes()):
                skipped.append({"path": rel, "bytes": size, "reason": "secret_like_content"})
                continue
            if total + size > cap_total:
                skipped.append({"path": rel, "bytes": size, "reason": "total_cap_reached"})
                continue
            chosen.append((rel, size))
            total += size
    return chosen, skipped


def build(project: Path, profile: dict, out_dir: Path, label: str) -> dict:
    chosen, skipped = collect(project, profile)
    stamp = time.strftime("%Y-%m-%d-%H%M")
    safe_label = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in label)[:60]
    name = f"{profile.get('name_prefix', 'project-LIGHT')}-{safe_label}-{stamp}.zip"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / name
    manifest = {"artifact": "light_manifest", "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                                            time.gmtime()),
                "label": label, "files": [], "skipped": skipped}
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for rel, size in chosen:
            data = (project / rel).read_bytes()
            z.writestr(rel, data)
            manifest["files"].append({"path": rel, "bytes": size,
                                      "sha256": hashlib.sha256(data).hexdigest()})
        z.writestr("LIGHT_MANIFEST.json", json.dumps(manifest, indent=1))
    with zipfile.ZipFile(out) as z:
        bad = z.testzip()
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    size = out.stat().st_size
    return {"name": name, "path": str(out), "bytes": size, "sha256": digest,
            "files": len(chosen), "skipped": len(skipped), "testzip_ok": bad is None,
            "within_50mb": size <= 50 * 2**20}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="controller/light_profile_v22.json")
    ap.add_argument("--label", default="manual")
    ap.add_argument("--project", default=str(PROJECT))
    ap.add_argument("--out-dir", default=None)
    a = ap.parse_args(argv)
    project = Path(a.project).resolve()
    profile = json.loads((project / a.profile).read_text(encoding="utf-8")) \
        if (project / a.profile).exists() else json.loads(Path(a.profile).read_text("utf-8"))
    out_dir = Path(a.out_dir) if a.out_dir else project.parent
    res = build(project, profile, out_dir, a.label)
    print("LIGHT_EXPORT_READY" if res["testzip_ok"] else "LIGHT_EXPORT_FAILED")
    print(f"LIGHT_EXPORT_NAME={res['name']}")
    print(f"LIGHT_EXPORT_PATH={res['path']}")
    print(f"LIGHT_EXPORT_SIZE_BYTES={res['bytes']}")
    print(f"LIGHT_EXPORT_SHA256={res['sha256']}")
    print(f"LIGHT_EXPORT_FILES={res['files']} SKIPPED={res['skipped']}")
    print(f"WITHIN_50MB={'YES' if res['within_50mb'] else 'NO'}")
    return 0 if res["testzip_ok"] and res["within_50mb"] else 1


if __name__ == "__main__":
    sys.exit(main())
