#!/usr/bin/env python3
# ruff: noqa: E501
"""M17_COMP_BASELINES_R2 — Phase 2 execution (zero paid API, same frozen protocol).

Runs the pre-specified cheap baselines on the EXACT frozen MAIN_297 population
under the evaluator used for RM-CSS / SIP / Agent (benchmark.wp1a.scorer
semantics) and records per-task predictions + metrics.

Arms (pre-specified, see BASELINE_PROTOCOL_FREEZE_R2.json):
  BM25@1/3/5/10, BM25_SIZE_MATCHED           -> DIRECT_SAME_PROTOCOL / SIZE_MATCHED_CONTROL
  DENSE@1/3/5/10, DENSE_SIZE_MATCHED         -> DIRECT_SAME_PROTOCOL (+DENSE_ONLY_ABLATION) / SIZE_MATCHED_CONTROL
  BM25_TO_CIA_1HOP/2HOP                      -> DIRECT_SAME_PROTOCOL
  C_ORACLE_1HOP/2HOP                         -> UPPER_BOUND_ONLY + GOLD_SEEDED
No paid API call. No parameter selection after seeing outcomes.

FREEZE: research/competitor-baselines-r2/BASELINE_PROTOCOL_FREEZE_R2.json
SHA256 = 881237ddef31efd66d1f437e861b6d8de9af296dc5ede0eef742b8df9ec1cef9
"""
from __future__ import annotations

import hashlib
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

# Load the frozen deterministic tokenizer directly (same file/implementation as
# benchmark.cheap_baselines.tokenize) without importing the package __init__
# chain (avoids heavy dependency surface; tokenizer module is standalone).
import importlib.util  # noqa: E402

_tok_spec = importlib.util.spec_from_file_location(
    "frozen_tokenize", PROJECT / "src" / "benchmark" / "cheap_baselines" / "tokenize.py"
)
_tok_module = importlib.util.module_from_spec(_tok_spec)
assert _tok_spec and _tok_spec.loader
_tok_spec.loader.exec_module(_tok_module)
tokenize = _tok_module.tokenize  # type: ignore[attr-defined]

# ---------------------------------------------------------------------------
# Frozen source locations
# ---------------------------------------------------------------------------
SCIENTIFIC = PROJECT / "benchmark_data" / "real_commit_impact_saleor" / "scientific"
MANIFEST = PROJECT / "research" / "wp1b" / "wp1b_main_297_manifest.json"
PROXIES = PROJECT / "research" / "saleor-reserve-300-rmcss" / "saleor_reserve_300_proxies.json"
SIPR = PROJECT / "research" / "wp1a" / "sip_rmcss_per_task_predictions.json"
AGENT = PROJECT / "research" / "wp1b" / "main-297-2026-09-22" / "wp1b_agent_predictions.json"
DENSE_PARQUET = PROJECT / "research" / "saleor-reserve-300-rmcss" / "full_file_scores_saleor300.parquet"
SALEOR_CACHE = Path(r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\dist\pilot-repo-cache\saleor")

OUT_DIR = PROJECT / "research" / "competitor-baselines-r2"

# ---------------------------------------------------------------------------
# Pre-specified parameters (from the freeze; no tuning)
# ---------------------------------------------------------------------------
K_VALUES = (1, 3, 5, 10)
BM25_K1 = 1.2
BM25_B = 0.75
BM25_EPS = 1e-9


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Deterministic BM25 (k1=1.2, b=0.75) over the frozen tokenizer
# ---------------------------------------------------------------------------
def _bm25_idf(df: int, n_docs: int) -> float:
    return __import__("math").log((n_docs - df + 0.5) / (df + 0.5) + 1.0)


def bm25_rank(docs: dict[str, str], query: str) -> list[str]:
    """Return universe paths ranked by BM25 score desc, path asc (frozen tie-break)."""
    from collections import Counter

    doc_ids = tuple(sorted(docs))
    if not doc_ids:
        return []
    term_lists: dict[str, tuple[str, ...]] = {}
    lengths: dict[str, int] = {}
    df: Counter[str] = Counter()
    total_len = 0
    for doc_id in doc_ids:
        terms = tokenize(docs[doc_id])
        term_lists[doc_id] = terms
        lengths[doc_id] = len(terms)
        total_len += len(terms)
        df.update(set(terms))
    avgdl = total_len / max(1, len(doc_ids))
    query_terms = tokenize(query)
    scored: list[tuple[float, str]] = []
    for doc_id in doc_ids:
        terms = term_lists[doc_id]
        doc_len = lengths[doc_id]
        freq = Counter(t for t in terms)
        score = 0.0
        for term in set(query_terms):
            tf = freq.get(term, 0)
            if tf == 0:
                continue
            idf = _bm25_idf(df.get(term, 0), len(doc_ids))
            denom = tf + BM25_K1 * (1 - BM25_B + BM25_B * (doc_len / max(1.0, avgdl)))
            score += idf * (tf * (BM25_K1 + 1)) / (denom + BM25_EPS)
        scored.append((score, doc_id))
    scored.sort(key=lambda pair: (-pair[0], pair[1]))
    return [doc_id for _, doc_id in scored]


# ---------------------------------------------------------------------------
# Parent-commit file content (same upstream cache the frozen MAIN_297 run used)
# ---------------------------------------------------------------------------
def parent_file_bytes(cache: Path, parent: str, want: set[str]) -> dict[str, bytes]:
    """Read wanted universe files at the parent commit (2 subprocesses, byte-verified).

    Uses git ls-tree -r -z + one git cat-file --batch stream. This is required
    because `git archive` fails for some Saleor parents (documented non-production
    test-cassette names with `?`/`[`/`]` break archive extraction; see
    scripts/saleor_portability_fix.py). Content is verified against the frozen
    candidate-universe blob sha256 (LF-normalized) at build time.
    """
    out: dict[str, bytes] = {}
    if not want:
        return out
    lst = subprocess.run(
        ["git", "-C", str(cache), "ls-tree", "-r", "-z", parent],
        capture_output=True, check=True,
    ).stdout
    entries: dict[str, str] = {}
    for rec in lst.split(b"\x00"):
        if not rec:
            continue
        meta, path = rec.split(b"\t", 1)
        parts = meta.split(b" ")
        typ, sha = parts[1].decode(), parts[2].decode()
        if typ == "blob":
            entries[path.decode("utf-8", "replace")] = sha
    payload = "".join((entries[p] + "\n") for p in want if p in entries)
    if not payload:
        return {}
    proc = subprocess.run(
        ["git", "-C", str(cache), "cat-file", "--batch"],
        input=payload.encode(), capture_output=True, check=True,
    )
    data = proc.stdout
    result: dict[str, bytes] = {}
    pos, n = 0, len(data)
    while pos < n:
        nl = data.index(b"\n", pos)
        sha, typ, size = data[pos:nl].split(b" ")
        size = int(size)
        pos = nl + 1
        result[sha.decode()] = data[pos:pos + size]
        pos += size + 1  # LF separator after each object
    for p in want:
        s = entries.get(p)
        out[p] = result.get(s, b"") if s else b""
    return out


# ---------------------------------------------------------------------------
# Frozen evaluator semantics (benchmark.wp1a.scorer)
# ---------------------------------------------------------------------------
def per_task_confusion(pred: set[str], label: set[str]) -> tuple[int, int, int]:
    tp = len(pred & label)
    fp = len(pred - label)
    fn = len(label - pred)
    return tp, fp, fn


def arm_aggregates(confusions: list[tuple[int, int, int]], sizes: list[int]) -> dict:
    tp = sum(c[0] for c in confusions)
    fp = sum(c[1] for c in confusions)
    fn = sum(c[2] for c in confusions)
    micro_p = tp / (tp + fp) if (tp + fp) else 0.0
    micro_r = tp / (tp + fn) if (tp + fn) else 0.0
    micro_f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
    micro_fnr = fn / (tp + fn) if (tp + fn) else 0.0
    # macro: mean of per-task metrics with the frozen per-task convention (0 when denom is 0)
    macro_p = []
    macro_r = []
    macro_f1 = []
    for (t, f, n) in confusions:
        macro_p.append(t / (t + f) if (t + f) else 0.0)
        macro_r.append(t / (t + n) if (t + n) else 0.0)
        d = 2 * t + f + n
        macro_f1.append(2 * t / d if d else 0.0)
    n = len(confusions)
    return {
        "micro": {
            "tp": tp, "fp": fp, "fn": fn,
            "precision": micro_p, "recall": micro_r, "f1": micro_f1, "fnr": micro_fnr,
        },
        "macro": {
            "precision": statistics.fmean(macro_p) if n else 0.0,
            "recall": statistics.fmean(macro_r) if n else 0.0,
            "f1": statistics.fmean(macro_f1) if n else 0.0,
        },
        "size": {
            "mean": statistics.fmean(sizes) if n else 0.0,
            "median": statistics.median(sizes) if n else 0.0,
            "min": min(sizes) if n else 0,
            "max": max(sizes) if n else 0,
        },
        "empty_set_count": sum(1 for s in sizes if s == 0),
        "n_tasks": n,
    }


# ---------------------------------------------------------------------------
# Static CIA (identical to scripts/classical_cia_baseline_v1.py)
# ---------------------------------------------------------------------------
def _adjacency(edges: list[list[str]]) -> dict[str, set[str]]:
    adj: dict[str, set[str]] = {}
    for s, d in edges:
        adj.setdefault(s, set()).add(d)
        adj.setdefault(d, set()).add(s)
    return adj


def _cia_1hop(seed_paths: set[str], edges: list[list[str]]) -> set[str]:
    adj = _adjacency(edges)
    out = set(seed_paths)
    for s in seed_paths:
        out.update(adj.get(s, set()))
    return out


def _cia_2hop(seed_paths: set[str], edges: list[list[str]], max_hops: int = 2) -> set[str]:
    adj = _adjacency(edges)
    dist: dict[str, int] = {}
    frontier = list(seed_paths)
    for n in frontier:
        dist[n] = 0
    hops = 0
    while frontier and hops < max_hops:
        hops += 1
        nxt: list[str] = []
        for node in frontier:
            for nb in adj.get(node, set()):
                if nb not in dist:
                    dist[nb] = hops
                    nxt.append(nb)
        frontier = nxt
    return set(dist)


def main() -> int:
    print("loading frozen artifacts ...", flush=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    task_ids: list[str] = list(manifest["task_ids"])
    proxies = json.loads(PROXIES.read_text(encoding="utf-8"))["proxies"]
    sipr = json.loads(SIPR.read_text(encoding="utf-8"))["per_task"]
    agent = json.loads(AGENT.read_text(encoding="utf-8"))["per_task"]

    assert len(task_ids) == 297
    assert set(task_ids) <= set(proxies)
    assert set(task_ids) <= set(sipr)
    assert set(task_ids) <= set(agent)

    import pandas as pd

    dense_df = pd.read_parquet(DENSE_PARQUET)

    # RM-CSS sizes for size-matched arms (RM-CSS OUTPUT SIZE only)
    rmcss_sizes = {t: len(set(sipr[t]["rmcss_predicted_set"])) for t in task_ids}

    arms: list[str] = (
        ["BM25@1", "BM25@3", "BM25@5", "BM25@10", "BM25_SIZE_MATCHED"]
        + ["DENSE@1", "DENSE@3", "DENSE@5", "DENSE@10", "DENSE_SIZE_MATCHED"]
        + ["BM25_TO_CIA_1HOP", "BM25_TO_CIA_2HOP"]
        + ["C_ORACLE_1HOP", "C_ORACLE_2HOP"]
    )
    # frozen arms (read-only reuse)
    frozen_arms = {"SIP": "sip", "RM-CSS": "rmcss", "AGENT": "agent"}

    per_task: dict[str, dict] = {}
    arm_data: dict[str, dict] = {a: {} for a in arms}

    bm25_ranks: dict[str, list[str]] = {}
    dense_ranks: dict[str, list[str]] = {}

    t_start = time.time()
    for i, tid in enumerate(task_ids):
        case_dir = SCIENTIFIC / tid
        intent = json.loads((case_dir / "public" / "intent.json").read_text(encoding="utf-8"))
        universe = json.loads((case_dir / "public" / "candidate_universe.json").read_text(encoding="utf-8"))
        graph = json.loads((case_dir / "public" / "dependency_graph.json").read_text(encoding="utf-8"))
        paths: list[str] = sorted(str(r["path"]) for r in universe["records"])
        path_set = set(paths)
        edges: list[list[str]] = [[str(s), str(d)] for s, d in graph.get("edges", [])]
        label: set[str] = set(proxies[tid])

        # ---- BM25 (document = path + LF-normalized parent file content) ----
        t0 = time.time()
        manifest_case = json.loads((case_dir / "case_manifest.json").read_text(encoding="utf-8"))
        parent = str(manifest_case["record"]["parent_commit"])
        raw = parent_file_bytes(SALEOR_CACHE, parent, path_set)
        docs: dict[str, str] = {}
        missing = 0
        for p in paths:
            b = raw.get(p)
            if b is None:
                missing += 1
                b = b""
            docs[p] = p + "\n" + b.replace(b"\r\n", b"\n").decode("utf-8", errors="replace")
        t_index = time.time() - t0
        t1 = time.time()
        bm25_order = bm25_rank(docs, str(intent["intent_text"]))
        t_query = time.time() - t1
        bm25_ranks[tid] = bm25_order
        arm_data["BM25@1"].setdefault("wall", 0.0)
        arm_data["BM25@1"]["wall"] += (t_index + t_query)
        arm_data["BM25@1"]["index_wall"] = arm_data["BM25@1"].get("index_wall", 0.0) + t_index
        arm_data["BM25@1"]["query_wall"] = arm_data["BM25@1"].get("query_wall", 0.0) + t_query
        arm_data["BM25@1"]["missing_at_parent"] = arm_data["BM25@1"].get("missing_at_parent", 0) + missing

        # ---- DENSE (frozen qwen dense scores, realization A) ----
        sub = dense_df[dense_df["case_id"] == tid]
        dense_rows = {}
        for _, r in sub.iterrows():
            p = str(r["file_path"])
            v = r["dense_file_score"]
            dense_rows[p] = float(v) if (v == v) else None  # NaN -> None
        # rank: finite desc, NaN last, tie path asc
        finite = sorted([p for p in paths if p in dense_rows and dense_rows[p] is not None],
                        key=lambda p: (-dense_rows[p], p))
        nonfinite = sorted([p for p in paths if p not in dense_rows or dense_rows[p] is None])
        dense_order = finite + nonfinite
        dense_ranks[tid] = dense_order

        # ---- CIA seeds ----
        bm25_top1 = bm25_order[0] if bm25_order else None
        gold_in_universe = sorted(label & path_set)
        oracle_seed = gold_in_universe[0] if gold_in_universe else None

        preds: dict[str, set[str]] = {}
        # BM25 variants
        preds["BM25@1"] = set(bm25_order[:1])
        preds["BM25@3"] = set(bm25_order[:3])
        preds["BM25@5"] = set(bm25_order[:5])
        preds["BM25@10"] = set(bm25_order[:10])
        preds["BM25_SIZE_MATCHED"] = set(bm25_order[: rmcss_sizes[tid]])
        # DENSE variants
        preds["DENSE@1"] = set(dense_order[:1])
        preds["DENSE@3"] = set(dense_order[:3])
        preds["DENSE@5"] = set(dense_order[:5])
        preds["DENSE@10"] = set(dense_order[:10])
        preds["DENSE_SIZE_MATCHED"] = set(dense_order[: rmcss_sizes[tid]])
        # CIA realistic (seed = BM25 top-1)
        if bm25_top1 is not None:
            preds["BM25_TO_CIA_1HOP"] = _cia_1hop({bm25_top1}, edges)
            preds["BM25_TO_CIA_2HOP"] = _cia_2hop({bm25_top1}, edges)
        else:
            preds["BM25_TO_CIA_1HOP"] = set()
            preds["BM25_TO_CIA_2HOP"] = set()
        # CIA oracle (seed = lexicographically first gold changed non-test file in universe)
        if oracle_seed is not None:
            preds["C_ORACLE_1HOP"] = _cia_1hop({oracle_seed}, edges)
            preds["C_ORACLE_2HOP"] = _cia_2hop({oracle_seed}, edges)
        else:
            preds["C_ORACLE_1HOP"] = set()
            preds["C_ORACLE_2HOP"] = set()

        # predict outside universe / duplicates accounting
        for a in arms:
            p = preds[a]
            universe_ok = p <= path_set
            arm_data[a].setdefault("invalid_prediction_count", 0)
            arm_data[a].setdefault("duplicate_prediction_count", 0)
            if not universe_ok:
                arm_data[a]["invalid_prediction_count"] += 1
            # sets are used everywhere above; duplicates already collapsed (0 by construction)

        row: dict = {"task_id": tid, "gold": sorted(label), "gold_in_universe_count": len(gold_in_universe),
                     "universe_size": len(path_set), "rmcss_size": rmcss_sizes[tid],
                     "bm25_missing_at_parent": missing}
        for a in arms:
            sl = sorted(preds[a])
            tp, fp, fn = per_task_confusion(preds[a], label)
            row[f"{a}_selected"] = sl
            row[f"{a}_confusion"] = {"tp": tp, "fp": fp, "fn": fn}
        # frozen arms
        row["SIP_selected"] = sorted(set(sipr[tid]["sip_predicted_set"]))
        row["RM-CSS_selected"] = sorted(set(sipr[tid]["rmcss_predicted_set"]))
        row["AGENT_selected"] = sorted(set(agent[tid]["selected_paths"]))
        for a, _key in frozen_arms.items():
            sl = row[f"{a}_selected"]
            a_ = set(sl)
            tp, fp, fn = per_task_confusion(a_, label)
            row[f"{a}_confusion"] = {"tp": tp, "fp": fp, "fn": fn}
        per_task[tid] = row

        if (i + 1) % 25 == 0 or (i + 1) == len(task_ids):
            print(f"  [{i+1}/{len(task_ids)}] {tid}  elapsed {time.time()-t_start:.1f}s", flush=True)

    # ------------------------------------------------------------------
    # Aggregates
    # ------------------------------------------------------------------
    all_arms = arms + ["SIP", "RM-CSS", "AGENT"]
    aggregates: dict[str, dict] = {}
    confusions_by_arm: dict[str, list[tuple[int, int, int]]] = {}
    sizes_by_arm: dict[str, list[int]] = {}
    for a in all_arms:
        confs = [tuple(per_task[t][f"{a}_confusion"].values()) for t in task_ids]  # type: ignore[assignment]
        sizes = [len(per_task[t][f"{a}_selected"]) for t in task_ids]
        confusions_by_arm[a] = [tuple(int(v) for v in c) for c in confs]  # type: ignore[assignment]
        sizes_by_arm[a] = sizes
        agg = arm_aggregates(confusions_by_arm[a], sizes)  # type: ignore[arg-type]
        aggregates[a] = agg

    # efficiency
    efficiency: dict[str, dict] = {}
    for a in arms:
        d = arm_data[a]
        efficiency[a] = {
            "llm_calls_new": 0, "prompt_tokens_new": 0, "completion_tokens_new": 0,
            "api_cost_usd_new": 0.0,
            "wall_seconds": d.get("wall", 0.0),
            "bm25_index_wall_seconds": d.get("index_wall", 0.0),
            "bm25_query_wall_seconds": d.get("query_wall", 0.0),
            "missing_at_parent_file_count": d.get("missing_at_parent", 0),
        }
    for a in frozen_arms:
        efficiency[a] = {"reused": True, "note": "read-only reuse of frozen MAIN_297 evidence; no rerun, no new API call"}

    out = {
        "protocol_freeze_sha256": "881237ddef31efd66d1f437e861b6d8de9af296dc5ede0eef742b8df9ec1cef9",
        "population": {"n_tasks": len(task_ids), "manifest_sha256": manifest["manifest_sha256"]},
        "arms": all_arms,
        "per_task": per_task,
        "aggregates": aggregates,
        "efficiency": efficiency,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "per_task_predictions_r2.json").write_text(
        json.dumps({k: v for k, v in out.items() if k != "aggregates"}, indent=1, sort_keys=True), encoding="utf-8")
    (OUT_DIR / "per_task_metrics_r2.json").write_text(json.dumps(out, indent=1, sort_keys=True), encoding="utf-8")

    print("\n=== AGGREGATES (micro) ===")
    for a in all_arms:
        m = aggregates[a]["micro"]
        print(f"{a:22s} P={m['precision']:.4f} R={m['recall']:.4f} F1={m['f1']:.4f} FNR={m['fnr']:.4f} "
              f"size={aggregates[a]['size']['mean']:.2f} (tp={m['tp']} fp={m['fp']} fn={m['fn']})")
    print("\ntotal wall:", round(time.time() - t_start, 1), "s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
