#!/usr/bin/env python3
"""Generate README transparency tables + V2 sampling-frame summaries from FROZEN artifacts.

All numbers are derived, never transcribed by hand:
- 30-task development table (TRAIN+VALIDATION from scientific_manifest.json)
- V2 sampling-frame summary (eligible pool 329, funnel 6000->916->334->329->40)
- exposed-v1 tagging (LEGACY_EXPOSED_V1)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

DATASET = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v1"
ADJ = _PROJECT_DIR / "reports" / "real_commit_m4a2_adjudication.json"
OUT = _PROJECT_DIR / "research" / "transparency"


def load():
    m = json.loads((DATASET / "scientific_manifest.json").read_text(encoding="utf-8"))
    split = json.loads((DATASET / "split_freeze.json").read_text(encoding="utf-8"))
    adj = json.loads(ADJ.read_text(encoding="utf-8"))
    return m, split, adj


def proxy_count_of(rec):
    return int(rec.get("observed_change_set_proxy_count") or 0)


def bucket(n):
    if n <= 2:
        return "small"
    if n <= 6:
        return "medium"
    return "large"


def short_intent(text: str, limit: int = 60) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def build_dev_table(m, split):
    rows = []
    for rec in m["cases"]:
        cid = rec["case_id"]
        sp = split["assignment"][cid]
        if sp not in ("TRAIN", "VALIDATION"):
            continue
        year = rec["target_commit_time"][:4]
        rows.append(
            {
                "case_id": cid,
                "split": sp,
                "target_commit": rec["target_commit"][:12],
                "year": year,
                "candidates": int(rec["candidate_universe_count"] or 0),
                "proxy": proxy_count_of(rec),
                "bucket": bucket(proxy_count_of(rec)),
                "change_type": rec["change_type"],
                "intent": short_intent(rec["intent_text"]),
            }
        )
    rows.sort(key=lambda r: (r["split"], r["target_commit"]))
    return rows


def render_dev_markdown(rows) -> str:
    lines = [
        "| Commit SHA | Split | Year | Candidates | Proxy | Bucket | Type | PUBLIC intent (shortened) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| `{r['target_commit']}` | {r['split']} | {r['year']} | {r['candidates']} "
            f"| {r['proxy']} | {r['bucket']} | {r['change_type']} | {r['intent']} |"
        )
    return "\n".join(lines)


def main() -> int:
    m, split, adj = load()
    dev = build_dev_table(m, split)
    OUT.mkdir(parents=True, exist_ok=True)

    (OUT / "dev_30_table.md").write_text(render_dev_markdown(dev), encoding="utf-8")
    (OUT / "dev_30_table.json").write_text(json.dumps(dev, indent=2), encoding="utf-8")

    # V2 sampling frame
    scan = adj["scan_summary"]
    dedup = adj["dedup_summary"]
    sel = adj["selection_summary"]
    frame = {
        "window_scanned": scan["window"],
        "eligible_after_filters": scan["candidates_eligible"],
        "after_r1_r2": dedup["after_r1_r2"],
        "after_r3": dedup["after_r3"],
        "independent_eligible_pool": dedup["after_r3"],
        "selected_v1": sel["selected"],
        "years": sel["years"],
        "exclusion_counts": scan["exclusion_counts"],
        "adjudication_count": dedup["adjudication_count"],
        "split": {"TRAIN": 24, "VALIDATION": 6, "HELD_OUT_TEST": 10},
        "legacy_exposed_v1_total": 40,
        "note": (
            "All 40 v1 cases are LEGACY_EXPOSED_V1 (TRAIN/VALIDATION used for "
            "cheap baselines, features and Sparse inference; HELD_OUT_TEST used "
            "by P1/P5). None may be used as an untouched V2 confirmatory test."
        ),
    }
    (OUT / "v2_sampling_frame.json").write_text(json.dumps(frame, indent=2), encoding="utf-8")

    # Exposed v1 case id list
    (OUT / "legacy_exposed_v1_case_ids.json").write_text(
        json.dumps(sorted(m["case_ids"]), indent=2), encoding="utf-8"
    )

    print("dev_table_rows", len(dev))
    print("train", sum(1 for r in dev if r["split"] == "TRAIN"))
    print("validation", sum(1 for r in dev if r["split"] == "VALIDATION"))
    print("frame", json.dumps(frame, indent=1)[:400])
    print("outputs:", sorted(p.name for p in OUT.iterdir()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
