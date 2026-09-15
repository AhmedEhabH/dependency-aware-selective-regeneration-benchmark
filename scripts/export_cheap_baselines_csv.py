"""Export cheap-baselines-v1 results to CSV (per-task and aggregate)."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
OUT = _PACKAGE_ROOT / "research" / "cheap-baselines-v1"

raw = json.loads((OUT / "raw_predictions_v1.json").read_text(encoding="utf-8"))
agg = json.loads((OUT / "aggregate_v1.json").read_text(encoding="utf-8"))

per_task_path = OUT / "per_task_metrics_v1.csv"
fields = [
    "case_id", "split", "baseline", "k", "selected_count", "proxy_count",
    "tp", "fp", "fn", "precision", "recall", "f1", "fnr", "full_recall",
    "seed_reason", "build_seconds", "query_seconds",
]
with per_task_path.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for case in raw["cases"]:
        for row in case["results"]:
            w.writerow({k: row.get(k, "") for k in fields})

agg_path = OUT / "aggregate_v1.csv"
agg_rows = []
for group in ("TRAIN", "VALIDATION", "TRAIN_VALIDATION"):
    for baseline in ("random", "bm25", "path_token", "graph", "hybrid"):
        for k in (1, 3, 5, 10):
            m = agg["aggregates"][group][baseline][str(k)]["micro"]
            ma = agg["aggregates"][group][baseline][str(k)]["macro"]
            agg_rows.append(
                {
                    "group": group, "baseline": baseline, "k": k,
                    "micro_precision": m["precision"], "micro_recall": m["recall"],
                    "micro_f1": m["f1"], "micro_fnr": m["fnr"],
                    "micro_tp": m["tp"], "micro_fp": m["fp"], "micro_fn": m["fn"],
                    "macro_precision": ma["precision"], "macro_recall": ma["recall"],
                    "macro_f1": ma["f1"], "macro_fnr": ma["fnr"],
                }
            )
with agg_path.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(agg_rows[0].keys()))
    w.writeheader()
    w.writerows(agg_rows)

print(f"wrote {per_task_path} ({sys.getsizeof('x') and len(raw['cases'])} cases)")
print(f"wrote {agg_path}")
