#!/usr/bin/env python3
"""Prepare semantic-proxy audit evidence packets (DEVELOPMENT-only sample).

Deterministic, ZERO API, no LLM. Stratified sample of 25 V2 DEV_TRAIN cases
(proxy-size bucket x year strata; seed 20260916). Each packet contains the
public intent, candidate-universe metadata, graph edges, and the P->T diff
(name-status; patch available only if the parent is in the cache).

FORBIDDEN: V2 INTERNAL_TEST, RESERVE, HELD_OUT_TEST.
Outputs under research/semantic_audit/.
"""

from __future__ import annotations

import json
import random
import subprocess
import sys
from collections import Counter
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))


V2_DATASET = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_v2"
SPLIT = _PROJECT_DIR / "research" / "transparency" / "v2_split_proposal.json"
OUT = _PROJECT_DIR / "research" / "semantic_audit"
CACHE = _PROJECT_DIR / "dist" / "real-commit-cache" / "djangocms"
SEED = 20260916
SAMPLE_N = 25

FORM_FIELDS = (
    "case_id",
    "file",
    "q1_semantically_necessary",
    "q2_evidence_impacted_unchanged",
    "q3_incidental_refactor",
    "evidence_refs",
    "reviewer_id",
    "confidence",
    "notes",
)


def _bucket(n: int) -> str:
    if n <= 2:
        return "small"
    if n <= 6:
        return "medium"
    return "large"


def main() -> int:
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    assignment = split["assignment"]
    dev_train = sorted(cid for cid, role in assignment.items() if role == "DEV_TRAIN")

    # Stratified sample by proxy-size bucket (deterministic).
    meta = {}
    for cid in dev_train:
        case_dir = V2_DATASET / "scientific" / cid
        m = json.loads((case_dir / "case_manifest.json").read_text(encoding="utf-8"))
        proxy = int(m["record"].get("observed_change_set_proxy_count") or 0)
        meta[cid] = {
            "bucket": _bucket(proxy),
            "proxy_count": proxy,
            "target": m["record"]["target_commit"],
            "parent": m["record"]["parent_commit"],
        }
    by_bucket = {"small": [], "medium": [], "large": []}
    for cid in dev_train:
        by_bucket[meta[cid]["bucket"]].append(cid)
    rng = random.Random(SEED)
    sampled: list[str] = []
    buckets = list(by_bucket.keys())
    while len(sampled) < SAMPLE_N:
        for b in buckets:
            if len(sampled) >= SAMPLE_N:
                break
            pool = by_bucket[b]
            rng.shuffle(pool)
            if pool:
                sampled.append(pool.pop())
    sampled.sort()

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "adjudication_schema.json").write_text(
        json.dumps({
            "schema_version": "semantic-proxy-adjudication-v1",
            "per_file": {
                "q1_semantically_necessary": "bool|ambiguous",
                "q2_evidence_impacted_unchanged": "bool|ambiguous",
                "q3_incidental_refactor": "bool|ambiguous",
                "evidence_refs": "list[str]",
                "confidence": "0..1",
                "notes": "str",
            },
            "per_case": {"summary": "str", "flagged_misses": "list[str]"},
            "human_only": True,
        }, indent=2),
        encoding="utf-8",
    )
    (OUT / "reviewer_instructions.md").write_text(
        "\n".join([
            "# Reviewer Instructions",
            "",
            "- For each changed production file, answer the three questions.",
            "- Focus on the STATED change; the changed-file set need not be minimal.",
            "- Flag ambiguity rather than guessing.",
            "- Question 2 asks whether a semantically impacted but UNCHANGED production",
            "  file is evident (a potential true omission the proxy would miss).",
            "- Machine notes (if present) are preliminary only, never authoritative.",
        ]),
        encoding="utf-8",
    )

    rows = [list(FORM_FIELDS)]
    packets = []
    held_test = set(
        json.loads(
            (_PROJECT_DIR / "benchmark_data/real_commit_impact_v1/split_freeze.json").read_text(
                encoding="utf-8"
            )
        )["per_split"]["HELD_OUT_TEST"]["case_ids"]
    )
    assert held_test.isdisjoint(set(sampled)), "HELD_OUT_TEST in sample!"
    for cid in sampled:
        packet_dir = OUT / cid
        packet_dir.mkdir(parents=True, exist_ok=True)
        case_dir = V2_DATASET / "scientific" / cid
        # Public intent + candidate universe metadata (parent-visible).
        intent = json.loads((case_dir / "public" / "intent.json").read_text(encoding="utf-8"))
        universe = json.loads((case_dir / "public" / "candidate_universe.json").read_text(encoding="utf-8"))
        graph = json.loads((case_dir / "public" / "dependency_graph.json").read_text(encoding="utf-8"))
        proxy_payload = json.loads(
            (case_dir / "hidden" / "observed_change_set_proxy.json").read_text(encoding="utf-8")
        )
        proxy_paths = sorted(proxy_payload.get("paths", []))
        # P->T diff (name-status; patch if parent is in the cache).
        diff_status = {}
        patch_text = None
        if (CACHE / ".git").exists():
            parent, target = meta[cid]["parent"], meta[cid]["target"]
            proc = subprocess.run(
                ["git", "-C", str(CACHE), "diff", "--name-status", parent, target],
                capture_output=True, text=True,
            )
            if proc.returncode == 0:
                for line in proc.stdout.splitlines():
                    parts = line.split("\t")
                    if len(parts) == 2:
                        diff_status[parts[1]] = parts[0]
                    elif len(parts) == 3:
                        diff_status[parts[2]] = parts[0]
            proc2 = subprocess.run(
                ["git", "-C", str(CACHE), "diff", parent, target],
                capture_output=True, text=True,
            )
            if proc2.returncode == 0:
                patch_text = proc2.stdout

        packet = {
            "case_id": cid,
            "public_intent": intent.get("intent_text"),
            "candidate_universe_count": universe.get("count"),
            "candidate_universe_paths": [r["path"] for r in universe.get("records", [])],
            "graph_edge_count": len(graph.get("edges", [])),
            "parent_commit": meta[cid]["parent"],
            "target_commit": meta[cid]["target"],
            "proxy_count": meta[cid]["proxy_count"],
            "proxy_paths": proxy_paths,
            "diff_name_status": diff_status,
            "diff_patch_available": patch_text is not None,
            "machine_note": (
                "PRELIMINARY machine note: no semantic judgment is made here. "
                "Adjudicate from the diff and intent."
            ),
        }
        (packet_dir / "evidence_packet.json").write_text(
            json.dumps(packet, indent=2, default=str), encoding="utf-8"
        )
        if patch_text is not None:
            (packet_dir / "diff.patch").write_text(patch_text, encoding="utf-8")
        for fp in proxy_paths:
            rows.append([cid, fp, "", "", "", "", "", "", ""])
        packets.append(cid)

    import csv

    with open(OUT / "annotation_form.csv", "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(rows)
    (OUT / "sample_manifest.json").write_text(
        json.dumps({
            "protocol": "docs/SEMANTIC_PROXY_AUDIT_PROTOCOL.md",
            "sample_n": len(packets),
            "seed": SEED,
            "sample_bucket_dist": dict(Counter(meta[c]["bucket"] for c in packets)),
            "case_ids": packets,
            "inter_rater_plan": "2 reviewers on 10-task subset; Cohen's kappa",
        }, indent=2),
        encoding="utf-8",
    )

    print("packets", len(packets))
    print("buckets", dict(Counter(meta[c]["bucket"] for c in packets)))
    print("outputs:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
