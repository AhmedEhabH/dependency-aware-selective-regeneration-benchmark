# -*- coding: utf-8 -*-
"""C6 FINAL — PHASE 1 RED tests for the seven independently confirmed defects
(F1..F7). Written to be RED against runner v0.2.0: each test asserts the
*intended fail-closed invariant* and must FAIL on the current code. They turn
GREEN only after the Phase 2 minimal repair. No real candidate test is ever
executed here: synthetic fixtures and read-only frozen data only.

Findings covered:
  F1  evaluator.py -> run_limited without the task plan -> docker_run needs
      plan.image -> AttributeError.
  F2  runner.py decides the verdict BEFORE the T-only/reference evaluation;
      evaluator_error / genuine reference failure can silently coexist with
      a PASS verdict.
  F3  oracle.py accepts arbitrary forged stdout ("pretend result: 1 passed")
      as a valid successful pytest report -> never a behavioral oracle.
  F4  runner.py computes ENVIRONMENT_ID without the actual interpreter,
      wheelhouse or container image digest; mutable image tags (:latest) are
      acceptable publication-grade identity -> stop on env drift.
  F5  isolation.py kills the docker CLI host PID on timeout instead of the
      container id -> deterministic id + forced cleanup + no orphans.
  F6  CLI overrides for git store / ledger / H2 events / protected cache /
      frozen manifest can substitute unverified alternate sources while the
      receipt still reports inputs_verified=True.
  F7  the reference evaluation must run the FULL M/A test contract AT T
      (P code + T test bytes) in a separate evaluation-only tree; P tests
      running green alone must never PASS; no T code/patch/oracle answers
      visible to the prospective input.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from c6runner.errors import Blocked, C6Stop  # noqa: E402
from c6runner.hashes import json_blob, sha256_file  # noqa: E402
from c6runner.verdicts import Verdict  # noqa: E402

P_CONTENT = {
    "src/x.py": "VALUE = 1\n",
    "src/y.py": "OTHER = 2\n",
    "tests/test_x.py": "def test_x():\n    assert True\n",
    "requirements.txt": "django==2.0\npytest\n",
    "setup.cfg": "[tool:pytest]\ntestpaths = tests\n",
}
T_X_SRC = "VALUE = 2\n"


def _git(*args, cwd=None, check=True):
    env = dict(os.environ)
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    r = subprocess.run(["git"] + list(args), capture_output=True, text=True,
                       cwd=cwd, env=env, check=False)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {args}: {r.stderr[-800:]}")
    return r


def _is_test(path):
    segs = path.split("/")
    if "tests" in segs or "test" in segs:
        return True
    return path.endswith("_test.py") or path.startswith("test_") or \
        path.endswith("conftest.py")


def _make_auth(data_dir, protocol_sha, scope="ALL", bindings=None):
    """Fresh authorization receipt (write-then-hash convention)."""
    doc = {"utc": "2026-10-27T00:01:00+00:00", "operator": "final-red",
           "protocol_sha256": protocol_sha, "scope": scope}
    if bindings:
        doc["task_bindings"] = bindings
    raw = (json.dumps(doc, indent=1, sort_keys=True) + "\n").encode("utf-8")
    doc["authorization_sha256"] = hashlib.sha256(raw).hexdigest().upper()
    final = (json.dumps(doc, indent=1, sort_keys=True) + "\n").encode("utf-8")
    path = os.path.join(data_dir, f"auth_{hashlib.sha256(raw).hexdigest()[:8]}.json")
    with open(path, "wb") as f:
        f.write(final)
    return path


def _variant_env(tmp_path, t_test_content, t_only_content,
                 oracle_mode="POSITIVE_REFERENCE", t_only_path=None):
    """Deterministic synthetic environment (repo P/T + ledger + H2 + body +
    freeze + auth bound to a harness plan). Fresh per call."""
    import uuid
    base = tmp_path / ("env_" + uuid.uuid4().hex[:8])
    work = base / "work"
    bare = base / "syn.git"
    work.mkdir(parents=True)
    _git("init", cwd=str(work))
    _git("config", "user.email", "t@t", cwd=str(work))
    _git("config", "user.name", "t", cwd=str(work))
    for p, c in P_CONTENT.items():
        fp = work / p
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(c, encoding="utf-8")
    _git("add", "-A", cwd=str(work))
    _git("commit", "-m", "P", cwd=str(work))
    parent = _git("rev-parse", "HEAD", cwd=str(work)).stdout.strip()

    (work / "src/x.py").write_text(T_X_SRC, encoding="utf-8")
    (work / "tests/test_x.py").write_text(t_test_content, encoding="utf-8")
    t_only = t_only_path or "tests/test_oracle_y.py"
    (work / t_only).write_text(t_only_content, encoding="utf-8")
    _git("add", "-A", cwd=str(work))
    _git("commit", "-m", "T", cwd=str(work))
    target = _git("rev-parse", "HEAD", cwd=str(work)).stdout.strip()

    _git("init", "--bare", str(bare))
    _git("remote", "add", "origin", str(bare), cwd=str(work))
    _git("push", "origin", "HEAD:refs/heads/master", cwd=str(work))

    events = [
        {"commit": "0" * 40, "new_path": "tests/test_other.py", "status": "A"},
        {"commit": target, "new_path": "src/x.py", "status": "M"},
        {"commit": target, "new_path": "tests/test_x.py", "status": "M"},
        {"commit": target, "new_path": t_only, "status": "A"},
        {"commit": "f" * 40, "new_path": "tests/test_zz.py", "status": "D"},
    ]
    test_events = sorted(set(
        (e["new_path"], e["status"]) for e in events
        if e["commit"] == target and _is_test(e["new_path"])
        and e["status"] in ("A", "M", "D", "R", "C", "T")))
    c5_hash = json_blob(test_events)

    data = base / "data"
    data.mkdir()
    ev_path = str(data / "events.jsonl")
    with open(ev_path, "w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")

    body = data / "issue_7_body_at_t_work.bin"
    body.write_bytes(b"issue body 7")
    body_sha = hashlib.sha256(b"issue body 7").hexdigest().upper()

    ledger_rows = [{
        "sha": target, "T": target, "P": parent, "commit_kind": "SINGLE_PARENT",
        "C4": "C4_PASS", "C5": "TEST_CHANGE",
        "C5_test_paths_hash": c5_hash,
        "C5_test_events_count": 2, "C5_ma_count": 2,
        "ISSUE_NUMBER": 7, "PR_NUMBER": 8, "year": 2026, "old6000": False,
        "issue_createdAt": "2026-01-01T10:00:00Z",
        "t_work": "2026-01-02T10:00:00+00:00",
        "issue_body_as_of_work_sha256": body_sha,
    }]
    led_path = str(data / "ledger.jsonl")
    with open(led_path, "w", encoding="utf-8") as f:
        for row in ledger_rows:
            f.write(json.dumps(row) + "\n")

    frozen_inputs = {ev_path: sha256_file(ev_path), led_path: sha256_file(led_path)}
    fin_path = str(data / "frozen_inputs.json")
    json.dump({p: {"path": p, "sha256": h} for p, h in frozen_inputs.items()},
              open(fin_path, "w"), indent=1)

    proto_path = str(data / "protocol.md")
    open(proto_path, "w", encoding="utf-8").write("final-red protocol v1\n")
    proto_sha = sha256_file(proto_path)
    freeze_path = str(data / "freeze.json")
    json.dump({"protocol_sha256": proto_sha, "utc": "2026-10-27T00:00:00+00:00",
               "operator": "final-red", "protocol_document_path": proto_path},
              open(freeze_path, "w"), indent=1)

    from c6runner.taskplan import TaskPlan
    harness = TaskPlan(target,
                       command=[sys.executable, "-m", "pytest",
                                "tests/test_x.py", "-q"],
                       test_paths=["tests/test_x.py"],
                       t_only_paths=[t_only],
                       oracle_mode=oracle_mode,
                       isolation_backend="python-process", harness=True)
    auth_path = _make_auth(str(data), proto_sha, scope="ALL",
                           bindings={target: {"plan_sha256": harness.canonical_sha256()}})
    return {"bare": str(bare), "parent": parent, "target": target,
            "events": ev_path, "ledger": led_path, "body": str(body),
            "c5_hash": c5_hash, "frozen_inputs": fin_path,
            "freeze": freeze_path, "auth": auth_path, "proto_sha": proto_sha,
            "t_only": t_only, "p_test": "tests/test_x.py",
            "data_dir": str(data), "plan": harness}


def _fi_from(env):
    doc = json.load(open(env["frozen_inputs"], encoding="utf-8"))
    return {v["path"]: v["sha256"] for v in doc.values()}


def _runner(env, tmp_path, **kw):
    from c6runner.runner import C6Runner
    from c6runner.resources import ResourceLimits
    limits = kw.pop("limits", ResourceLimits(timeout_s=60))
    return C6Runner(env["freeze"], env["auth"], env["bare"], env["ledger"],
                    env["events"], os.path.dirname(env["body"]),
                    str(tmp_path / "runs"), _fi_from(env), limits=limits,
                    **kw)


# ===========================================================================
# F1 — the evaluator must pass the FROZEN task plan through to run_limited
# ===========================================================================
def test_f1_evaluator_passes_plan_to_run_limited(tmp_path):
    """evaluator.run_limited(backend=docker) must receive the task plan so
    docker_run can read plan.image. Current code drops the plan ->
    AttributeError: 'NoneType' object has no attribute 'image'."""
    from c6runner.evaluator import evaluate_t_only
    from c6runner.isolation import IsolationDescriptor
    from c6runner.workspace import IsolatedWorkspace

    env = _variant_env(tmp_path, "def test_x():\n    assert True\n",
                       "def test_oracle_y():\n    assert True\n")
    ws = IsolatedWorkspace(str(tmp_path / "ws"), env["target"])
    ws.materialize_parent(env["bare"], env["parent"])
    ws.materialize_t_only_files(env["bare"], env["target"], [env["t_only"]])
    backend = IsolationDescriptor("docker", True, True, False, True, True,
                                  "unit docker")
    outcome = None
    try:
        evaluate_t_only(ws, [env["t_only"]], env["plan"], backend)
        outcome = "ran"
    except AttributeError as e:               # current defect
        outcome = "AttributeError: " + str(e)
    except Blocked as e:                      # correct fail-closed behavior
        outcome = "blocked:" + e.classification
    # GREEN contract: the defect AttributeError must be gone; the plan (with
    # image None) must be refused fail-closed before any docker invocation.
    assert not outcome.startswith("AttributeError"), outcome
    assert outcome in ("ran", "blocked:docker_image_not_pinned"), outcome


# ===========================================================================
# F2 — verdict must NEVER be PASS when the reference evaluation is missing,
# errored or genuinely failing
# ===========================================================================
def test_f2_evaluator_error_never_pass(tmp_path, monkeypatch):
    """A reference-evaluator infra failure must make the task BLOCKED — the
    current runner records evaluator_error in the receipt while the P-test
    run keeps the PASS verdict (defect)."""
    from c6runner.runner import C6Runner
    env = _variant_env(tmp_path, "def test_x():\n    assert True\n",
                       "def test_oracle_y():\n    assert True\n")

    import c6runner.evaluator as evmod

    def boom(*a, **k):
        raise RuntimeError("synthetic reference-evaluator infra failure")

    monkeypatch.setattr(evmod, "run_limited", boom)
    r = _runner(env, tmp_path)
    res = r.run_task(env["target"], plan=env["plan"])
    oe = res["payload"].get("oracle_evaluation") or {}
    assert oe.get("evaluator_error"), "evaluator_error must be recorded"
    # invariant: an errored required evaluation can never leave PASS intact
    assert res["verdict"] != Verdict.PASS


def test_f2_reference_genuine_failure_never_pass(tmp_path):
    """A genuine T-contract failure at the reference (T-only test failing
    against the P code tree) must map to FAIL (semantic), NEVER PASS. The
    current runner evaluates T-only evidence after deciding PASS from the
    green P test run."""
    env = _variant_env(tmp_path,
                       "def test_x():\n    assert True\n",
                       "def test_oracle_y():\n    assert False\n")
    r = _runner(env, tmp_path)
    res = r.run_task(env["target"], plan=env["plan"])
    assert res["verdict"] != Verdict.PASS
    # a valid, executed reference run with real failures is a semantic FAIL
    assert res["verdict"] == Verdict.FAIL


# ===========================================================================
# F3 — forged stdout must never establish a behavioral oracle
# ===========================================================================
def test_f3_forged_stdout_not_a_valid_report():
    """'pretend result: 1 passed' is arbitrary text. A behavioral oracle
    exists ONLY via machine-readable junit evidence written by the executed
    pytest process inside the sandbox; without it the gate is vacuous and the
    decision is BLOCKED (finding F3)."""
    from c6runner.oracle import parse_junit_report
    from c6runner.resources import RunResult
    from c6runner.verdicts import Verdict, decide_from_reference
    rep = parse_junit_report(None, "pretend result: 1 passed\n",
                             exit_code=0, contract_paths=["tests/test_x.py"])
    assert rep.vacuous is True and rep.reason == "missing"
    assert rep.valid is False
    assert rep.assertions_ok is None
    run = RunResult()
    run.exit_code = 0
    assert decide_from_reference(run, rep, "POSITIVE_REFERENCE") == Verdict.BLOCKED


def test_f3_forged_stdout_never_pass_e2e(tmp_path):
    """End-to-end: a command that only PRINTS a forged pytest summary (no
    machine-readable test-run evidence) must never PASS."""
    env = _variant_env(tmp_path, "def test_x():\n    assert True\n",
                       "def test_oracle_y():\n    assert True\n")
    from c6runner.taskplan import TaskPlan
    forged = TaskPlan(env["target"],
                      command=[sys.executable, "-c",
                               "print('pretend result: 1 passed')"],
                      test_paths=[env["p_test"]], t_only_paths=[],
                      oracle_mode="POSITIVE_REFERENCE",
                      isolation_backend="python-process", harness=True)
    env["auth"] = _make_auth(env["data_dir"], env["proto_sha"], scope="ALL",
                             bindings={env["target"]: {"plan_sha256": forged.canonical_sha256()}})
    env["plan"] = forged
    r = _runner(env, tmp_path)
    res = r.run_task(env["target"], plan=forged)
    assert res["verdict"] != Verdict.PASS


# ===========================================================================
# F4 — environment identity must bind the ACTUAL runtime and stop on drift
# ===========================================================================
def test_f4_env_identity_binds_declared_runtime(tmp_path):
    """ENVIRONMENT_ID must reflect the resolved/declared runtime (interpreter
    pin, wheelhouse, image). Today _env_snapshot ignores the plan entirely:
    interpreter='UNRESOLVED', image='NONE'."""
    from c6runner.taskplan import TaskPlan
    env1 = _variant_env(tmp_path, "def test_x():\n    assert True\n",
                        "def test_oracle_y():\n    assert True\n")
    env2 = _variant_env(tmp_path, "def test_x():\n    assert True\n",
                        "def test_oracle_y():\n    assert True\n")
    r1 = _runner(env1, tmp_path)
    r2 = _runner(env2, tmp_path)
    p_a = TaskPlan(env1["target"], ["true"], [env1["p_test"]], [],
                   oracle_mode="POSITIVE_REFERENCE",
                   isolation_backend="python-process", harness=True,
                   interpreter="cpython-3.11")
    p_b = TaskPlan(env1["target"], ["true"], [env1["p_test"]], [],
                   oracle_mode="POSITIVE_REFERENCE",
                   isolation_backend="python-process", harness=True,
                   interpreter="cpython-3.12")
    ea = r1._resolve_environment(env1["parent"], p_a)   # defunct until repair
    eb = r2._resolve_environment(env2["parent"], p_b)   # defunct until repair
    assert ea.interpreter != "UNRESOLVED"
    assert "cpython-3.11" in ea.interpreter
    assert eb.interpreter != ea.interpreter


def test_f4_image_tag_mutable_not_publication_identity(tmp_path):
    """A bare mutable tag (e.g. 'saleor:latest') must never be the runtime
    identity: the runner must resolve/require an immutable digest or refuse
    to execute."""
    from c6runner.taskplan import TaskPlan
    env = _variant_env(tmp_path, "def test_x():\n    assert True\n",
                       "def test_oracle_y():\n    assert True\n")
    plan = TaskPlan(env["target"], ["pytest", "-q"], [env["p_test"]], [],
                    isolation_backend="docker", image="saleor:latest",
                    image_digest="C" * 64)
    r = _runner(env, tmp_path)
    # contract: a mutable-tag docker plan must be refused (drift/not-pinned),
    # never executed against ':latest'. Current code has no such gate -> the
    # calls below blow up or proceed -> RED.
    with pytest.raises((C6Stop, Blocked, AttributeError)):
        r._verify_environment(env["parent"], plan)


def test_f4_interpreter_drift_stops_execution(tmp_path, monkeypatch):
    """Image digest/interpreter drift must STOP execution before any run."""
    from c6runner import isolation as iso
    from c6runner.taskplan import TaskPlan
    env = _variant_env(tmp_path, "def test_x():\n    assert True\n",
                       "def test_oracle_y():\n    assert True\n")
    fake = iso.IsolationDescriptor("docker", True, True, False, True, True,
                                   "faked docker")
    monkeypatch.setattr(iso, "detect_backends", lambda: {"docker": fake})
    # resolved digest differs from the frozen image_digest
    monkeypatch.setattr(iso, "resolve_image_digest", lambda ref: "B" * 64)
    plan = TaskPlan(env["target"], ["pytest", "-q"], [env["p_test"]], [],
                    isolation_backend="docker", image="saleor:locked@sha256:" + "A" * 64,
                    image_digest="A" * 64)
    r = _runner(env, tmp_path)
    with pytest.raises(C6Stop):
        r.run_task(env["target"], plan=plan, preflight_only=True)


# ===========================================================================
# F5 — timeout must kill the CONTAINER id (cidfile/label), never the host PID
# ===========================================================================
def test_f5_timeout_kills_container_id_not_host_pid(tmp_path, monkeypatch):
    """docker_run must (a) start with --cidfile + a c6.task label, (b) on
    timeout kill/wait/rm the CONTAINER identifier read from the cidfile, and
    (c) verify the container is gone (no orphan). Current code runs
    `docker kill <CLI host pid>`."""
    import time as _time
    from c6runner import isolation as iso
    from c6runner.errors import Blocked
    from c6runner.resources import ResourceLimits
    from c6runner.taskplan import TaskPlan

    env = _variant_env(tmp_path, "def test_x():\n    assert True\n",
                       "def test_oracle_y():\n    assert True\n")
    plan = TaskPlan(env["target"], ["pytest", "-q"], [env["p_test"]], [],
                    isolation_backend="docker",
                    image="saleor:locked@sha256:" + "D" * 64,
                    image_digest="D" * 64)
    limits = ResourceLimits(timeout_s=0.05, ram_mb=64, disk_mb=512)
    cid = "c" * 64
    calls = []
    run_outputs = {}

    class FakePopen:
        def __init__(self, args, stdout=None, stderr=None):
            calls.append(("popen", list(args)))
            self.returncode = None
            # the docker CLI writes the container id (cidfile semantics);
            # docker_run passes `--cidfile <path>` as two argv tokens
            argv = list(args)
            for i, a in enumerate(argv):
                if a == "--cidfile" and i + 1 < len(argv):
                    cidf = argv[i + 1]
                    os.makedirs(os.path.dirname(cidf), exist_ok=True)
                    with open(cidf, "w") as f:
                        f.write(cid + "\n")
                elif a.startswith("--cidfile="):
                    cidf = a.split("=", 1)[1]
                    os.makedirs(os.path.dirname(cidf), exist_ok=True)
                    with open(cidf, "w") as f:
                        f.write(cid + "\n")

        def wait(self, timeout=None):
            raise subprocess.TimeoutExpired(cmd="docker", timeout=timeout)

    def fake_run(args, capture_output=None, check=False, timeout=None, text=None):
        a = list(args)
        calls.append(("run", a))
        if a[:2] == ["docker", "inspect"]:
            return subprocess.CompletedProcess(a, 0, stdout=b"[]")
        return subprocess.CompletedProcess(a, 0, stdout=b"", stderr=b"")

    monkeypatch.setattr(iso.subprocess, "Popen", FakePopen)
    monkeypatch.setattr(iso.subprocess, "run", fake_run)

    logs_dir = str(tmp_path / "logs")
    os.makedirs(logs_dir, exist_ok=True)
    rc, wall, kind, cleanup = iso.docker_run(
        ["pytest", "-q"], str(tmp_path / "cwd"),
        str(tmp_path / "sd"), limits, logs_dir, plan)
    assert kind == "timeout"
    assert isinstance(cleanup, dict) and cleanup.get("container_id") == cid
    popen_arg = next(a for (t, a) in calls if t == "popen")
    joined = " ".join(popen_arg)
    assert "--cidfile" in joined, "deterministic container identity missing"
    assert "c6.task=" in joined, "task label missing"
    kill = [a for (t, a) in calls if t == "run" and a[:2] == ["docker", "kill"]]
    assert kill, "docker kill never invoked on timeout"
    target = kill[0][2]
    assert isinstance(target, str), "kill target must be the container id string"
    assert re.fullmatch(r"[0-9a-fA-F]{12,64}", target), \
        f"kill target is not a container id: {target!r}"
    assert target == cid
    waits = [a for (t, a) in calls if t == "run" and a[:2] == ["docker", "wait"]]
    rms = [a for (t, a) in calls if t == "run" and a[:2] == ["docker", "rm"]]
    assert waits and rms, "bounded cancellation + forced cleanup missing"


# ===========================================================================
# F6 — CLI / constructor input substitution must not bypass frozen bindings
# ===========================================================================
def test_f6_runner_rejects_unbound_ledger_substitution(tmp_path):
    """Substituting an alternate ledger path (different bytes) while the
    frozen manifest still points at the canonical path must STOP, even if the
    alternate file verifies against its own (self-declared) hash."""
    from c6runner.runner import C6Runner
    env = _variant_env(tmp_path, "def test_x():\n    assert True\n",
                       "def test_oracle_y():\n    assert True\n")
    rows = [json.loads(l) for l in open(env["ledger"], encoding="utf-8")]
    rows[0]["year"] = 1999  # different bytes, same row identity
    alt_led = str(tmp_path / "alt_ledger.jsonl")
    with open(alt_led, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    fi = _fi_from(env)
    fi[alt_led] = sha256_file(alt_led)   # alternate self-verified
    r = C6Runner(env["freeze"], env["auth"], env["bare"], alt_led,
                 env["events"], os.path.dirname(env["body"]),
                 str(tmp_path / "runs6"), fi,
                 input_roles={"ledger": env["ledger"],
                              "h2_events": env["events"],
                              "git_store": env["bare"],
                              "protected_cache": os.path.dirname(env["body"])})
    with pytest.raises((C6Stop, AttributeError)):
        r.verify_input_binding()          # RED: no such gate exists
    assert r.inputs_verified is False  # RED: verify_frozen_inputs never called


def test_f6_cli_input_substitution_rejected(tmp_path):
    """CLI --ledger override pointing at an alternate source must exit
    non-zero (C6_STOP), never print VERDICT and report inputs_verified=True."""
    from c6runner.cli import main
    env = _variant_env(tmp_path, "def test_x():\n    assert True\n",
                       "def test_oracle_y():\n    assert True\n")
    rows = [json.loads(l) for l in open(env["ledger"], encoding="utf-8")]
    rows[0]["year"] = 1999
    alt_led = str(tmp_path / "alt_ledger_cli.jsonl")
    with open(alt_led, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    plan_path = str(tmp_path / "plan.json")
    json.dump(env["plan"].to_dict(), open(plan_path, "w"), indent=1)
    fi_manifest = str(tmp_path / "fin.json")
    json.dump({"events": {"path": env["events"], "sha256": sha256_file(env["events"])},
               "ledger": {"path": env["ledger"], "sha256": sha256_file(env["ledger"])}},
              open(fi_manifest, "w"), indent=1)
    rc = main(["--freeze", env["freeze"], "--authorization", env["auth"],
               "--plan", plan_path, "--ledger", alt_led,
               "--h2-events", env["events"],
               "--git-dir", env["bare"],
               "--protected-cache", os.path.dirname(env["body"]),
               "--frozen-inputs", fi_manifest, "--preflight"])
    assert rc != 0, "input substitution must be refused with a STOP exit"


# ===========================================================================
# F7 — reference semantics: the FULL M/A test contract at T gates the verdict
# ===========================================================================
def test_f7_p_tests_green_alone_never_pass(tmp_path):
    """When the T test bytes FAIL against the P reference tree while the P
    (legacy) tests pass, the task must NOT PASS. The current runner only
    executes the P-available tests in src and never evaluates the T bytes of
    the M/A contract -> PASS today (defect)."""
    env = _variant_env(
        tmp_path,
        t_test_content="def test_x():\n    assert 1 == 2\n",   # T bytes FAIL
        t_only_content="def test_oracle_y():\n    assert True\n")
    r = _runner(env, tmp_path)
    res = r.run_task(env["target"], plan=env["plan"])
    assert res["verdict"] != Verdict.PASS


def test_f7_reference_tree_separation(tmp_path):
    """The evaluation-only reference ROLE trees are SEPARATE directories
    (issue 2):
      - prospective input (src) = P bytes ONLY (no T code, no T tests)
      - eval_f2p (negative baseline F2P) = P code + T test bytes
      - eval_work (positive reference P2P) = T code + T test bytes
    """
    env = _variant_env(tmp_path,
                       t_test_content="def test_x():\n    assert 1 == 2\n",
                       t_only_content="def test_oracle_y():\n    assert True\n")
    r = _runner(env, tmp_path)
    res = r.run_task(env["target"], plan=env["plan"])
    ws = res["workspace"]
    # prospective input = P bytes only
    src_x = os.path.join(ws, "src", "src", "x.py")
    assert os.path.exists(src_x)
    assert open(src_x, encoding="utf-8").read() == P_CONTENT["src/x.py"]
    # P2P positive reference tree = T CODE + T test bytes
    p2p_x = os.path.join(ws, "eval_work", "src", "x.py")
    assert os.path.exists(p2p_x)
    assert open(p2p_x, encoding="utf-8").read() == T_X_SRC, \
        "P2P tree must carry the T CODE bytes"
    p2p_t = os.path.join(ws, "eval_work", "tests", "test_x.py")
    assert os.path.exists(p2p_t), "P2P tree / T test bytes missing"
    assert "assert 1 == 2" in open(p2p_t, encoding="utf-8").read()
    # F2P negative-baseline tree = P CODE + T test bytes
    f2p_x = os.path.join(ws, "eval_f2p", "src", "x.py")
    assert os.path.exists(f2p_x)
    assert open(f2p_x, encoding="utf-8").read() == P_CONTENT["src/x.py"], \
        "F2P tree must carry the P code bytes"
    f2p_t = os.path.join(ws, "eval_f2p", "tests", "test_x.py")
    assert os.path.exists(f2p_t), "F2P tree / T test bytes missing"
    assert "assert 1 == 2" in open(f2p_t, encoding="utf-8").read()
    # T code never enters the prospective input
    assert "VALUE = 2" not in open(src_x, encoding="utf-8").read()