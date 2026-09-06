from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"

_SPEC = importlib.util.spec_from_file_location(
    "build_todo_microstudy_results", SCRIPTS_DIR / "build_todo_microstudy_results.py"
)
_MOD = importlib.util.module_from_spec(_SPEC)
sys.modules["build_todo_microstudy_results"] = _MOD
assert _SPEC.loader is not None
_spec = _SPEC
_spec.loader.exec_module(_MOD)

SCENARIOS = ("todo-smoke-001", "todo-smoke-002", "todo-smoke-003")
STRATEGIES = ("iterative_repository_agent", "selective")
REPS = 5


class TestThirtyCellPlan:
    def test_exactly_30_cells(self) -> None:
        plan = _MOD.build_scientific_microstudy_plan(
            scenario_ids=list(SCENARIOS),
            strategy_names=list(STRATEGIES),
            repetitions=REPS,
            config_hash="h" * 16,
            protocol_version="1.0",
        )
        assert len(plan) == 30

    def test_all_run_ids_unique(self) -> None:
        plan = _MOD.build_scientific_microstudy_plan(
            scenario_ids=list(SCENARIOS),
            strategy_names=list(STRATEGIES),
            repetitions=REPS,
            config_hash="h" * 16,
            protocol_version="1.0",
        )
        ids = [cell["run_id"] for cell in plan]
        assert len(ids) == len(set(ids))

    def test_strategy_balance_15_and_15(self) -> None:
        plan = _MOD.build_scientific_microstudy_plan(
            scenario_ids=list(SCENARIOS),
            strategy_names=list(STRATEGIES),
            repetitions=REPS,
            config_hash="h" * 16,
            protocol_version="1.0",
        )
        counts = {s: sum(1 for c in plan if c["strategy_name"] == s) for s in STRATEGIES}
        assert counts["iterative_repository_agent"] == 15
        assert counts["selective"] == 15

    def test_scenario_balance_10_each(self) -> None:
        plan = _MOD.build_scientific_microstudy_plan(
            scenario_ids=list(SCENARIOS),
            strategy_names=list(STRATEGIES),
            repetitions=REPS,
            config_hash="h" * 16,
            protocol_version="1.0",
        )
        counts = {s: sum(1 for c in plan if c["scenario_id"] == s) for s in SCENARIOS}
        assert counts == {"todo-smoke-001": 10, "todo-smoke-002": 10, "todo-smoke-003": 10}

    def test_rep_balance_6_each(self) -> None:
        plan = _MOD.build_scientific_microstudy_plan(
            scenario_ids=list(SCENARIOS),
            strategy_names=list(STRATEGIES),
            repetitions=REPS,
            config_hash="h" * 16,
            protocol_version="1.0",
        )
        counts = {}
        for cell in plan:
            counts[cell["repetition"]] = counts.get(cell["repetition"], 0) + 1
        assert counts == {1: 6, 2: 6, 3: 6, 4: 6, 5: 6}

    def test_deterministic_order_and_hash(self) -> None:
        a = _MOD.build_scientific_microstudy_plan(
            scenario_ids=list(SCENARIOS),
            strategy_names=list(STRATEGIES),
            repetitions=REPS,
            config_hash="h" * 16,
            protocol_version="1.0",
        )
        b = _MOD.build_scientific_microstudy_plan(
            scenario_ids=list(SCENARIOS),
            strategy_names=list(STRATEGIES),
            repetitions=REPS,
            config_hash="h" * 16,
            protocol_version="1.0",
        )
        assert [c["run_id"] for c in a] == [c["run_id"] for c in b]
        assert _MOD.plan_hash(a) == _MOD.plan_hash(b)

    def test_plan_hash_changes_when_config_hash_changes(self) -> None:
        a = _MOD.build_scientific_microstudy_plan(
            scenario_ids=list(SCENARIOS),
            strategy_names=list(STRATEGIES),
            repetitions=REPS,
            config_hash="aaaa" * 4,
            protocol_version="1.0",
        )
        b = _MOD.build_scientific_microstudy_plan(
            scenario_ids=list(SCENARIOS),
            strategy_names=list(STRATEGIES),
            repetitions=REPS,
            config_hash="bbbb" * 4,
            protocol_version="1.0",
        )
        assert _MOD.plan_hash(a) != _MOD.plan_hash(b)

    def test_every_run_id_includes_config_identity(self) -> None:
        plan = _MOD.build_scientific_microstudy_plan(
            scenario_ids=list(SCENARIOS),
            strategy_names=list(STRATEGIES),
            repetitions=REPS,
            config_hash="AAAA" * 4,
            protocol_version="1.0",
        )
        for cell in plan:
            assert cell["config_hash"] == "AAAA" * 4
            assert cell["protocol_version"] == "1.0"

    def test_plan_sorted_scenario_major(self) -> None:
        plan = _MOD.build_scientific_microstudy_plan(
            scenario_ids=list(SCENARIOS),
            strategy_names=list(STRATEGIES),
            repetitions=REPS,
            config_hash="h" * 16,
            protocol_version="1.0",
        )
        orders = [c["scenario_id"] for c in plan]
        assert orders[:10] == ["todo-smoke-001"] * 10
        assert orders[10:20] == ["todo-smoke-002"] * 10
        assert orders[20:30] == ["todo-smoke-003"] * 10
