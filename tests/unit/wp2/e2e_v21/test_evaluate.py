"""Mission-12B v2.1 - evaluation planner/runner unit tests (T5): zero API.

Covers:
- same diff shared by arms evaluated once (per-task unique diff)
- same diff hash on different tasks NOT deduped across tasks
- variance APPLIED diffs included
- plan cannot change after the first result (plan_hash stable)
- no provider/network dependency (synthetic evidence only)
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts import wp2_e2e_smoke_v21_evaluate as ev


def _mk_episode(root: Path, task: str, arm: str, status: str,
                diff_sha: str, subdir: str = "episodes") -> None:
    d = root / subdir / task / arm
    d.mkdir(parents=True, exist_ok=True)
    rec = {"smoke_version": "wp2-e2e-smoke-eng-v21", "task_id": task, "arm": arm,
           "status": status, "diff_sha256": diff_sha}
    (d / "episode.json").write_text(json.dumps(rec), encoding="utf-8")
    if status == "APPLIED":
        (d / "final_diff.patch").write_text(f"diff for {task} {arm}", encoding="utf-8")


def _swap_root(monkeypatch, tmp_path: Path) -> None:
    old = ev.V21_ROOT
    ev.V21_ROOT = tmp_path
    monkeypatch.setattr(ev, "V21_ROOT", tmp_path)
    return old


def test_same_diff_shared_by_arms_evaluated_once(tmp_path: Path, monkeypatch) -> None:
    _swap_root(monkeypatch, tmp_path)
    sha = "a" * 64
    _mk_episode(tmp_path, "t1", "GOLD_HARD", "APPLIED", sha)
    _mk_episode(tmp_path, "t1", "AGENT_HARD", "APPLIED", sha)  # same diff, same task
    plan = ev.build_plan()
    assert plan["n_unique_diffs"] == 1
    assert plan["items"][0]["task_id"] == "t1"
    assert "also_sources" in plan["items"][0]


def test_same_diff_hash_different_tasks_not_deduped(tmp_path: Path, monkeypatch) -> None:
    _swap_root(monkeypatch, tmp_path)
    sha = "b" * 64
    _mk_episode(tmp_path, "t1", "GOLD_HARD", "APPLIED", sha)
    _mk_episode(tmp_path, "t2", "GOLD_HARD", "APPLIED", sha)  # same hash, different task
    plan = ev.build_plan()
    assert plan["n_unique_diffs"] == 2


def test_variance_applied_included(tmp_path: Path, monkeypatch) -> None:
    _swap_root(monkeypatch, tmp_path)
    sha1 = "c" * 64
    sha2 = "d" * 64
    _mk_episode(tmp_path, "t1", "GOLD_HARD", "APPLIED", sha1)
    _mk_episode(tmp_path, "t1", "GOLD_HARD", "APPLIED", sha2, subdir="variance")
    plan = ev.build_plan()
    assert plan["n_unique_diffs"] == 2
    kinds = sorted(it["kind"] for it in plan["items"])
    assert kinds == ["main", "variance"]


def test_plan_cannot_change_after_first_result(tmp_path: Path, monkeypatch) -> None:
    _swap_root(monkeypatch, tmp_path)
    sha = "e" * 64
    _mk_episode(tmp_path, "t1", "GOLD_HARD", "APPLIED", sha)
    plan1 = ev.persist_plan()
    plan2 = ev.build_plan()
    assert plan1["plan_sha256"] == plan2["plan_sha256"]
    # simulate a persisted plan + a result already present: rebuild must be identical
    result = tmp_path / "evaluations" / "unique" / f"unique_{sha[:8]}" / "evaluation.json"
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text(json.dumps({"task_id": "t1", "diff_sha256": sha, "status": "DONE"}),
                      encoding="utf-8")
    plan3 = ev.build_plan()
    assert plan3["plan_sha256"] == plan1["plan_sha256"]


def test_plan_persisted_before_first_evaluation(tmp_path: Path, monkeypatch) -> None:
    _swap_root(monkeypatch, tmp_path)
    sha = "f" * 64
    _mk_episode(tmp_path, "t1", "GOLD_HARD", "APPLIED", sha)
    assert not (tmp_path / "evaluations" / "plan.json").exists()
    ev.persist_plan()
    assert (tmp_path / "evaluations" / "plan.json").exists()
    plan = json.loads((tmp_path / "evaluations" / "plan.json").read_text(encoding="utf-8"))
    assert plan["plan_sha256"]


def test_no_provider_network_dependency(tmp_path: Path, monkeypatch) -> None:
    """The planner imports no generation/transport provider module."""
    import importlib
    mod = importlib.import_module("scripts.wp2_e2e_smoke_v21_evaluate")
    src = Path(mod.__file__).read_text(encoding="utf-8")
    assert "transport" not in src or "wp2_e2e_smoke_v21" not in src
    assert "V21HttpClient" not in src
    assert "generate_messages" not in src
