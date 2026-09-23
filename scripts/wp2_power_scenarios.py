#!/usr/bin/env python3
"""WP-2 zero-API power / assay-sensitivity scenarios (deterministic, fixed seed).

Computes, from the confirmed oracle pool (primary behavioral F2P eligible n)
and plausible effect sizes, the expected paired-binary power and single-arm
confidence-interval widths. Uses exact binomial enumeration / a small fixed-seed
simulation. Does NOT choose a final NI margin or final Research Run n.

Output: research/wp2/wp2_power_scenarios_2026-09-22.json
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
RUN_DIR = _PROJECT_DIR / "research" / "wp2" / "oracle_confirmation_2026-09-22"
OUT = _PROJECT_DIR / "research" / "wp2" / "wp2_power_scenarios_2026-09-22.json"
SEED = 20260922

EFFECT_SIZES_PP = (5, 10, 15, 20)


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (centre - half, centre + half)


def paired_binary_power(n: int, effect_pp: float, n_sim: int = 20000) -> float:
    """Simulated one-sided paired (McNemar-style) power for a true difference.

    effect_pp: true difference in resolved rate (as a proportion, e.g. 0.10).
    Deterministic simulation with a fixed seed.
    """
    rng = random.Random(SEED)
    power_n = 0
    for _ in range(n_sim):
        p_base = 0.3
        p_b = min(1.0, p_base + effect_pp)
        d_plus = 0  # discordant pairs favoring B
        d_minus = 0  # discordant pairs favoring A
        for _i in range(n):
            a = rng.random() < p_base
            b = rng.random() < p_b
            if a and not b:
                d_minus += 1
            elif b and not a:
                d_plus += 1
        d = d_plus + d_minus
        stat = 0.0 if d == 0 else (d_plus - d_minus) / math.sqrt(d)
        if stat > 1.645:
            power_n += 1
    return power_n / n_sim


def main() -> int:
    summary = json.loads((RUN_DIR / "summary.json").read_text(encoding="utf-8"))
    n_behavioral = summary["f2p_pools"]["primary_behavioral_eligible"]
    n_extended = summary["f2p_pools"]["extended_f2p_eligible"]
    n_env_valid = summary["substrata"]["environment_valid"]

    paired = {}
    for epp in EFFECT_SIZES_PP:
        power = paired_binary_power(n=n_behavioral, effect_pp=epp / 100.0)
        paired[f"{epp}pp"] = {"true_difference_pp": epp, "n": n_behavioral, "power": round(power, 4)}

    # single-arm resolved-proportion CI widths across feasible n
    resolved_rates = (0.3, 0.5, 0.7)
    single_arm = {}
    for n in (n_behavioral, n_extended, n_env_valid, 60, 100):
        if n <= 0:
            continue
        single_arm[str(n)] = {}
        for rate in resolved_rates:
            k = int(round(rate * n))
            lo, hi = wilson_ci(k, n)
            single_arm[str(n)][f"{rate:.1f}"] = {
                "k": k, "ci": [round(lo, 4), round(hi, 4)],
                "width": round(hi - lo, 4),
            }

    payload = {
        "artifact": "wp2_power_scenarios",
        "date": "2026-09-22",
        "seed": SEED,
        "no_final_margin_chosen": True,
        "no_final_research_n_chosen": True,
        "decision": (
            f"WP2_F2P_POOL_SMALL (primary behavioral n={n_behavioral} < 60 after exhausting "
            "all 220 changed-test candidates)"
        ),
        "options_without_execution": [
            "estimation-first RQ with confidence intervals (report single-arm resolved "
            "proportion + CI rather than powered comparisons)",
            f"extended F2P including symbol-absence as secondary (n={n_extended})",
            "new prospective mining outside the sealed 786 (never open the reserve)",
            "cross-repository expansion (e.g. djangoCMS/e2e-capable repo) to grow the confirmed pool",
        ],
        "confirmed_pool": {
            "primary_behavioral_f2p": n_behavioral,
            "extended_f2p": n_extended,
            "environment_valid": n_env_valid,
        },
        "paired_power_effect_sizes": paired,
        "single_arm_ci_widths": single_arm,
        "interpretation": [
            f"with n={n_behavioral}, even a 20pp true difference has limited paired power; "
            "the confirmed pool is too small for a powered selector comparison",
            f"a single-arm estimation-first design with CI reporting is feasible at n={n_behavioral}",
            "Pilot must first demonstrate assay sensitivity (Gold vs Placebo) before "
            "any selector comparison, per Design v1 section 6.6",
        ],
    }
    OUT.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
