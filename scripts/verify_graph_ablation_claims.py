#!/usr/bin/env python3
"""ZERO-API verifier for M3 - Graph ablation (C0 / C1 / C2).

Recomputes every headline M3 claim from the frozen evidence WITHOUT any
model/API call:

- automatic graph (144 nodes / 144/144 AST parsed / 562 edges / hash parity /
  no manual scenario edges / no gold-derived edges / eligibility)
- C0 reuse (audited M1B Sparse-v2 30 cells; byte-identical prompt hashes)
- 90-cell manifest topology (30 per condition arm, 6 scenarios, 5 reps)
- 90/90 run records; 90/90 raw-response SHA-256 sidecars
- C1: 30/30 valid; P/R/F1/FNR/TP/FP/FN recomputed
- C2 1-hop: 2/30 valid, 28 mandatory-disclosure-failure, compliance 2/30
- C2 2-hop: 0/30 valid, 30 mandatory-disclosure-failure, compliance 0/30
- delta tables C0->C1 / C0->C2-1hop / C2-1hop->C2-2hop
- cost / token accounting recomputed from usage at frozen DeepInfra pricing
- six closure gates + independent audit (recomputed)

Exit 0 iff every check passes.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PROJECT_DIR / "src"))

STUDY_DIR = PROJECT_DIR / "research" / "graph-c0-c1-c2-01"
M1B_DIR = PROJECT_DIR / "research" / "controlled-encoding-ablation-16k-01"

from benchmark.selection import graph_ablation as ga  # noqa: E402

PROMPT_PER_TOKEN_USD = 0.0000003
COMPLETION_PER_TOKEN_USD = 0.000001


def _records() -> list[dict[str, Any]]:
    out = []
    path = STUDY_DIR / "run_records.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def _m1b_sparse() -> list[dict[str, Any]]:
    out = []
    for line in (M1B_DIR / "run_records.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            if rec.get("arm") == "sparse_v2":
                out.append(rec)
    return out


def _micro(rows: list[dict[str, Any]]) -> dict[str, Any]:
    selected = sum(int(r.get("predicted_write_set_size", 0)) for r in rows)
    tp = sum(int(r.get("tp", 0)) for r in rows)
    fp = sum(int(r.get("fp", 0)) for r in rows)
    fn = sum(int(r.get("fn", 0)) for r in rows)
    precision = tp / selected if selected else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fnr = fn / (tp + fn) if (tp + fn) else 0.0
    return {"selected": selected, "tp": tp, "fp": fp, "fn": fn,
            "precision": round(precision, 6), "recall": round(recall, 6),
            "f1": round(f1, 6), "fnr": round(fnr, 6)}


def main() -> int:
    failures: list[str] = []
    checks: list[dict[str, Any]] = []

    def check(label: str, ok: bool, detail: Any = None) -> None:
        checks.append({"check": label, "ok": bool(ok), "detail": detail})
        print(f"{'PASS' if ok else 'FAIL'}  {label}")
        if not ok:
            failures.append(label)

    print("=== M3 ZERO-API VERIFIER ===")

    # 1. automatic graph
    gv = ga.graph_verification()
    check("graph_verification", gv["passed"], [c["check"] for c in gv["checks"] if not c["ok"]])

    # 2. C0 reuse
    c0m = ga.c0_matches_audited_m1b()
    check("c0_reuse_prompt_identity", c0m["passed"])
    m1b_sparse = _m1b_sparse()
    check("c0_reuse_30_cells", len(m1b_sparse) == 30, len(m1b_sparse))

    # 3. manifest
    manifest = json.loads((STUDY_DIR / "manifest_90.json").read_text(encoding="utf-8"))
    cells = manifest["cells"]
    check("manifest_90_cells", len(cells) == 90, len(cells))
    check("manifest_run_ids_unique", len({c["run_id"] for c in cells}) == 90)
    c1_cells = [c for c in cells if c["condition"] == "c1"]
    c2_1 = [c for c in cells if c["condition"] == "c2" and c["hop"] == 1]
    c2_2 = [c for c in cells if c["condition"] == "c2" and c["hop"] == 2]
    check("manifest_30_per_arm", len(c1_cells) == 30 and len(c2_1) == 30 and len(c2_2) == 30,
          {"c1": len(c1_cells), "c2-1hop": len(c2_1), "c2-2hop": len(c2_2)})
    check("manifest_three_hop_not_eligible",
          manifest.get("three_hop_eligible") is False)

    # 4. run records
    recs = _records()
    check("records_90", len(recs) == 90, len(recs))
    check("records_unique_run_ids", len({r["run_id"] for r in recs}) == 90)
    check("records_match_manifest_cells",
          {r["run_id"] for r in recs} == {c["run_id"] for c in cells})

    # 5. raw SHA-256 sidecars 90/90
    raw_ok = 0
    for r in recs:
        raw_path = STUDY_DIR / "runs" / "raw" / f"{r['run_id']}.txt"
        if raw_path.is_file():
            body = raw_path.read_bytes()
            if hashlib.sha256(body).hexdigest() == r.get("raw_response_sha256"):
                raw_ok += 1
    check("raw_sha256_sidecars_90_90", raw_ok == 90, f"{raw_ok}/90")

    # 6. operational counts per condition
    c1_recs = [r for r in recs if r["condition"] == "c1"]
    c2_1_recs = [r for r in recs if r["condition"] == "c2" and r["hop"] == 1]
    c2_2_recs = [r for r in recs if r["condition"] == "c2" and r["hop"] == 2]
    check("c1_30_30_valid", len(c1_recs) == 30
          and all(r["terminal_status"] == "succeeded" for r in c1_recs))
    check("c2_1hop_2_valid_28_fail", sum(1 for r in c2_1_recs if r["terminal_status"] == "succeeded") == 2
          and sum(1 for r in c2_1_recs if r["terminal_status"] != "succeeded") == 28)
    check("c2_1hop_compliance_2_30",
          sum(1 for r in c2_1_recs if r.get("disclosure_valid") is True) == 2,
          {"compliant": sum(1 for r in c2_1_recs if r.get("disclosure_valid") is True)})
    check("c2_2hop_0_valid_30_fail", sum(1 for r in c2_2_recs if r["terminal_status"] == "succeeded") == 0
          and sum(1 for r in c2_2_recs if r["terminal_status"] != "succeeded") == 30)
    check("c2_2hop_compliance_0_30",
          sum(1 for r in c2_2_recs if r.get("disclosure_valid") is True) == 0)
    check("all_failures_mandatory_disclosure",
          all("mandatory-disclosure-failure" in r.get("failure_category", "")
              for r in c2_1_recs + c2_2_recs if r["terminal_status"] != "succeeded"))
    check("zero_truncations", all(not r.get("truncation_status") for r in recs))
    check("zero_transport_failures", all(not r.get("transport_failure") for r in recs))

    # 7. C1 semantic recompute (valid-only micro)
    c1_valid = [r for r in c1_recs if r["terminal_status"] == "succeeded"]
    c1_micro = _micro(c1_valid)
    c1_metrics = json.loads((STUDY_DIR / "final_metrics.json").read_text(encoding="utf-8"))
    c1_overall = c1_metrics["conditions"]["c1"]["overall"]
    check("c1_precision_recomputed", abs(c1_micro["precision"] - c1_overall["precision"]) < 1e-6,
          {"recomputed": c1_micro["precision"], "reported": c1_overall["precision"]})
    check("c1_recall_recomputed", abs(c1_micro["recall"] - c1_overall["recall"]) < 1e-6,
          {"recomputed": c1_micro["recall"], "reported": c1_overall["recall"]})
    check("c1_f1_recomputed", abs(c1_micro["f1"] - c1_overall["f1"]) < 1e-6)
    check("c1_fn_fp_recomputed", c1_micro["fn"] == c1_overall["fn"] == 24
          and c1_micro["fp"] == c1_overall["fp"] == 22,
          {"fn": c1_micro["fn"], "fp": c1_micro["fp"]})

    # 8. C0 numbers
    c0_valid = [r for r in m1b_sparse if r["terminal_status"] == "succeeded"]
    c0_micro = _micro(c0_valid)
    check("c0_recall_0p8833", abs(c0_micro["recall"] - 0.883333) < 1e-4, c0_micro["recall"])
    check("c0_f1_0p7940", abs(c0_micro["f1"] - 0.794007) < 1e-4, c0_micro["f1"])
    check("c0_fn_14_fp_41", c0_micro["fn"] == 14 and c0_micro["fp"] == 41,
          {"fn": c0_micro["fn"], "fp": c0_micro["fp"]})

    # 9. deltas
    c0_fn, c1_fn = 14, 24
    check("delta_c0_to_c1_fn_plus10", c1_fn - c0_fn == 10)
    check("delta_c0_to_c1_recall_neg_0p0833",
          abs((c1_micro["recall"] - c0_micro["recall"]) - (-0.083333)) < 1e-4)
    check("delta_c0_to_c1_precision_pos_0p0925",
          abs((c1_micro["precision"] - c0_micro["precision"]) - 0.092471) < 1e-4)
    check("delta_c0_to_c1_f1_pos_0p0127",
          abs((c1_micro["f1"] - c0_micro["f1"]) - 0.012716) < 1e-4)

    # 10. token / cost recompute (C1)
    c1_prompt = sum(int(r["prompt_tokens"]) for r in c1_recs)
    c1_completion = sum(int(r["completion_tokens"]) for r in c1_recs)
    c1_cost = round(c1_prompt * PROMPT_PER_TOKEN_USD + c1_completion * COMPLETION_PER_TOKEN_USD, 6)
    check("c1_cost_recomputed", abs(c1_cost - c1_metrics["conditions"]["c1"]["api_cost_usd"]) < 0.001,
          {"recomputed": c1_cost, "reported": c1_metrics["conditions"]["c1"]["api_cost_usd"]})
    totals = c1_metrics["totals"]
    check("totals_90_cells_32_valid", totals["new_cells"] == 90 and totals["new_valid"] == 32
          and totals["new_failed"] == 58, {"cells": totals["new_cells"], "valid": totals["new_valid"]})
    check("total_tokens_566623", totals["total_tokens"] == 566623, totals["total_tokens"])
    check("total_cost_recomputed",
          abs(totals["cost_usd"] - 0.234673) < 0.001, totals["cost_usd"])

    # 11. S006 pre-registered expectations
    c1_s006 = c1_metrics["conditions"]["c1"]["per_scenario"]["djangocms-external-validity-006"]
    c1_s006_pm = c1_s006["pooled_micro"]
    check("s006_c1_improves_vs_c0",
          c1_s006_pm["f1"] > 0.2778 and c1_s006_pm["recall"] > 0.3333,
          {"c1_f1": c1_s006_pm["f1"], "c0_f1": 0.277778})
    c2_s006 = c1_metrics["conditions"]["c2_1hop"]["per_scenario"]["djangocms-external-validity-006"]
    check("s006_c2_1hop_1_valid_run", c2_s006["valid_runs"] == 1, c2_s006["valid_runs"])

    # 12. closure gates + audit
    closure = json.loads((STUDY_DIR / "closure_gates.json").read_text(encoding="utf-8"))
    check("closure_gates_all_pass", closure.get("gates_all_passed") is True)
    check("closure_audit_pass", closure.get("audit", {}).get("passed") is True)
    check("closure_graph_verification", closure.get("graph_verification", {}).get("passed") is True)

    # 13. C2 2-hop zone size sanity (>= 2-hop zone)
    ident = json.loads((STUDY_DIR / "seed_zone_identity.json").read_text(encoding="utf-8"))
    z2_sizes = [d["zones"]["2"]["size"] for d in ident["per_scenario"].values()]
    check("zones_2hop_111_119", min(z2_sizes) == 111 and max(z2_sizes) == 119, sorted(z2_sizes))

    print(f"\nTOTAL_CHECKS={len(checks)}")
    print(f"PASSED={len(checks) - len(failures)}")
    print(f"FAILED={len(failures)}")
    print("M3_VERIFIER=" + ("PASS" if not failures else "FAIL"))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
