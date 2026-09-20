#!/usr/bin/env python3
"""STAGE5_V2_FINAL - independent audit of LocAgent-native metric compatibility (T3).

Recomputes Acc@K / Hit@K / Recall@K and the single-target slice from PERSISTED
DEV artifacts WITHOUT importing any Stage-5 analyzer or the primary pipeline.

Inputs:
  - research/contamination-bridge/qwen_embed/realization_A/full_file_scores.parquet
  - research/memory-rescue-v2/oof_probabilities_A.parquet
  - benchmark.recall.data.load_dev_tasks (artifact loader only)
  - research/locagent-p5b/shared_comparison.json (P5-C reference)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

import pandas as pd  # noqa: E402

from benchmark.recall.data import load_dev_tasks  # noqa: E402

Q = _PROJECT_DIR / "research"
CHECK: list[dict] = []


def _p(name: str, ok: bool, detail: str) -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    CHECK.append({"name": name, "pass": bool(ok), "detail": detail})


def _load_v2_rank() -> dict[str, list[str]]:
    oof = pd.read_parquet(Q / "memory-rescue-v2" / "oof_probabilities_A.parquet")
    rank: dict[str, list[str]] = {}
    for cid, g in oof.groupby("case_id"):
        g = g.sort_values(["prob", "file_path"], ascending=[False, True])
        rank[cid] = list(g["file_path"])
    return rank


def _metrics(rank_by_id: dict[str, list[str]], proxy_by_id: dict):
    n = 0
    acc = {1: 0, 3: 0, 5: 0}
    hit = {1: 0, 3: 0, 5: 0}
    rec = {1: 0.0, 3: 0.0, 5: 0.0}
    for cid, gset in sorted(proxy_by_id.items()):
        if cid not in rank_by_id or not gset:
            continue
        order = rank_by_id[cid]
        n += 1
        for k in (1, 3, 5):
            inter = len(set(order[:k]) & set(gset))
            acc[k] += 1 if inter == min(len(gset), k) else 0
            hit[k] += 1 if inter >= 1 else 0
            rec[k] += inter / len(gset)
    out = {}
    for k in (1, 3, 5):
        out[k] = {"acc": acc[k] / n, "hit": hit[k] / n, "rec": rec[k] / n}
    return out, n


def main() -> int:
    tasks = load_dev_tasks()
    proxy_by_id = {t.case_id: set(t.proxy) for t in tasks}
    rank = _load_v2_rank()
    assert len(proxy_by_id) == len(rank) == 323, (len(proxy_by_id), len(rank))

    metrics, n = _metrics(rank, proxy_by_id)
    expected_acc = {1: 47.4, 3: 25.1, 5: 26.6}
    for k in (1, 3, 5):
        _p(f"Acc@{k}", abs(metrics[k]["acc"] * 100 - expected_acc[k]) < 0.5,
           f"Acc@{k} = {metrics[k]['acc']:.4f}")
    _p("Hit@5", abs(metrics[5]["hit"] * 100 - 74.9) < 0.5,
       f"Hit@5 = {metrics[5]['hit']:.4f}")
    # single-target slice
    st_n = st_h = 0
    for cid, gset in proxy_by_id.items():
        if len(gset) == 1 and cid in rank:
            st_n += 1
            if len(set(rank[cid][:5]) & set(gset)) == 1:
                st_h += 1
    _p("SingleTarget|G|=1 n", st_n == 80, f"n={st_n}")
    _p("SingleTarget Acc@5", st_n == 80 and st_h / st_n == 0.60,
       f"Acc@5={st_h}/{st_n}={st_h / st_n:.4f}")

    # P5-C reference
    comp = json.loads((Q / "locagent-p5b" / "shared_comparison.json").read_text(encoding="utf-8"))
    nat = comp["locagent_native"]
    acc5 = [r["hits"] for r in nat["official_acc_at_k"] if r["k"] == 5][0]
    hit5 = [r["hits"] for r in nat["hit_at_k"] if r["k"] == 5][0]
    _p("P5C Acc@5 reference", acc5 == 2 and hit5 == 4, f"Acc@5={acc5}/10 Hit@5={hit5}/10")

    n_pass = sum(1 for c in CHECK if c["pass"])
    print(f"AUDIT SUMMARY: {n_pass}/{len(CHECK)} PASS")
    (reports_dir / "stage5_native_compat_audit.json").write_text(
        json.dumps({"pass": n_pass, "total": len(CHECK), "checks": CHECK}, indent=1),
        encoding="utf-8")
    return 0 if n_pass == len(CHECK) else 1


reports_dir = _PROJECT_DIR / "reports"

if __name__ == "__main__":
    raise SystemExit(main())
