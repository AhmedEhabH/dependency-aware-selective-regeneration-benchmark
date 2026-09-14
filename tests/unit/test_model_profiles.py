"""Unit tests for the prospective model/profile resolution layer (ZERO API)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from benchmark.model_profiles import (
    ResolvedModelConfig,
    assert_resolved_matches_frozen,
    load_profiles,
    profile_from_persisted,
    resolve_profile,
)

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "model_profiles.yaml"


def test_profiles_file_loads() -> None:
    profiles = load_profiles(CONFIG_PATH)
    assert "qwen3-coder-openrouter-deepinfra" in profiles
    assert "deepseek-v4-flash-openrouter" in profiles
    assert "deepseek-v4-flash-direct" in profiles
    assert "hf-example" in profiles


def test_historical_primary_profile_mirrors_frozen_constants() -> None:
    profiles = load_profiles(CONFIG_PATH)
    p = profiles["qwen3-coder-openrouter-deepinfra"]
    assert p.model == "qwen/qwen3-coder"
    assert p.provider_pin == "deepinfra/turbo"
    assert p.gateway == "openrouter"
    assert p.temperature == 0.0
    assert p.max_completion_tokens == 16384
    assert p.structured_output == "json_schema"
    assert p.fallbacks is False
    assert p.budget_abort_ceiling_usd == 1.50


def test_resolve_openrouter_exact_model() -> None:
    profiles = load_profiles(CONFIG_PATH)
    resolved = resolve_profile(profiles["qwen3-coder-openrouter-deepinfra"])
    assert resolved.exact_model == "openrouter:qwen/qwen3-coder@deepinfra/turbo"
    assert resolved.gateway == "openrouter"
    assert resolved.api_key_env == "OPENROUTER_API_KEY"


def test_resolve_deepseek_direct_exact_model() -> None:
    profiles = load_profiles(CONFIG_PATH)
    resolved = resolve_profile(profiles["deepseek-v4-flash-direct"])
    assert resolved.exact_model == "deepseek:deepseek-chat"
    assert resolved.gateway == "deepseek"
    assert resolved.api_key_env == "DEEPSEEK_API_KEY"


def test_api_key_present_only_boolean_never_value() -> None:
    profiles = load_profiles(CONFIG_PATH)
    key_name = "OPENROUTER_API_KEY"
    old = os.environ.get(key_name)
    try:
        os.environ[key_name] = "  \"sk-SECRET\"  "
        resolved = resolve_profile(profiles["deepseek-v4-flash-openrouter"])
        assert resolved.api_key_present is True
        # the secret value must never be part of the persisted identity
        assert "SECRET" not in json.dumps(resolved.to_persisted_dict())
        os.environ.pop(key_name, None)
        resolved2 = resolve_profile(profiles["deepseek-v4-flash-openrouter"])
        assert resolved2.api_key_present is False
    finally:
        if old is None:
            os.environ.pop(key_name, None)
        else:
            os.environ[key_name] = old


def test_profile_sha256_stable() -> None:
    profiles = load_profiles(CONFIG_PATH)
    p = profiles["qwen3-coder-openrouter-deepinfra"]
    assert p.profile_sha256() == p.profile_sha256()
    assert len(p.profile_sha256()) == 64


def test_persisted_identity_roundtrip_and_frozen_match() -> None:
    profiles = load_profiles(CONFIG_PATH)
    resolved = resolve_profile(profiles["deepseek-v4-flash-openrouter"])
    persisted = resolved.to_persisted_dict()
    assert persisted["profile_sha256"] == resolved.profile_sha256
    # re-resolve (simulating live run) and require match with frozen identity
    resolved2 = resolve_profile(profiles["deepseek-v4-flash-openrouter"])
    assert_resolved_matches_frozen(resolved2, persisted)


def test_frozen_mismatch_fails_closed() -> None:
    profiles = load_profiles(CONFIG_PATH)
    resolved = resolve_profile(profiles["deepseek-v4-flash-openrouter"])
    persisted = resolved.to_persisted_dict()
    tampered = dict(persisted)
    tampered["max_completion_tokens"] = 4096
    with pytest.raises(RuntimeError, match="differs from frozen manifest"):
        assert_resolved_matches_frozen(resolved, tampered)


def test_profile_from_persisted_type() -> None:
    profiles = load_profiles(CONFIG_PATH)
    resolved = resolve_profile(profiles["hf-example"])
    restored = profile_from_persisted(resolved.to_persisted_dict())
    assert isinstance(restored, ResolvedModelConfig)
    assert restored.exact_model == resolved.exact_model


def test_profile_sha256_changes_with_fields() -> None:
    profiles = load_profiles(CONFIG_PATH)
    p = profiles["deepseek-v4-flash-openrouter"]
    sha = p.profile_sha256()
    modified = profiles["deepseek-v4-flash-direct"]
    assert modified.profile_sha256() != sha
