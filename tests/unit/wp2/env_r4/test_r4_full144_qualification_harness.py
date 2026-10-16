"""M17_D7_R4_POPULATION_QUALIFICATION_144_HARNESS — wrapper + guard tests.

These tests exercise ONLY the deterministic qualification harness behaviour:
resume, continue-on-unit-failure, global-integrity fail-closed, environment
sanitization, atomic checkpoint, no pre-freshness redirect, volume cleanup
ownership, no pull/build/network, and the deterministic 144-unit order.

ZERO real Full-D7 qualification units are executed and ZERO Docker workloads are
run: the per-unit runner and every external probe are mocked.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(SCRIPTS))

import r4_full144_qualification_harness as harness  # noqa: E402


def _ids(n: int = 144) -> list[str]:
    return [f"vu-{i:012d}" for i in range(1, n + 1)]


def _order_hash(ids: list[str]) -> str:
    return hashlib.sha256(json.dumps(ids, separators=(",", ":")).encode("utf-8")).hexdigest()


class _FakePopulation:
    EXPECTED_ORDERED_MEMBERSHIP_HASH: str
    EXPECTED_POPULATION_IDENTITY = "p" * 64
    EXPECTED_BINDING_HASH = "b" * 64
    EXPECTED_UNIQUE_PAIRS = 11

    def __init__(self, ids: list[str]) -> None:
        self._ids = ids
        self.EXPECTED_ORDERED_MEMBERSHIP_HASH = _order_hash(ids)

    def ordered_unit_ids(self) -> list[str]:
        return list(self._ids)

    def ordered_membership_hash(self) -> str:
        return _order_hash(self._ids)

    def validate_population(self) -> dict[str, object]:
        return {
            "population_identity": self.EXPECTED_POPULATION_IDENTITY,
            "ordered_membership_hash": _order_hash(self._ids),
            "binding_hash": self.EXPECTED_BINDING_HASH,
            "unique_pairs": 11,
        }


class _FakeDriver:
    def __init__(self, tmp_path: Path) -> None:
        self.PROGRESS_DIR = tmp_path / "progress"
        self.PROGRESS_JSON = tmp_path / "progress" / "progress.json"
        self.UNITS_DIR = tmp_path / "units"
        self.MATERIALIZED_DIR = tmp_path / "materialized"
        self.FULL144_ROOT = tmp_path

    def configure_runner(self) -> None:
        self.PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
        self.UNITS_DIR.mkdir(parents=True, exist_ok=True)
        self.MATERIALIZED_DIR.mkdir(parents=True, exist_ok=True)

    def verify_image_bindings(self) -> list[dict[str, object]]:
        return []


@pytest.fixture(autouse=True)
def _isolate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate QUAL_ROOT + all external probes; provide the fake driver/population."""
    ids = _ids()
    fake = (_FakeDriver(tmp_path), _FakePopulation(ids))
    monkeypatch.setattr(harness, "QUAL_ROOT", tmp_path)
    monkeypatch.setattr(harness, "load_driver", lambda: fake)
    monkeypatch.setattr(harness, "freshness_check", lambda: {
        "branch": harness.FROZEN_BRANCH,
        "git_head": harness.FROZEN_SCIENTIFIC_HEAD,
        "harness_release_head": harness.FROZEN_SCIENTIFIC_HEAD,
        "harness_release_tag": harness.HARNESS_RELEASE_TAG,
        "scientific_authority_head": harness.FROZEN_SCIENTIFIC_HEAD,
        "tracked_clean": True,
        "effective_execution_code_set_hash": harness.FROZEN_CODE_SET_AGGREGATE,
        "population_identity": "p" * 64,
        "ordered_membership_hash": _order_hash(ids),
        "binding_hash": "b" * 64,
        "image_pairs_verified": 11,
        "disk_free_gib": 500.0,
        "docker_reachable": True,
        "source_repo_reachable": True,
    })
    monkeypatch.setattr(harness, "verify_artifact_closure", lambda: {
        "verdict": "PASS_FULL144_STATIC_ARTIFACT_CLOSURE",
        "n_units": 144,
        "n_resolvable": 144,
        "artifact_closure_hash": "c" * 64,
    })
    monkeypatch.setattr(harness, "docker_reachable", lambda: True)
    monkeypatch.setattr(harness, "source_repo_reachable", lambda: True)
    monkeypatch.setattr(harness, "image_bindings_ok", lambda: True)
    monkeypatch.setattr(harness, "disk_free_gib", lambda: 500.0)
    monkeypatch.setattr(harness, "owned_volumes", lambda: [])
    monkeypatch.setattr(harness, "cleanup_unit_wheelhouse", lambda uid: None)
    monkeypatch.setattr(harness, "_persist_harness_failure", lambda uid, exc: tmp_path / "units" / uid / "qf.json")


# ---------------------------------------------------------------------------
# Guard #1 — environment sanitization
# ---------------------------------------------------------------------------
class TestEnvSanitization:
    def test_sanitized_env_removes_ambient_keys(self) -> None:
        monkey = pytest.MonkeyPatch()
        monkey.setenv("R4_FULL144_RUN_ROOT", "D:\\should\\be\\overridden")
        monkey.setenv("PYTEST_ADDOPTS", "-q")
        monkey.setenv("PYTHONINSPECT", "1")
        env = harness.sanitized_env()
        assert env["R4_FULL144_RUN_ROOT"] == str(harness.QUAL_ROOT)
        assert "PYTEST_ADDOPTS" not in env
        assert "PYTHONINSPECT" not in env
        monkey.undo()

    def test_apply_env_sanitization_forces_run_root(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("R4_FULL144_RUN_ROOT", "D:\\other")
        monkeypatch.setenv("PYTHONSTARTUP", "x")
        harness.apply_env_sanitization()
        assert os.environ["R4_FULL144_RUN_ROOT"] == str(harness.QUAL_ROOT)
        assert "PYTHONSTARTUP" not in os.environ


# ---------------------------------------------------------------------------
# Guards #10/#11 — no pull/build/network
# ---------------------------------------------------------------------------
class TestStatic:
    def test_no_pull_build_network(self) -> None:
        checks = harness.static_checks()
        assert checks["no_pull_build"] is True
        assert checks["network_isolation"] == "--network=none"

    def test_runner_forces_network_none(self) -> None:
        runner_src = (SCRIPTS / "r4_behavioral_calibration_n12_r2.py").read_text(encoding="utf-8")
        assert '"--network=none"' in runner_src


# ---------------------------------------------------------------------------
# Guards #3/#4 — volume ownership + cleanup
# ---------------------------------------------------------------------------
class TestVolumeOwnership:
    def test_qualification_volume_prefix_is_unique(self) -> None:
        assert harness.VOLUME_PREFIX == "r4qual144_"
        assert harness.VOLUME_PREFIX != "r4full144_"
        assert harness.VOLUME_PREFIX != "r4n12_"

    def test_cleanup_owned_volumes_removes_each(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[list[str]] = []
        monkeypatch.setattr(
            harness,
            "_run",
            lambda cmd, cwd=None, timeout=120, env=None: calls.append(cmd) or __import__(
                "subprocess"
            ).CompletedProcess(cmd, 0, "", ""),
        )
        harness.cleanup_owned_volumes(["r4qual144_vu_a_t1_0", "r4qual144_vu_a_t2_1"])
        assert len(calls) == 2
        for call, name in zip(calls, ["r4qual144_vu_a_t1_0", "r4qual144_vu_a_t2_1"], strict=False):
            assert "volume" in call and "rm" in call
            assert call[-1] == name


# ---------------------------------------------------------------------------
# Guard #2 — no stdout/stderr redirect files inside a root before freshness
# ---------------------------------------------------------------------------
class TestNoPrefreshnessRedirect:
    def test_global_failure_creates_no_root_artifacts(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _broken() -> dict[str, object]:
            raise harness.GlobalIntegrityError("branch drift")

        monkeypatch.setattr(harness, "freshness_check", _broken)
        with pytest.raises(harness.GlobalIntegrityError):
            harness.run_sweep()
        assert list(tmp_path.iterdir()) == []


# ---------------------------------------------------------------------------
# Global integrity — stop on hash drift / disk / during unit
# ---------------------------------------------------------------------------
class TestGlobalIntegrity:
    def test_stop_on_hash_drift(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def _drift() -> dict[str, object]:
            raise harness.GlobalIntegrityError(
                f"execution-code hash drift: x != {harness.FROZEN_CODE_SET_AGGREGATE}"
            )

        monkeypatch.setattr(harness, "freshness_check", _drift)
        with pytest.raises(harness.GlobalIntegrityError, match="execution-code hash drift"):
            harness.run_sweep()

    def test_stop_below_disk_threshold(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[int] = []

        def _low() -> float:
            calls.append(1)
            return 100.0

        monkeypatch.setattr(harness, "disk_free_gib", _low)
        with pytest.raises(harness.GlobalIntegrityError, match="unsafe low disk"):
            harness.run_sweep()
        assert calls

    def test_stop_when_global_broken_during_unit(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _raise(_idx: int, _uids: list[str]) -> dict[str, object]:
            raise RuntimeError("container died")

        monkeypatch.setattr(harness, "run_one_unit", _raise)
        monkeypatch.setattr(harness, "image_bindings_ok", lambda: False)
        with pytest.raises(harness.GlobalIntegrityError, match="global integrity broken"):
            harness.run_sweep()


# ---------------------------------------------------------------------------
# Resume + continue-on-unit-failure + atomic checkpoint
# ---------------------------------------------------------------------------
class TestSweep:
    def _prefilled_manifest(self, tmp_path: Path, n_pass: int) -> None:
        manifest = harness.new_manifest(harness.freshness_check(), harness.verify_artifact_closure())
        for i in range(1, n_pass + 1):
            manifest["units"][str(i)] = "PASS"
        manifest.update(harness._counts(manifest["units"]))
        harness._atomic_write_json(tmp_path / harness.MANIFEST_NAME, manifest)

    def test_resume_skips_completed_units(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._prefilled_manifest(tmp_path, 3)
        called: list[int] = []

        def _run(idx: int, _uids: list[str]) -> dict[str, object]:
            called.append(idx)
            return {
                "result": "PASS", "classification": "PASS",
                "calibration_index": idx, "validation_unit_id": f"vu-{idx:012d}",
            }

        monkeypatch.setattr(harness, "run_one_unit", _run)
        manifest = harness.run_sweep()
        assert called[0] == 4
        assert len(called) == 141
        assert manifest["pass"] == 144
        assert manifest["pending"] == 0

    def test_continue_after_unit_gate_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        called: list[int] = []

        def _run(idx: int, _uids: list[str]) -> dict[str, object]:
            called.append(idx)
            if idx == 1:
                return {
                    "result": "FAIL", "classification": "ENV_OFFLINE_INSTALL_FAILURE",
                    "calibration_index": 1, "validation_unit_id": f"vu-{idx:012d}",
                }
            return {
                "result": "PASS", "classification": "PASS",
                "calibration_index": idx, "validation_unit_id": f"vu-{idx:012d}",
            }

        monkeypatch.setattr(harness, "run_one_unit", _run)
        manifest = harness.run_sweep()
        assert called[0] == 1 and called[1] == 2
        assert manifest["unit_gate_failure"] == 1
        assert manifest["pass"] == 143
        failures = manifest["failed_units"]
        assert failures[0]["result"] == "UNIT_GATE_FAILURE"
        assert failures[0]["classification"] == "ENV_OFFLINE_INSTALL_FAILURE"

    def test_continue_after_unit_harness_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        called: list[int] = []

        def _run(idx: int, _uids: list[str]) -> dict[str, object]:
            called.append(idx)
            if idx == 2:
                raise RuntimeError("materialization glitch")
            return {
                "result": "PASS", "classification": "PASS",
                "calibration_index": idx, "validation_unit_id": f"vu-{idx:012d}",
            }

        monkeypatch.setattr(harness, "run_one_unit", _run)
        manifest = harness.run_sweep()
        assert called[0:3] == [1, 2, 3]
        assert len(called) == 144
        assert manifest["unit_harness_failure"] == 1
        failures = manifest["failed_units"]
        assert failures[0]["result"] == "UNIT_HARNESS_FAILURE"
        assert failures[0]["classification"] == "RuntimeError"

    def test_atomic_checkpoint_manifest_is_valid(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _run(idx: int, _uids: list[str]) -> dict[str, object]:
            return {
                "result": "PASS", "classification": "PASS",
                "calibration_index": idx, "validation_unit_id": f"vu-{idx:012d}",
            }

        monkeypatch.setattr(harness, "run_one_unit", _run)
        harness.run_sweep()
        path = tmp_path / harness.MANIFEST_NAME
        assert path.is_file()
        assert not (tmp_path / (harness.MANIFEST_NAME + ".tmp")).exists()
        manifest = json.loads(path.read_text(encoding="utf-8"))
        assert manifest["total"] == 144
        assert manifest["pass"] == 144
        assert manifest["pending"] == 0
        assert manifest["zero_network"] is True


# ---------------------------------------------------------------------------
# Resume rejects hash drift (P2 #14)
# ---------------------------------------------------------------------------
class TestResumeDrift:
    def test_resume_rejects_execution_code_drift(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        manifest = harness.new_manifest(harness.freshness_check(), harness.verify_artifact_closure())
        manifest["frozen_execution_code_hash"] = "0" * 64
        harness._atomic_write_json(tmp_path / harness.MANIFEST_NAME, manifest)
        with pytest.raises(harness.GlobalIntegrityError, match="resume drift"):
            harness.run_sweep()


# ---------------------------------------------------------------------------
# Deterministic 144-unit order
# ---------------------------------------------------------------------------
class TestOrder:
    def test_deterministic_144_order(self, monkeypatch: pytest.MonkeyPatch) -> None:
        ids = _ids()
        fake = (_FakeDriver(Path(".")), _FakePopulation(ids))
        monkeypatch.setattr(harness, "load_driver", lambda: fake)
        uids = harness.ordered_uids()
        assert len(uids) == 144
        assert uids == ids
        assert harness.ordered_uids() == ids


# ---------------------------------------------------------------------------
# Compact manifest (P3) required fields
# ---------------------------------------------------------------------------
class TestManifestFields:
    def test_manifest_has_required_p3_fields(
        self, tmp_path: Path
    ) -> None:
        fresh = harness.freshness_check()
        closure = harness.verify_artifact_closure()
        manifest = harness.new_manifest(fresh, closure)
        for key in (
            "scientific_authority_head",
            "harness_release_head",
            "harness_release_tag",
            "frozen_branch",
            "frozen_execution_code_hash",
            "population_identity",
            "population_order_hash",
            "artifact_closure_hash",
            "image_binding_hash",
            "total",
            "units",
            "failed_units",
            "start_utc",
            "last_update_utc",
            "disk_free_gib",
            "zero_network",
        ):
            assert key in manifest
        assert manifest["total"] == 144
        assert manifest["zero_network"] is True
        assert set(manifest["disk_free_gib"]) == {"start", "current", "minimum"}
        assert manifest["scientific_authority_head"] == harness.FROZEN_SCIENTIFIC_HEAD
        assert manifest["harness_release_tag"] == harness.HARNESS_RELEASE_TAG
        assert manifest["frozen_execution_code_hash"] == harness.FROZEN_CODE_SET_AGGREGATE


# ---------------------------------------------------------------------------
# Post-freeze R2 regression — tag-based release identity + structural
# scientific authority (the R1 defect: preflight failed at the harness commit)
# ---------------------------------------------------------------------------
class TestReleaseIdentity:
    """verify_release_identity() with mocked git helpers.

    Positive: scientific authority is the base, current HEAD is a descendant
    harness commit equal to the peeled release tag -> PASS.
    Negative (all fail closed): missing tag, tag != HEAD, base not ancestor,
    extra changed path outside the allowlist.
    """

    HEAD = "ab" * 20
    RELEASE = "ab" * 20

    def _patch(
        self, monkeypatch: pytest.MonkeyPatch, *, peel: str | None = None, head: str | None = None
    ) -> None:
        monkeypatch.setattr(harness, "git_branch", lambda: harness.FROZEN_BRANCH)
        monkeypatch.setattr(harness, "git_clean_tracked", lambda: True)
        monkeypatch.setattr(harness, "git_head", lambda: head or self.HEAD)
        monkeypatch.setattr(harness, "git_peel", lambda tag: peel or self.RELEASE)
        monkeypatch.setattr(harness, "git_is_ancestor", lambda a, h: True)
        monkeypatch.setattr(
            harness,
            "git_diff_name_only",
            lambda a, h: [
                "scripts/r4_full144_qualification_harness.py",
                "scripts/r4_full144_qualification_launcher.ps1",
                "tests/unit/wp2/env_r4/test_r4_full144_qualification_harness.py",
            ],
        )

    def test_preflight_passes_at_release_head(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._patch(monkeypatch)
        identity = harness.verify_release_identity()
        assert identity["git_head"] == self.HEAD
        assert identity["harness_release_head"] == self.RELEASE
        assert identity["harness_release_tag"] == harness.HARNESS_RELEASE_TAG
        assert identity["scientific_authority_head"] == harness.FROZEN_SCIENTIFIC_HEAD

    def test_missing_tag_fails_closed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._patch(monkeypatch)

        def _missing(_tag: str) -> str:
            raise harness.GlobalIntegrityError("release tag missing/unresolvable")

        monkeypatch.setattr(harness, "git_peel", _missing)
        with pytest.raises(harness.GlobalIntegrityError, match="release tag"):
            harness.verify_release_identity()

    def test_tag_not_equal_head_fails_closed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._patch(monkeypatch, peel="1" * 40)
        with pytest.raises(harness.GlobalIntegrityError, match="harness release HEAD"):
            harness.verify_release_identity()

    def test_base_not_ancestor_fails_closed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._patch(monkeypatch)
        monkeypatch.setattr(harness, "git_is_ancestor", lambda a, h: False)
        with pytest.raises(harness.GlobalIntegrityError, match="not an ancestor"):
            harness.verify_release_identity()

    def test_extra_changed_path_fails_closed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._patch(monkeypatch)

        def _extra(_a: str, _h: str) -> list[str]:
            return ["scripts/r4_full144_qualification_harness.py", "src/benchmark/wp2/full144/driver.py"]

        monkeypatch.setattr(harness, "git_diff_name_only", _extra)
        with pytest.raises(harness.GlobalIntegrityError, match="outside harness allowlist"):
            harness.verify_release_identity()

    def test_only_scientific_sha_hardcoded_in_source(self) -> None:
        """ADDENDUM A: the harness source hardcodes ONLY the R2 tag name plus
        the scientific authority SHA — never a harness release commit SHA."""
        import re

        src = (SCRIPTS / "r4_full144_qualification_harness.py").read_text(encoding="utf-8")
        shas = set(re.findall(r"\b[0-9a-f]{40}\b", src))
        assert shas == {harness.FROZEN_SCIENTIFIC_HEAD}
        assert harness.HARNESS_RELEASE_TAG in src
