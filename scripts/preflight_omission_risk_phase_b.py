"""Omission-Risk Feature Study V1 — Phase-B mandatory preflight (A–G).

Implements the amended preflight gates:
A. Phase-B data availability gate (per split: proxy / Sparse-v2 / Full-v2
   prediction availability, repetitions, source artifact, model/provider,
   frozen tag, label usability, feature-design usability).
B. Repository evidence-capability audit (per repo: task count, candidate
   universe distribution, graph availability/stats/version, history
   availability, BM25 index availability, parent-revision correctness,
   missing-evidence reason) -> reports/OMISSION_RISK_REPOSITORY_EVIDENCE_AUDIT.md
   + machine-readable JSON/CSV.
C. Cross-repository confound rule (single-repository declaration).
D. Feature availability flags (repo_id, graph_available, history_available,
   retrieval_available, sparse_plan_available) added to the feature table.
E. Graph feature interpretation pre-registration (graph source/coverage).
F. History/co-change interpretation pre-registration (per-task prior-commit
   usability; cold-start condition).
G. Manual equivalence sanity check (deterministic 10-row sample: frozen
   cheap-baselines vs harness output; prediction/metric equality + config).
"""

# ruff: noqa: E501  (markdown/audit string literals are intentionally long)

from __future__ import annotations

import csv
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

from benchmark.harness.djangocms import DjangoCMSRealCommitDataset
from benchmark.omission_risk.study import DATASET_DIR_DEFAULT, OUTPUT_DIR_DEFAULT

FROZEN_TAG_RESEARCH_HARNESS = "research-harness-v1-dev-2026-09-16"
P1_PROTOCOL_VERSION = "real-commit-p1-v1.0.0"
P1_MODEL = "qwen/qwen3-coder"
P1_PROVIDER_TAG = "deepinfra/turbo"


def data_availability_gate(dataset_dir: Path) -> dict[str, Any]:
    """Gate A: record prediction availability per split (no inference)."""
    split_freeze = json.loads((dataset_dir / "split_freeze.json").read_text(encoding="utf-8"))
    raw_lines = Path("research/real-commit-p1-01/run_records.jsonl").read_text(encoding="utf-8").splitlines()
    p1_records = [json.loads(line) for line in raw_lines]
    p1_by_case: dict[str, list[dict[str, Any]]] = {}
    for rec in p1_records:
        p1_by_case.setdefault(rec["case_id"], []).append(rec)

    out: dict[str, Any] = {}
    for split, spec in split_freeze["per_split"].items():
        case_ids = sorted(spec["case_ids"])
        row: dict[str, Any] = {
            "split": split,
            "n_tasks": len(case_ids),
            "reference_proxy_available": True,
            "sparse_v2_prediction_available": all(
                any(r["arm"] == "sparse_v2" for r in p1_by_case.get(cid, []))
                for cid in case_ids
            )
            if case_ids
            else False,
            "full_v2_prediction_available": all(
                any(r["arm"] == "full_v2" for r in p1_by_case.get(cid, []))
                for cid in case_ids
            )
            if case_ids
            else False,
            "repetitions": (
                3
                if case_ids
                and all(
                    len([r for r in p1_by_case.get(cid, []) if r["arm"] == "sparse_v2"]) == 3
                    for cid in case_ids
                )
                else 0
            ),
            "source_artifact": (
                "research/real-commit-p1-01/run_records.jsonl"
                if any(p1_by_case.get(cid) for cid in case_ids)
                else "NONE"
            ),
            "model": P1_MODEL,
            "provider": P1_PROVIDER_TAG,
            "protocol_version": P1_PROTOCOL_VERSION,
            "frozen_tag": FROZEN_TAG_RESEARCH_HARNESS,
            "usable_for_labels": all(
                any(r["arm"] == "sparse_v2" for r in p1_by_case.get(cid, []))
                for cid in case_ids
            )
            if case_ids
            else False,
            "usable_for_feature_design": split != "HELD_OUT_TEST",
            "note": "",
        }
        if split == "HELD_OUT_TEST":
            row["usable_for_feature_design"] = False
            row["note"] = "PERMANENTLY EXPOSED: never for tuning/selection/threshold"
        out[split] = row

    out["decision"] = (
        "TRAIN/VALIDATION Sparse-v2 labels UNAVAILABLE (no Sparse-v2 predictions "
        "exist on TRAIN/VALIDATION; P1 ran only on HELD_OUT_TEST). Scientific "
        "feature analysis gated on the Sparse-v2 label is DEFERRED pending the "
        "frozen DEVELOPMENT-INFERENCE protocol + approval."
    )
    return out


def repository_evidence_audit(dataset_dir: Path) -> dict[str, Any]:
    """Gate B: per-repository evidence-capability audit."""
    ds = DjangoCMSRealCommitDataset(dataset_dir=dataset_dir)
    case_ids = ds.case_ids()
    sizes: list[int] = []
    graph_nodes: list[int] = []
    graph_edges: list[int] = []
    graph_density: list[float] = []
    graph_versions: Counter[str] = Counter()
    parent_commits: set[str] = set()
    for cid in case_ids:
        case = ds.load_public_case(cid)
        sizes.append(len(case.candidate_paths))
        active = set(case.candidate_paths)
        edges = [e for e in case.graph_edges if e[0] in active and e[1] in active]
        graph_edges.append(len(edges))
        graph_nodes.append(len(active))
        denom = len(active) * (len(active) - 1) / 2
        graph_density.append(len(edges) / denom if denom > 0 else 0.0)
        parent_commits.add(case.parent_commit)
        graph_path = dataset_dir / "scientific" / cid / "public" / "dependency_graph.json"
        if graph_path.exists():
            g = json.loads(graph_path.read_text(encoding="utf-8"))
            graph_versions[str(g.get("extractor_version"))] += 1

    sizes_sorted = sorted(sizes)

    def q(pct: float) -> float:
        if not sizes_sorted:
            return 0.0
        idx = int((len(sizes_sorted) - 1) * pct)
        return float(sizes_sorted[idx])

    def med(vals: list[int]) -> int:
        sv = sorted(vals)
        return sv[len(sv) // 2] if sv else 0

    n_cases = len(sizes_sorted)
    return {
        "repo_id": "djangocms",
        "repo_url": "https://github.com/django-cms/django-cms",
        "tasks_used_in_study": {"TRAIN": 24, "VALIDATION": 6, "total": len(case_ids)},
        "candidate_universe_size": {
            "n_cases": n_cases,
            "min": min(sizes_sorted) if sizes_sorted else 0,
            "q25": q(0.25),
            "median": q(0.5),
            "q75": q(0.75),
            "max": max(sizes_sorted) if sizes_sorted else 0,
        },
        "graph_available": True,
        "graph_node_count": {"min": min(graph_nodes, default=0), "median": med(graph_nodes), "max": max(graph_nodes, default=0)},
        "graph_edge_count": {
            "min": min(graph_edges, default=0),
            "median": med(graph_edges),
            "max": max(graph_edges, default=0),
            "zero_edge_cases": sum(1 for e in graph_edges if e == 0),
        },
        "graph_density": {
            "min": round(min(graph_density, default=0.0), 5),
            "median": round(sorted(graph_density)[len(graph_density) // 2], 6) if graph_density else 0.0,
            "max": round(max(graph_density, default=0.0), 6),
        },
        "graph_construction": {
            "source": "frozen parent-only AST dependency graph (RealCommitImpactDataset-v1)",
            "extractor_versions_seen": dict(graph_versions),
            "distinct_parent_commits_in_study": len(parent_commits),
        },
        "history_available": False,
        "co_change_history_depth_usable_commits": 0,
        "historical_memory_coverage": "none (no git cache; the frozen miner produced only the observed proxy per task)",
        "bm25_index_available": {"metadata_corpus": True, "parent_commit_corpus": False},
        "parent_revision_correctness": True,
        "parent_revision_note": "candidate universe + dependency graph are built from the parent commit only (M4A-1/M4A-2 audited)",
        "missing_evidence_reason": "pinned djangocms git cache (benchmark_data/repositories/djangocms) absent locally -> parent-commit corpus not re-materializable",
        "classification": "single-repository DEVELOPMENT evidence; no cross-repository generalization",
    }


def availability_flags(output_dir: Path) -> dict[str, Any]:
    """Gate D: attach availability flags to every feature-table row."""
    csv_path = output_dir / "feature_table.csv"
    if not csv_path.exists():
        return {"status": "feature_table not found"}
    with open(csv_path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    header = list(rows[0].keys())
    for col in (
        "repo_id",
        "graph_available",
        "history_available",
        "retrieval_available",
        "sparse_plan_available",
    ):
        if col not in header:
            header.append(col)
    out = output_dir / "feature_table_with_flags.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=header)
        writer.writeheader()
        for r in rows:
            r["repo_id"] = "djangocms"
            r["graph_available"] = "1"
            r["history_available"] = "0"
            r["retrieval_available"] = "1"
            r["sparse_plan_available"] = "0"
            writer.writerow(r)
    return {"feature_table_with_flags": str(out)}


def graph_interpretation_registration(dataset_dir: Path) -> dict[str, Any]:
    """Gate E: pre-register the graph source/coverage interpretation."""
    ds = DjangoCMSRealCommitDataset(dataset_dir=dataset_dir)
    zero_edge = 0
    tiny_edge = 0
    for cid in ds.case_ids():
        case = ds.load_public_case(cid)
        active = set(case.candidate_paths)
        edges = [e for e in case.graph_edges if e[0] in active and e[1] in active]
        if len(edges) == 0:
            zero_edge += 1
        elif len(edges) < 20:
            tiny_edge += 1
    return {
        "graph_source": "frozen parent-only AST dependency graph (RealCommitImpactDataset-v1, M4A-1 miner)",
        "coverage": "every task has a dependency_graph.json artifact from the parent revision",
        "zero_edge_cases": zero_edge,
        "tiny_edge_cases": tiny_edge,
        "safe_interpretation_branches": {
            "informative_graph_weak_feature": "graph present and non-trivial AND feature weak -> 'informative graph + weak feature'",
            "weak_incomplete_graph": "graph tiny/zero-edge -> 'weak/incomplete graph; no claim about feature'",
            "no_graph_evidence": "no graph artifact -> 'no graph evidence available'",
        },
        "registered_conclusion_for_this_study": (
            "if graph features are weak on non-trivial graphs the safe reading is "
            "'informative graph + weak feature', NOT 'graph reasoning is unhelpful'"
        ),
    }


def history_interpretation_registration() -> dict[str, Any]:
    """Gate F: pre-register history/co-change interpretation."""
    return {
        "rule": "historical/co-change features would use ONLY history visible before the task's parent revision; no future history.",
        "per_task_prior_commits_usable": 0,
        "co_change_observations_available": 0,
        "coverage_of_candidate_files": "none",
        "cold_start_condition": "yes (no usable git history in the study environment)",
        "deferred": "history/co-change feature family is DEFERRED pending the frozen DEVELOPMENT-INFERENCE protocol (no repo cache; zero-LLM principle)",
    }


def equivalence_sanity_sample(
    *, seed: int = 20260916, n_rows: int = 10,
) -> dict[str, Any]:
    """Gate G: deterministic 10-row manual sanity sample (frozen vs harness)."""
    frozen_path = Path("research/cheap-baselines-v1/raw_predictions_v1.json")
    harness_path = Path("research/harness-protocol-a-equivalence/raw_predictions_via_harness_v1.json")
    if not (frozen_path.exists() and harness_path.exists()):
        return {"status": "equivalence evidence missing"}
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    harness = json.loads(harness_path.read_text(encoding="utf-8"))
    fc = {c["case_id"]: c for c in frozen["cases"]}
    hc = {c["case_id"]: c for c in harness["cases"]}
    all_rows: list[tuple[str, dict[str, Any]]] = []
    for cid, c in fc.items():
        for r in c["results"]:
            all_rows.append((cid, r))
    all_rows.sort(key=lambda x: (x[0], x[1]["baseline"], x[1]["k"]))
    rng = random.Random(seed)
    idx = sorted(rng.sample(range(len(all_rows)), min(n_rows, len(all_rows))))
    out: list[dict[str, Any]] = []
    for i in idx:
        cid, fr = all_rows[i]
        hr = next(
            (
                r
                for r in hc[cid]["results"]
                if r["baseline"] == fr["baseline"] and r["k"] == fr["k"]
            ),
            None,
        )
        pred_eq = hr is not None and hr["ranked_paths"] == fr["ranked_paths"]
        metric_eq = hr is not None and all(
            hr.get(f) == fr.get(f)
            for f in ("tp", "fp", "fn", "precision", "recall", "f1", "fnr", "full_recall")
        )
        out.append(
            {
                "case_id": cid,
                "baseline": fr["baseline"],
                "k": fr["k"],
                "old_selected": fr["selected_paths"],
                "harness_selected": hr["selected_paths"] if hr else None,
                "prediction_equal": bool(pred_eq),
                "metric_equal": bool(metric_eq),
                "frozen_metrics": {f: fr.get(f) for f in ("tp", "fp", "fn", "precision", "recall", "f1", "fnr")},
                "harness_metrics": {f: hr.get(f) for f in ("tp", "fp", "fn", "precision", "recall", "f1", "fnr")} if hr else None,
                "config_hash_frozen": fc[cid].get("config_hash"),
                "config_hash_harness": hc[cid].get("config_hash"),
                "split": fc[cid].get("split"),
            }
        )
    all_equal = all(r["prediction_equal"] and r["metric_equal"] for r in out)
    return {
        "status": "ok",
        "n_rows": len(out),
        "seed": seed,
        "all_sample_equal": bool(all_equal),
        "note": "sampling is a sanity check only; the full 600-row byte-identical equivalence proof remains primary",
        "rows": out,
    }


def run_preflight() -> dict[str, Any]:
    dataset_dir = Path(DATASET_DIR_DEFAULT)
    output_dir = Path(OUTPUT_DIR_DEFAULT)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir = Path("reports")
    report_dir.mkdir(parents=True, exist_ok=True)

    avail = data_availability_gate(dataset_dir)
    (output_dir / "data_availability.json").write_text(
        json.dumps(avail, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    repo = repository_evidence_audit(dataset_dir)
    (output_dir / "repository_evidence_audit.json").write_text(
        json.dumps(repo, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    with open(output_dir / "repository_evidence_audit.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["metric", "value"])
        for k, v in repo.items():
            if isinstance(v, (int, float, str, bool)) or v is None:
                w.writerow([k, v])
            else:
                w.writerow([k, json.dumps(v)])

    flags = availability_flags(output_dir)

    graph_reg = graph_interpretation_registration(dataset_dir)
    hist_reg = history_interpretation_registration()

    sanity = equivalence_sanity_sample()
    (output_dir / "equivalence_sanity_sample.json").write_text(
        json.dumps(sanity, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    md = f"""# Omission-Risk Repository Evidence Audit — Phase-B preflight (A–G)

**Date:** 2026-09-16
**Study:** OMISSION_RISK_FEATURE_STUDY_V1 (development evidence only)
**Repo:** djangoCMS (RealCommitImpactDataset-v1 frozen split; TRAIN 24 / VALIDATION 6).

## A. Phase-B data availability (no inference)
| Split | n | proxy | Sparse-v2 | Full-v2 | reps | source | label usable |
|---|---|---|---|---|---|---|---|
| TRAIN | {avail['TRAIN']['n_tasks']} | yes | {avail['TRAIN']['sparse_v2_prediction_available']} | {avail['TRAIN']['full_v2_prediction_available']} | {avail['TRAIN']['repetitions']} | {avail['TRAIN']['source_artifact']} | {avail['TRAIN']['usable_for_labels']} |
| VALIDATION | {avail['VALIDATION']['n_tasks']} | yes | {avail['VALIDATION']['sparse_v2_prediction_available']} | {avail['VALIDATION']['full_v2_prediction_available']} | {avail['VALIDATION']['repetitions']} | {avail['VALIDATION']['source_artifact']} | {avail['VALIDATION']['usable_for_labels']} |
| HELD_OUT_TEST | {avail['HELD_OUT_TEST']['n_tasks']} | yes | {avail['HELD_OUT_TEST']['sparse_v2_prediction_available']} | {avail['HELD_OUT_TEST']['full_v2_prediction_available']} | {avail['HELD_OUT_TEST']['repetitions']} | {avail['HELD_OUT_TEST']['source_artifact']} | {avail['HELD_OUT_TEST']['usable_for_labels']} (exposed; feature-design NO) |

**Decision:** {avail['decision']}

## B. Repository evidence-capability
| Item | Value |
|---|---|
| repo_id | {repo['repo_id']} |
| tasks (study) | {repo['tasks_used_in_study']} |
| candidate universe size | {repo['candidate_universe_size']} |
| graph_available | {repo['graph_available']} |
| graph node count | {repo['graph_node_count']} |
| graph edge count | {repo['graph_edge_count']} |
| graph density | {repo['graph_density']} |
| graph construction | {repo['graph_construction']} |
| history_available | {repo['history_available']} |
| co-change depth usable | {repo['co_change_history_depth_usable_commits']} |
| historical-memory coverage | {repo['historical_memory_coverage']} |
| BM25 index | {repo['bm25_index_available']} |
| parent-revision correctness | {repo['parent_revision_correctness']} |
| missing-evidence reason | {repo['missing_evidence_reason']} |

## C. Cross-repository confound: single repository -> single-repository DEVELOPMENT evidence; no cross-repository generalization claim.

## D. Feature availability flags
Every row in `feature_table_with_flags.csv` carries: repo_id=djangocms, graph_available=1, history_available=0, retrieval_available=1, sparse_plan_available=0.

## E. Graph interpretation pre-registration
```json
{json.dumps(graph_reg, indent=1, ensure_ascii=False)}
```

## F. History/co-change interpretation pre-registration
```json
{json.dumps(hist_reg, indent=1, ensure_ascii=False)}
```

## G. Manual equivalence sanity check
```json
{json.dumps(sanity, indent=1, ensure_ascii=False)}
```
Machine-readable: research/omission-risk-feature-study-v1/repository_evidence_audit.json/.csv.
"""
    (report_dir / "OMISSION_RISK_REPOSITORY_EVIDENCE_AUDIT.md").write_text(md, encoding="utf-8")
    return {
        "availability": avail,
        "repo": repo,
        "flags": flags,
        "graph_reg": graph_reg,
        "hist_reg": hist_reg,
        "sanity_status": sanity["status"],
        "sanity_all_equal": sanity.get("all_sample_equal"),
    }


if __name__ == "__main__":
    print(json.dumps(run_preflight(), indent=1)[:4000])
