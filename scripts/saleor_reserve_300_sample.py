#!/usr/bin/env python3
"""SALEOR_RESERVE_300_RMCSS - deterministic label-free sampling (§8).

Samples EXACTLY 300 Saleor RESERVE task IDs without replacement using:

  seed = 20260920
  rng  = numpy.random.default_rng(20260920)

Procedure:
  1. obtain the frozen Saleor RESERVE case-ID universe WITHOUT loading any
     hidden target outcome;
  2. normalize case IDs exactly as current benchmark IDs (they already are
     `saleor-rc-<shortsha>`);
  3. sort candidate IDs lexicographically;
  4. initialize numpy.random.default_rng(20260920);
  5. select 300 unique indexes without replacement;
  6. persist the selected case IDs sorted lexicographically.

Outputs (research/saleor-reserve-300-rmcss/):
  - saleor_reserve_300_sample.json   (manifest: population count, algorithm,
    rng library/version, seed, selected IDs, sha256)
  - saleor_reserve_300_sample.txt    (newline-delimited selected IDs)

NO target labels are loaded. NO proxy is read. Deterministic.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))

import numpy as np  # noqa: E402

SC_SPLIT = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor" / "split_freeze_saleor.json"
OUT_DIR = _PROJECT_DIR / "research" / "saleor-reserve-300-rmcss"
SAMPLE_N = 300
SEED = 20260920


def main() -> int:
    split = json.loads(SC_SPLIT.read_text(encoding="utf-8"))
    assignment = split["assignment"]
    reserve = sorted(c for c, r in assignment.items() if r == "RESERVE")
    if len(reserve) != 1086:
        print(f"expected 1086 Saleor RESERVE tasks, got {len(reserve)}")
        return 1

    rng = np.random.default_rng(SEED)
    idx = rng.choice(len(reserve), size=SAMPLE_N, replace=False)
    selected = sorted(reserve[int(i)] for i in idx)

    ids_text = "\n".join(selected) + "\n"
    sha = hashlib.sha256(ids_text.encode("utf-8")).hexdigest()

    manifest = {
        "population": len(reserve),
        "population_role": "RESERVE",
        "sample_size": SAMPLE_N,
        "sampling_seed": SEED,
        "rng": "numpy.random.default_rng",
        "rng_version": np.__version__,
        "sampling_algorithm": "rng.choice(n, size=300, replace=False) over "
                              "lexicographically sorted RESERVE case IDs; output sorted lexicographically",
        "selected_ids_sha256": sha,
        "selected_ids": selected,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "saleor_reserve_300_sample.json").write_text(
        json.dumps(manifest, indent=1), encoding="utf-8")
    (OUT_DIR / "saleor_reserve_300_sample.txt").write_text(ids_text, encoding="utf-8")
    print(f"population={len(reserve)} sample={SAMPLE_N} seed={SEED}")
    print(f"selected_ids_sha256={sha}")
    print(f"first5={selected[:5]} last5={selected[-5:]}")
    print(f"wrote {OUT_DIR / 'saleor_reserve_300_sample.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
