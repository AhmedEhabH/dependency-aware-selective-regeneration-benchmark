#!/usr/bin/env python3
"""Snapshot Saleor scientific payload BEFORE identity migration (equivalence basis).

Captures, per DEV case (old djangocms-rc-* ID):
- parent_commit, target_commit, split (from manifest record)
- candidate universe records (paths + sha256 + loc + module + symbols)
- hidden proxy paths (sorted)
- graph edges (sorted)
- universe hash, graph canonical hash (pre-migration)

Written to research/transparency/saleor_pre_migration_payload_snapshot.json.
ZERO model calls.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.external_validity import source_graph as sg  # noqa: E402

DATASET_DIR = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor"
OUT = _PROJECT_DIR / "research" / "transparency" / "saleor_pre_migration_payload_snapshot.json"


def main() -> int:
    scientific = DATASET_DIR / "scientific"
    bundles = sorted(p.name for p in scientific.iterdir() if p.is_dir())
    snap: dict = {}
    for cid in bundles:
        d = scientific / cid
        manifest = json.loads((d / "case_manifest.json").read_text(encoding="utf-8"))
        rec = manifest["record"]
        universe = json.loads((d / "public" / "candidate_universe.json").read_text(encoding="utf-8"))
        graph = json.loads((d / "public" / "dependency_graph.json").read_text(encoding="utf-8"))
        proxy = json.loads((d / "hidden" / "observed_change_set_proxy.json").read_text(encoding="utf-8"))
        snap[cid] = {
            "parent_commit": rec["parent_commit"],
            "target_commit": rec["target_commit"],
            "split": rec["split"],
            "universe_count": len(universe["records"]),
            "universe_records": universe["records"],
            "universe_hash": universe["sha256"],
            "graph_hash": sg.canonical_graph_hash(graph),
            "graph_edges": sorted(graph["edges"]),
            "proxy_paths": sorted(proxy["paths"]),
            "proxy_sha256": proxy["sha256"],
        }
    OUT.write_text(
        json.dumps({"captured_at": datetime.now(UTC).isoformat(), "n": len(snap), "cases": snap}, indent=2),
        encoding="utf-8",
    )
    print("snapshot cases:", len(snap))
    print("output:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
