"""Leakage + split-leakage tests for the M4A-2 scientific corpus (ZERO API).

Proves on the REAL materialized scientific corpus (when present) that:

- every scientific public bundle is free of hidden proxy / diff / gold content;
- the split freeze keeps MINER_DEV disjoint from scientific splits;
- no accepted scientific pair shares a proxy path AND a PR reference across
  different splits (related changes never cross splits);
- no scientific case leaks intent path mentions;
- M1/M3 frozen evidence is unchanged.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from benchmark.real_commits import validation
from benchmark.real_commits import validation_scientific as vs
from benchmark.real_commits.models import SplitRole

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
DATASET_DIR = PROJECT_DIR / "benchmark_data" / "real_commit_impact_v1"
CACHE_DIR = PROJECT_DIR / "dist" / "real-commit-cache" / "djangocms"

PR_RE = re.compile(r"#(\d+)")


def _scientific_cases() -> list[dict]:
    manifest_path = DATASET_DIR / "scientific_manifest.json"
    if not manifest_path.is_file():
        pytest.skip("scientific manifest not materialized on this machine")
    return json.loads(manifest_path.read_text(encoding="utf-8")).get("cases", [])


def test_every_scientific_public_bundle_leakage_free() -> None:
    cases = _scientific_cases()
    if not cases:
        pytest.skip("no scientific cases")
    for case in cases:
        cid = case["case_id"]
        leak = validation.check_public_bundle_leakage(DATASET_DIR, cid, partition="scientific")
        assert leak["passed"], f"{cid}: {[c for c in leak['checks'] if not c['ok']]}"


def test_no_scientific_intent_path_leakage() -> None:
    cases = _scientific_cases()
    if not cases:
        pytest.skip("no scientific cases")
    for case in cases:
        assert case["intent_mentions_changed_path"] is False, case["case_id"]


def test_miner_dev_disjoint_from_scientific() -> None:
    md_path = DATASET_DIR / "miner_dev_manifest.json"
    sci_path = DATASET_DIR / "scientific_manifest.json"
    if not (md_path.is_file() and sci_path.is_file()):
        pytest.skip("corpus not materialized")
    md = json.loads(md_path.read_text(encoding="utf-8"))
    sci = json.loads(sci_path.read_text(encoding="utf-8"))
    md_ids = {c["case_id"] for c in md.get("cases", [])}
    sci_ids = set(sci.get("case_ids", []))
    assert not (md_ids & sci_ids)


def test_related_changes_never_cross_splits() -> None:
    """No accepted pair shares a proxy path AND a PR ref in different splits."""
    cases = _scientific_cases()
    split_freeze_path = DATASET_DIR / "split_freeze.json"
    if not cases or not split_freeze_path.is_file():
        pytest.skip("corpus not materialized")
    split_freeze = json.loads(split_freeze_path.read_text(encoding="utf-8"))
    assignment = split_freeze.get("assignment", {})

    crossings: list[tuple[str, str]] = []
    for i in range(len(cases)):
        for j in range(i + 1, len(cases)):
            a, b = cases[i], cases[j]
            shared_paths = set(a.get("change_statuses", {})) & set(b.get("change_statuses", {}))
            if not shared_paths:
                continue
            shared_prs = set(PR_RE.findall(a.get("intent_text", ""))) & set(
                PR_RE.findall(b.get("intent_text", ""))
            )
            if shared_prs and assignment.get(a["case_id"]) != assignment.get(b["case_id"]):
                crossings.append((a["case_id"], b["case_id"]))
    assert crossings == []


def test_every_split_is_valid() -> None:
    cases = _scientific_cases()
    if not cases:
        pytest.skip("no scientific cases")
    for case in cases:
        assert case["split"] in vs.SCIENTIFIC_SPLITS, case["case_id"]
        assert case["partition_role"] == "SCIENTIFIC", case["case_id"]
        assert case["split"] != SplitRole.MINER_DEV.value, case["case_id"]


def test_frozen_m1_m3_evidence_unchanged() -> None:
    frozen_universe = validation.frozen_universe_regression()
    frozen_graph = validation.frozen_graph_regression()
    assert frozen_universe["count_ok"] and frozen_universe["hash_ok"]
    assert frozen_graph["edge_count_ok"] and frozen_graph["hash_ok"]
    assert frozen_universe["count"] == 144
    assert frozen_graph["edge_count"] == 562
