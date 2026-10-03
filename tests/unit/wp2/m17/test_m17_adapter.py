"""M17 K02 - frozen-harness-derived adapter: identity, accounting, fail-closed (zero network)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

P = Path(__file__).resolve().parents[4]
for _p in (P, P / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts import wp2_m17_adapter as ad  # noqa: E402


# ------------------------------------------------------------------ frame / schema shapes
def test_schema_shape_main_census_row():
    census = {t["task_id"]: t for t in ad.load_json(P / ad.CENSUS_REL)["tasks"]}
    frame = ad.frame_220(P)
    assert len(frame) == 220
    for tid in frame:
        row = census[tid]
        assert row["task_id"] == tid
        assert row["parent_commit"] and row["target_commit"]
        assert row["f2p_candidacy"] in ("STRONG_F2P_CANDIDATE", "MODIFIED_TEST_CANDIDATE")


def test_schema_shape_per_task_v2_record():
    idx = ad._per_task_index(P)
    frame = set(ad.frame_220(P))
    assert set(idx) == frame
    for tid in frame:
        r = idx[tid]
        assert r["status"] == "DONE"
        assert r["era_key"] in ad.ERAS


def test_schema_shape_phase5_eng_records():
    frozen = ad.read_frozen_eng(P)
    assert len(frozen) == 29
    for r in frozen.values():
        assert r.task_id and r.target_commit
        assert r.recorded_install_mode in ("LOCK_EXACT_MAIN_PLUS_DEV", "V2_MAIN_PLUS_EXACT_LOCKED_DEV")
        assert r.recorded_lockfile_sha256
        assert r.recorded_closure_state in ("RECORDED", "NOT_RECORDED_ABSENT", "NOT_RECORDED_NULL")


# ------------------------------------------------------------------ ENG reader fail-closed schema
HEX40 = "a" * 40


def test_eng_reader_missing_task_id_fails_closed(monkeypatch, tmp_path):
    text = (f'{{"target_commit": "{HEX40}", "status": "DONE", '
            '"manifest": {"install_mode": "x", "lockfile_sha256": "y"}}\n')
    p = tmp_path / "eng.jsonl"
    p.write_text(text, encoding="utf-8")
    monkeypatch.setattr(ad, "PHASE5_ENG_V3_REL", p)
    with pytest.raises(ad.AdapterError):
        ad.read_frozen_eng(P)


def test_eng_reader_missing_target_commit_fails_closed(monkeypatch, tmp_path):
    text = ('{"task_id": "saleor-rc-a", "status": "DONE", '
            '"manifest": {"install_mode": "x", "lockfile_sha256": "y"}}\n')
    p = tmp_path / "eng.jsonl"
    p.write_text(text, encoding="utf-8")
    monkeypatch.setattr(ad, "PHASE5_ENG_V3_REL", p)
    with pytest.raises(ad.AdapterError):
        ad.read_frozen_eng(P)


def test_eng_reader_missing_install_mode_fails_closed(monkeypatch, tmp_path):
    text = (f'{{"task_id": "saleor-rc-a", "target_commit": "{HEX40}", "status": "DONE", '
            '"manifest": {"lockfile_sha256": "y"}}\n')
    p = tmp_path / "eng.jsonl"
    p.write_text(text, encoding="utf-8")
    monkeypatch.setattr(ad, "PHASE5_ENG_V3_REL", p)
    with pytest.raises(ad.AdapterError):
        ad.read_frozen_eng(P)


def test_eng_reader_missing_lockfile_fails_closed(monkeypatch, tmp_path):
    text = (f'{{"task_id": "saleor-rc-a", "target_commit": "{HEX40}", "status": "DONE", '
            '"manifest": {"install_mode": "x"}}\n')
    p = tmp_path / "eng.jsonl"
    p.write_text(text, encoding="utf-8")
    monkeypatch.setattr(ad, "PHASE5_ENG_V3_REL", p)
    with pytest.raises(ad.AdapterError):
        ad.read_frozen_eng(P)


def test_eng_reader_duplicate_task_id_fails_closed(monkeypatch, tmp_path):
    text = (
        f'{{"task_id": "saleor-rc-a", "target_commit": "{HEX40}", "status": "DONE", '
        '"manifest": {"install_mode": "x", "lockfile_sha256": "y"}}\n'
        f'{{"task_id": "saleor-rc-a", "target_commit": "{HEX40}", "status": "DONE", '
        '"manifest": {"install_mode": "x", "lockfile_sha256": "y"}}\n'
    )
    p = tmp_path / "eng.jsonl"
    p.write_text(text, encoding="utf-8")
    monkeypatch.setattr(ad, "PHASE5_ENG_V3_REL", p)
    with pytest.raises(ad.AdapterError):
        ad.read_frozen_eng(P)


def test_eng_reader_unknown_manifest_key_shape_fails_closed(monkeypatch, tmp_path):
    text = (f'{{"task_id": "saleor-rc-a", "target_commit": "{HEX40}", "status": "DONE", '
            '"manifest": {"install_mode": "x", "lockfile_sha256": "y", "dev_test_closure": [1, 2]}}\n')
    p = tmp_path / "eng.jsonl"
    p.write_text(text, encoding="utf-8")
    monkeypatch.setattr(ad, "PHASE5_ENG_V3_REL", p)
    with pytest.raises(ad.AdapterError):
        ad.read_frozen_eng(P)


# ------------------------------------------------------------------ frozen derivation primitives
def test_frozen_install_mode_matches_frozen_harness():
    # The adapter must derive install mode via the frozen harness lock_install_script.
    from benchmark.wp2.harness_v3 import lock_install_script
    tid = next(iter(ad.read_frozen_eng(P)))
    frozen = ad.read_frozen_eng(P)[tid]
    mf = ad.target_manifests_local(frozen.target_commit)
    assert ad.frozen_install_mode(mf) == lock_install_script(ad.PROBE_WT, mf)[1]


def test_frozen_lockfile_matches_frozen_harness():
    from benchmark.wp2.harness_v3 import lockfile_sha256
    frozen = ad.read_frozen_eng(P)
    for tid in list(frozen)[:5]:
        mf = ad.target_manifests_local(frozen[tid].target_commit)
        assert ad.frozen_lockfile(mf) == lockfile_sha256(mf)


def test_frozen_dev_closure_uses_frozen_compiler():
    frozen = ad.read_frozen_eng(P)
    tid = next(iter(frozen))
    mf = ad.target_manifests_local(frozen[tid].target_commit)
    c = ad.frozen_dev_closure(mf, frozen[tid].era_key)
    assert c["mechanism"] in ("uv", "poetry", "requirements", "none")
    assert "pins_sha256" in c and "era_key" in c


def test_frozen_declares_dev_group_uses_frozen_compiler():
    from benchmark.wp2.dep_compiler import pyproject_dev_group_names
    py = "x = 1\n[tool.poetry.group.dev.dependencies]\npytest = \"^8\"\n\n[tool.ruff]\n"
    mf = {"pyproject.toml": py}
    assert ad.frozen_declares_dev_group(mf) is True
    assert bool(pyproject_dev_group_names(py)) is True
    assert ad.frozen_declares_dev_group({"pyproject.toml": "x = 1\n"}) is False


# ------------------------------------------------------------------ ENG identity (all 29, derived-vs-derived)
def test_eng_identity_all_29_pass():
    check = ad.eng_identity_check(P)
    assert len(check) == 29
    assert all(r["pass"] for r in check.values()), {
        t: r["violations"] for t, r in check.items() if not r["pass"]}
    for r in check.values():
        assert r["closure_original_sha256"] == r["closure_adapted_sha256"]
        assert r["install_mode_original"] == r["install_mode_adapted"]
        assert r["lockfile_original"] == r["lockfile_adapted"]
        assert r["target_commit_frozen"] is not None


def test_eng_identity_is_not_copy_vs_copy(monkeypatch):
    # If the adapter changed era, the derived-vs-derived check must FAIL.
    real = ad.eng_record
    tid = next(iter(ad.read_frozen_eng(P)))

    def wrong_era(_p, t):
        rec = dict(real(_p, t))
        rec["era"] = "pyX-injected"
        return rec

    monkeypatch.setattr(ad, "eng_record", wrong_era)
    check = ad.eng_identity_check(P)
    assert check[tid]["pass"] is False
    assert "ERA_ADAPTER_DIFFERS_FROM_FROZEN" in check[tid]["violations"]


def test_eng_identity_fails_if_target_changes_harness_behavior(monkeypatch):
    # Changing target_commit changes the manifests the frozen harness reads,
    # so the identity check must fail.
    real = ad.eng_record
    tid = next(iter(ad.read_frozen_eng(P)))

    def wrong_target(_p, t):
        rec = dict(real(_p, t))
        rec["target_commit"] = "0" * 40
        return rec

    monkeypatch.setattr(ad, "eng_record", wrong_target)
    check = ad.eng_identity_check(P)
    assert check[tid]["pass"] is False


def test_eng_m16_flagged_tasks_now_match_frozen_harness():
    # M16 flagged these 3 for INSTALL_MODE_DIFFERS_FROM_RECORD. Under M17 the
    # adapter derives install mode through the CURRENT frozen harness on both
    # sides, so identity passes; the recorded value stays as reference only.
    check = ad.eng_identity_check(P)
    for tid in ("saleor-rc-939093a9c65c", "saleor-rc-a8e6a4dd55fe", "saleor-rc-f73c4e95c828"):
        r = check[tid]
        assert r["pass"] is True
        assert r["install_mode_original"] == "V2_MAIN_PLUS_EXACT_LOCKED_DEV"
        assert r["recorded_install_mode_reference"] == "LOCK_EXACT_MAIN_PLUS_DEV"


# ------------------------------------------------------------------ MAIN accounting (220)
def test_main_records_all_220_accounted():
    records, unresolved = ad.main_records(P)
    frame = set(ad.frame_220(P))
    assert set(records) | set(unresolved) == frame
    assert len(records) + len(unresolved) == 220
    assert set(records) & set(unresolved) == set()
    for rec in records.values():
        assert rec["task_id"] and rec["target_commit"] and rec["era"] in ad.ERAS
        assert rec["install_mode"] in ("LOCK_EXACT_MAIN_PLUS_DEV", "V2_MAIN_PLUS_EXACT_LOCKED_DEV")
        assert rec["lockfile_sha256"]
        assert rec["adapter_record_sha256"]
        assert rec["dev_test_closure"]["mechanism"] in ("uv", "poetry", "requirements", "none")


def test_main_f76d_dev_group_mechanism_none_adapter_unresolved():
    # Exact M16 R2A fail-closed class: declared dev group + frozen mechanism none.
    records, unresolved = ad.main_records(P)
    assert "saleor-rc-f76d0093b450" in unresolved
    assert "DEV_GROUP_DECLARED_BUT_MECHANISM_NONE" in unresolved["saleor-rc-f76d0093b450"]


def test_no_resolved_main_has_dev_group_with_mechanism_none():
    records, _unresolved = ad.main_records(P)
    for rec in records.values():
        if rec["declares_dev_group"]:
            assert rec["dev_test_closure"]["mechanism"] != "none"


# ------------------------------------------------------------------ determinism
def test_adapter_record_is_deterministic():
    records, _ = ad.main_records(P)
    tid = next(iter(records))
    assert ad.main_record(P, tid) == ad.main_record(P, tid)


def test_eng_identity_is_deterministic():
    assert ad.eng_identity_check(P) == ad.eng_identity_check(P)


# ------------------------------------------------------------------ no-selector-input static guard
def test_static_guard_blocks_selector_paths():
    source = Path(ad.__file__).read_text(encoding="utf-8")
    assert ad.static_selector_guard(source) is True
    assert ad.static_selector_guard("research/wp1a/sip_rmcss_per_task_predictions.json") is False
    assert ad.static_selector_guard("from benchmark.wp2.e2e.scopes import build_arm_scopes") is False
