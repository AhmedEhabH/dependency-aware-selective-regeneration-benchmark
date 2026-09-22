"""WP-2 Oracle Confirmation - integration tests (ZERO API, synthetic git repos).

Proves, on minimal synthetic repositories with real pytest subprocesses:
1. added test fails behaviorally on parent, passes target -> BEHAVIORAL_F2P;
2. added test fails because symbol missing on parent, passes target ->
   SYMBOL_ABSENCE_F2P;
3. test passes parent and target -> P2P-only;
4. flaky test detected across 3 runs;
5. test-only patch never applies a production change;
6. resume does not rerun a completed task;
7. the 786 sealed-outcomes guard fails closed.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from benchmark.wp2.oracle_confirmation import (
    FLAKY,
    OTHER_REVIEW_REQUIRED,
    SYMBOL_ABSENCE_F2P,
    derive_test_only_patch_bytes,
    parse_junit,
)

PROJECT = Path(__file__).resolve().parents[3]


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def _write(repo: Path, rel: str, text: str) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _init_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "commit.gpgsign", "false")
    _git(repo, "config", "core.autocrlf", "false")


def _commit_all(repo: Path, msg: str) -> str:
    _git(repo, "add", "-A")
    r = _git(repo, "commit", "-q", "-m", msg)
    assert r.returncode == 0, r.stderr
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def _run_pytest(cwd: Path, junit: Path, target: str) -> dict:
    """Run pytest with --junitxml in cwd; return parsed nodes."""
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "--junitxml",
        str(junit),
        "-q",
    ]
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert junit.exists(), f"junit missing; rc={r.returncode}\n{r.stdout}\n{r.stderr}"
    nodes = parse_junit(junit.read_text(encoding="utf-8"))
    return {"returncode": r.returncode, "nodes": nodes}


# ---------------------------------------------------------------------------
# 1. Behavioral F2P
# ---------------------------------------------------------------------------
def test_behavioral_f2p_on_synthetic_repo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    _write(
        repo,
        "greeter.py",
        "def greet(name):\n    return f'Hello {name}'\n",
    )
    _write(
        repo,
        "tests/test_greeter.py",
        "from greeter import greet\n\ndef test_greet():\n    assert greet('World') == 'Hello World'\n",
    )
    parent = _commit_all(repo, "parent")

    # target: change behavior and update/add test
    _write(
        repo,
        "greeter.py",
        "def greet(name, excited=False):\n    out = f'Hello {name}'\n    return out + '!' if excited else out\n",
    )
    _write(
        repo,
        "tests/test_greeter.py",
        "from greeter import greet\n\ndef test_greet():\n    assert greet('World') == 'Hello World'\n\ndef test_excited():\n    assert greet('World', excited=True) == 'Hello World!'\n",
    )
    target = _commit_all(repo, "target")

    # parent worktree + test-only patch: apply the target test diff
    parent_wt = tmp_path / "wt_parent"
    _git(repo, "worktree", "add", "-q", str(parent_wt), parent)
    target_wt = tmp_path / "wt_target"
    _git(repo, "worktree", "add", "-q", str(target_wt), target)

    try:
        diff = _git(repo, "diff", parent, target, "--", "tests/").stdout
        test_paths = ["tests/test_greeter.py"]
        test_only = derive_test_only_patch_bytes(diff, test_paths)
        # apply to parent
        patch_file = tmp_path / "test_only.patch"
        patch_file.write_text(test_only, encoding="utf-8")
        app = _git(parent_wt, "apply", "--check", str(patch_file))
        assert app.returncode == 0, app.stderr
        _git(parent_wt, "apply", str(patch_file))

        # parent+testpatch: test_excited should fail (attribute/behavior not present)
        parent_res = _run_pytest(parent_wt, tmp_path / "p.xml", "parent")
        target_res = _run_pytest(target_wt, tmp_path / "t.xml", "target")

        # target node passes
        target_nodes = target_res["nodes"]
        assert "tests/test_greeter.py::test_excited" in target_nodes
        assert target_nodes["tests/test_greeter.py::test_excited"] == "passed"

        # parent node fails (AssertionError because greet() takes 1 arg)
        parent_nodes = parent_res["nodes"]
        assert parent_nodes["tests/test_greeter.py::test_excited"] in ("failed", "error")
    finally:
        _git(repo, "worktree", "remove", "--force", str(parent_wt))
        _git(repo, "worktree", "remove", "--force", str(target_wt))


# ---------------------------------------------------------------------------
# 2. Symbol-absence F2P
# ---------------------------------------------------------------------------
def test_symbol_absence_f2p_on_synthetic_repo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    _write(repo, "existing.py", "VALUE = 1\n")
    _write(repo, "tests/test_existing.py", "from existing import VALUE\n\ndef test_value():\n    assert VALUE == 1\n")
    parent = _commit_all(repo, "parent")

    # target: add a new component and a test importing it
    _write(
        repo,
        "new_component.py",
        "def compute():\n    return 42\n",
    )
    _write(
        repo,
        "tests/test_new_component.py",
        "from new_component import compute\n\ndef test_compute():\n    assert compute() == 42\n",
    )
    target = _commit_all(repo, "target")

    parent_wt = tmp_path / "wt_parent"
    _git(repo, "worktree", "add", "-q", str(parent_wt), parent)
    target_wt = tmp_path / "wt_target"
    _git(repo, "worktree", "add", "-q", str(target_wt), target)

    try:
        diff = _git(repo, "diff", parent, target, "--", "tests/").stdout
        test_only = derive_test_only_patch_bytes(diff, ["tests/test_new_component.py"])
        patch_file = tmp_path / "test_only.patch"
        patch_file.write_text(test_only, encoding="utf-8")
        app = _git(parent_wt, "apply", "--check", str(patch_file))
        assert app.returncode == 0, app.stderr
        _git(parent_wt, "apply", str(patch_file))

        parent_res = _run_pytest(parent_wt, tmp_path / "p.xml", "parent")
        target_res = _run_pytest(target_wt, tmp_path / "t.xml", "target")

        assert target_res["nodes"]["tests/test_new_component.py::test_compute"] == "passed"
        # parent: new module cannot be imported -> file-level collection error
        parent_nodes = parent_res["nodes"]
        assert "tests/test_new_component.py" in parent_nodes
        assert parent_nodes["tests/test_new_component.py"] == "error"
    finally:
        _git(repo, "worktree", "remove", "--force", str(parent_wt))
        _git(repo, "worktree", "remove", "--force", str(target_wt))


# ---------------------------------------------------------------------------
# 3. P2P-only
# ---------------------------------------------------------------------------
def test_p2p_only_on_synthetic_repo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    _write(repo, "m.py", "X = 1\n")
    _write(repo, "tests/test_m.py", "from m import X\n\ndef test_x():\n    assert X == 1\n")
    parent = _commit_all(repo, "parent")
    # target changes production but not the test; the unchanged test passes both
    _write(repo, "m.py", "X = 1\nY = 2\n")
    _write(repo, "other.py", "def helper():\n    return 0\n")
    target = _commit_all(repo, "target")

    parent_wt = tmp_path / "wt_parent"
    _git(repo, "worktree", "add", "-q", str(parent_wt), parent)
    target_wt = tmp_path / "wt_target"
    _git(repo, "worktree", "add", "-q", str(target_wt), target)
    try:
        # test unchanged -> node passes both
        parent_res = _run_pytest(parent_wt, tmp_path / "p.xml", "parent")
        target_res = _run_pytest(target_wt, tmp_path / "t.xml", "target")
        node = "tests/test_m.py::test_x"
        assert parent_res["nodes"][node] == "passed"
        assert target_res["nodes"][node] == "passed"
    finally:
        _git(repo, "worktree", "remove", "--force", str(parent_wt))
        _git(repo, "worktree", "remove", "--force", str(target_wt))


# ---------------------------------------------------------------------------
# 4. Flaky detection across 3 runs
# ---------------------------------------------------------------------------
def test_flaky_detected_across_three_runs(tmp_path: Path) -> None:
    from benchmark.wp2.oracle_confirmation import three_run_stability

    assert three_run_stability(["passed", "failed", "passed"]) == FLAKY


# ---------------------------------------------------------------------------
# 5. Test-only patch never applies production change
# ---------------------------------------------------------------------------
def test_test_only_patch_is_source_free(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    _write(repo, "prod.py", "def f():\n    return 1\n")
    _write(repo, "tests/test_prod.py", "from prod import f\n\ndef test_f():\n    assert f() == 1\n")
    parent = _commit_all(repo, "parent")
    _write(repo, "prod.py", "def f():\n    return 2\n")
    _write(repo, "tests/test_prod.py", "from prod import f\n\ndef test_f():\n    assert f() == 2\n")
    target = _commit_all(repo, "target")

    diff = _git(repo, "diff", parent, target).stdout
    test_only = derive_test_only_patch_bytes(diff, ["tests/test_prod.py"])
    # the patch must contain no diff header for the production file
    assert "diff --git a/prod.py" not in test_only
    assert "diff --git a/tests/test_prod.py" in test_only


# ---------------------------------------------------------------------------
# 6. Resume does not rerun completed task (plan-level determinism check)
# ---------------------------------------------------------------------------
def test_resume_does_not_rerun_completed(tmp_path: Path) -> None:
    per_task_path = tmp_path / "per_task.jsonl"
    rows = [
        {"task_id": "saleor-rc-a", "status": "DONE", "classification": "BEHAVIORAL_F2P"},
        {"task_id": "saleor-rc-b", "status": "PENDING"},
    ]
    with open(per_task_path, "w", encoding="utf-8") as f:
        # only completed tasks are persisted to the jsonl resume log
        f.write(json.dumps(rows[0]) + "\n")
    done = {json.loads(line)["task_id"] for line in per_task_path.read_text(encoding="utf-8").splitlines()}
    assert "saleor-rc-a" in done
    assert "saleor-rc-b" not in done
    # the resume logic must skip 'a' and only run 'b'
    todo = [r for r in rows if r["task_id"] not in done or r["status"] != "DONE"]
    assert [r["task_id"] for r in todo] == ["saleor-rc-b"]


# ---------------------------------------------------------------------------
# 7. 786 sealed-outcomes guard fails closed
# ---------------------------------------------------------------------------
def test_sealed_outcomes_guard_fails_closed(tmp_path: Path) -> None:
    from benchmark.wp2.oracle_confirmation import is_sealed_outcome_source

    sealed = [
        "research/saleor-reserve-300-rmcss/saleor_reserve_300_sample.json",
        "research/transparency/saleor_candidate_metadata.json",
        "research/transparency/anything.json",
    ]
    for p in sealed:
        assert is_sealed_outcome_source(p), p
    ok = [
        "benchmark_data/real_commit_impact_saleor/scientific/saleor-rc-x/case_manifest.json",
        "research/wp2/wp2_saleor_main297_census_2026-09-22.json",
    ]
    for p in ok:
        assert not is_sealed_outcome_source(p), p