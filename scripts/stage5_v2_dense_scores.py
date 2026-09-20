#!/usr/bin/env python3
# ruff: noqa: E501
"""STAGE5_V2_FINAL - Stage-5 Qwen dense scores + build_rows for the 139 tasks (T3, paid).

Computes the frozen V2 candidate universe + 11 features for the Stage-5
population (dc RESERVE 59 + saleor IT 80) EXACTLY as the DEV pipeline, using:
  - the persisted Qwen realization-A code-unit embeddings (E: cache; all
    Stage-5 code units verified present -> reuses cached vectors, no corpus
    re-embed);
  - NEW query embeddings for the 139 Stage-5 intents (paid, ~$0.00005);
  - the frozen file-MAX cosine aggregation + full-universe dense rank;
  - the frozen memory bundles built for these tasks (parent-only history).

Budget: query embeddings ~$0.00005; hard ceiling $1.00 respected.
Outputs:
  - full_file_scores_stage5.parquet (label-free dense scores/ranks)
  - memory_bundles_stage5.json (parent-only memory)
  - candidate_rows_stage5.parquet (11 features + joined labels for eval)
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))
sys.path.insert(0, str(_PROJECT_DIR / "scripts"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from benchmark.memory_rescue.candidates import MemoryBundle, build_rows_with_provenance  # noqa: E402
from benchmark.memory_rescue.episodic import episode_signals  # noqa: E402
from benchmark.memory_rescue.history import RepoHistory, TaskHistory  # noqa: E402
from benchmark.real_commits import p1_evaluation as p1  # noqa: E402
from benchmark.signal.code_units import extract_code_units, sha256_text  # noqa: E402
from benchmark.signal.or_embeddings import OpenRouterEmbeddingsClient  # noqa: E402
from benchmark.signal.swrank_adapter import aggregate_file_score  # noqa: E402

BLOB_CACHE = Path(r"C:\Users\Ahmed\AppData\Local\Temp\opencode\swerank-cache\blob_text.json")
CACHE_ROOT_E = Path(r"E:\opencode\qwen3-embed-cache-2026-09-19")
DC_DATASET = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v2"
SC_DATASET = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor"
DC_SPLIT = _PROJECT_DIR / "research" / "transparency" / "v2_split_proposal.json"
SC_SPLIT = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor" / "split_freeze_saleor.json"
OUT = _PROJECT_DIR / "research" / "stage5-v2-final"
SPARSE_RECORDS = OUT / "sparse_stage5_run_records.jsonl"
PRICE_PER_1M = 0.01


def stage5_case_ids() -> tuple[list[str], list[str]]:
    prop = json.loads(DC_SPLIT.read_text(encoding="utf-8"))
    reserve = sorted(c for c, r in prop["assignment"].items() if r == "RESERVE")
    sc = json.loads(SC_SPLIT.read_text(encoding="utf-8"))
    it = sorted(c for c, r in sc["assignment"].items() if r == "INTERNAL_TEST")
    return reserve, it


def load_sparse_write_sets() -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    if SPARSE_RECORDS.exists():
        for line in SPARSE_RECORDS.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r["terminal_status"] == "succeeded":
                out.setdefault(r["case_id"], set(r["predicted_write_set"]))  # first-succeeded
    return out


class _Task:
    """Minimal RecallTask-compatible adapter (only write_set + proxy needed
    by the frozen V2 candidate builder)."""

    __slots__ = ("case_id", "repository", "parent_commit", "intent", "write_set",
                 "proxy", "universe_paths", "universe_records", "graph_edges")

    def __init__(self, **kw: object) -> None:
        for k, v in kw.items():
            setattr(self, k, v)


def build_task_df(reserve: list[str], it: list[str], write_sets: dict[str, set[str]]) -> tuple[pd.DataFrame, dict[str, _Task]]:
    """Return a 'task frame' (DataFrame row-only) plus case_id -> _Task map."""
    rows = []
    tasks: dict[str, _Task] = {}
    for cid in reserve:
        m = json.loads((DC_DATASET / "scientific" / cid / "case_manifest.json").read_text(encoding="utf-8"))
        intent = json.loads((DC_DATASET / "scientific" / cid / "public" / "intent.json").read_text(encoding="utf-8"))
        uni = json.loads((DC_DATASET / "scientific" / cid / "public" / "candidate_universe.json").read_text(encoding="utf-8"))
        proxy = p1.load_hidden_proxy_paths(DC_DATASET, cid)
        d = {
            "case_id": cid, "repository": "djangocms",
            "parent_commit": m["record"]["parent_commit"],
            "intent": intent["intent_text"],
            "write_set": write_sets.get(cid, set()),
            "proxy": set(proxy),
            "universe_paths": sorted(r2["path"] for r2 in uni["records"]),
            "universe_records": {str(r2["path"]): r2 for r2 in uni["records"]},
            "graph_edges": tuple((s, d2) for s, d2 in json.loads(
                (DC_DATASET / "scientific" / cid / "public" / "dependency_graph.json").read_text(encoding="utf-8")).get("edges", [])),
        }
        rows.append(d)
        tasks[cid] = _Task(**d)
    for cid in it:
        m = json.loads((SC_DATASET / "scientific" / cid / "case_manifest.json").read_text(encoding="utf-8"))
        intent = json.loads((SC_DATASET / "scientific" / cid / "public" / "intent.json").read_text(encoding="utf-8"))
        uni = json.loads((SC_DATASET / "scientific" / cid / "public" / "candidate_universe.json").read_text(encoding="utf-8"))
        proxy = p1.load_hidden_proxy_paths(SC_DATASET, cid)
        d = {
            "case_id": cid, "repository": "saleor",
            "parent_commit": m["record"]["parent_commit"],
            "intent": intent["intent_text"],
            "write_set": write_sets.get(cid, set()),
            "proxy": set(proxy),
            "universe_paths": sorted(r2["path"] for r2 in uni["records"]),
            "universe_records": {str(r2["path"]): r2 for r2 in uni["records"]},
            "graph_edges": tuple((s, d2) for s, d2 in json.loads(
                (SC_DATASET / "scientific" / cid / "public" / "dependency_graph.json").read_text(encoding="utf-8")).get("edges", [])),
        }
        rows.append(d)
        tasks[cid] = _Task(**d)
    return pd.DataFrame(rows), tasks


def load_cache_matrix() -> tuple[np.ndarray, dict[str, int]]:
    idx = json.loads((CACHE_ROOT_E / "realization_A" / "index.json").read_text(encoding="utf-8"))
    parts = sorted((CACHE_ROOT_E / "realization_A" / "parts").glob("part_*.npy"))
    rows = [np.load(p, mmap_mode="r") for p in parts]
    full = np.concatenate([np.asarray(r) for r in rows], axis=0).astype(np.float32)
    return full, idx


def build_plan(blob_texts: dict[str, str]) -> dict[str, list[str]]:
    plan: dict[str, list[str]] = {}
    for sha, text in blob_texts.items():
        if text is None:
            plan[sha] = []
            continue
        plan[sha] = [sha256_text(u) for u in extract_code_units(text) if u.strip()]
    return plan


def _l2(v: np.ndarray) -> np.ndarray:
    arr = np.asarray(v, dtype=np.float64)
    n = float(np.linalg.norm(arr))
    return (arr / n if n > 0 else arr).astype(np.float32)


def main() -> int:
    reserve, it = stage5_case_ids()
    sparse_ws = load_sparse_write_sets()
    print(f"[ss5-dense] cases: dc {len(reserve)} saleor {len(it)}; sparse write sets {len(sparse_ws)}")

    # task df (for memory + layout compat)
    task_df, task_rows = build_task_df(reserve, it, sparse_ws)

    # query texts
    queries: dict[str, str] = {}
    for cid in reserve:
        intent = json.loads((DC_DATASET / "scientific" / cid / "public" / "intent.json").read_text(encoding="utf-8"))
        queries[cid] = intent["intent_text"]
    for cid in it:
        intent = json.loads((SC_DATASET / "scientific" / cid / "public" / "intent.json").read_text(encoding="utf-8"))
        queries[cid] = intent["intent_text"]
    print(f"[ss5-dense] queries {len(queries)}")

    # embed NEW queries (paid; code units already cached)
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("OPENROUTER_API_KEY not set")
        return 1
    client = OpenRouterEmbeddingsClient(api_key=api_key, batch_size=64)
    ordered = [queries[c] for c in sorted(queries)]
    t0 = time.perf_counter()
    vecs = client.embed(ordered)
    query_emb = {c: np.asarray(v, dtype=np.float32)
                 for c, v in zip(sorted(queries), vecs, strict=True)}
    print(f"[ss5-dense] query embed: {len(vecs)} cost ${client.ledger.cost_usd:.6f} "
          f"tokens {client.ledger.prompt_tokens} in {time.perf_counter()-t0:.1f}s")

    unit_mat, cache_idx = load_cache_matrix()
    blob_texts = json.loads(BLOB_CACHE.read_text(encoding="utf-8"))
    plan = build_plan(blob_texts)
    print(f"[ss5-dense] unit matrix {unit_mat.shape}")

    # block-blob map per case
    def case_blob_sha(dataset: Path, cid: str) -> dict[str, str]:
        uni = json.loads((dataset / "scientific" / cid / "public" / "candidate_universe.json").read_text(encoding="utf-8"))
        return {str(r2["path"]): str(r2["sha256"]) for r2 in uni["records"]}

    score_rows: list[dict] = []
    t1 = time.perf_counter()
    for cid in sorted(queries):
        ds = DC_DATASET if cid in reserve else SC_DATASET
        blob_sha = case_blob_sha(ds, cid)
        universe = task_rows[cid].universe_paths
        qv = _l2(query_emb[cid])
        scores: dict[str, float] = {}
        for path in universe:
            sha = blob_sha.get(path)
            keys = plan.get(sha, []) if sha else []
            rows_ = [cache_idx[k] for k in keys if k in cache_idx]
            if not rows_:
                scores[path] = -1e9
                continue
            unit_cos = unit_mat[rows_] @ qv
            scores[path] = aggregate_file_score([(k, float(c)) for k, c in zip(keys, unit_cos, strict=True)])
        ranked = sorted(universe, key=lambda p: (-scores.get(p, -1e9), p))
        dense = {p: i + 1 for i, p in enumerate(ranked)}
        ws = task_rows[cid].write_set
        for path in universe:
            score_rows.append({
                "case_id": cid,
                "repository": task_rows[cid].repository,
                "parent_commit": task_rows[cid].parent_commit,
                "file_path": path,
                "dense_file_score": float(scores.get(path, np.nan)),
                "dense_rank": int(dense[path]),
                "in_sparse": bool(path in ws),
                "query_sha256": sha256_text(queries[cid]),
                "model_id": "qwen/qwen3-embedding-8b",
                "provider": "DeepInfra",
                "realization_id": "A",
            })
    parquet = pd.DataFrame(score_rows)
    parquet.to_parquet(OUT / "full_file_scores_stage5.parquet", index=False, compression="zstd")
    print(f"[ss5-dense] dense rows {len(parquet)} in {time.perf_counter()-t1:.1f}s")

    # ---- memory construction ----
    mem_out: dict[str, dict] = {}
    for repo in ("djangocms", "saleor"):
        rh = RepoHistory(repo)
        cids = [c for c in reserve if task_rows[c].repository == repo] if repo == "djangocms" else it
        for cid in cids:
            tr = task_rows[cid]
            universe = set(tr.universe_paths)
            th = TaskHistory(rh, tr.parent_commit, universe)
            sparse = set(tr.write_set)
            # structural (uses dense rank-1)
            parquet = pd.read_parquet(OUT / "full_file_scores_stage5.parquet")
            g = parquet[parquet["case_id"] == cid]
            rank1 = str(g["file_path"].iloc[int(g["dense_rank"].to_numpy(dtype=np.int64).argmin())])
            # cochange via frozen cochange module
            from benchmark.memory_rescue.cochange import (
                cochange_memory_score_map,
                cochange_sparse_map,
                cochange_top1_map,
                structural_candidates,
            )
            cs = cochange_sparse_map(th, sparse)
            ct1 = cochange_top1_map(th, rank1)
            mem = cochange_memory_score_map(cs, ct1)
            structural = structural_candidates(mem, th.history_change_count,
                                               [f for f in universe if f not in sparse], k=10)
            ep_records = [{"sha": rec.sha, "subject": rec.subject, "body": rec.body,
                           "paths": rec.paths} for rec in th.commits.values()]
            ep = episode_signals(ep_records, tr.intent) if ep_records else {}
            episodic = []
            scored = [(ep[f]["episode_similarity"], f) for f in universe
                      if f not in sparse and ep.get(f, {}).get("episode_similarity", 0.0) > 0.0]
            scored.sort(key=lambda x: (-x[0], x[1]))
            episodic = [f for _, f in scored[:10]]
            mem_out[cid] = {
                "repository": repo, "parent": tr.parent_commit,
                "history_change_count": {f: int(v) for f, v in th.history_change_count.items()},
                "cochange_sparse": {f: round(v, 12) for f, v in cs.items()},
                "episode_similarity": {f: v["episode_similarity"] for f, v in ep.items()},
                "episode_hit_count": {f: v["episode_hit_count"] for f, v in ep.items()},
                "n_production_changing_commits": th.n_production_changing_commits(),
                "variants": {"A": {"rank1": rank1,
                                   "cochange_top1": {f: round(v, 12) for f, v in ct1.items()},
                                   "structural": structural}},
                "episodic": episodic,
            }
    mem_path = OUT / "memory_bundles_stage5.json"
    mem_path.write_text(json.dumps({"tasks": mem_out}, sort_keys=True), encoding="utf-8")
    print(f"[ss5-dense] memory bundles {len(mem_out)} -> {mem_path}")

    # ---- build V2 rows with frozen features ----
    mem_bundles = {}
    for cid, t in mem_out.items():
        v = t["variants"]["A"]
        mem_bundles[cid] = MemoryBundle(
            history_change_count={k: int(x) for k, x in t["history_change_count"].items()},
            cochange_sparse={k: float(x) for k, x in t["cochange_sparse"].items()},
            episode_similarity={k: float(x) for k, x in t["episode_similarity"].items()},
            episode_hit_count={k: int(x) for k, x in t["episode_hit_count"].items()},
            n_production_changing_commits=int(t["n_production_changing_commits"]),
            cochange_top1={k: float(x) for k, x in v["cochange_top1"].items()},
            structural=list(v["structural"]), episodic=list(t["episodic"]),
        )
    rows, prov = build_rows_with_provenance(pd.read_parquet(OUT / "full_file_scores_stage5.parquet"),
                                             task_rows, mem_bundles)
    from benchmark.memory_rescue.candidates import rows_to_frame
    frame = rows_to_frame(rows)
    frame.to_parquet(OUT / "candidate_rows_stage5.parquet", index=False, compression="zstd")
    print(f"[ss5-dense] candidate rows {len(frame)} tasks {frame['case_id'].nunique()} "
          f"positives {int(frame['label'].sum())}; query cost ${client.ledger.cost_usd:.6f}")
    print("[ss5-dense] DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
