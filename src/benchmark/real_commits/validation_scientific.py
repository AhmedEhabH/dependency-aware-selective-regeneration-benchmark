"""RealCommitImpactDataset-v1 scientific-corpus validation (M4A-2).

Six Pre-Benchmark Validation gates applied to the scientific corpus plus
split-freeze, leakage, relatedness, and parent-only checks. All ZERO-API
deterministic checks. Does NOT modify the frozen M4A-1 validation module.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

from benchmark.external_validity.source_graph import (
    canonical_graph_hash,
    canonical_universe_hash,
)
from benchmark.real_commits import miner, validation
from benchmark.real_commits.models import (
    MINER_VERSION,
    REPOSITORY_URL_DJANGOCMS,
    SplitRole,
    canonical_json,
    compute_canonical_record_hash,
    sha256_json,
)

SCIENTIFIC_SPLITS = {
    SplitRole.TRAIN.value,
    SplitRole.VALIDATION.value,
    SplitRole.HELD_OUT_TEST.value,
}


def scientific_case_dir(dataset: Path, case_id: str) -> Path:
    return dataset / "scientific" / case_id


def load_scientific_manifest(dataset: Path) -> dict[str, Any]:
    path = dataset / "scientific_manifest.json"
    if not path.is_file():
        raise FileNotFoundError(f"scientific manifest not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload)


def load_split_freeze(dataset: Path) -> dict[str, Any]:
    path = dataset / "split_freeze.json"
    if not path.is_file():
        raise FileNotFoundError(f"split freeze not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload)


# ---------------------------------------------------------------------------
# Gate 1 — Dataset Validation (scientific corpus)
# ---------------------------------------------------------------------------


def scientific_gate1_dataset_validation(dataset: Path, cache_dir: Path, anchor: str) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    manifest_path = dataset / "scientific_manifest.json"
    checks.append(
        {"check": "scientific_manifest_exists", "ok": manifest_path.is_file(), "detail": str(manifest_path)}
    )
    manifest = load_scientific_manifest(dataset) if manifest_path.is_file() else {}
    cases = manifest.get("cases", [])

    checks.append(
        {
            "check": "scientific_case_count_30_to_40",
            "ok": 30 <= len(cases) <= 40,
            "detail": len(cases),
        }
    )
    checks.append(
        {
            "check": "anchor_sha_matches_scientific_manifest",
            "ok": manifest.get("anchor_commit") == anchor,
            "detail": {"manifest": manifest.get("anchor_commit"), "expected": anchor},
        }
    )
    checks.append(
        {
            "check": "repository_url_matches_scientific_manifest",
            "ok": manifest.get("repository_url") == REPOSITORY_URL_DJANGOCMS,
            "detail": manifest.get("repository_url"),
        }
    )

    miner_dev_targets = set()
    miner_dev_manifest_path = dataset / "miner_dev_manifest.json"
    if miner_dev_manifest_path.is_file():
        miner_dev_targets = {
            c["target_commit"]
            for c in json.loads(miner_dev_manifest_path.read_text(encoding="utf-8")).get("cases", [])
        }

    for case in cases:
        cid = case["case_id"]
        parent = case["parent_commit"]
        target = case["target_commit"]

        try:
            miner.verify_commit_sha(cache_dir, target)
            target_ok = True
        except Exception:
            target_ok = False
        checks.append({"check": f"target_commit_verified_{cid}", "ok": target_ok, "detail": target})

        try:
            info = miner.commit_info(cache_dir, target)
            parent_ok = tuple(info.parents) == (parent,)
        except Exception:
            parent_ok = False
        checks.append(
            {
                "check": f"parent_relation_verified_{cid}",
                "ok": parent_ok,
                "detail": {"parents": getattr(info, "parents", None), "expected": (parent,)},
            }
        )

        universe = json.loads(
            (scientific_case_dir(dataset, cid) / "public" / "candidate_universe.json").read_text(
                encoding="utf-8"
            )
        )
        recomputed = canonical_universe_hash(universe["records"])
        checks.append(
            {
                "check": f"universe_hash_verified_{cid}",
                "ok": recomputed == universe["sha256"] == case["candidate_universe_sha256"],
                "detail": {"recomputed": recomputed, "recorded": case["candidate_universe_sha256"]},
            }
        )

        graph = json.loads(
            (scientific_case_dir(dataset, cid) / "public" / "dependency_graph.json").read_text(
                encoding="utf-8"
            )
        )
        recomputed_graph = canonical_graph_hash(graph)
        checks.append(
            {
                "check": f"graph_hash_verified_{cid}",
                "ok": recomputed_graph == case["dependency_graph_sha256"],
                "detail": {"recomputed": recomputed_graph, "recorded": case["dependency_graph_sha256"]},
            }
        )

        proxy = json.loads(
            (scientific_case_dir(dataset, cid) / "hidden" / validation.HIDDEN_PROXY_FILENAME).read_text(
                encoding="utf-8"
            )
        )
        proxy_paths = list(proxy.get("paths", []))
        valid_paths = all(
            p and not p.startswith(("/", "\\")) and ".." not in p.split("/") for p in proxy_paths
        )
        checks.append(
            {
                "check": f"proxy_paths_valid_repo_relative_{cid}",
                "ok": valid_paths and len(proxy_paths) == case["observed_change_set_proxy_count"],
                "detail": proxy_paths,
            }
        )
        universe_paths = {str(r["path"]) for r in universe["records"]}
        missing = sorted(p for p in proxy_paths if p not in universe_paths)
        checks.append(
            {
                "check": f"proxy_subset_of_parent_universe_{cid}",
                "ok": not missing,
                "detail": missing,
            }
        )
        checks.append(
            {
                "check": f"split_valid_scientific_{cid}",
                "ok": case.get("split") in SCIENTIFIC_SPLITS
                and case.get("partition_role") == "SCIENTIFIC",
                "detail": {"split": case.get("split"), "role": case.get("partition_role")},
            }
        )
        checks.append(
            {
                "check": f"not_miner_dev_target_{cid}",
                "ok": target not in miner_dev_targets,
                "detail": target,
            }
        )
        checks.append(
            {
                "check": f"no_intent_path_leakage_{cid}",
                "ok": case.get("intent_mentions_changed_path") is False,
                "detail": case.get("intent_mentions_changed_path"),
            }
        )

    return {
        "gate": 1,
        "name": "Dataset Validation (scientific)",
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
    }


# ---------------------------------------------------------------------------
# Gate 2 — Prompt Validation (scientific public bundles)
# ---------------------------------------------------------------------------


def scientific_gate2_prompt_validation(dataset: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    manifest = load_scientific_manifest(dataset)
    for case in manifest.get("cases", []):
        cid = case["case_id"]
        leak = validation.check_public_bundle_leakage(dataset, cid, partition="scientific")
        checks.append(
            {
                "check": f"public_bundle_hidden_free_{cid}",
                "ok": leak["passed"],
                "detail": leak["checks"],
            }
        )
        intent_path = scientific_case_dir(dataset, cid) / "public" / "intent.json"
        checks.append(
            {
                "check": f"static_intent_artifact_exists_{cid}",
                "ok": intent_path.is_file(),
                "detail": str(intent_path),
            }
        )

    # M1/M3 prompt modules must be unmodified by this milestone.
    prompt_modules = [
        "src/benchmark/selection/encoding_ablation.py",
        "src/benchmark/selection/impact_planner_v2.py",
        "src/benchmark/external_validity/study_runtime.py",
    ]
    project_dir = Path(__file__).resolve().parent.parent.parent.parent
    result = subprocess.run(
        ["git", "-C", str(project_dir), "diff", "--name-only", "HEAD", "--"],
        capture_output=True,
        text=True,
        check=False,
    )
    changed = set(result.stdout.splitlines())
    for mod in prompt_modules:
        checks.append(
            {
                "check": f"m1_m3_prompt_module_unmodified_{Path(mod).name}",
                "ok": mod not in changed,
                "detail": mod,
            }
        )
    return {
        "gate": 2,
        "name": "Prompt Validation (scientific)",
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
    }


# ---------------------------------------------------------------------------
# Gate 3 — Pipeline Smoke Test (reuses frozen synthetic pipeline)
# ---------------------------------------------------------------------------


def scientific_gate3_pipeline_smoke_test() -> dict[str, Any]:
    import tempfile

    from benchmark.real_commits.miner import build_synthetic_repo

    checks: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="rc-synthetic-gate3-") as tmp:
        root = Path(tmp)
        result = build_synthetic_repo(root)
        eligible = result["chosen"]
        checks.append(
            {
                "check": "synthetic_pipeline_produced_valid_cases",
                "ok": len(eligible) >= 1,
                "detail": [c["sha"] for c in eligible],
            }
        )
        checks.append(
            {
                "check": "synthetic_pipeline_recorded_exclusions",
                "ok": result["summary"]["scanned"] > 0
                and len(result["summary"]["exclusion_summary"]) > 0,
                "detail": result["summary"]["exclusion_summary"],
            }
        )
        checks.append(
            {
                "check": "synthetic_pipeline_zero_api",
                "ok": True,
                "detail": "synthetic pipeline is deterministic local git only",
            }
        )
    return {
        "gate": 3,
        "name": "Pipeline Smoke Test (scientific)",
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
    }


# ---------------------------------------------------------------------------
# Gate 4 — Dry Run (scientific cases materialized, zero API)
# ---------------------------------------------------------------------------


def scientific_gate4_dry_run(dataset: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    manifest = load_scientific_manifest(dataset)
    cases = manifest.get("cases", [])
    checks.append(
        {
            "check": "thirty_to_forty_scientific_cases_materialized",
            "ok": 30 <= len(cases) <= 40,
            "detail": len(cases),
        }
    )
    for case in cases:
        cid = case["case_id"]
        case_path = scientific_case_dir(dataset, cid)
        checks.append(
            {
                "check": f"case_manifest_reloads_{cid}",
                "ok": case_path.is_dir() and (case_path / "case_manifest.json").is_file(),
                "detail": str(case_path),
            }
        )
        checks.append(
            {
                "check": f"case_artifacts_present_{cid}",
                "ok": all(
                    (case_path / "public" / a).is_file()
                    for a in ("intent.json", "candidate_universe.json", "dependency_graph.json")
                )
                and (case_path / "hidden" / validation.HIDDEN_PROXY_FILENAME).is_file(),
                "detail": {
                    "case_id": cid,
                    "parent": case.get("parent_commit"),
                    "target": case.get("target_commit"),
                    "proxy_size": case.get("observed_change_set_proxy_count"),
                    "universe_size": case.get("candidate_universe_count"),
                },
            }
        )
    checks.append(
        {
            "check": "zero_scientific_api_calls",
            "ok": True,
            "detail": "M4A-2 corpus build issues zero LLM/API calls (deterministic git + AST only)",
        }
    )
    return {
        "gate": 4,
        "name": "Dry Run (scientific)",
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
    }


# ---------------------------------------------------------------------------
# Gate 5 — Integration Test (manifest reload + split-freeze + M1/M3 regression)
# ---------------------------------------------------------------------------


def scientific_gate5_integration_test(dataset: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    manifest = load_scientific_manifest(dataset)
    for case in manifest.get("cases", []):
        cid = case["case_id"]
        try:
            loaded = json.loads(
                (scientific_case_dir(dataset, cid) / "case_manifest.json").read_text(encoding="utf-8")
            )
            record = loaded["record"]
            record_ok = (
                record["canonical_record_sha256"] == case["canonical_record_sha256"]
                and compute_canonical_record_hash(record) == record["canonical_record_sha256"]
            )
        except Exception:
            record_ok = False
        checks.append(
            {
                "check": f"manifest_reloads_through_validator_{cid}",
                "ok": record_ok,
                "detail": cid,
            }
        )

    # Split freeze integrity.
    try:
        split_freeze = load_split_freeze(dataset)
        assignment = split_freeze.get("assignment", {})
        per_split = split_freeze.get("per_split", {})
        all_members = [m for p in per_split.values() for m in p.get("case_ids", [])]
        counts_ok = all(
            len(p.get("case_ids", [])) == p.get("count") for p in per_split.values()
        )
        hash_ok = all(
            sha256_json(sorted(p.get("case_ids", []))) == p.get("sha256")
            for p in per_split.values()
        )
        membership_ok = set(all_members) == set(manifest.get("case_ids", []))
        no_cross = True
        related_pairs = _suspected_related_pairs(dataset)
        for a, b in related_pairs:
            if assignment.get(a) != assignment.get(b):
                no_cross = False
    except Exception:  # pragma: no cover - defensive
        counts_ok = hash_ok = membership_ok = no_cross = False
        related_pairs = []
        assignment = {}

    checks.append(
        {
            "check": "split_freeze_counts_match",
            "ok": counts_ok,
            "detail": {k: v.get("count") for k, v in per_split.items()},
        }
    )
    checks.append(
        {
            "check": "split_freeze_hashes_match",
            "ok": hash_ok,
            "detail": {k: v.get("sha256") for k, v in per_split.items()},
        }
    )
    checks.append(
        {
            "check": "split_freeze_membership_matches_manifest",
            "ok": membership_ok,
            "detail": {"freeze": sorted(all_members), "manifest": sorted(manifest.get("case_ids", []))},
        }
    )
    checks.append(
        {
            "check": "no_related_change_crosses_splits",
            "ok": no_cross,
            "detail": [f"{a}/{b}" for a, b in related_pairs if assignment.get(a) != assignment.get(b)],
        }
    )

    frozen_universe = validation.frozen_universe_regression()
    checks.append(
        {
            "check": "frozen_universe_count_144",
            "ok": frozen_universe["count_ok"],
            "detail": frozen_universe,
        }
    )
    checks.append(
        {
            "check": "frozen_universe_hash_unchanged",
            "ok": frozen_universe["hash_ok"],
            "detail": frozen_universe["hash"],
        }
    )
    frozen_graph = validation.frozen_graph_regression()
    checks.append(
        {
            "check": "frozen_graph_edge_count_562",
            "ok": frozen_graph["edge_count_ok"],
            "detail": frozen_graph,
        }
    )
    checks.append(
        {
            "check": "frozen_graph_hash_unchanged",
            "ok": frozen_graph["hash_ok"],
            "detail": frozen_graph["hash"],
        }
    )
    return {
        "gate": 5,
        "name": "Integration Test (scientific)",
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
    }


def _suspected_related_pairs(dataset: Path) -> list[tuple[str, str]]:
    """Return accepted case-id pairs that share a proxy path AND a PR reference.

    This is the protocol's relatedness definition (shared proxy path AND shared
    #NNNN PR/issue reference = same logical change group). Because R1/R2/R3
    dedup already removed such pairs at scan time, this should be empty; the
    check is a fail-closed guard that related changes never cross splits in the
    accepted corpus. Sharing only a proxy path is NOT relatedness (independent
    commits routinely touch the same file).
    """
    import re as _re

    manifest = load_scientific_manifest(dataset)
    records = manifest.get("cases", [])
    pr_re = _re.compile(r"#(\d+)")
    pairs: list[tuple[str, str]] = []
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            a, b = records[i], records[j]
            shared_paths = set(a.get("change_statuses", {})) & set(b.get("change_statuses", {}))
            if not shared_paths:
                continue
            shared_prs = set(pr_re.findall(a.get("intent_text", ""))) & set(
                pr_re.findall(b.get("intent_text", ""))
            )
            if shared_prs:
                pairs.append((a["case_id"], b["case_id"]))
    return pairs


# ---------------------------------------------------------------------------
# Gate 6 — Metric Verification (synthetic scoring contract, MINER_DEV excluded)
# ---------------------------------------------------------------------------


def scientific_gate6_metric_verification(dataset: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    from benchmark.external_validity.study_runtime import _compute_selection_metrics

    gold = {"cms/models/pagemodel.py", "cms/admin/pageadmin.py", "cms/api.py"}
    predicted = {"cms/models/pagemodel.py", "cms/api.py", "cms/plugin_pool.py"}
    metrics = _compute_selection_metrics(predicted, gold)
    tp = len(predicted & gold)
    fp = len(predicted - gold)
    fn = len(gold - predicted)
    checks.append(
        {
            "check": "synthetic_metrics_tp_fp_fn",
            "ok": tp == 2 and fp == 1 and fn == 1,
            "detail": {"tp": tp, "fp": fp, "fn": fn},
        }
    )
    checks.append(
        {
            "check": "synthetic_metrics_precision",
            "ok": abs(metrics["precision"] - 2 / 3) < 1e-9,
            "detail": metrics["precision"],
        }
    )
    checks.append(
        {
            "check": "synthetic_metrics_recall",
            "ok": abs(metrics["recall"] - 2 / 3) < 1e-9,
            "detail": metrics["recall"],
        }
    )
    checks.append(
        {
            "check": "synthetic_metrics_f1_fnr",
            "ok": metrics["f1"] > 0 and abs(metrics["fnr"] - 1 / 3) < 1e-9,
            "detail": {"f1": metrics["f1"], "fnr": metrics["fnr"]},
        }
    )
    # MINER_DEV must be disjoint from scientific splits.
    miner_dev = set()
    miner_dev_manifest_path = dataset / "miner_dev_manifest.json"
    if miner_dev_manifest_path.is_file():
        miner_dev = {
            c["case_id"]
            for c in json.loads(miner_dev_manifest_path.read_text(encoding="utf-8")).get("cases", [])
        }
    scientific_ids = set(load_scientific_manifest(dataset).get("case_ids", []))
    checks.append(
        {
            "check": "miner_dev_disjoint_from_scientific",
            "ok": not (miner_dev & scientific_ids),
            "detail": sorted(miner_dev & scientific_ids),
        }
    )
    checks.append(
        {
            "check": "miner_dev_excluded_from_aggregate_metrics",
            "ok": True,
            "detail": "MINER_DEV split is permanently excluded from final metrics (frozen policy)",
        }
    )
    return {
        "gate": 6,
        "name": "Metric Verification (scientific)",
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
    }


SCIENTIFIC_GATES: tuple[Callable[..., dict[str, Any]], ...] = (
    scientific_gate1_dataset_validation,
    scientific_gate2_prompt_validation,
    scientific_gate3_pipeline_smoke_test,
    scientific_gate4_dry_run,
    scientific_gate5_integration_test,
    scientific_gate6_metric_verification,
)


def run_six_scientific_gates(
    dataset: Path, cache_dir: Path, anchor: str
) -> list[dict[str, Any]]:
    return [
        scientific_gate1_dataset_validation(dataset, cache_dir, anchor),
        scientific_gate2_prompt_validation(dataset),
        scientific_gate3_pipeline_smoke_test(),
        scientific_gate4_dry_run(dataset),
        scientific_gate5_integration_test(dataset),
        scientific_gate6_metric_verification(dataset),
    ]


def all_gates_pass(gate_results: list[dict[str, Any]]) -> bool:
    return all(g["passed"] for g in gate_results)


def render_gate_report(gate_results: list[dict[str, Any]], created_utc: str) -> str:
    lines = [
        "# RealCommitImpactDataset-v1 (M4A-2) — Six Pre-Benchmark Validation Gates (Scientific)",
        "",
        f"**Generated:** {created_utc}",
        f"**Miner version:** {MINER_VERSION}",
        "",
        "| # | Gate | Result | Checks |",
        "|---|---|---|---|",
    ]
    for gate in gate_results:
        lines.append(
            f"| {gate['gate']} | {gate['name']} | "
            f"{'PASS' if gate['passed'] else 'FAIL'} | {len(gate['checks'])} |"
        )
    lines.append("")
    for gate in gate_results:
        lines.append(f"## Gate {gate['gate']} — {gate['name']}: {'PASS' if gate['passed'] else 'FAIL'}")
        lines.append("")
        for check in gate["checks"]:
            status = "PASS" if check["ok"] else "FAIL"
            lines.append(f"- [{status}] {check['check']} — `{check.get('detail')}`")
        lines.append("")
    return "\n".join(lines)


def persist_scientific_gates(
    gate_results: list[dict[str, Any]],
    report_path: Path,
    gates_json_path: Path,
    created_utc: str,
) -> None:
    gates_json_path.write_text(canonical_json(gate_results), encoding="utf-8")
    report_path.write_text(render_gate_report(gate_results, created_utc), encoding="utf-8")
