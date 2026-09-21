#!/usr/bin/env python3
"""WP-1b preflight: INDEPENDENT re-derivation of every Appendix R number.

This is OpenCode's OWN re-derivation code, written from the contract
definitions (APPENDIX R of OPENCODE_CONTRACT_WP1B_PREFLIGHT_FREEZE_2026-09-21.md)
and the frozen repository artifacts. It does NOT import the external reference
evidence script (wp1b_preflight_reference_evidence.py) and does NOT copy it.

Zero API, read-only, labels = opened RESERVE-300 proxies only (786 untouched).

The script writes a single JSON agreement record to the path given as argv[1]
(or prints if omitted). It never writes into the repository working tree.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
import tempfile
from math import erf, sqrt
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(".")
_P = json.loads((R / "research/wp1a/sip_rmcss_per_task_predictions.json").read_text("utf-8"))["per_task"]
_G = json.loads((R / "research/saleor-reserve-300-rmcss/saleor_reserve_300_proxies.json").read_text("utf-8"))["proxies"]
_MAIN50 = json.loads((R / "research/wp1a/wp1_main_50_manifest.json").read_text("utf-8"))["task_ids"]
_CAL3 = json.loads((R / "research/wp1a/wp1_calibration_3_manifest.json").read_text("utf-8"))["task_ids"]
_DEP = json.loads((R / "research/stage5-v2-final/deployment_artifact.json").read_text("utf-8"))
_CR = pd.read_parquet(R / "research/saleor-reserve-300-rmcss/candidate_rows_saleor300.parquet")
_FF = pd.read_parquet(R / "research/saleor-reserve-300-rmcss/full_file_scores_saleor300.parquet",
                      columns=["case_id", "file_path"])
IDS = sorted(_P)

out: dict = {
    "artifact": "wp1b_preflight_appendix_r_rederivation",
    "api_calls": 0,
    "labels_used": "opened RESERVE-300 proxies only; 786 untouched",
    "method_note": "independent re-derivation; does not import the external reference evidence script",
}


def _comp(t: str, key: str) -> tuple[int, int, int]:
    p, g = set(_P[t][key]), set(_G[t])
    return len(p & g), len(p), len(g)


def _micro_f1(rows) -> float:
    tp = sum(r[0] for r in rows)
    s = sum(r[1] + r[2] for r in rows)
    return 2 * tp / s if s else 0.0


# ---------------- R-A pooled micro-F1 ----------------
A = {}
for name, S in (("reserve300", IDS), ("main50", _MAIN50)):
    A[name] = {
        "n": len(S),
        "sip_micro_f1": _micro_f1([_comp(t, "sip_predicted_set") for t in S]),
        "rmcss_micro_f1": _micro_f1([_comp(t, "rmcss_predicted_set") for t in S]),
    }
    A[name]["delta"] = A[name]["rmcss_micro_f1"] - A[name]["sip_micro_f1"]
out["A_pooled_f1"] = A

# ---------------- R-B RM-CSS reproduction ----------------
cont, boo = _DEP["continuous_features"], _DEP["boolean_features"]
mu = dict(zip(cont, _DEP["scaler_mean"], strict=True))
sc = dict(zip(cont, _DEP["scaler_scale"], strict=True))


def _proba(order):
    x = np.column_stack(
        [( _CR[f] - mu[f]) / sc[f] if f in cont else _CR[f].astype(float) for f in order]
    )
    return 1 / (1 + np.exp(-(x @ np.array(_DEP["lr_coef"]) + _DEP["lr_intercept"])))


def _mismatches(p):
    tmp = _CR.assign(pred=p >= _DEP["threshold"])
    return int(sum(
        set(g.loc[g.pred, "file_path"]) != set(_P[c]["rmcss_predicted_set"])
        for c, g in tmp.groupby("case_id")
    ))


out["B_rmcss_reproduction"] = {
    "mismatch_tasks_coef_order_cont_plus_boolean": _mismatches(_proba(cont + boo)),
    "mismatch_tasks_if_feature_names_order_used": _mismatches(_proba(_DEP["feature_names"])),
}
_CR["p"] = _proba(cont + boo)

# ---------------- R-C bootstrap SE + power ----------------
rng = random.Random(20260920)
B = 10000


def _boot(tasks):
    a = [_comp(t, "sip_predicted_set") for t in tasks]
    b = [_comp(t, "rmcss_predicted_set") for t in tasks]
    n = len(tasks)
    single, diff = [], []
    for _ in range(B):
        idx = [rng.randrange(n) for _ in range(n)]
        single.append(_micro_f1([b[i] for i in idx]))
        diff.append(_micro_f1([b[i] for i in idx]) - _micro_f1([a[i] for i in idx]))
    return float(np.std(single, ddof=1)), float(np.std(diff, ddof=1))


se_single50, se_diff50 = _boot(_MAIN50)
_Phi = lambda z: 0.5 * (1 + erf(z / sqrt(2)))  # noqa: E731
bounds = {
    "high_correlation(RM-vs-SIP-like)": se_diff50,
    "mid": (se_diff50 + sqrt(2) * se_single50) / 2,
    "independent_methods": sqrt(2) * se_single50,
}
power = {}
for n in (50, 150, 297):
    k = sqrt(50 / n)
    power[f"n={n}"] = {
        lab: {
            "se_diff": se * k,
            **{
                f"power_NI_margin0.05_trueD={d:+.2f}": 1 - _Phi(1.645 - (d + 0.05) / (se * k))
                for d in (-0.03, 0.0, 0.03)
            },
            "point_estimate_needed_for_LCB_above_-0.05": 1.645 * se * k - 0.05,
        }
        for lab, se in bounds.items()
    }
out["C_power"] = {
    "bootstrap_resamples": B,
    "seed": 20260920,
    "main50_se_rmcss_micro_f1": se_single50,
    "main50_se_rm_minus_sip": se_diff50,
    "table": power,
}

# ---------------- R-D budget ----------------
T = 0.3137
grp = _FF.groupby("case_id")["file_path"]
size = grp.size()
chars = grp.apply(lambda s: sum(len("  - " + p + "\n") for p in s))
TEMPLATE_CHARS = 1500


def _task_cost(t, calls=8, cap=1024, tool=2000):
    pr = sum((chars[t] + TEMPLATE_CHARS + tool * (r - 1)) * T for r in range(1, calls + 1))
    return pr, cap * calls


def _total(ids, **kw):
    p = sum(_task_cost(t, **kw)[0] for t in ids)
    c = sum(_task_cost(t, **kw)[1] for t in ids)
    return {"prompt_tokens": p, "completion_tokens": c, "usd_base": p / 1e6 * 0.30 + c / 1e6 * 1.00}


main297 = [t for t in IDS if t not in set(_CAL3)]
SALT = "wp1b-variance-substudy-v1-2026-09-21"
VAR15 = sorted(_MAIN50, key=lambda t: hashlib.sha256((SALT + t).encode("utf-8")).hexdigest())[:15]
out["D_budget"] = {
    "universe_size_mean_53": float(size[_MAIN50 + _CAL3].mean()),
    "universe_size_min_max_53": [int(size[_MAIN50 + _CAL3].min()), int(size[_MAIN50 + _CAL3].max())],
    "editable_paths_prompt_tokens_mean_53": float(chars[_MAIN50 + _CAL3].mean() * T),
    "frozen_wp1a_model": {
        "projected_prompt_tokens_53": 1729114,
        "ceiling_usd": 1.103733,
        "prompt_base_chars_est": 6000,
    },
    "worst_case_cap1024_53_tasks": _total(_MAIN50 + _CAL3),
    "worst_case_cap1024_calibration3": _total(_CAL3),
    "worst_case_cap1024_main297": _total(main297),
    "worst_case_cap1024_variance_15x3": {"usd_base": 3 * _total(VAR15)["usd_base"], "task_ids": VAR15},
}
out["D_budget"]["underestimate_factor_prompt"] = (
    out["D_budget"]["worst_case_cap1024_53_tasks"]["prompt_tokens"] / 1729114
)

# ---------------- R-E exploratory headroom ----------------
_CR["pred"] = _CR["p"] >= _DEP["threshold"]
_CR["gold"] = [int(fp in set(_G[c])) for c, fp in zip(_CR.case_id, _CR.file_path, strict=True)]
E = {}
for name, S in (("reserve300", IDS), ("main50", _MAIN50)):
    sub = _CR[_CR.case_id.isin(S)]
    gold_total = sum(len(set(_G[t])) for t in S)
    in_pool = int(sub.gold.sum())
    tp = int((sub.pred & (sub.gold == 1)).sum())
    fp = int((sub.pred & (sub.gold == 0)).sum())
    e = {
        "gold_total": gold_total,
        "gold_in_pool": in_pool,
        "pool_coverage": in_pool / gold_total,
        "pool_size_mean": float(sub.groupby("case_id").size().mean()),
        "rmcss_tp": tp,
        "rmcss_fp": fp,
        "fn_in_pool_decision_errors": in_pool - tp,
        "fn_out_of_pool_recall_errors": gold_total - in_pool,
        "rmcss_micro_f1": 2 * tp / (tp + fp + gold_total),
        "oracle_keepdrop_over_pool_f1": 2 * in_pool / (in_pool + gold_total),
        "bands": {},
    }
    for lo, hi in ((0.10, 0.35), (0.05, 0.35)):
        band = sub[(sub.p >= lo) & (sub.p < hi)]
        rest = sub[(sub.p < lo) | (sub.p >= hi)]
        tp_o = int((rest.pred & (rest.gold == 1)).sum())
        fp_o = int((rest.pred & (rest.gold == 0)).sum())
        gb, nb = int(band.gold.sum()), len(band)
        verif = {}
        for se_, sp_ in ((1.0, 1.0), (0.9, 0.9), (0.8, 0.8), (0.7, 0.7), (0.6, 0.6), (0.6, 0.9), (0.8, 0.7)):
            t_ = tp_o + se_ * gb
            f_ = fp_o + (1 - sp_) * (nb - gb)
            verif[f"sens{se_}_spec{sp_}"] = 2 * t_ / (t_ + f_ + gold_total)
        e["bands"][f"[{lo},{hi})"] = {
            "files_per_task": nb / len(S),
            "gold_in_band": gb,
            "base_rate": gb / nb if nb else None,
            "expected_micro_f1_with_verifier": verif,
        }
    E[name] = e
out["E_headroom_exploratory"] = E

_OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.gettempdir()) / "wp1b_appendix_r_rederivation.json"
_OUT.write_text(json.dumps(out, indent=1), "utf-8")
print(f"written: {_OUT}")
print(json.dumps({
    "A": A,
    "B": out["B_rmcss_reproduction"],
    "D_factor": out["D_budget"]["underestimate_factor_prompt"],
    "C_main50_se_single": se_single50,
    "C_main50_se_diff": se_diff50,
}, indent=1))
