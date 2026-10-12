"""Rehash every recorded input and refresh its index without mutating evidence."""

import hashlib
import json
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent
manifest = json.loads((OUT / "FAILURE_EVIDENCE_MANIFEST.json").read_text(encoding="utf-8"))
files = manifest["files"]
git_blobs = manifest["git_blobs"]
failures = []
for path, record in files.items():
    raw = Path(path).read_bytes()
    if len(raw) != record["bytes"] or hashlib.sha256(raw).hexdigest() != record["sha256"]:
        failures.append(path)
for identity, record in git_blobs.items():
    raw = subprocess.check_output(["git", "-C", manifest["source_repo"], "show", identity])
    if len(raw) != record["bytes"] or hashlib.sha256(raw).hexdigest() != record["sha256"]:
        failures.append(identity)
receipt = {
    "file_inputs_checked": len(files),
    "git_blobs_checked": len(git_blobs),
    "mismatches": failures,
    "FROZEN_EVIDENCE_CHANGED": bool(failures),
    "status": "PASS" if not failures else "FAIL",
    "scope": "Every audit-consumed recorded file and historical Git blob; not an exhaustive disk-image comparison.",
}
(OUT / "INPUT_IMMUTABILITY_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
index = [
    "# Failure evidence index",
    "",
    "Raw SHA-256 hashes; no wheel payloads or large logs copied.",
    "",
    "| Local input | Bytes | SHA-256 |",
    "|---|---:|---|",
]
index += [f"| `{p}` | {v['bytes']} | `{v['sha256']}` |" for p, v in sorted(files.items())]
index += [
    "",
    f"{len(git_blobs)} exact historical Git blob identities are recorded in FAILURE_EVIDENCE_MANIFEST.json.",
    "SOURCE_FIDELITY_COMPARISON.json distinguishes raw lock SHA from the frozen raw-plus-LF convention.",
]
(OUT / "FAILURE_EVIDENCE_INDEX.md").write_text("\n".join(index) + "\n", encoding="utf-8")
print(json.dumps(receipt, indent=2))
if failures:
    raise SystemExit(1)
