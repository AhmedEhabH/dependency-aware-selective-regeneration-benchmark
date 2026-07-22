
from benchmark.core.exceptions import (
    BenchmarkError,
    BudgetExceededError,
    ConfigurationError,
    DuplicateRegistrationError,
    ModelBackendError,
    ProtocolViolationError,
    RegistryError,
    RepositoryError,
    ScenarioError,
    SerializationError,
    UnknownRegistrationError,
    ValidationError,
)


class TestExceptionHierarchy:
    def test_benchmark_error_base(self) -> None:
        err = BenchmarkError("base error")
        assert isinstance(err, Exception)
        assert str(err) == "base error"

    def test_configuration_error_subclass(self) -> None:
        err = ConfigurationError("bad config")
        assert isinstance(err, BenchmarkError)

    def test_validation_error_subclass(self) -> None:
        err = ValidationError("invalid")
        assert isinstance(err, BenchmarkError)

    def test_registry_error_subclass(self) -> None:
        err = RegistryError("registry issue")
        assert isinstance(err, BenchmarkError)

    def test_duplicate_registration_error_subclass(self) -> None:
        err = DuplicateRegistrationError("dup")
        assert isinstance(err, RegistryError)
        assert isinstance(err, BenchmarkError)

    def test_unknown_registration_error_subclass(self) -> None:
        err = UnknownRegistrationError("unknown")
        assert isinstance(err, RegistryError)
        assert isinstance(err, BenchmarkError)

    def test_repository_error_subclass(self) -> None:
        err = RepositoryError("repo issue")
        assert isinstance(err, BenchmarkError)

    def test_scenario_error_subclass(self) -> None:
        err = ScenarioError("scenario issue")
        assert isinstance(err, BenchmarkError)

    def test_model_backend_error_subclass(self) -> None:
        err = ModelBackendError("backend issue")
        assert isinstance(err, BenchmarkError)

    def test_budget_exceeded_error_subclass(self) -> None:
        err = BudgetExceededError("budget exceeded")
        assert isinstance(err, BenchmarkError)

    def test_protocol_violation_error_subclass(self) -> None:
        err = ProtocolViolationError("protocol violation")
        assert isinstance(err, BenchmarkError)

    def test_serialization_error_subclass(self) -> None:
        err = SerializationError("serialization issue")
        assert isinstance(err, BenchmarkError)


class TestExceptionContext:
    def test_context_is_preserved(self) -> None:
        err = ConfigurationError("bad config", context={"key": "value"})
        assert err.context == {"key": "value"}

    def test_default_context_is_empty(self) -> None:
        err = BenchmarkError("no context")
        assert err.context == {}

    def test_repr_includes_context(self) -> None:
        err = ValidationError("invalid", context={"field": "name"})
        rep = repr(err)
        assert "ValidationError" in rep
        assert "invalid" in rep
