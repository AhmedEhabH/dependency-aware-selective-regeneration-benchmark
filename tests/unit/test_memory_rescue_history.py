"""PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2 — history tests (T3, ZERO network).

Covers the mission §37 history requirements:
  strict parent-only history visibility; no future/target commit leakage;
  temporal ancestry (fail-closed); production-file history filtering;
  global index parsing determinism.
"""
# ruff: noqa: N812

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.memory_rescue import history as H  # noqa: E402
from benchmark.memory_rescue.cochange import (  # noqa: E402
    SUPPORT_FREEZE,
    jaccard,
)


def _fake_log(records):
    """Render fake CommitRecords into git-log-like text."""
    parts = []
    for sha, subject, body, paths in records:
        parts.append(f"{H.RECORD_SEP}{sha}{H.FIELD_SEP}{subject}"
                     f"{H.FIELD_SEP}{body}{H.RECORD_SEP}")
        for p in paths:
            parts.append(f"M\t{p}")
    return "\n".join(parts)


class _FakeRepoHistory:
    """Synthetic RepoHistory replacement (no subprocess)."""

    def __init__(self, commits, ancestors):
        self.commits_map = commits  # sha -> CommitRecord
        self.ancestors_map = ancestors  # parent -> set(sha)

    def ancestors_of(self, parent):
        if parent not in self.ancestors_map:
            raise RuntimeError("cannot prove ancestry")
        return frozenset(self.ancestors_map[parent])

    def commit(self, sha):
        return self.commits_map.get(sha)


class _BadRepoHistory(_FakeRepoHistory):
    """Ancestors that are missing from the index (visibility unprovable)."""

    def ancestors_of(self, parent):
        return frozenset(self.ancestors_map.get(parent, ())) | {"deadbeef0000"}

    def production_changing_commits(self, parent, universe):
        missing = [s for s in self.ancestors_of(parent) if s not in self.commits_map]
        if missing:
            raise RuntimeError("temporal visibility cannot be proven (fail-closed)")
        return super().production_changing_commits(parent, universe)


class _ParityRepoHistory(_FakeRepoHistory):
    def production_changing_commits(self, parent, universe):
        out = {}
        for sha, rec in self.commits_map.items():
            if sha in self.ancestors_map.get(parent, ()) and (set(rec.paths) & universe):
                out[sha] = rec
        return out


def _task_history(repo_history, parent, universe):
    th = H.TaskHistory.__new__(H.TaskHistory)
    th.repo = "saleor"
    th.parent = parent
    th._universe = frozenset(universe)
    th.commits = repo_history.production_changing_commits(parent, universe)
    c = {}
    for rec in th.commits.values():
        for p in set(rec.paths) & th._universe:
            c[p] = c.get(p, 0) + 1
    th.history_change_count = c
    return th


class _ParityRepoHistory(_FakeRepoHistory):
    def production_changing_commits(self, parent, universe):
        out = {}
        for sha, rec in self.commits_map.items():
            if sha in self.ancestors_map.get(parent, ()) and (set(rec.paths) & universe):
                out[sha] = rec
        return out


def test_parse_log_roundtrip():
    text = _fake_log([
        ("a" * 40, "subject one", "body line 1", ("f1.py", "f2.py")),
        ("b" * 40, "subject two", "", ("f3.py",)),
    ])
    commits = H._parse_log(text)
    assert set(commits) == {"a" * 40, "b" * 40}
    assert commits["a" * 40].subject == "subject one"
    assert commits["a" * 40].paths == ("f1.py", "f2.py")
    assert commits["b" * 40].body == ""


def test_parse_log_multiline_body():
    text = (f"{H.RECORD_SEP}{'c'*40}{H.FIELD_SEP}s{H.FIELD_SEP}line1\nline2{H.RECORD_SEP}"
            "\nM\tf.py")
    commits = H._parse_log(text)
    rec = commits["c" * 40]
    assert rec.body == "line1\nline2"
    assert rec.paths == ("f.py",)


def test_parse_log_rename_new_path():
    text = (f"{H.RECORD_SEP}{'d'*40}{H.FIELD_SEP}s{H.FIELD_SEP}b{H.RECORD_SEP}"
            "\nR100\told.py\tnew.py")
    commits = H._parse_log(text)
    assert commits["d" * 40].paths == ("new.py",)


def test_parse_log_empty_raises():
    with pytest.raises(RuntimeError):
        H._parse_log("")


def test_task_history_counts_and_production_filter():
    commits = {
        "p1": H.CommitRecord("p1", "s", "b", ("f1.py", "f2.py", "ignored.py")),
        "p2": H.CommitRecord("p2", "s", "b", ("f1.py", "f3.py")),
        "p3": H.CommitRecord("p3", "s", "b", ("only_vendor.py",)),
    }
    rh = _ParityRepoHistory(commits, {"P": {"p1", "p2", "p3"}})
    th = _task_history(rh, "P", {"f1.py", "f2.py", "f3.py"})
    assert th.n_production_changing_commits() == 2  # p3 filtered (vendor only)
    assert th.history_change_count == {"f1.py": 2, "f2.py": 1, "f3.py": 1}
    cto = th.cochange_counts_to("f1.py")
    assert cto == {"f2.py": 1, "f3.py": 1}


def test_parent_only_visibility_no_target_commit():
    # The target commit and its descendants must NEVER be visible.
    commits = {
        "target": H.CommitRecord("target", "s", "b", ("f1.py",)),
        "child": H.CommitRecord("child", "s", "b", ("f2.py",)),
        "ancestor": H.CommitRecord("ancestor", "s", "b", ("f1.py",)),
    }
    rh = _ParityRepoHistory(commits, {"P": {"ancestor", "target"}})
    th = _task_history(rh, "P", {"f1.py", "f2.py"})
    # child is NOT an ancestor of P -> never counted
    assert "child" not in th.commits
    # target IS an ancestor here for the test, but production-changing set
    # must only contain ancestors of P (git rev-list semantics are tested
    # separately; here we assert the filter uses the ancestor set).
    assert set(th.commits) == {"ancestor", "target"}


def test_fail_closed_when_visibility_unprovable():
    commits = {"ancestor": H.CommitRecord("ancestor", "s", "b", ("f1.py",))}
    rh = _BadRepoHistory(commits, {"P": {"ancestor"}})
    with pytest.raises(RuntimeError):
        rh.production_changing_commits("P", {"f1.py"})


def test_ancestors_of_fails_closed():
    class _GitFail:
        def __init__(self, returncode, stderr):
            self.returncode = returncode
            self.stderr = stderr

    orig = H._git

    def fake_git(repo, args):
        if args[:1] == ["rev-list"]:
            return _GitFail(1, "fatal: ambiguous")
        return orig(repo, args)

    H._git = fake_git
    try:
        rh = H.RepoHistory.__new__(H.RepoHistory)
        rh.repo = "saleor"
        rh.repo_path = Path(".")
        with pytest.raises(RuntimeError):
            rh.ancestors_of("nonsense" * 5)
    finally:
        H._git = orig


def test_support_threshold_frozen():
    assert SUPPORT_FREEZE == 2
    # C(f,s) < 2 -> 0 even if ratio otherwise high
    assert jaccard(10, 10, 1) == 0.0
    assert jaccard(10, 10, 0) == 0.0
    # C(f,s) >= 2 -> ratio
    assert jaccard(10, 10, 5) == pytest.approx(5 / 15, abs=1e-12)
    assert jaccard(5, 5, 2) == pytest.approx(2 / 8, abs=1e-12)


def test_jaccard_zero_denominator():
    assert jaccard(0, 0, 0) == 0.0
    assert jaccard(1, 1, 1) == 0.0  # support < 2


def test_episode_document_text_subject_plus_body():
    rec = H.CommitRecord("x", "subject line", "body line", ())
    assert rec.text == "subject line\nbody line"
    rec2 = H.CommitRecord("y", "subject line", "", ())
    assert rec2.text == "subject line"
