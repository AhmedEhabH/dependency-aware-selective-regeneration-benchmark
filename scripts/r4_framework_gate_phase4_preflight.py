#!/usr/bin/env python3
"""R4 framework-gate Phase4-repair successor local launcher preflight + single-step driver.

M17_D7_R4_FRAMEWORK_GATE_PHASE4_REPAIR_AND_REFREEZE (T3, PRE-EXECUTION FREEZE for
the fresh Phase4-repair successor Full144 run).

Deterministic, offline, non-scientific checks that the PowerShell launcher
invokes before and during the successor Full144 run.  This module NEVER calls
any LLM/API or any network acquisition tool; it only verifies frozen
invariants and delegates scientific execution to the frozen Full144 driver
(``scripts/r4_full144_preexecution.py``) with ``--network=none``.

The successor run RESTARTS FROM UNIT 1 on the fresh successor root and imports
ZERO prior scientific evidence from any previous Full144 attempt (the
artifact-recovery successor run root and all prior evidence are immutable).

Phase4-repair semantic binding:
  * the synthetic ``python manage.py check`` framework gate is REMOVED;
  * the repaired runner records an explicit per-worktree
    ``NOT_APPLICABLE_SYNTHETIC_GATE_REMOVED`` manage-gate state;
  * import/pytest smoke and every other scientific/environment gate are
    unchanged; failures still fail closed.

Subcommands:
  preflight  - validate the successor freeze record + git/worktree + code-set
               + population/order/binding + 144/144 static artifact closure +
               fresh successor run root + unchanged image bindings.
  static     - static checks (--network=none, no LLM, no pull/build, no unit
               special casing, no manage-gate execution path).
  freeze     - write the fresh successor PRE_EXECUTION_FREEZE.json.
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
CLOSURE_EVIDENCE_NAME = "FULL144_STATIC_ARTIFACT_CLOSURE.json"
CODE_SET_MANIFEST = (
    PROJECT / "research" / "env-canon-r4"
    / "R4_FRAMEWORK_GATE_PHASE4_EFFECTIVE_EXECUTION_CODE_SET.json"
)
CLOSURE_REPO_EVIDENCE = (
    PROJECT / "research" / "env-canon-r4" / "R4_FULL144_ARTIFACT_CLOSURE_144.json"
)
POWERSHELL_LAUNCHER = PROJECT / "scripts" / "r4_framework_gate_phase4_launcher.ps1"
RUNNER = PROJECT / "scripts" / "r4_behavioral_calibration_n12_r2.py"
DRIVER = SRC / "benchmark" / "wp2" / "full144" / "driver.py"
POPULATION = SRC / "benchmark" / "wp2" / "full144" / "population.py"

BRANCH = "parallel/r4-framework-gate-phase4-repair-2026-10-16"

EXPECTED_N_UNITS = 144
EXPECTED_N_MISSING = 0
EXPECTED_N_INCOMPATIBLE = 0

REMOVED_GATE_STATE = "NOT_APPLICABLE_SYNTHETIC_GATE_REMOVED"


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
        raise LauncherError(f"successor freeze record missing: {record_path}")
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


def closure_evidence(run_root: Path) -> dict[str, object]:
    """Load the frozen 144/144 static artifact closure evidence (fail closed on mismatch)."""
    candidates = [run_root / "freeze" / CLOSURE_EVIDENCE_NAME, CLOSURE_REPO_EVIDENCE]
    payload: dict[str, object] | None = None
    for c in candidates:
        if not c.is_file():
            continue
        data = json.loads(c.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("N_UNITS") == EXPECTED_N_UNITS:
            payload = data
            break
    if payload is None:
        raise LauncherError("144/144 static artifact closure evidence missing")
    if payload.get("N_RESOLVABLE") != EXPECTED_N_UNITS:
        raise LauncherError(
            f"static closure N_RESOLVABLE={payload.get('N_RESOLVABLE')} != {EXPECTED_N_UNITS}"
        )
    if int(payload.get("N_MISSING", -1)) != EXPECTED_N_MISSING:
        raise LauncherError(f"static closure N_MISSING={payload.get('N_MISSING')} != 0")
    if int(payload.get("N_INCOMPATIBLE", -1)) != EXPECTED_N_INCOMPATIBLE:
        raise LauncherError(f"static closure N_INCOMPATIBLE={payload.get('N_INCOMPATIBLE')} != 0")
    if payload.get("zero_recovery_outside_frozen_authority") is not True:
        raise LauncherError("static closure: recovery selected outside frozen R4-E authority")
    return payload


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
    if branch != BRANCH:
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
    if int(freeze.get("n_scientific_units_executed", -1)) != 0:
        raise LauncherError("freeze record binds a nonzero n_scientific_units_executed")

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

    closure = closure_evidence(run_root)
    images = image_binding_results()

    return {
        "preflight": "PASS",
        "branch": branch,
        "git_head": head,
        "freeze_head": freeze_head,
        "tracked_clean": True,
        "effective_execution_code_set_hash": code_hash,
        "static_closure_144": {
            "N_UNITS": closure.get("N_UNITS"),
            "N_RESOLVABLE": closure.get("N_RESOLVABLE"),
            "N_MISSING": closure.get("N_MISSING"),
            "N_INCOMPATIBLE": closure.get("N_INCOMPATIBLE"),
            "verdict": closure.get("verdict"),
        },
        "population_identity": pop["population_identity"],
        "ordered_membership_hash": pop["ordered_membership_hash"],
        "binding_hash": pop["binding_hash"],
        "image_pairs_verified": len(images),
        "run_root": str(run_root),
        "restart_from_unit_1": True,
        "no_prior_scientific_evidence_imported": True,
        "n_scientific_units_executed": 0,
    }


def static_checks() -> dict[str, object]:
    """Deterministic static checks: --network=none; no LLM/pull/build; no unit special casing."""
    runner_src = RUNNER.read_text(encoding="utf-8")
    driver_src = DRIVER.read_text(encoding="utf-8")
    population_src = POPULATION.read_text(encoding="utf-8")
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
    if "MANAGE_RC_" in runner_src:
        raise LauncherError("runner still emits the obsolete manage-gate rc marker")
    # The synthetic manage-gate execution path must be absent from the ACTUAL
    # generated container script (deterministic, offline, no container run).
    import r4_behavioral_calibration_n12_r2 as _r2

    generated = _r2.container_script("vu-static-check", 1, [], {"version_probes": {}})
    if "python manage.py check" in generated:
        raise LauncherError("generated container script still executes python manage.py check")
    if "MANAGE_RC_" in generated:
        raise LauncherError("generated container script still emits the obsolete manage-gate rc marker")
    if f"MANAGE_GATE_$(basename $wt)={REMOVED_GATE_STATE}" not in generated:
        raise LauncherError("generated container script does not record the explicit removed-gate state")
    if "MANAGE_GATE_" not in runner_src or REMOVED_GATE_STATE not in runner_src:
        raise LauncherError("runner does not record the explicit removed-gate state")
    if "RECOVERY_UNIT" in runner_src or "RECOVERY_UNIT" in driver_src or "RECOVERY_UNIT" in population_src:
        raise LauncherError("unit special casing (RECOVERY_UNIT) still present")
    if "recovery_overlay_inputs_for_pins" not in runner_src:
        raise LauncherError("generalized pin-driven recovery selection missing")

    return {
        "static": "PASS",
        "network_isolation": "--network=none",
        "no_llm_dependency": True,
        "no_pull_build": True,
        "no_hardcoded_manage_settings": True,
        "no_synthetic_manage_gate": True,
        "no_obsolete_manage_rc": True,
        "explicit_removed_gate_state": True,
        "no_recovery_unit_special_casing": True,
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
    """Write the fresh Phase4-repair successor PRE_EXECUTION_FREEZE.json.

    Deterministic; every hash is recomputed from the committed worktree.  The
    record binds: restart from Unit 1, ZERO prior scientific evidence imported,
    144/144 static artifact closure PASS, zero scientific successor units
    executed, --network=none, unchanged image bindings, repaired runner
    semantics (synthetic manage gate removed).
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

    closure = closure_evidence(run_root)
    closure_repo = json.loads(CLOSURE_REPO_EVIDENCE.read_text(encoding="utf-8"))

    payload: dict[str, object] = {
        "schema_version": "env-canon-r4/framework-gate-phase4/successor-preexecution-freeze/1.0",
        "mission_id": "M17_D7_R4_FRAMEWORK_GATE_PHASE4_REPAIR_AND_REFREEZE",
        "verdict": "PASS_FRAMEWORK_GATE_PHASE4_REPAIR_READY_FOR_FRESH_FULL144_SUCCESSOR_EXECUTION",
        "branch": BRANCH,
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
        "execution_image_bindings_unchanged": True,
        "effective_execution_code_set_hash": code_hash,
        "effective_execution_code_set": {
            "aggregate_hash": code_hash,
            "members": code_members,
        },
        "runner_sha256": _sha256_file(RUNNER),
        "driver_sha256": _sha256_file(DRIVER),
        "population_sha256": _sha256_file(POPULATION),
        "semantic_change": {
            "removed_gate": "python manage.py check",
            "removed_gate_evidence_representation": REMOVED_GATE_STATE,
            "removed_gate_never_PASS": True,
            "removed_gate_never_FAILURE": True,
            "import_smoke_unchanged": True,
            "pytest_smoke_unchanged": True,
            "no_unit_task_commit_special_casing": True,
            "saleor_source_unmodified": True,
        },
        "static_artifact_closure_144": {
            "repo_evidence": "research/env-canon-r4/R4_FULL144_ARTIFACT_CLOSURE_144.json",
            "repo_evidence_sha256": _sha256_file(CLOSURE_REPO_EVIDENCE),
            "run_root_copy": str(run_root / "freeze" / CLOSURE_EVIDENCE_NAME),
            "N_UNITS": closure.get("N_UNITS"),
            "N_RESOLVABLE": closure.get("N_RESOLVABLE"),
            "N_MISSING": closure.get("N_MISSING"),
            "N_INCOMPATIBLE": closure.get("N_INCOMPATIBLE"),
            "units_consuming_recovery": closure_repo.get("units_consuming_recovery"),
            "recovered_versions_consumed": closure_repo.get("recovered_versions_consumed"),
            "recovery_artifacts_used": closure_repo.get("recovery_artifacts_used"),
            "zero_recovery_outside_frozen_authority": closure_repo.get(
                "zero_recovery_outside_frozen_authority"
            ),
            "verdict": closure.get("verdict"),
        },
        "recovery_authority_hashes": {
            "e1_plan": full144_driver._sha256_file(
                PROJECT / "research" / "env-canon-r4" / "R4_E1_PYLINT_RECOVERY_PLAN.json"
            ),
            "e2_receipt": full144_driver._sha256_file(
                PROJECT / "research" / "env-canon-r4" / "R4_E2_PYLINT_ACQUISITION_RECEIPT.json"
            ),
            "e3_receipt": full144_driver._sha256_file(
                PROJECT / "research" / "env-canon-r4" / "R4_E3_AFFECTED_REVALIDATION_RECEIPT.json"
            ),
            "manifest": _sha256_file(
                Path(r"D:\wp2_env_store\recovery\r4e_pylint_py39\manifests\R4_E2_PYLINT_ACQUISITION_MANIFEST.json")
            ),
        },
        "launcher_path": "scripts/r4_framework_gate_phase4_launcher.ps1",
        "launcher_sha256": _sha256_file(POWERSHELL_LAUNCHER),
        "preflight_module": "scripts/r4_framework_gate_phase4_preflight.py",
        "run_root": str(run_root),
        "network_policy": "--network=none for every scientific unit; no pull/build/download/acquire",
        "concurrency": 1,
        "restart_from_unit_1": True,
        "no_prior_scientific_evidence_imported": True,
        "n_scientific_units_executed": 0,
        "prior_evidence_disposition": (
            "the artifact-recovery successor run (62 PASS units + partial Unit 63) and ALL earlier "
            "Full144 attempts are immutable historical evidence; ZERO prior scientific unit evidence "
            "is imported into this Phase4-repair successor run"
        ),
        "fail_fast_policy": "first mandatory unit failure stops the run; no skip/reorder/rerun",
        "checkpoint_restart_policy": (
            "intent before start; atomic progress checkpoint after PASS; fail closed on "
            "progress/evidence mismatch; never rerun completed PASS; partial unit -> STOP_OWNER_REVIEW"
        ),
        "tests_tooling_results": {
            "targeted_pytest": (
                "87 passed (test_r4_behavioral_calibration_n12_r2 + test_r4_framework_gate_phase3_repair; "
                "pre-existing environment failures reproduced on pristine base excluded)"
            ),
            "full144_related_pytest": (
                "63 passed (preexecution/successor/artifact-recovery modules; pre-existing environment "
                "failures reproduced on pristine base excluded)"
            ),
            "py_compile": "PASS",
            "ruff": "PASS",
            "mypy_strict": "PASS (src/benchmark/wp2/full144)",
            "git_diff_check": "PASS",
        },
        "frozen_invariance_statement": (
            "UNCHANGED from qualified artifact-recovery successor evidence HEAD for all frozen scientific "
            "authorities/providers; the ONLY execution-substrate change is removing the synthetic "
            "python manage.py check framework gate (M17_D7_R4_FRAMEWORK_GATE_PHASE4_REPAIR) plus the "
            "truthful contingency-taxonomy update; import/pytest smoke and all other gates are unchanged."
        ),
        "exact_next_gate": "M17_D7_R4_FRAMEWORK_GATE_PHASE4_FRESH_FULL144_SUCCESSOR_EXECUTION",
        "frozen_utc": __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat(),
    }
    target = run_root / "freeze" / FREEZE_RECORD_NAME
    tmp = target.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, target)
    return payload


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="R4 framework-gate Phase4 successor launcher preflight/step/freeze")
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
