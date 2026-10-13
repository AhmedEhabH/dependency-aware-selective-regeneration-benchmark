"""M17_D7_R4_E2 — bounded official PyPI acquisition of 28 exact pylint wheels.

Mission ``M17_D7_R4_E2_PYLINT_OFFICIAL_PYPI_ACQUISITION`` (class T3, owner
authorized).  This driver acquires EXACTLY the 28 pylint identities frozen by
the E1 plan (``research/env-canon-r4/R4_E1_PYLINT_RECOVERY_PLAN.json``) from the
two official allowlisted origins:

* metadata: ``https://pypi.org/pypi/pylint/<EXACT_VERSION>/json``
* artifacts: ``https://files.pythonhosted.org/``

Design rules (fail closed, no scientific knobs):

* exact allowlist only — any other package/version FAILS;
* metadata host allowlist ``pypi.org``, artifact host allowlist
  ``files.pythonhosted.org`` — any other host FAILS;
* no dependency resolver, no ``pip install``, no ``pip download``, no arbitrary
  URL, no sdist auto-fallback;
* wheel compatibility authority is R4-A
  (``benchmark.wp2.env_r4.wheel_tags`` behind the frozen shared interface);
* selection is deterministic; yanked releases and "no compatible wheel" both
  STOP for owner review;
* every downloaded wheel is verified (SHA-256, structural filename, canonical
  name, exact version, R4-A, ZIP integrity, path safety, METADATA identity)
  BEFORE promotion;
* promotion is additive into the R4-E overlay only; the frozen py39 wheelhouse
  and its manifest are never touched.

Transport policy: HTTPS with TLS verification; retry is transport-only
(maximum 2 additional attempts per request, transient/5xx/timeout only; never
on semantic failures such as 404, yanked, wrong metadata, hash mismatch).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import time
import urllib.error
import urllib.request
import zipfile
from collections.abc import Callable
from dataclasses import dataclass, field
from email.parser import Parser as _EmailParser
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from packaging.utils import parse_wheel_filename

from benchmark.wp2.env_r4.contracts import (
    RuntimeTarget,
    bind_lock_parser,
    normalize_name,
)
from benchmark.wp2.env_r4.contracts import (
    wheel_compatible as _interface_wheel_compatible,
)

# ---------------------------------------------------------------------------
# Frozen mission constants
# ---------------------------------------------------------------------------

MISSION_ID = "M17_D7_R4_E2_PYLINT_OFFICIAL_PYPI_ACQUISITION"
PACKAGE = "pylint"
METADATA_HOST = "pypi.org"
ARTIFACT_HOST = "files.pythonhosted.org"
METADATA_TEMPLATE = "https://pypi.org/pypi/{name}/{version}/json"
TARGET = RuntimeTarget(
    python_version="3.9",
    implementation="cpython",
    platform="linux",
    architecture="x86_64",
)

REQUIRED_IDENTITIES: tuple[tuple[str, str], ...] = (
    ("pylint", "2.7.2"),
    ("pylint", "2.7.4"),
    ("pylint", "2.8.1"),
    ("pylint", "2.8.2"),
    ("pylint", "2.9.5"),
    ("pylint", "2.9.6"),
    ("pylint", "2.10.2"),
    ("pylint", "2.11.1"),
    ("pylint", "2.12.2"),
    ("pylint", "2.13.4"),
    ("pylint", "2.13.5"),
    ("pylint", "2.13.8"),
    ("pylint", "2.13.9"),
    ("pylint", "2.14.3"),
    ("pylint", "2.14.5"),
    ("pylint", "2.15.2"),
    ("pylint", "2.15.3"),
    ("pylint", "2.15.4"),
    ("pylint", "2.15.5"),
    ("pylint", "2.15.8"),
    ("pylint", "2.15.10"),
    ("pylint", "2.16.1"),
    ("pylint", "2.17.1"),
    ("pylint", "2.17.2"),
    ("pylint", "2.17.3"),
    ("pylint", "2.17.4"),
    ("pylint", "2.17.5"),
    ("pylint", "2.17.7"),
)

STORAGE_ROOT = Path(r"D:\wp2_env_store\recovery\r4e_pylint_py39")
STAGING = STORAGE_ROOT / "staging"
WHEELS = STORAGE_ROOT / "wheels"
MANIFESTS = STORAGE_ROOT / "manifests"
MANIFEST_FILE = MANIFESTS / "R4_E2_PYLINT_ACQUISITION_MANIFEST.json"

FROZEN_WHEELHOUSE = Path(r"D:\wp2_env_store\wheelhouse\py39")
FROZEN_MANIFEST = Path(r"D:\wp2_env_store\manifests\WHEELHOUSE_HASHES_py39.json")

TRANSIENT_HTTP_STATUS = frozenset({500, 502, 503, 504})
MAX_RETRIES = 2
RETRY_BASE_DELAY_S = 1.5
REQUEST_TIMEOUT_S = 60.0

RECEIPT_PATH = Path("research") / "env-canon-r4" / "R4_E2_PYLINT_ACQUISITION_RECEIPT.json"
SUMMARY_PATH = Path("research") / "env-canon-r4" / "R4_E2_PYLINT_ACQUISITION_SUMMARY.md"


class AcquisitionError(Exception):
    """Any fail-closed acquisition gate failure (drives a STOP)."""


class StopOwnerReviewError(Exception):
    """A yanked release or a missing compatible wheel — owner decision required."""


class _TransientError(Exception):
    """Internal: a transport-level retryable failure."""


# ---------------------------------------------------------------------------
# Pure allowlist / URL guards
# ---------------------------------------------------------------------------


def is_exact_identity(name: str, version: str) -> bool:
    """Exactly one of the frozen 28 identities; fail closed otherwise."""
    return normalize_name(name) == PACKAGE and (name, version) in REQUIRED_IDENTITIES


def assert_exact_identity(name: str, version: str) -> None:
    if not is_exact_identity(name, version):
        raise AcquisitionError(f"identity not in exact allowlist: {name}=={version}")


def _host_of(url: str) -> str:
    from urllib.parse import urlparse

    return (urlparse(url).hostname or "").lower()


def is_allowed_metadata_url(url: str) -> bool:
    """Only the official PyPI metadata origin (https, exact host)."""
    if not url.startswith("https://"):
        return False
    return _host_of(url) == METADATA_HOST


def is_allowed_artifact_url(url: str) -> bool:
    """Only the official artifact origin (https, exact host)."""
    if not url.startswith("https://"):
        return False
    return _host_of(url) == ARTIFACT_HOST


def metadata_url(name: str, version: str) -> str:
    assert_exact_identity(name, version)
    return METADATA_TEMPLATE.format(name=name, version=version)


# ---------------------------------------------------------------------------
# Wheel filename structural parsing
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParsedWheel:
    filename: str
    distribution: str
    version: str
    build: tuple[str, ...] | None
    tags: frozenset[str]

    @property
    def is_pure_python(self) -> bool:
        return self.tags == frozenset({"py3-none-any"})


def parse_wheel_filename_structurally(filename: str) -> ParsedWheel:
    """Parse a wheel filename strictly; malformed -> AcquisitionError."""
    if not filename.endswith(".whl"):
        raise AcquisitionError(f"not a wheel filename: {filename!r}")
    try:
        dist_name, version, build, tags = parse_wheel_filename(filename)
    except Exception as exc:
        raise AcquisitionError(f"unparseable wheel filename {filename!r}: {exc}") from exc
    tag_strings = frozenset(str(t) for t in tags)
    build_parts = tuple(str(part) for part in build) if build else None
    return ParsedWheel(
        filename=filename,
        distribution=str(dist_name),
        version=str(version),
        build=build_parts,
        tags=tag_strings,
    )


# ---------------------------------------------------------------------------
# Metadata -> deterministic wheel selection (pure)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WheelCandidate:
    filename: str
    url: str
    sha256: str | None
    size: int | None
    upload_time: str | None
    upload_time_iso_8601: str | None
    yanked: bool
    yanked_reason: str | None
    packagetype: str
    tags: frozenset[str]
    is_pure_python: bool


@dataclass(frozen=True)
class SelectedArtifact:
    package: str
    version: str
    filename: str
    url: str
    expected_sha256: str
    size: int
    upload_time: str | None
    upload_time_iso_8601: str | None
    yanked: bool
    yanked_reason: str | None
    wheel_tags: str
    metadata_url: str
    rationale: str
    candidates_considered: tuple[dict[str, Any], ...]


def _release_urls(release_meta: dict[str, Any]) -> list[dict[str, Any]]:
    urls = release_meta.get("urls")
    if not isinstance(urls, list):
        raise AcquisitionError("release metadata missing 'urls' list (fail closed)")
    return urls


def select_wheel(
    release_meta: dict[str, Any],
    package: str,
    version: str,
    compat_fn: Callable[[str, RuntimeTarget], bool],
    target: RuntimeTarget = TARGET,
) -> SelectedArtifact:
    """Deterministically select the exact official compatible wheel.

    Prefers a pure-Python (``py3-none-any``) wheel; otherwise the first
    R4-A-compatible wheel in deterministic filename order.  A release whose
    exact version is absent, a release with no compatible wheel, and a release
    where every compatible wheel is yanked all raise :class:`StopOwnerReviewError`.
    """
    assert_exact_identity(package, version)
    if not isinstance(release_meta, dict):
        raise AcquisitionError("release metadata is not a JSON object (fail closed)")

    candidates: list[WheelCandidate] = []
    yanked_compatible: list[WheelCandidate] = []
    considered: list[dict[str, Any]] = []

    for entry in _release_urls(release_meta):
        if not isinstance(entry, dict):
            continue
        filename = entry.get("filename")
        packagetype = entry.get("packagetype")
        if not isinstance(filename, str) or not filename.endswith(".whl"):
            continue
        try:
            parsed = parse_wheel_filename_structurally(filename)
        except AcquisitionError:
            considered.append({"filename": filename, "parsed": False, "reason": "unparseable"})
            continue
        considered.append(
            {
                "filename": filename,
                "distribution": parsed.distribution,
                "version": parsed.version,
                "yanked": bool(entry.get("yanked", False)),
            }
        )
        if parsed.distribution != normalize_name(package):
            continue
        if parsed.version != version:
            continue
        if not compat_fn(filename, target):
            continue
        candidate = WheelCandidate(
            filename=filename,
            url=str(entry.get("url", "")),
            sha256=str((entry.get("digests") or {}).get("sha256") or "") or None,
            size=entry.get("size"),
            upload_time=entry.get("upload_time"),
            upload_time_iso_8601=entry.get("upload_time_iso_8601"),
            yanked=bool(entry.get("yanked", False)),
            yanked_reason=entry.get("yanked_reason"),
            packagetype=packagetype or "bdist_wheel",
            tags=parsed.tags,
            is_pure_python=parsed.is_pure_python,
        )
        if candidate.yanked:
            yanked_compatible.append(candidate)
        else:
            candidates.append(candidate)

    if not candidates and not yanked_compatible:
        raise StopOwnerReviewError(
            f"pylint=={version}: no official wheel for the exact version "
            f"(candidates considered: {json.dumps(considered)})"
        )
    if not candidates:
        raise StopOwnerReviewError(
            f"pylint=={version}: every compatible official wheel is yanked "
            f"(yanked_reason={yanked_compatible[0].yanked_reason!r})"
        )

    ordered = sorted(
        candidates,
        key=lambda c: (0 if c.is_pure_python else 1, c.filename),
    )
    selected = ordered[0]
    if not selected.url or not is_allowed_artifact_url(selected.url):
        raise AcquisitionError(
            f"pylint=={version}: selected wheel url not on allowed artifact host: "
            f"{selected.url!r}"
        )
    if not selected.sha256:
        raise AcquisitionError(f"pylint=={version}: official SHA-256 missing for {selected.filename!r}")
    rationale = (
        "prefer pure-Python py3-none-any official wheel (R4-A compatible)"
        if selected.is_pure_python
        else "first deterministic R4-A-compatible official wheel"
    )
    return SelectedArtifact(
        package=package,
        version=version,
        filename=selected.filename,
        url=selected.url,
        expected_sha256=selected.sha256,
        size=selected.size or 0,
        upload_time=selected.upload_time,
        upload_time_iso_8601=selected.upload_time_iso_8601,
        yanked=False,
        yanked_reason=None,
        wheel_tags=",".join(sorted(selected.tags)),
        metadata_url=metadata_url(package, version),
        rationale=rationale,
        candidates_considered=tuple(considered),
    )


# ---------------------------------------------------------------------------
# Downloaded wheel verification (13 gates, pure over local bytes)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VerificationResult:
    filename: str
    version: str
    url: str
    expected_sha256: str
    actual_sha256: str
    byte_size: int
    checks: dict[str, bool]
    wheel_tags: str
    metadata_name: str | None
    metadata_version: str | None

    @property
    def passed(self) -> bool:
        return all(self.checks.values())

    def as_manifest_block(self) -> dict[str, Any]:
        return {
            "url_host_allowed": self.checks["url_host_allowed"],
            "official_sha256_present": self.checks["official_sha256_present"],
            "downloaded_sha256_matches": self.checks["downloaded_sha256_matches"],
            "filename_structural": self.checks["filename_structural"],
            "canonical_name_equals_pylint": self.checks["canonical_name_equals_pylint"],
            "exact_version": self.checks["exact_version"],
            "r4a_compatibility": self.checks["r4a_compatibility"],
            "zip_integrity": self.checks["zip_integrity"],
            "no_absolute_paths": self.checks["no_absolute_paths"],
            "no_dotdot_traversal": self.checks["no_dotdot_traversal"],
            "exactly_one_distinfo_metadata": self.checks["exactly_one_distinfo_metadata"],
            "metadata_name_canonical_pylint": self.checks["metadata_name_canonical_pylint"],
            "metadata_version_exact": self.checks["metadata_version_exact"],
        }


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _zip_safety(names: list[str]) -> tuple[bool, bool, str]:
    absolute_bad: list[str] = []
    dotdot_bad: list[str] = []
    for name in names:
        stripped = name.rstrip("/")
        if stripped.startswith("/") or stripped.startswith("\\"):
            absolute_bad.append(name)
            continue
        if len(stripped) >= 2 and stripped[1] == ":" and stripped[0].isalpha():
            absolute_bad.append(name)
            continue
        parts = stripped.split("/")
        if any(part == ".." or part == "." for part in parts):
            dotdot_bad.append(name)
    return not absolute_bad, not dotdot_bad, json.dumps({"absolute": absolute_bad, "dotdot": dotdot_bad})


def _read_distinfo_metadata(data: bytes) -> tuple[bool, str | None, str | None, str | None]:
    """Extract exactly one relevant ``*.dist-info/METADATA``; never imports code."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = zf.namelist()
    except Exception as exc:
        return False, None, None, f"zip open failed: {exc!r}"
    metadata_entries = [n for n in names if n.count("/") == 1 and n.endswith(".dist-info/METADATA")]
    if len(metadata_entries) != 1:
        return False, None, None, f"expected exactly one dist-info/METADATA, got {len(metadata_entries)}"
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            raw = zf.read(metadata_entries[0])
    except Exception as exc:
        return False, None, None, f"metadata read failed: {exc!r}"
    try:
        msg = _EmailParser().parsestr(raw.decode("utf-8", errors="replace"))
    except Exception as exc:
        return False, None, None, f"metadata parse failed: {exc!r}"
    name = msg.get("Name")
    version = msg.get("Version")
    return True, name, version, metadata_entries[0]


def verify_wheel_bytes(
    data: bytes,
    *,
    url: str,
    expected_sha256: str,
    package: str,
    version: str,
    filename: str,
    compat_fn: Callable[[str, RuntimeTarget], bool],
    target: RuntimeTarget = TARGET,
) -> VerificationResult:
    """Run all 13 E2-F verification gates over the downloaded bytes."""
    checks: dict[str, bool] = {}
    actual = _sha256_bytes(data)

    checks["url_host_allowed"] = is_allowed_artifact_url(url)
    checks["official_sha256_present"] = bool(expected_sha256)
    checks["downloaded_sha256_matches"] = actual == expected_sha256
    try:
        parsed = parse_wheel_filename_structurally(filename)
        checks["filename_structural"] = True
    except AcquisitionError:
        parsed = None
        checks["filename_structural"] = False
    if parsed is not None:
        checks["canonical_name_equals_pylint"] = parsed.distribution == normalize_name(package)
        checks["exact_version"] = parsed.version == version
    else:
        checks["canonical_name_equals_pylint"] = False
        checks["exact_version"] = False
    checks["r4a_compatibility"] = compat_fn(filename, target) if parsed is not None else False

    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            zip_bad = zf.testzip()
        checks["zip_integrity"] = zip_bad is None
    except Exception:
        checks["zip_integrity"] = False

    names_ok: tuple[bool, bool, str] = (False, False, "")
    if checks["zip_integrity"]:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                names_ok = _zip_safety(zf.namelist())
        except Exception:
            names_ok = (False, False, "")
    checks["no_absolute_paths"] = names_ok[0]
    checks["no_dotdot_traversal"] = names_ok[1]

    metadata_ok, meta_name, meta_version, _ = _read_distinfo_metadata(data)
    checks["exactly_one_distinfo_metadata"] = metadata_ok
    checks["metadata_name_canonical_pylint"] = bool(meta_name) and normalize_name(meta_name) == normalize_name(package)
    checks["metadata_version_exact"] = bool(meta_version) and meta_version == version

    wheel_tags = ",".join(sorted(parsed.tags)) if parsed is not None else ""
    return VerificationResult(
        filename=filename,
        version=version,
        url=url,
        expected_sha256=expected_sha256,
        actual_sha256=actual,
        byte_size=len(data),
        checks=checks,
        wheel_tags=wheel_tags,
        metadata_name=meta_name,
        metadata_version=meta_version,
    )


# ---------------------------------------------------------------------------
# Transport (network boundary, mockable)
# ---------------------------------------------------------------------------


@runtime_checkable
class Transport(Protocol):
    def get_bytes(self, url: str) -> tuple[int, bytes]: ...

    def download(self, url: str) -> tuple[int, bytes]: ...


@dataclass
class RetryRecord:
    url: str
    attempt: int
    reason: str


@dataclass
class NetworkStats:
    metadata_requests: int = 0
    artifact_requests: int = 0
    downloaded_bytes: int = 0
    retries: list[RetryRecord] = field(default_factory=list)


class RealTransport:
    """HTTPS transport with bounded transport-only retry (no semantic retry)."""

    def __init__(self, stats: NetworkStats) -> None:
        self._stats = stats

    def get_bytes(self, url: str) -> tuple[int, bytes]:
        return self._request(url, count_metadata=True)

    def download(self, url: str) -> tuple[int, bytes]:
        return self._request(url, count_metadata=False)

    def _request(self, url: str, *, count_metadata: bool) -> tuple[int, bytes]:
        if not url.startswith("https://"):
            raise AcquisitionError(f"refusing non-https url {url!r}")
        for attempt in range(1, 1 + MAX_RETRIES + 1):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "r4-e2-pylint-recovery/1.0"})
                with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_S) as resp:
                    code = resp.status
                    data = resp.read()
                if code in TRANSIENT_HTTP_STATUS:
                    raise _TransientError(f"http {code}")
                if code >= 400:
                    raise AcquisitionError(f"http {code} for {url}")
                if count_metadata:
                    self._stats.metadata_requests += 1
                else:
                    self._stats.artifact_requests += 1
                    self._stats.downloaded_bytes += len(data)
                return code, data
            except _TransientError as exc:
                if attempt > MAX_RETRIES:
                    raise AcquisitionError(f"transport retries exhausted for {url}: {exc}") from exc
                self._stats.retries.append(RetryRecord(url=url, attempt=attempt, reason=str(exc)))
                time.sleep(RETRY_BASE_DELAY_S * attempt)
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
                if isinstance(exc, urllib.error.HTTPError) and exc.code not in TRANSIENT_HTTP_STATUS:
                    raise AcquisitionError(f"http {exc.code} for {url}") from exc
                if attempt > MAX_RETRIES:
                    raise AcquisitionError(f"transport retries exhausted for {url}: {exc}") from exc
                self._stats.retries.append(RetryRecord(url=url, attempt=attempt, reason=str(exc)))
                time.sleep(RETRY_BASE_DELAY_S * attempt)
        raise AcquisitionError(f"unreachable transport loop exit for {url}")


# ---------------------------------------------------------------------------
# Orchestration driver
# ---------------------------------------------------------------------------


@dataclass
class AcquisitionDriver:
    staging: Path = STAGING
    wheels: Path = WHEELS
    manifests: Path = MANIFESTS
    target: RuntimeTarget = TARGET
    transport: Transport | None = None
    stats: NetworkStats = field(default_factory=NetworkStats)
    compat_fn: Callable[[str, RuntimeTarget], bool] = _interface_wheel_compatible

    def __post_init__(self) -> None:
        if self.transport is None:
            self.transport = RealTransport(self.stats)

    # -- E2-D ---------------------------------------------------------------
    def discover(self) -> list[SelectedArtifact]:
        assert isinstance(self.transport, Transport)
        artifacts: list[SelectedArtifact] = []
        for package, version in REQUIRED_IDENTITIES:
            url = metadata_url(package, version)
            code, data = self.transport.get_bytes(url)
            if code != 200:
                raise AcquisitionError(f"metadata http {code} for {url}")
            try:
                release_meta = json.loads(data.decode("utf-8"))
            except Exception as exc:
                raise AcquisitionError(f"invalid metadata JSON for {url}: {exc}") from exc
            artifacts.append(select_wheel(release_meta, package, version, self.compat_fn, self.target))
        return artifacts

    # -- E2-E ---------------------------------------------------------------
    def download_all(self, artifacts: list[SelectedArtifact]) -> list[Path]:
        assert isinstance(self.transport, Transport)
        self.staging.mkdir(parents=True, exist_ok=True)
        paths: list[Path] = []
        for art in artifacts:
            code, data = self.transport.download(art.url)
            if code != 200:
                raise AcquisitionError(f"artifact http {code} for {art.url}")
            dest = self.staging / art.filename
            dest.write_bytes(data)
            paths.append(dest)
        return paths

    # -- E2-F ---------------------------------------------------------------
    def verify_all(self, artifacts: list[SelectedArtifact]) -> list[VerificationResult]:
        results: list[VerificationResult] = []
        for art in artifacts:
            data = (self.staging / art.filename).read_bytes()
            results.append(
                verify_wheel_bytes(
                    data,
                    url=art.url,
                    expected_sha256=art.expected_sha256,
                    package=art.package,
                    version=art.version,
                    filename=art.filename,
                    compat_fn=self.compat_fn,
                    target=self.target,
                )
            )
        return results

    # -- E2-G ---------------------------------------------------------------
    def promote_all(
        self, artifacts: list[SelectedArtifact], verified: list[VerificationResult]
    ) -> list[dict[str, Any]]:
        self.wheels.mkdir(parents=True, exist_ok=True)
        promoted: list[dict[str, Any]] = []
        for art, res in zip(artifacts, verified, strict=True):
            if not res.passed:
                raise AcquisitionError(f"refusing to promote unverified artifact {art.filename}")
            staging_path = self.staging / art.filename
            final_path = self.wheels / art.filename
            if final_path.exists():
                existing = _sha256_bytes(final_path.read_bytes())
                if existing != res.actual_sha256:
                    raise AcquisitionError(
                        f"overwrite refused: {final_path} exists and differs (no-overwrite rule)"
                    )
            else:
                final_path.write_bytes(staging_path.read_bytes())
            promoted.append(
                {
                    "package": art.package,
                    "version": art.version,
                    "filename": art.filename,
                    "staging_path": str(staging_path),
                    "final_overlay_path": str(final_path),
                    "promoted": True,
                }
            )
        return promoted

    # -- E2-H ---------------------------------------------------------------
    def build_manifest(
        self,
        artifacts: list[SelectedArtifact],
        verified: list[VerificationResult],
        promoted: list[dict[str, Any]],
    ) -> dict[str, Any]:
        entries: list[dict[str, Any]] = []
        prom = {p["filename"]: p for p in promoted}
        for art, res in zip(artifacts, verified, strict=True):
            p = prom.get(art.filename, {})
            entries.append(
                {
                    "package": art.package,
                    "version": art.version,
                    "filename": art.filename,
                    "metadata_url": art.metadata_url,
                    "artifact_url": art.url,
                    "yanked": art.yanked,
                    "yanked_reason": art.yanked_reason,
                    "upload_time": art.upload_time,
                    "upload_time_iso_8601": art.upload_time_iso_8601,
                    "expected_sha256": art.expected_sha256,
                    "actual_sha256": res.actual_sha256,
                    "byte_size": res.byte_size,
                    "wheel_tags": res.wheel_tags,
                    "r4a_compatibility": res.checks["r4a_compatibility"],
                    "zip_integrity": res.checks["zip_integrity"],
                    "archive_path_safety": {
                        "no_absolute_paths": res.checks["no_absolute_paths"],
                        "no_dotdot_traversal": res.checks["no_dotdot_traversal"],
                    },
                    "metadata_name": res.metadata_name,
                    "metadata_version": res.metadata_version,
                    "staging_path": str(self.staging / art.filename),
                    "final_overlay_path": p.get("final_overlay_path"),
                    "promoted": bool(p.get("promoted", False)),
                    "selection_rationale": art.rationale,
                }
            )
        manifest: dict[str, Any] = {
            "schema_version": "env-canon-r4-e2/1.0",
            "mission_id": MISSION_ID,
            "target": {
                "python_version": self.target.python_version,
                "implementation": self.target.implementation,
                "platform": self.target.platform,
                "architecture": self.target.architecture,
            },
            "origins": {
                "metadata_host": METADATA_HOST,
                "artifact_host": ARTIFACT_HOST,
            },
            "network": {
                "metadata_request_count": self.stats.metadata_requests,
                "artifact_request_count": self.stats.artifact_requests,
                "downloaded_bytes": self.stats.downloaded_bytes,
                "downloaded_mib": round(self.stats.downloaded_bytes / (1024 * 1024), 6),
                "downloaded_gib": round(self.stats.downloaded_bytes / (1024 * 1024 * 1024), 9),
                "retries": [
                    {"url": r.url, "attempt": r.attempt, "reason": r.reason}
                    for r in self.stats.retries
                ],
            },
            "dependency_downloads": 0,
            "frozen_wheelhouse_mutation": False,
            "counts": {
                "requested": len(REQUIRED_IDENTITIES),
                "metadata_resolved": len(artifacts),
                "wheels_selected": len(artifacts),
                "downloaded": len(artifacts),
                "verified": sum(1 for r in verified if r.passed),
                "promoted": sum(1 for p in promoted if p.get("promoted")),
            },
            "artifacts": entries,
        }
        return manifest

    def write_manifest(self, manifest: dict[str, Any]) -> Path:
        self.manifests.mkdir(parents=True, exist_ok=True)
        MANIFEST_FILE.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return MANIFEST_FILE


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _bind_r4a() -> None:
    from benchmark.wp2.env_r4.integrated_parser import IntegratedR4Parser

    bind_lock_parser(IntegratedR4Parser())


def _artifact_to_dict(art: SelectedArtifact) -> dict[str, Any]:
    return {
        "package": art.package,
        "version": art.version,
        "filename": art.filename,
        "url": art.url,
        "expected_sha256": art.expected_sha256,
        "size": art.size,
        "upload_time": art.upload_time,
        "upload_time_iso_8601": art.upload_time_iso_8601,
        "yanked": art.yanked,
        "yanked_reason": art.yanked_reason,
        "wheel_tags": art.wheel_tags,
        "metadata_url": art.metadata_url,
        "rationale": art.rationale,
        "candidates_considered": list(art.candidates_considered),
    }


def _artifact_from_dict(data: dict[str, Any]) -> SelectedArtifact:
    return SelectedArtifact(
        package=str(data["package"]),
        version=str(data["version"]),
        filename=str(data["filename"]),
        url=str(data["url"]),
        expected_sha256=str(data["expected_sha256"]),
        size=int(data.get("size") or 0),
        upload_time=data.get("upload_time"),
        upload_time_iso_8601=data.get("upload_time_iso_8601"),
        yanked=bool(data.get("yanked", False)),
        yanked_reason=data.get("yanked_reason"),
        wheel_tags=str(data["wheel_tags"]),
        metadata_url=str(data["metadata_url"]),
        rationale=str(data.get("rationale", "")),
        candidates_considered=tuple(data.get("candidates_considered") or []),
    )


def _state_path(manifests: Path) -> Path:
    return manifests / "R4_E2_PYLINT_SELECTIONS_STATE.json"


def _load_state(manifests: Path) -> list[SelectedArtifact]:
    state = _state_path(manifests)
    if not state.is_file():
        raise AcquisitionError(f"no selection state file: {state} (run --phase discover first)")
    return [_artifact_from_dict(item) for item in json.loads(state.read_text(encoding="utf-8"))]


def main() -> int:
    ap = argparse.ArgumentParser(description="R4-E2 pylint official PyPI acquisition (bounded)")
    ap.add_argument(
        "--phase",
        choices=["discover", "download", "verify", "promote", "manifest", "all"],
        default=None,
        help="run a single atomic DAG phase; 'all' runs the full DAG",
    )
    ap.add_argument("--staging", default=str(STAGING))
    ap.add_argument("--wheels", default=str(WHEELS))
    ap.add_argument("--manifests", default=str(MANIFESTS))
    ap.add_argument("--manifest-out", default=str(MANIFEST_FILE))
    ap.add_argument("--report-out", default=None, help="extra copy of the manifest (evidence)")
    args = ap.parse_args()

    _bind_r4a()
    if args.phase is None:
        ap.print_help()
        return 0

    for dest in (Path(args.staging), Path(args.wheels), Path(args.manifests)):
        resolved = dest.resolve()
        for frozen in (FROZEN_WHEELHOUSE.resolve(), FROZEN_MANIFEST.resolve()):
            if resolved == frozen or frozen in resolved.parents:
                raise AcquisitionError(
                    f"recovery destination {dest} points into a frozen store ({frozen})"
                )

    driver = AcquisitionDriver(
        staging=Path(args.staging),
        wheels=Path(args.wheels),
        manifests=Path(args.manifests),
    )

    print("EXPENSIVE_ACTION_GATE")
    print("Action: acquire 28 exact pylint wheels from official PyPI/files.pythonhosted.org")
    print("Acceptance gate: 28/28 exact owner-authorized artifacts verified and frozen in additive R4-E overlay")
    print("Can change owner decision: YES")
    print("Expected cost: approximately tens of MB, 28 metadata requests + at most 28 wheel downloads")
    print("Cheaper sufficient alternative: none; I6 proved these exact artifacts block 65 units")
    print("Owner authorization present: YES")

    try:
        phase = args.phase
        artifacts: list[SelectedArtifact] = []
        verified: list[VerificationResult] = []
        promoted: list[dict[str, Any]] = []
        manifest: dict[str, Any] | None = None

        if phase in ("discover", "all"):
            artifacts = driver.discover()
            driver.manifests.mkdir(parents=True, exist_ok=True)
            _state_path(driver.manifests).write_text(
                json.dumps([_artifact_to_dict(a) for a in artifacts], indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            print(f"DISCOVERY {len(artifacts)}/{len(REQUIRED_IDENTITIES)} compatible wheels selected")

        if phase in ("download", "verify", "promote", "manifest", "all") and not artifacts:
            artifacts = _load_state(driver.manifests)

        if phase in ("download", "all"):
            paths = driver.download_all(artifacts)
            print(f"DOWNLOAD {len(paths)}/{len(artifacts)} wheels staged -> {driver.staging}")

        if phase in ("verify", "promote", "manifest", "all"):
            verified = driver.verify_all(artifacts)
            for res in verified:
                if not res.passed:
                    failed = [k for k, v in res.checks.items() if not v]
                    raise AcquisitionError(
                        f"verification FAILED for {res.filename}: {failed}"
                    )
            print(f"VERIFY {sum(1 for r in verified if r.passed)}/{len(verified)} wheels passed all 13 gates")

        if phase in ("promote", "manifest", "all"):
            promoted = driver.promote_all(artifacts, verified)
            print(f"PROMOTE {len(promoted)}/{len(artifacts)} wheels -> {driver.wheels}")

        if phase in ("manifest", "all"):
            manifest = driver.build_manifest(artifacts, verified, promoted)
            out = Path(args.manifest_out)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(f"MANIFEST {out}")

        print(f"METADATA_REQUESTS={driver.stats.metadata_requests}")
        print(f"ARTIFACT_REQUESTS={driver.stats.artifact_requests}")
        print(f"DOWNLOADED_BYTES={driver.stats.downloaded_bytes}")
        print(f"DOWNLOADED_MIB={round(driver.stats.downloaded_bytes / (1024 * 1024), 6)}")
        print(f"DOWNLOADED_GIB={round(driver.stats.downloaded_bytes / (1024 * 1024 * 1024), 9)}")
        print(f"RETRIES={len(driver.stats.retries)}")
        return 0
    except StopOwnerReviewError as exc:
        print(f"STOP_OWNER_REVIEW {exc}", file=sys.stderr)
        return 3
    except AcquisitionError as exc:
        print(f"ACQUISITION_FAIL_CLOSED {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ACQUISITION_INSTRUMENTATION_ERROR {exc!r}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
