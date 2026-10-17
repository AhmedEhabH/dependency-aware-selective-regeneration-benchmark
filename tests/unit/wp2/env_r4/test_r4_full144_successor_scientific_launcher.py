"""M17_D7_R4_POSTQUAL_SUCCESSOR_PREEXECUTION_FREEZE — deterministic launcher P2P/F2P tests.

Mission M17_D7_R4_POSTQUAL_SUCCESSOR_PREEXECUTION_FREEZE (T3, PRE-EXECUTION FREEZE).

These tests exercise ONLY deterministic / non-scientific behaviour of the
successor scientific Full144 preflight module
(``scripts/r4_full144_successor_scientific_preflight.py``) and its operator
launcher.  ZERO real scientific units are executed.

P2P (must pass):
  P1  - release identity valid at the committed HEAD (branch/tag peel/code-set/
        closure/population/order/image recompute).
  P2  - all three fresh R3.1 receipts validated (TARGETED3 3/3/0, CAL12 12/12/0,
        FULL144 144/144/0) with exact membership/manifest/counts.
  P3  - scientific root freshness gate reports the real frozen root.
  P4  - static checks PASS (--network=none, no LLM/pull/build).
  P5  - freeze record composes all mission bindings (schemas + hashes + analysis).

F2P (must fail closed):
  F1  - wrong branch mock          -> reject
  F2  - dirty tracked worktree     -> reject
  F3  - wrong scientific tag peel  -> reject
  F4  - wrong code-set recompute   -> reject
  F5  - wrong closure content      -> reject
  F6  - wrong population identity  -> reject
  F7  - wrong order hash           -> reject
  F8  - wrong image binding        -> reject
  F9  - a receipt with wrong counts -> reject
  F10 - missing receipt            -> reject
  F11 - non-fresh scientific root  -> reject
  F12 - launcher no-subcommand     -> reject (rc != 0)
  F13 - launcher has no LLM/network dependency
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(SCRIPTS))

import r4_full144_successor_scientific_preflight as pf  # noqa: E402


class TestP1ReleaseIdentity:
    def test_release_identity_recomputes(self) -> None:
        out = pf.verify_release_identity()
        assert out["branch"] == pf.BRANCH
        assert out["scientific_authority_peel"] == pf.SCIENTIFIC_HEAD
        assert out["r3_1_release_head"] == pf.R3_1_RELEASE_HEAD
        assert out["effective_execution_code_set_hash"] == pf.EXPECTED_EXECUTION_CODE_SET
        assert out["committed_closure_content_hash"] == pf.EXPECTED_CLOSURE_CONTENT
        assert out["closure_semantic_footprint"] == pf.EXPECTED_CLOSURE_FOOTPRINT
        assert out["population_identity"] == pf.EXPECTED_POPULATION
        assert out["ordered_membership_hash"] == pf.EXPECTED_ORDER
        assert out["image_binding_hash"] == pf.EXPECTED_IMAGE
        assert out["tracked_clean"] is True


class TestP2Receipts:
    def test_all_three_receipts_valid(self) -> None:
        rx = pf.verify_all_receipts()
        assert rx["TARGETED3"]["counts"] == (3, 3, 0)
        assert rx["CAL12"]["counts"] == (12, 12, 0)
        assert rx["FULL144"]["counts"] == (144, 144, 0)
        assert len(rx["FULL144"]["sha256"]) == 64


class TestP3FreshRoot:
    def test_scientific_root_state_zero_units(self) -> None:
        st = pf._scientific_root_state()
        assert st["zero_units_executed"] is True
        assert st["n_scientific_unit_dirs"] == 0


class TestP4Static:
    def test_static_checks(self) -> None:
        s = pf.static_checks()
        assert s["static"] == "PASS"
        assert s["network_isolation"] == "--network=none"


class TestP5FreezeRecord:
    def test_freeze_record_composes_bindings(self) -> None:
        rec = pf.freeze_record()
        assert rec["schema_version"].startswith("env-canon-r4/r3.1/")
        assert rec["scientific_authority"]["head"] == pf.SCIENTIFIC_HEAD
        assert rec["execution_code_set_hash"] == pf.EXPECTED_EXECUTION_CODE_SET
        assert rec["committed_closure_content_hash"] == pf.EXPECTED_CLOSURE_CONTENT
        assert rec["population"]["ordered_membership_hash"] == pf.EXPECTED_ORDER
        assert rec["population"]["n_validation_units"] == 144
        assert rec["image_binding_hash"] == pf.EXPECTED_IMAGE
        assert rec["qualification_receipts"]["TARGETED3"]["counts"] == [3, 3, 0]
        assert rec["qualification_receipts"]["CAL12"]["counts"] == [12, 12, 0]
        assert rec["qualification_receipts"]["FULL144"]["counts"] == [144, 144, 0]
        assert rec["seeds_determinism"]["status"] == "NOT_APPLICABLE"
        analysis = rec["run_to_run_determinism_secondary_analysis"]
        assert analysis["title"] == "RUN_TO_RUN_DETERMINISM_SECONDARY_ANALYSIS"
        assert analysis["compared_fields"] == ["result", "classification"]
        assert rec["scientific_output_root"] == str(pf.SCIENTIFIC_ROOT)


class TestF1WrongBranch:
    def test_wrong_branch_fails_closed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(pf, "git_branch", lambda: "wrong/branch")
        with pytest.raises(pf.LauncherError, match="branch"):
            pf.verify_release_identity()


class TestF2DirtyTree:
    def test_dirty_tracked_fails_closed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(pf, "git_clean_tracked", lambda: False)
        with pytest.raises(pf.LauncherError, match="not clean"):
            pf.verify_release_identity()


class TestF3WrongSciPeel:
    def test_wrong_scientific_peel_fails_closed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(pf, "tag_peel", lambda tag: "0" * 40 if tag == pf.SCIENTIFIC_TAG else pf.SCIENTIFIC_HEAD)
        with pytest.raises(pf.LauncherError, match="scientific tag"):
            pf.verify_release_identity()


class TestF4WrongCodeSet:
    def test_wrong_code_set_fails_closed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(pf, "effective_code_set_hash", lambda: "0" * 64)
        with pytest.raises(pf.LauncherError, match="execution-code-set"):
            pf.verify_release_identity()


class TestF5WrongClosure:
    def test_wrong_closure_content_fails_closed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(pf, "effective_code_set_hash", lambda: pf.EXPECTED_EXECUTION_CODE_SET)
        monkeypatch.setattr(pf, "blob_lf_sha256_at", lambda rev, rel: "0" * 64)
        with pytest.raises(pf.LauncherError, match="closure"):
            pf.verify_release_identity()


class TestF6WrongPopulation:
    def test_wrong_population_fails_closed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(pf, "population_authority", lambda: {
            "population_identity": "0" * 64,
            "ordered_membership_hash": pf.EXPECTED_ORDER,
            "binding_hash": pf.EXPECTED_IMAGE,
        })
        with pytest.raises(pf.LauncherError, match="population"):
            pf.verify_release_identity()


class TestF7WrongOrder:
    def test_wrong_order_fails_closed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(pf, "population_authority", lambda: {
            "population_identity": pf.EXPECTED_POPULATION,
            "ordered_membership_hash": "0" * 64,
            "binding_hash": pf.EXPECTED_IMAGE,
        })
        with pytest.raises(pf.LauncherError, match="membership"):
            pf.verify_release_identity()


class TestF8WrongImage:
    def test_wrong_image_fails_closed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(pf, "population_authority", lambda: {
            "population_identity": pf.EXPECTED_POPULATION,
            "ordered_membership_hash": pf.EXPECTED_ORDER,
            "binding_hash": "0" * 64,
        })
        with pytest.raises(pf.LauncherError, match="binding"):
            pf.verify_release_identity()


class TestF9ReceiptCounts:
    def test_wrong_receipt_counts_fail_closed(self, monkeypatch: pytest.MonkeyPatch) -> None:

        import r4_full144_successor_scientific_preflight as _pf

        real = _pf.RECEIPTS["TARGETED3"]
        fake = dict(real)
        fake["counts"] = (2, 2, 0)
        monkeypatch.setattr(_pf, "RECEIPTS", {**_pf.RECEIPTS, "TARGETED3": fake})
        with pytest.raises(_pf.LauncherError, match="receipt counts"):
            _pf.verify_all_receipts()


class TestF10MissingReceipt:
    def test_missing_receipt_fails_closed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import r4_full144_successor_scientific_preflight as _pf

        fake = dict(_pf.RECEIPTS["CAL12"])
        fake["root"] = Path("Z:\\nonexistent")
        monkeypatch.setattr(_pf, "RECEIPTS", {**_pf.RECEIPTS, "CAL12": fake})
        with pytest.raises(_pf.LauncherError, match="missing"):
            _pf.verify_all_receipts()


class TestF11NonFreshRoot:
    def test_nonfresh_root_fails_closed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from pathlib import Path

        import r4_full144_successor_scientific_preflight as _pf

        fake_root = Path(r"D:\WP2\runs\r4-scientific-full144-successor-2026-10-17")
        monkeypatch.setattr(_pf, "SCIENTIFIC_ROOT", fake_root)
        monkeypatch.setattr(
            _pf,
            "_scientific_root_state",
            lambda: {"exists": True, "n_scientific_unit_dirs": 1,
                     "progress_exists": True, "receipt_exists": False,
                     "zero_units_executed": False},
        )
        with pytest.raises(_pf.LauncherError, match="NOT fresh"):
            _pf.verify_scientific_root_fresh()


class TestLauncherCompliance:
    def test_launcher_has_status_preflight_exec(self) -> None:
        src = (SCRIPTS / "r4_full144_successor_scientific_launcher.ps1").read_text(encoding="utf-8")
        assert "-Status" in src and "-Preflight" in src and "-Exec" in src
        for forbidden in ("OpenCode", "OpenRouter", "LLM", "openai", "anthropic"):
            assert forbidden.lower() not in src.lower()

    def test_python_cli_requires_subcommand(self) -> None:
        import subprocess

        p = subprocess.run(
            [sys.executable, str(SCRIPTS / "r4_full144_successor_scientific_preflight.py")],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        assert p.returncode != 0
