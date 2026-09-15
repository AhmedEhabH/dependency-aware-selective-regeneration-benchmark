#!/usr/bin/env python3
"""P5-C — Shared-protocol Full-v2 / Sparse-v2 / LocAgent comparison scorer.

Produces ONE scientifically valid table on the SAME 10 held-out real tasks:

- Full-v2, Sparse-v2: recomputed from existing frozen P1 raw evidence only
  (research/real-commit-p1-01/final_metrics.json). NO P1 rerun.
- LocAgent: NEW P5-C outputs (research/locagent-p5b/out_c/...), scored with the
  frozen common evaluator against the SAME observed change-set proxy.

Metrics (frozen):
- pooled micro TP/FP/FN/P/R/F1/FNR (primary);
- task-level macro means (secondary);
- paired task-level differences (LocAgent vs Full, LocAgent vs Sparse);
- bootstrap over the 10 independent tasks (CI95).
- efficiency per task: tokens (prompt/completion), model calls (from the
  per-call usage ledger, never len(raw_output_loc)), cost (real tokens x
  frozen P1 pricing), latency.
- LocAgent-native metrics reported SEPARATELY using the ORIGINAL ranked order
  from merged_loc_outputs_mrr.jsonl (never reconstructed from a Python set):
  * official LocAgent file-level Acc@K (task hit iff #correct-in-topK ==
    min(len(proxy), K)) — mirrors the pinned upstream evaluation/eval_metric.py
    `acc_at_k`;
  * simple task-level Hit@K (>=1 proxy file among top-K) as a secondary label;
  * item-hit counts are NOT reported as task accuracy (historical bug).
- Execution/validity reported with EXPLICIT denominators: independent tasks,
  runs/cells, non-empty/parseable outcomes, fail-closed/empty outcomes. The
  ambiguous single "Valid" column (30/30 vs 5/10) is not used.
- Efficiency ratios use ONE consistent denominator (mean per execution/task).

Classification: SYSTEM-LEVEL SHARED-PROTOCOL COMPARISON (P1 temperature 0 vs
LocAgent upstream temperature 1) — not a pure algorithm ablation.

ZERO additional model calls.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PACKAGE_ROOT))
sys.path.insert(0, str(_PACKAGE_ROOT / "src"))

from benchmark.locagent import evaluator  # noqa: E402

DATASET_DIR = _PACKAGE_ROOT / "benchmark_data" / "real_commit_impact_v1"
P1_METRICS = _PACKAGE_ROOT / "research" / "real-commit-p1-01" / "final_metrics.json"
P5C_DIR = _PACKAGE_ROOT / "research" / "locagent-p5b" / "out_c"

HELD_OUT = [
    "djangocms-rc-4307e1b8c2e2",
    "djangocms-rc-50c3576080be",
    "djangocms-rc-630a50361ada",
    "djangocms-rc-66c70394c9e1",
    "djangocms-rc-75978fb1c3ad",
    "djangocms-rc-8d50660e7bcf",
    "djangocms-rc-9e33db4f4660",
    "djangocms-rc-b39799f9fc1c",
    "djangocms-rc-ba16eb9a1d09",
    "djangocms-rc-fdda30c271f0",
]

BOOTSTRAP_ITER = 10_000
RNG_SEED = 20260915


def _load_json(path: Path) -> dict[str, Any]:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def proxy_paths(case_id: str) -> set[str]:
    p = DATASET_DIR / "scientific" / case_id / "hidden" / "observed_change_set_proxy.json"
    return set(_load_json(p)["paths"])


def universe(case_id: str) -> set[str]:
    p = DATASET_DIR / "scientific" / case_id / "public" / "candidate_universe.json"
    return {str(r["path"]) for r in _load_json(p)["records"]}


# ---------------------------------------------------------------------------
# LocAgent outputs
# ---------------------------------------------------------------------------


def load_locagent_outputs() -> dict[str, dict[str, Any]]:
    """loc_outputs.jsonl keyed by case; merged ranking from merged file."""
    out: dict[str, dict[str, Any]] = {}
    loc_path = P5C_DIR / "loc_outputs.jsonl"
    if loc_path.exists():
        for line in loc_path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            out[row["instance_id"]] = {"loc": row}
    merged_path = P5C_DIR / "merged_loc_outputs_mrr.jsonl"
    if merged_path.exists():
        for line in merged_path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row["instance_id"] in out:
                out[row["instance_id"]]["merged"] = row
    return out


def load_ledger() -> dict[str, list[dict[str, Any]]]:
    """Per-call usage ledger keyed by case (authoritative model-call count)."""
    path = P5C_DIR / "usage_ledger.jsonl"
    by_case: dict[str, list[dict[str, Any]]] = {}
    if not path.exists():
        return by_case
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        cid = row.get("case_id") or ""
        by_case.setdefault(cid, []).append(row)
    return by_case


def locagent_ranked_files(case_id: str, outputs: dict[str, dict[str, Any]]) -> tuple[str, ...]:
    """Native ranked order from merged_loc_outputs_mrr.jsonl (never a set)."""
    merged = outputs.get(case_id, {}).get("merged")
    if merged:
        ff = merged.get("found_files") or []
        if isinstance(ff, list) and ff and isinstance(ff[0], list):
            return tuple(ff[0])
        if isinstance(ff, list):
            return tuple(ff)
    loc = outputs.get(case_id, {}).get("loc") or {}
    ff = loc.get("found_files") or []
    if isinstance(ff, list) and ff and isinstance(ff[0], list):
        return tuple(ff[0])
    if isinstance(ff, list):
        return tuple(ff)
    return ()


# ---------------------------------------------------------------------------
# P1 Full/Sparse evidence (frozen, no rerun)
# ---------------------------------------------------------------------------


def p1_arm_summary() -> dict[str, Any]:
    p1 = _load_json(P1_METRICS)
    out: dict[str, Any] = {}
    for arm in ("full_v2", "sparse_v2"):
        a = p1["arms"][arm]
        out[arm] = {
            "micro": a["micro_overall"],
            "valid": a["valid"],
            "validity_rate": a["validity_rate"],
            "completion_tokens_mean": a["completion_tokens"]["mean"],
            "prompt_tokens_mean": a["prompt_tokens"]["mean"],
            "model_calls": a["calls"],
            "cost_usd": a["api_cost_usd"],
            "latency_seconds": a["latency_seconds"],
            "serialized_records_mean": a["serialized_records"]["mean"],
        }
    return out


def p1_task_level(arm: str) -> dict[str, dict[str, Any]]:
    p1 = _load_json(P1_METRICS)
    out: dict[str, dict[str, Any]] = {}
    for cid, tl in p1["task_level"].items():
        out[cid] = {
            "micro": tl[f"{arm}_micro"],
            "completion_mean": tl[f"{arm}_completion_mean"],
            "cost": tl[f"{arm}_cost"],
        }
    return out


# ---------------------------------------------------------------------------
# Bootstrap over the 10 independent tasks
# ---------------------------------------------------------------------------


def _bootstrap_mean_delta(
    deltas: list[float], iterations: int = BOOTSTRAP_ITER, seed: int = RNG_SEED
) -> dict[str, float]:
    rng = random.Random(seed)
    n = len(deltas)
    samples: list[float] = []
    for _ in range(iterations):
        idx = [rng.randrange(n) for _ in range(n)]
        samples.append(sum(deltas[i] for i in idx) / n)
    samples.sort()
    return {
        "mean_delta": round(sum(deltas) / n, 6),
        "ci95_low": round(samples[int(0.025 * len(samples))], 6),
        "ci95_high": round(samples[int(0.975 * len(samples))], 6),
    }


def _micro_pooled(rows: list[dict[str, Any]]) -> dict[str, float]:
    tp = sum(r["tp"] for r in rows)
    fp = sum(r["fp"] for r in rows)
    fn = sum(r["fn"] for r in rows)
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    fnr = fn / (tp + fn) if (tp + fn) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": round(p, 6), "recall": round(r, 6),
            "f1": round(f1, 6), "fnr": round(fnr, 6)}


def _macro_mean(rows: list[dict[str, Any]], key: str) -> float:
    if not rows:
        return 0.0
    total = 0.0
    for r in rows:
        total += float(r[key])
    return round(total / len(rows), 6)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    outputs = load_locagent_outputs()
    ledger = load_ledger()

    loc_rows: list[dict[str, Any]] = []
    loc_per_task: dict[str, dict[str, Any]] = {}
    acc_k_rows: list[dict[str, Any]] = []
    loc_efficiency: dict[str, dict[str, Any]] = {}

    for cid in HELD_OUT:
        proxy = proxy_paths(cid)
        uni = universe(cid)
        ranked = locagent_ranked_files(cid, outputs)
        predicted = set(ranked) & uni
        cells = ledger.get(cid, [])
        pt = sum(c["prompt_tokens"] for c in cells)
        ct = sum(c["completion_tokens"] for c in cells)
        n_calls = len(cells)
        cost = sum(c["estimated_cost_usd"] for c in cells)
        latency = sum(c["latency_s"] for c in cells)

        res = evaluator.common_evaluator(
            predicted_file_set=predicted,
            proxy_paths=proxy,
            valid_output=bool(predicted),
            model_calls=n_calls,
            prompt_tokens=pt,
            completion_tokens=ct,
            cost_usd=cost,
            latency_s=round(latency, 4),
            native_ranked_files=ranked,
        )
        res["case_id"] = cid
        loc_rows.append(res)
        loc_per_task[cid] = res

        # Native metrics from the ORIGINAL ranked order (never a set).
        # Official LocAgent Acc@K (task hit iff correct-in-topK ==
        # min(len(proxy), K)), simple Hit@K (>=1 proxy file in top-K), and
        # raw item-hit counts (audit-only, never labelled as task accuracy).
        for k in (1, 3, 5):
            acc = evaluator.locagent_acc_at_k(ranked, proxy, k)
            hit = evaluator.locagent_hit_at_k(ranked, proxy, k)
            items = evaluator.locagent_item_hits_at_k(ranked, proxy, k)
            acc_k_rows.append({
                "case_id": cid, "k": k,
                "official_acc": 1 if acc else 0,
                "hit_at_k": 1 if hit else 0,
                "item_hits": items,
            })

        loc_efficiency[cid] = {
            "prompt_tokens": pt, "completion_tokens": ct, "total_tokens": pt + ct,
            "model_calls": n_calls, "cost_usd": round(cost, 6),
            "latency_s": round(latency, 4), "found_files": len(predicted),
            "proxy_size": len(proxy), "ranked_count": len(ranked),
        }

    micro_loc = _micro_pooled(loc_rows)

    # Full/Sparse from P1 frozen evidence
    p1 = p1_arm_summary()
    p1_micro = {arm: p1[arm]["micro"] for arm in ("full_v2", "sparse_v2")}

    print("=== P5-C SHARED-PROTOCOL COMPARISON (10 real held-out tasks) ===")
    print("Classification: SYSTEM-LEVEL SHARED-PROTOCOL (P1 temp 0 vs LocAgent temp 1)\n")
    print("Execution/validity denominators are EXPLICIT: independent tasks; runs/cells")
    print("(P1 = 10 tasks x 3 nested reps = 30 cells; LocAgent = 10 tasks x 1 exec);")
    print("non-empty/parseable outcomes; fail-closed/empty outcomes.\n")

    hdr = (
        f"{'System':<10} {'tasks':>5} {'runs':>5} {'nonempty':>8} {'failclosed':>10} "
        f"{'P':>7} {'R':>7} {'F1':>7} {'FNR':>7} "
        f"{'comp_tok':>10} {'calls':>5} {'cost':>9} {'lat':>8}"
    )
    print(hdr)
    print("-" * len(hdr))
    loc_valid = sum(1 for r in loc_rows if r["valid_output"])
    loc_fail_closed = len(loc_rows) - loc_valid
    loc_comp_mean = round(sum(r["completion_tokens"] for r in loc_rows) / max(1, len(loc_rows)), 1)
    loc_calls = sum(r["model_calls"] for r in loc_rows)
    loc_cost = round(sum(r["cost_usd"] for r in loc_rows), 6)
    loc_lat = round(sum(r["latency_s"] for r in loc_rows), 1)
    rows_out = [
        ("Full-v2", 10, 30, 30, 0, p1_micro["full_v2"], p1["full_v2"]["completion_tokens_mean"],
         p1["full_v2"]["model_calls"], p1["full_v2"]["cost_usd"], p1["full_v2"]["latency_seconds"]),
        ("Sparse-v2", 10, 30, 30, 0, p1_micro["sparse_v2"], p1["sparse_v2"]["completion_tokens_mean"],
         p1["sparse_v2"]["model_calls"], p1["sparse_v2"]["cost_usd"], p1["sparse_v2"]["latency_seconds"]),
        ("LocAgent", 10, 10, loc_valid, loc_fail_closed, micro_loc, loc_comp_mean,
         loc_calls, loc_cost, loc_lat),
    ]
    for label, tasks, runs, nonempty, failclosed, micro, comp, calls, cost, lat in rows_out:
        print(
            f"{label:<10} {tasks:>5} {runs:>5} {nonempty:>8} {failclosed:>10} "
            f"{micro['precision']:>7.3f} {micro['recall']:>7.3f} "
            f"{micro['f1']:>7.3f} {micro['fnr']:>7.3f} {comp:>10.1f} {calls:>5} "
            f"{cost:>9.4f} {lat:>8.1f}"
        )

    print("\n--- Macro means (task-level, secondary) ---")
    # Full/Sparse macro from frozen P1 task_level
    for arm, label in (("full_v2", "Full-v2"), ("sparse_v2", "Sparse-v2")):
        tl = p1_task_level(arm)
        micros = [v["micro"] for v in tl.values()]
        print(
            f"{label:<10} macro P={_macro_mean(micros, 'precision'):.3f} "
            f"R={_macro_mean(micros, 'recall'):.3f} F1={_macro_mean(micros, 'f1'):.3f} "
            f"FNR={_macro_mean(micros, 'fnr'):.3f}"
        )
    print(
        f"{'LocAgent':<10} macro P={_macro_mean(loc_rows, 'precision'):.3f} "
        f"R={_macro_mean(loc_rows, 'recall'):.3f} F1={_macro_mean(loc_rows, 'f1'):.3f} "
        f"FNR={_macro_mean(loc_rows, 'fnr'):.3f}"
    )

    print("\n--- Paired task-level F1 deltas + bootstrap (10 independent tasks) ---")
    full_f1 = {cid: p1_task_level("full_v2")[cid]["micro"]["f1"] for cid in HELD_OUT}
    sparse_f1 = {cid: p1_task_level("sparse_v2")[cid]["micro"]["f1"] for cid in HELD_OUT}
    loc_f1 = {cid: loc_per_task[cid]["f1"] for cid in HELD_OUT}

    for label_a, label_b, f_a, f_b in (
        ("LocAgent", "Full", loc_f1, full_f1),
        ("LocAgent", "Sparse", loc_f1, sparse_f1),
    ):
        deltas = [f_a[cid] - f_b[cid] for cid in HELD_OUT]
        bs = _bootstrap_mean_delta(deltas)
        print(f"delta F1 {label_a}-{label_b}: mean {bs['mean_delta']:.4f} "
              f"CI95 [{bs['ci95_low']:.4f}, {bs['ci95_high']:.4f}]")

    print("\n--- LocAgent-native metrics (from original ranked order, separate from F1) ---")
    for k in (1, 3, 5):
        n_acc = sum(r["official_acc"] for r in acc_k_rows if r["k"] == k)
        n_hit = sum(r["hit_at_k"] for r in acc_k_rows if r["k"] == k)
        n_items = sum(r["item_hits"] for r in acc_k_rows if r["k"] == k)
        print(
            f"  Acc@{k} (official: correct-in-topK == min(proxy,K)): "
            f"{n_acc}/10 ({n_acc / len(HELD_OUT):.3f})"
        )
        print(
            f"  Hit@{k} (task-level >=1 proxy file in top-K): "
            f"{n_hit}/10 ({n_hit / len(HELD_OUT):.3f})"
        )
        print(f"  item-hits@{k} (audit-only, NOT task accuracy): {n_items}")

    print("\n--- LocAgent efficiency per task ---")
    for cid in HELD_OUT:
        e = loc_efficiency[cid]
        print(
            f"  {cid}: pred={e['found_files']} proxy={e['proxy_size']} "
            f"calls={e['model_calls']} ptok={e['prompt_tokens']} "
            f"ctok={e['completion_tokens']} cost=${e['cost_usd']:.6f} "
            f"lat={e['latency_s']}s"
        )

    # Persist summary JSON
    out = {
        "classification": "SYSTEM-LEVEL SHARED-PROTOCOL COMPARISON",
        "note": "P1 temperature 0; LocAgent upstream temperature 1. Not a pure algorithm ablation.",
        "provider_route": evaluator.LOCAGENT_PROVIDER_ROUTE_NOTE,
        "micro_pooled": {"Full-v2": p1_micro["full_v2"], "Sparse-v2": p1_micro["sparse_v2"], "LocAgent": micro_loc},
        "execution_validity": {
            "Full-v2": {"independent_tasks": 10, "runs_or_cells": 30, "nonempty_parseable": 30, "fail_closed_empty": 0},
            "Sparse-v2": {"independent_tasks": 10, "runs_or_cells": 30, "nonempty_parseable": 30, "fail_closed_empty": 0},
            "LocAgent": {"independent_tasks": 10, "runs_or_cells": 10, "nonempty_parseable": loc_valid, "fail_closed_empty": loc_fail_closed},
        },
        "locagent_efficiency": loc_efficiency,
        "locagent_native": {
            "official_acc_at_k": [
                {"k": k, "hits": sum(r["official_acc"] for r in acc_k_rows if r["k"] == k),
                 "tasks": len(HELD_OUT)}
                for k in (1, 3, 5)
            ],
            "hit_at_k": [
                {"k": k, "hits": sum(r["hit_at_k"] for r in acc_k_rows if r["k"] == k),
                 "tasks": len(HELD_OUT)}
                for k in (1, 3, 5)
            ],
            "item_hits_at_k_audit_only": [
                {"k": k, "items": sum(r["item_hits"] for r in acc_k_rows if r["k"] == k)}
                for k in (1, 3, 5)
            ],
            "definition": "Acc@K (official) = task hit iff #correct among top-K == min(len(proxy), K); "
                          "Hit@K = task hit iff >=1 proxy file among top-K. Never label item-hits as task accuracy.",
        },
    }
    out_path = _PACKAGE_ROOT / "research" / "locagent-p5b" / "shared_comparison.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("\nWrote:", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
