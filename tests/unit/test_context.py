import pytest

from benchmark.core.context import ExecutionContext
from benchmark.core.enums import EvidenceTier
from benchmark.core.models import Budget, RepositoryIdentity


class TestExecutionContext:
    def test_valid_creation(self) -> None:
        ctx = ExecutionContext(
            protocol_version="1.0",
            run_id="run-001",
            repository_identity=RepositoryIdentity(name="todo", url="https://example.com/repo"),
            scenario_id="scenario-1",
            strategy_name="hybrid",
            backend_name="mock",
            working_directory="/tmp/work",
            public_data_paths=("/data/public",),
        )
        assert ctx.protocol_version == "1.0"
        assert ctx.run_id == "run-001"
        assert ctx.scenario_id == "scenario-1"
        assert ctx.strategy_name == "hybrid"
        assert ctx.backend_name == "mock"
        assert ctx.private_evaluation_access is False
        assert ctx.publication_eligible is False
        assert ctx.evidence_tier == EvidenceTier.engineering_validation

    def test_empty_protocol_version_raises(self) -> None:
        with pytest.raises(ValueError, match="ExecutionContext.protocol_version"):
            ExecutionContext(
                protocol_version="",
                run_id="r1",
                repository_identity=RepositoryIdentity(name="r", url="https://r.com"),
                scenario_id="s1",
                strategy_name="st",
                backend_name="be",
                working_directory="/tmp",
                public_data_paths=(),
            )

    def test_empty_run_id_raises(self) -> None:
        with pytest.raises(ValueError, match="ExecutionContext.run_id"):
            ExecutionContext(
                protocol_version="1.0",
                run_id="",
                repository_identity=RepositoryIdentity(name="r", url="https://r.com"),
                scenario_id="s1",
                strategy_name="st",
                backend_name="be",
                working_directory="/tmp",
                public_data_paths=(),
            )

    def test_default_budget(self) -> None:
        ctx = ExecutionContext(
            protocol_version="1.0",
            run_id="r1",
            repository_identity=RepositoryIdentity(name="r", url="https://r.com"),
            scenario_id="s1",
            strategy_name="st",
            backend_name="be",
            working_directory="/tmp",
            public_data_paths=(),
        )
        assert isinstance(ctx.budget, Budget)
        assert ctx.budget.max_iterations == 3

    def test_private_access_default_false(self) -> None:
        ctx = ExecutionContext(
            protocol_version="1.0",
            run_id="r1",
            repository_identity=RepositoryIdentity(name="r", url="https://r.com"),
            scenario_id="s1",
            strategy_name="st",
            backend_name="be",
            working_directory="/tmp",
            public_data_paths=(),
        )
        assert ctx.private_evaluation_access is False

    def test_update_budget(self) -> None:
        ctx = ExecutionContext(
            protocol_version="1.0",
            run_id="r1",
            repository_identity=RepositoryIdentity(name="r", url="https://r.com"),
            scenario_id="s1",
            strategy_name="st",
            backend_name="be",
            working_directory="/tmp",
            public_data_paths=(),
        )
        new_budget = Budget(max_iterations=5)
        ctx.update_budget(new_budget)
        assert ctx.budget.max_iterations == 5

    def test_update_random_seed(self) -> None:
        ctx = ExecutionContext(
            protocol_version="1.0",
            run_id="r1",
            repository_identity=RepositoryIdentity(name="r", url="https://r.com"),
            scenario_id="s1",
            strategy_name="st",
            backend_name="be",
            working_directory="/tmp",
            public_data_paths=(),
        )
        ctx.update_random_seed(42)
        assert ctx.random_seed == 42

    def test_cannot_mutate_protected_fields(self) -> None:
        ctx = ExecutionContext(
            protocol_version="1.0",
            run_id="r1",
            repository_identity=RepositoryIdentity(name="r", url="https://r.com"),
            scenario_id="s1",
            strategy_name="st",
            backend_name="be",
            working_directory="/tmp",
            public_data_paths=(),
        )
        with pytest.raises(AttributeError, match="cannot assign to field"):
            ctx.protocol_version = "2.0"  # type: ignore[misc]

    def test_cannot_enable_private_access(self) -> None:
        ctx = ExecutionContext(
            protocol_version="1.0",
            run_id="r1",
            repository_identity=RepositoryIdentity(name="r", url="https://r.com"),
            scenario_id="s1",
            strategy_name="st",
            backend_name="be",
            working_directory="/tmp",
            public_data_paths=(),
        )
        with pytest.raises(AttributeError, match="cannot assign to field"):
            ctx.private_evaluation_access = True  # type: ignore[misc]
