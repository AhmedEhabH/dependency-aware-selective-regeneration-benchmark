"""T12 M02-D2 RD-8 classification provenance — isolated stdlib tests + real data.

Verifies: frozen status parser semantics, census->frozen mapping, rename /
unsupported-status fail-closed behavior, the COMPLETE change-set cross-check,
and — on this host — the real parent->target derivation against the frozen
saleor cache + census (byte-pinned parent/target OIDs).
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
_MOD_NAME = "t12_m02_classification_provenance"
_spec = importlib.util.spec_from_file_location(_MOD_NAME, _SCRIPTS / f"{_MOD_NAME}.py")
mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(mod)

SCH = importlib.util.spec_from_file_location("t12_m02_materializer_schema", _SCRIPTS / "t12_m02_materializer_schema.py")
schema = importlib.util.module_from_spec(SCH)
assert SCH and SCH.loader
SCH.loader.exec_module(schema)

TASK = "saleor-rc-7e42fc67ce72"

CENSUS_RECORDS = [
    {"path": "CHANGELOG.md", "status": "modified", "test_file": False},
    {"path": "saleor/app/installation_utils.py", "status": "modified", "test_file": False},
    {"path": "saleor/app/tests/test_app_commands.py", "status": "modified", "test_file": True},
]


class TestStatusParser(unittest.TestCase):
    def test_statuses_are_frozen_set(self):
        self.assertEqual(schema.FROZEN_STATUSES, ("M", "D", "A", "R_OLD", "R_NEW"))

    def test_parse_m_d_a(self):
        fields = [b"M", b"a.py", b"D", b"b.py", b"A", b"c.py", b""]
        out = schema.parse_name_status_z(fields)
        self.assertEqual(out, {"a.py": "M", "b.py": "D", "c.py": "A"})

    def test_parse_rename_pair(self):
        fields = [b"R100", b"old.py", b"new.py", b""]
        out = schema.parse_name_status_z(fields)
        self.assertEqual(out, {"old.py": "R_OLD", "new.py": "R_NEW"})

    def test_unsupported_statuses_fail_closed(self):
        for tok in (b"T", b"C", b"U", b"X", b"B"):
            with self.assertRaises(schema.SchemaError):
                schema.parse_name_status_z([tok, b"p.py", b""])

    def test_truncated_record_fails_closed(self):
        with self.assertRaises(schema.SchemaError):
            schema.parse_name_status_z([b"M"])  # missing path field
        with self.assertRaises(schema.SchemaError):
            schema.parse_name_status_z([b"R100", b"old.py"])  # missing new-side field
        # (an empty trailing field is skipped EXACTLY as the frozen parser does;
        #  an empty path is then rejected by the canonical rule)


class TestCensusMapping(unittest.TestCase):
    def test_census_status_mapping_to_frozen(self):
        out = schema.census_changes_map(CENSUS_RECORDS)
        self.assertEqual(out["CHANGELOG.md"], "M")
        self.assertEqual(out["saleor/app/installation_utils.py"], "M")
        self.assertEqual(out["saleor/app/tests/test_app_commands.py"], "M")

    def test_unknown_census_status_fails_closed(self):
        with self.assertRaises(schema.SchemaError):
            schema.census_changes_map([{"path": "x.py", "status": "weird", "test_file": False}])

    def test_renamed_without_side_authority_fails_closed(self):
        recs = [{"path": "pair", "status": "renamed", "test_file": False}]
        with self.assertRaises(schema.SchemaError):
            schema.census_changes_map(recs)
        with self.assertRaises(schema.SchemaError):
            schema.build_test_path_authority(recs)
        ok = schema.build_test_path_authority(recs, rename_sides={
            "pair": ("old.py", "new.py", False, True)})
        self.assertEqual(set(ok["changed_paths"]), {"old.py", "new.py"})
        self.assertEqual(ok["test_paths"], ["new.py"])
        self.assertEqual(ok["source"], "census")

    def test_test_path_authority_flags(self):
        auth = schema.build_test_path_authority(CENSUS_RECORDS)
        self.assertEqual(auth["changed_paths"], ["CHANGELOG.md",
                                                 "saleor/app/installation_utils.py",
                                                 "saleor/app/tests/test_app_commands.py"])
        self.assertEqual(auth["test_paths"], ["saleor/app/tests/test_app_commands.py"])


class TestClassificationNormalization(unittest.TestCase):
    def test_complete_change_set_json_schema(self):
        cls = {"CHANGELOG.md": "M", "saleor/app/tests/test_app_commands.py": "M"}
        canonical, invalid = schema.normalize_classification(cls)
        self.assertEqual(canonical, cls)
        self.assertEqual(invalid, [])

    def test_unknown_status_rejected(self):
        _, invalid = schema.normalize_classification({"a.py": "Q"})
        self.assertEqual(len(invalid), 1)
        self.assertIn("UNSUPPORTED_STATUS", invalid[0]["reason"])

    def test_invalid_path_rejected(self):
        _, invalid = schema.normalize_classification({"C:/abs.py": "M"})
        self.assertEqual(len(invalid), 1)
        self.assertIn("INVALID_PATH", invalid[0]["reason"])


class TestCrossCheck(unittest.TestCase):
    def test_equal_maps(self):
        git = {"a.py": "M", "b.py": "D"}
        cen = {"a.py": "M", "b.py": "D"}
        x = mod.cross_check(git, cen)
        self.assertTrue(x["equal"])
        self.assertFalse(any(x["diff"].values()))

    def test_diff_detected(self):
        x = mod.cross_check({"a.py": "M"}, {"a.py": "M", "b.py": "A"})
        self.assertFalse(x["equal"])
        self.assertEqual(x["diff"]["only_in_census"], ["b.py"])
        x2 = mod.cross_check({"a.py": "M"}, {"a.py": "D"})
        self.assertFalse(x2["equal"])
        self.assertIn("a.py", x2["diff"]["status_mismatch"])


def _git_available() -> bool:
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=False, timeout=20)
        return True
    except Exception:
        return False


class TestRealDerivationOnThisHost(unittest.TestCase):
    """Runs on Ahmed's host (2026-10-27): frozen saleor cache + frozen census."""

    def test_real_derivation_matches_frozen_reference_protocol(self):
        repo = Path(r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\dist\pilot-repo-cache\saleor")
        census = Path("research/wp2/wp2_saleor_main297_census_2026-09-22.json")
        if not repo.is_dir() or not census.is_file():
            self.skipTest("frozen saleor cache / census not present on this machine")
        parent = "798632158394c9f2911e6d36e8e424fd55007dc4"
        target = "7e42fc67ce72770720440781fc83685a48bd91b8"
        census_data = json.loads(census.read_text(encoding="utf-8"))
        real_records = next(r["changed_paths"] for r in census_data["tasks"]
                            if r.get("task_id") == TASK)
        self.assertEqual(len(real_records), 8)
        with tempfile.TemporaryDirectory() as td:
            receipt = mod.build_classification_artifacts(
                repo=repo, parent=parent, target=target,
                census_records=real_records, task_id=TASK, out_dir=Path(td))
            self.assertEqual(receipt["derivation_status"], mod.DERIVATION_STATUS)
            self.assertTrue(receipt["cross_check"]["equal"])
            self.assertEqual(receipt["changed_path_count"], 8)
            self.assertEqual(receipt["git_statuses"], ["M"])
            self.assertEqual(receipt["census_test_paths_count"], 4)
            self.assertFalse(receipt["frozen"])
            cls = json.loads(Path(receipt["classification_artifact"]).read_text(encoding="utf-8"))
            self.assertEqual(set(cls.keys()), {"changes"})
            self.assertEqual(len(cls["changes"]), 8)
            for status in cls["changes"].values():
                self.assertIn(status, schema.FROZEN_STATUSES)
            authority = json.loads(Path(receipt["test_authority_artifact"]).read_text(encoding="utf-8"))
            self.assertEqual(authority["source"], "census")
            self.assertEqual(len(authority["test_paths"]), 4)
            self.assertEqual(set(cls["changes"]), set(authority["changed_paths"]),
                             "classification must be the COMPLETE change set == authority")

    @unittest.skipUnless(_git_available(), "git not available")
    def test_real_scenario_mismatch_fails_closed(self):
        """A census that does NOT match the frozen parent->target diff must STOP."""
        repo = Path(r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\dist\pilot-repo-cache\saleor")
        if not repo.is_dir():
            self.skipTest("frozen saleor cache not present on this machine")
        bad_records = CENSUS_RECORDS + [
            {"path": "saleor/not_really_changed.py", "status": "modified", "test_file": False}]
        with tempfile.TemporaryDirectory() as td, self.assertRaises(mod.ClassificationError) as ctx:
            mod.build_classification_artifacts(
                repo=repo, parent="798632158394c9f2911e6d36e8e424fd55007dc4",
                target="7e42fc67ce72770720440781fc83685a48bd91b8",
                census_records=bad_records, task_id=TASK, out_dir=Path(td))
        self.assertIn("CROSS_CHECK_FAILED", str(ctx.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
