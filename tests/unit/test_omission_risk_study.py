"""Unit tests for the Omission-Risk Feature Study V1 modules."""

# ruff: noqa: E501  (synthetic record literals are intentionally long)

from __future__ import annotations

import pytest

from benchmark.harness.interfaces import PublicCase
from benchmark.omission_risk import adaptive_k, cost, labels, metrics
from benchmark.omission_risk.features import (
    _elbow_k,
    _norm_entropy,
    extract_features,
    feature_names,
)

_SYNTH_RECORDS = (
    {"path": "cms/models/pagemodel.py", "module": "cms.models", "classes": ["Page"], "functions": ["get_page"], "loc": 12, "import_count": 2},
    {"path": "cms/admin/pageadmin.py", "module": "cms.admin", "classes": ["PageAdmin"], "functions": [], "loc": 30, "import_count": 5},
    {"path": "cms/api.py", "module": "cms", "classes": [], "functions": ["render_api"], "loc": 8, "import_count": 1},
    {"path": "menus/modelmenus.py", "module": "menus", "classes": ["Menu"], "functions": [], "loc": 20, "import_count": 3},
)
_SYNTH_PATHS = tuple(r["path"] for r in _SYNTH_RECORDS)


def _synthetic_case() -> PublicCase:
    return PublicCase(
        case_id="synthetic-omission",
        repository="djangocms",
        repository_url="https://github.com/django-cms/django-cms",
        parent_commit="p" * 40,
        target_commit="t" * 40,
        intent_text="fix: page slug uniqueness check on the page model and api",
        candidate_paths=_SYNTH_PATHS,
        candidate_records=_SYNTH_RECORDS,
        graph_edges=(
            ("cms/models/pagemodel.py", "cms/admin/pageadmin.py"),
            ("cms/models/pagemodel.py", "cms/api.py"),
            ("cms/admin/pageadmin.py", "menus/modelmenus.py"),
        ),
        public_bundle_sha256="synthetic",
    )


class TestFeatureExtraction:
    def test_all_spec_features_present(self):
        feats = extract_features(_synthetic_case())
        assert set(feature_names()) == set(feats)

    def test_deterministic(self):
        c = _synthetic_case()
        assert extract_features(c) == extract_features(c)

    def test_no_gold_fields(self):
        feats = extract_features(_synthetic_case())
        assert "tp" not in feats and "fn" not in feats and "proxy" not in feats

    def test_bounded_entropy(self):
        e = _norm_entropy([3.0, 1.0, 0.5, 0.1])
        assert 0.0 <= e <= 1.0
        assert _norm_entropy([1.0, 1.0, 1.0, 1.0]) > 0.99
        assert _norm_entropy([0.0, 0.0, 0.0]) == 0.0

    def test_elbow_in_bounds(self):
        scores = [5.0, 4.9, 4.8, 0.5, 0.4, 0.1, 0.0, 0.0]
        k = _elbow_k(scores, len(scores))
        assert 1 <= k <= len(scores)


class TestLabels:
    def test_has_fn_definition(self):
        case = _synthetic_case()
        first_pass = {3: {"cms/models/pagemodel.py", "cms/api.py"}, 5: {"cms/models/pagemodel.py", "cms/api.py"}, 10: {"cms/models/pagemodel.py", "cms/api.py"}}
        proxy = ("cms/models/pagemodel.py", "cms/admin/pageadmin.py", "cms/api.py")
        lbl = labels.task_labels(case=case, first_pass_by_k=first_pass, proxy_paths=proxy)
        assert lbl["has_fn_k3"] == 1  # pageadmin.py omitted
        assert lbl["fn_count_k3"] == 1
        assert lbl["severity_k3"] == "partial"  # 1/3 < 0.5

    def test_no_fn(self):
        case = _synthetic_case()
        lbl = labels.task_labels(case=case, first_pass_by_k={3: set(_SYNTH_PATHS)}, proxy_paths=("cms/api.py",))
        assert lbl["has_fn_k3"] == 0
        assert lbl["severity_k3"] == "none"

    def test_complete_severity(self):
        case = _synthetic_case()
        lbl = labels.task_labels(
            case=case,
            first_pass_by_k={3: {"cms/api.py"}},
            proxy_paths=("cms/models/pagemodel.py", "cms/admin/pageadmin.py"),
        )
        assert lbl["fn_rate_k3"] == 1.0
        assert lbl["severity_k3"] == "complete"


class TestMetrics:
    def test_auroc_perfect_and_random(self):
        risk = [0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9]
        y = [0, 0, 0, 0, 1, 1, 1, 1]
        assert abs(metrics.auroc(risk, y) - 1.0) < 1e-9
        assert metrics.auroc([0.5] * 8, y) == 0.5  # constant risk -> 0.5

    def test_auprc_baseline(self):
        y = [0, 0, 0, 0, 1, 1, 1, 1]
        assert abs(metrics.auprc([0.5] * 8, y) - 0.5) < 1e-9

    def test_brier_perfect(self):
        y = [0, 0, 0, 0, 1, 1, 1, 1]
        p = [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0]
        assert abs(metrics.brier(p, y)) < 1e-9

    def test_recall_at_budget(self):
        risk = [0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9]
        y = [0, 0, 0, 0, 1, 1, 1, 1]
        out = metrics.recall_at_budget(risk, y, (0.5,))
        assert abs(out["recall_0.50"] - 1.0) < 1e-9

    def test_bootstrap_deterministic(self):
        risk = [0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9, 0.5, 0.55]
        y = [0, 0, 0, 0, 1, 1, 1, 1, 1, 0]
        a = metrics.bootstrap_ci(risk, y, metrics.auprc, n_resamples=100, seed=7)
        b = metrics.bootstrap_ci(risk, y, metrics.auprc, n_resamples=100, seed=7)
        assert a["ci95_low"] == b["ci95_low"] and a["ci95_high"] == b["ci95_high"]

    def test_calibration_bounds(self):
        tr_risk = [0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8]
        tr_y = [0, 0, 0, 0, 1, 1, 1]
        ev_risk = [0.15, 0.35, 0.65, 0.85]
        ev_y = [0, 0, 1, 1]
        rep = metrics.calibration_report(y_train=tr_y, risk_train=tr_risk, y_eval=ev_y, risk_eval=ev_risk, method="platt")
        assert 0.0 <= rep["brier"] <= 1.0
        assert 0.0 <= rep["ece"] <= 1.0


class TestAdaptiveK:
    def test_rules_bounded(self):
        scores = [3.0, 1.5, 0.8, 0.2, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0]
        for rule in adaptive_k.ADAPTIVE_RULES:
            k = adaptive_k.choose_k(rule, scores)
            assert 3 <= k <= 10

    def test_fixed_rules(self):
        scores = [1.0, 0.5, 0.3, 0.1]
        assert adaptive_k.choose_k("fixed_3", scores) == 3
        assert adaptive_k.choose_k("fixed_10", scores) == 10

    def test_unknown_rule(self):
        with pytest.raises(KeyError):
            adaptive_k.choose_k("nope", [1.0, 0.5])


class TestCost:
    def test_always_escalate_dominates_at_high_ratio(self):
        risk = {"t1": 0.9, "t2": 0.8, "t3": 0.7}
        prob = {"t1": 0.9, "t2": 0.8, "t3": 0.7}
        has_fn = {"t1": 1, "t2": 1, "t3": 1}
        out = cost.analyze_cost_sensitivity(
            risk_score=risk, prob_score=prob, has_fn=has_fn, fn_pos_mean=2.0, ratio_grid=(10,)
        )
        assert out["ratios"]["10"]["escalation_rate"] == 1.0
        assert out["ratios"]["10"]["n_escalated"] == 3

    def test_never_escalate_at_tiny_ratio(self):
        risk = {"t1": 0.5}
        prob = {"t1": 0.1}
        has_fn = {"t1": 1}
        out = cost.analyze_cost_sensitivity(
            risk_score=risk, prob_score=prob, has_fn=has_fn, fn_pos_mean=1.0, ratio_grid=(1,)
        )
        # 0.1 * 1 * 1.0 = 0.1 < 1 -> no escalation
        assert out["ratios"]["1"]["n_escalated"] == 0
