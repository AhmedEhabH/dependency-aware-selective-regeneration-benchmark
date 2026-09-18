# ruff: noqa: E501
"""Oracle-gap decomposition — DEVELOPMENT data access layer (ZERO API).

Loads djangoCMS DEV (174) + Saleor DEV (149) tasks via the frozen P2 task
loader and exposes:
  - Sparse predicted set (first-succeeded write set)
  - proxy (evaluation-only)
  - candidate features (bm25, graph_neighbor, composite) observable at inference
  - is_missed_positive (evaluation-only label; never consumed by a policy)

Tier: T3. No model/API calls.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PROJECT_DIR / "src"))

from benchmark.p2.tasks import load_dev_tasks  # noqa: E402


@dataclass
class DevTask:
    case_id: str
    repository: str
    role: str
    write_set: frozenset[str]
    proxy: frozenset[str]
    candidates: list[dict]  # path -> features
    universe_size: int
    omitted_size: int

    @property
    def n_missed(self) -> int:
        return sum(1 for c in self.candidates if c["is_missed_positive"])


def _to_devtask(t) -> DevTask:
    cands = []
    for c in t.candidates:
        cands.append(
            {
                "path": c.path,
                "bm25": float(c.bm25),
                "bm25_rank_pct": float(c.bm25_rank_pct),
                "graph_neighbor": float(c.graph_neighbor),
                "composite": float(c.composite),
                "intent_overlap": int(c.intent_overlap),
                "is_missed_positive": int(c.is_missed_positive),
            }
        )
    return DevTask(
        case_id=t.case_id,
        repository=t.repository,
        role=t.role,
        write_set=frozenset(t.proxy) | frozenset() if False else frozenset(),
        proxy=frozenset(t.proxy),
        candidates=cands,
        universe_size=t.universe_size,
        omitted_size=t.omitted_size,
    )


def _sparse_write_set(cid: str, repo: str) -> frozenset[str]:
    """Reconstruct the Sparse first-succeeded write set from frozen records."""
    import json as _json

    if repo == "saleor":
        rec_path = PROJECT_DIR / "research" / "saleor-sparse-inference" / "saleor_dev_run_records.jsonl"
    else:
        rec_path = PROJECT_DIR / "research" / "omission-risk-feature-study-v1" / "sparse_v2_trainval_run_records.jsonl"
    v2_rec_path = PROJECT_DIR / "research" / "omission-risk-feature-study-v1" / "v2_trainval" / "v2_trainval_run_records.jsonl"

    def _first_succeeded(path: Path) -> dict | None:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = _json.loads(line)
            if r.get("case_id") == cid and r.get("terminal_status") == "succeeded":
                return r
        return None

    rec = _first_succeeded(rec_path) or _first_succeeded(v2_rec_path)
    if rec is None:
        raise KeyError(f"no succeeded sparse record for {cid}")
    return frozenset(rec.get("predicted_write_set") or [])


def load_all() -> list[DevTask]:
    tasks = []
    for t in load_dev_tasks():
        repo = "saleor" if t.repository == "saleor" else "djangocms"
        write_set = _sparse_write_set(t.case_id, repo)
        cands = []
        for c in t.candidates:
            cands.append(
                {
                    "path": c.path,
                    "bm25": float(c.bm25),
                    "bm25_rank_pct": float(c.bm25_rank_pct),
                    "graph_neighbor": float(c.graph_neighbor),
                    "composite": float(c.composite),
                    "intent_overlap": int(c.intent_overlap),
                    "is_missed_positive": int(c.is_missed_positive),
                }
            )
        tasks.append(
            DevTask(
                case_id=t.case_id,
                repository=repo,
                role=t.role,
                write_set=write_set,
                proxy=frozenset(t.proxy),
                candidates=cands,
                universe_size=t.universe_size,
                omitted_size=t.omitted_size,
            )
        )
    return tasks


def aggregate_tp_fp_fn(tasks: list[DevTask]) -> dict:
    tp = fp = fn = 0
    for t in tasks:
        pred = t.write_set
        pos = t.proxy
        tp += len(pred & pos)
        fp += len(pred - pos)
        fn += len(pos - pred)
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"n_tasks": len(tasks), "tp": tp, "fp": fp, "fn": fn, "precision": round(p, 6), "recall": round(r, 6), "f1": round(f1, 6), "fnr": round(fn / (tp + fn), 6) if (tp + fn) else 0.0, "n_positives": tp + fn}


if __name__ == "__main__":
    tasks = load_all()
    dc = [t for t in tasks if t.repository == "djangocms"]
    sc = [t for t in tasks if t.repository == "saleor"]
    print("djangocms DEV tasks:", len(dc), "saleor DEV tasks:", len(sc))
    print("djangocms Sparse baseline:", json.dumps(aggregate_tp_fp_fn(dc), indent=1))
    print("saleor    Sparse baseline:", json.dumps(aggregate_tp_fp_fn(sc), indent=1))
    t0 = dc[0]
    print("\nexample task:", t0.case_id, "write_set_size", len(t0.write_set), "proxy_size", len(t0.proxy), "n_missed", t0.n_missed)
