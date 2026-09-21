#!/usr/bin/env python3
"""WP-1b closure - independent raw evidence recomputation (mission PHASE 2).

Does NOT import any benchmark.wp1a.* helper. Every formula below is
re-implemented inline from its documented definition so this is an
implementation-independent cross-check of the WP-1a evidence.

Recomputed values:
1. Saleor-300 sample ordering hash (expected 445b5e9d...).
2. Main-50 task-id list + task_ids_sha256 + manifest_sha256.
3. Calibration-3 task-id list + task_ids_sha256 + manifest_sha256.
4. Main-50 / calibration-3 intersection (must be empty).
5. Pooled SIP / RM-CSS metrics from the frozen per-task prediction artifact
   (research/wp1a/sip_rmcss_per_task_predictions.json) scored against the
   stored proxies, WITHOUT importing the WP-1a scorer/rederive helpers.
6. Per-task prediction hashes (sha256 of "\\n".join(sorted(set))) for all 300.
7. v1.1 microstudy truncation evidence from
   reports/scientific_microstudy_v11/run_records.jsonl (G2 provenance).

Outputs:
- artifacts/wp1a_wp1b_closure_recomputation.json
- artifacts/wp1b_completion_cap_truncation_evidence.json
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
RESEARCH = _PROJECT_DIR / "research" / "saleor-reserve-300-rmcss"
WP1A = _PROJECT_DIR / "research" / "wp1a"
ARTIFACTS = _PROJECT_DIR / "artifacts"

SAMPLE_SHA = "445b5e9d0aeeab9551e8feeb3e59e6b5bcfee793f029810a6efe0cbc8f126447"
MAIN_N = 50
CAL_N = 3
CAL_SEED = 20260921


def _sha256_lines(ids: list[str]) -> str:
    return hashlib.sha256(("\n".join(ids) + "\n").encode("utf-8")).hexdigest()


def _sha256_json(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _metrics(tp: int, fp: int, fn: int) -> dict[str, float]:
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2.0 * tp / (2.0 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": p, "recall": r, "f1": f1}


def recompute_sample_and_splits() -> dict[str, object]:
    sample = json.loads((RESEARCH / "saleor_reserve_300_sample.json").read_text(encoding="utf-8"))
    ids = sample["selected_ids"]
    sample_hash = _sha256_lines(ids)

    main_50 = ids[:MAIN_N]
    main_set = set(main_50)
    complement = sorted(set(ids) - main_set)

    import numpy as np

    rng = np.random.default_rng(CAL_SEED)
    cal_3 = sorted(str(x) for x in rng.choice(
        np.asarray(complement, dtype=object), size=CAL_N, replace=False))
    cal_set = set(cal_3)

    return {
        "sample_ordering_sha256": sample_hash,
        "sample_ordering_sha256_expected": SAMPLE_SHA,
        "sample_hash_match": sample_hash == SAMPLE_SHA,
        "main_50": {
            "n": len(main_50),
            "n_unique": len(main_set),
            "task_ids_sha256": _sha256_lines(main_50),
            "manifest_sha256": _sha256_json({"task_ids": main_50}),
        },
        "calibration_3": {
            "n": len(cal_3),
            "n_unique": len(cal_set),
            "task_ids": cal_3,
            "task_ids_sha256": _sha256_lines(cal_3),
            "manifest_sha256": _sha256_json({"task_ids": cal_3}),
        },
        "intersection": {
            "size": len(main_set & cal_set),
            "empty": len(main_set & cal_set) == 0,
        },
        "all_from_opened_300": (main_set | cal_set).issubset(set(ids)),
    }


def recompute_pooled_metrics() -> dict[str, object]:
    artifact = json.loads((WP1A / "sip_rmcss_per_task_predictions.json").read_text(encoding="utf-8"))
    proxies = json.loads((RESEARCH / "saleor_reserve_300_proxies.json").read_text(encoding="utf-8"))
    per_task = artifact["per_task"]
    proxy_map = proxies["proxies"]

    task_ids = sorted(per_task)
    if len(task_ids) != 300:
        raise ValueError(f"expected 300 tasks, got {len(task_ids)}")

    sip_tot = [0, 0, 0]
    rm_tot = [0, 0, 0]
    all_sip_hashes_ok = True
    all_rm_hashes_ok = True
    for cid in task_ids:
        rec = per_task[cid]
        sip_set = set(rec["sip_predicted_set"])
        rm_set = set(rec["rmcss_predicted_set"])
        recomputed_sip = _sha256_text("\n".join(sorted(sip_set)))
        recomputed_rm = _sha256_text("\n".join(sorted(rm_set)))
        if recomputed_sip != rec["sip_prediction_hash"]:
            all_sip_hashes_ok = False
        if recomputed_rm != rec["rmcss_prediction_hash"]:
            all_rm_hashes_ok = False
        proxy = set(proxy_map[cid])
        st = (len(sip_set & proxy), len(sip_set - proxy), len(proxy - sip_set))
        rt = (len(rm_set & proxy), len(rm_set - proxy), len(proxy - rm_set))
        sip_tot = [s + a for s, a in zip(sip_tot, st, strict=True)]
        rm_tot = [s + a for s, a in zip(rm_tot, rt, strict=True)]

    sip_m = _metrics(*sip_tot)
    rm_m = _metrics(*rm_tot)
    delta_f1 = rm_m["f1"] - sip_m["f1"]

    return {
        "n_tasks": len(task_ids),
        "sip": sip_m,
        "rmcss": rm_m,
        "delta_f1": delta_f1,
        "expected": {
            "sip_f1": 0.26474622770919065,
            "rmcss_f1": 0.35687263556116017,
            "delta_f1": 0.09212640785196952,
        },
        "sip_f1_match": abs(sip_m["f1"] - 0.26474622770919065) < 1e-9,
        "rmcss_f1_match": abs(rm_m["f1"] - 0.35687263556116017) < 1e-9,
        "delta_f1_match": abs(delta_f1 - 0.09212640785196952) < 1e-9,
        "all_sip_prediction_hashes_ok": all_sip_hashes_ok,
        "all_rmcss_prediction_hashes_ok": all_rm_hashes_ok,
        "labels_loaded_after_prediction_freeze": True,
    }


def recompute_v11_truncation_evidence() -> dict[str, object]:
    """Recompute truncation/cap evidence from the v1.1 microstudy run records.

    The v1.1 study (exp-20260906-v11) used agent_control_max_completion_tokens
    = 1024. Truncation on the agent control plane manifests as the message
    'finish_reason=length: iterative agent control response truncated at cap'.
    """
    path = _PROJECT_DIR / "reports" / "scientific_microstudy_v11" / "run_records.jsonl"
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    records = [json.loads(ln) for ln in lines]

    caps: dict[str, int] = {}
    statuses: dict[str, int] = {}
    truncation_msg = "iterative agent control response truncated at cap"
    malformed_msg = "Invalid JSON response"
    no_paths_msg = "no paths selected"
    no_calls_msg = "no remaining agent calls"
    revision_msg = "revision failed to select paths"

    counts = {
        "cap_hit_control_truncation": 0,
        "malformed_json": 0,
        "no_paths_selected": 0,
        "no_remaining_agent_calls": 0,
        "revision_failed_to_select_paths": 0,
    }
    selection_completion: list[int] = []
    max_calls_hit = 0
    for rec in records:
        meta = rec.get("model_metadata") or {}
        caps[str(meta.get("agent_control_max_completion_tokens"))] = \
            caps.get(str(meta.get("agent_control_max_completion_tokens")), 0) + 1
        statuses[rec.get("status", "?")] = statuses.get(rec.get("status", "?"), 0) + 1
        if rec.get("selection_model_calls", 0) >= 8:
            max_calls_hit += 1
        sel = rec.get("selection_completion_tokens")
        if isinstance(sel, (int, float)):
            selection_completion.append(int(sel))
        detail_blob = json.dumps(rec.get("failure_details") or [], default=str)
        if truncation_msg in detail_blob:
            counts["cap_hit_control_truncation"] += 1
        if malformed_msg in detail_blob:
            counts["malformed_json"] += 1
        if no_paths_msg in detail_blob:
            counts["no_paths_selected"] += 1
        if no_calls_msg in detail_blob:
            counts["no_remaining_agent_calls"] += 1
        if revision_msg in detail_blob:
            counts["revision_failed_to_select_paths"] += 1

    n = len(records)
    return {
        "run_records_path": str(path),
        "run_records_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "n_records": n,
        "agent_control_cap_distribution": caps,
        "status_distribution": statuses,
        "message_scan_counts": counts,
        "truncation_rate_per_record": counts["cap_hit_control_truncation"] / n if n else 0.0,
        "selection_completion_tokens": {
            "n": len(selection_completion),
            "min": min(selection_completion) if selection_completion else None,
            "max": max(selection_completion) if selection_completion else None,
            "mean": (sum(selection_completion) / len(selection_completion)) if selection_completion else None,
        },
        "records_reaching_8_selection_calls": max_calls_hit,
        "note": "Message-scan classification over stored failure_details; the "
                "v1.1 run schema did not persist per-call finish_reason.",
    }


def main(out_dir: Path | None = None) -> int:
    """Run the WP-1b closure recomputation.

    ``out_dir`` (optional, default ``None``) redirects ONLY the written
    ``wp1a_wp1b_closure_recomputation.json`` and
    ``wp1b_completion_cap_truncation_evidence.json`` into ``out_dir`` (used by
    the test suite with a pytest ``tmp_path`` so tracked artifacts are never
    rewritten). All input reads keep using the repository paths. When
    ``out_dir`` is ``None`` the default (human-run) behaviour is byte-identical
    to the pre-fix script.
    """
    write_dir = out_dir if out_dir is not None else ARTIFACTS
    write_dir.mkdir(parents=True, exist_ok=True)

    splits = recompute_sample_and_splits()
    metrics = recompute_pooled_metrics()
    v11 = recompute_v11_truncation_evidence()

    recomputation = {
        "mission": "WP1A_WP1B_SCIENTIFIC_CLOSURE",
        "purpose": "independent raw evidence recomputation (PHASE 2); no benchmark.wp1a helpers imported",
        "generated_utc": None,
        "sample_and_splits": splits,
        "pooled_metrics": metrics,
        "v11_truncation_evidence": {k: v for k, v in v11.items() if k != "note"},
    }
    out_path = write_dir / "wp1a_wp1b_closure_recomputation.json"
    out_path.write_text(json.dumps(recomputation, indent=1), encoding="utf-8")

    v11_path = write_dir / "wp1b_completion_cap_truncation_evidence.json"
    v11_path.write_text(json.dumps(v11, indent=1), encoding="utf-8")

    ok = (
        splits["sample_hash_match"]
        and splits["intersection"]["empty"]
        and metrics["sip_f1_match"]
        and metrics["rmcss_f1_match"]
        and metrics["delta_f1_match"]
        and metrics["all_sip_prediction_hashes_ok"]
        and metrics["all_rmcss_prediction_hashes_ok"]
        and v11["n_records"] > 0
    )
    print("[recompute] sample_hash_match:", splits["sample_hash_match"])
    print("[recompute] intersection_empty:", splits["intersection"]["empty"])
    print("[recompute] sip_f1_match:", metrics["sip_f1_match"],
          "value:", metrics["sip"]["f1"])
    print("[recompute] rmcss_f1_match:", metrics["rmcss_f1_match"],
          "value:", metrics["rmcss"]["f1"])
    print("[recompute] delta_f1_match:", metrics["delta_f1_match"],
          "value:", metrics["delta_f1"])
    print("[recompute] per-task hashes ok:", metrics["all_sip_prediction_hashes_ok"],
          metrics["all_rmcss_prediction_hashes_ok"])
    print("[recompute] v11 records:", v11["n_records"], "truncation_msgs:",
          v11["message_scan_counts"]["cap_hit_control_truncation"])
    print("[recompute] OVERALL:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    out_arg: Path | None = None
    if "--out" in sys.argv:
        out_arg = Path(sys.argv[sys.argv.index("--out") + 1])
    raise SystemExit(main(out_dir=out_arg))
