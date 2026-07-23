from __future__ import annotations

import logging
from pathlib import Path

import yaml

from benchmark.core.exceptions import ScenarioError
from benchmark.core.models import Scenario
from benchmark.scenarios.models import ScenarioModel

logger = logging.getLogger("benchmark.scenarios.loader")


class ScenarioLoader:
    def __init__(self, scenarios_dir: str | Path) -> None:
        self._scenarios_dir = Path(scenarios_dir)

    def load_scenario(self, path: str | Path) -> Scenario:
        path = Path(path)
        if not path.exists():
            raise ScenarioError(f"Scenario file not found: {path}", context={"path": str(path)})
        if not path.is_file():
            raise ScenarioError(f"Scenario path is not a file: {path}", context={"path": str(path)})

        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as e:
            raise ScenarioError(
                f"Failed to read scenario file: {e}", context={"path": str(path)}
            ) from e

        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as e:
            raise ScenarioError(
                f"Failed to parse scenario YAML: {e}", context={"path": str(path)}
            ) from e

        if not isinstance(data, dict):
            raise ScenarioError(
                f"Scenario YAML must be a mapping, got {type(data).__name__}",
                context={"path": str(path)},
            )

        try:
            model = ScenarioModel.from_yaml_mapping(data)
        except (ValueError, TypeError) as e:
            raise ScenarioError(
                f"Failed to build ScenarioModel: {e}", context={"path": str(path)}
            ) from e

        return model.to_core_scenario()

    def load_all(self, pattern: str = "*.yaml") -> list[Scenario]:
        if not self._scenarios_dir.is_dir():
            raise ScenarioError(
                f"Scenarios directory not found: {self._scenarios_dir}",
                context={"path": str(self._scenarios_dir)},
            )

        scenario_files = sorted(self._scenarios_dir.glob(pattern))

        if not scenario_files:
            raise ScenarioError(
                f"No scenario files found matching '{pattern}' in {self._scenarios_dir}",
                context={"path": str(self._scenarios_dir), "pattern": pattern},
            )

        results: list[Scenario] = []
        errors: list[str] = []

        for scenario_file in scenario_files:
            try:
                scenario = self.load_scenario(scenario_file)
                results.append(scenario)
            except ScenarioError as e:
                msg = f"Skipping {scenario_file.name}: {e}"
                logger.warning(msg)
                errors.append(msg)

        if errors and not results:
            raise ScenarioError(
                f"Failed to load any scenario from {self._scenarios_dir}",
                context={"errors": errors},
            )

        if errors:
            logger.info(
                "Loaded %d / %d scenario files (%d skipped)",
                len(results), len(scenario_files), len(errors),
            )

        return results

    def load_by_repository(self, repo_id: str) -> list[Scenario]:
        all_scenarios = self.load_all()
        return [s for s in all_scenarios if s.repository == repo_id]
