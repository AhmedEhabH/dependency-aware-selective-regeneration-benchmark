"""M17_D7_R4_FULL144_PREEXECUTION_FREEZE — offline Full144 orchestration tests.

Mission M17_D7_R4_FULL144_PREEXECUTION_FREEZE (T3).

These tests are OFFLINE: no real Full-D7 container is run.  Fail-closed
orchestration paths are exercised with fixtures, monkeypatched runners and
synthetic payloads; authoritative evidence is never mutated.

Themes covered:
  P1  — exact frozen 144 membership + order loads (population hash).
  P2  — 144/219 accounting and strata 25/21/83/15.
  P3  — runtime-clean binding hash + 11 pairs.
  P4  — all 144 units map to a binding pair (0 missing / 0 duplicate / 0 ambiguous).
  F1  — population identity mismatch fails closed.
  F2  — reordered population fails closed.
  F3  — duplicate/missing unit in binding membership fails closed.
  F4  — wrong binding hash fails closed.
  F5  — missing image binding pair fails closed.
  F6  — wrong immutable image ID fails closed.
  F7  — network flag omitted / pull-build attempt is structurally absent.
  F8  — completed-unit overwrite fails closed.
  F9  — resume attempting to rerun completed unit fails closed.
  F10 — progress/evidence mismatch fails closed.
  F11 — failure followed by later-unit execution is blocked (fail-fast).
  F12 — output-root mismatch fails closed.
  F13 — partial/incomplete unit -> STOP_OWNER_REVIEW (no frozen recovery rule).
  F14 — readiness synthesis is bounded (no execution) and 144/144 READY.

F2P uses fixtures/copies/mocks only.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
R4_DIR = ROOT / "research" / "env-canon-r4"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(SCRIPTS))

from benchmark.wp2.env_r4.contracts import unbind_lock_parser  # noqa: E402
from benchmark.wp2.full144 import driver, population  # noqa: E402

HAS_STORE = Path(r"D:\wp2_env_store\manifests").is_dir()

EXPECTED_ORDER = population.ordered_unit_ids()
EXPECTED_POP_IDENTITY = population.EXPECTED_POPULATION_IDENTITY
EXPECTED_BINDING_HASH = population.EXPECTED_BINDING_HASH


@pytest.fixture(autouse=True)
def _isolate_parser() -> None:
    unbind_lock_parser()
    yield
    unbind_lock_parser()


@pytest.fixture()
def _clean_progress(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(driver, "PROGRESS_JSON", tmp_path / "progress.json")
    monkeypatch.setattr(driver, "PROGRESS_DIR", tmp_path)
    monkeypatch.setattr(driver, "INTENT_JSON", tmp_path / "intent.json")
    monkeypatch.setattr(driver, "UNITS_DIR", tmp_path / "units")
    (tmp_path / "units").mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# P1/P2 — exact frozen 144 membership/order and accounting
# ---------------------------------------------------------------------------


class TestP1P2Population:
    def test_exact_144_membership_order(self) -> None:
        ids = population.ordered_unit_ids()
        assert len(ids) == 144
        assert len(set(ids)) == 144
        assert ids == EXPECTED_ORDER

    def test_ordered_membership_hash_exact(self) -> None:
        assert population.ordered_membership_hash() == population.EXPECTED_ORDERED_MEMBERSHIP_HASH

    def test_population_identity_and_accounting(self) -> None:
        census = json.loads(population.CENSUS_PATH.read_text(encoding="utf-8"))
        assert census["population_identity_sha256"] == EXPECTED_POP_IDENTITY
        assert census["processed_units"] == 144
        assert census["processed_mapped_tasks"] == 219

    def test_strata_exact(self) -> None:
        assert population.validate_population()["strata"] == population.EXPECTED_STRATA
        assert population.EXPECTED_STRATA == {"3.12_poetry": 25, "3.12_uv": 21, "3.8_poetry": 15, "3.9_poetry": 83}


class TestP3P4Binding:
    def test_runtime_clean_binding_hash(self) -> None:
        binding = json.loads(population.BINDING_PATH.read_text(encoding="utf-8"))
        assert binding["deterministic_binding_hash"] == EXPECTED_BINDING_HASH
        assert binding["unique_pair_count"] == 11

    def test_all_144_units_mapped_to_pair(self) -> None:
        census = json.loads(population.CENSUS_PATH.read_text(encoding="utf-8"))
        binding = json.loads(population.BINDING_PATH.read_text(encoding="utf-8"))
        pair_keys = {(p["docker_profile_id"], p["native_profile_id"]) for p in binding["pairs"]}
        missing = 0
        for u in census["units"]:
            if (u["docker_profile_id"], u["native_profile_id"]) not in pair_keys:
                missing += 1
        assert missing == 0
        assert len(pair_keys) == 11

    def test_no_duplicate_or_ambiguous_pair(self) -> None:
        binding = json.loads(population.BINDING_PATH.read_text(encoding="utf-8"))
        pair_keys = [(p["docker_profile_id"], p["native_profile_id"]) for p in binding["pairs"]]
        assert len(pair_keys) == len(set(pair_keys)) == 11


# ---------------------------------------------------------------------------
# F2P — fail closed
# ---------------------------------------------------------------------------


class TestF1F2PopulationMutation:
    def test_population_identity_mismatch_fails(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        census = json.loads(population.CENSUS_PATH.read_text(encoding="utf-8"))
        census["population_identity_sha256"] = "1" * 64
        p = tmp_path / "census.json"
        p.write_text(json.dumps(census), encoding="utf-8")
        monkeypatch.setattr(population, "CENSUS_PATH", p)
        with pytest.raises(population.PopulationError):
            population.validate_population()

    def test_reordered_population_fails(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        census = json.loads(population.CENSUS_PATH.read_text(encoding="utf-8"))
        census["units"].reverse()
        p = tmp_path / "census.json"
        p.write_text(json.dumps(census), encoding="utf-8")
        monkeypatch.setattr(population, "CENSUS_PATH", p)
        with pytest.raises(population.PopulationError):
            population.validate_population()


class TestF3DuplicateMissingUnit:
    def test_duplicate_unit_in_census_fails(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        census = json.loads(population.CENSUS_PATH.read_text(encoding="utf-8"))
        census["units"].append(census["units"][0])
        p = tmp_path / "census.json"
        p.write_text(json.dumps(census), encoding="utf-8")
        monkeypatch.setattr(population, "CENSUS_PATH", p)
        with pytest.raises(population.PopulationError):
            population.ordered_unit_ids()

    def test_binding_membership_gap_fails(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        binding = json.loads(population.BINDING_PATH.read_text(encoding="utf-8"))
        # drop one member unit from the first pair -> binding membership no longer covers 144
        binding["pairs"][0]["member_validation_unit_ids"] = binding["pairs"][0]["member_validation_unit_ids"][:-1]
        p = tmp_path / "binding.json"
        p.write_text(json.dumps(binding), encoding="utf-8")
        monkeypatch.setattr(population, "BINDING_PATH", p)
        with pytest.raises(population.PopulationError):
            population.validate_population()


class TestF4WrongBindingHash:
    def test_wrong_binding_hash_fails(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        binding = json.loads(population.BINDING_PATH.read_text(encoding="utf-8"))
        binding["deterministic_binding_hash"] = "0" * 64
        p = tmp_path / "binding.json"
        p.write_text(json.dumps(binding), encoding="utf-8")
        monkeypatch.setattr(population, "BINDING_PATH", p)
        with pytest.raises(population.PopulationError):
            population.validate_population()


class TestF5MissingImageBinding:
    def test_missing_image_binding_pair_fails(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        census = json.loads(population.CENSUS_PATH.read_text(encoding="utf-8"))
        # force a unit to reference an (docker_profile_id, native_profile_id) pair
        # that is NOT present in the 11-pair runtime-clean binding
        census["units"][0]["native_profile_id"] = "nat-does-not-exist"
        p = tmp_path / "census.json"
        p.write_text(json.dumps(census), encoding="utf-8")
        monkeypatch.setattr(driver, "CENSUS_PATH", p)
        with pytest.raises(driver.Full144FailClosedError, match="no binding pair"):
            driver.readiness_manifest()


class TestF6WrongImageID:
    def test_wrong_immutable_image_id_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(driver.r2, "local_image_id", lambda ref: "sha256:" + "9" * 64)
        with pytest.raises(driver.Full144FailClosedError):
            driver.verify_image_bindings()


class TestF7NetworkAndPullBuild:
    def test_network_flag_none_in_behavioral(self) -> None:
        runner_src = (SCRIPTS / "r4_behavioral_calibration_n12_r2.py").read_text(encoding="utf-8")
        assert '"--network=none"' in runner_src

    def test_no_pull_no_build_in_driver(self) -> None:
        src = (SCRIPTS / "r4_full144_preexecution.py").read_text(encoding="utf-8")
        dsrc = (SRC / "benchmark" / "wp2" / "full144" / "driver.py").read_text(encoding="utf-8")
        for s in (src, dsrc):
            assert '"pull"' not in s
            assert '"build"' not in s


class TestF8CompletedUnitOverwrite:
    def test_completed_unit_overwrite_fails(self, _clean_progress: None) -> None:
        driver.PROGRESS_JSON.write_text(
            json.dumps({"completed": [
                {"validation_unit_id": EXPECTED_ORDER[0], "calibration_index": 1,
                 "result": "PASS", "classification": "PASS", "elapsed_seconds": 1.0},
            ]}, sort_keys=True),
            encoding="utf-8",
        )
        rp = driver.UNITS_DIR / EXPECTED_ORDER[0] / "result.json"
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(json.dumps({
            "validation_unit_id": EXPECTED_ORDER[0], "calibration_index": 1, "result": "PASS",
        }), encoding="utf-8")
        with pytest.raises(driver.Full144FailClosedError, match="already executed"):
            driver.run_unit(1)


class TestF9ResumeRerunCompleted:
    def test_resume_refuses_rerun_completed(self, _clean_progress: None) -> None:
        # simulate unit 1 PASS in progress + evidence
        driver.PROGRESS_JSON.write_text(
            json.dumps({"completed": [
                {"validation_unit_id": EXPECTED_ORDER[0], "calibration_index": 1,
                 "result": "PASS", "classification": "PASS", "elapsed_seconds": 1.0},
            ]}, sort_keys=True),
            encoding="utf-8",
        )
        rp = driver.UNITS_DIR / EXPECTED_ORDER[0] / "result.json"
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(json.dumps({
            "validation_unit_id": EXPECTED_ORDER[0], "calibration_index": 1, "result": "PASS",
        }), encoding="utf-8")
        # run_next must target unit 2, never unit 1
        completed = driver.read_completed()
        assert driver.next_index(completed) == 2


class TestF10ProgressEvidenceMismatch:
    def test_progress_without_evidence_fails(self, _clean_progress: None) -> None:
        driver.PROGRESS_JSON.write_text(
            json.dumps({"completed": [
                {"validation_unit_id": EXPECTED_ORDER[0], "calibration_index": 1,
                 "result": "PASS", "classification": "PASS", "elapsed_seconds": 1.0},
            ]}, sort_keys=True),
            encoding="utf-8",
        )
        with pytest.raises(driver.Full144FailClosedError, match="progress/evidence mismatch"):
            driver.reconcile()

    def test_evidence_without_progress_fails(self, _clean_progress: None) -> None:
        rp = driver.UNITS_DIR / EXPECTED_ORDER[0] / "result.json"
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(json.dumps({
            "validation_unit_id": EXPECTED_ORDER[0], "calibration_index": 1, "result": "PASS",
        }), encoding="utf-8")
        with pytest.raises(driver.Full144FailClosedError, match="progress/evidence mismatch"):
            driver.reconcile()


class TestF11FailureBlocksLater:
    def test_failed_unit_blocks_later_unit(self, _clean_progress: None) -> None:
        driver.PROGRESS_JSON.write_text(
            json.dumps({"completed": [
                {"validation_unit_id": EXPECTED_ORDER[0], "calibration_index": 1,
                 "result": "FAIL", "classification": "ENV_OFFLINE_INSTALL_FAILURE", "elapsed_seconds": 1.0},
            ]}, sort_keys=True),
            encoding="utf-8",
        )
        rp = driver.UNITS_DIR / EXPECTED_ORDER[0] / "result.json"
        rp.parent.mkdir(parents=True, exist_ok=True)
        rp.write_text(json.dumps({
            "validation_unit_id": EXPECTED_ORDER[0], "calibration_index": 1, "result": "FAIL",
        }), encoding="utf-8")
        with pytest.raises(driver.Full144FailClosedError, match="FAILED"):
            driver.run_unit(2)


class TestF12OutputRootMismatch:
    def test_run_root_is_canonical(self) -> None:
        assert driver.EXPECTED_RUN_ROOT_STR == r"D:\WP2\runs\r4-full-d7-144-2026-10-14"
        assert str(driver.FULL144_ROOT) == driver.EXPECTED_RUN_ROOT_STR
        assert driver.UNITS_DIR == driver.FULL144_ROOT / "units"
        assert driver.PROGRESS_JSON == driver.FULL144_ROOT / "progress" / "progress.json"


class TestF13PartialUnitOwnerReview:
    def test_partial_intent_owner_review(self, _clean_progress: None) -> None:
        driver.write_intent(1, EXPECTED_ORDER[0])
        with pytest.raises(driver.Full144FailClosedError, match="PARTIAL_INCOMPLETE_UNIT_STOP_OWNER_REVIEW"):
            driver.check_intent()


class TestF14ReadinessBounded:
    def test_readiness_144_ready(self) -> None:
        rows = driver.readiness_manifest()
        assert len(rows) == 144
        summary = driver.readiness_summary(rows)
        assert summary == {"READY": 144, "BLOCKED": 0, "AMBIGUOUS": 0, "FALLBACK": 0}

    def test_readiness_rows_have_all_fields(self) -> None:
        rows = driver.readiness_manifest()
        for r in rows:
            for k in (
                "validation_unit_id", "member_task_ids", "python_version", "lock_type",
                "install_route", "wheelhouse_era", "docker_profile_id", "native_profile_id",
                "execution_image_ref", "immutable_image_id", "readiness_verdict",
            ):
                assert k in r
