"""M17_D7 R4-D capability/calibration-plan P2P/F2P tests (mission-local).

Mission M17_D7_R4_D_CAPABILITY_AND_CALIBRATION_PLAN.

Covers:
  P1..P13  positive acceptance checks on the frozen population and plan;
  F1..F11  fail-closed checks on the same algorithm.

The generator script reads frozen manifests from D:\\wp2_env_store.  Tests that
require that store are skipped when it is absent; synthetic fixtures are used
for the field-level fail-closed checks.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import r4d_capability_plan as rp  # noqa: E402

HAS_STORE = Path(r"D:\wp2_env_store\manifests").is_dir()

OUT_DIR = ROOT / "research" / "env-canon-r4"
MATRIX_PATH = OUT_DIR / "R4_CAPABILITY_MATRIX_DRAFT.json"
PLAN_PATH = OUT_DIR / "R4_STRATIFIED_CALIBRATION_PLAN_DRAFT.json"
REPORT_PATH = OUT_DIR / "R4_D_CALIBRATION_COVERAGE_REPORT.md"

OUTCOME_KEYS = ("success", "result", "resolution", "classification", "failure")


def _contains_outcome_keys(obj: object) -> bool:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in OUTCOME_KEYS:
                return True
            if _contains_outcome_keys(value):
                return True
    elif isinstance(obj, list):
        for item in obj:
            if _contains_outcome_keys(item):
                return True
    return False


def make_unit(**overrides: object) -> dict:
    base = {
        "validation_unit_id": "vu-test0000001",
        "member_task_ids": ["saleor-rc-test0001"],
        "member_task_count": 1,
        "era": "py312",
        "python_version": "3.12",
        "lock_sha256": "0" * 64,
        "lock_type": "poetry",
        "install_route": "LOCK_FRAGMENT_MAIN_PLUS_DEV",
        "native_profile_id": "nat-34c1a3756742",
        "docker_profile_id": "dk-py312-bookworm",
        "marker_platform_context": "linux/amd64",
    }
    base.update(overrides)
    return base


def real_units() -> list[dict]:
    return [rp.normalize_unit(r) for r in rp.load_units()]


@pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
class TestPopulationP2P:
    def test_p1_population_144(self):
        units = real_units()
        assert len(units) == 144

    def test_p2_mapped_tasks_219(self):
        units = real_units()
        ids = {t for u in units for t in u["member_task_ids"]}
        assert len(ids) == 219

    def test_p3_strata_25_21_83_15(self):
        units = real_units()
        strata = {}
        for u in units:
            key = (u["python_version"], u["lock_type"])
            strata[key] = strata.get(key, 0) + 1
        assert strata == {("3.12", "poetry"): 25, ("3.12", "uv"): 21, ("3.9", "poetry"): 83, ("3.8", "poetry"): 15}

    def test_p4_every_unit_explicit_python_era(self):
        for u in real_units():
            assert u["python_version"] in ("3.12", "3.8", "3.9")

    def test_p5_every_unit_explicit_lock_type(self):
        for u in real_units():
            assert u["lock_type"] in ("poetry", "uv")

    def test_p6_every_unit_explicit_install_route(self):
        for u in real_units():
            assert u["install_route"] in rp.ALLOWED_INSTALL_ROUTES

    def test_p7_every_unit_explicit_docker_profile(self):
        for u in real_units():
            assert u["docker_profile_id"]

    def test_p8_all_docker_profiles_in_capability_matrix(self):
        matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
        units = real_units()
        required = {u["docker_profile_id"] for u in units}
        represented = {
            i["docker_profile_id"] for i in matrix["docker_image_inventory"]["images"] if i["layer_role"] == "base"
        }
        assert required <= represented

    def test_p9_all_native_profiles_in_capability_matrix(self):
        matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
        units = real_units()
        required = {u["native_profile_id"] for u in units}
        represented = {
            i["native_profile_id"] for i in matrix["docker_image_inventory"]["images"] if i["layer_role"] == "native"
        }
        assert required <= represented

    def test_p10_both_source_fidelity_units_selected(self):
        plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        selected = {c["validation_unit_id"] for c in plan["calibration_units"]}
        assert {"vu-692af9112c6d", "vu-b9808f19ace4"} <= selected

    def test_p11_all_coverage_categories_covered(self):
        plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        assert plan["overall_pass"] is True
        assert plan["uncovered_categories"] == []

    def test_p12_selection_deterministic(self):
        units = real_units()
        first = rp.select_calibration(units)[0]
        second = rp.select_calibration(units)[0]
        assert first == second

    def test_p13_selection_ignores_outcome_fields(self):
        units = real_units()
        baseline = rp.select_calibration(units)[0]
        tainted = []
        for i, u in enumerate(units):
            row = dict(u)
            for key in OUTCOME_KEYS:
                row[key] = ["PASS", "FAIL", "ok", "blocked"][i % 4]
            tainted.append(row)
        assert rp.select_calibration(tainted)[0] == baseline
        plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        assert not _contains_outcome_keys(plan)


@pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
class TestPlanArtifact:
    def test_plan_schema_fields(self):
        plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        for key in (
            "mission_id",
            "source_population_identity_sha256",
            "algorithm",
            "coverage_dimensions",
            "calibration_units",
            "n_calibration",
            "uncovered_categories",
            "overall_pass",
            "plan_sha256",
        ):
            assert key in plan
        first = plan["calibration_units"][0]
        for key in (
            "validation_unit_id",
            "member_task_ids",
            "python_version",
            "lock_type",
            "install_route",
            "docker_profile_id",
            "native_profile_id",
            "source_fidelity_changed",
            "selection_reasons",
        ):
            assert key in first

    def test_plan_sha256_self_consistent(self):
        plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        recomputed = rp._sha256_bytes(rp._canonical({k: v for k, v in plan.items() if k != "plan_sha256"}))
        assert plan["plan_sha256"] == recomputed

    def test_report_status_label(self):
        text = REPORT_PATH.read_text(encoding="utf-8")
        assert "DRAFT_PENDING_R4_INTEGRATION" in text
        assert "NOT FINAL" in text


@pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
class TestFailClosed:
    def test_f1_population_count_mutation(self):
        units = real_units()
        with pytest.raises(rp.PlanValidationError):
            rp.validate_units(units[:-1])

    def test_f2_task_count_mutation(self):
        units = real_units()
        mutated = [dict(u) for u in units]
        mutated[0]["member_task_ids"] = mutated[0]["member_task_ids"][:-1]
        with pytest.raises(rp.PlanValidationError):
            rp.validate_units(mutated)

    def test_f8_stratum_omission_reported(self):
        frozen = real_units()
        required = {c for u in frozen for c in rp.unit_categories(u)}
        stripped = [u for u in frozen if (u["python_version"], u["lock_type"]) != ("3.12", "uv")]
        _, covered, _, _ = rp.select_calibration(stripped)
        missing = required - covered
        assert "stratum:3.12|uv|UV_EXPORT" in missing
        assert not missing <= covered

    def test_f9_source_fidelity_unit_omission_impossible(self):
        units = real_units()
        selected, _, uncovered, _ = rp.select_calibration(units, forced=())
        assert {"vu-692af9112c6d", "vu-b9808f19ace4"} <= set(selected)
        assert not uncovered


class TestFieldFailClosed:
    def test_f3_missing_stratum_metadata(self):
        with pytest.raises(rp.PlanValidationError):
            rp.validate_units([make_unit(python_version="")])

    def test_f4_unknown_lock_type(self):
        with pytest.raises(rp.PlanValidationError):
            rp.validate_units([make_unit(lock_type="pip")])

    def test_f5_unknown_install_route(self):
        with pytest.raises(rp.PlanValidationError):
            rp.validate_units([make_unit(install_route="UNKNOWN_ROUTE")])

    def test_f6_missing_docker_profile(self):
        with pytest.raises(rp.PlanValidationError):
            rp.validate_units([make_unit(docker_profile_id="")])

    def test_f7_missing_native_profile(self):
        with pytest.raises(rp.PlanValidationError):
            rp.validate_units([make_unit(native_profile_id="")])

    def test_f10_outcome_fields_never_consumed(self):
        unit = make_unit()
        for key in OUTCOME_KEYS:
            assert key not in rp.unit_categories(unit)

    @pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
    def test_f11_missing_image_not_silently_available(self):
        def stub(tag: str) -> str | None:
            if tag == "envcanon/saleor-env-native-nat-34c1a3756742:latest":
                return None
            return "sha256:" + "0" * 64

        units = [make_unit()]
        inv = rp.build_docker_inventory(units, image_id_fn=stub)
        assert inv["all_expected_images_present_locally"] is False
        assert "envcanon/saleor-env-native-nat-34c1a3756742:latest" in inv["absent_images"]
        absent = [i for i in inv["images"] if i.get("native_profile_id") == "nat-34c1a3756742"]
        assert absent and absent[0]["local_present"] is False
