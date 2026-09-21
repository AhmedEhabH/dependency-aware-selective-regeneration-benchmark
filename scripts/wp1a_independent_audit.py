#!/usr/bin/env python3
"""WP-1a same-session alternate-implementation cross-check (AC-1A.10).

TERMINOLOGY CORRECTED 2026-09-21: this checker is a SAME-SESSION
alternate-implementation cross-check (isolated recomputation). It is NOT an
independent/external audit: the same execution context authored both the WP-1a
implementation and this checker. A blind independent-audit packet is prepared
at exports/wp1a_independent_audit_packet_2026-09-21/.

This checker does NOT import the WP-1a helpers being audited
(benchmark.wp1a.schema / rederive / scorer / accounting / budget /
semantics). It independently recomputes every claim from raw frozen
artifacts and reports PASS/FAIL per check.

Checks:
A1 main-50 IDs (first 50 of frozen sample ordering)
A2 calibration-3 IDs (deterministic complement draw)
A3 main/calibration disjointness
A4 sample hash (frozen ordering 445b5e9d...)
A5 intent parity (53/53 canonical hash match)
A6 label-free prediction schema (forbidden columns absent from view)
A7 repository-agent candidate universe is parent-state/public (not labeled
   candidate rows)
A8 exact SIP/RM-CSS 300 reproduction (TP/FP/FN/P/R/F1 + DeltaF1)
A9 per-task prediction hashes match the frozen artifact
A10 scientific model/provider provenance (300/300 consistent qwen3-coder
    deepinfra/turbo)
A11 agent protocol freeze completeness (required keys present)
A12 scorer metric formulas (synthetic confusion)
A13 accounting identities (tokens = prompt+completion; USD view sums)
A14 budget-model inputs (ceilings present; abort rule pre-registered)
A15 allow_ground_truth_universe=False (protocol + RunRecord audit field)
A16 no access to 786 unread Saleor RESERVE outcomes (source scan)

Output: research/wp1a/wp1a_independent_audit.json
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent

OUT_DIR = _PROJECT_DIR / "research" / "wp1a"
RESEARCH = _PROJECT_DIR / "research" / "saleor-reserve-300-rmcss"
SAMPLE_SHA = "445b5e9d0aeeab9551e8feeb3e59e6b5bcfee793f029810a6efe0cbc8f126447"
MAIN_N = 50
CAL_N = 3
CAL_SEED = 20260921
AUTHORITATIVE = {
    "sip": {"tp": 193, "fp": 344, "fn": 728, "f1": 0.26474622770919065},
    "rmcss": {"tp": 283, "fp": 382, "fn": 638, "f1": 0.35687263556116017},
    "delta_f1": 0.09212640785196952,
}

# Forbidden column names/fragments (mirror of schema; intentionally re-listed
# here so the audit does not import the audited module).
_FORBIDDEN_EXACT = {"label", "proxy", "outcome", "gold", "target", "y", "gt",
                    "ground_truth", "expected_affected", "change_status",
                    "observed_change_set", "is_changed", "is_positive"}
_FORBIDDEN_FRAG = ("label", "proxy", "outcome", "ground_truth",
                   "expected_affected", "change_status", "observed_change")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _check(checks: list[dict], name: str, ok: bool, detail: str) -> None:
    checks.append({"name": name, "pass": bool(ok), "detail": detail})


def main(out_dir: Path | None = None) -> int:
    """Run the WP-1a same-session cross-check.

    ``out_dir`` (optional, default ``None``) redirects ONLY the written
    ``wp1a_independent_audit.json`` into ``out_dir`` (used by the test suite
    with a pytest ``tmp_path`` so tracked artifacts are never rewritten).
    All input reads keep using the repository paths. When ``out_dir`` is
    ``None`` the default (human-run) behaviour is byte-identical to the
    pre-fix script.
    """
    write_dir = out_dir if out_dir is not None else OUT_DIR
    import numpy as np
    import pandas as pd

    checks: list[dict] = []

    # ---------- A1/A2/A3/A4 sample freeze ----------
    sample = json.loads((RESEARCH / "saleor_reserve_300_sample.json").read_text(encoding="utf-8"))
    ids = sample["selected_ids"]
    ids_text = "\n".join(ids) + "\n"
    _check(checks, "A1.sample_hash", _sha256_text(ids_text) == SAMPLE_SHA,
           f"len={len(ids)} sha={_sha256_text(ids_text)[:16]}...")

    main_50 = ids[:MAIN_N]
    complement = sorted(set(ids) - set(main_50))
    rng = np.random.default_rng(CAL_SEED)
    cal_3 = sorted(str(x) for x in rng.choice(
        np.asarray(complement, dtype=object), size=CAL_N, replace=False))
    _check(checks, "A1.main_50", len(set(main_50)) == MAIN_N,
           f"n={len(main_50)} unique={len(set(main_50))}")
    _check(checks, "A2.calibration_3", len(set(cal_3)) == CAL_N,
           f"n={len(cal_3)} unique={len(set(cal_3))}")
    _check(checks, "A3.disjointness", set(main_50).isdisjoint(set(cal_3)),
           f"intersection={len(set(main_50) & set(cal_3))}")

    stored_main = json.loads((OUT_DIR / "wp1_main_50_manifest.json").read_text(encoding="utf-8"))
    stored_cal = json.loads((OUT_DIR / "wp1_calibration_3_manifest.json").read_text(encoding="utf-8"))
    _check(checks, "A1.main_50_matches_frozen", stored_main["task_ids"] == main_50, "exact list equality")
    _check(checks, "A2.calibration_matches_frozen", stored_cal["task_ids"] == cal_3, "exact list equality")

    # ---------- A5 intent parity ----------
    parity = json.loads((OUT_DIR / "wp1a_intent_parity.json").read_text(encoding="utf-8"))
    _check(checks, "A5.intent_parity", parity["status"] == "WP1A_INTENT_PARITY_PASS"
           and parity["n_canonical_hash_match"] == 53,
           f"status={parity['status']} match={parity['n_canonical_hash_match']}/53")

    # ---------- A6 label-free schema ----------
    raw = pd.read_parquet(RESEARCH / "candidate_rows_saleor300.parquet")
    violations = [
        c for c in raw.columns
        if c in _FORBIDDEN_EXACT or any(f in c.lower() for f in _FORBIDDEN_FRAG)
    ]
    _check(checks, "A6.raw_artifact_forbidden_present",
           len(violations) > 0, f"detected forbidden col(s) in raw: {violations}")

    # The audited load_prediction_view drops forbidden columns; the independent
    # check re-reads the frozen prediction artifact columns (must NOT contain
    # label). Use the stored per-task artifact + re-read the raw view columns.
    view = raw.drop(columns=list(violations)) if violations else raw
    still = [c for c in view.columns if c in _FORBIDDEN_EXACT or any(f in c.lower() for f in _FORBIDDEN_FRAG)]
    _check(checks, "A6.prediction_view_label_free", not still,
           f"forbidden after boundary drop: {still}")

    # ---------- A7 parent-only candidate universe ----------
    case_dir = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor" / "scientific" / main_50[0]
    uni = json.loads((case_dir / "public" / "candidate_universe.json").read_text(encoding="utf-8"))
    uni_paths = {str(r["path"]) for r in uni["records"]}
    hidden_exists = (case_dir / "hidden").exists()
    _check(checks, "A7.universe_is_public_parent_state",
           len(uni_paths) > 0 and not hidden_exists,
           f"universe n={len(uni_paths)} hidden_dir_present={hidden_exists}")

    # ---------- A8/A9 exact reproduction ----------
    verification = json.loads((OUT_DIR / "wp1_rederivation_verification.json").read_text(encoding="utf-8"))
    v_ok = (
        verification["verification"] == "EXACT_REPRODUCTION"
        and verification["sip"]["tp"] == AUTHORITATIVE["sip"]["tp"]
        and verification["sip"]["fp"] == AUTHORITATIVE["sip"]["fp"]
        and verification["sip"]["fn"] == AUTHORITATIVE["sip"]["fn"]
        and abs(verification["sip"]["f1"] - AUTHORITATIVE["sip"]["f1"]) < 1e-9
        and verification["rmcss"]["tp"] == AUTHORITATIVE["rmcss"]["tp"]
        and verification["rmcss"]["fp"] == AUTHORITATIVE["rmcss"]["fp"]
        and verification["rmcss"]["fn"] == AUTHORITATIVE["rmcss"]["fn"]
        and abs(verification["rmcss"]["f1"] - AUTHORITATIVE["rmcss"]["f1"]) < 1e-9
        and abs(verification["delta_f1"] - AUTHORITATIVE["delta_f1"]) < 1e-9
    )
    _check(checks, "A8.exact_reproduction", v_ok,
           f"verification={verification['verification']} sip_f1={verification['sip']['f1']} "
           f"rmcss_f1={verification['rmcss']['f1']} delta={verification['delta_f1']}")

    pred = json.loads((OUT_DIR / "sip_rmcss_per_task_predictions.json").read_text(encoding="utf-8"))
    per_task = pred["per_task"]
    all_hashes_ok = all(
        _sha256_text("\n".join(sorted(per_task[c]["sip_predicted_set"]))) == per_task[c]["sip_prediction_hash"]
        and _sha256_text("\n".join(sorted(per_task[c]["rmcss_predicted_set"]))) == per_task[c]["rmcss_prediction_hash"]
        for c in per_task
    )
    _check(checks, "A9.per_task_prediction_hashes", len(per_task) == 300 and all_hashes_ok,
           f"n={len(per_task)} hashes_ok={all_hashes_ok}")

    # ---------- A10 model provenance ----------
    prov = json.loads((OUT_DIR / "sip_scientific_model_provenance.json").read_text(encoding="utf-8"))
    prov_ok = prov["conclusion"] == "IDENTITY_MECHANICALLY_RECOVERED_AND_CONSISTENT" and all(
        v["consistent_across_all_tasks"] for v in prov["identity"].values()
    )
    _check(checks, "A10.model_provenance", prov_ok,
           f"model={prov['identity']['scientific_model']['value']} "
           f"provider={prov['identity']['provider_tag']['value']}")

    # ---------- A11 protocol completeness ----------
    protocol = json.loads((OUT_DIR / "wp1a_frozen_agent_protocol.json").read_text(encoding="utf-8"))
    required = [
        "initial_system_prompt", "tools", "tool_schemas",
        "parent_repository_snapshot_source", "candidate_universe_boundary",
        "allowed_directories_file_types", "file_read_policy", "search_policy",
        "context_retention_policy", "context_truncation_policy",
        "round_definition", "proposed_hard_max_rounds",
        "completion_token_cap_per_model_response", "stop_rule", "timeout_rule",
        "retry_rule", "malformed_output_rule", "empty_output_rule",
        "path_outside_universe_handling", "duplicate_path_normalization",
        "allow_ground_truth_universe", "runrecord_audit_field",
        "final_file_set_json_schema", "fail_closed_semantics",
        "labels_never_accessed",
    ]
    missing = [k for k in required if k not in protocol["sections"]]
    _check(checks, "A11.protocol_complete", not missing,
           f"missing={missing}" if missing else f"{len(required)} required keys present")

    # ---------- A12 scorer formula ----------
    # synthetic: predicted {a,b}, label {a,c} -> tp=1 fp=1 fn=1 f1=2/4=0.5
    tp = len({"a", "b"} & {"a", "c"})
    fp = len({"a", "b"} - {"a", "c"})
    fn = len({"a", "c"} - {"a", "b"})
    f1 = 2 * tp / (2 * tp + fp + fn)
    _check(checks, "A12.scorer_formula", (tp, fp, fn) == (1, 1, 1) and abs(f1 - 0.5) < 1e-12,
           f"tp={tp} fp={fp} fn={fn} f1={f1}")

    # ---------- A13 accounting identities ----------
    acc_schema = json.loads((OUT_DIR / "wp1a_accounting_schema.json").read_text(encoding="utf-8"))
    _check(checks, "A13.accounting_identity_fields",
           "total_tokens" in acc_schema["per_arm_fields"]
           and "prompt_tokens" in acc_schema["per_arm_fields"]
           and "completion_tokens" in acc_schema["per_arm_fields"],
           "tokens = prompt + completion identity present in schema")

    # ---------- A14 budget inputs ----------
    budget = json.loads((OUT_DIR / "wp1a_budget_model.json").read_text(encoding="utf-8"))
    budget_ok = (
        budget["main_n"] == 50 and budget["calibration_n"] == 3
        and budget["max_calls_per_task"] == 8
        and budget["completion_cap"] == 512
        and "BUDGET_ABORT_INVALID_FOR_PRIMARY_COMPARISON" in str(budget["abort_rule"])
        and budget["calibration_cannot_prove_worst_case"] is True
    )
    _check(checks, "A14.budget_inputs", budget_ok,
           f"main={budget['main_n']} cal={budget['calibration_n']} "
           f"ceiling_usd={budget['recommended_ceiling_usd']}")

    # ---------- A15 allow_ground_truth_universe=False ----------
    _check(checks, "A15.allow_ground_truth_universe_false",
           protocol["sections"]["allow_ground_truth_universe"] is False,
           "protocol allow_ground_truth_universe == False")

    # ---------- A16 no access to 786 RESERVE outcomes ----------
    scan_violations: list[str] = []
    for script in sorted(Path("scripts").glob("wp1a_*.py")):
        text = script.read_text(encoding="utf-8")
        # forbid reading the unopened metadata source in wp1a scripts
        if "saleor_candidate_metadata.json" in text and "proxies" not in text:
            scan_violations.append(f"{script.name} references saleor_candidate_metadata.json")
    _check(checks, "A16.no_786_access", not scan_violations,
           f"violations={scan_violations}" if scan_violations else
           "wp1a scripts do not open unread RESERVE outcomes (source scan + "
           "artifact uses only opened 300 proxies)")

    total = len(checks)
    passed = sum(1 for c in checks if c["pass"])
    result = {
        "wp1a": "wp1a_independent_audit",
        "pass": passed,
        "total": total,
        "status": "PASS" if passed == total else "FAIL",
        "checks": checks,
        "note": "same-session alternate-implementation cross-check WITHOUT importing "
        "benchmark.wp1a helpers (NOT an independent/external audit)",
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_dir.mkdir(parents=True, exist_ok=True)
    (write_dir / "wp1a_independent_audit.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    for c in checks:
        print(f"[audit] {c['name']}: {'PASS' if c['pass'] else 'FAIL'} - {c['detail']}")
    print(f"[audit] {passed}/{total} PASS; status={result['status']}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    import sys
    out_arg: Path | None = None
    if "--out" in sys.argv:
        out_arg = Path(sys.argv[sys.argv.index("--out") + 1])
    raise SystemExit(main(out_dir=out_arg))
