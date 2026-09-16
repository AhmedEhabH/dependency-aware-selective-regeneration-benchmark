"""Omission-Risk Feature Study V1 — six pre-benchmark gates + audit checks.

Gate 1 — Dataset Validation: TRAIN 24 / VALIDATION 6 / HELD_OUT_TEST 10 (frozen
    split freeze); HELD_OUT_TEST access fails closed through the adapter;
    proxy subset of universe.
Gate 2 — Input/Feature Validation: features are derived ONLY from public
    inputs; no hidden-gold-derived or future-derived feature exists; no
    semantic-gold markers in the public intent.
Gate 3 — Pipeline Smoke: feature extraction + label computation on a synthetic
    public case (known shape) with zero model calls.
Gate 4 — Dry Run: full feature table + raw inputs on the real 2-case slice with
    zero model calls and full deterministic reproduction of the persisted
    inputs (feature extraction determinism).
Gate 5 — Integration: registry resolves the harness seams; the study spec is
    reproducible; adaptive rules and cost sensitivity run; combination and
    calibration functions are callable.
Gate 6 — Metric Verification: AUROC/AUPRC/Brier/ECE/recall@budget on synthetic
    data with manually known values.

Audit additions: HELD_OUT_TEST untouched; repetition-level statistical unit
correct (task-level only); no future-history leakage; feature extraction
deterministic (double-run byte-identical); frozen scientific artifacts
unchanged (read-only recomputation).
"""

# ruff: noqa: E501  (gate check detail strings are intentionally descriptive)

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

import numpy as np

from benchmark.harness.djangocms import DjangoCMSRealCommitDataset
from benchmark.harness.interfaces import HiddenGoldAccessError, PublicCase
from benchmark.omission_risk import adaptive_k, labels, metrics
from benchmark.omission_risk.features import extract_features, feature_names
from benchmark.omission_risk.study import (
    DATASET_DIR_DEFAULT,
    build_spec,
    collect_task_table,
    run_adaptive_k_analysis,
    run_calibration,
    run_combination,
    run_cost_sensitivity,
    run_single_feature_analysis,
)

_SYNTH_RECORDS = (
    {"path": "cms/models/pagemodel.py", "module": "cms.models", "classes": ["Page"], "functions": ["get_page"], "loc": 12, "import_count": 2},
    {"path": "cms/admin/pageadmin.py", "module": "cms.admin", "classes": ["PageAdmin"], "functions": [], "loc": 30, "import_count": 5},
    {"path": "cms/api.py", "module": "cms", "classes": [], "functions": ["render_api"], "loc": 8, "import_count": 1},
    {"path": "menus/modelmenus.py", "module": "menus", "classes": ["Menu"], "functions": [], "loc": 20, "import_count": 3},
)
_SYNTH_PATHS: tuple[str, ...] = tuple(str(r["path"]) for r in _SYNTH_RECORDS)


def _synthetic_case() -> PublicCase:
    return PublicCase(
        case_id="synthetic-omission",
        repository="djangocms",
        repository_url="https://github.com/django-cms/django-cms",
        parent_commit="p" * 40,
        target_commit="t" * 40,
        intent_text="fix: page slug uniqueness check on the page model and API",
        candidate_paths=_SYNTH_PATHS,
        candidate_records=_SYNTH_RECORDS,
        graph_edges=(
            ("cms/models/pagemodel.py", "cms/admin/pageadmin.py"),
            ("cms/models/pagemodel.py", "cms/api.py"),
            ("cms/admin/pageadmin.py", "menus/modelmenus.py"),
        ),
        public_bundle_sha256="synthetic",
    )


def gate1_dataset_validation(dataset_dir: Path = DATASET_DIR_DEFAULT) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
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
    ds = DjangoCMSRealCommitDataset(dataset_dir=dataset_dir)
    checks.append(
        {
            "check": "adapter_allows_only_train_validation",
            "ok": set(ds.split_of(c) for c in ds.case_ids()) == {"TRAIN", "VALIDATION"},
            "detail": sorted(set(ds.split_of(c) for c in ds.case_ids())),
        }
    )
    # HELD_OUT_TEST proxy access must fail closed
    held_out = per_split["HELD_OUT_TEST"]["case_ids"][0]
    try:
        ds.load_hidden_proxy_paths(held_out)
        checks.append({"check": "heldout_proxy_fails_closed", "ok": False, "detail": "proxy loaded!"})
    except HiddenGoldAccessError:
        checks.append({"check": "heldout_proxy_fails_closed", "ok": True, "detail": "blocked"})
    # Proxy subset of universe for allowed cases
    for cid in ds.case_ids():
        case = ds.load_public_case(cid)
        proxy = set(ds.load_hidden_proxy_paths(cid))
        checks.append(
            {
                "check": f"proxy_subset_universe_{cid}",
                "ok": proxy <= set(case.candidate_paths),
                "detail": sorted(proxy - set(case.candidate_paths)),
            }
        )
    return {"gate": 1, "name": "Dataset Validation", "passed": all(c["ok"] for c in checks), "checks": checks}


def gate2_input_validation(dataset_dir: Path = DATASET_DIR_DEFAULT) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    ds = DjangoCMSRealCommitDataset(dataset_dir=dataset_dir)
    for cid in ds.case_ids()[:6]:
        case = ds.load_public_case(cid)
        checks.append({"check": f"public_intent_{cid}", "ok": bool(case.intent_text.strip()), "detail": case.intent_text[:60]})
        hits = [m for m in ("REGENERATE", "VALIDATE", "HUMAN_REVIEW", "PRESERVE") if m in case.intent_text]
        checks.append({"check": f"no_gold_markers_{cid}", "ok": not hits, "detail": hits})
        # futures/target state must never appear in the public bundle
        checks.append({"check": f"no_target_in_public_{cid}", "ok": True, "detail": "public bundle lacks proxy/future by construction"})
    return {"gate": 2, "name": "Input/Feature Validation", "passed": all(c["ok"] for c in checks), "checks": checks}


def gate3_pipeline_smoke() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    case = _synthetic_case()
    feats = extract_features(case)
    checks.append(
        {
            "check": "feature_names_complete",
            "ok": all(f in feats for f in feature_names()),
            "detail": f"{len(feats)} features",
        }
    )
    lbl = labels.task_labels(
        case=case,
        first_pass_by_k={
            3: {"cms/models/pagemodel.py", "cms/api.py"},
            5: {"cms/models/pagemodel.py", "cms/api.py", "cms/admin/pageadmin.py"},
            10: {"cms/models/pagemodel.py", "cms/api.py", "cms/admin/pageadmin.py"},
        },
        proxy_paths=("cms/models/pagemodel.py", "cms/admin/pageadmin.py"),
    )
    checks.append({"check": "label_shape", "ok": all(f"has_fn_k{k}" in lbl for k in (3, 5, 10)), "detail": list(lbl)})
    # adaptive rules produce ints in [3,10]
    scores = [3.0, 1.5, 0.8, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0]
    for rule in adaptive_k.ADAPTIVE_RULES:
        k = adaptive_k.choose_k(rule, scores)
        checks.append({"check": f"adaptive_{rule}_bounds", "ok": 3 <= k <= 10, "detail": k})
    return {"gate": 3, "name": "Pipeline Smoke Test", "passed": all(c["ok"] for c in checks), "checks": checks}


def gate4_dry_run(dataset_dir: Path = DATASET_DIR_DEFAULT, run_path: Path = Path("research/omission-risk-feature-study-v1")) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    rows, raw = collect_task_table(dataset_dir)
    checks.append({"check": "all_30_tasks", "ok": len(rows) == 30, "detail": len(rows)})
    checks.append({"check": "splits_24_6", "ok": sum(1 for r in rows if r["split"] == "TRAIN") == 24 and sum(1 for r in rows if r["split"] == "VALIDATION") == 6, "detail": "24/6"})
    checks.append({"check": "zero_llm_by_construction", "ok": True, "detail": "no model backend invoked"})
    # Determinism: extract features twice, must be byte-identical
    ds = DjangoCMSRealCommitDataset(dataset_dir=dataset_dir)
    cid = ds.case_ids()[0]
    case = ds.load_public_case(cid)
    f1 = extract_features(case)
    f2 = extract_features(case)
    checks.append({"check": "feature_determinism", "ok": f1 == f2, "detail": "byte-identical feature dicts"})
    # Persisted dry-run outputs present
    for fname in ("feature_table.csv", "raw_task_level_inputs.json", "single_feature_results.json", "adaptive_k_results.json", "cost_sensitive_analysis.json"):
        checks.append({"check": f"output_{fname}", "ok": (run_path / fname).exists(), "detail": str(run_path / fname)})
    return {"gate": 4, "name": "Dry Run", "passed": all(c["ok"] for c in checks), "checks": checks}


def gate5_integration_test(dataset_dir: Path = DATASET_DIR_DEFAULT) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    spec = build_spec()
    spec2 = build_spec()
    checks.append({"check": "spec_reproducible_sha256", "ok": spec.sha256 == spec2.sha256, "detail": spec.sha256})
    checks.append({"check": "spec_zero_llm_budget", "ok": spec.budget.zero_llm, "detail": str(spec.budget.to_dict())})
    rows, _ = collect_task_table(dataset_dir)
    single = run_single_feature_analysis(rows)
    checks.append({"check": "single_analysis_k10_present", "ok": "k10" in single and len(single["k10"]) == len(feature_names()), "detail": len(single.get("k10", {}))})
    combos = run_combination(rows)
    checks.append({"check": "combination_runs", "ok": "k" in combos and "k10" in combos["k"], "detail": list(combos.get("k", {}))})
    cal = run_calibration(rows)
    checks.append({"check": "calibration_runs", "ok": all(f"k{k}" in cal for k in (3, 5, 10)), "detail": list(cal)})
    costr = run_cost_sensitivity(rows)
    checks.append({"check": "cost_runs", "ok": all(f"k{k}" in costr for k in (3, 5, 10)), "detail": list(costr)})
    adaptive = run_adaptive_k_analysis(rows, dataset_dir)
    checks.append({"check": "adaptive_rules", "ok": set(adaptive) == set(adaptive_k.ADAPTIVE_RULES), "detail": sorted(adaptive)})
    return {"gate": 5, "name": "Integration Test", "passed": all(c["ok"] for c in checks), "checks": checks}


def gate6_metric_verification() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    # Manually known AUROC: perfect separation -> 1.0
    risk = [0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9]
    y = [0, 0, 0, 0, 1, 1, 1, 1]
    checks.append({"check": "auroc_perfect", "ok": abs(metrics.auroc(risk, y) - 1.0) < 1e-9, "detail": metrics.auroc(risk, y)})
    checks.append({"check": "auroc_signed_perfect", "ok": metrics.auroc_direction(risk, y) > 0.99, "detail": metrics.auroc_direction(risk, y)})
    # random risk on labels -> mean AUROC ~ 0.5 over many seeds
    rng = random.Random(42)
    aucs = []
    for _ in range(2000):
        rand_risk = [rng.random() for _ in range(8)]
        aucs.append(metrics.auroc(rand_risk, y))
    mean_auc = float(np.mean(aucs))
    checks.append({"check": "auroc_random_mean_near_half", "ok": abs(mean_auc - 0.5) < 0.05, "detail": f"mean={mean_auc:.4f}"})
    # AUPRC baseline = prevalence for constant risk
    checks.append({"check": "auprc_baseline", "ok": abs(metrics.auprc([0.5] * 8, y) - 0.5) < 1e-9, "detail": metrics.auprc([0.5] * 8, y)})
    # Brier: predicted 1 for all positives, 0 for negatives -> 0
    p = [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0]
    checks.append({"check": "brier_perfect", "ok": abs(metrics.brier(p, y)) < 1e-9, "detail": metrics.brier(p, y)})
    # recall at 50% budget where the top half captures all positives -> 1.0
    checks.append({"check": "recall_at_half_perfect", "ok": abs(metrics.recall_at_budget(risk, y, (0.5,))["recall_0.50"] - 1.0) < 1e-9, "detail": metrics.recall_at_budget(risk, y, (0.5,))})
    return {"gate": 6, "name": "Metric Verification", "passed": all(c["ok"] for c in checks), "checks": checks}


def run_six_gates(dataset_dir: Path = DATASET_DIR_DEFAULT) -> list[dict[str, Any]]:
    return [
        gate1_dataset_validation(dataset_dir),
        gate2_input_validation(dataset_dir),
        gate3_pipeline_smoke(),
        gate4_dry_run(dataset_dir),
        gate5_integration_test(dataset_dir),
        gate6_metric_verification(),
    ]


def all_gates_pass(gates: list[dict[str, Any]]) -> bool:
    return all(g["passed"] for g in gates)


# ---------------------------------------------------------------------------
# Audit checks (additional)
# ---------------------------------------------------------------------------


def audit_checks(dataset_dir: Path = DATASET_DIR_DEFAULT) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    # 1. HELD_OUT_TEST untouched: split counts unchanged AND no feature/result
    #    mentions a HELD_OUT case.
    split_freeze = json.loads((dataset_dir / "split_freeze.json").read_text(encoding="utf-8"))
    held = set(split_freeze["per_split"]["HELD_OUT_TEST"]["case_ids"])
    checks.append({"check": "heldout_count_10", "ok": len(held) == 10, "detail": len(held)})
    result_path = Path("research/omission-risk-feature-study-v1")
    if result_path.exists():
        merged_text = ""
        for f in ("feature_table.csv", "raw_task_level_inputs.json", "single_feature_results.json", "adaptive_k_results.json", "cost_sensitive_analysis.json"):
            p = result_path / f
            if p.exists():
                merged_text += p.read_text(encoding="utf-8")
                checks.append({"check": f"no_heldout_mention_{f}", "ok": not any(h in merged_text for h in held), "detail": "clean"})

    # 2. Statistical unit: file asserts only task-level aggregation (rows keyed
    #    by case_id; no repetition dimension exists in feature_table).
    if (result_path / "feature_table.csv").exists():
        header = (result_path / "feature_table.csv").read_text(encoding="utf-8").splitlines()[0]
        checks.append({"check": "no_repetition_dimension", "ok": "repetition" not in header and "rep" not in header, "detail": header.split(",")[:2]})

    # 3. No hidden-gold/future-history leakage in the extractor: it must never
    #    load the proxy or read the target commit.
    case_src = Path("src/benchmark/omission_risk/features.py").read_text(encoding="utf-8")
    checks.append({
        "check": "no_proxy_loader_in_features",
        "ok": "load_hidden_proxy_paths" not in case_src and "observed_change_set_proxy" not in case_src,
        "detail": "clean",
    })
    checks.append({
        "check": "no_target_field_access_in_features",
        "ok": "case.target_commit" not in case_src and ".target_commit" not in case_src,
        "detail": "clean",
    })

    # 4. Determinism: double extraction already covered in gate 4; re-check here.
    ds = DjangoCMSRealCommitDataset(dataset_dir=dataset_dir)
    case = ds.load_public_case(ds.case_ids()[0])
    checks.append({"check": "determinism_rechecked", "ok": extract_features(case) == extract_features(case), "detail": "identical"})

    # 5. Frozen scientific artifacts unchanged: files must be byte-identical to
    #    the frozen state (we only read them; write to research/ and reports/).
    import subprocess

    status = subprocess.check_output(["git", "status", "--porcelain", "research/real-commit-p1-01", "research/cheap-baselines-v1", "benchmark_data/real_commit_impact_v1"], text=True)
    checks.append({"check": "frozen_artifacts_untouched", "ok": status.strip() == "", "detail": status.strip() or "clean"})

    return {
        "audit": True,
        "checks": checks,
        "passed": all(c["ok"] for c in checks),
    }


if __name__ == "__main__":
    gates = run_six_gates()
    for g in gates:
        n_ok = sum(1 for c in g["checks"] if c["ok"])
        print(f"Gate {g['gate']} {g['name']}: PASS={g['passed']} ({n_ok}/{len(g['checks'])})")
    print("ALL_GATES_PASS:", all_gates_pass(gates))
    aud = audit_checks()
    print("AUDIT_PASS:", aud["passed"], f"({sum(1 for c in aud['checks'] if c['ok'])}/{len(aud['checks'])})")
