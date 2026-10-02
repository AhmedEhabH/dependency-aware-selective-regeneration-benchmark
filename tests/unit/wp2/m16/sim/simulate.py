#!/usr/bin/env python3
"""M16 zero-Docker / zero-API end-to-end simulation (synthetic world, real controller + engine).

Builds a throw-away git repository with a bare `origin`, copies the M16 kit and the frozen code it
pins, writes SYNTHETIC inputs (220-task frame, 297 MAIN ids, selections, gold sets), points a copy
of the engine at `sim_world.FakeWorld` (the shipped engine is never modified), and runs the REAL
controller (scripts/wp2_ctl_v224.py) through the dry-run plan and the main plan, including
injected faults and negative scenarios. Prints a JSON report.

    python tests/unit/wp2/m16/sim/simulate.py [--out report.json] [--keep]
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

P = Path(__file__).resolve().parents[5]
SIMSRC = Path(__file__).resolve().parent
R = "research/wp2/m16_v1/"


def sh(cmd: list[str], cwd: Path, env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    if check and r.returncode:
        raise RuntimeError(f"{cmd} -> {r.returncode}\n{r.stdout[-3000:]}\n{r.stderr[-3000:]}")
    return r


def norm(p: Path) -> str:
    b = p.read_bytes()
    if b"\x00" not in b[:8192]:
        b = b.replace(b"\r\n", b"\n")
    return hashlib.sha256(b).hexdigest()


def sha_obj(x) -> str:
    return hashlib.sha256(json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def wj(root: Path, rel: str, obj) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def synth(root: Path, sim: Path, seed: int = 16) -> dict:
    rng = random.Random(seed)
    ids = [f"saleor-rc-sim{i:09d}" for i in range(297)]
    frame = ids[:220]
    dev = [f"saleor-rc-dev{i:09d}" for i in range(5)]
    eras = ["py38", "py39", "py312"]
    tasks = {}
    for i, t in enumerate(ids):
        k = rng.random()
        kind = ("behavioral" if k < 0.55 else "not_primary" if k < 0.80 else "install_blocked" if k < 0.90
                else "behavioral_not_ready")
        app = f"saleor/app{i % 9}"
        gold = [f"{app}/m{j}.py" for j in range(rng.randint(1, 4))]
        noise = [f"{app}/n{j}.py" for j in range(3)] + [f"saleor/other{i % 5}/z.py"]
        tasks[t] = {"era": eras[i % 3], "parent": f"{i:040x}"[-40:], "target": f"{i + 1000:040x}"[-40:],
                    "kind": kind, "gold": gold, "essential": gold[:rng.randint(1, len(gold))],
                    "repo_files": gold + noise, "large": [gold[-1]] if (i % 37 == 5 and len(gold) > 1) else [],
                    "f2p": [f"{app}/tests/test_m.py::test_{i}_{j}" for j in range(rng.randint(1, 3))],
                    "p2ps": [f"{app}/tests/test_m.py::test_keep_{i}_{j}" for j in range(rng.randint(0, 2))],
                    "p2pu": [f"{app}/tests/test_u.py::test_u_{i}_{j}" for j in range(rng.randint(0, 3))],
                    "breaks_if_partial": [gold[0]] if i % 11 == 3 else []}
        if tasks[t]["large"] and tasks[t]["large"][0] in tasks[t]["essential"]:
            tasks[t]["essential"] = [g for g in tasks[t]["essential"] if g not in tasks[t]["large"]] or [gold[0]]

    def pick(t: str, p_full: float) -> list[str]:
        g, n = tasks[t]["gold"], tasks[t]["repo_files"][len(tasks[t]["gold"]):]
        u = rng.random()
        if u < 0.12:
            return []
        if u < p_full:
            s = list(g)
        else:
            s = rng.sample(g, max(1, len(g) - 1)) if len(g) > 1 else ([] if rng.random() < 0.5 else g)
        return sorted(set(s + rng.sample(n, rng.randint(0, 2))))
    world = {"tasks": tasks, "dev_ids": dev}
    wj(sim, "world.json", world)
    wj(root, "research/wp1b/wp1b_main_297_manifest.json", {"task_ids": ids, "n": 297})
    wj(root, "research/wp2/wp2_saleor_main297_census_2026-09-22.json",
       {"tasks": [{"task_id": t, "parent_commit": tasks[t]["parent"], "target_commit": tasks[t]["target"]}
                  for t in ids]})
    wj(root, "research/wp2/wp2_oracle_confirmation_selection_2026-09-22.json",
       {"status": "FROZEN_BEFORE_ORACLE_EXECUTION", "selection": {"tasks": [{"task_id": t} for t in frame]}})
    v2 = root / "research/wp2/oracle_confirmation_linux_v2_2026-09-23"
    v2.mkdir(parents=True, exist_ok=True)
    (v2 / "per_task_v2.jsonl").write_text("".join(json.dumps({"task_id": t, "era_key": tasks[t]["era"]}) + "\n"
                                                 for t in frame), encoding="utf-8")
    wj(root, str((v2 / "summary_v2.json").relative_to(root)), {"sim": True})
    wj(root, str((v2 / "wp2_unchanged_p2p_candidate_inventory_v1_final_2026-09-25.json").relative_to(root)),
       {"tasks": [{"task_id": t, "associated_unchanged_test_files": ["x/tests/test_u.py"]} for t in ids]})
    wj(root, str((v2 / "dev_census_2026-09-23.json").relative_to(root)),
       {"tasks": [{"task_id": t, "parent_commit": "d" * 40, "target_commit": "e" * 40} for t in dev]})
    wj(root, str((v2 / "dev_split_v2_2026-09-23.json").relative_to(root)), {"sim": True})
    wj(root, "research/wp2/wp2_dev_unchanged_p2p_candidate_inventory_v1_2026-09-25.json",
       {"tasks": [{"task_id": t, "era_key": "py39"} for t in dev]})
    for f in ("research/wp2/main_generation_quarantine_2026-09-23.json",
              "research/wp2/protected_pools_untouched_proof_2026-09-23.json",
              "research/wp2/wp2_p2p_u_v2_rule_freeze_2026-09-25.json",
              "research/wp2/wp2_p2p_u_v2_membership_2026-09-25.json",
              "research/wp2/harness_v3_2026-09-26/harness_v3_spec.json",
              "research/wp2/m15r_v1/m15r_e1a1_amendment.json"):
        wj(root, f, {"sim": True, "path": f})
    lock = lambda tgt: hashlib.sha256(("L" + tgt[:6]).encode()).hexdigest()[:16]  # noqa: E731

    def hist(t: str, status: str, with_closure: bool) -> dict:          # R2A: mixed historical schema
        m = {"install_mode": "LOCK_EXACT_MAIN_PLUS_DEV", "lockfile_sha256": lock("e" * 40)}
        if with_closure:                                                 # V3.1-era record
            m["dev_test_closure"] = {"mechanism": "poetry", "n_pins": 1, "pins_sha256": "p", "n_unsupported": 0}
        return {"task_id": t, "status": status, "target_commit": "e" * 40, "manifest": m}
    (root / "research/wp2/harness_v3_2026-09-26/phase5_c4_v3_per_task.jsonl").write_text("".join(
        json.dumps(r) + "\n" for r in (hist(dev[0], "DONE", True), hist(dev[1], "ENV_INSTALL_BLOCKED", False),
                                       hist(dev[2], "DONE", False))), encoding="utf-8")
    wj(root, "research/wp2/pilot_a_v1/pilot_final_membership.json", {"A": [], "B": []})
    wj(root, "research/wp2/pilot_v1_design/pilot_selection.json", {"pilot_a_tasks": [], "pilot_b_tasks": []})
    wj(root, "research/wp2/m14r_v1/m14r_design_freeze_v1.json", {"population": {"candidate_tasks": []}})
    wj(root, "research/memory-rescue-v2/final_oof_predictions_A.json", {t: [] for t in dev})
    wj(root, "research/wp1a/sip_rmcss_per_task_predictions.json",
       {"per_task": {t: {"rmcss_predicted_set": pick(t, 0.45)} for t in ids}})
    (root / "research/wp1b/main-297-2026-09-22").mkdir(parents=True, exist_ok=True)
    (root / "research/wp1b/main-297-2026-09-22/agent_run_records.jsonl").write_text("".join(
        json.dumps({"task_id": t, "replicate": 0, "selected_paths": pick(t, 0.40)}) + "\n" for t in ids),
        encoding="utf-8")
    var = frame[:15]
    (root / "research/wp1b/variance-15x3-2026-09-22").mkdir(parents=True, exist_ok=True)
    (root / "research/wp1b/variance-15x3-2026-09-22/agent_run_records.jsonl").write_text("".join(
        json.dumps({"task_id": t, "replicate": k, "selected_paths": pick(t, 0.4)}) + "\n"
        for t in var for k in (1, 2, 3)), encoding="utf-8")
    for d in ("research/stage5-v2-final",):
        wj(root, d + "/deployment_artifact.json", {"sim": True})
    return world


def build(tmp: Path) -> tuple[Path, Path, Path, dict]:
    root, sim, remote, cold = tmp / "proj", tmp / "sim", tmp / "origin.git", tmp / "cold"
    for d in (root, sim, cold):
        d.mkdir(parents=True)
    design = json.loads((P / R / "m16_design_freeze_v1.json").read_text(encoding="utf-8"))
    copy_files = set(design["kit_code_files"]) | {"scripts/wp2_m16_r2a.py",
        "scripts/wp2_ctl_v224.py", "scripts/wp2_export_light.py", "scripts/wp2_m14r_core.py",
        "src/benchmark/__init__.py", "src/benchmark/wp2/__init__.py", "src/benchmark/wp1b/__init__.py",
        "src/benchmark/wp2/oracle_semantics_v2.py", "src/benchmark/wp1b/git_gate.py", "scripts/__init__.py",
        R + "m16_l_opws_quarantine_amendment.json", R + "m16_r1_repetition_amendment.json",
        "controller/plan_m16_v1.json", "controller/plan_m16_v1_dryrun.json", "controller/light_profile_m16.json",
        "DECISIONS.md", "PROGRESS.md", "pyproject.toml"}
    for f in design["pins"]["file_norm_sha256"]:
        if f.endswith(".py"):
            copy_files.add(f)
    for f in sorted(copy_files):
        if (P / f).exists():
            (root / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(P / f, root / f)
    world = synth(root, sim)
    # engine + resource copies pointed at the synthetic world (the shipped files are untouched)
    eng = (root / "scripts/wp2_m16_run.py").read_text(encoding="utf-8")
    eng = eng.replace('WORLD: Any = None   # injectable (tests); defaults to RealWorld()',
                      'sys.path.insert(0, os.environ["M16_SIM_WORLD_DIR"])\n'
                      'WORLD: Any = __import__("sim_world").FakeWorld()')
    res = (root / "scripts/wp2_m16_resource.py").read_text(encoding="utf-8")
    res = res.replace('def c_free_gib(path: str | None = None) -> float:\n',
                      'def c_free_gib(path: str | None = None) -> float:\n'
                      '    if os.environ.get("M16_SIM_DIR"):\n'
                      '        return json.loads((Path(os.environ["M16_SIM_DIR"]) / "disk.json").read_text())["c_free_gib"]\n')
    (root / "scripts/wp2_m16_resource.py").write_text(res, encoding="utf-8", newline="\n")
    # synthetic design: same constants/amendments, synthetic pins, re-hashed; engine pin patched
    d = copy.deepcopy(design)
    d["pins"]["file_norm_sha256"] = {f: norm(root / f) for f in design["pins"]["file_norm_sha256"]}
    d["status"] = "SIMULATION COPY (synthetic pins)"
    d["artifact_sha256"] = ""
    d["artifact_sha256"] = sha_obj(d)
    wj(root, R + "m16_design_freeze_v1.json", d)
    eng = re.sub(r'DESIGN_SHA = "[^"]*"', f'DESIGN_SHA = "{d["artifact_sha256"]}"', eng)
    (root / "scripts/wp2_m16_run.py").write_text(eng, encoding="utf-8", newline="\n")
    for pf in ("controller/plan_m16_v1.json", "controller/plan_m16_v1_dryrun.json"):
        plan = json.loads((root / pf).read_text(encoding="utf-8"))
        for ph in plan["phases"]:
            if ph["id"].endswith("_KIT_SELFTEST"):
                ph["command"] = ["{python}", "-c", "print('unit tests run separately in the simulation')"]
        wj(root, pf, plan)
    kit = sorted(set(design["kit_code_files"]) | {"scripts/wp2_m16_r2a.py", "controller/plan_m16_v1.json", "controller/plan_m16_v1_dryrun.json",
                                                  "controller/light_profile_m16.json", "scripts/wp2_ctl_v224.py",
                                                  R + "m16_design_freeze_v1.json"})
    wj(root, "controller/KIT_MANIFEST_M16.json", {"files": {f: norm(root / f) for f in kit}})
    (root / ".gitignore").write_text("_workspace/\nlogs/\n__pycache__/\n", encoding="utf-8")
    sh(["git", "init", "-q", "-b", "main"], root)
    for k, v in (("user.name", "sim"), ("user.email", "sim@x"), ("core.autocrlf", "false")):
        sh(["git", "config", k, v], root)
    sh(["git", "add", "-A"], root)
    sh(["git", "commit", "-qm", "sim base + M16 kit"], root)
    sh(["git", "init", "-q", "--bare", str(remote)], tmp)
    sh(["git", "remote", "add", "origin", str(remote)], root)
    sh(["git", "push", "-q", "origin", "main"], root)
    sh(["git", "tag", "-a", design["constants"]["tags"]["kit"], "-m", "kit"], root)
    sh(["git", "push", "-q", "origin", f"refs/tags/{design['constants']['tags']['kit']}"], root)
    return root, sim, cold, world


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="m16sim_"))
    root, sim, cold, world = build(tmp)
    env = dict(os.environ, M16_SIM_DIR=str(sim), M16_SIM_WORLD_DIR=str(SIMSRC), M16_COLD_ROOT=str(cold),
               PYTHONPATH=os.pathsep.join([str(root / "src"), str(root)]))
    py = sys.executable
    rep: dict = {"workdir": str(tmp), "steps": []}

    def ctl(plan: str, *extra: str) -> subprocess.CompletedProcess:
        r = sh([py, "scripts/wp2_ctl_v224.py", "run", "--plan", plan, *extra], root, env, check=False)
        tail = "\n".join(r.stdout.splitlines()[-14:])
        rep["steps"].append({"cmd": f"ctl {plan} {' '.join(extra)}", "exit": r.returncode,
                             "stop": re.findall(r"STOP_TOKEN=(\S+)", r.stdout), "tail": tail})
        return r

    def eng(*args: str, extra_env: dict | None = None) -> subprocess.CompletedProcess:
        r = sh([py, "scripts/wp2_m16_run.py", *args], root, dict(env, **(extra_env or {})), check=False)
        rep["steps"].append({"cmd": "engine " + " ".join(args), "exit": r.returncode,
                             "tail": "\n".join((r.stdout + r.stderr).splitlines()[-4:])})
        return r

    def faults(**kw) -> None:
        (sim / "faults.json").write_text(json.dumps(kw), encoding="utf-8")

    def disk(g: float) -> None:
        (sim / "disk.json").write_text(json.dumps({"c_free_gib": g}), encoding="utf-8")

    frame = [t for t in json.loads((root / "research/wp2/wp2_oracle_confirmation_selection_2026-09-22.json")
                                   .read_text())["selection"]["tasks"]]
    frame = sorted(x["task_id"] for x in frame)
    beh = [t for t in frame if world["tasks"][t]["kind"] == "behavioral"]
    # ---------------- dry-run plan: first S3_REQUIRED, then PASS after "maintenance"
    disk(30.0)
    faults(gib_per_state=0.004)
    r1_ = ctl("controller/plan_m16_v1_dryrun.json")
    rep["dryrun_first"] = {"exit": r1_.returncode, "stop": re.findall(r"STOP_TOKEN=(\S+)", r1_.stdout)}
    disk(60.0)
    faults(gib_per_state=0.0005)
    r2_ = ctl("controller/plan_m16_v1_dryrun.json")
    rep["dryrun_after_s3"] = {"exit": r2_.returncode}
    # ---------------- negative: adapter fail-closed, firewall
    faults(closure_none=[frame[7]])
    rep["neg_adapter_fail_closed_exit"] = eng("adapter-verify").returncode
    sh(["git", "checkout", "--", R + "adapter/adapter_report.json"], root)
    faults(oracle_infra_first=[beh[0]], infra_attempts=2)
    rep["neg_firewall_exit"] = eng("oracle", "--max-tasks", "1",
                                   extra_env={"M16_SIM_FIREWALL_PROBE": "1"}).returncode
    # ---------------- main plan with injected faults
    faults(oracle_infra_first=[beh[0], beh[1]], infra_attempts=2, p2pu_infra_first=[beh[2]],
           opws_infra_always=[beh[3]], e1a1_tasks=beh[4:6], gib_per_state=0.0005)
    # beh[1] keeps failing on every attempt -> ORACLE_INFRA_UNRESOLVED after the resume
    f = json.loads((sim / "faults.json").read_text())
    f["oracle_infra_first"] = [beh[0], beh[1]]
    (sim / "faults.json").write_text(json.dumps(f), encoding="utf-8")
    c = ctl("controller/plan_m16_v1.json", "--until", "Q05M_MIRROR")
    rep["main_first"] = re.findall(r"STOP_TOKEN=(\S+)", c.stdout)
    f["infra_attempts"] = 2                                   # beh[0] recovers on attempt 3
    f["oracle_infra_first"] = [beh[0], beh[1]]
    f["infra_attempts_by_task"] = {beh[1]: 99}
    (sim / "faults.json").write_text(json.dumps(f), encoding="utf-8")
    for _ in range(4):
        c = ctl("controller/plan_m16_v1.json", "--until", "Q05M_MIRROR")
        if c.returncode == 20 and "PAUSED_AT_Q05M_MIRROR" in c.stdout:
            break
    rep["neg_scopes_before_ready_exit"] = eng("scopes").returncode
    for _ in range(4):
        c = ctl("controller/plan_m16_v1.json", "--until", "Q07M_MIRROR")
        if "PAUSED_AT_Q07M_MIRROR" in c.stdout:
            break
    sh(["git", "tag", "-a", "wp2-m16-v1-ready-dup", "-m", "dup"], root)
    sh(["git", "push", "-q", "origin", "refs/tags/wp2-m16-v1-ready-dup"], root)
    rep["neg_duplicate_ready_tag_exit"] = eng("scopes").returncode
    sh(["git", "tag", "-d", "wp2-m16-v1-ready-dup"], root)
    sh(["git", "push", "-q", "origin", ":refs/tags/wp2-m16-v1-ready-dup"], root)
    for _ in range(8):
        c = ctl("controller/plan_m16_v1.json")
        if c.returncode == 0:
            break
    rep["main_final_exit"] = c.returncode
    def opt(rel: str) -> dict:
        return json.loads((root / R / rel).read_text()) if (root / R / rel).exists() else {}
    ana, elig = opt("analysis/m16_analysis.json"), opt("m16_v3_eligibility.json")
    rem = sh(["git", "ls-remote", "--tags", "origin"], root).stdout
    rep["remote_tags"] = sorted({x.split("refs/tags/")[1].removesuffix("^{}")
                                 for x in rem.splitlines() if "refs/tags/" in x})
    rep["eligibility_status_counts"] = elig.get("status_counts")
    rep["n_eligible"] = elig.get("n_eligible")
    rep["analysis_tokens"] = ana.get("tokens")
    rep["n_ready"], rep["n_analysed"] = ana.get("n_ready"), ana.get("n_analysed")
    rep["listwise_dropped"] = ana.get("listwise_dropped")
    rep["amended_e1a1_tasks"] = ana.get("amended_e1a1_tasks")
    rep["primary_table"] = (ana.get("primary_robust") or {}).get("table")
    rep["tango_95"] = (ana.get("primary_robust") or {}).get("tango_95")
    rep["amended_item_rate"] = ana.get("amended_item_rate")
    rep["amended_e1a1_items"] = ana.get("amended_e1a1_items")
    rep["n_evaluated_items"] = ana.get("n_evaluated_items")
    # resume idempotency (verifier fix 3): re-running the freezes after COMPLETE must not change any byte
    rep["refreeze_exits"] = {c: eng(c).returncode for c in ("evalsets-freeze", "scopes", "opws-complete")}
    rep["refreeze_git_status"] = sh(["git", "status", "--porcelain", "--", R], root).stdout.splitlines()
    rep["scopes_verify_exit"] = eng("scopes-verify").returncode
    rep["historical_verify_exit"] = eng("historical-verify").returncode
    rep["cold_mirror_files"] = sum(1 for _ in cold.rglob("*") if _.is_file())
    rep["light_zips"] = sorted(p.name for p in root.parent.glob("project-LIGHT-*.zip")) + \
        sorted(p.name for p in root.glob("project-LIGHT-*.zip"))
    ledger = root / R / "oracle/attempts.jsonl"
    rep["oracle_attempt_ledger"] = [json.loads(x) for x in ledger.read_text().splitlines()] if ledger.exists() else []
    rep["oracle_infra_unresolved"] = sorted(t for t, v in (elig.get("tasks") or {}).items()
                                            if v["status"] == "ORACLE_INFRA_UNRESOLVED")
    rep["report_md_exists"] = (root / "docs/WP2_M16_V1_RESULT.md").exists()
    out = json.dumps(rep, indent=1, sort_keys=True)
    if a.out:
        Path(a.out).write_text(out + "\n", encoding="utf-8")
    print(out[-6000:])
    if not a.keep:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
