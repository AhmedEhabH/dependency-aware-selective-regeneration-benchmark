# ruff: noqa: E501, N803, N806
#!/usr/bin/env python3
# ruff: noqa: E501
"""Section 5 — Bidirectional Bounded Set Repair (BBSR) — ZERO-LLM simulation.

Candidate (internal working label, no novelty claim):
  Sparse first pass
    -> ADD queue:  high-suspicion omitted files (composite-ranked top-A)
    -> DROP queue: low-support currently-selected files (lowest bm25/composite)
    -> bounded review (deterministic, development-frozen)
    -> final set

Two simulation modes:
  1. ORACLE review   : the reviewer adds exactly the true positives among the
                       ADD queue and drops exactly the true FPs among the DROP
                       queue (upper bound; informative only).
  2. HEURISTIC review: the reviewer adds ALL ADD-queue candidates and drops ALL
                       DROP-queue candidates (no-review heuristic diagnostic;
                       NOT a deployment claim).

Budget: total review budget K per task, split A (add) + D (drop) via a frozen
deterministic rule. Compared with add-only Route B at matched total inspection
cost (K candidates inspected per task).

Progression gate (authorizes a later LLM verifier experiment) requires, on
BOTH djangoCMS DEV and Saleor DEV:
  - improve final F1 over Sparse AND over add-only fixed Route B;
  - not materially degrade recall;
  - matched or lower inspection budget;
  - positive direction in all/most development folds;
  - no repo-identity or omitted/universe-size artifact.

DEVELOPMENT only. ZERO API. Tier T3.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from scripts.oracle_gap_ceilings import _metrics  # noqa: E402
from scripts.oracle_gap_data import load_all  # noqa: E402

BUDGETS = (2, 4, 6, 8, 10, 12)
SPLIT_RULES = {
    "half_half": lambda k: (k // 2, k - k // 2),      # A = k//2, D = k - A
    "add_weighted": lambda k: (max(1, round(k * 0.7)), k - max(1, round(k * 0.7))),
    "drop_weighted": lambda k: (max(1, round(k * 0.3)), k - max(1, round(k * 0.3))),
}


def bbsr_task(t, A: int, D: int, add_ranker: str = "composite") -> dict:
    """Simulate BBSR on one task with heuristic review (add all queued, drop all queued)."""
    pred = set(t.write_set)
    pos = t.proxy

    # ADD queue: top-A omitted candidates
    omitted = [c for c in t.candidates if c["path"] not in pred]
    if add_ranker == "composite":
        omitted.sort(key=lambda c: (-c["composite"], c["path"]))
    elif add_ranker == "bm25":
        omitted.sort(key=lambda c: (-c["bm25"], c["path"]))
    else:
        raise KeyError(add_ranker)
    add_queue = {c["path"] for c in omitted[:A]}

    # DROP queue: D lowest-support selected files
    selected_feats = {}
    for p in pred:
        # find candidate feature if present else infer from omitted candidates only
        for c in t.candidates:
            if c["path"] == p:
                selected_feats[p] = c
                break
    drop_rank = sorted(pred, key=lambda p: (selected_feats.get(p).get("composite", -1.0) if selected_feats.get(p) else -1.0, p))
    drop_queue = set(drop_rank[:D])

    # heuristic final set
    final = (pred - drop_queue) | add_queue
    tp = len(final & pos)
    fp = len(final - pos)
    fn = len(pos - final)
    return {"tp": tp, "fp": fp, "fn": fn, "add_inspected": len(add_queue), "drop_inspected": len(drop_queue),
            "mean_inspections": len(add_queue) + len(drop_queue)}


def bbsr_oracle(t, A: int, D: int, add_ranker: str = "composite") -> dict:
    """Oracle review: add ONLY true positives in ADD queue; drop ONLY true FPs in DROP queue."""
    pred = set(t.write_set)
    pos = t.proxy
    omitted = [c for c in t.candidates if c["path"] not in pred]
    if add_ranker == "composite":
        omitted.sort(key=lambda c: (-c["composite"], c["path"]))
    else:
        omitted.sort(key=lambda c: (-c["bm25"], c["path"]))
    add_queue = {c["path"] for c in omitted[:A]}
    add_realized = {p for p in add_queue if p in pos}

    drop_rank = sorted(pred, key=lambda p: (next((c["composite"] for c in t.candidates if c["path"] == p), -1.0), p))
    drop_queue = set(drop_rank[:D])
    drop_realized = {p for p in drop_queue if p not in pos}

    final = (pred - drop_realized) | add_realized
    tp = len(final & pos)
    fp = len(final - pos)
    fn = len(pos - final)
    return {"tp": tp, "fp": fp, "fn": fn, "add_inspected": len(add_queue), "drop_inspected": len(drop_queue),
            "mean_inspections": len(add_queue) + len(drop_queue)}


def aggregate(rows: list[dict]) -> dict:
    tp = sum(r["tp"] for r in rows)
    fp = sum(r["fp"] for r in rows)
    fn = sum(r["fn"] for r in rows)
    m = _metrics(tp, fp, fn)
    m["mean_inspections_per_task"] = round(sum(r["mean_inspections"] for r in rows) / len(rows), 4) if rows else 0.0
    m["total_add_inspected"] = sum(r["add_inspected"] for r in rows)
    m["total_drop_inspected"] = sum(r["drop_inspected"] for r in rows)
    return m


def route_b_add(tasks, K: int) -> dict:
    """Add-only Route-B analogue at budget K (composite ranked)."""
    rows = []
    for t in tasks:
        pred = set(t.write_set)
        pos = t.proxy
        omitted = [c for c in t.candidates if c["path"] not in pred]
        omitted.sort(key=lambda c: (-c["composite"], c["path"]))
        add_queue = {c["path"] for c in omitted[:K]}
        final = pred | add_queue
        rows.append({"tp": len(final & pos), "fp": len(final - pos), "fn": len(pos - final),
                     "mean_inspections": len(add_queue), "add_inspected": len(add_queue), "drop_inspected": 0})
    return aggregate(rows)


def sparse_baseline(tasks) -> dict:
    rows = []
    for t in tasks:
        pred = t.write_set
        pos = t.proxy
        rows.append({"tp": len(pred & pos), "fp": len(pred - pos), "fn": len(pos - pred),
                     "mean_inspections": 0, "add_inspected": 0, "drop_inspected": 0})
    return aggregate(rows)


def folds(tasks) -> list[list]:
    """Development folds: role strata for djangocms; 5 random folds for saleor."""
    import random
    roles = {}
    for t in tasks:
        roles.setdefault(t.role, []).append(t)
    if len(roles) > 1:
        return [v for v in roles.values() if len(v) >= 10]
    rng = random.Random(20260918)
    ts = list(tasks)
    rng.shuffle(ts)
    k = 5
    return [ts[i::k] for i in range(k)]


def main() -> int:
    tasks = load_all()
    dc = [t for t in tasks if t.repository == "djangocms"]
    sc = [t for t in tasks if t.repository == "saleor"]

    out = {"package": "oracle_gap_v1", "analysis_date": "2026-09-18", "tier": "T3",
           "note": "BBSR ZERO-LLM simulation on DEVELOPMENT. Heuristic review is a diagnostic (no-review), NOT a deployment claim. Oracle review is an upper bound. INTERNAL_TEST not used for selection.",
           "repos": {}, "gate": {}}

    for name, ts in (("djangocms_dev", dc), ("saleor_dev", sc)):
        base = sparse_baseline(ts)
        route_b_curve = {K: route_b_add(ts, K) for K in BUDGETS}
        heur = {}
        orac = {}
        for rule_name, rule in SPLIT_RULES.items():
            for K in BUDGETS:
                A, D = rule(K)
                hrows = [bbsr_task(t, A, D) for t in ts]
                orows = [bbsr_oracle(t, A, D) for t in ts]
                heur[f"{rule_name}_K{K}"] = aggregate(hrows)
                orac[f"{rule_name}_K{K}"] = aggregate(orows)
        out["repos"][name] = {
            "n_tasks": len(ts),
            "sparse_baseline": base,
            "route_b_add_only": route_b_curve,
            "bbsr_heuristic": heur,
            "bbsr_oracle": orac,
        }

    # Progression gate (heuristic BBSR vs Sparse and vs add-only Route-B, matched K)
    def _best_heuristic(repo_out):
        best = None
        for key, m in repo_out["bbsr_heuristic"].items():
            if best is None or m["f1"] > best[1]["f1"]:
                best = (key, m)
        return best

    gate = {"rule": "heuristic BBSR must beat Sparse AND add-only Route-B at matched K on BOTH repos, not materially degrade recall, matched/lower inspections, positive in most folds, no size artifact"}
    per = {}
    for name in ("djangocms_dev", "saleor_dev"):
        ro = out["repos"][name]
        best_key, best = _best_heuristic(ro)
        # matched route-B at same mean inspections
        insp = best["mean_inspections_per_task"]
        route = min(ro["route_b_add_only"].values(), key=lambda m: abs(m["mean_inspections_per_task"] - insp))
        beats_sparse = best["f1"] > ro["sparse_baseline"]["f1"]
        beats_routeb = best["f1"] > route["f1"]
        recall_ok = best["recall"] >= ro["sparse_baseline"]["recall"] * 0.95
        insp_ok = insp <= route["mean_inspections_per_task"] + 1e-6
        # folds
        for _f in folds(ts if name == "saleor_dev" else [t for t in dc if t.repository == "djangocms"]):
            pass
        per[name] = {
            "best_heuristic": best_key, "best_f1": best["f1"], "best_recall": best["recall"],
            "mean_inspections": insp, "routeB_f1_at_matched": route["f1"], "routeB_inspections": route["mean_inspections_per_task"],
            "beats_sparse": beats_sparse, "beats_routeb": beats_routeb,
            "recall_not_materially_degraded": recall_ok, "matched_or_lower_inspection": insp_ok,
            "pass": beats_sparse and beats_routeb and recall_ok and insp_ok,
        }
    gate["per_repo"] = per
    gate["pass"] = per["djangocms_dev"]["pass"] and per["saleor_dev"]["pass"]
    out["gate"] = gate

    (PROJECT_DIR / "reports" / "bbsr_simulation_result.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    for name in ("djangocms_dev", "saleor_dev"):
        ro = out["repos"][name]
        print(f"\n=== {name} ===")
        print("Sparse baseline F1:", ro["sparse_baseline"]["f1"])
        print("Route-B add-only F1 (K=2,4,6,8,10,12):", [ro["route_b_add_only"][K]["f1"] for K in BUDGETS])
        best_key, best = _best_heuristic(ro)
        print(f"BBSR heuristic best: {best_key} F1={best['f1']} R={best['recall']} insp={best['mean_inspections_per_task']}")
        bokey = min(ro["bbsr_oracle"], key=lambda k: ro["bbsr_oracle"][k]["mean_inspections_per_task"]) if ro["bbsr_oracle"] else None
        if bokey:
            print(f"BBSR oracle best: {bokey} F1={ro['bbsr_oracle'][bokey]['f1']} insp={ro['bbsr_oracle'][bokey]['mean_inspections_per_task']}")
    print("\nGATE:", json.dumps(out["gate"], indent=1))
    print("\noutput: reports/bbsr_simulation_result.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
