#!/usr/bin/env python3
"""WP-2 DEV unchanged-test P2P SERIAL pilot - frozen evaluator (Mission-08).

Runs the frozen P2P Preservation Rule V1 evaluator SERIALLY (workers=1) for one
DEV task using the frozen candidate-node set from the DEV inventory artifact.

Frozen semantics (addendum Q1/Q2/Q7):
- PARENT condition: parent commit + SAME frozen test patch as the Linux V2 F2P
  oracle (TEST_PATCH_APPLIED_ON_PARENT=true). Target condition: target commit.
- Every discovered candidate node is executed 3/3 on parent and 3/3 on target
  (NO pre-cap; NO early-stop; NO reduced repetitions).
- Exactly one P2P class per node (Q2 precedence):
  FLAKY > COLLECTION_ERROR > STABLE_P2P > TARGET_BROKEN > PARENT_BROKEN >
  BOTH_FAIL. Only STABLE_P2P nodes enter the preservation set; the frozen
  fixed-seed cap=400 is applied to the STABLE_P2P set only.

Evidence is persisted per task, verified, then the completed worktrees are
removed and PostgreSQL test DBs dropped.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.oracle_confirmation import parse_junit_with_failures  # noqa: E402
from benchmark.wp2.p2p_inventory_dev_v1 import (  # noqa: E402
    classify_p2p_node,
)
from scripts.wp2_linux_dryrun import (  # noqa: E402
    TOOLING_INSTALL,
    WSL_CACHE,
    WSL_DISTRO,
    WSL_WT,
    deps_install_cmd,
    ensure_cache,
    ensure_era_images,
    ensure_postgres,
    wsl,
    wsl_docker,
)

INVENTORY_ARTIFACT = PROJECT / "research" / "wp2" / "wp2_dev_unchanged_p2p_candidate_inventory_v1_2026-09-25.json"
EVIDENCE_ROOT = PROJECT / "research" / "wp2" / "p2p_serial_pilot_2026-09-25"

PILOT_VERSION = "p2p-serial-pilot-v1-2026-09-25"
REPS = 3


def git_linux(workdir: str, *args: str) -> subprocess.CompletedProcess[str]:
    quoted = " ".join(f"'{a}'" for a in args)
    return wsl(f"git -C {workdir} {quoted}")


def ensure_worktrees(task_id: str, parent: str, target: str) -> dict:
    """Frozen state creation: target worktree + parent worktree WITH the frozen
    test patch applied (Q1)."""
    tid = task_id.split("-")[-1][:12]
    wt_t = f"{WSL_WT}/{tid}_t"
    wt_p = f"{WSL_WT}/{tid}_p"
    wsl(f"mkdir -p {WSL_WT}")
    r = wsl(f"test -e {wt_t}/.git && echo OK || echo MISSING")
    if "OK" not in r.stdout:
        r = git_linux(WSL_CACHE, "worktree", "add", "--detach", wt_t, target)
        if r.returncode != 0:
            raise SystemExit(f"[wt] target add FAILED: {r.stderr[-1200:]}")
    r = wsl(f"test -f {wt_p}/.wp2_patch_applied && echo OK || echo MISSING")
    if "OK" not in r.stdout:
        git_linux(WSL_CACHE, "worktree", "remove", "--force", wt_p)
        r = git_linux(WSL_CACHE, "worktree", "add", "--detach", wt_p, parent)
        if r.returncode != 0:
            raise SystemExit(f"[wt] parent add FAILED: {r.stderr[-1200:]}")
        patch = derive_test_patch_linux(parent, target)
        if patch:
            proc = subprocess.run(
                ["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
                 f"cat > {WSL_CACHE}/../patch.patch"],
                input=patch.encode("utf-8"), capture_output=True, timeout=120,
            )
            if proc.returncode != 0:
                raise SystemExit(f"[wt] patch write FAILED: {proc.stderr[-500:]}")
            ap = git_linux(wt_p, "apply", f"{WSL_CACHE}/../patch.patch")
            if ap.returncode != 0:
                raise SystemExit(f"[wt] parent patch apply FAILED: {ap.stderr[-800:]}")
        wsl(f"touch {wt_p}/.wp2_patch_applied")
    return {"t": wt_t, "p": wt_p}


def derive_test_patch_linux(parent: str, target: str) -> str:
    from benchmark.wp2.oracle_semantics_v2 import is_test_path_v2

    r = git_linux(WSL_CACHE, "diff", "--name-status", parent, target)
    paths = []
    for line in r.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and is_test_path_v2(parts[-1]):
            paths.append(parts[-1])
    if not paths:
        return ""
    r = git_linux(WSL_CACHE, "diff", parent, target, "--", *paths)
    if r.returncode != 0:
        raise SystemExit(f"patch diff failed: {r.stderr}")
    return r.stdout


def group_nodes_by_file(node_ids: list[str]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for node in node_ids:
        f = node.split("::", 1)[0]
        groups.setdefault(f, []).append(node)
    return {k: sorted(v) for k, v in sorted(groups.items())}


def sample_wsl_mem_gib() -> float:
    r = wsl("free -g | sed -n '2p'")
    parts = (r.stdout or "").split()
    return float(parts[1]) if len(parts) >= 2 else 0.0  # total GiB


def run_state(
    *,
    era_key: str,
    worktree_linux: str,
    tid: str,
    state: str,
    node_groups: dict[str, list[str]],
    timeout_s: int = 14400,
) -> dict:
    """One container per state: install deps once, then run each node-group 3x
    with per-run JUnit (frozen C4-style per-file isolation). Node IDs are
    passed via sidecar files (robust for unicode/special-char node IDs).
    Returns per-node 3-run outcome LISTS (index = rep), timings and per-rep
    wall."""
    wt_name = worktree_linux.rsplit("/", 1)[-1]
    db_name = f"saleor_{tid}_{state}"
    setup = deps_install_cmd(worktree_linux, era_key)
    runs = []
    for rep in range(REPS):
        for idx, (_fpath, _nodes) in enumerate(node_groups.items()):
            jname = f"{tid}_{state}_r{rep}_f{idx}"
            runs.append((jname, _nodes))
    # Write per-group node sidecars via a payload file (stdin) + a self-contained
    # bash splitter script (avoid nested-quoting mangling across WSL layers).
    payload = "".join(
        f"@@FILE@@ {jname}\n" + "\n".join(nodes) + "\n" for jname, nodes in runs
    )
    subprocess.run(
        ["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
         f"cat > {worktree_linux}/.wp2_all_nodes.txt"],
        input=payload.encode("utf-8"), capture_output=True, timeout=180,
    )
    splitter = (
        f"cd {worktree_linux}\n"
        "rm -f *.nodes\n"
        'f=""\n'
        "while IFS= read -r line; do\n"
        '  case "$line" in\n'
        "    @@FILE@@*)\n"
        '      f="${line#@@FILE@@ }"\n'
        '      : > "$f.nodes"\n'
        "      ;;\n"
        "    *)\n"
        '      [ -n "$f" ] && printf "%s\\n" "$line" >> "$f.nodes"\n'
        "      ;;\n"
        "  esac\n"
        "done < .wp2_all_nodes.txt\n"
    )
    subprocess.run(
        ["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
         f"cat > {worktree_linux}/.wp2_split.sh"],
        input=splitter.encode("utf-8"), capture_output=True, timeout=180,
    )
    r_split = subprocess.run(
        ["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
         f"mkdir -p {worktree_linux}/logs; rm -f {worktree_linux}/.wp2_timings.txt; "
         f"bash {worktree_linux}/.wp2_split.sh; echo SPLIT_RC=$?; "
         f"ls {worktree_linux}/*.nodes 2>/dev/null | wc -l"],
        capture_output=True, text=True, timeout=180,
    )
    if "SPLIT_RC=0" not in r_split.stdout:
        return {"error": "SIDECAR_SPLIT_FAIL", "outcomes": {}, "failures": {}, "wall_s": None,
                "per_rep_s": [], "timings": [], "stdout_tail": r_split.stdout[-800:] or r_split.stderr[-800:]}
    runs_script_lines = []
    for i, (jname, _nodes) in enumerate(runs):
        logf = f"/workspace/{wt_name}/logs/run_{i}_{jname}.log"
        runs_script_lines.append(
            f"( mapfile -t NODES < /workspace/{wt_name}/{jname}.nodes && "
            "/opt/venv/bin/python -m pytest -p no:cacheprovider -o addopts= "
            "--ds=saleor.tests.settings --disable-socket --reuse-db "
            f"--junitxml /workspace/{wt_name}/{jname}.xml -q "
            f'\"${{NODES[@]}}\" >{logf} 2>&1; echo RUN_{i}_RC=$? >>{logf}; '
            f"echo TIMING {i} $SECONDS >> /workspace/{wt_name}/.wp2_timings.txt )"
        )
    runs_script = " ; ".join(runs_script_lines)
    proc = subprocess.run(
        ["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
         f"cat >> {worktree_linux}/.wp2_runs.sh"],
        input=runs_script.encode("utf-8"), capture_output=True, timeout=120,
    )
    if proc.returncode != 0:
        return {"error": "RUNS_SCRIPT_WRITE_FAIL", "outcomes": {}, "failures": {}, "wall_s": None,
                "per_rep_s": [], "timings": [], "stdout_tail": ""}
    script = (
        "set -e; "
        "uv venv /opt/venv >/dev/null 2>&1 || true; "
        f"{setup} >/tmp/install.log 2>&1 || {{ echo INSTALL_FAIL; tail -120 /tmp/install.log; exit 2; }}; "
        f"{TOOLING_INSTALL} >>/tmp/install.log 2>&1 || {{ echo TOOLING_FAIL; tail -80 /tmp/install.log; exit 2; }}; "
        f"cd /workspace/{wt_name} && bash /workspace/{wt_name}/.wp2_runs.sh; echo ALL_RUNS_DONE"
    )
    t0 = time.monotonic()
    r = wsl_docker(
        [
            "run", "--rm", "--network", "host",
            "-e", f"DATABASE_URL=postgres://saleor:saleor@127.0.0.1:5433/{db_name}",
            "-e", "CACHE_URL=locmem://",
            "-v", f"{worktree_linux}:/workspace/{wt_name}",
            "-v", "wp2-uv-cache:/root/.cache/uv",
            f"wp2-era-{era_key}",
            "bash", "-lc", script,
        ],
        timeout_s=timeout_s,
    )
    wall = round(time.monotonic() - t0, 1)
    if r.returncode != 0 and "INSTALL_FAIL" in r.stdout:
        return {"error": "INSTALL_FAIL", "outcomes": {}, "failures": {}, "wall_s": wall,
                "per_rep_s": [], "timings": [], "stdout_tail": r.stdout[-2000:]}
    timings_txt = wsl(f"cat {worktree_linux}/.wp2_timings.txt 2>/dev/null || echo __NO_TIMING__")
    timings: list[float] = []
    if "__NO_TIMING__" not in timings_txt.stdout[:20]:
        for line in timings_txt.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[0] == "TIMING":
                timings.append(float(parts[2]))
    # timings are cumulative bash $SECONDS; convert to per-run deltas.
    per_run_s: list[float] = []
    prev = 0.0
    for v in timings:
        per_run_s.append(max(0.0, v - prev))
        prev = v
    outcomes: dict[str, list[str]] = {}
    failures: dict[str, str] = {}
    for rep in range(REPS):
        for idx, (_fpath, nodes) in enumerate(node_groups.items()):
            jname = f"{tid}_{state}_r{rep}_f{idx}"
            rr = wsl(f"cat {worktree_linux}/{jname}.xml 2>/dev/null || echo __NO_FILE__")
            if "__NO_FILE__" in rr.stdout[:20]:
                for n in nodes:
                    outcomes.setdefault(n, []).append("missing")
                continue
            try:
                outs, fails = parse_junit_with_failures(rr.stdout)
            except Exception:
                outs, fails = {}, {}
            for n in nodes:
                outcomes.setdefault(n, []).append(outs.get(n, "missing"))
                if n in fails:
                    failures[n] = fails[n]
    per_rep_s: list[float] = []
    n_per_rep = len(node_groups)
    for rep in range(REPS):
        seg = per_run_s[rep * n_per_rep: (rep + 1) * n_per_rep]
        per_rep_s.append(round(sum(seg), 1))
    return {
        "error": None,
        "wall_s": wall,
        "per_rep_s": per_rep_s,
        "per_run_s": per_run_s,
        "outcomes": outcomes,
        "failures": failures,
        "stdout_tail": r.stdout[-2000:],
    }


def drop_task_dbs(tid: str) -> dict:
    short = tid.split("-")[-1][:12]
    results = {}
    for state in ("t", "p"):
        db = f"saleor_{short}_{state}"
        t0 = time.monotonic()
        r = wsl_docker(
            ["exec", "wp2-pg", "psql", "-U", "saleor", "-d", "postgres", "-c",
             f"DROP DATABASE IF EXISTS {db} WITH (FORCE)"],
            timeout_s=120,
        )
        results[state] = {"db": db, "drop_ok": r.returncode == 0, "drop_s": round(time.monotonic() - t0, 2)}
    return results


def remove_worktrees(task_id: str) -> None:
    tid = task_id.split("-")[-1][:12]
    for state in ("t", "p"):
        wt = f"{WSL_WT}/{tid}_{state}"
        wsl(f"git -C {WSL_CACHE} worktree remove --force {wt} 2>/dev/null || rm -rf {wt}")
    wsl(f"git -C {WSL_CACHE} worktree prune 2>/dev/null || true")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--run-label", default="A")
    ap.add_argument("--evidence-root", default=None)
    ap.add_argument("--allow-any-task", action="store_true",
                    help="future-authorization flag; the Phase-A pilot refuses any task "
                         "other than the explicitly selected SMALL task without it")
    ap.add_argument("--dry-run", action="store_true",
                    help="validate wiring only: no docker/WSL execution")
    args = ap.parse_args()

    # Hard safety assertion: Phase-A pilot may ONLY run the explicitly selected
    # SMALL task. Any other task requires an explicit future authorization flag.
    small_pilot_task = "saleor-rc-2d45b76a52f2"
    if args.task != small_pilot_task and not args.allow_any_task:
        raise SystemExit(
            f"Phase-A pilot refuses task {args.task}. Only the explicitly selected "
            f"SMALL pilot task {small_pilot_task} is allowed without "
            "--allow-any-task (future authorization)."
        )

    artifact = json.loads(INVENTORY_ARTIFACT.read_text(encoding="utf-8"))
    row = next(r for r in artifact["tasks"] if r["task_id"] == args.task)
    if not row["oracle_valid"]:
        raise SystemExit("task not oracle-valid; pilot requires oracle-valid ENG task")
    node_ids = row["candidate_node_ids"]
    groups = group_nodes_by_file(node_ids)

    out_root = Path(args.evidence_root) if args.evidence_root else EVIDENCE_ROOT / args.task / args.run_label
    out_root.mkdir(parents=True, exist_ok=True)
    junit_dir = out_root / "junit"
    junit_dir.mkdir(parents=True, exist_ok=True)

    c_free_gib = shutil.disk_usage("C:/").free / (1024 ** 3)
    if c_free_gib < 40.0:
        raise SystemExit(f"C: free {c_free_gib:.1f} GiB < 40 GiB; refusing pilot start")

    preflight = {
        "PRE_PILOT_PREFLIGHT": {
            "task_id": args.task,
            "raw_discovered_nodes": len(node_ids),
            "n_file_groups": len(groups),
            "parent_condition": "parent commit + frozen test patch (TEST_PATCH_APPLIED_ON_PARENT=true)",
            "target_condition": "target commit",
            "repetitions": f"{REPS} parent + {REPS} target",
            "workers": 1,
            "expected_commands": (
                "1 setup container per state; per state "
                f"{REPS} reps x {len(groups)} pytest invocations"
            ),
            "c_free_gib": round(c_free_gib, 1),
            "evidence_path": str(out_root),
            "inventory_sha256": artifact["hashes"]["inventory_sha256"],
        }
    }
    if args.dry_run:
        print(json.dumps(preflight, indent=1))
        print("DRY_RUN_OK: wiring validated; no docker/WSL execution performed.")
        return 0
    print(json.dumps(preflight, indent=1))

    ensure_cache()
    ensure_era_images()
    ensure_postgres()

    mem_before = sample_wsl_mem_gib()
    wt_before = wsl("du -sm /opt/wp2_v2/worktrees 2>/dev/null | cut -f1").stdout.strip()
    disk_before = shutil.disk_usage("C:/").free / (1024 ** 3)

    t_setup0 = time.monotonic()
    wts = ensure_worktrees(args.task, row["parent_commit"], row["target_commit"])
    setup_s = round(time.monotonic() - t_setup0, 1)

    short = args.task.split("-")[-1][:12]
    results = {}
    peak_mem = mem_before
    for state in ("t", "p"):
        t0 = time.monotonic()
        res = run_state(
            era_key=row["era_key"],
            worktree_linux=wts[state],
            tid=short,
            state=state,
            node_groups=groups,
        )
        results[state] = res
        results[state]["total_state_wall_s"] = round(time.monotonic() - t0, 1)
        peak_mem = max(peak_mem, sample_wsl_mem_gib())
        print(f"[{state}] wall={results[state].get('total_state_wall_s')} error={res.get('error')}", flush=True)

    # Q2 classification from per-node 3-run outcome lists
    node_classes: dict[str, str] = {}
    outcome_records: dict[str, dict] = {}
    missing3 = ["missing"] * REPS
    for node in node_ids:
        p_out = results["p"]["outcomes"].get(node, missing3)
        t_out = results["t"]["outcomes"].get(node, missing3)
        cls = classify_p2p_node(list(p_out), list(t_out))
        node_classes[node] = cls
        outcome_records[node] = {
            "parent_outcomes": list(p_out),
            "target_outcomes": list(t_out),
            "class": cls,
            "parent_failure": results["p"]["failures"].get(node, ""),
        }

    counts: dict[str, int] = {}
    for cls in set(node_classes.values()):
        counts[cls] = sum(1 for c in node_classes.values() if c == cls)
    for k in ("STABLE_P2P", "TARGET_BROKEN", "PARENT_BROKEN", "BOTH_FAIL", "FLAKY", "COLLECTION_ERROR"):
        counts.setdefault(k, 0)

    rec = {
        "task_id": args.task,
        "run_label": args.run_label,
        "pilot_version": PILOT_VERSION,
        "era_key": row["era_key"],
        "python_requirement": row["python_requirement"],
        "inventory_sha256": artifact["hashes"]["inventory_sha256"],
        "n_associated_test_files": row["n_associated_unchanged_test_files"],
        "n_discovered_candidate_nodes": row["n_discovered_candidate_nodes"],
        "n_candidate_nodes_executed": len(node_ids),
        "test_patch_applied_on_parent": True,
        "class_counts": counts,
        "n_stable_p2p": counts.get("STABLE_P2P", 0),
        "stable_over_discovered": round(counts.get("STABLE_P2P", 0) / len(node_ids), 4) if node_ids else 0.0,
        "measurements": {
            "setup_env_s": setup_s,
            "target_wall_s": results["t"].get("total_state_wall_s"),
            "parent_wall_s": results["p"].get("total_state_wall_s"),
            "target_per_rep_s": results["t"].get("per_rep_s"),
            "parent_per_rep_s": results["p"].get("per_rep_s"),
            "total_wall_s": round(setup_s + sum(results[s].get("total_state_wall_s", 0) for s in ("t", "p")), 1),
            "peak_wsl_ram_gib": round(peak_mem, 1),
            "wsl_mem_before_gib": round(mem_before, 1),
            "worktrees_mib_before": wt_before,
            "disk_before_c_free_gib": round(disk_before, 1),
            "db_lifecycle": {"target_db": f"saleor_{short}_t", "parent_db": f"saleor_{short}_p"},
        },
        "states": {s: {"error": results[s].get("error"), "wall_s": results[s].get("total_state_wall_s"),
                        "per_rep_s": results[s].get("per_rep_s")} for s in ("t", "p")},
    }

    # persist evidence
    manifest_text = json.dumps(rec, indent=1, ensure_ascii=False)
    (out_root / "manifest.json").write_text(manifest_text, encoding="utf-8")
    (out_root / "node_outcomes.json").write_text(
        json.dumps(outcome_records, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    (out_root / "node_classes.json").write_text(
        json.dumps(node_classes, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    for state in ("t", "p"):
        for rep in range(REPS):
            for idx, (_fpath, _nodes) in enumerate(groups.items()):
                jname = f"{short}_{state}_r{rep}_f{idx}"
                rr = wsl(f"cat {wts[state]}/{jname}.xml 2>/dev/null || echo __NO_FILE__")
                if "__NO_FILE__" not in rr.stdout[:20]:
                    (junit_dir / f"{jname}.xml").write_text(rr.stdout, encoding="utf-8")
        # persist per-run container logs for diagnosis
        logdir = out_root / "logs" / state
        logdir.mkdir(parents=True, exist_ok=True)
        logs = wsl(f"cat {wts[state]}/logs/run_*.log 2>/dev/null || echo __NO_LOG__")
        if "__NO_LOG__" not in logs.stdout[:20]:
            (logdir / "runs_concatenated.log").write_text(logs.stdout, encoding="utf-8")

    # verify evidence: exact 1:1 node <-> record, no missing/duplicate/orphan
    n_expected = len(node_ids)
    rec_keys = set(outcome_records)
    n_missing = sum(1 for n in node_ids if n not in rec_keys)
    n_orphan = len(rec_keys - set(node_ids))
    n_dupes = len(node_ids) - len(set(node_ids))
    evidence_ok = (
        n_missing == 0
        and n_orphan == 0
        and n_dupes == 0
        and all(s.get("error") is None for s in results.values())
    )
    rec["evidence_integrity"] = {
        "n_expected": n_expected,
        "n_records": len(outcome_records),
        "n_missing_nodes": n_missing,
        "n_duplicate_nodes": n_dupes,
        "n_orphan_nodes": n_orphan,
        "ok": evidence_ok,
    }
    (out_root / "manifest.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")

    # cleanup
    db_drop = drop_task_dbs(short)
    rec["measurements"]["db_lifecycle"]["drop"] = db_drop
    remove_worktrees(args.task)
    wt_after = wsl("du -sm /opt/wp2_v2/worktrees 2>/dev/null | cut -f1").stdout.strip()
    disk_after = shutil.disk_usage("C:/").free / (1024 ** 3)
    rec["measurements"]["worktrees_mib_after"] = wt_after
    rec["measurements"]["disk_after_c_free_gib"] = round(disk_after, 1)
    rec["measurements"]["reclaimed_disk_gib"] = round(disk_after - disk_before, 2)
    (out_root / "manifest.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")

    print(
        json.dumps(
            {k: rec[k] for k in ("class_counts", "n_stable_p2p",
                                 "stable_over_discovered", "measurements",
                                 "evidence_integrity")},
            indent=1,
        )
    )
    print("evidence:", out_root)
    return 0 if evidence_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
