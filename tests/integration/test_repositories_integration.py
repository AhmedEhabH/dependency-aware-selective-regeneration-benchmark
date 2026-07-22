from pathlib import Path

import pytest

from benchmark.repositories.loader import RepositoryLoader


@pytest.mark.skipif(
    not Path("benchmark_data/manifests/repositories.yaml").exists(),
    reason="benchmark_data not available in test environment",
)
class TestRealManifestLoading:
    def test_load_real_manifests(self) -> None:
        loader = RepositoryLoader(Path("benchmark_data"))
        collection = loader.load_manifest()
        assert len(collection.manifests) >= 1
        assert len(collection.versions) >= 1

    def test_todo_manifest_present(self) -> None:
        loader = RepositoryLoader(Path("benchmark_data"))
        collection = loader.load_manifest()
        manifest = collection.get_manifest("todo")
        assert manifest is not None
        assert manifest.architecture_style == "Layered REST"

    def test_djangocms_manifest_present(self) -> None:
        loader = RepositoryLoader(Path("benchmark_data"))
        collection = loader.load_manifest()
        manifest = collection.get_manifest("djangocms")
        assert manifest is not None
        assert manifest.size == "medium"

    def test_saleor_manifest_present(self) -> None:
        loader = RepositoryLoader(Path("benchmark_data"))
        collection = loader.load_manifest()
        manifest = collection.get_manifest("saleor")
        assert manifest is not None
        assert manifest.size == "large"

    def test_todo_profile_present(self) -> None:
        loader = RepositoryLoader(Path("benchmark_data"))
        collection = loader.load_manifest()
        profile = collection.get_profile("todo")
        assert profile is not None
        assert "Layered REST" in profile.architecture.get("style", "")
        assert len(profile.artifact_catalog) > 0

    def test_version_entries_have_shas(self) -> None:
        loader = RepositoryLoader(Path("benchmark_data"))
        collection = loader.load_manifest()
        for version in collection.versions:
            if version.repository_id == "todo":
                assert version.commit_sha == "TBD"
            else:
                assert version.commit_sha not in ("TBD", "", "unknown"), (
                    f"{version.repository_id} commit_sha is not resolved"
                )
