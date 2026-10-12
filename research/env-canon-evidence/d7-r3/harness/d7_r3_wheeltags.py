#!/usr/bin/env python3
"""D7_R3 standards-based wheel tag compatibility (FROZEN with the R3 harness).

Mission: M17_ENV_CANON_D7_R3_HARNESS_DEFECT_CORRECTION_AND_FREEZE
(ENGINEERING QUALIFICATION / HARNESS DEFECT CORRECTION ONLY)

This module is byte-identical in behavior to the frozen R2 wheeltags module
(identity/header renamed only).  Target: CPython 3.12, Linux x86_64, Debian
bookworm (glibc 2.36).

This module is the *authoritative* artifact-resolution gate for the D7 runtime
wheel-only install path.  It replaces the ad-hoc filename heuristic of the R1
harness with the same PEP 425/427 tag-acceptance algorithm pip uses
(``packaging.utils.parse_wheel_filename`` + set intersection against the
target's supported-tag set), with the following corrections applied:

  * stable-ABI wheels (``cp37/38/39...-abi3-manylinux...``) ARE accepted for the
    CPython 3.12 target (PEP 384 stable ABI forward compatibility), exactly as
    the observed wheels ``bcrypt-4.2.1-cp37-abi3-manylinux...``,
    ``cryptography-43.0.3-cp37-abi3-manylinux...``,
    ``deptry-0.21.2-cp39-abi3-...``, ``protobuf-5.29.2-cp38-abi3-...`` require.
  * ``py3-none-*`` / ``py2.py3-none-*`` universal wheels are accepted.
  * platform-incompatible wheels (``*-win_amd64``, ``*-macosx*``,
    ``linux_aarch64``), non-abi3 wrong-version CPython wheels
    (``cp311-cp311-manylinux...`` for target 3.12) and future-CPython-only
    wheels (``cp313-cp313...``) are REJECTED.

The target tag set is computed deterministically from the frozen target
parameters (NOT from the Windows host ``sys_tags``): we enumerate the
manylinux platform tags that Debian bookworm (glibc 2.36, x86_64) is
compatible with, then build the supported-tag set with pip's vendored
algorithm (``cpython_tags`` + ``compatible_tags``).

Rules it encodes (asserted by the synthetic P2P/F2P suite):
  NOT package-specific, NOT outcome-tuned: purely host/platform semantics.
"""
from __future__ import annotations

import functools

from packaging.tags import Tag, cpython_tags, compatible_tags
from packaging.utils import parse_wheel_filename

# ---------------------------------------------------------------------------
# Frozen target parameters
# ---------------------------------------------------------------------------
TARGET_PYVER = (3, 12)
TARGET_INTERPRETER = "cp312"
TARGET_CPYTHON_ABIS = ("cp312",)  # CPython 3.12 (non-debug, non-free-threaded)
TARGET_ARCH = "x86_64"
# Debian bookworm glibc; oldest manylinux glibc for x86_64 is (2, 4) per PEP 600.
TARGET_GLIBC_MAX = (2, 36)
_LEGACY_MANYLINUX = {  # mapping by allowed glibc (same table pip uses)
    (2, 17): "manylinux2014",
    (2, 12): "manylinux2010",
    (2, 5): "manylinux1",
}


def target_manylinux_platforms(
    arch: str = TARGET_ARCH,
    glibc_current: tuple[int, int] = TARGET_GLIBC_MAX,
    oldest: tuple[int, int] = (2, 4),
) -> list[str]:
    """Deterministically enumerate the manylinux/linux platform tags the
    frozen Linux target accepts (glibc <= target, x86_64).  Independent of the
    Windows host; mirrors pip's ``_manylinux.platform_tags`` for this target
    (descends every glibc version from the target down to ``oldest``, and adds
    the PEP 600 legacy manylinux tags).
    """
    out: list[str] = []
    glibc_major = glibc_current[0]
    # All glibc versions descending from the current max to the newest version
    # of the oldest allowed major, emitted as manylinux_<major>_<minor>_<arch>.
    # For the frozen target this is 2.36 down to 2.4 (x86_64 oldest = (2,4)).
    for minor in range(glibc_current[1], oldest[1], -1):
        g = (glibc_major, minor)
        tag = f"manylinux_{g[0]}_{g[1]}_{arch}"
        out.append(tag)
        legacy = _LEGACY_MANYLINUX.get(g)
        if legacy and f"{legacy}_{arch}" not in out:
            out.append(f"{legacy}_{arch}")
    out.append(f"linux_{arch}")
    return out


@functools.lru_cache(maxsize=1)
def target_supported_tags() -> frozenset[Tag]:
    """The supported PEP 425 tag set for the frozen target (computed from the
    frozen target params, never from the running host)."""
    platforms = target_manylinux_platforms()
    tags: set[Tag] = set()
    tags |= set(cpython_tags(python_version=TARGET_PYVER, abis=list(TARGET_CPYTHON_ABIS), platforms=platforms))
    tags |= set(compatible_tags(python_version=TARGET_PYVER, interpreter=TARGET_INTERPRETER, platforms=platforms))
    return frozenset(tags)


@functools.lru_cache(maxsize=1)
def supported_tag_strs() -> frozenset[str]:
    return frozenset(str(t) for t in target_supported_tags())


def parse_wheel(filename: str) -> tuple[str, str, frozenset[Tag]] | None:
    """Return (canonical name, version, tags) or None for unparseable names."""
    try:
        name, version, _build, tags = parse_wheel_filename(filename)
    except Exception:
        return None
    return str(name), str(version), frozenset(tags)


def wheel_compatible(filename: str) -> bool:
    """True iff the wheel (by filename) is installable on the frozen target.

    Same acceptance rule pip uses: strip the wheel's own file tags and test
    whether any of them intersects the target's supported-tag set (PEP 425
    ``not file_tags.isdisjoint(supported_tags)``).
    """
    parsed = parse_wheel(filename)
    if parsed is None:
        return False
    _name, _version, tags = parsed
    return bool(tags & target_supported_tags())


def wheel_tags_str(filename: str) -> list[str]:
    """Human-readable parsed tag strings for a wheel filename (diagnostics)."""
    parsed = parse_wheel(filename)
    if parsed is None:
        return []
    return sorted(str(t) for t in parsed[2])


if __name__ == "__main__":  # pragma: no cover
    import sys

    for fn in sys.argv[1:]:
        print(("OK " if wheel_compatible(fn) else "NO "), fn)
        for ts in wheel_tags_str(fn):
            print("      tag:", ts)