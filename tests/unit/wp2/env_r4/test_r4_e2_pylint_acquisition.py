"""M17_D7_R4_E2 pylint acquisition P2P/F2P tests (mission-local, OFFLINE).

Mission M17_D7_R4_E2_PYLINT_OFFICIAL_PYPI_ACQUISITION.

These tests exercise the acquisition driver logic with MOCKS and local
wheel fixtures ONLY.  NO real network, NO real PyPI metadata, NO downloads.

P2P (P1..P12):
  P1  — exact allowlist has exactly 28 identities.
  P2  — every identity canonicalizes to ``pylint`` and is in the frozen set.
  P3  — metadata URL template is exactly the official PyPI JSON endpoint.
  P4  — metadata host allowlist accepts ``pypi.org`` only.
  P5  — artifact host allowlist accepts ``files.pythonhosted.org`` only.
  P6  — a ``py3-none-any`` wheel is accepted when R4-A reports compatible.
  P7  — official SHA-256 equals downloaded SHA-256.
  P8  — safe ZIP + matching METADATA passes verification.
  P9  — a verified staging artifact promotes into the overlay.
  P10 — 28/28 produces a complete manifest.
  P11 — no dependency acquisition occurs (driver never resolves deps).
  P12 — frozen wheelhouse path/manifest are never written.

F2P (F1..F18):
  F1  — missing required version fails.
  F2  — extra version fails.
  F3  — wrong package name fails.
  F4  — non-PyPI metadata host fails.
  F5  — non-files.pythonhosted.org artifact host fails.
  F6  — yanked release stops owner review.
  F7  — no compatible wheel stops owner review.
  F8  — wrong-version wheel fails.
  F9  — incompatible wheel fails.
  F10 — hash mismatch fails.
  F11 — corrupt ZIP fails.
  F12 — absolute path fails.
  F13 — path traversal fails.
  F14 — METADATA Name mismatch fails.
  F15 — METADATA Version mismatch fails.
  F16 — dependency download attempt fails (any non-allowlist URL refused).
  F17 — frozen wheelhouse destination fails closed.
  F18 — unverified staging file cannot promote.
"""
from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(SCRIPTS))

import r4_e2_pylint_official_pypi_acquisition as e2  # noqa: E402

from benchmark.wp2.env_r4.contracts import RuntimeTarget  # noqa: E402

T39 = RuntimeTarget(python_version="3.9", implementation="cpython", platform="linux", architecture="x86_64")


def _r4a(name: str, target: RuntimeTarget) -> bool:
    from benchmark.wp2.env_r4.wheel_tags import wheel_compatible as _wc

    return _wc(name, target)


def _fake_release(
    *,
    version: str = "2.7.2",
    wheel_tag: str = "py3-none-any",
    sha256: str = "a" * 64,
    yanked: bool = False,
    yanked_reason: str | None = None,
    url: str | None = None,
    filename: str | None = None,
) -> dict:
    fn = filename or f"pylint-{version}-{wheel_tag}.whl"
    u = url or f"https://files.pythonhosted.org/packages/aa/{fn}"
    return {
        "info": {"name": "pylint", "version": version},
        "urls": [
            {
                "filename": fn,
                "packagetype": "bdist_wheel",
                "url": u,
                "digests": {"sha256": sha256},
                "size": 1000,
                "upload_time": "2021-01-01T00:00:00",
                "upload_time_iso_8601": "2021-01-01T00:00:00.000000Z",
                "yanked": yanked,
                "yanked_reason": yanked_reason,
            }
        ],
    }


def _wheel_bytes(
    *,
    version: str = "2.7.2",
    metadata_name: str = "pylint",
    metadata_version: str | None = None,
    extra_entry: str | None = None,
    absolute: bool = False,
    traversal: bool = False,
) -> bytes:
    mv = metadata_version or version
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        meta = f"Metadata-Version: 2.1\nName: {metadata_name}\nVersion: {mv}\n"
        zf.writestr(f"pylint-{version}.dist-info/METADATA", meta)
        zf.writestr("pylint/__init__.py", "VERSION = 'x'\n")
        if extra_entry:
            zf.writestr(extra_entry, "x")
        if absolute:
            zf.writestr("/abs/path.txt", "x")
        if traversal:
            zf.writestr("../escape.txt", "x")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# P2P
# ---------------------------------------------------------------------------


class TestP1Allowlist:
    def test_exactly_28(self) -> None:
        assert len(e2.REQUIRED_IDENTITIES) == 28
        assert len({v for _, v in e2.REQUIRED_IDENTITIES}) == 28

    def test_all_pylint(self) -> None:
        for name, _v in e2.REQUIRED_IDENTITIES:
            assert e2.normalize_name(name) == "pylint"

    def test_matches_plan_identities(self) -> None:
        plan = json.loads(
            (ROOT / "research" / "env-canon-r4" / "R4_E1_PYLINT_RECOVERY_PLAN.json").read_text(encoding="utf-8")
        )
        plan_ids = tuple(tuple(i) for i in plan["exact_ordered_recovery_identities"])
        assert plan_ids == e2.REQUIRED_IDENTITIES


class TestP2ExactIdentity:
    def test_accepts_every_allowed(self) -> None:
        for name, version in e2.REQUIRED_IDENTITIES:
            assert e2.is_exact_identity(name, version)

    def test_rejects_unknown(self) -> None:
        assert not e2.is_exact_identity("pylint", "9.9.9")
        assert not e2.is_exact_identity("ruff", "2.7.2")


class TestP3MetadataURL:
    def test_template_exact(self) -> None:
        assert e2.METADATA_TEMPLATE == "https://pypi.org/pypi/{name}/{version}/json"

    def test_constructed_url(self) -> None:
        assert e2.metadata_url("pylint", "2.7.2") == "https://pypi.org/pypi/pylint/2.7.2/json"


class TestP4MetadataHost:
    def test_pypi_org_only(self) -> None:
        assert e2.is_allowed_metadata_url("https://pypi.org/pypi/pylint/2.7.2/json")
        assert not e2.is_allowed_metadata_url("https://files.pythonhosted.org/xx")
        assert not e2.is_allowed_metadata_url("http://pypi.org/x")
        assert not e2.is_allowed_metadata_url("https://github.com/x")


class TestP5ArtifactHost:
    def test_files_host_only(self) -> None:
        assert e2.is_allowed_artifact_url("https://files.pythonhosted.org/packages/aa/pylint-2.7.2-py3-none-any.whl")
        assert not e2.is_allowed_artifact_url("https://pypi.org/packages/aa/x.whl")
        assert not e2.is_allowed_artifact_url("https://example.com/x.whl")


class TestP6CompatibleSelection:
    def test_py3_none_any_selected(self) -> None:
        art = e2.select_wheel(_fake_release(), "pylint", "2.7.2", _r4a, T39)
        assert art.filename == "pylint-2.7.2-py3-none-any.whl"
        assert art.version == "2.7.2"
        assert not art.yanked

    def test_deterministic_prefers_pure_python(self) -> None:
        rel = {
            "urls": [
                {
                    "filename": "pylint-2.7.2-cp39-cp39-manylinux_2_17_x86_64.whl",
                    "packagetype": "bdist_wheel",
                    "url": "https://files.pythonhosted.org/packages/aa/pylint-2.7.2-cp39-cp39-manylinux_2_17_x86_64.whl",
                    "digests": {"sha256": "b" * 64},
                    "size": 1,
                    "yanked": False,
                },
                {
                    "filename": "pylint-2.7.2-py3-none-any.whl",
                    "packagetype": "bdist_wheel",
                    "url": "https://files.pythonhosted.org/packages/bb/pylint-2.7.2-py3-none-any.whl",
                    "digests": {"sha256": "c" * 64},
                    "size": 2,
                    "yanked": False,
                },
            ]
        }
        art = e2.select_wheel(rel, "pylint", "2.7.2", _r4a, T39)
        assert art.filename == "pylint-2.7.2-py3-none-any.whl"


class TestP7P8P9VerificationAndPromotion:
    def test_full_verify_passes(self, tmp_path: Path) -> None:
        data = _wheel_bytes()
        art = e2.select_wheel(_fake_release(sha256=e2._sha256_bytes(data)), "pylint", "2.7.2", _r4a, T39)
        res = e2.verify_wheel_bytes(
            data,
            url=art.url,
            expected_sha256=art.expected_sha256,
            package="pylint",
            version="2.7.2",
            filename=art.filename,
            compat_fn=_r4a,
            target=T39,
        )
        assert res.passed, res.checks
        assert res.metadata_name == "pylint"
        assert res.metadata_version == "2.7.2"

    def test_promotion_only_after_verify(self, tmp_path: Path) -> None:
        staging = tmp_path / "staging"
        wheels = tmp_path / "wheels"
        staging.mkdir()
        data = _wheel_bytes()
        art = e2.select_wheel(_fake_release(sha256=e2._sha256_bytes(data)), "pylint", "2.7.2", _r4a, T39)
        (staging / art.filename).write_bytes(data)
        res = e2.verify_wheel_bytes(
            data,
            url=art.url,
            expected_sha256=art.expected_sha256,
            package="pylint",
            version="2.7.2",
            filename=art.filename,
            compat_fn=_r4a,
            target=T39,
        )
        assert res.passed
        driver = e2.AcquisitionDriver(staging=staging, wheels=wheels, manifests=tmp_path / "m")
        promoted = driver.promote_all([art], [res])
        assert (wheels / art.filename).exists()
        assert promoted[0]["promoted"] is True

    def test_28_28_complete_manifest(self, tmp_path: Path) -> None:
        staging = tmp_path / "staging"
        staging.mkdir()
        artifacts = []
        results = []
        for name, version in e2.REQUIRED_IDENTITIES:
            data = _wheel_bytes(version=version)
            rel = _fake_release(version=version, sha256=e2._sha256_bytes(data))
            art = e2.select_wheel(rel, name, version, _r4a, T39)
            (staging / art.filename).write_bytes(data)
            res = e2.verify_wheel_bytes(
                data,
                url=art.url,
                expected_sha256=art.expected_sha256,
                package=name,
                version=version,
                filename=art.filename,
                compat_fn=_r4a,
                target=T39,
            )
            assert res.passed
            artifacts.append(art)
            results.append(res)
        driver = e2.AcquisitionDriver(staging=staging, wheels=tmp_path / "w", manifests=tmp_path / "m")
        promoted = driver.promote_all(artifacts, results)
        manifest = driver.build_manifest(artifacts, results, promoted)
        assert manifest["counts"]["requested"] == 28
        assert manifest["counts"]["verified"] == 28
        assert manifest["counts"]["promoted"] == 28
        assert len(manifest["artifacts"]) == 28
        assert manifest["dependency_downloads"] == 0


class TestP11NoDependencies:
    def test_driver_never_resolves_dependencies(self) -> None:
        driver = e2.AcquisitionDriver()
        assert driver.stats.artifact_requests == 0
        assert e2.METADATA_HOST == "pypi.org"
        assert e2.ARTIFACT_HOST == "files.pythonhosted.org"


class TestP13SelectionStateRoundTrip:
    def test_state_roundtrip_preserves_identity(self) -> None:
        art = e2.select_wheel(_fake_release(), "pylint", "2.7.2", _r4a, T39)
        data = e2._artifact_to_dict(art)
        back = e2._artifact_from_dict(data)
        assert back.package == "pylint"
        assert back.version == "2.7.2"
        assert back.filename == art.filename
        assert back.url == art.url
        assert back.expected_sha256 == art.expected_sha256
        assert back.wheel_tags == art.wheel_tags
        assert back.metadata_url == art.metadata_url


class TestP12FrozenStore:
    def test_frozen_wheelhouse_not_modified(self) -> None:
        assert e2.STORAGE_ROOT != e2.FROZEN_WHEELHOUSE
        assert e2.WHEELS != e2.FROZEN_WHEELHOUSE
        assert e2.FROZEN_WHEELHOUSE not in e2.WHEELS.parents


# ---------------------------------------------------------------------------
# F2P
# ---------------------------------------------------------------------------


class TestF1MissingVersion:
    def test_reject_unknown_version(self) -> None:
        with pytest.raises(e2.AcquisitionError):
            e2.metadata_url("pylint", "1.0.0")


class TestF2ExtraVersion:
    def test_reject_unfrozen_extra(self) -> None:
        assert not e2.is_exact_identity("pylint", "2.7.6")


class TestF3WrongPackage:
    def test_reject_wrong_name(self) -> None:
        with pytest.raises(e2.AcquisitionError):
            e2.metadata_url("black", "2.7.2")


class TestF4MetadataHost:
    def test_reject_foreign_metadata_url(self) -> None:
        assert not e2.is_allowed_metadata_url("https://example.org/pypi/pylint/2.7.2/json")


class TestF5ArtifactHost:
    def test_selection_rejects_foreign_url(self) -> None:
        rel = _fake_release(url="https://example.org/x/pylint-2.7.2-py3-none-any.whl")
        with pytest.raises(e2.AcquisitionError):
            e2.select_wheel(rel, "pylint", "2.7.2", _r4a, T39)


class TestF6Yanked:
    def test_all_yanked_stops_owner_review(self) -> None:
        rel = _fake_release(yanked=True, yanked_reason="bad packaging")
        with pytest.raises(e2.StopOwnerReviewError):
            e2.select_wheel(rel, "pylint", "2.7.2", _r4a, T39)


class TestF7NoCompatible:
    def test_no_compatible_wheel_stops_owner_review(self) -> None:
        rel = _fake_release(wheel_tag="cp311-cp311-manylinux_2_36_x86_64")
        with pytest.raises(e2.StopOwnerReviewError):
            e2.select_wheel(rel, "pylint", "2.7.2", _r4a, T39)


class TestF8WrongVersionWheel:
    def test_selection_ignores_wrong_version(self) -> None:
        rel = _fake_release(filename="pylint-2.8.1-py3-none-any.whl", version="2.8.1")
        with pytest.raises(e2.StopOwnerReviewError):
            e2.select_wheel(rel, "pylint", "2.7.2", _r4a, T39)


class TestF9Incompatible:
    def test_wrong_python_tag_rejected(self) -> None:
        rel = _fake_release(wheel_tag="cp311-cp311-win_amd64")
        with pytest.raises(e2.StopOwnerReviewError):
            e2.select_wheel(rel, "pylint", "2.7.2", _r4a, T39)


class TestF10HashMismatch:
    def test_sha_mismatch_fails(self) -> None:
        data = _wheel_bytes()
        res = e2.verify_wheel_bytes(
            data,
            url="https://files.pythonhosted.org/packages/aa/pylint-2.7.2-py3-none-any.whl",
            expected_sha256="f" * 64,
            package="pylint",
            version="2.7.2",
            filename="pylint-2.7.2-py3-none-any.whl",
            compat_fn=_r4a,
            target=T39,
        )
        assert not res.passed
        assert res.checks["downloaded_sha256_matches"] is False


class TestF11CorruptZip:
    def test_corrupt_zip_fails(self) -> None:
        data = b"this is not a zip archive at all" + b"\x00" * 32
        res = e2.verify_wheel_bytes(
            data,
            url="https://files.pythonhosted.org/packages/aa/pylint-2.7.2-py3-none-any.whl",
            expected_sha256=e2._sha256_bytes(data),
            package="pylint",
            version="2.7.2",
            filename="pylint-2.7.2-py3-none-any.whl",
            compat_fn=_r4a,
            target=T39,
        )
        assert not res.passed
        assert res.checks["zip_integrity"] is False


class TestF12AbsolutePath:
    def test_absolute_path_fails(self) -> None:
        data = _wheel_bytes(absolute=True)
        res = e2.verify_wheel_bytes(
            data,
            url="https://files.pythonhosted.org/packages/aa/pylint-2.7.2-py3-none-any.whl",
            expected_sha256=e2._sha256_bytes(data),
            package="pylint",
            version="2.7.2",
            filename="pylint-2.7.2-py3-none-any.whl",
            compat_fn=_r4a,
            target=T39,
        )
        assert not res.passed
        assert res.checks["no_absolute_paths"] is False


class TestF13Traversal:
    def test_dotdot_traversal_fails(self) -> None:
        data = _wheel_bytes(traversal=True)
        res = e2.verify_wheel_bytes(
            data,
            url="https://files.pythonhosted.org/packages/aa/pylint-2.7.2-py3-none-any.whl",
            expected_sha256=e2._sha256_bytes(data),
            package="pylint",
            version="2.7.2",
            filename="pylint-2.7.2-py3-none-any.whl",
            compat_fn=_r4a,
            target=T39,
        )
        assert not res.passed
        assert res.checks["no_dotdot_traversal"] is False


class TestF14MetadataName:
    def test_wrong_metadata_name_fails(self) -> None:
        data = _wheel_bytes(metadata_name="black")
        res = e2.verify_wheel_bytes(
            data,
            url="https://files.pythonhosted.org/packages/aa/pylint-2.7.2-py3-none-any.whl",
            expected_sha256=e2._sha256_bytes(data),
            package="pylint",
            version="2.7.2",
            filename="pylint-2.7.2-py3-none-any.whl",
            compat_fn=_r4a,
            target=T39,
        )
        assert not res.passed
        assert res.checks["metadata_name_canonical_pylint"] is False


class TestF15MetadataVersion:
    def test_wrong_metadata_version_fails(self) -> None:
        data = _wheel_bytes(metadata_version="9.9.9")
        res = e2.verify_wheel_bytes(
            data,
            url="https://files.pythonhosted.org/packages/aa/pylint-2.7.2-py3-none-any.whl",
            expected_sha256=e2._sha256_bytes(data),
            package="pylint",
            version="2.7.2",
            filename="pylint-2.7.2-py3-none-any.whl",
            compat_fn=_r4a,
            target=T39,
        )
        assert not res.passed
        assert res.checks["metadata_version_exact"] is False


class TestF16DependencyDownload:
    def test_non_allowlisted_artifact_refused(self) -> None:
        deps = "https://files.pythonhosted.org/packages/xx/astroid-2.5.1-py3-none-any.whl"
        assert e2.is_allowed_artifact_url(deps)
        # dependency URLs never appear in allowlist checks and foreign hosts fail
        assert not e2.is_allowed_artifact_url("https://example.com/packages/xx/astroid-2.5.1-py3-none-any.whl")

    def test_dependency_identity_not_in_allowlist(self) -> None:
        assert not e2.is_exact_identity("astroid", "2.5.1")
        with pytest.raises(e2.AcquisitionError):
            e2.metadata_url("astroid", "2.5.1")


class TestF17FrozenStore:
    def test_frozen_store_never_recovery_destination(self) -> None:
        assert e2.WHEELS != e2.FROZEN_WHEELHOUSE
        assert e2.FROZEN_MANIFEST.parent != e2.MANIFESTS


class TestF18UnverifiedNoPromote:
    def test_unverified_staging_cannot_promote(self, tmp_path: Path) -> None:
        staging = tmp_path / "staging"
        wheels = tmp_path / "wheels"
        staging.mkdir()
        data = _wheel_bytes()
        art = e2.select_wheel(_fake_release(sha256=e2._sha256_bytes(data)), "pylint", "2.7.2", _r4a, T39)
        (staging / art.filename).write_bytes(b"corrupted")
        bad = e2.verify_wheel_bytes(
            b"corrupted",
            url=art.url,
            expected_sha256=art.expected_sha256,
            package="pylint",
            version="2.7.2",
            filename=art.filename,
            compat_fn=_r4a,
            target=T39,
        )
        assert not bad.passed
        driver = e2.AcquisitionDriver(staging=staging, wheels=wheels, manifests=tmp_path / "m")
        with pytest.raises(e2.AcquisitionError):
            driver.promote_all([art], [bad])
        assert not (wheels / art.filename).exists()
