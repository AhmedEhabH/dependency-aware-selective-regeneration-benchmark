"""WP-1a Correction A - scientific model/provider provenance tests."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

RESEARCH = PROJECT_DIR / "research" / "saleor-reserve-300-rmcss"
WP1A = PROJECT_DIR / "research" / "wp1a"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_records_all_consistent_model_identity() -> None:
    records = [
        json.loads(line)
        for line in (RESEARCH / "sip_300_run_records.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(records) == 300
    for field, expected in (
        ("scientific_model", "qwen/qwen3-coder"),
        ("provider_tag", "deepinfra/turbo"),
        ("exact_model", "openrouter:qwen/qwen3-coder@deepinfra/turbo"),
        ("temperature", 0.0),
        ("completion_cap", 16384),
    ):
        values = {str(r.get(field)) for r in records}
        assert values == {str(expected)}, f"{field}: {values}"


def test_prompt_hash_per_task_unique_and_recorded() -> None:
    records = [
        json.loads(line)
        for line in (RESEARCH / "sip_300_run_records.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    hashes = {r["prompt_sha256"] for r in records}
    assert len(hashes) == 300


def test_provenance_artifact_consistent_with_records() -> None:
    prov = json.loads((WP1A / "sip_scientific_model_provenance.json").read_text(encoding="utf-8"))
    assert prov["conclusion"] == "IDENTITY_MECHANICALLY_RECOVERED_AND_CONSISTENT"
    assert all(v["consistent_across_all_tasks"] for v in prov["identity"].values())
    assert prov["identity"]["scientific_model"]["value"] == "qwen/qwen3-coder"
    assert prov["identity"]["provider_tag"]["value"] == "deepinfra/turbo"


def test_provenance_artifact_rejects_deepseek_claim() -> None:
    """The WP-1 draft's DeepSeek model claim is FALSE; the artifact must
    record the mechanically-recovered qwen identity, never DeepSeek."""
    prov = json.loads((WP1A / "sip_scientific_model_provenance.json").read_text(encoding="utf-8"))
    model = prov["identity"]["scientific_model"]["value"].lower()
    assert "deepseek" not in model
    assert "qwen" in model


def test_prompt_template_source_sha() -> None:
    src = (PROJECT_DIR / "src" / "benchmark" / "real_commits" / "p1_evaluation.py").read_text(encoding="utf-8")
    prov = json.loads((WP1A / "sip_scientific_model_provenance.json").read_text(encoding="utf-8"))
    assert prov["prompt_template_source"]["sha256"] == _sha256_text(src)
