"""M17_D7_R4_PHASE1B - GENERAL declared-but-unlocked pin rule P2P/F2P tests.

Mission ``M17_D7_R4_PHASE1B_SCIENTIFIC_SUCCESSOR_RESOLUTION_REPAIR`` (TASK A/E).

Owner decision #1 (GENERAL declared-but-unlocked rule): at the exact historical
commit, if a package is a direct dependency declared by pyproject.toml, has an
exact ``name==version`` pin in an authoritative same-commit requirements file,
and is absent from poetry.lock, then that exact pin is added to the runtime pin
set.

The rule is implemented in ``benchmark.wp2.env_r4.route_closure`` and exercised
generically (no unit / commit / package literals in logic).  These tests verify:

P2P:
  P1  declared + exact-pinned + absent-from-lock package is injected exactly.
  P2  the real posuto predicate reproduces the Phase-1A hit.
  P3  case-insensitive name canonicalization.
  P4  ``-`` vs ``_`` name normalization.
  P5  PEP 503 canonicalization (``normalize_name``) is used, no second helper.

F2P:
  F1  dependency not declared -> decline injection.
  F2  no exact same-commit pin (range only) -> decline injection.
  F3  conflicting exact pins -> decline injection (never pick a version).
  F4  already present in lock -> decline injection (lock-authoritative).
  F5  malformed dependency authority (bad TOML) -> fail closed.
  F6  malformed requirements line -> fail closed.
  F7  unsupported requirements expression -> decline injection.
  F8  inferred rather than explicit version -> decline injection.
  F9  ordinary lock-complete commit stays lock-authoritative and unchanged.
  F10 ambiguous canonical package-name match -> decline injection.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from benchmark.wp2.env_r4 import route_closure  # noqa: E402
from benchmark.wp2.env_r4.contracts import normalize_name  # noqa: E402

TASK_ID_RE = re.compile(r"saleor-rc-[0-9a-f]{12}")
UNIT_ID_RE = re.compile(r"vu-[0-9a-f]{12}")


def _rule(*, lock: set[str], pyproject: str, reqs: dict[str, str]) -> list[str]:
    return route_closure.declared_exact_pin_but_unlocked_pins(
        lock_pin_names=lock,
        pyproject_toml=pyproject,
        requirements_texts=reqs,
    )


POSUTO_PYPROJECT = (
    '[tool.poetry]\nname = "saleor"\n'
    "[tool.poetry.dependencies]\npython = \"~3.9\"\n"
    'posuto = "^2021.10.0"\ndjango = "^3.2"\n'
)
POSUTO_REQS = {
    "requirements.txt": "django==3.2.12\nposuto==2021.10.0\n",
    "requirements_dev.txt": "posuto==2021.10.0\n",
}
POSUTO_LOCK = {"django", "celery", "pytest"}


class TestP2P:
    def test_p1_declared_pinned_unlocked_injected_exactly(self) -> None:
        pins = _rule(lock=POSUTO_LOCK, pyproject=POSUTO_PYPROJECT, reqs=POSUTO_REQS)
        assert pins == ["posuto==2021.10.0"]

    def test_p2_real_posuto_predicate_reproduces_phase1a_hit(self) -> None:
        pins = _rule(lock=POSUTO_LOCK, pyproject=POSUTO_PYPROJECT, reqs=POSUTO_REQS)
        assert pins == ["posuto==2021.10.0"]
        assert len(pins) == 1

    def test_p3_case_insensitive_names(self) -> None:
        pyproj = '[tool.poetry.dependencies]\nFoo = "^1.0"\n'
        pins = _rule(lock=set(), pyproject=pyproj, reqs={"requirements.txt": "foo==1.0\n"})
        assert pins == ["foo==1.0"]

    def test_p4_dash_vs_underscore(self) -> None:
        pyproj = '[tool.poetry.dependencies]\nFoo_Bar = "^1.0"\n'
        pins = _rule(lock=set(), pyproject=pyproj, reqs={"requirements.txt": "foo-bar==1.0\n"})
        assert pins == ["foo-bar==1.0"]

    def test_p5_uses_existing_normalize_name_helper(self) -> None:
        assert normalize_name("Foo_Bar") == "foo-bar"
        import inspect

        src = inspect.getsource(route_closure)
        assert "normalize_name" in src


class TestF2P:
    def test_f1_not_declared_declines(self) -> None:
        pyproj = '[tool.poetry.dependencies]\ndjango = "^3.2"\n'
        pins = _rule(lock=set(), pyproject=pyproj, reqs={"requirements.txt": "posuto==2021.10.0\n"})
        assert pins == []

    def test_f2_no_exact_pin_declines(self) -> None:
        pins = _rule(
            lock=set(),
            pyproject=POSUTO_PYPROJECT,
            reqs={"requirements.txt": "posuto>=2021.10.0\n"},
        )
        assert pins == []

    def test_f3_conflicting_exact_pins_declines_injection(self) -> None:
        # Mission F2P: "Must fail closed OR decline injection" for conflicting
        # exact pins.  Real historical data contains cross-file conflicts
        # (e.g. azure-core 1.29.1 vs 1.29.2); the general rule declines so the
        # conflict can never silently pick a version.
        pins = _rule(
            lock=set(),
            pyproject=POSUTO_PYPROJECT,
            reqs={
                "requirements.txt": "posuto==2021.10.0\n",
                "requirements_dev.txt": "posuto==2022.1.0\n",
            },
        )
        assert pins == []

    def test_f4_already_present_in_lock_declines(self) -> None:
        pins = _rule(
            lock={"posuto", "django", "celery"},
            pyproject=POSUTO_PYPROJECT,
            reqs=POSUTO_REQS,
        )
        assert pins == []

    def test_f5_malformed_pyproject_fails_closed(self) -> None:
        with pytest.raises(route_closure.DeclaredPinRuleError):
            _rule(
                lock=set(),
                pyproject="[tool.poetry.dependencies\nnot = valid\n",
                reqs={"requirements.txt": "posuto==2021.10.0\n"},
            )

    def test_f6_malformed_requirements_line_fails_closed(self) -> None:
        with pytest.raises(route_closure.DeclaredPinRuleError):
            _rule(
                lock=set(),
                pyproject=POSUTO_PYPROJECT,
                reqs={"requirements.txt": "posuto==2021.10.0\n@@garbage@@\n"},
            )

    def test_f7_unsupported_expression_declines(self) -> None:
        pins = _rule(
            lock=set(),
            pyproject=POSUTO_PYPROJECT,
            reqs={"requirements.txt": "posuto~=2021.10.0\n"},
        )
        assert pins == []

    def test_f8_inferred_version_declines(self) -> None:
        pins = _rule(
            lock=set(),
            pyproject=POSUTO_PYPROJECT,
            reqs={"requirements.txt": "posuto\n"},
        )
        assert pins == []

    def test_f9_ordinary_lock_complete_commit_unchanged(self) -> None:
        pyproj = '[tool.poetry.dependencies]\ndjango = "^3.2"\n'
        pins = _rule(
            lock={"django"},
            pyproject=pyproj,
            reqs={"requirements.txt": "django==3.2.12\n"},
        )
        assert pins == []

    def test_f10_ambiguous_canonical_match_declines_injection(self) -> None:
        # Mission F2P: "Must fail closed OR decline injection" for ambiguous
        # canonical package-name matches.  Conflicting pins for the same
        # canonical name are declined (never silently resolved).
        pyproj = '[tool.poetry.dependencies]\nFoo_Bar = "^1.0"\n'
        pins = _rule(
            lock=set(),
            pyproject=pyproj,
            reqs={
                "requirements.txt": "foo-bar==1.0\n",
                "requirements_dev.txt": "foo_bar==2.0\n",
            },
        )
        assert pins == []


class TestGeneralRuleHygiene:
    def test_no_task_or_unit_literal_in_rule(self) -> None:
        import inspect

        src = inspect.getsource(route_closure)
        assert TASK_ID_RE.search(src) is None
        assert UNIT_ID_RE.search(src) is None

    def test_no_commit_sha_literal_in_rule(self) -> None:
        import inspect

        src = inspect.getsource(route_closure)
        assert "484ce881" not in src

    def test_no_package_name_literal_in_logic(self) -> None:
        import inspect

        src = inspect.getsource(route_closure)
        # strip docstrings/comments; 'posuto' must not appear in logic
        stripped = re.sub(r'""".*?"""', "", src, flags=re.S)
        assert "posuto" not in stripped
