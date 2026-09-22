"""WP-1b MAIN_297 scoring + freeze - ZERO-API tests.

Binds to research/wp1b/wp1b_decision_rules_v2.json (7 ordered verdicts, P/S,
cost verdict), research/wp1b/wp1b_ni_margin_frozen.json (Q5 rule, 10,000
resamples, seed 20260920) and the frozen scorer draws of
benchmark.wp1a.scorer.paired_bootstrap_delta_f1.
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

import pytest

from benchmark.strategies.iterative_agent import IterativeRepositoryAgentStrategy
from benchmark.wp1a.scorer import ArmConfusion, paired_bootstrap_delta_f1
from benchmark.wp1b import freeze as fz
from benchmark.wp1b import main_runner as mr
from benchmark.wp1b import main_scoring as ms
from benchmark.wp1b.resilient_backend import ResilientAccountingBackend, SpendLedger

PROJECT = Path(__file__).resolve().parents[2]
SIP_RMCSS = PROJECT / "research" / "wp1a" / "sip_rmcss_per_task_predictions.json"
PROXIES = PROJECT / "research" / "saleor-reserve-300-rmcss" / "saleor_reserve_300_proxies.json"
SIP_RECORDS = PROJECT / "research" / "saleor-reserve-300-rmcss" / "sip_300_run_records.jsonl"
EFFICIENCY = PROJECT / "research" / "saleor-reserve-300-rmcss" / "saleor_reserve_300_efficiency.json"
MAIN297 = PROJECT / "research" / "wp1b" / "wp1b_main_297_manifest.json"


def _synthetic(n: int, seed: int) -> tuple[list[ArmConfusion], list[ArmConfusion]]:
    rng = random.Random(seed)
    a = [ArmConfusion(rng.randint(0, 3), rng.randint(0, 3), rng.randint(0, 3)) for _ in range(n)]
    b = [ArmConfusion(rng.randint(0, 3), rng.randint(0, 3), rng.randint(0, 3)) for _ in range(n)]
    return a, b


def test_bootstrap_draws_identical_to_frozen_scorer() -> None:
    a, b = _synthetic(60, 7)
    ref = paired_bootstrap_delta_f1(a, b, n_resamples=2000)
    draws = ms.bootstrap_indices(60, n_resamples=2000)
    mine = ms.summarize_delta(a, b, draws)
    assert mine["q025"] == pytest.approx(ref["ci95_lower"], abs=1e-15)
    assert mine["q975"] == pytest.approx(ref["ci95_upper"], abs=1e-15)
    assert mine["point"] == pytest.approx(ref["delta_f1_point"], abs=1e-15)
    assert mine["q025"] <= mine["q05"] <= mine["q975"]


def test_authoritative_reserve300_reproduces_exactly() -> None:
    sip, rmcss = ms.load_sip_rmcss(SIP_RMCSS, SIP_RMCSS.with_suffix(".sha256"))
    labels = ms.load_opened_proxies(PROXIES)
    out = ms.verify_authoritative(sip, rmcss, labels)
    assert out["verification"] == "EXACT_REPRODUCTION_RESERVE_300"
    assert out["rmcss_f1"] == pytest.approx(0.35687263556116017, abs=1e-15)


def test_scorer_drift_detected() -> None:
    sip, rmcss = ms.load_sip_rmcss(SIP_RMCSS, SIP_RMCSS.with_suffix(".sha256"))
    labels = ms.load_opened_proxies(PROXIES)
    tampered = dict(rmcss)
    first = sorted(tampered)[0]
    tampered[first] = frozenset()
    with pytest.raises(ms.ScorerDriftError):
        ms.verify_authoritative(sip, tampered, labels)


@pytest.mark.parametrize(
    ("p", "s", "expected"),
    [
        ({"q025": 0.01, "q05": 0.02, "q975": 0.2}, {"q05": 0.0}, 1),
        ({"q025": -0.04, "q05": -0.03, "q975": -0.001}, {"q05": -0.03}, 2),
        ({"q025": -0.04, "q05": -0.03, "q975": 0.05}, {"q05": -0.03}, 3),
        ({"q025": -0.04, "q05": -0.03, "q975": 0.05}, {"q05": -0.06}, 4),
        ({"q025": -0.2, "q05": -0.18, "q975": -0.06}, {"q05": -0.2}, 5),
        ({"q025": -0.2, "q05": -0.18, "q975": -0.01}, {"q05": -0.2}, 6),
        ({"q025": -0.2, "q05": -0.18, "q975": 0.02}, {"q05": -0.2}, 7),
    ],
)
def test_quality_verdict_table(p: dict[str, float], s: dict[str, float], expected: int) -> None:
    assert ms.quality_verdict(p, s)[0] == expected


def test_final_category_mapping() -> None:
    assert ms.final_category(1, True) == "RMCSS_SUPERIOR_AT_LOWER_COST"
    assert ms.final_category(2, True) == "RMCSS_NONINFERIOR_AT_LOWER_COST"
    assert ms.final_category(3, True) == "RMCSS_NONINFERIOR_AT_LOWER_COST"
    assert ms.final_category(4, True) == "INCONCLUSIVE_QUALITY_AT_LOWER_COST"
    assert ms.final_category(7, True) == "INCONCLUSIVE_QUALITY_AT_LOWER_COST"
    assert ms.final_category(5, True) == "COST_QUALITY_TRADEOFF"
    assert ms.final_category(6, True) == "COST_QUALITY_TRADEOFF"
    assert ms.final_category(1, False) == "NO_EFFICIENCY_ADVANTAGE"


def test_cost_ratio_ci() -> None:
    draws = ms.bootstrap_indices(50, n_resamples=500)
    out = ms.cost_ratio([1.0] * 50, [4.0 + (i % 3) for i in range(50)], draws)
    assert out["ratio_point"] == pytest.approx(1.0 / (sum(4.0 + (i % 3) for i in range(50)) / 50))
    assert out["ci95_upper"] < 1.0


def _fake_freeze(ids: list[str], preds: dict[str, frozenset[str]], empty: dict[str, str]) -> ms.AgentFreeze:
    return ms.AgentFreeze(
        task_ids=tuple(ids), predictions=preds, empty_reason=empty,
        tokens={t: 70000 for t in ids}, calls={t: 6 for t in ids}, usd={t: 0.021 for t in ids}, meta={},
    )


def test_score_main_end_to_end_with_synthetic_agent() -> None:
    ids = json.loads(MAIN297.read_text(encoding="utf-8"))["task_ids"]
    sip, rmcss = ms.load_sip_rmcss(SIP_RMCSS, SIP_RMCSS.with_suffix(".sha256"))
    labels = ms.load_opened_proxies(PROXIES)
    # Agent == RM-CSS exactly -> D == 0 in every draw -> NI_SUPPORTED (not superior).
    agent = _fake_freeze(ids, {t: rmcss[t] for t in ids}, {t: "none" for t in ids})
    res = ms.score_main(agent=agent, sip=sip, rmcss=rmcss, labels=labels,
                        sip_cost=ms.load_sip_cost(SIP_RECORDS), emb=ms.load_embedding_cost(EFFICIENCY),
                        task_ids=ids, n_resamples=300)
    assert res["P_primary_fail_closed"]["point"] == 0.0
    assert res["quality_verdict"]["verdict"] == "NI_SUPPORTED"
    assert res["cheaper_view_A"] is True
    assert res["final_category"] == "RMCSS_NONINFERIOR_AT_LOWER_COST"
    assert res["S_instrument_failure_excluded"]["n_dropped"] == 0
    assert res["arms"]["RM-CSS"]["n_tasks"] == 297


def test_s_analysis_drops_only_instrument_reasons() -> None:
    ids = json.loads(MAIN297.read_text(encoding="utf-8"))["task_ids"]
    sip, rmcss = ms.load_sip_rmcss(SIP_RMCSS, SIP_RMCSS.with_suffix(".sha256"))
    labels = ms.load_opened_proxies(PROXIES)
    empty = {t: "none" for t in ids}
    preds = {t: sip[t] for t in ids}
    for t, reason in zip(ids[:4], ("truncation", "parser_failure", "infrastructure", "round_cap"), strict=True):
        empty[t] = reason
        preds[t] = frozenset()
    res = ms.score_main(agent=_fake_freeze(ids, preds, empty), sip=sip, rmcss=rmcss, labels=labels,
                        sip_cost=ms.load_sip_cost(SIP_RECORDS), emb=ms.load_embedding_cost(EFFICIENCY),
                        task_ids=ids, n_resamples=200)
    s = res["S_instrument_failure_excluded"]
    assert s["n_dropped"] == 3 and ids[3] not in s["dropped_task_ids"]
    assert res["agent_empty_by_reason"] == {"truncation": 1, "parser_failure": 1, "infrastructure": 1,
                                            "round_cap": 1}


# ---------------------------------------------------------------------------
# freeze
# ---------------------------------------------------------------------------
class _FinalInner:
    def count_prompt_tokens(self, prompt: str) -> int:
        return max(1, len(prompt) // 4)

    async def generate_structured(self, prompt: str, *, schema_name: str, schema: dict[str, Any],
                                  temperature: float = 0.0, max_tokens: int = 4096) -> Any:
        from benchmark.core.models import LLMResponse, TokenUsage
        return LLMResponse(json.dumps({"action": "final", "selected_paths": ["a/x.py"], "rationale": "r"}),
                           TokenUsage(50, 5, 55), "stop")


def _run_fake(tmp_path: Path, n: int) -> tuple[Path, list[mr.WorkItem]]:
    out = tmp_path / "run"
    out.mkdir()
    items = [mr.WorkItem(key=f"t{i}", task_id=f"t{i}", replicate=0, index=i) for i in range(n)]
    backend = ResilientAccountingBackend(_FinalInner(), ledger=SpendLedger.open(out / mr.LEDGER_FILE),
                                         ceiling_usd=1.0, sleep=lambda _s: None)
    cfg = mr.RunnerConfig(run_label="T", kind="main297", out_dir=out, ceiling_usd=1.0,
                          worst_case_usd={i.task_id: 0.001 for i in items}, items=items,
                          manifest_sha256="m", code_sha256={"c": "d"})

    def mat(bundle: mr.TaskBundle, ws: Path) -> None:
        (ws / "a").mkdir()
        (ws / "a" / "x.py").write_text("x = 1\n", encoding="utf-8")

    runner = mr.MainRunner(
        cfg, backend=backend,
        load_bundle=lambda t: mr.TaskBundle(t, "intent", "c" * 40, ("a/x.py",)),
        materialize=mat, make_strategy=lambda b: IterativeRepositoryAgentStrategy(backend=b),
        workspace_parent=tmp_path,
    )
    assert runner.run().exit_code == mr.EXIT_OK
    return out, items


def test_freeze_roundtrip_and_tamper_detection(tmp_path: Path) -> None:
    out, items = _run_fake(tmp_path, 3)
    payload = fz.build_freeze(out, items, kind="main297")
    path, digest = fz.write_freeze(out, payload)
    agent = ms.load_agent_freeze(path, out / (fz.FREEZE_FILE + ".sha256"))
    assert agent.task_ids == ("t0", "t1", "t2") and agent.predictions["t1"] == frozenset({"a/x.py"})
    assert payload["labels_used"] is False and payload["empty_count"] == 0
    path.write_text(path.read_text(encoding="utf-8").replace("a/x.py", "a/y.py"), encoding="utf-8")
    with pytest.raises(ms.FreezeIntegrityError):
        ms.load_agent_freeze(path, out / (fz.FREEZE_FILE + ".sha256"))


def test_freeze_refuses_incomplete_run(tmp_path: Path) -> None:
    out, items = _run_fake(tmp_path, 2)
    more = [*items, mr.WorkItem(key="t9", task_id="t9", replicate=0, index=2)]
    with pytest.raises(fz.FreezeError):
        fz.build_freeze(out, more, kind="main297")


def test_freeze_verifies_after_crlf_checkout(tmp_path: Path) -> None:
    """Windows checkout with text=auto may turn the LF freeze into CRLF: it must still verify."""
    out, items = _run_fake(tmp_path, 2)
    path, _ = fz.write_freeze(out, fz.build_freeze(out, items, kind="main297"))
    assert b"\r\n" not in path.read_bytes()
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    agent = ms.load_agent_freeze(path, out / (fz.FREEZE_FILE + ".sha256"))
    assert agent.task_ids == ("t0", "t1")
