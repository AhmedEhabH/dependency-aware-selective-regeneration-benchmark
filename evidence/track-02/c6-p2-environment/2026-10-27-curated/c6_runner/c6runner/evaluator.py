# -*- coding: utf-8 -*-
"""Separate evaluation-only oracle evaluator (C6 reference runs).

Reference SEMANTICS (issue 2 — negative/positive roles):
  - diagnostic   = P code + P tests            (starting environment, evidence
                   only; NEVER a PASS source)
  - F2P baseline  = P code + T test bytes        (negative control / expected
                   fail; evaluation-only, separate dir)
  - P2P reference = T code + T test bytes        (positive reference / expected
                   pass; evaluation-only, separate dir)
  - generated code + evaluation tests = a FUTURE E2E gate, NOT implemented.

The F2P and P2P runs each execute in a SEPARATE evaluator process/container
and SEPARATE directory (never in the task input tree). The frozen TaskPlan is
passed THROUGH to run_limited (finding F1) so the docker backend receives
plan.image_digest / resources / junitxml_path. The candidate verdict NEVER
rests on the P tests alone and an EXPECTED F2P failure is recorded as the
negative-baseline outcome, never as a broken environment.
"""
import os
import shutil

from .errors import Blocked
from .resources import ResourceLimits, run_limited
from .oracle import parse_junit_report

P_AVAILABLE_ONLY = "__P_AVAILABLE_ONLY__"

# oracle_mode -> evaluation role label
ROLE_BY_MODE = {"POSITIVE_REFERENCE": "p2p",
                "NEG_TESTS_EXPECTED_FAIL": "f2p",
                "NONE": None}

TREE_SEMANTICS = {
    "f2p": "P code + T test bytes (negative baseline F2P, expected failure; "
            "evaluation-only)",
    "p2p": "T code + T test bytes (positive reference P2P, expected pass; "
            "evaluation-only)",
}


class ReferenceEvaluation:
    """Result of one reference evaluation (serializable evidence + objects)."""

    def __init__(self, run, junit_report, evidence, role=None, error=None):
        self.run = run            # resources.RunResult of the reference run
        self.junit_report = junit_report  # oracle.JunitReport or None
        self.evidence = evidence  # serializable dict
        self.role = role          # "f2p" | "p2p" | None
        self.error = error        # exception string when infra failed


def _arg_to_contract_path(token, contract_paths):
    t = str(token).split("::")[0]
    if t in contract_paths:
        return t
    for c in contract_paths:
        if c.replace("/", ".") == t or c[:-3].replace("/", ".") == t:
            return c
    return None


def expand_contract_in_command(command, contract_paths, subset=None):
    """Return the argv exercising exactly `subset` of the frozen contract.

    - subset=None -> the FULL M/A contract (reference run): contract path
      tokens are kept verbatim, missing contract files are appended as
      repo-relative paths so the whole contract is covered.
    - subset=paths -> the prospective-input run: contract path tokens whose
      file does not exist at P (T-only paths) are DROPPED (they are not part
      of the pre-change input); if no contract token exists the subset is
      appended.
    """
    argv = [str(a) for a in command]
    allowed = set(subset) if subset is not None else None
    found = set()
    out = []
    for a in argv:
        c = _arg_to_contract_path(a, contract_paths)
        if c is not None:
            if allowed is None or c in allowed:
                out.append(a)
                found.add(c)
            # else: dropped — T-only target not part of the P input run
        else:
            out.append(a)
    target = sorted(allowed) if allowed is not None else sorted(contract_paths)
    missing = [c for c in target if c not in found]
    out = out + missing
    return out


def _build_reference_tree(ws, git_dir, code_rev, contract_paths, dst=None):
    """Direct-call fallback (unit harness): P bytes from ws/src copy +
    whatever oracle bytes exist (missing ones keep the P bytes).
    `code_rev` is accepted for API symmetry; the harness has no git store
    so it can only reconstruct the P-code form."""
    dst = dst or ws.eval_work
    for p in contract_paths:
        out = os.path.join(dst, p)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        src_oracle = os.path.join(ws.oracle, p)
        if os.path.exists(src_oracle):
            shutil.copy2(src_oracle, out)
        else:
            src_p = os.path.join(ws.src, p)
            if os.path.exists(src_p):
                os.makedirs(os.path.dirname(out), exist_ok=True)
                shutil.copy2(src_p, out)


def _reference_limits(plan):
    r = plan.resources
    return ResourceLimits(timeout_s=float(r.get("timeout_s", 1800)),
                          ram_mb=float(r.get("ram_mb", 16384)),
                          disk_mb=float(r.get("disk_mb", 5120)))


def evaluate_t_only(ws, t_only_paths, plan, backend, git_dir=None,
                    parent=None, code_rev=None, role=None,
                    dst=None) -> ReferenceEvaluation:
    """Run ONE role of the M/A reference evaluation in the separate evaluator.

    Layout:
      role="f2p" -> ws.eval_f2p  = P code + T test bytes (negative baseline)
      role="p2p" -> ws.eval_work = T code + T test bytes (positive reference)
      cwd                = the role tree
      logs / scratch     = ws.eval_logs / ws.eval_scratch
    The frozen command runs against the reference tree; the junit-xml report
    written inside the sandbox becomes the machine-readable oracle evidence.

    `role` defaults from plan.oracle_mode; `code_rev` defaults to parent (the
    F2P form) for direct-call harnesses. The runner always passes explicit
    role + code_rev (parent for F2P, task_sha for P2P).
    """
    if role is None:
        role = ROLE_BY_MODE.get(plan.oracle_mode)
    tree_dir = dst or (ws.eval_f2p if role == "f2p" else ws.eval_work)
    if not os.path.isdir(tree_dir):
        raise Blocked("reference tree missing", tree_dir)
    contract_paths = sorted(set(list(plan.test_paths) + list(t_only_paths)))
    if git_dir and (code_rev or parent):
        ws.materialize_reference_tree(git_dir, code_rev or parent,
                                      contract_paths, dst=tree_dir)
    else:
        _build_reference_tree(ws, git_dir, parent, contract_paths,
                              dst=tree_dir)

    ref_cmd = expand_contract_in_command(plan.command, contract_paths,
                                         subset=None)
    run = run_limited(ref_cmd, tree_dir, _reference_limits(plan),
                      ws.eval_logs, offline_gate=True, backend=backend,
                      scratch_dir=ws.eval_scratch, plan=plan)

    junit_report = None
    stdout_txt = ""
    try:
        with open(run.stdout_path, "rb") as f:
            stdout_txt = f.read(1 << 20).decode("utf-8", "replace")
    except (OSError, AttributeError):
        pass
    if run.junit_path is not None:
        junit_report = parse_junit_report(run.junit_path, stdout_txt,
                                          run.exit_code, contract_paths)

    from .hashes import sha256_file

    def _dg(p):
        try:
            return sha256_file(p)
        except OSError:
            return None

    evidence = {
        "kind": "reference_evaluation",
        "role": role,
        "tree_semantics": TREE_SEMANTICS.get(role or ""),
        "reference_dir": tree_dir,
        "evaluator": "separate process and separate directory; evaluation-only "
                     "reference tree (no T bytes in the prospective input)",
        "contract": contract_paths,
        "effective_command": list(ref_cmd),
        "exit_code": run.exit_code,
        "wall_s": round(run.wall_s, 3) if run.wall_s is not None else None,
        "timeout": run.timeout,
        "resource_overflow": run.resource_overflow,
        "blocked_reason": run.blocked_reason,
        "python_gate_active": run.python_gate_active,
        "os_isolation_active": run.os_isolation_active,
        "network_enforced": run.network_enforced,
        "stdout_sha256": _dg(run.stdout_path),
        "stderr_sha256": _dg(run.stderr_path),
        "junit_path": run.junit_path,
        "junit_sha256": run.junit_sha256,
        "cleanup": run.cleanup_evidence,
    }
    if junit_report is not None:
        evidence["junit_report"] = junit_report.as_dict()
    return ReferenceEvaluation(run, junit_report, evidence, role=role)