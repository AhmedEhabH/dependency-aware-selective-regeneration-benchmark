"""WP-2 Mission-11 E2E Smoke spec constants (B1.2).

Every value below is frozen from MISSION-11 section 3 (D30-D64). Do not change
any value without a DECISIONS.md entry and a new spec_sha256.
"""
from __future__ import annotations

import hashlib
import json

SMOKE_VERSION = "wp2-e2e-smoke-eng-v1"
SMOKE_VERSION_V2 = "wp2-e2e-smoke-eng-v2"
INTERFACE_VERSION = "wp2-e2e-interface-v2"
ARMS = ("GOLD_HARD", "RMCSS_HARD", "AGENT_HARD", "PLACEBO_HARD")

SMOKE_TASKS = [
    "saleor-rc-2d45b76a52f2",
    "saleor-rc-39b4138e8550",
    "saleor-rc-644f33094857",
    "saleor-rc-6abb53f3407b",
    "saleor-rc-74538ea00ce9",
    "saleor-rc-823b899757ab",
    "saleor-rc-82c56bde0e34",
    "saleor-rc-8f76ddc6267f",
    "saleor-rc-93b20d78c011",
    "saleor-rc-c3b9e396b07d",
    "saleor-rc-d220843b5418",
    "saleor-rc-dc6ac9d252df",
    "saleor-rc-e03ee76d2b89",
    "saleor-rc-e25cf9b4a837",
]

MODEL = "qwen/qwen3-coder"
TEMPERATURE = 0.0
TOP_P = 1.0
MAX_TOKENS = 8192
MAX_REPAIRS = 1
MAX_FILE_CHARS = 120_000
MAX_CONTEXT_CHARS = 300_000
PLACEBO_SALT = "wp2-e2e-smoke-placebo-v1"
CEILING_AGENT_USD = 1.00
CEILING_SMOKE_USD = 4.50
CEILING_TOTAL_USD = 5.50
CEILING_SMOKE_V2_USD = 2.00
REPS = 3
STATE_TIMEOUT_S = 7200

_FROZEN = {
    "smoke_version": SMOKE_VERSION,
    "arms": list(ARMS),
    "smoke_tasks": SMOKE_TASKS,
    "model": MODEL,
    "temperature": TEMPERATURE,
    "top_p": TOP_P,
    "max_tokens": MAX_TOKENS,
    "max_repairs": MAX_REPAIRS,
    "max_file_chars": MAX_FILE_CHARS,
    "max_context_chars": MAX_CONTEXT_CHARS,
    "placebo_salt": PLACEBO_SALT,
    "ceiling_agent_usd": CEILING_AGENT_USD,
    "ceiling_smoke_usd": CEILING_SMOKE_USD,
    "ceiling_total_usd": CEILING_TOTAL_USD,
    "reps": REPS,
    "state_timeout_s": STATE_TIMEOUT_S,
}


def spec_sha256() -> str:
    """SHA-256 of the sorted frozen constants JSON."""
    return hashlib.sha256(
        json.dumps(_FROZEN, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


if __name__ == "__main__":
    print(spec_sha256())
