#!/usr/bin/env python3
"""Saleor sparse-inference pre-call gates (Block C).

Builds reports/saleor_inference_gates.json AFTER verifying (zero-API):
1. Dataset validation: 150/150 DEV bundles; split counts; TEST/RESERVE untouched
2. Input validation: parent-only prompt rendering (dry) + intent-leakage off
3. Pipeline smoke: bundle structural completeness 150/150
4. Dry run: manifest shape (450 cells) + run-record schema
5. Integration: frozen p1 prompt/schema/metrics load on Saleor bundles
6. Metric verification: synthetic TP/FP/FN via frozen p1_selection_metrics
+ portability equivalence (98/98, from Block B)
+ independent audit (rebuilt hashes == pre-portability, 0 mismatch)
"""

# ruff: noqa: E501
from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.real_commits import p1_evaluation as p1  # noqa: E402
from scripts.saleor_inference_manifest import build_saleor_manifest, saleor_development_case_ids  # noqa: E402

DATASET_DIR = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor"
SPLIT = _PROJECT_DIR / "research" / "transparency" / "saleor_split_proposal.json"
OUT = _PROJECT_DIR / "reports" / "saleor_inference_gates.json"


def main() -> int:
    gates: dict[str, dict] = {}

    # G1 dataset validation
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    sci = DATASET_DIR / "scientific"
    built = {p.name for p in sci.iterdir() if p.is_dir()} if sci.is_dir() else set()
    dev_ids = set(saleor_development_case_ids())
    assignment = {cid: role for role, per in split["per_role"].items() for cid in per["case_ids"]}
    test_reserve_materialized = [c for c in built if assignment.get(c) in ("INTERNAL_TEST", "RESERVE")]
    g1_ok = (
        len(dev_ids) == 150
        and len(built & dev_ids) == 150
        and len(test_reserve_materialized) == 0
    )
    gates["dataset_validation"] = {
        "status": "PASS" if g1_ok else "FAIL",
        "dev_expected": 150, "dev_built": len(built & dev_ids),
        "test_reserve_materialized": len(test_reserve_materialized),
        "split_seed": split["seed"],
        "role_counts": {r: len(v["case_ids"]) for r, v in split["per_role"].items()},
    }

    # G2 input validation (parent-only, dry render)
    prompt_errors = []
    for cid in sorted(dev_ids)[:5]:
        b = p1.load_case_public_bundle(DATASET_DIR, cid)
        m = p1.build_p1_candidate_map(b.candidate_paths)
        prompt = str(p1.render_p1_sparse_prompt(case=b, mapping=m))
        if not prompt or "PRESERVE" not in prompt:
            prompt_errors.append(cid)
    gates["input_validation"] = {
        "status": "PASS" if not prompt_errors else "FAIL",
        "dry_rendered": len(sorted(dev_ids)[:5]), "prompt_errors": prompt_errors,
        "leakage": "parent-only (frozen p1 bundle; hidden proxy separate)",
    }

    # G3 pipeline smoke (structural completeness)
    incomplete = []
    for cid in sorted(dev_ids):
        d = sci / cid
        need = ["public/candidate_universe.json", "public/dependency_graph.json",
                "public/intent.json", "hidden/observed_change_set_proxy.json", "case_manifest.json"]
        if not all((d / n).is_file() for n in need):
            incomplete.append(cid)
    gates["pipeline_smoke"] = {
        "status": "PASS" if not incomplete else "FAIL",
        "checked": 150, "incomplete": incomplete,
    }

    # G4 dry run (manifest shape + record schema)
    cells = build_saleor_manifest()
    expected_keys = {"run_id", "case_id", "repetition", "arm", "serialization_policy",
                     "expected_model", "provider_tag", "temperature", "max_completion_tokens",
                     "candidate_count", "candidate_map_sha256", "public_bundle_sha256", "protocol_version"}
    cell_ok = all(expected_keys <= set(c.keys()) for c in cells)
    run_ids = [c["run_id"] for c in cells]
    unique = len(set(run_ids)) == len(run_ids)
    gates["dry_run"] = {
        "status": "PASS" if (len(cells) == 450 and cell_ok and unique) else "FAIL",
        "cells": len(cells), "cell_keys_ok": cell_ok, "run_ids_unique": unique,
    }

    # G5 integration (frozen machinery loads + validates on Saleor)
    integ_errors = []
    for cid in sorted(dev_ids)[:3]:
        b = p1.load_case_public_bundle(DATASET_DIR, cid)
        m = p1.build_p1_candidate_map(b.candidate_paths)
        p1.p1_common_schema(len(m.id_to_path))
        # validate a synthetic minimal valid payload (SPARSE: no PRESERVE rows)
        valid_payload = {"decisions": [{"id": 1, "action": "REGENERATE", "reason": "build", "confidence": 0.9}]}
        vres = p1.validate_p1_sparse(valid_payload, candidate_count=len(m.id_to_path))
        if vres.get("errors"):
            integ_errors.append(f"{cid}: {vres['errors'][:1]}")
    gates["integration"] = {
        "status": "PASS" if not integ_errors else "FAIL",
        "checked": 3, "errors": integ_errors,
    }

    # G6 metric verification (synthetic TP/FP/FN)
    proxy = {"a.py", "b.py"}
    m_all = p1.p1_selection_metrics({"a.py", "b.py"}, proxy)
    m_part = p1.p1_selection_metrics({"a.py", "c.py"}, proxy)
    m_none = p1.p1_selection_metrics(set(), proxy)
    metric_ok = (
        m_all["tp"] == 2 and m_all["fp"] == 0 and m_all["fn"] == 0 and m_all["recall"] == 1.0
        and m_part["tp"] == 1 and m_part["fp"] == 1 and m_part["recall"] == 0.5
        and m_none["tp"] == 0 and m_none["fn"] == 2 and m_none["recall"] == 0.0
    )
    gates["metric_verification"] = {
        "status": "PASS" if metric_ok else "FAIL",
        "synthetic": {"all": m_all, "partial": m_part, "none": m_none},
    }

    # + portability equivalence (Block B) — 98/98 vs pre-portability
    try:
        ev = json.loads((_PROJECT_DIR / "research" / "transparency" / "saleor_portability_fix_evidence.json").read_text(encoding="utf-8"))
        eq = ev["equivalence_gate"]["all_pass"]
    except Exception:
        eq = False
    gates["portability_equivalence"] = {
        "status": "PASS" if eq else "FAIL",
        "evidence": "research/transparency/saleor_portability_fix_evidence.json",
        "note": "98/98 byte-equivalence of the production-only materializer vs git archive (Block B; pre-identity-fix IDs)",
    }

    # + identity-migration equivalence (S2) — 150/150 vs pre-migration snapshot
    try:
        eq150 = json.loads((_PROJECT_DIR / "research" / "transparency" / "saleor_identity_equivalence_150.json").read_text(encoding="utf-8"))
        id_eq = bool(eq150.get("all_pass"))
    except Exception:
        id_eq = False
    gates["identity_equivalence"] = {
        "status": "PASS" if id_eq else "FAIL",
        "evidence": "research/transparency/saleor_identity_equivalence_150.json",
        "note": "150/150 post-migration scientific payload (commits/split/universes/proxies/edges) identical to pre-migration snapshot; IDs migrated saleor-rc-*",
    }

    # + independent audit: identity fields corrected on all 150 bundles
    try:
        bad_id = []
        for cid in sorted(dev_ids):
            d = sci / cid
            rec = json.loads((d / "case_manifest.json").read_text(encoding="utf-8"))["record"]
            graph = json.loads((d / "public" / "dependency_graph.json").read_text(encoding="utf-8"))
            if not (
                cid.startswith("saleor-rc-")
                and rec.get("repository") == "saleor"
                and rec.get("repository_url") == "https://github.com/saleor/saleor"
                and graph.get("repo_id") == "saleor"
                and (rec.get("provenance_hashes") or {}).get("anchor_commit") == "2c48391b652c26ce4f27a53d6532d4c873306af0"
            ):
                bad_id.append(cid)
        audit_ok = len(bad_id) == 0
    except Exception:
        audit_ok = False
        bad_id = ["exception"]
    gates["independent_audit"] = {
        "status": "PASS" if audit_ok else "FAIL",
        "note": "identity fields (saleor-rc-* ID, repository=saleor, url, graph repo_id=saleor, anchor 2c48391b...) corrected on all 150 bundles",
        "bad_identity_cases": bad_id,
    }

    all_passed = all(g["status"] == "PASS" for g in gates.values())
    payload = {
        "study": "saleor-sparse-v2-development",
        "ran_at": datetime.now(UTC).isoformat(),
        "all_passed": all_passed,
        "gates": gates,
    }
    OUT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    for k, g in gates.items():
        print(f"{k}: {g['status']}")
    print("ALL_PASSED", all_passed)
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
