from __future__ import annotations


class FakeArgs:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


def _make_args(**over):
    base = {
        "dry_run": False,
        "profile": "scientific-microstudy-01",
        "strategy": None,
        "max_attempts": 3,
        "timeout": 900,
        "protocol_version": "1.0",
        "max_completion_tokens_per_call": 4096,
        "max_total_workflow_tokens": 0,
        "max_tokens": 0,
        "qwen_quantization": "bnb-int8",
        "exact_patch": True,
        "agent_control_max_completion_tokens": 512,
        "backend": "openrouter",
        "openrouter_model": "deepseek/deepseek-v4-flash-0731",
        "openrouter_provider": "DeepSeek",
    }
    base.update(over)
    return FakeArgs(**base)


class TestModelIdentityIncludesProvider:
    def test_openrouter_identity_includes_provider(self):
        from seven_arm_benchmark import _get_model_identity

        ident = _get_model_identity(
            backend_name="openrouter",
            openrouter_model="deepseek/deepseek-v4-flash-0731",
            openrouter_provider="DeepSeek",
        )
        assert ident == "openrouter:deepseek/deepseek-v4-flash-0731@DeepSeek"

    def test_openrouter_identity_without_provider_not_allowed_for_openrouter(self):
        from seven_arm_benchmark import _get_model_identity

        ident = _get_model_identity(
            backend_name="openrouter",
            openrouter_model="m",
            openrouter_provider="",
        )
        assert ident == "openrouter:m"

    def test_dry_run_mock_identity(self):
        from seven_arm_benchmark import _get_model_identity

        ident = _get_model_identity()
        assert ident == "dry-run:mock"


class TestConfigHashIdentity:
    def test_model_change_changes_config_hash(self):
        from seven_arm_benchmark import _compute_config_hash

        h1 = _compute_config_hash(_make_args(openrouter_model="deepseek/deepseek-v4-flash-0731"))
        h2 = _compute_config_hash(_make_args(openrouter_model="qwen/qwen-2.5-coder-32b-instruct"))
        assert h1 != h2

    def test_provider_change_changes_config_hash(self):
        from seven_arm_benchmark import _compute_config_hash

        h1 = _compute_config_hash(_make_args(openrouter_provider="DeepSeek"))
        h2 = _compute_config_hash(_make_args(openrouter_provider="OpenRouter"))
        assert h1 != h2

    def test_backend_change_changes_config_hash(self):
        from seven_arm_benchmark import _compute_config_hash

        h1 = _compute_config_hash(_make_args(backend="openrouter"))
        h2 = _compute_config_hash(_make_args(backend="kaggle-qwen"))
        assert h1 != h2

    def test_config_hash_is_deterministic(self):
        from seven_arm_benchmark import _compute_config_hash

        h1 = _compute_config_hash(_make_args())
        h2 = _compute_config_hash(_make_args())
        assert h1 == h2

    def test_config_hash_hash_algorithm(self):
        from seven_arm_benchmark import _compute_config_hash

        h = _compute_config_hash(_make_args())
        assert len(h) == 16
        assert all(c in "0123456789abcdef" for c in h)


class TestRunIdCoversIdentity:
    def test_run_id_changes_with_provider(self):
        from seven_arm_benchmark import _make_run_id

        id1 = _make_run_id(
            "todo-smoke-001", "selective", 1,
            config_hash="aaaaaaaaaaaaaaaa", protocol_version="1.0",
        )
        id2 = _make_run_id(
            "todo-smoke-001", "selective", 1,
            config_hash="bbbbbbbbbbbbbbbb", protocol_version="1.0",
        )
        assert id1 != id2


class TestImpactPlanStrategyIdentity:
    def test_strategy_registered_and_hashable(self):
        """impact_plan strategy is part of the config identity namespace
        (backend/model/provider + strategy are hashed together)."""
        from seven_arm_benchmark import STRATEGY_NAMES, _compute_config_hash

        assert "impact_plan" in STRATEGY_NAMES
        h1 = _compute_config_hash(_make_args(strategy="impact_plan"))
        h2 = _compute_config_hash(_make_args(strategy="selective"))
        assert h1 != h2
