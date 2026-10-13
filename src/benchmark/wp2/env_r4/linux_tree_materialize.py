"""R4 Linux-faithful target-commit materialization from local Git objects.

Mission ``M17_D7_R4_C_LINUX_TREE_FIDELITY`` proves repository-tree fidelity
only: a deterministic, Linux-native route to materialize a historical target
commit from local Git objects into an ephemeral Linux container volume, without
a permanent 219-worktree duplicate.

Successor ``M17_D7_R4C_SYMLINK_MATERIALIZATION`` adds Git-faithful symlink
materialization required by the same frozen exact-tree-fidelity contract:

  100644 -> regular file (unchanged)
  100755 -> executable regular file (unchanged)
  120000 -> real Linux symbolic link (new; target = exact Git blob bytes,
            never dereferenced/flattened/normalized, broken relative links
            preserved)
  all other modes (e.g. 160000 gitlink/submodule) -> fail closed (unchanged)

Windows/NTFS cannot faithfully materialize every historical repository path
(e.g. Saleor VCR cassettes containing ``?``).  This module never treats a
Windows checkout as authoritative: the tree is read object-authoritatively from
local Git objects (``ls-tree`` / ``cat-file``), and every entry is written to a
Linux volume with its exact Git path, exact blob bytes and Git mode, fail
closed on any missing commit, missing object, partial extraction, silent skip,
dirty destination, or unexpected mode.

This module is track-owned implementation.  It does NOT modify the frozen
shared interface (``contracts.py`` / ``__init__.py``).
"""
from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass

from benchmark.wp2.linux_adapter import CommandResult, LinuxBackend, contains_windows_invalid_char

# ---------------------------------------------------------------------------
# Fail-closed errors
# ---------------------------------------------------------------------------


class MaterializeError(Exception):
    """Raised (fail closed) on any materialization or verification failure."""


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TreeEntry:
    """One blob entry of the target tree (Git object authority)."""

    mode: str
    oid: str
    path: str

    @property
    def unix_mode(self) -> int:
        """Git file mode -> Unix permission bits (e.g. ``100755`` -> ``0o755``)."""
        return git_mode_to_unix(self.mode)

    @property
    def ntfs_invalid(self) -> bool:
        """True if the path would be invalid on Windows/NTFS."""
        return contains_windows_invalid_char(self.path)


def git_mode_to_unix(mode: str) -> int:
    """Map a Git tree entry mode to Unix permission bits; unknown modes fail closed.

    ``100644`` -> regular file, ``100755`` -> executable regular file,
    ``120000`` -> symbolic link (Linux symlinks are always ``0o777``; the
    permission bits are not meaningful for symlinks).  Any other mode
    (including ``160000`` gitlinks) fails closed.
    """
    if mode == "100755":
        return 0o755
    if mode == "100644":
        return 0o644
    if mode == "120000":
        return 0o777
    raise MaterializeError(f"unsupported git blob mode {mode!r} (fail closed)")


def parse_tree_line(line: str) -> TreeEntry:
    """Parse one ``ls-tree`` line ``<mode> <oid>\t<path>`` -> ``TreeEntry``.

    Supported entry modes are regular file (100644), executable regular file
    (100755) and symbolic link (120000).  Any other mode (e.g. 160000 gitlink)
    is rejected (never silently skipped).
    """
    if not line:
        raise MaterializeError("empty ls-tree line (fail closed)")
    mode, rest = line.split(" ", 1)
    if "\t" not in rest:
        raise MaterializeError(f"malformed ls-tree line {line!r} (fail closed)")
    oid, path = rest.split("\t", 1)
    if not oid or not path:
        raise MaterializeError(f"malformed ls-tree line {line!r} (fail closed)")
    if mode not in ("100644", "100755", "120000"):
        raise MaterializeError(f"non-blob/unsupported entry {line!r} (fail closed)")
    return TreeEntry(mode=mode, oid=oid, path=path)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def encode_runner_script(script: str, entrypoint: str = "bash") -> str:
    """Base64-transport ``script`` for ``docker run ... -lc``.

    WSL/Win32 argv mangles ``$``, quotes and newlines; base64 keeps the payload
    byte-exact inside ``echo <b64> | base64 -d | <entrypoint>``.
    """
    encoded = base64.b64encode(script.encode("utf-8")).decode("ascii")
    return f"echo {encoded} | base64 -d | {entrypoint}"


def tree_identity(entries: list[TreeEntry]) -> str:
    """Deterministic identity of a target tree (sorted ``mode path`` records).

    Used for P5: repeated materialization must reproduce the same identity.
    """
    records = sorted(f"{e.unix_mode:03o} {e.path}" for e in entries)
    return sha256_text("\n".join(records))


# ---------------------------------------------------------------------------
# Container-side materialization script (object-authoritative, fail closed)
# ---------------------------------------------------------------------------

MATERIALIZE_SCRIPT = r"""
#!/usr/bin/env bash
set -euo pipefail
src=/src
out=/out
commit=${COMMIT}
# Fail closed: missing commit.
rev="$(git -C "$src" rev-parse --verify "${commit}^{commit}")" \
  || { echo "MISSING_COMMIT ${commit}"; exit 10; }
# Fail closed: dirty destination -> never silently merge trees.
if [ -n "$(find "$out" -mindepth 1 -print -quit 2>/dev/null)" ]; then
  echo "DIRTY_DESTINATION $out"; exit 11
fi
# Fail closed: tree listing must succeed.
git -C "$src" ls-tree -r -z --format='%(objectmode)%x00%(objecttype)%x00%(objectname)%x00%(path)' "$rev" > /tmp/tree.z \
  || { echo "LS_TREE_FAIL"; exit 12; }
count=0
while IFS= read -r -d '' mode; do
  IFS= read -r -d '' typ  || { echo "PARSE_FAIL"; exit 13; }
  IFS= read -r -d '' oid  || { echo "PARSE_FAIL"; exit 13; }
  IFS= read -r -d '' path || { echo "PARSE_FAIL"; exit 13; }
  if [ "$typ" != "blob" ]; then echo "NON_BLOB $typ $path"; exit 14; fi
  case "$mode" in
    100755) um=755 ;;
    100644) um=644 ;;
    120000)
      # Real Linux symlink: target = exact Git blob bytes; never dereference,
      # never flatten, never normalize. Broken relative links preserved.
      target="$(git -C "$src" cat-file blob "$oid")" \
        || { echo "SYMLINK_TARGET_FAIL $oid $path"; exit 20; }
      mkdir -p "$out/$(dirname "$path")" || { echo "MKDIR_FAIL $path"; exit 16; }
      ln -s "$target" "$out/$path" || { echo "SYMLINK_FAIL $path"; exit 21; }
      count=$((count+1))
      continue
      ;;
    *) echo "UNEXPECTED_MODE $mode $path"; exit 15 ;;
  esac
  mkdir -p "$out/$(dirname "$path")" || { echo "MKDIR_FAIL $path"; exit 16; }
  if ! git -C "$src" cat-file blob "$oid" > "$out/$path"; then
    echo "BLOB_FAIL $oid $path"; exit 17
  fi
  chmod "$um" "$out/$path" || { echo "CHMOD_FAIL $um $path"; exit 18; }
  count=$((count+1))
done < /tmp/tree.z
echo "MATERIALIZED $count"
"""


# ---------------------------------------------------------------------------
# Materializer
# ---------------------------------------------------------------------------


class Materializer:
    """Deterministic Linux-native materialization from local Git objects.

    ``repo_linux_path`` is the local Git repository as seen inside the Linux
    backend (e.g. ``/opt/wp2_v2/saleor-cache``) and is mounted read-only into
    each container.  ``image`` must already exist locally; it is never pulled.
    """

    def __init__(
        self,
        backend: LinuxBackend,
        image: str,
        repo_linux_path: str,
        *,
        mount_src: str = "/src",
        mount_out: str = "/out",
        image_verified: bool = False,
    ) -> None:
        self._backend = backend
        self.image = image
        self.repo = repo_linux_path
        self.mount_src = mount_src
        self.mount_out = mount_out
        self._image_verified = image_verified

    # -- low-level runner -------------------------------------------------

    def run(self, cmd: list[str], *, timeout_s: int = 1200) -> CommandResult:
        return self._backend.run(cmd, timeout_s=timeout_s)

    def _run_in_image(
        self,
        entrypoint: str,
        script: str,
        *,
        volumes: list[str] | None = None,
        timeout_s: int = 1200,
        network: bool = False,
    ) -> CommandResult:
        """Run ``entrypoint`` with ``script`` in the local image.

        The script is base64-transported so WSL/Win32 argv mangling of ``$``,
        quotes and newlines never reaches the container.  ``network=False``
        (default) keeps the container without network access by construction
        (``--network none`` is passed).
        """
        encoded = base64.b64encode(script.encode("utf-8")).decode("ascii")
        runner_script = f"echo {encoded} | base64 -d | {entrypoint}"
        docker = ["run", "--rm"]
        docker += ["-v", f"{self.repo}:{self.mount_src}:ro"]
        for vol in volumes or []:
            docker += ["-v", vol]
        if not network:
            docker += ["--network", "none"]
        docker += ["--entrypoint", "bash", self.image, "-lc", runner_script]
        return self.run(docker, timeout_s=timeout_s)

    def _require_image_local(self) -> None:
        """Fail closed if the image is not present locally (never pull)."""
        if self._image_verified:
            return
        r = self.run(["image", "inspect", self.image], timeout_s=120)
        if r.returncode != 0:
            raise MaterializeError(
                f"local image {self.image!r} not present; refusing to pull (fail closed): "
                f"{r.stderr.strip()}"
            )
        self._image_verified = True

    # -- git object authority ---------------------------------------------

    def resolve_commit(self, commit: str) -> str:
        """Resolve ``commit`` to a full object name; missing commit fails closed."""
        self._require_image_local()
        script = f"git -C '{self.mount_src}' rev-parse --verify '{commit}^{{commit}}'"
        r = self._run_in_image("bash", script)
        out = r.stdout.strip()
        if r.returncode != 0 or not out:
            raise MaterializeError(
                f"missing commit {commit!r} in local Git objects (fail closed): "
                f"{r.stderr.strip()} {r.stdout.strip()}"
            )
        return out.splitlines()[-1]

    def tree_entries(self, commit: str) -> list[TreeEntry]:
        """List the target tree from local Git objects (object authority)."""
        self._require_image_local()
        resolved = self.resolve_commit(commit)
        script = (
            f"git -C '{self.mount_src}' ls-tree -r --format='%(objectmode) %(objectname)%x09%(path)' "
            f"'{resolved}'"
        )
        r = self._run_in_image("bash", script)
        if r.returncode != 0:
            raise MaterializeError(
                f"ls-tree failed for {resolved!r} (fail closed): {r.stderr.strip()}"
            )
        entries = []
        for line in r.stdout.splitlines():
            if not line.strip():
                continue
            mode, rest = line.split(" ", 1)
            oid, path = rest.split("\t", 1)
            if mode not in ("100644", "100755", "120000"):
                raise MaterializeError(f"non-blob/unsupported entry {line!r} (fail closed)")
            entries.append(TreeEntry(mode=mode, oid=oid, path=path))
        if not entries:
            raise MaterializeError(f"empty tree for {resolved!r} (fail closed)")
        return entries

    # -- materialization ---------------------------------------------------

    def materialize(
        self,
        commit: str,
        volume: str,
        *,
        resolve: bool = True,
    ) -> int:
        """Materialize ``commit`` into an existing, empty Linux ``volume``.

        Returns the number of files written.  Fails closed on missing commit,
        missing object, partial extraction, dirty destination, or any skip.
        """
        self._require_image_local()
        resolved = self.resolve_commit(commit) if resolve else commit
        script = MATERIALIZE_SCRIPT.replace("${COMMIT}", resolved)
        r = self._run_in_image(
            "bash",
            script,
            volumes=[f"{volume}:{self.mount_out}"],
        )
        stdout = r.stdout
        if r.returncode != 0:
            raise MaterializeError(
                f"materialization failed for {resolved!r} (fail closed): {stdout.strip()} {r.stderr.strip()}"
            )
        marker = "MATERIALIZED "
        for line in stdout.splitlines():
            if line.startswith(marker):
                count = int(line[len(marker):].strip())
                return count
        raise MaterializeError(
            f"materialization produced no count marker (fail closed): {stdout.strip()}"
        )

    # -- verification ------------------------------------------------------

    def verify_file(
        self,
        commit: str,
        volume: str,
        path: str,
        expected_mode: int,
        expected_oid: str,
        *,
        resolve: bool = True,
    ) -> dict[str, object]:
        """Verify one materialized file against Git-tree authority.

        Checks: exact path exists, Git mode preserved, blob content (via
        ``git hash-object``) matches the Git object id.
        """
        if resolve:
            self.resolve_commit(commit)
        _ = expected_oid
        script = (
            "set -euo pipefail\n"
            f'p={path!r}\n'
            f"f={self.mount_out}/$p\n"
            "if [ ! -f \"$f\" ]; then echo 'MISSING'; exit 21; fi\n"
            f"mode=$(stat -c %a \"$f\")\n"
            f"echo \"MODE $mode\"\n"
            f"hash=$(git -C {self.mount_src} hash-object \"$f\")\n"
            f"echo \"OID $hash\"\n"
        )
        r = self._run_in_image(
            "bash",
            script,
            volumes=[f"{volume}:{self.mount_out}"],
        )
        if r.returncode != 0:
            return {
                "path": path,
                "present": False,
                "error": r.stdout.strip() or r.stderr.strip(),
            }
        mode = None
        oid = None
        for line in r.stdout.splitlines():
            if line.startswith("MODE "):
                mode = line[len("MODE "):].strip()
            elif line.startswith("OID "):
                oid = line[len("OID "):].strip()
        return {
            "path": path,
            "present": True,
            "mode": mode,
            "git_mode": f"{expected_mode:03o}",
            "mode_match": mode == f"{expected_mode:03o}",
            "blob_oid": oid,
            "expected_oid": expected_oid,
            "content_match": oid == expected_oid,
        }

    def verify_symlink(
        self,
        commit: str,
        volume: str,
        path: str,
        expected_target: str,
        *,
        resolve: bool = True,
    ) -> dict[str, object]:
        """Verify one materialized symlink against Git-tree authority.

        Checks the entry is a REAL symbolic link (not a copied/dereferenced
        file) and that ``readlink`` returns exactly the Git blob target.
        """
        if resolve:
            self.resolve_commit(commit)
        script = (
            "set -euo pipefail\n"
            f'p={path!r}\n'
            f"f={self.mount_out}/$p\n"
            "if [ ! -L \"$f\" ]; then echo 'NOT_SYMLINK'; exit 22; fi\n"
            f"tgt=$(readlink \"$f\")\n"
            f"echo \"TARGET $tgt\"\n"
        )
        r = self._run_in_image(
            "bash",
            script,
            volumes=[f"{volume}:{self.mount_out}"],
        )
        if r.returncode != 0:
            return {
                "path": path,
                "is_symlink": False,
                "error": r.stdout.strip() or r.stderr.strip(),
            }
        target = None
        for line in r.stdout.splitlines():
            if line.startswith("TARGET "):
                target = line[len("TARGET "):].strip()
        return {
            "path": path,
            "is_symlink": True,
            "readlink": target,
            "expected_target": expected_target,
            "target_match": target == expected_target,
        }

    def materialized_tree_identity(self, commit: str, volume: str) -> str:
        """Deterministic identity of the materialized tree (sorted mode+path).

        Used to prove repeated materialization produces equivalent trees (P5)
        without byte-hashing every file.
        """
        resolved = self.resolve_commit(commit)
        script = (
            "set -euo pipefail\n"
            f"cd '{self.mount_out}'\n"
            "find . \\( -type f -o -type l \\) | sort | while read -r f; do\n"
            '  if [ -L "$f" ]; then\n'
            '    mode=$(stat -c %a "$f")\n'
            '    tgt=$(readlink "$f")\n'
            '    printf "%s %s -> %s\\n" "$mode" "${f#./}" "$tgt"\n'
            '  else\n'
            '    mode=$(stat -c %a "$f")\n'
            '    printf "%s %s\\n" "$mode" "${f#./}"\n'
            '  fi\n'
            "done\n"
        )
        r = self._run_in_image(
            "bash",
            script,
            volumes=[f"{volume}:{self.mount_out}"],
        )
        if r.returncode != 0:
            raise MaterializeError(
                f"tree identity scan failed (fail closed): {r.stdout.strip()} {r.stderr.strip()}"
            )
        _ = resolved
        return sha256_text("\n".join(sorted(r.stdout.splitlines())))


# ---------------------------------------------------------------------------
# Container orchestration helpers (volume lifecycle)
# ---------------------------------------------------------------------------


def ensure_empty_volume(backend: LinuxBackend, volume: str) -> None:
    """Create (or reset) a Linux Docker volume, guaranteeing it is empty."""
    r = backend.run(["volume", "rm", "-f", volume], timeout_s=120)
    if r.returncode != 0 and "No such volume" not in r.stderr:
        raise MaterializeError(f"volume reset failed for {volume!r}: {r.stderr.strip()}")
    r = backend.run(["volume", "create", volume], timeout_s=120)
    if r.returncode != 0:
        raise MaterializeError(f"volume create failed for {volume!r}: {r.stderr.strip()}")


def remove_volume(backend: LinuxBackend, volume: str) -> None:
    """Deterministically remove a volume; missing volume is not an error."""
    r = backend.run(["volume", "rm", "-f", volume], timeout_s=120)
    if r.returncode != 0 and "No such volume" not in r.stderr:
        raise MaterializeError(f"volume cleanup failed for {volume!r}: {r.stderr.strip()}")


def volume_exists(backend: LinuxBackend, volume: str) -> bool:
    r = backend.run(["volume", "inspect", volume], timeout_s=120)
    return r.returncode == 0
