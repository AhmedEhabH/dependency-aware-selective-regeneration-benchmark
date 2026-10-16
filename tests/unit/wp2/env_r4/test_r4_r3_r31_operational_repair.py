"""M17_D7_R4_PHASE1C_R31_OPERATIONAL_HARNESS_REPAIR - R3.1 repair tests.

Deterministic / non-scientific only.  ZERO real benchmark units are executed.

Covers the two confirmed R3 defects plus the R3.1 repair contract:
  L1  - launcher uses $HarnessArgs (no $Args automatic-variable collision).
  C1  - Python CLI no-subcommand returns non-zero.
  D1  - disk guard 161/150/119 GiB behaviour on the real sweep path.
  E1  - TARGETED3 / CAL12 fail-fast (single non-PASS stops the sweep).
  E2  - FULL144 QUALIFICATION ordinary non-PASS continues + aggregate non-PASS.
  E3  - qualification GLOBAL stop on corrupt checkpoint.
  F1  - resume from N+1 (atomic checkpoint, exact next required unit).
  F2  - corrupt/mismatched checkpoint => STOP (fail closed).
  H1  - ambient env sanitisation (single effective root per selection).
  G1  - cleanup contract: only per-unit wheelhouse removed; shared stores intact;
        Docker-volume cleanup stays with the frozen runner (never duplicated).
  J1  - predecessor R3 receipt (old release identity) is rejected by R3.1.
  I1  - committed selection membership / manifest hashes are unchanged.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import r4_r3_selection_harness as h  # noqa: E402

R3_TAG = "m17-d7-r4-population-qualification-harness-r3-2026-10-16"
R31_TAG = "m17-d7-r4-population-qualification-harness-r3-1-2026-10-16"


def _auth() -> dict[str, Any]:
    return h.load_authority()


def _fake_driver(records: list[dict[str, Any]]) -> Any:
    class _Driver:
        def __init__(self) -> None:
            self.r2 = type("_R2", (), {"FROZEN_UNIT_ORDER": (), "load_plan": (lambda: None)})()

        def run_unit(self, idx: int) -> dict[str, Any]:
            return records[idx - 1]

    return _Driver()


# ---------------------------------------------------------------------------
# L1 launcher forwarding fix
# ---------------------------------------------------------------------------
class TestLauncherHarnessArgs:
    def test_launcher_uses_harness_args_param(self) -> None:
        src = (SCRIPTS / "r4_r3_selection_launcher.ps1").read_text(encoding="utf-8")
        assert "param([string[]]$HarnessArgs)" in src
        assert "param([string[]]$Args)" not in src
        assert "Invoke-Harness -HarnessArgs @(" in src
        assert "--preflight" in src and "--exec" in src and "--status" in src

    def test_launcher_forwarding_real_status(self) -> None:
        """Real pwsh launcher forwards to the real harness; no argparse usage."""
        import shutil

        pwsh = shutil.which("pwsh")
        if not pwsh:
            pytest.skip("pwsh not available")
        p = subprocess.run(
            [
                pwsh, "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(SCRIPTS / "r4_r3_selection_launcher.ps1"),
                "-Selection", "TARGETED3", "-Status",
            ],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        assert p.returncode == 0, p.stdout + p.stderr
        assert "usage:" not in p.stdout
        assert "TARGETED3" in p.stdout


# ---------------------------------------------------------------------------
# C1 no-subcommand rc != 0
# ---------------------------------------------------------------------------
class TestCliNoSubcommand:
    def test_main_no_args_returns_nonzero(self) -> None:
        assert h.main([]) != 0

    def test_real_no_subcommand_rc_nonzero(self) -> None:
        p = subprocess.run([sys.executable, str(SCRIPTS / "r4_r3_selection_harness.py")],
                           capture_output=True, text=True, cwd=str(ROOT))
        assert p.returncode != 0
        assert "usage:" in (p.stdout + p.stderr).lower()

    def test_subcommands_still_pass(self) -> None:
        assert h.main(["--verify-selection", "TARGETED3"]) == 0


# ---------------------------------------------------------------------------
# D1 disk guard
# ---------------------------------------------------------------------------
class TestDiskGuard:
    @pytest.mark.parametrize("free,action", [
        (161.0, "CONTINUE"),
        (150.0, "WARN_CONTINUE"),
    ])
    def test_continue_warn(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
                           free: float, action: str) -> None:
        monkeypatch.setattr(h, "disk_free_gib", lambda path=None: free)
        out = h.check_disk_before_unit("TARGETED3", tmp_path)
        assert out["action"] == action

    def test_hard_stop(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr(h, "disk_free_gib", lambda path=None: 119.0)
        with pytest.raises(h.R3Error):
            h.check_disk_before_unit("FULL144", tmp_path)


# ---------------------------------------------------------------------------
# E1 fail-fast TARGETED3 / CAL12
# ---------------------------------------------------------------------------
class TestFailFast:
    def _sweep_with(self, monkeypatch: pytest.MonkeyPatch, root: Path,
                    records: list[dict[str, Any]]) -> None:
        monkeypatch.setattr(h, "configure_driver", lambda name, r: _fake_driver(records))
        monkeypatch.setattr(h, "disk_free_gib", lambda path=None: 300.0)
        monkeypatch.setenv("R4_R3_TARGETED3_ROOT", str(root))

    def test_targeted3_non_pass_stops(self, monkeypatch: pytest.MonkeyPatch,
                                      tmp_path: Path) -> None:
        m = h.load_selection("TARGETED3")
        records = [
            {"calibration_index": i, "validation_unit_id": m["ordered_unit_ids"][i - 1],
             "result": "FAIL" if i == 1 else "PASS", "classification": "ENV_OFFLINE_INSTALL_FAILURE"}
            for i in range(1, 4)
        ]
        self._sweep_with(monkeypatch, tmp_path, records)
        with pytest.raises(h.ReceiptError):
            h.run_selection_sweep("TARGETED3", tmp_path)

    def test_cal12_non_pass_stops(self, monkeypatch: pytest.MonkeyPatch,
                                  tmp_path: Path) -> None:
        m = h.load_selection("CAL12")
        records = [
            {"calibration_index": i, "validation_unit_id": m["ordered_unit_ids"][i - 1],
             "result": "FAIL" if i == 3 else "PASS", "classification": "ENV_TIMEOUT"}
            for i in range(1, 13)
        ]
        self._sweep_with(monkeypatch, tmp_path, records)
        with pytest.raises(h.ReceiptError):
            h.run_selection_sweep("CAL12", tmp_path)

    def test_targeted3_fail_fast_does_not_run_later_units(self, monkeypatch: pytest.MonkeyPatch,
                                                          tmp_path: Path) -> None:
        calls: list[int] = []

        class _ThrowingDriver:
            def __init__(self, *_args: Any, **_kwargs: Any) -> None:
                pass

            r2 = type("_R2", (), {})()

            def run_unit(self, idx: int) -> dict[str, Any]:
                calls.append(idx)
                raise RuntimeError("driver fail-fast")

        monkeypatch.setattr(h, "configure_driver", lambda name, r: _ThrowingDriver())
        monkeypatch.setattr(h, "disk_free_gib", lambda path=None: 300.0)
        monkeypatch.setenv("R4_R3_TARGETED3_ROOT", str(tmp_path))
        with pytest.raises(h.R3Error):
            h.run_selection_sweep("TARGETED3", tmp_path)
        assert calls == [1]


# ---------------------------------------------------------------------------
# E2 / E3 / F1 / F2 FULL144 qualification continuation + resume semantics
# ---------------------------------------------------------------------------
def _qual_world(tmp_path: Path, completed: int | None = None) -> list[dict[str, Any]]:
    m = h.load_selection("FULL144")
    records: list[dict[str, Any]] = []
    for i in range(1, int(m["expected_count"]) + 1):
        records.append({
            "calibration_index": i,
            "validation_unit_id": m["ordered_unit_ids"][i - 1],
            "result": "PASS",
            "classification": "PASS",
        })
    if completed is not None:
        records[completed - 1]["result"] = "FAIL"
        records[completed - 1]["classification"] = "ENV_OFFLINE_INSTALL_FAILURE"
    return records


class TestFULL144Qualification:
    def _patch(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
               records: list[dict[str, Any]]) -> None:
        monkeypatch.setattr(h, "configure_driver", lambda name, r: _fake_driver(records))
        monkeypatch.setattr(h, "disk_free_gib", lambda path=None: 300.0)
        monkeypatch.setenv("R4_R3_QUALIFICATION144_ROOT", str(tmp_path))

        def bind(driver: Any, m: dict[str, Any], idx: int, uid: str, root: Path) -> Any:
            class _Runner:
                def run_unit(self, _idx: int) -> dict[str, Any]:
                    return records[idx - 1]

            # emulate a GLOBAL infra failure on a specific unit
            if uid == "vu-GLOBAL":
                raise RuntimeError("docker daemon unreachable")
            return _Runner()

        monkeypatch.setattr(h, "_bind_qualification_unit", bind)

    def test_full144_continues_on_local_non_pass(self, monkeypatch: pytest.MonkeyPatch,
                                                 tmp_path: Path) -> None:
        records = _qual_world(tmp_path, completed=2)
        self._patch(monkeypatch, tmp_path, records)
        agg = h.run_qualification_sweep("FULL144", tmp_path)
        assert agg["N_EXECUTED"] == 144
        assert agg["N_PASS"] == 143
        assert agg["N_NON_PASS"] == 1
        assert agg["order_preserved"] is True

    def test_full144_final_receipt_non_pass(self, monkeypatch: pytest.MonkeyPatch,
                                            tmp_path: Path) -> None:
        records = _qual_world(tmp_path, completed=7)
        self._patch(monkeypatch, tmp_path, records)
        agg = h.run_qualification_sweep("FULL144", tmp_path)
        assert agg["N_NON_PASS"] == 1
        assert agg["N_PASS"] == 143

    def test_full144_global_stop_on_infra(self, monkeypatch: pytest.MonkeyPatch,
                                          tmp_path: Path) -> None:
        records = _qual_world(tmp_path)
        records[0]["validation_unit_id"] = "vu-GLOBAL"
        records[0]["calibration_index"] = 1
        self._patch(monkeypatch, tmp_path, records)

        def bind(driver: Any, m: dict[str, Any], idx: int, uid: str, root: Path) -> Any:
            raise RuntimeError("docker daemon unreachable")

        monkeypatch.setattr(h, "_bind_qualification_unit", bind)
        with pytest.raises(h.R3Error):
            h.run_qualification_sweep("FULL144", tmp_path)

    def test_resume_from_n_plus_1(self, monkeypatch: pytest.MonkeyPatch,
                                  tmp_path: Path) -> None:
        m = h.load_selection("FULL144")
        records = _qual_world(tmp_path)
        self._patch(monkeypatch, tmp_path, records)

        # pre-seed checkpoint with the first N units
        first_n = 5
        (tmp_path).mkdir(parents=True, exist_ok=True)
        progress_path = tmp_path / h.PROGRESS_NAME
        seeded = [
            {"calibration_index": i, "validation_unit_id": m["ordered_unit_ids"][i - 1],
             "result": "PASS", "classification": "PASS"}
            for i in range(1, first_n + 1)
        ]
        progress_path.write_text(json.dumps({"completed": seeded}, indent=2), encoding="utf-8")

        started: list[int] = []

        def bind(driver: Any, m2: dict[str, Any], idx: int, uid: str, root: Path) -> Any:
            started.append(idx)

            class _Runner:
                def run_unit(self, _idx: int) -> dict[str, Any]:
                    return records[idx - 1]

            return _Runner()

        monkeypatch.setattr(h, "configure_driver", lambda name, r: _fake_driver(records))
        monkeypatch.setattr(h, "disk_free_gib", lambda path=None: 300.0)
        monkeypatch.setattr(h, "_bind_qualification_unit", bind)
        monkeypatch.setenv("R4_R3_QUALIFICATION144_ROOT", str(tmp_path))

        agg = h.run_qualification_sweep("FULL144", tmp_path)
        assert started[0] == 6  # resumed at the exact next required unit (N+1)
        assert len(started) == int(h.load_selection("FULL144")["expected_count"]) - 5
        assert agg["N_EXECUTED"] == 144
        assert agg["N_PASS"] == 144

    def test_corrupt_checkpoint_stops(self, monkeypatch: pytest.MonkeyPatch,
                                      tmp_path: Path) -> None:
        m = h.load_selection("FULL144")
        records = _qual_world(tmp_path)
        self._patch(monkeypatch, tmp_path, records)

        (tmp_path).mkdir(parents=True, exist_ok=True)
        progress_path = tmp_path / h.PROGRESS_NAME
        # out-of-order / non-prefix completed entry
        progress_path.write_text(json.dumps({
            "completed": [
                {"calibration_index": 1, "validation_unit_id": m["ordered_unit_ids"][2],
                 "result": "PASS", "classification": "PASS"},
            ]
        }, indent=2), encoding="utf-8")
        with pytest.raises(h.ReceiptError):
            h.run_qualification_sweep("FULL144", tmp_path)


# ---------------------------------------------------------------------------
# H1 environment / root sanitisation
# ---------------------------------------------------------------------------
class TestEnvSanitisation:
    def test_one_effective_root_per_selection(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("R4_R3_CAL12_ROOT", r"D:\stale\cal12\root")
        monkeypatch.delenv("R4_R3_TARGETED3_ROOT", raising=False)
        t3 = h.run_root_for("TARGETED3")
        assert str(t3) == str(h.DEFAULT_ROOTS["TARGETED3"])

    def test_stale_r4_full144_root_does_not_redirect(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("R4_FULL144_RUN_ROOT", r"D:\stale\full144\root")
        cal = h.run_root_for("CAL12")
        assert str(cal) == str(h.DEFAULT_ROOTS["CAL12"])

    def test_override_root_is_effective_and_receipt_records_it(self, monkeypatch: pytest.MonkeyPatch,
                                                               tmp_path: Path) -> None:
        monkeypatch.setenv("R4_R3_TARGETED3_ROOT", str(tmp_path))
        assert h.run_root_for("TARGETED3") == tmp_path
        agg = {"N_EXECUTED": 3, "N_PASS": 3, "N_NON_PASS": 0,
               "order_preserved": True, "units": []}
        monkeypatch.setattr(h, "git_head", lambda: "HEADPLACEHOLDER1" * 8)
        receipt = h.write_receipt("TARGETED3", agg)
        assert json.loads(receipt.read_text(encoding="utf-8"))["run_root"] == str(tmp_path)

    def test_run_root_env_restored_after_sweep_error(self, monkeypatch: pytest.MonkeyPatch,
                                                     tmp_path: Path) -> None:
        monkeypatch.setenv("R4_FULL144_RUN_ROOT", "prev-value")
        monkeypatch.setattr(h, "configure_driver", lambda name, r: _fake_driver([]))
        monkeypatch.setattr(h, "disk_free_gib", lambda path=None: 300.0)
        monkeypatch.setattr(h, "load_selection", lambda name: {
            "expected_count": 3, "ordered_unit_ids": ["a", "b", "c"]})
        with pytest.raises(h.R3Error):
            h.run_selection_sweep("CAL12", tmp_path)
        assert os.environ.get("R4_FULL144_RUN_ROOT") == "prev-value"


# ---------------------------------------------------------------------------
# G1 cleanup contract
# ---------------------------------------------------------------------------
class TestCleanupContract:
    def test_removes_only_per_unit_wheelhouse(self, tmp_path: Path) -> None:
        (tmp_path / "materialized" / "unit_wheelhouse" / "u1").mkdir(parents=True)
        (tmp_path / "materialized" / "unit_wheelhouse" / "u1" / "x.whl").write_bytes(b"x")
        (tmp_path / "materialized" / "merged" / "py39").mkdir(parents=True)
        canonical = tmp_path / "canonical_store" / "wheelhouse"
        canonical.mkdir(parents=True)
        (canonical / "keep.whl").write_bytes(b"k")
        h._cleanup_unit_wheelhouse(tmp_path, "u1")
        assert not (tmp_path / "materialized" / "unit_wheelhouse" / "u1").exists()
        assert (tmp_path / "materialized" / "merged" / "py39").is_dir()
        assert (canonical / "keep.whl").is_file()

    def test_docker_volume_cleanup_remains_in_frozen_runner(self) -> None:
        runner_src = (SCRIPTS / "r4_behavioral_calibration_n12_r2.py").read_text(encoding="utf-8")
        assert "def cleanup_volume" in runner_src
        harness_src = (SCRIPTS / "r4_r3_selection_harness.py").read_text(encoding="utf-8")
        assert "remove_volume" not in harness_src


# ---------------------------------------------------------------------------
# J1 predecessor R3 receipt rejected by R3.1
# ---------------------------------------------------------------------------
class TestR31ReceiptIdentity:
    def test_r3_receipt_rejected_by_r31(self, monkeypatch: pytest.MonkeyPatch,
                                        tmp_path: Path) -> None:
        a = _auth()
        assert a["r3_release_tag"] == R31_TAG
        m = h.load_selection("TARGETED3")
        target = tmp_path / "TARGETED3"
        target.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "env-canon-r4/r3-selection/receipt/1.0",
            "selection_name": "TARGETED3",
            "release_tag": R3_TAG,  # OLD R3 release identity
            "release_head": "ade82267871de7ac01118efb077955069daabf43",
            "scientific_authority_head": a["two_head_model"]["scientific_authority_head"],
            "support_evidence_head": a["two_head_model"]["support_evidence_head"],
            "execution_code_set_hash": a["execution_code_set_hash"],
            "committed_closure_content_hash": a["committed_closure_content_hash"],
            "selection_membership_hash": m["membership_hash"],
            "selection_manifest_sha256": m["manifest_sha256"],
            "population_identity": a["population_identity"],
            "ordered_membership_hash": a["ordered_membership_hash"],
            "image_binding_hash": a["image_binding_hash"],
            "N_EXECUTED": 3, "N_PASS": 3, "N_NON_PASS": 0,
            "units": [], "zero_network": True,
        }
        (target / h.RECEIPT_NAME).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        monkeypatch.setattr(h, "run_root_for", lambda name: tmp_path / name)
        with pytest.raises(h.ReceiptError):
            h.validate_self_receipt("TARGETED3", payload, a)

    def test_r31_receipt_identity_fields(self) -> None:
        a = _auth()
        assert a["r3_release_tag"] == R31_TAG
        assert a["required_branch"] == "parallel/r4-successor-harness-r31-2026-10-16"
        # scientific authorities unchanged
        assert a["two_head_model"]["scientific_authority_head"] == "5171a4e75cfb2064e7758423c146fcd4ca9ee95c"
        assert a["two_head_model"]["support_evidence_head"] == "beeff152de2307b2067c8cd9f469542ef8200b95"
        assert a["execution_code_set_hash"] == "72d3d1262133505dd3046a78e9fc0130d004cfaf6e8ca89169b67620335584c0"


# ---------------------------------------------------------------------------
# I1 selection hash invariance
# ---------------------------------------------------------------------------
class TestSelectionHashInvariance:
    def test_membership_and_manifest_hashes_unchanged(self) -> None:
        a = _auth()
        for name, memb, man in [
            ("TARGETED3", "d39710c6101b06f963bdead27958b050ad93912ccfdf98e6af03896d56e4c2fd",
             "9626853afe91b8922288f409d93788d92f6a9e9ef613bef77cf61fdbc1a44976"),
            ("CAL12", "613557a69e43fdfe67e760bd34388f7e4aa333abec37451ff2fa21b6a6e54f87",
             "19a2ce61682b03bdd67634ea2881a09b4cc415f36a3c592db64a4ba1c2c7f430"),
            ("FULL144", "8eb4a7242e12bb03715adac5fffdea2e4340585843fc137ececd38952ad6a19e",
             "f1a3dde720ab855de39702c564427b6e4867c7019bd8ff83ff5d6f55a7866d0f"),
        ]:
            m = h.load_selection(name)
            assert m["membership_hash"] == memb
            assert m["manifest_sha256"] == man
        assert a["ordered_membership_hash"] == "8eb4a7242e12bb03715adac5fffdea2e4340585843fc137ececd38952ad6a19e"
