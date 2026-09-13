"""RealCommitImpactDataset-v1 miner (M4A-1).

Deterministic, auditable miner for real historical djangoCMS commits.

HARD RULES
- Uses the system ``git`` CLI through ``subprocess`` (no GitPython).
- Every checkout/acquire operation is explicit and FAILS CLOSED on SHA mismatch.
- Parent commit P = the single parent of target T.
- Candidate universe and dependency graph are built from P ONLY.
- The hidden observed change-set proxy (diff P -> T) is NEVER written into the
  public inference bundle (public/ artifacts).
- No P/R/V/H semantic gold is fabricated from the diff.
- ZERO scientific LLM/API calls.
"""

from __future__ import annotations

import io
import re
import shutil
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from benchmark.external_validity.source_graph import (
    EXCLUDED_DIR_SEGMENTS,
    build_candidate_universe,
    build_dependency_graph,
    canonical_graph_hash,
    canonical_universe_hash,
    extractor_source_hash,
)
from benchmark.real_commits.models import (
    DJANGOCMS_ANCHOR_COMMIT,
    EXCLUSION_REASON_CODES,
    LICENSE_MANIFEST_REF,
    MINER_VERSION,
    REPOSITORY_URL_DJANGOCMS,
    SCHEMA_VERSION,
    SplitRole,
    canonical_json,
    compute_canonical_record_hash,
    sha256_json,
    sha256_text,
)

PRODUCTION_ROOTS: tuple[str, ...] = ("cms", "menus")

# Test path detection: any path segment in this set marks a test path.
TEST_DIR_SEGMENTS: frozenset[str] = frozenset({"tests", "test_utils"})

# Migration path detection.
MIGRATION_SEGMENTS: frozenset[str] = frozenset({"migrations"})

# Generated / vendor detection (conservative).
GENERATED_VENDOR_SUFFIXES: tuple[str, ...] = (
    ".po",
    ".mo",
    ".min.js",
    ".min.css",
    ".map",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".lock",
)
GENERATED_VENDOR_DIR_SEGMENTS: frozenset[str] = frozenset(
    {"static", "locale", "node_modules", "vendor", "docs", ".github", "js", "css", "sass"}
)
GENERATED_VENDOR_FILENAMES: frozenset[str] = frozenset(
    {"package-lock.json", "yarn.lock", "poetry.lock", "Pipfile.lock", "package.json"}
)

_BOT_OR_RELEASE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*(?:chore\s*:\s*)?(?:release|bump|version)\b", re.IGNORECASE),
    re.compile(r"^bump\b", re.IGNORECASE),
    re.compile(r"dependabot", re.IGNORECASE),
    re.compile(r"renovate", re.IGNORECASE),
    re.compile(r"\[ci\s+skip\]", re.IGNORECASE),
    re.compile(r"^update\s+changelog", re.IGNORECASE),
    re.compile(r"^changelog", re.IGNORECASE),
    re.compile(r"^merge\s+(?:branch|back|pull|request)", re.IGNORECASE),
    re.compile(r"^merge back", re.IGNORECASE),
)

CONVENTIONAL_TYPE_PREFIXES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^fix(?:\([^)]*\))?\s*:"), "bugfix"),
    (re.compile(r"^feat(?:\([^)]*\))?\s*:"), "feature"),
    (re.compile(r"^refactor(?:\([^)]*\))?\s*:"), "refactor"),
    (re.compile(r"^perf(?:\([^)]*\))?\s*:"), "refactor"),
    (re.compile(r"^style(?:\([^)]*\))?\s*:"), "style"),
    (re.compile(r"^docs?(?:\([^)]*\))?\s*:"), "docs"),
    (re.compile(r"^build(?:\([^)]*\))?\s*:"), "build"),
    (re.compile(r"^ci(?:\([^)]*\))?\s*:"), "ci"),
    (re.compile(r"^test(?:\([^)]*\))?\s*:"), "test"),
    (re.compile(r"^chore(?:\([^)]*\))?\s*:"), "chore"),
)


# ---------------------------------------------------------------------------
# Git subprocess helpers (fail closed)
# ---------------------------------------------------------------------------


def run_git(cache_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run a git command in the cache repository, fail closed on nonzero exit."""
    result = subprocess.run(
        ["git", "-C", str(cache_dir), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git {args[0]} failed (rc={result.returncode}): {result.stderr.strip()}"
        )
    return result


def git_output(cache_dir: Path, *args: str) -> str:
    return run_git(cache_dir, *args).stdout


def verify_commit_sha(cache_dir: Path, sha: str) -> str:
    """Resolve and verify a full commit SHA, fail closed on mismatch."""
    out = git_output(cache_dir, "rev-parse", "--verify", f"{sha}^{{commit}}").strip()
    if out != sha:
        raise ValueError(
            f"commit SHA mismatch: requested {sha}, git resolved {out}"
        )
    typ = git_output(cache_dir, "cat-file", "-t", sha).strip()
    if typ != "commit":
        raise ValueError(f"object {sha} is {typ!r}, expected 'commit'")
    return out


def acquire_cache(cache_dir: Path, url: str, anchor: str, *, force: bool = False) -> None:
    """Clone the upstream repository into the ignored cache if missing.

    Fails closed if the anchor SHA cannot be verified after acquisition.
    """
    if cache_dir.is_dir() and (cache_dir / ".git").is_dir() and not force:
        verify_commit_sha(cache_dir, anchor)
        return
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    cache_dir.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "clone", "--no-checkout", url, str(cache_dir)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git clone failed: {result.stderr.strip()}")
    verify_commit_sha(cache_dir, anchor)


# ---------------------------------------------------------------------------
# Commit enumeration + diff extraction
# ---------------------------------------------------------------------------


@dataclass
class CommitInfo:
    sha: str
    parents: tuple[str, ...]
    commit_time_utc: str
    subject: str
    body: str

    @property
    def message(self) -> str:
        if self.body:
            return f"{self.subject}\n{self.body}"
        return self.subject


def commit_info(cache_dir: Path, sha: str) -> CommitInfo:
    verify_commit_sha(cache_dir, sha)
    out = git_output(
        cache_dir,
        "log",
        "-1",
        "--format=%H%x1f%P%x1f%ct%x1f%s%x1f%b",
        sha,
    ).strip()
    parts = out.split("\x1f")
    commit_sha = parts[0]
    parents = tuple(p for p in parts[1].split() if p)
    ctime = datetime.fromtimestamp(int(parts[2]), tz=UTC).isoformat()
    subject = parts[3]
    body = parts[4] if len(parts) > 4 else ""
    if commit_sha != sha:
        raise ValueError(f"git log returned {commit_sha}, expected {sha}")
    return CommitInfo(sha=sha, parents=parents, commit_time_utc=ctime, subject=subject, body=body)


def diff_name_status(cache_dir: Path, parent: str, target: str) -> dict[str, str]:
    """Return {path: status} for diff parent->target using --name-status."""
    verify_commit_sha(cache_dir, parent)
    verify_commit_sha(cache_dir, target)
    out = git_output(cache_dir, "diff-tree", "--name-status", "-r", parent, target)
    mapping: dict[str, str] = {}
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith(("R", "C")):
            # Rename/copy: status\told\tnew
            if len(parts) >= 3:
                mapping[parts[2]] = status
        else:
            path = parts[1] if len(parts) > 1 else ""
            if path:
                mapping[path] = status
    return mapping


def production_diff_is_whitespace_only(
    cache_dir: Path, parent: str, target: str, proxy_paths: tuple[str, ...]
) -> bool:
    """True when the production diff reduces to whitespace under ``git diff -w``.

    Uses ``git diff --quiet -w`` (exit 0 = no non-whitespace difference), which is
    the exact ``git diff -w`` check the v1 rules require.
    """
    if not proxy_paths:
        return False
    result = subprocess.run(
        ["git", "-C", str(cache_dir), "diff", "--quiet", "-w", parent, target, "--", *proxy_paths],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


# ---------------------------------------------------------------------------
# Path classification
# ---------------------------------------------------------------------------


def is_tests_path(path: str) -> bool:
    parts = Path(path).parts
    return any(part in TEST_DIR_SEGMENTS for part in parts)


def is_migration_path(path: str) -> bool:
    parts = Path(path).parts
    return any(part in MIGRATION_SEGMENTS for part in parts)


def is_generated_or_vendor_path(path: str) -> bool:
    parts = Path(path).parts
    if any(part in GENERATED_VENDOR_DIR_SEGMENTS for part in parts):
        return True
    if Path(path).name in GENERATED_VENDOR_FILENAMES:
        return True
    return path.endswith(GENERATED_VENDOR_SUFFIXES)


def is_production_python(path: str) -> bool:
    """Production Python under the configured production roots, not excluded.

    Mirrors the frozen candidate-universe extraction in source_graph.py.
    """
    if not path.endswith(".py"):
        return False
    parts = Path(path).parts
    if not parts or parts[0] not in PRODUCTION_ROOTS:
        return False
    return not any(part in EXCLUDED_DIR_SEGMENTS for part in parts)


def classify_paths(
    name_status: dict[str, str],
) -> dict[str, list[str]]:
    """Classify changed paths into production/tests/migrations/generated/other."""
    classified: dict[str, list[str]] = {
        "production": [],
        "tests": [],
        "migrations": [],
        "generated_vendor": [],
        "other": [],
    }
    for path in sorted(name_status):
        if is_tests_path(path):
            classified["tests"].append(path)
        elif is_migration_path(path):
            classified["migrations"].append(path)
        elif is_generated_or_vendor_path(path):
            classified["generated_vendor"].append(path)
        elif is_production_python(path):
            classified["production"].append(path)
        else:
            classified["other"].append(path)
    return classified


# ---------------------------------------------------------------------------
# Intent normalization + leakage detection
# ---------------------------------------------------------------------------


def normalize_intent(message: str) -> str:
    """Normalize commit message: collapse whitespace, strip, keep first line strong."""
    lines = [ln.strip() for ln in message.splitlines()]
    lines = [ln for ln in lines if ln]
    if not lines:
        return ""
    joined = " ".join(lines)
    return re.sub(r"\s+", " ", joined).strip()


def meaningful_intent(intent: str) -> bool:
    """Non-empty, human-readable intent not dominated by bot/release/changelog text."""
    if not intent or len(intent.strip()) < 5:
        return False
    return not any(pattern.search(intent) for pattern in _BOT_OR_RELEASE_PATTERNS)


def infer_change_type(intent: str) -> str:
    for pattern, kind in CONVENTIONAL_TYPE_PREFIXES:
        if pattern.search(intent):
            return kind
    return "unknown"


def intent_mentions_changed_path(intent: str, proxy_paths: tuple[str, ...]) -> bool:
    """Detect exact repo-relative path mentions and obvious basename mentions.

    Conservative detector: a proxy path is 'mentioned' if the exact normalized
    repo-relative path, its basename, or its basename stem appears in the intent.
    """
    for path in proxy_paths:
        norm = path.replace("\\", "/")
        if norm in intent:
            return True
        basename = Path(norm).name
        if basename and basename in intent:
            return True
        stem = Path(basename).stem
        if stem and stem in intent:
            return True
    return False


# ---------------------------------------------------------------------------
# Eligibility evaluation (v1 rules)
# ---------------------------------------------------------------------------


def _no_production_reason(classified: dict[str, list[str]]) -> str:
    """Conservative reason code when a commit has no production python change."""
    has_tests = bool(classified["tests"])
    has_migrations = bool(classified["migrations"])
    has_generated = bool(classified["generated_vendor"])
    has_other = bool(classified["other"])

    if has_tests and not (has_migrations or has_generated or has_other):
        return "tests_only"
    if has_migrations and not (has_tests or has_generated or has_other):
        return "migrations_only"
    if has_generated and not (has_tests or has_migrations or has_other):
        return "generated_or_vendor_only"
    return "no_production_source_change"


def evaluate_eligibility(
    *,
    parents: tuple[str, ...],
    intent: str,
    name_status: dict[str, str],
    proxy_min: int = 1,
    proxy_max: int = 12,
    total_diff_ceiling: int = 40,
    allow_intent_path_leakage: bool = False,
) -> dict[str, Any]:
    """Apply the frozen v1 eligibility rules. Returns decision + reason codes.

    The proxy-subset-of-parent-universe check is intentionally NOT evaluated here
    (it requires building the parent universe); it is verified during case build
    and recorded there. ``allow_intent_path_leakage=True`` permits keeping a dev
    case that mentions a changed path (must be marked, never HELD_OUT_TEST).
    """
    reasons: list[str] = []

    if len(parents) != 1:
        reasons.append("merge_commit")

    if not meaningful_intent(intent):
        reasons.append("no_meaningful_intent")

    classified = classify_paths(name_status)
    proxy = tuple(classified["production"])
    total_changed = len(name_status)

    if not proxy:
        reasons.append(_no_production_reason(classified))

    if proxy and any(status != "M" for status in (name_status[p] for p in proxy)):
        reasons.append("production_add_delete_rename_copy_v1_unsupported")

    if proxy and not (proxy_min <= len(proxy) <= proxy_max):
        reasons.append("proxy_too_large")

    if total_changed > total_diff_ceiling:
        reasons.append("diff_too_large")

    leaked = bool(proxy) and intent_mentions_changed_path(intent, proxy)
    if leaked and not allow_intent_path_leakage:
        reasons.append("intent_path_leakage")

    # Deduplicate while preserving the frozen canonical order.
    ordered = [code for code in EXCLUSION_REASON_CODES if code in reasons]
    eligible = not ordered

    return {
        "eligible": eligible,
        "decision": "ELIGIBLE" if eligible else "INELIGIBLE",
        "reason_codes": ordered,
        "proxy_paths": proxy,
        "proxy_count": len(proxy),
        "total_changed": total_changed,
        "intent_mentions_changed_path": leaked,
        "change_type": infer_change_type(intent),
        "classified": classified,
    }


# ---------------------------------------------------------------------------
# Parent checkout + candidate universe + graph (P only)
# ---------------------------------------------------------------------------


def extract_parent_tree(cache_dir: Path, parent: str, dest: Path) -> None:
    """Materialize the parent commit tree via ``git archive`` (P only).

    Explicit and fail-closed on SHA mismatch.
    """
    verify_commit_sha(cache_dir, parent)
    result = subprocess.run(
        ["git", "-C", str(cache_dir), "archive", "--format=tar", parent],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git archive failed for {parent}: {result.stderr.decode('utf-8', 'replace')}"
        )
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r|") as tf:
        tf.extractall(dest, filter="data")


def build_parent_universe_and_graph(
    cache_dir: Path,
    parent: str,
) -> dict[str, Any]:
    """Build candidate universe + dependency graph from the parent commit only.

    Returns a dict with the records, canonical hashes, and graph artifact.
    """
    with tempfile.TemporaryDirectory(prefix="rc-parent-") as tmp:
        tmp_path = Path(tmp)
        extract_parent_tree(cache_dir, parent, tmp_path)
        records = build_candidate_universe(tmp_path, package_roots=PRODUCTION_ROOTS)
        universe_hash = canonical_universe_hash(records)
        extractor_hash = extractor_source_hash()
        generated_utc = datetime.now(UTC).isoformat()
        graph = build_dependency_graph(
            repo_root=tmp_path,
            records=records,
            pinned_commit=parent,
            candidate_universe_hash=universe_hash,
            extractor_hash=extractor_hash,
            generated_utc=generated_utc,
            repo_id="djangocms",
            version="historical-parent",
        )
        graph_hash = canonical_graph_hash(graph)
    return {
        "records": records,
        "universe_count": len(records),
        "universe_hash": universe_hash,
        "graph": graph,
        "graph_node_count": graph["node_count"],
        "graph_edge_count": graph["edge_count"],
        "graph_hash": graph_hash,
        "parent": parent,
    }


# ---------------------------------------------------------------------------
# Case builder (public/hidden separation)
# ---------------------------------------------------------------------------


def build_case(
    *,
    cache_dir: Path,
    case_id: str,
    target: str,
    parent: str,
    name_status: dict[str, str],
    eligibility: dict[str, Any],
    output_dir: Path,
    created_utc: str,
) -> Path:
    """Build one MINER_DEV case with physical public/hidden separation.

    Returns the case directory path.
    """
    proxy_paths = tuple(eligibility["proxy_paths"])
    if not proxy_paths:
        raise ValueError(f"case {case_id}: no production proxy paths")

    universe_and_graph = build_parent_universe_and_graph(cache_dir, parent)
    universe_paths = {str(rec["path"]) for rec in universe_and_graph["records"]}

    # proxy must be a subset of the parent universe
    missing = sorted(p for p in proxy_paths if p not in universe_paths)
    if missing:
        raise ValueError(
            f"case {case_id}: proxy paths not in parent universe: {missing}"
        )

    info = commit_info(cache_dir, target)
    intent = normalize_intent(info.message)
    intent_hash = sha256_text(intent)

    proxy_statuses = {path: name_status[path] for path in proxy_paths}
    proxy_hash = sha256_json(proxy_statuses)

    case_dir = output_dir / case_id
    public_dir = case_dir / "public"
    hidden_dir = case_dir / "hidden"
    public_dir.mkdir(parents=True, exist_ok=True)
    hidden_dir.mkdir(parents=True, exist_ok=True)

    # Public artifacts (inference-time surface).
    intent_payload = {
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "intent_text": intent,
        "intent_source": "commit_message",
        "intent_sha256": intent_hash,
        "target_commit": target,
        "target_commit_time": info.commit_time_utc,
    }
    intent_path = public_dir / "intent.json"
    intent_path.write_text(canonical_json(intent_payload), encoding="utf-8")

    universe_path = public_dir / "candidate_universe.json"
    universe_path.write_text(
        canonical_json(
            {
                "schema_version": SCHEMA_VERSION,
                "case_id": case_id,
                "parent_commit": parent,
                "count": universe_and_graph["universe_count"],
                "sha256": universe_and_graph["universe_hash"],
                "records": universe_and_graph["records"],
            }
        ),
        encoding="utf-8",
    )

    graph_path = public_dir / "dependency_graph.json"
    graph_path.write_text(canonical_json(universe_and_graph["graph"]), encoding="utf-8")

    # Hidden artifact (evaluation-only observed change-set proxy).
    proxy_payload = {
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "parent_commit": parent,
        "target_commit": target,
        "paths": list(proxy_paths),
        "count": len(proxy_paths),
        "statuses": proxy_statuses,
        "sha256": proxy_hash,
    }
    proxy_path = hidden_dir / "observed_change_set_proxy.json"
    proxy_path.write_text(canonical_json(proxy_payload), encoding="utf-8")

    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "case_id": case_id,
        "repository": "djangocms",
        "repository_url": REPOSITORY_URL_DJANGOCMS,
        "repository_license_or_manifest_ref": LICENSE_MANIFEST_REF,
        "parent_commit": parent,
        "target_commit": target,
        "target_commit_time": info.commit_time_utc,
        "intent_text": intent,
        "intent_source": "commit_message",
        "intent_sha256": intent_hash,
        "candidate_universe_artifact": "public/candidate_universe.json",
        "candidate_universe_count": universe_and_graph["universe_count"],
        "candidate_universe_sha256": universe_and_graph["universe_hash"],
        "dependency_graph_artifact": "public/dependency_graph.json",
        "dependency_graph_sha256": universe_and_graph["graph_hash"],
        "observed_change_set_proxy_artifact": "hidden/observed_change_set_proxy.json",
        "observed_change_set_proxy_count": len(proxy_paths),
        "observed_change_set_proxy_sha256": proxy_hash,
        "change_statuses": {p: name_status[p] for p in proxy_paths},
        "rename_delete_metadata": {},
        "change_type": eligibility["change_type"],
        "eligibility_decision": eligibility["decision"],
        "eligibility_reason_codes": eligibility["reason_codes"],
        "intent_mentions_changed_path": bool(eligibility["intent_mentions_changed_path"]),
        "partition_role": "MINER_DEVELOPMENT",
        "split": SplitRole.MINER_DEV.value,
        "miner_version": MINER_VERSION,
        "provenance_hashes": {
            "miner_version": MINER_VERSION,
            "schema_version": SCHEMA_VERSION,
            "extractor_version": "1.0.0",
            "extractor_source_hash": extractor_source_hash(),
            "anchor_commit": DJANGOCMS_ANCHOR_COMMIT,
            "repository_url": REPOSITORY_URL_DJANGOCMS,
        },
        "created_utc": created_utc,
        "canonical_record_sha256": "",
    }
    record["canonical_record_sha256"] = compute_canonical_record_hash(record)

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "miner_version": MINER_VERSION,
        "record": record,
        "public_artifact_paths": {
            "intent": "public/intent.json",
            "candidate_universe": "public/candidate_universe.json",
            "dependency_graph": "public/dependency_graph.json",
        },
        "hidden_artifact_paths": {
            "observed_change_set_proxy": "hidden/observed_change_set_proxy.json",
        },
        "canonical_record_sha256": record["canonical_record_sha256"],
    }
    manifest_path = case_dir / "case_manifest.json"
    manifest_path.write_text(canonical_json(manifest), encoding="utf-8")
    return case_dir


# ---------------------------------------------------------------------------
# Deterministic selection of MINER_DEV cases
# ---------------------------------------------------------------------------


def enumerate_ancestors(cache_dir: Path, anchor: str) -> list[str]:
    """Enumerate commits reachable from the anchor in deterministic topo order.

    Newest-first topological order (git rev-list default), which is deterministic.
    """
    verify_commit_sha(cache_dir, anchor)
    out = git_output(cache_dir, "rev-list", "--topo-order", anchor)
    shas = [ln.strip() for ln in out.splitlines() if ln.strip()]
    return shas


def select_miner_dev_cases(
    cache_dir: Path,
    anchor: str,
    *,
    max_cases: int = 6,
    window: int | None = None,
    proxy_max: int = 12,
    total_diff_ceiling: int = 40,
    skip_anchor: bool = True,
    max_leak_cases: int = 1,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Deterministically select MINER_DEV cases from real djangoCMS history.

    Scans newest-first (most recent ancestors first), applies frozen v1 filters,
    prefers distinct proxy-size shapes, and keeps at most ``max_leak_cases`` cases
    whose intent mentions a changed path (spec section 9: MINER_DEV may keep one
    such case to test the detector; it is permanently excluded from held-out).
    Returns (chosen, scan_summary).
    """
    ancestors = enumerate_ancestors(cache_dir, anchor)
    if skip_anchor and ancestors and ancestors[0] == anchor:
        ancestors = ancestors[1:]
    if window is not None:
        ancestors = ancestors[:window]

    chosen: list[dict[str, Any]] = []
    exclusions: list[dict[str, Any]] = []
    scanned = 0
    seen_related: set[frozenset[str]] = set()
    leak_count = 0

    for sha in ancestors:
        scanned += 1
        try:
            info = commit_info(cache_dir, sha)
        except Exception:
            continue
        intent = normalize_intent(info.message)
        if len(info.parents) != 1:
            exclusions.append({"sha": sha, "subject": info.subject, "reason": "merge_commit"})
            continue
        parent = info.parents[0]
        try:
            name_status = diff_name_status(cache_dir, parent, sha)
        except Exception:
            continue
        if not name_status:
            exclusions.append({"sha": sha, "subject": info.subject, "reason": "no_production_source_change"})
            continue

        elig = evaluate_eligibility(
            parents=info.parents,
            intent=intent,
            name_status=name_status,
            proxy_max=proxy_max,
            total_diff_ceiling=total_diff_ceiling,
            allow_intent_path_leakage=True,
        )

        if not elig["eligible"]:
            reason = elig["reason_codes"][0] if elig["reason_codes"] else "no_production_source_change"
            exclusions.append({"sha": sha, "subject": info.subject, "reason": reason})
            continue

        # Whitespace-only production diff check (git diff -w), fail closed.
        if production_diff_is_whitespace_only(cache_dir, parent, sha, elig["proxy_paths"]):
            exclusions.append({"sha": sha, "subject": info.subject, "reason": "whitespace_only"})
            continue

        # Related-commit dedupe: same proxy set as an already-chosen case.
        proxy_set_key = frozenset(elig["proxy_paths"])
        if proxy_set_key in seen_related:
            exclusions.append({"sha": sha, "subject": info.subject, "reason": "duplicate_or_related_change"})
            continue
        seen_related.add(proxy_set_key)

        # MINER_DEV leak cap: at most max_leak_cases cases may mention a changed path.
        if elig["intent_mentions_changed_path"] and leak_count >= max_leak_cases:
            exclusions.append({"sha": sha, "subject": info.subject, "reason": "intent_path_leakage"})
            continue
        if elig["intent_mentions_changed_path"]:
            leak_count += 1

        chosen.append(
            {
                "sha": sha,
                "parent": parent,
                "subject": info.subject,
                "commit_time": info.commit_time_utc,
                "intent": intent,
                "proxy_paths": elig["proxy_paths"],
                "proxy_count": elig["proxy_count"],
                "change_type": elig["change_type"],
                "intent_mentions_changed_path": elig["intent_mentions_changed_path"],
            }
        )
        if len(chosen) >= max_cases:
            break

    # Prefer distinct proxy-size shapes when available (deterministic).
    chosen = _shape_diverse_selection(chosen, max_cases)

    summary = {
        "anchor": anchor,
        "scanned": scanned,
        "eligible_count": len(chosen),
        "leak_case_count": sum(1 for c in chosen if c["intent_mentions_changed_path"]),
        "exclusion_summary": _summarize_exclusions(exclusions),
        "window": window,
    }
    return chosen, summary


def _shape_bucket(proxy_count: int) -> str:
    if proxy_count <= 2:
        return "small"
    if proxy_count <= 6:
        return "medium"
    return "large"


def _shape_diverse_selection(candidates: list[dict[str, Any]], max_cases: int) -> list[dict[str, Any]]:
    """Deterministically prefer distinct proxy-size buckets, then fill in order."""
    by_bucket: dict[str, list[dict[str, Any]]] = {"small": [], "medium": [], "large": []}
    for cand in candidates:
        by_bucket[_shape_bucket(cand["proxy_count"])].append(cand)
    ordered: list[dict[str, Any]] = []
    for bucket in ("small", "medium", "large"):
        for cand in by_bucket[bucket]:
            if len(ordered) < max_cases:
                ordered.append(cand)
    if len(ordered) < max_cases:
        for cand in candidates:
            if len(ordered) >= max_cases:
                break
            if cand not in ordered:
                ordered.append(cand)
    return ordered[:max_cases]


def _summarize_exclusions(exclusions: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in exclusions:
        reason = item["reason"]
        counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items()))


def make_case_id(target: str) -> str:
    return f"djangocms-rc-{target[:12]}"


# ---------------------------------------------------------------------------
# Synthetic temporary git repository pipeline (Gate 3 + integration tests)
# ---------------------------------------------------------------------------


def _git_repo(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {args[0]} failed: {result.stderr.strip()}")
    return result.stdout


def build_synthetic_repo(root: Path) -> dict[str, Any]:
    """Build a tiny temporary git repo exercising the v1 eligibility/exclusion rules.

    Returns a dict with commit SHAs, per-commit name-status maps, and the results
    of running the miner selection over it.
    """
    root.mkdir(parents=True, exist_ok=True)
    _git_repo(root, "init", "-q", "-b", "main")
    _git_repo(root, "config", "user.name", "synthetic")
    _git_repo(root, "config", "user.email", "synthetic@example.com")

    def commit(message: str, files: dict[str, str]) -> str:
        for rel, content in files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            _git_repo(root, "add", "--", rel)
        _git_repo(root, "commit", "-q", "-m", message)
        return _git_repo(root, "rev-parse", "HEAD").strip()

    def write_only(rel: str, content: str) -> None:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    # C0: initial commit with production files.
    c0 = commit(
        "initial commit",
        {
            "cms/models/pagemodel.py": "class PageModel:\n    pass\n",
            "cms/admin/pageadmin.py": "from cms.models.pagemodel import PageModel\n",
            "cms/models/pluginmodel.py": "class PluginModel:\n    pass\n",
            "menus/menu.py": "class Menu:\n    pass\n",
            "cms/tests/test_page.py": "def test_page():\n    assert True\n",
            "cms/migrations/0001_initial.py": "migration = 1\n",
            "setup.py": "setup()\n",
            "README.rst": "readme\n",
        },
    )

    # C1: eligible normal existing-file production modification.
    c1 = commit(
        "fix: add page publish validation",
        {
            "cms/models/pagemodel.py": "class PageModel:\n    def publish(self):\n        return True\n",
        },
    )

    # C2: tests-only commit.
    c2 = commit(
        "test: cover page publish",
        {
            "cms/tests/test_page.py": "def test_page():\n    assert True\n\ndef test_publish():\n    assert True\n",
        },
    )

    # C3: migration-only commit.
    c3 = commit(
        "chore: add migration",
        {
            "cms/migrations/0002_auto.py": "migration = 2\n",
        },
    )

    # C4: whitespace-only commit (production diff collapses under -w).
    c4 = commit(
        "style: whitespace only",
        {
            "menus/menu.py": "class Menu:\n     pass\n",
        },
    )

    # C5: production file addition (add is unsupported in v1).
    c5 = commit(
        "feat: add new utility module",
        {
            "cms/utils/newutil.py": "def util():\n    return 1\n",
        },
    )

    # C6: production rename (unsupported in v1).
    _git_repo(root, "mv", "cms/utils/newutil.py", "cms/utils/renamed.py")
    _git_repo(root, "commit", "-q", "-m", "refactor: rename utility module")
    c6 = _git_repo(root, "rev-parse", "HEAD").strip()

    # C7: intent contains changed path (leakage detector fires; still a valid
    # MINER_DEV case, flagged, never HELD_OUT_TEST).
    write_only(
        "cms/models/pagemodel.py",
        "class PageModel:\n    def publish(self):\n        return True\n\n    def title(self):\n        return ''\n",
    )
    _git_repo(root, "add", "--", "cms/models/pagemodel.py")
    _git_repo(root, "commit", "-q", "-m", "fix: update cms/models/pagemodel.py to add title")
    c7 = _git_repo(root, "rev-parse", "HEAD").strip()

    # C8: another eligible normal modification (distinct shape).
    c8 = commit(
        "fix: menu ordering",
        {
            "menus/menu.py": "class Menu:\n    def order(self):\n        return [1, 2]\n",
            "cms/models/pluginmodel.py": "class PluginModel:\n    def refresh(self):\n        return 0\n",
        },
    )

    # Merge commit (C9) from a side branch.
    side = _git_repo(root, "rev-parse", "HEAD").strip()
    _git_repo(root, "checkout", "-q", "-b", "side-branch", side)
    commit(
        "feat: side change",
        {
            "cms/models/sidemodel.py": "class SideModel:\n    pass\n",
        },
    )
    _git_repo(root, "checkout", "-q", "main")
    _git_repo(root, "merge", "-q", "--no-ff", "-m", "merge: side branch", "side-branch")
    c9 = _git_repo(root, "rev-parse", "HEAD").strip()

    anchor = c9
    chosen, summary = select_miner_dev_cases(
        root,
        anchor,
        max_cases=6,
        window=100,
        skip_anchor=True,
    )
    return {
        "anchor": anchor,
        "commits": {
            "c0": c0,
            "c1": c1,
            "c2": c2,
            "c3": c3,
            "c4": c4,
            "c5": c5,
            "c6": c6,
            "c7": c7,
            "c8": c8,
            "c9": c9,
        },
        "chosen": chosen,
        "summary": summary,
    }
