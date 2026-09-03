"""PILOT-EXEC-01 D10.3 / D10.5: pilot-canary evidence gate and the
terminality/viability split.

D10.5 separates TERMINALITY (did the pipeline finish to a terminal record)
from SCIENTIFIC VIABILITY (is that terminal result acceptable). A
deadline-censored run (``scientific_budget_exhausted`` reached the workflow
budget) is NOT an accepted measured failure - the D9.6 real pilot had 33/48
runs killed at the 600 s deadline and must never be masked as a clean
scientific failure. D10.3 adds a real pilot-canary gate that fail-closes on
any deadline-censored or engineering-blocker record (a canary must never be
masked by a timeout).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from benchmark.execution.preflight import (
    LaunchAuthorizationError,
    _pilot_viability,
    validate_pilot_canary_evidence,
)
from seven_arm_benchmark import _pilot_record_viability


def _terminal_record(
    *,
    status: str = "failed",
    strategy_id: str = "selective",
    repository_id: str = "todo",
    repetition: int = 1,
    kinds: list[str] | None = None,
    classification: str = "",
) -> dict[str, Any]:
    return {
        "run_id": f"canary-{strategy_id}-r{repetition}",
        "status": status,
        "strategy_id": strategy_id,
        "repository_id": repository_id,
        "repetition": repetition,
        "failure_details": (
            [{"kind": kind} for kind in (kinds or [])]
        ),
        "failure_classification": classification,
    }


def _source_identity(**overrides: Any) -> dict[str, Any]:
    identity: dict[str, Any] = {
        "protocol_version": "1.2",
        "profile": "pilot-canary",
        "source_commit": "abcdef1234567890abcdef1234567890abcdef12",
        "source_tag": "v0.9.22-d13r2-candidate",
        "deployed_build_id": "abcdef12",
        "model_identity": "qwen:14b-instruct-v1:bnb-nf4:cfg-test",
        "exact_patch": True,
        "agent_control_max_completion_tokens": 512,
    }
    identity.update(overrides)
    return identity


def _write_canary(
    tmp_path: Path,
    records: list[dict[str, Any]],
    identity: dict[str, Any],
) -> Path:
    canary_dir = tmp_path / "canary"
    canary_dir.mkdir(parents=True, exist_ok=True)
    (canary_dir / "run_records.jsonl").write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in records) + "\n",
        encoding="utf-8",
    )
    (canary_dir / "source_identity.json").write_text(
        json.dumps(identity, sort_keys=True), encoding="utf-8"
    )
    return canary_dir


def _valid_records() -> list[dict[str, Any]]:
    # 3 repositories (todo, djangocms, saleor) x 2 strategies x 1 rep = 6 records,
    # all accepted (D11 B1: the canary represents ALL three Pilot repositories).
    accepted = [
        _terminal_record(status="succeeded", strategy_id="iterative_repository_agent",
                         repository_id="todo", repetition=1),
        _terminal_record(status="succeeded", strategy_id="selective",
                         repository_id="todo", repetition=1),
        _terminal_record(status="succeeded", strategy_id="iterative_repository_agent",
                         repository_id="djangocms", repetition=1),
        _terminal_record(status="succeeded", strategy_id="selective",
                         repository_id="djangocms", repetition=1),
        _terminal_record(status="succeeded", strategy_id="iterative_repository_agent",
                         repository_id="saleor", repetition=1),
        _terminal_record(status="succeeded", strategy_id="selective",
                         repository_id="saleor", repetition=1),
    ]
    for index, record in enumerate(accepted):
        record["run_id"] = f"canary-{index:02d}"
    return accepted


class TestPilotRecordViability:
    """D10.5: the seven_arm_benchmark classifier taxonomy."""

    def test_accepted_when_succeeded(self) -> None:
        assert _pilot_record_viability({"status": "succeeded"}) == "accepted"

    def test_deadline_censored_is_separate_from_scientific_failure(self) -> None:
        rec = _terminal_record(kinds=["scientific_budget_exhausted"])
        assert _pilot_record_viability(rec) == "deadline_censored"

    def test_clean_scientific_failure(self) -> None:
        rec = _terminal_record(kinds=["build"])
        assert _pilot_record_viability(rec) == "scientific_failure"

    def test_classification_mirrors_failure_kinds(self) -> None:
        rec = _terminal_record(classification="model_output")
        assert _pilot_record_viability(rec) == "scientific_failure"

    def test_engineering_blocker(self) -> None:
        for status in ("timed_out", "cancelled"):
            assert _pilot_record_viability({"status": status}) == "engineering_blocker"
        for kinds in (["infrastructure"], ["harness_defect"], ["environment"]):
            assert (
                _pilot_record_viability(_terminal_record(kinds=kinds))
                == "engineering_blocker"
            )

    def test_unknown_failure_is_engineering_blocker(self) -> None:
        assert (
            _pilot_record_viability(_terminal_record(kinds=[]))
            == "engineering_blocker"
        )

    def test_deadline_censored_status_masks_scientific(self) -> None:
        rec = _terminal_record(kinds=["scientific_budget_exhausted", "build"])
        assert _pilot_record_viability(rec) == "deadline_censored"


class TestPilotViabilityMirror:
    """D10.5: preflight's mirror ``_pilot_viability`` matches the taxonomy."""

    def test_matches_benchmark_classifier(self) -> None:
        cases = [
            {"status": "succeeded"},
            _terminal_record(kinds=["scientific_budget_exhausted"]),
            _terminal_record(kinds=["build"]),
            _terminal_record(classification="model_output"),
            _terminal_record(kinds=["infrastructure"]),
            _terminal_record(kinds=[]),
            _terminal_record(kinds=["timeout"]),
        ]
        for record in cases:
            assert _pilot_viability(record) == _pilot_record_viability(record), record


class TestValidatePilotCanaryEvidence:
    """D10.3: the fail-closed pilot-canary gate."""

    def test_passes_on_real_six_cell_canary(self, tmp_path: Path) -> None:
        canary_dir = _write_canary(
            tmp_path, _valid_records(), _source_identity()
        )
        summary = validate_pilot_canary_evidence(
            canary_dir=canary_dir,
            expected_source_commit="abcdef1234567890abcdef1234567890abcdef12",
            expected_source_tag="v0.9.22-d13r2-candidate",
            expected_model_identity="qwen:14b-instruct-v1:bnb-nf4:cfg-test",
            expected_deployed_build_id="abcdef12",
        )
        assert summary["passed"] is True
        assert summary["records"] == 6
        assert summary["terminal"] == 6
        assert summary["viability_counts"]["accepted"] == 6

    def test_fails_closed_on_deadline_censored(self, tmp_path: Path) -> None:
        records = _valid_records()
        records[0] = _terminal_record(kinds=["scientific_budget_exhausted"])
        records[0]["run_id"] = "canary-00"
        canary_dir = _write_canary(tmp_path, records, _source_identity())
        with pytest.raises(LaunchAuthorizationError) as exc:
            validate_pilot_canary_evidence(
                canary_dir=canary_dir,
                expected_source_commit="abcdef1234567890abcdef1234567890abcdef12",
                expected_source_tag="v0.9.22-d13r2-candidate",
                expected_model_identity="qwen:14b-instruct-v1:bnb-nf4:cfg-test",
            )
        assert "deadline-censored" in str(exc.value)

    def test_fails_closed_on_engineering_blocker(self, tmp_path: Path) -> None:
        records = _valid_records()
        records[1] = _terminal_record(kinds=["infrastructure"])
        records[1]["run_id"] = "canary-01"
        canary_dir = _write_canary(tmp_path, records, _source_identity())
        with pytest.raises(LaunchAuthorizationError) as exc:
            validate_pilot_canary_evidence(
                canary_dir=canary_dir,
                expected_source_commit="abcdef1234567890abcdef1234567890abcdef12",
                expected_source_tag="v0.9.22-d13r2-candidate",
                expected_model_identity="qwen:14b-instruct-v1:bnb-nf4:cfg-test",
            )
        assert "engineering-blocker" in str(exc.value)

    def test_fails_closed_on_mock_identity(self, tmp_path: Path) -> None:
        canary_dir = _write_canary(
            tmp_path,
            _valid_records(),
            _source_identity(model_identity="dry-run:mock"),
        )
        with pytest.raises(LaunchAuthorizationError) as exc:
            validate_pilot_canary_evidence(
                canary_dir=canary_dir,
                expected_source_commit="abcdef1234567890abcdef1234567890abcdef12",
                expected_source_tag="v0.9.22-d13r2-candidate",
                expected_model_identity="qwen:14b-instruct-v1:bnb-nf4:cfg-test",
            )
        assert "dry-run:mock" in str(exc.value)

    def test_fails_closed_on_wrong_protocol(self, tmp_path: Path) -> None:
        canary_dir = _write_canary(
            tmp_path,
            _valid_records(),
            _source_identity(protocol_version="1.0"),
        )
        with pytest.raises(LaunchAuthorizationError) as exc:
            validate_pilot_canary_evidence(
                canary_dir=canary_dir,
                expected_source_commit="abcdef1234567890abcdef1234567890abcdef12",
                expected_source_tag="v0.9.22-d13r2-candidate",
                expected_model_identity="qwen:14b-instruct-v1:bnb-nf4:cfg-test",
            )
        assert "protocol_version" in str(exc.value)

    def test_fails_closed_on_wrong_topology(self, tmp_path: Path) -> None:
        records = _valid_records()[:2]  # only one strategy -> wrong count
        canary_dir = _write_canary(tmp_path, records, _source_identity())
        with pytest.raises(LaunchAuthorizationError) as exc:
            validate_pilot_canary_evidence(
                canary_dir=canary_dir,
                expected_source_commit="abcdef1234567890abcdef1234567890abcdef12",
                expected_source_tag="v0.9.22-d13r2-candidate",
                expected_model_identity="qwen:14b-instruct-v1:bnb-nf4:cfg-test",
            )
        assert "records" in str(exc.value) or "strategy_counts" in str(exc.value)

    def test_fails_closed_when_a_repository_is_missing(self, tmp_path: Path) -> None:
        records = _valid_records()
        for record in records:
            record["repository_id"] = "todo"  # all records now Todo -> djangocms/saleor unrepresented
        canary_dir = _write_canary(tmp_path, records, _source_identity())
        with pytest.raises(LaunchAuthorizationError) as exc:
            validate_pilot_canary_evidence(
                canary_dir=canary_dir,
                expected_source_commit="abcdef1234567890abcdef1234567890abcdef12",
                expected_source_tag="v0.9.22-d13r2-candidate",
                expected_model_identity="qwen:14b-instruct-v1:bnb-nf4:cfg-test",
            )
        assert "repo_counts" in str(exc.value) or "djangocms" in str(exc.value) or "saleor" in str(exc.value)

    def test_fails_closed_when_saleor_is_missing(self, tmp_path: Path) -> None:
        records = _valid_records()[:4]  # only todo + djangocms -> saleor missing / cell count 6
        canary_dir = _write_canary(tmp_path, records, _source_identity())
        with pytest.raises(LaunchAuthorizationError) as exc:
            validate_pilot_canary_evidence(
                canary_dir=canary_dir,
                expected_source_commit="abcdef1234567890abcdef1234567890abcdef12",
                expected_source_tag="v0.9.22-d13r2-candidate",
                expected_model_identity="qwen:14b-instruct-v1:bnb-nf4:cfg-test",
            )
        assert "records" in str(exc.value) or "saleor" in str(exc.value)
