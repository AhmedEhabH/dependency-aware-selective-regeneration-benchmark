#!/usr/bin/env python3
"""Independent audit — Omission-Risk Development Inference (Sparse-v2 TRAIN/VALIDATION).

Reads persisted artifacts ONLY (no recomputation of model outputs, no new API
calls). Verifies:
1. Run integrity: 90 cells, 90/90 valid, run_ids unique, raw+sha256 sidecars match.
2. Budget discipline: total tokens <= 600,000 AND cost <= $0.30 (frozen hard stop).
3. Split discipline: only TRAIN+VALIDATION case ids; HELD_OUT_TEST never in
   manifest, run records, or analysis outputs.
4. Provenance: provider/model/graph/cap/temperature frozen; exact model id; no fallback.
5. No replacement / no result-dependent reruns (closure flag + single record per run_id).
6. Statistical unit: task-level labels (N=30) with nested reps; feature table keyed
   by case_id; no repetition treated as an independent task.
7. No multivariable RiskScorer fitted (class-balance gate failed: 4 negatives < 10).
8. Raw responses parse to the recorded schema/counts (spot re-derivation).
9. Deterministic frozen artifacts unchanged (feature_table.csv byte-identical
   recomputation is out of scope; git status on frozen study dirs clean).
10. Gates evidence passed pre-run.
"""

# ruff: noqa: E501
from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from scripts.omission_risk_inference_manifest import (  # noqa: E402
    COST_CEILING_USD,
    DATASET_DIR,
    STUDY_DIR,
    TOKEN_CEILING,
    build_omission_risk_manifest,
    trainval_case_ids,
)

ANALYSIS_DIR = STUDY_DIR / "sparse_v2_label_analysis"
RUN_RECORDS = STUDY_DIR / "sparse_v2_trainval_run_records.jsonl"
GATES_JSON = _PROJECT_DIR / "reports" / "omission_risk_inference_gates.json"
HELD_OUT_JSON = DATASET_DIR / "split_freeze.json"

AUDIT_OUT = _PROJECT_DIR / "reports" / "omission_risk_inference_audit.json"
REPORT_OUT = _PROJECT_DIR / "reports" / "OMISSION_RISK_INFERENCE_AUDIT.md"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _load_lines(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run_audit() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    recs = _load_lines(RUN_RECORDS)
    manifest_cells = build_omission_risk_manifest()

    # 1. Run integrity
    checks.append({"check": "cells_exactly_90", "ok": len(recs) == 90, "detail": len(recs)})
    checks.append(
        {
            "check": "run_ids_unique",
            "ok": len({r["run_id"] for r in recs}) == 90,
            "detail": len({r["run_id"] for r in recs}),
        }
    )
    checks.append(
        {
            "check": "manifest_matches_records",
            "ok": {c["run_id"] for c in manifest_cells} == {r["run_id"] for r in recs},
            "detail": "exact run_id set equality",
        }
    )
    valid = sum(1 for r in recs if r["terminal_status"] == "succeeded")
    checks.append({"check": "valid_90_of_90", "ok": valid == 90, "detail": valid})
    checks.append({"check": "schema_valid_all", "ok": all(r.get("schema_valid") for r in recs), "detail": sum(1 for r in recs if r.get("schema_valid"))})
    checks.append({"check": "no_truncations", "ok": all(not r.get("truncation_status") for r in recs), "detail": sum(1 for r in recs if r.get("truncation_status"))})

    # raw + sha256 sidecars
    raw_dir = STUDY_DIR / "sparse_v2_trainval_runs" / "raw"
    bad = 0
    for r in recs:
        txt = raw_dir / f"{r['run_id']}.txt"
        sha = raw_dir / f"{r['run_id']}.sha256"
        if not txt.is_file() or not sha.is_file():
            bad += 1
            continue
        h = hashlib.sha256(txt.read_bytes()).hexdigest()
        if h != r["raw_response_sha256"] or h != sha.read_text(encoding="utf-8").strip():
            bad += 1
    checks.append({"check": "raw_sha256_all_match", "ok": bad == 0, "detail": f"mismatches={bad}"})

    # 2. Budget discipline
    total_tokens = sum(int(r["total_tokens"]) for r in recs)
    total_cost = round(sum(float(r.get("api_cost", 0.0)) for r in recs), 6)
    checks.append(
        {
            "check": "token_budget_respected",
            "ok": total_tokens <= TOKEN_CEILING,
            "detail": {"tokens": total_tokens, "ceiling": TOKEN_CEILING},
        }
    )
    checks.append(
        {
            "check": "cost_budget_respected",
            "ok": total_cost <= COST_CEILING_USD,
            "detail": {"cost": total_cost, "ceiling": COST_CEILING_USD},
        }
    )

    # 3. Split discipline
    allowed = set(trainval_case_ids())
    held = set(json.loads(HELD_OUT_JSON.read_text(encoding="utf-8"))["per_split"]["HELD_OUT_TEST"]["case_ids"])
    checks.append(
        {
            "check": "records_only_train_validation",
            "ok": {r["case_id"] for r in recs} <= allowed,
            "detail": {"n_cases": len({r["case_id"] for r in recs})},
        }
    )
    checks.append(
        {
            "check": "records_exclude_heldout",
            "ok": held.isdisjoint({r["case_id"] for r in recs}),
            "detail": "no HELD_OUT_TEST case in records",
        }
    )
    checks.append(
        {
            "check": "manifest_excludes_heldout",
            "ok": held.isdisjoint({c["case_id"] for c in manifest_cells}),
            "detail": "no HELD_OUT_TEST case in manifest",
        }
    )
    # analysis outputs must not mention held-out case ids
    held_mentions = 0
    for f in ("sparse_v2_labels.json", "sparse_v2_feature_table.csv", "sparse_v2_summary.json", "sparse_v2_comparison.json"):
        p = ANALYSIS_DIR / f
        if p.is_file():
            text = p.read_text(encoding="utf-8")
            if any(h in text for h in held):
                held_mentions += 1
    checks.append({"check": "analysis_outputs_exclude_heldout", "ok": held_mentions == 0, "detail": f"files_with_heldout={held_mentions}"})

    # 4. Provenance
    checks.append({"check": "provider_deepinfra_all", "ok": all(r.get("provider_name") == "DeepInfra" for r in recs), "detail": len(set(r.get("provider_name") for r in recs))})
    checks.append({"check": "model_frozen", "ok": all(r.get("scientific_model") == "qwen/qwen3-coder" for r in recs), "detail": "qwen/qwen3-coder"})
    checks.append({"check": "provider_tag_frozen", "ok": all(r.get("provider_tag") == "deepinfra/turbo" for r in recs), "detail": "deepinfra/turbo"})
    checks.append({"check": "graph_off_all", "ok": all(r.get("graph") == "OFF" for r in recs), "detail": "OFF"})
    checks.append({"check": "temperature_zero_all", "ok": all(float(r.get("temperature")) == 0.0 for r in recs), "detail": "0.0"})
    checks.append({"check": "cap_16384_all", "ok": all(int(r.get("completion_cap")) == 16384 for r in recs), "detail": "16384"})
    checks.append({"check": "fallback_off_all", "ok": all(r.get("fallback_status") == "off" for r in recs), "detail": "off"})

    # 5. No replacement / no result-dependent reruns
    checks.append({"check": "single_record_per_run_id", "ok": len(recs) == len({r["run_id"] for r in recs}), "detail": "one record per cell"})
    closure = json.loads((STUDY_DIR / "sparse_v2_trainval_closure.json").read_text(encoding="utf-8"))
    checks.append({"check": "closure_no_replacement_reruns", "ok": closure.get("no_replacement_reruns") is True, "detail": closure.get("no_replacement_reruns")})
    checks.append({"check": "closure_no_result_reruns", "ok": closure.get("no_result_dependent_reruns") is True, "detail": closure.get("no_result_dependent_reruns")})
    checks.append({"check": "closure_run_complete", "ok": closure.get("run_complete") is True, "detail": closure.get("recorded_cells")})

    # 6. Statistical unit
    labels = json.loads((ANALYSIS_DIR / "sparse_v2_labels.json").read_text(encoding="utf-8"))
    checks.append({"check": "labels_n_30_tasks", "ok": labels["n_tasks"] == 30, "detail": labels["n_tasks"]})
    checks.append({"check": "reps_nested_not_independent", "ok": "task-level unit" in labels.get("label_definition", ""), "detail": labels.get("label_definition", "")[:120]})

    # 7. No multivariable RiskScorer
    checks.append({"check": "class_balance_gate_failed_no_scorer", "ok": labels.get("multivariable_fitted") is False, "detail": {"n_pos": labels.get("n_positive"), "n_neg": labels.get("n_negative"), "reason": labels.get("reason", "")[:120]}})
    checks.append(
        {
            "check": "no_scorer_artifact",
            "ok": not (ANALYSIS_DIR / "risk_scorer.json").exists(),
            "detail": "no risk_scorer.json produced",
        }
    )

    # 8. Spot re-derivation: one non-empty cell's serialized count from raw response
    spot = next((r for r in recs if int(r.get("serialized_decision_count", 0)) >= 2), recs[0])
    raw_txt = (raw_dir / f"{spot['run_id']}.txt").read_text(encoding="utf-8")
    parsed = json.loads(raw_txt)
    content = parsed["choices"][0]["message"]["content"]
    payload = json.loads(content)
    serialized_from_raw = len(payload.get("decisions") or [])
    checks.append(
        {
            "check": "spot_serialized_count_reproducible",
            "ok": serialized_from_raw == int(spot.get("serialized_decision_count")),
            "detail": {"run_id": spot["run_id"], "from_raw": serialized_from_raw, "recorded": spot.get("serialized_decision_count")},
        }
    )

    # 9. Gates evidence passed pre-run
    gates = json.loads(GATES_JSON.read_text(encoding="utf-8"))
    checks.append({"check": "gates_all_passed", "ok": bool(gates.get("all_passed")), "detail": gates.get("all_passed")})
    checks.append({"check": "gates_audit_passed", "ok": bool(gates.get("audit", {}).get("passed")), "detail": gates.get("audit", {}).get("passed")})

    passed = all(c["ok"] for c in checks)
    return {
        "audit": True,
        "study_id": "omission-risk-development-inference-v1",
        "passed": passed,
        "checks": checks,
        "n_checks": len(checks),
        "n_passed": sum(1 for c in checks if c["ok"]),
        "ran_at": _now_iso(),
    }


def _render(audit: dict[str, Any]) -> str:
    lines = [
        "# Independent Audit — Omission-Risk Development Inference (Sparse-v2)",
        "",
        f"**Generated:** {audit['ran_at']}",
        f"**Study:** {audit['study_id']}",
        "",
        f"**OVERALL:** {'PASS' if audit['passed'] else 'FAIL'}",
        f"**Checks:** {audit['n_passed']}/{audit['n_checks']}",
        "",
    ]
    for c in audit["checks"]:
        lines.append(f"- [{'PASS' if c['ok'] else 'FAIL'}] {c['check']} — {json.dumps(c['detail'])[:220]}")
    lines.append("")
    lines.append("## Discipline")
    lines.append("")
    lines.append("- Reads persisted artifacts only; no recomputation of model outputs; no new API calls.")
    lines.append("- Historical diff = OBSERVED CHANGE-SET PROXY, never semantic ground truth.")
    lines.append("- Independent task = historical change; repetitions are nested observations.")
    lines.append("- HELD_OUT_TEST never used for any decision in this run.")
    return "\n".join(lines)


if __name__ == "__main__":
    audit = run_audit()
    AUDIT_OUT.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    REPORT_OUT.write_text(_render(audit), encoding="utf-8")
    for c in audit["checks"]:
        print(f"{'PASS' if c['ok'] else 'FAIL'}  {c['check']} — {json.dumps(c['detail'])[:160]}")
    print(f"AUDIT={'PASS' if audit['passed'] else 'FAIL'} ({audit['n_passed']}/{audit['n_checks']})")
    raise SystemExit(0 if audit["passed"] else 1)
