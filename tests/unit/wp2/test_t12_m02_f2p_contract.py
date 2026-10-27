"""T12 M02-D2 F2P call contract — isolated stdlib tests.

Proves: the rendered run_state_v3 plan is source-contract-exact, per-arm
distinct, never executable, and that the D1 illustrative m3b argv is replaced
by a real per-arm plan (m3b smoke cannot run the 3-node pilot contract).
"""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
_spec = importlib.util.spec_from_file_location("t12_m02_f2p_contract", _SCRIPTS / "t12_m02_f2p_contract.py")
mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(mod)

FOUR_FROZEN = ["SIP", "DENSE_K3", "DENSE_K10", "BM25_K10"]
EXPECTED_NODES_PIN = "aa12d54639efd07fcf93efc7fa880d1c1df8f4f878d04eb6b20d27f82946b9a2"


class TestPlanShape(unittest.TestCase):
    def test_first_four_plan_contract(self):
        for arm in FOUR_FROZEN:
            plan = mod.f2p_plan_for(arm)
            self.assertFalse(plan["executable"], arm)
            self.assertEqual(plan["run_mode"], "OFFLINE_DRY_RUN_PLAN_ONLY")
            self.assertEqual(plan["engine"]["call_contract"]["era_key"], "py312")
            self.assertEqual(plan["engine"]["call_contract"]["tid"], "7e42fc67ce72")
            self.assertEqual(plan["physical_execution_contract"]["junit_count_plan"], 9)
            self.assertEqual(plan["physical_execution_contract"]["physical_test_invocations"], 9)
            self.assertEqual(plan["physical_execution_contract"]["nodes_count"], 3)
            self.assertEqual(plan["physical_execution_contract"]["repetitions"], 3)
            self.assertEqual(plan["physical_execution_contract"]["option_b"],
                             "REUSE_NOT_PERMITTED: distinct physical arm execution, DBs, "
                             "receipts, wall/resource measurements")

    def test_nodes_pin_matches_frozen(self):
        nodes = mod._adapt.F2P_NODES
        self.assertEqual(len(nodes), 3)
        self.assertEqual(mod._adapt.F2P_NODES_SHA256, EXPECTED_NODES_PIN)
        plan = mod.f2p_plan_for("SIP")
        self.assertEqual(plan["engine"]["call_contract"]["test_files"], nodes)
        self.assertEqual(plan["engine"]["call_contract"]["test_files_pin"], EXPECTED_NODES_PIN)

    def test_wrong_node_list_rejected(self):
        with self.assertRaises(ValueError):
            mod.f2p_plan_for("SIP", node_list=["saleor/app/tests/test_validators.py::x"])

    def test_unknown_arm_rejected(self):
        with self.assertRaises(ValueError):
            mod.f2p_plan_for("NOT_AN_ARM")

    def test_required_inputs_never_fabricated(self):
        plan = mod.f2p_plan_for("SIP")
        cc = plan["engine"]["call_contract"]
        self.assertTrue(cc["worktree_linux"].startswith("REQUIRED_INPUT_FROM_"))
        self.assertTrue(cc["install_fragment"].startswith("REQUIRED_INPUT_FROM_"))
        self.assertTrue(isinstance(cc["isolated"], str) and cc["isolated"].startswith("REQUIRED_INPUT_FROM_"))
        self.assertEqual(cc["locked_dev_fragment"], "echo NO_LOCKED_DEV_GROUP")
        self.assertEqual(cc["timeout_s"], 7200)

    def test_m3b_smoke_limitation_documented_honestly(self):
        plan = mod.f2p_plan_for("SIP")
        self.assertEqual(plan["m3b_smoke_limitation"]["smoke_junit"], 3)
        self.assertEqual(plan["m3b_smoke_limitation"]["smoke_nodes"], 1)
        self.assertIn("never parses argv positionals", plan["m3b_smoke_limitation"]["why_not_pilot_contract"])

    def test_per_arm_distinct_identity(self):
        with tempfile.TemporaryDirectory() as td:
            plans = [mod.f2p_plan_for(arm["arm_id"], out_root=Path(td)) for arm in mod._adapt.load_arms()]
        ids = [p["execution_id"] for p in plans]
        self.assertEqual(len(set(ids)), len(plans), "Option B: distinct execution ids per arm")
        states = [p["engine"]["call_contract"]["state"] for p in plans]
        self.assertEqual(len(set(states)), len(plans), "per-arm state labels must differ")
        dbs = [p["physical_execution_contract"]["db_identity"]["legacy_mode"] for p in plans]
        self.assertEqual(len(set(dbs)), len(plans), "per-arm DB identities must differ")


class TestMaterializerArgv(unittest.TestCase):
    def test_argv_built_only_from_frozen_flags_and_d2_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "scopes").mkdir()
            (root / "scopes" / "scope_SIP.json").write_text('{"scope": []}\n', encoding="utf-8")
            cls = root / "classification.json"
            auth = root / "authority.json"
            cls.write_text('{"changes": {}}\n', encoding="utf-8")
            auth.write_text('{"changed_paths": [], "test_paths": [], "source": "census"}\n',
                            encoding="utf-8")
            r = mod.render_materializer_argv(
                "SIP", worktree=Path("."), source_repo=Path("."),
                scope_artifacts_dir=root / "scopes",
                classification_artifact=cls, test_authority_artifact=auth)
        argv = r["argv"]
        self.assertIn("--scope-json", argv)
        self.assertTrue(any("scope_SIP.json" in u for u in argv))
        self.assertIn("--classification-json", argv)
        self.assertTrue(any("classification.json" in u for u in argv))
        self.assertIn("--test-authority-json", argv)
        self.assertTrue(any("authority.json" in u for u in argv))
        self.assertIn("--dry-run", argv)
        self.assertFalse(r["executable"])
        # every flag comes from the frozen parser set
        flags = {a for a in argv if a.startswith("--")}
        self.assertTrue(flags <= {"--repo", "--parent", "--target", "--task-id",
                                  "--scope-json", "--classification-json",
                                  "--test-authority-json", "--dry-run"})

    def test_missing_artifacts_are_typed_markers_not_inventions(self):
        r = mod.render_materializer_argv("SIP", worktree=Path("."), source_repo=Path("."),
                                        scope_artifacts_dir=None,
                                        classification_artifact=None,
                                        test_authority_artifact=None)
        banned = [u for u in r["argv"] if u.startswith("REQUIRED_INPUT_FROM_")]
        self.assertTrue(any("SCOPE_NORMALIZER" in u for u in banned))
        self.assertTrue(any("RD8_DERIVATION" in u for u in banned))


if __name__ == "__main__":
    unittest.main(verbosity=2)
