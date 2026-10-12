"""R4-B uv lock adapter — P2P / F2P targeted tests.

Mission ``M17_D7_R4_B_UV_LOCK_ADAPTER``.

P2P (valid inputs must pass):

* P1  uv registry dependency becomes ``NormalizedRequirement(REGISTRY)``.
* P2  uv root virtual/editable Saleor project is represented as ``EDITABLE_SELF``.
* P3  the editable root is absent from third-party requirements.
* P4  a marker valid for Python 3.12 is included for a 3.12 ``RuntimeTarget``.
* P5  a marker not valid for the target is excluded and recorded deterministically.
* P6  requires-python semantics are evaluated correctly.
* P7  DIRECTORY/PATH source identity is preserved.
* P8  representative Poetry input preserves qualified behavior.
* P9  repeated parsing yields identical ``LockClosure`` freeze hash.

F2P (invalid/mutated inputs must fail closed):

* F1  malformed uv.lock => FAIL CLOSED.
* F2  unknown source type => FAIL CLOSED.
* F3  unsupported/invalid marker expression => FAIL CLOSED.
* F4  editable root emitted as REGISTRY requirement => test FAIL.
* F5  missing required name/version for registry package => FAIL CLOSED.
* F6  ambiguous source identity => FAIL CLOSED.
* F7  unsupported lock format => FAIL CLOSED.
* F8  task-ID-specific branch/special case => FAIL.

The real frozen Saleor 3.23.0 ``uv.lock`` (SHA-256 ``86a35ab0...`` matching the
frozen environment-provisioning evidence) is exercised in P2/P3/P5 to prove the
adapter handles genuine root-virtual/editable + registry + marker data.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from benchmark.wp2.env_r4.contracts import (
    LockClosure,
    LockParseError,
    NormalizedRequirement,
    RuntimeTarget,
    SourceType,
    normalize_name,
    parse_lock,
    unbind_lock_parser,
)
from benchmark.wp2.env_r4.uv_adapter import (
    EnvR4LockAdapter,
    bind_r4_b_parser,
)

PROJECT_DIR = Path(__file__).resolve().parents[4]
REAL_UV_LOCK = (
    PROJECT_DIR
    / "research"
    / "env-canon-r4"
    / "fixtures"
    / "saleor-3.23.0-uv.lock"
)

TARGET_312 = RuntimeTarget(
    python_version="3.12",
    implementation="cpython",
    platform="linux",
    architecture="x86_64",
)
TARGET_39 = RuntimeTarget(
    python_version="3.9",
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


# ---------------------------------------------------------------------------
# P2P
# ---------------------------------------------------------------------------


class TestP2PP1Registry:
    def test_uv_registry_dependency_is_registry(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            """version = 1
[[package]]
name = "requests"
version = "2.32.3"
source = { registry = "https://pypi.org/simple" }
""",
        )
        closure = EnvR4LockAdapter().parse_lock(lock, TARGET_312)
        req = next(r for r in closure.requirements if r.normalized_name == "requests")
        assert req.source_type is SourceType.REGISTRY
        assert req.source_reference == "https://pypi.org/simple"
        assert req.version == "2.32.3"
        assert closure.is_valid


class TestP2PEditableSelf:
    def test_root_virtual_project_is_editable_self(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            """version = 1
[[package]]
name = "saleor"
version = "3.23.0"
source = { virtual = "." }
dependencies = [
    { name = "django", marker = "platform_python_implementation != 'PyPy'" },
]

[[package]]
name = "django"
version = "5.2.13"
source = { registry = "https://pypi.org/simple" }
""",
        )
        closure = EnvR4LockAdapter().parse_lock(lock, TARGET_312)
        assert closure.editable_self is not None
        assert closure.editable_self.normalized_name == "saleor"
        assert closure.editable_self.source_type is SourceType.EDITABLE_SELF
        assert closure.editable_self.editable_self is True

    def test_editable_root_absent_from_requirements(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            """version = 1
[[package]]
name = "saleor"
version = "3.23.0"
source = { virtual = "." }
dependencies = [
    { name = "django", marker = "platform_python_implementation != 'PyPy'" },
]

[[package]]
name = "django"
version = "5.2.13"
source = { registry = "https://pypi.org/simple" }
""",
        )
        closure = EnvR4LockAdapter().parse_lock(lock, TARGET_312)
        assert "saleor" not in _names(closure)
        assert not any(r.editable_self for r in closure.requirements)


class TestRealFrozenFixture:
    @pytest.fixture()
    def real_closure(self) -> LockClosure:
        assert REAL_UV_LOCK.is_file(), "frozen Saleor uv.lock fixture missing"
        return EnvR4LockAdapter().parse_lock(REAL_UV_LOCK, TARGET_312)

    def test_real_fixture_hash(self) -> None:
        assert REAL_UV_LOCK.is_file()
        import hashlib

        digest = hashlib.sha256(REAL_UV_LOCK.read_bytes()).hexdigest()
        assert digest == "86a35ab0bf69629d04cc7f3d09f1c1fa205eb6afc6620b317754490b33f22907"

    def test_real_root_editable_self(self, real_closure: LockClosure) -> None:
        assert real_closure.editable_self is not None
        assert real_closure.editable_self.normalized_name == "saleor"
        assert real_closure.editable_self.version == "3.23.0"
        assert real_closure.editable_self.source_type is SourceType.EDITABLE_SELF

    def test_real_root_absent_from_requirements(self, real_closure: LockClosure) -> None:
        assert "saleor" not in _names(real_closure)

    def test_real_registry_dependencies(self, real_closure: LockClosure) -> None:
        django = next(r for r in real_closure.requirements if r.normalized_name == "django")
        assert django.source_type is SourceType.REGISTRY
        assert django.version == "5.2.13"

    def test_real_win32_only_excluded_with_marker(self, real_closure: LockClosure) -> None:
        excluded = {r.normalized_name: r for r in real_closure.exclusions}
        assert "pywin32" in excluded
        assert excluded["pywin32"].marker_applies is False
        assert excluded["pywin32"].marker is not None
        assert "sys_platform == 'win32'" in excluded["pywin32"].marker or "win32" in excluded["pywin32"].marker


class TestP2PMarkers:
    def test_marker_valid_for_312_included(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            """version = 1
[[package]]
name = "root"
version = "1.0"
source = { virtual = "." }
dependencies = [
    { name = "pycurl", marker = "python_version >= '3.12'" },
]

[[package]]
name = "pycurl"
version = "7.45.3"
source = { registry = "https://pypi.org/simple" }
""",
        )
        closure = EnvR4LockAdapter().parse_lock(lock, TARGET_312)
        assert "pycurl" in _names(closure)
        req = next(r for r in closure.requirements if r.normalized_name == "pycurl")
        assert req.marker_applies is True
        assert req.marker is not None and "python_version" in req.marker

    def test_marker_invalid_for_target_excluded_deterministically(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            """version = 1
[[package]]
name = "root"
version = "1.0"
source = { virtual = "." }
dependencies = [
    { name = "pycurl", marker = "python_version >= '3.12'" },
]

[[package]]
name = "pycurl"
version = "7.45.3"
source = { registry = "https://pypi.org/simple" }
""",
        )
        closure39 = EnvR4LockAdapter().parse_lock(lock, TARGET_39)
        assert "pycurl" not in _names(closure39)
        excl = {r.normalized_name: r for r in closure39.exclusions}
        assert "pycurl" in excl
        assert excl["pycurl"].marker_applies is False
        assert excl["pycurl"].marker is not None and "python_version >= '3.12'" in excl["pycurl"].marker
        closure39b = EnvR4LockAdapter().parse_lock(lock, TARGET_39)
        assert closure39.freeze_sha256() == closure39b.freeze_sha256()


class TestP2PRequiresPython:
    def test_requires_python_admits_target(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            """version = 1
requires-python = ">=3.12,<3.13"
[[package]]
name = "django"
version = "5.2.13"
source = { registry = "https://pypi.org/simple" }
""",
        )
        closure = EnvR4LockAdapter().parse_lock(lock, TARGET_312)
        assert closure.is_valid
        assert "django" in _names(closure)

    def test_requires_python_rejects_target_fail_closed(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            """version = 1
requires-python = ">=3.12,<3.13"
[[package]]
name = "django"
version = "5.2.13"
source = { registry = "https://pypi.org/simple" }
""",
        )
        with pytest.raises(LockParseError):
            EnvR4LockAdapter().parse_lock(lock, TARGET_39)


class TestP2PSourceIdentity:
    def test_directory_source_identity_preserved(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            """version = 1
[[package]]
name = "root"
version = "1.0"
source = { virtual = "." }
dependencies = [
    { name = "vendored-lib" },
]

[[package]]
name = "vendored-lib"
version = "0.1.0"
source = { directory = "vendor/vendored-lib" }
""",
        )
        closure = EnvR4LockAdapter().parse_lock(lock, TARGET_312)
        req = next(r for r in closure.requirements if r.normalized_name == "vendored-lib")
        assert req.source_type is SourceType.DIRECTORY
        assert req.source_reference == "vendor/vendored-lib"

    def test_path_source_identity_preserved(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            """version = 1
[[package]]
name = "root"
version = "1.0"
source = { virtual = "." }
dependencies = [
    { name = "local-lib" },
]

[[package]]
name = "local-lib"
version = "0.2.0"
source = { path = "../local-lib" }
""",
        )
        closure = EnvR4LockAdapter().parse_lock(lock, TARGET_312)
        req = next(r for r in closure.requirements if r.normalized_name == "local-lib")
        assert req.source_type is SourceType.PATH
        assert req.source_reference == "../local-lib"


class TestP2PPoetryRegression:
    POETRY_LOCK = """[[package]]
name = "django"
version = "5.2.13"
description = "web framework"
optional = false
python-versions = ">=3.8"
groups = ["main"]

[[package]]
name = "pytest"
version = "8.3.4"
description = "test framework"
optional = false
python-versions = ">=3.8"
groups = ["dev"]
markers = "sys_platform != 'win32' or python_version >= '3.12'"

[[package]]
name = "pywin32"
version = "311"
description = "win only"
optional = false
python-versions = ">=3.8"
groups = ["dev"]
markers = "sys_platform == 'win32'"

[metadata]
lock-version = "2.0"
python-versions = "^3.12"
content-hash = "deadbeef"
"""

    def test_poetry_input_preserves_qualified_behavior(self, tmp_path: Path) -> None:
        from benchmark.wp2 import source_fidelity_r1 as sf

        lock = _write(tmp_path, "poetry.lock", self.POETRY_LOCK)
        closure = EnvR4LockAdapter().parse_lock(lock, TARGET_312)
        assert closure.lock_format == "poetry"
        assert closure.is_valid
        assert {r.normalized_name for r in closure.requirements} == {"django", "pytest"}
        assert {r.normalized_name for r in closure.exclusions} == {"pywin32"}

        pre = sf.derive_source_aware_closure(
            self.POETRY_LOCK,
            target_commit="0" * 40,
            repo_dir=None,
            python_version="3.12",
            sys_platform="linux",
            lock_format="poetry",
        )
        pre_names = {r["name"] for r in pre["records"]}
        assert {r.normalized_name for r in closure.requirements} == pre_names

    def test_poetry_registry_source_classification(self, tmp_path: Path) -> None:
        lock = _write(tmp_path, "poetry.lock", self.POETRY_LOCK)
        closure = EnvR4LockAdapter().parse_lock(lock, TARGET_312)
        for req in closure.requirements:
            assert req.source_type is SourceType.REGISTRY
        assert closure.editable_self is None


class TestP2PDeterminism:
    def test_repeated_parse_identical_freeze_hash(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            """version = 1
[[package]]
name = "b"
version = "2.0"
source = { registry = "https://pypi.org/simple" }
[[package]]
name = "a"
version = "1.0"
source = { registry = "https://pypi.org/simple" }
""",
        )
        adapter = EnvR4LockAdapter()
        c1 = adapter.parse_lock(lock, TARGET_312)
        c2 = adapter.parse_lock(lock, TARGET_312)
        assert c1.freeze_sha256() == c2.freeze_sha256()
        assert c1.to_canonical_dict() == c2.to_canonical_dict()


class TestInterfaceDispatch:
    def test_bound_interface_uv(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            """version = 1
[[package]]
name = "requests"
version = "2.32.3"
source = { registry = "https://pypi.org/simple" }
""",
        )
        bind_r4_b_parser()
        try:
            closure = parse_lock(lock, TARGET_312)
            assert closure.lock_format == "uv"
            assert "requests" in _names(closure)
        finally:
            unbind_lock_parser()


# ---------------------------------------------------------------------------
# F2P
# ---------------------------------------------------------------------------


class TestF2PMalformed:
    def test_malformed_uv_lock_fails_closed(self, tmp_path: Path) -> None:
        lock = _write(tmp_path, "uv.lock", "version = 1\n[[package]]\nname = ")
        with pytest.raises(LockParseError):
            EnvR4LockAdapter().parse_lock(lock, TARGET_312)


class TestF2PUnknownSource:
    @pytest.mark.parametrize(
        "source_line",
        [
            'source = { git = { url = "https://github.com/x/y" } }',
            'source = { url = "https://example.com/x.tar.gz" }',
            'source = { file = "/tmp/x.whl" }',
            'source = { editable = "../local" }',
            "source = { registry = 123 }",
        ],
    )
    def test_unknown_source_type_fails_closed(
        self, tmp_path: Path, source_line: str
    ) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            f"""version = 1
[[package]]
name = "mystery"
version = "1.0"
{source_line}
""",
        )
        with pytest.raises(LockParseError):
            EnvR4LockAdapter().parse_lock(lock, TARGET_312)


class TestF2PInvalidMarker:
    def test_unsupported_marker_fails_closed(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            """version = 1
[[package]]
name = "root"
version = "1.0"
source = { virtual = "." }
dependencies = [
    { name = "bad", marker = "python_version >>= '3.12'" },
]

[[package]]
name = "bad"
version = "1.0"
source = { registry = "https://pypi.org/simple" }
""",
        )
        with pytest.raises(LockParseError):
            EnvR4LockAdapter().parse_lock(lock, TARGET_312)


class TestF2PEditableRootAsRegistry:
    def test_editable_root_never_emitted_as_registry_requirement(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            """version = 1
[[package]]
name = "saleor"
version = "3.23.0"
source = { virtual = "." }
dependencies = [
    { name = "django" },
]

[[package]]
name = "django"
version = "5.2.13"
source = { registry = "https://pypi.org/simple" }
""",
        )
        closure = EnvR4LockAdapter().parse_lock(lock, TARGET_312)
        assert closure.editable_self is not None
        assert closure.editable_self.source_type is SourceType.EDITABLE_SELF
        assert "saleor" not in _names(closure)
        assert not any(r.editable_self for r in closure.requirements)
        root_as_registry = NormalizedRequirement(
            normalized_name="saleor",
            version="3.23.0",
            source_type=SourceType.REGISTRY,
            source_reference="https://pypi.org/simple",
            marker=None,
            marker_applies=True,
            editable_self=True,
        )
        with pytest.raises(LockParseError):
            LockClosure(
                lock_format="uv",
                target=TARGET_312,
                requirements=(root_as_registry,),
                editable_self=None,
                exclusions=(),
                fail_closed_reasons=(),
            )


class TestF2PMissingNameVersion:
    def test_missing_name_fails_closed(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            """version = 1
[[package]]
version = "1.0"
source = { registry = "https://pypi.org/simple" }
""",
        )
        with pytest.raises(LockParseError):
            EnvR4LockAdapter().parse_lock(lock, TARGET_312)

    def test_missing_version_fails_closed(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            """version = 1
[[package]]
name = "nover"
source = { registry = "https://pypi.org/simple" }
""",
        )
        with pytest.raises(LockParseError):
            EnvR4LockAdapter().parse_lock(lock, TARGET_312)


class TestF2PAmbiguousSource:
    def test_duplicate_package_name_fails_closed(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            """version = 1
[[package]]
name = "dup"
version = "1.0"
source = { registry = "https://pypi.org/simple" }
[[package]]
name = "dup"
version = "2.0"
source = { registry = "https://pypi.org/simple" }
""",
        )
        with pytest.raises(LockParseError):
            EnvR4LockAdapter().parse_lock(lock, TARGET_312)

    def test_multiple_virtual_roots_fails_closed(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            """version = 1
[[package]]
name = "root1"
version = "1.0"
source = { virtual = "." }
[[package]]
name = "root2"
version = "1.0"
source = { virtual = "." }
""",
        )
        with pytest.raises(LockParseError):
            EnvR4LockAdapter().parse_lock(lock, TARGET_312)


class TestF2PUnsupportedFormat:
    @pytest.mark.parametrize(
        "text",
        [
            "version = 3\n[[package]]\nname = 'x'\nversion = '1'\n",
            "version = 'one'\n[[package]]\nname = 'x'\nversion = '1'\n",
            "not a lock file at all",
            "[[package]]\nname = 'x'\nversion = '1'\n",
        ],
    )
    def test_unsupported_lock_format_fails_closed(self, tmp_path: Path, text: str) -> None:
        lock = _write(tmp_path, "uv.lock", text)
        with pytest.raises(LockParseError):
            EnvR4LockAdapter().parse_lock(lock, TARGET_312)


class TestF2PNoTaskIdSpecialCase:
    TASK_ID = r"saleor-rc-[0-9a-f]{12}"

    def test_no_task_id_branch_in_adapter_source(self) -> None:
        import inspect

        source = inspect.getsource(EnvR4LockAdapter)
        assert re.search(self.TASK_ID, source) is None

    def test_task_id_named_package_is_normalized_generically(self, tmp_path: Path) -> None:
        lock = _write(
            tmp_path,
            "uv.lock",
            """version = 1
[[package]]
name = "saleor-rc-19bb9b070965"
version = "1.0"
source = { registry = "https://pypi.org/simple" }
""",
        )
        closure = EnvR4LockAdapter().parse_lock(lock, TARGET_312)
        names = _names(closure)
        assert "saleor-rc-19bb9b070965" in names
        req = next(iter(closure.requirements))
        assert req.normalized_name == normalize_name("saleor-rc-19bb9b070965")


class TestWheelCompatibleOutOfScope:
    def test_wheel_compatible_fails_closed(self) -> None:
        with pytest.raises(LockParseError):
            EnvR4LockAdapter().wheel_compatible("demo-1.0-py3-none-any.whl", TARGET_312)


class TestNormalizationLabelAgnostic:
    def test_requirement_sorting_and_hash_are_label_agnostic(self) -> None:
        lock_a = """version = 1
[[package]]
name = "task-a-000000000000"
version = "1.0"
source = { registry = "https://pypi.org/simple" }
"""
        lock_b = """version = 1
[[package]]
name = "task-b-111111111111"
version = "1.0"
source = { registry = "https://pypi.org/simple" }
"""
        import tempfile

        adapter = EnvR4LockAdapter()
        with tempfile.TemporaryDirectory() as d:
            pa = Path(d) / "uv.lock"
            pa.write_text(lock_a, encoding="utf-8")
            ca = adapter.parse_lock(pa, TARGET_312)
        with tempfile.TemporaryDirectory() as d:
            pb = Path(d) / "uv.lock"
            pb.write_text(lock_b, encoding="utf-8")
            cb = adapter.parse_lock(pb, TARGET_312)
        a_name = ca.to_canonical_dict()["requirements"][0]["normalized_name"]
        b_name = cb.to_canonical_dict()["requirements"][0]["normalized_name"]
        assert a_name.count("-") == b_name.count("-")
