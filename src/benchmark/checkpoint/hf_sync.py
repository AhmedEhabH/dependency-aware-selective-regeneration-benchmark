from __future__ import annotations

import json
import logging
import posixpath
import shutil
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from huggingface_hub import CommitOperationAdd, HfApi, hf_hub_download
from huggingface_hub.utils import RepositoryNotFoundError

from benchmark.checkpoint.checkpoint import CheckpointManager
from benchmark.checkpoint.persistence import RunRecordStore

logger = logging.getLogger("benchmark.hf_sync")

RECOVERY_FILES: tuple[str, ...] = (
    "run_records.jsonl",
    "checkpoint.json",
    "progress.json",
    "benchmark_summary.partial.json",
    "experiment_id.txt",
    "source_identity.json",
    "dashboard/dashboard_summary.json",
    "dashboard/run_matrix.csv",
    "dashboard/strategy_summary.csv",
    "dashboard/failure_summary.csv",
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
    "benchmark-results",
    "MANIFEST.json",
    "manifest.json",
    "environment_metadata.json",
    "failure_records.json",
    "remote_sync.json",
    "remote_sync_failure.json",
    "experiment_id.txt",
    "source_identity.json",
    "COMPLETED",
    "dashboard_summary.json",
    "run_matrix.csv",
    "strategy_summary.csv",
    "failure_summary.csv",
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

    return any(lower.startswith(prefix.lower()) for prefix in ALLOWLIST_PREFIXES)


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


@dataclass(frozen=True)
class CompatibilityResult:
    compatible: bool
    reasons: tuple[str, ...]
    identity_source: str = ""


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
        self._last_error = ""

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
        pairs: list[tuple[Path, str]] = []
        for local_name in RECOVERY_FILES:
            local_path = self._runs_dir / local_name
            if not local_path.is_file():
                continue
            if not _is_path_allowed(local_path, self._runs_dir):
                logger.warning("Security filter blocked: %s", local_name)
                continue
            pairs.append((local_path, self._remote_path(local_name)))

        # Write the intended successful state BEFORE the commit and include
        # that exact file in the same recovery commit. The remote must never
        # see a `pending` state as its final truth.
        self._write_sync_state(
            "recovery_uploaded",
            self._layout.recovery(),
            "all recovery files uploaded",
        )
        pairs.append((self._sync_state_path, self._remote_path("remote_sync.json")))

        if not self._upload_batch_with_retry(
            pairs,
            self._layout.recovery(),
            "sync recovery batch",
        ):
            # On commit failure overwrite the local state with a truthful
            # failure state, preserving the actual remote path and error
            # details; the SyncFailureStore record is retained.
            self._write_sync_state(
                "failed_local_safe",
                self._layout.recovery(),
                self._last_error or "recovery commit failed",
            )
            return False
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

        pairs: list[tuple[Path, str]] = [
            (local_zip, f"{snapshot_dir}/{zip_name}"),
        ]
        local_manifest = self._runs_dir / "manifest.json"
        if local_manifest.is_file():
            pairs.append((local_manifest, f"{snapshot_dir}/MANIFEST.json"))

        if not self._upload_batch_with_retry(
            pairs,
            snapshot_dir,
            f"snapshot chunk-{chunk_num:04d}",
        ):
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

        pairs: list[tuple[Path, str]] = [
            (local_zip, f"{self._layout.final()}/benchmark-results.zip"),
        ]
        local_manifest = self._runs_dir / "manifest.json"
        if local_manifest.is_file():
            pairs.append((local_manifest, f"{self._layout.final()}/MANIFEST.json"))

        if not self._upload_batch_with_retry(
            pairs,
            self._layout.final(),
            "final batch",
        ):
            return False

        self._write_sync_state("final_uploaded", self._layout.final())
        return True

    def _upload_batch_with_retry(
        self,
        pairs: list[tuple[Path, str]],
        remote_dir: str,
        commit_message: str,
    ) -> bool:
        """Upload a batch of files as exactly one HF commit, with bounded retry.

        Returns False (after writing a SyncFailureRecord) if the commit never
        succeeds. Never creates an empty commit.
        """
        if not pairs:
            logger.warning("Refusing to create an empty HF commit for %s", remote_dir)
            return False

        operations = [
            CommitOperationAdd(
                path_in_repo=remote_path,
                path_or_fileobj=str(local_path),
            )
            for local_path, remote_path in pairs
        ]
        last_error = ""
        for attempt in range(self._max_retries + 1):
            try:
                self._api.create_commit(
                    repo_id=self._repo_id,
                    repo_type="dataset",
                    operations=operations,
                    commit_message=commit_message,
                    token=self._token,
                )
                for _local_path, remote_path in pairs:
                    logger.info("Uploaded: %s", remote_path)
                return True
            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    "Commit attempt %d/%d failed for %s: %s",
                    attempt + 1, self._max_retries + 1, remote_dir, last_error,
                )
                if attempt < self._max_retries:
                    delay = self._base_delay * (2 ** attempt)
                    time.sleep(delay)

        self._last_error = last_error
        self._failure_store.record_failure(SyncFailureRecord(
            stage="upload",
            remote_path=remote_dir,
            error=last_error,
            local_checkpoint_ok=self._check_local_integrity(),
        ))
        logger.error(
            "Commit failed after %d retries: %s (%d files)",
            self._max_retries + 1, remote_dir, len(pairs),
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
        self._scenario_ids = scenario_ids
        self._strategy_names = strategy_names

    def download_and_validate(self) -> set[str]:
        """Download recovery files to an isolated temp dir, validate, then activate.

        The activation copies only the allowlisted recovery files into
        ``self._runs_dir`` so that subsequent validation reads them from the
        canonical root (e.g. ``<output_dir>/checkpoint.json``).
        """
        recovery_prefix = self._layout.recovery()

        with tempfile.TemporaryDirectory(prefix="hf_recovery_") as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            downloaded_paths: list[Path] = []
            download_errors: list[str] = []

            for name in RECOVERY_FILES:
                remote_path = f"{recovery_prefix}/{name}"
                try:
                    result_path = hf_hub_download(
                        repo_id=self._repo_id,
                        filename=remote_path,
                        repo_type="dataset",
                        local_dir=str(temp_dir),
                        token=self._token,
                        local_dir_use_symlinks=False,
                    )
                    logger.info("Downloaded recovery file: %s", name)
                    downloaded_paths.append(Path(result_path))
                except Exception as exc:
                    download_errors.append(f"{name}: {exc}")
                    logger.warning("Recovery file not found or failed: %s: %s", name, exc)

            if not downloaded_paths:
                missing_list = ", ".join(download_errors) if download_errors else "all files"
                raise ResumeValidationError(
                    f"No recovery files could be downloaded from '{recovery_prefix}'. "
                    f"Errors: {missing_list}. "
                    "Resume requires all mandatory recovery files. "
                    "Cannot continue with an empty checkpoint."
                )

            # Locate the recovery directory inside the temp tree.
            # hf_hub_download preserves the repo directory structure under
            # local_dir, so the files live at:
            #   <temp>/experiments/.../<experiment_id>/recovery/<name>
            recovery_dir = self._find_recovery_dir(temp_dir)
            if recovery_dir is None:
                raise ResumeValidationError(
                    f"Could not locate recovery directory under "
                    f"'{temp_dir}' for experiment '{self._layout.experiment_id}'."
                )

            # --- Pre-activation validation -----------------------------------
            self._validate_pre_activation(recovery_dir)

            # --- Atomic activation into canonical output dir ------------------
            self._activate_recovery(recovery_dir)

        # Post-activation validation from the canonical location
        self._validate_recovery()

        checkpoint_mgr = CheckpointManager(self._runs_dir)
        record_store = RunRecordStore(self._runs_dir)

        cp = checkpoint_mgr.read()
        if cp is not None:
            self._validate_compatibility(cp)

        completed_ids = record_store.get_completed_run_ids()
        logger.info("HF resume: %d completed run IDs to skip", len(completed_ids))
        return completed_ids

    # ------------------------------------------------------------------
    # Recovery directory discovery
    # ------------------------------------------------------------------

    def _find_recovery_dir(self, temp_root: Path) -> Path | None:
        """Locate the exact recovery directory for this experiment inside *temp_root*.

        The expected hierarchy is:
            <temp_root>/experiments/<profile>/<protocol>/<commit>/<exp_id>/recovery/
        """
        base_parts = self._layout._base().split("/")
        candidate = temp_root
        for part in base_parts:
            candidate = candidate / part
        recovery_dir = candidate / "recovery"
        if recovery_dir.is_dir():
            return recovery_dir

        # Fallback: search for recovery dirs containing checkpoint.json
        for d in temp_root.rglob("recovery"):
            if (d / "checkpoint.json").is_file():
                return d
        return None

    # ------------------------------------------------------------------
    # Pre-activation validation
    # ------------------------------------------------------------------

    def _validate_pre_activation(self, recovery_dir: Path) -> None:
        """Validate the downloaded recovery state before modifying output_dir.

        Checks:
        - checkpoint.json exists and parses
        - experiment ID matches the selected experiment
        - checkpoint compatibility is valid
        - run-record file parses when present
        - completed/pending Run IDs are subsets of planned Run IDs
        """
        cp_path = recovery_dir / "checkpoint.json"
        if not cp_path.is_file():
            raise ResumeValidationError(
                f"Pre-activation validation failed: no checkpoint.json in "
                f"recovery directory '{recovery_dir}'"
            )

        cp_mgr = CheckpointManager(recovery_dir)
        try:
            cp = cp_mgr.read()
        except (ValueError, OSError) as exc:
            raise ResumeValidationError(
                f"Pre-activation validation failed: checkpoint.json is corrupted: {exc}"
            ) from exc
        if cp is None:
            raise ResumeValidationError(
                "Pre-activation validation failed: checkpoint.json could not be parsed"
            )

        # Verify experiment ID matches (only when the file is present)
        exp_id_path = recovery_dir / "experiment_id.txt"
        if exp_id_path.is_file():
            remote_exp_id = exp_id_path.read_text(encoding="utf-8").strip()
            if remote_exp_id and remote_exp_id != self._layout.experiment_id:
                raise ResumeValidationError(
                    f"Pre-activation validation failed: experiment ID mismatch "
                    f"(remote='{remote_exp_id}', expected='{self._layout.experiment_id}')"
                )

        # Verify checkpoint compatibility
        result = compare_checkpoint_compatibility(
            cp=cp,
            expected_protocol_version=self._protocol_version,
            expected_config_hash=self._config_hash,
            expected_source_commit=self._source_commit,
            expected_model_identity=self._model_identity,
            expected_scenario_ids=self._scenario_ids,
            expected_strategy_names=self._strategy_names,
        )
        if not result.compatible:
            raise ResumeValidationError(
                f"Pre-activation validation failed: {'; '.join(result.reasons)}"
            )

        # Verify run-record file parses and IDs are subsets of planned
        records_path = recovery_dir / "run_records.jsonl"
        if records_path.is_file():
            from benchmark.checkpoint.persistence import RunRecordStore as _RRS
            tmp_store = _RRS(recovery_dir)
            planned = set(cp.planned_run_ids)
            for rec in tmp_store.load_all():
                if rec.run_id not in planned:
                    raise ResumeValidationError(
                        f"Pre-activation validation failed: run record "
                        f"'{rec.run_id}' is not in planned_run_ids"
                    )

        logger.info(
            "Pre-activation validation passed for experiment '%s'",
            self._layout.experiment_id,
        )

    # ------------------------------------------------------------------
    # Atomic activation
    # ------------------------------------------------------------------

    def _activate_recovery(self, recovery_dir: Path) -> None:
        """Copy allowlisted recovery files from *recovery_dir* into self._runs_dir.

        Only the flat recovery files are copied. The outer
        ``experiments/.../recovery/`` hierarchy is NOT copied into output_dir.
        HF cache directories are never copied.
        """
        self._runs_dir.mkdir(parents=True, exist_ok=True)

        # Verify no stale experiment hierarchy exists under output_dir
        stale_experiments = self._runs_dir / "experiments"
        if stale_experiments.is_dir():
            shutil.rmtree(str(stale_experiments))
            logger.warning("Removed stale experiments/ hierarchy from output dir")

        stale_cache = self._runs_dir / ".cache"
        if stale_cache.is_dir():
            shutil.rmtree(str(stale_cache))
            logger.warning("Removed .cache/ from output dir")

        activated: list[str] = []
        for name in RECOVERY_FILES:
            src = recovery_dir / name
            if src.is_file():
                dst = self._runs_dir / name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src), str(dst))
                activated.append(name)

        logger.info(
            "Activated %d recovery files into '%s': %s",
            len(activated), self._runs_dir, activated,
        )

        # Confirm checkpoint.json is present
        if not (self._runs_dir / "checkpoint.json").is_file():
            raise ResumeValidationError(
                "Activation failed: checkpoint.json not present in output dir "
                f"'{self._runs_dir}' after activation"
            )

    def _validate_compatibility(self, _cp: Any) -> None:
        record_store = RunRecordStore(self._runs_dir)
        all_strategies = set(self._strategy_names)
        for rec in record_store.load_all():
            if rec.strategy_id not in all_strategies:
                raise ResumeValidationError(
                    f"Strategy '{rec.strategy_id}' in run record not in current strategy set"
                )

    def _validate_recovery(self) -> None:
        """Validate the activated recovery state in self._runs_dir."""
        checkpoint_mgr = CheckpointManager(self._runs_dir)
        cp = checkpoint_mgr.read()
        if cp is None:
            raise ResumeValidationError("No checkpoint found in activated recovery state")

        result = compare_checkpoint_compatibility(
            cp=cp,
            expected_protocol_version=self._protocol_version,
            expected_config_hash=self._config_hash,
            expected_source_commit=self._source_commit,
            expected_model_identity=self._model_identity,
            expected_scenario_ids=self._scenario_ids,
            expected_strategy_names=self._strategy_names,
        )
        if not result.compatible:
            raise ResumeValidationError(
                f"Resume validation failed: {'; '.join(result.reasons)}"
            )


class ResumeValidationError(Exception):
    pass


def compare_checkpoint_compatibility(
    cp: Any,
    expected_protocol_version: str,
    expected_config_hash: str,
    expected_source_commit: str,
    expected_model_identity: str,
    expected_scenario_ids: list[str],
    expected_strategy_names: list[str],
) -> CompatibilityResult:
    """Compare a checkpoint against expected values using explicit identity fields.

    Returns a CompatibilityResult with detailed rejection reasons.
    Identity source is 'explicit_checkpoint' when scenario_ids/strategy_names
    are present, or 'legacy_exact_plan_lookup' when using planned_run_ids.
    """
    reasons: list[str] = []

    if cp.protocol_version != expected_protocol_version:
        reasons.append(
            f"Protocol version mismatch: remote={cp.protocol_version}, expected={expected_protocol_version}"
        )
    if cp.config_hash and expected_config_hash and cp.config_hash != expected_config_hash:
        reasons.append(
            f"Config hash mismatch: remote={cp.config_hash}, expected={expected_config_hash}"
        )
    if cp.source_commit and expected_source_commit and cp.source_commit != expected_source_commit:
        reasons.append(
            f"Source commit mismatch: remote={cp.source_commit}, expected={expected_source_commit}"
        )
    if cp.model_identity and expected_model_identity and cp.model_identity != expected_model_identity:
        reasons.append(
            f"Model identity mismatch: remote={cp.model_identity}, expected={expected_model_identity}"
        )

    remote_scenarios = getattr(cp, "scenario_ids", None)
    remote_strategies = getattr(cp, "strategy_names", None)

    has_explicit = (
        remote_scenarios is not None
        and remote_strategies is not None
        and len(remote_scenarios) > 0
        and len(remote_strategies) > 0
    )

    if has_explicit:
        identity_source = "explicit_checkpoint"
        assert remote_scenarios is not None
        assert remote_strategies is not None
        remote_sc_set = set(remote_scenarios)
        remote_st_set = set(remote_strategies)
        expected_sc_set = set(expected_scenario_ids)
        expected_st_set = set(expected_strategy_names)

        if remote_sc_set and remote_sc_set != expected_sc_set:
            reasons.append(
                f"Scenario identity mismatch: remote={sorted(remote_sc_set)}, "
                f"expected={sorted(expected_sc_set)}"
            )
        if remote_st_set and remote_st_set != expected_st_set:
            reasons.append(
                f"Strategy identity mismatch: remote={sorted(remote_st_set)}, "
                f"expected={sorted(expected_st_set)}"
            )
    else:
        identity_source = "legacy_exact_plan_lookup"
        planned_run_ids = getattr(cp, "planned_run_ids", []) or []
        if planned_run_ids:
            expected_plan_run_ids = set(
                _make_run_id_for_plan(s, st, 1, cp.config_hash, cp.protocol_version)
                for s in expected_scenario_ids
                for st in expected_strategy_names
            )
            remote_plan_set = set(planned_run_ids)
            if remote_plan_set and remote_plan_set != expected_plan_run_ids:
                reasons.append(
                    "Legacy checkpoint lacks explicit execution identity "
                    "and planned Run IDs do not match current execution plan"
                )
        else:
            reasons.append(
                "Legacy checkpoint lacks explicit execution identity "
                "and cannot be mapped safely"
            )

    compatible = len(reasons) == 0
    return CompatibilityResult(
        compatible=compatible,
        reasons=tuple(reasons),
        identity_source=identity_source,
    )


def _make_run_id_for_plan(
    scenario_id: str,
    strategy_name: str,
    repetition: int,
    config_hash: str = "",
    protocol_version: str = "1.0",
) -> str:
    """Build a deterministic Run ID matching seven_arm_benchmark._make_run_id."""
    import hashlib
    payload = json.dumps({
        "scenario_id": scenario_id,
        "strategy_name": strategy_name,
        "repetition": repetition,
        "protocol_version": protocol_version,
        "config_hash": config_hash,
    }, sort_keys=True)
    suffix = hashlib.sha256(payload.encode()).hexdigest()[:8]
    return f"{scenario_id}_{strategy_name}_rep{repetition}_{suffix}"


def _emit_candidate_diagnostic(
    exp_id: str,
    cp_status: str,
    records_status: str,
    remote_profile: str,
    expected_profile: str,
    remote_protocol: str,
    expected_protocol: str,
    remote_source_commit: str,
    expected_source_commit: str,
    remote_config_hash: str,
    expected_config_hash: str,
    remote_model_identity: str,
    expected_model_identity: str,
    remote_completion_status: str,
    remote_total_planned: int,
    expected_total_planned: int,
    remote_scenario_ids: list[str],
    expected_scenario_ids: list[str],
    remote_strategy_names: list[str],
    expected_strategy_names: list[str],
    compatible: bool,
    rejection_reasons: list[str],
    identity_source: str,
    planned_run_ids_match: bool | None = None,
) -> None:
    """Emit a structured INFO log for a candidate experiment diagnostic."""
    logger.info(
        "AUTO_RESUME_CANDIDATE: experiment_id=%s compatible=%s rejection_reasons=%s "
        "checkpoint_download=%s records_download=%s "
        "remote_profile=%s expected_profile=%s "
        "remote_protocol=%s expected_protocol=%s "
        "remote_source_commit=%s expected_source_commit=%s "
        "remote_config_hash=%s expected_config_hash=%s "
        "remote_model_identity=%s expected_model_identity=%s "
        "remote_completion_status=%s remote_total_planned=%d expected_total_planned=%d "
        "remote_scenarios=%s expected_scenarios=%s "
        "remote_strategies=%s expected_strategies=%s "
        "planned_run_ids_match=%s "
        "identity_source=%s",
        exp_id,
        compatible,
        rejection_reasons,
        cp_status,
        records_status,
        remote_profile,
        expected_profile,
        remote_protocol,
        expected_protocol,
        remote_source_commit,
        expected_source_commit,
        remote_config_hash,
        expected_config_hash,
        remote_model_identity,
        expected_model_identity,
        remote_completion_status,
        remote_total_planned,
        expected_total_planned,
        remote_scenario_ids,
        expected_scenario_ids,
        remote_strategy_names,
        expected_strategy_names,
        planned_run_ids_match,
        identity_source,
    )



# ---------------------------------------------------------------------------
# Auto-resume: discover compatible experiments
# ---------------------------------------------------------------------------


@dataclass
class CompatibleExperiment:
    """A remote experiment that matches the requested profile/config."""

    experiment_id: str
    remote_prefix: str
    is_complete: bool
    completed_count: int
    total_planned: int
    failed_count: int
    last_update: str = ""
    completion_status: str = ""
    identity_source: str = ""
    planned_run_ids_match: bool = True


@dataclass
class AutoResumeResult:
    """Outcome of the auto-resume search."""

    action: str  # "resume" | "start_new" | "already_complete" | "error"
    experiment_id: str
    compatible_experiments: list[CompatibleExperiment]
    message: str


def list_compatible_experiments(
    repo_id: str,
    token: str,
    profile: str,
    protocol_version: str,
    source_commit: str,
    config_hash: str,
    model_identity: str,
    scenario_ids: list[str],
    strategy_names: list[str],
) -> list[CompatibleExperiment]:
    """Search the canonical remote prefix for compatible experiments.

    Lists all files in the repo, filters to the canonical prefix
    ``experiments/{profile}/{protocol_version}/{source_commit}/``, then
    downloads each experiment's checkpoint to validate compatibility.

    Uses explicit checkpoint identity fields (scenario_ids, strategy_names)
    when available, falls back to legacy exact-plan lookup.

    Returns a list of compatible experiments (both complete and incomplete).
    Raises ResumeValidationError on HF API or download failures.
    """
    api = HfApi()
    prefix = posixpath.join(
        "experiments", profile, protocol_version, source_commit,
    )

    try:
        all_files = list(api.list_repo_files(
            repo_id=repo_id,
            repo_type="dataset",
            token=token,
        ))
    except Exception as exc:
        raise ResumeValidationError(
            f"Failed to list files in HF repo '{repo_id}': {exc}. "
            "Cannot discover experiments for auto-resume."
        ) from exc

    experiment_ids: set[str] = set()
    for f in all_files:
        if not f.startswith(prefix + "/"):
            continue
        parts = f[len(prefix) + 1:].split("/")
        if parts and parts[0]:
            experiment_ids.add(parts[0])

    if not experiment_ids:
        return []

    compatible: list[CompatibleExperiment] = []
    with tempfile.TemporaryDirectory(prefix="auto_resume_") as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        for exp_id in sorted(experiment_ids):
            exp_recovery_prefix = posixpath.join(prefix, exp_id, "recovery")
            cp_path = f"{exp_recovery_prefix}/checkpoint.json"
            records_path = f"{exp_recovery_prefix}/run_records.jsonl"

            cp_local: Path | None = None
            records_local: Path | None = None

            try:
                cp_result = hf_hub_download(
                    repo_id=repo_id,
                    filename=cp_path,
                    repo_type="dataset",
                    local_dir=str(temp_dir),
                    token=token,
                    local_dir_use_symlinks=False,
                )
                records_result = hf_hub_download(
                    repo_id=repo_id,
                    filename=records_path,
                    repo_type="dataset",
                    local_dir=str(temp_dir),
                    token=token,
                    local_dir_use_symlinks=False,
                )
                cp_local = Path(cp_result)
                records_local = Path(records_result)
            except ResumeValidationError:
                raise
            except Exception as exc:
                _emit_candidate_diagnostic(
                    exp_id=exp_id,
                    cp_status="download_failed",
                    records_status="download_failed",
                    remote_profile=profile,
                    expected_profile=profile,
                    remote_protocol="",
                    expected_protocol=protocol_version,
                    remote_source_commit="",
                    expected_source_commit=source_commit,
                    remote_config_hash="",
                    expected_config_hash=config_hash,
                    remote_model_identity="",
                    expected_model_identity=model_identity,
                    remote_completion_status="",
                    remote_total_planned=0,
                    expected_total_planned=0,
                    remote_scenario_ids=[],
                    expected_scenario_ids=scenario_ids,
                    remote_strategy_names=[],
                    expected_strategy_names=strategy_names,
                    compatible=False,
                    rejection_reasons=[f"Failed to download recovery files: {exc}"],
                    identity_source="",
                )
                continue

            try:
                cp_text = cp_local.read_text(encoding="utf-8")
                cp_data = json.loads(cp_text)
                records_text = records_local.read_text(encoding="utf-8").strip()
                completed_ids: set[str] = set()
                failed_count = 0
                total_planned = cp_data.get("total_planned", 0)
                if records_text:
                    for line in records_text.split("\n"):
                        if not line.strip():
                            continue
                        rec = json.loads(line)
                        status = rec.get("status", "")
                        if status in ("succeeded", "failed", "timed_out", "cancelled"):
                            completed_ids.add(rec.get("run_id", ""))
                        if status in ("failed", "timed_out"):
                            failed_count += 1

                remote_protocol = cp_data.get("protocol_version", "")
                remote_config = cp_data.get("config_hash", "")
                remote_commit = cp_data.get("source_commit", "")
                remote_model = cp_data.get("model_identity", "")

                remote_completion_status = cp_data.get("completion_status", "")
                is_complete = remote_completion_status == "completed"
                remote_last_update = cp_data.get("last_update", "")

                remote_scenarios_list = cp_data.get("scenario_ids", None)
                remote_strategies_list = cp_data.get("strategy_names", None)

                rejection_reasons: list[str] = []

                if remote_protocol and remote_protocol != protocol_version:
                    rejection_reasons.append(
                        f"Protocol mismatch: remote={remote_protocol} expected={protocol_version}"
                    )
                if remote_config and config_hash and remote_config != config_hash:
                    rejection_reasons.append(
                        f"Config hash mismatch: remote={remote_config} expected={config_hash}"
                    )
                if remote_commit and source_commit and remote_commit != source_commit:
                    rejection_reasons.append(
                        f"Source commit mismatch: remote={remote_commit} expected={source_commit}"
                    )
                if remote_model and model_identity and remote_model != model_identity:
                    rejection_reasons.append(
                        f"Model identity mismatch: remote={remote_model} expected={model_identity}"
                    )

                identity_source = ""
                planned_run_ids_match = True
                has_explicit_in_cp = (
                    remote_scenarios_list is not None
                    and remote_strategies_list is not None
                    and len(remote_scenarios_list) > 0
                    and len(remote_strategies_list) > 0
                )
                if has_explicit_in_cp:
                    identity_source = "explicit_checkpoint"
                    remote_sc_set = set(remote_scenarios_list)
                    remote_st_set = set(remote_strategies_list)
                    expected_sc_set = set(scenario_ids)
                    expected_st_set = set(strategy_names)

                    if remote_sc_set and remote_sc_set != expected_sc_set:
                        rejection_reasons.append(
                            f"Scenario identity mismatch: remote={sorted(remote_sc_set)} "
                            f"expected={sorted(expected_sc_set)}"
                        )
                    if remote_st_set and remote_st_set != expected_st_set:
                        rejection_reasons.append(
                            f"Strategy identity mismatch: remote={sorted(remote_st_set)} "
                            f"expected={sorted(expected_st_set)}"
                        )
                else:
                    identity_source = "legacy_exact_plan_lookup"
                    planned = cp_data.get("planned_run_ids", [])
                    if planned:
                        expected_plan = set(
                            _make_run_id_for_plan(s, st, 1, remote_config, remote_protocol)
                            for s in scenario_ids
                            for st in strategy_names
                        )
                        remote_plan_set = set(planned)
                        planned_run_ids_match = (remote_plan_set == expected_plan)
                        if not planned_run_ids_match:
                            rejection_reasons.append(
                                "Legacy checkpoint lacks explicit execution identity "
                                "and planned Run IDs do not match current execution plan"
                            )
                    else:
                        rejection_reasons.append(
                            "Legacy checkpoint lacks explicit execution identity "
                            "and cannot be mapped safely"
                        )

                _emit_candidate_diagnostic(
                    exp_id=exp_id,
                    cp_status="ok",
                    records_status="ok",
                    remote_profile=profile,
                    expected_profile=profile,
                    remote_protocol=remote_protocol,
                    expected_protocol=protocol_version,
                    remote_source_commit=remote_commit,
                    expected_source_commit=source_commit,
                    remote_config_hash=remote_config,
                    expected_config_hash=config_hash,
                    remote_model_identity=remote_model,
                    expected_model_identity=model_identity,
                    remote_completion_status=remote_completion_status,
                    remote_total_planned=total_planned,
                    expected_total_planned=len(scenario_ids) * len(strategy_names),
                    remote_scenario_ids=sorted(remote_scenarios_list) if remote_scenarios_list else [],
                    expected_scenario_ids=sorted(scenario_ids),
                    remote_strategy_names=sorted(remote_strategies_list) if remote_strategies_list else [],
                    expected_strategy_names=sorted(strategy_names),
                    compatible=len(rejection_reasons) == 0,
                    rejection_reasons=rejection_reasons,
                    identity_source=identity_source,
                    planned_run_ids_match=planned_run_ids_match,
                )

                if rejection_reasons:
                    continue

                compatible.append(CompatibleExperiment(
                    experiment_id=exp_id,
                    remote_prefix=posixpath.join(prefix, exp_id),
                    is_complete=is_complete,
                    completed_count=len(completed_ids),
                    total_planned=total_planned,
                    failed_count=failed_count,
                    last_update=remote_last_update,
                    completion_status=remote_completion_status,
                    identity_source=identity_source,
                    planned_run_ids_match=planned_run_ids_match,
                ))
            except Exception as exc:
                _emit_candidate_diagnostic(
                    exp_id=exp_id,
                    cp_status="validation_error",
                    records_status="validation_error",
                    remote_profile=profile,
                    expected_profile=profile,
                    remote_protocol="",
                    expected_protocol=protocol_version,
                    remote_source_commit="",
                    expected_source_commit=source_commit,
                    remote_config_hash="",
                    expected_config_hash=config_hash,
                    remote_model_identity="",
                    expected_model_identity=model_identity,
                    remote_completion_status="",
                    remote_total_planned=0,
                    expected_total_planned=0,
                    remote_scenario_ids=[],
                    expected_scenario_ids=scenario_ids,
                    remote_strategy_names=[],
                    expected_strategy_names=strategy_names,
                    compatible=False,
                    rejection_reasons=[f"Unexpected validation error: {type(exc).__name__}: {exc}"],
                    identity_source="",
                )
                continue
            finally:
                if cp_local is not None and cp_local.is_file():
                    cp_local.unlink(missing_ok=True)
                if records_local is not None and records_local.is_file():
                    records_local.unlink(missing_ok=True)

    return compatible


def resolve_auto_resume(
    repo_id: str,
    token: str,
    profile: str,
    protocol_version: str,
    source_commit: str,
    config_hash: str,
    model_identity: str,
    scenario_ids: list[str],
    strategy_names: list[str],
    explicit_experiment_id: str | None = None,
    new_experiment: bool = False,
) -> AutoResumeResult:
    """Determine the auto-resume action.

    Returns an AutoResumeResult with one of:
      - resume: compatible incomplete experiment found
      - start_new: no compatible incomplete experiment found
      - already_complete: a compatible experiment is already complete
      - error: API failure or ambiguous selection

    Selection policy for multiple compatible incomplete experiments:
    - If explicit_experiment_id matches one, use it
    - Otherwise, select the one with the newest valid last_update
    - Log superseded candidates
    - Tie-break deterministically by experiment_id (lexicographic)
    """
    try:
        compatible = list_compatible_experiments(
            repo_id=repo_id,
            token=token,
            profile=profile,
            protocol_version=protocol_version,
            source_commit=source_commit,
            config_hash=config_hash,
            model_identity=model_identity,
            scenario_ids=scenario_ids,
            strategy_names=strategy_names,
        )
    except ResumeValidationError as exc:
        return AutoResumeResult(
            action="error",
            experiment_id="",
            compatible_experiments=[],
            message=f"Remote listing failed: {exc}",
        )

    incomplete = [e for e in compatible if not e.is_complete]
    complete = [e for e in compatible if e.is_complete]

    if new_experiment:
        if complete:
            return AutoResumeResult(
                action="already_complete",
                experiment_id=complete[0].experiment_id,
                compatible_experiments=compatible,
                message=(
                    f"Existing complete experiment found: {complete[0].experiment_id}. "
                    "Use --new-experiment to bypass."
                ),
            )
        return AutoResumeResult(
            action="start_new",
            experiment_id="",
            compatible_experiments=[],
            message="No existing experiments found. Creating new experiment.",
        )

    if len(incomplete) == 1:
        exp = incomplete[0]
        msg = (
            f"Compatible remote experiment found:\n"
            f"Experiment ID: {exp.experiment_id}\n"
            f"Completed: {exp.completed_count}/{exp.total_planned}\n"
            f"Failed: {exp.failed_count}\n"
            f"Pending: {exp.total_planned - exp.completed_count}\n"
            f"Action: RESUME"
        )
        return AutoResumeResult(
            action="resume",
            experiment_id=exp.experiment_id,
            compatible_experiments=compatible,
            message=msg,
        )

    if len(incomplete) > 1:
        if explicit_experiment_id:
            matched = [e for e in incomplete if e.experiment_id == explicit_experiment_id]
            if matched:
                exp = matched[0]
                superseded = [e for e in incomplete if e.experiment_id != explicit_experiment_id]
                msg = (
                    f"Compatible remote experiment found:\n"
                    f"Experiment ID: {exp.experiment_id}\n"
                    f"Completed: {exp.completed_count}/{exp.total_planned}\n"
                    f"Failed: {exp.failed_count}\n"
                    f"Pending: {exp.total_planned - exp.completed_count}\n"
                    f"Action: RESUME"
                )
                if superseded:
                    superseded_ids = [e.experiment_id for e in superseded]
                    msg += f"\nSuperseded candidates: {superseded_ids}"
                return AutoResumeResult(
                    action="resume",
                    experiment_id=exp.experiment_id,
                    compatible_experiments=compatible,
                    message=msg,
                )

        sorted_incomplete = _sort_experiments_by_recency(incomplete)
        selected = sorted_incomplete[0]
        superseded = sorted_incomplete[1:]

        msg = (
            f"Multiple compatible incomplete experiments found: "
            f"{[e.experiment_id for e in sorted_incomplete]}.\n"
            f"Selected (newest last_update): {selected.experiment_id}\n"
            f"Completed: {selected.completed_count}/{selected.total_planned}\n"
            f"Failed: {selected.failed_count}\n"
            f"Pending: {selected.total_planned - selected.completed_count}\n"
            f"Action: RESUME"
        )
        if superseded:
            superseded_ids = [e.experiment_id for e in superseded]
            msg += f"\nSuperseded candidates: {superseded_ids}"

        return AutoResumeResult(
            action="resume",
            experiment_id=selected.experiment_id,
            compatible_experiments=compatible,
            message=msg,
        )

    if len(complete) == 1:
        exp = complete[0]
        msg = (
            f"Compatible experiment already complete: {exp.experiment_id}\n"
            f"Completed: {exp.completed_count}/{exp.total_planned}\n"
            f"Action: ALREADY_COMPLETE"
        )
        return AutoResumeResult(
            action="already_complete",
            experiment_id=exp.experiment_id,
            compatible_experiments=compatible,
            message=msg,
        )

    return AutoResumeResult(
        action="start_new",
        experiment_id="",
        compatible_experiments=[],
        message="No compatible incomplete remote experiment found.",
    )


def _sort_experiments_by_recency(experiments: list[CompatibleExperiment]) -> list[CompatibleExperiment]:
    """Sort experiments by last_update descending, then experiment_id for determinism."""
    def _sort_key(e: CompatibleExperiment) -> tuple[str, str]:
        ts = e.last_update if e.last_update else ""
        return (ts, e.experiment_id)
    return sorted(experiments, key=_sort_key, reverse=True)
