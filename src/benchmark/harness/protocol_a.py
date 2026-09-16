"""Protocol-A compatibility layer (V1).

Reproduces the current Protocol-A cheap-baseline outputs THROUGH the harness
seams (goal D). The frozen generators
(``benchmark.cheap_baselines``) are never rewritten; the harness drives the
same frozen rankers/corpora via the djangoCMS adapter. Scientific outputs
(ranked/selected paths + metrics) must be byte-identical to the frozen
persisted evidence ``research/cheap-baselines-v1/*.json``.

Wall-clock timing fields are inherently non-deterministic and are NOT part of
the scientific equivalence comparison.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from benchmark.harness.djangocms import (
    FROZEN_SEED,
    DjangoCMSParentSnapshot,
    DjangoCMSRealCommitDataset,
)
from benchmark.harness.interfaces import BudgetPolicy
from benchmark.harness.runner import HarnessRunner
from benchmark.harness.spec import ExperimentSpec

from . import interfaces, registry

PROTOCOL_A_ID: str = "protocol-a-cheap-nonllm-baselines-v1"
PROTOCOL_A_VERSION: str = "cheap-nonllm-baselines-v1"
FROZEN_K_VALUES: tuple[int, ...] = (1, 3, 5, 10)
FROZEN_METHODS: tuple[str, ...] = ("random", "bm25", "path_token", "graph", "hybrid")

# Mapping to the frozen cheap-baselines names used in persisted evidence.
FROZEN_BASELINE_KEYS: tuple[str, ...] = FROZEN_METHODS

# Per-baseline corpus_source labels exactly as recorded by the frozen runner
# (``cheap_baselines.runner._run_single_case`` metadata).
FROZEN_CORPUS_SOURCE_BY_METHOD: dict[str, str] = {
    "random": "seed",
    "path_token": "metadata",
    "graph": "graph",
}

SCIENTIFIC_ROW_FIELDS: tuple[str, ...] = (
    "case_id",
    "split",
    "baseline",
    "k",
    "ranked_paths",
    "selected_paths",
    "seed_reason",
    "corpus_source",
    "selected_count",
    "proxy_count",
    "tp",
    "fp",
    "fn",
    "precision",
    "recall",
    "f1",
    "fnr",
    "full_recall",
)


def build_protocol_a_spec(
    *,
    method_name: str,
    corpus_mode: str = "metadata",
    k_values: tuple[int, ...] = FROZEN_K_VALUES,
    seed: int = FROZEN_SEED,
) -> ExperimentSpec:
    """Build one frozen Protocol-A spec for a single method.

    Model/provider are configuration: Protocol A is zero-LLM, so the backend is
    the ``none`` backend and the model/provider names are empty markers.
    """
    if method_name not in FROZEN_METHODS:
        raise ValueError(
            f"unknown Protocol-A method {method_name!r}; expected one of {FROZEN_METHODS}"
        )
    if corpus_mode not in ("metadata", "parent_commit"):
        raise ValueError(f"corpus_mode must be 'metadata' or 'parent_commit', got {corpus_mode!r}")
    return ExperimentSpec(
        spec_id=f"{PROTOCOL_A_ID}:{method_name}:{corpus_mode}",
        protocol_version=PROTOCOL_A_VERSION,
        dataset_name="djangocms-real-commit-v1",
        repository="djangocms",
        method_name=method_name,
        model_name="",
        provider="none",
        k_values=k_values,
        splits_allowed=("TRAIN", "VALIDATION"),
        seed=seed,
        budget=BudgetPolicy(zero_llm=True),
        frozen_rules=(
            "TRAIN+VALIDATION only; HELD_OUT_TEST forbidden",
            "frozen seed 20260915",
            "frozen B0-B4 rules from cheap-baselines-v1",
            "zero LLM calls (backend=none)",
        ),
        notes="Protocol-A cheap non-LLM baseline reproduced through the harness (compat layer)",
    )


def _resolve_ranker(method_name: str) -> interfaces.Ranker:
    ranker_cls = registry.resolve_ranker(method_name)
    return ranker_cls()


def _method_key(method_name: str) -> str:
    """Return the frozen cheap-baselines baseline key (identity for V1)."""
    return method_name


def run_protocol_a_via_harness(
    *,
    dataset_dir: Path,
    cache_dir: Path | None = None,
    methods: tuple[str, ...] = FROZEN_METHODS,
    case_slice: tuple[int, int] | None = None,
) -> dict[str, Any]:
    """Run Protocol-A through the harness and return a frozen-shaped payload.

    Returns a dict with the same top-level structure as
    ``research/cheap-baselines-v1/raw_predictions_v1.json`` plus a
    ``per_task`` and ``aggregate`` view mirroring the run-script outputs.
    """
    dataset_dir = Path(dataset_dir)
    cache_dir = Path(cache_dir) if cache_dir is not None else None
    # The snapshot provider always exists; without a cache it builds the
    # metadata-only parent snapshot (matching the frozen runner's corpus_mode).
    snapshot = DjangoCMSParentSnapshot(cache_dir=cache_dir)
    corpus_mode = "parent_commit" if cache_dir is not None else "metadata"
    dataset = DjangoCMSRealCommitDataset(dataset_dir=dataset_dir)

    all_case_ids = dataset.case_ids()
    if case_slice is not None:
        lo, hi = case_slice
        case_ids = all_case_ids[lo:hi]
    else:
        case_ids = all_case_ids

    cases_payload: list[dict[str, Any]] = []
    per_task: dict[str, dict[str, dict[str, dict[str, Any]]]] = {}
    row_accumulator: list[dict[str, Any]] = []

    for cid in case_ids:
        split = dataset.split_of(cid)
        case = dataset.load_public_case(cid)
        case_rows: list[dict[str, Any]] = []
        case_proxy: tuple[str, ...] = ()
        case_source = "none"
        for method in methods:
            spec = build_protocol_a_spec(method_name=method, corpus_mode=corpus_mode)
            # Run the runner for exactly this case by wrapping the dataset.
            single_case_dataset = _SingleCaseAdapter(dataset, cid)
            result = HarnessRunner(
                spec=spec,
                dataset=single_case_dataset,
                snapshot_provider=snapshot,
                ranker=_resolve_ranker(method),
            ).run()
            assert len(result.case_results) == 1
            cr = result.case_results[0]
            case_proxy = cr.proxy_paths
            case_source = cr.corpus_source
            for row in cr.rows:
                baseline = _method_key(method)
                seed_reason = str(row["metadata"].get("seed_reason", ""))
                row_source = FROZEN_CORPUS_SOURCE_BY_METHOD.get(
                    method, cr.corpus_source
                )
                case_rows.append(
                    {
                        "case_id": cid,
                        "split": split,
                        "baseline": baseline,
                        "k": row["k"],
                        "ranked_paths": row["ranked_paths"],
                        "selected_paths": row["selected_paths"],
                        "seed_reason": seed_reason,
                        "corpus_source": row_source,
                        "selected_count": row["selected_count"],
                        "proxy_count": row["proxy_count"],
                        "tp": row["tp"],
                        "fp": row["fp"],
                        "fn": row["fn"],
                        "precision": row["precision"],
                        "recall": row["recall"],
                        "f1": row["f1"],
                        "fnr": row["fnr"],
                        "full_recall": row["full_recall"],
                    }
                )
        cases_payload.append(
            {
                "case_id": cid,
                "split": split,
                "intent_text": case.intent_text,
                "candidate_paths": list(case.candidate_paths),
                "proxy_paths": list(case_proxy),
                "corpus_source": case_source,
                "config_hash": spec.sha256,
                "results": case_rows,
            }
        )
        row_accumulator.extend(case_rows)

    # per_task view (mirrors per_task_metrics_v1.json scientific subset).
    for row in row_accumulator:
        per_task.setdefault(row["case_id"], {}).setdefault(row["baseline"], {})[
            str(row["k"])
        ] = {
            "tp": row["tp"],
            "fp": row["fp"],
            "fn": row["fn"],
            "precision": row["precision"],
            "recall": row["recall"],
            "f1": row["f1"],
            "fnr": row["fnr"],
            "selected_count": row["selected_count"],
            "proxy_count": row["proxy_count"],
            "seed_reason": row["seed_reason"],
        }

    aggregate = _aggregate_from_rows(row_accumulator)

    return {
        "protocol_version": PROTOCOL_A_VERSION,
        "dataset_authority": "benchmark_data/real_commit_impact_v1",
        "reference": "observed changed-production-Python proxy within U_t",
        "predicted_positive": "selected file (top-K ranked)",
        "cases": cases_payload,
        "per_task": per_task,
        "aggregate": aggregate,
        "scientific_row_count": len(row_accumulator),
        "corpus_mode": corpus_mode,
    }


class _SingleCaseAdapter(interfaces.DatasetAdapter):
    """Adapter view exposing exactly one case (used by the compat driver)."""

    name = "_single_case_adapter"

    def __init__(
        self,
        dataset: interfaces.DatasetAdapter,
        case_id: str,
    ) -> None:
        self._dataset = dataset
        self._case_id = case_id

    def case_ids(self) -> tuple[str, ...]:
        return (self._case_id,)

    def split_of(self, case_id: str) -> str:
        return self._dataset.split_of(case_id)

    def load_public_case(self, case_id: str) -> interfaces.PublicCase:
        return self._dataset.load_public_case(case_id)

    def load_hidden_proxy_paths(self, case_id: str) -> tuple[str, ...]:
        return self._dataset.load_hidden_proxy_paths(case_id)


def _aggregate_from_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Recompute split-grouped micro/macro aggregates (mirrors run script)."""
    from benchmark.harness import evaluator as h_eval

    split_groups: dict[str, list[dict[str, Any]]] = {
        "TRAIN": [],
        "VALIDATION": [],
        "TRAIN_VALIDATION": [],
    }
    for row in rows:
        if row["split"] == "TRAIN":
            split_groups["TRAIN"].append(row)
            split_groups["TRAIN_VALIDATION"].append(row)
        elif row["split"] == "VALIDATION":
            split_groups["VALIDATION"].append(row)
            split_groups["TRAIN_VALIDATION"].append(row)
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for group, group_rows in split_groups.items():
        out[group] = {}
        for baseline in FROZEN_METHODS:
            out[group][baseline] = {}
            for k in FROZEN_K_VALUES:
                krows = [
                    r
                    for r in group_rows
                    if r["baseline"] == baseline and r["k"] == k
                ]
                out[group][baseline][str(k)] = {
                    "micro": h_eval.aggregate_micro(krows),
                    "macro": h_eval.aggregate_macro(krows),
                }
    return out


def scientific_projection(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract the deterministic scientific projection from a payload.

    Timing fields are excluded; everything that must be byte-identical across
    runs is kept.
    """
    out: dict[str, Any] = {"cases": []}
    for case in payload["cases"]:
        crows = []
        for row in case["results"]:
            crows.append(
                {
                    "case_id": row["case_id"],
                    "split": row["split"],
                    "baseline": row["baseline"],
                    "k": row["k"],
                    "ranked_paths": row["ranked_paths"],
                    "selected_paths": row["selected_paths"],
                    "seed_reason": row["seed_reason"],
                    "corpus_source": row["corpus_source"],
                    "selected_count": row["selected_count"],
                    "proxy_count": row["proxy_count"],
                    "tp": row["tp"],
                    "fp": row["fp"],
                    "fn": row["fn"],
                    "precision": row["precision"],
                    "recall": row["recall"],
                    "f1": row["f1"],
                    "fnr": row["fnr"],
                    "full_recall": row["full_recall"],
                }
            )
        out["cases"].append({"case_id": case["case_id"], "results": crows})
    out["per_task"] = payload["per_task"]
    out["aggregate"] = payload["aggregate"]
    return out


def compare_to_frozen(
    harness_payload: dict[str, Any],
    frozen_raw_path: Path,
    *,
    case_ids: tuple[str, ...] | None = None,
) -> list[str]:
    """Return a list of mismatches between harness output and frozen evidence.

    Empty list = scientific equivalence for the compared cases. Compares the
    full scientific projection per (case, baseline, k): ranked/selected paths,
    seed_reason, corpus_source, and all TP/FP/FN/P/R/F1/FNR metrics.
    """
    frozen = json.loads(Path(frozen_raw_path).read_text(encoding="utf-8"))
    frozen_cases = {c["case_id"]: c for c in frozen["cases"]}
    harness_cases = {c["case_id"]: c for c in harness_payload["cases"]}
    errors: list[str] = []
    compare_ids = (
        tuple(sorted(harness_cases)) if case_ids is None else tuple(sorted(case_ids))
    )
    for cid in compare_ids:
        if cid not in frozen_cases:
            errors.append(f"case {cid} absent from frozen evidence")
            continue
        if cid not in harness_cases:
            errors.append(f"case {cid} absent from harness output")
            continue
        frows = {
            (r["baseline"], r["k"]): r
            for r in frozen_cases[cid]["results"]
        }
        hrows = {
            (r["baseline"], r["k"]): r
            for r in harness_cases[cid]["results"]
        }
        for key in sorted(set(frows) | set(hrows)):
            fr = frows.get(key)
            hr = hrows.get(key)
            if fr is None or hr is None:
                errors.append(f"case {cid} {key}: row present in only one side")
                continue
            for field in SCIENTIFIC_ROW_FIELDS:
                if field == "case_id":
                    continue
                if fr.get(field) != hr.get(field):
                    errors.append(
                        f"case {cid} {key} field {field!r}: frozen={fr.get(field)!r} "
                        f"harness={hr.get(field)!r}"
                    )
    return errors
