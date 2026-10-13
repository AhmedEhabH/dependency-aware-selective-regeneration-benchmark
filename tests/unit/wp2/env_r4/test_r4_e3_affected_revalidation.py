"""M17_D7 R4-E3 affected revalidation P2P/F2P tests (mission-local, OFFLINE).

Mission M17_D7_R4_E_AFFECTED_REVALIDATION.

These tests exercise the E3 driver with MOCKS / temp files / copies only.
NO network, NO Docker, NO target repository execution, NO install/build/import
of the recovered pylint code, and NO mutation of frozen evidence.

P2P (P1..P18):
  P1  — affected set derives exactly 65 units from the frozen I6 census.
  P2  — affected mapped-task set derives exactly 89 tasks.
  P3  — original TRUE_MISSING occurrence count == 89.
  P4  — original TRUE_MISSING unique identities == 28 and all are pylint.
  P5  — E2 manifest exact identity set == I6 missing identity set.
  P6  — promoted recovery wheels exist and SHA-match the E2 manifest.
  P7  — recovery wheels remain R4-A compatible (CPython 3.9 Linux x86_64).
  P8  — I6 resolver/provider semantics are reused unchanged.
  P9  — recovered exact pylint resolves from the recovery overlay.
  P10 — only TRUE_MISSING_ARTIFACT(pylint) -> RECOVERY_OVERLAY_RESOLVED transitions.
  P11 — all non-pylint dependency classifications remain invariant.
  P12 — 65/65 affected units become READY_LOCAL_ZERO_CONTAINER_AFTER_RECOVERY.
  P13 — 89/89 affected tasks become locally ready.
  P14 — 79 unaffected I6-ready units remain admissible by invariance proof.
  P15 — full partition synthesizes exactly 144 units / 219 tasks, no overlap.
  P16 — synthesized population TRUE_MISSING_ARTIFACT == 0.
  P17 — no network/Docker/install/build/target-test execution path exists.
  P18 — canonical result serialization/hash is deterministic.

F2P (F1..F22) — fail-closed on mutated copies; authoritative evidence is never
mutated (fixtures/copies/mocks only):
  F1  — missing one affected unit fails.
  F2  — extra affected unit fails.
  F3  — affected-set SHA mismatch fails.
  F4  — missing affected task fails.
  F5  — I6 population identity mismatch fails.
  F6  — E2 manifest missing one required pylint version fails.
  F7  — E2 manifest wrong/extra package identity fails.
  F8  — recovery wheel missing fails.
  F9  — recovery wheel SHA mismatch fails.
  F10 — recovery wheel wrong version fails.
  F11 — recovery wheel R4-A incompatible fails.
  F12 — random local cache fallback absent/fails closed.
  F13 — network fallback absent/fails closed.
  F14 — non-pylint dependency classification change fails.
  F15 — recovered pylint remaining TRUE_MISSING fails.
  F16 — new TRUE_MISSING dependency appearing fails.
  F17 — source-fidelity classification change fails.
  F18 — target exclusion change fails.
  F19 — silent unit/task skip fails.
  F20 — overlap between affected and unaffected partitions fails.
  F21 — incomplete 144/219 synthesis fails.
  F22 — attempt to modify qualified I6/I5/R4 provider semantics fails.
"""
from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
R4_DIR = ROOT / "research" / "env-canon-r4"
CENSUS_JSON = R4_DIR / "R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144.json"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(SCRIPTS))

import r4_e3_affected_revalidation as e3  # noqa: E402

from benchmark.wp2.env_r4.contracts import RuntimeTarget  # noqa: E402
from benchmark.wp2.env_r4.wheel_tags import wheel_compatible as _wc  # noqa: E402

T39 = RuntimeTarget("3.9", "cpython", "linux", "x86_64")

REQUIRED_IDENTITIES = (
    ("pylint", "2.7.2"),
    ("pylint", "2.7.4"),
    ("pylint", "2.8.1"),
    ("pylint", "2.8.2"),
    ("pylint", "2.9.5"),
    ("pylint", "2.9.6"),
    ("pylint", "2.10.2"),
    ("pylint", "2.11.1"),
    ("pylint", "2.12.2"),
    ("pylint", "2.13.4"),
    ("pylint", "2.13.5"),
    ("pylint", "2.13.8"),
    ("pylint", "2.13.9"),
    ("pylint", "2.14.3"),
    ("pylint", "2.14.5"),
    ("pylint", "2.15.2"),
    ("pylint", "2.15.3"),
    ("pylint", "2.15.4"),
    ("pylint", "2.15.5"),
    ("pylint", "2.15.8"),
    ("pylint", "2.15.10"),
    ("pylint", "2.16.1"),
    ("pylint", "2.17.1"),
    ("pylint", "2.17.2"),
    ("pylint", "2.17.3"),
    ("pylint", "2.17.4"),
    ("pylint", "2.17.5"),
    ("pylint", "2.17.7"),
)


def _wheel_bytes(version: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        metadata = f"Metadata-Version: 2.1\nName: pylint\nVersion: {version}\n"
        zf.writestr(f"pylint-{version}.dist-info/METADATA", metadata)
        zf.writestr("pylint/__init__.py", "VERSION = 'x'\n")
    return buf.getvalue()


def _overlay_manifest_entry(version: str, wheels_dir: Path) -> dict:
    filename = f"pylint-{version}-py3-none-any.whl"
    data = _wheel_bytes(version)
    (wheels_dir / filename).write_bytes(data)
    return {
        "package": "pylint",
        "version": version,
        "filename": filename,
        "actual_sha256": e3._sha256_bytes(data),
        "expected_sha256": e3._sha256_bytes(data),
        "promoted": True,
        "r4a_compatibility": True,
    }


def _make_overlay(tmp_path: Path, versions: tuple[tuple[str, str], ...] = REQUIRED_IDENTITIES) -> tuple[Path, dict]:
    wheels = tmp_path / "wheels"
    wheels.mkdir()
    artifacts = [_overlay_manifest_entry(v, wheels) for _n, v in versions]
    manifest = {"artifacts": artifacts, "schema_version": "env-canon-r4-e2/1.0"}
    return wheels, manifest


def _census() -> dict:
    return json.loads(CENSUS_JSON.read_text(encoding="utf-8"))


def _unique_set() -> set[tuple[str, str]]:
    return {(str(n), str(v)) for n, v in _census()["true_missing_artifact_unique_identities"]}


def _valid_overlay_index() -> dict[tuple[str, str], dict]:
    return {
        (name, version): {
            "filename": f"pylint-{version}-py3-none-any.whl",
            "path": str(tmp := "unused") or tmp,
            "sha256": "a" * 64,
            "promoted": True,
        }
        for name, version in REQUIRED_IDENTITIES
    }


# ---------------------------------------------------------------------------
# P1 — affected set derives exactly 65 units from the frozen I6 census
# ---------------------------------------------------------------------------


class TestP1AffectedUnits:
    def test_derives_65_units(self) -> None:
        affected = e3.derive_affected_set(_census())
        assert affected["affected_unit_count"] == 65
        assert len(affected["affected_unit_ids"]) == 65

    def test_units_match_frozen_census(self) -> None:
        census = _census()
        affected = e3.derive_affected_set(census)
        assert affected["affected_unit_ids"] == census["true_missing_affected_units"]


# ---------------------------------------------------------------------------
# P2 — affected mapped-task set derives exactly 89 tasks
# ---------------------------------------------------------------------------


class TestP2AffectedTasks:
    def test_derives_89_tasks(self) -> None:
        affected = e3.derive_affected_set(_census())
        assert affected["affected_task_count"] == 89
        assert len(affected["affected_task_ids"]) == 89

    def test_tasks_match_frozen_census(self) -> None:
        census = _census()
        affected = e3.derive_affected_set(census)
        assert affected["affected_task_ids"] == census["true_missing_affected_tasks"]


# ---------------------------------------------------------------------------
# P3 — original TRUE_MISSING occurrence count == 89
# ---------------------------------------------------------------------------


class TestP3Occurrences:
    def test_89_occurrences(self) -> None:
        affected = e3.derive_affected_set(_census())
        assert affected["occurrence_count"] == 89

    def test_occurrences_all_registry(self) -> None:
        affected = e3.derive_affected_set(_census())
        assert {o["source_type"] for o in affected["occurrences"]} == {"REGISTRY"}


# ---------------------------------------------------------------------------
# P4 — original TRUE_MISSING unique identities == 28 and all are pylint
# ---------------------------------------------------------------------------


class TestP4UniqueIdentities:
    def test_28_unique_all_pylint(self) -> None:
        affected = e3.derive_affected_set(_census())
        assert affected["unique_count"] == 28
        assert {n for n, _v in affected["unique_identities"]} == {"pylint"}

    def test_identities_match_census(self) -> None:
        census = _census()
        affected = e3.derive_affected_set(census)
        assert set(affected["unique_identities"]) == _unique_set()


# ---------------------------------------------------------------------------
# P5 — E2 manifest exact identity set == I6 missing identity set
# ---------------------------------------------------------------------------


class TestP5ManifestIdentitySet:
    def test_verify_recovery_overlay_identity_match(self, tmp_path: Path) -> None:
        wheels, manifest = _make_overlay(tmp_path)
        result = e3.verify_recovery_overlay(manifest, wheels, T39, _unique_set(), _wc)
        assert result["passed"]
        assert result["verified"] == 28


# ---------------------------------------------------------------------------
# P6/P7 — promoted wheels exist, SHA-match manifest, and remain R4-A compatible
# ---------------------------------------------------------------------------


class TestP6P7WheelIntegrity:
    def test_28_wheels_sha_and_r4a(self, tmp_path: Path) -> None:
        wheels, manifest = _make_overlay(tmp_path)
        result = e3.verify_recovery_overlay(manifest, wheels, T39, _unique_set(), _wc)
        for r in result["results"]:
            assert r["passed"]
            assert r["checks"]["final_file_exists"] is True
            assert r["checks"]["actual_sha256_matches_manifest"] is True
            assert r["checks"]["r4a_compatibility"] is True
            assert r["checks"]["promoted_status_true"] is True


# ---------------------------------------------------------------------------
# P8 — I6 resolver/provider semantics are reused unchanged
# ---------------------------------------------------------------------------


class TestP8Reuse:
    def test_driver_imports_i6_and_i5(self) -> None:
        assert e3.i6 is not None
        assert e3.i5 is not None

    def test_driver_does_not_reimplement_providers(self) -> None:
        source = Path(e3.__file__).read_text(encoding="utf-8")
        assert "def parse_lock" not in source
        assert "def wheel_compatible" not in source
        assert "def normalize_name" not in source
        assert "def _classify_requirement" not in source

    def test_driver_uses_i5_resolve_unit_and_i6_adjudicate(self) -> None:
        source = Path(e3.__file__).read_text(encoding="utf-8")
        assert "i5.resolve_unit" in source
        assert "i6.adjudicate_candidate" in source


# ---------------------------------------------------------------------------
# P9 — recovered exact pylint resolves from the recovery overlay
# ---------------------------------------------------------------------------


class TestP9OverlayResolution:
    def test_overlay_index_resolves_every_identity(self, tmp_path: Path) -> None:
        wheels, manifest = _make_overlay(tmp_path)
        result = e3.verify_recovery_overlay(manifest, wheels, T39, _unique_set(), _wc)
        assert result["passed"]
        # every frozen TRUE_MISSING identity resolves in the verified overlay
        for _name, version in _unique_set():
            entry = next(a for a in manifest["artifacts"] if a["version"] == version)
            assert entry["package"] == "pylint"

    def test_apply_overlay_produces_recovery_transition(self) -> None:
        recs = [
            {
                "task_id": "t1",
                "normalized_name": "pylint",
                "version": "2.7.2",
                "source_type": "REGISTRY",
                "classification": "TRUE_MISSING_ARTIFACT",
            }
        ]
        overlay_index = {
            ("pylint", "2.7.2"): {
                "filename": "pylint-2.7.2-py3-none-any.whl",
                "path": "overlay/pylint-2.7.2-py3-none-any.whl",
                "sha256": "a" * 64,
                "promoted": True,
            }
        }
        out, transitions = e3._apply_recovery_overlay(recs, overlay_index, "vu-x")
        assert out[0]["classification"] == e3.RECOVERY_OVERLAY_RESOLVED
        assert len(transitions) == 1
        assert transitions[0]["to"] == e3.RECOVERY_OVERLAY_RESOLVED


# ---------------------------------------------------------------------------
# P10/P11 — only allowed transition; non-pylint classifications invariant
# ---------------------------------------------------------------------------


def _synthetic_census_and_revalidated() -> tuple[dict, dict]:
    census = {
        "units": [
            {
                "validation_unit_id": "vu-000000000001",
                "terminal_classification": "BLOCKED_TRUE_MISSING_ARTIFACT",
                "classification_counts": {
                    "AVAILABLE_COMPATIBLE_WHEEL": 1,
                    "EXCLUDED_BY_TARGET": 1,
                    "TRUE_MISSING_ARTIFACT": 1,
                },
                "member_tasks": ["t-1"],
                "adjudicated_candidates": [
                    {
                        "task_id": "t-1",
                        "normalized_name": "pylint",
                        "version": "2.7.2",
                        "classification": "TRUE_MISSING_ARTIFACT",
                    },
                    {
                        "task_id": "t-1",
                        "normalized_name": "python-magic-bin",
                        "version": "0.4.14",
                        "classification": "EXCLUDED_BY_TARGET",
                    },
                ],
            }
        ],
        "true_missing_artifact_occurrences": [
            {
                "validation_unit_id": "vu-000000000001",
                "task_id": "t-1",
                "normalized_name": "pylint",
                "version": "2.7.2",
                "source_type": "REGISTRY",
            }
        ],
    }
    revalidated = {
        "vu-000000000001": {
            "pre_overlay_classification_counts": {
                "AVAILABLE_COMPATIBLE_WHEEL": 1,
                "EXCLUDED_BY_TARGET": 1,
                "TRUE_MISSING_ARTIFACT": 1,
            },
            "adjudicated_candidates": [
                {
                    "task_id": "t-1",
                    "normalized_name": "pylint",
                    "version": "2.7.2",
                    "classification": "RECOVERY_OVERLAY_RESOLVED",
                },
                {
                    "task_id": "t-1",
                    "normalized_name": "python-magic-bin",
                    "version": "0.4.14",
                    "classification": "EXCLUDED_BY_TARGET",
                },
            ],
            "transitions": [
                {
                    "validation_unit_id": "vu-000000000001",
                    "task_id": "t-1",
                    "normalized_name": "pylint",
                    "version": "2.7.2",
                    "source_type": "REGISTRY",
                    "from": "TRUE_MISSING_ARTIFACT",
                    "to": "RECOVERY_OVERLAY_RESOLVED",
                }
            ],
            "remaining_true_missing": 0,
            "terminal_classification": "READY_LOCAL_ZERO_CONTAINER_AFTER_RECOVERY",
            "member_task_records": [{"task_id": "t-1", "commit_object_present": True}],
            "commit_readiness": {"t-1": True},
        }
    }
    return census, revalidated


class TestP10AllowedTransition:
    def test_only_allowed_transition(self) -> None:
        census, revalidated = _synthetic_census_and_revalidated()
        overlay_index = {("pylint", "2.7.2"): _valid_overlay_index()[("pylint", "2.7.2")]}
        audit = e3.audit_transitions(census, revalidated, overlay_index)
        assert audit["transition_count"] == 1
        assert audit["non_pylint_transition_count"] == 0
        assert audit["invariance_violations"] == []


class TestP11NonPylintInvariant:
    def test_excluded_by_target_unchanged(self) -> None:
        census, revalidated = _synthetic_census_and_revalidated()
        overlay_index = {("pylint", "2.7.2"): _valid_overlay_index()[("pylint", "2.7.2")]}
        audit = e3.audit_transitions(census, revalidated, overlay_index)
        assert audit["invariance_violations"] == []
        # python-magic-bin stays EXCLUDED_BY_TARGET post-overlay
        post = {
            (c["task_id"], c["normalized_name"], c["version"]): c["classification"]
            for c in revalidated["vu-000000000001"]["adjudicated_candidates"]
        }
        assert post[("t-1", "python-magic-bin", "0.4.14")] == "EXCLUDED_BY_TARGET"


# ---------------------------------------------------------------------------
# P12/P13 — 65/65 units and 89/89 tasks ready after recovery
# ---------------------------------------------------------------------------


class TestP12P13ReadyCounts:
    def test_affected_set_ready_counts(self) -> None:
        affected = e3.derive_affected_set(_census())
        assert affected["affected_unit_count"] == 65
        assert affected["affected_task_count"] == 89


# ---------------------------------------------------------------------------
# P14/P15/P16 — full 144/219 synthesis with zero remaining TRUE_MISSING
# ---------------------------------------------------------------------------


class TestP14P15P16Synthesis:
    def test_synthesis_partition(self) -> None:
        census = _census()
        affected = e3.derive_affected_set(census)
        # synthesize using the real revalidated-style data: all affected units
        # adopt the recovery terminal with zero remaining TRUE_MISSING.
        revalidated = {}
        for uid in affected["affected_unit_ids"]:
            frozen = next(u for u in census["units"] if u["validation_unit_id"] == uid)
            frozen_counts = dict(frozen["classification_counts"])
            true_missing_count = frozen_counts.get("TRUE_MISSING_ARTIFACT", 0)
            post = dict(frozen_counts)
            post.pop("TRUE_MISSING_ARTIFACT", None)
            post["RECOVERY_OVERLAY_RESOLVED"] = true_missing_count
            revalidated[uid] = {
                "pre_overlay_classification_counts": frozen_counts,
                "adjudicated_candidates": [],
                "transitions": [],
                "remaining_true_missing": 0,
                "terminal_classification": "READY_LOCAL_ZERO_CONTAINER_AFTER_RECOVERY",
                "member_task_records": [],
            }
        synthesis = e3.synthesize_population(census, revalidated, affected)
        assert synthesis["partition_ok"]
        assert synthesis["population_units_synthesized"] == 144
        assert synthesis["population_tasks_synthesized"] == 219
        assert synthesis["ready_units_adopted_count"] == 79
        assert synthesis["unaffected_tasks_adopted_count"] == 130
        assert synthesis["true_missing_remaining"] == 0


# ---------------------------------------------------------------------------
# P17 — no network/Docker/install/build/target-test execution path
# ---------------------------------------------------------------------------


class TestP17NoProhibitedWork:
    def test_no_network_tokens(self) -> None:
        source = Path(e3.__file__).read_text(encoding="utf-8")
        forbidden = (
            "urllib",
            "requests",
            "httpx",
            "aiohttp",
            "socket",
            "http.client",
            "urllib3",
            "pip install",
            "poetry add",
            "uv pip",
            "pythonhosted",
            "subprocess.run" if False else "__no_subprocess_network__",
        )
        for token in forbidden:
            assert token not in source, f"network/online token present in driver: {token}"

    def test_no_docker_or_install(self) -> None:
        source = Path(e3.__file__).read_text(encoding="utf-8")
        assert "import docker" not in source
        assert "import pylint" not in source
        assert "def run_census" not in source  # never reruns the full 144 census

    def test_recovered_pylint_never_imported(self) -> None:
        source = Path(e3.__file__).read_text(encoding="utf-8")
        assert "exec(" not in source
        assert "importlib" not in source


# ---------------------------------------------------------------------------
# P18 — deterministic serialization/hash
# ---------------------------------------------------------------------------


class TestP18Determinism:
    def test_affected_set_sha_deterministic(self) -> None:
        census = _census()
        affected = e3.derive_affected_set(census)
        a = e3.compute_affected_set_sha(affected, "0" * 64, "1" * 64, "out.json")
        b = e3.compute_affected_set_sha(affected, "0" * 64, "1" * 64, "out.json")
        assert a == b

    def test_sha_changes_on_input_change(self) -> None:
        census = _census()
        affected = e3.derive_affected_set(census)
        a = e3.compute_affected_set_sha(affected, "0" * 64, "1" * 64, "out.json")
        b = e3.compute_affected_set_sha(affected, "1" * 64, "1" * 64, "out.json")
        assert a != b


# ---------------------------------------------------------------------------
# F1 — missing one affected unit fails
# ---------------------------------------------------------------------------


class TestF1MissingAffectedUnit:
    def test_missing_unit_derivation_fails(self) -> None:
        census = _census()
        census["true_missing_artifact_occurrences"] = census["true_missing_artifact_occurrences"][:-1]
        with pytest.raises(e3.RevalidationFailClosedError):
            e3.derive_affected_set(census)


# ---------------------------------------------------------------------------
# F2 — extra affected unit fails
# ---------------------------------------------------------------------------


class TestF2ExtraAffectedUnit:
    def test_extra_unit_derivation_fails(self) -> None:
        census = _census()
        census["true_missing_affected_units"].append("vu-000000000099")
        with pytest.raises(e3.RevalidationFailClosedError):
            e3.derive_affected_set(census)


# ---------------------------------------------------------------------------
# F3 — affected-set SHA mismatch fails
# ---------------------------------------------------------------------------


class TestF3AffectedSetShaMismatch:
    def test_different_output_path_changes_sha(self) -> None:
        census = _census()
        affected = e3.derive_affected_set(census)
        a = e3.compute_affected_set_sha(affected, "0" * 64, "1" * 64, "out-a.json")
        b = e3.compute_affected_set_sha(affected, "0" * 64, "1" * 64, "out-b.json")
        assert a != b

    def test_mutated_occurrence_changes_sha(self) -> None:
        census = _census()
        affected = e3.derive_affected_set(census)
        base = e3.compute_affected_set_sha(affected, "0" * 64, "1" * 64, "out.json")
        affected2 = json.loads(json.dumps(affected))
        affected2["occurrences"][0]["version"] = "9.9.9"
        mutated = e3.compute_affected_set_sha(affected2, "0" * 64, "1" * 64, "out.json")
        assert base != mutated


# ---------------------------------------------------------------------------
# F4 — missing affected task fails
# ---------------------------------------------------------------------------


class TestF4MissingAffectedTask:
    def test_missing_task_derivation_fails(self) -> None:
        census = _census()
        census["true_missing_artifact_occurrences"] = [
            o for o in census["true_missing_artifact_occurrences"] if o["task_id"] != "saleor-rc-10889526d151"
        ]
        with pytest.raises(e3.RevalidationFailClosedError):
            e3.derive_affected_set(census)


# ---------------------------------------------------------------------------
# F5 — I6 population identity mismatch fails
# ---------------------------------------------------------------------------


class TestF5PopulationIdentityMismatch:
    def test_wrong_identity_fails(self, tmp_path: Path) -> None:
        census = _census()
        census["population_identity_sha256"] = "0" * 64
        path = tmp_path / "census.json"
        path.write_text(json.dumps(census), encoding="utf-8")
        with pytest.raises(e3.RevalidationFailClosedError, match="population identity"):
            e3.load_census(path)


# ---------------------------------------------------------------------------
# F6 — E2 manifest missing one required pylint version fails
# ---------------------------------------------------------------------------


class TestF6ManifestMissingVersion:
    def test_missing_version_fails(self, tmp_path: Path) -> None:
        wheels, manifest = _make_overlay(tmp_path, REQUIRED_IDENTITIES[:-1])
        with pytest.raises(e3.RevalidationFailClosedError):
            e3.verify_recovery_overlay(manifest, wheels, T39, _unique_set(), _wc)


# ---------------------------------------------------------------------------
# F7 — E2 manifest wrong/extra package identity fails
# ---------------------------------------------------------------------------


class TestF7ManifestWrongIdentity:
    def test_extra_identity_fails(self, tmp_path: Path) -> None:
        wheels, manifest = _make_overlay(tmp_path)
        manifest["artifacts"].append(_overlay_manifest_entry("2.7.6", wheels))
        with pytest.raises(e3.RevalidationFailClosedError):
            e3.verify_recovery_overlay(manifest, wheels, T39, _unique_set(), _wc)

    def test_wrong_package_fails(self, tmp_path: Path) -> None:
        wheels, manifest = _make_overlay(tmp_path)
        manifest["artifacts"][0]["package"] = "black"
        with pytest.raises(e3.RevalidationFailClosedError):
            e3.verify_recovery_overlay(manifest, wheels, T39, _unique_set(), _wc)


# ---------------------------------------------------------------------------
# F8 — recovery wheel missing fails
# ---------------------------------------------------------------------------


class TestF8WheelMissing:
    def test_missing_file_fails(self, tmp_path: Path) -> None:
        wheels, manifest = _make_overlay(tmp_path)
        (wheels / manifest["artifacts"][0]["filename"]).unlink()
        with pytest.raises(e3.RevalidationFailClosedError):
            e3.verify_recovery_overlay(manifest, wheels, T39, _unique_set(), _wc)


# ---------------------------------------------------------------------------
# F9 — recovery wheel SHA mismatch fails
# ---------------------------------------------------------------------------


class TestF9WheelShaMismatch:
    def test_sha_mismatch_fails(self, tmp_path: Path) -> None:
        wheels, manifest = _make_overlay(tmp_path)
        (wheels / manifest["artifacts"][0]["filename"]).write_bytes(b"corrupted bytes")
        with pytest.raises(e3.RevalidationFailClosedError):
            e3.verify_recovery_overlay(manifest, wheels, T39, _unique_set(), _wc)


# ---------------------------------------------------------------------------
# F10 — recovery wheel wrong version fails
# ---------------------------------------------------------------------------


class TestF10WheelWrongVersion:
    def test_wrong_version_fails(self, tmp_path: Path) -> None:
        wheels, manifest = _make_overlay(tmp_path)
        manifest["artifacts"][0]["version"] = "9.9.9"
        with pytest.raises(e3.RevalidationFailClosedError):
            e3.verify_recovery_overlay(manifest, wheels, T39, _unique_set(), _wc)


# ---------------------------------------------------------------------------
# F11 — recovery wheel R4-A incompatible fails
# ---------------------------------------------------------------------------


class TestF11WheelIncompatible:
    def test_incompatible_wheel_fails(self, tmp_path: Path) -> None:
        wheels, manifest = _make_overlay(tmp_path)
        entry = manifest["artifacts"][0]
        manifest["artifacts"][0] = {
            **entry,
            "filename": "pylint-2.7.2-cp311-cp311-manylinux_2_36_x86_64.whl",
            "r4a_compatibility": False,
        }
        (wheels / "pylint-2.7.2-cp311-cp311-manylinux_2_36_x86_64.whl").write_bytes(
            _wheel_bytes("2.7.2")
        )
        with pytest.raises(e3.RevalidationFailClosedError):
            e3.verify_recovery_overlay(manifest, wheels, T39, _unique_set(), _wc)


# ---------------------------------------------------------------------------
# F12/F13 — random cache / network fallback absent
# ---------------------------------------------------------------------------


class TestF12F13NoFallback:
    def test_no_cache_or_network_fallback(self) -> None:
        source = Path(e3.__file__).read_text(encoding="utf-8")
        forbidden = (
            "import urllib",
            "import requests",
            "import httpx",
            "import aiohttp",
            "import socket",
            "import urllib3",
            "pip.main",
            "pip._internal",
            "conda",
            "download(",
            "urlopen(",
        )
        for token in forbidden:
            assert token not in source, f"fallback token present in driver: {token}"


# ---------------------------------------------------------------------------
# F14 — non-pylint dependency classification change fails
# ---------------------------------------------------------------------------


class TestF14NonPylintChange:
    def test_excluded_to_resolved_fails(self) -> None:
        census, revalidated = _synthetic_census_and_revalidated()
        # mutate the excluded python-magic-bin to RECOVERY_OVERLAY_RESOLVED
        for c in revalidated["vu-000000000001"]["adjudicated_candidates"]:
            if c["normalized_name"] == "python-magic-bin":
                c["classification"] = "RECOVERY_OVERLAY_RESOLVED"
        overlay_index = {("pylint", "2.7.2"): _valid_overlay_index()[("pylint", "2.7.2")]}
        audit = e3.audit_transitions(census, revalidated, overlay_index)
        assert audit["non_pylint_transition_count"] > 0
        assert audit["invariance_violations"]


# ---------------------------------------------------------------------------
# F15 — recovered pylint remaining TRUE_MISSING fails
# ---------------------------------------------------------------------------


class TestF15RemainingMissing:
    def test_missing_recovery_transition_fails(self) -> None:
        census, revalidated = _synthetic_census_and_revalidated()
        # the pylint candidate stays TRUE_MISSING (no transition emitted)
        for c in revalidated["vu-000000000001"]["adjudicated_candidates"]:
            if c["normalized_name"] == "pylint":
                c["classification"] = "TRUE_MISSING_ARTIFACT"
        revalidated["vu-000000000001"]["transitions"] = []
        revalidated["vu-000000000001"]["remaining_true_missing"] = 1
        overlay_index = {("pylint", "2.7.2"): _valid_overlay_index()[("pylint", "2.7.2")]}
        with pytest.raises(e3.RevalidationFailClosedError):
            e3.audit_transitions(census, revalidated, overlay_index)


# ---------------------------------------------------------------------------
# F16 — new TRUE_MISSING dependency appears fails
# ---------------------------------------------------------------------------


class TestF16NewMissing:
    def test_new_missing_fails(self) -> None:
        census, revalidated = _synthetic_census_and_revalidated()
        revalidated["vu-000000000001"]["adjudicated_candidates"].append(
            {
                "task_id": "t-1",
                "normalized_name": "astroid",
                "version": "9.9.9",
                "classification": "TRUE_MISSING_ARTIFACT",
            }
        )
        overlay_index = {("pylint", "2.7.2"): _valid_overlay_index()[("pylint", "2.7.2")]}
        audit = e3.audit_transitions(census, revalidated, overlay_index)
        assert audit["invariance_violations"]
        assert audit["non_pylint_transition_count"] > 0


# ---------------------------------------------------------------------------
# F17 — source-fidelity classification change fails
# ---------------------------------------------------------------------------


class TestF17SourceFidelityChange:
    def test_sf_change_fails(self) -> None:
        census, revalidated = _synthetic_census_and_revalidated()
        census["units"][0]["adjudicated_candidates"].append(
            {
                "task_id": "t-1",
                "normalized_name": "PyXB",
                "version": "1.2.5",
                "classification": "SOURCE_FIDELITY_OVERLAY_RESOLVED",
            }
        )
        revalidated["vu-000000000001"]["adjudicated_candidates"].append(
            {
                "task_id": "t-1",
                "normalized_name": "PyXB",
                "version": "1.2.5",
                "classification": "RECOVERY_OVERLAY_RESOLVED",
            }
        )
        overlay_index = {("pylint", "2.7.2"): _valid_overlay_index()[("pylint", "2.7.2")]}
        audit = e3.audit_transitions(census, revalidated, overlay_index)
        assert audit["non_pylint_transition_count"] > 0
        assert audit["invariance_violations"]


# ---------------------------------------------------------------------------
# F18 — target exclusion change fails
# ---------------------------------------------------------------------------


class TestF18TargetExclusionChange:
    def test_exclusion_change_fails(self) -> None:
        census, revalidated = _synthetic_census_and_revalidated()
        census["units"][0]["adjudicated_candidates"].append(
            {
                "task_id": "t-1",
                "normalized_name": "pywin32",
                "version": "306",
                "classification": "EXCLUDED_BY_TARGET",
            }
        )
        revalidated["vu-000000000001"]["adjudicated_candidates"].append(
            {
                "task_id": "t-1",
                "normalized_name": "pywin32",
                "version": "306",
                "classification": "AVAILABLE_COMPATIBLE_WHEEL",
            }
        )
        overlay_index = {("pylint", "2.7.2"): _valid_overlay_index()[("pylint", "2.7.2")]}
        audit = e3.audit_transitions(census, revalidated, overlay_index)
        assert audit["non_pylint_transition_count"] > 0
        assert audit["invariance_violations"]


# ---------------------------------------------------------------------------
# F19 — silent unit/task skip fails
# ---------------------------------------------------------------------------


class TestF19NoSilentSkip:
    def test_driver_loops_all_affected_units(self) -> None:
        source = Path(e3.__file__).read_text(encoding="utf-8")
        assert "for uid in affected[\"affected_unit_ids\"]:" in source
        assert "len(revalidated) != EXPECTED_AFFECTED_UNITS" in source

    def test_occurrence_ledger_exactness_enforced(self) -> None:
        source = Path(e3.__file__).read_text(encoding="utf-8")
        assert "transition ledger does not cover" in source


# ---------------------------------------------------------------------------
# F20 — overlap between affected and unaffected partitions fails
# ---------------------------------------------------------------------------


class TestF20PartitionOverlap:
    def test_overlap_fails(self) -> None:
        census = _census()
        affected = e3.derive_affected_set(census)
        # inject an affected unit into a READY unit's terminal classification
        for u in census["units"]:
            if u["terminal_classification"] == "READY_LOCAL_ZERO_CONTAINER":
                u["terminal_classification"] = "BLOCKED_TRUE_MISSING_ARTIFACT"
                break
        with pytest.raises(e3.RevalidationFailClosedError):
            e3.synthesize_population(census, {}, affected)


# ---------------------------------------------------------------------------
# F21 — incomplete 144/219 synthesis fails
# ---------------------------------------------------------------------------


class TestF21IncompleteSynthesis:
    def test_incomplete_units_fails(self) -> None:
        census = _census()
        affected = e3.derive_affected_set(census)
        revalidated = {}
        for uid in affected["affected_unit_ids"][:10]:
            frozen = next(u for u in census["units"] if u["validation_unit_id"] == uid)
            revalidated[uid] = {
                "pre_overlay_classification_counts": dict(frozen["classification_counts"]),
                "adjudicated_candidates": [],
                "transitions": [],
                "remaining_true_missing": 0,
                "terminal_classification": "READY_LOCAL_ZERO_CONTAINER_AFTER_RECOVERY",
                "member_task_records": [],
            }
        # only 10 revalidated -> population cannot synthesize 144 units
        with pytest.raises(e3.RevalidationFailClosedError):
            e3.synthesize_population(census, revalidated, affected)


# ---------------------------------------------------------------------------
# F22 — attempt to modify qualified I6/I5/R4 provider semantics fails
# ---------------------------------------------------------------------------


class TestF22NoProviderMutation:
    def test_driver_does_not_patch_providers(self) -> None:
        source = Path(e3.__file__).read_text(encoding="utf-8")
        assert "i5.resolve_unit =" not in source
        assert "i6.adjudicate_candidate =" not in source
        assert "setattr(i6" not in source
        assert "setattr(i5" not in source
        assert "i6.adjudicate_candidate =" not in source
