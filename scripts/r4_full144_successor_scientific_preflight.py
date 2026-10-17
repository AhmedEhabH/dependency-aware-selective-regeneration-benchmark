#!/usr/bin/env python3
"""M17_D7_R4 successor scientific Full144 pre-execution launcher preflight.

MISSION: M17_D7_R4_POSTQUAL_SUCCESSOR_PREEXECUTION_FREEZE (T3, PRE-EXECUTION
FREEZE ONLY).  ZERO scientific units executed by this module.

Deterministic, offline, non-scientific checks the PowerShell operator launcher
invokes for Status / Preflight of the scientific Full144 successor run at the
fresh successor root.  Delegates scientific execution to the FROZEN Full144
driver (``r4_full144_preexecution.py --next``) with ``--network=none``; this
module NEVER calls OpenCode / OpenRouter / any LLM / API / network acquisition.

All authority values are verified against the committed frozen R3.1 two-head
binding (SCIENTIFIC_AUTHORITY_HEAD / SUPPORT_EVIDENCE_HEAD), the frozen
execution-code set (72d3d126...), the committed closure authority
(71cc7fb7...), the frozen population/order/image bindings, and the three fresh
R3.1 qualification receipts (TARGETED3 3/3/0, CAL12 12/12/0, FULL144 144/144/0).

Commands:
  status     - compact status of the scientific successor run root (safe).
  preflight  - all authority + receipt + fresh-root gates (zero execution).
  freeze     - write the successor PRE_EXECUTION_FREEZE.json (additive).

Exit codes: 0 = PASS, 1 = fail-closed mismatch, 2 = unexpected internal error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src"
SCRIPTS = PROJECT / "scripts"
R4_DIR = PROJECT / "research" / "env-canon-r4"
R3_DIR = R4_DIR / "r3"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

FREEZE_RECORD_NAME = "PRE_EXECUTION_FREEZE.json"
CODE_SET_MANIFEST = R4_DIR / "R4_PHASE1B_EFFECTIVE_EXECUTION_CODE_SET.json"
AUTHORITY_PATH = R3_DIR / "R3_AUTHORITY_BINDING.json"
CLOSURE_EVIDENCE_FILE = R4_DIR / "R4_PHASE1B_SUCCESSOR_ARTIFACT_CLOSURE_144.json"
CENSUS_PATH = R4_DIR / "R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144.json"
MATRIX_PATH = R4_DIR / "R4_CAPABILITY_MATRIX_DRAFT.json"
BINDING_PATH = R4_DIR / "R4_EXECUTION_IMAGE_BINDING_RUNTIME_CLEAN.json"
POWERSHELL_LAUNCHER = PROJECT / "scripts" / "r4_full144_successor_scientific_launcher.ps1"
RUNNER = PROJECT / "scripts" / "r4_behavioral_calibration_n12_r2.py"
DRIVER = SRC / "benchmark" / "wp2" / "full144" / "driver.py"

# Mission binding -------------------------------------------------------------
BRANCH = "parallel/r4-successor-preexecution-freeze-2026-10-17"
SUCCESSOR_TAG = "m17-d7-r4-successor-preexecution-freeze-2026-10-17"
R3_1_TAG = "m17-d7-r4-population-qualification-harness-r3-1-2026-10-16"
R3_1_RELEASE_HEAD = "b143d12e9117265d024778d7f807eb51d3572613"
SCIENTIFIC_TAG = "m17-d7-r4-framework-gate-phase5-resolution-successor-r1-2026-10-16"
SCIENTIFIC_HEAD = "5171a4e75cfb2064e7758423c146fcd4ca9ee95c"
SUPPORT_HEAD = "beeff152de2307b2067c8cd9f469542ef8200b95"

SEQUENCE_TAG = "m17-d7-r4-population-qualification-harness-r3-1-2026-10-16"

# Frozen authority values (committed single source: R3_AUTHORITY_BINDING.json)
EXPECTED_EXECUTION_CODE_SET = "72d3d1262133505dd3046a78e9fc0130d004cfaf6e8ca89169b67620335584c0"
EXPECTED_CLOSURE_CONTENT = "71cc7fb72e34fbf707e0a7e8052d3ea2d49fc726cb3a16d9d678271f4a6404e1"
EXPECTED_CLOSURE_FOOTPRINT = "8831e9c761e0c6a15da76e789f7b86a175e5bebbf993c9033a1e202239720f34"
EXPECTED_POPULATION = "ce51d2ec0eb28f6b720fbab13a852618e2de0f0a1111a3cc19dc64b1d19defac"
EXPECTED_ORDER = "8eb4a7242e12bb03715adac5fffdea2e4340585843fc137ececd38952ad6a19e"
EXPECTED_IMAGE = "5169c69d45f0761c85792ec182c9e949f58d8c9f5a29355d5a371944293d2ef2"

SCIENTIFIC_ROOT = Path(r"D:\WP2\runs\r4-scientific-full144-successor-2026-10-17")

# Fresh R3.1 receipts (external canonical run roots).
RECEIPTS: dict[str, dict[str, Any]] = {
    "TARGETED3": {
        "root": Path(r"D:\WP2\runs\r4-successor-r3-targeted3-2026-10-16"),
        "counts": (3, 3, 0),
        "membership": "d39710c6101b06f963bdead27958b050ad93912ccfdf98e6af03896d56e4c2fd",
        "manifest": "9626853afe91b8922288f409d93788d92f6a9e9ef613bef77cf61fdbc1a44976",
    },
    "CAL12": {
        "root": Path(r"D:\WP2\runs\r4-successor-r3-cal12-2026-10-16"),
        "counts": (12, 12, 0),
        "membership": "613557a69e43fdfe67e760bd34388f7e4aa333abec37451ff2fa21b6a6e54f87",
        "manifest": "19a2ce61682b03bdd67634ea2881a09b4cc415f36a3c592db64a4ba1c2c7f430",
    },
    "FULL144": {
        "root": Path(r"D:\WP2\runs\r4-successor-r3-qualification144-2026-10-16"),
        "counts": (144, 144, 0),
        "membership": "8eb4a7242e12bb03715adac5fffdea2e4340585843fc137ececd38952ad6a19e",
        "manifest": "f1a3dde720ab855de39702c564427b6e4867c7019bd8ff83ff5d6f55a7866d0f",
    },
}

DISK_STOP_GIB = 120.0
WSL_DISTRO = "Ubuntu-24.04"


class LauncherError(Exception):
    """Fail-closed frozen-invariant violation."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise LauncherError(f"missing artifact: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise LauncherError(f"artifact {path} is not a JSON object")
    return data


def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd) if cwd else None, timeout=timeout)


def utcnow() -> str:
    return datetime.now(UTC).isoformat()


def git_head() -> str:
    p = _run(["git", "rev-parse", "HEAD"], cwd=PROJECT)
    if p.returncode != 0:
        raise LauncherError(f"git rev-parse HEAD failed: {p.stderr.strip()}")
    return p.stdout.strip()


def git_branch() -> str:
    p = _run(["git", "branch", "--show-current"], cwd=PROJECT)
    if p.returncode != 0:
        raise LauncherError(f"git branch failed: {p.stderr.strip()}")
    return p.stdout.strip()


def git_clean_tracked() -> bool:
    p = _run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=PROJECT)
    if p.returncode != 0:
        raise LauncherError(f"git status failed: {p.stderr.strip()}")
    return p.stdout.strip() == ""


def tag_peel(tag: str) -> str | None:
    p = _run(["git", "rev-list", "-n", "1", tag], cwd=PROJECT)
    return p.stdout.strip() if p.returncode == 0 else None


def _is_ancestor(anc: str, desc: str) -> bool:
    p = _run(["git", "merge-base", "--is-ancestor", anc, desc], cwd=PROJECT)
    return p.returncode == 0


def blob_lf_sha256_at(rev: str, relpath: str) -> str:
    blob = subprocess.run(
        ["git", "rev-parse", f"{rev}:{relpath}"], capture_output=True, text=True, cwd=str(PROJECT)
    )
    if blob.returncode != 0:
        raise LauncherError(f"committed blob missing {relpath} at {rev}")
    data = subprocess.run(
        ["git", "cat-file", "blob", blob.stdout.strip()], capture_output=True, cwd=str(PROJECT)
    ).stdout
    return _sha256_bytes(data.replace(b"\r\n", b"\n"))


def effective_code_set_hash() -> str:
    manifest = _read_json(CODE_SET_MANIFEST)
    lines: list[str] = []
    for member in sorted((dict(m) for m in manifest["members"]), key=lambda m: m["path"]):
        lines.append(f"{blob_lf_sha256_at('HEAD', str(member['path']))}  {member['path']}")
    return _sha256_bytes(("\n".join(sorted(lines)) + "\n").encode("utf-8"))


def committed_closure_footprint() -> str:
    c = _read_json(CLOSURE_EVIDENCE_FILE)
    sem = {
        "N_UNITS": c["N_UNITS"],
        "N_RESOLVABLE": c["N_RESOLVABLE"],
        "N_MISSING": c["N_MISSING"],
        "N_INCOMPATIBLE": c["N_INCOMPATIBLE"],
        "verdict": c["verdict"],
        "population_identity": c["population_identity"],
        "ordered_membership_hash": c["ordered_membership_hash"],
        "ordered_membership": c["ordered_membership"],
        "per_unit": [
            {
                "calibration_index": u["calibration_index"],
                "validation_unit_id": u["validation_unit_id"],
                "python_version": u["python_version"],
                "lock_type": u["lock_type"],
                "install_route": u["install_route"],
                "wheelhouse_era": u["wheelhouse_era"],
                "runtime_pins_count": u["runtime_pins_count"],
                "resolved_wheels_count": u["resolved_wheels_count"],
                "resolvable": u["resolvable"],
                "missing": u["missing"],
                "incompatible": u["incompatible"],
                "source_fidelity_filenames": u["source_fidelity_filenames"],
                "source_fidelity_overlay_count": u["source_fidelity_overlay_count"],
                "recovery_overlay": u["recovery_overlay"],
                "recovery_overlay_versions": u["recovery_overlay_versions"],
            }
            for u in c["per_unit"]
        ],
    }
    return _sha256_bytes(json.dumps(sem, separators=(",", ":")).encode("utf-8"))


def population_authority() -> dict[str, Any]:
    from typing import cast

    from benchmark.wp2.full144 import population

    return cast(dict[str, Any], population.validate_population())


# ---------------------------------------------------------------------------
def verify_release_identity() -> dict[str, Any]:
    branch = git_branch()
    if branch != BRANCH:
        raise LauncherError(f"branch {branch} != required {BRANCH}")
    if not git_clean_tracked():
        raise LauncherError("tracked worktree is not clean")

    head = git_head()
    sci_peel = tag_peel(SCIENTIFIC_TAG)
    if sci_peel != SCIENTIFIC_HEAD:
        raise LauncherError(f"scientific tag {SCIENTIFIC_TAG} peels to {sci_peel} != {SCIENTIFIC_HEAD}")
    r3_peel = tag_peel(SEQUENCE_TAG)
    if r3_peel != R3_1_RELEASE_HEAD:
        raise LauncherError(f"R3.1 tag {SEQUENCE_TAG} peels to {r3_peel} != {R3_1_RELEASE_HEAD}")
    if not _is_ancestor(SCIENTIFIC_HEAD, SUPPORT_HEAD):
        raise LauncherError("scientific head not ancestor of support head")
    if not _is_ancestor(SUPPORT_HEAD, head):
        raise LauncherError("support head not ancestor of current HEAD")
    if not _is_ancestor(R3_1_RELEASE_HEAD, head):
        raise LauncherError("R3.1 release head not ancestor of current HEAD")

    # Successor release tag identity (Task L): present -> must peel to HEAD.
    succ_peel = tag_peel(SUCCESSOR_TAG)
    if succ_peel is not None and succ_peel != head:
        raise LauncherError(f"successor tag {SUCCESSOR_TAG} peels to {succ_peel} != HEAD {head}")

    code = effective_code_set_hash()
    if code != EXPECTED_EXECUTION_CODE_SET:
        raise LauncherError(f"execution-code-set recompute {code} != frozen")
    closure = blob_lf_sha256_at("HEAD", "research/env-canon-r4/R4_PHASE1B_SUCCESSOR_ARTIFACT_CLOSURE_144.json")
    if closure != EXPECTED_CLOSURE_CONTENT:
        raise LauncherError(f"committed closure content {closure} != frozen")
    footprint = committed_closure_footprint()
    if footprint != EXPECTED_CLOSURE_FOOTPRINT:
        raise LauncherError(f"closure semantic footprint {footprint} != frozen")

    pop = population_authority()
    if pop["population_identity"] != EXPECTED_POPULATION:
        raise LauncherError("population identity mismatch")
    if pop["ordered_membership_hash"] != EXPECTED_ORDER:
        raise LauncherError("ordered membership hash mismatch")
    if pop["binding_hash"] != EXPECTED_IMAGE:
        raise LauncherError("image binding hash mismatch")

    return {
        "branch": branch,
        "git_head": head,
        "scientific_authority_peel": sci_peel,
        "support_evidence_head": SUPPORT_HEAD,
        "r3_1_release_head": r3_peel,
        "successor_tag_peel": succ_peel,
        "effective_execution_code_set_hash": code,
        "committed_closure_content_hash": closure,
        "closure_semantic_footprint": footprint,
        "population_identity": pop["population_identity"],
        "ordered_membership_hash": pop["ordered_membership_hash"],
        "image_binding_hash": pop["binding_hash"],
        "tracked_clean": True,
        "zero_network": True,
    }


# ---------------------------------------------------------------------------
def _validate_receipt(name: str) -> dict[str, Any]:
    spec = RECEIPTS[name]
    path = spec["root"] / "R3_SELECTION_RECEIPT.json"
    if not path.is_file():
        raise LauncherError(f"fresh {name} receipt missing: {path}")
    r = _read_json(path)
    if r.get("schema_version") != "env-canon-r4/r3-selection/receipt/1.0":
        raise LauncherError(f"{name} receipt schema mismatch")
    if r.get("selection_name") != name:
        raise LauncherError(f"{name} receipt selection_name mismatch")
    if r.get("release_head") != R3_1_RELEASE_HEAD:
        raise LauncherError(f"{name} receipt release_head mismatch")
    if r.get("release_tag") != SEQUENCE_TAG:
        raise LauncherError(f"{name} receipt release_tag mismatch")
    if r.get("scientific_authority_head") != SCIENTIFIC_HEAD:
        raise LauncherError(f"{name} receipt scientific authority mismatch")
    if r.get("support_evidence_head") != SUPPORT_HEAD:
        raise LauncherError(f"{name} receipt support evidence mismatch")
    if r.get("execution_code_set_hash") != EXPECTED_EXECUTION_CODE_SET:
        raise LauncherError(f"{name} receipt code-set mismatch")
    if r.get("committed_closure_content_hash") != EXPECTED_CLOSURE_CONTENT:
        raise LauncherError(f"{name} receipt closure content mismatch")
    if r.get("selection_membership_hash") != spec["membership"]:
        raise LauncherError(f"{name} receipt membership mismatch")
    if r.get("selection_manifest_sha256") != spec["manifest"]:
        raise LauncherError(f"{name} receipt manifest mismatch")
    if r.get("population_identity") != EXPECTED_POPULATION:
        raise LauncherError(f"{name} receipt population mismatch")
    if r.get("ordered_membership_hash") != EXPECTED_ORDER:
        raise LauncherError(f"{name} receipt order mismatch")
    if r.get("image_binding_hash") != EXPECTED_IMAGE:
        raise LauncherError(f"{name} receipt image binding mismatch")
    if r.get("zero_network") is not True:
        raise LauncherError(f"{name} receipt zero_network not asserted")
    if r.get("run_root") != str(spec["root"]):
        raise LauncherError(f"{name} receipt run_root mismatch")
    counts = (int(r.get("N_EXECUTED", -1)), int(r.get("N_PASS", -1)), int(r.get("N_NON_PASS", -1)))
    if counts != spec["counts"]:
        raise LauncherError(f"{name} receipt counts {counts} != {spec['counts']}")
    units = r.get("units", [])
    if len(units) != spec["counts"][0]:
        raise LauncherError(f"{name} receipt unit count mismatch")
    for u in units:
        if u.get("result") != "PASS" or u.get("classification") != "PASS":
            raise LauncherError(f"{name} receipt contains non-PASS unit")
    return {"name": name, "counts": counts, "run_root": str(path), "sha256": _sha256_file(path)}


def verify_all_receipts() -> dict[str, dict[str, Any]]:
    return {name: _validate_receipt(name) for name in ("TARGETED3", "CAL12", "FULL144")}


# ---------------------------------------------------------------------------
def _scientific_root_state() -> dict[str, Any]:
    units_dir = SCIENTIFIC_ROOT / "units"
    n_units = 0
    if units_dir.is_dir():
        n_units = len([p for p in units_dir.iterdir() if p.is_dir()])
    progress_exist = (SCIENTIFIC_ROOT / "progress" / "progress.json").is_file()
    receipt_exist = (SCIENTIFIC_ROOT / "R3_SELECTION_RECEIPT.json").is_file()
    return {
        "run_root": str(SCIENTIFIC_ROOT),
        "exists": SCIENTIFIC_ROOT.is_dir(),
        "n_scientific_unit_dirs": n_units,
        "progress_exists": progress_exist,
        "receipt_exists": receipt_exist,
        "zero_units_executed": n_units == 0 and not progress_exist and not receipt_exist,
    }


def verify_scientific_root_fresh() -> dict[str, Any]:
    st = _scientific_root_state()
    if st["exists"] is False:
        raise LauncherError(f"scientific root missing: {SCIENTIFIC_ROOT}")
    for other in ("r4-successor-r3-targeted3-2026-10-16",
                  "r4-successor-r3-cal12-2026-10-16",
                  "r4-successor-r3-qualification144-2026-10-16"):
        if str(SCIENTIFIC_ROOT) == str(Path(r"D:\WP2\runs") / other):
            raise LauncherError("scientific root collides with a qualification root")
    if not st["zero_units_executed"]:
        raise LauncherError("scientific root is NOT fresh (units/progress/receipt present)")
    return st


def verify_disk() -> dict[str, Any]:
    import shutil

    free = shutil.disk_usage(str(SCIENTIFIC_ROOT) + "\\").free / (1024**3)
    if free < DISK_STOP_GIB:
        raise LauncherError(f"disk free {free:.1f} GiB < {DISK_STOP_GIB} GiB hard stop")
    return {"free_gib": round(free, 2), "threshold_gib": DISK_STOP_GIB}


def verify_images() -> list[dict[str, Any]]:
    binding = _read_json(BINDING_PATH)
    out: list[dict[str, Any]] = []
    for p in binding.get("pairs", []):
        ref = str(p["execution_image_ref"])
        expected = str(p["immutable_image_id"])
        r = _run(["wsl", "-d", WSL_DISTRO, "--", "docker", "image", "inspect", "--format", "{{.Id}}", ref])
        if r.returncode != 0:
            raise LauncherError(f"image {ref} missing locally (no pull): {r.stderr.strip()}")
        got = (r.stdout or "").strip()
        if got != expected:
            raise LauncherError(f"image {ref}: local {got} != frozen {expected}")
        out.append({"native_profile_id": p["native_profile_id"], "ref": ref, "match": True})
    if len(out) != 11:
        raise LauncherError(f"image pair count {len(out)} != 11")
    return out


def static_checks() -> dict[str, Any]:
    runner_src = RUNNER.read_text(encoding="utf-8")
    driver_src = DRIVER.read_text(encoding="utf-8")
    ps1_src = POWERSHELL_LAUNCHER.read_text(encoding="utf-8")
    if '"--network=none"' not in runner_src:
        raise LauncherError("runner does not require --network=none")
    for forbidden in ("OpenCode", "OpenRouter", "LLM", "openai", "anthropic"):
        if forbidden.lower() in ps1_src.lower():
            raise LauncherError(f"launcher must not depend on {forbidden!r}")
    for src in (runner_src, driver_src):
        if '"pull"' in src or '"build"' in src:
            raise LauncherError("pull/build literal present in execution path")
    return {"static": "PASS", "network_isolation": "--network=none", "no_llm_dependency": True}


# ---------------------------------------------------------------------------
def status() -> dict[str, Any]:
    if not SCIENTIFIC_ROOT.is_dir():
        return {"selection": "SCIENTIFIC_FULL144", "status": "NOT_STARTED", "run_root": str(SCIENTIFIC_ROOT)}
    st = _scientific_root_state()
    freeze = SCIENTIFIC_ROOT / "freeze" / FREEZE_RECORD_NAME
    return {
        "selection": "SCIENTIFIC_FULL144",
        "status": "NOT_STARTED" if st["zero_units_executed"] else "RUNNING",
        "n_scientific_unit_dirs": st["n_scientific_unit_dirs"],
        "freeze_record_present": freeze.is_file(),
        "run_root": str(SCIENTIFIC_ROOT),
    }


def preflight() -> dict[str, Any]:
    release = verify_release_identity()
    receipts = verify_all_receipts()
    fresh = verify_scientific_root_fresh()
    disk = verify_disk()
    static = static_checks()
    images = verify_images()
    return {
        "preflight": "PASS",
        "authority": release,
        "receipts": receipts,
        "scientific_root": fresh,
        "disk": disk,
        "static": static["static"],
        "execution_image_pairs": images,
        "zero_network": True,
        "zero_scientific_units_executed": fresh["zero_units_executed"],
    }


def freeze_record() -> dict[str, Any]:
    """Compose the additive successor PRE_EXECUTION_FREEZE record (no write)."""
    release = verify_release_identity()
    receipt_hashes = verify_all_receipts()
    coding_members = [
        {"path": str(m["path"]), "sha256": str(m["sha256"]), "role": str(m.get("role", ""))}
        for m in _read_json(CODE_SET_MANIFEST)["members"]
    ]
    # Image pairs + deterministic authority
    binding = _read_json(BINDING_PATH)
    pairs = [
        {
            "docker_profile_id": p["docker_profile_id"],
            "native_profile_id": p["native_profile_id"],
            "execution_image_ref": p["execution_image_ref"],
            "immutable_image_id": p["immutable_image_id"],
        }
        for p in binding["pairs"]
    ]
    census = _read_json(CENSUS_PATH)
    ordered_membership = [str(u["validation_unit_id"]) for u in census["units"]]

    # RUN_TO_RUN_DETERMINISM_SECONDARY_ANALYSIS (Task H) - frozen, prospective.
    secondary_analysis = {
        "title": "RUN_TO_RUN_DETERMINISM_SECONDARY_ANALYSIS",
        "status_note": (
            "Prospectively specified BEFORE the successor scientific Full144 run, AFTER "
            "observing the successful R3.1 FULL144 qualification. NOT preregistered before "
            "the qualification."
        ),
        "purpose": "Assess run-to-run stability between A (non-scientific R3.1 FULL144 "
                   "qualification) and B (successor scientific Full144) per exact validation unit.",
        "primary_outputs": {
            "agreement_denominator": 144,
            "agreement_count": "A == B on every compared field",
            "disagreement_count": "144 - agreement_count",
            "disagreement_unit_ids": "exact validation_unit_ids where any compared field differs",
        },
        "compared_fields": ["result", "classification"],
        "additional_predeclared_fields": [
            {"field": "immutable_image_id", "schema": "env-canon-r4-full144/1.0",
             "rationale": "deterministic image binding per unit"},
            {"field": "requirements_lock_sha256", "schema": "env-canon-r4-full144/1.0",
             "rationale": "deterministic resolved lock identity"},
            {"field": "runtime_pins_count", "schema": "env-canon-r4-full144/1.0",
             "rationale": "deterministic pin-count footprint"},
            {"field": "resolved_wheels_count", "schema": "env-canon-r4-full144/1.0",
             "rationale": "deterministic closure footprint"},
        ],
        "disagreement_handling": (
            "Any disagreement is reported as INSTABILITY, is investigated, is NOT resolved "
            "by selectively rerunning/replacing the disagreeing unit, and does NOT silently "
            "rewrite either run's evidence."
        ),
        "secondary_scope_guard": "This analysis does NOT replace or redefine the primary scientific Full144 analysis.",
        "operator_command": (
            "python scripts/r4_run_to_run_secondary_analysis.py "
            "--result-dir-b D:\\WP2\\runs\\r4-scientific-full144-successor-2026-10-17"
        ),
    }

    record: dict[str, Any] = {
        "schema_version": "env-canon-r4/r3.1/successor-preexecution-freeze/1.0",
        "mission_id": "M17_D7_R4_POSTQUAL_SUCCESSOR_PREEXECUTION_FREEZE",
        "generated_utc": utcnow(),
        "branch": BRANCH,
        "successor_release_tag": SUCCESSOR_TAG,
        "git_head": release["git_head"],
        "scientific_authority": {
            "head": SCIENTIFIC_HEAD,
            "tag": SCIENTIFIC_TAG,
            "peel_verified": release["scientific_authority_peel"],
            "support_evidence_head": SUPPORT_HEAD,
        },
        "execution_code_set_hash": EXPECTED_EXECUTION_CODE_SET,
        "execution_code_members": coding_members,
        "committed_closure_content_hash": EXPECTED_CLOSURE_CONTENT,
        "closure_semantic_footprint": EXPECTED_CLOSURE_FOOTPRINT,
        "population": {
            "population_identity": EXPECTED_POPULATION,
            "ordered_membership_hash": EXPECTED_ORDER,
            "n_validation_units": len(ordered_membership),
            "ordered_membership": ordered_membership,
        },
        "image_binding_hash": EXPECTED_IMAGE,
        "execution_image_pairs": pairs,
        "r3_1_release": {"tag": SEQUENCE_TAG, "peeled_head": R3_1_RELEASE_HEAD},
        "qualification_receipts": {
            name: {
                "counts": list(spec["counts"]),
                "run_root": str(spec["root"]),
                "receipt_sha256": receipt_hashes[name]["sha256"],
            }
            for name, spec in RECEIPTS.items()
        },
        "scientific_full144": {
            "population_order_frozen": (
                "R3_SELECTION_FULL144.json == I6 census == execution-code-set population"
            ),
            "n_units": 144,
            "per_unit_execution_path": (
                "src/benchmark/wp2/full144/driver.py Full144UnitRunner "
                "-> qualified Attempt-6 runner"
            ),
        },
        "replay_equivalence_matrix": {
            "per_unit_execution_path": "IDENTICAL (same frozen Full144UnitRunner -> Attempt-6 runner)",
            "ordered_144_units": "IDENTICAL (same frozen 144 ordered population/order/hash 8eb4a724...)",
            "dependency_environment_resolution": "IDENTICAL (same committed closure + wheelhouse + runtime pins)",
            "docker_runtime_image": "IDENTICAL (same 11 immutable image binding, 5169c69d...)",
            "zero_network_policy": "IDENTICAL (--network=none on every unit)",
            "execution_semantics_difference": (
                "SCIENTIFIC successor run uses fail-fast per-unit semantics "
                "(driver.run_next / r4_full144_preexecution.py --next; STOP on first "
                "mandatory FAIL).  QUALIFICATION used continue-on-local-failure sweep. "
                "This is an aggregation/continuation difference ONLY at the harness layer; "
                "it does not alter the frozen per-unit execution path, order, resolution, "
                "image, or network.  Each individual unit's behaviour is identical."
            ),
        },
        "timeout_retry_policy": {
            "install_timeout_seconds": 5400,
            "retry_policy": (
                "NO automatic semantic retry; fail-fast stop on first mandatory FAIL; "
                "partial unit -> STOP_OWNER_REVIEW"
            ),
        },
        "failure_taxonomy": (
            "FROZEN driver CONTINGENCY_MATRIX (12 classes); no skip/reorder/rerun; "
            "instrumentation failures classified separately."
        ),
        "zero_network_policy": "--network=none for every scientific unit; no pull/build/download/acquire",
        "docker_runtime_image_authority": (
            "R4_EXECUTION_IMAGE_BINDING_RUNTIME_CLEAN.json (11 pairs, immutable_image_id exact)"
        ),
        "seeds_determinism": {
            "status": "NOT_APPLICABLE",
            "justification": (
                "The frozen execution path (driver.py, population.py, "
                "r4_behavioral_calibration_n12_r2.py, route_closure.py) contains NO "
                "stochastic/sampling/shuffle/seed-controlled component; grep for "
                "random/seed/shuffle/sample returns no hits in the 4 execution-code members."
            ),
        },
        "scientific_output_root": str(SCIENTIFIC_ROOT),
        "launcher_identity": (
            "scripts/r4_full144_successor_scientific_launcher.ps1 + "
            "scripts/r4_full144_successor_scientific_preflight.py"
        ),
        "post_tag_preflight_requirements": [
            "HEAD == successor release tag peel",
            "tracked tree clean",
            "3 fresh qualification receipts exact counts",
            "scientific root fresh (zero units)",
            "11/11 images present with exact immutable IDs",
            "zero-network policy static",
        ],
        "run_to_run_determinism_secondary_analysis": secondary_analysis,
    }
    return record


def write_freeze() -> dict[str, Any]:
    path = SCIENTIFIC_ROOT / "freeze" / FREEZE_RECORD_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    rec = freeze_record()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    rec["freeze_path"] = str(path)
    rec["freeze_sha256"] = _sha256_file(path)
    return rec


# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="M17_D7_R4 successor scientific Full144 preflight")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--status", action="store_true")
    grp.add_argument("--preflight", action="store_true")
    grp.add_argument("--freeze", action="store_true")
    try:
        args = ap.parse_args(argv)
    except SystemExit:
        return 1
    try:
        if args.status:
            print(json.dumps(status(), indent=2, sort_keys=True))
            return 0
        if args.preflight:
            out = preflight()
            print(json.dumps(out, indent=2, sort_keys=True))
            print(
                "PREFLIGHT_AUTHORITY_VALID SCIENTIFIC_FULL144 "
                "zero_scientific_units=True receipts=TARGETED3 3/3/0,CAL12 12/12/0,FULL144 144/144/0"
            )
            return 0
        if args.freeze:
            rec = write_freeze()
            print(rec["freeze_path"])
            print(rec["freeze_sha256"])
            print("PRE_EXECUTION_FREEZE_WRITTEN")
            return 0
    except (LauncherError, Exception) as exc:
        print(f"FAIL_CLOSED {exc}", file=sys.stderr)
        return 1
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
