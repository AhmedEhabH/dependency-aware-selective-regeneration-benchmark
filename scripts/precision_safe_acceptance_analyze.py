#!/usr/bin/env python3
# ruff: noqa: E501, N803, N806
# B is the frozen protocol's budget symbol (docs/PRECISION_SAFE_ACCEPTANCE_PROTOCOL_FROZEN.md).
"""PRECISION-SAFE ACCEPTANCE PILOT — metrics + preregistered gate (deterministic).

Consumes research/precision-safe-acceptance-pilot/pilot_results.json and
computes, per repo and at B in {1,3,5,10}, for Arm A (frozen Route-B verifier)
and Arm B (RANK -> VERIFY -> VARIABLE ACCEPT):
  - macro ORR (recovered FNs / total missed; macro over tasks);
  - candidate precision (accepted additions that are FN);
  - naive-union final P/R/F1 (Sparse write set UNION additions);
  - oracle-reviewer F1; fraction of Oracle-Add gap closed;
  - calls / tokens / cost / latency / failure rate (ledger).

Preregistered stop gate (docs/PRECISION_SAFE_ACCEPTANCE_PROTOCOL_FROZEN.md
Section 11; reference B=5; MUST hold on BOTH repos):
  c1 macro ORR (Arm B) > macro ORR (Arm A) + 0.05,
  c2 >=3/5 seeded folds positive direction,
  c3 naive-union F1 (Arm B) >= Arm A F1 - 0.05,
  c4 Arm-B candidate precision >= Arm-A candidate precision,
  c5 leak-free (audited separately),
  c6 >=90% schema-valid dispatched calls AND zero partial credit,
  c7 within frozen ceilings AND marginal cost justified (Arm B <= 2 calls/task),
  c8 per-task delta distribution (descriptive).

If any gate condition fails on either repo -> freeze the negative; no tuning.

Outputs:
- reports/precision_safe_acceptance_metrics.json
- reports/precision_safe_acceptance_gate.json
- reports/PRECISION_SAFE_ACCEPTANCE_PILOT_REPORT.md
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

RESULT_JSON = _PROJECT_DIR / "research" / "precision-safe-acceptance-pilot" / "pilot_results.json"
METRICS_JSON = _PROJECT_DIR / "reports" / "precision_safe_acceptance_metrics.json"
GATE_JSON = _PROJECT_DIR / "reports" / "precision_safe_acceptance_gate.json"
OUT_MD = _PROJECT_DIR / "reports" / "PRECISION_SAFE_ACCEPTANCE_PILOT_REPORT.md"

BUDGETS = (1, 3, 5, 10)
B_REF = 5
K_FOLDS = 5
SEED = 20260919


def _f1(tp: int, fp: int, fn: int) -> dict:
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": round(p, 4),
            "recall": round(r, 4), "f1": round(f1, 4)}


def compute() -> dict:
    data = json.loads(RESULT_JSON.read_text(encoding="utf-8"))
    records = data["records"]
    ledger = data["ledger"]

    from benchmark.recall.data import load_dev_tasks

    tasks = load_dev_tasks()
    by_cid = {t.case_id: t for t in tasks}

    arm_a = [r for r in records if r["stage"] == "arm_a_verifier"]
    rank_recs = [r for r in records if r["stage"] == "rank"]
    verify_recs = [r for r in records if r["stage"] == "verify"]

    def _fn_paths(t) -> set[str]:
        return {c["path"] for c in t.candidates if c["is_missed_positive"]}

    def oracle_add_f1(ts, B):
        tp = fp = fn = 0
        for t in ts:
            pos = set(t.proxy)
            pred = set(t.write_set)
            fn_set = pos - pred
            add = set(list(sorted(fn_set))[:B])
            final = pred | add
            tp += len(final & pos)
            fp += len(final - pos)
            fn += len(pos - final)
        return _f1(tp, fp, fn)

    def sparse_f1(ts):
        tp = fp = fn = 0
        for t in ts:
            pos = set(t.proxy)
            pred = set(t.write_set)
            tp += len(pred & pos)
            fp += len(pred - pos)
            fn += len(pos - pred)
        return _f1(tp, fp, fn)

    repos = ("djangocms", "saleor")
    out: dict = {"repos": {}, "ledger": ledger}

    for repo in repos:
        ts = [t for t in tasks if t.repository == repo]
        sampled_ids = {r["case_id"] for r in rank_recs if r["repository"] == repo}
        ts_sampled = [t for t in ts if t.case_id in sampled_ids]
        sparse = sparse_f1(ts_sampled)
        per_b: dict = {}
        for B in BUDGETS:
            armA_recs = [r for r in arm_a if r["repository"] == repo and r["B"] == B]
            armB_recs = [r for r in rank_recs if r["repository"] == repo]

            def _pooled(arm_records, budget: int):
                tp = fp = fn = 0
                cand_fn = 0
                cand_sel = 0
                for r in arm_records:
                    t = by_cid[r["case_id"]]
                    pos = set(t.proxy)
                    fn_set = _fn_paths(t)
                    if r["stage"] == "arm_a_verifier":
                        sel = set(r["verifier_selected"])
                    else:
                        sel = set(r.get("per_b", {}).get(str(budget), {}).get("additions", []))
                    final = set(t.write_set) | sel
                    tp += len(final & pos)
                    fp += len(final - pos)
                    fn += len(pos - final)
                    cand_sel += len(sel)
                    cand_fn += len(sel & fn_set)
                return tp, fp, fn, cand_sel, cand_fn

            def _orr(arm_records, budget: int) -> float:
                vals = []
                for r in arm_records:
                    t = by_cid[r["case_id"]]
                    M = t.n_missed
                    if M == 0:
                        vals.append(0.0)
                        continue
                    if r["stage"] == "arm_a_verifier":
                        vals.append(len(r["verifier_recovered"]) / M)
                    else:
                        vals.append(len(r.get("per_b", {}).get(str(budget), {}).get("recovered", [])) / M)
                return sum(vals) / len(vals) if vals else 0.0

            def _oracle_reviewer_pooled(arm_records, budget: int):
                tp = fp = fn = 0
                for r in arm_records:
                    t = by_cid[r["case_id"]]
                    pos = set(t.proxy)
                    fn_set = _fn_paths(t)
                    if r["stage"] == "arm_a_verifier":
                        accepted = set(r["verifier_selected"]) & fn_set
                    else:
                        accepted = set(r.get("per_b", {}).get(str(budget), {}).get("additions", [])) & fn_set
                    final = set(t.write_set) | accepted
                    tp += len(final & pos)
                    fp += len(final - pos)
                    fn += len(pos - final)
                return _f1(tp, fp, fn)

            a_tp, a_fp, a_fn, a_sel, a_fns = _pooled(armA_recs, B)
            b_tp, b_fp, b_fn, b_sel, b_fns = _pooled(armB_recs, B)
            a_final = _f1(a_tp, a_fp, a_fn)
            b_final = _f1(b_tp, b_fp, b_fn)
            a_rev = _oracle_reviewer_pooled(armA_recs, B)
            b_rev = _oracle_reviewer_pooled(armB_recs, B)
            oa = oracle_add_f1(ts_sampled, B)["f1"]

            aggA = {
                "macro_orr": round(_orr(armA_recs, B), 4),
                "candidate_precision": round((a_fns / a_sel), 4) if a_sel else 0.0,
                "naive_union_f1": a_final["f1"],
                "final_precision": a_final["precision"],
                "final_recall": a_final["recall"],
                "final_fnr": round(a_fn / (a_tp + a_fn), 4) if (a_tp + a_fn) else 0.0,
                "oracle_reviewer_f1": a_rev["f1"],
                "total_recovered": sum(len(r["verifier_recovered"]) for r in armA_recs),
                "n_selected": a_sel,
                "valid_calls": sum(1 for r in armA_recs if r["schema_valid"]),
                "n_tasks": len(armA_recs),
            }
            aggB = {
                "macro_orr": round(_orr(armB_recs, B), 4),
                "candidate_precision": round((b_fns / b_sel), 4) if b_sel else 0.0,
                "naive_union_f1": b_final["f1"],
                "final_precision": b_final["precision"],
                "final_recall": b_final["recall"],
                "final_fnr": round(b_fn / (b_tp + b_fn), 4) if (b_tp + b_fn) else 0.0,
                "oracle_reviewer_f1": b_rev["f1"],
                "total_recovered": sum(len(r.get("per_b", {}).get(str(B), {}).get("recovered", [])) for r in armB_recs),
                "n_selected": b_sel,
                "valid_calls": sum(1 for r in armB_recs if r["schema_valid"]),
                "n_tasks": len(armB_recs),
            }
            per_b[str(B)] = {
                "arm_a": aggA, "arm_b": aggB,
                "oracle_add_f1": oa,
                "sparse_f1": sparse["f1"],
                "arm_a_fraction_oracle_add_gap_closed": round(
                    (a_rev["f1"] - sparse["f1"]) / (oa - sparse["f1"]), 4
                ) if (oa - sparse["f1"]) > 0 else 0.0,
                "arm_b_fraction_oracle_add_gap_closed": round(
                    (b_rev["f1"] - sparse["f1"]) / (oa - sparse["f1"]), 4
                ) if (oa - sparse["f1"]) > 0 else 0.0,
            }
        out["repos"][repo] = {"n_tasks_dev": len(ts), "n_tasks_sampled": len(ts_sampled),
                              "sparse_f1": sparse["f1"], "B": per_b}

    # ---- fold stability (seeded task-grouped) for ORR@5 delta ArmB - ArmA ----
    def _fold_macro(recs, repo: str, fold_ids: set, budget: int) -> float:
        vals: list[float] = []
        for r in recs:
            if r["repository"] != repo or r["case_id"] not in fold_ids:
                continue
            t = by_cid[r["case_id"]]
            M = t.n_missed
            if M == 0:
                vals.append(0.0)
                continue
            if r["stage"] == "arm_a_verifier":
                if r["B"] != budget:
                    continue
                vals.append(len(r["verifier_recovered"]) / M)
            else:
                vals.append(len(r.get("per_b", {}).get(str(budget), {}).get("recovered", [])) / M)
        return sum(vals) / len(vals) if vals else 0.0

    fold_results: dict[str, list[float]] = {}
    for repo in repos:
        rng = random.Random(SEED)
        case_ids = [r["case_id"] for r in rank_recs if r["repository"] == repo]
        rng.shuffle(case_ids)
        fold_frac = []
        for k in range(K_FOLDS):
            fold_ids = set(case_ids[k::K_FOLDS])
            ma = _fold_macro(arm_a, repo, fold_ids, B_REF)
            mb = _fold_macro(rank_recs, repo, fold_ids, B_REF)
            frac = 1.0 if mb > ma else (0.5 if mb == ma else 0.0)
            fold_frac.append(frac)
        fold_results[repo] = [round(x, 2) for x in fold_frac]

    # ---- per-task delta distribution at B=5 (c8, descriptive) ----
    task_deltas: dict[str, dict] = {}
    for repo in repos:
        rows = []
        for r in rank_recs:
            if r["repository"] != repo:
                continue
            t = by_cid[r["case_id"]]
            M = t.n_missed
            if M == 0:
                continue
            orr_b = len(r.get("per_b", {}).get(str(B_REF), {}).get("recovered", [])) / M
            a5 = next((x for x in arm_a if x["case_id"] == r["case_id"] and x["B"] == B_REF), None)
            orr_a = len(a5["verifier_recovered"]) / M if a5 else 0.0
            rows.append({"case_id": r["case_id"], "orr_a5": round(orr_a, 4),
                         "orr_b5": round(orr_b, 4), "delta": round(orr_b - orr_a, 4)})
        task_deltas[repo] = {
            "n_tasks": len(rows),
            "n_b_gt_a": sum(1 for x in rows if x["delta"] > 0),
            "n_b_lt_a": sum(1 for x in rows if x["delta"] < 0),
            "n_b_eq_a": sum(1 for x in rows if x["delta"] == 0),
            "mean_delta": round(sum(x["delta"] for x in rows) / len(rows), 4) if rows else 0.0,
        }

    # ---- preregistered gate at B=5 ----
    dispatched = [r for r in records if r.get("total_tokens", 0) > 0 or r.get("api_cost", 0) > 0]
    dispatched_invalid = [r for r in dispatched if not r["schema_valid"]]
    partial_credit = [r for r in records if not r["schema_valid"] and
                      len(r.get("per_b", {}).get(str(B_REF), {}).get("additions", [])) > 0]
    schema_rate = (len(dispatched) - len(dispatched_invalid)) / len(dispatched) if dispatched else 0.0
    arm_b_calls_per_task = (len(rank_recs) + len(verify_recs)) / 60 if rank_recs else 0.0

    gate: dict = {"reference_budget": B_REF, "repos": {}}
    for repo in repos:
        b5 = out["repos"][repo]["B"]["5"]
        a = b5["arm_a"]
        b = b5["arm_b"]
        c1 = b["macro_orr"] > a["macro_orr"] + 0.05
        c2 = sum(1 for x in fold_results[repo] if x >= 0.5) >= 3
        c3 = b["naive_union_f1"] >= a["naive_union_f1"] - 0.05
        c4 = b["candidate_precision"] >= a["candidate_precision"]
        gate["repos"][repo] = {
            "c1_orr_materially_above_armA": c1,
            "orr_delta_armB_minus_armA": round(b["macro_orr"] - a["macro_orr"], 4),
            "c2_fold_majority_positive": c2,
            "fold_direction_frac": fold_results[repo],
            "c3_naive_f1_not_materially_worse": c3,
            "naive_f1_delta_armB_minus_armA": round(b["naive_union_f1"] - a["naive_union_f1"], 4),
            "c4_candidate_precision_not_below_armA": c4,
            "candidate_precision_delta": round(b["candidate_precision"] - a["candidate_precision"], 4),
            "c5_leak_free": True,
            "c6_schema_rate_ge_90pct": schema_rate >= 0.90 and not partial_credit,
            "c7_within_ceilings_and_cost_justified": (
                ledger.get("budget_respected") is True and arm_b_calls_per_task <= 2.0),
        }
    dc = gate["repos"]["djangocms"]
    sc = gate["repos"]["saleor"]
    all_cond = [dc[c] for c in ("c1_orr_materially_above_armA", "c2_fold_majority_positive",
                                "c3_naive_f1_not_materially_worse", "c4_candidate_precision_not_below_armA",
                                "c5_leak_free", "c6_schema_rate_ge_90pct", "c7_within_ceilings_and_cost_justified")]
    all_cond += [sc[c] for c in ("c1_orr_materially_above_armA", "c2_fold_majority_positive",
                                 "c3_naive_f1_not_materially_worse", "c4_candidate_precision_not_below_armA",
                                 "c5_leak_free", "c6_schema_rate_ge_90pct", "c7_within_ceilings_and_cost_justified")]
    gate["schema_rate_all_dispatched_calls"] = round(schema_rate, 4)
    gate["n_dispatched_calls"] = len(dispatched)
    gate["n_invalid_dispatched_calls"] = len(dispatched_invalid)
    gate["zero_partial_credit"] = not partial_credit
    gate["arm_b_calls_per_task"] = round(arm_b_calls_per_task, 3)
    gate["decision"] = "PRECISION_SAFE_ACCEPTANCE_PASS" if all(all_cond) else "PRECISION_SAFE_ACCEPTANCE_FAIL"
    gate["pass"] = all(all_cond)
    gate["task_deltas_b5"] = task_deltas

    METRICS_JSON.parent.mkdir(parents=True, exist_ok=True)
    METRICS_JSON.write_text(json.dumps(out, indent=2), encoding="utf-8")
    GATE_JSON.write_text(json.dumps(gate, indent=2), encoding="utf-8")

    md = [
        "# Precision-Safe Acceptance Pilot (DEVELOPMENT, AUTHORIZED 2026-09-18)",
        "",
        f"**Calls:** {ledger['actual_calls']}/{ledger['reserved_calls']}  **Tokens:** {ledger['actual_tokens']}  "
        f"**Cost:** ${ledger['actual_cost_usd']:.4f}  **Wall:** {ledger['wall_seconds']}s  **Stop:** {ledger['stop_reason'] or 'none'}",
        "",
        "Arms: A = frozen Route-B verifier (4 calls/task), B = RANK->VERIFY->VARIABLE ACCEPT (2 calls/task), C = analytic references.",
        "",
    ]
    for repo in repos:
        r = out["repos"][repo]
        md += [f"## {repo} DEV (sparse F1 {r['sparse_f1']})", "",
               "| B | Arm | ORR | cand-prec | naive-F1 | oracleRev-F1 | OracleAdd-gap | valid/tasks |",
               "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for B in BUDGETS:
            b5 = r["B"][str(B)]
            for arm_key, arm in (("arm_a", "A"), ("arm_b", "B")):
                a = b5[arm_key]
                md.append(
                    f"| {B} | {arm} | {a['macro_orr']:.3f} | {a['candidate_precision']:.3f} | "
                    f"{a['naive_union_f1']:.3f} | {a['oracle_reviewer_f1']:.3f} | "
                    f"{b5[f'{arm_key}_fraction_oracle_add_gap_closed']:.3f} | {a['valid_calls']}/{a['n_tasks']} |"
                )
        md.append("")
    md += ["## Preregistered stop gate (B=5)", "",
           f"**Decision: {gate['decision']}**", "",
           "| Repo | c1 ORR>+0.05 | fold+ (>=3/5) | c3 naive-F1 | c4 cand-prec | c5 leak | c6 schema | c7 cost |",
           "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for repo in repos:
        g = gate["repos"][repo]
        md.append(f"| {repo} | {g['c1_orr_materially_above_armA']} (d {g['orr_delta_armB_minus_armA']:+.3f}) | "
                  f"{g['c2_fold_majority_positive']} {g['fold_direction_frac']} | {g['c3_naive_f1_not_materially_worse']} "
                  f"({g['naive_f1_delta_armB_minus_armA']:+.3f}) | {g['c4_candidate_precision_not_below_armA']} "
                  f"({g['candidate_precision_delta']:+.3f}) | {g['c5_leak_free']} | {g['c6_schema_rate_ge_90pct']} | {g['c7_within_ceilings_and_cost_justified']} |")
    md += ["", f"Schema rate (dispatched calls): {gate['schema_rate_all_dispatched_calls']} "
              f"({gate['n_invalid_dispatched_calls']} invalid / {gate['n_dispatched_calls']}); "
              f"zero partial credit: {gate['zero_partial_credit']}; Arm B calls/task: {gate['arm_b_calls_per_task']}",
           "", "Machine-readable: reports/precision_safe_acceptance_metrics.json, reports/precision_safe_acceptance_gate.json",
           "Raw calls: research/precision-safe-acceptance-pilot/runs/"]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({repo: gate["repos"][repo] for repo in repos}, indent=1))
    print("decision:", gate["decision"])
    print("outputs:", METRICS_JSON, GATE_JSON, OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(compute())
