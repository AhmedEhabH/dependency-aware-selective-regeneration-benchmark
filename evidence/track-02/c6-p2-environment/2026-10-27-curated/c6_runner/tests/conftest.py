# -*- coding: utf-8 -*-
"""Shared synthetic fixtures for c6runner tests (fully offline, no experiments).

Builds a tiny scratch git repo:
  P: src/x.py, src/y.py, tests/test_x.py, requirements.txt, setup.cfg
  T: modifies src/x.py and tests/test_x.py (M events), ADDS tests/test_oracle_y.py
     (A event -> T-only oracle test).
Plus minimal ledger jsonl, H2 events jsonl, protected body cache, frozen
inputs manifest, protocol freeze and authorization receipt files.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from c6runner.hashes import json_blob, sha256_file  # noqa: E402
from c6runner.authorization import FrozenProtocol, AuthorizationReceipt  # noqa: E402

P_CONTENT = {
    "src/x.py": "VALUE = 1\n",
    "src/y.py": "OTHER = 2\n",
    "tests/test_x.py": "def test_x():\n    assert True\n",
    "requirements.txt": "django==2.0\npytest\n",
    "setup.cfg": "[tool:pytest]\ntestpaths = tests\n",
}
T_ONLY_TEST = "tests/test_oracle_y.py"
T_ONLY_CONTENT = "def test_oracle_y():\n    assert True\n"
T_X_TEST = "def test_x():\n    assert True\n\ndef test_x2():\n    assert True\n"
T_X_SRC = "VALUE = 2\n"


def git(*args, cwd=None, env_extra=None, check=True):
    env = dict(os.environ)
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    if env_extra:
        env.update(env_extra)
    r = subprocess.run(["git"] + list(args), capture_output=True, text=True,
                       cwd=cwd, env=env, check=False)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {args}: {r.stderr}")
    return r


@pytest.fixture(scope="session")
def syn(tmp_path_factory):
    base = tmp_path_factory.mktemp("syn")
    work = base / "work"
    bare = base / "syn.git"
    work.mkdir()
    git("init", cwd=str(work))
    git("config", "user.email", "t@t", cwd=str(work))
    git("config", "user.name", "t", cwd=str(work))
    for p, c in P_CONTENT.items():
        fp = work / p
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(c, encoding="utf-8")
    git("add", "-A", cwd=str(work))
    git("commit", "-m", "P", cwd=str(work))
    parent = git("rev-parse", "HEAD", cwd=str(work)).stdout.strip()

    # T: modify x.py + test_x.py, add T-only test
    (work / "src/x.py").write_text(T_X_SRC, encoding="utf-8")
    (work / "tests/test_x.py").write_text(T_X_TEST, encoding="utf-8")
    (work / T_ONLY_TEST).write_text(T_ONLY_CONTENT, encoding="utf-8")
    git("add", "-A", cwd=str(work))
    git("commit", "-m", "T", cwd=str(work))
    target = git("rev-parse", "HEAD", cwd=str(work)).stdout.strip()

    git("init", "--bare", str(bare))
    git("remote", "add", "origin", str(bare), cwd=str(work))
    git("push", "origin", "HEAD:refs/heads/master", cwd=str(work))

    # H2 events (only T's events needed; extra commit rows to prove filtering)
    events = [
        {"commit": "0" * 40, "new_path": "tests/test_other.py", "status": "A"},
        {"commit": target, "new_path": "src/x.py", "status": "M"},
        {"commit": target, "new_path": "tests/test_x.py", "status": "M"},
        {"commit": target, "new_path": T_ONLY_TEST, "status": "A"},
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

    frozen_inputs = {
        ev_path: sha256_file(ev_path),
        led_path: sha256_file(led_path),
    }
    fin_path = str(data / "frozen_inputs.json")
    json.dump({p: {"path": p, "sha256": h} for p, h in frozen_inputs.items()},
              open(fin_path, "w"), indent=1)

    # freeze + authorization receipts
    proto_path = str(data / "protocol.md")
    open(proto_path, "w", encoding="utf-8").write("synthetic protocol v1\n")
    proto_sha = sha256_file(proto_path)
    freeze_path = str(data / "freeze.json")
    json.dump({"protocol_sha256": proto_sha, "utc": "2026-10-27T00:00:00+00:00",
               "operator": "synthetic-test", "protocol_document_path": proto_path},
              open(freeze_path, "w"), indent=1)

    auth_path = _make_auth(data, proto_sha, scope="ALL")
    # integrity check the fixtures themselves
    fp = FrozenProtocol(freeze_path)
    ar = AuthorizationReceipt(auth_path)
    assert ar.authorize(fp) is True

    return {
        "bare": str(bare), "parent": parent, "target": target,
        "events": ev_path, "ledger": led_path, "body": str(body),
        "c5_hash": c5_hash, "frozen_inputs": fin_path,
        "freeze": freeze_path, "auth": auth_path, "proto_sha": proto_sha,
        "t_only_test": T_ONLY_TEST, "p_test": "tests/test_x.py",
        "data_dir": str(data),
    }


def bind_plan_to_auth(auth_path, task_sha, plan_sha):
    """Re-write an authorization receipt to include task_bindings (used by the
    harness plan fixture so plan-bound paths are exercised with real binding)."""
    doc = json.load(open(auth_path, encoding="utf-8"))
    doc["task_bindings"] = doc.get("task_bindings") or {}
    doc["task_bindings"][task_sha] = {"plan_sha256": plan_sha}
    stripped = {k: v for k, v in doc.items() if k != "authorization_sha256"}
    raw = (json.dumps(stripped, indent=1, sort_keys=True) + "\n").encode("utf-8")
    doc["authorization_sha256"] = hashlib.sha256(raw).hexdigest().upper()
    with open(auth_path, "wb") as f:
        f.write((json.dumps(doc, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    return auth_path


@pytest.fixture(scope="session")
def plan(syn):
    """Synthetic harness TaskPlan: runs the real pytest command over the
    synthetic P-tree test; python-process backend, harness=True (unit tests
    only — never an OS-isolation claim). Bound into the synthetic auth so the
    plan-bound runner paths are covered."""
    from c6runner.taskplan import TaskPlan
    p = TaskPlan(syn["target"],
                 command=[sys.executable, "-m", "pytest",
                          syn["p_test"], "-q"],
                 test_paths=[syn["p_test"]],
                 t_only_paths=[syn["t_only_test"]],
                 oracle_mode="POSITIVE_REFERENCE",
                 isolation_backend="python-process", harness=True)
    bind_plan_to_auth(syn["auth"], syn["target"], p.canonical_sha256())
    return p


def _make_auth(data_dir, protocol_sha, scope="ALL", utc="2026-10-27T00:01:00+00:00"):
    # documented convention: authorization_sha256 = SHA-256 over the canonical
    # document WITHOUT the self-field (the verifier recomputes identically).
    doc = {"utc": utc, "operator": "synthetic-test",
           "protocol_sha256": protocol_sha, "scope": scope}
    raw = (json.dumps(doc, indent=1, sort_keys=True) + "\n").encode("utf-8")
    doc["authorization_sha256"] = hashlib.sha256(raw).hexdigest().upper()
    final = (json.dumps(doc, indent=1, sort_keys=True) + "\n").encode("utf-8")
    path = os.path.join(data_dir, f"authorization_{protocol_sha[:16]}.json")
    with open(path, "wb") as f:
        f.write(final)
    return path


def _is_test(path):
    segs = path.split("/")
    if "tests" in segs or "test" in segs:
        return True
    return path.endswith("_test.py") or path.startswith("test_") or path.endswith("conftest.py")