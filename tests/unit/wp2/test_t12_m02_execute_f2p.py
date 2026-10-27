"""T12 M02-D3 real per-arm F2P execution bridge — fail-closed unit tests.

Proves (all at unit level; mocks ONLY here, never in the real execution path):
- run/preflight gates are fail-closed with typed stops
- RD-8 decision artifact absence is PENDING (never self-approved)
- changed matrix/plan hash, invalid arm, wrong windows, undeclared model API,
  budget > authorization cap, alias-arm physical replica reuse, oracle-boundary
  separation, and partial engine failures all STOP/raise typed reasons
- the D3 runner made the same frozen-plan/source paths mandatory in every mode
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
_MOD = "t12_m02_execute_f2p"

_spec = importlib.util.spec_from_file_location(_MOD, _SCRIPTS / "t12_m02_execute_f2p.py")
mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(mod)

FROZEN_WORKTREE = mod._adapt.FROZEN_WORKTREE_ROOT_DEFAULT
# Machine-dependent inputs are supplied ONLY via environment (no private
# machine paths in the public repo).  Absent -> the dependent tests self-skip.
MATRIX = Path(os.environ["T12_M02_MATRIX"]) if os.environ.get("T12_M02_MATRIX") else None
PLAN = Path(os.environ["T12_M02_PLAN"]) if os.environ.get("T12_M02_PLAN") else None
HAS_FROZEN = (
    FROZEN_WORKTREE.is_dir() and MATRIX is not None and MATRIX.is_file() and PLAN is not None and PLAN.is_file()
)

RD8_OK = {
    "schema": "t12_m02_rd8_pilot_decision_v1",
    "decision": "ADOPT_PILOT_ONLY",
    "signed_by": "researcher",
    "signed_at_utc": "2026-11-10T00:00:00Z",
    "classification_sha256": mod.DERIVED_CLASSIFICATION_SHA256,
    "test_authority_sha256": mod.DERIVED_TEST_AUTHORITY_SHA256,
}
AUTH_OK = {
    "schema": "t12_m02_execution_authorization_v1",
    "grant": "RD9_F2P_PILOT",
    "authorized_arms": ["SIP", "NEG", "FULL_REFERENCE", "RM_CSS"],
    "exclusivity_window": {"start_utc": "2026-11-10T08:00:00Z", "end_utc": "2026-11-10T20:00:00Z"},
    "max_wall_s": 7200,
    "recorded_by": "researcher",
}
BUDGET_OK = {
    "benchmark_api_model_usd": 0.0,
    "request_count": 0,
    "exclusivity_slots": ["2026-11-10T08:00:00Z/2026-11-10T20:00:00Z"],
}


def write_json(p: Path, payload: object) -> Path:
    p.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return p


class TestRd8DecisionGate(unittest.TestCase):
    def test_missing_rd8_decision_is_pending(self):
        r = mod.validate_rd8_decision(None)
        self.assertEqual(r["status"], "RD8_PENDING")
        self.assertFalse(r["present"])

    def test_missing_rd8_artifact_path_is_pending(self):
        r = mod.validate_rd8_decision(Path("does-not-exist.json"))
        self.assertEqual(r["status"], "RD8_PENDING")

    def test_rd8_wrong_schema_stops(self):
        with tempfile.TemporaryDirectory() as td:
            p = write_json(Path(td) / "d.json", {"schema": "other", "decision": "ADOPT_PILOT_ONLY"})
            r = mod.validate_rd8_decision(p)
            self.assertEqual(r["status"], "STOP")

    def test_rd8_decision_must_be_adopt_pilot_only(self):
        with tempfile.TemporaryDirectory() as td:
            p = write_json(Path(td) / "d.json", dict(RD8_OK, decision="REJECT"))
            r = mod.validate_rd8_decision(p)
            self.assertEqual(r["status"], "STOP")

    def test_rd8_decision_must_pin_derived_oracle_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            p = write_json(Path(td) / "d.json", dict(RD8_OK, classification_sha256="0" * 64))
            r = mod.validate_rd8_decision(p)
            self.assertEqual(r["status"], "STOP")
            self.assertIn("classification", r["reason"])

    def test_rd8_decision_missing_signature_stops(self):
        with tempfile.TemporaryDirectory() as td:
            p = write_json(
                Path(td) / "d.json", {k: v for k, v in RD8_OK.items() if k not in ("signed_by", "signed_at_utc")}
            )
            r = mod.validate_rd8_decision(p)
            self.assertEqual(r["status"], "STOP")

    def test_rd8_adopt_with_all_pins_passes_structure(self):
        with tempfile.TemporaryDirectory() as td:
            r = mod.validate_rd8_decision(write_json(Path(td) / "d.json", RD8_OK))
            self.assertEqual(r["status"], "ADOPT_PILOT_ONLY")


class TestAuthorizationGate(unittest.TestCase):
    def test_missing_authorization_not_authorized(self):
        r = mod.validate_authorization(None, mod.PILOT_ARMS)
        self.assertEqual(r["status"], "EXECUTION_NOT_AUTHORIZED")

    def test_wrong_grant_stops(self):
        with tempfile.TemporaryDirectory() as td:
            r = mod.validate_authorization(
                write_json(Path(td) / "a.json", dict(AUTH_OK, grant="RDX_UNKNOWN")), mod.PILOT_ARMS
            )
            self.assertEqual(r["status"], "STOP")

    def test_missing_exclusivity_window_stops(self):
        with tempfile.TemporaryDirectory() as td:
            payload = dict(AUTH_OK)
            payload.pop("exclusivity_window")
            r = mod.validate_authorization(write_json(Path(td) / "a.json", payload), mod.PILOT_ARMS)
            self.assertEqual(r["status"], "STOP")
            self.assertIn("exclusivity", r["reason"])

    def test_requested_arms_exceeding_authorization_stop(self):
        with tempfile.TemporaryDirectory() as td:
            payload = dict(AUTH_OK, authorized_arms=["SIP"])
            r = mod.validate_authorization(write_json(Path(td) / "a.json", payload), mod.PILOT_ARMS)
            self.assertEqual(r["status"], "STOP")

    def test_authorized_arms_must_be_pilot_subset(self):
        with tempfile.TemporaryDirectory() as td:
            payload = dict(AUTH_OK, authorized_arms=["SIP", "GOLD"])
            r = mod.validate_authorization(write_json(Path(td) / "a.json", payload), mod.PILOT_ARMS)
            self.assertEqual(r["status"], "STOP")

    def test_empty_authorized_arms_stops(self):
        with tempfile.TemporaryDirectory() as td:
            r = mod.validate_authorization(
                write_json(Path(td) / "a.json", dict(AUTH_OK, authorized_arms=[])), mod.PILOT_ARMS
            )
            self.assertEqual(r["status"], "STOP")


class TestBudgetWindowGate(unittest.TestCase):
    def _auth(self) -> dict:
        return {"max_wall_s": 7200}

    def test_zero_api_budget_ok(self):
        with tempfile.TemporaryDirectory() as td:
            r = mod.validate_budget(write_json(Path(td) / "b.json", BUDGET_OK), 3600, self._auth())
            self.assertEqual(r["status"], "OK")

    def test_nonzero_model_usd_is_undeclared_api_call(self):
        with tempfile.TemporaryDirectory() as td:
            r = mod.validate_budget(
                write_json(Path(td) / "b.json", dict(BUDGET_OK, benchmark_api_model_usd=1.5)), 3600, self._auth()
            )
            self.assertEqual(r["status"], "STOP")

    def test_nonzero_request_count_stops(self):
        with tempfile.TemporaryDirectory() as td:
            r = mod.validate_budget(
                write_json(Path(td) / "b.json", dict(BUDGET_OK, request_count=3)), 3600, self._auth()
            )
            self.assertEqual(r["status"], "STOP")
            self.assertIn("request_count", r["reason"])

    def test_wall_cap_over_authorization_cap_stops(self):
        with tempfile.TemporaryDirectory() as td:
            r = mod.validate_budget(write_json(Path(td) / "b.json", BUDGET_OK), 9000, self._auth())
            self.assertEqual(r["status"], "STOP")

    def test_missing_wall_cap_stops(self):
        with tempfile.TemporaryDirectory() as td:
            r = mod.validate_budget(write_json(Path(td) / "b.json", BUDGET_OK), None, self._auth())
            self.assertEqual(r["status"], "STOP")


class TestIdentityAndOracleBoundary(unittest.TestCase):
    def test_unknown_arm_rejected(self):
        with self.assertRaises(ValueError):
            mod.arms_to_run("BOGUS_ARM", False)

    def test_alias_pair_distinct_physical_identity(self):
        # AGENTLESS_STYLE_ADAPTATION + BM25_K3 are the ALLOWED alias pair but
        # Option B forbids physical reuse: distinct execution id, db, tree plan.
        row = mod._adapt.load_arms()
        by_arm = {a["arm_id"]: a for a in row}
        self.assertEqual(
            by_arm["AGENTLESS_STYLE_ADAPTATION"]["effective_tree_oid"], by_arm["BM25_K3"]["effective_tree_oid"]
        )  # same tree oid
        with tempfile.TemporaryDirectory() as td:
            wt = {
                "AGENTLESS_STYLE_ADAPTATION": "/root/m19b_r3_20261024/wt_t_AGENTLESS",
                "BM25_K3": "/root/m19b_r3_20261024/wt_t_BM25_K3",
            }
            p1 = mod.physical_plan_for(
                "AGENTLESS_STYLE_ADAPTATION", matrix_by_arm=by_arm, worktrees=wt, out_root=Path(td) / "o"
            )
            p2 = mod.physical_plan_for("BM25_K3", matrix_by_arm=by_arm, worktrees=wt, out_root=Path(td) / "o")
        self.assertNotEqual(p1["execution_id"], p2["execution_id"])
        self.assertNotEqual(p1["db_identity"]["legacy_mode"], p2["db_identity"]["legacy_mode"])
        self.assertNotEqual(p1["worktree_linux"], p2["worktree_linux"])
        self.assertNotEqual(p1["receipt_paths"]["run_receipt"], p2["receipt_paths"]["run_receipt"])

    def test_selector_never_receives_classification_or_test_authority(self):
        # The oracle boundary: derived classification/test-authority appear
        # ONLY in the materializer argv (evaluation/materializer-only).  The
        # engine call (run_state_v3) and its kwargs never carry them.
        row = {a["arm_id"]: a for a in mod._adapt.load_arms()}
        with tempfile.TemporaryDirectory() as td:
            wt = {"SIP": "/root/m19b_r3_20261024/wt_t_SIP"}
            plan = mod.physical_plan_for("SIP", matrix_by_arm=row, worktrees=wt, out_root=Path(td) / "o")
        argv = " ".join(plan["materializer_argv"]["argv"])
        # materializer (oracle-side) may receive them:
        self.assertIn("--classification-json", argv)
        self.assertIn("--test-authority-json", argv)
        # engine call carries only frozen callback fields, no oracle artifacts:
        kwargs = plan["run_state_v3"]["kwargs"]
        self.assertNotIn("classification", kwargs)
        self.assertNotIn("test_authority", kwargs)
        self.assertNotIn("classification_json", kwargs)
        self.assertNotIn("test_authority_json", kwargs)
        self.assertEqual(kwargs["test_files"], mod._adapt.F2P_NODES)

    def test_wrong_node_oracle_never_leaks(self):
        # physical plan's node pin must equal the frozen R7 node pin; the plan
        # records that the engine consumes ONLY those nodes.
        row = {a["arm_id"]: a for a in mod._adapt.load_arms()}
        with tempfile.TemporaryDirectory() as td:
            wt = {"NEG": "/root/m19b_r3_20261024/wt_t_NEG"}
            plan = mod.physical_plan_for("NEG", matrix_by_arm=row, worktrees=wt, out_root=Path(td) / "o")
        self.assertEqual(plan["run_state_v3"]["kwargs"]["test_files_pin"], mod._adapt.F2P_NODES_SHA256)
        self.assertEqual(len(plan["run_state_v3"]["kwargs"]["test_files"]), 3)

    def test_materializer_argv_uses_only_frozen_parser_flags(self):
        row = {a["arm_id"]: a for a in mod._adapt.load_arms()}
        with tempfile.TemporaryDirectory() as td:
            wt = {"DENSE_K3": "/root/m19b_r3_20261024/wt_t_DENSE_K3"}
            plan = mod.physical_plan_for("DENSE_K3", matrix_by_arm=row, worktrees=wt, out_root=Path(td) / "o")
        argv = plan["materializer_argv"]["argv"]
        flags = {a for a in argv if a.startswith("--")}
        allowed = {
            "--repo",
            "--parent",
            "--target",
            "--task-id",
            "--scope-json",
            "--classification-json",
            "--test-authority-json",
            "--out-dir",
        }
        self.assertTrue(flags <= allowed, flags)


class TestBusyMatrixBurnCheck(unittest.TestCase):
    """Tampered matrix/plan must fail closed with typed reasons."""

    def test_tampered_matrix_hash_raises(self):
        if MATRIX is None or not MATRIX.is_file():
            self.skipTest("frozen matrix unavailable (set T12_M02_MATRIX)")
        import csv

        with open(MATRIX, encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        rows[0]["notes"] = "TAMPERED"
        with tempfile.TemporaryDirectory() as td:
            bad = Path(td) / "matrix.csv"
            with open(bad, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)
            with self.assertRaises(ValueError) as ctx:
                mod._matrix_rows(bad)
            self.assertIn("MATRIX_HASH_MISMATCH", str(ctx.exception))

    def test_changed_plan_hash_fails(self):
        with tempfile.TemporaryDirectory() as td:
            bad = Path(td) / "plan.json"
            bad.write_text(json.dumps({"x": 1}), encoding="utf-8")
            ok, reason = mod._plan_ok(bad)
            self.assertFalse(ok)
            self.assertIn("PLAN_HASH_MISMATCH", reason)


class TestRealEngineBridge(unittest.TestCase):
    """The execution path must call the REAL pinned frozen functions; mocks
    only here.  Partial engine failure must never be reported as PASS."""

    def test_bridge_documents_real_frozen_functions_only(self):
        details = mod.real_bridge_stage_details()
        for fn in ("run_state_v3", "lock_install_script", "OpwsIsolatedRuntime", "resolve_runtime_image"):
            self.assertIn(fn, details["functions"])
        self.assertEqual(details["executable_in_d3"], "false")

    def test_stage_pins_verified_against_frozen_worktree_when_available(self):
        if not HAS_FROZEN:
            self.skipTest("frozen worktree unavailable on this host")
        st = mod._driver.engine_scripts_pin_status(FROZEN_WORKTREE)
        self.assertTrue(all(v["ok"] for v in st.values()), st)

    def test_partial_engine_failure_never_pass(self):
        # Mock ONLY in the unit test: a fake engine module whose run_state_v3
        # fails for the second authorized arm (a real partial failure), and a
        # fake materialize subprocess that reports success (never touches the
        # real engine or the frozen worktree).
        class FakeEngine:
            def run_state_v3(self, **kwargs: object) -> dict:
                arm = str(kwargs.get("state"))
                if arm == "NEG":
                    raise RuntimeError("CONTAINER_CRASH_MID_RUN")
                return {"junit": ["x"] * 9, "junit_failures": 0, "db_name": "opws_m3b_x"}

        class FakeProc:
            returncode = 0
            stdout = "MATERIALIZE_RECORD_OK"
            stderr = ""

        fake = FakeEngine()
        orig_load = mod._load_frozen_module
        orig_sub = mod.subprocess.run

        def _fake_load(_wt: object, _rel: str, name: str) -> object:
            if name == "benchmark_harness_v3":
                return fake

            class _Dummy:
                class OpwsIsolatedRuntime:
                    def __init__(self, **kwargs: object) -> None:
                        pass

            return _Dummy()

        try:
            mod._load_frozen_module = _fake_load
            mod.subprocess.run = lambda *a, **k: FakeProc()
            with tempfile.TemporaryDirectory() as td:
                auth = {
                    "authorized_arms": ["SIP", "NEG"],
                    "max_wall_s": 7200,
                    "exclusivity_window": {},
                    "recorded_by": "t",
                }
                result = mod.run_bridge(
                    {"worktree_linux": "/root/m19b_r3_20261024/wt_t_SIP", "worktree_oid_expected": "x"},
                    rd8={"status": "ADOPT_PILOT_ONLY"},
                    auth=auth,
                    budget={"status": "OK"},
                    worktree=FROZEN_WORKTREE,
                    source_repo=Path("."),
                    scopes_dir=Path("."),
                    classification=Path("."),
                    test_authority=Path("."),
                    out_root=Path(td) / "out",
                )
        finally:
            mod._load_frozen_module = orig_load
            mod.subprocess.run = orig_sub
        self.assertEqual(result["overall"], "FAIL")
        by_arm = {a["arm_id"]: a for a in result["arms"]}
        self.assertEqual(by_arm["SIP"]["status"], "PASS")
        self.assertEqual(by_arm["NEG"]["status"], "FAIL")
        self.assertIn("CONTAINER_CRASH_MID_RUN", by_arm["NEG"]["reason"])


class TestCliGate(unittest.TestCase):
    def _run_cli(self, *extra: str, cwd_frozen: bool = True) -> tuple[int, Path, dict]:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "o"
            argv = ["run", "--out", str(out), "--worktree", str(FROZEN_WORKTREE)]
            if cwd_frozen and MATRIX is not None and PLAN is not None:
                argv += ["--matrix", str(MATRIX), "--plan", str(PLAN)]
            argv += list(extra)
            with redirect_stdout(io.StringIO()):
                code = mod.main(argv)
            gate_path = out / "RUN_GATE.json"
            gate = json.loads(gate_path.read_text(encoding="utf-8")) if gate_path.is_file() else None
            return code, out, gate

    def test_run_gate_stops_not_authorized_via_cli(self):
        code, _out, gate = self._run_cli("--wall-max-s", "3600", "--autorun-in-d3-flag", "NEVER_IN_D3")
        self.assertEqual(code, 4)
        self.assertIsNotNone(gate)
        self.assertEqual(gate["outcome"], "STOP_NOT_AUTHORIZED")  # type: ignore[index]
        self.assertFalse(gate["executed"])  # type: ignore[index]
        stops = set(gate["hard_stops"])  # type: ignore[index]
        self.assertIn("RD8_APPROVAL_PENDING", stops)
        self.assertIn("EXECUTION_NOT_AUTHORIZED", stops)

    def test_run_wrong_autorun_flag_stops(self):
        code, _out, _gate = self._run_cli()
        self.assertEqual(code, 4)

    def test_preflight_exit_4_expected_stops_when_available(self):
        if not HAS_FROZEN:
            self.skipTest("frozen data unavailable")
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "o"
            with redirect_stdout(io.StringIO()):
                code = mod.main(
                    [
                        "preflight",
                        "--out",
                        str(out),
                        "--worktree",
                        str(FROZEN_WORKTREE),
                        "--matrix",
                        str(MATRIX),
                        "--plan",
                        str(PLAN),
                    ]
                )
            self.assertEqual(code, 4)
            pf = json.loads((out / "PREFLIGHT.json").read_text(encoding="utf-8"))
            self.assertIn("RD8_APPROVAL_PENDING", pf["hard_stops"])
            self.assertIn("EXECUTION_NOT_AUTHORIZED", pf["hard_stops"])

    def test_dry_run_thirteen_not_run_when_available(self):
        if not HAS_FROZEN:
            self.skipTest("frozen data unavailable")
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "o"
            code = mod.main(
                [
                    "dry-run",
                    "--out",
                    str(out),
                    "--worktree",
                    str(FROZEN_WORKTREE),
                    "--matrix",
                    str(MATRIX),
                    "--plan",
                    str(PLAN),
                    "--pilot-only",
                ]
            )
            self.assertEqual(code, 0)
            ep = json.loads((out / "EXECUTION_PLAN.json").read_text(encoding="utf-8"))
            arms = ep["plan"]["arms"]
            self.assertEqual(len(arms), 4)
            self.assertTrue(ep["not_run_confirmed"])

    def test_out_dir_reuse_refused(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "o"
            out.mkdir()
            with self.assertRaises(SystemExit) as ctx:
                mod.main(["preflight", "--out", str(out)])
            self.assertIn("OUT_DIR_EXISTS", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
