"""PILOT-EXEC-01 D9.6: repo-wide Kaggle/GitHub boundary audit + current-truth
documentation/release regression.

The permanent contract (AGENTS.md): GitHub is durable source/release storage
(visibility is owner-controlled and out of scope); annotated tags mark proven
stable candidates and are created/pushed/peeled LOCALLY after a real preflight;
Kaggle runs the frozen artifact and NEVER contacts GitHub for launch/resume; no
GitHub token/credential is required in Kaggle.

These tests fail closed against regressions that re-introduce a runtime
GitHub/git/network launch gate OR a documentation claim that the repository
must be public or that a GitHub secret is required in Kaggle.
"""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent

RUNTIME_CODE_GLOBS = ("src/**/*.py", "scripts/*.py")
RUNTIME_FILES = (
    [*PROJECT_DIR.glob("src/**/*.py"), *PROJECT_DIR.glob("scripts/*.py")]
    + [PROJECT_DIR / "seven_arm_benchmark.py", PROJECT_DIR / "notebooks" / "pilot_exec_01.ipynb"]
)

# D9.5 machinery and any GitHub secret/credential must not exist anywhere in
# the current runtime launch/resume path.
FORBIDDEN_RUNTIME_FRAGMENTS = (
    "verify_remote_annotated_tag_peel",
    "KAGGLE_PUBLIC_CANONICAL_REMOTE",
    "REMOTE_TAG_PROOF_TIMEOUT_SECONDS",
    "PILOT_STABLE_TAG",
    "ls-remote",
    "GITHUB_TOKEN",
    "ghp_",
)

# The only legitimate github.com references in runtime code are the pinned
# THIRD-PARTY benchmark-target / reference repositories (scientific repository
# pins, NOT the benchmark's own repo, NOT launch auth). The set of allowed
# github.com URLs below is enforced repo-wide: any github.com URL found in
# runtime code MUST be one of these pinned third-party repositories.
PILOT_REPO_SNAPSHOT_URLS = (
    "https://github.com/ahmed-ehab/controlled-django-todo",
    "https://github.com/django-cms/django-cms",
    "https://github.com/saleor/saleor",
)

# Immutable pinned third-party REFERENCE/upstream repositories (comparison
# systems or benchmark-target repos) that runtime code may name for
# provenance. LocAgent is the P5 shared-protocol comparison upstream; djangoCMS
# is the real-commit benchmark-target repository. Neither is the benchmark's
# own remote and neither is contacted for launch/resume.
ALLOWED_THIRD_PARTY_RUNTIME_URLS = PILOT_REPO_SNAPSHOT_URLS + (
    "https://github.com/gersteinlab/LocAgent",
)

# Active current-truth documentation on which the release/Timing regression is
# enforced. Historical reports keep their records untouched.
ACTIVE_DOCS = (
    PROJECT_DIR / "README.md",
    PROJECT_DIR / "AGENTS.md",
    PROJECT_DIR / "SYSTEM_STATE.md",
    PROJECT_DIR / "TODO.md",
    PROJECT_DIR / "docs" / "PILOT_KAGGLE_RUNBOOK.md",
    PROJECT_DIR / "docs" / "START_HERE.md",
)

FORBIDDEN_DOC_FRAGMENTS = (
    "GITHUB_TOKEN",
    "must be public",
    "make the repository public",
    "public mirror",
    "public canonical remote",
    "REMOTE TAG-PEEL PRE-LAUNCH GATE",
    "verify_remote_annotated_tag_peel",
    "REMOTE TAG PEEL PROOF",
    "RESUME REMOTE TAG PEEL PROOF",
)

REQUIRED_DOC_MARKERS = (
    "never contact GitHub",
    "owner-controlled",
    "locally verified against",
    "after real preflight",
    "v0.9.22-d12-candidate",
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")


def test_runtime_launch_resume_path_has_no_github_machinery() -> None:
    for path in RUNTIME_FILES:
        text = _text(path)
        for fragment in FORBIDDEN_RUNTIME_FRAGMENTS:
            assert fragment not in text, (
                f"{path.relative_to(PROJECT_DIR)} must not contain {fragment!r}"
            )
        for url in re.findall(r"https://github\.com/[A-Za-z0-9_.\-/]+", text):
            assert url in ALLOWED_THIRD_PARTY_RUNTIME_URLS, (
                f"{path.relative_to(PROJECT_DIR)} references non-pinned github.com "
                f"URL {url!r} (only pinned third-party benchmark/reference repos "
                "may appear in runtime code)"
            )
        # The benchmark's own remote must never be embedded.
        assert "dependency-aware-selective-regeneration-benchmark.git" not in text, (
            f"{path.relative_to(PROJECT_DIR)} must not embed the benchmark remote"
        )


def test_pilot_repo_snapshot_only_pins_the_three_target_repos() -> None:
    snapshot = PROJECT_DIR / "scripts" / "pilot_repo_snapshot.py"
    text = _text(snapshot)
    found = [m.group(0) for m in re.finditer(r"https://github\.com/[^\"]+", text)]
    for pinned in PILOT_REPO_SNAPSHOT_URLS:
        assert pinned in found, f"pinned data-repo URL missing: {pinned}"
    assert all(url in PILOT_REPO_SNAPSHOT_URLS for url in found), (
        "pilot_repo_snapshot.py must only reference the three pinned target repos"
    )


def test_runtime_code_never_references_the_benchmark_own_remote() -> None:
    for path in RUNTIME_FILES:
        text = _text(path)
        assert "dependency-aware-selective-regeneration-benchmark.git" not in text, (
            f"{path.relative_to(PROJECT_DIR)} must not embed the benchmark remote"
        )


def test_bundled_runtime_cli_has_no_launch_auth_git_dependency() -> None:
    """The exact frozen artifact entry is the bundled CLI; its launch path must
    have no git/network gate beyond the already-required HF token."""
    entry = PROJECT_DIR / "seven_arm_benchmark.py"
    text = _text(entry)
    assert "launch_authorization" in text
    for fragment in FORBIDDEN_RUNTIME_FRAGMENTS:
        assert fragment not in text, f"seven_arm_benchmark.py: {fragment!r}"
    assert "git ls-remote" not in text


def test_current_truth_docs_contract_markers() -> None:
    corpus = "\n".join(_text(p) for p in ACTIVE_DOCS)
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in corpus, f"current-truth docs must contain {marker!r}"


def test_current_truth_docs_have_no_forbidden_contract_fragments() -> None:
    for path in ACTIVE_DOCS:
        text = _text(path)
        for fragment in FORBIDDEN_DOC_FRAGMENTS:
            assert fragment not in text, (
                f"{path.relative_to(PROJECT_DIR)} must not contain {fragment!r}"
            )
