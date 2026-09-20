"""PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2 — strict parent-only git history.

Deterministic, ZERO network, ZERO API. Builds a global per-repository commit
index (sha, subject, body, changed paths) from the local git caches, then
provides per-task ancestor filtering and production-changing filtering.

Visibility rule (frozen, mission §7):
  For a task with parent revision P, ONLY commits that are provably ancestors
  of P are visible. The target commit, all child revisions, future commits,
  future issue/PR metadata, and later branch state are forbidden. The
  construction FAILS CLOSED if temporal visibility cannot be proven.

Production-changing filter (frozen, mission §8):
  A commit is production-changing iff it modifies at least one file in the
  task's legal production universe (the frozen candidate_universe paths).
  Commits that modify ONLY files excluded by the benchmark's production-file
  policy are excluded.

Semantics (frozen, deterministic):
  - changed paths = the commit's diff paths from `git log --name-status`
    (M/A/D, and the NEW path for R/C). Merge commits contribute no file diff
    (git default), matching the existing project co-change convention.
  - C(f)        = number of parent-visible production-changing commits
                  touching f.
  - C(f, s)     = number touching both f and s.
  - history_change_count(f) = C(f).

All functions are pure given a repo path; results are cached on D: (outside
Git/export).
"""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

# History cache root OUTSIDE the repository (mission §30: keep large caches
# outside Git/export; prefer D: for large temporary/history cache data).
CACHE_ROOT = Path("D:/opencode_cache/memory_rescue_v2")

REPO_PATHS: dict[str, Path] = {
    "djangocms": PROJECT_DIR / "dist" / "real-commit-cache" / "djangocms",
    "saleor": PROJECT_DIR / "dist" / "pilot-repo-cache" / "saleor",
}

RECORD_SEP = "\x1e"
FIELD_SEP = "\x1f"
_FORMAT = f"--format={RECORD_SEP}%H{FIELD_SEP}%s{FIELD_SEP}%b{RECORD_SEP}"


@dataclass(frozen=True)
class CommitRecord:
    """One commit: sha, subject, body, and changed (diff) paths."""

    sha: str
    subject: str
    body: str
    paths: tuple[str, ...] = field(default_factory=tuple)

    @property
    def text(self) -> str:
        """Episodic document text = subject + body (frozen, mission §11)."""
        return f"{self.subject}\n{self.body}".strip()


def _git(repo: Path, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        check=False,
    )


def _parse_log(text: str) -> dict[str, CommitRecord]:
    """Parse `git log --name-status --format=...` output into sha -> record.

    Each commit is printed as:
        \x1e<sha>\x1f<subject>\x1f<body>\x1e\n<file lines>\n
    Splitting on \x1e therefore yields an alternating pattern of header
    segments (odd indices after the leading empty segment) and file-line
    segments (even indices). \x1e / \x1f are control characters that do not
    occur in commit messages or paths; a malformed record fails closed.
    """
    commits: dict[str, CommitRecord] = {}
    segments = text.split(RECORD_SEP)
    for idx in range(1, len(segments), 2):
        header = segments[idx]
        fields = header.split(FIELD_SEP, 2)
        if len(fields) < 1 or not fields[0]:
            raise RuntimeError(f"malformed commit header segment {idx!r}")
        sha = fields[0].strip()
        subject = fields[1].strip() if len(fields) > 1 else ""
        body = fields[2].strip() if len(fields) > 2 else ""
        files_text = segments[idx + 1] if idx + 1 < len(segments) else ""
        paths: list[str] = []
        for line in files_text.splitlines():
            line = line.strip()
            if not line or "\t" not in line:
                continue
            status, _, rest = line.partition("\t")
            if status[:1] in ("R", "C") and "\t" in rest:
                # rename/copy: keep the NEW path (deterministic; the path
                # matches the state where the file exists after the change).
                paths.append(rest.partition("\t")[2])
            else:
                paths.append(rest)
        commits[sha] = CommitRecord(sha=sha, subject=subject, body=body,
                                    paths=tuple(paths))
    if not commits:
        raise RuntimeError("no commits parsed from git log")
    return commits


class RepoHistory:
    """Global per-repository commit index + parent-only accessors.

    The index is built once per process from the local git cache and cached
    on D: (outside Git). All queries are pure given the index.
    """

    def __init__(self, repo: str) -> None:
        if repo not in REPO_PATHS:
            raise ValueError(f"unknown repository {repo!r}")
        self.repo = repo
        self.repo_path = REPO_PATHS[repo]
        if not self.repo_path.is_dir():
            raise FileNotFoundError(f"git cache missing: {self.repo_path}")
        self._commits: dict[str, CommitRecord] = {}
        self._load_index()

    # ---- index build / load -------------------------------------------------
    def _index_cache_path(self) -> Path:
        return CACHE_ROOT / f"{self.repo}_commits.json"

    def _load_index(self) -> None:
        cache = self._index_cache_path()
        if cache.exists():
            raw = json.loads(cache.read_text(encoding="utf-8"))
            self._commits = {
                sha: CommitRecord(sha=c["sha"], subject=c["subject"],
                                  body=c["body"], paths=tuple(c["paths"]))
                for sha, c in raw.items()
            }
            return
        proc = _git(self.repo_path, ["log", "--all", "--name-status", _FORMAT])
        if proc.returncode != 0:
            raise RuntimeError(
                f"git log failed for {self.repo}: {proc.stderr[:400]}")
        self._commits = _parse_log(proc.stdout)
        if not self._commits:
            raise RuntimeError(f"empty commit index for {self.repo}")
        CACHE_ROOT.mkdir(parents=True, exist_ok=True)
        cache.write_text(
            json.dumps(
                {sha: {"sha": c.sha, "subject": c.subject, "body": c.body,
                       "paths": list(c.paths)}
                 for sha, c in self._commits.items()},
                sort_keys=True),
            encoding="utf-8")

    # ---- parent-only accessors ----------------------------------------------
    def ancestors_of(self, parent: str) -> frozenset[str]:
        """Ancestors of P (P included) via `git rev-list`. FAIL CLOSED.

        Temporal visibility is proven by git itself: rev-list returns exactly
        the commits reachable from P (no descendant can be included).
        """
        proc = _git(self.repo_path, ["rev-list", parent])
        if proc.returncode != 0:
            raise RuntimeError(
                f"cannot prove ancestry of {parent[:12]} in {self.repo}: "
                f"{proc.stderr[:200]}")
        shas = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
        if not shas:
            raise RuntimeError(f"no ancestors returned for {parent[:12]}")
        return frozenset(shas)

    def commit(self, sha: str) -> CommitRecord | None:
        return self._commits.get(sha)

    def parent_visible_commits(self, parent: str) -> dict[str, CommitRecord]:
        """All commits strictly visible before P (ancestors, P included).

        FAIL CLOSED: if any ancestor commit is absent from the index (temporal
        visibility cannot be proven), raise RuntimeError.
        """
        out: dict[str, CommitRecord] = {}
        missing: list[str] = []
        for sha in self.ancestors_of(parent):
            rec = self._commits.get(sha)
            if rec is None:
                missing.append(sha)
                continue
            out[sha] = rec
        if missing:
            raise RuntimeError(
                f"{len(missing)} ancestor commit(s) of {parent[:12]} in "
                f"{self.repo} are missing from the index; temporal visibility "
                f"cannot be proven (fail-closed). first: "
                f"{missing[0][:12]}")
        return out

    def production_changing_commits(
        self, parent: str, production_universe: set[str],
    ) -> dict[str, CommitRecord]:
        """Parent-visible commits that touch >=1 legal production file.

        Fail closed: any ancestor commit missing from the index aborts.
        """
        out: dict[str, CommitRecord] = {}
        for sha, rec in self.parent_visible_commits(parent).items():
            paths = set(rec.paths)
            if not paths:
                # merge/empty-diff commits never change a production file
                continue
            if paths & production_universe:
                out[sha] = rec
        return out


class TaskHistory:
    """Per-task parent-visible history statistics (deterministic).

    Attributes (frozen semantics, mission §9/§11/§14):
      history_change_count[path] = C(path)
      commits                     = {sha: CommitRecord} of production-changing
                                    commits (parent-visible only).

    The full pair matrix is NOT materialized (too large). Pair counts to a
    single seed are computed on demand via cochange_counts_to(seed).
    """

    def __init__(self, repo_history: RepoHistory, parent: str,
                 production_universe: set[str]) -> None:
        self.repo = repo_history.repo
        self.parent = parent
        self.commits = repo_history.production_changing_commits(
            parent, production_universe)
        self._universe = frozenset(production_universe)

        c: dict[str, int] = {}
        for rec in self.commits.values():
            for p in set(rec.paths) & self._universe:
                c[p] = c.get(p, 0) + 1
        self.history_change_count = c

    def cochange_counts_to(self, seed: str) -> dict[str, int]:
        """C(f, seed) for every f in the universe (single pass).

        One pass over the production-changing commits touching `seed`; only
        the pair counts against ONE seed are produced (frozen §9 semantics).
        """
        out: dict[str, int] = {}
        for rec in self.commits.values():
            paths = set(rec.paths)
            if seed not in paths:
                continue
            for f in paths & self._universe:
                if f == seed:
                    continue
                out[f] = out.get(f, 0) + 1
        return out

    def n_production_changing_commits(self) -> int:
        return len(self.commits)

    def episode_documents(self) -> dict[str, str]:
        """sha -> commit text (subject + body) for production-changing commits."""
        return {sha: rec.text for sha, rec in self.commits.items()}
