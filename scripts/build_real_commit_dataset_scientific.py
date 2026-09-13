#!/usr/bin/env python3
"""Build the RealCommitImpactDataset-v1 SCIENTIFIC corpus (M4A-2).

Deterministic, auditable. ZERO scientific LLM/API calls. Writes:

- benchmark_data/real_commit_impact_v1/scientific/<case-id>/{public,hidden,...}
- benchmark_data/real_commit_impact_v1/scientific_manifest.json
- benchmark_data/real_commit_impact_v1/split_freeze.json
- reports/REAL_COMMIT_M4A2_ADJUDICATION.md + reports/real_commit_m4a2_adjudication.json
- reports/REAL_COMMIT_M4A2_VALIDATION.md + reports/real_commit_m4a2_gates.json

Usage:
    python scripts/build_real_commit_dataset_scientific.py
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from benchmark.real_commits import miner, scientific
from benchmark.real_commits.models import MINER_VERSION, canonical_json

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = PROJECT_DIR / "benchmark_data" / "real_commit_impact_v1"
CACHE_DIR = PROJECT_DIR / "dist" / "real-commit-cache" / "djangocms"
REPORTS_DIR = PROJECT_DIR / "reports"

ADJUDICATION_REPORT_PATH = REPORTS_DIR / "REAL_COMMIT_M4A2_ADJUDICATION.md"
ADJUDICATION_JSON_PATH = REPORTS_DIR / "real_commit_m4a2_adjudication.json"
GATE_REPORT_PATH = REPORTS_DIR / "REAL_COMMIT_M4A2_VALIDATION.md"
GATES_JSON_PATH = REPORTS_DIR / "real_commit_m4a2_gates.json"


def load_miner_dev_targets(dataset_dir: Path) -> frozenset[str]:
    manifest_path = dataset_dir / "miner_dev_manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError(f"miner_dev_manifest.json not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return frozenset(c["target_commit"] for c in manifest.get("cases", []))


def render_adjudication_report(result: dict[str, Any], created_utc: str) -> str:
    lines = [
        "# RealCommitImpactDataset-v1 (M4A-2) — Scientific Corpus Adjudication",
        "",
        f"**Generated:** {created_utc}",
        f"**Miner version:** {MINER_VERSION}",
        f"**Window:** newest {result['scan_summary']['window']} ancestors of the frozen anchor",
        "",
        "## 1. Commits scanned",
        "",
        f"- Ancestors scanned (newest-first, window): "
        f"{result['scan_summary']['window']}",
        f"- Eligible after frozen eligibility + leakage barrier + MINER_DEV exclusion: "
        f"{result['scan_summary']['candidates_eligible']}",
        "",
        "## 2. Exclusion counts by reason code",
        "",
    ]
    for code, count in result["scan_summary"]["exclusion_counts"].items():
        lines.append(f"- `{code}`: {count}")
    lines.append("")

    lines.append("## 3. Duplicate / related-change adjudication (R1/R2/R3)")
    lines.append("")
    adj = result["adjudication"]
    lines.append(f"- Total adjudication records: {len(adj)}")
    from collections import Counter

    rule_counts = Counter(r["rule"] for r in adj)
    for rule in ("R1_exact_proxy_set", "R2_shared_pr_reference", "R3_suspected_related"):
        lines.append(f"- `{rule}`: {rule_counts.get(rule, 0)}")
    lines.append("")
    lines.append("### R3 suspected-related pairs (overlapping proxy + intent Jaccard ≥ 0.5)")
    lines.append("")
    r3 = [r for r in adj if r["rule"] == "R3_suspected_related"]
    if not r3:
        lines.append("- None.")
    else:
        for rec in r3:
            lines.append(
                f"- Kept `{rec['kept_sha'][:12]}` vs excluded `{rec['excluded_sha'][:12]}` "
                f"(Jaccard {rec.get('intent_jaccard')}): {rec['rationale']}"
            )
    lines.append("")

    lines.append("## 4. Accepted count")
    lines.append("")
    lines.append(f"- **{result['selection_summary']['selected']}** scientific cases accepted")
    lines.append("")

    lines.append("## 5. Proxy-size distribution")
    lines.append("")
    for size, count in result["selection_summary"]["proxy_sizes"].items():
        lines.append(f"- proxy size {size}: {count}")
    lines.append("")

    lines.append("## 6. Change-type distribution (intent-derived conservative taxonomy)")
    lines.append("")
    for ctype, count in result["selection_summary"]["change_types"].items():
        lines.append(f"- `{ctype}`: {count}")
    lines.append("")

    lines.append("## 7. Temporal distribution (target commit year)")
    lines.append("")
    for year, count in result["selection_summary"]["years"].items():
        lines.append(f"- {year}: {count}")
    lines.append("")

    lines.append("## 8. Intent-source quality notes")
    lines.append("")
    lines.append(
        "- `intent_source` is the normalized commit message only (frozen M4A-1 "
        "choice); no PR body / linked-issue mining (would require network/API)."
    )
    lines.append(
        "- Scientific cases with `intent_mentions_changed_path=true` are "
        "INELIGIBLE (leakage barrier)."
    )
    lines.append(
        "- Intent quality is variable by era; the year-capped selection favors "
        "recent PR-referenced conventional commits while retaining temporal spread."
    )
    lines.append("")

    lines.append("## 9. Accepted-case table (parent / target / proxy size)")
    lines.append("")
    lines.append("| case_id | parent | target | year | proxy_size | change_type | split |")
    lines.append("|---|---|---|---|---|---|---|")
    for record in result["cases"]:
        lines.append(
            f"| {record['case_id']} | {record['parent_commit'][:12]} | "
            f"{record['target_commit'][:12]} | {record['target_commit_time'][:10]} | "
            f"{record['observed_change_set_proxy_count']} | {record['change_type']} | "
            f"{record['split']} |"
        )
    lines.append("")
    lines.append("## 10. Manual adjudication decisions (every decision with rationale)")
    lines.append("")
    lines.append(
        "- R1 (identical proxy set) and R2 (shared PR reference) are deterministic "
        "mechanical dedup rules; their per-commit records are persisted in "
        "`reports/real_commit_m4a2_adjudication.json`. R3 below required semantic "
        "adjudication:"
    )
    manual = [r for r in adj if r["rule"] == "R3_suspected_related"]
    if not manual:
        lines.append("- None (no R3 suspected-related pairs required manual adjudication).")
    else:
        for rec in manual:
            lines.append(
                f"- Kept `{rec['kept_sha'][:12]}` vs excluded `{rec['excluded_sha'][:12]}` "
                f"(Jaccard {rec.get('intent_jaccard')}): {rec['rationale']}"
            )
    lines.append("")
    lines.append("## 11. Scientific discipline")
    lines.append("")
    lines.append(
        "- The historical diff is an **OBSERVED CHANGE-SET PROXY**, never semantic "
        "ground truth; no P/R/V/H gold fabricated from Git diffs."
    )
    lines.append(
        "- All six MINER_DEV cases remain permanently excluded from scientific "
        "metrics (`miner_dev_target`)."
    )
    lines.append("- ZERO scientific LLM/API calls in this milestone.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=CACHE_DIR)
    parser.add_argument("--anchor", default=miner.DJANGOCMS_ANCHOR_COMMIT)
    parser.add_argument("--dataset-dir", type=Path, default=DATASET_DIR)
    parser.add_argument("--window", type=int, default=scientific.SCIENTIFIC_WINDOW)
    parser.add_argument("--year-cap", type=int, default=scientific.YEAR_CAP)
    parser.add_argument("--target-cases", type=int, default=scientific.TARGET_CASES)
    parser.add_argument("--split-seed", type=int, default=scientific.SPLIT_SEED)
    args = parser.parse_args()

    created_utc = datetime.now(UTC).isoformat()

    miner.acquire_cache(args.cache_dir, miner.REPOSITORY_URL_DJANGOCMS, args.anchor)
    miner_dev_targets = load_miner_dev_targets(args.dataset_dir)

    result = scientific.build_scientific_dataset(
        cache_dir=args.cache_dir,
        anchor=args.anchor,
        dataset_dir=args.dataset_dir,
        created_utc=created_utc,
        window=args.window,
        year_cap=args.year_cap,
        target_cases=args.target_cases,
        split_seed=args.split_seed,
        miner_dev_targets=miner_dev_targets,
    )

    if result["selection_summary"]["selected"] < 30:
        raise RuntimeError(
            f"fewer than 30 scientific cases selected after all filters: "
            f"got {result['selection_summary']['selected']}. Do NOT loosen rules."
        )

    ADJUDICATION_REPORT_PATH.write_text(
        render_adjudication_report(result, created_utc), encoding="utf-8"
    )
    # JSON-safe adjudication snapshot (exclude Path objects).
    snapshot_keys = (
        "scan_summary",
        "dedup_summary",
        "selection_summary",
        "split_summary",
        "case_ids",
        "cases",
        "adjudication",
    )
    adjudication_snapshot = {k: result[k] for k in snapshot_keys}
    ADJUDICATION_JSON_PATH.write_text(canonical_json(adjudication_snapshot), encoding="utf-8")

    print("=== RealCommitImpactDataset-v1 SCIENTIFIC build (M4A-2) ===")
    print(f"dataset_dir: {result['dataset_dir']}")
    print(f"manifest:    {result['manifest_path']}")
    print(f"split_freeze:{result['split_freeze_path']}")
    print(f"scan:        {result['scan_summary']}")
    print(f"dedup:       {result['dedup_summary']}")
    print(f"selection:   {result['selection_summary']}")
    print(f"splits:      {result['split_summary']}")
    print(f"adjudication: {ADJUDICATION_REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
