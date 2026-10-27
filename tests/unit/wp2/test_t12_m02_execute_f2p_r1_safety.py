"""T12 M02-D3-R1 — adversarial RED tests for the real F2P executor repair.

Mission: T12_M02_D3R1_EXECUTION_SAFETY_REPAIR_20261027 (Track 1.2, D3-R1).

These tests target the REPAIRED ``run_bridge`` / admission contracts BEFORE the
production repair lands.  They encode the eight demonstrated D3 defects:

  D1 per-arm plan selection (defect 1): the bridge must read each arm's plan
     from ``plan_doc['arms'][i]`` (per-arm ``worktree_linux`` /
     ``worktree_oid_expected`` / digests), never the plan top level.
  D2 real install fragment (defect 2): the engine must receive the actual
     output of the frozen ``lock_install_script``, never the literal string
     ``'computed'``.
  D3 no invented status booleans (defect 3): teardown evidence must come from
     a real post-run DB scan (injectable probe; absent probe => NOT verified),
     never ``{'db_deleted': True}``; the executor never claims it resolved the
     runtime image (delegated to the frozen engine's first fail-closed step).
  D4 control sequencing (defect 4): execution order is exactly
     NEG -> FULL_REFERENCE -> RM_CSS -> SIP regardless of the order in which
     the authorization lists them; ANY control mismatch or infrastructure
     failure stops before SIP (SIP NOT_RUN); no retries; NEG's expected
     assertion failure is classified CONTROL_EXPECTED, never PASS.
  D5 UTC window (defect 5): syntactically valid UTC timestamps, current UTC
     inside the authorized interval, max wall time fits the remaining window,
     and a fail-closed wall deadline during execution; ``signed_by`` /
     ``recorded_by`` are operator ATTESTATIONS, not signatures.
  D6 worktree contract (defect 6): the frozen isolated runtime requires the
     worktree basename ``wt_t`` (``OpwsIsolatedRuntime.validate``) and the
     executor must READ-ONLY prove the worktree content equals the arm's
     ``effective_tree_oid`` BEFORE any side effect; a wrong tree never runs.
  D7 real receipts (defect 7): exactly 9 raw per-repetition/node JUnit XML
     receipts verified against REAL produced artifacts via the real
     ``validate_run_receipt``; extra/missing files and repeated DB identities
     across arms must STOP.
  D8 oracle boundary (defect 8): classification/test-authority bytes reach
     ONLY the materializer argv; materializer-record digests must match the
     frozen arm plan (tampered scope/patch record STOPS); GOLD is not a pilot
     comparator.

Fakes policy (mission): test-only fixture git repositories, a fixture "frozen
worktree" holding stub engine modules with the REAL frozen signatures, an
injected materializer runner and an injected post-run DB probe.  The bridge's
default execution path still loads the real frozen functions on the real
frozen worktree and uses the real ``subprocess`` runner.  A unit-test receipt
is a TEST fixture, never real evidence.
"""

from __future__ import annotations

import datetime
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
_MOD = "t12_m02_execute_f2p"

_spec = importlib.util.spec_from_file_location(_MOD, _SCRIPTS / "t12_m02_execute_f2p.py")
mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(mod)

_adapt = mod._adapt
TID = mod.TID
PILOT_JUNIT_PER_ARM = mod.PILOT_JUNIT_PER_ARM
PILOT_ARMS = list(mod.PILOT_ARMS)
CONTROL_EXPECTED = dict(_adapt.CONTROL_EXPECTED_JUNIT)

FROZEN_WORKTREE = _adapt.FROZEN_WORKTREE_ROOT_DEFAULT
MATRIX = Path(os.environ["T12_M02_MATRIX"]) if os.environ.get("T12_M02_MATRIX") else None
PLAN = Path(os.environ["T12_M02_PLAN"]) if os.environ.get("T12_M02_PLAN") else None
HAS_FROZEN = (
    FROZEN_WORKTREE.is_dir() and MATRIX is not None and MATRIX.is_file() and PLAN is not None and PLAN.is_file()
)


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8", check=False
    )


def make_git_repo(dirpath: Path, files: dict[str, str]) -> str:
    """Create a real git repo committed with ``files``; return HEAD^{tree} OID."""
    dirpath.mkdir(parents=True, exist_ok=True)
    _git(dirpath, "init", "-q")
    for name, text in files.items():
        p = dirpath / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    _git(dirpath, "add", "-A")
    _git(dirpath, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "x")
    r = _git(dirpath, "rev-parse", "HEAD^{tree}")
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


HARNESS_FAKE = '''\
"""TEST-ONLY fake frozen harness_v3 (stub; real frozen stage never loaded)."""
from __future__ import annotations
import datetime
import json
import secrets
from pathlib import Path

_CFG_PATH = Path(__file__).parent / "engine_config.json"


def _cfg() -> dict:
    return json.loads(_CFG_PATH.read_text(encoding="utf-8"))


def _save(cfg: dict) -> None:
    _CFG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def target_manifests(target: str) -> dict:
    return {
        "pyproject.toml": "[tool.poetry.group.dev.dependencies]\\n",
        "poetry.lock": "lock",
        "requirements.txt": "req",
    }


def lock_install_script(worktree_linux: str, manifests: dict) -> tuple:
    return (
        f"REAL_LOCK_FRAGMENT:{worktree_linux}",
        "LOCK_EXACT",
        {"lockfile": "poetry.lock", "main": "requirements.txt"},
    )


def run_state_v3(**kwargs: object) -> dict:
    cfg = _cfg()
    history = cfg.setdefault("history", [])
    entry = {
        k: kwargs.get(k)
        for k in ("era_key", "worktree_linux", "tid", "state", "test_files",
                  "install_fragment", "locked_dev_fragment", "raw_junit_dir", "timeout_s")
    }
    entry["_oracle_keys_present"] = sorted(
        k for k in kwargs if "classif" in k.lower() or "authority" in k.lower()
    )
    entry["_has_isolated"] = kwargs.get("isolated") is not None
    history.append(entry)
    _save(cfg)

    state = str(kwargs.get("state"))
    if state in cfg.get("crash_arms", []):
        raise RuntimeError("CONTAINER_CRASH_MID_RUN")
    if state in cfg.get("timeout_arms", []):
        raise TimeoutError("WALL_DEADLINE_VIOLATION")

    tid = str(kwargs.get("tid"))
    test_files = list(kwargs.get("test_files") or [])
    isolated = kwargs.get("isolated")
    if isolated is None:
        raise RuntimeError("ISOLATED_REQUIRED")
    db_name = cfg.get("db_name_override", {}).get(state) or isolated.fresh_db_name()
    junit_dir = Path(str(kwargs.get("raw_junit_dir")))
    junit_dir.mkdir(parents=True, exist_ok=True)
    outcome = cfg.get("outcome_by_arm", {}).get(state, "PASS")
    files: dict[str, str] = {}
    for rep in range(3):
        for idx, _tf in enumerate(test_files):
            jname = f"{tid}_{state}_r{rep}_f{idx}.xml"
            if outcome == "FAILURE":
                body = (
                    '<testsuite name="pytest" tests="1" failures="1">'
                    '<testcase name="x"><failure message="boom">assert False</failure></testcase>'
                    "</testsuite>"
                )
            else:
                body = '<testsuite name="pytest" tests="1" failures="0"><testcase name="x" time="0.01"/></testsuite>'
            (junit_dir / jname).write_text(body, encoding="utf-8")
            files[jname] = outcome
    extra = cfg.get("extra_junit_file")
    if extra:
        (junit_dir / extra).write_text("<testsuite/>", encoding="utf-8")
    if cfg.get("omit_one_junit_file") and files:
        (junit_dir / sorted(files)[0]).unlink()
    res: dict = {
        "junit": files,
        "junit_failures": {},
        "db_name": db_name,
        "db_cleanup": "DROPPED_AFTER_JUNIT_PARSE",
        "junit_files": sorted(files),
    }
    if cfg.get("omit_cleanup_flag"):
        res["db_cleanup"] = "NO_CLEANUP_EVIDENCE"
    if cfg.get("omit_db_name"):
        del res["db_name"]
    return res
'''

ISOLATED_FAKE = '''\
"""TEST-ONLY fake frozen OpwsIsolatedRuntime (mirrors frozen contract)."""
from __future__ import annotations
import dataclasses
import datetime
import re
import secrets


@dataclasses.dataclass(frozen=True)
class OpwsIsolatedRuntime:
    worktree_linux: str = "/root/m19b_r3_20261024/wt_t"
    scratch_linux: str = ""
    scratch_windows: str = ""
    db_prefix: str = "opws_m3b_"
    db_commit_short: str = "000000000000"

    @property
    def container_results_dir(self) -> str:
        return "/results"

    @property
    def container_worktree_dst(self) -> str:
        return f"/workspace/{self.worktree_linux.rsplit('/', 1)[-1]}"

    def validate(self) -> None:
        if not self.scratch_linux or not self.scratch_windows:
            raise RuntimeError("SCRATCH_UNSET")
        if self.worktree_linux.rsplit("/", 1)[-1] != "wt_t":
            raise RuntimeError("WORKTREE_UNEXPECTED")
        if not re.fullmatch(r"[a-z0-9_]{1,32}", self.db_prefix + "x"):
            raise RuntimeError("DB_PREFIX_INVALID")

    def fresh_db_name(self) -> str:
        self.validate()
        stamp = datetime.datetime.now(datetime.UTC)
        nonce = secrets.token_hex(10)
        return f"{self.db_prefix}{self.db_commit_short}_{stamp:%H%M%S}_{nonce}"
'''

MATERIALIZER_FAKE = '''\
"""TEST-ONLY fake frozen materializer (stub)."""
import json
import sys
from pathlib import Path

argv = sys.argv[1:]
if "--out-dir" in argv:
    out = Path(argv[argv.index("--out-dir") + 1])
    out.mkdir(parents=True, exist_ok=True)
    cfg_path = Path(__file__).resolve().parent.parent.parent / "src/benchmark/wp2/engine_config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    (out / "record.json").write_text(json.dumps(cfg.get("materialize_record", {})), encoding="utf-8")
sys.exit(0)
'''


def write_fake_frozen_worktree(td: Path) -> Path:
    wt = td / "frozen_wt"
    (wt / "scripts").mkdir(parents=True)
    (wt / "src" / "benchmark" / "wp2").mkdir(parents=True)
    (wt / "scripts" / "opws_phase3b_patch_materialize.py").write_text(MATERIALIZER_FAKE, encoding="utf-8")
    (wt / "src" / "benchmark" / "wp2" / "harness_v3.py").write_text(HARNESS_FAKE, encoding="utf-8")
    (wt / "src" / "benchmark" / "wp2" / "opws_isolated_runtime_v1.py").write_text(ISOLATED_FAKE, encoding="utf-8")
    _write_engine_config(wt, {})
    return wt


def _write_engine_config(wt: Path, cfg: dict) -> None:
    base = {
        "outcome_by_arm": dict(CONTROL_EXPECTED),
        "crash_arms": [],
        "timeout_arms": [],
        "db_name_override": {},
        "extra_junit_file": None,
        "omit_one_junit_file": False,
        "omit_cleanup_flag": False,
        "omit_db_name": False,
        "materialize_record": {},
    }
    base.update(cfg)
    (wt / "src" / "benchmark" / "wp2" / "engine_config.json").write_text(
        json.dumps(base, indent=2), encoding="utf-8"
    )


def read_engine_history(wt: Path) -> list[dict]:
    cfg_path = wt / "src" / "benchmark" / "wp2" / "engine_config.json"
    return json.loads(cfg_path.read_text(encoding="utf-8")).get("history", [])


def build_plan_doc(
    td: Path,
    *,
    arms: list[str],
    worktrees: dict[str, Path],
    oids: dict[str, str],
    out_root: Path,
) -> dict:
    """Hermetic plan doc: per-arm plan from the REAL adapter row with
    ``effective_tree_oid`` overridden to each fixture repo's ACTUAL tree OID
    (receipt identity stays the frozen adapter row --- unit receipt is a
    TEST fixture)."""
    rows = {a["arm_id"]: dict(a) for a in _adapt.load_arms()}
    for arm in arms:
        if oids.get(arm):
            rows[arm]["effective_tree_oid"] = oids[arm]
    plans = []
    for arm in arms:
        # worktree paths are expressed POSIX-style exactly like the real
        # operator-supplied --worktrees-json (frozen Linux-side contract)
        wtmap = {a: worktrees[a].as_posix() for a in arms}
        p = mod.physical_plan_for(arm, matrix_by_arm=rows, worktrees=wtmap, out_root=out_root)
        plans.append(p)
    return {"schema": mod.SCHEMA_DRYRUN, "worktree": str(worktrees[arms[0]]), "arms": plans}


def make_mat_runner(
    rows: dict[str, dict], tamper_key: str | None = None, tamper_value: str | None = None
):
    """Injected materializer runner: records argv, writes a schema record whose
    scope_hash/reference_patch_sha256 match the arm plan (or tampered)."""

    def runner(argv: list[str], timeout_s: int = 900) -> SimpleNamespace:
        del timeout_s
        out_dir = Path(argv[argv.index("--out-dir") + 1])
        scope_json = argv[argv.index("--scope-json") + 1]
        arm = Path(scope_json).name.replace("scope_", "").replace(".json", "")
        row = rows[arm]
        rec = {
            "schema": "opws-phase3b-patch-materialize/1.0-engineering",
            "arm_id": arm,
            "scope_hash": row["scope_hash"],
            "reference_patch_sha256": row["patch_sha256"],
            "reference_patch_bytes": row["patch_bytes"],
            "test_contract_hash": row["test_contract_hash"],
        }
        if tamper_key:
            rec[tamper_key] = tamper_value or ("0" * 64)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "record.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="MATERIALIZE_RECORD_OK", stderr="")

    return runner


def _arm_worktree(td: Path, arm: str, content: dict[str, str] | None = None) -> tuple[Path, str]:
    # the FROZEN isolated runtime requires the execution worktree BASENAME
    # 'wt_t' (OpwsIsolatedRuntime.validate()); per-arm distinct paths live in
    # per-arm parent directories
    content = content or {f"file_{arm}.py": f"x = {arm!r}"}
    wt = td / arm / "wt_t"
    oid = make_git_repo(wt, content)
    return wt, oid


def _run_bridge_cfg(
    td: Path,
    *,
    arms: list[str],
    engine_cfg: dict | None = None,
    tamper_key: str | None = None,
    deadline_utc: str | None = None,
    probe: object | None = None,
) -> tuple[dict, Path, list[dict]]:
    """Run the bridge against a hermetic fixture; returns
    (result, fake_frozen_worktree, engine_call_history).  History is
    snapshotted while the fixture is alive (the tempdir is torn down by the
    caller's ``with`` block)."""
    wt = write_fake_frozen_worktree(td)
    _write_engine_config(wt, engine_cfg or {})
    rows = {a["arm_id"]: dict(a) for a in _adapt.load_arms()}
    worktrees: dict[str, Path] = {}
    oids: dict[str, str] = {}
    for arm in arms:
        wtpath, oid = _arm_worktree(td / "worktrees", arm)
        worktrees[arm] = wtpath
        oids[arm] = oid
    out_root = td / "out"
    scope_dir = td / "scopes"
    scope_dir.mkdir()
    for arm in arms:
        (scope_dir / f"scope_{arm}.json").write_text(json.dumps({"arm": arm}), encoding="utf-8")
    cls = td / "classification.json"
    authf = td / "test_authority.json"
    cls.write_text("{}", encoding="utf-8")
    authf.write_text("{}", encoding="utf-8")
    plan_doc = build_plan_doc(td, arms=arms, worktrees=worktrees, oids=oids, out_root=out_root)
    auth = {
        "authorized_arms": list(arms),
        "max_wall_s": 7200,
        "exclusivity_window": {},  # unit bridge: sequencing/evidence only
        "recorded_by": "test-operator",
    }
    budget = {"status": "OK", "benchmark_api_model_usd": 0.0, "request_count": 0, "max_wall_s": 3600}
    if probe is None:
        probe = []
    result = mod.run_bridge(
        plan_doc,
        rd8={"status": "ADOPT_PILOT_ONLY"},
        auth=auth,
        budget=budget,
        worktree=wt,
        source_repo=td,
        scopes_dir=scope_dir,
        classification=cls,
        test_authority=authf,
        out_root=out_root,
        deadline_utc=deadline_utc,
        materializer=make_mat_runner(rows, tamper_key),
        postrun_db_probe=(lambda: list(probe)),  # type: ignore[arg-type]
    )
    return result, wt, read_engine_history(wt)


class TestD1PerArmPlanSelection(unittest.TestCase):
    def test_fully_admitted_bridge_selects_per_arm_plan_not_top_level(self):
        # D3 defect 1: the old bridge read plan["worktree_linux"] from the plan
        # DOC top level -> KeyError on a fully admitted run.  The repaired
        # bridge must read the arm's own plan entry and run it.
        with tempfile.TemporaryDirectory() as td:
            result, _wt, history = _run_bridge_cfg(Path(td), arms=["NEG"], probe=[])
        self.assertEqual(result["overall"], "PASS", result)
        self.assertEqual(len(history), 1)
        self.assertTrue(history[0]["worktree_linux"].endswith("/wt_t"))
        by_arm = {a["arm_id"]: a for a in result["arms"]}
        self.assertEqual(
            by_arm["NEG"]["stages"]["plan_selection"]["worktree_linux"],
            history[0]["worktree_linux"],
            "engine must run the PER-ARM plan worktree, never a top-level key",
        )

    def test_missing_arm_plan_stops_typed(self):
        with tempfile.TemporaryDirectory() as td:
            wt = write_fake_frozen_worktree(Path(td))
            _write_engine_config(wt, {})
            plan_doc = {"schema": mod.SCHEMA_DRYRUN, "arms": []}
            with self.assertRaises(Exception) as ctx:
                mod.run_bridge(
                    plan_doc,
                    rd8={"status": "ADOPT_PILOT_ONLY"},
                    auth={"authorized_arms": ["NEG"]},
                    budget={"status": "OK"},
                    worktree=wt,
                    source_repo=Path(td),
                    scopes_dir=Path(td),
                    classification=Path(td),
                    test_authority=Path(td),
                    out_root=Path(td) / "out",
                    materializer=make_mat_runner({}),
                    postrun_db_probe=lambda: [],
                )
            # typed per-arm plan-selection failure (D1): missing "arms" or a
            # missing arm must never silently proceed
            self.assertIn("PLAN", str(ctx.exception))


class TestD2RealInstallFragment(unittest.TestCase):
    def test_engine_receives_real_lock_install_fragment(self):
        with tempfile.TemporaryDirectory() as td:
            result, _wt, history = _run_bridge_cfg(Path(td), arms=["NEG"], probe=[])
        self.assertEqual(result["overall"], "PASS", result)
        frag = history[0]["install_fragment"]
        self.assertTrue(frag.startswith("REAL_LOCK_FRAGMENT:"), frag)
        self.assertNotEqual(frag, "computed")
        stage = result["arms"][0]["stages"]["install_fragment"]
        self.assertEqual(stage["mode"], "LOCK_EXACT")
        self.assertTrue(stage.get("fragment_sha256"))
        self.assertNotIn("computed", str(stage))


class TestD3NoInventedStatusBooleans(unittest.TestCase):
    def test_teardown_requires_real_post_run_db_scan(self):
        # probe unavailable -> NOT verified -> never PASS
        with tempfile.TemporaryDirectory() as td:
            wt = write_fake_frozen_worktree(Path(td))
            _write_engine_config(wt, {})
            rows = {a["arm_id"]: dict(a) for a in _adapt.load_arms()}
            arm = "NEG"
            wtpath, oid = _arm_worktree(Path(td) / "w", arm)
            out_root = Path(td) / "out"
            scope_dir = Path(td) / "scopes"
            scope_dir.mkdir()
            (scope_dir / f"scope_{arm}.json").write_text("{}", encoding="utf-8")
            cls = Path(td) / "c.json"
            authf = Path(td) / "a.json"
            cls.write_text("{}", encoding="utf-8")
            authf.write_text("{}", encoding="utf-8")
            plan_doc = build_plan_doc(
                Path(td), arms=[arm], worktrees={arm: wtpath}, oids={arm: oid}, out_root=out_root
            )
            result = mod.run_bridge(
                plan_doc,
                rd8={"status": "ADOPT_PILOT_ONLY"},
                auth={"authorized_arms": [arm]},
                budget={"status": "OK"},
                worktree=wt,
                source_repo=Path(td),
                scopes_dir=scope_dir,
                classification=cls,
                test_authority=authf,
                out_root=out_root,
                materializer=make_mat_runner(rows),
                postrun_db_probe=None,  # probe ABSENT
            )
        self.assertEqual(result["overall"], "FAIL")
        self.assertEqual(result["arms"][0]["status"], "FAIL")
        self.assertIn("TEARDOWN_NOT_VERIFIED", result["arms"][0].get("reason", ""))

    def test_db_teardown_failure_stops(self):
        with tempfile.TemporaryDirectory() as td:
            result, _wt, _hist = _run_bridge_cfg(
                Path(td), arms=["NEG"], probe=["opws_m3b_7e42fc67_083233_ab12cd34ef56"]
            )
        self.assertEqual(result["overall"], "FAIL")
        self.assertEqual(result["arms"][0]["status"], "FAIL")
        self.assertIn("DB_LEFTOVER", result["arms"][0].get("reason", ""))

    def test_clean_probe_is_captured_evidence_not_invented_boolean(self):
        with tempfile.TemporaryDirectory() as td:
            result, _wt, _hist = _run_bridge_cfg(Path(td), arms=["NEG"], probe=[])
        stage = result["arms"][0]["stages"]["post_run_teardown"]
        self.assertTrue(stage["db_deleted"] is True)
        self.assertEqual(stage["post_run_db_scan"], [])  # REAL probe output, not invented
        self.assertEqual(stage["engine_db_cleanup"], "DROPPED_AFTER_JUNIT_PARSE")

    def test_executor_never_claims_runtime_image_resolution(self):
        with tempfile.TemporaryDirectory() as td:
            result, _wt, _hist = _run_bridge_cfg(Path(td), arms=["NEG"], probe=[])
        stage = result["arms"][0]["stages"]["runtime_image_resolved"]
        # the executor delegates to the frozen engine's first fail-closed step
        self.assertIn("delegated", str(stage).lower())
        self.assertNotIn("validated", [k.lower() for k in stage])


class TestD4ControlSequencing(unittest.TestCase):
    def test_scrambled_authorization_still_runs_frozen_control_order(self):
        # Option B demands separate physical runs in frozen control order
        # NEG -> FULL_REFERENCE -> RM_CSS -> SIP.  The sequential driver shares
        # one OS pid; the frozen engine result exposes no per-state container
        # id, so the Option-B process-identity gate is UNPROVABLE in one
        # process: the bridge must report that gap (FAIL), never a fake PASS.
        scrambled = ["SIP", "RM_CSS", "NEG", "FULL_REFERENCE"]
        with tempfile.TemporaryDirectory() as td:
            result, _wt, history = _run_bridge_cfg(Path(td), arms=scrambled, probe=[])
        self.assertEqual(
            [h["state"] for h in history],
            ["NEG", "FULL_REFERENCE", "RM_CSS", "SIP"],
            "frozen control order must win over authorization order",
        )
        by_arm = {a["arm_id"]: a for a in result["arms"]}
        self.assertTrue(all(by_arm[a]["executed"] for a in ("NEG", "FULL_REFERENCE", "RM_CSS", "SIP")))
        self.assertEqual(result["overall"], "FAIL")
        self.assertIn("IDENTITY_GAP", result.get("note", ""))
        self.assertIn("container", result.get("note", "").lower())

    def test_neg_expected_failure_is_control_expected_never_pass(self):
        with tempfile.TemporaryDirectory() as td:
            result, _wt, _hist = _run_bridge_cfg(Path(td), arms=["NEG"], probe=[])
        arm = result["arms"][0]
        self.assertEqual(arm["status"], "CONTROL_EXPECTED")
        self.assertEqual(arm["control_outcome"], "CONTROL_EXPECTED")
        self.assertNotEqual(arm["status"], "PASS")
        self.assertEqual(result["overall"], "PASS", "NEG control gate met; single-arm run may proceed")

    def test_control_mismatch_stops_before_sip(self):
        # NEG produces PASS files although its frozen control expects FAILURE:
        # the FIRST control mismatches so SIP (and the other controls) never run.
        with tempfile.TemporaryDirectory() as td:
            result, _wt, history = _run_bridge_cfg(
                Path(td),
                arms=list(PILOT_ARMS),
                engine_cfg={"outcome_by_arm": {**CONTROL_EXPECTED, "NEG": "PASS"}},
                probe=[],
            )
        self.assertEqual([h["state"] for h in history], ["NEG"], "bridge stops at first control mismatch")
        self.assertEqual(result["overall"], "FAIL")
        by_arm = {a["arm_id"]: a for a in result["arms"]}
        self.assertEqual(by_arm["NEG"]["status"], "FAIL")
        self.assertIn("CONTROL_MISMATCH", by_arm["NEG"].get("reason", ""))
        for arm in ("FULL_REFERENCE", "RM_CSS", "SIP"):
            self.assertEqual(by_arm[arm]["status"], "NOT_RUN")

    def test_infra_failure_stops_before_sip_no_retries(self):
        with tempfile.TemporaryDirectory() as td:
            result, _wt, history = _run_bridge_cfg(
                Path(td), arms=list(PILOT_ARMS), engine_cfg={"crash_arms": ["NEG"]}, probe=[]
            )
        self.assertEqual(len(history), 1, "no retries after infrastructure failure")
        self.assertEqual(result["overall"], "FAIL")
        by_arm = {a["arm_id"]: a for a in result["arms"]}
        self.assertEqual(by_arm["NEG"]["status"], "FAIL")
        self.assertEqual(by_arm["SIP"]["status"], "NOT_RUN")

    def test_sip_records_its_own_outcome_without_protocol_change(self):
        # If SIP itself F2P-fails, the negative outcome is recorded as data
        # (single-arm scope: no cross-arm identity gate involved).
        with tempfile.TemporaryDirectory() as td:
            result, _wt, _hist = _run_bridge_cfg(
                Path(td),
                arms=["SIP"],
                engine_cfg={"outcome_by_arm": {**CONTROL_EXPECTED, "SIP": "FAILURE"}},
                probe=[],
            )
        by_arm = {a["arm_id"]: a for a in result["arms"]}
        self.assertEqual(result["overall"], "PASS", "SIP outcome is data, not a gate failure")
        self.assertEqual(by_arm["SIP"]["observed_classifications"], ["FAILURE"])


class TestD5UtcWindowAndWallCap(unittest.TestCase):
    def _auth_payload(self, **kw: object) -> dict:
        payload = {
            "schema": "t12_m02_execution_authorization_v1",
            "grant": "RD9_F2P_PILOT",
            "authorized_arms": list(PILOT_ARMS),
            "exclusivity_window": {"start_utc": "2026-11-10T08:00:00Z", "end_utc": "2026-11-10T20:00:00Z"},
            "max_wall_s": 7200,
            "recorded_by": "researcher",
        }
        payload.update(kw)
        return payload

    def test_invalid_window_timestamp_stops(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "a.json"
            p.write_text(
                json.dumps(
                    self._auth_payload(
                        exclusivity_window={
                            "start_utc": "not-a-date",
                            "end_utc": "2026-11-10T20:00:00Z",
                        }
                    )
                ),
                encoding="utf-8",
            )
            r = mod.validate_authorization(p, PILOT_ARMS)
        self.assertEqual(r["status"], "STOP")
        self.assertIn("window", r["reason"].lower())

    def test_expired_window_stops(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "a.json"
            past = "2020-01-01T00:00:00Z"
            p.write_text(
                json.dumps(
                    self._auth_payload(
                        exclusivity_window={"start_utc": past, "end_utc": "2020-01-01T12:00:00Z"}
                    )
                ),
                encoding="utf-8",
            )
            r = mod.validate_authorization(p, PILOT_ARMS)
        self.assertEqual(r["status"], "STOP")
        self.assertIn("expired", r["reason"].lower())

    def test_window_not_yet_started_stops(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "a.json"
            future = "2099-01-01T00:00:00Z"
            p.write_text(
                json.dumps(
                    self._auth_payload(
                        exclusivity_window={"start_utc": future, "end_utc": "2099-01-01T12:00:00Z"}
                    )
                ),
                encoding="utf-8",
            )
            r = mod.validate_authorization(p, PILOT_ARMS)
        self.assertEqual(r["status"], "STOP")
        self.assertIn("not", r["reason"].lower())

    def test_wall_cap_higher_than_remaining_window_stops(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "a.json"
            p.write_text(
                json.dumps(
                    self._auth_payload(
                        exclusivity_window={
                            "start_utc": "2026-11-10T08:00:00Z",
                            "end_utc": "2026-11-10T08:00:10Z",
                        },
                        max_wall_s=60,
                    )
                ),
                encoding="utf-8",
            )
            r = mod.validate_authorization(p, PILOT_ARMS)
        self.assertEqual(r["status"], "STOP")
        self.assertIn("window", r["reason"].lower())

    def test_valid_window_grants_with_attestation_label(self):
        now = datetime.datetime(2026, 11, 10, 9, 0, 0, tzinfo=datetime.UTC)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "a.json"
            p.write_text(
                json.dumps(
                    self._auth_payload(
                        exclusivity_window={
                            "start_utc": "2026-11-10T08:00:00Z",
                            "end_utc": "2026-11-10T20:00:00Z",
                        }
                    )
                ),
                encoding="utf-8",
            )
            r = mod.validate_authorization(p, PILOT_ARMS, now_utc=now)
        self.assertEqual(r["status"], "GRANTED")
        self.assertIn("attestation", str(r).lower())
        self.assertIn("not a cryptographic signature", str(r).lower())

    def test_wall_deadline_blocks_arms_before_side_effect(self):
        with tempfile.TemporaryDirectory() as td:
            result, _wt, history = _run_bridge_cfg(
                Path(td), arms=list(PILOT_ARMS), deadline_utc="2020-01-01T00:00:00Z", probe=[]
            )
        self.assertEqual(history, [], "no engine call after the wall deadline")
        self.assertEqual(result["overall"], "FAIL")
        by_arm = {a["arm_id"]: a for a in result["arms"]}
        for arm in PILOT_ARMS:
            self.assertEqual(by_arm[arm]["status"], "NOT_RUN")
            self.assertIn("WALL_DEADLINE", by_arm[arm].get("reason", ""))


class TestD6WorktreeContract(unittest.TestCase):
    def test_worktree_basename_must_be_wt_t(self):
        # The frozen OpwsIsolatedRuntime.validate() requires basename wt_t.
        with tempfile.TemporaryDirectory() as td:
            wt = write_fake_frozen_worktree(Path(td))
            _write_engine_config(wt, {})
            rows = {a["arm_id"]: dict(a) for a in _adapt.load_arms()}
            arm = "NEG"
            wtpath, oid = _arm_worktree(Path(td) / "w", arm)
            bad_path = wtpath.parent / "wt_t_NEG"
            wtpath.rename(bad_path)
            out_root = Path(td) / "out"
            scope_dir = Path(td) / "scopes"
            scope_dir.mkdir()
            (scope_dir / f"scope_{arm}.json").write_text("{}", encoding="utf-8")
            cls = Path(td) / "c.json"
            authf = Path(td) / "a.json"
            cls.write_text("{}", encoding="utf-8")
            authf.write_text("{}", encoding="utf-8")
            plan_doc = build_plan_doc(
                Path(td), arms=[arm], worktrees={arm: bad_path}, oids={arm: oid}, out_root=out_root
            )
            result = mod.run_bridge(
                plan_doc,
                rd8={"status": "ADOPT_PILOT_ONLY"},
                auth={"authorized_arms": [arm]},
                budget={"status": "OK"},
                worktree=wt,
                source_repo=Path(td),
                scopes_dir=scope_dir,
                classification=cls,
                test_authority=authf,
                out_root=out_root,
                materializer=make_mat_runner(rows),
                postrun_db_probe=lambda: [],
            )
        self.assertEqual(result["overall"], "FAIL")
        self.assertEqual(result["arms"][0]["status"], "FAIL")
        self.assertIn("WORKTREE_UNEXPECTED", result["arms"][0].get("reason", ""))

    def test_wrong_worktree_tree_stops_before_any_side_effect(self):
        # The worktree contains the WRONG tree (unmodified target or another
        # scope): the arm must never execute and the materializer must not run.
        with tempfile.TemporaryDirectory() as td:
            wt = write_fake_frozen_worktree(Path(td))
            _write_engine_config(wt, {})
            arm = "NEG"
            wrong, _wrong_oid = _arm_worktree(Path(td) / "w", arm, content={"other.py": "different"})
            out_root = Path(td) / "out"
            scope_dir = Path(td) / "scopes"
            scope_dir.mkdir()
            (scope_dir / f"scope_{arm}.json").write_text("{}", encoding="utf-8")
            cls = Path(td) / "c.json"
            authf = Path(td) / "a.json"
            cls.write_text("{}", encoding="utf-8")
            authf.write_text("{}", encoding="utf-8")
            # expected OID = a DIFFERENT repo's tree (deliberately mismatched)
            _other, other_oid = _arm_worktree(Path(td) / "o", "other", content={"file.py": "other"})
            calls: list[str] = []

            def mat_runner(argv: list[str], timeout_s: int = 900) -> SimpleNamespace:
                del timeout_s
                calls.append(argv)
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            plan_doc = build_plan_doc(
                Path(td), arms=[arm], worktrees={arm: wrong}, oids={arm: other_oid}, out_root=out_root
            )
            result = mod.run_bridge(
                plan_doc,
                rd8={"status": "ADOPT_PILOT_ONLY"},
                auth={"authorized_arms": [arm]},
                budget={"status": "OK"},
                worktree=wt,
                source_repo=Path(td),
                scopes_dir=scope_dir,
                classification=cls,
                test_authority=authf,
                out_root=out_root,
                materializer=mat_runner,
                postrun_db_probe=lambda: [],
            )
            history_after = read_engine_history(wt)
        self.assertEqual(result["overall"], "FAIL")
        self.assertEqual(result["arms"][0]["status"], "FAIL")
        self.assertIn("WORKTREE_OID_MISMATCH", result["arms"][0].get("reason", ""))
        self.assertEqual(calls, [], "materializer must not run before tree proof")
        self.assertEqual(history_after, [], "engine must never run the wrong tree")

    def test_correct_worktree_content_runs(self):
        with tempfile.TemporaryDirectory() as td:
            result, _wt, _hist = _run_bridge_cfg(Path(td), arms=["NEG"], probe=[])
        self.assertEqual(result["overall"], "PASS", result)
        self.assertEqual(
            result["arms"][0]["stages"]["worktree_input"]["tree_proven_oid"],
            result["arms"][0]["stages"]["worktree_input"]["expected_oid"],
        )


class TestD7RealReceipts(unittest.TestCase):
    def test_extra_junit_file_fails_receipt_not_pass(self):
        with tempfile.TemporaryDirectory() as td:
            result, _wt, _hist = _run_bridge_cfg(
                Path(td), arms=["NEG"], engine_cfg={"extra_junit_file": "junk_extra.xml"}, probe=[]
            )
        self.assertEqual(result["overall"], "FAIL")
        self.assertEqual(result["arms"][0]["status"], "FAIL")
        self.assertIn("junit", result["arms"][0].get("reason", "").lower())

    def test_missing_junit_file_fails_receipt(self):
        # the engine reports 9 but the physical files are fewer -> fail closed
        with tempfile.TemporaryDirectory() as td:
            result, _wt, _hist = _run_bridge_cfg(
                Path(td), arms=["NEG"], engine_cfg={"omit_one_junit_file": True}, probe=[]
            )
        self.assertEqual(result["overall"], "FAIL")
        self.assertEqual(result["arms"][0]["status"], "FAIL")

    def test_repeated_db_identity_across_arms_fails(self):
        with tempfile.TemporaryDirectory() as td:
            same_db = "opws_m3b_7e42fc67_083233_ab12cd34ef56"
            result, _wt, _hist = _run_bridge_cfg(
                Path(td),
                arms=["NEG", "FULL_REFERENCE", "RM_CSS", "SIP"],
                engine_cfg={"db_name_override": {a: same_db for a in PILOT_ARMS}},
                probe=[],
            )
        self.assertEqual(result["overall"], "FAIL")
        self.assertIn("IDENTITY", str(result.get("note", "")).upper())

    def test_engine_must_prove_db_cleanup_flag(self):
        with tempfile.TemporaryDirectory() as td:
            result, _wt, _hist = _run_bridge_cfg(
                Path(td), arms=["NEG"], engine_cfg={"omit_cleanup_flag": True}, probe=[]
            )
        self.assertEqual(result["overall"], "FAIL")
        self.assertEqual(result["arms"][0]["status"], "FAIL")
        self.assertIn("DB_CLEANUP_UNPROVEN", result["arms"][0].get("reason", ""))


class TestD8OracleBoundary(unittest.TestCase):
    def test_oracle_bytes_never_reach_engine_and_materializer_digests_must_match(self):
        with tempfile.TemporaryDirectory() as td:
            result, _wt, history = _run_bridge_cfg(Path(td), arms=["NEG"], probe=[])
        self.assertEqual(result["overall"], "PASS", result)
        for h in history:
            self.assertEqual(
                h["_oracle_keys_present"], [],
                "classification/test-authority must never reach run_state_v3",
            )
        for arm in result["arms"]:
            self.assertEqual(arm["stages"]["materialize"]["record_digests_match"], True)

    def test_tampered_materializer_scope_digest_stops_before_engine(self):
        with tempfile.TemporaryDirectory() as td:
            result, _wt, history = _run_bridge_cfg(Path(td), arms=["NEG"], tamper_key="scope_hash", probe=[])
        self.assertEqual(result["overall"], "FAIL")
        self.assertEqual(result["arms"][0]["status"], "FAIL")
        self.assertIn("MATERIALIZER_RECORD_MISMATCH", result["arms"][0].get("reason", ""))
        self.assertEqual(history, [], "tampered selector input must never reach the engine")

    def test_gold_is_not_a_pilot_comparator(self):
        self.assertNotIn("GOLD", PILOT_ARMS)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "a.json"
            p.write_text(
                json.dumps(
                    {
                        "schema": "t12_m02_execution_authorization_v1",
                        "grant": "RD9_F2P_PILOT",
                        "authorized_arms": ["SIP", "GOLD"],
                        "exclusivity_window": {
                            "start_utc": "2026-11-10T08:00:00Z",
                            "end_utc": "2026-11-10T20:00:00Z",
                        },
                        "max_wall_s": 7200,
                        "recorded_by": "researcher",
                    }
                ),
                encoding="utf-8",
            )
            r = mod.validate_authorization(p, PILOT_ARMS)
        self.assertEqual(r["status"], "STOP")
        self.assertIn("GOLD", r["reason"])


if __name__ == "__main__":
    unittest.main()
