"""WP-1a failure semantics + cost-quality outcome categories (pre-registered).

Primary analysis is ALL-TASKS / FAIL-CLOSED:
- strategy-level completion without selected paths -> EMPTY prediction;
- unrecoverable execution/transport failure -> EMPTY prediction in the primary
  fail-closed analysis, with a separate failure flag;
- sensitivity analysis may exclude ONLY pre-defined infrastructure failures and
  MUST be reported alongside primary, never instead of it.

Recorded per arm: empty-set rate, timeout rate, malformed-output rate,
transport-failure rate, other instrument-failure rate.

Cost-quality outcome categories (narrow hypothesis H_WP1):
H_WP1: frozen RM-CSS provides a lower-cost file-selection operating point than
the iterative repository agent without lower file-set F1 on the same main
sample. Latency is NOT a hard dominance gate unless same-machine matched
latency is available. No universal/SOTA claim regardless of result.
"""
from __future__ import annotations

FAILURE_RATE_NAMES: tuple[str, ...] = (
    "empty_set_rate",
    "timeout_rate",
    "malformed_output_rate",
    "transport_failure_rate",
    "other_instrument_failure_rate",
)

PRIMARY_ANALYSIS_RULE: str = (
    "ALL-TASKS / FAIL-CLOSED. No silent exclusions. Strategy-level completion "
    "without selected paths -> EMPTY prediction. Unrecoverable execution or "
    "transport failure -> EMPTY prediction in the primary analysis with a "
    "separate failure flag. Sensitivity analysis may exclude ONLY pre-defined "
    "infrastructure failures and must be reported alongside the primary, never "
    "instead of it."
)

INTERPRETATION_RULE: str = (
    "If RM-CSS appears better mainly because the repository-agent instrument "
    "produces many empty/failed outputs, report that as an instrument/"
    "operational finding, not pure method superiority."
)

COST_QUALITY_CATEGORIES: dict[str, dict[str, str]] = {
    "RM_CSS_COST_QUALITY_DOMINANCE": {
        "condition": (
            "RM-CSS F1 >= Agent F1 AND RM-CSS total tokens lower AND RM-CSS "
            "model calls lower AND RM-CSS USD cost lower"
        ),
        "meaning": "frozen RM-CSS dominates the repository agent on the frozen "
                   "cost-quality operating point",
    },
    "COST_QUALITY_TRADEOFF": {
        "condition": (
            "RM-CSS cheaper on the core efficiency metrics (tokens / calls / "
            "USD) BUT RM-CSS F1 < Agent F1"
        ),
        "meaning": "report the frontier/trade-off; do NOT call this superiority",
    },
    "NO_RM_CSS_EFFICIENCY_ADVANTAGE": {
        "condition": (
            "RM-CSS does not reduce the pre-registered core efficiency "
            "dimensions (total tokens, total model calls, USD cost)"
        ),
        "meaning": "no RM-CSS efficiency advantage detected",
    },
    "RM_CSS_EFFICIENCY_HYPOTHESIS_FALSIFIED": {
        "condition": (
            "RM-CSS F1 < Agent F1 OR RM-CSS fails to reduce one or more of the "
            "pre-registered core efficiency dimensions (total tokens, total "
            "model calls, USD cost)"
        ),
        "meaning": (
            "the narrow hypothesis 'lower cost without lower F1' is falsified "
            "on this main sample"
        ),
    },
}

HYPOTHESIS_H_WP1: str = (
    "H_WP1: frozen RM-CSS provides a lower-cost file-selection operating point "
    "than the iterative repository agent without lower file-set F1 on the same "
    "main sample."
)

DOMINANCE_GATE_LATENCY_RULE: str = (
    "Latency is NOT a hard dominance gate unless same-machine matched latency "
    "is available (stored SIP/RM-CSS latency is descriptive only)."
)

CLAIM_BOUNDARY: str = (
    "No universal/SOTA claim regardless of result. This is a same-protocol "
    "n=50 (main) selection-only comparison."
)
