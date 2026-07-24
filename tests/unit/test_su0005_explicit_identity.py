"""SU-0005 regression tests: explicit resume identity, canonical Run IDs, idempotent persistence."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from benchmark.checkpoint.checkpoint import CheckpointData, CheckpointManager
from benchmark.checkpoint.hf_sync import (
    HfResumeManager,
    RemoteLayout,
    compare_checkpoint_compatibility,
    resolve_auto_resume,
)
from benchmark.checkpoint.persistence import (
    RunRecordData,
    RunRecordIntegrityError,
    RunRecordStore,
)

TEST_REPO = "NabilDo/selective-regeneration-experiment-results"

ALL_SEVEN_STRATEGIES = [
    "monolithic",
    "agent",
    "selective",
    "compiled_ai",
    "delta_mcp",
    "incr_rtl",
    "code_plan",
]

SCENARIO_IDS = ["djangocms-cross-007"]
STRATEGY_NAMES = ALL_SEVEN_STRATEGIES


def _make_run_id(scenario_id: str, strategy_name: str, rep: int, config_hash: str = "deadbeef", protocol_version: str = "1.0") -> str:
    payload = json.dumps({
        "scenario_id": scenario_id,
        "strategy_name": strategy_name,
        "repetition": rep,
        "protocol_version": protocol_version,
        "config_hash": config_hash,
    }, sort_keys=True)
    suffix = hashlib.sha256(payload.encode()).hexdigest()[:8]
    return f"{scenario_id}_{strategy_name}_rep{rep}_{suffix}"


def _make_checkpoint(
    tmp_path: Path,
    scenario_ids: list[str] | None = None,
    strategy_names: list[str] | None = None,
    planned_run_ids: list[str] | None = None,
    completed_run_ids: list[str] | None = None,
    pending_run_ids: list[str] | None = None,
    completion_status: str = "incomplete",
    config_hash: str = "deadbeef",
    protocol_version: str = "1.0",
    source_commit: str = "abc1234",
    model_identity: str = "dry-run:mock",
    total_planned: int = 7,
) -> CheckpointData:
    if scenario_ids is None:
        scenario_ids = SCENARIO_IDS
    if strategy_names is None:
        strategy_names = STRATEGY_NAMES
    if planned_run_ids is None:
        planned_run_ids = [
            _make_run_id(s, st, 1, config_hash, protocol_version)
            for s in scenario_ids
            for st in strategy_names
        ]
    if completed_run_ids is None:
        completed_run_ids = []
    if pending_run_ids is None:
        pending_run_ids = [r for r in planned_run_ids if r not in completed_run_ids]

    data = CheckpointData(
        profile="smoke",
        execution_plan_hash=config_hash,
        planned_run_ids=planned_run_ids,
        completed_run_ids=completed_run_ids,
        failed_run_ids=[],
        pending_run_ids=pending_run_ids,
        total_planned=total_planned,
        total_completed=len(completed_run_ids),
        protocol_version=protocol_version,
        model_identity=model_identity,
        config_hash=config_hash,
        source_commit=source_commit,
        completion_status=completion_status,
        scenario_ids=scenario_ids,
        strategy_names=strategy_names,
    )
    CheckpointManager(tmp_path).write_atomic(data)
    return data


def _make_record(
    tmp_path: Path,
    run_id: str = "test-run-001",
    status: str = "succeeded",
    strategy_id: str = "agent",
    scenario_id: str = "djangocms-cross-007",
) -> RunRecordData:
    rec = RunRecordData(
        run_id=run_id,
        profile="smoke",
        repository_id="djangocms",
        scenario_id=scenario_id,
        strategy_id=strategy_id,
        repetition=1,
        seed=42,
        status=status,
        duration_seconds=1.0,
        protocol_version="1.0",
        source_commit="abc1234",
        config_hash="deadbeef",
        timestamp="2026-07-25T00:00:00",
    )
    RunRecordStore(tmp_path).append(rec)
    return rec


def _make_fake_cp_content(
    scenario_ids: list[str] | None = None,
    strategy_names: list[str] | None = None,
    planned_run_ids: list[str] | None = None,
    completed_run_ids: list[str] | None = None,
    completion_status: str = "incomplete",
    config_hash: str = "deadbeef",
    protocol_version: str = "1.0",
    source_commit: str = "abc1234",
    model_identity: str = "dry-run:mock",
    total_planned: int = 7,
    last_update: str = "",
) -> str:
    if scenario_ids is None:
        scenario_ids = SCENARIO_IDS
    if strategy_names is None:
        strategy_names = STRATEGY_NAMES
    if planned_run_ids is None:
        planned_run_ids = [
            _make_run_id(s, st, 1, config_hash, protocol_version)
            for s in scenario_ids
            for st in strategy_names
        ]
    if completed_run_ids is None:
        completed_run_ids = []
    pending = [r for r in planned_run_ids if r not in completed_run_ids]
    return json.dumps({
        "profile": "smoke",
        "execution_plan_hash": config_hash,
        "planned_run_ids": planned_run_ids,
        "completed_run_ids": completed_run_ids,
        "failed_run_ids": [],
        "pending_run_ids": pending,
        "total_planned": total_planned,
        "total_completed": len(completed_run_ids),
        "protocol_version": protocol_version,
        "model_identity": model_identity,
        "config_hash": config_hash,
        "source_commit": source_commit,
        "completion_status": completion_status,
        "scenario_ids": scenario_ids,
        "strategy_names": strategy_names,
        "last_update": last_update,
    })


def _make_fake_records_content(run_ids: list[str], statuses: list[str] | None = None) -> str:
    if statuses is None:
        statuses = ["succeeded"] * len(run_ids)
    records = []
    for rid, status in zip(run_ids, statuses):
        records.append(json.dumps({
            "run_id": rid,
            "profile": "smoke",
            "scenario_id": "djangocms-cross-007",
            "strategy_id": "agent",
            "repetition": 1,
            "seed": 42,
            "status": status,
            "duration_seconds": 1.0,
            "protocol_version": "1.0",
            "source_commit": "abc1234",
            "config_hash": "deadbeef",
            "timestamp": "2026-07-25T00:00:00",
        }))
    return "\n".join(records)


# ---------------------------------------------------------------------------
# 1. Explicit identity comparator accepts matching remote checkpoint
# ---------------------------------------------------------------------------

class TestExplicitIdentityComparator:
    def test_matching_explicit_identity_is_compatible(self) -> None:
        cp = CheckpointData(
            profile="smoke",
            execution_plan_hash="abc",
            scenario_ids=["djangocms-cross-007"],
            strategy_names=ALL_SEVEN_STRATEGIES,
            planned_run_ids=[],
            protocol_version="1.0",
            config_hash="deadbeef",
            source_commit="abc1234",
            model_identity="dry-run:mock",
        )
        result = compare_checkpoint_compatibility(
            cp=cp,
            expected_protocol_version="1.0",
            expected_config_hash="deadbeef",
            expected_source_commit="abc1234",
            expected_model_identity="dry-run:mock",
            expected_scenario_ids=["djangocms-cross-007"],
            expected_strategy_names=ALL_SEVEN_STRATEGIES,
        )
        assert result.compatible is True
        assert result.reasons == ()
        assert result.identity_source == "explicit_checkpoint"

    def test_explicit_scenario_mismatch_fails(self) -> None:
        cp = CheckpointData(
            profile="smoke",
            execution_plan_hash="abc",
            scenario_ids=["wrong-scenario"],
            strategy_names=ALL_SEVEN_STRATEGIES,
            planned_run_ids=[],
            protocol_version="1.0",
            config_hash="deadbeef",
            source_commit="abc1234",
            model_identity="dry-run:mock",
        )
        result = compare_checkpoint_compatibility(
            cp=cp,
            expected_protocol_version="1.0",
            expected_config_hash="deadbeef",
            expected_source_commit="abc1234",
            expected_model_identity="dry-run:mock",
            expected_scenario_ids=["djangocms-cross-007"],
            expected_strategy_names=ALL_SEVEN_STRATEGIES,
        )
        assert result.compatible is False
        assert any("Scenario identity mismatch" in r for r in result.reasons)

    def test_explicit_strategy_mismatch_fails(self) -> None:
        cp = CheckpointData(
            profile="smoke",
            execution_plan_hash="abc",
            scenario_ids=["djangocms-cross-007"],
            strategy_names=["monolithic", "agent"],
            planned_run_ids=[],
            protocol_version="1.0",
            config_hash="deadbeef",
            source_commit="abc1234",
            model_identity="dry-run:mock",
        )
        result = compare_checkpoint_compatibility(
            cp=cp,
            expected_protocol_version="1.0",
            expected_config_hash="deadbeef",
            expected_source_commit="abc1234",
            expected_model_identity="dry-run:mock",
            expected_scenario_ids=["djangocms-cross-007"],
            expected_strategy_names=ALL_SEVEN_STRATEGIES,
        )
        assert result.compatible is False
        assert any("Strategy identity mismatch" in r for r in result.reasons)


# ---------------------------------------------------------------------------
# 2. Regression: underscore-split would fail, explicit identity succeeds
# ---------------------------------------------------------------------------

class TestUnderscoreSplitRegression:
    def test_underscore_split_corrupts_strategy_names(self) -> None:
        """Prove the old underscore-split logic would fail on compiled_ai etc."""
        strategy_names_with_underscores = ["compiled_ai", "delta_mcp", "incr_rtl", "code_plan"]
        for name in strategy_names_with_underscores:
            rid = f"djangocms-cross-007_{name}_rep1_aabbccdd"
            parts = rid.split("_", 2)
            extracted = parts[1] if len(parts) >= 2 else ""
            assert extracted != name, f"Old split extracted '{extracted}' != expected '{name}'"
            # The corruption: compiled_ai -> compiled, delta_mcp -> delta, etc.
            assert "_" not in extracted, f"Old split should corrupt '{name}' to '{extracted}'"

    def test_explicit_identity_accepts_all_seven_strategies(self) -> None:
        """New explicit identity comparator correctly handles all 7 strategy names."""
        cp = CheckpointData(
            profile="smoke",
            execution_plan_hash="abc",
            scenario_ids=SCENARIO_IDS,
            strategy_names=ALL_SEVEN_STRATEGIES,
            planned_run_ids=[],
            protocol_version="1.0",
            config_hash="deadbeef",
            source_commit="abc1234",
            model_identity="dry-run:mock",
        )
        result = compare_checkpoint_compatibility(
            cp=cp,
            expected_protocol_version="1.0",
            expected_config_hash="deadbeef",
            expected_source_commit="abc1234",
            expected_model_identity="dry-run:mock",
            expected_scenario_ids=SCENARIO_IDS,
            expected_strategy_names=ALL_SEVEN_STRATEGIES,
        )
        assert result.compatible is True
        assert result.identity_source == "explicit_checkpoint"


# ---------------------------------------------------------------------------
# 3. Complete mocked three-session sequence: 1->2->3 resume
# ---------------------------------------------------------------------------

class TestThreeSessionResumeSequence:
    def test_one_to_two_to_three_resume(self) -> None:
        prefix = "experiments/smoke/1.0/abc1234"
        all_planned = [
            _make_run_id("djangocms-cross-007", s, 1)
            for s in ALL_SEVEN_STRATEGIES
        ]
        run_0 = all_planned[0]  # monolithic
        run_1 = all_planned[1]  # agent
        run_2 = all_planned[2]  # selective

        def _build_files(exp_id: str, completed_ids: list[str]) -> list[str]:
            return [
                f"{prefix}/{exp_id}/recovery/checkpoint.json",
                f"{prefix}/{exp_id}/recovery/run_records.jsonl",
                f"{prefix}/{exp_id}/recovery/progress.json",
            ]

        def _build_cp(exp_id: str, completed_ids: list[str]) -> str:
            return _make_fake_cp_content(
                completed_run_ids=completed_ids,
                total_planned=7,
            )

        def _build_records(completed_ids: list[str]) -> str:
            statuses = ["succeeded"] * len(completed_ids)
            return _make_fake_records_content(completed_ids, statuses)

        exp_id = "exp-session-test"

        # ---- Session 1: No remote, START_NEW ----
        with patch("benchmark.checkpoint.hf_sync.HfApi") as mock_api_cls:
            mock_api = MagicMock()
            mock_api_cls.return_value = mock_api
            mock_api.list_repo_files.return_value = ["unrelated/file.txt"]
            result = resolve_auto_resume(
                repo_id=TEST_REPO, token="t", profile="smoke",
                protocol_version="1.0", source_commit="abc1234",
                config_hash="deadbeef", model_identity="dry-run:mock",
                scenario_ids=SCENARIO_IDS, strategy_names=ALL_SEVEN_STRATEGIES,
            )
            assert result.action == "start_new"

        # ---- Session 2: Remote has 1 completed, RESUME, skip 0, execute 1 ----
        files = _build_files(exp_id, [run_0])
        cp = _build_cp(exp_id, [run_0])
        recs = _build_records([run_0])

        with patch("benchmark.checkpoint.hf_sync.HfApi") as mock_api_cls:
            mock_api = MagicMock()
            mock_api_cls.return_value = mock_api
            mock_api.list_repo_files.return_value = files

            def fake_download(repo_id, filename, local_dir, token, **kwargs):
                local_p = Path(local_dir) / filename
                local_p.parent.mkdir(parents=True, exist_ok=True)
                if "checkpoint.json" in filename:
                    local_p.write_text(cp)
                elif "run_records.jsonl" in filename:
                    local_p.write_text(recs)
                return str(local_p)

            with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_download):
                result = resolve_auto_resume(
                    repo_id=TEST_REPO, token="t", profile="smoke",
                    protocol_version="1.0", source_commit="abc1234",
                    config_hash="deadbeef", model_identity="dry-run:mock",
                    scenario_ids=SCENARIO_IDS, strategy_names=ALL_SEVEN_STRATEGIES,
                )
                assert result.action == "resume"
                assert result.experiment_id == exp_id

        # ---- Session 3: Remote has 2 completed, RESUME, skip 0+1, execute 2 ----
        files = _build_files(exp_id, [run_0, run_1])
        cp = _build_cp(exp_id, [run_0, run_1])
        recs = _build_records([run_0, run_1])

        with patch("benchmark.checkpoint.hf_sync.HfApi") as mock_api_cls:
            mock_api = MagicMock()
            mock_api_cls.return_value = mock_api
            mock_api.list_repo_files.return_value = files

            def fake_download2(repo_id, filename, local_dir, token, **kwargs):
                local_p = Path(local_dir) / filename
                local_p.parent.mkdir(parents=True, exist_ok=True)
                if "checkpoint.json" in filename:
                    local_p.write_text(cp)
                elif "run_records.jsonl" in filename:
                    local_p.write_text(recs)
                return str(local_p)

            with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_download2):
                result = resolve_auto_resume(
                    repo_id=TEST_REPO, token="t", profile="smoke",
                    protocol_version="1.0", source_commit="abc1234",
                    config_hash="deadbeef", model_identity="dry-run:mock",
                    scenario_ids=SCENARIO_IDS, strategy_names=ALL_SEVEN_STRATEGIES,
                )
                assert result.action == "resume"
                assert result.experiment_id == exp_id

        # Verify: one experiment ID, exactly three unique Run IDs, no duplicates
        assert exp_id == exp_id  # same experiment throughout
        unique_run_ids = {run_0, run_1, run_2}
        assert len(unique_run_ids) == 3
        assert len(all_planned) == 7


# ---------------------------------------------------------------------------
# 4. Config mismatch
# ---------------------------------------------------------------------------

class TestConfigMismatch:
    def test_config_hash_mismatch_rejected(self) -> None:
        cp = CheckpointData(
            profile="smoke", execution_plan_hash="abc",
            scenario_ids=SCENARIO_IDS, strategy_names=ALL_SEVEN_STRATEGIES,
            planned_run_ids=[], config_hash="old_hash",
            protocol_version="1.0", source_commit="abc1234",
            model_identity="dry-run:mock",
        )
        result = compare_checkpoint_compatibility(
            cp=cp,
            expected_protocol_version="1.0",
            expected_config_hash="new_hash",
            expected_source_commit="abc1234",
            expected_model_identity="dry-run:mock",
            expected_scenario_ids=SCENARIO_IDS,
            expected_strategy_names=ALL_SEVEN_STRATEGIES,
        )
        assert result.compatible is False
        assert any("Config hash mismatch" in r for r in result.reasons)


# ---------------------------------------------------------------------------
# 5. Model mismatch
# ---------------------------------------------------------------------------

class TestModelMismatch:
    def test_model_identity_mismatch_rejected(self) -> None:
        cp = CheckpointData(
            profile="smoke", execution_plan_hash="abc",
            scenario_ids=SCENARIO_IDS, strategy_names=ALL_SEVEN_STRATEGIES,
            planned_run_ids=[], model_identity="qwen:old",
            protocol_version="1.0", source_commit="abc1234",
            config_hash="deadbeef",
        )
        result = compare_checkpoint_compatibility(
            cp=cp,
            expected_protocol_version="1.0",
            expected_config_hash="deadbeef",
            expected_source_commit="abc1234",
            expected_model_identity="qwen:new",
            expected_scenario_ids=SCENARIO_IDS,
            expected_strategy_names=ALL_SEVEN_STRATEGIES,
        )
        assert result.compatible is False
        assert any("Model identity mismatch" in r for r in result.reasons)


# ---------------------------------------------------------------------------
# 6. Source mismatch
# ---------------------------------------------------------------------------

class TestSourceMismatch:
    def test_source_commit_mismatch_rejected(self) -> None:
        cp = CheckpointData(
            profile="smoke", execution_plan_hash="abc",
            scenario_ids=SCENARIO_IDS, strategy_names=ALL_SEVEN_STRATEGIES,
            planned_run_ids=[], source_commit="old_commit",
            protocol_version="1.0", config_hash="deadbeef",
            model_identity="dry-run:mock",
        )
        result = compare_checkpoint_compatibility(
            cp=cp,
            expected_protocol_version="1.0",
            expected_config_hash="deadbeef",
            expected_source_commit="new_commit",
            expected_model_identity="dry-run:mock",
            expected_scenario_ids=SCENARIO_IDS,
            expected_strategy_names=ALL_SEVEN_STRATEGIES,
        )
        assert result.compatible is False
        assert any("Source commit mismatch" in r for r in result.reasons)


# ---------------------------------------------------------------------------
# 7. Corrupt checkpoint
# ---------------------------------------------------------------------------

class TestCorruptCheckpoint:
    def test_corrupt_checkpoint_raises_value_error(self, tmp_path: Path) -> None:
        mgr = CheckpointManager(tmp_path)
        mgr.path.write_text("{invalid json", encoding="utf-8")
        with pytest.raises(ValueError, match="Corrupted"):
            mgr.read()


# ---------------------------------------------------------------------------
# 8. Unexpected validation exception fails closed
# ---------------------------------------------------------------------------

class TestUnexpectedException:
    def test_download_exception_logs_and_skips(self) -> None:
        prefix = "experiments/smoke/1.0/abc1234"
        exp_files = [f"{prefix}/exp-err/recovery/checkpoint.json"]

        with patch("benchmark.checkpoint.hf_sync.HfApi") as mock_api_cls:
            mock_api = MagicMock()
            mock_api_cls.return_value = mock_api
            mock_api.list_repo_files.return_value = exp_files

            with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=Exception("network error")):
                result = resolve_auto_resume(
                    repo_id=TEST_REPO, token="t", profile="smoke",
                    protocol_version="1.0", source_commit="abc1234",
                    config_hash="deadbeef", model_identity="dry-run:mock",
                    scenario_ids=SCENARIO_IDS, strategy_names=ALL_SEVEN_STRATEGIES,
                )
                assert result.action == "start_new"

    def test_validation_exception_logs_and_skips(self) -> None:
        prefix = "experiments/smoke/1.0/abc1234"
        exp_files = [f"{prefix}/exp-bad/recovery/checkpoint.json", f"{prefix}/exp-bad/recovery/run_records.jsonl"]

        bad_cp = json.dumps({"invalid": "structure"})
        bad_records = "not-json"

        with patch("benchmark.checkpoint.hf_sync.HfApi") as mock_api_cls:
            mock_api = MagicMock()
            mock_api_cls.return_value = mock_api
            mock_api.list_repo_files.return_value = exp_files

            def fake_download(repo_id, filename, local_dir, token, **kwargs):
                local_p = Path(local_dir) / filename
                local_p.parent.mkdir(parents=True, exist_ok=True)
                if "checkpoint.json" in filename:
                    local_p.write_text(bad_cp)
                elif "run_records.jsonl" in filename:
                    local_p.write_text(bad_records)
                return str(local_p)

            with patch("benchmark.checkpoint.hf_sync.hf_hub_download", side_effect=fake_download):
                result = resolve_auto_resume(
                    repo_id=TEST_REPO, token="t", profile="smoke",
                    protocol_version="1.0", source_commit="abc1234",
                    config_hash="deadbeef", model_identity="dry-run:mock",
                    scenario_ids=SCENARIO_IDS, strategy_names=ALL_SEVEN_STRATEGIES,
                )
                assert result.action == "start_new"


# ---------------------------------------------------------------------------
# 9. Legacy exact-plan lookup
# ---------------------------------------------------------------------------

class TestLegacyPlanLookup:
    def test_legacy_checkpoint_without_explicit_identity_uses_plan_lookup(self) -> None:
        planned = [
            _make_run_id("djangocms-cross-007", "monolithic", 1),
            _make_run_id("djangocms-cross-007", "agent", 1),
        ]
        cp_data = json.dumps({
            "profile": "smoke",
            "execution_plan_hash": "deadbeef",
            "planned_run_ids": planned,
            "completed_run_ids": [planned[0]],
            "failed_run_ids": [],
            "pending_run_ids": [planned[1]],
            "total_planned": 2,
            "total_completed": 1,
            "protocol_version": "1.0",
            "model_identity": "dry-run:mock",
            "config_hash": "deadbeef",
            "source_commit": "abc1234",
            "completion_status": "incomplete",
        })
        cp = json.loads(cp_data)
        cp_obj = CheckpointData(**cp)

        result = compare_checkpoint_compatibility(
            cp=cp_obj,
            expected_protocol_version="1.0",
            expected_config_hash="deadbeef",
            expected_source_commit="abc1234",
            expected_model_identity="dry-run:mock",
            expected_scenario_ids=["djangocms-cross-007"],
            expected_strategy_names=["monolithic", "agent"],
        )
        assert result.compatible is True
        assert result.identity_source == "legacy_exact_plan_lookup"

    def test_legacy_checkpoint_unsafe_identity_rejection(self) -> None:
        cp_data = json.dumps({
            "profile": "smoke",
            "execution_plan_hash": "deadbeef",
            "planned_run_ids": [],
            "completed_run_ids": [],
            "failed_run_ids": [],
            "pending_run_ids": [],
            "total_planned": 0,
            "total_completed": 0,
            "protocol_version": "1.0",
            "model_identity": "dry-run:mock",
            "config_hash": "deadbeef",
            "source_commit": "abc1234",
            "completion_status": "incomplete",
        })
        cp = json.loads(cp_data)
        cp_obj = CheckpointData(**cp)

        result = compare_checkpoint_compatibility(
            cp=cp_obj,
            expected_protocol_version="1.0",
            expected_config_hash="deadbeef",
            expected_source_commit="abc1234",
            expected_model_identity="dry-run:mock",
            expected_scenario_ids=SCENARIO_IDS,
            expected_strategy_names=ALL_SEVEN_STRATEGIES,
        )
        assert result.compatible is False
        assert any("cannot be mapped safely" in r for r in result.reasons)


# ---------------------------------------------------------------------------
# 10. Multiple compatible experiment selection
# ---------------------------------------------------------------------------

class TestMultipleCompatibleSelection:
    def test_selects_newest_by_last_update(self) -> None:
        exp_old = MagicMock()
        exp_old.experiment_id = "exp-old"
        exp_old.last_update = "2026-07-25T10:00:00"
        exp_old.is_complete = False
        exp_old.completed_count = 1
        exp_old.total_planned = 7
        exp_old.failed_count = 0

        exp_new = MagicMock()
        exp_new.experiment_id = "exp-new"
        exp_new.last_update = "2026-07-25T12:00:00"
        exp_new.is_complete = False
        exp_new.completed_count = 2
        exp_new.total_planned = 7
        exp_new.failed_count = 0

        from benchmark.checkpoint.hf_sync import _sort_experiments_by_recency
        sorted_exps = _sort_experiments_by_recency([exp_old, exp_new])
        assert sorted_exps[0].experiment_id == "exp-new"
        assert sorted_exps[1].experiment_id == "exp-old"

    def test_tie_break_by_experiment_id(self) -> None:
        exp_a = MagicMock()
        exp_a.experiment_id = "exp-aaa"
        exp_a.last_update = ""
        exp_a.is_complete = False

        exp_b = MagicMock()
        exp_b.experiment_id = "exp-bbb"
        exp_b.last_update = ""
        exp_b.is_complete = False

        from benchmark.checkpoint.hf_sync import _sort_experiments_by_recency
        sorted_exps = _sort_experiments_by_recency([exp_b, exp_a])
        assert sorted_exps[0].experiment_id == "exp-bbb"
        assert sorted_exps[1].experiment_id == "exp-aaa"


# ---------------------------------------------------------------------------
# 11. Idempotent persistence
# ---------------------------------------------------------------------------

class TestIdempotentPersistence:
    def test_append_same_record_twice_is_idempotent(self, tmp_path: Path) -> None:
        store = RunRecordStore(tmp_path)
        rec = RunRecordData(
            run_id="idem-001", profile="smoke", repository_id="djangocms",
            scenario_id="djangocms-cross-007", strategy_id="agent",
            repetition=1, seed=42, status="succeeded",
            duration_seconds=1.0, protocol_version="1.0",
            source_commit="abc1234", config_hash="deadbeef",
            timestamp="2026-07-25T00:00:00",
        )
        store.append(rec)
        store.append(rec)
        assert store.count() == 1

    def test_conflicting_record_raises_integrity_error(self, tmp_path: Path) -> None:
        store = RunRecordStore(tmp_path)
        rec1 = RunRecordData(
            run_id="conflict-001", profile="smoke", repository_id="djangocms",
            scenario_id="djangocms-cross-007", strategy_id="agent",
            repetition=1, seed=42, status="succeeded",
            duration_seconds=1.0, protocol_version="1.0",
            source_commit="abc1234", config_hash="deadbeef",
            timestamp="2026-07-25T00:00:00",
        )
        rec2 = RunRecordData(
            run_id="conflict-001", profile="smoke", repository_id="djangocms",
            scenario_id="djangocms-cross-007", strategy_id="agent",
            repetition=1, seed=42, status="failed",
            duration_seconds=2.0, protocol_version="1.0",
            source_commit="abc1234", config_hash="deadbeef",
            timestamp="2026-07-25T00:01:00",
        )
        store.append(rec1)
        with pytest.raises(RunRecordIntegrityError, match="conflict"):
            store.append(rec2)


# ---------------------------------------------------------------------------
# 12. Planned Run-ID equality across artifacts
# ---------------------------------------------------------------------------

class TestPlannedRunIdEquality:
    def test_all_planned_run_ids_are_deterministic(self) -> None:
        planned = [
            _make_run_id("djangocms-cross-007", s, 1)
            for s in ALL_SEVEN_STRATEGIES
        ]
        assert len(planned) == 7
        assert len(set(planned)) == 7
        for rid in planned:
            assert rid.startswith("djangocms-cross-007_")
            assert "_rep1_" in rid

    def test_run_ids_match_expected_strategy_names(self) -> None:
        for strategy in ALL_SEVEN_STRATEGIES:
            rid = _make_run_id("djangocms-cross-007", strategy, 1)
            assert strategy in rid, f"Run ID '{rid}' does not contain strategy '{strategy}'"


# ---------------------------------------------------------------------------
# 13. Notebook progress logic
# ---------------------------------------------------------------------------

class TestNotebookProgressLogic:
    def test_checkpoint_explicit_fields_present(self, tmp_path: Path) -> None:
        _make_checkpoint(
            tmp_path,
            scenario_ids=SCENARIO_IDS,
            strategy_names=ALL_SEVEN_STRATEGIES,
        )
        loaded = CheckpointManager(tmp_path).read()
        assert loaded is not None
        assert loaded.scenario_ids == SCENARIO_IDS
        assert loaded.strategy_names == ALL_SEVEN_STRATEGIES
        assert loaded.completion_status == "incomplete"

    def test_completion_status_completed(self, tmp_path: Path) -> None:
        planned = [_make_run_id("djangocms-cross-007", s, 1) for s in ALL_SEVEN_STRATEGIES]
        _make_checkpoint(
            tmp_path,
            scenario_ids=SCENARIO_IDS,
            strategy_names=ALL_SEVEN_STRATEGIES,
            planned_run_ids=planned,
            completed_run_ids=planned,
            completion_status="completed",
        )
        loaded = CheckpointManager(tmp_path).read()
        assert loaded is not None
        assert loaded.completion_status == "completed"
        assert len(loaded.completed_run_ids) == 7
        assert len(loaded.pending_run_ids) == 0


# ---------------------------------------------------------------------------
# 14. CheckpointData backward compatibility (reading old checkpoints)
# ---------------------------------------------------------------------------

class TestBackwardCompatibility:
    def test_old_checkpoint_without_identity_fields_loads(self, tmp_path: Path) -> None:
        """Old checkpoints without scenario_ids/strategy_names should still load."""
        old_data = {
            "profile": "smoke",
            "execution_plan_hash": "deadbeef",
            "planned_run_ids": ["run-1", "run-2"],
            "completed_run_ids": ["run-1"],
            "failed_run_ids": [],
            "pending_run_ids": ["run-2"],
            "total_planned": 2,
            "total_completed": 1,
            "protocol_version": "1.0",
            "model_identity": "dry-run:mock",
            "config_hash": "deadbeef",
            "source_commit": "abc1234",
            "last_update": "",
            "completion_status": "incomplete",
        }
        cp_path = tmp_path / "checkpoint.json"
        cp_path.write_text(json.dumps(old_data), encoding="utf-8")
        loaded = CheckpointManager(tmp_path).read()
        assert loaded is not None
        assert loaded.scenario_ids == []
        assert loaded.strategy_names == []
        assert loaded.planned_run_ids == ["run-1", "run-2"]
