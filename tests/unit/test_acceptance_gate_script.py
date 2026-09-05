from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"

_SPEC = importlib.util.spec_from_file_location(
    "run_model_acceptance_gate", SCRIPTS_DIR / "run_model_acceptance_gate.py"
)
_MOD = importlib.util.module_from_spec(_SPEC)
sys.modules["run_model_acceptance_gate"] = _MOD
assert _SPEC.loader is not None
_spec = _SPEC
_spec.loader.exec_module(_MOD)


class _MockBackend:
    def __init__(self, texts: list[str]):
        self._texts = list(texts)
        self.transient_retry_count = 0

    async def generate(self, prompt: str = "", temperature: float = 0.0, max_tokens: int = 4096):
        from benchmark.core.exceptions import ModelBackendError
        from benchmark.core.models import LLMResponse, TokenUsage

        text = self._texts.pop(0)
        if text.startswith("ERR:"):
            raise ModelBackendError(f"OpenRouter HTTP 429: {text[4:]}")
        return LLMResponse(
            text=text,
            token_usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            finish_reason="stop",
        )


_A1_OK = (
    '{"decisions": ['
    '{"path": "pkg/alpha.py", "action": "REGENERATE", "rationale": "edit", "confidence": 0.9},'
    '{"path": "pkg/beta.py", "action": "REGENERATE", "rationale": "edit", "confidence": 0.9},'
    '{"path": "pkg/gamma.py", "action": "PRESERVE", "rationale": "no edit", "confidence": 0.9}],'
    '"context_set": ["pkg/alpha.py", "pkg/beta.py"],'
    '"validation_obligations": [], "architecture_checks": []}'
)

_A2_OK = (
    "<<<<<<< SEARCH\nrename_me = 0\n=======\ncounter_new = 0\n>>>>>>> REPLACE\n"
    "<<<<<<< SEARCH\n    return rename_me + 1\n=======\n    return counter_new + 1\n>>>>>>> REPLACE"
)

_A3_OK = '{"selected_paths": ["pkg/alpha.py", "pkg/beta.py"], "rationale": "need edits"}'


class TestProviderResolution:
    def test_deepinfra_resolved_first(self) -> None:
        endpoints = [
            {"provider_name": "DeepInfra", "tag": "deepinfra/turbo"},
            {"provider_name": "Novita", "tag": "novita"},
        ]
        provider = _MOD.resolve_provider_from_endpoints(
            "qwen/qwen3-coder", endpoints, ("DeepInfra", "Novita")
        )
        assert provider == "DeepInfra"

    def test_novita_fallback_when_deepinfra_absent(self) -> None:
        endpoints = [{"provider_name": "Novita", "tag": "novita"}]
        provider = _MOD.resolve_provider_from_endpoints(
            "qwen/qwen3-coder", endpoints, ("DeepInfra", "Novita")
        )
        assert provider == "Novita"

    def test_no_provider_in_order_raises(self) -> None:
        with pytest.raises(RuntimeError, match="do not model-shop"):
            _MOD.resolve_provider_from_endpoints(
                "qwen/qwen3-coder", [{"provider_name": "Google"}], ("DeepInfra", "Novita")
            )

    def test_empty_endpoints_raises(self) -> None:
        with pytest.raises(RuntimeError, match="do not model-shop"):
            _MOD.resolve_provider_from_endpoints("qwen/qwen3-coder", [], ("DeepInfra", "Novita"))


class TestPricingSnapshot:
    def test_extracts_deepinfra_pricing(self) -> None:
        endpoints = [
            {"provider_name": "DeepInfra", "tag": "deepinfra/turbo",
             "pricing": {"prompt": "0.0000003", "completion": "0.000001"}}
        ]
        snap = _MOD.pricing_snapshot("qwen/qwen3-coder", endpoints, "DeepInfra")
        assert snap["prompt_per_token_usd"] == "0.0000003"
        assert snap["tag"] == "deepinfra/turbo"

    def test_missing_provider_returns_empty(self) -> None:
        snap = _MOD.pricing_snapshot("m", [{"provider_name": "X"}], "Y")
        assert snap == {}


class TestTaskParsers:
    def test_a1_correct_plan_success(self) -> None:
        backend = _MockBackend([_A1_OK])
        outcome = _MOD.run_task_a1(backend)
        assert outcome["deterministic_success"] is True
        assert outcome["parser_pass"] is True
        assert outcome["truncation"] is False

    def test_a1_garbage_fails(self) -> None:
        backend = _MockBackend(["not json"])
        outcome = _MOD.run_task_a1(backend)
        assert outcome["deterministic_success"] is False
        assert outcome["parser_pass"] is False

    def test_a1_wrong_action_fails(self) -> None:
        bad = _A1_OK.replace('"pkg/gamma.py", "action": "PRESERVE"',
                             '"pkg/gamma.py", "action": "REGENERATE"')
        backend = _MockBackend([bad])
        outcome = _MOD.run_task_a1(backend)
        assert outcome["deterministic_success"] is False

    def test_a2_correct_patch_success(self) -> None:
        backend = _MockBackend([_A2_OK])
        outcome = _MOD.run_task_a2(backend)
        assert outcome["deterministic_success"] is True
        assert outcome["parser_pass"] is True

    def test_a2_garbage_fails(self) -> None:
        backend = _MockBackend(["not a patch"])
        outcome = _MOD.run_task_a2(backend)
        assert outcome["deterministic_success"] is False
        assert outcome["parser_pass"] is False

    def test_a3_correct_control_success(self) -> None:
        backend = _MockBackend([_A3_OK])
        outcome = _MOD.run_task_a3(backend)
        assert outcome["deterministic_success"] is True
        assert outcome["parser_pass"] is True

    def test_a3_wrong_paths_fails(self) -> None:
        bad = '{"selected_paths": ["pkg/alpha.py"], "rationale": "missing beta"}'
        backend = _MockBackend([bad])
        outcome = _MOD.run_task_a3(backend)
        assert outcome["deterministic_success"] is False


class TestEligibility:
    def _good_tasks(self, n=3) -> list[dict]:
        return [
            {
                "deterministic_success": True,
                "parser_pass": True,
                "truncation": False,
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
                "latency_seconds": 5.0,
                "transient_retry_count": 0,
            }
            for _i in range(n)
        ]

    def test_all_thresholds_met(self) -> None:
        el = _MOD.compute_eligibility(self._good_tasks())
        assert el["eligible"] is True

    def test_truncation_fails(self) -> None:
        tasks = self._good_tasks()
        tasks[0]["truncation"] = True
        tasks[0]["deterministic_success"] = False
        el = _MOD.compute_eligibility(tasks)
        assert el["eligible"] is False

    def test_latency_over_120_fails(self) -> None:
        tasks = self._good_tasks()
        tasks[0]["latency_seconds"] = 150
        el = _MOD.compute_eligibility(tasks)
        assert el["eligible"] is False

    def test_median_over_60_fails(self) -> None:
        tasks = self._good_tasks()
        for t in tasks:
            t["latency_seconds"] = 70
        el = _MOD.compute_eligibility(tasks)
        assert el["eligible"] is False

    def test_one_transient_ok(self) -> None:
        tasks = self._good_tasks()
        tasks[0]["transient_retry_count"] = 1
        el = _MOD.compute_eligibility(tasks)
        assert el["eligible"] is True


class TestFreeze:
    def test_freeze_identity_shape(self) -> None:
        outcome = _MOD.GateOutcome(model="qwen/qwen3-coder", provider="DeepInfra", eligible=True)
        freeze = _MOD.write_freeze(
            outcome,
            acceptance_report={},
            prereg_amendment_commit="abc123",
            source_commit="def456",
            pricing_timestamp="2026-09-05T00:00:00Z",
            pricing={"prompt_per_token_usd": "0.0000003"},
        )
        assert freeze["identity"] == "openrouter:qwen/qwen3-coder@DeepInfra"
        assert freeze["protocol"] == "scientific-wip-impactplan-v1"
        assert freeze["provider_fallbacks"] is False
        assert freeze["require_parameters"] is True
        assert freeze["workflow_timeout_seconds"] == 900
        assert freeze["source_edit_cap"] == 4096
        assert freeze["agent_control_cap"] == 512
