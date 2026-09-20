"""Issue-grounded intent headroom - frozen issue corpus (T3).

Before ranking evaluation, save a compact frozen corpus:

  - case_id
  - repository
  - provenance category
  - issue IDs
  - created_at / updated_at per issue
  - exact title/body text
  - retrieval timestamp
  - SHA256 of normalized text
  - temporal-clean flag
  - target_commit_time (audit only)

Compute a corpus-level SHA256 manifest over the canonical JSON bytes.
NO secrets/tokens in the artifact.
"""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

NORMALIZE_EXCLUDE = ("\r\n", "\r")
NORMALIZE_JOIN = ("\n", "\n")


def normalized_text(title: str, body: str) -> str:
    """CRLF -> LF, collapse, title + '\n' + body."""
    t = (title or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    b = (body or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    return f"{t}\n{b}"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def build_corpus_record(
    *,
    case_id: str,
    repository: str,
    provenance: str,
    issue_numbers: tuple[int, ...],
    created_at: tuple[str, ...],
    updated_at: tuple[str, ...],
    titles: tuple[str, ...],
    bodies: tuple[str, ...],
    temporal_flags: tuple[str, ...],
    target_commit_time: str,
) -> dict[str, Any]:
    """One frozen corpus record. `titles`/`bodies` align with `issue_numbers`."""
    texts = [normalized_text(t, b) for t, b in zip(titles, bodies, strict=True)]
    return {
        "case_id": case_id,
        "repository": repository,
        "provenance": provenance,
        "issue_numbers": list(issue_numbers),
        "created_at": list(created_at),
        "updated_at": list(updated_at),
        "title": list(titles),
        "body": list(bodies),
        "normalized_sha256": [sha256_text(t) for t in texts],
        "temporal_flag": list(temporal_flags),
        "target_commit_time": target_commit_time,
        "retrieved_at_utc": _utcnow_iso(),
    }


def save_corpus(path: Path, records: list[dict[str, Any]]) -> dict[str, str]:
    """Persist the corpus + compute a deterministic corpus-level SHA256.

    GETSHA: the digest is computed over the CANONICAL corpus content with only
    the volatile wall-clock timestamps (generated_at_utc / retrieved_at_utc)
    stripped, so a frozen corpus hash is stable across regeneration runs. The
    timestamps are still persisted for the retrieval-timestamp record; they
    are just not part of the SHA.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    sorted_records = sorted(records, key=lambda r: (r["repository"], r["case_id"]))
    canonical = {
        "corpus_version": 1,
        "records": [
            {k: v for k, v in r.items() if k not in ("retrieved_at_utc",)}
            for r in sorted_records
        ],
    }
    digest = hashlib.sha256(
        json.dumps(canonical, indent=1, sort_keys=True).encode("utf-8")).hexdigest()
    payload = {"corpus_version": 1, "generated_at_utc": _utcnow_iso(),
               "corpus_sha256": digest, "records": sorted_records}
    path.write_text(json.dumps(payload, indent=1, sort_keys=True), encoding="utf-8")
    manifest = {
        "corpus_sha256": digest,
        "records": len(sorted_records),
        "path": str(path),
    }
    return manifest


def load_corpus(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
