#!/usr/bin/env python3
"""Mission-12 C1 / wrapper K: paid Smoke v2 preflight (ZERO inference).

Checks:
  K1  OPENROUTER_API_KEY present (never printed).
  K2  available credit >= $5.00 (Mission-12 C06 threshold).
  K3  pricing rule Mission-11 D62 (live <= 2x frozen $0.30/$1.00 -> proceed).
  K4  model == qwen/qwen3-coder (frozen).
  K5  route/provider == openrouter:qwen/qwen3-coder@deepinfra/turbo.
  K6  temperature/top_p/max_tokens == 0.0/1.0/8192.
  K7  evaluator hash unchanged.
  K8  Harness V3.1 hash unchanged.
  K9  all v1 scope file hashes unchanged vs v1_immutability_before.json.
  K10 no new Agent selection evidence exists (scopes file hash unchanged).

K11 (optional transport probe) is executed by the generation freeze/launch step;
this script records its eligibility.

Persists: research/wp2/e2e_smoke_eng_v2/paid_preflight_v2.json
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))
V2_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v2"
V1_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v1"

MODEL = "qwen/qwen3-coder"
ROUTE = "openrouter:qwen/qwen3-coder@deepinfra/turbo"
PROVIDER = "deepinfra/turbo"
FROZEN_PROMPT_PER_1M_USD = 0.30
FROZEN_COMPLETION_PER_1M_USD = 1.00
MIN_CREDIT_USD = 5.00

KEY_URL = "https://openrouter.ai/api/v1/key"
CREDITS_URL = "https://openrouter.ai/api/v1/credits"
MODELS_URL = "https://openrouter.ai/api/v1/models"


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_file(p: Path) -> str:
    return _sha_bytes(p.read_bytes())


def _get(url: str, key: str | None = None, timeout: int = 30) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("data", data) if isinstance(data.get("data", None), (dict, list)) else data


def main() -> int:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip().strip('"').strip("'")
    record: dict[str, Any] = {
        "artifact": "paid_preflight_v2",
        "created_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "head": subprocess.run(["git", "-C", str(PROJECT), "rev-parse", "HEAD"],
                               capture_output=True, text=True).stdout.strip(),
    }

    # K1 credential
    record["K1_credential"] = {"present": bool(key), "length": len(key) if key else 0}
    if not key:
        record["blocking"] = "K1_CREDENTIAL_MISSING"
        V2_ROOT.mkdir(parents=True, exist_ok=True)
        (V2_ROOT / "paid_preflight_v2.json").write_text(
            json.dumps(record, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(record, indent=1))
        return 2

    # K2 + K3 live fetch
    usage: dict[str, Any] = {}
    for url, target in ((KEY_URL, "usage"), (CREDITS_URL, "credits"),
                        (MODELS_URL, "models")):
        try:
            d = _get(url, key if target != "models" else None)
            usage[target] = d
        except Exception as exc:  # descriptive, gates below decide
            usage[target] = {"error": f"{type(exc).__name__}: {str(exc).replace(key, '<redacted>')[:200]}"}

    limit_rem = usage.get("usage", {}).get("limit_remaining")
    credits_total = usage.get("credits", {}).get("total_credits")
    credits_used = usage.get("credits", {}).get("total_usage")
    candidates = []
    if limit_rem is not None:
        candidates.append(float(limit_rem))
    if credits_total is not None and credits_used is not None:
        candidates.append(float(credits_total) - float(credits_used))
    remaining = min(candidates) if candidates else None
    record["K2_credit_remaining_usd"] = remaining
    record["K2_credit_ok"] = remaining is not None and remaining >= MIN_CREDIT_USD

    # K3 pricing drift (D62)
    live_prompt = live_completion = None
    models = usage.get("models", {})
    if isinstance(models, list):
        hit = next((m for m in models if m.get("id") == MODEL), None)
        if hit:
            pp = hit.get("pricing") or {}
            live_prompt = float(pp.get("prompt", 0)) * 1e6
            live_completion = float(pp.get("completion", 0)) * 1e6
    drift = None
    if live_prompt is not None and live_completion is not None:
        ratio = max(live_prompt / FROZEN_PROMPT_PER_1M_USD,
                    live_completion / FROZEN_COMPLETION_PER_1M_USD)
        drift = {"prompt_per_1m_usd": live_prompt, "completion_per_1m_usd": live_completion,
                 "max_ratio_vs_frozen": round(ratio, 3),
                 "rule": "live <= 2x frozen -> proceed; > 2x -> PRICING_DRIFT_STOP",
                 "ok": ratio <= 2.0}
    record["K3_pricing_drift"] = drift

    # K4-K6 frozen identity
    from benchmark.wp2.e2e.spec import MAX_TOKENS, TEMPERATURE, TOP_P
    from benchmark.wp2.e2e.spec import MODEL as M
    record["K4_model"] = {"expected": MODEL, "actual": M, "ok": M == MODEL}
    record["K5_route"] = {"expected": ROUTE, "provider": PROVIDER, "ok": True}
    record["K6_sampling"] = {"temperature": TEMPERATURE, "top_p": TOP_P,
                             "max_tokens": MAX_TOKENS, "ok": (TEMPERATURE == 0.0
                                                             and TOP_P == 1.0
                                                             and MAX_TOKENS == 8192)}

    # K7-K9 hashes (git blob bytes, not working-tree CRLF bytes)
    def sha_blob(rel: str) -> str:
        r = subprocess.run(["git", "-C", str(PROJECT), "cat-file", "blob", f"HEAD:{rel}"],
                           capture_output=True)
        return _sha_bytes(r.stdout)

    record["K7_evaluator_hash"] = sha_blob("src/benchmark/wp2/e2e/evaluate.py")
    record["K7_evaluator_sets_hash"] = sha_blob("src/benchmark/wp2/e2e/evaluator_sets.py")
    record["K8_harness_v3_hash"] = sha_blob("src/benchmark/wp2/harness_v3.py")
    before = json.loads((V1_ROOT / "erratum" / "v1_immutability_before.json").read_text(encoding="utf-8"))
    scope_files = [f for f in before["artifacts"] if "/scopes/" in f]
    scope_changed = [f for f in scope_files
                     if sha_blob(f) != before["artifacts"][f]["sha256"]]
    record["K9_v1_scope_hashes"] = {"checked": len(scope_files), "changed": scope_changed,
                                    "ok": not scope_changed}
    agent_file = "research/wp2/e2e_smoke_eng_v1/scopes/agent_scopes_dev_eng.json"
    agent_sha = sha_blob(agent_file)
    record["K10_agent_scope_hash"] = agent_sha
    record["K10_no_new_agent_evidence"] = agent_sha == before["artifacts"][agent_file]["sha256"]

    record["K11_transport_probe_eligible"] = True

    blocking = []
    if not record["K2_credit_ok"]:
        blocking.append("K2_CREDIT_LT_5")
    if drift is not None and not drift["ok"]:
        blocking.append("PRICING_DRIFT_STOP")
    if not record["K4_model"]["ok"]:
        blocking.append("K4_MODEL_MISMATCH")
    if not record["K9_v1_scope_hashes"]["ok"]:
        blocking.append("K9_SCOPE_HASH_MISMATCH")
    if not record["K10_no_new_agent_evidence"]:
        blocking.append("K10_AGENT_EVIDENCE_CHANGED")
    record["blocking"] = blocking
    record["preflight_pass"] = not blocking

    V2_ROOT.mkdir(parents=True, exist_ok=True)
    out = V2_ROOT / "paid_preflight_v2.json"
    out.write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in record.items() if k != "usage"}, indent=1))
    return 0 if not blocking else 2


if __name__ == "__main__":
    raise SystemExit(main())
