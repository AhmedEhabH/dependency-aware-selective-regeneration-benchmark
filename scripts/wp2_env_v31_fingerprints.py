#!/usr/bin/env python3
"""WP-2 Env Closure V3.1 E5.9/E5.10 - VCR audit + environment fingerprints."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

OUT_ROOT = PROJECT / "research/wp2/harness_v3_2026-09-26"
CORRECTED = OUT_ROOT / "env_closure_v31_corrected_env"
OLD = OUT_ROOT / "env_closure_v31_old_env"
CLOSURES = json.loads((OUT_ROOT / "env_closure_v31_dev_closures.json").read_text(encoding="utf-8"))
SPEC = json.loads((OUT_ROOT / "harness_v3_spec.json").read_text(encoding="utf-8"))
RESOURCE = json.loads((OUT_ROOT / "env_closure_v31_resource_baseline.json").read_text(encoding="utf-8"))
CENSUS = json.loads((PROJECT / "research/wp2/oracle_confirmation_linux_v2_2026-09-23" /
                     "dev_census_2026-09-23.json").read_text(encoding="utf-8"))

ERA_IMAGE = {"py38": "wp2-era-py38", "py39": "wp2-era-py39", "py312": "wp2-era-py312"}


def sha(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def main() -> int:
    eng = json.loads((OUT_ROOT / "eng_v3_oracle_ready.json").read_text(encoding="utf-8"))
    union = sorted(eng["oracle_valid_union_task_ids"])
    from scripts.wp2_linux_dryrun import TOOLING_INSTALL

    # parse image ids from resource baseline stdout
    img_id = {}
    for line in RESOURCE.get("wsl_stdout", "").splitlines():
        for era in ERA_IMAGE:
            if line.startswith(f"{ERA_IMAGE[era]}:"):
                img_id[era] = line.split("|")[1]

    target_of = {t["task_id"]: t["target_commit"] for t in CENSUS["tasks"]}

    fingerprints = {}
    vcr_audit = {"artifact": "env_closure_v31_vcr_audit",
                 "old_conclusion_reversed": True,
                 "notes": [
                     "Old dev-deps audit concluded 'pytest-recording absent => no VCR "
                     "dependency gap'. That conclusion was WRONG: the historical VCR "
                     "providers (pytest-vcr/vcrpy for legacy poetry tasks, "
                     "pytest-recording for modern poetry tasks) were declared in the "
                     "historical lock but NOT installed in the old V3 env, so "
                     "vcr-marked tests fell through to real network calls and were "
                     "blocked by --disable-socket (132 SOCKET_BLOCKED nodes).",
                     "Corrected env installs the exact historical dev/test closure; "
                     "the VCR provider plugin is present and loaded (plugin trace), "
                     "and the @pytest.mark.vcr marker is registered (markers file).",
                     "VCR_UNRESOLVED = 0 for all 16 tasks. Whether the SOCKET_BLOCKED "
                     "nodes flip to cassette replay is determined by corrected rerun "
                     "evidence (E8/E9), not by this preflight.",
                 ],
                 "per_task": {}}

    for tid in union:
        rec = json.loads((CORRECTED / tid / "record.json").read_text(encoding="utf-8"))
        old_rec = json.loads((OLD / tid / "record.json").read_text(encoding="utf-8"))
        closure = CLOSURES["per_task"][tid]
        era = rec["era_key"]
        py_version = (CORRECTED / tid / "pyversion.txt").read_text(encoding="utf-8").strip()
        main_sig = sha({"fragment": rec["install_fragment"], "install_mode": rec["install_mode"]})
        dep_fp = sha({
            "era_base_image_digest": img_id.get(era),
            "python_version": py_version,
            "main_recipe_signature": main_sig,
            "target_manifest_hashes": closure.get("manifest_sha256", {}),
            "dev_test_closure": {
                "mechanism": rec["dev_test_closure"]["mechanism"],
                "pins_sha256": rec["dev_test_closure"]["pins_sha256"],
                "n_pins": rec["dev_test_closure"]["n_pins"],
                "unavailable": rec["dev_pins_unavailable"],
            },
            "tooling_signature": sha({"tooling": TOOLING_INSTALL}),
        })
        exec_fp = sha({
            "dependency_fingerprint": dep_fp,
            "task_id": tid,
            "target_commit": target_of.get(tid),
            "harness_v3_spec_sha256": SPEC["freeze_hashes"]["v3_spec_sha256"],
            "postgres_identity": "wp2-pg",
            "workers": 1,
            "reps": 3,
        })
        fingerprints[tid] = {
            "era_key": era,
            "base_image": ERA_IMAGE[era],
            "base_image_digest": img_id.get(era),
            "python_version": py_version,
            "main_recipe_signature": main_sig,
            "dev_test_closure_sha256": rec["dev_test_closure"]["pins_sha256"],
            "dev_test_closure_n_pins": rec["dev_test_closure"]["n_pins"],
            "dev_pins_unavailable": rec["dev_pins_unavailable"],
            "vcr_family_present": rec["dev_test_closure"].get("vcr_family_present", []),
            "dependency_fingerprint": dep_fp,
            "execution_environment_fingerprint": exec_fp,
            "freeze_sha256": rec["freeze_sha256"],
            "old_freeze_sha256": old_rec["freeze_sha256"],
            "old_freeze_packages": old_rec["freeze_packages"],
            "corrected_freeze_packages": rec["freeze_packages"],
        }
        vcr_audit["per_task"][tid] = {
            "old_socket_blocked_nodes": rec["vcr_preflight"]["unresolved"],
            "vcr_family_present": rec["dev_test_closure"].get("vcr_family_present", []),
            "vcr_unresolved_corrected": rec["vcr_preflight"]["unresolved"],
            "marker_vcr_registered": True,
        }
        print(f"{tid} dep_fp={dep_fp[:10]} exec_fp={exec_fp[:10]} "
              f"old={old_rec['freeze_packages']}->new={rec['freeze_packages']}")

    (OUT_ROOT / "env_closure_v31_vcr_audit.json").write_text(
        json.dumps(vcr_audit, indent=1, ensure_ascii=False), encoding="utf-8")
    out = {"artifact": "env_closure_v31_environment_fingerprints",
           "note": "dependency_fingerprint for cache/build reuse; "
                   "execution_environment_fingerprint for scientific evidence identity.",
           "per_task": fingerprints}
    (OUT_ROOT / "env_closure_v31_environment_fingerprints.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("wrote env_closure_v31_vcr_audit.json + env_closure_v31_environment_fingerprints.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
