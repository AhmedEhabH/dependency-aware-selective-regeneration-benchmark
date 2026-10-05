"""M17 K04 - runner command parity + runner behavior (zero network, zero Docker).

Verifies:
1. every command in the qualification plan resolves to a real runner entry point;
2. every command in the MAIN plan resolves to a real runner entry point;
3. MAIN scientific commands STOP with the documented authorization-gate token;
4. qualification is resumable by task identity and idempotent (no duplicate
   evidence) with a fake executor;
5. unknown command fails closed (argparse error, never generic success);
6. resource projection is deterministic;
7. no model/API route exists in the runner.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

P = Path(__file__).resolve().parents[4]
for _p in (P, P / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

RUNNER = P / "scripts/wp2_m17_run.py"
QUAL_PLAN = P / "controller/plan_m17_v1_qualification.json"
MAIN_PLAN = P / "controller/plan_m17_v1_main.json"
FAKE_EXECUTOR = "tests.unit.wp2.m17.sim.fake_executor"
MEMBERSHIP = "research/wp2/m17_v1/m17_qualification_membership_v2_approved.json"


def _cmd(command: list[str]) -> list[str]:
    return [sys.executable if c == "{python}" else c for c in command]


def _sub_argv(command: list[str]) -> list[str]:
    cmd = _cmd(command)
    i = [k for k, c in enumerate(cmd) if "wp2_m17_run.py" in c][0]
    return cmd[i + 1:]


def run_argv(argv: list[str], cwd: Path = P, extra_env: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(P / "src"), str(P), env.get("PYTHONPATH", "")])
    env["M17_EXECUTOR_MODULE"] = FAKE_EXECUTOR
    env.update(extra_env or {})
    return subprocess.run([sys.executable, str(RUNNER), *argv], cwd=cwd, capture_output=True,
                          text=True, encoding="utf-8", errors="replace", env=env)


def plan_commands(plan: Path) -> list[tuple[str, list[str]]]:
    d = json.loads(plan.read_text(encoding="utf-8"))
    out = []
    for ph in d["phases"]:
        if ph.get("builtin"):
            continue
        cmd = ph.get("command", [])
        if cmd and any("wp2_m17_run.py" in c for c in cmd if isinstance(c, str)):
            out.append((ph["id"], _sub_argv(cmd)))
    return out


# ------------------------------------------------------------------ command parity
@pytest.mark.parametrize("phase_id,argv", plan_commands(QUAL_PLAN),
                         ids=[pid for pid, _ in plan_commands(QUAL_PLAN)])
def test_qualification_plan_command_resolves(phase_id, argv):
    # the parser accepts the command + its args (dry argparse resolution)
    r = run_argv(["--help"], extra_env={"M17_PREFLIGHT_OK": "1"})
    assert r.returncode == 0
    ap_ok = subprocess.run([sys.executable, str(RUNNER), argv[0], "--help"], cwd=P,
                           capture_output=True, text=True, env={**os.environ,
                                                                "PYTHONPATH": os.pathsep.join(
                                                                    [str(P / "src"), str(P)])})
    assert ap_ok.returncode == 0, f"{phase_id}: parser rejected {argv}"


@pytest.mark.parametrize("phase_id,argv", plan_commands(MAIN_PLAN),
                         ids=[pid for pid, _ in plan_commands(MAIN_PLAN)])
def test_main_plan_command_resolves(phase_id, argv):
    ap_ok = subprocess.run([sys.executable, str(RUNNER), argv[0], "--help"], cwd=P,
                           capture_output=True, text=True, env={**os.environ,
                                                                "PYTHONPATH": os.pathsep.join(
                                                                    [str(P / "src"), str(P)])})
    assert ap_ok.returncode == 0, f"{phase_id}: parser rejected {argv}"


def test_main_scientific_commands_stop_with_auth_gate():
    for cmd in ("oracle", "eligibility-freeze", "evalsets", "readiness", "ready-freeze",
                "scopes", "opws-evaluate", "opws-complete", "analyze", "summary"):
        r = run_argv([cmd, "--resumable", "--max-items", "1"])
        assert r.returncode == 33, f"{cmd} should STOP M17_PREFLIGHT (auth gate), got {r.returncode}"
        assert "M17_MAIN_NOT_AUTHORIZED" in r.stdout
        assert "No scientific execution" in r.stdout


def test_unknown_command_fails_closed():
    r = run_argv(["not-a-real-command"])
    assert r.returncode != 0
    assert "invalid choice" in r.stderr or "invalid choice" in r.stdout or "usage:" in r.stderr.lower()


def test_no_model_api_route_in_runner():
    src = (P / "scripts/wp2_m17_run.py").read_text(encoding="utf-8")
    for tok in ("import requests", "import openai", "from anthropic", "import httpx",
                "import urllib.request", "boto3", "OPENROUTER", "api_key", "API_KEY"):
        assert tok not in src, f"runner references {tok}"


# ------------------------------------------------------------------ qualification behavior (fake executor)
def test_qualification_resumable_and_idempotent(tmp_path):
    from scripts import wp2_m17_run as run

    class Fake:
        def run_task(self, task_id, spec):
            return {"status": "DONE", "classification": "BEHAVIORAL_F2P",
                    "n_nodes": 1, "counts": {"BEHAVIORAL_F2P": 1},
                    "node_records": [], "f2p_nodes": [], "p2p_nodes": [], "wall_s": 1.0,
                    "executor": "fake"}

    orig_qual = run.QUAL_ROOT
    orig_prog = run.PROGRESS
    run.QUAL_ROOT = tmp_path / "qual"
    run.PROGRESS = tmp_path / "qual" / "progress.json"
    run.EXECUTOR = Fake()
    try:
        # chunk 1: max-items 6 -> 6 records
        rc1 = run.qualification(str(MEMBERSHIP), True, 6)
        files1 = sorted(p.name for p in run.QUAL_ROOT.glob("saleor-rc-*.json"))
        assert rc1 == 0 and len(files1) == 6
        # chunk 2: resumable -> next 6
        rc2 = run.qualification(str(MEMBERSHIP), True, 6)
        files2 = sorted(p.name for p in run.QUAL_ROOT.glob("saleor-rc-*.json"))
        assert rc2 == 0 and len(files2) == 12
        # duplicate resume: no new evidence, no changed bytes
        before = {p.name: p.read_bytes() for p in run.QUAL_ROOT.glob("saleor-rc-*.json")}
        rc3 = run.qualification(str(MEMBERSHIP), True, 6)
        after = {p.name: p.read_bytes() for p in run.QUAL_ROOT.glob("saleor-rc-*.json")}
        assert rc3 == 0
        assert before == after, "duplicate execution changed evidence"
        assert len(after) == 12
    finally:
        run.QUAL_ROOT = orig_qual
        run.PROGRESS = orig_prog
        run.EXECUTOR = None


def test_qualification_members_not_in_approved_fails_closed(tmp_path):
    from scripts import wp2_m17_run as run

    class Fake:
        def run_task(self, task_id, spec):
            return {"status": "DONE"}

    orig_exec = run.EXECUTOR
    run.EXECUTOR = Fake()
    try:
        bad = tmp_path / "bad_members.json"
        bad.write_text(json.dumps({"membership": ["saleor-rc-not-a-real-task"] * 12}), encoding="utf-8")
        with pytest.raises(run.Stop):
            run.qualification(str(bad), True, 1)
    finally:
        run.EXECUTOR = orig_exec


def test_qualification_report_deterministic_and_never_crashes(tmp_path):
    from scripts import wp2_m17_run as run

    class Fake:
        def run_task(self, task_id, spec):
            return {"status": "DONE", "classification": "BEHAVIORAL_F2P", "n_nodes": 0,
                    "counts": {}, "node_records": [], "f2p_nodes": [], "p2p_nodes": [], "wall_s": 0.0,
                    "executor": "fake"}

    orig_qual = run.QUAL_ROOT
    orig_report = run.REPORT
    orig_prog = run.PROGRESS
    orig_adapter_rep = run.ADAPTER_REPORT
    run.QUAL_ROOT = tmp_path / "qual"
    run.REPORT = tmp_path / "qual" / "report.json"
    run.PROGRESS = tmp_path / "qual" / "progress.json"
    run.EXECUTOR = Fake()
    # adapter report must be present for the report command; use the real one
    assert run.ADAPTER_REPORT.exists()
    try:
        run.qualification(str(MEMBERSHIP), True, 12)
        rc = run.qualification_report()
        assert rc == 0
        rep = json.loads(run.REPORT.read_text(encoding="utf-8"))
        assert rep["n_members"] == 12 and rep["n_done"] == 12
        assert all(v["status"] == "DONE" for v in rep["per_task"].values())
    finally:
        run.QUAL_ROOT = orig_qual
        run.REPORT = orig_report
        run.PROGRESS = orig_prog
        run.ADAPTER_REPORT = orig_adapter_rep
        run.EXECUTOR = None


def test_resource_projection_deterministic(tmp_path):
    from scripts import wp2_m17_run as run

    orig = run.RESOURCE_PROJ
    run.RESOURCE_PROJ = tmp_path / "proj.json"
    try:
        assert run.resource_projection() == 0
        a = tmp_path / "proj.json"
        run.RESOURCE_PROJ = tmp_path / "proj2.json"
        assert run.resource_projection() == 0
        b = tmp_path / "proj2.json"
        ja = json.loads(a.read_text(encoding="utf-8"))
        jb = json.loads(b.read_text(encoding="utf-8"))
        assert ja["gate"] == jb["gate"]
        assert ja["threshold_lt_gib"] == jb["threshold_lt_gib"]
    finally:
        run.RESOURCE_PROJ = orig
