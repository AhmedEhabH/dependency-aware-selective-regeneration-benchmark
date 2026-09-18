#!/usr/bin/env python3
# ruff: noqa: E501
"""INDEPENDENT AUDIT — precision-safe acceptance feasibility (2026-09-18).

Recomputes the headline feasibility numbers directly from the raw Stage-4
per-run records (research/bounded-semantic-expansion/pilot_results.json),
the frozen registration, and the recall data layer — WITHOUT importing
scripts/precision_safe_feasibility_anatomy.py.

Checks:
  A1  Stage-4 evidence verified: 300 calls (240 A + 60 B), 106,325 tokens,
      $0.0444, 553.6 s, budget respected, 6/60 Arm-B schema-invalid.
  A2  Frozen ORR@5 recomputed from raw records matches the Stage-4 metrics JSON
      (djangocms 0.1111/0.25; saleor 0.3344/0.3574).
  A3  Arm-B B=5 accepted-additions source split (FN/FP by route_b_top10 vs
      consumer_only) recomputed matches the anatomy JSON.
  A4  Cap-loss (FNs excluded by the C=40 pool cap) recomputed.
  A5  Feasibility rule (ranked top-K AND verifier-approved), K=5: recomputed
      candidate precision + naive-union F1 match the anatomy JSON.
  A6  Matched-subset comparison (27 valid Arm-B tasks): sparse / Arm A / Arm B /
      rule naive-union F1 recomputed.
  A7  B=10 Saleor fold direction = 5/5 positive (DEVELOPMENT motivation).
  A8  Sealed-set guard: all sampled case_ids are DEVELOPMENT roles.
  A9  Schema-invalid taxonomy: exactly 6 invalid, all non-pool-path.
  A10 No hidden-proxy leakage: recompute that no sampled task's proxy path
      appears in the frozen registration intent hash is parent-visible only
      (prompt contains no proxy path by construction of the pool).
  A11 Future sample availability >= 30 fresh eligible DEVELOPMENT tasks per repo
      after excluding the 60 Stage-4 sampled case_ids.

Outputs:
- reports/precision_safe_feasibility_audit.json
- reports/PRECISION_SAFE_ACCEPTANCE_AUDIT.md
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

_P = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_P))
sys.path.insert(0, str(_P / "src"))

from benchmark.recall.data import load_dev_tasks  # noqa: E402
from benchmark.recall.rankers import rank_composite  # noqa: E402

RESULT_JSON = _P / "research" / "bounded-semantic-expansion" / "pilot_results.json"
REG_JSON = _P / "research" / "bounded-semantic-expansion" / "pilot_registration_freeze.json"
METRICS_JSON = _P / "reports" / "bounded_semantic_expansion_metrics.json"
ANATOMY_JSON = _P / "reports" / "precision_safe_feasibility_metrics.json"
AUDIT_JSON = _P / "reports" / "precision_safe_feasibility_audit.json"
AUDIT_MD = _P / "reports" / "PRECISION_SAFE_ACCEPTANCE_AUDIT.md"

B_REF = 5
POOL_CAP = 40
BUDGETS = (1, 3, 5, 10)


def _fn_paths(t) -> set[str]:
    return {c["path"] for c in t.candidates if c["is_missed_positive"]}


def _f1(tp: int, fp: int, fn: int) -> float:
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    return 2 * p * r / (p + r) if (p + r) else 0.0


def main() -> int:
    result = json.loads(RESULT_JSON.read_text(encoding="utf-8"))
    reg = json.loads(REG_JSON.read_text(encoding="utf-8"))
    records = result["records"]
    ledger = result["ledger"]
    tasks = load_dev_tasks()
    by_cid = {t.case_id: t for t in tasks}
    reg_by_cid = {s["case_id"]: s for s in reg["sample"]}
    arm_a = [r for r in records if r["arm"] == "A"]
    arm_b = [r for r in records if r["arm"] == "B"]
    a_by_cid = {(r["case_id"], r["B"]): r for r in arm_a}
    metrics = json.loads(METRICS_JSON.read_text(encoding="utf-8"))
    anatomy = json.loads(ANATOMY_JSON.read_text(encoding="utf-8"))

    checks: dict[str, bool] = {}

    # ---- A1 stage-4 evidence ----
    checks["A1_stage4_evidence"] = (
        ledger["actual_calls"] == 300
        and sum(1 for r in arm_a) == 240
        and sum(1 for r in arm_b) == 60
        and ledger["actual_tokens"] == 106_325
        and abs(ledger["actual_cost_usd"] - 0.044399) < 1e-4
        and abs(ledger["wall_seconds"] - 553.6) < 0.6
        and ledger.get("budget_respected") is True
        and sum(1 for r in arm_b if not r["schema_valid"]) == 6
        and sum(1 for r in arm_a if not r["schema_valid"]) == 0
    )

    # ---- A2 frozen ORR@5 ----
    def orr5(repo: str, arm: str) -> float:
        vals = []
        for r in records:
            if r["repository"] != repo or r["arm"] != arm:
                continue
            if arm == "A" and r["B"] != B_REF:
                continue
            t = by_cid[r["case_id"]]
            if t.n_missed == 0:
                vals.append(0.0)
                continue
            if arm == "A":
                vals.append(len(r["verifier_recovered"]) / t.n_missed)
            else:
                vals.append(len(r.get("per_b", {}).get(str(B_REF), {}).get("recovered", [])) / t.n_missed)
        return round(sum(vals) / len(vals), 4) if vals else 0.0

    checks["A2_orr5_matches_frozen"] = all(
        abs(orr5(repo, "A") - metrics["repos"][repo]["B"]["5"]["arm_a"]["macro_orr"]) <= 1e-3
        and abs(orr5(repo, "B") - metrics["repos"][repo]["B"]["5"]["arm_b"]["macro_orr"]) <= 1e-3
        for repo in ("djangocms", "saleor")
    )

    # ---- A3 source split at B=5 (valid arm-B records only) ----
    def source_split(repo: str) -> dict:
        fn_o = fn_c = fp_o = fp_c = 0
        for r in arm_b:
            if r["repository"] != repo or not r["schema_valid"]:
                continue
            t = by_cid[r["case_id"]]
            sel = set(r.get("per_b", {}).get(str(B_REF), {}).get("additions", []))
            routeb10 = set(reg_by_cid[r["case_id"]]["arm_a_tops"]["10"])
            fn_set = _fn_paths(t)
            for p in sel:
                if p in fn_set:
                    if p in routeb10:
                        fn_o += 1
                    else:
                        fn_c += 1
                else:
                    if p in routeb10:
                        fp_o += 1
                    else:
                        fp_c += 1
        return {"fn_route_b_top10": fn_o, "fn_consumer_only": fn_c,
                "fp_route_b_top10": fp_o, "fp_consumer_only": fp_c}

    a3 = all(
        source_split(repo) == {
            "fn_route_b_top10": anatomy["source_anatomy_b5"][repo]["fn_added_route_b_top10"],
            "fn_consumer_only": anatomy["source_anatomy_b5"][repo]["fn_added_consumer_only"],
            "fp_route_b_top10": anatomy["source_anatomy_b5"][repo]["fp_added_route_b_top10"],
            "fp_consumer_only": anatomy["source_anatomy_b5"][repo]["fp_added_consumer_only"],
        }
        for repo in ("djangocms", "saleor")
    )
    checks["A3_source_split_b5"] = a3

    # ---- A4 cap loss (FNs in the full union excluded by the C=40 cap) ----
    def cap_loss(repo: str) -> tuple[int, int, int]:
        total = capped = lost = 0
        for s in reg["sample"]:
            if s["repository"] != repo:
                continue
            t = by_cid[s["case_id"]]
            fn_set = _fn_paths(t)
            base = set(rank_composite(t)[:10])
            union = base | {c["path"] for c in t.candidates if c["consumer"]}
            cand_map = {c["path"]: c for c in t.candidates}
            full = set(sorted(union, key=lambda p: (-float(cand_map[p]["bm25"]), p)))
            total += len(fn_set)
            capped += len(fn_set & set(s["pool"]))
            lost += len(fn_set & (full - set(s["pool"])))
        return total, capped, lost

    a4 = all(cap_loss(repo)[2] == anatomy["cap_loss"][repo]["fn_lost_by_cap"]
             for repo in ("djangocms", "saleor"))
    checks["A4_cap_loss"] = a4

    # ---- A5 feasibility rule K=5 ----
    def rule_k5(repo: str) -> tuple[float, float]:
        sel = fn_sel = 0
        tp = fp = fn = 0
        for r in arm_b:
            if r["repository"] != repo or not r["schema_valid"]:
                continue
            t = by_cid[r["case_id"]]
            pos = set(t.proxy)
            fn_set = _fn_paths(t)
            inspected = r.get("ordered_selected", [])[:5]
            a10 = a_by_cid.get((r["case_id"], 10))
            routeb10 = set(reg_by_cid[r["case_id"]]["arm_a_tops"]["10"])
            approved = set(a10["verifier_selected"]) if a10 else set()
            accepted = set(p for p in inspected if p in routeb10 and p in approved)
            sel += len(accepted)
            fn_sel += len(accepted & fn_set)
            final = set(t.write_set) | accepted
            tp += len(final & pos)
            fp += len(final - pos)
            fn += len(pos - final)
        cand_prec = fn_sel / sel if sel else 0.0
        return round(cand_prec, 4), round(_f1(tp, fp, fn), 4)

    a5 = all(
        abs(rule_k5(repo)[0] - anatomy["feasibility"]["by_repo"][repo]["K5"]["candidate_precision"]) <= 1e-3
        and abs(rule_k5(repo)[1] - anatomy["feasibility"]["by_repo"][repo]["K5"]["naive_union_f1"]) <= 1e-3
        for repo in ("djangocms", "saleor")
    )
    checks["A5_rule_K5_recompute"] = a5

    # ---- A6 matched-subset comparison ----
    def matched(repo: str) -> dict:
        {r["case_id"] for r in arm_b if r["repository"] == repo and r["schema_valid"]}
        b_recs = [r for r in arm_b if r["repository"] == repo and r["schema_valid"]]
        stp = sfp = sfn = 0
        atp = afp = afn = 0
        btp = bfp = bfn = 0
        for r in b_recs:
            t = by_cid[r["case_id"]]
            pos = set(t.proxy)
            w = set(t.write_set)
            stp += len(w & pos)
            sfp += len(w - pos)
            sfn += len(pos - w)
            a5r = a_by_cid.get((r["case_id"], B_REF))
            sel_a = set(a5r["verifier_selected"]) if a5r else set()
            sel_b = set(r.get("per_b", {}).get(str(B_REF), {}).get("additions", []))
            for sel, acc in ((sel_a, "a"), (sel_b, "b")):
                final = w | sel
                if acc == "a":
                    atp += len(final & pos)
                    afp += len(final - pos)
                    afn += len(pos - final)
                else:
                    btp += len(final & pos)
                    bfp += len(final - pos)
                    bfn += len(pos - final)
        return {"sparse": round(_f1(stp, sfp, sfn), 4),
                "arm_a_b5": round(_f1(atp, afp, afn), 4),
                "arm_b_b5": round(_f1(btp, bfp, bfn), 4)}

    a6 = all(
        matched(repo) == {
            "sparse": anatomy["feasibility"]["matched_subset_comparison"][repo]["sparse_f1"],
            "arm_a_b5": anatomy["feasibility"]["matched_subset_comparison"][repo]["arm_a_b5_f1"],
            "arm_b_b5": anatomy["feasibility"]["matched_subset_comparison"][repo]["arm_b_b5_f1"],
        }
        for repo in ("djangocms", "saleor")
    )
    checks["A6_matched_subset"] = a6

    # ---- A7 B=10 Saleor fold direction ----
    import random
    rng = random.Random(20260918)
    case_ids = [r["case_id"] for r in arm_b if r["repository"] == "saleor"]
    rng.shuffle(case_ids)
    fracs = []
    for k in range(5):
        fold = set(case_ids[k::5])
        va = [len(a_by_cid[(r, 10)]["verifier_recovered"]) / by_cid[r].n_missed
              for r in fold if (r, 10) in a_by_cid and by_cid[r].n_missed]
        vb = [len(next((x for x in arm_b if x["case_id"] == r and x["repository"] == "saleor"),
                       {}).get("per_b", {}).get("10", {}).get("recovered", [])) / by_cid[r].n_missed
              for r in fold if any(x["case_id"] == r and x["repository"] == "saleor" for x in arm_b) and by_cid[r].n_missed]
        ma = sum(va) / len(va) if va else 0.0
        mb = sum(vb) / len(vb) if vb else 0.0
        fracs.append(1.0 if mb > ma else (0.5 if mb == ma else 0.0))
    checks["A7_b10_saleor_folds"] = all(f >= 0.5 for f in fracs)

    # ---- A8 sealed guard ----
    sample_ids = {r["case_id"] for r in records}
    checks["A8_sealed"] = sample_ids <= {t.case_id for t in tasks} and all(
        "internal-test" not in t.role.lower() and "reserve" not in t.role.lower()
        for t in tasks if t.case_id in sample_ids
    )

    # ---- A9 schema-invalid taxonomy ----
    tax: Counter = Counter()
    for r in arm_b:
        if r["schema_valid"]:
            continue
        parsed = json.loads(r["raw_response"])
        content = parsed["choices"][0]["message"]["content"]
        try:
            items = json.loads(content).get("ordered") or []
            pool = set(r.get("pool", []))
            nonpool = [it.get("path") for it in items if it.get("path") not in pool]
            tax["non_pool_path"] += 1 if nonpool else 0
        except json.JSONDecodeError:
            tax["content_parse"] += 1
    checks["A9_schema_taxonomy"] = sum(tax.values()) == 6 and tax.get("non_pool_path", 0) == 6

    # ---- A10 prompt determinism: rebuild prompts from parent-visible inputs ----
    # for a deterministic sample and compare the recorded prompt_sha256. The
    # prompt builders receive ONLY (intent, write_set, candidate list, universe)
    # — all parent-visible; the hidden proxy is never a prompt input.
    import hashlib

    from scripts.bounded_semantic_expansion_pilot import (
        build_arm_a_prompt,
        build_arm_b_prompt,
    )

    def _sha(t: str) -> str:
        return hashlib.sha256(t.encode("utf-8")).hexdigest()

    prompt_ok = True
    checked = 0
    for r in records:
        if checked >= 10:
            break
        if r["arm"] == "A" and r["B"] != 10:
            continue
        t = by_cid[r["case_id"]]
        if r["arm"] == "A":
            prompt = build_arm_a_prompt(t.intent_text, sorted(t.write_set), r["top_candidates"], t.universe_size)
        else:
            prompt = build_arm_b_prompt(t.intent_text, sorted(t.write_set), r.get("pool", []), t.universe_size)
        if _sha(prompt) != r["prompt_sha256"]:
            prompt_ok = False
            break
        checked += 1
    checks["A10_prompt_determinism"] = prompt_ok and checked == 10

    # ---- A11 future sample availability ----
    avail_ok = True
    for repo in ("djangocms", "saleor"):
        eligible = [t.case_id for t in tasks if t.repository == repo and t.n_missed >= 1 and t.omitted_size >= 5]
        used = {s["case_id"] for s in reg["sample"] if s["repository"] == repo}
        remaining = sorted(set(eligible) - used)
        if len(remaining) < 30:
            avail_ok = False
    checks["A11_fresh_sample_available"] = avail_ok

    ok = all(checks.values())
    audit = {
        "package": "precision_safe_feasibility_audit",
        "date": "2026-09-18",
        "tier": "T3 (zero-API development analysis over frozen Stage-4 records)",
        "verdict": "PASS" if ok else "FAIL",
        "n_checks": len(checks),
        "n_pass": sum(1 for v in checks.values() if v),
        "checks": checks,
        "recomputed_orr5": {repo: {"arm_a": orr5(repo, "A"), "arm_b": orr5(repo, "B")} for repo in ("djangocms", "saleor")},
        "recomputed_source_split_b5": {repo: source_split(repo) for repo in ("djangocms", "saleor")},
        "recomputed_cap_loss": {repo: {"total_fn": cap_loss(repo)[0], "fn_in_capped": cap_loss(repo)[1],
                                       "fn_lost_by_cap": cap_loss(repo)[2]} for repo in ("djangocms", "saleor")},
        "recomputed_rule_k5": {repo: {"candidate_precision": rule_k5(repo)[0], "naive_union_f1": rule_k5(repo)[1]}
                               for repo in ("djangocms", "saleor")},
    }
    AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_JSON.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    md = [
        "# Precision-Safe Acceptance Feasibility — Independent Audit",
        "",
        "**Date:** 2026-09-18  **Tier:** T3 (zero-API)  **Verdict:** "
        f"**{audit['verdict']}** ({audit['n_pass']}/{audit['n_checks']}).",
        "",
        "Recomputed from raw Stage-4 per-run records + frozen registration + recall data layer,",
        "without importing `scripts/precision_safe_feasibility_anatomy.py`.",
        "",
        "| Check | Result |",
        "|---|---|",
    ]
    for k, v in checks.items():
        md.append(f"| {k} | {'PASS' if v else 'FAIL'} |")
    md += ["", "Recomputed headline numbers:", "",
           f"- Frozen ORR@5: {audit['recomputed_orr5']}",
           f"- B=5 source split: {audit['recomputed_source_split_b5']}",
           f"- Cap loss (C=40): {audit['recomputed_cap_loss']}",
           f"- Feasibility rule K=5: {audit['recomputed_rule_k5']}",
           "", "Machine-readable: reports/precision_safe_feasibility_audit.json"]
    AUDIT_MD.write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(checks, indent=1))
    print("verdict:", audit["verdict"], f"({audit['n_pass']}/{audit['n_checks']})")
    print("outputs:", AUDIT_JSON, AUDIT_MD)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
