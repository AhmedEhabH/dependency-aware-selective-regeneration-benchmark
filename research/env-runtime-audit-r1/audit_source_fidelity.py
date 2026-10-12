"""Supplement static source fidelity evidence, without executing dependency code."""

import json
import subprocess
import tomllib
import zipfile

from audit_static import OUT, REPO, STORE, TARGET, TASK, blob, dump, git_inputs, inputs, read, sha

manifest = json.loads((OUT / "FAILURE_EVIDENCE_MANIFEST.json").read_text(encoding="utf-8"))
inputs.update(manifest["files"])
git_inputs.update(manifest["git_blobs"])
original = blob(TARGET, "poetry.lock")
frozen = read(STORE / "artifacts/locks" / (TASK + "_poetry.toml"))
assert original == frozen
packages = tomllib.loads(original.decode())["package"]
selected = [p for p in packages if p["name"].lower() in ("pyxb", "authorizenet")]
source_compare = {}
for package in ("pyxb", "authorizenet"):
    prefix = "vendored/" + package + "/" + package + "/"
    names = (
        subprocess.check_output(["git", "-C", str(REPO), "ls-tree", "-r", "--name-only", TARGET, prefix])
        .decode()
        .splitlines()
    )
    source = {n[len("vendored/" + package + "/") :]: blob(TARGET, n) for n in names if n.endswith(".py")}
    wheels = [
        p
        for p in (STORE / "built_wheelhouse/canon_r4b/py312").rglob(package + "-*.whl")
        if "-1.2.5-" in p.name or "-1.1.4-" in p.name
    ]
    if package == "pyxb":
        wheels += list((STORE / "wheelhouse/py312").glob("PyXB_X*.whl"))
    comparisons = []
    for wheel in wheels:
        read(wheel)
        with zipfile.ZipFile(wheel) as z:
            wn = {n for n in z.namelist() if n.startswith(package + "/") and n.endswith(".py")}
            common = sorted(set(source) & wn)
            differences = [n for n in common if source[n] != z.read(n)]
            comparisons.append(
                {
                    "wheel": str(wheel),
                    "historical_python_files": len(source),
                    "wheel_python_files": len(wn),
                    "common": len(common),
                    "different_common_files": differences,
                    "historical_only": sorted(set(source) - wn),
                    "wheel_only": sorted(wn - set(source)),
                }
            )
    source_compare[package] = comparisons
for path in [STORE / "tmp/d7_r3_calibration_driver.py", STORE / "receipts/R4B_FINAL_215_BUILD_ACCOUNTING.json"]:
    read(path)
for name in ["R4B_FINAL_PYXB_COMPATIBILITY_BACKPORT.json", "PYXB_DISPOSITION_R4X_DELTA.json"]:
    read(STORE / "manifests" / name)
result = {
    "original_lock_equals_frozen_bytes": original == frozen,
    "raw_lock_sha256": sha(original),
    "raw_plus_lf_sha256": sha(original + b"\n"),
    "lock_packages": selected,
    "source_comparisons": source_compare,
    "notes": [
        "Python-file equality is not whole-distribution or scientific equivalence.",
        "No dependency code imported, installed, or built.",
    ],
}
dump("SOURCE_FIDELITY_COMPARISON.json", result)
dump("FAILURE_EVIDENCE_MANIFEST.json", {**manifest, "files": inputs, "git_blobs": git_inputs})
print("Source fidelity comparison written; original lock bytes match frozen lock.")
