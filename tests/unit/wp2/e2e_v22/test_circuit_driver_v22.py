"""v2.2 circuit breaker + generation driver: provider outages never become outcomes."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from benchmark.wp2.e2e_v22 import common
from benchmark.wp2.e2e_v22.circuit import CircuitBreaker
from benchmark.wp2.e2e_v22.transport import HoldActiveV22, ProviderUnavailable, RequestRejected

PROJECT = Path(__file__).resolve().parents[4]


def load_driver():
    spec = importlib.util.spec_from_file_location("drv", PROJECT / "scripts" / "wp2_e2e_v22_generate.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Wall:
    def __init__(self) -> None:
        self.t = 1000.0

    def __call__(self) -> float:
        return self.t


# ------------------------------------------------------------------ circuit
def test_circuit_three_cooldowns_then_stop(tmp_path):
    w = Wall()
    cb = CircuitBreaker(tmp_path / "c.json", wall=w)
    for _ in range(3):
        d = cb.on_unavailable("429")
        assert d.action == "COOLDOWN" and d.seconds == 900
        w.t += 900
    assert cb.on_unavailable("429").action == "STOP"


def test_circuit_stops_on_elapsed(tmp_path):
    w = Wall()
    cb = CircuitBreaker(tmp_path / "c.json", wall=w)
    assert cb.on_unavailable("x").action == "COOLDOWN"
    w.t += 3600
    assert cb.on_unavailable("x").action == "STOP"


def test_circuit_success_resets_and_persists(tmp_path):
    w = Wall()
    cb = CircuitBreaker(tmp_path / "c.json", wall=w)
    cb.on_unavailable("x")
    cb.on_success()
    cb2 = CircuitBreaker(tmp_path / "c.json", wall=w)
    assert cb2.state["state"] == "CLOSED" and cb2.state["cooldowns_used"] == 0


def test_circuit_reset_on_restart_after_cooldown(tmp_path):
    w = Wall()
    cb = CircuitBreaker(tmp_path / "c.json", wall=w)
    for _ in range(4):
        cb.on_unavailable("x")
    w.t += 1000
    cb2 = CircuitBreaker(tmp_path / "c.json", wall=w)
    cb2.on_start()
    assert cb2.on_unavailable("x").action == "COOLDOWN"


# ------------------------------------------------------------------ driver
class FakeClient:
    def __init__(self, hold: Path) -> None:
        self.hold = hold
        self.ctx = {}

    def set_context(self, **kw):
        self.ctx = kw

    def check_hold(self):
        if self.hold.exists():
            raise HoldActiveV22("hold")


class FakeLedger:
    def __init__(self, total: float = 0.0, ceiling: float = 2.0) -> None:
        self._t, self._c = total, ceiling

    def can_spend(self, w):
        return self._t + w <= self._c

    def total(self):
        return self._t


class EpisodeFn:
    """Scripted episode function: per (task,label) a list of outcomes (status str or exception)."""

    def __init__(self, script: dict | None = None, default: str = "APPLIED") -> None:
        self.script = script or {}
        self.default = default
        self.calls: list[tuple[str, str]] = []

    def __call__(self, task_id, arm, client, ledger, cache, root, subdir="episodes", label=None):
        lab = label or arm
        self.calls.append((task_id, lab))
        seq = self.script.get((task_id, lab))
        outcome = seq.pop(0) if seq else self.default
        if isinstance(outcome, Exception):
            raise outcome
        p = common.episode_path(root, subdir, task_id, lab)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"task_id": task_id, "arm": arm, "status": outcome}))
        return {"status": outcome}


def run_drive(drv, tmp, fn, mode="main", max_new=8, ledger=None, wall=None, stop=None):
    wall = wall or Wall()
    sleeps: list[float] = []

    def sleep(s):
        sleeps.append(s)
        wall.t += s
    code, info = drv.drive(mode, tmp, FakeClient(tmp / "HOLD"), ledger or FakeLedger(),
                           CircuitBreaker(tmp / "transport" / "circuit.json", wall=wall),
                           fn, lambda lab: None, max_new, 1e9, clock=lambda: 0.0, sleep=sleep,
                           stop_path=stop or tmp / "STOP.flag")
    return code, info, sleeps


def test_driver_chunk_and_order(tmp_path):
    drv = load_driver()
    fn = EpisodeFn()
    code, info, _ = run_drive(drv, tmp_path, fn)
    assert code == 0 and info["new_terminal"] == 8
    assert fn.calls == [(t, a) for t, a, _l in common.planned_main()[:8]]
    code, info, _ = run_drive(drv, tmp_path, fn, max_new=100)
    assert info["terminal"] == 56


def test_outage_retries_same_episode_without_record(tmp_path):
    drv = load_driver()
    first = common.planned_main()[0]
    fn = EpisodeFn({(first[0], first[2]): [ProviderUnavailable("429", []),
                                          ProviderUnavailable("429", []), "APPLIED"]})
    code, info, sleeps = run_drive(drv, tmp_path, fn, max_new=1)
    assert code == 0 and info["new_terminal"] == 1
    assert fn.calls == [(first[0], first[2])] * 3
    assert sum(sleeps) == pytest.approx(1800)


def test_persistent_outage_stops_75_and_writes_nothing(tmp_path):
    drv = load_driver()
    first = common.planned_main()[0]
    fn = EpisodeFn({(first[0], first[2]): [ProviderUnavailable("429", [])] * 10})
    code, info, _ = run_drive(drv, tmp_path, fn)
    assert code == 75 and info["new_terminal"] == 0
    assert not common.episode_path(tmp_path, "episodes", first[0], first[2]).exists()
    assert (tmp_path / "transport" / "pending.json").exists()
    assert len(fn.calls) == 4  # initial + 3 half-open retries, never a 5th cycle


def test_existing_generation_fail_is_invariant_violation(tmp_path):
    drv = load_driver()
    t, _a, lab = common.planned_main()[5]
    p = common.episode_path(tmp_path, "episodes", t, lab)
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"status": "GENERATION_FAIL"}))
    fn = EpisodeFn()
    code, _info, _ = run_drive(drv, tmp_path, fn)
    assert code == 78 and fn.calls == []


@pytest.mark.parametrize("exc,expected", [(RequestRejected("402"), 76),
                                          (HoldActiveV22("h"), 3),
                                          (RuntimeError("docker"), 78)])
def test_exception_exit_codes(tmp_path, exc, expected):
    drv = load_driver()
    first = common.planned_main()[0]
    code, _info, _ = run_drive(drv, tmp_path, EpisodeFn({(first[0], first[2]): [exc]}))
    assert code == expected
    assert not common.episode_path(tmp_path, "episodes", first[0], first[2]).exists()


def test_non_terminal_status_is_invariant(tmp_path):
    drv = load_driver()
    code, _info, _ = run_drive(drv, tmp_path, EpisodeFn(default="GENERATION_FAIL"))
    assert code == 78


def test_budget_and_stop_flag(tmp_path):
    drv = load_driver()
    code, _i, _ = run_drive(drv, tmp_path, EpisodeFn(), ledger=FakeLedger(total=1.99))
    assert code == 77
    (tmp_path / "STOP.flag").write_text("x")
    code, _i, _ = run_drive(drv, tmp_path, EpisodeFn())
    assert code == 4


def test_variance_plan_and_paths(tmp_path):
    drv = load_driver()
    fn = EpisodeFn()
    code, info, _ = run_drive(drv, tmp_path, fn, mode="variance", max_new=6)
    assert code == 0 and info["terminal"] == 6
    assert (tmp_path / "variance" / "saleor-rc-2d45b76a52f2" / "var_r1" / "episode.json").exists()
