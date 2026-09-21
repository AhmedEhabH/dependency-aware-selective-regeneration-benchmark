"""WP-1a label-free budget feasibility model for the future WP-1b paid run.

The WP-1 draft's $2.50 ceiling is NOT automatically accepted. WP-1a computes a
label-free budget model using:
- the frozen scientific model/provider (qwen/qwen3-coder @ deepinfra/turbo,
  frozen DeepInfra-through-OpenRouter pricing $0.30/$1.00 per 1M, verified
  live 2026-09-20);
- proposed max rounds (MAX_AGENT_CALLS = 8 per task);
- agent control completion cap (512 tokens/response);
- prompt/context growth policy (accumulated tool results; per-call prompt
  growth bounded by tool output caps);
- 50 main tasks + 3 future calibration tasks;
- explicit safety factor.

Important: 3 calibration tasks cannot mathematically prove a worst case, so
WP-1b hard protection = fixed max rounds + fixed response cap + explicit
context cap/policy + cumulative USD guard checked before each paid request +
main-run ceiling frozen before main task 1.

Pre-registered abort rule:
  If the main run hits its hard ceiling before completing all 50 tasks, the
  primary WP-1b main run is BUDGET_ABORT_INVALID_FOR_PRIMARY_COMPARISON.
  Do NOT report an ordered partial n<50 table as the primary result.
"""
from __future__ import annotations

PRICING: dict[str, object] = {
    "model": "qwen/qwen3-coder",
    "provider": "deepinfra/turbo (through OpenRouter)",
    "prompt_per_1m_usd": 0.30,
    "completion_per_1m_usd": 1.00,
    "source": "frozen DeepInfra-through-OpenRouter pricing ($0.30/$1.00 per 1M); verified live 2026-09-20",
}

MAX_AGENT_CALLS_PER_TASK = 8
AGENT_CONTROL_MAX_COMPLETION_TOKENS = 512
MAIN_N = 50
CALIBRATION_N = 3
SAFETY_FACTOR_DEFAULT = 1.5

# Upper-bound context estimate per round: intent + tool schema + candidate list
# + accumulated tool results. 2000 chars/round tool output, 0.3137 tok/char
# calibrated ratio (saleor stage-5). Prompt grows linearly across 8 calls.
TOKENS_PER_CHAR = 0.3137  # calibrated ratio: tokens per character
PROMPT_BASE_CHARS_EST = 6000.0
TOOL_OUTPUT_CHARS_PER_ROUND = 2000.0


def project_agent_cost(
    *,
    main_n: int = MAIN_N,
    calibration_n: int = CALIBRATION_N,
    max_calls_per_task: int = MAX_AGENT_CALLS_PER_TASK,
    completion_cap: int = AGENT_CONTROL_MAX_COMPLETION_TOKENS,
    prompt_base_chars: float = PROMPT_BASE_CHARS_EST,
    tool_output_chars_per_round: float = TOOL_OUTPUT_CHARS_PER_ROUND,
    safety_factor: float = SAFETY_FACTOR_DEFAULT,
) -> dict[str, object]:
    # Prompt tokens: base + cumulative tool output growth across calls
    total_prompt_chars = 0.0
    for r in range(1, max_calls_per_task + 1):
        total_prompt_chars += prompt_base_chars + tool_output_chars_per_round * (r - 1)
    prompt_tokens_per_task = total_prompt_chars * TOKENS_PER_CHAR
    completion_tokens_per_task = completion_cap * max_calls_per_task

    total_tasks = main_n + calibration_n
    total_prompt_tokens = prompt_tokens_per_task * total_tasks
    total_completion_tokens = completion_tokens_per_task * total_tasks
    total_tokens = total_prompt_tokens + total_completion_tokens

    prompt_price = float(str(PRICING["prompt_per_1m_usd"]))
    completion_price = float(str(PRICING["completion_per_1m_usd"]))
    base_cost = (
        total_prompt_tokens / 1e6 * prompt_price
        + total_completion_tokens / 1e6 * completion_price
    )
    projected_with_safety = base_cost * safety_factor

    return {
        "model": str(PRICING["model"]),
        "provider": str(PRICING["provider"]),
        "pricing": PRICING,
        "main_n": main_n,
        "calibration_n": calibration_n,
        "max_calls_per_task": max_calls_per_task,
        "completion_cap": completion_cap,
        "prompt_base_chars_est": prompt_base_chars,
        "tool_output_chars_per_round_est": tool_output_chars_per_round,
        "chars_per_token_est": round(1.0 / TOKENS_PER_CHAR, 4),
        "safety_factor": safety_factor,
        "projected_prompt_tokens": round(total_prompt_tokens, 0),
        "projected_completion_tokens": round(total_completion_tokens, 0),
        "projected_total_tokens": round(total_tokens, 0),
        "projected_base_usd": round(base_cost, 6),
        "projected_with_safety_usd": round(projected_with_safety, 6),
        "recommended_ceiling_usd": round(projected_with_safety, 6),
        "calibration_cannot_prove_worst_case": True,
        "hard_protection": [
            "fixed max rounds (8 calls/task)",
            "fixed response cap (512 completion tokens/response)",
            "explicit context cap/policy",
            "cumulative USD guard checked before each paid request",
            "main-run ceiling frozen before main task 1",
        ],
        "abort_rule": (
            "If the main run hits its hard ceiling before completing all 50 "
            "tasks, the primary WP-1b main run is "
            "BUDGET_ABORT_INVALID_FOR_PRIMARY_COMPARISON. Do NOT report an "
            "ordered partial n<50 table as the primary result."
        ),
        "ceiling_status": "RECOMMENDED_FOR_AHMED_REVIEW - WP-1a spends NO money",
    }


ABORT_LABEL = "BUDGET_ABORT_INVALID_FOR_PRIMARY_COMPARISON"
