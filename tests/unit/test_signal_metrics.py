"""Signal metrics + paired task bootstrap tests (T3, ZERO API).

Synthetic TP/FP/FN verification with manually known values for P/R/F1/FNR,
candidate precision, macro ORR, and the task-paired bootstrap CI.
"""
from __future__ import annotations

import numpy as np
import pytest

from benchmark.signal.metrics import (
    candidate_precision,
    confusion,
    macro_orr,
    orr,
    p_r_f1_fnr,
    paired_bootstrap,
)


def test_confusion_basic():
    pred = {"a", "b", "c"}
    pos = {"b", "c", "d"}
    tp, fp, fn = confusion(pred, pos)
    assert (tp, fp, fn) == (2, 1, 1)


def test_p_r_f1_fnr_manual():
    # TP=6, FP=4, FN=2
    m = p_r_f1_fnr(6, 4, 2)
    assert m["tp"] == 6 and m["fp"] == 4 and m["fn"] == 2
    assert m["precision"] == 6 / 10  # 0.6
    assert m["recall"] == 6 / 8  # 0.75
    assert m["fnr"] == 2 / 8  # 0.25
    assert m["f1"] == pytest.approx(2 * 6 / (2 * 6 + 4 + 2))  # 2/3
    # FNR == 1 - Recall
    assert m["fnr"] == pytest.approx(1 - m["recall"])


def test_p_r_f1_fnr_zero_denominators():
    m = p_r_f1_fnr(0, 0, 0)
    assert (m["precision"], m["recall"], m["f1"], m["fnr"]) == (0.0, 0.0, 0.0, 0.0)
    m = p_r_f1_fnr(5, 0, 0)
    assert m["precision"] == 1.0 and m["recall"] == 1.0 and m["f1"] == 1.0 and m["fnr"] == 0.0


def test_candidate_precision():
    assert candidate_precision(3, 10) == 0.3
    assert candidate_precision(0, 0) == 0.0
    assert candidate_precision(0, 5) == 0.0


def test_orr_and_macro():
    # task with 2 missed, 1 recovered -> 0.5; task with 0 missed -> 0; task with 5 missed 5 recovered -> 1.0
    assert orr(1, 2) == 0.5
    assert orr(0, 0) == 0.0
    vals = [orr(1, 2), orr(0, 0), orr(5, 5)]
    assert macro_orr(vals) == pytest.approx((0.5 + 0.0 + 1.0) / 3)


def test_paired_bootstrap_point_estimate_is_pooled_delta():
    # 10 tasks; arm A always TP2 FP1 FN1 ; arm B TP3 FP1 FN1
    a = [(2, 1, 1)] * 10
    b = [(3, 1, 1)] * 10
    res = paired_bootstrap(a, b, "final_f1", n_resamples=200, seed=1)
    fa = 2 * 2 / (2 * 2 + 1 + 1)  # 2/3
    fb = 2 * 3 / (2 * 3 + 1 + 1)  # 3/4
    assert res["point_arm_a"] == pytest.approx(fa)
    assert res["point_arm_b"] == pytest.approx(fb)
    assert res["point_delta"] == pytest.approx(fb - fa)
    assert res["n_tasks"] == 10
    assert res["ci95_lower"] <= res["point_delta"] <= res["ci95_upper"]


def test_paired_bootstrap_deterministic_seed():
    a = [(i % 3, 1, 1) for i in range(20)]
    b = [(i % 3 + 1, 1, 1) for i in range(20)]
    r1 = paired_bootstrap(a, b, "final_recall", n_resamples=300, seed=20260919)
    r2 = paired_bootstrap(a, b, "final_recall", n_resamples=300, seed=20260919)
    assert r1 == r2
    r3 = paired_bootstrap(a, b, "final_recall", n_resamples=300, seed=20260920)
    assert r1 != r3 or abs(r1["ci95_lower"] - r3["ci95_lower"]) > 1e-12


def test_paired_bootstrap_macro_orr_unit_is_task():
    # arm A: [1.0, 0.0, 0.5], arm B: [0.5, 0.5, 0.5] -> delta should be mean of per-task deltas
    a = [(1.0,), (0.0,), (0.5,)]
    b = [(0.5,), (0.5,), (0.5,)]
    res = paired_bootstrap(a, b, "macro_orr", n_resamples=200, seed=7)
    assert res["point_delta"] == pytest.approx(np.mean([-0.5, 0.5, 0.0]))


def test_paired_bootstrap_candidate_precision_pooled():
    a = [(1, 10), (0, 0)]
    b = [(3, 10), (0, 0)]
    res = paired_bootstrap(a, b, "candidate_precision", n_resamples=200, seed=3)
    assert res["point_arm_a"] == pytest.approx(1 / 10)
    assert res["point_arm_b"] == pytest.approx(3 / 10)


def test_paired_bootstrap_requires_aligned():
    import pytest as _p

    with _p.raises(ValueError):
        paired_bootstrap([(1, 0, 0)], [(1, 0, 0), (1, 0, 0)], "final_f1")
    with _p.raises(ValueError):
        paired_bootstrap([], [], "final_f1")
