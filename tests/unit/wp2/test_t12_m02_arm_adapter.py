"""T12 M02 arm adapter — isolated standard-library tests (mission requirements a–i).

Runs with the Python standard library only (``python -m unittest``), no pytest
dependency inside this file, no frozen worktree, no API, no execution, no writes
outside ``tempfile`` directories.
"""
from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
_spec = importlib.util.spec_from_file_location("t12_m02_arm_adapter", _SCRIPTS / "t12_m02_arm_adapter.py")
mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(mod)

FROZEN_WORKTREE_HEAD = "22d569464fdbf9d0ebda842497cc23a7a10e2237"

JUNIT_FAIL = """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" tests="1" failures="1" errors="0">
  <testcase classname="saleor.app.tests.test_validators" name="test_new_tab_relative_url_without_app_url" time="0.01">
    <failure message="AssertionError: boom">assert False</failure>
  </testcase>
</testsuite>
"""
JUNIT_PASS = """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" tests="1" failures="0" errors="0">
  <testcase classname="saleor.app.tests.test_validators" name="test_new_tab_relative_url_without_app_url" time="0.01"/>
</testsuite>
"""


def _mk_junit(directory: Path, name: str, body: str) -> Path:
    p = directory / f"{name}.xml"
    p.write_text(body, encoding="utf-8")
    return p


def _fake_worktree() -> Path:
    """A throwaway worktree: real .git layout with a mismatched HEAD."""
    td = Path(tempfile.mkdtemp(prefix="t12m02_wt_"))
    gitdir = td / ".git"
    gitdir.mkdir()
    (gitdir / "HEAD").write_text("ref: refs/heads/research/track-1-2\n", encoding="utf-8")
    ref = gitdir / "refs/heads/research/track-1-2"
    ref.parent.mkdir(parents=True)
    ref.write_text("deadbeefdeadbeefdeadbeefdeadbeefdeadbeef\n", encoding="utf-8")
    (td / "scripts").mkdir()
    (td / "scripts" / "wp2_m3b_runner_smoke.py").write_text("x = 1\n", encoding="utf-8")
    return td


class Test13FrozenIdentities(unittest.TestCase):
    """(a) 13 frozen identities: 13 arms, 7 trees, 12 four-field classes,
    12 five-field provisional IDs, one alias pair, frozen first-four order."""

    def test_13_arms(self):
        self.assertEqual(len(mod.load_arms()), 13)

    def test_arithmetic_13_7_12_12_1(self):
        ar = mod.matrix_arithmetic()
        self.assertEqual(ar["n_arms"], 13)
        self.assertEqual(ar["n_unique_trees"], 7)
        self.assertEqual(ar["n_four_field_classes"], 12)
        self.assertEqual(ar["n_five_field_provisional"], 12)
        self.assertEqual(ar["n_alias_pairs"], 1)

    def test_alias_pair_is_agentless_bm25k3(self):
        pairs = mod.matrix_arithmetic()["alias_pairs"]
        self.assertEqual(len(pairs), 1)
        self.assertEqual(set(pairs[0]["arms"]), {"AGENTLESS_STYLE_ADAPTATION", "BM25_K3"})

    def test_first_four_frozen_order_is_invariable(self):
        self.assertEqual(mod.matrix_arithmetic()["first_four_frozen_order"],
                         ["SIP", "DENSE_K3", "DENSE_K10", "BM25_K10"])

    def test_one_frozen_task_and_contract(self):
        tasks = {a["task_id"] for a in mod.load_arms()}
        contracts = {a["test_contract_hash"] for a in mod.load_arms()}
        self.assertEqual(tasks, {mod.FROZEN_TASK})
        self.assertEqual(len(contracts), 1)

    def test_four_field_identity_deterministic_and_alias_shared(self):
        """Four-field class identity: sha256(scope | patch | bytes | contract).

        Composition is defined by this adapter (documented in the README); the
        prior ledger's column serialization is not disclosed in the kit and is
        therefore NOT used as a frozen identity source.
        """
        arms = {a["arm_id"]: a for a in mod.load_arms()}
        sip = arms["SIP"]
        self.assertEqual(mod.four_field_id(sip), mod.four_field_id(sip))
        self.assertEqual(arms["AGENTLESS_STYLE_ADAPTATION"]["four_field_id"],
                         arms["BM25_K3"]["four_field_id"])
        # two arms share a class iff scope+patch+bytes+contract are equal
        by_class: dict = {}
        for a in mod.load_arms():
            by_class.setdefault(a["four_field_id"], set()).add(a["arm_id"])
        self.assertEqual(sum(len(v) for v in by_class.values()), 13)
        singleton_classes = [v for v in by_class.values() if len(v) > 1]
        self.assertEqual([sorted(v) for v in singleton_classes],
                         [["AGENTLESS_STYLE_ADAPTATION", "BM25_K3"]])


class TestOptionBOnePhysicalExecutionPerArm(unittest.TestCase):
    """(b) one physical execution per arm under Option B (REUSE_NOT_PERMITTED)."""

    def test_all_13_rows_option_b_yes(self):
        rows = mod.build_manifest_rows()
        self.assertEqual(len(rows), 13)
        self.assertTrue(all(r["option_b_physical_execution_required"] == "YES" for r in rows))

    def test_execution_ids_all_distinct(self):
        rows = mod.build_manifest_rows("TOKEN_A")
        ids = [r["execution_id"] for r in rows]
        self.assertEqual(len(ids), len(set(ids)), "every arm gets its own fresh execution id")

    def test_alias_pair_never_shares_execution(self):
        rows = {r["arm_id"]: r for r in mod.build_manifest_rows("TOKEN_A")}
        self.assertNotEqual(rows["AGENTLESS_STYLE_ADAPTATION"]["execution_id"],
                            rows["BM25_K3"]["execution_id"],
                            "AGENTLESS_STYLE_ADAPTATION and BM25_K3 require two physical executions")

    def test_reuse_never_allowed(self):
        rows = mod.build_manifest_rows()
        self.assertTrue(all(r["result_reuse_allowed"] == "NO" for r in rows))

    def test_token_changes_ids(self):
        a = {r["arm_id"]: r["execution_id"] for r in mod.build_manifest_rows("T1")}
        b = {r["arm_id"]: r["execution_id"] for r in mod.build_manifest_rows("T2")}
        self.assertNotEqual(a["SIP"], b["SIP"])


class TestNoOracleLeakage(unittest.TestCase):
    """(c) no JUnit/test-oracle leakage to selectors."""

    def test_plan_scope_inputs_are_never_junit_paths(self):
        rows = mod.dry_run_plan(Path("."))
        for r in rows:
            cmd = r["materialize_cmd"].lower()
            self.assertNotIn(".xml", cmd)
            self.assertNotIn("receipt", cmd)
            self.assertNotIn("junit", cmd)
            self.assertIn("--scope-json", cmd)

    def test_preflight_unaffected_by_junit_files(self):
        wt = _fake_worktree()
        res_before = mod.preflight(wt)
        (wt / "receipts").mkdir()
        _mk_junit(wt / "receipts", "junit_0", JUNIT_FAIL)
        res_after = mod.preflight(wt)
        self.assertEqual(res_before["hard_stops"], res_after["hard_stops"])
        self.assertIn("FROZEN_WORKTREE_DRIFT", res_after["hard_stops"])

    def test_receipts_are_outcomes_not_inputs(self):
        # receipts-check consumes JUnit XMLs as OUTPUT evidence only; the
        # materialization plan inputs never point at the execution receipts dir.
        with tempfile.TemporaryDirectory():
            rows = mod.dry_run_plan(Path("."))
            plan_inputs = set()
            for r in rows:
                for part in r["materialize_cmd"].split():
                    if part.startswith("<") and part.endswith((".json>", '"')):
                        plan_inputs.add(part)
            self.assertTrue(all(p.endswith(".json>") for p in plan_inputs))
        # the ordering guarantee is structural: JUnit receipts are produced
        # only after scope selection; the adapter never reads *.xml for scope input.
        self.assertTrue(mod.results_are_outcome_domain_only())


class TestRefusalOfMismatchedHashes(unittest.TestCase):
    """(d) refusal of mismatched hashes -> HASH_STOP (exit 4)."""

    def test_matrix_hash_mismatch_stops(self):
        with tempfile.TemporaryDirectory() as td:
            bogus = Path(td) / "matrix.csv"
            bogus.write_text("arm_id,anything\nSIP,x\n", encoding="utf-8")
            res = mod.preflight(Path("."), matrix_path=bogus)
            self.assertFalse(res["matrix_hash_ok"])
            self.assertIn("MATRIX_HASH_MISMATCH", res["hard_stops"])
            self.assertEqual(res["exit_code"], 4)

    def test_plan_hash_mismatch_stops(self):
        with tempfile.TemporaryDirectory() as td:
            bogus = Path(td) / "plan.json"
            bogus.write_text("{}", encoding="utf-8")
            res = mod.preflight(Path("."), plan_path=bogus)
            self.assertIn("PLAN_HASH_MISMATCH", res["hard_stops"])
            self.assertEqual(res["exit_code"], 4)

    def test_route_ref_provider_mismatch_stops(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "route.json"
            p.write_text(json.dumps({"model": "qwen/qwen3-coder", "provider_order": ["other/thing"],
                                     "allow_fallbacks": True, "endpoint": "x"}), encoding="utf-8")
            ok_h, ok_p, pin = mod.check_route_file(p)
            self.assertFalse(ok_h)
            self.assertFalse(ok_p)

    def test_route_ref_real_schema_passes_when_hash_pinned(self):
        """The frozen BENCHMARK_ROUTE_REFERENCE.json nests provider fields; a
        byte-identical copy (same hash) must pass hash AND pin checks."""
        # Build a byte-identical copy of the frozen route reference.
        frozen = Path(r"D:\WP2\audit_results\T12_M01D_SETUP_20261027-074837-1346394\BENCHMARK_ROUTE_REFERENCE.json")
        if frozen.is_file():
            raw = frozen.read_bytes()
            with tempfile.TemporaryDirectory() as td:
                p = Path(td) / "route.json"
                p.write_bytes(raw)
                ok_h, ok_p, pin = mod.check_route_file(p)
                self.assertTrue(ok_h)
                self.assertTrue(ok_p)
                self.assertEqual(pin["provider_order"], ["deepinfra/turbo"])
                self.assertIs(pin["allow_fallbacks"], False)
        else:
            self.skipTest("frozen route reference not present on this machine")

    def test_worktree_head_drift_stops(self):
        wt = _fake_worktree()
        res = mod.preflight(wt)
        self.assertFalse(res["worktree_head_match"])
        self.assertIn("FROZEN_WORKTREE_DRIFT", res["hard_stops"])
        self.assertEqual(res["exit_code"], 4)

    def test_head_resolution_matches_pinned_oid(self):
        td = Path(tempfile.mkdtemp(prefix="t12m02_hd_"))
        gitdir = td / ".git"
        gitdir.mkdir()
        (gitdir / "HEAD").write_text("ref: refs/heads/opws\n", encoding="utf-8")
        (gitdir / "packed-refs").write_text(
            f"{FROZEN_WORKTREE_HEAD} refs/heads/opws\n", encoding="utf-8")
        self.assertEqual(mod.resolve_git_head(td), FROZEN_WORKTREE_HEAD)

    def test_head_resolution_linked_worktree_commondir(self):
        """mirror of the real frozen worktree layout: .git is a gitdir pointer
        and the branch ref lives in the common dir (commondir)."""
        root = Path(tempfile.mkdtemp(prefix="t12m02_linked_"))
        common = root / "main" / ".git"
        common.mkdir(parents=True)
        refdir = common / "refs/heads/parallel"
        refdir.mkdir(parents=True)
        (refdir / "opws-runtime-compat-2026-10-26").write_text(
            FROZEN_WORKTREE_HEAD + "\n", encoding="utf-8")
        wt = root / "worktrees/opws-runtime-compat-2026-10-26"
        wt.mkdir(parents=True)
        (wt / "HEAD").write_text("ref: refs/heads/parallel/opws-runtime-compat-2026-10-26\n",
                                 encoding="utf-8")
        (wt / "commondir").write_text(str(common.resolve()) + "\n", encoding="utf-8")
        checkout = root / "checkout"
        checkout.mkdir()
        (checkout / ".git").write_text("gitdir: " + (wt.resolve() / "").as_posix() + "\n", encoding="utf-8")
        self.assertEqual(mod.resolve_git_head(checkout), FROZEN_WORKTREE_HEAD)

    def test_preflight_cli_exit_4_on_matrix_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            bogus = Path(td) / "matrix.csv"
            bogus.write_text("nope", encoding="utf-8")
            code = mod.main(["preflight", "--worktree", str(_fake_worktree()),
                             "--matrix", str(bogus)])
            self.assertEqual(code, 4)


class TestUnknownProviderUnsetBudget(unittest.TestCase):
    """(e) refusal to run with unknown provider or unset budget."""

    def test_empty_authorization_rejected(self):
        va = mod.validate_authorization({})
        self.assertFalse(va["ok"])
        self.assertTrue(any("budget_usd" in e for e in va["errors"]))

    def test_unknown_provider_rejected(self):
        auth = {"budget_usd": 5.0, "route": {"provider": "openrouter/auto", "model": "qwen/qwen3-coder",
                                             "allow_fallbacks": False}, "arms": ["SIP"],
                "resource_window": "2026-11-01", "approval_message_id": "m1", "tasks": [mod.FROZEN_TASK]}
        va = mod.validate_authorization(auth)
        self.assertFalse(va["ok"])
        self.assertTrue(any("provider" in e for e in va["errors"]))

    def test_fallbacks_enabled_rejected(self):
        auth = {"budget_usd": 5.0, "route": {"provider": "deepinfra/turbo", "model": "qwen/qwen3-coder",
                                             "allow_fallbacks": True}, "arms": ["SIP"],
                "resource_window": "2026-11-01", "approval_message_id": "m1"}
        self.assertFalse(mod.validate_authorization(auth)["ok"])

    def test_unknown_arm_rejected(self):
        auth = {"budget_usd": 5.0, "route": {"provider": "deepinfra/turbo", "model": "qwen/qwen3-coder",
                                             "allow_fallbacks": False}, "arms": ["SIP", "NOT_AN_ARM"],
                "resource_window": "2026-11-01", "approval_message_id": "m1", "tasks": [mod.FROZEN_TASK]}
        va = mod.validate_authorization(auth)
        self.assertFalse(va["ok"])
        self.assertTrue(any("unknown arm" in e for e in va["errors"]))

    def test_valid_authorization_passes_schema(self):
        auth = {"budget_usd": 10.0, "route": {"provider": "deepinfra/turbo", "model": "qwen/qwen3-coder",
                                              "allow_fallbacks": False}, "arms": ["SIP", "NEG", "FULL_REFERENCE"],
                "resource_window": "2026-11-02..2026-11-06", "approval_message_id": "sep-auth-1",
                "tasks": [mod.FROZEN_TASK]}
        self.assertTrue(mod.validate_authorization(auth)["ok"])

    def test_run_refuses_without_authorization(self):
        code = mod.main(["run", "--authorization", str(Path(".") / "missing_auth.json")])
        self.assertEqual(code, 2, "run must fail closed when no authorization file is readable")

    def test_run_refuses_design_gap_even_with_auth(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "auth.json"
            p.write_text(json.dumps({"budget_usd": 10.0,
                                     "route": {"provider": "deepinfra/turbo", "model": "qwen/qwen3-coder",
                                               "allow_fallbacks": False},
                                     "arms": ["SIP"], "resource_window": "2026-11-02..2026-11-06",
                                     "approval_message_id": "sep-auth-2", "tasks": [mod.FROZEN_TASK]}),
                         encoding="utf-8")
            code = mod.main(["run", "--authorization", str(p)])
            self.assertEqual(code, 5, "no frozen multi-node per-arm F2P driver: design gap, not a mock run")


class TestNoSourceWorktreeWrites(unittest.TestCase):
    """(f) no writes into source worktrees (dry-run/preflight/manifest are read-only)."""

    def test_dry_run_never_modifies_worktree(self):
        wt = _fake_worktree()
        target = wt / "scripts" / "wp2_m3b_runner_smoke.py"
        before = mod.sha256_file(target)
        listing_before = sorted(str(p.relative_to(wt)) for p in wt.rglob("*"))
        buf = io.StringIO()
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "manifest.csv"
            with redirect_stdout(buf):
                code = mod.main(["dry-run", "--worktree", str(wt), "--out", str(out)])
            self.assertEqual(code, 0)
            self.assertTrue(out.exists())
        self.assertEqual(mod.sha256_file(target), before)
        listing_after = sorted(str(p.relative_to(wt)) for p in wt.rglob("*"))
        self.assertEqual(listing_before, listing_after, "dry-run wrote inside the worktree")

    def test_preflight_never_modifies_worktree(self):
        wt = _fake_worktree()
        before = sorted(str(p.relative_to(wt)) for p in wt.rglob("*"))
        res = mod.preflight(wt)
        self.assertEqual(res["exit_code"], 4)  # legitimately STOPs on drift
        after = sorted(str(p.relative_to(wt)) for p in wt.rglob("*"))
        self.assertEqual(before, after)

    def test_manifest_writes_only_to_requested_out(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "manifest.csv"
            mod.write_manifest_csv(out, mod.build_manifest_rows())
            self.assertTrue(out.exists())
            self.assertEqual(len(list(Path(td).iterdir())), 1)


class TestFailClosedNotRunRows(unittest.TestCase):
    """(g) fail-closed NOT_RUN row output."""

    def test_manifest_all_not_run(self):
        rows = mod.build_manifest_rows()
        self.assertEqual(len(rows), 13)
        for r in rows:
            self.assertEqual(r["prospective_m02e_status"], "NOT_RUN")
            self.assertEqual(r["prospective_model_usd"], 0.0)
            self.assertEqual(r["prospective_junit_count"], 0)

    def test_receipts_check_missing_dir_not_run(self):
        res = mod.receipts_check(Path(tempfile.mkdtemp(prefix="t12m02_empty_")) / "nope")
        self.assertEqual(res["status"], "NOT_RUN")

    def test_gate_verdict_stop_until_authorization(self):
        pre = {"matrix_hash_ok": True, "runner_13_arm_driver": "MISSING"}
        g = mod.compute_gates(pre)
        self.assertEqual(g["verdict"], "STOP")
        self.assertIn("arm_runner_13_frozen_interface", g["hard_stops"])

    def test_dry_run_plan_all_not_run(self):
        rows = mod.dry_run_plan(Path("."))
        self.assertTrue(all(r["status"] == "NOT_RUN" for r in rows))
        self.assertTrue(all(r["execute_driver"] == "INTEGRATION_GAP" for r in rows))


class TestDistinctCostReceipts(unittest.TestCase):
    """(h) each arm's distinct cost/resource receipt; no receipt sharing."""

    def test_each_arm_has_distinct_execution_id(self):
        ids = [r["execution_id"] for r in mod.build_manifest_rows("TOKEN_X")]
        self.assertEqual(len(ids), 13)
        self.assertEqual(len(set(ids)), 13)

    def test_neg_receipt_classification_matches_control(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "NEG"
            d.mkdir()
            _mk_junit(d, "n_r0_f0", JUNIT_FAIL)
            res = mod.receipts_check(d)
            self.assertEqual(res["status"], "PASS")
            self.assertEqual(res["expected_classification"], "FAILURE")
            self.assertEqual(res["matched"], res["total"])

    def test_neg_with_pass_receipt_stops(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "NEG"
            d.mkdir()
            _mk_junit(d, "wrong", JUNIT_PASS)
            res = mod.receipts_check(d)
            self.assertEqual(res["status"], "STOP")

    def test_duplicate_receipt_across_arms_is_reuse_violation(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "M02E_OBS"
            d.mkdir()
            _mk_junit(d, "a", JUNIT_FAIL)
            _mk_junit(d, "b", JUNIT_FAIL)  # same bytes -> same sha -> reuse flag
            res = mod.receipts_check(d)
            self.assertEqual(res["status"], "STOP")
            self.assertTrue(res["reuse_violations"])

    def test_full_reference_pass_classification(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "FULL_REFERENCE"
            d.mkdir()
            _mk_junit(d, "p0", JUNIT_PASS)
            res = mod.receipts_check(d)
            self.assertEqual(res["status"], "PASS")
            self.assertEqual(res["expected_classification"], "PASS")


class TestNoPseudoReplication(unittest.TestCase):
    """(i) three pytest repetitions on one task never create independent units."""

    def test_repetition_model_never_inflates_executions(self):
        info = mod.no_pseudo_replication()
        self.assertFalse(info["scientific_independent_repetitions"])
        self.assertEqual(info["task_count"], 1)
        self.assertEqual(info["independent_research_task_count"], 1)
        self.assertEqual(info["junit_receipts"], 9)  # 3 nodes x 3 invocations

    def test_manifest_rows_constant_despite_repetitions(self):
        rows = mod.build_manifest_rows()
        self.assertEqual(len(rows), 13)  # repetitions never add physical executions
        self.assertTrue(all(r["scientific_independent_repetitions"] == "FALSE" for r in rows))

    def test_f2p_node_list_pin_enforced_by_exact_match(self):
        self.assertTrue(mod.check_f2p_nodes(mod.F2P_NODES))
        self.assertFalse(mod.check_f2p_nodes([mod.F2P_NODES[0]]),
                         "changing the frozen node list must fail the pin")
        self.assertFalse(mod.check_f2p_nodes(mod.F2P_NODES + ["extra/node"]))
        self.assertEqual(mod.f2p_pin_status(), "EXTERNALLY_VERIFIED_PIN_COMPOSITION_UNDOCUMENTED")


class TestCliSanity(unittest.TestCase):
    def test_manifest_cli_ok(self):
        self.assertEqual(mod.main(["manifest"]), 0)

    def test_unknown_command_usage(self):
        with self.assertRaises(SystemExit):
            mod.main(["nope"])

    def test_receipts_check_missing_dir_exit_2(self):
        code = mod.main(["receipts-check", str(Path(tempfile.mkdtemp()) / "absent")])
        self.assertEqual(code, 2)

if __name__ == "__main__":
    unittest.main(verbosity=2)
