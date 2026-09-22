"""WP-1b exploratory X1-X11, variance scoring, MAIN review card, report render,
and CLI plumbing (scripts run in SUBPROCESSES because they install audit-hook
guards that must not leak into the pytest process). ZERO API."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from benchmark.wp1b import exploratory as ex
from benchmark.wp1b import freeze as fz
from benchmark.wp1b import main_scoring as ms
from benchmark.wp1b.report_render import render_latex_table, render_markdown
from benchmark.wp1b.svg_plot import Marker, Series, line_chart
from benchmark.wp1b.variance_scoring import score_variance

PROJECT = Path(__file__).resolve().parents[2]
SIP_RMCSS = PROJECT / "research" / "wp1a" / "sip_rmcss_per_task_predictions.json"
PROXIES = PROJECT / "research" / "saleor-reserve-300-rmcss" / "saleor_reserve_300_proxies.json"
MAIN297 = PROJECT / "research" / "wp1b" / "wp1b_main_297_manifest.json"
SKIP_ENV = {**os.environ, "WP1B_ALLOW_SKIP_GIT_CHECK": "1"}  # tests only


def _toy_inputs() -> ex.ExploratoryInputs:
    ids = ("t1", "t2", "t3", "t4")
    labels = {"t1": frozenset({"a"}), "t2": frozenset({"b", "c"}), "t3": frozenset({"d"}), "t4": frozenset({"e"})}
    rmcss = {"t1": frozenset({"a"}), "t2": frozenset({"b"}), "t3": frozenset(), "t4": frozenset({"x"})}
    agent = {"t1": frozenset({"a"}), "t2": frozenset({"b", "c"}), "t3": frozenset({"d"}), "t4": frozenset()}
    sip = {"t1": frozenset({"a"}), "t2": frozenset(), "t3": frozenset(), "t4": frozenset({"x"})}
    probs = {"t1": {"a": 0.9, "z": 0.05}, "t2": {"b": 0.6, "c": 0.15}, "t3": {"d": 0.12}, "t4": {"x": 0.4}}
    return ex.ExploratoryInputs(
        task_ids=ids, labels=labels, agent=agent, rmcss=rmcss, sip=sip,
        agent_usd={t: 0.02 for t in ids}, agent_tokens={t: 70000.0 for t in ids},
        agent_forced_final={"t1": False, "t2": True, "t3": True, "t4": False},
        agent_calls={"t1": 3, "t2": 8, "t3": 8, "t4": 4},
        agent_empty_reason={"t1": "none", "t2": "none", "t3": "none", "t4": "round_cap"},
        rmcss_usd={t: 0.005 for t in ids}, rmcss_tokens={t: 17000.0 for t in ids},
        candidate_prob=probs,
        dense_rank={"t1": ["a", "q"], "t2": ["c", "b"], "t3": ["d"], "t4": ["y", "e"]},
        paths_read={"t1": frozenset({"a"}), "t4": frozenset({"e"})},
        paths_surfaced={"t4": frozenset({"e"})},
        sidecar=[
            {"work_key": "t1", "call_index": 1, "action": "search_text", "query": "foo bar", "path": "",
             "search_results_returned": 0},
            {"work_key": "t1", "call_index": 2, "action": "read_file", "path": "a", "query": ""},
            {"work_key": "t1", "call_index": 3, "action": "search_text", "query": "foo bar", "path": "",
             "search_results_returned": 0},
        ],
        n_resamples=200,
    )


def test_exploratory_toy_values() -> None:
    inp = _toy_inputs()
    res = ex.run_all(inp)
    assert res["X2_recall_vs_decision_split"]["gold_files_total"] == 5
    assert res["X2_recall_vs_decision_split"]["gold_in_pool"] == 4  # e not in t4 pool
    x4 = res["X4_discovery_commitment_gap"]
    assert x4["selected"] == 4 and x4["read_but_not_selected"] == 1  # e read in t4 but not selected
    x5 = res["X5_complementarity"]
    assert x5["union"]["tp"] == 4  # a, b, c, d (t4: {x} U {} misses e)
    x11 = res["X11_tool_quality"]
    assert x11["non_consecutive_duplicate_requests"] == 1 and x11["zero_result_search_share"] == 1.0
    x9 = res["X9_budget_binding"]
    assert x9["forced_final"]["n"] == 2 and x9["calls_histogram"] == {"3": 1, "8": 2, "4": 1}
    x10 = res["X10_dense_anchor"]
    assert x10["top_1"]["tp"] == 3  # a, c, d
    x6 = res["X6_escalation_frontier"]
    assert len(x6["frontier"]["U1_REPLACE"]) == 21
    assert x6["frontier"]["U1_REPLACE"][0]["f1"] == pytest.approx(x6["rmcss_f1"])
    assert x6["preregistered_reading"] in ("ESCALATION_BETTER_THAN_RANDOM", "ESCALATION_NO_GAIN")


def test_x6_order_uses_u1_and_sip_empty_first() -> None:
    inp = _toy_inputs()
    u1 = ex.uncertainty_u1(inp)
    assert u1["t2"] == pytest.approx(0.6 * 0.4 + 0.15 * 0.85)
    order_u2 = ex.escalation_order(inp, "U2")
    assert set(order_u2[:3]) == {"t2", "t3"} | {order_u2[2]} and order_u2[-1] in ("t1", "t4")
    assert all(not inp.sip[t] for t in order_u2[:2])


def test_x3_hybrid_band_logic() -> None:
    inp = _toy_inputs()
    hyb, stats = ex._hybrid(inp, 0.10, 0.35)
    # t2: b (0.6) kept by RM-CSS rule; c (0.15) in band and agent selected it -> added
    assert hyb["t2"] == frozenset({"b", "c"})
    # t4: x (0.4) outside band, >= 0.2 -> RM-CSS keeps it
    assert hyb["t4"] == frozenset({"x"})
    assert stats["band_positive_files"] == 2  # c and d


def test_variance_scoring_toy() -> None:
    per: dict[str, Any] = {}
    for r in (1, 2, 3):
        per[f"t1#r{r}"] = {"task_id": "t1", "replicate": r, "selected_paths": ["a"] if r < 3 else ["a", "b"],
                           "prompt_tokens": 100 + r, "completion_tokens": 10, "usd_cost": 0.01,
                           "latency_s_sum": 1.0, "model_calls": 4, "empty_reason": "none",
                           "prediction_empty": False}
    res = score_variance(per, {"t1": frozenset({"a"})})
    assert res["n_runs"] == 3 and res["selected_set_exact_match_rate_pairwise"] == pytest.approx(1 / 3)
    assert res["selected_set_all_replicates_identical_rate"] == 0.0
    assert res["aggregate_pooled_f1_by_replicate"]["1"] == 1.0


def test_svg_chart_renders() -> None:
    svg = line_chart([Series("s", [(0.0, 0.3), (0.02, 0.4)])], [Marker("m", 0.01, 0.35)],
                     title="t", x_label="x", y_label="y")
    assert svg.startswith("<svg") and "polyline" in svg and "circle" in svg


def _synthetic_run_dir(tmp_path: Path) -> Path:
    """A MAIN_297-shaped freeze whose 'agent' predictions are the SIP sets."""
    ids = json.loads(MAIN297.read_text(encoding="utf-8"))["task_ids"]
    sip, _ = ms.load_sip_rmcss(SIP_RMCSS, SIP_RMCSS.with_suffix(".sha256"))
    per = {}
    for t in ids:
        paths = sorted(sip[t])
        per[t] = {"task_id": t, "replicate": 0, "selected_paths": paths,
                  "prediction_sha256": hashlib.sha256("\n".join(paths).encode()).hexdigest(),
                  "prediction_empty": not paths, "empty_reason": "none" if paths else "round_cap",
                  "infra_failure": False, "forced_final": False, "model_calls": 5, "http_attempts": 5,
                  "prompt_tokens": 60000, "completion_tokens": 300, "total_tokens": 60300, "usd_cost": 0.0183,
                  "latency_s_sum": 8.0, "wall_seconds": 12.0}
    payload = {"artifact": "wp1b_agent_predictions", "kind": "main297", "analysis_scope": "MAIN_297",
               "n": 297, "task_ids": ids, "empty_count": 0, "run_summary": {"ledger_usd": 5.4, "ceiling_usd": 21.5},
               "labels_used": False, "per_task": per}
    run = tmp_path / "run"
    run.mkdir()
    fz.write_freeze(run, payload)
    (run / "wp1b_telemetry.jsonl").write_text(
        "".join(json.dumps({"task_id": t, "work_key": t, "paths_read": [], "paths_surfaced": []}) + "\n" for t in ids),
        encoding="utf-8")
    (run / "wp1b_call_sidecar.jsonl").write_text("", encoding="utf-8")
    return run


def test_score_and_exploratory_cli_end_to_end(tmp_path: Path) -> None:
    run = _synthetic_run_dir(tmp_path)
    out_json = tmp_path / "res.json"
    cmd = [sys.executable, str(PROJECT / "scripts" / "wp1b_score_main.py"), "--run-dir", str(run),
           "--freeze-tag", "test-tag", "--out-json", str(out_json), "--out-md", str(tmp_path / "res.md"),
           "--out-tex", str(tmp_path / "t.tex"), "--skip-git-check"]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd=PROJECT, env=SKIP_ENV)
    assert out.returncode == 0, out.stdout + out.stderr
    res = json.loads(out_json.read_text(encoding="utf-8"))
    # agent == SIP -> D = RM-CSS - SIP on MAIN_297 (positive, CI excludes 0) -> SUPERIOR
    assert res["quality_verdict"]["verdict"] == "SUPERIOR"
    assert res["scorer_sanity_reserve300"]["verification"] == "EXACT_REPRODUCTION_RESERVE_300"
    assert "\\begin{table}" in (tmp_path / "t.tex").read_text(encoding="utf-8")
    cmd2 = [sys.executable, str(PROJECT / "scripts" / "wp1b_exploratory.py"), "--run-dir", str(run),
            "--primary-result", str(out_json), "--primary-tag", "t", "--out-json", str(tmp_path / "x.json"),
            "--out-md", str(tmp_path / "x.md"), "--out-svg", str(tmp_path / "f.svg"),
            "--out-paragraph", str(tmp_path / "p.tex"), "--skip-git-check"]
    out2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=900, cwd=PROJECT, env=SKIP_ENV)
    assert out2.returncode == 0, out2.stdout + out2.stderr
    x = json.loads((tmp_path / "x.json").read_text(encoding="utf-8"))
    assert x["X2_recall_vs_decision_split"]["gold_files_total"] > 0
    assert (tmp_path / "f.svg").read_text(encoding="utf-8").startswith("<svg")
    par = (tmp_path / "p.tex").read_text(encoding="utf-8")
    assert "more accurately than the budget-bounded repository agent" in par and "MAIN\\_297" in par


def test_score_cli_refuses_tampered_freeze(tmp_path: Path) -> None:
    run = _synthetic_run_dir(tmp_path)
    f = run / fz.FREEZE_FILE
    f.write_text(f.read_text(encoding="utf-8").replace('"n": 297', '"n": 296'), encoding="utf-8")
    cmd = [sys.executable, str(PROJECT / "scripts" / "wp1b_score_main.py"), "--run-dir", str(run),
           "--freeze-tag", "x", "--out-json", str(tmp_path / "r.json"), "--out-md", str(tmp_path / "r.md"),
           "--skip-git-check"]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=PROJECT, env=SKIP_ENV)
    assert out.returncode == 1 and "FREEZE INTEGRITY FAILURE" in out.stdout
    assert not (tmp_path / "r.json").exists()


def test_skip_git_check_refused_without_test_env(tmp_path: Path) -> None:
    run = _synthetic_run_dir(tmp_path)
    env = {k: v for k, v in os.environ.items() if k != "WP1B_ALLOW_SKIP_GIT_CHECK"}
    cmd = [sys.executable, str(PROJECT / "scripts" / "wp1b_score_main.py"), "--run-dir", str(run),
           "--freeze-tag", "x", "--out-json", str(tmp_path / "r.json"), "--out-md", str(tmp_path / "r.md"),
           "--skip-git-check"]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=PROJECT, env=env)
    assert out.returncode == 3 and "tests only" in out.stdout, out.stdout + out.stderr
    assert not (tmp_path / "r.json").exists()


def test_render_functions_on_minimal_result() -> None:
    arm = {"tp": 1, "fp": 1, "fn": 1, "precision": 0.5, "recall": 0.5, "f1": 0.5, "f2": 0.5, "fnr": 0.5,
           "mean_predicted_set_size": 2.0, "empty_set_rate": 0.0}
    d = {"point": 0.01, "q025": -0.02, "q05": -0.01, "q975": 0.04, "n_tasks": 10}
    c = {"ratio_point": 0.25, "ci95_lower": 0.2, "ci95_upper": 0.3, "rmcss_mean": 1.0, "agent_mean": 4.0}
    res = {"analysis": "X", "final_category": "RMCSS_NONINFERIOR_AT_LOWER_COST", "n_tasks": 10, "margin": 0.05,
           "quality_verdict": {"id": 3, "verdict": "NI_SUPPORTED", "mandatory_note": None},
           "cheaper_view_A": True, "labels": "l", "arms": {"SIP": arm, "RM-CSS": arm, "Agent": arm},
           "P_primary_fail_closed": d, "S_instrument_failure_excluded": {**d, "n_dropped": 0},
           "sensitivity_margins_not_decisive": {"0.03": "NI_SUPPORTED"},
           "cost_view_A_marginal": {"total_tokens": c, "model_calls": c, "usd": c},
           "cost_view_B_setup": {"amortized_setup_usd_per_task": 0.0001, "rmcss_view_b_usd_per_task": 0.0055},
           "rmcss_calls_per_task_view_a": 2, "agent_empty_by_reason": {},
           "descriptive": {"SIP_minus_Agent": d, "RMCSS_minus_SIP_on_this_subset": d}}
    md = render_markdown(res, freeze_tag="tag", freeze_sha256="abc", run_summary={})
    assert "NI_SUPPORTED" in md and "What this result does NOT mean" in md
    assert "NI\\_SUPPORTED" in render_latex_table(res)


def test_main_review_card_cli(tmp_path: Path) -> None:
    # build a tiny real run with the stub-driven runner, then card it in a subprocess
    from tests.unit.test_wp1b_main_scoring import _run_fake

    out, _items = _run_fake(tmp_path, 3)
    proc = subprocess.run([sys.executable, str(PROJECT / "scripts" / "wp1b_main_review_card.py"), str(out)],
                          capture_output=True, text=True, timeout=120, cwd=PROJECT)
    assert proc.returncode == 0, proc.stderr
    card = json.loads((out / "MAIN_REVIEW_CARD.json").read_text(encoding="utf-8"))
    # the fake run uses run_label "T" / model etc. from the runner constants -> no drift
    assert card["verdict"] == "NO_BLOCKING_INSTRUMENT_ANOMALIES", card["blocking"]
    assert card["items"] == "3/3"
    assert card["ledger_reconciliation_AC14"]["ok"] is True


def test_main_review_card_ac14_attempt_aware(tmp_path: Path) -> None:
    from tests.unit.test_wp1b_main_scoring import _run_fake

    out, _items = _run_fake(tmp_path, 3)
    card_cmd = [sys.executable, str(PROJECT / "scripts" / "wp1b_main_review_card.py"), str(out)]
    ledger = out / "spend_ledger.jsonl"
    # an abandoned (restarted) attempt spends money but has no kept record: still reconciles
    with ledger.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"kind": "call", "work_key": "t1", "attempt_id": "t1@s0#r0", "usd": 0.01,
                             "prompt_tokens": 10, "completion_tokens": 1, "http_attempts": 1}) + "\n")
    proc = subprocess.run(card_cmd, capture_output=True, text=True, timeout=120, cwd=PROJECT)
    card = json.loads((out / "MAIN_REVIEW_CARD.json").read_text(encoding="utf-8"))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert card["ledger_reconciliation_AC14"]["abandoned_attempts"] == 1
    # a ledger entry charged to a KEPT attempt that the record does not carry -> M6 BLOCKING, exit 1
    kept = json.loads((out / "agent_run_records.jsonl").read_text(encoding="utf-8").splitlines()[0])
    with ledger.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"kind": "call", "work_key": kept["work_key"], "attempt_id": kept["attempt_id"],
                             "usd": 0.5, "prompt_tokens": 10, "completion_tokens": 1, "http_attempts": 1}) + "\n")
    proc = subprocess.run(card_cmd, capture_output=True, text=True, timeout=120, cwd=PROJECT)
    card = json.loads((out / "MAIN_REVIEW_CARD.json").read_text(encoding="utf-8"))
    assert proc.returncode == 1 and any(b.startswith("M6") for b in card["blocking"]), proc.stdout


def test_exploratory_constants_match_prereg_addendum_v2() -> None:
    prereg = json.loads((PROJECT / "research" / "wp1b" / "wp1b_exploratory_prereg_addendum_v2.json")
                        .read_text(encoding="utf-8"))
    x6 = prereg["analyses"]["X6_confidence_escalation_frontier"]
    assert x6["operating_point"] == ex.X6_OPERATING_POINT == 0.20
    assert "2000 random escalation sets" in x6["random_null"] and ex.X6_RANDOM_SETS == 2000
    assert "20260922" in x6["random_null"] and ex.X6_RANDOM_SEED == 20260922
    assert ex.X6_TIE_SALT in x6["uncertainty_U1"]
    assert "p < 0.025" in x6["reading"] and ex.X6_ALPHA_EACH == 0.025
    assert ">= +0.02" in x6["reading"] and ex.X6_MIN_GAIN == 0.02
    assert ex.X6_FRACTIONS[0] == 0.0 and ex.X6_FRACTIONS[-1] == 1.0 and len(ex.X6_FRACTIONS) == 21
    assert "{1, 3, 5}" in prereg["analyses"]["X10_zero_generative_dense_anchor"]["definition"]
    assert ex.X10_FIXED_K == (1, 3, 5)
    old = json.loads((PROJECT / "research" / "wp1b" / "wp1b_exploratory_prereg.json").read_text(encoding="utf-8"))
    assert "[0.10, 0.35)" in old["analyses"]["X3_band_teacher_ceiling"]["description"]
    assert ex.X3_BANDS == ((0.10, 0.35), (0.05, 0.35))


def test_dry_run_check_detects_prompt_mismatch_on_fake_universe(tmp_path: Path) -> None:
    """297 real task IDs with a FAKE 3-file universe: D1/D2 pass, D3 must fail."""
    from benchmark.strategies.iterative_agent import IterativeRepositoryAgentStrategy
    from benchmark.wp1b import main_runner as mr
    from benchmark.wp1b.resilient_backend import ResilientAccountingBackend, SpendLedger

    out = tmp_path / "dry"
    out.mkdir()
    items = mr.load_main297_items(MAIN297)
    backend = ResilientAccountingBackend(mr.DryRunStubBackend(), ledger=SpendLedger.open(out / mr.LEDGER_FILE),
                                         ceiling_usd=1.0, sleep=lambda _s: None)
    cfg = mr.RunnerConfig(run_label="DRY_RUN", kind="dry_run", out_dir=out, ceiling_usd=1.0,
                          worst_case_usd={i.task_id: 0.001 for i in items}, items=items,
                          manifest_sha256="m", code_sha256={"c": "d"})

    def mat(bundle: mr.TaskBundle, ws: Path) -> None:
        (ws / "a").mkdir()
        (ws / "a" / "x.py").write_text("x = 1\n", encoding="utf-8")

    runner = mr.MainRunner(cfg, backend=backend,
                           load_bundle=lambda t: mr.TaskBundle(t, "intent", "c" * 40, ("a/x.py",)),
                           materialize=mat, make_strategy=lambda b: IterativeRepositoryAgentStrategy(backend=b),
                           workspace_parent=tmp_path)
    assert runner.run().status == "COMPLETE"
    proc = subprocess.run([sys.executable, str(PROJECT / "scripts" / "wp1b_dry_run_check.py"), str(out)],
                          capture_output=True, text=True, timeout=120, cwd=PROJECT)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    check = json.loads((out / "dry_run_check.json").read_text(encoding="utf-8"))
    assert check["verdict"] == "DRY_RUN_FAIL(D3)"
    assert check["checks"]["D1_complete"]["records"] == 297
