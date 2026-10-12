"""R4-A era-aware wheel-tag compatibility (Track A, behind the frozen interface).

Mission: ``M17_D7_R4_A_ERA_AWARE_WHEEL_TAGS``.

This module implements the ``wheel_compatible`` entry point of the frozen R4
shared interface (``benchmark.wp2.env_r4.contracts``) for the Full-D7 historical
Python targets (CPython 3.8, 3.9, 3.12) on Linux x86_64.

It lives **behind** the frozen interface and never modifies it: consumers bind
it with :func:`bind` (which calls the frozen ``bind_lock_parser``), after which
``env_r4.wheel_compatible`` dispatches here.

Semantics
---------
Compatibility is evaluated entirely from the explicit :class:`RuntimeTarget`
(``python_version`` / ``implementation`` / ``platform`` / ``architecture``) and
the wheel filename, using standard wheel-tag tooling (``packaging.tags`` +
``packaging.utils``).  It never consults the running host interpreter:

* the target's supported PEP 425 tag set is built from ``cpython_tags`` +
  ``compatible_tags`` with an explicit python version, ABI and platform list;
* a wheel is compatible iff its own parsed tag set intersects that target set
  (pip's ``not file_tags.isdisjoint(supported_tags)`` rule).

Documented assumptions (the frozen ``RuntimeTarget`` carries no glibc field):

* implementation — only ``cpython``;
* platform — only ``linux``;
* architecture — only ``x86_64``;
* Python eras — only the Full-D7 targets ``3.8`` / ``3.9`` / ``3.12``;
* linux platform family — manylinux tags with a glibc ceiling of ``(2, 36)``
  (Debian bookworm) descending to the PEP 600 oldest glibc ``(2, 4)``, plus the
  legacy ``manylinux2014`` / ``manylinux2010`` / ``manylinux1`` aliases and
  ``linux_x86_64``.  This mirrors the frozen R3 ``d7_r3_wheeltags`` py312 target
  enumeration exactly and is reused uniformly for every supported era.

Any unknown implementation / platform / architecture / era, any malformed
``python_version`` and any malformed wheel filename FAIL CLOSED (``False``).

``parse_lock`` keeps the frozen ``LockParser`` parameter names even though they
are unused by the fail-closed stub, so ARG002 is disabled for this module.
"""
# ruff: noqa: ARG002
from __future__ import annotations

import functools
import re
from pathlib import Path

from packaging.tags import Tag, compatible_tags, cpython_tags
from packaging.utils import parse_wheel_filename

from benchmark.wp2.env_r4.contracts import (
    LockClosure,
    LockParseError,
    RuntimeTarget,
    bind_lock_parser,
)

SUPPORTED_PYTHON_VERSIONS: frozenset[tuple[int, int]] = frozenset({(3, 8), (3, 9), (3, 12)})
SUPPORTED_IMPLEMENTATIONS: frozenset[str] = frozenset({"cpython"})
SUPPORTED_PLATFORMS: frozenset[str] = frozenset({"linux"})
SUPPORTED_LINUX_ARCHITECTURES: frozenset[str] = frozenset({"x86_64"})

PLATFORM_GLIBC_MAX: tuple[int, int] = (2, 36)
_GLIBC_OLDEST_MINOR = 4
_LEGACY_MANYLINUX: dict[tuple[int, int], str] = {
    (2, 17): "manylinux2014",
    (2, 12): "manylinux2010",
    (2, 5): "manylinux1",
}
_PYTHON_VERSION_RE = re.compile(r"(\d+)\.(\d+)")


def linux_platform_tags(arch: str) -> tuple[str, ...]:
    """Deterministic linux/manylinux platform tag family for ``arch``.

    Mirrors the frozen R3 py312 target enumeration: manylinux tags descending
    from ``PLATFORM_GLIBC_MAX`` to the PEP 600 oldest glibc, the legacy aliases
    and ``linux_<arch>``.  Never consults the running host.
    """
    out: list[str] = []
    for minor in range(PLATFORM_GLIBC_MAX[1], _GLIBC_OLDEST_MINOR, -1):
        glibc = (PLATFORM_GLIBC_MAX[0], minor)
        out.append(f"manylinux_{glibc[0]}_{glibc[1]}_{arch}")
        legacy = _LEGACY_MANYLINUX.get(glibc)
        if legacy is not None and f"{legacy}_{arch}" not in out:
            out.append(f"{legacy}_{arch}")
    out.append(f"linux_{arch}")
    return tuple(out)


@functools.lru_cache(maxsize=32)
def _target_supported_tags(python_version: tuple[int, int]) -> frozenset[Tag]:
    """Frozen target's supported PEP 425 tag set, built from explicit params."""
    platforms = linux_platform_tags("x86_64")
    interpreter = f"cp{python_version[0]}{python_version[1]}"
    tags: set[Tag] = set()
    tags.update(
        cpython_tags(python_version=python_version, abis=[interpreter], platforms=platforms)
    )
    tags.update(
        compatible_tags(python_version=python_version, interpreter=interpreter, platforms=platforms)
    )
    return frozenset(tags)


def _parse_python_version(python_version: str) -> tuple[int, int] | None:
    match = _PYTHON_VERSION_RE.fullmatch(python_version.strip())
    if match is None:
        return None
    return (int(match.group(1)), int(match.group(2)))


def wheel_compatible(wheel_filename: str, target: RuntimeTarget) -> bool:
    """Is ``wheel_filename`` installable on ``target`` (era-aware, host-free)?

    Fails closed (``False``) on unknown target semantics and on any wheel
    filename that does not parse under the PEP 427 wheel tag grammar.
    """
    if target.implementation not in SUPPORTED_IMPLEMENTATIONS:
        return False
    if target.platform not in SUPPORTED_PLATFORMS:
        return False
    if target.architecture not in SUPPORTED_LINUX_ARCHITECTURES:
        return False
    python_version = _parse_python_version(target.python_version)
    if python_version is None or python_version not in SUPPORTED_PYTHON_VERSIONS:
        return False
    try:
        _name, _version, _build, wheel_tags = parse_wheel_filename(wheel_filename)
    except Exception:
        return False
    return bool(wheel_tags & _target_supported_tags(python_version))


class WheelTagParser:
    """R4-A Track A implementation of the frozen ``LockParser`` shape.

    ``wheel_compatible`` is the era-aware engine.  ``parse_lock`` is out of
    scope for this mission (lock-format parsing is Track A/B lock work) and
    fails closed with :class:`LockParseError`.
    """

    def parse_lock(
        self,
        lock_path: Path,
        target: RuntimeTarget,
        pyproject_path: Path | None = None,
    ) -> LockClosure:
        raise LockParseError(
            "lock parsing is out of scope for R4-A wheel tags (fail closed)"
        )

    def wheel_compatible(self, wheel_filename: str, target: RuntimeTarget) -> bool:
        return wheel_compatible(wheel_filename, target)


def bind() -> None:
    """Bind the R4-A implementation behind the frozen R4 interface."""
    bind_lock_parser(WheelTagParser())
