#!/usr/bin/env python3
"""M17_D7 R4-E1 pylint bounded recovery plan generator (planning ONLY — ZERO network).

Mission: M17_D7_R4_E1_PYLINT_RECOVERY_PLAN (T2, bounded external-artifact
acquisition planning and owner-gate preparation).

This driver FREEZES the exact recovery plan that the owner will review before
authorizing any external acquisition.  It performs NO network request, NO
download, NO build, NO install, NO Docker execution, and NO mutation of frozen
I6 evidence.  The authoritative input is the frozen I6 receipt
``research/env-canon-r4/R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144.json``; the
generator proves, from that receipt and nothing else:

  * TRUE_MISSING occurrence count == 89;
  * unique TRUE_MISSING identity count == 28;
  * every unique package name canonicalizes exactly to ``pylint``;
  * the exact 28-version set matches the frozen census (and the mission list);
  * affected validation-unit count == 65;
  * no non-pylint TRUE_MISSING identity exists.

The generated ``R4_E1_PYLINT_RECOVERY_PLAN.json`` records the exact-version-only
acquisition policy, the allowed metadata/artifact origins, the R4-A wheel
compatibility authority, the integrity/structural validation policy, the
yanked-release and sdist-fallback policies, and the additive recovery overlay
store design — all WITHOUT any executable network path.  A deterministic
``plan_sha256`` is computed over the canonical semantic plan.

Status: PLANNED_AWAITING_OWNER_NETWORK_APPROVAL.  The next phase (E2) may only
start after the owner explicitly authorizes network acquisition.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from packaging.version import Version

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import benchmark  # noqa: E402
from benchmark.wp2.env_r4.contracts import RuntimeTarget, normalize_name  # noqa: E402

R4_DIR = PROJECT / "research" / "env-canon-r4"
CENSUS_JSON = R4_DIR / "R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144.json"
PLAN_JSON = R4_DIR / "R4_E1_PYLINT_RECOVERY_PLAN.json"
PLAN_MD = R4_DIR / "R4_E1_PYLINT_RECOVERY_PLAN.md"

SCHEMA_VERSION = "env-canon-r4-e1/1.0"
MISSION_ID = "M17_D7_R4_E1_PYLINT_RECOVERY_PLAN"
MISSION_CLASS = "T2_bounded_external_artifact_acquisition_planning"
STARTING_HEAD = "b4667fd56738b4d7d069ba88c73a290c201d1628"
BRANCH = "parallel/d7-r4-e-bounded-artifact-recovery-2026-10-13"
UPSTREAM_I6_HEAD = STARTING_HEAD

PACKAGE_NAME = "pylint"
TARGET = RuntimeTarget("3.9", "cpython", "linux", "x86_64")
INSTALL_ROUTE = "REQ_MAIN_PLUS_LOCK_DEV"
ALLOWED_METADATA_ORIGIN = "https://pypi.org/"
ALLOWED_ARTIFACT_ORIGIN = "https://files.pythonhosted.org/"
METADATA_ENDPOINT_TEMPLATE = "https://pypi.org/pypi/pylint/<EXACT_VERSION>/json"
WHEEL_COMPATIBILITY_AUTHORITY = "R4-A"

FROZEN_WHEELHOUSE = Path(r"D:\wp2_env_store\wheelhouse\py39")
FROZEN_MANIFEST = Path(r"D:\wp2_env_store\manifests\WHEELHOUSE_HASHES_py39.json")
RECOVERY_ROOT = Path(r"D:\wp2_env_store\recovery\r4e_pylint_py39")
RECOVERY_STAGING = RECOVERY_ROOT / "staging"
RECOVERY_WHEELS = RECOVERY_ROOT / "wheels"
RECOVERY_MANIFESTS = RECOVERY_ROOT / "manifests"

# Mission-provided authoritative 28-version recovery set.  The frozen I6 census
# is the primary authority: if the census unique-version set differs from this
# list, the generator FAILS CLOSED (STOP_OWNER_REVIEW), never trusting the list.
EXPECTED_VERSIONS: tuple[str, ...] = (
    "2.7.2", "2.7.4", "2.8.1", "2.8.2", "2.9.5", "2.9.6", "2.10.2",
    "2.11.1", "2.12.2", "2.13.4", "2.13.5", "2.13.8", "2.13.9", "2.14.3",
    "2.14.5", "2.15.2", "2.15.3", "2.15.4", "2.15.5", "2.15.8", "2.15.10",
    "2.16.1", "2.17.1", "2.17.2", "2.17.3", "2.17.4", "2.17.5", "2.17.7",
)

EXPECTED_OCCURRENCES = 89
EXPECTED_UNIQUE_IDENTITIES = 28
EXPECTED_AFFECTED_UNITS = 65

ACQUISITION_STATUS = "PLANNED_AWAITING_OWNER_NETWORK_APPROVAL"


class PlanFailClosedError(Exception):
    """Raised when any E1 fail-closed gate fails (drives nonzero exit)."""


def _canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_import_provenance() -> dict[str, object]:
    """Prove ``benchmark`` resolves under the workspace ``src`` (not Anaconda)."""
    resolved = Path(benchmark.__file__).resolve()
    src_resolved = SRC.resolve()
    if not resolved.is_relative_to(src_resolved):
        raise PlanFailClosedError(
            f"import provenance wrong: benchmark = {resolved}, expected under {src_resolved}"
        )
    return {
        "benchmark_module": str(resolved),
        "expected_src": str(src_resolved),
        "resolves_to_expected_src": True,
    }


def load_census(path: Path = CENSUS_JSON) -> dict[str, Any]:
    """Load the frozen I6 receipt without mutation."""
    if not path.is_file():
        raise PlanFailClosedError(f"missing frozen I6 census: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise PlanFailClosedError(f"frozen census {path} is not a JSON object")
    return data


def prove_census(census: dict[str, Any]) -> dict[str, Any]:
    """Prove every E1 census gate; FAILS CLOSED on any mismatch.

    Returns deterministic derived facts used by the plan builder.
    """
    occ = census.get("true_missing_artifact_occurrences")
    uniq = census.get("true_missing_artifact_unique_identities")
    units = census.get("true_missing_affected_units")
    dep_totals = census.get("dependency_terminal_classifications", {})
    terminal = census.get("terminal_classifications", {})

    if not isinstance(occ, list) or not isinstance(uniq, list) or not isinstance(units, list):
        raise PlanFailClosedError("frozen census missing TRUE_MISSING occurrence/identity/unit lists")
    if dep_totals.get("TRUE_MISSING_ARTIFACT") != EXPECTED_OCCURRENCES:
        raise PlanFailClosedError(
            f"census TRUE_MISSING_ARTIFACT total {dep_totals.get('TRUE_MISSING_ARTIFACT')} != 89"
        )
    if terminal.get("BLOCKED_TRUE_MISSING_ARTIFACT") != EXPECTED_AFFECTED_UNITS:
        raise PlanFailClosedError(
            f"census BLOCKED_TRUE_MISSING_ARTIFACT "
            f"{terminal.get('BLOCKED_TRUE_MISSING_ARTIFACT')} != 65"
        )

    unique_set = {(str(n), str(v)) for n, v in uniq}
    if len(unique_set) != len(uniq):
        raise PlanFailClosedError("census unique identity list contains duplicates")
    if len(unique_set) != EXPECTED_UNIQUE_IDENTITIES:
        raise PlanFailClosedError(
            f"census unique TRUE_MISSING identity count {len(unique_set)} != 28"
        )
    names = {normalize_name(n) for n, _v in unique_set}
    if names != {PACKAGE_NAME}:
        raise PlanFailClosedError(f"census unique package names {names} != {{pylint}}")
    census_versions = {v for _n, v in unique_set}
    if census_versions != set(EXPECTED_VERSIONS):
        missing = sorted(census_versions - set(EXPECTED_VERSIONS))
        extra = sorted(set(EXPECTED_VERSIONS) - census_versions)
        raise PlanFailClosedError(
            f"census version set != authoritative 28-version set "
            f"(extra={extra}, missing={missing})"
        )

    occ_set = {(str(o["normalized_name"]), str(o["version"])) for o in occ}
    if len(occ) != EXPECTED_OCCURRENCES:
        raise PlanFailClosedError(f"census occurrence count {len(occ)} != 89")
    if occ_set != unique_set:
        raise PlanFailClosedError("census occurrence identities != unique identity set")
    occ_sources = {str(o.get("source_type")) for o in occ}
    if occ_sources != {"REGISTRY"}:
        raise PlanFailClosedError(f"census occurrence source types {occ_sources} != {{REGISTRY}}")
    if len(units) != EXPECTED_AFFECTED_UNITS:
        raise PlanFailClosedError(f"census affected-unit count {len(units)} != 65")

    ordered = sorted(
        unique_set, key=lambda iv: (Version(iv[1]), iv[0])
    )
    ordered_identities = [[name, version] for name, version in ordered]
    if ordered_identities != [[PACKAGE_NAME, v] for v in EXPECTED_VERSIONS]:
        raise PlanFailClosedError("ordered recovery identities != authoritative version order")

    return {
        "unique_identity_set": unique_set,
        "ordered_identities": ordered_identities,
        "occurrence_identities": occ_set,
        "affected_unit_ids": sorted(units),
        "census_versions": census_versions,
    }


def _store_design() -> dict[str, Any]:
    return {
        "recovery_root": str(RECOVERY_ROOT),
        "staging_path": str(RECOVERY_STAGING),
        "wheels_path": str(RECOVERY_WHEELS),
        "manifests_path": str(RECOVERY_MANIFESTS),
        "frozen_wheelhouse_path": str(FROZEN_WHEELHOUSE),
        "frozen_manifest_path": str(FROZEN_MANIFEST),
        "network_downloads_go_to": str(RECOVERY_STAGING),
        "promotion_rule": "promote staging -> wheels ONLY after complete verification",
        "no_overwrite_rule": (
            "no overwrite of an existing artifact unless byte-identical and "
            "already recorded by the same recovery manifest"
        ),
        "frozen_wheelhouse_mutation_prohibited": True,
        "additive_overlay_only": True,
    }


def _artifact_selection_policy() -> dict[str, Any]:
    return {
        "source_of_truth": "official PyPI release metadata per exact version",
        "steps": [
            "1. read official PyPI release metadata",
            "2. reject release if the exact version is absent",
            "3. reject release if only unapproved/ambiguous artifacts exist",
            "4. reject a yanked release unless frozen scientific authority requires "
            "that exact yanked version AND the owner explicitly approves the yanked "
            "artifact after evidence review",
            "5. prefer an officially published wheel over an sdist",
            "6. require exact wheel Name == pylint",
            "7. require exact wheel Version == expected version",
            "8. require R4-A compatibility with the frozen RuntimeTarget "
            "(CPython 3.9 / linux / x86_64)",
            "9. pure-Python wheels (e.g. py3-none-any) acceptable only if R4-A "
            "accepts them for this target",
            "10. no host-Python tag inference",
            "11. no arbitrary filename-prefix matching",
        ],
        "multiple_compatible_wheels": {
            "prefer": "a pure-Python wheel compatible with the target",
            "otherwise": "deterministic R4-A-compatible choice",
            "record": "selection rationale and all candidates considered",
        },
        "no_compatible_wheel": (
            "STOP_OWNER_REVIEW with exact evidence; do NOT automatically build from sdist"
        ),
    }


def _exact_version_only_policy() -> dict[str, Any]:
    return {
        "package_name_must_equal": PACKAGE_NAME,
        "version_must_be_exact": True,
        "no_version_upgrades": True,
        "no_version_downgrades": True,
        "no_latest": True,
        "no_semver_compatible_substitution": True,
        "no_alternative_package": True,
        "no_locally_rebuilt_substitute": True,
        "no_dependency_downloads_in_acquisition": True,
        "no_mutation_of_frozen_i6_evidence": True,
    }


def _no_dependency_download_policy() -> dict[str, Any]:
    return {
        "acquisition_downloads_contain_dependencies": False,
        "only_exact_pylint_versions_downloaded": True,
        "dependency_resolution": "outside E1 scope; requires a later owner-approved phase",
    }


def _integrity_validation_policy() -> dict[str, Any]:
    return {
        "https_tls_verification_enabled": True,
        "final_artifact_host": "files.pythonhosted.org",
        "official_sha256_captured_before_acceptance": True,
        "downloaded_file_sha256_must_equal_official": True,
        "evidence_claims_limited_to": [
            "official origin",
            "hash integrity",
            "archive structural safety",
            "exact package identity",
        ],
        "no_malware_free_claim": True,
    }


def _structural_wheel_validation_policy() -> dict[str, Any]:
    return {
        "wheel_filename_parsed_structurally": True,
        "canonical_name_equals_pylint": True,
        "exact_version_equals_required": True,
        "r4a_target_compatibility_pass": True,
        "zip_integrity_pass": True,
        "no_absolute_archive_paths": True,
        "no_dotdot_path_traversal": True,
        "wheel_metadata_name_equals_pylint": True,
        "wheel_metadata_version_equals_exact": True,
        "artifact_never_imported_or_executed_during_recovery_validation": True,
        "contents_not_trusted_merely_because_download_succeeded": True,
    }


def _yanked_release_policy() -> dict[str, Any]:
    return {
        "default": "reject yanked release",
        "exception": (
            "frozen scientific authority requires that exact yanked version AND "
            "the owner explicitly approves the yanked artifact after evidence review"
        ),
    }


def build_plan(census: dict[str, Any]) -> dict[str, Any]:
    """Build the full E1 recovery plan payload (deterministic, no network)."""
    facts = prove_census(census)
    provenance = verify_import_provenance()

    occ_counts: dict[str, int] = {}
    for o in census["true_missing_artifact_occurrences"]:
        v = str(o["version"])
        occ_counts[v] = occ_counts.get(v, 0) + 1

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "mission_id": MISSION_ID,
        "mission_class": MISSION_CLASS,
        "starting_head": STARTING_HEAD,
        "branch": BRANCH,
        "upstream_i6_head": UPSTREAM_I6_HEAD,
        "upstream_i6_census_sha256": _sha256_file(CENSUS_JSON),
        "upstream_i6_census_canonical_sha256": census.get("canonical_sha256"),
        "population_identity_sha256": census.get("population_identity_sha256"),
        "population_identity": {
            "n_validation_units": census.get("processed_units"),
            "n_mapped_tasks": census.get("processed_mapped_tasks"),
            "strata": census.get("strata_counts"),
        },
        "true_missing_occurrences": EXPECTED_OCCURRENCES,
        "true_missing_unique_identities": EXPECTED_UNIQUE_IDENTITIES,
        "affected_units": EXPECTED_AFFECTED_UNITS,
        "affected_unit_ids": facts["affected_unit_ids"],
        "exact_ordered_recovery_identities": facts["ordered_identities"],
        "occurrence_counts_by_version": dict(sorted(occ_counts.items())),
        "target": {
            "python_version": TARGET.python_version,
            "implementation": TARGET.implementation,
            "platform": TARGET.platform,
            "architecture": TARGET.architecture,
        },
        "install_route": INSTALL_ROUTE,
        "allowed_metadata_origin": ALLOWED_METADATA_ORIGIN,
        "allowed_artifact_origin": ALLOWED_ARTIFACT_ORIGIN,
        "metadata_endpoint_template": METADATA_ENDPOINT_TEMPLATE,
        "metadata_endpoints_queried_in_e1": False,
        "wheel_compatibility_authority": WHEEL_COMPATIBILITY_AUTHORITY,
        "artifact_selection_policy": _artifact_selection_policy(),
        "exact_version_only_policy": _exact_version_only_policy(),
        "no_dependency_download_policy": _no_dependency_download_policy(),
        "integrity_validation_policy": _integrity_validation_policy(),
        "structural_wheel_validation_policy": _structural_wheel_validation_policy(),
        "yanked_release_policy": _yanked_release_policy(),
        "sdist_fallback_policy": "OWNER_REVIEW_REQUIRED",
        "store_design": _store_design(),
        "staging_path": str(RECOVERY_STAGING),
        "wheels_path": str(RECOVERY_WHEELS),
        "manifests_path": str(RECOVERY_MANIFESTS),
        "frozen_wheelhouse_mutation_prohibited": True,
        "network_used": False,
        "artifacts_downloaded": 0,
        "Docker_used": False,
        "Full_D7_executed": False,
        "behavioral_calibration_executed": False,
        "owner_network_approval": False,
        "acquisition_status": ACQUISITION_STATUS,
        "import_provenance": provenance,
    }
    violations = validate_plan(payload, census)
    if violations:
        raise PlanFailClosedError("; ".join(violations))
    payload["plan_sha256"] = _sha256_bytes(
        _canonical({k: v for k, v in payload.items() if k != "plan_sha256"})
    )
    return payload


def validate_plan(plan: dict[str, Any], census: dict[str, Any] | None = None) -> list[str]:
    """Fail-closed validation of an E1 plan payload (self + cross vs census)."""
    errors: list[str] = []
    if census is None:
        census = load_census()
    facts = prove_census(census)

    plan_identities = [tuple(x) for x in plan.get("exact_ordered_recovery_identities", [])]
    plan_set = set(plan_identities)
    if len(plan_identities) != EXPECTED_UNIQUE_IDENTITIES:
        errors.append("exact recovery identity count != 28")
    if len(plan_set) != len(plan_identities):
        errors.append("duplicate recovery identity present")
    if plan_set != facts["unique_identity_set"]:
        errors.append("recovery identity set differs from authoritative census set")
    for name, _v in plan_identities:
        if normalize_name(str(name)) != PACKAGE_NAME:
            errors.append(f"non-pylint identity {name}")

    if plan.get("true_missing_occurrences") != EXPECTED_OCCURRENCES:
        errors.append("true_missing_occurrences != 89")
    if plan.get("true_missing_unique_identities") != EXPECTED_UNIQUE_IDENTITIES:
        errors.append("true_missing_unique_identities != 28")
    if plan.get("affected_units") != EXPECTED_AFFECTED_UNITS:
        errors.append("affected_units != 65")

    t = plan.get("target", {})
    if not (
        t.get("python_version") == "3.9"
        and t.get("implementation") == "cpython"
        and t.get("platform") == "linux"
        and t.get("architecture") == "x86_64"
    ):
        errors.append("target != CPython 3.9 linux x86_64")
    if plan.get("install_route") != INSTALL_ROUTE:
        errors.append("install route != REQ_MAIN_PLUS_LOCK_DEV")

    ev = plan.get("exact_version_only_policy", {})
    for key in (
        "no_version_upgrades",
        "no_version_downgrades",
        "no_latest",
        "no_semver_compatible_substitution",
        "no_alternative_package",
        "no_locally_rebuilt_substitute",
        "no_dependency_downloads_in_acquisition",
    ):
        if ev.get(key) is not True:
            errors.append(f"exact-version-only policy {key} not enforced")
    nd = plan.get("no_dependency_download_policy", {})
    if nd.get("acquisition_downloads_contain_dependencies") is not False:
        errors.append("dependency downloads allowed in acquisition")

    sd = plan.get("store_design", {})
    recovery_dests = [
        Path(str(plan.get("staging_path", ""))),
        Path(str(plan.get("wheels_path", ""))),
        Path(str(plan.get("manifests_path", ""))),
        Path(str(sd.get("staging_path", ""))),
        Path(str(sd.get("wheels_path", ""))),
        Path(str(sd.get("manifests_path", ""))),
    ]
    frozen_dir = FROZEN_WHEELHOUSE.resolve()
    frozen_manifest = FROZEN_MANIFEST.resolve()
    for d in recovery_dests:
        if d.resolve() in (frozen_dir, frozen_manifest) or frozen_dir in d.resolve().parents:
            errors.append(f"recovery destination {d} points into frozen wheelhouse")
    if plan.get("frozen_wheelhouse_mutation_prohibited") is not True:
        errors.append("frozen wheelhouse mutation not prohibited")

    if plan.get("allowed_metadata_origin") != ALLOWED_METADATA_ORIGIN:
        errors.append("metadata origin != https://pypi.org/")
    if plan.get("allowed_artifact_origin") != ALLOWED_ARTIFACT_ORIGIN:
        errors.append("artifact origin != https://files.pythonhosted.org/")
    if plan.get("metadata_endpoint_template") != METADATA_ENDPOINT_TEMPLATE:
        errors.append("metadata endpoint template mutated")
    if plan.get("wheel_compatibility_authority") != WHEEL_COMPATIBILITY_AUTHORITY:
        errors.append("wheel compatibility authority != R4-A")
    if plan.get("sdist_fallback_policy") != "OWNER_REVIEW_REQUIRED":
        errors.append("sdist fallback policy != OWNER_REVIEW_REQUIRED")

    if plan.get("network_used") is not False:
        errors.append("network_used != false")
    if plan.get("artifacts_downloaded") != 0:
        errors.append("artifacts_downloaded != 0")
    if plan.get("Docker_used") is not False:
        errors.append("Docker_used != false")
    if plan.get("Full_D7_executed") is not False:
        errors.append("Full_D7_executed != false")
    if plan.get("behavioral_calibration_executed") is not False:
        errors.append("behavioral_calibration_executed != false")
    if plan.get("owner_network_approval") is not False:
        errors.append("owner_network_approval != false")
    if plan.get("acquisition_status") != ACQUISITION_STATUS:
        errors.append("acquisition_status != PLANNED_AWAITING_OWNER_NETWORK_APPROVAL")

    if plan.get("plan_sha256"):
        recomputed = _sha256_bytes(
            _canonical({k: v for k, v in plan.items() if k != "plan_sha256"})
        )
        if plan.get("plan_sha256") != recomputed:
            errors.append("plan_sha256 not self-consistent")
    return errors


def render_plan_md(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# R4-E1 Pylint Recovery Plan — Owner Review Summary")
    lines.append("")
    lines.append(f"- Mission: `{payload['mission_id']}`")
    lines.append(f"- Branch: `{payload['branch']}`")
    lines.append(f"- Starting HEAD: `{payload['starting_head']}`")
    lines.append(f"- Upstream I6 census SHA-256: `{payload['upstream_i6_census_sha256']}`")
    lines.append(f"- Population identity SHA-256: `{payload['population_identity_sha256']}`")
    lines.append("")
    lines.append("## Recovery scope (exact, frozen)")
    lines.append("")
    lines.append("- **Exactly 28 versions** of exactly **one package** (`pylint`), no substitution.")
    lines.append("- Exactly one target era: **CPython 3.9 / Linux / x86_64**.")
    lines.append("- Install route: `REQ_MAIN_PLUS_LOCK_DEV`.")
    lines.append(f"- TRUE_MISSING occurrences: **{payload['true_missing_occurrences']}**")
    lines.append(f"- Unique identities: **{payload['true_missing_unique_identities']}**")
    lines.append(f"- Affected units: **{payload['affected_units']}**")
    lines.append("")
    lines.append("### Exact ordered recovery identities")
    lines.append("")
    for name, version in payload["exact_ordered_recovery_identities"]:
        lines.append(f"- `{name}=={version}`")
    lines.append("")
    lines.append("## External authority (future acquisition ONLY)")
    lines.append("")
    lines.append(f"- Metadata origin: `{payload['allowed_metadata_origin']}`")
    lines.append(f"- Artifact origin: `{payload['allowed_artifact_origin']}`")
    lines.append(f"- Metadata endpoint template: `{payload['metadata_endpoint_template']}`")
    lines.append(f"- Wheel compatibility authority: `{payload['wheel_compatibility_authority']}`")
    lines.append("- No dependency downloads. No version substitution. No \"latest\".")
    lines.append("- No sdist auto-build: sdist fallback is `OWNER_REVIEW_REQUIRED`.")
    lines.append("")
    lines.append("## Store design (additive overlay only)")
    lines.append("")
    sd = payload["store_design"]
    lines.append(f"- Recovery root: `{sd['recovery_root']}`")
    lines.append(f"- Staging (network downloads land here): `{sd['staging_path']}`")
    lines.append(f"- Final overlay (wheels after full verification): `{sd['wheels_path']}`")
    lines.append(f"- Recovery manifest path: `{sd['manifests_path']}`")
    lines.append(f"- Frozen wheelhouse: `{sd['frozen_wheelhouse_path']}`")
    lines.append(f"- Frozen manifest: `{sd['frozen_manifest_path']}`")
    lines.append("- Frozen wheelhouse/manifest are read-only and NEVER a recovery destination.")
    lines.append("- No overwrite of an existing artifact unless byte-identical and recorded "
                 "by the same recovery manifest.")
    lines.append("")
    lines.append("## E1 status (this planning phase)")
    lines.append("")
    lines.append("- `network_used`: false — **no network performed in E1**.")
    lines.append("- `artifacts_downloaded`: 0.")
    lines.append("- `Docker_used`: false; `Full_D7_executed`: false; "
                 "`behavioral_calibration_executed`: false.")
    lines.append("- Frozen I6 evidence and frozen store are unmutated.")
    lines.append(f"- Acquisition status: **`{payload['acquisition_status']}`**")
    lines.append("")
    lines.append("## Next action")
    lines.append("")
    lines.append("Requires **explicit owner authorization** before any external "
                 "acquisition (E2) may start.")
    lines.append("")
    lines.append(f"Plan SHA-256: `{payload['plan_sha256']}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="R4-E1 pylint recovery plan generator (offline)")
    ap.add_argument("--write", action="store_true", help="write plan JSON + summary MD")
    ap.add_argument("--plan-out", default=None, help="plan JSON output path")
    ap.add_argument("--md-out", default=None, help="summary MD output path")
    args = ap.parse_args()
    try:
        census = load_census()
        payload = build_plan(census)
        if args.write:
            plan_out = Path(args.plan_out) if args.plan_out else PLAN_JSON
            md_out = Path(args.md_out) if args.md_out else PLAN_MD
            plan_out.parent.mkdir(parents=True, exist_ok=True)
            plan_out.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            md_out.parent.mkdir(parents=True, exist_ok=True)
            md_out.write_text(render_plan_md(payload), encoding="utf-8")
        print(f"PLAN_SHA256={payload['plan_sha256']}")
        print(f"OCCURRENCES={payload['true_missing_occurrences']}")
        print(f"UNIQUE_IDENTITIES={payload['true_missing_unique_identities']}")
        print(f"AFFECTED_UNITS={payload['affected_units']}")
        print(f"ACQUISITION_STATUS={payload['acquisition_status']}")
        print("NETWORK_USED=false")
    except PlanFailClosedError as exc:
        print(f"PLAN_FAIL_CLOSED {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"PLAN_INSTRUMENTATION_ERROR {exc!r}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
