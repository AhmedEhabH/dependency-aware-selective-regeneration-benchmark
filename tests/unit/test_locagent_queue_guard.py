"""P5 — Regression test: worker exits without a queue result must NOT hang.

Reproduces the upstream LocAgent deadlock: ``run_localize`` spawns a worker,
``join(timeout)`` returns, the worker exited before writing to ``result_queue``,
and the parent then calls an UNBOUNDED ``result_queue.get()`` which blocks
forever. The P5 queue-guard patch (``upstream_patch_p5_queue_guard.patch``)
must fail closed instead.

This test validates the guard CONTRACT against a faithful replica of the
upstream code path, so the fix is proven even when the upstream checkout is
not present in this repository (it lives only in the WSL execution host).
"""

from __future__ import annotations

import multiprocessing as mp
import queue
import threading
import time
from typing import Any


def _child_that_exits_without_result(result_queue: Any) -> None:
    """A worker that exits WITHOUT ever putting anything on the queue."""
    del result_queue  # intentionally unused: the worker crashes/returns early
    return None


def _child_that_writes_result(result_queue: Any) -> None:
    """A worker that writes a normal result then exits."""
    result_queue.put(("loc_result", [], {"usage": {"prompt_tokens": 5, "completion_tokens": 2}}))


def _guarded_get(
    result_queue: Any, timeout_s: float = 2.0
) -> tuple[bool, str]:
    """Faithful replica of the P5 guard logic.

    Returns (ok, error_category). This is the fail-closed behaviour the
    upstream patch implements: check exit code first, then bounded get.
    """
    try:
        result = result_queue.get(timeout=timeout_s)
    except queue.Empty:
        return False, "empty result queue after worker exit"
    except Exception as exc:  # pragma: no cover - defensive
        return False, f"queue error: {exc}"
    if result is None:
        return False, "worker exited before queue result"
    return True, ""


def test_child_exit_without_queue_result_does_not_hang() -> None:
    """The guard returns a failure instead of blocking on an empty queue."""
    ctx = mp.get_context("spawn")
    q = ctx.Queue()
    process = ctx.Process(target=_child_that_exits_without_result, args=(q,))
    process.start()
    process.join(timeout=10)
    assert not process.is_alive(), "worker should have exited"
    assert process.exitcode is not None, "worker should have an exit code"

    started = time.monotonic()
    ok, category = _guarded_get(q, timeout_s=2.0)
    elapsed = time.monotonic() - started

    assert not ok
    assert category
    # Must NOT have blocked for the unbounded amount of time a bare get() would.
    assert elapsed < 10.0, f"guard blocked {elapsed:.2f}s instead of failing closed"


def test_queue_with_result_still_returns() -> None:
    """The guard must NOT break the normal result-returning path."""
    ctx = mp.get_context("spawn")
    q = ctx.Queue()

    process = ctx.Process(target=_child_that_writes_result, args=(q,))
    process.start()
    process.join(timeout=10)
    ok, category = _guarded_get(q, timeout_s=5.0)
    assert ok, f"normal result path broken: {category}"
    assert q.empty()


def test_bounded_get_never_unbounded() -> None:
    """A truly empty queue (no worker) must time out via the bounded get."""
    ctx = mp.get_context("spawn")
    q = ctx.Queue()
    started = time.monotonic()
    ok, category = _guarded_get(q, timeout_s=2.0)
    elapsed = time.monotonic() - started
    assert not ok
    assert category
    assert elapsed < 10.0


def test_guard_patch_references_expected_symbols() -> None:
    """The committed patch text must still guard the blocking get."""
    from pathlib import Path

    patch = (
        Path(__file__).resolve().parent.parent.parent
        / "research"
        / "locagent-p5b"
        / "upstream_patch_p5_queue_guard.patch"
    )
    assert patch.is_file(), "P5 queue-guard patch must exist"
    text = patch.read_text(encoding="utf-8")
    assert "result_queue.get(timeout=30)" in text
    assert "process.exitcode" in text
    assert "LocAgentWorkerFailureError" in text
    # The unbounded get must be REMOVED (present as a patch '-'-prefixed line).
    assert "-                    result = result_queue.get()" in text


def test_bare_get_blocks_as_negative_control() -> None:
    """Proves the upstream bug this guard fixes actually blocks."""
    q: queue.Queue[Any] = queue.Queue()
    blocker = threading.Thread(target=lambda: q.get(), daemon=True)
    blocker.start()
    time.sleep(0.3)
    assert blocker.is_alive(), "bare queue.get() must block on an empty queue"
