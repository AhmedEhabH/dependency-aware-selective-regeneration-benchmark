from __future__ import annotations

import fnmatch
import time
from dataclasses import dataclass
from pathlib import Path

BINARY_EXTENSIONS: frozenset[str] = frozenset({
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".dylib",
    ".exe", ".bin", ".dat", ".db", ".sqlite", ".sqlite3",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip", ".tar",
    ".gz", ".bz2", ".7z", ".rar", ".whl", ".egg", ".lock",
})

MAX_FILE_SIZE: int = 200 * 1024  # 200 KB
MAX_LIST_ENTRIES: int = 200
MAX_READ_CHARS: int = 12000
MAX_SEARCH_RESULTS: int = 50
MAX_DISTINCT_FILES: int = 30

SKIP_PATTERNS: tuple[str, ...] = (
    ".git/*",
    "__pycache__/*",
    ".pytest_cache/*",
    ".eggs/*",
    "*.pyc",
    "*.pyo",
    ".DS_Store",
)


@dataclass(frozen=True)
class RepositoryToolResult:
    ok: bool
    output: str
    error: str = ""
    duration_seconds: float = 0.0


class RepositoryTools:
    def __init__(self, workspace_root: str | Path, max_distinct_files: int = MAX_DISTINCT_FILES) -> None:
        self._root = Path(workspace_root).resolve()
        self._max_distinct_files = max_distinct_files
        self._inspected: set[str] = set()

    @property
    def inspected_files(self) -> set[str]:
        return set(self._inspected)

    @property
    def distinct_file_count(self) -> int:
        return len(self._inspected)

    def _resolve(self, path: str) -> Path | None:
        stripped = path.strip("/\\")
        if not stripped:
            return None
        resolved = (self._root / stripped).resolve()
        try:
            resolved.relative_to(self._root)
        except ValueError:
            return None
        if ".." in Path(stripped).parts:
            return None
        if "\\" in path:
            return None
        if Path(stripped).is_absolute():
            return None
        if resolved.is_symlink():
            link_target = resolved.resolve(strict=False)
            try:
                link_target.relative_to(self._root)
            except ValueError:
                return None
        return resolved

    def _reserve_inspected_file(self, resolved: Path) -> str | None:
        rel = resolved.relative_to(self._root).as_posix()
        if self._skip(rel):
            return "Skipped path"
        if rel in self._inspected:
            return None
        if len(self._inspected) >= self._max_distinct_files:
            return f"Max distinct files limit ({self._max_distinct_files}) reached"
        self._inspected.add(rel)
        return None

    def _skip(self, rel: str) -> bool:
        return any(fnmatch.fnmatch(rel, pat) for pat in SKIP_PATTERNS)

    def _err(self, msg: str, t0: float) -> RepositoryToolResult:
        return RepositoryToolResult(ok=False, output="", error=msg, duration_seconds=time.monotonic() - t0)

    def _ok(self, out: str, t0: float) -> RepositoryToolResult:
        return RepositoryToolResult(ok=True, output=out, duration_seconds=time.monotonic() - t0)

    def list_files(self, path: str = ".") -> RepositoryToolResult:
        t0 = time.monotonic()
        resolved = self._resolve(path)
        if resolved is None:
            return self._err("Invalid path", t0)
        if not resolved.is_dir():
            return self._err("Not a directory", t0)
        results: list[str] = []
        for entry in sorted(resolved.rglob("*")):
            rel = entry.relative_to(self._root).as_posix()
            if self._skip(rel):
                continue
            if entry.is_file() and entry.stat().st_size > MAX_FILE_SIZE:
                continue
            if entry.suffix in BINARY_EXTENSIONS:
                continue
            if entry.is_dir():
                results.append(rel + "/")
            else:
                results.append(rel)
            if len(results) >= MAX_LIST_ENTRIES:
                break
        return self._ok("\n".join(results), t0)

    def read_file(self, path: str) -> RepositoryToolResult:
        t0 = time.monotonic()
        resolved = self._resolve(path)
        if resolved is None:
            return self._err("Invalid path", t0)
        if not resolved.is_file():
            return self._err("Not a file", t0)
        if resolved.stat().st_size > MAX_FILE_SIZE:
            return self._err("File too large", t0)
        if resolved.suffix in BINARY_EXTENSIONS:
            return self._err("Binary file", t0)
        err = self._reserve_inspected_file(resolved)
        if err is not None:
            return self._err(err, t0)
        try:
            text = resolved.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return self._err("Cannot read file", t0)
        if len(text) > MAX_READ_CHARS:
            text = text[:MAX_READ_CHARS]
        return self._ok(text, t0)

    def search_text(self, query: str, path: str = ".") -> RepositoryToolResult:
        t0 = time.monotonic()
        if not query:
            return self._err("Empty query", t0)
        resolved = self._resolve(path)
        if resolved is None:
            return self._err("Invalid path", t0)
        if not resolved.is_dir():
            return self._err("Not a directory", t0)
        matches: list[str] = []
        query_lower = query.lower()
        for entry in sorted(resolved.rglob("*")):
            if not entry.is_file():
                continue
            resolved_entry = entry.resolve()
            try:
                resolved_entry.relative_to(self._root)
            except ValueError:
                continue
            rel = entry.relative_to(self._root).as_posix()
            if self._skip(rel):
                continue
            err = self._reserve_inspected_file(resolved_entry)
            if err is not None:
                return self._err(err, t0) if not matches else self._ok("\n".join(matches), t0)
            if entry.stat().st_size > MAX_FILE_SIZE:
                continue
            if entry.suffix in BINARY_EXTENSIONS:
                continue
            try:
                for i, line in enumerate(entry.read_text(encoding="utf-8").splitlines(), 1):
                    if query_lower in line.lower():
                        matches.append(f"{rel}:{i}:{line.strip()[:200]}")
                        if len(matches) >= MAX_SEARCH_RESULTS:
                            return self._ok("\n".join(matches), t0)
            except (OSError, UnicodeDecodeError):
                continue
        return self._ok("\n".join(matches), t0)
