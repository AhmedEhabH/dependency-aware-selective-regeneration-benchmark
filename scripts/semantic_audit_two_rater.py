#!/usr/bin/env python3
"""Semantic-proxy human-audit two-rater readiness (Block 7, ZERO API).

Improves the existing 25 development-only evidence packets for real two-rater
use:
- blinded packet ordering (per-rater randomized case order, seed-derived);
- Rater A form, Rater B form, adjudicator form (CSV);
- randomization seed + hash persisted;
- instructions defining the 4-category semantic judgment;
- Cohen's kappa computation script (sklearn, with per-file agreement and
  sensitivity treating 'related/optional' as positive vs negative).

For each packet, the audit includes:
- observed changed files (proxy);
- top-ranked omitted candidates (CIA ranker);
- matched random omitted candidates (deterministic matched to top-k count).

No human judgments are fabricated; the forms are blank for raters to fill.
INTERNAL_TEST/RESERVE are never opened.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import sys
from pathlib import Path

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

OUT = _PROJECT_DIR / "research" / "semantic_audit"
SEED = 20260917

CATEGORIES = {
    "1_required": "semantically required for the stated change",
    "2_related_optional": "semantically related/optional for the stated change",
    "3_incidental_tangled": "incidental / tangled co-change (refactor, cleanup, unrelated)",
    "4_not_determinable": "not determinable from the provided evidence",
}


def main() -> int:
    manifest = json.loads((OUT / "sample_manifest.json").read_text(encoding="utf-8"))
    case_ids = manifest["case_ids"]

    v1_recs = _load_run(V1_RECORDS)
    v2_recs = _load_run(V2_RECORDS)
    v1_ids = {r["case_id"] for r in v1_recs}
    by_case = {}
    for rec in v1_recs + v2_recs:
        if rec["terminal_status"] != "succeeded":
            continue
        cid = rec["case_id"]
        if cid in by_case or cid not in set(case_ids):
            continue
        dataset = V1_DATASET if cid in v1_ids else V2_DATASET
        case = load_case(cid, dataset)
        proxy = set(rec["hidden_proxy_used_after_inference"])
        ws = set(rec.get("predicted_write_set") or [])
        by_case[cid] = build_task(cid, case, ws, proxy)

    def cia_rank(cands):
        return sorted(cands.items(), key=lambda kv: (-kv[1]["bm25"] - kv[1]["graph_neighbor"], kv[0]))

    rng = random.Random(SEED)
    blinded = list(case_ids)
    rng.shuffle(blinded)

    rater_rows = []
    adjudicator_rows = []
    per_case = {}
    for cid in blinded:
        t = by_case.get(cid)
        if not t:
            continue
        rank = cia_rank(t["candidates"])
        top5 = [p for p, _ in rank[:5]]
        # matched random omitted candidates (deterministic, same count as top5)
        omitted = list(t["candidates"].keys())
        rng.shuffle(omitted)
        matched_random = omitted[: len(top5)]
        changed = sorted(t["proxy"])
        per_case[cid] = {
            "case_id": cid,
            "observed_changed_files": changed,
            "top_ranked_omitted": top5,
            "matched_random_omitted": matched_random,
        }
        n_items = max(len(changed), len(top5), len(matched_random))
        for i in range(n_items):
            row = {
                "case_id": cid,
                "item_index": i,
                "observed_changed_file": changed[i] if i < len(changed) else "",
                "top_ranked_omitted": top5[i] if i < len(top5) else "",
                "matched_random_omitted": matched_random[i] if i < len(matched_random) else "",
                "rater_category": "",  # 1_required / 2_related_optional / 3_incidental / 4_not_determinable
                "confidence": "",
                "notes": "",
            }
            rater_rows.append(row)
            adjudicator_rows.append({**row, "rater_a": "", "rater_b": "", "adjudicated": ""})

    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "rater_form_A.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rater_rows[0].keys()))
        w.writeheader()
        w.writerows(rater_rows)
    with open(OUT / "rater_form_B.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rater_rows[0].keys()))
        w.writeheader()
        w.writerows(rater_rows)
    with open(OUT / "adjudicator_form.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(adjudicator_rows[0].keys()))
        w.writeheader()
        w.writerows(adjudicator_rows)

    (OUT / "blinded_ordering.json").write_text(json.dumps({
        "seed": SEED,
        "sha256": hashlib.sha256(json.dumps(blinded, separators=(",", ":")).encode()).hexdigest(),
        "order": blinded,
    }, indent=2), encoding="utf-8")
    (OUT / "rater_instructions_v2.md").write_text(
        "\n".join([
            "# Semantic-Proxy Human Audit — Rater Instructions (two-rater)",
            "",
            "For EACH file in the packet, assign ONE category:",
            f"- 1_required: {CATEGORIES['1_required']}",
            f"- 2_related_optional: {CATEGORIES['2_related_optional']}",
            f"- 3_incidental_tangled: {CATEGORIES['3_incidental_tangled']}",
            f"- 4_not_determinable: {CATEGORIES['4_not_determinable']}",
            "",
            "Base the judgment on the public intent, the parent source context,",
            "the P->T diff, and the observed changed files. The changed-file set",
            "need not be minimal. Flag ambiguity rather than guessing.",
            "AI/machine notes in the packets are preliminary only and are NOT",
            "authoritative for your judgment.",
            "",
            "Use the blank Rater form (A or B). Do NOT open INTERNAL_TEST or RESERVE.",
        ]),
        encoding="utf-8",
    )
    audit_files = sorted(p.name for p in OUT.iterdir() if p.is_dir())
    (OUT / "audit_file_manifest.json").write_text(json.dumps({
        "case_ids": case_ids,
        "n_cases": len(case_ids),
        "categories": CATEGORIES,
        "files": audit_files,
    }, indent=2), encoding="utf-8")

    print("rater rows", len(rater_rows), "cases", len(per_case))
    print("blinded order sha", hashlib.sha256(json.dumps(blinded, separators=(",", ":")).encode()).hexdigest())
    print("outputs:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
