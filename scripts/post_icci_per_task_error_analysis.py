#!/usr/bin/env python3
"""POST-ICCI — Per-task error-analysis table over the 10 held-out tasks.

Builds a single CSV + Markdown table combining, AT THE CORRECT TASK LEVEL:

- task ID (the 10 HELD_OUT_TEST historical djangoCMS changes);
- |U_t| (candidate universe size) and |G_t| (observed change-set proxy size);
- Full-v2: predicted set size, TP/FP/FN, P/R/F1/FNR — micro over the 3 nested
  repetitions (repetitions are nested observations, not independent tasks);
- Sparse-v2: same columns;
- action composition per arm (count of PRESERVE / REGENERATE / VALIDATE /
  HUMAN_REVIEW across the decoded per-cell policies, summed over the 3 reps);
- LocAgent: usable/failure status (valid / timeout / context-length /
  completed-but-empty), predicted file count, and calls/tokens/cost from the
  authoritative per-call ledger.

Source: frozen P1 run records + raw responses, LocAgent P5-C outputs +
ledger, frozen dataset. ZERO API.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PACKAGE_ROOT))
sys.path.insert(0, str(_PACKAGE_ROOT / "src"))

DATASET_DIR = _PACKAGE_ROOT / "benchmark_data" / "real_commit_impact_v1"
P1_METRICS = _PACKAGE_ROOT / "research" / "real-commit-p1-01" / "final_metrics.json"
P1_RECORDS = _PACKAGE_ROOT / "research" / "real-commit-p1-01" / "run_records.jsonl"
P1_RAW = _PACKAGE_ROOT / "research" / "real-commit-p1-01" / "runs" / "raw"
P5C_DIR = _PACKAGE_ROOT / "research" / "locagent-p5b" / "out_c"
TWO_WAY = _PACKAGE_ROOT / "research" / "locagent-p5b" / "locagent_two_way.json"
OUT_DIR = _PACKAGE_ROOT / "research" / "post-icci-zero-api-closure"

ARMS = ("full_v2", "sparse_v2")

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


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def universe_size(case_id: str) -> int:
    p = DATASET_DIR / "scientific" / case_id / "public" / "candidate_universe.json"
    return len(_load_json(p)["records"])


def proxy_size(case_id: str) -> int:
    p = DATASET_DIR / "scientific" / case_id / "hidden" / "observed_change_set_proxy.json"
    return len(_load_json(p)["paths"])


def action_composition(case_id: str, arm: str) -> dict[str, int]:
    """Sum of per-cell action counts over the 3 repetitions for one arm."""
    counts = {"PRESERVE": 0, "REGENERATE": 0, "VALIDATE": 0, "HUMAN_REVIEW": 0}
    for line in P1_RECORDS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec["case_id"] != case_id or rec["arm"] != arm:
            continue
        raw_path = P1_RAW / f"{rec['run_id']}.txt"
        if not raw_path.exists():
            continue
        parsed = json.loads(raw_path.read_text(encoding="utf-8"))
        choices = parsed.get("choices") or []
        choice = choices[0] if choices else {}
        content = (choice.get("message") or {}).get("content") or ""
        if not content.strip():
            continue
        payload = json.loads(content)
        if not isinstance(payload, dict):
            continue
        decisions = payload.get("decisions")
        if not isinstance(decisions, list):
            continue
        for item in decisions:
            action = str(item.get("action") or "").strip().upper()
            if action in counts:
                counts[action] += 1
    return counts


def locagent_status(case_id: str, two_way: dict[str, Any]) -> str:
    taxonomy = two_way["failure_taxonomy"]
    if case_id in taxonomy["timeout"]:
        return "empty:timeout"
    if case_id in taxonomy["context_length_badrequest"]:
        return "empty:context-length"
    if case_id in taxonomy["completed_but_empty"]:
        return "empty:completed-but-empty"
    return "usable"


def main() -> int:
    p1 = _load_json(P1_METRICS)
    two_way = _load_json(TWO_WAY)
    loc_per_task = two_way["per_task"]
    eff = two_way["efficiency"]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for cid in HELD_OUT:
        tl = p1["task_level"][cid]
        row: dict[str, Any] = {
            "task_id": cid,
            "|U_t|": universe_size(cid),
            "|G_t|": proxy_size(cid),
        }
        for arm in ARMS:
            m = tl[f"{arm}_micro"]
            row[f"{arm}_predicted"] = m["selected"]
            row[f"{arm}_tp"] = m["tp"]
            row[f"{arm}_fp"] = m["fp"]
            row[f"{arm}_fn"] = m["fn"]
            row[f"{arm}_P"] = round(m["precision"], 4)
            row[f"{arm}_R"] = round(m["recall"], 4)
            row[f"{arm}_F1"] = round(m["f1"], 4)
            row[f"{arm}_FNR"] = round(m["fnr"], 4)
            ac = action_composition(cid, arm)
            row[f"{arm}_PRESERVE"] = ac["PRESERVE"]
            row[f"{arm}_REGENERATE"] = ac["REGENERATE"]
            row[f"{arm}_VALIDATE"] = ac["VALIDATE"]
            row[f"{arm}_HUMAN_REVIEW"] = ac["HUMAN_REVIEW"]
        row["LocAgent_status"] = locagent_status(cid, two_way)
        row["LocAgent_predicted"] = loc_per_task[cid]["predicted_count"]
        row["LocAgent_calls"] = eff[cid]["model_calls"]
        row["LocAgent_total_tokens"] = eff[cid]["total_tokens"]
        row["LocAgent_cost_usd"] = round(eff[cid]["cost_usd"], 6)
        rows.append(row)

    csv_path = OUT_DIR / "per_task_error_analysis.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # Markdown table (compact; both arms + LocAgent status).
    md: list[str] = []
    hdr = ("| task | |U| | |G| | Fv-pred | Fv-TP | Fv-FP | Fv-FN | Fv-F1 | "
           "Sv-pred | Sv-TP | Sv-FP | Sv-FN | Sv-F1 | LocAgent |")
    md.append(hdr)
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for r in rows:
        md.append(
            f"| {r['task_id'].replace('djangocms-rc-', '')} "
            f"| {r['|U_t|']} | {r['|G_t|']} "
            f"| {r['full_v2_predicted']} | {r['full_v2_tp']} | {r['full_v2_fp']} | {r['full_v2_fn']} "
            f"| {r['full_v2_F1']:.3f} "
            f"| {r['sparse_v2_predicted']} | {r['sparse_v2_tp']} | {r['sparse_v2_fp']} | {r['sparse_v2_fn']} "
            f"| {r['sparse_v2_F1']:.3f} "
            f"| {r['LocAgent_status']} |"
        )
    md_path = OUT_DIR / "per_task_error_analysis.md"
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    print("=== PER-TASK ERROR-ANALYSIS TABLE (10 held-out tasks; ZERO API) ===")
    for r in rows:
        print(
            f"{r['task_id']}: |U|={r['|U_t|']} |G|={r['|G_t|']} "
            f"sparse pred={r['sparse_v2_predicted']} TP={r['sparse_v2_tp']} FP={r['sparse_v2_fp']} "
            f"FN={r['sparse_v2_fn']} F1={r['sparse_v2_F1']:.3f} "
            f"LocAgent={r['LocAgent_status']} calls={r['LocAgent_calls']}"
        )
    print(f"Wrote: {csv_path}")
    print(f"Wrote: {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
