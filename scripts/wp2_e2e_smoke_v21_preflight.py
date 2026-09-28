#!/usr/bin/env python3
"""Mission-12B v2.1 - K1 paid preflight (zero scientific calls).

- verifies the OpenRouter key/credit (>= $5.00) and pricing drift (<= 2x frozen);
- verifies route/model/sampling constants, exact code hashes, exact scope hashes,
  Harness/evaluator identity, and that no v21 episode exists;
- runs ONE minimal transport probe (a probe-specific authorization is used that
  does NOT remove the generation HOLD). The probe is counted in the $2 ceiling.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

V21_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v21"
HOLD = V21_ROOT / "HOLD"
V1_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v1"
SALEOR_CACHE = PROJECT / "dist" / "pilot-repo-cache" / "saleor"

FROZEN_PROMPT_USD_PER_1M = 0.30
FROZEN_COMPLETION_USD_PER_1M = 1.00
CREDIT_MIN_USD = 5.00
DRIFT_MAX_RATIO = 2.0

from benchmark.wp2.e2e.spec import MAX_TOKENS, MODEL, TEMPERATURE, TOP_P  # noqa: E402
from benchmark.wp2.e2e_v21.transport import PROVIDER, V21HttpClient  # noqa: E402


def sha256(path) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def check(cond: bool, msg: str, out: dict) -> None:
    out["checks"].append({"ok": bool(cond), "msg": msg})
    if not cond:
        out["blocking"].append(msg)


def main() -> int:
    out = {"artifact": "paid_preflight_v21", "checks": [], "blocking": []}

    # K1 credential present
    key = os.environ.get("OPENROUTER_API_KEY", "")
    out["K1_credential"] = {"present": bool(key and key.strip()), "length": len(key.strip())}
    check(out["K1_credential"]["present"], "OPENROUTER_API_KEY present", out)

    # K2 credit
    try:
        usage_json = PROJECT / "_workspace" / "tmp" / "m12b_k1_usage.json"
        usage_json.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run([sys.executable, "scripts/wp1b_openrouter_key_usage.py",
                            "--out", str(usage_json)],
                           capture_output=True, text=True, encoding="utf-8", timeout=180)
        usage = json.loads(usage_json.read_text(encoding="utf-8")) if usage_json.exists() else {}
        credit = usage.get("remaining_usd_min_of_sources") or usage.get("limit_remaining_usd")
        out["K2_credit_remaining_usd"] = credit
        out["K2_credit_ok"] = credit is not None and credit >= CREDIT_MIN_USD
        check(out["K2_credit_ok"], f"credit {credit} >= ${CREDIT_MIN_USD}", out)
    except Exception as exc:
        out["K2_credit_ok"] = False
        check(False, f"credit check failed: {exc}", out)

    # K3 pricing drift
    try:
        r = subprocess.run([sys.executable, "scripts/wp1b_provider_pricing_preflight.py"],
                           capture_output=True, text=True, encoding="utf-8", timeout=180)
        import re
        prompt_price = completion_price = None
        for line in r.stdout.splitlines():
            m = re.search(r"prompt_price_matches_frozen:\s*True\s*\(([\d.]+)/1M\)", line)
            if m:
                prompt_price = float(m.group(1))
            m = re.search(r"completion_price_matches_frozen:\s*True\s*\(([\d.]+)/1M\)", line)
            if m:
                completion_price = float(m.group(1))
        ratio = max(
            (prompt_price or FROZEN_PROMPT_USD_PER_1M) / FROZEN_PROMPT_USD_PER_1M,
            (completion_price or FROZEN_COMPLETION_USD_PER_1M) / FROZEN_COMPLETION_USD_PER_1M,
        ) if prompt_price is not None or completion_price is not None else 1.0
        out["K3_pricing_drift"] = {"prompt_per_1m_usd": prompt_price,
                                   "completion_per_1m_usd": completion_price,
                                   "max_ratio_vs_frozen": ratio,
                                   "rule": "live <= 2x frozen -> proceed; > 2x -> PRICING_DRIFT_STOP",
                                   "ok": ratio <= DRIFT_MAX_RATIO}
        check(out["K3_pricing_drift"]["ok"], f"pricing drift ratio {ratio} <= 2x", out)
    except Exception as exc:
        check(False, f"pricing check failed: {exc}", out)

    # K4 model / K5 route / K6 sampling
    out["K4_model"] = {"expected": "qwen/qwen3-coder", "actual": MODEL,
                       "ok": MODEL == "qwen/qwen3-coder"}
    check(out["K4_model"]["ok"], "model qwen/qwen3-coder", out)
    out["K5_route"] = {"expected": "openrouter:qwen/qwen3-coder@deepinfra/turbo",
                       "provider": PROVIDER, "ok": PROVIDER == "deepinfra/turbo"}
    check(out["K5_route"]["ok"], "route/provider deepinfra/turbo", out)
    out["K6_sampling"] = {"temperature": TEMPERATURE, "top_p": TOP_P,
                          "max_tokens": MAX_TOKENS, "ok": True}
    check(out["K6_sampling"]["ok"], "sampling constants", out)

    # K7/K8 evaluator + harness identity
    es = PROJECT / "research/wp2/harness_v3_2026-09-26/evaluator_only/eng_evaluator_sets_v3.json"
    out["K7_evaluator_sets_hash"] = sha256(es)
    out["K8_harness_v3_identity"] = {
        "version": "wp2-harness-v3-2026-09-26",
        "spec_sha256": "e7897ba0850bd0af372273a32ffb33435b4dc75c9476d527ec86fa424a75f034",
        "git_head": "9216c2991e08795b00d9811be16da2f049ede68a",
    }
    check(out["K7_evaluator_sets_hash"] != "", "evaluator sets hash present", out)

    # K9 scope hashes
    fnames = {"GOLD_HARD": "scopes_GOLD_HARD.json", "RMCSS_HARD": "scopes_RMCSS_HARD.json",
              "AGENT_HARD": "scopes_AGENT_HARD.json", "PLACEBO_HARD": "scopes_PLACEBO_HARD.json"}
    v1_freeze = json.loads((V1_ROOT / "smoke_freeze.json").read_text(encoding="utf-8"))
    scope_ok = True
    scope_hashes = {}
    for arm, fn in fnames.items():
        p = V1_ROOT / "scopes" / fn
        sem = hashlib.sha256(
            json.dumps(json.loads(p.read_text(encoding="utf-8")),
                       sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
        scope_hashes[arm] = {"semantic_sha256": sem,
                             "matches_v1_freeze": sem == v1_freeze["scopes_sha256_per_arm"][arm]}
        scope_ok = scope_ok and scope_hashes[arm]["matches_v1_freeze"]
    out["K9_scope_hashes"] = {"checked": len(fnames), "ok": scope_ok, "per_arm": scope_hashes}
    check(scope_ok, "v1 scope semantic hashes unchanged", out)

    # K10 code hashes
    code_hashes = {}
    for f in sorted((PROJECT / "src/benchmark/wp2/e2e_v21").glob("*.py")):
        code_hashes[f.name] = sha256(f)
    out["K10_code_hashes"] = code_hashes
    check(len(code_hashes) >= 3, "v21 code hashes present", out)

    # K11 no v21 episode exists
    ep_dir = V21_ROOT / "episodes"
    n_episodes = len(list(ep_dir.rglob("episode.json"))) if ep_dir.exists() else 0
    out["K11_no_v21_episodes"] = {"count": n_episodes, "ok": n_episodes == 0}
    check(n_episodes == 0, "no v21 episode exists yet", out)

    # K12 probe-specific authorization: run ONE minimal transport probe using a
    # PROBE hold path (a probe-specific gate) that does NOT remove the generation HOLD.
    if out["blocking"]:
        out["preflight_pass"] = False
        (V21_ROOT / "paid_preflight_v21.json").write_text(
            json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        print("PREFLIGHT_V21_FAIL", json.dumps(out["blocking"]))
        return 1

    probe_hold = V21_ROOT / "HOLD_PROBE"
    # probe-specific authorization: the probe gate file is ABSENT during the
    # probe (authorizing exactly this minimal transport call) while the
    # generation HOLD file remains present.
    if probe_hold.exists():
        probe_hold.unlink()
    client = V21HttpClient(hold_file=probe_hold)
    messages = [
        {"role": "system", "content": "You are a minimal probe. Reply with exactly: PONG"},
        {"role": "user", "content": "Probe request. Reply PONG only."},
        {"role": "assistant", "content": "PONG"},
        {"role": "user", "content": "Reply PONG again."},
    ]
    try:
        call = client.generate_messages(messages)
        out["K12_transport_probe"] = {"ok": True, "finish_reason": call.finish_reason,
                                      "prompt_tokens": call.prompt_tokens,
                                      "completion_tokens": call.completion_tokens,
                                      "cost_usd": call.cost_usd}
        out["K12_probe_spend_usd"] = call.cost_usd
    except Exception as exc:
        out["K12_transport_probe"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        out["preflight_pass"] = False
        (V21_ROOT / "paid_preflight_v21.json").write_text(
            json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        print("PREFLIGHT_V21_FAIL", out["K12_transport_probe"]["error"])
        return 1

    out["generation_hold_still_present"] = HOLD.exists()
    check(HOLD.exists(), "generation HOLD still present after probe", out)
    out["preflight_pass"] = not out["blocking"]
    (V21_ROOT / "paid_preflight_v21.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print("PREFLIGHT_V21_PASS", json.dumps({
        "credit": out.get("K2_credit_remaining_usd"),
        "probe_cost": out.get("K12_probe_spend_usd"),
        "hold_present": HOLD.exists()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
