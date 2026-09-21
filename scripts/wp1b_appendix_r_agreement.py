#!/usr/bin/env python3
"""Compare OpenCode's independent re-derivation against the external reference
evidence JSON and emit the AGREE/DISAGREE record required by the contract
(APPENDIX R re-derivation; tolerance checks).

Run from the repository root:
    python scripts/wp1b_appendix_r_agreement.py <ref_json> <mine_json> [out_json]
    - <ref_json>   the external reference evidence JSON (NOT committed; lives
                   outside the repository)
    - <mine_json>  the output of scripts/wp1b_appendix_r_rederivation.py
    - out_json     default: printed to stdout and written to <mine_json>.agreement.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if len(sys.argv) < 3:
    raise SystemExit("usage: wp1b_appendix_r_agreement.py <ref_json> <mine_json> [out_json]")
REF = Path(sys.argv[1])
MY = Path(sys.argv[2])
OUT = Path(sys.argv[3]) if len(sys.argv) > 3 else MY.with_suffix(MY.suffix + ".agreement.json")

ref = json.loads(REF.read_text(encoding="utf-8"))
my = json.loads(MY.read_text(encoding="utf-8"))

record: dict = {"artifact": "wp1b_preflight_appendix_r_agreement", "api_calls": 0, "entries": []}


def agree(key: str, mine: object, theirs: object, tol: float | None = None) -> bool:
    del key  # key is used for the record, not the comparison
    if isinstance(mine, (int, float)) and isinstance(theirs, (int, float)):
        if tol is None:
            return mine == theirs
        return abs(float(mine) - float(theirs)) <= tol
    return mine == theirs


def add(key: str, mine: object, theirs: object, *, tol: float | None = None,
        note: str = "") -> None:
    ok = agree(key, mine, theirs, tol)
    record["entries"].append({
        "key": key, "mine": mine, "reference": theirs, "tolerance": tol,
        "status": "AGREE" if ok else "DISAGREE", "note": note,
    })
    return ok


# ---- R-A pooled micro-F1 (exact) ----
add("R-A.reserve300.sip_f1", my["A_pooled_f1"]["reserve300"]["sip_micro_f1"],
    ref["A_pooled_f1"]["reserve300"]["sip_micro_f1"])
add("R-A.reserve300.rmcss_f1", my["A_pooled_f1"]["reserve300"]["rmcss_micro_f1"],
    ref["A_pooled_f1"]["reserve300"]["rmcss_micro_f1"])
add("R-A.reserve300.delta", my["A_pooled_f1"]["reserve300"]["delta"],
    ref["A_pooled_f1"]["reserve300"]["delta"])
add("R-A.main50.sip_f1", my["A_pooled_f1"]["main50"]["sip_micro_f1"],
    ref["A_pooled_f1"]["main50"]["sip_micro_f1"])
add("R-A.main50.rmcss_f1", my["A_pooled_f1"]["main50"]["rmcss_micro_f1"],
    ref["A_pooled_f1"]["main50"]["rmcss_micro_f1"])
add("R-A.main50.delta", my["A_pooled_f1"]["main50"]["delta"],
    ref["A_pooled_f1"]["main50"]["delta"])

# ---- R-B RM-CSS reproduction ----
add("R-B.mismatch_coef_order", my["B_rmcss_reproduction"]["mismatch_tasks_coef_order_cont_plus_boolean"],
    ref["B_rmcss_reproduction"]["mismatch_tasks_coef_order_continuous_plus_boolean"])
add("R-B.mismatch_feature_names_order", my["B_rmcss_reproduction"]["mismatch_tasks_if_feature_names_order_used"],
    ref["B_rmcss_reproduction"]["mismatch_tasks_if_feature_names_order_used"])

# ---- R-C power ----
add("R-C.se_rmcss_main50", my["C_power"]["main50_se_rmcss_micro_f1"],
    ref["C_power"]["main50_se_rmcss_micro_f1"], tol=1e-9)
add("R-C.se_rm_minus_sip_main50", my["C_power"]["main50_se_rm_minus_sip"],
    ref["C_power"]["main50_se_rm_minus_sip"], tol=1e-9)
for n in ("50", "150", "297"):
    for lab in ("high_correlation(RM-vs-SIP-like)", "mid", "independent_methods"):
        mine = my["C_power"]["table"][f"n={n}"][lab]
        theirs = ref["C_power"]["table"][f"n={n}"][lab]
        for sub in ("se_diff", "point_estimate_needed_for_LCB_above_-0.05"):
            add(f"R-C.n{n}.{lab}.{sub}", mine[sub], theirs[sub], tol=1e-6)
        for D in ("-0.03", "+0.00", "+0.03"):
            k = f"power_NI_margin0.05_trueD={D}"
            add(f"R-C.n{n}.{lab}.{k}", mine[k], theirs[k], tol=1e-6)

# ---- R-D budget ----
tol15 = 0.15  # +-15% tolerance per contract B1.7
add("R-D.universe_mean", my["D_budget"]["universe_size_mean_53"],
    ref["D_budget"]["universe_size_mean_53"], tol=tol15 * 810)
add("R-D.universe_min_max", my["D_budget"]["universe_size_min_max_53"],
    ref["D_budget"]["universe_size_min_max_53"])
add("R-D.prompt_tokens_mean", my["D_budget"]["editable_paths_prompt_tokens_mean_53"],
    ref["D_budget"]["editable_paths_prompt_tokens_mean_53"], tol=tol15 * 11190)
add("R-D.underestimate_factor", my["D_budget"]["underestimate_factor_prompt"],
    ref["D_budget"]["underestimate_factor_prompt"], tol=0.2)
for name in ("worst_case_cap1024_53_tasks", "worst_case_cap1024_calibration3",
             "worst_case_cap1024_main297"):
    for sub in ("prompt_tokens", "completion_tokens", "usd_base"):
        add(f"R-D.{name}.{sub}", my["D_budget"][name][sub], ref["D_budget"][name][sub],
            tol=0.02 * ref["D_budget"][name][sub])
add("R-D.variance_usd_base", my["D_budget"]["worst_case_cap1024_variance_15x3"]["usd_base"],
    ref["D_budget"]["worst_case_cap1024_variance_15x3"]["usd_base"], tol=1e-6)

# ---- R-E exploratory headroom ----
for pop in ("reserve300", "main50"):
    m, r = my["E_headroom_exploratory"][pop], ref["E_headroom_exploratory"][pop]
    for k in ("gold_total", "gold_in_pool", "rmcss_tp", "rmcss_fp",
              "fn_in_pool_decision_errors", "fn_out_of_pool_recall_errors"):
        add(f"R-E.{pop}.{k}", m[k], r[k])
    for k in ("pool_coverage", "pool_size_mean", "rmcss_micro_f1", "oracle_keepdrop_over_pool_f1"):
        add(f"R-E.{pop}.{k}", m[k], r[k], tol=1e-9)
    for band in ("[0.1,0.35)", "[0.05,0.35)"):
        add(f"R-E.{pop}.{band}.files_per_task", m["bands"][band]["files_per_task"],
            r["bands"][band]["files_per_task"], tol=1e-9)
        add(f"R-E.{pop}.{band}.gold_in_band", m["bands"][band]["gold_in_band"],
            r["bands"][band]["gold_in_band"])
        for se, sp in ((1.0, 1.0), (0.9, 0.9), (0.8, 0.8), (0.7, 0.7), (0.6, 0.6), (0.6, 0.9), (0.8, 0.7)):
            k = f"sens{se}_spec{sp}"
            add(f"R-E.{pop}.{band}.{k}", m["bands"][band]["expected_micro_f1_with_verifier"][k],
                r["bands"][band]["expected_micro_f1_with_verifier"][k], tol=1e-9)

n_dis = sum(1 for e in record["entries"] if e["status"] == "DISAGREE")
record["total"] = len(record["entries"])
record["disagreements"] = n_dis
record["status"] = "ALL_AGREE" if n_dis == 0 else "DISAGREEMENTS_PRESENT"

OUT.write_text(json.dumps(record, indent=1), "utf-8")
print(f"written: {OUT}")
print(f"entries={record['total']} disagreements={n_dis} status={record['status']}")
for e in record["entries"]:
    if e["status"] == "DISAGREE":
        print("DISAGREE:", e["key"], "mine=", e["mine"], "ref=", e["reference"])
