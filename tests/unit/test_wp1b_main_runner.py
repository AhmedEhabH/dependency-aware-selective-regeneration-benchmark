"""WP-1b MAIN_297 runner harness - ZERO-API tests (stub backends only).

Binds to:
- research/wp1a/wp1a_failure_semantics.json (max 3 byte-identical transport
  retries; unrecoverable transport failure -> EMPTY + flag; no silent exclusion)
- research/wp1b/wp1b_budget_model_v2.json (per-task worst case; ceilings)
- docs/WP1B_MAIN297_EXECUTION_ADDENDUM_2026-09-22.md (resume, halting H1-H7,
  label-access guard, predictions persisted)
"""
from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from benchmark.core.exceptions import ModelBackendError
from benchmark.core.models import LLMResponse, TokenUsage
from benchmark.strategies.iterative_agent import IterativeRepositoryAgentStrategy
from benchmark.wp1b import main_runner as mr
from benchmark.wp1b.label_guard import is_forbidden_relative
from benchmark.wp1b.resilient_backend import (
    BudgetGuardError,
    ResilientAccountingBackend,
    SpendLedger,
    frozen_usd,
)

PROJECT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
class _Inner:
    """Scripted inner backend. Each entry: a dict response or an exception."""

    def __init__(self, script: list[Any]) -> None:
        self.script = list(script)
        self.calls = 0
        self.prompts: list[str] = []

    def count_prompt_tokens(self, prompt: str) -> int:
        return max(1, len(prompt) // 4)

    async def generate_structured(self, prompt: str, *, schema_name: str, schema: dict[str, Any],
                                  temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:
        self.calls += 1
        self.prompts.append(prompt)
        entry = self.script[min(self.calls - 1, len(self.script) - 1)]
        if isinstance(entry, Exception):
            raise entry
        text = json.dumps(entry) if isinstance(entry, dict) else str(entry)
        return LLMResponse(text, TokenUsage(100, 10, 110), "stop")


def _run(coro: Any) -> Any:
    return asyncio.new_event_loop().run_until_complete(coro)


def _backend(tmp_path: Path, inner: Any, ceiling: float = 5.0) -> tuple[ResilientAccountingBackend, list[float]]:
    sleeps: list[float] = []
    ledger = SpendLedger.open(tmp_path / "ledger.jsonl")
    return ResilientAccountingBackend(inner, ledger=ledger, ceiling_usd=ceiling, sleep=sleeps.append), sleeps


FILES = {
    "app/models.py": "class Order:\n    currency = 'USD'\n",
    "app/views.py": "from app.models import Order\n\ndef view():\n    return Order()\n",
    "app/utils.py": "def helper():\n    return 1\n",
}


def _bundle(task_id: str) -> mr.TaskBundle:
    return mr.TaskBundle(task_id=task_id, intent_text=f"Change currency handling ({task_id})",
                         parent_commit="a" * 40, universe_paths=tuple(sorted(FILES)))


def _materialize(bundle: mr.TaskBundle, workspace: Path) -> None:
    for rel, text in FILES.items():
        p = workspace / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


GOOD_SCRIPT: list[Any] = [
    {"action": "search_text", "query": "currency", "path": "."},
    {"action": "read_file", "path": "app/models.py"},
    {"action": "final", "selected_paths": ["app/models.py"], "rationale": "currency lives here"},
]


def _items(n: int) -> list[mr.WorkItem]:
    return [mr.WorkItem(key=f"t{i}", task_id=f"t{i}", replicate=0, index=i) for i in range(n)]


class _PerItemInner(_Inner):
    """Restarts the script whenever a new prompt (new task) begins."""

    def __init__(self, script: list[Any]) -> None:
        super().__init__(script)
        self._pos = 0

    async def generate_structured(self, prompt: str, *, schema_name: str, schema: dict[str, Any],
                                  temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:
        if prompt.startswith("You are analyzing") and "[call " not in prompt and "[result]" not in prompt:
            self._pos = 0
        entry = self.script[min(self._pos, len(self.script) - 1)]
        self._pos += 1
        self.calls += 1
        if isinstance(entry, Exception):
            raise entry
        return LLMResponse(json.dumps(entry), TokenUsage(100, 10, 110), "stop")


def _runner(tmp_path: Path, inner: Any, *, n: int = 4, ceiling: float = 5.0, resume: bool = False,
            materialize: Any = _materialize, worst: float = 0.01, out: Path | None = None,
            code: dict[str, str] | None = None) -> mr.MainRunner:
    out_dir = out or (tmp_path / "out")
    out_dir.mkdir(parents=True, exist_ok=True)
    ledger = SpendLedger.open(out_dir / mr.LEDGER_FILE)
    backend = ResilientAccountingBackend(inner, ledger=ledger, ceiling_usd=ceiling, sleep=lambda _s: None)
    items = _items(n)
    cfg = mr.RunnerConfig(
        run_label="TEST", kind="main297", out_dir=out_dir, ceiling_usd=ceiling,
        worst_case_usd={it.task_id: worst for it in items}, items=items,
        manifest_sha256="m" * 64, code_sha256=code or {"x": "y"}, resume=resume,
    )
    return mr.MainRunner(
        cfg, backend=backend, load_bundle=_bundle, materialize=materialize,
        make_strategy=lambda b: IterativeRepositoryAgentStrategy(backend=b, agent_control_max_completion_tokens=1024),
        workspace_parent=tmp_path, sleep=lambda _s: None,
    )


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


# ---------------------------------------------------------------------------
# resilient backend
# ---------------------------------------------------------------------------
def test_transient_errors_retried_with_backoff_then_success(tmp_path: Path) -> None:
    inner = _Inner([ModelBackendError("OpenRouter HTTP 429: slow down"),
                    ModelBackendError("OpenRouter connection failed: reset"),
                    {"action": "final", "selected_paths": ["a.py"], "rationale": "r"}])
    backend, sleeps = _backend(tmp_path, inner)
    backend.begin_item(work_key="k", task_id="k")
    resp = _run(backend.generate_structured("p" * 400, schema_name="s", schema={"x": 1}, max_tokens=1024))
    assert "final" in resp.text
    assert inner.calls == 3
    assert sleeps == [10.0, 60.0]
    assert backend.item_http_attempts == 3 and backend.item_transport_retries == 2
    entries = _jsonl(tmp_path / "ledger.jsonl")
    assert len(entries) == 1 and entries[0]["kind"] == "call" and entries[0]["http_attempts"] == 3
    assert entries[0]["usd"] == pytest.approx(frozen_usd(100, 10))


def test_identical_request_bytes_on_retry(tmp_path: Path) -> None:
    inner = _Inner([ModelBackendError("OpenRouter HTTP 503: x"), {"action": "final", "selected_paths": ["a"]}])
    backend, _ = _backend(tmp_path, inner)
    _run(backend.generate_structured("same prompt", schema_name="s", schema={"x": 1}, max_tokens=1024))
    assert inner.prompts == ["same prompt", "same prompt"]


def test_non_transient_error_not_retried(tmp_path: Path) -> None:
    inner = _Inner([ModelBackendError("OpenRouter HTTP 400: bad request")])
    backend, sleeps = _backend(tmp_path, inner)
    with pytest.raises(ModelBackendError):
        _run(backend.generate_structured("p", schema_name="s", schema={"x": 1}, max_tokens=1024))
    assert inner.calls == 1 and sleeps == []
    entries = _jsonl(tmp_path / "ledger.jsonl")
    assert entries[0]["kind"] == "failure" and entries[0]["transient"] is False


def test_transport_retry_budget_is_exactly_three(tmp_path: Path) -> None:
    inner = _Inner([ModelBackendError("OpenRouter HTTP 502: bad gateway")] * 10)
    backend, sleeps = _backend(tmp_path, inner)
    with pytest.raises(ModelBackendError):
        _run(backend.generate_structured("p", schema_name="s", schema={"x": 1}, max_tokens=1024))
    assert inner.calls == 4  # 1 + 3 retries
    assert sleeps == [10.0, 60.0, 180.0]


def test_retry_rule_cannot_be_changed(tmp_path: Path) -> None:
    ledger = SpendLedger.open(tmp_path / "l.jsonl")
    with pytest.raises(ValueError):
        ResilientAccountingBackend(_Inner([]), ledger=ledger, ceiling_usd=1.0, max_retries=1)


def test_per_request_guard_blocks_before_sending(tmp_path: Path) -> None:
    inner = _Inner([{"action": "final", "selected_paths": ["a"]}])
    backend, _ = _backend(tmp_path, inner, ceiling=0.0005)
    with pytest.raises(BudgetGuardError):
        _run(backend.generate_structured("p" * 4000, schema_name="s", schema={"x": 1}, max_tokens=1024))
    assert inner.calls == 0


def test_ledger_survives_torn_last_line(tmp_path: Path) -> None:
    path = tmp_path / "ledger.jsonl"
    torn = json.dumps({"kind": "call", "usd": 0.5, "http_attempts": 1}) + "\n{\"kind\": \"ca"
    path.write_text(torn, encoding="utf-8")
    ledger = SpendLedger.open(path)
    assert ledger.total_usd == pytest.approx(0.5) and ledger.logical_calls == 1


# ---------------------------------------------------------------------------
# runner
# ---------------------------------------------------------------------------
def test_runner_persists_predictions_and_completes(tmp_path: Path) -> None:
    runner = _runner(tmp_path, _PerItemInner(GOOD_SCRIPT), n=4)
    outcome = runner.run()
    assert outcome.exit_code == mr.EXIT_OK and outcome.status == "COMPLETE"
    out = tmp_path / "out"
    records = _jsonl(out / mr.RECORDS_FILE)
    assert [r["work_key"] for r in records] == ["t0", "t1", "t2", "t3"]
    for r in records:
        assert r["selected_paths"] == ["app/models.py"]
        assert r["prediction_empty"] is False and r["empty_reason"] == "none"
        assert r["allow_ground_truth_universe"] is False
        assert r["model_calls"] == 3 and r["http_attempts"] == 3
        assert r["protocol"] == mr.PROTOCOL_ID
    sidecar = _jsonl(out / mr.SIDECAR_FILE)
    assert len(sidecar) == 12 and all("work_key" in s for s in sidecar)
    telemetry = _jsonl(out / mr.TELEMETRY_FILE)
    assert len(telemetry) == 4 and telemetry[0]["successful_reads"] == 1
    progress = json.loads((out / mr.PROGRESS_FILE).read_text(encoding="utf-8"))
    assert progress["completed"] == 4 and progress["progress_line"] == "TEST - 4/4 complete"
    ledger = SpendLedger.open(out / mr.LEDGER_FILE)
    assert ledger.logical_calls == 12
    assert ledger.total_usd == pytest.approx(sum(r["token_usage"]["usd_cost"] for r in records))


def test_runner_refuses_existing_run_without_resume_and_never_deletes(tmp_path: Path) -> None:
    out = tmp_path / "out"
    out.mkdir()
    (out / mr.RECORDS_FILE).write_text('{"work_key": "x"}\n', encoding="utf-8")
    runner = _runner(tmp_path, _PerItemInner(GOOD_SCRIPT), n=1, out=out)
    with pytest.raises(mr.ResumeError):
        runner.run()  # no --resume
    runner = _runner(tmp_path, _PerItemInner(GOOD_SCRIPT), n=1, out=out, resume=True)
    with pytest.raises(mr.ResumeError):
        runner.run()  # --resume but no run_state.json: unknown directory
    assert (out / mr.RECORDS_FILE).read_text(encoding="utf-8") == '{"work_key": "x"}\n'


def test_unrelated_files_do_not_block_a_fresh_start(tmp_path: Path) -> None:
    out = tmp_path / "out"
    out.mkdir()
    (out / "notes.txt").write_text("precious", encoding="utf-8")
    outcome = _runner(tmp_path, _PerItemInner(GOOD_SCRIPT), n=1, out=out).run()
    assert outcome.exit_code == mr.EXIT_OK
    assert (out / "notes.txt").read_text(encoding="utf-8") == "precious"


def test_crash_then_resume_skips_finished_and_quarantines_orphans(tmp_path: Path) -> None:
    calls = {"n": 0}

    def flaky_materialize(bundle: mr.TaskBundle, workspace: Path) -> None:
        calls["n"] += 1
        if bundle.task_id == "t2":
            raise RuntimeError("disk hiccup")
        _materialize(bundle, workspace)

    outcome = _runner(tmp_path, _PerItemInner(GOOD_SCRIPT), n=4, materialize=flaky_materialize).run()
    assert outcome.exit_code == mr.EXIT_INFRA_HALT and outcome.completed == 2
    out = tmp_path / "out"
    halt = json.loads((out / mr.HALT_FILE).read_text(encoding="utf-8"))
    assert halt["status"] == "MATERIALIZATION_HALT" and halt["item"] == "t2" and halt["resumable"] is True
    assert "disk hiccup" in halt["cause"]
    # simulate a torn orphan sidecar line from the crashed item
    with (out / mr.SIDECAR_FILE).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"work_key": "t2", "call_index": 1}) + "\n{\"work_key\": \"t2\"")
    outcome2 = _runner(tmp_path, _PerItemInner(GOOD_SCRIPT), n=4, resume=True).run()
    assert outcome2.exit_code == mr.EXIT_OK and outcome2.completed == 4
    records = _jsonl(out / mr.RECORDS_FILE)
    assert [r["work_key"] for r in records] == ["t0", "t1", "t2", "t3"]
    sidecar = _jsonl(out / mr.SIDECAR_FILE)
    assert len(sidecar) == 12
    orphans = (out / "wp1b_call_sidecar.orphaned.jsonl").read_text(encoding="utf-8")
    assert "torn_line" in orphans and '"work_key": "t2"' in orphans
    state = json.loads((out / mr.STATE_FILE).read_text(encoding="utf-8"))
    assert len(state["resumes"]) == 1 and state["resumes"][0]["archived_halt"] == "halt_001.json"
    assert not (out / mr.HALT_FILE).exists() and (out / "halt_history" / "halt_001.json").exists()
    summary = json.loads((out / mr.SUMMARY_FILE).read_text(encoding="utf-8"))
    assert summary["status"] == "COMPLETE"


def test_chunked_execution_until_complete(tmp_path: Path) -> None:
    statuses = []
    for _ in range(3):
        runner = _runner(tmp_path, _PerItemInner(GOOD_SCRIPT), n=5, resume=True)
        object.__setattr__(runner._cfg, "limit", 2)
        statuses.append(runner.run().status)
    assert statuses == ["CHUNK_DONE", "CHUNK_DONE", "COMPLETE"]
    records = _jsonl(tmp_path / "out" / mr.RECORDS_FILE)
    assert [r["work_key"] for r in records] == ["t0", "t1", "t2", "t3", "t4"]
    progress = json.loads((tmp_path / "out" / mr.PROGRESS_FILE).read_text(encoding="utf-8"))
    assert progress["status"] == "COMPLETE" and progress["completed"] == 5


def test_resume_identity_frozen_vs_harness_code(tmp_path: Path) -> None:
    frozen = "src/benchmark/strategies/iterative_agent.py"
    base = {frozen: "A", "src/benchmark/wp1b/main_runner.py": "H1"}
    runner = _runner(tmp_path, _PerItemInner(GOOD_SCRIPT), n=3, code=base)
    object.__setattr__(runner._cfg, "limit", 1)
    assert runner.run().status == "CHUNK_DONE"
    # a harness fix between chunks is allowed and logged per session
    harness_fix = {frozen: "A", "src/benchmark/wp1b/main_runner.py": "H2"}
    runner = _runner(tmp_path, _PerItemInner(GOOD_SCRIPT), n=3, resume=True, code=harness_fix)
    object.__setattr__(runner._cfg, "limit", 1)
    assert runner.run().status == "CHUNK_DONE"
    state = json.loads((tmp_path / "out" / mr.STATE_FILE).read_text(encoding="utf-8"))
    assert [x["code_sha256"]["src/benchmark/wp1b/main_runner.py"] for x in state["sessions"]] == ["H1", "H2"]
    # a change to FROZEN agent code is refused
    agent_change = {frozen: "B", "src/benchmark/wp1b/main_runner.py": "H2"}
    with pytest.raises(mr.ResumeError):
        _runner(tmp_path, _PerItemInner(GOOD_SCRIPT), n=3, resume=True, code=agent_change).run()


def test_provider_outage_never_records_empty_until_third_failing_session(tmp_path: Path) -> None:
    down = [ModelBackendError("OpenRouter HTTP 503: down")]
    outcome = _runner(tmp_path, _PerItemInner(down), n=4).run()
    assert outcome.exit_code == mr.EXIT_INFRA_HALT and outcome.status == "PROVIDER_OUTAGE_HALT"
    out = tmp_path / "out"
    assert not (out / mr.RECORDS_FILE).exists() or _jsonl(out / mr.RECORDS_FILE) == []
    ledger = [e for e in _jsonl(out / mr.LEDGER_FILE) if e["kind"] == "failure"]
    assert len(ledger) == 3 and all(e["http_attempts"] == 4 for e in ledger)  # 3 attempts x (1 + 3 retries)
    assert {e["attempt_id"] for e in ledger} == {"t0@s1#r0", "t0@s1#r1", "t0@s1#r2"}
    # session 2: still down -> halt again, nothing recorded
    assert _runner(tmp_path, _PerItemInner(down), n=4, resume=True).run().status == "PROVIDER_OUTAGE_HALT"
    # session 3: still down -> the frozen fail-closed rule applies to t0 only, then t1 halts
    outcome3 = _runner(tmp_path, _PerItemInner(down), n=4, resume=True).run()
    assert outcome3.status == "PROVIDER_OUTAGE_HALT"
    records = _jsonl(out / mr.RECORDS_FILE)
    assert [r["work_key"] for r in records] == ["t0"]
    assert records[0]["empty_reason"] == "infrastructure" and records[0]["infra_failure"] is True
    sessions = json.loads((out / mr.INFRA_SESSIONS_FILE).read_text(encoding="utf-8"))
    assert sessions["t0"]["count"] == 3 and sessions["t1"]["count"] == 1
    # provider back: t1.. complete normally
    outcome4 = _runner(tmp_path, _PerItemInner(GOOD_SCRIPT), n=4, resume=True).run()
    assert outcome4.status == "COMPLETE"
    assert [r["empty_reason"] for r in _jsonl(out / mr.RECORDS_FILE)] == ["infrastructure", "none", "none", "none"]


class _FailFirstAttempt(_PerItemInner):
    """Every call of the first attempt of t0 fails (transport); later attempts work."""

    def __init__(self, script: list[Any]) -> None:
        super().__init__(script)
        self.fail_budget = 4  # 1 + 3 retries -> the whole first attempt fails

    async def generate_structured(self, prompt: str, *, schema_name: str, schema: dict[str, Any],
                                  temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:
        if self.fail_budget > 0:
            self.fail_budget -= 1
            raise ModelBackendError("OpenRouter request failed: Remote end closed connection without response")
        return await super().generate_structured(prompt, schema_name=schema_name, schema=schema,
                                                 temperature=temperature, max_tokens=max_tokens)


def test_transient_item_failure_restarts_in_process(tmp_path: Path) -> None:
    import http.client

    inner = _FailFirstAttempt(GOOD_SCRIPT)
    # make the generic wrapper carry a transport cause, like openrouter_backend does
    orig = inner.generate_structured

    async def wrapped(prompt: str, **kw: Any) -> LLMResponse:
        try:
            return await orig(prompt, **kw)
        except ModelBackendError as exc:
            raise exc from http.client.RemoteDisconnected("closed")

    inner.generate_structured = wrapped  # type: ignore[method-assign]
    outcome = _runner(tmp_path, inner, n=2).run()
    assert outcome.status == "COMPLETE"
    records = _jsonl(tmp_path / "out" / mr.RECORDS_FILE)
    assert records[0]["restarts"] == 1 and records[0]["attempt_id"] == "t0@s1#r1"
    assert records[0]["empty_reason"] == "none" and records[1]["restarts"] == 0


@pytest.mark.parametrize(("message", "status", "code"), [
    ("OpenRouter HTTP 402: insufficient credits", "ACCOUNT_OR_CONFIG_HALT", mr.EXIT_CONFIG_ERROR),
    ("OpenRouter HTTP 401: bad key", "ACCOUNT_OR_CONFIG_HALT", mr.EXIT_CONFIG_ERROR),
    ("OpenRouter HTTP 400: bad schema", "BAD_REQUEST_HALT", mr.EXIT_INSTRUMENT_HALT),
])
def test_account_and_bad_request_halt_without_recording(tmp_path: Path, message: str, status: str,
                                                        code: int) -> None:
    outcome = _runner(tmp_path, _PerItemInner([ModelBackendError(message)]), n=3).run()
    assert outcome.status == status and outcome.exit_code == code
    assert not (tmp_path / "out" / mr.RECORDS_FILE).exists()


def test_backend_error_classification() -> None:
    import http.client
    import ssl as _ssl

    from benchmark.wp1b.resilient_backend import classify_backend_error

    def wrapped(cause: BaseException) -> ModelBackendError:
        err = ModelBackendError(f"OpenRouter request failed: {cause}")
        err.__cause__ = cause
        return err

    assert classify_backend_error(ModelBackendError("OpenRouter HTTP 429: x")) == "TRANSPORT"
    assert classify_backend_error(ModelBackendError("OpenRouter HTTP 502: x")) == "TRANSPORT"
    assert classify_backend_error(ModelBackendError("OpenRouter HTTP 408: x")) == "TRANSPORT"
    assert classify_backend_error(ModelBackendError("OpenRouter HTTP 404: no endpoints")) == "ACCOUNT_OR_CONFIG"
    assert classify_backend_error(ModelBackendError("OpenRouter HTTP 422: bad")) == "BAD_REQUEST"
    assert classify_backend_error(ModelBackendError("OpenRouter request timed out after 120.0s")) == "TRANSPORT"
    assert classify_backend_error(wrapped(http.client.RemoteDisconnected("closed"))) == "TRANSPORT"
    assert classify_backend_error(wrapped(ConnectionResetError(10054, "reset"))) == "TRANSPORT"
    assert classify_backend_error(wrapped(http.client.IncompleteRead(b"x"))) == "TRANSPORT"
    assert classify_backend_error(wrapped(_ssl.SSLError("eof"))) == "TRANSPORT"
    assert classify_backend_error(ModelBackendError("OpenRouter HTTP 402: credits")) == "ACCOUNT_OR_CONFIG"
    assert classify_backend_error(ModelBackendError("API key not found in environment variable X")) == \
        "ACCOUNT_OR_CONFIG"
    assert classify_backend_error(ModelBackendError("OpenRouter HTTP 400: bad")) == "BAD_REQUEST"
    assert classify_backend_error(ModelBackendError("OpenRouter returned malformed JSON: x")) == "PROVIDER_GLITCH"


def test_lock_blocks_live_process_and_recovers_stale(tmp_path: Path) -> None:
    import os

    out = tmp_path / "out"
    out.mkdir()
    (out / mr.LOCK_FILE).write_text(json.dumps({"pid": os.getppid(), "created_epoch": __import__("time").time()}),
                                    encoding="utf-8")
    outcome = _runner(tmp_path, _PerItemInner(GOOD_SCRIPT), n=1).run()
    assert outcome.exit_code == mr.EXIT_LOCKED and outcome.status == "LOCKED"
    (out / mr.LOCK_FILE).write_text(json.dumps({"pid": 999_999_9, "created_epoch": 0}), encoding="utf-8")
    outcome = _runner(tmp_path, _PerItemInner(GOOD_SCRIPT), n=1).run()
    assert outcome.exit_code == mr.EXIT_OK and not (out / mr.LOCK_FILE).exists()


def test_monitor_replay_spans_chunks(tmp_path: Path) -> None:
    bad_final: list[Any] = [{"action": "final", "selected_paths": ["not/in/universe.py"], "rationale": "x"}]
    runner = _runner(tmp_path, _PerItemInner(bad_final), n=8)
    object.__setattr__(runner._cfg, "limit", 3)
    assert runner.run().status == "CHUNK_DONE"
    # 3 parser_failure EMPTY so far; the streak continues across the chunk boundary -> H6 at item 5
    runner = _runner(tmp_path, _PerItemInner(bad_final), n=8, resume=True)
    outcome = runner.run()
    assert outcome.status == "H6_SYSTEMIC_PARSE_OR_TRUNCATION" and outcome.completed == 5


def test_pre_item_budget_abort(tmp_path: Path) -> None:
    outcome = _runner(tmp_path, _PerItemInner(GOOD_SCRIPT), n=3, ceiling=0.02, worst=0.0199).run()
    assert outcome.exit_code == mr.EXIT_BUDGET_ABORT and outcome.status == "H1_BUDGET_ABORT"
    assert outcome.completed == 1


def test_agent_behaviour_never_halts_main(tmp_path: Path) -> None:
    # every task exhausts 8 calls with invalid finals -> EMPTY parser_failure? No:
    # repeated identical reads -> rejected repeats -> forced final with a valid path.
    loop_script: list[Any] = [{"action": "read_file", "path": "app/views.py"}] * 7 + [
        {"action": "final", "selected_paths": ["app/views.py"], "rationale": "forced"}]
    outcome = _runner(tmp_path, _PerItemInner(loop_script), n=5).run()
    assert outcome.exit_code == mr.EXIT_OK
    records = _jsonl(tmp_path / "out" / mr.RECORDS_FILE)
    assert all(r["forced_final"] is True for r in records)
    telemetry = _jsonl(tmp_path / "out" / mr.TELEMETRY_FILE)
    assert all(t["rejected_repeat_count"] == 6 for t in telemetry)


def test_round_cap_empty_is_data_not_halt(tmp_path: Path) -> None:
    bad_final: list[Any] = [{"action": "final", "selected_paths": ["not/in/universe.py"], "rationale": "x"}]
    outcome = _runner(tmp_path, _PerItemInner(bad_final), n=6).run()
    # parser_failure EMPTY x5 consecutive -> H6 (systemic) halts; fewer would not.
    assert outcome.status == "H6_SYSTEMIC_PARSE_OR_TRUNCATION"
    records = _jsonl(tmp_path / "out" / mr.RECORDS_FILE)
    assert len(records) == 5 and all(r["empty_reason"] == "parser_failure" for r in records)


def test_halt_monitor_rules() -> None:
    mon = mr.HaltMonitor()
    for _ in range(30):
        assert mon.observe({"empty_reason": "round_cap", "infra_failure": False, "tool_attempts": 2,
                            "tool_ok_count": 1}, {"successful_reads": 1}) is None
    mon = mr.HaltMonitor()
    halt = None
    for _ in range(mr.H7_CONSECUTIVE_BLIND_TASKS):
        halt = mon.observe({"empty_reason": "none", "tool_attempts": 3, "tool_ok_count": 0}, {})
    assert halt is not None and halt[0] == "H7_TOOLS_BLIND"
    # items that never call a tool (immediate final) are behaviour: never counted as blind
    mon = mr.HaltMonitor()
    res = [mon.observe({"empty_reason": "none", "tool_attempts": 0, "tool_ok_count": 0}, {}) for _ in range(40)]
    assert all(r is None for r in res)
    # zero-hit searches are ok tool results, not blindness
    mon = mr.HaltMonitor()
    res = [mon.observe({"empty_reason": "none", "tool_attempts": 2, "tool_ok_count": 2}, {}) for _ in range(40)]
    assert all(r is None for r in res)
    mon = mr.HaltMonitor()
    res = [mon.observe({"empty_reason": "none"}, {"tool_error_counts": {"Cannot read file": 1},
                                                  "successful_reads": 1}) for _ in range(3)]
    assert res[-1] is not None and res[-1][0] == "H4_INSTRUMENT_TOOL_ERRORS"
    mon = mr.HaltMonitor()
    res = [mon.observe({"empty_reason": "none"}, {"tool_error_counts": {"Not a file": 1},
                                                  "successful_reads": 1}) for _ in range(10)]
    assert all(r is None for r in res)  # agent misuse is behaviour, not instrument


def test_stop_file_halts_cleanly(tmp_path: Path) -> None:
    stop = tmp_path / "STOP"
    stop.write_text("x", encoding="utf-8")
    runner = _runner(tmp_path, _PerItemInner(GOOD_SCRIPT), n=2)
    object.__setattr__(runner._cfg, "stop_file", stop)  # frozen dataclass; test-only override
    outcome = runner.run()
    assert outcome.status == "OPERATOR_STOP" and outcome.completed == 0


# ---------------------------------------------------------------------------
# frozen inputs
# ---------------------------------------------------------------------------
def test_real_main297_manifest_and_tamper_detection(tmp_path: Path) -> None:
    path = PROJECT / "research" / "wp1b" / "wp1b_main_297_manifest.json"
    items = mr.load_main297_items(path)
    assert len(items) == 297 and items[0].index == 0
    assert not {i.task_id for i in items} & set(mr.CALIBRATION_TASK_IDS)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["task_ids"] = list(reversed(data["task_ids"]))
    bad = tmp_path / "m.json"
    bad.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(mr.ManifestError):
        mr.load_main297_items(bad)


def test_real_variance_items() -> None:
    main = mr.load_main297_items(PROJECT / "research" / "wp1b" / "wp1b_main_297_manifest.json")
    items = mr.load_variance_items(
        PROJECT / "artifacts" / "wp1b_variance_substudy_preregistration_2026-09-21.json",
        [i.task_id for i in main],
    )
    assert len(items) == 45 and len({i.key for i in items}) == 45
    assert [i.replicate for i in items[:15]] == [1] * 15 and items[-1].replicate == 3
    assert {i.task_id for i in items} <= {i.task_id for i in main[:50]}


def test_frozen_knobs_match_protocol_v3() -> None:
    report = mr.verify_frozen_knobs(PROJECT / "research" / "wp1b" / "wp1b_frozen_agent_protocol_v3.json")
    assert report["knobs"]["MAX_AGENT_CALLS"] == 8 and report["knobs"]["OBSERVATION_WINDOW_CHARS"] == 2000


def test_requirement_change_parity_with_calibration_runner() -> None:
    sys.path.insert(0, str(PROJECT))
    from scripts.wp1b_calibration_run import _build_requirement_change

    bundle = {"task_id": "t", "intent_text": "Do X", "parent_commit": "b" * 40, "records": []}
    ours = mr.build_requirement_change(mr.TaskBundle("t", "Do X", "b" * 40, ("a.py",)))
    assert ours == _build_requirement_change(bundle)


def test_dry_run_stub_selects_first_editable_path(tmp_path: Path) -> None:
    runner = _runner(tmp_path, mr.DryRunStubBackend(), n=2)
    outcome = runner.run()
    assert outcome.exit_code == mr.EXIT_OK
    records = _jsonl(tmp_path / "out" / mr.RECORDS_FILE)
    assert all(r["selected_paths"] == ["app/models.py"] and r["model_calls"] == 1 for r in records)


# ---------------------------------------------------------------------------
# label guard
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("rel", "forbidden"),
    [
        ("research/transparency/saleor_candidate_metadata.json", True),
        ("research/saleor-reserve-300-rmcss/saleor_reserve_300_proxies.json", True),
        ("research/saleor-reserve-300-rmcss/candidate_rows_saleor300.parquet", True),
        ("benchmark_data/real_commit_impact_saleor/scientific/saleor-rc-1/hidden/labels.json", True),
        ("benchmark_data/real_commit_impact_saleor/split_freeze_saleor.json", True),
        ("benchmark_data/real_commit_impact_saleor/scientific/saleor-rc-1/case_manifest.json", False),
        ("benchmark_data/real_commit_impact_saleor/scientific/saleor-rc-1/public/intent.json", False),
        ("benchmark_data/real_commit_impact_saleor/scientific/saleor-rc-1/public/candidate_universe.json", False),
        ("research/wp1b/wp1b_main_297_manifest.json", False),
        ("research/wp1b/wp1b_budget_model_v2.json", False),
        ("artifacts/wp1b_variance_substudy_preregistration_2026-09-21.json", False),
    ],
)
def test_label_guard_policy(rel: str, forbidden: bool) -> None:
    assert is_forbidden_relative(rel) is forbidden


def test_label_guard_blocks_open_in_subprocess(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    (proj / "research" / "saleor-reserve-300-rmcss").mkdir(parents=True)
    (proj / "research" / "saleor-reserve-300-rmcss" / "saleor_reserve_300_proxies.json").write_text("{}")
    (proj / "research" / "wp1b").mkdir(parents=True)
    (proj / "research" / "wp1b" / "ok.json").write_text("{}")
    src_dir = str(PROJECT / "src")
    code = (
        f"import sys; sys.path.insert(0, {src_dir!r})\n"
        "from pathlib import Path\n"
        "from benchmark.wp1b.label_guard import install_label_access_guard\n"
        f"p = Path({str(proj)!r})\n"
        "install_label_access_guard(p)\n"
        "open(p / 'research/wp1b/ok.json').read()\n"
        "try:\n"
        "    open(p / 'research/saleor-reserve-300-rmcss/saleor_reserve_300_proxies.json').read()\n"
        "    print('NOT_BLOCKED')\n"
        "except PermissionError as e:\n"
        "    print('BLOCKED', 'LABEL_ACCESS_VIOLATION' in str(e))\n"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60)
    assert out.stdout.strip() == "BLOCKED True", out.stderr


def test_cli_dry_run_chunked_with_fake_saleor(tmp_path: Path) -> None:
    """Drive scripts/wp1b_main_run.py main() in a subprocess with a fake bundle loader and
    materializer (no Saleor cache, no network): knob check, manifest check, chunking, resume."""
    out = tmp_path / "dry"
    driver = f"""
import sys, types
from pathlib import Path
sys.path.insert(0, {str(PROJECT)!r}); sys.path.insert(0, {str(PROJECT / 'src')!r})
sys.path.insert(0, {str(PROJECT / 'scripts')!r})
import wp1b_main_run as cli
from benchmark.wp1b import main_runner as mr
cli.SALEOR_CACHE = Path({str(tmp_path)!r})
mr.load_saleor_bundle = lambda sci, t: mr.TaskBundle(t, "intent " + t, "e" * 40, ("saleor/a.py", "saleor/b.py"))
fake = types.ModuleType("scripts.saleor_portability_fix")
def _mat(cache, parent, ws, roots=("saleor",)):
    (ws / "saleor").mkdir(parents=True, exist_ok=True)
    (ws / "saleor" / "a.py").write_text("a = 1\\n"); (ws / "saleor" / "b.py").write_text("b = 2\\n")
fake.materialize_production_parent = _mat
sys.modules["scripts.saleor_portability_fix"] = fake
code = cli.main(["--kind", "dry_run", "--out-dir", {str(out)!r}, "--resume", "--max-items", sys.argv[1]])
print("EXIT", code)
"""
    drv = tmp_path / "drv.py"
    drv.write_text(driver, encoding="utf-8")
    first = subprocess.run([sys.executable, str(drv), "150"], capture_output=True, text=True, timeout=600)
    assert "EXIT 0" in first.stdout, first.stdout + first.stderr
    progress = json.loads((out / mr.PROGRESS_FILE).read_text(encoding="utf-8"))
    assert progress["status"] == "CHUNK_DONE" and progress["completed"] == 150
    second = subprocess.run([sys.executable, str(drv), "200"], capture_output=True, text=True, timeout=600)
    assert "EXIT 0" in second.stdout, second.stdout + second.stderr
    progress = json.loads((out / mr.PROGRESS_FILE).read_text(encoding="utf-8"))
    assert progress["status"] == "COMPLETE" and progress["completed"] == 297
    assert (out / "knob_check.json").exists()
    state = json.loads((out / mr.STATE_FILE).read_text(encoding="utf-8"))
    assert state["kind"] == "dry_run" and state["n_items"] == 297 and len(state["resumes"]) == 1
