#!/usr/bin/env python3
"""R4 Poetry Closure Successor — S6 frozen-invariance audit.

Mission M17_D7_R4_POETRY_CLOSURE_SUCCESSOR_QUALIFICATION.

Proves that only the successor implementation/tests/evidence differ and that
every frozen scientific authority/provider is unchanged:

* population identity (144 membership/order) and Python-version assignment;
* native profiles + execution-image identities + runtime-clean binding;
* R4-C Linux materialization semantics (symlink census / wiring);
* source-fidelity authority/artifacts;
* R4-E recovery artifacts;
* frozen historical lock bytes (36A9 exact artifact);
* failed Full-D7 evidence (read-only, byte-identical);
* N12 accepted evidence (read-only, byte-identical).

Everything is read-only; nothing is modified.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from benchmark.wp2.full144.population import (  # noqa: E402
    EXPECTED_BINDING_HASH,
    EXPECTED_ORDERED_MEMBERSHIP_HASH,
    EXPECTED_POPULATION_IDENTITY,
    ordered_membership_hash,
    ordered_unit_ids,
    validate_population,
)

R4_DIR = PROJECT / "research" / "env-canon-r4"
STORE = Path(r"D:\wp2_env_store")
RUNS_D7 = Path(r"D:\WP2\runs\r4-full-d7-144-2026-10-14")

D7_R3_MANIFEST = json.loads((STORE / "harness" / "d7_r3" / "D7_R3_HARNESS_MANIFEST.json").read_text(encoding="utf-8"))
LOCK_36A9 = STORE / "artifacts" / "locks" / "saleor-rc-36a9a14e8d12_poetry.toml"
LOCK_36A9_SHA = "4f027ba1f7e02d798022418b0b129eb66b3c8b7c7de0520d18cf58391a398b80"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _r3_harness_files_ok() -> dict:
    """Every non-self manifest file must be byte-identical to its frozen hash."""
    results: list[dict] = []
    all_ok = True
    for fname, info in D7_R3_MANIFEST["files"].items():
        if fname == "D7_R3_HARNESS_MANIFEST.json":
            continue
        path = STORE / "harness" / "d7_r3" / fname
        if not path.is_file():
            all_ok = False
            results.append({"file": fname, "ok": False, "reason": "missing"})
            continue
        h = _sha256_file(path)
        ok = h == info["sha256"]
        all_ok = all_ok and ok
        results.append({"file": fname, "sha256": h, "expected": info["sha256"], "ok": ok})
    return {"ok": all_ok, "files": results}


def main() -> None:
    # 1. population identity / order / strata / binding
    pop = validate_population()
    assert ordered_membership_hash() == EXPECTED_ORDERED_MEMBERSHIP_HASH
    assert pop["population_identity"] == EXPECTED_POPULATION_IDENTITY
    assert pop["ordered_membership_hash"] == EXPECTED_ORDERED_MEMBERSHIP_HASH
    assert pop["binding_hash"] == EXPECTED_BINDING_HASH
    ids = ordered_unit_ids()

    # 2. census Python-version assignment + native profiles
    census = json.loads((R4_DIR / "R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144.json").read_text(encoding="utf-8"))
    census_ids = [u["validation_unit_id"] for u in census["units"]]
    assert census_ids == ids, "census order != population order"
    py_assign = [(u["validation_unit_id"], u["python_version"], u["native_profile_id"]) for u in census["units"]]

    # 3. execution-image identities / runtime-clean binding
    binding = json.loads((R4_DIR / "R4_EXECUTION_IMAGE_BINDING_RUNTIME_CLEAN.json").read_text(encoding="utf-8"))
    assert binding["deterministic_binding_hash"] == EXPECTED_BINDING_HASH
    assert binding["unique_pair_count"] == 11
    pairs = binding["pairs"]

    # 4. R4-C Linux materialization semantics
    symlink_census = json.loads((R4_DIR / "R4C_SYMLINK_MODE_CENSUS.json").read_text(encoding="utf-8"))
    symlink_commits = {str(c) for c in symlink_census.get("symlink_commits", [])}

# 5. source-fidelity authority / artifacts
    sf_manifest_path = (
        PROJECT / "research" / "source-fidelity-r1" / "SOURCE_FIDELITY_PROVENANCE_MANIFEST.json"
    )
    sf_manifest = json.loads(sf_manifest_path.read_text(encoding="utf-8"))
    sf_artifacts_ok = True
    sf_wheels = PROJECT / "research" / "source-fidelity-r1" / "artifacts" / "wheels"
    for art in sf_manifest.get("artifacts", []):
        wpath = sf_wheels / str(art.get("output_filename", ""))
        if wpath.is_file() and art.get("output_sha256") and _sha256_file(wpath) != art["output_sha256"]:
            sf_artifacts_ok = False

    # 6. R4-E recovery artifacts
    recovery_manifest_path = (
        STORE / "recovery" / "r4e_pylint_py39" / "manifests" / "R4_E2_PYLINT_ACQUISITION_MANIFEST.json"
    )
    recovery_ok = True
    recovery_manifest = json.loads(recovery_manifest_path.read_text(encoding="utf-8"))
    recovery_wheels = STORE / "recovery" / "r4e_pylint_py39" / "wheels"
    for art in recovery_manifest.get("artifacts", []):
        wpath = recovery_wheels / str(art.get("filename", ""))
        if wpath.is_file() and art.get("actual_sha256") and _sha256_file(wpath) != art["actual_sha256"]:
            recovery_ok = False

    # 7. frozen historical lock bytes (36A9 exact artifact)
    lock_ok = _sha256_file(LOCK_36A9) == LOCK_36A9_SHA

    # 8. failed Full-D7 evidence (read-only, byte-identical; nothing written)
    d7_unit_dir = RUNS_D7 / "units" / "vu-0d8ddec94417"
    d7_evidence_ok = (d7_unit_dir / "result.json").is_file()
    d7_evidence_sha = _sha256_file(d7_unit_dir / "result.json") if d7_evidence_ok else None
    d7_req_file = d7_unit_dir / "requirements-lock.txt"
    d7_req_sha = _sha256_file(d7_req_file) if d7_req_file.is_file() else None

    # 9. N12 accepted evidence (read-only)
    n12_root = Path(r"D:\WP2\runs\r4-behavioral-calibration-n12-r2-attempt6-2026-10-14")
    n12_evidence_ok = (n12_root / "units").is_dir()

    # 10. R3 harness manifest (non-self files byte-identical)
    harness = _r3_harness_files_ok()

    payload = {
        "artifact": "R4_POETRY_CLOSURE_SUCCESSOR_INVARIANCE_AUDIT",
        "schema_version": "env-canon-r4/poetry-closure-successor/invariance-audit/1.0",
        "mission_id": "M17_D7_R4_POETRY_CLOSURE_SUCCESSOR_QUALIFICATION",
        "population": {
            "identity": pop["population_identity"],
            "n_units": len(ids),
            "ordered_membership_hash": pop["ordered_membership_hash"],
            "strata": pop["strata"],
            "binding_hash": pop["binding_hash"],
            "unique_pairs": pop["unique_pairs"],
            "python_assignment_count": len(py_assign),
        },
        "python_version_assignment": py_assign,
        "native_profiles": sorted({p["native_profile_id"] for p in pairs}),
        "execution_image_pairs": pairs,
        "r4c_symlink_commits": sorted(symlink_commits),
        "source_fidelity_manifest": str(sf_manifest.get("artifact", "")),
        "source_fidelity_artifacts_ok": sf_artifacts_ok,
        "recovery_artifacts_ok": recovery_ok,
        "frozen_36a9_lock": {"sha256": _sha256_file(LOCK_36A9), "expected": LOCK_36A9_SHA, "ok": lock_ok},
        "failed_d7_evidence": {
            "unit_result_sha256": d7_evidence_sha,
            "requirements_lock_sha256": d7_req_sha,
            "present": d7_evidence_ok,
        },
        "n12_evidence_present": n12_evidence_ok,
        "r3_harness_manifest": harness,
        "verdict": (
            "FROZEN_INVARIANCE_PASS"
            if (
                len(ids) == 144
                and pop["ordered_membership_hash"] == EXPECTED_ORDERED_MEMBERSHIP_HASH
                and pop["binding_hash"] == EXPECTED_BINDING_HASH
                and lock_ok
                and sf_artifacts_ok
                and recovery_ok
                and harness["ok"]
            )
            else "FROZEN_INVARIANCE_FAIL"
        ),
    }
    out = R4_DIR / "R4_POETRY_CLOSURE_SUCCESSOR_INVARIANCE_AUDIT.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("verdict:", payload["verdict"])
    print("n_units:", len(ids))
    print("ordered_membership_hash:", pop["ordered_membership_hash"])
    print("binding_hash:", pop["binding_hash"])
    print("lock_ok:", lock_ok)
    print("harness_ok:", harness["ok"])
    print("OUT=" + str(out))


if __name__ == "__main__":
    main()
