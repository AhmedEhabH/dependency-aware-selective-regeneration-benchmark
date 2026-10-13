"""M17_D7_R4_RUNTIME_TOOLHOUSE_CLEAN — successor binding tests (offline).

Mission M17_D7_R4_RUNTIME_TOOLHOUSE_CLEAN (bounded environment repair).

Verifies the additive runtime-toolhouse-clean successor binding:
- key remains (docker_profile_id, native_profile_id);
- clean bindings retain their existing qualified image ID;
- only the four proven contaminated py38/py39 bindings map to successors;
- no unit-ID / task-ID special cases;
- deterministic semantic hash; 144/144 accounting; N12 readiness.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = ROOT / "scripts"
R4_DIR = ROOT / "research" / "env-canon-r4"
sys.path.insert(0, str(SCRIPTS))

import r4_runtime_toolhouse_clean as clean  # noqa: E402

PARENT = json.loads((R4_DIR / "R4_EXECUTION_IMAGE_COMPOSITE_BINDING.json").read_text(encoding="utf-8"))
SUCC = json.loads((R4_DIR / "R4_EXECUTION_IMAGE_BINDING_RUNTIME_CLEAN.json").read_text(encoding="utf-8"))
PLAN = json.loads((R4_DIR / "R4_STRATIFIED_CALIBRATION_PLAN_DRAFT.json").read_text(encoding="utf-8"))

SUCCESSOR_PROVENANCE = "R4_RUNTIME_TOOLHOUSE_CLEAN"


def test_successor_binding_hash_self_consistent() -> None:
    core = {k: v for k, v in SUCC.items() if k != "deterministic_binding_hash"}
    assert SUCC["deterministic_binding_hash"] == clean._sha256_bytes(clean._canonical(core))


def test_build_is_deterministic() -> None:
    a = clean.build_successor_binding(PARENT)
    b = clean.build_successor_binding(PARENT)
    assert a["deterministic_binding_hash"] == b["deterministic_binding_hash"]


def test_pair_count_and_accounting() -> None:
    assert SUCC["unique_pair_count"] == 11
    keys = [(r["docker_profile_id"], r["native_profile_id"]) for r in SUCC["pairs"]]
    assert len(keys) == len(set(keys)) == 11
    assert sum(r["affected_unit_count"] for r in SUCC["pairs"]) == 144
    acct = clean.verify_accounting(SUCC)
    assert acct["units_resolved"] == 144
    assert acct["no_missing"] and acct["no_duplicate"] and acct["no_ambiguity"] and acct["no_fallback"]


def test_exactly_four_successors_py38_py39() -> None:
    succs = [r for r in SUCC["pairs"] if r["provenance"] == SUCCESSOR_PROVENANCE]
    assert len(succs) == 4
    for r in succs:
        assert r["frozen_python_version"] in ("3.8", "3.9")
        assert r["removed_toolhouse_dists"] == ["wheel"]
        assert "-runtimeclean:r4-toolhouse-clean-20261014" in r["execution_image_ref"]
        assert r["execution_image_ref"] != r["parent_image_ref"]
        assert r["immutable_image_id"] != r["parent_image_id"]


def test_clean_bindings_retain_existing_ids() -> None:
    parent_by_pair = {(r["docker_profile_id"], r["native_profile_id"]): r for r in PARENT["pairs"]}
    for r in SUCC["pairs"]:
        if r["provenance"] == SUCCESSOR_PROVENANCE:
            continue
        p = parent_by_pair[(r["docker_profile_id"], r["native_profile_id"])]
        assert r["execution_image_ref"] == p["execution_image_ref"]
        assert r["immutable_image_id"] == p["immutable_image_id"]


def test_no_unit_or_task_special_casing() -> None:
    # Resolution is by (docker_profile_id, native_profile_id) only. The
    # member_validation_unit_ids list is inherited accounting, not a selector.
    resolution_fields = [
        {k: v for k, v in r.items() if k != "member_validation_unit_ids"}
        for r in SUCC["pairs"]
    ]
    joined = json.dumps(resolution_fields)
    assert "vu-" not in joined
    assert "saleor-rc-" not in joined


def test_n12_readiness_resolution() -> None:
    by_pair = {(r["docker_profile_id"], r["native_profile_id"]): r for r in SUCC["pairs"]}
    composite = "envcanon/saleor-env-native-nat-f65b9bf250fd-py312-bookworm:r4-composite-20261013"
    order = [c["validation_unit_id"] for c in PLAN["calibration_units"]]
    assert order[0] == "vu-b9808f19ace4"
    assert order[8] == "vu-eda4e9f82401"
    # unit 2 (repaired composite, py312)
    u2 = next(c for c in PLAN["calibration_units"] if c["validation_unit_id"] == "vu-692af9112c6d")
    assert by_pair[(u2["docker_profile_id"], u2["native_profile_id"])]["execution_image_ref"] == composite
    # unit 9 (py38) -> clean successor
    u9 = next(c for c in PLAN["calibration_units"] if c["validation_unit_id"] == "vu-eda4e9f82401")
    r9 = by_pair[(u9["docker_profile_id"], u9["native_profile_id"])]
    assert r9["provenance"] == SUCCESSOR_PROVENANCE
    # units 10-12 (py39) -> clean successors
    for uid in ("vu-457f26c93ff1", "vu-ffe68ddec229", "vu-0e0ef31c7634"):
        u = next(c for c in PLAN["calibration_units"] if c["validation_unit_id"] == uid)
        r = by_pair[(u["docker_profile_id"], u["native_profile_id"])]
        assert r["provenance"] == SUCCESSOR_PROVENANCE
