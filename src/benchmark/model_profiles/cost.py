"""Cost accounting — explicit ceiling / estimated / billed separation.

Implements the prospective cost-terminology refactor from the README/model
provider spec. Three quantities must never be conflated:

- ``budget_abort_ceiling_usd``: pre-run safety threshold (aborts before
  uncontrolled spending). NOT a scientific result.
- ``estimated_api_cost_usd``: token usage x frozen endpoint prices.
- ``provider_billed_cost_usd``: actual provider/account billing (nullable;
  only filled when an authoritative value is exposed).

Historical records keep their legacy ``api_cost`` field and remain readable
through backward-compatible parsing. This module only re-labels FUTURE
derived outputs; it never rewrites historical raw records.
"""

from __future__ import annotations

from typing import Any


def split_legacy_cost(record: dict[str, Any]) -> dict[str, Any]:
    """Backward-compatible reader for historical records.

    Reads ``api_cost`` (legacy combined estimate) and exposes the three modern
    fields with the estimate mapped to ``estimated_api_cost_usd``.
    """
    legacy = float(record.get("api_cost") or 0.0)
    return {
        "budget_abort_ceiling_usd": record.get("budget_abort_ceiling_usd"),
        "estimated_api_cost_usd": record.get("estimated_api_cost_usd", legacy),
        "provider_billed_cost_usd": record.get("provider_billed_cost_usd"),
        "pricing_snapshot": record.get("pricing_snapshot"),
        "pricing_source": record.get("pricing_source"),
        "usage_source": record.get("usage_source", "provider_reported" if record.get("usage_known") else "unknown"),
        "legacy_api_cost": legacy,
    }


def build_cost_fields(
    *,
    prompt_tokens: int,
    completion_tokens: int,
    prompt_per_token_usd: float,
    completion_per_token_usd: float,
    ceiling_usd: float | None = None,
    provider_billed_usd: float | None = None,
    pricing_source: str = "",
    usage_source: str = "provider_reported",
) -> dict[str, Any]:
    """Build the three-field cost block for a FUTURE record.

    Returns ``estimated_api_cost_usd`` (token usage x frozen prices),
    ``budget_abort_ceiling_usd`` (frozen safety ceiling), and nullable
    ``provider_billed_cost_usd``. Does NOT emit a legacy ``api_cost``; callers
    that need it can add it explicitly.
    """
    estimated = prompt_tokens * float(prompt_per_token_usd) + completion_tokens * float(completion_per_token_usd)
    return {
        "budget_abort_ceiling_usd": ceiling_usd,
        "estimated_api_cost_usd": round(estimated, 6),
        "provider_billed_cost_usd": provider_billed_usd,
        "pricing_snapshot": {
            "prompt_per_token_usd": prompt_per_token_usd,
            "completion_per_token_usd": completion_per_token_usd,
        },
        "pricing_source": pricing_source,
        "usage_source": usage_source,
    }
