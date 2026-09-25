#!/usr/bin/env python3
"""WP-2 real resource sampler CLI (Mission-09) - ZERO API.

Runs the 5 s-interval resource sampler as a SEPARATE process writing raw
samples to a JSONL file; also computes aggregate metrics from raw samples.

Usage:
    python scripts/wp2_resource_sampler.py --run \
        --out <samples.jsonl> [--duration 3600] [--stop-file <f>] [--test-container <name>]
    python scripts/wp2_resource_sampler.py --aggregate --out <samples.jsonl>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.resource_sampler import (  # noqa: E402
    aggregate_samples,
    run_sampler_loop,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--aggregate", action="store_true")
    ap.add_argument("--out", required=True)
    ap.add_argument("--duration", type=float, default=None)
    ap.add_argument("--stop-file", default=None)
    ap.add_argument("--test-container", default=None)
    args = ap.parse_args()

    out_path = Path(args.out)
    if args.run:
        stop_file = Path(args.stop_file) if args.stop_file else None
        n = run_sampler_loop(
            out_path,
            duration_s=args.duration,
            stop_file=stop_file,
            test_container=args.test_container,
        )
        print(f"WROTE {n} samples to {out_path}")
        return 0
    if args.aggregate:
        if not out_path.exists():
            print("no samples file:", out_path)
            return 2
        agg = aggregate_samples(out_path)
        print(json.dumps(agg, indent=1, sort_keys=True))
        return 0
    print("use --run or --aggregate")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
