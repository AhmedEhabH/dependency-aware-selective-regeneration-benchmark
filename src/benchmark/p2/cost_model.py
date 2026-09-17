"""P2 — measured verifier cost model.

The P2 policies trade omission recovery against verification cost. Because P2
Phase 1 runs ZERO new model calls, the cost of verifying ``B`` candidates is
ESTIMATED from the frozen confirmatory verifier calls (320 calls, djangoCMS
INTERNAL_TEST 2026-09-17). The per-B mean prompt-token counts were:

    B=1 -> 211.9  B=3 -> 226.7  B=5 -> 241.6  B=10 -> 278.5

and the least-squares fit over those 320 calls is:

    prompt_tokens(B) ~= 204.51 + 7.40*B
    api_cost(B)      ~= 0.000065 + 0.000005*B

These coefficients are FROZEN here (measured, not tuned). They are used for
relative cost accounting only; they are NOT presented as provider billing
truth.
"""
# ruff: noqa: N803
# B is the frozen protocol's verification budget symbol.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VerifierCostModel:
    """Linear measured verifier cost model: cost(B) = intercept + slope*B."""

    token_intercept: float = 204.51
    token_slope: float = 7.40
    cost_intercept: float = 0.000065
    cost_slope: float = 0.000005

    def prompt_tokens(self, B: int) -> float:
        if B <= 0:
            return 0.0
        return self.token_intercept + self.token_slope * B

    def api_cost_usd(self, B: int) -> float:
        if B <= 0:
            return 0.0
        return self.cost_intercept + self.cost_slope * B


def measured_verifier_cost_model() -> VerifierCostModel:
    """Return the frozen measured verifier cost model."""
    return VerifierCostModel()
