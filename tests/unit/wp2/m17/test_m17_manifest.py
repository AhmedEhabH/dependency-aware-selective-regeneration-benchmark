"""M17 K05 - kit manifest: verify-kit passes, fails on one-byte drift (zero network)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

P = Path(__file__).resolve().parents[4]
for _p in (P, P / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.wp2_ctl_v224 import verify_kit  # noqa: E402

MANIFEST = P / "controller/KIT_MANIFEST_M17.json"


def test_manifest_exists_and_pins_expected_members():
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files = m["files"]
    assert isinstance(files, dict) and len(files) >= 20
    required = {
        "scripts/wp2_m17_run.py",
        "scripts/wp2_m17_adapter.py",
        "controller/plan_m17_v1_qualification.json",
        "controller/plan_m17_v1_main.json",
        "research/wp2/m17_v1/m17_qualification_membership_v2_approved.json",
        "research/wp2/m17_v1/m17_m16_root_cause_map.json",
    }
    assert required <= set(files)


def test_manifest_records_governance_facts():
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert m["baseline"]["commit"] == "f7412ec0031a4585df9c4102a9e18607cf2d7db8"
    assert m["baseline"]["tag"] == "msc-research-baseline-2026-10-02"
    assert m["verified_frame_count"] == 220
    assert m["qualification_membership_sha256"] == (
        "75c13be8b44080407944291db8d7c2809e2ddd0fff8cc03ca6e80cfb9ded6cee")
    assert m["m15r_reference"]["result_tag"] == "wp2-m15r-v1-result-2026-10-01"
    assert m["m16_reference"]["status"] == "CLOSED_PRE_EXPERIMENT_IMMUTABLE"
    assert m["zero_model_policy"] is True
    assert any("scopes" in s for s in m["selector_firewall_paths"])
    assert any("opws" in s for s in m["selector_firewall_paths"])


def test_verify_kit_passes():
    assert verify_kit(P, MANIFEST) == []


def test_verify_kit_fails_on_one_byte_drift(tmp_path):
    # copy the manifest into a temp dir, mutate one pinned file there, verify fail
    import shutil

    root = tmp_path / "proj"
    (root / "controller").mkdir(parents=True)
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    # copy every pinned file
    for rel in m["files"]:
        src = P / rel
        if src.exists():
            dst = root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
    (root / "controller/KIT_MANIFEST_M17.json").write_text(
        json.dumps(m, indent=1), encoding="utf-8")
    # verify clean in the copy
    assert verify_kit(root, root / "controller/KIT_MANIFEST_M17.json") == []
    # mutate one byte of the adapter
    ad = root / "scripts/wp2_m17_adapter.py"
    data = ad.read_bytes()
    ad.write_bytes(data + b"\n")
    bad = verify_kit(root, root / "controller/KIT_MANIFEST_M17.json")
    assert any("modified" in b for b in bad)


def test_verify_kit_fails_on_missing_member(tmp_path):
    import json as _json

    root = tmp_path
    m = {"files": {"scripts/wp2_m17_run.py": "00" * 32}}
    (root / "controller").mkdir(parents=True)
    (root / "controller/KIT_MANIFEST_M17.json").write_text(_json.dumps(m), encoding="utf-8")
    bad = verify_kit(root, root / "controller/KIT_MANIFEST_M17.json")
    assert any("missing" in b for b in bad)
