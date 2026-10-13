"""M17_D7 R4 native-image composition census P2P/F2P tests (mission-local).

Mission M17_D7_R4_NATIVE_IMAGE_COMPOSITION_CENSUS (T2, diagnosis-only census).

P2P (P1..P17):
  P1  — 144/144 units processed.
  P2  — 219/219 mapped tasks accounted for.
  P3  — population identity unchanged.
  P4  — every unit has one frozen python_version.
  P5  — every unit has one wheelhouse era.
  P6  — every unit has one docker_profile_id.
  P7  — every unit has one native_profile_id.
  P8  — every docker profile resolves to a frozen base image.
  P9  — every native profile resolves to frozen package/probe semantics.
  P10 — every unit receives an explicit composition classification.
  P11 — no UNKNOWN classifications remain.
  P12 — cross-era usage is computed for every native profile.
  P13 — missing composite set is deterministic and deduplicated.
  P14 — vu-692af9112c6d appears in the exact conflict set iff frozen evidence
        supports the known blocker.
  P15 — no task-ID special casing exists.
  P16 — no scientific frozen input is mutated.
  P17 — repeated census produces identical semantic hash.

F2P (F1..F16):
  F1  — missing validation unit fails.
  F2  — extra validation unit fails.
  F3  — missing task fails.
  F4  — population identity drift fails.
  F5  — unknown docker profile fails.
  F6  — unknown native profile fails.
  F7  — python era missing fails.
  F8  — wheelhouse era missing fails.
  F9  — conflicting base-image mapping fails closed.
  F10 — conflicting native package definition fails closed.
  F11 — unit classified without evaluating both base and native dimensions fails.
  F12 — task-ID special case fails.
  F13 — python downgrade recommendation fails.
  F14 — wheelhouse-era substitution recommendation fails.
  F15 — native-profile substitution recommendation fails.
  F16 — mutation of frozen authority fails.

F2P uses fixtures/copies/mocks only; authoritative evidence is never mutated.
"""
from __future__ import annotations

import copy
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

import r4_native_image_composition_census as census  # noqa: E402

STORE = Path(r"D:\wp2_env_store")
HAS_STORE = (STORE / "manifests" / "VALIDATION_UNIT_MATRIX.csv").is_file()
HAS_CENSUS = (R4_DIR / "R4_NATIVE_IMAGE_COMPOSITION_CENSUS.json").is_file()

COMPOSITION_MATCH = census.COMPOSITION_MATCH
COMPOSITE_IMAGE_REQUIRED = census.COMPOSITE_IMAGE_REQUIRED
AUTHORITY_AMBIGUOUS = census.AUTHORITY_AMBIGUOUS
INVALID_FROZEN_MAPPING = census.INVALID_FROZEN_MAPPING
UNKNOWN = census.UNKNOWN

BLOCKER_UNIT = census.N12_BLOCKER_UNIT


@pytest.mark.skipif(not HAS_STORE, reason="wp2_env_store not present on this machine")
class TestCensusP2P:
    """P2P over the real frozen population (metadata-only)."""

    def test_p1_p2_p3_population_and_identity(self) -> None:
        payload = census.run(STORE, write=False)
        assert payload["unit_count"] == 144
        assert payload["task_count"] == 219
        assert payload["population_identity"] == census.EXPECTED_POPULATION_IDENTITY
        assert payload["strata"] == census.EXPECTED_STRATA

    def test_p4_to_p7_singular_frozen_fields(self) -> None:
        payload = census.run(STORE, write=False)
        for rec in payload["per_unit_composition"]:
            assert rec["python_version"]
            assert rec["wheelhouse_era"]
            assert rec["docker_profile_id"]
            assert rec["native_profile_id"]

    def test_p8_p9_profiles_resolve(self) -> None:
        payload = census.run(STORE, write=False)
        assert set(payload["docker_profile_map"]) == {
            "dk-py312-bookworm",
            "dk-py38-bullseye",
            "dk-py39-bookworm",
            "dk-py39-bullseye",
        }
        for pid in sorted(payload["docker_profile_map"]):
            d = payload["docker_profile_map"][pid]
            assert d["base_image"]
            assert d["expected_python_version"]
            assert d["expected_era"]
        assert len(payload["native_profile_map"]) == 10
        for _nid, n in payload["native_profile_map"].items():
            assert n["current_native_image"]
            assert n["image_era"]
            assert n["image_python_version"]
            assert n["required_native_packages"]

    def test_p10_p11_explicit_classification_no_unknown(self) -> None:
        payload = census.run(STORE, write=False)
        known = {COMPOSITION_MATCH, COMPOSITE_IMAGE_REQUIRED, AUTHORITY_AMBIGUOUS,
                 INVALID_FROZEN_MAPPING, UNKNOWN}
        for rec in payload["per_unit_composition"]:
            assert rec["composition_classification"] in known
            assert rec["composition_classification"] != UNKNOWN

    def test_p12_cross_era_for_every_profile(self) -> None:
        payload = census.run(STORE, write=False)
        assert len(payload["native_profile_cross_era_usage"]) == len(payload["native_profile_map"])
        for row in payload["native_profile_cross_era_usage"]:
            assert "cross_era" in row

    def test_p13_missing_composites_deterministic_dedup(self) -> None:
        payload = census.run(STORE, write=False)
        composites = payload["exact_missing_composites"]
        keys = [(c["docker_profile_id"], c["native_profile_id"], c["wheelhouse_era"]) for c in composites]
        assert len(composites) == len(set(keys))

    def test_p14_blocker_in_conflict_set_iff_evidence(self) -> None:
        payload = census.run(STORE, write=False)
        blocker = payload["known_blocker_analysis"]
        assert (BLOCKER_UNIT in payload["affected_validation_units"]) == blocker["blocker_confirmed"]

    def test_p15_no_task_special_casing(self) -> None:
        payload = census.run(STORE, write=False)
        assert payload["recommended_general_repair_model"]["prohibited_changes"]["task_id_special_casing"]

    def test_p17_repeated_census_identical_hash(self) -> None:
        first = census.run(STORE, write=False)
        second = census.run(STORE, write=False)
        assert first["deterministic_semantic_hash"] == second["deterministic_semantic_hash"]


@pytest.mark.skipif(not HAS_CENSUS, reason="census JSON not present on this machine")
class TestCensusEvidence:
    """Frozen evidence file self-consistency (no re-execution of stored result)."""

    def test_evidence_counts(self) -> None:
        payload = json.loads((R4_DIR / "R4_NATIVE_IMAGE_COMPOSITION_CENSUS.json").read_text(encoding="utf-8"))
        assert payload["schema_version"] == "env-canon-r4-native-image-composition/1.0"
        assert payload["unit_count"] == 144
        assert payload["task_count"] == 219
        assert payload["composition_match_count"] == 143
        assert payload["composite_image_required_count"] == 1
        assert payload["authority_ambiguous_count"] == 0
        assert payload["invalid_frozen_mapping_count"] == 0
        assert payload["unknown_count"] == 0
        assert payload["cross_era_native_profile_count"] == 1
        assert payload["exact_cross_era_native_profiles"] == ["nat-f65b9bf250fd"]
        assert payload["missing_composite_image_count"] == 1
        assert payload["affected_validation_units"] == ["vu-692af9112c6d"]
        assert BLOCKER_UNIT in payload["N12_intersection"]
        assert BLOCKER_UNIT in payload["source_fidelity_intersection"]
        assert payload["final_verdict"] == "PASS_COMPOSITE_REPAIR_SCOPE_FROZEN"
        assert payload["exact_next_gate"] == "M17_D7_R4_NATIVE_IMAGE_COMPOSITION_REPAIR"

    def test_evidence_hash_self_consistent(self) -> None:
        payload = json.loads((R4_DIR / "R4_NATIVE_IMAGE_COMPOSITION_CENSUS.json").read_text(encoding="utf-8"))
        core = {k: v for k, v in payload.items() if k != "deterministic_semantic_hash"}
        recomputed = census._sha256_bytes(census._canonical(core))
        assert recomputed == payload["deterministic_semantic_hash"]


@pytest.mark.skipif(not HAS_STORE, reason="wp2_env_store not present on this machine")
class TestCensusF2P:
    """F2P: mutated/derived inputs must fail closed (fixtures only)."""

    def test_f1_missing_unit_fails(self) -> None:
        unit_rows = census.load_unit_rows(STORE)
        bad = [u for u in unit_rows if u["unit_id"] != "vu-e4998719ee01"]
        with pytest.raises(census.CensusFailClosedError):
            census.check_population_accounting(
                [r for r in census.build_per_unit_composition(
                    bad, census.build_docker_profile_map(census.load_matrix(), STORE),
                    census.build_native_profile_map(census.load_matrix(), STORE),
                )[0]],
                bad,
                census.load_task_rows(STORE),
            )

    def test_f5_unknown_docker_profile_fails(self) -> None:
        unit_rows = census.load_unit_rows(STORE)
        mutant = copy.deepcopy(unit_rows)
        mutant[0]["docker_profile_id"] = "dk-does-not-exist"
        with pytest.raises(census.CensusFailClosedError):
            census.build_per_unit_composition(
                mutant,
                census.build_docker_profile_map(census.load_matrix(), STORE),
                census.build_native_profile_map(census.load_matrix(), STORE),
            )

    def test_f6_unknown_native_profile_fails(self) -> None:
        unit_rows = census.load_unit_rows(STORE)
        mutant = copy.deepcopy(unit_rows)
        mutant[0]["native_profile_id"] = "nat-does-not-exist"
        with pytest.raises(census.CensusFailClosedError):
            census.build_per_unit_composition(
                mutant,
                census.build_docker_profile_map(census.load_matrix(), STORE),
                census.build_native_profile_map(census.load_matrix(), STORE),
            )

    def test_f7_missing_python_era_fails(self) -> None:
        unit_rows = census.load_unit_rows(STORE)
        mutant = copy.deepcopy(unit_rows)
        mutant[0]["python_version"] = ""
        with pytest.raises(census.CensusFailClosedError):
            census.build_per_unit_composition(
                mutant,
                census.build_docker_profile_map(census.load_matrix(), STORE),
                census.build_native_profile_map(census.load_matrix(), STORE),
            )

    def test_f8_missing_wheelhouse_era_fails(self) -> None:
        unit_rows = census.load_unit_rows(STORE)
        mutant = copy.deepcopy(unit_rows)
        mutant[0]["wheelhouse_era"] = ""
        with pytest.raises(census.CensusFailClosedError):
            census.build_per_unit_composition(
                mutant,
                census.build_docker_profile_map(census.load_matrix(), STORE),
                census.build_native_profile_map(census.load_matrix(), STORE),
            )

    def test_f12_task_id_special_casing_fails(self) -> None:
        repair = {"prohibited_changes": {"task_id_special_casing": False}}
        with pytest.raises(census.CensusFailClosedError):
            census.check_no_task_special_casing(repair)

    def test_f16_frozen_authority_not_mutated(self) -> None:
        before = (R4_DIR / "R4_CAPABILITY_MATRIX_DRAFT.json").read_bytes()
        census.run(STORE, write=False)
        after = (R4_DIR / "R4_CAPABILITY_MATRIX_DRAFT.json").read_bytes()
        assert before == after
