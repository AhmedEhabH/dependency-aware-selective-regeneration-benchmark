#!/usr/bin/env python3
# ruff: noqa: E501, N803, N806
"""QWEN3-EMBEDDING-8B contamination-robustness bridge runner (T3, DEVELOPMENT).

Resumes the frozen bridge (docs/QWEN3_EMBED_CONTAMINATION_ROBUSTNESS_PROTOCOL_FROZEN.md)
using the corrected availability probe + pinned DeepInfra provider. Scientific
endpoint: POST https://openrouter.ai/api/v1/embeddings.

Modes:
  --probe     : embed ~200 already-exposed DEVELOPMENT code units twice,
                report max cosine drift (TECHNICAL determinism probe only).
  --full      : embed the FULL DEV corpus (49,705 units) + 323 queries
                (cache-backed, resume-safe), then compute file-level
                metrics / paired bootstrap CIs / frozen gate.

ZERO sealed data. NO Stage-5 execution. Provider pinned, fallback disabled.
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

from benchmark.recall.data import (  # noqa: E402
    SALEOR_DATASET,
    V1_DATASET,
    V2_DATASET,
    load_dev_tasks,
)
from benchmark.recall.rankers import rank_bm25, rank_composite  # noqa: E402
from benchmark.signal.code_units import extract_code_units, sha256_text  # noqa: E402
from benchmark.signal.metrics import METRIC_NAMES, paired_bootstrap  # noqa: E402
from benchmark.signal.or_embeddings import (  # noqa: E402
    OPENROUTER_EMBED_MODEL,
    OpenRouterEmbeddingsClient,
)
from benchmark.signal.swrank_adapter import aggregate_file_score, rank_files  # noqa: E402
from scripts.route_b_v2_robustness import load_case  # noqa: E402

BLOB_CACHE = Path(r"C:\Users\Ahmed\AppData\Local\Temp\opencode\swerank-cache\blob_text.json")
EMB_CACHE_DIR = Path(r"C:\Users\Ahmed\AppData\Local\Temp\opencode\qwen3-cache")
OUT_DIR = _PROJECT_DIR / "research" / "contamination-bridge" / "qwen_embed"

BATCH = 64
BUDGETS = (1, 3, 5, 10)
B_REF = 5
N_RESAMPLES = 10_000
SEED = 20260919


def _dataset_for(repo: str, role: str) -> Path:
    if repo == "saleor":
        return SALEOR_DATASET
    return V1_DATASET if role.startswith("V1") else V2_DATASET


def _valid_unit(text: str) -> bool:
    """Deterministic input-preparation rule (execution clarification, frozen
    before target-aware calls): whitespace-only code units are skipped because
    the embedding endpoint rejects empty strings. This has no target influence."""
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


class EmbeddingCache:
    """Resume-safe disk cache: input_sha -> row in embeddings.npy (float32)."""

    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.cache_dir / "index.json"
        self.data_path = self.cache_dir / "embeddings.npy"
        self.index: dict[str, int] = {}
        self.matrix: np.ndarray | None = None
        if self.index_path.exists():
            self.index = json.loads(self.index_path.read_text(encoding="utf-8"))
        if self.data_path.exists():
            self.matrix = np.load(self.data_path, mmap_mode=None)

    def missing(self, texts: list[str]) -> list[str]:
        return [t for t in texts if sha256_text(t) not in self.index]

    def add(self, texts: list[str], vectors: list[list[float]]) -> None:
        dim = len(vectors[0])
        base = int(self.matrix.shape[0]) if self.matrix is not None else 0
        new = np.zeros((base + len(texts), dim), dtype=np.float32)
        if self.matrix is not None:
            new[:base] = self.matrix
        for i, (t, v) in enumerate(zip(texts, vectors, strict=True)):
            self.index[sha256_text(t)] = base + i
            new[base + i] = v
        self.matrix = new
        np.save(self.data_path, self.matrix)
        self.index_path.write_text(json.dumps(self.index), encoding="utf-8")

    def get(self, texts: list[str]) -> np.ndarray:
        rows = [self.index[sha256_text(t)] for t in texts]
        assert self.matrix is not None
        return self.matrix[rows]

    def __len__(self) -> int:
        return len(self.index)


def _l2(v: np.ndarray) -> np.ndarray:
    """Row-wise L2 normalization (1-D vector or 2-D matrix of rows).

    NOTE: np.linalg.norm(v) with no axis returns the MATRIX Frobenius norm,
    which would NOT normalize rows (this was a probe bug on 2026-09-19 that
    made the determinism probe look nondeterministic).
    """
    arr = np.asarray(v, dtype=np.float64)
    if arr.ndim == 1:
        n = float(np.linalg.norm(arr))
        return (arr / n if n > 0 else arr).astype(np.float32)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (arr / norms).astype(np.float32)


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("probe", "stability", "full"), required=True)
    args = ap.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("OPENROUTER_API_KEY not set")
        return 1
    client = OpenRouterEmbeddingsClient(api_key=api_key, batch_size=BATCH)
    assert client.model == OPENROUTER_EMBED_MODEL

    units = build_unit_corpus()
    print(f"[corpus] {len(units)} distinct units")

    if args.mode == "probe":
        return _probe(client, units)
    if args.mode == "stability":
        return _stability(client, units)

    return _full(client, units)


def _probe(client: OpenRouterEmbeddingsClient, units: dict[str, str]) -> int:
    anchor = "def fact(n):\n    return 1 if n == 0 else n * fact(n - 1)"
    texts = [units[k] for k in list(units)[:200]] + [anchor]
    t0 = time.perf_counter()
    v1 = client.embed(texts)
    v2 = client.embed(texts)
    dt = time.perf_counter() - t0
    arr1 = _l2(np.asarray(v1, dtype=np.float32))
    arr2 = _l2(np.asarray(v2, dtype=np.float32))
    cos = np.sum(arr1 * arr2, axis=1)
    # cosine distance between the two identical-input embeddings (drift = 1 - cos)
    anchor_v = _l2(np.asarray(client.embed([anchor])[0], dtype=np.float32))
    anchor_cos_vs_call1 = float(np.dot(arr1[-1], anchor_v))
    anchor_cos_vs_call2 = float(np.dot(arr2[-1], anchor_v))

    # Ranking-stability check: rank the probe units by cosine to ONE parent-visible
    # DEVELOPMENT query using call-1 vs call-2 embeddings; compare top-10 overlap
    # and rank correlation. This tests whether the measured drift could change ties.
    tasks = load_dev_tasks()
    q_text = tasks[0].intent_text
    q = _l2(np.asarray(client.embed([q_text])[0], dtype=np.float32))
    s1 = arr1[:-1] @ q
    s2 = arr2[:-1] @ q
    order1 = np.argsort(-s1)
    order2 = np.argsort(-s2)
    top1 = set(order1[:10].tolist())
    top2 = set(order2[:10].tolist())
    overlap = len(top1 & top2) / 10.0
    # Kendall tau on the full 200-rank (normalized)
    from scipy.stats import kendalltau
    tau, _ = kendalltau(order1, order2)
    # adjacent-score gaps in call-1 order (|gap| tells whether drift can flip)
    ranked_s1 = np.sort(s1)[::-1]
    gaps = np.abs(np.diff(ranked_s1))
    max_drift = float(np.max(1.0 - cos))
    n_tight = int(np.sum(gaps < 2 * max_drift))
    top50_gaps = np.abs(np.diff(ranked_s1[:50]))
    n_tight_top50 = int(np.sum(top50_gaps < 2 * max_drift))
    rank_stable = bool(overlap >= 0.9 and n_tight_top50 == 0)
    out = {
        "n": len(texts),
        "dim": arr1.shape[1],
        "max_cosine_drift": float(np.max(1.0 - cos)),
        "mean_cosine_drift": float(np.mean(1.0 - cos)),
        "p99_cosine_drift": float(np.quantile(1.0 - cos, 0.99)),
        "min_cosine_sim": float(np.min(cos)),
        "max_cosine_sim": float(np.max(cos)),
        "identical_vectors": bool(np.array_equal(arr1, arr2)),
        "anchor_cos_call1_vs_fresh": anchor_cos_vs_call1,
        "anchor_cos_call2_vs_fresh": anchor_cos_vs_call2,
        "rank_stability": {
            "query_sha256": sha256_text(q_text),
            "top10_overlap_frac": round(float(overlap), 4),
            "kendall_tau_full": round(float(tau), 4),
            "max_cosine_drift": round(max_drift, 6),
            "n_adjacent_pairs_full_with_gap_lt_2x_drift": n_tight,
            "n_adjacent_pairs_top50_with_gap_lt_2x_drift": n_tight_top50,
            "verdict": "RANK_STABLE" if rank_stable else "RANK_DRIFT_PLAUSIBLE",
        },
        "wall_seconds": round(dt, 3),
        "ledger_requests": client.ledger.requests,
        "ledger_prompt_tokens": client.ledger.prompt_tokens,
        "ledger_cost_usd": client.ledger.cost_usd,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "probe.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


def _stability(client: OpenRouterEmbeddingsClient, units: dict[str, str]) -> int:
    """FILE-level ranking stability across two full realizations of a small set
    of complete DEVELOPMENT tasks (technical diagnostic only, no model
    selection). Answers: can the measured ~1e-4 cosine drift change the B=5
    file-level addition set?"""
    tasks = load_dev_tasks()
    sample = [t for t in tasks if t.repository == "djangocms"][:5]
    task_files = {t.case_id: build_task_files([t])[t.case_id] for t in sample}
    blob_texts = json.loads(BLOB_CACHE.read_text(encoding="utf-8"))
    plan = {}
    for sha, text in blob_texts.items():
        if text is None:
            plan[sha] = []
            continue
        plan[sha] = [sha256_text(u) for u in extract_code_units(text) if _valid_unit(u)]

    def realize():
        # second/independent realization: embed this task set's units + queries
        qs = [t.intent_text for t in sample]
        q_emb = {sha256_text(q): _l2(np.asarray(client.embed([q])[0], dtype=np.float32)) for q in qs}
        q_rows = {t.case_id: q_emb[sha256_text(t.intent_text)] for t in sample}
        # embed ONLY the units that appear in these 5 tasks (cheap)
        needed: dict[str, str] = {}
        for _cid, tf in task_files.items():
            for path in tf["paths"]:
                sha = tf["blob_sha"].get(path)
                if sha is None:
                    continue
                for k in plan.get(sha, []):
                    needed.setdefault(k, units[k])
        vecs = client.embed(list(needed.values()))
        emb = {sha256_text(t): v for t, v in zip(list(needed.values()), vecs, strict=True)}
        out = {}
        for cid, tf in task_files.items():
            q = q_rows[cid]
            scores = {}
            for path in tf["paths"]:
                sha = tf["blob_sha"].get(path)
                if sha is None:
                    continue
                keys = plan.get(sha, [])
                if not keys:
                    continue
                cs = [float(np.dot(_l2(emb[k]), q)) for k in keys]
                scores[path] = aggregate_file_score(list(zip(keys, cs, strict=True)))
            out[cid] = rank_files(scores, tf["paths"], frozenset())
        return out

    r1 = realize()
    r2 = realize()
    overlap_b5 = {}
    for cid in r1:
        set1 = set(r1[cid][:5])
        set2 = set(r2[cid][:5])
        overlap_b5[cid] = len(set1 & set2) / 5.0
    out = {
        "n_tasks": len(sample),
        "b5_file_set_overlap_frac": overlap_b5,
        "all_tasks_b5_identical": all(v == 1.0 for v in overlap_b5.values()),
        "ledger_requests": client.ledger.requests,
        "ledger_prompt_tokens": client.ledger.prompt_tokens,
        "ledger_cost_usd": client.ledger.cost_usd,
        "note": "technical stability diagnostic on already-exposed DEVELOPMENT tasks; not model selection",
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "stability.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


def _full(client: OpenRouterEmbeddingsClient, units: dict[str, str]) -> int:
    t_start = time.perf_counter()
    cache = EmbeddingCache(EMB_CACHE_DIR)

    # ---- embed corpus (resume-safe) ----
    unit_texts = [units[k] for k in units]
    t0 = time.perf_counter()
    to_embed = cache.missing(unit_texts)
    print(f"[corpus] missing {len(to_embed)} / {len(unit_texts)}")
    for i in range(0, len(to_embed), BATCH):
        chunk = to_embed[i:i + BATCH]
        vecs = client.embed(chunk)
        cache.add(chunk, vecs)
        if (i // BATCH) % 25 == 0:
            print(f"  ... {i + len(chunk)}/{len(to_embed)} embeddings; "
                  f"cost ${client.ledger.cost_usd:.4f}")
    t_corpus = time.perf_counter() - t0
    print(f"[corpus] done {len(units)} units in {t_corpus:.1f}s, "
          f"cost ${client.ledger.cost_usd:.4f}")

    # ---- embed queries ----
    tasks = load_dev_tasks()
    query_texts = [t.intent_text for t in tasks]
    t0 = time.perf_counter()
    to_embed_q = cache.missing(query_texts)
    for i in range(0, len(to_embed_q), BATCH):
        chunk = to_embed_q[i:i + BATCH]
        cache.add(chunk, client.embed(chunk))
    t_queries = time.perf_counter() - t0

    # ---- per-task file scores (MAX cosine) + rankings ----
    task_files = build_task_files(tasks)
    by_cid = {t.case_id: t for t in tasks}
    blob_texts = json.loads(BLOB_CACHE.read_text(encoding="utf-8"))
    plan = {}
    for sha, text in blob_texts.items():
        if text is None:
            plan[sha] = []
            continue
        plan[sha] = [sha256_text(u) for u in extract_code_units(text) if _valid_unit(u)]

    query_emb = {sha256_text(t): _l2(cache.get([t])[0]) for t in query_texts}
    unit_mat = cache.matrix  # rows aligned to cache.index by sha
    results: dict[str, dict] = {}
    t0 = time.perf_counter()
    n_scored = 0
    for cid, tf in task_files.items():
        t = by_cid[cid]
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
            units_mat = unit_mat[rows]
            unit_cos = units_mat @ q
            scores[path] = aggregate_file_score(
                [(k, float(c)) for k, c in zip(keys, unit_cos, strict=True)])
        universe = tf["paths"]
        write_set = frozenset(t.write_set)
        ranked = rank_files(scores, universe, write_set)
        results[cid] = {
            "repository": tf["repository"],
            "case_id": cid,
            "write_set": sorted(t.write_set),
            "proxy": sorted(t.proxy),
            "fn_paths": list(t.fn_paths),
            "n_missed": t.n_missed,
            "omitted_size": len([p for p in universe if p not in write_set]),
            "qwen_ranked": ranked,
            "routeb_ranked": rank_composite(t),
            "bm25_ranked": rank_bm25(t),
            "query_sha256": sha256_text(tf["intent_text"]),
            "parent_commit": t.parent_commit,
        }
        n_scored += len(scores)
    t_rank = time.perf_counter() - t0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.joinpath("task_rankings.json").write_text(
        json.dumps(results, indent=1), encoding="utf-8")

    metrics, gate = evaluate(results, by_cid)
    OUT_DIR.joinpath("metrics.json").write_text(json.dumps(metrics, indent=1), encoding="utf-8")
    OUT_DIR.joinpath("gate.json").write_text(json.dumps(gate, indent=1), encoding="utf-8")
    OUT_DIR.joinpath("ledger.json").write_text(json.dumps({
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
    }, indent=2), encoding="utf-8")
    print(json.dumps({r: metrics["repos"][r]["B"]["5"]["qwen_embed"]["macro_orr"]
                      for r in ("djangocms", "saleor")}, indent=1))
    print("decision:", gate["decision"])
    print("ledger:", json.dumps({
        "requests": client.ledger.requests, "tokens": client.ledger.prompt_tokens,
        "cost": client.ledger.cost_usd, "failures": client.ledger.permanent_failures}, indent=1))
    return 0


def _contrib(r: dict, t, key: str, B: int) -> dict:
    pos = set(t.proxy)
    fn_set = set(t.fn_paths)
    B_eff = min(B, r["omitted_size"])
    added = set(r[key][:B_eff])
    final = set(t.write_set) | added
    tp = len(final & pos)
    fp = len(final - pos)
    fn = len(pos - final)
    return {"tp": tp, "fp": fp, "fn": fn,
            "orr": (len(added & fn_set) / t.n_missed) if t.n_missed else 0.0,
            "cand_fn": len(added & fn_set), "cand_sel": len(added)}


def evaluate(results: dict, by_cid: dict) -> tuple[dict, dict]:

    methods = {"routeb": "routeb_ranked", "bm25": "bm25_ranked", "qwen_embed": "qwen_ranked"}
    metrics: dict = {"repos": {}, "BUDGETS": list(BUDGETS)}
    for repo in ("djangocms", "saleor"):
        cids = [c for c in results if results[c]["repository"] == repo]
        per_b: dict = {}
        for B in BUDGETS:
            per_b[str(B)] = {}
            for name, key in methods.items():
                rows = [_contrib(results[c], by_cid[c], key, B) for c in cids]
                tp = sum(r["tp"] for r in rows)
                fp = sum(r["fp"] for r in rows)
                fn = sum(r["fn"] for r in rows)
                p = tp / (tp + fp) if (tp + fp) else 0.0
                rec = tp / (tp + fn) if (tp + fn) else 0.0
                f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
                fnr = fn / (tp + fn) if (tp + fn) else 0.0
                orr = sum(r["orr"] for r in rows) / len(rows) if rows else 0.0
                cand = sum(r["cand_fn"] for r in rows) / sum(r["cand_sel"] for r in rows) if sum(r["cand_sel"] for r in rows) else 0.0
                per_b[str(B)][name] = {
                    "tp": tp, "fp": fp, "fn": fn, "precision": round(p, 4),
                    "recall": round(rec, 4), "f1": round(f1, 4), "fnr": round(fnr, 4),
                    "macro_orr": round(orr, 4), "candidate_precision": round(cand, 4),
                    "n_tasks": len(cids),
                }
        metrics["repos"][repo] = {"n_tasks_dev": len(cids), "B": per_b}

    # ---- paired bootstrap CIs @B=5 (Qwen - RouteB) ----
    ci_out: dict[str, dict] = {}
    for repo in ("djangocms", "saleor"):
        cids = [c for c in results if results[c]["repository"] == repo]
        rows = {m: [] for m in METRIC_NAMES}
        rb_rows = {m: [] for m in METRIC_NAMES}
        for cid in cids:
            q = _contrib(results[cid], by_cid[cid], "qwen_ranked", B_REF)
            rb = _contrib(results[cid], by_cid[cid], "routeb_ranked", B_REF)
            rows["macro_orr"].append((q["orr"],))
            rb_rows["macro_orr"].append((rb["orr"],))
            for name in ("final_precision", "final_recall", "final_f1", "final_fnr"):
                rows[name].append((q["tp"], q["fp"], q["fn"]))
                rb_rows[name].append((rb["tp"], rb["fp"], rb["fn"]))
            rows["candidate_precision"].append((q["cand_fn"], q["cand_sel"]))
            rb_rows["candidate_precision"].append((rb["cand_fn"], rb["cand_sel"]))
        ci_out[repo] = {m: paired_bootstrap(rb_rows[m], rows[m], m, N_RESAMPLES, SEED)
                        for m in METRIC_NAMES}

    # ---- frozen numeric gate (B=5, both repos) ----
    gate: dict = {"reference_budget": B_REF, "baseline": "routeb", "repos": {}, "decision": "QWEN3_EMBED_FAIL"}
    all_pass = True
    for repo in ("djangocms", "saleor"):
        b5 = metrics["repos"][repo]["B"]["5"]
        q = b5["qwen_embed"]
        rb = b5["routeb"]
        ci = ci_out[repo]
        d_f1 = q["f1"] - rb["f1"]
        ci_low_f1 = ci["final_f1"]["ci95_lower"]
        a = d_f1 > 0.0 and ci_low_f1 > 0.0
        b_cond = (q["recall"] - rb["recall"]) >= -0.02
        c_cond = (q["fnr"] - rb["fnr"]) <= 0.02
        d_cond = (q["precision"] - rb["precision"]) >= -0.02
        folds = _folds(cids, by_cid, results)
        e = sum(1 for x in folds if x >= 0.0) >= 3
        rec = all([a, b_cond, c_cond, d_cond, e])
        all_pass = all_pass and rec
        gate["repos"][repo] = {
            "A_delta_f1_gt0_and_ci_low_gt0": a, "delta_f1": round(d_f1, 4), "ci_low_f1": round(ci_low_f1, 4),
            "B_delta_recall_ge_minus_0.02": b_cond, "delta_recall": round(q["recall"] - rb["recall"], 4),
            "C_delta_fnr_le_plus_0.02": c_cond, "delta_fnr": round(q["fnr"] - rb["fnr"], 4),
            "D_delta_precision_ge_minus_0.02": d_cond, "delta_precision": round(q["precision"] - rb["precision"], 4),
            "E_folds_ge_3_5": e, "fold_deltas_f1": [round(x, 4) for x in folds],
            "ci": ci, "pass": rec,
        }
    gate["pass"] = all_pass
    gate["decision"] = "QWEN3_EMBED_PASS" if all_pass else "QWEN3_EMBED_FAIL"
    return metrics, gate


def _folds(cids: list, by_cid: dict, results: dict, folds: int = 5, seed: int = SEED) -> list[float]:
    import random
    rng = random.Random(seed)
    order = list(cids)
    rng.shuffle(order)
    out: list[float] = []
    for k in range(folds):
        fold = order[k::folds]
        pos = 0.0
        for cid in fold:
            r = results[cid]
            t = by_cid[cid]
            M = t.n_missed
            if M == 0:
                continue
            B_eff = min(B_REF, r["omitted_size"])
            fn_set = set(t.fn_paths)
            q = len(set(r["qwen_ranked"][:B_eff]) & fn_set) / M
            rb = len(set(r["routeb_ranked"][:B_eff]) & fn_set) / M
            pos += (q - rb)
        out.append(pos / len(fold) if fold else 0.0)
    return out


if __name__ == "__main__":
    raise SystemExit(main())
