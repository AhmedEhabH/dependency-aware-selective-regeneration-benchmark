#!/usr/bin/env python3
"""ZERO-API verifier for M1A — CONTROLLED 4096-CAP FEASIBILITY BOUNDARY.

Verifies the persisted M1A evidence WITHOUT any model/API calls:

- PROMPT_CONTROLLED_DIFF PASS (only SERIALIZATION_POLICY differs between arms)
- common schema identity (frozen hash)
- representation equivalence property tests (D_s(E_s(pi)) == pi)
- capability-probe usage capture (usage_known True, exact tokens)
- finish_reason classification (Probe A = length; Probe B = stop)
- truncation classification (Probe A truncated at cap)
- raw-response SHA-256 verification against persisted .sha256 sidecars
- decoded Sparse-v2 policy (144 candidates reconstructed)
- ZERO scientific study cells executed (no run_records.jsonl)
- six deterministic gates + independent audit (recomputed locally)
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(PROJECT_DIR / "src"))

STUDY_DIR = PROJECT_DIR / "research" / "controlled-encoding-ablation-01"
STUDY_ID = "scientific-djangocms-controlled-encoding-ablation-01"
COMMON_CAP = 4096

from benchmark.selection import encoding_ablation as ea  # noqa: E402


def _load_json(name: str) -> dict[str, Any]:
    path = STUDY_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"missing evidence: {name}")
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    failures: list[str] = []
    checks: list[dict[str, Any]] = []

    def check(label: str, ok: bool, detail: Any = None) -> None:
        checks.append({"check": label, "ok": bool(ok), "detail": detail})
        print(f"{'PASS' if ok else 'FAIL'}  {label}")
        if not ok:
            failures.append(label)

    print("=== M1A ZERO-API VERIFIER ===")

    # 1. Prompt controlled diff
    prompt_control = _load_json("prompt_control.json")
    check(
        "prompt_controlled_diff",
        prompt_control.get("PROMPT_CONTROLLED_DIFF") == "PASS"
        and all(c.get("ok") for c in prompt_control.get("checks", [])),
        {"PROMPT_CONTROLLED_DIFF": prompt_control.get("PROMPT_CONTROLLED_DIFF")},
    )

    # 2. Schema identity (frozen hash matches module)
    check(
        "schema_identity_frozen",
        ea.COMMON_SCHEMA_SHA256 == prompt_control.get("common_schema_sha256"),
        {"module": ea.COMMON_SCHEMA_SHA256, "frozen": prompt_control.get("common_schema_sha256")},
    )
    # schema allows variable-length decisions and does not force Full/Sparse
    schema = ea.COMMON_ABLATION_SCHEMA
    decisions = schema["properties"]["decisions"]
    actions = schema["properties"]["decisions"]["items"]["properties"]["action"]["enum"]
    check(
        "schema_variable_length_neutral",
        decisions.get("minItems", 0) == 0
        and set(actions) == {"PRESERVE", "REGENERATE", "VALIDATE", "HUMAN_REVIEW"},
        {"minItems": decisions.get("minItems"), "maxItems": decisions.get("maxItems"), "actions": actions},
    )

    # 3. Representation equivalence property tests
    rep = ea.representation_equivalence_checks()
    check(
        "representation_equivalence",
        rep.get("REPRESENTATION_EQUIVALENCE") == "PASS" and rep.get("all_pass"),
        {"label": "D_s(E_s(pi)) == pi", "checks": len(rep.get("checks", []))},
    )

    # 4. Six pre-benchmark gates + audit (recompute locally, zero calls)
    spec = importlib.util.spec_from_file_location(
        "cea_exec", PROJECT_DIR / "scripts" / "controlled_encoding_ablation_execute.py"
    )
    exe = importlib.util.module_from_spec(spec)
    sys.modules["cea_exec"] = exe
    spec.loader.exec_module(exe)
    gates = exe.run_gates()
    for g in gates:
        check(f"gate_{g['gate']}_{g['name']}", bool(g["passed"]), g.get("checks"))
    audit = exe._independent_audit()
    check("independent_audit", bool(audit["passed"]), audit.get("checks"))

    # 5. Capability probes
    probes = _load_json("capability_probes.json")
    pa = probes["probes"]["probe_a_full_v2"]
    pb = probes["probes"]["probe_b_sparse_v2"]

    check("probe_a_transport_ok", bool(pa.get("transport_ok")), pa.get("error", ""))
    check("probe_a_usage_known", bool(pa.get("usage_known")), pa.get("usage"))
    check(
        "probe_a_finish_reason_length",
        pa.get("finish_reason") == "length",
        pa.get("finish_reason"),
    )
    check(
        "probe_a_completion_at_cap",
        pa["usage"].get("completion_tokens") == COMMON_CAP,
        pa["usage"].get("completion_tokens"),
    )
    check(
        "probe_a_truncation_classified",
        bool(pa.get("finish_reason") == "length"),
        {"truncation": True, "schema_valid": pa.get("schema_valid")},
    )

    check("probe_b_transport_ok", bool(pb.get("transport_ok")), pb.get("error", ""))
    check("probe_b_usage_known", bool(pb.get("usage_known")), pb.get("usage"))
    check(
        "probe_b_finish_reason_stop",
        pb.get("finish_reason") == "stop",
        pb.get("finish_reason"),
    )
    check(
        "probe_b_decoded_144_candidates",
        pb.get("decoded_candidate_count") == 144,
        {"decoded_candidate_count": pb.get("decoded_candidate_count"),
         "write_set_ids": pb.get("decoded_write_set_ids")},
    )
    check(
        "probe_b_semantic_valid",
        bool(pb.get("schema_valid")) and not pb.get("errors"),
        pb.get("errors"),
    )

    # 6. Raw-response SHA verification against persisted sidecars
    raw_dir = STUDY_DIR / "probes" / "raw"
    for label in ("probe_a_full_v2", "probe_b_sparse_v2"):
        raw_path = raw_dir / f"{label}.txt"
        sha_path = raw_dir / f"{label}.sha256"
        if not raw_path.is_file() or not sha_path.is_file():
            check(f"raw_persisted_{label}", False, "missing raw or sha file")
            continue
        actual = _sha256_file(raw_path)
        expected = sha_path.read_text(encoding="utf-8").strip()
        recorded = (
            pa.get("raw_response_sha256") if label == "probe_a_full_v2"
            else pb.get("raw_response_sha256")
        )
        check(
            f"raw_sha_{label}",
            actual == expected == recorded,
            {"file": actual, "sidecar": expected, "recorded": recorded},
        )

    # 7. ZERO scientific study cells executed
    records_path = STUDY_DIR / "run_records.jsonl"
    check(
        "zero_scientific_study_cells",
        not records_path.is_file() or records_path.read_text(encoding="utf-8").strip() == "",
        "no run_records.jsonl or empty -> zero study cells",
    )
    check(
        "manifest_not_frozen",
        not (STUDY_DIR / "manifest_60.json").is_file(),
        "manifest_60.json absent -> study never froze/ran",
    )

    # 8. Endpoint freeze identity
    freeze = _load_json("endpoint_freeze.json")
    check(
        "endpoint_freeze_model_provider",
        freeze.get("model_id") == "qwen/qwen3-coder"
        and freeze.get("provider_name") == "DeepInfra"
        and freeze.get("provider_tag") == "deepinfra/turbo",
        {"model": freeze.get("model_id"), "provider": freeze.get("provider_tag")},
    )
    check(
        "endpoint_freeze_frozen_cap",
        freeze.get("completion_cap") == 4096 and freeze.get("temperature") == 0.0,
        {"cap": freeze.get("completion_cap"), "temperature": freeze.get("temperature")},
    )

    print("\n=== M1A VERIFIER RESULT ===")
    print(f"TOTAL_CHECKS={len(checks)}")
    print(f"PASSED={len(checks) - len(failures)}")
    print(f"FAILED={len(failures)}")
    print("M1A_VERIFIER=" + ("PASS" if not failures else "FAIL"))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
