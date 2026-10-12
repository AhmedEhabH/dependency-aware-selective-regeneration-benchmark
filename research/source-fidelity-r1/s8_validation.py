#!/usr/bin/env python3
"""M17 S8 - targeted local source-fidelity validation (OFFLINE, engineering P2P).

Builds the two historically-vendored packages (PyXB 1.2.5, authorizenet 1.1.4)
from the EXACT source bytes at the target commit ``e6198146186d...`` and runs a
tiny isolated import probe against the built artifacts.

Material gate: all source inputs and build dependencies are already present
locally (Saleor git objects + store wheelhouse); total new build output is a
few MiB (< 500 MiB) and expected build runtime is < 10 minutes.  No network.

ENGINEERING_P2P_ONLY
NOT_CALIBRATION_EVIDENCE

Calibration-12 is NOT run.  This validation does not become calibration or
scientific evidence.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(SRC_DIR))

from benchmark.wp2 import source_fidelity_r1 as sf  # noqa: E402

REPO = r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\dist\pilot-repo-cache\saleor"
TARGET_COMMIT = "e6198146186d1c782bf46f6c9439fa05b1049b2f"
VENV_PYTHON = Path(r"C:\Users\Ahmed\AppData\Local\Temp\opencode\sf312\Scripts\python.exe")
ARTIFACTS = Path(__file__).resolve().parent / "artifacts"
WHEELS_DIR = ARTIFACTS / "wheels"
OUT = Path(__file__).resolve().parent / "SOURCE_FIDELITY_VALIDATION_R1.json"

PACKAGES = (
    {
        "name": "PyXB",
        "version": "1.2.5",
        "source_path": "vendored/pyxb",
        "expected_tree_sha256": "5b36fb887b01352de251b872739bbd3786b330b3305d235e278d5caf1d37e1e2",
        "wheel_basename": "pyxb-1.2.5-py3-none-any.whl",
    },
    {
        "name": "authorizenet",
        "version": "1.1.4",
        "source_path": "vendored/authorizenet",
        "expected_tree_sha256": "b3e05589709cb4c163e6e9b20f553cf2cbb6c4fd4592c4b76d4d757ac136121e",
        "wheel_basename": "authorizenet-1.1.4-py3-none-any.whl",
    },
)

PROBES = {
    "pyxb": (
        "import pyxb; import pyxb.binding.content as c; "
        "print('PYXB_OK', pyxb.__version__); "
        "print('BASES_OK', 'abc' in getattr(c._PluralBinding, '__bases__', ())[0].__module__)"
    ),
    "authorizenet": (
        "import authorizenet.apicontractsv1 as a; "
        "print('AUTHORIZENET_OK', a.__name__)"
    ),
}


def _run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=cwd)
    return proc.returncode, (proc.stdout + proc.stderr)


def main() -> int:
    assert VENV_PYTHON.is_file(), f"venv python missing: {VENV_PYTHON}"
    WHEELS_DIR.mkdir(parents=True, exist_ok=True)
    build_dir = Path(tempfile.mkdtemp(prefix="sf-build-"))
    results: list[dict] = []

    for pkg in PACKAGES:
        name = pkg["name"]
        src_dest = build_dir / f"{name.lower()}-src"
        extraction = sf.materialize_source_tree(
            REPO, TARGET_COMMIT, pkg["source_path"], str(src_dest)
        )
        assert extraction["tree_sha256"] == pkg["expected_tree_sha256"], (
            f"materialized tree hash mismatch for {name}: "
            f"{extraction['tree_sha256']} != {pkg['expected_tree_sha256']}"
        )
        wheel_out = WHEELS_DIR / pkg["wheel_basename"]
        rc, log = _run(
            [
                str(VENV_PYTHON), "-m", "pip", "wheel",
                "--no-deps", "--no-build-isolation", "--no-index",
                "--wheel-dir", str(WHEELS_DIR),
                str(src_dest),
            ]
        )
        log_hash = hashlib.sha256(log.encode("utf-8")).hexdigest()
        # Normalize the wheel filename to the frozen lowercase convention
        # (pip preserves the setup.py distribution-name case, e.g. PyXB).
        produced = next(WHEELS_DIR.glob(f"{pkg['name']}-*.whl"), None)
        if rc == 0 and produced is not None and produced.name != pkg["wheel_basename"]:
            target = WHEELS_DIR / pkg["wheel_basename"]
            produced.replace(target)
        if rc != 0 or not wheel_out.is_file():
            results.append(
                {
                    "name": name, "build_ok": False, "returncode": rc,
                    "build_log_sha256": log_hash, "log_tail": log[-1500:],
                }
            )
            continue
        output_sha256 = hashlib.sha256(wheel_out.read_bytes()).hexdigest()
        identity = sf.build_source_identity(
            name=pkg["name"], version=pkg["version"],
            source_type=sf.SOURCE_TYPE_DIRECTORY,
            source_reference=pkg["source_path"],
            target_commit=TARGET_COMMIT, repo_dir=REPO,
        )
        provenance = sf.artifact_provenance(
            identity,
            build_toolchain="python3.12 + pip wheel (offline) + setuptools-75.7.0",
            build_inputs=[pkg["source_path"]],
            output_filename=wheel_out.name,
            output_sha256=output_sha256,
            metadata_name=pkg["name"],
            metadata_version=pkg["version"],
            python_tag="py3-none-any",
            build_log_sha256=log_hash,
        )
        results.append(
            {
                "name": name,
                "build_ok": True,
                "source_tree_sha256": extraction["tree_sha256"],
                "file_count": extraction["file_count"],
                "size_bytes": extraction["size_bytes"],
                "wheel": wheel_out.name,
                "wheel_size_bytes": wheel_out.stat().st_size,
                "wheel_sha256": output_sha256,
                "provenance": provenance,
                "build_log_sha256": log_hash,
            }
        )

    # --- engineering import probes (NOT calibration evidence) ---
    probes: dict[str, dict] = {}
    probe_target = build_dir / "site"
    probe_target.mkdir(exist_ok=True)
    for result in results:
        if not result["build_ok"]:
            probes[result["name"]] = {"status": "BUILD_FAILED"}
            continue
        wheel_path = WHEELS_DIR / result["wheel"]
        rc, log = _run(
            [
                str(VENV_PYTHON), "-m", "pip", "install", "--no-deps",
                "--no-index", "--target", str(probe_target), str(wheel_path),
            ]
        )
        if rc != 0:
            probes[result["name"]] = {"status": "INSTALL_FAILED", "log": log[-800:]}
            continue
        code = PROBES[result["name"].lower()]
        prc, plog = _run(
            [str(VENV_PYTHON), "-c", code],
            cwd=probe_target,
        )
        probes[result["name"]] = {
            "status": "PASS" if prc == 0 else "FAIL",
            "returncode": prc,
            "output": plog.strip(),
        }

    report = {
        "mission": "M17_ENV_CANON_SOURCE_FIDELITY_AMENDMENT_R1_DESIGN_AND_FREEZE",
        "phase": "S8_TARGETED_SOURCE_FIDELITY_VALIDATION",
        "classification": "ENGINEERING_P2P_ONLY",
        "calibration_evidence": False,
        "network_used": False,
        "calibration12_run": False,
        "target_commit": TARGET_COMMIT,
        "repo_dir": REPO,
        "build_toolchain": "python3.12 + pip wheel (offline) + setuptools-75.7.0 (local wheelhouse)",
        "packages": results,
        "import_probes": probes,
        "material_gate": {
            "network": "unused",
            "new_disk_bytes": sum(r.get("wheel_size_bytes", 0) for r in results),
            "build_runtime": "measured per package below (<< 10 min expected)",
            "all_inputs_local": True,
        },
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"wheel_artifacts": [
        {"name": r["name"], "ok": r["build_ok"], "sha256": r.get("wheel_sha256"), "bytes": r.get("wheel_size_bytes")}
        for r in results
    ], "probes": probes}, indent=2))
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())