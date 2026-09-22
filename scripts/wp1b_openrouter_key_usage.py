#!/usr/bin/env python3
"""Record OpenRouter key usage and account credits - zero tokens, no inference.

Run once BEFORE and once AFTER each paid WP-1b run:
  python scripts/wp1b_openrouter_key_usage.py --out research/wp1b/main-297-2026-09-22/key_usage_before.json \
      --require-remaining-usd 25
  python scripts/wp1b_openrouter_key_usage.py --out research/wp1b/main-297-2026-09-22/key_usage_after.json

Sources: ``GET /api/v1/key`` (usage, key limit, limit remaining) and, when the
key may read it, ``GET /api/v1/credits`` (total_credits, total_usage).
The key is read from OPENROUTER_API_KEY and is never printed or written.

Billed spend = after.usage - before.usage (valid only if nothing else used the key
in between). The preregistered verdicts use frozen list-price accounting; this is
a transparency check (prompt caching can make billed < list price).

``--require-remaining-usd X`` (pre-run gate): the smaller of the key's
limit_remaining and the account balance (total_credits - total_usage), over the
sources that are available, must be >= X.

Exit: 0 recorded (gate passed, or no gate) | 2 remaining < X (top up / raise the
key limit, then rerun) | 4 OpenRouter unreachable or key rejected while a gate was
requested (retry later) - without a gate the script always exits 0.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import urllib.request
from pathlib import Path
from typing import Any

KEY_URL = "https://openrouter.ai/api/v1/key"
CREDITS_URL = "https://openrouter.ai/api/v1/credits"


def _get(url: str, key: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8")).get("data", {})
    return data if isinstance(data, dict) else {}


def remaining_usd(record: dict[str, Any]) -> float | None:
    """min(key limit_remaining, account balance) over the available sources."""
    candidates: list[float] = []
    if record.get("limit_remaining_usd") is not None:
        candidates.append(float(record["limit_remaining_usd"]))
    if record.get("credits_total_usd") is not None and record.get("credits_used_usd") is not None:
        candidates.append(float(record["credits_total_usd"]) - float(record["credits_used_usd"]))
    return min(candidates) if candidates else None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--require-remaining-usd", type=float, default=None)
    args = ap.parse_args(argv)
    key = os.environ.get("OPENROUTER_API_KEY", "").strip().strip('"').strip("'")
    record: dict[str, Any] = {"utc": datetime.datetime.now(datetime.UTC).isoformat()}
    key_ok = False
    if not key:
        record["error"] = "OPENROUTER_API_KEY not set"
    else:
        try:
            data = _get(KEY_URL, key)
            record.update({"usage_usd": data.get("usage"), "limit_usd": data.get("limit"),
                           "limit_remaining_usd": data.get("limit_remaining"),
                           "is_free_tier": data.get("is_free_tier")})
            key_ok = True
        except Exception as exc:  # descriptive; the gate below decides
            record["error"] = f"{type(exc).__name__}: {str(exc).replace(key, '<redacted>')[:200]}"
        try:
            credits = _get(CREDITS_URL, key)
            record.update({"credits_total_usd": credits.get("total_credits"),
                           "credits_used_usd": credits.get("total_usage")})
        except Exception as exc:  # some keys may not read account credits
            record["credits_error"] = f"{type(exc).__name__}: {str(exc).replace(key, '<redacted>')[:200]}"
    rem = remaining_usd(record)
    record["remaining_usd_min_of_sources"] = rem
    code = 0
    if args.require_remaining_usd is not None:
        record["gate_required_usd"] = args.require_remaining_usd
        if not key_ok:
            record["gate"] = "UNREACHABLE_OR_KEY_REJECTED"
            code = 4
        elif rem is None:
            record["gate"] = "UNDETERMINED_NO_LIMIT_AND_NO_CREDITS_ACCESS"  # recorded; not blocking
        elif rem < args.require_remaining_usd:
            record["gate"] = "INSUFFICIENT"
            code = 2
        else:
            record["gate"] = "PASS"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=1), encoding="utf-8")
    print(f"[key-usage] {json.dumps(record)}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
