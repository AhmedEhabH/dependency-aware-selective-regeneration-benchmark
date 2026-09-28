"""WP-2 Mission-11 E2E Smoke - evaluator for generated states (B9).

Materializes a generated state (parent + frozen test patch + generated diff),
runs the evaluator groups (Group C = behavioral F2P + P2P-S; Group U = cap200
STABLE_P2P) 3x each with fresh DB and the frozen flags, and scores per D50-D52.
This module (and evaluator_sets) is EVALUATOR-ONLY: generator modules never
import it.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[4]
E2E_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v1"
OUT_ROOT = PROJECT / "research" / "wp2" / "harness_v3_2026-09-26"
WSL_CACHE = "/opt/wp2_v2/saleor-cache"
WSL_WT = "/opt/wp2_v2/worktrees"
DISTRO = "Ubuntu-24.04"

from benchmark.wp2.e2e.evaluator_sets import load_evaluator_sets  # noqa: E402
from benchmark.wp2.e2e.spec import REPS, STATE_TIMEOUT_S  # noqa: E402
from benchmark.wp2.harness_v3 import (  # noqa: E402
    NOFILE_HARD,
    derive_test_patch_linux,
    drop_db,
    ensure_fresh_db,
    ensure_postgres_running,
    fresh_db_name,
)


def _sha(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def wsl(script: str, timeout_s: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["wsl", "-d", DISTRO, "--", "bash", "-lc", script],
                          capture_output=True, text=True, encoding="utf-8", timeout=timeout_s)


def materialize(task_id: str, label: str, diff_text: str) -> tuple[str, str]:
    """Create a detached worktree at parent, apply frozen test patch + diff."""
    from benchmark.wp2.e2e.scopes import commits_of
    parent, _ = commits_of(task_id)
    tid = task_id.split("-")[-1][:12]
    wt = f"{WSL_WT}/{tid}_e2e_{label}"
    wsl(f"git -C {WSL_CACHE} worktree remove --force {wt} 2>/dev/null || rm -rf {wt}")
    r = wsl(f"git -C {WSL_CACHE} worktree add --detach {wt} {parent}", timeout_s=180)
    if r.returncode != 0:
        raise RuntimeError(f"worktree add failed: {r.stderr[-800:]}")
    patch = derive_test_patch_linux(parent, _target(task_id))
    if patch:
        subprocess.run(["wsl", "-d", DISTRO, "--", "bash", "-lc",
                        "cat > /opt/wp2_v2/v31_e2e_test.patch"],
                       input=patch.encode("utf-8"), capture_output=True, timeout=120)
        ap = wsl(f"git -C {wt} apply /opt/wp2_v2/v31_e2e_test.patch")
        if ap.returncode != 0:
            wsl(f"git -C {WSL_CACHE} worktree remove --force {wt} 2>/dev/null || rm -rf {wt}")
            raise RuntimeError(f"test patch apply failed: {ap.stderr[-800:]}")
    if diff_text:
        subprocess.run(["wsl", "-d", DISTRO, "--", "bash", "-lc",
                        "cat > /opt/wp2_v2/v31_e2e_gen.patch"],
                       input=diff_text.encode("utf-8"), capture_output=True, timeout=120)
        check = wsl(f"git -C {wt} apply --check /opt/wp2_v2/v31_e2e_gen.patch")
        if check.returncode != 0:
            wsl(f"git -C {WSL_CACHE} worktree remove --force {wt} 2>/dev/null || rm -rf {wt}")
            raise ValueError(f"generated diff does not apply: {check.stderr[-800:]}")
        ap = wsl(f"git -C {wt} apply /opt/wp2_v2/v31_e2e_gen.patch")
        if ap.returncode != 0:
            wsl(f"git -C {WSL_CACHE} worktree remove --force {wt} 2>/dev/null || rm -rf {wt}")
            raise ValueError(f"generated diff apply failed: {ap.stderr[-800:]}")
    wsl(f"git -C {wt} add -A")
    tree_sha = wsl(f"git -C {wt} write-tree").stdout.strip()
    return wt, tree_sha


def _target(task_id: str) -> str:
    from benchmark.wp2.e2e.scopes import commits_of
    _, target = commits_of(task_id)
    return target


def evaluate_state(task_id: str, label: str, worktree: str) -> dict:
    """Install + run Group C x3 and Group U x3 with fresh DB; persist JUnit."""
    from benchmark.wp2.e2e.scopes import commits_of
    _, target = commits_of(task_id)
    from benchmark.wp2.e2e.evaluator_sets import load_evaluator_sets
    inv = json.loads((PROJECT / "research/wp2/wp2_dev_unchanged_p2p_candidate_inventory_v1_2026-09-25.json")
                     .read_text(encoding="utf-8"))
    era_key = next(r["era_key"] for r in inv["tasks"] if r["task_id"] == task_id)
    from benchmark.wp2.harness_v3 import (
        TOOLING_INSTALL,
        lock_install_script,
        locked_dev_install,
        target_manifests,
    )

    wt_name = worktree.rsplit("/", 1)[-1]
    db = fresh_db_name(f"saleor-rc-{task_id.split('-')[-1][:12]}", f"g_{label[:4]}")
    ensure_postgres_running()
    ensure_fresh_db(db)
    manifests = target_manifests(target)
    install_frag, mode, _ = lock_install_script(worktree, manifests)
    dev_frag = locked_dev_install(task_id)

    sets = load_evaluator_sets()
    t = sets["tasks"][task_id]
    group_c = sorted(set(t["behavioral_f2p_node_ids"]) | set(t["p2p_s_node_ids"]))
    group_u = list(t["p2p_u_cap200_stable_ids"])

    subprocess.run(["wsl", "-d", DISTRO, "--", "bash", "-lc",
                    f"cat > {worktree}/.v31_e2e_c.txt"],
                   input=("\n".join(group_c) + "\n").encode("utf-8"), timeout=120)
    subprocess.run(["wsl", "-d", DISTRO, "--", "bash", "-lc",
                    f"cat > {worktree}/.v31_e2e_u.txt"],
                   input=("\n".join(group_u) + "\n").encode("utf-8"), timeout=120)

    runs = []
    for group, fname in (("C", ".v31_e2e_c.txt"), ("U", ".v31_e2e_u.txt")):
        for rep in range(REPS):
            runs.append(
                f"( mapfile -t NODES < /workspace/{wt_name}/{fname} && "
                "/opt/venv/bin/python -m pytest -p no:cacheprovider -o addopts= "
                f"--ds=saleor.tests.settings --disable-socket --reuse-db "
                f"--junitxml /workspace/{wt_name}/{task_id[:12]}_{label[:4]}_{group}_r{rep}.xml -q "
                f'\"${{NODES[@]}}\" >/workspace/{wt_name}/run_{group}_{rep}.log 2>&1; '
                f"echo RC_{group}_{rep}=$? )"
            )
    runs_script = " ; ".join(runs)
    subprocess.run(["wsl", "-d", DISTRO, "--", "bash", "-lc",
                    f"mkdir -p {worktree}/logs; cat > {worktree}/.v31_e2e_runs.sh"],
                   input=runs_script.encode("utf-8"), capture_output=True, timeout=120)
    script = (
        "set -e; uv venv /opt/venv >/dev/null 2>&1 || true; "
        f"{install_frag}; {dev_frag} >>/tmp/install.log 2>&1 "
        "|| { echo INSTALL_DEV_FAIL; exit 2; }; "
        f"{TOOLING_INSTALL} >>/tmp/install.log 2>&1 || {{ echo TOOLING_FAIL; exit 2; }}; "
        f"cd /workspace/{wt_name} && bash /workspace/{wt_name}/.v31_e2e_runs.sh; echo E2E_DONE"
    )
    subprocess.run(["wsl", "-d", DISTRO, "--", "bash", "-lc",
                    f"cat > {worktree}/.v31_e2e_install.sh"],
                   input=script.encode("utf-8"), capture_output=True, timeout=120)
    subprocess.run(["wsl", "-d", DISTRO, "--", "docker", "run", "--rm", "--network", "host",
                        "--ulimit", f"nofile={NOFILE_HARD}:{NOFILE_HARD}",
                        "-e", f"DATABASE_URL=postgres://saleor:saleor@127.0.0.1:5433/{db}",
                        "-e", "CACHE_URL=locmem://",
                        "-v", f"{worktree}:/workspace/{wt_name}",
                        "-v", "wp2-uv-cache:/root/.cache/uv",
                        f"wp2-era-{era_key}", "bash", f"/workspace/{wt_name}/.v31_e2e_install.sh"],
                       capture_output=True, text=True, encoding="utf-8", timeout=STATE_TIMEOUT_S)

    from benchmark.wp2.oracle_confirmation import parse_junit_with_failures
    junit_files: dict[str, str] = {}
    node_outcomes: dict[str, list[str]] = {}
    for group, fname in (("C", ".v31_e2e_c.txt"), ("U", ".v31_e2e_u.txt")):
        nodes = (worktree and wsl(f"cat {worktree}/{fname}").stdout.splitlines()) or []
        for rep in range(REPS):
            xml_name = f"{task_id[:12]}_{label[:4]}_{group}_r{rep}.xml"
            rr = wsl(f"cat {worktree}/{xml_name} 2>/dev/null || echo __NO_FILE__")
            if "__NO_FILE__" in rr.stdout[:20]:
                for n in nodes:
                    node_outcomes.setdefault(n, []).append("missing")
                continue
            junit_dir = E2E_ROOT / "junit" / task_id / label
            junit_dir.mkdir(parents=True, exist_ok=True)
            jp = junit_dir / f"{group}_r{rep}.xml"
            jp.write_text(rr.stdout, encoding="utf-8", newline="")
            junit_files[f"{group}_r{rep}.xml"] = hashlib.sha256(rr.stdout.encode("utf-8")).hexdigest()
            outs, _fails = parse_junit_with_failures(rr.stdout)
            for n in nodes:
                node_outcomes.setdefault(n, []).append(outs.get(n, "missing"))
    drop_db(db)
    wsl(f"git -C {WSL_CACHE} worktree remove --force {worktree} 2>/dev/null || rm -rf {worktree}")
    return {"task_id": task_id, "label": label, "status": "DONE",
            "groups": {"C": {n: o for n, o in node_outcomes.items() if n in set(group_c)},
                       "U": {n: o for n, o in node_outcomes.items() if n in set(group_u)}},
            "junit_files": junit_files}


def score(task_id: str, label: str, node_outcomes: dict[str, dict[str, list[str]]]) -> dict:
    """D50-D52 scoring from {group: {node: [o1,o2,o3]}}."""
    sets = load_evaluator_sets()
    t = sets["tasks"][task_id]

    def passed(outcomes: list[str]) -> bool:
        return len(outcomes) == 3 and all(o == "passed" for o in outcomes)

    c = node_outcomes.get("C", {})
    u = node_outcomes.get("U", {})
    f2p_nodes = [n for n in t["behavioral_f2p_node_ids"] if n in c]
    f2p_ok = all(passed(c[n]) for n in f2p_nodes)
    f2p_task = "PASS" if f2p_ok and f2p_nodes else ("UNDEFINED" if not f2p_nodes else "FAIL")
    p2ps_nodes = [n for n in t["p2p_s_node_ids"] if n in c]
    p2ps_task = ("PASS" if all(passed(c[n]) for n in p2ps_nodes)
                 else ("UNDEFINED" if not p2ps_nodes else "FAIL"))
    p2pu_nodes = [n for n in t["p2p_u_cap200_stable_ids"] if n in u]
    p2pu_task = ("PASS" if all(passed(u[n]) for n in p2pu_nodes)
                 else ("UNDEFINED" if not p2pu_nodes else "FAIL"))
    flaky = [n for n in c if n in c and any(o != "passed" for o in c[n])]
    resolved = (f2p_task == "PASS" and p2ps_task in ("PASS", "UNDEFINED")
                and p2pu_task in ("PASS", "UNDEFINED"))
    return {"task_id": task_id, "label": label,
            "f2p_task": f2p_task, "p2p_s_task": p2ps_task, "p2p_u200_task": p2pu_task,
            "resolved": resolved, "flaky_under_patch": sorted(flaky)}
