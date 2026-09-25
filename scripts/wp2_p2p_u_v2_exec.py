#!/usr/bin/env python3
"""WP-2 P2P-U V2 ENG execution runner (Mission-09) - ZERO API.

Executes the frozen P2P-U V2 rule on ONE oracle-valid ENG task for ONE cap
(200 primary or 400 sensitivity), workers=1, OUTCOME-BLIND membership from the
frozen membership artifact.

Frozen execution semantics (Mission-09 sections 11-12):
- PARENT: parent commit + SAME frozen test patch as Linux V2 F2P
  (TEST_PATCH_APPLIED_ON_PARENT=true). TARGET: target commit.
- Repetitions: 3 parent + 3 target complete repetitions, NO early stopping.
- Workers = 1 throughout. No parallelism/performance gate. No .wslconfig change.
- Invocation design: prefer ONE pytest invocation per state-repetition with
  explicit node IDs -> nominally 6 pytest invocations/task/cap. If command-line
  argument-length limits require chunking, chunk deterministically with
  identical chunks across states/repetitions and record chunk counts.
- cap200 and cap400 are executed INDEPENDENTLY (never infer one from the other).
- Unique mutable state: unique DB names, worktrees, JUnit/output paths.
- Node classification uses the frozen 6-class taxonomy precedence
  (FLAKY > COLLECTION_ERROR > STABLE_P2P > TARGET_BROKEN > PARENT_BROKEN >
  BOTH_FAIL); only STABLE_P2P nodes become the frozen preservation set.
- Evidence integrity verified before cleanup; worktrees removed + DBs dropped
  after verification.

Usage:
    python scripts/wp2_p2p_u_v2_exec.py --task saleor-rc-... --cap 200 \
        --run-label A [--evidence-root ...] [--dry-run]
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
from benchmark.wp2.p2p_inventory_dev_v1 import classify_p2p_node  # noqa: E402
from benchmark.wp2.p2p_u_v2 import (  # noqa: E402
    P2P_U_V2_VERSION,
    file_path_of,
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
MEMBERSHIP_ARTIFACT = PROJECT / "research" / "wp2" / "wp2_p2p_u_v2_membership_2026-09-25.json"
RULE_ARTIFACT = PROJECT / "research" / "wp2" / "wp2_p2p_u_v2_rule_freeze_2026-09-25.json"
EVIDENCE_ROOT = PROJECT / "research" / "wp2" / "p2p_u_v2_eng_2026-09-25"

P2P_U_V2_EXEC_VERSION = "p2p-u-v2-eng-exec-2026-09-25"
REPS = 3
CHUNK_ARG_CHARS = 200000  # far below WSL ARG_MAX (2,097,152); chunk guard


def git_linux(workdir: str, *args: str) -> subprocess.CompletedProcess[str]:
    quoted = " ".join(f"'{a}'" for a in args)
    return wsl(f"git -C {workdir} {quoted}")


def ensure_postgres_running() -> None:
    """Start the wp2-pg container if it exists but is stopped; create via the
    shared helper only when absent. Guards against a name collision when the
    container exits between runs (WSL idle shutdown)."""
    r = wsl("docker ps -a --filter 'name=^wp2-pg$' --format '{{.Names}}'")
    if "wp2-pg" in r.stdout:
        wsl_docker(["start", "wp2-pg"], timeout_s=120)
        time.sleep(3)
        return
    ensure_postgres()


def deterministic_chunks(node_ids: list[str], max_chars: int = CHUNK_ARG_CHARS) -> list[list[str]]:
    """Deterministic chunking preserving the frozen order. Identical chunk
    membership/order across states and repetitions."""
    chunks: list[list[str]] = []
    current: list[str] = []
    chars = 0
    for n in node_ids:
        if current and chars + len(n) + 1 > max_chars:
            chunks.append(current)
            current = []
            chars = 0
        current.append(n)
        chars += len(n) + 1
    if current:
        chunks.append(current)
    return chunks


def ensure_worktrees(task_id: str, parent: str, target: str, cap: int) -> dict:
    tid = task_id.split("-")[-1][:12]
    wt_t = f"{WSL_WT}/{tid}_c{cap}_t"
    wt_p = f"{WSL_WT}/{tid}_c{cap}_p"
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


def run_state(
    *,
    era_key: str,
    worktree_linux: str,
    tid: str,
    cap: int,
    state: str,
    chunks: list[list[str]],
    timeout_s: int = 28800,
) -> dict:
    """One container per state: install deps once, then run each chunk 3x with
    per-run JUnit (frozen V2 invocation design). Node IDs passed via explicit
    command-line args (within ARG_MAX) or sidecar files when a chunk would be
    too large. Returns per-node 3-run outcome LISTS and timings."""
    wt_name = worktree_linux.rsplit("/", 1)[-1]
    db_name = f"saleor_{tid}_c{cap}_{state}"
    setup = deps_install_cmd(worktree_linux, era_key)
    runs = []
    for rep in range(REPS):
        for idx, _chunk in enumerate(chunks):
            jname = f"{tid}_c{cap}_{state}_r{rep}_c{idx}"
            runs.append((jname, _chunk))
    # Write node lists as sidecar files inside the mounted worktree.
    for jname, nodes in runs:
        payload = "\n".join(nodes) + "\n"
        subprocess.run(
            ["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
             f"cat > {worktree_linux}/{jname}.nodes"],
            input=payload.encode("utf-8"), capture_output=True, timeout=180,
        )
    wsl(f"mkdir -p {worktree_linux}/logs; rm -f {worktree_linux}/.wp2_runs.sh {worktree_linux}/.wp2_timings.txt")
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
         f"cat > {worktree_linux}/.wp2_runs.sh"],
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
    test_container_name = f"wp2-test-{tid}-c{cap}-{state}"
    r = wsl_docker(
        [
            "run", "--rm", "--network", "host",
            "--name", test_container_name,
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
    per_run_s: list[float] = []
    prev = 0.0
    for v in timings:
        per_run_s.append(max(0.0, v - prev))
        prev = v
    outcomes: dict[str, list[str]] = {}
    failures: dict[str, str] = {}
    for rep in range(REPS):
        for idx in range(len(chunks)):
            jname = f"{tid}_c{cap}_{state}_r{rep}_c{idx}"
            rr = wsl(f"cat {worktree_linux}/{jname}.xml 2>/dev/null || echo __NO_FILE__")
            if "__NO_FILE__" in rr.stdout[:20]:
                for n in chunks[idx]:
                    outcomes.setdefault(n, []).append("missing")
                continue
            try:
                outs, fails = parse_junit_with_failures(rr.stdout)
            except Exception:
                outs, fails = {}, {}
            for n in chunks[idx]:
                outcomes.setdefault(n, []).append(outs.get(n, "missing"))
                if n in fails:
                    failures[n] = fails[n]
    per_rep_s: list[float] = []
    n_per_rep = len(chunks)
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


def drop_task_dbs(tid: str, cap: int) -> dict:
    short = tid.split("-")[-1][:12]
    results = {}
    for state in ("t", "p"):
        db = f"saleor_{short}_c{cap}_{state}"
        t0 = time.monotonic()
        r = wsl_docker(
            ["exec", "wp2-pg", "psql", "-U", "saleor", "-d", "postgres", "-c",
             f"DROP DATABASE IF EXISTS {db} WITH (FORCE)"],
            timeout_s=120,
        )
        results[state] = {"db": db, "drop_ok": r.returncode == 0, "drop_s": round(time.monotonic() - t0, 2)}
    return results


def remove_worktrees(task_id: str, cap: int) -> None:
    tid = task_id.split("-")[-1][:12]
    for state in ("t", "p"):
        wt = f"{WSL_WT}/{tid}_c{cap}_{state}"
        wsl(f"git -C {WSL_CACHE} worktree remove --force {wt} 2>/dev/null || rm -rf {wt}")
    wsl(f"git -C {WSL_CACHE} worktree prune 2>/dev/null || true")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--cap", type=int, required=True, choices=(200, 400))
    ap.add_argument("--run-label", default="A")
    ap.add_argument("--evidence-root", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not INVENTORY_ARTIFACT.exists() or not MEMBERSHIP_ARTIFACT.exists():
        print("missing frozen artifact(s)")
        return 2
    inventory = json.loads(INVENTORY_ARTIFACT.read_text(encoding="utf-8"))
    membership = json.loads(MEMBERSHIP_ARTIFACT.read_text(encoding="utf-8"))

    row = next((r for r in inventory["tasks"] if r["task_id"] == args.task), None)
    if row is None:
        print("task not in DEV inventory")
        return 2
    if not row["oracle_valid"]:
        print("task not oracle-valid; execution refused")
        return 2
    if row["split_role"] != "DEV_TRAIN_ENG":
        print("task not ENG; Mission-09 executes ENG only")
        return 2
    if args.task not in membership["tasks"]:
        print("task not in P2P-U V2 membership")
        return 2
    sel = membership["tasks"][args.task]
    node_ids = list(sel["cap200_node_ids"] if args.cap == 200 else sel["cap400_node_ids"])
    if not node_ids:
        print(f"P2P-U UNDEFINED for {args.task}: zero candidate nodes; no execution.")
        return 0

    # Verify selected node IDs all belong to the frozen Mission-08 raw inventory.
    raw = set(row["candidate_node_ids"] or [])
    foreign = [n for n in node_ids if n not in raw]
    if foreign:
        print(f"FATAL: {len(foreign)} selected nodes outside frozen raw inventory")
        return 2

    # Chunk deterministically (identical across states/repetitions).
    chunks = deterministic_chunks(node_ids)

    if args.evidence_root:
        out_root = Path(args.evidence_root)
    else:
        out_root = EVIDENCE_ROOT / args.task / f"cap{args.cap}" / args.run_label
    out_root.mkdir(parents=True, exist_ok=True)
    junit_dir = out_root / "junit"
    junit_dir.mkdir(parents=True, exist_ok=True)

    c_free_gib = shutil.disk_usage("C:/").free / (1024**3)
    if c_free_gib < 32.0:
        print(f"HARD STOP: C: free {c_free_gib:.1f} GiB < 32 GiB")
        return 3
    preflight = {
        "PRE_EXECUTION_PREFLIGHT": {
            "task_id": args.task,
            "cap": args.cap,
            "era_key": row["era_key"],
            "n_selected_nodes": len(node_ids),
            "n_chunks": len(chunks),
            "n_invocations": len(chunks) * REPS,
            "invocations_per_state": len(chunks) * REPS,
            "parent_condition": "parent commit + frozen test patch (TEST_PATCH_APPLIED_ON_PARENT=true)",
            "target_condition": "target commit",
            "repetitions": f"{REPS} parent + {REPS} target",
            "workers": 1,
            "chunk_arg_chars_max": CHUNK_ARG_CHARS,
            "c_free_gib": round(c_free_gib, 1),
            "evidence_path": str(out_root),
            "membership_sha256": membership["hashes"]["artifact_sha256"],
            "rule_sha256": membership["hashes"]["rule_sha256"],
            "inventory_sha256": inventory["hashes"]["inventory_sha256"],
        }
    }
    if args.dry_run:
        print(json.dumps(preflight, indent=1))
        print("DRY_RUN_OK: wiring validated; no docker/WSL execution performed.")
        return 0
    print(json.dumps(preflight, indent=1))

    ensure_cache()
    ensure_era_images()
    ensure_postgres_running()

    # Resource sampler (separate process, 5 s interval). It auto-discovers the
    # running wp2-test-* container plus wp2-pg for per-container metrics.
    import subprocess as _sp

    sample_file = out_root / "resource_samples.jsonl"
    stop_file = out_root / ".sampler_stop"
    if stop_file.exists():
        stop_file.unlink()
    sampler_proc = _sp.Popen(
        [sys.executable, str(PROJECT / "scripts" / "wp2_resource_sampler.py"),
         "--run", "--out", str(sample_file), "--stop-file", str(stop_file)],
        stdout=_sp.PIPE, stderr=_sp.STDOUT, text=True,
    )

    disk_before = shutil.disk_usage("C:/").free / (1024**3)
    wt_before = wsl("du -sm /opt/wp2_v2/worktrees 2>/dev/null | cut -f1").stdout.strip()

    t_setup0 = time.monotonic()
    wts = ensure_worktrees(args.task, row["parent_commit"], row["target_commit"], args.cap)
    setup_s = round(time.monotonic() - t_setup0, 1)

    short = args.task.split("-")[-1][:12]
    results = {}
    for state in ("t", "p"):
        t0 = time.monotonic()
        res = run_state(
            era_key=row["era_key"],
            worktree_linux=wts[state],
            tid=short,
            cap=args.cap,
            state=state,
            chunks=chunks,
        )
        results[state] = res
        results[state]["total_state_wall_s"] = round(time.monotonic() - t0, 1)
        print(f"[{state}] wall={results[state].get('total_state_wall_s')} error={res.get('error')}", flush=True)

    # Stop sampler.
    stop_file.touch()
    sampler_proc.wait(timeout=60)
    n_samples = sum(1 for _ in sample_file.open(encoding="utf-8")) if sample_file.exists() else 0

    # Classification (frozen 6-class precedence).
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
            "proximity": sel["proximity_by_file"].get(file_path_of(node), 0),
            "proximal_distal": "PROXIMAL"
            if sel["proximity_by_file"].get(file_path_of(node), 0) >= 2
            else "DISTAL",
        }

    counts: dict[str, int] = {}
    for cls in set(node_classes.values()):
        counts[cls] = sum(1 for c in node_classes.values() if c == cls)
    for k in ("STABLE_P2P", "TARGET_BROKEN", "PARENT_BROKEN", "BOTH_FAIL", "FLAKY", "COLLECTION_ERROR"):
        counts.setdefault(k, 0)

    stable = sorted(n for n, c in node_classes.items() if c == "STABLE_P2P")
    rec = {
        "artifact": "wp2_p2p_u_v2_eng_exec",
        "exec_version": P2P_U_V2_EXEC_VERSION,
        "task_id": args.task,
        "split_role": row["split_role"],
        "era_key": row["era_key"],
        "cap": args.cap,
        "run_label": args.run_label,
        "rule_version": P2P_U_V2_VERSION,
        "membership_sha256": membership["hashes"]["artifact_sha256"],
        "rule_sha256": membership["hashes"]["rule_sha256"],
        "inventory_sha256": inventory["hashes"]["inventory_sha256"],
        "test_patch_applied_on_parent": True,
        "workers": 1,
        "n_selected_nodes": len(node_ids),
        "n_chunks": len(chunks),
        "n_pytest_invocations": len(chunks) * REPS * 2,
        "class_counts": counts,
        "n_stable_p2p": counts["STABLE_P2P"],
        "stable_over_selected": round(counts["STABLE_P2P"] / len(node_ids), 4) if node_ids else 0.0,
        "preservation_set_sha256": _sha256_json(sorted(stable)),
        "n_preservation_files": len({file_path_of(n) for n in stable}),
        "composition": {
            "selected_proximal": sum(1 for n in node_ids if sel["proximity_by_file"].get(file_path_of(n), 0) >= 2),
            "selected_distal": sum(1 for n in node_ids if sel["proximity_by_file"].get(file_path_of(n), 0) < 2),
            "stable_proximal": sum(1 for n in stable if sel["proximity_by_file"].get(file_path_of(n), 0) >= 2),
            "stable_distal": sum(1 for n in stable if sel["proximity_by_file"].get(file_path_of(n), 0) < 2),
        },
        "measurements": {
            "setup_s": setup_s,
            "target_wall_s": results["t"].get("total_state_wall_s"),
            "parent_wall_s": results["p"].get("total_state_wall_s"),
            "target_per_rep_s": results["t"].get("per_rep_s"),
            "parent_per_rep_s": results["p"].get("per_rep_s"),
            "total_wall_s": round(setup_s + sum(results[s].get("total_state_wall_s", 0) for s in ("t", "p")), 1),
            "n_resource_samples": n_samples,
            "disk_before_c_free_gib": round(disk_before, 1),
            "worktrees_mib_before": wt_before,
        },
        "states": {s: {"error": results[s].get("error"), "wall_s": results[s].get("total_state_wall_s"),
                        "per_rep_s": results[s].get("per_rep_s")} for s in ("t", "p")},
    }

    # Persist evidence.
    (out_root / "manifest.json").write_text(
        json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    (out_root / "node_outcomes.json").write_text(
        json.dumps(outcome_records, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    (out_root / "node_classes.json").write_text(
        json.dumps(node_classes, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    for state in ("t", "p"):
        for rep in range(REPS):
            for idx in range(len(chunks)):
                jname = f"{short}_c{args.cap}_{state}_r{rep}_c{idx}"
                rr = wsl(f"cat {wts[state]}/{jname}.xml 2>/dev/null || echo __NO_FILE__")
                if "__NO_FILE__" not in rr.stdout[:20]:
                    (junit_dir / f"{jname}.xml").write_text(rr.stdout, encoding="utf-8")
        logdir = out_root / "logs" / state
        logdir.mkdir(parents=True, exist_ok=True)
        logs = wsl(f"cat {wts[state]}/logs/run_*.log 2>/dev/null || echo __NO_LOG__")
        if "__NO_LOG__" not in logs.stdout[:20]:
            (logdir / "runs_concatenated.log").write_text(logs.stdout, encoding="utf-8")

    # Evidence integrity verification.
    n_expected = len(node_ids)
    rec_keys = set(outcome_records)
    n_missing = sum(1 for n in node_ids if n not in rec_keys)
    n_orphan = len(rec_keys - set(node_ids))
    n_dupes = len(node_ids) - len(set(node_ids))
    junit_refs_ok = all(
        (junit_dir / f"{short}_c{args.cap}_{state}_r{rep}_c{idx}.xml").exists()
        for state in ("t", "p") for rep in range(REPS) for idx in range(len(chunks))
    )
    evidence_ok = (
        n_missing == 0 and n_orphan == 0 and n_dupes == 0 and junit_refs_ok
        and all(s.get("error") is None for s in results.values())
    )
    rec["evidence_integrity"] = {
        "n_expected": n_expected,
        "n_records": len(outcome_records),
        "n_missing_nodes": n_missing,
        "n_duplicate_nodes": n_dupes,
        "n_orphan_nodes": n_orphan,
        "junit_refs_ok": junit_refs_ok,
        "ok": evidence_ok,
    }
    (out_root / "manifest.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")

    # Cleanup.
    db_drop = drop_task_dbs(short, args.cap)
    rec["measurements"]["db_lifecycle"] = {"drop": db_drop}
    remove_worktrees(args.task, args.cap)
    wt_after = wsl("du -sm /opt/wp2_v2/worktrees 2>/dev/null | cut -f1").stdout.strip()
    disk_after = shutil.disk_usage("C:/").free / (1024**3)
    rec["measurements"]["worktrees_mib_after"] = wt_after
    rec["measurements"]["disk_after_c_free_gib"] = round(disk_after, 1)
    rec["measurements"]["reclaimed_disk_gib"] = round(disk_after - disk_before, 2)
    (out_root / "manifest.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(
        {k: rec[k] for k in ("class_counts", "n_stable_p2p", "stable_over_selected",
                             "preservation_set_sha256", "composition", "measurements",
                             "evidence_integrity")}, indent=1))
    print("evidence:", out_root)
    return 0 if evidence_ok else 2


def _sha256_json(payload: object) -> str:
    import hashlib

    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
