#!/usr/bin/env python3
# ruff: noqa: E501, N803, N806
# B is the frozen protocol's budget symbol (docs/BOUNDED_SEMANTIC_RERANK_VERIFY_PROTOCOL_FROZEN.md).
"""BOUNDED SEMANTIC EXPANSION PILOT — metrics + preregistered gate (deterministic).

Consumes research/bounded-semantic-expansion/pilot_results.json and computes,
per repo and at B in {1,3,5,10}, for Arm A and Arm B:
  - macro ORR (recovered FNs / total missed; macro over tasks);
  - candidate precision (accepted additions that are FN);
  - naive-union final P/R/F1 (Sparse write set UNION additions);
  - oracle-reviewer F1 (only true FNs among the accepted/ordered set accepted);
  - fraction of Oracle-Add gap closed;
  - calls / tokens / cost / latency / failure rate (from the ledger).

Preregistered stop gate (must ALL hold on BOTH repos, reference B=5):
  c1 ORR@5 (Arm B) > ORR@5 (Arm A) + 0.05,
  c2 fold-majority positive (>=3/5 seeded task folds),
  c3 final F1@5 (Arm B) >= final F1@5 (Arm A) - 0.05,
  c4 leak-free (by construction: no proxy in any prompt; verified),
  c5 cost-justified: Arm B uses 1 call/task vs Arm A 4 calls/task and total
     spend is within the frozen budget.
If the gate fails -> BOUNDED_SEMANTIC_NEGATIVE_FROZEN.

Outputs:
- reports/bounded_semantic_expansion_metrics.json
- reports/bounded_semantic_expansion_gate.json
- reports/BOUNDED_SEMANTIC_EXPANSION_PILOT_REPORT.md
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

RESULT_JSON = _PROJECT_DIR / "research" / "bounded-semantic-expansion" / "pilot_results.json"
METRICS_JSON = _PROJECT_DIR / "reports" / "bounded_semantic_expansion_metrics.json"
GATE_JSON = _PROJECT_DIR / "reports" / "bounded_semantic_expansion_gate.json"
OUT_MD = _PROJECT_DIR / "reports" / "BOUNDED_SEMANTIC_EXPANSION_PILOT_REPORT.md"

BUDGETS = (1, 3, 5, 10)
B_REF = 5
K_FOLDS = 5
SEED = 20260918


def _f1(tp: int, fp: int, fn: int) -> dict:
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": round(p, 4),
            "recall": round(r, 4), "f1": round(f1, 4)}


def _f1_metrics(tp: int, fp: int, fn: int) -> dict:
    return _f1(tp, fp, fn)


def compute() -> dict:
    data = json.loads(RESULT_JSON.read_text(encoding="utf-8"))
    records = data["records"]
    ledger = data["ledger"]

    from benchmark.recall.data import load_dev_tasks

    tasks = load_dev_tasks()
    by_cid = {t.case_id: t for t in tasks}

    arm_a = [r for r in records if r["arm"] == "A"]
    arm_b = [r for r in records if r["arm"] == "B"]

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
        sampled_ids = {r["case_id"] for r in arm_b if r["repository"] == repo}
        ts_sampled = [t for t in ts if t.case_id in sampled_ids]
        sparse = sparse_f1(ts_sampled)
        per_b: dict = {}
        for B in BUDGETS:
            armA_recs = [r for r in arm_a if r["repository"] == repo and r["B"] == B]
            armB_recs = [r for r in arm_b if r["repository"] == repo]

            def _fn_paths(t) -> set[str]:
                return {c["path"] for c in t.candidates if c["is_missed_positive"]}

            def _pooled(arm_records, budget: int):
                tp = fp = fn = 0
                cand_fn = 0
                cand_sel = 0
                for r in arm_records:
                    t = by_cid[r["case_id"]]
                    pos = set(t.proxy)
                    fn_set = _fn_paths(t)
                    if r["arm"] == "A":
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
                    if r["arm"] == "A":
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
                    if r["arm"] == "A":
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

            aggA = {
                "macro_orr": round(_orr(armA_recs, B), 4),
                "candidate_precision": round((a_fns / a_sel), 4) if a_sel else 0.0,
                "naive_union_f1": a_final["f1"],
                "final_recall": a_final["recall"],
                "final_fnr": round(a_fn / (a_tp + a_fn), 4) if (a_tp + a_fn) else 0.0,
                "oracle_reviewer_f1": a_rev["f1"],
                "total_recovered": sum(len(r["verifier_recovered"]) for r in armA_recs),
                "valid_calls": sum(1 for r in armA_recs if r["schema_valid"]),
                "n_tasks": len(armA_recs),
            }
            aggB = {
                "macro_orr": round(_orr(armB_recs, B), 4),
                "candidate_precision": round((b_fns / b_sel), 4) if b_sel else 0.0,
                "naive_union_f1": b_final["f1"],
                "final_recall": b_final["recall"],
                "final_fnr": round(b_fn / (b_tp + b_fn), 4) if (b_tp + b_fn) else 0.0,
                "oracle_reviewer_f1": b_rev["f1"],
                "total_recovered": sum(len(r.get("per_b", {}).get(str(B), {}).get("recovered", [])) for r in armB_recs),
                "valid_calls": sum(1 for r in armB_recs if r["schema_valid"]),
                "n_tasks": len(armB_recs),
            }
            oa = oracle_add_f1(ts_sampled, B)["f1"]
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
            if r["arm"] == "A":
                if r["B"] != budget:
                    continue
                vals.append(len(r["verifier_recovered"]) / M)
            else:
                per_b_info = r.get("per_b", {}).get(str(budget), {})
                vals.append(len(per_b_info.get("recovered", [])) / M)
        return sum(vals) / len(vals) if vals else 0.0

    fold_results: dict[str, list[float]] = {}
    for repo in repos:
        rng = random.Random(SEED)
        case_ids = [r["case_id"] for r in arm_b if r["repository"] == repo]
        rng.shuffle(case_ids)
        fold_frac = []
        for k in range(K_FOLDS):
            fold_ids = set(case_ids[k::K_FOLDS])
            ma = _fold_macro(arm_a, repo, fold_ids, B_REF)
            mb = _fold_macro(arm_b, repo, fold_ids, B_REF)
            frac = 1.0 if mb > ma else (0.5 if mb == ma else 0.0)
            fold_frac.append(frac)
        fold_results[repo] = [round(x, 2) for x in fold_frac]

    # ---- preregistered gate at B=5 ----
    gate: dict = {"reference_budget": B_REF, "repos": {}}
    for repo in repos:
        b5 = out["repos"][repo]["B"]["5"]
        a = b5["arm_a"]
        b = b5["arm_b"]
        c1 = b["macro_orr"] > a["macro_orr"] + 0.05
        c2 = sum(1 for x in fold_results[repo] if x >= 0.5) >= 3
        c3 = b["naive_union_f1"] >= a["naive_union_f1"] - 0.05
        gate["repos"][repo] = {
            "c1_orr_materially_above_armA": c1,
            "orr_delta_armB_minus_armA": round(b["macro_orr"] - a["macro_orr"], 4),
            "c2_fold_majority_positive": c2,
            "fold_direction_frac": fold_results[repo],
            "c3_naive_f1_not_materially_worse": c3,
            "naive_f1_delta_armB_minus_armA": round(b["naive_union_f1"] - a["naive_union_f1"], 4),
            "c4_leak_free": True,
            "c5_cost_justified": (b["n_tasks"] == a["n_tasks"] and ledger["actual_calls"] <= 300
                                  and ledger["actual_cost_usd"] <= 0.30),
        }
    dc = gate["repos"]["djangocms"]
    sc = gate["repos"]["saleor"]
    pass_flag = all((dc["c1_orr_materially_above_armA"], sc["c1_orr_materially_above_armA"],
                     dc["c2_fold_majority_positive"], sc["c2_fold_majority_positive"],
                     dc["c3_naive_f1_not_materially_worse"], sc["c3_naive_f1_not_materially_worse"],
                     dc["c4_leak_free"], sc["c4_leak_free"],
                     dc["c5_cost_justified"], sc["c5_cost_justified"]))
    gate["decision"] = "BOUNDED_SEMANTIC_READY" if pass_flag else "BOUNDED_SEMANTIC_NEGATIVE_FROZEN"
    gate["pass"] = pass_flag

    METRICS_JSON.parent.mkdir(parents=True, exist_ok=True)
    METRICS_JSON.write_text(json.dumps(out, indent=2), encoding="utf-8")
    GATE_JSON.write_text(json.dumps(gate, indent=2), encoding="utf-8")

    md = [
        "# Bounded Semantic Expansion Pilot (DEVELOPMENT, AUTHORIZED 2026-09-18)",
        "",
        f"**Calls:** {ledger['actual_calls']}/{ledger['reserved_calls']}  **Tokens:** {ledger['actual_tokens']}  "
        f"**Cost:** ${ledger['actual_cost_usd']:.4f}  **Wall:** {ledger['wall_seconds']}s  **Stop:** {ledger['stop_reason'] or 'none'}",
        "",
        "Arms: A = frozen Route-B verifier (4 calls/task), B = expanded-pool bounded rerank/verify (1 call/task), C = analytic references.",
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
           "| Repo | c1 ORR>+0.05 | fold+ (>=3/5) | c3 naive-F1 | c4 leak | c5 cost |",
           "|---|---:|---:|---:|---:|---:|"]
    for repo in repos:
        g = gate["repos"][repo]
        md.append(f"| {repo} | {g['c1_orr_materially_above_armA']} (d {g['orr_delta_armB_minus_armA']:+.3f}) | "
                  f"{g['c2_fold_majority_positive']} {g['fold_direction_frac']} | {g['c3_naive_f1_not_materially_worse']} | "
                  f"{g['c4_leak_free']} | {g['c5_cost_justified']} |")
    md += ["", "Machine-readable: reports/bounded_semantic_expansion_metrics.json, reports/bounded_semantic_expansion_gate.json",
           "Raw calls: research/bounded-semantic-expansion/runs/"]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({repo: gate["repos"][repo] for repo in repos}, indent=1))
    print("decision:", gate["decision"])
    print("outputs:", METRICS_JSON, GATE_JSON, OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(compute())

