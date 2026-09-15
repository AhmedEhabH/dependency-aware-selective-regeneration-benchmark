"""Corpus construction for cheap baselines.

A corpus is the per-candidate text representation used by the lexical and
hybrid baselines. Two deterministic sources:

- ``MetadataCorpus``: candidate metadata only (module, classes, functions) —
  always available from the public candidate universe, no git required.
- ``GitParentCorpus``: the candidate file's repository content **at the parent
  commit only** (never the target/future state), fetched from the frozen
  upstream cache repository via ``git show <parent>:<path>``.

Both are strictly parent-visible: the proxy / future diff never enters.
Properties:

- ``texts``  : ``dict[path, str]`` per-candidate text representation.
- ``source`` : corpus provenance label (``metadata`` | ``parent_commit``).
- ``parent_commit`` : the exact commit the corpus was built from.
"""

from __future__ import annotations

import hashlib
import io
import json
import subprocess
import tarfile
import tempfile
from collections.abc import Collection
from dataclasses import dataclass, field
from pathlib import Path

from .tokenize import tokenize

REPO_DJANGOCMS = "https://github.com/django-cms/django-cms"

CandidateRecord = dict[str, object]


def _string_list(rec: CandidateRecord, key: str) -> list[str]:
    """Safely extract a list of strings (e.g. classes/functions) from a record."""
    value = rec.get(key)
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if isinstance(x, str)]
    if isinstance(value, str):
        return [value]
    return []


def _canonical_hash(payload: dict[str, Collection[str] | str]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CandidateCorpus:
    """Parent-only per-candidate text representation for one case."""

    source: str
    parent_commit: str
    texts: dict[str, str]
    sha256: str = field(default="")

    def __post_init__(self) -> None:
        canonical = {
            "source": self.source,
            "parent_commit": self.parent_commit,
            "texts": self.texts,
        }
        object.__setattr__(self, "sha256", _canonical_hash(canonical))

    def text_for(self, path: str) -> str:
        return self.texts.get(path, "")

    def doc_id_set(self) -> tuple[str, ...]:
        return tuple(sorted(self.texts))


def MetadataCorpus(  # noqa: N802 - constructor-style factory, keyword-only args
    *,
    parent_commit: str,
    candidate_records: tuple[CandidateRecord, ...],
) -> CandidateCorpus:
    """Build a metadata text representation from candidate-universe records.

    Text = module + classes + functions per candidate. Tokens are the same
    deterministic tokenizer used elsewhere. Purely parent-visible public
    metadata; zero git access.
    """
    texts: dict[str, str] = {}
    for rec in candidate_records:
        path = str(rec.get("path", ""))
        module = str(rec.get("module", ""))
        classes = " ".join(_string_list(rec, "classes"))
        functions = " ".join(_string_list(rec, "functions"))
        texts[path] = f"{module} {classes} {functions}".strip()
    return CandidateCorpus(
        source="metadata",
        parent_commit=parent_commit,
        texts=texts,
    )


def _run_git(cache_dir: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cache_dir), *args],
        capture_output=True,
        text=True,
        check=False,
        encoding="utf-8",
        errors="replace",
    )


def _materialize_parent_tree(cache_dir: str, parent_commit: str, dest: Path) -> None:
    """Materialize the parent tree(s) via ``git archive`` (one subprocess)."""
    result = subprocess.run(
        ["git", "-C", str(cache_dir), "archive", "--format=tar", parent_commit],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git archive failed for parent {parent_commit}: "
            f"{result.stderr.decode('utf-8', 'replace')}"
        )
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r|") as tf:
        tf.extractall(dest, filter="data")


def GitParentCorpus(  # noqa: N802 - constructor-style factory, keyword-only args
    *,
    cache_dir: str,
    parent_commit: str,
    candidate_paths: tuple[str, ...],
) -> CandidateCorpus:
    """Build a parent-commit file-content corpus from the frozen cache repo.

    The parent commit tree is materialized once via ``git archive`` (a single
    subprocess, parent revision only) and each candidate file is read from the
    materialized tree. A missing file at parent yields empty text (fail-closed,
    deterministic). Raises if the parent commit is not present in the cache
    (indexing from a future/unavailable state would be invalid).
    """
    probe = _run_git(cache_dir, "cat-file", "-t", parent_commit)
    if probe.returncode != 0 or probe.stdout.strip() != "commit":
        raise RuntimeError(
            f"parent commit {parent_commit} not available in cache {cache_dir} "
            f"(indexing requires parent-state corpus)"
        )
    texts: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="cb-parent-") as tmp:
        tree = Path(tmp)
        _materialize_parent_tree(cache_dir, parent_commit, tree)
        for path in candidate_paths:
            file_path = tree / path
            if file_path.is_file():
                texts[path] = file_path.read_text(encoding="utf-8", errors="replace")
            else:
                texts[path] = ""
    return CandidateCorpus(
        source=f"parent_commit:{parent_commit}",
        parent_commit=parent_commit,
        texts=texts,
    )


def corpus_tokens(corpus_text: str) -> frozenset[str]:
    """Deterministic token set for one candidate's corpus text."""
    return frozenset(tokenize(corpus_text))
