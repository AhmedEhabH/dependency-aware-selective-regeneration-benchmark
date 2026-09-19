#!/usr/bin/env python3
# ruff: noqa: N803, N806
"""SWERANKEMBED-SMALL DEVELOPMENT EVALUATION (T3, ZERO API, DEVELOPMENT only).

Runs the frozen SweRankEmbed-Small baseline
(docs/SWERANK_EMBED_BASELINE_PROTOCOL_FROZEN.md) on the FULL currently
permissible DEVELOPMENT populations:

  - djangoCMS DEV  (174 tasks)
  - Saleor DEV     (149 tasks)

Pipeline (deterministic, parent-visible ONLY):
  1. Build the per-task candidate-universe blob registry from the frozen case
     bundles (path + blob sha256 at the PARENT revision).
  2. Materialize blob text with `git show <parent>:<path>` from the local
     read-only caches:
         djangoCMS -> dist/real-commit-cache/djangocms
         Saleor    -> dist/pilot-repo-cache/saleor   (full 22,615-commit
                      history available locally; resolves the documented
                      "Saleor parent-visible history cache absent" blocker
                      at the real-commit-cache path)
  3. Extract code units per blob (official SweRank-style AST spans; whole-file
     fallback). Unit text is hashed; identical unit text is embedded once.
  4. Encode units with the PINNED model revision (L2-normalized) + encode the
     parent-visible issue intent (query prompt applied by the model).
  5. Frozen adapter: score(file) = MAX cosine over units; rank the omitted
     candidates desc by score, asc path (Route-B matched pool + tie-break).
  6. Metrics at B in {1,3,5,10}: macro ORR, pooled final P/R/F1/FNR, candidate
     precision, plus paired task-bootstrap 95% CIs (>=10,000 resamples, fixed
     seed) for SweRank minus frozen Route-B at B=5.
  7. Frozen progression gate (docs/SWERANK_EMBED_BASELINE_PROTOCOL_FROZEN.md).

NO paid LLM/API call is made. API calls = 0, API cost = $0. Only local CPU
inference on the pinned CC-BY-NC-4.0 model is used (labeled EXTERNAL
PRETRAINED DIAGNOSTIC BASELINE; see reports/SWERANK_TRAINING_PROVENANCE_AUDIT.md).

Outputs under research/strong-localization-signal/swerank/ + reports/.
"""
from __future__ import annotations

import json
import os
import subprocess
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
from benchmark.recall.quant_rankers import rank_bm25_rev_support  # noqa: E402
from benchmark.recall.rankers import rank_bm25, rank_composite  # noqa: E402
from benchmark.signal.code_units import extract_code_units, sha256_text  # noqa: E402
from benchmark.signal.metrics import METRIC_NAMES, paired_bootstrap  # noqa: E402
from benchmark.signal.swerank_model import (  # noqa: E402
    MODEL_ID,
    MODEL_REVISION,
    SweRankEmbed,
)
from benchmark.signal.swrank_adapter import (  # noqa: E402
    aggregate_file_score,
    rank_files,
)
from scripts.route_b_v2_robustness import load_case  # noqa: E402

OUT_DIR = _PROJECT_DIR / "research" / "strong-localization-signal" / "swerank"
REPORT_DIR = _PROJECT_DIR / "reports"
BUDGETS = (1, 3, 5, 10)
B_REF = 5
N_RESAMPLES = 10_000
SEED = 20260919

DJANGOCMS_GIT = _PROJECT_DIR / "dist" / "real-commit-cache" / "djangocms"
SALEOR_GIT = _PROJECT_DIR / "dist" / "pilot-repo-cache" / "saleor"

# Large regenerable caches live OUTSIDE the repo (temp); small artifacts stay in the repo.
TMP_CACHE = Path(r"C:\Users\Ahmed\AppData\Local\Temp\opencode\swerank-cache")
HF_HOME = Path(r"C:\Users\Ahmed\AppData\Local\Temp\opencode\hf")


def _git_show(git_dir: Path, parent: str, path: str) -> str | None:
    proc = subprocess.run(
        ["git", "-C", str(git_dir), "show", f"{parent}:{path}"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        return None
    return proc.stdout


def _dataset_for(repo: str, role: str) -> Path:
    if repo == "saleor":
        return SALEOR_DATASET
    return V1_DATASET if role.startswith("V1") else V2_DATASET


def build_blob_registry(tasks) -> dict:
    """sha256(blob) -> (repo, parent_commit, path)."""
    blobs: dict[str, tuple[str, str, str]] = {}
    for t in tasks:
        case = load_case(t.case_id, _dataset_for(t.repository, t.role))
        for r in case["records"]:
            blobs.setdefault(r["sha256"], (t.repository, t.parent_commit, r["path"]))
    return blobs


def materialize(blobs: dict) -> dict[str, str | None]:
    """blob sha -> text (None when the parent path is unavailable at the cache)."""
    cache_file = TMP_CACHE / "blob_text.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))
    out: dict[str, str | None] = {}
    git_dir_by_repo = {"djangocms": DJANGOCMS_GIT, "saleor": SALEOR_GIT}
    t0 = time.perf_counter()
    for sha, (repo, parent, path) in blobs.items():
        out[sha] = _git_show(git_dir_by_repo[repo], parent, path)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(out), encoding="utf-8")
    print(f"[materialize] {len(blobs)} blobs in {time.perf_counter() - t0:.1f}s")
    return out


def unit_plan(blobs: dict, texts: dict) -> tuple[dict, dict, int]:
    """blob sha -> list of unit hashes; unit hash -> unit text; count of empty."""
    plan: dict[str, list[str]] = {}
    units: dict[str, str] = {}
    n_missing = 0
    for sha in blobs:
        text = texts.get(sha)
        if text is None:
            plan[sha] = []
            n_missing += 1
            continue
        us = extract_code_units(text)
        keys = [sha256_text(u) for u in us]
        plan[sha] = keys
        for k, u in zip(keys, us, strict=True):
            units.setdefault(k, u)
    return plan, units, n_missing


def build_task_files(tasks) -> dict:
    """case_id -> {repo, parent, paths, write_set, proxy, fn_paths, role, intent_text}."""
    out: dict[str, dict] = {}
    for t in tasks:
        case = load_case(t.case_id, _dataset_for(t.repository, t.role))
        out[t.case_id] = {
            "repository": t.repository,
            "parent_commit": t.parent_commit,
            "role": t.role,
            "intent_text": t.intent_text,
            "paths": [str(p) for p in case["paths"]],
            "blob_sha": {str(r["path"]): r["sha256"] for r in case["records"]},
            "write_set": sorted(t.write_set),
            "proxy": sorted(t.proxy),
            "fn_paths": list(t.fn_paths),
            "n_missed": t.n_missed,
        }
    return out


def rank_task(model: SweRankEmbed, task: dict, plan: dict,
              emb_lookup: dict) -> dict[str, float]:
    """File scores for a task: MAX cosine over the task's universe files.

    emb_lookup: precomputed unit_sha -> embedding (encoded once for ALL units).
    """
    query_emb = model.encode_query(task["intent_text"])
    scores: dict[str, float] = {}
    for path in task["paths"]:
        sha = task["blob_sha"].get(path)
        if sha is None:
            continue
        unit_keys = plan.get(sha, [])
        if not unit_keys:
            continue
        unit_scores = {k: float(np.dot(emb_lookup[k], query_emb)) for k in unit_keys}
        scores[path] = aggregate_file_score([(k, s) for k, s in unit_scores.items()])
    return scores


def main() -> int:
    t_start = time.perf_counter()
    tasks = load_dev_tasks()
    limit = os.environ.get("SWERANK_LIMIT_TASKS")
    if limit:
        tasks = tasks[: int(limit)]
    print(f"[load] {len(tasks)} dev tasks")

    blobs = build_blob_registry(tasks)
    texts = materialize(blobs)
    plan, units, n_missing = unit_plan(blobs, texts)
    t_materialize = time.perf_counter() - t_start
    print(f"[units] {len(units)} distinct unit texts; {n_missing} missing blobs")

    t_load = time.perf_counter()
    model = SweRankEmbed(TMP_CACHE / "emb", hf_home=HF_HOME)
    t_load = time.perf_counter() - t_load

    task_files = build_task_files(tasks)
    # Batch-encode ALL distinct unit texts ONCE (cache-backed), then score per task.
    all_unit_texts = list(units.values())
    t0 = time.perf_counter()
    emb_lookup = model.encode_units(all_unit_texts)
    t_encode = time.perf_counter() - t0
    print(f"[encode] {len(all_unit_texts)} distinct units in {t_encode:.1f}s; "
          f"cached {model.n_cached} ({model.cache_bytes/1e6:.1f} MB)")

    per_task: dict[str, dict] = {}
    t0 = time.perf_counter()
    n_files_scored = 0
    for cid, tf in task_files.items():
        scores = rank_task(model, tf, plan, emb_lookup)
        per_task[cid] = {"scores": scores}
        n_files_scored += len(scores)
    t_rank = time.perf_counter() - t0
    print(f"[score] scored {n_files_scored} (task,file) pairs in {t_rank:.1f}s")

    # ---- rankings for SweRank + matched baselines ----
    by_cid = {t.case_id: t for t in tasks}
    results: dict[str, dict] = {}
    for cid in per_task:
        tf = task_files[cid]
        t = by_cid[cid]
        universe = tf["paths"]
        write_set = frozenset(t.write_set)
        ranked = rank_files(per_task[cid]["scores"], universe, write_set)
        results[cid] = {
            "repository": tf["repository"],
            "case_id": cid,
            "write_set": sorted(write_set),
            "proxy": sorted(t.proxy),
            "fn_paths": list(t.fn_paths),
            "n_missed": t.n_missed,
            "omitted_size": len([p for p in universe if p not in write_set]),
            "swe_ranked": ranked,
            "routeb_ranked": rank_composite(t),
            "bm25_ranked": rank_bm25(t),
            "r1_ranked": rank_bm25_rev_support(t),
            "query_sha256": sha256_text(tf["intent_text"]),
            "parent_commit": tf["parent_commit"],
            "n_files": len(universe),
        }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.joinpath("task_rankings.json").write_text(
        json.dumps(results, indent=1), encoding="utf-8")
    OUT_DIR.joinpath("blob_manifest.json").write_text(
        json.dumps({k: list(v) for k, v in blobs.items()}, indent=1), encoding="utf-8")
    OUT_DIR.joinpath("unit_manifest.json").write_text(
        json.dumps({k: list(v) for k, v in plan.items()}, indent=1), encoding="utf-8")
    OUT_DIR.joinpath("model_pin.json").write_text(
        json.dumps({"model_id": MODEL_ID, "revision": MODEL_REVISION,
                    "max_seq_length": 1024, "prompt_name": "query",
                    "dtype": "float32(cpu)", "license": "CC-BY-NC-4.0"}, indent=1),
        encoding="utf-8")

    # ---- metrics ----
    metrics, gate = evaluate(results, by_cid)
    OUT_DIR.joinpath("metrics.json").write_text(json.dumps(metrics, indent=1), encoding="utf-8")
    OUT_DIR.joinpath("gate.json").write_text(json.dumps(gate, indent=1), encoding="utf-8")

    efficiency = {
        "api_calls": 0, "api_cost_usd": 0.0,
        "model_load_seconds": round(t_load, 2),
        "materialize_seconds": round(t_materialize, 2),
        "encode_seconds": round(t_encode, 2),
        "per_task_scoring_seconds": round(t_rank, 2),
        "total_seconds": round(time.perf_counter() - t_start, 2),
        "distinct_blobs": len(blobs),
        "distinct_units": len(units),
        "missing_blobs": n_missing,
        "cached_unit_embeddings": model.n_cached,
        "embedding_cache_bytes": model.cache_bytes,
        "per_query_seconds_est": round((t_encode + t_rank) / len(per_task), 4),
    }
    OUT_DIR.joinpath("efficiency.json").write_text(json.dumps(efficiency, indent=1), encoding="utf-8")
    print(json.dumps({r: metrics["repos"][r]["B"]["5"]["swerank_embed"]["macro_orr"]
                      for r in ("djangocms", "saleor")}, indent=1))
    print("decision:", gate["decision"])
    print("wrote", OUT_DIR)
    return 0


# --------------------------------------------------------------------------
def _per_task_metric_contribs(results: dict, by_cid: dict, B: int,
                              rank_key: str):
    """Aligned per-task contribution tuples for the pooled metrics."""
    rows = []
    for cid, r in results.items():
        t = by_cid[cid]
        pos = set(t.proxy)
        fn_set = set(t.fn_paths)
        ranked = r[rank_key]
        B_eff = min(B, r["omitted_size"])
        added = set(ranked[:B_eff])
        final = set(t.write_set) | added
        tp = len(final & pos)
        fp = len(final - pos)
        fn = len(pos - final)
        recovered = len(added & fn_set)
        cand_fn = len(added & fn_set)
        cand_sel = len(added)
        missed = t.n_missed
        orr_i = (recovered / missed) if missed else 0.0  # frozen macro convention
        rows.append({
            "tp": tp, "fp": fp, "fn": fn,
            "recovered": recovered, "missed": missed, "orr_i": orr_i,
            "cand_fn": cand_fn, "cand_sel": cand_sel,
        })
    return rows


def evaluate(results: dict, by_cid: dict) -> tuple[dict, dict]:
    methods = ("routeb", "bm25", "r1", "swerank_embed")
    _RANK_KEY = {"routeb": "routeb_ranked", "bm25": "bm25_ranked",
                 "r1": "r1_ranked", "swerank_embed": "swe_ranked"}
    metrics: dict = {"repos": {}, "BUDGETS": list(BUDGETS)}
    for repo in ("djangocms", "saleor"):
        cids = [c for c in results if results[c]["repository"] == repo]
        per_b: dict = {}
        for B in BUDGETS:
            per_b[str(B)] = {}
            for m in methods:
                rows = _per_task_metric_contribs({c: results[c] for c in cids}, by_cid, B,
                                                 _RANK_KEY[m])
                tp = sum(r["tp"] for r in rows)
                fp = sum(r["fp"] for r in rows)
                fn = sum(r["fn"] for r in rows)
                vals = {}
                for k in ("tp", "fp", "fn"):
                    vals[k] = sum(r[k] for r in rows)
                p = tp / (tp + fp) if (tp + fp) else 0.0
                rec = tp / (tp + fn) if (tp + fn) else 0.0
                f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
                fnr = fn / (tp + fn) if (tp + fn) else 0.0
                orr = sum(r["orr_i"] for r in rows) / len(rows) if rows else 0.0
                cand_sel = sum(r["cand_sel"] for r in rows)
                cand_fn = sum(r["cand_fn"] for r in rows)
                cand_p = cand_fn / cand_sel if cand_sel else 0.0
                per_b[str(B)][m] = {
                    "tp": tp, "fp": fp, "fn": fn,
                    "precision": round(p, 4), "recall": round(rec, 4),
                    "f1": round(f1, 4), "fnr": round(fnr, 4),
                    "macro_orr": round(orr, 4),
                    "candidate_precision": round(cand_p, 4),
                    "n_tasks": len(cids),
                }
        metrics["repos"][repo] = {"n_tasks_dev": len(cids), "B": per_b}
    gate = build_gate(metrics, results, by_cid)
    return metrics, gate


def build_gate(metrics: dict, results: dict, by_cid: dict) -> dict:
    """Frozen progression gate vs the matched frozen baseline (Route-B composite)."""
    gate: dict = {"reference_budget": B_REF, "baseline": "routeb", "repos": {},
                  "non_inferiority_margin_recall": 0.05,
                  "non_inferiority_margin_fnr": 0.05,
                  "decision": "SWERANK_EMBED_FAIL"}
    all_pass = True
    for repo in ("djangocms", "saleor"):
        b5 = metrics["repos"][repo]["B"][str(B_REF)]
        sw = b5["swerank_embed"]
        rb = b5["routeb"]
        cids = [c for c in results if results[c]["repository"] == repo]
        ci = ci_map(repo, results, by_cid)
        a = sw["f1"] - rb["f1"] > 0.0
        b = sw["recall"] >= rb["recall"] - 0.05
        c = sw["fnr"] <= rb["fnr"] + 0.05
        d = sw["precision"] >= rb["precision"] or (sw["precision"] - rb["precision"] >= -0.02
                                                   and sw["f1"] >= rb["f1"] + 0.02)
        e = sum(1 for x in fold_direction(cids, by_cid, results) if x >= 0.5) >= 3
        rec = all([a, b, c, d, e])
        all_pass = all_pass and rec
        gate["repos"][repo] = {
            "A_f1_direction_positive": a, "f1_delta": round(sw["f1"] - rb["f1"], 4),
            "B_recall_not_materially_worse": b, "recall_delta": round(sw["recall"] - rb["recall"], 4),
            "C_fnr_not_materially_worse": c, "fnr_delta": round(sw["fnr"] - rb["fnr"], 4),
            "D_precision_rule": d, "precision_delta": round(sw["precision"] - rb["precision"], 4),
            "E_folds_ge_3_5": e, "fold_frac": [round(x, 2) for x in fold_direction(cids, by_cid, results)],
            "ci": ci,
            "pass": rec,
        }
    gate["pass"] = all_pass
    gate["decision"] = "SWERANK_EMBED_PASS" if all_pass else "SWERANK_EMBED_FAIL"
    return gate


def fold_direction(cids: list, by_cid: dict, results: dict, folds: int = 5, seed: int = SEED) -> list[float]:
    import random
    rng = random.Random(seed)
    order = list(cids)
    rng.shuffle(order)
    out = []
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
            rB = r["routeb_ranked"][:B_eff]
            sB = r["swe_ranked"][:B_eff]
            fn_set = set(t.fn_paths)
            q = len(set(sB) & fn_set) / M
            a = len(set(rB) & fn_set) / M
            pos += 1.0 if q > a else (0.5 if q == a else 0.0)
        out.append(pos / len(fold) if fold else 0.0)
    return out


def ci_map(repo: str, results: dict, by_cid: dict) -> dict:
    """Paired bootstrap CIs (SweRank - RouteB) for each pooled metric at B=5."""
    cids = [c for c in results if results[c]["repository"] == repo]
    if not cids:
        return {}
    rows: dict[str, list] = {m: [] for m in METRIC_NAMES}
    rb_rows: dict[str, list] = {m: [] for m in METRIC_NAMES}
    for cid in cids:
        r = results[cid]
        t = by_cid[cid]
        sw = _contrib(r, t, "swe_ranked", B_REF)
        rb = _contrib(r, t, "routeb_ranked", B_REF)
        rows["macro_orr"].append((sw["orr"],))
        rb_rows["macro_orr"].append((rb["orr"],))
        for name in ("final_precision", "final_recall", "final_f1", "final_fnr"):
            rows[name].append((sw["tp"], sw["fp"], sw["fn"]))
            rb_rows[name].append((rb["tp"], rb["fp"], rb["fn"]))
        rows["candidate_precision"].append((sw["cand_fn"], sw["cand_sel"]))
        rb_rows["candidate_precision"].append((rb["cand_fn"], rb["cand_sel"]))
    out = {}
    for m in METRIC_NAMES:
        out[m] = paired_bootstrap(rb_rows[m], rows[m], m, N_RESAMPLES, SEED)
    return out


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


if __name__ == "__main__":
    raise SystemExit(main())
