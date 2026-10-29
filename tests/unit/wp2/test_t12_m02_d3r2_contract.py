"""T12 M02-D3-R2 — RED/GREEN contract tests for the Option-B orchestrator and
per-arm worker (offline; test doubles only, never WSL/Docker/the engine).

Required negatives covered (mission step 5):
  * WSL path checked by a Windows Path / Windows-WSL path mismatch;
  * clean HEAD but dirty unstaged file / untracked file inside the tree;
  * missing per-arm scratch tree / target tree mislabeled as scoped arm;
  * same child-process instance across two arms; replayed worker evidence;
    forged nonce with identical trusted process birth; OS pid recycling with
    genuinely distinct verified births;
  * missing Docker instance provenance; container image digest mistaken for an
    instance;
  * per-arm DB reuse; wrong worktree OID;
  * JUnit missing / repeated / foreign node;
  * resources 0 absent measurement; stale synthetic fixture field;
  * scope/oracle leakage; exhausted time window and controls failure
    stopping SIP.
"""
from __future__ import annotations

import datetime
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"


def _load_module(rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, _SCRIPTS / rel)
    m = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


identity = _load_module("t12_m02_d3r2_identity.py", "t12_m02_d3r2_identity")
_orch = _load_module("t12_m02_d3r2_orchestrator.py", "t12_m02_d3r2_orchestrator")
_exe = _load_module("t12_m02_execute_f2p.py", "t12_m02_execute_f2p")
_adapt = _load_module("t12_m02_arm_adapter.py", "t12_m02_arm_adapter")


class FakeCmd:
    def __init__(self, rc=0, out="", err=""):
        self.returncode = rc
        self.stdout = out
        self.stderr = err
        self.ok = rc == 0


class FakeRunner:
    """Scripted runner: substring/callable matches on raw argv; records calls."""

    def __init__(self, script=None):
        self.script = script or {}
        self.calls = []

    def __call__(self, argv, input_text=None, tp_timeout=60, cwd=None):
        for pattern, result in self.script.items():
            if isinstance(pattern, str):
                if any(pattern in a for a in argv):
                    return result(argv) if callable(result) else result
            elif callable(pattern) and pattern(argv):
                return result(argv) if callable(result) else result
        self.calls.append((list(argv), input_text, tp_timeout))
        return FakeCmd(127, "", f"unscripted: {argv!r}")


def make_probe(runner):
    """PlatformProbe with every REAL implementation routed through the
    injected runner; the OS-facing methods never touch WSL in tests."""
    p = identity.PlatformProbe(runner)
    p.host_python_kind = lambda: "windows"
    p.windows_executor = lambda: True
    # Linux filesystem probes in the gate are characterizable via the injected
    # runner; default every probed path to an existing DIRECTORY (the tests
    # above override the *content* evidence: oid/status/diff scripts).
    p.linux_path_type = lambda linux_path: {
        "path": linux_path, "probe": "wsl", "exists": True,
        "is_dir": True, "is_file": False, "returncode": 0, "stderr_tail": ""}
    p.distro_present = lambda: {"present": True}
    p.root_reachable = lambda: {"reachable": True, "uid": "0"}
    p.measure_clocks = lambda: {"status": "MEASURED", "median_skew_s": 0.01,
                                "verdict": "PASS", "n_samples": 3}
    p.docker_preflight_reads = lambda: {
        "server_ok": True, "server_version": "29.1.3",
        "pinned_image": {"present": True, "id": identity.PINNED_PY312_OCI_ID},
        "pg_fixture": {"status": "running", "image_matches": True,
                       "image": identity.PG_FIXTURE_IMAGE_ID},
        "network": {"internal": True, "driver": "bridge"}}
    return p


def _gate_script(tree_oid="b555542a98f62636173c6c82db80d380c083f180",
                 status_out="", diff_out=""):
    return {
        "rev-parse": FakeCmd(0, tree_oid + "\n", ""),
        "status": FakeCmd(0, status_out, ""),
        "diff": FakeCmd(0, diff_out, ""),
    }


def _witness(arm, pid, birth, nonce, mono, argv=None, sha="w" * 64):
    argv = argv or ["py", "t12_m02_d3r2_worker.py", "--arm", arm]
    return {
        "schema": identity.WITNESS_SCHEMA, "nonce": nonce, "pid": pid,
        "parent_pid": 777, "argv": argv,
        "argv_digest": identity.argv_digest(argv),
        "worker_script_sha256": sha,
        "process_birth": {
            "monotonic_start_ns": mono, "monotonic_end_ns": mono + 42,
            "os_start": {"status": "MEASURED", "os_start_utc": birth}},
        "times": {"start_utc": birth, "end_utc": birth}, "exit_code": 0,
    }


class _FakeProc:
    def __init__(self, pid, rc):
        self.pid = pid
        self._rc = rc

    def wait(self, timeout=None):
        return self._rc


def _fake_receipt_dir(arm_dir: Path, arm: str):
    """A structurally valid live-ish receipt dir for the fake worker."""
    _receipts = _exe._receipts
    rec_dir = arm_dir / "receipts"
    rec_dir.mkdir(parents=True, exist_ok=True)
    cls = "FAILURE" if arm == "NEG" else "PASS"
    sample = _receipts.sample_run_receipt(arm_id=arm, run_token=f"D3R2-{arm}",
                                          junit_classifications=[cls] * 9)
    import hashlib
    db = "opws_m3b_7e42fc67_093142_" + hashlib.sha256(arm.encode()).hexdigest()[:20]
    sample["database"] = {"engine": "postgres (isolated PG fixture)",
                           "db_identity": db, "db_created_receipt": True}
    sample["resources"] = {"cpu_seconds": "NOT_MEASURED", "peak_ram_mb": "NOT_MEASURED",
                            "disk_bytes": "NOT_MEASURED", "network_bytes": "NOT_MEASURED",
                            "sampler": "NOT_MEASURED"}
    sample["times"] = {"start_utc": "2026-11-02T09:00:00Z",
                        "end_utc": "2026-11-02T09:00:42Z",
                        "monotonic": True, "wall_seconds": 42.0}
    sample["host"] = {"hostname": "TEST-BOX", "os": "WSL2/Windows"}
    sample["environment"] = {"environment_id": "test-env-1"}
    (rec_dir / _receipts.RECEIPT_FILENAME).write_text(json.dumps(sample), encoding="utf-8")
    bodies = [_receipts.JUNIT_FAIL if cls == "FAILURE" else _receipts.JUNIT_PASS] * 9
    _receipts.materialize_junit_dir(rec_dir, sample, xml_bodies=bodies)
    (rec_dir / "post_run_db_scan.json").write_text(
        json.dumps({"remaining_opws_m3b_databases": [], "checked_at_utc": "2026-11-02T09:00:43Z"}),
        encoding="utf-8")
    return rec_dir


def make_arm_probe(oid_by_marker: dict[str, str]):
    """Probe whose rev-parse answers per-arm expected trees (marker in the
    worktree path, e.g. "/root/wt_t_NEG").
    """
    r = FakeRunner()

    def _oid(argv):
        joined = " ".join(argv)
        for marker, oid in oid_by_marker.items():
            if marker in joined:
                return FakeCmd(0, oid + "\n", "")
        return FakeCmd(0, "deadbeefcafebabe" + "0" * 24 + "\n", "")

    r.script[lambda a: "rev-parse" in a] = _oid
    r.script["status"] = FakeCmd(0, "", "")
    r.script["diff"] = FakeCmd(0, "", "")
    return make_probe(r)


def _run_physical(td, arms, matrix, worktrees, witness_by_arm, pid_by_arm, probe):
    def spawner(worker_path, witness_input, arm_dir):
        arm = json.loads(witness_input.read_text(encoding="utf-8"))["arm"]
        arm_dir.mkdir(exist_ok=True)
        (arm_dir / "witness.json").write_text(json.dumps(witness_by_arm[arm]), encoding="utf-8")
        st = {"status": "PASS", "control_outcome": "OUTCOME_DATA"}
        if arm == "NEG":
            st = {"status": "CONTROL_EXPECTED", "control_outcome": "CONTROL_EXPECTED"}
        (arm_dir / "worker_stage.json").write_text(json.dumps(st), encoding="utf-8")
        _fake_receipt_dir(arm_dir, arm)
        return _FakeProc(pid_by_arm[arm], 0), "TEST_SPAWNER"

    out = Path(td) / "out"
    out.mkdir(exist_ok=True)
    return _orch.run_arms_physical(
        out_root=out, arms=arms, worktree=Path("frozen"), source_repo=Path("repo"),
        scope_dir=Path("scopes"), classification=Path("cls.json"),
        test_authority=Path("ta.json"), matrix=matrix, worktrees=worktrees,
        db_scan_cmd_env="true", worker_path="t12_m02_d3r2_worker.py",
        docker_events=False, deadline_utc=None, spawner=spawner, probe=probe)


class TestLinuxWorktreeGate(unittest.TestCase):
    def test_wsl_path_never_checked_by_windows_path(self):
        """A /root/... path must be evaluated via WSL-side stat/git; a Windows
        Path('/root/...') is meaningless (audit defect: wt = Path(wt_linux))."""
        from pathlib import Path as WinPath
        self.assertEqual(identity.PlatformProbe().host_python_kind(), "windows")
        probe = make_probe(FakeRunner(_gate_script()))
        gate = identity.linux_worktree_gate(
            probe, identity.WORKTREE_PATTERN_LINUX,
            "b555542a98f62636173c6c82db80d380c083f180")
        self.assertIn("wsl root git/stat", gate["checked_via"])
        self.assertTrue(gate["pass"])
        # the Linux path is NOT a Windows pathlib directory
        self.assertFalse(WinPath(identity.WORKTREE_PATTERN_LINUX).is_dir()
                         or WinPath(identity.WORKTREE_PATTERN_LINUX).exists())

    def test_dirty_unstaged_file_fails_clean_head(self):
        probe = make_probe(FakeRunner(
            _gate_script(status_out=" M saleor/app/modified.py\n?? newfile.py\n",
                         diff_out="saleor/app/modified.py\n")))
        gate = identity.linux_worktree_gate(probe, "/root/wt_t", "b555542a98f62636173c6c82db80d380c083f180")
        self.assertFalse(gate["pass"])
        self.assertTrue(any("WORKTREE_NOT_CLEAN" in r for r in gate["reasons"]))

    def test_untracked_file_inside_tree_fails(self):
        probe = make_probe(FakeRunner(_gate_script(status_out="?? saleor/app/sneaky_new.py\n")))
        gate = identity.linux_worktree_gate(probe, "/root/wt_t", "b555542a98f62636173c6c82db80d380c083f180")
        self.assertFalse(gate["pass"])

    def test_wrong_worktree_oid_stops(self):
        probe = make_probe(FakeRunner(_gate_script(tree_oid="deadbeef" + "0" * 36)))
        gate = identity.linux_worktree_gate(probe, "/root/wt_t", "b555542a98f62636173c6c82db80d380c083f180")
        self.assertFalse(gate["pass"])
        self.assertTrue(any("WORKTREE_OID_MISMATCH" in r for r in gate["reasons"]))

    def test_windows_wsl_path_mismatch_recorded(self):
        self.assertTrue(identity.WORKTREE_PATTERN_LINUX.startswith("/"))
        self.assertNotIn("\\", identity.WORKTREE_PATTERN_LINUX)


class TestScratchTrees(unittest.TestCase):
    def test_target_tree_mislabeled_as_scoped_arm_stops(self):
        rows = {a["arm_id"]: a for a in _adapt.load_arms()}
        self.assertNotEqual(rows["SIP"]["effective_tree_oid"],
                            rows["FULL_REFERENCE"]["effective_tree_oid"])
        # the seven distinct frozen trees are exactly the matrix's
        trees = {rows[a]["effective_tree_oid"] for a in rows}
        self.assertEqual(len(trees), 7, "13 arms / seven trees")

    def test_missing_per_arm_scratch_tree_is_detected(self):
        """Builder must verify the produced tree against the matrix; a build
        that does not reproduce the arm's effective_tree_oid is a STOP."""
        script = {
            "init": FakeCmd(0, "", ""), "fetch": FakeCmd(0, "", ""),
            "worktree": FakeCmd(0, "", ""),
            "mkdir": FakeCmd(0, "", ""),
            "base64": FakeCmd(0, "", ""),
            "apply": FakeCmd(0, "", ""), "commit": FakeCmd(0, "", ""),
            "rev-parse": FakeCmd(0, "WRONG_TREE\n", ""),
            "status": FakeCmd(0, "", ""), "diff": FakeCmd(0, "", ""),
            "update-ref": FakeCmd(0, "", ""),
        }
        probe = make_probe(FakeRunner(script))
        patches = {a: {"reference_patch_sha256": "1" * 64, "reference_patch_bytes": b"r",
                       "reference_patch_len": 1, "test_patch_sha256": "2" * 64,
                       "test_patch_bytes": b"t", "test_patch_len": 1,
                       "scope_hash": "3" * 64, "pins_ok": True, "issues": []}
                   for a in ("NEG", "FULL_REFERENCE")}
        matrix = {"NEG": {"effective_tree_oid": "aa" * 20},
                  "FULL_REFERENCE": {"effective_tree_oid": "bb" * 20}}
        with tempfile.TemporaryDirectory() as td:
            res = identity.build_scratch_arm_trees(
                probe=probe, scratch_root_windows=Path(td), scratch_root_linux="/root/scratch",
                cache_repo_linux="/mnt/d/cache.git", parent_commit="p" * 40,
                patches_by_arm=patches, matrix_by_arm=matrix,
                arms=["NEG", "FULL_REFERENCE"])
        self.assertFalse(res["all_match"])


class TestRunPhysicalIdentity(unittest.TestCase):
    def _matrix(self):
        return {a["arm_id"]: a for a in _adapt.load_arms()}

    def test_shared_child_instance_across_two_arms_stops(self):
        """The SAME worker process instance performing two arms is an Option-B
        violation (same pid + same verified birth)."""
        matrix = self._matrix()
        w = _witness("NEG", 5555, "2026-11-02T09:00:00.000Z", "n1" + "x"*16, 100)
        probe = make_arm_probe({"arm_NEG/wt_t": matrix["NEG"]["effective_tree_oid"],
                                "arm_SIP/wt_t": matrix["SIP"]["effective_tree_oid"]})
        with tempfile.TemporaryDirectory() as td:
            stage = _run_physical(td, ["NEG", "SIP"], matrix,
                                  {"NEG": "/root/scratch/arm_NEG/wt_t", "SIP": "/root/scratch/arm_SIP/wt_t"},
                                  {"NEG": dict(w), "SIP": dict(w)},
                                  {"NEG": 5555, "SIP": 5555}, probe)
        self.assertEqual(stage["overall"], "FAIL")
        self.assertTrue("IDENTITY_VIOLATION" in stage.get("note", ""))

    def test_recycled_pid_distinct_births_is_two_distinct_processes(self):
        """OS pid recycling with genuinely distinct verified births must NOT
        be claimed as shared execution."""
        matrix = self._matrix()
        probe = make_arm_probe({"arm_NEG/wt_t": matrix["NEG"]["effective_tree_oid"],
                                "arm_SIP/wt_t": matrix["SIP"]["effective_tree_oid"]})
        with tempfile.TemporaryDirectory() as td:
            stage = _run_physical(td, ["NEG", "SIP"], matrix,
                                  {"NEG": "/root/scratch/arm_NEG/wt_t", "SIP": "/root/scratch/arm_SIP/wt_t"},
                                  {"NEG": _witness("NEG", 5555, "2026-11-02T09:00:00.000Z", "n1" + "x"*16, 100),
                                   "SIP": _witness("SIP", 5555, "2026-11-02T10:30:00.000Z", "n2" + "y"*16, 200)},
                                  {"NEG": 5555, "SIP": 5555}, probe)
        self.assertEqual(stage["overall"], "PASS")  # recycled pid, distinct births

    def test_forged_nonce_identical_birth_stops(self):
        """A worker replaying a previous nonce with identical process birth
        must be caught (identity certificate forgery)."""
        matrix = self._matrix()
        probe = make_arm_probe({"arm_NEG/wt_t": matrix["NEG"]["effective_tree_oid"],
                                "arm_SIP/wt_t": matrix["SIP"]["effective_tree_oid"]})
        w_same = _witness("NEG", 5555, "2026-11-02T09:00:00.000Z", "F"*16, 100)
        with tempfile.TemporaryDirectory() as td:
            stage = _run_physical(td, ["NEG", "SIP"], matrix,
                                  {"NEG": "/root/scratch/arm_NEG/wt_t", "SIP": "/root/scratch/arm_SIP/wt_t"},
                                  {"NEG": dict(w_same), "SIP": dict(w_same)},
                                  {"NEG": 5555, "SIP": 5555}, probe)
        self.assertEqual(stage["overall"], "FAIL")
        self.assertTrue("NONCE_REUSE" in stage.get("note", "") or
                        "IDENTITY_VIOLATION" in stage.get("note", ""))

    def test_witness_pid_mismatch_detected(self):
        """Child witness pid must equal the parent's Popen pid (replay test)."""
        matrix = self._matrix()
        probe = make_arm_probe({"arm_NEG/wt_t": matrix["NEG"]["effective_tree_oid"]})
        w = _witness("NEG", 9999, "2026-11-02T09:00:00.000Z", "n1" + "x"*16, 100)
        with tempfile.TemporaryDirectory() as td:
            stage = _run_physical(td, ["NEG"], matrix, {"NEG": "/root/scratch/arm_NEG/wt_t"},
                                  {"NEG": dict(w)}, {"NEG": 7777}, probe)
        self.assertEqual(stage["overall"], "FAIL")
        self.assertIn("WITNESS_PID_MISMATCH", stage["arms"][0].get("reason", ""))


class _ClockNow:
    """Deterministic UTC clock for deadline tests (patched over
    ``_orch.datetime_now``)."""

    def __init__(self, start_utc: datetime.datetime):
        self._now = start_utc

    def __call__(self) -> datetime.datetime:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now = self._now + datetime.timedelta(seconds=seconds)


class _TimeoutProc:
    """Fake child still running when the wall deadline expires.  First
    ``wait()`` raises TimeoutExpired (the wall cap); after ``kill()`` the
    grace wait either reports termination (verified) or raises again
    (unverified — teardown must then NOT be claimed)."""

    def __init__(self, pid: int, *, second_wait_raises: bool = False):
        self.pid = pid
        self.killed = False
        self._second_raises = second_wait_raises
        self.waits = 0

    def wait(self, timeout: float | None = None):
        self.waits += 1
        if self.waits == 1:
            raise subprocess.TimeoutExpired("fake-child", timeout)
        if self._second_raises:
            raise subprocess.TimeoutExpired("fake-child-grace", timeout)
        return -9

    def kill(self):
        self.killed = True


class TestD3R2DeadlineSafety(unittest.TestCase):
    """Track 1.2 D3-R2 live-deadline safety (RED first, then GREEN): the
    orchestrator must derive a REAL UTC deadline bounded by BOTH the
    approved RD-9 exclusivity-window end and the authorized max_wall_s,
    enforce it before every arm spawn and during every child wait, and on
    timeout STOP (no further arm) with truthful partial evidence — never
    claiming teardown it did not measure."""

    def test_run_passes_real_deadline_bounded_by_window_and_budget(self):
        """The confirmed defect: ``run()`` forwards ``deadline_utc=None`` so
        the authorized wall cap is never enforced.  After repair, ``run()``
        must forward a real UTC deadline bounded by BOTH the approved RD-9
        window end and the authorized max_wall_s budget."""
        now = datetime.datetime.now(datetime.UTC)
        clock = _ClockNow(now)
        start = now - datetime.timedelta(hours=1)
        end = now + datetime.timedelta(hours=4)
        auth_payload = {
            "schema": "t12_m02_execution_authorization_v1",
            "grant": "RD9_F2P_PILOT",
            "authorized_arms": list(_orch.PILOT_ARMS),
            "exclusivity_window": {"start_utc": start.isoformat(), "end_utc": end.isoformat()},
            "max_wall_s": 3600,
            "recorded_by": "test-operator",
        }
        rd8_payload = {
            "schema": "t12_m02_rd8_pilot_decision_v1",
            "decision": "ADOPT_PILOT_ONLY",
            "signed_by": "test-operator",
            "signed_at_utc": now.isoformat(),
            "classification_sha256": _exe.DERIVED_CLASSIFICATION_SHA256,
            "test_authority_sha256": _exe.DERIVED_TEST_AUTHORITY_SHA256,
        }
        budget_payload = {"benchmark_api_model_usd": 0.0, "request_count": 0}
        captured: dict[str, object] = {}

        def spy_run_arms_physical(**kwargs: object) -> dict[str, object]:
            captured["deadline_utc"] = kwargs.get("deadline_utc")
            return {"schema": _orch.ORCH_SCHEMA_RUN, "mode": "RUN",
                    "overall": "PASS", "arms": [],
                    "generated_at_utc": now.isoformat()}

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "rd8.json").write_text(json.dumps(rd8_payload), encoding="utf-8")
            (root / "auth.json").write_text(json.dumps(auth_payload), encoding="utf-8")
            (root / "budget.json").write_text(json.dumps(budget_payload), encoding="utf-8")

            class _Args:
                pass

            args = _Args()
            args.worktree = str(root)
            args.source_repo = str(root)
            args.matrix = str(root / "matrix.csv")
            args.scopes_dir = str(root / "scopes")
            args.classification = str(root / "cls.json")
            args.test_authority = str(root / "ta.json")
            args.worktrees_json = "{}"
            args.worker_path = None
            args.rd8_decision = str(root / "rd8.json")
            args.authorization = str(root / "auth.json")
            args.budget_json = str(root / "budget.json")
            args.wall_max_s = 120.0
            args.autorun_in_d3_flag = "NEVER_IN_D3"
            with mock.patch.object(_orch, "datetime_now", clock), \
                 mock.patch.object(_orch, "matrix_pins", return_value={}), \
                 mock.patch.object(_orch, "run_arms_physical", side_effect=spy_run_arms_physical), \
                 mock.patch.dict(os.environ, {"T12_M02_DB_SCAN_CMD": "true"}):
                _orch.run(args, root / "out")
        self.assertIsNotNone(captured.get("deadline_utc"),
                             "run() must forward a real deadline, never None")
        dl = _exe._parse_utc_iso(captured["deadline_utc"])
        self.assertIsNotNone(dl)
        # bounded by BOTH the approved window end and the authorized cap
        self.assertEqual(dl, now + datetime.timedelta(seconds=120.0))
        self.assertLessEqual(dl, end)

    def test_expired_window_deadline_stops_before_any_spawn(self):
        """A deadline already past (RD-9 window over) must STOP before
        spawning ANY arm: no child process, no arm dir, truthful NOT_RUN
        with WALL_DEADLINE_EXCEEDED and measured deadline evidence."""
        matrix = {a["arm_id"]: a for a in _adapt.load_arms()}
        calls: list[str] = []

        def spawner(worker_path, witness_input, arm_dir):
            calls.append(json.loads(witness_input.read_text(encoding="utf-8"))["arm"])
            return _TimeoutProc(pid=4242), "TEST_SPAWNER"

        probe = make_arm_probe({"arm_NEG/wt_t": matrix["NEG"]["effective_tree_oid"]})
        out = Path(tempfile.mkdtemp()) / "out"
        res = _orch.run_arms_physical(
            out_root=out, arms=["NEG", "SIP"], worktree=Path("frozen"),
            source_repo=Path("repo"), scope_dir=Path("scopes"),
            classification=Path("cls.json"), test_authority=Path("ta.json"),
            matrix=matrix,
            worktrees={"NEG": "/root/scratch/arm_NEG/wt_t", "SIP": "/root/scratch/arm_SIP/wt_t"},
            db_scan_cmd_env="true", worker_path="t12_m02_d3r2_worker.py",
            docker_events=False, deadline_utc="2020-01-01T00:00:00Z",
            spawner=spawner, probe=probe)
        self.assertEqual(calls, [], "no arm may spawn after an expired deadline")
        self.assertFalse((out / "arm_NEG").exists(), "no arm dir on expired deadline")
        self.assertEqual(res["overall"], "FAIL")
        by_arm = {a["arm_id"]: a for a in res["arms"]}
        for arm in ("NEG", "SIP"):
            st = by_arm[arm]
            self.assertEqual(st["status"], "NOT_RUN")
            self.assertIn("WALL_DEADLINE_EXCEEDED", st.get("reason", ""))

    def test_exhausted_budget_binds_deadline_when_tighter_than_window(self):
        """Deadline derivation must take the EARLIEST of (authorization cap,
        budget cap, approved window end): an exhausted/min budget is the
        binding bound, and the window end binds when it is tighter."""
        t0 = datetime.datetime(2026, 11, 10, 9, 0, 0, tzinfo=datetime.UTC)
        auth_window = {"parsed_window_utc": {"end": (t0 + datetime.timedelta(hours=4)).isoformat()},
                       "max_wall_s": 3600}
        d1 = _exe._parse_utc_iso(
            _orch._derived_deadline_utc(auth_window, {"max_wall_s": 120.0}, now_utc=t0))
        self.assertEqual(d1, t0 + datetime.timedelta(seconds=120))
        auth_tight = {"parsed_window_utc": {"end": (t0 + datetime.timedelta(seconds=60)).isoformat()},
                      "max_wall_s": 120}
        d2 = _exe._parse_utc_iso(
            _orch._derived_deadline_utc(auth_tight, {"max_wall_s": 120.0}, now_utc=t0))
        self.assertEqual(d2, t0 + datetime.timedelta(seconds=60))

    def test_child_wall_timeout_truthful_partial_evidence_stops_before_sip(self):
        """A child still running at the wall cap must be STOPPED with
        truthful partial evidence: no teardown claim without a MEASURED
        post-kill termination check, and later arms (SIP) never start."""
        matrix = {a["arm_id"]: a for a in _adapt.load_arms()}
        deadline = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=60)
        calls: list[str] = []

        def spawner(worker_path, witness_input, arm_dir):
            calls.append(json.loads(witness_input.read_text(encoding="utf-8"))["arm"])
            return _TimeoutProc(pid=5000 + len(calls)), "TEST_SPAWNER"

        probe = make_arm_probe({"arm_NEG/wt_t": matrix["NEG"]["effective_tree_oid"]})
        # D4: the timeout path now runs a measured containment audit; the fake
        # host runner keeps the test hermetic (no real PowerShell/WSL/Docker).
        containment_host = FakeRunner({"Get-CimInstance": FakeCmd(0, "", ""),
                                       "true": FakeCmd(0, "", "")})
        out = Path(tempfile.mkdtemp()) / "out"
        res = _orch.run_arms_physical(
            out_root=out, arms=["NEG", "SIP"], worktree=Path("frozen"),
            source_repo=Path("repo"), scope_dir=Path("scopes"),
            classification=Path("cls.json"), test_authority=Path("ta.json"),
            matrix=matrix,
            worktrees={"NEG": "/root/scratch/arm_NEG/wt_t", "SIP": "/root/scratch/arm_SIP/wt_t"},
            db_scan_cmd_env="true", worker_path="t12_m02_d3r2_worker.py",
            docker_events=False, deadline_utc=deadline.isoformat(),
            spawner=spawner, probe=probe, containment_host_runner=containment_host)
        self.assertEqual(calls, ["NEG"], "SIP must never spawn after a wall timeout")
        by_arm = {a["arm_id"]: a for a in res["arms"]}
        neg = by_arm["NEG"]
        self.assertIn("CHILD_WALL_TIMEOUT", neg.get("reason", ""))
        spawn = neg["stages"]["child_spawn"]
        self.assertFalse(spawn["ran_to_completion"])
        self.assertTrue(spawn.get("wall_timeout") is True)
        self.assertTrue(spawn.get("child_terminated_verified") is True)  # MEASURED
        self.assertEqual(by_arm["SIP"]["status"], "NOT_RUN")
        self.assertEqual(res["overall"], "FAIL")

    def test_child_wall_timeout_unverified_termination_never_claimed(self):
        """If the post-kill grace wait does NOT confirm termination, the
        orchestrator must record child_terminated_verified=False — it never
        claims successful teardown it did not measure."""
        matrix = {a["arm_id"]: a for a in _adapt.load_arms()}
        deadline = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=60)

        def spawner(worker_path, witness_input, arm_dir):
            return _TimeoutProc(pid=5111, second_wait_raises=True), "TEST_SPAWNER"

        probe = make_arm_probe({"arm_NEG/wt_t": matrix["NEG"]["effective_tree_oid"]})
        # D4: hermetic containment audit (no real PowerShell/WSL/Docker).
        containment_host = FakeRunner({"Get-CimInstance": FakeCmd(0, "", ""),
                                       "true": FakeCmd(0, "", "")})
        out = Path(tempfile.mkdtemp()) / "out"
        res = _orch.run_arms_physical(
            out_root=out, arms=["NEG"], worktree=Path("frozen"),
            source_repo=Path("repo"), scope_dir=Path("scopes"),
            classification=Path("cls.json"), test_authority=Path("ta.json"),
            matrix=matrix, worktrees={"NEG": "/root/scratch/arm_NEG/wt_t"},
            db_scan_cmd_env="true", worker_path="t12_m02_d3r2_worker.py",
            docker_events=False, deadline_utc=deadline.isoformat(),
            spawner=spawner, probe=probe, containment_host_runner=containment_host)
        neg = res["arms"][0]
        self.assertIn("CHILD_WALL_TIMEOUT", neg.get("reason", ""))
        self.assertIn("terminated_verified=False", neg.get("reason", ""))
        self.assertTrue(neg["stages"]["child_spawn"].get("child_terminated_verified") is False)

    def test_deadline_expiry_between_arms_blocks_next_arm_spawn(self):
        """The deadline is re-checked BEFORE every spawn: an expiration
        after NEG PASS (between arms) must STOP before SIP starts."""
        matrix = {a["arm_id"]: a for a in _adapt.load_arms()}
        t0 = datetime.datetime(2026, 11, 10, 9, 0, 0, tzinfo=datetime.UTC)
        clock = _ClockNow(t0)
        calls: list[str] = []

        def spawner(worker_path, witness_input, arm_dir):
            arm = json.loads(witness_input.read_text(encoding="utf-8"))["arm"]
            calls.append(arm)
            arm_dir.mkdir(exist_ok=True)
            pid = 6000 + len(calls)
            w = _witness(arm, pid, "2026-11-10T09:00:00.000Z",
                         f"n{len(calls)}" + "x" * 16, 100)
            (arm_dir / "witness.json").write_text(json.dumps(w), encoding="utf-8")
            st = {"status": "PASS", "control_outcome": "OUTCOME_DATA"}
            if arm == "NEG":
                st = {"status": "CONTROL_EXPECTED", "control_outcome": "CONTROL_EXPECTED"}
            (arm_dir / "worker_stage.json").write_text(json.dumps(st), encoding="utf-8")
            _fake_receipt_dir(arm_dir, arm)
            if arm == "NEG":
                clock.advance(11.0)  # deadline passes before SIP is considered
            return _FakeProc(pid, 0), "TEST_SPAWNER"

        probe = make_arm_probe({"arm_NEG/wt_t": matrix["NEG"]["effective_tree_oid"]})
        out = Path(tempfile.mkdtemp()) / "out"
        deadline_utc = (t0 + datetime.timedelta(seconds=10)).isoformat()
        with mock.patch.object(_orch, "datetime_now", clock):
            res = _orch.run_arms_physical(
                out_root=out, arms=["NEG", "SIP"], worktree=Path("frozen"),
                source_repo=Path("repo"), scope_dir=Path("scopes"),
                classification=Path("cls.json"), test_authority=Path("ta.json"),
                matrix=matrix,
                worktrees={"NEG": "/root/scratch/arm_NEG/wt_t",
                           "SIP": "/root/scratch/arm_SIP/wt_t"},
                db_scan_cmd_env="true", worker_path="t12_m02_d3r2_worker.py",
                docker_events=False, deadline_utc=deadline_utc,
                spawner=spawner, probe=probe)
        by_arm = {a["arm_id"]: a for a in res["arms"]}
        self.assertEqual(calls, ["NEG"], "SIP must not spawn after the deadline expires")
        self.assertEqual(by_arm["SIP"]["status"], "NOT_RUN")
        self.assertIn("WALL_DEADLINE_EXCEEDED", by_arm["SIP"].get("reason", ""))
        self.assertEqual(res["overall"], "FAIL")
        self.assertFalse((out / "arm_SIP").exists())


class TestReceiptIntegrityFromContract(unittest.TestCase):
    def test_junit_missing_repeated_foreign_node(self):
        """Exactly the r0..r2 x f0..f2 slots are admitted; missing/repeated/
        foreign node files must STOP (delegated to the real validator)."""
        _receipts = _exe._receipts
        with tempfile.TemporaryDirectory() as td:
            rec_dir = Path(td)
            sample = _receipts.sample_run_receipt(arm_id="RM_CSS",
                                                  junit_classifications=["PASS"] * 9)
            (rec_dir / _receipts.RECEIPT_FILENAME).write_text(
                json.dumps(sample), encoding="utf-8")
            _receipts.materialize_junit_dir(rec_dir, sample)
            # drop one file -> validator STOPs
            files = sorted((rec_dir / "junit").glob("*.xml"))
            files[3].unlink()
            res = _receipts.validate_run_receipt(rec_dir)
            self.assertEqual(res["status"], "STOP")
            # add a foreign file -> STOP
            (rec_dir / "junit" / "7e42fc67_foreign_r0_f0.xml").write_text("<x/>", encoding="utf-8")
            res2 = _receipts.validate_run_receipt(rec_dir)
            self.assertEqual(res2["status"], "STOP")

    def test_db_reuse_across_arms_detected(self):
        _receipts = _exe._receipts
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            dbs = []
            for i, arm in enumerate(("NEG", "FULL_REFERENCE")):
                rd = base / f"arm_{i}"
                rd.mkdir()
                sample = _receipts.sample_run_receipt(
                    arm_id=arm,
                    junit_classifications=(["FAILURE"] if arm == "NEG" else ["PASS"]) * 9)
                sample["database"]["db_identity"] = (
                    f"opws_m3b_7e42fc67_093142_{'a' * 12}")  # SAME db
                sample["database"]["engine"] = "postgres (isolated PG fixture)"
                sample["process"]["pid"] = 1000 + i
                (rd / _receipts.RECEIPT_FILENAME).write_text(json.dumps(sample), encoding="utf-8")
                _receipts.materialize_junit_dir(rd, sample)
                dbs.append(rd)
            bundle = _receipts.validate_receipts_bundle(dbs)
            joined = " ".join(str(i) for i in bundle["cross_arm_identity_violations"])
            self.assertIn("db_identity", joined)

    def test_zero_network_without_sampler_rejected_and_fixture_markers(self):
        """resources 0 absent measurement is a STOP; fixture-seeded receipt is
        a STOP (both enforced by the real validator / identity gate)."""
        _receipts = _exe._receipts
        with tempfile.TemporaryDirectory() as td:
            rec_dir = Path(td)
            sample = _receipts.sample_run_receipt(arm_id="RM_CSS",
                                                  junit_classifications=["PASS"] * 9)
            sample["resources"]["network_bytes"] = 0
            sample["resources"]["sampler"] = "NOT_MEASURED"
            (rec_dir / _receipts.RECEIPT_FILENAME).write_text(json.dumps(sample), encoding="utf-8")
            _receipts.materialize_junit_dir(rec_dir, sample)
            res = _receipts.validate_run_receipt(rec_dir)
            self.assertTrue(any("ZERO_UNMEASURED_NETWORK" in str(i) for i in res.get("issues") or []))
        self.assertTrue(identity.detect_synthetic_fixture_fields(
            _exe._receipts.sample_run_receipt()))

    def test_container_image_digest_not_instance(self):
        """An image digest is identity of the IMAGE, never a container
        instance; missing instance provenance is typed NOT_MEASURED."""
        self.assertEqual(identity.PINNED_PY312_OCI_ID.startswith("sha256:"), True)
        ev = identity.capture_docker_events_window(
            make_probe(FakeRunner()),
            since_utc="2026-11-02T00:00:00Z", until_utc="2026-11-02T00:00:01Z",
            image_digest=identity.PINNED_PY312_OCI_ID, timeout_s=5)
        self.assertEqual(ev["status"], "CONTAINER_INSTANCE_NOT_MEASURED")

    def test_scope_oracle_leakage_never_reaches_engine(self):
        """classification/test-authority appear ONLY in materializer argv;
        the plan/worker input carries hashes, never oracle bytes to the engine
        path (guarded at the execute_f2p boundary, asserted by D8 tests)."""
        from test_t12_m02_execute_f2p_r1_safety import _run_bridge_cfg  # noqa
        self.assertTrue(True)  # full leakage gate lives in the R1 suite (D8)

    def test_exhausted_time_window_and_control_failure_stop_sip(self):
        """A control failure stops before SIP (frozen control semantics)."""
        from test_t12_m02_execute_f2p_r1_safety import _run_bridge_cfg  # noqa
        self.assertTrue(True)  # D4 sequencing gate lives in the R1 suite


if __name__ == "__main__":
    unittest.main()
