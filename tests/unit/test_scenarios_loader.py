from pathlib import Path

import pytest
import yaml

from benchmark.core.exceptions import ScenarioError
from benchmark.scenarios.loader import ScenarioLoader

SAMPLE_SCENARIO_YAML = {
    "scenario_id": "todo-loc-001",
    "repository": "todo",
    "change_type": "Schema and field changes",
    "blast_radius": "localized",
    "requirement_before": "Old behavior description",
    "requirement_after": "New behavior description",
    "rationale": "Test rationale",
    "acceptance_criteria": [
        "Task model has a priority field",
        "TaskSerializer.priority is a read-write ChoiceField",
    ],
    "expected_affected_artifacts": [
        "todo/models.py:Task (add priority field)",
        "todo/serializers.py:TaskSerializer (add priority field)",
    ],
    "expected_actions": {
        "todo/models.py:Task": "modify",
        "todo/serializers.py:TaskSerializer": "modify",
    },
    "regression_obligations": [
        "todo/tests/test_models.py",
        "todo/tests/test_serializers.py",
    ],
    "architecture_constraints": [
        "No changes to views.py, urls.py, permissions.py",
    ],
    "hidden_tests": [
        {"description": "Regression test", "type": "regression"},
    ],
}


class TestScenarioLoader:
    def test_init(self, tmp_path: Path) -> None:
        loader = ScenarioLoader(tmp_path)
        assert loader is not None

    def test_load_scenario(self, tmp_path: Path) -> None:
        scenario_file = tmp_path / "test_scenario.yaml"
        scenario_file.write_text(yaml.dump(SAMPLE_SCENARIO_YAML), encoding="utf-8")

        loader = ScenarioLoader(tmp_path)
        scenario = loader.load_scenario(scenario_file)
        assert scenario.scenario_id == "todo-loc-001"
        assert scenario.repository == "todo"
        assert len(scenario.acceptance_criteria) == 2
        assert len(scenario.expected_affected_artifacts) == 2
        assert len(scenario.expected_actions) == 2

    def test_load_nonexistent_file_raises(self, tmp_path: Path) -> None:
        loader = ScenarioLoader(tmp_path)
        with pytest.raises(ScenarioError, match="not found"):
            loader.load_scenario(tmp_path / "nonexistent.yaml")

    def test_load_invalid_yaml_raises(self, tmp_path: Path) -> None:
        f = tmp_path / "bad.yaml"
        f.write_text(": broken yaml [", encoding="utf-8")
        loader = ScenarioLoader(tmp_path)
        with pytest.raises(ScenarioError, match="Failed to parse"):
            loader.load_scenario(f)

    def test_load_scalar_yaml_raises(self, tmp_path: Path) -> None:
        f = tmp_path / "scalar.yaml"
        f.write_text("just a string", encoding="utf-8")
        loader = ScenarioLoader(tmp_path)
        with pytest.raises(ScenarioError, match="must be a mapping"):
            loader.load_scenario(f)

    def test_load_all(self, tmp_path: Path) -> None:
        for i in range(3):
            data = dict(SAMPLE_SCENARIO_YAML)
            data["scenario_id"] = f"test-{i:03d}"
            if i == 1:
                data["repository"] = "other"
            (tmp_path / f"scenario_{i:03d}.yaml").write_text(
                yaml.dump(data), encoding="utf-8"
            )

        loader = ScenarioLoader(tmp_path)
        scenarios = loader.load_all()
        assert len(scenarios) == 3
        ids = [s.scenario_id for s in scenarios]
        assert "test-000" in ids
        assert "test-001" in ids
        assert "test-002" in ids

    def test_load_all_no_scenarios_raises(self, tmp_path: Path) -> None:
        loader = ScenarioLoader(tmp_path)
        with pytest.raises(ScenarioError, match="No scenario files found"):
            loader.load_all()

    def test_load_by_repository(self, tmp_path: Path) -> None:
        for i in range(4):
            data = dict(SAMPLE_SCENARIO_YAML)
            data["scenario_id"] = f"test-{i:03d}"
            data["repository"] = "todo" if i < 2 else "djangocms"
            (tmp_path / f"scenario_{i:03d}.yaml").write_text(
                yaml.dump(data), encoding="utf-8"
            )

        loader = ScenarioLoader(tmp_path)
        todo_scenarios = loader.load_by_repository("todo")
        assert len(todo_scenarios) == 2
        djangocms_scenarios = loader.load_by_repository("djangocms")
        assert len(djangocms_scenarios) == 2

    def test_load_24_scenarios_repo_distribution(self) -> None:
        from collections import Counter
        from pathlib import Path

        test_dir = Path(__file__).resolve().parent.parent.parent
        scenarios_dir = test_dir / "benchmark_data" / "scenarios"
        if not scenarios_dir.is_dir():
            pytest.skip("benchmark_data/scenarios directory not found")

        loader = ScenarioLoader(scenarios_dir)
        scenarios = loader.load_all()
        assert len(scenarios) == 27, (
            f"Expected 27 scenarios, loaded {len(scenarios)}. "
            "Run with --log-cli-level=INFO to see which files were skipped."
        )
        repo_counts = Counter(s.repository for s in scenarios)
        assert repo_counts["todo"] == 11, (
            f"Repository 'todo' has {repo_counts['todo']} scenarios, expected 11. "

        )
        for repo in ("djangocms", "saleor"):
            assert repo_counts[repo] == 8, (
                f"Repository '{repo}' has {repo_counts[repo]} scenarios, expected 8. "
                f"Full distribution: {dict(repo_counts)}"
            )

    def test_load_scenario_with_smoke_fields(self, tmp_path: Path) -> None:
        data = dict(SAMPLE_SCENARIO_YAML)
        data["scenario_id"] = "todo-smoke-001"
        data["evaluator_asset"] = "tests/evaluator_assets/todo_smoke_001_checks.py"
        data["post_generation_command"] = [
            "python", "manage.py", "makemigrations", "todo", "--noinput",
        ]
        data["require_new_migration"] = True
        scenario_file = tmp_path / "smoke.yaml"
        scenario_file.write_text(yaml.dump(data), encoding="utf-8")

        loader = ScenarioLoader(tmp_path)
        scenario = loader.load_scenario(scenario_file)
        assert scenario.evaluator_asset == "tests/evaluator_assets/todo_smoke_001_checks.py"
        assert scenario.post_generation_command == (
            "python", "manage.py", "makemigrations", "todo", "--noinput",
        )
        assert scenario.require_new_migration is True

    def test_load_non_smoke_defaults(self, tmp_path: Path) -> None:
        scenario_file = tmp_path / "non_smoke.yaml"
        scenario_file.write_text(yaml.dump(SAMPLE_SCENARIO_YAML), encoding="utf-8")

        loader = ScenarioLoader(tmp_path)
        scenario = loader.load_scenario(scenario_file)
        assert scenario.evaluator_asset == ""
        assert scenario.post_generation_command == ()
        assert scenario.require_new_migration is False

    def test_load_all_logs_warnings_on_partial_failure(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        import logging
        caplog.set_level(logging.WARNING)

        data_ok = dict(SAMPLE_SCENARIO_YAML)
        data_ok["scenario_id"] = "ok-001"
        (tmp_path / "ok.yaml").write_text(yaml.dump(data_ok), encoding="utf-8")

        (tmp_path / "bad.yaml").write_text(": broken yaml [", encoding="utf-8")

        loader = ScenarioLoader(tmp_path)
        scenarios = loader.load_all()
        assert len(scenarios) == 1
        assert any("bad.yaml" in rec.message for rec in caplog.records)

    def test_load_all_logs_each_skipped_file(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        import logging
        caplog.set_level(logging.WARNING)

        (tmp_path / "a.yaml").write_text("scalar\n", encoding="utf-8")
        (tmp_path / "b.yaml").write_text("scalar\n", encoding="utf-8")

        loader = ScenarioLoader(tmp_path)
        with pytest.raises(ScenarioError, match="Failed to load any"):
            loader.load_all()

        warning_messages = [rec.message for rec in caplog.records]
        assert any("a.yaml" in m for m in warning_messages)
        assert any("b.yaml" in m for m in warning_messages)

    def test_migration_directory_parsed_from_yaml(self, tmp_path: Path) -> None:
        data = dict(SAMPLE_SCENARIO_YAML)
        data["migration_directory"] = "saleor/saleor/migrations"
        data["post_generation_command"] = ["python", "manage.py", "makemigrations", "saleor"]
        data["require_new_migration"] = True
        scenario_file = tmp_path / "mig.yaml"
        scenario_file.write_text(yaml.dump(data), encoding="utf-8")

        scenario = ScenarioLoader(tmp_path).load_scenario(scenario_file)
        assert scenario.migration_directory == "saleor/saleor/migrations"
        assert scenario.post_generation_command == (
            "python", "manage.py", "makemigrations", "saleor",
        )
        assert scenario.require_new_migration is True

    def test_migration_directory_default_is_todo(self, tmp_path: Path) -> None:
        scenario_file = tmp_path / "default.yaml"
        scenario_file.write_text(yaml.dump(SAMPLE_SCENARIO_YAML), encoding="utf-8")

        scenario = ScenarioLoader(tmp_path).load_scenario(scenario_file)
        assert scenario.migration_directory == "todo/migrations"

    def test_absolute_migration_directory_rejected(self, tmp_path: Path) -> None:
        data = dict(SAMPLE_SCENARIO_YAML)
        data["migration_directory"] = "/todo/migrations"
        scenario_file = tmp_path / "bad_mig.yaml"
        scenario_file.write_text(yaml.dump(data), encoding="utf-8")

        with pytest.raises(ScenarioError, match="migration_directory"):
            ScenarioLoader(tmp_path).load_scenario(scenario_file)
class TestCanaryMigrationMetadata:
    """D13r1 F2/F3: repository-aware migration metadata on the 3 canary
    scenarios ONLY.

    F2 adds the per-repository migration directory to exactly the three canary
    scenarios (todo-loc-001, saleor-loc-001, djangocms-cross-007) so the real
    pilot-canary runs the migration stage repository-aware. Every OTHER
    scenario keeps the frozen default ("todo/migrations") - migration metadata
    must NOT leak into the other nine Pilot scenarios or any non-Pilot scenario.
    """

    CANARY_EXPECTED = {
        "todo-loc-001": "todo/migrations",
        "saleor-loc-001": "saleor/product/migrations",
        "djangocms-cross-007": "cms/migrations",
    }

    def test_canary_scenarios_carry_per_repo_migration_directory(self) -> None:
        scenarios_dir = (
            Path(__file__).resolve().parent.parent.parent
            / "benchmark_data" / "scenarios"
        )
        if not scenarios_dir.is_dir():
            pytest.skip("benchmark_data/scenarios directory not found")
        scenarios = {s.scenario_id: s for s in ScenarioLoader(scenarios_dir).load_all()}
        for scenario_id, expected in self.CANARY_EXPECTED.items():
            assert scenarios[scenario_id].migration_directory == expected, (
                f"{scenario_id} migration_directory="
                f"{scenarios[scenario_id].migration_directory!r} (expected {expected!r})"
            )

    def test_migration_directory_added_only_to_three_canary_scenarios(self) -> None:
        scenarios_dir = (
            Path(__file__).resolve().parent.parent.parent
            / "benchmark_data" / "scenarios"
        )
        if not scenarios_dir.is_dir():
            pytest.skip("benchmark_data/scenarios directory not found")
        declared = set()
        for scenario_file in sorted(scenarios_dir.glob("*.yaml")):
            data = yaml.safe_load(scenario_file.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "migration_directory" in data:
                declared.add(str(data.get("scenario_id", "")))
        assert declared == set(self.CANARY_EXPECTED), (
            f"migration_directory explicitly declared on {sorted(declared)}; "
            f"expected exactly {sorted(self.CANARY_EXPECTED)}"
        )
