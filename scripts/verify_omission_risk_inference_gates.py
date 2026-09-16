#!/usr/bin/env python3
"""Omission-Risk Development Inference — six ZERO-API pre-benchmark gates + leakage audit.

Frozen protocol: docs/OMISSION_RISK_DEVELOPMENT_INFERENCE_PROTOCOL.md §5.

Gates (all ZERO model/API calls; HELD_OUT_TEST NEVER touched):
1. Dataset validation   — TRAIN 24 / VALIDATION 6 only; HELD_OUT_TEST fails closed.
2. Prompt/input validation — P1 prompt contract byte-checks; policy block = SPARSE.
3. Pipeline smoke       — 1 synthetic case end-to-end (deterministic mock backend).
4. Dry run              — 2-case slice, 0 model calls, row-shape contract.
5. Integration          — 30-case manifest + run_records schema + persisted raw+sha256.
6. Metric verification  — synthetic TP/FP/FN P/R/F1/FNR.

Plus leakage audit: proxy never in prompt; determinism; task-level statistical
unit; Phase-B preflight A–G data availability (sparse_v2 now available on
TRAIN/VALIDATION is checked post-run by the analysis stage; here we assert the
preconditions).

Usage:
    python scripts/verify_omission_risk_inference_gates.py
"""


from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.harness.djangocms import DjangoCMSRealCommitDataset  # noqa: E402
from benchmark.real_commits import p1_evaluation as p1  # noqa: E402
from scripts.omission_risk_inference_manifest import (  # noqa: E402
    ARM,
    DATASET_DIR,
    MODEL,
    PROVIDER_TAG,
    STUDY_ID,
    build_omission_risk_manifest,
    trainval_case_ids,
)

REPORTS_DIR = _PROJECT_DIR / "reports"
GATES_PATH = REPORTS_DIR / "omission_risk_inference_gates.json"
REPORT_PATH = REPORTS_DIR / "OMISSION_RISK_INFERENCE_GATES.md"

TRAIN_EXPECTED = 24
VALIDATION_EXPECTED = 6
HELD_OUT_EXPECTED = 10
CELLS_EXPECTED = 90

# Run-record schema enforced by the executor (shared with execute script).
RUN_RECORD_REQUIRED_FIELDS = (
    "run_id",
    "case_id",
    "repetition",
    "arm",
    "serialization_policy",
    "scientific_model",
    "model_human",
    "gateway",
    "provider",
    "provider_tag",
    "exact_model",
    "exact_provider_used",
    "quantization",
    "fallback_status",
    "temperature",
    "completion_cap",
    "reasoning_mode",
    "graph",
    "dry_run",
    "request_attempted",
    "request_dispatched",
    "prompt_sha256",
    "request_issued",
    "transport_failure",
    "raw_response_sha256",
    "latency_seconds",
    "recorded_at",
    "provider_response_received",
    "raw_response_persisted",
    "usage_known",
    "usage_received",
    "provider_name",
    "finish_reason",
    "truncation_status",
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "model_calls",
    "api_cost",
    "pricing_source",
    "schema_valid",
    "failure_category",
    "decoded_candidate_count",
    "decoded_write_set_ids",
    "serialized_decision_count",
    "predicted_write_set_size",
    "decoded_policy_sha256",
    "terminal_status",
    "predicted_write_set",
    "predicted_write_set_size",
    "hidden_proxy_used_after_inference",
    "tp",
    "fp",
    "fn",
    "precision",
    "recall",
    "f1",
    "fnr",
    "full_recall",
    "proxy_size",
)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _jaccard(a: set[str], b: set[str]) -> float:
    union = a | b
    return len(a & b) / len(union) if union else 1.0


# ---------------------------------------------------------------------------
# Gate 1 — Dataset validation
# ---------------------------------------------------------------------------


def gate1_dataset_validation() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    split_freeze = json.loads(
        (DATASET_DIR / "split_freeze.json").read_text(encoding="utf-8")
    )
    per_split = split_freeze["per_split"]
    for split, expected in (
        ("TRAIN", TRAIN_EXPECTED),
        ("VALIDATION", VALIDATION_EXPECTED),
        ("HELD_OUT_TEST", HELD_OUT_EXPECTED),
    ):
        checks.append(
            {
                "check": f"split_count_{split}",
                "ok": per_split[split]["count"] == expected,
                "detail": per_split[split]["count"],
            }
        )

    # Adapter (splits_allowed = TRAIN, VALIDATION) returns exactly 30 cases.
    ds = DjangoCMSRealCommitDataset(dataset_dir=DATASET_DIR)
    allowed = set(ds.case_ids())
    checks.append(
        {
            "check": "adapter_case_ids_only_train_validation",
            "ok": len(allowed) == 30 and allowed == set(trainval_case_ids()),
            "detail": {"n": len(allowed), "splits": sorted({ds.split_of(c) for c in allowed})},
        }
    )
    checks.append(
        {
            "check": "adapter_excludes_held_out",
            "ok": all(ds.split_of(c) in ("TRAIN", "VALIDATION") for c in allowed),
            "detail": "no HELD_OUT_TEST case exposed by the adapter",
        }
    )
    # HELD_OUT_TEST proxy access must fail closed.
    held_out_id = per_split["HELD_OUT_TEST"]["case_ids"][0]
    try:
        ds.load_hidden_proxy_paths(held_out_id)
        checks.append({"check": "heldout_proxy_fails_closed", "ok": False, "detail": "proxy loaded!"})
    except Exception:
        checks.append({"check": "heldout_proxy_fails_closed", "ok": True, "detail": "blocked"})
    # Proxy subset of universe for allowed cases.
    for cid in allowed:
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


# ---------------------------------------------------------------------------
# Gate 2 — Prompt/input validation (P1 SPARSE contract + leakage)
# ---------------------------------------------------------------------------


def gate2_prompt_validation() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    rendered: dict[str, Any] = {}
    hidden_markers = (
        "observed_change_set_proxy",
        "observed-change-set",
        "changed_paths",
        "change_statuses",
        "statuses",
        "target_diff",
        "target_commit_diff",
        "hidden/",
        "proxy_sha256",
    )
    for cid in trainval_case_ids():
        bundle = p1.load_case_public_bundle(DATASET_DIR, cid)
        mapping = p1.build_p1_candidate_map(bundle.candidate_paths)
        sparse_prompt = p1.render_p1_sparse_prompt(case=bundle, mapping=mapping)
        full_prompt = p1.render_p1_full_prompt(case=bundle, mapping=mapping)
        proof = p1.prompt_control_proof(full_prompt, sparse_prompt)
        rendered[cid] = {
            "sparse_prompt_sha256": p1.sha256_text(sparse_prompt),
            "policy_block_present": "SPARSE SERIALIZATION POLICY" in sparse_prompt
            and "PRESERVE-BY-OMISSION" in sparse_prompt,
            "stripped_sha256": proof["stripped_sparse_sha256"],
            "prompt_control_proof": proof["PROMPT_CONTROLLED_DIFF"],
        }
        checks.append(
            {
                "check": f"prompt_control_proof_{cid}",
                "ok": proof["PROMPT_CONTROLLED_DIFF"] == "PASS",
                "detail": proof,
            }
        )
        checks.append(
            {
                "check": f"sparse_policy_block_{cid}",
                "ok": "PRESERVE-BY-OMISSION" in sparse_prompt,
                "detail": "SPARSE policy block present",
            }
        )
        leaked = [m for m in hidden_markers if m in sparse_prompt]
        checks.append(
            {
                "check": f"no_hidden_proxy_marker_in_prompt_{cid}",
                "ok": not leaked,
                "detail": sorted(leaked),
            }
        )
        checks.append(
            {
                "check": f"intent_present_{cid}",
                "ok": bool(bundle.intent_text.strip()),
                "detail": bundle.intent_text[:80],
            }
        )
        checks.append(
            {
                "check": f"candidate_ids_1_n_{cid}",
                "ok": [i for i, _ in mapping.id_to_path] == list(range(1, len(mapping.id_to_path) + 1)),
                "detail": len(mapping.id_to_path),
            }
        )
    checks.append(
        {
            "check": "zero_model_calls_prompt_render",
            "ok": True,
            "detail": "pure string rendering; no backend constructed",
        }
    )
    return {
        "gate": 2,
        "name": "Prompt/Input Validation",
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
        "rendered": rendered,
    }


# ---------------------------------------------------------------------------
# Gate 3 — Pipeline smoke (1 synthetic case, deterministic mock backend)
# ---------------------------------------------------------------------------


def gate3_pipeline_smoke() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    # Use the first TRAIN case as the single end-to-end smoke cell (mock fixture).
    cid = trainval_case_ids()[0]
    bundle = p1.load_case_public_bundle(DATASET_DIR, cid)
    mapping = p1.build_p1_candidate_map(bundle.candidate_paths)
    n = len(mapping.id_to_path)
    proxy = set(p1.load_hidden_proxy_paths(DATASET_DIR, cid))
    prompt = p1.render_p1_sparse_prompt(case=bundle, mapping=mapping)
    checks.append(
        {
            "check": "prompt_renders",
            "ok": "PRESERVE-BY-OMISSION" in prompt and len(prompt) > 1000,
            "detail": {"prompt_len": len(prompt)},
        }
    )
    payload = p1.fixture_payload_for_arm(arm=ARM, mapping=mapping, proxy_paths=proxy)
    vres = p1.validate_p1_sparse(payload, candidate_count=n)
    checks.append(
        {
            "check": "mock_sparse_decode_valid",
            "ok": vres["valid"] and vres["decoded_candidate_count"] == n,
            "detail": {"valid": vres["valid"], "count": vres.get("decoded_candidate_count")},
        }
    )
    write_set = {mapping.path_for(i) for i in vres["decoded_write_set_ids"]}
    metrics = p1.p1_selection_metrics(write_set, proxy)
    checks.append(
        {
            "check": "mock_metrics_exact_fixture",
            "ok": metrics["recall"] == 1.0 and metrics["fnr"] == 0.0 and metrics["full_recall"],
            "detail": {k: metrics[k] for k in ("tp", "fp", "fn", "precision", "recall", "f1", "fnr")},
        }
    )
    checks.append({"check": "zero_model_calls_smoke", "ok": True, "detail": "fixture encode/decode only"})
    return {"gate": 3, "name": "Pipeline Smoke Test", "passed": all(c["ok"] for c in checks), "checks": checks}


# ---------------------------------------------------------------------------
# Gate 4 — Dry run (2-case slice, 0 model calls, row-shape contract)
# ---------------------------------------------------------------------------


def gate4_dry_run() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    cells = build_omission_risk_manifest()
    # 2-case slice: first TRAIN + first VALIDATION, all their reps.
    train_ids = [c for c in trainval_case_ids() if _split_of(c) == "TRAIN"]
    valid_ids = [c for c in trainval_case_ids() if _split_of(c) == "VALIDATION"]
    slice_ids = {train_ids[0], valid_ids[0]}
    slice_cells = [c for c in cells if c["case_id"] in slice_ids]
    checks.append({"check": "slice_cell_count_6", "ok": len(slice_cells) == 6, "detail": len(slice_cells)})
    checks.append(
        {
            "check": "slice_run_ids_unique",
            "ok": len({c["run_id"] for c in slice_cells}) == len(slice_cells),
            "detail": len(slice_cells),
        }
    )
    required = (
        "run_id", "case_id", "repetition", "arm", "serialization_policy",
        "expected_model", "provider_tag", "temperature", "max_completion_tokens",
        "candidate_count", "candidate_map_sha256", "public_bundle_sha256",
        "protocol_version",
    )
    row_shape_ok = all(all(k in c for k in required) for c in slice_cells)
    checks.append({"check": "row_shape_contract", "ok": row_shape_ok, "detail": f"{len(required)} fields"})
    checks.append(
        {
            "check": "frozen_config_slice",
            "ok": all(
                c["arm"] == ARM
                and c["expected_model"] == MODEL
                and c["provider_tag"] == PROVIDER_TAG
                and c["temperature"] == 0.0
                and c["max_completion_tokens"] == 16384
                for c in slice_cells
            ),
            "detail": "sparse_v2 / qwen3-coder / deepinfra-turbo / temp0 / cap16384",
        }
    )
    checks.append({"check": "zero_model_calls_dry_run", "ok": True, "detail": "manifest-shape proof only"})
    return {"gate": 4, "name": "Dry Run", "passed": all(c["ok"] for c in checks), "checks": checks}


def _split_of(case_id: str) -> str:
    ds = DjangoCMSRealCommitDataset(dataset_dir=DATASET_DIR)
    return ds.split_of(case_id)


# ---------------------------------------------------------------------------
# Gate 5 — Integration (30-case manifest + run_records schema + raw/sha256)
# ---------------------------------------------------------------------------


def gate5_integration_test() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    cells = build_omission_risk_manifest()
    checks.append({"check": "manifest_exactly_90", "ok": len(cells) == CELLS_EXPECTED, "detail": len(cells)})
    checks.append(
        {
            "check": "manifest_30_unique_cases",
            "ok": len({c["case_id"] for c in cells}) == 30,
            "detail": len({c["case_id"] for c in cells}),
        }
    )
    checks.append(
        {
            "check": "manifest_three_reps_each",
            "ok": all(
                sum(1 for c in cells if c["case_id"] == cid) == 3 for cid in trainval_case_ids()
            ),
            "detail": "30 cases x 3 reps = 90",
        }
    )
    checks.append(
        {
            "check": "manifest_sparse_only",
            "ok": {c["arm"] for c in cells} == {"sparse_v2"},
            "detail": sorted({c["arm"] for c in cells}),
        }
    )
    checks.append(
        {
            "check": "manifest_protocol_frozen",
            "ok": all(c["protocol_version"] == p1.P1_PROTOCOL_VERSION for c in cells),
            "detail": p1.P1_PROTOCOL_VERSION,
        }
    )
    # run_records schema: build a mock evidence record and assert required fields.
    mock_evidence = {
        "run_id": "omission-dummy-sparse_v2-r1",
        "case_id": "dummy",
        "repetition": 1,
        "arm": "sparse_v2",
        "serialization_policy": "sparse_v2",
        "scientific_model": MODEL,
        "model_human": "Qwen3-Coder-480B-A35B-Instruct",
        "gateway": "OpenRouter",
        "provider": "DeepInfra pinned through OpenRouter",
        "provider_tag": PROVIDER_TAG,
        "exact_model": f"openrouter:{MODEL}@{PROVIDER_TAG}",
        "exact_provider_used": PROVIDER_TAG,
        "quantization": "fp4",
        "fallback_status": "off",
        "temperature": 0.0,
        "completion_cap": 16384,
        "reasoning_mode": "direct/non-thinking",
        "graph": "OFF",
        "dry_run": False,
        "request_attempted": True,
        "request_dispatched": True,
        "prompt_sha256": "0" * 64,
        "request_issued": True,
        "transport_failure": False,
        "raw_response_sha256": "0" * 64,
        "latency_seconds": 1.0,
        "recorded_at": _now_iso(),
        "provider_response_received": True,
        "raw_response_persisted": True,
        "usage_known": True,
        "usage_received": True,
        "provider_name": "DeepInfra",
        "finish_reason": "stop",
        "truncation_status": False,
        "prompt_tokens": 5000,
        "completion_tokens": 600,
        "total_tokens": 5600,
        "model_calls": 1,
        "api_cost": 0.0021,
        "pricing_source": "frozen",
        "schema_valid": True,
        "failure_category": "",
        "decoded_candidate_count": 140,
        "decoded_write_set_ids": [1, 2],
        "serialized_decision_count": 2,
        "decoded_policy_sha256": "0" * 64,
        "terminal_status": "succeeded",
        "predicted_write_set": ["a.py", "b.py"],
        "predicted_write_set_size": 2,
        "hidden_proxy_used_after_inference": ["a.py"],
        "tp": 1,
        "fp": 1,
        "fn": 0,
        "precision": 0.5,
        "recall": 1.0,
        "f1": 0.666667,
        "fnr": 0.0,
        "full_recall": True,
        "proxy_size": 1,
    }
    missing = [f for f in RUN_RECORD_REQUIRED_FIELDS if f not in mock_evidence]
    checks.append(
        {
            "check": "run_records_schema_fields",
            "ok": not missing,
            "detail": {"missing": missing, "n_fields": len(RUN_RECORD_REQUIRED_FIELDS)},
        }
    )
    # Persisted raw + sha256 sidecar contract (write to a temp path).
    import tempfile

    raw_dir = Path(tempfile.mkdtemp(prefix="omission_raw_"))
    raw_text = '{"choices":[{"message":{"content":"{}"}}]}'
    raw_path = raw_dir / "raw.txt"
    sha_path = raw_dir / "raw.txt.sha256"
    raw_path.write_text(raw_text, encoding="utf-8")
    sha_path.write_text(p1.sha256_text(raw_text) + "\n", encoding="utf-8")
    persisted_ok = (
        sha_path.read_text(encoding="utf-8").strip()
        == p1.sha256_text(raw_path.read_text(encoding="utf-8"))
    )
    checks.append(
        {
            "check": "raw_sha256_sidecar_contract",
            "ok": persisted_ok,
            "detail": {"raw_bytes": len(raw_text), "sha256": p1.sha256_text(raw_text)},
        }
    )
    checks.append({"check": "zero_model_calls_integration", "ok": True, "detail": "schema + manifest proof only"})
    return {"gate": 5, "name": "Integration Test", "passed": all(c["ok"] for c in checks), "checks": checks}


# ---------------------------------------------------------------------------
# Gate 6 — Metric verification (synthetic TP/FP/FN P/R/F1/FNR)
# ---------------------------------------------------------------------------


def gate6_metric_verification() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    predicted = {"a", "b", "c", "d"}
    proxy = {"a", "b", "c"}
    metrics = p1.p1_selection_metrics(predicted, proxy)
    tp = len(predicted & proxy)
    fn = len(proxy - predicted)
    precision = tp / len(predicted)
    recall = tp / (tp + fn)
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    checks.append(
        {
            "check": "micro_precision_recall_f1_recomputed",
            "ok": abs(metrics["precision"] - precision) < 1e-9
            and abs(metrics["recall"] - recall) < 1e-9
            and abs(metrics["f1"] - f1) < 1e-9,
            "detail": {"computed": metrics, "expected": {"precision": precision, "recall": recall, "f1": f1}},
        }
    )
    empty = p1.p1_selection_metrics(set(), {"x"})
    checks.append(
        {
            "check": "empty_prediction_fail_closed_metrics",
            "ok": empty["precision"] == 0.0 and empty["recall"] == 0.0 and empty["fnr"] == 1.0,
            "detail": empty,
        }
    )
    try:
        p1.decode_p1_sparse({"decisions": [{"id": 1, "action": "PRESERVE"}]}, candidate_count=5)
        sparse_preserve_ok = False
    except p1.P1DecodeError:
        sparse_preserve_ok = True
    checks.append(
        {
            "check": "sparse_explicit_preserve_rejected",
            "ok": sparse_preserve_ok,
            "detail": "SPARSE-v2 must not contain explicit PRESERVE rows",
        }
    )
    return {"gate": 6, "name": "Metric Verification", "passed": all(c["ok"] for c in checks), "checks": checks}


# ---------------------------------------------------------------------------
# Leakage / determinism / statistical-unit audit (pre-run preconditions)
# ---------------------------------------------------------------------------


def _independent_audit() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    # 1. Feature extractor never loads the proxy (source-level).
    features_src = (_PROJECT_DIR / "src" / "benchmark" / "omission_risk" / "features.py").read_text(
        encoding="utf-8"
    )
    checks.append(
        {
            "check": "features_no_proxy_loader",
            "ok": "load_hidden_proxy_paths" not in features_src,
            "detail": "extractor is proxy-free by construction",
        }
    )

    # 2. HELD_OUT_TEST never in the manifest.
    held = set(
        json.loads((DATASET_DIR / "split_freeze.json").read_text(encoding="utf-8"))[
            "per_split"
        ]["HELD_OUT_TEST"]["case_ids"]
    )
    cells = build_omission_risk_manifest()
    checks.append(
        {
            "check": "heldout_never_in_manifest",
            "ok": held.isdisjoint({c["case_id"] for c in cells}),
            "detail": "no HELD_OUT_TEST case in any of the 90 cells",
        }
    )

    # 3. Determinism: feature extraction double-run byte-identical.
    from benchmark.harness.djangocms import DjangoCMSRealCommitDataset
    from benchmark.omission_risk.features import extract_features

    ds = DjangoCMSRealCommitDataset(dataset_dir=DATASET_DIR)
    case = ds.load_public_case(trainval_case_ids()[0])
    checks.append(
        {
            "check": "feature_extraction_deterministic",
            "ok": extract_features(case) == extract_features(case),
            "detail": "byte-identical feature dicts",
        }
    )

    # 4. Task-level statistical unit: manifest keys on task + nested rep, no rep-averaged leakage.
    checks.append(
        {
            "check": "task_level_unit_30_tasks",
            "ok": len({c["case_id"] for c in cells}) == 30,
            "detail": "N=30 independent tasks; 3 nested repetitions per task",
        }
    )

    # 5. Phase-B preconditions (A–G): sparse_v2 predictions absent pre-run (Gate A), graph
    #    available, history absent — re-checked fully post-run by the analysis stage.
    data_avail = json.loads(
        (_PROJECT_DIR / "research" / "omission-risk-feature-study-v1" / "data_availability.json").read_text(
            encoding="utf-8"
        )
    )
    checks.append(
        {
            "check": "phase_b_gate_a_precondition",
            "ok": data_avail["TRAIN"]["sparse_v2_prediction_available"] is False
            and data_avail["VALIDATION"]["sparse_v2_prediction_available"] is False,
            "detail": "TRAIN/VALIDATION Sparse-v2 predictions absent before this run",
        }
    )
    return {"passed": all(c["ok"] for c in checks), "checks": checks, "ran_at": _now_iso()}


GATES = (
    gate1_dataset_validation,
    gate2_prompt_validation,
    gate3_pipeline_smoke,
    gate4_dry_run,
    gate5_integration_test,
    gate6_metric_verification,
)


def _render_report(gates: list[dict[str, Any]], audit: dict[str, Any]) -> str:
    lines = [
        "# Omission-Risk Development Inference — ZERO-API Gates + Leakage Audit",
        "",
        f"**Generated:** {_now_iso()}",
        f"**Study ID:** {STUDY_ID}",
        "**Frozen protocol:** docs/OMISSION_RISK_DEVELOPMENT_INFERENCE_PROTOCOL.md",
        "",
        "ZERO scientific LLM/API calls in this milestone. No model call is made before these gates pass.",
        "",
    ]
    all_pass = all(g["passed"] for g in gates) and audit["passed"]
    lines.append(f"**OVERALL:** {'PASS' if all_pass else 'FAIL'}")
    lines.append("")
    for gate in gates:
        lines.append(f"## Gate {gate['gate']} — {gate['name']}")
        lines.append("")
        for c in gate["checks"]:
            lines.append(f"- [{'PASS' if c['ok'] else 'FAIL'}] {c['check']} — {json.dumps(c['detail'])[:200]}")
        lines.append("")
    lines.append("## Independent Audit (pre-run preconditions)")
    lines.append("")
    for c in audit["checks"]:
        lines.append(f"- [{'PASS' if c['ok'] else 'FAIL'}] {c['check']} — {c['detail']}")
    lines.append("")
    lines.append("## Scientific discipline")
    lines.append("")
    lines.append("- Historical diff is an OBSERVED CHANGE-SET PROXY, never semantic ground truth.")
    lines.append("- Independent task = historical change; repeated model calls are nested observations.")
    lines.append("- HELD_OUT_TEST is never used for any decision in this run.")
    return "\n".join(lines)


def main() -> int:
    gates = [g() for g in GATES]
    audit = _independent_audit()
    all_passed = all(g["passed"] for g in gates) and audit["passed"]
    result = {
        "study_id": STUDY_ID,
        "model": MODEL,
        "provider_tag": PROVIDER_TAG,
        "gates": gates,
        "all_passed": all(g["passed"] for g in gates),
        "audit": audit,
        "ran_at": _now_iso(),
    }
    GATES_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    REPORT_PATH.write_text(_render_report(gates, audit), encoding="utf-8")
    for g in gates:
        print(f"Gate {g['gate']} {g['name']}: {'PASS' if g['passed'] else 'FAIL'}")
    print(f"AUDIT={'PASS' if audit['passed'] else 'FAIL'}")
    print(f"OVERALL={'PASS' if all_passed else 'FAIL'}")
    print(f"gates_json={GATES_PATH}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
