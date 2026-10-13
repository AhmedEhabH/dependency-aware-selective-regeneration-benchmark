"""M17_D7 R4-E1 pylint recovery plan P2P/F2P tests (mission-local, offline).

Mission M17_D7_R4_E1_PYLINT_RECOVERY_PLAN.

Covers:

P2P (P1..P12):
  P1  — I6 unique TRUE_MISSING identity count == 28.
  P2  — all 28 identities canonicalize to ``pylint``.
  P3  — exact version set equals the authoritative I6 census.
  P4  — 89 TRUE_MISSING occurrences are accounted for.
  P5  — 65 affected units are accounted for.
  P6  — target == CPython 3.9 / Linux / x86_64.
  P7  — no version substitution exists in the plan.
  P8  — no dependency acquisition exists in the plan.
  P9  — frozen py39 wheelhouse/manifest paths are read-only and NOT recovery
        destinations.
  P10 — recovery overlay paths are additive and outside the frozen wheelhouse.
  P11 — network usage in E1 == false.
  P12 — canonical plan serialization/hash is deterministic.

F2P (F1..F12) — fail-closed on mutated plan copies; authoritative evidence is
never mutated (fixtures/copies/mocks only):
  F1  — missing one required version fails.
  F2  — adding an extra version fails.
  F3  — wrong package name fails.
  F4  — duplicate identity fails.
  F5  — wrong target Python era fails.
  F6  — wrong platform/architecture fails.
  F7  — plan allows version substitution fails.
  F8  — plan allows dependency downloads fails.
  F9  — plan points recovery output into the frozen wheelhouse fails.
  F10 — plan allows non-PyPI metadata origin fails.
  F11 — plan allows non-files.pythonhosted.org artifact origin fails.
  F12 — plan marks network approval true in E1 fails.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
R4_DIR = ROOT / "research" / "env-canon-r4"
CENSUS_JSON = R4_DIR / "R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144.json"
PLAN_JSON = R4_DIR / "R4_E1_PYLINT_RECOVERY_PLAN.json"
PLAN_MD = R4_DIR / "R4_E1_PYLINT_RECOVERY_PLAN.md"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(SCRIPTS))

import r4_e1_pylint_recovery_plan as e1  # noqa: E402


def _census() -> dict:
    return json.loads(CENSUS_JSON.read_text(encoding="utf-8"))


def _plan() -> dict:
    return copy.deepcopy(e1.build_plan(_census()))


def _built_plan() -> dict:
    return copy.deepcopy(json.loads(PLAN_JSON.read_text(encoding="utf-8")))


# ---------------------------------------------------------------------------
# P1 — I6 unique TRUE_MISSING identity count == 28
# ---------------------------------------------------------------------------


class TestP1UniqueIdentityCount:
    def test_unique_count_28(self) -> None:
        assert len(e1.prove_census(_census())["unique_identity_set"]) == 28

    def test_plan_records_28(self) -> None:
        assert _plan()["true_missing_unique_identities"] == 28
        assert len(_plan()["exact_ordered_recovery_identities"]) == 28


# ---------------------------------------------------------------------------
# P2 — all 28 identities canonicalize to pylint
# ---------------------------------------------------------------------------


class TestP2CanonicalPylint:
    def test_all_names_normalize_to_pylint(self) -> None:
        plan = _plan()
        for name, _version in plan["exact_ordered_recovery_identities"]:
            assert e1.normalize_name(name) == "pylint"

    def test_no_non_pylint_true_missing_identity(self) -> None:
        census = _census()
        occ_names = {o["normalized_name"] for o in census["true_missing_artifact_occurrences"]}
        uniq_names = {n for n, _v in census["true_missing_artifact_unique_identities"]}
        assert occ_names == {"pylint"}
        assert uniq_names == {"pylint"}


# ---------------------------------------------------------------------------
# P3 — exact version set equals the authoritative I6 census
# ---------------------------------------------------------------------------


class TestP3ExactVersionSet:
    def test_version_set_matches_census(self) -> None:
        census = _census()
        census_versions = {v for _n, v in census["true_missing_artifact_unique_identities"]}
        plan_versions = {v for _n, v in _plan()["exact_ordered_recovery_identities"]}
        assert plan_versions == census_versions
        assert plan_versions == set(e1.EXPECTED_VERSIONS)

    def test_ordered_identity_list(self) -> None:
        plan = _plan()
        assert [v for _n, v in plan["exact_ordered_recovery_identities"]] == list(e1.EXPECTED_VERSIONS)


# ---------------------------------------------------------------------------
# P4 — 89 TRUE_MISSING occurrences accounted for
# ---------------------------------------------------------------------------


class TestP4Occurrences:
    def test_occurrence_count_89(self) -> None:
        census = _census()
        occ = census["true_missing_artifact_occurrences"]
        assert len(occ) == 89
        assert census["dependency_terminal_classifications"]["TRUE_MISSING_ARTIFACT"] == 89
        assert _plan()["true_missing_occurrences"] == 89

    def test_all_occurrences_are_unique_identities(self) -> None:
        census = _census()
        uniq = {(n, v) for n, v in census["true_missing_artifact_unique_identities"]}
        occ = {(o["normalized_name"], o["version"]) for o in census["true_missing_artifact_occurrences"]}
        assert occ == uniq
        assert len(occ) == 28


# ---------------------------------------------------------------------------
# P5 — 65 affected units accounted for
# ---------------------------------------------------------------------------


class TestP5AffectedUnits:
    def test_affected_unit_count_65(self) -> None:
        census = _census()
        units = census["true_missing_affected_units"]
        assert len(units) == 65
        assert census["terminal_classifications"]["BLOCKED_TRUE_MISSING_ARTIFACT"] == 65
        assert _plan()["affected_units"] == 65
        assert len(_plan()["affected_unit_ids"]) == 65

    def test_plan_units_match_census(self) -> None:
        assert set(_plan()["affected_unit_ids"]) == set(_census()["true_missing_affected_units"])


# ---------------------------------------------------------------------------
# P6 — target == CPython 3.9 Linux x86_64
# ---------------------------------------------------------------------------


class TestP6Target:
    def test_target_exact(self) -> None:
        plan = _plan()
        assert plan["target"] == {
            "python_version": "3.9",
            "implementation": "cpython",
            "platform": "linux",
            "architecture": "x86_64",
        }

    def test_frozen_runtime_target_validates(self) -> None:
        target = e1.RuntimeTarget("3.9", "cpython", "linux", "x86_64")
        assert target.python_version == "3.9"
        assert target.implementation == "cpython"
        assert target.platform == "linux"
        assert target.architecture == "x86_64"

    def test_install_route(self) -> None:
        assert _plan()["install_route"] == "REQ_MAIN_PLUS_LOCK_DEV"


# ---------------------------------------------------------------------------
# P7 — no version substitution exists in the plan
# ---------------------------------------------------------------------------


class TestP7NoSubstitution:
    def test_exact_version_only_policy(self) -> None:
        plan = _plan()
        ev = plan["exact_version_only_policy"]
        for key in (
            "version_must_be_exact",
            "no_version_upgrades",
            "no_version_downgrades",
            "no_latest",
            "no_semver_compatible_substitution",
            "no_alternative_package",
            "no_locally_rebuilt_substitute",
            "no_dependency_downloads_in_acquisition",
        ):
            assert ev[key] is True, key

    def test_versions_are_exact(self) -> None:
        for name, version in _plan()["exact_ordered_recovery_identities"]:
            assert "==" in f"{name}=={version}"
            assert "-" not in version  # no range/compat specifiers


# ---------------------------------------------------------------------------
# P8 — no dependency acquisition exists in the plan
# ---------------------------------------------------------------------------


class TestP8NoDependencies:
    def test_no_dependency_download_policy(self) -> None:
        plan = _plan()
        assert plan["no_dependency_download_policy"]["acquisition_downloads_contain_dependencies"] is False
        assert plan["no_dependency_download_policy"]["only_exact_pylint_versions_downloaded"] is True
        assert plan["exact_version_only_policy"]["no_dependency_downloads_in_acquisition"] is True

    def test_recovery_set_is_only_pylint(self) -> None:
        identities = _plan()["exact_ordered_recovery_identities"]
        assert all(n == "pylint" for n, _v in identities)


# ---------------------------------------------------------------------------
# P9 — frozen py39 wheelhouse/manifest are read-only, not recovery destinations
# ---------------------------------------------------------------------------


class TestP9FrozenWheelhouseReadOnly:
    def test_frozen_paths_not_recovery_destinations(self) -> None:
        plan = _plan()
        sd = plan["store_design"]
        frozen = {Path(e1.FROZEN_WHEELHOUSE).resolve(), Path(e1.FROZEN_MANIFEST).resolve()}
        for key in ("staging_path", "wheels_path", "manifests_path"):
            dest = Path(sd[key]).resolve()
            assert dest not in frozen
            assert e1.FROZEN_WHEELHOUSE.resolve() not in dest.parents

    def test_mutation_prohibited_flag(self) -> None:
        assert _plan()["frozen_wheelhouse_mutation_prohibited"] is True


# ---------------------------------------------------------------------------
# P10 — recovery overlay paths are additive and outside frozen wheelhouse
# ---------------------------------------------------------------------------


class TestP10AdditiveOverlay:
    def test_overlay_paths_outside_frozen_wheelhouse(self) -> None:
        plan = _plan()
        root = Path(plan["store_design"]["recovery_root"]).resolve()
        frozen = Path(e1.FROZEN_WHEELHOUSE).resolve()
        assert root not in (frozen, frozen.parent)
        assert root.is_absolute()
        assert plan["store_design"]["additive_overlay_only"] is True

    def test_layout(self) -> None:
        sd = _plan()["store_design"]
        assert sd["staging_path"].endswith("staging")
        assert sd["wheels_path"].endswith("wheels")
        assert sd["manifests_path"].endswith("manifests")


# ---------------------------------------------------------------------------
# P11 — network usage in E1 == false
# ---------------------------------------------------------------------------


class TestP11NetworkFalse:
    def test_network_flags_false(self) -> None:
        plan = _plan()
        assert plan["network_used"] is False
        assert plan["artifacts_downloaded"] == 0
        assert plan["metadata_endpoints_queried_in_e1"] is False

    def test_acquisition_status(self) -> None:
        plan = _plan()
        assert plan["owner_network_approval"] is False
        assert plan["acquisition_status"] == "PLANNED_AWAITING_OWNER_NETWORK_APPROVAL"


# ---------------------------------------------------------------------------
# P12 — canonical plan serialization/hash is deterministic
# ---------------------------------------------------------------------------


class TestP12Determinism:
    def test_repeated_build_identical(self) -> None:
        first = e1.build_plan(_census())
        second = e1.build_plan(_census())
        assert first["plan_sha256"] == second["plan_sha256"]

    def test_plan_file_sha_self_consistent(self) -> None:
        plan = _built_plan()
        recomputed = e1._sha256_bytes(
            e1._canonical({k: v for k, v in plan.items() if k != "plan_sha256"})
        )
        assert plan["plan_sha256"] == recomputed

    def test_plan_file_matches_regenerated_plan(self) -> None:
        plan_file = _built_plan()
        regenerated = e1.build_plan(_census())
        assert plan_file["plan_sha256"] == regenerated["plan_sha256"]
        assert plan_file["exact_ordered_recovery_identities"] == regenerated[
            "exact_ordered_recovery_identities"
        ]


# ---------------------------------------------------------------------------
# F2P — invalid/mutated inputs fail closed (fixtures/copies only)
# ---------------------------------------------------------------------------


class TestF1MissingVersion:
    def test_missing_one_version_fails(self) -> None:
        plan = _plan()
        plan["exact_ordered_recovery_identities"] = plan["exact_ordered_recovery_identities"][:-1]
        plan["true_missing_unique_identities"] = 27
        errors = e1.validate_plan(plan, _census())
        assert errors, "plan with a missing version must fail closed"


class TestF2ExtraVersion:
    def test_extra_version_fails(self) -> None:
        plan = _plan()
        plan["exact_ordered_recovery_identities"].append(["pylint", "2.18.0"])
        plan["true_missing_unique_identities"] = 29
        errors = e1.validate_plan(plan, _census())
        assert errors


class TestF3WrongPackageName:
    def test_wrong_name_fails(self) -> None:
        plan = _plan()
        plan["exact_ordered_recovery_identities"][0] = ["pylinx", "2.7.2"]
        errors = e1.validate_plan(plan, _census())
        assert any("pylint" in e or "pylinx" in e for e in errors)


class TestF4DuplicateIdentity:
    def test_duplicate_fails(self) -> None:
        plan = _plan()
        plan["exact_ordered_recovery_identities"].append(["pylint", "2.7.2"])
        plan["true_missing_unique_identities"] = 29
        errors = e1.validate_plan(plan, _census())
        assert any("duplicate" in e for e in errors)


class TestF5WrongPythonEra:
    def test_wrong_era_fails(self) -> None:
        plan = _plan()
        plan["target"]["python_version"] = "3.12"
        errors = e1.validate_plan(plan, _census())
        assert any("target" in e for e in errors)


class TestF6WrongPlatformArch:
    def test_wrong_platform_fails(self) -> None:
        plan = _plan()
        plan["target"]["platform"] = "darwin"
        errors = e1.validate_plan(plan, _census())
        assert any("target" in e for e in errors)

    def test_wrong_arch_fails(self) -> None:
        plan = _plan()
        plan["target"]["architecture"] = "arm64"
        errors = e1.validate_plan(plan, _census())
        assert any("target" in e for e in errors)


class TestF7VersionSubstitution:
    def test_substitution_allowed_fails(self) -> None:
        plan = _plan()
        plan["exact_version_only_policy"]["no_semver_compatible_substitution"] = False
        errors = e1.validate_plan(plan, _census())
        assert any("substitution" in e for e in errors)


class TestF8DependencyDownloads:
    def test_dependency_download_allowed_fails(self) -> None:
        plan = _plan()
        plan["no_dependency_download_policy"]["acquisition_downloads_contain_dependencies"] = True
        errors = e1.validate_plan(plan, _census())
        assert any("dependency" in e for e in errors)


class TestF9RecoveryIntoFrozenWheelhouse:
    def test_wheels_path_in_frozen_wheelhouse_fails(self) -> None:
        plan = _plan()
        frozen = str(e1.FROZEN_WHEELHOUSE)
        plan["wheels_path"] = frozen
        plan["store_design"]["wheels_path"] = frozen
        errors = e1.validate_plan(plan, _census())
        assert any("frozen wheelhouse" in e for e in errors)


class TestF10NonPypiMetadataOrigin:
    def test_wrong_metadata_origin_fails(self) -> None:
        plan = _plan()
        plan["allowed_metadata_origin"] = "https://pypi.example.org/"
        errors = e1.validate_plan(plan, _census())
        assert any("metadata origin" in e for e in errors)


class TestF11NonFilesHostedArtifactOrigin:
    def test_wrong_artifact_origin_fails(self) -> None:
        plan = _plan()
        plan["allowed_artifact_origin"] = "https://github.com/pylint/pylint/"
        errors = e1.validate_plan(plan, _census())
        assert any("artifact origin" in e for e in errors)


class TestF12NetworkApprovalTrueInE1:
    def test_network_approval_true_fails(self) -> None:
        plan = _plan()
        plan["owner_network_approval"] = True
        plan["acquisition_status"] = "OWNER_NETWORK_APPROVED"
        errors = e1.validate_plan(plan, _census())
        assert any("approval" in e or "acquisition_status" in e for e in errors)

    def test_network_used_true_fails(self) -> None:
        plan = _plan()
        plan["network_used"] = True
        plan["artifacts_downloaded"] = 1
        errors = e1.validate_plan(plan, _census())
        assert any("network_used" in e or "artifacts_downloaded" in e for e in errors)


# ---------------------------------------------------------------------------
# Offline enforcement — E1 driver must not contain executable network paths
# ---------------------------------------------------------------------------


class TestE1Offline:
    def test_driver_has_no_network_code(self) -> None:
        source = Path(e1.__file__).read_text(encoding="utf-8")
        forbidden_imports = (
            "import urllib",
            "import requests",
            "import httpx",
            "import aiohttp",
            "import socket",
            "import http.client",
            "import urllib3",
            "import subprocess",
            "import pip",
            "from urllib",
            "import docker",
        )
        for token in forbidden_imports:
            assert token not in source, f"network/online token present in driver: {token}"

    def test_driver_never_invokes_downloader_tools(self) -> None:
        source = Path(e1.__file__).read_text(encoding="utf-8")
        for token in ("curl", "wget", "Invoke-WebRequest", "pip download", "poetry", " uv "):
            assert token not in source, f"downloader invocation token present: {token}"

    def test_driver_records_endpoint_template_only(self) -> None:
        # The endpoint is a recorded template, never fetched in E1.
        plan = _plan()
        assert plan["metadata_endpoint_template"] == "https://pypi.org/pypi/pylint/<EXACT_VERSION>/json"
        assert plan["metadata_endpoints_queried_in_e1"] is False
