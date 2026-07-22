import pytest
import yaml

from benchmark.config.models import (
    BackendConfig,
    BenchmarkConfig,
    ExecutionConfig,
    OutputConfig,
    RepositoryConfig,
    StrategyConfig,
)
from benchmark.core.enums import EvidenceTier


class TestStrategyConfig:
    def test_valid(self) -> None:
        sc = StrategyConfig(name="hybrid", llm_backend="qwen")
        assert sc.name == "hybrid"
        assert sc.llm_backend == "qwen"

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError):
            StrategyConfig(name="")


class TestBackendConfig:
    def test_mock_backend(self) -> None:
        bc = BackendConfig(name="mock1", kind="mock")
        assert bc.kind == "mock"

    def test_kaggle_qwen_kind(self) -> None:
        bc = BackendConfig(name="qwen", kind="kaggle_qwen")
        assert bc.kind == "kaggle_qwen"

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError):
            BackendConfig(name="", kind="mock")


class TestRepositoryConfig:
    def test_valid(self) -> None:
        rc = RepositoryConfig(name="todo", url="https://example.com/repo", ref="main")
        assert rc.name == "todo"


class TestExecutionConfig:
    def test_valid(self) -> None:
        ec = ExecutionConfig(max_iterations=5, random_seed=42)
        assert ec.max_iterations == 5
        assert ec.random_seed == 42

    def test_negative_iterations_raises(self) -> None:
        with pytest.raises(ValueError):
            ExecutionConfig(max_iterations=0)

    def test_negative_timeout_raises(self) -> None:
        with pytest.raises(ValueError):
            ExecutionConfig(timeout_seconds=-1)


class TestOutputConfig:
    def test_defaults(self) -> None:
        oc = OutputConfig()
        assert oc.output_dir == "runs"
        assert oc.format == "jsonl"


class TestBenchmarkConfig:
    def test_minimal_config(self) -> None:
        config = BenchmarkConfig()
        assert config.protocol_version == "1.0"
        assert config.execution_mode == "local"
        assert config.strategies == []
        assert config.backends == []

    def test_yaml_roundtrip(self) -> None:
        raw = {
            "protocol_version": "1.0",
            "execution_mode": "local",
            "strategies": [{"name": "hybrid", "llm_backend": "mock1"}],
            "backends": [{"name": "mock1", "kind": "mock"}],
            "repositories": [{"name": "todo", "url": "https://example.com/repo"}],
            "execution": {"max_iterations": 3, "evidence_tier": "pilot"},
        }
        yaml_str = yaml.dump(raw)
        loaded_data = yaml.safe_load(yaml_str)
        config = BenchmarkConfig(**loaded_data)
        assert config.protocol_version == "1.0"
        assert len(config.strategies) == 1
        assert config.strategies[0].name == "hybrid"
        assert config.execution.evidence_tier == EvidenceTier.pilot

    def test_reject_kaggle_backend_in_local_mode(self) -> None:
        with pytest.raises(ValueError, match="cannot be used in local execution mode"):
            BenchmarkConfig(
                execution_mode="local",
                backends=[BackendConfig(name="qwen", kind="kaggle_qwen")],
            )

    def test_accept_kaggle_backend_in_kaggle_mode(self) -> None:
        config = BenchmarkConfig(
            execution_mode="kaggle",
            backends=[BackendConfig(name="qwen", kind="kaggle_qwen")],
        )
        assert len(config.backends) == 1
        assert config.backends[0].kind == "kaggle_qwen"


class TestConfigValidation:
    def test_validation_empty_strategies(self) -> None:
        from benchmark.config.validation import validate_config
        from benchmark.core.exceptions import ValidationError

        config = BenchmarkConfig()
        with pytest.raises(ValidationError, match="Config validation failed"):
            validate_config(config)

    def test_validation_valid_config(self) -> None:
        from benchmark.config.validation import validate_config

        config = BenchmarkConfig(
            strategies=[StrategyConfig(name="hybrid")],
            backends=[BackendConfig(name="mock1", kind="mock")],
            repositories=[RepositoryConfig(name="todo", url="https://example.com/repo")],
        )
        errors = validate_config(config)
        assert errors == []
