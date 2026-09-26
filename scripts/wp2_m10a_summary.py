#!/usr/bin/env python3
"""WP-2 Mission-10A: materiality evaluation + summary + V3 impact estimate.

ZERO API. Evaluates the preregistered materiality rule against the read-only
audit and probe outcomes, writes mission10a_summary.json and
v3_impact_estimate.json, and prints the single decision token.

Usage:
    python scripts/wp2_m10a_summary.py [--out DIR]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.m10a_audit import (  # noqa: E402
    evaluate_materiality,
)

OUT_ROOT = PROJECT / "research" / "wp2" / "mission10a_env_audit_2026-09-26"


def load(out_root: Path, name: str) -> dict:
    return json.loads((out_root / name).read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out_root = Path(args.out) if args.out else OUT_ROOT

    matrix = load(out_root, "dependency_declaration_matrix.json")
    cat = load(out_root, "category_exclusion_analysis.json")
    sel = load(out_root, "probe_selection.json")
    recon = load(out_root, "reconciliation.json")

    # Count declared-but-not-installed causes from matrix.
    declared_not_installed = 0
    for t in matrix["tasks"]:
        for m in t["fixture_map"].values():
            if m["install_state"] == "B_DECLARED_BUT_NOT_INSTALLED":
                declared_not_installed += 1

    # Probe outcomes (task 1 ran; task 2 STOPPED per §18 due to S2 transition).
    probe_results_path = out_root / "probe" / "saleor-rc-74538ea00ce9" / "probe_results.json"
    set_a_recovery: Counter = Counter()
    set_b_transitions: dict = {}
    set_b_non_reg_holds: bool | None = None
    probe_ran = probe_results_path.exists()
    if probe_ran:
        pr = json.loads(probe_results_path.read_text(encoding="utf-8"))
        set_a_recovery = Counter(pr["set_a_error_recovery_class_counts"])
        set_b_transitions = pr["set_b_v2_class_transitions"]
        set_b_non_reg_holds = pr["set_b_v2_non_regression_holds"]

    # Materiality inputs.
    eng_cat = cat["datasets"]["P2P_U_ENG_cap200"]["by_category"]
    m3_systematic = (
        eng_cat["benchmark-count-queries"].get("excluded_share_of_category") == 1.0
        or eng_cat["mocker-fixture"].get("excluded_share_of_category") == 1.0
    )
    m1_new_oracle_valid = 0
    m2_recovered_behavioral_f2p = 0
    if probe_ran:
        m1_new_oracle_valid = 0  # recovered nodes are P2P_ONLY, task already oracle-valid
        m2_recovered_behavioral_f2p = set_a_recovery.get("BEHAVIORAL_F2P", 0)
    s1_new_infra_fail = 0
    s2_non_reg_holds = set_b_non_reg_holds if probe_ran else None

    decision = evaluate_materiality(
        declared_but_not_installed_causes=declared_not_installed,
        declared_installed_plugin_not_loaded_causes=0,
        m1_newly_oracle_valid_tasks=m1_new_oracle_valid,
        m2_recovered_behavioral_f2p_nodes=m2_recovered_behavioral_f2p,
        m3_systematic_category_exclusion=m3_systematic,
        s1_new_infrastructure_failure_categories=s1_new_infra_fail,
        s2_non_regression_holds=s2_non_reg_holds,
    )

    summary = {
        "artifact": "mission10a_summary",
        "schema_version": "mission10a-summary-v1",
        "created_utc": _now_utc(),
        "mission": "MISSION-10A_ENV_TEST_DEPENDENCY_AUDIT",
        "tier": "T3",
        "decision_token": decision,
        "inputs": {
            "declared_but_not_installed_causes": declared_not_installed,
            "declared_installed_but_plugin_not_loaded_causes": 0,
            "m1_newly_oracle_valid_tasks": m1_new_oracle_valid,
            "m2_recovered_behavioral_f2p_nodes": m2_recovered_behavioral_f2p,
            "m3_systematic_category_exclusion": m3_systematic,
            "s1_new_infrastructure_failure_categories": s1_new_infra_fail,
            "s2_non_regression_holds": s2_non_reg_holds,
            "probe_ran": probe_ran,
        },
        "probe_summary": {
            "ran": probe_ran,
            "selected_tasks": sel["selected_tasks"],
            "task1_set_a_recovery_class_counts": dict(set_a_recovery) if probe_ran else None,
            "task1_set_b_v2_transitions": set_b_transitions if probe_ran else None,
            "task1_set_b_non_regression_holds": set_b_non_reg_holds,
            "stopped_after_task1_reason": (
                "SET B classification transition (BEHAVIORAL_F2P->P2P_ONLY) under "
                "preregistered S2; Mission-10A section 18 requires STOP probe "
                "continuation and ENV_AUDIT_INCONCLUSIVE."
                if (probe_ran and set_b_non_reg_holds is False) else None
            ),
        },
        "reconciliation": {
            "C4_TOI": recon["C4"],
            "ENG_cap200": recon["P2P_U_ENG"],
            "C2": recon["C2"],
        },
    }
    (out_root / "mission10a_summary.json").write_text(
        json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8"
    )

    # V3 impact estimate (estimate only; NOT built in Mission-10A).
    eng_cat_total = eng_cat["benchmark-count-queries"].get("count", 0) + eng_cat["mocker-fixture"].get("count", 0)
    c4_cq = cat["datasets"]["C4"]["error_TOI_nodes_by_category"]["benchmark-count-queries"].get("count", 0)
    c4_mocker = cat["datasets"]["C4"]["error_TOI_nodes_by_category"]["mocker-fixture"].get("count", 0)
    c2_cq = cat["datasets"]["C2"]["error_nodes_by_category"]["benchmark-count-queries"].get("count", 0)
    c2_mocker = cat["datasets"]["C2"]["error_nodes_by_category"]["mocker-fixture"].get("count", 0)

    v3 = {
        "artifact": "v3_impact_estimate",
        "schema_version": "mission10a-v3-impact-v1",
        "created_utc": _now_utc(),
        "note": "ESTIMATE ONLY. Mission-10A does NOT build/run Env V3. V3 "
                "concept: same frozen era strategy + same historical lock + "
                "project-declared test/dev dependency group(s) that V2 omitted.",
        "recoverable_node_estimate": {
            "MEASURED_in_probe": {
                "task_saleor-rc-74538ea00ce9_set_a_recovered": sum(set_a_recovery.values()) if probe_ran else 0,
                "recovered_classes": dict(set_a_recovery) if probe_ran else None,
            },
            "PROJECTED_across_population": {
                "C4_benchmark_count_queries_error_TOI": c4_cq,
                "C4_mocker_fixture_error_TOI": c4_mocker,
                "C2_rescue_benchmark_count_queries_errors": c2_cq,
                "C2_rescue_mocker_fixture_errors": c2_mocker,
                "P2P_U_ENG_cap200_category_error_nodes": eng_cat_total,
                "label": "PROJECTION; never report as observed recovery.",
            },
        },
        "affected_tasks_estimate": {
            "matrix_tasks_with_declared_but_not_installed": len(
                [t for t in matrix["tasks"] if any(
                    m["install_state"] == "B_DECLARED_BUT_NOT_INSTALLED" for m in t["fixture_map"].values())]
            ),
            "affected_eras": sorted({t["era_key"] for t in matrix["tasks"]}),
        },
        "v3_artifacts_needing_new_versions": [
            "era image(s) (new image with dev/test group; frozen base reused)",
            "environment manifest (V3)",
            "C4 DEV oracle evidence (re-run required where category excluded)",
            "C2/MAIN oracle evidence if affected",
            "F2P sets",
            "P2P-S extraction (unchanged membership; re-verify)",
            "P2P-U candidate membership (collection membership may change)",
            "P2P-U ENG execution (re-run affected tasks)",
            "P2P-U full DEV execution",
            "Smoke draft population (if ENG oracle-valid membership changes)",
            "runtime/resource estimates",
            "reconciliation report V2->V3",
        ],
        "reusable_unchanged_metadata": [
            "historical task commits (unchanged)",
            "split membership (unchanged)",
            "oracle semantics (unchanged)",
            "test patch semantics (unchanged)",
            "P2P-S/P2P-U V2 scientific rules (unchanged)",
            "P2P-U membership artifact for unaffected tasks (re-verify hashes)",
        ],
        "runtime_estimate": {
            "ENG_probe_measured_wall_s_per_union_node_set": None,
            "DEV_47_cap200_re_run_central_h": 6.7,
            "note": "Central re-run time unchanged from Mission-09 estimate; "
                    "only category-excluded tasks need re-execution in the "
                    "cleanest path, not a full 47-task rerun.",
        },
        "decision_token_for_this_estimate": decision,
    }
    (out_root / "v3_impact_estimate.json").write_text(
        json.dumps(v3, indent=1, ensure_ascii=False), encoding="utf-8"
    )

    print("DECISION_TOKEN:", decision)
    print(f"declared_but_not_installed: {declared_not_installed}")
    print(f"m3_systematic_category_exclusion: {m3_systematic}")
    print(f"s2_non_regression_holds: {s2_non_reg_holds}")
    print("wrote mission10a_summary.json + v3_impact_estimate.json")
    return 0


def _now_utc() -> str:
    import datetime

    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


if __name__ == "__main__":
    raise SystemExit(main())
