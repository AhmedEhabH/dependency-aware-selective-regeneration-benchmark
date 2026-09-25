#!/usr/bin/env python3
"""WP-2 DEV unchanged-test P2P node discovery (Mission-08) - ZERO API.

Deterministic node discovery for the 47 oracle-valid DEV tasks: run
``pytest --collect-only`` at the TARGET state inside the era container for the
associated UNCHANGED test files (P2P Preservation Rule V1, deterministic
discovery). Outcome inspection is FORBIDDEN here: no stability filtering, no
classification; candidate node IDs are recorded as discovered.

Resumable / chunked (--start --max-tasks), mirrors the C4 sweep pattern. Writes
``dev_unchanged_p2p_node_discovery_2026-09-25.jsonl`` plus a progress file.
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

RUN_ROOT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23"
INVENTORY_ARTIFACT = PROJECT / "research" / "wp2" / "wp2_dev_unchanged_p2p_candidate_inventory_v1_2026-09-25.json"
DISCOVERY_JSONL = RUN_ROOT / "dev_unchanged_p2p_node_discovery_2026-09-25.jsonl"
DISCOVERY_PROGRESS = RUN_ROOT / "dev_p2p_node_discovery_progress_2026-09-25.json"

DISCOVERY_VERSION = "dev-p2p-node-discovery-v1-2026-09-25"


def git_linux(workdir: str, *args: str) -> subprocess.CompletedProcess[str]:
    quoted = " ".join(f"'{a}'" for a in args)
    return wsl(f"git -C {workdir} {quoted}")


def remove_worktree_linux(task_id: str) -> None:
    """Q9: remove a completed discovery worktree safely and prune metadata."""
    tid = task_id.split("-")[-1][:12]
    wt_t = f"{WSL_WT}/{tid}_t"
    wsl(f"git -C {WSL_CACHE} worktree remove --force {wt_t} 2>/dev/null || rm -rf {wt_t}")
    wsl(f"git -C {WSL_CACHE} worktree prune 2>/dev/null || true")


def storage_gb() -> dict:
    """Monitor C: and WSL ext4 free space (GiB, PowerShell /1GB semantics)."""
    import shutil

    c_free = shutil.disk_usage("C:/").free / (1024 ** 3)
    r = wsl("df -BG /")
    tail = [ln for ln in (r.stdout or "").splitlines() if ln.strip()]
    wsl_line = tail[-1].split() if tail else []
    avail = wsl_line[3] if len(wsl_line) >= 4 else "?"
    return {"c_free_gib": round(c_free, 1), "wsl_avail": avail}


def ensure_target_worktree(task_id: str, target: str) -> str:
    tid = task_id.split("-")[-1][:12]
    wt_t = f"{WSL_WT}/{tid}_t"
    wsl(f"mkdir -p {WSL_WT}")
    r = wsl(f"test -e {wt_t}/.git && echo OK || echo MISSING")
    if "OK" not in r.stdout:
        r = git_linux(WSL_CACHE, "worktree", "add", "--detach", wt_t, target)
        if r.returncode != 0:
            raise SystemExit(f"[wt] target add FAILED: {r.stderr[-1200:]}")
    return wt_t


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--max-tasks", type=int, default=4)
    ap.add_argument("--task", default=None)
    ap.add_argument("--force", action="store_true",
                    help="re-run discovery even if a completed record exists (determinism check)")
    args = ap.parse_args()

    artifact = json.loads(INVENTORY_ARTIFACT.read_text(encoding="utf-8"))
    if args.task or args.force:
        oracle_tasks = [r for r in artifact["tasks"] if r["oracle_valid"]]
    else:
        oracle_tasks = [
            r for r in artifact["tasks"]
            if r["oracle_valid"] and r["node_discovery_status"] == "PENDING"
        ]
    oracle_tasks.sort(key=lambda r: r["task_id"])
    print(f"[discovery] {len(oracle_tasks)} oracle-valid tasks in scope", flush=True)

    ensure_cache()
    ensure_era_images()
    ensure_postgres()

    done: dict[str, dict] = {}
    if DISCOVERY_JSONL.exists():
        for line in DISCOVERY_JSONL.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                done[rec["task_id"]] = rec

    processed = 0
    for idx, row in enumerate(oracle_tasks):
        if idx < args.start:
            continue
        tid = row["task_id"]
        if tid in done and done[tid].get("error") is None and not args.force:
            continue
        if args.task and tid != args.task:
            continue
        if processed >= args.max_tasks:
            break
        t0 = time.monotonic()
        print(
            f"[discovery] {idx+1}/{len(oracle_tasks)} {tid} era={row['era_key']} "
            f"files={row['n_associated_unchanged_test_files']}",
            flush=True,
        )
        rec = {
            "task_id": tid,
            "era_key": row["era_key"],
            "target_commit": row["target_commit"],
            "discovery_version": DISCOVERY_VERSION,
            "discovery_wall_s": None,
            "error": "INTERNAL",
            "candidate_node_ids_before_cap": [],
            "n_associated_files": row["n_associated_unchanged_test_files"],
        }
        try:
            wt_t = ensure_target_worktree(tid, row["target_commit"])
            all_associated = row["associated_unchanged_test_files"]
            # pytest collect-only enumerates nodes ONLY from .py test modules.
            # Cassette/fixture data files (incl. names containing [] parametrization
            # markers) are test-support and MUST NOT be passed as collect args --
            # pytest ERRORS the whole session on such paths. Association is
            # unaffected; this is the deterministic node-discovery mechanism.
            collect_files = [
                f for f in all_associated
                if f.endswith(".py")
                and "[" not in f and "]" not in f
                and not f.endswith("__init__.py")
                and not f.endswith("conftest.py")
            ]
            n_excluded = len(all_associated) - len(collect_files)
            files = collect_files
            if n_excluded:
                rec["n_files_excluded_from_collect_args"] = n_excluded
                rec["exclusion_reason"] = "non-py test-support or []-parametrization path (pytest cannot collect)"
            wt_name = wt_t.rsplit("/", 1)[-1]
            # Pass the (possibly >32K char) file list via a sidecar file in the
            # worktree; Windows command-line length limits forbid argv passing.
            proc = subprocess.run(
                ["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
                 f"cat > {wt_t}/.wp2_discovery_files.txt"],
                input=("\n".join(files) + "\n").encode("utf-8"),
                capture_output=True,
                timeout=120,
            )
            if proc.returncode != 0:
                raise RuntimeError(f"files sidecar write failed: {proc.stderr[-500:]}")
            # verify sidecar content (determinism/evidence: files actually used)
            chk = wsl(f"wc -l < {wt_t}/.wp2_discovery_files.txt 2>/dev/null || echo 0")
            n_sidecar = int((chk.stdout or "0").strip().split()[0])
            if n_sidecar != len(files):
                rec["sidecar_warning"] = f"sidecar has {n_sidecar} lines, expected {len(files)}"
                print(f"[discovery] WARNING {tid}: sidecar {n_sidecar} != {len(files)}", flush=True)
            setup = deps_install_cmd(wt_t, row["era_key"])
            # Run the collect via a SCRIPT FILE (not `bash -lc "<long string>"`):
            # inline mapfile/readarray through the WSL->docker->bash argv layer is
            # unreliable (silently reads 0 lines). A script file is deterministic.
            script = (
                "#!/usr/bin/env bash\n"
                "set -e\n"
                "uv venv /opt/venv >/dev/null 2>&1 || true\n"
                f"{setup} >/tmp/install.log 2>&1 || "
                "{ echo INSTALL_FAIL; tail -120 /tmp/install.log; exit 2; }\n"
                f"{TOOLING_INSTALL} >>/tmp/install.log 2>&1 || "
                "{ echo TOOLING_FAIL; tail -80 /tmp/install.log; exit 2; }\n"
                f"cd /workspace/{wt_name}\n"
                f"mapfile -t FILES < /workspace/{wt_name}/.wp2_discovery_files.txt\n"
                "rc=0\n"
                "/opt/venv/bin/python -m pytest -p no:cacheprovider -o addopts= "
                "--ds=saleor.tests.settings --collect-only -q "
                '"${FILES[@]}" >/tmp/collect.log 2>&1 || rc=$?\n'
                "grep -E '::' /tmp/collect.log | grep -v '^=' | sort -u > "
                f"/workspace/{wt_name}/.wp2_discovery_nodes.txt\n"
                "cp /tmp/collect.log /workspace/"
                f"{wt_name}/.wp2_discovery_collect.log 2>/dev/null || true\n"
                "echo COLLECT_RC=$rc\n"
                f"wc -l /workspace/{wt_name}/.wp2_discovery_nodes.txt\n"
            )
            subprocess.run(
                ["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc",
                 f"cat > {wt_t}/.wp2_discover.sh"],
                input=script.encode("utf-8"), capture_output=True, timeout=120,
            )
            r = wsl_docker(
                [
                    "run", "--rm", "--network", "host",
                    "-e", "DATABASE_URL=postgres://saleor:saleor@127.0.0.1:5433/saleor",
                    "-e", "CACHE_URL=locmem://",
                    "-v", f"{wt_t}:/workspace/{wt_name}",
                    "-v", "wp2-uv-cache:/root/.cache/uv",
                    f"wp2-era-{row['era_key']}",
                    "bash", f"/workspace/{wt_name}/.wp2_discover.sh",
                ],
                timeout_s=3600,
            )
            if r.returncode != 0 and "INSTALL_FAIL" in r.stdout:
                rec["error"] = "INSTALL_FAIL"
                rec["stdout_tail"] = r.stdout[-2000:]
            else:
                nodes = wsl(f"cat {wt_t}/.wp2_discovery_nodes.txt 2>/dev/null || echo __NO_FILE__")
                if "__NO_FILE__" in nodes.stdout[:20]:
                    rec["error"] = "NO_NODES_FILE"
                    rec["stdout_tail"] = r.stdout[-2000:]
                else:
                    rec["error"] = None
                    rec["candidate_node_ids_before_cap"] = sorted(
                        line.strip() for line in nodes.stdout.splitlines() if line.strip()
                    )
                if rec.get("error") or not rec["candidate_node_ids_before_cap"]:
                    clog = wsl(f"tail -60 {wt_t}/.wp2_discovery_collect.log 2>/dev/null || echo __NO_LOG__")
                    rec["collect_log_tail"] = (
                        clog.stdout[-3000:] if "__NO_LOG__" not in clog.stdout[:20] else ""
                    )
            rec["discovery_wall_s"] = round(time.monotonic() - t0, 1)
            rec["returncode"] = r.returncode
        except Exception as exc:
            rec["error"] = f"{type(exc).__name__}: {exc}"
            rec["discovery_wall_s"] = round(time.monotonic() - t0, 1)
        with open(DISCOVERY_JSONL, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        done[tid] = rec
        processed += 1
        print(
            "  -> "
            f"n_nodes={len(rec['candidate_node_ids_before_cap'])} "
            f"error={rec['error']} wall={rec['discovery_wall_s']}s",
            flush=True,
        )
        # Q9: clean completed discovery worktree immediately after persistence.
        remove_worktree_linux(tid)
        print("  -> storage:", storage_gb(), flush=True)
    summary = {
        "artifact": "wp2_dev_p2p_node_discovery_progress",
        "date": "2026-09-25",
        "version": DISCOVERY_VERSION,
        "completed": len(done),
        "pending": len(oracle_tasks) - len(done),
        "completed_with_error": sum(1 for v in done.values() if v.get("error") is not None),
    }
    DISCOVERY_PROGRESS.write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[discovery] chunk complete: {processed} processed; {len(done)} total", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
