#!/usr/bin/env python3
"""WP2 M14A-E1 evaluator amendment (brain-authored). ZERO model API.

Why this exists
---------------
Guard G2 in `wp2_m14a_evalcore.py` turns every missing JUnit file into an
infrastructure STOP. That is right when the environment fails. It is wrong when the
*patched tree itself* cannot start pytest: a generated patch that leaves an
undefined name in a Django model module makes `django.setup()` raise inside
pytest-django, pytest exits before the session starts, and no JUnit file is written.
The environment is healthy (the same task's parent and gold trees started pytest
during readiness), so this is a scientific outcome of the patch, not an outage.

The frozen Smoke v2.2 evaluator scored exactly this case as outcome "missing" for
every node (not passed). E1 restores that frozen semantics under a strict,
preregistered signature, and keeps G2 for everything else.

Rule M14A_E1_PATCH_STARTUP_FAILURE_V1 (all conditions required)
  R1 the evaluation container finished (E2E_DONE), as before;
  R2 EVERY active run (each group x repetition) has no JUnit file;
  R3 for every run: the pytest return code is an integer 1..127, the run log exists,
     contains a Python traceback marker and an exception line, and names at least
     one file edited by the patch;
  R4 the task's readiness record shows the parent (empty diff) and gold trees
     started pytest in this environment (gold_empty_ok = true).
If R1-R4 hold: every node of every active group gets ["missing"] * REPS, which the
frozen `score` reads as not passed. Otherwise: EvalInfraError (resumable STOP), as
before. In both cases a diagnostics file with return codes and redacted log tails is
written BEFORE the worktree is removed.

Everything else (materialize, groups, install, pytest command, 3 repetitions,
fresh DB, JUnit parsing, scoring) is byte-for-byte the frozen M14A behaviour.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from scripts.wp2_m14a_evalcore import EvalInfraError  # same class: run.evaluate catches it

RULE_ID = "M14A_E1_PATCH_STARTUP_FAILURE_V1"
PATCH_STARTUP_FAILURE = "PATCH_STARTUP_FAILURE"
ALL_JUNIT_PRESENT = "ALL_JUNIT_PRESENT"
INFRA_PARTIAL_MISSING = "INFRA_PARTIAL_MISSING"
INFRA_UNCLASSIFIED = "INFRA_UNCLASSIFIED"
INFRA_PARENT_UNVERIFIED = "INFRA_PARENT_UNVERIFIED"

TRACEBACK_RE = re.compile(r"Traceback \(most recent call last\)|ImportError while loading conftest"
                          r"|ConftestImportFailure")
EXC_RE = re.compile(r"^\s*(?:E\s+)?(?:[A-Za-z_][\w]*\.)*[A-Za-z_]\w*(?:Error|Exception)\b",
                    re.M)
RC_RE = re.compile(r"^RC_([CU])_(\d+)=(\d+)\s*$", re.M)
DIFF_RE = re.compile(r"^diff --git a/(\S+) b/(\S+)\s*$", re.M)
PLUS_RE = re.compile(r"^\+\+\+ b/(\S+)\s*$", re.M)
SECRET_RE = re.compile(r"postgres(?:ql)?://\S+")
LOG_TAIL_LINES = 80
LOG_LINE_MAX = 400
RULE_CONSTANTS = {
    "rule_id": RULE_ID, "traceback_re": TRACEBACK_RE.pattern, "exception_re": EXC_RE.pattern,
    "rc_range": [1, 127], "require_all_runs_missing": True,
    "require_edited_file_in_log": True, "require_readiness_gold_empty_ok": True,
    "missing_outcome": "missing", "log_tail_lines": LOG_TAIL_LINES,
}


def rule_constants_sha() -> str:
    return hashlib.sha256(json.dumps(RULE_CONSTANTS, sort_keys=True).encode("utf-8")).hexdigest()


def edited_paths(diff_text: str) -> list[str]:
    """Repository-relative paths touched by a unified diff (both sides, no /dev/null)."""
    out: set[str] = set()
    for a, b in DIFF_RE.findall(diff_text or ""):
        out.update((a, b))
    out.update(PLUS_RE.findall(diff_text or ""))
    return sorted(p for p in out if p and p != "/dev/null")


def parse_rcs(container_stdout: str) -> dict[str, int]:
    """{'C_0': rc, ...} from the `echo RC_<g>_<rep>=$?` lines of the runs script."""
    return {f"{g}_{rep}": int(rc) for g, rep, rc in RC_RE.findall(container_stdout or "")}


def redact_tail(log: str) -> list[str]:
    lines = SECRET_RE.sub("postgres://<redacted>", log or "").splitlines()[-LOG_TAIL_LINES:]
    return [x[:LOG_LINE_MAX] for x in lines]


def classify_run(rc: int | None, log: str | None, edited: list[str]) -> dict[str, Any]:
    """R3 for one run. Pure function (unit-tested)."""
    text = log or ""
    refs = sorted(p for p in edited if p and p in text)
    d = {"rc": rc, "log_present": log is not None,
         "rc_in_range": isinstance(rc, int) and 1 <= rc <= 127,
         "traceback": bool(TRACEBACK_RE.search(text)),
         "exception_line": bool(EXC_RE.search(text)),
         "edited_files_in_log": refs}
    d["startup_failure_signature"] = bool(d["log_present"] and d["rc_in_range"] and
                                          d["traceback"] and d["exception_line"] and refs)
    return d


def decide(all_keys: list[str], missing: list[str], per_run: dict[str, dict],
           parent_starts_ok: bool) -> str:
    """R2 + R3 + R4. Pure function (unit-tested)."""
    if not missing:
        return ALL_JUNIT_PRESENT
    if sorted(missing) != sorted(all_keys):
        return INFRA_PARTIAL_MISSING
    if not all(per_run.get(k, {}).get("startup_failure_signature") for k in missing):
        return INFRA_UNCLASSIFIED
    if not parent_starts_ok:
        return INFRA_PARENT_UNVERIFIED
    return PATCH_STARTUP_FAILURE


def _sha_obj(x: Any) -> str:
    return hashlib.sha256(json.dumps(x, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def write_diagnostics(path: Path, d: dict) -> None:
    d = dict(d, artifact="m14a_e1_eval_diagnostics", artifact_sha256="")
    d["artifact_sha256"] = _sha_obj(d)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                    encoding="utf-8", newline="\n")


def evaluate_state_e1(ev: Any, task_id: str, label: str, worktree: str, *, diff_text: str,
                      diag_path: Path, parent_starts_ok: bool) -> dict:
    """Frozen evaluate_state_safe semantics + E1 (see module docstring)."""
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
    decision = ALL_JUNIT_PRESENT
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
            if "E2E_DONE" not in (r.stdout or ""):                     # G2 / R1
                raise EvalInfraError(f"evaluation container did not finish: rc={r.returncode} "
                                     f"{(r.stdout or '')[-600:]}")
            xml: dict[str, str | None] = {}
            for g in active:
                for rep in range(ev.REPS):
                    xml_name = f"{task_id[:12]}_{label[:4]}_{g}_r{rep}.xml"
                    rr = ev.wsl(f"cat {worktree}/{xml_name} 2>/dev/null || echo __NO_FILE__")
                    xml[f"{g}_{rep}"] = None if "__NO_FILE__" in rr.stdout[:20] else rr.stdout
            missing = [k for k, v in xml.items() if v is None]
            if missing:                                                  # E1
                rcs = parse_rcs(r.stdout or "")
                edited = edited_paths(diff_text)
                per_run: dict[str, dict] = {}
                for k in missing:
                    g, rep = k.split("_")
                    lg = ev.wsl(f"cat {worktree}/run_{g}_{rep}.log 2>/dev/null "
                                "|| echo __NO_FILE__").stdout
                    log = None if lg.startswith("__NO_FILE__") else lg
                    c = classify_run(rcs.get(k), log, edited)
                    c["log_sha256"] = hashlib.sha256((log or "").encode("utf-8")).hexdigest()
                    c["log_tail_redacted"] = redact_tail(log or "")
                    per_run[k] = c
                decision = decide(list(xml), missing, per_run, parent_starts_ok)
                write_diagnostics(diag_path, {
                    "rule_id": RULE_ID, "rule_constants_sha256": rule_constants_sha(),
                    "task_id": task_id, "label": label, "decision": decision,
                    "active_runs": sorted(xml), "missing_runs": sorted(missing),
                    "container_rc": r.returncode, "rcs": rcs, "edited_paths": edited,
                    "parent_starts_ok": parent_starts_ok, "per_run": per_run,
                    "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(
                        timespec="seconds").replace("+00:00", "Z")})
                if decision != PATCH_STARTUP_FAILURE:
                    raise EvalInfraError(f"JUnit missing: {sorted(missing)} (E1 decision "
                                         f"{decision}; diagnostics {diag_path.name})")
                for g in active:
                    for n in groups[g]:
                        node_outcomes[n] = ["missing"] * ev.REPS
            else:
                for g in active:
                    for rep in range(ev.REPS):
                        text = xml[f"{g}_{rep}"] or ""
                        jd = ev.E2E_ROOT / "junit" / task_id / label
                        jd.mkdir(parents=True, exist_ok=True)
                        (jd / f"{g}_r{rep}.xml").write_text(text, encoding="utf-8", newline="")
                        junit_files[f"{g}_r{rep}.xml"] = hashlib.sha256(
                            text.encode("utf-8")).hexdigest()
                        outs, _f = parse_junit_with_failures(text)
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
                                                                 if not groups[g]],
            "e1_decision": decision}
