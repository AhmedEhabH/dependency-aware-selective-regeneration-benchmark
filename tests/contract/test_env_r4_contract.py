"""Targeted contract tests for the frozen R4 shared interface (env-canon-r4).

These tests validate the frozen surface ONLY (types, rules, entry points);
they never exercise a lock-format parser because parsing is track-owned work.
See ``research/env-canon-r4/R4_SHARED_INTERFACE.md``.
"""
from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

import pytest

from benchmark.wp2.env_r4 import (
    LockClosure,
    LockParseError,
    LockParser,
    NormalizedRequirement,
    RuntimeTarget,
    SourceType,
    bind_lock_parser,
    normalize_name,
    parse_lock,
    unbind_lock_parser,
    wheel_compatible,
)

TARGET = RuntimeTarget(
    python_version="3.12",
    implementation="cpython",
    platform="linux",
    architecture="x86_64",
)


def _req(
    name: str,
    version: str = "1.0",
    source_type: SourceType = SourceType.REGISTRY,
    source_reference: str | None = None,
    marker: str | None = None,
    marker_applies: bool = True,
    editable_self: bool = False,
) -> NormalizedRequirement:
    return NormalizedRequirement(
        normalized_name=normalize_name(name),
        version=version,
        source_type=source_type,
        source_reference=source_reference,
        marker=marker,
        marker_applies=marker_applies,
        editable_self=editable_self,
    )


class TestFrozenFieldSets:
    def test_runtime_target_fields(self) -> None:
        names = tuple(f.name for f in dataclasses.fields(RuntimeTarget))
        assert names == ("python_version", "implementation", "platform", "architecture")

    def test_normalized_requirement_fields(self) -> None:
        names = tuple(f.name for f in dataclasses.fields(NormalizedRequirement))
        assert names == (
            "normalized_name",
            "version",
            "source_type",
            "source_reference",
            "marker",
            "marker_applies",
            "editable_self",
        )

    def test_lock_closure_fields(self) -> None:
        names = tuple(f.name for f in dataclasses.fields(LockClosure))
        assert names == (
            "lock_format",
            "target",
            "requirements",
            "editable_self",
            "exclusions",
            "fail_closed_reasons",
        )


class TestSourceType:
    def test_exactly_four_members(self) -> None:
        assert {member.value for member in SourceType} == {
            "REGISTRY",
            "DIRECTORY",
            "PATH",
            "EDITABLE_SELF",
        }

    @pytest.mark.parametrize(
        ("token", "expected"),
        [
            (None, SourceType.REGISTRY),
            ("registry", SourceType.REGISTRY),
            ("Registry", SourceType.REGISTRY),
            ("directory", SourceType.DIRECTORY),
            ("path", SourceType.PATH),
            ("virtual", SourceType.EDITABLE_SELF),
            ("editable_self", SourceType.EDITABLE_SELF),
            ("editable", SourceType.EDITABLE_SELF),
        ],
    )
    def test_known_tokens_classify(self, token: str | None, expected: SourceType) -> None:
        assert SourceType.from_token(token) is expected

    @pytest.mark.parametrize("token", ["git", "url", "file", "unknown", "", "  git  "])
    def test_unknown_token_fails_closed(self, token: str) -> None:
        with pytest.raises(LockParseError):
            SourceType.from_token(token)


class TestNormalizeName:
    def test_pep503_normalization(self) -> None:
        assert normalize_name("Django_Test.Pkg") == "django-test-pkg"
        assert normalize_name("  requests ") == "requests"

    def test_deterministic(self) -> None:
        assert normalize_name("a.b__c--d") == normalize_name("A_B.C---D")


class TestRuntimeTargetValidation:
    def test_malformed_python_version_fails_closed(self) -> None:
        with pytest.raises(LockParseError):
            RuntimeTarget(python_version="three", implementation="cpython", platform="linux", architecture="x86_64")


class TestRequirementValidation:
    def test_non_normalized_name_fails_closed(self) -> None:
        with pytest.raises(LockParseError):
            NormalizedRequirement(
                normalized_name="Django.Test",
                version="5.0",
                source_type=SourceType.REGISTRY,
                source_reference=None,
                marker=None,
                marker_applies=True,
                editable_self=False,
            )


def _closure(requirements: list[NormalizedRequirement], **kwargs: Any) -> LockClosure:
    kwargs.setdefault("lock_format", "poetry")
    kwargs.setdefault("target", TARGET)
    kwargs.setdefault("editable_self", None)
    kwargs.setdefault("exclusions", ())
    kwargs.setdefault("fail_closed_reasons", ())
    return LockClosure(requirements=tuple(requirements), **kwargs)


class TestDeterministicOrderingAndSerialization:
    @staticmethod
    def _shuffled_pair() -> tuple[tuple[NormalizedRequirement, ...], tuple[NormalizedRequirement, ...]]:
        a = (
            _req("gamma", version="2.0"),
            _req("alpha", version="1.0"),
            _req("beta", version="0.5"),
        )
        return a, tuple(reversed(a))

    def test_input_order_irrelevant_for_canonical_dict(self) -> None:
        first, second = self._shuffled_pair()
        a = _closure(list(first))
        b = _closure(list(second))
        assert a.to_canonical_dict() == b.to_canonical_dict()

    def test_input_order_irrelevant_for_freezing(self) -> None:
        first, second = self._shuffled_pair()
        a = _closure(list(first))
        b = _closure(list(second))
        assert a.freeze_sha256() == b.freeze_sha256()

    def test_serialization_is_stable(self) -> None:
        c = _closure([_req("django"), _req("requests", version="2.0")])
        payload = c.to_canonical_dict()
        assert c.to_canonical_dict() == payload


class TestEditableSelfIsolation:
    def test_editable_self_never_a_wheel_requirement(self) -> None:
        root = _req("root-project", editable_self=True)
        with pytest.raises(LockParseError):
            _closure([root])

    def test_root_project_carried_explicitly_not_emitted(self) -> None:
        root = _req("root-project", editable_self=True)
        dep = _req("django")
        closure = _closure([dep], editable_self=root)
        assert closure.editable_self == root
        assert closure.requirements == (dep,)
        assert not any(req.editable_self for req in closure.requirements)
        canonical = closure.to_canonical_dict()
        assert canonical["editable_self"] is not None
        assert canonical["editable_self"]["normalized_name"] == "root-project"
        assert canonical["editable_self"]["editable_self"] is True


class TestFailClosedSemantics:
    def test_fail_closed_reasons_mark_closure_invalid(self) -> None:
        closure = _closure([], fail_closed_reasons=("unknown source token 'git'",))
        assert closure.is_valid is False

    def test_clean_closure_is_valid(self) -> None:
        assert _closure([]).is_valid is True

    def test_invalid_closure_still_serializes_deterministically(self) -> None:
        closure = _closure([], fail_closed_reasons=("unknown source token 'git'",))
        assert closure.freeze_sha256() == closure.freeze_sha256()


class TestInterfaceDispatch:
    class _FakeParser:
        def parse_lock(
            self,
            lock_path: Path,
            target: RuntimeTarget,
            pyproject_path: Path | None = None,
        ) -> LockClosure:
            assert target == TARGET
            return _closure([_req("fake")])

        def wheel_compatible(self, wheel_filename: str, target: RuntimeTarget) -> bool:
            assert target == TARGET
            return wheel_filename.endswith(".whl")

    def test_unbound_fails_closed(self, tmp_path: Path) -> None:
        unbind_lock_parser()
        with pytest.raises(LockParseError):
            parse_lock(tmp_path / "poetry.lock", TARGET)
        with pytest.raises(LockParseError):
            wheel_compatible("demo-1.0-py3-none-any.whl", TARGET)

    def test_bound_dispatch_p2p(self, tmp_path: Path) -> None:
        bind_lock_parser(self._FakeParser())
        try:
            closure = parse_lock(tmp_path / "poetry.lock", TARGET)
            assert isinstance(closure, LockClosure)
            assert wheel_compatible("demo-1.0-py3-none-any.whl", TARGET) is True
            assert wheel_compatible("demo-1.0.tar.gz", TARGET) is False
        finally:
            unbind_lock_parser()

    def test_interface_signatures(self) -> None:
        import inspect
        from typing import get_type_hints

        sig = inspect.signature(LockParser.parse_lock)
        assert list(sig.parameters) == ["self", "lock_path", "target", "pyproject_path"]
        assert sig.parameters["pyproject_path"].default is None

        hints = get_type_hints(LockParser.parse_lock)
        assert hints["lock_path"] is Path
        assert hints["target"] is RuntimeTarget
        assert hints["pyproject_path"] == (Path | None)
        assert hints["return"] is LockClosure

        wsig = inspect.signature(LockParser.wheel_compatible)
        assert list(wsig.parameters) == ["self", "wheel_filename", "target"]
        whints = get_type_hints(LockParser.wheel_compatible)
        assert whints["wheel_filename"] is str
        assert whints["target"] is RuntimeTarget
        assert whints["return"] is bool


class TestNoTaskIdSpecialCases:
    def test_normalization_is_label_agnostic(self) -> None:
        taskish = normalize_name("SALEOR_RC-19bb9b070965.foo")
        assert taskish == "saleor-rc-19bb9b070965-foo"
        assert taskish == normalize_name("saleor-rc-19bb9b070965.foo")

    def test_classification_is_label_agnostic(self) -> None:
        for token in (None, "registry", "directory", "path", "virtual"):
            assert SourceType.from_token(token) is SourceType.from_token(token)

    def test_closure_freezing_is_label_agnostic(self) -> None:
        a = _closure([_req("task-a-000000000000")])
        b = _closure([_req("task-b-111111111111")])
        a_name = a.to_canonical_dict()["requirements"][0]["normalized_name"]
        b_name = b.to_canonical_dict()["requirements"][0]["normalized_name"]
        assert a_name.count("-") == b_name.count("-")
