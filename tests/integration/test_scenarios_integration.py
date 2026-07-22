from pathlib import Path

import pytest

from benchmark.scenarios.loader import ScenarioLoader


@pytest.mark.skipif(
    not Path("benchmark_data/scenarios").is_dir(),
    reason="benchmark_data/scenarios not available in test environment",
)
class TestRealScenarioLoading:
    def test_load_all_real_scenarios(self) -> None:
        loader = ScenarioLoader(Path("benchmark_data/scenarios"))
        scenarios = loader.load_all()
        assert len(scenarios) >= 1
        scenario_ids = [s.scenario_id for s in scenarios]
        assert "todo-loc-001" in scenario_ids

    def test_all_scenarios_valid(self) -> None:
        loader = ScenarioLoader(Path("benchmark_data/scenarios"))
        scenarios = loader.load_all()

        from benchmark.scenarios.validator import ScenarioValidator
        validator = ScenarioValidator()
        errors = validator.validate_all(scenarios)
        assert len(errors) == 0, f"Validation errors: {errors}"

    def test_scenarios_have_required_fields(self) -> None:
        loader = ScenarioLoader(Path("benchmark_data/scenarios"))
        scenarios = loader.load_all()
        for s in scenarios:
            assert s.scenario_id, f"Missing scenario_id in {s}"
            assert s.repository, f"Missing repository in {s.scenario_id}"
            assert s.requirement_before, f"Missing requirement_before in {s.scenario_id}"
            assert s.requirement_after, f"Missing requirement_after in {s.scenario_id}"
            assert s.rationale, f"Missing rationale in {s.scenario_id}"

    def test_scenario_ids_match_pattern(self) -> None:
        loader = ScenarioLoader(Path("benchmark_data/scenarios"))
        scenarios = loader.load_all()
        for s in scenarios:
            parts = s.scenario_id.split("-")
            assert len(parts) == 3, f"Unexpected scenario_id format: {s.scenario_id}"
            assert parts[0] in ("todo", "djangocms", "saleor")
            assert parts[1] in ("loc", "mod", "cross")
            assert parts[2].isdigit()

    def test_blast_radius_distribution(self) -> None:
        loader = ScenarioLoader(Path("benchmark_data/scenarios"))
        scenarios = loader.load_all()
        from benchmark.core.enums import BlastRadius
        counts = {br: 0 for br in BlastRadius}
        for s in scenarios:
            counts[s.blast_radius] += 1
        assert counts[BlastRadius.localized] >= 1
        assert counts[BlastRadius.moderate] >= 1
        assert counts[BlastRadius.cross_cutting] >= 1
