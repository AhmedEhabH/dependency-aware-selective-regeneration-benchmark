"""Integration tests: RealCommitImpactDataset-v1 leakage barrier (M4A-1, ZERO API).

Proves that serializing the public/ inference bundle never exposes the hidden
observed change-set proxy, changed-path proxy list, target diff text, target
file contents, or semantic gold/action labels.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from benchmark.real_commits import validation
from benchmark.real_commits.models import canonical_json


def _write_artifacts(root: Path) -> Path:
    """Write a public bundle + hidden proxy and return the dataset dir."""
    dataset = root / "dataset"
    case = dataset / "miner_dev" / "djangocms-rc-deadbeef"
    (case / "public").mkdir(parents=True)
    (case / "hidden").mkdir(parents=True)

    proxy_paths = ["cms/models/pagemodel.py", "cms/api.py"]
    intent = {
        "schema_version": "v1",
        "case_id": "djangocms-rc-deadbeef",
        "intent_text": "fix: pagemodel publish",
    }
    universe = {
        "schema_version": "v1",
        "records": [
            {"path": "cms/models/pagemodel.py"},
            {"path": "cms/api.py"},
            {"path": "cms/models/pluginmodel.py"},
        ],
    }
    graph = {"schema_version": "v1", "edges": [["cms/models/pagemodel.py", "cms/api.py"]]}
    proxy = {
        "schema_version": "v1",
        "paths": proxy_paths,
        "statuses": {p: "M" for p in proxy_paths},
        "count": 2,
    }
    (case / "public" / "intent.json").write_text(canonical_json(intent), encoding="utf-8")
    (case / "public" / "candidate_universe.json").write_text(
        canonical_json(universe), encoding="utf-8"
    )
    (case / "public" / "dependency_graph.json").write_text(
        canonical_json(graph), encoding="utf-8"
    )
    (case / "hidden" / validation.HIDDEN_PROXY_FILENAME).write_text(
        canonical_json(proxy), encoding="utf-8"
    )
    return dataset


def test_public_bundle_free_of_hidden_proxy() -> None:
    with tempfile.TemporaryDirectory(prefix="rc-leak-") as tmp:
        dataset = _write_artifacts(Path(tmp))
        result = validation.check_public_bundle_leakage(dataset, "djangocms-rc-deadbeef")
        assert result["passed"] is True
        labels = {c["check"]: c["ok"] for c in result["checks"]}
        assert labels["no_proxy_filename_in_public"]
        assert labels["no_hidden_field_names_in_public"]
        assert labels["no_proxy_status_marker_rows_in_public"]
        assert labels["no_target_diff_text_in_public"]
        assert labels["no_hidden_proxy_payload_embedded_in_public"]
        assert labels["no_semantic_gold_tokens_in_public"]


def test_public_bundle_with_proxy_injection_fails_closed() -> None:
    with tempfile.TemporaryDirectory(prefix="rc-leak-inject-") as tmp:
        dataset = _write_artifacts(Path(tmp))
        case = dataset / "miner_dev" / "djangocms-rc-deadbeef"
        # Maliciously inject the proxy payload into a public artifact.
        proxy = json.loads((case / "hidden" / validation.HIDDEN_PROXY_FILENAME).read_text(encoding="utf-8"))
        (case / "public" / "candidate_universe.json").write_text(
            canonical_json({"records": [], "proxy": proxy}),
            encoding="utf-8",
        )
        result = validation.check_public_bundle_leakage(dataset, "djangocms-rc-deadbeef")
        assert result["passed"] is False
        labels = {c["check"]: c["ok"] for c in result["checks"]}
        assert not labels["no_hidden_field_names_in_public"]
        assert not labels["no_hidden_proxy_payload_embedded_in_public"]


def test_target_diff_text_in_public_fails_closed() -> None:
    with tempfile.TemporaryDirectory(prefix="rc-leak-diff-") as tmp:
        dataset = _write_artifacts(Path(tmp))
        case = dataset / "miner_dev" / "djangocms-rc-deadbeef"
        # Maliciously embed a git diff text blob into intent.json.
        intent_path = case / "public" / "intent.json"
        payload = json.loads(intent_path.read_text(encoding="utf-8"))
        payload["intent_text"] = (
            "diff --git a/cms/models/pagemodel.py b/cms/models/pagemodel.py\n"
            "--- a/...\n+++ b/...\n"
        )
        intent_path.write_text(canonical_json(payload), encoding="utf-8")
        result = validation.check_public_bundle_leakage(dataset, "djangocms-rc-deadbeef")
        assert result["passed"] is False
        labels = {c["check"]: c["ok"] for c in result["checks"]}
        assert not labels["no_target_diff_text_in_public"]


def test_semantic_gold_labels_in_public_fail_closed() -> None:
    with tempfile.TemporaryDirectory(prefix="rc-leak-gold-") as tmp:
        dataset = _write_artifacts(Path(tmp))
        case = dataset / "miner_dev" / "djangocms-rc-deadbeef"
        intent_path = case / "public" / "intent.json"
        payload = json.loads(intent_path.read_text(encoding="utf-8"))
        payload["intent_text"] = "the plan says REGENERATE for cms/models/pagemodel.py"
        intent_path.write_text(canonical_json(payload), encoding="utf-8")
        result = validation.check_public_bundle_leakage(dataset, "djangocms-rc-deadbeef")
        assert result["passed"] is False
        labels = {c["check"]: c["ok"] for c in result["checks"]}
        assert not labels["no_semantic_gold_tokens_in_public"]


def test_public_bundle_text_includes_three_artifacts() -> None:
    with tempfile.TemporaryDirectory(prefix="rc-leak-text-") as tmp:
        dataset = _write_artifacts(Path(tmp))
        text = validation.public_bundle_text(dataset, "djangocms-rc-deadbeef")
        # Content from all three public artifacts must be present.
        assert "fix: pagemodel publish" in text  # intent.json
        assert "cms/models/pluginmodel.py" in text  # candidate_universe.json
        assert "dependency_graph" not in text  # artifact content, not the file name
        # But the graph edge content IS present.
        assert "cms/api.py" in text
