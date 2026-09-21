#!/usr/bin/env python3
"""WP-1b G6 - provider/model pricing preflight (ZERO paid inference).

Fetches the current OpenRouter public model metadata for qwen/qwen3-coder
(free metadata API, no key, no inference) and records:
- timestamp UTC
- model ID, provider/router, provider route (deepinfra/turbo)
- input/output/cache prices, context limits, completion limit
- structured-output and tool support
Compares against the frozen WP-1a protocol identity
(openrouter:qwen/qwen3-coder@deepinfra/turbo, $0.30/$1.00 per 1M).
If the live fetch is unavailable, records the frozen verified pricing with an
explicit live-metadata-unavailable flag.

Outputs: artifacts/wp1b_provider_pricing_preflight_2026-09-21.json
"""
from __future__ import annotations

import datetime
import json
import urllib.request
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
OUT = _PROJECT_DIR / "artifacts" / "wp1b_provider_pricing_preflight_2026-09-21.json"

FROZEN_MODEL = "qwen/qwen3-coder"
FROZEN_ROUTE = "openrouter:qwen/qwen3-coder@deepinfra/turbo"
FROZEN_PROMPT_PER_1M_USD = 0.30
FROZEN_COMPLETION_PER_1M_USD = 1.00


def _fetch_model_metadata() -> tuple[dict | None, str | None]:
    """Fetch live metadata. Returns (payload_or_None, error_message_or_None)."""
    try:
        with urllib.request.urlopen(
            "https://openrouter.ai/api/v1/models", timeout=25
        ) as r:
            models = json.loads(r.read().decode("utf-8")).get("data", [])
        hit = next((m for m in models if m.get("id") == FROZEN_MODEL), None)
        if hit is None:
            return None, f"model {FROZEN_MODEL!r} not found in live model list"
        with urllib.request.urlopen(
            f"https://openrouter.ai/api/v1/models/{FROZEN_MODEL}/endpoints", timeout=25
        ) as r:
            endpoints = json.loads(r.read().decode("utf-8")).get("data", {}).get("endpoints", [])
        deepinfra = next((e for e in endpoints if e.get("tag") == "deepinfra/turbo"), None)
        return {"model": hit, "endpoints": endpoints, "deepinfra": deepinfra}, None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def _frozen_fallback() -> dict:
    return {
        "live_metadata_available": False,
        "error": "live metadata fetch failed at execution time",
        "frozen_verified_pricing_2026_09_20": {
            "prompt_per_1m_usd": FROZEN_PROMPT_PER_1M_USD,
            "completion_per_1m_usd": FROZEN_COMPLETION_PER_1M_USD,
            "source": "research/wp1a/wp1a_budget_model.json (verified live 2026-09-20)",
        },
    }


def main() -> int:
    ts = datetime.datetime.now(datetime.UTC).isoformat()
    payload, error = _fetch_model_metadata()

    if payload is None:
        record = {
            "artifact": "wp1b_provider_pricing_preflight",
            "generated_utc": ts,
            **_frozen_fallback(),
            "frozen_route": FROZEN_ROUTE,
            "route_matches_frozen": None,
            "model_matches_frozen": None,
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(record, indent=1), encoding="utf-8")
        print(f"[pricing-preflight] live metadata unavailable: {error}")
        print("[pricing-preflight] WARNING: route/model match could not be "
              "re-confirmed at execution time; frozen verified pricing recorded.")
        return 0

    model = payload["model"]
    pricing = model.get("pricing", {})
    deepinfra = payload["deepinfra"]
    deepinfra_pricing = (deepinfra or {}).get("pricing", {})
    supported = model.get("supported_parameters", [])
    endpoints = payload["endpoints"]
    endpoint_tags = [e.get("tag") for e in endpoints]

    model_matches = model.get("id") == FROZEN_MODEL
    route_matches = "deepinfra/turbo" in endpoint_tags
    prompt_ok = abs(float(deepinfra_pricing.get("prompt", 0)) * 1e6 - FROZEN_PROMPT_PER_1M_USD) < 1e-9
    completion_ok = abs(float(deepinfra_pricing.get("completion", 0)) * 1e6 - FROZEN_COMPLETION_PER_1M_USD) < 1e-9

    record = {
        "artifact": "wp1b_provider_pricing_preflight",
        "generated_utc": ts,
        "live_metadata_available": True,
        "model": {
            "id": model.get("id"),
            "name": model.get("name"),
            "context_length": model.get("context_length"),
            "pricing_per_token": pricing,
            "pricing_per_1m_usd": {
                "prompt": float(pricing.get("prompt", 0)) * 1e6,
                "completion": float(pricing.get("completion", 0)) * 1e6,
                "input_cache_read": float(pricing.get("input_cache_read", 0)) * 1e6,
            },
            "top_provider_max_completion_tokens": (model.get("top_provider") or {}).get("max_completion_tokens"),
            "supported_parameters": supported,
            "structured_outputs_supported": "structured_outputs" in supported,
            "response_format_supported": "response_format" in supported,
            "tools_supported": "tools" in supported,
        },
        "deepinfra_route": {
            "tag": (deepinfra or {}).get("tag"),
            "quantization": (deepinfra or {}).get("quantization"),
            "context_length": (deepinfra or {}).get("context_length"),
            "max_completion_tokens": (deepinfra or {}).get("max_completion_tokens"),
            "pricing_per_1m_usd": {
                "prompt": float(deepinfra_pricing.get("prompt", 0)) * 1e6,
                "completion": float(deepinfra_pricing.get("completion", 0)) * 1e6,
                "input_cache_read": float(deepinfra_pricing.get("input_cache_read", 0)) * 1e6,
            },
            "status": (deepinfra or {}).get("status"),
            "uptime_last_1d_pct": (deepinfra or {}).get("uptime_last_1d"),
        },
        "available_endpoint_tags": endpoint_tags,
        "frozen_protocol": {
            "model": FROZEN_MODEL,
            "route": FROZEN_ROUTE,
            "prompt_per_1m_usd": FROZEN_PROMPT_PER_1M_USD,
            "completion_per_1m_usd": FROZEN_COMPLETION_PER_1M_USD,
        },
        "checks": {
            "model_matches_frozen": model_matches,
            "route_matches_frozen": route_matches,
            "prompt_price_matches_frozen": prompt_ok,
            "completion_price_matches_frozen": completion_ok,
            "no_drift": bool(model_matches and route_matches and prompt_ok and completion_ok),
        },
        "note": "Fetched from OpenRouter public metadata API at execution time; "
                "no paid inference was invoked.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(record, indent=1), encoding="utf-8")

    ok = record["checks"]["no_drift"]
    print(f"[pricing-preflight] generated_utc: {ts}")
    print(f"[pricing-preflight] model_matches_frozen: {model_matches}")
    print(f"[pricing-preflight] route_matches_frozen: {route_matches}")
    print(f"[pricing-preflight] prompt_price_matches_frozen: {prompt_ok} "
          f"({record['deepinfra_route']['pricing_per_1m_usd']['prompt']:.4f}/1M)")
    print(f"[pricing-preflight] completion_price_matches_frozen: {completion_ok} "
          f"({record['deepinfra_route']['pricing_per_1m_usd']['completion']:.4f}/1M)")
    print(f"[pricing-preflight] no_drift: {ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
