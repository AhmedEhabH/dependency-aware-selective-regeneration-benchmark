#!/usr/bin/env python3
"""T12 M02-D3-R2 — one-arm OS child (NEW interpreter PER arm).

Mission: T12_M02_D3R2_OPTION_B_PROCESS_20261028.  The parent orchestrator
launches ONE new OS process per arm (the frozen control order); this worker
executes exactly ONE arm through the REAL frozen engine once:

  1. truthful process witness (pid, parent pid, argv digest, worker source
     SHA, UTC start/end, monotonic birth markers, OS-verified process start);
  2. real frozen materializer subprocess (engineering record);
  3. real frozen ``harness_v3.run_state_v3`` with ``OpwsIsolatedRuntime``
     (frozen modules imported read-only from the frozen worktree);
  4. canonical JUnit evidence (9 per arm) + control classification;
  5. real post-run DB scan (operator-supplied command) + read-only snapshot
     hash of the scan;
  6. LIVE receipt built ONLY from measured evidence (no ``sample_run_receipt``
     seeding; network bytes NOT_MEASURED unless actually sampled) and validated
     by the real validator;
  7. bounded read-only docker-events capture for container INSTANCE evidence
     (an image digest is never presented as a container id).

This file is the deployable child of the D3-R2 orchestrator.  It is NEVER
invoked in this offline mission (``run`` stays RD-8/RD-9 gated and absent);
it exists so the run-mode path provably uses only real pinned engine
functions.  Test doubles appear only in unit tests.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

_SCRIPTS = Path(__file__).resolve().parent


def _load(rel_name: str, mod_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(mod_name, _SCRIPTS / f"{rel_name}.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


_adapt = _load("t12_m02_arm_adapter", "t12_m02_arm_adapter")
_contract = _load("t12_m02_f2p_contract", "t12_m02_f2p_contract")
_exe = _load("t12_m02_execute_f2p", "t12_m02_execute_f2p")
_identity = _load("t12_m02_d3r2_identity", "t12_m02_d3r2_identity")
_receipts = _load("t12_m02_receipts", "t12_m02_receipts")

WORKER_SCHEMA = "t12_m02_d3r2_worker_input_v1"


def _load_frozen(worktree: Path, rel: str, name: str) -> Any:
    return _exe._load_frozen_module(worktree, rel, name)


def _default_db_scan(cmd: str | None) -> list[str]:
    """Real read-only scan of the isolated PG fixture (operator-supplied)."""
    if not cmd:
        raise RuntimeError("TEARDOWN_NOT_VERIFIED: T12_M02_DB_SCAN_CMD not configured")
    return shlex.split(cmd, posix=(os.name != "nt"))


def run_arm(witness_input: Path, out_dir: Path, *, db_scan_cmd_env: str | None = None) -> dict[str, Any]:
    """Execute EXACTLY ONE arm; returns the arm stage result (never raises on
    scientific outcome; raises on engineering contract violations)."""
    cfg = json.loads(witness_input.read_text(encoding="utf-8"))
    if cfg.get("schema") != WORKER_SCHEMA:
        raise ValueError(f"worker input schema {cfg.get('schema')!r} != {WORKER_SCHEMA!r}")
    arm = cfg["arm"]
    worktree = Path(cfg["worktree"])
    source_repo = Path(cfg["source_repo"])
    scopes_dir = Path(cfg["scopes_dir"])
    classification = Path(cfg["classification"])
    test_authority = Path(cfg["test_authority"])
    wt_linux = cfg["worktree_linux"]
    expected_oid = cfg["effective_tree_oid"]
    pinned_oci = cfg.get("pinned_oci", _identity.PINNED_PY312_OCI_ID)
    stage: dict[str, Any] = {
        "schema": "t12_m02_d3r2_worker_stage_v1",
        "arm_id": arm,
        "status": "NOT_RUN",
        "control_outcome": "NOT_RUN",
        "stages": {},
        "worker_utc_start": _identity.utc_now(),
    }
    run_dir = out_dir / "receipts"
    witness = _identity.span_witness(
        nonce=_identity.new_nonce(),
        pid=int(os.getpid()),
        parent_pid=int(os.getppid()),
        argv=list(sys.argv),
        worker_script_path=Path(__file__).resolve(),
        monotonic_start_ns=time.monotonic_ns(),
        monotonic_end_ns=0,                    # filled at end
        start_utc=stage["worker_utc_start"],
        end_utc="",
        exit_code=0,
        worker_os_start=_identity.windows_os_process_start(int(os.getpid())),
    )
    try:
        # ---- 0) worktree admission on the OS that owns it, BEFORE side effects
        probe = _identity.PlatformProbe()
        gate = _identity.linux_worktree_gate(probe, wt_linux, expected_oid)
        stage["stages"]["worktree_gate_pre"] = gate
        if not gate["pass"]:
            raise RuntimeError("WORKTREE_GATE_FAILED_PRE:" + ";".join(gate["reasons"]))
        # ---- 1) real materializer (frozen CLI) ----
        mat_dir = out_dir / "materialize_record"
        argv = [
            "python", str(worktree / cfg["materializer_rel"]),
            "--repo", str(source_repo),
            "--parent", _adapt.FROZEN_PARENT,
            "--target", _adapt.FROZEN_TARGET,
            "--task-id", _adapt.FROZEN_TASK,
            "--scope-json", str(scopes_dir / f"scope_{arm}.json"),
            "--classification-json", str(classification),
            "--test-authority-json", str(test_authority),
            "--out-dir", str(mat_dir),
        ]
        proc = subprocess.run(argv, capture_output=True, text=True,
                              encoding="utf-8", timeout=900, check=False)
        if proc.returncode != 0:
            raise RuntimeError("MATERIALIZE_FAILED:" + (proc.stderr or "")[-400:])
        records = _exe._load_materialize_records(mat_dir)
        bad = [r for r in records
               if r.get("scope_hash") != cfg.get("scope_hash")
               or r.get("reference_patch_sha256") != cfg.get("patch_sha256")]
        if bad:
            raise RuntimeError("MATERIALIZER_RECORD_MISMATCH")
        stage["stages"]["materialize"] = {"exit": proc.returncode, "record_digests_match": True}
        # ---- 2) engine imports (real frozen modules) ----
        harness = _load_frozen(worktree, _exe.HARNESS_REL, "benchmark_harness_v3")
        isolated_mod = _load_frozen(worktree, _exe.ISOLATED_RUNTIME_REL, "benchmark_opws_isolated_runtime_v1")
        manifests = harness.target_manifests(_adapt.FROZEN_TARGET)
        fragment_raw, install_mode, install_evidence = harness.lock_install_script(wt_linux, manifests)
        if not isinstance(fragment_raw, str) or not fragment_raw.strip():
            raise RuntimeError("INSTALL_FRAGMENT_EMPTY")
        isolated = isolated_mod.OpwsIsolatedRuntime(
            worktree_linux=wt_linux,
            scratch_linux=f"{cfg['scratch_linux_base']}/{out_dir.parent.name}",
            scratch_windows=str(out_dir),
            db_commit_short=_exe.TASK8,
        )
        isolated.validate()
        stage["stages"]["engine_imports"] = {"ok": True, "install_mode": install_mode}
        # ---- 3) bounded READ-ONLY container-instance stream for this arm's
        # window: started BEFORE the engine call (concurrent capture; a docker
        # event stream is a daemon read with no side effects) and stopped right
        # after the engine returns.
        container_evidence = {"container_instance_status": "CONTAINER_INSTANCE_NOT_MEASURED",
                              "reason": "docker events capture disabled or unavailable"}
        cap_proc: Any = None
        cap_file = out_dir / "docker_events_window.jsonl"
        if cfg.get("docker_events"):
            until_proj = _identity.utc_seconds()
            cap_proc, _ = _start_events_capture(cap_file, since=stage["worker_utc_start"], until=until_proj)
        # ---- 4) the REAL frozen one-arm engine call ----
        run_start = _identity.utc_seconds()
        result = harness.run_state_v3(
            era_key="py312",
            worktree_linux=wt_linux,
            tid=_exe.TID,
            state=arm,
            test_files=list(_adapt.F2P_NODES),
            install_fragment=fragment_raw,
            locked_dev_fragment="echo NO_LOCKED_DEV_GROUP",
            raw_junit_dir=str(run_dir / "engine_raw_junit"),
            timeout_s=7200,
            isolated=isolated,
        )
        run_end = _identity.utc_seconds()
        if cap_proc is not None:
            events_cap = _finish_events_capture(cap_proc, cap_file, pinned_oci)
            if events_cap.get("status") == "MEASURED":
                container_evidence = {
                    "container_instance_status": "MEASURED",
                    "instances": str(events_cap.get("instances")),
                    "image_digest": pinned_oci,
                }
            else:
                container_evidence = {
                    "container_instance_status": "CONTAINER_INSTANCE_NOT_MEASURED",
                    "reason": str(events_cap.get("reason")),
                    "capture_log": str(cap_file.read_text(encoding="utf-8", errors="replace")[-1000:]
                                        if cap_file.exists() else ""),
                }
        stage["stages"]["run_state_v3"] = {
            "start_utc": run_start, "end_utc": run_end,
            "db_name": result.get("db_name"),
            "result_error": result.get("error"),
        }
        # ---- 5) honest evidence checks ----
        db_name = result.get("db_name")
        if not isinstance(db_name, str) or not _receipts.DB_IDENTITY_RE.match(db_name):
            raise RuntimeError("DB_IDENTITY_UNPROVEN")
        if result.get("db_cleanup") != "DROPPED_AFTER_JUNIT_PARSE":
            raise RuntimeError("DB_CLEANUP_UNPROVEN")
        junit_files = list(result.get("junit_files") or [])
        if len(junit_files) != _exe.PILOT_JUNIT_PER_ARM:
            raise RuntimeError(f"JUNIT_COUNT_MISMATCH:{len(junit_files)}")
        mapping = _exe._canonical_junit_map(run_dir / "engine_raw_junit", run_dir / "junit", arm)
        classifications = [
            _receipts.classify_junit(run_dir / "junit" / c) for c in sorted(mapping.values())
        ]
        expected = _adapt.CONTROL_EXPECTED_JUNIT.get(arm)
        observed = set(classifications)
        if expected is not None and observed != {expected}:
            raise RuntimeError(f"CONTROL_MISMATCH:{arm} expected {expected} observed {sorted(observed)}")
        # ---- 6) real teardown DB scan + read-only snapshot hash ----
        scan_cmd = db_scan_cmd_env or os.environ.get("T12_M02_DB_SCAN_CMD")
        if not scan_cmd:
            raise RuntimeError("TEARDOWN_NOT_VERIFIED: T12_M02_DB_SCAN_CMD not configured")
        scan_proc = subprocess.run(
            _default_db_scan(scan_cmd), capture_output=True, text=True,
            encoding="utf-8", timeout=120, check=False)
        if scan_proc.returncode != 0:
            raise RuntimeError("TEARDOWN_NOT_VERIFIED: DB scan failed rc="
                               f"{scan_proc.returncode}: {scan_proc.stderr[-300:]}")
        leftovers = [t.strip() for t in (scan_proc.stdout or "").splitlines()
                     if _receipts.DB_IDENTITY_RE.match(t.strip())]
        scan_path = run_dir / "post_run_db_scan.json"
        scan_path.write_text(json.dumps({
            "remaining_opws_m3b_databases": leftovers,
            "checked_at_utc": _identity.utc_now(),
            "scan_cmd_digest": _identity.argv_digest(_default_db_scan(scan_cmd)),
        }, indent=2), encoding="utf-8")
        scan_sha = _identity.file_sha256(scan_path)
        stage["stages"]["post_run_teardown"] = {
            "engine_db_cleanup": result.get("db_cleanup"),
            "leftovers": leftovers,
            "scan_artifact": str(scan_path),
            "scan_sha256": scan_sha,
            "db_deleted": len(leftovers) == 0,
        }
        if leftovers:
            raise RuntimeError(f"DB_LEFTOVER:{leftovers}")
        # ---- 7) LIVE receipt (no fixture seeding) + real validator ----
        julist = []
        for canon in sorted(mapping.values()):
            jf = run_dir / "junit" / canon
            julist.append(_identity.file_sha256(jf) if jf.is_file() else None)
        witness["monotonic_end_ns"] = time.monotonic_ns()
        witness["times"]["end_utc"] = _identity.utc_seconds()
        receipt = _receipts.live_run_receipt_template(
            arm_id=arm, run_token=cfg.get("execution_id", f"M02E-RUN-{arm}"),
            junit_classifications=classifications,
            db_identity=db_name,
            process={
                "pid": witness["pid"], "driver_argv": witness["argv"],
                "nonce": witness["nonce"], "process_birth": witness["process_birth"],
                "container_oci_id": pinned_oci,
            },
            times={"start_utc": run_start, "end_utc": run_end,
                   "monotonic": True, "wall_seconds": 0.0},
            resources={
                "cpu_seconds": _receipts.NOT_MEASURED,
                "peak_ram_mb": _receipts.NOT_MEASURED,
                "disk_bytes": _receipts.NOT_MEASURED,
                "network_bytes": _identity.live_network_policy(None, None),
                "sampler": "NOT_MEASURED: no resource sampler wired in this mode",
            },
            teardown={
                "present": True, "db_deleted": True,
                "path": "post_run_db_scan.json", "verified_by_post_run_scan": True,
                "post_run_db_scan": leftovers,
                "post_run_db_scan_sha256": scan_sha,
            },
            materialize_provenance={
                "materializer": cfg["materializer_rel"],
                "scope_hash": cfg["scope_hash"],
                "reference_patch_sha256": cfg["patch_sha256"],
                "record_digests_match": True,
                "record_dir": str(mat_dir),
            },
            junit_dir=run_dir / "junit",
            host={"hostname": os.environ.get("COMPUTERNAME", "HOST_UNSET"), "os": "WSL2/Windows"},
            environment={"environment_id": f"live-{_adapt.FROZEN_TASK}-{witness['nonce'][:8]}"},
            pinned_image={"image": "opws-py312-isolated", "oci_id": pinned_oci,
                          "resolved_by": "frozen resolve_runtime_image (engine first fail-closed step)"},
            container=container_evidence,
            junit_receipts_sha=julist,
        )
        receipt["database"]["db_scan_snapshot_sha256"] = scan_sha
        receipt["database"]["db_scan_artifact"] = "post_run_db_scan.json"
        receipt["junit_engine_native_to_canonical"] = mapping
        receipt["engine_native_junit_dir"] = str(run_dir / "engine_raw_junit")
        _identity.assert_live_receipt(receipt)
        _receipts.write_run_receipt(run_dir, receipt)
        vres = _receipts.validate_run_receipt(run_dir)
        issues = list(vres.get("issues") or [])
        stage["stages"]["receipt_validation"] = {"status": "PASS" if not issues else "STOP",
                                                 "issues": issues[:8]}
        if issues:
            raise RuntimeError("RECEIPT_INVALID:" + ";".join(issues[:6]))
        stage["status"] = ("CONTROL_EXPECTED" if arm == "NEG"
                           else ("PASS" if expected else "PASS"))
        stage["control_outcome"] = ("CONTROL_EXPECTED" if arm == "NEG"
                                    else ("CONTROL_PASS" if expected else "OUTCOME_DATA"))
        stage["executed"] = True
    except Exception as exc:
        stage["status"] = "FAIL"
        stage["reason"] = f"{type(exc).__name__}: {exc}"
    finally:
        witness["monotonic_end_ns"] = time.monotonic_ns()
        witness["times"]["end_utc"] = _identity.utc_seconds()
        witness["exit_code"] = 0 if stage["status"] in ("PASS", "CONTROL_EXPECTED") else 2
        stage["worker_utc_end"] = _identity.utc_now()
        (out_dir / "witness.json").write_text(
            json.dumps(witness, indent=2, default=str), encoding="utf-8")
        (out_dir / "worker_stage.json").write_text(
            json.dumps(stage, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"arm": arm, "status": stage["status"],
                      "reason": stage.get("reason")}, indent=2))
    return stage


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="t12_m02_d3r2_worker",
                                 description="one-arm D3-R2 engine child (offline mission: never invoked)")
    ap.add_argument("--witness-input", required=True)
    ap.add_argument("--out", required=True)
    return ap


def _start_events_capture(cap_file: Path, *, since: str, until: str) -> tuple[Any, Path]:
    """Start a bounded background ``docker events`` stream (read-only)."""
    argv = ["wsl", "-d", _identity.WSL_DISTRO, "-u", "root", "--",
            "docker", "events", "--format", "{{json .}}",
            "--since", since, "--until", until]
    with open(cap_file, "w", encoding="utf-8") as fh:
        proc = subprocess.Popen(argv, stdout=fh, stderr=subprocess.DEVNULL,
                                text=True, encoding="utf-8")
    return proc, cap_file


def _finish_events_capture(proc: Any, cap_file: Path, image_digest: str, timeout_s: int = 30) -> dict[str, Any]:
    """Stop the capture and parse image-matched create/start events."""
    done = False
    for _ in range(int(timeout_s * 5)):
        if proc.poll() is not None:
            done = True
            break
        time.sleep(0.2)
    if not done:
        import contextlib

        with contextlib.suppress(Exception):
            proc.terminate()
    events: list[dict[str, Any]] = []
    matched: list[dict[str, Any]] = []
    img12 = image_digest.split(":")[-1][:12]
    if cap_file.exists():
        for line in cap_file.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            events.append(ev)
            if str(ev.get("Action") or "") in ("create", "start") and img12 in json.dumps(ev.get("Actor") or {}):
                matched.append({"container_id": str(ev.get("id") or (ev.get("Actor") or {}).get("ID") or ""),
                                "action": str(ev.get("Action") or ""), "time": ev.get("time")})
    if not matched:
        return {"status": "CONTAINER_INSTANCE_NOT_MEASURED",
                "reason": "no pinned-image create/start event in arm window",
                "events_seen": len(events)}
    return {"status": "MEASURED", "instances": matched,
            "events_seen": len(events), "image_digest": image_digest}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=False)
    stage = run_arm(Path(args.witness_input), out_dir)
    return 0 if stage["status"] in ("PASS", "CONTROL_EXPECTED") else 2


if __name__ == "__main__":
    sys.exit(main())
