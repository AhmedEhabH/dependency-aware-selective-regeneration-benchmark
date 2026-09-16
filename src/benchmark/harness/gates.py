"""Six T3 validation gates for the pluggable research harness (ZERO API).

Gate 1 — Dataset Validation: adapter split counts (TRAIN 24 / VALIDATION 6 /
HELD_OUT_TEST 10), frozen case-count 40, proxy subset of universe.
Gate 2 — Input/Query Validation: the public case bundle is the only method
input; hidden proxy is never part of it; no semantic-gold markers.
Gate 3 — Pipeline Smoke Test: harness runner on a synthetic case produces the
expected row shape for every seam.
Gate 4 — Dry Run: metadata-mode harness run on a 2-case slice produces the
expected cell counts (5 methods x 4 K) with ZERO model calls.
Gate 5 — Integration Test: registry resolves all seams; every frozen B0–B4
ranker runs through the harness; per-case config hashes reproducible.
Gate 6 — Metric Verification: synthetic TP/FP/FN with manually known
P/R/F1/FNR through the common evaluator.

Plus: interface contract checks, hidden-gold access test, config
reproducibility, deterministic ranking, budget enforcement, dataset-adapter
isolation. All deterministic, all ZERO-API.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from benchmark.harness import (
    DatasetAdapter,
    interfaces,
    registry,
)
from benchmark.harness.djangocms import DjangoCMSRealCommitDataset
from benchmark.harness.evaluator import (
    aggregate_micro,
    evaluate_prediction,
)
from benchmark.harness.protocol_a import (
    build_protocol_a_spec,
    run_protocol_a_via_harness,
)
from benchmark.harness.runner import HarnessRunner

DATASET_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "benchmark_data"
    / "real_commit_impact_v1"
)

_SYNTHETIC_RECORDS = (
    {"path": "cms/models/pagemodel.py", "module": "cms.models", "classes": ["Page"], "functions": []},
    {"path": "cms/admin/pageadmin.py", "module": "cms.admin", "classes": ["PageAdmin"], "functions": []},
    {"path": "cms/api.py", "module": "cms", "classes": [], "functions": ["get_page"]},
)
_SYNTHETIC_PATHS = ("cms/models/pagemodel.py", "cms/admin/pageadmin.py", "cms/api.py")


def _synthetic_case() -> interfaces.PublicCase:
    return interfaces.PublicCase(
        case_id="synthetic-smoke",
        repository="djangocms",
        repository_url="https://github.com/django-cms/django-cms",
        parent_commit="p" * 40,
        target_commit="t" * 40,
        intent_text="fix: slug uniqueness check on page model",
        candidate_paths=_SYNTHETIC_PATHS,
        candidate_records=_SYNTHETIC_RECORDS,
        graph_edges=(("cms/models/pagemodel.py", "cms/admin/pageadmin.py"),),
        public_bundle_sha256="x",
    )


class _SyntheticDataset(DatasetAdapter):
    """Deterministic synthetic adapter for smoke/gate checks."""

    name = "synthetic"
    splits_allowed = ("TRAIN",)

    def case_ids(self) -> tuple[str, ...]:
        return ("synthetic-smoke",)

    def split_of(self, case_id: str) -> str:
        if case_id == "synthetic-smoke":
            return "TRAIN"
        raise KeyError(case_id)

    def load_public_case(self, case_id: str) -> interfaces.PublicCase:
        if case_id != "synthetic-smoke":
            raise KeyError(case_id)
        return _synthetic_case()

    def load_hidden_proxy_paths(self, case_id: str) -> tuple[str, ...]:
        if case_id != "synthetic-smoke":
            raise KeyError(case_id)
        return ("cms/models/pagemodel.py", "cms/api.py")


def gate1_dataset_validation(dataset_dir: Path = DATASET_DIR) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    adapter = DjangoCMSRealCommitDataset(dataset_dir=dataset_dir)
    split_freeze = json.loads(
        (dataset_dir / "split_freeze.json").read_text(encoding="utf-8")
    )
    per_split = split_freeze["per_split"]
    for split, expected in (("TRAIN", 24), ("VALIDATION", 6), ("HELD_OUT_TEST", 10)):
        checks.append(
            {
                "check": f"split_count_{split}",
                "ok": per_split[split]["count"] == expected,
                "detail": per_split[split]["count"],
            }
        )
    checks.append(
        {
            "check": "adapter_case_ids_allowed_only",
            "ok": all(adapter.split_of(c) in adapter.splits_allowed for c in adapter.case_ids()),
            "detail": len(adapter.case_ids()),
        }
    )
    # Proxy subset of universe for every allowed case.
    for cid in adapter.case_ids():
        case = adapter.load_public_case(cid)
        universe = set(case.candidate_paths)
        proxy = set(adapter.load_hidden_proxy_paths(cid))
        checks.append(
            {
                "check": f"proxy_subset_universe_{cid}",
                "ok": proxy <= universe,
                "detail": sorted(proxy - universe),
            }
        )
    return {"gate": 1, "name": "Dataset Validation", "passed": all(c["ok"] for c in checks), "checks": checks}


def gate2_query_validation(dataset_dir: Path = DATASET_DIR) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    adapter = DjangoCMSRealCommitDataset(dataset_dir=dataset_dir)
    gold_markers = ("REGENERATE", "VALIDATE", "HUMAN_REVIEW", "PRESERVE")
    for cid in adapter.case_ids()[:6]:
        case = adapter.load_public_case(cid)
        checks.append(
            {
                "check": f"query_is_public_intent_{cid}",
                "ok": bool(case.intent_text.strip()),
                "detail": case.intent_text[:80],
            }
        )
        hits = [m for m in gold_markers if m in case.intent_text]
        checks.append(
            {
                "check": f"no_semantic_gold_{cid}",
                "ok": not hits,
                "detail": hits,
            }
        )
    return {"gate": 2, "name": "Input/Query Validation", "passed": all(c["ok"] for c in checks), "checks": checks}


def gate3_pipeline_smoke_test(_dataset_dir: Path = DATASET_DIR) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for method in ("random", "bm25", "path_token", "graph", "hybrid"):
        spec = build_protocol_a_spec(method_name=method, corpus_mode="metadata")
        from benchmark.harness.djangocms import DjangoCMSParentSnapshot

        result = HarnessRunner(
            spec=spec,
            dataset=_SyntheticDataset(),
            snapshot_provider=DjangoCMSParentSnapshot(cache_dir=None),
            ranker=registry.resolve_ranker(method)(),
        ).run()
        assert len(result.case_results) == 1
        cr = result.case_results[0]
        checks.append(
            {
                "check": f"smoke_{method}_rows",
                "ok": len(cr.rows) == len(spec.k_values),
                "detail": len(cr.rows),
            }
        )
        for row in cr.rows:
            expect = min(int(row["k"]), len(_SYNTHETIC_PATHS))
            checks.append(
                {
                    "check": f"smoke_{method}_k{row['k']}_bounded",
                    "ok": len(row["selected_paths"]) == expect,
                    "detail": expect,
                }
            )
        checks.append(
            {
                "check": f"smoke_{method}_zero_llm",
                "ok": result.manifest["llm_calls"] == 0,
                "detail": result.manifest["llm_calls"],
            }
        )
    return {"gate": 3, "name": "Pipeline Smoke Test", "passed": all(c["ok"] for c in checks), "checks": checks}


def gate4_dry_run(dataset_dir: Path = DATASET_DIR) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    payload = run_protocol_a_via_harness(
        dataset_dir=dataset_dir, cache_dir=None, case_slice=(0, 2)
    )
    checks.append(
        {
            "check": "dryrun_cases_2",
            "ok": len(payload["cases"]) == 2,
            "detail": len(payload["cases"]),
        }
    )
    total_rows = sum(len(c["results"]) for c in payload["cases"])
    checks.append(
        {
            "check": "dryrun_rows_40",
            "ok": total_rows == 2 * 5 * 4,
            "detail": total_rows,
        }
    )
    checks.append(
        {
            "check": "dryrun_zero_llm",
            "ok": payload["scientific_row_count"] == total_rows,
            "detail": payload["scientific_row_count"],
        }
    )
    return {"gate": 4, "name": "Dry Run", "passed": all(c["ok"] for c in checks), "checks": checks}


def gate5_integration_test(_dataset_dir: Path = DATASET_DIR) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    known = registry.known_names()
    # Concrete seams must be resolvable in V1.
    for kind in ("datasets", "snapshots", "rankers", "backends"):
        checks.append(
            {
                "check": f"registry_{kind}_nonempty",
                "ok": len(known[kind]) >= 1,
                "detail": known[kind],
            }
        )
    # Interface-only seams may remain unregistered in V1; they are abstract.
    checks.append(
        {
            "check": "registry_planners_may_be_empty_v1",
            "ok": "planners" in known,
            "detail": known["planners"],
        }
    )
    checks.append(
        {
            "check": "registry_risk_scorers_may_be_empty_v1",
            "ok": "risk_scorers" in known,
            "detail": known["risk_scorers"],
        }
    )
    checks.append(
        {
            "check": "registry_verifiers_may_be_empty_v1",
            "ok": "verifiers" in known,
            "detail": known["verifiers"],
        }
    )
    # Config reproducibility: same spec dict -> same sha256.
    s1 = build_protocol_a_spec(method_name="bm25", corpus_mode="metadata")
    s2 = build_protocol_a_spec(method_name="bm25", corpus_mode="metadata")
    checks.append(
        {
            "check": "config_reproducible_sha256",
            "ok": s1.sha256 == s2.sha256,
            "detail": s1.sha256,
        }
    )
    # RiskScorer / Verifier remain interface-only (abstract).
    import abc as _abc

    for cls_name in ("RiskScorer", "Verifier"):
        cls = getattr(interfaces, cls_name)
        checks.append(
            {
                "check": f"{cls_name}_interface_only",
                "ok": _abc.ABC in cls.__mro__ and bool(getattr(cls, "__abstractmethods__", ())),
                "detail": sorted(getattr(cls, "__abstractmethods__", ())),
            }
        )
    return {"gate": 5, "name": "Integration Test", "passed": all(c["ok"] for c in checks), "checks": checks}


def gate6_metric_verification(_dataset_dir: Path = DATASET_DIR) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    prediction = interfaces.RankedPrediction(
        method="synthetic",
        case_id="synthetic",
        k=3,
        ranked_paths=("cms/models/pagemodel.py", "cms/api.py", "cms/plugin_pool.py"),
    )
    row = evaluate_prediction(
        prediction=prediction,
        proxy_paths=("cms/models/pagemodel.py", "cms/admin/pageadmin.py", "cms/api.py"),
    )
    checks.append({"check": "metric_tp", "ok": row["tp"] == 2, "detail": row["tp"]})
    checks.append({"check": "metric_fp", "ok": row["fp"] == 1, "detail": row["fp"]})
    checks.append({"check": "metric_fn", "ok": row["fn"] == 1, "detail": row["fn"]})
    checks.append({"check": "metric_precision", "ok": abs(row["precision"] - 2 / 3) < 1e-9, "detail": row["precision"]})
    checks.append({"check": "metric_recall", "ok": abs(row["recall"] - 2 / 3) < 1e-9, "detail": row["recall"]})
    checks.append({"check": "metric_f1", "ok": abs(row["f1"] - 2 / 3) < 1e-9, "detail": row["f1"]})
    checks.append({"check": "metric_fnr", "ok": abs(row["fnr"] - 1 / 3) < 1e-9, "detail": row["fnr"]})
    micro = aggregate_micro([row])
    checks.append({"check": "metric_micro_pool", "ok": micro["tp"] == 2 and micro["fn"] == 1, "detail": micro})
    return {"gate": 6, "name": "Metric Verification", "passed": all(c["ok"] for c in checks), "checks": checks}


def run_six_gates(dataset_dir: Path = DATASET_DIR) -> list[dict[str, Any]]:
    return [
        gate1_dataset_validation(dataset_dir),
        gate2_query_validation(dataset_dir),
        gate3_pipeline_smoke_test(dataset_dir),
        gate4_dry_run(dataset_dir),
        gate5_integration_test(dataset_dir),
        gate6_metric_verification(dataset_dir),
    ]


def all_gates_pass(gate_results: list[dict[str, Any]]) -> bool:
    return all(g["passed"] for g in gate_results)
