from __future__ import annotations

import pytest

from benchmark.core.exceptions import UnknownRegistrationError
from benchmark.llm import BackendFactory, DryRunLLMBackend, MockLLMBackend, OpenRouterBackend
from benchmark.llm.kaggle_qwen_backend import KaggleQwenBackend
from seven_arm_benchmark import make_backend


class TestBackendFactory:
    def test_register_and_create_mock(self) -> None:
        factory = BackendFactory()
        factory.register("mock", MockLLMBackend)
        backend = factory.create("mock")
        assert isinstance(backend, MockLLMBackend)

    def test_register_and_create_dry_run(self) -> None:
        factory = BackendFactory()
        factory.register("dry_run", DryRunLLMBackend)
        backend = factory.create("dry_run")
        assert isinstance(backend, DryRunLLMBackend)

    def test_register_and_create_kaggle_qwen(self) -> None:
        factory = BackendFactory()
        factory.register("kaggle_qwen", KaggleQwenBackend)
        backend = factory.create("kaggle_qwen")
        assert isinstance(backend, KaggleQwenBackend)

    def test_register_and_create_openrouter(self) -> None:
        factory = BackendFactory()
        factory.register("openrouter", OpenRouterBackend)
        backend = factory.create("openrouter", model="test-model")
        assert isinstance(backend, OpenRouterBackend)

    def test_create_unknown_raises(self) -> None:
        factory = BackendFactory()
        with pytest.raises(UnknownRegistrationError, match="unknown_backend"):
            factory.create("unknown_backend")

    def test_list_names(self) -> None:
        factory = BackendFactory()
        factory.register("mock", MockLLMBackend)
        factory.register("dry_run", DryRunLLMBackend)
        names = factory.list_names()
        assert "mock" in names
        assert "dry_run" in names

    def test_freeze_prevents_registration(self) -> None:
        factory = BackendFactory()
        factory.register("mock", MockLLMBackend)
        factory.freeze()
        assert factory.is_frozen
        with pytest.raises(RuntimeError, match="frozen"):
            factory.register("another", MockLLMBackend)

    def test_contains(self) -> None:
        factory = BackendFactory()
        factory.register("mock", MockLLMBackend)
        assert "mock" in factory
        assert "nonexistent" not in factory

    def test_len(self) -> None:
        factory = BackendFactory()
        assert len(factory) == 0
        factory.register("mock", MockLLMBackend)
        assert len(factory) == 1


class TestMakeBackend:
    def test_explicit_mock_no_dry_run(self) -> None:
        backend = make_backend(dry_run=False, backend_name="mock")
        assert isinstance(backend, MockLLMBackend)
        assert not isinstance(backend, KaggleQwenBackend)

    def test_explicit_mock_dry_run(self) -> None:
        backend = make_backend(dry_run=True, backend_name="mock")
        assert isinstance(backend, MockLLMBackend)

    def test_dry_run_no_backend(self) -> None:
        backend = make_backend(dry_run=True, backend_name=None)
        assert isinstance(backend, MockLLMBackend)

    def test_default_non_dry_run(self) -> None:
        backend = make_backend(dry_run=False, backend_name=None)
        assert isinstance(backend, KaggleQwenBackend)
        assert not isinstance(backend, MockLLMBackend)
