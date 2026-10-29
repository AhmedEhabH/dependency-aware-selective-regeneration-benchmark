"""T12 M02-D3-R2 — D4 RED/GREEN: docker event-window coverage (worker) and
post-timeout descendant containment (orchestrator).

Track 1.2 D4 minimal evidence-safety gate, engineering-only (no model calls,
no live Docker/WSL/engine).  Test doubles only.

Defect A (verified in review): in ``t12_m02_d3r2_worker`` the ``docker events
--until`` bound was projected with ``_identity.utc_seconds()`` BEFORE
``harness.run_state_v3()`` ran, so the arm's actual engine create/start events
could fall entirely outside the stream; the capture was also never awaited on
exception paths and never validated instance id / window.

Defect B (verified in review): in ``t12_m02_d3r2_orchestrator`` a child wall
timeout called ``proc.kill()`` and verified only the direct Windows Python
worker — descendant WSL/Docker/DB activity was never MEASURED.

RED phase: these tests fail on commit 7c53fc05:
  * the projected ``until`` does not cover the engine end (A);
  * outside-window and digest-only events are wrongly MEASURED (A);
  * the capture is not closed/awaited on the exception path (A);
  * no containment audit exists (B) and unverified resources are not reported.

Test doubles only; no WSL/Docker/engine invocation.
"""
from __future__ import annotations

import datetime
import importlib.util
import json
import os
import shlex
import subprocess
import sys
import tempfile
import time
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
_worker = _load_module("t12_m02_d3r2_worker.py", "t12_m02_d3r2_worker")

DIGEST = identity.PINNED_PY312_OCI_ID
IMG12 = DIGEST.split(":")[-1][:12]
PG_FIXTURE = identity.PG_FIXTURE


def _parse_iso(value: str) -> datetime.datetime:
    dt = _exe._parse_utc_iso(value)
    assert dt is not None, f"unparseable iso {value!r}"
    return dt


def _event(action: str, cid: str, at_unix: float, *, image_digest: str = DIGEST) -> dict:
    """A docker-events container line for pinterest-compatible JSON parse."""
    return {
        "status": action,
        "id": cid,
        "from": image_digest,
        "Type": "container",
        "Action": action,
        "Actor": {
            "ID": cid,
            "Attributes": {
                "name": "isolated-helper",
                "image": image_digest,
            },
        },
        "time": int(at_unix),
        "timeNano": int(at_unix * 1_000_000_000),
    }


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
    p = identity.PlatformProbe(runner)
    p.host_python_kind = lambda: "windows"
    p.windows_executor = lambda: True
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


def _gate_script(tree_oid="b555542a98f62636173c6c82db80d380c083f180"):
    return {
        "rev-parse": FakeCmd(0, tree_oid + "\n", ""),
        "status": FakeCmd(0, "", ""),
        "diff": FakeCmd(0, "", ""),
    }


# ---------------------------------------------------------------------------
# Worker-side doubles (defect A)
# ---------------------------------------------------------------------------
class FakeEventProc:
    """Fake ``docker events`` stream process.  ``natural=True`` exits at once
    (as a real daemon stream whose ``--until`` was reached); otherwise it only
    ends after terminate/kill (used for cleanup-path tests)."""

    def __init__(self, natural: bool = True):
        self.pid = 424242
        self._done = natural
        self.waited = False
        self.terminate_calls = 0
        self.kill_calls = 0

    def poll(self):
        return 0 if self._done else None

    def terminate(self):
        self.terminate_calls += 1
        self._done = True

    def kill(self):
        self.kill_calls += 1
        self._done = True

    def wait(self, timeout=None):
        self.waited = True
        return 0


class StubbornEventProc(FakeEventProc):
    """Never exits, even after terminate/kill (worst case capture leak)."""

    def __init__(self):
        super().__init__(natural=False)
        self.terminate_calls = 0
        self.kill_calls = 0

    def terminate(self):
        self.terminate_calls += 1

    def kill(self):
        self.kill_calls += 1


class _FakeCompleted:
    def __init__(self, rc=0, out="", err=""):
        self.returncode = rc
        self.stdout = out
        self.stderr = err


class FakeHarness:
    """Offline stand-in for the frozen harness; writes the 9 native junits."""

    def __init__(self, *, raises: bool = False, sleep_s: float = 1.5,
                 arm: str = "RM_CSS"):
        self.raises = raises
        self.sleep_s = sleep_s
        self.arm = arm
        self.junit_bodies = [_worker._receipts.JUNIT_PASS for _ in range(9)]

    def target_manifests(self, target):
        return {}

    def lock_install_script(self, wt_linux, manifests):
        return ("echo NO_LOCKED_DEV_GROUP", "install", {"ok": True})

    def run_state_v3(self, **kw):
        if self.raises:
            raise RuntimeError("ENGINE_BOOM")
        if self.sleep_s:
            time.sleep(self.sleep_s)
        raw = Path(kw["raw_junit_dir"])
        raw.mkdir(parents=True, exist_ok=True)
        names: list[str] = []
        idx = 0
        for rep in range(_exe.PILOT_REPS):
            for node in range(_exe.PILOT_NODE_COUNT):
                fname = f"{_exe.TID}_{self.arm}_r{rep}_f{node}.xml"
                (raw / fname).write_text(self.junit_bodies[idx % len(self.junit_bodies)],
                                         encoding="utf-8")
                names.append(fname)
                idx += 1
        return {
            "db_name": "opws_m3b_7e42fc67_093142_" + "a" * 12,
            "db_cleanup": "DROPPED_AFTER_JUNIT_PARSE",
            "junit_files": names,
            "error": None,
        }


class _FakeIsolatedRuntime:
    def __init__(self, **kw):
        pass

    def validate(self):
        return None


def _rm_css_row() -> dict:
    return next(a for a in _adapt.load_arms() if a["arm_id"] == "RM_CSS")


def _run_worker(td: Path, *, docker_events: bool, events: list[dict] | None = None,
                until_utc: str | None = None, engine_raises: bool = False,
                natural: bool = True):
    """Run the REAL ``worker.run_arm`` offline with injected fakes.  Returns
    ``(stage, spy)`` where ``spy`` records the projected capture window and the
    fake Popen handle (so tests can assert close/reap happened)."""
    out = Path(td) / "out"
    out.mkdir(parents=True, exist_ok=True)
    row = _rm_css_row()
    now = datetime.datetime.now(datetime.UTC)
    cfg = {
        "schema": _worker.WORKER_SCHEMA,
        "arm": "RM_CSS",
        "arm_dir": str(out / "arm_RM_CSS"),
        "nonce": "n" * 32,
        "worktree": str(Path(td)),
        "source_repo": str(Path(td)),
        "scopes_dir": str(Path(td)),
        "classification": str(Path(td) / "cls.json"),
        "test_authority": str(Path(td) / "ta.json"),
        "worktree_linux": "/root/scratch/arm_RM_CSS/wt_t",
        "effective_tree_oid": row["effective_tree_oid"],
        "scope_hash": "S" * 64,
        "patch_sha256": "P" * 64,
        "patch_bytes": 12,
        "materializer_rel": "scripts/opws_phase3b_patch_materialize.py",
        "execution_id": "M02E-RUN-D4TEST",
        "scratch_linux_base": "/results",
        "docker_events": docker_events,
        "events_until_utc": until_utc or (now + datetime.timedelta(seconds=600)).isoformat(),
    }
    witness = Path(td) / "witness.json"
    witness.write_text(json.dumps(cfg), encoding="utf-8")

    spy: dict[str, object] = {}
    real_start = _worker._start_events_capture

    def fake_load_frozen(worktree: Path, rel: str, name: str):
        if rel == _exe.HARNESS_REL:
            return FakeHarness(raises=engine_raises)
        return type("_IsolatedMod", (), {"OpwsIsolatedRuntime": _FakeIsolatedRuntime})()

    def spy_start(cap_file: Path, *, since: str, until: str):
        proc, cf = real_start(cap_file, since=since, until=until)
        spy["since"] = since
        spy["until"] = until
        spy["proc"] = proc
        if events is not None:
            with open(cf, "a", encoding="utf-8") as fh:
                for ev in events:
                    fh.write(json.dumps(ev) + "\n")
        return proc, cf

    def fake_subprocess_run(argv, **kw):
        if "--out-dir" in argv:
            odir = Path(argv[argv.index("--out-dir") + 1])
            odir.mkdir(parents=True, exist_ok=True)
            (odir / "record.json").write_text(
                json.dumps({"scope_hash": cfg["scope_hash"],
                            "reference_patch_sha256": cfg["patch_sha256"]}),
                encoding="utf-8")
        return _FakeCompleted()

    def fake_popen(argv, **kw):
        spy["popen_argv"] = list(argv)
        return FakeEventProc(natural=natural)

    with mock.patch.object(_worker, "_load_frozen", side_effect=fake_load_frozen), \
         mock.patch.object(_worker.subprocess, "run", side_effect=fake_subprocess_run), \
         mock.patch.object(_worker.subprocess, "Popen", side_effect=fake_popen), \
         mock.patch.object(_worker, "_start_events_capture", side_effect=spy_start), \
         mock.patch.object(_worker._identity, "linux_worktree_gate",
                           return_value={"pass": True, "reasons": []}), \
         mock.patch.object(
             _worker._identity, "windows_os_process_start",
             return_value={"status": "NOT_MEASURED"}):
        stage = _worker.run_arm(witness, out, db_scan_cmd_env="SCAN_CMD")
    return stage, spy


# ---------------------------------------------------------------------------
# Defect A — docker event window coverage and bounded capture
# ---------------------------------------------------------------------------
class TestEventsWindowCoverage(unittest.TestCase):
    """RED on 7c53fc05: the projected ``--until`` was computed BEFORE the
    engine call, so the stream never contained the arm's create/start events."""

    def test_events_capture_window_covers_the_actual_engine_interval(self):
        with tempfile.TemporaryDirectory() as td:
            stage, spy = _run_worker(
                Path(td), docker_events=True,
                events=[_event("create", "c" * 64, time.time()),
                        _event("start", "c" * 64, time.time())])
        run = stage["stages"]["run_state_v3"]
        self.assertEqual(stage["status"], "PASS")
        # D4 invariant: since <= run_start AND until >= run_end.
        self.assertLessEqual(_parse_iso(str(spy["since"])), _parse_iso(run["start_utc"]))
        self.assertGreaterEqual(_parse_iso(str(spy["until"])), _parse_iso(run["end_utc"]))
        self.assertLessEqual(_parse_iso(str(spy["since"])), _parse_iso(str(spy["until"])))
        # the capture was closed and reaped.
        self.assertTrue(spy["proc"].waited)  # type: ignore[attr-defined]
        cap = stage["stages"]["container_events"]
        self.assertEqual(cap["status"], "MEASURED")
        self.assertTrue(cap["capture_exited"])
        self.assertEqual(cap["instances"][0]["container_id"], "c" * 64)

    def test_empty_event_stream_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            stage, spy = _run_worker(Path(td), docker_events=True, events=[])
        self.assertEqual(stage["status"], "PASS")
        cap = stage["stages"]["container_events"]
        self.assertEqual(cap["status"], "CONTAINER_INSTANCE_NOT_MEASURED")
        self.assertTrue(spy["proc"].waited)  # still closed/awaited

    def test_unrelated_and_out_of_window_events_never_measured(self):
        """A pinned-image event OUTSIDE the arm window (or any event from an
        unrelated image) is NOT this arm's instance evidence.  RED on the old
        code: the old matcher returned MEASURED whenever the digest appeared,
        regardless of when/whether the instance was real."""
        now = time.time()
        outside = _event("create", "d" * 64, now - 3600)  # one hour BEFORE the run
        unrelated = _event("create", "e" * 64, now, image_digest="sha256:" + "f" * 64)
        with tempfile.TemporaryDirectory() as td:
            stage, _ = _run_worker(Path(td), docker_events=True,
                                   events=[outside, unrelated])
        cap = stage["stages"]["container_events"]
        self.assertEqual(cap["status"], "CONTAINER_INSTANCE_NOT_MEASURED")
        self.assertEqual(cap["events_seen"], 2)
        self.assertTrue(any("EVENT_OUTSIDE_ARM_WINDOW" in str(a) for a in cap.get("anomalies", []))
                        or "outside" in str(cap.get("reason", "")))

    def test_image_digest_never_accepted_as_instance_id(self):
        """An event whose only identity link is the pinned digest (empty id or
        id == digest) must fail closed — the digest is never an instance."""
        now = time.time()
        digest_as_id = _event("create", DIGEST, now)
        no_id = {"status": "create", "Type": "container", "Action": "create",
                 "Actor": {"ID": "", "Attributes": {"image": DIGEST}},
                 "time": int(now)}
        with tempfile.TemporaryDirectory() as td:
            stage, _ = _run_worker(Path(td), docker_events=True,
                                   events=[digest_as_id, no_id])
        cap = stage["stages"]["container_events"]
        self.assertEqual(cap["status"], "CONTAINER_INSTANCE_NOT_MEASURED")
        joined = " ".join(str(a) for a in cap.get("anomalies", []))
        self.assertTrue("EVENT_WITHOUT_INSTANCE_ID" in joined)

    def test_capture_closed_and_awaited_when_engine_raises(self):
        """RED on the old code: an engine exception leaked the capture process
        (never terminated/awaited).  After repair the stream is closed and
        reaped on the exception path too, and the failure stays FAIL."""
        with tempfile.TemporaryDirectory() as td:
            stage, spy = _run_worker(Path(td), docker_events=True,
                                     events=[_event("create", "c" * 64, time.time())],
                                     engine_raises=True)
        self.assertEqual(stage["status"], "FAIL")
        self.assertIn("ENGINE_BOOM", stage.get("reason", ""))
        self.assertTrue(spy["proc"].waited)  # closed/awaited even on failure
        cap = stage["stages"]["container_events"]
        self.assertEqual(cap["status"], "CONTAINER_INSTANCE_NOT_MEASURED")

    def test_capture_never_exiting_is_terminated_then_killed_then_reaped(self):
        """Bounded termination: natural-exit wait -> terminate -> kill -> reap.
        A stubborn stream must be torn down and reaped, never left running."""
        import tempfile as _t
        with _t.TemporaryDirectory() as td:
            cap_file = Path(td) / "events.jsonl"
            proc = StubbornEventProc()
            res = _worker._finish_events_capture(
                proc, cap_file, DIGEST, run_start="2026-11-02T09:00:00Z",
                run_end="2026-11-02T09:00:01Z", since_proj="2026-11-02T08:59:55Z",
                until_proj="2026-11-02T10:00:00Z", timeout_s=0.01, reap_grace_s=0.01)
        self.assertEqual(res["status"], "CONTAINER_INSTANCE_NOT_MEASURED")
        self.assertFalse(res["capture_exited"])
        self.assertGreaterEqual(proc.terminate_calls, 1)
        self.assertGreaterEqual(proc.kill_calls, 1)

    def test_capture_window_must_be_bounded_fail_closed(self):
        """An unconfigurable/absent/past wall bound is a fail-closed error —
        the stream is never left with an open-ended upper bound."""
        with self.assertRaisesRegex(RuntimeError, "EVENT_WINDOW_UNBOUNDED"):
            _worker._events_until_projection({})
        with self.assertRaisesRegex(RuntimeError, "EVENT_WINDOW_UNBOUNDED"):
            _worker._events_until_projection({"events_until_utc": "2020-01-01T00:00:00Z"})
        with self.assertRaisesRegex(RuntimeError, "EVENT_SINCE_INVALID"):
            _worker._events_since_projection("not-a-timestamp")
        ok = _worker._events_since_projection("2026-11-02T09:00:00Z")
        self.assertLessEqual(_parse_iso(ok), _parse_iso("2026-11-02T09:00:00Z"))


# ---------------------------------------------------------------------------
# Orchestrator-side doubles (defect B)
# ---------------------------------------------------------------------------
class _TimeoutProc:
    """Fake child still running when the wall deadline expires: first wait()
    raises TimeoutExpired; after kill() the grace wait either verifies or
    raises again."""

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


def _run_timeout_case(
    td: Path,
    *,
    arms: list[str],
    probe_script: dict,
    host_script: dict,
    docker_events: bool = True,
    second_wait_raises: bool = False,
    db_scan_cmd_env: str = "SCAN_CMD",
):
    matrix = {a["arm_id"]: a for a in _adapt.load_arms()}
    deadline = (datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=60)).isoformat()
    calls: list[str] = []

    def spawner(worker_path, witness_input, arm_dir):
        calls.append(json.loads(witness_input.read_text(encoding="utf-8"))["arm"])
        return _TimeoutProc(10000 + len(calls), second_wait_raises=second_wait_raises), "TEST_SPAWNER"

    out = Path(td) / "out"
    out.mkdir(parents=True, exist_ok=True)
    res = _orch.run_arms_physical(
        out_root=out, arms=arms, worktree=Path("frozen"), source_repo=Path("repo"),
        scope_dir=Path("scopes"), classification=Path("cls.json"),
        test_authority=Path("ta.json"), matrix=matrix,
        worktrees={a: f"/root/scratch/arm_{a}/wt_t" for a in arms},
        db_scan_cmd_env=db_scan_cmd_env, worker_path="t12_m02_d3r2_worker.py",
        docker_events=docker_events, deadline_utc=deadline,
        spawner=spawner, probe=make_probe(FakeRunner(probe_script)),
        containment_host_runner=FakeRunner(host_script))
    return res, calls


class TestTimeoutContainmentAudit(unittest.TestCase):
    """Defect B RED: ``proc.kill()`` only proves the direct Windows worker
    exited; the parent must MEASURE descendant WSL/Docker/DB containment and
    keep STOP (reportunverified) otherwise."""

    def test_timeout_runs_measured_containment_audit_and_keeps_stop_before_sip(self):
        probe_script = dict(_gate_script(_rm_css_row()["effective_tree_oid"]))
        probe_script["{{.ID}}|{{.Names}}|{{.Image}}"] = FakeCmd(0, "", "")
        host_script = {
            "Get-CimInstance": FakeCmd(0, "", ""),
            "SCAN_CMD": FakeCmd(0, "", ""),
        }
        with tempfile.TemporaryDirectory() as td:
            res, calls = _run_timeout_case(
                Path(td), arms=["RM_CSS", "SIP"],
                probe_script=probe_script, host_script=host_script)
        self.assertEqual(calls, ["RM_CSS"], "SIP must never spawn after a wall timeout")
        by_arm = {a["arm_id"]: a for a in res["arms"]}
        neg = by_arm["RM_CSS"]
        self.assertIn("CHILD_WALL_TIMEOUT", neg.get("reason", ""))
        self.assertIn("containment=CONTAINMENT_VERIFIED", neg.get("reason", ""))
        audit = neg["stages"]["containment"]
        self.assertEqual(audit["status"], "CONTAINMENT_VERIFIED")
        self.assertFalse(audit["resident_resources"]["processes"])
        self.assertFalse(audit["resident_resources"]["containers"])
        self.assertFalse(audit["resident_resources"]["opws_databases"])
        self.assertTrue(neg["stages"]["child_spawn"]["child_terminated_verified"])
        self.assertEqual(by_arm["SIP"]["status"], "NOT_RUN")
        self.assertEqual(res["overall"], "FAIL")

    def test_timeout_surviving_descendant_processes_reported_not_claimed(self):
        probe_script = dict(_gate_script(_rm_css_row()["effective_tree_oid"]))
        probe_script["{{.ID}}|{{.Names}}|{{.Image}}"] = FakeCmd(0, "", "")
        host_script = {
            "Get-CimInstance": FakeCmd(0, "12345|12346", ""),
            "SCAN_CMD": FakeCmd(0, "", ""),
        }
        with tempfile.TemporaryDirectory() as td:
            res, _ = _run_timeout_case(
                Path(td), arms=["RM_CSS"],
                probe_script=probe_script, host_script=host_script)
        arm = res["arms"][0]
        audit = arm["stages"]["containment"]
        self.assertEqual(audit["status"], "CONTAINMENT_UNVERIFIED")
        self.assertEqual(audit["resident_resources"]["processes"], ["12345", "12346"])
        self.assertIn("CONTAINMENT_UNVERIFIED", arm.get("reason", ""))
        self.assertEqual(res["overall"], "FAIL")

    def test_timeout_new_docker_containers_reported_but_fixture_excluded(self):
        """Containers beyond the pre-spawn baseline are surviving resources
        and must be REPORTED as unverified; the long-lived PG fixture is never
        deleted and never counted as leftover.  The baseline snapshot is the
        PRE-spawn docker ps (empty); only the post-timeout snapshot shows the
        new engine container alongside the pre-existing fixture."""
        fixture_line = "ff1a11b22c33|wp2-opws-pg-smoke|sha256:f7d23353e1b15"
        engine_line = "aa22bb33cc44|opws-py312-engine-4|sha256:a6e743589b60"
        probe_script = dict(_gate_script(_rm_css_row()["effective_tree_oid"]))

        def docker_ps(argv):
            # first call = pre-spawn baseline (empty); second = post-timeout
            docker_ps.n += 1
            if docker_ps.n == 1:
                return FakeCmd(0, "", "")
            return FakeCmd(0, engine_line + "\n" + fixture_line + "\n", "")

        docker_ps.n = 0
        probe_script["{{.ID}}|{{.Names}}|{{.Image}}"] = docker_ps
        host_script = {
            "Get-CimInstance": FakeCmd(0, "", ""),
            "SCAN_CMD": FakeCmd(0, "", ""),
        }
        with tempfile.TemporaryDirectory() as td:
            res, _ = _run_timeout_case(
                Path(td), arms=["RM_CSS"],
                probe_script=probe_script, host_script=host_script)
        arm = res["arms"][0]
        audit = arm["stages"]["containment"]
        self.assertEqual(audit["status"], "CONTAINMENT_UNVERIFIED")
        containers = audit["resident_resources"]["containers"]
        self.assertTrue(any(engine_line in c for c in containers),
                        f"engine container must be reported, got {containers}")
        self.assertFalse(any(PG_FIXTURE in c for c in containers),
                         "long-lived PG fixture must never be reported as leftover")
        self.assertEqual(audit["probes"]["docker"]["status"], "MEASURED")
        self.assertTrue(audit["probes"]["docker"]["attribution_ok"])

    def test_timeout_docker_probe_unavailable_fails_closed(self):
        probe_script = dict(_gate_script(_rm_css_row()["effective_tree_oid"]))
        probe_script["{{.ID}}|{{.Names}}|{{.Image}}"] = FakeCmd(1, "", "docker dead")
        host_script = {
            "Get-CimInstance": FakeCmd(0, "", ""),
            "SCAN_CMD": FakeCmd(0, "", ""),
        }
        with tempfile.TemporaryDirectory() as td:
            res, _ = _run_timeout_case(
                Path(td), arms=["RM_CSS"],
                probe_script=probe_script, host_script=host_script)
        arm = res["arms"][0]
        audit = arm["stages"]["containment"]
        self.assertEqual(audit["status"], "CONTAINMENT_UNVERIFIED")
        self.assertEqual(audit["probes"]["docker"]["status"], "NOT_MEASURED")
        self.assertIn("docker dead", audit["probes"]["docker"]["reason"])

    def test_timeout_db_leftovers_reported(self):
        leftover_db = "opws_m3b_7e42fc67_093142_1234567890ab"
        probe_script = dict(_gate_script(_rm_css_row()["effective_tree_oid"]))
        probe_script["{{.ID}}|{{.Names}}|{{.Image}}"] = FakeCmd(0, "", "")
        host_script = {
            "Get-CimInstance": FakeCmd(0, "", ""),
            "SCAN_CMD": FakeCmd(0, leftover_db + "\n", ""),
        }
        with tempfile.TemporaryDirectory() as td:
            res, _ = _run_timeout_case(
                Path(td), arms=["RM_CSS"],
                probe_script=probe_script, host_script=host_script)
        arm = res["arms"][0]
        audit = arm["stages"]["containment"]
        self.assertEqual(audit["status"], "CONTAINMENT_UNVERIFIED")
        self.assertEqual(audit["resident_resources"]["opws_databases"], [leftover_db])

    def test_unverified_child_termination_still_fails_closed(self):
        """If the direct child does not even exit after kill, containment cannot
        be claimed even when probes look clean."""
        probe_script = dict(_gate_script(_rm_css_row()["effective_tree_oid"]))
        probe_script["{{.ID}}|{{.Names}}|{{.Image}}"] = FakeCmd(0, "", "")
        host_script = {
            "Get-CimInstance": FakeCmd(0, "", ""),
            "SCAN_CMD": FakeCmd(0, "", ""),
        }
        with tempfile.TemporaryDirectory() as td:
            res, _ = _run_timeout_case(
                Path(td), arms=["RM_CSS"], probe_script=probe_script,
                host_script=host_script, second_wait_raises=True)
        arm = res["arms"][0]
        self.assertIn("terminated_verified=False", arm.get("reason", ""))
        audit = arm["stages"]["containment"]
        self.assertEqual(audit["status"], "CONTAINMENT_UNVERIFIED")
        self.assertFalse(audit["direct_child_exited"])

    def test_containment_audit_fails_closed_when_nothing_measured(self):
        """No baseline, no scan command, unscripted probes -> every probe
        NOT_MEASURED -> CONTAINMENT_UNVERIFIED (never assumed success)."""
        aud = _orch.containment_audit(
            child_pid=4242, direct_child_exited=True,
            probe=make_probe(FakeRunner()), baseline_containers=None,
            db_scan_cmd_env=None, spawned_utc="2026-11-02T00:00:00Z",
            host_runner=FakeRunner(), per_probe_timeout_s=1)
        self.assertEqual(aud["status"], "CONTAINMENT_UNVERIFIED")
        self.assertEqual(aud["probes"]["db_scan"]["status"], "NOT_MEASURED")
        self.assertEqual(aud["probes"]["docker"]["status"], "NOT_MEASURED")
        self.assertEqual(aud["resident_resources"]["opws_databases"], [])

    def test_db_scan_cmd_split_uses_posix_false_on_windows(self):
        """The operator-supplied scanner must be split with Windows semantics
        (posix=False) on Windows Python, mirroring the worker: POSIX mode is
        only used on POSIX hosts, so on Windows a quoted path keeps its quotes
        literally (shlex posix=False semantics) — deterministic and distinct
        from posix=True, which strips them."""
        cmd = 'scan.ps1 -Root "C:\\Program Files\\scans" -Tag opws'
        if os.name == "nt":
            tokens = _orch._split_db_scan_cmd(cmd)
            self.assertEqual(tokens, ["scan.ps1", "-Root", '"C:\\Program Files\\scans"', "-Tag", "opws"])
            # posix=True would strip the quotes — proves posix=False is active
            posix_tokens = shlex.split(cmd, posix=True)
            self.assertEqual(posix_tokens[2], "C:\\Program Files\\scans")
            self.assertNotEqual(posix_tokens, tokens)
        else:
            # On a POSIX host the split is POSIX mode, not Windows mode.
            self.assertEqual(_orch._split_db_scan_cmd(cmd),
                             ["scan.ps1", "-Root", "C:\\Program Files\\scans", "-Tag", "opws"])


if __name__ == "__main__":
    unittest.main()
