"""Dynamic future model/provider profiles — immutable resolved configuration.

This module implements the prospective model-layer refactor described in
`docs/MODEL_PROVIDER_GUIDE.md` and `README_MODEL_PROVIDER_REFACTOR_SPEC`.

Design rules:
- ``ModelProfile`` is a small immutable dataclass (config-file friendly).
- ``ResolvedModelConfig`` is the fully resolved snapshot that a scientific run
  MUST freeze BEFORE call #1; a live run refuses to continue if the resolved
  profile differs from the frozen manifest.
- The transport layer is OpenAI-compatible (OpenRouter, DeepSeek direct, and
  Hugging Face Inference Providers all expose OpenAI-compatible endpoints), so
  no provider-specific HTTP adapter is required here.
- Secrets are referenced by environment-variable NAME only; this module never
  reads or logs a token value.
- Historical scripts keep their own frozen constants; this layer is for FUTURE
  studies. Historical study launchers remain the reproducible source of truth.

ZERO scientific model calls are required to build or validate profiles.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

StructuredOutputMode = Literal["json_schema", "json_object", "prompt_only_json", "unsupported"]
GatewayKind = Literal["openrouter", "deepseek", "huggingface", "openai_compatible"]


@dataclass(frozen=True)
class ModelProfile:
    """Human-readable versioned model/provider configuration.

    All fields are public and match the YAML keys in ``config/model_profiles.yaml``.
    """

    id: str
    gateway: GatewayKind
    base_url: str
    model: str
    provider_pin: str | None = None
    api_key_env: str | None = None
    temperature: float = 0.0
    max_completion_tokens: int = 16384
    reasoning: dict[str, Any] = field(default_factory=dict)
    structured_output: StructuredOutputMode = "json_schema"
    fallbacks: bool = False
    timeout_seconds: int = 300
    retry_policy: dict[str, Any] = field(
        default_factory=lambda: {"max_retries": 3, "backoff_seconds": 20.0}
    )
    budget_abort_ceiling_usd: float | None = None
    description: str = ""

    def profile_sha256(self) -> str:
        canonical = json.dumps(
            {
                "id": self.id,
                "gateway": self.gateway,
                "base_url": self.base_url,
                "model": self.model,
                "provider_pin": self.provider_pin,
                "api_key_env": self.api_key_env,
                "temperature": self.temperature,
                "max_completion_tokens": self.max_completion_tokens,
                "reasoning": self.reasoning,
                "structured_output": self.structured_output,
                "fallbacks": self.fallbacks,
                "timeout_seconds": self.timeout_seconds,
                "retry_policy": self.retry_policy,
                "budget_abort_ceiling_usd": self.budget_abort_ceiling_usd,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ResolvedModelConfig:
    """Fully resolved model/provider snapshot frozen before scientific call #1."""

    profile_id: str
    gateway: GatewayKind
    base_url: str
    model: str
    provider_pin: str | None
    exact_model: str
    api_key_env: str | None
    api_key_present: bool
    temperature: float
    max_completion_tokens: int
    reasoning: dict[str, Any]
    structured_output: StructuredOutputMode
    fallbacks: bool
    timeout_seconds: int
    retry_policy: dict[str, Any]
    budget_abort_ceiling_usd: float | None
    profile_sha256: str

    def to_persisted_dict(self) -> dict[str, Any]:
        """Serializable identity to persist in a scientific manifest pre-call #1."""
        return {
            "profile_id": self.profile_id,
            "gateway": self.gateway,
            "base_url": self.base_url,
            "model": self.model,
            "provider_pin": self.provider_pin,
            "exact_model": self.exact_model,
            "api_key_env": self.api_key_env,
            "api_key_present": self.api_key_present,
            "temperature": self.temperature,
            "max_completion_tokens": self.max_completion_tokens,
            "reasoning": self.reasoning,
            "structured_output": self.structured_output,
            "fallbacks": self.fallbacks,
            "timeout_seconds": self.timeout_seconds,
            "retry_policy": self.retry_policy,
            "budget_abort_ceiling_usd": self.budget_abort_ceiling_usd,
            "profile_sha256": self.profile_sha256,
        }


def _default_config_path() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent / "config" / "model_profiles.yaml"


def load_profiles(path: Path | None = None) -> dict[str, ModelProfile]:
    """Load all profiles from a YAML file (default ``config/model_profiles.yaml``)."""
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - only without pyyaml installed
        raise RuntimeError("PyYAML is required to load model profiles") from exc

    config_path = path or _default_config_path()
    if not config_path.is_file():
        raise FileNotFoundError(f"model profiles not found: {config_path}")
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    entries = raw.get("profiles") if isinstance(raw, dict) else None
    if not isinstance(entries, list):
        raise ValueError("model_profiles.yaml must contain a 'profiles' list")

    profiles: dict[str, ModelProfile] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("each profile entry must be a mapping")
        profile = ModelProfile(
            id=str(entry["id"]),
            gateway=entry["gateway"],
            base_url=str(entry["base_url"]),
            model=str(entry["model"]),
            provider_pin=entry.get("provider_pin"),
            api_key_env=entry.get("api_key_env"),
            temperature=float(entry.get("temperature", 0.0)),
            max_completion_tokens=int(entry.get("max_completion_tokens", 16384)),
            reasoning=entry.get("reasoning") or {},
            structured_output=entry.get("structured_output", "json_schema"),
            fallbacks=bool(entry.get("fallbacks", False)),
            timeout_seconds=int(entry.get("timeout_seconds", 300)),
            retry_policy=entry.get("retry_policy")
            or {"max_retries": 3, "backoff_seconds": 20.0},
            budget_abort_ceiling_usd=(
                float(entry["budget_abort_ceiling_usd"])
                if entry.get("budget_abort_ceiling_usd") is not None
                else None
            ),
            description=str(entry.get("description", "")),
        )
        if profile.id in profiles:
            raise ValueError(f"duplicate profile id {profile.id!r}")
        profiles[profile.id] = profile
    return profiles


def resolve_profile(
    profile: ModelProfile,
    *,
    fallbacks_override: bool | None = None,
) -> ResolvedModelConfig:
    """Resolve a profile to an immutable, frozen configuration.

    Never reads the secret value — only records whether the referenced
    environment variable is present (fail-closed for live runs).
    """
    api_key_env = profile.api_key_env
    api_key_present = False
    if api_key_env:
        value = os.environ.get(api_key_env, "")
        api_key_present = bool(value and value.strip().strip('"').strip("'").strip())

    exact_model = profile.model
    if profile.gateway == "openrouter":
        suffix = f"@{profile.provider_pin}" if profile.provider_pin else ""
        exact_model = f"openrouter:{profile.model}{suffix}"
    elif profile.gateway == "huggingface":
        suffix = f":{profile.provider_pin}" if profile.provider_pin else ""
        exact_model = f"hf:{profile.model}{suffix}"
    elif profile.gateway == "deepseek":
        exact_model = f"deepseek:{profile.model}"

    return ResolvedModelConfig(
        profile_id=profile.id,
        gateway=profile.gateway,
        base_url=profile.base_url,
        model=profile.model,
        provider_pin=profile.provider_pin,
        exact_model=exact_model,
        api_key_env=api_key_env,
        api_key_present=api_key_present,
        temperature=profile.temperature,
        max_completion_tokens=profile.max_completion_tokens,
        reasoning=profile.reasoning,
        structured_output=profile.structured_output,
        fallbacks=profile.fallbacks if fallbacks_override is None else fallbacks_override,
        timeout_seconds=profile.timeout_seconds,
        retry_policy=profile.retry_policy,
        budget_abort_ceiling_usd=profile.budget_abort_ceiling_usd,
        profile_sha256=profile.profile_sha256(),
    )


def profile_from_persisted(persisted: dict[str, Any]) -> ResolvedModelConfig:
    """Reconstruct a resolved config from a frozen manifest identity."""
    return ResolvedModelConfig(
        profile_id=str(persisted["profile_id"]),
        gateway=persisted["gateway"],
        base_url=str(persisted["base_url"]),
        model=str(persisted["model"]),
        provider_pin=persisted.get("provider_pin"),
        exact_model=str(persisted["exact_model"]),
        api_key_env=persisted.get("api_key_env"),
        api_key_present=bool(persisted.get("api_key_present")),
        temperature=float(persisted["temperature"]),
        max_completion_tokens=int(persisted["max_completion_tokens"]),
        reasoning=persisted.get("reasoning") or {},
        structured_output=persisted["structured_output"],
        fallbacks=bool(persisted.get("fallbacks")),
        timeout_seconds=int(persisted.get("timeout_seconds", 300)),
        retry_policy=persisted.get("retry_policy") or {},
        budget_abort_ceiling_usd=persisted.get("budget_abort_ceiling_usd"),
        profile_sha256=str(persisted["profile_sha256"]),
    )


def assert_resolved_matches_frozen(resolved: ResolvedModelConfig, frozen: dict[str, Any]) -> None:
    """Fail closed if a live-resolved profile differs from the frozen manifest."""
    frozen_resolved = profile_from_persisted(frozen)
    mismatches: list[str] = []
    for field_name in (
        "profile_id",
        "gateway",
        "base_url",
        "model",
        "provider_pin",
        "exact_model",
        "temperature",
        "max_completion_tokens",
        "reasoning",
        "structured_output",
        "fallbacks",
        "timeout_seconds",
        "retry_policy",
        "budget_abort_ceiling_usd",
    ):
        if getattr(resolved, field_name) != getattr(frozen_resolved, field_name):
            mismatches.append(field_name)
    if resolved.profile_sha256 != frozen_resolved.profile_sha256:
        mismatches.append("profile_sha256")
    if mismatches:
        raise RuntimeError(
            "resolved profile differs from frozen manifest identity: "
            + ", ".join(mismatches)
        )
