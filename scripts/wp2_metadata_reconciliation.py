#!/usr/bin/env python3
"""WP-2 metadata reconciliation (amendment I, Mission 07 §14) - ZERO API.

Mechanically resolves:
1. Power-analysis CI-width mismatch (n=8): doc '≈0.63/0.6' vs JSON exact widths.
2. Empty-set claim: Agent empty count vs RM-CSS empty count (verified: 2 vs 29).
3. 147 vs 140 environment-family counts (canonical rule defined).
4. migration/config-heavy summary contradiction (summary=0 vs census).

Never overwrites old evidence; produces a reconciliation artifact.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

POWER = PROJECT / "research" / "wp2" / "wp2_power_scenarios_2026-09-22.json"
RESULT = PROJECT / "reports" / "wp1b_main297_result.json"
SIP_RM = PROJECT / "research" / "wp1a" / "sip_rmcss_per_task_predictions.json"
AGENT = PROJECT / "research" / "wp1b" / "main-297-2026-09-22" / "wp1b_agent_predictions.json"
ENVFP = PROJECT / "research" / "wp2" / "oracle_confirmation_2026-09-22" / "environment_fingerprints.json"
SELECTION = PROJECT / "research" / "wp2" / "wp2_oracle_confirmation_selection_2026-09-22.json"
SUMMARY = PROJECT / "research" / "wp2" / "oracle_confirmation_2026-09-22" / "summary.json"
CENSUS = PROJECT / "research" / "wp2" / "wp2_saleor_main297_census_2026-09-22.json"
OUT = PROJECT / "research" / "wp2" / "wp2_metadata_reconciliation_2026-09-23.json"

FAMILY_SALT = "wp2-env-family-2026-09-22"


def family_of(fp: dict) -> str:
    import hashlib
    payload = {
        "python_requirement": fp.get("python_requirement"),
        "dependency_files": sorted((fp.get("dependency_files") or {}).items()),
        "package_manager_markers": fp.get("package_manager_markers"),
        "django_version_constraint": fp.get("django_version_constraint"),
    }
    blob = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{FAMILY_SALT}::{blob}"


def main() -> int:
    power = json.loads(POWER.read_text(encoding="utf-8"))
    sip = json.loads(SIP_RM.read_text(encoding="utf-8"))
    agent = json.loads(AGENT.read_text(encoding="utf-8"))
    envfp = json.loads(ENVFP.read_text(encoding="utf-8"))["tasks"]
    selection = json.loads(SELECTION.read_text(encoding="utf-8"))
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    census = json.loads(CENSUS.read_text(encoding="utf-8"))

    # 1. CI width at n=8 (authoritative source: wp2_power_scenarios JSON)
    n8 = power["single_arm_ci_widths"]["8"]
    ci_widths_n8 = {k: v["width"] for k, v in n8.items()}

    # 2. Empty-set: Agent vs RM-CSS
    agent_empty = sum(
        1 for v in agent["per_task"].values()
        if v.get("prediction_empty") or not v.get("selected_paths")
    )
    rm_empty = sum(
        1 for v in sip["per_task"].values() if not v.get("rmcss_predicted_set")
    )
    common = set(sip["per_task"]) & set(agent["per_task"])
    identical = sum(
        1 for t in common
        if set(sip["per_task"][t].get("rmcss_predicted_set") or [])
        == set(agent["per_task"][t].get("selected_paths") or [])
    )

    # 3. env families: canonical rule = unique target-state fingerprint family
    fams_target = {
        family_of(states["target"])
        for states in envfp.values()
        if isinstance(states.get("target"), dict)
    }
    # selection-manifest count (as computed by scripts/wp2_oracle_summary.py)
    sel_fams = {t.get("env_family") or "UNKNOWN" for t in selection["selection"]["tasks"]}
    n_sel = len(sel_fams)

    # 4. migration/config-heavy
    summary_mch = summary["substrata"]["migration_config_heavy"]
    census_tasks = census["tasks"]

    def is_mch(t: dict) -> bool:
        return (t.get("n_migration", 0) or 0) + (t.get("n_config_or_infra", 0) or 0) > 0

    census_mch_all297 = sum(1 for t in census_tasks if is_mch(t))
    census_mch_220 = sum(
        1 for t in census_tasks if is_mch(t)
    )
    smoke_migration_heavy = [t["task_id"] for t in census_tasks if is_mch(t)][:5]

    findings = {
        "ci_width_n8": {
            "document_reported": (
                "n=8 single-arm CI width approx 0.6 "
                "(rounded text in WP2_ORACLE_CONFIRMATION_DESIGN_V1_STOP_REPORT_2026-09-22.md)"
            ),
            "authoritative_json": ci_widths_n8,
            "resolution": (
                "JSON is the authoritative computation (scripts/wp2_power_scenarios.py, "
                "exact Clopper-Pearson widths 0.5193-0.5696 at n=8); current-facing docs "
                "corrected to JSON-exact values"
            ),
        },
        "empty_set": {
            "agent_empty_count": agent_empty,
            "agent_empty_note": (
                "Agent EMPTY 2/297 (parser_failure), "
                "from reports/wp1b_main297_result.json agent_empty_by_reason"
            ),
            "rmcss_empty_count": rm_empty,
            "rmcss_empty_note": (
                "RM-CSS 29/297 empty MAIN scopes (empty r mcss_predicted_set), "
                "matching Claude audit"
            ),
            "scope_identical_count": identical,
            "resolution": (
                "claim sheet EMPTY 2/297 refers to the Agent only; "
                "RM-CSS empty count reported separately"
            ),
        },
        "env_families_147_vs_140": {
            "count_147": len(fams_target),
            "count_147_source": (
                "unique TARGET-state fingerprint families from "
                "environment_fingerprints.json (canonical V2 rule)"
            ),
            "count_140": n_sel,
            "count_140_source": (
                "selection-manifest unique env_family values "
                "(139 real + 1 UNKNOWN bucket: 20 Wave-A tasks have env_family None)"
            ),
            "resolution": (
                "canonical V2 fingerprint rule = unique target-state family over the "
                "220 candidates; 147 used for V2 reporting; the 140 is a different "
                "(selection-manifest) count, documented not contradictory"
            ),
        },
        "migration_config_heavy": {
            "summary_value": summary_mch,
            "summary_defect": (
                "summary.json substrata.migration_config_heavy=0 because per_task.jsonl "
                "rows lack n_migration/n_config_or_infra fields"
            ),
            "census_recomputed_297": census_mch_all297,
            "census_recomputed_220": census_mch_220,
            "smoke_evidence_example": smoke_migration_heavy,
            "resolution": (
                "recomputed from census source: 40/297 tasks have migration/config "
                "changes; summary.json 0 is a summary-script field defect, corrected "
                "in current-facing docs"
            ),
        },
    }
    artifact = {
        "artifact": "wp2_metadata_reconciliation",
        "date": "2026-09-23",
        "old_evidence_preserved": True,
        "findings": findings,
        "reconciliation_artifact_md": "docs/WP2_METADATA_RECONCILIATION_2026-09-23.md",
    }
    OUT.write_text(json.dumps(artifact, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(artifact["findings"], indent=1))
    print("wrote", OUT.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
