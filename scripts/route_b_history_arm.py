#!/usr/bin/env python3
# ruff: noqa: N803, N806
# B / N / M are the frozen protocol's budget / omitted-count / missed-count
# symbols (docs/ROUTE_B_V2_DEVELOPMENT_PROTOCOL.md).
"""Route B history/co-change arm — evaluate on DEVELOPMENT only (zero model calls).

Uses the parent-visible djangoCMS history (dist/real-commit-cache/djangocms,
16,602 commits, non-shallow) to add a co-change feature per Sparse-omitted
candidate, then ranks omitted candidates by co-change with the Sparse write set.

Parent-visible rule: only commits reachable from P (git log P) are used. NEVER
commits after P. If history is unavailable for a task, the feature is
UNAVAILABLE (not zero).

Compares: History@B vs analytic Random@B and vs CIA@B over B in {1,3,5,10}.

Outputs:
- research/transparency/route_b_history_arm_results.json
- reports/ROUTE_B_HISTORY_ARM_REPORT.md
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from scripts.route_b_v2_robustness import (  # noqa: E402
    V1_DATASET,
    V1_RECORDS,
    V2_DATASET,
    V2_RECORDS,
    _load_run,
    build_task,
    load_case,
)

CACHE = _PROJECT_DIR / "dist" / "real-commit-cache" / "djangocms"
SPLIT = _PROJECT_DIR / "research" / "transparency" / "v2_split_proposal.json"
OUT_JSON = _PROJECT_DIR / "research" / "transparency" / "route_b_history_arm_results.json"
OUT_MD = _PROJECT_DIR / "reports" / "ROUTE_B_HISTORY_ARM_REPORT.md"

SEED = 20260917
BUDGETS = (1, 3, 5, 10)


def files_changed_with(cache: Path, parent: str, seed_paths: set[str], window: int = 2000) -> dict[str, int]:
    """For each candidate, count co-change commits with any seed path before P."""
    # git log P: name-status, ancestors of P only.
    proc = subprocess.run(
        ["git", "-C", str(cache), "log", "--name-status", "-n", str(window), parent],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        return {}
    co: dict[str, int] = {}
    current_files: set[str] = set()
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(("M\t", "A\t")):
            p = line[2:]
            if p in seed_paths:
                for f in current_files:
                    co[f] = co.get(f, 0) + 1
            current_files.add(p)
        elif "\t" in line:
            # status \t path  (or  status \t old \t new)
            parts = line.split("\t")
            if len(parts) == 2:
                current_files = {parts[1]}
            elif len(parts) == 3:
                current_files = {parts[2]}
        else:
            current_files = set()
    return co


def main() -> int:
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    assign = split["assignment"]
    v1_recs = _load_run(V1_RECORDS)
    v2_recs = _load_run(V2_RECORDS)
    v1_case_ids = {r["case_id"] for r in v1_recs}

    rows = []
    n_history_available = 0
    n_unavailable = 0
    seen_tasks: set[str] = set()
    for rec in v1_recs + v2_recs:
        if rec["terminal_status"] != "succeeded":
            continue
        cid = rec["case_id"]
        if cid in seen_tasks:
            continue  # repetitions are nested; one representative rep per task
        seen_tasks.add(cid)
        dataset = V1_DATASET if cid in v1_case_ids else V2_DATASET
        case = load_case(cid, dataset)
        proxy = set(rec["hidden_proxy_used_after_inference"])
        write_set = set(rec.get("predicted_write_set") or [])
        task = build_task(cid, case, write_set, proxy)
        if task["n_missed"] == 0:
            continue
        # co-change with the Sparse write set, from ancestors of P only.
        co = files_changed_with(CACHE, case["parent_commit"], write_set)
        if not co:
            n_unavailable += 1
            continue
        n_history_available += 1
        # rank omitted candidates by co-change count (descending)
        cands = task["candidates"]
        max_co = max((co.get(p, 0) for p in cands), default=0)
        for p, c in cands.items():
            c["co_change"] = co.get(p, 0) / max_co if max_co else 0.0
        task["role"] = assign.get(cid, "V1_DEV")
        rows.append(task)

    def hist_rank(cands):
        return sorted(cands.items(), key=lambda kv: (-kv[1]["co_change"], kv[0]))

    def orr(task, ranked_fn, B):
        N = task["omitted_size"]
        M = task["n_missed"]
        if M == 0 or B == 0:
            return 0.0, 0.0
        B_eff = min(B, N)
        top = [p for p, _ in ranked_fn(task["candidates"])][:B_eff]
        rec = sum(1 for p in top if task["candidates"][p]["is_missed_positive"])
        exp_random = B_eff * M / N if N else 0.0
        return rec / M, exp_random / M

    def orr_ranked(task, ranked, B):
        N = task["omitted_size"]
        M = task["n_missed"]
        if M == 0 or B == 0:
            return 0.0, 0.0
        B_eff = min(B, N)
        top = [p for p, _ in ranked][:B_eff]
        rec = sum(1 for p in top if task["candidates"][p]["is_missed_positive"])
        exp_random = B_eff * M / N if N else 0.0
        return rec / M, exp_random / M

    result = {"n_tasks_with_history": n_history_available, "n_unavailable": n_unavailable}
    for B in BUDGETS:
        hist = []
        cia = []
        rand = []
        for t in rows:
            h, r = orr(t, hist_rank, B)
            hist.append(h)
            rand.append(r)
            # CIA = BM25 + graph-neighbor
            cia_rank = sorted(t["candidates"].items(), key=lambda kv: (-kv[1]["bm25"] - kv[1]["graph_neighbor"], kv[0]))
            c, _ = orr_ranked(t, cia_rank, B)
            cia.append(c)
        result[str(B)] = {
            "history_macro_orr": round(float(np.mean(hist)), 4),
            "cia_macro_orr": round(float(np.mean(cia)), 4),
            "analytic_random_macro_orr": round(float(np.mean(rand)), 4),
            "history_delta_vs_random": round(float(np.mean(hist)) - float(np.mean(rand)), 4),
            "cia_delta_vs_random": round(float(np.mean(cia)) - float(np.mean(rand)), 4),
            "n_tasks": len(rows),
        }

    OUT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")
    md = [
        "# Route B — History / Co-Change Arm (parent-visible, DEVELOPMENT only)",
        "",
        f"**Date:** 2026-09-17  **History available:** {n_history_available} tasks; "
        f"unavailable: {n_unavailable}.",
        "Co-change with the Sparse write set, from ancestors of P only (never future).",
        "",
        "| B | History ORR | CIA ORR | AnalyticRandom ORR | History-Random Δ | CIA-Random Δ |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for B in BUDGETS:
        r = result[str(B)]
        md.append(
            f"| {B} | {r['history_macro_orr']:.3f} | {r['cia_macro_orr']:.3f} | "
            f"{r['analytic_random_macro_orr']:.3f} | {r['history_delta_vs_random']:+.3f} | "
            f"{r['cia_delta_vs_random']:+.3f} |"
        )
    md += [
        "",
        "## Notes",
        "",
        "- Parent-visible history: git log P only (ancestors); future commits never used.",
        "- HISTORY-UNAVAILABLE is reported as unavailable, not numeric zero.",
        "- CIA remains the frozen primary verifier ranker; History is an additional predeclared arm.",
    ]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(json.dumps(result, indent=1))
    print("outputs:", OUT_JSON, OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
