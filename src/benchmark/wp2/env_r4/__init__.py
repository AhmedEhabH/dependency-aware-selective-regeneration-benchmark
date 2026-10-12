"""R4 shared environment interface (frozen contract, offline, ZERO API).

Frozen by ``M17_D7_R4_SHARED_INTERFACE_FREEZE``.  Authoritative specification:
``research/env-canon-r4/R4_SHARED_INTERFACE.md``.

Ownership: Track A / Track B implement behind this interface; Track C /
Track D consume it.  No track may modify this package.
"""
from benchmark.wp2.env_r4.contracts import (
    SCHEMA_VERSION,
    LockClosure,
    LockParseError,
    LockParser,
    NormalizedRequirement,
    RuntimeTarget,
    SourceType,
    bind_lock_parser,
    normalize_name,
    parse_lock,
    unbind_lock_parser,
    wheel_compatible,
)

__all__ = [
    "SCHEMA_VERSION",
    "LockClosure",
    "LockParseError",
    "LockParser",
    "NormalizedRequirement",
    "RuntimeTarget",
    "SourceType",
    "bind_lock_parser",
    "normalize_name",
    "parse_lock",
    "unbind_lock_parser",
    "wheel_compatible",
]
