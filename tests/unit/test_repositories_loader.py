from pathlib import Path

import pytest
import yaml

from benchmark.core.exceptions import RepositoryError
from benchmark.repositories.loader import RepositoryLoader


class TestRepositoryLoader:
    def test_init(self, tmp_path: Path) -> None:
        loader = RepositoryLoader(tmp_path)
        assert loader.collection is None

    def test_resolve_identity_before_load_raises(self, tmp_path: Path) -> None:
        loader = RepositoryLoader(tmp_path)
        with pytest.raises(RepositoryError, match="File not found"):
            loader.resolve_identity("nonexistent")

    def test_load_from_nonexistent_dir_raises(self, tmp_path: Path) -> None:
        loader = RepositoryLoader(tmp_path / "nonexistent")
        with pytest.raises(RepositoryError, match="not found"):
            loader.load_manifest()

    def test_load_manifest_missing_file_raises(self, tmp_path: Path) -> None:
        loader = RepositoryLoader(tmp_path)
        with pytest.raises(RepositoryError, match="not found"):
            loader.load_manifest()

    def test_load_with_invalid_yaml_raises(self, tmp_path: Path) -> None:
        manifests_dir = tmp_path / "manifests"
        manifests_dir.mkdir(parents=True)
        (manifests_dir / "repositories.yaml").write_text(": broken yaml [", encoding="utf-8")
        (manifests_dir / "repository_versions.yaml").write_text("versions: {}", encoding="utf-8")
        loader = RepositoryLoader(tmp_path)
        with pytest.raises(RepositoryError, match="Failed to parse"):
            loader.load_manifest()

    def test_load_with_scalar_yaml_raises(self, tmp_path: Path) -> None:
        manifests_dir = tmp_path / "manifests"
        manifests_dir.mkdir(parents=True)
        (manifests_dir / "repositories.yaml").write_text("just a string", encoding="utf-8")
        (manifests_dir / "repository_versions.yaml").write_text("versions: {}", encoding="utf-8")
        loader = RepositoryLoader(tmp_path)
        with pytest.raises(RepositoryError, match="must be a mapping"):
            loader.load_manifest()

    def test_successful_load(self, tmp_path: Path) -> None:
        manifests_dir = tmp_path / "manifests"
        profiles_dir = tmp_path / "repository_profiles"
        manifests_dir.mkdir(parents=True)
        profiles_dir.mkdir(parents=True)

        repos_yaml = {
            "repositories": {
                "todo": {
                    "id": "todo",
                    "name": "Todo App",
                    "description": "A todo app",
                    "architecture_style": "Layered REST",
                    "size": "small",
                    "language": "Python",
                    "license": "MIT",
                    "license_url": "https://opensource.org/licenses/MIT",
                    "url": "https://github.com/example/todo",
                    "default_branch": "main",
                    "test_runner": "pytest",
                    "test_discovery": "python -m pytest",
                    "build_system": "pip",
                    "status": "confirmatory",
                    "protocol_eligibility": {"da_01": True, "da_03": True},
                }
            }
        }
        (manifests_dir / "repositories.yaml").write_text(
            yaml.dump(repos_yaml), encoding="utf-8"
        )

        versions_yaml = {
            "versions": {
                "todo": {
                    "version": "1.0.0",
                    "version_type": "stable",
                    "commit_sha": "abc123",
                    "commit_date": "2026-01-01",
                    "tag": "v1.0.0",
                    "release_date": "2026-01-01",
                    "age_at_freeze_days": 200,
                    "da_03_compliant": True,
                    "branch": "main",
                    "dependency_file": "requirements.txt",
                    "python_version": ">=3.10",
                    "test_setup_verified": "verified",
                    "notes": "Test note",
                }
            }
        }
        (manifests_dir / "repository_versions.yaml").write_text(
            yaml.dump(versions_yaml), encoding="utf-8"
        )

        profile_yaml = {
            "repository_id": "todo",
            "name": "Todo App",
            "protocol_version": "1.0",
            "overview": "A test repo overview",
        }
        (profiles_dir / "todo.yaml").write_text(
            yaml.dump(profile_yaml), encoding="utf-8"
        )

        loader = RepositoryLoader(tmp_path)
        collection = loader.load_manifest()

        assert len(collection.manifests) == 1
        assert collection.manifests[0].identity.name == "todo"
        assert len(collection.versions) == 1
        assert collection.versions[0].repository_id == "todo"
        assert len(collection.profiles) == 1
        assert collection.profiles[0].repository_id == "todo"

    def test_resolve_identity_after_load(self, tmp_path: Path) -> None:
        manifests_dir = tmp_path / "manifests"
        manifests_dir.mkdir(parents=True)

        repos_yaml = {
            "repositories": {
                "todo": {
                    "id": "todo",
                    "name": "Todo App",
                    "description": "A todo app",
                    "architecture_style": "Layered REST",
                    "size": "small",
                    "language": "Python",
                    "license": "MIT",
                    "license_url": "https://opensource.org/licenses/MIT",
                    "url": "https://github.com/example/todo",
                    "default_branch": "main",
                    "test_runner": "pytest",
                    "test_discovery": "python -m pytest",
                    "build_system": "pip",
                    "status": "confirmatory",
                    "protocol_eligibility": {"da_01": True, "da_03": True},
                }
            }
        }
        (manifests_dir / "repositories.yaml").write_text(
            yaml.dump(repos_yaml), encoding="utf-8"
        )
        (manifests_dir / "repository_versions.yaml").write_text(
            "versions: {}", encoding="utf-8"
        )

        loader = RepositoryLoader(tmp_path)
        identity = loader.resolve_identity("todo")
        assert identity.name == "todo"
        assert identity.url == "https://github.com/example/todo"

    def test_resolve_unknown_identity_raises(self, tmp_path: Path) -> None:
        manifests_dir = tmp_path / "manifests"
        manifests_dir.mkdir(parents=True)
        (manifests_dir / "repositories.yaml").write_text(
            "repositories: {}", encoding="utf-8"
        )
        (manifests_dir / "repository_versions.yaml").write_text(
            "versions: {}", encoding="utf-8"
        )

        loader = RepositoryLoader(tmp_path)
        with pytest.raises(RepositoryError, match="Unknown repository"):
            loader.resolve_identity("unknown")
