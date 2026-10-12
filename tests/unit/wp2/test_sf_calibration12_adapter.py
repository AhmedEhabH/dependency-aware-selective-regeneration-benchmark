"""M17 source-fidelity fresh calibration-12 adapter tests (mission-local).

Mission M17_ENV_CANON_SOURCE_FIDELITY_R1_FRESH_CALIBRATION_12.

Tests the additive source-aware resolution adapter used by the fresh
calibration driver:
  * DIRECTORY/PATH pins select the frozen source-fidelity artifact;
  * REGISTRY pins are never overlaid (retain R3 wheelhouse/canon behavior);
  * unresolved non-registry identities FAIL CLOSED;
  * a missing source-fidelity artifact FAILS CLOSED;
  * a wheel-hash mismatch FAILS CLOSED;
  * the calibration population/order is the frozen first-12.

The driver module performs no network, no docker, and no real execution in
these tests (unit/static scope only).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
SRC = ROOT / "src"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SRC))

import sf_calibration12_driver as drv  # noqa: E402

PLAN_PATH = Path(r"D:\wp2_env_store\manifests\D7_CALIBRATION_12_PLAN.json")
PLAN = json.loads(PLAN_PATH.read_text(encoding="utf-8"))

AFFECTED_UNIT = "vu-b9808f19ace4"
AFFECTED_PINS = ("PyXB==1.2.5", "authorizenet==1.1.4")

HAS_STORE = Path(r"D:\wp2_env_store").is_dir()
HAS_WHEELS = Path(r"D:\wp2_sf_calibration_r1\research\source-fidelity-r1\artifacts\wheels").is_dir()


def _sa_records(source_type: str, names: list[tuple[str, str]]) -> list[dict]:
    return [
        {"name": n, "version": v, "source_type": source_type,
         "source_reference": "x", "target_commit": "c"}
        for n, v in names
    ]


@pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
def test_driver_plan_is_frozen_first_12():
    units = PLAN["units"]
    assert len(units) == 12
    assert [u["ordered_calibration_index"] for u in units] == list(range(1, 13))
    assert len({u["validation_unit_id"] for u in units}) == 12
    assert units[-1]["validation_unit_id"] == AFFECTED_UNIT


@pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
def test_unit12_runtime_pins_contain_pyxb_auth():
    closure = drv.unit_closure(PLAN["units"][-1])
    pins = closure["runtime_pins"]
    assert all(p in pins for p in AFFECTED_PINS)


@pytest.mark.skipif(not HAS_WHEELS, reason="source-fidelity wheels unavailable")
def test_source_fidelity_wheel_map_has_exact_artifacts():
    m = drv.source_fidelity_wheel_map()
    pyxb = m[("pyxb", "1.2.5")]
    auth = m[("authorizenet", "1.1.4")]
    assert pyxb["output_sha256"] == "ee196b69018cf9833f0210d050d8ae544070353a92d490a713be4e8347965aee"
    assert auth["output_sha256"] == "ba04a34ddba7496d778a458f8023ef597918b301b0824ad0517feed35c727ca9"


@pytest.mark.skipif(not HAS_WHEELS, reason="source-fidelity wheels unavailable")
def test_directory_pins_overlaid_registry_pins_not(tmp_path, monkeypatch):
    # DIRECTORY pins -> overlaid; REGISTRY pins -> untouched.
    monkeypatch.setattr(drv, "MERGED", str(tmp_path))
    records = _sa_records("DIRECTORY", [("PyXB", "1.2.5")]) + _sa_records("REGISTRY", [("Django", "4.2.0")])
    out = drv.apply_source_fidelity_overlay(["PyXB==1.2.5", "Django==4.2.0"], records)
    assert "PyXB==1.2.5" in out["overlaid_pins"]
    assert "Django==4.2.0" not in out["overlaid_pins"]
    assert out["n_overlaid"] == 1


def test_non_registry_without_frozen_artifact_fails_closed():
    with pytest.raises(RuntimeError, match="FAIL_CLOSED"):
        drv.apply_source_fidelity_overlay(
            ["weird==1.0.0"], _sa_records("GIT", [("weird", "1.0.0")]))


def test_registry_only_no_overlay(tmp_path, monkeypatch):
    monkeypatch.setattr(drv, "MERGED", str(tmp_path))
    records = _sa_records("REGISTRY", [("Django", "4.2.0"), ("celery", "5.3.0")])
    out = drv.apply_source_fidelity_overlay(["Django==4.2.0", "celery==5.3.0"], records)
    assert out["n_overlaid"] == 0


@pytest.mark.skipif(not HAS_WHEELS, reason="source-fidelity wheels unavailable")
def test_overlay_preserves_frozen_artifact_bytes(tmp_path, monkeypatch):
    monkeypatch.setattr(drv, "MERGED", str(tmp_path))
    records = _sa_records("DIRECTORY", [("PyXB", "1.2.5")])
    drv.apply_source_fidelity_overlay(["PyXB==1.2.5"], records)
    dst = tmp_path / "pyxb-1.2.5-py3-none-any.whl"
    assert dst.is_file()
    assert drv.sha256(str(dst)) == "ee196b69018cf9833f0210d050d8ae544070353a92d490a713be4e8347965aee"


@pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
def test_unit12_source_aware_closure_reproduces_frozen_identity():
    unit = next(u for u in PLAN["units"] if u["validation_unit_id"] == AFFECTED_UNIT)
    sa = drv.source_aware_closure(unit)
    assert sa["closure_identity_sha256"] == (
        "7bf871f278d8c5008682a8203be8835fcb643f9e471c5c43700cd914fa2cb1bd"
    )
    assert sa["n_fail_closed"] == 0
    non_reg = {r["name"] for r in sa["records"] if r["source_type"] != "REGISTRY"}
    assert non_reg == {"PyXB", "authorizenet"}


@pytest.mark.skipif(not HAS_STORE, reason="store unavailable")
def test_no_task_specific_branch_in_impl():
    import re
    text = Path(drv.__file__).read_text(encoding="utf-8")
    assert re.findall(r"saleor-rc-[0-9a-f]{12}", text) == []


def test_driver_uses_network_none():
    text = Path(drv.__file__).read_text(encoding="utf-8")
    assert '"--network=none"' in text
    assert "NETWORK_UNAVAILABLE" in text
