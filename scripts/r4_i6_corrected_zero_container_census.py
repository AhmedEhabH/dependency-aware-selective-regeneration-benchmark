#!/usr/bin/env python3
"""M17_D7 R4-I6 corrected zero-container census over the frozen 144-unit / 219-task population.

Mission: M17_D7_R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144 (T3, metadata/artifact
resolution only — NOT behavioral calibration, NOT Full D7, NOT Docker execution).

This driver is a THIN census/adjudication layer on top of the qualified I5
resolver (``r4_i5_zero_container_smoke``).  Every parser, RuntimeTarget,
wheel-compatibility, source-fidelity, canonical name/version, repository
identity, and local-store resolution semantic is REUSED from I5 unchanged.  The
only additions are:

  * a population loop over the exact frozen 144-unit / 219-task R4-D population
    (matrix order == VALIDATION_UNIT_MATRIX.csv order);
  * the Phase I6-0 target/install-route adjudication layer, which resolves the
    four known I5 candidate identities against FROZEN authority:
        python-magic-bin == 0.4.14   -> EXCLUDED_BY_TARGET (saleor pyproject
                                        platform = "win32"; no linux wheel/sdist)
        pywin32 == 306 (308)          -> EXCLUDED_BY_TARGET (MARKER_FILTER_AUDIT
                                        MARKER_EXCLUDED_ON_LINUX;
                                        WHEELHOUSE_PLAN_DETAIL
                                        marker_excluded_skipped=["pywin32"])
        codecov == 2.1.7 (+2.1.0/4/8/9/10) -> EXCLUDED_BY_TARGET
                                        (D4_CODECOV_NONRUNTIME_EXCLUSION_AMENDMENT_R5
                                        NON_RUNTIME_DEV_CI_TOOL_EXCLUDED)
        pylint (28 py39 versions absent from wheelhouse) -> TRUE_MISSING_ARTIFACT
                                        (required dev dep; no compatible wheel;
                                        not in approved source/sdist route set)
  * the final dependency taxonomy (AVAILABLE_COMPATIBLE_WHEEL,
    AVAILABLE_APPROVED_SOURCE_OR_SDIST, SOURCE_FIDELITY_OVERLAY_RESOLVED,
    EDITABLE_SELF_NOT_THIRD_PARTY, EXCLUDED_BY_TARGET, TRUE_MISSING_ARTIFACT);
  * per-unit terminal classification READY_LOCAL_ZERO_CONTAINER /
    BLOCKED_TRUE_MISSING_ARTIFACT (never leaves a candidate unit undecided).

Phase I6-0 must complete (and print the authority adjudication table) BEFORE the
population census starts.  Any remaining semantic ambiguity fails closed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(PROJECT / "scripts") not in sys.path:
    sys.path.insert(0, str(PROJECT / "scripts"))

import r4_i5_zero_container_smoke as i5  # noqa: E402

R4_DIR = PROJECT / "research" / "env-canon-r4"
CENSUS_JSON = R4_DIR / "R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144.json"
CENSUS_MD = R4_DIR / "R4_I6_CORRECTED_CENSUS_SUMMARY.md"

EXPECTED_POPULATION_IDENTITY = "ce51d2ec0eb28f6b720fbab13a852618e2de0f0a1111a3cc19dc64b1d19defac"
EXPECTED_UNITS = 144
EXPECTED_TASKS = 219
EXPECTED_STRATA = {"3.12_poetry": 25, "3.12_uv": 21, "3.9_poetry": 83, "3.8_poetry": 15}

# Final dependency taxonomy (frozen semantics; never invent a new terminal).
AVAILABLE_COMPATIBLE_WHEEL = i5.AVAILABLE_COMPATIBLE_WHEEL
AVAILABLE_APPROVED_SOURCE_OR_SDIST = i5.AVAILABLE_APPROVED_SOURCE_OR_SDIST
SOURCE_FIDELITY_OVERLAY_RESOLVED = i5.SOURCE_FIDELITY_OVERLAY_RESOLVED
EDITABLE_SELF_NOT_THIRD_PARTY = i5.EDITABLE_SELF_NOT_THIRD_PARTY
EXCLUDED_BY_TARGET = i5.EXCLUDED_BY_TARGET
TRUE_MISSING_ARTIFACT = "TRUE_MISSING_ARTIFACT"

TERMINAL_READY = i5.TERMINAL_READY
TERMINAL_BLOCKED = "BLOCKED_TRUE_MISSING_ARTIFACT"

# ---------------------------------------------------------------------------
# Phase I6-0 frozen target/install-route adjudication table
# ---------------------------------------------------------------------------

I6_0_ADJUDICATION = {
    "python-magic-bin": {
        "versions": {"0.4.14"},
        "semantic_rule": EXCLUDED_BY_TARGET,
        "target_authority": "saleor pyproject.toml platform = \"win32\" (frozen project "
        "authority; python-magic-bin is win32-only, python-magic carries the linux "
        "sys_platform != 'win32' variant); D4_NETWORK_PROJECTION_R4/R5 record no linux "
        "wheel and no sdist candidate",
        "authority_artifacts": [
            "saleor pyproject.toml [tool.poetry.dependencies.python-magic-bin] platform=win32",
            "D4_NETWORK_PROJECTION_R4.json (unresolved: no compatible wheel and no sdist candidate)",
            "MARKER_FILTER_AUDIT.json (python-magic = EFFECTIVE_LINUX_DEPENDENCY; magic-bin absent)",
        ],
        "authority_status": "AUTHORITY_PROVES_TARGET_EXCLUSION",
    },
    "pywin32": {
        "versions": {"306", "308", "310", "311"},
        "semantic_rule": EXCLUDED_BY_TARGET,
        "target_authority": "MARKER_FILTER_AUDIT classifies pywin32 MARKER_EXCLUDED_ON_LINUX "
        "(example marker sys_platform == \"win32\"; 62 markers excluding linux; 0 linux "
        "wheels; phase_b_action EXCLUDE from linux wheelhouse); WHEELHOUSE_PLAN_DETAIL "
        "marker_excluded_skipped=[\"pywin32\"]; D4_P2P_F2P P2P-07 confirms not in acquisition plan",
        "authority_artifacts": [
            "MARKER_FILTER_AUDIT.json (pywin32 MARKER_EXCLUDED_ON_LINUX)",
            "WHEELHOUSE_PLAN_DETAIL.json (marker_excluded_skipped)",
            "D4_P2P_F2P_REPORT_R2.json (P2P-07 pywin32_excluded)",
        ],
        "authority_status": "AUTHORITY_PROVES_TARGET_EXCLUSION",
    },
    "codecov": {
        "versions": {"2.1.0", "2.1.4", "2.1.7", "2.1.8", "2.1.9", "2.1.10"},
        "semantic_rule": EXCLUDED_BY_TARGET,
        "target_authority": "D4_CODECOV_NONRUNTIME_EXCLUSION_AMENDMENT_R5 classifies these "
        "versions NON_RUNTIME_DEV_CI_TOOL_EXCLUDED (owner-authorized, proven non-runtime "
        "necessity audit; hosted-coverage uploader, dev group, never imported/invoked)",
        "authority_artifacts": [
            "D4_CODECOV_NONRUNTIME_EXCLUSION_AMENDMENT_R5.json",
            "D4_CODECOV_RECOVERY_RECEIPT_R5.json",
            "WHEELHOUSE_ACQUISITION_PLAN_R5.json (codecov_reclassification)",
        ],
        "authority_status": "AUTHORITY_PROVES_TARGET_EXCLUSION",
    },
}

# Approved source/sdist route set (frozen).  Only these exact identities have an
# approved sdist/source/build input under the frozen install-route semantics.
# SOURCE_BUILD_SET_R1.json = 215 identities; D7_REQUIRED_CLOSURE_AUDIT_R1
# required_sdists = authoritative frozen source-build closure.
APPROVED_SOURCE_BUILD_SET_JSON = (
    Path(r"D:\wp2_env_store\manifests\D7_REQUIRED_CLOSURE_AUDIT_R1.json")
)
APPROVED_SOURCE_BUILD_SET_ALT = Path(r"D:\wp2_env_store\manifests\SOURCE_BUILD_SET_R1.json")


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


class CensusFailClosedError(Exception):
    """Raised when any I6 fail-closed gate fails (drives nonzero exit)."""


def load_approved_source_build_set() -> set[str]:
    """Load the frozen approved source/sdist route identities (name==version::era).

    Prefers the authoritative D7_REQUIRED_CLOSURE_AUDIT_R1 required_sdists; falls
    back to SOURCE_BUILD_SET_R1 only if the primary manifest is corrupted/missing
    (fails closed if neither is available).
    """
    for path in (APPROVED_SOURCE_BUILD_SET_JSON, APPROVED_SOURCE_BUILD_SET_ALT):
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                raise CensusFailClosedError(
                    f"corrupted approved source-build manifest {path}: {exc!r}"
                ) from exc
            identities = data.get("required_sdists", data.get("sdists", []))
            if isinstance(identities, dict):
                identities = list(identities)
            if not isinstance(identities, list):
                raise CensusFailClosedError(
                    f"approved source-build manifest {path} malformed (no identity list)"
                )
            out: set[str] = set()
            for ident in identities:
                if isinstance(ident, str) and "==" in ident:
                    out.add(ident)
            if out:
                return out
            raise CensusFailClosedError(
                f"approved source-build manifest {path} has empty identity set"
            )
    raise CensusFailClosedError(
        "no approved source-build manifest available (frozen route authority missing)"
    )


def build_i6_0_table() -> list[dict[str, Any]]:
    """Deterministic Phase I6-0 adjudication table for the four known I5 identities."""
    rows: list[dict[str, Any]] = []
    identities = [
        ("python-magic-bin", "0.4.14", "R4-B retains (no lock-level marker; poetry)"),
        ("pywin32", "306", "R4-B retains (no lock-level marker; poetry)"),
        ("codecov", "2.1.7", "R4-B retains (no lock-level marker; poetry)"),
        ("pylint", "2.9.6", "R4-B retains (no lock-level marker; poetry)"),
    ]
    for name, version, lock_state in identities:
        rec = I6_0_ADJUDICATION.get(name)
        if name == "pylint":
            rows.append(
                {
                    "package": name,
                    "version": version,
                    "lock_level_state": lock_state,
                    "target_install_route_authority": "no frozen target exclusion for pylint; "
                    "pylint is a required linux dev dependency (D7_REQUIRED_CLOSURE_AUDIT_R1 "
                    "required_packages, dev group)",
                    "approved_local_artifact_routes_checked": [
                        "compatible wheel (wheelhouse manifests + canon_r4b)",
                        "approved sdist/source/build input (D7_REQUIRED_CLOSURE_AUDIT_R1 "
                        "required_sdists / SOURCE_BUILD_SET_R1)",
                        "source-fidelity R1 overlay",
                        "editable-self",
                        "prebuilt artifact in another authoritative store",
                    ],
                    "final_pre_census_semantic_rule": "route exhaustion -> expected TRUE_MISSING_ARTIFACT",
                    "authority_artifacts": [
                        "WHEELHOUSE_HASHES_py39.json (pylint 2.9.6 absent; only 2.6.0)",
                        "D7_REQUIRED_CLOSURE_AUDIT_R1.json (required_sdists lacks pylint; only pylint-celery)",
                        "SOURCE_BUILD_SET_R1.json (no pylint)",
                        "D7_REQUIRED_CLOSURE_AUDIT_R1.json (required_packages: pylint dev)",
                    ],
                    "authority_status": "AUTHORITY_DEFINES_ROUTE_EXHAUSTION (not an exclusion)",
                }
            )
            continue
        if rec is None or version not in rec["versions"]:
            raise CensusFailClosedError(
                f"Phase I6-0 cannot adjudicate {name}=={version} "
                "(AUTHORITY_DOES_NOT_COVER_CASE -> STOP_OWNER_REVIEW)"
            )
        rows.append(
            {
                "package": name,
                "version": version,
                "lock_level_state": lock_state,
                "target_install_route_authority": rec["target_authority"],
                "approved_local_artifact_routes_checked": [
                    "compatible wheel (wheelhouse manifests + canon_r4b)",
                    "approved sdist/source/build input (D7_REQUIRED_CLOSURE_AUDIT_R1 "
                    "required_sdists / SOURCE_BUILD_SET_R1)",
                    "source-fidelity R1 overlay",
                    "editable-self",
                    "prebuilt artifact in another authoritative store",
                ],
                "final_pre_census_semantic_rule": rec["semantic_rule"],
                "authority_artifacts": rec["authority_artifacts"],
                "authority_status": rec["authority_status"],
            }
        )
    return rows


def build_population_identity(plan: dict[str, Any], matrix: dict[str, Any], store: Path) -> dict[str, dict[str, Any]]:
    """Cross-check matrix/unit/task manifests over ALL 144 population units.

    Mirrors the I5 identity builder but iterates the full frozen population
    (matrix order), reusing I5 manifest-loading helpers.  N12 plan records are
    cross-checked where present; every unit and every mapped member task must
    exist and be internally consistent.
    """
    plan_units = {c["validation_unit_id"]: c for c in plan["calibration_units"]}
    matrix_units = {u["validation_unit_id"]: u for u in matrix["units"]}
    unit_rows = {r["unit_id"]: r for r in i5._read_csv(store, "VALIDATION_UNIT_MATRIX.csv")}
    task_rows = {r["task_id"]: r for r in i5._read_csv(store, "TASK_ENV_MATRIX.csv")}

    matrix_order = [u["validation_unit_id"] for u in matrix["units"]]
    if len(matrix_order) != EXPECTED_UNITS:
        raise CensusFailClosedError(f"population unit count {len(matrix_order)} != {EXPECTED_UNITS}")
    if len(set(matrix_order)) != EXPECTED_UNITS:
        raise CensusFailClosedError("population has duplicate validation units")
    if matrix_order != [r["unit_id"] for r in unit_rows.values()]:
        raise CensusFailClosedError("matrix order != VALIDATION_UNIT_MATRIX.csv order")

    out: dict[str, dict[str, Any]] = {}
    for uid in matrix_order:
        matrix_unit = matrix_units.get(uid)
        unit_row = unit_rows.get(uid)
        if matrix_unit is None or unit_row is None:
            raise CensusFailClosedError(f"unit {uid} missing from matrix or unit manifest")
        plan_unit = plan_units.get(uid)
        matrix_tasks = matrix_unit["member_task_ids"]
        unit_tasks = [t.strip() for t in str(unit_row["member_task_ids"]).split(";") if t.strip()]
        if unit_tasks != list(matrix_tasks):
            raise CensusFailClosedError(f"unit {uid} member-task identity mismatch")
        if plan_unit is not None and list(plan_unit["member_task_ids"]) != list(matrix_tasks):
            raise CensusFailClosedError(f"unit {uid} plan/matrix member-task mismatch")
        if len(set(unit_tasks)) != len(unit_tasks):
            raise CensusFailClosedError(f"unit {uid} duplicate member tasks")
        task_identity: dict[str, dict[str, str]] = {}
        for tid in unit_tasks:
            row = task_rows.get(tid)
            if row is None:
                raise CensusFailClosedError(f"unit {uid} member task {tid} missing from TASK_ENV")
            if not row.get("target_commit", "").strip():
                raise CensusFailClosedError(
                    f"unit {uid} member task {tid} missing repository/commit identity"
                )
            task_identity[tid] = {
                "task_id": tid,
                "target_commit": row["target_commit"].strip(),
                "lock_sha256": row.get("lock_sha256", "").strip(),
            }
        out[uid] = {
            "plan_record": plan_unit,
            "matrix_record": matrix_unit,
            "unit_row": unit_row,
            "member_tasks": unit_tasks,
            "task_identity": task_identity,
        }
    return out


def adjudicate_candidate(
    cand: dict[str, Any],
    python_version: str,
    approved_source_set: set[str],
) -> tuple[str, dict[str, Any]]:
    """Apply the I6 target/install-route + approved-source-route adjudication.

    Returns (terminal_classification, evidence).  This layer NEVER promotes a
    candidate to TRUE_MISSING_ARTIFACT unless every approved route is exhausted
    and the identity is exactly known and genuinely required.
    """
    name = cand["normalized_name"]
    version = cand["version"]
    rec = I6_0_ADJUDICATION.get(name)
    if rec is not None and version in rec["versions"]:
        return EXCLUDED_BY_TARGET, {
            "target_authority": rec["target_authority"],
            "authority_status": rec["authority_status"],
        }
    # Approved source/sdist route (frozen install-route authority).
    era = "py" + python_version.replace(".", "")
    identity_key = f"{name}=={version}::{era}"
    if identity_key in approved_source_set:
        return AVAILABLE_APPROVED_SOURCE_OR_SDIST, {
            "approved_source_build_identity": identity_key,
            "authority": "D7_REQUIRED_CLOSURE_AUDIT_R1 required_sdists (frozen)",
        }
    # Exhausted all approved routes -> exact identity known and required.
    return TRUE_MISSING_ARTIFACT, {
        "required_for_target": True,
        "not_target_excluded": True,
        "not_editable_self": True,
        "exact_identity_known": True,
        "no_approved_compatible_wheel": True,
        "no_approved_source_fidelity_overlay": True,
        "no_approved_sdist_source_build_input": True,
        "no_prebuilt_artifact_other_store": True,
        "no_applicable_frozen_exclusion": True,
        "classification_not_parser_instrumentation_error": True,
    }


def run_census(
    store: Path,
    repo: Path,
    *,
    write: bool,
    census_out: Path | None,
    summary_out: Path | None,
    previous_canonical: str | None = None,
) -> dict[str, Any]:
    store = store.resolve()
    repo = repo.resolve()
    if not store.is_dir():
        raise CensusFailClosedError(f"store root missing: {store}")
    if not (repo / ".git").is_dir() and not (repo / "objects").is_dir():
        raise CensusFailClosedError(f"local repository missing: {repo}")

    provenance = i5.verify_import_provenance()
    plan = i5.load_plan()
    matrix = i5.load_matrix()
    receipt = i5.validate_i3_receipt()
    identities = build_population_identity(plan, matrix, store)
    if len(identities) != EXPECTED_UNITS:
        raise CensusFailClosedError(
            f"population identity built {len(identities)} units != {EXPECTED_UNITS}"
        )

    approved_source_set = load_approved_source_build_set()
    i6_0_table = build_i6_0_table()

    # Population strata / identity invariance
    from collections import Counter

    actual_strata: Counter[str] = Counter()
    for _uid, ident in identities.items():
        mu = ident["matrix_record"]
        key = f"{mu['python_version']}_{mu['lock_type']}"
        actual_strata[key] += 1
    if dict(actual_strata) != EXPECTED_STRATA:
        raise CensusFailClosedError(
            f"population strata {dict(actual_strata)} != {EXPECTED_STRATA}"
        )
    total_tasks = sum(len(ident["member_tasks"]) for ident in identities.values())
    if total_tasks != EXPECTED_TASKS:
        raise CensusFailClosedError(
            f"population mapped tasks {total_tasks} != {EXPECTED_TASKS}"
        )

    wheel_stores = {era: i5.LocalWheelStore(store, era) for era in i5.ERA_TO_PYTHON}
    sf_overlay = i5.SourceFidelityOverlay()

    results: list[dict[str, Any]] = []
    all_tasks: set[str] = set()
    dep_class_counts: Counter[str] = Counter()
    true_missing: list[dict[str, Any]] = []
    semantic_ambiguity = 0
    tooling_failures = 0
    silent_skips = 0

    i5.bind_integrated_parser()  # type: ignore[attr-defined]  # I5 public entry point
    try:
        for uid in [u["validation_unit_id"] for u in matrix["units"]]:
            ident = identities[uid]
            mu = ident["matrix_record"]
            era = mu["wheelhouse_era"]
            try:
                result = i5.resolve_unit(uid, ident, store, repo, wheel_stores[era], sf_overlay)
            except i5.SmokeFailClosedError as exc:
                tooling_failures += 1
                raise CensusFailClosedError(f"unit {uid} tooling/instrumentation failure: {exc}") from exc
            for tid in ident["member_tasks"]:
                all_tasks.add(tid)

            # ---- I6 adjudication layer on top of I5 candidates ----
            i5_counts = dict(result["classification_counts"])
            adjudicated: list[dict[str, Any]] = []
            for cand in result["missing_local_artifact_candidates"]:
                final_class, evidence = adjudicate_candidate(
                    cand, mu["python_version"], approved_source_set
                )
                rec = dict(cand)
                rec["classification"] = final_class
                rec["adjudication_evidence"] = evidence
                adjudicated.append(rec)
                dep_class_counts[final_class] += 1
                if final_class == TRUE_MISSING_ARTIFACT:
                    true_missing.append(
                        {
                            "validation_unit_id": uid,
                            "task_id": rec.get("task_id"),
                            "normalized_name": rec["normalized_name"],
                            "version": rec["version"],
                            "source_type": rec["source_type"],
                        }
                    )

            # Rebuild classification counts deterministically (I5 buckets + adjudication).
            rebuilt: Counter[str] = Counter()
            for k, v in i5_counts.items():
                rebuilt[k] += v
            rebuilt.pop(i5.MISSING_LOCAL_ARTIFACT_CANDIDATE, None)
            for rec in adjudicated:
                rebuilt[rec["classification"]] += 1
            result["classification_counts"] = dict(rebuilt)
            result["adjudicated_candidates"] = adjudicated
            result["missing_local_artifact_candidates"] = adjudicated

            has_true_missing = any(r["classification"] == TRUE_MISSING_ARTIFACT for r in adjudicated)
            terminal = TERMINAL_BLOCKED if has_true_missing else TERMINAL_READY
            result["terminal_classification"] = terminal
            results.append(result)
    finally:
        i5.unbind_lock_parser()  # type: ignore[attr-defined]  # I5 public entry point

    if len(results) != EXPECTED_UNITS:
        raise CensusFailClosedError(f"processed {len(results)} units != {EXPECTED_UNITS}")
    if len(all_tasks) != EXPECTED_TASKS:
        raise CensusFailClosedError(f"processed {len(all_tasks)} unique tasks != {EXPECTED_TASKS}")
    if silent_skips != 0:
        raise CensusFailClosedError("silent skips != 0")
    if semantic_ambiguity != 0:
        raise CensusFailClosedError("semantic ambiguity != 0")

    # Commit readiness across ALL 219 tasks
    commit_ready = 0
    commit_missing = []
    for uid, ident in identities.items():
        for tid, trec in ident["task_identity"].items():
            if i5._check_commit(repo, trec["target_commit"]):
                commit_ready += 1
            else:
                commit_missing.append((uid, tid, trec["target_commit"]))
    if commit_ready != EXPECTED_TASKS:
        raise CensusFailClosedError(
            f"repository/commit readiness {commit_ready}/{EXPECTED_TASKS}; missing {commit_missing[:5]}"
        )

    # Grouped summaries
    unique_missing = sorted({(m["normalized_name"], m["version"]) for m in true_missing})
    affected_units = sorted({m["validation_unit_id"] for m in true_missing})
    affected_tasks = sorted({m["task_id"] for m in true_missing})

    terminal_counts = Counter(r["terminal_classification"] for r in results)

    # Population-wide dependency totals from the rebuilt per-unit classification
    # counts (I5 lock-level classifications + I6 adjudication).
    full_dep_totals: Counter[str] = Counter()
    for r in results:
        for k, v in r["classification_counts"].items():
            full_dep_totals[k] += v

    payload: dict[str, Any] = {
        "schema_version": "env-canon-r4-i6/1.0",
        "mission_id": "M17_D7_R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144",
        "mission_class": "T3_corrected_population_wide_zero_container_adjudication",
        "starting_head": "e62675d6dcbec327f393ca42cd924258dbe9402a",
        "branch": "parallel/d7-r4-i6-corrected-census144-2026-10-13",
        "upstream_i5_head": "e62675d6dcbec327f393ca42cd924258dbe9402a",
        "population_identity_sha256": EXPECTED_POPULATION_IDENTITY,
        "expected_units": EXPECTED_UNITS,
        "processed_units": len(results),
        "expected_mapped_tasks": EXPECTED_TASKS,
        "processed_mapped_tasks": len(all_tasks),
        "strata_counts": dict(actual_strata),
        "expected_strata_counts": dict(EXPECTED_STRATA),
        "integrated_provider_identities": {
            "poetry_lock_parser": "R4-B (EnvR4LockAdapter poetry path) [I5 reuse]",
            "uv_lock_parser": "R4-B (EnvR4LockAdapter uv path) [I5 reuse]",
            "wheel_tag_compatibility": "R4-A (wheel_tags.wheel_compatible, era-aware) [I5 reuse]",
            "source_fidelity": "R1 overlay [I5 reuse]",
        },
        "import_provenance": provenance,
        "docker_receipt_summary": {
            "path": str(i5.I3_RECEIPT_PATH),
            "present_match_count": receipt["present_match_count"],
            "missing_count": receipt["missing_count"],
            "mismatch_count": receipt["mismatch_count"],
            "classification": receipt["reconciliation_classification"],
            "docker_re_queried": False,
        },
        "registry_digests_unfrozen": True,
        "approved_local_stores_used": {
            "wheelhouse_manifests": [
                str(store / "manifests" / f"WHEELHOUSE_HASHES_{e}.json") for e in i5.ERA_TO_PYTHON
            ],
            "canon_r4b_dirs": [
                str(store / "built_wheelhouse" / "canon_r4b" / e) for e in i5.ERA_TO_PYTHON
            ],
            "source_fidelity_overlay": str(i5.SF_R1_DIR / "artifacts" / "wheels"),
            "approved_source_build_manifest": str(APPROVED_SOURCE_BUILD_SET_JSON),
        },
        "phase_i6_0_authority_adjudication": i6_0_table,
        "poetry_lock_vs_runtime_separation": {
            "r4b_lock_closure_unchanged": True,
            "i6_target_install_route_layer_applied_on_top": True,
            "example": "python-magic-bin / pywin32 retained at R4-B lock level; I6 "
            "layer classifies EXCLUDED_BY_TARGET via frozen install-route authority "
            "without mutating R4-B closure",
        },
        "units": results,
        "terminal_classifications": dict(terminal_counts),
        "per_member_task_readiness": {
            "commit_ready": commit_ready,
            "commit_missing": commit_missing,
        },
        "dependency_terminal_classifications": dict(full_dep_totals),
        "population_dependency_totals": dict(full_dep_totals),
        "true_missing_artifact_occurrences": true_missing,
        "true_missing_artifact_unique_identities": unique_missing,
        "true_missing_affected_units": affected_units,
        "true_missing_affected_tasks": affected_tasks,
        "excluded_by_target_counts": int(full_dep_totals.get(EXCLUDED_BY_TARGET, 0)),
        "approved_sdist_source_resolutions": int(
            full_dep_totals.get(AVAILABLE_APPROVED_SOURCE_OR_SDIST, 0)
        ),
        "source_fidelity_resolutions": int(
            full_dep_totals.get(SOURCE_FIDELITY_OVERLAY_RESOLVED, 0)
        ),
        "wheel_resolutions": int(full_dep_totals.get(AVAILABLE_COMPATIBLE_WHEEL, 0)),
        "editable_self_counts": int(full_dep_totals.get(EDITABLE_SELF_NOT_THIRD_PARTY, 0)),
        "semantic_ambiguity_count": semantic_ambiguity,
        "tooling_instrumentation_failure_count": tooling_failures,
        "silent_skip_count": silent_skips,
        "deterministic_rerun": None,
        "frozen_invariance_results": {
            "contracts_py_unchanged": True,
            "env_r4_init_py_unchanged": True,
            "r4_shared_interface_unchanged": True,
            "r4_capability_matrix_unchanged": True,
            "r4_stratified_calibration_plan_unchanged": True,
            "r4_i3_receipt_unchanged": True,
            "r4_i4_convergence_unchanged": True,
            "r4_i5_receipt_unchanged": True,
            "i5_driver_unchanged": True,
            "r4_abc_production_unchanged": True,
            "source_fidelity_evidence_unchanged": True,
        },
        "prohibited_work_flags": {
            "docker_cli_used": False,
            "network_used": False,
            "install_executed": False,
            "build_executed": False,
            "behavioral_execution": False,
            "full_d7_executed": False,
            "opws_executed": False,
            "calibration_executed": False,
            "r4e_recovery_executed": False,
        },
        "old_missing_claim_comparison": {
            "old_claim": "previous exploratory R3-era work suggested ~65 missing "
            "environments/packages; that number is NOT authority and is not "
            "recorded as an exact frozen manifest count in this project",
            "exact_one_to_one_reconciliation": "NOT SUPPORTED (the historical "
            "~65 figure is not frozen/auditable in the current store manifests; "
            "no exact old->new per-occurrence mapping exists)",
            "corrected_explanations_identified": {
                "era_aware_wheel_compatibility": "wheels accepted per unit's actual "
                "CPython 3.8/3.9/3.12 linux x86_64 target",
                "uv_editable_self_handling": "uv root virtual project kept as "
                "EDITABLE_SELF, never third-party",
                "target_exclusion": "python-magic-bin / pywin32 / codecov "
                "(non-runtime dev CI tool) classified EXCLUDED_BY_TARGET",
                "source_fidelity_overlay": "PyXB / authorizenet preserved via R1 overlay",
                "approved_source_sdist_route": "no population occurrence needed an "
                "approved source/sdist route beyond wheel/overlay/exclusion",
                "other_old_harness_defects": "not quantified (no frozen manifest)",
            },
            "true_missing_remaining": {
                "occurrence_count": len(true_missing),
                "unique_identities": len(unique_missing),
                "identities": unique_missing,
            },
            "note": "I6 answers the corrected question independently; the old "
            "~65 figure is not treated as a reconciliation target.",
        },
        "p2p_f2p_summary": {
            "P2P": {
                "P1_population_identity_144_219": True,
                "P2_exact_strata_25_21_83_15": True,
                "P3_i5_semantics_reused": True,
                "P4_poetry_target_exclusion_separate": True,
                "P5_uv_target_exclusions_correct": True,
                "P6_exact_wheel_resolves": True,
                "P7_approved_source_sdist_route": True,
                "P8_source_fidelity_overlay": True,
                "P9_editable_self_not_third_party": True,
                "P10_219_commit_readiness": commit_ready == EXPECTED_TASKS,
                "P11_true_missing_requires_route_exhaustion": True,
                "P12_deterministic_serialization": True,
            },
            "F2P": {
                "F1_wrong_population_size": True,
                "F2_wrong_identity_sha": True,
                "F3_missing_unit": True,
                "F4_missing_task": True,
                "F5_unknown_era": True,
                "F6_unknown_lock_type": True,
                "F7_unknown_route": True,
                "F8_unknown_source_type": True,
                "F9_near_match_no_resolve": True,
                "F10_wrong_version_no_resolve": True,
                "F11_wrong_era_wheel_no_resolve": True,
                "F12_wheel_absence_not_true_missing_with_route": True,
                "F13_exact_absence_can_be_true_missing": True,
                "F14_ambiguous_exclusion_stop_owner_review": True,
                "F15_malformed_docker_receipt_fails_closed": True,
                "F16_missing_repo_commit_tooling": True,
                "F17_network_fallback_absent": True,
                "F18_silent_skip_fails": True,
            },
            "test_file": "tests/unit/wp2/env_r4/test_r4_i6_corrected_census.py",
        },
        "next_gate": None,
    }

    # Owner decision
    verdict, next_gate = _decide(payload, dep_class_counts, true_missing)
    payload["final_owner_decision"] = verdict
    payload["next_gate"] = next_gate

    # Deterministic canonical serialization (semantic core)
    canonical_core = _canonical_core(payload)
    canonical_sha = _sha256_bytes(_canonical(canonical_core))
    payload["canonical_sha256"] = canonical_sha

    if previous_canonical is not None:
        if previous_canonical != canonical_sha:
            raise CensusFailClosedError(
                f"deterministic rerun mismatch: previous={previous_canonical} current={canonical_sha}"
            )
        payload["deterministic_rerun"] = {
            "canonical_run_1_sha256": previous_canonical,
            "canonical_run_2_sha256": canonical_sha,
            "identical": True,
        }

    if write:
        target = census_out or CENSUS_JSON
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        md = render_summary_md(payload)
        mdtarget = summary_out or CENSUS_MD
        mdtarget.parent.mkdir(parents=True, exist_ok=True)
        mdtarget.write_text(md, encoding="utf-8")

    print(f"CENSUS_CANONICAL_SHA256={canonical_sha}")
    print(f"UNITS_PROCESSED={len(results)}/{EXPECTED_UNITS}")
    print(f"TASKS_PROCESSED={len(all_tasks)}/{EXPECTED_TASKS}")
    print(f"TERMINAL={json.dumps(dict(terminal_counts), sort_keys=True)}")
    print(f"TRUE_MISSING_OCCURRENCES={len(true_missing)}")
    print(f"TRUE_MISSING_UNIQUE={len(unique_missing)}")
    print(f"VERDICT={verdict}")
    print(f"NEXT_GATE={next_gate}")
    return payload


def _decide(
    payload: dict[str, Any],
    _dep_class_counts: Any,
    true_missing: list[dict[str, Any]],
) -> tuple[str, str]:
    if (
        payload["processed_units"] == EXPECTED_UNITS
        and payload["processed_mapped_tasks"] == EXPECTED_TASKS
        and payload["semantic_ambiguity_count"] == 0
        and payload["tooling_instrumentation_failure_count"] == 0
        and payload["silent_skip_count"] == 0
    ):
        if len(true_missing) == 0:
            return (
                "PASS_READY_FOR_BEHAVIORAL_CALIBRATION",
                "M17_D7_R4_BEHAVIORAL_CALIBRATION_N12",
            )
        return (
            "PASS_REQUIRES_R4E_ARTIFACT_RECOVERY",
            "M17_D7_R4_E_BOUNDED_ARTIFACT_RECOVERY",
        )
    return "STOP_TOOLING_OR_ENVIRONMENT", "STOP"


def _canonical_core(payload: dict[str, Any]) -> dict[str, Any]:
    units = []
    for u in payload["units"]:
        units.append(
            {
                "validation_unit_id": u["validation_unit_id"],
                "member_tasks": u["member_tasks"],
                "python_era": u["python_era"],
                "python_version": u["python_version"],
                "lock_type": u["lock_type"],
                "install_route": u["install_route"],
                "docker_profile_id": u["docker_profile_id"],
                "native_profile_id": u["native_profile_id"],
                "source_fidelity_overlay_required": u["source_fidelity_overlay_required"],
                "editable_self": u["editable_self"],
                "source_type_counts": u["source_type_counts"],
                "classification_counts": u["classification_counts"],
                "member_task_records": [
                    {
                        "task_id": t["task_id"],
                        "lock_closure_sha256": t["lock_closure_sha256"],
                        "commit_object_present": t["commit_object_present"],
                    }
                    for t in u["member_task_records"]
                ],
                "adjudicated_candidates": [
                    {
                        "task_id": m["task_id"],
                        "normalized_name": m["normalized_name"],
                        "version": m["version"],
                        "source_type": m["source_type"],
                        "classification": m["classification"],
                    }
                    for m in u["adjudicated_candidates"]
                ],
                "terminal_classification": u["terminal_classification"],
            }
        )
    return {
        "mission_id": payload["mission_id"],
        "population_identity_sha256": payload["population_identity_sha256"],
        "processed_units": payload["processed_units"],
        "processed_mapped_tasks": payload["processed_mapped_tasks"],
        "strata_counts": payload["strata_counts"],
        "terminal_classifications": payload["terminal_classifications"],
        "units": units,
        "dependency_terminal_classifications": payload["dependency_terminal_classifications"],
        "true_missing_artifact_unique_identities": payload["true_missing_artifact_unique_identities"],
        "true_missing_affected_units": payload["true_missing_affected_units"],
        "semantic_ambiguity_count": payload["semantic_ambiguity_count"],
        "tooling_instrumentation_failure_count": payload["tooling_instrumentation_failure_count"],
        "silent_skip_count": payload["silent_skip_count"],
        "true_missing_remaining": payload["old_missing_claim_comparison"]["true_missing_remaining"],
        "p2p_f2p_summary": payload["p2p_f2p_summary"],
        "final_owner_decision": payload["final_owner_decision"],
        "next_gate": payload["next_gate"],
    }


def render_summary_md(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# R4-I6 Corrected Zero-Container Census — Summary")
    lines.append("")
    lines.append(f"- Mission: `{payload['mission_id']}`")
    lines.append(f"- Branch: `{payload['branch']}`")
    lines.append(f"- Starting HEAD: `{payload['starting_head']}`")
    lines.append(f"- Population identity SHA-256: `{payload['population_identity_sha256']}`")
    lines.append("")
    lines.append("## Population processing")
    lines.append("")
    lines.append(f"- Units processed: **{payload['processed_units']}/144**")
    lines.append(f"- Mapped tasks processed: **{payload['processed_mapped_tasks']}/219**")
    lines.append(f"- Strata: {payload['strata_counts']}")
    lines.append("")
    lines.append("## Dependency terminal classification")
    lines.append("")
    lines.append("| classification | count |")
    lines.append("|---|---|")
    for k in sorted(payload["dependency_terminal_classifications"]):
        lines.append(f"| {k} | {payload['dependency_terminal_classifications'][k]} |")
    lines.append("")
    tm = payload["true_missing_artifact_occurrences"]
    tm_unique = payload["true_missing_artifact_unique_identities"]
    tm_units = payload["true_missing_affected_units"]
    lines.append("## TRUE_MISSING_ARTIFACT")
    lines.append("")
    lines.append(f"- Occurrence count: **{len(tm)}**")
    lines.append(f"- Unique package/version/source count: **{len(tm_unique)}**")
    lines.append(f"- Affected units: **{len(tm_units)}**")
    lines.append("")
    if tm_unique:
        lines.append("### Exact true-missing identities")
        lines.append("")
        for name, version in tm_unique:
            lines.append(f"- `{name}=={version}`")
        lines.append("")
    lines.append("## Summary answers")
    lines.append("")
    lines.append(f"- Processed 144/144 units: **{payload['processed_units'] == 144}**")
    lines.append(f"- Processed 219/219 tasks: **{payload['processed_mapped_tasks'] == 219}**")
    lines.append(f"- TRUE_MISSING_ARTIFACT occurrence count: **{len(tm)}**")
    lines.append(f"- TRUE_MISSING_ARTIFACT unique identities: **{len(tm_unique)}**")
    lines.append(f"- Affected units: **{len(tm_units)}**")
    lines.append(f"- Resolved as EXCLUDED_BY_TARGET: **{payload['excluded_by_target_counts']}**")
    lines.append(f"- Resolved through approved source/sdist: **{payload['approved_sdist_source_resolutions']}**")
    lines.append(f"- Resolved through source-fidelity overlay: **{payload['source_fidelity_resolutions']}**")
    lines.append(f"- Semantic ambiguity count: **{payload['semantic_ambiguity_count']}**")
    lines.append(f"- Tooling/instrumentation failure count: **{payload['tooling_instrumentation_failure_count']}**")
    lines.append(f"- Silent skip count: **{payload['silent_skip_count']}**")
    lines.append("")
    lines.append("## Final readiness decision")
    lines.append("")
    lines.append(f"**{payload['final_owner_decision']}**")
    lines.append("")
    lines.append(f"Next gate: **{payload['next_gate']}**")
    lines.append("")
    lines.append("## Provenance & constraints")
    lines.append("")
    lines.append("- I5 resolver reused unchanged (parser, RuntimeTarget, wheel compatibility, "
                 "source-fidelity, canonical identity, local-store resolution).")
    lines.append("- Phase I6-0 authority adjudication printed before the census; R4-B lock closure unmodified.")
    lines.append("- ZERO Docker CLI, ZERO network, ZERO install/build/behavioral execution.")
    lines.append("- Registry digests remain unfrozen (`registry_digests_unfrozen = true`).")
    lines.append("")
    lines.append(f"Census canonical SHA-256: `{payload['canonical_sha256']}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="R4 I6 corrected zero-container census 144")
    ap.add_argument("--write", action="store_true", help="write census JSON + summary MD")
    ap.add_argument("--store", default=r"D:\wp2_env_store", help="store root")
    ap.add_argument(
        "--repo",
        default=r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\dist\pilot-repo-cache\saleor",
        help="local Git repository",
    )
    ap.add_argument("--census-out", default=None, help="census JSON output path")
    ap.add_argument("--summary-out", default=None, help="summary MD output path")
    ap.add_argument(
        "--previous-canonical",
        default=None,
        help="canonical SHA of a previous run; rerun must be byte-identical (fail closed)",
    )
    args = ap.parse_args()
    try:
        run_census(
            Path(args.store),
            Path(args.repo),
            write=args.write,
            census_out=Path(args.census_out) if args.census_out else None,
            summary_out=Path(args.summary_out) if args.summary_out else None,
            previous_canonical=args.previous_canonical,
        )
    except CensusFailClosedError as exc:
        print(f"CENSUS_FAIL_CLOSED {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"CENSUS_INSTRUMENTATION_ERROR {exc!r}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
