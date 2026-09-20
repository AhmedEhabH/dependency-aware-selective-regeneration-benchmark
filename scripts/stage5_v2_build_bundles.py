#!/usr/bin/env python3
"""STAGE5_V2_FINAL - materialize the 139 Stage-5 case bundles (T3, ZERO API).

Authorized one-time opening (mission P84) AFTER the preregistration tag exists.
Builds the frozen case bundles (public parent-only + hidden observed-proxy)
exactly like the frozen builders, for:

  - 59 djangoCMS RESERVE tasks (v2 split proposal RESERVE role);
  - 80 Saleor INTERNAL_TEST tasks (saleor split freeze INTERNAL_TEST role).

Uses ONLY the pinned git caches and the frozen miner / enumerators. No model
call. No method change. Deterministic; fail closed on any missing case.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.real_commits import miner, scientific  # noqa: E402
from scripts.saleor_portability_fix import materialize_production_parent  # noqa: E402

DC_CACHE = _PROJECT_DIR / "dist" / "real-commit-cache" / "djangocms"
SC_CACHE = _PROJECT_DIR / "dist" / "pilot-repo-cache" / "saleor"
DC_ANCHOR = miner.DJANGOCMS_ANCHOR_COMMIT
SC_ANCHOR = "2c48391b652c26ce4f27a53d6532d4c873306af0"
DC_SPLIT = _PROJECT_DIR / "research" / "transparency" / "v2_split_proposal.json"
SC_SPLIT = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor" / "split_freeze_saleor.json"
DC_OUT = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v2"
SC_OUT = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor"
DC_META = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v2"
SC_META = _PROJECT_DIR / "research" / "transparency" / "saleor_candidate_metadata.json"
CREATED_UTC = "2026-09-20T00:00:00+00:00"


def build_dc_reserve() -> int:
    prop = json.loads(DC_SPLIT.read_text(encoding="utf-8"))
    assignment = prop["assignment"]
    ids = sorted(c for c, r in assignment.items() if r == "RESERVE")
    assert len(ids) == 59, f"expected 59 dc RESERVE, got {len(ids)}"
    miner_dev = json.loads((_PROJECT_DIR / "benchmark_data" / "real_commit_impact_v1" /
                            "miner_dev_manifest.json").read_text(encoding="utf-8"))
    mdt = frozenset(m["target_commit"] for m in miner_dev["cases"])
    cands, _ = scientific.enumerate_scientific_candidates(
        DC_CACHE, DC_ANCHOR, window=scientific.SCIENTIFIC_WINDOW, miner_dev_targets=mdt)
    kept, _ = scientific.deduplicate_candidates(cands)
    by_cid = {miner.make_case_id(c["sha"]): c for c in kept}
    missing = [c for c in ids if c not in by_cid]
    if missing:
        print("DC_RESERVE_MISSING", missing)
        return 2
    sci = DC_OUT / "scientific"
    sci.mkdir(parents=True, exist_ok=True)
    built = 0
    skipped_existing = 0
    for cid in ids:
        if (sci / cid / "case_manifest.json").exists():
            skipped_existing += 1
            continue
        c = by_cid[cid]
        miner.build_case(cache_dir=DC_CACHE, case_id=cid, target=c["sha"],
                         parent=c["parent"], name_status=c["status"],
                         eligibility=c["eligibility"], output_dir=sci,
                         created_utc=CREATED_UTC, partition_role="SCIENTIFIC",
                         split="RESERVE")
        built += 1
    print("dc_reserve_built", built, "already_existing", skipped_existing)
    return 0


def build_saleor_it() -> int:
    split = json.loads(SC_SPLIT.read_text(encoding="utf-8"))
    assignment = split["assignment"]
    ids = sorted(c for c, r in assignment.items() if r == "INTERNAL_TEST")
    assert len(ids) == 80, f"expected 80 saleor IT, got {len(ids)}"
    meta = json.loads(SC_META.read_text(encoding="utf-8"))
    missing = [c for c in ids if c not in meta or not meta[c].get("eligibility", {}).get("proxy_paths")]
    if missing:
        print("SALEOR_IT_MISSING", missing)
        return 2

    # Portability fix (frozen, equivalence-proven 98/98): production-only
    # parent materializer + production roots (Saleor config adapter).
    miner.PRODUCTION_ROOTS = ("saleor",)

    def _production_only_extract(cache_dir, parent: str, dest: Path) -> None:
        materialize_production_parent(cache_dir, parent, dest, roots=("saleor",))

    miner.extract_parent_tree = _production_only_extract

    sci = SC_OUT / "scientific"
    sci.mkdir(parents=True, exist_ok=True)
    built = 0
    for cid in ids:
        c = meta[cid]
        miner.build_case(cache_dir=SC_CACHE, case_id=cid, target=c["sha"],
                         parent=c["parent"], name_status=c["status"],
                         eligibility=c["eligibility"], output_dir=sci,
                         created_utc=CREATED_UTC, partition_role="SCIENTIFIC",
                         split="INTERNAL_TEST")
        built += 1
    print("saleor_it_built", built)
    return 0


def main() -> int:
    print("STAGE5 bundle materialization (authorized one-shot opening)")
    rc = 0
    rc |= build_dc_reserve()
    rc |= build_saleor_it()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
