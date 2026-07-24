from typing import Any


class BenchmarkError(Exception):
    def __init__(self, message: str, *, context: dict[str, Any] | None = None) -> None:
        self.message = message
        self.context = context or {}
        super().__init__(message)

    def __repr__(self) -> str:
        ctx = f" context={self.context}" if self.context else ""
        return f"{self.__class__.__name__}('{self.message}'{ctx})"


class ConfigurationError(BenchmarkError):
    pass


class ValidationError(BenchmarkError):
    pass


class RegistryError(BenchmarkError):
    pass


class DuplicateRegistrationError(RegistryError):
    pass


class UnknownRegistrationError(RegistryError):
    pass


class RepositoryError(BenchmarkError):
    pass


class ScenarioError(BenchmarkError):
    pass


class ModelBackendError(BenchmarkError):
    pass


class BudgetExceededError(BenchmarkError):
    pass


class ProtocolViolationError(BenchmarkError):
    pass


class SerializationError(BenchmarkError):
    pass
