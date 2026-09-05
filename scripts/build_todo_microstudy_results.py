"""SCIENTIFIC-MICROSTUDY-01 results computation and GO/NO-GO decision.

This is a standalone results/analysis module (not a framework). It reads the
persisted ``run_records.jsonl`` (RunRecordData) or synthetic records and
computes the preregistered scientific metrics plus the frozen GO/NO-GO
decision (PA-001 / D046 / D043).

RunRecordData remains the source of truth; this module only *derives* metrics
from the persisted evidence.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from benchmark.checkpoint.persistence import RunRecordData

FIVE_FILE_UNIVERSE = frozenset(
    {
        "todo/models.py",
        "todo/serializers.py",
        "todo/views.py",
        "todo/permissions.py",
        "todo/urls.py",
    }
)

# Frozen gold expected-action maps derived from the scenario YAMLs
# (expected_actions ∩ the five-file source universe). Migrations are excluded
# (shared-executor obligations, scored separately).
_GOLD_ACTIONS: dict[str, dict[str, str]] = {
    "todo-smoke-001": {
        "todo/models.py": "regenerate",
        "todo/serializers.py": "regenerate",
        "todo/views.py": "regenerate",
        "todo/permissions.py": "preserve",
        "todo/urls.py": "preserve",
    },
    "todo-smoke-002": {
        "todo/models.py": "regenerate",
        "todo/views.py": "regenerate",
        "todo/serializers.py": "preserve",
        "todo/permissions.py": "preserve",
        "todo/urls.py": "preserve",
    },
    "todo-smoke-003": {
        "todo/models.py": "regenerate",
        "todo/serializers.py": "regenerate",
        "todo/permissions.py": "regenerate",
        "todo/views.py": "regenerate",
        "todo/urls.py": "preserve",
    },
}

PERFECT_001_PREDICTED = {
    "todo/models.py": "regenerate",
    "todo/serializers.py": "regenerate",
    "todo/views.py": "regenerate",
    "todo/permissions.py": "preserve",
    "todo/urls.py": "preserve",
}

STRATEGY_AGENT = "iterative_repository_agent"
STRATEGY_SELECTIVE = "selective"

_BOTH_STRATEGIES = (STRATEGY_AGENT, STRATEGY_SELECTIVE)

STUDY_REQUIREMENT = "all 3 clear G1 AND G2 AND at least 2/3 clear G3"


def gold_sets_for_scenario(scenario_id: str) -> tuple[set[str], set[str]]:
    """Return (gold_regenerate, gold_preserve) for the frozen 5-file universe."""
    actions = _GOLD_ACTIONS.get(scenario_id)
    if actions is None:
        raise ValueError(f"Unknown scientific scenario: {scenario_id}")
    regen = {p for p, a in actions.items() if a == "regenerate"}
    preserve = FIVE_FILE_UNIVERSE - regen
    return regen, preserve


def _normalise_predicted_actions(
    record: RunRecordData,
) -> dict[str, str]:
    raw = record.predicted_actions or {}
    return {str(k): str(v) for k, v in raw.items()}


def compute_run_metrics(
    record: RunRecordData,
    scenario_id: str,
) -> dict[str, Any]:
    """Compute the preregistered per-run scientific metrics from persisted evidence.

    - changed_requirement_pass = scenario_evaluator_passed
    - baseline_pass = baseline_validation_passed (regression/preservation checks)
    - predicted_regenerate_source_paths / gold_regenerate_source_paths
    - impact_recall
    - actual_changed_source_paths / unintended_preserve_changes
    - preservation_pass
    - migration_generation_passed (scored separately, never affects recall)
    """
    if scenario_id == "todo-smoke-001":
        pass
    regen_gold, preserve_gold = gold_sets_for_scenario(scenario_id)

    predicted = _normalise_predicted_actions(record)
    predicted_regen = {
        p for p, a in predicted.items() if a == "regenerate" and p in FIVE_FILE_UNIVERSE
    }

    changed = list(record.changed_artifact_paths or [])
    changed_in_universe = {p for p in changed if p in FIVE_FILE_UNIVERSE}
    unintended = sorted(changed_in_universe & preserve_gold)

    gold_regen = regen_gold
    impact_recall = (
        len(predicted_regen & gold_regen) / len(gold_regen) if gold_regen else 1.0
    )

    preservation_pass = (
        len(unintended) == 0
        and record.baseline_validation_passed is not False
    )

    return {
        "run_id": record.run_id,
        "scenario_id": record.scenario_id,
        "strategy_id": record.strategy_id,
        "repetition": record.repetition,
        "status": record.status,
        "changed_requirement_pass": bool(
            record.scenario_evaluator_passed is True
        ),
        "baseline_pass": bool(record.baseline_validation_passed is True),
        "migration_generation_passed": (
            record.migration_generation_passed is True
        ),
        "gold_regenerate_source_paths": sorted(gold_regen),
        "predicted_regenerate_source_paths": sorted(predicted_regen),
        "impact_recall": impact_recall,
        "impact_recall_full": impact_recall == 1.0,
        "gold_preserve_source_paths": sorted(preserve_gold),
        "actual_changed_source_paths": sorted(changed_in_universe),
        "unintended_preserve_changes": unintended,
        "preservation_pass": preservation_pass,
        # Efficiency
        "selection_prompt_tokens": record.selection_prompt_tokens,
        "selection_completion_tokens": record.selection_completion_tokens,
        "regeneration_prompt_tokens": record.regeneration_prompt_tokens,
        "regeneration_completion_tokens": record.regeneration_completion_tokens,
        "repair_prompt_tokens": record.repair_prompt_tokens,
        "repair_completion_tokens": record.repair_completion_tokens,
        "total_workflow_tokens": record.total_workflow_tokens,
        "total_workflow_model_calls": record.total_workflow_model_calls,
        "selected_artifact_count": record.selected_artifact_count,
        "regenerated_artifact_count": record.regenerated_artifact_count,
        "duration_seconds": record.duration_seconds,
        "repair_attempts": record.repair_attempts,
    }


def _passes_count(records: list[RunRecordData], key: str, scenario_id: str) -> int:
    return sum(
        1 for r in records if compute_run_metrics(r, scenario_id).get(key) is True
    )


def evaluate_scenario(
    scenario_id: str,
    agent_records: list[RunRecordData],
    selective_records: list[RunRecordData],
) -> dict[str, Any]:
    """Compute per-scenario G1/G2/G3 gates (D043)."""
    agent_passes = _passes_count(agent_records, "changed_requirement_pass", scenario_id)
    sel_passes = _passes_count(selective_records, "changed_requirement_pass", scenario_id)

    selective_ge_4_5 = sel_passes >= 4
    agent_not_worse_by_more_than_1 = (agent_passes - sel_passes) <= 1
    g1 = selective_ge_4_5 and agent_not_worse_by_more_than_1

    sel_pres = _passes_count(selective_records, "preservation_pass", scenario_id)
    g2 = sel_pres >= 4

    sel_recall = _passes_count(selective_records, "impact_recall_full", scenario_id)
    g3 = sel_recall >= 4

    return {
        "scenario_id": scenario_id,
        "G1": {
            "selective": g1,
            "selective_ge_4_5": selective_ge_4_5,
            "agent_not_worse_by_more_than_1": agent_not_worse_by_more_than_1,
            "agent": agent_passes >= 4,
            "agent_passes": agent_passes,
            "selective_passes": sel_passes,
        },
        "G2": {
            "selective": g2,
            "preservation_4_5": g2,
            "preservation_pass_count": sel_pres,
        },
        "G3": {
            "selective": g3,
            "recall_4_5": g3,
            "recall_full_count": sel_recall,
        },
    }


def _gate_bool(scenario_result: dict[str, Any], gate_key: str) -> bool:
    value = scenario_result.get(gate_key)
    if isinstance(value, dict):
        return value.get("selective", False) is True
    return value is True


def compute_study_decision(scenario_results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Frozen study-level GO/NO-GO (D043 + preregistration section 4)."""
    scenarios = list(_GOLD_ACTIONS.keys())
    g1_all = all(
        scenario_results[s].get("G1", {}).get("selective") is True for s in scenarios
    )
    g2_all = all(_gate_bool(scenario_results[s], "G2") for s in scenarios)
    g3_count = sum(
        1 for s in scenarios if _gate_bool(scenario_results[s], "G3")
    )
    g3_two_thirds = g3_count >= 2
    go = g1_all and g2_all and g3_two_thirds
    if not go:
        if not g1_all:
            reason = "G1 correctness not cleared in all 3 scenarios; study NO-GO"
        elif not g2_all:
            reason = "G2 preservation not cleared in all 3 scenarios; study NO-GO"
        else:
            reason = (
                "impact recall cleared in fewer than 2/3 scenarios; study NO-GO"
            )
    else:
        reason = "study GO: all 3 clear G1 AND G2 AND at least 2/3 clear G3"
    return {
        "go": go,
        "reason": reason,
        "requirement": STUDY_REQUIREMENT,
        "per_scenario": {
            s: {
                "G1": scenario_results[s].get("G1", {}).get("selective"),
                "G2": _gate_bool(scenario_results[s], "G2"),
                "G3": _gate_bool(scenario_results[s], "G3"),
            }
            for s in scenarios
        },
    }


# --- 30-cell deterministic plan (T7 / dry-run gate) -------------------------

def build_scientific_microstudy_plan(
    scenario_ids: list[str],
    strategy_names: list[str],
    repetitions: int,
    config_hash: str = "",
    protocol_version: str = "1.0",
) -> list[dict[str, Any]]:
    """Immutable pre-generated 30-cell deterministic plan.

    Order is scenario-major, then strategy-major, then repetition ascending —
    an explicit deterministic counterbalancing (documented seed-equivalent).
    Run IDs embed the config identity so different model/provider/backend
    configurations can never share plan cells.
    """
    plan: list[dict[str, Any]] = []
    for scenario_id in scenario_ids:
        for strategy_name in strategy_names:
            for rep in range(1, repetitions + 1):
                run_id = _make_run_id(
                    scenario_id,
                    strategy_name,
                    rep,
                    config_hash=config_hash,
                    protocol_version=protocol_version,
                )
                plan.append(
                    {
                        "run_id": run_id,
                        "scenario_id": scenario_id,
                        "strategy_name": strategy_name,
                        "repetition": rep,
                        "config_hash": config_hash,
                        "protocol_version": protocol_version,
                    }
                )
    return plan


def _make_run_id(
    scenario_id: str,
    strategy_name: str,
    rep: int,
    config_hash: str = "",
    protocol_version: str = "1.0",
) -> str:
    payload = json.dumps(
        {
            "scenario_id": scenario_id,
            "strategy_name": strategy_name,
            "repetition": rep,
            "protocol_version": protocol_version,
            "config_hash": config_hash,
        },
        sort_keys=True,
    )
    suffix = hashlib.sha256(payload.encode()).hexdigest()[:8]
    return f"{scenario_id}_{strategy_name}_rep{rep}_{suffix}"


def plan_hash(plan: list[dict[str, Any]]) -> str:
    """Deterministic hash of the ordered 30-cell plan."""
    ordered = json.dumps([c["run_id"] for c in plan], sort_keys=False)
    return hashlib.sha256(ordered.encode()).hexdigest()


def load_run_records(runs_dir: str | Path) -> list[RunRecordData]:
    from benchmark.checkpoint.persistence import RunRecordStore

    return RunRecordStore(Path(runs_dir)).load_all()


def full_microstudy_results(runs_dir: str | Path) -> dict[str, Any]:
    """Compute the full study table + scenario aggregates + GO/NO-GO."""
    records = load_run_records(runs_dir)
    rows: list[dict[str, Any]] = []
    for record in records:
        if record.scenario_id not in _GOLD_ACTIONS:
            continue
        rows.append(compute_run_metrics(record, record.scenario_id))

    scenario_results: dict[str, dict[str, Any]] = {}
    for scenario_id in _GOLD_ACTIONS:
        agent = [r for r in records if r.scenario_id == scenario_id and r.strategy_id == STRATEGY_AGENT]
        selective = [r for r in records if r.scenario_id == scenario_id and r.strategy_id == STRATEGY_SELECTIVE]
        ev = evaluate_scenario(scenario_id, agent, selective)
        # recall_full uses recall == 1.0 within the evaluate loop
        scenario_results[scenario_id] = ev

    decision = compute_study_decision(scenario_results)
    return {
        "rows": rows,
        "scenario_results": scenario_results,
        "decision": decision,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compute SCIENTIFIC-MICROSTUDY-01 results")
    parser.add_argument("--runs-dir", required=True, help="Directory containing run_records.jsonl")
    args = parser.parse_args()
    result = full_microstudy_results(args.runs_dir)
    print(json.dumps(result, indent=2, default=str))
