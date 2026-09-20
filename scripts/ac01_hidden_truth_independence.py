"""AC-0.1 mechanical proof: a complete non-fixture regeneration/execution
path constructs ArtifactUniverse even when hidden/ground-truth outcome
artifacts are unavailable/unreadable.

This runs the runner's production `_build_artifact_universe` for a
non-fixture execution against the parent-commit repository state, while the
scenario's ground-truth (`expected_affected_artifacts`) points at a hidden
path that is made unavailable. The repository-derived universe must still be
constructed and must NOT contain the ground-truth-only path.

Uses an ALREADY-EXPOSED real task (djangoCMS scientific case) parent commit
materialized from the local full git cache. No Saleor RESERVE outcome is
touched. Scientific API spend: $0.00.
"""

from __future__ import annotations

import io
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path

from benchmark.core.enums import ArtifactType, BlastRadius
from benchmark.core.models import ArtifactRef, Scenario
from benchmark.execution.isolation import IsolationContext
from benchmark.execution.runner import BenchmarkRunner, RunnerConfig
from benchmark.repositories.workspace import WorkspacePath

# An already-exposed djangoCMS scientific case (TRAIN split, already opened).
CASE_ID = "djangocms-rc-06ecf3a8e8de"
PARENT_COMMIT = "369f77689346b9689a4c9fba14a96d9bd85ac1f2"
REPO_CACHE = Path("dist") / "real-commit-cache" / "djangocms"
CASE_DIR = (
    Path("benchmark_data")
    / "real_commit_impact_v1"
    / "scientific"
    / CASE_ID
)

# The public real-commit candidate universe (already-exposed metadata) gives
# the concrete eligible artifact file paths derived from the parent state.
PUBLIC_UNIVERSE = CASE_DIR / "public" / "candidate_universe.json"


def load_public_universe_paths() -> tuple[str, ...]:
    data = json.loads(PUBLIC_UNIVERSE.read_text(encoding="utf-8"))
    records = data.get("records", [])
    return tuple(sorted(str(r["path"]) for r in records))


def materialize_parent_tree(parent: str, dest: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(REPO_CACHE), "archive", "--format=tar", parent],
        check=True,
        capture_output=True,
    )
    with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r|") as tf:
        tf.extractall(dest, filter="data")
    return dest


def main() -> int:
    if not REPO_CACHE.is_dir():
        print("FAIL: repo cache missing", REPO_CACHE)
        return 1
    if not PUBLIC_UNIVERSE.is_file():
        print("FAIL: public candidate universe missing", PUBLIC_UNIVERSE)
        return 1
    editable = load_public_universe_paths()
    print("public_candidate_universe_count:", len(editable))

    with tempfile.TemporaryDirectory(prefix="ac01-") as tmp:
        tmp = Path(tmp)
        ws_root = tmp / "workspace"
        ws_root.mkdir()
        snap_base = tmp / "snapshots"
        snap_base.mkdir()
        parent_root = snap_base / "repo" / "v1"
        parent_root.mkdir(parents=True)
        materialize_parent_tree(PARENT_COMMIT, parent_root)

        ws = WorkspacePath(root=str(ws_root))
        iso = IsolationContext(
            workspace=ws,
            snapshot_base=snap_base,
            active_snapshot_root=parent_root,
        )

        # Hidden ground-truth outcome artifact, made unavailable/unreadable.
        hidden_dir = parent_root / "hidden"
        hidden_dir.mkdir(parents=True, exist_ok=True)
        hidden_proxy = hidden_dir / "observed_change_set_proxy.json"
        hidden_proxy.write_text('{"paths": ["hidden/observed_change_set_proxy.py"]}\n', encoding="utf-8")
        # Remove read permission to prove production never needs it.
        import os

        os.chmod(hidden_proxy, 0)
        hidden_path = "hidden/observed_change_set_proxy.py"
        hidden_abs = parent_root / hidden_path
        hidden_abs.parent.mkdir(parents=True, exist_ok=True)
        hidden_abs.write_text("# hidden ground truth sentinel\n", encoding="utf-8")

        scenario = Scenario(
            scenario_id=CASE_ID,
            repository="djangocms",
            change_type="modify",
            blast_radius=BlastRadius.localized,
            requirement_before="before",
            requirement_after="after",
            rationale="AC-0.1 hidden-truth independence",
            expected_affected_artifacts=(
                ArtifactRef(path=hidden_path, artifact_type=ArtifactType.source),
            ),
        )

        config = RunnerConfig(
            strategy_name="selective",
            backend_name="mock",
            protocol_version="1.0",
            max_attempts=1,
            enable_regeneration=False,
            selection_only=True,
            editable_artifact_paths=editable,
        )
        runner = BenchmarkRunner(
            strategy=_RecordingStrategy(),
            backend=_NoopBackend(),
            isolation=iso,
            config=config,
        )
        record = runner.run(scenario)

        print("== AC-0.1 transcript ==")
        print("case_id:", CASE_ID)
        print("parent_commit:", PARENT_COMMIT)
        print("hidden_proxy_made_unreadable:", hidden_proxy)
        print("record.status:", record.status)
        for f in record.failures:
            print("failure:", f.failure_kind, "|", f.message[:200])
        print("allow_ground_truth_universe:", record.allow_ground_truth_universe)
        calls = _calls_of(runner)
        print("analyze_impact_calls:", len(calls))
        if not calls:
            print("FAIL: strategy was not invoked; universe not constructed")
            return 1
        _repo, _change, universe = calls[0]
        paths = {a.path for a in universe.artifacts}
        print("universe_size:", len(paths))
        print("hidden_in_universe:", hidden_path in paths)
        print("sample_repo_path_in_universe:", "cms/api.py" in paths)
        ok = True
        if record.status.name != "succeeded":
            print("FAIL: run did not succeed")
            ok = False
        if hidden_path in paths:
            print("FAIL: hidden ground-truth path leaked into universe")
            ok = False
        if "cms/api.py" not in paths:
            print("FAIL: repository-derived path missing from universe")
            ok = False
        if record.allow_ground_truth_universe is not False:
            print("FAIL: non-fixture run wrongly audited ground-truth flag True")
            ok = False

        print("AC-0.1 RESULT:", "PASS" if ok else "FAIL")
        return 0 if ok else 1


class _RecordingStrategy:
    def __init__(self) -> None:
        self.calls = []

    def analyze_impact(self, repository, requirement_change, artifact_universe):
        self.calls.append((repository, requirement_change, artifact_universe))
        from benchmark.core.models import ImpactPrediction

        return ImpactPrediction()


class _NoopBackend:
    async def generate(self, prompt="", temperature=0.0, max_tokens=4096):  # noqa: ARG002
        from benchmark.core.models import LLMResponse, TokenUsage

        return LLMResponse(text="mock", token_usage=TokenUsage(), finish_reason="stop")


def _calls_of(runner):
    return list(runner._strategy.calls)


if __name__ == "__main__":
    raise SystemExit(main())
