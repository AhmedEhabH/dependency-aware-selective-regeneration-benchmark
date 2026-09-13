"""Integration tests: RealCommitImpactDataset-v1 scientific pipeline (M4A-2, ZERO API).

Proves the end-to-end scientific corpus path on a temporary synthetic git
repository: batch scan -> eligibility -> dedup -> year-capped selection ->
split freeze -> case build (public/hidden separation) -> six scientific gates.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pytest

from benchmark.real_commits import miner, scientific
from benchmark.real_commits import validation_scientific as vs


def _commit(root: Path, message: str, files: dict[str, str]) -> str:
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "add", "--", rel], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(root), "commit", "-q", "-m", message], check=True, capture_output=True
    )
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


@pytest.fixture
def scientific_repo() -> dict[str, object]:
    """A small synthetic repo with enough eligible independent commits."""
    with tempfile.TemporaryDirectory(prefix="rc-sci-repo-") as tmp:
        root = Path(tmp)
        subprocess.run(["git", "-C", str(root), "init", "-q", "-b", "main"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "it"], check=True)
        subprocess.run(
            ["git", "-C", str(root), "config", "user.email", "it@example.com"], check=True
        )
        subprocess.run(
            ["git", "-C", str(root), "config", "commit.gpgsign", "false"], check=True
        )
        _commit(
            root,
            "initial commit",
            {
                "cms/models/pagemodel.py": "class PageModel:\n    pass\n",
                "cms/models/pluginmodel.py": "class PluginModel:\n    pass\n",
                "menus/menu.py": "class Menu:\n    pass\n",
                "cms/tests/test_page.py": "def test_page():\n    assert True\n",
            },
        )
        shas = {}
        page_model = "class PageModel:\n    def publish(self):\n        return True\n"
        menu_order = "class Menu:\n    def order(self):\n        return []\n"
        plugin_render = "class PluginModel:\n    def render(self):\n        return ''\n"
        page_slug = "class PageModel:\n    def slug(self):\n        return 'x'\n"
        menu_toolbar = "class Menu:\n    def toolbar(self):\n        return True\n"
        page_title = "class PageModel:\n    def title(self):\n        return 't'\n"
        for i, (msg, files) in enumerate(
            [
                ("fix: page publish (#1001)", {"cms/models/pagemodel.py": page_model}),
                ("feat: menu order (#1002)", {"menus/menu.py": menu_order}),
                ("fix: plugin render (#1003)", {"cms/models/pluginmodel.py": plugin_render}),
                ("fix: slug (#1004)", {"cms/models/pagemodel.py": page_slug}),
                ("feat: toolbar (#1005)", {"menus/menu.py": menu_toolbar}),
                ("fix: title (#1006)", {"cms/models/pagemodel.py": page_title}),
            ]
        ):
            shas[f"c{i + 1}"] = _commit(root, msg, files)
        # A merge commit (must be excluded as scientific candidate).
        side = shas["c6"]
        subprocess.run(
            ["git", "-C", str(root), "checkout", "-q", "-b", "side", side], check=True
        )
        _commit(root, "feat: side (#1007)", {"cms/models/sidemodel.py": "class SideModel:\n    pass\n"})
        subprocess.run(["git", "-C", str(root), "checkout", "-q", "main"], check=True)
        subprocess.run(
            ["git", "-C", str(root), "merge", "-q", "--no-ff", "-m", "merge: side (#1008)", "side"],
            check=True,
        )
        anchor = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        yield {"root": root, "anchor": anchor, "shas": shas}


def test_scientific_enumerate_filters_and_counts(scientific_repo: dict) -> None:
    root: Path = scientific_repo["root"]
    anchor: str = scientific_repo["anchor"]
    candidates, counts = scientific.enumerate_scientific_candidates(
        root, anchor, window=20, miner_dev_targets=frozenset()
    )
    # 6 eligible single-parent commits; merge excluded; initial commit has no
    # production change vs parent (it is the root) -> excluded as
    # no_meaningful_intent or no_production_source_change.
    assert len(candidates) >= 4
    assert counts.get("merge_commit", 0) >= 1
    for c in candidates:
        assert c["intent_mentions_changed_path"] is False
        assert len(c["proxy_paths"]) >= 1


def test_scientific_miner_dev_target_excluded(scientific_repo: dict) -> None:
    root: Path = scientific_repo["root"]
    anchor: str = scientific_repo["anchor"]
    target = scientific_repo["shas"]["c1"]
    candidates, counts = scientific.enumerate_scientific_candidates(
        root, anchor, window=20, miner_dev_targets=frozenset({target})
    )
    assert counts.get("miner_dev_target", 0) == 1
    assert all(c["sha"] != target for c in candidates)


def test_scientific_dedup_removes_related(scientific_repo: dict) -> None:
    # Two commits that share a PR ref must be deduplicated (keep newest).
    from benchmark.real_commits import scientific as sci

    a = sci.deduplicate_candidates(
        [
            {
                "sha": "a" * 40, "parent": "p" * 40, "subject": "fix: x (#9001)",
                "intent": "fix: x (#9001)", "status": {"cms/a.py": "M"},
                "time": "2024-01-01T00:00:00+00:00", "ts": 0, "year": "2024",
                "proxy_paths": ("cms/a.py",), "proxy_count": 1,
                "change_type": "unknown", "intent_mentions_changed_path": False,
                "prs": sci.extract_pr_refs("fix: x (#9001)"), "eligibility": {},
            },
            {
                "sha": "b" * 40, "parent": "p" * 40, "subject": "fix: y (#9001)",
                "intent": "fix: y (#9001)", "status": {"cms/b.py": "M"},
                "time": "2024-01-02T00:00:00+00:00", "ts": 1, "year": "2024",
                "proxy_paths": ("cms/b.py",), "proxy_count": 1,
                "change_type": "unknown", "intent_mentions_changed_path": False,
                "prs": sci.extract_pr_refs("fix: y (#9001)"), "eligibility": {},
            },
        ]
    )
    kept, adj = a
    assert [c["sha"] for c in kept] == ["a" * 40]
    assert any(r["rule"] == "R2_shared_pr_reference" for r in adj)


def test_freeze_splits_integration_with_manifest(scientific_repo: dict) -> None:
    """Split freeze membership must match the scientific manifest case ids."""
    root: Path = scientific_repo["root"]
    anchor: str = scientific_repo["anchor"]
    candidates, _ = scientific.enumerate_scientific_candidates(
        root, anchor, window=20, miner_dev_targets=frozenset()
    )
    kept, _ = scientific.deduplicate_candidates(candidates)
    selected = scientific.select_year_capped(kept, cap=5, target=40)
    assert 1 <= len(selected) <= 40
    sf = scientific.freeze_splits(selected, seed=20260913)
    all_members = [m for p in sf["per_split"].values() for m in p["case_ids"]]
    expected_ids = [miner.make_case_id(c["sha"]) for c in selected]
    assert sorted(all_members) == sorted(expected_ids)


def test_build_scientific_dataset_end_to_end(scientific_repo: dict, tmp_path: Path) -> None:
    root: Path = scientific_repo["root"]
    anchor: str = scientific_repo["anchor"]
    dataset_dir = tmp_path / "dataset"

    result = scientific.build_scientific_dataset(
        cache_dir=root,
        anchor=anchor,
        dataset_dir=dataset_dir,
        created_utc="2026-09-13T00:00:00+00:00",
        window=20,
        year_cap=5,
        target_cases=40,
        split_seed=20260913,
        miner_dev_targets=frozenset(),
    )
    assert result["selection_summary"]["selected"] >= 1
    assert (dataset_dir / "scientific_manifest.json").is_file()
    assert (dataset_dir / "split_freeze.json").is_file()

    manifest = json.loads((dataset_dir / "scientific_manifest.json").read_text(encoding="utf-8"))
    split_freeze = json.loads((dataset_dir / "split_freeze.json").read_text(encoding="utf-8"))
    assert len(manifest["cases"]) == len(manifest["case_ids"])

    for record in manifest["cases"]:
        cid = record["case_id"]
        case_path = dataset_dir / "scientific" / cid
        assert (case_path / "public" / "intent.json").is_file()
        assert (case_path / "public" / "candidate_universe.json").is_file()
        assert (case_path / "public" / "dependency_graph.json").is_file()
        assert (case_path / "hidden" / "observed_change_set_proxy.json").is_file()
        assert record["split"] in vs.SCIENTIFIC_SPLITS
        assert record["partition_role"] == "SCIENTIFIC"
        assert record["intent_mentions_changed_path"] is False
        assert split_freeze["assignment"][cid] == record["split"]


def test_six_scientific_gates_pass_on_synthetic(scientific_repo: dict, tmp_path: Path) -> None:
    """Synthetic repo: structural gates pass; count-based checks are the only
    exclusions (the tiny synthetic repo has fewer than 30 eligible commits).
    The full 30-40 corpus gate contract is validated against the REAL corpus
    (test_real_commit_scientific_leakage.py + the persisted gate report).
    """
    root: Path = scientific_repo["root"]
    anchor: str = scientific_repo["anchor"]
    dataset_dir = tmp_path / "dataset"
    scientific.build_scientific_dataset(
        cache_dir=root,
        anchor=anchor,
        dataset_dir=dataset_dir,
        created_utc="2026-09-13T00:00:00+00:00",
        window=20,
        year_cap=5,
        target_cases=40,
        split_seed=20260913,
        miner_dev_targets=frozenset(),
    )
    results = vs.run_six_scientific_gates(dataset_dir, root, anchor)
    for gate in results:
        if gate["gate"] == 1:
            # Only the count check may be non-ok on the tiny synthetic repo.
            bad = [c for c in gate["checks"] if not c["ok"]]
            assert all(b["check"] == "scientific_case_count_30_to_40" for b in bad)
            assert gate["checks"][2]["check"] == "anchor_sha_matches_scientific_manifest"
        elif gate["gate"] == 4:
            bad = [c for c in gate["checks"] if not c["ok"]]
            assert all(b["check"] == "thirty_to_forty_scientific_cases_materialized" for b in bad)
        else:
            assert gate["passed"], f"gate {gate['gate']} failed: {[c for c in gate['checks'] if not c['ok']]}"


def test_miner_dev_targets_loaded_from_manifest(tmp_path: Path) -> None:
    import sys

    # Simulate a miner_dev_manifest with one case and verify the loader.
    sys.path.insert(0, ".")
    from scripts.build_real_commit_dataset_scientific import load_miner_dev_targets

    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir(parents=True)
    (dataset_dir / "miner_dev_manifest.json").write_text(
        json.dumps({"cases": [{"target_commit": "ab" * 20}]}), encoding="utf-8"
    )
    assert load_miner_dev_targets(dataset_dir) == frozenset({"ab" * 20})
