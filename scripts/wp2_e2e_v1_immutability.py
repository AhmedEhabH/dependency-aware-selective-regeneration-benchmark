#!/usr/bin/env python3
"""Mission-12 A2: protect Smoke-v1 evidence.

Read-only against v1: enumerates every frozen v1 scientific result artifact,
hashes the committed (HEAD) bytes, resolves every existing v1 tag to its commit
SHA, and persists research/wp2/e2e_smoke_eng_v1/erratum/v1_immutability_before.json.
No v1 file is written or altered.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
V1_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v1"
ERRATUM_DIR = V1_ROOT / "erratum"
V1_TAGS = [
    "wp2-e2e-smoke-eng-v1-freeze-2026-09-28",
    "wp2-e2e-smoke-eng-v1-result-2026-09-28",
]


def git(args: list[str]) -> str:
    out = subprocess.run(
        ["git", "-C", str(PROJECT), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.strip()


def main() -> None:
    files = git(["ls-files", "research/wp2/e2e_smoke_eng_v1"]).splitlines()
    artifacts: dict[str, dict] = {}
    for rel in files:
        blob = subprocess.run(
            ["git", "-C", str(PROJECT), "cat-file", "blob", f"HEAD:{rel}"],
            capture_output=True,
        )
        if blob.returncode != 0:
            raise SystemExit(f"FATAL: cannot read HEAD blob for {rel}")
        digest = hashlib.sha256(blob.stdout).hexdigest()
        artifacts[rel] = {
            "sha256": digest,
            "bytes": len(blob.stdout),
            "tracked": True,
        }

    tags: dict[str, dict] = {}
    for tag in V1_TAGS:
        tags[tag] = {
            "tag_object_sha": git(["rev-parse", tag]),
            "peeled_commit_sha": git(["rev-parse", f"{tag}^{{commit}}"]),
        }

    record = {
        "artifact": "v1_immutability_before",
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "head": git(["rev-parse", "HEAD"]),
        "origin_main": git(["rev-parse", "origin/main"]),
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "tags": tags,
        "flags": {
            "V1_RESULT_JSON_MUTABLE": "NO",
            "V1_TAG_MOVE_ALLOWED": "NO",
        },
    }
    ERRATUM_DIR.mkdir(parents=True, exist_ok=True)
    out = ERRATUM_DIR / "v1_immutability_before.json"
    out.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    # verify round-trip integrity
    check = json.loads(out.read_text(encoding="utf-8"))
    assert check["artifact_count"] == len(artifacts) == len(check["artifacts"])
    assert check["head"] == record["head"]
    assert set(check["tags"]) == set(V1_TAGS)
    print(f"V1_IMMUTABILITY_BEFORE={out}")
    print(f"ARTIFACTS_HASHED={len(artifacts)}")
    print(f"TAGS_RESOLVED={json.dumps({k: v['peeled_commit_sha'] for k, v in tags.items()})}")
    print(f"HEAD={record['head']}")
    print("CHECK=OK")


if __name__ == "__main__":
    main()