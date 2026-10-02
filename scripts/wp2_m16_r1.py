#!/usr/bin/env python3
"""WP2 M16 R1 - repetition-retaining V3 oracle construction (brain-authored). ZERO model API.

Historical fact (not reinterpreted): the frozen C4-V3 path executes 3 repetitions per
changed-test file, but `harness_v3.run_state_v3` merges them with `dict.update` (the last
repetition wins) and `phase5.run_task` then passes `[outcome] * 3` to `classify_node_v2`.
The ENG / M14R / M15-R oracle sets were built that way and stay exactly as recorded.

Rule M16_R1_REPETITION_RETENTION_V1 (MAIN, all 220 tasks of the frozen frame, before Q03):
  * the container work is the FROZEN `run_state_v3`, called unchanged with its own
    `raw_junit_dir` argument so that every repetition's JUnit is persisted;
  * the per-repetition files are parsed with the FROZEN `parse_junit_with_failures`, and for
    every node the outcomes of repetitions 0,1,2 become a 3-list (absent in a repetition ->
    "missing"; a missing JUnit file -> the frozen pseudo-node `<file> = "error"` in that
    repetition, exactly as the frozen merge does);
  * failure texts and node membership are the frozen merged values (dict.update order);
  * classification is the FROZEN `classify_node_v2` / `task_eligibility_v2`, through a loop
    that is a verbatim copy of `phase5.run_task` (identity test against the real function).
Identical triples therefore reproduce the historical classification exactly; only unstable
triples change (they now reach the existing FLAKY precedence).

Infrastructure (refined from Review v2, stated in the R1 artifact): a state is
infrastructure-failed when the container did not finish (`ALL_RUNS_DONE` absent and no
install marker), when a script could not be written, or when a persisted JUnit file does
not parse. It is retried and never classified. A JUnit file missing although the container
finished keeps the frozen pseudo-node semantics (a deterministic state outcome).
"""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import shutil
import tarfile
import time
from pathlib import Path
from typing import Any, Callable

RULE_ID = "M16_R1_REPETITION_RETENTION_V1"
REPS = 3
NO_FILE = "__NO_FILE__"
COUNT_KEYS = ("BEHAVIORAL_F2P", "SYMBOL_ABSENCE_F2P", "PARENT_COLLECTION_ERROR", "FLAKY",
              "TARGET_ORACLE_INVALID", "P2P_ONLY", "OTHER_REVIEW_REQUIRED")
INFRA_ERRORS = ("RUNS_SCRIPT_WRITE_FAIL", "INSTALL_SCRIPT_WRITE_FAIL")
RULE_CONSTANTS = {
    "rule_id": RULE_ID, "reps": REPS, "absent_in_rep": "missing",
    "missing_junit_file": "frozen pseudo-node <test_file> = 'error' in that repetition",
    "failure_text": "frozen dict.update merge across repetitions",
    "classifier": "benchmark.wp2.oracle_semantics_v2.classify_node_v2 (unchanged)",
    "eligibility": "task_eligibility_v2(environment_valid=True, task_collection_failure=False) as frozen",
    "infra": ["container incomplete (no ALL_RUNS_DONE, no INSTALL marker)",
              "RUNS_SCRIPT_WRITE_FAIL", "INSTALL_SCRIPT_WRITE_FAIL", "JUnit parse error",
              "TimeoutExpired / OSError / CalledProcessError"],
    "install_blocked": "frozen INSTALL_FAIL on 2 consecutive attempts of the same task",
}


class OracleInfraError(RuntimeError):
    """A state could not be executed/recorded; never a scientific outcome."""


def rule_constants_sha() -> str:
    return hashlib.sha256(json.dumps(RULE_CONSTANTS, sort_keys=True).encode("utf-8")).hexdigest()


def _sha_obj(x: Any) -> str:
    return hashlib.sha256(json.dumps(x, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


# ------------------------------------------------------------------ per-repetition retention
def raw_name(tid: str, state: str, rep: int, idx: int) -> str:
    """The frozen run_state_v3 JUnit name (same f-string)."""
    return f"{tid}_{state}_r{rep}_f{idx}"


def per_rep_from_raw(raw_dir: Path, tid: str, state: str, test_files: list[str],
                     parse: Callable[[str], tuple[dict, dict]]) -> dict:
    """Rebuild per-node 3-lists from the frozen raw JUnit files (pure given the files)."""
    reps: list[dict[str, str]] = [dict() for _ in range(REPS)]
    merged_fail: dict[str, str] = {}
    raw_hashes: dict[str, str] = {}
    missing: list[str] = []
    parse_errors: list[str] = []
    for rep in range(REPS):
        for idx, tf in enumerate(test_files):
            name = raw_name(tid, state, rep, idx)
            p = raw_dir / f"{name}.xml"
            text = p.read_text(encoding="utf-8", errors="replace") if p.exists() else NO_FILE
            raw_hashes[name] = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if NO_FILE in text[:20]:
                reps[rep][tf] = "error"
                merged_fail[tf] = f"JUNIT_MISSING_R{rep}_F{idx}"
                missing.append(name)
                continue
            try:
                nodes, fails = parse(text)
            except Exception as exc:  # noqa: BLE001 - recorded, then treated as infrastructure
                parse_errors.append(f"{name}: {type(exc).__name__}: {exc}"[:300])
                continue
            reps[rep].update(nodes)
            merged_fail.update(fails)
    universe = sorted(set().union(*[set(r) for r in reps]))
    lists = {n: [reps[r].get(n, "missing") for r in range(REPS)] for n in universe}
    return {"junit": lists, "junit_failures": merged_fail, "raw_hashes": raw_hashes,
            "missing_junit": missing, "parse_errors": parse_errors}


def run_state_r1(*, run_state: Callable[..., dict], parse: Callable[[str], tuple[dict, dict]],
                 raw_dir: Path, era_key: str, worktree_linux: str, tid: str, state: str,
                 test_files: list[str], install_fragment: str, locked_dev_fragment: str,
                 timeout_s: int = 7200) -> dict:
    """Call the frozen run_state_v3 unchanged (with raw_junit_dir) and retain repetitions."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    res = run_state(era_key=era_key, worktree_linux=worktree_linux, tid=tid, state=state,
                    test_files=test_files, install_fragment=install_fragment,
                    locked_dev_fragment=locked_dev_fragment, raw_junit_dir=str(raw_dir),
                    timeout_s=timeout_s)
    out = dict(res)
    out["frozen_junit_last_rep"] = res.get("junit", {})
    err = res.get("error")
    tail = res.get("stdout_tail", "") or ""
    out["container_complete"] = "ALL_RUNS_DONE" in tail
    out["infra_reason"] = ""
    if err in INFRA_ERRORS:
        out["infra_reason"] = err
    elif err is None and not out["container_complete"]:
        out["infra_reason"] = f"CONTAINER_INCOMPLETE rc={res.get('returncode')}"
    if err is None and not out["infra_reason"]:
        r1 = per_rep_from_raw(raw_dir, tid, state, test_files, parse)
        if r1["parse_errors"]:
            out["infra_reason"] = "JUNIT_PARSE_ERROR"
        out["junit"] = r1["junit"]
        out["junit_failures_r1"] = r1["junit_failures"]
        out["r1"] = {k: r1[k] for k in ("raw_hashes", "missing_junit", "parse_errors")}
        # the merged failure texts and node membership are the frozen ones
        if set(r1["junit"]) != set(res.get("junit", {})) and not r1["parse_errors"]:
            raise OracleInfraError(f"R1 node universe differs from the frozen merge ({tid}/{state})")
    return out


# ------------------------------------------------------------------ classification (verbatim)
def classify_task(tgt: dict, par: dict, classify_node_v2: Callable[..., str],
                  task_eligibility_v2: Callable[..., dict]) -> tuple[dict, list[dict], dict]:
    """Verbatim copy of the phase5.run_task classification loop (identity-tested)."""
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
    flags = task_eligibility_v2(
        n_behavioral_f2p=counts["BEHAVIORAL_F2P"],
        n_symbol_absence_f2p=counts["SYMBOL_ABSENCE_F2P"],
        n_parent_collection_error=counts["PARENT_COLLECTION_ERROR"],
        environment_valid=True,
        task_collection_failure=False,
    )
    return counts, node_records, flags


def frozen_status(tgt: dict, par: dict) -> str:
    """Frozen phase5 terminal status from the two state errors."""
    t_err, p_err = tgt.get("error"), par.get("error")
    if t_err or p_err:
        if t_err == "INSTALL_FAIL" or p_err == "INSTALL_FAIL":
            return "ENV_INSTALL_BLOCKED"
        if t_err == "CLOCK_BLOCKED" or p_err == "CLOCK_BLOCKED":
            return "CLOCK_BLOCKED"
        return "ERROR"
    return "DONE"


# ------------------------------------------------------------------ evidence packing
def pack_raw(raw_root: Path, dest: Path) -> str:
    """Deterministic tar.gz of the raw JUnit tree (sorted names, mtime 0, uid/gid 0)."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        for p in sorted(x for x in raw_root.rglob("*") if x.is_file()):
            data = p.read_bytes()
            info = tarfile.TarInfo(p.relative_to(raw_root).as_posix())
            info.size, info.mtime, info.uid, info.gid, info.mode = len(data), 0, 0, 0, 0o644
            info.uname = info.gname = ""
            tar.addfile(info, io.BytesIO(data))
    gz = io.BytesIO()
    with gzip.GzipFile(fileobj=gz, mode="wb", mtime=0, compresslevel=9) as g:
        g.write(buf.getvalue())
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(gz.getvalue())
    shutil.rmtree(raw_root, ignore_errors=True)
    return hashlib.sha256(gz.getvalue()).hexdigest()


# ------------------------------------------------------------------ one task (no file writes)
def oracle_task(task_id: str, *, parent: str, target: str, era_key: str, raw_root: Path,
                deps: dict[str, Callable[..., Any]],
                between_states: Callable[[str], None] | None = None) -> dict:
    """The frozen phase5 per-task procedure with R1 retention and MAIN inputs.

    `deps` holds the frozen callables (injectable for tests): changed_test_files,
    clock_preflight, target_manifests, ensure_worktrees_v3, lock_install_script,
    locked_dev_install, base_image_id, run_state_v3, parse_junit_with_failures,
    classify_node_v2, task_eligibility_v2, remove_worktrees_v3, v31_dev_closure, lockfile_sha256.
    """
    t0 = time.monotonic()
    test_files = deps["changed_test_files"](parent, target)
    clock = deps["clock_preflight"]()
    if clock["verdict"] == "CLOCK_BLOCKED":
        return {"task_id": task_id, "status": "CLOCK_BLOCKED", "infra_reason": "CLOCK_BLOCKED",
                "clock": clock}
    manifests = deps["target_manifests"](target)
    wts = deps["ensure_worktrees_v3"](task_id, parent, target)
    tid = task_id.split("-")[-1][:12]
    install_t, install_mode, _ = deps["lock_install_script"](wts["t"], manifests)
    install_p, _, _ = deps["lock_install_script"](wts["p"], manifests)
    locked_dev = deps["locked_dev_install"](task_id)
    img_id = deps["base_image_id"](era_key)
    states = {}
    try:
        for st, frag in (("t", install_t), ("p", install_p)):
            if between_states:
                between_states(f"before_{st}")
            ts = time.monotonic()
            states[st] = run_state_r1(run_state=deps["run_state_v3"],
                                      parse=deps["parse_junit_with_failures"],
                                      raw_dir=raw_root / st, era_key=era_key,
                                      worktree_linux=wts[st], tid=tid, state=st,
                                      test_files=test_files, install_fragment=frag,
                                      locked_dev_fragment=locked_dev, timeout_s=7200)
            states[st]["wall_s"] = round(time.monotonic() - ts, 1)
            if between_states:
                between_states(f"after_{st}")
    finally:
        deps["remove_worktrees_v3"](task_id)
    tgt, par = states["t"], states["p"]
    infra = [f"{s}:{states[s]['infra_reason']}" for s in ("t", "p") if states[s].get("infra_reason")]
    status = frozen_status(tgt, par)
    closure = deps["v31_dev_closure"](task_id)
    rec: dict[str, Any] = {
        "task_id": task_id, "rule_id": RULE_ID, "rule_constants_sha256": rule_constants_sha(),
        "era_key": era_key, "parent_commit": parent, "target_commit": target,
        "n_test_files": len(test_files), "test_files": test_files,
        "frozen_status": status, "infra_reasons": infra,
        "install_mode": install_mode, "frozen_base_image_id": img_id,
        "lockfile_sha256": deps["lockfile_sha256"](manifests),
        "dev_test_closure": {"mechanism": closure.get("mechanism"),
                             "n_pins": len(closure.get("pins", [])),
                             "pins_sha256": closure.get("pins_sha256"),
                             "n_unsupported": len(closure.get("unsupported", []))},
        "locked_dev_fragment_sha256": hashlib.sha256(locked_dev.encode("utf-8")).hexdigest(),
        "clock_pre": clock.get("pre", {}).get("median_skew_s"),
        "operations": {s: {"error": states[s].get("error"), "returncode": states[s].get("returncode"),
                           "container_complete": states[s].get("container_complete"),
                           "wall_s": states[s].get("wall_s"), "db_name": states[s].get("db_name"),
                           "r1": states[s].get("r1", {})} for s in ("t", "p")},
    }
    if infra:
        rec["status"] = "INFRA"
    elif status == "DONE":
        counts, node_records, flags = classify_task(tgt, par, deps["classify_node_v2"],
                                                    deps["task_eligibility_v2"])
        rec.update({"status": "DONE", "counts": counts, "eligibility": flags,
                    "classification": ("BEHAVIORAL_F2P" if flags["PRIMARY_BEHAVIORAL_F2P_ELIGIBLE"]
                                       else "NOT_PRIMARY"),
                    "n_nodes": len(node_records), "node_records": node_records,
                    "parent_failure_text_sha256": _sha_obj(par.get("junit_failures", {})),
                    "parent_failure_text": {n: par["junit_failures"][n][:4000]
                                            for n in sorted(par.get("junit_failures", {}))
                                            if any(r["node_id"] == n and r["v3_class"] in
                                                   ("BEHAVIORAL_F2P", "SYMBOL_ABSENCE_F2P",
                                                    "OTHER_REVIEW_REQUIRED")
                                                   for r in node_records)}})
    else:
        rec["status"] = status                     # ENV_INSTALL_BLOCKED (candidate) / CLOCK_BLOCKED / ERROR
    rec["wall_s"] = round(time.monotonic() - t0, 1)
    return rec
