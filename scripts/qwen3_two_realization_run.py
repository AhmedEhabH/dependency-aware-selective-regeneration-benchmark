#!/usr/bin/env python3
"""QWEN3 TWO-REALIZATION REPLICATION runner (T3, DEVELOPMENT).

Mission: QWEN3_TWO_REALIZATION_REPLICATION_2026-09-19. Runs TWO COMPLETE
INDEPENDENT realizations (A and B) of the hosted Qwen embeddings
(qwen/qwen3-embedding-8b @ DeepInfra, $0.01/M, fallback disabled) over the
FULL legal DEVELOPMENT population (djangoCMS 174 + Saleor 149; 49,705 code
units per the frozen token estimate; whitespace-only units excluded per the
frozen execution clarification protocol §12.9, so 49,703 embeddable units).

Per realization:
  1. embed all distinct code-unit texts (batch 64, resume-safe chunk cache);
  2. embed the 323 parent-visible query texts;
  3. frozen adapter: score(file) = MAX cosine over units; rank the OMITTED
     candidates desc by score, asc path (Route-B matched pool + tie-break);
  4. persist a LABEL-FREE full-file-score Parquet (engineering artifact for a
     FUTURE calibrated ADD+DROP study) and inference-only task_rankings;
  5. the target-aware metrics / paired bootstrap CIs / frozen gate are computed
     in a SEPARATE analyze step (labels joined AFTER ranking is frozen).

Each realization uses its OWN cache directory on E: (never shares embeddings).
Cumulative budget guard: prior probes (~$0.023) + spent + projected remaining
must stay below the frozen $0.50 ceiling; otherwise STOP and report.

ZERO sealed data. NO Stage-5 execution. NO calibrated set selection.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

import numpy as np  # noqa: E402

from benchmark.recall.data import (  # noqa: E402
    SALEOR_DATASET,
    V1_DATASET,
    V2_DATASET,
    load_dev_tasks,
)
from benchmark.recall.rankers import rank_bm25, rank_composite  # noqa: E402
from benchmark.signal.code_units import extract_code_units, sha256_text  # noqa: E402
from benchmark.signal.or_embeddings import (  # noqa: E402
    OPENROUTER_EMBED_MODEL,
    OpenRouterEmbeddingsClient,
)
from benchmark.signal.swrank_adapter import aggregate_file_score, rank_files  # noqa: E402
from scripts.route_b_v2_robustness import load_case  # noqa: E402

BLOB_CACHE = Path(r"C:\Users\Ahmed\AppData\Local\Temp\opencode\swerank-cache\blob_text.json")
# Embedding caches live OUTSIDE the repository on E: (storage discipline).
CACHE_ROOT = Path(r"E:\opencode\qwen3-embed-cache-2026-09-19")
OUT_DIR = _PROJECT_DIR / "research" / "contamination-bridge" / "qwen_embed"

BATCH = 64
PRICE_PER_1M = 0.01
CEILING_USD = 0.50
PRIOR_PROBES_USD = 0.023
# Frozen token estimate (reports/qwen3_embed_bridge_budget_freeze.json):
UNIT_TOKENS_TOTAL = 21_870_401
QUERY_TOKENS_TOTAL = 12_128
N_UNITS_ESTIMATE = 49_705
AVG_UNIT_TOKENS = UNIT_TOKENS_TOTAL / N_UNITS_ESTIMATE
AVG_QUERY_TOKENS = QUERY_TOKENS_TOTAL / 323


def _dataset_for(repo: str, role: str) -> Path:
    if repo == "saleor":
        return SALEOR_DATASET
    return V1_DATASET if role.startswith("V1") else V2_DATASET


def _valid_unit(text: str) -> bool:
    """Frozen input-preparation rule (protocol §12.9): whitespace-only code
    units are skipped (the endpoint rejects empty strings; no target effect)."""
    return bool(text and text.strip())


def build_unit_corpus() -> dict[str, str]:
    """unit_sha -> unit text for ALL DEVELOPMENT blobs (frozen extraction)."""
    blob_texts = json.loads(BLOB_CACHE.read_text(encoding="utf-8"))
    units: dict[str, str] = {}
    for text in blob_texts.values():
        if text is None:
            continue
        for u in extract_code_units(text):
            if not _valid_unit(u):
                continue
            units.setdefault(sha256_text(u), u)
    return units


def build_task_files(tasks) -> dict:
    out: dict[str, dict] = {}
    for t in tasks:
        case = load_case(t.case_id, _dataset_for(t.repository, t.role))
        out[t.case_id] = {
            "repository": t.repository,
            "intent_text": t.intent_text,
            "paths": [str(p) for p in case["paths"]],
            "blob_sha": {str(r["path"]): r["sha256"] for r in case["records"]},
        }
    return out


class ChunkCache:
    """Resume-safe chunked embedding cache (float32 npy parts + index.json).

    Each add() writes ONE small part file (<=64 rows x dim), so total I/O is
    O(n), unlike a whole-matrix rewrite per batch. Load concatenates parts.
    """

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = Path(cache_dir)
        self.parts_dir = self.cache_dir / "parts"
        self.parts_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.cache_dir / "index.json"
        self.dim: int | None = None
        self.index: dict[str, int] = {}
        self._part_rows: list[int] = []
        self.matrix: np.ndarray | None = None
        if self.index_path.exists():
            self.index = json.loads(self.index_path.read_text(encoding="utf-8"))
            for part in sorted(self.parts_dir.glob("part_*.npy")):
                arr = np.load(part)
                if self.dim is None:
                    self.dim = arr.shape[1]
                self._part_rows.append(arr.shape[0])
        if self._part_rows:
            total = sum(self._part_rows)
            self.matrix = np.zeros((total, self.dim), dtype=np.float32)
            row = 0
            for part in sorted(self.parts_dir.glob("part_*.npy")):
                arr = np.load(part)
                self.matrix[row:row + arr.shape[0]] = arr
                row += arr.shape[0]

    def missing(self, texts: list[str]) -> list[str]:
        return [t for t in texts if sha256_text(t) not in self.index]

    def add(self, texts: list[str], vectors: list[list[float]]) -> None:
        base = len(self.index)
        arr = np.asarray(vectors, dtype=np.float32)
        if self.dim is None:
            self.dim = arr.shape[1]
        elif arr.shape[1] != self.dim:
            raise ValueError(f"dim mismatch: {arr.shape[1]} != {self.dim}")
        part_name = f"part_{base:06d}.npy"
        np.save(self.parts_dir / part_name, arr)
        for i, t in enumerate(texts):
            self.index[sha256_text(t)] = base + i
        self.index_path.write_text(json.dumps(self.index), encoding="utf-8")
        if self.matrix is None:
            self.matrix = arr
        else:
            self.matrix = np.concatenate([self.matrix, arr], axis=0)

    def get(self, texts: list[str]) -> np.ndarray:
        rows = [self.index[sha256_text(t)] for t in texts]
        assert self.matrix is not None
        return self.matrix[rows]

    def __len__(self) -> int:
        return len(self.index)


def _l2(v: np.ndarray) -> np.ndarray:
    """Row-wise L2 normalization (see qwen3_embed_bridge_run.py; axis-aware)."""
    arr = np.asarray(v, dtype=np.float64)
    if arr.ndim == 1:
        n = float(np.linalg.norm(arr))
        return (arr / n if n > 0 else arr).astype(np.float32)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (arr / norms).astype(np.float32)


def _projected_cost(ledger_cost: float, remaining_units: int, remaining_queries: int) -> float:
    """Fail-closed budget projection: spent + projected remaining + prior probes."""
    projected_remaining = (remaining_units * AVG_UNIT_TOKENS + remaining_queries * AVG_QUERY_TOKENS)
    projected_remaining_usd = projected_remaining / 1e6 * PRICE_PER_1M
    return PRIOR_PROBES_USD + ledger_cost + projected_remaining_usd


def _embed_all(client: OpenRouterEmbeddingsClient, cache: ChunkCache,
               texts: list[str], kind: str, budget_state: dict) -> None:
    """Embed `texts` with the budget guard; cache-backed and resume-safe."""
    to_embed = cache.missing(texts)
    total = len(to_embed)
    done = 0
    counter_key = "remaining_units" if kind == "corpus" else "remaining_queries"
    for i in range(0, total, BATCH):
        chunk = to_embed[i:i + BATCH]
        # Budget guard BEFORE each request. prior_spent persists across
        # process restarts; client.ledger.cost_usd is THIS process only.
        rem_units = budget_state["remaining_units"]
        rem_queries = budget_state["remaining_queries"]
        spent_total = budget_state["prior_spent"] + client.ledger.cost_usd
        proj = _projected_cost(spent_total, rem_units, rem_queries)
        if proj >= CEILING_USD:
            raise SystemExit(
                f"BUDGET_STOP projected_cumulative={proj:.4f} >= ceiling={CEILING_USD}; "
                f"cumulative_spent={spent_total:.4f} (prior={budget_state['prior_spent']:.4f} "
                f"this_process={client.ledger.cost_usd:.4f}) remaining_units={rem_units} "
                f"remaining_queries={rem_queries}. Report the exact projection and STOP.")
        vecs = client.embed(chunk)
        cache.add(chunk, vecs)
        done += len(chunk)
        budget_state[counter_key] -= len(chunk)
        spend_path = cache.cache_dir / "cumulative_spend.json"
        spend_path.write_text(json.dumps({
            "cost_usd": budget_state["prior_spent"] + client.ledger.cost_usd,
            "prompt_tokens": client.ledger.prompt_tokens,
            "requests": client.ledger.requests,
        }), encoding="utf-8")
        if (done // BATCH) % 25 == 0:
            print(f"  [{kind}] {done}/{total} embedded; cost ${client.ledger.cost_usd:.4f} "
                  f"(cum proj ${proj:.4f})", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--realization", choices=("A", "B"), required=True)
    args = ap.parse_args()

    rid = args.realization
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("OPENROUTER_API_KEY not set")
        return 1
    client = OpenRouterEmbeddingsClient(api_key=api_key, batch_size=BATCH)
    assert client.model == OPENROUTER_EMBED_MODEL

    cache = ChunkCache(CACHE_ROOT / f"realization_{rid}")
    # Persistent cumulative spend for THIS realization across process restarts
    # (the client ledger only tracks the current process).
    spend_path = cache.cache_dir / "cumulative_spend.json"
    prior_spent: float = 0.0
    if spend_path.exists():
        prior_spent = float(json.loads(spend_path.read_text(encoding="utf-8")).get("cost_usd", 0.0))
    t_start = time.perf_counter()

    units = build_unit_corpus()
    unit_texts = [units[k] for k in sorted(units)]  # deterministic ordering
    print(f"[{rid}] corpus: {len(unit_texts)} distinct units "
          f"(frozen estimate 49,705; whitespace-only excluded -> {len(unit_texts)})")

    tasks = load_dev_tasks()
    query_texts = [t.intent_text for t in tasks]
    print(f"[{rid}] queries: {len(query_texts)}")

    budget_state = {
        "remaining_units": len(cache.missing(unit_texts)),
        "remaining_queries": len(cache.missing(query_texts)),
        "prior_spent": prior_spent,
    }

    # ---- embed corpus units ----
    t0 = time.perf_counter()
    _embed_all(client, cache, unit_texts, "corpus", budget_state)
    t_corpus = time.perf_counter() - t0
    print(f"[{rid}] corpus done in {t_corpus:.1f}s; cost ${client.ledger.cost_usd:.4f}")

    # ---- embed queries ----
    t0 = time.perf_counter()
    _embed_all(client, cache, query_texts, "query", budget_state)
    t_queries = time.perf_counter() - t0
    print(f"[{rid}] queries done in {t_queries:.1f}s; cost ${client.ledger.cost_usd:.4f}")

    # ---- per-task file scores (MAX cosine) + rankings ----
    task_files = build_task_files(tasks)
    blob_texts = json.loads(BLOB_CACHE.read_text(encoding="utf-8"))
    plan: dict[str, list[str]] = {}
    for sha, text in blob_texts.items():
        if text is None:
            plan[sha] = []
            continue
        plan[sha] = [sha256_text(u) for u in extract_code_units(text) if _valid_unit(u)]

    query_emb = {sha256_text(t): _l2(cache.get([t])[0]) for t in query_texts}
    unit_mat = cache.matrix
    assert unit_mat is not None

    # Label-free full-file-score rows (engineering artifact for the future
    # calibrated ADD+DROP study). dense_rank = full-universe rank (all legal
    # production files), in_sparse = file in the Sparse write set.
    score_rows: list[dict] = []
    results: dict[str, dict] = {}
    t0 = time.perf_counter()
    for cid, tf in task_files.items():
        t = next(x for x in tasks if x.case_id == cid)
        q = query_emb[sha256_text(tf["intent_text"])]
        scores: dict[str, float] = {}
        for path in tf["paths"]:
            sha = tf["blob_sha"].get(path)
            if sha is None:
                continue
            keys = plan.get(sha, [])
            if not keys:
                continue
            rows = [cache.index[k] for k in keys]
            unit_cos = unit_mat[rows] @ q
            scores[path] = aggregate_file_score(
                [(k, float(c)) for k, c in zip(keys, unit_cos, strict=True)])
        universe = tf["paths"]
        write_set = frozenset(t.write_set)
        ranked = rank_files(scores, universe, write_set)
        # Full-universe dense ranking (label-free artifact).
        full_rank = sorted(universe, key=lambda p: (-scores.get(p, -1e9), p))
        dense_rank = {p: i + 1 for i, p in enumerate(full_rank)}
        for path in universe:
            score_rows.append({
                "case_id": cid,
                "repository": tf["repository"],
                "parent_commit": t.parent_commit,
                "file_path": path,
                "dense_file_score": float(scores.get(path, np.nan)),
                "dense_rank": int(dense_rank[path]),
                "in_sparse": bool(path in write_set),
                "query_sha256": sha256_text(tf["intent_text"]),
                "model_id": OPENROUTER_EMBED_MODEL,
                "provider": "DeepInfra",
                "realization_id": rid,
            })
        results[cid] = {
            "repository": tf["repository"],
            "case_id": cid,
            "write_set": sorted(t.write_set),
            "omitted_size": len([p for p in universe if p not in write_set]),
            "qwen_ranked": ranked,
            "routeb_ranked": rank_composite(t),
            "bm25_ranked": rank_bm25(t),
            "query_sha256": sha256_text(tf["intent_text"]),
            "parent_commit": t.parent_commit,
            "n_files": len(universe),
        }
    t_rank = time.perf_counter() - t0

    # ---- persist (realization-specific subdir) ----
    # task_rankings stores the top-10 ranked lists per method (the maximum
    # evaluated budget; the frozen SweRank convention stores top-10 only).
    rdir = OUT_DIR / f"realization_{rid}"
    rdir.mkdir(parents=True, exist_ok=True)
    for _cid, v in results.items():
        for k in ("qwen_ranked", "routeb_ranked", "bm25_ranked"):
            v[k] = v[k][:10]
    rdir.joinpath("task_rankings.json").write_text(
        json.dumps(results, indent=1), encoding="utf-8")

    import pandas as pd
    df = pd.DataFrame(score_rows)
    parquet_path = rdir / "full_file_scores.parquet"
    df.to_parquet(parquet_path, index=False, compression="zstd")
    print(f"[{rid}] full-file score table: {len(df)} rows -> {parquet_path.name} "
          f"({parquet_path.stat().st_size / 1e6:.2f} MB)")

    cumulative_spent = budget_state["prior_spent"] + client.ledger.cost_usd
    rdir.joinpath("ledger.json").write_text(json.dumps({
        "realization": rid,
        "requests": client.ledger.requests,
        "prompt_tokens": client.ledger.prompt_tokens,
        "cost_usd": client.ledger.cost_usd,
        "transport_failures": client.ledger.transport_failures,
        "transport_retries": client.ledger.transport_retries,
        "permanent_failures": client.ledger.permanent_failures,
        "corpus_seconds": round(t_corpus, 2),
        "query_seconds": round(t_queries, 2),
        "ranking_seconds": round(t_rank, 2),
        "total_seconds": round(time.perf_counter() - t_start, 2),
        "n_units": len(unit_texts),
        "n_queries": len(query_texts),
        "n_score_rows": len(score_rows),
        "cumulative_spend_including_prior_probes": round(
            PRIOR_PROBES_USD + cumulative_spent, 6),
        "ceiling_usd": CEILING_USD,
    }, indent=2), encoding="utf-8")

    print(json.dumps({
        "realization": rid,
        "requests": client.ledger.requests,
        "prompt_tokens": client.ledger.prompt_tokens,
        "cost_usd": round(client.ledger.cost_usd, 6),
        "permanent_failures": client.ledger.permanent_failures,
        "projected_cumulative_usd": round(
            PRIOR_PROBES_USD + cumulative_spent, 6),
    }, indent=1))
    print(f"[{rid}] DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
