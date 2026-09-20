#!/usr/bin/env python3
# ruff: noqa: E501
"""STAGE5_CORRECTED_REEXECUTION - corrected Stage-5 dense scores + memory + rows.

Repairs the P86 embedding-coverage execution defect in the frozen Stage-5 V2
pipeline WITHOUT changing any scientific V2 design choice.

Fix scope (mission §5, §7):
  - CASE A (cache hit): reuse the realization-A embedding exactly.
  - CASE B (cache miss but file has embeddable units): materialize/split the
    Stage-5 blob using the SAME frozen unit splitter and embed the missing
    units with qwen/qwen3-embedding-8b @ DeepInfra (fallback disabled), same
    realization-A MAX-cosine aggregation procedure.
  - CASE C (file truly has no embeddable unit): dense score MUST be NaN /
    missing (frozen DEV semantics -> feature builder imputes min_finite - 1).
  - NEVER emit a finite sentinel (-1e9 / -1e6 / -999999) for no-unit or
    missing-embedding state.
Hard pipeline guards:
  - fail if abs(dense_file_score) > 10 for any finite candidate dense score;
  - fail if a blob has embeddable units but no embedding result;
  - fail if a required cache lookup silently resolves to a finite sentinel;
  - fail if dense score generation produces values outside the scientifically
    expected range without an explicit documented reason.
  - NO silent fallback.

Cost guard: hard incremental ceiling $0.25 for new embeddings (live price
verified before call 1; STOP before paid calls if projected > $0.25).

Outputs (research/stage5-v2-final, corrected suffix):
  - full_file_scores_stage5_corrected.parquet (label-free)
  - memory_bundles_stage5_corrected.json
  - candidate_rows_stage5_corrected.parquet (11 features + labels for eval)

Sparse write sets are REUSED from sparse_stage5_run_records.jsonl (no Sparse
LLM re-call). Population = the SAME 139 exposed tasks (dc RESERVE 59 + saleor
INTERNAL_TEST 80). Frozen V2 model/scaler/threshold/endpoint unchanged.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))
sys.path.insert(0, str(_PROJECT_DIR / "scripts"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from benchmark.memory_rescue.candidates import MemoryBundle, build_rows_with_provenance  # noqa: E402
from benchmark.memory_rescue.cochange import (  # noqa: E402
    cochange_memory_score_map,
    cochange_sparse_map,
    cochange_top1_map,
    structural_candidates,
)
from benchmark.memory_rescue.episodic import episode_signals  # noqa: E402
from benchmark.memory_rescue.history import RepoHistory, TaskHistory  # noqa: E402
from benchmark.real_commits import p1_evaluation as p1  # noqa: E402
from benchmark.signal.code_units import extract_code_units, sha256_text  # noqa: E402
from benchmark.signal.or_embeddings import OPENROUTER_EMBED_MODEL, OpenRouterEmbeddingsClient  # noqa: E402
from benchmark.signal.swrank_adapter import aggregate_file_score  # noqa: E402
from scripts.qwen3_two_realization_run import ChunkCache  # noqa: E402

BLOB_CACHE = Path(r"C:\Users\Ahmed\AppData\Local\Temp\opencode\swerank-cache\blob_text.json")
DEV_CACHE_ROOT = Path(r"E:\opencode\qwen3-embed-cache-2026-09-19")
CORRECTED_CACHE_ROOT = Path(r"E:\opencode\qwen3-embed-cache-stage5-corrected-2026-09-20")
CORRECTED_WORK = Path(r"E:\opencode\stage5-corrected-2026-09-20")
DC_DATASET = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v2"
SC_DATASET = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor"
DC_SPLIT = _PROJECT_DIR / "research" / "transparency" / "v2_split_proposal.json"
SC_SPLIT = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor" / "split_freeze_saleor.json"
OUT = _PROJECT_DIR / "research" / "stage5-v2-final"
SPARSE_RECORDS = OUT / "sparse_stage5_run_records.jsonl"
PRICE_PER_1M = 0.01
CEILING_USD = 0.25
SENTINEL_FINITE_BOUND = 10.0
EMPTY_BLOB = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


class _Task:
    __slots__ = ("case_id", "repository", "parent_commit", "intent", "write_set",
                 "proxy", "universe_paths", "universe_records", "graph_edges")

    def __init__(self, **kw: object) -> None:
        for k, v in kw.items():
            setattr(self, k, v)


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
                out.setdefault(r["case_id"], set(r["predicted_write_set"]))
    return out


def build_task_df(reserve: list[str], it: list[str],
                  write_sets: dict[str, set[str]]) -> tuple[pd.DataFrame, dict[str, _Task]]:
    rows: list[dict] = []
    tasks: dict[str, _Task] = {}

    def _one(ds: Path, cid: str, repo: str) -> None:
        m = json.loads((ds / "scientific" / cid / "case_manifest.json").read_text(encoding="utf-8"))
        intent = json.loads((ds / "scientific" / cid / "public" / "intent.json").read_text(encoding="utf-8"))
        uni = json.loads((ds / "scientific" / cid / "public" / "candidate_universe.json").read_text(encoding="utf-8"))
        proxy = p1.load_hidden_proxy_paths(ds, cid)
        d = {
            "case_id": cid, "repository": repo,
            "parent_commit": m["record"]["parent_commit"],
            "intent": intent["intent_text"],
            "write_set": write_sets.get(cid, set()),
            "proxy": set(proxy),
            "universe_paths": sorted(r2["path"] for r2 in uni["records"]),
            "universe_records": {str(r2["path"]): r2 for r2 in uni["records"]},
            "graph_edges": tuple((s, d2) for s, d2 in json.loads(
                (ds / "scientific" / cid / "public" / "dependency_graph.json").read_text(encoding="utf-8")).get("edges", [])),
        }
        rows.append(d)
        tasks[cid] = _Task(**d)

    for cid in reserve:
        _one(DC_DATASET, cid, "djangocms")
    for cid in it:
        _one(SC_DATASET, cid, "saleor")
    return pd.DataFrame(rows), tasks


def _l2(v: np.ndarray) -> np.ndarray:
    arr = np.asarray(v, dtype=np.float64)
    n = float(np.linalg.norm(arr))
    return (arr / n if n > 0 else arr).astype(np.float32)


def load_dev_matrix() -> tuple[np.ndarray, dict[str, int]]:
    idx = json.loads((DEV_CACHE_ROOT / "realization_A" / "index.json").read_text(encoding="utf-8"))
    parts = sorted((DEV_CACHE_ROOT / "realization_A" / "parts").glob("part_*.npy"))
    rows = [np.load(p, mmap_mode="r") for p in parts]
    full = np.concatenate([np.asarray(r) for r in rows], axis=0).astype(np.float32)
    return full, idx


def _live_price() -> dict:
    for attempt in range(6):
        try:
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/embeddings/models",
                headers={"User-Agent": "research"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                d = json.loads(resp.read().decode("utf-8"))
            break
        except (Exception, urllib.error.URLError):
            if attempt == 5:
                return {}
            time.sleep(1.5 ** attempt)
    for m in (d or {}).get("data", []):
        if m.get("id") == OPENROUTER_EMBED_MODEL:
            return m.get("pricing") or {}
    return {}


def build_plan(blob_texts: dict[str, str]) -> tuple[dict[str, list[str]], dict[str, str]]:
    """Return (blob_sha -> unit shas, unit_sha -> unit text)."""
    plan: dict[str, list[str]] = {}
    unit_texts: dict[str, str] = {}
    for sha, text in blob_texts.items():
        if text is None:
            plan[sha] = []
            continue
        keys: list[str] = []
        for u in extract_code_units(text):
            if not u.strip():
                continue
            us = sha256_text(u)
            keys.append(us)
            unit_texts.setdefault(us, u)
        plan[sha] = keys
    return plan, unit_texts


def main() -> int:
    reserve, it = stage5_case_ids()
    sparse_ws = load_sparse_write_sets()
    print(f"[s5c-run] cases: dc {len(reserve)} saleor {len(it)}; sparse write sets {len(sparse_ws)}")
    _, task_rows = build_task_df(reserve, it, sparse_ws)

    # ---- blob-text sources (DEV cache + corrected materialization) ----
    dev_blob_texts = json.loads(BLOB_CACHE.read_text(encoding="utf-8"))
    corr_blob_path = CORRECTED_WORK / "missing_blob_texts.json"
    corr_blob_texts = json.loads(corr_blob_path.read_text(encoding="utf-8")) if corr_blob_path.exists() else {}
    blob_texts: dict[str, str] = {**dev_blob_texts, **corr_blob_texts}
    plan, unit_texts = build_plan(blob_texts)
    print(f"[s5c-run] blob texts: dev {len(dev_blob_texts)} + corrected {len(corr_blob_texts)} "
          f"= {len(blob_texts)}; distinct units {len(unit_texts)}")

    # ---- merged embedding caches ----
    dev_mat, dev_idx = load_dev_matrix()
    corr_cache = ChunkCache(CORRECTED_CACHE_ROOT / "realization_A")
    print(f"[s5c-run] dev matrix {dev_mat.shape}; corrected cache {len(corr_cache)}")
    corr_idx = dict(corr_cache.index)

    def covered(k: str) -> bool:
        return k in dev_idx or k in corr_idx

    # ---- queries (139 intents; cached) ----
    queries: dict[str, str] = {}
    for cid in list(reserve) + list(it):
        ds = DC_DATASET if cid in reserve else SC_DATASET
        intent = json.loads((ds / "scientific" / cid / "public" / "intent.json").read_text(encoding="utf-8"))
        queries[cid] = intent["intent_text"]
    qcache = ChunkCache(CORRECTED_CACHE_ROOT / "queries")
    q_texts = [queries[c] for c in sorted(queries)]
    to_embed_q = qcache.missing(q_texts)

    # ---- cost guard: live price + projection BEFORE any paid call ----
    api_key = os.environ.get("OPENROUTER_API_KEY")
    price = _live_price()
    prompt_price = float((price or {}).get("prompt", 0) or 0)
    if prompt_price <= 0:
        print("LIVE_PRICE_UNVERIFIED - cannot confirm qwen/qwen3-embedding-8b price; STOP")
        return 1
    print(f"[s5c-run] live price verified: prompt ${prompt_price:.12f}/token "
          f"(= ${prompt_price * 1e6:.4f}/M)")

    missing_units = [k for k in unit_texts if not covered(k)]
    est_unit_tokens = sum(len(unit_texts[k]) / 3.5 for k in missing_units)
    est_query_tokens = sum(32 for _ in to_embed_q)
    proj_cost = est_unit_tokens / 1e6 * prompt_price
    proj_query_cost = est_query_tokens / 1e6 * prompt_price
    total_proj = proj_cost + proj_query_cost
    print(f"[s5c-run] missing units {len(missing_units)} (est {est_unit_tokens:.0f} tok = "
          f"${proj_cost:.4f}); queries to embed {len(to_embed_q)} (est ${proj_query_cost:.4f}); "
          f"TOTAL projected ${total_proj:.4f}; ceiling ${CEILING_USD}")
    if total_proj > CEILING_USD:
        print(f"COST_STOP projected ${total_proj:.4f} > ceiling ${CEILING_USD}; STOP before paid calls")
        return 1

    client: OpenRouterEmbeddingsClient | None = None
    if to_embed_q or missing_units:
        if not api_key:
            print("OPENROUTER_API_KEY not set")
            return 1
        client = OpenRouterEmbeddingsClient(api_key=api_key, batch_size=64)

    # ---- embed queries ----
    if to_embed_q:
        assert client is not None
        vecs = client.embed(to_embed_q)
        qcache.add(to_embed_q, vecs)
        print(f"[s5c-run] query embed: {len(to_embed_q)} cost ${client.ledger.cost_usd:.6f} "
              f"tokens {client.ledger.prompt_tokens}")
    qvec: dict[str, np.ndarray] = {}
    for c in sorted(queries):
        qvec[c] = _l2(qcache.get([queries[c]])[0])

    # ---- embed missing units ----
    if missing_units:
        assert client is not None
        texts = [unit_texts[k] for k in missing_units]
        vecs = client.embed(texts)
        corr_cache.add(texts, vecs)
        print(f"[s5c-run] embedded missing units: {len(missing_units)} cost ${client.ledger.cost_usd:.6f} "
              f"tokens {client.ledger.prompt_tokens}")
    corr_idx = dict(corr_cache.index)
    corr_mat = corr_cache.matrix
    if corr_mat is None:
        corr_mat = np.zeros((0, dev_mat.shape[1]), dtype=np.float32)

    still_missing = [k for k in unit_texts if not covered(k)]
    if still_missing:
        print(f"EMBEDDING_RESOLUTION_FAIL: {len(still_missing)} units unresolved "
              f"(blob has embeddable units but no embedding result) -> FAIL")
        return 1
    print(f"[s5c-run] distinct units {len(unit_texts)}; embedding coverage 100%")

    # ---- score all files (CASE A/B/C) ----
    def unit_vec(k: str) -> np.ndarray:
        if k in dev_idx:
            return dev_mat[dev_idx[k]]
        assert k in corr_idx
        return corr_mat[corr_idx[k]]

    score_rows: list[dict] = []
    for cid in sorted(queries):
        ds = DC_DATASET if cid in reserve else SC_DATASET
        uni = json.loads((ds / "scientific" / cid / "public" / "candidate_universe.json").read_text(encoding="utf-8"))
        blob_sha = {str(r2["path"]): str(r2["sha256"]) for r2 in uni["records"]}
        universe = task_rows[cid].universe_paths
        qv = _l2(qvec[cid])
        scores: dict[str, float] = {}
        for path in universe:
            sha = blob_sha.get(path)
            keys = plan.get(sha, []) if sha else []
            if not keys:
                # CASE C: no embeddable unit -> NaN (frozen DEV semantics)
                continue
            missing = [k for k in keys if not covered(k)]
            if missing:
                print(f"EMBEDDING_RESOLUTION_FAIL {cid} {path}: {len(missing)}/{len(keys)} "
                      f"units unresolved (blob has embeddable units but no embedding result)")
                return 1
            unit_cos = [float(unit_vec(k) @ qv) for k in keys]
            score = aggregate_file_score([(k, float(c)) for k, c in zip(keys, unit_cos, strict=True)])
            if not np.isfinite(score) or abs(score) > SENTINEL_FINITE_BOUND:
                print(f"SCORE_RANGE_GUARD_FAIL {cid} {path}: {score}")
                return 1
            scores[path] = score
        ranked = sorted(universe, key=lambda p: (-scores.get(p, -1e9), p))
        dense = {p: i + 1 for i, p in enumerate(ranked)}
        ws = task_rows[cid].write_set
        for path in universe:
            score_rows.append({
                "case_id": cid, "repository": task_rows[cid].repository,
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
    n_sent = int((parquet["dense_file_score"] == -1e9).sum())
    if n_sent:
        print(f"SENTINEL_GUARD_FAIL: {n_sent} rows == -1e9; no finite sentinels allowed")
        return 1
    parquet.to_parquet(OUT / "full_file_scores_stage5_corrected.parquet", index=False, compression="zstd")
    print(f"[s5c-run] dense rows {len(parquet)} -> full_file_scores_stage5_corrected.parquet")

    # ---- memory bundles (rebuilt from corrected rank-1) ----
    mem_out: dict[str, dict] = {}
    for repo in ("djangocms", "saleor"):
        rh = RepoHistory(repo)
        cids = ([c for c in reserve if task_rows[c].repository == repo] if repo == "djangocms" else it)
        for cid in cids:
            tr = task_rows[cid]
            universe = set(tr.universe_paths)
            th = TaskHistory(rh, tr.parent_commit, universe)
            sparse = set(tr.write_set)
            g = parquet[parquet["case_id"] == cid]
            rank1 = str(g["file_path"].iloc[int(g["dense_rank"].to_numpy(dtype=np.int64).argmin())])
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
    mem_path = OUT / "memory_bundles_stage5_corrected.json"
    mem_path.write_text(json.dumps({"tasks": mem_out}, sort_keys=True), encoding="utf-8")
    print(f"[s5c-run] memory bundles {len(mem_out)} -> {mem_path}")

    # ---- build V2 candidate rows (frozen 11 features) ----
    mem_bundles: dict[str, MemoryBundle] = {}
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
    rows, _prov = build_rows_with_provenance(
        pd.read_parquet(OUT / "full_file_scores_stage5_corrected.parquet"),
        task_rows, mem_bundles)
    from benchmark.memory_rescue.candidates import rows_to_frame
    frame = rows_to_frame(rows)
    frame.to_parquet(OUT / "candidate_rows_stage5_corrected.parquet", index=False, compression="zstd")
    print(f"[s5c-run] candidate rows {len(frame)} tasks {frame['case_id'].nunique()} "
          f"positives {int(frame['label'].sum())}")
    print("[s5c-run] DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
