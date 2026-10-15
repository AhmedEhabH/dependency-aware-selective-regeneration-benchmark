"""M17_D7_R4_FULL144_SUCCESSOR_REFREEZE — launcher + restart (deterministic only).

Mission M17_D7_R4_FULL144_SUCCESSOR_REFREEZE (T3, PRE-EXECUTION FREEZE).

These tests exercise ONLY deterministic / non-scientific behaviour of the
local unattended launcher (``scripts/r4_full144_successor_launcher.ps1``) and
its preflight gates (``scripts/r4_full144_successor_preflight.py``), plus the
frozen driver's restart/fail-fast semantics.  ZERO real Full-D7 validation
units are executed.

Fail-closed gates covered (RF5):
  F1  wrong git HEAD            -> fail closed
  F2  dirty tracked worktree    -> fail closed
  F3  wrong effective code hash -> fail closed
  F4  wrong population/order/binding hash -> fail closed
  F5  wrong/nonfresh run root   -> fail closed
  F6  missing image             -> fail closed without pull
  F7  completed PASS cannot be rerun/overwritten
  F8  prior FAIL prevents later execution
  F9  progress/evidence disagreement -> fail closed
  F10 partial intent            -> STOP_OWNER_REVIEW
  F11 exact next-unit order
  F12 success loop stops at exactly 144 completed PASS units
  F13 scientific command contains --network=none
  F14 launcher contains no OpenCode/OpenRouter/LLM dependency
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(SCRIPTS))

from r4_full144_successor_preflight import (  # noqa: E402
    POWERSHELL_LAUNCHER,
    LauncherError,
    preflight,
    static_checks,
)

from benchmark.wp2.full144 import driver, population  # noqa: E402

EXPECTED_ORDER = population.ordered_unit_ids()
FROZEN_RUN_ROOT = Path(r"D:\WP2\runs\r4-full-d7-144-successor-2026-10-15")


@pytest.fixture(autouse=True)
def _isolate_driver_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect the frozen driver's progress/units paths to a per-test tmp dir."""
    monkeypatch.setattr(driver, "PROGRESS_JSON", tmp_path / "progress.json")
    monkeypatch.setattr(driver, "PROGRESS_DIR", tmp_path)
    monkeypatch.setattr(driver, "INTENT_JSON", tmp_path / "intent.json")
    monkeypatch.setattr(driver, "UNITS_DIR", tmp_path / "units")
    (tmp_path / "units").mkdir(parents=True, exist_ok=True)


def _minimal_freeze_record(
    tmp_path: Path,
    *,
    branch: str = "parallel/d7-r4-full144-successor-refreeze-2026-10-15",
    final_head: str = "HEAD",
    run_root: str | None = None,
) -> Path:
    """Write a minimal canonical freeze record into a temp run root."""
    run_root_p = Path(run_root or str(tmp_path))
    freeze_dir = run_root_p / "freeze"
    freeze_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "mission_id": "M17_D7_R4_FULL144_SUCCESSOR_REFREEZE",
        "branch": branch,
        "final_freeze_head": final_head,
        "effective_execution_code_set_hash": "eb2a0c4dca00c31a8f4bdc57c337f79e5b51c000125d945f3eb7b3fb57c2c8b3",
        "run_root": str(run_root_p),
    }
    p = freeze_dir / "PRE_EXECUTION_FREEZE.json"
    p.write_text(json.dumps(record), encoding="utf-8")
    return p


class TestF1WrongHead:
    def test_wrong_git_head_fails_closed(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        # freeze record declares a HEAD that differs from the real worktree HEAD
        _minimal_freeze_record(tmp_path, final_head="0" * 40)
        monkeypatch.setattr(driver, "UNITS_DIR", tmp_path / "units")
        monkeypatch.setattr(driver, "PROGRESS_JSON", tmp_path / "progress" / "progress.json")
        monkeypatch.setattr(driver, "PROGRESS_DIR", tmp_path / "progress")
        monkeypatch.setattr(driver, "INTENT_JSON", tmp_path / "progress" / "intent.json")
        with pytest.raises(LauncherError, match="git HEAD"):
            preflight(tmp_path)


class TestF2DirtyWorktree:
    def test_dirty_tracked_worktree_fails_closed(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        _minimal_freeze_record(tmp_path, final_head="REAL_HEAD")
        monkeypatch.setattr("r4_full144_successor_preflight.git_head", lambda: "REAL_HEAD")
        monkeypatch.setattr("r4_full144_successor_preflight.git_clean_tracked", lambda: False)
        with pytest.raises(LauncherError, match="not clean"):
            preflight(tmp_path)


class TestF3WrongCodeHash:
    def test_wrong_effective_code_hash_fails_closed(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        _minimal_freeze_record(tmp_path, final_head="REAL_HEAD")
        monkeypatch.setattr("r4_full144_successor_preflight.git_head", lambda: "REAL_HEAD")
        monkeypatch.setattr("r4_full144_successor_preflight.git_clean_tracked", lambda: True)
        monkeypatch.setattr(
            "r4_full144_successor_preflight.effective_code_set_hash_from_worktree",
            lambda: "0" * 64,
        )
        with pytest.raises(LauncherError, match="code-set hash"):
            preflight(tmp_path)


class TestF4WrongPopulationHash:
    def test_wrong_population_hash_fails_closed(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        _minimal_freeze_record(tmp_path, final_head="REAL_HEAD")
        monkeypatch.setattr("r4_full144_successor_preflight.git_head", lambda: "REAL_HEAD")
        monkeypatch.setattr("r4_full144_successor_preflight.git_clean_tracked", lambda: True)
        monkeypatch.setattr(
            "r4_full144_successor_preflight.effective_code_set_hash_from_worktree",
            lambda: "eb2a0c4dca00c31a8f4bdc57c337f79e5b51c000125d945f3eb7b3fb57c2c8b3",
        )
        monkeypatch.setattr(population, "EXPECTED_ORDERED_MEMBERSHIP_HASH", "1" * 64)
        with pytest.raises(LauncherError, match="ordered membership hash"):
            preflight(tmp_path)


class TestF5WrongRunRoot:
    def test_wrong_run_root_fails_closed(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        run_root_a = tmp_path / "runA"
        run_root_a.mkdir(parents=True, exist_ok=True)
        run_root_b = tmp_path / "runB"
        run_root_b.mkdir(parents=True, exist_ok=True)
        # freeze record in A declares A as the run root
        _minimal_freeze_record(run_root_a, final_head="REAL_HEAD")
        # but the caller points the launcher at B -> must fail closed on run root
        monkeypatch.setattr("r4_full144_successor_preflight.git_head", lambda: "REAL_HEAD")
        monkeypatch.setattr("r4_full144_successor_preflight.git_clean_tracked", lambda: True)
        monkeypatch.setattr(
            "r4_full144_successor_preflight.effective_code_set_hash_from_worktree",
            lambda: "eb2a0c4dca00c31a8f4bdc57c337f79e5b51c000125d945f3eb7b3fb57c2c8b3",
        )
        # load_freeze_record must read the freeze record from the *caller* root;
        # simulate the launcher copying/validating: preflight at B finds no record
        with pytest.raises(LauncherError, match="freeze record missing|run root"):
            preflight(run_root_b)


class TestF6MissingImage:
    def test_missing_image_fails_closed_without_pull(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        _minimal_freeze_record(tmp_path, final_head="REAL_HEAD")
        monkeypatch.setattr("r4_full144_successor_preflight.git_head", lambda: "REAL_HEAD")
        monkeypatch.setattr("r4_full144_successor_preflight.git_clean_tracked", lambda: True)
        monkeypatch.setattr(
            "r4_full144_successor_preflight.effective_code_set_hash_from_worktree",
            lambda: "eb2a0c4dca00c31a8f4bdc57c337f79e5b51c000125d945f3eb7b3fb57c2c8b3",
        )
        # simulate a missing local image: wsl docker inspect returns nonzero
        def _fake_run(cmd, cwd=None, timeout=120):
            if cmd and cmd[-1].startswith("envcanon/") and "inspect" in cmd:
                return __import__("subprocess").CompletedProcess(cmd, 1, "", "image not found (no pull)")
            return __import__("subprocess").CompletedProcess(cmd, 0, "", "")
        monkeypatch.setattr("r4_full144_successor_preflight._run", _fake_run)
        with pytest.raises(LauncherError, match="missing locally"):
            preflight(tmp_path)


class TestF7CompletedNotRerun:
    def test_completed_pass_cannot_be_rerun(self, tmp_path: Path) -> None:
        import json as _json

        driver.PROGRESS_JSON.write_text(_json.dumps({"completed": [
            {"validation_unit_id": EXPECTED_ORDER[0], "calibration_index": 1,
             "result": "PASS", "classification": "PASS", "elapsed_seconds": 1.0},
        ]}), encoding="utf-8")
        rp = driver.UNITS_DIR / EXPECTED_ORDER[0] / "result.json"
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(_json.dumps({
            "validation_unit_id": EXPECTED_ORDER[0], "calibration_index": 1, "result": "PASS",
        }), encoding="utf-8")
        with pytest.raises(driver.Full144FailClosedError, match="already executed"):
            driver.run_unit(1)


class TestF8PriorFailBlocks:
    def test_prior_fail_prevents_later_execution(self, tmp_path: Path) -> None:
        import json as _json

        driver.PROGRESS_JSON.write_text(_json.dumps({"completed": [
            {"validation_unit_id": EXPECTED_ORDER[0], "calibration_index": 1,
             "result": "FAIL", "classification": "ENV_OFFLINE_INSTALL_FAILURE", "elapsed_seconds": 1.0},
        ]}), encoding="utf-8")
        rp = driver.UNITS_DIR / EXPECTED_ORDER[0] / "result.json"
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(_json.dumps({
            "validation_unit_id": EXPECTED_ORDER[0], "calibration_index": 1, "result": "FAIL",
        }), encoding="utf-8")
        with pytest.raises(driver.Full144FailClosedError, match="FAILED"):
            driver.run_unit(2)


class TestF9ProgressEvidenceMismatch:
    def test_progress_evidence_disagreement_fails_closed(self, tmp_path: Path) -> None:
        import json as _json

        # progress claims a completed unit but no result.json exists
        driver.PROGRESS_JSON.write_text(_json.dumps({"completed": [
            {"validation_unit_id": EXPECTED_ORDER[0], "calibration_index": 1,
             "result": "PASS", "classification": "PASS", "elapsed_seconds": 1.0},
        ]}), encoding="utf-8")
        with pytest.raises(driver.Full144FailClosedError, match="progress/evidence mismatch"):
            driver.reconcile()


class TestF10PartialIntentOwnerReview:
    def test_partial_intent_stops_for_owner_review(self, tmp_path: Path) -> None:
        driver.write_intent(1, EXPECTED_ORDER[0])
        with pytest.raises(driver.Full144FailClosedError, match="PARTIAL_INCOMPLETE_UNIT_STOP_OWNER_REVIEW"):
            driver.check_intent()


class TestF11ExactNextUnitOrder:
    def test_next_index_is_exact_next_uncompleted(self, tmp_path: Path) -> None:
        import json as _json

        completed = {}
        for i in range(1, 5):
            uid = EXPECTED_ORDER[i - 1]
            completed[i] = {"validation_unit_id": uid, "calibration_index": i,
                            "result": "PASS", "classification": "PASS", "elapsed_seconds": 1.0}
            rp = driver.UNITS_DIR / uid / "result.json"
            rp.parent.mkdir(parents=True, exist_ok=True)
            rp.write_text(_json.dumps({
                "validation_unit_id": uid, "calibration_index": i, "result": "PASS",
            }), encoding="utf-8")
        driver.PROGRESS_JSON.write_text(_json.dumps({"completed": list(completed.values())}), encoding="utf-8")
        assert driver.next_index(completed) == 5


class TestF12SuccessLoopStopsAt144:
    def test_run_complete_at_exactly_144(self, tmp_path: Path) -> None:
        import json as _json

        completed = []
        for i in range(1, 145):
            uid = EXPECTED_ORDER[i - 1]
            completed.append({"validation_unit_id": uid, "calibration_index": i,
                              "result": "PASS", "classification": "PASS", "elapsed_seconds": 1.0})
            rp = driver.UNITS_DIR / uid / "result.json"
            rp.parent.mkdir(parents=True, exist_ok=True)
            rp.write_text(_json.dumps({
                "validation_unit_id": uid, "calibration_index": i, "result": "PASS",
            }), encoding="utf-8")
        driver.PROGRESS_JSON.write_text(_json.dumps({"completed": completed}), encoding="utf-8")
        result = driver.run_next()
        assert result["status"] == "COMPLETE"
        assert result["n_completed"] == 144


class TestF13NetworkNone:
    def test_scientific_command_contains_network_none(self) -> None:
        runner_src = (SCRIPTS / "r4_behavioral_calibration_n12_r2.py").read_text(encoding="utf-8")
        assert '"--network=none"' in runner_src
        driver_src = (SRC / "benchmark" / "wp2" / "full144" / "driver.py").read_text(encoding="utf-8")
        assert "--network=none" in driver_src


class TestF14NoLLMDependency:
    def test_launcher_has_no_llm_or_network_dependency(self) -> None:
        src = POWERSHELL_LAUNCHER.read_text(encoding="utf-8")
        for forbidden in ("OpenCode", "OpenRouter", "LLM", "openai", "anthropic"):
            assert forbidden.lower() not in src.lower()
        # launcher delegates to the frozen driver; it must not pull/build anything
        assert '"pull"' not in src
        assert '"build"' not in src
        static = static_checks()
        assert static["no_llm_dependency"] is True
        assert static["no_pull_build"] is True
