"""Six T3 validation gates for the research harness (ZERO API).

Runs the canonical gate module (``benchmark.harness.gates``) inside pytest and
asserts every gate passes.
"""

from __future__ import annotations

from pathlib import Path

from benchmark.harness import gates

DATASET_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "benchmark_data"
    / "real_commit_impact_v1"
)


def test_all_six_gates_pass() -> None:
    results = gates.run_six_gates(DATASET_DIR)
    assert len(results) == 6
    for gate in results:
        assert gate["passed"], (
            f"gate {gate['gate']} ({gate['name']}) failed: "
            + "; ".join(c["check"] for c in gate["checks"] if not c["ok"])
        )


def test_gate_names_match_protocol() -> None:
    names = [g["name"] for g in gates.run_six_gates(DATASET_DIR)]
    assert names == [
        "Dataset Validation",
        "Input/Query Validation",
        "Pipeline Smoke Test",
        "Dry Run",
        "Integration Test",
        "Metric Verification",
    ]
