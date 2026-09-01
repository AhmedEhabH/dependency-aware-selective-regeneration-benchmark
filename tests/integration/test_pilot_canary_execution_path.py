"""D11 B1/B4: executable six-cell pilot-canary topology.

B4 requires more than a unit assertion that the canary profile "looks right":
the D10 canary profile passed its unit test while the real CLI could not even
start it (``djangocms-cross-007`` is ``cross_cutting`` but the profile blast
radius filter was ``["localized"]``, so the scenario was dropped and the CLI
exited before a single model call).

This integration test invokes the ACTUAL benchmark CLI in no-model/dry-run mode
against the canonical scenario data and proves the SALEOR-INCLUSIVE six-cell
canary topology (todo/djangocms/saleor 2/2/2, both strategies, one repetition,
protocol 1.1, zero model calls).
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
SCRIPT = PROJECT_DIR / "seven_arm_benchmark.py"
BENCHMARK_DATA = PROJECT_DIR / "benchmark_data"

CANARY_REPOSITORIES = ("todo", "djangocms", "saleor")
CANARY_SCENARIO_IDS = ("todo-loc-001", "djangocms-cross-007", "saleor-loc-001")


def _run_canary_dry_run(output_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--dry-run",
            "--profile", "pilot-canary",
            "--data-dir", str(BENCHMARK_DATA),
            "--output-dir", str(output_dir),
            "--source-commit", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        ],
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )


def _load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class TestPilotCanaryExecutionPath:
    """D11 B4: the canary must be cli-executable in dry-run mode."""

    def test_canary_dry_run_produces_six_cells(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "canary-runs"
        result = _run_canary_dry_run(output_dir)
        assert result.returncode == 0, (
            f"pilot-canary dry-run must be executable; STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        records_path = output_dir / "run_records.jsonl"
        records = _load_jsonl(records_path)
        assert len(records) == 6, f"expected 6 canary records, got {len(records)}"

        run_ids = [r.get("run_id") for r in records]
        assert len(run_ids) == len(set(run_ids)), "duplicate canary run IDs"

        repo_counts = Counter(str(r.get("repository_id", "")) for r in records)
        assert repo_counts == {"todo": 2, "djangocms": 2, "saleor": 2}, repo_counts

        strategy_counts = Counter(str(r.get("strategy_id", "")) for r in records)
        assert strategy_counts == {
            "iterative_repository_agent": 3,
            "selective": 3,
        }, strategy_counts

        rep_counts = Counter(int(r.get("repetition", -1)) for r in records)
        assert rep_counts == {1: 6}, rep_counts

        for record in records:
            assert record.get("status") == "succeeded", record

    def test_canary_dry_run_has_no_model_calls_and_protocol_11(self, tmp_path: Path) -> None:
        output_dir = tmp_path / "canary-identity"
        result = _run_canary_dry_run(output_dir)
        assert result.returncode == 0, result.stdout + result.stderr

        records = _load_jsonl(output_dir / "run_records.jsonl")
        for record in records:
            assert record.get("total_workflow_model_calls") == 0, record
            assert record.get("total_workflow_tokens") == 0, record

        identity_path = output_dir / "source_identity.json"
        assert identity_path.is_file()
        identity = json.loads(identity_path.read_text(encoding="utf-8"))
        assert identity.get("profile") == "pilot-canary"
        assert identity.get("protocol_version") == "1.1"
        assert identity.get("model_identity") == "dry-run:mock"
        assert identity.get("dry_run") is True

    def test_canary_scenario_ids_all_resolve_and_are_covered(self) -> None:
        from seven_arm_benchmark import ScenarioProvider

        provider = ScenarioProvider(BENCHMARK_DATA / "scenarios")
        scenarios = provider.list_scenarios()
        by_id = {s.scenario_id: s for s in scenarios}
        for scenario_id in CANARY_SCENARIO_IDS:
            assert scenario_id in by_id, f"missing canary scenario {scenario_id}"
        radii = {by_id[sid].blast_radius for sid in CANARY_SCENARIO_IDS}
        assert radii == {"localized", "cross_cutting"}, radii
        repos = {by_id[sid].repository for sid in CANARY_SCENARIO_IDS}
        assert repos == set(CANARY_REPOSITORIES), repos

    def test_resolved_profile_matches_canary_contract(self) -> None:
        from seven_arm_benchmark import PROFILES

        canary = PROFILES["pilot-canary"]
        assert canary.repository_names == ["todo", "djangocms", "saleor"]
        assert canary.scenario_ids == list(CANARY_SCENARIO_IDS)
        assert canary.scenario_count == 3
        assert canary.repetitions == 1
        assert canary.strategies == ["iterative_repository_agent", "selective"]
        assert canary.timeout_seconds == 1200
