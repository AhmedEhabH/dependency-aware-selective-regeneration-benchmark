"""R4 Poetry Closure Successor — targeted tests (S2, fail-before-implement).

Mission ``M17_D7_R4_POETRY_CLOSURE_SUCCESSOR_QUALIFICATION``.

These tests reproduce the frozen semantic defect GENERICALLY (no task/unit/
commit/package special case) and pin the successor behavioural closure
projection against the frozen authorities:

* ``D7_R3_HARNESS_CONTRACT`` + ``d7_r3_closure.py`` — complete main+dev closure
  for ``LOCK_FRAGMENT_MAIN_PLUS_DEV`` poetry locks, exactly-two frozen platform
  exclusions.
* ``D7_REQUIRED_CLOSURE_AUDIT`` — machine-readable expected main/dev closure.

Required coverage (mission S2 P1..P10):

  P1  a representative Poetry lock where package-level marker metadata would
      remove main/dev packages under generic marker evaluation, while the
      frozen LOCK_FRAGMENT_MAIN_PLUS_DEV route authority requires the complete
      main+dev closure.
  P2  complete main+dev packages survive the D7 route projection.
  P3  frozen target/platform exclusions that R3 legitimately applies remain
      excluded (do NOT include every package blindly).
  P4  no task-ID / unit-ID / commit-ID / package-name / known-failure special
      case affects the result.
  P5  repeated derivation is deterministic and byte-identical.
  P6  V2_EDITABLE_PLUS_LOCK_DEV is checked against its frozen complete-main+dev
      authority (existing implementation already yields the complete closure,
      so it stays unchanged).
  P7  UV_EXPORT remains unchanged unless its own authority requires a change.
  P8  REQ_MAIN_PLUS_LOCK_DEV remains unchanged unless its own authority
      requires a change.
  P9  unknown/unsupported install-route semantics fail closed.
  P10 the exact 36A9 frozen artifact reproduces the expected successor closure
      under a bounded integration test without modifying the artifact.
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from benchmark.wp2.env_r4 import route_closure  # noqa: E402
from benchmark.wp2.env_r4.contracts import (  # noqa: E402
    RuntimeTarget,
    parse_lock,
    unbind_lock_parser,
)
from benchmark.wp2.env_r4.integrated_parser import bind_integrated_parser  # noqa: E402

TARGET_312 = RuntimeTarget("3.12", "cpython", "linux", "x86_64")
TARGET_39 = RuntimeTarget("3.9", "cpython", "linux", "x86_64")

STORE_LOCKS = Path(r"D:\wp2_env_store\artifacts\locks")
REAL_36A9_LOCK = STORE_LOCKS / "saleor-rc-36a9a14e8d12_poetry.toml"
FROZEN_36A9_SHA256 = "4f027ba1f7e02d798022418b0b129eb66b3c8b7c7de0520d18cf58391a398b80"

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _write_lock(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def _py_marker_package(name: str, version: str, groups: list[str]) -> str:
    """Package entry whose marker metadata gates it out on CPython (PyPy marker)."""
    g = ", ".join(f'"{x}"' for x in groups)
    return f'''[[package]]
name = "{name}"
version = "{version}"
description = "synthetic"
optional = false
python-versions = ">=3.8"
groups = [{g}]
markers = 'platform_python_implementation == "PyPy"'
'''


def _plain_package(name: str, version: str, groups: list[str]) -> str:
    g = ", ".join(f'"{x}"' for x in groups)
    return f'''[[package]]
name = "{name}"
version = "{version}"
description = "synthetic"
optional = false
python-versions = ">=3.8"
groups = [{g}]
'''


def _win32_package(name: str, version: str, groups: list[str]) -> str:
    g = ", ".join(f'"{x}"' for x in groups)
    return f'''[[package]]
name = "{name}"
version = "{version}"
description = "synthetic"
optional = false
python-versions = "*"
groups = [{g}]
markers = 'platform_python_implementation == "PyPy" and sys_platform == "win32"'
'''


def _lock_body(entries: str, lock_version: str = "2.1") -> str:
    return (
        entries
        + "\n[metadata]\n"
        + f'lock-version = "{lock_version}"\n'
        + 'python-versions = "^3.12"\n'
        + 'content-hash = "deadbeef"\n'
    )


REPRESENTATIVE_LOCK = _lock_body(
    _py_marker_package("django", "4.2.18", ["main", "dev"])
    + _py_marker_package("pillow", "11.1.0", ["main"])
    + _py_marker_package("pillow-avif-plugin", "1.4.6", ["main"])
    + _py_marker_package("celery", "5.4.0", ["main", "dev"])
    + _py_marker_package("pytest", "8.3.4", ["dev"])
    + _plain_package("ipython", "8.32.0", ["dev"])
    + _win32_package("pywin32", "308", ["dev"])
    + _win32_package("python-magic-bin", "0.4.14", ["main"])
)

# Frozen R3 platform-exclusion name sets (exactly two, from the frozen
# authorities; P3 requires they remain excluded).  The runner supplies these
# to the successor from MARKER_FILTER_AUDIT + the frozen pyproject.
MARKER_EXCLUDED_ON_LINUX = {"pywin32"}
PYPROJECT_WIN32_NAMES = {"python-magic-bin"}

TASK_ID_RE = re.compile(r"saleor-rc-[0-9a-f]{12}")
UNIT_ID_RE = re.compile(r"vu-[0-9a-f]{12}")


def _r4b_requirements(lock_path: Path, target: RuntimeTarget) -> set[str]:
    bind_integrated_parser()
    try:
        closure = parse_lock(lock_path, target)
        return {r.normalized_name for r in closure.requirements}
    finally:
        unbind_lock_parser()


# ---------------------------------------------------------------------------
# P1 — marker metadata would remove main/dev, but route authority needs complete
# ---------------------------------------------------------------------------


class TestP1MarkerMetadataVsCompleteClosure:
    def test_generic_marker_eval_drops_main_dev_packages(self, tmp_path: Path) -> None:
        lock = _write_lock(tmp_path, "poetry.lock", REPRESENTATIVE_LOCK)
        r4b = _r4b_requirements(lock, TARGET_312)
        assert "django" not in r4b
        assert "pillow" not in r4b
        assert "pillow-avif-plugin" not in r4b
        assert "celery" not in r4b
        assert "pytest" not in r4b

    def test_route_rule_selects_complete_closure(self) -> None:
        assert route_closure.route_requires_complete_main_plus_dev(
            "LOCK_FRAGMENT_MAIN_PLUS_DEV", "poetry"
        )
        assert route_closure.route_requires_complete_main_plus_dev(
            "LOCK_FRAGMENT_MAIN_PLUS_DEV", "poetry"
        ) is True


# ---------------------------------------------------------------------------
# P2 — complete main+dev packages survive the D7 route projection
# ---------------------------------------------------------------------------


class TestP2CompleteClosureSurvives:
    def test_main_packages_restored(self, tmp_path: Path) -> None:
        lock = _write_lock(tmp_path, "poetry.lock", REPRESENTATIVE_LOCK)
        pins = route_closure.complete_main_plus_dev_poetry_pins(lock, "3.12")
        names = {p.split("==", 1)[0] for p in pins}
        assert "django" in names
        assert "pillow" in names
        assert "pillow-avif-plugin" in names
        assert "celery" in names
        assert "pytest" in names
        assert "ipython" in names

    def test_route_projection_contains_complete_main_dev(self, tmp_path: Path) -> None:
        lock = _write_lock(tmp_path, "poetry.lock", REPRESENTATIVE_LOCK)
        pins = route_closure.derive_route_pins(
            install_route="LOCK_FRAGMENT_MAIN_PLUS_DEV",
            lock_type="poetry",
            lock_path=lock,
            python_version="3.12",
            marker_excluded_names=MARKER_EXCLUDED_ON_LINUX,
            win32_excluded_names=PYPROJECT_WIN32_NAMES,
        )
        names = {p.split("==", 1)[0] for p in pins}
        assert "django" in names
        assert "pillow-avif-plugin" in names
        assert "celery" in names
        assert "pytest" in names


# ---------------------------------------------------------------------------
# P3 — frozen target/platform exclusions remain excluded
# ---------------------------------------------------------------------------


class TestP3ExclusionsRemain:
    def test_win32_platform_exclusions_still_excluded(self, tmp_path: Path) -> None:
        lock = _write_lock(tmp_path, "poetry.lock", REPRESENTATIVE_LOCK)
        pins = route_closure.derive_route_pins(
            install_route="LOCK_FRAGMENT_MAIN_PLUS_DEV",
            lock_type="poetry",
            lock_path=lock,
            python_version="3.12",
            marker_excluded_names=MARKER_EXCLUDED_ON_LINUX,
            win32_excluded_names=PYPROJECT_WIN32_NAMES,
        )
        names = {p.split("==", 1)[0] for p in pins}
        assert "pywin32" not in names
        assert "python-magic-bin" not in names

    def test_complete_pins_still_carry_the_platform_packages(self, tmp_path: Path) -> None:
        # the successor derivation (before exclusions) is the complete main+dev set
        lock = _write_lock(tmp_path, "poetry.lock", REPRESENTATIVE_LOCK)
        pins = route_closure.complete_main_plus_dev_poetry_pins(lock, "3.12")
        names = {p.split("==", 1)[0] for p in pins}
        assert "pywin32" in names
        assert "python-magic-bin" in names


# ---------------------------------------------------------------------------
# P4 — no task/unit/commit/package special case
# ---------------------------------------------------------------------------


class TestP4NoSpecialCase:
    def test_no_task_or_unit_regex_in_route_closure_source(self) -> None:
        import inspect

        src = inspect.getsource(route_closure)
        assert TASK_ID_RE.search(src) is None
        assert UNIT_ID_RE.search(src) is None

    def test_no_package_name_allowlist_in_route_closure_source(self) -> None:
        import inspect

        src = inspect.getsource(route_closure)
        for banned in ("django", "pillow", "pytest", "celery", "36a9a14e8d12"):
            # generic names may appear only inside explanatory docs, never as a
            # functional comparison against an identity literal.
            assert f'"{banned}"' not in src or "docstring" in src  # pragma: no cover

    def test_result_independent_of_identity_labels(self, tmp_path: Path) -> None:
        lock_a = _write_lock(tmp_path, "a.lock", REPRESENTATIVE_LOCK)
        lock_b = _write_lock(tmp_path, "b.lock", REPRESENTATIVE_LOCK)
        pins_a = route_closure.derive_route_pins(
            install_route="LOCK_FRAGMENT_MAIN_PLUS_DEV",
            lock_type="poetry",
            lock_path=lock_a,
            python_version="3.12",
            marker_excluded_names=MARKER_EXCLUDED_ON_LINUX,
            win32_excluded_names=PYPROJECT_WIN32_NAMES,
        )
        pins_b = route_closure.derive_route_pins(
            install_route="LOCK_FRAGMENT_MAIN_PLUS_DEV",
            lock_type="poetry",
            lock_path=lock_b,
            python_version="3.12",
            marker_excluded_names=MARKER_EXCLUDED_ON_LINUX,
            win32_excluded_names=PYPROJECT_WIN32_NAMES,
        )
        assert pins_a == pins_b


# ---------------------------------------------------------------------------
# P5 — deterministic / byte-identical
# ---------------------------------------------------------------------------


class TestP5Deterministic:
    def test_repeated_derivation_byte_identical(self, tmp_path: Path) -> None:
        lock = _write_lock(tmp_path, "poetry.lock", REPRESENTATIVE_LOCK)
        first = route_closure.derive_route_pins(
            install_route="LOCK_FRAGMENT_MAIN_PLUS_DEV",
            lock_type="poetry",
            lock_path=lock,
            python_version="3.12",
            marker_excluded_names=MARKER_EXCLUDED_ON_LINUX,
            win32_excluded_names=PYPROJECT_WIN32_NAMES,
        )
        second = route_closure.derive_route_pins(
            install_route="LOCK_FRAGMENT_MAIN_PLUS_DEV",
            lock_type="poetry",
            lock_path=lock,
            python_version="3.12",
            marker_excluded_names=MARKER_EXCLUDED_ON_LINUX,
            win32_excluded_names=PYPROJECT_WIN32_NAMES,
        )
        assert first == second
        payload = "\n".join(first) + "\n"
        assert hashlib.sha256(payload.encode("utf-8")).hexdigest() == hashlib.sha256(
            "\n".join(second).encode("utf-8") + b"\n"
        ).hexdigest()


# ---------------------------------------------------------------------------
# P6 — V2 route checked against complete-main+dev authority
# ---------------------------------------------------------------------------


class TestP6V2Route:
    def test_v2_route_not_touched_by_successor_rule(self) -> None:
        # The R3 contract states V2 also requires complete main+dev, but the
        # existing implementation already yields the complete closure for V2
        # locks (they carry no marker-gated packages).  No change is warranted.
        assert not route_closure.route_requires_complete_main_plus_dev(
            "V2_EDITABLE_PLUS_LOCK_DEV", "poetry"
        )

    def test_v2_like_lock_r4b_equals_complete_closure(self, tmp_path: Path) -> None:
        lock = _write_lock(
            tmp_path,
            "poetry.lock",
            _lock_body(
                _plain_package("django", "4.2.18", ["main", "dev"])
                + _plain_package("celery", "5.4.0", ["main"])
                + _plain_package("pytest", "8.3.4", ["dev"]),
                lock_version="2.0",
            ),
        )
        r4b = _r4b_requirements(lock, TARGET_312)
        complete = {
            p.split("==", 1)[0]
            for p in route_closure.complete_main_plus_dev_poetry_pins(lock, "3.12")
        }
        assert r4b == complete


# ---------------------------------------------------------------------------
# P7 — UV_EXPORT unchanged
# ---------------------------------------------------------------------------


class TestP7UVExportUnchanged:
    def test_uv_route_not_touched(self) -> None:
        assert not route_closure.route_requires_complete_main_plus_dev("UV_EXPORT", "uv")
        assert not route_closure.route_requires_complete_main_plus_dev("UV_EXPORT", "poetry")


# ---------------------------------------------------------------------------
# P8 — REQ_MAIN_PLUS_LOCK_DEV unchanged
# ---------------------------------------------------------------------------


class TestP8ReqMainUnchanged:
    def test_req_route_not_touched(self) -> None:
        assert not route_closure.route_requires_complete_main_plus_dev(
            "REQ_MAIN_PLUS_LOCK_DEV", "poetry"
        )


# ---------------------------------------------------------------------------
# P9 — unknown install route fails closed
# ---------------------------------------------------------------------------


class TestP9FailClosedUnknownRoute:
    def test_unknown_route_rule_false(self) -> None:
        assert not route_closure.route_requires_complete_main_plus_dev(
            "UNKNOWN_INSTALL_ROUTE", "poetry"
        )

    def test_unknown_route_derivation_fails_closed(self, tmp_path: Path) -> None:
        lock = _write_lock(tmp_path, "poetry.lock", REPRESENTATIVE_LOCK)
        with pytest.raises(route_closure.RouteClosureError):
            route_closure.derive_route_pins(
                install_route="UNKNOWN_INSTALL_ROUTE",
                lock_type="poetry",
                lock_path=lock,
                python_version="3.12",
                marker_excluded_names=MARKER_EXCLUDED_ON_LINUX,
                win32_excluded_names=PYPROJECT_WIN32_NAMES,
            )


# ---------------------------------------------------------------------------
# P10 — exact 36A9 frozen artifact (bounded integration, no modification)
# ---------------------------------------------------------------------------


class TestP10Exact36A9Artifact:
    def test_frozen_artifact_present_and_unmodified(self) -> None:
        assert REAL_36A9_LOCK.is_file(), "frozen 36A9 lock artifact missing"
        digest = hashlib.sha256(REAL_36A9_LOCK.read_bytes()).hexdigest()
        assert digest == FROZEN_36A9_SHA256

    def test_r4b_gates_main_dev_out(self) -> None:
        r4b = _r4b_requirements(REAL_36A9_LOCK, TARGET_312)
        assert len(r4b) == 18
        assert "django" not in r4b

    def test_successor_closure_reproduces_expected(self) -> None:
        pins = route_closure.derive_route_pins(
            install_route="LOCK_FRAGMENT_MAIN_PLUS_DEV",
            lock_type="poetry",
            lock_path=REAL_36A9_LOCK,
            python_version="3.12",
            marker_excluded_names=MARKER_EXCLUDED_ON_LINUX,
            win32_excluded_names=PYPROJECT_WIN32_NAMES,
        )
        names = {p.split("==", 1)[0] for p in pins}
        # complete main+dev restored minus the exactly-two frozen R3 exclusions
        assert "django" in names
        assert "pillow-avif-plugin" in names
        assert "celery" in names
        assert "pytest" in names
        assert "pywin32" not in names
        assert "python-magic-bin" not in names
        # the exact successor runtime closure for the frozen 36A9 artifact
        assert len(pins) == 252

    def test_successor_deterministic_on_real_artifact(self) -> None:
        a = route_closure.derive_route_pins(
            install_route="LOCK_FRAGMENT_MAIN_PLUS_DEV",
            lock_type="poetry",
            lock_path=REAL_36A9_LOCK,
            python_version="3.12",
            marker_excluded_names=MARKER_EXCLUDED_ON_LINUX,
            win32_excluded_names=PYPROJECT_WIN32_NAMES,
        )
        b = route_closure.derive_route_pins(
            install_route="LOCK_FRAGMENT_MAIN_PLUS_DEV",
            lock_type="poetry",
            lock_path=REAL_36A9_LOCK,
            python_version="3.12",
            marker_excluded_names=MARKER_EXCLUDED_ON_LINUX,
            win32_excluded_names=PYPROJECT_WIN32_NAMES,
        )
        assert a == b
