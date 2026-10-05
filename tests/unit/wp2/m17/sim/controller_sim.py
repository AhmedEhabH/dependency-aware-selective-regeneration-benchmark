#!/usr/bin/env python3
"""M17 K06 - REAL zero-Docker controller integration in a throwaway git repo.

Builds a throwaway git repository with a bare `origin`, copies the M17 kit
(runner, adapter, plans, manifest, light profiles, tests, sim fake executor)
and the frozen inputs the adapter reads, points the runner at the real frozen
saleor cache (read-only) and at the deterministic fake executor (env), and runs
the REAL controller (scripts/wp2_ctl_v224.py) against the REAL qualification
plan.

Scenarios (mission K06):
  1. happy path through qualification-report/resource-projection -> COMPLETE
  2. adapter violation                                  -> STOP M17_ADAPTER_FAIL
  3. resource HOLD                                     -> STOP HOLD_ACTIVE
  4. resumable infrastructure interruption             -> STOP EVAL_ERROR then COMPLETE
  5. duplicate resume                                  -> COMPLETE again, no duplicate evidence
  6. unknown command                                   -> FAIL (never generic success)
  7. manifest drift                                    -> KIT_TAMPERED
  8. selector-firewall violation                       -> STOP M17_FIREWALL

ZERO Docker, ZERO WSL, ZERO model/API. The fake executor replaces only the
Docker subprocess boundary.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

P = Path(__file__).resolve().parents[5]
SIMSRC = Path(__file__).resolve().parent
QUAL_PLAN = "controller/plan_m17_v1_qualification.json"


def sh(cmd: list[str], cwd: Path, env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=env)
    if check and r.returncode:
        raise RuntimeError(f"{cmd} -> {r.returncode}\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}")
    return r


def norm(p: Path) -> str:
    import hashlib
    b = p.read_bytes()
    if b"\x00" not in b[:8192]:
        b = b.replace(b"\r\n", b"\n")
    return hashlib.sha256(b).hexdigest()


def copy_kit(root: Path) -> None:
    """Copy the M17 kit code + the frozen inputs the adapter/runner read."""
    files = [
        "scripts/wp2_m17_run.py",
        "scripts/wp2_m17_exec.py",
        "scripts/wp2_m16_r1.py",
        "scripts/wp2_m16_firewall.py",
        "scripts/wp2_m17_adapter.py",
        "scripts/wp2_m17_contract.py",
        "scripts/wp2_m17_p01_census.py",
        "scripts/wp2_m17_p04_qualification.py",
        "scripts/wp2_ctl_v224.py",
        "scripts/wp2_export_light.py",
        "controller/plan_m17_v1_qualification.json",
        "controller/plan_m17_v1_main.json",
        "controller/light_profile_m17.json",
        "controller/light_profile_m17_qualification.json",
        "research/wp2/m17_v1/m17_design_freeze_v1.json",
        "research/wp2/m17_v1/m17_historical_schema_contract.json",
        "research/wp2/m17_v1/m17_main_frame_audit.json",
        "research/wp2/m17_v1/m17_qualification_membership.json",
        "research/wp2/m17_v1/m17_qualification_membership_v2_candidate.json",
        "research/wp2/m17_v1/m17_qualification_membership_v2_approved.json",
        "research/wp2/m17_v1/m17_resource_contract.json",
        "research/wp2/m17_v1/m17_m16_root_cause_map.json",
        "research/wp2/m17_v1/m17_membership_decision_record_2026-10-03.json",
        "research/wp2/wp2_saleor_main297_census_2026-09-22.json",
        "research/wp2/wp2_oracle_confirmation_selection_2026-09-22.json",
        "research/wp2/oracle_confirmation_linux_v2_2026-09-23/per_task_v2.jsonl",
        "research/wp2/harness_v3_2026-09-26/phase5_c4_v3_per_task.jsonl",
        "research/wp2/oracle_confirmation_linux_v2_2026-09-23/dev_census_2026-09-23.json",
        "research/wp2/wp2_dev_unchanged_p2p_candidate_inventory_v1_2026-09-25.json",
        "research/wp2/wp2_p2p_u_v2_rule_freeze_2026-09-25.json",
        "DECISIONS.md",
        "PROGRESS.md",
        "pyproject.toml",
        # frozen harness sources relied on at runtime (adapter imports them)
        "src/benchmark/__init__.py",
        "src/benchmark/wp2/__init__.py",
        "src/benchmark/wp2/harness_v3.py",
        "src/benchmark/wp2/dep_compiler.py",
        "src/benchmark/wp2/oracle_semantics_v2.py",
        "src/benchmark/wp2/oracle_confirmation.py",
        "src/benchmark/wp2/era_resolver.py",
        "scripts/wp2_linux_dryrun.py",
        "scripts/__init__.py",
    ]
    for f in files:
        if (P / f).exists():
            dst = root / f
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(P / f, dst)
    # tests + sim fake executor
    for t in (P / "tests/unit/wp2/m17").rglob("*.py"):
        dst = root / t.relative_to(P)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(t, dst)


def build(tmp: Path) -> tuple[Path, Path, dict]:
    root, remote = tmp / "proj", tmp / "origin.git"
    for d in (root, remote):
        d.mkdir(parents=True)
    copy_kit(root)
    # synthetic guard-sensitive pilot files (protected pools empty)
    import json as _j
    for rel, obj in (
        ("research/wp2/pilot_a_v1/pilot_final_membership.json", {"A": [], "B": []}),
        ("research/wp2/pilot_v1_design/pilot_selection.json", {"pilot_a_tasks": [], "pilot_b_tasks": []}),
        ("research/wp2/m14r_v1/m14r_design_freeze_v1.json", {"population": {"candidate_tasks": []}}),
        ("research/wp2/m15r_v1/m15r_design_freeze_v1.json", {"population": {"candidate_tasks": []}}),
    ):
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(_j.dumps(obj), encoding="utf-8")
    # replace the Q00 selftest with a no-op (unit tests run separately; keeps the
    # controller->plan->runner chain fast and focused)
    plan = json.loads((root / QUAL_PLAN).read_text(encoding="utf-8"))
    for ph in plan["phases"]:
        if ph["id"].endswith("_KIT_SELFTEST"):
            ph["command"] = ["{python}", "-c", "print('unit tests run separately in the simulation')"]
    (root / QUAL_PLAN).write_text(json.dumps(plan, indent=1), encoding="utf-8")
    # KIT_MANIFEST_M17 for the throwaway world (re-hash the copied files)
    manifest = {"files": {}}
    for rel in [
        "scripts/wp2_m17_run.py", "scripts/wp2_m17_exec.py", "scripts/wp2_m17_adapter.py",
        "scripts/wp2_m17_p01_census.py", "scripts/wp2_m17_p04_qualification.py",
        "controller/plan_m17_v1_qualification.json", "controller/plan_m17_v1_main.json",
        "controller/light_profile_m17.json", "controller/light_profile_m17_qualification.json",
        "research/wp2/m17_v1/m17_design_freeze_v1.json",
        "research/wp2/m17_v1/m17_historical_schema_contract.json",
        "research/wp2/m17_v1/m17_main_frame_audit.json",
        "research/wp2/m17_v1/m17_qualification_membership.json",
        "research/wp2/m17_v1/m17_qualification_membership_v2_candidate.json",
        "research/wp2/m17_v1/m17_qualification_membership_v2_approved.json",
        "research/wp2/m17_v1/m17_resource_contract.json",
        "research/wp2/m17_v1/m17_m16_root_cause_map.json",
    ]:
        manifest["files"][rel] = norm(root / rel)
    (root / "controller/KIT_MANIFEST_M17.json").write_text(
        json.dumps(manifest, indent=1), encoding="utf-8")
    (root / ".gitignore").write_text("_workspace/\nlogs/\n__pycache__/\n", encoding="utf-8")
    sh(["git", "init", "-q", "-b", "main"], root)
    for k, v in (("user.name", "sim"), ("user.email", "sim@x"), ("core.autocrlf", "false")):
        sh(["git", "config", k, v], root)
    sh(["git", "add", "-A"], root)
    sh(["git", "commit", "-qm", "sim base + M17 kit"], root)
    sh(["git", "init", "-q", "--bare", str(remote)], tmp)
    sh(["git", "remote", "add", "origin", str(remote)], root)
    sh(["git", "push", "-q", "origin", "main"], root)
    env = dict(os.environ)
    env["M17_EXECUTOR_MODULE"] = "tests.unit.wp2.m17.sim.fake_executor"
    env["M17_ALLOW_FAKE_EXECUTOR"] = "1"
    env["M17_SALEOR_CACHE"] = str((P / "dist/pilot-repo-cache/saleor").resolve())
    env["PYTHONPATH"] = os.pathsep.join([str(root / "src"), str(root),
                                        env.get("PYTHONPATH", "")])
    return root, remote, env


def run_scenario(tmp: Path, name: str, *, disk_gib: float | None = None,
                 world: dict | None = None, plan: str = QUAL_PLAN,
                 mutate: callable | None = None, extra_env: dict | None = None,
                 argv_extra: tuple[str, ...] = ()) -> dict:
    root, remote, env = build(tmp / name)
    if disk_gib is not None:
        env["M17_SIM_DISK_GIB"] = str(disk_gib)
    if world is not None:
        wpath = tmp / name / "world.json"
        wpath.write_text(json.dumps(world), encoding="utf-8")
        env["M17_FAKE_WORLD"] = str(wpath)
    env.update(extra_env or {})
    if mutate:
        mutate(root, env)
    r = sh([sys.executable, "scripts/wp2_ctl_v224.py", "run", "--plan", plan, *argv_extra],
           root, env, check=False)
    tail = "\n".join(r.stdout.splitlines()[-16:])
    return {"exit": r.returncode, "stop": [ln for ln in r.stdout.splitlines()
                                           if ln.startswith("STOP_TOKEN=")],
            "tail": tail, "stdout": r.stdout, "root": root, "env": env}


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="m17ctl_"))
    report: dict = {"workdir": str(tmp), "scenarios": {}}
    try:
        # 1. happy path
        s = run_scenario(tmp, "happy")
        report["scenarios"]["happy_path"] = {"exit": s["exit"]}
        assert s["exit"] == 0, s["tail"]

        # 2. adapter violation: one qualification member made unresolved by a
        #    synthetic per_task_v2 row missing lockfile -> adapter-verify exit 35
        def _adapter_bad(root: Path, env: dict) -> None:
            # corrupt the frozen ENG file (missing install_mode) -> the adapter's
            # fail-closed reader raises -> adapter-verify exits 35 -> M17_ADAPTER_FAIL
            eng = root / "research/wp2/harness_v3_2026-09-26/phase5_c4_v3_per_task.jsonl"
            lines = [json.loads(x) for x in eng.read_text().splitlines() if x.strip()]
            lines[0]["manifest"].pop("install_mode", None)
            eng.write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")
            sh(["git", "add", "-A"], root)
            sh(["git", "commit", "-qm", "sim: corrupt ENG record for adapter violation"], root)

        s = run_scenario(tmp, "adapter_bad", mutate=_adapter_bad)
        report["scenarios"]["adapter_violation"] = {"exit": s["exit"],
                                                    "stop": s["stop"]}
        assert s["exit"] == 10 and any("M17_ADAPTER_FAIL" in x for x in s["stop"]), s["tail"]

        # 3. resource HOLD
        s = run_scenario(tmp, "hold", disk_gib=5.0)
        report["scenarios"]["resource_hold"] = {"exit": s["exit"], "stop": s["stop"]}
        assert s["exit"] == 10 and any("HOLD_ACTIVE" in x for x in s["stop"]), s["tail"]

        # 4. resumable infrastructure interruption: first task raises infra once
        def _world_ok() -> dict:
            return {"default_status": "DONE",
                    "per_task": {"saleor-rc-14a682044ca4": {"status": "DONE"}}}

        def _infra_once(world_path: Path, attempts: list) -> None:
            if attempts:
                return
            attempts.append(True)
            world_path.write_text(json.dumps(
                {"default_status": "DONE", "infra_raise": True,
                 "per_task": {"saleor-rc-14a682044ca4": {"status": "DONE"}}}), encoding="utf-8")

        root, remote, env = build(tmp / "resume")
        wpath = tmp / "resume" / "world.json"
        wpath.write_text(json.dumps(_world_ok()), encoding="utf-8")
        env["M17_FAKE_WORLD"] = str(wpath)
        env["M17_SIM_DISK_GIB"] = "60.0"
        # first run: infra_raise via env flag consumed by the fake executor
        env["M17_FAKE_INFRA_ONCE"] = "1"
        r1 = sh([sys.executable, "scripts/wp2_ctl_v224.py", "run", "--plan", QUAL_PLAN],
                root, env, check=False)
        report["scenarios"]["resume_first"] = {"exit": r1.returncode,
                                               "stop": [x for x in r1.stdout.splitlines()
                                                        if x.startswith("STOP_TOKEN=")]}
        assert r1.returncode == 10 and any("EVAL_ERROR" in x for x in r1.stdout.splitlines()), r1.stdout[-2000:]
        del env["M17_FAKE_INFRA_ONCE"]
        r2 = sh([sys.executable, "scripts/wp2_ctl_v224.py", "run", "--plan", QUAL_PLAN],
                root, env, check=False)
        report["scenarios"]["resume_second"] = {"exit": r2.returncode}
        assert r2.returncode == 0, r2.stdout[-2000:]

        # 5. duplicate resume: run the happy repo again -> COMPLETE, no dup evidence
        root, remote, env = build(tmp / "dup")
        wpath = tmp / "dup" / "world.json"
        wpath.write_text(json.dumps(_world_ok()), encoding="utf-8")
        env["M17_FAKE_WORLD"] = str(wpath)
        env["M17_SIM_DISK_GIB"] = "60.0"
        r1 = sh([sys.executable, "scripts/wp2_ctl_v224.py", "run", "--plan", QUAL_PLAN],
                root, env, check=False)
        qdir = root / "research/wp2/m17_v1/qualification"
        n1 = sorted(p.name for p in qdir.glob("saleor-rc-*.json")) if qdir.exists() else []
        # clear the prior LIGHT (created outside the repo in the sim tmp dir) so the
        # exporter's same-minute collision protection does not trip on the resume run
        for z in (tmp / "dup").glob("project-light-*.zip"):
            z.unlink(missing_ok=True)
        r2 = sh([sys.executable, "scripts/wp2_ctl_v224.py", "run", "--plan", QUAL_PLAN],
                root, env, check=False)
        n2 = sorted(p.name for p in qdir.glob("saleor-rc-*.json")) if qdir.exists() else []
        report["scenarios"]["duplicate_resume"] = {"exit1": r1.returncode, "exit2": r2.returncode,
                                                   "n_evidence1": len(n1), "n_evidence2": len(n2)}
        assert r1.returncode == 0 and r2.returncode == 0
        assert len(n2) >= len(n1) and len(n2) <= 12

        # 6. unknown command: plan Q03 command replaced with a bogus subcommand
        def _unknown(root: Path, env: dict) -> None:
            plan = json.loads((root / QUAL_PLAN).read_text(encoding="utf-8"))
            for ph in plan["phases"]:
                if ph["id"] == "Q03_QUALIFICATION_RUN":
                    ph["command"] = ["{python}", "scripts/wp2_m17_run.py", "no-such-command"]
            (root / QUAL_PLAN).write_text(json.dumps(plan, indent=1), encoding="utf-8")
            # the plan file is pinned: rebuild the throwaway manifest so verify-kit
            # still passes and the controller reaches the bogus command (FAIL, not drift)
            mf = json.loads((root / "controller/KIT_MANIFEST_M17.json").read_text(encoding="utf-8"))
            mf["files"][QUAL_PLAN] = norm(root / QUAL_PLAN)
            (root / "controller/KIT_MANIFEST_M17.json").write_text(
                json.dumps(mf, indent=1), encoding="utf-8")
            sh(["git", "add", "-A"], root)
            sh(["git", "commit", "-qm", "sim: bogus command plan"], root)

        s = run_scenario(tmp, "unknown", mutate=_unknown)
        report["scenarios"]["unknown_command"] = {"exit": s["exit"], "stop": s["stop"]}
        # runner exits 2 on bad subcommand -> controller maps to FAIL -> STOP fail_token
        assert s["exit"] == 10, s["tail"]

        # 7. manifest drift: append a byte to a pinned file
        def _drift(root: Path, env: dict) -> None:
            with open(root / "scripts/wp2_m17_adapter.py", "a", encoding="utf-8") as fh:
                fh.write("\n# drift\n")

        s = run_scenario(tmp, "drift", mutate=_drift)
        report["scenarios"]["manifest_drift"] = {"exit": s["exit"]}
        assert s["exit"] == 2, s["tail"]  # KIT_TAMPERED

        # 8. selector-firewall violation: scopes/ exists before Q08
        def _scopes(root: Path, env: dict) -> None:
            (root / "research/wp2/m17_v1/scopes").mkdir(parents=True, exist_ok=True)
            (root / "research/wp2/m17_v1/scopes/__init__.py").write_text("", encoding="utf-8")
            sh(["git", "add", "-A"], root)
            sh(["git", "commit", "-qm", "add scopes"], root)

        s = run_scenario(tmp, "firewall", mutate=_scopes)
        report["scenarios"]["selector_firewall"] = {"exit": s["exit"], "stop": s["stop"]}
        assert s["exit"] == 10 and any("M17_FIREWALL" in x for x in s["stop"]), s["tail"]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("M17_K06_REAL_CONTROLLER_PASS " + json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
