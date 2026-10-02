"""M16 statistics + decision tokens: reference values (scipy, computed brain-side) and invariants."""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import pytest

P = Path(__file__).resolve().parents[4]
for _p in (P, P / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts import wp2_m16_stats as S  # noqa: E402

CP_REF = [(0, 10, 0.0, 0.3084971078187607), (3, 10, 0.06673951117773447, 0.6524528500599973),
          (10, 10, 0.6915028921812392, 1.0), (17, 60, 0.17450528351437514, 0.41443606894983004),
          (40, 80, 0.38604788336490936, 0.6139521166350905)]
MCN_REF = [(5, 1, 0.21875, 0.125), (1, 5, 0.21875, 0.125), (10, 10, 1.0, 1.0),
           (12, 3, 0.03515625, 0.02127075195312501), (0, 7, 0.015625, 0.0078125)]


@pytest.mark.parametrize("x,n,lo,hi", CP_REF)
def test_clopper_pearson_matches_scipy(x, n, lo, hi):
    a, b = S.clopper_pearson(x, n)
    assert a == pytest.approx(lo, abs=1e-7) and b == pytest.approx(hi, abs=1e-7)


@pytest.mark.parametrize("b,c,pe,pm", MCN_REF)
def test_mcnemar_exact_and_midp(b, c, pe, pm):
    assert S.mcnemar_exact(b, c) == pytest.approx(pe, abs=1e-12)
    assert S.mcnemar_midp(b, c) == pytest.approx(pm, abs=1e-12)
    assert S.mcnemar_midp(b, c) <= S.mcnemar_exact(b, c)


@pytest.mark.parametrize("b,c,n", [(5, 2, 60), (8, 8, 80), (12, 3, 100), (1, 0, 40), (0, 6, 50), (0, 0, 45)])
def test_tango_bounds_solve_the_score_equation(b, c, n):
    lo, hi = S.tango_ci(b, c, n)
    assert -1.0 <= lo <= (b - c) / n <= hi <= 1.0
    for d in (lo, hi):
        if -1 < d < 1:
            assert abs(abs(S._tango_stat(b, c, n, d)) - S.Z975) < 1e-6


def test_tango_is_monotone_and_symmetric():
    lo, hi = S.tango_ci(9, 4, 70)
    lo2, hi2 = S.tango_ci(4, 9, 70)
    assert lo == pytest.approx(-hi2, abs=1e-9) and hi == pytest.approx(-lo2, abs=1e-9)
    ds = [i / 100 for i in range(-90, 91)]
    ts = [S._tango_stat(9, 4, 70, d) for d in ds]
    assert all(x >= y for x, y in zip(ts, ts[1:]))


def test_newcombe_contains_point_and_is_ordered():
    for a, b, c, d in [(20, 5, 2, 33), (10, 0, 0, 30), (0, 3, 9, 28), (40, 1, 1, 0)]:
        lo, hi = S.newcombe10_ci(a, b, c, d)
        n = a + b + c + d
        assert lo <= (b - c) / n <= hi


def test_band_position_is_exhaustive_and_exclusive():
    rng = random.Random(7)
    for _ in range(20000):
        lo, hi = sorted((rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5)))
        conds = {"CI_OUTSIDE_BAND": hi <= -0.1 or lo >= 0.1,
                 "CI_WIDER_THAN_BAND": lo <= -0.1 and hi >= 0.1,
                 "CI_INSIDE_DESCRIPTIVE_BAND": lo > -0.1 and hi < 0.1}
        conds["CI_CROSSES_BAND_EDGE"] = not any(conds.values())
        assert sum(conds.values()) == 1
        assert conds[S.band_position(lo, hi)]


def test_ci_position_and_no_winner_tokens():
    assert S.ci_position(0.01, 0.2) == "DIFFERENCE_CI_EXCLUDES_ZERO_POSITIVE"
    assert S.ci_position(-0.2, -0.01) == "DIFFERENCE_CI_EXCLUDES_ZERO_NEGATIVE"
    assert S.ci_position(-0.1, 0.1) == "DIFFERENCE_CI_INCLUDES_ZERO"
    src = (P / "scripts/wp2_m16_stats.py").read_text(encoding="utf-8")
    for bad in ("NONINFERIOR", "EQUIVALENT_WITHIN", "HIGHER_ESTIMATE", "_SUPERIOR", "MORE_SUFFICIENT"):
        assert bad not in src


def test_run_status_precedence():
    base = dict(n_ready=60, listwise_drop_frac=0.0, amended_frac=0.0, complete=True)
    assert S.run_status(stop_reason=None, **base) == "M16_OPWS_COMPLETE"
    assert S.run_status(stop_reason="GOLD_IDENTITY", **base) == "M16_STOP_GOLD_IDENTITY"
    assert S.run_status(stop_reason=None, **{**base, "n_ready": 39}) == "M16_POOL_INSUFFICIENT_DESCRIPTIVE_ONLY"
    assert S.run_status(stop_reason=None, **{**base, "n_ready": 39, "listwise_drop_frac": 0.2}) == \
        "M16_INSTRUMENT_REVIEW"
    assert S.run_status(stop_reason=None, **{**base, "amended_frac": 0.11}) == "M16_INSTRUMENT_REVIEW"
    assert S.run_status(stop_reason=None, **{**base, "complete": False}) == "M16_INSTRUMENT_REVIEW"


def test_paired_analysis_fields_and_method_agreement():
    rows = [(True, True)] * 20 + [(True, False)] * 12 + [(False, True)] * 3 + [(False, False)] * 25
    r = S.paired_analysis(rows)
    assert r["table"] == {"a_both": 20, "b_rmcss_only": 12, "c_agent_only": 3, "d_neither": 25, "n": 60}
    assert r["delta_hat"] == pytest.approx(9 / 60)
    assert r["ci_position"] == "DIFFERENCE_CI_EXCLUDES_ZERO_POSITIVE"
    assert r["method_agreement"] in ("CONCORDANT", "DISCORDANT")
    assert S.paired_analysis([])["delta_hat"] is None


def test_adversarial_bounds_bracket_the_estimate():
    rows = [(True, False)] * 5 + [(False, True)] * 3 + [(True, True)] * 30
    b = S.adversarial_bounds(rows, 4)
    assert b["delta_if_drops_favour_agent"] < S.paired_analysis(rows)["delta_hat"] < b["delta_if_drops_favour_rmcss"]


def test_bootstrap_is_deterministic():
    x = [0.1, -0.2, 0.0, 0.3, 0.05]
    assert S.bootstrap_mean_diff(x, 1) == S.bootstrap_mean_diff(x, 1)
    assert S.bootstrap_mean_diff([], 1)["mean"] is None
    assert math.isclose(S.bootstrap_mean_diff(x, 1)["mean"], sum(x) / 5)
