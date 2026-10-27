"""T12 M02-D1 receipts — isolated standard-library Option-B receipt tests."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
_spec = importlib.util.spec_from_file_location("t12_m02_receipts", _SCRIPTS / "t12_m02_receipts.py")
mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(mod)


def _body_for(classification: str) -> str:
    return mod.JUNIT_FAIL if classification == "FAILURE" else mod.JUNIT_PASS


def _mk_run_dir(arm_id: str, *, junit=None, overrides=None) -> Path:
    td = Path(tempfile.mkdtemp(prefix=f"t12m02_rx_{arm_id}_"))
    rec = mod.sample_run_receipt(arm_id, run_token="TOK-" + arm_id)
    if junit is None:
        junit = [_body_for(e["classification"]) for e in rec["junit_receipts"]]
    # declarations must match the actual bytes written (validator enforces this)
    for i, entry in enumerate(rec["junit_receipts"]):
        entry["classification"] = mod.classify_body(junit[i % len(junit)])
    mod.materialize_junit_dir(td, rec, xml_bodies=junit)
    if overrides:
        rec.update(overrides)
    mod.write_run_receipt(td, rec)
    return td


def _neg_junit() -> list[str]:
    return [mod.JUNIT_FAIL] * 9


class TestReceiptCompleteness(unittest.TestCase):
    """Positive + negative completeness cases (never silent PASS)."""

    def test_complete_run_passes(self):
        d = _mk_run_dir("RM_CSS")
        res = mod.validate_run_receipt(d)
        self.assertEqual(res["status"], "PASS", res["issues"])
        self.assertEqual(res["junit_verified"], 9)

    def test_full_reference_passes(self):
        d = _mk_run_dir("FULL_REFERENCE")
        res = mod.validate_run_receipt(d)
        self.assertEqual(res["status"], "PASS", res["issues"])

    def test_neg_requires_failures(self):
        d = _mk_run_dir("NEG")
        res = mod.validate_run_receipt(d)
        self.assertEqual(res["status"], "PASS", res["issues"])

    def test_neg_with_pass_receipts_stops(self):
        # consistent PASS bytes + PASS declarations on the NEG control arm:
        # the control expectation (9/9 FAILURE) must turn it into a STOP.
        d = _mk_run_dir("NEG", junit=[mod.JUNIT_PASS])
        res = mod.validate_run_receipt(d)
        self.assertEqual(res["status"], "STOP")
        self.assertTrue(any("expected FAILURE" in i for i in res["issues"]))

    def test_declared_vs_actual_dishonesty_stops(self):
        d = _mk_run_dir("RM_CSS", junit=[mod.JUNIT_PASS])  # consistent PASS
        rec = json.loads((d / "run_receipt.json").read_text(encoding="utf-8"))
        for e in rec["junit_receipts"]:
            e["classification"] = "FAILURE"  # lie: files actually PASS
        mod.write_run_receipt(d, rec)
        res = mod.validate_run_receipt(d)
        self.assertEqual(res["status"], "STOP")
        self.assertTrue(any("dishonesty" in i for i in res["issues"]))

    def test_partial_7_of_9_junit_stops(self):
        d = _mk_run_dir("RM_CSS")
        rec = json.loads((d / "run_receipt.json").read_text(encoding="utf-8"))
        rec["junit_receipts"] = rec["junit_receipts"][:7]
        mod.write_run_receipt(d, rec)
        res = mod.validate_run_receipt(d)
        self.assertEqual(res["status"], "STOP")
        self.assertTrue(any("!= expected 9" in i for i in res["issues"]))

    def test_missing_teardown_stops(self):
        d = _mk_run_dir("RM_CSS", overrides={"teardown_receipt": {
            "present": False, "db_deleted": False, "workspace_removed": False}})
        res = mod.validate_run_receipt(d)
        self.assertEqual(res["status"], "STOP")
        self.assertTrue(any("teardown_receipt" in i for i in res["issues"]))

    def test_non_monotonic_times_stop(self):
        d = _mk_run_dir("RM_CSS", overrides={"times": {
            "start_utc": "2026-11-02T09:00:00Z", "end_utc": "2026-11-02T08:00:00Z",
            "wall_seconds": 3600.0}})
        res = mod.validate_run_receipt(d)
        self.assertEqual(res["status"], "STOP")
        self.assertTrue(any("non-monotonic" in i for i in res["issues"]))

    def test_missing_run_receipt_is_not_run(self):
        res = mod.validate_run_receipt(Path(tempfile.mkdtemp()))
        self.assertEqual(res["status"], "NOT_RUN")

    def test_bad_db_identity_stops(self):
        d = _mk_run_dir("RM_CSS", overrides={"database": {
            "engine": "sqlite", "db_identity": "shared.db", "db_created_receipt": True}})
        res = mod.validate_run_receipt(d)
        self.assertEqual(res["status"], "STOP")
        self.assertTrue(any("db_identity" in i for i in res["issues"]))

    def test_not_measured_samplers_allowed(self):
        d = _mk_run_dir("RM_CSS", overrides={"resources": {
            "cpu_seconds": "NOT_MEASURED", "peak_ram_mb": "NOT_MEASURED",
            "disk_bytes": "NOT_MEASURED", "network_bytes": "NOT_MEASURED"}})
        res = mod.validate_run_receipt(d)
        self.assertEqual(res["status"], "PASS", res["issues"])

    def test_undeclared_junit_file_stops(self):
        d = _mk_run_dir("RM_CSS")
        (d / "junit" / "extra_file.xml").write_text(mod.JUNIT_PASS, encoding="utf-8")
        res = mod.validate_run_receipt(d)
        self.assertEqual(res["status"], "STOP")
        self.assertTrue(any("undeclared" in i for i in res["issues"]))


class TestCrossArmOptionB(unittest.TestCase):
    """Physical identity segregation across arms; bytes are never reuse proof."""

    def test_cross_arm_identical_receipt_bytes_stop(self):
        a = _mk_run_dir("SIP", junit=[mod.JUNIT_PASS])
        b = _mk_run_dir("DENSE_K3", junit=[mod.JUNIT_PASS])
        # force the two physical receipts to be byte-identical JSON
        import shutil
        shutil.copy(a / "run_receipt.json", b / "run_receipt.json")
        res = mod.validate_receipts_bundle([a, b])
        self.assertEqual(res["status"], "STOP")
        self.assertTrue(any("byte-identical physical run_receipt" in i
                            for i in res["cross_arm_identity_violations"]))

    def test_db_identity_reuse_across_arms_stops(self):
        a = _mk_run_dir("SIP")
        b = _mk_run_dir("DENSE_K3")
        shared = "opws_shared_7e42fc67_083233_ab12cd34ef56"
        mod.write_run_receipt(a, {**json.loads((a / "run_receipt.json").read_text()),
                                 "database": {"engine": "sqlite", "db_identity": shared,
                                              "db_created_receipt": True}})
        mod.write_run_receipt(b, {**json.loads((b / "run_receipt.json").read_text()),
                                 "database": {"engine": "sqlite", "db_identity": shared,
                                              "db_created_receipt": True}})
        res = mod.validate_receipts_bundle([a, b])
        self.assertEqual(res["status"], "STOP")
        self.assertTrue(any("db_identity" in i for i in res["cross_arm_identity_violations"]))

    def test_execution_id_reuse_across_arms_stops(self):
        a = _mk_run_dir("SIP")
        b = _mk_run_dir("DENSE_K3")
        mod.write_run_receipt(a, {**json.loads((a / "run_receipt.json").read_text()),
                                 "execution_id": "SAME_EXEC"})
        mod.write_run_receipt(b, {**json.loads((b / "run_receipt.json").read_text()),
                                 "execution_id": "SAME_EXEC"})
        res = mod.validate_receipts_bundle([a, b])
        self.assertEqual(res["status"], "STOP")
        self.assertTrue(any("execution_id" in i for i in res["cross_arm_identity_violations"]))

    def test_identical_junit_bytes_across_arms_is_signal_not_stop(self):
        a = _mk_run_dir("SIP", junit=[mod.JUNIT_PASS])
        b = _mk_run_dir("DENSE_K3", junit=[mod.JUNIT_PASS])
        res = mod.validate_receipts_bundle([a, b])
        self.assertEqual(res["status"], "PASS",
                         "identical JUnit bytes alone never prove physical reuse")
        self.assertTrue(res["duplicate_bytes_signals"],
                        "duplicate bytes must still be flagged as a signal")
        self.assertTrue(res["never_infer_reuse_from_identical_bytes"])

    def test_independent_arms_with_distinct_receipts_pass(self):
        a = _mk_run_dir("SIP", junit=[mod.JUNIT_PASS])
        b = _mk_run_dir("DENSE_K3", junit=[mod.JUNIT_FAIL])
        res = mod.validate_receipts_bundle([a, b])
        self.assertEqual(res["status"], "PASS", res["cross_arm_identity_violations"])


class TestHistoricalDiagnosticScoped(unittest.TestCase):
    def test_r7_diagnostic_is_marked_historical(self):
        d = _mk_run_dir("RM_CSS")
        res = mod.historical_r7_diagnostic(d)
        self.assertEqual(res["scope"], "HISTORICAL_DIAGNOSTIC_ONLY")
        self.assertTrue(res["not_m02e_evidence"])
        self.assertTrue(res["single_node_historical_scoped"])

    def test_cli_validate_run_exit_codes(self):
        d = _mk_run_dir("RM_CSS")
        self.assertEqual(mod.main(["validate-run", str(d)]), 0)
        self.assertEqual(mod.main(["validate-run", str(Path(tempfile.mkdtemp()))]), 2)
        bad = _mk_run_dir("NEG", junit=[mod.JUNIT_PASS])
        self.assertEqual(mod.main(["validate-run", str(bad)]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
