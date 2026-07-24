from __future__ import annotations

from benchmark.core.models import Scenario, ScenarioSequence

_BLAST_RADIUS_ORDER: dict[str, int] = {
    "localized": 0,
    "moderate": 1,
    "cross_cutting": 2,
}


class ScenarioSequencer:
    def sequence(self, scenarios: list[Scenario]) -> ScenarioSequence:
        sorted_scenarios = sorted(
            scenarios,
            key=lambda s: (
                _BLAST_RADIUS_ORDER.get(str(s.blast_radius), 99),
                s.scenario_id,
            ),
        )
        return ScenarioSequence(scenarios=tuple(sorted_scenarios))

    def sequence_by_repository(
        self, scenarios: list[Scenario]
    ) -> dict[str, ScenarioSequence]:
        by_repo: dict[str, list[Scenario]] = {}
        for s in scenarios:
            by_repo.setdefault(s.repository, []).append(s)
        return {
            repo_id: self.sequence(repo_scenarios)
            for repo_id, repo_scenarios in sorted(by_repo.items())
        }
