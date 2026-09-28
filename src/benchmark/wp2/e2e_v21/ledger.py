"""Mission-12B v2.1 - spend ledger (T2/T3).

v2.1 ledger: persistent JSONL under the v21 root only. Every ``record`` call
fsyncs the file so that a process crash right after a provider call never loses
the spend entry. Ceilings are per-stage; the scientific ceiling is $2.00 total
(probe + generation + variance).
"""
from __future__ import annotations

import json
import os
from pathlib import Path


class LedgerV21:
    def __init__(self, path: Path, ceilings: dict[str, float]) -> None:
        self._path = path
        self._ceilings = ceilings
        self._totals: dict[str, float] = {}
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            return
        for line in self._path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            stage = entry.get("stage", "SMOKE")
            self._totals[stage] = self._totals.get(stage, 0.0) + float(entry.get("cost_usd", 0.0))

    def totals(self) -> dict[str, float]:
        return dict(self._totals)

    def total(self) -> float:
        return sum(self._totals.values())

    def can_spend(self, worst_case_usd: float) -> bool:
        return all(self._totals.get(stage, 0.0) + worst_case_usd <= ceil
                   for stage, ceil in self._ceilings.items())

    def record(self, call: dict) -> None:
        stage = call.get("stage", "SMOKE")
        self._totals[stage] = self._totals.get(stage, 0.0) + float(call.get("cost_usd", 0.0))
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(call, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
