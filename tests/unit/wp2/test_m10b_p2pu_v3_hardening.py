"""Mission-11 A2 hardening of the P2P-U V3 executor - unit tests (ZERO API, no Docker).

Covers H1-H8 (A2.1-A2.8) with fakes:
- H1 raw JUnit persistence + SHA-256 per file
- H2 install/tooling failure -> ENV_FAIL_P2PU (never classified)
- H3 parse errors -> INTEGRITY_FAIL (never swallowed)
- H4 monotonic wall clock + clock post-check
- H5 verified resume (verify_unit)
- H6 collection-session abort flag (D18)
- H7 chunk control (--max-units plan)
- H8 manifest completeness
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

import scripts.wp2_m10b_p2pu_v3_eng as mod
from scripts.wp2_m10b_p2pu_v3_eng import (
    HARNESS_SPEC_SHA256,
    PYTEST_FLAGS,
    RUNNER_SHA256,
    _is_collection_abort,
    _sha256,
    execute_cap,
    main,
    run_p2pu_state,
    verify_unit,
)

TASK = "saleor-rc-abcd12345678"
TID = "abcd12345678"
WT_T = f"/opt/wp2_v2/worktrees/{TID}_v3_t"
WT_P = f"/opt/wp2_v2/worktrees/{TID}_v3_p"


def _node_ids(n: int = 4, prefix: str = "saleor/a/tests/test_a.py::t") -> list[str]:
    return [f"{prefix}{i}" for i in range(n)]


def _junit_xml(node_ids: list[str], statuses: list[str] | None = None) -> str:
    rows: list[str] = []
    for i, n in enumerate(node_ids):
        path, _, name = n.rpartition("::")
        if statuses is None:
            inner = "<system-out/>"
        elif statuses[i] == "failed":
            inner = "<failure message='boom'>" + "x" * 20 + "</failure>"
        elif statuses[i] == "error":
            inner = "<error message='err'>" + "y" * 20 + "</error>"
        elif statuses[i] == "skipped":
            inner = "<skipped message='skip'/>"
        else:
            inner = "<system-out/>"
        rows.append(
            f'<testcase classname="c" name="{name}" file="{path}" time="0.1">{inner}</testcase>'
        )
    return f'<testsuite name="pytest" tests="{len(rows)}">' + "".join(rows) + "</testsuite>"


def _collection_error_xml(node_ids: list[str]) -> str:
    """One real testcase + one collection-error testcase."""
    real = "".join(
        f'<testcase classname="c" name="{n.split("::")[1]}" '
        f'file="{n.split("::")[0]}" time="0.1"><system-out/></testcase>'
        for n in node_ids
    )
    return (
        '<testsuite name="pytest" tests="2">'
        + real
        + '<testcase classname="" name="saleor.graphql.checkout.tests.test_checkout" time="0.00">'
        + '<error message="collection failed">cannot collect ...</error></testcase></testsuite>'
    )


def _ok_proc(stdout: str = "ALL_RUNS_DONE", rc: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["wsl"], rc, stdout=stdout)


def _make_wsl(files: dict[str, str | None], missing: set[str] | None = None) -> object:
    missing = missing or set()

    def fake_wsl(script: str, timeout_s: int = 3600) -> subprocess.CompletedProcess[str]:
        m = re.search(r"cat (/\S+?/\S+\.xml)", script)
        if m:
            name = m.group(1).rsplit("/", 1)[-1]
            if name in missing:
                return _ok_proc("__NO_FILE__\n")
            xml = files.get(name)
            if xml is None:
                return _ok_proc("__NO_FILE__\n")
            return _ok_proc(xml)
        return _ok_proc("")

    return fake_wsl


def _fake_sp_run(*args, **kwargs) -> subprocess.CompletedProcess[str]:
    return _ok_proc("")


def _patch_basics(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(mod, "OUT_ROOT", tmp_path)
    monkeypatch.setattr(mod, "ensure_postgres_running", lambda: None)
    monkeypatch.setattr(mod, "ensure_fresh_db", lambda n: {"db": n, "created": True})
    monkeypatch.setattr(mod, "drop_db", lambda n: None)
    monkeypatch.setattr(subprocess, "run", _fake_sp_run)


def _ok_run_state(**kwargs) -> dict:
    node_ids = kwargs.get("node_ids", [])
    state = kwargs.get("state", "t")
    return {
        "ok": True,
        "outcomes": {n: ["passed"] * 3 for n in node_ids},
        "failures": {},
        "junit_files": {f"{state}_r0.xml": "abcdef" * 8},
        "collection_session_abort": [],
        "db_name": f"saleor_v3_{TID}_{state}",
        "stdout_tail": "ALL_RUNS_DONE",
        "wall_s": 0.01,
    }


def _patch_exec_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
                    run_state=None) -> None:
    _patch_basics(monkeypatch, tmp_path)
    monkeypatch.setattr(mod, "task_commits", lambda t: ("p", "t"))
    monkeypatch.setattr(mod, "inventory_row",
                        lambda t: {"task_id": t, "era_key": "py39"})
    monkeypatch.setattr(mod, "clock_preflight",
                        lambda *a, **k: {"verdict": "PASS",
                                         "pre": {"median_skew_s": 0.1, "verdict": "PASS"},
                                         "post": None})
    monkeypatch.setattr(mod, "target_manifests", lambda t: {})
    monkeypatch.setattr(mod, "ensure_worktrees_v3",
                        lambda t, p, target: {"t": WT_T, "p": WT_P,
                                              "patch_applied_on_parent": False})
    monkeypatch.setattr(mod, "lock_install_script",
                        lambda wt, m: ("echo INSTALL_OK", "LOCK_EXACT_MAIN_PLUS_DEV", {}))
    monkeypatch.setattr(mod, "locked_dev_install", lambda t: "echo NO_LOCKED_DEV_GROUP")
    monkeypatch.setattr(mod, "base_image_id", lambda era: "img123")
    monkeypatch.setattr(mod, "lockfile_sha256", lambda m: "lock-sha")
    monkeypatch.setattr(mod, "remove_worktrees_v3", lambda t: None)
    if run_state is not None:
        monkeypatch.setattr(mod, "run_p2pu_state", run_state)
    else:
        monkeypatch.setattr(mod, "run_p2pu_state", _ok_run_state)


# ---------------------------------------------------------------------------
# H1 - persist raw JUnit + hash
# ---------------------------------------------------------------------------
def test_h1_persist_raw_junit_and_hash(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    node_ids = _node_ids()
    xml = _junit_xml(node_ids, statuses=["passed", "failed", "passed", "passed"])
    files = {f"{TID}_t_c200_r{rep}.xml": xml for rep in range(3)}
    _patch_basics(monkeypatch, tmp_path)
    monkeypatch.setattr(mod, "wsl_docker", lambda args, timeout_s=3600: _ok_proc())
    monkeypatch.setattr(mod, "wsl", _make_wsl(files))

    res = run_p2pu_state(task_id=TASK, era_key="py39", worktree_linux=WT_T, tid=TID,
                         state="t", cap=200, node_ids=node_ids,
                         install_fragment="echo INSTALL_OK",
                         locked_dev_fragment="echo NO", timeout_s=100)

    assert res["ok"] is True
    junit_dir = tmp_path / "p2pu_v3_junit" / TASK / "cap200"
    for rep in range(3):
        jpath = junit_dir / f"t_r{rep}.xml"
        assert jpath.exists()
        name = f"t_r{rep}.xml"
        assert jpath.read_text(encoding="utf-8") == xml
        assert res["junit_files"][name] == _sha256_bytes_of(xml)
    assert res["outcomes"]["saleor/a/tests/test_a.py::t0"] == ["passed", "passed", "passed"]
    assert res["outcomes"]["saleor/a/tests/test_a.py::t1"] == ["failed", "failed", "failed"]


def _sha256_bytes_of(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_h1_missing_xml_recorded_as_missing(monkeypatch: pytest.MonkeyPatch,
                                            tmp_path: Path) -> None:
    node_ids = _node_ids()
    xml = _junit_xml(node_ids)
    files = {f"{TID}_t_c200_r{rep}.xml": xml for rep in range(3)}
    _patch_basics(monkeypatch, tmp_path)
    monkeypatch.setattr(mod, "wsl_docker", lambda args, timeout_s=3600: _ok_proc())
    monkeypatch.setattr(mod, "wsl", _make_wsl(files, missing={f"{TID}_t_c200_r0.xml"}))

    res = run_p2pu_state(task_id=TASK, era_key="py39", worktree_linux=WT_T, tid=TID,
                         state="t", cap=200, node_ids=node_ids,
                         install_fragment="echo INSTALL_OK",
                         locked_dev_fragment="echo NO", timeout_s=100)
    assert res["ok"] is True
    assert res["junit_files"]["t_r0.xml"] == "MISSING"
    assert res["outcomes"][node_ids[0]] == ["missing", "passed", "passed"]


# ---------------------------------------------------------------------------
# H2 - install/tooling failure -> ENV_FAIL_P2PU
# ---------------------------------------------------------------------------
def test_h2_install_dev_fail_not_classified(monkeypatch: pytest.MonkeyPatch,
                                            tmp_path: Path) -> None:
    node_ids = _node_ids()
    xml = _junit_xml(node_ids)
    files = {f"{TID}_t_c200_r{rep}.xml": xml for rep in range(3)}
    _patch_basics(monkeypatch, tmp_path)
    monkeypatch.setattr(mod, "wsl_docker",
                        lambda args, timeout_s=3600: _ok_proc(
                            "INSTALL_DEV_FAIL\nuv error: no matching distribution"))
    monkeypatch.setattr(mod, "wsl", _make_wsl(files))

    res = run_p2pu_state(task_id=TASK, era_key="py39", worktree_linux=WT_T, tid=TID,
                         state="t", cap=200, node_ids=node_ids,
                         install_fragment="echo INSTALL_OK",
                         locked_dev_fragment="echo NO", timeout_s=100)
    assert res["ok"] is False
    assert res["error"] == "ENV_FAIL_P2PU"
    assert "no matching" in res["stdout_tail"]


def test_h2_all_xml_missing_is_env_fail(monkeypatch: pytest.MonkeyPatch,
                                        tmp_path: Path) -> None:
    node_ids = _node_ids()
    _patch_basics(monkeypatch, tmp_path)
    monkeypatch.setattr(mod, "wsl_docker",
                        lambda args, timeout_s=3600: _ok_proc("ALL_RUNS_DONE"))
    monkeypatch.setattr(mod, "wsl", _make_wsl({}, missing={f"{TID}_t_c200_r{i}.xml" for i in range(3)}))

    res = run_p2pu_state(task_id=TASK, era_key="py39", worktree_linux=WT_T, tid=TID,
                         state="t", cap=200, node_ids=node_ids,
                         install_fragment="echo INSTALL_OK",
                         locked_dev_fragment="echo NO", timeout_s=100)
    assert res["ok"] is False
    assert res["error"] == "ENV_FAIL_P2PU"
    assert res["reason"] == "MISSING_XML"


def test_h2_timeout_is_env_fail(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    node_ids = _node_ids()
    _patch_basics(monkeypatch, tmp_path)

    def raise_timeout(args, timeout_s=3600):
        raise subprocess.TimeoutExpired("wsl docker run", timeout_s)

    monkeypatch.setattr(mod, "wsl_docker", raise_timeout)
    res = run_p2pu_state(task_id=TASK, era_key="py39", worktree_linux=WT_T, tid=TID,
                         state="t", cap=200, node_ids=node_ids,
                         install_fragment="echo INSTALL_OK",
                         locked_dev_fragment="echo NO", timeout_s=100)
    assert res["ok"] is False
    assert res["error"] == "ENV_FAIL_P2PU"
    assert res["reason"] == "TIMEOUT"


# ---------------------------------------------------------------------------
# H3 - parse errors never swallowed -> INTEGRITY_FAIL
# ---------------------------------------------------------------------------
def test_h3_malformed_xml_is_integrity_fail(monkeypatch: pytest.MonkeyPatch,
                                            tmp_path: Path) -> None:
    node_ids = _node_ids()
    files = {f"{TID}_t_c200_r{rep}.xml": "<not-valid-xml" for rep in range(3)}
    _patch_basics(monkeypatch, tmp_path)
    monkeypatch.setattr(mod, "wsl_docker", lambda args, timeout_s=3600: _ok_proc())
    monkeypatch.setattr(mod, "wsl", _make_wsl(files))

    res = run_p2pu_state(task_id=TASK, era_key="py39", worktree_linux=WT_T, tid=TID,
                         state="t", cap=200, node_ids=node_ids,
                         install_fragment="echo INSTALL_OK",
                         locked_dev_fragment="echo NO", timeout_s=100)
    assert res["ok"] is False
    assert res["error"] == "INTEGRITY_FAIL"
    assert res["parse_error"]


# ---------------------------------------------------------------------------
# H4 - wall time + clock post-check
# ---------------------------------------------------------------------------
def test_h4_wall_clock_post(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    node_ids = _node_ids(2)
    _patch_exec_env(monkeypatch, tmp_path)
    res = execute_cap(TASK, 200, node_ids, {"rediscovery_sha256": "d1"})

    assert res["status"] == "DONE"
    assert res["wall_s"] < 10
    cc = res["manifest"]["clock_pre_post"]
    assert cc["pre"]["median_skew_s"] == 0.1
    assert cc["post"]["median_skew_s"] == 0.1
    assert cc["post"] is not None


# ---------------------------------------------------------------------------
# H5 - verified resume
# ---------------------------------------------------------------------------
def _write_synthetic_done(tmp_path: Path, tamper: bool = False,
                          drop_junit: bool = False) -> None:
    node_ids = _node_ids(1)
    xml = _junit_xml(node_ids)
    junit_dir = tmp_path / "p2pu_v3_junit" / TASK / "cap200"
    junit_dir.mkdir(parents=True, exist_ok=True)
    junit_files: dict[str, str] = {}
    for rep in range(3):
        jp = junit_dir / f"t_r{rep}.xml"
        jp.write_text(xml, encoding="utf-8")
        junit_files[f"t_r{rep}.xml"] = _sha256_bytes_of(xml)
    if drop_junit:
        (junit_dir / "t_r1.xml").unlink()
    result = {
        "task_id": TASK, "cap": 200, "status": "DONE", "era_key": "py39",
        "n_selected": 1, "node_classes": {node_ids[0]: "STABLE_P2P"},
        "junit_files": junit_files, "class_counts": {"STABLE_P2P": 1},
    }
    result["evidence_sha256"] = _sha256(
        {k: v for k, v in result.items() if k != "evidence_sha256"})
    if tamper:
        result["n_selected"] = 5
    (tmp_path / f"p2pu_v3_eng_{TASK}_cap200.json").write_text(
        json.dumps(result), encoding="utf-8")


def test_h5_valid_unit_verifies(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_basics(monkeypatch, tmp_path)
    _write_synthetic_done(tmp_path)
    ok, reason = verify_unit(TASK, 200)
    assert ok is True
    assert reason == "OK"


def test_h5_tampered_json_reruns(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_basics(monkeypatch, tmp_path)
    _write_synthetic_done(tmp_path, tamper=True)
    ok, reason = verify_unit(TASK, 200)
    assert ok is False
    assert reason == "EVIDENCE_HASH_MISMATCH"


def test_h5_missing_xml_reruns(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_basics(monkeypatch, tmp_path)
    _write_synthetic_done(tmp_path, drop_junit=True)
    ok, reason = verify_unit(TASK, 200)
    assert ok is False
    assert "JUNIT_NOT_ON_DISK" in reason


def test_h5_missing_result_reruns(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_basics(monkeypatch, tmp_path)
    ok, reason = verify_unit(TASK, 200)
    assert ok is False
    assert reason == "MISSING_RESULT"


# ---------------------------------------------------------------------------
# H6 - collection-session abort flag
# ---------------------------------------------------------------------------
def test_h6_collection_abort_flag(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    node_ids = _node_ids(10)
    present = node_ids[:4]
    normal = _junit_xml(node_ids, statuses=["passed"] * 10)
    abort_xml = _collection_error_xml(present)
    files = {f"{TID}_t_c200_r0.xml": abort_xml,
             f"{TID}_t_c200_r1.xml": normal,
             f"{TID}_t_c200_r2.xml": normal}
    _patch_basics(monkeypatch, tmp_path)
    monkeypatch.setattr(mod, "wsl_docker", lambda args, timeout_s=3600: _ok_proc())
    monkeypatch.setattr(mod, "wsl", _make_wsl(files))

    res = run_p2pu_state(task_id=TASK, era_key="py39", worktree_linux=WT_T, tid=TID,
                         state="t", cap=200, node_ids=node_ids,
                         install_fragment="echo INSTALL_OK",
                         locked_dev_fragment="echo NO", timeout_s=100)
    assert res["ok"] is True
    assert res["collection_session_abort"] == [0]
    assert 1 not in res["collection_session_abort"]


def test_h6_is_collection_abort_detector() -> None:
    assert _is_collection_abort(_collection_error_xml(["saleor/a/tests/test_a.py::t0"])) is True
    assert _is_collection_abort('<testsuite name="pytest" tests="0"></testsuite>') is True
    assert _is_collection_abort(_junit_xml(["saleor/a/tests/test_a.py::t0"])) is False


# ---------------------------------------------------------------------------
# H7 - chunk control: --max-units 0 lists the 32-unit plan
# ---------------------------------------------------------------------------
def test_h7_max_units_zero_lists_plan(monkeypatch: pytest.MonkeyPatch,
                                      capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr("sys.argv", ["wp2_m10b_p2pu_v3_eng.py", "--all-tasks", "--max-units", "0"])
    rc = main()
    out = capsys.readouterr().out
    assert rc == 0
    assert "32 units" in out
    assert "saleor-rc-9258154b8a0b cap200 -> UNDEFINED" in out
    assert "saleor-rc-9258154b8a0b cap400 -> UNDEFINED" in out


# ---------------------------------------------------------------------------
# H8 - manifest completeness
# ---------------------------------------------------------------------------
def test_h8_manifest_schema(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    node_ids = _node_ids(2)
    _patch_exec_env(monkeypatch, tmp_path)
    res = execute_cap(TASK, 200, node_ids, {"rediscovery_sha256": "d1"})

    m = res["manifest"]
    assert m["runner_sha256"] == RUNNER_SHA256
    assert m["harness_v3_spec_sha256"] == HARNESS_SPEC_SHA256
    assert m["rediscovery_sha256"] == "d1"
    assert m["selection_sha256"] == _sha256(node_ids)
    assert m["pytest_flags"] == PYTEST_FLAGS
    assert m["reps"] == 3
    assert m["db_names"] == {"t": f"saleor_v3_{TID}_t", "p": f"saleor_v3_{TID}_p"}
    assert m["junit_dir"] == f"p2pu_v3_junit/{TASK}/cap200"
    assert m["clock_pre_post"]["pre"]["median_skew_s"] == 0.1
    assert m["clock_pre_post"]["post"]["median_skew_s"] == 0.1
    assert m["collection_session_abort"] == {"t": [], "p": []}
    assert m["workers"] == 1
    assert res["evidence_sha256"]
    assert len(res["node_classes"]) == res["n_selected"] == 2


def test_h8_env_fail_second_attempt_terminal(monkeypatch: pytest.MonkeyPatch,
                                             tmp_path: Path) -> None:
    node_ids = _node_ids(2)
    calls = {"n": 0}

    def failing_run(**kwargs):
        calls["n"] += 1
        return {"ok": False, "error": "ENV_FAIL_P2PU", "reason": "INSTALL",
                "db_name": "x", "stdout_tail": "INSTALL_DEV_FAIL", "wall_s": 0.01}

    _patch_exec_env(monkeypatch, tmp_path, run_state=failing_run)
    res = execute_cap(TASK, 200, node_ids, {"rediscovery_sha256": "d1"})
    assert res["status"] == "ENV_FAIL_P2PU"
    assert res["node_classes"] == {}
    # whole unit (both states) retried once -> 2 states x 2 attempts
    assert calls["n"] == 4
    (tmp_path / f"p2pu_v3_eng_{TASK}_cap200.json").exists()
