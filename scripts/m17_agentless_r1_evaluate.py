#!/usr/bin/env python3
# ruff: noqa: E501
"""M17 Agentless-style R1 - Phases A9-A11: freeze, score, bootstrap, compare, receipt.

1. Read the frozen run records; assemble the 297-task prediction artifact and
   SHA-256 sidecar (prediction freeze).
2. ONLY THEN load gold (opened RESERVE-300 proxies).
3. Compute per-task confusion + pooled macro/micro metrics under the exact
   file-level evaluator used by R2 / MAIN_297.
4. Paired cluster bootstrap (10,000, seed 20261012) vs RM-CSS / AGENT / SIP.
5. Additive comparison + reproducibility receipt.
No frozen R2 artifact is modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.agentless_r1.evaluate import (  # noqa: E402
    compute_confusions,
    delta_f1_and_recall,
    freeze_predictions,
    load_gold,
    load_prediction_sets,
    pooled_metrics,
    size_statistics,
    write_json_lf,
)

OUT_DIR = PROJECT / "research" / "competitor-agentless-r1"
RUN_DIR = OUT_DIR / "run"
PROXIES = PROJECT / "research" / "saleor-reserve-300-rmcss" / "saleor_reserve_300_proxies.json"
MANIFEST = PROJECT / "research" / "wp1b" / "wp1b_main_297_manifest.json"
SIPR = PROJECT / "research" / "wp1a" / "sip_rmcss_per_task_predictions.json"
AGENT = PROJECT / "research" / "wp1b" / "main-297-2026-09-22" / "wp1b_agent_predictions.json"
R2_PT_METRICS = PROJECT / "research" / "competitor-baselines-r2" / "per_task_metrics_r2.json"
R2_PT_PREDS = PROJECT / "research" / "competitor-baselines-r2" / "per_task_predictions_r2.json"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_run_records(run_dir: Path) -> dict[str, dict]:
    records = {}
    path = run_dir / "agentless_r1_run_records.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            records[str(rec["task_id"])] = rec
    return records


def main(argv: list[str] | None = None) -> int:
    from argparse import Namespace

    ns = _parse_args(argv)
    run_dir = Path(ns.run_dir)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    task_ids = list(manifest["task_ids"])
    assert len(task_ids) == 297

    records = load_run_records(run_dir)
    missing = [t for t in task_ids if t not in records]
    if missing:
        print("MISSING_RECORDS", len(missing), missing[:10])
        return 2

    # ---- A9 step 1: freeze predictions BEFORE opening gold ----
    eval_rows = {
        tid: {
            "prediction_set": records[tid]["prediction_set"],
            "parsed_files": records[tid]["parsed_files"],
            "classification": records[tid]["classification"],
            "api_cost_usd": records[tid]["api_cost_usd"],
            "prompt_tokens": records[tid]["prompt_tokens"],
            "completion_tokens": records[tid]["completion_tokens"],
            "latency_seconds": records[tid]["latency_seconds"],
            "raw_output_sha256": records[tid]["raw_output_sha256"],
        }
        for tid in task_ids
    }
    pred_json = OUT_DIR / "agentless_r1_prediction_freeze.json"
    pred_sha = OUT_DIR / "agentless_r1_prediction_freeze.json.sha256"
    freeze_predictions(eval_rows, task_ids, pred_json, pred_sha)
    freeze_digest = _sha256_file(pred_json)
    sidecar_digest = pred_sha.read_text(encoding="utf-8").strip().split()[0]
    assert sidecar_digest == freeze_digest, "prediction freeze sidecar mismatch"
    print(f"prediction freeze: {pred_json} sha256={freeze_digest}")
    print("gold NOT yet opened at prediction-freeze time.")

    # ---- A9 step 2: only now open gold ----
    gold = load_gold(PROXIES)
    if not set(task_ids) <= set(gold):
        print("GOLD_MISSING_TASKS")
        return 2

    agentless_preds = load_prediction_sets(pred_json, task_ids)

    # frozen comparators
    sip_rmcss = json.loads(SIPR.read_text(encoding="utf-8"))["per_task"]
    sip = {t: frozenset(sip_rmcss[t]["sip_predicted_set"]) for t in task_ids}
    rmcss = {t: frozenset(sip_rmcss[t]["rmcss_predicted_set"]) for t in task_ids}
    agent_per = json.loads(AGENT.read_text(encoding="utf-8"))["per_task"]
    agent = {t: frozenset(agent_per[t]["selected_paths"]) for t in task_ids}

    r2_all_arms = json.loads(R2_PT_PREDS.read_text(encoding="utf-8"))
    r2_per = r2_all_arms["per_task"]

    arms = {
        "AGENTLESS_STYLE_ADAPTATION": agentless_preds,
        "RM-CSS": rmcss,
        "AGENT": agent,
        "SIP": sip,
    }
    for arm in r2_all_arms["arms"]:
        if arm in arms:
            continue
        arms[arm] = {t: frozenset(r2_per[t][f"{arm}_selected"]) for t in task_ids}

    # per-task confusion under the frozen evaluator
    confs = {arm: compute_confusions(pred, gold, task_ids) for arm, pred in arms.items()}
    sizes = {arm: [len(arms[arm][t]) for t in task_ids] for arm in arms}

    aggregates = {}
    for arm in arms:
        micro = pooled_metrics(list(confs[arm].values()))
        from statistics import fmean

        macro = {
            "precision": fmean([c.precision for c in confs[arm].values()]),
            "recall": fmean([c.recall for c in confs[arm].values()]),
            "f1": fmean([c.f1 for c in confs[arm].values()]),
        }
        aggregates[arm] = {
            "micro": micro,
            "macro": macro,
            "size": size_statistics(sizes[arm]),
            "empty_set_count": sum(1 for s in sizes[arm] if s == 0),
            "n_tasks": len(task_ids),
        }

    # ---- bootstrap: Agentless vs frozen RM-CSS / AGENT / SIP (paired, seed 20261012) ----
    bootstrap = {}
    for baseline in ("RM-CSS", "AGENT", "SIP"):
        bootstrap[f"AGENTLESS_vs_{baseline}"] = delta_f1_and_recall(
            {t: confs["AGENTLESS_STYLE_ADAPTATION"][t] for t in task_ids},
            {t: confs[baseline][t] for t in task_ids},
            task_ids,
        )

    # efficiency
    total_cost = round(sum(float(records[t]["api_cost_usd"]) for t in task_ids), 6)
    total_prompt = sum(int(records[t]["prompt_tokens"]) for t in task_ids)
    total_completion = sum(int(records[t]["completion_tokens"]) for t in task_ids)
    total_latency = sum(float(records[t]["latency_seconds"]) for t in task_ids)
    failures = sum(1 for t in task_ids if records[t]["ok"] is not True)
    empty = sum(1 for t in task_ids if records[t]["classification"] != "VALID")

    out = {
        "protocol_freeze": "research/competitor-agentless-r1/AGENTLESS_STYLE_ADAPTATION_PROTOCOL_FREEZE.json",
        "prediction_freeze_sha256": freeze_digest,
        "prediction_freeze_artifact": "research/competitor-agentless-r1/agentless_r1_prediction_freeze.json",
        "scientific_predictions_frozen": True,
        "gold_loaded_after_prediction_freeze": True,
        "protocol_changed_after_first_output": False,
        "population": {"n_tasks": len(task_ids), "manifest_sha256": manifest["manifest_sha256"]},
        "label": "AGENTLESS_STYLE_ADAPTATION (file-level localization comparator; NOT an exact published-Agentless reproduction)",
        "bootstrap": {
            "method": "paired cluster bootstrap over tasks",
            "n_resamples": 10000,
            "seed": 20261012,
            "per_comparison_delta_f1": {k: v["delta_f1_point"] for k, v in bootstrap.items()},
        },
        "bootstrap_details": bootstrap,
        "aggregates": aggregates,
        "efficiency": {
            "llm_calls": len(task_ids),
            "prompt_tokens": total_prompt,
            "completion_tokens": total_completion,
            "wall_latency_seconds": round(total_latency, 3),
            "api_cost_usd": total_cost,
            "price_source": "frozen deepinfra/turbo $0.30/$1.00 per 1M",
            "failures": failures,
            "failure_rate": round(failures / len(task_ids), 6),
            "empty_and_malfunction_count": empty,
        },
        "per_task_call_level": {
            t: {
                "prediction_set": records[t]["prediction_set"],
                "classification": records[t]["classification"],
                "parsed_files": records[t]["parsed_files"],
                "retry_count": records[t]["retry_count"],
                "api_cost_usd": records[t]["api_cost_usd"],
                "prompt_tokens": records[t]["prompt_tokens"],
                "completion_tokens": records[t]["completion_tokens"],
                "latency_seconds": records[t]["latency_seconds"],
                "raw_output_sha256": records[t]["raw_output_sha256"],
            }
            for t in task_ids
        },
    }
    write_json_lf(OUT_DIR / "agentless_r1_evaluation.json", out)
    print("\n=== AGGREGATES (micro) ===")
    for arm in arms:
        m = aggregates[arm]["micro"]
        print(f"{arm:28s} P={m['precision']:.4f} R={m['recall']:.4f} F1={m['f1']:.4f} FNR={m['fnr']:.4f} size={aggregates[arm]['size']['mean']:.2f} (tp={m['tp']} fp={m['fp']} fn={m['fn']})")
    print("\nefficiency:", out["efficiency"])
    print("\nbootstrap (Agentless vs baseline, micro F1 delta):")
    for k, v in bootstrap.items():
        print(f"  {k}: point={v['delta_f1_point']:+.4f} [q025={v['delta_f1_q025']:+.4f}, q975={v['delta_f1_q975']:+.4f}]")
    print("\nwrote:", OUT_DIR / "agentless_r1_evaluation.json")
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-dir", type=str, default="research/competitor-agentless-r1/run",
                   help="directory containing agentless_r1_run_records.jsonl to evaluate")
    return p.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
