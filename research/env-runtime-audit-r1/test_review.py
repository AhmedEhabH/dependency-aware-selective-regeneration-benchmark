"""Audit-only P2P/F2P checks. No dependency, harness or benchmark execution."""

import csv
import hashlib
import json
import tomllib
from pathlib import Path

OUT = Path(__file__).resolve().parent
STORE = Path(r"D:\wp2_env_store")


def load(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def read_rows(path):
    return list(csv.DictReader(path.read_text(encoding="utf-8-sig").splitlines()))


def assess_proposal(proposal, calibration_status="BLOCKED_STOP"):
    """Review boundary for this audit, not a replacement for frozen harness guards."""
    reasons = []
    if proposal.get("replace_pyxb"):
        reasons.append("LOCAL_ARTIFACT_PRESENCE_IS_NOT_SUBSTITUTION_AUTHORITY")
    if proposal.get("change_python"):
        reasons.append("RUNTIME_CHANGE_NOT_AUTHORIZED_IN_AUDIT")
    if proposal.get("exclude_unit"):
        reasons.append("NO_APPLICABLE_PREDECLARED_EXCLUSION_RULE")
    if proposal.get("change_smoke"):
        reasons.append("FROZEN_SMOKE_SEMANTICS")
    if proposal.get("modify_harness"):
        reasons.append("FROZEN_R3_HARNESS")
    if proposal.get("modify_receipt") or proposal.get("modify_report"):
        reasons.append("IMMUTABLE_FAILED_CALIBRATION_EVIDENCE")
    if proposal.get("full_d7") and calibration_status != "PASS":
        reasons.append("CALIBRATION_BLOCKED_STOP")
    return {"allowed": not reasons, "reasons": reasons}


def test_p1_failure_proven_by_existing_evidence():
    receipt = json.loads((STORE / "receipts/D7_R3_CALIBRATION_12_RECEIPT.json").read_text())
    assert [receipt[k] for k in ["N_EXECUTED", "N_PASS", "N_FAIL"]] == [12, 11, 1]
    assert receipt["D7_R3_CALIBRATION_STATUS"] == "BLOCKED_STOP"
    text = (STORE / "tmp/d7_r3_cal_out/vu-b9808f19ace4/pytest_wt0.log").read_text()
    assert "13245 tests collected, 1 error" in text
    assert "AttributeError: module 'collections' has no attribute 'MutableSequence'" in text
    assert receipt["units"][-1]["run_summary"]["smoke"]["pytest_wt0"] == "2"


def test_p2_dependency_chain_and_source_identity():
    comparison = load("SOURCE_FIDELITY_COMPARISON.json")
    assert comparison["original_lock_equals_frozen_bytes"]
    packages = {p["name"].lower(): p for p in comparison["lock_packages"]}
    assert packages["authorizenet"]["dependencies"]["pyxb"] == "1.2.5"
    assert packages["pyxb"]["source"] == {"type": "directory", "url": "vendored/pyxb"}
    assert packages["authorizenet"]["source"]["type"] == "directory"
    wheels = load("LOCAL_WHEEL_AUDIT.json")
    wheel = next(w for w in wheels if "py312" in w["path"] and w["name"] == "PyXB")
    assert "class _PluralBinding (collections.MutableSequence):" in wheel["mutable_sequence_lines"]
    assert (
        wheel["content_sha256"]
        != load("STATIC_AUDIT_RESULTS.json")["py312_pyxb_vendored_checks"]["saleor-rc-e6198146186d"][
            "vendored_content_sha256"
        ]
    )


def test_p3_runtime_provenance_population():
    history = load("HISTORICAL_RUNTIME_BY_TASK.json")
    mapping = {"~3.8": "3.8", "~3.9": "3.9", "~3.12": "3.12", ">=3.12,<3.13": "3.12"}
    assert len(history) == 219
    for task in history.values():
        assert mapping[task["python_requirement"]] == task["assigned_python"]
    target = history["saleor-rc-e6198146186d"]
    assert target["python_requirement"] == "~3.12"
    assert target["python_evidence"]["pyproject_poetry_python"] == "~3.12"
    assert load("D7_R3_RUNTIME_FAILURE_OWNER_REVIEW.json")["runtime_assignment_type"] == "HISTORICAL_RUNTIME"


def test_p4_independent_wheel_hashes_and_frozen_authority():
    wheels = load("LOCAL_WHEEL_AUDIT.json")
    assert len(wheels) == 6
    for wheel in wheels:
        assert hashlib.sha256(Path(wheel["path"]).read_bytes()).hexdigest() == wheel["sha256"]
    accounting = json.loads((STORE / "receipts/R4B_FINAL_215_BUILD_ACCOUNTING.json").read_text())
    pyxb = next(w for w in wheels if "py312" in w["path"] and w["name"] == "PyXB")
    assert pyxb["sha256"] == accounting["pyxb_backport_wheel"]["sha256"]
    hash_text = (STORE / "manifests/WHEELHOUSE_HASHES_py312.json").read_text()
    for wheel in wheels:
        if wheel["name"] == "PyXB-X":
            assert wheel["sha256"] in hash_text


def test_p5_independent_blast_radius_recount():
    population = read_rows(STORE / "manifests/VALIDATION_UNIT_MATRIX.csv")
    report = read_rows(OUT / "D7_RUNTIME_BLAST_RADIUS.csv")
    assert len(population) == len(report) == 144
    assert {r["unit_id"] for r in population} == {r["unit_id"] for r in report}
    report = {r["unit_id"]: r for r in report}
    total_pyxb = total_auth = exposed = 0
    for unit in population:
        row = report[unit["unit_id"]]
        lock = tomllib.loads(Path(row["lock_path"]).read_text(encoding="utf-8"))
        packages = {p["name"].lower(): p for p in lock["package"]}
        pyxb = packages.get("pyxb", {})
        auth = packages.get("authorizenet", {})
        has_pyxb = pyxb.get("version") == "1.2.5"
        has_auth = auth.get("version") == "1.1.4"
        if has_pyxb:
            assert pyxb.get("python-versions", "*") == "*"
        if has_auth:
            assert auth.get("python-versions", "*") == "*"
        assert int(row["pyxb_1_2_5"]) == has_pyxb
        assert int(row["authorizenet_1_1_4"]) == has_auth
        total_pyxb += has_pyxb
        total_auth += has_auth
        exposed += has_pyxb and unit["python_version"] == "3.12"
    assert (total_pyxb, total_auth, exposed) == (84, 75, 2)


def test_p6_recommendation_requires_owner_and_preserves_boundary():
    packet = load("D7_R3_RUNTIME_FAILURE_OWNER_REVIEW.json")
    action = packet["recommended_next_action"]
    assert action["requires_separate_owner_authorization"] and not action["executed"]
    assert packet["answers"]["9_full_d7_authorized"] == "NO"
    assert packet["ROOT_CAUSE_CLASSIFICATION"] == "C_LOCK_RECONSTRUCTION_DEFECT"
    for key in [
        "FROZEN_EVIDENCE_CHANGED",
        "HARNESS_CHANGED",
        "ENVIRONMENT_CHANGED",
        "BENCHMARK_EXECUTED",
        "NETWORK_USED",
    ]:
        assert packet[key] is False


def test_f1_local_pyxbx_presence_does_not_authorize_replacement():
    assert not assess_proposal({"replace_pyxb": True, "local_pyxbx_exists": True})["allowed"]


def test_f2_unsupported_python_change_rejected():
    assert not assess_proposal({"change_python": "3.9", "historical_evidence": None})["allowed"]


def test_f3_posthoc_exclusion_rejected():
    assert not assess_proposal({"exclude_unit": "vu-b9808f19ace4", "observed_failure": True})["allowed"]


def test_f4_smoke_weakening_rejected():
    assert not assess_proposal({"change_smoke": "omit_collect"})["allowed"]


def test_f5_r3_harness_modification_rejected():
    assert not assess_proposal({"modify_harness": True})["allowed"]


def test_f6_receipt_and_report_mutation_rejected():
    assert not assess_proposal({"modify_receipt": True})["allowed"]
    assert not assess_proposal({"modify_report": True})["allowed"]


def test_f7_full_d7_blocked_by_calibration():
    assert not assess_proposal({"full_d7": True}, calibration_status="BLOCKED_STOP")["allowed"]
