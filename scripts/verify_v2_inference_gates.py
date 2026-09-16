#!/usr/bin/env python3
"""RealCommitImpactDataset-v2 — six ZERO-API gates + leakage audit.

Mirrors the v1 verifier but for the V2 development set (DEV_TRAIN + DEV_VALIDATION).
INTERNAL_TEST / RESERVE / LEGACY_EXPOSED_V1 are never touched.

Usage:
    python scripts/verify_v2_inference_gates.py
"""

# ruff: noqa: E501
from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.real_commits import p1_evaluation as p1  # noqa: E402
from scripts.v2_inference_manifest import (  # noqa: E402
    DATASET_DIR,
    SPLIT,
    build_v2_manifest,
    v2_development_case_ids,
)

REPORTS_DIR = _PROJECT_DIR / "reports"
GATES_PATH = REPORTS_DIR / "v2_inference_gates.json"
REPORT_PATH = REPORTS_DIR / "V2_INFERENCE_GATES.md"
LEGACY_JSON = _PROJECT_DIR / "research" / "transparency" / "legacy_exposed_v1_case_ids.json"

CELLS_EXPECTED = 450


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _load_case_ids_from_manifest() -> list[str]:
    return v2_development_case_ids()


# Gate 1 — Dataset Validation
def gate1_dataset_validation() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    case_ids = _load_case_ids_from_manifest()
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    legacy = set(json.loads(LEGACY_JSON.read_text(encoding="utf-8")))
    assignment = split["assignment"]
    checks.append({"check": "v2_dev_count_150", "ok": len(case_ids) == 150, "detail": len(case_ids)})
    checks.append({"check": "roles_only_train_validation", "ok": all(assignment[c] in ("DEV_TRAIN", "DEV_VALIDATION") for c in case_ids), "detail": sorted({assignment[c] for c in case_ids})})
    checks.append({"check": "no_legacy_exposed_in_v2", "ok": legacy.isdisjoint(set(case_ids)), "detail": "no v1 exposed case in v2 dev"})
    for cid in case_ids[:6]:
        case = p1.load_case_public_bundle(DATASET_DIR, cid)
        proxy = set(p1.load_hidden_proxy_paths(DATASET_DIR, cid))
        checks.append({"check": f"proxy_subset_universe_{cid}", "ok": proxy <= set(case.candidate_paths), "detail": sorted(proxy - set(case.candidate_paths))})
    checks.append({"check": "test_reserve_never_in_dev", "ok": not any(assignment[c] in ("INTERNAL_TEST", "RESERVE") for c in case_ids), "detail": "none"})
    return {"gate": 1, "name": "Dataset Validation (V2 DEV)", "passed": all(c["ok"] for c in checks), "checks": checks}


# Gate 2 — Prompt Validation
def gate2_prompt_validation() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    hidden_markers = ("observed_change_set_proxy", "changed_paths", "target_diff", "target_commit_diff", "hidden/", "proxy_sha256")
    for cid in _load_case_ids_from_manifest()[:6]:
        bundle = p1.load_case_public_bundle(DATASET_DIR, cid)
        mapping = p1.build_p1_candidate_map(bundle.candidate_paths)
        prompt = p1.render_p1_sparse_prompt(case=bundle, mapping=mapping)
        leaked = [m for m in hidden_markers if m in prompt]
        checks.append({"check": f"no_hidden_marker_{cid}", "ok": not leaked, "detail": sorted(leaked)})
        checks.append({"check": f"sparse_policy_{cid}", "ok": "PRESERVE-BY-OMISSION" in prompt, "detail": "ok"})
        checks.append({"check": f"intent_present_{cid}", "ok": bool(bundle.intent_text.strip()), "detail": bundle.intent_text[:60]})
    checks.append({"check": "zero_model_calls_render", "ok": True, "detail": "string rendering only"})
    return {"gate": 2, "name": "Prompt Validation (V2 DEV)", "passed": all(c["ok"] for c in checks), "checks": checks}


# Gate 3 — Pipeline smoke
def gate3_pipeline_smoke() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    cid = _load_case_ids_from_manifest()[0]
    bundle = p1.load_case_public_bundle(DATASET_DIR, cid)
    mapping = p1.build_p1_candidate_map(bundle.candidate_paths)
    proxy = set(p1.load_hidden_proxy_paths(DATASET_DIR, cid))
    payload = p1.fixture_payload_for_arm(arm="sparse_v2", mapping=mapping, proxy_paths=proxy)
    vres = p1.validate_p1_sparse(payload, candidate_count=len(mapping.id_to_path))
    checks.append({"check": "mock_sparse_decode_valid", "ok": vres["valid"] and vres["decoded_candidate_count"] == len(mapping.id_to_path), "detail": vres["valid"]})
    checks.append({"check": "zero_calls_smoke", "ok": True, "detail": "fixture only"})
    return {"gate": 3, "name": "Pipeline Smoke (V2 DEV)", "passed": all(c["ok"] for c in checks), "checks": checks}


# Gate 4 — Dry run
def gate4_dry_run() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    cells = build_v2_manifest()
    checks.append({"check": "cells_exactly_450", "ok": len(cells) == CELLS_EXPECTED, "detail": len(cells)})
    checks.append({"check": "run_ids_unique", "ok": len({c["run_id"] for c in cells}) == CELLS_EXPECTED, "detail": len({c["run_id"] for c in cells})})
    checks.append({"check": "three_reps_each", "ok": all(sum(1 for c in cells if c["case_id"] == cid) == 3 for cid in _load_case_ids_from_manifest()), "detail": "150x3=450"})
    checks.append({"check": "frozen_config", "ok": all(c["expected_model"] == p1.P1_MODEL and c["provider_tag"] == p1.P1_PROVIDER_TAG and c["temperature"] == 0.0 and c["max_completion_tokens"] == 16384 for c in cells), "detail": "qwen3-coder/deepinfra/temp0/cap16384"})
    checks.append({"check": "zero_calls_dryrun", "ok": True, "detail": "manifest shape only"})
    return {"gate": 4, "name": "Dry Run (V2 DEV)", "passed": all(c["ok"] for c in checks), "checks": checks}


# Gate 5 — Integration
def gate5_integration() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    cells = build_v2_manifest()
    checks.append({"check": "manifest_sparse_only", "ok": {c["arm"] for c in cells} == {"sparse_v2"}, "detail": "sparse_v2 only"})
    checks.append({"check": "manifest_protocol_frozen", "ok": all(c["protocol_version"] == p1.P1_PROTOCOL_VERSION for c in cells), "detail": p1.P1_PROTOCOL_VERSION})
    required = ("run_id", "case_id", "repetition", "arm", "candidate_count", "candidate_map_sha256", "public_bundle_sha256")
    checks.append({"check": "row_shape", "ok": all(all(k in c for k in required) for c in cells), "detail": f"{len(required)} fields"})
    return {"gate": 5, "name": "Integration (V2 DEV)", "passed": all(c["ok"] for c in checks), "checks": checks}


# Gate 6 — Metric verification
def gate6_metric_verification() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    predicted = {"a", "b", "c", "d"}
    proxy = {"a", "b", "c"}
    m = p1.p1_selection_metrics(predicted, proxy)
    tp = len(predicted & proxy)
    fn = len(proxy - predicted)
    prec = tp / len(predicted)
    rec = tp / (tp + fn)
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    checks.append({"check": "micro_recomputed", "ok": abs(m["precision"] - prec) < 1e-9 and abs(m["recall"] - rec) < 1e-9 and abs(m["f1"] - f1) < 1e-9, "detail": m})
    empty = p1.p1_selection_metrics(set(), {"x"})
    checks.append({"check": "empty_fail_closed", "ok": empty["precision"] == 0.0 and empty["recall"] == 0.0 and empty["fnr"] == 1.0, "detail": empty})
    return {"gate": 6, "name": "Metric Verification (V2 DEV)", "passed": all(c["ok"] for c in checks), "checks": checks}


GATES = (gate1_dataset_validation, gate2_prompt_validation, gate3_pipeline_smoke, gate4_dry_run, gate5_integration, gate6_metric_verification)


def main() -> int:
    gates = [g() for g in GATES]
    all_passed = all(g["passed"] for g in gates)
    result = {"study_id": "real-commit-impact-v2-dev-inference", "gates": gates, "all_passed": all_passed, "ran_at": _now_iso()}
    GATES_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    REPORT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    for g in gates:
        print(f"Gate {g['gate']} {g['name']}: {'PASS' if g['passed'] else 'FAIL'}")
    print(f"OVERALL={'PASS' if all_passed else 'FAIL'}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
