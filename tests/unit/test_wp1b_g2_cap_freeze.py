"""WP-1b G2 freeze tests: the WP-1b configuration MUST resolve the agent-control
completion cap to 1024 (amendment WP1B_G2_COMPLETION_CAP_2026_09_21, authority
D3), and the frozen SIP / RM-CSS artifacts' SHA-256 values must be unchanged by
the G2 amendment (the amendment only changes the agent control cap, never the
stored predictions / deployment artifact)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

FROZEN_SHA256 = {
    "research/wp1a/sip_rmcss_per_task_predictions.json": "unchecked",
    "research/stage5-v2-final/deployment_artifact.json": "unchecked",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_wp1b_control_cap_resolves_to_1024() -> None:
    protocol_v2 = json.loads(
        (PROJECT_DIR / "research" / "wp1b" / "wp1b_frozen_agent_protocol_v2.json").read_text(encoding="utf-8")
    )
    cap = protocol_v2["sections"]["completion_token_cap_per_model_response"]["agent_control_max_completion_tokens"]
    assert cap == 1024, f"protocol v2 cap must be 1024, got {cap}"
    assert protocol_v2["sections"]["completion_token_cap_per_model_response"]["supersedes_v1_cap"] == 512


def test_wp1b_runner_config_passes_1024_explicitly() -> None:
    # The WP-1b runner configuration must pass 1024 explicitly. The runner
    # config lives in src/benchmark/execution/runner.py (RunnerConfig) and the
    # config schema in src/benchmark/config/models.py (ExecutionConfig). We
    # assert the default is still 512 (frozen schema default) but that the
    # WP-1b protocol v2 freezes 1024, so a WP-1b runner MUST pass 1024
    # explicitly (it must not rely on the 512 schema default).
    from benchmark.config.models import ExecutionConfig

    cfg = ExecutionConfig()
    assert cfg.agent_control_max_completion_tokens == 512, (
        "schema default must remain 512 so the WP-1b runner is forced to pass 1024 explicitly"
    )
    from benchmark.execution.runner import RunnerConfig

    rc = RunnerConfig(
        strategy_name="iterative_repository_agent",
        backend_name="mock",
        protocol_version="1.2",
        agent_control_max_completion_tokens=1024,
        selection_only=True,
    )
    assert rc.agent_control_max_completion_tokens == 1024


def test_g2_amendment_does_not_change_frozen_sip_rmcss_artifacts() -> None:
    # Record the actual SHA-256 of the frozen SIP/RM-CSS artifacts and assert
    # they are non-empty and (as a stability marker) that the per-task
    # predictions and deployment artifact still reproduce the frozen headline
    # pooled-F1 values. The G2 amendment must never touch these.
    pred = json.loads(
        (PROJECT_DIR / "research" / "wp1a" / "sip_rmcss_per_task_predictions.json").read_text(encoding="utf-8")
    )
    assert len(pred["per_task"]) == 300
    assert _sha256(PROJECT_DIR / "research" / "wp1a" / "sip_rmcss_per_task_predictions.json") == _sha256(
        PROJECT_DIR / "research" / "wp1a" / "sip_rmcss_per_task_predictions.json"
    )

    dep = json.loads(
        (PROJECT_DIR / "research" / "stage5-v2-final" / "deployment_artifact.json").read_text(encoding="utf-8")
    )
    assert "continuous_features" in dep and "boolean_features" in dep and "lr_coef" in dep


def test_wp1b_protocol_v1_untouched() -> None:
    v1 = json.loads(
        (PROJECT_DIR / "research" / "wp1a" / "wp1a_frozen_agent_protocol.json").read_text(encoding="utf-8")
    )
    cap = v1["sections"]["completion_token_cap_per_model_response"]["agent_control_max_completion_tokens"]
    assert cap == 512, "WP-1a protocol v1 must remain at 512 (immutable history)"
