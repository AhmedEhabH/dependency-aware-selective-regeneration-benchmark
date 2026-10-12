#!/usr/bin/env python3
"""M17 source-fidelity fresh calibration-12 driver (mission-local ADDITIVE tool).

Mission: M17_ENV_CANON_SOURCE_FIDELITY_R1_FRESH_CALIBRATION_12

This driver executes the frozen D7_CALIBRATION_12_PLAN.json population under
the FROZEN D7_R3 harness semantics, ONE UNIT PER INVOCATION (--unit N),
with the ONLY authorized environment change: dependency artifact reconstruction
now preserves historical source identity according to ``source_fidelity_r1``.

It does NOT edit any frozen file:
  * frozen R3 harness modules (d7_r3_closure / d7_r3_probes /
    d7_r3_native_specs) are imported READ-ONLY from harness/d7_r3 and mounted
    READ-ONLY into each container;
  * frozen store inputs (locks, wheelhouse, canon wheels, worktrees) are only
    read;
  * the frozen lock is never altered.

Source-aware resolution (additive):
  * derive the R3 runtime closure with the frozen closure function;
  * derive the source-aware closure identity with ``source_fidelity_r1``;
  * for DIRECTORY/PATH-source dependencies the merged runtime wheel input is
    overlaid with the frozen source-fidelity wheel artifact (same filename,
    exact frozen bytes verified against SOURCE_FIDELITY_PROVENANCE_MANIFEST);
  * REGISTRY dependencies keep the original frozen R3 wheelhouse+canon
    resolution (artifact closure equivalent to prior R3 semantics);
  * an unresolved non-registry historical source identity FAILS CLOSED.

Per-unit record includes the full gate evidence plus:
  unit id, task/member ids, runtime profile, python version, image id, lock
  SHA, old R3 closure identity, new source-aware closure identity, selected
  artifact hashes, source-fidelity artifacts used, network / install /
  pip check / native / wheel-tag / import / manage / pytest-collect gates,
  wall time, classification, PASS/FAIL, SOURCE_FIDELITY_CHANGE_APPLIED.

Usage:
  python scripts/sf_calibration12_driver.py --unit 1   # exactly one unit
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime

STORE = r"D:\wp2_env_store"
HARNESS = os.path.join(STORE, "harness", "d7_r3")
MANIFESTS = os.path.join(STORE, "manifests")
RECEIPTS = os.path.join(STORE, "receipts")
TMP = os.path.join(STORE, "tmp")

PLAN = os.path.join(MANIFESTS, "D7_CALIBRATION_12_PLAN.json")
MARKER_AUDIT = os.path.join(MANIFESTS, "MARKER_FILTER_AUDIT.json")
DOCKER_PROFILES = os.path.join(MANIFESTS, "DOCKER_PROFILE_MANIFEST.json")
D6_NATIVE = os.path.join(MANIFESTS, "D6_NATIVE_RESULTS.json")
TASK_ENV = os.path.join(MANIFESTS, "TASK_ENV_MATRIX.csv")
MATRIX = os.path.join(MANIFESTS, "VALIDATION_UNIT_MATRIX.csv")
LOCKS = os.path.join(STORE, "artifacts", "locks")
WHEELHOUSE = os.path.join(STORE, "wheelhouse", "py312")
CANON = os.path.join(STORE, "built_wheelhouse", "canon_r4b", "py312")
WORKTREES = os.path.join(TMP, "d7_r1_worktrees")

R3_RECEIPT = os.path.join(RECEIPTS, "D7_R3_CALIBRATION_12_RECEIPT.json")
R3_IMPACT = r"D:\wp2_sf_calibration_r1\research\source-fidelity-r1\POPULATION_CLOSURE_IMPACT_R1.json"
SF_MANIFEST = r"D:\wp2_sf_calibration_r1\research\source-fidelity-r1\SOURCE_FIDELITY_PROVENANCE_MANIFEST.json"
SF_WHEELS = r"D:\wp2_sf_calibration_r1\research\source-fidelity-r1\artifacts\wheels"
SALEOR_REPO = r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\dist\pilot-repo-cache\saleor"

# Fresh mission output root (C6): MUST NOT be D:\wp2_env_store\tmp\d7_r3_cal_out
OUT_ROOT = r"D:\wp2_sf_calibration_r1_store"
MERGED = os.path.join(OUT_ROOT, "merged", "py312")
REQS = os.path.join(OUT_ROOT, "reqs")
OUT_UNITS = os.path.join(OUT_ROOT, "units")
PROGRESS = os.path.join(OUT_ROOT, "progress.json")

IMAGE_BY_PROFILE = {
    "nat-34c1a3756742": "envcanon/saleor-env-native-nat-34c1a3756742:latest",
    "nat-a39687f3d19c": "envcanon/saleor-env-native-nat-a39687f3d19c:latest",
    "nat-cc2f641e9e04": "envcanon/saleor-env-native-nat-cc2f641e9e04:latest",
}

SRC_DIR = r"D:\wp2_sf_calibration_r1\src"
sys.path.insert(0, SRC_DIR)
sys.path.insert(0, HARNESS)

from d7_r3_closure import (  # noqa: E402
    derive_runtime_closure,
    resolve_runtime_artifacts,
)

from benchmark.wp2 import source_fidelity_r1 as sf  # noqa: E402


def utcnow() -> str:
    return datetime.now(UTC).isoformat()


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def docker_image_id(image: str) -> str | None:
    r = subprocess.run(["docker", "image", "inspect", "-f", "{{.Id}}", image],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def build_merged_wheelhouse() -> dict:
    """Wheel-only runtime input = wheelhouse/py312 + canon_r4b/py312 (canon wins)."""
    if os.path.isdir(MERGED):
        shutil.rmtree(MERGED)
    os.makedirs(MERGED, exist_ok=True)
    n_src = n_canon = 0
    for fn in sorted(os.listdir(WHEELHOUSE)):
        if fn.endswith(".whl"):
            shutil.copy2(os.path.join(WHEELHOUSE, fn), os.path.join(MERGED, fn))
            n_src += 1
    for identity_dir in sorted(os.listdir(CANON)):
        wd = os.path.join(CANON, identity_dir, "wheels")
        if not os.path.isdir(wd):
            continue
        for wf in sorted(os.listdir(wd)):
            if wf.endswith(".whl"):
                shutil.copy2(os.path.join(wd, wf), os.path.join(MERGED, wf))
                n_canon += 1
    wheels = sorted(fn for fn in os.listdir(MERGED) if fn.endswith(".whl"))
    return {"n_src": n_src, "n_canon": n_canon, "n_total": len(wheels)}


def source_fidelity_wheel_map() -> dict[str, dict]:
    """Map (normalized dist name, version) -> frozen source-fidelity artifact.

    Returns keyed by the frozen provenance manifest's built_artifacts (name,
    declared_version, output_filename, output_sha256, source_tree_sha256).
    """
    man = load_json(SF_MANIFEST)
    out: dict[tuple[str, str], dict] = {}
    for art in man["artifacts"]:
        norm = sf.normalize_dist_name(art["dependency_name"])
        out[(norm, str(art["declared_version"]).lower())] = art
    return out


def apply_source_fidelity_overlay(runtime_pins: list[str], source_records: list[dict]) -> dict:
    """Overlay frozen source-fidelity wheels into MERGED for DIRECTORY/PATH deps.

    The rule is generic and source-type-driven: for every runtime pin whose
    frozen lock records a DIRECTORY/PATH source, the merged wheel input is
    overlaid with the frozen source-fidelity wheel (identical filename, exact
    frozen bytes).  A DIRECTORY/PATH pin WITHOUT a frozen source-fidelity
    artifact FAILS CLOSED.  Any other non-registry source type (GIT/URL/FILE/
    UNKNOWN) with no exact historical identity FAILS CLOSED.
    Returns the overlay record (artifacts used + hashes).
    """
    sf_map = source_fidelity_wheel_map()
    rec_by_key: dict[tuple[str, str], dict] = {}
    for rec in source_records:
        norm = sf.normalize_dist_name(rec["name"])
        rec_by_key[(norm, str(rec["version"]).lower())] = rec

    overlay: list[dict] = []
    for pin in runtime_pins:
        pname, pver = pin.split("==", 1)
        norm = sf.normalize_dist_name(pname)
        key = (norm, pver.lower())
        rec = rec_by_key.get(key)
        stype = (rec or {}).get("source_type")
        if stype in (sf.SOURCE_TYPE_REGISTRY, None):
            # REGISTRY (or no lock record) -> original frozen R3 resolution.
            continue
        if stype not in (sf.SOURCE_TYPE_DIRECTORY, sf.SOURCE_TYPE_PATH):
            raise RuntimeError(
                f"FAIL_CLOSED: non-registry source '{stype}' for {pin} has no "
                "exact frozen historical artifact identity"
            )
        if key not in sf_map:
            raise RuntimeError(
                f"FAIL_CLOSED: DIRECTORY/PATH pin {pin} has no frozen "
                "source-fidelity artifact"
            )
        art = sf_map[key]
        src_path = os.path.join(SF_WHEELS, art["output_filename"])
        if not os.path.isfile(src_path):
            raise RuntimeError(
                f"FAIL_CLOSED: DIRECTORY/PATH artifact missing for {pin}: {src_path}"
            )
        disk_sha = sha256(src_path)
        if disk_sha != art["output_sha256"]:
            raise RuntimeError(
                f"FAIL_CLOSED: source-fidelity wheel hash mismatch for {pin}: "
                f"expected {art['output_sha256']} got {disk_sha}"
            )
        dst = os.path.join(MERGED, art["output_filename"])
        shutil.copy2(src_path, dst)
        overlay.append(
            {
                "pin": pin,
                "source_type": stype,
                "source_reference": art.get("vendored_source_path"),
                "source_tree_sha256": art.get("source_tree_sha256"),
                "target_commit": art.get("target_commit"),
                "output_filename": art["output_filename"],
                "output_sha256": disk_sha,
                "selected_sha256": disk_sha,
            }
        )
    return {
        "overlaid_pins": [o["pin"] for o in overlay],
        "artifacts": overlay,
        "n_overlaid": len(overlay),
    }


def unit_closure(unit: dict) -> dict:
    member = unit["member_task_ids"][0]
    lock = os.path.join(LOCKS, f"{member}_{unit['lock_type']}.toml")
    pps = []
    for tid in unit["member_task_ids"]:
        pp = os.path.join(WORKTREES, tid, "pyproject.toml")
        if os.path.isfile(pp):
            pps.append(pp)
    return derive_runtime_closure(lock, pps, MARKER_AUDIT)


def source_aware_closure(unit: dict) -> dict:
    """Frozen R1 source-aware closure identity for a unit (P10)."""
    member = unit["member_task_ids"][0]
    lock = os.path.join(LOCKS, f"{member}_{unit['lock_type']}.toml")
    with open(lock, "rb") as fh:
        text = fh.read().decode("utf-8")
    commit = member_to_commit(member)
    return sf.derive_source_aware_closure(
        text, commit, SALEOR_REPO, python_version="3.12",
        sys_platform="linux", lock_format=unit["lock_type"],
    )


def member_to_commit(tid: str) -> str:
    with open(TASK_ENV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["task_id"] == tid:
                return row["target_commit"]
    raise RuntimeError(f"no TASK_ENV row for {tid}")


def write_reqs(unit: dict, closure: dict) -> str:
    os.makedirs(REQS, exist_ok=True)
    out = os.path.join(REQS, f"{unit['validation_unit_id']}.txt")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(closure["runtime_pins"]) + "\n")
    return out


def verify_unit_identity(unit: dict) -> dict:
    """Verify the exact frozen identity of one unit before execution (FAIL CLOSED)."""
    res = {"validation_unit_id": unit["validation_unit_id"], "checks": {}}
    uid = unit["validation_unit_id"]
    ok = True

    with open(MATRIX, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    mrow = next((r for r in rows if r["unit_id"] == uid), None)
    if mrow is None:
        ok = False
        res["checks"]["matrix_row"] = "MISSING"
    else:
        checks = {
            "member_task_ids": mrow["member_task_ids"] == ";".join(unit["member_task_ids"]),
            "lock_sha256": mrow["lock_sha256"] == unit["lock_sha256"],
            "lock_type": mrow["lock_type"] == unit["lock_type"],
            "install_route": mrow["install_route"] == unit["install_route"],
            "native_profile_id": mrow["native_profile_id"] == unit["native_profile_id"],
            "docker_profile_id": mrow["docker_profile_id"] == unit["docker_profile_id"],
            "python_version": mrow["python_version"] == unit["python_version"],
        }
        res["checks"]["matrix_row"] = "OK" if all(checks.values()) else "MISMATCH"
        if not all(checks.values()):
            ok = False

    nid = unit["native_profile_id"]
    if nid not in IMAGE_BY_PROFILE:
        ok = False
        res["checks"]["image_map"] = "MISSING_PROFILE"
    else:
        image = IMAGE_BY_PROFILE[nid]
        res["image"] = image
        image_id = docker_image_id(image)
        res["image_id"] = image_id
        d6 = load_json(D6_NATIVE)
        d6_short = d6["image_ids"].get(image.replace(":latest", ""))
        short = image_id.replace("sha256:", "")[:12] if image_id else None
        match = bool(short) and (d6_short is None or short == d6_short)
        res["checks"]["image_id"] = "OK" if match else "MISMATCH"
        if not match:
            ok = False

    task_rows = {}
    with open(TASK_ENV, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            task_rows[r["task_id"]] = r
    lock_ok = True
    for tid in unit["member_task_ids"]:
        p = os.path.join(LOCKS, f"{tid}_{unit['lock_type']}.toml")
        disk = sha256(p) if os.path.isfile(p) else None
        ref = task_rows.get(tid, {}).get("lock_sha256_git_blob")
        if disk != ref:
            lock_ok = False
    res["checks"]["lock_artifacts"] = "OK" if lock_ok else "MISMATCH"
    if not lock_ok:
        ok = False

    res["pass_"] = ok
    return res


def container_script(wt_dirs: list[str], profile_pkgs: list[str]) -> str:
    wts = " ".join(f"/wt{i}" for i in range(len(wt_dirs)))
    lines = [
        "set +e",
        "mkdir -p /tmp/d7 /out",
        "echo '=== NETPROBE ==='",
        r'''python - <<'PYEOF'
import socket, json
host="pypi.org"; port=443
socket.setdefaulttimeout(3)
res={"dns":{"reachable":False},"tcp":[]}
try:
    infos=socket.getaddrinfo(host,port,proto=socket.IPPROTO_TCP)
    addrs=sorted({i[4][0] for i in infos})
    res["dns"]={"reachable":True,"addrs":addrs}
except socket.gaierror as e:
    res["dns"]={"reachable":False,"errstr":str(e)}
tcp_ok=False
for tgt in (res["dns"].get("addrs",[])[:2] or [host]):
    try:
        s=socket.create_connection((tgt,port),timeout=3); s.close(); tcp_ok=True
    except Exception:
        pass
if res["dns"]["reachable"] and tcp_ok:
    st="NETWORK_REACHABLE"
elif not res["dns"]["reachable"] and not tcp_ok:
    st="NETWORK_UNAVAILABLE"
else:
    st="AMBIGUOUS"
res["status"]=st
print("NET_STATUS="+st)
open("/tmp/d7/netprobe.json","w").write(json.dumps(res))
PYEOF''',
        "cp /tmp/d7/netprobe.json /out/netprobe.json",
        "echo '=== INSTALL (wheel-only, frozen closure) ==='",
        "T0=$(date +%s%3N)",
        "uv pip install --system --no-index --find-links /wheelhouse --only-binary=:all: -r /reqs/requirements-lock.txt >/tmp/d7/install.log 2>&1",  # noqa: E501
        "IR=$?",
        "T1=$(date +%s%3N)",
        "echo \"INSTALL_RC=$IR\"",
        "echo \"INSTALL_MS=$((T1-T0))\"",
        "cp /tmp/d7/install.log /out/install.log",
        "echo '=== PIPLIST ==='",
        "python -m pip list --format=freeze >/tmp/d7/pipfreeze.txt 2>&1",
        "cp /tmp/d7/pipfreeze.txt /out/pipfreeze.txt",
        "echo '=== TOOLHOUSE AUDIT (frozen) ==='",
        r'''PYTHONPATH=/harness python - <<'PYEOF'
import json, importlib.metadata
from d7_r3_probes import audit_toolhouse_contamination
names = sorted({d.metadata["Name"].lower().replace("_","-") for d in importlib.metadata.distributions()
              if d.metadata and d.metadata.get("Name")})
contam = audit_toolhouse_contamination(names)
print("TOOLHOUSE_PRESENT=" + json.dumps(contam))
data = {"contamination": contam, "n_installed": len(names)}
open("/out/toolhouse.json","w").write(json.dumps(data, indent=2, sort_keys=True))
PYEOF''',
        "echo '=== PIPCHECK ==='",
        "pip check >/tmp/d7/pipcheck.log 2>&1",
        "echo \"PIPCHECK_RC=$?\"",
        "cp /tmp/d7/pipcheck.log /out/pipcheck.log",
        "echo '=== NATIVE (frozen modules) ==='",
        f"echo '{{\"packages\": {json.dumps(profile_pkgs)}}}' >/tmp/d7/profile.json",
        r'''PYTHONPATH=/harness python - <<'PYEOF'
import json, subprocess, os
from d7_r3_native_specs import PATH_PROBE, EXEC_PROBE
from d7_r3_probes import derive_probe_payload, run_native_probes
profile = json.load(open("/tmp/d7/profile.json", encoding="utf-8"))
pkgs = profile["packages"]
try:
    payload = derive_probe_payload(pkgs)
except KeyError as e:
    print("NATIVE_SPEC_GAP=" + str(e))
    open("/out/native.json","w").write(json.dumps({"spec_gap": str(e)}))
    raise SystemExit(0)
out = subprocess.run(["ldconfig","-p"], capture_output=True, text=True).stdout or ""
loader_tokens = [ln.strip() for ln in out.splitlines() if ln.strip()]
fs = {}
exec_resolutions = {}
for pkg, spec in payload.items():
    if spec["kind"] == PATH_PROBE:
        fs[spec["path"]] = os.path.exists(spec["path"])
    elif spec["kind"] == EXEC_PROBE:
        exe = spec["executable"]
        r = subprocess.run(["sh","-lc","command -v " + exe], capture_output=True, text=True)
        resolved = (r.stdout or "").strip().splitlines()
        resolved = resolved[0] if resolved else ""
        if resolved:
            exec_resolutions[exe] = resolved
            fs[resolved] = os.path.exists(resolved)
failures = run_native_probes(payload, loader_tokens, fs, exec_resolutions)
print("NATIVE_FAILURES=" + json.dumps(failures))
print("EXEC_RESOLUTIONS=" + json.dumps(exec_resolutions))
open("/out/native.json","w").write(json.dumps({"failures": failures,
    "profile_packages": pkgs,
    "loader_tokens": loader_tokens[:40],
    "fs": fs,
    "exec_resolutions": exec_resolutions}, indent=2, sort_keys=True))
PYEOF''',
    ]
    if wts:
        lines += [
            "echo '=== SMOKE ==='",
            f"for wt in {wts}; do",
            "  if [ -d \"$wt\" ]; then",
            "    echo \"== SMOKE $(basename $wt) ==\"",
            "    cd \"$wt\"",
            "    python -c \"import saleor\" >/tmp/d7/import_$(basename $wt).log 2>&1",
            "    echo \"IMPORT_RC_$(basename $wt)=$?\"",
            "    cp /tmp/d7/import_$(basename $wt).log /out/import_$(basename $wt).log",
            "    if [ -f manage.py ]; then",
            "      python manage.py check --settings=saleor.tests.settings >/tmp/d7/manage_$(basename $wt).log 2>&1",
            "      echo \"MANAGE_RC_$(basename $wt)=$?\"",
            "      cp /tmp/d7/manage_$(basename $wt).log /out/manage_$(basename $wt).log",
            "    else",
            "      echo \"MANAGE_RC_$(basename $wt)=SKIP\"",
            "    fi",
            "    if [ -f pytest.ini ] || [ -f pyproject.toml ]; then",
            "      python -m pytest --collect-only -q >/tmp/d7/pytest_$(basename $wt).log 2>&1",
            "      echo \"PYTEST_RC_$(basename $wt)=$?\"",
            "      cp /tmp/d7/pytest_$(basename $wt).log /out/pytest_$(basename $wt).log",
            "    else",
            "      echo \"PYTEST_RC_$(basename $wt)=SKIP\"",
            "    fi",
            "  fi",
            "done",
        ]
    lines.append("echo 'D7_UNIT_DONE'")
    return "\n".join(lines)


def parse_output(out: str) -> dict:
    res = {}
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("NET_STATUS="):
            res["network_status"] = line.split("=", 1)[1]
        elif line.startswith("INSTALL_RC="):
            res["install_rc"] = int(line.split("=", 1)[1])
        elif line.startswith("INSTALL_MS="):
            res["install_ms"] = int(line.split("=", 1)[1])
        elif line.startswith("TOOLHOUSE_PRESENT="):
            res["toolhouse_present"] = json.loads(line.split("=", 1)[1] or "[]")
        elif line.startswith("PIPCHECK_RC="):
            res["pipcheck_rc"] = int(line.split("=", 1)[1])
        elif line.startswith("NATIVE_FAILURES="):
            res["native_failures"] = json.loads(line.split("=", 1)[1] or "[]")
        elif line.startswith("NATIVE_SPEC_GAP="):
            res["native_spec_gap"] = line.split("=", 1)[1]
        elif line.startswith("EXEC_RESOLUTIONS="):
            res["exec_resolutions"] = json.loads(line.split("=", 1)[1] or "{}")
        elif line.startswith("IMPORT_RC_"):
            k = line.split("=", 1)[0][len("IMPORT_RC_"):]
            res.setdefault("smoke", {})[f"import_{k}"] = line.split("=", 1)[1]
        elif line.startswith("MANAGE_RC_"):
            k = line.split("=", 1)[0][len("MANAGE_RC_"):]
            res.setdefault("smoke", {})[f"manage_{k}"] = line.split("=", 1)[1]
        elif line.startswith("PYTEST_RC_"):
            k = line.split("=", 1)[0][len("PYTEST_RC_"):]
            res.setdefault("smoke", {})[f"pytest_{k}"] = line.split("=", 1)[1]
    return res


def classify_unit(run: dict) -> str:
    """Mirror the frozen driver's simulate_unit gate order (fail closed)."""
    if run.get("network_status") != "NETWORK_UNAVAILABLE":
        return "NETWORK_FAIL_CLOSED"
    if run.get("install_rc") != 0:
        return "RUNTIME_ARTIFACT_CLOSURE_FAILURE"
    if run.get("toolhouse_present"):
        return "RUNTIME_TOOLHOUSE_CONTAMINATION"
    if run.get("pipcheck_rc") != 0:
        return "PIP_CHECK_FAIL"
    if run.get("native_spec_gap"):
        return "NATIVE_SPEC_GAP_FAIL_CLOSED"
    if run.get("native_failures"):
        return "NATIVE_FAIL"
    smoke = run.get("smoke", {})
    bad = [k for k, v in smoke.items() if isinstance(v, str) and v not in ("0", "SKIP")]
    if bad:
        return "SMOKE_FAIL"
    return "PASS"


def wheel_tag_gate(resolution: dict) -> dict:
    """Frozen wheel-tag gate = the frozen resolver's wheel-compatibility check.

    The frozen ``resolve_runtime_artifacts`` already filters candidates through
    ``wheel_compatible``; its ``missing`` / ``incompatible`` results ARE the
    wheel-tag gate evidence.  This wrapper records it with the gate name.
    """
    return {
        "gate": "WHEEL_TAG",
        "pass_": resolution["pass_"],
        "missing": resolution.get("missing", []),
        "incompatible": resolution.get("incompatible", []),
    }


def run_unit(unit: dict) -> dict:
    image = IMAGE_BY_PROFILE[unit["native_profile_id"]]
    image_id = docker_image_id(image)
    uid = unit["validation_unit_id"]
    out_dir = os.path.join(OUT_UNITS, uid)
    os.makedirs(out_dir, exist_ok=True)

    identity = verify_unit_identity(unit)
    if not identity["pass_"]:
        return {
            "validation_unit_id": uid,
            "ordered_calibration_index": unit["ordered_calibration_index"],
            "member_task_ids": unit["member_task_ids"],
            "mapped_task_count": unit["mapped_task_count"],
            "native_profile_id": unit["native_profile_id"],
            "docker_profile_id": unit["docker_profile_id"],
            "image": image, "image_id": image_id,
            "identity_check": identity,
            "identity_pass": False,
            "execution_performed": False,
            "final_classification": "IDENTITY_MISMATCH_FAIL_CLOSED",
            "logs_dir": out_dir,
        }

    closure = unit_closure(unit)
    source_aware = source_aware_closure(unit)
    r3_receipt = load_json(R3_RECEIPT)
    r3_impact = load_json(R3_IMPACT)

    old_r3_identity = next(
        (u.get("closure_identity_sha256") for u in r3_receipt["units"]
         if u["validation_unit_id"] == uid), None)
    impact_entry = next(
        (u for u in r3_impact["changed"] if u["validation_unit_id"] == uid), None)

    # build merged wheelhouse with R3 semantics + source-fidelity overlay
    merge = build_merged_wheelhouse()
    overlay = apply_source_fidelity_overlay(closure["runtime_pins"], source_aware["records"])
    wheels = sorted(fn for fn in os.listdir(MERGED) if fn.endswith(".whl"))
    resolution = resolve_runtime_artifacts(closure["runtime_pins"], wheel_file_list=wheels)
    wtg = wheel_tag_gate(resolution)

    # source-fidelity change applied when any DIRECTORY/PATH pin was overlaid
    sf_applied = overlay["n_overlaid"] > 0

    req_path = write_reqs(unit, closure)

    dmp = load_json(DOCKER_PROFILES)
    profile_pkgs = dmp.get("native_profiles", {}).get(unit["native_profile_id"], [])

    wt_dirs = [os.path.join(WORKTREES, tid) for tid in unit["member_task_ids"]]
    script = container_script(wt_dirs, profile_pkgs)

    volumes = [
        "-v", f"{MERGED}:/wheelhouse:ro",
        "-v", f"{req_path}:/reqs/requirements-lock.txt:ro",
        "-v", f"{HARNESS}:/harness:ro",
        "-v", f"{out_dir}:/out:rw",
    ]
    for i, wt in enumerate(wt_dirs):
        volumes += ["-v", f"{wt}:/wt{i}:ro"]

    cmd = ["docker", "run", "--rm", "--network=none", *volumes, image, "sh", "-lc", script]
    start = utcnow()
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=5400000)
        docker_out, docker_err = r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return {"validation_unit_id": uid, "elapsed_seconds": None,
                "execution_performed": True,
                "final_classification": "TIMEOUT", "docker_error": "TIMEOUT_90MIN",
                "image": image, "image_id": image_id, "logs_dir": out_dir}
    except Exception as exc:
        return {"validation_unit_id": uid, "elapsed_seconds": None,
                "execution_performed": True,
                "final_classification": "ENVIRONMENT_RUNTIME_FAILURE",
                "docker_error": repr(exc), "image": image, "image_id": image_id,
                "logs_dir": out_dir}

    elapsed = round(time.time() - t0, 2)
    parsed = parse_output(docker_out)
    parsed["docker_exit"] = r.returncode
    if docker_err:
        parsed["docker_stderr_tail"] = docker_err[-500:]

    rec = {
        "validation_unit_id": uid,
        "ordered_calibration_index": unit["ordered_calibration_index"],
        "member_task_ids": unit["member_task_ids"],
        "mapped_task_count": unit["mapped_task_count"],
        "task_ids": unit["member_task_ids"],
        "python_version": unit["python_version"],
        "lock_type": unit["lock_type"],
        "lock_sha256": unit["lock_sha256"],
        "install_route": unit["install_route"],
        "native_profile_id": unit["native_profile_id"],
        "docker_profile_id": unit["docker_profile_id"],
        "image": image,
        "image_id": image_id,
        "identity_check": identity,
        "identity_pass": True,
        "old_r3_closure_identity_sha256": old_r3_identity,
        "new_source_aware_closure_identity_sha256": source_aware["closure_identity_sha256"],
        "old_canon_closure_identity_sha256": (impact_entry["old_canon_closure_identity_sha256"]
            if impact_entry else None),
        "source_aware_n_fail_closed": source_aware["n_fail_closed"],
        "source_aware_non_registry": sorted(
            {r["name"] for r in source_aware["records"] if r["source_type"] != "REGISTRY"}),
        "source_fidelity_change_applied": sf_applied,
        "source_fidelity_overlay": overlay,
        "merged_wheelhouse": merge,
        "selected_pyxb_authorizenet_hashes": {
            art["pin"]: art["selected_sha256"] for art in overlay["artifacts"]
            if art["pin"].lower().startswith(("pyxb", "authorizenet"))
        },
        "closure": {"n_pins": len(closure["pins"]), "n_runtime": len(closure["runtime_pins"]),
                    "excluded": closure["excluded"]},
        "resolution": resolution,
        "wheel_tag_gate": wtg,
        "resolution_passed": resolution["pass_"] and wtg["pass_"],
        "requirements_lock": req_path,
        "start_utc": start,
        "end_utc": utcnow(),
        "elapsed_seconds": elapsed,
        "run": parsed,
        "logs_dir": out_dir,
    }

    if not rec["resolution_passed"]:
        rec["final_classification"] = "RUNTIME_ARTIFACT_CLOSURE_FAILURE"
        rec["install_status"] = "NOT_RUN"
        rec["pip_check_status"] = "NOT_RUN"
        rec["network_status"] = "NOT_RUN"
        rec["native_status"] = "NOT_RUN"
        rec["smoke_status"] = "NOT_RUN"
        rec["execution_performed"] = False
        return rec

    rec["final_classification"] = classify_unit(parsed)
    rec["install_status"] = "PASS" if parsed.get("install_rc") == 0 else "FAIL"
    rec["pip_check_status"] = "PASS" if parsed.get("pipcheck_rc") == 0 else "FAIL"
    rec["network_status"] = parsed.get("network_status")
    native_cls = ("NATIVE_FAIL", "NATIVE_SPEC_GAP_FAIL_CLOSED", "HARNESS_DEFECT_NATIVE_SPEC")
    rec["native_status"] = "FAIL" if rec["final_classification"] in native_cls else "PASS"
    rec["smoke_status"] = "FAIL" if rec["final_classification"] == "SMOKE_FAIL" else "PASS"
    rec["execution_performed"] = True
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(description="SF calibration runner (one unit per invocation)")
    ap.add_argument("--unit", type=int, required=True, help="ordered_calibration_index 1..12")
    ap.add_argument("--merge-only", action="store_true", help="build merged wheelhouse + overlay then exit (preflight)")
    args = ap.parse_args()

    plan = load_json(PLAN)
    units = plan["units"]
    assert len(units) == 12, "plan != 12 units"
    if not (1 <= args.unit <= 12):
        print("UNIT_INDEX_OUT_OF_RANGE")
        return 2
    unit = units[args.unit - 1]

    os.makedirs(OUT_ROOT, exist_ok=True)
    if args.merge_only:
        merge = build_merged_wheelhouse()
        closure = unit_closure(unit)
        source_aware = source_aware_closure(unit)
        overlay = apply_source_fidelity_overlay(closure["runtime_pins"], source_aware["records"])
        print(json.dumps({"merge": merge, "overlay": overlay}, indent=2, sort_keys=True))
        return 0

    print("MERGED_WHEELHOUSE")
    print(json.dumps(build_merged_wheelhouse()))
    print(f"RUN {args.unit}/12 {unit['validation_unit_id']} tasks={unit['member_task_ids']} "
          f"image={IMAGE_BY_PROFILE[unit['native_profile_id']]}", flush=True)
    rec = run_unit(unit)

    progress = {"completed": [], "stopped_early": False}
    if os.path.isfile(PROGRESS):
        progress = load_json(PROGRESS)
    progress["completed"] = [c for c in progress["completed"]
                             if c["validation_unit_id"] != unit["validation_unit_id"]]
    progress["completed"].append(rec)
    with open(PROGRESS, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)

    print(json.dumps({k: rec.get(k) for k in
                      ("validation_unit_id", "elapsed_seconds", "final_classification",
                       "network_status", "install_status", "pip_check_status",
                       "native_status", "smoke_status", "identity_pass",
                       "source_fidelity_change_applied")}), flush=True)
    if rec["final_classification"] != "PASS":
        print(f"UNIT_FAIL {unit['validation_unit_id']} -> {rec['final_classification']}", flush=True)
        return 1
    print(f"UNIT_PASS {unit['validation_unit_id']}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
