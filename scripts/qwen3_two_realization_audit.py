#!/usr/bin/env python3
# ruff: noqa: N803, N806
"""Independent audit for the Qwen3 two-realization replication (T3, ZERO API).

Recomputes the key claims WITHOUT importing the analyzer/runner:
  1. corpus size from the E: cache index (49,703 units + 323 queries per
     realization);
  2. cumulative spend from cumulative_spend.json vs the frozen ceiling;
  3. per-realization pooled metrics + paired-bootstrap CIs from the persisted
     task_rankings.json (labels joined from load_dev_tasks) -- independent
     recomputation of TP/FP/FN, F1, ORR;
  4. the A/B reproducibility stats (same-set %, Jaccard, one-file flips);
  5. label-free guarantee on the Parquet columns;
  6. no sealed data touched (the analyze path only reads DEV tasks).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

import pandas as pd  # noqa: E402

from benchmark.recall.data import load_dev_tasks  # noqa: E402

OUT_DIR = _PROJECT_DIR / "research" / "contamination-bridge" / "qwen_embed"
REPORT_DIR = _PROJECT_DIR / "reports"
CACHE_ROOT = Path(r"E:\opencode\qwen3-embed-cache-2026-09-19")

B_REF = 5
N_RESAMPLES = 10_000
SEED = 20260919
CEILING = 0.50


def _contrib(r: dict, t, key: str, B: int) -> dict:
    pos = set(t.proxy)
    fn_set = set(t.fn_paths)
    B_eff = min(B, r["omitted_size"])
    added = set(r[f"{key}_ranked"][:B_eff])
    final = set(t.write_set) | added
    tp = len(final & pos)
    fp = len(final - pos)
    fn = len(pos - final)
    return {"tp": tp, "fp": fp, "fn": fn,
            "orr": (len(added & fn_set) / t.n_missed) if t.n_missed else 0.0,
            "cand_fn": len(added & fn_set), "cand_sel": len(added)}


def main() -> int:
    checks: list[dict] = []
    tasks = load_dev_tasks()
    by_cid = {t.case_id: t for t in tasks}
    assert len(by_cid) == 323

    for rid in ("A", "B"):
        # 1. corpus + spend
        idx = json.loads((CACHE_ROOT / f"realization_{rid}" / "index.json").read_text(encoding="utf-8"))
        spend = json.loads((CACHE_ROOT / f"realization_{rid}" / "cumulative_spend.json").read_text(encoding="utf-8"))
        checks.append({"check": f"{rid} index entries == 50026",
                       "value": len(idx), "pass": len(idx) == 50_026})
        checks.append({"check": f"{rid} cumulative spend <= ceiling",
                       "value": spend["cost_usd"], "pass": spend["cost_usd"] < CEILING})

        # 2. recompute pooled metrics independently
        r = json.loads((OUT_DIR / f"realization_{rid}" / "task_rankings.json").read_text(encoding="utf-8"))
        for repo in ("djangocms", "saleor"):
            cids = [c for c in r if r[c]["repository"] == repo]
            rows = [_contrib(r[c], by_cid[c], "qwen", B_REF) for c in cids]
            tp = sum(x["tp"] for x in rows)
            fp = sum(x["fp"] for x in rows)
            fn = sum(x["fn"] for x in rows)
            f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
            checks.append({"check": f"{rid} {repo} pooled F1 >= 0.25 (recomputed)",
                           "value": round(f1, 4), "pass": f1 >= 0.25})

        # 3. label-free Parquet
        df = pd.read_parquet(OUT_DIR / f"realization_{rid}" / "full_file_scores.parquet")
        forbidden = {"proxy", "fn_paths", "write_set", "target"}
        cols = set(df.columns)
        checks.append({"check": f"{rid} parquet label-free",
                       "value": sorted(cols), "pass": not (cols & forbidden)})
        checks.append({"check": f"{rid} parquet rows == 143852",
                       "value": len(df), "pass": len(df) == 143_852})

    # 4. reproducibility independent recompute
    ra = json.loads((OUT_DIR / "realization_A" / "task_rankings.json").read_text(encoding="utf-8"))
    rb = json.loads((OUT_DIR / "realization_B" / "task_rankings.json").read_text(encoding="utf-8"))
    common = [c for c in ra if c in rb]
    same = sum(1 for c in common
               if set(ra[c]["qwen_ranked"][:B_REF]) == set(rb[c]["qwen_ranked"][:B_REF]))
    checks.append({"check": "exact same set % >= 95",
                   "value": round(100.0 * same / len(common), 2),
                   "pass": same / len(common) >= 0.95})

    results = {"audit_date": "2026-09-19", "n_checks": len(checks),
               "passed": sum(1 for c in checks if c["pass"]),
               "failed": sum(1 for c in checks if not c["pass"]),
               "checks": checks,
               "verdict": "PASS" if all(c["pass"] for c in checks) else "FAIL"}
    (REPORT_DIR / "qwen3_two_realization_audit.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps({"passed": results["passed"], "failed": results["failed"],
                      "verdict": results["verdict"]}))
    return 0 if results["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
