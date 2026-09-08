#!/usr/bin/env python3
"""Persist SHA-256 hashes of ALL frozen scientific evidence (raw + frozen inputs).

Run BEFORE and AFTER documentation changes to prove immutability.
"""

from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from benchmark.external_validity import study_runtime as wiring

PROJECT_DIR = wiring.PROJECT_DIR
STUDY_DIR = PROJECT_DIR / "reports" / "scientific-stagec-djangocms-study-01"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def collect() -> dict:
    out: dict = {}

    # Frozen study inputs
    out["manifest_60.json"] = sha256_file(STUDY_DIR / "manifest_60.json")
    out["run_records.jsonl"] = sha256_file(STUDY_DIR / "run_records.jsonl")
    out["hidden_gold"] = sha256_file(wiring.HIDDEN_GOLD_PATH)
    out["candidate_universe"] = sha256_file(wiring.CANDIDATE_UNIVERSE_PATH)
    out["dependency_graph"] = sha256_file(
        PROJECT_DIR / "benchmark_data" / "external_validity" / "djangocms_5_0_0_dependency_graph.json"
    )
    for sid in sorted(wiring.final_scenario_ids()):
        p = wiring.VISIBLE_DRAFTS_DIR / f"{sid}.yaml"
        out[f"scenario_{sid}"] = sha256_file(p)

    # 60 raw run records
    runs_dir = STUDY_DIR / "runs"
    run_files = sorted(runs_dir.glob("*.json"))
    for rf in run_files:
        out[f"run:{rf.stem}"] = sha256_file(rf)

    return out


def main() -> int:
    hashes = collect()
    print(f"files_hashed={len(hashes)}")
    for k in sorted(hashes):
        print(f"{k}={hashes[k]}")
    out_path = STUDY_DIR / "raw_evidence_hashes.json"
    out_path.write_text(json.dumps(hashes, indent=2, sort_keys=True), encoding="utf-8")
    print(f"persisted={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())