#!/usr/bin/env python3
"""WP-1a Correction A - SIP scientific model/provider provenance.

Mechanically recovers the scientific model identity of the frozen Saleor-300
SIP run from the authoritative run records
(research/saleor-reserve-300-rmcss/sip_300_run_records.jsonl) WITHOUT
hard-coding any claim. Also hashes the frozen prompt-template source module
(src/benchmark/real_commits/p1_evaluation.py) that defines the P1 prompt/model
constants.

Output: research/wp1a/sip_scientific_model_provenance.json
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = _PROJECT_DIR / "research" / "wp1a"
SIP_RECORDS = _PROJECT_DIR / "research" / "saleor-reserve-300-rmcss" / "sip_300_run_records.jsonl"
P1_SOURCE = _PROJECT_DIR / "src" / "benchmark" / "real_commits" / "p1_evaluation.py"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    records = [
        json.loads(line)
        for line in SIP_RECORDS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(records) != 300:
        print(f"FATAL: expected 300 run records, got {len(records)}")
        return 1

    identity_fields = (
        "scientific_model", "provider_tag", "exact_model", "temperature",
        "completion_cap", "graph", "serialization_policy",
    )
    identity: dict[str, object] = {}
    for field in identity_fields:
        counter = Counter(str(r.get(field)) for r in records)
        identity[field] = {
            "value": max(counter, key=counter.get),
            "n_matching": counter[max(counter, key=counter.get)],
            "n_total": len(records),
            "consistent_across_all_tasks": len(counter) == 1,
        }
        if len(counter) != 1:
            print(f"FATAL: field {field} inconsistent across records: {counter}")
            return 1

    terminal = Counter(r.get("terminal_status") for r in records)
    prompt_hashes = sorted({str(r.get("prompt_sha256")) for r in records})
    raw_hashes = sorted({str(r.get("raw_response_sha256")) for r in records if r.get("raw_response_sha256")})
    pricing = Counter(str(r.get("pricing_source")) for r in records if r.get("pricing_source"))
    provider_name = Counter(str(r.get("provider_name")) for r in records if r.get("provider_name"))

    p1_source = P1_SOURCE.read_text(encoding="utf-8")

    artifact = {
        "wp1a": "sip_scientific_model_provenance",
        "generated_utc": datetime.now(UTC).isoformat(),
        "source": "research/saleor-reserve-300-rmcss/sip_300_run_records.jsonl (authoritative)",
        "n_records": len(records),
        "identity": identity,
        "terminal_status": dict(terminal),
        "per_task_prompt_hash": {
            "n_unique": len(prompt_hashes),
            "n_total": len(records),
            "example": prompt_hashes[:3],
        },
        "per_task_raw_response_hash": {
            "n_unique": len(raw_hashes),
            "n_total": len(records),
        },
        "pricing_source": dict(pricing.most_common()),
        "provider_name": dict(provider_name.most_common()),
        "prompt_template_source": {
            "path": "src/benchmark/real_commits/p1_evaluation.py",
            "sha256": _sha256_text(p1_source),
            "note": "P1_COMMON_PROMPT_TEMPLATE + P1_SERIALIZATION_POLICY_SPARSE + "
                    "P1_MODEL/P1_PROVIDER_TAG/P1_TEMPERATURE/P1_MAX_COMPLETION_TOKENS "
                    "defined here; prompt_sha256 per task recorded in run records.",
        },
        "conclusion": (
            "IDENTITY_MECHANICALLY_RECOVERED_AND_CONSISTENT" if all(
                v["consistent_across_all_tasks"] for v in identity.values()
            ) else "IDENTITY_INCONSISTENT"
        ),
        "future_agent_arm_model_requirement": (
            "The future WP-1b repository-agent generative arm MUST use the SAME "
            "scientific model identity as the frozen SIP run to avoid model "
            "mismatch. The OpenCode coding model is NOT the scientific arm model."
        ),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "sip_scientific_model_provenance.json"
    out.write_text(json.dumps(artifact, indent=1), encoding="utf-8")
    print(json.dumps(artifact, indent=1))
    print("[wp1a-prov] conclusion:", artifact["conclusion"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
