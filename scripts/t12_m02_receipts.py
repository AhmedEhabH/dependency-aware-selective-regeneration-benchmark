#!/usr/bin/env python3
"""T12 M02-D1 — Honest JUnit / Option B physical receipts (stdlib only, offline).

Mission: T12_M02_D1_20261027 (Track 1.2), Task 2.

WHAT THIS IS
------------
A fail-closed per-run receipt schema and validator for the future option-B
13-arm executions.  Option B (REUSE_NOT_PERMITTED) requires every arm to have
its own fresh process, database, execution ID, JUnit receipts, resource and
cost ledger, EVEN when two arms share identical tree/patch content.  Duplicate
output bytes alone do NOT prove physical reuse — identity evidence does.

The validator enforces completeness and classification, forbids the same
*physical* receipt or database/run identity across arms, and never infers
reuse merely because two independently executed pytest XML files contain
identical bytes (it records a signal to investigate instead).

Missing proof is STOP or NOT_MEASURED — never a silent PASS.

The historical single-node R7 checker is exposed separately as a scoped
diagnostic (``historical_r7_diagnostic``), explicitly NOT M02-E evidence.

Exit codes: 0 PASS | 1 STOP | 2 NOT_RUN.
"""
from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

_SCRIPTS = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "t12_m02_arm_adapter", _SCRIPTS / "t12_m02_arm_adapter.py")
assert _spec is not None and _spec.loader is not None
_adapt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_adapt)

RECEIPT_SCHEMA = "t12_m02_run_receipt_v1"
RECEIPT_FILENAME = "run_receipt.json"
JUNIT_DIR_REL = "junit"
JUNIT_RECEIPTS_EXPECTED = _adapt.JUNIT_COUNT_PER_ARM_PILOT  # 9 (3 nodes x 3)
F2P_REPETITIONS = _adapt.F2P_REPETITIONS  # 3
F2P_NODES_COUNT = _adapt.F2P_NODES_COUNT  # 3

# R7 receipt naming precedent: <task8>_<letter>_r<rep>_f<node>.xml.  M02-D1 uses
# an 8-hex arm-class tag (unique per four-field class; alias pair shares class
# so two physical arms may share the tag — separation is by run DIR + identity).
JUNIT_RE = re.compile(
    r"^(?P<task>[0-9a-f]{4,})_(?P<tag>[0-9a-f]{8})_r(?P<rep>[0-2])_f(?P<node>[0-2])\.xml$")
# DB identity precedent from R7: opws_m3b_<task8>_<HHMMSS>_<12hex>.
# D3-R1: the FROZEN OpwsIsolatedRuntime.fresh_db_name() produces an 80-bit
# nonce via secrets.token_hex(10) (20 hex chars) — the suffix regex therefore
# accepts 12..20 hex chars so REAL frozen-format DB identities validate.
DB_IDENTITY_RE = re.compile(r"^opws_[0-9a-z_]+_[0-9a-f]{8}_[0-9]{6}_[0-9a-f]{12,20}$")

REQUIRED_IDENTITY_FIELDS = [
    "task_id", "arm_id", "effective_tree_oid", "scope_hash",
    "reference_patch_sha256", "reference_patch_bytes", "test_contract_hash",
    "five_field_provisional_id",
]
REQUIRED_TOP_LEVEL = [
    "schema", "identity", "f2p_nodes", "f2p_repetitions",
    "f2p_nodes_sha256", "execution_id", "process", "database", "times",
    "junit_receipts", "resources", "cost", "teardown_receipt", "host",
    "environment", "pinned_image", "materialize_provenance",
]
NOT_MEASURED = "NOT_MEASURED"


JUNIT_PASS = """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" tests="1" failures="0" errors="0">
  <testcase classname="saleor.app.tests.test_validators" name="test_new_tab_relative_url_without_app_url" time="0.01"/>
</testsuite>
"""
JUNIT_FAIL = """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" tests="1" failures="1" errors="0">
  <testcase classname="saleor.app.tests.test_validators" name="test_new_tab_relative_url_without_app_url" time="0.01">
    <failure message="AssertionError: boom">assert False</failure>
  </testcase>
</testsuite>
"""


def classify_junit(path: Path) -> str:
    return str(_adapt.classify_junit(path))


def classify_body(body: str) -> str:
    """classify_junit for an in-memory XML string (mirrors file behavior)."""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "body.xml"
        p.write_text(body, encoding="utf-8")
        return classify_junit(p)


def _sha256_file(path: Path) -> str:
    return str(_adapt.sha256_file(path))


def _iso_now() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _tag_for(arm_id: str) -> str:
    arms = {a["arm_id"]: a for a in _adapt.load_arms()}
    row = arms.get(arm_id)
    if row is None:
        raise ValueError(f"unknown arm {arm_id}")
    return str(_adapt.four_field_id(row))[:8]


def sample_run_receipt(
    arm_id: str = "RM_CSS",
    run_token: str = "M02E-TOKEN",
    junit_classifications: list[str] | None = None,
    **overrides: Any,
) -> dict:
    """A structurally complete, schema-valid run receipt (test/demo fixture).

    junit_classifications: 9 classifications in r0f0..r2f2 order; default
    derives from the control map (PASS for RM_CSS/FULL_REFERENCE, FAILURE for
    NEG); other arms default to PASS (arbitrary-arm outcomes are outcome data).
    """
    arms = {a["arm_id"]: a for a in _adapt.load_arms()}
    row = arms[arm_id]
    tag = _tag_for(arm_id)
    task8 = _adapt.FROZEN_TASK.split("-")[-1][:8]
    if junit_classifications is None:
        expected = _adapt.CONTROL_EXPECTED_JUNIT.get(arm_id, "PASS")
        junit_classifications = [expected] * JUNIT_RECEIPTS_EXPECTED
    if len(junit_classifications) != JUNIT_RECEIPTS_EXPECTED:
        raise ValueError(f"need exactly {JUNIT_RECEIPTS_EXPECTED} classifications")
    start = datetime.datetime(2026, 11, 2, 8, 0, 0, tzinfo=datetime.UTC)
    end = start + datetime.timedelta(minutes=4, seconds=10)
    fid = row["five_field_provisional_id"]
    base = {
        "schema": RECEIPT_SCHEMA,
        "identity": {
            "task_id": _adapt.FROZEN_TASK,
            "arm_id": arm_id,
            "effective_tree_oid": row["effective_tree_oid"],
            "scope_hash": row["scope_hash"],
            "reference_patch_sha256": row["patch_sha256"],
            "reference_patch_bytes": row["patch_bytes"],
            "test_contract_hash": row["test_contract_hash"],
            "five_field_provisional_id": fid,
        },
        "f2p_nodes": _adapt.F2P_NODES,
        "f2p_nodes_sha256": _adapt.F2P_NODES_SHA256,
        "f2p_repetitions": F2P_REPETITIONS,
        "execution_id": _adapt.execution_id_for(arm_id, run_token),
        "process": {
            "pid": 4242 + hash(arm_id) % 1000,
            "driver_argv": ["python", "t12_m02_driver.py", "run", "--arm", arm_id],
            "container_oci_id": "sha256:a6e743589b60a4c15676eece07f52ed8347dc501bc782cc53ddffb7200d06c4c",
        },
        "database": {
            "engine": "sqlite",
            "db_identity": f"opws_{arm_id.lower()[:8]}_{task8}_083233_ab12cd34ef56",
            "db_created_receipt": True,
        },
        "times": {
            "start_utc": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_utc": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "monotonic": True,
            "wall_seconds": (end - start).total_seconds(),
        },
        "junit_receipts": [],
        "resources": {
            "cpu_seconds": 96.4,
            "peak_ram_mb": 1845.2,
            "disk_bytes": 212401152,
            "network_bytes": 0,
            "sampler": "resource_sampler_v1 (pinned host sampler, frozen stage)",
        },
        "cost": {
            "benchmark_api_model_usd": 0.0,
            "request_count": 0,
            "provider_receipts": [],
            "zero_generation_api_declared": True,
            "note": "reference-patch phase: zero benchmark API; orchestration cost recorded separately",
        },
        "teardown_receipt": {
            "present": True,
            "db_deleted": True,
            "workspace_removed": True,
            "path": "teardown_receipt.json",
        },
        "host": {"hostname": "OPWS-RUNTIME-COMPAT-2026-10-26", "os": "WSL2/Windows"},
        "environment": {"environment_id": "5186f584ed178ef10e02e919f15716096a01fe0bdac2f8f99238889187d81048"},
        "pinned_image": {
            "image": "opws-py312-isolated",
            "oci_id": "sha256:a6e743589b60a4c15676eece07f52ed8347dc501bc782cc53ddffb7200d06c4c",
        },
        "materialize_provenance": {
            "materializer": "scripts/opws_phase3b_patch_materialize.py",
            "scope_source": _adapt.ARM_SCOPE_SOURCES[arm_id].get("source"),
            "classification_input": _adapt.CLASSIFICATION_INPUT_STATUS,
            "tree_oid": row["effective_tree_oid"],
        },
        "run_token": run_token,
    }
    for i in range(JUNIT_RECEIPTS_EXPECTED):
        rep, node = divmod(i, 3)
        base["junit_receipts"].append({
            "filename": f"{task8}_{tag}_r{rep}_f{node}.xml",
            "node_id": _adapt.F2P_NODES[node],
            "repetition": rep,
            "classification": junit_classifications[i],
            "sha256": None,  # filled by validator from the actual file
        })
    base.update(overrides)
    return base


def write_run_receipt(run_dir: Path, receipt: dict) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    p = run_dir / RECEIPT_FILENAME
    p.write_text(json.dumps(receipt, indent=2, default=str), encoding="utf-8")
    return p


def materialize_junit_dir(run_dir: Path, receipt: dict,
                         xml_bodies: list[str] | None = None) -> None:
    """Write the 9 JUnit XMLs a receipt declares (test fixture helper)."""
    jdir = run_dir / JUNIT_DIR_REL
    jdir.mkdir(parents=True, exist_ok=True)
    bodies = xml_bodies or [JUNIT_PASS for _ in range(JUNIT_RECEIPTS_EXPECTED)]
    for i, entry in enumerate(receipt["junit_receipts"]):
        body = bodies[i % len(bodies)]
        (jdir / entry["filename"]).write_text(body, encoding="utf-8")


def validate_run_receipt(run_dir: Path) -> dict:
    """Validate one option-B run dir: schema, completeness, classification and
    physical-identity fields.  Missing proof → STOP/NOT_RUN; never silent PASS.
    """
    issues: list[str] = []
    rpath = run_dir / RECEIPT_FILENAME
    if not rpath.is_file():
        return {"status": "NOT_RUN", "reason": "run_receipt.json absent",
                "dir": str(run_dir)}
    try:
        rec = json.loads(rpath.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"status": "STOP", "issues": [f"run_receipt.json unreadable: {exc}"],
                "dir": str(run_dir)}
    if not isinstance(rec, dict):
        return {"status": "STOP", "issues": ["run_receipt.json is not a JSON object"]}
    if rec.get("schema") != RECEIPT_SCHEMA:
        return {"status": "STOP", "issues": [
            f"schema mismatch: {rec.get('schema')!r} != {RECEIPT_SCHEMA!r}"]}

    missing_top = [k for k in REQUIRED_TOP_LEVEL if k not in rec]
    if missing_top:
        issues.append(f"missing top-level sections: {missing_top}")
    ident = rec.get("identity") or {}
    missing_id = [k for k in REQUIRED_IDENTITY_FIELDS if k not in ident]
    if missing_id:
        issues.append(f"missing identity fields: {missing_id}")

    arm_id = ident.get("arm_id")
    row = next((a for a in _adapt.load_arms() if a["arm_id"] == arm_id), None)
    if row is None:
        issues.append(f"arm_id {arm_id!r} is not in the frozen 13-arm set")
    else:
        if ident.get("task_id") != _adapt.FROZEN_TASK:
            issues.append(f"task_id {ident.get('task_id')!r} != {_adapt.FROZEN_TASK}")
        for field, key in (("effective_tree_oid", "effective_tree_oid"),
                           ("scope_hash", "scope_hash"),
                           ("reference_patch_sha256", "patch_sha256"),
                           ("reference_patch_bytes", "patch_bytes"),
                           ("test_contract_hash", "test_contract_hash"),
                           ("five_field_provisional_id", "five_field_provisional_id")):
            if ident.get(field) != row[key]:
                issues.append(f"identity {field} {ident.get(field)!r} != frozen {row[key]!r}")

    # JUnit completeness: exactly 9 receipts, each node exactly 3 times.
    jreps = rec.get("junit_receipts") or []
    jdir = run_dir / JUNIT_DIR_REL
    if len(jreps) != JUNIT_RECEIPTS_EXPECTED:
        issues.append(
            f"junit_receipts entries {len(jreps)} != expected {JUNIT_RECEIPTS_EXPECTED}")
    filenames = [e.get("filename", "") for e in jreps]
    if len(set(filenames)) != len(filenames):
        issues.append("duplicate junit filenames in receipt")
    node_counts: dict[str, int] = {}
    extra: set[str] = set()
    for fname in filenames:
        m = JUNIT_RE.match(fname)
        if not m:
            issues.append(f"junit filename does not match frozen scheme: {fname}")
            continue
        rep, node = m.group("rep"), m.group("node")
        key = f"r{rep}_f{node}"
        node_counts[key] = node_counts.get(key, 0) + 1
        (jdir / fname)
    if len(node_counts) != JUNIT_RECEIPTS_EXPECTED:
        issues.append(
            f"junit coverage {len(node_counts)} distinct r/f slots != {JUNIT_RECEIPTS_EXPECTED}"
            " (expect each of 3 nodes x 3 repetitions)")
    for fname in sorted(p.name for p in jdir.glob("*.xml")):
        if fname not in set(filenames):
            extra.add(fname)
    if extra:
        issues.append(f"junit files present but undeclared: {sorted(extra)}")
    # per-file classification + existing-file verification + declared==actual
    for entry in jreps:
        fp = jdir / entry.get("filename", "")
        if not fp.is_file():
            issues.append(f"declared junit file missing on disk: {entry.get('filename')}")
            continue
        dig = _sha256_file(fp)
        entry["sha256"] = dig
        actual = classify_junit(fp)
        declared = entry.get("classification")
        if actual == "MALFORMED":
            issues.append(f"junit MALFORMED: {entry.get('filename')}")
        if declared not in ("PASS", "FAILURE", "ERROR", "MIXED"):
            issues.append(f"junit classification {declared!r} invalid: {entry.get('filename')}")
        elif declared != actual:
            issues.append(f"junit classification dishonesty: declared {declared!r} "
                          f"but file parses as {actual!r}: {entry.get('filename')}")
    if arm_id in _adapt.CONTROL_EXPECTED_JUNIT:
        expected = _adapt.CONTROL_EXPECTED_JUNIT[arm_id]
        bad = [e.get("filename") for e in jreps if e.get("classification") != expected
               and e.get("sha256")]
        # only flag when the file exists (missing already flagged)
        bad = [b for b in bad if (jdir / b).is_file()]
        if bad:
            issues.append(f"control arm {arm_id}: expected {expected}, got {bad}")

    # times monotonic
    times = rec.get("times") or {}
    try:
        start = datetime.datetime.strptime(times.get("start_utc", ""), "%Y-%m-%dT%H:%M:%SZ")
        end = datetime.datetime.strptime(times.get("end_utc", ""), "%Y-%m-%dT%H:%M:%SZ")
        if end < start:
            issues.append("end_utc before start_utc (non-monotonic times)")
    except Exception:
        issues.append("times.start_utc/end_utc must both be ISO-8601 UTC")
    wall = times.get("wall_seconds", NOT_MEASURED)
    if isinstance(wall, (int, float)) and wall < 0:
        issues.append("wall_seconds negative")

    # DB identity, process, execution_id
    db = rec.get("database") or {}
    dbi = db.get("db_identity")
    if not dbi:
        issues.append("database.db_identity missing (fresh per-arm DB identity required)")
    elif not DB_IDENTITY_RE.match(str(dbi)):
        issues.append(f"db_identity {dbi!r} does not match the frozen naming pattern")
    if db.get("db_created_receipt") is not True:
        issues.append("db_created_receipt must be true (fresh DB creation attested)")
    proc = rec.get("process") or {}
    if not isinstance(proc.get("pid"), int):
        issues.append("process.pid must be an integer")
    if not proc.get("container_oci_id"):
        issues.append("process.container_oci_id missing (pinned image identity)")
    if not rec.get("execution_id"):
        issues.append("execution_id missing (unique physical run identity per arm)")

    # teardown
    td = rec.get("teardown_receipt") or {}
    if td.get("present") is not True:
        issues.append("teardown_receipt.present must be true")
    if td.get("db_deleted") is not True:
        issues.append("teardown_receipt.db_deleted must attest DB removal")

    # resources: numbers or explicit NOT_MEASURED
    res = rec.get("resources") or {}
    for k in ("cpu_seconds", "peak_ram_mb", "disk_bytes", "network_bytes"):
        v = res.get(k)
        if not (isinstance(v, (int, float)) or v == NOT_MEASURED):
            issues.append(f"resources.{k} must be numeric or {NOT_MEASURED}")

    # cost/request receipts
    cost = rec.get("cost") or {}
    if not isinstance(cost.get("benchmark_api_model_usd"), (int, float)):
        issues.append("cost.benchmark_api_model_usd must be numeric")
    if not isinstance(cost.get("request_count"), int) or cost["request_count"] < 0:
        issues.append("cost.request_count must be a non-negative integer")
    if cost.get("request_count", 0) > 0 and not cost.get("provider_receipts"):
        issues.append("positive request_count requires per-request provider receipts")

    # host/environment/pinned image
    if not rec.get("host"):
        issues.append("host missing")
    if not rec.get("environment"):
        issues.append("environment missing (environment_id / pinned image)")
    if not rec.get("pinned_image"):
        issues.append("pinned_image missing")

    status = "STOP" if issues else "PASS"
    return {"status": status, "issues": issues, "dir": str(run_dir),
            "arm_id": arm_id, "junit_verified": len(jreps),
            "execution_id": rec.get("execution_id"),
            "db_identity": (rec.get("database") or {}).get("db_identity"),
            "process_pid": (rec.get("process") or {}).get("pid"),
            "duplicate_bytes_across_arms": [],  # filled by bundle scan
        }


def _bundle_scan(run_dirs: list[Path]) -> tuple[list[str], list[dict], dict]:
    """Cross-arm physical identity scan.  Returns (issues, byte_signals, idx)."""
    issues: list[str] = []
    signals: list[dict] = []
    seen_exec: dict[str, str] = {}
    seen_db: dict[str, str] = {}
    seen_pid: dict[str, str] = {}
    seen_receipt_bytes: dict[str, str] = {}
    seen_junit_bytes: dict[str, list[tuple[str, str, str]]] = {}
    idx: dict[str, Any] = {}
    for rd in run_dirs:
        rp = rd / RECEIPT_FILENAME
        if not rp.is_file():
            idx[str(rd)] = {"status": "NOT_RUN", "arm_id": None}
            continue
        raw = rp.read_bytes()
        rec = json.loads(raw.decode("utf-8"))
        arm = (rec.get("identity") or {}).get("arm_id")
        exec_id = rec.get("execution_id")
        dbi = (rec.get("database") or {}).get("db_identity")
        pid = (rec.get("process") or {}).get("pid")
        rh = _sha256_file(rp)
        if rh in seen_receipt_bytes:
            issues.append(
                f"byte-identical physical run_receipt.json claimed by TWO distinct "
                f"run directories ({seen_receipt_bytes[rh]} vs {rd}): the same "
                f"physical receipt cannot be reused across arms — STOP")
        seen_receipt_bytes[rh] = str(rd)
        if exec_id:
            if exec_id in seen_exec and seen_exec[exec_id] != arm:
                issues.append(f"execution_id {exec_id!r} reused across arms "
                              f"({seen_exec[exec_id]} vs {arm})")
            seen_exec[exec_id] = arm or str(rd)
        if dbi:
            if dbi in seen_db and seen_db[dbi] != arm:
                issues.append(f"db_identity {dbi!r} reused across arms "
                              f"({seen_db[dbi]} vs {arm}) — shared DB violates Option B")
            seen_db[dbi] = arm or str(rd)
        if pid:
            if pid in seen_pid and seen_pid[pid] != arm:
                issues.append(f"process pid {pid} reused across arms "
                              f"({seen_pid[pid]} vs {arm})")
            seen_pid[pid] = arm or str(rd)
        jdir = rd / JUNIT_DIR_REL
        for f in sorted(jdir.glob("*.xml")):
            dig = _sha256_file(f)
            seen_junit_bytes.setdefault(dig, []).append((arm or str(rd), str(f), rh))
        idx[str(rd)] = {"status": "READ", "arm_id": arm, "execution_id": exec_id,
                        "db_identity": dbi, "process_pid": pid,
                        "run_receipt_sha256": rh}
    for dig, hits in seen_junit_bytes.items():
        arms_involved = {h[0] for h in hits}
        if len(arms_involved) > 1:
            # byte-identical junit across arms is a SIGNAL to investigate, NOT
            # proof of reuse; Option B identity evidence decides reuse.
            signals.append({"duplicate_bytes": dig, "across_arms": sorted(arms_involved),
                            "files": [h[1] for h in hits],
                            "interpretation": "signal only — never inference of "
                                              "physical reuse from identical bytes"})
    return issues, signals, idx


def validate_receipts_bundle(run_dirs: list[Path]) -> dict:
    per_dir = [validate_run_receipt(rd) for rd in run_dirs]
    not_run = [r for r in per_dir if r["status"] == "NOT_RUN"]
    stopped = [r for r in per_dir if r["status"] == "STOP"]
    b_issues, signals, idx = _bundle_scan(run_dirs)
    status = "STOP" if (not_run or stopped or b_issues) else "PASS"
    return {
        "status": status,
        "schema": "receipts_bundle_scan_v1",
        "directories": per_dir,
        "cross_arm_identity_violations": b_issues,
        "duplicate_bytes_signals": signals,
        "never_infer_reuse_from_identical_bytes": True,
        "index": idx,
        "generated_utc": _iso_now(),
    }


def historical_r7_diagnostic(run_dir: Path) -> dict:
    """Scoped HISTORICAL diagnostic: classifies one R7 state dir (9 JUnits).

    Explicitly NOT M02-E evidence — historical R7 receipts never substitute
    for fresh option-B observations.  Signature reflects the frozen single-node
    R7 checker scope (repetitions are stability checks, not independent units).
    """
    res: dict[str, Any] = dict(_adapt.receipts_check(run_dir))
    res.update({
        "scope": "HISTORICAL_DIAGNOSTIC_ONLY",
        "not_m02e_evidence": True,
        "single_node_historical_scoped": True,
    })
    return res


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="T12 M02-D1 receipts validator (offline).")
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("validate-run", help="validate ONE option-B run dir (9 junit)")
    p.add_argument("run_dir")
    p = sub.add_parser("validate-bundle", help="validate a set of arm run dirs (cross-arm identity)")
    p.add_argument("dirs", nargs="+")
    p = sub.add_parser("r7-diagnostic", help="historical R7 classification diagnostic (scoped)")
    p.add_argument("run_dir")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "validate-run":
        res = validate_run_receipt(Path(args.run_dir))
        print(json.dumps(res, indent=2, default=str))
        return {"PASS": 0, "STOP": 1, "NOT_RUN": 2}[res["status"]]
    if args.command == "validate-bundle":
        res = validate_receipts_bundle([Path(d) for d in args.dirs])
        print(json.dumps(res, indent=2, default=str))
        return 1 if res["status"] == "STOP" else 0
    if args.command == "r7-diagnostic":
        res = historical_r7_diagnostic(Path(args.run_dir))
        print(json.dumps(res, indent=2, default=str))
        return {"PASS": 0, "STOP": 1, "NOT_RUN": 2}.get(res["status"], 1)
    return 3


if __name__ == "__main__":
    sys.exit(main())
