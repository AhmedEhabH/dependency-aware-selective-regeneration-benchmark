"""R4 I1 A+B composition tests — one composite LockParser behind the frozen interface.

Mission ``M17_D7_R4_I1_AB_COMPOSITION``.

These tests prove that after a single ``bind_integrated_parser()`` bind the one
frozen ``LockParser`` slot serves BOTH frozen entry points simultaneously:

* ``parse_lock``      -> R4-B ``EnvR4LockAdapter`` semantics (Poetry + uv).
* ``wheel_compatible`` -> R4-A era-aware wheel-tag semantics.

P2P: P1 unbound fail-closed, P2 exactly-one composite bind, P3 real Saleor uv
fixture parses, P4 closure identical to direct R4-B parsing, P5 era-aware wheel
compatibility, P6 alternating operations on one binding, P7 lock fail-closed,
P8 wheel fail-closed, P9 deterministic repeated parsing, P10 unbind restores
fail-closed.

F2P: no parser bound / malformed lock / unknown lock source / malformed wheel /
wrong era or platform wheel all fail closed.
"""
from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

import pytest

from benchmark.wp2.env_r4 import contracts as _contracts
from benchmark.wp2.env_r4.contracts import (
    LockClosure,
    LockParseError,
    RuntimeTarget,
    parse_lock,
    unbind_lock_parser,
    wheel_compatible,
)
from benchmark.wp2.env_r4.integrated_parser import (
    IntegratedR4Parser,
    bind_integrated_parser,
)
from benchmark.wp2.env_r4.uv_adapter import EnvR4LockAdapter

PROJECT_DIR = Path(__file__).resolve().parents[4]
REAL_UV_LOCK = (
    PROJECT_DIR
    / "research"
    / "env-canon-r4"
    / "fixtures"
    / "saleor-3.23.0-uv.lock"
)

T38 = RuntimeTarget(
    python_version="3.8",
    implementation="cpython",
    platform="linux",
    architecture="x86_64",
)
T39 = RuntimeTarget(
    python_version="3.9",
    implementation="cpython",
    platform="linux",
    architecture="x86_64",
)
T312 = RuntimeTarget(
    python_version="3.12",
    implementation="cpython",
    platform="linux",
    architecture="x86_64",
)


def _write(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def _names(closure: LockClosure) -> set[str]:
    return {r.normalized_name for r in closure.requirements}


@pytest.fixture(autouse=True)
def _isolate_binding() -> Iterator[None]:
    unbind_lock_parser()
    yield
    unbind_lock_parser()


class TestP1UnboundFailClosed:
    def test_unbound_parse_lock_fails_closed(self, tmp_path: Path) -> None:
        with pytest.raises(LockParseError):
            parse_lock(tmp_path / "uv.lock", T312)

    def test_unbound_wheel_compatible_fails_closed(self) -> None:
        with pytest.raises(LockParseError):
            wheel_compatible("pkg-1.0-py3-none-any.whl", T312)


class TestP2SingleCompositeBind:
    def test_one_composite_parser_bound(self) -> None:
        bind_integrated_parser()
        try:
            parser = _contracts._lock_parser
            assert parser is not None
            assert isinstance(parser, IntegratedR4Parser)
            assert parser is _contracts._lock_parser
        finally:
            unbind_lock_parser()

    def test_both_entry_points_work_after_single_bind(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            "version = 1\n"
            "[[package]]\n"
            "name = 'requests'\n"
            "version = '2.32.3'\n"
            "source = { registry = 'https://pypi.org/simple' }\n",
        )
        bind_integrated_parser()
        try:
            closure = parse_lock(lock, T312)
            assert closure.lock_format == "uv"
            assert "requests" in _names(closure)
            assert wheel_compatible("pkg-1.0-cp312-cp312-linux_x86_64.whl", T312) is True
        finally:
            unbind_lock_parser()


class TestSaleorRealFixture:
    def test_p3_parse_lock_succeeds_and_preserves_r4b_result(self) -> None:
        assert REAL_UV_LOCK.is_file()
        bind_integrated_parser()
        try:
            closure = parse_lock(REAL_UV_LOCK, T312)
        finally:
            unbind_lock_parser()
        assert closure.is_valid
        assert closure.lock_format == "uv"
        assert len(closure.requirements) == 230
        assert closure.editable_self is not None
        assert closure.editable_self.normalized_name == "saleor"
        excluded = {r.normalized_name for r in closure.exclusions}
        assert excluded == {"python-magic-bin", "pywin32"}

    def test_p4_closure_identical_to_direct_r4b(self) -> None:
        bind_integrated_parser()
        try:
            composed = parse_lock(REAL_UV_LOCK, T312)
        finally:
            unbind_lock_parser()
        direct = EnvR4LockAdapter().parse_lock(REAL_UV_LOCK, T312)
        assert composed.to_canonical_dict() == direct.to_canonical_dict()
        assert composed.freeze_sha256() == direct.freeze_sha256()

    def test_p9_repeated_parsing_is_deterministic(self) -> None:
        bind_integrated_parser()
        try:
            first = parse_lock(REAL_UV_LOCK, T312)
            second = parse_lock(REAL_UV_LOCK, T312)
        finally:
            unbind_lock_parser()
        assert first.to_canonical_dict() == second.to_canonical_dict()
        assert first.freeze_sha256() == second.freeze_sha256()


class TestP5WheelCompatibleEras:
    @pytest.mark.parametrize("target", [T38, T39, T312])
    def test_pure_python_wheel_accepted_across_all_eras(self, target: RuntimeTarget) -> None:
        bind_integrated_parser()
        try:
            assert wheel_compatible("pkg-1.0-py3-none-any.whl", target) is True
            assert wheel_compatible("pkg-1.0-py2.py3-none-any.whl", target) is True
        finally:
            unbind_lock_parser()

    def test_cp38_era_wheel_only_for_cp38(self) -> None:
        bind_integrated_parser()
        try:
            assert wheel_compatible("pkg-1.0-cp38-cp38-linux_x86_64.whl", T38) is True
            assert wheel_compatible("pkg-1.0-cp38-cp38-linux_x86_64.whl", T39) is False
            assert wheel_compatible("pkg-1.0-cp38-cp38-linux_x86_64.whl", T312) is False
        finally:
            unbind_lock_parser()

    def test_abi3_wheel_accepted(self) -> None:
        bind_integrated_parser()
        try:
            assert wheel_compatible("pkg-1.0-cp38-abi3-manylinux_2_17_x86_64.whl", T38) is True
            assert wheel_compatible("pkg-1.0-cp312-abi3-manylinux_2_17_x86_64.whl", T312) is True
        finally:
            unbind_lock_parser()

    def test_representative_r3_real_artifacts(self) -> None:
        bind_integrated_parser()
        try:
            assert wheel_compatible("bcrypt-4.2.1-cp37-abi3-manylinux_2_17_x86_64.whl", T312) is True
            assert wheel_compatible("deptry-0.21.2-cp39-abi3-manylinux_2_17_x86_64.whl", T312) is True
            assert wheel_compatible("pyxb-1.2.5-py3-none-any.whl", T312) is True
        finally:
            unbind_lock_parser()


class TestP6AlternatingOperations:
    def test_parse_wheel_parse_wheel_on_same_binding(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            "version = 1\n"
            "[[package]]\n"
            "name = 'requests'\n"
            "version = '2.32.3'\n"
            "source = { registry = 'https://pypi.org/simple' }\n",
        )
        bind_integrated_parser()
        try:
            first = parse_lock(lock, T312)
            assert first.is_valid
            assert wheel_compatible("pkg-1.0-cp312-cp312-linux_x86_64.whl", T312) is True
            second = parse_lock(lock, T312)
            assert second.to_canonical_dict() == first.to_canonical_dict()
            assert wheel_compatible("pkg-1.0-py3-none-any.whl", T312) is True
            assert wheel_compatible("pkg-1.0-cp39-cp39-linux_x86_64.whl", T312) is False
        finally:
            unbind_lock_parser()


class TestP7LockFailClosed:
    def test_malformed_lock_fails_closed(self, tmp_path: Path) -> None:
        lock = _write(tmp_path, "uv.lock", "version = 1\n[[package]]\nname = ")
        bind_integrated_parser()
        try:
            with pytest.raises(LockParseError):
                parse_lock(lock, T312)
        finally:
            unbind_lock_parser()

    def test_unsupported_source_fails_closed(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            "version = 1\n"
            "[[package]]\n"
            "name = 'mystery'\n"
            "version = '1.0'\n"
            "source = { git = { url = 'https://github.com/x/y' } }\n",
        )
        bind_integrated_parser()
        try:
            with pytest.raises(LockParseError):
                parse_lock(lock, T312)
        finally:
            unbind_lock_parser()

    def test_unsupported_lock_format_fails_closed(self, tmp_path: Path) -> None:
        lock = _write(tmp_path, "uv.lock", "not a lock file")
        bind_integrated_parser()
        try:
            with pytest.raises(LockParseError):
                parse_lock(lock, T312)
        finally:
            unbind_lock_parser()

    def test_requires_python_rejects_target_fails_closed(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            'version = 1\n'
            'requires-python = ">=3.12,<3.13"\n'
            '[[package]]\n'
            'name = "django"\n'
            'version = "5.2.13"\n'
            'source = { registry = "https://pypi.org/simple" }\n',
        )
        bind_integrated_parser()
        try:
            with pytest.raises(LockParseError):
                parse_lock(lock, T39)
        finally:
            unbind_lock_parser()


class TestP8WheelFailClosed:
    @pytest.mark.parametrize(
        "name",
        [
            "",
            "   ",
            "notawheel",
            "pkg-1.0.whl",
            "pkg-1.0-py3-none-any.tar.gz",
            "pkg-1.0-py3-none-any",
            "pkg-1.0-cp312-cp312-linux_x86_64",
        ],
    )
    def test_malformed_wheel_fails_closed(self, name: str) -> None:
        bind_integrated_parser()
        try:
            assert wheel_compatible(name, T312) is False
        finally:
            unbind_lock_parser()

    def test_wrong_era_and_platform_rejected(self) -> None:
        bind_integrated_parser()
        try:
            assert wheel_compatible("pkg-1.0-cp39-cp39-linux_x86_64.whl", T312) is False
            assert wheel_compatible("pkg-1.0-cp312-cp312-win_amd64.whl", T312) is False
            assert wheel_compatible("pkg-1.0-cp312-cp312-macosx_11_0_arm64.whl", T312) is False
            assert wheel_compatible("pkg-1.0-cp312-cp312-linux_aarch64.whl", T312) is False
        finally:
            unbind_lock_parser()


class TestP10UnbindRestoresFailClosed:
    def test_unbind_parse_lock_fails_closed_after_bind(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            "version = 1\n"
            "[[package]]\n"
            "name = 'requests'\n"
            "version = '2.32.3'\n"
            "source = { registry = 'https://pypi.org/simple' }\n",
        )
        bind_integrated_parser()
        try:
            assert parse_lock(lock, T312).is_valid
        finally:
            unbind_lock_parser()
        with pytest.raises(LockParseError):
            parse_lock(lock, T312)

    def test_unbind_wheel_compatible_fails_closed_after_bind(self) -> None:
        bind_integrated_parser()
        try:
            assert wheel_compatible("pkg-1.0-py3-none-any.whl", T312) is True
        finally:
            unbind_lock_parser()
        with pytest.raises(LockParseError):
            wheel_compatible("pkg-1.0-py3-none-any.whl", T312)


class TestF2PComposition:
    """F2P: invalid/mutated inputs must fail closed through the composite."""

    def test_no_parser_bound_fails_closed(self, tmp_path: Path) -> None:
        with pytest.raises(LockParseError):
            parse_lock(tmp_path / "uv.lock", T312)
        with pytest.raises(LockParseError):
            wheel_compatible("pkg-1.0-py3-none-any.whl", T312)

    def test_malformed_lock_fails_closed(self, tmp_path: Path) -> None:
        lock = _write(tmp_path, "uv.lock", "version = 1\n[[package]]\nname = ")
        bind_integrated_parser()
        try:
            with pytest.raises(LockParseError):
                parse_lock(lock, T312)
        finally:
            unbind_lock_parser()

    @pytest.mark.parametrize(
        "source_line",
        [
            'source = { git = { url = "https://github.com/x/y" } }',
            'source = { url = "https://example.com/x.tar.gz" }',
            'source = { editable = "../local" }',
        ],
    )
    def test_unknown_lock_source_fails_closed(
        self, tmp_path: Path, source_line: str
    ) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            f"version = 1\n[[package]]\nname = 'mystery'\nversion = '1.0'\n{source_line}\n",
        )
        bind_integrated_parser()
        try:
            with pytest.raises(LockParseError):
                parse_lock(lock, T312)
        finally:
            unbind_lock_parser()

    @pytest.mark.parametrize(
        "name",
        ["", "notawheel", "pkg-1.0.whl", "pkg-1.0-py3-none-any", "pkg-1.0-py3-none-any.tar.gz"],
    )
    def test_malformed_wheel_filename_fails_closed(self, name: str) -> None:
        bind_integrated_parser()
        try:
            assert wheel_compatible(name, T312) is False
        finally:
            unbind_lock_parser()

    def test_wrong_era_or_platform_wheel_fails_closed(self) -> None:
        bind_integrated_parser()
        try:
            assert wheel_compatible("pkg-1.0-cp39-cp39-linux_x86_64.whl", T312) is False
            assert wheel_compatible("pkg-1.0-cp312-cp312-win_amd64.whl", T312) is False
            assert wheel_compatible("pkg-1.0-cp312-cp312-linux_aarch64.whl", T312) is False
        finally:
            unbind_lock_parser()


class TestNoTaskIdSpecialCase:
    def test_composition_source_has_no_task_id_branch(self) -> None:
        import inspect

        source = inspect.getsource(IntegratedR4Parser) + inspect.getsource(bind_integrated_parser)
        assert re.search(r"saleor-rc-[0-9a-f]{12}", source) is None

    def test_task_id_named_package_parsed_generically(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            "version = 1\n"
            "[[package]]\n"
            "name = 'saleor-rc-19bb9b070965'\n"
            "version = '1.0'\n"
            "source = { registry = 'https://pypi.org/simple' }\n",
        )
        bind_integrated_parser()
        try:
            closure = parse_lock(lock, T312)
            assert "saleor-rc-19bb9b070965" in _names(closure)
        finally:
            unbind_lock_parser()


class TestDelegationIntact:
    def test_parse_lock_delegates_to_r4b_not_duplicated(self, tmp_path: Path) -> None:
        import inspect

        source = inspect.getsource(IntegratedR4Parser.parse_lock)
        assert "EnvR4LockAdapter" in source or "_lock_adapter" in source

    def test_wheel_compatible_delegates_to_r4a_engine(self) -> None:
        import inspect

        source = inspect.getsource(IntegratedR4Parser.wheel_compatible)
        assert "wheel_compatible" in source

    def test_p2p_wheel_results_equal_direct_r4a(self) -> None:
        from benchmark.wp2.env_r4 import wheel_tags

        names = [
            "pkg-1.0-py3-none-any.whl",
            "pkg-1.0-cp38-cp38-linux_x86_64.whl",
            "pkg-1.0-cp39-cp39-linux_x86_64.whl",
            "pkg-1.0-cp312-cp312-linux_x86_64.whl",
            "pkg-1.0-cp312-cp312-win_amd64.whl",
            "pkg-1.0-cp38-abi3-manylinux_2_17_x86_64.whl",
            "notawheel",
        ]
        bind_integrated_parser()
        try:
            for name in names:
                assert wheel_compatible(name, T312) is wheel_tags.wheel_compatible(name, T312)
        finally:
            unbind_lock_parser()


