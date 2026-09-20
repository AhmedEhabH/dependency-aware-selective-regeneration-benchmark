#!/usr/bin/env python3
"""ISSUE_GROUNDED_INTENT_HEADROOM - compute ARM I dense rankings (T3).

For the PRIMARY paired (temporally-clean) population, embed ONLY the new
issue-query texts (title + body) through the SAME frozen Qwen model/provider,
then score every file in the SAME frozen candidate universe against the SAME
persisted code-unit embeddings (E: cache) with the SAME file-MAX cosine
aggregation and SAME full-universe dense rank.

ARM M rankings are read from the frozen realizations (no recomputation).

Hard budget guard: live price verified before any call; incremental cost
projection must stay below $0.05, else STOP before paid calls.
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

import numpy as np  # noqa: E402

from benchmark.issue_grounded.corpus import load_corpus  # noqa: E402
from benchmark.issue_grounded.dense import (  # noqa: E402
    arm_i_queries,
    build_plan,
    load_cache_matrix,
    rank_files_full_universe,
)
from benchmark.recall.data import SALEOR_DATASET, V1_DATASET, V2_DATASET, load_dev_tasks  # noqa: E402
from benchmark.signal.or_embeddings import (  # noqa: E402
    OPENROUTER_EMBED_MODEL,
    OpenRouterEmbeddingsClient,
)
from scripts.route_b_v2_robustness import load_case  # noqa: E402

BLOB_CACHE = Path(r"C:\Users\Ahmed\AppData\Local\Temp\opencode\swerank-cache\blob_text.json")
CACHE_ROOT = Path(r"E:\opencode\qwen3-embed-cache-2026-09-19")
QWEN_DIR = _PROJECT_DIR / "research" / "contamination-bridge" / "qwen_embed"
OUT_DIR = _PROJECT_DIR / "research" / "issue-grounded-intent-headroom"
CEILING_QUERY_USD = 0.05
PRICE_PER_1M = 0.01  # live-verified qwen/qwen3-embedding-8b @ DeepInfra (2026-09-20)


def _dataset_for(repo: str, role: str) -> Path:
    if repo == "saleor":
        return SALEOR_DATASET
    return V2_DATASET if role != "V1_DEV" else V1_DATASET


def _task_files(tasks) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for t in tasks:
        case = load_case(t.case_id, _dataset_for(t.repository, t.role))
        out[t.case_id] = {
            "repository": t.repository,
            "intent_text": t.intent_text,
            "paths": [str(p) for p in case["paths"]],
            "blob_sha": {str(r["path"]): r["sha256"] for r in case["records"]},
            "proxy": sorted(t.proxy),
        }
    return out


def main() -> int:
    tasks = load_dev_tasks()
    corpus = load_corpus(OUT_DIR / "issue_corpus.json")
    clean_ids = [
        r["case_id"] for r in corpus["records"]
        if any(f == "TEMPORALLY_CLEAN" for f in r["temporal_flag"])
    ]
    queries = arm_i_queries(clean_ids, OUT_DIR / "issue_corpus.json")
    print(f"[arm-i] clean paired population: {len(clean_ids)} tasks; queries: {len(queries)}")
    n_words = sum(len(q.split()) for q in queries.values())
    est_tokens = int(n_words * 1.35) + 12 * 8
    proj_cost = est_tokens / 1e6 * PRICE_PER_1M
    print(f"[arm-i] projected query tokens ~{est_tokens}; cost ~${proj_cost:.6f} "
          f"(ceiling ${CEILING_QUERY_USD})")

    # Live-price verification (mission §1: verify before any Qwen call).
    price = _live_price()
    if price.get("prompt") is None:
        raise SystemExit("LIVE_PRICE_UNVERIFIED - cannot confirm qwen/qwen3-embedding-8b price; STOP")
    print(f"[arm-i] live price verified: prompt ${price['prompt']}/token "
          f"(= ${float(price['prompt']) * 1e6}/M)")

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("OPENROUTER_API_KEY not set")
        return 1

    client = OpenRouterEmbeddingsClient(api_key=api_key, batch_size=64)
    assert client.model == OPENROUTER_EMBED_MODEL
    if proj_cost > CEILING_QUERY_USD:
        raise SystemExit(f"BUDGET_STOP projected ${proj_cost:.4f} > ${CEILING_QUERY_USD}")

    ordered = [q for _, q in sorted(queries.items())]
    t0 = time.perf_counter()
    vecs = client.embed(ordered)
    query_emb = {cid: np.asarray(v, dtype=np.float32)
                 for cid, v in zip(sorted(queries), vecs, strict=True)}
    print(f"[arm-i] queries embedded: {len(vecs)}; cost ${client.ledger.cost_usd:.6f}; "
          f"tokens {client.ledger.prompt_tokens}; {time.perf_counter()-t0:.1f}s")

    blob_texts = json.loads(BLOB_CACHE.read_text(encoding="utf-8"))
    plan = build_plan(blob_texts)
    task_files = _task_files(tasks)
    task_files_by_id = {cid: tf for cid, tf in task_files.items() if cid in queries}

    results = {}
    ledger_parts = {}
    for rid in ("A", "B"):
        unit_mat, cache_idx, dim = load_cache_matrix(rid, CACHE_ROOT)
        ledger_parts[rid] = {"rows": unit_mat.shape[0], "dim": dim}
        t1 = time.perf_counter()
        for cid, _q in sorted(queries.items()):
            tf = task_files_by_id[cid]
            file_blobs = tf["blob_sha"]
            dense = rank_files_full_universe(query_emb[cid], unit_mat, cache_idx,
                                             file_blobs, plan, tf["paths"])
            results.setdefault(cid, {})[rid] = {
                "dense_rank": dense,
                "proxy": list(tf["proxy"]),
                "repository": tf["repository"],
            }
        print(f"[arm-i] realization {rid} ranked in {time.perf_counter()-t1:.1f}s")

    # Persist minimal artifact.
    payload = {cid: {rid: {"repository": v[rid]["repository"],
                           "proxy": v[rid]["proxy"],
                           "proxy_dense_rank": {p: v[rid]["dense_rank"].get(p) for p in v[rid]["proxy"]}}
                     for rid in ("A", "B")}
               for cid, v in results.items()}
    (OUT_DIR / "arm_i_dense.json").write_text(
        json.dumps({"model": OPENROUTER_EMBED_MODEL, "provider": "DeepInfra",
                    "n_tasks": len(payload), "tasks": payload,
                    "query_ledger": {"prompt_tokens": client.ledger.prompt_tokens,
                                     "cost_usd": client.ledger.cost_usd,
                                     "requests": client.ledger.requests}}, indent=1),
        encoding="utf-8")
    print(f"[arm-i] saved arm_i_dense.json ({len(payload)} tasks)")
    print(json.dumps(ledger_parts, indent=1))
    print("[arm-i] DONE")
    return 0


def _live_price():
    """Fetch the OpenRouter embeddings catalog (public) and return the prompt
    price dict for qwen/qwen3-embedding-8b. Empty dict when not found."""
    import urllib.error

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


if __name__ == "__main__":
    raise SystemExit(main())
