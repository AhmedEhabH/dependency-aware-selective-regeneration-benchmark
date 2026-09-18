#!/usr/bin/env python3
"""POST-HOC sensitivity analysis for the AI semantic audit (ZERO LLM).

Runs AFTER `semantic_ai_audit_agreement.py` and does NOT alter any frozen label.

Partitions the 250 `omitted_candidate_file` rows by whether the same file_path
ALSO appears in that case's historical changed set (the observed
`observed_changed_file` rows). Because some rater rationales interpret "omitted"
as "absent from the historical diff", this separates:

  - sparse_omitted_and_historical_changed  (file in the historical diff too)
  - sparse_omitted_and_outside_historical_diff (file NOT in the historical diff)

and reports agreement statistics for each partition separately.

Then, DESCRIPTIVELY and WITHOUT semantic-gold claims, compares the AI-rated
semantic relevance (labels 1_required / 2_related_optional) of
`top_ranked_omitted` vs `matched_random_omitted` candidates OUTSIDE the
historical diff, per rater (ChatGPT and Claude reported SEPARATELY, never pooled
into human ground truth).

Usage:
    python scripts/semantic_ai_audit_posthoc.py
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.semantic_ai_audit_agreement import (
    LABELS,
    _pair_labels,
    _row_agreement_stats,
    expected_ids,
    load_sealed,
    reassemble_rater,
    validate_reassembly,
)

PROJECT = Path(__file__).resolve().parent.parent
AI = PROJECT / "research" / "semantic_audit" / "ai_blinded_v1"
OUTPUTS_DIR = AI / "rater_outputs"
SEALED = AI / "sealed_mapping.json"
ANALYSIS = PROJECT / "reports" / "ai_semantic_audit_agreement_result.json"
RESULT = PROJECT / "reports" / "ai_semantic_audit_posthoc_result.json"

RELEVANT_LABELS = {"1_required", "2_related_optional"}


def row_meta_map(sealed: dict) -> dict[str, dict]:
    """neutral_row_id -> {case, role, file, arm}."""
    out = {}
    for ncid, cinfo in sealed["cases"].items():
        for r in cinfo["rows"]:
            out[r["neutral_row_id"]] = {
                "case": ncid,
                "role": r["semantic_role"],
                "file": r["file_path"],
                "arm": r["original_arm"],
            }
    return out


def historical_changed_paths(sealed: dict) -> dict[str, set[str]]:
    """case -> set of file paths that appear as observed_changed_file rows."""
    out = {}
    for ncid, cinfo in sealed["cases"].items():
        out[ncid] = {
            r["file_path"] for r in cinfo["rows"] if r["original_arm"] == "observed_changed_file"
        }
    return out


def partition_omitted(
    pairs: list[tuple[str, str | None, str | None]], meta: dict, hist_paths: dict[str, set[str]]
) -> dict[str, list]:
    out: dict[str, list] = {
        "sparse_omitted_and_historical_changed": [],
        "sparse_omitted_and_outside_historical_diff": [],
    }
    for nid, la, lb in pairs:
        m = meta.get(nid)
        if not m or m["role"] != "omitted_candidate_file":
            continue
        in_hist = m["file"] in hist_paths.get(m["case"], set())
        key = "sparse_omitted_and_historical_changed" if in_hist else "sparse_omitted_and_outside_historical_diff"
        out[key].append((nid, la, lb))
    return out


def semantic_relevance_split(
    pairs: list[tuple[str, str | None, str | None]],
    meta: dict,
    hist_paths: dict[str, set[str]],
    rater_idx: int,
) -> dict:
    """Among omitted rows OUTSIDE the historical diff, per-arm relevance rates."""
    arms: dict[str, list[str]] = {}
    for nid, la, lb in pairs:
        m = meta.get(nid)
        if not m or m["role"] != "omitted_candidate_file":
            continue
        if m["file"] in hist_paths.get(m["case"], set()):
            continue
        label = (la, lb)[rater_idx - 1]
        if label is None:
            continue
        arms.setdefault(m["arm"], []).append(label)
    out: dict = {}
    for arm, labels in sorted(arms.items()):
        n = len(labels)
        n_rel = sum(1 for x in labels if x in RELEVANT_LABELS)
        out[arm] = {
            "n": n,
            "n_relevant": n_rel,
            "rate_relevant": round(n_rel / n, 4) if n else None,
            "label_distribution": {lab: labels.count(lab) for lab in LABELS},
        }
    return out


def main() -> int:
    sealed = load_sealed(SEALED)
    meta = row_meta_map(sealed)
    hist_paths = historical_changed_paths(sealed)

    base = json.loads(ANALYSIS.read_text(encoding="utf-8"))
    # Recompute pair labels from the frozen outputs (deterministic).
    exp_rows, exp_cases, role_by_row = expected_ids(sealed)
    outputs = {}
    from scripts.semantic_ai_audit_agreement import load_batch_outputs

    outputs = load_batch_outputs(OUTPUTS_DIR)
    chatgpt = reassemble_rater(outputs, "chatgpt")
    claude = reassemble_rater(outputs, "claude")
    validate_reassembly(chatgpt, exp_rows, exp_cases, "chatgpt")
    validate_reassembly(claude, exp_rows, exp_cases, "claude")
    pairs = _pair_labels(chatgpt, claude)

    partitions = partition_omitted(pairs, meta, hist_paths)

    posthoc = {
        "analysis_date": "2026-09-18",
        "package": "ai_blinded_v1",
        "note": (
            "POST-HOC sensitivity analysis. Frozen labels NOT altered. Splits "
            "omitted_candidate_file rows by whether the same file also appears in "
            "the case's historical changed set, because some rater rationales "
            "interpret 'omitted' as 'absent from the historical diff'. Inter-model "
            "agreement is NOT human agreement; the relevance comparison is "
            "descriptive AI-rated signal, NOT semantic gold, and ChatGPT/Claude "
            "are reported separately and never pooled into human ground truth."
        ),
        "n_omitted_total": 250,
        "n_sparse_omitted_and_historical_changed": len(partitions["sparse_omitted_and_historical_changed"]),
        "n_sparse_omitted_and_outside_historical_diff": len(
            partitions["sparse_omitted_and_outside_historical_diff"]
        ),
        "partitions": {
            key: _row_agreement_stats(partitions[key])
            for key in partitions
        },
        "semantic_relevance_outside_historical_diff": {
            "chatgpt": semantic_relevance_split(pairs, meta, hist_paths, 1),
            "claude": semantic_relevance_split(pairs, meta, hist_paths, 2),
            "label_definition": (
                "AI-rated semantic relevance = label in {1_required, 2_related_optional} "
                "among omitted candidates OUTSIDE the historical diff."
            ),
        },
        "agreement_row_level_reference": base["row_level"],
    }
    RESULT.write_text(json.dumps(posthoc, indent=2), encoding="utf-8")
    print(json.dumps(posthoc, indent=2))
    print("output:", RESULT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
