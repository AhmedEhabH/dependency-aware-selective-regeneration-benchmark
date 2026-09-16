#!/usr/bin/env python3
"""Protocol-A output-equivalence runner (compat layer).

Runs the Protocol-A cheap non-LLM baselines THROUGH the pluggable harness
(git parent-commit corpus, full TRAIN+VALIDATION) and compares the scientific
projection against the frozen persisted evidence
``research/cheap-baselines-v1/raw_predictions_v1.json``.

Byte-for-byte scientific equivalence is asserted for every case/baseline/K:
ranked + selected paths, seed reason, corpus source, and TP/FP/FN/P/R/F1/FNR.
Wall-clock timing fields are excluded (non-deterministic by nature).

Usage:
    python scripts/run_harness_protocol_a_equivalence.py [--case-slice lo hi]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PACKAGE_ROOT))
sys.path.insert(0, str(_PACKAGE_ROOT / "src"))

from benchmark.harness import protocol_a  # noqa: E402

DATASET_DIR = _PACKAGE_ROOT / "benchmark_data" / "real_commit_impact_v1"
CACHE_DIR = _PACKAGE_ROOT / "dist" / "real-commit-cache" / "djangocms"
FROZEN_RAW = _PACKAGE_ROOT / "research" / "cheap-baselines-v1" / "raw_predictions_v1.json"
OUT_DIR = _PACKAGE_ROOT / "research" / "harness-protocol-a-equivalence"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DATASET_DIR)
    parser.add_argument("--cache-dir", type=Path, default=CACHE_DIR)
    parser.add_argument("--frozen-raw", type=Path, default=FROZEN_RAW)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--case-slice", nargs=2, type=int, default=None)
    args = parser.parse_args()

    dataset_dir = args.dataset_dir.resolve()
    cache_dir = args.cache_dir.resolve()
    frozen_raw = args.frozen_raw.resolve()
    out_dir = args.out_dir.resolve()

    if not cache_dir.is_dir():
        print(f"ERROR: git cache dir not found: {cache_dir}")
        return 2
    if not frozen_raw.is_file():
        print(f"ERROR: frozen evidence not found: {frozen_raw}")
        return 2

    slice_ = tuple(args.case_slice) if args.case_slice else None
    payload = protocol_a.run_protocol_a_via_harness(
        dataset_dir=dataset_dir,
        cache_dir=cache_dir,
        case_slice=slice_,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "raw_predictions_via_harness_v1.json"
    out.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    errors = protocol_a.compare_to_frozen(payload, frozen_raw)
    agg_errors = _compare_aggregates(
        payload["aggregate"], _PACKAGE_ROOT / "research" / "cheap-baselines-v1" / "aggregate_v1.json"
    )
    print(f"corpus_mode={payload['corpus_mode']}")
    print(f"cases={len(payload['cases'])} rows={payload['scientific_row_count']}")
    print(f"output={out}")
    if errors or agg_errors:
        all_errors = errors + agg_errors
        print(f"EQUIVALENCE=FAIL ({len(all_errors)} mismatches)")
        for e in all_errors[:40]:
            print("  " + e)
        return 1
    print("EQUIVALENCE=PASS (scientific projection + aggregates byte-identical to frozen evidence)")
    return 0


def _compare_aggregates(harness_agg: dict, frozen_agg_path: Path) -> list[str]:
    """Compare harness aggregate tables to the frozen aggregate_v1.json."""
    if not frozen_agg_path.is_file():
        return [f"frozen aggregate not found: {frozen_agg_path}"]
    frozen = json.loads(frozen_agg_path.read_text(encoding="utf-8"))["aggregates"]
    errors: list[str] = []
    for group in ("TRAIN", "VALIDATION", "TRAIN_VALIDATION"):
        for baseline in ("random", "bm25", "path_token", "graph", "hybrid"):
            for k in (1, 3, 5, 10):
                fcell = frozen[group][baseline][str(k)]
                hcell = harness_agg[group][baseline][str(k)]
                if fcell != hcell:
                    errors.append(
                        f"aggregate {group}/{baseline}/k={k}: frozen={fcell} harness={hcell}"
                    )
    return errors


if __name__ == "__main__":
    raise SystemExit(main())
