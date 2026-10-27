"""T12 M02-D1 driver — isolated standard-library tests (stdlib only, offline)."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
_spec = importlib.util.spec_from_file_location("t12_m02_driver", _SCRIPTS / "t12_m02_driver.py")
mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(mod)

FROZEN_WORKTREE_HEAD = "22d569464fdbf9d0ebda842497cc23a7a10e2237"


def _fake_worktree() -> Path:
    """Throwaway worktree with wrong HEAD so hard-stop behavior is deterministic."""
    td = Path(tempfile.mkdtemp(prefix="t12m02_drv_wt_"))
    gitdir = td / ".git"
    gitdir.mkdir()
    (gitdir / "HEAD").write_text("ref: refs/heads/x\n", encoding="utf-8")
    (gitdir / "refs/heads").mkdir(parents=True)
    (gitdir / "refs/heads" / "x").write_text("deadbeefdeadbeefdeadbeefdeadbeefdeadbeef\n",
                                             encoding="utf-8")
    return td


class TestDriverAdmissionFailClosed(unittest.TestCase):
    """Preflight fails closed with typed STOPs; no mock, no invented flags."""

    def test_missing_worktree_typed_stop(self):
        res = mod.preflight(Path(tempfile.mkdtemp()) / "absent", admission_required=False)
        self.assertIn("REQUIRED_WORKTREE_MISSING", res["hard_stops"])
        self.assertFalse(res["admission_ready"])
        self.assertEqual(res["exit_code"], 4)

    def test_drifted_worktree_typed_stop(self):
        res = mod.preflight(_fake_worktree(), admission_required=False)
        self.assertIn("FROZEN_WORKTREE_DRIFT", res["hard_stops"])
        self.assertFalse(res["admission_ready"])

    def test_input_contract_status_closed_by_d2_derivation(self):
        # M02-D2: the integration gap (no frozen classification JSON) is CLOSED
        # by the offline derivation; the preflight now reports contract status
        # and stops ONLY on missing artifacts/authorization — never on a fake gap.
        res = mod.preflight(Path(tempfile.mkdtemp()) / "absent", admission_required=False)
        self.assertIsNone(res["runner_integration_gap"])
        self.assertNotIn("RUNNER_INTEGRATION_GAP_CLASSIFICATION_INPUT_UNRESOLVED",
                         res["hard_stops"])
        self.assertIn("input_contract_status", res)
        self.assertIn("EXECUTION_NOT_AUTHORIZED", res["hard_stops"])

    def test_rd8_artifacts_required_for_ready_status(self):
        with tempfile.TemporaryDirectory() as td:
            fake_cls = Path(td) / "classification.json"
            fake_cls.write_text('{"changes": {}}', encoding="utf-8")
            res = mod.preflight(_fake_worktree(), admission_required=False,
                                classification_artifact=fake_cls,
                                test_authority_artifact=Path(td) / "authority.json")
            self.assertIn("RD8_TEST_AUTHORITY_ARTIFACT_MISSING", res["hard_stops"])
            self.assertNotEqual(res["input_contract_status"],
                                "INPUT_CONTRACT_READY_FOR_RESEARCHER_REVIEW")

    def test_no_run_subcommand_exists(self):
        with self.assertRaises(SystemExit):
            mod.main(["run", "--arm", "SIP"])  # build_parser rejects unknown subcommand

    def test_preflight_exit_4_via_cli(self):
        code = mod.main(["preflight", "--worktree", str(_fake_worktree())])
        self.assertEqual(code, 4)


class TestDriverDryRun(unittest.TestCase):
    """Dry-run emits 13 NOT_RUN rows with verified flags and pins."""

    def test_thirteen_rows_all_not_run(self):
        rows = mod.dry_run_rows(_fake_worktree())
        self.assertEqual(len(rows), 13)
        self.assertTrue(all(r["prospective_m02e_status"] == "NOT_RUN" for r in rows))
        self.assertTrue(all(r["prospective_model_usd"] == 0.0 for r in rows))
        self.assertEqual(len({r["execution_id"] for r in rows}), 13,
                         "Option B: every arm has a distinct physical execution id")

    def test_materialize_cmd_uses_only_verified_flags(self):
        allowed = {"--repo", "--parent", "--target", "--task-id", "--scope-json",
                   "--classification-json", "--dry-run"}
        for r in mod.dry_run_rows(_fake_worktree()):
            argv = r["materialize_dry_run_cmd"].split()
            flags = {a for a in argv if a.startswith("--")}
            self.assertTrue(flags <= allowed, f"unverified flag: {flags - allowed}")
            self.assertNotIn("-n", flags)

    def test_first_four_frozen_order_invariant(self):
        rows = mod.dry_run_rows(_fake_worktree())
        self.assertEqual([r["arm_id"] for r in rows[:4]],
                         ["SIP", "DENSE_K3", "DENSE_K10", "BM25_K10"])

    def test_controls_marked_derived_and_others_pinned(self):
        rows = {r["arm_id"]: r for r in mod.dry_run_rows(_fake_worktree())}
        self.assertEqual(rows["NEG"]["scope_pin_status"], "DERIVED_CONTROL")
        self.assertEqual(rows["FULL_REFERENCE"]["scope_pin_status"], "DERIVED_CONTROL")
        # without the D2 normalized artifacts the raw multi-task prediction file
        # is recorded as NOT materializer-ready (never passed as scope-json)
        self.assertEqual(rows["SIP"]["scope_pin_status"],
                         "PIN_MATCH_BUT_MULTI_TASK_SOURCE")
        # RD-8: derived proposals are NOT silently treated as historical pins
        self.assertEqual(rows["SIP"]["classification_input"],
                         "DERIVED_PROPOSED_PENDING_RD8_APPROVAL")

    def test_dry_run_cli_writes_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "DRY_RUN_MANIFEST.csv"
            code = mod.main(["dry-run", "--worktree", str(_fake_worktree()), "--out", str(out)])
            self.assertEqual(code, 0)
            self.assertTrue(out.is_file())

    def test_manifest_has_expected_header(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "m.csv"
            mod.main(["dry-run", "--worktree", str(_fake_worktree()), "--out", str(out)])
            first = out.read_text(encoding="utf-8").splitlines()[0]
            for col in ("arm_id", "scope_pin_status", "prospective_m02e_status",
                        "prospective_model_usd", "execution_id", "junit_count_plan"):
                self.assertIn(col, first)


class TestDriverRealInterfaces(unittest.TestCase):
    """Machine-dependent: byte-verifies the REAL frozen interfaces where present."""

    def test_real_frozen_preflight_when_available(self):
        wt = mod._adapt.FROZEN_WORKTREE_ROOT_DEFAULT
        if not wt.is_dir():
            self.skipTest("frozen worktree not present on this machine")
        res = mod.preflight(wt, admission_required=False)
        self.assertTrue(res["worktree_present"])
        self.assertTrue(res["worktree_head_match"])
        self.assertTrue(all(s["ok"] for s in res["engines"].values()),
                        "frozen engine scripts must byte-match stage pins")
        self.assertTrue(res["source_repo_oid_ok"],
                        "parent/target OIDs must resolve in the frozen saleor cache repo")
        pin_map = {p["arm_id"]: p for p in res["per_arm"]}
        for arm in ("SIP", "RM_CSS", "AGENT", "DENSE_K3", "BM25_K10", "GOLD",
                    "AGENTLESS_STYLE_ADAPTATION"):
            self.assertTrue(pin_map[arm]["scope_status"] in ("PIN_MATCH", "DERIVED_CONTROL"),
                            f"{arm}: {pin_map[arm]['scope_status']}")

    def test_scope_source_tags_match_frozen_pins(self):
        # structural: every non-derived arm has a 64-hex byte pin.
        for arm_id, pin in mod._adapt.ARM_SCOPE_SOURCES.items():
            if pin["kind"] == "DERIVED_CONTROL":
                continue
            self.assertEqual(len(pin["sha256"]), 64, arm_id)
        # the alias pair shares a four-field CLASS but may have distinct raw
        # prediction sources (agentless freeze vs baselines r2) — both pinned.
        self.assertIsNotNone(mod._adapt.ARM_SCOPE_SOURCES["AGENTLESS_STYLE_ADAPTATION"]["sha256"])
        self.assertIsNotNone(mod._adapt.ARM_SCOPE_SOURCES["BM25_K3"]["sha256"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
