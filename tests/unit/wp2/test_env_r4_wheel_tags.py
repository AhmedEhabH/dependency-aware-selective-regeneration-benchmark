"""R4-A era-aware wheel-tag compatibility tests (P2P / F2P + predecessor parity).

Mission: ``M17_D7_R4_A_ERA_AWARE_WHEEL_TAGS``.

These tests exercise the Track A implementation behind the frozen R4 shared
interface (``benchmark.wp2.env_r4.wheel_tags``) for the Full-D7 historical
targets (CPython 3.8 / 3.9 / 3.12, Linux x86_64).  They never modify the frozen
interface.
"""
from __future__ import annotations

import sys

import pytest

from benchmark.wp2.env_r4 import wheel_tags
from benchmark.wp2.env_r4.contracts import LockParseError, RuntimeTarget, unbind_lock_parser


def _target(
    version: str,
    implementation: str = "cpython",
    platform: str = "linux",
    architecture: str = "x86_64",
) -> RuntimeTarget:
    return RuntimeTarget(
        python_version=version,
        implementation=implementation,
        platform=platform,
        architecture=architecture,
    )


T38 = _target("3.8")
T39 = _target("3.9")
T312 = _target("3.12")


class TestP2P:
    """Valid inputs must pass (P1-P7)."""

    def test_p1_cp38_matches_cpython38_linux_x86_64(self) -> None:
        assert wheel_tags.wheel_compatible("pkg-1.0-cp38-cp38-linux_x86_64.whl", T38) is True

    def test_p2_cp39_matches_cpython39_linux_x86_64(self) -> None:
        assert wheel_tags.wheel_compatible("pkg-1.0-cp39-cp39-linux_x86_64.whl", T39) is True

    def test_p3_cp312_matches_cpython312_linux_x86_64(self) -> None:
        assert wheel_tags.wheel_compatible("pkg-1.0-cp312-cp312-linux_x86_64.whl", T312) is True

    @pytest.mark.parametrize("target", [T38, T39, T312])
    def test_p4_pure_python_wheel_accepted(self, target: RuntimeTarget) -> None:
        assert wheel_tags.wheel_compatible("pkg-1.0-py3-none-any.whl", target) is True
        assert wheel_tags.wheel_compatible("pkg-1.0-py2.py3-none-any.whl", target) is True

    @pytest.mark.parametrize("wheel", ["cp38", "cp39", "cp310", "cp311"])
    def test_p5_stable_abi_wheel_accepted_for_later_cpython(self, wheel: str) -> None:
        name = f"pkg-1.0-{wheel}-abi3-manylinux_2_17_x86_64.whl"
        assert wheel_tags.wheel_compatible(name, T312) is True

    def test_p6_deterministic_across_repeated_calls(self) -> None:
        name = "pkg-1.0-cp39-cp39-manylinux_2_17_x86_64.whl"
        first = wheel_tags.wheel_compatible(name, T39)
        for _ in range(5):
            assert wheel_tags.wheel_compatible(name, T39) is first
        # A cold cache must reproduce the identical verdict.
        wheel_tags._target_supported_tags.cache_clear()
        assert wheel_tags.wheel_compatible(name, T39) is first

    def test_p7_result_depends_on_target_not_host(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import packaging.tags as ptag

        def _boom(*_args: object, **_kwargs: object) -> object:
            raise AssertionError("host tag helper must not be consulted")

        # Force recomputation so the host-helper guards are actually exercised.
        wheel_tags._target_supported_tags.cache_clear()
        monkeypatch.setattr(ptag, "platform_tags", _boom)
        monkeypatch.setattr(ptag, "_cpython_abis", _boom)
        monkeypatch.setattr(sys, "version_info", (3, 7, 0, "final", 0))
        monkeypatch.setattr(sys, "version", "3.7.0")

        name = "pkg-1.0-cp38-cp38-linux_x86_64.whl"
        assert wheel_tags.wheel_compatible(name, T38) is True
        assert wheel_tags.wheel_compatible(name, T312) is False
        wheel_tags._target_supported_tags.cache_clear()


class TestF2P:
    """Invalid inputs must fail closed (F1-F7)."""

    def test_f1_cp39_rejected_for_cpython312(self) -> None:
        assert wheel_tags.wheel_compatible("pkg-1.0-cp39-cp39-linux_x86_64.whl", T312) is False

    def test_f2_cp38_rejected_for_cpython39(self) -> None:
        assert wheel_tags.wheel_compatible("pkg-1.0-cp38-cp38-linux_x86_64.whl", T39) is False

    def test_f3_windows_wheel_rejected_for_linux_target(self) -> None:
        for name in (
            "pkg-1.0-cp38-cp38-win_amd64.whl",
            "pkg-1.0-cp312-cp312-win32.whl",
        ):
            assert wheel_tags.wheel_compatible(name, T312) is False

    def test_f4_macos_wheel_rejected_for_linux_target(self) -> None:
        for name in (
            "pkg-1.0-cp38-cp38-macosx_10_9_x86_64.whl",
            "pkg-1.0-cp312-cp312-macosx_11_0_arm64.whl",
        ):
            assert wheel_tags.wheel_compatible(name, T312) is False

    def test_f5_wrong_architecture_rejected(self) -> None:
        for name in (
            "pkg-1.0-cp312-cp312-linux_aarch64.whl",
            "pkg-1.0-cp312-cp312-manylinux_2_17_aarch64.whl",
            "pkg-1.0-cp312-cp312-manylinux_2_17_i686.whl",
        ):
            assert wheel_tags.wheel_compatible(name, T312) is False

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
    def test_f6_malformed_wheel_filename_fails_closed(self, name: str) -> None:
        assert wheel_tags.wheel_compatible(name, T312) is False

    @pytest.mark.parametrize(
        "target",
        [
            _target("3.12", implementation="pypy"),
            _target("3.12", implementation="graalpy"),
            _target("3.12", platform="windows"),
            _target("3.12", platform="macos"),
            _target("3.12", architecture="amd64"),
            _target("3.12", architecture="aarch64"),
            _target("3.10"),
            _target("3.11"),
            _target("3.13"),
            _target("3.8.1"),
        ],
    )
    def test_f7_unknown_target_semantics_fail_closed(self, target: RuntimeTarget) -> None:
        assert wheel_tags.wheel_compatible("pkg-1.0-py3-none-any.whl", target) is False


class TestPredecessorRegression:
    """Targeted py312 parity with the frozen R3 wheel-tag semantics."""

    @pytest.mark.parametrize(
        "name",
        [
            # Real frozen R3-known py312 artifacts (docstring / calibration receipt).
            "bcrypt-4.2.1-cp37-abi3-manylinux_2_17_x86_64.whl",
            "cryptography-43.0.3-cp37-abi3-manylinux_2_17_x86_64.whl",
            "deptry-0.21.2-cp39-abi3-manylinux_2_17_x86_64.whl",
            "protobuf-5.29.2-cp38-abi3-manylinux_2_17_x86_64.whl",
            "pyxb-1.2.5-py3-none-any.whl",
            "authorizenet-1.1.4-py3-none-any.whl",
            "pkg-1.0-cp312-cp312-manylinux_2_17_x86_64.whl",
            "pkg-1.0-cp312-cp312-manylinux_2_36_x86_64.whl",
            "pkg-1.0-cp312-abi3-manylinux_2_17_x86_64.whl",
            "pkg-1.0-py2.py3-none-any.whl",
            "pkg-1.0-py38-none-any.whl",
        ],
    )
    def test_r3_accepted_py312_cases_still_accepted(self, name: str) -> None:
        assert wheel_tags.wheel_compatible(name, T312) is True

    @pytest.mark.parametrize(
        "name",
        [
            "pkg-1.0-cp311-cp311-manylinux_2_17_x86_64.whl",
            "pkg-1.0-cp313-cp313-manylinux_2_17_x86_64.whl",
            "pkg-1.0-cp312-cp312-win_amd64.whl",
            "pkg-1.0-cp312-cp312-macosx_10_9_x86_64.whl",
            "pkg-1.0-cp312-cp312-linux_aarch64.whl",
        ],
    )
    def test_r3_rejected_py312_cases_still_rejected(self, name: str) -> None:
        assert wheel_tags.wheel_compatible(name, T312) is False


class TestInterfaceIntegration:
    """Track A binds behind the frozen interface without modifying it."""

    def test_bound_dispatch_and_fail_closed_unbound(self) -> None:
        import benchmark.wp2.env_r4 as env_r4

        unbind_lock_parser()
        try:
            with pytest.raises(LockParseError):
                env_r4.wheel_compatible("pkg-1.0-py3-none-any.whl", T312)

            wheel_tags.bind()
            assert env_r4.wheel_compatible("pkg-1.0-py3-none-any.whl", T312) is True
            assert env_r4.wheel_compatible("pkg-1.0-cp39-cp39-linux_x86_64.whl", T312) is False
        finally:
            unbind_lock_parser()

    def test_parse_lock_out_of_scope_fails_closed(self) -> None:
        from pathlib import Path

        parser = wheel_tags.WheelTagParser()
        with pytest.raises(LockParseError):
            parser.parse_lock(Path("poetry.lock"), T312)
