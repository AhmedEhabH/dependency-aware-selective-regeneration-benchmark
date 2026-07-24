"""Test that run IDs are deterministic across processes and sessions."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from benchmark.checkpoint.persistence import make_run_id


CODE = r"""
import hashlib, json, sys
sys.path.insert(0, r"{src}")
from benchmark.checkpoint.persistence import make_run_id
rid = make_run_id(
    scenario_id="djangocms-cross-007",
    strategy_name="monolithic",
    repetition=1,
    protocol_version="1.0",
    config_hash="abc1234",
)
print(rid)
"""


class TestDeterministicRunId:
    def test_same_params_same_id(self) -> None:
        id1 = make_run_id("scenario-A", "agent", 1, "1.0", "hash1")
        id2 = make_run_id("scenario-A", "agent", 1, "1.0", "hash1")
        assert id1 == id2

    def test_different_scenario_different_id(self) -> None:
        id1 = make_run_id("scenario-A", "agent", 1, "1.0", "hash1")
        id2 = make_run_id("scenario-B", "agent", 1, "1.0", "hash1")
        assert id1 != id2

    def test_different_strategy_different_id(self) -> None:
        id1 = make_run_id("scenario-A", "agent", 1, "1.0", "hash1")
        id2 = make_run_id("scenario-A", "selective", 1, "1.0", "hash1")
        assert id1 != id2

    def test_different_repetition_different_id(self) -> None:
        id1 = make_run_id("scenario-A", "agent", 1, "1.0", "hash1")
        id2 = make_run_id("scenario-A", "agent", 2, "1.0", "hash1")
        assert id1 != id2

    def test_different_config_hash_different_id(self) -> None:
        id1 = make_run_id("scenario-A", "agent", 1, "1.0", "hash1")
        id2 = make_run_id("scenario-A", "agent", 1, "1.0", "hash2")
        assert id1 != id2

    def test_no_uuid_in_suffix(self) -> None:
        rid = make_run_id("s", "s", 1, "1.0", "h")
        suffix = rid.split("_")[-1]
        assert len(suffix) == 8, f"Suffix should be 8 hex chars, got '{suffix}'"
        int(suffix, 16)  # must be valid hex

    def test_two_subprocesses_generate_identical_ids(self, tmp_path: Path) -> None:
        src_path = Path(__file__).resolve().parent.parent.parent / "src"
        script = CODE.format(src=src_path)
        script_file = tmp_path / "gen_run_id.py"
        script_file.write_text(script)

        results = []
        for _ in range(2):
            result = subprocess.run(
                [sys.executable, str(script_file)],
                capture_output=True, text=True, timeout=30,
            )
            assert result.returncode == 0, f"Subprocess failed: {result.stderr}"
            results.append(result.stdout.strip())

        assert results[0] == results[1], (
            f"Run IDs differ across subprocesses:\n  {results[0]}\n  {results[1]}"
        )
