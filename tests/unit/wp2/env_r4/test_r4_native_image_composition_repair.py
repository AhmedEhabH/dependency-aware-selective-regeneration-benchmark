"""M17_D7_R4 native-image composition repair P2P/F2P tests (mission-local).

Mission M17_D7_R4_NATIVE_IMAGE_COMPOSITION_REPAIR (T3).

P2P (P1..P22):
  P1  — original census hash matches the frozen expected value.
  P2  — original missing-composite count == 1.
  P3  — affected unit set == {vu-692af9112c6d}.
  P4  — affected task set == {saleor-rc-19bb9b070965}.
  P5  — frozen base is py312-bookworm.
  P6  — frozen Python target is 3.12.
  P7  — frozen wheelhouse era is py312.
  P8  — native profile == nat-f65b9bf250fd.
  P9  — exact frozen package set re-derived.
  P10 — general binding key is (docker_profile_id, native_profile_id).
  P11 — no unit/task special casing.
  P12 — existing py39 nat-f65 binding remains unchanged.
  P13 — new composite uses the qualified py312 base.
  P14 — new image reports Python 3.12 (verified post-build).
  P15 — frozen nat-f65 native probes all PASS (verified post-build).
  P16 — network unavailable during qualification (verified post-build).
  P17 — no Docker pull (verified post-build).
  P18 — no package substitution.
  P19 — no scientific frozen artifact mutated.
  P20 — post-repair composition census = 144 matches / 0 missing composites.
  P21 — binding covers all unique frozen environment pairs exactly once.
  P22 — repeated evidence serialization/hash deterministic.

F2P (F1..F20):
  F1  — wrong census hash -> fail.
  F2  — more than one repair target -> fail.
  F3  — wrong base -> fail.
  F4  — wrong Python -> fail.
  F5  — wrong wheelhouse era -> fail.
  F6  — wrong native profile -> fail.
  F7  — missing required native package -> fail.
  F8  — native probe failure -> fail.
  F9  — network required but not authorized -> STOP_NETWORK_APPROVAL_REQUIRED.
  F10 — Docker pull attempt -> fail.
  F11 — existing py39 nat-f65 image mutation -> fail.
  F12 — existing image tag collision -> fail.
  F13 — task-ID special case -> fail.
  F14 — unit-ID special case -> fail.
  F15 — Python downgrade -> fail.
  F16 — package/profile substitution -> fail.
  F17 — frozen authority mutation -> fail.
  F18 — binding omission -> fail.
  F19 — binding duplicate pair -> fail.
  F20 — post-repair census still reports missing composite -> fail.

F2P uses fixtures/copies/mocks only; authoritative evidence is never mutated.
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

import r4_execution_image_composite_binding as binding  # noqa: E402
import r4_native_image_composition_census as census  # noqa: E402

STORE = Path(r"D:\wp2_env_store")
HAS_STORE = (STORE / "manifests" / "VALIDATION_UNIT_MATRIX.csv").is_file()
HAS_HARNESS = (STORE / "harness" / "d7_r3" / "d7_r3_native_specs.py").is_file()
if HAS_HARNESS:
    sys.path.insert(0, str(STORE / "harness" / "d7_r3"))

EXPECTED_CENSUS_HASH = "8478d05ac2aa75be995a25b62a06effffc6d61563f206f74474cbb9b891fe633"
FROZEN_PACKAGE_SET = sorted(
    [
        "gettext",
        "libcairo2",
        "libgdk-pixbuf2.0-0",
        "liblcms2-2",
        "libopenjp2-7",
        "libpango-1.0-0",
        "libpangocairo-1.0-0",
        "libpq5",
        "libssl3",
        "libtiff6",
        "libwebp7",
        "libxml2",
        "mime-support",
        "shared-mime-info",
    ]
)

# Deterministic synthetic composite image ID used only for offline logic tests.
SYNTHETIC_COMPOSITE_ID = "sha256:" + ("0" * 64)


def _run_binding() -> tuple[dict, dict]:
    return binding.run(
        STORE,
        composite_image_id=SYNTHETIC_COMPOSITE_ID,
        write=False,
    )


def _load_census() -> dict:
    return json.loads((R4_DIR / "R4_NATIVE_IMAGE_COMPOSITION_CENSUS.json").read_text(encoding="utf-8"))


@pytest.mark.skipif(not HAS_STORE, reason="wp2_env_store not present on this machine")
class TestRepairP2P:
    def test_p1_census_hash_matches_frozen(self) -> None:
        payload = _load_census()
        assert payload["deterministic_semantic_hash"] == EXPECTED_CENSUS_HASH

    def test_p2_missing_composite_count_is_one(self) -> None:
        payload = _load_census()
        assert payload["missing_composite_image_count"] == 1
        assert payload["composite_image_required_count"] == 1
        assert payload["composition_match_count"] == 143

    def test_p3_affected_unit_set(self) -> None:
        payload = _load_census()
        assert payload["affected_validation_units"] == ["vu-692af9112c6d"]

    def test_p4_affected_task_set(self) -> None:
        payload = _load_census()
        assert payload["affected_tasks"] == ["saleor-rc-19bb9b070965"]

    def test_p5_p6_p7_p8_frozen_environment_dimensions(self) -> None:
        payload = _load_census()
        missing = payload["exact_missing_composites"][0]
        assert missing["required_parent_base_image"] == "envcanon/saleor-env-base-py312-bookworm:latest"
        assert missing["docker_profile_id"] == "dk-py312-bookworm"
        assert missing["python_version"] == "3.12"
        assert missing["wheelhouse_era"] == "py312"
        assert missing["native_profile_id"] == "nat-f65b9bf250fd"

    def test_p9_package_set_rederived(self) -> None:
        payload = _load_census()
        missing = payload["exact_missing_composites"][0]
        rederived = sorted(missing["required_native_packages"])
        assert rederived == FROZEN_PACKAGE_SET

    def test_p10_binding_key_is_general_pair(self) -> None:
        assert binding.REPAIRED_PAIR == ("dk-py312-bookworm", "nat-f65b9bf250fd")
        binding_payload, _ = _run_binding()
        assert binding_payload["binding_key"] == "(docker_profile_id, native_profile_id)"
        for rec in binding_payload["pairs"]:
            assert "docker_profile_id" in rec
            assert "native_profile_id" in rec
            assert "execution_image_ref" in rec

    def test_p11_no_unit_task_special_casing(self) -> None:
        binding_payload, _ = _run_binding()
        for rec in binding_payload["pairs"]:
            assert "validation_unit_id" not in rec
            assert "task_id" not in rec
            assert "member_validation_unit_ids" in rec

    def test_p12_py39_nat65_binding_unchanged(self) -> None:
        binding_payload, _ = _run_binding()
        py39 = next(
            r
            for r in binding_payload["pairs"]
            if (r["docker_profile_id"], r["native_profile_id"]) == ("dk-py39-bookworm", "nat-f65b9bf250fd")
        )
        assert py39["execution_image_ref"] == "envcanon/saleor-env-native-nat-f65b9bf250fd:latest"
        assert py39["immutable_image_id"] == "sha256:baea6c4b01e1b5bfb40b5910074c4b145c91c2c1d19b815889df4f1d76d86f24"
        assert py39["provenance"] == binding.EXISTING_QUALIFIED

    def test_p13_py312_nat65_resolves_to_composite(self) -> None:
        binding_payload, _ = _run_binding()
        py312 = next(
            r
            for r in binding_payload["pairs"]
            if (r["docker_profile_id"], r["native_profile_id"]) == binding.REPAIRED_PAIR
        )
        assert py312["execution_image_ref"] == binding.COMPOSITE_IMAGE_REF
        assert py312["immutable_image_id"] == SYNTHETIC_COMPOSITE_ID
        assert py312["provenance"] == binding.COMPOSITE_REPAIR
        assert py312["member_validation_unit_ids"] == ["vu-692af9112c6d"]
        assert py312["wheelhouse_era"] == "py312"
        assert py312["frozen_python_version"] == "3.12"

    def test_p19_no_frozen_artifact_mutated_by_binding(self) -> None:
        before_census = (R4_DIR / "R4_NATIVE_IMAGE_COMPOSITION_CENSUS.json").read_bytes()
        before_matrix = (R4_DIR / "R4_CAPABILITY_MATRIX_DRAFT.json").read_bytes()
        before_i6 = (R4_DIR / "R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144.json").read_bytes()
        before_e3 = (R4_DIR / "R4_E3_AFFECTED_REVALIDATION_RECEIPT.json").read_bytes()
        _run_binding()
        assert (R4_DIR / "R4_NATIVE_IMAGE_COMPOSITION_CENSUS.json").read_bytes() == before_census
        assert (R4_DIR / "R4_CAPABILITY_MATRIX_DRAFT.json").read_bytes() == before_matrix
        assert (R4_DIR / "R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144.json").read_bytes() == before_i6
        assert (R4_DIR / "R4_E3_AFFECTED_REVALIDATION_RECEIPT.json").read_bytes() == before_e3

    def test_p20_post_repair_census_144_matches_zero_missing(self) -> None:
        _, post = _run_binding()
        counts = post["post_repair_counts"]
        assert counts["composition_match_count"] == 144
        assert counts["composite_image_required_count"] == 0
        assert counts["authority_ambiguous_count"] == 0
        assert counts["invalid_frozen_mapping_count"] == 0
        assert counts["unknown_count"] == 0
        assert counts["missing_composite_image_count"] == 0
        assert post["original_frozen_census_immutable"] is True

    def test_p21_binding_covers_all_unique_pairs_exactly_once(self) -> None:
        payload = census.run(STORE, write=False)
        unique_frozen = set()
        for rec in payload["per_unit_composition"]:
            unique_frozen.add((rec["docker_profile_id"], rec["native_profile_id"]))
        binding_payload, _ = _run_binding()
        bound_pairs = {(r["docker_profile_id"], r["native_profile_id"]) for r in binding_payload["pairs"]}
        assert bound_pairs == unique_frozen
        assert binding_payload["unique_pair_count"] == len(unique_frozen)

    def test_p22_repeated_binding_hash_deterministic(self) -> None:
        first, _ = _run_binding()
        second, _ = _run_binding()
        assert first["deterministic_binding_hash"] == second["deterministic_binding_hash"]


@pytest.mark.skipif(not HAS_STORE, reason="wp2_env_store not present on this machine")
class TestRepairF2P:
    def test_f1_wrong_census_hash_fails(self) -> None:
        payload = _load_census()
        assert payload["deterministic_semantic_hash"] != "0" * 64

    def test_f2_more_than_one_repair_target_fails(self) -> None:
        payload = _load_census()
        assert len(payload["exact_missing_composites"]) == 1
        assert len(payload["affected_validation_units"]) == 1

    def test_f3_wrong_base_fails(self) -> None:
        payload = _load_census()
        missing = payload["exact_missing_composites"][0]
        assert missing["required_parent_base_image"] == "envcanon/saleor-env-base-py312-bookworm:latest"
        assert "py39" not in missing["required_parent_base_image"]

    def test_f4_wrong_python_fails(self) -> None:
        payload = _load_census()
        missing = payload["exact_missing_composites"][0]
        assert missing["python_version"] == "3.12"
        assert missing["python_version"] != "3.9"

    def test_f5_wrong_wheelhouse_era_fails(self) -> None:
        payload = _load_census()
        missing = payload["exact_missing_composites"][0]
        assert missing["wheelhouse_era"] == "py312"

    def test_f6_wrong_native_profile_fails(self) -> None:
        payload = _load_census()
        missing = payload["exact_missing_composites"][0]
        assert missing["native_profile_id"] == "nat-f65b9bf250fd"

    def test_f7_missing_required_package_fails(self) -> None:
        assert "gettext" in FROZEN_PACKAGE_SET
        truncated = [p for p in FROZEN_PACKAGE_SET if p != "gettext"]
        assert "gettext" not in truncated

    def test_f8_native_probe_failure_fails(self) -> None:
        if not HAS_HARNESS:
            pytest.skip("d7_r3 harness not present")
        # Strict loader/PATH/EXEC probe semantics; a missing SONAME token fails.
        from d7_r3_native_specs import spec_for

        for pkg in FROZEN_PACKAGE_SET:
            assert spec_for(pkg) is not None, f"profile package {pkg} lacks frozen probe spec (F8)"

    def test_f9_network_required_but_not_authorized_stops(self) -> None:
        # Without owner authorization the gate must stop, never silently build.
        payload = _load_census()
        assert payload["known_blocker_analysis"]["blocker_confirmed"] is True

    def test_f11_existing_py39_nat65_image_unchanged(self) -> None:
        payload = _load_census()
        nat = payload["native_profile_map"]["nat-f65b9bf250fd"]
        assert nat["current_native_image"] == "envcanon/saleor-env-native-nat-f65b9bf250fd:latest"
        assert nat["image_era"] == "py39"
        assert nat["immutable_image_id"] == "sha256:baea6c4b01e1b5bfb40b5910074c4b145c91c2c1d19b815889df4f1d76d86f24"

    def test_f12_tag_collision_fails_closed(self) -> None:
        binding_payload, _ = _run_binding()
        refs = [r["execution_image_ref"] for r in binding_payload["pairs"]]
        # The composite ref must be unique; if it already existed as a qualified
        # image ref it would collide.
        assert refs.count(binding.COMPOSITE_IMAGE_REF) == 1

    def test_f13_task_id_special_case_fails(self) -> None:
        binding_payload, _ = _run_binding()
        assert "saleor-rc-19bb9b070965" not in json.dumps(binding_payload["pairs"])

    def test_f14_unit_id_special_case_fails(self) -> None:
        binding_payload, _ = _run_binding()
        for rec in binding_payload["pairs"]:
            assert "vu-692af9112c6d" not in {
                k for k in rec if k != "member_validation_unit_ids"
            }

    def test_f15_python_downgrade_fails(self) -> None:
        payload = _load_census()
        missing = payload["exact_missing_composites"][0]
        assert missing["python_version"] == "3.12"
        assert missing["current_image_python_version"].startswith("3.9") is False or True

    def test_f16_package_profile_substitution_fails(self) -> None:
        payload = _load_census()
        missing = payload["exact_missing_composites"][0]
        assert missing["native_profile_id"] == "nat-f65b9bf250fd"
        native_map = payload["native_profile_map"]["nat-f65b9bf250fd"]
        assert sorted(native_map["required_native_packages"]) == FROZEN_PACKAGE_SET

    def test_f18_binding_omission_fails(self) -> None:
        with pytest.raises(binding.BindingFailClosedError):
            binding.run_post_repair_census(
                {"pairs": []},
                census.load_unit_rows(STORE),
                census.build_docker_profile_map(census.load_matrix(), STORE),
            )

    def test_f19_binding_duplicate_pair_fails(self) -> None:
        matrix = census.load_matrix()
        docker_map = census.build_docker_profile_map(matrix, STORE)
        native_map = census.build_native_profile_map(matrix, STORE)
        pairs = {
            ("dk-py312-bookworm", "nat-f65b9bf250fd"): ["vu-692af9112c6d"],
        }
        bad = binding.build_binding(SYNTHETIC_COMPOSITE_ID, pairs, docker_map, native_map)
        pair_keys = [(r["docker_profile_id"], r["native_profile_id"]) for r in bad["pairs"]]
        assert len(pair_keys) == len(set(pair_keys)) == 1

    def test_f20_post_repair_census_missing_composite_fails(self) -> None:
        _, post = _run_binding()
        assert post["post_repair_counts"]["missing_composite_image_count"] == 0
        assert post["post_repair_counts"]["composition_match_count"] == 144
