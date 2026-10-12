"""WP-2 environment canon source-fidelity amendment R1 (additive, ZERO API).

Mission M17_ENV_CANON_SOURCE_FIDELITY_AMENDMENT_R1_DESIGN_AND_FREEZE.

Root cause addressed (frozen owner review, C_LOCK_RECONSTRUCTION_DEFECT): the
D7 R3 environment canon and its closure representation select dependency
artifacts by normalized distribution ``name`` + ``version`` only.  When the
historical Poetry lock records a directory (vendored) source, that source
identity is discarded and a registry wheel with a matching name/version is
substituted.  The historical vendored PyXB 1.2.5 uses
``collections.abc.MutableSequence``; the substituted registry wheel uses
``collections.MutableSequence`` and fails on Python 3.12.

This module is an ADDITIVE, source-aware reconstruction rule.  It:

* never special-cases a task ID (no ``if task == ...`` hacks);
* never overwrites an existing canon schema (``SOURCE_IDENTITY_SCHEMA_VERSION``
  is a new additive identity);
* never touches the network (offline only; ``assert_offline_source``);
* never mutates frozen R3 evidence or the store;
* fails closed whenever historical source identity cannot be reconstructed
  exactly (missing path, tree-hash mismatch, ambiguous source, unknown source).

Scientific invariant: the produced runtime artifact must derive from the exact
historical vendored source at the exact target commit, not from a registry
sdist selected because the name/version happens to match.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from typing import Any, Iterable

from benchmark.wp2.dep_compiler import marker_applicable

SOURCE_IDENTITY_SCHEMA_VERSION = "source_fidelity_r1"
SCHEMA_SALT = "wp2-env-canon-source-fidelity-r1-2026-10-12"

SOURCE_TYPE_REGISTRY = "REGISTRY"
SOURCE_TYPE_DIRECTORY = "DIRECTORY"
SOURCE_TYPE_PATH = "PATH"
SOURCE_TYPE_GIT = "GIT"
SOURCE_TYPE_URL = "URL"
SOURCE_TYPE_FILE = "FILE"
SOURCE_TYPE_UNKNOWN = "UNKNOWN"

SOURCE_TYPES = (
    SOURCE_TYPE_REGISTRY,
    SOURCE_TYPE_DIRECTORY,
    SOURCE_TYPE_PATH,
    SOURCE_TYPE_GIT,
    SOURCE_TYPE_URL,
    SOURCE_TYPE_FILE,
    SOURCE_TYPE_UNKNOWN,
)

REPRO_CLASS_SOURCE_IDENTITY_REPRODUCIBLE = "SOURCE_IDENTITY_REPRODUCIBLE"
REPRO_CLASS_ARTIFACT_BYTE_REPRODUCIBLE = "ARTIFACT_BYTE_REPRODUCIBLE"

_LOCAL_SOURCE_TYPES = (SOURCE_TYPE_DIRECTORY, SOURCE_TYPE_PATH)

_FORBIDDEN_NETWORK_IMPORTS = (
    "import urllib",
    "from urllib",
    "import requests",
    "from requests",
    "import httpx",
    "from httpx",
    "import aiohttp",
    "from aiohttp",
    "import socket",
    "from socket",
    "import http.client",
    "from http.client",
    "import curl",
    "import ftplib",
)

_TASK_ID_RE = re.compile(r"saleor-rc-[0-9a-f]{12}")


class SourceIdentityError(Exception):
    """Base error for source-fidelity reconstruction failures (fail closed)."""


class SourcePathMissing(SourceIdentityError):
    """The historical source path does not exist at the target commit (F5)."""


class SourceTreeMismatch(SourceIdentityError):
    """Observed source bytes do not match the frozen source-tree hash (F6)."""


class AmbiguousSourceIdentity(SourceIdentityError):
    """A source cannot be pinned to one unambiguous historical identity (F7)."""


class NetworkFallbackForbidden(SourceIdentityError):
    """A reconstruction path attempted a network fallback (F8)."""


def normalize_dist_name(name: str) -> str:
    """Deterministic distribution-name normalization (PEP 503 style)."""
    return name.strip().lower().replace("_", "-")


def classify_poetry_source(source: dict[str, Any] | None) -> tuple[str, str | None]:
    """Classify a Poetry lock ``source`` table into (source_type, reference).

    Reference semantics per type:
    * DIRECTORY / PATH -> ``url`` (historical repo-relative path);
    * GIT -> ``url`` (``#<reference-or-resolved_reference>`` appended when
      present, binding to the exact resolved revision when recorded);
    * URL / FILE -> ``url``;
    * REGISTRY -> the registry URL (``None`` when the lock carries no source
      table, i.e. an implicit registry package).
    """
    if not source:
        return SOURCE_TYPE_REGISTRY, None
    stype = str(source.get("type", "")).strip().lower()
    url = source.get("url")
    if stype in ("directory", "path"):
        if not url:
            raise AmbiguousSourceIdentity(
                f"{SOURCE_TYPE_DIRECTORY if stype == 'directory' else SOURCE_TYPE_PATH} "
                "source without a url reference"
            )
        return (
            SOURCE_TYPE_DIRECTORY if stype == "directory" else SOURCE_TYPE_PATH,
            str(url),
        )
    if stype == "git":
        if not url:
            raise AmbiguousSourceIdentity("git source without a url reference")
        ref = source.get("resolved_reference") or source.get("reference")
        return SOURCE_TYPE_GIT, f"{url}#{ref}" if ref else str(url)
    if stype in ("url", "file"):
        if not url:
            raise AmbiguousSourceIdentity(f"{stype} source without a url reference")
        return SOURCE_TYPE_URL if stype == "url" else SOURCE_TYPE_FILE, str(url)
    if stype in ("registry",):
        return SOURCE_TYPE_REGISTRY, url
    return SOURCE_TYPE_UNKNOWN, (str(url) if url else None)


def classify_uv_source(source: dict[str, Any] | None) -> tuple[str, str | None]:
    """Classify a uv.lock ``source`` table into (source_type, reference).

    uv encodes sources as tagged inline tables, e.g.
    ``source = { registry = ... }``, ``source = { directory = ... }``,
    ``source = { git = { url = ..., rev = ... } }``, ``source = { url = ... }``,
    ``source = { path = ... }``.  The root project appears as
    ``source = { virtual = "." }`` (editable self); it is classified PATH by
    ``uv_editable_self`` so callers can exclude it from artifact closure.
    """
    if not source:
        return SOURCE_TYPE_REGISTRY, None
    if "registry" in source:
        return SOURCE_TYPE_REGISTRY, source["registry"]
    if "directory" in source:
        ref = source["directory"]
        return SOURCE_TYPE_DIRECTORY, str(ref)
    if "path" in source:
        return SOURCE_TYPE_PATH, str(source["path"])
    if "virtual" in source:
        return SOURCE_TYPE_PATH, str(source["virtual"])
    if "url" in source:
        return SOURCE_TYPE_URL, str(source["url"])
    if "git" in source:
        git = source["git"]
        if not isinstance(git, dict) or not git.get("url"):
            raise AmbiguousSourceIdentity("uv git source without a url reference")
        url = str(git["url"])
        rev = git.get("rev") or git.get("branch") or git.get("tag")
        return SOURCE_TYPE_GIT, f"{url}#{rev}" if rev else url
    return SOURCE_TYPE_UNKNOWN, None


def uv_editable_self(source: dict[str, Any] | None) -> bool:
    """True when a uv.lock source is the root project's editable self
    (``source = { virtual = ... }``).  The D7 harness materializes the task
    checkout at the target commit as the editable project, so this is not a
    dependency artifact whose identity can be lost by name/version flattening.
    """
    return bool(source and "virtual" in source)


def _git_text(repo_dir: str, git_bin: str, *args: str) -> str:
    return _git_bytes(repo_dir, git_bin, *args).decode("utf-8", errors="replace")


def _git_bytes(repo_dir: str, git_bin: str, *args: str) -> bytes:
    proc = subprocess.run(
        [git_bin, "-C", str(repo_dir), *args],
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SourcePathMissing(
            f"git {args[0] if args else ''} failed in {repo_dir}: "
            f"{proc.stderr.decode('utf-8', 'replace').strip()[:300]}"
        )
    return proc.stdout


def _list_tree_entries(
    repo_dir: str, target_commit: str, source_path: str, git_bin: str
) -> list[tuple[str, str, str]]:
    """Return [(mode, fullpath, blob_sha1)] for every blob under source_path.

    One ``git ls-tree -r -z`` call; raises ``SourcePathMissing`` when the path
    is absent at the target commit (F5).
    """
    ls = _git_bytes(
        repo_dir, git_bin, "ls-tree", "-r", "-z", target_commit, "--", source_path + "/"
    )
    entries: list[tuple[str, str, str]] = []
    if ls:
        for record in ls.split(b"\0"):
            if not record:
                continue
            text = record.decode("utf-8", errors="replace")
            meta, _, full = text.partition("\t")
            mode, _type, blob_sha = meta.split()
            if _type == "blob":
                entries.append((mode, full, blob_sha))
    if not entries:
        raise SourcePathMissing(
            f"source path '{source_path}' not found at {target_commit}"
        )
    return entries


def extract_source_tree(
    repo_dir: str,
    target_commit: str,
    source_path: str,
    git_bin: str = "git",
) -> dict[str, Any]:
    """Deterministically extract a historical vendored source tree (F5/P5).

    Reads ONLY Git object storage anchored to ``target_commit + source_path``
    (``git ls-tree`` + raw ``git cat-file --batch``), never the mutable working
    tree (F4).  Raw object bytes are used (no CRLF/text filters, so the result
    is identical on every platform).  Returns:

    * ``target_commit`` / ``source_path`` as given;
    * ``git_tree_sha1`` — the Git tree object ID (``git rev-parse
      <commit>:<path>``), a content-addressed cross-check;
    * ``file_count`` / ``size_bytes`` — tree inventory;
    * ``per_file_hashes`` — {"<mode> <relpath>": sha256-hex} for every blob;
    * ``tree_sha256`` — canonical source-tree hash (see ``_canonical_tree_hash``).

    Raises ``SourcePathMissing`` when the commit or path is absent (F5).
    """
    entries = _list_tree_entries(repo_dir, target_commit, source_path, git_bin)
    blob_contents = _cat_file_batch(repo_dir, git_bin, [e[2] for e in entries])

    prefix = source_path.rstrip("/") + "/"
    per_file: dict[str, str] = {}
    total_size = 0
    for mode, full, blob_sha in entries:
        rel = full[len(prefix):] if full.startswith(prefix) else full
        raw = blob_contents[blob_sha]
        per_file[f"{mode} {rel}"] = hashlib.sha256(raw).hexdigest()
        total_size += len(raw)

    tree_sha256 = _canonical_tree_hash(per_file)
    try:
        git_tree_sha1 = _git_text(
            repo_dir, git_bin, "rev-parse", f"{target_commit}:{source_path}"
        ).strip()
    except SourcePathMissing:
        git_tree_sha1 = None
    return {
        "target_commit": target_commit,
        "source_path": source_path,
        "git_tree_sha1": git_tree_sha1,
        "file_count": len(per_file),
        "size_bytes": total_size,
        "per_file_hashes": per_file,
        "tree_sha256": tree_sha256,
    }


def _cat_file_batch(
    repo_dir: str, git_bin: str, blob_shas: list[str]
) -> dict[str, bytes]:
    """Read raw blob contents in one ``git cat-file --batch`` call.

    Returns {blob_sha1: raw_bytes}.  ``--batch`` is the raw object transport:
    no filters, no CRLF conversion, deterministic across platforms.
    """
    unique = list(dict.fromkeys(blob_shas))
    payload = "".join(f"{sha}\n" for sha in unique).encode("ascii")
    proc = subprocess.run(
        [git_bin, "-C", str(repo_dir), "cat-file", "--batch"],
        input=payload,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SourcePathMissing(
            f"git cat-file --batch failed in {repo_dir}: "
            f"{proc.stderr.decode('utf-8', 'replace').strip()[:300]}"
        )
    out = proc.stdout
    contents: dict[str, bytes] = {}
    pos = 0
    for sha in unique:
        header_end = out.index(b"\n", pos)
        header = out[pos:header_end].decode("ascii")
        _sha, _type, size_s = header.split()
        size = int(size_s)
        start = header_end + 1
        contents[sha] = out[start:start + size]
        pos = start + size + 1  # skip trailing newline
    return contents


def _canonical_tree_hash(per_file_hashes: dict[str, str]) -> str:
    """Deterministic canonical tree hash.

    SHA-256 over the sorted ``"<mode> <relpath>\\0<content-sha256-hex>"``
    serialization.  Binds to exact historical bytes and relative paths, so
    ``same commit + same path => same hash`` (P2P) and
    ``different bytes => different hash`` (F2P).
    """
    digest = hashlib.sha256()
    for key in sorted(per_file_hashes):
        digest.update(key.encode("utf-8"))
        digest.update(b"\0")
        digest.update(per_file_hashes[key].encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def canonical_tree_hash_from_working_dir(workdir: str) -> str:
    """Hash a mutable working-tree directory (for F4 negative checks only).

    This is the NAIVE implementation that consumes the working tree instead of
    the target commit; tests assert it differs from ``extract_source_tree`` for
    the same logical path, proving the committed source is the authority.
    """
    import os

    per_file: dict[str, str] = {}
    for root, _dirs, files in os.walk(workdir):
        for name in files:
            full = os.path.join(root, name)
            rel = os.path.relpath(full, workdir).replace(os.sep, "/")
            with open(full, "rb") as fh:
                per_file[f"100644 {rel}"] = hashlib.sha256(fh.read()).hexdigest()
    return _canonical_tree_hash(per_file)


@dataclass(frozen=True)
class SourceIdentity:
    """Additive source-aware dependency identity (R1 schema)."""

    name: str
    version: str
    source_type: str
    source_reference: str | None
    source_tree_sha256: str | None = None
    git_tree_sha1: str | None = None
    target_commit: str | None = None
    markers: str | None = None
    python_versions: str | None = None
    schema_version: str = SOURCE_IDENTITY_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "version": self.version,
            "source_type": self.source_type,
            "source_reference": self.source_reference,
            "source_tree_sha256": self.source_tree_sha256,
            "git_tree_sha1": self.git_tree_sha1,
            "target_commit": self.target_commit,
            "markers": self.markers,
            "python_versions": self.python_versions,
        }

    def canonical_pin(self) -> str:
        """Deterministic source-aware pin.

        Two dependencies with equal name/version but different source bytes
        obtain different canonical pins (F2P).
        """
        norm = normalize_dist_name(self.name)
        src = self.source_type
        ref = self.source_reference or ""
        if src == SOURCE_TYPE_REGISTRY:
            return f"{norm}=={self.version}@{src}"
        if src in _LOCAL_SOURCE_TYPES:
            if not self.source_tree_sha256:
                raise AmbiguousSourceIdentity(
                    f"local-source package '{self.name}' has no source-tree hash; "
                    "identity is ambiguous (F7)"
                )
            return f"{norm}=={self.version}@{src}:{ref}#{self.source_tree_sha256}"
        if src == SOURCE_TYPE_UNKNOWN:
            raise AmbiguousSourceIdentity(
                f"package '{self.name}' has an unclassifiable source (F7)"
            )
        if not ref:
            raise AmbiguousSourceIdentity(
                f"package '{self.name}' source '{src}' has no reference (F7)"
            )
        return f"{norm}=={self.version}@{src}:{ref}"

    def identity_sha256(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _pyv_matches(python_versions: str | None, python_version: str) -> bool:
    if not python_versions or python_versions.strip() == "*":
        return True
    from packaging.specifiers import SpecifierSet

    try:
        return python_version in SpecifierSet(python_versions)
    except Exception:
        return True


def _poetry_lock_packages(lock_text: str) -> list[dict[str, Any]]:
    import tomllib

    data = tomllib.loads(lock_text)
    packages: list[dict[str, Any]] = []
    for p in data.get("package", []):
        name = p.get("name")
        version = p.get("version")
        if not name or not version:
            raise AmbiguousSourceIdentity("lock package missing name or version")
        groups = p.get("groups")
        category = p.get("category")
        packages.append(
            {
                "name": str(name),
                "version": str(version),
                "source": p.get("source"),
                "markers": p.get("markers"),
                "python_versions": p.get("python-versions"),
                "develop": bool(p.get("develop", False)),
                "dev": bool(category == "dev") or bool(
                    isinstance(groups, list) and "dev" in groups
                ),
            }
        )
    return packages


def _uv_lock_packages(lock_text: str) -> list[dict[str, Any]]:
    import tomllib

    data = tomllib.loads(lock_text)
    packages: list[dict[str, Any]] = []
    for p in data.get("package", []):
        name = p.get("name")
        version = p.get("version")
        if not name or not version:
            raise AmbiguousSourceIdentity("uv lock package missing name or version")
        packages.append(
            {
                "name": str(name),
                "version": str(version),
                "source": p.get("source"),
                "markers": p.get("marker"),
                "python_versions": p.get("requires-python"),
                "dev": bool(p.get("dev", False)),
            }
        )
    return packages


def build_source_identity(
    name: str,
    version: str,
    source_type: str,
    source_reference: str | None,
    target_commit: str,
    repo_dir: str | None = None,
    markers: str | None = None,
    python_versions: str | None = None,
    git_bin: str = "git",
) -> SourceIdentity:
    """Build an R1 SourceIdentity, extracting the source tree when local.

    For DIRECTORY/PATH sources the identity binds to the exact historical
    source-tree hash extracted from ``target_commit``; a missing path or a
    tree-hash mismatch fails closed (F5/F6).
    """
    tree_sha256: str | None = None
    git_tree_sha1: str | None = None
    if source_type in _LOCAL_SOURCE_TYPES:
        if not repo_dir:
            raise SourcePathMissing(
                f"no repo_dir for local-source package '{name}'; cannot extract "
                "historical source (F5)"
            )
        extraction = extract_source_tree(repo_dir, target_commit, source_reference or "", git_bin)
        tree_sha256 = extraction["tree_sha256"]
        git_tree_sha1 = extraction["git_tree_sha1"]
    return SourceIdentity(
        name=name,
        version=version,
        source_type=source_type,
        source_reference=source_reference,
        source_tree_sha256=tree_sha256,
        git_tree_sha1=git_tree_sha1,
        target_commit=target_commit,
        markers=markers,
        python_versions=python_versions,
    )


def derive_source_aware_closure(
    lock_text: str,
    target_commit: str,
    repo_dir: str | None = None,
    python_version: str = "3.12",
    sys_platform: str = "linux",
    git_bin: str = "git",
    lock_format: str = "poetry",
) -> dict[str, Any]:
    """Derive the R1 source-aware closure for one historical lock.

    The rule is generic (derived from lock source semantics); it never
    special-cases a task or unit ID.  Returns the additive closure with:

    * ``records`` — per-package SourceIdentity dicts (applicable packages);
    * ``pins`` — sorted source-aware canonical pins;
    * ``fail_closed`` — packages whose exact historical identity cannot be
      reconstructed (missing path / ambiguous / unknown source);
    * ``closure_identity_sha256`` — deterministic closure identity.
    """
    if lock_format == "uv":
        packages = _uv_lock_packages(lock_text)
    else:
        packages = _poetry_lock_packages(lock_text)

    records: list[dict[str, Any]] = []
    fail_closed: list[dict[str, Any]] = []
    editable_self: list[dict[str, Any]] = []
    pins: list[str] = []

    for pkg in packages:
        markers = pkg.get("markers")
        pyv = pkg.get("python_versions")
        if not marker_applicable(markers, sys_platform=sys_platform, python_version=python_version):
            continue
        if not _pyv_matches(pyv, python_version):
            continue
        if lock_format == "uv":
            source_type, reference = classify_uv_source(pkg.get("source"))
            if uv_editable_self(pkg.get("source")):
                editable_self.append(
                    {
                        "name": pkg["name"],
                        "version": pkg["version"],
                        "role": "editable_self",
                        "source_type": source_type,
                        "source_reference": reference,
                        "target_commit": target_commit,
                    }
                )
                continue
        else:
            source_type, reference = classify_poetry_source(pkg.get("source"))
        try:
            identity = build_source_identity(
                name=pkg["name"],
                version=pkg["version"],
                source_type=source_type,
                source_reference=reference,
                target_commit=target_commit,
                repo_dir=repo_dir,
                markers=markers,
                python_versions=pyv,
                git_bin=git_bin,
            )
            records.append(identity.to_dict())
            pins.append(identity.canonical_pin())
        except SourceIdentityError as exc:
            fail_closed.append(
                {
                    "name": pkg["name"],
                    "version": pkg["version"],
                    "source_type": source_type,
                    "source_reference": reference,
                    "reason": str(exc),
                }
            )

    return {
        "schema_version": SOURCE_IDENTITY_SCHEMA_VERSION,
        "lock_format": lock_format,
        "target_commit": target_commit,
        "python_version": python_version,
        "sys_platform": sys_platform,
        "n_records": len(records),
        "n_fail_closed": len(fail_closed),
        "n_editable_self": len(editable_self),
        "records": records,
        "editable_self": editable_self,
        "pins": sorted(set(pins)),
        "fail_closed": fail_closed,
        "closure_identity_sha256": closure_identity_sha256(pins),
    }


def materialize_source_tree(
    repo_dir: str,
    target_commit: str,
    source_path: str,
    dest_dir: str,
    git_bin: str = "git",
) -> dict[str, Any]:
    """Materialize the exact historical source bytes to ``dest_dir`` (S8).

    Uses the same raw-object transport as ``extract_source_tree`` so the
    on-disk bytes are byte-identical to the committed blobs (no CRLF/text
    filters).  Returns the extraction metadata plus ``materialized`` = True.
    """
    import os

    entries = _list_tree_entries(repo_dir, target_commit, source_path, git_bin)
    blob_contents = _cat_file_batch(repo_dir, git_bin, [e[2] for e in entries])

    os.makedirs(dest_dir, exist_ok=True)
    prefix = source_path.rstrip("/") + "/"
    per_file: dict[str, str] = {}
    total_size = 0
    for mode, full, blob_sha in entries:
        rel = full[len(prefix):] if full.startswith(prefix) else full
        dest = os.path.join(dest_dir, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        raw = blob_contents[blob_sha]
        with open(dest, "wb") as fh:
            fh.write(raw)
        if mode == "100755":
            os.chmod(dest, 0o755)
        per_file[f"{mode} {rel}"] = hashlib.sha256(raw).hexdigest()
        total_size += len(raw)
    tree_sha256 = _canonical_tree_hash(per_file)
    assert len(per_file) == len(entries)
    return {
        "target_commit": target_commit,
        "source_path": source_path,
        "file_count": len(per_file),
        "size_bytes": total_size,
        "tree_sha256": tree_sha256,
        "materialized": True,
        "dest_dir": dest_dir,
    }


def verify_source_tree(
    identity: SourceIdentity | dict[str, Any], candidate_tree_sha256: str
) -> None:
    """Verify a candidate tree hash against the identity's frozen tree (F6).

    Raises ``SourceTreeMismatch`` when the candidate bytes do not match the
    exact historical source-tree hash bound to the identity (fail closed).
    """
    if isinstance(identity, SourceIdentity):
        expected = identity.source_tree_sha256
    else:
        expected = identity.get("source_tree_sha256")
    if not expected:
        raise SourceTreeMismatch("local-source identity without a frozen tree hash")
    if candidate_tree_sha256 != expected:
        raise SourceTreeMismatch(
            f"tree-hash mismatch: expected {expected}, got {candidate_tree_sha256}"
        )


def closure_identity_sha256(pins: Iterable[str]) -> str:
    """Deterministic SHA-256 over the sorted source-aware pin set."""
    payload = json.dumps(sorted(set(pins)), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def artifact_provenance(
    identity: SourceIdentity | dict[str, Any],
    *,
    build_toolchain: str,
    build_inputs: list[str],
    output_filename: str,
    output_sha256: str,
    metadata_name: str,
    metadata_version: str,
    python_tag: str,
    build_log_sha256: str | None = None,
    byte_reproducible: bool = False,
) -> dict[str, Any]:
    """Build the S5 artifact provenance record for one produced artifact.

    ``reproducibility_class`` is ``ARTIFACT_BYTE_REPRODUCIBLE`` only when the
    build toolchain has been demonstrated to produce byte-identical wheels for
    identical inputs; otherwise it is ``SOURCE_IDENTITY_REPRODUCIBLE`` (the
    artifact derives from the exact historical source, but byte-for-byte wheel
    reproducibility is not falsely claimed).
    """
    if isinstance(identity, SourceIdentity):
        ident = identity.to_dict()
    else:
        ident = identity
    return {
        "schema_version": SOURCE_IDENTITY_SCHEMA_VERSION,
        "dependency_name": ident.get("name"),
        "declared_version": ident.get("version"),
        "source_type": ident.get("source_type"),
        "target_commit": ident.get("target_commit"),
        "vendored_source_path": ident.get("source_reference"),
        "source_tree_sha256": ident.get("source_tree_sha256"),
        "git_tree_sha1": ident.get("git_tree_sha1"),
        "build_toolchain_identity": build_toolchain,
        "build_inputs": sorted(build_inputs),
        "output_filename": output_filename,
        "output_sha256": output_sha256,
        "metadata_name": metadata_name,
        "metadata_version": metadata_version,
        "python_tag": python_tag,
        "build_log_sha256": build_log_sha256,
        "reproducibility_class": (
            REPRO_CLASS_ARTIFACT_BYTE_REPRODUCIBLE
            if byte_reproducible
            else REPRO_CLASS_SOURCE_IDENTITY_REPRODUCIBLE
        ),
    }


def module_source_text() -> str:
    """Return this module's source text (for offline / no-hack assertions)."""
    import inspect

    return inspect.getsource(__import__(__name__, fromlist=["*"]))


def assert_offline_source(source_text: str | None = None) -> list[str]:
    """Return forbidden network import violations in the module source (F8)."""
    text = source_text if source_text is not None else module_source_text()
    return [imp for imp in _FORBIDDEN_NETWORK_IMPORTS if re.search(rf"^\s*{imp}", text, re.MULTILINE)]


def assert_no_task_specific_branch(source_text: str | None = None) -> list[str]:
    """Return task-ID special-case violations in the module source (F9).

    The correction rule must derive from historical lock source semantics, so
    no ``saleor-rc-<hash>`` task identifier may appear in the implementation.
    """
    text = source_text if source_text is not None else module_source_text()
    return list(_TASK_ID_RE.findall(text))


# Markers are assembled from fragments so the frozen store/evidence path
# strings never literally appear in this module (the F10 self-check scans the
# module source for exactly these markers).
_FORBIDDEN_STORE_REFERENCE_MARKERS = (
    "wp2" + "_env" + "_store",
    "env-canon" + "-evidence",
    "D7" + "_R3" + "_",
    "d7" + "_r3" + "_",
    "env-runtime" + "-audit",
)


def assert_no_store_mutation_calls(source_text: str | None = None) -> list[str]:
    """Return frozen-store mutation call violations in the module source (F10).

    The amendment must never edit R2/R3 historical evidence or the read-only
    store in place: the implementation must not reference store/frozen-evidence
    paths at all, and must not contain write/unlink/delete call sites.  Writing
    build artifacts to caller-supplied destination directories (S8 materialize
    uses ``open(..., "wb")``) is permitted.
    """
    text = source_text if source_text is not None else module_source_text()
    violations: list[str] = []
    for marker in _FORBIDDEN_STORE_REFERENCE_MARKERS:
        if marker in text:
            violations.append(f"store_ref:{marker}")
    for pattern in (
        r"\bwrite_text\s*\(",
        r"\bwrite_bytes\s*\(",
        r"\bunlink\s*\(",
        r"\brmtree\s*\(",
        r"\bos\.remove\s*\(",
    ):
        if re.search(pattern, text):
            violations.append(pattern)
    return violations