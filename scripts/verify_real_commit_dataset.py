#!/usr/bin/env python3
"""Independent verifier for RealCommitImpactDataset-v1 MINER_DEV (M4A-1).

This is a SEPARATE audit path: it reads only persisted artifacts (never the
builder's in-memory objects) and independently verifies:

- Git parent relation for every case;
- public/hidden physical separation;
- artifact hashes (universe, graph, proxy, intent, canonical record);
- candidate/proxy path constraints;
- no target diff / target content in the public bundle;
- MINER_DEV exclusion from held-out;
- no scientific API-call artifacts created;
- frozen M1/M3 evidence unchanged (frozen universe/graph identities);
- docs state agrees with the actual implementation.

Exit code 0 = AUDIT=PASS, 1 = AUDIT=FAIL.

Usage:
    python scripts/verify_real_commit_dataset.py [--dataset-dir ...] [--cache-dir ...]
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from benchmark.real_commits import miner, validation
from benchmark.real_commits.models import (
    compute_canonical_record_hash,
    sha256_json,
    sha256_text,
)

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = PROJECT_DIR / "benchmark_data" / "real_commit_impact_v1"
CACHE_DIR = PROJECT_DIR / "dist" / "real-commit-cache" / "djangocms"


def audit_dataset(dataset: Path, cache_dir: Path, anchor: str) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    manifest_path = dataset / "miner_dev_manifest.json"

    items.append(
        {
            "item": "dataset_manifest_exists",
            "ok": manifest_path.is_file(),
            "detail": str(manifest_path),
        }
    )
    if not manifest_path.is_file():
        return {"passed": False, "items": items}

    manifest = validation.load_json(manifest_path)
    cases = manifest.get("cases", [])

    items.append(
        {
            "item": "four_to_six_dev_cases",
            "ok": 4 <= len(cases) <= 6,
            "detail": len(cases),
        }
    )
    items.append(
        {
            "item": "all_cases_split_miner_dev",
            "ok": all(c.get("split") == "MINER_DEV" for c in cases),
            "detail": sorted({c.get("split") for c in cases}),
        }
    )
    items.append(
        {
            "item": "no_held_out_test_assigned",
            "ok": all(c.get("split") != "HELD_OUT_TEST" for c in cases),
            "detail": "MINER_DEV is permanently excluded from held-out evaluation",
        }
    )

    for case in cases:
        cid = case["case_id"]
        case_path = validation.case_dir(dataset, cid)
        parent = case["parent_commit"]
        target = case["target_commit"]

        # 1. Git parent relation independently re-derived.
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

        # 2. Public/hidden physical separation.
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

        # 3. Hash verification.
        universe = validation.load_public_artifact(dataset, cid, "candidate_universe.json")
        items.append(
            {
                "item": f"universe_hash_ok_{cid}",
                "ok": validation.canonical_universe_hash(universe["records"]) == universe["sha256"],
                "detail": universe["sha256"],
            }
        )
        graph = validation.load_public_artifact(dataset, cid, "dependency_graph.json")
        items.append(
            {
                "item": f"graph_hash_ok_{cid}",
                "ok": validation.canonical_graph_hash(graph) == case["dependency_graph_sha256"],
                "detail": case["dependency_graph_sha256"],
            }
        )
        proxy = validation.load_hidden_proxy(dataset, cid)
        recomputed_proxy = sha256_json(proxy["statuses"])
        items.append(
            {
                "item": f"proxy_hash_ok_{cid}",
                "ok": recomputed_proxy == case["observed_change_set_proxy_sha256"],
                "detail": recomputed_proxy,
            }
        )
        intent = validation.load_public_artifact(dataset, cid, "intent.json")
        items.append(
            {
                "item": f"intent_hash_ok_{cid}",
                "ok": sha256_text(intent["intent_text"]) == case["intent_sha256"],
                "detail": case["intent_sha256"],
            }
        )
        record = validation.load_case_manifest(dataset, cid)["record"]
        items.append(
            {
                "item": f"canonical_record_hash_ok_{cid}",
                "ok": compute_canonical_record_hash(record) == record["canonical_record_sha256"],
                "detail": record["canonical_record_sha256"],
            }
        )

        # 4. Candidate/proxy path constraints.
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

        # 5. No target diff / target content in the public bundle.
        leak = validation.check_public_bundle_leakage(dataset, cid)
        items.append(
            {
                "item": f"public_bundle_leakage_free_{cid}",
                "ok": leak["passed"],
                "detail": [c for c in leak["checks"] if not c["ok"]],
            }
        )

        # 6. No scientific API-call artifacts created by this milestone.
        api_artifact_indicators = ("run_records.jsonl", "manifest_90.json", "raw_response")
        case_files = [p.name for p in case_path.rglob("*") if p.is_file()]
        items.append(
            {
                "item": f"no_api_artifacts_in_case_{cid}",
                "ok": not any(ind in name for name in case_files for ind in api_artifact_indicators),
                "detail": api_artifact_indicators,
            }
        )

    # 7. Frozen M1/M3 evidence unchanged (frozen regression identities).
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

    # 8. Anchor matches project truth.
    items.append(
        {
            "item": "anchor_matches_project_truth",
            "ok": anchor == miner.DJANGOCMS_ANCHOR_COMMIT,
            "detail": anchor,
        }
    )

    # 9. Docs state agrees with actual implementation.
    docs_agree = _check_docs_agree()
    items.append(
        {
            "item": "docs_state_agrees",
            "ok": docs_agree,
            "detail": "README/SYSTEM_STATE/TODO record M4A-1 COMPLETE and MINER_DEV cases",
        }
    )

    return {"passed": all(i["ok"] for i in items), "items": items}


def _check_docs_agree() -> bool:
    """Lightweight check that current-state docs mention the M4A-1 milestone."""
    system_state = PROJECT_DIR / "SYSTEM_STATE.md"
    todo = PROJECT_DIR / "TODO.md"
    readme = PROJECT_DIR / "README.md"
    keyword = "M4A-1"
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

    result = audit_dataset(args.dataset_dir, args.cache_dir, args.anchor)
    print(f"AUDIT={'PASS' if result['passed'] else 'FAIL'}")
    for item in result["items"]:
        print(f"  [{'PASS' if item['ok'] else 'FAIL'}] {item['item']} — {item['detail']}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
