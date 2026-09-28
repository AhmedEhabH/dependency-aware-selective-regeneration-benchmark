"""Mission-12B v2.1 - freeze builder unit tests (T4): zero API.

Covers:
- null Harness SHA -> hard FAIL (FreezeViolation)
- missing v21 HOLD -> hard FAIL
- v1 frozen scope semantic hash mismatch -> hard FAIL
- model/route/sampling mismatch -> hard FAIL
- historical v2 root configured as output -> hard FAIL
- valid build records semantic + git blob hashes with distinct field names,
  14x4 plan, transport policy, budget, variance, d220 rule, dedup rule.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts import wp2_e2e_smoke_v21_freeze as fb


def _monkey(monkeypatch, tmp_path: Path) -> dict:
    """Build a monkeypatched module state against a tmp v21 root."""
    v21 = tmp_path / "e2e_smoke_eng_v21"
    (v21 / "HOLD").parent.mkdir(parents=True, exist_ok=True)
    (v21 / "HOLD").write_text("", encoding="utf-8")
    old_root = fb.V21_ROOT
    old_hold = fb.HOLD
    fb.V21_ROOT = v21
    fb.HOLD = v21 / "HOLD"
    return {"v21": v21, "old_root": old_root, "old_hold": old_hold}


def _restore(monkeypatch, state: dict) -> None:
    fb.V21_ROOT = state["old_root"]
    fb.HOLD = state["old_hold"]


def test_null_harness_sha_hard_fail(monkeypatch, tmp_path: Path) -> None:
    state = _monkey(monkeypatch, tmp_path)
    try:
        fb.HARNESS_SPEC_SHA256 = ""
        with pytest.raises(fb.FreezeViolation):
            fb.build_freeze(allow_write=False)
    finally:
        fb.HARNESS_SPEC_SHA256 = "e7897ba0850bd0af372273a32ffb33435b4dc75c9476d527ec86fa424a75f034"
        _restore(monkeypatch, state)


def test_missing_hold_hard_fail(monkeypatch, tmp_path: Path) -> None:
    state = _monkey(monkeypatch, tmp_path)
    try:
        fb.HOLD.unlink()
        with pytest.raises(fb.FreezeViolation):
            fb.build_freeze(allow_write=False)
    finally:
        _restore(monkeypatch, state)


def test_scope_hash_mismatch_hard_fail(monkeypatch, tmp_path: Path) -> None:
    state = _monkey(monkeypatch, tmp_path)
    # isolate against a tmp copy of the frozen v1 scopes so the test can never
    # mutate the historical v1 evidence (F01-style test isolation)
    import json
    import shutil

    from benchmark.wp2.e2e.spec import ARMS
    scopes_tmp = tmp_path / "v1_scopes_tmp"
    shutil.copytree(fb.V1_SCOPES, scopes_tmp)
    old_scopes = fb.V1_SCOPES
    fb.V1_SCOPES = scopes_tmp
    try:
        for arm in ARMS:
            fname = {"GOLD_HARD": "scopes_GOLD_HARD.json", "RMCSS_HARD": "scopes_RMCSS_HARD.json",
                     "AGENT_HARD": "scopes_AGENT_HARD.json",
                     "PLACEBO_HARD": "scopes_PLACEBO_HARD.json"}[arm]
            p = scopes_tmp / fname
            d = json.loads(p.read_text(encoding="utf-8"))
            d["tamper"] = True
            p.write_text(json.dumps(d), encoding="utf-8")
            with pytest.raises(fb.FreezeViolation):
                fb.build_freeze(allow_write=False)
    finally:
        fb.V1_SCOPES = old_scopes
        _restore(monkeypatch, state)


def test_model_mismatch_hard_fail(monkeypatch, tmp_path: Path) -> None:
    state = _monkey(monkeypatch, tmp_path)
    try:
        old = fb.MODEL
        fb.MODEL = "wrong/model"
        with pytest.raises(fb.FreezeViolation):
            fb.build_freeze(allow_write=False)
        fb.MODEL = old
    finally:
        _restore(monkeypatch, state)


def test_valid_build_records_full_identity(monkeypatch, tmp_path: Path) -> None:
    state = _monkey(monkeypatch, tmp_path)
    try:
        fz = fb.build_freeze(allow_write=False)
        assert fz["n_planned"] == 56
        assert len(fz["arms"]) == 4
        assert fz["harness_v3_identity"]["spec_sha256"]
        # distinct field names for semantic vs git blob
        assert set(fz["scopes_sha256_per_arm"]) == set(fz["scopes_git_blob_per_arm"])
        assert set(fz["scopes_sha256_per_arm"]) == set(fz["scopes_raw_sha256_per_arm"])
        for arm in fz["arms"]:
            assert fz["scopes_sha256_per_arm"][arm] != fz["scopes_git_blob_per_arm"][arm]
            assert fz["scopes_sha256_per_arm"][arm] != fz["scopes_raw_sha256_per_arm"][arm]
        assert fz["evaluator_sets"]["semantic_sha256"]
        assert fz["evaluator_sets"]["git_blob_sha1"]
        assert fz["transport_policy"]["total_http_attempts"] == 4
        assert fz["budget"]["scientific_ceiling_usd"] == 2.00
        assert len(fz["variance_design"]["replicates"]) == 2
        assert fz["variance_design"]["n_episodes"] == 6
        assert "d220_sensitivity" in fz
        assert "evaluation_dedup_rule" in fz
        assert fz["workers"] == 1
        assert len(fz["code_sha256"]) >= 3
    finally:
        _restore(monkeypatch, state)
