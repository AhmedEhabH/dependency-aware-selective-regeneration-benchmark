from __future__ import annotations

from benchmark.core.exceptions import ScenarioError
from benchmark.core.models import Scenario


class ScenarioValidator:
    def validate(self, scenario: Scenario) -> list[str]:
        errors: list[str] = []

        if not scenario.scenario_id:
            errors.append("scenario_id must not be empty")
        if not scenario.repository:
            errors.append("repository must not be empty")
        if not scenario.change_type:
            errors.append("change_type must not be empty")
        if not scenario.requirement_before:
            errors.append("requirement_before must not be empty")
        if not scenario.requirement_after:
            errors.append("requirement_after must not be empty")
        if not scenario.rationale:
            errors.append("rationale must not be empty")

        if scenario.expected_affected_artifacts:
            for ref in scenario.expected_affected_artifacts:
                if not ref.path:
                    errors.append(f"Expected affected artifact has empty path: {ref}")
                if not ref.artifact_type:
                    errors.append(f"Expected affected artifact has empty type: {ref}")

        seen_actions: set[str] = set()
        for ref, action in scenario.expected_actions:
            if not ref.path:
                errors.append(f"Expected action artifact has empty path: {ref}")
            key = f"{ref.path}:{action}"
            if key in seen_actions:
                errors.append(f"Duplicate expected action: {key}")
            seen_actions.add(key)

        if not errors:
            return errors

        raise ScenarioError(
            f"Scenario validation failed for '{scenario.scenario_id}'",
            context={"errors": errors},
        )

    def validate_all(self, scenarios: list[Scenario]) -> list[tuple[str, list[str]]]:
        all_errors: list[tuple[str, list[str]]] = []
        for scenario in scenarios:
            try:
                self.validate(scenario)
            except ScenarioError as e:
                ctx = e.context or {}
                all_errors.append((scenario.scenario_id, ctx.get("errors", [str(e)])))
        return all_errors
