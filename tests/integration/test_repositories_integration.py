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
            assert version.commit_sha not in ("TBD", "", "unknown"), (
                f"{version.repository_id} commit_sha is not resolved"
            )

    def test_pilot_config_refs_match_manifest_shas(self) -> None:
        """Gate 2: configs/pilot.yaml repository refs equal frozen manifest SHAs."""
        from benchmark.config.loader import load_config

        loader = RepositoryLoader(Path("benchmark_data"))
        collection = loader.load_manifest()

        config = load_config(Path("configs/pilot.yaml"))
        assert len(config.repositories) == 3
        for repo in config.repositories:
            version = collection.get_version(repo.name)
            assert version is not None, f"no frozen version for {repo.name}"
            assert repo.ref == version.commit_sha, (
                f"{repo.name} pilot config ref {repo.ref!r} != manifest SHA "
                f"{version.commit_sha!r}"
            )

    def test_no_main_ref_in_pilot_config(self) -> None:
        """Gate 2: no floating 'main' ref remains in Pilot execution config."""
        from benchmark.config.loader import load_config

        config = load_config(Path("configs/pilot.yaml"))
        for repo in config.repositories:
            assert repo.ref != "main", f"{repo.name} still uses floating ref 'main'"

    def test_pilot_config_todo_url_canonical(self) -> None:
        """todo uses the established canonical project URI, not a placeholder."""
        from benchmark.config.loader import load_config

        config = load_config(Path("configs/pilot.yaml"))
        todo = next(r for r in config.repositories if r.name == "todo")
        assert "example" not in todo.url
        assert todo.url.startswith("https://github.com/")

    def test_pilot_repo_profiles_have_artifact_universe(self) -> None:
        """Regeneration strategies require a valid llm_editable artifact universe."""
        loader = RepositoryLoader(Path("benchmark_data"))
        collection = loader.load_manifest()
        for repo_id in ("todo", "djangocms", "saleor"):
            profile = collection.get_profile(repo_id)
            assert profile is not None, f"{repo_id} has no repository profile"
            au = profile.artifact_universe or {}
            editable = au.get("llm_editable")
            assert isinstance(editable, list) and len(editable) > 0, (
                f"{repo_id} profile has no non-empty llm_editable artifact universe"
            )
