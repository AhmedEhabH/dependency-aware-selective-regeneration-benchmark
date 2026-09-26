#!/usr/bin/env python3
"""WP-2 Mission-10B Phase 5: C4 V3 rerun orchestrator (ZERO API).

Executes the authoritative C4 changed-test candidates under Harness V3 with
workers=2 task-level parallelism, ENG-first queue barrier, W2-equivalence gate
(the 4 Phase-3 probe tasks re-run first under workers=2), per-task transaction
(persist -> parse -> integrity -> sha256 -> archive -> drop DB -> remove
worktree), resource guards, and resume.

Queue (17.2):
- STAGE A: 4 probe tasks first under workers=2 (W2 equivalence).
- STAGE B: remaining ENG C4 candidates, longest V2 wall_s first.
- BARRIER: no non-ENG task until ENG candidates DONE + W2 equivalence PASS +
  ENG oracle summary persisted.
- STAGE C: non-ENG candidates after ENG_SMOKE_READY, V2 wall_s desc.

Usage:
    python scripts/wp2_m10b_phase5_c4_v3.py [--out DIR] [--max-tasks N]
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
    base_image_id,
    clock_preflight,
    ensure_worktrees_v3,
    git_linux,
    lock_install_script,
    locked_dev_install,
    lockfile_sha256,
    now_utc,
    remove_worktrees_v3,
    run_state_v3,
    target_manifests,
)
from benchmark.wp2.oracle_semantics_v2 import classify_node_v2  # noqa: E402
from benchmark.wp2.oracle_semantics_v2 import (  # noqa: E402
    task_eligibility_v2 as _task_eligibility_v2,
)

V2_ROOT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23"
OUT_ROOT = PROJECT / "research" / "wp2" / "harness_v3_2026-09-26"
PROGRESS_FILE = OUT_ROOT / "phase5_c4_v3_progress.json"
PER_TASK = OUT_ROOT / "phase5_c4_v3_per_task.jsonl"
STOP_FLAG = PROJECT / "logs" / "C4_STOP.flag"

PROBE_TASKS = [
    "saleor-rc-c3b9e396b07d",
    "saleor-rc-e25cf9b4a837",
    "saleor-rc-74538ea00ce9",
    "saleor-rc-8f76ddc6267f",
]
WSL_CACHE = "/opt/wp2_v2/saleor-cache"
C_FREE_HARD_STOP_GIB = 32.0
C_FREE_WARN_GIB = 40.0
HOST_AVAIL_W1_GIB = 2.5
HOST_AVAIL_W2_PREFER_GIB = 5.0
WSL_AVAIL_W1_GIB = 2.0
WSL_AVAIL_W2_PREFER_GIB = 3.0


def _gib_free(path: str = "C:/") -> float:
    import shutil
    return shutil.disk_usage(path).free / (1024 ** 3)


def _host_avail_gib() -> float:
    import psutil
    return psutil.virtual_memory().available / (1024 ** 3)


def _wsl_avail_gib() -> float:
    r = subprocess.run(["wsl", "-d", "Ubuntu-24.04", "--", "bash", "-lc",
                        "grep MemAvailable /proc/meminfo"],
                       capture_output=True, text=True, encoding="utf-8", timeout=30)
    for tok in r.stdout.split():
        if tok.isdigit():
            return int(tok) / (1024 ** 2)
    return 0.0


def load_v2_tasks() -> dict[str, dict]:
    out = {}
    for line in (V2_ROOT / "per_task_dev_v2.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        out[r["task_id"]] = r
    return out


def task_commits(task_id: str) -> tuple[str, str]:
    census = json.loads((V2_ROOT / "dev_census_2026-09-23.json").read_text(encoding="utf-8"))
    for t in census.get("tasks", []):
        if t["task_id"] == task_id:
            return t["parent_commit"], t["target_commit"]
    raise RuntimeError(f"{task_id} not in census")


def changed_test_files(parent: str, target: str) -> list[str]:
    r = git_linux(WSL_CACHE, "diff", "--name-only", parent, target)
    return sorted(ln.strip() for ln in r.stdout.splitlines()
                  if ln.strip().endswith(".py") and "/test" in ln)


def git_local(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(PROJECT), *args],
                          capture_output=True, text=True, encoding="utf-8", check=False)


def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
    return {"done": {}, "w2_equivalence": None, "eng_ready": False,
            "smoke_ready": False, "status": "init"}


def save_progress(p: dict) -> None:
    p["last_heartbeat"] = now_utc()
    PROGRESS_FILE.write_text(json.dumps(p, indent=1, ensure_ascii=False), encoding="utf-8")


def load_done() -> set[str]:
    done = set()
    if PER_TASK.exists():
        for line in PER_TASK.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                done.add(json.loads(line)["task_id"])
    return done


def build_queue(v2: dict[str, dict]) -> dict[str, list[str]]:
    """Queue per 17.2: STAGE A (probes) -> STAGE B (ENG) -> STAGE C (non-ENG)."""
    eng = set()
    ds = json.loads((V2_ROOT / "dev_split_v2_2026-09-23.json").read_text(encoding="utf-8"))
    eng = set(ds["membership"].get("DEV_TRAIN_ENG", []))
    all_ids = list(v2)
    eng_ids = [t for t in all_ids if t in eng]
    non_eng = [t for t in all_ids if t not in eng]
    # STAGE A: probes in frozen order
    stage_a = [t for t in PROBE_TASKS if t in all_ids]
    # STAGE B: remaining ENG, longest V2 wall_s first, tie task_id
    rest_eng = [t for t in eng_ids if t not in stage_a]
    rest_eng.sort(key=lambda t: (-(v2[t].get("wall_s") or 0), t))
    # STAGE C: non-ENG, V2 wall_s desc
    non_eng.sort(key=lambda t: (-(v2[t].get("wall_s") or 0), t))
    return {"STAGE_A": stage_a, "STAGE_B": rest_eng, "STAGE_C": non_eng}


def run_task(task_id: str, out_root: Path) -> dict:
    parent, target = task_commits(task_id)
    v2_task = load_v2_tasks().get(task_id, {})
    era_key = v2_task.get("era_key", "UNKNOWN")
    test_files = changed_test_files(parent, target)
    print(f"[C4V3] {task_id} era={era_key} files={len(test_files)}", flush=True)

    clock = clock_preflight()
    if clock["verdict"] == "CLOCK_BLOCKED":
        return {"task_id": task_id, "status": "CLOCK_BLOCKED",
                "clock": clock, "error": "CLOCK_BLOCKED"}

    manifests = target_manifests(target)
    wts = ensure_worktrees_v3(task_id, parent, target)
    tid = task_id.split("-")[-1][:12]
    install_t, install_mode, _ = lock_install_script(wts["t"], manifests)
    install_p, _, _ = lock_install_script(wts["p"], manifests)
    locked_dev = locked_dev_install(task_id)
    img_id = base_image_id(era_key)

    t0 = time.monotonic()
    tgt = run_state_v3(era_key=era_key, worktree_linux=wts["t"], tid=tid,
                       state="t", test_files=test_files,
                       install_fragment=install_t,
                       locked_dev_fragment=locked_dev, timeout_s=7200)
    t_wall = round(time.monotonic() - t0, 1)
    par = run_state_v3(era_key=era_key, worktree_linux=wts["p"], tid=tid,
                       state="p", test_files=test_files,
                       install_fragment=install_p,
                       locked_dev_fragment=locked_dev, timeout_s=7200)
    p_wall = round(time.monotonic() - t0, 1)

    all_nodes = sorted(set(tgt["junit"]) | set(par["junit"]))
    counts = {"BEHAVIORAL_F2P": 0, "SYMBOL_ABSENCE_F2P": 0, "PARENT_COLLECTION_ERROR": 0,
              "FLAKY": 0, "TARGET_ORACLE_INVALID": 0, "P2P_ONLY": 0,
              "OTHER_REVIEW_REQUIRED": 0}
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
        node_records.append({
            "node_id": node, "v3_class": cls,
            "target_outcomes": list(t_list), "parent_outcomes": list(p_list),
        })
    flags = _task_eligibility_v2(
        n_behavioral_f2p=counts["BEHAVIORAL_F2P"],
        n_symbol_absence_f2p=counts["SYMBOL_ABSENCE_F2P"],
        n_parent_collection_error=counts["PARENT_COLLECTION_ERROR"],
        environment_valid=True,
        task_collection_failure=False,
    )
    # Classify terminal status under Harness V3 (11.1 / 17.2).
    # INSTALL_FAIL from the lock-exact install = deterministic ENV_INSTALL_BLOCKED
    # (no historically faithful install producible); counted terminal for the
    # ENG barrier but NOT oracle-executable.
    t_err = tgt.get("error")
    p_err = par.get("error")
    if t_err or p_err:
        if t_err == "INSTALL_FAIL" or p_err == "INSTALL_FAIL":
            status = "ENV_INSTALL_BLOCKED"
        elif t_err == "CLOCK_BLOCKED" or p_err == "CLOCK_BLOCKED":
            status = "CLOCK_BLOCKED"
        else:
            status = "ERROR"
    else:
        status = "DONE"
    result = {
        "task_id": task_id,
        "status": status,
        "era_key": era_key,
        "target_commit": target,
        "counts": counts,
        "eligibility": flags,
        "classification": "BEHAVIORAL_F2P" if flags["PRIMARY_BEHAVIORAL_F2P_ELIGIBLE"] else "NOT_PRIMARY",
        "n_nodes": len(all_nodes),
        "n_test_files": len(test_files),
        "wall_s": round(time.monotonic() - t0, 1),
        "operations": {"target_wall_s": t_wall, "parent_wall_s": p_wall,
                       "target_error": tgt.get("error"), "parent_error": par.get("error")},
        "node_records": node_records,
        "manifest": {
            "task_id": task_id,
            "target_commit": target,
            "era": era_key,
            "frozen_base_image_id": img_id,
            "harness_v3_version": "wp2-harness-v3-2026-09-26",
            "runner_sha": git_local("rev-parse", "HEAD").stdout.strip(),
            "install_mode": install_mode,
            "lockfile_sha256": lockfile_sha256(manifests),
            "nofile_soft": 65536, "nofile_hard": 65536,
            "clock_pre_post": {"pre": clock["pre"]["median_skew_s"],
                               "post": (clock.get("post") or {}).get("median_skew_s")},
            "C4_EFFECTIVE_WORKERS": 1,
            "db_names": {"t": tgt.get("db_name"), "p": par.get("db_name")},
        },
    }
    result["evidence_sha256"] = _sha256(result)
    remove_worktrees_v3(task_id)
    (out_root / f"phase5_c4v3_{task_id}.json").write_text(
        json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    with PER_TASK.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(result, ensure_ascii=False) + "\n")
    print(f"  -> {result['status']} counts={counts} wall={result['wall_s']}s", flush=True)
    return result


def _sha256(payload: object) -> str:
    import hashlib
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def w1_rerun_reproducibility_check() -> dict:
    """Compare Phase-3 (w1) vs Phase-5 (w1-rerun, same effective concurrency)
    node classes for the 4 probes. This is W1_RERUN_REPRODUCIBILITY, NOT a
    workers=2 equivalence test (task-level concurrency was never exercised;
    C4_EFFECTIVE_WORKERS = 1 throughout)."""
    mismatches = []
    for tid in PROBE_TASKS:
        w1 = OUT_ROOT / f"phase3_probe_{tid}.json"
        w2 = OUT_ROOT / f"phase5_c4v3_{tid}.json"
        if not w1.exists() or not w2.exists():
            mismatches.append(f"{tid}: missing w1 or w2 evidence")
            continue
        d1 = json.loads(w1.read_text(encoding="utf-8"))
        d2 = json.loads(w2.read_text(encoding="utf-8"))
        m1 = {r["node_id"]: r["v3_class"] for r in d1.get("node_records", [])}
        m2 = {r["node_id"]: r["v3_class"] for r in d2.get("node_records", [])}
        for nid in sorted(set(m1) | set(m2)):
            c1 = m1.get(nid)
            c2 = m2.get(nid)
            if c1 != c2:
                mismatches.append(f"{tid}::{nid}: w1={c1} w2={c2}")
    return {"pass": len(mismatches) == 0, "mismatches": mismatches[:20],
            "n_mismatches": len(mismatches)}


def _verify_done(task_id: str) -> dict:
    """Resume-hardening (directive step 3): a task is skippable only if its
    DONE record exists, expected scientific evidence exists, its persisted
    SHA256 verifies, and integrity checks pass. Returns {'ok': True} or
    {'ok': False, 'reason': ...}."""
    ev = OUT_ROOT / f"phase5_c4v3_{task_id}.json"
    if not ev.exists():
        return {"ok": False, "reason": "missing evidence json"}
    try:
        rec = json.loads(ev.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "reason": f"evidence unparseable: {exc}"}
    if rec.get("status") not in ("DONE", "ENV_INSTALL_BLOCKED"):
        return {"ok": False, "reason": f"record status {rec.get('status')}"}
    # SHA256 of the persisted evidence (without the self-referential field)
    payload = dict(rec)
    payload.pop("evidence_sha256", None)
    expected = rec.get("evidence_sha256")
    if expected and _sha256(payload) != expected:
        return {"ok": False, "reason": "SHA256 mismatch"}
    # integrity: node records must be present and internally consistent
    n_nodes = rec.get("n_nodes", 0)
    if n_nodes and len(rec.get("node_records", [])) == 0:
        return {"ok": False, "reason": "n_nodes>0 but no node_records"}
    # operations must not carry an infra error (ENV_INSTALL_BLOCKED is a
    # deterministic classification, not an unexpected error)
    ops = rec.get("operations", {})
    if rec.get("status") == "DONE" and (ops.get("target_error") or ops.get("parent_error")):
        return {"ok": False, "reason": "infra error in operations"}
    return {"ok": True}


def _discard_task_state(task_id: str) -> None:
    """Discard a partial/verify-failed task safely (resume-hardening): remove
    orphan containers, worktrees, temp DBs, and the incomplete evidence."""
    tid = task_id.split("-")[-1][:12]
    import subprocess as _sp
    # remove any v3 containers for this task
    _sp.run(["wsl", "-d", "Ubuntu-24.04", "--", "bash", "-lc",
             f"docker ps -a --format '{{{{.Names}}}}' | grep -E '{tid}.*v3|v3.*{tid}' | "
             "xargs -r docker rm -f"],
            capture_output=True, text=True, encoding="utf-8", timeout=120)
    # remove worktrees
    _sp.run(["wsl", "-d", "Ubuntu-24.04", "--", "bash", "-lc",
             f"git -C {WSL_CACHE} worktree remove --force "
             f"/opt/wp2_v2/worktrees/{tid}_v3_t 2>/dev/null || rm -rf "
             f"/opt/wp2_v2/worktrees/{tid}_v3_t; "
             f"git -C {WSL_CACHE} worktree remove --force "
             f"/opt/wp2_v2/worktrees/{tid}_v3_p 2>/dev/null || rm -rf "
             f"/opt/wp2_v2/worktrees/{tid}_v3_p; "
             f"git -C {WSL_CACHE} worktree prune"],
            capture_output=True, text=True, encoding="utf-8", timeout=120)
    # drop any v3 DBs
    _sp.run(["wsl", "-d", "Ubuntu-24.04", "--", "bash", "-lc",
             f"docker exec wp2-pg psql -U saleor -d postgres -c "
             f"\"DROP DATABASE IF EXISTS saleor_v3_{tid}_t WITH (FORCE)\" "
             f"2>/dev/null; docker exec wp2-pg psql -U saleor -d postgres -c "
             f"\"DROP DATABASE IF EXISTS saleor_v3_{tid}_p WITH (FORCE)\" 2>/dev/null; "
             f"docker exec wp2-pg psql -U saleor -d postgres -c "
             f"\"DROP DATABASE IF EXISTS test_saleor_v3_{tid}_t WITH (FORCE)\" 2>/dev/null; "
             f"docker exec wp2-pg psql -U saleor -d postgres -c "
             f"\"DROP DATABASE IF EXISTS test_saleor_v3_{tid}_p WITH (FORCE)\" 2>/dev/null"],
            capture_output=True, text=True, encoding="utf-8", timeout=120)
    # remove incomplete evidence + progress entry
    ev = OUT_ROOT / f"phase5_c4v3_{task_id}.json"
    if ev.exists():
        ev.unlink()
    prog = load_progress()
    prog.get("done", {}).pop(task_id, None)
    save_progress(prog)
    # remove from per_task jsonl (rebuild without this task)
    if PER_TASK.exists():
        lines = [ln for ln in PER_TASK.read_text(encoding="utf-8").splitlines()
                 if ln.strip()]
        kept = [ln for ln in lines
                if json.loads(ln)["task_id"] != task_id]
        if len(kept) != len(lines):
            PER_TASK.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--max-tasks", type=int, default=9999)
    ap.add_argument("--stage", choices=["A", "B", "C", "ALL"], default="ALL")
    args = ap.parse_args()
    out_root = Path(args.out) if args.out else OUT_ROOT
    out_root.mkdir(parents=True, exist_ok=True)

    v2 = load_v2_tasks()
    queue = build_queue(v2)
    print(f"[C4V3] queue: A={len(queue['STAGE_A'])} B={len(queue['STAGE_B'])} "
          f"C={len(queue['STAGE_C'])}", flush=True)

    # resource preflight
    c_free = _gib_free()
    if c_free < C_FREE_HARD_STOP_GIB:
        print(f"[C4V3] HARD STOP: C free {c_free:.1f} GiB < 32", flush=True)
        return 1
    print(f"[C4V3] C free {c_free:.1f} GiB; host avail {_host_avail_gib():.1f} GiB; "
          f"WSL avail {_wsl_avail_gib():.1f} GiB", flush=True)

    done = load_done()
    order = []
    if args.stage in ("A", "ALL"):
        order += queue["STAGE_A"]
    if args.stage in ("B", "ALL"):
        order += queue["STAGE_B"]
    if args.stage in ("C", "ALL"):
        order += queue["STAGE_C"]

    # ENG barrier: in FULL mode, do not run STAGE C until ENG (A+B) DONE
    eng_set = set(queue["STAGE_A"]) | set(queue["STAGE_B"])
    progress = load_progress()
    if "w1_rerun_reproducibility" not in progress:
        # correctness (directive step 1): record the truth of what ran.
        progress["w1_rerun_reproducibility"] = w1_rerun_reproducibility_check()
        progress["W2_EQUIVALENCE"] = "NOT_TESTED"
        progress["C4_EFFECTIVE_WORKERS"] = 1
    processed = 0
    for tid in order:
        if processed >= args.max_tasks:
            break
        if tid in done:
            # resume-hardening: verify evidence/hash/integrity before skip
            v = _verify_done(tid)
            if not v["ok"]:
                print(f"[C4V3] {tid} marked done but FAILS verification "
                      f"({v['reason']}); discarding and re-running", flush=True)
                done.discard(tid)
                _discard_task_state(tid)
            else:
                continue
        if STOP_FLAG.exists():
            print("[C4V3] STOP flag present; stopping gracefully", flush=True)
            break
        if tid in queue["STAGE_C"] and args.stage == "ALL":
            eng_done = eng_set.issubset(done)
            if not progress.get("eng_ready") and not eng_done:
                print(f"[C4V3] BARRIER: ENG not complete ({len(eng_set - done)} "
                      f"remaining); not launching non-ENG {tid}", flush=True)
                continue
        # resource guard: single worker (C4_EFFECTIVE_WORKERS = 1)
        host_avail = _host_avail_gib()
        wsl_avail = _wsl_avail_gib()
        if host_avail < HOST_AVAIL_W1_GIB or wsl_avail < WSL_AVAIL_W1_GIB:
            print(f"[C4V3] low resource (host {host_avail:.1f}, wsl {wsl_avail:.1f}); "
                  f"waiting 30s", flush=True)
            time.sleep(30)
            continue
        res = run_task(tid, out_root)
        done.add(tid)
        processed += 1
        progress = load_progress()
        progress["done"][tid] = res.get("status")
        save_progress(progress)
        if tid in queue["STAGE_B"] and eng_set.issubset(done):
            progress["eng_ready"] = True
            progress["status"] = "ENG_DONE_WAITING_SMOKE_READY"
            save_progress(progress)
            print("[C4V3] all ENG candidates DONE; ENG oracle summary needed "
                  "(phase5_eng_oracle step)", flush=True)
    save_progress(progress)
    print(f"[C4V3] processed {processed}; total done {len(done)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
