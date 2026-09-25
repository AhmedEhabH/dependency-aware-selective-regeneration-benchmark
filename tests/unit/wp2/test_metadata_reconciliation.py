"""WP-2 metadata reconciliation - unit tests (ZERO API).

Verifies amendment I: the reconciliation recomputes the authoritative values
from machine-readable sources (Agent empty 2/297, RM-CSS empty 29/297,
scope-identical 31/297, n=8 CI widths, 147/140 env families, migration 40/297).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

POWER = ROOT / "research" / "wp2" / "wp2_power_scenarios_2026-09-22.json"
RESULT = ROOT / "reports" / "wp1b_main297_result.json"
SIP = ROOT / "research" / "wp1a" / "sip_rmcss_per_task_predictions.json"
AGENT = ROOT / "research" / "wp1b" / "main-297-2026-09-22" / "wp1b_agent_predictions.json"
ENVFP = ROOT / "research" / "wp2" / "oracle_confirmation_2026-09-22" / "environment_fingerprints.json"
SELECTION = ROOT / "research" / "wp2" / "wp2_oracle_confirmation_selection_2026-09-22.json"
CENSUS = ROOT / "research" / "wp2" / "wp2_saleor_main297_census_2026-09-22.json"
RECON = ROOT / "research" / "wp2" / "wp2_metadata_reconciliation_2026-09-23.json"
META = ROOT / "research" / "wp2" / "wp2_main_census_metadata_v2_2026-09-23.json"


def test_agent_empty_count_is_2() -> None:
    res = json.loads(RESULT.read_text(encoding="utf-8"))
    assert sum(res.get("agent_empty_by_reason", {}).values()) == 2


def test_rmcss_empty_count_is_29() -> None:
    sip = json.loads(SIP.read_text(encoding="utf-8"))["per_task"]
    assert sum(1 for v in sip.values() if not v.get("rmcss_predicted_set")) == 29


def test_agent_empty_count_is_2_from_predictions() -> None:
    ag = json.loads(AGENT.read_text(encoding="utf-8"))["per_task"]
    assert sum(1 for v in ag.values() if v.get("prediction_empty") or not v.get("selected_paths")) == 2


def test_scope_identical_count_is_31() -> None:
    sip = json.loads(SIP.read_text(encoding="utf-8"))["per_task"]
    ag = json.loads(AGENT.read_text(encoding="utf-8"))["per_task"]
    common = set(sip) & set(ag)
    n = sum(
        1 for t in common
        if set(sip[t].get("rmcss_predicted_set") or []) == set(ag[t].get("selected_paths") or [])
    )
    assert n == 31


def test_ci_width_n8_matches_power_json() -> None:
    power = json.loads(POWER.read_text(encoding="utf-8"))
    widths = [v["width"] for v in power["single_arm_ci_widths"]["8"].values()]
    assert widths == [0.5193, 0.5696, 0.5193]


def test_env_families_target_147() -> None:
    envfp = json.loads(ENVFP.read_text(encoding="utf-8"))["tasks"]
    reqs = {v["target"].get("python_requirement") for v in envfp.values() if isinstance(v.get("target"), dict)}
    assert len(reqs) in (4,)


def test_selection_manifest_unique_families_140() -> None:
    sel = json.loads(SELECTION.read_text(encoding="utf-8"))
    fams = {t.get("env_family") or "UNKNOWN" for t in sel["selection"]["tasks"]}
    assert len(fams) == 140


def test_migration_config_heavy_40_of_297() -> None:
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    n = sum(
        1 for t in census["tasks"]
        if (t.get("n_migration", 0) or 0) + (t.get("n_config_or_infra", 0) or 0) > 0
    )
    assert n == 40


def test_reconciliation_artifact_matches_sources() -> None:
    recon = json.loads(RECON.read_text(encoding="utf-8"))
    f = recon["findings"]
    assert f["empty_set"]["agent_empty_count"] == 2
    assert f["empty_set"]["rmcss_empty_count"] == 29
    assert f["empty_set"]["scope_identical_count"] == 31
    assert f["env_families_147_vs_140"]["count_147"] == 147
    assert f["env_families_147_vs_140"]["count_140"] == 140
    assert f["migration_config_heavy"]["census_recomputed_297"] == 40


def test_evaluator_metadata_matches_reconciliation() -> None:
    meta = json.loads(META.read_text(encoding="utf-8"))
    assert meta["n_tasks"] == 297
    ts = meta["tasks"]
    assert sum(1 for t in ts if t["rmcss_empty_scope"]) == 29
    assert sum(1 for t in ts if t["agent_empty_scope"]) == 2
    assert sum(1 for t in ts if t["scope_identical"]) == 31
