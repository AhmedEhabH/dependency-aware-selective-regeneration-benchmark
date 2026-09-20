"""CALIBRATED_SET_SELECTION_V1 — unit tests (T3, ZERO network).

Covers the frozen components required by the mission §36:
  task grouping; repository-stratified grouped folds; train-only scaling;
  train-only model fitting; inner-OOF threshold selection; no outer-label
  threshold leakage; candidate-universe construction; absolute log-rank
  transform; repository file-count N is NOT a feature; sparse-rank
  interaction; ADD/KEEP/DROP accounting; metric formulas; paired bootstrap
  determinism; realization-B robustness; sealed-data guard; Lipton tie-break.
"""
# ruff: noqa: N802, N812

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))
sys.path.insert(0, str(_PROJECT_DIR / "scripts"))

from benchmark.calibrated import analysis as A  # noqa: E402
from benchmark.calibrated import features as F  # noqa: E402
from benchmark.calibrated import folds as Fd  # noqa: E402
from benchmark.calibrated import policy as P  # noqa: E402


class _Task:
    def __init__(self, cid, repo, write, proxy):
        self.case_id = cid
        self.repository = repo
        self.write_set = frozenset(write)
        self.proxy = frozenset(proxy)


def _synthetic_frame(n_tasks=40, n_files=25, seed=7, top=20):
    rng = np.random.RandomState(seed)
    frames = []
    tasks = {}
    for i in range(n_tasks):
        repo = "djangocms" if i < int(n_tasks * 0.6) else "saleor"
        cid = f"c{i:03d}"
        paths = [f"f{j:02d}.py" for j in range(n_files)]
        scores = rng.uniform(0.05, 0.7, n_files)
        scores[rng.randint(0, n_files)] = np.nan
        rank = np.argsort(np.argsort(-scores, kind="stable"), kind="stable") + 1
        write = set(rng.choice(paths, size=2, replace=False).tolist())
        proxy = set(rng.choice(paths, size=3, replace=False).tolist())
        tasks[cid] = _Task(cid, repo, write, proxy)
        frames.append(pd.DataFrame({
            "case_id": cid, "repository": repo, "file_path": paths,
            "dense_file_score": scores, "dense_rank": rank,
            "in_sparse": [p in write for p in paths]}))
    df = pd.concat(frames, ignore_index=True)
    return df, tasks


def test_absolute_log_rank_transform():
    # Two tasks with different universe sizes, same absolute rank -> same feature.
    r1 = F.build_rows(pd.DataFrame({
        "case_id": ["a", "a"], "repository": ["djangocms", "djangocms"],
        "file_path": ["x.py", "y.py"], "dense_file_score": [0.8, 0.5],
        "dense_rank": [1, 2], "in_sparse": [True, False]}),
        {"a": _Task("a", "djangocms", ["x.py"], ["x.py"])})
    r2 = F.build_rows(pd.DataFrame({
        "case_id": ["b", "b", "b"], "repository": ["saleor", "saleor", "saleor"],
        "file_path": ["m.py", "n.py", "o.py"], "dense_file_score": [0.8, 0.5, 0.2],
        "dense_rank": [1, 2, 3], "in_sparse": [True, False, False]}),
        {"b": _Task("b", "saleor", ["m.py"], ["m.py"])})
    lr_a = {r.file_path: r.log_rank for r in r1}
    lr_b = {r.file_path: r.log_rank for r in r2}
    assert lr_a["x.py"] == pytest.approx(np.log1p(1), abs=1e-12)
    assert lr_a["y.py"] == pytest.approx(np.log1p(2), abs=1e-12)
    assert lr_b["m.py"] == pytest.approx(np.log1p(1), abs=1e-12)
    assert lr_b["n.py"] == pytest.approx(np.log1p(2), abs=1e-12)
    assert lr_a["y.py"] == lr_b["n.py"]  # absolute rank, not normalized by N


def test_repository_file_count_N_is_not_a_feature():
    assert "repository" not in F.FEATURE_NAMES
    assert "file_count" not in F.FEATURE_NAMES
    assert "n_files" not in F.FEATURE_NAMES
    assert "norm_rank" not in F.FEATURE_NAMES
    # no feature encodes repository identity or universe size
    assert len(F.FEATURE_NAMES) == 7


def test_sparse_rank_interaction():
    df, tasks = _synthetic_frame(n_tasks=2)
    rows = F.build_rows(df, tasks)
    for r in rows:
        assert r.sparse_rank_interaction == pytest.approx(r.in_sparse * r.log_rank, abs=1e-12)


def test_candidate_universe_construction():
    df, tasks = _synthetic_frame(n_tasks=1, n_files=30, seed=3)
    tasks = {"c000": tasks["c000"]}
    df = df[df["case_id"] == "c000"]
    rows = F.build_rows(df, tasks)
    sparse_paths = set(df.loc[df["in_sparse"], "file_path"])
    top = df[~df["in_sparse"]].sort_values("dense_rank")["file_path"].head(20).tolist()
    cand = {r.file_path for r in rows}
    assert cand == set(sparse_paths) | set(top)
    assert len(rows) == len(sparse_paths) + min(20, int((~df["in_sparse"]).sum()))


def test_nan_imputation_deterministic():
    df, tasks = _synthetic_frame(n_tasks=1, n_files=10, seed=5)
    tasks = {"c000": tasks["c000"]}
    df = df[df["case_id"] == "c000"]
    floor = F.no_units_score(df)
    finite_min = float(df.loc[np.isfinite(df["dense_file_score"]), "dense_file_score"].min())
    assert floor == pytest.approx(finite_min - 1.0, abs=1e-12)
    rows = F.build_rows(df, tasks)
    for r in rows:
        assert np.isfinite(r.dense_file_score)
        assert np.isfinite(r.gap_to_top1)


def test_task_grouping_in_folds():
    df, tasks = _synthetic_frame()
    fold_map = Fd.grouped_stratified_folds(sorted(tasks), lambda c: tasks[c].repository, k=5)
    assert set(fold_map) == set(tasks)
    for _cid, f in fold_map.items():
        assert 0 <= f < 5


def test_repository_stratified_folds():
    df, tasks = _synthetic_frame(n_tasks=100)
    fold_map = Fd.grouped_stratified_folds(sorted(tasks), lambda c: tasks[c].repository, k=5)
    per_repo = {}
    for cid, f in fold_map.items():
        per_repo.setdefault(tasks[cid].repository, {}).setdefault(f, 0)
        per_repo[tasks[cid].repository][f] += 1
    for repo in ("djangocms", "saleor"):
        counts = per_repo[repo]
        assert max(counts.values()) - min(counts.values()) <= 1


def test_folds_deterministic():
    df, tasks = _synthetic_frame()
    fm1 = Fd.grouped_stratified_folds(sorted(tasks), lambda c: tasks[c].repository, k=5)
    fm2 = Fd.grouped_stratified_folds(sorted(tasks), lambda c: tasks[c].repository, k=5)
    assert fm1 == fm2


def test_train_only_scaling():
    # The scaler must reflect ONLY training-row statistics.
    x_mat = np.array([[0.0, 10.0, 1.0, 0.0, 2.0, 0.0, 1.0],
                      [1.0, 10.0, 1.0, 1.0, 2.0, 0.0, 1.0]])
    y = np.array([0, 1])
    scaler, model = P.fit_policy(x_mat, y)
    assert scaler.mean_[0] == pytest.approx(0.5, abs=1e-9)  # dense_file_score col
    assert model.classes_.tolist() == [0, 1]


def test_inner_oof_threshold_selection_and_tiebreak():
    # Known probabilities -> higher-threshold tie-break must win.
    probs = np.array([0.10, 0.11, 0.10, 0.11, 0.10])
    labels = np.array([1, 0, 1, 0, 0])
    t = P.select_threshold(probs, labels)
    # F1 identical across ties; the HIGHER threshold must be returned.
    f1s = [P.pooled_micro_f1(probs, labels, round(0.01 * i, 2)) for i in range(1, 100)]
    best = max(f1s)
    higher = max(round(0.01 * i, 2) for i in range(1, 100)
                 if abs(P.pooled_micro_f1(probs, labels, round(0.01 * i, 2)) - best) < 1e-9)
    assert t == pytest.approx(higher, abs=1e-9)


def test_no_outer_label_leakage():
    # Corrupting the labels of fold-0 HELD-OUT rows must NOT change the
    # fold-0 OOF probabilities or fold-0 final sets (those labels are used
    # only for scoring, never for fit/threshold of fold 0's model). Other
    # folds train on those tasks, so their predictions legitimately change.
    df, tasks = _synthetic_frame(n_tasks=40, seed=11)
    frame = F.rows_to_frame(F.build_rows(df, tasks))
    fold_map = Fd.grouped_stratified_folds(sorted(tasks), lambda c: tasks[c].repository, k=5)
    _, held0 = Fd.split_by_fold(fold_map, 0)
    res = A.run_nested_cv(frame, tasks, fold_map)
    frame2 = frame.copy()
    mask = frame2["case_id"].isin(held0)
    frame2.loc[mask, "label"] = 1 - frame2.loc[mask, "label"]
    res2 = A.run_nested_cv(frame2, tasks, fold_map)
    oof = {(r["case_id"], r["file_path"]): r["prob"] for r in res["oof"]}
    oof2 = {(r["case_id"], r["file_path"]): r["prob"] for r in res2["oof"]}
    held0 = set(held0)
    for k in oof:
        if k[0] in held0:
            assert oof[k] == pytest.approx(oof2[k], abs=1e-12)
    for cid in held0:
        assert res["final_sets"][cid] == res2["final_sets"][cid]


def test_nested_cv_determinism():
    df, tasks = _synthetic_frame(n_tasks=30, seed=9)
    frame = F.rows_to_frame(F.build_rows(df, tasks))
    fold_map = Fd.grouped_stratified_folds(sorted(tasks), lambda c: tasks[c].repository, k=5)
    r1 = A.run_nested_cv(frame, tasks, fold_map)
    r2 = A.run_nested_cv(frame, tasks, fold_map)
    assert r1["oof"] == r2["oof"]
    assert r1["final_sets"] == r2["final_sets"]
    assert r1["repo_metrics"] == r2["repo_metrics"]


def test_metric_formulas():
    m = P.confusion(50, 10, 20)
    assert m["precision"] == pytest.approx(50 / 60, abs=1e-9)
    assert m["recall"] == pytest.approx(50 / 70, abs=1e-9)
    assert m["fnr"] == pytest.approx(20 / 70, abs=1e-9)
    assert m["f1"] == pytest.approx(100 / (100 + 10 + 20), abs=1e-9)


def test_paired_bootstrap_determinism():
    policy = [(1, 1, 1)] * 12
    sparse = [(1, 1, 1)] * 12
    c1 = P.paired_bootstrap_deltas(policy, sparse, n_resamples=2000, seed=20260920)
    c2 = P.paired_bootstrap_deltas(policy, sparse, n_resamples=2000, seed=20260920)
    assert c1 == c2
    assert c1["f1"]["point_delta"] == pytest.approx(0.0, abs=1e-12)


def test_add_keep_drop_accounting():
    tasks = {
        "t1": _Task("t1", "djangocms", {"a.py", "b.py", "c.py"},
                    {"a.py", "x.py"}),
        "t2": _Task("t2", "djangocms", {"d.py"}, {"d.py", "e.py"}),
    }
    final_sets = {"t1": {"a.py", "x.py", "z.py"}, "t2": {"d.py"}}
    repo_of = {"t1": "djangocms", "t2": "djangocms"}
    dec, sizes = A.decompose_and_set_sizes(final_sets, tasks, repo_of, ["t1", "t2"])
    d = dec["djangocms"]
    # t1: sparse={a,b,c}, proxy={a,x}; policy={a,x,z}
    #  A: sparse TP retained = {a} & policy = a            -> 1
    #  B: sparse TP dropped = ({a}) - policy = {}          -> 0
    #  C: sparse FP dropped = ({b,c}) - policy = {b,c}     -> 2
    #  D: sparse FP retained = ({b,c}) & policy = {}       -> 0
    #  E: proxy-sparse & policy-sparse = {x} & {x,z} = {x} -> 1
    #  F: (policy-sparse) - proxy = {z}                    -> 1
    # t2: sparse={d}, proxy={d,e}; policy={d}
    #  A: {d} -> 1 ; B: 0 ; C: 0 ; D: 0 ; E: {e} & {} = 0 ; F: 0
    assert d == {"A_sparse_tp_retained": 2, "B_sparse_tp_incorrectly_dropped": 0,
                 "C_sparse_fp_correctly_dropped": 2, "D_sparse_fp_retained": 0,
                 "E_sparse_fn_correctly_added": 1, "F_new_fp_added": 1}


def test_robustness_ab():
    res_a = {"final_sets": {"t1": ["a", "b"], "t2": ["c"]},
             "repo_metrics": {"djangocms": {"policy": {"f1": 0.5}}, "saleor": {"policy": {"f1": 0.4}}}}
    res_b = {"final_sets": {"t1": ["a", "b"], "t2": ["c", "d"]},
             "repo_metrics": {"djangocms": {"policy": {"f1": 0.5}}, "saleor": {"policy": {"f1": 0.4}}}}
    ga = {"both_repos_pass": True, "gate": {"djangocms": {"pass": True}, "saleor": {"pass": True}}}
    gb = {"both_repos_pass": False, "gate": {"djangocms": {"pass": False}, "saleor": {"pass": False}}}
    from scripts.calibrated_set_selection_v1_run import robustness_ab
    out = robustness_ab(res_a, ga, res_b, gb)
    assert out["n_tasks_common"] == 2
    assert out["exact_same_selected_set_percentage"] == 50.0
    assert out["jaccard_mean"] == pytest.approx((1.0 + 0.5) / 2, abs=1e-9)
    assert out["gate_verdict_same"] is False


def test_sealed_guard():
    import scripts.calibrated_set_selection_v1_run as run_mod
    tasks = [_Task(f"c{i}", "djangocms", {"a"}, {"a"}) for i in range(174)]
    tasks += [_Task(f"s{i}", "saleor", {"a"}, {"a"}) for i in range(149)]
    run_mod.sealed_guard(tasks)  # 323 DEV -> OK
    with pytest.raises(RuntimeError):
        run_mod.sealed_guard(tasks[:-1])
    with pytest.raises(RuntimeError):
        bad = list(tasks) + [_Task("extra", "djangocms", {"a"}, {"a"})]
        run_mod.sealed_guard(bad)


def test_gate_and_pareto_evaluation():
    # A passing-config synthetic gate.
    results = {
        "repo_metrics": {
            "djangocms": {"policy": {"f1": 0.5, "recall": 0.5, "precision": 0.6, "fnr": 0.5},
                          "sparse": {"f1": 0.4, "recall": 0.4, "precision": 0.5, "fnr": 0.6}},
            "saleor": {"policy": {"f1": 0.5, "recall": 0.5, "precision": 0.6, "fnr": 0.5},
                       "sparse": {"f1": 0.4, "recall": 0.4, "precision": 0.5, "fnr": 0.6}},
        },
        "bootstrap": {
            "djangocms": {"f1": {"ci95_lower": 0.01, "ci95_upper": 0.3, "point_delta": 0.1}},
            "saleor": {"f1": {"ci95_lower": 0.01, "ci95_upper": 0.3, "point_delta": 0.1}},
        },
        "fold_deltas": {"djangocms": [0.1, 0.0, -0.1, 0.2, 0.3],
                        "saleor": [0.1, 0.1, 0.1, 0.1, 0.1]},
    }
    gate = A.evaluate_gate(results)
    assert gate["both_repos_pass"] is True
    assert gate["pareto_success"] is True
    # downgrade one repo -> fail
    results2 = json_deepcopy(results)
    results2["bootstrap"]["djangocms"]["f1"]["ci95_lower"] = -0.01
    assert A.evaluate_gate(results2)["both_repos_pass"] is False


def json_deepcopy(obj):
    import json
    return json.loads(json.dumps(obj))
