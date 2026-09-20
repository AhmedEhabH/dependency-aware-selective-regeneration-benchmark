#!/usr/bin/env python3
# ruff: noqa: E501
"""SALEOR_RESERVE_300_RMCSS - Qwen dense scores + RM-CSS memory + candidate
rows for the 300 sampled Saleor RESERVE tasks (label-free; §10.B/C).

Embedding-coverage semantics (P86-corrected, §15):
  CASE A cached -> reuse; CASE B not cached but embeddable units -> embed the
  missing units (qwen/qwen3-embedding-8b @ DeepInfra, realization A, frozen
  splitter + MAX-cosine aggregation); CASE C no embeddable units -> NaN.
  NEVER a finite sentinel; hard guard abs(dense_file_score) > 10 -> RAISE.

Label-free: SIP write sets are taken from sip_300_run_records.jsonl; the proxy
is passed as EMPTY (labels are joined ONLY at the outcome-open step §19).

Outputs (research/saleor-reserve-300-rmcss/):
  - full_file_scores_saleor300.parquet
  - memory_bundles_saleor300.json
  - candidate_rows_saleor300.parquet
Observability every 10 tasks (flush=True). No scientific behavior change.
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
from benchmark.signal.code_units import extract_code_units, sha256_text  # noqa: E402
from benchmark.signal.or_embeddings import OPENROUTER_EMBED_MODEL, OpenRouterEmbeddingsClient  # noqa: E402
from benchmark.signal.swrank_adapter import aggregate_file_score  # noqa: E402
from scripts.qwen3_two_realization_run import ChunkCache  # noqa: E402

BLOB_CACHE = Path(r"C:\Users\Ahmed\AppData\Local\Temp\opencode\swerank-cache\blob_text.json")
DEV_CACHE_ROOT = Path(r"E:\opencode\qwen3-embed-cache-2026-09-19")
STAGE5_CORR_CACHE_ROOT = Path(r"E:\opencode\qwen3-embed-cache-stage5-corrected-2026-09-20")
RESERVE_CACHE_ROOT = Path(r"E:\opencode\qwen3-embed-cache-saleor-reserve-300-2026-09-20")
CORRECTED_WORK = Path(r"E:\opencode\stage5-corrected-2026-09-20")
RESERVE_WORK = Path(r"E:\opencode\saleor-reserve-300-2026-09-20")
SC_DATASET = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor"
OUT_DIR = _PROJECT_DIR / "research" / "saleor-reserve-300-rmcss"
SAMPLE = OUT_DIR / "saleor_reserve_300_sample.json"
SIP_RECORDS = OUT_DIR / "sip_300_run_records.jsonl"
PRICE_PER_1M = 0.01
CEILING_USD = 1.75  # amended P89; only embeddings consume this now (SIP already spent)
SENTINEL_FINITE_BOUND = 10.0


class _Task:
    __slots__ = ("case_id", "repository", "parent_commit", "intent", "write_set",
                 "proxy", "universe_paths", "universe_records", "graph_edges")

    def __init__(self, **kw: object) -> None:
        for k, v in kw.items():
            setattr(self, k, v)


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


def build_task_map() -> dict[str, _Task]:
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))["selected_ids"]
    sip = {}
    for line in SIP_RECORDS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            sip.setdefault(r["case_id"], set(r["predicted_write_set"]))
    tasks: dict[str, _Task] = {}
    for cid in sample:
        case_dir = SC_DATASET / "scientific" / cid
        mani = json.loads((case_dir / "case_manifest.json").read_text(encoding="utf-8"))
        intent = json.loads((case_dir / "public" / "intent.json").read_text(encoding="utf-8"))
        uni = json.loads((case_dir / "public" / "candidate_universe.json").read_text(encoding="utf-8"))
        graph = json.loads((case_dir / "public" / "dependency_graph.json").read_text(encoding="utf-8"))
        tasks[cid] = _Task(
            case_id=cid, repository="saleor",
            parent_commit=mani["record"]["parent_commit"],
            intent=intent["intent_text"],
            write_set=sip.get(cid, set()),
            proxy=set(),  # LABEL-FREE: proxy joined only at outcome-open (§19)
            universe_paths=sorted(r2["path"] for r2 in uni["records"]),
            universe_records={str(r2["path"]): r2 for r2 in uni["records"]},
            graph_edges=tuple((s, d2) for s, d2 in graph.get("edges", [])),
        )
    return tasks


def build_plan(blob_texts: dict[str, str]) -> tuple[dict[str, list[str]], dict[str, str]]:
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
    t0_total = time.monotonic()
    tasks = build_task_map()
    sample_ids = sorted(tasks)
    print(f"[s300-dense] tasks {len(tasks)}")

    # ---- blob texts (DEV + stage5-corrected + reserve-300 materialized) ----
    dev_blob_texts = json.loads(BLOB_CACHE.read_text(encoding="utf-8"))
    corr_blob_texts = json.loads((CORRECTED_WORK / "missing_blob_texts.json").read_text(encoding="utf-8")) if (CORRECTED_WORK / "missing_blob_texts.json").exists() else {}
    res_blob_texts = json.loads((RESERVE_WORK / "missing_blob_texts.json").read_text(encoding="utf-8")) if (RESERVE_WORK / "missing_blob_texts.json").exists() else {}
    blob_texts: dict[str, str] = {**dev_blob_texts, **corr_blob_texts, **res_blob_texts}
    plan, unit_texts = build_plan(blob_texts)
    print(f"[s300-dense] blob texts: dev {len(dev_blob_texts)} + corr {len(corr_blob_texts)} + reserve {len(res_blob_texts)} = {len(blob_texts)}; distinct units {len(unit_texts)}")

    # ---- embedding caches ----
    dev_mat, dev_idx = load_dev_matrix()
    corr_cache = ChunkCache(STAGE5_CORR_CACHE_ROOT / "realization_A")
    res_cache = ChunkCache(RESERVE_CACHE_ROOT / "realization_A")
    print(f"[s300-dense] dev matrix {dev_mat.shape}; corr cache {len(corr_cache)}; reserve cache {len(res_cache)}")

    def covered(k: str) -> bool:
        return k in dev_idx or k in corr_cache.index or k in res_cache.index

    # ---- queries (dedupe identical intent texts; embed unique only) ----
    queries = {cid: tasks[cid].intent for cid in sample_ids}
    qcache = ChunkCache(RESERVE_CACHE_ROOT / "queries")
    unique_q = sorted(set(queries.values()))
    to_embed_q = qcache.missing(unique_q)

    # ---- cost guard: live price + projection BEFORE any paid call ----
    price = _live_price()
    prompt_price = float((price or {}).get("prompt", 0) or 0)
    if prompt_price <= 0:
        print("LIVE_PRICE_UNVERIFIED - STOP")
        return 1
    print(f"[s300-dense] live price prompt ${prompt_price:.12f}/token (= ${prompt_price * 1e6:.4f}/M)")

    missing_units = [k for k in unit_texts if not covered(k)]
    est_unit_tokens = sum(len(unit_texts[k]) / 3.5 for k in missing_units)
    proj_unit = est_unit_tokens / 1e6 * prompt_price
    proj_q = sum(len(t) / 3.5 for t in unique_q) / 1e6 * prompt_price
    proj_total = proj_unit + proj_q
    print(f"[s300-dense] missing units {len(missing_units)} (est ${proj_unit:.4f}); queries {len(to_embed_q)} (est ${proj_q:.4f}); TOTAL projected ${proj_total:.4f} (ceiling ${CEILING_USD})")
    if proj_total > CEILING_USD:
        print(f"COST_STOP projected ${proj_total:.4f} > ${CEILING_USD}; STOP")
        return 1

    client: OpenRouterEmbeddingsClient | None = None
    api_key = os.environ.get("OPENROUTER_API_KEY")
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
        print(f"[s300-dense] query embed {len(to_embed_q)} unique cost ${client.ledger.cost_usd:.6f} tokens {client.ledger.prompt_tokens}", flush=True)
    qvec: dict[str, np.ndarray] = {}
    for cid in sample_ids:
        qvec[cid] = _l2(qcache.get([queries[cid]])[0])

    # ---- embed missing units ----
    if missing_units:
        assert client is not None
        texts = [unit_texts[k] for k in missing_units]
        vecs = client.embed(texts)
        res_cache.add(texts, vecs)
        print(f"[s300-dense] embedded missing units {len(missing_units)} cost ${client.ledger.cost_usd:.6f} tokens {client.ledger.prompt_tokens}", flush=True)
    res_mat = res_cache.matrix
    if res_mat is None:
        res_mat = np.zeros((0, dev_mat.shape[1]), dtype=np.float32)

    still_missing = [k for k in unit_texts if not covered(k)]
    if still_missing:
        print(f"EMBEDDING_RESOLUTION_FAIL: {len(still_missing)} units unresolved -> FAIL")
        return 1
    print(f"[s300-dense] distinct units {len(unit_texts)}; embedding coverage 100%")

    # ---- score all files (CASE A/B/C) ----
    def unit_vec(k: str) -> np.ndarray:
        if k in dev_idx:
            return dev_mat[dev_idx[k]]
        if k in corr_cache.index:
            assert corr_cache.matrix is not None
            return corr_cache.matrix[corr_cache.index[k]]
        return res_mat[res_cache.index[k]]

    score_rows: list[dict] = []
    t_start = time.monotonic()
    for idx, cid in enumerate(sample_ids, start=1):
        tr = tasks[cid]
        blob_sha = {path: rec["sha256"] for path, rec in tr.universe_records.items()}
        qv = qvec[cid]
        scores: dict[str, float] = {}
        for path in tr.universe_paths:
            sha = blob_sha.get(path)
            keys = plan.get(sha, []) if sha else []
            if not keys:
                # CASE C: no embeddable unit -> NaN
                continue
            missing = [k for k in keys if not covered(k)]
            if missing:
                print(f"EMBEDDING_RESOLUTION_FAIL {cid} {path}: {len(missing)}/{len(keys)} -> FAIL")
                return 1
            unit_cos = [float(unit_vec(k) @ qv) for k in keys]
            score = aggregate_file_score([(k, float(c)) for k, c in zip(keys, unit_cos, strict=True)])
            if not np.isfinite(score) or abs(score) > SENTINEL_FINITE_BOUND:
                print(f"SCORE_RANGE_GUARD_FAIL {cid} {path}: {score} -> FAIL")
                return 1
            scores[path] = score
        ranked = sorted(tr.universe_paths, key=lambda p: (-scores.get(p, -1e9), p))
        dense = {p: i + 1 for i, p in enumerate(ranked)}
        for path in tr.universe_paths:
            score_rows.append({
                "case_id": cid, "repository": "saleor",
                "parent_commit": tr.parent_commit, "file_path": path,
                "dense_file_score": float(scores.get(path, np.nan)),
                "dense_rank": int(dense[path]),
                "in_sparse": bool(path in tr.write_set),
                "query_sha256": sha256_text(queries[cid]),
                "model_id": "qwen/qwen3-embedding-8b", "provider": "DeepInfra",
                "realization_id": "A",
            })
        if idx % 10 == 0 or idx == len(sample_ids):
            el = time.monotonic() - t_start
            rate = el / idx
            eta = rate * (len(sample_ids) - idx)
            print(f"[s300-dense] scoring {idx}/{len(sample_ids)} elapsed={el:.0f}s "
                  f"rate={rate:.1f}s/task ETA={eta:.0f}s", flush=True)
    parquet = pd.DataFrame(score_rows)
    n_sent = int((parquet["dense_file_score"] == -1e9).sum())
    if n_sent:
        print(f"SENTINEL_GUARD_FAIL: {n_sent} rows == -1e9 -> FAIL")
        return 1
    parquet.to_parquet(OUT_DIR / "full_file_scores_saleor300.parquet", index=False, compression="zstd")
    print(f"[s300-dense] dense rows {len(parquet)} -> full_file_scores_saleor300.parquet", flush=True)

    # ---- memory bundles (parent-only Repository Memory) ----
    mem_out: dict[str, dict] = {}
    rh = RepoHistory("saleor")
    t_start = time.monotonic()
    for idx, cid in enumerate(sample_ids, start=1):
        tr = tasks[cid]
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
            "repository": "saleor", "parent": tr.parent_commit,
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
        if idx % 10 == 0 or idx == len(sample_ids):
            el = time.monotonic() - t_start
            rate = el / idx
            eta = rate * (len(sample_ids) - idx)
            print(f"[s300-dense] memory {idx}/{len(sample_ids)} elapsed={el:.0f}s "
                  f"rate={rate:.1f}s/task ETA={eta:.0f}s", flush=True)
    (OUT_DIR / "memory_bundles_saleor300.json").write_text(
        json.dumps({"tasks": mem_out}, sort_keys=True), encoding="utf-8")
    print(f"[s300-dense] memory bundles {len(mem_out)} -> memory_bundles_saleor300.json", flush=True)

    # ---- candidate rows (frozen 11 features; proxy = EMPTY (label-free)) ----
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
        pd.read_parquet(OUT_DIR / "full_file_scores_saleor300.parquet"),
        tasks, mem_bundles)
    from benchmark.memory_rescue.candidates import rows_to_frame
    frame = rows_to_frame(rows)
    frame.to_parquet(OUT_DIR / "candidate_rows_saleor300.parquet", index=False, compression="zstd")
    print(f"[s300-dense] candidate rows {len(frame)} tasks {frame['case_id'].nunique()} "
          f"(label column is EMPTY/label-free; labels joined at outcome-open)")
    print(f"[s300-dense] total elapsed {time.monotonic() - t0_total:.0f}s; DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
