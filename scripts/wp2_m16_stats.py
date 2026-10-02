#!/usr/bin/env python3
"""WP2 M16 statistics and decision tokens (brain-authored). Pure Python, ZERO model API.

Everything here is a pure function of its inputs (no files, git, WSL, Docker or network),
implemented without numpy/scipy so the frozen kit runs on the plain project interpreter.

Paired 2x2 (one row per task in T*): a = both pass, b = RMCSS only, c = AGENT only, d = neither.
  delta_hat = (b - c) / n
  primary interval   : Tango (1998) asymptotic score interval for a paired difference
  sensitivity        : Newcombe (1998) method 10 (hybrid score, Wilson components, no CC)
  supporting tests   : exact conditional McNemar (two-sided) and mid-p McNemar
  single proportions : Clopper-Pearson exact
Decision fields (no winner labels): run_status, ci_position, band_position, method_agreement.
"""
from __future__ import annotations

import math
import random
from collections.abc import Sequence

Z975 = 1.959963984540054
BAND = 0.10
VERSION = "m16-stats-v1"


# ------------------------------------------------------------------ binomial helpers
def _log_comb(n: int, k: int) -> float:
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def binom_pmf(k: int, n: int, p: float) -> float:
    if k < 0 or k > n:
        return 0.0
    if p <= 0.0:
        return 1.0 if k == 0 else 0.0
    if p >= 1.0:
        return 1.0 if k == n else 0.0
    return math.exp(_log_comb(n, k) + k * math.log(p) + (n - k) * math.log1p(-p))


def binom_cdf(k: int, n: int, p: float) -> float:
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    return min(1.0, sum(binom_pmf(i, n, p) for i in range(k + 1)))


def _bisect(f, lo: float, hi: float, iters: int = 200) -> float:
    flo = f(lo)
    for _ in range(iters):
        mid = (lo + hi) / 2
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return (lo + hi) / 2


def clopper_pearson(x: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Exact two-sided CI for x/n (Clopper & Pearson 1934)."""
    if n <= 0:
        return (0.0, 1.0)
    lo = 0.0 if x == 0 else _bisect(lambda p: (1 - binom_cdf(x - 1, n, p)) - alpha / 2, 0.0, 1.0)
    hi = 1.0 if x == n else _bisect(lambda p: binom_cdf(x, n, p) - alpha / 2, 0.0, 1.0)
    return (lo, hi)


def wilson(x: int, n: int, z: float = Z975) -> tuple[float, float]:
    if n <= 0:
        return (0.0, 1.0)
    p = x / n
    den = 1 + z * z / n
    cen = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, cen - half), min(1.0, cen + half))


# ------------------------------------------------------------------ paired tests
def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact conditional McNemar: 2 * P(X <= min(b,c)), X ~ Bin(b+c, 1/2), capped."""
    m = b + c
    if m == 0:
        return 1.0
    return min(1.0, 2.0 * binom_cdf(min(b, c), m, 0.5))


def mcnemar_midp(b: int, c: int) -> float:
    """Mid-p McNemar (Fagerland, Lydersen & Laake 2013): exact p minus P(X = min(b,c))."""
    m = b + c
    if m == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2.0 * (binom_cdf(k, m, 0.5) - 0.5 * binom_pmf(k, m, 0.5)))


def _tango_stat(b: int, c: int, n: int, d0: float) -> float:
    """Tango (1998) score statistic for H0: p12 - p21 = d0 (n12 = b, n21 = c)."""
    a_ = 2.0 * n
    b_ = -b - c + (2.0 * n - b + c) * d0
    c_ = -c * d0 * (1.0 - d0)
    disc = max(0.0, b_ * b_ - 4.0 * a_ * c_)
    p21 = (-b_ + math.sqrt(disc)) / (2.0 * a_)
    p21 = min(max(p21, 0.0), 1.0)
    var = n * (2.0 * p21 + d0 * (1.0 - d0))
    num = b - c - n * d0
    if var <= 0.0:
        return 0.0 if num == 0 else math.copysign(math.inf, num)
    return num / math.sqrt(var)


def tango_ci(b: int, c: int, n: int, z: float = Z975) -> tuple[float, float]:
    """Asymptotic score interval {d0 : |T(d0)| <= z}; T is decreasing in d0 on (-1, 1)."""
    if n <= 0:
        return (-1.0, 1.0)
    eps = 1e-12
    lo_end, hi_end = -1.0 + eps, 1.0 - eps
    if _tango_stat(b, c, n, lo_end) <= z:
        lower = -1.0
    else:
        lower = _bisect(lambda d: _tango_stat(b, c, n, d) - z, lo_end, (b - c) / n)
    if _tango_stat(b, c, n, hi_end) >= -z:
        upper = 1.0
    else:
        upper = _bisect(lambda d: _tango_stat(b, c, n, d) + z, (b - c) / n, hi_end)
    return (lower, upper)


def newcombe10_ci(a: int, b: int, c: int, d: int, z: float = Z975) -> tuple[float, float]:
    """Newcombe (1998) method 10 for p1 - p2, p1 = (a+b)/n (RMCSS), p2 = (a+c)/n (AGENT)."""
    n = a + b + c + d
    if n <= 0:
        return (-1.0, 1.0)
    x1, x2 = a + b, a + c
    p1, p2 = x1 / n, x2 / n
    l1, u1 = wilson(x1, n, z)
    l2, u2 = wilson(x2, n, z)
    den = (a + b) * (c + d) * (a + c) * (b + d)
    phi = 0.0 if den == 0 else (a * d - b * c) / math.sqrt(den)
    dlt = p1 - p2
    lo = dlt - math.sqrt(max(0.0, (p1 - l1) ** 2 - 2 * phi * (p1 - l1) * (u2 - p2) + (u2 - p2) ** 2))
    hi = dlt + math.sqrt(max(0.0, (u1 - p1) ** 2 - 2 * phi * (u1 - p1) * (p2 - l2) + (p2 - l2) ** 2))
    return (max(-1.0, lo), min(1.0, hi))


# ------------------------------------------------------------------ tokens
def ci_position(lo: float, hi: float) -> str:
    if lo > 0:
        return "DIFFERENCE_CI_EXCLUDES_ZERO_POSITIVE"
    if hi < 0:
        return "DIFFERENCE_CI_EXCLUDES_ZERO_NEGATIVE"
    return "DIFFERENCE_CI_INCLUDES_ZERO"


def band_position(lo: float, hi: float, band: float = BAND) -> str:
    """Exactly one value for any lo <= hi (exhaustive, mutually exclusive; unit-tested)."""
    if hi <= -band or lo >= band:
        return "CI_OUTSIDE_BAND"
    if lo <= -band and hi >= band:
        return "CI_WIDER_THAN_BAND"
    if lo > -band and hi < band:
        return "CI_INSIDE_DESCRIPTIVE_BAND"
    return "CI_CROSSES_BAND_EDGE"


def method_agreement(tango: tuple[float, float], newcombe: tuple[float, float],
                     p_exact: float, p_mid: float, alpha: float = 0.05) -> str:
    flags = {not (tango[0] <= 0 <= tango[1]), not (newcombe[0] <= 0 <= newcombe[1]),
             p_exact < alpha, p_mid < alpha}
    return "CONCORDANT" if len(flags) == 1 else "DISCORDANT"


def run_status(*, stop_reason: str | None, n_ready: int, listwise_drop_frac: float,
               amended_frac: float, complete: bool, pool_min: int = 40,
               drop_max: float = 0.10, amended_max: float = 0.10) -> str:
    """Precedence STOP > INSTRUMENT_REVIEW > POOL_INSUFFICIENT > COMPLETE (exactly one)."""
    if stop_reason:
        return f"M16_STOP_{stop_reason}"
    if (not complete) or listwise_drop_frac > drop_max or amended_frac > amended_max:
        return "M16_INSTRUMENT_REVIEW"
    if n_ready < pool_min:
        return "M16_POOL_INSUFFICIENT_DESCRIPTIVE_ONLY"
    return "M16_OPWS_COMPLETE"


# ------------------------------------------------------------------ analyses
def paired_table(rows: Sequence[tuple[bool, bool]]) -> dict:
    a = sum(1 for r, g in rows if r and g)
    b = sum(1 for r, g in rows if r and not g)
    c = sum(1 for r, g in rows if g and not r)
    d = sum(1 for r, g in rows if not r and not g)
    return {"a_both": a, "b_rmcss_only": b, "c_agent_only": c, "d_neither": d, "n": a + b + c + d}


def paired_analysis(rows: Sequence[tuple[bool, bool]]) -> dict:
    t = paired_table(rows)
    a, b, c, d, n = t["a_both"], t["b_rmcss_only"], t["c_agent_only"], t["d_neither"], t["n"]
    if n == 0:
        return {"table": t, "n": 0, "delta_hat": None}
    tg, nw = tango_ci(b, c, n), newcombe10_ci(a, b, c, d)
    pe, pm = mcnemar_exact(b, c), mcnemar_midp(b, c)
    return {"table": t, "n": n, "delta_hat": (b - c) / n,
            "theta_rmcss": (a + b) / n, "theta_agent": (a + c) / n,
            "discordant_rate": (b + c) / n,
            "tango_95": list(tg), "newcombe10_95": list(nw),
            "mcnemar_exact_p": pe, "mcnemar_midp_p": pm,
            "ci_position": ci_position(*tg), "band_position": band_position(*tg),
            "method_agreement": method_agreement(tg, nw, pe, pm)}


def adversarial_bounds(rows: Sequence[tuple[bool, bool]], n_dropped: int) -> dict:
    """delta bounds with every dropped task imputed (RMCSS=0, AGENT=1) and (RMCSS=1, AGENT=0)."""
    lo = paired_analysis(list(rows) + [(False, True)] * n_dropped)
    hi = paired_analysis(list(rows) + [(True, False)] * n_dropped)
    return {"n_dropped": n_dropped, "delta_if_drops_favour_agent": lo.get("delta_hat"),
            "tango_if_drops_favour_agent": lo.get("tango_95"),
            "delta_if_drops_favour_rmcss": hi.get("delta_hat"),
            "tango_if_drops_favour_rmcss": hi.get("tango_95")}


def proportion(x: int, n: int) -> dict:
    lo, hi = clopper_pearson(x, n)
    return {"x": x, "n": n, "estimate": (x / n) if n else None, "cp_95": [lo, hi]}


def bootstrap_mean_diff(diffs: Sequence[float], seed: int, reps: int = 2000) -> dict:
    """Percentile bootstrap of the mean of per-task differences (descriptive only)."""
    if not diffs:
        return {"n": 0, "mean": None, "percentile_95": None}
    rng = random.Random(seed)
    n = len(diffs)
    ms = sorted(sum(diffs[rng.randrange(n)] for _ in range(n)) / n for _ in range(reps))
    return {"n": n, "mean": sum(diffs) / n, "percentile_95": [ms[int(0.025 * reps)],
                                                                ms[int(0.975 * reps) - 1]],
            "reps": reps, "seed": seed}
