#!/usr/bin/env python3
"""POST-STUDY closure audit (Section 18). Verifies the corrected documentation
against raw evidence. Zero scientific calls.

Checks:
1. 19-vs-20 truncation issue resolved (19 confirmed from raw evidence)
2. valid/failed arm counts (25/5 Agent, 6/24 ImpactPlan; 31/29 total)
3. valid-only vs all-cell separation in reports
4. cost wording (recorded $0.264148 + missing-cost caveat)
5. output-budget limitation documented (8x1024 vs 1x4096)
6. Git provenance (live HEAD, parity, scientific-results commit)
7. no raw scientific evidence modification (hashes unchanged)
"""

from __future__ import annotations
import json
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
STUDY_DIR = PROJECT_DIR / "reports" / "scientific-stagec-djangocms-study-01"


def git(*a: str) -> str:
    return subprocess.run(["git", *a], cwd=PROJECT_DIR, capture_output=True, text=True).stdout.strip()


def load(name: str):
    return json.loads((STUDY_DIR / name).read_text(encoding="utf-8"))


def main() -> int:
    rc = load("closure_recompute.json")
    items: list[dict] = []

    # 1. Truncation count
    trunc = rc["failure_taxonomy"].get("completion_truncation_4096_cap", {})
    items.append({
        "item": "truncation_count_is_19",
        "ok": trunc.get("count") == 19,
        "detail": f"count={trunc.get('count')} (raw evidence confirms 19; was wrongly 20)",
    })
    items.append({
        "item": "truncations_have_length_finish_and_4096_completion",
        "ok": all(t["finish_reason"] == "length" and t["completion_tokens"] == 4096 for t in rc["truncation_raw_evidence"]),
        "detail": f"{len(rc['truncation_raw_evidence'])} truncation records, all finish_reason=length & completion_tokens=4096",
    })

    # 2. Arm valid/failed counts
    a = rc["arm_counts"]
    items.append({
        "item": "arm_counts_agent_25_5",
        "ok": a["iterative_repository_agent"]["valid"] == 25 and a["iterative_repository_agent"]["failed"] == 5,
        "detail": a["iterative_repository_agent"],
    })
    items.append({
        "item": "arm_counts_impactplan_6_24",
        "ok": a["impact_plan"]["valid"] == 6 and a["impact_plan"]["failed"] == 24,
        "detail": a["impact_plan"],
    })
    items.append({
        "item": "total_31_valid_29_failed",
        "ok": rc["valid"] == 31 and rc["failed"] == 29,
        "detail": {"valid": rc["valid"], "failed": rc["failed"]},
    })

    # 3. Valid-only vs all-cell separation in reports
    main_md = (PROJECT_DIR / "reports" / "FINAL_BENCHMARK_RESULTS.md").read_text(encoding="utf-8")
    val_md = (PROJECT_DIR / "reports" / "BENCHMARK_VALIDITY_AND_LIMITATIONS.md").read_text(encoding="utf-8")
    items.append({
        "item": "main_report_has_valid_headline_and_all_cell_tables",
        "ok": "ALL-CELL OPERATIONAL TABLE" in main_md and "VALID-RUN MICRO-AGGREGATION" in main_md,
        "detail": "sections present",
    })
    items.append({
        "item": "valid_only_vs_all_cell_not_confused",
        "ok": "Do not confuse this all-cell resource table with valid-only correctness" in main_md,
        "detail": "explicit separation statement present",
    })

    # 4. Cost wording
    items.append({
        "item": "cost_wording_recorded_not_exact_total",
        "ok": "Recorded API cost across persisted study records was $0.264148" in main_md
        and "Actual spend is slightly higher" in main_md,
        "detail": "recorded + missing-cost caveat wording present",
    })
    items.append({
        "item": "cost_ceiling_status",
        "ok": rc["total_recorded_cost_usd"] <= 0.50,
        "detail": f"recorded ${rc['total_recorded_cost_usd']:.6f} <= $0.50",
    })

    # 5. Output-budget limitation
    items.append({
        "item": "output_budget_asymmetry_documented",
        "ok": "8 × 1024 = 8192 tokens" in main_md and "4096 tokens in one structured response" in main_md
        and "confound representational scalability with completion-budget sufficiency" in val_md,
        "detail": "both reports document 8x1024 vs 1x4096",
    })

    # 6. Git provenance
    head = git("rev-parse", "HEAD")
    remote = git("rev-parse", "origin/research/djangocms-external-validity-prep-01")
    items.append({
        "item": "git_live_head_parity",
        "ok": head == remote and bool(head),
        "detail": {"head": head, "remote": remote},
    })
    items.append({
        "item": "scientific_results_commit_identified",
        "ok": "0c110bb1e42788ea68f0c23e70a729e695153a46" in (STUDY_DIR / "STOP_REPORT.md").read_text(encoding="utf-8"),
        "detail": "frozen scientific-results commit 0c110bb documented (manifest + 60 raw records)",
    })

    # 7. Raw evidence immutability
    baseline = load("raw_evidence_hashes.json")
    import hashlib
    import sys
    sys.path.insert(0, str(PROJECT_DIR / "src"))
    from benchmark.external_validity import study_runtime as wiring

    def sha(p: Path) -> str:
        return hashlib.sha256(p.read_bytes()).hexdigest()

    current = {}
    current["manifest_60.json"] = sha(STUDY_DIR / "manifest_60.json")
    current["run_records.jsonl"] = sha(STUDY_DIR / "run_records.jsonl")
    current["hidden_gold"] = sha(wiring.HIDDEN_GOLD_PATH)
    current["candidate_universe"] = sha(wiring.CANDIDATE_UNIVERSE_PATH)
    current["dependency_graph"] = sha(PROJECT_DIR / "benchmark_data" / "external_validity" / "djangocms_5_0_0_dependency_graph.json")
    for sid in sorted(wiring.final_scenario_ids()):
        current[f"scenario_{sid}"] = sha(wiring.VISIBLE_DRAFTS_DIR / f"{sid}.yaml")
    for rf in sorted((STUDY_DIR / "runs").glob("*.json")):
        current[f"run:{rf.stem}"] = sha(rf)
    mismatches = [k for k in baseline if baseline.get(k) != current.get(k)]
    items.append({
        "item": "raw_scientific_evidence_immutable",
        "ok": not mismatches,
        "detail": {"baseline_keys": len(baseline), "mismatches": mismatches},
    })

    result = {
        "audit": "POST_STUDY_CLOSURE_AUDIT",
        "zero_scientific_calls": True,
        "passed": all(i["ok"] for i in items),
        "items": items,
        "audited_at": __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat(),
    }
    out = STUDY_DIR / "closure_audit.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    for i in items:
        print(f"[{'PASS' if i['ok'] else 'FAIL'}] {i['item']} -> {i['detail']}")
    print(f"AUDIT_PASSED={result['passed']}")
    print(f"persisted={out}")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())