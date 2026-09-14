"""Unit tests for prospective cost-accounting fields (ZERO API)."""

from __future__ import annotations

from benchmark.model_profiles.cost import build_cost_fields, split_legacy_cost


def test_legacy_api_cost_maps_to_estimated() -> None:
    record = {
        "api_cost": 0.25,
        "usage_known": True,
        "pricing_source": "frozen live endpoint pricing",
    }
    out = split_legacy_cost(record)
    assert out["estimated_api_cost_usd"] == 0.25
    assert out["provider_billed_cost_usd"] is None
    assert out["budget_abort_ceiling_usd"] is None
    assert out["legacy_api_cost"] == 0.25
    assert out["usage_source"] == "provider_reported"


def test_modern_fields_read_through() -> None:
    record = {
        "budget_abort_ceiling_usd": 1.50,
        "estimated_api_cost_usd": 0.359964,
        "provider_billed_cost_usd": None,
        "pricing_source": "endpoint_freeze.json",
        "usage_source": "provider_reported",
    }
    out = split_legacy_cost(record)
    assert out["budget_abort_ceiling_usd"] == 1.50
    assert out["estimated_api_cost_usd"] == 0.359964
    assert out["provider_billed_cost_usd"] is None


def test_build_cost_fields_separates_three_quantities() -> None:
    fields = build_cost_fields(
        prompt_tokens=1000,
        completion_tokens=500,
        prompt_per_token_usd=0.0000003,
        completion_per_token_usd=0.000001,
        ceiling_usd=1.50,
        pricing_source="frozen endpoint",
    )
    assert fields["estimated_api_cost_usd"] == 0.0008
    assert fields["budget_abort_ceiling_usd"] == 1.50
    assert fields["provider_billed_cost_usd"] is None
    assert fields["pricing_snapshot"]["prompt_per_token_usd"] == 0.0000003
    assert fields["usage_source"] == "provider_reported"


def test_provider_billed_optional_and_nullable() -> None:
    fields = build_cost_fields(
        prompt_tokens=1,
        completion_tokens=1,
        prompt_per_token_usd=0.0,
        completion_per_token_usd=0.0,
        provider_billed_usd=0.1234,
    )
    assert fields["provider_billed_cost_usd"] == 0.1234


def test_ceiling_is_not_a_scientific_result() -> None:
    # A budget ceiling is a safety threshold, never a reported cost.
    fields = build_cost_fields(
        prompt_tokens=0,
        completion_tokens=0,
        prompt_per_token_usd=0.0000003,
        completion_per_token_usd=0.000001,
        ceiling_usd=10.0,
    )
    assert fields["budget_abort_ceiling_usd"] == 10.0
    assert fields["estimated_api_cost_usd"] == 0.0
