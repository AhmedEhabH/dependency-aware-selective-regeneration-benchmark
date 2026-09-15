"""Build a zero-held-out smoke dataset for LocAgent P5 from MINER_DEV cases."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from benchmark.locagent.adapter import LocAgentAdapter  # noqa: E402

DATASET_DIR = Path(__file__).resolve().parent.parent.parent / "benchmark_data" / "real_commit_impact_v1"
CASE_ID = "djangocms-rc-110d4c740927"
OUT = Path(__file__).resolve().parent / "dataset" / "smoke.json"

adapter = LocAgentAdapter(DATASET_DIR)
inst = adapter.build_input(CASE_ID)
adapter.assert_no_leakage(inst)
row = {
    "instance_id": inst.instance_id,
    "repo": "djangocms/djangocms",
    "base_commit": inst.base_commit,
    "problem_statement": inst.problem_statement,
    "patch": inst.patch,
    "source_case_id": inst.source_case_id,
}
OUT.write_text(json.dumps([row], indent=2), encoding="utf-8")
print("wrote", OUT, "split=", inst.split, "leak_errors=", adapter.leakage_errors(inst))