#!/usr/bin/env python3
# ruff: noqa: E501
"""SALEOR_RESERVE_300_RMCSS - label-free public-bundle materialization (§9/§19).

For each of the 300 sampled Saleor RESERVE tasks, materialize ONLY the PUBLIC
(parent-only, label-free) case bundle:

  - public/intent.json
  - public/candidate_universe.json
  - public/dependency_graph.json
  - case_manifest.json WITHOUT change_statuses and WITHOUT the hidden proxy

This NEVER writes hidden/observed_change_set_proxy.json and NEVER writes
change_statuses. The label-bearing proxy is loaded ONLY at the §19 outcome-open
step (from saleor_candidate_metadata.json eligibility.proxy_paths).

Deterministic. Uses the frozen production-only parent materializer + the frozen
universe/graph builders (exactly as the frozen saleor bundle builder).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))
sys.path.insert(0, str(_PROJECT_DIR / "scripts"))

from benchmark.real_commits import miner  # noqa: E402
from scripts.saleor_portability_fix import materialize_production_parent  # noqa: E402

SC_META = _PROJECT_DIR / "research" / "transparency" / "saleor_candidate_metadata.json"
SC_CACHE = _PROJECT_DIR / "dist" / "pilot-repo-cache" / "saleor"
SC_DATASET = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor"
SAMPLE = _PROJECT_DIR / "research" / "saleor-reserve-300-rmcss" / "saleor_reserve_300_sample.json"
OUT_DIR = _PROJECT_DIR / "research" / "saleor-reserve-300-rmcss"
CREATED_UTC = "2026-09-20T00:00:00+00:00"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical_json(obj) -> str:
    return json.dumps(obj, indent=1, sort_keys=True)


def main() -> int:
    meta = json.loads(SC_META.read_text(encoding="utf-8"))
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
    selected = sample["selected_ids"]

    miner.PRODUCTION_ROOTS = ("saleor",)
    miner.extract_parent_tree = lambda cache_dir, parent, dest: materialize_production_parent(
        cache_dir, parent, dest, roots=("saleor",))

    sci = SC_DATASET / "scientific"
    sci.mkdir(parents=True, exist_ok=True)
    built = skipped = failed = 0
    for cid in selected:
        case_dir = sci / cid
        if (case_dir / "public" / "candidate_universe.json").exists():
            skipped += 1
            continue
        rec = meta[cid]
        uni = miner.build_parent_universe_and_graph(SC_CACHE, rec["parent"])
        info = miner.commit_info(SC_CACHE, rec["sha"])
        intent = miner.normalize_intent(info.message)
        intent_sha = _sha256_text(intent)

        public_dir = case_dir / "public"
        public_dir.mkdir(parents=True, exist_ok=True)
        (public_dir / "intent.json").write_text(_canonical_json({
            "schema_version": miner.SCHEMA_VERSION, "case_id": cid,
            "intent_text": intent, "intent_source": "commit_message",
            "intent_sha256": intent_sha, "target_commit": rec["sha"],
            "target_commit_time": info.commit_time_utc,
        }), encoding="utf-8")
        (public_dir / "candidate_universe.json").write_text(_canonical_json({
            "schema_version": miner.SCHEMA_VERSION, "case_id": cid,
            "parent_commit": rec["parent"], "count": uni["universe_count"],
            "sha256": uni["universe_hash"], "records": uni["records"],
        }), encoding="utf-8")
        (public_dir / "dependency_graph.json").write_text(
            _canonical_json(uni["graph"]), encoding="utf-8")

        # Label-free manifest (NO change_statuses, NO hidden proxy paths)
        record = {
            "case_id": cid, "parent_commit": rec["parent"],
            "target_commit": rec["sha"], "repository": "saleor",
            "candidate_universe_count": uni["universe_count"],
            "candidate_universe_sha256": uni["universe_hash"],
            "dependency_graph_sha256": uni["graph_hash"],
            "intent_sha256": intent_sha, "created_utc": CREATED_UTC,
            "partition_role": "SCIENTIFIC", "split": "RESERVE",
            "label_free_manifest": True,
        }
        canonical_record_sha256 = _sha256_text(_canonical_json(record))
        manifest = {
            "miner_version": miner.MINER_VERSION,
            "label_free": True,
            "canonical_record_sha256": canonical_record_sha256,
            "public_artifact_paths": {
                "candidate_universe": "public/candidate_universe.json",
                "dependency_graph": "public/dependency_graph.json",
                "intent": "public/intent.json",
            },
            "record": record,
        }
        (case_dir / "case_manifest.json").write_text(_canonical_json(manifest), encoding="utf-8")
        built += 1

    out = {"sampled": len(selected), "built": built, "skipped_existing": skipped,
           "failed": failed, "label_free": True,
           "note": "public-only bundles; hidden proxy NOT written (loaded only at outcome-open)"}
    (OUT_DIR / "saleor_reserve_300_materialize_public.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    print(f"sampled={len(selected)} built={built} skipped={skipped} failed={failed}")
    print(f"wrote {OUT_DIR / 'saleor_reserve_300_materialize_public.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())