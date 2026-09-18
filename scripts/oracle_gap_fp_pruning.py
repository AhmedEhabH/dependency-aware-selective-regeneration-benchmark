# ruff: noqa: E501, N803
#!/usr/bin/env python3
# ruff: noqa: E501
"""Section 4 — Simple false-positive pruning feasibility (ZERO LLM, DEVELOPMENT).

For every file the Sparse first pass SELECTED (the write set), we reconstruct
ONLY observable parent-visible features (intent-bm25, path-token overlap,
graph-neighbor support, intent-overlap) and ask whether low-scoring selected
files are more likely to be FPs.

Rankers (all observable, no hidden proxy):
  - bm25 (lowest first)  -> drop candidate
  - composite (bm25+graph)
  - path-token overlap
  - graph-neighbor
  - analytic random control
  - oracle-drop upper bound

For drop budgets D in {1,2,3,5}:
  - precision@flagged (share of flagged that are FPs)
  - TP-loss risk (share of flagged that are TPs)
  - final P/R/F1 if the reviewer dropped ONLY true FPs (oracle review)

DEVELOPMENT only. No neural/RL. ZERO API.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from benchmark.p2.tasks import (  # noqa: E402
    SALEOR_DATASET,
    V1_DATASET,
    V1_RECORDS,
    V2_DATASET,
)
from scripts.route_b_v2_robustness import (  # noqa: E402
    BM25Index,
    MetadataCorpus,
    _adjacency,
    compute_seed_paths,
    load_case,
    rank_path_token,
    tokenize,
)

DROP_BUDGETS = (1, 2, 3, 5)


_CASE_CACHE: dict[tuple[str, str], dict] = {}
_CASE_FEAT_CACHE: dict[str, dict] = {}


def selected_file_features(cid: str, dataset: Path, write_set: frozenset[str]) -> dict[str, dict]:
    """Observable features for the SELECTED files (bm25, tokens, graph support)."""
    cache_key = f"{cid}|{dataset.name}"
    if cache_key in _CASE_FEAT_CACHE:
        return {p: _CASE_FEAT_CACHE[cache_key].get(p) for p in write_set if p in _CASE_FEAT_CACHE[cache_key]}
    case = load_case(cid, dataset)
    records = {str(r["path"]): r for r in case["records"]}
    mcorpus = MetadataCorpus(parent_commit=case["parent_commit"], candidate_records=case["records"])
    index = BM25Index(mcorpus.texts)
    qt = tokenize(case["intent_text"])
    bm25_scores = {doc: index.score(doc, qt) for doc in index.doc_ids}
    max_bm25 = max(bm25_scores.values()) if bm25_scores else 1.0
    paths = case["paths"]
    pt_rank = rank_path_token(
        intent_text=case["intent_text"], candidate_paths=paths,
        candidate_records=case["records"], k=len(paths),
    )
    {p: i for i, p in enumerate(pt_rank)}
    seeds = compute_seed_paths(
        intent_text=case["intent_text"], candidate_paths=paths,
        candidate_records=case["records"],
    ).seed_paths
    adj = _adjacency(case["graph_edges"])
    neighbors: set[str] = set()
    for s in set(seeds):
        neighbors.update(adj.get(s, set()))
    intent_tokens = set(tokenize(case["intent_text"]))
    sorted_bm25 = sorted(bm25_scores.get(q, 0.0) for q in paths)
    bm25_rank_map: dict[str, int] = {}
    for p in write_set:
        bm25_rank_map[p] = sorted_bm25.index(bm25_scores.get(p, 0.0)) if paths else 0

    feats = {}
    for p in write_set:
        if p not in records:
            continue
        rec = records[p]
        path_tokens = set(str(p).replace("/", " ").replace(".", " ").split())
        module = str(rec.get("module", ""))
        intent_hit = bool((path_tokens | set(module.split())) & intent_tokens)
        nb = 1.0 if p in neighbors else 0.0
        bm = bm25_scores.get(p, 0.0) / max_bm25 if max_bm25 else 0.0
        feats[p] = {
            "bm25": bm,
            "pt_overlap": int(intent_hit),
            "graph_neighbor": nb,
            "composite": bm + nb,
            "bm25_rank_pct": (bm25_rank_map.get(p, len(paths)) + 1) / len(paths) if paths else 1.0,
        }
    _CASE_FEAT_CACHE[cache_key] = feats
    return feats


def build_selected_rows(tasks) -> list[dict]:
    """One row per selected file: features + evaluation-only is_fp."""
    rows = []
    for t in tasks:
        if not t.write_set:
            continue
        dataset = None
        # determine dataset by repo
        if t.repository == "saleor":
            dataset = SALEOR_DATASET
        else:
            # djangocms: V1 or V2
            v1_ids = {r["case_id"] for r in _load_records(V1_RECORDS)}
            dataset = V1_DATASET if t.case_id in v1_ids else V2_DATASET
        feats = selected_file_features(t.case_id, dataset, t.write_set)
        for path in sorted(t.write_set):
            f = feats.get(path)
            if f is None:
                continue
            is_fp = int(path not in t.proxy)
            rows.append({"case_id": t.case_id, "repository": t.repository, "path": path,
                         "is_fp": is_fp, "is_tp": 1 - is_fp, **f})
    return rows


def _load_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def rank_selected(rows: list[dict], key: str) -> list[dict]:
    """Sort selected-file rows by feature ascending (lowest first = most droppable)."""
    return sorted(rows, key=lambda r: (r[key], r["case_id"], r["path"]))


def evaluate_drop(rows: list[dict], D: int, order: list[dict], task_map: dict) -> dict:  # noqa: ARG001 (rows unused; order drives)
    """Drop the D lowest-scoring selected files (per task)."""
    # group by case
    by_case: dict[str, list[dict]] = {}
    for r in order:
        by_case.setdefault(r["case_id"], []).append(r)
    total_flagged_fp = total_flagged = 0
    dropped_tp = 0
    # final-set simulation: start from sparse set per task, drop flagged
    tp = fp = fn = 0
    for cid, rows_c in by_case.items():
        t = task_map[cid]
        flagged = rows_c[:D]
        flagged_fp = sum(1 for r in flagged if r["is_fp"])
        flagged_tp = sum(1 for r in flagged if r["is_tp"])
        total_flagged += len(flagged)
        total_flagged_fp += flagged_fp
        dropped_tp += flagged_tp
        # final set after drop
        drop_paths = {r["path"] for r in flagged}
        final = t.write_set - drop_paths
        pos = t.proxy
        tp += len(final & pos)
        fp += len(final - pos)
        fn += len(pos - final)
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return {
        "D": D,
        "n_flagged": total_flagged,
        "n_flagged_fp": total_flagged_fp,
        "flagged_precision": round(total_flagged_fp / total_flagged, 4) if total_flagged else None,
        "tp_loss_risk": round(dropped_tp / total_flagged, 4) if total_flagged else None,
        "final_tp": tp, "final_fp": fp, "final_fn": fn,
        "final_precision": round(p, 4), "final_recall": round(r, 4), "final_f1": round(f1, 4),
    }


def oracle_drop_upper(tasks, D: int) -> dict:
    """Oracle: drop ONLY true FPs, D per task. Upper bound."""
    tp = fp = fn = 0
    for t in tasks:
        fps = sorted(t.write_set - t.proxy)
        drop = set(fps[:D])
        final = t.write_set - drop
        pos = t.proxy
        tp += len(final & pos)
        fp += len(final - pos)
        fn += len(pos - final)
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return {"D": D, "final_tp": tp, "final_fp": fp, "final_fn": fn, "final_precision": round(p, 4), "final_recall": round(r, 4), "final_f1": round(f1, 4)}


def main() -> int:
    from scripts.oracle_gap_data import load_all
    tasks = load_all()
    dc = [t for t in tasks if t.repository == "djangocms"]
    sc = [t for t in tasks if t.repository == "saleor"]

    out = {"package": "oracle_gap_v1", "analysis_date": "2026-09-18", "tier": "T3",
           "note": "Observable FP-pruning feasibility on DEVELOPMENT. Features are parent-visible only; no hidden proxy. Rankers are diagnostic, not deployment claims.", "repos": {}}
    for name, ts in (("djangocms_dev", dc), ("saleor_dev", sc)):
        rows = build_selected_rows(ts)
        print(f"[fp-pruning] {name}: {len(rows)} selected-file rows", flush=True)
        total_fp = sum(r["is_fp"] for r in rows)
        total = len(rows)
        rng = random.Random(20260918)
        random_rows = list(rows)
        rng.shuffle(random_rows)
        task_map = {t.case_id: t for t in ts}
        repo_out = {
            "n_selected_files": total,
            "n_fp": total_fp,
            "fp_rate": round(total_fp / total, 4) if total else 0.0,
            "rankers": {},
        }
        for key in ("bm25", "composite", "pt_overlap", "graph_neighbor"):
            order = rank_selected(rows, key)
            repo_out["rankers"][key] = {str(D): evaluate_drop(rows, D, order, task_map) for D in DROP_BUDGETS}
        repo_out["rankers"]["random"] = {str(D): evaluate_drop(rows, D, random_rows, task_map) for D in DROP_BUDGETS}
        repo_out["oracle_drop_upper"] = {str(D): oracle_drop_upper(ts, D) for D in DROP_BUDGETS}
        out["repos"][name] = repo_out

    (PROJECT_DIR / "reports" / "selected_set_fp_pruning_feasibility.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")

    for name in ("djangocms_dev", "saleor_dev"):
        r = out["repos"][name]
        print(f"\n=== {name} selected files: n={r['n_selected_files']} fp={r['n_fp']} fp_rate={r['fp_rate']} ===")
        for key in ("bm25", "composite", "random"):
            d3 = r["rankers"][key]["3"]
            print(f"  ranker={key:12s} D=3: flagged_fp={d3['n_flagged_fp']}/{d3['n_flagged']} flagged_prec={d3['flagged_precision']} tp_loss={d3['tp_loss_risk']} final_F1={d3['final_f1']}")
        od = r["oracle_drop_upper"]["3"]
        print(f"  oracle-drop D=3 upper: final_F1={od['final_f1']} (P={od['final_precision']} R={od['final_recall']})")
    print("\noutput: reports/selected_set_fp_pruning_feasibility.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
