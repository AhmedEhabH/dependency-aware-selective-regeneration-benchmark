"""WP-1b MAIN_297 / variance-substudy runner core (harness only; resume-safe).

The frozen agent (``IterativeRepositoryAgentStrategy``, protocol v3) is used
exactly as in Calibration-3c. This module only adds what a 297-task paid run
needs and the 3-task calibration runner did not have:

* every work item's PREDICTED SET is persisted (the calibration runner did not
  persist ``selected_paths``);
* per-item durable commit (sidecar + telemetry first, then the run record as the
  commit marker; each line flushed + fsync'ed); a crash never loses finished
  items and the output directory is NEVER deleted;
* resume: finished items are skipped; orphan sidecar/telemetry lines from an
  unfinished item are moved aside to ``*.orphaned.jsonl``;
* the frozen retry rule (via ``ResilientAccountingBackend``), a durable spend
  ledger, a pre-item worst-case USD guard and a per-request USD guard;
* instrument-level halting rules H1-H7 (preregistered in
  ``docs/WP1B_MAIN297_EXECUTION_ADDENDUM_2026-09-22.md``). Per-task AGENT
  BEHAVIOUR (EMPTY, rejected repeats, 0 reads, forced final, cost ratio > 1 on
  one task) NEVER halts a MAIN run: it is data.

Labels / proxies / target diffs are never read by this module (the optional
label-access guard enforces it at the ``open`` audit-event level).
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
import traceback
from collections import deque
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from benchmark.core.enums import ActionKind, ArtifactType
from benchmark.core.models import (
    ArtifactRef,
    ArtifactUniverse,
    ImpactPrediction,
    LLMResponse,
    RepositoryIdentity,
    RepositorySnapshot,
    RequirementChange,
    TokenUsage,
)
from benchmark.strategies.iterative_agent import IterativeRepositoryAgentStrategy
from benchmark.wp1b.resilient_backend import (
    ACCOUNT_OR_CONFIG,
    BAD_REQUEST,
    BackendCallFailedError,
    BudgetGuardError,
    ResilientAccountingBackend,
    frozen_usd,
    fsync_append,
    utc_now,
)
from benchmark.wp1b.telemetry import call_sidecar_records, strategy_telemetry

# ---------------------------------------------------------------------------
# Frozen identity (protocol v3). Any drift -> KnobDriftError before call 1.
# ---------------------------------------------------------------------------
PROTOCOL_ID = "wp1b_frozen_agent_protocol_v3"
FROZEN_MODEL = "qwen/qwen3-coder"
FROZEN_PROVIDER = "deepinfra/turbo"
FROZEN_ROUTE = "openrouter:qwen/qwen3-coder@deepinfra/turbo"
FROZEN_TEMPERATURE = 0.0
FROZEN_AGENT_CAP = 1024
FROZEN_MAX_AGENT_CALLS = 8
FROZEN_OBSERVATION_WINDOW = 2000
FROZEN_MAX_READ_CHARS = 12000
FROZEN_MAX_SEARCH_RESULTS = 50
FROZEN_MAX_DISTINCT_FILES = 30
FROZEN_MAX_LIST_ENTRIES = 200
FROZEN_MAX_FILE_SIZE = 200 * 1024

FROZEN_MAIN297_TASK_IDS_SHA256 = "1678dbaa3793588df4b82dce7d7b2d29586b612698e12a1c4d52ce32f4ccbceb"
FROZEN_VARIANCE_SELECTION_SHA256 = "2c4ac5b192dfc2f1432d09b95a22410102d8ae00913fe1b4bd96da45f7ee95f9"
CALIBRATION_TASK_IDS: tuple[str, ...] = (
    "saleor-rc-349d46d906ad",
    "saleor-rc-b05633dae118",
    "saleor-rc-d52a55471bfc",
)
VARIANCE_REPLICATES = 3

# ---------------------------------------------------------------------------
# Instrument-level halting thresholds (addendum section 4). Agent behaviour is
# never a halt reason.
# ---------------------------------------------------------------------------
H3_CONSECUTIVE_INFRA_FAILURES = 3
H4_INSTRUMENT_ERROR_TASKS = 3
H4_WINDOW = 20
H6_CONSECUTIVE_PARSE_OR_TRUNCATION_EMPTY = 5
H7_CONSECUTIVE_BLIND_TASKS = 10  # items where tools WERE attempted and every attempt failed

EXIT_OK = 0
EXIT_BUDGET_ABORT = 2
EXIT_CONFIG_ERROR = 3
EXIT_INFRA_HALT = 4
EXIT_INSTRUMENT_HALT = 5
EXIT_CRASH_HALT = 6
EXIT_LOCKED = 7

# Item-level handling of transport / provider failures (addendum section 3.8).
MAX_INPROCESS_RESTARTS = 2          # an item is restarted from scratch at most 2x per session
RESTART_COOLDOWN_SECONDS = 120.0
INFRA_SESSIONS_BEFORE_EMPTY = 3     # fail-closed EMPTY/infrastructure only in the 3rd failing session
LOCK_MAX_AGE_SECONDS = 6 * 3600.0
# Resume identity: these must never change inside one run; harness files may (logged per session).
FROZEN_CODE_KEYS: tuple[str, ...] = (
    "src/benchmark/strategies/iterative_agent.py",
    "src/benchmark/strategies/repository_tools.py",
    "src/benchmark/wp1b/telemetry.py",
    "protocol_v3",
)

RECORDS_FILE = "agent_run_records.jsonl"
TELEMETRY_FILE = "wp1b_telemetry.jsonl"
SIDECAR_FILE = "wp1b_call_sidecar.jsonl"
LEDGER_FILE = "spend_ledger.jsonl"
STATE_FILE = "run_state.json"
PROGRESS_FILE = "progress.json"
HALT_FILE = "halt_report.json"
SUMMARY_FILE = "run_summary.json"
LOCK_FILE = "run.lock"
INFRA_SESSIONS_FILE = "infra_sessions.json"

# Tool-error classes (mirror scripts/wp1b_sidecar_tool_audit.ERROR_CATALOG).
INSTRUMENT_TOOL_ERRORS: frozenset[str] = frozenset({
    f"Max distinct files limit ({FROZEN_MAX_DISTINCT_FILES}) reached",
    "Cannot read file",
    "Skipped path",
})


class KnobDriftError(RuntimeError):
    """A frozen protocol-v3 knob differs from the code that would run."""


class ManifestError(RuntimeError):
    """A manifest / preregistration artifact does not match its frozen hash."""


class ResumeError(RuntimeError):
    """The output directory cannot be (re)used safely."""


class LockedError(RuntimeError):
    """Another live runner process holds the output directory."""


class ProviderOutageHaltError(RuntimeError):
    """Transport/provider failure persisted for an item in this session; item NOT recorded."""


class AccountOrConfigHaltError(RuntimeError):
    """401/402/403/404 or a missing key: not the item's fault; item NOT recorded."""


class BadRequestHaltError(RuntimeError):
    """HTTP 400/413/422: request shape rejected; instrument halt; item NOT recorded."""


class MaterializationHaltError(RuntimeError):
    """The parent snapshot could not be materialized (I/O, git, lock); item NOT recorded."""


def pid_alive(pid: int) -> bool:
    """True if a process with this PID is running (Windows-safe: never signals it)."""
    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes

        kernel32 = getattr(ctypes, "windll").kernel32  # noqa: B009 - windll exists only on Windows
        handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        code = ctypes.c_ulong()
        ok = kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
        kernel32.CloseHandle(handle)
        return bool(ok) and code.value == 259  # STILL_ACTIVE
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


# ---------------------------------------------------------------------------
# Hash helpers
# ---------------------------------------------------------------------------
def sha256_lines(ids: Sequence[str]) -> str:
    """Hash convention of the WP-1a/WP-1b manifests ("\\n".join(ids) + "\\n")."""
    return hashlib.sha256(("\n".join(ids) + "\n").encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prediction_sha256(paths: Iterable[str]) -> str:
    return hashlib.sha256("\n".join(sorted(paths)).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Work items
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class WorkItem:
    key: str
    task_id: str
    replicate: int
    index: int


def load_main297_items(
    manifest_path: Path,
    *,
    expected_task_ids_sha256: str = FROZEN_MAIN297_TASK_IDS_SHA256,
) -> list[WorkItem]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    task_ids = [str(t) for t in manifest["task_ids"]]
    if len(task_ids) != 297 or len(set(task_ids)) != 297:
        raise ManifestError(f"MAIN_297 manifest must hold 297 unique IDs, got {len(task_ids)}")
    digest = sha256_lines(task_ids)
    if digest != expected_task_ids_sha256 or manifest.get("task_ids_sha256") != expected_task_ids_sha256:
        raise ManifestError(f"MAIN_297 task_ids_sha256 mismatch: {digest}")
    if set(task_ids) & set(CALIBRATION_TASK_IDS):
        raise ManifestError("calibration task IDs must be absent from MAIN_297")
    return [WorkItem(key=tid, task_id=tid, replicate=0, index=i) for i, tid in enumerate(task_ids)]


def load_variance_items(
    prereg_path: Path,
    main297_task_ids: Sequence[str],
    *,
    expected_selection_sha256: str = FROZEN_VARIANCE_SELECTION_SHA256,
) -> list[WorkItem]:
    prereg = json.loads(prereg_path.read_text(encoding="utf-8"))
    if prereg.get("selection_manifest_sha256") != expected_selection_sha256:
        raise ManifestError("variance selection_manifest_sha256 mismatch")
    if prereg.get("first_main_execution_may_count_as_replicate_1") is not False:
        raise ManifestError("variance prereg: the main execution must NOT count as replicate 1")
    selected = [str(t) for t in prereg["selected_15_task_ids"]]
    if len(selected) != 15 or len(set(selected)) != 15:
        raise ManifestError("variance prereg must select exactly 15 unique tasks")
    if not set(selected) <= set(main297_task_ids[:50]):
        raise ManifestError("variance tasks must be a subset of the nested MAIN_50")
    if int(prereg.get("runs_per_selected_task", 0)) != VARIANCE_REPLICATES:
        raise ManifestError("variance prereg must specify 3 runs per selected task")
    items: list[WorkItem] = []
    for rep in range(1, VARIANCE_REPLICATES + 1):
        for tid in selected:
            items.append(WorkItem(key=f"{tid}#r{rep}", task_id=tid, replicate=rep, index=len(items)))
    return items


# ---------------------------------------------------------------------------
# Frozen knobs
# ---------------------------------------------------------------------------
def verify_frozen_knobs(protocol_path: Path | None = None) -> dict[str, Any]:
    """Compare the code constants that would run with the frozen protocol v3."""
    from benchmark.strategies import iterative_agent as ia
    from benchmark.strategies import repository_tools as rt

    observed = {
        "MAX_AGENT_CALLS": ia.MAX_AGENT_CALLS,
        "OBSERVATION_WINDOW_CHARS": ia.OBSERVATION_WINDOW_CHARS,
        "MAX_READ_CHARS": rt.MAX_READ_CHARS,
        "MAX_SEARCH_RESULTS": rt.MAX_SEARCH_RESULTS,
        "MAX_DISTINCT_FILES": rt.MAX_DISTINCT_FILES,
        "MAX_LIST_ENTRIES": rt.MAX_LIST_ENTRIES,
        "MAX_FILE_SIZE": rt.MAX_FILE_SIZE,
    }
    expected = {
        "MAX_AGENT_CALLS": FROZEN_MAX_AGENT_CALLS,
        "OBSERVATION_WINDOW_CHARS": FROZEN_OBSERVATION_WINDOW,
        "MAX_READ_CHARS": FROZEN_MAX_READ_CHARS,
        "MAX_SEARCH_RESULTS": FROZEN_MAX_SEARCH_RESULTS,
        "MAX_DISTINCT_FILES": FROZEN_MAX_DISTINCT_FILES,
        "MAX_LIST_ENTRIES": FROZEN_MAX_LIST_ENTRIES,
        "MAX_FILE_SIZE": FROZEN_MAX_FILE_SIZE,
    }
    drift = {k: (observed[k], expected[k]) for k in expected if observed[k] != expected[k]}
    if drift:
        raise KnobDriftError(f"frozen knob drift: {drift}")
    report: dict[str, Any] = {"knobs": observed, "drift": {}}
    if protocol_path is not None:
        protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
        sections = protocol.get("sections", {})
        cap = sections.get("completion_token_cap_per_model_response", {}).get(
            "agent_control_max_completion_tokens"
        )
        calls = sections.get("proposed_hard_max_rounds", {}).get("MAX_AGENT_CALLS")
        if protocol.get("wp1a") != PROTOCOL_ID or cap != FROZEN_AGENT_CAP or calls != FROZEN_MAX_AGENT_CALLS:
            raise KnobDriftError(
                f"protocol artifact mismatch: id={protocol.get('wp1a')} cap={cap} calls={calls}"
            )
        report["protocol_sha256"] = file_sha256(protocol_path)
    return report


# ---------------------------------------------------------------------------
# Task inputs (byte-identical construction to scripts/wp1b_calibration_run.py)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class TaskBundle:
    task_id: str
    intent_text: str
    parent_commit: str
    universe_paths: tuple[str, ...]


def build_universe(bundle: TaskBundle) -> ArtifactUniverse:
    return ArtifactUniverse(artifacts=tuple(
        ArtifactRef(path=p, artifact_type=ArtifactType.source) for p in bundle.universe_paths
    ))


def build_requirement_change(bundle: TaskBundle) -> RequirementChange:
    """Deterministic WP-1b agent input construction (matches B1 exactly)."""
    return RequirementChange(
        before=f"Repository state at parent commit {bundle.parent_commit}",
        after=bundle.intent_text,
        acceptance_criteria=(),
    )


def load_saleor_bundle(scientific_dir: Path, task_id: str) -> TaskBundle:
    """Load ONLY the public, label-free task inputs (same files as calibration)."""
    base = scientific_dir / task_id
    intent = json.loads((base / "public" / "intent.json").read_text(encoding="utf-8"))
    cu = json.loads((base / "public" / "candidate_universe.json").read_text(encoding="utf-8"))
    manifest = json.loads((base / "case_manifest.json").read_text(encoding="utf-8"))
    return TaskBundle(
        task_id=task_id,
        intent_text=str(intent.get("intent_text", "")),
        parent_commit=str(manifest.get("record", {}).get("parent_commit", "")),
        universe_paths=tuple(str(r["path"]) for r in cu.get("records", [])),
    )


def selected_paths_from_prediction(prediction: ImpactPrediction) -> list[str]:
    return sorted({d.artifact.path for d in prediction.decisions if d.action == ActionKind.regenerate})


# ---------------------------------------------------------------------------
# JSONL helpers (tolerant of a torn last line after a crash)
# ---------------------------------------------------------------------------
def read_jsonl_tolerant(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    good: list[dict[str, Any]] = []
    bad: list[str] = []
    if not path.exists():
        return good, bad
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            bad.append(raw)
            continue
        if isinstance(obj, dict):
            good.append(obj)
        else:
            bad.append(raw)
    return good, bad


def _atomic_write_text(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def _atomic_write_json(path: Path, payload: Any) -> None:
    _atomic_write_text(path, json.dumps(payload, indent=1, sort_keys=True))


def _best_effort_write_json(path: Path, payload: Any, *, attempts: int = 5) -> None:
    """Progress is advisory: a reader holding the file open (Windows) must never halt a paid run."""
    for i in range(attempts):
        try:
            _atomic_write_json(path, payload)
            return
        except OSError:
            time.sleep(0.2 * (i + 1))
    print(f"[main] warning: could not update {path.name} (advisory only)", file=sys.stderr)


# ---------------------------------------------------------------------------
# Halt monitor (instrument-level only)
# ---------------------------------------------------------------------------
@dataclass
class HaltMonitor:
    blind_check: bool = True  # H7 is meaningless for the zero-API stub (it never calls tools)
    consecutive_infra: int = 0
    consecutive_parse_or_trunc_empty: int = 0
    consecutive_blind: int = 0
    recent_instrument: deque[bool] = field(default_factory=lambda: deque(maxlen=H4_WINDOW))

    def observe(self, record: Mapping[str, Any], telemetry: Mapping[str, Any]) -> tuple[str, str] | None:
        infra = bool(record.get("infra_failure"))
        self.consecutive_infra = self.consecutive_infra + 1 if infra else 0
        if self.consecutive_infra >= H3_CONSECUTIVE_INFRA_FAILURES:
            return "H3_INFRA", f"{self.consecutive_infra} consecutive items failed at the transport layer"

        errors = telemetry.get("tool_error_counts", {}) or {}
        instrument_hit = any(str(msg) in INSTRUMENT_TOOL_ERRORS for msg in errors)
        self.recent_instrument.append(instrument_hit)
        if sum(self.recent_instrument) >= H4_INSTRUMENT_ERROR_TASKS:
            return "H4_INSTRUMENT_TOOL_ERRORS", (
                f"instrument-class tool errors in {sum(self.recent_instrument)} of the last "
                f"{len(self.recent_instrument)} items"
            )

        reason = str(record.get("empty_reason", "none"))
        if reason in ("truncation", "parser_failure"):
            self.consecutive_parse_or_trunc_empty += 1
        else:
            self.consecutive_parse_or_trunc_empty = 0
        if self.consecutive_parse_or_trunc_empty >= H6_CONSECUTIVE_PARSE_OR_TRUNCATION_EMPTY:
            return "H6_SYSTEMIC_PARSE_OR_TRUNCATION", (
                f"{self.consecutive_parse_or_trunc_empty} consecutive EMPTY items from truncation/parser_failure"
            )

        attempts = int(record.get("tool_attempts", 0))
        if not infra and self.blind_check and attempts > 0:
            # Items without any tool attempt are agent behaviour and leave the counter unchanged.
            blind = int(record.get("tool_ok_count", 0)) == 0
            self.consecutive_blind = self.consecutive_blind + 1 if blind else 0
            if self.consecutive_blind >= H7_CONSECUTIVE_BLIND_TASKS:
                return "H7_TOOLS_BLIND", (
                    f"{self.consecutive_blind} consecutive items in which every attempted tool call failed"
                )
        return None


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
BundleLoader = Callable[[str], TaskBundle]
Materializer = Callable[[TaskBundle, Path], None]
StrategyFactory = Callable[[ResilientAccountingBackend], IterativeRepositoryAgentStrategy]


@dataclass(frozen=True)
class RunnerConfig:
    run_label: str
    kind: str  # "main297" | "variance" | "dry_run"
    out_dir: Path
    ceiling_usd: float
    worst_case_usd: Mapping[str, float]
    items: Sequence[WorkItem]
    manifest_sha256: str
    code_sha256: Mapping[str, str]
    resume: bool = False
    limit: int | None = None
    stop_file: Path | None = None
    extra_files: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RunOutcome:
    exit_code: int
    status: str
    detail: str
    completed: int
    total: int
    ledger_usd: float


class MainRunner:
    def __init__(
        self,
        config: RunnerConfig,
        *,
        backend: ResilientAccountingBackend,
        load_bundle: BundleLoader,
        materialize: Materializer,
        make_strategy: StrategyFactory,
        workspace_parent: Path | None = None,
        wall_clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._sleep = sleep
        self._session = "s1"
        self._restarts_total = 0
        self._cfg = config
        self._backend = backend
        self._load_bundle = load_bundle
        self._materialize = materialize
        self._make_strategy = make_strategy
        self._workspace_parent = workspace_parent
        self._clock = wall_clock
        self._out = config.out_dir
        self._monitor = HaltMonitor(blind_check=config.kind != "dry_run")
        self._started = self._clock()

    # -- output directory ---------------------------------------------------
    def _state_payload(self) -> dict[str, Any]:
        return {
            "schema": "wp1b_main_run_state_v1",
            "run_label": self._cfg.run_label,
            "kind": self._cfg.kind,
            "protocol": PROTOCOL_ID,
            "model": FROZEN_MODEL,
            "route": FROZEN_ROUTE,
            "temperature": FROZEN_TEMPERATURE,
            "agent_control_max_completion_tokens": FROZEN_AGENT_CAP,
            "max_agent_calls": FROZEN_MAX_AGENT_CALLS,
            "ceiling_usd": self._cfg.ceiling_usd,
            "manifest_sha256": self._cfg.manifest_sha256,
            "code_sha256": dict(self._cfg.code_sha256),
            "n_items": len(self._cfg.items),
        }

    def _prepare_out_dir(self) -> set[str]:
        out = self._out
        state_path = out / STATE_FILE
        run_artifacts = (STATE_FILE, RECORDS_FILE, LEDGER_FILE, TELEMETRY_FILE, SIDECAR_FILE)
        has_run_artifacts = out.exists() and any(
            (out / name).exists() and (out / name).stat().st_size > 0 for name in run_artifacts
        )
        if has_run_artifacts:
            if not self._cfg.resume:
                raise ResumeError(
                    f"{out} exists and is not empty; pass --resume to continue (it is NEVER deleted)"
                )
            if not state_path.exists():
                raise ResumeError(f"{out} has no {STATE_FILE}; refusing to resume into an unknown directory")
            prior = json.loads(state_path.read_text(encoding="utf-8"))
            mine = self._state_payload()
            for k in ("run_label", "kind", "protocol", "model", "route", "manifest_sha256",
                      "n_items", "max_agent_calls", "agent_control_max_completion_tokens"):
                if prior.get(k) != mine.get(k):
                    raise ResumeError(f"resume mismatch on {k!r}: {prior.get(k)!r} != {mine.get(k)!r}")
            prior_code = prior.get("code_sha256", {}) or {}
            for k in FROZEN_CODE_KEYS:
                if k in prior_code and prior_code.get(k) != self._cfg.code_sha256.get(k):
                    raise ResumeError(f"frozen code changed since the run started: {k}")
            if float(mine["ceiling_usd"]) > float(prior["ceiling_usd"]):
                raise ResumeError("the USD ceiling may not be raised on resume")
        else:
            out.mkdir(parents=True, exist_ok=True)
            payload = self._state_payload()
            payload["created_utc"] = utc_now()
            payload["resumes"] = []
            _atomic_write_json(state_path, payload)

        records, bad_records = read_jsonl_tolerant(out / RECORDS_FILE)
        completed = {str(r["work_key"]) for r in records}
        if bad_records:
            self._quarantine(RECORDS_FILE, records, bad_records, keep=_keep_all)
        for name in (TELEMETRY_FILE, SIDECAR_FILE):
            rows, bad = read_jsonl_tolerant(out / name)
            orphans = [r for r in rows if str(r.get("work_key", "")) not in completed]
            if orphans or bad:
                self._quarantine(name, rows, bad, keep=lambda r: str(r.get("work_key", "")) in completed)
        ledger_rows, ledger_bad = read_jsonl_tolerant(out / LEDGER_FILE)
        if ledger_bad:
            self._quarantine(LEDGER_FILE, ledger_rows, ledger_bad, keep=_keep_all)
        for name, payload in self._cfg.extra_files.items():
            target = out / name
            if target.exists():
                target = out / f"{Path(name).stem}_resume_{utc_now()[:19].replace(':', '')}{Path(name).suffix}"
            _atomic_write_json(target, payload)
        state = json.loads(state_path.read_text(encoding="utf-8"))
        prior_halt = out / HALT_FILE
        archived_halt = None
        if prior_halt.exists():
            history = out / "halt_history"
            history.mkdir(exist_ok=True)
            archived_halt = history / f"halt_{len(list(history.iterdir())) + 1:03d}.json"
            os.replace(prior_halt, archived_halt)
        sessions = state.setdefault("sessions", [])
        self._session = f"s{len(sessions) + 1}"
        sessions.append({"session": self._session, "utc": utc_now(), "completed_before": len(completed),
                         "code_sha256": dict(self._cfg.code_sha256)})
        if self._cfg.resume and (records or archived_halt is not None):
            state.setdefault("resumes", []).append({
                "utc": utc_now(),
                "completed_before": len(completed),
                "archived_halt": None if archived_halt is None else archived_halt.name,
            })
        _atomic_write_json(state_path, state)
        return completed

    # -- lock -----------------------------------------------------------------
    def _acquire_lock(self) -> None:
        self._out.mkdir(parents=True, exist_ok=True)
        lock = self._out / LOCK_FILE
        if lock.exists():
            try:
                info = json.loads(lock.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                info = {}
            pid = int(info.get("pid", 0) or 0)
            age = time.time() - float(info.get("created_epoch", 0.0) or 0.0)
            if pid != os.getpid() and pid_alive(pid) and age < LOCK_MAX_AGE_SECONDS:
                raise LockedError(f"{lock} held by live PID {pid} (age {age:.0f}s)")
            lock.unlink(missing_ok=True)
        with lock.open("x", encoding="utf-8") as fh:
            fh.write(json.dumps({"pid": os.getpid(), "created_epoch": time.time(), "utc": utc_now()}))

    def _release_lock(self) -> None:
        lock = self._out / LOCK_FILE
        try:
            info = json.loads(lock.read_text(encoding="utf-8"))
            if int(info.get("pid", 0)) == os.getpid():
                lock.unlink(missing_ok=True)
        except (OSError, json.JSONDecodeError):
            pass

    # -- infra sessions -------------------------------------------------------
    def _bump_infra_sessions(self, key: str) -> int:
        path = self._out / INFRA_SESSIONS_FILE
        data: dict[str, Any] = {}
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                data = {}
        entry = data.setdefault(key, {"sessions": [], "count": 0})
        if self._session not in entry["sessions"]:
            entry["sessions"].append(self._session)
            entry["count"] = len(entry["sessions"])
        _atomic_write_json(path, data)
        return int(entry["count"])

    def _replay_monitor(self) -> None:
        """Rebuild H4/H6/H7 streaks from finished items; H3 restarts after a wait (its remedy)."""
        records, _ = read_jsonl_tolerant(self._out / RECORDS_FILE)
        telemetry, _ = read_jsonl_tolerant(self._out / TELEMETRY_FILE)
        tel = {str(t.get("work_key")): t for t in telemetry}
        for r in records:
            self._monitor.observe(r, tel.get(str(r.get("work_key")), {}))
        self._monitor.consecutive_infra = 0

    def _quarantine(
        self,
        name: str,
        rows: list[dict[str, Any]],
        bad: list[str],
        *,
        keep: Callable[[dict[str, Any]], bool],
    ) -> None:
        path = self._out / name
        kept = [r for r in rows if keep(r)]
        dropped = [r for r in rows if not keep(r)]
        orphan_path = self._out / (Path(name).stem + ".orphaned.jsonl")
        for r in dropped:
            fsync_append(orphan_path, json.dumps(r, sort_keys=True))
        for raw in bad:
            fsync_append(orphan_path, json.dumps({"torn_line": raw}))
        _atomic_write_text(path, "".join(json.dumps(r, sort_keys=True) + "\n" for r in kept))

    # -- execution ----------------------------------------------------------
    def run(self) -> RunOutcome:
        try:
            self._acquire_lock()
        except LockedError as exc:
            return RunOutcome(EXIT_LOCKED, "LOCKED", str(exc), 0, len(self._cfg.items),
                              self._backend.ledger.total_usd)
        try:
            return self._run_locked()
        finally:
            self._release_lock()

    def _run_locked(self) -> RunOutcome:
        completed = self._prepare_out_dir()
        self._replay_monitor()
        items = [it for it in self._cfg.items if it.key not in completed]
        if self._cfg.limit is not None:
            items = items[: self._cfg.limit]
        total = len(self._cfg.items)
        done = len(completed)
        self._write_progress(done, total, current=None, status="RUNNING")
        for item in items:
            if self._cfg.stop_file is not None and self._cfg.stop_file.exists():
                return self._halt(EXIT_INFRA_HALT, "OPERATOR_STOP", f"stop file {self._cfg.stop_file} present",
                                  done, total)
            worst = float(self._cfg.worst_case_usd.get(item.task_id, 0.0))
            if worst <= 0.0:
                return self._halt(EXIT_CONFIG_ERROR, "CONFIG_NO_WORST_CASE",
                                  f"no budget-v2 worst case for {item.task_id}", done, total)
            if self._backend.ledger.total_usd + worst > self._cfg.ceiling_usd:
                return self._halt(
                    EXIT_BUDGET_ABORT, "H1_BUDGET_ABORT",
                    f"ledger {self._backend.ledger.total_usd:.6f} + worst case {worst:.6f} "
                    f"> ceiling {self._cfg.ceiling_usd:.2f} before {item.key}",
                    done, total,
                )
            self._write_progress(done, total, current=item.key, status="RUNNING")
            try:
                record, telemetry, sidecar = self._execute_item(item)
            except BudgetGuardError as exc:
                return self._halt(EXIT_BUDGET_ABORT, "H1_BUDGET_ABORT_PER_REQUEST", str(exc), done, total)
            except AccountOrConfigHaltError as exc:
                return self._halt(EXIT_CONFIG_ERROR, "ACCOUNT_OR_CONFIG_HALT", str(exc), done, total,
                                  extra={"item": item.key})
            except BadRequestHaltError as exc:
                return self._halt(EXIT_INSTRUMENT_HALT, "BAD_REQUEST_HALT", str(exc), done, total,
                                  extra={"item": item.key})
            except ProviderOutageHaltError as exc:
                return self._halt(EXIT_INFRA_HALT, "PROVIDER_OUTAGE_HALT", str(exc), done, total,
                                  extra={"item": item.key})
            except MaterializationHaltError as exc:
                return self._halt(EXIT_INFRA_HALT, "MATERIALIZATION_HALT", str(exc), done, total,
                                  extra={"item": item.key, "cause": repr(exc.__cause__)[:500]})
            except Exception as exc:  # any other exception halts (never silently EMPTY)
                tb = traceback.format_exc()
                origin = _exception_origin(exc)
                return self._halt(EXIT_CRASH_HALT, "CRASH_HALT", f"{type(exc).__name__}: {exc}", done, total,
                                  extra={"traceback": tb[-6000:], "origin": origin, "item": item.key})
            for row in sidecar:
                fsync_append(self._out / SIDECAR_FILE, json.dumps(row, sort_keys=True))
            fsync_append(self._out / TELEMETRY_FILE, json.dumps(telemetry, sort_keys=True))
            fsync_append(self._out / RECORDS_FILE, json.dumps(record, sort_keys=True))
            done += 1
            halt = self._monitor.observe(record, telemetry)
            self._write_progress(done, total, current=None, status="RUNNING", last=record)
            if halt is not None:
                code = EXIT_INFRA_HALT if halt[0] == "H3_INFRA" else EXIT_INSTRUMENT_HALT
                return self._halt(code, halt[0], halt[1], done, total)
        status = "COMPLETE" if done == total else "CHUNK_DONE"
        self._write_progress(done, total, current=None, status=status)
        detail = ("all items finished" if done == total
                  else f"chunk finished; {total - done} items pending (rerun with --resume)")
        summary = self._summary(status, detail, done, total)
        _atomic_write_json(self._out / SUMMARY_FILE, summary)
        return RunOutcome(EXIT_OK, status, summary["detail"], done, total, self._backend.ledger.total_usd)

    def _execute_item(self, item: WorkItem) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
        """Run one item; restart it from scratch after a transport/provider failure.

        Never records an EMPTY because of a provider outage unless the same item
        failed in INFRA_SESSIONS_BEFORE_EMPTY different sessions (then the frozen
        fail-closed rule applies: EMPTY + infra flag).
        """
        last: BackendCallFailedError | None = None
        for restart in range(MAX_INPROCESS_RESTARTS + 1):
            attempt_id = f"{item.key}@{self._session}#r{restart}"
            try:
                return self._execute(item, attempt_id=attempt_id, restarts=restart, fail_closed=False)
            except BackendCallFailedError as exc:
                if exc.classification == ACCOUNT_OR_CONFIG:
                    raise AccountOrConfigHaltError(str(exc)) from exc
                if exc.classification == BAD_REQUEST:
                    raise BadRequestHaltError(str(exc)) from exc
                last = exc
                if restart < MAX_INPROCESS_RESTARTS:
                    self._restarts_total += 1
                    self._sleep(RESTART_COOLDOWN_SECONDS)
        sessions = self._bump_infra_sessions(item.key)
        if sessions >= INFRA_SESSIONS_BEFORE_EMPTY:
            return self._execute(item, attempt_id=f"{item.key}@{self._session}#final",
                                 restarts=MAX_INPROCESS_RESTARTS + 1, fail_closed=True)
        raise ProviderOutageHaltError(
            f"{item.key}: {last.classification if last else '?'} failure persisted after "
            f"{MAX_INPROCESS_RESTARTS + 1} attempts in session {self._session} "
            f"(failing sessions {sessions}/{INFRA_SESSIONS_BEFORE_EMPTY}); item not recorded: {last}"
        )

    def _execute(
        self,
        item: WorkItem,
        *,
        attempt_id: str,
        restarts: int,
        fail_closed: bool,
    ) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
        t_start = self._clock()
        started_utc = utc_now()
        bundle = self._load_bundle(item.task_id)
        if bundle.task_id != item.task_id or not bundle.parent_commit or not bundle.universe_paths:
            raise RuntimeError(f"invalid public bundle for {item.task_id}")
        universe = build_universe(bundle)
        req = build_requirement_change(bundle)
        workspace = Path(tempfile.mkdtemp(prefix="wp1b-main-", dir=self._workspace_parent))
        infra_error = ""
        prediction: ImpactPrediction | None = None
        strategy = self._make_strategy(self._backend)
        self._backend.begin_item(work_key=item.key, task_id=item.task_id, attempt_id=attempt_id)
        try:
            try:
                self._materialize(bundle, workspace)
            except Exception as exc:
                raise MaterializationHaltError(f"{item.key}: parent snapshot materialization failed") from exc
            strategy.begin_run(workspace)
            repo = RepositorySnapshot(
                identity=RepositoryIdentity(name="saleor", url="https://github.com/saleor/saleor"),
                commit_sha=bundle.parent_commit,
                path=str(workspace),
            )
            try:
                prediction = strategy.analyze_impact(
                    repository=repo,
                    requirement_change=req,
                    artifact_universe=universe,
                    max_completion_tokens_per_call=FROZEN_AGENT_CAP,
                )
            except BackendCallFailedError as exc:
                if not fail_closed or exc.classification in (ACCOUNT_OR_CONFIG, BAD_REQUEST):
                    raise
                # Frozen failure semantics, applied only after INFRA_SESSIONS_BEFORE_EMPTY
                # failing sessions: unrecoverable transport failure -> EMPTY + flag.
                infra_error = f"{exc.classification}: {str(exc)[:480]}"
        finally:
            shutil.rmtree(workspace, ignore_errors=True)

        infra = bool(infra_error)
        selected = [] if prediction is None else selected_paths_from_prediction(prediction)
        empty_reason = "infrastructure" if infra else strategy.selection_empty_reason
        if not infra and (len(selected) == 0) != (empty_reason != "none"):
            raise RuntimeError(
                f"prediction/empty_reason inconsistency on {item.key}: {len(selected)} paths, {empty_reason}"
            )
        sidecar = [dict(r, work_key=item.key, replicate=item.replicate)
                   for r in call_sidecar_records(strategy, task_id=item.task_id)]
        telemetry = dict(strategy_telemetry(strategy, task_id=item.task_id))
        telemetry.update({"work_key": item.key, "replicate": item.replicate})
        if infra:
            telemetry.update({"empty_reason": "infrastructure", "prediction_empty": True,
                              "infra_failure": True, "infra_error": infra_error})
        forced_final = bool(sidecar) and bool(sidecar[-1].get("force_final")) and not infra
        tool_rows = [r for r in sidecar if r.get("action") in ("list_files", "read_file", "search_text")]
        tool_ok_count = sum(1 for r in tool_rows if r.get("tool_ok"))
        latency_sum = float(sum(float(r.get("latency_s", 0.0)) for r in sidecar))
        prompt_tokens = strategy.prompt_tokens
        completion_tokens = strategy.completion_tokens
        record: dict[str, Any] = {
            "schema": "wp1b_agent_run_record_v1",
            "run_label": self._cfg.run_label,
            "kind": self._cfg.kind,
            "work_key": item.key,
            "task_id": item.task_id,
            "replicate": item.replicate,
            "manifest_index": item.index,
            "attempt_id": attempt_id,
            "session": self._session,
            "restarts": restarts,
            "protocol": PROTOCOL_ID,
            "model": FROZEN_MODEL,
            "route": FROZEN_ROUTE,
            "temperature": FROZEN_TEMPERATURE,
            "agent_control_max_completion_tokens": FROZEN_AGENT_CAP,
            "max_agent_calls": FROZEN_MAX_AGENT_CALLS,
            "allow_ground_truth_universe": False,
            "universe_size": len(bundle.universe_paths),
            "selected_paths": selected,
            "predicted_set_size": len(selected),
            "prediction_sha256": prediction_sha256(selected),
            "prediction_empty": len(selected) == 0,
            "empty_reason": empty_reason,
            "infra_failure": infra,
            "infra_error": infra_error,
            "forced_final": forced_final,
            "model_calls": strategy.model_call_count,
            "http_attempts": self._backend.item_http_attempts,
            "transport_retries": self._backend.item_transport_retries,
            "tool_calls": strategy.tool_call_count,
            "tool_attempts": len(tool_rows),
            "tool_ok_count": tool_ok_count,
            "token_usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": strategy.total_tokens,
                "usd_cost": frozen_usd(prompt_tokens, completion_tokens),
            },
            "latency_s_sum": round(latency_sum, 4),
            "wall_seconds": round(self._clock() - t_start, 4),
            "started_utc": started_utc,
            "finished_utc": utc_now(),
            "worst_case_usd_budget_v2": float(self._cfg.worst_case_usd.get(item.task_id, 0.0)),
            "code_sha256": dict(self._cfg.code_sha256),
        }
        return record, telemetry, sidecar

    # -- reporting ----------------------------------------------------------
    def _write_progress(
        self,
        done: int,
        total: int,
        *,
        current: str | None,
        status: str,
        last: Mapping[str, Any] | None = None,
    ) -> None:
        ledger = self._backend.ledger
        elapsed = self._clock() - self._started
        records, _ = read_jsonl_tolerant(self._out / RECORDS_FILE)
        empty_by_reason: dict[str, int] = {}
        forced = 0
        for r in records:
            if r.get("prediction_empty"):
                reason = str(r.get("empty_reason"))
                empty_by_reason[reason] = empty_by_reason.get(reason, 0) + 1
            forced += int(bool(r.get("forced_final")))
        n = len(records)
        per_item = ledger.total_usd / n if n else 0.0
        payload = {
            "run_label": self._cfg.run_label,
            "status": status,
            "completed": done,
            "total": total,
            "progress_line": f"{self._cfg.run_label} - {done}/{total} complete",
            "current_item": current,
            "ledger_usd": round(ledger.total_usd, 6),
            "ceiling_usd": self._cfg.ceiling_usd,
            "projected_total_usd": round(per_item * total, 4) if n else None,
            "logical_calls": ledger.logical_calls,
            "http_attempts": ledger.http_attempts,
            "failed_calls": ledger.failed_calls,
            "empty_by_reason": empty_by_reason,
            "forced_final_items": forced,
            "infra_failed_items": sum(1 for r in records if r.get("infra_failure")),
            "session": self._session,
            "item_restarts_this_session": self._restarts_total,
            "elapsed_seconds_this_session": round(elapsed, 1),
            "last_item": None if last is None else {
                "work_key": last.get("work_key"),
                "calls": last.get("model_calls"),
                "empty_reason": last.get("empty_reason"),
                "usd": last.get("token_usage", {}).get("usd_cost"),
            },
            "updated_utc": utc_now(),
        }
        _best_effort_write_json(self._out / PROGRESS_FILE, payload)

    def _summary(self, status: str, detail: str, done: int, total: int) -> dict[str, Any]:
        ledger = self._backend.ledger
        return {
            "artifact": "wp1b_main_run_summary",
            "run_label": self._cfg.run_label,
            "kind": self._cfg.kind,
            "status": status,
            "detail": detail,
            "completed": done,
            "total": total,
            "ledger_usd": round(ledger.total_usd, 6),
            "ceiling_usd": self._cfg.ceiling_usd,
            "logical_calls": ledger.logical_calls,
            "http_attempts": ledger.http_attempts,
            "failed_calls": ledger.failed_calls,
            "prompt_tokens": ledger.total_prompt_tokens,
            "completion_tokens": ledger.total_completion_tokens,
            "finished_utc": utc_now(),
        }

    def _halt(
        self,
        code: int,
        status: str,
        detail: str,
        done: int,
        total: int,
        *,
        extra: Mapping[str, Any] | None = None,
    ) -> RunOutcome:
        report = self._summary(status, detail, done, total)
        report["exit_code"] = code
        report["resumable"] = code in (EXIT_INFRA_HALT, EXIT_CRASH_HALT)
        report["session"] = self._session
        report["main50_complete"] = done >= 50 if self._cfg.kind == "main297" else None
        if extra:
            report.update(dict(extra))
        _atomic_write_json(self._out / HALT_FILE, report)
        _atomic_write_json(self._out / SUMMARY_FILE, report)
        self._write_progress(done, total, current=None, status=status)
        return RunOutcome(code, status, detail, done, total, self._backend.ledger.total_usd)


def _keep_all(_row: dict[str, Any]) -> bool:
    return True


def _exception_origin(exc: BaseException) -> str:
    """Classify the DEEPEST project frame of an unexpected exception."""
    tb = exc.__traceback__
    frames: list[str] = []
    while tb is not None:
        frames.append(tb.tb_frame.f_code.co_filename.replace("\\", "/"))
        tb = tb.tb_next
    project = [f for f in frames if "/src/benchmark/" in f or "/scripts/" in f]
    if not project:
        return "OTHER"
    deepest = project[-1]
    if deepest.endswith("strategies/iterative_agent.py") or deepest.endswith("strategies/repository_tools.py"):
        return "FROZEN_AGENT_CODE"
    if "/src/benchmark/wp1b/" in deepest or "/scripts/wp1b_" in deepest:
        return "HARNESS_CODE"
    return "OTHER"


# ---------------------------------------------------------------------------
# Zero-API stub backend (dry run): exercises the full pipeline on real data.
# ---------------------------------------------------------------------------
class DryRunStubBackend:
    """Zero-API stand-in. Call 1 returns ``final`` with the first universe path.

    Token counts use the same local estimate as ``OpenRouterBackend``
    (len(prompt) // 4) so the dry run can be compared with budget-v2 base
    prompt estimates. No network access.
    """

    def __init__(self) -> None:
        self.prompts_chars: list[int] = []

    def count_prompt_tokens(self, prompt: str) -> int:
        return max(1, len(prompt) // 4)

    async def generate_structured(
        self,
        prompt: str,
        *,
        schema_name: str,  # noqa: ARG002 - protocol signature
        schema: dict[str, Any],  # noqa: ARG002 - protocol signature
        temperature: float = 0.0,  # noqa: ARG002 - protocol signature
        max_tokens: int = 4096,  # noqa: ARG002 - protocol signature
    ) -> LLMResponse:
        self.prompts_chars.append(len(prompt))
        first = ""
        lines = prompt.splitlines()
        if "Editable paths:" in lines:
            start = lines.index("Editable paths:") + 1
            for line in lines[start:]:
                stripped = line.strip()
                if not stripped.startswith("- "):
                    break
                first = stripped[2:]
                break
        text = json.dumps({"action": "final", "selected_paths": [first], "rationale": "dry run"})
        p = self.count_prompt_tokens(prompt)
        return LLMResponse(text, TokenUsage(p, 10, p + 10), "stop")


def run_coroutine(coro: Any) -> Any:
    """Tiny helper for scripts (kept here so scripts stay thin)."""
    return asyncio.get_event_loop().run_until_complete(coro)


def python_identity() -> dict[str, str]:
    return {"python": sys.version.split()[0], "platform": sys.platform}
