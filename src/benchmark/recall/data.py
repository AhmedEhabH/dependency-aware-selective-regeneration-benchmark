"""First-pass recall bottleneck — DEVELOPMENT data layer (ZERO API, T3).

Rebuilds each DEVELOPMENT task (djangoCMS 174 + Saleor 149) from the SAME
frozen records + case bundles used by Route-B V2 / the Saleor transfer, and
adds the parent-visible features needed for the FN taxonomy and the
source-specific recall-ceiling analysis:

  - Sparse write set (first-succeeded rep), proxy (evaluation-only);
  - per-omitted-candidate observable features: normalized BM25, BM25 rank pct,
    path-token rank pct, binary graph-neighbor (undirected 1-hop, Route-B),
    intent overlap, undirected BFS distance from the known-seed set,
    directed consumer/provider flags, parent-visible co-change count
    (djangoCMS only; Saleor history UNAVAILABLE), module + parent dir;
  - is_missed_positive is the evaluation-only proxy label (never a ranking
    input; used only for post-hoc diagnosis).

Only parent-visible inputs are used to compute features: public intent,
candidate universe, dependency graph, and (djangoCMS) ancestors-of-parent git
history. The hidden proxy never enters a feature.
"""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
if str(PROJECT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR / "src"))

from benchmark.cheap_baselines.bm25 import BM25Index  # noqa: E402
from benchmark.cheap_baselines.corpus import MetadataCorpus  # noqa: E402
from benchmark.cheap_baselines.rankers import (  # noqa: E402
    compute_seed_paths,
    rank_path_token,
)
from benchmark.cheap_baselines.tokenize import tokenize  # noqa: E402
from scripts.route_b_v2_robustness import (  # noqa: E402
    _adjacency,
    _load_run,
    load_case,
)

V1_DATASET = PROJECT_DIR / "benchmark_data" / "real_commit_impact_v1"
V2_DATASET = PROJECT_DIR / "benchmark_data" / "real_commit_impact_v2"
V1_RECORDS = PROJECT_DIR / "research" / "omission-risk-feature-study-v1" / "sparse_v2_trainval_run_records.jsonl"
V2_RECORDS = (
    PROJECT_DIR / "research" / "omission-risk-feature-study-v1" / "v2_trainval" / "v2_trainval_run_records.jsonl"
)
SALEOR_DATASET = PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor"
SALEOR_RECORDS = PROJECT_DIR / "research" / "saleor-sparse-inference" / "saleor_dev_run_records.jsonl"
SPLIT = PROJECT_DIR / "research" / "transparency" / "v2_split_proposal.json"
DJANGOCMS_CACHE = PROJECT_DIR / "dist" / "real-commit-cache" / "djangocms"
SALEOR_CACHE = PROJECT_DIR / "dist" / "real-commit-cache" / "saleor"

SEED_BUDGETS = (0, 1, 3, 5, 10)

COCHANGE_CACHE_PATH = PROJECT_DIR / "research" / "first-pass-recall-bottleneck" / "cochange_cache.json"


@dataclass(frozen=True)
class RecallTask:
    """One DEVELOPMENT task with FN-taxonomy features (parent-visible only)."""

    case_id: str
    repository: str  # "djangocms" | "saleor"
    role: str
    intent_text: str
    parent_commit: str
    year: str
    write_set: frozenset[str]
    proxy: frozenset[str]
    seeds: frozenset[str]  # intent-seed paths UNION write set
    candidates: tuple[dict, ...]  # omitted candidates, each with observable features
    universe_records: dict[str, dict]  # path -> {path, module} for ALL universe files
    universe_size: int
    omitted_size: int

    @property
    def n_missed(self) -> int:
        return sum(1 for c in self.candidates if c["is_missed_positive"])

    @property
    def fn_paths(self) -> tuple[str, ...]:
        return tuple(sorted(c["path"] for c in self.candidates if c["is_missed_positive"]))


def _directed_consumers_providers(
    edges: tuple[tuple[str, str], ...], seeds: set[str], candidates: list[str]
) -> tuple[set[str], set[str]]:
    """consumer(f): edge f->s for some seed s (f imports a seed; downstream).
    provider(f): edge s->f for some seed s (a seed imports f; upstream)."""
    edge_set = set(edges)
    seed_set = set(seeds)
    consumers: set[str] = set()
    providers: set[str] = set()
    for f in candidates:
        for s in seed_set:
            if (f, s) in edge_set:
                consumers.add(f)
            if (s, f) in edge_set:
                providers.add(f)
    return consumers, providers


def _bfs_distances_undirected(
    edges: tuple[tuple[str, str], ...], seeds: set[str], nodes: list[str]
) -> dict[str, int]:
    adj = _adjacency(edges)  # type: ignore[no-untyped-call]
    dist: dict[str, int] = {n: 0 for n in seeds}
    frontier = list(seeds)
    hops = 0
    while frontier:
        hops += 1
        nxt: list[str] = []
        for node in frontier:
            for nb in adj.get(node, set()):
                if nb not in dist:
                    dist[nb] = hops
                    nxt.append(nb)
        frontier = nxt
    return {p: dist.get(p, -1) for p in nodes}


def _files_changed_with(cache: Path, parent: str, seed_paths: set[str], window: int = 2000) -> dict[str, int]:
    proc = subprocess.run(
        ["git", "-C", str(cache), "log", "--name-status", "-n", str(window), parent],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        return {}
    co: dict[str, int] = {}
    current_files: set[str] = set()
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(("M\t", "A\t")):
            p = line[2:]
            if p in seed_paths:
                for f in current_files:
                    co[f] = co.get(f, 0) + 1
            current_files.add(p)
        elif "\t" in line:
            parts = line.split("\t")
            if len(parts) == 2:
                current_files = {parts[1]}
            elif len(parts) == 3:
                current_files = {parts[2]}
        else:
            current_files = set()
    return co


def _load_cochange_cache() -> dict[str, dict[str, int]]:
    if COCHANGE_CACHE_PATH.exists():
        return dict(json.loads(COCHANGE_CACHE_PATH.read_text(encoding="utf-8")))
    return {}


def _save_cochange_cache(cache: dict[str, dict[str, int]]) -> None:
    COCHANGE_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    COCHANGE_CACHE_PATH.write_text(json.dumps(cache, sort_keys=True, indent=1), encoding="utf-8")


def _cochange_for_case(
    case_id: str, parent: str, seed_paths: set[str], cache: dict[str, dict[str, int]]
) -> dict[str, int]:
    if case_id in cache:
        return cache[case_id]
    co = _files_changed_with(DJANGOCMS_CACHE, parent, seed_paths)
    cache[case_id] = co
    return co


def _build_recall_task(cid: str, repo: str, role: str, rec: dict, case: dict, co_cache: dict) -> RecallTask:
    proxy = frozenset(rec["hidden_proxy_used_after_inference"])
    write_set = frozenset(rec.get("predicted_write_set") or [])
    paths = case["paths"]
    records = {str(r["path"]): r for r in case["records"]}
    intent_tokens = set(tokenize(case["intent_text"]))
    mcorpus = MetadataCorpus(parent_commit=case["parent_commit"], candidate_records=case["records"])
    index = BM25Index(mcorpus.texts)
    qt = tokenize(case["intent_text"])
    bm25_scores = {doc: index.score(doc, qt) for doc in index.doc_ids}
    max_bm25 = max(bm25_scores.values()) if bm25_scores else 1.0
    pt_rank = rank_path_token(
        intent_text=case["intent_text"], candidate_paths=paths,
        candidate_records=case["records"], k=len(paths),
    )
    pt_idx = {p: i for i, p in enumerate(pt_rank)}
    seed_elig = compute_seed_paths(
        intent_text=case["intent_text"], candidate_paths=paths,
        candidate_records=case["records"],
    )
    intent_seeds = set(seed_elig.seed_paths)
    seeds: frozenset[str] = frozenset(intent_seeds | set(write_set))
    seeds_as_set = set(seeds)
    bm25_rank = sorted(paths, key=lambda p: (-bm25_scores.get(p, 0.0), p))
    bm25_idx = {p: i for i, p in enumerate(bm25_rank)}
    omitted_paths = [p for p in paths if p not in write_set]
    dist = _bfs_distances_undirected(case["graph_edges"], seeds_as_set, omitted_paths)
    consumers, providers = _directed_consumers_providers(case["graph_edges"], seeds_as_set, omitted_paths)
    nb_set = _neighbors(case["graph_edges"], seeds_as_set)
    seed_dirs = {str(Path(s).parent) for s in seeds}
    seed_modules = {str(records.get(s, {}).get("module", "")) for s in seeds}

    co = {}
    if repo == "djangocms":
        co = _cochange_for_case(cid, case["parent_commit"], set(write_set), co_cache)

    candidates: list[dict] = []
    for p in omitted_paths:
        rec_r = records.get(p, {})
        path_tokens = set(str(p).replace("/", " ").replace(".", " ").split())
        module = str(rec_r.get("module", ""))
        intent_hit = bool((path_tokens | set(module.split())) & intent_tokens)
        bm = bm25_scores.get(p, 0.0) / max_bm25 if max_bm25 else 0.0
        nb = 1.0 if p in nb_set else 0.0
        candidates.append(
            {
                "path": p,
                "module": module,
                "parent_dir": str(Path(p).parent),
                "bm25": bm,
                "bm25_rank_pct": (bm25_idx.get(p, len(paths)) + 1) / len(paths),
                "pt_rank_pct": (pt_idx.get(p, len(paths)) + 1) / len(paths),
                "graph_neighbor": nb,
                "intent_overlap": float(intent_hit),
                "composite": bm + nb,
                "dist": dist.get(p, -1),
                "consumer": int(p in consumers),
                "provider": int(p in providers),
                "sibling": int((str(Path(p).parent) in seed_dirs) or (module in seed_modules)),
                "co_change": co.get(p, 0),
                "history_available": int(repo == "djangocms"),
                "is_missed_positive": int(p in proxy),
            }
        )
    candidates.sort(key=lambda c: (c["path"],))
    return RecallTask(
        case_id=cid,
        repository=repo,
        role=role,
        intent_text=case["intent_text"],
        parent_commit=case["parent_commit"],
        year=case.get("year", ""),
        write_set=write_set,
        proxy=proxy,
        seeds=seeds,
        candidates=tuple(candidates),
        universe_records={
            str(r["path"]): {
                "path": str(r["path"]),
                "module": str(r.get("module", "")),
                "parent_dir": str(Path(str(r["path"])).parent),
            }
            for r in case["records"]
        },
        universe_size=len(paths),
        omitted_size=len(omitted_paths),
    )


def _neighbors(edges: tuple[tuple[str, str], ...], seeds: set[str]) -> set[str]:
    adj = _adjacency(edges)  # type: ignore[no-untyped-call]
    out: set[str] = set()
    for s in seeds:
        out.update(adj.get(s, set()))
    return out


def load_dev_tasks() -> tuple[RecallTask, ...]:
    """Load djangoCMS DEV (174) + Saleor DEV (149) with taxonomy features."""
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    tasks: list[RecallTask] = []
    co_cache = _load_cochange_cache()

    for recs, dataset, repo in (
        (_load_run(V1_RECORDS), V1_DATASET, "djangocms"),
        (_load_run(V2_RECORDS), V2_DATASET, "djangocms"),
    ):
        seen: set[str] = set()
        for rec in recs:
            if rec["terminal_status"] != "succeeded":
                continue
            cid = rec["case_id"]
            if cid in seen:
                continue
            seen.add(cid)
            case = load_case(cid, dataset)
            role = str(split["assignment"].get(cid, "V1_DEV"))
            tasks.append(_build_recall_task(cid, repo, role, rec, case, co_cache))

    saleor_recs = _load_run(SALEOR_RECORDS)
    seen_s: set[str] = set()
    for rec in saleor_recs:
        if rec["terminal_status"] != "succeeded":
            continue
        cid = rec["case_id"]
        if cid in seen_s:
            continue
        seen_s.add(cid)
        case = load_case(cid, SALEOR_DATASET)
        tasks.append(_build_recall_task(cid, "saleor", "SALEOR_DEV", rec, case, co_cache))

    _save_cochange_cache(co_cache)
    tasks.sort(key=lambda t: (t.repository, t.case_id))
    return tuple(tasks)


def aggregate_tp_fp_fn(tasks: list[RecallTask]) -> dict:
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
    return {"n_tasks": len(tasks), "tp": tp, "fp": fp, "fn": fn,
            "precision": round(p, 6), "recall": round(r, 6), "f1": round(f1, 6),
            "fnr": round(fn / (tp + fn), 6) if (tp + fn) else 0.0, "n_positives": tp + fn}


if __name__ == "__main__":
    tasks = load_dev_tasks()
    dc = [t for t in tasks if t.repository == "djangocms"]
    sc = [t for t in tasks if t.repository == "saleor"]
    print("djangocms DEV tasks:", len(dc), "saleor DEV tasks:", len(sc))
    print("djangocms Sparse baseline:", json.dumps(aggregate_tp_fp_fn(dc), indent=1))
    print("saleor    Sparse baseline:", json.dumps(aggregate_tp_fp_fn(sc), indent=1))
    print("total FN djangocms:", sum(t.n_missed for t in dc), "saleor:", sum(t.n_missed for t in sc))
