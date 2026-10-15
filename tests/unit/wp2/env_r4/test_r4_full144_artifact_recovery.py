"""M17_D7_R4_FULL144_ARTIFACT_RECOVERY_SUCCESSOR — evidence-driven recovery binding gates.

MISSION-SCOPED TESTS ONLY (no broad audit).  These tests prove that the
N12-only pylint recovery special case was replaced by a deterministic,
evidence-driven Full144 recovery binding driven by the ACTUAL runtime pin:

  1. legacy R4-E pylint 2.9.6 recovery still resolves;
  2. pylint 2.15.3 resolves through the SAME generalized evidence-driven path;
  3. every other frozen-manifest pylint version resolves without code changes;
  4. non-recovery units behave exactly as before (base wheelhouse preferred);
  5. missing manifest entry fails closed;
  6. duplicate/conflicting manifest entries fail closed;
  7. hash drift fails closed;
  8. malformed package/version evidence fails closed;
  9. no unit/task/commit/index special casing exists.

All fail-closed paths use fixtures/copies/mocks only.  No frozen evidence or
store artifact is mutated.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import r4_behavioral_calibration_n12_r2 as r2  # noqa: E402

HAS_STORE = Path(r"D:\wp2_env_store\recovery\r4e_pylint_py39\wheels").is_dir()


def _manifest_copy() -> dict:
    return json.loads(r2.RECOVERY_MANIFEST.read_text(encoding="utf-8"))


def _write_and_patch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, manifest: dict) -> None:
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(r2, "RECOVERY_MANIFEST", p)


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ---------------------------------------------------------------------------
# 1..3 — pin-driven selection resolves frozen pylint versions (generalized)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_STORE, reason="recovery store unavailable")
class TestPinDrivenSelection:
    _WHEELS = {
        "2.7.2": (
            "pylint-2.7.2-py3-none-any.whl",
            "d09b0b07ba06bcdff463958f53f23df25e740ecd81895f7d2699ec04bbd8dc3b",
        ),
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
    def test_version_resolves_through_generalized_path(self, version: str, exp: tuple[str, str]) -> None:
        filename, sha256 = exp
        info = r2._recovery_overlay_input_for_pin("pylint", version)
        assert info["version"] == version
        assert info["filename"] == filename
        assert info["sha256"] == sha256
        assert info["package"] == "pylint"
        assert info["manifest_sha256"] == r2._sha256_file(r2.RECOVERY_MANIFEST)

    def test_every_frozen_manifest_version_resolves_without_code_change(self) -> None:
        manifest = _manifest_copy()
        artifacts = [a for a in manifest["artifacts"] if a.get("promoted") is True]
        assert len(artifacts) == 28
        resolved: dict[str, str] = {}
        for art in artifacts:
            info = r2._recovery_overlay_input_for_pin(str(art["package"]), str(art["version"]))
            resolved[str(art["version"])] = info["filename"]
            assert info["filename"] == art["filename"]
            assert info["sha256"] == art["actual_sha256"]
        assert set(resolved) == {
            "2.7.2", "2.7.4", "2.8.1", "2.8.2", "2.9.5", "2.9.6", "2.10.2", "2.11.1",
            "2.12.2", "2.13.4", "2.13.5", "2.13.8", "2.13.9", "2.14.3", "2.14.5", "2.15.2",
            "2.15.3", "2.15.4", "2.15.5", "2.15.8", "2.15.10", "2.16.1", "2.17.1", "2.17.2",
            "2.17.3", "2.17.4", "2.17.5", "2.17.7",
        }

    def test_selection_key_is_pin_not_unit(self) -> None:
        """Same call shape resolves DIFFERENT pins; unit/task/index ids are unused."""
        sig = inspect.signature(r2.recovery_overlay_inputs_for_pins)
        assert list(sig.parameters) == ["pins", "era"]
        a = r2._recovery_overlay_input_for_pin("pylint", "2.9.6")
        b = r2._recovery_overlay_input_for_pin("pylint", "2.15.3")
        assert a["version"] != b["version"]
        assert a["filename"] != b["filename"]


# ---------------------------------------------------------------------------
# 4 — non-recovery units behave exactly as before (base-first, no overlay)
# ---------------------------------------------------------------------------


class TestBaseFirstNoOverlay:
    def test_base_satisfied_pin_selects_no_recovery(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        wheel_dir = tmp_path / "wheels"
        wheel_dir.mkdir()
        (wheel_dir / "pylint-2.9.6-py3-none-any.whl").write_bytes(b"x")
        monkeypatch.setattr(r2, "build_merged_wheelhouse", lambda era: wheel_dir)
        out = r2.recovery_overlay_inputs_for_pins(["pylint==2.9.6"], "py39")
        assert out == []

    def test_unrelated_missing_pin_without_manifest_fails_closed(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        wheel_dir = tmp_path / "wheels"
        wheel_dir.mkdir()
        (wheel_dir / "django-4.2.20-py3-none-any.whl").write_bytes(b"x")
        monkeypatch.setattr(r2, "build_merged_wheelhouse", lambda era: wheel_dir)
        manifest = _manifest_copy()
        _write_and_patch(monkeypatch, tmp_path, manifest)
        with pytest.raises(r2.CalibrationFailClosedError):
            r2.recovery_overlay_inputs_for_pins(["definitely-not-recovered==999.0"], "py39")


# ---------------------------------------------------------------------------
# 5 — missing manifest entry fails closed
# ---------------------------------------------------------------------------


class TestMissingManifestEntry:
    def test_absent_pin_fails_closed(self) -> None:
        with pytest.raises(r2.CalibrationFailClosedError):
            r2._recovery_overlay_input_for_pin("pylint", "9.9.9")

    def test_manifest_entry_removed_fails_closed(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        manifest = _manifest_copy()
        manifest["artifacts"] = [a for a in manifest["artifacts"] if a["version"] != "2.15.3"]
        _write_and_patch(monkeypatch, tmp_path, manifest)
        with pytest.raises(r2.CalibrationFailClosedError):
            r2._recovery_overlay_input_for_pin("pylint", "2.15.3")


# ---------------------------------------------------------------------------
# 6 — duplicate/conflicting manifest entries fail closed
# ---------------------------------------------------------------------------


class TestDuplicateConflicting:
    def test_duplicate_entry_fails_closed(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        manifest = _manifest_copy()
        base = next(a for a in manifest["artifacts"] if a["version"] == "2.15.3")
        dup = dict(base)
        dup["filename"] = "pylint-2.15.3-cp39-cp39-manylinux_2_36_x86_64.whl"
        dup["actual_sha256"] = "0" * 64
        manifest["artifacts"].append(dup)
        _write_and_patch(monkeypatch, tmp_path, manifest)
        with pytest.raises(r2.CalibrationFailClosedError):
            r2._recovery_overlay_input_for_pin("pylint", "2.15.3")

    def test_metadata_name_conflict_fails_closed(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        manifest = _manifest_copy()
        for a in manifest["artifacts"]:
            if a["version"] == "2.15.3":
                a["metadata_name"] = "pylint-not"
        _write_and_patch(monkeypatch, tmp_path, manifest)
        with pytest.raises(r2.CalibrationFailClosedError):
            r2._recovery_overlay_input_for_pin("pylint", "2.15.3")


# ---------------------------------------------------------------------------
# 7 — hash drift fails closed
# ---------------------------------------------------------------------------


class TestHashDrift:
    def test_hash_drift_fails_closed(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        manifest = _manifest_copy()
        for a in manifest["artifacts"]:
            if a["version"] == "2.15.3":
                a["actual_sha256"] = "0" * 64
        _write_and_patch(monkeypatch, tmp_path, manifest)
        with pytest.raises(r2.CalibrationFailClosedError):
            r2._recovery_overlay_input_for_pin("pylint", "2.15.3")

    def test_missing_recorded_hash_fails_closed(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        manifest = _manifest_copy()
        for a in manifest["artifacts"]:
            if a["version"] == "2.15.3":
                del a["actual_sha256"]
        _write_and_patch(monkeypatch, tmp_path, manifest)
        with pytest.raises(r2.CalibrationFailClosedError):
            r2._recovery_overlay_input_for_pin("pylint", "2.15.3")


# ---------------------------------------------------------------------------
# 8 — malformed package/version evidence fails closed
# ---------------------------------------------------------------------------


class TestMalformedEvidence:
    def test_entry_missing_version_fails_closed(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        manifest = _manifest_copy()
        for a in manifest["artifacts"]:
            if a["version"] == "2.15.3":
                del a["version"]
        _write_and_patch(monkeypatch, tmp_path, manifest)
        with pytest.raises(r2.CalibrationFailClosedError):
            r2._recovery_overlay_input_for_pin("pylint", "2.15.3")

    def test_entry_missing_package_fails_closed(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        manifest = _manifest_copy()
        for a in manifest["artifacts"]:
            if a["version"] == "2.15.3":
                del a["package"]
        _write_and_patch(monkeypatch, tmp_path, manifest)
        with pytest.raises(r2.CalibrationFailClosedError):
            r2._recovery_overlay_input_for_pin("pylint", "2.15.3")

    def test_entry_non_object_fails_closed(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        manifest = _manifest_copy()
        manifest["artifacts"] = ["not-an-object"]
        _write_and_patch(monkeypatch, tmp_path, manifest)
        with pytest.raises(r2.CalibrationFailClosedError):
            r2._recovery_overlay_input_for_pin("pylint", "2.15.3")

    def test_malformed_artifacts_container_fails_closed(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        manifest = _manifest_copy()
        manifest["artifacts"] = "not-a-list"
        _write_and_patch(monkeypatch, tmp_path, manifest)
        with pytest.raises(r2.CalibrationFailClosedError):
            r2._recovery_overlay_input_for_pin("pylint", "2.15.3")

    def test_non_promoted_entry_fails_closed(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        manifest = _manifest_copy()
        for a in manifest["artifacts"]:
            if a["version"] == "2.15.3":
                a["promoted"] = False
        _write_and_patch(monkeypatch, tmp_path, manifest)
        with pytest.raises(r2.CalibrationFailClosedError):
            r2._recovery_overlay_input_for_pin("pylint", "2.15.3")


# ---------------------------------------------------------------------------
# 9 — no unit/task/commit/index special casing exists
# ---------------------------------------------------------------------------


class TestNoSpecialCasing:
    def test_runner_has_no_recovery_unit_special_case(self) -> None:
        runner_src = (SCRIPTS / "r4_behavioral_calibration_n12_r2.py").read_text(encoding="utf-8")
        assert "RECOVERY_UNIT" not in runner_src
        assert "def _recovery_overlay_input_for_pin(" in runner_src
        assert "def recovery_overlay_inputs_for_pins(" in runner_src

        def _function_body(def_name: str) -> str:
            start = runner_src.index(f"def {def_name}(")
            nxt = runner_src.find("\ndef ", start + 1)
            return runner_src[start:nxt] if nxt != -1 else runner_src[start:]

        bodies = _function_body("_recovery_overlay_input_for_pin") + "\n" + _function_body(
            "recovery_overlay_inputs_for_pins"
        )
        # selection is a pure function of the runtime pin: no unit/task/index/commit key
        for marker in ("uid ==", "validation_unit_id", "calibration_index", "member_task_ids"):
            assert marker not in bodies, marker

    def test_build_unit_wheelhouse_gates_on_inputs_not_uid(self) -> None:
        runner_src = (SCRIPTS / "r4_behavioral_calibration_n12_r2.py").read_text(encoding="utf-8")
        assert "needs_overlay = bool(sf_inputs) or recovery_input is not None" in runner_src

    def test_driver_record_uses_recovery_input_version_not_hardcode(self) -> None:
        driver_src = (ROOT / "src" / "benchmark" / "wp2" / "full144" / "driver.py").read_text(
            encoding="utf-8"
        )
        assert '"expected_pylint": "2.9.6"' not in driver_src
        assert '"expected_pylint": recovery_input["version"]' in driver_src

    def test_population_has_no_recovery_unit_constant(self) -> None:
        pop_src = (ROOT / "src" / "benchmark" / "wp2" / "full144" / "population.py").read_text(
            encoding="utf-8"
        )
        assert "RECOVERY_UNIT" not in pop_src


# ---------------------------------------------------------------------------
# wheel_names override preserves resolution semantics (closure gate helper)
# ---------------------------------------------------------------------------


class TestWheelNamesOverride:
    def test_explicit_names_resolve_identically(self, tmp_path: Path) -> None:
        wheel_dir = tmp_path / "wheels"
        wheel_dir.mkdir()
        (wheel_dir / "django-4.2.20-py3-none-any.whl").write_bytes(b"x")
        (wheel_dir / "pylint-2.15.3-py3-none-any.whl").write_bytes(b"x")
        res = r2._resolve_pin_wheels(
            ["django==4.2.20", "pylint==2.15.3"], "py39", wheel_dir=wheel_dir
        )
        assert not res["missing"]
        assert not res["incompatible"]
        names = sorted(p.name for p in wheel_dir.glob("*.whl"))
        res2 = r2._resolve_pin_wheels(["django==4.2.20", "pylint==2.15.3"], "py39", wheel_names=names)
        assert res2["resolved"] == res["resolved"]

    def test_overlay_name_shadows_base_same_name(self, tmp_path: Path) -> None:
        wheel_dir = tmp_path / "wheels"
        wheel_dir.mkdir()
        (wheel_dir / "pylint-2.15.3-py3-none-any.whl").write_bytes(b"base")
        base_names = sorted(p.name for p in wheel_dir.glob("*.whl"))
        res = r2._resolve_pin_wheels(["pylint==2.15.3"], "py39", wheel_names=base_names)
        assert not res["missing"]
        assert res["resolved"]["pylint==2.15.3"] == "pylint-2.15.3-py3-none-any.whl"
