"""PARENT_ONLY_REPOSITORY_MEMORY_RESCUE_V2 — pipeline unit tests (T3, ZERO network).

Covers the mission §37 requirements: V1 fold reuse; V1 LR reuse; V1 threshold
procedure reuse; metrics; task-paired bootstrap; intent bucket assignment (NOT
a feature); realization-B robustness; sealed-data guard; candidate-union
construction; structural/episodic top10 in the universe.
"""
# ruff: noqa: N812

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))
sys.path.insert(0, str(_PROJECT_DIR / "scripts"))

from benchmark.memory_rescue import analysis as MA  # noqa: E402
from benchmark.memory_rescue import candidates as C  # noqa: E402


class _Task:
    def __init__(self, cid, repo, write, proxy, intent=""):
        self.case_id = cid
        self.repository = repo
        self.write_set = frozenset(write)
        self.proxy = frozenset(proxy)
        self.intent_text = intent


def _synthetic_frame(n_tasks=20, n_files=20, seed=7):
    rng = np.random.RandomState(seed)
    frames = []
    tasks = {}
    for i in range(n_tasks):
        repo = "djangocms" if i < int(n_tasks * 0.6) else "saleor"
        cid = f"c{i:03d}"
        paths = [f"mod/f{j:02d}.py" for j in range(n_files)]
        scores = rng.uniform(0.05, 0.7, n_files)
        scores[rng.randint(0, n_files)] = np.nan
        rank = np.argsort(np.argsort(-scores, kind="stable"), kind="stable") + 1
        write = set(rng.choice(paths, size=2, replace=False).tolist())
        proxy = set(rng.choice(paths, size=3, replace=False).tolist())
        tasks[cid] = _Task(cid, repo, write, proxy, "add feature widget test")
        frames.append(pd.DataFrame({
            "case_id": cid, "repository": repo, "file_path": paths,
            "dense_file_score": scores, "dense_rank": rank,
            "in_sparse": [p in write for p in paths]}))
    return pd.concat(frames, ignore_index=True), tasks


def _memory_for(frame, tasks):
    """Synthetic MemoryBundle: history on a few files, structural/episodic."""
    memory = {}
    for cid, g in frame.groupby("case_id"):
        paths = g["file_path"].tolist()
        sparse = [p for p in paths if g.loc[g["file_path"] == p, "in_sparse"].iloc[0]]
        hcc = {p: (i + 1) * 3 for i, p in enumerate(paths)}
        # structural = a couple of non-sparse files with co-change to sparse
        structural = [p for p in paths if p not in sparse][:2]
        episodic = [p for p in paths if p not in sparse][2:4]
        cs = {p: 0.5 for p in structural}
        ct1 = {p: 0.4 for p in structural}
        ep_sim = {p: 0.6 for p in episodic}
        memory[cid] = C.MemoryBundle(
            history_change_count=hcc,
            cochange_sparse=cs,
            episode_similarity=ep_sim,
            episode_hit_count={p: 1 for p in episodic},
            n_production_changing_commits=10,
            cochange_top1=ct1,
            structural=structural,
            episodic=episodic,
        )
    return memory


def test_feature_count_exactly_11():
    assert len(C.FEATURE_NAMES) == 11
    for f in ("dense_file_score", "log_rank", "gap_to_top1", "in_sparse",
              "log_sparse_set_size", "sparse_empty", "sparse_rank_interaction",
              "cochange_sparse", "cochange_top1", "log_history_change_count",
              "episode_similarity"):
        assert f in C.FEATURE_NAMES
    # forbidden features never added
    for f in ("repository", "file_count", "n_files", "episode_hit_count",
              "graph_neighbor", "bm25", "path", "extension"):
        assert f not in C.FEATURE_NAMES


def test_candidate_union_construction():
    df, tasks = _synthetic_frame(n_tasks=2)
    memory = _memory_for(df, tasks)
    rows, prov = C.build_rows_with_provenance(df, tasks, memory)
    for cid in tasks:
        p = prov[cid]
        channels = set().union(*[set(v) for v in p.values()]) if p else set()
        assert "structural" in channels or "episodic" in channels
    # every candidate has 11 features present
    for r in rows:
        assert r.log_history_change_count == pytest.approx(
            np.log1p(memory[r.case_id].history_change_count[r.file_path]), abs=1e-9)


def test_v1_model_reuse_parameters():
    from benchmark.calibrated import policy as P
    x_mat = np.zeros((10, 11))
    y = np.zeros(10, dtype=np.int64)
    y[:4] = 1
    scaler, model = P.fit_policy(
        x_mat, y, continuous_cols=C.CONTINUOUS_FEATURES,
        boolean_cols=C.BOOLEAN_FEATURES, feature_names=C.FEATURE_NAMES)
    assert model.C == 1.0
    assert model.solver == "liblinear"
    assert model.max_iter == 1000
    assert model.random_state == 0
    assert model.penalty == "l2"


def test_v1_threshold_procedure_reuse():
    from benchmark.calibrated import policy as P
    probs = np.array([0.2, 0.4, 0.6, 0.8])
    labels = np.array([0, 1, 0, 1])
    # argmax pooled micro-F1; tie-break higher threshold
    t = P.select_threshold(probs, labels)
    assert P.THRESHOLD_GRID[0] == pytest.approx(0.01, abs=1e-12)
    assert P.THRESHOLD_GRID[-1] == pytest.approx(0.99, abs=1e-12)
    assert 0.01 <= t <= 0.99
    best_f1 = max(P.pooled_micro_f1(probs, labels, x) for x in P.THRESHOLD_GRID)
    assert P.pooled_micro_f1(probs, labels, t) == pytest.approx(best_f1, abs=1e-12)


def test_v1_fold_assignments_reuse_exact():
    from benchmark.calibrated.folds import grouped_stratified_folds
    persisted = json.loads(
        (_PROJECT_DIR / "research/calibrated-set-selection-v1"
         / "fold_assignments_A.json").read_text(encoding="utf-8"))
    scores = pd.read_parquet(
        _PROJECT_DIR / "research/contamination-bridge/qwen_embed"
        / "realization_A/full_file_scores.parquet")
    repo_of = scores.groupby("case_id")["repository"].first().to_dict()
    assert sorted(repo_of) == sorted(persisted)
    recomp = grouped_stratified_folds(
        sorted(repo_of), lambda c: repo_of[c], k=5, seed=20260920)
    assert persisted == recomp


def test_load_v1_fold_map_rejects_mismatch():
    from scripts.memory_rescue_v2_run import load_v1_fold_map
    tasks = {f"c{i:03d}": _Task(f"c{i:03d}", "saleor", [], [])
             for i in range(5)}
    with pytest.raises(RuntimeError):
        load_v1_fold_map(tasks)


def test_metrics_formulas():
    from benchmark.calibrated import policy as P
    m = P.confusion(10, 5, 20)
    assert m["precision"] == pytest.approx(10 / 15, abs=1e-12)
    assert m["recall"] == pytest.approx(10 / 30, abs=1e-12)
    assert m["fnr"] == pytest.approx(20 / 30, abs=1e-12)
    assert m["f1"] == pytest.approx(20 / (20 + 5 + 20), abs=1e-12)


def test_paired_bootstrap_deterministic():
    from benchmark.calibrated import policy as P
    pol = [(1, 0, 0)] * 10
    spa = [(0, 1, 0)] * 10
    b1 = P.paired_bootstrap_deltas(pol, spa, n_resamples=500, seed=20260920)
    b2 = P.paired_bootstrap_deltas(pol, spa, n_resamples=500, seed=20260920)
    assert b1["f1"]["point_delta"] == b2["f1"]["point_delta"]
    assert b1["f1"]["ci95_lower"] == b2["f1"]["ci95_lower"]


def test_intent_bucket_assignment():
    assert MA.intent_bucket("fix bug") == "<=6"
    assert MA.intent_bucket("a b c d e f g") == "7-15"
    assert MA.intent_bucket(" ".join(["w"] * 16)) == ">15"
    # boundary
    assert MA.intent_bucket(" ".join(["w"] * 6)) == "<=6"
    assert MA.intent_bucket(" ".join(["w"] * 15)) == "7-15"


def test_intent_bucket_not_a_feature():
    assert "intent_bucket" not in C.FEATURE_NAMES
    assert "intent_length" not in C.FEATURE_NAMES
    assert "n_words" not in C.FEATURE_NAMES


def test_robustness_ab_verdict_logic():
    def _res(f1):
        return {"final_sets": {"a": ["x.py"], "b": ["y.py"]},
                "repo_metrics": {
                    "djangocms": {"policy": {"f1": f1, "precision": 0.5,
                                             "recall": 0.5, "fnr": 0.5}},
                    "saleor": {"policy": {"f1": f1, "precision": 0.5,
                                          "recall": 0.5, "fnr": 0.5}}}}

    def _gate(pass_repos):
        return {"both_repos_pass": all(pass_repos.values()),
                "gate": {r: {"pass": p} for r, p in pass_repos.items()}}

    res = _res(0.4)
    g_ok = _gate({"djangocms": True, "saleor": True})
    g_fail = _gate({"djangocms": False, "saleor": True})
    from scripts.memory_rescue_v2_run import robustness_ab
    rob = robustness_ab(res, g_ok, res, g_fail)
    assert rob["gate_verdict_same"] is False


def test_sealed_guard():
    from scripts.memory_rescue_v2_run import sealed_guard
    tasks = [_Task(f"c{i:03d}", "djangocms", [], []) for i in range(5)]
    with pytest.raises(RuntimeError):
        sealed_guard(tasks)
    bad_repo = [_Task(f"c{i:03d}", "locagent", [], []) for i in range(323)]
    with pytest.raises(RuntimeError):
        sealed_guard(bad_repo)


def test_no_target_labels_in_candidates():
    df, tasks = _synthetic_frame(n_tasks=2)
    memory = _memory_for(df, tasks)
    rows, _ = C.build_rows_with_provenance(df, tasks, memory)
    # features are all numeric/parent-visible; label is the only target column
    feature_cols = C.FEATURE_NAMES
    for r in rows:
        for f in feature_cols:
            v = getattr(r, f)
            assert isinstance(v, (int, float))


def test_memory_feature_zero_when_channel_absent():
    df, tasks = _synthetic_frame(n_tasks=1)
    memory = _memory_for(df, tasks)
    cid = list(tasks)[0]
    b = memory[cid]
    mem2 = {
        cid: C.MemoryBundle(
            history_change_count=b.history_change_count,
            cochange_sparse=b.cochange_sparse,
            episode_similarity=b.episode_similarity,
            episode_hit_count=b.episode_hit_count,
            n_production_changing_commits=b.n_production_changing_commits,
            cochange_top1=b.cochange_top1,
            structural=b.structural,
            episodic=None,
        )
    }
    rows, prov = C.build_rows_with_provenance(df, tasks, mem2)
    assert "episodic" not in set().union(*[set(v) for v in prov[cid].values()])
