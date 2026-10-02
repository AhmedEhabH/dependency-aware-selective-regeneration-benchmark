#!/usr/bin/env python3
"""TRUE LIGHT export by profile (brain-authored kit; hash-verified).

Profile JSON: {"include": [glob, ...] (priority order), "exclude": [fnmatch, ...],
               "max_file_bytes": int, "max_total_bytes": int, "name_prefix": str}
Files are added in include order until the total cap; anything skipped is listed with
its reason inside LIGHT_MANIFEST.json (in the zip). Always produces a zip, verifies it
(testzip) and prints the LIGHT_EXPORT_READY block.

LIGHT filename convention (effective 2026-10-02 for FUTURE exports only):
    project-light-YYYY-MM-DD-HHMM.zip
- lowercase `project-light` prefix;
- timezone-aware LOCAL timestamp only in the filename (minute precision,
  machine local time at export creation);
- no STOP token / experiment name / result claim in the filename;
- historical LIGHT filenames are never renamed.
Collision handling: if the exact target filename already exists (same-minute
collision), the exporter FAILS CLOSED and never overwrites it.
The label / stop token / plan / phase / git identity / sha256 / timestamp are
recorded inside LIGHT_MANIFEST.json and in the printed LIGHT_EXPORT block.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
SECRET_RE = re.compile(rb"sk-or-v1-[0-9a-f]{16,}|Bearer\s+sk-[A-Za-z0-9_-]{16,}")
ALWAYS_EXCLUDED = (".env", "*/.env", ".env.*", "*/.env.*", "*.pem", "*.key")
LIGHT_PREFIX = "project-light"
NAME_RE = re.compile(r"^project-light-\d{4}-\d{2}-\d{2}-\d{4}\.zip$")


def future_name(now: datetime | None = None) -> str:
    """New-convention filename: project-light-YYYY-MM-DD-HHMM.zip.

    Uses the machine's timezone-aware local time at export creation, at minute
    precision. Pass ``now`` (a timezone-aware datetime) for deterministic tests.
    """
    dt = now if now is not None else datetime.now().astimezone()
    return f"{LIGHT_PREFIX}-{dt.strftime('%Y-%m-%d-%H%M')}.zip"


def _git_identity(project: Path) -> dict[str, str | None]:
    """Best-effort git commit/tag; never raises."""
    commit: str | None = None
    tag: str | None = None
    for args in (["rev-parse", "HEAD"], ["describe", "--tags", "--exact-match"]):
        try:
            r = subprocess.run(["git", *args], cwd=project, capture_output=True,
                               text=True, timeout=10)
            if r.returncode == 0 and r.stdout.strip():
                if args[0] == "rev-parse":
                    commit = r.stdout.strip()
                else:
                    tag = r.stdout.strip()
        except Exception:  # best effort only
            continue
    return {"commit": commit, "tag": tag}


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


def build(project: Path, profile: dict, out_dir: Path, label: str,
          now: datetime | None = None) -> dict:
    chosen, skipped = collect(project, profile)
    out_dir.mkdir(parents=True, exist_ok=True)
    name = future_name(now)
    out = out_dir / name
    if out.exists():
        return {"name": name, "path": str(out), "bytes": 0, "sha256": "",
                "files": len(chosen), "skipped": len(skipped), "testzip_ok": False,
                "within_50mb": True, "collision": True,
                "reason": "same-minute collision; failed closed without overwrite"}
    local = now if now is not None else datetime.now().astimezone()
    if local.tzinfo is None:
        local = local.astimezone()
    created_utc = local.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    created_local = local.isoformat(timespec="seconds")
    git = _git_identity(project)
    manifest = {
        "artifact": "light_manifest",
        "naming_convention": "project-light-YYYY-MM-DD-HHMM",
        "created_utc": created_utc,
        "export_timestamp_utc": created_utc,
        "created_local": created_local,
        "local_offset": local.strftime("%z"),
        "label": label,
        "stop_or_completion_token": label,
        "plan_id": profile.get("plan_id"),
        "phase": profile.get("phase"),
        "git_commit": git["commit"],
        "git_tag": git["tag"],
        "source_run_identifiers": profile.get("source_run_identifiers", []),
        "files": [], "skipped": skipped,
    }
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
            "within_50mb": size <= 50 * 2**20, "collision": False}


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
    if res.get("collision"):
        print("LIGHT_EXPORT_COLLISION")
        print(f"LIGHT_EXPORT_NAME={res['name']}")
        print(f"LIGHT_EXPORT_PATH={res['path']}")
        print("LIGHT_EXPORT_REASON=" + res.get("reason", ""))
        return 1
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
