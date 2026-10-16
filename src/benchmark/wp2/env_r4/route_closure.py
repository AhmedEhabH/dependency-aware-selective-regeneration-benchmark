"""D7 install-route behavioral closure projection (successor).

Mission ``M17_D7_R4_POETRY_CLOSURE_SUCCESSOR_QUALIFICATION``.

Ownership boundary (per the frozen authorities, ``AUTHORITY.md``):

* The layer that owns D7 install-route semantics is the runner's
  ``runtime_pins()`` (``scripts/r4_behavioral_calibration_n12_r2.py``), reused
  unchanged by the Full144 driver.  This module is that layer's closure
  projection.
* The generic R4-B parser (``benchmark.wp2.env_r4.uv_adapter``) MUST remain
  marker-aware for its other consumers (UV_EXPORT, source-fidelity, census).
  It is therefore NOT modified; only this route-aware projection layer
  changes.
* For ``LOCK_FRAGMENT_MAIN_PLUS_DEV`` poetry locks, the frozen R3 behavioral
  authority (``d7_r3_closure.py``) requires the COMPLETE main+dev dependency
  closure.  The qualified frozen R3 closure implementation (``poetry_pins`` /
  ``derive_runtime_closure``) is reused verbatim -- no second independent
  poetry parser is created.

General successor rule (no task/unit/commit/package-name literals in logic):

* ``LOCK_FRAGMENT_MAIN_PLUS_DEV`` poetry -> the frozen R3 complete main+dev
  closure, from which the caller-supplied frozen R3 platform exclusions
  (pywin32 marker-excluded-on-linux; python-magic-bin platform=win32 from the
  frozen pyproject) are removed.  The exclusion name sets are supplied by the
  runner from the frozen authorities, never hard-coded here.
* Every other frozen route (``UV_EXPORT``, ``REQ_MAIN_PLUS_LOCK_DEV``,
  ``V2_EDITABLE_PLUS_LOCK_DEV``) keeps its existing closure projection.
* Unknown install routes fail closed.
"""
from __future__ import annotations

import re
import sys
import tomllib
from collections.abc import Mapping
from collections.abc import Set as AbstractSet
from pathlib import Path

from benchmark.wp2.env_r4.contracts import normalize_name

# Frozen R3 harness directory (qualified frozen closure implementation).
_HARNESS_DIR = Path(r"D:\wp2_env_store\harness\d7_r3")

# Frozen install route whose authority requires the complete main+dev closure.
_LOCK_FRAGMENT_MAIN_PLUS_DEV = "LOCK_FRAGMENT_MAIN_PLUS_DEV"


class RouteClosureError(Exception):
    """Fail-closed: an install route has no frozen behavioural closure rule."""


class DeclaredPinRuleError(RouteClosureError):
    """Fail-closed: a declared-but-unlocked pin rule cannot be applied safely.

    Raised when the historical dependency authorities are malformed, when
    conflicting exact pins exist, or when a canonical package-name match is
    ambiguous.  Injection is declined in every case that does not satisfy all
    three predicate conditions.
    """


def _poetry_direct_dependency_names(pyproject_toml: str) -> set[str]:
    """Canonical names of direct dependencies declared by ``[tool.poetry.dependencies]``.

    Fails closed on unparseable TOML.  The ``python`` key (interpreter
    constraint, not a distribution) is excluded.
    """
    try:
        data = tomllib.loads(pyproject_toml)
    except tomllib.TOMLDecodeError as exc:  # pragma: no cover - malformed authority
        raise DeclaredPinRuleError(f"malformed pyproject.toml: {exc}") from exc
    deps = (data.get("tool", {}).get("poetry", {}) or {}).get("dependencies", {})
    if not isinstance(deps, dict):
        raise DeclaredPinRuleError("pyproject.toml has no [tool.poetry.dependencies] table")
    return {normalize_name(k) for k in deps if k != "python"}


def _requirements_exact_pins(requirements_text: str) -> dict[str, str]:
    """Exact ``name==version`` pins from one requirements file, canonical names.

    Returns ``{canonical_name: version}``.  Non-exact constraint lines, marker
    suffixes and comments are skipped (decline injection).  Conflicting exact
    pins for the same canonical name are recorded as conflicted (the package is
    removed from the exact-pin map and injection is declined).  A malformed
    line that cannot be classified fails closed.
    """
    pins: dict[str, str] = {}
    conflicts: set[str] = set()
    for raw_line in requirements_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        line = line.split(";", maxsplit=1)[0].strip()  # drop env markers
        line = re.sub(r"\s+#.*$", "", line).strip()
        if not line:
            continue
        line = re.sub(r"\[[^\]]*\]", "", line)  # strip extras
        m = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)\s*(==|!=|>=|<=|>|<|~=|===)\s*([^\s]+)", line)
        if not m:
            if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", line):
                continue  # bare package name, no version -> inferred, decline
            raise DeclaredPinRuleError(f"malformed requirements line: {line!r}")
        name, op, version = m.group(1), m.group(2), m.group(3).strip()
        if op != "==":
            continue  # not an exact pin -> decline injection
        canonical = normalize_name(name)
        if canonical in pins and pins[canonical] != version:
            conflicts.add(canonical)
            continue
        pins[canonical] = version
    for canonical in conflicts:
        pins.pop(canonical, None)
    return pins


def declared_exact_pin_but_unlocked_pins(
    *,
    lock_pin_names: AbstractSet[str],
    pyproject_toml: str,
    requirements_texts: Mapping[str, str],
) -> list[str]:
    """GENERAL declared-but-unlocked pin rule (owner decision #1).

    At the exact historical commit, if a package
      * is a direct dependency declared by pyproject.toml,
      * has an exact ``name==version`` pin in an authoritative same-commit
        requirements file, and
      * is absent from poetry.lock,
    then that exact same-commit requirements pin is added to the runtime pin set.

    No compatible-version inference, no newest-version selection, no package /
    unit / commit special cases.  Fails closed on malformed dependency
    authorities and ambiguous canonical name matches; declines injection for
    every non-satisfying case (not declared, no exact pin, conflicting exact
    pins, already present in lock, unsupported expression, inferred version) so
    ordinary lock-complete commits stay lock-authoritative and unchanged.
    """
    declared = _poetry_direct_dependency_names(pyproject_toml)
    exact: dict[str, str] = {}
    conflicted: set[str] = set()
    for _filename, text in requirements_texts.items():
        for canonical, version in _requirements_exact_pins(text).items():
            if canonical in exact and exact[canonical] != version:
                conflicted.add(canonical)
                continue
            exact[canonical] = version
    for canonical in conflicted:
        exact.pop(canonical, None)

    out: list[str] = []
    for canonical in sorted(declared):
        if canonical in lock_pin_names:
            continue  # already present in lock -> lock-authoritative, unchanged
        found_version = exact.get(canonical)
        if found_version is None:
            continue  # no exact same-commit pin (or conflicted) -> decline injection
        out.append(f"{canonical}=={found_version}")
    return out


def route_requires_complete_main_plus_dev(install_route: str, lock_type: str) -> bool:
    """General rule: LOCK_FRAGMENT_MAIN_PLUS_DEV poetry requires the full closure.

    Keyed to the frozen install-route authority; never to a task/unit/commit
    identifier or package name.
    """
    return install_route == _LOCK_FRAGMENT_MAIN_PLUS_DEV and lock_type == "poetry"


def _r3_poetry_pins(lock_path: Path, python_version: str) -> list[str]:
    """Reuse the frozen R3 closure implementation verbatim (no cloning)."""
    if str(_HARNESS_DIR) not in sys.path:
        sys.path.insert(0, str(_HARNESS_DIR))
    from d7_r3_closure import poetry_pins

    pins, _ = poetry_pins(str(lock_path), python_version)
    return sorted(set(pins))


def complete_main_plus_dev_poetry_pins(lock_path: Path, python_version: str) -> list[str]:
    """The COMPLETE main+dev closure pins for a poetry lock (frozen R3 semantics).

    Pin names are PEP 503 normalized so exclusions supplied by the caller can
    be compared generically.
    """
    out: set[str] = set()
    for pin in _r3_poetry_pins(lock_path, python_version):
        name, _, version = pin.partition("==")
        out.add(f"{normalize_name(name)}=={version}")
    return sorted(out)


def derive_route_pins(
    *,
    install_route: str,
    lock_type: str,
    lock_path: Path,
    python_version: str,
    marker_excluded_names: AbstractSet[str] = frozenset(),
    win32_excluded_names: AbstractSet[str] = frozenset(),
) -> list[str]:
    """D7 behavioural closure pins for one member-task lock under its route.

    ``LOCK_FRAGMENT_MAIN_PLUS_DEV`` poetry: the frozen R3 complete main+dev
    closure MINUS the caller-supplied frozen R3 platform exclusions.  Unknown
    routes fail closed.
    """
    if not route_requires_complete_main_plus_dev(install_route, lock_type):
        raise RouteClosureError(
            f"no successor rule for route {install_route!r} lock_type {lock_type!r} (fail closed)"
        )
    excluded = set(marker_excluded_names) | set(win32_excluded_names)
    return sorted(
        p for p in complete_main_plus_dev_poetry_pins(lock_path, python_version)
        if p.partition("==")[0] not in excluded
    )


def derive_route_pins_multi(
    *,
    install_route: str,
    lock_type: str,
    lock_paths: list[Path],
    python_version: str,
    marker_excluded_names: AbstractSet[str] = frozenset(),
    win32_excluded_names: AbstractSet[str] = frozenset(),
) -> list[str]:
    """D7 behavioural closure pins across a unit's member-task locks.

    Deterministic deduplicated union over the member locks under the route's
    frozen rule.  Unknown routes fail closed.
    """
    if not route_requires_complete_main_plus_dev(install_route, lock_type):
        raise RouteClosureError(
            f"no successor rule for route {install_route!r} lock_type {lock_type!r} (fail closed)"
        )
    pins: set[str] = set()
    for lock_path in lock_paths:
        pins.update(
            derive_route_pins(
                install_route=install_route,
                lock_type=lock_type,
                lock_path=lock_path,
                python_version=python_version,
                marker_excluded_names=marker_excluded_names,
                win32_excluded_names=win32_excluded_names,
            )
        )
    return sorted(pins)
