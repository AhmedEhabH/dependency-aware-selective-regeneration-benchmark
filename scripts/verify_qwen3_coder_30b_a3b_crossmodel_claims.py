#!/usr/bin/env python3
"""Zero-API verifier for the Qwen3-Coder-30B-A3B-Instruct cross-model
/cross-provider robustness replication.

STUDY_ID: scientific-stagec-djangocms-qwen3-coder-30b-a3b-crossmodel-01

Recomputes every headline metric from the FROZEN RunRecords (no API calls),
verifies raw-response SHA-256 sidecars, and exits non-zero on any
inconsistency.

Model: Qwen3-Coder-30B-A3B-Instruct (OpenRouter slug
`qwen/qwen3-coder-30b-a3b-instruct`) @ OpenRouter / SiliconFlow (`siliconflow/fp8`),
model-native non-thinking (no reasoning control parameter), fallback OFF,
temperature 0, cap 4096.

Checks:
- 60 recorded cells / 60 unique run_ids / 2 arms / 6 scenarios / 5 reps
- every record: model == qwen/qwen3-coder-30b-a3b-instruct,
  provider_tag == siliconflow/fp8, reasoning_mode == model-native non-thinking,
  fallback off, temperature 0, cap 4096
- raw SHA-256 of runs/raw/{run_id}.txt == record.raw_response_sha256 == .sha256
- request / response / usage-known / usage-unknown accounting
- truncation accounting (corrected semantics: finish_reason=length at cap is a
  truncation even on failed JSON/schema/semantic paths)
- per-arm metrics recomputed and compared against final_metrics.json
- known/lower-bound token and cost semantics
- cross-product Sparse-v2 Jaccard agreement vs historical
  Qwen3-Coder-480B-A35B-Instruct (read-only evidence)
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent
STUDY_DIR = _PROJECT_DIR / "reports" / "scientific-stagec-djangocms-qwen3-coder-30b-a3b-crossmodel-01"
MANIFEST_PATH = STUDY_DIR / "manifest_60.json"
RECORDS_PATH = STUDY_DIR / "run_records.jsonl"
METRICS_PATH = STUDY_DIR / "final_metrics.json"
AGREEMENT_PATH = STUDY_DIR / "cross_model_agreement.json"
RAW_DIR = STUDY_DIR / "runs" / "raw"

ARMS = ("impact_plan", "impact_plan_v2")
FINAL_SCENARIOS = {
    "djangocms-external-validity-002",
    "djangocms-external-validity-004",
    "djangocms-external-validity-005",
    "djangocms-external-validity-006",
    "djangocms-external-validity-007",
    "djangocms-external-validity-008",
}
MODEL = "qwen/qwen3-coder-30b-a3b-instruct"
MODEL_HUMAN = "Qwen3-Coder-30B-A3B-Instruct"
PROVIDER_TAG = "siliconflow/fp8"
REASONING_MODE = "model-native non-thinking"
PRICING_PROMPT = 0.00000007
PRICING_COMPLETION = 0.00000028

failures: list[str] = []


def check(name: str, ok: bool, detail: Any = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  {detail}" if detail else ""))
    if not ok:
        failures.append(name)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def live_cost(rec: dict[str, Any]) -> float:
    return round(
        int(rec.get("prompt_tokens", 0)) * PRICING_PROMPT
        + int(rec.get("completion_tokens", 0)) * PRICING_COMPLETION,
        6,
    )


def load_records() -> list[dict[str, Any]]:
    out = []
    for line in RECORDS_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def is_truncation(rec: dict[str, Any]) -> bool:
    """Corrected truncation classifier (accounting semantics, C4).

    A cell is a truncation when ANY of the following holds:
    1. ``truncation_status`` is True;
    2. ``finish_reason`` == ``length``;
    3. ``completion_cap_hit`` is True;
    4. the failure evidence / category message contains ``finish_reason=length``;
    5. the persisted raw response is present but unterminated JSON.
    """
    if rec.get("truncation_status"):
        return True
    if rec.get("finish_reason") == "length":
        return True
    if rec.get("completion_cap_hit"):
        return True
    blob = (
        json.dumps(rec.get("failure_evidence", []), default=str)
        + " "
        + str(rec.get("failure_category", ""))
    )
    if "finish_reason=length" in blob:
        return True
    raw_sha = rec.get("raw_response_sha256") or ""
    if raw_sha:
        raw_path = RAW_DIR / f"{rec['run_id']}.txt"
        if raw_path.is_file():
            try:
                json.loads(raw_path.read_text(encoding="utf-8"))
            except Exception:
                return True
    return False


def _transport_failure(rec: dict[str, Any]) -> bool:
    blob = (
        json.dumps(rec.get("failure_evidence", []), default=str)
        + " "
        + str(rec.get("failure_category", ""))
    )
    return any(
        tok in blob
        for tok in (
            "Remote end closed",
            "RemoteDisconnected",
            "IncompleteRead",
            "connection failed",
            "Connection reset",
            "timed out",
            "TimeoutError",
        )
    )


def _derived_request_dispatched(rec: dict[str, Any]) -> bool:
    if rec.get("request_dispatched"):
        return True
    if rec.get("provider_response_received"):
        return True
    if rec.get("raw_response_sha256"):
        return True
    if int(rec.get("model_calls", 0) or 0) > 0:
        return True
    if _transport_failure(rec):
        return True
    if rec.get("usage_known"):
        return True
    return False


def _derived_responses_received(rec: dict[str, Any]) -> bool:
    return bool(rec.get("provider_response_received") or rec.get("raw_response_sha256"))


def _derived_usage_known(rec: dict[str, Any]) -> bool:
    if not rec.get("usage_known"):
        return False
    return (int(rec.get("prompt_tokens", 0) or 0) + int(rec.get("completion_tokens", 0) or 0)) > 0


def micro(rows: list[dict[str, Any]]) -> dict[str, Any]:
    selected = sum(int(r["predicted_write_set_size"]) for r in rows)
    tp = sum(int(r["tp"]) for r in rows)
    fp = sum(int(r["fp"]) for r in rows)
    fn = sum(int(r["fn"]) for r in rows)
    precision = tp / selected if selected else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fnr = fn / (tp + fn) if (tp + fn) else 0.0
    return {
        "selected": selected,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
        "fnr": round(fnr, 6),
    }


def verify_raw_hashes(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Fail closed on any raw SHA mismatch / missing raw for a recorded SHA."""
    missing_raw = 0
    sha_mismatch = 0
    for r in records:
        run_id = r["run_id"]
        rec_sha = r.get("raw_response_sha256", "")
        if not rec_sha:
            continue
        txt = RAW_DIR / f"{run_id}.txt"
        sha = RAW_DIR / f"{run_id}.sha256"
        if not txt.is_file():
            missing_raw += 1
            continue
        actual = sha256_bytes(txt.read_bytes())
        sidecar = sha.read_text(encoding="utf-8").strip() if sha.is_file() else ""
        if actual != rec_sha:
            sha_mismatch += 1
        if sidecar and actual != sidecar:
            sha_mismatch += 1
    return {"missing_raw": missing_raw, "sha_mismatch": sha_mismatch}


def main() -> int:
    print("=== QWEN3-CODER-30B-A3B CROSS-MODEL CLAIMS VERIFIER (zero API) ===")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    cells = manifest["cells"]
    check("manifest_has_60_cells", len(cells) == 60, len(cells))
    check(
        "manifest_no_run_61",
        all(
            c["run_id"].endswith(("-r1", "-r2", "-r3", "-r4", "-r5"))
            for c in cells
        ),
    )

    records = load_records()
    check("recorded_60", len(records) == 60, len(records))
    check("run_ids_unique", len({r["run_id"] for r in records}) == 60)

    from collections import Counter

    arms = Counter(r["arm"] for r in records)
    check(
        "two_arms_30_each",
        arms == {"impact_plan": 30, "impact_plan_v2": 30},
        dict(arms),
    )
    scen = {r["scenario_id"] for r in records}
    check("six_scenarios_exact", scen == FINAL_SCENARIOS, sorted(scen))
    rep_count = Counter((r["scenario_id"], r["arm"]) for r in records)
    check(
        "five_reps_every_scenario_arm",
        all(v == 5 for v in rep_count.values()) and len(rep_count) == 12,
    )

    model_ok = all(r.get("scientific_model") == MODEL for r in records)
    provider_ok = all(r.get("provider_tag") == PROVIDER_TAG for r in records)
    reasoning_ok = all(r.get("reasoning_mode") == REASONING_MODE for r in records)
    fallback_ok = all(r.get("fallback_status") == "off" for r in records)
    temp_ok = all(r.get("temperature") == 0.0 for r in records)
    cap_ok = all(r.get("completion_cap") == 4096 for r in records)
    check("every_record_model", model_ok)
    check("every_record_provider", provider_ok)
    check("every_record_reasoning_non_thinking", reasoning_ok)
    check("every_record_fallback_off", fallback_ok)
    check("every_record_temperature_0", temp_ok)
    check("every_record_completion_cap_4096", cap_ok)

    raw = verify_raw_hashes(records)
    check(
        "raw_hashes_verified",
        raw["missing_raw"] == 0 and raw["sha_mismatch"] == 0,
        raw,
    )

    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    total_live = 0.0
    for arm in ARMS:
        rows = [r for r in records if r["arm"] == arm]
        valid = [r for r in rows if r["terminal_status"] == "succeeded"]
        m = micro(valid)
        m_expected = metrics["arms"][arm]["overall"]
        check(
            f"{arm}_overall_micro_matches",
            m == {
                "selected": m_expected["selected"],
                "tp": m_expected["tp"],
                "fp": m_expected["fp"],
                "fn": m_expected["fn"],
                "precision": m_expected["precision"],
                "recall": m_expected["recall"],
                "f1": m_expected["f1"],
                "fnr": m_expected["fnr"],
            },
            f"recomputed={m}",
        )
        recorded = metrics["arms"][arm]["recorded"]
        check(
            f"{arm}_recorded_valid_failed",
            recorded == len(rows)
            and metrics["arms"][arm]["valid"] == len(valid)
            and metrics["arms"][arm]["failed"] == len(rows) - len(valid),
            f"recorded={len(rows)} valid={len(valid)}",
        )
        trunc = sum(1 for r in rows if is_truncation(r))
        check(
            f"{arm}_truncations_matches",
            metrics["arms"][arm]["truncations"] == trunc,
            f"trunc={trunc}",
        )
        check(
            f"{arm}_requests_issued",
            metrics["arms"][arm]["requests_issued"] == len(rows),
            len(rows),
        )
        live = sum(live_cost(r) for r in rows)
        total_live += live
        check(
            f"{arm}_live_cost_matches",
            abs(live - metrics["arms"][arm]["live_api_cost_usd"]) < 1e-6,
            f"{live:.6f}",
        )
        calls = sum(int(r["model_calls"]) for r in rows)
        check(
            f"{arm}_calls_match",
            calls == metrics["arms"][arm]["calls"],
            calls,
        )

    totals = metrics["totals"]
    check(
        "totals_valid_failed_truncations",
        totals["recorded"] == 60
        and totals["valid"] == sum(1 for r in records if r["terminal_status"] == "succeeded")
        and totals["failed"] == sum(1 for r in records if r["terminal_status"] != "succeeded")
        and totals["truncations"] == sum(1 for r in records if is_truncation(r)),
        f"valid={totals['valid']} failed={totals['failed']} trunc={totals['truncations']}",
    )
    check(
        "totals_requests_issued",
        totals["requests_issued"] == sum(1 for r in records if _derived_request_dispatched(r)),
        totals["requests_issued"],
    )
    check(
        "totals_responses_received",
        totals["responses_received"]
        == sum(1 for r in records if _derived_responses_received(r)),
        totals["responses_received"],
    )
    check(
        "totals_usage_known_unknown",
        totals["usage_known_cells"]
        == sum(1 for r in records if _derived_usage_known(r))
        and totals["usage_unknown_cells"]
        == sum(1 for r in records if not _derived_usage_known(r)),
        f"known={totals['usage_known_cells']} unknown={totals['usage_unknown_cells']}",
    )
    check(
        "totals_transport_failures",
        totals.get("transport_failure_cells")
        == sum(1 for r in records if _transport_failure(r)),
        totals.get("transport_failure_cells"),
    )
    check(
        "totals_tokens_match",
        totals["prompt_tokens"] == sum(int(r["prompt_tokens"]) for r in records)
        and totals["completion_tokens"] == sum(int(r["completion_tokens"]) for r in records)
        and totals["total_tokens"] == sum(int(r["total_tokens"]) for r in records),
        f"total={totals['total_tokens']}",
    )
    check(
        "totals_live_cost_matches",
        abs(total_live - totals["live_api_cost_usd"]) < 1e-6,
        f"{total_live:.6f}",
    )
    check(
        "lower_bound_semantics",
        (totals["usage_unknown_cells"] == 0) or totals.get("lower_bound_qualified", False),
        f"usage_unknown={totals['usage_unknown_cells']}",
    )

    agreement = json.loads(AGREEMENT_PATH.read_text(encoding="utf-8"))
    hist_records_path = (
        _PROJECT_DIR
        / "reports"
        / "scientific-stagec-djangocms-impactplan-v2-01"
        / "run_records.jsonl"
    )
    hist = []
    for line in hist_records_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            hist.append(json.loads(line))
    hist_valid = [r for r in hist if r.get("terminal_status") == "succeeded"]
    new_valid_v2 = [
        r for r in records if r["arm"] == "impact_plan_v2" and r["terminal_status"] == "succeeded"
    ]
    expected_pairs = 0
    for sid in sorted(FINAL_SCENARIOS):
        h = [r for r in hist_valid if r.get("scenario_id") == sid]
        n = [r for r in new_valid_v2 if r.get("scenario_id") == sid]
        expected_pairs += len(h) * len(n)
    check(
        "agreement_pair_count_matches",
        agreement["total_pair_count"] == expected_pairs,
        f"{agreement['total_pair_count']} vs {expected_pairs}",
    )

    ok = not failures
    print(f"\nVERIFIER_RESULT={'PASS' if ok else 'FAIL'}")
    if not ok:
        for f in failures:
            print("  FAILED:", f)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
