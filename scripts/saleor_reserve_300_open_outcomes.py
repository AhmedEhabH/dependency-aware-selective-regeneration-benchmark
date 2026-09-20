#!/usr/bin/env python3
"""SALEOR_RESERVE_300_RMCSS - OPEN OUTCOMES ONCE (§19).

Loads the hidden target changed-file/proxy outcomes for the preregistered
eligible sample (the 300 Saleor RESERVE tasks) from
saleor_candidate_metadata.json eligibility.proxy_paths, and persists them to
saleor_reserve_300_proxies.json.

This is the ONE-TIME outcome-open step; it runs only AFTER the amended
preregistration is pushed/tagged and the label-free parity gate PASSES.
No configuration may change after this point.
"""
from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))

SC_META = _PROJECT_DIR / "research" / "transparency" / "saleor_candidate_metadata.json"
OUT_DIR = _PROJECT_DIR / "research" / "saleor-reserve-300-rmcss"
SAMPLE = OUT_DIR / "saleor_reserve_300_sample.json"


def main() -> int:
    meta = json.loads(SC_META.read_text(encoding="utf-8"))
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
    selected = sample["selected_ids"]
    proxies = {}
    missing = []
    for cid in selected:
        elig = (meta.get(cid) or {}).get("eligibility") or {}
        paths = elig.get("proxy_paths") or []
        if not paths:
            missing.append(cid)
        proxies[cid] = sorted(str(p) for p in paths)
    if missing:
        print(f"PROXY_MISSING: {len(missing)} tasks with empty proxy")
        for m in missing:
            print("  ", m)
        return 1
    out = {
        "opened_once": True,
        "opened_utc": datetime.now(UTC).isoformat(),
        "n_tasks": len(proxies),
        "proxy_source": "saleor_candidate_metadata.json eligibility.proxy_paths",
        "proxies": proxies,
    }
    (OUT_DIR / "saleor_reserve_300_proxies.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    total = sum(len(p) for p in proxies.values())
    print(f"outcomes opened ONCE for {len(proxies)} tasks; total proxy files {total}")
    print(f"wrote {OUT_DIR / 'saleor_reserve_300_proxies.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
