# ruff: noqa: E501, N803, N806
#!/usr/bin/env python3
# ruff: noqa: E501
"""Oracle F1 ceilings + budget surface — Sections 2-3 of the Oracle-gap mission.

Computes, per repository (djangoCMS DEV, Saleor DEV), deterministic oracle
upper-bound surfaces:

  A. ORACLE-ADD      : perfect add of omitted true positives, per-task budget A
                       in {0,1,2,3,5,10,ALL}, zero FPs added.
  B. ORACLE-DROP     : perfect removal of Sparse FPs, per-task budget D in
                       {0,1,2,3,5,10,ALL}, zero TPs removed.
  C. ORACLE-BIDIRECTIONAL: perfect add + perfect drop over the A x D grid.

  D. F1 reachability for targets {0.50,0.60,0.70,0.80,0.85,0.90}.

Also computes Route-B add-only reference (composite-ranked top-B) and the
Sparse baseline. ZERO API; DEVELOPMENT only; the spent djangoCMS INTERNAL_TEST
is reported separately (POST-HOC) in another script.

Tier: T3.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from scripts.oracle_gap_data import DevTask, load_all  # noqa: E402

ADD_GRID = (0, 1, 2, 3, 5, 10, None)  # None == ALL
DROP_GRID = (0, 1, 2, 3, 5, 10, None)
TARGETS = (0.50, 0.60, 0.70, 0.80, 0.85, 0.90)
GRID_LABELS = {0: "0", 1: "1", 2: "2", 3: "3", 5: "5", 10: "10", None: "ALL"}


def per_task_counts(tasks: list[DevTask]) -> list[dict]:
    """Per-task Sparse counts: tp, fp, fn, proxy_size, write_set_size."""
    out = []
    for t in tasks:
        pred = t.write_set
        pos = t.proxy
        tp = len(pred & pos)
        fp = len(pred - pos)
        fn = len(pos - pred)
        out.append({"case_id": t.case_id, "tp": tp, "fp": fp, "fn": fn,
                    "proxy_size": len(pos), "write_set_size": len(pred),
                    "n_missed": fn})
    return out


def _f1(tp: int, fp: int, fn: int) -> float:
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    return 2 * p * r / (p + r) if (p + r) else 0.0


def _metrics(tp: int, fp: int, fn: int) -> dict:
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": round(p, 4),
            "recall": round(r, 4), "f1": round(_f1(tp, fp, fn), 4),
            "fnr": round(fn / (tp + fn), 4) if (tp + fn) else 0.0,
            "n_positives": tp + fn}


def oracle_add(counts: list[dict], A) -> dict:
    tp = sum(c["tp"] for c in counts)
    fp = sum(c["fp"] for c in counts)
    fn = sum(c["fn"] for c in counts)
    for c in counts:
        add = c["fn"] if A is None else min(A, c["fn"])
        tp += add
        fn -= add
    return _metrics(tp, fp, fn)


def oracle_drop(counts: list[dict], D) -> dict:
    tp = sum(c["tp"] for c in counts)
    fp = sum(c["fp"] for c in counts)
    fn = sum(c["fn"] for c in counts)
    for c in counts:
        drop = c["fp"] if D is None else min(D, c["fp"])
        fp -= drop
    return _metrics(tp, fp, fn)


def oracle_bi(counts: list[dict], A, D) -> dict:
    tp = sum(c["tp"] for c in counts)
    fp = sum(c["fp"] for c in counts)
    fn = sum(c["fn"] for c in counts)
    n_add = n_drop = 0
    for c in counts:
        add = c["fn"] if A is None else min(A, c["fn"])
        drop = c["fp"] if D is None else min(D, c["fp"])
        tp += add
        fn -= add
        fp -= drop
        n_add += add
        n_drop += drop
    m = _metrics(tp, fp, fn)
    m["n_add_inspected"] = n_add
    m["n_drop_inspected"] = n_drop
    m["mean_inspections_per_task"] = round((n_add + n_drop) / len(counts), 4) if counts else 0.0
    return m


def route_b_add_only(tasks: list[DevTask], B: int) -> dict:
    """Composite-ranked add-only: final set = Sparse write set ∪ top-B omitted
    (composite rank). Uses observable composite only."""
    tp = fp = fn = 0
    for t in tasks:
        pred = set(t.write_set)
        # top-B omitted candidates by composite desc
        omitted = [c for c in t.candidates if c["path"] not in pred]
        omitted.sort(key=lambda c: (-c["composite"], c["path"]))
        added = {c["path"] for c in omitted[:B]}
        final = pred | added
        pos = t.proxy
        tp += len(final & pos)
        fp += len(final - pos)
        fn += len(pos - final)
    return _metrics(tp, fp, fn)


def reachability(counts: list[dict]) -> dict:
    """For each target F1, min oracle add budget (drop=0) / drop budget (add=0)
    / smallest (A,D) pair reaching it; None if unreachable even at ALL/ALL."""
    out = {}
    alladd = oracle_add(counts, None)
    alldrop = oracle_drop(counts, None)
    allbi = oracle_bi(counts, None, None)
    for target in TARGETS:
        entry = {"target": target,
                 "add_only": None, "drop_only": None, "bidirectional": None,
                 "reachable_add": alladd["f1"] >= target,
                 "reachable_drop": alldrop["f1"] >= target,
                 "reachable_bi": allbi["f1"] >= target}
        # add-only minimal A
        for A in ADD_GRID:
            if oracle_add(counts, A)["f1"] >= target:
                entry["add_only"] = GRID_LABELS[A]
                break
        # drop-only minimal D
        for D in DROP_GRID:
            if oracle_drop(counts, D)["f1"] >= target:
                entry["drop_only"] = GRID_LABELS[D]
                break
        # bidirectional minimal total inspections (A+D); ALL treated as unbounded
        best = None
        for A in ADD_GRID:
            for D in DROP_GRID:
                m = oracle_bi(counts, A, D)
                if m["f1"] >= target:
                    mean_insp = m["mean_inspections_per_task"]
                    if best is None or mean_insp < best[0]:
                        best = (mean_insp, GRID_LABELS[A], GRID_LABELS[D], m["f1"])
        entry["bidirectional"] = {"min_mean_inspections_per_task": best[0] if best else None,
                                  "A": best[1] if best else None,
                                  "D": best[2] if best else None,
                                  "f1_at_min": best[3] if best else None} if best else None
        out[target] = entry
    return out


def main() -> int:
    tasks = load_all()
    dc = [t for t in tasks if t.repository == "djangocms"]
    sc = [t for t in tasks if t.repository == "saleor"]

    result: dict = {
        "package": "oracle_gap_v1",
        "analysis_date": "2026-09-18",
        "tier": "T3",
        "note": "Deterministic oracle upper bounds on DEVELOPMENT. ZERO API. Not a method budget; INTERNAL_TEST never used for selection.",
        "repos": {},
    }
    for repo_name, ts in (("djangocms_dev", dc), ("saleor_dev", sc)):
        counts = per_task_counts(ts)
        sparse = _metrics(sum(c["tp"] for c in counts), sum(c["fp"] for c in counts), sum(c["fn"] for c in counts))
        add_surface = {GRID_LABELS[A]: oracle_add(counts, A) for A in ADD_GRID}
        drop_surface = {GRID_LABELS[D]: oracle_drop(counts, D) for D in DROP_GRID}
        bi_surface = {}
        for A in ADD_GRID:
            for D in DROP_GRID:
                m = oracle_bi(counts, A, D)
                bi_surface[f"A={GRID_LABELS[A]},D={GRID_LABELS[D]}"] = m
        route_b = {B: route_b_add_only(ts, B) for B in (1, 3, 5, 10)}
        result["repos"][repo_name] = {
            "n_tasks": len(ts),
            "sparse_baseline": sparse,
            "oracle_add": add_surface,
            "oracle_drop": drop_surface,
            "oracle_bidirectional": bi_surface,
            "route_b_add_only_composite": route_b,
            "reachability": reachability(counts),
        }

    out_path = PROJECT_DIR / "reports" / "oracle_f1_ceiling_and_budget_surface.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    # ---- console summary ----
    for repo_name in ("djangocms_dev", "saleor_dev"):
        r = result["repos"][repo_name]
        print(f"\n=== {repo_name} (n={r['n_tasks']}) ===")
        print("Sparse baseline:", json.dumps(r["sparse_baseline"]))
        print("Route-B add-only composite B=5:", json.dumps(r["route_b_add_only_composite"][5]))
        print("Oracle-Add ALL:", json.dumps(r["oracle_add"]["ALL"]))
        print("Oracle-Drop ALL:", json.dumps(r["oracle_drop"]["ALL"]))
        print("Oracle-Bi A=ALL,D=ALL:", json.dumps(r["oracle_bidirectional"]["A=ALL,D=ALL"]))
        print("Reachability (target: add-only / drop-only / bi):")
        for tgt, e in r["reachability"].items():
            b = e["bidirectional"]
            print(f"  F1>={tgt}: add={e['add_only']} drop={e['drop_only']} bi={'A='+str(b['A'])+' D='+str(b['D'])+' mean_insp='+str(b['min_mean_inspections_per_task']) if b else 'UNREACHABLE'}")

    print("\noutput:", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
