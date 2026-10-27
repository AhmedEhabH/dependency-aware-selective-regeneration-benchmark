"""T12 M02-D2 scope normalizer — isolated stdlib tests + real-data closures.

Standard library only; no pytest dependency inside this file; no frozen
worktree import required; no API, no execution, no writes outside
``tempfile``.  Oracle-field noninterference is enforced by construction
(allowlisted extraction) and asserted by poisoned-source tests.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
_spec = importlib.util.spec_from_file_location("t12_m02_scope_normalizer", _SCRIPTS / "t12_m02_scope_normalizer.py")
mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(mod)

SCH = importlib.util.spec_from_file_location("t12_m02_materializer_schema", _SCRIPTS / "t12_m02_materializer_schema.py")
schema = importlib.util.module_from_spec(SCH)
assert SCH and SCH.loader
SCH.loader.exec_module(schema)

TASK = "saleor-rc-7e42fc67ce72"

FOUR_FROZEN = ["SIP", "DENSE_K3", "DENSE_K10", "BM25_K10"]

PATHS_A = ["saleor/app/installation_utils.py", "saleor/app/manifest_validations.py",
           "saleor/app/management/commands/install_app.py"]
PATHS_B = ["saleor/app/tests/test_validators.py", "saleor/app/tests/test_app_commands.py"]


def _sip_source(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "per_task": {
            TASK: {"task_id": TASK, "sip_predicted_set": PATHS_A + PATHS_A,
                   "rmcss_predicted_set": PATHS_B,
                   "sip_prediction_hash": "x", "rmcss_prediction_hash": "y"},
        },
    }), encoding="utf-8")
    return path


def _comp_source(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "per_task": {
            TASK: {
                "task_id": TASK,
                "DENSE@3_selected": PATHS_A,
                "DENSE@10_selected": PATHS_A + PATHS_B,
                "BM25@3_selected": PATHS_A[:1],
                "BM25@10_selected": PATHS_A + PATHS_B,
                "BM25_TO_CIA_1HOP_selected": PATHS_B,
                # outcome-domain fields coexist in the real file; must never be consumed
                "gold": ["saleor/app/installation_utils.py"],
                "gold_in_universe_count": 1,
                "universe_size": 1086,
                "rmcss_size": 3,
                "DENSE@3_confusion": {"fn": 1, "fp": 3, "tp": 0},
                "DENSE@10_confusion": {"fn": 1, "fp": 10, "tp": 0},
            },
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class TestCanonicalRule(unittest.TestCase):
    def test_canonical_hash_matches_frozen_recipe(self):
        # frozen recipe: json.dumps(sorted unique, compact separators) -> sha256
        paths = ["b.py", "a.py", "b.py"]
        canonical = sorted({"a.py", "b.py"})
        expected = hashlib.sha256(
            json.dumps(canonical, sort_keys=False, ensure_ascii=False,
                       separators=(",", ":")).encode("utf-8")).hexdigest()
        self.assertEqual(schema.canonical_scope_hash(paths), expected)
        self.assertNotEqual(schema.canonical_scope_hash(["a.py"]),
                            schema.canonical_scope_hash(["a.py", "b.py"]))

    def test_canonical_rule_rejects_bad_spellings(self):
        for bad in ("", "\\weird", "C:/abs.py", "/abs.py", "a/../b.py", "a/./b.py", "./a.py", 3):
            with self.assertRaises(schema.SchemaError):
                schema.canonicalize_scope_path(bad, context="test")
        # dedupe + sort are deterministic
        uniq, dup = schema.canonicalize_scope_paths(["b.py", "a.py", "b.py"])
        self.assertEqual(uniq, ["a.py", "b.py"])
        self.assertEqual(dup, 1)

    def test_crosscheck_against_frozen_opws_phase2_plan_when_present(self):
        """Machine-dependent: seed the frozen worktree's own implementation."""
        frozen = Path(r"D:\WP2\active\opws-runtime-compat-2026-10-26\scripts\opws_phase2_plan.py")
        if not frozen.is_file():
            self.skipTest("frozen worktree not present on this machine")
        spec = importlib.util.spec_from_file_location("opws_phase2_plan_frozen", frozen)
        p2 = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(p2)
        src = ["saleor/app/a.py", "saleor/app/b.py", "saleor/app/a.py"]
        mine = schema.canonical_scope_hash(src)
        theirs = p2.compute_canonical_scope_hash(src)
        self.assertEqual(mine, theirs, "our canonical hash must match the frozen recipe")


class TestHermeticExtraction(unittest.TestCase):
    def setUp(self) -> None:
        self.td = Path(tempfile.mkdtemp(prefix="t12m02_scope_"))

    def test_sip_and_rmcss_allowlisted_fields(self):
        p = _sip_source(self.td / "sip.json")
        sip, oracle_sip = mod._extract_per_task_file(p, TASK, "sip_predicted_set", "sip_rmcss")
        rmcss, oracle_rmcss = mod._extract_per_task_file(p, TASK, "rmcss_predicted_set", "sip_rmcss")
        self.assertEqual(sip, PATHS_A + PATHS_A)  # raw extraction; dedupe happens later
        self.assertEqual(rmcss, PATHS_B)
        self.assertEqual(oracle_sip, [])
        self.assertEqual(oracle_rmcss, [])

    def test_comp_r2_arm_field_selection_and_oracle_guard(self):
        p = _comp_source(self.td / "comp.json")
        d3, oracle = mod._extract_comp_r2(p, TASK, "DENSE@3_selected")
        d10, _ = mod._extract_comp_r2(p, TASK, "DENSE@10_selected")
        b10, _ = mod._extract_comp_r2(p, TASK, "BM25@10_selected")
        hop, _ = mod._extract_comp_r2(p, TASK, "BM25_TO_CIA_1HOP_selected")
        self.assertEqual(d3, PATHS_A)
        self.assertEqual(d10, PATHS_A + PATHS_B)
        self.assertEqual(b10, PATHS_A + PATHS_B)
        self.assertEqual(hop, PATHS_B)
        self.assertIn("gold", oracle)
        self.assertIn("DENSE@3_confusion", oracle)  # presence recorded, never consumed

    def test_agent_selected_paths(self):
        p = self.td / "agent.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"per_task": {TASK: {"task_id": TASK,
                                                     "selected_paths": PATHS_A}}}), encoding="utf-8")
        out, oracle = mod._extract_per_task_file(p, TASK, "selected_paths", "wp1b_agent")
        self.assertEqual(out, PATHS_A)
        self.assertEqual(oracle, [])

    def test_agentless_prediction_set_with_oracle_classification(self):
        p = self.td / "agentless.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"records": [{"task_id": TASK, "prediction_set": PATHS_B,
                                               "classification": "COMPLETE"}]}), encoding="utf-8")
        out, oracle = mod._extract_agentless(p, TASK)
        self.assertEqual(out, PATHS_B)
        self.assertEqual(oracle, ["classification"])  # recorded, never consumed

    def test_gold_proxy_list(self):
        p = self.td / "gold.json"
        p.write_text(json.dumps({"opened_once": True, "proxies": {TASK: PATHS_A}}), encoding="utf-8")
        out, oracle = mod._extract_gold(p, TASK)
        self.assertEqual(out, PATHS_A)
        self.assertEqual(oracle, ["opened_once"])

    def test_universe_all_files(self):
        p = self.td / "universe.json"
        p.write_text(json.dumps({"records": [{"path": "a.py"}, {"path": "b/c.py"}]}), encoding="utf-8")
        out, _ = mod._extract_universe(p, TASK)
        self.assertEqual(out, ["a.py", "b/c.py"])

    def test_missing_task_fails_closed(self):
        p = self.td / "sip.json"
        p.write_text(json.dumps({"per_task": {"saleor-rc-other": {"sip_predicted_set": []}}}),
                     encoding="utf-8")
        with self.assertRaises(mod.ExtractionError) as ctx:
            mod._extract_per_task_file(p, TASK, "sip_predicted_set", "sip_rmcss")
        self.assertIn("MISSING_TASK_OR_FIELD", str(ctx.exception))

    def test_malformed_field_fails_closed(self):
        p = self.td / "sip.json"
        p.write_text(json.dumps({"per_task": {TASK: {"sip_predicted_set": "not-a-list"}}}),
                     encoding="utf-8")
        with self.assertRaises(mod.ExtractionError) as ctx:
            mod._extract_per_task_file(p, TASK, "sip_predicted_set", "sip_rmcss")
        self.assertIn("FIELD_MALFORMED", str(ctx.exception))

    def test_unknown_arm_fails_closed(self):
        with self.assertRaises(mod.ExtractionError):
            mod.extraction_rule_for("NOT_AN_ARM")


class TestOracleNoninterference(unittest.TestCase):
    """Poisoned sources: outcome fields must be structurally unreachable."""

    def setUp(self) -> None:
        self.td = Path(tempfile.mkdtemp(prefix="t12m02_oracle_"))

    def _source(self, poisoned: bool) -> Path:
        p = self.td / "comp.json"
        base = {"DENSE@3_selected": PATHS_A, "task_id": TASK}
        if poisoned:
            base["gold"] = PATHS_B  # if consumed the scope would differ
            base["DENSE@3_confusion"] = {"tp": 99, "fp": 0, "fn": 0}
        p.write_text(json.dumps({"per_task": {TASK: base}}), encoding="utf-8")
        return p

    def test_poisoned_gold_field_changes_nothing(self):
        a = mod._extract_comp_r2(self._source(False), TASK, "DENSE@3_selected")
        b = mod._extract_comp_r2(self._source(True), TASK, "DENSE@3_selected")
        self.assertEqual(a[0], b[0])
        self.assertEqual(a[0], PATHS_A)

    def test_classification_payload_cannot_be_routed_into_scope(self):
        # a classification-looking record inside the source is never read by
        # the allowlisted extractor
        p = self.td / "sip.json"
        p.write_text(json.dumps({"per_task": {TASK: {
            "sip_predicted_set": PATHS_A,
            "classification": "M",
            "changes": {"a.py": "M"},
        }}}), encoding="utf-8")
        out, _ = mod._extract_per_task_file(p, TASK, "sip_predicted_set", "sip_rmcss")
        self.assertEqual(out, PATHS_A)


class TestNormalizeArmScope(unittest.TestCase):
    def setUp(self) -> None:
        self.td = Path(tempfile.mkdtemp(prefix="t12m02_norm_"))
        mod.SOURCE_PATH_OVERRIDES.clear()

    def tearDown(self) -> None:
        mod.SOURCE_PATH_OVERRIDES.clear()

    def _env(self):
        sip = _sip_source(self.td / "sip.json")
        comp = _comp_source(self.td / "comp.json")
        agent = self.td / "agent.json"
        agent.write_text(json.dumps({"per_task": {TASK: {"selected_paths": PATHS_A}}}),
                         encoding="utf-8")
        universe = self.td / "universe.json"
        universe.write_text(json.dumps({"records": [{"path": p} for p in PATHS_A]}),
                            encoding="utf-8")
        mod.SOURCE_PATH_OVERRIDES.update({
            "SIP": sip, "RM_CSS": sip, "DENSE_K3": comp, "DENSE_K10": comp,
            "BM25_K3": comp, "BM25_K10": comp, "BM25_TO_CIA_1HOP": comp,
            "AGENT": agent, "SELECT_ALL": universe,
        })
        return sip, self.td

    def _n(self, arm: str) -> dict:
        sip, td = self._env()
        return mod.normalize_arm_scope(arm, TASK, base=td, repo=Path("."),
                                       census_records=[])

    def test_sip_receipt_fields(self):
        receipt = self._n("SIP")
        self.assertEqual(receipt["status"], "OK")
        self.assertEqual(receipt["arm_id"], "SIP")
        self.assertEqual(receipt["selected_path_count"], 3)  # duplicates removed
        self.assertEqual(receipt["duplicate_count"], 3)
        self.assertEqual(receipt["scope_json"], {"scope": sorted(set(PATHS_A))})
        self.assertEqual(set(receipt.keys()),
                         {"schema", "rule_version", "arm_id", "task_id", "status",
                          "source", "source_kind", "source_sha256", "source_pin_matched",
                          "extraction_keypath_allowlist", "oracle_fields_present_never_consumed",
                          "selected_path_count", "duplicate_count", "scope_hash",
                          "scope_json_sha256", "scope_json"})

    def test_scope_json_matches_materializer_schema(self):
        r = self._n("DENSE_K3")
        self.assertEqual(r["status"], "OK")
        self.assertEqual(r["scope_json"]["scope"], sorted(set(PATHS_A)))
        self.assertIn("gold", r["oracle_fields_present_never_consumed"])
        parsed = json.loads(json.dumps({"scope": r["scope_json"]["scope"]}))
        uniq, dup = schema.canonicalize_scope_paths(parsed["scope"])
        self.assertEqual(dup, 0)
        self.assertEqual(schema.canonical_scope_hash(uniq), r["scope_hash"])

    def test_neg_empty_scope(self):
        r = self._n("NEG")
        self.assertEqual(r["status"], "OK")
        self.assertEqual(r["scope_json"], {"scope": []})
        self.assertEqual(r["selected_path_count"], 0)

    def test_select_all_uses_universe_paths(self):
        r = self._n("SELECT_ALL")
        self.assertEqual(r["status"], "OK")
        self.assertEqual(r["scope_json"]["scope"], sorted(set(PATHS_A)))

    def test_invalid_scope_spelling_rejected(self):
        agent = self.td / "agent_bad.json"
        agent.write_text(json.dumps({"per_task": {TASK: {"selected_paths": ["../escape"]}}}),
                         encoding="utf-8")
        mod.SOURCE_PATH_OVERRIDES["AGENT"] = agent
        r = mod.normalize_arm_scope("AGENT", TASK, base=self.td, repo=Path("."),
                                    census_records=[])
        self.assertEqual(r["status"], "REJECTED_INVALID_SCOPE_SPELLING")
        self.assertIn("forbidden", r["reason"])

    def test_first_four_frozen_order(self):
        self._env()
        receipts = mod.normalize_all_arms(base=self.td, repo=Path("."), census_records=[],
                                          arms=["BM25_K10", "DENSE_K3", "SIP", "DENSE_K10"])
        self.assertEqual([r["arm_id"] for r in receipts], FOUR_FROZEN)


def _git_available() -> bool:
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=False, timeout=20)
        return True
    except Exception:
        return False


def _mini_repo() -> tuple[Path, str, str] | None:
    """Build a two-commit fixture repo; return (repo, parent, target) or None."""
    if not _git_available():
        return None
    td = tempfile.mkdtemp(prefix="t12m02_git_")
    repo = Path(td)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    # deleted files inside the fixture make TemporaryDirectory cleanup race on
    # Windows; the caller removes the tree with ignore_errors=True instead.
    import shutil

    def _cleanup() -> None:
        shutil.rmtree(td, ignore_errors=True)

    _mini_repo.cleanup = _cleanup  # type: ignore[attr-defined]
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    (repo / "m.py").write_text("one\n", encoding="utf-8")
    (repo / "d.py").write_text("two\n", encoding="utf-8")
    (repo / "renamed_old.py").write_text("three\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "parent"], cwd=repo, check=True)
    parent = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True,
                            text=True, check=True).stdout.strip()
    (repo / "m.py").write_text("one changed\n", encoding="utf-8")
    (repo / "d.py").unlink()
    (repo / "renamed_old.py").unlink()
    (repo / "a.py").write_text("new\n", encoding="utf-8")
    (repo / "renamed_new.py").write_text("three\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "target"], cwd=repo, check=True)
    target = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True,
                            text=True, check=True).stdout.strip()
    return repo, parent, target  # type: ignore[return-value]


class TestGitDerivation(unittest.TestCase):
    """Hermetic mini-git-repo exercising the frozen protocol path."""

    @unittest.skipUnless(_git_available(), "git not available")
    def test_name_status_map_m_ad_and_rename_as_d_a(self):
        got = _mini_repo()
        if got is None:
            self.skipTest("git init failed")
        repo, parent, target = got
        self.addCleanup(getattr(_mini_repo, "cleanup", lambda: None))
        # --no-renames: a rename appears as D(old) + A(new), never R
        out = schema.git_name_status_map(Path(repo), parent, target)
        self.assertEqual(out["m.py"], "M")
        self.assertEqual(out["d.py"], "D")
        self.assertEqual(out["a.py"], "A")
        self.assertEqual(out.get("renamed_old.py"), "D")
        self.assertEqual(out.get("renamed_new.py"), "A")
        self.assertNotIn("R_OLD", out.values())
        self.assertNotIn("R_NEW", out.values())

    def test_parse_name_status_z_rejects_unsupported_and_truncated(self):
        with self.assertRaises(schema.SchemaError):
            schema.parse_name_status_z([b"T", b"p.py", b""])
        with self.assertRaises(schema.SchemaError):
            schema.parse_name_status_z([b"M"])  # truncated


class TestRealDataOnThisHost(unittest.TestCase):
    """Machine-dependent: normalize the REAL frozen sources (runs here 2026-10-27)."""

    def test_real_sources_normalize_all_thirteen(self):
        repo = mod._adapt.FROZEN_SOURCE_SALEOR_REPO
        census = Path("research/wp2/wp2_saleor_main297_census_2026-09-22.json")
        if not repo.is_dir() or not census.is_file():
            self.skipTest("real frozen sources not present on this machine")
        census_data = json.loads(census.read_text(encoding="utf-8"))
        records = next(r["changed_paths"] for r in census_data["tasks"]
                       if r.get("task_id") == TASK)
        receipts = mod.normalize_all_arms(base=Path.cwd(), repo=repo,
                                          census_records=records, log=None)
        by_arm = {r["arm_id"]: r for r in receipts}
        self.assertEqual([r["arm_id"] for r in receipts][:4], FOUR_FROZEN)
        for arm, r in by_arm.items():
            self.assertEqual(r["status"], "OK", f"{arm}: {r.get('reason')}")
            if arm == "NEG":
                self.assertEqual(r["selected_path_count"], 0)
            elif arm == "FULL_REFERENCE":
                self.assertEqual(r["selected_path_count"], 4)  # 8 changed - 4 test files
            else:
                self.assertGreater(r["selected_path_count"], 0, arm)
            self.assertFalse(r["source_pin_matched"] is False, f"{arm} pin drift")
        # oracle keys recorded but never consumed in the real comp file
        dense = by_arm["DENSE_K3"]
        self.assertIn("gold", dense["oracle_fields_present_never_consumed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
