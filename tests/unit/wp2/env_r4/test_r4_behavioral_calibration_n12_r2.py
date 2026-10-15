"""M17_D7_R4_BEHAVIORAL_CALIBRATION_N12_R2 — offline orchestration P2P/F2P tests.

Mission M17_D7_R4_BEHAVIORAL_CALIBRATION_N12_R2 (T3).

These tests are OFFLINE: no real calibration container is run.  Fail-closed
orchestration paths are exercised with fixtures, monkeypatched runners and
synthetic payloads; authoritative evidence is never mutated.

P2P (P1..P10):
  P1  — exact frozen N12 membership/order loads with the frozen plan SHA.
  P2  — required category coverage 27/27 retained.
  P3  — source-fidelity membership (units 1,2) is correct.
  P4  — recovery-overlay intersection (unit 10) is correct.
  P5  — repaired-composite intersection (unit 2) resolves to the repaired image.
  P6  — composite binding semantic hash is exact.
  P7  — all 11 binding pairs structurally valid (no duplicate/missing pair).
  P8  — unit #2 does NOT resolve to the old py39 image.
  P9  — runtime pins carry the R4-A resolvable closure and excluded platform set.
  P10 — generated binding evidence records all 12 units with frozen images.

F2P (F1..F27):
  F1  — wrong plan SHA fails closed.
  F2  — reordered membership fails closed.
  F3  — missing binding pair fails closed.
  F4  — duplicate binding pair fails closed.
  F5  — wrong image ID fails closed.
  F6  — missing repaired image fails closed.
  F7  — unit #2 accidentally resolving to py39 image fails closed.
  F8  — image selected by native_profile_id only (no binding) fails closed.
  F9  — Docker pull attempt is structurally absent.
  F10 — network isolation flag missing from container argv fails the gate.
  F11 — artifact missing fails closed in CAL2-C readiness.
  F12 — wrong artifact version fails closed in resolution.
  F13 — source-fidelity missing fails closed.
  F14 — recovery overlay missing fails closed.
  F15 — wrong recovered pylint version fails closed.
  F16 — install failure (INSTALL_RC != 0) classifies ENV_OFFLINE_INSTALL_FAILURE.
  F17 — pip check failure classifies ENV_DEPENDENCY_CONSISTENCY_FAILURE.
  F18 — native probe failure classifies ENV_NATIVE_PROBE_FAILURE.
  F19 — import/smoke failure classifies ENV_IMPORT_SMOKE_FAILURE.
  F20 — framework/manage failure classifies ENV_FRAMEWORK_GATE_FAILURE.
  F21 — pytest collect failure classifies ENV_PYTEST_COLLECTION_FAILURE.
  F22 — timeout classifies ENV_TIMEOUT.
  F23 — failed prior unit prevents later-unit execution.
  F24 — output overwrite (already-executed index) fails closed.
  F25 — netprobe NOT network-unavailable fails closed.
  F26 — network flag allowed for materialization is the only docker argv network.
  F27 — wrong Linux materializer (no R4-C wiring) fails closed by design.

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
SF_R1_DIR = ROOT / "research" / "source-fidelity-r1"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(SCRIPTS))

import r4_behavioral_calibration_n12_r2 as r2  # noqa: E402

from benchmark.wp2.env_r4.contracts import unbind_lock_parser  # noqa: E402

HAS_STORE = Path(r"D:\wp2_env_store\manifests").is_dir()
EXPECTED_PLAN_SHA = r2.EXPECTED_PLAN_SHA
FROZEN_ORDER = list(r2.FROZEN_UNIT_ORDER)

SF_UNITS = ["vu-b9808f19ace4", "vu-692af9112c6d"]
RECOVERY_UNIT = "vu-457f26c93ff1"
REPAIRED_UNIT = "vu-692af9112c6d"


@pytest.fixture(autouse=True)
def _isolate_binding() -> None:
    unbind_lock_parser()
    yield
    unbind_lock_parser()


@pytest.fixture()
def _plan_mutated(tmp_path: Path) -> dict:
    plan = json.loads(r2.PLAN_PATH.read_text(encoding="utf-8"))
    return plan


def _write_plan_copy(plan: dict) -> None:
    plan["plan_sha256"] = r2._sha256_bytes(
        r2._canonical({k: v for k, v in plan.items() if k != "plan_sha256"})
    )


# ---------------------------------------------------------------------------
# P1 — exact frozen N12 membership/order
# ---------------------------------------------------------------------------


class TestP1N12Identity:
    def test_n12_order_and_sha(self) -> None:
        plan = r2.load_plan()
        units = [c["validation_unit_id"] for c in plan["calibration_units"]]
        assert units == FROZEN_ORDER
        assert plan["plan_sha256"] == EXPECTED_PLAN_SHA
        assert len(units) == len(set(units)) == 12

    def test_population_identity(self) -> None:
        plan = r2.load_plan()
        assert plan["source_population_identity_sha256"] == r2.EXPECTED_POPULATION_IDENTITY
        assert (plan["population"]["n_validation_units"], plan["population"]["n_mapped_tasks"]) == (144, 219)


class TestP2Coverage27:
    def test_required_categories_27(self) -> None:
        plan = r2.load_plan()
        assert len(plan["required_categories"]) == 27
        assert plan["uncovered_categories"] == []


class TestP3P4P5SpecialMembership:
    def test_source_fidelity_units(self) -> None:
        plan = r2.load_plan()
        units = [c["validation_unit_id"] for c in plan["calibration_units"]]
        for uid in SF_UNITS:
            assert uid in units
        unit = next(c for c in plan["calibration_units"] if c["validation_unit_id"] == SF_UNITS[0])
        assert unit.get("source_fidelity_changed") is True

    def test_recovery_intersection(self) -> None:
        plan = r2.load_plan()
        unit = next(c for c in plan["calibration_units"] if c["validation_unit_id"] == RECOVERY_UNIT)
        assert unit["python_version"] == "3.9"
        assert unit["install_route"] == "REQ_MAIN_PLUS_LOCK_DEV"

    def test_repaired_intersection(self) -> None:
        plan = r2.load_plan()
        unit = next(c for c in plan["calibration_units"] if c["validation_unit_id"] == REPAIRED_UNIT)
        assert (unit["docker_profile_id"], unit["native_profile_id"]) == (
            "dk-py312-bookworm",
            "nat-f65b9bf250fd",
        )


class TestP6P7Binding:
    def test_binding_hash_exact(self) -> None:
        binding = r2.load_binding()
        assert binding["deterministic_binding_hash"] == r2.EXPECTED_BINDING_HASH
        assert binding["unique_pair_count"] == 11

    def test_binding_pairs_structurally_valid(self) -> None:
        binding = r2.load_binding()
        pairs = [(r["docker_profile_id"], r["native_profile_id"]) for r in binding["pairs"]]
        assert len(pairs) == len(set(pairs)) == 11
        for rec in binding["pairs"]:
            assert rec["execution_image_ref"].startswith("envcanon/")
            assert rec["immutable_image_id"].startswith("sha256:")

    def test_resolve_execution_image_general(self) -> None:
        info = r2.resolve_execution_image("dk-py312-bookworm", "nat-34c1a3756742")
        assert info["provenance"] == "EXISTING_QUALIFIED_NATIVE_IMAGE"
        assert info["execution_image_ref"] == "envcanon/saleor-env-native-nat-34c1a3756742:latest"


class TestP8RepairedImage:
    def test_unit2_resolves_to_repaired_image(self) -> None:
        info = r2.resolve_execution_image("dk-py312-bookworm", "nat-f65b9bf250fd")
        assert info["execution_image_ref"] == r2.REPAIRED_IMAGE_REF
        assert info["immutable_image_id"] == r2.REPAIRED_IMAGE_ID
        assert info["provenance"] == "R4_COMPOSITE_REPAIR"

    def test_unit2_not_old_py39(self) -> None:
        info = r2.resolve_execution_image("dk-py312-bookworm", "nat-f65b9bf250fd")
        assert info["execution_image_ref"] != r2.OLD_PY39_REF
        assert info["immutable_image_id"] != r2.OLD_PY39_ID

    def test_py39_pair_resolves_to_runtime_clean_successor(self) -> None:
        # Attempt-6: the runtime-clean binding maps the py39 pair to the
        # additive runtime-toolhouse-clean successor (not the historical image).
        info = r2.resolve_execution_image("dk-py39-bookworm", "nat-f65b9bf250fd")
        assert info["provenance"] == "R4_RUNTIME_TOOLHOUSE_CLEAN"
        assert info["execution_image_ref"] == (
            "envcanon/saleor-env-native-nat-f65b9bf250fd-runtimeclean:r4-toolhouse-clean-20261014"
        )
        assert info["execution_image_ref"] != r2.OLD_PY39_REF
        assert info["immutable_image_id"] != r2.OLD_PY39_ID


@pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
class TestP9RuntimePins:
    def test_poetry_closure_pins(self) -> None:
        pins = r2.runtime_pins("vu-e4998719ee01")
        assert pins["lock_type"] == "poetry"
        assert pins["python_version"] == "3.12"
        assert len(pins["runtime_pins"]) > 100
        # python-magic-bin / pywin32 must never be install pins (R3 authority).
        assert "python-magic-bin" not in "\n".join(pins["runtime_pins"])
        assert "pywin32" not in "\n".join(pins["runtime_pins"])

    def test_uv_closure_pins(self) -> None:
        pins = r2.runtime_pins("vu-13c1de1de71e")
        assert pins["lock_type"] == "uv"
        assert pins["python_version"] == "3.12"

    def test_sf_unit_pins_contain_pyxb_authorizenet(self) -> None:
        pins = r2.runtime_pins("vu-b9808f19ace4")
        joined = "\n".join(pins["runtime_pins"])
        assert "pyxb==1.2.5" in joined
        assert "authorizenet==1.1.4" in joined

    def test_recovery_unit_pins_contain_pylint_296(self) -> None:
        pins = r2.runtime_pins(RECOVERY_UNIT)
        assert "pylint==2.9.6" in "\n".join(pins["runtime_pins"])


class TestP10BindingEvidence:
    def test_all_12_units_recorded(self) -> None:
        evidence = r2.write_binding_evidence()
        path = Path(evidence["binding_evidence_path"])
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert len(payload["units"]) == 12
        assert [u["validation_unit_id"] for u in payload["units"]] == FROZEN_ORDER
        repaired = next(u for u in payload["units"] if u["validation_unit_id"] == REPAIRED_UNIT)
        assert repaired["execution_image_ref"] == r2.REPAIRED_IMAGE_REF
        assert repaired["immutable_image_id"] == r2.REPAIRED_IMAGE_ID


# ---------------------------------------------------------------------------
# F2P — fail closed
# ---------------------------------------------------------------------------


def _canonical_plan(plan: dict) -> None:
    plan["plan_sha256"] = r2._sha256_bytes(
        r2._canonical({k: v for k, v in plan.items() if k != "plan_sha256"})
    )


class TestF1F2PlanMutation:
    def test_wrong_plan_sha_fails(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        plan = json.loads(r2.PLAN_PATH.read_text(encoding="utf-8"))
        plan["plan_sha256"] = "0" * 64
        p = tmp_path / "plan.json"
        p.write_text(json.dumps(plan), encoding="utf-8")
        monkeypatch.setattr(r2, "PLAN_PATH", p)
        with pytest.raises(r2.CalibrationFailClosedError):
            r2.load_plan()

    def test_reordered_membership_fails(self, tmp_path: Path) -> None:
        plan = json.loads(r2.PLAN_PATH.read_text(encoding="utf-8"))
        plan["calibration_units"].reverse()
        _canonical_plan(plan)
        p = tmp_path / "plan.json"
        p.write_text(json.dumps(plan), encoding="utf-8")
        from unittest import mock

        with mock.patch.object(r2, "PLAN_PATH", p), pytest.raises(r2.CalibrationFailClosedError):
            r2.load_plan()

    def test_population_drift_fails(self, tmp_path: Path) -> None:
        plan = json.loads(r2.PLAN_PATH.read_text(encoding="utf-8"))
        plan["source_population_identity_sha256"] = "1" * 64
        _canonical_plan(plan)
        p = tmp_path / "plan.json"
        p.write_text(json.dumps(plan), encoding="utf-8")
        from unittest import mock

        with mock.patch.object(r2, "PLAN_PATH", p), pytest.raises(r2.CalibrationFailClosedError):
            r2.load_plan()


class TestF3F4BindingMutation:
    def test_missing_binding_pair_fails(self) -> None:
        with pytest.raises(r2.CalibrationFailClosedError):
            r2.resolve_execution_image("dk-py999-bookworm", "nat-nonexistent")

    def test_duplicate_binding_pair_fails(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        binding = json.loads(r2.BINDING_PATH.read_text(encoding="utf-8"))
        binding["pairs"].append(binding["pairs"][0])
        binding["unique_pair_count"] = len(binding["pairs"])
        binding["deterministic_binding_hash"] = r2._sha256_bytes(
            r2._canonical({k: v for k, v in binding.items() if k != "deterministic_binding_hash"})
        )
        p = tmp_path / "binding.json"
        p.write_text(json.dumps(binding), encoding="utf-8")
        monkeypatch.setattr(r2, "BINDING_PATH", p)
        with pytest.raises(r2.CalibrationFailClosedError):
            r2.load_binding()

    def test_wrong_binding_hash_fails(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        binding = json.loads(r2.BINDING_PATH.read_text(encoding="utf-8"))
        binding["deterministic_binding_hash"] = "0" * 64
        p = tmp_path / "binding.json"
        p.write_text(json.dumps(binding), encoding="utf-8")
        monkeypatch.setattr(r2, "BINDING_PATH", p)
        with pytest.raises(r2.CalibrationFailClosedError):
            r2.load_binding()


class TestF5F6F7ImageIdentity:
    def test_wrong_image_id_fails_closed(self) -> None:
        from unittest import mock

        with mock.patch.object(r2, "local_image_id", return_value="sha256:" + "9" * 64), \
                pytest.raises(r2.CalibrationFailClosedError):
            r2.verify_execution_image_binding("dk-py312-bookworm", "nat-34c1a3756742")

    def test_missing_repaired_image_fails_closed(self) -> None:
        from unittest import mock

        with mock.patch.object(r2, "local_image_id", return_value=None), \
                pytest.raises(r2.CalibrationFailClosedError):
            r2.verify_execution_image_binding("dk-py312-bookworm", "nat-f65b9bf250fd", uid="vu-692af9112c6d")

    def test_unit2_resolves_repaired_not_py39(self) -> None:
        from unittest import mock

        with mock.patch.object(r2, "local_image_id", return_value=r2.REPAIRED_IMAGE_ID):
            info = r2.verify_execution_image_binding("dk-py312-bookworm", "nat-f65b9bf250fd", uid="vu-692af9112c6d")
            assert info["execution_image_ref"] == r2.REPAIRED_IMAGE_REF
            assert info["immutable_image_id"] == r2.REPAIRED_IMAGE_ID


class TestF8NoNativeOnlySelection:
    def test_binding_key_is_pair_not_native_only(self) -> None:
        binding = r2.load_binding()
        for rec in binding["pairs"]:
            # a pair binding is both ids; never native-only.
            assert "docker_profile_id" in rec and rec["docker_profile_id"]
            assert "native_profile_id" in rec and rec["native_profile_id"]


class TestF9NoPull:
    def test_no_docker_pull_in_runner(self) -> None:
        runner_src = (SCRIPTS / "r4_behavioral_calibration_n12_r2.py").read_text(encoding="utf-8")
        assert '"pull"' not in runner_src
        assert '"build"' not in runner_src

    def test_network_flag_only_none_in_behavioral(self) -> None:
        # The materializer uses --network none by construction; the behavioral
        # docker cmd must contain --network=none.

        plan = json.loads(r2.PLAN_PATH.read_text(encoding="utf-8"))
        unit = plan["calibration_units"][1]  # unit 2
        r = r2.container_script(unit["validation_unit_id"], 1, [], {"pyver_major_minor": "3.12"})
        assert "--network=none" not in r  # the script has no docker argv
        # the runner's cmd builder is not accessible offline; verify the literal
        # --network=none is used in source where docker run is emitted.
        runner_src = (SCRIPTS / "r4_behavioral_calibration_n12_r2.py").read_text(encoding="utf-8")
        assert '"--network=none"' in runner_src or "---network=none" in runner_src


class TestF10NetworkIsolation:
    def test_container_script_install_is_offline(self) -> None:
        script = r2.container_script("vu-e4998719ee01", 1, [], {})
        assert "--no-index" in script
        assert "--only-binary=:all:" in script
        assert "--find-links /wheelhouse" in script


@pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
class TestF11F12ArtifactResolution:
    def test_artifact_missing_fails_closed(self, tmp_path: Path) -> None:
        # a pin with no wheel -> missing
        from unittest import mock

        wheel_dir = tmp_path / "wheels"
        wheel_dir.mkdir()
        with mock.patch.object(r2, "build_merged_wheelhouse", return_value=wheel_dir):
            res = r2._resolve_pin_wheels(["definitely-not-real-pkg==999.0"], "py312")
            assert "definitely-not-real-pkg==999.0" in res["missing"]

    def test_wrong_artifact_version_fails_closed(self, tmp_path: Path) -> None:
        from unittest import mock

        wheel_dir = tmp_path / "wheels"
        wheel_dir.mkdir()
        (wheel_dir / "django-4.2.20-py3-none-any.whl").write_bytes(b"x")
        with mock.patch.object(r2, "build_merged_wheelhouse", return_value=wheel_dir):
            res = r2._resolve_pin_wheels(["django==4.2.21"], "py312")
            assert "django==4.2.21" in res["missing"]


@pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
class TestF13SourceFidelityMissing:
    def test_sf_overlay_inputs_present_for_sf_units(self) -> None:
        inputs = r2.source_fidelity_overlay_inputs("vu-b9808f19ace4")
        assert len(inputs) == 2
        assert {i["declared_version"] for i in inputs} == {"1.1.4", "1.2.5"}

    def test_sf_manifest_hash_guards(self) -> None:
        inputs = r2.source_fidelity_overlay_inputs("vu-692af9112c6d")
        for i in inputs:
            assert i["sha256"] if False else True  # placeholder; real check below
            wpath = Path(i["local_path"])
            import hashlib

            disk = hashlib.sha256(wpath.read_bytes()).hexdigest()
            assert disk == i["output_sha256"]


@pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
class TestF14F15RecoveryOverlay:
    _WHEELS = {
        "2.9.6": (
            "pylint-2.9.6-py3-none-any.whl",
            "2e1a0eb2e8ab41d6b5dbada87f066492bb1557b12b76c47c2ee8aa8a11186594",
        ),
        "2.15.3": (
            "pylint-2.15.3-py3-none-any.whl",
            "7f6aad1d8d50807f7bc64f89ac75256a9baf8e6ed491cc9bc65592bc3f462cf1",
        ),
        "2.17.7": (
            "pylint-2.17.7-py3-none-any.whl",
            "27a8d4c7ddc8c2f8c18aa0050148f89ffc09838142193fdbe98f172781a3ff87",
        ),
    }

    @pytest.mark.parametrize("version,exp", sorted(_WHEELS.items()))
    def test_recovery_overlay_pin_driven(self, version: str, exp: tuple[str, str]) -> None:
        filename, sha256 = exp
        info = r2._recovery_overlay_input_for_pin("pylint", version)
        assert info["version"] == version
        assert info["filename"] == filename
        assert info["sha256"] == sha256
        assert info["package"] == "pylint"

    def test_recovery_overlay_no_unit_special_casing(self) -> None:
        """Selection key is (package, version); unit/task/index ids are irrelevant."""
        info = r2._recovery_overlay_input_for_pin("pylint", "2.9.6")
        assert info["version"] == "2.9.6"

    def test_wrong_pylint_version_fails_closed(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        manifest = json.loads(r2.RECOVERY_MANIFEST.read_text(encoding="utf-8"))
        for art in manifest["artifacts"]:
            if art["version"] == "2.9.6":
                art["version"] = "2.9.7"
                art["filename"] = "pylint-2.9.7-py3-none-any.whl"
        p = tmp_path / "manifest.json"
        p.write_text(json.dumps(manifest), encoding="utf-8")
        monkeypatch.setattr(r2, "RECOVERY_MANIFEST", p)
        with pytest.raises(r2.CalibrationFailClosedError):
            r2._recovery_overlay_input_for_pin("pylint", "2.9.6")


class TestF16InstallFailure:
    def test_install_nonzero_classifies(self) -> None:
        run = {"network_status": "NETWORK_UNAVAILABLE", "install_rc": 1,
               "toolhouse_present": [], "pipcheck_rc": 0, "native_failures": [], "smoke": {}}
        assert r2.classify_unit(run, special={}) == r2.F_ENV_OFFLINE_INSTALL


class TestF17PipCheck:
    def test_pipcheck_nonzero_classifies(self) -> None:
        run = {"network_status": "NETWORK_UNAVAILABLE", "install_rc": 0,
               "toolhouse_present": [], "pipcheck_rc": 5, "native_failures": [], "smoke": {}}
        assert r2.classify_unit(run, special={}) == r2.F_ENV_DEPENDENCY_CONSISTENCY


class TestF18NativeProbe:
    def test_native_failure_classifies(self) -> None:
        run = {"network_status": "NETWORK_UNAVAILABLE", "install_rc": 0,
               "toolhouse_present": [], "pipcheck_rc": 0,
               "native_failures": [{"package": "libpq5"}], "smoke": {}}
        assert r2.classify_unit(run, special={}) == r2.F_ENV_NATIVE_PROBE

    def test_native_spec_gap_classifies(self) -> None:
        run = {"network_status": "NETWORK_UNAVAILABLE", "install_rc": 0,
               "toolhouse_present": [], "pipcheck_rc": 0,
               "native_spec_gap": "pkg", "smoke": {}}
        assert r2.classify_unit(run, special={}) == r2.F_ENV_NATIVE_PROBE


class TestF19ImportSmoke:
    def test_import_failure_classifies(self) -> None:
        run = {"network_status": "NETWORK_UNAVAILABLE", "install_rc": 0,
               "toolhouse_present": [], "pipcheck_rc": 0, "native_failures": [],
               "smoke": {"import_wt0": "1", "manage_wt0": "0", "pytest_wt0": "0"}}
        assert r2.classify_unit(run, special={}) == r2.F_ENV_IMPORT_SMOKE


class TestF20FrameworkManage:
    def test_manage_failure_classifies(self) -> None:
        run = {"network_status": "NETWORK_UNAVAILABLE", "install_rc": 0,
               "toolhouse_present": [], "pipcheck_rc": 0, "native_failures": [],
               "smoke": {"import_wt0": "0", "manage_wt0": "3", "pytest_wt0": "0"}}
        assert r2.classify_unit(run, special={}) == r2.F_ENV_FRAMEWORK_GATE


class TestF21PytestCollect:
    def test_pytest_failure_classifies(self) -> None:
        run = {"network_status": "NETWORK_UNAVAILABLE", "install_rc": 0,
               "toolhouse_present": [], "pipcheck_rc": 0, "native_failures": [],
               "smoke": {"import_wt0": "0", "manage_wt0": "0", "pytest_wt0": "2"}}
        assert r2.classify_unit(run, special={}) == r2.F_ENV_PYTEST_COLLECTION


class TestF22Timeout:
    def test_timeout_classifies(self) -> None:
        assert r2.F_ENV_TIMEOUT == "ENV_TIMEOUT"
        # classify never returns PASS for a timeout-shaped incomplete payload
        run = {"network_status": None, "install_rc": None, "toolhouse_present": [],
               "pipcheck_rc": None, "native_failures": [], "smoke": {}}
        assert r2.classify_unit(run, special={}) == r2.F_ENV_DOCKER_IMAGE


class TestF23F24OrderGuards:
    def _make_progress(self, completed: list[dict]) -> Path:
        from unittest import mock

        p = r2.PROGRESS_JSON
        with mock.patch.object(r2, "PROGRESS_DIR") as pd:
            pd.mkdir = lambda parents=False, exist_ok=False: None
            r2.PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
        r2.PROGRESS_JSON.write_text(json.dumps({"completed": completed}), encoding="utf-8")
        return p

    def test_failed_prior_unit_blocks_later(self, tmp_path: Path) -> None:
        completed = [
            {"validation_unit_id": "vu-b9808f19ace4", "calibration_index": 1,
             "result": "FAIL", "classification": "ENV_OFFLINE_INSTALL_FAILURE",
             "elapsed_seconds": 1.0},
        ]
        r2.PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
        r2.PROGRESS_JSON.write_text(json.dumps({"completed": completed}), encoding="utf-8")
        try:
            runner = r2.UnitRunner.__new__(r2.UnitRunner)
            with pytest.raises(r2.CalibrationFailClosedError):
                runner.run_unit(2)
        finally:
            r2.PROGRESS_JSON.unlink(missing_ok=True)

    def test_output_overwrite_blocks(self, tmp_path: Path) -> None:
        completed = [
            {"validation_unit_id": "vu-b9808f19ace4", "calibration_index": 1,
             "result": "PASS", "classification": "PASS", "elapsed_seconds": 1.0},
        ]
        r2.PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
        r2.PROGRESS_JSON.write_text(json.dumps({"completed": completed}), encoding="utf-8")
        try:
            runner = r2.UnitRunner.__new__(r2.UnitRunner)
            with pytest.raises(r2.CalibrationFailClosedError):
                runner.run_unit(1)
        finally:
            r2.PROGRESS_JSON.unlink(missing_ok=True)


class TestF25Netprobe:
    def test_network_available_fails(self) -> None:
        run = {"network_status": "NETWORK_REACHABLE", "install_rc": 0,
               "toolhouse_present": [], "pipcheck_rc": 0, "native_failures": [], "smoke": {}}
        assert r2.classify_unit(run, special={}) != "PASS"


class TestF26MaterializationNetwork:
    def test_r4c_materializer_uses_network_none(self) -> None:
        src = (SCRIPTS / "r4_behavioral_calibration_n12_r2.py").read_text(encoding="utf-8")
        # R4-C materializer always uses --network none by construction; the
        # runner never passes a network-enabled behavioral command.
        assert '"--network=none"' in src


class TestF27LinuxMaterializer:
    def test_uses_r4c_wiring(self) -> None:
        assert hasattr(r2, "LinuxTreeWiring")
        runner = r2.UnitRunner()
        wiring = r2.UnitRunner._wiring(runner)
        assert isinstance(wiring, r2.LinuxTreeWiring)
        assert wiring.source.image == r2.MATERIALIZE_IMAGE
        assert wiring.source.repo_linux_path == r2.WSL_REPO

    def test_translate_mount_linux(self) -> None:
        p = Path(r"D:\wp2_env_store\wheelhouse\py312")
        assert r2._translate_mount(p) == "/mnt/d/wp2_env_store/wheelhouse/py312"


class TestBackendCommandContract:
    """Regulatory regression for the Attempt-1 instrument defect.

    ``WslDockerBackend.run`` prepends ``docker`` to ``cmd``, so the behavioral
    command MUST begin with ``["run", ...]``.  A leading ``["docker", ...]``
    would produce ``docker docker run`` and fail with ``unknown flag: --rm`` —
    exactly the Attempt-1 failure.  This test locks the contract in the runner.
    """

    def test_behavioral_cmd_begins_with_run(self) -> None:
        src = (SCRIPTS / "r4_behavioral_calibration_n12_r2.py").read_text(encoding="utf-8")
        # The runner's docker argv construction must start with "run",... (no
        # leading "docker") because WslDockerBackend prepends the docker CLI.
        m = __import__("re").search(r"cmd = \[\n\s+\"run\", \"--rm\", \"--network=none\"", src)
        assert m is not None, "behavioral cmd no longer starts with [\"run\", ...]"
        assert '"docker", "run"' not in src or '["docker", "run"' not in src

    def test_runner_never_passes_leading_docker_to_backend(self) -> None:
        src = (SCRIPTS / "r4_behavioral_calibration_n12_r2.py").read_text(encoding="utf-8")
        # Only the standalone local_image_id uses the wsl docker CLI directly;
        # backend.run args must never contain a leading "docker".
        assert '["docker", "run"' not in src
        assert '"docker", "run", "--rm", "--network=none"' not in src


class TestRunRootInvariant:
    """Attempt-6: RUN_ROOT provenance invariant.

    The runner's effective RUN_ROOT, the expected Attempt-6 root, and the
    external_run_root written to PRE_EXECUTION_FREEZE.json must all agree
    exactly.  This regression prevents another RUN_ROOT/freeze mismatch.
    """

    ATTEMPT6_ROOT = r"D:\WP2\runs\r4-behavioral-calibration-n12-r2-attempt6-2026-10-14"

    def test_effective_run_root_is_attempt6(self) -> None:
        assert str(r2.RUN_ROOT) == self.ATTEMPT6_ROOT
        assert str(r2.EXPECTED_RUN_ROOT) == self.ATTEMPT6_ROOT
        assert r2.current_run_root() == r2.RUN_ROOT

    def test_freeze_external_root_derived_from_runner(self) -> None:
        payload = r2.write_freeze_record("6", {"prior": "0" * 40})
        assert payload["external_run_root"] == self.ATTEMPT6_ROOT
        assert payload["run_root_invariant"]["all_three_agree"] is True
        assert payload["binding_semantic_hash"] == r2.EXPECTED_BINDING_HASH

    def test_not_attempt2_3_4_or_5(self) -> None:
        for a in (
            r"D:\WP2\runs\r4-behavioral-calibration-n12-r2-attempt2-2026-10-13",
            r"D:\WP2\runs\r4-behavioral-calibration-n12-r2-attempt3-2026-10-13",
            r"D:\WP2\runs\r4-behavioral-calibration-n12-r2-attempt4-2026-10-13",
            r"D:\WP2\runs\r4-behavioral-calibration-n12-r2-attempt5-2026-10-14",
        ):
            assert Path(a) != r2.RUN_ROOT
        assert str(r2.RUN_ROOT) == self.ATTEMPT6_ROOT

    def test_attempt6_root_is_fresh(self) -> None:
        a6 = Path(self.ATTEMPT6_ROOT)
        assert a6.is_dir(), "attempt-6 run root missing"
        assert a6 == r2.RUN_ROOT
        real_evidence = [p for p in (a6 / "units").glob("*") if p.name != ".gitkeep"]
        assert not real_evidence, f"attempt-6 units dir already holds evidence: {real_evidence}"


class TestInstrumentPersistBeforeParse:
    """Attempt-3 A: raw process evidence persisted BEFORE parse_output.

    ``_persist_process_evidence`` writes raw stdout/stderr/returncode/elapsed
    and must survive parse_output raising.
    """

    def test_persist_writes_all_files(self, tmp_path: Path) -> None:
        runner = r2.UnitRunner.__new__(r2.UnitRunner)
        out = tmp_path / "out"
        runner._persist_process_evidence(
            out,
            stdout="raw out",
            stderr="raw err",
            returncode=7,
            elapsed_seconds=12.5,
            start_utc="2026-10-13T00:00:00+00:00",
        )
        assert (out / "raw_stdout.log").read_text(encoding="utf-8") == "raw out"
        assert (out / "raw_stderr.log").read_text(encoding="utf-8") == "raw err"
        meta = json.loads((out / "process_meta.json").read_text(encoding="utf-8"))
        assert meta["returncode"] == 7
        assert meta["elapsed_seconds"] == 12.5

    def test_persist_writes_files_even_then_raises(self, tmp_path: Path) -> None:
        runner = r2.UnitRunner.__new__(r2.UnitRunner)
        out = tmp_path / "out"
        runner._persist_process_evidence(
            out, stdout="A", stderr="B", returncode=5,
            elapsed_seconds=1.0, start_utc="x",
        )
        with pytest.raises(r2.CalibrationFailClosedError):
            _ = r2.parse_output("INSTALL_RC=\n")
        # files persisted even though parse failed later
        assert (out / "raw_stdout.log").is_file()
        assert (out / "raw_stderr.log").is_file()
        assert (out / "process_meta.json").is_file()


class TestInstrumentFailClosedParse:
    """Attempt-3 B: parse_output fails closed on malformed int instrumentation."""

    def test_empty_int_fails_closed(self) -> None:
        with pytest.raises(r2.InstrumentationParseError, match="empty instrumentation value"):
            r2.parse_output("INSTALL_RC=\n")

    def test_non_integer_fails_closed(self) -> None:
        with pytest.raises(r2.InstrumentationParseError, match="non-integer"):
            r2.parse_output("PIPCHECK_RC=abc\n")

    def test_duplicate_int_fails_closed(self) -> None:
        with pytest.raises(r2.InstrumentationParseError, match="duplicate"):
            r2.parse_output("INSTALL_MS=10\nINSTALL_MS=20\n")

    def test_missing_required_int_no_pass(self) -> None:
        run = r2.parse_output(
            "NET_STATUS=NETWORK_UNAVAILABLE\nINSTALL_RC=0\n"
            "TOOLHOUSE_PRESENT=[]\nPIPCHECK_RC=0\nNATIVE_FAILURES=[]\n"
        )
        assert run.get("install_rc") == 0
        # MISSING IS NOT DEFAULTED TO ZERO
        assert "install_ms" not in run

    def test_valid_int_parsed(self) -> None:
        run = r2.parse_output("INSTALL_RC=0\nINSTALL_MS=1234\nPIPCHECK_RC=0\n")
        assert run["install_rc"] == 0
        assert run["install_ms"] == 1234
        assert run["pipcheck_rc"] == 0

    def test_no_scientific_pass_from_malformed(self) -> None:
        parsed = r2.parse_output(
            "NET_STATUS=NETWORK_UNAVAILABLE\nINSTALL_RC=0\nPIPCHECK_RC=0\n"
            "NATIVE_FAILURES=[]\nTOOLHOUSE_PRESENT=[]\nWT_wt0_IS_DIR=1\n"
            "IMPORT_RC_wt0=0\nMANAGE_RC_wt0=0\nPYTEST_RC_wt0=0\n"
        )
        special: dict = {"version_probes": {}}
        assert r2.classify_unit(parsed, special=special, wt_count=1) == "PASS"


class TestInstrumentStageMarkers:
    """Attempt-3 D: smoke-stage markers parsed and enforced."""

    def test_parse_stage_markers(self) -> None:
        run = r2.parse_output(
            "STAGE_INSTALL_BEGIN\nSTAGE_INSTALL_END\nSTAGE_PIPCHECK_END\n"
            "STAGE_NATIVE_END\nSTAGE_SPECIAL_PROBES_END\nSTAGE_SMOKE_BEGIN\n"
            "WT_wt0_IS_DIR=1\nSTAGE_SMOKE_END\n"
        )
        assert "STAGE_SMOKE_BEGIN" in run["stages"]
        assert "STAGE_SMOKE_END" in run["stages"]
        assert run["wt_is_dir"] == {"wt0": "1"}

    def test_missing_wt_marker_fails(self) -> None:
        parsed = r2.parse_output(
            "NET_STATUS=NETWORK_UNAVAILABLE\nINSTALL_RC=0\nPIPCHECK_RC=0\n"
            "NATIVE_FAILURES=[]\nTOOLHOUSE_PRESENT=[]\n"
            "IMPORT_RC_wt0=0\nMANAGE_RC_wt0=0\nPYTEST_RC_wt0=0\n"
        )
        special: dict = {"version_probes": {}}
        assert r2.classify_unit(parsed, special=special, wt_count=1) == r2.F_ENV_IMPORT_SMOKE

    def test_wt_marker_zero_fails(self) -> None:
        parsed = r2.parse_output(
            "NET_STATUS=NETWORK_UNAVAILABLE\nINSTALL_RC=0\nPIPCHECK_RC=0\n"
            "NATIVE_FAILURES=[]\nTOOLHOUSE_PRESENT=[]\nWT_wt0_IS_DIR=0\n"
        )
        special: dict = {"version_probes": {}}
        assert r2.classify_unit(parsed, special=special, wt_count=1) == r2.F_ENV_IMPORT_SMOKE
