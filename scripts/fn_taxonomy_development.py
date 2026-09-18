#!/usr/bin/env python3
# ruff: noqa: E501
"""FIRST-PASS RECALL — Section 2+3: FN taxonomy + S006-like-pattern test.

For EVERY Sparse FN file on DEVELOPMENT, classifies via deterministic rules
using only parent-visible / inference-time-available evidence. Produces:
- reports/FN_TAXONOMY_DEVELOPMENT.md
- reports/fn_taxonomy_development.json

Also tests whether S006-like indirect-utility/downstream misses are a general
pattern (Section 3): proportions of downstream consumers / upstream providers,
graph-distance distribution, lexical disconnect, repo consistency.

Decision: GENERAL_PATTERN | REPO_SPECIFIC | RARE_CASE | INCONCLUSIVE.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PROJECT_DIR / "src"))

from benchmark.recall.data import load_dev_tasks  # noqa: E402
from benchmark.recall.taxonomy import ALL_CATEGORIES, classify_tasks  # noqa: E402

OUT_MD = PROJECT_DIR / "reports" / "FN_TAXONOMY_DEVELOPMENT.md"
OUT_JSON = PROJECT_DIR / "reports" / "fn_taxonomy_development.json"


def _overlap_matrix(rows) -> dict:
    cats = [c for c in ALL_CATEGORIES if c != "NO_OBSERVABLE_SIGNAL"]
    mat: dict[str, dict[str, int]] = {}
    for a in cats:
        mat[a] = {}
        for b in cats:
            mat[a][b] = sum(1 for r in rows if a in r["labels"] and b in r["labels"])
    return mat


def _top_paths(rows, n: int = 20) -> list[dict]:
    cnt = Counter()
    for r in rows:
        path = r["path"]
        parts = path.split("/")
        key = "/".join(parts[-2:]) if len(parts) >= 3 else path
        cnt[key] += 1
    return [{"pattern": k, "count": v} for k, v in cnt.most_common(n)]


def _dist_distribution(rows) -> dict:
    cnt = Counter()
    for r in rows:
        cnt[str(r["dist"])] += 1
    return {k: cnt[k] for k in sorted(cnt, key=lambda x: int(x))}


def _bm25_distribution(rows, bins: tuple = (0.0, 0.001, 0.1, 0.25, 0.5, 0.75, 1.0)) -> dict:
    out: dict[str, int] = {}
    for r in rows:
        b = r["bm25"]
        label = None
        for i in range(len(bins) - 1):
            lo, hi = bins[i], bins[i + 1]
            if lo <= b < hi or (i == len(bins) - 2 and b == hi):
                label = f"[{lo:.3f},{hi:.3f})"
                break
        if label is None:
            label = f"=={bins[-1]}"
        out[label] = out.get(label, 0) + 1
    return out


def _per_task_fn_distribution(tasks) -> dict:
    cnt = Counter(t.n_missed for t in tasks)
    return {str(k): cnt[k] for k in sorted(cnt)}


def main() -> int:
    tasks = load_dev_tasks()
    rows = classify_tasks(list(tasks))
    dc = [r for r in rows if r["repository"] == "djangocms"]
    sc = [r for r in rows if r["repository"] == "saleor"]
    dc_tasks = [t for t in tasks if t.repository == "djangocms"]
    sc_tasks = [t for t in tasks if t.repository == "saleor"]

    def per_repo(repo_rows):
        total = len(repo_rows)
        primary = Counter(r["primary"] for r in repo_rows)
        labels = Counter()
        for r in repo_rows:
            for lab in r["labels"]:
                labels[lab] += 1
        return {
            "n_fn": total,
            "primary_counts": {k: primary[k] for k in ALL_CATEGORIES},
            "primary_pct": {k: round(100 * primary[k] / total, 2) if total else 0.0 for k in ALL_CATEGORIES},
            "label_counts": {k: labels.get(k, 0) for k in ALL_CATEGORIES},
            "overlap_matrix": _overlap_matrix(repo_rows),
            "top_20_patterns": _top_paths(repo_rows),
            "dist_distribution": _dist_distribution(repo_rows),
            "bm25_distribution": _bm25_distribution(repo_rows),
            "per_task_fn_distribution": _per_task_fn_distribution(dc_tasks if repo_rows is dc else sc_tasks),
            "n_tasks": len(dc_tasks) if repo_rows is dc else len(sc_tasks),
            "tasks_with_fn": sum(1 for t in (dc_tasks if repo_rows is dc else sc_tasks) if t.n_missed > 0),
        }

    result = {
        "package": "fn_taxonomy_development",
        "date": "2026-09-18",
        "tier": "T3",
        "note": "Deterministic taxonomy on DEVELOPMENT only. Proxy used ONLY as post-hoc FN label. ZERO API.",
        "categories": list(ALL_CATEGORIES),
        "djangocms_dev": per_repo(dc),
        "saleor_dev": per_repo(sc),
    }

    # ---- Section 3: S006-like pattern test ----
    s3 = {}
    for name, repo_rows in (("djangocms", dc), ("saleor", sc)):
        total = len(repo_rows)
        consumer = sum(1 for r in repo_rows if r["consumer"])
        provider = sum(1 for r in repo_rows if r["provider"])
        consumer_or_provider = sum(1 for r in repo_rows if r["consumer"] or r["provider"])
        # downstream consumers & upstream providers with lexical disconnect
        distant_consumer = sum(1 for r in repo_rows if r["primary"] == "DOWNSTREAM_CONSUMER")
        distant_provider = sum(1 for r in repo_rows if r["primary"] == "UPSTREAM_PROVIDER")
        # lexical disconnect among direct-1-hop FNs (dist==1): how many are lexically silent
        hop1 = [r for r in repo_rows if r["dist"] == 1]
        hop1_no_lex = sum(1 for r in hop1 if r["bm25"] <= 0.0 and r["intent_overlap"] == 0)
        dist_buckets = {"0_seed": sum(1 for r in repo_rows if r["dist"] == 0),
                        "1_hop": sum(1 for r in repo_rows if r["dist"] == 1),
                        "2_hop": sum(1 for r in repo_rows if r["dist"] == 2),
                        "gt2": sum(1 for r in repo_rows if r["dist"] > 2),
                        "unreachable": sum(1 for r in repo_rows if r["dist"] < 0)}
        s3[name] = {
            "n_fn": total,
            "raw_consumer_flag": round(100 * consumer / total, 2) if total else 0.0,
            "raw_provider_flag": round(100 * provider / total, 2) if total else 0.0,
            "raw_consumer_or_provider": round(100 * consumer_or_provider / total, 2) if total else 0.0,
            "primary_downstream_consumer": round(100 * distant_consumer / total, 2) if total else 0.0,
            "primary_upstream_provider": round(100 * distant_provider / total, 2) if total else 0.0,
            "direct_1hop_count": len(hop1),
            "direct_1hop_lexically_silent_pct": round(100 * hop1_no_lex / len(hop1), 2) if hop1 else 0.0,
            "graph_distance_buckets_pct": {k: round(100 * v / total, 2) if total else 0.0 for k, v in dist_buckets.items()},
            "graph_distance_buckets_count": dist_buckets,
            "distant_consumer_lexical_disconnect": round(
                100 * sum(1 for r in repo_rows if r["primary"] == "DOWNSTREAM_CONSUMER" and r["bm25"] <= 0.0 and r["intent_overlap"] == 0)
                / max(1, distant_consumer), 2),
            "distant_provider_lexical_disconnect": round(
                100 * sum(1 for r in repo_rows if r["primary"] == "UPSTREAM_PROVIDER" and r["bm25"] <= 0.0 and r["intent_overlap"] == 0)
                / max(1, distant_provider), 2),
        }

    # GENERAL_PATTERN decision: downstream/upstream consumers+providers are a
    # large, repo-consistent share of FNs and mostly lexically silent.
    dc_share = s3["djangocms"]["raw_consumer_or_provider"]
    sc_share = s3["saleor"]["raw_consumer_or_provider"]
    dc_1hop = s3["djangocms"]["direct_1hop_lexically_silent_pct"]
    sc_1hop = s3["saleor"]["direct_1hop_lexically_silent_pct"]
    if dc_share >= 30 and sc_share >= 30 and (dc_1hop >= 50 or sc_1hop >= 50):
        decision = "GENERAL_PATTERN"
    elif dc_share >= 30 or sc_share >= 30:
        decision = "REPO_SPECIFIC"
    elif dc_share < 15 and sc_share < 15:
        decision = "RARE_CASE"
    else:
        decision = "INCONCLUSIVE"
    s3["decision"] = decision
    s3["evidence"] = {
        "djangocms_consumer_or_provider_pct": dc_share,
        "saleor_consumer_or_provider_pct": sc_share,
        "djangocms_direct_1hop_lexically_silent_pct": dc_1hop,
        "saleor_direct_1hop_lexically_silent_pct": sc_1hop,
    }
    result["s006_like_pattern_test"] = s3

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(result, indent=2), encoding="utf-8")

    md = [
        "# FN Taxonomy — DEVELOPMENT (deterministic)",
        "",
        "**Date:** 2026-09-18  **Tier:** T3 (ZERO API)  **Data:** djangoCMS DEV 174 + Saleor DEV 149",
        "",
        "Classifier input: parent-visible features only (intent text, universe metadata,",
        "dependency graph, djangocms ancestors-of-parent co-change). The hidden proxy is used",
        "ONLY to identify FN files after the fact. Multi-label allowed; one primary per file.",
        "",
        "| Category | Code | Meaning |",
        "|---|---|---|",
        "| DIRECT_LEXICAL | A | path/module/symbol overlaps change intent |",
        "| DIRECT_DEPENDENCY | B | 1-hop undirected edge to/from a seed |",
        "| INDIRECT_DEPENDENCY_2HOP | C | reachable in 2 hops, not 1 |",
        "| DOWNSTREAM_CONSUMER | D | imports a seed, lexically distant |",
        "| UPSTREAM_PROVIDER | E | imported by a seed, lexically distant |",
        "| CROSS_LAYER | F | shared concern across layers, no 1/2-hop edge |",
        "| HISTORY_COCHANGE | G | co-changed with write set in parent ancestors |",
        "| STRUCTURAL_NEIGHBOR | H | same parent dir/module as a seed, no stronger evidence |",
        "| NO_OBSERVABLE_SIGNAL | I | no cheap evidence exposes the file |",
        "",
    ]

    for name, _repo_rows in (("djangocms", dc), ("saleor", sc)):
        rep = result[name + "_dev"]
        md += [
            f"## {name} DEV — primary reason counts",
            "",
            "| Primary | Count | % of FN |",
            "|---|---:|---:|",
        ]
        for cat in ALL_CATEGORIES:
            md.append(f"| {cat} | {rep['primary_counts'][cat]} | {rep['primary_pct'][cat]:.1f} |")
        md += [
            "",
            f"Total FN: **{rep['n_fn']}** over {rep['n_tasks']} tasks "
            f"({rep['tasks_with_fn']} with >=1 FN).",
            "",
            f"### Graph-distance distribution ({name})",
            "",
            "| dist | count |",
            "|---:|---:|",
        ]
        for k, v in rep["dist_distribution"].items():
            md.append(f"| {k} | {v} |")
        md += [
            "",
            f"### Lexical (normalized BM25) distribution ({name})",
            "",
            "| BM25 bin | count |",
            "|---|---:|",
        ]
        for k, v in rep["bm25_distribution"].items():
            md.append(f"| {k} | {v} |")
        md += [
            "",
            f"### Per-task FN count distribution ({name})",
            "",
            "| FNs/task | tasks |",
            "|---:|---:|",
        ]
        for k, v in rep["per_task_fn_distribution"].items():
            md.append(f"| {k} | {v} |")

    md += [
        "",
        "## S006-like indirect-utility / downstream-miss pattern test",
        "",
        "| Metric | djangoCMS | Saleor |",
        "|---|---:|---:|",
        f"| % FN with downstream-consumer flag | {s3['djangocms']['raw_consumer_flag']:.1f} | {s3['saleor']['raw_consumer_flag']:.1f} |",
        f"| % FN with upstream-provider flag | {s3['djangocms']['raw_provider_flag']:.1f} | {s3['saleor']['raw_provider_flag']:.1f} |",
        f"| % FN consumer OR provider (raw) | {s3['djangocms']['raw_consumer_or_provider']:.1f} | {s3['saleor']['raw_consumer_or_provider']:.1f} |",
        f"| % FN primary DOWNSTREAM_CONSUMER | {s3['djangocms']['primary_downstream_consumer']:.1f} | {s3['saleor']['primary_downstream_consumer']:.1f} |",
        f"| % FN primary UPSTREAM_PROVIDER | {s3['djangocms']['primary_upstream_provider']:.1f} | {s3['saleor']['primary_upstream_provider']:.1f} |",
        f"| direct-1-hop FN count | {s3['djangocms']['direct_1hop_count']} | {s3['saleor']['direct_1hop_count']} |",
        f"| direct-1-hop lexically silent % | {s3['djangocms']['direct_1hop_lexically_silent_pct']:.1f} | {s3['saleor']['direct_1hop_lexically_silent_pct']:.1f} |",
        f"| downstream-consumer lexical-disconnect % | {s3['djangocms']['distant_consumer_lexical_disconnect']:.1f} | {s3['saleor']['distant_consumer_lexical_disconnect']:.1f} |",
        "",
        f"**Decision: {decision}**",
        "",
        "Evidence: " + json.dumps(s3["evidence"]),
        "",
        "Machine-readable: reports/fn_taxonomy_development.json",
    ]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("FN rows:", len(rows), "dc:", len(dc), "sc:", len(sc))
    print("S006 decision:", decision)
    print("outputs:", OUT_MD, OUT_JSON)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
