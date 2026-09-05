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

    async def generate(self, prompt: str, temperature: float = 0.0, max_tokens: int = 4096):
        from benchmark.core.models import LLMResponse, TokenUsage

        text = self._texts.pop(0)
        from benchmark.core.exceptions import ModelBackendError

        if text.startswith("ERR:"):
            raise ModelBackendError(f"OpenRouter HTTP 429: {text[4:]}")
        return LLMResponse(
            text=text,
            token_usage=TokenUsage(prompt_tokens=10, completion_tokens=len(text), total_tokens=10 + len(text)),
            finish_reason="stop",
        )


_CORRECT_T1 = (
    "<<<<<<< SEARCH\ncounter = 0\n=======\ncounter_new = 0\n>>>>>>> REPLACE\n"
    "<<<<<<< SEARCH\n    return counter + 1\n=======\n    return counter_new + 1\n>>>>>>> REPLACE"
)

_CORRECT_T2 = json = (
    '{"decisions": ['
    '{"path": "todo/models.py", "action": "regenerate"},'
    '{"path": "todo/serializers.py", "action": "regenerate"},'
    '{"path": "todo/views.py", "action": "regenerate"},'
    '{"path": "todo/permissions.py", "action": "preserve"},'
    '{"path": "todo/urls.py", "action": "preserve"}],'
    '"rationale": "models/serializers/views must change; permissions and urls are invariant"}'
)

_CORRECT_T3 = (
    "<<<<<<< SEARCH\n    return counter + 1\n    print('after')\n=======\n    return counter + 1\n>>>>>>> REPLACE"
)


class TestProviderResolution:
    def test_first_party_deepseek_pinned(self) -> None:
        metadata = [
            {
                "id": "deepseek/deepseek-v4-flash-0731",
                "endpoints": [
                    {"provider_name": "DeepSeek", "name": "deepseek"},
                    {"provider_name": "Fireworks", "name": "fireworks"},
                ],
            }
        ]
        provider = _MOD.resolve_provider_for_candidate(
            "deepseek/deepseek-v4-flash-0731", metadata,
            policy="first_party_deepseek", first_party_provider="DeepSeek",
        )
        assert provider == "DeepSeek"

    def test_first_party_deepseek_absent_stops(self) -> None:
        metadata = [
            {
                "id": "deepseek/deepseek-v4-flash-0731",
                "endpoints": [{"provider_name": "Fireworks", "name": "fireworks"}],
            }
        ]
        with pytest.raises(RuntimeError, match="preregistration amendment"):
            _MOD.resolve_provider_for_candidate(
                "deepseek/deepseek-v4-flash-0731", metadata,
                policy="first_party_deepseek", first_party_provider="DeepSeek",
            )

    def test_single_provider_qwen_pinned(self) -> None:
        metadata = [
            {
                "id": "qwen/qwen-2.5-coder-32b-instruct",
                "endpoints": [{"provider_name": "Together", "name": "together"}],
            }
        ]
        provider = _MOD.resolve_provider_for_candidate(
            "qwen/qwen-2.5-coder-32b-instruct", metadata, policy="single_provider"
        )
        assert provider == "Together"

    def test_single_provider_no_longer_single_stops(self) -> None:
        metadata = [
            {
                "id": "qwen/qwen-2.5-coder-32b-instruct",
                "endpoints": [
                    {"provider_name": "Together", "name": "together"},
                    {"provider_name": "Fireworks", "name": "fireworks"},
                ],
            }
        ]
        with pytest.raises(RuntimeError, match="single-provider"):
            _MOD.resolve_provider_for_candidate(
                "qwen/qwen-2.5-coder-32b-instruct", metadata, policy="single_provider"
            )

    def test_unknown_model_stops(self) -> None:
        with pytest.raises(RuntimeError, match="not found in OpenRouter"):
            _MOD.resolve_provider_for_candidate(
                "nope/no-model", [], policy="single_provider"
            )


class TestTaskParsers:
    def test_t1_correct_patch_success(self) -> None:
        backend = _MockBackend([_CORRECT_T1])
        outcome = _MOD.run_task_t1(backend)
        assert outcome["deterministic_success"] is True
        assert outcome["parser_pass"] is True
        assert outcome["truncation"] is False

    def test_t1_garbage_fails(self) -> None:
        backend = _MockBackend(["not a patch at all"])
        outcome = _MOD.run_task_t1(backend)
        assert outcome["deterministic_success"] is False
        assert outcome["parser_pass"] is False

    def test_t2_correct_json_success(self) -> None:
        backend = _MockBackend([json])
        outcome = _MOD.run_task_t2(backend)
        assert outcome["deterministic_success"] is True
        assert outcome["parser_pass"] is True

    def test_t2_wrong_regen_set_fails(self) -> None:
        bad = json.replace('"todo/views.py", "action": "regenerate"',
                           '"todo/views.py", "action": "preserve"')
        backend = _MockBackend([bad])
        outcome = _MOD.run_task_t2(backend)
        assert outcome["deterministic_success"] is False

    def test_t3_correct_repair_success(self) -> None:
        backend = _MockBackend([_CORRECT_T3])
        outcome = _MOD.run_task_t3(backend)
        assert outcome["deterministic_success"] is True
        assert "print('after')" not in outcome.get("repaired", "")

    def test_t3_incomplete_repair_fails(self) -> None:
        backend = _MockBackend(["<<<<<<< SEARCH\ncounter = 0\n=======\nx = 1\n>>>>>>> REPLACE"])
        outcome = _MOD.run_task_t3(backend)
        assert outcome["deterministic_success"] is False


class TestEligibility:
    def _good_tasks(self, n=3) -> list[dict]:
        tasks = []
        for _i in range(n):
            tasks.append(
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
            )
        return tasks

    def test_all_thresholds_met(self) -> None:
        el = _MOD.compute_eligibility(self._good_tasks())
        assert el["eligible"] is True

    def test_truncation_fails(self) -> None:
        tasks = self._good_tasks()
        tasks[0]["truncation"] = True
        tasks[0]["finish_reason"] = "length"
        tasks[0]["deterministic_success"] = False
        el = _MOD.compute_eligibility(tasks)
        assert el["eligible"] is False

    def test_latency_over_120_fails(self) -> None:
        tasks = self._good_tasks()
        tasks[0]["latency_seconds"] = 150
        el = _MOD.compute_eligibility(tasks)
        assert el["eligible"] is False

    def test_median_latency_over_60_fails(self) -> None:
        tasks = self._good_tasks()
        for t in tasks:
            t["latency_seconds"] = 70
        el = _MOD.compute_eligibility(tasks)
        assert el["eligible"] is False

    def test_one_transient_allowed(self) -> None:
        tasks = self._good_tasks()
        tasks[0]["transient_retry_count"] = 1
        el = _MOD.compute_eligibility(tasks)
        assert el["eligible"] is True


class TestSelection:
    def _candidate(self, cid: str, eligible: bool) -> _MOD.CandidateGateResult:
        return _MOD.CandidateGateResult(
            id=cid, model=f"m-{cid}", provider="P",
            eligible=eligible,
            tasks=[
                {"parser_pass": True, "truncation": False, "latency_seconds": 5.0},
                {"parser_pass": True, "truncation": False, "latency_seconds": 5.0},
                {"parser_pass": True, "truncation": False, "latency_seconds": 5.0},
            ],
        )

    def test_neither_eligible_none(self) -> None:
        winner = _MOD.select_winner([self._candidate("A", False), self._candidate("B", False)])
        assert winner is None

    def test_single_eligible_wins(self) -> None:
        winner = _MOD.select_winner([self._candidate("A", False), self._candidate("B", True)])
        assert winner.id == "B"

    def test_lower_truncation_wins(self) -> None:
        a = self._candidate("A", True)
        a.tasks[0]["truncation"] = True
        b = self._candidate("B", True)
        winner = _MOD.select_winner([a, b])
        assert winner.id == "B"

    def test_lower_median_latency_wins(self) -> None:
        a = self._candidate("A", True)
        b = self._candidate("B", True)
        b.tasks = [
            {"parser_pass": True, "truncation": False, "latency_seconds": 2.0},
            {"parser_pass": True, "truncation": False, "latency_seconds": 2.0},
            {"parser_pass": True, "truncation": False, "latency_seconds": 2.0},
        ]
        winner = _MOD.select_winner([a, b])
        assert winner.id == "B"


class TestFreeze:
    def test_freeze_identity_shape(self) -> None:
        winner = _MOD.CandidateGateResult(
            id="A", model="deepseek/deepseek-v4-flash-0731", provider="DeepSeek",
            eligible=True, tasks=[],
        )
        freeze = _MOD.write_freeze(
            winner,
            acceptance_report={},
            prereg_amendment_commit="abc123",
            source_commit="def456",
            pricing_timestamp="2026-09-05T00:00:00Z",
        )
        assert freeze["identity"] == "openrouter:deepseek/deepseek-v4-flash-0731@DeepSeek"
        assert freeze["provider_fallbacks"] is False
        assert freeze["require_parameters"] is True
        assert freeze["workflow_timeout_seconds"] == 900
        assert freeze["source_edit_cap"] == 4096
        assert freeze["agent_control_cap"] == 512
        assert freeze["max_attempts"] == 3
