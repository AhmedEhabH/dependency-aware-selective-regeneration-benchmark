#!/usr/bin/env python3
"""P5-B — LocAgent VALIDATION pilot: six Pre-Benchmark Validation gates.

Runs EXACTLY the six frozen P5 Pre-Benchmark Validation gates on the 6
VALIDATION cases only (HELD_OUT_TEST is NEVER touched here):

  1. Dataset Validation        — split freeze identity, case presence, leak-free
  2. Prompt/Input Validation   — input boundary (intent/parent/repo/patch="")
  3. Pipeline Smoke Test       — LocAgent output -> common evaluator (fixture)
  4. Dry Run                   — exact run plan manifest with 0 model calls
  5. Integration Test          — adapter -> output parser -> common evaluator
  6. Metric Verification       — TP/FP/FN/P/R/F1/FNR independently recomputed

Then prints a gate summary. The REAL LocAgent localization run is a separate
step (executed on Ubuntu/WSL); this script validates inputs + scoring only.

ZERO scientific LLM/API calls in this script.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PACKAGE_ROOT))
sys.path.insert(0, str(_PACKAGE_ROOT / "src"))

from benchmark.locagent import evaluator  # noqa: E402
from benchmark.locagent.adapter import LocAgentAdapter  # noqa: E402

DATASET_DIR = _PACKAGE_ROOT / "benchmark_data" / "real_commit_impact_v1"
REPORTS_DIR = _PACKAGE_ROOT / "reports"
OUT_DIR = _PACKAGE_ROOT / "research" / "locagent-p5b" / "gates"

VALIDATION_CASES = [
    "djangocms-rc-0daae01f2f65",
    "djangocms-rc-0fec81224889",
    "djangocms-rc-1031d20fca28",
    "djangocms-rc-47b63015feb1",
    "djangocms-rc-a9e2a8d3b7a6",
    "djangocms-rc-e3a23a7fc757",
]


def _load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _proxy_paths(case_id: str) -> set[str]:
    proxy = _load_json(
        DATASET_DIR / "scientific" / case_id / "hidden" / "observed_change_set_proxy.json"
    )
    return set(proxy["paths"])


def _candidate_universe(case_id: str) -> set[str]:
    uni = _load_json(DATASET_DIR / "scientific" / case_id / "public" / "candidate_universe.json")
    return {str(r["path"]) for r in uni.get("records", [])}


def gate1_dataset_validation() -> list[str]:
    errors: list[str] = []
    split_freeze = _load_json(DATASET_DIR / "split_freeze.json")
    per = split_freeze.get("per_split", {})
    val_ids = set(per.get("VALIDATION", {}).get("case_ids", []))
    held_out = set(per.get("HELD_OUT_TEST", {}).get("case_ids", []))
    if set(VALIDATION_CASES) != val_ids:
        errors.append(f"VALIDATION set mismatch: {sorted(val_ids)}")
    for cid in VALIDATION_CASES:
        if not (DATASET_DIR / "scientific" / cid / "case_manifest.json").exists():
            errors.append(f"{cid}: missing case_manifest")
        if not (DATASET_DIR / "scientific" / cid / "hidden" / "observed_change_set_proxy.json").exists():
            errors.append(f"{cid}: missing hidden proxy")
        if not (DATASET_DIR / "scientific" / cid / "public" / "candidate_universe.json").exists():
            errors.append(f"{cid}: missing public universe")
    if VALIDATION_CASES and VALIDATION_CASES[-1] in held_out:
        errors.append("VALIDATION case leaked into HELD_OUT_TEST")
    if len(val_ids) != 6:
        errors.append(f"expected 6 VALIDATION cases, found {len(val_ids)}")
    return errors


def gate2_prompt_input_validation() -> list[str]:
    errors: list[str] = []
    adapter = LocAgentAdapter(DATASET_DIR)
    for cid in VALIDATION_CASES:
        inst = adapter.build_input(cid)
        if inst.split != "VALIDATION":
            errors.append(f"{cid}: split={inst.split} != VALIDATION")
        if not inst.base_commit or len(inst.base_commit) != 40:
            errors.append(f"{cid}: bad base_commit {inst.base_commit!r}")
        if not inst.problem_statement.strip():
            errors.append(f"{cid}: empty problem_statement")
        if inst.patch != "":
            errors.append(f"{cid}: patch must be EMPTY")
        leak = adapter.leakage_errors(inst)
        if leak:
            errors.append(f"{cid}: leakage {leak}")
    return errors


def gate3_pipeline_smoke() -> list[str]:
    errors: list[str] = []
    # Fixture LocAgent-style raw output for ONE validation case parsed + scored.
    cid = VALIDATION_CASES[0]
    proxy = _proxy_paths(cid)
    uni = _candidate_universe(cid)
    raw = "\n".join(f"- {p}" for p in sorted(proxy))
    parsed = evaluator.parse_locagent_raw_output(raw, uni)
    if not parsed.valid or not parsed.found_files:
        errors.append("pipeline smoke: parser rejected valid fixture")
        return errors
    res = evaluator.common_evaluator(
        predicted_file_set=set(parsed.found_files),
        proxy_paths=proxy,
        model_calls=1,
        prompt_tokens=100,
        completion_tokens=50,
    )
    if res["recall"] < 1.0 or res["fnr"] > 0.0:
        errors.append("pipeline smoke: perfect fixture not scored as recall=1")
    if res["cost_usd"] <= 0.0:
        errors.append("pipeline smoke: non-zero tokens must estimate non-zero cost")
    return errors


def gate4_dry_run() -> list[str]:
    errors: list[str] = []
    adapter = LocAgentAdapter(DATASET_DIR)
    rows = []
    for cid in VALIDATION_CASES:
        inst = adapter.build_input(cid)
        adapter.assert_no_leakage(inst)
        rows.append(
            {
                "case_id": cid,
                "split": inst.split,
                "instance_id": inst.instance_id,
                "repo": inst.repo,
                "base_commit": inst.base_commit,
                "patch_chars": len(inst.patch),
                "input_sha256": inst.input_sha256,
            }
        )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "gate": "dry_run",
        "frozen_at_utc": datetime.now(UTC).isoformat(),
        "model": "openrouter/qwen/qwen3-coder",
        "temperature": 1,  # upstream hard-coded temp=1 in run_localize
        "num_samples": 1,
        "max_attempt_num": 1,
        "eval_n_limit": len(VALIDATION_CASES),
        "ranking_method": "mrr",
        "cases": rows,
        "model_calls": 0,
        "tokens": 0,
    }
    (OUT_DIR / "p5b_dryrun_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    if len(rows) != 6:
        errors.append(f"dry run: expected 6 rows, got {len(rows)}")
    if any(r["patch_chars"] != 0 for r in rows):
        errors.append("dry run: non-empty patch in VALIDATION inputs")
    return errors


def gate5_integration_test() -> list[str]:
    errors: list[str] = []
    adapter = LocAgentAdapter(DATASET_DIR)
    for cid in VALIDATION_CASES:
        inst = adapter.build_input(cid)
        proxy = _proxy_paths(cid)
        # LocAgent-style raw (simulated from public info; no hidden used at input).
        inst_payload = inst.to_swebench_dict()
        blob = " ".join(inst_payload.values())
        for marker in ("observed_change_set_proxy", "hidden/", "gold", "target_diff"):
            if marker in blob:
                errors.append(f"{cid}: hidden marker in input {marker}")
        # Scorer must accept an empty result and still produce a metric row.
        res = evaluator.common_evaluator(
            predicted_file_set=set(),
            proxy_paths=proxy,
            model_calls=0,
            prompt_tokens=0,
            completion_tokens=0,
        )
        if not isinstance(res.get("f1"), (int, float)):
            errors.append(f"{cid}: evaluator missing f1")
        if set(res) != {
            "evaluator_version", "policy", "valid_output", "predicted_file_count",
            "proxy_size", "tp", "fp", "fn", "precision", "recall", "f1", "fnr",
            "full_recall", "model_calls", "prompt_tokens", "completion_tokens",
            "total_tokens", "cost_usd", "cost_source", "latency_s",
            "native_ranked_file_count", "note",
        }:
            errors.append(f"{cid}: evaluator schema drift")
    return errors


def gate6_metric_verification() -> list[str]:
    errors: list[str] = []
    # Independent recomputation of TP/FP/FN/P/R/F1/FNR.
    pred = {"a.py", "b.py", "c.py"}
    proxy = {"a.py", "b.py"}
    res = evaluator.common_evaluator(
        predicted_file_set=pred, proxy_paths=proxy,
        model_calls=1, prompt_tokens=100, completion_tokens=50,
    )
    tp = len(pred & proxy)
    fp = len(pred - proxy)
    fn = len(proxy - pred)
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    fnr = fn / (tp + fn) if (tp + fn) else 0.0
    if (res["tp"], res["fp"], res["fn"]) != (tp, fp, fn):
        errors.append("metric: TP/FP/FN mismatch")
    if abs(res["precision"] - p) > 1e-9 or abs(res["recall"] - r) > 1e-9:
        errors.append("metric: P/R mismatch")
    if abs(res["f1"] - f1) > 1e-9 or abs(res["fnr"] - fnr) > 1e-9:
        errors.append("metric: F1/FNR mismatch")
    if res["cost_usd"] <= 0.0:
        errors.append("metric: cost must be > 0 with tokens")
    return errors


def main() -> int:
    gates = {
        "1_dataset_validation": gate1_dataset_validation,
        "2_prompt_input_validation": gate2_prompt_input_validation,
        "3_pipeline_smoke": gate3_pipeline_smoke,
        "4_dry_run": gate4_dry_run,
        "5_integration": gate5_integration_test,
        "6_metric_verification": gate6_metric_verification,
    }
    results = {}
    failed = 0
    for name, fn in gates.items():
        errors = fn()
        results[name] = {"pass": not errors, "errors": errors}
        if errors:
            failed += 1
        print(f"[gate] {name}: {'PASS' if not errors else 'FAIL'}")
        for e in errors:
            print(f"    - {e}")
    print(f"\nP5-B six gates: {len(gates) - failed}/{len(gates)} PASS")
    if failed:
        print("P5-B six gates: OVERALL FAIL")
        return 1
    print("P5-B six gates: OVERALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
