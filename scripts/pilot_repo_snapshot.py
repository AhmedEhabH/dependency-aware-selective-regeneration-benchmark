#!/usr/bin/env python3
"""Deterministic, fail-closed materialization of frozen Pilot repository snapshots.

PILOT-EXEC-01 closure (``_workspace/active/PILOT-EXEC-01-REAL-LAUNCH-CLOSURE/
02_REPOSITORY_SNAPSHOT_CONTRACT.md``).

The real non-dry-run Pilot path in ``seven_arm_benchmark.py`` resolves every
selected repository from ``data_dir / "repositories" / repo_id`` and aborts
before model initialization when the source root is missing. The historical
Smoke bundle only embedded the ``todo`` tree, so the corrected Pilot bundle must
additionally carry the pinned django CMS and Saleor source trees.

Guarantees:

- materializes tracked files AT the exact pinned commit only (no floating
  branch/head; no ``.git`` directory in the deployment archive);
- fails closed when a materialized source does not match its pinned commit;
- reuses a reusable local acquisition cache (git checkouts) outside the bundle;
- emits deterministic per-repository snapshot evidence (requested SHA,
  resolved HEAD, file count, content hash, size).

The pinned SHAs mirror ``benchmark_data/manifests/repository_versions.yaml``.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tarfile
import time
import urllib.parse
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from benchmark.repositories.validation_commands import FrozenValidationCommand

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EMBEDDED_TODO_SOURCE = (
    PROJECT_ROOT / "benchmark_data" / "repositories" / "todo"
)

_STAGING_EXCLUDED_DIRS: frozenset[str] = frozenset({
    ".git",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "runs",
    "tmp",
    "_auto_resume_temp",
})


@dataclass(frozen=True)
class RepositoryPin:
    """Frozen identity of one Pilot repository source snapshot."""

    repo_id: str
    commit_sha: str
    mode: str  # "git" (external checkout cache) or "embedded" (canonical tree)
    url: str = ""
    embedded_source: Path | None = None


DEFAULT_PINS: tuple[RepositoryPin, ...] = (
    RepositoryPin(
        repo_id="todo",
        commit_sha="b8a33e20bdaf5b329114273063fbe8d5aa66e9cf",
        mode="embedded",
        url="https://github.com/ahmed-ehab/controlled-django-todo",
        embedded_source=EMBEDDED_TODO_SOURCE,
    ),
    RepositoryPin(
        repo_id="djangocms",
        commit_sha="0f633fc9fa213357f4202482aab2b0edad680f95",
        mode="git",
        url="https://github.com/django-cms/django-cms",
    ),
    RepositoryPin(
        repo_id="saleor",
        commit_sha="e11a5557eff29fbb2eed36e6ff3cd0af08ab9e10",
        mode="git",
        url="https://github.com/saleor/saleor",
    ),
)


@dataclass(frozen=True)
class SnapshotEvidence:
    repo_id: str
    mode: str
    requested_sha: str
    resolved_head: str
    file_count: int
    content_hash: str
    size_bytes: int


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _tree_content_hash(directory: Path) -> str:
    """Deterministic tree/content hash over eligible files.

    Mirrors the bundle ``_tree_sha256`` contract used by the deployment tests so
    the materialized snapshot evidence is reproducible.
    """
    digest = hashlib.sha256()
    eligible = [
        p.relative_to(directory).as_posix()
        for p in directory.rglob("*")
        if p.is_file()
        and p.name not in (".git",)
        and not any(part in _STAGING_EXCLUDED_DIRS for part in p.relative_to(directory).parts)
    ]
    for rel in sorted(eligible):
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update((directory / rel).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _count_files(directory: Path) -> int:
    return sum(
        1
        for p in directory.rglob("*")
        if p.is_file()
        and not any(part in _STAGING_EXCLUDED_DIRS for part in p.relative_to(directory).parts)
    )


def _total_size(directory: Path) -> int:
    return sum(
        p.stat().st_size
        for p in directory.rglob("*")
        if p.is_file()
        and not any(part in _STAGING_EXCLUDED_DIRS for part in p.relative_to(directory).parts)
    )


def _git(repo_path: Path, args: list[str], *, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_path), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed in {repo_path}: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def _resolve_commit(repo_path: Path, commit_sha: str) -> str:
    resolved = _git(repo_path, ["rev-parse", "--verify", f"{commit_sha}^{{commit}}"])
    if len(resolved) != 40:
        raise RuntimeError(
            f"pinned commit {commit_sha} did not resolve to a 40-char SHA "
            f"in {repo_path}: {resolved!r}"
        )
    return resolved


def _export_git_tree(repo_path: Path, commit_sha: str, target_dir: Path) -> None:
    """Export tracked files at ``commit_sha`` into ``target_dir`` (no .git).

    Uses ``git archive`` (deterministic; honors the exact tree) and extracts
    with Python tarfile. Symlinks are skipped (never required by the benchmark
    validation paths and they are not portable on Windows).
    """
    result = subprocess.run(
        ["git", "-C", str(repo_path), "archive", "--format=tar", commit_sha],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git archive failed for {commit_sha} in {repo_path}: "
            f"{result.stderr.decode('utf-8', 'replace').strip()}"
        )
    target_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r:") as tf:
        for member in tf.getmembers():
            if member.isdir():
                continue
            if member.issym() or member.islnk():
                continue
            name = member.name.lstrip("./")
            if ".." in Path(name).parts:
                raise RuntimeError(
                    f"tar member escapes target directory: {member.name!r}"
                )
            out_path = target_dir / name
            out_path.parent.mkdir(parents=True, exist_ok=True)
            extracted = tf.extractfile(member)
            if extracted is None:
                continue
            data = extracted.read()
            out_path.write_bytes(data)


def _copy_embedded_tree(source: Path, target_dir: Path) -> None:
    if target_dir.is_dir():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    def _ignore(_dirpath: str, names: list[str]) -> list[str]:
        ignored: list[str] = []
        for name in names:
            if name in _STAGING_EXCLUDED_DIRS:
                ignored.append(name)
        return ignored

    shutil.copytree(source, target_dir, dirs_exist_ok=True, ignore=_ignore)


def materialize_repository(
    pin: RepositoryPin,
    repo_cache: Path | None,
    target_dir: Path,
    *,
    allow_acquire: bool = False,
) -> SnapshotEvidence:
    """Materialize one frozen repository snapshot and return its evidence.

    Fails closed on any identity mismatch. No ``.git`` directory is ever
    included in the output.
    """
    if pin.mode == "embedded":
        source = pin.embedded_source
        if source is None or not source.is_dir():
            raise RuntimeError(
                f"embedded source for '{pin.repo_id}' is missing: {source}"
            )
        _copy_embedded_tree(source, target_dir)
        resolved_head = "embedded"
    elif pin.mode == "git":
        if repo_cache is None:
            raise RuntimeError(
                f"repository '{pin.repo_id}' requires --repo-cache "
                f"(git checkout cache); none provided."
            )
        checkout = repo_cache / pin.repo_id
        if not (checkout / ".git").exists():
            raise RuntimeError(
                f"repo cache checkout for '{pin.repo_id}' is missing: {checkout}. "
                "Provide --repo-cache pointing at a directory containing git "
                "checkouts of djangocms and saleor at their pinned commits."
            )
        try:
            resolved_head = _resolve_commit(checkout, pin.commit_sha)
        except RuntimeError:
            if not allow_acquire:
                raise
            _git(checkout, ["fetch", "--quiet", "--depth", "1", "origin", pin.commit_sha])
            _git(checkout, ["fetch", "--quiet", "origin", pin.commit_sha])
            resolved_head = _resolve_commit(checkout, pin.commit_sha)
        if resolved_head != pin.commit_sha:
            raise RuntimeError(
                f"pinned commit mismatch for '{pin.repo_id}': requested "
                f"{pin.commit_sha} resolved to {resolved_head}"
            )
        if target_dir.is_dir():
            shutil.rmtree(target_dir)
        _export_git_tree(checkout, resolved_head, target_dir)
    else:
        raise RuntimeError(f"unsupported materialization mode: {pin.mode!r}")

    return SnapshotEvidence(
        repo_id=pin.repo_id,
        mode=pin.mode,
        requested_sha=pin.commit_sha,
        resolved_head=resolved_head,
        file_count=_count_files(target_dir),
        content_hash=_tree_content_hash(target_dir),
        size_bytes=_total_size(target_dir),
    )


def materialize_repositories(
    data_repositories_dir: Path,
    repo_cache: Path | None,
    pins: tuple[RepositoryPin, ...] = DEFAULT_PINS,
    *,
    allow_acquire: bool = False,
) -> dict[str, dict]:
    """Materialize every pinned repository under ``data_repositories_dir``.

    Returns an ordered mapping of repo_id -> evidence dict suitable for JSON
    manifest serialization. Fails closed on any missing/divergent source.
    """
    data_repositories_dir.mkdir(parents=True, exist_ok=True)
    evidence: dict[str, dict] = {}
    for pin in pins:
        target = data_repositories_dir / pin.repo_id
        result = materialize_repository(
            pin,
            repo_cache=repo_cache,
            target_dir=target,
            allow_acquire=allow_acquire,
        )
        evidence[pin.repo_id] = asdict(result)
    return evidence


# ---------------------------------------------------------------------------
# Engineering preflight: run each frozen validation command against a pristine
# staged snapshot and report PASS/FAIL per repository (05_REAL_PREBENCHMARK_GATE,
# Pipeline Smoke Test). The Kaggle notebook runs the same entry point.
# ---------------------------------------------------------------------------

DEFAULT_MANIFEST = (
    PROJECT_ROOT
    / "benchmark_data"
    / "manifests"
    / "pilot_validation_commands.yaml"
)


def _tail_output(raw: str, *, max_lines: int = 25) -> str:
    lines = [line.rstrip("\r") for line in raw.splitlines() if line.strip()]
    return "\n".join(lines[-max_lines:])


def _host_port_from_url(url: str) -> tuple[str, int] | None:
    parsed = urllib.parse.urlparse(url)
    if not parsed.hostname:
        return None
    port = parsed.port or {"http": 80, "https": 443, "postgres": 5432, "redis": 6379}.get(
        parsed.scheme, 5432
    )
    return parsed.hostname, int(port)


def _service_reachable(url: str, *, timeout: float = 5.0) -> bool:
    host_port = _host_port_from_url(url)
    if host_port is None:
        return False
    host, port = host_port
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _resolve_services(
    declared: tuple[str, ...], env: dict[str, str]
) -> list[dict[str, object]]:
    """Probe every service URL referenced by the frozen command env.

    ``postgres://`` / ``redis://`` URLs are reachability-checked over TCP. The
    SQLite backend requires no service and is reported as ``required: False``.
    """
    results: list[dict[str, object]] = []
    for value in sorted(env.values()):
        scheme = urllib.parse.urlparse(value).scheme
        if scheme not in {"postgres", "postgresql", "redis"}:
            continue
        name = "postgresql" if scheme.startswith("postgres") else "valkey"
        reachable = _service_reachable(value)
        results.append({
            "name": name,
            "url_scheme": scheme,
            "required": name in declared,
            "reachable": reachable,
        })
    for service in sorted(declared):
        if not any(r["name"] == service for r in results):
            results.append({"name": service, "required": True, "reachable": False})
    return results


def apply_windows_infra_workarounds(staged_dir: Path, repo_id: str) -> list[str]:
    """Apply documented win32-only environment compatibility shims to a staged copy.

    The staged copy is a disposable materialization; the source-of-truth tree is
    never modified. On Linux/Kaggle no shim is applied (see
    PILOT-READY-01-SALEOR-VALIDATION: ``saleor/core/rlimit.py`` imports the
    Unix-only ``resource`` module unconditionally).
    """
    applied: list[str] = []
    if sys.platform != "win32" or repo_id != "saleor":
        return applied
    target = staged_dir / "saleor" / "core" / "rlimit.py"
    if not target.is_file():
        raise RuntimeError(f"expected {target} for saleor win32 shim; missing")
    original = target.read_text(encoding="utf-8")
    if "except ImportError" in original:
        return applied
    guarded = original.replace(
        "import resource\n",
        "try:\n    import resource\nexcept ImportError:\n    resource = None\n",
        1,
    )
    guarded = guarded.replace(
        "RLIMIT_TYPE = resource.RLIMIT_DATA\n",
        "RLIMIT_TYPE = resource.RLIMIT_DATA if resource is not None else None\n",
        1,
    )
    guarded = guarded.replace(
        '        "Both `SOFT_MEMORY_LIMIT_IN_MB` and `HARD_MEMORY_LIMIT_IN_MB` must be set to enable memory limits."\n'
        "        )\n",
        '        "Both `SOFT_MEMORY_LIMIT_IN_MB` and `HARD_MEMORY_LIMIT_IN_MB` must be set to enable memory limits."\n'
        "        )\n\n"
        "    if resource is None:\n"
        "        return\n",
        1,
    )
    if guarded == original:
        raise RuntimeError(
            f"win32 rlimit guard for {target} did not change the file"
        )
    target.write_text(guarded, encoding="utf-8", newline="\n")
    applied.append("saleor/core/rlimit.py: guard Unix-only `resource` import (win32 only)")
    return applied


def _run_command(
    argv: list[str],
    cwd: Path,
    env: dict[str, str],
    timeout: int,
    label: str,
) -> dict[str, object]:
    start = time.monotonic()
    try:
        proc = subprocess.run(
            argv,
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        duration = round(time.monotonic() - start, 2)
        return {
            "label": label,
            "command": argv,
            "passed": proc.returncode == 0,
            "exit_code": proc.returncode,
            "duration_seconds": duration,
            "output_tail": _tail_output(proc.stdout + proc.stderr),
        }
    except subprocess.TimeoutExpired as exc:
        duration = round(time.monotonic() - start, 2)
        return {
            "label": label,
            "command": argv,
            "passed": False,
            "exit_code": -1,
            "duration_seconds": duration,
            "output_tail": _tail_output(str(getattr(exc, "output", "") or "")),
        }
    except FileNotFoundError:
        duration = round(time.monotonic() - start, 2)
        return {
            "label": label,
            "command": argv,
            "passed": False,
            "exit_code": -1,
            "duration_seconds": duration,
            "output_tail": f"command not found: {argv[0]}",
        }


def run_repo_preflight(
    repo_id: str,
    staging_dir: Path,
    repo_cache: Path | None,
    venv_python: str,
    command: FrozenValidationCommand,
    timeout: int,
    pins: tuple[RepositoryPin, ...] = DEFAULT_PINS,
    repo_source: Path | None = None,
) -> dict[str, object]:
    """Materialize one pristine snapshot and run every frozen command in it.

    ``repo_source`` (an already-materialized repository tree, e.g. a bundled
    Kaggle snapshot) bypasses git-checkout materialization while preserving the
    pristine-staging contract: the tree is re-staged with the same
    deterministic copy rules and evidence is recomputed over the staged copy.

    PASS/FAIL is fail-closed: ``passed`` requires BOTH every declared required
    service to be reachable AND every frozen command to exit 0. The returned
    record distinguishes service checks, command checks and the overall result.
    """
    pin = next((p for p in pins if p.repo_id == repo_id), None)
    if pin is None:
        raise RuntimeError(f"no RepositoryPin defined for '{repo_id}'")
    if repo_source is not None:
        if not repo_source.is_dir():
            raise RuntimeError(
                f"repo_source for '{repo_id}' is not a directory: {repo_source}"
            )
        _copy_embedded_tree(repo_source, staging_dir)
        evidence = SnapshotEvidence(
            repo_id=pin.repo_id,
            mode="bundled",
            requested_sha=pin.commit_sha,
            resolved_head="bundled",
            file_count=_count_files(staging_dir),
            content_hash=_tree_content_hash(staging_dir),
            size_bytes=_total_size(staging_dir),
        )
    else:
        evidence = materialize_repository(
            pin,
            repo_cache=repo_cache,
            target_dir=staging_dir,
            allow_acquire=True,
        )
    workarounds = apply_windows_infra_workarounds(staging_dir, repo_id)
    env = dict(os.environ)
    env.update(command.env_dict())
    services = _resolve_services(command.services, command.env_dict())
    services_passed = all(
        not bool(entry["required"]) or bool(entry["reachable"]) for entry in services
    )
    runs: list[dict[str, object]] = []
    all_passed = True
    for label, argv in (
        ("primary", command.resolve_interpreter(venv_python)),
        *(
            (f"additional-{idx}", list(extra))
            for idx, extra in enumerate(command.resolved_additional_commands(venv_python))
        ),
    ):
        result = _run_command(argv, staging_dir, env, timeout, label)
        runs.append(result)
        all_passed = all_passed and bool(result["passed"])
    return {
        "repo_id": repo_id,
        "mode": evidence.mode,
        "requested_sha": evidence.requested_sha,
        "resolved_head": evidence.resolved_head,
        "file_count": evidence.file_count,
        "content_hash": evidence.content_hash,
        "applied_workarounds": workarounds,
        "services": services,
        "services_passed": services_passed,
        "commands": runs,
        "command_passed": all_passed,
        "passed": all_passed and services_passed,
    }


def run_preflight(
    manifest_path: Path,
    staging_root: Path,
    repo_cache: Path | None,
    venv_pythons: dict[str, str],
    repos: tuple[str, ...],
    timeout: int,
    repo_sources: dict[str, Path] | None = None,
) -> dict[str, object]:
    """Run the frozen validation contract against pristine staged snapshots."""
    from benchmark.repositories.validation_commands import load_validation_commands

    manifest = load_validation_commands(manifest_path)
    results: dict[str, object] = {}
    all_passed = True
    for repo_id in repos:
        command = manifest.require(repo_id)
        python = venv_pythons.get(repo_id)
        if not python:
            raise RuntimeError(
                f"no interpreter provided for '{repo_id}' (--venv-python {repo_id}=<path>)"
            )
        repo_staging = staging_root / repo_id
        if repo_staging.is_dir():
            shutil.rmtree(repo_staging)
        repo_staging.mkdir(parents=True, exist_ok=True)
        try:
            result = run_repo_preflight(
                repo_id=repo_id,
                staging_dir=repo_staging,
                repo_cache=repo_cache,
                venv_python=python,
                command=command,
                timeout=timeout,
                repo_source=(repo_sources or {}).get(repo_id),
            )
        except Exception as exc:
            result = {
                "repo_id": repo_id,
                "passed": False,
                "error": f"{type(exc).__name__}: {exc}",
            }
        results[repo_id] = result
        all_passed = all_passed and bool(result["passed"])
    return {
        "task": "PILOT-EXEC-01",
        "manifest": str(manifest_path),
        "created_utc": datetime.now(UTC).isoformat(),
        "platform": sys.platform,
        "staging_root": str(staging_root),
        "overall": "PASS" if all_passed else "FAIL",
        "repositories": results,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="pilot_repo_snapshot",
        description=(
            "Deterministic, fail-closed materialization and engineering "
            "preflight of frozen Pilot repository snapshots."
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    materialize = subparsers.add_parser("materialize", help="materialize snapshots")
    materialize.add_argument("--output-root", type=Path, required=True)
    materialize.add_argument("--repo-cache", type=Path, default=None)
    materialize.add_argument("--allow-acquire", action="store_true", default=False)

    preflight = subparsers.add_parser(
        "preflight",
        help="run the frozen validation command per repo on pristine snapshots",
    )
    preflight.add_argument(
        "--manifest", type=Path, default=DEFAULT_MANIFEST
    )
    preflight.add_argument("--staging-root", type=Path, required=True)
    preflight.add_argument("--repo-cache", type=Path, default=None)
    preflight.add_argument(
        "--venv-python",
        action="append",
        default=[],
        metavar="repo_id=path",
        help="Python interpreter for one repository (repeatable).",
    )
    preflight.add_argument(
        "--repo-source",
        action="append",
        default=[],
        metavar="repo_id=path",
        help=(
            "Already-materialized repository tree to preflight (repeatable); "
            "bypasses git-checkout materialization for bundled Kaggle snapshots."
        ),
    )
    preflight.add_argument(
        "--repos",
        default="todo,djangocms,saleor",
        help="Comma-separated repositories to preflight (default: all).",
    )
    preflight.add_argument(
        "--timeout", type=int, default=3600, help="Per-command timeout (seconds)."
    )
    preflight.add_argument("--out", type=Path, required=True, help="Result JSON path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "materialize":
        evidence = materialize_repositories(
            data_repositories_dir=args.output_root / "data" / "repositories",
            repo_cache=args.repo_cache,
            allow_acquire=args.allow_acquire,
        )
        print(json.dumps(evidence, indent=2, sort_keys=True))
        return 0
    if args.command == "preflight":
        venv_pythons: dict[str, str] = {}
        for item in args.venv_python:
            repo_id, _, python = item.partition("=")
            if not repo_id or not python:
                raise SystemExit(f"invalid --venv-python value: {item!r}")
            venv_pythons[repo_id] = python
        repo_sources: dict[str, Path] = {}
        for item in args.repo_source:
            repo_id, _, source = item.partition("=")
            if not repo_id or not source:
                raise SystemExit(f"invalid --repo-source value: {item!r}")
            repo_sources[repo_id] = Path(source)
        repos = tuple(r for r in args.repos.split(",") if r)
        result = run_preflight(
            manifest_path=args.manifest,
            staging_root=args.staging_root,
            repo_cache=args.repo_cache,
            venv_pythons=venv_pythons,
            repos=repos,
            timeout=args.timeout,
            repo_sources=repo_sources,
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(f"overall: {result['overall']}")
        repositories = cast("dict[str, dict[str, object]]", result["repositories"])
        for repo_id, entry in repositories.items():
            print(f"  {repo_id}: {'PASS' if entry['passed'] else 'FAIL'}")
        return 0 if result["overall"] == "PASS" else 1
    raise SystemExit("subcommand required: materialize | preflight")
