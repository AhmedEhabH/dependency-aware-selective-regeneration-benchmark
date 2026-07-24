from __future__ import annotations

import hashlib
import json
import logging
import os
import posixpath
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from huggingface_hub import HfApi, hf_hub_download
from huggingface_hub.utils import RepositoryNotFoundError

from benchmark.checkpoint.checkpoint import CheckpointManager, ProgressManager
from benchmark.checkpoint.persistence import RunRecordStore

logger = logging.getLogger("benchmark.hf_sync")

RECOVERY_FILES: tuple[str, ...] = (
    "run_records.jsonl",
    "checkpoint.json",
    "progress.json",
    "benchmark_summary.partial.json",
    "experiment_id.txt",
    "source_identity.json",
)

DRY_RUN_REPO_ID = "validkhv/placeholder-mirror"


# ---------------------------------------------------------------------------
# Security filter
# ---------------------------------------------------------------------------

ALLOWLIST_PREFIXES: tuple[str, ...] = (
    "run_records.jsonl",
    "checkpoint.json",
    "progress.json",
    "benchmark_summary",
    "MANIFEST.json",
    "manifest.json",
    "environment_metadata.json",
    "failure_records.json",
    "remote_sync.json",
    "remote_sync_failure.json",
    "experiment_id.txt",
    "source_identity.json",
    "COMPLETED",
)

DENYLIST_PATTERNS: tuple[str, ...] = (
    ".hf_token",
    ".token",
    "token",
    "secret",
    "credentials",
    ".netrc",
    ".aws",
    ".gcp",
    "model.safetensors",
    "model.bin",
    "pytorch_model",
    ".cache",
    "huggingface",
    "snapshots",
    "blobs",
    "test_",
    "hidden_test",
    "ground_truth",
    ".ssh",
    ".kaggle",
    "C:",
    "D:",
    "Windows",
    "Program Files",
)


def _is_path_allowed(local_path: Path, runs_dir: Path) -> bool:
    try:
        local_path.resolve().relative_to(runs_dir.resolve())
    except ValueError:
        return False

    name = local_path.name
    lower = name.lower()

    for pat in DENYLIST_PATTERNS:
        if pat in lower:
            return False

    for prefix in ALLOWLIST_PREFIXES:
        if lower.startswith(prefix.lower()):
            return True

    return False


# ---------------------------------------------------------------------------
# Remote layout builder
# ---------------------------------------------------------------------------


@dataclass
class RemoteLayout:
    profile: str
    protocol_version: str
    source_commit: str
    experiment_id: str

    def __post_init__(self) -> None:
        _parts = [self.profile, self.protocol_version, self.source_commit, self.experiment_id]
        for i, part in enumerate(_parts):
            if not part:
                names = ["profile", "protocol_version", "source_commit", "experiment_id"]
                raise ValueError(
                    f"RemoteLayout component '{names[i]}' must not be empty"
                )

    def _base(self) -> str:
        return posixpath.join(
            "experiments",
            self.profile,
            self.protocol_version,
            self.source_commit,
            self.experiment_id,
        )

    def recovery(self) -> str:
        return posixpath.join(self._base(), "recovery")

    def snapshot(self, chunk_number: int) -> str:
        return posixpath.join(
            self._base(), "snapshots", f"chunk-{chunk_number:04d}"
        )

    def final(self) -> str:
        return posixpath.join(self._base(), "final")


# ---------------------------------------------------------------------------
# Sync failure record
# ---------------------------------------------------------------------------


@dataclass
class SyncFailureRecord:
    stage: str
    remote_path: str
    error: str
    timestamp: str = ""
    local_checkpoint_ok: bool = False


class SyncFailureStore:
    def __init__(self, runs_dir: Path) -> None:
        self._path = runs_dir / "remote_sync_failure.json"

    def record_failure(self, record: SyncFailureRecord) -> None:
        existing: list[dict[str, Any]] = []
        if self._path.is_file():
            try:
                existing = json.loads(self._path.read_text())
            except (json.JSONDecodeError, TypeError):
                existing = []
        existing.append(asdict(record))
        self._path.write_text(json.dumps(existing, indent=2), encoding="utf-8")

    def has_failures(self) -> bool:
        return self._path.is_file() and self._path.stat().st_size > 0

    def clear(self) -> None:
        if self._path.is_file():
            self._path.unlink()


# ---------------------------------------------------------------------------
# Visibility verifier
# ---------------------------------------------------------------------------


class RepoVisibilityError(Exception):
    pass


def verify_repo_private(repo_id: str) -> None:
    if repo_id == DRY_RUN_REPO_ID:
        return
    api = HfApi()
    try:
        info = api.repo_info(repo_id=repo_id, repo_type="dataset")
    except RepositoryNotFoundError:
        raise RepoVisibilityError(
            f"Repository '{repo_id}' not found on Hugging Face. "
            "Blocking upload until a valid private repository is verified."
        )
    except Exception as exc:
        raise RepoVisibilityError(
            f"Cannot verify visibility of '{repo_id}': {exc}. "
            "Blocking upload for safety."
        )

    private = getattr(info, "private", None)
    if not private:
        raise RepoVisibilityError(
            f"Repository '{repo_id}' exists but is NOT private. "
            "Pilot and research artifacts must never be uploaded to a "
            "public repository. Blocking upload."
        )


# ---------------------------------------------------------------------------
# Uploader with bounded exponential backoff
# ---------------------------------------------------------------------------


class HfUploader:
    def __init__(
        self,
        runs_dir: Path,
        repo_id: str,
        layout: RemoteLayout,
        token: str,
        max_retries: int = 3,
        base_delay: float = 2.0,
    ) -> None:
        self._runs_dir = runs_dir
        self._repo_id = repo_id
        self._layout = layout
        self._token = token
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._api = HfApi()
        self._sync_state_path = runs_dir / "remote_sync.json"
        self._failure_store = SyncFailureStore(runs_dir)
        self._chunk_counter = 0

    @property
    def sync_state_path(self) -> Path:
        return self._sync_state_path

    @property
    def failure_store(self) -> SyncFailureStore:
        return self._failure_store

    def _remote_path(self, local_name: str) -> str:
        return f"{self._layout.recovery()}/{local_name}"

    def _get_token_safe(self) -> str:
        return self._token

    def _write_sync_state(self, status: str, remote_path: str, details: str = "") -> None:
        state: dict[str, Any] = {
            "last_sync": status,
            "remote_path": remote_path,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "details": details,
        }
        self._sync_state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def upload_recovery(self) -> bool:
        self._write_sync_state("pending", self._layout.recovery(), "sync state initialized")
        upload_names = list(RECOVERY_FILES) + ["remote_sync.json"]
        for local_name in upload_names:
            local_path = self._runs_dir / local_name
            if not local_path.is_file():
                continue
            if not _is_path_allowed(local_path, self._runs_dir):
                logger.warning("Security filter blocked: %s", local_name)
                continue
            remote_path = self._remote_path(local_name)
            if not self._upload_with_retry(local_path, remote_path):
                return False
        self._write_sync_state("recovery_uploaded", self._layout.recovery(), "all recovery files uploaded")
        return True

    def upload_snapshot(self, packager: Any, first: bool = False) -> bool:
        if first:
            self._chunk_counter = 0
        self._chunk_counter += 1
        chunk_num = self._chunk_counter
        snapshot_dir = self._layout.snapshot(chunk_num)
        zip_name = f"benchmark-results-chunk-{chunk_num:04d}.zip"

        local_zip = self._runs_dir / zip_name
        try:
            packager.create_zip(local_zip)
        except Exception as exc:
            logger.error("Snapshot ZIP creation failed: %s", exc)
            return False

        remote_zip = f"{snapshot_dir}/{zip_name}"
        if not self._upload_with_retry(local_zip, remote_zip):
            return False

        local_manifest = self._runs_dir / "manifest.json"
        if local_manifest.is_file():
            remote_manifest = f"{snapshot_dir}/MANIFEST.json"
            if not self._upload_with_retry(local_manifest, remote_manifest):
                return False

        self._write_sync_state("snapshot_uploaded", f"chunk-{chunk_num:04d}")
        return True

    def upload_final(self, packager: Any) -> bool:
        self._chunk_counter = 0
        local_zip = self._runs_dir / "benchmark-results.zip"
        try:
            packager.create_zip(local_zip)
        except Exception as exc:
            logger.error("Final ZIP creation failed: %s", exc)
            return False

        remote_zip = f"{self._layout.final()}/benchmark-results.zip"
        if not self._upload_with_retry(local_zip, remote_zip):
            return False

        local_manifest = self._runs_dir / "manifest.json"
        if local_manifest.is_file():
            remote_manifest = f"{self._layout.final()}/MANIFEST.json"
            if not self._upload_with_retry(local_manifest, remote_manifest):
                return False

        self._write_sync_state("final_uploaded", self._layout.final())
        return True

    def _upload_with_retry(self, local_path: Path, remote_path: str) -> bool:
        last_error = ""
        for attempt in range(self._max_retries + 1):
            try:
                self._api.upload_file(
                    path_or_fileobj=str(local_path),
                    path_in_repo=remote_path,
                    repo_id=self._repo_id,
                    repo_type="dataset",
                    token=self._token,
                )
                logger.info("Uploaded: %s -> %s", local_path.name, remote_path)
                return True
            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    "Upload attempt %d/%d failed for %s: %s",
                    attempt + 1, self._max_retries + 1, local_path.name, last_error,
                )
                if attempt < self._max_retries:
                    delay = self._base_delay * (2 ** attempt)
                    time.sleep(delay)

        self._failure_store.record_failure(SyncFailureRecord(
            stage="upload",
            remote_path=remote_path,
            error=last_error,
            local_checkpoint_ok=self._check_local_integrity(),
        ))
        logger.error(
            "Upload failed after %d retries: %s -> %s",
            self._max_retries + 1, local_path.name, remote_path,
        )
        return False

    def _check_local_integrity(self) -> bool:
        cp = self._runs_dir / "checkpoint.json"
        records = self._runs_dir / "run_records.jsonl"
        return cp.is_file() and records.is_file()


# ---------------------------------------------------------------------------
# Resume from HF
# ---------------------------------------------------------------------------


class HfResumeManager:
    def __init__(
        self,
        runs_dir: Path,
        repo_id: str,
        layout: RemoteLayout,
        token: str,
        protocol_version: str,
        config_hash: str,
        model_identity: str,
        source_commit: str,
        scenario_ids: list[str],
        strategy_names: list[str],
    ) -> None:
        self._runs_dir = runs_dir
        self._repo_id = repo_id
        self._layout = layout
        self._token = token
        self._protocol_version = protocol_version
        self._config_hash = config_hash
        self._model_identity = model_identity
        self._source_commit = source_commit
        self._scenario_ids = set(scenario_ids)
        self._strategy_names = set(strategy_names)

    def download_and_validate(self) -> set[str]:
        recovery_prefix = self._layout.recovery()
        local_files: list[Path] = []
        download_errors: list[str] = []

        for name in RECOVERY_FILES:
            remote_path = f"{recovery_prefix}/{name}"
            local_path = self._runs_dir / name
            try:
                hf_hub_download(
                    repo_id=self._repo_id,
                    filename=remote_path,
                    repo_type="dataset",
                    local_dir=str(self._runs_dir),
                    token=self._token,
                    local_dir_use_symlinks=False,
                )
                logger.info("Downloaded recovery file: %s", name)
                local_files.append(local_path)
            except Exception as exc:
                download_errors.append(f"{name}: {exc}")
                logger.warning("Recovery file not found or failed: %s: %s", name, exc)

        if not local_files:
            missing_list = ", ".join(download_errors) if download_errors else "all files"
            raise ResumeValidationError(
                f"No recovery files could be downloaded from '{recovery_prefix}'. "
                f"Errors: {missing_list}. "
                "Resume requires all mandatory recovery files. "
                "Cannot continue with an empty checkpoint."
            )

        self._validate_recovery()

        checkpoint_mgr = CheckpointManager(self._runs_dir)
        record_store = RunRecordStore(self._runs_dir)

        cp = checkpoint_mgr.read()
        if cp is not None:
            self._validate_compatibility(cp)

        completed_ids = record_store.get_completed_run_ids()
        logger.info("HF resume: %d completed run IDs to skip", len(completed_ids))
        return completed_ids

    def _validate_recovery(self) -> None:
        checkpoint_mgr = CheckpointManager(self._runs_dir)
        cp = checkpoint_mgr.read()
        if cp is None:
            raise ResumeValidationError("No checkpoint found in downloaded recovery state")

        if cp.protocol_version != self._protocol_version:
            raise ResumeValidationError(
                f"Protocol version mismatch: remote={cp.protocol_version}, local={self._protocol_version}"
            )
        if cp.config_hash and self._config_hash and cp.config_hash != self._config_hash:
            raise ResumeValidationError(
                f"Config hash mismatch: remote={cp.config_hash}, local={self._config_hash}"
            )
        if cp.source_commit and self._source_commit and cp.source_commit != self._source_commit:
            raise ResumeValidationError(
                f"Source commit mismatch: remote={cp.source_commit}, local={self._source_commit}"
            )
        if cp.model_identity and self._model_identity and cp.model_identity != self._model_identity:
            raise ResumeValidationError(
                f"Model identity mismatch: remote={cp.model_identity}, local={self._model_identity}"
            )

        remote_scenarios = set()
        remote_strategies = set()
        for rid in cp.planned_run_ids:
            parts = rid.split("_", 2)
            if len(parts) >= 2:
                remote_strategies.add(parts[1])
            if len(parts) >= 1:
                sc_id = parts[0].rsplit("-rep", 1)[0] if "-rep" in parts[0] else parts[0]
                remote_scenarios.add(sc_id)

        if remote_scenarios and remote_scenarios != self._scenario_ids:
            raise ResumeValidationError(
                f"Scenario set mismatch: remote has {len(remote_scenarios)} scenarios, "
                f"local has {len(self._scenario_ids)}"
            )
        if remote_strategies and remote_strategies != self._strategy_names:
            raise ResumeValidationError(
                f"Strategy set mismatch: remote has {remote_strategies}, "
                f"local has {self._strategy_names}"
            )

    def _validate_compatibility(self, cp: Any) -> None:
        record_store = RunRecordStore(self._runs_dir)
        for rec in record_store.load_all():
            parts = rec.run_id.split("_", 2)
            if len(parts) >= 2:
                if parts[1] not in self._strategy_names:
                    raise ResumeValidationError(
                        f"Strategy '{parts[1]}' in run record not in current strategy set"
                    )


class ResumeValidationError(Exception):
    pass
