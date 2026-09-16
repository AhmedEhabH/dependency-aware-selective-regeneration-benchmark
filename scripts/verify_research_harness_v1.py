#!/usr/bin/env python3
"""Research Harness V1 — six T3 validation gates + audit summary.

Usage:
    python scripts/verify_research_harness_v1.py [--report-dir reports]

ZERO API. Writes reports/research_harness_v1_gates.json.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PACKAGE_ROOT))
sys.path.insert(0, str(_PACKAGE_ROOT / "src"))

from benchmark.harness import gates  # noqa: E402

DATASET_DIR = _PACKAGE_ROOT / "benchmark_data" / "real_commit_impact_v1"
DEFAULT_REPORT_DIR = _PACKAGE_ROOT / "reports"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DATASET_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    args = parser.parse_args()

    report_dir = args.report_dir.resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    gate_results = gates.run_six_gates(args.dataset_dir.resolve())
    passed = gates.all_gates_pass(gate_results)

    payload = {
        "protocol": "research-harness-v1",
        "all_gates_passed": passed,
        "gates": gate_results,
    }
    out = report_dir / "research_harness_v1_gates.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for g in gate_results:
        print(f"GATE {g['gate']} {g['name']}: {'PASS' if g['passed'] else 'FAIL'} ({len(g['checks'])} checks)")
    print(f"ALL_GATES_PASS={passed}")
    print(f"GATE_JSON={out}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
