#!/usr/bin/env python3
"""Saleor identity migration — 150/150 scientific-payload equivalence proof.

Compares the POST-migration bundles (saleor-rc-*) against the PRE-migration
snapshot (research/transparency/saleor_pre_migration_payload_snapshot.json,
captured before the identity fix) for every DEV case:

1. parent_commit identical
2. target_commit identical
3. split membership identical
4. candidate universe records identical (paths + sha256 + loc + symbols)
5. hidden proxy paths identical (sorted)
6. graph edges identical (sorted)
7. case ID deterministically migrated (old -> saleor-rc-<target sha>)
8. identity fields corrected (repository=saleor, url, license, graph repo_id)

Exits 0 only if ALL 150 pass ALL checks.
"""

# ruff: noqa: E501
from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))


DATASET_DIR = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor"
SNAPSHOT = _PROJECT_DIR / "research" / "transparency" / "saleor_pre_migration_payload_snapshot.json"
MIGRATION = _PROJECT_DIR / "research" / "transparency" / "saleor_case_id_migration.json"

SALEOR_URL = "https://github.com/saleor/saleor"
SALEOR_LICENSE_REF = "BSD-3-Clause; benchmark_data/manifests/repositories.yaml#saleor"
SALEOR_ANCHOR = "2c48391b652c26ce4f27a53d6532d4c873306af0"


def main() -> int:
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))["cases"]
    mapping = json.loads(MIGRATION.read_text(encoding="utf-8"))["old_to_new"]
    scientific = DATASET_DIR / "scientific"
    all_pass = True
    results: dict = {}

    for old_id, pre in snap.items():
        new_id = mapping[old_id]
        d = scientific / new_id
        checks: dict[str, str] = {}
        if not d.is_dir():
            checks["dir"] = "MISSING"
            all_pass = False
            results[old_id] = checks
            continue

        manifest = json.loads((d / "case_manifest.json").read_text(encoding="utf-8"))
        rec = manifest["record"]
        universe = json.loads((d / "public" / "candidate_universe.json").read_text(encoding="utf-8"))
        graph = json.loads((d / "public" / "dependency_graph.json").read_text(encoding="utf-8"))
        proxy = json.loads((d / "hidden" / "observed_change_set_proxy.json").read_text(encoding="utf-8"))

        # 1-3: commits + split
        checks["parent_commit"] = "MATCH" if rec["parent_commit"] == pre["parent_commit"] else "DIFF"
        checks["target_commit"] = "MATCH" if rec["target_commit"] == pre["target_commit"] else "DIFF"
        checks["split"] = "MATCH" if rec["split"] == pre["split"] else "DIFF"

        # 4: universe records identical
        checks["universe_records"] = (
            "MATCH" if json.dumps(universe["records"], sort_keys=True) == json.dumps(pre["universe_records"], sort_keys=True) else "DIFF"
        )
        # 5: proxy identical
        checks["proxy"] = "MATCH" if sorted(proxy["paths"]) == pre["proxy_paths"] else "DIFF"
        # 6: edges identical
        checks["edges"] = "MATCH" if sorted(graph["edges"]) == sorted(pre["graph_edges"]) else "DIFF"
        # 7: deterministic new ID
        expected_id = "saleor-rc-" + rec["target_commit"][:12]
        checks["new_id"] = "MATCH" if (new_id == expected_id and rec["case_id"] == new_id) else "DIFF"
        # 8: identity corrected
        checks["repository"] = "MATCH" if rec["repository"] == "saleor" else "DIFF"
        checks["repository_url"] = "MATCH" if rec["repository_url"] == SALEOR_URL else "DIFF"
        checks["license_ref"] = "MATCH" if rec["repository_license_or_manifest_ref"] == SALEOR_LICENSE_REF else "DIFF"
        checks["graph_repo_id"] = "MATCH" if graph.get("repo_id") == "saleor" else "DIFF"
        checks["anchor"] = "MATCH" if (rec["provenance_hashes"]["anchor_commit"] == SALEOR_ANCHOR) else "DIFF"

        if any(v == "DIFF" for v in checks.values()) or any(v == "MISSING" for v in checks.values()):
            all_pass = False
        results[old_id] = checks

    diff_any = [cid for cid, c in results.items() if any(v in ("DIFF", "MISSING") for v in c.values())]
    print("checked:", len(results))
    print("all_pass:", all_pass)
    print("cases with any DIFF/MISSING:", len(diff_any))
    if diff_any:
        print("first diff cases:", diff_any[:5])
    summary = {"checked": len(results), "all_pass": all_pass, "diff_cases": diff_any, "per_case": results}
    (DATASET_DIR.parent.parent / "research" / "transparency" / "saleor_identity_equivalence_150.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
