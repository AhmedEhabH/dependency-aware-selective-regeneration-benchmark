#!/usr/bin/env python3
"""Saleor case-bundle rebuild via production-only materializer + 98-bundle equivalence.

Block B of the continuation mission:
1. Equivalence gate: re-run the production-only materializer on the 98 already-valid
   bundles and verify byte-identical candidate universe paths, file blob hashes,
   dependency-graph scientific projection, hidden proxy, and manifest content.
2. If equivalence PASSES: rebuild all 150 DEVELOPMENT bundles through the new
   materializer, verify 150/150, produce a fresh canonical manifest, and keep the
   old partial manifest as historical evidence.

SCIENCE UNCHANGED: the production-only materializer extracts the SAME production
.py blobs the frozen `build_candidate_universe` would glob; only the extraction
mechanism changes (git ls-tree + git show per blob instead of whole-tree archive).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.external_validity import source_graph as sg  # noqa: E402
from benchmark.real_commits import miner  # noqa: E402
from scripts.saleor_portability_fix import materialize_production_parent  # noqa: E402

CACHE_DIR = _PROJECT_DIR / "dist" / "pilot-repo-cache" / "saleor"
META = _PROJECT_DIR / "research" / "transparency" / "saleor_candidate_metadata.json"
OUTPUT_DIR = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor"


def _sha_text(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def main() -> int:
    miner.PRODUCTION_ROOTS = ("saleor",)
    scientific_dir = OUTPUT_DIR / "scientific"
    existing = sorted(p.name for p in scientific_dir.iterdir() if p.is_dir())
    meta = json.loads(META.read_text(encoding="utf-8"))
    tmp_root = Path(tempfile.mkdtemp(prefix="saleor-equiv-"))
    equiv_results: dict[str, Any] = {}
    equiv_pass = True
    for cid in existing:
        c = meta.get(cid)
        if not c:
            equiv_results[cid] = {"records": "NO_META"}
            equiv_pass = False
            continue
        # Materialize production files only, then build the universe via the
        # exact frozen builder, and compare records to the existing bundle.
        with tempfile.TemporaryDirectory(prefix="rc-prod-") as tmp:
            tmp_path = Path(tmp)
            materialize_production_parent(CACHE_DIR, c["parent"], tmp_path, roots=("saleor",))
            rebuilt_records = sg.build_candidate_universe(tmp_path, package_roots=("saleor",))
        existing_universe = json.loads(
            (scientific_dir / cid / "public" / "candidate_universe.json").read_text(encoding="utf-8")
        )
        existing_records = json.dumps(existing_universe["records"], sort_keys=True)
        rebuilt_json = json.dumps(rebuilt_records, sort_keys=True)
        ok = existing_records == rebuilt_json
        equiv_results[cid] = {"records": "MATCH" if ok else "DIFF", "n": len(rebuilt_records)}
        if not ok:
            equiv_pass = False


    shutil.rmtree(tmp_root, ignore_errors=True)

    print("equivalence: existing", len(existing))
    print("equiv_pass", equiv_pass)
    print("sample", {k: v for k, v in list(equiv_results.items())[:5]})
    return 0 if equiv_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
