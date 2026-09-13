#!/usr/bin/env python3
"""Build the RealCommitImpactDataset-v1 MINER_DEV subset (M4A-1).

Deterministic, auditable miner over real djangoCMS history. ZERO scientific
LLM/API calls. Writes:

- benchmark_data/real_commit_impact_v1/schema.json
- benchmark_data/real_commit_impact_v1/miner_dev_manifest.json
- benchmark_data/real_commit_impact_v1/miner_dev/<case-id>/{public,hidden,...}
- reports/REAL_COMMIT_M4A1_VALIDATION.md + gates JSON

Usage:
    python scripts/build_real_commit_dataset.py
    python scripts/build_real_commit_dataset.py --window 3000 --max-cases 6
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from benchmark.real_commits import miner, validation
from benchmark.real_commits.models import (
    MINER_VERSION,
    SCHEMA_VERSION,
    canonical_json,
    compute_canonical_dataset_manifest_hash,
)

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = PROJECT_DIR / "benchmark_data" / "real_commit_impact_v1"
CACHE_DIR = PROJECT_DIR / "dist" / "real-commit-cache" / "djangocms"
REPORTS_DIR = PROJECT_DIR / "reports"

GATE_REPORT_PATH = REPORTS_DIR / "REAL_COMMIT_M4A1_VALIDATION.md"
GATES_JSON_PATH = REPORTS_DIR / "real_commit_m4a1_gates.json"


def write_schema(output_dir: Path) -> Path:
    schema: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "miner_version": MINER_VERSION,
        "record_fields": {
            "schema_version": "str",
            "case_id": "str",
            "repository": "str",
            "repository_url": "str",
            "repository_license_or_manifest_ref": "str",
            "parent_commit": "str (40-hex)",
            "target_commit": "str (40-hex)",
            "target_commit_time": "str (ISO-8601 UTC)",
            "intent_text": "str",
            "intent_source": "str (commit_message in M4A-1)",
            "intent_sha256": "str",
            "candidate_universe_artifact": "str (public/candidate_universe.json)",
            "candidate_universe_count": "int",
            "candidate_universe_sha256": "str",
            "dependency_graph_artifact": "str (public/dependency_graph.json)",
            "dependency_graph_sha256": "str",
            "observed_change_set_proxy_artifact": "str (hidden/observed_change_set_proxy.json)",
            "observed_change_set_proxy_count": "int",
            "observed_change_set_proxy_sha256": "str",
            "change_statuses": "dict[str,str]",
            "rename_delete_metadata": "dict",
            "change_type": "str (conservative taxonomy; UNKNOWN allowed)",
            "eligibility_decision": "str (ELIGIBLE|INELIGIBLE)",
            "eligibility_reason_codes": "list[str]",
            "intent_mentions_changed_path": "bool",
            "partition_role": "str (MINER_DEVELOPMENT in M4A-1)",
            "split": "str (MINER_DEV|TRAIN|VALIDATION|HELD_OUT_TEST)",
            "miner_version": "str",
            "provenance_hashes": "dict",
            "created_utc": "str (excluded from canonical record hash)",
            "canonical_record_sha256": "str",
        },
        "split_values": ["MINER_DEV", "TRAIN", "VALIDATION", "HELD_OUT_TEST"],
        "exclusion_reason_codes": list(miner.EXCLUSION_REASON_CODES),
        "scientific_boundary": {
            "inference_repository_state": "parent commit only",
            "candidate_universe": "production python files present at parent only",
            "dependency_graph": "derived from source present at parent only",
            "hidden_evaluation_proxy": "production files observed changed by diff parent->target",
            "semantic_gold_fabricated": False,
        },
    }
    path = output_dir / "schema.json"
    path.write_text(canonical_json(schema), encoding="utf-8")
    return path


def build_dataset(
    *,
    cache_dir: Path,
    anchor: str,
    window: int | None,
    max_cases: int,
    dataset_dir: Path,
    created_utc: str,
) -> dict[str, Any]:
    """Acquire cache, select MINER_DEV cases, build public/hidden artifacts."""
    miner.acquire_cache(cache_dir, miner.REPOSITORY_URL_DJANGOCMS, anchor)
    chosen, summary = miner.select_miner_dev_cases(
        cache_dir,
        anchor,
        max_cases=max_cases,
        window=window,
    )
    if len(chosen) < 4:
        raise RuntimeError(
            f"fewer than 4 eligible MINER_DEV cases after window={window}: "
            f"got {len(chosen)}. Expand the scan window, do not loosen rules."
        )

    dataset_dir.mkdir(parents=True, exist_ok=True)
    write_schema(dataset_dir)

    cases: list[dict[str, Any]] = []
    for cand in chosen:
        target = cand["sha"]
        parent = cand["parent"]
        case_id = miner.make_case_id(target)
        name_status = miner.diff_name_status(cache_dir, parent, target)
        eligibility = miner.evaluate_eligibility(
            parents=(parent,),
            intent=cand["intent"],
            name_status=name_status,
            allow_intent_path_leakage=True,
        )
        miner.build_case(
            cache_dir=cache_dir,
            case_id=case_id,
            target=target,
            parent=parent,
            name_status=name_status,
            eligibility=eligibility,
            output_dir=dataset_dir / "miner_dev",
            created_utc=created_utc,
        )
        manifest = validation.load_case_manifest(dataset_dir, case_id)
        cases.append(manifest["record"])

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "miner_version": MINER_VERSION,
        "dataset_version": "v1",
        "repository": "djangocms",
        "repository_url": miner.REPOSITORY_URL_DJANGOCMS,
        "anchor_commit": anchor,
        "created_utc": created_utc,
        "case_ids": [c["case_id"] for c in cases],
        "cases": cases,
        "canonical_manifest_sha256": "",
    }
    manifest["canonical_manifest_sha256"] = compute_canonical_dataset_manifest_hash(manifest)
    manifest_path = dataset_dir / "miner_dev_manifest.json"
    manifest_path.write_text(canonical_json(manifest), encoding="utf-8")

    return {
        "dataset_dir": dataset_dir,
        "manifest_path": manifest_path,
        "cases": cases,
        "scan_summary": summary,
    }


def run_gates_and_report(
    dataset_dir: Path,
    cache_dir: Path,
    anchor: str,
    created_utc: str,
) -> list[dict[str, Any]]:
    gate_results = validation.run_six_gates(dataset_dir, cache_dir, anchor)
    validation.persist_gate_results(gate_results, GATES_JSON_PATH)
    all_pass = validation.all_gates_pass(gate_results)
    GATE_REPORT_PATH.write_text(
        _render_gate_report(gate_results, created_utc),
        encoding="utf-8",
    )
    if not all_pass:
        raise RuntimeError(f"one or more M4A-1 gates FAILED: {GATES_JSON_PATH}")
    return gate_results


def _render_gate_report(gate_results: list[dict[str, Any]], created_utc: str) -> str:
    lines = [
        "# RealCommitImpactDataset-v1 (M4A-1) — Six Pre-Benchmark Validation Gates",
        "",
        f"**Generated:** {created_utc}",
        f"**Minery version:** {MINER_VERSION}",
        "",
        "| # | Gate | Result | Checks |",
        "|---|---|---|---|",
    ]
    for gate in gate_results:
        lines.append(
            f"| {gate['gate']} | {gate['name']} | "
            f"{'PASS' if gate['passed'] else 'FAIL'} | {len(gate['checks'])} |"
        )
    lines.append("")
    for gate in gate_results:
        lines.append(f"## Gate {gate['gate']} — {gate['name']}: {'PASS' if gate['passed'] else 'FAIL'}")
        lines.append("")
        for check in gate["checks"]:
            status = "PASS" if check["ok"] else "FAIL"
            lines.append(f"- [{status}] {check['check']} — `{check.get('detail')}`")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=CACHE_DIR)
    parser.add_argument("--anchor", default=miner.DJANGOCMS_ANCHOR_COMMIT)
    parser.add_argument("--window", type=int, default=None, help="scan window (ancestors)")
    parser.add_argument("--max-cases", type=int, default=6)
    parser.add_argument("--dataset-dir", type=Path, default=DATASET_DIR)
    args = parser.parse_args()

    created_utc = datetime.now(UTC).isoformat()

    result = build_dataset(
        cache_dir=args.cache_dir,
        anchor=args.anchor,
        window=args.window,
        max_cases=args.max_cases,
        dataset_dir=args.dataset_dir,
        created_utc=created_utc,
    )

    print("=== RealCommitImpactDataset-v1 MINER_DEV build ===")
    print(f"dataset_dir: {result['dataset_dir']}")
    print(f"manifest:    {result['manifest_path']}")
    print(f"scan:        {result['scan_summary']}")
    print("")
    for case in result["cases"]:
        print(
            f"  case={case['case_id']} "
            f"parent={case['parent_commit'][:12]} target={case['target_commit'][:12]} "
            f"proxy={case['observed_change_set_proxy_count']} "
            f"universe={case['candidate_universe_count']} "
            f"leak={case['intent_mentions_changed_path']}"
        )

    gate_results = run_gates_and_report(
        args.dataset_dir,
        args.cache_dir,
        args.anchor,
        created_utc,
    )
    for gate in gate_results:
        print(f"GATE {gate['gate']} {gate['name']}: {'PASS' if gate['passed'] else 'FAIL'}")
    print(f"gates JSON: {GATES_JSON_PATH}")
    print(f"report:     {GATE_REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
