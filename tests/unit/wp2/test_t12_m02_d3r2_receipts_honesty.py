"""T12 M02-D3-R2 — RED tests for receipt/bundle HONESTY (offline).

Mission: T12_M02_D3R2_OPTION_B_PROCESS_20261028.  These tests encode the
source-grounded dishonesty defects found in the committed D3-R1 code:

  * ``resources.network_bytes = 0`` was emitted without any sampler — an
    unmeasured value must be ``NOT_MEASURED`` (or numeric with sampler
    provenance), never a bare 0;
  * live receipts were seeded from ``sample_run_receipt`` (a TEST/demo
    fixture) and partly overwritten — any fixture marker surviving in a live
    receipt is a STOP;
  * the bundle scan treated a bare integer PID as process identity — a
    recycled PID with genuinely distinct verified process BIRTHS is two
    distinct processes, and an identical pid + identical verified birth is a
    shared-process violation (Option-B STOP).

Test doubles only; no WSL/Docker/engine invocation.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"

for _mod in ("t12_m02_receipts", "t12_m02_d3r2_identity"):
    _spec = importlib.util.spec_from_file_location(_mod, _SCRIPTS / f"{_mod}.py")
    _m = importlib.util.module_from_spec(_spec)
    assert _spec and _spec.loader
    sys.modules[_mod] = _m
    _spec.loader.exec_module(_m)
    if _mod == "t12_m02_receipts":
        receipts = _m
    else:
        identity = _m


def _build_run_dir(receipt: dict, junit_bodies: list[str] | None = None) -> Path:
    """Write one valid-shaped run_dir with a receipt; returns the dir."""
    td = Path(tempfile.mkdtemp())
    (td / receipts.RECEIPT_FILENAME).write_text(
        json.dumps(receipt, indent=2, default=str), encoding="utf-8")
    receipts.materialize_junit_dir(td, receipt, xml_bodies=junit_bodies)
    return td


def _live_like_receipt(arm: str = "RM_CSS", **overrides) -> dict:
    """A structurally LIVE receipt (measured fields; NOT the demo fixture)."""
    import hashlib as _h
    arm_id = arm
    rec = receipts.sample_run_receipt(arm_id=arm_id, run_token=f"D3R2-TEST-{arm_id}")
    db_suffix = _h.sha256(arm_id.encode()).hexdigest()[:20]
    rec.update({
        "times": {"start_utc": "2026-11-02T09:30:00Z", "end_utc": "2026-11-02T09:30:42Z",
                  "monotonic": True, "wall_seconds": 42.0},
        "process": {
            "pid": 77123,
            "driver_argv": ["py", "-3.11", "t12_m02_d3r2_worker.py", "--arm", arm_id],
            "nonce": identity.new_nonce(),
            "container_oci_id": identity.PINNED_PY312_OCI_ID,
            "process_birth": identity.span_witness(
                nonce=identity.new_nonce(), pid=77123, parent_pid=8120,
                argv=["py", "-3.11", "t12_m02_d3r2_worker.py", "--arm", arm_id],
                worker_script_path=None,
                monotonic_start_ns=900000000000000 + hash(arm_id) % 1000,
                monotonic_end_ns=900000000000042 + hash(arm_id) % 1000,
                start_utc="2026-11-02T09:30:00Z", end_utc="2026-11-02T09:30:42Z",
                exit_code=0),
        },
        "container": {"container_instance_status": "CONTAINER_INSTANCE_NOT_MEASURED"},
        "database": {"engine": "postgres (isolated PG fixture)", "db_identity": (
            f"opws_m3b_7e42fc67_093042_{db_suffix}"),
            "db_created_receipt": True},
        "resources": {
            "cpu_seconds": "NOT_MEASURED", "peak_ram_mb": "NOT_MEASURED",
            "disk_bytes": "NOT_MEASURED", "network_bytes": "NOT_MEASURED",
            "sampler": "NOT_MEASURED",
        },
        "host": {"hostname": "TEST-HOSTNAME", "os": "WSL2/Windows"},
        "environment": {"environment_id": "live-env-7e42fc67ce72-20261028"},
        "pinned_image": {"image": "opws-py312-isolated",
                         "oci_id": identity.PINNED_PY312_OCI_ID,
                         "resolved_by": "frozen resolve_runtime_image (engine first fail-closed step)"},
        "teardown_receipt": {"present": True, "db_deleted": True,
                             "path": "post_run_db_scan.json",
                             "post_run_db_scan_sha256": "0" * 64},
        "materialize_provenance": rec["materialize_provenance"],
    })
    rec.update(overrides)
    return rec


class TestReceiptHonestyNetworkZero(unittest.TestCase):
    def test_unmeasured_zero_network_without_sampler_is_rejected(self):
        """RED: the D3-R1 'network_bytes: 0' with no sampler must STOP."""
        rec = _live_like_receipt()
        rec["resources"]["network_bytes"] = 0
        rec["resources"]["sampler"] = "NOT_MEASURED"
        rd = _build_run_dir(rec)
        res = receipts.validate_run_receipt(rd)
        joined = " | ".join(res.get("issues") or [])
        self.assertIn("ZERO_UNMEASURED_NETWORK", joined)

    def test_measured_network_bytes_requires_sampler_provenance(self):
        rec = _live_like_receipt()
        rec["resources"]["network_bytes"] = 12345
        rec["resources"]["sampler"] = "host sampler v1 (pinned, measured)"
        rd = _build_run_dir(rec)
        res = receipts.validate_run_receipt(rd)
        self.assertEqual(res["status"], "PASS", res.get("issues"))  # junit PASS default


class TestReceiptHonestyFixtureMarkers(unittest.TestCase):
    def test_live_receipt_rejects_fixture_seeded_values(self):
        """Any field still carrying sample_run_receipt demo values must STOP."""
        rec = receipts.sample_run_receipt()  # full fixture
        markers = identity.detect_synthetic_fixture_fields(rec)
        self.assertTrue(markers, "fixture receipt must expose markers")
        with self.assertRaises(ValueError):
            identity.assert_live_receipt(rec)

    def test_clean_live_receipt_has_no_fixture_markers(self):
        rec = _live_like_receipt()
        self.assertEqual(identity.detect_synthetic_fixture_fields(rec), [])

    def test_receipt_builder_uses_live_constructor_not_fixture_seed(self):
        """The D3-R2 construction path must go through the live builder; the
        live builder never writes network_bytes 0 (policy function)."""
        val = identity.live_network_policy(None, None)
        self.assertEqual(val, "NOT_MEASURED")
        self.assertEqual(identity.live_network_policy(0, None), "NOT_MEASURED")
        self.assertEqual(identity.live_network_policy(512, "sampler v1"), 512)


class TestBundleProcessIdentity(unittest.TestCase):
    def _witness_for(self, arm: str, pid: int, birth: str, nonce: str, mono: int) -> dict:
        return {
            "schema": identity.WITNESS_SCHEMA, "nonce": nonce, "pid": pid,
            "parent_pid": 8120, "argv": ["py", "worker.py", "--arm", arm],
            "argv_digest": identity.argv_digest(["py", "worker.py", "--arm", arm]),
            "worker_script_sha256": "w" * 64,
            "process_birth": {
                "monotonic_start_ns": mono, "monotonic_end_ns": mono + 42,
                "os_start": {"status": "MEASURED", "os_start_utc": birth}},
            "times": {"start_utc": birth, "end_utc": birth}, "exit_code": 0,
        }

    def test_identical_pid_and_identical_birth_is_shared_execution_stop(self):
        w = self._witness_for("NEG", 5000, "2026-11-02T09:30:00.000Z", "n1", 100)
        w2 = self._witness_for("FULL_REFERENCE", 5000, "2026-11-02T09:30:00.000Z", "n2", 100)
        res = identity.bundle_identity_check([("NEG", w), ("FULL_REFERENCE", w2)])
        self.assertEqual(res["status"], "STOP")
        self.assertTrue(any("SHARED_PROCESS" in i for i in res["issues"]))

    def test_recycled_pid_with_distinct_verified_births_is_two_processes(self):
        """RED: a recycled OS pid with genuinely distinct verified process
        births must NOT be flagged as reuse; it is two distinct processes."""
        w1 = self._witness_for("NEG", 5000, "2026-11-02T09:00:00.000Z", "n1", 100)
        w2 = self._witness_for("FULL_REFERENCE", 5000, "2026-11-02T10:00:00.000Z", "n2", 200)
        res = identity.bundle_identity_check([("NEG", w1), ("FULL_REFERENCE", w2)])
        self.assertEqual(res["status"], "PASS")
        self.assertTrue(any("PID_RECYCLED_DISTINCT_BIRTH" in s for s in res["signals"]))

    def test_replayed_nonce_is_stop(self):
        w1 = self._witness_for("NEG", 5000, "2026-11-02T09:30:00.000Z", "same", 100)
        w2 = self._witness_for("FULL_REFERENCE", 5100, "2026-11-02T09:31:00.000Z", "same", 200)
        res = identity.bundle_identity_check([("NEG", w1), ("FULL_REFERENCE", w2)])
        self.assertEqual(res["status"], "STOP")
        self.assertTrue(any("NONCE_REUSE" in i for i in res["issues"]))

    def test_same_child_instance_across_two_arms_is_stop(self):
        """A worker 'running' two arms (same pid, same birth, same nonce)."""
        w = self._witness_for("NEG", 7000, "2026-11-02T09:30:00.000Z", "single", 300)
        res = identity.bundle_identity_check([("NEG", dict(w)), ("RM_CSS", dict(w))])
        self.assertEqual(res["status"], "STOP")


class TestWitnessValidation(unittest.TestCase):
    def test_validate_witness_pass(self):
        w = _live_like_receipt()["process"]["process_birth"]
        w.update({"schema": identity.WITNESS_SCHEMA, "nonce": identity.new_nonce(),
                  "pid": 1, "parent_pid": 1, "argv": ["x"], "argv_digest": "0" * 64,
                  "exit_code": 0,
                  "times": {"start_utc": "2026-11-02T09:30:00Z", "end_utc": "2026-11-02T09:30:42Z"}})
        res = identity.validate_witness(w)
        self.assertEqual(res["status"], "PASS")

    def test_validate_witness_rejects_invented_birth(self):
        w = _live_like_receipt()["process"]["process_birth"]
        w.update({"schema": identity.WITNESS_SCHEMA, "nonce": identity.new_nonce(),
                  "pid": 1, "parent_pid": 1, "argv": ["x"], "argv_digest": "0" * 64,
                  "exit_code": 0, "times": {"start_utc": "x", "end_utc": "y"}})
        w["times"] = {}
        res = identity.validate_witness(w)
        self.assertEqual(res["status"], "STOP")


if __name__ == "__main__":
    unittest.main()
