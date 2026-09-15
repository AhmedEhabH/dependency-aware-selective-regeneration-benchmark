#!/usr/bin/env python3
"""POST-ICCI — Recompute LocAgent two ways from existing frozen evidence (ZERO API).

A. FAIL-CLOSED all-10-task common metrics — the scientific headline:
   every one of the 10 HELD_OUT_TEST outcomes enters the pooled micro
   metrics; the 5 empty outcomes contribute predicted={} (TP=FP=0, FN=|G_t|).

B. USABLE-OUTPUT-ONLY 5-task metrics — DIAGNOSTIC ONLY (survivor-conditioned):
   pooled micro + macro means over the 5 tasks with a non-empty, parseable,
   in-universe predicted file set. NOT the headline; the survivor-conditioned
   bias (only cases that ran to a usable localization) is stated explicitly.

Failure taxonomy is preserved from the raw logs (audited 2026-09-15):
   2 timeout, 1 context-length BadRequest, 2 completed-but-empty.

All metrics are recomputed from raw evidence (research/locagent-p5b/out_c +
benchmark_data/real_commit_impact_v1) — NOT copied from a previous summary —
so this script is a standalone independent recomputation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PACKAGE_ROOT))
sys.path.insert(0, str(_PACKAGE_ROOT / "src"))

from benchmark.locagent import evaluator  # noqa: E402

DATASET_DIR = _PACKAGE_ROOT / "benchmark_data" / "real_commit_impact_v1"
P5C_DIR = _PACKAGE_ROOT / "research" / "locagent-p5b" / "out_c"
OUT_PATH = _PACKAGE_ROOT / "research" / "locagent-p5b" / "locagent_two_way.json"

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

# Audited failure taxonomy (raw localize.log evidence; NOT "5 timeouts").
EMPTY_TAXONOMY: dict[str, str] = {
    "djangocms-rc-4307e1b8c2e2": "timeout",
    "djangocms-rc-66c70394c9e1": "context_length_badrequest",
    "djangocms-rc-9e33db4f4660": "completed_but_empty",
    "djangocms-rc-b39799f9fc1c": "completed_but_empty",
    "djangocms-rc-fdda30c271f0": "timeout",
}

USABLE_TASKS = [cid for cid in HELD_OUT if cid not in EMPTY_TAXONOMY]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def proxy_paths(case_id: str) -> set[str]:
    p = DATASET_DIR / "scientific" / case_id / "hidden" / "observed_change_set_proxy.json"
    return set(_load_json(p)["paths"])


def universe(case_id: str) -> set[str]:
    p = DATASET_DIR / "scientific" / case_id / "public" / "candidate_universe.json"
    return {str(r["path"]) for r in _load_json(p)["records"]}


def load_merged() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for line in (P5C_DIR / "merged_loc_outputs_mrr.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        out[row["instance_id"]] = row
    return out


def ranked_files(case_id: str, merged: dict[str, dict[str, Any]]) -> tuple[str, ...]:
    m = merged.get(case_id, {})
    ff = m.get("found_files") or []
    if ff and isinstance(ff[0], list):
        return tuple(ff[0])
    if isinstance(ff, list):
        return tuple(ff)
    return ()


def load_ledger() -> dict[str, list[dict[str, Any]]]:
    by_case: dict[str, list[dict[str, Any]]] = {}
    path = P5C_DIR / "usage_ledger.jsonl"
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


def per_task_metrics(case_id: str, merged: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Common-evaluator metrics for ONE task (exact emitted file set, in-universe)."""
    proxy = proxy_paths(case_id)
    uni = universe(case_id)
    ranked = ranked_files(case_id, merged)
    predicted = set(ranked) & uni
    res = evaluator.common_evaluator(
        predicted_file_set=predicted,
        proxy_paths=proxy,
        valid_output=bool(predicted),
    )
    return {
        "case_id": case_id,
        "predicted_file_set": sorted(predicted),
        "predicted_count": len(predicted),
        "ranked_count": len(ranked),
        "out_of_universe_ranked": sorted(set(ranked) - uni),
        "proxy_size": len(proxy),
        "tp": res["tp"],
        "fp": res["fp"],
        "fn": res["fn"],
        "precision": res["precision"],
        "recall": res["recall"],
        "f1": res["f1"],
        "fnr": res["fnr"],
    }


def _micro_pooled(rows: list[dict[str, Any]]) -> dict[str, float]:
    tp = sum(r["tp"] for r in rows)
    fp = sum(r["fp"] for r in rows)
    fn = sum(r["fn"] for r in rows)
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    fnr = fn / (tp + fn) if (tp + fn) else 0.0
    return {
        "tp": tp, "fp": fp, "fn": fn,
        "precision": round(p, 6), "recall": round(r, 6),
        "f1": round(f1, 6), "fnr": round(fnr, 6),
    }


def _macro_mean(rows: list[dict[str, Any]], key: str) -> float:
    if not rows:
        return 0.0
    return round(sum(float(r[key]) for r in rows) / len(rows), 6)


def main() -> int:
    merged = load_merged()
    ledger = load_ledger()
    task_rows = {cid: per_task_metrics(cid, merged) for cid in HELD_OUT}

    # --- A. Fail-closed all-10 (HEADLINE) ---
    fail_closed = _micro_pooled([task_rows[cid] for cid in HELD_OUT])

    # --- B. Usable-output-only 5-task (DIAGNOSTIC, survivor-conditioned) ---
    usable_rows = [task_rows[cid] for cid in USABLE_TASKS]
    usable = _micro_pooled(usable_rows)
    usable_macro = {
        "precision": _macro_mean(usable_rows, "precision"),
        "recall": _macro_mean(usable_rows, "recall"),
        "f1": _macro_mean(usable_rows, "f1"),
        "fnr": _macro_mean(usable_rows, "fnr"),
    }

    # Efficiency (authoritative per-call ledger) per task.
    efficiency: dict[str, dict[str, float]] = {}
    for cid in HELD_OUT:
        cells = ledger.get(cid, [])
        pt = sum(c["prompt_tokens"] for c in cells)
        ct = sum(c["completion_tokens"] for c in cells)
        efficiency[cid] = {
            "prompt_tokens": pt,
            "completion_tokens": ct,
            "total_tokens": pt + ct,
            "model_calls": len(cells),
            "cost_usd": round(sum(c["estimated_cost_usd"] for c in cells), 6),
        }

    out = {
        "classification": "POST-ICCI ZERO-API RECOMPUTATION (raw evidence only)",
        "computed_at": "2026-09-15",
        "zero_api": True,
        "headline_A_fail_closed_all_10": {
            "label": "FAIL-CLOSED all-10-task common metrics — SCIENTIFIC HEADLINE",
            "denominator": "10 tasks x 1 execution = 10 outcomes; 5 empty outcomes enter as predicted={}",
            "micro_pooled": fail_closed,
        },
        "diagnostic_B_usable_5": {
            "label": "USABLE-OUTPUT-ONLY 5-task metrics — DIAGNOSTIC ONLY (survivor-conditioned)",
            "warning": "NOT the headline. Computed only over tasks that produced a usable localization; "
                       "survivor-conditioned bias is explicit.",
            "usable_task_ids": USABLE_TASKS,
            "micro_pooled": usable,
            "macro_mean": usable_macro,
        },
        "failure_taxonomy": {
            "label": "preserved from raw logs (audited 2026-09-15)",
            "timeout": [cid for cid, t in EMPTY_TAXONOMY.items() if t == "timeout"],
            "context_length_badrequest": [
                cid for cid, t in EMPTY_TAXONOMY.items() if t == "context_length_badrequest"
            ],
            "completed_but_empty": [
                cid for cid, t in EMPTY_TAXONOMY.items() if t == "completed_but_empty"
            ],
            "counts": {
                "timeout": sum(1 for t in EMPTY_TAXONOMY.values() if t == "timeout"),
                "context_length_badrequest": sum(
                    1 for t in EMPTY_TAXONOMY.values() if t == "context_length_badrequest"
                ),
                "completed_but_empty": sum(
                    1 for t in EMPTY_TAXONOMY.values() if t == "completed_but_empty"
                ),
                "total_empty": len(EMPTY_TAXONOMY),
            },
        },
        "per_task": task_rows,
        "efficiency": efficiency,
        "note": "A is the headline. B is survivor-conditioned diagnostic only and MUST NOT be "
                "reported as the primary LocAgent result.",
    }
    OUT_PATH.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print("=== LOCAGENT TWO-WAY RECOMPUTATION (ZERO API, raw evidence) ===")
    print(f"A. FAIL-CLOSED ALL-10 (HEADLINE): {fail_closed}")
    print(f"B. USABLE-5 (DIAGNOSTIC, survivor-conditioned): micro {usable} macro {usable_macro}")
    print(f"USABLE_TASKS={USABLE_TASKS}")
    print(f"EMPTY_TAXONOMY={EMPTY_TAXONOMY}")
    for cid in HELD_OUT:
        t = task_rows[cid]
        print(
            f"  {cid}: pred={t['predicted_count']} oou={len(t['out_of_universe_ranked'])} "
            f"|G|={t['proxy_size']} TP={t['tp']} FP={t['fp']} FN={t['fn']} "
            f"P={t['precision']:.4f} R={t['recall']:.4f} F1={t['f1']:.4f}"
        )
    print(f"Wrote: {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
