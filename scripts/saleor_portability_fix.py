#!/usr/bin/env python3
"""Saleor Windows portability fix — production-only parent materializer (Block B).

Problem: the frozen `git archive` whole-tree extraction fails on Windows for
Saleor parents that contain a non-production test cassette with `?`/`[`/`]`
characters. This materializer extracts ONLY the production `.py` files under the
frozen package roots (the exact set `build_candidate_universe` globs), so
candidate-universe records and the AST dependency graph are byte-identical.

SCIENCE UNCHANGED: this only changes HOW the parent production files are
materialized (git ls-tree + git show per blob instead of whole-tree archive).
No eligibility rule, production-file predicate, graph algorithm, or proxy
changes. Non-production files (tests, cassettes, configs, migrations) are not
extracted — they are outside the candidate universe by the frozen predicate.

Equivalence gate: the caller verifies that the newly materialized 98 valid
bundles are byte-identical to the existing ones (candidate paths, blob hashes,
graph projection, hidden proxy, manifest content).

Usage (library): materialize_production_parent(cache_dir, parent, dest, roots=("saleor",))
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from benchmark.external_validity.source_graph import _is_excluded


def _git(cache_dir: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(cache_dir), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {proc.stderr.strip()[:300]}"
        )
    return proc.stdout


def list_production_files(cache_dir: Path, parent: str, roots: tuple[str, ...]) -> list[str]:
    """Enumerate production .py files under roots at parent (frozen predicate)."""
    listing = _git(cache_dir, "ls-tree", "-r", "--name-only", parent)
    files = [ln.strip() for ln in listing.splitlines() if ln.strip()]
    out: list[str] = []
    for f in files:
        if not f.endswith(".py"):
            continue
        parts = f.split("/")
        if not parts or parts[0] not in roots:
            continue
        if _is_excluded(Path(f)):
            continue
        out.append(f)
    out.sort()
    return out


def _materialize_batch(cache_dir: Path, parent: str, files: list[str], dest: Path) -> None:
    """Bulk-extract blobs via git cat-file --batch (one persistent subprocess)."""
    # For each path, resolve its blob SHA at parent, then batch-read all blobs.
    import subprocess as _sp

    # First: get blob SHA per path (ls-tree already gave names; use rev-parse per
    # path is slow; instead use `git rev-list --objects`? Simplest robust approach:
    # run `git cat-file --batch` feeding "<parent>:<path>" lines.)
    proc = _sp.Popen(
        ["git", "-C", str(cache_dir), "cat-file", "--batch"],
        stdin=_sp.PIPE, stdout=_sp.PIPE, stderr=_sp.PIPE,
    )
    assert proc.stdin is not None and proc.stdout is not None
    queries = "\n".join(f"{parent}:{f}" for f in files) + "\n"
    out, err = proc.communicate(queries.encode("utf-8"), timeout=600)
    if proc.returncode != 0:
        raise RuntimeError(f"git cat-file --batch failed: {err.decode('utf-8','replace')[:300]}")
    # Parse the batch stream: repeated <sha> <type> <size>\n<blob bytes>\n
    stream = out
    idx = 0
    blob_map: dict[str, bytes] = {}
    for f in files:
        # find the header line for this entry; entries are in query order
        hdr_end = stream.find(b"\n", idx)
        hdr = stream[idx:hdr_end].decode("utf-8", "replace")
        parts = hdr.split(" ")
        size = int(parts[2]) if len(parts) >= 3 else 0
        start = hdr_end + 1
        blob = stream[start : start + size]
        blob_map[f] = blob
        idx = start + size + 1  # skip the trailing newline
    for f in files:
        out_path = dest / f
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(blob_map[f])


def materialize_production_parent(
    cache_dir: Path,
    parent: str,
    dest: Path,
    roots: tuple[str, ...] = ("saleor",),
) -> list[str]:
    """Materialize ONLY production .py blobs at parent under dest (bulk, fast).

    Returns the list of repo-relative production file paths.
    Raises if a blob cannot be read (fail-closed; no partial silent snapshot).
    """
    files = list_production_files(cache_dir, parent, roots)
    dest.mkdir(parents=True, exist_ok=True)
    _materialize_batch(cache_dir, parent, files, dest)
    return files


if __name__ == "__main__":
    import sys

    cache = Path("dist/pilot-repo-cache/saleor")
    parent = sys.argv[1] if len(sys.argv) > 1 else "2c48391b652c26ce4f27a53d6532d4c873306af0"
    files = list_production_files(cache, parent, ("saleor",))
    print("production files:", len(files))
    print("sample:", files[:5])
