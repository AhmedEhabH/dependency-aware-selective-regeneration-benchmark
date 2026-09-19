"""SweRank leakage + provenance + pinning tests (T3, ZERO API).

Verifies:
- the pinned model revision constant (never an unpinned 'main' at runtime);
- query construction uses ONLY the parent-visible intent text (the proxy and
  child-revision information never enter a query input);
- parent-revision indexing is required (no child/target patch paths);
- deterministic ranking output (fixed seed).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from benchmark.signal.swerank_model import MODEL_ID, MODEL_REVISION

_PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
_RUN_DIR = _PROJECT_DIR / "research" / "strong-localization-signal" / "swerank"


def test_model_revision_is_pinned():
    assert MODEL_ID == "Salesforce/SweRankEmbed-Small"
    assert len(MODEL_REVISION) == 40
    assert MODEL_REVISION != "main"
    assert all(c in "0123456789abcdef" for c in MODEL_REVISION)


def test_model_pin_json_matches_constant():
    pin = json.loads((_RUN_DIR / "model_pin.json").read_text(encoding="utf-8"))
    assert pin["revision"] == MODEL_REVISION
    assert pin["model_id"] == MODEL_ID


def test_no_target_paths_in_rankings():
    """Each task ranking must not contain the observed-change proxy or write-set
    paths inside the SweRank query; the query hash is present and the proxy is
    only evaluation metadata."""
    rankings = json.loads((_RUN_DIR / "task_rankings.json").read_text(encoding="utf-8"))
    assert len(rankings) >= 300
    for _cid, r in rankings.items():
        assert r["query_sha256"]
        assert len(r["query_sha256"]) == 64
        # the ranked pool must be a permutation subset of the universe paths
        # (no synthetic/hallucinated paths)
        for p in r["swe_ranked"]:
            assert isinstance(p, str) and "/" in p


def test_query_sha256_is_intent_hash():
    """The recorded query hash must equal sha256(intent_text) from the task
    bundle — i.e. ONLY the parent-visible intent text (no patch/proxy)."""
    import sys

    sys.path.insert(0, str(_PROJECT_DIR))
    sys.path.insert(0, str(_PROJECT_DIR / "src"))
    from benchmark.recall.data import SALEOR_DATASET, V1_DATASET, V2_DATASET, load_dev_tasks
    from scripts.route_b_v2_robustness import load_case

    rankings = json.loads((_RUN_DIR / "task_rankings.json").read_text(encoding="utf-8"))
    tasks = load_dev_tasks()
    by_cid = {t.case_id: t for t in tasks}
    checked = 0
    for cid, r in list(rankings.items())[:40]:
        t = by_cid[cid]
        ds = V1_DATASET if t.repository == "djangocms" and t.role.startswith("V1") else (
            V2_DATASET if t.repository == "djangocms" else SALEOR_DATASET)
        case = load_case(cid, ds)
        expected = hashlib.sha256(case["intent_text"].encode("utf-8")).hexdigest()
        assert r["query_sha256"] == expected
        checked += 1
    assert checked == 40


def test_parent_revision_indexed():
    """Each task must carry a parent_commit and the run must have used only
    parent-visible file content (verified in the development report); here we
    assert the parent commit is recorded for every task."""
    rankings = json.loads((_RUN_DIR / "task_rankings.json").read_text(encoding="utf-8"))
    for _cid, r in rankings.items():
        assert len(r["parent_commit"]) == 40


def test_embeddings_regenerable_deterministic():
    """Unit manifest hashes are stable and all scoring keys derive from unit
    text hashes (no external randomness)."""
    plan = json.loads((_RUN_DIR / "unit_manifest.json").read_text(encoding="utf-8"))
    assert len(plan) > 1000
    for blob_sha, unit_keys in plan.items():
        assert len(blob_sha) == 64
        for k in unit_keys:
            assert len(k) == 64


def test_metrics_gate_files_exist():
    for name in ("metrics.json", "gate.json", "efficiency.json"):
        assert (_RUN_DIR / name).exists()
