from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from benchmark.core.models import RepositoryIdentity


@dataclass(frozen=True)
class RepositoryManifest:
    identity: RepositoryIdentity
    description: str
    architecture_style: str
    size: str
    language: str
    license_name: str
    license_url: str
    url: str
    default_branch: str
    test_runner: str
    test_discovery: str
    build_system: str
    status: str
    protocol_eligibility: dict[str, bool] = field(default_factory=dict)


@dataclass(frozen=True)
class RepositoryVersionEntry:
    repository_id: str
    version: str
    version_type: str
    commit_sha: str
    commit_date: str
    tag: str
    release_date: str
    age_at_freeze_days: int
    da_03_compliant: bool
    branch: str
    dependency_file: str
    python_version: str
    test_setup_verified: str = "pending"
    notes: str = ""


@dataclass(frozen=True)
class RepositoryProfile:
    repository_id: str
    name: str
    protocol_version: str
    overview: str
    architecture: dict[str, Any] = field(default_factory=dict)
    artifact_catalog: tuple[dict[str, Any], ...] = ()
    module_boundaries: tuple[dict[str, Any], ...] = ()
    test_suite_description: str = ""
    architecture_boundaries: tuple[dict[str, Any], ...] = ()
    known_limitations: tuple[dict[str, Any], ...] = ()
    artifact_universe: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.repository_id:
            raise ValueError("RepositoryProfile.repository_id must not be empty")
        if not self.name:
            raise ValueError("RepositoryProfile.name must not be empty")


@dataclass(frozen=True)
class ManifestCollection:
    manifests: tuple[RepositoryManifest, ...] = ()
    versions: tuple[RepositoryVersionEntry, ...] = ()
    profiles: tuple[RepositoryProfile, ...] = ()

    def __post_init__(self) -> None:
        seen_manifests: set[str] = set()
        for m in self.manifests:
            if m.identity.name in seen_manifests:
                raise ValueError(f"Duplicate manifest repository: {m.identity.name}")
            seen_manifests.add(m.identity.name)
        seen_versions: set[str] = set()
        for v in self.versions:
            if v.repository_id in seen_versions:
                raise ValueError(f"Duplicate version entry: {v.repository_id}")
            seen_versions.add(v.repository_id)
        seen_profiles: set[str] = set()
        for p in self.profiles:
            if p.repository_id in seen_profiles:
                raise ValueError(f"Duplicate profile: {p.repository_id}")
            seen_profiles.add(p.repository_id)

    def get_manifest(self, repo_id: str) -> RepositoryManifest | None:
        for m in self.manifests:
            if m.identity.name == repo_id:
                return m
        return None

    def get_version(self, repo_id: str) -> RepositoryVersionEntry | None:
        for v in self.versions:
            if v.repository_id == repo_id:
                return v
        return None

    def get_profile(self, repo_id: str) -> RepositoryProfile | None:
        for p in self.profiles:
            if p.repository_id == repo_id:
                return p
        return None

    @property
    def repository_ids(self) -> tuple[str, ...]:
        return tuple(m.identity.name for m in self.manifests)
