from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from benchmark.core.exceptions import RepositoryError
from benchmark.core.models import RepositoryIdentity, RepositorySnapshot
from benchmark.repositories.base import RepositoryLoaderBase
from benchmark.repositories.manifest import (
    ManifestCollection,
    RepositoryManifest,
    RepositoryProfile,
    RepositoryVersionEntry,
)


def _normalize_artifact_catalog(raw: Any) -> tuple[dict[str, Any], ...]:
    """Convert any supported ``artifact_catalog`` shape to canonical descriptors.

    Canonical entries are descriptor dictionaries carrying an ``id`` that is a
    repository-relative artifact path. Directory entries keep a trailing ``/``
    id and are expanded to concrete files by ``descriptors_from_profile``.

    Supported input shapes:
      - list/tuple of descriptor dicts with ``id`` (todo, canonical);
      - list/tuple of descriptor dicts with ``path`` (explicit file lists);
      - list/tuple of path strings;
      - mapping (django CMS shorthand and Saleor category mapping).

    Preserves the todo behavior exactly: its canonical list passes through
    unchanged. No Ground Truth enters here; the catalog is profile data only.
    """
    if isinstance(raw, dict):
        result: list[dict[str, Any]] = []
        for key, value in raw.items():
            if isinstance(value, str):
                result.append({"id": str(key), "description": value})
            elif isinstance(value, list):
                if all(isinstance(item, dict) for item in value):
                    for item in value:
                        item_path = item.get("path", "")
                        if not isinstance(item_path, str) or not item_path:
                            raise RepositoryError(
                                f"artifact_catalog mapping {key!r} has an entry "
                                f"without a valid 'path': {item!r}"
                            )
                        result.append({
                            "id": item_path,
                            "category": str(key),
                            "description": str(item.get("description", "")),
                        })
                else:
                    for item in value:
                        if isinstance(item, dict):
                            for name, desc in item.items():
                                result.append({
                                    "id": f"{key}{name}",
                                    "description": str(desc),
                                })
                        elif isinstance(item, str):
                            name, _, desc = item.partition(":")
                            result.append({
                                "id": f"{key}{name.strip()}",
                                "description": desc.strip(),
                            })
                        else:
                            raise RepositoryError(
                                f"artifact_catalog mapping {key!r} has an "
                                f"unsupported entry: {item!r}"
                            )
            else:
                raise RepositoryError(
                    f"artifact_catalog mapping {key!r} has an unsupported value "
                    f"of type {type(value).__name__}"
                )
        return tuple(result)

    if isinstance(raw, (list, tuple)):
        result = []
        for entry in raw:
            if isinstance(entry, dict):
                item = dict(entry)
                if "path" in item and "id" not in item:
                    item["id"] = item.pop("path")
                if not isinstance(item.get("id"), str) or not item.get("id"):
                    raise RepositoryError(
                        f"artifact_catalog entry has no valid 'id': {entry!r}"
                    )
                result.append(item)
            elif isinstance(entry, str):
                result.append({"id": entry})
            else:
                raise RepositoryError(
                    f"artifact_catalog has an unsupported entry: {entry!r}"
                )
        return tuple(result)

    raise RepositoryError(
        f"artifact_catalog must be a mapping or a sequence, got {type(raw).__name__}"
    )


class RepositoryLoader(RepositoryLoaderBase):
    def __init__(self, base_path: str | Path) -> None:
        self._base_path = Path(base_path)
        self._collection: ManifestCollection | None = None

    def _resolve_path(self, relative: str) -> Path:
        return self._base_path / relative

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise RepositoryError(f"File not found: {path}", context={"path": str(path)})
        if not path.is_file():
            raise RepositoryError(f"Path is not a file: {path}", context={"path": str(path)})
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError as e:
            raise RepositoryError(f"Failed to read file: {e}", context={"path": str(path)}) from e
        try:
            data = yaml.safe_load(raw)
        except yaml.YAMLError as e:
            raise RepositoryError(
                f"Failed to parse YAML: {e}", context={"path": str(path)}
            ) from e
        if not isinstance(data, dict):
            raise RepositoryError(
                f"YAML content must be a mapping, got {type(data).__name__}",
                context={"path": str(path)},
            )
        return data

    def load_manifest(self) -> ManifestCollection:
        manifests_path = self._resolve_path("manifests/repositories.yaml")
        versions_path = self._resolve_path("manifests/repository_versions.yaml")
        profiles_dir = self._resolve_path("repository_profiles")

        raw_manifests = self._load_yaml(manifests_path)
        raw_versions = self._load_yaml(versions_path)

        manifest_list: list[RepositoryManifest] = []
        repos_data = raw_manifests.get("repositories", {})
        if not isinstance(repos_data, dict):
            raise RepositoryError(
                "repositories.yaml must contain a 'repositories' mapping"
            )
        for repo_id, entry in repos_data.items():
            if not isinstance(entry, dict):
                raise RepositoryError(
                    f"Repository entry '{repo_id}' must be a mapping"
                )
            identity = RepositoryIdentity(
                name=repo_id,
                url=entry.get("url", ""),
            )
            manifest_list.append(
                RepositoryManifest(
                    identity=identity,
                    description=entry.get("description", ""),
                    architecture_style=entry.get("architecture_style", ""),
                    size=entry.get("size", ""),
                    language=entry.get("language", ""),
                    license_name=entry.get("license", ""),
                    license_url=entry.get("license_url", ""),
                    url=entry.get("url", ""),
                    default_branch=entry.get("default_branch", "main"),
                    test_runner=entry.get("test_runner", ""),
                    test_discovery=entry.get("test_discovery", ""),
                    build_system=entry.get("build_system", ""),
                    status=entry.get("status", ""),
                    protocol_eligibility=entry.get("protocol_eligibility", {}),
                )
            )

        version_list: list[RepositoryVersionEntry] = []
        versions_data = raw_versions.get("versions", {})
        if not isinstance(versions_data, dict):
            raise RepositoryError(
                "repository_versions.yaml must contain a 'versions' mapping"
            )
        for repo_id, entry in versions_data.items():
            if not isinstance(entry, dict):
                raise RepositoryError(
                    f"Version entry '{repo_id}' must be a mapping"
                )
            version_list.append(
                RepositoryVersionEntry(
                    repository_id=repo_id,
                    version=entry.get("version", ""),
                    version_type=entry.get("version_type", ""),
                    commit_sha=entry.get("commit_sha", ""),
                    commit_date=entry.get("commit_date", ""),
                    tag=entry.get("tag", ""),
                    release_date=entry.get("release_date", ""),
                    age_at_freeze_days=entry.get("age_at_freeze_days", 0),
                    da_03_compliant=entry.get("da_03_compliant", False),
                    branch=entry.get("branch", ""),
                    dependency_file=entry.get("dependency_file", ""),
                    python_version=entry.get("python_version", ""),
                    test_setup_verified=entry.get("test_setup_verified", "pending"),
                    notes=entry.get("notes", ""),
                )
            )

        profile_list: list[RepositoryProfile] = []
        if profiles_dir.is_dir():
            for profile_file in sorted(profiles_dir.glob("*.yaml")):
                raw_profile = self._load_yaml(profile_file)
                repo_id = (
                    raw_profile.get("repository_id")
                    or raw_profile.get("repository")
                    or profile_file.stem
                )
                profile_name = (
                    raw_profile.get("name")
                    or raw_profile.get("description")
                    or repo_id
                )
                raw_overview = raw_profile.get("overview", "")
                if isinstance(raw_overview, dict):
                    overview_str = str(raw_overview.get("purpose", raw_overview))
                else:
                    overview_str = str(raw_overview)
                raw_test_suite = raw_profile.get("test_suite_description", "")
                if isinstance(raw_test_suite, dict):
                    test_suite_str = str(raw_test_suite.get("description", raw_test_suite))
                else:
                    test_suite_str = str(raw_test_suite)
                profile_list.append(
                    RepositoryProfile(
                        repository_id=repo_id,
                        name=profile_name,
                        protocol_version=raw_profile.get("protocol_version", ""),
                        overview=overview_str,
                        architecture=raw_profile.get("architecture", {}),
                        artifact_catalog=_normalize_artifact_catalog(raw_profile.get("artifact_catalog", [])),
                        module_boundaries=tuple(raw_profile.get("module_boundaries", [])),
                        test_suite_description=test_suite_str,
                        architecture_boundaries=tuple(raw_profile.get("architecture_boundaries", [])),
                        known_limitations=tuple(raw_profile.get("known_limitations", [])),
                        artifact_universe=raw_profile.get("artifact_universe", {}),
                    )
                )

        self._collection = ManifestCollection(
            manifests=tuple(manifest_list),
            versions=tuple(version_list),
            profiles=tuple(profile_list),
        )
        return self._collection

    def load_manifest_only(self) -> ManifestCollection:
        return self.load_manifest()

    def resolve_identity(self, repo_id: str) -> RepositoryIdentity:
        if self._collection is None:
            self.load_manifest()
        if self._collection is None:
            raise RepositoryError("Failed to load manifest collection")
        manifest = self._collection.get_manifest(repo_id)
        if manifest is None:
            raise RepositoryError(f"Unknown repository: {repo_id}")
        return manifest.identity

    def resolve_snapshot(self, repo_id: str) -> RepositorySnapshot:
        if self._collection is None:
            self.load_manifest()
        if self._collection is None:
            raise RepositoryError("Failed to load manifest collection")
        identity = self._collection.get_manifest(repo_id)
        if identity is None:
            raise RepositoryError(f"Unknown repository: {repo_id}")
        version = self._collection.get_version(repo_id)
        commit_sha = version.commit_sha if version else "unknown"
        return RepositorySnapshot(
            identity=identity.identity,
            commit_sha=commit_sha,
            path=f"snapshots/{repo_id}",
        )

    @property
    def collection(self) -> ManifestCollection | None:
        return self._collection
