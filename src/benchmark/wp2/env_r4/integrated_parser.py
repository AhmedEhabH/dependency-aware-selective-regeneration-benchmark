"""R4 I1 A+B composition — one composite ``LockParser`` behind the frozen interface.

Mission ``M17_D7_R4_I1_AB_COMPOSITION``.

The frozen shared interface (``benchmark.wp2.env_r4.contracts``) exposes exactly
one ``LockParser`` binding slot consumed by ``parse_lock`` and
``wheel_compatible``.  R4-A and R4-B each implement only one half of that
interface and fail closed on the other, so sequential binding cannot provide
both entry points.  This module is the smallest composition layer that binds a
single composite object:

* ``parse_lock``  -> R4-B ``EnvR4LockAdapter`` semantics (Poetry + uv).
* ``wheel_compatible`` -> R4-A era-aware wheel-tag engine.

Both qualified components are delegated to verbatim; no algorithm is duplicated
and no frozen file is modified.  The frozen ``LockParser`` Protocol is satisfied
structurally by :class:`IntegratedR4Parser`.
"""
from __future__ import annotations

from pathlib import Path

from benchmark.wp2.env_r4.contracts import (
    LockClosure,
    RuntimeTarget,
    bind_lock_parser,
)
from benchmark.wp2.env_r4.uv_adapter import EnvR4LockAdapter
from benchmark.wp2.env_r4.wheel_tags import wheel_compatible


class IntegratedR4Parser:
    """Composite ``LockParser``: R4-B ``parse_lock`` + R4-A ``wheel_compatible``."""

    def __init__(self) -> None:
        self._lock_adapter = EnvR4LockAdapter()

    def parse_lock(
        self,
        lock_path: Path,
        target: RuntimeTarget,
        pyproject_path: Path | None = None,
    ) -> LockClosure:
        """R4-B lock parsing (Poetry / uv closure normalization), delegated."""
        return self._lock_adapter.parse_lock(
            lock_path, target, pyproject_path=pyproject_path
        )

    def wheel_compatible(self, wheel_filename: str, target: RuntimeTarget) -> bool:
        """R4-A era-aware wheel-tag verdict, delegated to the qualified engine."""
        return wheel_compatible(wheel_filename, target)


def bind_integrated_parser() -> None:
    """Bind exactly one composite ``LockParser`` behind the frozen interface."""
    bind_lock_parser(IntegratedR4Parser())
