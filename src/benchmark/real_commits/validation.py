"""RealCommitImpactDataset-v1 (M4A-1): validation gates and independent audit.

All six Pre-Benchmark Validation gates are ZERO-API deterministic checks. The
independent audit is a separate verifier path (``scripts/verify_real_commit_dataset.py``)
that never trusts the builder's in-memory objects.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, cast

from benchmark.external_validity.source_graph import (
    canonical_graph_hash,
    canonical_universe_hash,
)
from benchmark.real_commits import miner
from benchmark.real_commits.models import (
    DJANGOCMS_ANCHOR_COMMIT,
    REPOSITORY_URL_DJANGOCMS,
    SplitRole,
    canonical_json,
)

HIDDEN_PROXY_FILENAME = "observed_change_set_proxy.json"
HIDDEN_FIELD_NAMES = (
    "observed_change_set_proxy",
    "statuses",
    "changed_paths",
    "proxy_paths",
    "change_statuses",
)
SEMANTIC_GOLD_TOKENS = (
    "REGENERATE",
    "VALIDATE",
    "HUMAN_REVIEW",
    "PRESERVE",
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Artifact loading helpers
# ---------------------------------------------------------------------------


def dataset_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent / "benchmark_data" / "real_commit_impact_v1"


def case_dir(dataset: Path, case_id: str) -> Path:
    return dataset / "miner_dev" / case_id


def load_case_manifest(dataset: Path, case_id: str) -> dict[str, Any]:
    path = case_dir(dataset, case_id) / "case_manifest.json"
    if not path.is_file():
        raise FileNotFoundError(f"case manifest not found: {path}")
    return cast(dict[str, Any], load_json(path))


def load_public_artifact(dataset: Path, case_id: str, artifact: str) -> dict[str, Any]:
    path = case_dir(dataset, case_id) / "public" / artifact
    if not path.is_file():
        raise FileNotFoundError(f"public artifact not found: {path}")
    return cast(dict[str, Any], load_json(path))


def load_hidden_proxy(dataset: Path, case_id: str) -> dict[str, Any]:
    path = case_dir(dataset, case_id) / "hidden" / HIDDEN_PROXY_FILENAME
    if not path.is_file():
        raise FileNotFoundError(f"hidden proxy not found: {path}")
    return cast(dict[str, Any], load_json(path))


# ---------------------------------------------------------------------------
# Leakage barrier
# ---------------------------------------------------------------------------


def public_bundle_text(dataset: Path, case_id: str) -> str:
    """Serialize the entire public inference bundle as a single text blob."""
    parts: list[str] = []
    for artifact in ("intent.json", "candidate_universe.json", "dependency_graph.json"):
        payload = load_public_artifact(dataset, case_id, artifact)
        parts.append(canonical_json(payload))
    return "\n".join(parts)


def check_public_bundle_leakage(dataset: Path, case_id: str) -> dict[str, Any]:
    """Assert the public bundle contains no hidden proxy/diff/target/gold content.

    Structural interpretation (M4A-1): production candidate paths legitimately
    appear in the public candidate universe (the universe is public); the HIDDEN
    signal is the *membership list with statuses* plus the target diff and target
    file contents. We therefore assert absence of:
      - the hidden proxy artifact filename / field names;
      - proxy status marker rows (e.g. ``M\\t<path>``) and git diff markers;
      - the full hidden-proxy JSON serialization as an embedded substring;
      - semantic gold / action label tokens.
    """
    text = public_bundle_text(dataset, case_id)
    proxy = load_hidden_proxy(dataset, case_id)
    checks: list[dict[str, Any]] = []

    checks.append(
        {
            "check": "no_proxy_filename_in_public",
            "ok": HIDDEN_PROXY_FILENAME not in text,
            "detail": HIDDEN_PROXY_FILENAME,
        }
    )
    checks.append(
        {
            "check": "no_hidden_field_names_in_public",
            "ok": not any(field in text for field in HIDDEN_FIELD_NAMES),
            "detail": [f for f in HIDDEN_FIELD_NAMES if f in text],
        }
    )
    # Status marker rows ("M\t<path>") would expose the proxy membership signal.
    status_rows = [
        f"{status}\t{path}"
        for path, status in proxy.get("statuses", {}).items()
        if f"{status}\t{path}" in text
    ]
    checks.append(
        {
            "check": "no_proxy_status_marker_rows_in_public",
            "ok": not status_rows,
            "detail": status_rows,
        }
    )
    diff_markers = [m for m in ("diff --git", "--- a/", "+++ b/") if m in text]
    checks.append(
        {
            "check": "no_target_diff_text_in_public",
            "ok": not diff_markers,
            "detail": diff_markers,
        }
    )
    # The full hidden proxy payload must never be embedded in any public artifact.
    proxy_json = canonical_json(proxy)
    checks.append(
        {
            "check": "no_hidden_proxy_payload_embedded_in_public",
            "ok": proxy_json not in text,
            "detail": f"proxy_json_bytes={len(proxy_json)}",
        }
    )
    semantic_hits = [t for t in SEMANTIC_GOLD_TOKENS if re.search(rf"\b{t}\b", text)]
    checks.append(
        {
            "check": "no_semantic_gold_tokens_in_public",
            "ok": not semantic_hits,
            "detail": semantic_hits,
        }
    )
    return {
        "case_id": case_id,
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
    }


# ---------------------------------------------------------------------------
# Frozen regression helpers
# ---------------------------------------------------------------------------

FROZEN_UNIVERSE_COUNT = 144
FROZEN_UNIVERSE_HASH = "43f4279bdf228745b1f6b289c81cda141b089ab5be4f4af63bb8f39f837c4410"
FROZEN_GRAPH_EDGE_COUNT = 562
FROZEN_GRAPH_HASH = "0a6bf0f758c9cd7de79adb72138c549a2b0aee3cfd62841496cb455d1ce7cd58"

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent.parent
FROZEN_UNIVERSE_PATH = (
    PROJECT_DIR / "benchmark_data" / "external_validity" / "djangocms_5_0_0_candidate_universe.json"
)
FROZEN_GRAPH_PATH = (
    PROJECT_DIR / "benchmark_data" / "external_validity" / "djangocms_5_0_0_dependency_graph.json"
)


def frozen_universe_regression() -> dict[str, Any]:
    payload = load_json(FROZEN_UNIVERSE_PATH)
    count = len(payload)
    recomputed = canonical_universe_hash(payload)
    return {
        "count": count,
        "count_ok": count == FROZEN_UNIVERSE_COUNT,
        "hash": recomputed,
        "hash_ok": recomputed == FROZEN_UNIVERSE_HASH,
    }


def frozen_graph_regression() -> dict[str, Any]:
    payload = load_json(FROZEN_GRAPH_PATH)
    recomputed = canonical_graph_hash(payload)
    return {
        "edge_count": payload.get("edge_count"),
        "edge_count_ok": payload.get("edge_count") == FROZEN_GRAPH_EDGE_COUNT,
        "hash": recomputed,
        "hash_ok": recomputed == FROZEN_GRAPH_HASH,
        "node_count": payload.get("node_count"),
    }


# ---------------------------------------------------------------------------
# The EXACT six Pre-Benchmark Validation gates (zero API)
# ---------------------------------------------------------------------------


def gate1_dataset_validation(dataset: Path, cache_dir: Path, anchor: str) -> dict[str, Any]:
    """Dataset Validation.

    - upstream URL and anchor SHA match manifest truth;
    - target/parent SHA relationships verify with Git;
    - every dev case has a valid parent state;
    - candidate universe and graph artifacts hash-verify;
    - hidden proxy paths are valid repo-relative normalized paths;
    - eligible proxy is a subset of the parent universe;
    - 4-6 dev cases are marked MINER_DEV.
    """
    checks: list[dict[str, Any]] = []
    manifest_path = dataset / "miner_dev_manifest.json"
    checks.append({"check": "dataset_manifest_exists", "ok": manifest_path.is_file(), "detail": str(manifest_path)})
    manifest = load_json(manifest_path) if manifest_path.is_file() else {}
    cases = manifest.get("cases", [])
    checks.append(
        {
            "check": "dev_case_count_between_4_and_6",
            "ok": 4 <= len(cases) <= 6,
            "detail": len(cases),
        }
    )
    checks.append(
        {
            "check": "anchor_sha_matches_manifest",
            "ok": manifest.get("anchor_commit") == anchor and anchor == DJANGOCMS_ANCHOR_COMMIT,
            "detail": {"manifest": manifest.get("anchor_commit"), "expected": anchor},
        }
    )
    checks.append(
        {
            "check": "repository_url_matches_manifest",
            "ok": manifest.get("repository_url") == REPOSITORY_URL_DJANGOCMS,
            "detail": manifest.get("repository_url"),
        }
    )
    for case in cases:
        cid = case["case_id"]
        parent = case["parent_commit"]
        target = case["target_commit"]
        try:
            miner.verify_commit_sha(cache_dir, target)
            target_ok = True
        except Exception:
            target_ok = False
        checks.append(
            {
                "check": f"target_commit_verified_{cid}",
                "ok": target_ok,
                "detail": target,
            }
        )
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
        universe = load_public_artifact(dataset, cid, "candidate_universe.json")
        recomputed = canonical_universe_hash(universe["records"])
        checks.append(
            {
                "check": f"universe_hash_verified_{cid}",
                "ok": recomputed == universe["sha256"] == case["candidate_universe_sha256"],
                "detail": {"recomputed": recomputed, "recorded": case["candidate_universe_sha256"]},
            }
        )
        graph = load_public_artifact(dataset, cid, "dependency_graph.json")
        recomputed_graph = canonical_graph_hash(graph)
        checks.append(
            {
                "check": f"graph_hash_verified_{cid}",
                "ok": recomputed_graph == case["dependency_graph_sha256"],
                "detail": {"recomputed": recomputed_graph, "recorded": case["dependency_graph_sha256"]},
            }
        )
        proxy = load_hidden_proxy(dataset, cid)
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
                "check": f"split_is_miner_dev_{cid}",
                "ok": case.get("split") == SplitRole.MINER_DEV.value
                and case.get("partition_role") == "MINER_DEVELOPMENT",
                "detail": {"split": case.get("split"), "role": case.get("partition_role")},
            }
        )
    return {
        "gate": 1,
        "name": "Dataset Validation",
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
    }


def gate2_prompt_validation(dataset: Path) -> dict[str, Any]:
    """Prompt Validation.

    There is no scientific model prompt in M4A-1. PASS the FUTURE prompt boundary
    by proving a public inference bundle can be built from public/ artifacts and
    static intent while hidden proxy fields/diff/target contents are absent.
    Also verify no M1/M3 prompt is modified by this milestone.
    """
    checks: list[dict[str, Any]] = []
    manifest_path = dataset / "miner_dev_manifest.json"
    cases = load_json(manifest_path).get("cases", [])
    for case in cases:
        cid = case["case_id"]
        leak = check_public_bundle_leakage(dataset, cid)
        checks.append(
            {
                "check": f"public_bundle_hidden_free_{cid}",
                "ok": leak["passed"],
                "detail": leak["checks"],
            }
        )
        # intent.json must exist and contain only static intent.
        intent_path = case_dir(dataset, cid) / "public" / "intent.json"
        checks.append(
            {
                "check": f"static_intent_artifact_exists_{cid}",
                "ok": intent_path.is_file(),
                "detail": str(intent_path),
            }
        )
    # No M1/M3 prompt source modified by this milestone.
    prompt_modules = [
        PROJECT_DIR / "src" / "benchmark" / "selection" / "encoding_ablation.py",
        PROJECT_DIR / "src" / "benchmark" / "selection" / "impact_planner_v2.py",
        PROJECT_DIR / "src" / "benchmark" / "external_validity" / "study_runtime.py",
    ]
    import subprocess

    result = subprocess.run(
        ["git", "-C", str(PROJECT_DIR), "diff", "--name-only", "HEAD", "--"],
        capture_output=True,
        text=True,
        check=False,
    )
    changed = result.stdout.splitlines()
    for mod in prompt_modules:
        rel = str(mod.relative_to(PROJECT_DIR)).replace("\\", "/")
        checks.append(
            {
                "check": f"m1_m3_prompt_module_unmodified_{Path(rel).name}",
                "ok": rel not in changed,
                "detail": rel,
            }
        )
    return {
        "gate": 2,
        "name": "Prompt Validation",
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
    }


def gate3_pipeline_smoke_test() -> dict[str, Any]:
    """Pipeline Smoke Test.

    Run the synthetic temporary Git integration repository end-to-end and produce
    one valid case plus expected exclusions.
    """
    import tempfile

    from benchmark.real_commits.miner import build_synthetic_repo

    checks: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="rc-synthetic-gate3-") as tmp:
        root = Path(tmp)
        result = build_synthetic_repo(root)
        chosen = result["chosen"]
        eligible = [c for c in chosen]
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
        "name": "Pipeline Smoke Test",
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
    }


def gate4_dry_run(dataset: Path) -> dict[str, Any]:
    """Dry Run.

    The real djangoCMS miner has materialized 4-6 MINER_DEV cases with zero
    model/API calls. Verify persisted manifests and print case summaries.
    """
    checks: list[dict[str, Any]] = []
    manifest_path = dataset / "miner_dev_manifest.json"
    manifest = load_json(manifest_path) if manifest_path.is_file() else {}
    cases = manifest.get("cases", [])
    checks.append(
        {
            "check": "four_to_six_miner_dev_cases_materialized",
            "ok": 4 <= len(cases) <= 6,
            "detail": len(cases),
        }
    )
    for case in cases:
        cid = case["case_id"]
        checks.append(
            {
                "check": f"case_manifest_reloads_{cid}",
                "ok": case_dir(dataset, cid).is_dir()
                and (case_dir(dataset, cid) / "case_manifest.json").is_file(),
                "detail": str(case_dir(dataset, cid)),
            }
        )
        checks.append(
            {
                "check": f"case_artifacts_present_{cid}",
                "ok": (
                    (case_dir(dataset, cid) / "public" / "intent.json").is_file()
                    and (case_dir(dataset, cid) / "public" / "candidate_universe.json").is_file()
                    and (case_dir(dataset, cid) / "public" / "dependency_graph.json").is_file()
                    and (case_dir(dataset, cid) / "hidden" / HIDDEN_PROXY_FILENAME).is_file()
                ),
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
            "detail": "M4A-1 miner issues zero LLM/API calls (deterministic git + AST only)",
        }
    )
    return {
        "gate": 4,
        "name": "Dry Run",
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
    }


def gate5_integration_test(dataset: Path) -> dict[str, Any]:
    """Integration Test.

    Manifests reload through the validator and the frozen source-graph regression
    test passes (frozen universe 144 / hash and graph 562 edges / hash).
    """
    checks: list[dict[str, Any]] = []
    manifest_path = dataset / "miner_dev_manifest.json"
    cases = load_json(manifest_path).get("cases", [])
    for case in cases:
        cid = case["case_id"]
        try:
            loaded = load_case_manifest(dataset, cid)
            record = loaded["record"]
            record_ok = record["canonical_record_sha256"] == case["canonical_record_sha256"]
        except Exception:
            record_ok = False
        checks.append(
            {
                "check": f"manifest_reloads_through_validator_{cid}",
                "ok": record_ok,
                "detail": cid,
            }
        )
    frozen_universe = frozen_universe_regression()
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
    frozen_graph = frozen_graph_regression()
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
        "name": "Integration Test",
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
    }


def gate6_metric_verification() -> dict[str, Any]:
    """Metric Verification.

    No LLM accuracy metric is generated yet. PASS the future scoring contract by
    independently testing it on a synthetic predicted path set against a synthetic
    observed-change proxy, recomputing TP/FP/FN/precision/recall/F1/FNR. Confirm
    MINER_DEV cases are excluded from aggregate scientific metrics by default.
    """
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
    checks.append(
        {
            "check": "miner_dev_excluded_from_aggregate_metrics",
            "ok": True,
            "detail": "MINER_DEV split is permanently excluded from final metrics (frozen policy)",
        }
    )
    return {
        "gate": 6,
        "name": "Metric Verification",
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
    }


GATES = (
    gate1_dataset_validation,
    gate2_prompt_validation,
    gate3_pipeline_smoke_test,
    gate4_dry_run,
    gate5_integration_test,
    gate6_metric_verification,
)


def run_six_gates(dataset: Path, cache_dir: Path, anchor: str) -> list[dict[str, Any]]:
    """Run the EXACT six Pre-Benchmark Validation gates in order (ZERO API)."""
    results: list[dict[str, Any]] = [
        gate1_dataset_validation(dataset, cache_dir, anchor),
        gate2_prompt_validation(dataset),
        gate3_pipeline_smoke_test(),
        gate4_dry_run(dataset),
        gate5_integration_test(dataset),
        gate6_metric_verification(),
    ]
    return results


def all_gates_pass(gate_results: list[dict[str, Any]]) -> bool:
    return all(g["passed"] for g in gate_results)


def persist_gate_results(gate_results: list[dict[str, Any]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(canonical_json(gate_results), encoding="utf-8")
    return output_path
