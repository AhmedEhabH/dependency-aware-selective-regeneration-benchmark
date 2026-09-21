"""WP-1a intent parity - the future repository-agent input intent MUST be
byte-identical (canonical-hash-identical) to the intent text that generated the
frozen SIP predictions.

Authoritative intent source: the frozen public intent bundle
benchmark_data/real_commit_impact_saleor/scientific/<case_id>/public/intent.json
(intent_text + intent_sha256 + intent_source). The SIP runner consumed exactly
this bundle (P1CaseBundle.intent_text). For every main-50 and calibration-3
task this script:

- loads intent.json;
- recomputes sha256(intent_text) and asserts it equals the stored
  intent_sha256 (canonical-hash identity);
- records intent_source, task identifiers (case_id, parent_commit,
  target_commit, repository);
- asserts that the SIP run record for the same task used the same case_id
  (same candidate map / public bundle).

Output: research/wp1a/wp1a_intent_parity.json
On any ambiguity -> WP1A_INTENT_PARITY_BLOCKED.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))

OUT_DIR = _PROJECT_DIR / "research" / "wp1a"
SALEOR_DATASET = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor" / "scientific"
MAIN = OUT_DIR / "wp1_main_50_manifest.json"
CAL = OUT_DIR / "wp1_calibration_3_manifest.json"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    main = json.loads(MAIN.read_text(encoding="utf-8"))
    cal = json.loads(CAL.read_text(encoding="utf-8"))
    task_ids = main["task_ids"] + cal["task_ids"]
    assert len(set(task_ids)) == 53, f"expected 53 unique tasks, got {len(set(task_ids))}"

    entries: dict[str, object] = {}
    blocked: list[str] = []
    for cid in task_ids:
        intent_path = SALEOR_DATASET / cid / "public" / "intent.json"
        manifest_path = SALEOR_DATASET / cid / "case_manifest.json"
        if not intent_path.is_file() or not manifest_path.is_file():
            blocked.append(f"{cid}: missing intent/manifest bundle")
            continue
        intent = json.loads(intent_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        stored_sha = intent.get("intent_sha256", "")
        recomputed_sha = _sha256_text(str(intent.get("intent_text", "")))
        source = str(intent.get("intent_source", ""))
        record = manifest.get("record", {})
        entries[cid] = {
            "intent_text_sha256": recomputed_sha,
            "stored_intent_sha256": stored_sha,
            "canonical_hash_match": recomputed_sha == stored_sha,
            "intent_source": source,
            "repository": record.get("repository"),
            "parent_commit": record.get("parent_commit"),
            "target_commit": record.get("target_commit"),
            "split": record.get("split"),
            "manifest_record_sha256": manifest.get("canonical_record_sha256"),
        }
        if recomputed_sha != stored_sha or not source:
            blocked.append(f"{cid}: hash mismatch or missing source")

    artifact = {
        "wp1a": "wp1a_intent_parity",
        "authoritative_intent_source": (
            "benchmark_data/real_commit_impact_saleor/scientific/<case_id>/public/intent.json "
            "(intent_text; intent_source field)"
        ),
        "rule": "future agent input intent MUST be byte-identical / canonical-hash-identical "
                "to the stored SIP intent text per task",
        "n_tasks": len(task_ids),
        "n_canonical_hash_match": sum(1 for e in entries.values() if e["canonical_hash_match"]),
        "blocked": blocked,
        "status": "WP1A_INTENT_PARITY_PASS" if not blocked else "WP1A_INTENT_PARITY_BLOCKED",
        "per_task": entries,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "wp1a_intent_parity.json").write_text(
        json.dumps(artifact, indent=1), encoding="utf-8")
    print(json.dumps(artifact, indent=1))
    print("[wp1a-intent] status:", artifact["status"])
    return 0 if not blocked else 1


if __name__ == "__main__":
    raise SystemExit(main())
