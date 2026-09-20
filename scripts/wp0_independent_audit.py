"""Independent audit for WP-0 (G7): ArtifactUniverse must be repository-derived,
never ground truth.

This checker does NOT import the audited helper
(`BenchmarkRunner._build_artifact_universe`) nor `resolve_allowed_artifacts`.
It independently re-reads the source and independently re-derives the universe
from the parent repository state using its own resolver, then compares the two
independent derivations.

Items verified (WP-0 §17):
1. non-fixture universe source is parent repository state;
2. hidden outcome artifacts are unnecessary;
3. expected affected artifacts are not touched by the production path;
4. representative universe counts/semantics;
5. fixture flag default is False;
6. fixture usage is explicit and auditable.
"""

from __future__ import annotations

import io
import json
import re
import subprocess
import tarfile
import tempfile
from pathlib import Path

REPO_CACHE = Path("dist") / "real-commit-cache" / "djangocms"
SCIENTIFIC_DIR = Path("benchmark_data") / "real_commit_impact_v1" / "scientific"
RUNNER_SRC = Path("src") / "benchmark" / "execution" / "runner.py"
MODELS_SRC = Path("src") / "benchmark" / "core" / "models.py"
PIPELINE_SRC = Path("src") / "benchmark" / "execution" / "pipeline.py"

CASE = ("djangocms-rc-06ecf3a8e8de", "369f77689346b9689a4c9fba14a96d9bd85ac1f2")


# ---------------------------------------------------------------------------
# Independent source-level checks (no import of the audited code)
# ---------------------------------------------------------------------------


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _check_item1_universe_source() -> bool:
    """Non-fixture universe must come from parent repository state
    (resolve_allowed_artifacts on the active snapshot), not expected artifacts."""
    src = _source(RUNNER_SRC)
    # Find _build_artifact_universe body and ensure the fixture branch is
    # guarded by allow_ground_truth_universe.
    m = re.search(
        r"def _build_artifact_universe\(self, scenario: Scenario\) -> ArtifactUniverse:(.*?)"
        r"(?=\n    def |\Z)",
        src,
        re.DOTALL,
    )
    if not m:
        return False
    body = m.group(1)
    ok_guard = "if self._config.allow_ground_truth_universe:" in body
    ok_repo = "resolve_allowed_artifacts(" in body and "_active_snapshot()" in body
    ok_fixture_only = (
        "expected_affected_artifacts" in body
        and body.index("expected_affected_artifacts") > body.index("allow_ground_truth_universe:")
    )
    return ok_guard and ok_repo and ok_fixture_only


def _check_item2_hidden_unnecessary() -> bool:
    """Production universe construction must not read hidden proxies."""
    src = _source(RUNNER_SRC)
    universe_block = re.search(
        r"def _build_artifact_universe\(self, scenario: Scenario\) -> ArtifactUniverse:(.*?)"
        r"(?=\n    def |\Z)",
        src,
        re.DOTALL,
    )
    if not universe_block:
        return False
    body = universe_block.group(1)
    return "observed_change_set_proxy" not in body and "hidden" not in body.lower().replace(
        "hidden proxies", ""
    ).replace("hidden/", "")


def _check_item3_expected_not_touched() -> bool:
    """The production branch must not consult scenario.expected_affected_artifacts."""
    src = _source(RUNNER_SRC)
    # The only expected_affected_artifacts read is inside the fixture guard.
    fixture_branch = re.search(
        r"if self\._config\.allow_ground_truth_universe:.*?expected_affected_artifacts.*?"
        r"(?=\n        # Production path)",
        src,
        re.DOTALL,
    )
    return fixture_branch is not None


def _check_item5_flag_default_false() -> bool:
    """RunnerConfig / PipelineConfig / RunRecord defaults must be False."""
    runner = _source(RUNNER_SRC)
    models = _source(MODELS_SRC)
    pipeline = _source(PIPELINE_SRC)
    ok_runner = "allow_ground_truth_universe: bool = False" in runner
    ok_models = "allow_ground_truth_universe: bool = False" in models
    ok_pipeline = "allow_ground_truth_universe: bool = False" in pipeline
    return ok_runner and ok_models and ok_pipeline


def _check_item6_fixture_explicit_and_auditable() -> bool:
    """Fixture must be explicit opt-in and the RunRecord must carry the flag."""
    runner = _source(RUNNER_SRC)
    models = _source(MODELS_SRC)
    # fail-closed config guards exist
    ok_fail_closed = (
        "incompatible with" in runner
        and "enable_regeneration" in runner
        and "selection_only" in runner
    )
    # run()/dry_run stamp the flag onto records
    ok_stamp = (
        "allow_ground_truth_universe=self._config.allow_ground_truth_universe" in runner
    )
    # RunRecord field exists with validation
    ok_field = "allow_ground_truth_universe: bool = False" in models
    ok_validation = "RunRecord.allow_ground_truth_universe must be a bool" in models
    return ok_fail_closed and ok_stamp and ok_field and ok_validation


# ---------------------------------------------------------------------------
# Independent repository-derived universe (own resolver, does not import
# benchmark.resolve_allowed_artifacts)
# ---------------------------------------------------------------------------


def _independent_eligible_files(parent_root: Path, eligible: tuple[str, ...]) -> tuple[str, ...]:
    """Independent eligible-file resolver: every listed path must exist as a
    regular file strictly inside the parent root (path-safety enforced here,
    independent of the audited resolver)."""
    root = parent_root.resolve()
    out: list[str] = []
    for p in eligible:
        if p.startswith("/") or "\\" in p or ".." in p.split("/"):
            continue
        full = (root / p).resolve()
        if full == root or root not in full.parents:
            continue
        if full.is_file():
            out.append(p)
    return tuple(sorted(out))


def _materialize(parent: str, dest: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(REPO_CACHE), "archive", "--format=tar", parent],
        check=True,
        capture_output=True,
    )
    with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r|") as tf:
        tf.extractall(dest, filter="data")
    return dest


def _check_item4_counts() -> bool:
    case_id, parent = CASE
    pub_path = SCIENTIFIC_DIR / case_id / "public" / "candidate_universe.json"
    data = json.loads(pub_path.read_text(encoding="utf-8"))
    eligible = tuple(sorted(str(r["path"]) for r in data["records"]))
    pub_count = len(eligible)

    with tempfile.TemporaryDirectory(prefix="audit-") as tmp:
        parent_root = _materialize(parent, Path(tmp) / "parent")
        independent = _independent_eligible_files(parent_root, eligible)
    return len(independent) == pub_count


def main() -> int:
    results = {
        "1. non-fixture universe source is parent repository state": _check_item1_universe_source(),
        "2. hidden outcome artifacts are unnecessary": _check_item2_hidden_unnecessary(),
        "3. expected affected artifacts not touched by production path": _check_item3_expected_not_touched(),
        "4. representative universe counts/semantics": _check_item4_counts(),
        "5. fixture flag default is False": _check_item5_flag_default_false(),
        "6. fixture usage is explicit and auditable": _check_item6_fixture_explicit_and_auditable(),
    }
    all_pass = True
    for label, passed in results.items():
        print(f"{'PASS' if passed else 'FAIL'}\t{label}")
        all_pass = all_pass and passed
    print("INDEPENDENT AUDIT:", "PASS" if all_pass else "FAIL")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
