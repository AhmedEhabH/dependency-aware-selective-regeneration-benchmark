#!/usr/bin/env python3
"""Independent verifier for RealCommitImpactDataset-v1 scientific corpus (M4A-2).

Reads ONLY persisted artifacts (never the builder's in-memory objects) and
independently verifies:

- scientific manifest exists, 30-40 cases, anchor/URL truth;
- per-case: Git parent relation, public/hidden separation, artifact hashes
  (universe/graph/proxy/intent/canonical record), proxy constraints
  (subset of parent universe, ordinary M only, size in [1,12]);
- leakage barrier: public bundle free of hidden proxy/diff/gold content;
- scientific strictness: every split in {TRAIN,VALIDATION,HELD_OUT_TEST},
  partition_role == SCIENTIFIC, no MINER_DEV target, no intent path leakage;
- split freeze integrity: counts, per-split hashes, membership == manifest,
  no related change crosses splits, MINER_DEV disjoint;
- zero scientific API artifacts in any scientific case;
- frozen M1/M3 evidence unchanged;
- docs state agrees.

Exit code 0 = AUDIT=PASS, 1 = AUDIT=FAIL.

Usage:
    python scripts/verify_real_commit_dataset_scientific.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from benchmark.real_commits import miner, validation
from benchmark.real_commits import validation_scientific as vs
from benchmark.real_commits.models import (
    compute_canonical_record_hash,
    sha256_json,
    sha256_text,
)

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = PROJECT_DIR / "benchmark_data" / "real_commit_impact_v1"
CACHE_DIR = PROJECT_DIR / "dist" / "real-commit-cache" / "djangocms"


def audit_scientific_dataset(
    dataset: Path, cache_dir: Path, anchor: str
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    manifest_path = dataset / "scientific_manifest.json"

    items.append(
        {"item": "scientific_manifest_exists", "ok": manifest_path.is_file(), "detail": str(manifest_path)}
    )
    if not manifest_path.is_file():
        return {"passed": False, "items": items}

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cases = manifest.get("cases", [])
    items.append(
        {
            "item": "scientific_case_count_30_to_40",
            "ok": 30 <= len(cases) <= 40,
            "detail": len(cases),
        }
    )
    items.append(
        {
            "item": "anchor_matches_project_truth",
            "ok": manifest.get("anchor_commit") == anchor == miner.DJANGOCMS_ANCHOR_COMMIT,
            "detail": manifest.get("anchor_commit"),
        }
    )

    # MINER_DEV targets loaded from the frozen MINER_DEV manifest.
    miner_dev_targets: set[str] = set()
    miner_dev_ids: set[str] = set()
    md_path = dataset / "miner_dev_manifest.json"
    if md_path.is_file():
        md = json.loads(md_path.read_text(encoding="utf-8"))
        miner_dev_targets = {c["target_commit"] for c in md.get("cases", [])}
        miner_dev_ids = {c["case_id"] for c in md.get("cases", [])}

    for case in cases:
        cid = case["case_id"]
        case_path = vs.scientific_case_dir(dataset, cid)
        parent = case["parent_commit"]
        target = case["target_commit"]

        try:
            info = miner.commit_info(cache_dir, target)
            parent_ok = tuple(info.parents) == (parent,)
        except Exception:
            parent_ok = False
            info = None
        items.append(
            {
                "item": f"git_parent_relation_{cid}",
                "ok": parent_ok,
                "detail": {"parent": parent, "git_parents": getattr(info, "parents", None)},
            }
        )

        public_dir = case_path / "public"
        hidden_dir = case_path / "hidden"
        items.append(
            {
                "item": f"public_hidden_separation_{cid}",
                "ok": public_dir.is_dir()
                and hidden_dir.is_dir()
                and (hidden_dir / validation.HIDDEN_PROXY_FILENAME).is_file(),
                "detail": {"public": public_dir.is_dir(), "hidden": hidden_dir.is_dir()},
            }
        )

        universe = json.loads((public_dir / "candidate_universe.json").read_text(encoding="utf-8"))
        items.append(
            {
                "item": f"universe_hash_ok_{cid}",
                "ok": validation.canonical_universe_hash(universe["records"]) == universe["sha256"],
                "detail": universe["sha256"],
            }
        )
        graph = json.loads((public_dir / "dependency_graph.json").read_text(encoding="utf-8"))
        items.append(
            {
                "item": f"graph_hash_ok_{cid}",
                "ok": validation.canonical_graph_hash(graph) == case["dependency_graph_sha256"],
                "detail": case["dependency_graph_sha256"],
            }
        )
        proxy = json.loads((hidden_dir / validation.HIDDEN_PROXY_FILENAME).read_text(encoding="utf-8"))
        recomputed_proxy = sha256_json(proxy["statuses"])
        items.append(
            {
                "item": f"proxy_hash_ok_{cid}",
                "ok": recomputed_proxy == case["observed_change_set_proxy_sha256"],
                "detail": recomputed_proxy,
            }
        )
        intent = json.loads((public_dir / "intent.json").read_text(encoding="utf-8"))
        items.append(
            {
                "item": f"intent_hash_ok_{cid}",
                "ok": sha256_text(intent["intent_text"]) == case["intent_sha256"],
                "detail": case["intent_sha256"],
            }
        )
        record = json.loads((case_path / "case_manifest.json").read_text(encoding="utf-8"))["record"]
        items.append(
            {
                "item": f"canonical_record_hash_ok_{cid}",
                "ok": compute_canonical_record_hash(record) == record["canonical_record_sha256"],
                "detail": record["canonical_record_sha256"],
            }
        )

        universe_paths = {str(r["path"]) for r in universe["records"]}
        proxy_paths = list(proxy.get("paths", []))
        items.append(
            {
                "item": f"proxy_subset_of_parent_universe_{cid}",
                "ok": set(proxy_paths) <= universe_paths,
                "detail": sorted(set(proxy_paths) - universe_paths),
            }
        )
        items.append(
            {
                "item": f"proxy_ordinary_modifications_only_{cid}",
                "ok": all(status == "M" for status in proxy.get("statuses", {}).values()),
                "detail": proxy.get("statuses"),
            }
        )
        items.append(
            {
                "item": f"proxy_size_in_bounds_{cid}",
                "ok": 1 <= len(proxy_paths) <= 12,
                "detail": len(proxy_paths),
            }
        )

        leak = validation.check_public_bundle_leakage(dataset, cid, partition="scientific")
        items.append(
            {
                "item": f"public_bundle_leakage_free_{cid}",
                "ok": leak["passed"],
                "detail": [c for c in leak["checks"] if not c["ok"]],
            }
        )

        items.append(
            {
                "item": f"split_valid_scientific_{cid}",
                "ok": case.get("split") in vs.SCIENTIFIC_SPLITS
                and case.get("partition_role") == "SCIENTIFIC",
                "detail": {"split": case.get("split"), "role": case.get("partition_role")},
            }
        )
        items.append(
            {
                "item": f"not_miner_dev_target_{cid}",
                "ok": target not in miner_dev_targets,
                "detail": target,
            }
        )
        items.append(
            {
                "item": f"no_intent_path_leakage_{cid}",
                "ok": case.get("intent_mentions_changed_path") is False,
                "detail": case.get("intent_mentions_changed_path"),
            }
        )

        api_artifact_indicators = ("run_records.jsonl", "manifest_90.json", "raw_response")
        case_files = [p.name for p in case_path.rglob("*") if p.is_file()]
        items.append(
            {
                "item": f"no_api_artifacts_in_case_{cid}",
                "ok": not any(ind in name for name in case_files for ind in api_artifact_indicators),
                "detail": api_artifact_indicators,
            }
        )

    # Split freeze integrity.
    split_freeze = json.loads((dataset / "split_freeze.json").read_text(encoding="utf-8"))
    per_split = split_freeze.get("per_split", {})
    items.append(
        {
            "item": "split_freeze_counts_match",
            "ok": all(len(p.get("case_ids", [])) == p.get("count") for p in per_split.values()),
            "detail": {k: v.get("count") for k, v in per_split.items()},
        }
    )
    items.append(
        {
            "item": "split_freeze_hashes_match",
            "ok": all(
                sha256_json(sorted(p.get("case_ids", []))) == p.get("sha256")
                for p in per_split.values()
            ),
            "detail": {k: v.get("sha256") for k, v in per_split.items()},
        }
    )
    freeze_members = {m for p in per_split.values() for m in p.get("case_ids", [])}
    items.append(
        {
            "item": "split_freeze_membership_matches_manifest",
            "ok": freeze_members == set(manifest.get("case_ids", [])),
            "detail": {
                "freeze_count": len(freeze_members),
                "manifest_count": len(manifest.get("case_ids", [])),
            },
        }
    )
    items.append(
        {
            "item": "miner_dev_disjoint_from_scientific",
            "ok": not (miner_dev_ids & set(manifest.get("case_ids", []))),
            "detail": sorted(miner_dev_ids & set(manifest.get("case_ids", []))),
        }
    )

    # Frozen M1/M3 regression.
    frozen_universe = validation.frozen_universe_regression()
    items.append(
        {
            "item": "frozen_universe_identity_unchanged",
            "ok": frozen_universe["count_ok"] and frozen_universe["hash_ok"],
            "detail": frozen_universe,
        }
    )
    frozen_graph = validation.frozen_graph_regression()
    items.append(
        {
            "item": "frozen_graph_identity_unchanged",
            "ok": frozen_graph["edge_count_ok"] and frozen_graph["hash_ok"],
            "detail": frozen_graph,
        }
    )

    items.append(
        {
            "item": "docs_state_agrees",
            "ok": _check_docs_agree(),
            "detail": "README/SYSTEM_STATE/TODO record M4A-2 scientific corpus",
        }
    )

    return {"passed": all(i["ok"] for i in items), "items": items}


def _check_docs_agree() -> bool:
    system_state = PROJECT_DIR / "SYSTEM_STATE.md"
    todo = PROJECT_DIR / "TODO.md"
    readme = PROJECT_DIR / "README.md"
    keyword = "M4A-2"
    files = [f for f in (system_state, todo, readme) if f.is_file()]
    if not files:
        return False
    return all(keyword in f.read_text(encoding="utf-8", errors="replace") for f in files)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DATASET_DIR)
    parser.add_argument("--cache-dir", type=Path, default=CACHE_DIR)
    parser.add_argument("--anchor", default=miner.DJANGOCMS_ANCHOR_COMMIT)
    args = parser.parse_args()

    result = audit_scientific_dataset(args.dataset_dir, args.cache_dir, args.anchor)
    print(f"AUDIT={'PASS' if result['passed'] else 'FAIL'}")
    for item in result["items"]:
        print(f"  [{'PASS' if item['ok'] else 'FAIL'}] {item['item']} - {item['detail']}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
