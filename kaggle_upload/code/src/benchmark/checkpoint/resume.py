from __future__ import annotations

import shutil
from pathlib import Path

from benchmark.checkpoint.checkpoint import CheckpointData, CheckpointManager
from benchmark.checkpoint.persistence import RunRecordStore


class ResumeValidationError(Exception):
    pass


class ResumeManager:
    def __init__(
        self,
        runs_dir: Path,
        protocol_version: str,
        config_hash: str,
        model_identity: str,
        source_commit: str,
        deployed_build_id: str = "",
    ) -> None:
        self._runs_dir = runs_dir
        self._protocol_version = protocol_version
        self._config_hash = config_hash
        self._model_identity = model_identity
        self._source_commit = source_commit
        self._deployed_build_id = deployed_build_id or source_commit
        self._checkpoint_mgr = CheckpointManager(runs_dir)
        self._record_store = RunRecordStore(runs_dir)

    def checkpoint(self) -> CheckpointManager:
        return self._checkpoint_mgr

    def record_store(self) -> RunRecordStore:
        return self._record_store

    def resume_from(self, previous_results_dir: Path) -> None:
        if not previous_results_dir.is_dir():
            raise ResumeValidationError(f"Previous results directory not found: {previous_results_dir}")

        src_checkpoint = previous_results_dir / "checkpoint.json"
        if not src_checkpoint.is_file():
            raise ResumeValidationError(f"No checkpoint found in {previous_results_dir}")

        src_records = previous_results_dir / "run_records.jsonl"

        self._runs_dir.mkdir(parents=True, exist_ok=True)

        src_cp = CheckpointManager(previous_results_dir)
        cp_data = src_cp.read()
        if cp_data is None:
            raise ResumeValidationError("Could not read checkpoint from previous run")

        self._validate_compatibility(cp_data)

        for src in [src_checkpoint, src_records]:
            if src.is_file():
                dest = self._runs_dir / src.name
                shutil.copy2(str(src), str(dest))

        src_progress = previous_results_dir / "progress.json"
        if src_progress.is_file():
            shutil.copy2(str(src_progress), str(self._runs_dir / "progress.json"))

    def validate_and_get_skip_ids(self) -> set[str]:
        cp_data = self._checkpoint_mgr.read()
        if cp_data is None:
            return set()

        self._validate_compatibility(cp_data)

        # Normalize checkpoint from run records, enforcing invariants:
        #   attempted = succeeded ∪ failed
        #   pending = planned - attempted
        #   succeeded ∩ failed = ∅
        normalized = self._checkpoint_mgr.normalize_from_records(self._record_store)
        if normalized is None:
            return set()

        # Skip set = succeeded ∪ non-retryable failed
        # Retryable failures are NOT skipped — they are retried on resume.
        skip_ids: set[str] = set(normalized.succeeded_run_ids)
        for rid in normalized.failed_run_ids:
            if rid not in normalized.retryable_run_ids:
                skip_ids.add(rid)
        return skip_ids

    def get_normalized_checkpoint(self) -> CheckpointData | None:
        """Return the full normalized checkpoint state for resume.

        Unlike validate_and_get_skip_ids which only returns the skip set,
        this method returns the complete normalized CheckpointData including
        succeeded, failed, retryable, and pending run IDs. The caller must
        use this to initialize the active checkpoint on RESUME so that prior
        state is preserved and extended, never destroyed.
        """
        cp_data = self._checkpoint_mgr.read()
        if cp_data is None:
            return None

        self._validate_compatibility(cp_data)

        normalized = self._checkpoint_mgr.normalize_from_records(self._record_store)
        return normalized

    def _validate_compatibility(self, cp: CheckpointData) -> None:
        mismatches: list[str] = []

        if cp.protocol_version != self._protocol_version:
            mismatches.append(
                f"Protocol version mismatch: checkpoint={cp.protocol_version}, expected={self._protocol_version}"
            )

        if cp.config_hash and self._config_hash and cp.config_hash != self._config_hash:
            mismatches.append(
                f"Config hash mismatch: checkpoint={cp.config_hash}, expected={self._config_hash}"
            )

        if cp.model_identity and self._model_identity and cp.model_identity != self._model_identity:
            mismatches.append(
                f"Model identity mismatch: checkpoint={cp.model_identity}, expected={self._model_identity}"
            )

        if cp.source_commit and self._source_commit and cp.source_commit != self._source_commit:
            mismatches.append(
                f"Source commit mismatch: checkpoint={cp.source_commit}, expected={self._source_commit}"
            )

        if cp.deployed_build_id and self._deployed_build_id and cp.deployed_build_id != self._deployed_build_id:
            mismatches.append(
                f"Deployed build ID mismatch: checkpoint={cp.deployed_build_id}, expected={self._deployed_build_id}"
            )

        if mismatches:
            raise ResumeValidationError("; ".join(mismatches))
