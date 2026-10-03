"""M17 K02 - fail-closed historical-schema reader + dev-group/mechanism fail-closed (zero network)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

P = Path(__file__).resolve().parents[4]
for _p in (P, P / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts import wp2_m17_adapter as ad  # noqa: E402


def _eng_line(task_id: str, *, manifest: dict | None = None, status: str = "DONE") -> dict:
    m = {"install_mode": "LOCK_EXACT_MAIN_PLUS_DEV", "lockfile_sha256": "aa"}
    if manifest is not None:
        m = dict(manifest)
    return {"task_id": task_id, "target_commit": "a" * 40, "status": status, "manifest": m}


def _write_eng(monkeypatch, tmp_path, records: list[dict]) -> None:
    p = tmp_path / "eng.jsonl"
    p.write_text("".join(ad.canon(r) + "\n" for r in records), encoding="utf-8")
    monkeypatch.setattr(ad, "PHASE5_ENG_V3_REL", p)


# ------------------------------------------------------------------ fail-closed schema (the reader itself must raise)
def test_missing_task_id_fails_closed(monkeypatch, tmp_path):
    _write_eng(monkeypatch, tmp_path, [{**_eng_line("x"), "task_id": ""}])
    with pytest.raises(ad.AdapterError):
        ad.read_frozen_eng(P)


def test_missing_target_commit_fails_closed(monkeypatch, tmp_path):
    rec = _eng_line("saleor-rc-x")
    rec["target_commit"] = ""
    _write_eng(monkeypatch, tmp_path, [rec])
    with pytest.raises(ad.AdapterError):
        ad.read_frozen_eng(P)


def test_missing_install_mode_fails_closed(monkeypatch, tmp_path):
    _write_eng(monkeypatch, tmp_path, [_eng_line("saleor-rc-x", manifest={"lockfile_sha256": "aa"})])
    with pytest.raises(ad.AdapterError):
        ad.read_frozen_eng(P)


def test_missing_lockfile_fails_closed(monkeypatch, tmp_path):
    _write_eng(monkeypatch, tmp_path, [_eng_line("saleor-rc-x", manifest={"install_mode": "x"})])
    with pytest.raises(ad.AdapterError):
        ad.read_frozen_eng(P)


def test_duplicate_task_id_fails_closed(monkeypatch, tmp_path):
    _write_eng(monkeypatch, tmp_path, [_eng_line("saleor-rc-x"), _eng_line("saleor-rc-x")])
    with pytest.raises(ad.AdapterError):
        ad.read_frozen_eng(P)


def test_unknown_closure_key_shape_fails_closed(monkeypatch, tmp_path):
    _write_eng(monkeypatch, tmp_path, [
        _eng_line("saleor-rc-x", manifest={"install_mode": "x", "lockfile_sha256": "y",
                                           "dev_test_closure": [1, 2]})])
    with pytest.raises(ad.AdapterError):
        ad.read_frozen_eng(P)


# ------------------------------------------------------------------ accepted historical schema shapes
def test_closure_absent_null_recorded_all_accepted(monkeypatch, tmp_path):
    _write_eng(monkeypatch, tmp_path, [
        _eng_line("saleor-rc-a", manifest={"install_mode": "x", "lockfile_sha256": "y"}),
        _eng_line("saleor-rc-b", manifest={"install_mode": "x", "lockfile_sha256": "y",
                                           "dev_test_closure": None}),
        _eng_line("saleor-rc-c", manifest={"install_mode": "x", "lockfile_sha256": "y",
                                           "dev_test_closure": {"mechanism": "poetry"}}),
    ])
    frozen = ad.read_frozen_eng(P)
    assert {r.recorded_closure_state for r in frozen.values()} == {
        "NOT_RECORDED_ABSENT", "NOT_RECORDED_NULL", "RECORDED"}


def test_eng_record_carries_recorded_reference_and_derived_fields():
    frozen = ad.read_frozen_eng(P)
    tid = next(iter(frozen))
    rec = ad.eng_record(P, tid)
    assert rec["adapter_record_sha256"]
    assert rec["install_mode"] in ("LOCK_EXACT_MAIN_PLUS_DEV", "V2_MAIN_PLUS_EXACT_LOCKED_DEV")
    assert rec["recorded_reference"]["recorded_install_mode"] == frozen[tid].recorded_install_mode
    # independent provenance: derived fields are NOT copied from the record
    assert rec["install_mode_provenance"].startswith("DERIVED_FROM_TARGET_MANIFESTS")


# ------------------------------------------------------------------ dev-group + mechanism-none fail-closed (M16 class)
def test_dev_group_declared_with_mechanism_none_is_rejected():
    records, unresolved = ad.main_records(P)
    assert "saleor-rc-f76d0093b450" in unresolved
    assert "DEV_GROUP_DECLARED_BUT_MECHANISM_NONE" in unresolved["saleor-rc-f76d0093b450"]


def test_mechanism_none_without_dev_group_is_not_a_devgroup_violation():
    # A task that resolves to frozen closure mechanism none without declaring a
    # dev/test group is resolvable (not the M16 class).
    mf = {"requirements.txt": "django==4.2\n"}
    assert ad.frozen_declares_dev_group(mf) is False
    c = ad.frozen_dev_closure(mf, "py39")
    assert c["mechanism"] in ("requirements", "none")


# ------------------------------------------------------------------ determinism
def test_adapter_record_is_deterministic():
    records, _ = ad.main_records(P)
    tid = next(iter(records))
    a = ad.main_record(P, tid)
    b = ad.main_record(P, tid)
    assert a == b
    assert a["adapter_record_sha256"] == b["adapter_record_sha256"]
