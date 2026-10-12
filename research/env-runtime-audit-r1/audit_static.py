"""Local-only M17 static audit. Never imports task/harness code or writes the store."""

import csv
import email
import hashlib
import json
import re
import subprocess
import tomllib
import zipfile
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
STORE = Path(r"D:\wp2_env_store")
MASTER = Path(r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355")
REPO = MASTER / "project/dist/pilot-repo-cache/saleor"
ENV = MASTER / "m17-posteligibility-dev/research/wp2/m17_v1/r2b/environment/ENVIRONMENT_MATRIX_248.json"
TARGET = "e6198146186d1c782bf46f6c9439fa05b1049b2f"
TASK = "saleor-rc-e6198146186d"
UNIT = "vu-b9808f19ace4"
inputs = {}
git_inputs = {}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    path = Path(path)
    data = path.read_bytes()
    inputs[str(path)] = {"sha256": sha(data), "bytes": len(data)}
    return data


def js(path):
    return json.loads(read(path))


def rows(path):
    return list(csv.DictReader(read(path).decode("utf-8-sig").splitlines()))


def blob(commit, name, optional=False):
    p = subprocess.run(["git", "-C", str(REPO), "show", f"{commit}:{name}"], capture_output=True, check=False)
    if p.returncode:
        if optional:
            return None
        raise RuntimeError(p.stderr.decode())
    git_inputs[f"{commit}:{name}"] = {"sha256": sha(p.stdout), "bytes": len(p.stdout)}
    return p.stdout


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def norm(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def classify(req):
    if req in ("~3.12", ">=3.12,<3.13"):
        return "EXPLICIT_SUPPORT_3_12"
    if req in ("~3.8", "~3.9"):
        return "EXPLICIT_EXCLUDE_3_12"
    return "UNKNOWN"


def main():
    receipt = js(STORE / "receipts/D7_R3_CALIBRATION_12_RECEIPT.json")
    assert (receipt["D7_R3_CALIBRATION_STATUS"], receipt["N_EXECUTED"], receipt["N_PASS"], receipt["N_FAIL"]) == (
        "BLOCKED_STOP",
        12,
        11,
        1,
    )
    assert receipt["first_failure"]["unit"] == UNIT
    for path in [
        STORE / "reports/D7_R3_CALIBRATION_12_REPORT.md",
        STORE / "manifests/D7_CALIBRATION_12_PLAN.json",
        STORE / "harness/d7_r3/D7_R3_HARNESS_CONTRACT.md",
    ]:
        read(path)
    freeze = js(STORE / "manifests/D7_R3_HARNESS_FREEZE.json")
    harness_checks = {}
    for name, record in freeze["harness_files"].items():
        data = read(STORE / "harness/d7_r3" / name)
        if name == "D7_R3_HARNESS_MANIFEST.json":
            harness_checks[name] = sha(data) == receipt["manifest_hashes"]["manifest_actual_file_sha256"]
        else:
            harness_checks[name] = sha(data) == record["sha256"]
    assert all(harness_checks.values())
    for path in sorted((STORE / "tmp/d7_r3_cal_out" / UNIT).iterdir()):
        if path.is_file():
            read(path)
    pop = rows(STORE / "manifests/VALIDATION_UNIT_MATRIX.csv")
    tasks = {r["task_id"]: r for r in rows(STORE / "manifests/TASK_ENV_MATRIX.csv")}
    env = {r["task_id"]: r for r in js(ENV)["per_task"]}
    assert len(pop) == 144
    task_data = {}
    for i, (tid, task) in enumerate(tasks.items(), 1):
        raw = blob(task["target_commit"], "pyproject.toml")
        pp = tomllib.loads(raw.decode())
        req = pp.get("tool", {}).get("poetry", {}).get("dependencies", {}).get("python") or pp.get("project", {}).get(
            "requires-python"
        )
        task_data[tid] = {
            "target_commit": task["target_commit"],
            "python_requirement": req,
            "compatibility": classify(req),
            "assigned_python": task["python_version"],
            "era": task["era"],
            "source_pyproject_sha256": sha(raw),
            "frozen_pyproject_sha256": task["pyproject_sha256"],
            "python_evidence": env[tid]["python_evidence"],
        }
        if i % 50 == 0:
            print(f"Historical runtime declarations: {i}/{len(tasks)}", flush=True)
    results = []
    lock_evidence = {}
    special = {}
    for unit in pop:
        members = unit["member_task_ids"].split(";")
        tid = members[0]
        lock_path = (
            STORE / "artifacts/locks" / (tid + "_" + ("poetry" if unit["lock_type"] == "poetry" else "uv") + ".toml")
        )
        raw = read(lock_path)
        # Phase A accepts raw Git bytes or raw bytes plus one LF (E1 evidence convention).
        logical_sha = unit["lock_sha256"] if unit["lock_sha256"] in (sha(raw), sha(raw + b"\n")) else sha(raw)
        assert logical_sha == unit["lock_sha256"], (tid, logical_sha, unit["lock_sha256"])
        data = tomllib.loads(raw.decode("utf-8"))
        pkgs = data.get("package", [])
        selected = [p for p in pkgs if norm(p["name"]) in ("pyxb", "pyxb-x", "authorizenet")]
        pins = {norm(p["name"]) + "==" + p.get("version", "") for p in selected}
        directories = [p for p in pkgs if p.get("source", {}).get("type") == "directory"]
        categories = {task_data[t]["compatibility"] for t in members}
        category = next(iter(categories)) if len(categories) == 1 else "MIXED"
        out = {
            **unit,
            "historical_python_requirements": ";".join(
                sorted({task_data[t]["python_requirement"] or "UNKNOWN" for t in members})
            ),
            "historical_3_12_classification": category,
            "pyxb_1_2_5": int("pyxb==1.2.5" in pins),
            "authorizenet_1_1_4": int("authorizenet==1.1.4" in pins),
            "same_failing_lock": int(unit["lock_sha256"] == tasks[TASK]["lock_sha256"]),
            "v2_editable_plus_lock_dev": int(unit["install_route"] == "V2_EDITABLE_PLUS_LOCK_DEV"),
            "assigned_py312": int(unit["python_version"] == "3.12"),
            "directory_source_names": ";".join(sorted(p["name"] for p in directories)),
            "directory_pyxb": int(any(norm(p["name"]) == "pyxb" for p in directories)),
            "lock_path": str(lock_path),
            "lock_file_sha256": sha(raw),
        }
        out["py312_pyxb_1_2_5"] = out["assigned_py312"] * out["pyxb_1_2_5"]
        results.append(out)
        if selected or directories:
            lock_evidence[unit["unit_id"]] = {
                "packages": selected,
                "directory_packages": directories,
                "metadata": {
                    k: v
                    for k, v in data.get("metadata", {}).items()
                    if k in ("lock-version", "python-versions", "content-hash")
                },
            }
        if out["py312_pyxb_1_2_5"]:
            for t in members:
                commit = tasks[t]["target_commit"]
                b = blob(commit, "vendored/pyxb/pyxb/binding/content.py", optional=True)
                special[t] = {
                    "commit": commit,
                    "vendored_content_sha256": sha(b) if b else None,
                    "uses_collections_abc": b is not None and b"collections.abc.MutableSequence" in b,
                }
    with (OUT / "D7_RUNTIME_BLAST_RADIUS.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    evidence = {}
    for name in [
        "pyproject.toml",
        "poetry.lock",
        "Dockerfile",
        ".github/workflows/pytest.yml",
        "setup.py",
        "tox.ini",
        "runtime.txt",
        "vendored/pyxb/setup.py",
        "vendored/authorizenet/setup.py",
        "vendored/pyxb/pyxb/binding/content.py",
        "vendored/pyxb/pyxb/utils/six.py",
        "vendored/authorizenet/authorizenet/apicontractsv1.py",
        "saleor/payment/gateways/authorize_net/__init__.py",
    ]:
        raw = blob(TARGET, name, optional=True)
        if raw is None:
            evidence[name] = {"present": False}
            continue
        lines = raw.decode("utf-8", errors="replace").splitlines()
        hits = [
            {"line": i, "text": line}
            for i, line in enumerate(lines, 1)
            if re.search(
                r"python|authorizenet|pyxb|MutableSequence|collections|find_spec|find_module|directory", line, re.I
            )
        ]
        evidence[name] = {"present": True, "sha256": sha(raw), "excerpts": hits[:80]}
    wheels = []
    candidates = (
        list((STORE / "built_wheelhouse/canon_r4b").rglob("*pyxb*.whl"))
        + list((STORE / "built_wheelhouse/canon_r4b").rglob("authorizenet-1.1.4-*.whl"))
        + list((STORE / "wheelhouse/py312").glob("PyXB_X*.whl"))
    )
    for path in sorted(set(candidates)):
        raw = read(path)
        with zipfile.ZipFile(path) as z:
            meta_name = next(n for n in z.namelist() if n.endswith(".dist-info/METADATA"))
            meta = email.message_from_bytes(z.read(meta_name))
            top_names = [n for n in z.namelist() if n.endswith(".dist-info/top_level.txt")]
            content = z.read("pyxb/binding/content.py").decode() if "pyxb/binding/content.py" in z.namelist() else ""
            six = z.read("pyxb/utils/six.py").decode() if "pyxb/utils/six.py" in z.namelist() else ""
            wheels.append(
                {
                    "path": str(path),
                    "filename": path.name,
                    "sha256": sha(raw),
                    "name": meta["Name"],
                    "version": meta["Version"],
                    "requires_python": meta["Requires-Python"],
                    "requires_dist": meta.get_all("Requires-Dist", []),
                    "top_level": z.read(top_names[0]).decode().splitlines()
                    if top_names
                    else sorted(
                        {
                            n.split("/")[0]
                            for n in z.namelist()
                            if "/" in n and not n.split("/")[0].endswith(".dist-info")
                        }
                    ),
                    "provides_pyxb": "pyxb/__init__.py" in z.namelist(),
                    "content_sha256": sha(content.encode()) if content else None,
                    "mutable_sequence_lines": [
                        x for x in content.splitlines() if "MutableSequence" in x or "import collections" in x
                    ],
                    "six_find_spec": "def find_spec(" in six,
                }
            )
    for name in [
        "R4B_FINAL_PYXB_COMPATIBILITY_BACKPORT.json",
        "PYXB_DISPOSITION_R4X_DELTA.json",
        "R4B_FINAL_SOURCE_BUILD_CANON_FREEZE.json",
        "WHEELHOUSE_HASHES_py312.json",
        "WHEELHOUSE_HASHES_py39.json",
        "D7_REQUIRED_CLOSURE_AUDIT_R1.json",
    ]:
        read(STORE / "manifests" / name)
    for name in ["env_canon_phase_a_generate.py", "env_canon_phase_b_wheelhouse.py"]:
        read(Path(r"D:\wp2_env_canon/scripts") / name)
    date = subprocess.check_output(["git", "-C", str(REPO), "show", "-s", "--format=%aI%n%cI", TARGET]).decode().strip()
    summary = {
        "units": len(pop),
        "tasks": len(tasks),
        "counts": {
            k: sum(r[k] for r in results)
            for k in [
                "pyxb_1_2_5",
                "authorizenet_1_1_4",
                "same_failing_lock",
                "v2_editable_plus_lock_dev",
                "assigned_py312",
                "directory_pyxb",
                "py312_pyxb_1_2_5",
            ]
        },
        "unit_compatibility": dict(Counter(r["historical_3_12_classification"] for r in results)),
        "task_compatibility": dict(Counter(r["compatibility"] for r in task_data.values())),
        "requirements": dict(Counter(r["python_requirement"] for r in task_data.values())),
        "target_dates": date,
        "target_env_runtime_evidence": {
            k: env[TASK].get(k)
            for k in ["era", "python_evidence", "python_role_evidence", "conflict_present", "frozen_install_route"]
        },
        "harness_hash_checks": harness_checks,
        "py312_pyxb_vendored_checks": special,
    }
    dump("STATIC_AUDIT_RESULTS.json", summary)
    dump("HISTORICAL_RUNTIME_BY_TASK.json", task_data)
    dump("DEPENDENCY_SOURCE_EVIDENCE.json", lock_evidence)
    dump("TARGET_COMMIT_EVIDENCE.json", evidence)
    dump("LOCAL_WHEEL_AUDIT.json", wheels)
    manifest = {"store_read_only": True, "source_repo": str(REPO), "files": inputs, "git_blobs": git_inputs}
    dump("FAILURE_EVIDENCE_MANIFEST.json", manifest)
    index = [
        "# Failure evidence index",
        "",
        "Source files remain in place. SHA-256 covers raw bytes; Git blob hashes cover git show stdout.",
        "",
        "| Path | Bytes | SHA-256 |",
        "|---|---:|---|",
    ]
    index += [f"| `{p}` | {v['bytes']} | `{v['sha256']}` |" for p, v in sorted(inputs.items())]
    index += [
        "",
        "Historical Git blob identities are listed in FAILURE_EVIDENCE_MANIFEST.json.",
        "No large logs, wheel payloads, or repositories are copied.",
    ]
    (OUT / "FAILURE_EVIDENCE_INDEX.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
