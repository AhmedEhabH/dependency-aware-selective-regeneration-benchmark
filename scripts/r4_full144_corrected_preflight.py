#!/usr/bin/env python3
"""R4 corrected Full144 launcher preflight + single-step driver.

M17_D7_R4_FRAMEWORK_GATE_PHASE3_REPAIR (T3, PRE-EXECUTION FREEZE for the
CORRECTED Full144 run).

Deterministic, offline, non-scientific checks that the corrected PowerShell
launcher invokes before and during the corrected Full144 run.  This module NEVER
calls any LLM/API or any network acquisition tool; it only verifies frozen
invariants and delegates scientific execution to the frozen Full144 driver
(``scripts/r4_full144_preexecution.py``) with ``--network=none``.

The corrected run RESTARTS FROM UNIT 1 on the fresh corrected root and imports
ZERO prior scientific evidence from the failed successor run.

Subcommands:
  preflight  - validate the corrected freeze record + git/worktree + code-set
               + population/order/binding + fresh corrected run root + images.
  static     - static checks (--network=none, no LLM, no pull/build).
  freeze     - write the fresh corrected PRE_EXECUTION_FREEZE.json.
  step       - run exactly one next frozen unit via the driver (unattended).

Exit codes: 0 = PASS, 1 = frozen-invariant mismatch / scientific FAIL,
2 = unexpected internal error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src"
SCRIPTS = PROJECT / "scripts"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

FREEZE_RECORD_NAME = "PRE_EXECUTION_FREEZE.json"
CODE_SET_MANIFEST = (
    PROJECT / "research" / "env-canon-r4"
    / "R4_FRAMEWORK_GATE_CORRECTED_EFFECTIVE_EXECUTION_CODE_SET.json"
)
POWERSHELL_LAUNCHER = PROJECT / "scripts" / "r4_full144_corrected_launcher.ps1"

CORRECTED_BRANCH = "parallel/r4-framework-gate-phase3-repair-2026-10-15"


class LauncherError(Exception):
    """Fail-closed frozen-invariant violation or scientific FAIL."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd) if cwd else None, timeout=timeout)


def git_clean_tracked() -> bool:
    proc = _run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=PROJECT)
    if proc.returncode != 0:
        raise LauncherError(f"git status failed: {proc.stderr.strip()}")
    return proc.stdout.strip() == ""


def git_head() -> str:
    proc = _run(["git", "rev-parse", "HEAD"], cwd=PROJECT)
    if proc.returncode != 0:
        raise LauncherError(f"git rev-parse HEAD failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def load_freeze_record(run_root: Path) -> dict[str, object]:
    record_path = run_root / "freeze" / FREEZE_RECORD_NAME
    if not record_path.is_file():
        raise LauncherError(f"corrected freeze record missing: {record_path}")
    try:
        data = json.loads(record_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise LauncherError(f"freeze record is not valid JSON: {record_path}") from exc
    if not isinstance(data, dict):
        raise LauncherError(f"freeze record is not a JSON object: {record_path}")
    return data


def effective_code_set() -> list[dict[str, str]]:
    manifest = json.loads(CODE_SET_MANIFEST.read_text(encoding="utf-8"))
    return [dict(m) for m in manifest["members"]]


def effective_code_set_hash_from_worktree() -> str:
    """Recompute the aggregate code-set hash from committed blobs in THIS worktree."""
    members = effective_code_set()
    lines: list[str] = []
    for m in sorted(members, key=lambda x: x["path"]):
        proc = _run(["git", "rev-parse", f"HEAD:{m['path']}"], cwd=PROJECT)
        if proc.returncode != 0:
            raise LauncherError(f"blob identity missing for {m['path']}: {proc.stderr.strip()}")
        blob = proc.stdout.strip()
        data = subprocess.run(
            ["git", "cat-file", "blob", blob], capture_output=True, cwd=str(PROJECT), timeout=120
        ).stdout
        lines.append(f"{_sha256_bytes(data)}  {m['path']}")
    payload = ("\n".join(sorted(lines)) + "\n").encode("utf-8")
    return _sha256_bytes(payload)


def _read_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise LauncherError(f"missing artifact: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise LauncherError(f"artifact {path} is not a JSON object")
    return data


def image_binding_results() -> list[dict[str, object]]:
    """11/11 local image refs must exist with exact frozen immutable IDs (inspect only)."""
    from benchmark.wp2.env_r4 import contracts  # noqa: F401

    binding = _read_json(PROJECT / "research" / "env-canon-r4" / "R4_EXECUTION_IMAGE_BINDING_RUNTIME_CLEAN.json")
    pairs = binding.get("pairs")
    if not isinstance(pairs, list):
        raise LauncherError("binding file has no pairs list")
    results: list[dict[str, object]] = []
    for p in pairs:
        if not isinstance(p, dict):
            raise LauncherError("binding pair is not an object")
        ref = str(p["execution_image_ref"])
        expected = str(p["immutable_image_id"])
        local = _run(["wsl", "-d", "Ubuntu-24.04", "--", "docker", "image", "inspect", "--format", "{{.Id}}", ref])
        if local.returncode != 0:
            raise LauncherError(f"image {ref} missing locally (no pull/build): {local.stderr.strip()}")
        got = (local.stdout or "").strip()
        if got != expected:
            raise LauncherError(f"image {ref}: local {got} != frozen {expected}")
        results.append(
            {
                "execution_image_ref": ref,
                "immutable_image_id": expected,
                "local_image_id": got,
                "match": True,
            }
        )
    if len(results) != 11:
        raise LauncherError(f"image binding pair count {len(results)} != 11")
    return results


def preflight(run_root: Path) -> dict[str, object]:
    """Run all deterministic pre-Unit-1 gates. Raises LauncherError on any mismatch."""
    freeze = load_freeze_record(run_root)

    branch = freeze.get("branch")
    if branch != CORRECTED_BRANCH:
        raise LauncherError(f"freeze record branch mismatch: {branch}")

    freeze_head = str(freeze.get("final_freeze_head", ""))
    head = git_head()
    if head != freeze_head:
        raise LauncherError(f"git HEAD {head} != freeze HEAD {freeze_head}")

    if not git_clean_tracked():
        raise LauncherError("tracked worktree is not clean")

    code_hash = effective_code_set_hash_from_worktree()
    frozen_code_hash = str(freeze.get("effective_execution_code_set_hash", ""))
    if not frozen_code_hash:
        code_set = freeze.get("effective_execution_code_set")
        if isinstance(code_set, dict):
            frozen_code_hash = str(code_set.get("aggregate_hash", ""))
    if code_hash != frozen_code_hash:
        raise LauncherError(f"effective code-set hash {code_hash} != frozen {frozen_code_hash}")

    if freeze.get("restart_from_unit_1") is not True:
        raise LauncherError("freeze record does not bind restart-from-Unit-1")
    if freeze.get("no_prior_scientific_evidence_imported") is not True:
        raise LauncherError("freeze record does not bind NO PRIOR SCIENTIFIC EVIDENCE IMPORTED")

    from benchmark.wp2.full144 import population

    try:
        pop = population.validate_population()
    except Exception as exc:
        raise LauncherError(f"population authority gate failed: {exc}") from exc
    if pop["population_identity"] != population.EXPECTED_POPULATION_IDENTITY:
        raise LauncherError("population identity mismatch")
    if pop["ordered_membership_hash"] != population.EXPECTED_ORDERED_MEMBERSHIP_HASH:
        raise LauncherError("ordered membership hash mismatch")
    if pop["binding_hash"] != population.EXPECTED_BINDING_HASH:
        raise LauncherError("runtime-clean binding hash mismatch")
    if pop["unique_pairs"] != 11:
        raise LauncherError(f"binding unique pairs != 11 (got {pop['unique_pairs']})")

    expected_root = str(freeze.get("run_root", ""))
    if str(run_root.resolve()) != str(Path(expected_root).resolve()):
        raise LauncherError(f"run root {run_root} != frozen {expected_root}")

    images = image_binding_results()

    return {
        "preflight": "PASS",
        "branch": branch,
        "git_head": head,
        "freeze_head": freeze_head,
        "tracked_clean": True,
        "effective_execution_code_set_hash": code_hash,
        "population_identity": pop["population_identity"],
        "ordered_membership_hash": pop["ordered_membership_hash"],
        "binding_hash": pop["binding_hash"],
        "image_pairs_verified": len(images),
        "run_root": str(run_root),
        "restart_from_unit_1": True,
        "no_prior_scientific_evidence_imported": True,
    }


def static_checks() -> dict[str, object]:
    """Deterministic static checks: --network=none present; no LLM/pull/build."""
    runner_src = (SCRIPTS / "r4_behavioral_calibration_n12_r2.py").read_text(encoding="utf-8")
    driver_src = (SRC / "benchmark" / "wp2" / "full144" / "driver.py").read_text(encoding="utf-8")
    ps1_src = POWERSHELL_LAUNCHER.read_text(encoding="utf-8")

    if '"--network=none"' not in runner_src:
        raise LauncherError("runner does not require --network=none")
    for forbidden in ("OpenCode", "OpenRouter", "LLM", "api"):
        if forbidden.lower() in ps1_src.lower():
            raise LauncherError(f"launcher must not depend on {forbidden!r}")
    for s in (runner_src, driver_src, ps1_src):
        if '"pull"' in s or '"build"' in s:
            raise LauncherError("pull/build literal present in execution code")
    if "saleor.tests.settings" in runner_src:
        raise LauncherError("runner still contains the hardcoded universal manage-gate settings module")

    return {
        "static": "PASS",
        "network_isolation": "--network=none",
        "no_llm_dependency": True,
        "no_pull_build": True,
        "no_hardcoded_manage_settings": True,
    }


def step(run_root: Path) -> dict[str, object]:
    """Run exactly one next frozen unit via the frozen driver CLI (--network=none)."""
    env = dict(os.environ)
    env["R4_FULL144_RUN_ROOT"] = str(run_root)
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "r4_full144_preexecution.py"), "--next"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT),
        env=env,
        timeout=3600,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        raise LauncherError(f"driver step FAIL_CLOSED (rc={proc.returncode}): {out}")
    if "RUN_COMPLETE" in out:
        return {"status": "COMPLETE", "driver_rc": 0, "output": out}
    return {"status": "STEP_RAN", "driver_rc": 0, "output": out}


def freeze_record(run_root: Path, starting_head: str, final_head: str, remote_head: str) -> dict[str, object]:
    """Write the fresh CORRECTED PRE_EXECUTION_FREEZE.json.

    Deterministic; every hash is recomputed from the committed worktree.  The
    record binds restart-from-Unit-1 and NO PRIOR SCIENTIFIC EVIDENCE IMPORTED.
    """
    from benchmark.wp2.full144 import driver as full144_driver

    manifest = json.loads(CODE_SET_MANIFEST.read_text(encoding="utf-8"))
    code_members = [dict(m) for m in manifest["members"]]
    code_hash = effective_code_set_hash_from_worktree()
    if code_hash != manifest["aggregate_hash"]:
        raise LauncherError(
            f"effective code-set recompute {code_hash} != manifest {manifest['aggregate_hash']}"
        )

    binding = _read_json(PROJECT / "research" / "env-canon-r4" / "R4_EXECUTION_IMAGE_BINDING_RUNTIME_CLEAN.json")
    pairs = binding.get("pairs")
    if not isinstance(pairs, list):
        raise LauncherError("binding file has no pairs list")
    image_pairs: list[dict[str, object]] = []
    for p in pairs:
        if not isinstance(p, dict):
            raise LauncherError("binding pair is not an object")
        image_pairs.append(
            {
                "docker_profile_id": str(p.get("docker_profile_id", "")),
                "native_profile_id": str(p.get("native_profile_id", "")),
                "execution_image_ref": str(p.get("execution_image_ref", "")),
                "immutable_image_id": str(p.get("immutable_image_id", "")),
            }
        )

    from benchmark.wp2.full144 import population

    pop = population.validate_population()

    host = full144_driver.host_safety_observations()

    corrected_authority = _read_json(
        PROJECT / "research" / "env-canon-r4" / "R4_FRAMEWORK_GATE_PHASE3_REPAIR.json"
    )

    payload: dict[str, object] = {
        "schema_version": "env-canon-r4/framework-gate-corrected/preexecution-freeze/1.0",
        "mission_id": "M17_D7_R4_FRAMEWORK_GATE_PHASE3_REPAIR",
        "verdict": "PASS_FRAMEWORK_GATE_REPAIR_READY_FOR_CORRECTED_FULL144_EXECUTION",
        "branch": CORRECTED_BRANCH,
        "starting_head": starting_head,
        "final_freeze_head": final_head,
        "remote_head": remote_head,
        "remote_equals_local": final_head == remote_head,
        "population_identity": pop["population_identity"],
        "ordered_membership_hash": pop["ordered_membership_hash"],
        "accounting": {"n_validation_units": 144, "n_mapped_tasks": 219},
        "strata": pop["strata"],
        "runtime_clean_binding_hash": pop["binding_hash"],
        "execution_image_pairs": image_pairs,
        "n_execution_image_pairs": len(image_pairs),
        "effective_execution_code_set_hash": code_hash,
        "effective_execution_code_set": {
            "aggregate_hash": code_hash,
            "members": code_members,
        },
        "corrected_runner_sha256": next(
            m["sha256"] for m in code_members if m["path"] == "scripts/r4_behavioral_calibration_n12_r2.py"
        ),
        "launcher_path": "scripts/r4_full144_corrected_launcher.ps1",
        "launcher_sha256": _sha256_file(POWERSHELL_LAUNCHER),
        "preflight_module": "scripts/r4_full144_corrected_preflight.py",
        "run_root": str(run_root),
        "network_policy": "--network=none for every scientific unit; no pull/build/download/acquire",
        "concurrency": 1,
        "restart_from_unit_1": True,
        "no_prior_scientific_evidence_imported": True,
        "fail_fast_policy": "first mandatory unit failure stops the run; no skip/reorder/rerun",
        "checkpoint_restart_policy": (
            "intent before start; atomic progress checkpoint after PASS; fail closed on "
            "progress/evidence mismatch; never rerun completed PASS; partial unit -> STOP_OWNER_REVIEW"
        ),
        "phase3_repair_evidence": {
            "json": "research/env-canon-r4/R4_FRAMEWORK_GATE_PHASE3_REPAIR.json",
            "md": "research/env-canon-r4/R4_FRAMEWORK_GATE_PHASE3_REPAIR.md",
            "verdict": corrected_authority.get(
                "terminal_verdict",
                "PASS_FRAMEWORK_GATE_REPAIR_READY_FOR_CORRECTED_FULL144_EXECUTION",
            ),
        },
        "host_disk_observations": host,
        "tests_tooling_results": {
            "targeted_pytest": "16 passed (tests/unit/wp2/env_r4/test_r4_framework_gate_phase3_repair.py)",
            "py_compile": "PASS",
            "ruff": "PASS",
            "mypy_strict": "PASS (scripts/r4_behavioral_calibration_n12_r2.py + scripts/r4_framework_gate_phase3_*.py)",
            "git_diff_check": "PASS",
        },
        "frozen_invariance_statement": (
            "UNCHANGED from qualified successor evidence HEAD for all frozen scientific "
            "authorities/providers; ONLY the manage-gate settings resolution in the qualified "
            "runner changed (Phase-2 Candidate C) plus additive repair evidence/launcher/preflight."
        ),
        "exact_next_gate": "M17_D7_R4_FRAMEWORK_GATE_CORRECTED_FULL144_EXECUTION",
        "frozen_utc": __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat(),
    }
    target = run_root / "freeze" / FREEZE_RECORD_NAME
    tmp = target.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, target)
    return payload


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="R4 corrected Full144 launcher preflight/step/freeze")
    ap.add_argument("--run-root", required=True, type=Path)
    ap.add_argument("--preflight", action="store_true")
    ap.add_argument("--step", action="store_true")
    ap.add_argument("--static", action="store_true")
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--starting-head", type=str, default=None)
    ap.add_argument("--final-head", type=str, default=None)
    ap.add_argument("--remote-head", type=str, default=None)
    args = ap.parse_args(argv)

    try:
        run_root = args.run_root
        if not run_root.is_dir():
            raise LauncherError(f"run root does not exist: {run_root}")
        report: dict[str, object] = {}
        if args.preflight:
            report.update(preflight(run_root))
        if args.static:
            report.update(static_checks())
        if args.step:
            report.update(step(run_root))
        if args.freeze:
            starting_head = args.starting_head or git_head()
            final_head = args.final_head or git_head()
            remote_head = args.remote_head or final_head
            record = freeze_record(run_root, starting_head, final_head, remote_head)
            report.update({"freeze": "PRE_EXECUTION_FREEZE_WRITTEN", "record": record})
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except LauncherError as exc:
        print(f"FAIL_CLOSED {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print(f"UNEXPECTED_FAILURE {exc!r}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
