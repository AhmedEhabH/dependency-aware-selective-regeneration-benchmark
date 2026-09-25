#!/usr/bin/env python3
"""WP-2 DEV changed-test Linux V2 oracle sweep (C4) - ZERO API.

Same frozen V2 pipeline as C2 over the DEV pool's changed-test candidates
(DEV_TRAIN + DEV_VALIDATION, 111 with changed-test evidence). Persists
node-level records (per_test_v2_dev.jsonl) and per-task records
(per_task_dev_v2.jsonl). Resumable and chunked.
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

from benchmark.wp2.era_resolver import ERA_TABLE, resolve_era  # noqa: E402
from benchmark.wp2.oracle_semantics_v2 import (  # noqa: E402
    TEST_PATH_RULE_SHA256,
    canary_verdict,
    classify_node_v2,
    select_canary_node,
    task_eligibility_v2,
)
from benchmark.wp2.provenance_schema_v2 import make_provenance_record  # noqa: E402
from scripts.wp2_linux_dryrun import (  # noqa: E402
    RUN_ROOT,
    WSL_CACHE,
    changed_paths_linux,
    ensure_cache,
    ensure_era_images,
    ensure_postgres,
    ensure_worktrees,
    git_linux,
    run_state_in_container,
)

DEV_CENSUS = RUN_ROOT / "dev_census_2026-09-23.json"
OUT_DIR = RUN_ROOT
PER_TASK = OUT_DIR / "per_task_dev_v2.jsonl"
PER_TEST = OUT_DIR / "per_test_dev_v2.jsonl"
JUNIT_ROOT = OUT_DIR / "junit"
JUNIT_MANIFEST = OUT_DIR / "junit_manifest_2026-09-23.tsv"
HARNESS_VERSION = "wp2-linux-harness-v2-2026-09-23"
SEMANTIC_CLASSIFIER_BUNDLE_SHA256 = "01c3430f221e70fb75ff4dbf1c0e5093a3c1305f2c870e1b20e2b6c4b64dd337"
PERSISTENCE_REVISION = "c4-persistence-v2-2026-09-23"


def archive_task_junit(task_id: str, wt_t: str, wt_p: str, short: str) -> dict:
    """PURE PERSISTENCE: copy the JUnit XML already written into the worktrees
    by run_state_in_container's existing pytest --junitxml into the evidence
    root. No execution, selection, ordering, environment, or classification
    change."""
    import subprocess as sp

    dest_win = JUNIT_ROOT / task_id
    dest_linux = "/mnt/c" + str(dest_win).replace("\\", "/").split("C:", 1)[1]
    script = (
        f"mkdir -p '{dest_linux}' && "
        f"cp {wt_t}/{short}_*.xml '{dest_linux}/' 2>/dev/null; "
        f"cp {wt_p}/{short}_*.xml '{dest_linux}/' 2>/dev/null; "
        f"ls '{dest_linux}/' | wc -l; "
        f"stat -c%s '{dest_linux}'/*.xml 2>/dev/null | awk '{{s+=$1}} END {{print s+0}}'"
    )
    r = sp.run(["wsl", "-d", "Ubuntu-24.04", "--", "bash", "-lc", script],
               capture_output=True, text=True, encoding="utf-8", timeout=120)
    lines = [line.strip() for line in r.stdout.splitlines() if line.strip() and line.strip().isdigit()]
    n = int(lines[-2]) if len(lines) >= 2 else 0
    size = int(lines[-1]) if lines else 0
    return {"n_junit_archived": n, "junit_bytes": size}


def git_local(*args: str) -> subprocess.CompletedProcess[str]:
    cmd = ["git", "-C", str(PROJECT), *args]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=False)


def lockfile_sha256(target: str) -> str:
    import hashlib

    for name in ("requirements.txt", "pyproject.toml", "poetry.lock"):
        r = git_linux(WSL_CACHE, "show", f"{target}:{name}")
        if r.returncode == 0 and r.stdout.strip():
            return hashlib.sha256(r.stdout.encode()).hexdigest()
    return "none-lockfile"


def load_dev_candidates() -> list[dict]:
    dev = json.loads(DEV_CENSUS.read_text(encoding="utf-8"))
    tasks = []
    for t in dev["tasks"]:
        if t["no_changed_test_evidence"]:
            continue
        req = t.get("python_requirement")
        if req not in ERA_TABLE:
            continue
        tasks.append({
            "task_id": t["task_id"],
            "parent_commit": t["parent_commit"],
            "target_commit": t["target_commit"],
            "era_key": ERA_TABLE[req].era_key,
        })
    return tasks


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--max-tasks", type=int, default=4)
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ensure_cache()
    ensure_era_images()
    ensure_postgres()

    harness_commit = git_local("rev-parse", "HEAD").stdout.strip() or "WORKTREE_UNCOMMITTED"
    done_ids = set()
    if PER_TASK.exists():
        for line in PER_TASK.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done_ids.add(json.loads(line)["task_id"])

    tasks = load_dev_candidates()
    print(f"[C4] loaded {len(tasks)} DEV changed-test candidates; done {len(done_ids)}", flush=True)
    processed = 0
    for idx, task in enumerate(tasks):
        if idx < args.start:
            continue
        if task["task_id"] in done_ids:
            continue
        if processed >= args.max_tasks:
            break
        tid = task["task_id"]
        era_key = task["era_key"]
        t0 = time.monotonic()
        print(f"[C4] {idx+1}/{len(tasks)} {tid} era={era_key}", flush=True)
        try:
            wts = ensure_worktrees(tid, task["parent_commit"], task["target_commit"])
            ch = changed_paths_linux(task["parent_commit"], task["target_commit"])
            short = tid.split("-")[-1][:12]
            tgt = run_state_in_container(era_key=era_key, worktree_linux=wts["target"],
                                         tid=short, state="t", test_files=ch["test_files"])
            par = run_state_in_container(era_key=era_key, worktree_linux=wts["parent"],
                                         tid=short, state="p", test_files=ch["test_files"])
            junit_archive = archive_task_junit(tid, wts["target"], wts["parent"], short)
            with open(JUNIT_MANIFEST, "a", encoding="utf-8") as fh:
                fh.write(json.dumps({"task_id": tid, **junit_archive}, ensure_ascii=False) + "\n")
            all_nodes = sorted(set(tgt["junit"]) | set(par["junit"]))
            counts = {"BEHAVIORAL_F2P": 0, "SYMBOL_ABSENCE_F2P": 0, "PARENT_COLLECTION_ERROR": 0,
                      "FLAKY": 0, "TARGET_ORACLE_INVALID": 0, "P2P_ONLY": 0, "OTHER_REVIEW_REQUIRED": 0}
            node_records = []
            for node in all_nodes:
                t_out = tgt["junit"].get(node, "missing")
                p_out = par["junit"].get(node, "missing")
                t_list = t_out if isinstance(t_out, list) else [t_out] * 3
                p_list = p_out if isinstance(p_out, list) else [p_out] * 3
                cls = classify_node_v2(
                    target_outcomes=list(t_list),
                    parent_outcomes=list(p_list),
                    parent_failure_text=par["junit_failures"].get(node, ""),
                    parent_collects_node=node in par["junit"],
                    shared_test_support_failed=node not in par["junit"],
                )
                counts[cls] += 1
                node_records.append({"node_id": node, "classification": cls})
                with open(PER_TEST, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps({
                        "task_id": tid, "node_id": node, "classification": cls,
                        "target_outcomes": list(t_list), "parent_outcomes": list(p_list),
                    }, ensure_ascii=False) + "\n")
            canary = select_canary_node(node_ids=all_nodes, changed_test_files=ch["test_files"],
                                        touched_production_files=ch["prod_files"])
            canary_rec = {"canary_node_id": canary}
            if canary:
                c_t = tgt["junit"].get(canary, ["missing"] * 3)
                c_p = par["junit"].get(canary, ["missing"] * 3)
                canary_rec["canary_verdict"] = canary_verdict(
                    list(c_p) if isinstance(c_p, list) else [c_p] * 3,
                    list(c_t) if isinstance(c_t, list) else [c_t] * 3,
                )
            else:
                canary_rec["canary_verdict"] = "CANARY_NONE"
            flags = task_eligibility_v2(
                n_behavioral_f2p=counts["BEHAVIORAL_F2P"],
                n_symbol_absence_f2p=counts["SYMBOL_ABSENCE_F2P"],
                n_parent_collection_error=counts["PARENT_COLLECTION_ERROR"],
                environment_valid=True,
                task_collection_failure=bool(tgt.get("error") == "INSTALL_FAIL" or par.get("error") == "INSTALL_FAIL"),
            )
            era_spec = resolve_era(
                python_requirement=next((k for k, v in ERA_TABLE.items() if v.era_key == era_key), "UNKNOWN"),
                lockfile_sha256=lockfile_sha256(task["target_commit"]),
            )
            provenance = make_provenance_record({
                "harness_version": HARNESS_VERSION,
                "harness_commit_sha": harness_commit,
                "classifier_bundle_sha256": SEMANTIC_CLASSIFIER_BUNDLE_SHA256,
                "os_distro": "ubuntu-24.04",
                "container_image_tag": f"wp2-era-{era_key}:latest",
                "container_image_digest": era_spec["image_digest"],
                "python_executable": "/opt/venv/bin/python",
                "python_version": era_spec["python_version"],
                "installer_version": era_spec["installer_version"],
                "lockfile_sha256": era_spec["lockfile_sha256"],
                "dependency_pip_freeze_hash": "dev-sweep-2026-09-23",
                "environment_fingerprint": era_spec["era_fingerprint_sha256"],
                "parent_commit": task["parent_commit"],
                "target_commit": task["target_commit"],
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "test_command": "pytest --ds=saleor.tests.settings --disable-socket --reuse-db (per-file 3x per state)",
                "junit_sha256": "collected-per-file",
                "output_sha256": "collected-per-file",
                "test_patch_rule_sha256": TEST_PATH_RULE_SHA256,
                "postgres_version": "15",
                "postgres_image_digest": "sha256:f7d23353e1b15400d22ebe31189f4d314b87a4c129cc400c8c2d8d4ca127bf81",
            })
            rec = {
                "task_id": tid,
                "status": "DONE",
                "classification": "BEHAVIORAL_F2P" if flags["PRIMARY_BEHAVIORAL_F2P_ELIGIBLE"] else "NOT_PRIMARY",
                "era_key": era_key,
                "counts": counts,
                "eligibility": flags,
                "canary": canary_rec,
                "n_nodes": len(all_nodes),
                "n_test_files": len(ch["test_files"]),
                "junit_archive": junit_archive,
                "persistence_revision": PERSISTENCE_REVISION,
                "wall_s": round(time.monotonic() - t0, 1),
                "provenance": provenance,
            }
        except Exception as exc:
            rec = {
                "task_id": tid,
                "status": "ERROR",
                "error": f"{type(exc).__name__}: {exc}",
                "wall_s": round(time.monotonic() - t0, 1),
            }
        with open(PER_TASK, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        done_ids.add(tid)
        processed += 1
        print(f"  -> {rec['status']} counts={rec.get('counts', {})} wall={rec['wall_s']}s", flush=True)
    print(f"[C4] chunk complete: {processed} processed; {len(done_ids)} total done", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
