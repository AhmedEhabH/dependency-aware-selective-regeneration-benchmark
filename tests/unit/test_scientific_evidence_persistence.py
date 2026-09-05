from __future__ import annotations

from pathlib import Path

from benchmark.checkpoint.persistence import RunRecordData, RunRecordStore
from benchmark.core.enums import RunStatus
from benchmark.core.models import RunIdentity, RunRecord, TokenUsage


def _make_run_record(*, predicted_actions: dict[str, str] | None = None, changed: list[str] | None = None) -> RunRecord:
    return RunRecord(
        identity=RunIdentity(
            run_id="todo-smoke-001_selective_rep1_abc12345",
            protocol_version="1.0",
            repository_commit_sha="s",
            scenario_id="todo-smoke-001",
            strategy_name="selective",
        ),
        status=RunStatus.succeeded,
        token_usage=TokenUsage(1, 2, 3),
        predicted_actions=dict(predicted_actions or {}),
        changed_artifact_paths=list(changed or []),
    )


def _make_record_data(**over):
    base = {
        "run_id": "todo-smoke-001_selective_rep1_abc12345",
        "profile": "scientific-microstudy-01",
        "repository_id": "todo",
        "scenario_id": "todo-smoke-001",
        "strategy_id": "selective",
        "repetition": 1,
        "seed": 42,
        "status": "succeeded",
    }
    base.update(over)
    return RunRecordData(**base)


class TestPredictedActionsPersistence:
    def test_predicted_actions_survive_jsonl_roundtrip(self, tmp_path: Path) -> None:
        store = RunRecordStore(tmp_path)
        rec = _make_record_data(
            predicted_actions={
                "todo/models.py": "regenerate",
                "todo/serializers.py": "regenerate",
                "todo/views.py": "preserve",
                "todo/permissions.py": "preserve",
                "todo/urls.py": "preserve",
            }
        )
        store.append(rec)
        loaded = store.load_all()[0]
        assert loaded.predicted_actions == {
            "todo/models.py": "regenerate",
            "todo/serializers.py": "regenerate",
            "todo/views.py": "preserve",
            "todo/permissions.py": "preserve",
            "todo/urls.py": "preserve",
        }

    def test_predicted_actions_default_empty(self, tmp_path: Path) -> None:
        store = RunRecordStore(tmp_path)
        rec = _make_record_data()
        store.append(rec)
        loaded = store.load_all()[0]
        assert loaded.predicted_actions == {}


class TestChangedArtifactPathsPersistence:
    def test_changed_artifact_paths_survive_jsonl_roundtrip(self, tmp_path: Path) -> None:
        store = RunRecordStore(tmp_path)
        rec = _make_record_data(
            changed_artifact_paths=["todo/models.py", "todo/serializers.py"],
            generated_migration_paths=["todo/migrations/0003_auto_20260905.py"],
        )
        store.append(rec)
        loaded = store.load_all()[0]
        assert loaded.changed_artifact_paths == ["todo/models.py", "todo/serializers.py"]
        assert loaded.generated_migration_paths == ["todo/migrations/0003_auto_20260905.py"]

    def test_changed_artifact_paths_default_empty(self, tmp_path: Path) -> None:
        store = RunRecordStore(tmp_path)
        rec = _make_record_data()
        store.append(rec)
        loaded = store.load_all()[0]
        assert loaded.changed_artifact_paths == []

    def test_migrations_kept_separate_from_changed_artifact_paths(self, tmp_path: Path) -> None:
        store = RunRecordStore(tmp_path)
        rec = _make_record_data(
            changed_artifact_paths=["todo/models.py"],
            generated_migration_paths=["todo/migrations/0003_foo.py"],
        )
        store.append(rec)
        loaded = store.load_all()[0]
        assert "todo/migrations/0003_foo.py" not in loaded.changed_artifact_paths
        assert "todo/migrations/0003_foo.py" in loaded.generated_migration_paths


class TestRunRecordToRecordDataLinkage:
    def test_seven_arm_record_to_run_record_data_forward_fields(self) -> None:
        """The single entry-point conversion in seven_arm_benchmark forwards both fields."""
        import seven_arm_benchmark

        record = _make_run_record(
            predicted_actions={"todo/models.py": "regenerate"},
            changed=["todo/models.py"],
        )
        record_dict = {
            "predicted_actions": dict(record.predicted_actions),
            "changed_artifact_paths": list(record.changed_artifact_paths),
        }
        data = seven_arm_benchmark._to_run_record_data(
            record_dict,
            run_id="r1",
            profile="scientific-microstudy-01",
            repository_id="todo",
            scenario_id="todo-smoke-001",
            strategy_id="selective",
            repetition=1,
            model_identity="openrouter:m@p",
            dry_run=False,
            protocol_version="1.0",
            source_commit="s",
            config_hash="h" * 16,
            started_at="",
            ended_at="",
            hw_id="cpu",
            sw_id="py",
            max_attempts=3,
        )
        assert data.predicted_actions == {"todo/models.py": "regenerate"}
        assert data.changed_artifact_paths == ["todo/models.py"]

    def test_run_record_data_prefers_explicit_fields_over_defaults(self) -> None:
        import seven_arm_benchmark

        data = seven_arm_benchmark._to_run_record_data(
            {"predicted_actions": {}, "changed_artifact_paths": []},
            run_id="r1",
            profile="x",
            repository_id="todo",
            scenario_id="s",
            strategy_id="selective",
            repetition=1,
            model_identity="m",
            dry_run=False,
            protocol_version="1.0",
            source_commit="s",
            config_hash="h" * 16,
            started_at="",
            ended_at="",
            hw_id="cpu",
            sw_id="py",
            max_attempts=3,
        )
        assert data.predicted_actions == {}
        assert data.changed_artifact_paths == []
