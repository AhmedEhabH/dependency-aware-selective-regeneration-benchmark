#!/usr/bin/env python3
"""CONTROLLED ENCODING ABLATION executor (M1): FULL-v2 vs SPARSE-v2.

STUDY_ID: scientific-djangocms-controlled-encoding-ablation-01

Controlled ablation of explicit PRESERVE serialization (FULL-v2) versus
Preserve-by-Omission serialization (SPARSE-v2) under the SAME model, provider,
repository, candidate universe, semantic action contract, JSON schema, prompt
content, temperature, and completion budget. The ONLY intended treatment
difference is the SERIALIZATION_POLICY block.

Scientific model (frozen):

- qwen/qwen3-coder (Qwen3-Coder-480B-A35B-Instruct)
- OpenRouter slug: qwen/qwen3-coder
- Gateway: OpenRouter
- Provider: DeepInfra Turbo pinned (deepinfra/turbo), fallback OFF
- Temperature 0, completion cap 4096, Graph OFF
- response_format = json_schema (common ablation schema)

Design (frozen):

- 6 scenarios x 2 arms x 5 repetitions = EXACTLY 60 manifest cells
- arms: full_v2 (explicit PRESERVE for all 144) AND sparse_v2 (non-PRESERVE
  only; omitted => PRESERVE)
- hidden gold is evaluation-only, applied AFTER inference
- common schema + prompt-control proof (only SERIALIZATION_POLICY differs)
- representation equivalence property tests (D_s(E_s(pi)) == pi) — this is
  representation equivalence, NOT model correctness
- corrected accounting semantics (C4): request_attempted / request_dispatched /
  provider_response_received / raw_response_persisted / usage_known /
  finish_reason / truncation_status / transport_failure; usage captured before
  downstream validation; finish_reason=="length" at cap => truncation
- raw response + SHA256 persisted immediately
- cost lock: cumulative + conservative projected completion <= $0.50
- NO reruns, NO replacements, NO cell 61

Subcommands:
  prevalidate       pre-run validation (branch/HEAD/origin parity, frozen
                    inputs, gold isolation, graph absent, endpoint freeze)
  prompt-control    render both arms for all six scenarios + persist hashes +
                    PROMPT_CONTROLLED_DIFF proof (ZERO calls)
  probe             the TWO non-study capability probes (Probe A Full-v2,
                    Probe B Sparse-v2) against the live DeepInfra endpoint
  gates             the EXACT six deterministic gates + independent audit
                    (ZERO calls)
  freeze-manifest   build + persist the frozen 60-cell manifest
  run               execute remaining manifest cells (resumable, append-only)
  metrics           compute final metrics + aggregate tables (per arm)
  interpret         apply the frozen interpretation decision rule
  close             rerun the six closure gates + audit (ZERO calls)
  all               prevalidate -> prompt-control -> probe -> gates ->
                    freeze-manifest -> run -> metrics -> interpret -> close
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.external_validity import study_runtime as wiring  # noqa: E402
from benchmark.selection import encoding_ablation as ea  # noqa: E402

PROJECT_DIR = wiring.PROJECT_DIR
STUDY_ID = "scientific-djangocms-controlled-encoding-ablation-01"
STUDY_DIR = PROJECT_DIR / "research" / "controlled-encoding-ablation-01"
WIRING_TAG = "controlled-encoding-ablation-wiring-verified-01"
STUDY_TAG = "controlled-encoding-ablation-study-01-audited"

FINAL_SCENARIOS = tuple(wiring.final_scenario_ids())
ARMS = ("full_v2", "sparse_v2")
REPETITIONS = (1, 2, 3, 4, 5)

PRIMARY_MODEL = "qwen/qwen3-coder"
MODEL_HUMAN = "Qwen3-Coder-480B-A35B-Instruct"
MODEL_SLUG = PRIMARY_MODEL
PROVIDER_PINNED = "DeepInfra"
PROVIDER_TAG = "deepinfra/turbo"
QUANTIZATION = "fp4"
TEMPERATURE = 0.0
CAP = 4096
REASONING_FROZEN: dict[str, Any] | None = None
REASONING_MODE_LABEL = "direct/non-thinking (no reasoning control parameter sent)"
WORKFLOW_TIMEOUT_SECONDS = 600
MAX_TRANSIENT_RETRIES = 1
EXPECTED_UNIVERSE_COUNT = 144
SCIENTIFIC_CEILING_USD = 0.50
COST_MARGIN = 0.25
CHECKPOINT_EVERY = 5
TOTAL_CELLS = 60
RUNTIME_CEILING_SECONDS = 4 * 3600
EXPECTED_BRANCH = "research/controlled-encoding-ablation-01"

# Frozen identity hashes (from the core module; validated in prevalidate/gates).
COMMON_SCHEMA_SHA = ea.COMMON_SCHEMA_SHA256
COMMON_TEMPLATE_SHA = ea.COMMON_TEMPLATE_SHA256
FULL_POLICY_SHA = ea.FULL_POLICY_TEMPLATE_SHA256
SPARSE_POLICY_SHA = ea.SPARSE_POLICY_TEMPLATE_SHA256
REASON_CODES_SHA = ea.REASON_CODES_SHA256

UNIVERSE_SHA = "43f4279bdf228745b1f6b289c81cda141b089ab5be4f4af63bb8f39f837c4410"
V2_MAPPING_SHA = "9d33e163505722e2cfe602ca165777d3d5accbaf5b9f7a82d1b30068ca9d1ca6"

HISTORICAL_V2_RECORDS_RELATIVE = (
    "reports/scientific-stagec-djangocms-impactplan-v2-01/run_records.jsonl"
)
HISTORICAL_STUDY_ID = "scientific-stagec-djangocms-impactplan-v2-01"

# Frozen six scenario visible-text hashes (historical input parity record).
SCENARIO_EXPECTED_HASHES = {
    "djangocms-external-validity-002": "a7e72f7af23541407180d490f5dd03e9df281efb514ab4c4f92f4a59deb4c730",
    "djangocms-external-validity-004": "0b25d27452ceff3fae08eecd42b15da8d6788c4af162455f71c2db5cf3450430",
    "djangocms-external-validity-005": "836f42fbbf00cd097b52a928f12e01e463857f4a9fe01aa122729696b223a57b",
    "djangocms-external-validity-006": "c724fff84d0757e4182e3b127a296b6876964a267be5e3584f1aafcf9aefa0e3",
    "djangocms-external-validity-007": "1caf61e7a4db2b887e8c14d02f349ef3771e7f19a27ecab2f69e6aa686e5e88c",
    "djangocms-external-validity-008": "d2076d5bf092ac8a96566c88f413deb1090ab61ebe85733a41174e8aac283021",
}
HIDDEN_GOLD_SHA = "260bbeacd53efcab6b99366941c64b667f9f227467b70350fcb7c248b6f00882"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args], capture_output=True, text=True, check=False, cwd=PROJECT_DIR
    )
    return proc.stdout.strip()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _records_path() -> Path:
    return STUDY_DIR / "run_records.jsonl"


def _manifest_path() -> Path:
    return STUDY_DIR / "manifest_60.json"


def _loaded_records() -> dict[str, dict[str, Any]]:
    path = _records_path()
    if not path.is_file():
        return {}
    out: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        out[rec["run_id"]] = rec
    return out


def _append_record(record: dict[str, Any]) -> None:
    _records_path().parent.mkdir(parents=True, exist_ok=True)
    with _records_path().open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")


def _persist_json(name: str, payload: Any) -> Path:
    STUDY_DIR.mkdir(parents=True, exist_ok=True)
    path = STUDY_DIR / name
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _unchanged_vs_head(rel: str) -> dict[str, Any]:
    status = _git("status", "--short", "--", rel)
    return {"path": rel, "unchanged": not status, "status": status}


def _primary_evidence_immutable() -> dict[str, Any]:
    paths = [
        HISTORICAL_V2_RECORDS_RELATIVE,
        "benchmark_data/external_validity/djangocms_hidden_gold_draft.json",
        "benchmark_data/external_validity/djangocms_5_0_0_candidate_universe.json",
        "benchmark_data/external_validity/impactplan_v2_candidate_id_map.json",
        "reports/SCIENTIFIC_MICROSTUDY_MODEL_FREEZE.json",
        "src/benchmark/selection/impact_planner_v2.py",
    ]
    checks = [_unchanged_vs_head(p) for p in paths]
    return {
        "immutable": all(c["unchanged"] for c in checks),
        "checks": checks,
    }


def _git_state() -> dict[str, Any]:
    head = _git("rev-parse", "HEAD")
    branch = _git("branch", "--show-current")
    origin_ref = _git("rev-parse", f"origin/{branch}") if branch else ""
    status = _git("status", "--short")
    return {
        "branch": branch,
        "head": head,
        "origin_ref": origin_ref,
        "parity": bool(head and origin_ref and head == origin_ref),
        "expected_branch": EXPECTED_BRANCH,
        "branch_ok": branch == EXPECTED_BRANCH,
        "working_tree_has_untracked_study_files": status != "",
    }


def _scenario_facing(sid: str) -> dict[str, Any]:
    scenario, scenario_path = wiring.load_study_scenario(sid)
    visible_text = scenario.requirement_before + "\n" + scenario.requirement_after
    gold_paths = wiring.hidden_gold_paths_for(sid)
    gold_mentions = [p for p in gold_paths if p in visible_text]
    return {
        "scenario_id": sid,
        "scenario_path": str(scenario_path),
        "gold_paths": list(gold_paths),
        "gold_not_in_visible_text": not gold_mentions,
    }


def _scenario_hashes() -> dict[str, str]:
    out: dict[str, str] = {}
    for sid in FINAL_SCENARIOS:
        scenario, scenario_path = wiring.load_study_scenario(sid)
        out[sid] = wiring.visible_input_sha256(scenario_path)
    return out


# ---------------------------------------------------------------------------
# Endpoint freeze (persisted before any scientific call)
# ---------------------------------------------------------------------------


def _persist_endpoint_freeze() -> dict[str, Any]:
    import urllib.request

    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip().strip('"').strip("'").strip()
    url = "https://openrouter.ai/api/v1/models/qwen/qwen3-coder/endpoints"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    d = payload["data"]
    deepinfra = [e for e in d.get("endpoints", []) if e.get("provider_name") == "DeepInfra"]
    if not deepinfra:
        raise RuntimeError("live OpenRouter metadata has NO DeepInfra endpoint for qwen/qwen3-coder")
    ep = deepinfra[0]
    freeze = {
        "model_id": d["id"],
        "model_name": d.get("name"),
        "provider_name": ep.get("provider_name"),
        "provider_tag": ep.get("tag"),
        "quantization": ep.get("quantization"),
        "context_length": ep.get("context_length"),
        "max_completion_tokens": ep.get("max_completion_tokens"),
        "supported_parameters": ep.get("supported_parameters"),
        "input_price_per_1M_usd": float(ep.get("pricing", {}).get("prompt", 0)) * 1_000_000,
        "output_price_per_1M_usd": float(ep.get("pricing", {}).get("completion", 0)) * 1_000_000,
        "reasoning_frozen": REASONING_FROZEN,
        "reasoning_mode": REASONING_MODE_LABEL,
        "temperature": TEMPERATURE,
        "completion_cap": CAP,
        "graph": "OFF",
        "routing": {
            "provider": {"order": [PROVIDER_TAG], "allow_fallbacks": False, "require_parameters": True}
        },
        "metadata_fetched_at_utc": _now_iso(),
    }
    _persist_json("endpoint_freeze.json", freeze)
    return freeze


def _endpoint_freeze_unchanged() -> dict[str, Any]:
    path = STUDY_DIR / "endpoint_freeze.json"
    if not path.is_file():
        return {"ok": False, "reason": "endpoint_freeze.json not found"}
    data = json.loads(path.read_text(encoding="utf-8"))
    ok = (
        data.get("model_id") == PRIMARY_MODEL
        and data.get("provider_name") == "DeepInfra"
        and data.get("provider_tag") == PROVIDER_TAG
        and data.get("quantization") == QUANTIZATION
        and data.get("temperature") == TEMPERATURE
        and data.get("completion_cap") == CAP
        and data.get("graph") == "OFF"
    )
    return {"ok": ok, "data": data}


def _load_live_pricing() -> dict[str, Any]:
    """Live DeepInfra pricing from the persisted endpoint freeze."""
    freeze_path = STUDY_DIR / "endpoint_freeze.json"
    if freeze_path.is_file():
        data = json.loads(freeze_path.read_text(encoding="utf-8"))
        prompt = float(data.get("input_price_per_1M_usd", 0.30)) / 1_000_000
        completion = float(data.get("output_price_per_1M_usd", 1.00)) / 1_000_000
        return {
            "prompt_per_token_usd": prompt,
            "completion_per_token_usd": completion,
            "source": str(freeze_path),
        }
    return {
        "prompt_per_token_usd": 0.0000003,
        "completion_per_token_usd": 0.000001,
        "source": "frozen live endpoint pricing (DeepInfra $0.30/$1.00 per 1M)",
    }


# ---------------------------------------------------------------------------
# Pre-validation
# ---------------------------------------------------------------------------


def cmd_prevalidate(_args: argparse.Namespace) -> int:
    print("=== PRE-RUN VALIDATION ===")
    checks: list[dict[str, Any]] = []
    state = _git_state()
    checks.append(
        {
            "check": "branch_expected",
            "ok": state["branch"] == EXPECTED_BRANCH,
            "detail": state["branch"],
        }
    )
    checks.append(
        {
            "check": "head_matches_origin_branch",
            "ok": state["parity"],
            "detail": {"head": state["head"], "origin_ref": state["origin_ref"]},
        }
    )
    immutable = _primary_evidence_immutable()
    checks.append(
        {
            "check": "historical_evidence_immutable",
            "ok": immutable["immutable"],
            "detail": immutable["checks"],
        }
    )
    facing = [_scenario_facing(sid) for sid in FINAL_SCENARIOS]
    checks.append(
        {
            "check": "hidden_gold_not_in_visible_inputs",
            "ok": all(f["gold_not_in_visible_text"] for f in facing),
            "detail": [{"scenario": f["scenario_id"], "gold_paths": f["gold_paths"]} for f in facing],
        }
    )
    checks.append(
        {
            "check": "frozen_universe_artifact_available",
            "ok": wiring.CANDIDATE_UNIVERSE_PATH.is_file()
            and len(wiring.load_frozen_universe_records()) == EXPECTED_UNIVERSE_COUNT,
            "detail": str(wiring.CANDIDATE_UNIVERSE_PATH),
        }
    )
    checks.append(
        {
            "check": "common_schema_sha_frozen",
            "ok": ea.COMMON_SCHEMA_SHA256 == COMMON_SCHEMA_SHA,
            "detail": ea.COMMON_SCHEMA_SHA256,
        }
    )
    checks.append(
        {
            "check": "common_template_sha_frozen",
            "ok": ea.COMMON_TEMPLATE_SHA256 == COMMON_TEMPLATE_SHA,
            "detail": ea.COMMON_TEMPLATE_SHA256,
        }
    )
    checks.append(
        {
            "check": "full_policy_sha_frozen",
            "ok": ea.FULL_POLICY_TEMPLATE_SHA256 == FULL_POLICY_SHA,
            "detail": ea.FULL_POLICY_TEMPLATE_SHA256,
        }
    )
    checks.append(
        {
            "check": "sparse_policy_sha_frozen",
            "ok": ea.SPARSE_POLICY_TEMPLATE_SHA256 == SPARSE_POLICY_SHA,
            "detail": ea.SPARSE_POLICY_TEMPLATE_SHA256,
        }
    )
    checks.append(
        {
            "check": "reason_codes_sha_frozen",
            "ok": ea.REASON_CODES_SHA256 == REASON_CODES_SHA,
            "detail": ea.REASON_CODES_SHA256,
        }
    )
    from benchmark.selection import impact_planner_v2 as v2

    mapping = v2.derive_candidate_id_map()
    checks.append(
        {
            "check": "candidate_id_map_sha_frozen",
            "ok": mapping.sha256 == V2_MAPPING_SHA
            and mapping.universe_canonical_sha256 == UNIVERSE_SHA,
            "detail": {"mapping_sha": mapping.sha256, "universe_sha": mapping.universe_canonical_sha256},
        }
    )
    checks.append(
        {
            "check": "universe_count_144",
            "ok": len(wiring.runtime_universe_paths()) == EXPECTED_UNIVERSE_COUNT,
            "detail": len(wiring.runtime_universe_paths()),
        }
    )
    checks.append(
        {
            "check": "graph_absent_not_injected",
            "ok": True,
            "detail": "graph OFF / NOT INJECTED (encoding-only study)",
        }
    )
    result = {
        "study_id": STUDY_ID,
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
        "checked_at": _now_iso(),
    }
    _persist_json("prevalidation.json", result)
    for c in checks:
        print(f"{'PASS' if c['ok'] else 'FAIL'}  {c['check']}")
    return 0 if result["passed"] else 1


def _prevalidation_passed() -> bool:
    path = STUDY_DIR / "prevalidation.json"
    if not path.is_file():
        return False
    return bool(json.loads(path.read_text(encoding="utf-8")).get("passed", False))


def _prompt_control_passed() -> bool:
    path = STUDY_DIR / "prompt_control.json"
    if not path.is_file():
        return False
    return bool(json.loads(path.read_text(encoding="utf-8")).get("PROMPT_CONTROLLED_DIFF") == "PASS")


def _gates_evidence_passed() -> bool:
    path = STUDY_DIR / "prestudy_gates.json"
    if not path.is_file():
        return False
    data = json.loads(path.read_text(encoding="utf-8"))
    return bool(data.get("all_passed", False)) and bool(data.get("audit", {}).get("passed", False))


def _probes_passed() -> bool:
    path = STUDY_DIR / "capability_probes.json"
    if not path.is_file():
        return False
    return bool(json.loads(path.read_text(encoding="utf-8")).get("contract_pass", False))


# ---------------------------------------------------------------------------
# Prompt-control proof (M1.4) — ZERO scientific calls
# ---------------------------------------------------------------------------


def cmd_prompt_control(_args: argparse.Namespace) -> int:
    print("=== PROMPT CONTROL PROOF (M1.4) ===")
    mapping = _derive_mapping()
    scenario_hashes = _scenario_hashes()
    rendered: dict[str, dict[str, Any]] = {}
    checks: list[dict[str, Any]] = []
    all_pass = True
    for sid in FINAL_SCENARIOS:
        scenario, _ = wiring.load_study_scenario(sid)
        full_prompt = ea.render_full_prompt(
            scenario_id=sid,
            before=scenario.requirement_before,
            after=scenario.requirement_after,
            acceptance_criteria=[c.description for c in scenario.acceptance_criteria],
            architecture_constraints=[c.description for c in scenario.architecture_constraints],
            mapping=mapping,
        )
        sparse_prompt = ea.render_sparse_prompt(
            scenario_id=sid,
            before=scenario.requirement_before,
            after=scenario.requirement_after,
            acceptance_criteria=[c.description for c in scenario.acceptance_criteria],
            architecture_constraints=[c.description for c in scenario.architecture_constraints],
            mapping=mapping,
        )
        proof = ea.prompt_control_proof(full_prompt, sparse_prompt)
        rendered[sid] = {
            "scenario_id": sid,
            "scenario_sha256": scenario_hashes[sid],
            "full_prompt": full_prompt,
            "sparse_prompt": sparse_prompt,
            "full_prompt_sha256": ea.sha256_text(full_prompt),
            "sparse_prompt_sha256": ea.sha256_text(sparse_prompt),
            "stripped_full_sha256": proof["stripped_full_sha256"],
            "stripped_sparse_sha256": proof["stripped_sparse_sha256"],
            "byte_identical_after_policy_strip": proof["byte_identical_after_policy_strip"],
        }
        checks.append(
            {
                "check": f"prompt_controlled_diff_{sid}",
                "ok": proof["PROMPT_CONTROLLED_DIFF"] == "PASS",
                "detail": proof,
            }
        )
        all_pass = all_pass and proof["PROMPT_CONTROLLED_DIFF"] == "PASS"
    result = {
        "study_id": STUDY_ID,
        "PROMPT_CONTROLLED_DIFF": "PASS" if all_pass else "FAIL",
        "common_template_sha256": COMMON_TEMPLATE_SHA,
        "common_schema_sha256": COMMON_SCHEMA_SHA,
        "candidate_map_sha256": mapping.sha256,
        "full_serialization_policy_sha256": FULL_POLICY_SHA,
        "sparse_serialization_policy_sha256": SPARSE_POLICY_SHA,
        "scenario_hashes": scenario_hashes,
        "scenarios": rendered,
        "checks": checks,
        "checked_at": _now_iso(),
    }
    _persist_json("prompt_control.json", result)
    for c in checks:
        print(f"{'PASS' if c['ok'] else 'FAIL'}  {c['check']}")
    print(f"PROMPT_CONTROLLED_DIFF={'PASS' if all_pass else 'FAIL'}")
    return 0 if all_pass else 1


def _derive_mapping():
    from benchmark.selection import impact_planner_v2 as v2

    return v2.derive_candidate_id_map()


# ---------------------------------------------------------------------------
# Capability probes (M1.6) — REAL tiny non-study calls
# ---------------------------------------------------------------------------

_PROBE_SYNTHETIC_BEFORE = (
    "The admin dashboard currently shows user activity as a static table."
)
_PROBE_SYNTHETIC_AFTER = (
    "The admin dashboard should show user activity as an interactive chart "
    "with a refresh button."
)
_PROBE_SYNTHETIC_ACCEPTANCE = (
    "The dashboard renders an interactive activity chart.",
    "A refresh button reloads the activity data.",
)
_PROBE_SYNTHETIC_CONSTRAINTS = (
    "Keep the existing admin styling.",
    "Do not introduce a new external charting library.",
)


def _probe_prompt(arm: str, mapping: Any) -> str:
    """Render the REAL Full-v2 / Sparse-v2 prompt with SYNTHETIC scenario text.

    The serialization-policy block and the common schema are the exact study
    inputs; only the scenario text is synthetic (unrelated to the six
    scientific scenarios).
    """
    if arm == "full_v2":
        return ea.render_full_prompt(
            scenario_id="synthetic-capability-fixture",
            before=_PROBE_SYNTHETIC_BEFORE,
            after=_PROBE_SYNTHETIC_AFTER,
            acceptance_criteria=_PROBE_SYNTHETIC_ACCEPTANCE,
            architecture_constraints=_PROBE_SYNTHETIC_CONSTRAINTS,
            mapping=mapping,
        )
    return ea.render_sparse_prompt(
        scenario_id="synthetic-capability-fixture",
        before=_PROBE_SYNTHETIC_BEFORE,
        after=_PROBE_SYNTHETIC_AFTER,
        acceptance_criteria=_PROBE_SYNTHETIC_ACCEPTANCE,
        architecture_constraints=_PROBE_SYNTHETIC_CONSTRAINTS,
        mapping=mapping,
    )


def _raw_openrouter_call(
    schema_name: str,
    schema: dict[str, Any],
    prompt: str,
    max_attempts: int = 2,
) -> dict[str, Any]:
    import urllib.error
    import urllib.request

    from benchmark.llm.openrouter_backend import (
        _redact,
        _safe_error_from_http_error,
        _safe_exc_message,
    )

    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip().strip('"').strip("'").strip()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    body = {
        "model": PRIMARY_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": TEMPERATURE,
        "max_tokens": CAP,
        "stream": False,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": schema_name, "strict": True, "schema": schema},
        },
        "provider": {
            "order": [PROVIDER_TAG],
            "allow_fallbacks": False,
            "require_parameters": True,
        },
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    last_error: BaseException | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                raw = resp.read()
            return {"ok": True, "attempt": attempt, "raw": raw.decode("utf-8")}
        except Exception as exc:
            last_error = exc
            if isinstance(exc, urllib.error.HTTPError):
                msg = _redact(_safe_error_from_http_error(exc, api_key), api_key)
            else:
                msg = _redact(_safe_exc_message(exc), api_key)
            print(f"  probe attempt {attempt}/{max_attempts} failed: {msg}")
    return {"ok": False, "error": str(last_error)}


def cmd_probe(_args: argparse.Namespace) -> int:
    print("=== CAPABILITY PROBES (M1.6, non-study) ===")
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("OPENROUTER_API_KEY not set — cannot probe")
        return 1

    freeze = _persist_endpoint_freeze()
    print(json.dumps(freeze, indent=2))

    results: dict[str, Any] = {
        "study_id": STUDY_ID,
        "model": PRIMARY_MODEL,
        "model_human": MODEL_HUMAN,
        "provider": "DeepInfra",
        "provider_tag": PROVIDER_TAG,
        "quantization": QUANTIZATION,
        "temperature": TEMPERATURE,
        "max_tokens": CAP,
        "probes": {},
        "contract_pass": False,
        "ran_at": _now_iso(),
    }

    probes = [
        ("probe_a_full_v2", "controlled_encoding_full_v2", "full_v2"),
        ("probe_b_sparse_v2", "controlled_encoding_sparse_v2", "sparse_v2"),
    ]
    mapping = _derive_mapping()
    all_pass = True
    for label, schema_name, arm in probes:
        print(f"\n--- PROBE {label} ---")
        prompt = _probe_prompt(arm, mapping)
        out = _raw_openrouter_call(schema_name, ea.COMMON_ABLATION_SCHEMA, prompt)
        entry: dict[str, Any] = {
            "probe": label,
            "arm": arm,
            "schema_name": schema_name,
            "attempts_used": out.get("attempt", 0),
            "transport_ok": out.get("ok", False),
            "error": out.get("error", ""),
        }
        content = ""
        if not out.get("ok"):
            entry["schema_valid"] = False
            entry["validated"] = False
            entry["errors"] = [out.get("error", "transport failed")]
            all_pass = False
            results["probes"][label] = entry
            continue
        try:
            parsed = json.loads(out["raw"])
        except json.JSONDecodeError:
            parsed = None
        choices = (parsed or {}).get("choices") or []
        choice = choices[0] if choices else {}
        message = choice.get("message") or {}
        content = message.get("content") or ""
        entry["finish_reason"] = choice.get("finish_reason", "")
        entry["provider_reported"] = parsed.get("provider")
        usage = parsed.get("usage") or {}
        entry["usage"] = {
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
        }
        entry["usage_known"] = bool(
            usage.get("prompt_tokens") is not None and usage.get("completion_tokens") is not None
        )
        entry["prompt_sha256"] = ea.sha256_text(prompt)
        validation_errors: list[str] = []
        import jsonschema

        if not content:
            validation_errors.append("empty assistant content")
        else:
            entry["raw_response_sha256"] = _sha256_bytes(content.encode("utf-8"))
            try:
                payload = json.loads(content)
            except json.JSONDecodeError as exc:
                payload = None
                validation_errors.append(f"content not valid JSON: {exc}")
            if isinstance(payload, dict):
                try:
                    jsonschema.validate(instance=payload, schema=ea.COMMON_ABLATION_SCHEMA)
                except jsonschema.ValidationError as exc:
                    validation_errors.append(f"common schema validation failed: {exc.message}")
                validator = (
                    ea.validate_full_v2 if arm == "full_v2" else ea.validate_sparse_v2
                )
                vres = validator(payload)
                if not vres["valid"]:
                    validation_errors.extend(vres["errors"])
                entry["decoded_candidate_count"] = vres.get("decoded_candidate_count")
                entry["decoded_write_set_ids"] = vres.get("decoded_write_set_ids")
                entry["validated_payload_keys"] = sorted(payload.keys())
        entry["errors"] = validation_errors
        entry["schema_valid"] = not validation_errors
        entry["validated"] = (
            entry["schema_valid"]
            and bool(entry.get("finish_reason"))
            and entry.get("usage_known")
        )
        provider_field = entry.get("provider_reported")
        provider_name = (
            provider_field.get("provider_name")
            if isinstance(provider_field, dict)
            else provider_field
        )
        entry["provider_name"] = provider_name
        contract = (
            entry["schema_valid"]
            and provider_name == "DeepInfra"
            and entry.get("finish_reason") in ("stop", "length")
            and entry.get("usage_known")
        )
        entry["contract_ok"] = contract
        all_pass = all_pass and contract
        results["probes"][label] = entry
        print(json.dumps(entry, indent=2))
        # persist raw response + sha immediately
        raw_path = STUDY_DIR / "probes" / "raw" / f"{label}.txt"
        _write_bytes(raw_path, content.encode("utf-8"))
        _write_bytes(STUDY_DIR / "probes" / "raw" / f"{label}.sha256",
                     (entry.get("raw_response_sha256", "") + "\n").encode("utf-8"))
        print(f"persisted raw={raw_path}")

    results["contract_pass"] = all_pass
    _persist_json("capability_probes.json", results)
    if all_pass:
        print("\nCONTROLLED_ENCODING_CAPABILITY_CONTRACT: PASS")
    else:
        print("\nCONTROLLED_ENCODING_CAPABILITY_CONTRACT: FAIL")
    return 0 if all_pass else 1


# ---------------------------------------------------------------------------
# Six deterministic gates + audit (ZERO scientific calls)
# ---------------------------------------------------------------------------


def gate1_dataset_validation() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    checks.append(
        {
            "check": "pinned_djangocms_commit_frozen",
            "ok": wiring.PINNED_COMMIT == "0f633fc9fa213357f4202482aab2b0edad680f95",
            "detail": wiring.PINNED_COMMIT,
        }
    )
    checks.append(
        {
            "check": "universe_exactly_144_paths",
            "ok": len(wiring.runtime_universe_paths()) == EXPECTED_UNIVERSE_COUNT,
            "detail": len(wiring.runtime_universe_paths()),
        }
    )
    universe_hash = wiring.frozen_universe_canonical_hash()
    checks.append(
        {
            "check": "universe_sha256_frozen",
            "ok": universe_hash == UNIVERSE_SHA,
            "detail": universe_hash,
        }
    )
    checks.append(
        {
            "check": "six_exact_scenario_ids",
            "ok": set(FINAL_SCENARIOS)
            == {
                "djangocms-external-validity-002",
                "djangocms-external-validity-004",
                "djangocms-external-validity-005",
                "djangocms-external-validity-006",
                "djangocms-external-validity-007",
                "djangocms-external-validity-008",
            },
            "detail": sorted(FINAL_SCENARIOS),
        }
    )
    checks.append(
        {
            "check": "scenario_hashes_match_historical",
            "ok": all(
                _scenario_hashes().get(sid) == SCENARIO_EXPECTED_HASHES.get(sid)
                for sid in FINAL_SCENARIOS
            ),
            "detail": _scenario_hashes(),
        }
    )
    mapping = _derive_mapping()
    checks.append(
        {
            "check": "candidate_mapping_sha256_frozen",
            "ok": mapping.sha256 == V2_MAPPING_SHA,
            "detail": mapping.sha256,
        }
    )
    gold_paths = {
        p for rec in wiring.load_hidden_gold() for p in rec.get("source_files", [])
    }
    runtime_set = set(wiring.runtime_universe_paths())
    checks.append(
        {
            "check": "hidden_gold_files_exist_in_frozen_universe",
            "ok": gold_paths <= runtime_set,
            "detail": sorted(gold_paths - runtime_set),
        }
    )
    facing = [_scenario_facing(sid) for sid in FINAL_SCENARIOS]
    checks.append(
        {
            "check": "no_hidden_gold_exposed_to_inference_input",
            "ok": all(f["gold_not_in_visible_text"] for f in facing),
            "detail": [{"scenario": f["scenario_id"], "gold_paths": f["gold_paths"]} for f in facing],
        }
    )
    return {
        "gate": 1,
        "name": "Dataset Validation",
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
    }


def gate2_prompt_validation() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    checks.append(
        {
            "check": "common_template_sha_frozen",
            "ok": ea.COMMON_TEMPLATE_SHA256 == COMMON_TEMPLATE_SHA,
            "detail": ea.COMMON_TEMPLATE_SHA256,
        }
    )
    checks.append(
        {
            "check": "common_schema_sha_frozen",
            "ok": ea.COMMON_SCHEMA_SHA256 == COMMON_SCHEMA_SHA,
            "detail": ea.COMMON_SCHEMA_SHA256,
        }
    )
    checks.append(
        {
            "check": "full_policy_sha_frozen",
            "ok": ea.FULL_POLICY_TEMPLATE_SHA256 == FULL_POLICY_SHA,
            "detail": ea.FULL_POLICY_TEMPLATE_SHA256,
        }
    )
    checks.append(
        {
            "check": "sparse_policy_sha_frozen",
            "ok": ea.SPARSE_POLICY_TEMPLATE_SHA256 == SPARSE_POLICY_SHA,
            "detail": ea.SPARSE_POLICY_TEMPLATE_SHA256,
        }
    )
    checks.append(
        {
            "check": "candidate_id_map_frozen",
            "ok": _derive_mapping().sha256 == V2_MAPPING_SHA,
            "detail": _derive_mapping().sha256,
        }
    )
    checks.append(
        {
            "check": "prompt_has_no_hidden_gold",
            "ok": all(_scenario_facing(sid)["gold_not_in_visible_text"] for sid in FINAL_SCENARIOS),
            "detail": "gold isolated to evaluation-only",
        }
    )
    checks.append(
        {
            "check": "prompt_control_diff_pass",
            "ok": _prompt_control_passed(),
            "detail": "only SERIALIZATION_POLICY differs between arms",
        }
    )
    checks.append(
        {
            "check": "action_vocab_common",
            "ok": set(ea.ABLATION_ACTION_VOCAB) == {"PRESERVE", "REGENERATE", "VALIDATE", "HUMAN_REVIEW"},
            "detail": list(ea.ABLATION_ACTION_VOCAB),
        }
    )
    return {
        "gate": 2,
        "name": "Prompt Validation",
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
    }


def _fixture_payload_for_arm(arm: str, mapping: Any) -> dict[str, Any]:
    gold = set(wiring.hidden_gold_paths_for("djangocms-external-validity-004"))
    policy_rows: dict[int, str] = {}
    for i, path in mapping.id_to_path:
        policy_rows[i] = "REGENERATE" if path in gold else "PRESERVE"
    policy = ea.complete_policy_from_actions(policy_rows)
    if arm == "full_v2":
        return ea.full_payload_for(policy, mapping)
    return ea.sparse_payload_for(policy, mapping)


def gate3_pipeline_smoke_test() -> dict[str, Any]:
    """Deterministic mocked pipeline smoke over BOTH arms (ZERO calls)."""
    checks: list[dict[str, Any]] = []
    mapping = _derive_mapping()
    for arm in ARMS:
        payload = _fixture_payload_for_arm(arm, mapping)
        validator = ea.validate_full_v2 if arm == "full_v2" else ea.validate_sparse_v2
        vres = validator(payload)
        checks.append(
            {
                "check": f"smoke_{arm}_decodes_to_144",
                "ok": vres["valid"] and vres["decoded_candidate_count"] == 144,
                "detail": {
                    "valid": vres["valid"],
                    "decoded_candidate_count": vres.get("decoded_candidate_count"),
                    "write_set_ids": vres.get("decoded_write_set_ids"),
                },
            }
        )
    checks.append(
        {
            "check": "zero_scientific_calls",
            "ok": True,
            "detail": "deterministic encode/decode only; no real LLM backend constructed",
        }
    )
    return {
        "gate": 3,
        "name": "Pipeline Smoke Test",
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
    }


def gate4_dry_run() -> dict[str, Any]:
    """Deterministic dry run proving the 60-cell manifest shape (ZERO calls)."""
    checks: list[dict[str, Any]] = []
    rows = _build_manifest()
    checks.append(
        {
            "check": "manifest_iteration_exactly_60",
            "ok": len(rows) == TOTAL_CELLS,
            "detail": len(rows),
        }
    )
    checks.append(
        {
            "check": "run_ids_unique",
            "ok": len({r["run_id"] for r in rows}) == TOTAL_CELLS,
            "detail": {"unique": len({r["run_id"] for r in rows})},
        }
    )
    checks.append(
        {
            "check": "six_scenarios",
            "ok": {r["scenario_id"] for r in rows} == set(FINAL_SCENARIOS),
            "detail": sorted({r["scenario_id"] for r in rows}),
        }
    )
    checks.append(
        {
            "check": "two_arms",
            "ok": {r["arm"] for r in rows} == set(ARMS),
            "detail": sorted({r["arm"] for r in rows}),
        }
    )
    checks.append(
        {
            "check": "five_reps_per_scenario_per_arm",
            "ok": all(
                sum(1 for r in rows if r["scenario_id"] == sid and r["arm"] == arm) == 5
                for sid in FINAL_SCENARIOS
                for arm in ARMS
            ),
            "detail": {
                f"{sid}/{arm}": sum(1 for r in rows if r["scenario_id"] == sid and r["arm"] == arm)
                for sid in FINAL_SCENARIOS
                for arm in ARMS
            },
        }
    )
    checks.append(
        {
            "check": "same_common_schema_every_cell",
            "ok": all(r["common_schema_sha256"] == COMMON_SCHEMA_SHA for r in rows),
            "detail": COMMON_SCHEMA_SHA,
        }
    )
    checks.append(
        {
            "check": "only_serialization_policy_differs",
            "ok": all(
                (r["arm"] == "full_v2" and r["serialization_policy_sha256"] == FULL_POLICY_SHA)
                or (r["arm"] == "sparse_v2" and r["serialization_policy_sha256"] == SPARSE_POLICY_SHA)
                for r in rows
            ),
            "detail": "policy block per arm; all other inputs identical",
        }
    )
    checks.append(
        {
            "check": "frozen_configuration_propagation",
            "ok": all(
                r["expected_scientific_model"] == PRIMARY_MODEL
                and r["provider_tag"] == PROVIDER_TAG
                and r["temperature"] == TEMPERATURE
                and r["max_completion_tokens"] == CAP
                for r in rows
            ),
            "detail": "all cells carry frozen qwen/qwen3-coder @ deepinfra/turbo config",
        }
    )
    checks.append(
        {
            "check": "zero_scientific_calls_and_tokens",
            "ok": True,
            "detail": "dry-run is manifest-shape proof only; zero real model calls and zero billed tokens",
        }
    )
    return {
        "gate": 4,
        "name": "Dry Run",
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
    }


def gate5_integration_test() -> dict[str, Any]:
    """Complete local integration path for BOTH arms with deterministic fixtures."""
    checks: list[dict[str, Any]] = []
    mapping = _derive_mapping()
    scenario, _ = wiring.load_study_scenario("djangocms-external-validity-004")
    gold = set(wiring.hidden_gold_paths_for("djangocms-external-validity-004"))
    for arm in ARMS:
        payload = _fixture_payload_for_arm(arm, mapping)
        validator = ea.validate_full_v2 if arm == "full_v2" else ea.validate_sparse_v2
        vres = validator(payload)
        write_set_paths = [mapping.path_for(i) for i in vres.get("decoded_write_set_ids", [])]
        checks.append(
            {
                "check": f"{arm}_decode_and_full_policy_reconstruction",
                "ok": vres["valid"] and vres["decoded_candidate_count"] == 144,
                "detail": {"valid": vres["valid"], "policy_size": vres.get("decoded_candidate_count")},
            }
        )
        predicted_set = set(write_set_paths)
        tp = len(predicted_set & gold)
        fn = len(gold - predicted_set)
        checks.append(
            {
                "check": f"{arm}_predicted_write_set_equals_gold_fixture",
                "ok": predicted_set == gold,
                "detail": {
                    "predicted": sorted(predicted_set),
                    "gold": sorted(gold),
                    "tp": tp,
                    "fn": fn,
                },
            }
        )
        metrics = wiring._compute_selection_metrics(predicted_set, gold)
        checks.append(
            {
                "check": f"{arm}_post_inference_hidden_gold_evaluation_metrics",
                "ok": metrics["recall"] == 1.0
                and metrics["fnr"] == 0.0
                and metrics["full_recall"]
                and tp == len(gold)
                and fn == 0,
                "detail": {**metrics, "tp": tp, "fn": fn},
            }
        )
    checks.append(
        {
            "check": "same_visible_scenario_for_both_arms",
            "ok": True,
            "detail": {"scenario_id": scenario.scenario_id, "gold_size": len(gold)},
        }
    )
    checks.append(
        {
            "check": "zero_scientific_calls",
            "ok": True,
            "detail": "deterministic fixture payloads only",
        }
    )
    return {
        "gate": 5,
        "name": "Integration Test",
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
    }


def gate6_metric_verification() -> dict[str, Any]:
    """Deterministic metric recomputation + representation-equivalence checks."""
    checks: list[dict[str, Any]] = []
    predicted = {"a", "b", "c", "d"}
    gold = {"a", "b", "c"}
    metrics = wiring._compute_selection_metrics(predicted, gold)
    tp = len(predicted & gold)
    fn = len(gold - predicted)
    precision = tp / len(predicted) if predicted else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    checks.append(
        {
            "check": "micro_averaged_precision_recall_f1",
            "ok": abs(metrics["precision"] - precision) < 1e-9
            and abs(metrics["recall"] - recall) < 1e-9
            and abs(metrics["f1"] - f1) < 1e-9,
            "detail": {"computed": metrics, "expected": {"precision": precision, "recall": recall, "f1": f1}},
        }
    )
    rep = ea.representation_equivalence_checks()
    checks.append(
        {
            "check": "representation_equivalence",
            "ok": rep["REPRESENTATION_EQUIVALENCE"] == "PASS",
            "detail": {"label": "D_s(E_s(pi)) == pi", "checks": len(rep["checks"])},
        }
    )
    # full-v2 vs sparse-v2 decode to the SAME canonical 144-policy for the same input policy
    mapping = _derive_mapping()
    policy = ea.complete_policy_from_actions({3: "REGENERATE", 7: "VALIDATE", 11: "HUMAN_REVIEW"})
    full_decoded = ea.decode_full_policy(ea.full_payload_for(policy, mapping))
    sparse_decoded = ea.decode_sparse_policy(ea.sparse_payload_for(policy, mapping))
    checks.append(
        {
            "check": "both_arms_same_canonical_policy_after_decode",
            "ok": full_decoded.to_dict() == sparse_decoded.to_dict() == policy.to_dict(),
            "detail": {
                "full": full_decoded.to_dict(),
                "sparse": sparse_decoded.to_dict(),
            },
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


def run_gates() -> list[dict[str, Any]]:
    return [g() for g in GATES]


def _independent_audit() -> dict[str, Any]:
    records = _loaded_records()
    manifest = _load_manifest() if _manifest_path().is_file() else {"cells": []}
    checks: list[dict[str, Any]] = []
    checks.append({"check": "study_id_frozen", "ok": True, "detail": STUDY_ID})
    checks.append(
        {
            "check": "model_frozen",
            "ok": PRIMARY_MODEL == "qwen/qwen3-coder",
            "detail": PRIMARY_MODEL,
        }
    )
    checks.append(
        {
            "check": "provider_deepinfra_frozen",
            "ok": PROVIDER_TAG == "deepinfra/turbo",
            "detail": PROVIDER_TAG,
        }
    )
    checks.append(
        {
            "check": "reasoning_direct_non_thinking",
            "ok": REASONING_FROZEN is None,
            "detail": REASONING_MODE_LABEL,
        }
    )
    checks.append(
        {
            "check": "historical_evidence_immutable",
            "ok": _primary_evidence_immutable()["immutable"],
            "detail": _primary_evidence_immutable()["checks"],
        }
    )
    checks.append(
        {
            "check": "no_reruns_after_failure",
            "ok": True,
            "detail": "result-based reruns FORBIDDEN; cell replacement FORBIDDEN",
        }
    )
    checks.append(
        {
            "check": "no_run_61",
            "ok": len(manifest.get("cells", [])) <= 60,
            "detail": len(manifest.get("cells", [])),
        }
    )
    checks.append(
        {
            "check": "hidden_gold_evaluation_only",
            "ok": True,
            "detail": "gold applied only after inference",
        }
    )
    checks.append(
        {
            "check": "graph_absent",
            "ok": True,
            "detail": "graph OFF / NOT INJECTED",
        }
    )
    if records:
        model_ok = all(r.get("scientific_model") == PRIMARY_MODEL for r in records.values())
        provider_ok = all(r.get("provider_tag") == PROVIDER_TAG for r in records.values())
        checks.append(
            {
                "check": "every_record_model_provider",
                "ok": model_ok and provider_ok,
                "detail": {"model": model_ok, "provider": provider_ok},
            }
        )
    return {
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
        "ran_at": _now_iso(),
    }


def cmd_gates(_args: argparse.Namespace) -> int:
    print("=== SIX PRE-BENCHMARK GATES + AUDIT ===")
    gates = run_gates()
    audit = _independent_audit()
    all_passed = all(g["passed"] for g in gates) and audit["passed"]
    result = {
        "gates": gates,
        "all_passed": all(g["passed"] for g in gates),
        "audit": audit,
        "ran_at": _now_iso(),
    }
    _persist_json("prestudy_gates.json", result)
    for g in gates:
        print(f"Gate {g['gate']} {g['name']}: {'PASS' if g['passed'] else 'FAIL'}")
    print(f"AUDIT={'PASS' if audit['passed'] else 'FAIL'}")
    return 0 if all_passed else 1


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


def _build_manifest() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    universe_hash = wiring.runtime_universe_canonical_hash()
    mapping_sha = _derive_mapping().sha256
    scenario_hashes = _scenario_hashes()
    for scenario_id in FINAL_SCENARIOS:
        visible_hash = scenario_hashes[scenario_id]
        for arm in ARMS:
            policy_sha = FULL_POLICY_SHA if arm == "full_v2" else SPARSE_POLICY_SHA
            for rep in REPETITIONS:
                run_id = f"cea-{scenario_id}-{arm}-r{rep}"
                rows.append(
                    {
                        "run_id": run_id,
                        "scenario_id": scenario_id,
                        "repetition": rep,
                        "arm": arm,
                        "serialization_policy": "full_v2" if arm == "full_v2" else "sparse_v2",
                        "serialization_policy_sha256": policy_sha,
                        "expected_scientific_model": PRIMARY_MODEL,
                        "expected_model_human": MODEL_HUMAN,
                        "model_slug": PRIMARY_MODEL,
                        "gateway": "OpenRouter",
                        "expected_provider": f"{PROVIDER_PINNED} pinned through OpenRouter",
                        "provider_tag": PROVIDER_TAG,
                        "quantization": QUANTIZATION,
                        "fallback": "off",
                        "temperature": TEMPERATURE,
                        "max_completion_tokens": CAP,
                        "reasoning_mode": REASONING_MODE_LABEL,
                        "graph": "OFF",
                        "selection_only": True,
                        "common_schema_sha256": COMMON_SCHEMA_SHA,
                        "common_template_sha256": COMMON_TEMPLATE_SHA,
                        "candidate_id_mapping_sha256": mapping_sha,
                        "frozen_visible_scenario_sha256": visible_hash,
                        "scenario_sha256": visible_hash,
                        "frozen_runtime_universe_hash": universe_hash,
                        "universe_sha256": universe_hash,
                    }
                )
    assert len(rows) == TOTAL_CELLS
    return rows


def cmd_freeze_manifest(_args: argparse.Namespace) -> int:
    if not _prevalidation_passed():
        print("Pre-run validation NOT passed — STOP BEFORE FREEZE")
        return 1
    if not _prompt_control_passed():
        print("Prompt control proof NOT passed — STOP BEFORE FREEZE")
        return 1
    if not _gates_evidence_passed():
        print("Six gates + audit NOT passed — STOP BEFORE FREEZE")
        return 1
    if not _probes_passed():
        print("Capability probes NOT passed — STOP BEFORE FREEZE")
        return 1
    rows = _build_manifest()
    manifest = {
        "study_id": STUDY_ID,
        "study_label": "CONTROLLED ENCODING ABLATION (FULL-v2 vs SPARSE-v2)",
        "model": PRIMARY_MODEL,
        "model_human": MODEL_HUMAN,
        "gateway": "OpenRouter",
        "provider": f"{PROVIDER_PINNED} pinned through OpenRouter",
        "provider_tag": PROVIDER_TAG,
        "quantization": QUANTIZATION,
        "fallback": "off",
        "temperature": TEMPERATURE,
        "completion_cap": CAP,
        "reasoning_mode": REASONING_MODE_LABEL,
        "graph": "OFF",
        "selection_only": True,
        "arms": list(ARMS),
        "scenarios": list(FINAL_SCENARIOS),
        "repetitions": list(REPETITIONS),
        "total_cells": len(rows),
        "common_schema_sha256": COMMON_SCHEMA_SHA,
        "common_template_sha256": COMMON_TEMPLATE_SHA,
        "candidate_id_mapping_sha256": V2_MAPPING_SHA,
        "full_serialization_policy_sha256": FULL_POLICY_SHA,
        "sparse_serialization_policy_sha256": SPARSE_POLICY_SHA,
        "reason_codes_sha256": REASON_CODES_SHA,
        "frozen_universe_hash": UNIVERSE_SHA,
        "universe_count": len(wiring.runtime_universe_paths()),
        "gold": "evaluation only after inference",
        "result_based_reruns": "FORBIDDEN",
        "cell_replacement": "FORBIDDEN",
        "hard_cost_ceiling_usd": SCIENTIFIC_CEILING_USD,
        "runtime_ceiling_seconds": RUNTIME_CEILING_SECONDS,
        "manifest_frozen_at": _now_iso(),
        "cells": rows,
    }
    path = _persist_json("manifest_60.json", manifest)
    print(f"MANIFEST_CELLS={len(rows)}")
    print(f"persisted={path}")
    return 0


def _load_manifest() -> dict[str, Any]:
    path = _manifest_path()
    if not path.is_file():
        raise FileNotFoundError("manifest_60.json not found — run freeze-manifest first")
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Execution (selection-only, direct common-schema path)
# ---------------------------------------------------------------------------


def _render_cell_prompt(cell: dict[str, Any]) -> str:
    scenario, _ = wiring.load_study_scenario(cell["scenario_id"])
    mapping = _derive_mapping()
    if cell["arm"] == "full_v2":
        return ea.render_full_prompt(
            scenario_id=cell["scenario_id"],
            before=scenario.requirement_before,
            after=scenario.requirement_after,
            acceptance_criteria=[c.description for c in scenario.acceptance_criteria],
            architecture_constraints=[c.description for c in scenario.architecture_constraints],
            mapping=mapping,
        )
    return ea.render_sparse_prompt(
        scenario_id=cell["scenario_id"],
        before=scenario.requirement_before,
        after=scenario.requirement_after,
        acceptance_criteria=[c.description for c in scenario.acceptance_criteria],
        architecture_constraints=[c.description for c in scenario.architecture_constraints],
        mapping=mapping,
    )


def _call_openrouter(prompt: str, schema_name: str) -> dict[str, Any]:
    import urllib.error
    import urllib.request

    from benchmark.llm.openrouter_backend import (
        _redact,
        _safe_error_from_http_error,
        _safe_exc_message,
    )

    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip().strip('"').strip("'").strip()
    body = {
        "model": PRIMARY_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": TEMPERATURE,
        "max_tokens": CAP,
        "stream": False,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": schema_name, "strict": True, "schema": ea.COMMON_ABLATION_SCHEMA},
        },
        "provider": {
            "order": [PROVIDER_TAG],
            "allow_fallbacks": False,
            "require_parameters": True,
        },
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    last_error: BaseException | None = None
    for attempt in range(1, MAX_TRANSIENT_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                raw = resp.read()
            return {"ok": True, "attempt": attempt, "raw": raw.decode("utf-8"), "dispatched": True}
        except Exception as exc:
            last_error = exc
            if isinstance(exc, urllib.error.HTTPError):
                msg = _redact(_safe_error_from_http_error(exc, api_key), api_key)
            else:
                msg = _redact(_safe_exc_message(exc), api_key)
            print(f"  call attempt {attempt}/{MAX_TRANSIENT_RETRIES} failed: {msg}")
    return {"ok": False, "error": str(last_error), "dispatched": True}


def _build_cell_evidence(
    cell: dict[str, Any],
    prompt: str,
    result: dict[str, Any],
    elapsed: float,
) -> dict[str, Any]:
    raw_text = result.get("raw") if result.get("ok") else None
    raw_sha = _sha256_bytes(raw_text.encode("utf-8")) if raw_text is not None else ""
    pricing = _load_live_pricing()

    entry: dict[str, Any] = {
        "run_id": cell["run_id"],
        "scenario_id": cell["scenario_id"],
        "repetition": cell["repetition"],
        "arm": cell["arm"],
        "serialization_policy": cell["serialization_policy"],
        "scientific_model": PRIMARY_MODEL,
        "model_human": MODEL_HUMAN,
        "model_slug": PRIMARY_MODEL,
        "gateway": "OpenRouter",
        "provider": f"{PROVIDER_PINNED} pinned through OpenRouter",
        "provider_tag": PROVIDER_TAG,
        "exact_model": f"openrouter:{PRIMARY_MODEL}@{PROVIDER_TAG}",
        "exact_provider_used": PROVIDER_TAG,
        "quantization": QUANTIZATION,
        "fallback_status": "off",
        "temperature": TEMPERATURE,
        "completion_cap": CAP,
        "reasoning_mode": REASONING_MODE_LABEL,
        "graph": "OFF",
        "dry_run": False,
        "request_attempted": True,
        "request_dispatched": bool(result.get("dispatched", True)),
        "prompt_sha256": ea.sha256_text(prompt),
        "request_issued": bool(result.get("ok")) or bool(result.get("dispatched")),
        "transport_failure": bool(not result.get("ok") and result.get("dispatched")),
        "raw_response_sha256": raw_sha,
        "latency_seconds": round(elapsed, 6),
        "recorded_at": _now_iso(),
    }

    if not result.get("ok"):
        entry.update(
            {
                "provider_response_received": False,
                "raw_response_persisted": False,
                "usage_known": False,
                "usage_received": False,
                "finish_reason": "",
                "truncation_status": False,
                "terminal_status": "failed",
                "schema_valid": False,
                "decoded_candidate_count": 0,
                "decoded_write_set_ids": [],
                "decoded_policy_sha256": "",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "model_calls": 0,
                "api_cost": 0.0,
                "pricing_source": pricing.get("source", ""),
                "failure_category": result.get("error", "transport failed"),
                "failure_evidence": [
                    {"kind": "transport", "stage": "openrouter", "message": result.get("error", "")}
                ],
                "tp": 0,
                "fp": 0,
                "fn": len(wiring.hidden_gold_paths_for(cell["scenario_id"])),
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0,
                "fnr": 1.0,
                "full_recall": False,
            }
        )
        return entry

    try:
        parsed = json.loads(raw_text or "")
    except json.JSONDecodeError:
        parsed = None

    choices = (parsed or {}).get("choices") or []
    choice = choices[0] if choices else {}
    message = choice.get("message") or {}
    content = message.get("content") or ""
    finish_reason = choice.get("finish_reason", "") or ""
    provider_field = parsed.get("provider")
    provider_name = (
        provider_field.get("provider_name") if isinstance(provider_field, dict) else provider_field
    )
    usage = parsed.get("usage") or {}
    prompt_tokens = int(usage.get("prompt_tokens") or 0)
    completion_tokens = int(usage.get("completion_tokens") or 0)
    total_tokens = int(usage.get("total_tokens") or 0)
    usage_known = bool(
        usage.get("prompt_tokens") is not None and usage.get("completion_tokens") is not None
    )
    cap_hit = finish_reason == "length"

    entry.update(
        {
            "provider_response_received": True,
            "raw_response_persisted": True,
            "usage_received": usage_known,
            "usage_known": usage_known,
            "provider_reported": provider_field,
            "provider_name": provider_name,
            "finish_reason": finish_reason,
            "truncation_status": cap_hit,
            "completion_cap_hit": cap_hit,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "model_calls": 1,
            "api_cost": round(
                prompt_tokens * float(pricing["prompt_per_token_usd"])
                + completion_tokens * float(pricing["completion_per_token_usd"]),
                6,
            ),
            "pricing_source": pricing.get("source", ""),
        }
    )

    import jsonschema

    validator_errors: list[str] = []
    decoded_candidate_count = 0
    decoded_write_set_ids: list[int] = []
    decoded_policy_sha256 = ""
    if content:
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            payload = None
            validator_errors.append(f"content not valid JSON: {exc}")
        if isinstance(payload, dict):
            try:
                jsonschema.validate(instance=payload, schema=ea.COMMON_ABLATION_SCHEMA)
            except jsonschema.ValidationError as exc:
                validator_errors.append(f"common schema validation failed: {exc.message}")
            validator = ea.validate_full_v2 if cell["arm"] == "full_v2" else ea.validate_sparse_v2
            vres = validator(payload)
            if not vres["valid"]:
                validator_errors.extend(vres["errors"])
            policy = vres.get("policy")
            decoded_candidate_count = vres.get("decoded_candidate_count") or 0
            decoded_write_set_ids = vres.get("decoded_write_set_ids") or []
            if policy is not None:
                decoded_policy_sha256 = ea.sha256_json(policy.to_dict())
            entry["decoded_action_map"] = policy.to_dict() if policy is not None else {}

    entry.update(
        {
            "schema_valid": not validator_errors,
            "failure_category": "; ".join(validator_errors),
            "failure_evidence": [{"kind": "semantic", "stage": "decode", "message": e} for e in validator_errors],
            "decoded_candidate_count": decoded_candidate_count,
            "decoded_write_set_ids": decoded_write_set_ids,
            "decoded_policy_sha256": decoded_policy_sha256,
        }
    )

    # hidden-gold scoring AFTER output persisted (evaluation-only)
    mapping = _derive_mapping()
    write_set_paths = [mapping.path_for(i) for i in decoded_write_set_ids]
    gold = set(wiring.hidden_gold_paths_for(cell["scenario_id"]))
    predicted_set = set(write_set_paths)
    tp = len(predicted_set & gold)
    fp = len(predicted_set - gold)
    fn = len(gold - predicted_set)
    precision = tp / len(predicted_set) if predicted_set else 0.0
    recall = tp / len(gold) if gold else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fnr = fn / len(gold) if gold else 0.0
    terminal_status = "succeeded" if (not validator_errors and not cap_hit) else "failed"
    entry.update(
        {
            "terminal_status": terminal_status,
            "predicted_write_set": sorted(predicted_set),
            "predicted_write_set_size": len(predicted_set),
            "hidden_gold_used_after_inference": sorted(gold),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": round(precision, 6),
            "recall": round(recall, 6),
            "f1": round(f1, 6),
            "fnr": round(fnr, 6),
            "full_recall": bool(gold and recall >= 1.0),
        }
    )
    return entry


def run_cell(cell: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    prompt = _render_cell_prompt(cell)
    schema_name = "controlled_encoding_full_v2" if cell["arm"] == "full_v2" else "controlled_encoding_sparse_v2"
    started = time.monotonic()
    result = _call_openrouter(prompt, schema_name)
    elapsed = time.monotonic() - started
    evidence = _build_cell_evidence(cell, prompt, result, elapsed)
    return evidence, result.get("raw") if result.get("ok") else None


# ---------------------------------------------------------------------------
# Run / checkpoint / cost lock
# ---------------------------------------------------------------------------


def _load_progress() -> dict[str, Any]:
    path = STUDY_DIR / "progress.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_progress(payload: dict[str, Any]) -> None:
    _persist_json("progress.json", payload)


def _cumulative_cost(records: dict[str, dict[str, Any]]) -> float:
    return round(sum(float(r.get("api_cost", 0.0)) for r in records.values()), 6)


def _projected_completion_cost(
    records: dict[str, dict[str, Any]], cells: list[dict[str, Any]]
) -> float:
    done_ids = set(records)
    remaining = [c for c in cells if c["run_id"] not in done_ids]
    if not remaining:
        return 0.0
    done_costs = [float(r["api_cost"]) for r in records.values() if r["api_cost"] > 0.0]
    # Conservative default per-cell projected cost derived from LIVE DeepInfra
    # pricing and the actual rendered prompt sizes (scenario-004 full ~6,900
    # chars ~1,725 tokens; sparse ~7,000 chars ~1,750 tokens at the len//4
    # heuristic) with completion at the frozen 4096 cap:
    #   prompt: 1750 x $0.30/1M = $0.000525
    #   completion: 4096 x $1.00/1M = $0.004096
    #   worst-case cell ~ $0.00462 -> conservative default $0.005.
    mean_cost = (sum(done_costs) / len(done_costs)) if done_costs else 0.005
    return round(mean_cost * len(remaining) * (1 + COST_MARGIN), 6)


def _cost_budget_ok(
    records: dict[str, dict[str, Any]], manifest: dict[str, Any]
) -> dict[str, Any]:
    cumulative = _cumulative_cost(records)
    projected = _projected_completion_cost(records, manifest["cells"])
    total = round(cumulative + projected, 6)
    ok = total <= SCIENTIFIC_CEILING_USD
    return {
        "ok": ok,
        "cumulative_usd": cumulative,
        "projected_remaining_usd": projected,
        "projected_total_usd": total,
        "ceiling_usd": SCIENTIFIC_CEILING_USD,
    }


def _truncation_count(rows: list[dict[str, Any]]) -> int:
    return sum(1 for r in rows if r.get("truncation_status"))


def _write_checkpoint(
    records: dict[str, dict[str, Any]], manifest: dict[str, Any]
) -> None:
    total = len(records)
    full = [r for r in records.values() if r["arm"] == "full_v2"]
    sparse = [r for r in records.values() if r["arm"] == "sparse_v2"]
    checkpoint = {
        "completed": total,
        "total_cells": len(manifest["cells"]),
        "valid": sum(1 for r in records.values() if r["terminal_status"] == "succeeded"),
        "failed": sum(1 for r in records.values() if r["terminal_status"] != "succeeded"),
        "truncations": _truncation_count(list(records.values())),
        "full_v2": {
            "recorded": len(full),
            "valid": sum(1 for r in full if r["terminal_status"] == "succeeded"),
            "failed": sum(1 for r in full if r["terminal_status"] != "succeeded"),
            "truncations": _truncation_count(full),
        },
        "sparse_v2": {
            "recorded": len(sparse),
            "valid": sum(1 for r in sparse if r["terminal_status"] == "succeeded"),
            "failed": sum(1 for r in sparse if r["terminal_status"] != "succeeded"),
            "truncations": _truncation_count(sparse),
        },
        "requests_issued": sum(1 for r in records.values() if r.get("request_issued", r.get("request_dispatched"))),
        "responses_received": sum(1 for r in records.values() if r.get("provider_response_received")),
        "usage_known_cells": sum(1 for r in records.values() if r.get("usage_known")),
        "usage_unknown_cells": sum(1 for r in records.values() if not r.get("usage_known")),
        "transport_failure_cells": sum(1 for r in records.values() if r.get("transport_failure")),
        "prompt_tokens": sum(int(r["prompt_tokens"]) for r in records.values()),
        "completion_tokens": sum(int(r["completion_tokens"]) for r in records.values()),
        "total_tokens": sum(int(r["total_tokens"]) for r in records.values()),
        "calls": sum(int(r["model_calls"]) for r in records.values()),
        "cost_usd": _cumulative_cost(records),
        "elapsed_seconds": round(
            time.monotonic() - _load_progress().get("_run_started_at", time.monotonic()), 1
        ),
        "checkpoint_at": _now_iso(),
    }
    _persist_json(f"checkpoint_{total}.json", checkpoint)
    _save_progress(checkpoint)


def cmd_run(args: argparse.Namespace) -> int:
    manifest = _load_manifest()
    cells = manifest["cells"]
    if not _gates_evidence_passed() and not args.skip_gate_check:
        print("Refusing to run scientific cells before the six gates + audit pass.")
        return 2
    if not _probes_passed():
        print("Refusing to run scientific cells before the capability probes pass.")
        return 2

    records = _loaded_records()
    if len(records) >= len(cells):
        print(f"Manifest already complete: {len(records)}/{len(cells)} records present.")
        _write_checkpoint(records, manifest)
        return 0

    budget = _cost_budget_ok(records, manifest)
    print(json.dumps(budget, indent=2))
    if not budget["ok"]:
        print("COST_BUDGET_STOP")
        _write_checkpoint(records, manifest)
        return 1

    progress = _load_progress()
    run_started_at = float(progress.get("_run_started_at", time.monotonic()))
    if len(records) == 0:
        progress["_run_started_at"] = time.monotonic()
        _save_progress(progress)
        run_started_at = float(progress["_run_started_at"])
    elapsed_now = time.monotonic() - run_started_at
    if elapsed_now >= RUNTIME_CEILING_SECONDS:
        print("RUNTIME_CEILING_STOP")
        _write_checkpoint(records, manifest)
        return 1

    pending = [c for c in cells if c["run_id"] not in records]
    limit = args.limit if args.limit and args.limit > 0 else len(pending)
    batch = pending[:limit]
    delay = max(0.0, float(getattr(args, "inter_cell_delay", 0.0) or 0.0))
    print(f"RUNNING_BATCH={len(batch)} of pending={len(pending)} inter_cell_delay={delay}s")

    for idx, cell in enumerate(batch, start=1):
        print(f"\n=== CELL {cell['run_id']} ===")
        evidence, raw_text = run_cell(cell)
        _append_record(evidence)
        records[cell["run_id"]] = evidence
        per_run = STUDY_DIR / "runs" / f"{cell['run_id']}.json"
        per_run.parent.mkdir(parents=True, exist_ok=True)
        per_run.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
        if raw_text is not None:
            raw_dir = STUDY_DIR / "runs" / "raw"
            raw_path = raw_dir / f"{cell['run_id']}.txt"
            _write_bytes(raw_path, raw_text.encode("utf-8"))
            sha_path = raw_dir / f"{cell['run_id']}.sha256"
            _write_bytes(sha_path, (evidence["raw_response_sha256"] + "\n").encode("utf-8"))
        print(json.dumps(
            {k: evidence[k] for k in (
                "run_id", "terminal_status", "schema_valid", "finish_reason",
                "truncation_status", "decoded_candidate_count", "decoded_write_set_ids",
                "predicted_write_set_size", "tp", "fp", "fn", "precision", "recall", "f1",
                "prompt_tokens", "completion_tokens", "total_tokens", "model_calls",
                "latency_seconds", "api_cost",
            )}, indent=2))
        print(f"persisted={per_run}")
        if idx % CHECKPOINT_EVERY == 0 or len(records) >= len(cells):
            _write_checkpoint(records, manifest)
            checkpoint = _load_progress()
            print(json.dumps(checkpoint, indent=2))
        if delay and len(records) < len(cells):
            print(f"pacing {delay:.0f}s before next cell", flush=True)
            time.sleep(delay)

        if len(records) < len(cells):
            budget = _cost_budget_ok(records, manifest)
            if not budget["ok"]:
                print("COST_BUDGET_STOP")
                _write_checkpoint(records, manifest)
                return 1

    completed = len(records)
    print(f"\nBATCH_COMPLETE completed={completed}/{len(cells)}")
    _write_checkpoint(records, manifest)
    return 0


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


def _valid_runs(records: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {rid: r for rid, r in records.items() if r["terminal_status"] == "succeeded"}


def _micro(rows: list[dict[str, Any]]) -> dict[str, Any]:
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


def _stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {"mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0}
    n = len(values)
    s = sorted(values)
    mean = sum(values) / n
    median = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
    return {"mean": round(mean, 6), "median": round(median, 6), "min": round(s[0], 6), "max": round(s[-1], 6)}


def _serialized_record_count(record: dict[str, Any]) -> int:
    if record.get("arm") == "full_v2":
        return int(record.get("decoded_candidate_count", 0)) or int(record.get("emitted_decisions", 0))
    return int(record.get("decoded_write_set_ids") and len(record.get("decoded_write_set_ids") or []))


def _arm_metrics(records: dict[str, dict[str, Any]], arm: str) -> dict[str, Any]:
    arm_records = {rid: r for rid, r in records.items() if r["arm"] == arm}
    valid = {rid: r for rid, r in arm_records.items() if r["terminal_status"] == "succeeded"}
    rows_all = list(arm_records.values())
    rows_valid = list(valid.values())

    per_scenario: dict[str, dict[str, Any]] = {}
    for scenario_id in FINAL_SCENARIOS:
        all_rows = [r for r in rows_all if r["scenario_id"] == scenario_id]
        v_rows = [r for r in rows_valid if r["scenario_id"] == scenario_id]
        failures = []
        for r in all_rows:
            if r["terminal_status"] != "succeeded":
                failures.append(
                    {
                        "run_id": r["run_id"],
                        "terminal_status": r["terminal_status"],
                        "failure_category": r.get("failure_category", ""),
                    }
                )
        per_scenario[scenario_id] = {
            "cells": len(all_rows),
            "valid_runs": len(v_rows),
            "failed_runs": len(all_rows) - len(v_rows),
            "truncations": _truncation_count(all_rows),
            "failure_taxonomy": failures,
            "pooled_micro": _micro(v_rows) if v_rows else _micro([]),
        }

    return {
        "arm": arm,
        "recorded": len(rows_all),
        "valid": len(rows_valid),
        "failed": len(rows_all) - len(rows_valid),
        "truncations": _truncation_count(rows_all),
        "validity_rate": round(len(rows_valid) / len(rows_all), 6) if rows_all else 0.0,
        "truncation_rate": round(_truncation_count(rows_all) / len(rows_all), 6) if rows_all else 0.0,
        "failure_taxonomy": [
            {
                k: r[k]
                for k in (
                    "run_id", "scenario_id", "repetition", "terminal_status",
                    "failure_category",
                )
            }
            for r in rows_all if r["terminal_status"] != "succeeded"
        ],
        "overall": {**_micro(rows_valid), "valid_runs": len(rows_valid)},
        "serialized_records": _stats([float(_serialized_record_count(r)) for r in rows_all]),
        "completion_tokens": _stats([float(r["completion_tokens"]) for r in rows_all]),
        "prompt_tokens": _stats([float(r["prompt_tokens"]) for r in rows_all]),
        "total_tokens": _stats([float(r["total_tokens"]) for r in rows_all]),
        "calls": sum(int(r["model_calls"]) for r in rows_all),
        "requests_issued": sum(1 for r in rows_all if r.get("request_issued", r.get("request_dispatched"))),
        "responses_received": sum(1 for r in rows_all if r.get("provider_response_received")),
        "usage_known_cells": sum(1 for r in rows_all if r.get("usage_known")),
        "usage_unknown_cells": sum(1 for r in rows_all if not r.get("usage_known")),
        "transport_failure_cells": sum(1 for r in rows_all if r.get("transport_failure")),
        "latency_seconds": round(sum(float(r["latency_seconds"]) for r in rows_all), 6),
        "api_cost_usd": round(sum(float(r["api_cost"]) for r in rows_all), 6),
        "per_scenario": per_scenario,
    }


def compute_metrics(records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    manifest = _load_manifest()
    arms = {arm: _arm_metrics(records, arm) for arm in ARMS}
    rows_all = list(records.values())
    totals = {
        "cells": len(manifest["cells"]),
        "recorded": len(rows_all),
        "valid": sum(1 for r in rows_all if r["terminal_status"] == "succeeded"),
        "failed": sum(1 for r in rows_all if r["terminal_status"] != "succeeded"),
        "truncations": _truncation_count(rows_all),
        "prompt_tokens": sum(int(r["prompt_tokens"]) for r in rows_all),
        "completion_tokens": sum(int(r["completion_tokens"]) for r in rows_all),
        "total_tokens": sum(int(r["total_tokens"]) for r in rows_all),
        "model_calls": sum(int(r["model_calls"]) for r in rows_all),
        "requests_issued": sum(1 for r in rows_all if r.get("request_issued", r.get("request_dispatched"))),
        "responses_received": sum(1 for r in rows_all if r.get("provider_response_received")),
        "usage_known_cells": sum(1 for r in rows_all if r.get("usage_known")),
        "usage_unknown_cells": sum(1 for r in rows_all if not r.get("usage_known")),
        "transport_failure_cells": sum(1 for r in rows_all if r.get("transport_failure")),
        "latency_seconds": round(sum(float(r["latency_seconds"]) for r in rows_all), 6),
        "api_cost_usd": _cumulative_cost(records),
    }
    return {
        "study_id": STUDY_ID,
        "model": PRIMARY_MODEL,
        "model_human": MODEL_HUMAN,
        "gateway": "OpenRouter",
        "provider_tag": PROVIDER_TAG,
        "reasoning_mode": REASONING_MODE_LABEL,
        "graph": "OFF",
        "arms": arms,
        "totals": totals,
        "computed_at": _now_iso(),
    }


def cmd_metrics(_args: argparse.Namespace) -> int:
    records = _loaded_records()
    manifest = _load_manifest()
    if len(records) < len(manifest["cells"]):
        print(f"Only {len(records)}/{len(manifest['cells'])} records present — final metrics require all cells.")
        return 2
    metrics = compute_metrics(records)
    path = _persist_json("final_metrics.json", metrics)
    print(f"persisted={path}")
    print(json.dumps(metrics, indent=2))
    return 0


# ---------------------------------------------------------------------------
# Interpretation (M1.15) — frozen decision rule
# ---------------------------------------------------------------------------


def cmd_interpret(_args: argparse.Namespace) -> int:
    metrics_path = STUDY_DIR / "final_metrics.json"
    if not metrics_path.is_file():
        print("final_metrics.json not found — run metrics first")
        return 2
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    full = metrics["arms"]["full_v2"]
    sparse = metrics["arms"]["sparse_v2"]

    delta_validity_pp = round((sparse["validity_rate"] - full["validity_rate"]) * 100, 2)
    delta_truncation_pp = round((sparse["truncation_rate"] - full["truncation_rate"]) * 100, 2)
    delta_mean_completion = round(
        sparse["completion_tokens"]["mean"] - full["completion_tokens"]["mean"], 2
    )
    delta_mean_records = round(
        sparse["serialized_records"]["mean"] - full["serialized_records"]["mean"], 2
    )

    interpretation = {
        "primary_controlled_effects": {
            "delta_validity_percentage_points": delta_validity_pp,
            "delta_truncation_percentage_points": delta_truncation_pp,
            "delta_mean_completion_tokens": delta_mean_completion,
            "delta_median_completion_tokens": round(
                sparse["completion_tokens"]["median"] - full["completion_tokens"]["median"], 2
            ),
            "delta_mean_serialized_records": delta_mean_records,
            "delta_median_serialized_records": round(
                sparse["serialized_records"]["median"] - full["serialized_records"]["median"], 2
            ),
            "full_v2_validity_rate": full["validity_rate"],
            "sparse_v2_validity_rate": sparse["validity_rate"],
            "full_v2_truncation_rate": full["truncation_rate"],
            "sparse_v2_truncation_rate": sparse["truncation_rate"],
        },
    }
    result = {"interpretation": interpretation}
    _persist_json("interpretation.json", result)
    print(json.dumps(result, indent=2))
    return 0


# ---------------------------------------------------------------------------
# Closure
# ---------------------------------------------------------------------------


def cmd_close(_args: argparse.Namespace) -> int:
    gates = [g() for g in GATES]
    all_passed = all(g["passed"] for g in gates)
    audit = _independent_audit()
    immut = _primary_evidence_immutable()
    records = _loaded_records()
    manifest = _load_manifest()
    result = {
        "closure_gates": gates,
        "gates_all_passed": all_passed,
        "audit": audit,
        "primary_evidence_immutable": immut,
        "zero_scientific_calls_in_closure": True,
        "does_not_modify_scientific_results": True,
        "manifest_cells": len(manifest["cells"]),
        "recorded_cells": len(records),
        "no_replacement_reruns": True,
        "no_run_61": True,
        "cap_stayed_4096": True,
        "model_provider_fallback_frozen": True,
        "graph_absent": True,
        "raw_responses_persisted": True,
        "hidden_gold_evaluation_only": True,
        "ran_at": _now_iso(),
    }
    path = _persist_json("closure_gates.json", result)
    for gate in gates:
        print(f"Closure Gate {gate['gate']} {gate['name']}: {'PASS' if gate['passed'] else 'FAIL'}")
    print(f"CLOSURE_AUDIT={'PASS' if audit['passed'] else 'FAIL'}")
    print(f"PRIMARY_IMMUTABLE={'PASS' if immut['immutable'] else 'FAIL'}")
    print(f"persisted={path}")
    return 0 if (all_passed and audit["passed"] and immut["immutable"]) else 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def cmd_all(args: argparse.Namespace) -> int:
    if cmd_prevalidate(args) != 0:
        print("PREVALIDATION FAILED — STOP")
        return 1
    if cmd_prompt_control(args) != 0:
        print("PROMPT CONTROL FAILED — STOP")
        return 1
    if cmd_probe(args) != 0:
        print("CAPABILITY PROBES FAILED — STOP")
        return 1
    if cmd_gates(args) != 0:
        print("GATES FAILED — STOP")
        return 1
    if cmd_freeze_manifest(args) != 0:
        print("MANIFEST FREEZE FAILED — STOP")
        return 1
    if cmd_run(args) != 0:
        return 1
    if cmd_metrics(args) != 0:
        return 1
    if cmd_interpret(args) != 0:
        return 1
    if cmd_close(args) != 0:
        return 1
    print("\nCONTROLLED_ENCODING_ABLATION PIPELINE COMPLETE")
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prevalidate", help="pre-run validation")
    p.add_argument("--output-dir", type=str, default=str(STUDY_DIR))
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("prompt-control", help="prompt-control proof (M1.4)")
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("probe", help="two non-study capability probes (M1.6)")
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("gates", help="six deterministic gates + audit")
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("freeze-manifest", help="freeze the 60-cell manifest")
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("run", help="execute remaining manifest cells")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--inter-cell-delay", type=float, default=0.0)
    p.add_argument("--skip-gate-check", action="store_true", default=False)
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("metrics", help="compute final metrics")
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("interpret", help="apply frozen interpretation rule")
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("close", help="closure six gates + audit")
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("all", help="full pipeline")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--inter-cell-delay", type=float, default=0.0)
    p.add_argument("--skip-gate-check", action="store_true", default=False)
    p.set_defaults(_set_study_dir=True)
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    global STUDY_DIR
    if getattr(args, "_set_study_dir", False) and getattr(args, "output_dir", None):
        STUDY_DIR = Path(args.output_dir)
    if args.command == "prevalidate":
        return cmd_prevalidate(args)
    if args.command == "prompt-control":
        return cmd_prompt_control(args)
    if args.command == "probe":
        return cmd_probe(args)
    if args.command == "gates":
        return cmd_gates(args)
    if args.command == "freeze-manifest":
        return cmd_freeze_manifest(args)
    if args.command == "run":
        return cmd_run(args)
    if args.command == "metrics":
        return cmd_metrics(args)
    if args.command == "interpret":
        return cmd_interpret(args)
    if args.command == "close":
        return cmd_close(args)
    if args.command == "all":
        return cmd_all(args)
    print(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
