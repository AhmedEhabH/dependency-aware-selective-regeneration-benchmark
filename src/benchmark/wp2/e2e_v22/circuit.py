"""Persistent provider circuit breaker (brain-authored kit).

A provider outage never advances the scientific episode counter. The driver keeps
retrying the SAME pending episode after a cooldown, and stops the run (resumable)
when the outage lasts too long.

Policy: cooldown COOLDOWN_S between half-open retries; STOP when MAX_COOLDOWNS
cooldowns were used or the outage lasted MAX_OUTAGE_S. A new process that finds an
OPEN circuit whose last event is older than COOLDOWN_S starts a fresh outage window.
"""
from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

COOLDOWN_S = 900.0
MAX_COOLDOWNS = 3
MAX_OUTAGE_S = 3600.0


@dataclass
class Decision:
    action: str  # "COOLDOWN" | "STOP"
    seconds: float = 0.0
    reason: str = ""


class CircuitBreaker:
    def __init__(self, path: Path, wall: Callable[[], float] = time.time,
                 cooldown_s: float = COOLDOWN_S, max_cooldowns: int = MAX_COOLDOWNS,
                 max_outage_s: float = MAX_OUTAGE_S) -> None:
        self.path = Path(path)
        self._wall = wall
        self.cooldown_s = cooldown_s
        self.max_cooldowns = max_cooldowns
        self.max_outage_s = max_outage_s
        self.state = self._load()

    def _load(self) -> dict[str, Any]:
        if self.path.exists():
            return json.loads(self.path.read_text(encoding="utf-8"))
        return {"state": "CLOSED", "outage_started": None, "cooldowns_used": 0,
                "last_event": None, "events": []}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, indent=1, sort_keys=True), encoding="utf-8")
        os.replace(tmp, self.path)

    def _event(self, kind: str, detail: str = "") -> None:
        now = self._wall()
        self.state["last_event"] = now
        self.state["events"].append({"t": now, "event": kind, "detail": detail[:300]})
        self.state["events"] = self.state["events"][-200:]

    def on_start(self) -> None:
        if self.state["state"] == "OPEN":
            last = self.state.get("last_event") or 0.0
            if self._wall() - last >= self.cooldown_s:
                self.state.update({"state": "CLOSED", "outage_started": None,
                                   "cooldowns_used": 0})
                self._event("RESET_ON_RESTART")
                self._save()

    def on_success(self) -> None:
        if self.state["state"] != "CLOSED":
            self.state.update({"state": "CLOSED", "outage_started": None, "cooldowns_used": 0})
            self._event("CLOSED_AFTER_SUCCESS")
            self._save()

    def on_unavailable(self, detail: str) -> Decision:
        now = self._wall()
        if self.state["state"] == "CLOSED":
            self.state.update({"state": "OPEN", "outage_started": now, "cooldowns_used": 0})
            self._event("OPEN", detail)
        started = self.state["outage_started"] or now
        elapsed = now - started
        if self.state["cooldowns_used"] >= self.max_cooldowns or elapsed >= self.max_outage_s:
            self._event("STOP", f"cooldowns={self.state['cooldowns_used']} elapsed={elapsed:.0f}s")
            self._save()
            return Decision("STOP", 0.0, f"outage {elapsed:.0f}s, "
                                          f"{self.state['cooldowns_used']} cooldowns used")
        self.state["cooldowns_used"] += 1
        self._event("COOLDOWN", detail)
        self._save()
        return Decision("COOLDOWN", self.cooldown_s,
                        f"cooldown {self.state['cooldowns_used']}/{self.max_cooldowns}")
