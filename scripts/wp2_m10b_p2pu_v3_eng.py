#!/usr/bin/env python3
"""WP-2 Mission-10B Phase 5B: P2P-U V3 ENG rediscovery + execution (20) - ZERO API.

TRUE candidate rediscovery under Harness V3 (not frozen V2 membership reuse):

For each V3 oracle-valid ENG task:
1. Re-run unchanged-test candidate discovery (pytest --collect-only at the
   TARGET state inside the V3 era container, nofile=65536, lock-exact install)
   over the frozen associated unchanged-test files -- SAME scientific rule as
   P2P-U V2 (same candidate pool source, UNKNOWN handling, proximal/distal,
   salt, hashing, round-robin, 3P:1D, cap200/cap400, first200 subset first400).
2. Freeze the NEW V3 raw candidate pool BEFORE outcome execution.
3. Derive V3 cap200/cap400 memberships from the V3-discovered pool.
4. Report true V2->V3 membership diff (raw candidates, files, first200,
   first400, intersection, additions, removals, reason categories).
5. Execute V3 cap200 and cap400 INDEPENDENTLY, workers=1, 3 parent + 3 target
   reps, nofile=65536, fresh DB policy, frozen classify_p2p_node taxonomy.

The V2 membership is a comparison baseline only, never the V3 population.

Usage:
    python scripts/wp2_m10b_p2pu_v3_eng.py --task saleor-rc-... [--cap 200|400]
    python scripts/wp2_m10b_p2pu_v3_eng.py --all-tasks [--cap 200|400]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.harness_v3 import (  # noqa: E402
    NOFILE_HARD,
    NOFILE_SOFT,
    TOOLING_INSTALL,
    base_image_id,
    clock_preflight,
    drop_db,
    ensure_fresh_db,
    ensure_postgres_running,
    ensure_worktrees_v3,
    fresh_db_name,
    git_linux,
    lock_install_script,
    locked_dev_install,
    lockfile_sha256,
    remove_worktrees_v3,
    target_manifests,
    wsl,
    wsl_docker,
)
from benchmark.wp2.p2p_inventory_dev_v1 import classify_p2p_node  # noqa: E402
from benchmark.wp2.p2p_u_v2 import build_task_selection  # noqa: E402

V2_ROOT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23"
OUT_ROOT = PROJECT / "research" / "wp2" / "harness_v3_2026-09-26"
MEMBERSHIP = json.loads((PROJECT / "research" / "wp2" /
                         "wp2_p2p_u_v2_membership_2026-09-25.json").read_text(encoding="utf-8"))
INVENTORY = json.loads((PROJECT / "research" / "wp2" /
                        "wp2_dev_unchanged_p2p_candidate_inventory_v1_2026-09-25.json").read_text(encoding="utf-8"))
WSL_CACHE = "/opt/wp2_v2/saleor-cache"
WSL_WT = "/opt/wp2_v2/worktrees"
WSL_DISTRO = "Ubuntu-24.04"
REPS = 3
P2PU_V3_VERSION = "p2p-u-v3-eng-2026-09-26"


def _now_utc() -> str:
    import datetime
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def _sha256(payload: object) -> str:
    import hashlib
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def load_v3_oracle_valid_eng() -> list[str]:
    ds = json.loads((V2_ROOT / "dev_split_v2_2026-09-23.json").read_text(encoding="utf-8"))
    eng = set(ds["membership"].get("DEV_TRAIN_ENG", []))
    valid = []
    for line in (V2_ROOT / "per_task_dev_v2.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["task_id"] in eng:
            f = OUT_ROOT / f"phase5_c4v3_{r['task_id']}.json"
            if f.exists():
                rec = json.loads(f.read_text(encoding="utf-8"))
                if rec.get("classification") == "BEHAVIORAL_F2P":
                    valid.append(r["task_id"])
    return sorted(valid)


def inventory_row(task_id: str) -> dict:
    for r in INVENTORY["tasks"]:
        if r["task_id"] == task_id:
            return r
    raise RuntimeError(f"{task_id} not in unchanged-test inventory")


def task_commits(task_id: str) -> tuple[str, str]:
    census = json.loads((V2_ROOT / "dev_census_2026-09-23.json").read_text(encoding="utf-8"))
    for t in census.get("tasks", []):
        if t["task_id"] == task_id:
            return t["parent_commit"], t["target_commit"]
    raise RuntimeError(f"{task_id} not in census")


def v2_membership_for(task_id: str, cap: int) -> list[str]:
    t = MEMBERSHIP.get("tasks", {}).get(task_id)
    if not t:
        return []
    key = "cap200_node_ids" if cap == 200 else "cap400_node_ids"
    return list(t.get(key, []))


# ---------------------------------------------------------------------------
# V3 rediscovery (20 step 1)
# ---------------------------------------------------------------------------
def rediscover_v3(task_id: str) -> dict:
    """pytest --collect-only at TARGET under V3 environment (nofile, lock-exact)."""
    row = inventory_row(task_id)
    parent, target = task_commits(task_id)
    era_key = row["era_key"]
    all_associated = row.get("associated_unchanged_test_files", [])
    collect_files = [
        f for f in all_associated
        if f.endswith(".py") and "[" not in f and "]" not in f
        and not f.endswith("__init__.py") and not f.endswith("conftest.py")
    ]
    tid = task_id.split("-")[-1][:12]
    wt = f"{WSL_WT}/{tid}_v3_p2pu_t"
    wsl(f"mkdir -p {WSL_WT}")
    wsl(f"git -C {WSL_CACHE} worktree remove --force {wt} 2>/dev/null || rm -rf {wt}")
    r = git_linux(WSL_CACHE, "worktree", "add", "--detach", wt, target)
    if r.returncode != 0:
        raise RuntimeError(f"[wt] target add FAILED: {r.stderr[-1200:]}")
    wt_name = wt.rsplit("/", 1)[-1]

    manifests = target_manifests(target)
    install_frag, install_mode, _ = lock_install_script(wt, manifests)
    locked_dev = locked_dev_install(task_id)

    subprocess.run(["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
                    f"cat > {wt}/.wp2_disc_files.txt"],
                   input=("\n".join(collect_files) + "\n").encode("utf-8"),
                   capture_output=True, timeout=180, check=True)
    script = (
        "#!/usr/bin/env bash\nset -e\n"
        "uv venv /opt/venv >/dev/null 2>&1 || true\n"
        f"{install_frag} >/tmp/install.log 2>&1 || "
        "{ echo INSTALL_FAIL; tail -120 /tmp/install.log; exit 2; }\n"
        f"{locked_dev} >>/tmp/install.log 2>&1 || "
        "{ echo INSTALL_DEV_FAIL; tail -80 /tmp/install.log; exit 2; }\n"
        f"{TOOLING_INSTALL} >>/tmp/install.log 2>&1 || "
        "{ echo TOOLING_FAIL; tail -80 /tmp/install.log; exit 2; }\n"
        f"cd /workspace/{wt_name}\n"
        f"mapfile -t FILES < /workspace/{wt_name}/.wp2_disc_files.txt\n"
        "rc=0\n"
        "/opt/venv/bin/python -m pytest -p no:cacheprovider -o addopts= "
        "--ds=saleor.tests.settings --collect-only -q "
        '"${FILES[@]}" >/tmp/collect.log 2>&1 || rc=$?\n'
        "grep -E '::' /tmp/collect.log | grep -v '^=' | sort -u > "
        f"/workspace/{wt_name}/.wp2_disc_nodes.txt\n"
        "echo COLLECT_RC=$rc\n"
    )
    subprocess.run(["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
                    f"cat > {wt}/.wp2_discover.sh"],
                   input=script.encode("utf-8"), capture_output=True, timeout=180, check=True)
    r = wsl_docker(
        ["run", "--rm", "--network", "host",
         "--ulimit", f"nofile={NOFILE_SOFT}:{NOFILE_HARD}",
         "-e", "DATABASE_URL=postgres://saleor:saleor@127.0.0.1:5433/saleor",
         "-e", "CACHE_URL=locmem://",
         "-v", f"{wt}:/workspace/{wt_name}",
         "-v", "wp2-uv-cache:/root/.cache/uv",
         f"wp2-era-{era_key}", "bash", f"/workspace/{wt_name}/.wp2_discover.sh"],
        timeout_s=7200,
    )
    nodes_txt = wsl(f"cat {wt}/.wp2_disc_nodes.txt 2>/dev/null || echo __NO_FILE__")
    nodes = []
    if "__NO_FILE__" not in nodes_txt.stdout[:20]:
        nodes = sorted(line.strip() for line in nodes_txt.stdout.splitlines() if line.strip())
    wsl(f"git -C {WSL_CACHE} worktree remove --force {wt} 2>/dev/null || rm -rf {wt}")
    wsl(f"git -C {WSL_CACHE} worktree prune 2>/dev/null || true")
    return {
        "task_id": task_id,
        "era_key": era_key,
        "target_commit": target,
        "rediscovery_version": "p2p-u-v3-eng-rediscovery-2026-09-26",
        "install_mode": install_mode,
        "collect_rc": r.returncode,
        "n_associated_files": len(all_associated),
        "n_collect_files": len(collect_files),
        "candidate_node_ids": nodes,
        "wall_s": round(time.monotonic(), 1),
    }


def derive_v3_selection(discovery: dict) -> dict:
    """Derive V3 cap200/cap400 from the V3-discovered pool (SAME rule/salt)."""
    touched = []
    census = json.loads((V2_ROOT / "dev_census_2026-09-23.json").read_text(encoding="utf-8"))
    for c in census.get("tasks", []):
        if c["task_id"] == discovery["task_id"]:
            r = git_linux(WSL_CACHE, "diff", "--name-only", c["parent_commit"], c["target_commit"])
            touched = [ln.strip() for ln in r.stdout.splitlines()
                       if ln.strip().endswith(".py") and "/test" not in ln]
            break
    sel = build_task_selection(
        task_id=discovery["task_id"],
        candidate_node_ids=discovery["candidate_node_ids"],
        touched_production_files=touched,
    )
    return sel


# ---------------------------------------------------------------------------
# V3 execution (20 step 5)
# ---------------------------------------------------------------------------
def run_p2pu_state(*, era_key: str, worktree_linux: str, tid: str, state: str,
                   cap: int, node_ids: list[str], install_fragment: str,
                   locked_dev_fragment: str, timeout_s: int) -> tuple[dict, dict]:
    wt_name = worktree_linux.rsplit("/", 1)[-1]
    mount = f"{worktree_linux}:/workspace/{wt_name}"
    db_name = fresh_db_name(f"saleor-rc-{tid}", state)
    ensure_postgres_running()
    ensure_fresh_db(db_name)
    subprocess.run(["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
                    f"cat > {worktree_linux}/.p2pu_nodes.txt"],
                   input=("\n".join(node_ids) + "\n").encode("utf-8"),
                   capture_output=True, timeout=180, check=True)
    runs_script_lines = []
    for rep in range(REPS):
        logf = f"/workspace/{wt_name}/logs/run_{rep}.log"
        runs_script_lines.append(
            f"( mapfile -t NODES < /workspace/{wt_name}/.p2pu_nodes.txt && "
            "/opt/venv/bin/python -m pytest -p no:cacheprovider -o addopts= "
            "--ds=saleor.tests.settings --disable-socket --reuse-db "
            f"--junitxml /workspace/{wt_name}/{tid}_{state}_c{cap}_r{rep}.xml -q "
            f'\"${{NODES[@]}}\" >{logf} 2>&1; echo RUN_{rep}_RC=$? >>{logf} )'
        )
    runs_script = " ; ".join(runs_script_lines)
    subprocess.run(["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
                    f"mkdir -p {worktree_linux}/logs; cat > {worktree_linux}/.p2pu_runs.sh"],
                   input=runs_script.encode("utf-8"), capture_output=True, timeout=180, check=True)
    script = (
        "set -e; "
        "uv venv /opt/venv >/dev/null 2>&1 || true; "
        f"{install_fragment}; "
        f"{locked_dev_fragment} >>/tmp/install.log 2>&1 "
        "|| { echo INSTALL_DEV_FAIL; tail -80 /tmp/install.log; exit 2; }; "
        f"{TOOLING_INSTALL} >>/tmp/install.log 2>&1 || {{ echo TOOLING_FAIL; "
        "tail -80 /tmp/install.log; exit 2; }; "
        f"cd /workspace/{wt_name} && bash /workspace/{wt_name}/.p2pu_runs.sh; "
        "echo ALL_RUNS_DONE"
    )
    wsl_docker(
        ["run", "--rm", "--network", "host",
         "--ulimit", f"nofile={NOFILE_SOFT}:{NOFILE_HARD}",
         "-e", f"DATABASE_URL=postgres://saleor:saleor@127.0.0.1:5433/{db_name}",
         "-e", "CACHE_URL=locmem://",
         "-v", mount, "-v", "wp2-uv-cache:/root/.cache/uv",
         f"wp2-era-{era_key}", "bash", "-lc", script],
        timeout_s=timeout_s,
    )
    from benchmark.wp2.oracle_confirmation import parse_junit_with_failures
    outcomes: dict[str, list[str]] = {}
    failures: dict[str, str] = {}
    for rep in range(REPS):
        rr = wsl(f"cat {worktree_linux}/{tid}_{state}_c{cap}_r{rep}.xml 2>/dev/null || echo __NO_FILE__")
        if "__NO_FILE__" in rr.stdout[:20]:
            for n in node_ids:
                outcomes.setdefault(n, []).append("missing")
            continue
        try:
            outs, fails = parse_junit_with_failures(rr.stdout)
        except Exception:
            outs, fails = {}, {}
        for n in node_ids:
            outcomes.setdefault(n, []).append(outs.get(n, "missing"))
            if n in fails:
                failures[n] = fails[n]
    drop_db(db_name)
    return outcomes, failures


def execute_cap(task_id: str, cap: int, node_ids: list[str], discovery: dict) -> dict:
    parent, target = task_commits(task_id)
    row = inventory_row(task_id)
    era_key = row["era_key"]
    print(f"[P2PU-V3] {task_id} cap={cap} nodes={len(node_ids)} era={era_key}", flush=True)

    clock = clock_preflight()
    if clock["verdict"] == "CLOCK_BLOCKED":
        return {"task_id": task_id, "cap": cap, "status": "CLOCK_BLOCKED"}

    manifests = target_manifests(target)
    wts = ensure_worktrees_v3(task_id, parent, target)
    tid = task_id.split("-")[-1][:12]
    install_t, install_mode, _ = lock_install_script(wts["t"], manifests)
    install_p, _, _ = lock_install_script(wts["p"], manifests)
    locked_dev = locked_dev_install(task_id)
    img_id = base_image_id(era_key)

    outcomes_t, failures_t = run_p2pu_state(
        era_key=era_key, worktree_linux=wts["t"], tid=tid, state="t", cap=cap,
        node_ids=node_ids, install_fragment=install_t,
        locked_dev_fragment=locked_dev, timeout_s=28800)
    outcomes_p, failures_p = run_p2pu_state(
        era_key=era_key, worktree_linux=wts["p"], tid=tid, state="p", cap=cap,
        node_ids=node_ids, install_fragment=install_p,
        locked_dev_fragment=locked_dev, timeout_s=28800)

    class_counts = {"STABLE_P2P": 0, "TARGET_BROKEN": 0, "PARENT_BROKEN": 0,
                    "BOTH_FAIL": 0, "FLAKY": 0, "COLLECTION_ERROR": 0}
    node_classes = {}
    for nid in node_ids:
        t = outcomes_t.get(nid, ["missing"] * 3)
        p = outcomes_p.get(nid, ["missing"] * 3)
        t_list = t if isinstance(t, list) else [t] * 3
        p_list = p if isinstance(p, list) else [p] * 3
        cls = classify_p2p_node(list(p_list), list(t_list))
        class_counts[cls] = class_counts.get(cls, 0) + 1
        node_classes[nid] = cls

    result = {
        "task_id": task_id,
        "cap": cap,
        "status": "DONE",
        "era_key": era_key,
        "rediscovery_sha256": discovery.get("rediscovery_sha256", ""),
        "n_selected": len(node_ids),
        "class_counts": class_counts,
        "n_stable_p2p": class_counts.get("STABLE_P2P", 0),
        "node_classes": node_classes,
        "wall_s": round(time.monotonic(), 1),
        "manifest": {
            "task_id": task_id, "era": era_key, "cap": cap,
            "harness_v3_version": "wp2-harness-v3-2026-09-26",
            "frozen_base_image_id": img_id,
            "install_mode": install_mode,
            "lockfile_sha256": lockfile_sha256(manifests),
            "nofile_soft": NOFILE_SOFT, "nofile_hard": NOFILE_HARD,
            "clock_pre_post": {"pre": clock["pre"]["median_skew_s"],
                               "post": (clock.get("post") or {}).get("median_skew_s")},
            "workers": 1,
        },
    }
    remove_worktrees_v3(task_id)
    (OUT_ROOT / f"p2pu_v3_eng_{task_id}_cap{cap}.json").write_text(
        json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"  -> {class_counts}", flush=True)
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default=None)
    ap.add_argument("--cap", type=int, default=None, choices=(200, 400))
    ap.add_argument("--all-tasks", action="store_true")
    ap.add_argument("--discovery-only", action="store_true")
    args = ap.parse_args()
    tasks = [args.task] if args.task else (load_v3_oracle_valid_eng() if args.all_tasks else [])
    caps = [args.cap] if args.cap else [200, 400]
    if not tasks:
        print("no tasks selected; use --task or --all-tasks")
        return 2
    print(f"[P2PU-V3] tasks={len(tasks)} caps={caps}", flush=True)
    for tid in tasks:
        discovery_file = OUT_ROOT / f"p2pu_v3_rediscovery_{tid}.json"
        if discovery_file.exists():
            discovery = json.loads(discovery_file.read_text(encoding="utf-8"))
        else:
            print(f"  {tid}: rediscovering candidates under V3 ...", flush=True)
            discovery = rediscover_v3(tid)
            sel = derive_v3_selection(discovery)
            v2_200 = set(v2_membership_for(tid, 200))
            v2_400 = set(v2_membership_for(tid, 400))
            v3_200 = set(sel.get("cap200_node_ids", []))
            v3_400 = set(sel.get("cap400_node_ids", []))
            discovery["rediscovery_sha256"] = _sha256({
                "task_id": tid,
                "candidate_node_ids": discovery["candidate_node_ids"],
            })
            discovery["v3_selection"] = {
                "cap200_node_ids": sel.get("cap200_node_ids", []),
                "cap400_node_ids": sel.get("cap400_node_ids", []),
                "proximal_nodes": sel.get("proximal_nodes", []),
                "distal_nodes": sel.get("distal_nodes", []),
                "composition_cap200": sel.get("composition_cap200"),
                "composition_cap400": sel.get("composition_cap400"),
            }
            discovery["membership_diff"] = {
                "v2_cap200": sorted(v2_200),
                "v3_cap200": sorted(v3_200),
                "v2_cap400": sorted(v2_400),
                "v3_cap400": sorted(v3_400),
                "cap200_intersection": sorted(v2_200 & v3_200),
                "cap200_additions": sorted(v3_200 - v2_200),
                "cap200_removals": sorted(v2_200 - v3_200),
                "cap400_intersection": sorted(v2_400 & v3_400),
                "cap400_additions": sorted(v3_400 - v2_400),
                "cap400_removals": sorted(v2_400 - v3_400),
            }
            discovery_file.write_text(json.dumps(discovery, indent=1, ensure_ascii=False),
                                      encoding="utf-8")
            print(f"  -> rediscovered {len(discovery['candidate_node_ids'])} nodes; "
                  f"cap200={len(v3_200)} cap400={len(v3_400)}")
        if args.discovery_only:
            continue
        for cap in caps:
            f = OUT_ROOT / f"p2pu_v3_eng_{tid}_cap{cap}.json"
            if f.exists():
                print(f"  {tid} cap{cap} already done; skip", flush=True)
                continue
            sel = discovery.get("v3_selection", {})
            key = "cap200_node_ids" if cap == 200 else "cap400_node_ids"
            node_ids = list(sel.get(key, []))
            if not node_ids:
                print(f"  {tid} cap{cap} UNDEFINED (zero nodes)", flush=True)
                (OUT_ROOT / f"p2pu_v3_eng_{tid}_cap{cap}.json").write_text(
                    json.dumps({"task_id": tid, "cap": cap, "status": "UNDEFINED",
                                "n_selected": 0}, indent=1), encoding="utf-8")
                continue
            execute_cap(tid, cap, node_ids, discovery)
    print("[P2PU-V3] complete", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
