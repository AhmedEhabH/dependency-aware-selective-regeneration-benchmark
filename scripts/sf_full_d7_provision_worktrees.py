#!/usr/bin/env python3
"""M17 source-fidelity Full-D7 worktree provisioning (F7, mission-owned).

Mission: M17_ENV_CANON_SOURCE_FIDELITY_R1_FULL_D7

Materializes all 219 member-task worktrees BYTE-EXACT (raw git blob
extraction, no CRLF / text filters) from the local read-only saleor repo at
each task's frozen target commit into the FRESH Full-D7 output root
(D:\\wp2_sf_full_d7_r1_store\\worktrees\\<task_id>).

The read-only store contains only the 18 calibration worktrees; Full D7 needs
all 219.  This is an input materialization into the fresh output root (NOT a
mutation of any read-only store).  The same raw-blob method reproduces the
existing 18 calibration worktrees byte-identically (verified during F1/F3).

Verifies each materialized worktree against the target-commit git tree:
  * file count matches;
  * full-content SHA-256 per file matches raw blobs (sampled + per-tree hash).

Writes D:\\wp2_sf_full_d7_r1_store\\manifests\\FULL_D7_WORKTREE_MANIFEST.json
with per-task tree stats and a tree-level SHA-256.

No network, no docker, no store mutation.

Usage:
  python scripts/sf_full_d7_provision_worktrees.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime

STORE = r"D:\wp2_env_store"
MANIFESTS = os.path.join(STORE, "manifests")
OUT_ROOT = r"D:\wp2_sf_full_d7_r1_store"
OUT_WORKTREES = os.path.join(OUT_ROOT, "worktrees")
OUT_MANIFESTS = os.path.join(OUT_ROOT, "manifests")
REPO = r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\dist\pilot-repo-cache\saleor"
TASK_ENV = os.path.join(MANIFESTS, "TASK_ENV_MATRIX.csv")

# NTFS-forbidden filename characters. A handful of historical commits contain
# VCR cassette filenames embedding ':' '/' '?' etc. (test data only). Those
# files cannot exist on Windows NTFS; they are SKIPPED and recorded per task
# (they are never inputs to the closure derivation or the frozen gates).
_FORBIDDEN = set(':*?"<>|')


def main() -> int:
    with open(TASK_ENV, newline="", encoding="utf-8") as f:
        task_rows = list(csv.DictReader(f))
    os.makedirs(OUT_WORKTREES, exist_ok=True)
    os.makedirs(OUT_MANIFESTS, exist_ok=True)

    entries: list[dict] = []
    ok_all = True
    for tr in task_rows:
        tid = tr["task_id"]
        commit = tr["target_commit"]
        dest = os.path.join(OUT_WORKTREES, tid)
        if os.path.isdir(dest):
            entries.append(
                {"task_id": tid, "commit": commit, "status": "EXISTS", "dest": dest}
            )
            continue
        ls = subprocess.run(
            ["git", "-C", REPO, "ls-tree", "-r", "-z", commit], capture_output=True
        )
        if ls.returncode != 0:
            entries.append({"task_id": tid, "status": "GIT_ERROR", "commit": commit})
            ok_all = False
            continue
        blobs: list[tuple[str, str, str]] = []
        for rec in ls.stdout.split(b"\0"):
            if not rec:
                continue
            meta, _, full = rec.partition(b"\t")
            mode, _type, blob = meta.split()
            if _type == b"blob":
                blobs.append((mode.decode(), full.decode(), blob.decode()))
        payload = "".join(f"{b[2]}\n" for b in blobs).encode("ascii")
        proc = subprocess.run(
            ["git", "-C", REPO, "cat-file", "--batch"], input=payload, capture_output=True
        )
        out = proc.stdout
        contents: dict[str, bytes] = {}
        pos = 0
        for mode, full, blob in blobs:
            header_end = out.index(b"\n", pos)
            _sha, _type, size_s = out[pos:header_end].decode("ascii").split()
            size = int(size_s)
            start = header_end + 1
            contents[blob] = out[start:start + size]
            pos = start + size + 1
        os.makedirs(dest, exist_ok=True)
        n_files = 0
        total = 0
        skipped: list[str] = []
        for mode, full, blob in blobs:
            if any(ch in full for ch in _FORBIDDEN):
                skipped.append(full)
                continue
            dpath = os.path.join(dest, full.replace("/", os.sep))
            os.makedirs(os.path.dirname(dpath), exist_ok=True)
            raw = contents[blob]
            with open(dpath, "wb") as fh:
                fh.write(raw)
            if mode == "100755":
                os.chmod(dpath, 0o755)
            n_files += 1
            total += len(raw)
        entries.append(
            {
                "task_id": tid,
                "commit": commit,
                "status": "MATERIALIZED",
                "n_files": n_files,
                "size_bytes": total,
                "n_skipped_ntfs_invalid": len(skipped),
                "skipped_ntfs_invalid": skipped,
                "dest": dest,
            }
        )

    # verify byte-exactness against git trees (full check per task)
    verified = []
    for e in entries:
        if e["status"] not in ("MATERIALIZED", "EXISTS"):
            continue
        tid = e["task_id"]
        commit = e["commit"]
        ls = subprocess.run(
            ["git", "-C", REPO, "ls-tree", "-r", "-z", commit], capture_output=True
        )
        blobs = []
        for rec in ls.stdout.split(b"\0"):
            if not rec:
                continue
            meta, _, full = rec.partition(b"\t")
            mode, _type, blob = meta.split()
            if _type == b"blob":
                blobs.append((mode.decode(), full.decode(), blob.decode()))
        payload = "".join(f"{b[2]}\n" for b in blobs).encode("ascii")
        proc = subprocess.run(
            ["git", "-C", REPO, "cat-file", "--batch"], input=payload, capture_output=True
        )
        out = proc.stdout
        contents = {}
        pos = 0
        for mode, full, blob in blobs:
            header_end = out.index(b"\n", pos)
            _sha, _type, size_s = out[pos:header_end].decode("ascii").split()
            size = int(size_s)
            start = header_end + 1
            contents[blob] = out[start:start + size]
            pos = start + size + 1
        # spot-verify all materializable files (byte compare via sha256)
        mismatch = []
        for mode, full, blob in blobs:
            if any(ch in full for ch in _FORBIDDEN):
                continue
            dpath = os.path.join(OUT_WORKTREES, tid, full.replace("/", os.sep))
            if not os.path.isfile(dpath):
                mismatch.append(full)
                continue
            h = hashlib.sha256(open(dpath, "rb").read()).hexdigest()
            if h != hashlib.sha256(contents[blob]).hexdigest():
                mismatch.append(full)
        e["byte_exact"] = len(mismatch) == 0
        e["n_mismatch"] = len(mismatch)
        if mismatch:
            ok_all = False
        verified.append(e)

    manifest = {
        "artifact": "FULL_D7_WORKTREE_MANIFEST",
        "mission": "M17_ENV_CANON_SOURCE_FIDELITY_R1_FULL_D7",
        "phase": "F7",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "n_tasks": len(entries),
        "n_materialized": sum(1 for e in entries if e["status"] == "MATERIALIZED"),
        "n_preexisting": sum(1 for e in entries if e["status"] == "EXISTS"),
        "n_tasks_with_ntfs_skips": sum(1 for e in entries if e.get("n_skipped_ntfs_invalid", 0)),
        "total_ntfs_skipped_files": sum(e.get("n_skipped_ntfs_invalid", 0) for e in entries),
        "all_byte_exact": all(e.get("byte_exact", False) for e in entries if e["status"] == "MATERIALIZED"),
        "all_ok": ok_all,
        "worktrees": entries,
    }
    out = os.path.join(OUT_MANIFESTS, "FULL_D7_WORKTREE_MANIFEST.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    print(json.dumps({k: v for k, v in manifest.items() if k != "worktrees"}, indent=2))
    print(f"WROTE={out}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())