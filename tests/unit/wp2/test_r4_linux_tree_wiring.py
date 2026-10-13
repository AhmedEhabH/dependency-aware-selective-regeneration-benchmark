"""I2 wiring tests for the R4 materialization seam (no Docker).

Tests the wiring seam in ``benchmark.wp2.env_r4.linux_tree_wiring``: that it
delegates to the qualified R4-C ``Materializer``, never falls back to a
Windows working-tree copy, preserves R4-C fail-closed behavior, is
deterministic, and does not touch the frozen shared interface.

The R4-C Docker integration suite is NOT recreated here; the seam is tested
with spies/stubs per the mission (P1-P6 + F2P).
"""
from __future__ import annotations

import re
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from benchmark.wp2.env_r4 import linux_tree_wiring
from benchmark.wp2.env_r4.linux_tree_materialize import MaterializeError, Materializer
from benchmark.wp2.env_r4.linux_tree_wiring import (
    LinuxTreeWiring,
    R4MaterializationSource,
)
from benchmark.wp2.linux_adapter import CommandResult, LinuxBackend

IMAGE = "envcanon/saleor-env-base-py312-bookworm:latest"
REPO_LINUX = "/opt/wp2_v2/saleor-cache"
COMMIT = "24f9b244d6bc8c591c9707380917d9b6c6d35c35"
VOLUME = "r4-i2-test-vol"


def _source(**overrides: object) -> R4MaterializationSource:
    values: dict[str, object] = {
        "image": IMAGE,
        "repo_linux_path": REPO_LINUX,
    }
    values.update(overrides)
    return R4MaterializationSource(**values)  # type: ignore[arg-type]


class _FakeBackend(LinuxBackend):
    """Backend that must never run; any call is a wiring/fallback defect."""

    def run(
        self,
        cmd: list[str],
        *,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout_s: int = 900,
    ) -> CommandResult:
        raise AssertionError("backend must never run in wiring tests")


class _SpyMaterializer(Materializer):
    """Spy on the qualified R4-C materializer's ``materialize`` entry point."""

    def __init__(self) -> None:
        super().__init__(_FakeBackend(), IMAGE, REPO_LINUX)
        self.calls: list[tuple[str, str]] = []
        self.result = 1788
        self.raise_error: MaterializeError | None = None

    def materialize(
        self, commit: str, volume: str, *, resolve: bool = True
    ) -> int:
        self.calls.append((commit, volume))
        if self.raise_error is not None:
            raise self.raise_error
        return self.result


def _wiring(spy: Materializer | None = None) -> LinuxTreeWiring:
    return LinuxTreeWiring(_FakeBackend(), _source(), materializer=spy)


# ---------------------------------------------------------------------------
# P1 — the facade delegates to the qualified R4-C materializer
# ---------------------------------------------------------------------------


def test_materialize_delegates_to_qualified_r4c_materializer() -> None:
    spy = _SpyMaterializer()
    w = _wiring(spy)
    count = w.materialize(COMMIT, VOLUME)
    assert count == spy.result
    assert spy.calls == [(COMMIT, VOLUME)]


def test_default_wiring_builds_qualified_r4c_materializer_from_source() -> None:
    backend = _FakeBackend()
    source = _source()
    w = LinuxTreeWiring(backend, source)
    m = w.materializer
    assert isinstance(m, Materializer)
    assert m.image == IMAGE
    assert m.repo == REPO_LINUX
    assert m.mount_src == "/src"
    assert m.mount_out == "/out"
    assert m._image_verified is False  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# P2 — the explicit Git commit identity reaches the materializer unchanged
# ---------------------------------------------------------------------------


def test_commit_identity_reaches_materializer_unchanged() -> None:
    spy = _SpyMaterializer()
    w = _wiring(spy)
    w.materialize(COMMIT, VOLUME)
    assert spy.calls == [(COMMIT, VOLUME)]
    assert spy.calls[0][0] is COMMIT
    assert spy.calls[0][1] is VOLUME


# ---------------------------------------------------------------------------
# P3 — no Windows working-tree fallback path exists in the facade
# ---------------------------------------------------------------------------


def test_facade_source_has_no_working_tree_copy_imports_or_calls() -> None:
    source = Path(linux_tree_wiring.__file__).read_text(encoding="utf-8")
    mods = {
        p
        for m in re.findall(r"^(?:from ([\w.]+)|import ([\w.]+))", source, re.M)
        for p in (m,)
        if p
    }
    forbidden = {"shutil", "os", "pathlib", "shlex", "glob", "subprocess"}
    assert not (mods & forbidden), mods & forbidden
    for call in ("copytree(", "copyfile(", "copy2(", "shutil.copy(", "os.replace("):
        assert call not in source


def test_materialize_invokes_only_the_r4c_materializer_at_runtime() -> None:
    spy = _SpyMaterializer()
    w = _wiring(spy)
    w.materialize(COMMIT, VOLUME)
    assert len(spy.calls) == 1
    assert spy.calls == [(COMMIT, VOLUME)]


# ---------------------------------------------------------------------------
# P4 — materialization failure from R4-C propagates fail closed
# ---------------------------------------------------------------------------


def test_materialize_failure_propagates_fail_closed() -> None:
    spy = _SpyMaterializer()
    error = MaterializeError(
        f"materialization failed for {COMMIT!r} (fail closed): BLOB_FAIL"
    )
    spy.raise_error = error
    w = _wiring(spy)
    with pytest.raises(MaterializeError) as exc_info:
        w.materialize(COMMIT, VOLUME)
    assert exc_info.value is error


# ---------------------------------------------------------------------------
# P5 — repeated identical calls are deterministic
# ---------------------------------------------------------------------------


def test_repeated_identical_calls_are_deterministic() -> None:
    spy = _SpyMaterializer()
    w = _wiring(spy)
    first = w.materialize(COMMIT, VOLUME)
    second = w.materialize(COMMIT, VOLUME)
    assert first == second == spy.result
    assert spy.calls == [(COMMIT, VOLUME), (COMMIT, VOLUME)]


def test_source_descriptor_is_frozen_and_equal_sources_are_equal() -> None:
    a = _source()
    b = _source()
    assert a == b
    assert hash(a) == hash(b)
    with pytest.raises(FrozenInstanceError):
        a.image = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# P6 — the facade does not alter the frozen shared interface
# ---------------------------------------------------------------------------


def test_facade_does_not_import_frozen_shared_interface() -> None:
    source = Path(linux_tree_wiring.__file__).read_text(encoding="utf-8")
    assert "env_r4.contracts" not in source
    assert "from benchmark.wp2.env_r4 import" not in source


# ---------------------------------------------------------------------------
# F2P — fail closed at the seam
# ---------------------------------------------------------------------------


def test_missing_repository_input_fails_closed() -> None:
    with pytest.raises(MaterializeError, match="blank"):
        _source(repo_linux_path=" ")
    with pytest.raises(MaterializeError, match="blank"):
        _source(repo_linux_path="")


def test_missing_image_input_fails_closed() -> None:
    with pytest.raises(MaterializeError, match="blank"):
        _source(image="  ")


def test_blank_commit_fails_closed_at_seam() -> None:
    w = _wiring(_SpyMaterializer())
    with pytest.raises(MaterializeError, match="blank"):
        w.materialize("", VOLUME)
    with pytest.raises(MaterializeError, match="blank"):
        w.materialize("   ", VOLUME)


def test_blank_volume_fails_closed_at_seam() -> None:
    w = _wiring(_SpyMaterializer())
    with pytest.raises(MaterializeError, match="blank"):
        w.materialize(COMMIT, "")


def test_missing_commit_identity_failure_propagates_fail_closed() -> None:
    spy = _SpyMaterializer()
    error = MaterializeError(
        "missing commit 'deadbeef' in local Git objects (fail closed)"
    )
    spy.raise_error = error
    w = _wiring(spy)
    with pytest.raises(MaterializeError) as exc_info:
        w.materialize("deadbeef", VOLUME)
    assert exc_info.value is error
    assert spy.calls == [("deadbeef", VOLUME)]
