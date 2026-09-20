#!/usr/bin/env python3
"""SALEOR_RESERVE_300_RMCSS - temporal descriptor (§10).

Records target-commit dates for the sampled population and the comparison
populations (Saleor DEV, corrected Saleor INTERNAL_TEST) using ONLY commit-date
metadata from the frozen git cache. This does NOT disclose target labels.

Output: research/saleor-reserve-300-rmcss/saleor_reserve_300_temporal.json
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))

SC_META = _PROJECT_DIR / "research" / "transparency" / "saleor_candidate_metadata.json"
SC_CACHE = _PROJECT_DIR / "dist" / "pilot-repo-cache" / "saleor"
SC_SPLIT = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor" / "split_freeze_saleor.json"
SAMPLE = _PROJECT_DIR / "research" / "saleor-reserve-300-rmcss" / "saleor_reserve_300_sample.json"
OUT_DIR = _PROJECT_DIR / "research" / "saleor-reserve-300-rmcss"


def _commit_date(cache: Path, sha: str):
    r = subprocess.run(["git", "-C", str(cache), "show", "-s", "--format=%ci", sha],
                       capture_output=True, text=True, check=False)
    if r.returncode != 0 or not r.stdout.strip():
        return None
    s = r.stdout.strip()
    return s[:10]  # YYYY-MM-DD


def _stats(dates: list[str]) -> dict:
    ds = sorted(dates)
    n = len(ds)
    def med():
        if n == 0:
            return None
        return ds[n // 2]
    return {"n": n, "earliest": ds[0] if n else None,
            "latest": ds[-1] if n else None, "median": med() if n else None}


def main() -> int:
    meta = json.loads(SC_META.read_text(encoding="utf-8"))
    split = json.loads(SC_SPLIT.read_text(encoding="utf-8"))
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
    selected = set(sample["selected_ids"])

    reserve_all = [c for c, r in split["assignment"].items() if r == "RESERVE"]
    dev_all = [c for c, r in split["assignment"].items() if r in ("DEV_TRAIN", "DEV_VALIDATION")]
    it_all = [c for c, r in split["assignment"].items() if r == "INTERNAL_TEST"]

    dates = {}
    for label, ids in (("sample_300", sorted(selected)), ("reserve_1086", reserve_all),
                       ("dev_150", dev_all), ("internal_test_80", it_all)):
        ds = []
        missing = 0
        for cid in ids:
            d = _commit_date(SC_CACHE, meta[cid]["sha"])
            if d is None:
                missing += 1
            else:
                ds.append(d)
        dates[label] = {**_stats(ds), "missing_dates": missing}

    wording = "B"
    # compare sample vs dev
    samp = dates["sample_300"]
    dev = dates["dev_150"]
    if (samp["earliest"] and dev["latest"] and samp["earliest"] > dev["latest"]) or \
            (samp["latest"] and dev["earliest"] and samp["latest"] < dev["earliest"]):
        wording = "A"

    out = {
        "temporal_descriptor_wording": wording,
        "wording_A": "later-period untouched Saleor replication",
        "wording_B": "same/overlapping-period disjoint-commit Saleor replication",
        "date_ranges": dates,
        "note": "target-commit dates are commit metadata only; no target labels disclosed",
    }
    (OUT_DIR / "saleor_reserve_300_temporal.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))
    print(f"wrote {OUT_DIR / 'saleor_reserve_300_temporal.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
