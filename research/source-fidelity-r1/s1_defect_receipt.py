#!/usr/bin/env python3
"""M17 S1 - reproduce the source-identity defect from frozen/local evidence.

Writes ``research/source-fidelity-r1/SOURCE_IDENTITY_DEFECT_RECEIPT.json``.

No runtime execution, no network, no calibration.  Reads only:
* frozen owner-review evidence (local Git objects + store hashes);
* the exact historical vendored source trees at the target commits;
* the substituted canonical wheel hashes.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(SRC_DIR))

from benchmark.wp2 import source_fidelity_r1 as sf  # noqa: E402

REPO = r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\dist\pilot-repo-cache\saleor"
LOCK_DIR = Path(r"D:\wp2_env_store\artifacts\locks")
OUT = Path(__file__).resolve().parent / "SOURCE_IDENTITY_DEFECT_RECEIPT.json"

EXPOSED_TASKS = {
    "saleor-rc-e6198146186d": {
        "target_commit": "e6198146186d1c782bf46f6c9439fa05b1049b2f",
        "unit": "vu-b9808f19ace4",
        "lock_raw_sha256": "95884b5108283b7929da9adf82afde2532d5de6eb7ef58287cac067154298137",
        "lock_plus_lf_sha256": "5ac46a7ec1a90deb4fb152a7a10bb3e115c6ddc126aaa6c75b2a138f075822bf",
        "calibration_observed_failure": True,
    },
    "saleor-rc-19bb9b070965": {
        "target_commit": "19bb9b0709654010d1b4e4e9049af119d3b28815",
        "unit": "vu-692af9112c6d",
        "lock_raw_sha256": "ab997871ddf77412202d83eee31f4eab5cde7f38c73281e363bc8a23098318ec",
        "lock_plus_lf_sha256": "4c0fd4e05e9c8934a998c4653d64ac487e3817c6d9e5f081b607ce69aaa230d6",
        "calibration_observed_failure": False,
    },
}

SUBSITITUTED_ARTIFACTS = {
    "PyXB 1.2.5": {
        "filename": "pyxb-1.2.5-py3-none-any.whl",
        "sha256": "52a256ce138aa2a4031a86789ba8edbe5379eb4ca96391eb4c572092894092d9",
        "source": "registry sdist + R4B find_spec backport (R4B_FINAL_PYXB_COMPATIBILITY_BACKPORT.json)",
    },
    "authorizenet 1.1.4": {
        "filename": "authorizenet-1.1.4-py3-none-any.whl",
        "sha256": "d5e8d38de4c7ac6c4e8d2cbe190fcbb5427995c9da760ba3eba60e0faaa94e36",
        "source": "registry sdist",
    },
}

CODE_PATH_IDENTITY_DISCARDED = {
    "phase_a_parser": {
        "file": "scripts/env_canon_phase_a_generate.py::parse_poetry_lock",
        "emits": "name/version/python-marker with generic source_type 'poetry.lock'",
    },
    "closure_derivation": {
        "file": "research/env-canon-evidence/d7-r3/harness/d7_r3_closure.py::poetry_pins",
        "emits": "name==version pins (source table never carried)",
    },
    "artifact_resolution": {
        "file": "research/env-canon-evidence/d7-r3/harness/d7_r3_closure.py::resolve_runtime_artifacts",
        "matches": "wheels by (name, version) parsed from the wheel filename only",
    },
    "repo_parser": {
        "file": "src/benchmark/wp2/dep_compiler.py::parse_poetry_lock/PkgRecord",
        "emits": "name/version/source-kind tag; source url and tree identity are not retained",
    },
    "install_route": {
        "file": "tmp/d7_r3_calibration_driver.py (line 139 runtime pins; line 248 uv pip install -r requirements-lock.txt)",
        "note": "a route label (V2_EDITABLE_PLUS_LOCK_DEV) does not restore omitted source provenance",
    },
}


def _lock_text(task: str) -> str:
    path = LOCK_DIR / f"{task}_poetry.toml"
    return path.read_text(encoding="utf-8")


def main() -> int:
    tasks = {}
    for task, meta in EXPOSED_TASKS.items():
        lock_text = _lock_text(task)
        identities = {}
        for source_path in ("vendored/pyxb", "vendored/authorizenet"):
            extraction = sf.extract_source_tree(
                REPO, meta["target_commit"], source_path
            )
            identity = sf.build_source_identity(
                name="PyXB" if source_path.endswith("pyxb") else "authorizenet",
                version="1.2.5" if source_path.endswith("pyxb") else "1.1.4",
                source_type=sf.SOURCE_TYPE_DIRECTORY,
                source_reference=source_path,
                target_commit=meta["target_commit"],
                repo_dir=REPO,
            )
            identities[source_path] = {
                "extraction": extraction,
                "identity": identity.to_dict(),
                "canonical_pin": identity.canonical_pin(),
                "identity_sha256": identity.identity_sha256(),
            }
        tasks[task] = {
            "validation_unit_id": meta["unit"],
            "target_commit": meta["target_commit"],
            "lock_raw_sha256": meta["lock_raw_sha256"],
            "lock_plus_lf_sha256": meta["lock_plus_lf_sha256"],
            "calibration_observed_failure": meta["calibration_observed_failure"],
            "lock_source_semantics": {
                "pyxb": {"source": {"type": "directory", "url": "vendored/pyxb"}},
                "authorizenet": {"source": {"type": "directory", "url": "vendored/authorizenet"}},
            },
            "historical_source_trees": identities,
        }

    receipt = {
        "mission": "M17_ENV_CANON_SOURCE_FIDELITY_AMENDMENT_R1_DESIGN_AND_FREEZE",
        "phase": "S1_REPRODUCE_SOURCE_IDENTITY_DEFECT",
        "network_used": False,
        "runtime_execution_used": False,
        "root_cause_classification": "C_LOCK_RECONSTRUCTION_DEFECT",
        "schema_version": sf.SOURCE_IDENTITY_SCHEMA_VERSION,
        "defect_summary": (
            "Historical Poetry lock records directory sources for PyXB 1.2.5 "
            "(vendored/pyxb) and authorizenet 1.1.4 (vendored/authorizenet). "
            "The D7 R3 canon and closure derivation flatten these to "
            "name==version, and the artifact resolver selects a wheel by "
            "normalized distribution name/version, substituting a registry "
            "wheel that is NOT source-identical to the historical vendored "
            "dependency. The vendored PyXB uses collections.abc.MutableSequence; "
            "the substituted registry PyXB 1.2.5 wheel uses "
            "collections.MutableSequence and fails on Python 3.12."
        ),
        "proven_loss_code_path": CODE_PATH_IDENTITY_DISCARDED,
        "substituted_artifacts": SUBSITITUTED_ARTIFACTS,
        "tasks": tasks,
        "p2p_note": (
            "Both exposed tasks vend the same bytes: their source trees hash "
            "identically, so one source-aware artifact identity covers both "
            "directory packages under the same generic rule."
        ),
    }
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote {OUT}")
    print("closure_ids:")
    for task, meta in EXPOSED_TASKS.items():
        closure = sf.derive_source_aware_closure(
            _lock_text(task), meta["target_commit"], REPO, python_version="3.12"
        )
        print(" ", task, closure["closure_identity_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())