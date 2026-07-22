import pytest

from benchmark.core.models import RepositoryIdentity
from benchmark.repositories.manifest import (
    ManifestCollection,
    RepositoryManifest,
    RepositoryProfile,
    RepositoryVersionEntry,
)


def _make_manifest(repo_id: str, url: str = "https://example.com/repo") -> RepositoryManifest:
    return RepositoryManifest(
        identity=RepositoryIdentity(name=repo_id, url=url),
        description="Test repo",
        architecture_style="modular",
        size="small",
        language="Python",
        license_name="MIT",
        license_url="https://opensource.org/licenses/MIT",
        url=url,
        default_branch="main",
        test_runner="pytest",
        test_discovery="pytest",
        build_system="pip",
        status="confirmatory",
        protocol_eligibility={"da_01": True, "da_03": True},
    )


def _make_version(repo_id: str) -> RepositoryVersionEntry:
    return RepositoryVersionEntry(
        repository_id=repo_id,
        version="1.0.0",
        version_type="stable",
        commit_sha="abc123",
        commit_date="2026-01-01",
        tag="v1.0.0",
        release_date="2026-01-01",
        age_at_freeze_days=200,
        da_03_compliant=True,
        branch="main",
        dependency_file="requirements.txt",
        python_version=">=3.10",
    )


def _make_profile(repo_id: str) -> RepositoryProfile:
    return RepositoryProfile(
        repository_id=repo_id,
        name="Test Repo",
        protocol_version="1.0",
        overview="A test repository",
    )


class TestRepositoryManifest:
    def test_valid_creation(self) -> None:
        m = _make_manifest("test-repo")
        assert m.identity.name == "test-repo"
        assert m.size == "small"
        assert m.protocol_eligibility["da_01"] is True

    def test_empty_identity_raises(self) -> None:
        with pytest.raises(ValueError, match="RepositoryIdentity.name"):
            RepositoryIdentity(name="", url="x")


class TestRepositoryVersionEntry:
    def test_valid_creation(self) -> None:
        v = _make_version("test-repo")
        assert v.repository_id == "test-repo"
        assert v.commit_sha == "abc123"

    def test_tbd_commit_sha_allowed(self) -> None:
        v = RepositoryVersionEntry(
            repository_id="r",
            version="0.0.1",
            version_type="initial",
            commit_sha="TBD",
            commit_date="TBD",
            tag="v0.0.1",
            release_date="2026-01-01",
            age_at_freeze_days=0,
            da_03_compliant=True,
            branch="main",
            dependency_file="",
            python_version=">=3.10",
        )
        assert v.commit_sha == "TBD"


class TestRepositoryProfile:
    def test_valid_creation(self) -> None:
        p = _make_profile("test-repo")
        assert p.repository_id == "test-repo"
        assert p.name == "Test Repo"

    def test_empty_id_raises(self) -> None:
        with pytest.raises(ValueError, match="RepositoryProfile.repository_id"):
            RepositoryProfile(
                repository_id="",
                name="Name",
                protocol_version="1.0",
                overview="",
            )

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError, match="RepositoryProfile.name"):
            RepositoryProfile(
                repository_id="r",
                name="",
                protocol_version="1.0",
                overview="",
            )


class TestManifestCollection:
    def test_empty_collection(self) -> None:
        c = ManifestCollection()
        assert len(c.manifests) == 0
        assert len(c.versions) == 0
        assert len(c.profiles) == 0

    def test_duplicate_manifest_raises(self) -> None:
        m1 = _make_manifest("dup")
        m2 = _make_manifest("dup")
        with pytest.raises(ValueError, match="Duplicate manifest"):
            ManifestCollection(manifests=(m1, m2))

    def test_duplicate_version_raises(self) -> None:
        v1 = _make_version("dup")
        v2 = _make_version("dup")
        with pytest.raises(ValueError, match="Duplicate version"):
            ManifestCollection(versions=(v1, v2))

    def test_duplicate_profile_raises(self) -> None:
        p1 = _make_profile("dup")
        p2 = _make_profile("dup")
        with pytest.raises(ValueError, match="Duplicate profile"):
            ManifestCollection(profiles=(p1, p2))

    def test_get_manifest(self) -> None:
        m = _make_manifest("find-me")
        c = ManifestCollection(manifests=(m,))
        assert c.get_manifest("find-me") is m
        assert c.get_manifest("missing") is None

    def test_get_version(self) -> None:
        v = _make_version("find-me")
        c = ManifestCollection(versions=(v,))
        assert c.get_version("find-me") is v
        assert c.get_version("missing") is None

    def test_get_profile(self) -> None:
        p = _make_profile("find-me")
        c = ManifestCollection(profiles=(p,))
        assert c.get_profile("find-me") is p
        assert c.get_profile("missing") is None

    def test_repository_ids(self) -> None:
        m1 = _make_manifest("a")
        m2 = _make_manifest("b")
        c = ManifestCollection(manifests=(m1, m2))
        assert c.repository_ids == ("a", "b")
