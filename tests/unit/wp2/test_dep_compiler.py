"""WP-2 Env Closure V3.1 E2 - dependency compiler unit tests (ZERO API).

Covers legacy/modern poetry.lock dev detection, multi-group, markers,
unsupported sources, requirement-file parsing, uv preservation,
normalization, and VCR-family detection.
"""

from __future__ import annotations

from benchmark.wp2.dep_compiler import (
    dev_supplement_from_poetry,
    marker_applicable,
    normalize_pkg_name,
    parse_poetry_lock,
    parse_requirements,
)

LEGACY_BLOCK = """
[[package]]
name = "pytest-django-queries"
version = "1.1.0"
description = "pytest plugin"
category = "dev"
optional = false
python-versions = "*"
"""

LEGACY_MAIN_BLOCK = """
[[package]]
name = "django"
version = "3.2.7"
description = "web framework"
category = "main"
optional = false
python-versions = ">=3.6"
"""

MODERN_DEV_BLOCK = """
[[package]]
name = "pytest-mock"
version = "3.6.1"
description = "mock plugin"
category = "main"
optional = false
python-versions = ">=3.5"
groups = ["dev"]
"""

MULTI_GROUP_BLOCK = """
[[package]]
name = "freezegun"
version = "1.5.1"
description = "freeze time"
category = "main"
optional = false
python-versions = ">=3.6"
groups = ["main", "dev"]
"""

WIN_ONLY_BLOCK = """
[[package]]
name = "pywin32"
version = "305"
description = "windows only"
category = "dev"
optional = false
python-versions = ">=3.7"
markers = "sys_platform == 'win32'"
"""

PY310_ONLY_BLOCK = """
[[package]]
name = "black"
version = "22.3.0"
description = "formatter"
category = "dev"
optional = false
python-versions = ">=3.6.2"
markers = "python_version < '3.8'"
"""

GIT_BLOCK = """
[[package]]
name = "mypkg"
version = "1.0.0"
description = "git dep"
category = "dev"
optional = false
python-versions = "*"
source = {url = "https://github.com/x/y.git", reference = "abc", type = "git"}
"""

PATH_BLOCK = """
[[package]]
name = "localpkg"
version = "0.1"
description = "path dep"
category = "dev"
optional = false
python-versions = "*"
source = {path = "../local", editable = true}
"""


def _lock(*blocks: str) -> str:
    return "".join("[package.metadata]\n" + b + "\n" for b in blocks)


# E2.1 legacy poetry: category = "dev"
def test_legacy_poetry_category_dev_classified_dev() -> None:
    recs = parse_poetry_lock(_lock(LEGACY_BLOCK))
    assert len(recs) == 1
    assert recs[0].dev is True


# E2.2 modern poetry: groups = ["dev"]
def test_modern_poetry_groups_dev_classified_dev() -> None:
    recs = parse_poetry_lock(_lock(MODERN_DEV_BLOCK))
    assert len(recs) == 1
    assert recs[0].dev is True


# E2.3 multi-group ["main", "dev"] must be a dev supplement, not misparsed
def test_multi_group_includes_dev() -> None:
    recs = parse_poetry_lock(_lock(MULTI_GROUP_BLOCK))
    assert len(recs) == 1
    assert recs[0].dev is True
    assert recs[0].name == "freezegun"


# E2.4 legacy main: category = "main" is NOT a dev supplement
def test_legacy_main_not_dev() -> None:
    recs = parse_poetry_lock(_lock(LEGACY_MAIN_BLOCK))
    assert len(recs) == 1
    assert recs[0].dev is False


# E2.5 markers: windows-only and py<3.8 excluded on Linux py39; applicable kept
def test_marker_applicable_windows_only_excluded() -> None:
    assert marker_applicable("sys_platform == 'win32'", python_version="3.9") is False


def test_marker_applicable_python_version_excluded() -> None:
    assert marker_applicable("python_version < '3.8'", python_version="3.9") is False


def test_marker_applicable_included() -> None:
    assert marker_applicable("sys_platform == 'linux'", python_version="3.9") is True
    assert marker_applicable(None, python_version="3.9") is True


def test_dev_supplement_excludes_non_applicable_markers() -> None:
    sup = dev_supplement_from_poetry(_lock(WIN_ONLY_BLOCK, PY310_ONLY_BLOCK, LEGACY_BLOCK),
                                     python_version="3.9")
    names = [r["name"] for r in sup["records"]]
    assert "pytest-django-queries" in names
    assert "pywin32" not in names
    assert "black" not in names


# E2.6 source types: git/path/url/directory -> unsupported, no PyPI guess
def test_source_type_git_unsupported() -> None:
    recs = parse_poetry_lock(_lock(GIT_BLOCK))
    assert recs[0].source == "git"
    sup = dev_supplement_from_poetry(_lock(GIT_BLOCK), python_version="3.9")
    assert len(sup["unsupported"]) == 1
    assert sup["unsupported"][0]["source"] == "git"
    assert sup["pins"] == []


def test_source_type_path_unsupported() -> None:
    recs = parse_poetry_lock(_lock(PATH_BLOCK))
    assert recs[0].source == "path"
    sup = dev_supplement_from_poetry(_lock(PATH_BLOCK), python_version="3.9")
    assert len(sup["unsupported"]) == 1


# E2.7 requirements: exact pins vs constraints; -r deferred
def test_parse_requirements_exact_and_constraint() -> None:
    reqs = parse_requirements(
        "# comment\npytest==7.0.1\npytest-mock>=3.2\n-r other.txt\nSome_Pkg==1.2\n")
    d = dict(reqs)
    assert d["pytest"] == "7.0.1"
    assert d["pytest-mock"] == ">=3.2"
    assert d["some-pkg"] == "1.2"
    assert "-r" not in [n for n, _ in reqs]


# E2.8 uv-era: dev_supplement must signal uv preservation, not poetry pins
def test_uv_mode_signal() -> None:
    from benchmark.wp2.dep_compiler import derive_dev_test_closure

    out = derive_dev_test_closure({"uv.lock": "[uv.lock placeholder]",
                                   "pyproject.toml": "[tool.uv]"})
    assert out["mechanism"] == "uv"


def test_poetry_mechanism_signal() -> None:
    from benchmark.wp2.dep_compiler import derive_dev_test_closure

    out = derive_dev_test_closure({"poetry.lock": _lock(LEGACY_BLOCK)})
    assert out["mechanism"] == "poetry"
    assert "pytest-django-queries==1.1.0" in out["pins"]


# E2.9 normalization
def test_normalize_pkg_name() -> None:
    assert normalize_pkg_name("Foo_Bar") == "foo-bar"
    assert normalize_pkg_name("pytest-django-queries") == "pytest-django-queries"
    assert normalize_pkg_name(" PyTest-Mock ") == "pytest-mock"


# E2.11 VCR family detection (historically declared only)
def test_vcr_family_detection() -> None:
    from benchmark.wp2.dep_compiler import vcr_family_present

    assert vcr_family_present(["pytest-recording==0.13.2"]) == ["pytest-recording"]
    assert vcr_family_present(["pytest-vcr==1.0.2"]) == ["pytest-vcr"]
    assert vcr_family_present(["vcrpy==4.1.1"]) == ["vcrpy"]
    assert vcr_family_present(["pytest==7.0.1"]) == []


# E2.10 real-lock regression (fixture lock sample from legacy Saleor)
def test_real_legacy_lock_22ec() -> None:
    snippet = """
[[package]]
name = "pytest-django-queries"
version = "1.1.0"
description = "Pytest plugin for checking django queries count"
category = "dev"
optional = false
python-versions = "*"

[[package]]
name = "django"
version = "3.2.7"
description = "A high-level Python Web framework"
category = "main"
optional = false
python-versions = ">=3.6"
"""
    recs = parse_poetry_lock(snippet)
    by_name = {r.name: r for r in recs}
    assert by_name["pytest-django-queries"].dev is True
    assert by_name["django"].dev is False


# E2.10b poetry+requirements.txt: main roots = requirements.txt, so dev/test
# plugins declared in pyproject main deps but absent from requirements.txt are
# still derived as the DEV/TEST supplement.
def test_poetry_plus_req_uses_req_main_roots() -> None:
    from benchmark.wp2.dep_compiler import derive_dev_test_closure

    modern_lock = _lock(MODERN_DEV_BLOCK)  # pytest-mock, no group info needed
    manifests = {
        "poetry.lock": modern_lock,
        "requirements.txt": "django==3.2.7\npytest-django==4.2.0\n",
        "pyproject.toml": (
            "[tool.poetry.dependencies]\n"
            "python = '^3.9'\n"
            "django = '^3.2'\n"
            "pytest-mock = '^3.6'\n"
        ),
    }
    out = derive_dev_test_closure(manifests, python_version="3.9")
    assert out["mechanism"] == "poetry"
    # pytest-mock is NOT in requirements.txt -> dev supplement
    assert "pytest-mock==3.6.1" in out["pins"]
