"""WP-2 Env Closure V3.1 - historical DEV/TEST dependency compiler (ZERO API).

Rule-derived historical dev/test closure from TARGET-commit evidence (never
task-ID based). Covers legacy poetry.lock (``category = "dev"``), modern
poetry.lock (``groups = [...]``), multi-group packages, environment markers,
unsupported package sources, and dev/test requirement files.

The MAIN install mechanism is deliberately untouched; this module only derives
the exact historical DEV/TEST supplement. No package version is ever chosen
from "latest": exact lock pins first, historical constraints second, and an
explicit ``unsupported`` result when no exact reproducible installation can be
constructed from the historical record.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from packaging.markers import Marker
from packaging.specifiers import SpecifierSet

SOURCE_INDEX = "index"
SOURCE_GIT = "git"
SOURCE_PATH = "path"
SOURCE_DIRECTORY = "directory"
SOURCE_URL = "url"

PYTHON_VERSION_BY_ERA = {"py38": "3.8", "py39": "3.9", "py312": "3.12"}

VCR_FAMILY = ("pytest-recording", "pytest-vcr", "vcrpy", "pytest-socket")


@dataclass
class PkgRecord:
    name: str
    version: str | None
    dev: bool
    source: str = SOURCE_INDEX
    markers: str | None = None
    python_versions: str | None = None
    group_info: bool = False


def normalize_pkg_name(name: str) -> str:
    """Deterministic package-name normalization for comparison."""
    return name.strip().lower().replace("_", "-")


def _marker_text(block: str) -> str | None:
    m = re.search(r'markers\s*=\s*"([^"]*)"', block)
    if m and m.group(1).strip():
        return m.group(1).strip()
    m = re.search(r"markers\s*=\s*'([^']*)'", block)
    return m.group(1).strip() if m and m.group(1).strip() else None


def _source_of(block: str) -> str:
    for kind, pat in (
        (SOURCE_GIT, r"\bsource\s*=\s*\{[^}]*\btype\s*=\s*[\"']?git[\"']?"),
        (SOURCE_URL, r"\bsource\s*=\s*\{[^}]*\btype\s*=\s*[\"']?url[\"']?|^url\s*="),
        (SOURCE_PATH, r"\bsource\s*=\s*\{[^}]*\bpath\b|^path\s*="),
        (SOURCE_DIRECTORY, r"\bsource\s*=\s*\{[^}]*\bdirectory\b"),
    ):
        if re.search(pat, block, re.MULTILINE):
            return kind
    return SOURCE_INDEX


def parse_poetry_lock(lock_text: str) -> list[PkgRecord]:
    """Parse a poetry.lock into package records (legacy + modern formats).

    ``group_info`` is True when the block carries category/groups metadata
    (poetry <=1.0 legacy ``category`` or modern ``groups``). Modern poetry.lock
    (>=1.1) carries NO per-package group info; the dev/main split is then
    derived from pyproject.toml + the lock dependency graph.
    """
    records: list[PkgRecord] = []
    for block in re.split(r"\[\[package\]\]", lock_text)[1:]:
        name_m = re.search(r'name\s*=\s*"([^"]+)"', block)
        ver_m = re.search(r'version\s*=\s*"([^"]+)"', block)
        if not name_m or not ver_m:
            continue
        dev = False
        group_info = False
        category_m = re.search(r'category\s*=\s*"([^"]+)"', block)
        if category_m:
            group_info = True
            dev = category_m.group(1) == "dev"
        groups_m = re.search(r"groups\s*=\s*\[([^\]]*)\]", block)
        if groups_m is not None:
            group_info = True
            dev = dev or "dev" in groups_m.group(1)
        pv_m = re.search(r'python-versions\s*=\s*"([^"]+)"', block)
        records.append(PkgRecord(
            name=name_m.group(1),
            version=ver_m.group(1),
            dev=dev,
            source=_source_of(block),
            markers=_marker_text(block),
            python_versions=pv_m.group(1).strip() if pv_m else None,
            group_info=group_info,
        ))
    return records


def main_dep_names(pyproject_text: str) -> set[str]:
    """Top-level MAIN dependency names from [tool.poetry.dependencies]."""
    m = re.search(r"\[tool\.poetry\.dependencies\]\s*(.*?)(?=\n\[)", pyproject_text, re.DOTALL)
    if not m:
        return set()
    names: set[str] = set()
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("python"):
            continue
        km = re.match(r"^([A-Za-z0-9_.-]+)\s*=", line)
        if km:
            names.add(normalize_pkg_name(km.group(1)))
    return names


def pyproject_dev_group_names(pyproject_text: str) -> set[str]:
    """DEV/TEST group names from pyproject.toml (all historical forms)."""
    names: set[str] = set()
    for pattern in (r"\[tool\.poetry\.group\.dev\.dependencies\]",
                    r"\[tool\.poetry\.dev-dependencies\]",
                    r"\[dependency-groups\]\s*\n\s*dev\s*=\s*\{"):
        m = re.search(pattern + r"\s*(.*?)(?=\n\[)", pyproject_text, re.DOTALL)
        if not m:
            continue
        for line in m.group(1).splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if pattern.endswith("=") and line.startswith(("[", "]")):
                continue
            km = re.match(r"^([A-Za-z0-9_.-]+)\s*=", line)
            if km:
                names.add(normalize_pkg_name(km.group(1)))
            else:
                # [dependency-groups] dev table entries like  'name = ...' or toml lines
                km2 = re.match(r"^['\"]?([A-Za-z0-9_.-]+)['\"]?\s*=", line)
                if km2:
                    names.add(normalize_pkg_name(km2.group(1)))
    return names


def lock_dependency_edges(lock_text: str) -> dict[str, list[str]]:
    """name -> dependency names, from each [[package]] [package.dependencies]."""
    edges: dict[str, list[str]] = {}
    for block in re.split(r"\[\[package\]\]", lock_text)[1:]:
        name_m = re.search(r'name\s*=\s*"([^"]+)"', block)
        if not name_m:
            continue
        deps: list[str] = []
        dm = re.search(r"\[package\.dependencies\]\s*(.*?)(?=\n\[package|\n\[\[package\]\])",
                       block, re.DOTALL)
        if dm:
            for line in dm.group(1).splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                km = re.match(r"^([A-Za-z0-9_.-]+)\s*=", line)
                if km:
                    deps.append(normalize_pkg_name(km.group(1)))
        edges[normalize_pkg_name(name_m.group(1))] = deps
    return edges


def main_reachable_names(lock_text: str, pyproject_text: str) -> set[str]:
    """BFS closure of MAIN dependency names over the lock dependency graph."""
    return _reachable_from(main_dep_names(pyproject_text), lock_text)


def requirements_main_names(requirements_text: str) -> set[str]:
    """Main-recipe roots for the poetry+requirements.txt path."""
    return {name for name, _ver in parse_requirements(requirements_text)}


def _reachable_from(roots: set[str], lock_text: str) -> set[str]:
    edges = lock_dependency_edges(lock_text)
    seen: set[str] = set(roots)
    stack = list(roots)
    while stack:
        cur = stack.pop()
        for d in edges.get(cur, []):
            if d not in seen:
                seen.add(d)
                stack.append(d)
    return seen


def parse_requirements(text: str) -> list[tuple[str, str | None]]:
    """Parse a requirements file into (normalized_name, exact|constraint|None).

    ``-r``/``--requirement`` includes are NOT followed here (the caller maps
    files); each line is returned only if it carries a pin/constraint.
    """
    out: list[tuple[str, str | None]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        line = re.sub(r"\s+#.*$", "", line).strip()
        if not line:
            continue
        line = re.sub(r"\[[^\]]*\]", "", line)  # strip extras
        m = re.match(r"^([A-Za-z0-9_.-]+)\s*(==|!=|>=|<=|>|<|~=|===)\s*([^\s;]+)", line)
        if not m:
            continue
        name = normalize_pkg_name(m.group(1))
        op, ver = m.group(2), m.group(3).strip()
        if op == "==" and ver:
            out.append((name, ver))
        elif op:
            out.append((name, f"{op}{ver}"))
        else:
            out.append((name, None))
    return out


def marker_applicable(markers: str | None, *, sys_platform: str = "linux",
                      python_version: str) -> bool:
    """Evaluate a poetry marker string for the target Linux + historical Python."""
    if not markers:
        return True
    env = {
        "sys_platform": sys_platform,
        "platform_system": "Linux" if sys_platform == "linux" else "Windows",
        "platform_machine": "x86_64",
        "python_version": python_version,
        "python_full_version": f"{python_version}.0",
        "platform_python_implementation": "CPython",
        "os_name": "posix" if sys_platform == "linux" else "nt",
        "implementation_name": "cpython",
    }
    try:
        return bool(Marker(markers).evaluate(env))
    except Exception:
        # Unparseable marker: include conservatively; install/preflight will
        # surface an actual problem instead of silently dropping a dep.
        return True


def _pyv_matches(python_versions: str | None, python_version: str) -> bool:
    if not python_versions or python_versions.strip() == "*":
        return True
    try:
        return python_version in SpecifierSet(python_versions)
    except Exception:
        return True


def _applicable_records(records: list[PkgRecord], *, python_version: str,
                        sys_platform: str) -> list[PkgRecord]:
    return [
        r for r in records
        if marker_applicable(r.markers, sys_platform=sys_platform, python_version=python_version)
        and _pyv_matches(r.python_versions, python_version)
    ]


def all_locked_pins(lock_text: str, *, python_version: str,
                    sys_platform: str = "linux") -> dict:
    """Every exact locked pin applicable to the target (main + dev/test).

    Returns {"pins": [...], "unsupported": [...]}. Non-index sources are never
    guessed and reported separately.
    """
    pins: list[str] = []
    unsupported: list[dict] = []
    for rec in _applicable_records(parse_poetry_lock(lock_text),
                                   python_version=python_version, sys_platform=sys_platform):
        if rec.source != SOURCE_INDEX:
            unsupported.append({"name": rec.name, "version": rec.version, "source": rec.source})
            continue
        if rec.version:
            pins.append(f"{rec.name}=={rec.version}")
    return {"pins": pins, "unsupported": unsupported}


def dev_supplement_from_poetry(lock_text: str, *, python_version: str,
                               sys_platform: str = "linux",
                               pyproject_text: str | None = None,
                               main_roots: set[str] | None = None,
                               dev_group_names: set[str] | None = None) -> dict:
    """Exact historical DEV/TEST pins (name==version) from a poetry.lock.

    Dev membership is determined by:
    1. per-package group metadata when the lock carries it (legacy category /
       modern groups), else
    2. the dev closure = locked packages NOT reachable from the ACTUAL main
       recipe roots (``main_roots``; for poetry+requirements.txt this is the
       requirements.txt name set), else
    3. the pyproject DEV/TEST group declarations (``dev_group_names``) resolved
       to exact lock versions (for the ``-e .`` main path where the build
       backend may not install the declared dev plugins).

    Returns {"pins": [...], "unsupported": [...], "records": [...]}. Packages
    with a non-index source are reported as unsupported (never guessed).
    """
    records = parse_poetry_lock(lock_text)
    has_group_info = any(r.group_info for r in records)
    if not has_group_info and main_roots is not None:
        main_reachable = _reachable_from(main_roots, lock_text)
        dev_recs = [r for r in records if r.name not in main_reachable]
    elif not has_group_info and dev_group_names:
        dev_recs = [r for r in records if r.name in dev_group_names]
    elif not has_group_info and pyproject_text:
        main_reachable = _reachable_from(main_dep_names(pyproject_text), lock_text)
        dev_recs = [r for r in records if r.name not in main_reachable]
    else:
        dev_recs = [r for r in records if r.dev]

    pins: list[str] = []
    unsupported: list[dict] = []
    recs: list[dict] = []
    for rec in _applicable_records(dev_recs, python_version=python_version,
                                   sys_platform=sys_platform):
        recs.append(rec.__dict__)
        if rec.source != SOURCE_INDEX:
            unsupported.append({"name": rec.name, "version": rec.version,
                                "source": rec.source})
            continue
        if rec.version:
            pins.append(f"{rec.name}=={rec.version}")
    return {"pins": pins, "unsupported": unsupported, "records": recs}


def _pins_from_req_files(req_dev: str | None, req_test: str | None) -> list[str]:
    pins: list[str] = []
    for text in (req_dev, req_test):
        if not text:
            continue
        for name, ver in parse_requirements(text):
            if ver and ver.startswith("=="):
                pins.append(f"{name}=={ver[2:]}")
    # de-dup preserving order
    return list(dict.fromkeys(pins))


def derive_dev_test_closure(manifests: dict[str, str], *,
                            python_version: str | None = None,
                            sys_platform: str = "linux") -> dict:
    """Derive the exact historical DEV/TEST closure from target manifests.

    Priority: poetry.lock exact pins -> dev/test requirement files exact pins.
    uv.lock -> the frozen uv-group mechanism is preserved unchanged.
    """
    out: dict = {"mechanism": None, "pins": [], "unsupported": [],
                 "records": [], "note": ""}
    if "uv.lock" in manifests:
        out["mechanism"] = "uv"
        out["note"] = ("uv-era: frozen `uv export --frozen --group dev` "
                       "mechanism preserved unchanged (E3.5).")
        return out
    if "poetry.lock" in manifests:
        pv = python_version or "3.11"
        main_roots: set[str] | None = None
        dev_group_names: set[str] | None = None
        if "requirements.txt" in manifests:
            # poetry + requirements.txt: the ACTUAL main recipe is
            # `-r requirements.txt`; dev supplement = lock packages not
            # reachable from those pins.
            main_roots = requirements_main_names(manifests["requirements.txt"])
        elif pyproject := manifests.get("pyproject.toml"):
            # `-e .` path: main roots would be the pyproject main deps, but the
            # editable install may not materialize the declared dev plugins, so
            # the dev supplement = the pyproject DEV/TEST group declarations
            # resolved to exact lock versions.
            dev_group_names = pyproject_dev_group_names(pyproject) or None
            main_roots = None
        sup = dev_supplement_from_poetry(
            manifests["poetry.lock"],
            python_version=pv,
            sys_platform=sys_platform,
            pyproject_text=manifests.get("pyproject.toml"),
            main_roots=main_roots,
            dev_group_names=dev_group_names,
        )
        out["mechanism"] = "poetry"
        out["pins"] = sup["pins"]
        out["unsupported"] = sup["unsupported"]
        out["records"] = sup["records"]
        out["all_locked_pins"] = all_locked_pins(
            manifests["poetry.lock"], python_version=pv, sys_platform=sys_platform)
        return out
    # no lock: dev/test requirement files
    pins = _pins_from_req_files(manifests.get("requirements_dev.txt"),
                                manifests.get("requirements-test.txt"))
    if pins:
        out["mechanism"] = "requirements"
        out["pins"] = pins
    else:
        out["mechanism"] = "none"
        out["note"] = "no historical lock and no exact dev/test pins found"
    return out


def vcr_family_present(pins: list[str]) -> list[str]:
    """Which VCR-family plugins are represented in an exact-pin list."""
    found = []
    for pin in pins:
        name = normalize_pkg_name(pin.split("==")[0].strip())
        if name in VCR_FAMILY:
            found.append(name)
    return found


def exclude_tooling_pins(pins: list[str], lock_text: str,
                         tooling_names: set[str]) -> list[str]:
    """Drop harness-tooling packages and their transitive deps from a pin list.

    The frozen Harness tooling (pytest, pytest-django, pytest-socket,
    pytest-xdist, ...) is installed separately by TOOLING_INSTALL at pinned
    versions; the historical dev/test closure must not downgrade it.
    """
    excluded = _reachable_from(tooling_names, lock_text)
    return [p for p in pins if normalize_pkg_name(p.split("==")[0]) not in excluded]
