"""WP-1a frozen protocol + failure semantics tests (AC-1A.6, section 8)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
if str(PROJECT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR / "src"))

from benchmark.wp1a.semantics import (  # noqa: E402
    FAILURE_RATE_NAMES,
    PRIMARY_ANALYSIS_RULE,
)

WP1A = PROJECT_DIR / "research" / "wp1a"

REQUIRED_PROTOCOL_SECTIONS = [
    "initial_system_prompt", "tools", "tool_schemas",
    "parent_repository_snapshot_source", "candidate_universe_boundary",
    "allowed_directories_file_types", "file_read_policy", "search_policy",
    "context_retention_policy", "context_truncation_policy",
    "round_definition", "proposed_hard_max_rounds",
    "completion_token_cap_per_model_response", "stop_rule", "timeout_rule",
    "retry_rule", "malformed_output_rule", "empty_output_rule",
    "path_outside_universe_handling", "duplicate_path_normalization",
    "allow_ground_truth_universe", "runrecord_audit_field",
    "final_file_set_json_schema", "fail_closed_semantics",
    "labels_never_accessed",
]


def test_protocol_completeness() -> None:
    protocol = json.loads((WP1A / "wp1a_frozen_agent_protocol.json").read_text(encoding="utf-8"))
    missing = [k for k in REQUIRED_PROTOCOL_SECTIONS if k not in protocol["sections"]]
    assert not missing


def test_protocol_allow_ground_truth_universe_false() -> None:
    protocol = json.loads((WP1A / "wp1a_frozen_agent_protocol.json").read_text(encoding="utf-8"))
    assert protocol["sections"]["allow_ground_truth_universe"] is False


def test_protocol_max_rounds_frozen() -> None:
    protocol = json.loads((WP1A / "wp1a_frozen_agent_protocol.json").read_text(encoding="utf-8"))
    assert protocol["sections"]["proposed_hard_max_rounds"]["MAX_AGENT_CALLS"] == 8


def test_protocol_control_cap_frozen() -> None:
    protocol = json.loads((WP1A / "wp1a_frozen_agent_protocol.json").read_text(encoding="utf-8"))
    assert protocol["sections"]["completion_token_cap_per_model_response"][
        "agent_control_max_completion_tokens"] == 512


def test_protocol_labels_never_accessed() -> None:
    protocol = json.loads((WP1A / "wp1a_frozen_agent_protocol.json").read_text(encoding="utf-8"))
    assert protocol["sections"]["labels_never_accessed"]


def test_failure_semantics_preregistered() -> None:
    fs = json.loads((WP1A / "wp1a_failure_semantics.json").read_text(encoding="utf-8"))
    assert fs["no_silent_exclusions"] is True
    for rate in FAILURE_RATE_NAMES:
        assert rate in fs["per_arm_failure_rates"]
    assert "ALL-TASKS / FAIL-CLOSED" in fs["primary_analysis_rule"]
    assert "EMPTY prediction" in fs["primary_analysis_rule"]


def test_failure_retry_rule() -> None:
    fs = json.loads((WP1A / "wp1a_failure_semantics.json").read_text(encoding="utf-8"))
    assert "3" in fs["retry"]["transport"]
    assert "ONLY transport failures may be retried" in fs["retry"]["transport"]


def test_cost_quality_categories_frozen() -> None:
    cats = json.loads((WP1A / "wp1a_cost_quality_categories.json").read_text(encoding="utf-8"))
    for name in ("RM_CSS_COST_QUALITY_DOMINANCE", "COST_QUALITY_TRADEOFF",
                 "NO_RM_CSS_EFFICIENCY_ADVANTAGE", "RM_CSS_EFFICIENCY_HYPOTHESIS_FALSIFIED"):
        assert name in cats["categories"]
        assert cats["categories"][name]["condition"]
    assert "H_WP1" in cats["hypothesis"]
    assert "No universal/SOTA claim" in cats["claim_boundary"]


def test_primary_analysis_rule_semantics_module() -> None:
    assert "FAIL-CLOSED" in PRIMARY_ANALYSIS_RULE
    assert "EMPTY prediction" in PRIMARY_ANALYSIS_RULE
