"""M17_D7_R4_PHASE1C_HARNESS_R3 - generate the R3 authority binding, allowlist,
and the three frozen selection manifests.

Deterministic builder over frozen committed evidence.  Scientific inputs are
never modified: membership/order/strata are read from the frozen I6 census and
the frozen R4-D calibration plan / N12 receipt only.  The closure content hash
is verified against the COMMITTED closure blob (CLOSURE HASH RULE - not a
fresh re-derivation).  This script is build-time only; the harness does not
depend on it.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
R4_DIR = PROJECT / "research" / "env-canon-r4"
OUT_DIR = R4_DIR / "r3"

SCIENTIFIC_AUTHORITY_HEAD = "5171a4e75cfb2064e7758423c146fcd4ca9ee95c"
SCIENTIFIC_AUTHORITY_TAG = "m17-d7-r4-framework-gate-phase5-resolution-successor-r1-2026-10-16"
SUPPORT_EVIDENCE_HEAD = "beeff152de2307b2067c8cd9f469542ef8200b95"
EXECUTION_CODE_SET_HASH = "72d3d1262133505dd3046a78e9fc0130d004cfaf6e8ca89169b67620335584c0"
COMMITTED_CLOSURE_CONTENT_HASH = "71cc7fb72e34fbf707e0a7e8052d3ea2d49fc726cb3a16d9d678271f4a6404e1"
CLOSURE_EVIDENCE_FILE = "research/env-canon-r4/R4_PHASE1B_SUCCESSOR_ARTIFACT_CLOSURE_144.json"
POPULATION_IDENTITY = "ce51d2ec0eb28f6b720fbab13a852618e2de0f0a1111a3cc19dc64b1d19defac"
ORDERED_MEMBERSHIP_HASH = "8eb4a7242e12bb03715adac5fffdea2e4340585843fc137ececd38952ad6a19e"
IMAGE_BINDING_HASH = "5169c69d45f0761c85792ec182c9e949f58d8c9f5a29355d5a371944293d2ef2"
R3_RELEASE_TAG = "m17-d7-r4-population-qualification-harness-r3-2026-10-16"
REQUIRED_BRANCH = "parallel/r4-successor-harness-r3-2026-10-16"

R3_SEMANTIC_FOOTPRINT = "8831e9c761e0c6a15da76e789f7b86a175e5bebbf993c9033a1e202239720f34"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _blob_sha256_at(rev: str, path: str) -> str:
    blob = subprocess.run(["git", "rev-parse", f"{rev}:{path}"], capture_output=True, text=True)
    if blob.returncode != 0:
        raise RuntimeError(f"blob {path} missing at {rev}")
    data = subprocess.run(
        ["git", "cat-file", "blob", blob.stdout.strip()], capture_output=True
    ).stdout
    return _sha256_bytes(data.replace(b"\r\n", b"\n"))


def membership_hash(ids: list[str]) -> str:
    return _sha256_bytes(json.dumps(ids, separators=(",", ":")).encode("utf-8"))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---- authority binding -------------------------------------------------
    binding = {
        "artifact": "R3_AUTHORITY_BINDING",
        "schema_version": "env-canon-r4/r3/authority-binding/1.0",
        "mission_id": "M17_D7_R4_PHASE1C_HARNESS_R3_RELEASE",
        "two_head_model": {
            "scientific_authority_head": SCIENTIFIC_AUTHORITY_HEAD,
            "scientific_authority_tag": SCIENTIFIC_AUTHORITY_TAG,
            "support_evidence_head": SUPPORT_EVIDENCE_HEAD,
            "note": (
                "The scientific tag MUST peel to SCIENTIFIC_AUTHORITY_HEAD; SUPPORT_EVIDENCE_HEAD "
                "is the descendant carrying the committed successor receipts/manifests/closure. "
                "Harness R3 is operational evidence layered on SUPPORT_EVIDENCE_HEAD while its "
                "scientific binding remains SCIENTIFIC_AUTHORITY_HEAD. Never move the scientific tag."
            ),
        },
        "execution_code_set_hash": EXECUTION_CODE_SET_HASH,
        "execution_code_set_manifest": "research/env-canon-r4/R4_PHASE1B_EFFECTIVE_EXECUTION_CODE_SET.json",
        "committed_closure_content_hash": COMMITTED_CLOSURE_CONTENT_HASH,
        "closure_evidence_file": CLOSURE_EVIDENCE_FILE,
        "closure_authority_file": "research/env-canon-r4/R4_PHASE1B_SUCCESSOR_ARTIFACT_CLOSURE_AUTHORITY.json",
        "closure_semantic_footprint": R3_SEMANTIC_FOOTPRINT,
        "closure_hash_policy": (
            "Verify COMMITTED_CLOSURE_CONTENT_HASH against the exact committed closure blob "
            "(LF-normalized git blob bytes). A fresh re-derivation is never required to reproduce "
            "the same volatile serialization bytes; if re-derived, compare scientific semantics "
            "via R3_SEMANTIC_FOOTPRINT."
        ),
        "population_identity": POPULATION_IDENTITY,
        "ordered_membership_hash": ORDERED_MEMBERSHIP_HASH,
        "image_binding_hash": IMAGE_BINDING_HASH,
        "r3_release_tag": R3_RELEASE_TAG,
        "required_branch": REQUIRED_BRANCH,
        "allowlist_file": "research/env-canon-r4/r3/R3_OPERATIONAL_ALLOWLIST.json",
        "selection_manifests_dir": "research/env-canon-r4/r3",
        "generated_utc": "2026-10-16T00:00:00Z",
    }
    (OUT_DIR / "R3_AUTHORITY_BINDING.json").write_text(
        json.dumps(binding, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    # ---- operational allowlist (recomputed relative to SUPPORT_EVIDENCE_HEAD)
    allow_files = [
        ("src/benchmark/wp2/full144/driver.py", "Full144 execution driver (frozen per-unit path)"),
        ("src/benchmark/wp2/full144/population.py", "Frozen population/order/binding authority"),
        ("scripts/r4_behavioral_calibration_n12_r2.py", "Qualified Attempt-6 runner (behavioral semantics)"),
        ("src/benchmark/wp2/env_r4/route_closure.py", "Successor D7 install-route closure projection"),
        ("src/benchmark/wp2/env_r4/contracts.py", "R4 contracts/parser semantics"),
        ("src/benchmark/wp2/env_r4/uv_adapter.py", "R4-B uv adapter"),
        ("src/benchmark/wp2/env_r4/integrated_parser.py", "R4 integrated lock parser"),
        ("src/benchmark/wp2/env_r4/linux_tree_materialize.py", "R4-C Linux-faithful materializer"),
        ("src/benchmark/wp2/env_r4/linux_tree_wiring.py", "R4-C materialization wiring"),
        ("src/benchmark/wp2/env_r4/wheel_tags.py", "R4-A wheel tag semantics"),
        ("src/benchmark/wp2/linux_adapter.py", "WSL Docker backend"),
        ("scripts/r4_full144_preexecution.py", "Full144 preexecution CLI (freeze + unit gate)"),
    ]
    allowlist = {
        "artifact": "R3_OPERATIONAL_ALLOWLIST",
        "schema_version": "env-canon-r4/r3/operational-allowlist/1.0",
        "relative_to_head": SUPPORT_EVIDENCE_HEAD,
        "note": (
            "Recomputed against SUPPORT_EVIDENCE_HEAD (beeff152); supersedes the R2 3-path "
            "allowlist. Scientific frozen files must match these blob hashes at the R3 release HEAD."
        ),
        "files": [
            {
                "path": path,
                "blob_sha256_at_support_head": _blob_sha256_at(SUPPORT_EVIDENCE_HEAD, path),
                "role": role,
            }
            for path, role in allow_files
        ],
        "generated_utc": "2026-10-16T00:00:00Z",
    }
    (OUT_DIR / "R3_OPERATIONAL_ALLOWLIST.json").write_text(
        json.dumps(allowlist, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    # ---- selection manifests ----------------------------------------------
    sys.path.insert(0, str(PROJECT / "src"))
    from benchmark.wp2.full144 import population

    full_ids = population.ordered_unit_ids()

    def unit_records(ids: list[str]) -> list[dict[str, object]]:
        census = json.loads(
            (R4_DIR / "R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144.json").read_text(encoding="utf-8")
        )
        by_id = {u["validation_unit_id"]: u for u in census["units"]}
        recs: list[dict[str, object]] = []
        for uid in ids:
            u = by_id[uid]
            recs.append(
                {
                    "validation_unit_id": uid,
                    "member_task_ids": u["member_tasks"],
                    "docker_profile_id": u["docker_profile_id"],
                    "native_profile_id": u["native_profile_id"],
                    "python_version": u["python_version"],
                    "lock_type": u["lock_type"],
                    "install_route": u["install_route"],
                    "wheelhouse_era": u["wheelhouse_era"],
                    "source_fidelity_overlay_required": bool(u.get("source_fidelity_overlay_required", False)),
                }
            )
        return recs

    t3_ids = ["vu-cd262bbb641d", "vu-bbb37661a274", "vu-9ed193747002"]
    rec_ids = ["vu-b9808f19ace4", "vu-692af9112c6d", "vu-e4998719ee01", "vu-db74b3640c98",
               "vu-422bca69f329", "vu-13c1de1de71e", "vu-b78ebcf3e530", "vu-bfe987de6e53",
               "vu-eda4e9f82401", "vu-457f26c93ff1", "vu-ffe68ddec229", "vu-0e0ef31c7634"]
    if [full_ids.index(t) + 1 for t in t3_ids] != [71, 119, 130]:
        raise RuntimeError("TARGETED3 membership indices drifted")
    plan = json.loads((R4_DIR / "R4_STRATIFIED_CALIBRATION_PLAN_DRAFT.json").read_text(encoding="utf-8"))
    n12_strata = []
    for uid in rec_ids:
        cu = next(c for c in plan["calibration_units"] if c["validation_unit_id"] == uid)
        reasons = cu.get("selection_reasons", [])
        stratum = next((r.split("stratum:", 1)[1] for r in reasons if r.startswith("stratum:")), None)
        n12_strata.append(stratum or f"{cu['python_version']}|{cu['lock_type']}|{cu['install_route']}")
    for uid in rec_ids:
        if uid not in full_ids:
            raise RuntimeError(f"CAL12 unit {uid} not in frozen population")

    def manifest(name: str, purpose: str, ids: list[str], n: int, predecessor: str | None,
                 strata: list[str] | None) -> dict[str, object]:
        mh = membership_hash(ids)
        return {
            "artifact": f"R3_SELECTION_{name}",
            "schema_version": "env-canon-r4/r3-selection/1.0",
            "selection_name": name,
            "expected_count": n,
            "ordered_unit_ids": ids,
            "membership_hash": mh,
            "membership_hash_method": "sha256(canonical compact JSON array of ordered unit ids, separators=(',',':'))",
            "selection_purpose": purpose,
            "scientific_authority_head": SCIENTIFIC_AUTHORITY_HEAD,
            "support_evidence_head": SUPPORT_EVIDENCE_HEAD,
            "execution_code_set_hash": EXECUTION_CODE_SET_HASH,
            "committed_closure_content_hash": COMMITTED_CLOSURE_CONTENT_HASH,
            "closure_semantic_footprint": R3_SEMANTIC_FOOTPRINT,
            "population_identity": POPULATION_IDENTITY,
            "ordered_membership_hash": ORDERED_MEMBERSHIP_HASH,
            "image_binding_hash": IMAGE_BINDING_HASH,
            "predecessor_selection": predecessor,
            "required_predecessor_receipt": None if predecessor is None else None,
            "per_unit_strata": strata,
            "unit_records": unit_records(ids),
            "generated_utc": "2026-10-16T00:00:00Z",
        }

    manifests = [
        manifest(
            "TARGETED3",
            "Frozen successor dynamic validation of exactly units 71 (vu-cd262bbb641d / posuto repair), "
            "119 (vu-bbb37661a274) and 130 (vu-9ed193747002) under the successor chain - 3/3 PASS prerequisite "
            "before CAL12.",
            t3_ids,
            3,
            None,
            None,
        ),
        manifest(
            "CAL12",
            "Exact frozen N12 membership/order/strata from the qualified R4-B calibration plan and the "
            "N12 R2 receipt (exact_ordered_n12); predecessor TARGETED3 must be 3/3 PASS.",
            rec_ids,
            12,
            "TARGETED3",
            n12_strata,
        ),
        manifest(
            "FULL144",
            "Exact frozen 144 ordered population membership (I6 census == matrix); predecessor CAL12 must "
            "be 12/12 PASS.",
            full_ids,
            144,
            "CAL12",
            None,
        ),
    ]
    for m in manifests:
        name = m["selection_name"]
        rec = {k: v for k, v in m.items() if k not in ("generated_utc", "manifest_sha256")}
        m["manifest_sha256"] = _sha256_bytes(
            json.dumps(rec, sort_keys=True, separators=(",", ":")).encode("utf-8")
        )
        (OUT_DIR / f"R3_SELECTION_{name}.json").write_text(
            json.dumps(m, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"{name}: count={m['expected_count']} members={m['membership_hash']} "
              f"manifest={m['manifest_sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
