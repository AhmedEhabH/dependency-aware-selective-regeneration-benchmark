"""Git gates for WP-1b MAIN_297 (AC-4 / AC-10), shared by every CLI.

A tag counts as "on origin" only if origin's ref points at the SAME object as
the local tag (annotated tag object, or commit for a lightweight tag). A tag
name that exists on origin but points elsewhere is a failure, not a pass.

``--skip-git-check`` exists for the zero-API unit tests only; it is refused
unless the environment variable ``WP1B_ALLOW_SKIP_GIT_CHECK`` equals ``1``.
"""
from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path

SKIP_ENV = "WP1B_ALLOW_SKIP_GIT_CHECK"
GIT_TIMEOUT_SECONDS = 120


class GitGateError(RuntimeError):
    """The gate failed: wrong / missing tag, content mismatch, or a refused skip."""


class GitRemoteUnavailableError(GitGateError):
    """origin could not be reached (network) - retry later, never bypass."""


def skip_allowed(requested: bool) -> bool:
    """Return True iff the caller asked to skip AND the test-only env var is set."""
    if not requested:
        return False
    if os.environ.get(SKIP_ENV) != "1":
        raise GitGateError(f"--skip-git-check is for unit tests only (requires {SKIP_ENV}=1); refused")
    return True


def _git(project_dir: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}  # never block on a credential prompt
    return subprocess.run(["git", *args], cwd=project_dir, capture_output=True, timeout=GIT_TIMEOUT_SECONDS,
                          env=env)


def local_tag_object(project_dir: Path, tag: str) -> str:
    out = _git(project_dir, "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}")
    if out.returncode != 0 or not out.stdout.strip():
        raise GitGateError(f"tag {tag} does not exist locally")
    return out.stdout.decode().strip()


def local_tag_commit(project_dir: Path, tag: str) -> str:
    out = _git(project_dir, "rev-parse", "--verify", "--quiet", f"refs/tags/{tag}^{{commit}}")
    if out.returncode != 0 or not out.stdout.strip():
        raise GitGateError(f"tag {tag} does not resolve to a commit locally")
    return out.stdout.decode().strip()


def remote_tag_objects(project_dir: Path, tag: str, remote: str = "origin") -> dict[str, str]:
    """``{"object": sha, "peeled": sha-or-""}`` for ``refs/tags/<tag>`` on ``remote``."""
    try:
        out = _git(project_dir, "ls-remote", "--tags", remote, f"refs/tags/{tag}", f"refs/tags/{tag}^{{}}")
    except subprocess.TimeoutExpired as exc:
        raise GitRemoteUnavailableError(f"git ls-remote {remote} timed out") from exc
    if out.returncode != 0:
        raise GitRemoteUnavailableError(
            f"git ls-remote {remote} failed: {out.stderr.decode(errors='replace').strip()[:300]}")
    found: dict[str, str] = {"object": "", "peeled": ""}
    for line in out.stdout.decode().splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        sha, ref = parts
        if ref == f"refs/tags/{tag}":
            found["object"] = sha
        elif ref == f"refs/tags/{tag}^{{}}":
            found["peeled"] = sha
    return found


def verify_tag_on_origin(project_dir: Path, tag: str, remote: str = "origin") -> dict[str, str]:
    """The local tag exists and origin's tag points at the same object."""
    local_obj = local_tag_object(project_dir, tag)
    commit = local_tag_commit(project_dir, tag)
    remote_refs = remote_tag_objects(project_dir, tag, remote)
    if not remote_refs["object"]:
        raise GitGateError(f"tag {tag} is not on {remote} (push it first)")
    if remote_refs["object"] != local_obj:
        raise GitGateError(
            f"tag {tag} differs between local ({local_obj}) and {remote} ({remote_refs['object']})")
    return {"tag": tag, "tag_object": local_obj, "commit": commit, "remote_object": remote_refs["object"]}


def lf_sha256(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def verify_file_in_tag(project_dir: Path, tag: str, path: Path) -> str:
    """LF-normalized SHA-256 of ``path`` must equal the blob stored in ``tag``."""
    rel = path.resolve().relative_to(project_dir.resolve()).as_posix()
    blob = _git(project_dir, "show", f"refs/tags/{tag}:{rel}")
    if blob.returncode != 0:
        raise GitGateError(f"{rel} is not in tag {tag}")
    tagged = lf_sha256(blob.stdout)
    local = lf_sha256(path.read_bytes())
    if tagged != local:
        raise GitGateError(f"{rel} in tag {tag} ({tagged}) != working tree ({local})")
    return local


def verify_tree_matches_tag(project_dir: Path, tag: str, pathspecs: tuple[str, ...]) -> None:
    """The working tree (incl. uncommitted edits) equals ``tag`` for ``pathspecs``."""
    out = _git(project_dir, "diff", "--quiet", f"refs/tags/{tag}", "--", *pathspecs)
    if out.returncode == 1:
        names = _git(project_dir, "diff", "--name-only", f"refs/tags/{tag}", "--", *pathspecs)
        changed = names.stdout.decode(errors="replace").split()
        raise GitGateError(f"working tree differs from tag {tag} in: {changed[:10]}")
    if out.returncode != 0:
        raise GitGateError(f"git diff against {tag} failed: {out.stderr.decode(errors='replace')[:300]}")
    untracked = _git(project_dir, "ls-files", "--others", "--exclude-standard", "--", *pathspecs)
    extra = untracked.stdout.decode(errors="replace").split()
    if extra:
        raise GitGateError(f"untracked files under frozen paths (not in tag {tag}): {extra[:10]}")
