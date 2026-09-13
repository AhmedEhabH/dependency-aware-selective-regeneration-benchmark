"""Integration tests: RealCommitImpactDataset-v1 miner pipeline (M4A-1, ZERO API).

Builds a tiny temporary git repository covering all v1 eligibility/exclusion
shapes and proves the end-to-end pipeline:
``git history -> target/parent -> parent checkout -> candidate universe ->
graph -> hidden diff proxy -> manifest -> validator``.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest

from benchmark.real_commits import miner, validation
from benchmark.real_commits.models import SplitRole, compute_canonical_record_hash


def _commit(root: Path, message: str, files: dict[str, str]) -> str:
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(root), "add", "--", rel], check=True, capture_output=True
        )
    subprocess.run(
        ["git", "-C", str(root), "commit", "-q", "-m", message],
        check=True,
        capture_output=True,
    )
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


@pytest.fixture
def synthetic_repo() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="rc-it-repo-") as tmp:
        root = Path(tmp)
        subprocess.run(["git", "-C", str(root), "init", "-q", "-b", "main"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "it"], check=True)
        subprocess.run(
            ["git", "-C", str(root), "config", "user.email", "it@example.com"], check=True
        )

        _commit(
            root,
            "initial commit",
            {
                "cms/models/pagemodel.py": "class PageModel:\n    pass\n",
                "cms/models/pluginmodel.py": "class PluginModel:\n    pass\n",
                "menus/menu.py": "class Menu:\n    pass\n",
                "cms/tests/test_page.py": "def test_page():\n    assert True\n",
                "cms/migrations/0001_initial.py": "migration = 1\n",
                "setup.py": "setup()\n",
                "README.rst": "readme\n",
            },
        )
        _commit(
            root,
            "fix: add page publish validation",
            {
                "cms/models/pagemodel.py": (
                    "class PageModel:\n    def publish(self):\n        return True\n"
                )
            },
        )
        _commit(
            root,
            "test: cover publish",
            {
                "cms/tests/test_page.py": (
                    "def test_page():\n    assert True\n"
                    "\ndef test_publish():\n    assert True\n"
                )
            },
        )
        _commit(root, "chore: add migration", {"cms/migrations/0002.py": "migration = 2\n"})
        _commit(root, "style: whitespace only", {"menus/menu.py": "class Menu:\n     pass\n"})
        _commit(
            root,
            "feat: add new utility module",
            {"cms/utils/newutil.py": "def util():\n    return 1\n"},
        )
        subprocess.run(
            ["git", "-C", str(root), "mv", "cms/utils/newutil.py", "cms/utils/renamed.py"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(root), "commit", "-q", "-m", "refactor: rename utility module"],
            check=True,
            capture_output=True,
        )
        _commit(
            root,
            "fix: update cms/models/pagemodel.py to add title",
            {
                "cms/models/pagemodel.py": (
                    "class PageModel:\n    def publish(self):\n        return True\n"
                    "\n    def title(self):\n        return ''\n"
                )
            },
        )
        _commit(
            root,
            "fix: menu ordering",
            {
                "menus/menu.py": "class Menu:\n    def order(self):\n        return [1, 2]\n",
                "cms/models/pluginmodel.py": (
                    "class PluginModel:\n    def refresh(self):\n        return 0\n"
                ),
            },
        )
        side = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        subprocess.run(
            ["git", "-C", str(root), "checkout", "-q", "-b", "side-branch", side],
            check=True,
            capture_output=True,
        )
        _commit(
            root,
            "feat: side change",
            {"cms/models/sidemodel.py": "class SideModel:\n    pass\n"},
        )
        subprocess.run(["git", "-C", str(root), "checkout", "-q", "main"], check=True)
        subprocess.run(
            ["git", "-C", str(root), "merge", "-q", "--no-ff", "-m", "merge: side branch", "side-branch"],
            check=True,
            capture_output=True,
        )
        c9 = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        yield {
            "root": root,
            "commits": {
                "c0": None,
                "c1": None,
                "c2": None,
                "c3": None,
                "c4": None,
                "c5": None,
                "c6": None,
                "c7": None,
                "c8": None,
                "c9": c9,
            },
        }


def _target_shas(root: Path) -> dict[str, str]:
    """Map commit subject -> full sha for the synthetic repo."""
    shas: dict[str, str] = {}
    out = subprocess.run(
        ["git", "-C", str(root), "log", "--reverse", "--format=%H%x1f%s"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    for line in out.splitlines():
        sha, _, subject = line.partition("\x1f")
        shas[subject] = sha
    return shas


def test_end_to_end_pipeline_builds_case(synthetic_repo: dict[str, object]) -> None:
    root: Path = synthetic_repo["root"]
    shas = _target_shas(root)
    target = shas["fix: menu ordering"]
    parent = miner.commit_info(root, target).parents[0]

    name_status = miner.diff_name_status(root, parent, target)
    assert set(name_status) == {"cms/models/pluginmodel.py", "menus/menu.py"}

    info = miner.commit_info(root, target)
    intent = miner.normalize_intent(info.message)
    eligibility = miner.evaluate_eligibility(
        parents=info.parents,
        intent=intent,
        name_status=name_status,
        allow_intent_path_leakage=True,
    )
    assert eligibility["eligible"] is True
    assert eligibility["proxy_count"] == 2

    with tempfile.TemporaryDirectory(prefix="rc-it-case-") as tmp:
        out = Path(tmp)
        case_id = miner.make_case_id(target)
        miner.build_case(
            cache_dir=root,
            case_id=case_id,
            target=target,
            parent=parent,
            name_status=name_status,
            eligibility=eligibility,
            output_dir=out / "miner_dev",
            created_utc="2026-09-13T00:00:00+00:00",
        )
        manifest = validation.load_case_manifest(out, case_id)
        record = manifest["record"]
        assert record["parent_commit"] == parent
        assert record["target_commit"] == target
        assert record["split"] == SplitRole.MINER_DEV.value
        assert record["partition_role"] == "MINER_DEVELOPMENT"
        assert record["candidate_universe_count"] >= 1
        assert record["observed_change_set_proxy_count"] == 2
        assert compute_canonical_record_hash(record) == record["canonical_record_sha256"]

        case_dir = validation.case_dir(out, case_id)
        assert (case_dir / "public" / "intent.json").is_file()
        assert (case_dir / "public" / "candidate_universe.json").is_file()
        assert (case_dir / "public" / "dependency_graph.json").is_file()
        assert (case_dir / "hidden" / validation.HIDDEN_PROXY_FILENAME).is_file()


def test_proxy_subset_of_parent_universe(synthetic_repo: dict[str, object]) -> None:
    root: Path = synthetic_repo["root"]
    shas = _target_shas(root)
    target = shas["fix: menu ordering"]
    parent = miner.commit_info(root, target).parents[0]
    built = miner.build_parent_universe_and_graph(root, parent)
    universe_paths = {str(r["path"]) for r in built["records"]}
    proxy = {"cms/models/pluginmodel.py", "menus/menu.py"}
    assert proxy <= universe_paths
    assert built["universe_hash"]
    assert built["graph_hash"]
    assert built["graph_node_count"] >= 1
    assert built["graph_edge_count"] >= 0


def test_eligible_commit_produces_public_and_hidden(
    synthetic_repo: dict[str, object],
) -> None:
    root: Path = synthetic_repo["root"]
    shas = _target_shas(root)
    with tempfile.TemporaryDirectory(prefix="rc-it-bundle-") as tmp:
        out = Path(tmp)
        dataset = out / "dataset"
        target = shas["fix: menu ordering"]
        parent = miner.commit_info(root, target).parents[0]
        ns = miner.diff_name_status(root, parent, target)
        elig = miner.evaluate_eligibility(
            parents=(parent,),
            intent=miner.normalize_intent(miner.commit_info(root, target).message),
            name_status=ns,
            allow_intent_path_leakage=True,
        )
        case_id = miner.make_case_id(target)
        miner.build_case(
            cache_dir=root,
            case_id=case_id,
            target=target,
            parent=parent,
            name_status=ns,
            eligibility=elig,
            output_dir=dataset / "miner_dev",
            created_utc="2026-09-13T00:00:00+00:00",
        )
        proxy = validation.load_hidden_proxy(dataset, case_id)
        assert set(proxy["paths"]) == {"cms/models/pluginmodel.py", "menus/menu.py"}
        assert validation.check_public_bundle_leakage(dataset, case_id)["passed"]
