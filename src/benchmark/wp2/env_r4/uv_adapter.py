"""R4-B uv.lock lock adapter — Track B implementation behind the frozen R4 interface.

Mission ``M17_D7_R4_B_UV_LOCK_ADAPTER``.

This module implements the required ``parse_lock`` entry point (and the
``LockParser`` Protocol shape) WITHOUT touching the frozen shared interface
(``env_r4/contracts.py`` and ``env_r4/__init__.py`` stay byte-for-byte
unchanged).  It normalizes a deterministic ``uv.lock`` into the frozen
``LockClosure`` contract, and preserves the already-qualified Poetry path by
reusing the frozen R3 Poetry closure code (``benchmark.wp2.source_fidelity_r1``
and ``benchmark.wp2.dep_compiler``) as read-only evidence.

Design rules implemented here (each mirrors a frozen R4 rule):

* The root virtual/editable project (``source = { virtual = ... }``) is carried
  by ``LockClosure.editable_self`` as ``EDITABLE_SELF`` and is NEVER emitted as
  a third-party wheel requirement.
* Source types map to exactly REGISTRY / DIRECTORY / PATH / EDITABLE_SELF;
  any other uv source (git / url / file / editable / multi-key / unknown)
  FAILS CLOSED because the frozen 4-member enum cannot represent it without
  inventing policy.
* Dependency markers are evaluated against the ``RuntimeTarget``; packages that
  are not applicable are recorded deterministically in ``exclusions`` (no
  silent skips).
* The lock-level ``requires-python`` gates the whole lock: a target whose
  Python version is not admitted FAILS CLOSED.
* Malformed lock data, unknown sources, invalid markers and unsupported lock
  formats FAIL CLOSED via ``LockParseError``.
* No task-ID / commit-ID special cases exist in this module.
* ``wheel_compatible`` is OUT_OF_SCOPE for R4-B and therefore fails closed.
"""
from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from packaging.markers import Marker
from packaging.specifiers import SpecifierSet

from benchmark.wp2 import source_fidelity_r1 as _sf
from benchmark.wp2.dep_compiler import marker_applicable
from benchmark.wp2.env_r4.contracts import (
    LockClosure,
    LockParseError,
    NormalizedRequirement,
    RuntimeTarget,
    SourceType,
    bind_lock_parser,
    normalize_name,
)

LOCK_FORMAT_UV = "uv"
LOCK_FORMAT_POETRY = "poetry"

_UV_SOURCE_KEYS = ("registry", "directory", "path", "virtual")
_POETRY_KEYS = ("category", "groups", "python-versions", "description", "optional")


class EnvR4LockAdapter:
    """Deterministic uv.lock adapter that also preserves the qualified Poetry path."""

    def parse_lock(
        self,
        lock_path: Path,
        target: RuntimeTarget,
        pyproject_path: Path | None = None,  # noqa: ARG002 - frozen interface signature
    ) -> LockClosure:
        lock_text = _read_lock_text(lock_path)
        lock_format = _detect_lock_format(lock_text)
        if lock_format == LOCK_FORMAT_UV:
            return _parse_uv_lock(lock_text, target)
        return _parse_poetry_lock(lock_text, target)

    def wheel_compatible(
        self,
        wheel_filename: str,  # noqa: ARG002 - frozen interface signature
        target: RuntimeTarget,  # noqa: ARG002 - frozen interface signature
    ) -> bool:
        raise LockParseError(
            "wheel compatibility is OUT_OF_SCOPE for R4-B (frozen interface "
            "entry point preserved, behaviour not implemented)"
        )


def bind_r4_b_parser() -> None:
    """Bind the R4-B adapter behind the frozen interface (Track B)."""
    bind_lock_parser(EnvR4LockAdapter())


def _read_lock_text(lock_path: Path) -> str:
    try:
        raw = lock_path.read_bytes()
    except OSError as exc:
        raise LockParseError(f"cannot read lock file {lock_path}: {exc} (fail closed)") from exc
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise LockParseError(f"lock file {lock_path} is not utf-8 (fail closed)") from exc


def _detect_lock_format(lock_text: str) -> str:
    """Deterministically classify a lock file as uv or poetry (fail closed).

    uv.lock carries an integer top-level ``version`` (1/2) plus a ``package``
    list whose entries use uv inline ``source`` tables.  poetry.lock carries a
    ``metadata`` table and/or poetry package keys.  Anything else fails closed.
    """
    try:
        data = tomllib.loads(lock_text)
    except tomllib.TOMLDecodeError as exc:
        raise LockParseError(f"lock file is not valid TOML (fail closed): {exc}") from exc
    if not isinstance(data.get("package"), list):
        raise LockParseError("lock file has no [[package]] list (fail closed)")
    packages = data["package"]
    if (
        isinstance(data.get("version"), int)
        and data["version"] in (1, 2)
        and any(
            isinstance(p, dict)
            and isinstance(p.get("source"), dict)
            and set(p["source"].keys()) & set(_UV_SOURCE_KEYS)
            for p in packages
        )
    ):
        return LOCK_FORMAT_UV
    if isinstance(data.get("metadata"), dict) or any(
        isinstance(p, dict) and (set(p) & set(_POETRY_KEYS)) for p in packages
    ):
        return LOCK_FORMAT_POETRY
    raise LockParseError(
        "unsupported lock format: neither uv nor poetry structure detected (fail closed)"
    )


def _marker_env(target: RuntimeTarget) -> dict[str, str]:
    """PEP 508 marker evaluation environment derived from the RuntimeTarget."""
    return {
        "sys_platform": target.platform,
        "platform_system": "Linux" if target.platform == "linux" else "Windows",
        "platform_machine": target.architecture,
        "python_version": target.python_version,
        "python_full_version": f"{target.python_version}.0",
        "platform_python_implementation": (
            "CPython" if target.implementation == "cpython" else "PyPy"
        ),
        "os_name": "posix" if target.platform == "linux" else "nt",
        "implementation_name": target.implementation,
    }


def _evaluate_marker(marker_text: str, target: RuntimeTarget) -> bool:
    """Strictly evaluate a PEP 508 marker for the target (fail closed)."""
    try:
        return bool(Marker(marker_text).evaluate(_marker_env(target)))
    except Exception as exc:
        raise LockParseError(
            f"unsupported or invalid marker {marker_text!r} (fail closed): {exc}"
        ) from exc


def _classify_uv_source(source: dict[str, Any] | None) -> tuple[SourceType, str | None]:
    """Classify a uv ``source`` table into the frozen 4-member SourceType.

    ``None`` (no source table) is an implicit registry package.  Any other uv
    source (git / url / file / editable / multi-key / unknown) fails closed.
    """
    if not source:
        return SourceType.REGISTRY, None
    keys = set(source)
    if keys == {"registry"}:
        if not isinstance(source["registry"], str):
            raise LockParseError(f"malformed uv registry source {source!r} (fail closed)")
        return SourceType.REGISTRY, source["registry"]
    if keys == {"directory"}:
        if not isinstance(source["directory"], str):
            raise LockParseError(f"malformed uv directory source {source!r} (fail closed)")
        return SourceType.DIRECTORY, source["directory"]
    if keys == {"path"}:
        if not isinstance(source["path"], str):
            raise LockParseError(f"malformed uv path source {source!r} (fail closed)")
        return SourceType.PATH, source["path"]
    if keys == {"virtual"}:
        if not isinstance(source["virtual"], str):
            raise LockParseError(f"malformed uv virtual source {source!r} (fail closed)")
        return SourceType.EDITABLE_SELF, source["virtual"]
    raise LockParseError(
        f"unknown or ambiguous uv source {source!r} (fail closed; frozen SourceType "
        "has exactly REGISTRY/DIRECTORY/PATH/EDITABLE_SELF)"
    )


def _own_applies(pkg: dict[str, Any], target: RuntimeTarget) -> bool:
    """A package's own marker and requires-python admit the target (strict)."""
    own_marker = pkg.get("marker")
    if own_marker is not None and not _evaluate_marker(str(own_marker), target):
        return False
    own_rp = pkg.get("requires-python")
    if own_rp is not None:
        try:
            spec = SpecifierSet(str(own_rp))
        except Exception as exc:
            raise LockParseError(
                f"invalid requires-python {own_rp!r} (fail closed): {exc}"
            ) from exc
        if target.python_version not in spec:
            return False
    return True


def _parse_uv_lock(lock_text: str, target: RuntimeTarget) -> LockClosure:
    data = tomllib.loads(lock_text)
    version = data.get("version")
    if not isinstance(version, int) or version not in (1, 2):
        raise LockParseError(
            f"unsupported uv.lock version {version!r} (fail closed; only 1/2 validated)"
        )

    requires_python = data.get("requires-python")
    if requires_python is not None:
        try:
            spec = SpecifierSet(str(requires_python))
        except Exception as exc:
            raise LockParseError(
                f"invalid requires-python {requires_python!r} (fail closed): {exc}"
            ) from exc
        if target.python_version not in spec:
            raise LockParseError(
                f"lock requires-python {requires_python!r} does not admit target "
                f"python {target.python_version} (fail closed)"
            )

    for group in ("resolution-markers", "supported-markers"):
        markers = data.get(group, [])
        if isinstance(markers, list):
            for m in markers:
                _evaluate_marker(str(m), target)

    packages = data["package"]
    by_name: dict[str, dict[str, Any]] = {}
    for pkg in packages:
        name = pkg.get("name")
        pkg_version = pkg.get("version")
        if not isinstance(name, str) or not name or not isinstance(pkg_version, str) or not pkg_version:
            raise LockParseError(f"uv package missing required name/version (fail closed): {pkg}")
        if name in by_name:
            raise LockParseError(
                f"ambiguous source identity: duplicate package name {name!r} (fail closed)"
            )
        by_name[name] = pkg

    root_names = [
        name for name, pkg in by_name.items()
        if isinstance(pkg.get("source"), dict) and "virtual" in pkg["source"]
    ]
    if len(root_names) > 1:
        raise LockParseError(
            f"ambiguous source identity: multiple virtual root projects {root_names} (fail closed)"
        )
    root_name = root_names[0] if root_names else None

    applicable = _reachable_applicable(by_name, root_name, target)
    referencing_markers, unconditional_refs = _referencing_edge_markers(by_name)

    requirements: list[NormalizedRequirement] = []
    exclusions: list[NormalizedRequirement] = []
    editable_self: NormalizedRequirement | None = None

    for name, pkg in by_name.items():
        source_type, reference = _classify_uv_source(pkg.get("source"))

        if name == root_name:
            editable_self = NormalizedRequirement(
                normalized_name=normalize_name(name),
                version=str(pkg["version"]),
                source_type=SourceType.EDITABLE_SELF,
                source_reference=reference,
                marker=None,
                marker_applies=True,
                editable_self=True,
            )
            continue

        marker_text = _package_marker(
            pkg,
            referencing_markers.get(name, []),
            unconditional=name in unconditional_refs,
        )
        applies = name in applicable
        marker_applies = (
            True
            if marker_text is None
            else _evaluate_marker(marker_text, target)
        )
        req = NormalizedRequirement(
            normalized_name=normalize_name(name),
            version=str(pkg["version"]),
            source_type=source_type,
            source_reference=reference,
            marker=marker_text,
            marker_applies=marker_applies,
            editable_self=False,
        )
        if applies:
            requirements.append(req)
        else:
            exclusions.append(req)

    return LockClosure(
        lock_format=LOCK_FORMAT_UV,
        target=target,
        requirements=tuple(requirements),
        editable_self=editable_self,
        exclusions=tuple(exclusions),
        fail_closed_reasons=(),
    )


def _referencing_edge_markers(
    by_name: dict[str, dict[str, Any]],
) -> tuple[dict[str, list[str]], set[str]]:
    """Distinct edge markers that reference each package across the lock.

    A package is installed when ANY referencing edge is active, so the union of
    the distinct edge markers is the governing raw marker string (deterministic:
    sorted).  Edges without a marker are unconditional: a package with at least
    one unconditional reference is never marker-gated (returned in the second
    set).
    """
    referenced: dict[str, set[str]] = {name: set() for name in by_name}
    unconditional: set[str] = set()
    for pkg in by_name.values():
        for edge in _all_edges(pkg):
            dep_name = edge.get("name")
            if not isinstance(dep_name, str) or dep_name not in referenced:
                continue
            edge_marker = edge.get("marker")
            if edge_marker is None:
                unconditional.add(dep_name)
            else:
                referenced[dep_name].add(str(edge_marker))
    return {name: sorted(markers) for name, markers in referenced.items()}, unconditional


def _package_marker(
    pkg: dict[str, Any],
    referencing_markers: list[str],
    *,
    unconditional: bool,
) -> str | None:
    """Deterministic raw marker string governing a package's inclusion.

    Priority: the package's own ``marker`` field; otherwise the OR-conjunction
    of all distinct edge markers that reference the package; otherwise None.
    A package with an unconditional reference is never marker-gated, so its
    governing marker is its own ``marker`` field or None.
    """
    own = pkg.get("marker")
    if own is not None:
        return str(own)
    if not unconditional and referencing_markers:
        return "(" + ") or (".join(referencing_markers) + ")"
    return None


def _reachable_applicable(
    by_name: dict[str, dict[str, Any]],
    root_name: str | None,
    target: RuntimeTarget,
) -> set[str]:
    """Packages applicable to the target, via uv edge-marker reachability.

    The root project is always applicable.  A dependency edge is traversed only
    when its own marker (if any) evaluates true for the target AND the source
    package itself is applicable.  Packages that fail their own marker or
    requires-python do not propagate their edges (uv resolution semantics).

    All root edge groups participate: ``dependencies`` (list), and the
    ``dev-dependencies`` / ``optional-dependencies`` group dicts, so the
    resolved closure matches uv's main + dev + extras lock.
    """
    if root_name is None:
        return set(by_name)

    applicable: set[str] = set()
    stack = [root_name]
    while stack:
        name = stack.pop()
        if name in applicable:
            continue
        pkg = by_name[name]
        if not _own_applies(pkg, target):
            continue
        applicable.add(name)
        for edge in _all_edges(pkg):
            dep_name = edge.get("name")
            if not isinstance(dep_name, str) or dep_name not in by_name:
                raise LockParseError(
                    f"dependency edge {dep_name!r} does not resolve to a package (fail closed)"
                )
            edge_marker = edge.get("marker")
            if edge_marker is None or _evaluate_marker(str(edge_marker), target):
                stack.append(dep_name)
    return applicable


def _all_edges(pkg: dict[str, Any]) -> list[dict[str, Any]]:
    """All dependency edges of one uv package record.

    ``dependencies`` is a list of edges; ``dev-dependencies`` and
    ``optional-dependencies`` are group dicts whose values are edge lists.
    """
    edges: list[dict[str, Any]] = []
    deps = pkg.get("dependencies")
    if isinstance(deps, list):
        edges.extend(d for d in deps if isinstance(d, dict))
    for group_field in ("dev-dependencies", "optional-dependencies"):
        groups = pkg.get(group_field)
        if isinstance(groups, dict):
            for value in groups.values():
                if isinstance(value, list):
                    edges.extend(d for d in value if isinstance(d, dict))
    return edges


def _parse_poetry_lock(lock_text: str, target: RuntimeTarget) -> LockClosure:
    """Poetry path: preserve the qualified R3 closure semantics (read-only reuse).

    The frozen ``source_fidelity_r1`` classification and ``dep_compiler`` marker
    evaluation are reused verbatim so the normalized closure stays equivalent to
    the predecessor semantics for the exercised cases.  Source types that the
    frozen 4-member enum cannot represent (git / url / file / unknown) fail
    closed.
    """
    records = _sf._poetry_lock_packages(lock_text)  # frozen R3, read-only reuse

    requirements: list[NormalizedRequirement] = []
    exclusions: list[NormalizedRequirement] = []

    for rec in records:
        name = str(rec["name"])
        version = str(rec["version"])
        markers = rec.get("markers")
        pyv = rec.get("python_versions")

        applicable = (
            marker_applicable(
                markers,
                sys_platform=target.platform,
                python_version=target.python_version,
            )
            and _sf._pyv_matches(pyv, target.python_version)
        )

        source_type_str, reference = _sf.classify_poetry_source(rec.get("source"))
        source_type = {
            _sf.SOURCE_TYPE_REGISTRY: SourceType.REGISTRY,
            _sf.SOURCE_TYPE_DIRECTORY: SourceType.DIRECTORY,
            _sf.SOURCE_TYPE_PATH: SourceType.PATH,
        }.get(source_type_str)
        if source_type is None:
            raise LockParseError(
                f"poetry source type {source_type_str!r} is not representable in the "
                "frozen 4-member SourceType (fail closed)"
            )

        req = NormalizedRequirement(
            normalized_name=normalize_name(name),
            version=version,
            source_type=source_type,
            source_reference=reference,
            marker=markers,
            marker_applies=applicable,
            editable_self=False,
        )
        if applicable:
            requirements.append(req)
        else:
            exclusions.append(req)

    return LockClosure(
        lock_format=LOCK_FORMAT_POETRY,
        target=target,
        requirements=tuple(requirements),
        editable_self=None,
        exclusions=tuple(exclusions),
        fail_closed_reasons=(),
    )
