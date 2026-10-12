"""env-canon R4 shared interface — frozen contract (offline, ZERO API).

Mission ``M17_D7_R4_SHARED_INTERFACE_FREEZE`` freezes the minimal contract that
the four R4 tracks share so that they can work independently without inventing
incompatible APIs.  The authoritative specification is
``research/env-canon-r4/R4_SHARED_INTERFACE.md``; this module is the machine
encoding of that specification and MUST NOT be modified by any track.

Ownership rules (frozen):

* Track A and Track B may implement the ``LockParser`` Protocol *behind* this
  interface and bind it via :func:`bind_lock_parser`; they MUST NOT modify this
  module.
* Track C and Track D may consume the frozen data types and the
  :func:`parse_lock` / :func:`wheel_compatible` entry points; they MUST NOT
  modify this module.

Design rules encoded here (each is enforced by ``tests/contract``):

* The editable/virtual root project is represented explicitly via
  ``LockClosure.editable_self`` and is NEVER emitted as a third-party wheel
  requirement inside ``LockClosure.requirements``.
* ``SourceType`` distinguishes exactly REGISTRY / DIRECTORY / PATH /
  EDITABLE_SELF; any other semantic fails closed.
* Unknown semantics fail closed: a non-empty ``fail_closed_reasons`` marks the
  ``LockClosure`` invalid and unusable.
* No task-ID special cases: ordering, normalization and classification never
  depend on a task/unit identifier.
* Deterministic ordering and serialization: ``requirements`` and ``exclusions``
  are order-independent at construction time and serialize byte-for-byte
  identically for semantically equal closures.

This module intentionally ships NO lock-format parser.  Parsing (poetry / uv)
is track-owned implementation work that must satisfy ``LockParser`` and the
behavioural rules in the specification.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Protocol

SCHEMA_VERSION = "env-canon-r4/1.0"


class LockParseError(Exception):
    """Raised (fail closed) on structural contract violations or unbound interface."""


class SourceType(Enum):
    """Frozen R4 dependency source classification (exactly four members)."""

    REGISTRY = "REGISTRY"
    DIRECTORY = "DIRECTORY"
    PATH = "PATH"
    EDITABLE_SELF = "EDITABLE_SELF"

    @classmethod
    def from_token(cls, token: str | None) -> SourceType:
        """Classify a lock source token; unknown semantics fail closed.

        ``None`` means the lock carries no source table, i.e. an implicit
        registry package.  ``virtual`` is the ``uv`` editable root-project
        token; ``editable_self`` is the explicit PEP 660 form.  Any other token
        raises :class:`LockParseError` so callers never guess.
        """
        if token is None:
            return SourceType.REGISTRY
        compact = re.sub(r"[-_.\s+]+", "", token.strip().lower())
        if compact == "registry":
            return SourceType.REGISTRY
        if compact == "directory":
            return SourceType.DIRECTORY
        if compact == "path":
            return SourceType.PATH
        if compact in ("virtual", "editableself", "editable"):
            return SourceType.EDITABLE_SELF
        raise LockParseError(f"unknown source token {token!r} (fail closed)")


def normalize_name(name: str) -> str:
    """Deterministic PEP 503 distribution-name normalization.

    Always applies the identical generic rule; a task/unit identifier embedded
    in a name is normalized like any other run of separator characters (no
    task-ID special cases).
    """
    return re.sub(r"[-_.]+", "-", name.strip().lower())


@dataclass(frozen=True)
class RuntimeTarget:
    """Target Python runtime the closure is resolved for."""

    python_version: str
    implementation: str
    platform: str
    architecture: str

    def __post_init__(self) -> None:
        if not re.fullmatch(r"(?:0|[1-9]\d*)(?:\.(?:0|[1-9]\d*))*", self.python_version):
            raise LockParseError(f"malformed python_version {self.python_version!r} (fail closed)")


@dataclass(frozen=True)
class NormalizedRequirement:
    """One dependency in canonical form (``normalized_name`` is always PEP 503)."""

    normalized_name: str
    version: str
    source_type: SourceType
    source_reference: str | None
    marker: str | None
    marker_applies: bool
    editable_self: bool

    def __post_init__(self) -> None:
        if self.normalized_name != normalize_name(self.normalized_name):
            raise LockParseError(
                f"non-normalized name {self.normalized_name!r} (fail closed)"
            )


def _requirement_sort_key(req: NormalizedRequirement) -> tuple[Any, ...]:
    return (
        req.normalized_name,
        req.version,
        req.source_type.value,
        req.source_reference or "",
        req.marker or "",
        req.marker_applies,
    )


def _requirement_dict(req: NormalizedRequirement) -> dict[str, Any]:
    return {
        "normalized_name": req.normalized_name,
        "version": req.version,
        "source_type": req.source_type.value,
        "source_reference": req.source_reference,
        "marker": req.marker,
        "marker_applies": req.marker_applies,
        "editable_self": req.editable_self,
    }


@dataclass(frozen=True)
class LockClosure:
    """Frozen closure of one lock file for one ``target``.

    * ``requirements`` — applicable third-party wheel requirements, sorted
      deterministically; NEVER contains an editable-self entry.
    * ``editable_self`` — the explicit editable/virtual root project (or
      ``None`` when the lock records no root project).
    * ``exclusions`` — requirements excluded because they do not apply to the
      ``target`` (e.g. ``marker_applies`` is False); visible so nothing is
      silently skipped.
    * ``fail_closed_reasons`` — non-empty marks the closure INVALID: consumers
      MUST NOT use it (unknown lock semantics fail closed).
    """

    lock_format: str
    target: RuntimeTarget
    requirements: tuple[NormalizedRequirement, ...]
    editable_self: NormalizedRequirement | None
    exclusions: tuple[NormalizedRequirement, ...]
    fail_closed_reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.lock_format.strip():
            raise LockParseError("empty lock_format (fail closed)")
        for req in self.requirements:
            if req.editable_self:
                raise LockParseError(
                    "editable-self must be carried by the explicit editable_self field, "
                    "never emitted as a third-party wheel requirement"
                )
        object.__setattr__(self, "requirements", tuple(sorted(self.requirements, key=_requirement_sort_key)))
        object.__setattr__(self, "exclusions", tuple(sorted(self.exclusions, key=_requirement_sort_key)))

    @property
    def is_valid(self) -> bool:
        """A closure with any fail-closed reason must never be consumed."""
        return not self.fail_closed_reasons

    def to_canonical_dict(self) -> dict[str, Any]:
        """Deterministic, order-independent serialization (frozen layout)."""
        return {
            "lock_format": self.lock_format,
            "target": {
                "python_version": self.target.python_version,
                "implementation": self.target.implementation,
                "platform": self.target.platform,
                "architecture": self.target.architecture,
            },
            "requirements": [_requirement_dict(r) for r in self.requirements],
            "editable_self": _requirement_dict(self.editable_self) if self.editable_self else None,
            "exclusions": [_requirement_dict(r) for r in self.exclusions],
            "fail_closed_reasons": list(self.fail_closed_reasons),
        }

    def freeze_sha256(self) -> str:
        """Deterministic closure identity (``sort_keys=True`` for cross-track parity)."""
        payload = json.dumps(
            self.to_canonical_dict(), sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class LockParser(Protocol):
    """Implementation shape A/B tracks must satisfy to live behind the interface."""

    def parse_lock(
        self,
        lock_path: Path,
        target: RuntimeTarget,
        pyproject_path: Path | None = None,
    ) -> LockClosure:
        ...

    def wheel_compatible(self, wheel_filename: str, target: RuntimeTarget) -> bool:
        ...


_lock_parser: LockParser | None = None


def bind_lock_parser(parser: LockParser) -> None:
    """Bind a track implementation behind the frozen interface (A/B tracks only)."""
    global _lock_parser
    _lock_parser = parser


def unbind_lock_parser() -> None:
    """Remove the bound parser; the interface fails closed until rebound."""
    global _lock_parser
    _lock_parser = None


def parse_lock(
    lock_path: Path,
    target: RuntimeTarget,
    pyproject_path: Path | None = None,
) -> LockClosure:
    """Required interface: resolve a lock file into a frozen ``LockClosure``.

    Consumed by C/D tracks.  The bound A/B implementation performs the actual
    lock-format parsing.  With no parser bound the interface fails closed.
    """
    if _lock_parser is None:
        raise LockParseError(
            "no R4 lock parser bound; A/B tracks implement behind env_r4.contracts"
        )
    return _lock_parser.parse_lock(
        lock_path, target, pyproject_path=pyproject_path
    )


def wheel_compatible(wheel_filename: str, target: RuntimeTarget) -> bool:
    """Required interface: is ``wheel_filename`` compatible with ``target``?

    Consumed by C/D tracks.  See ``R4_SHARED_INTERFACE.md`` for the precise
    True/False contract an A/B implementation must satisfy.  No parser bound
    -> fail closed.
    """
    if _lock_parser is None:
        raise LockParseError(
            "no R4 lock parser bound; A/B tracks implement behind env_r4.contracts"
        )
    return _lock_parser.wheel_compatible(wheel_filename, target)
