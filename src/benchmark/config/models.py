from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from benchmark.core.enums import EvidenceTier


class StrategyConfig(BaseModel, frozen=True):
    name: str
    params: dict[str, str | int | float | bool] = Field(default_factory=dict)
    llm_backend: str | None = None

    @model_validator(mode="after")
    def _validate_name(self) -> StrategyConfig:
        if not self.name:
            raise ValueError("StrategyConfig.name must not be empty")
        return self


class BackendConfig(BaseModel, frozen=True):
    name: str
    kind: Literal["mock", "dry_run", "kaggle_qwen"] = "mock"
    params: dict[str, str | int | float | bool] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_name(self) -> BackendConfig:
        if not self.name:
            raise ValueError("BackendConfig.name must not be empty")
        return self


class RepositoryConfig(BaseModel, frozen=True):
    name: str
    url: str
    ref: str = "main"


class ScenarioSelectionConfig(BaseModel, frozen=True):
    repository_names: list[str] = Field(default_factory=list)
    scenario_ids: list[str] = Field(default_factory=list)
    blast_radii: list[str] = Field(default_factory=list)


class ExecutionConfig(BaseModel, frozen=True):
    max_iterations: int = Field(default=3, ge=1)
    max_tokens: int = Field(default=0, ge=0)
    timeout_seconds: int = Field(default=0, ge=0)
    random_seed: int = 0
    evidence_tier: EvidenceTier = EvidenceTier.engineering_validation


class OutputConfig(BaseModel, frozen=True):
    output_dir: str = "runs"
    format: Literal["json", "jsonl"] = "jsonl"
    write_provenance: bool = True


class BenchmarkConfig(BaseModel, frozen=True):
    protocol_version: str = "1.0"
    execution_mode: Literal["local", "kaggle"] = "local"
    strategies: list[StrategyConfig] = Field(default_factory=list)
    backends: list[BackendConfig] = Field(default_factory=list)
    repositories: list[RepositoryConfig] = Field(default_factory=list)
    scenario_selection: ScenarioSelectionConfig = Field(default_factory=ScenarioSelectionConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)

    @model_validator(mode="after")
    def _reject_kaggle_backend_for_local(self) -> BenchmarkConfig:
        if self.execution_mode == "local":
            for b in self.backends:
                if b.kind == "kaggle_qwen":
                    raise ValueError(
                        f"Kaggle backend '{b.name}' cannot be used in local execution mode"
                    )
        return self

    @model_validator(mode="after")
    def _reject_publication_for_mock(self) -> BenchmarkConfig:
        if self.execution.evidence_tier in (EvidenceTier.smoke, EvidenceTier.engineering_validation):
            for b in self.backends:
                if b.kind in ("mock", "dry_run"):
                    pass
        return self
