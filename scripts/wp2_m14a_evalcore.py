#!/usr/bin/env python3
"""WP2 M14A evaluator core (brain-authored, corrected kit). ZERO model API.

Wraps the FROZEN Smoke v2.2/v2.2.1 evaluator primitives (materialize, score, the
frozen group C / group U definitions, 3 repetitions, fresh DB, workers=1) with two
instrument-safety guards that do not change any scientific outcome:

G1 An empty group is never executed. The frozen evaluate_state passes the node list
   to pytest as "${NODES[@]}". With an empty list, pytest receives no node ids and
   collects the default test paths, i.e. the WHOLE Saleor suite, three times.
   Smoke never hit this (every Smoke task had non-empty groups C and U), but a
   Pilot task may have P2P-U UNDEFINED. An empty group contributes no outcomes
   either way, so skipping it is outcome-identical.
G2 Infrastructure failure raises EvalInfraError instead of silently becoming FAIL.
   The frozen code ignores the container return code and turns missing JUnit into
   "missing" outcomes, i.e. a scientific FAIL. Any expected JUnit file that is
   missing now aborts the evaluation (controller EVAL_ERROR, resumable).

Scoring is the frozen `benchmark.wp2.e2e.evaluate.score`, unchanged.
"""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


class EvalInfraError(RuntimeError):
    """Evaluation could not be executed (environment); never a scientific outcome."""


def sets_artifact(tasks: dict[str, dict], version: str) -> dict:
    """Evaluator-sets artifact in the exact hashed schema load_evaluator_sets verifies."""
    d = {"artifact": "pilot_a_evaluator_sets", "version": version, "tasks": tasks,
         "hashes": {"artifact_sha256": ""},
         "leakage_note": "EVALUATOR-ONLY. Never readable by generator/prompt modules."}
    c = copy.deepcopy(d)
    c["hashes"]["artifact_sha256"] = ""
    d["hashes"]["artifact_sha256"] = hashlib.sha256(
        json.dumps(c, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return d


def point_evaluator(sets_path: Path, e2e_root: Path):
    """Point the frozen evaluator at a sets file and a JUnit root; returns the module."""
    import benchmark.wp2.e2e.evaluator_sets as es
    from benchmark.wp2.e2e import evaluate as ev
    es.EVAL_PATH = sets_path
    es._CACHE = None
    ev.E2E_ROOT = e2e_root
    return ev


def evaluate_state_safe(ev: Any, task_id: str, label: str, worktree: str) -> dict:
    """Frozen evaluate_state semantics + guards G1/G2 (see module docstring)."""
    from benchmark.wp2.e2e.scopes import commits_of
    from benchmark.wp2.harness_v3 import (TOOLING_INSTALL, lock_install_script,
                                          locked_dev_install, target_manifests)
    from benchmark.wp2.oracle_confirmation import parse_junit_with_failures
    _, target = commits_of(task_id)
    inv = json.loads((ev.PROJECT / "research/wp2/wp2_dev_unchanged_p2p_candidate_inventory_v1"
                      "_2026-09-25.json").read_text(encoding="utf-8"))
    era_key = next(r["era_key"] for r in inv["tasks"] if r["task_id"] == task_id)
    wt_name = worktree.rsplit("/", 1)[-1]
    db = ev.fresh_db_name(f"saleor-rc-{task_id.split('-')[-1][:12]}", f"g_{label[:4]}")
    t = ev.load_evaluator_sets()["tasks"][task_id]
    groups = {"C": sorted(set(t["behavioral_f2p_node_ids"]) | set(t["p2p_s_node_ids"])),
              "U": list(t["p2p_u_cap200_stable_ids"])}
    active = [g for g in ("C", "U") if groups[g]]                      # G1
    node_outcomes: dict[str, list[str]] = {}
    junit_files: dict[str, str] = {}
    try:
        if active:
            ev.ensure_postgres_running()
            ev.ensure_fresh_db(db)
            manifests = target_manifests(target)
            install_frag, _mode, _ = lock_install_script(worktree, manifests)
            dev_frag = locked_dev_install(task_id)
            runs = []
            for g in active:
                subprocess.run(["wsl", "-d", ev.DISTRO, "--", "bash", "-lc",
                                f"cat > {worktree}/.m14a_{g}.txt"],
                               input=("\n".join(groups[g]) + "\n").encode("utf-8"), timeout=120,
                               check=True)
                for rep in range(ev.REPS):
                    runs.append(
                        f"( mapfile -t NODES < /workspace/{wt_name}/.m14a_{g}.txt && "
                        "/opt/venv/bin/python -m pytest -p no:cacheprovider -o addopts= "
                        "--ds=saleor.tests.settings --disable-socket --reuse-db "
                        f"--junitxml /workspace/{wt_name}/{task_id[:12]}_{label[:4]}_{g}_r{rep}.xml -q "
                        f'"${{NODES[@]}}" >/workspace/{wt_name}/run_{g}_{rep}.log 2>&1; '
                        f"echo RC_{g}_{rep}=$? )")
            subprocess.run(["wsl", "-d", ev.DISTRO, "--", "bash", "-lc",
                            f"mkdir -p {worktree}/logs; cat > {worktree}/.m14a_runs.sh"],
                           input=" ; ".join(runs).encode("utf-8"), capture_output=True,
                           timeout=120, check=True)
            script = ("set -e; uv venv /opt/venv >/dev/null 2>&1 || true; "
                      f"{install_frag}; {dev_frag} >>/tmp/install.log 2>&1 "
                      "|| { echo INSTALL_DEV_FAIL; exit 2; }; "
                      f"{TOOLING_INSTALL} >>/tmp/install.log 2>&1 || {{ echo TOOLING_FAIL; exit 2; }}; "
                      f"cd /workspace/{wt_name} && bash /workspace/{wt_name}/.m14a_runs.sh; "
                      "echo E2E_DONE")
            subprocess.run(["wsl", "-d", ev.DISTRO, "--", "bash", "-lc",
                            f"cat > {worktree}/.m14a_install.sh"],
                           input=script.encode("utf-8"), capture_output=True, timeout=120,
                           check=True)
            r = subprocess.run(["wsl", "-d", ev.DISTRO, "--", "docker", "run", "--rm",
                                "--network", "host", "--ulimit",
                                f"nofile={ev.NOFILE_HARD}:{ev.NOFILE_HARD}",
                                "-e", f"DATABASE_URL=postgres://saleor:saleor@127.0.0.1:5433/{db}",
                                "-e", "CACHE_URL=locmem://",
                                "-v", f"{worktree}:/workspace/{wt_name}",
                                "-v", "wp2-uv-cache:/root/.cache/uv",
                                f"wp2-era-{era_key}", "bash",
                                f"/workspace/{wt_name}/.m14a_install.sh"],
                               capture_output=True, text=True, encoding="utf-8",
                               timeout=ev.STATE_TIMEOUT_S)
            if "E2E_DONE" not in (r.stdout or ""):                     # G2
                raise EvalInfraError(f"evaluation container did not finish: rc={r.returncode} "
                                     f"{(r.stdout or '')[-600:]}")
            for g in active:
                for rep in range(ev.REPS):
                    xml_name = f"{task_id[:12]}_{label[:4]}_{g}_r{rep}.xml"
                    rr = ev.wsl(f"cat {worktree}/{xml_name} 2>/dev/null || echo __NO_FILE__")
                    if "__NO_FILE__" in rr.stdout[:20]:                  # G2
                        raise EvalInfraError(f"JUnit missing: {xml_name}")
                    jd = ev.E2E_ROOT / "junit" / task_id / label
                    jd.mkdir(parents=True, exist_ok=True)
                    (jd / f"{g}_r{rep}.xml").write_text(rr.stdout, encoding="utf-8", newline="")
                    junit_files[f"{g}_r{rep}.xml"] = hashlib.sha256(
                        rr.stdout.encode("utf-8")).hexdigest()
                    outs, _f = parse_junit_with_failures(rr.stdout)
                    for n in groups[g]:
                        node_outcomes.setdefault(n, []).append(outs.get(n, "missing"))
    finally:
        if active:
            ev.drop_db(db)
        ev.wsl(f"git -C {ev.WSL_CACHE} worktree remove --force {worktree} 2>/dev/null "
               f"|| rm -rf {worktree}")
    return {"task_id": task_id, "label": label, "status": "DONE",
            "groups": {g: {n: node_outcomes[n] for n in groups[g] if n in node_outcomes}
                       for g in ("C", "U")},
            "junit_files": junit_files, "skipped_empty_groups": [g for g in ("C", "U")
                                                                 if not groups[g]]}


def gold_nontest_diff(task_id: str) -> tuple[str, str]:
    """(gold non-test diff, target tree sha) from the Saleor cache in WSL."""
    from benchmark.wp2.e2e.scopes import commits_of
    from benchmark.wp2.oracle_semantics_v2 import is_test_path_v2
    from scripts.wp2_linux_dryrun import WSL_CACHE, wsl
    parent, target = commits_of(task_id)
    r = wsl(f"git -C {WSL_CACHE} diff --name-only {parent} {target}")
    if r.returncode != 0:
        raise EvalInfraError(f"git diff failed for {task_id}")
    paths = [p for p in r.stdout.split() if not is_test_path_v2(p)]
    quoted = " ".join(f"'{p}'" for p in paths)
    diff = wsl(f"git -C {WSL_CACHE} diff {parent} {target} -- {quoted}").stdout
    tree = wsl(f"git -C {WSL_CACHE} rev-parse {target}^{{tree}}").stdout.strip()
    return diff, tree


def gold_empty_canary(ev: Any, task_id: str, prefix: str) -> dict:
    """Frozen M14A.S0.A1 check for one task: gold non-test diff on parent+test patch must
    rebuild the target tree and PASS F2P with preservation PASS/UNDEFINED (= Smoke positive
    canary); the empty diff must FAIL F2P with preservation PASS/UNDEFINED (= Smoke negative
    canary). ValueError from materialize (gold diff does not apply) is task-specific."""
    diff, target_tree = gold_nontest_diff(task_id)
    out: dict[str, Any] = {}
    try:
        wt, tree = ev.materialize(task_id, f"{prefix}pos", diff)
    except ValueError as exc:
        return {"gold_applies": False, "gold_error": str(exc)[:500], "ok": False}
    rec = evaluate_state_safe(ev, task_id, f"{prefix}pos", wt)
    out["positive"] = {"tree_matches": tree == target_tree, "tree_sha": tree,
                       "target_tree": target_tree,
                       **ev.score(task_id, f"{prefix}pos", rec["groups"])}
    wt2, _ = ev.materialize(task_id, f"{prefix}neg", "")
    rec2 = evaluate_state_safe(ev, task_id, f"{prefix}neg", wt2)
    out["negative"] = dict(ev.score(task_id, f"{prefix}neg", rec2["groups"]))
    out["gold_applies"] = True
    out["ok"] = canary_ok(out["positive"], out["negative"])
    return out


OK_PRES = ("PASS", "UNDEFINED")


def canary_ok(pos: dict, neg: dict) -> bool:
    return (pos.get("tree_matches") is True and pos.get("f2p_task") == "PASS"
            and pos.get("p2p_s_task") in OK_PRES and pos.get("p2p_u200_task") in OK_PRES
            and neg.get("f2p_task") == "FAIL"
            and neg.get("p2p_s_task") in OK_PRES and neg.get("p2p_u200_task") in OK_PRES)
