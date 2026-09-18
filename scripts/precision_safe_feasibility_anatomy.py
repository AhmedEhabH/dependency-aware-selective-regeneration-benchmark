#!/usr/bin/env python3
# ruff: noqa: N806
"""PRECISION-SAFE ACCEPTANCE FEASIBILITY — zero-API failure anatomy (2026-09-18).

POST-Stage-4 DEVELOPMENT analysis over the ALREADY-RECORDED 300 pilot calls.
NO model/API call is made. Everything is a deterministic recomputation from:

  - research/bounded-semantic-expansion/pilot_results.json (300 records)
  - research/bounded-semantic-expansion/pilot_registration_freeze.json (60 tasks)
  - benchmark.recall.data.load_dev_tasks() (frozen DEV task features)

Sections:
  B  Stage-4 evidence verification (frozen negative untouched).
  C  Failure anatomy (13 analyses) decomposing why Arm B gained recovery but
     lost precision, separately for djangoCMS and Saleor.
  D  Inspection-vs-acceptance decoupling (variable accepted set, 0..K).
  E  Precision-safe acceptance feasibility: EXACTLY ONE principled rule family
     (ranked-top-K AND verifier-approved), clearly labelled POST-HOC
     DEVELOPMENT FEASIBILITY — NOT CONFIRMATORY EVIDENCE.
  F  Schema-reliability incidence (valid vs invalid; failure taxonomy).
  H  Future sample-selection availability (fresh disjoint DEVELOPMENT sample).
  J  Cost accounting basis for the future budget freeze draft.

The frozen Stage-4 verdict BOUNDED_SEMANTIC_NEGATIVE_FROZEN is NOT changed.

Output: reports/precision_safe_feasibility_metrics.json
"""
from __future__ import annotations

import json
import random
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
OUT_JSON = _P / "reports" / "precision_safe_feasibility_metrics.json"

BUDGETS = (1, 3, 5, 10)
B_REF = 5
SEED = 20260918
K_FOLDS = 5
POOL_CAP = 40


def _f1(tp: int, fp: int, fn: int) -> dict:
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": round(p, 4),
            "recall": round(r, 4), "f1": round(f1, 4)}


def _fn_paths(t) -> set[str]:
    return {c["path"] for c in t.candidates if c["is_missed_positive"]}


def _consumers(t) -> list[str]:
    return sorted(c["path"] for c in t.candidates if c["consumer"])


def _full_union(t) -> list[str]:
    """Uncapped pool = Route-B composite top-10 UNION reverse-1hop consumers,
    in the frozen deterministic pre-order (desc bm25, asc path)."""
    base = set(rank_composite(t)[:10])
    union = base | set(_consumers(t))
    cand_map = {c["path"]: c for c in t.candidates}
    return sorted(union, key=lambda p: (-float(cand_map[p]["bm25"]), p))


def compute() -> dict:
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
    b_by_cid = {r["case_id"]: r for r in arm_b}

    repos = ("djangocms", "saleor")

    # ---------------------------------------------------------------- B ----
    b_verify = {
        "stage4_verdict_frozen": "BOUNDED_SEMANTIC_NEGATIVE_FROZEN",
        "calls_total": ledger["actual_calls"],
        "calls_arm_a": len(arm_a),
        "calls_arm_b": len(arm_b),
        "tokens": ledger["actual_tokens"],
        "cost_usd": ledger["actual_cost_usd"],
        "wall_seconds": ledger["wall_seconds"],
        "ceilings_respected": ledger.get("budget_respected") is True,
        "arm_a_valid": sum(1 for r in arm_a if r["schema_valid"]),
        "arm_b_valid": sum(1 for r in arm_b if r["schema_valid"]),
        "arm_b_invalid": sum(1 for r in arm_b if not r["schema_valid"]),
    }
    # Recompute frozen ORR@5 for the record (must match reports JSON).
    def _orr5(repo: str, arm: str) -> float:
        vals = []
        for r in records:
            if r["repository"] != repo or r["arm"] != arm:
                continue
            if arm == "A" and r["B"] != B_REF:
                continue
            t = by_cid[r["case_id"]]
            M = t.n_missed
            if M == 0:
                vals.append(0.0)
                continue
            if arm == "A":
                vals.append(len(r["verifier_recovered"]) / M)
            else:
                vals.append(len(r.get("per_b", {}).get(str(B_REF), {}).get("recovered", [])) / M)
        return round(sum(vals) / len(vals), 4) if vals else 0.0

    b_verify["orr5_recomputed"] = {repo: {"arm_a": _orr5(repo, "A"), "arm_b": _orr5(repo, "B")} for repo in repos}

    # ------------------------------------------------------------- C.1 ----
    # Arm-B candidate precision by semantic rank position (pooled, valid only).
    rank_precision: dict[str, dict] = {}
    for repo in repos:
        recs = [r for r in arm_b if r["repository"] == repo and r["schema_valid"]]
        cum_sel: list[int] = []
        cum_fn: list[int] = []
        n_at_rank: list[int] = []
        for i in range(1, 41):
            sel = fp_all = 0
            fn_at = 0
            n_tasks = 0
            for r in recs:
                t = by_cid[r["case_id"]]
                ordered = r.get("ordered_selected", [])
                if len(ordered) >= i:
                    p = ordered[i - 1]
                    n_tasks += 1
                    sel += 1
                    if p in _fn_paths(t):
                        fn_at += 1
            if n_tasks == 0:
                break
            n_at_rank.append(n_tasks)
            cum_sel.append((cum_sel[-1] + sel) if cum_sel else sel)
            cum_fn.append((cum_fn[-1] + fn_at) if cum_fn else fn_at)
            fp_all = cum_sel[-1] - cum_fn[-1]
            rank_precision.setdefault(repo, {"cumulative": [], "pointwise": []})
            rank_precision[repo]["cumulative"].append({
                "rank": i, "n_tasks_with_rank": n_tasks,
                "cum_sel": cum_sel[-1], "cum_fn": cum_fn[-1], "cum_fp": fp_all,
                "cum_candidate_precision": round(cum_fn[-1] / cum_sel[-1], 4) if cum_sel[-1] else 0.0,
            })
            rank_precision[repo]["pointwise"].append({
                "rank": i, "n_tasks_with_rank": n_tasks,
                "point_precision": round(fn_at / n_tasks, 4) if n_tasks else 0.0,
            })

    # --------------------------------------------------------- C.2/C.3 ----
    # Cumulative ORR + candidate precision + FN/FP additions at frozen B.
    def _orr_macro(recs, arm: str, budget: int) -> float:
        vals = []
        for r in recs:
            t = by_cid[r["case_id"]]
            M = t.n_missed
            if M == 0:
                vals.append(0.0)
                continue
            if arm == "A":
                vals.append(len(r["verifier_recovered"]) / M)
            else:
                vals.append(len(r.get("per_b", {}).get(str(budget), {}).get("recovered", [])) / M)
        return round(sum(vals) / len(vals), 4) if vals else 0.0

    per_b_anatomy: dict[str, dict] = {}
    for repo in repos:
        per_b_anatomy[repo] = {}
        for B in BUDGETS:
            a_recs = [r for r in arm_a if r["repository"] == repo and r["B"] == B]
            b_recs = [r for r in arm_b if r["repository"] == repo]
            a_sel = a_fn = 0
            a_rec = 0
            a_M = 0
            for r in a_recs:
                t = by_cid[r["case_id"]]
                sel = set(r["verifier_selected"])
                a_sel += len(sel)
                a_fn += len(sel & _fn_paths(t))
                a_rec += len(r["verifier_recovered"])
                a_M += t.n_missed
            b_sel = b_fn = b_rec = 0
            b_M = 0
            b_fp_by_src: Counter = Counter()
            b_fn_by_src: Counter = Counter()
            for r in b_recs:
                t = by_cid[r["case_id"]]
                per_b = r.get("per_b", {}).get(str(B), {})
                sel = set(per_b.get("additions", []))
                b_sel += len(sel)
                fns = sel & _fn_paths(t)
                b_fn += len(fns)
                b_rec += len(per_b.get("recovered", []))
                b_M += t.n_missed
                routeb10 = set(reg_by_cid[r["case_id"]]["arm_a_tops"]["10"])
                for p in sel:
                    src = "route_b_top10" if p in routeb10 else "consumer_only"
                    if p in _fn_paths(t):
                        b_fn_by_src[src] += 1
                    else:
                        b_fp_by_src[src] += 1
            per_b_anatomy[repo][str(B)] = {
                "arm_a": {
                    "micro_orr": round(a_rec / a_M, 4) if a_M else 0.0,
                    "macro_orr": _orr_macro(a_recs, "A", B),
                    "candidate_precision": round(a_fn / a_sel, 4) if a_sel else 0.0,
                    "fn_added": a_fn, "fp_added": a_sel - a_fn, "n_selected": a_sel,
                },
                "arm_b": {
                    "micro_orr": round(b_rec / b_M, 4) if b_M else 0.0,
                    "macro_orr": _orr_macro(b_recs, "B", B),
                    "candidate_precision": round(b_fn / b_sel, 4) if b_sel else 0.0,
                    "fn_added": b_fn, "fp_added": b_sel - b_fn, "n_selected": b_sel,
                },
                "arm_b_fp_by_source": dict(b_fp_by_src),
                "arm_b_fn_by_source": dict(b_fn_by_src),
            }

    # --------------------------------------------------------- C.4-C.6 ----
    # Source-level composition of the B=5 accepted set (Route-B top-10 overlap
    # vs reverse-1hop-only) for both FN recovery and the FP tail.
    source_anatomy: dict[str, dict] = {}
    for repo in repos:
        b_recs = [r for r in arm_b if r["repository"] == repo and r["schema_valid"]]
        fn_in_overlap = fn_in_consumer = fp_in_overlap = fp_in_consumer = 0
        n_tasks_with_fn_overlap = 0
        n_tasks_with_fn_consumer = 0
        for r in b_recs:
            t = by_cid[r["case_id"]]
            sel = set(r.get("per_b", {}).get(str(B_REF), {}).get("additions", []))
            routeb10 = set(reg_by_cid[r["case_id"]]["arm_a_tops"]["10"])
            fn_set = _fn_paths(t)
            for p in sel:
                if p in fn_set:
                    if p in routeb10:
                        fn_in_overlap += 1
                    else:
                        fn_in_consumer += 1
                else:
                    if p in routeb10:
                        fp_in_overlap += 1
                    else:
                        fp_in_consumer += 1
            if sel & fn_set & routeb10:
                n_tasks_with_fn_overlap += 1
            if sel & fn_set - routeb10:
                n_tasks_with_fn_consumer += 1
        source_anatomy[repo] = {
            "fn_added_route_b_top10": fn_in_overlap,
            "fn_added_consumer_only": fn_in_consumer,
            "fp_added_route_b_top10": fp_in_overlap,
            "fp_added_consumer_only": fp_in_consumer,
            "n_tasks_with_recovered_fn_in_overlap": n_tasks_with_fn_overlap,
            "n_tasks_with_recovered_fn_consumer_only": n_tasks_with_fn_consumer,
        }

    # --------------------------------------------------------- C.7/C.8 ----
    # Pool-size distribution + cap saturation.
    pool_size: dict[str, dict] = {}
    full_union_size: dict[str, dict] = {}
    for repo in repos:
        sizes = [s["pool_size"] for s in reg["sample"] if s["repository"] == repo]
        pool_size[repo] = {
            "min": min(sizes), "max": max(sizes),
            "n_at_cap": sum(1 for s in sizes if s == POOL_CAP),
            "n_tasks": len(sizes),
            "distribution": {str(k): v for k, v in sorted(Counter(sizes).items())},
        }
        fsizes = [len(_full_union(by_cid[s["case_id"]])) for s in reg["sample"] if s["repository"] == repo]
        full_union_size[repo] = {
            "min": min(fsizes), "max": max(fsizes),
            "mean": round(sum(fsizes) / len(fsizes), 1) if fsizes else 0,
            "p95": sorted(fsizes)[int(len(fsizes) * 0.95)] if fsizes else 0,
            "n_gt_40": sum(1 for s in fsizes if s > POOL_CAP),
            "n_gt_80": sum(1 for s in fsizes if s > 80),
            "distribution": {str(k): v for k, v in sorted(Counter(fsizes).items())},
        }

    # ------------------------------------------------------------- C.9 ----
    # Are useful FNs lost by the cap / by an inspection limit?
    cap_loss: dict[str, dict] = {}
    for repo in repos:
        total_fn = total_fn_capped = total_fn_full_union = 0
        lost_by_cap = 0
        for t in tasks:
            if t.repository != repo:
                continue
            s = reg_by_cid.get(t.case_id)
            if s is None:
                continue
            fn_set = _fn_paths(t)
            total_fn += len(fn_set)
            capped = set(s["pool"])
            full = set(_full_union(t))
            total_fn_capped += len(fn_set & capped)
            total_fn_full_union += len(fn_set & full)
            lost_by_cap += len(fn_set & (full - capped))
        cap_loss[repo] = {
            "total_fn_sampled_tasks": total_fn,
            "fn_in_capped_pool": total_fn_capped,
            "fn_in_full_union": total_fn_full_union,
            "fn_lost_by_cap": lost_by_cap,
            "fraction_fn_in_capped": round(total_fn_capped / total_fn, 4) if total_fn else 0.0,
        }

    # FN coverage as a function of the pool pre-order cap (mechanism diagnosis:
    # how much recovery is structurally reachable at a given cost bound).
    cap_coverage: dict[str, dict] = {}
    for cap in (40, 80, 120):
        cap_coverage[str(cap)] = {}
        for repo in repos:
            covered = 0
            total = 0
            for t in tasks:
                if t.repository != repo:
                    continue
                s = reg_by_cid.get(t.case_id)
                if s is None:
                    continue
                fn_set = _fn_paths(t)
                total += len(fn_set)
                top = set(_full_union(t)[:cap])
                covered += len(fn_set & top)
            cap_coverage[str(cap)][repo] = {
                "fn_covered": covered,
                "fraction_fn_covered": round(covered / total, 4) if total else 0.0,
            }

    # ------------------------------------------------------ C.10/C.11 ----
    # Valid vs schema-invalid incidence + failure taxonomy.
    schema_incidence: dict = {}
    for repo in repos:
        b_recs = [r for r in arm_b if r["repository"] == repo]
        schema_incidence[repo] = {
            "arm_b_total": len(b_recs),
            "arm_b_valid": sum(1 for r in b_recs if r["schema_valid"]),
            "arm_b_invalid": sum(1 for r in b_recs if not r["schema_valid"]),
        }
    taxonomy: Counter = Counter()
    finish_reasons: Counter = Counter()
    invalid_details: list[dict] = []
    for r in arm_b:
        if r["schema_valid"]:
            continue
        parsed = json.loads(r["raw_response"])
        finish_reasons[parsed["choices"][0].get("finish_reason", "?")] += 1
        content = parsed["choices"][0]["message"]["content"]
        pool = set(r.get("pool", []))
        try:
            obj = json.loads(content)
            items = obj.get("ordered") or []
            paths = [it.get("path") for it in items]
            dup = any(paths.count(p) > 1 for p in paths)
            nonpool = [p for p in paths if p not in pool]
            if nonpool:
                taxonomy["non_pool_path"] += 1
            elif dup:
                taxonomy["duplicate_path"] += 1
            else:
                taxonomy["other"] += 1
            invalid_details.append({
                "run_id": r["run_id"], "n_items": len(items),
                "n_nonpool": len(nonpool), "n_dup": sum(1 for p in paths if paths.count(p) > 1),
                "nonpool_sample": nonpool[:3],
            })
        except json.JSONDecodeError:
            taxonomy["content_parse_failure"] += 1
            invalid_details.append({"run_id": r["run_id"], "content_parse_failure": True})

    # --------------------------------------------------------- C.12 ----
    # Task-level heterogeneity at B=5 (per-task ORR delta ArmB - ArmA) + folds.
    task_heterogeneity: dict[str, dict] = {}
    fold_results: dict[str, dict] = {}
    for repo in repos:
        rows = []
        for r in b_recs if False else [r for r in arm_b if r["repository"] == repo]:
            t = by_cid[r["case_id"]]
            M = t.n_missed
            if M == 0:
                continue
            orr_b = len(r.get("per_b", {}).get(str(B_REF), {}).get("recovered", [])) / M
            a5 = a_by_cid.get((r["case_id"], B_REF))
            orr_a = len(a5["verifier_recovered"]) / M if a5 else 0.0
            rows.append({"case_id": r["case_id"], "n_missed": M, "orr_a5": round(orr_a, 4),
                         "orr_b5": round(orr_b, 4), "delta": round(orr_b - orr_a, 4)})
        task_heterogeneity[repo] = {
            "n_tasks": len(rows),
            "n_b_gt_a": sum(1 for x in rows if x["delta"] > 0),
            "n_b_lt_a": sum(1 for x in rows if x["delta"] < 0),
            "n_b_eq_a": sum(1 for x in rows if x["delta"] == 0),
            "delta_distribution": {
                "min": round(min(x["delta"] for x in rows), 4) if rows else None,
                "max": round(max(x["delta"] for x in rows), 4) if rows else None,
                "mean": round(sum(x["delta"] for x in rows) / len(rows), 4) if rows else None,
            },
            "rows": rows,
        }
        rng = random.Random(SEED)
        case_ids = [r["case_id"] for r in arm_b if r["repository"] == repo]
        rng.shuffle(case_ids)
        fold_frac: list[float] = []
        for k in range(K_FOLDS):
            fold_ids = set(case_ids[k::K_FOLDS])
            va: list[float] = []
            vb: list[float] = []
            for r in arm_a:
                if r["repository"] == repo and r["case_id"] in fold_ids and r["B"] == B_REF:
                    t = by_cid[r["case_id"]]
                    if t.n_missed == 0:
                        continue
                    va.append(len(r["verifier_recovered"]) / t.n_missed)
            for r in arm_b:
                if r["repository"] == repo and r["case_id"] in fold_ids:
                    t = by_cid[r["case_id"]]
                    if t.n_missed == 0:
                        continue
                    vb.append(len(r.get("per_b", {}).get(str(B_REF), {}).get("recovered", [])) / t.n_missed)
            ma = sum(va) / len(va) if va else 0.0
            mb = sum(vb) / len(vb) if vb else 0.0
            fold_frac.append(1.0 if mb > ma else (0.5 if mb == ma else 0.0))
        fold_results[repo] = {"b5_fold_direction_frac": [round(x, 2) for x in fold_frac],
                              "n_positive_folds": sum(1 for x in fold_frac if x >= 0.5)}

    # ------------------------------------------------------- C.13 ----
    # B=10 consistency (DEVELOPMENT motivation only; Saleor).
    b10_anatomy: dict[str, dict] = {}
    for repo in repos:
        b_recs = [r for r in arm_b if r["repository"] == repo]
        a10 = [r for r in arm_a if r["repository"] == repo and r["B"] == 10]
        a_sel = a_fn = 0
        a_rec = a_M = 0
        for r in a10:
            t = by_cid[r["case_id"]]
            sel = set(r["verifier_selected"])
            a_sel += len(sel)
            a_fn += len(sel & _fn_paths(t))
            a_rec += len(r["verifier_recovered"])
            a_M += t.n_missed
        b_sel = b_fn = b_rec = b_M = 0
        rows10 = []
        for r in b_recs:
            t = by_cid[r["case_id"]]
            per_b = r.get("per_b", {}).get("10", {})
            sel = set(per_b.get("additions", []))
            b_sel += len(sel)
            fns = sel & _fn_paths(t)
            b_fn += len(fns)
            b_rec += len(per_b.get("recovered", []))
            b_M += t.n_missed
            if t.n_missed:
                orr_a10 = 0.0
                a10r = a_by_cid.get((r["case_id"], 10))
                if a10r:
                    orr_a10 = len(a10r["verifier_recovered"]) / t.n_missed
                orr_b10 = len(per_b.get("recovered", [])) / t.n_missed
                rows10.append({"case_id": r["case_id"], "delta10": round(orr_b10 - orr_a10, 4)})
        b10_anatomy[repo] = {
            "arm_a": {"micro_orr": round(a_rec / a_M, 4) if a_M else 0.0,
                      "macro_orr": _orr_macro(a10, "A", 10),
                      "candidate_precision": round(a_fn / a_sel, 4) if a_sel else 0.0},
            "arm_b": {"micro_orr": round(b_rec / b_M, 4) if b_M else 0.0,
                      "macro_orr": _orr_macro(b_recs, "B", 10),
                      "candidate_precision": round(b_fn / b_sel, 4) if b_sel else 0.0},
            "n_tasks_delta_positive": sum(1 for x in rows10 if x["delta10"] > 0),
            "n_tasks_delta_nonpositive": sum(1 for x in rows10 if x["delta10"] <= 0),
            "n_valid_tasks": len(rows10),
            "delta_distribution": {
                "min": round(min(x["delta10"] for x in rows10), 4) if rows10 else None,
                "max": round(max(x["delta10"] for x in rows10), 4) if rows10 else None,
                "mean": round(sum(x["delta10"] for x in rows10) / len(rows10), 4) if rows10 else None,
            },
        }
        rng10 = random.Random(SEED)
        case_ids10 = [r["case_id"] for r in arm_b if r["repository"] == repo]
        rng10.shuffle(case_ids10)
        f10 = []
        for k in range(K_FOLDS):
            fold_ids = set(case_ids10[k::K_FOLDS])
            va = [len(a_by_cid[(r, 10)]["verifier_recovered"]) / by_cid[r].n_missed
                  for r in fold_ids if (r, 10) in a_by_cid and by_cid[r].n_missed]
            vb = [len(b_by_cid[r].get("per_b", {}).get("10", {}).get("recovered", [])) / by_cid[r].n_missed
                  for r in fold_ids if r in b_by_cid and by_cid[r].n_missed]
            ma = sum(va) / len(va) if va else 0.0
            mb = sum(vb) / len(vb) if vb else 0.0
            f10.append(1.0 if mb > ma else (0.5 if mb == ma else 0.0))
        b10_anatomy[repo]["b10_fold_direction_frac"] = [round(x, 2) for x in f10]
        b10_anatomy[repo]["n_positive_folds_b10"] = sum(1 for x in f10 if x >= 0.5)

    # ------------------------------------------------------------ D/E ----
    # RANK -> VERIFY -> VARIABLE ACCEPT feasibility (POST-HOC, exactly one
    # principled family). Verifier = frozen Arm A B=10 reconsider decisions on
    # the Route-B top-10 (a subset of the Arm B pool). Candidates outside the
    # Route-B top-10 have NO frozen verifier decision -> explicit insufficiency.
    # K is an inspection depth; accepted count is variable in [0, K].
    feasibility: dict = {"family": "ranked_top_K_AND_verifier_approved",
                          "label": "POST-HOC DEVELOPMENT FEASIBILITY - NOT CONFIRMATORY EVIDENCE",
                          "verifier_source": "frozen Arm A B=10 reconsider decisions (Route-B top-10 only)"}
    ks = (5, 10)
    feasibility["by_repo"] = {}
    for repo in repos:
        feasibility["by_repo"][repo] = {}
        for K in ks:
            sel = fn_sel = fp_sel = 0
            rec = 0
            M = 0
            accepted_per_task: list[int] = []
            n_accepted_tasks = 0
            fn_outside_verifier_coverage = 0
            for r in arm_b:
                if r["repository"] != repo or not r["schema_valid"]:
                    continue
                t = by_cid[r["case_id"]]
                fn_set = _fn_paths(t)
                M += t.n_missed
                ordered = r.get("ordered_selected", [])
                inspected = ordered[:K]
                a10 = a_by_cid.get((r["case_id"], 10))
                routeb10 = set(reg_by_cid[r["case_id"]]["arm_a_tops"]["10"])
                approved = set(a10["verifier_selected"]) if a10 else set()
                accepted = [p for p in inspected if p in routeb10 and p in approved]
                accepted_per_task.append(len(accepted))
                if accepted:
                    n_accepted_tasks += 1
                sel += len(accepted)
                fns = fn_set & set(accepted)
                fn_sel += len(fns)
                fp_sel += len(set(accepted) - fns)
                rec += len(fns)
                fn_outside_verifier_coverage += len(
                    [p for p in inspected if p in fn_set and p not in routeb10])
            feasibility["by_repo"][repo][f"K{K}"] = {
                "candidate_precision": round(fn_sel / sel, 4) if sel else 0.0,
                "macro_orr": round(rec / M, 4) if M else 0.0,
                "fn_accepted": fn_sel, "fp_accepted": fp_sel,
                "n_accepted": sel, "n_tasks": sum(1 for r in arm_b if r["repository"] == repo and r["schema_valid"]),
                "accepted_per_task_distribution": {
                    "min": min(accepted_per_task) if accepted_per_task else 0,
                    "max": max(accepted_per_task) if accepted_per_task else 0,
                    "mean": round(sum(accepted_per_task) / len(accepted_per_task), 3) if accepted_per_task else 0,
                    "n_tasks_with_gt0": n_accepted_tasks,
                },
                "fn_in_topK_but_outside_verifier_coverage": fn_outside_verifier_coverage,
            }
        # naive-union F1 under the rule at K=5/K=10
        for K in ks:
            tp = fp = fn = 0
            for r in arm_b:
                if r["repository"] != repo or not r["schema_valid"]:
                    continue
                t = by_cid[r["case_id"]]
                pos = set(t.proxy)
                fn_set = _fn_paths(t)
                ordered = r.get("ordered_selected", [])[:K]
                a10 = a_by_cid.get((r["case_id"], 10))
                routeb10 = set(reg_by_cid[r["case_id"]]["arm_a_tops"]["10"])
                approved = set(a10["verifier_selected"]) if a10 else set()
                accepted = set(p for p in ordered if p in routeb10 and p in approved)
                final = set(t.write_set) | accepted
                tp += len(final & pos)
                fp += len(final - pos)
                fn += len(pos - final)
            m = _f1(tp, fp, fn)
            feasibility["by_repo"][repo][f"K{K}"]["naive_union_f1"] = m["f1"]
            feasibility["by_repo"][repo][f"K{K}"]["naive_union_tp_fp_fn"] = {
                "tp": m["tp"], "fp": m["fp"], "fn": m["fn"]}
    feasibility["explicit_insufficiency"] = (
        "The frozen Arm A verifier only decided on Route-B top-10 candidates; "
        "it NEVER saw reverse-1hop-only candidates. Existing frozen records "
        "CANNOT assess a verifier on reverse-1hop-only candidates. Stated "
        "explicitly: NO such evidence exists in the 300-call record.")

    # Matched-subset comparison (the 27 valid Arm-B tasks per repo): sparse,
    # Arm A @B=5, Arm B @B=5, rule K=5/K=10 — same task denominator.
    feasibility["matched_subset_comparison"] = {}
    for repo in repos:
        valid_ids = {r["case_id"] for r in arm_b if r["repository"] == repo and r["schema_valid"]}
        subset = [t for t in tasks if t.case_id in valid_ids and t.repository == repo]
        b_recs = [r for r in arm_b if r["repository"] == repo and r["schema_valid"]]

        def _naive_f1(subset_tasks) -> dict:
            tp = fp = fn = 0
            for t in subset_tasks:
                pos = set(t.proxy)
                pred = set(t.write_set)
                tp += len(pred & pos)
                fp += len(pred - pos)
                fn += len(pos - pred)
            return _f1(tp, fp, fn)

        def _arm_a_f1(budget: int, recs) -> dict:
            tp = fp = fn = 0
            for r in recs:
                t = by_cid[r["case_id"]]
                pos = set(t.proxy)
                a = a_by_cid.get((r["case_id"], budget))
                sel = set(a["verifier_selected"]) if a else set()
                final = set(t.write_set) | sel
                tp += len(final & pos)
                fp += len(final - pos)
                fn += len(pos - final)
            return _f1(tp, fp, fn)

        def _arm_b_f1(budget: int, recs) -> dict:
            tp = fp = fn = 0
            for r in recs:
                t = by_cid[r["case_id"]]
                pos = set(t.proxy)
                sel = set(r.get("per_b", {}).get(str(budget), {}).get("additions", []))
                final = set(t.write_set) | sel
                tp += len(final & pos)
                fp += len(final - pos)
                fn += len(pos - final)
            return _f1(tp, fp, fn)

        sparse = _naive_f1(subset)
        a5 = _arm_a_f1(B_REF, b_recs)
        b5 = _arm_b_f1(B_REF, b_recs)
        feasibility["matched_subset_comparison"][repo] = {
            "n_valid_tasks": len(b_recs),
            "sparse_f1": sparse["f1"],
            "arm_a_b5_f1": a5["f1"],
            "arm_b_b5_f1": b5["f1"],
        }
        for K in ks:
            r = feasibility["by_repo"][repo][f"K{K}"]
            feasibility["matched_subset_comparison"][repo][f"rule_K{K}_f1"] = r["naive_union_f1"]

    # Frozen-verifier strength summary: the Arm A B=10 approval decisions that
    # the feasibility rule reuses as its acceptance layer.
    feasibility["frozen_verifier_strength_b10"] = {}
    for repo in repos:
        a10 = [r for r in arm_a if r["repository"] == repo and r["B"] == 10]
        n_approved = 0
        n_approved_fn = 0
        n_routeb10_fn = 0
        for r in a10:
            t = by_cid[r["case_id"]]
            fn_set = _fn_paths(t)
            top = set(r["top_candidates"])
            sel = set(r["verifier_selected"])
            n_approved += len(sel)
            n_approved_fn += len(sel & fn_set)
            n_routeb10_fn += len(top & fn_set)
        feasibility["frozen_verifier_strength_b10"][repo] = {
            "n_approved": n_approved,
            "n_approved_fn": n_approved_fn,
            "approval_candidate_precision": round(n_approved_fn / n_approved, 4) if n_approved else 0.0,
            "routeb10_fn_total": n_routeb10_fn,
            "fn_recovery_among_routeb10": round(n_approved_fn / n_routeb10_fn, 4) if n_routeb10_fn else 0.0,
        }

    # ------------------------------------------------------------ H ----
    sample_availability: dict = {}
    for repo in repos:
        eligible = [t.case_id for t in tasks if t.repository == repo and t.n_missed >= 1 and t.omitted_size >= 5]
        used = [s["case_id"] for s in reg["sample"] if s["repository"] == repo]
        remaining = sorted(set(eligible) - set(used))
        sample_availability[repo] = {
            "eligible": len(eligible), "used_stage4": len(used), "remaining_fresh": len(remaining),
        }

    # ------------------------------------------------------------ J ----
    cost_basis: dict = {}
    for repo in repos:
        a_recs = [r for r in arm_a if r["repository"] == repo]
        b_recs = [r for r in arm_b if r["repository"] == repo]
        def stats(recs):
            tot = [r["total_tokens"] for r in recs]
            comp = [r["completion_tokens"] for r in recs]
            cost = [r["api_cost"] for r in recs]
            return {
                "n": len(recs),
                "total_tokens": sum(tot),
                "total_cost_usd": round(sum(cost), 6),
                "mean_total_tokens": round(sum(tot) / len(tot), 1) if tot else 0,
                "p95_total_tokens": round(sorted(tot)[int(len(tot) * 0.95)] if tot else 0, 1),
                "max_total_tokens": max(tot) if tot else 0,
                "mean_completion_tokens": round(sum(comp) / len(comp), 1) if comp else 0,
                "mean_cost_usd": round(sum(cost) / len(cost), 6) if cost else 0,
                "max_cost_usd": max(cost) if cost else 0,
            }
        cost_basis[repo] = {"arm_a": stats(a_recs), "arm_b": stats(b_recs)}

    out = {
        "study_id": "precision-safe-acceptance-feasibility-2026-09-18",
        "tier": "T3 (zero-API development analysis over frozen Stage-4 records)",
        "model_authoring_agent": "openrouter/deepseek/deepseek-v4-flash-0731",
        "stage4_evidence_verification": b_verify,
        "arm_b_rank_position_precision": rank_precision,
        "per_b_anatomy": per_b_anatomy,
        "source_anatomy_b5": source_anatomy,
        "pool_size": pool_size,
        "full_union_size": full_union_size,
        "cap_loss": cap_loss,
        "cap_coverage": cap_coverage,
        "schema_incidence": schema_incidence,
        "schema_invalid_taxonomy": dict(taxonomy),
        "schema_invalid_finish_reasons": dict(finish_reasons),
        "schema_invalid_details": invalid_details,
        "task_heterogeneity_b5": {repo: {k: v for k, v in task_heterogeneity[repo].items() if k != "rows"}
                                  for repo in repos},
        "fold_results_b5": fold_results,
        "b10_anatomy": b10_anatomy,
        "feasibility": feasibility,
        "future_sample_availability": sample_availability,
        "cost_basis": cost_basis,
        "stage4_verdict": "BOUNDED_SEMANTIC_NEGATIVE_FROZEN (unchanged; not reinterpreted)",
    }
    return out


def main() -> int:
    out = compute()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("wrote", OUT_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
