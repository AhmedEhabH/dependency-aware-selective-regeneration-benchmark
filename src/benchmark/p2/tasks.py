"""P2 — task loading from frozen DEVELOPMENT records (ZERO API).

Builds the P2 task table from the SAME frozen run records + public bundles used
by Route-B V2 / the Saleor transfer:

- djangoCMS DEV: V1 (30, V1_DEV) + V2 (DEV_TRAIN 117 + DEV_VALIDATION 27) =
  174 tasks, roles from ``v2_split_proposal.json``.
- Saleor DEV: 149 succeeded tasks, role SALEOR_DEV.

An :class:`ObservableTask` contains ONLY parent-visible features plus an
evaluation-only ``is_missed_positive`` label that MUST never be consumed by a
policy. The evaluation-only proxy is separated.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(_PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(_PROJECT_DIR))
if str(_PROJECT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_DIR / "src"))

from scripts.route_b_v2_robustness import build_task, load_case  # noqa: E402

PROJECT_DIR = _PROJECT_DIR
V1_DATASET = PROJECT_DIR / "benchmark_data" / "real_commit_impact_v1"
V2_DATASET = PROJECT_DIR / "benchmark_data" / "real_commit_impact_v2"
SALEOR_DATASET = PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor"
V1_RECORDS = PROJECT_DIR / "research" / "omission-risk-feature-study-v1" / "sparse_v2_trainval_run_records.jsonl"
V2_RECORDS = PROJECT_DIR / "research" / "omission-risk-feature-study-v1" / "v2_trainval" / "v2_trainval_run_records.jsonl"  # noqa: E501
SALEOR_RECORDS = PROJECT_DIR / "research" / "saleor-sparse-inference" / "saleor_dev_run_records.jsonl"
V2_SPLIT = PROJECT_DIR / "research" / "transparency" / "v2_split_proposal.json"

# Frozen constant: the P2 policies may emit budgets up to this cap (equal to
# the largest fixed-B anchor). Policies never emit below 1 (B=0 is Sparse alone).
MAX_BUDGET = 10
FIXED_BUDGETS = (1, 3, 5, 10)


@dataclass(frozen=True)
class ObservableCandidate:
    """Observable candidate features (parent-visible only)."""

    path: str
    bm25: float
    bm25_rank_pct: float
    graph_neighbor: float
    composite: float
    intent_overlap: int
    is_missed_positive: int  # evaluation-only; policies MUST NOT read this


@dataclass(frozen=True)
class ObservableTask:
    """One P2 task. ``proxy`` and the candidate labels are evaluation-only."""

    case_id: str
    repository: str
    role: str
    candidates: tuple[ObservableCandidate, ...]  # sorted composite desc, tie path asc
    omitted_size: int
    universe_size: int
    proxy: frozenset[str]
    n_missed: int

    @property
    def ranked_paths(self) -> tuple[str, ...]:
        return tuple(c.path for c in self.candidates)


def _load_records(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _first_succeeded_by_case(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for rec in records:
        cid = rec.get("case_id")
        if not cid or cid in out:
            continue
        if rec.get("terminal_status") == "succeeded":
            out[cid] = rec
    return out


def _build_observable(cid: str, repository: str, role: str, task: dict[str, Any]) -> ObservableTask:
    cands: list[ObservableCandidate] = []
    for path, c in task["candidates"].items():
        cands.append(
            ObservableCandidate(
                path=path,
                bm25=float(c["bm25"]),
                bm25_rank_pct=float(c["bm25_rank_pct"]),
                graph_neighbor=float(c["graph_neighbor"]),
                composite=float(c["bm25"]) + float(c["graph_neighbor"]),
                intent_overlap=int(c["intent_overlap"]),
                is_missed_positive=int(c["is_missed_positive"]),
            )
        )
    cands.sort(key=lambda c: (-c.composite, c.path))
    return ObservableTask(
        case_id=cid,
        repository=repository,
        role=role,
        candidates=tuple(cands),
        omitted_size=task["omitted_size"],
        universe_size=task["universe_size"],
        proxy=frozenset(task["proxy"]),
        n_missed=task["n_missed"],
    )


def _djangocms_role(cid: str, split: dict[str, Any]) -> str:
    return str(split["assignment"].get(cid, "V1_DEV"))


def load_dev_tasks() -> tuple[ObservableTask, ...]:
    """Load djangoCMS DEV (174) + Saleor DEV (149) tasks (sorted by case_id)."""
    split = json.loads(V2_SPLIT.read_text(encoding="utf-8"))
    out: list[ObservableTask] = []

    v1_recs = _load_records(V1_RECORDS)
    v2_recs = _load_records(V2_RECORDS)
    v1_case_ids = {r["case_id"] for r in v1_recs}

    for recs in (v1_recs, v2_recs):
        for cid, rec in _first_succeeded_by_case(recs).items():
            dataset = V1_DATASET if cid in v1_case_ids else V2_DATASET
            case = load_case(cid, dataset)
            proxy = set(rec["hidden_proxy_used_after_inference"])
            write_set = set(rec.get("predicted_write_set") or [])
            task = build_task(cid, case, write_set, proxy)  # type: ignore[no-untyped-call]
            role = _djangocms_role(cid, split)
            out.append(_build_observable(cid, "djangocms", role, task))

    saleor_recs = _load_records(SALEOR_RECORDS)
    for cid, rec in _first_succeeded_by_case(saleor_recs).items():
        case = load_case(cid, SALEOR_DATASET)
        proxy = set(rec["hidden_proxy_used_after_inference"])
        write_set = set(rec.get("predicted_write_set") or [])
        task = build_task(cid, case, write_set, proxy)  # type: ignore[no-untyped-call]
        out.append(_build_observable(cid, "saleor", "SALEOR_DEV", task))

    out.sort(key=lambda t: (t.repository, t.case_id))
    return tuple(out)
