"""WP-1b MAIN_297 scoring - frozen decision rules v2, applied mechanically.

Inputs (all frozen before labels are touched):
* the agent prediction freeze (``wp1b_agent_predictions.json`` + ``.sha256``),
  committed and tagged BEFORE this module loads any label;
* the frozen SIP / RM-CSS per-task predictions
  (``research/wp1a/sip_rmcss_per_task_predictions.json`` + ``.sha256``);
* the ALREADY-OPENED RESERVE-300 proxies
  (``research/saleor-reserve-300-rmcss/saleor_reserve_300_proxies.json``) - the
  ONLY label source. The 786 sealed RESERVE outcomes are never read.

Statistics (``research/wp1b/wp1b_ni_margin_frozen.json`` +
``research/wp1b/wp1b_decision_rules_v2.json``):
* D = F1_pooled(RM-CSS) - F1_pooled(Agent) over identical task IDs;
* paired task bootstrap, 10,000 resamples, seed 20260920, the SAME index-draw
  algorithm as ``benchmark.wp1a.scorer.paired_bootstrap_delta_f1``;
* NI decision on Q5 (one-sided 95%), reporting CI [Q2.5, Q97.5];
* analyses P (fail-closed, all tasks) and S (drop tasks whose agent
  empty_reason is truncation / parser_failure / infrastructure from BOTH arms;
  round_cap is NOT dropped);
* the seven ordered quality verdicts (first match wins), margin 0.05; the
  0.03 / 0.10 margins are reported, not decisive;
* cost verdict: ratio RM-CSS / Agent of per-task means (tokens, calls, USD)
  with paired bootstrap CIs on the same resampling; CHEAPER iff every upper
  95% bound < 1 (View A, marginal cost).
"""
from __future__ import annotations

import hashlib
import json
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from benchmark.wp1a.rederive import AUTHORITATIVE
from benchmark.wp1a.scorer import ArmConfusion, per_task_confusion

MARGIN = 0.05
SENSITIVITY_MARGINS: tuple[float, ...] = (0.03, 0.10)
N_RESAMPLES = 10_000
SEED = 20260920
S_DROP_REASONS: frozenset[str] = frozenset({"truncation", "parser_failure", "infrastructure"})

VERDICTS: tuple[tuple[int, str], ...] = (
    (1, "SUPERIOR"),
    (2, "NI_SUPPORTED_AGENT_BETTER_WITHIN_MARGIN"),
    (3, "NI_SUPPORTED"),
    (4, "NI_NOT_ROBUST"),
    (5, "AGENT_MATERIALLY_BETTER"),
    (6, "AGENT_BETTER"),
    (7, "INCONCLUSIVE_AT_THIS_N"),
)
VERDICT_2_NOTE = (
    "RM-CSS is non-inferior within the 0.05 margin, but its F1 is statistically LOWER than the "
    "agent's (Q97.5(D) < 0). This must be stated in every summary."
)

# View A marginal RM-CSS per-task embedding cost (preregistered in the MAIN_297
# execution addendum, section 6): one query-embedding request per task, costed
# per unique query from research/saleor-reserve-300-rmcss/saleor_reserve_300_efficiency.json.
RMCSS_CALLS_PER_TASK_VIEW_A = 2  # 1 SIP coder call + 1 query-embedding request


class ScorerDriftError(RuntimeError):
    """The frozen scorer does not reproduce the authoritative RESERVE-300 values."""


class FreezeIntegrityError(RuntimeError):
    """A frozen prediction artifact does not match its recorded SHA-256."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_sha_sidecar(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip().split()[0].lower()


def line_ending_variants_sha256(data: bytes) -> set[str]:
    """SHA-256 of the raw bytes and of the LF / CRLF normalizations.

    Git (``* text=auto``) may check a JSON file out with CRLF on Windows and LF
    elsewhere; a sidecar hash written on either platform must still verify the
    same logical content.
    """
    lf = data.replace(b"\r\n", b"\n")
    crlf = lf.replace(b"\n", b"\r\n")
    return {hashlib.sha256(v).hexdigest() for v in (data, lf, crlf)}


def verify_sha_sidecar(path: Path, sidecar: Path) -> str:
    data = path.read_bytes()
    exp = _read_sha_sidecar(sidecar)
    if exp not in line_ending_variants_sha256(data):
        raise FreezeIntegrityError(f"{path.name}: sha256 {hashlib.sha256(data).hexdigest()} != sidecar {exp}")
    return exp


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class AgentFreeze:
    task_ids: tuple[str, ...]
    predictions: dict[str, frozenset[str]]
    empty_reason: dict[str, str]
    tokens: dict[str, int]
    calls: dict[str, int]
    usd: dict[str, float]
    meta: dict[str, Any]


def load_agent_freeze(path: Path, sidecar: Path) -> AgentFreeze:
    verify_sha_sidecar(path, sidecar)
    data = json.loads(path.read_text(encoding="utf-8"))
    per = data["per_task"]
    ids = tuple(str(t) for t in data["task_ids"])
    if len(set(ids)) != len(ids) or set(ids) != set(per):
        raise FreezeIntegrityError("agent freeze task_ids / per_task mismatch")
    preds: dict[str, frozenset[str]] = {}
    for tid in ids:
        entry = per[tid]
        paths = frozenset(str(p) for p in entry["selected_paths"])
        digest = hashlib.sha256("\n".join(sorted(paths)).encode("utf-8")).hexdigest()
        if digest != entry["prediction_sha256"]:
            raise FreezeIntegrityError(f"prediction hash mismatch for {tid}")
        preds[tid] = paths
    return AgentFreeze(
        task_ids=ids,
        predictions=preds,
        empty_reason={t: str(per[t]["empty_reason"]) for t in ids},
        tokens={t: int(per[t]["total_tokens"]) for t in ids},
        calls={t: int(per[t]["model_calls"]) for t in ids},
        usd={t: float(per[t]["usd_cost"]) for t in ids},
        meta={k: v for k, v in data.items() if k != "per_task"},
    )


def load_sip_rmcss(path: Path, sidecar: Path) -> tuple[dict[str, frozenset[str]], dict[str, frozenset[str]]]:
    verify_sha_sidecar(path, sidecar)
    per = json.loads(path.read_text(encoding="utf-8"))["per_task"]
    sip = {t: frozenset(v["sip_predicted_set"]) for t, v in per.items()}
    rmcss = {t: frozenset(v["rmcss_predicted_set"]) for t, v in per.items()}
    return sip, rmcss


def load_opened_proxies(path: Path) -> dict[str, frozenset[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("opened_once") is not True or int(data.get("n_tasks", 0)) != 300:
        raise ScorerDriftError("proxies artifact is not the opened-once RESERVE-300 set")
    return {t: frozenset(v) for t, v in data["proxies"].items()}


@dataclass(frozen=True)
class SipCost:
    tokens: dict[str, int]
    usd: dict[str, float]
    http_attempts: dict[str, int]


def load_sip_cost(records_path: Path) -> SipCost:
    tokens: dict[str, int] = {}
    usd: dict[str, float] = {}
    attempts: dict[str, int] = {}
    for line in records_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        cid = str(rec["case_id"])
        tokens[cid] = int(rec.get("total_tokens") or 0)
        usd[cid] = float(rec.get("api_cost") or 0.0)
        attempts[cid] = int(rec.get("transport_attempts") or 0)
    return SipCost(tokens=tokens, usd=usd, http_attempts=attempts)


@dataclass(frozen=True)
class EmbeddingCost:
    tokens_per_task: float
    usd_per_task: float
    setup_usd: float


def load_embedding_cost(efficiency_path: Path) -> EmbeddingCost:
    eff = json.loads(efficiency_path.read_text(encoding="utf-8"))["qwen_embeddings"]
    unique = max(1, int(eff["query_count_unique"]))
    return EmbeddingCost(
        tokens_per_task=float(eff["query_est_tokens"]) / unique,
        usd_per_task=float(eff["query_cost_usd"]) / unique,
        setup_usd=float(eff["unit_cost_usd"]),
    )


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
def pooled(components: Sequence[ArmConfusion]) -> dict[str, float]:
    tp = sum(c.tp for c in components)
    fp = sum(c.fp for c in components)
    fn = sum(c.fn for c in components)
    c = ArmConfusion(tp=tp, fp=fp, fn=fn)
    f2_den = 5 * tp + 4 * fn + fp
    return {
        "tp": tp, "fp": fp, "fn": fn,
        "precision": c.precision, "recall": c.recall, "fnr": c.fnr, "f1": c.f1,
        "f2": (5 * tp / f2_den) if f2_den else 0.0,
    }


def arm_metrics(pred: Mapping[str, frozenset[str]], labels: Mapping[str, frozenset[str]],
                task_ids: Sequence[str]) -> dict[str, Any]:
    comps = [per_task_confusion(set(pred.get(t, frozenset())), set(labels[t])) for t in task_ids]
    sizes = [len(pred.get(t, frozenset())) for t in task_ids]
    out: dict[str, Any] = pooled(comps)
    out.update({
        "n_tasks": len(task_ids),
        "mean_predicted_set_size": float(np.mean(sizes)) if sizes else 0.0,
        "empty_set_rate": (sum(1 for s in sizes if s == 0) / len(sizes)) if sizes else 0.0,
    })
    return out


def verify_authoritative(sip: Mapping[str, frozenset[str]], rmcss: Mapping[str, frozenset[str]],
                         labels: Mapping[str, frozenset[str]]) -> dict[str, Any]:
    ids = sorted(labels)
    s = arm_metrics(sip, labels, ids)
    r = arm_metrics(rmcss, labels, ids)
    diffs = []
    for arm, got in (("sip", s), ("rmcss", r)):
        for k in ("tp", "fp", "fn"):
            if int(got[k]) != int(AUTHORITATIVE[arm][k]):
                diffs.append(f"{arm}.{k}: {got[k]} != {AUTHORITATIVE[arm][k]}")
        if abs(float(got["f1"]) - float(AUTHORITATIVE[arm]["f1"])) > 1e-12:
            diffs.append(f"{arm}.f1: {got['f1']} != {AUTHORITATIVE[arm]['f1']}")
    if diffs:
        raise ScorerDriftError("; ".join(diffs))
    return {"verification": "EXACT_REPRODUCTION_RESERVE_300", "sip_f1": s["f1"], "rmcss_f1": r["f1"],
            "delta_f1": r["f1"] - s["f1"]}


# ---------------------------------------------------------------------------
# Bootstrap (identical draws to benchmark.wp1a.scorer.paired_bootstrap_delta_f1)
# ---------------------------------------------------------------------------
def bootstrap_indices(n: int, *, n_resamples: int = N_RESAMPLES, seed: int = SEED) -> NDArray[np.int64]:
    rng = random.Random(seed)
    draws = np.empty((n_resamples, n), dtype=np.int64)
    for b in range(n_resamples):
        draws[b] = [rng.randrange(n) for _ in range(n)]
    return draws


def _components_array(comps: Sequence[ArmConfusion]) -> NDArray[np.float64]:
    return np.array([[c.tp, c.fp, c.fn] for c in comps], dtype=np.float64).reshape(-1, 3)


def _pooled_f1_draws(arr: NDArray[np.float64], draws: NDArray[np.int64]) -> NDArray[np.float64]:
    sums = arr[draws].sum(axis=1)  # (B, 3)
    tp, fp, fn = sums[:, 0], sums[:, 1], sums[:, 2]
    den = 2 * tp + fp + fn
    return np.where(den > 0, 2 * tp / np.where(den > 0, den, 1.0), 0.0)


def delta_distribution(comp_a: Sequence[ArmConfusion], comp_b: Sequence[ArmConfusion],
                       draws: NDArray[np.int64]) -> NDArray[np.float64]:
    a = _components_array(comp_a)
    b = _components_array(comp_b)
    return _pooled_f1_draws(a, draws) - _pooled_f1_draws(b, draws)


def summarize_delta(comp_a: Sequence[ArmConfusion], comp_b: Sequence[ArmConfusion],
                    draws: NDArray[np.int64]) -> dict[str, float]:
    deltas = delta_distribution(comp_a, comp_b, draws)
    point = pooled(comp_a)["f1"] - pooled(comp_b)["f1"]
    q025, q05, q975 = np.quantile(deltas, (0.025, 0.05, 0.975))
    return {"point": float(point), "q025": float(q025), "q05": float(q05), "q975": float(q975),
            "n_tasks": len(comp_a)}


def quality_verdict(p: Mapping[str, float], s: Mapping[str, float], margin: float = MARGIN) -> tuple[int, str]:
    ni_p = p["q05"] > -margin
    ni_s = s["q05"] > -margin
    if ni_p and ni_s and p["q025"] > 0:
        return VERDICTS[0]
    if ni_p and ni_s and p["q975"] < 0:
        return VERDICTS[1]
    if ni_p and ni_s:
        return VERDICTS[2]
    if ni_p != ni_s:
        return VERDICTS[3]
    if p["q975"] < -margin:
        return VERDICTS[4]
    if p["q975"] < 0:
        return VERDICTS[5]
    return VERDICTS[6]


def cost_ratio(rm: Sequence[float], ag: Sequence[float], draws: NDArray[np.int64]) -> dict[str, float]:
    rm_a = np.asarray(rm, dtype=np.float64)
    ag_a = np.asarray(ag, dtype=np.float64)
    point = float(rm_a.mean() / ag_a.mean()) if ag_a.mean() > 0 else float("inf")
    rm_m = rm_a[draws].mean(axis=1)
    ag_m = ag_a[draws].mean(axis=1)
    ratios = np.where(ag_m > 0, rm_m / np.where(ag_m > 0, ag_m, 1.0), np.inf)
    lo, hi = np.quantile(ratios, (0.025, 0.975))
    return {"ratio_point": point, "ci95_lower": float(lo), "ci95_upper": float(hi),
            "rmcss_mean": float(rm_a.mean()), "agent_mean": float(ag_a.mean())}


def final_category(verdict_id: int, cheaper: bool) -> str:
    if not cheaper:
        return "NO_EFFICIENCY_ADVANTAGE"
    if verdict_id == 1:
        return "RMCSS_SUPERIOR_AT_LOWER_COST"
    if verdict_id in (2, 3):
        return "RMCSS_NONINFERIOR_AT_LOWER_COST"
    if verdict_id in (4, 7):
        return "INCONCLUSIVE_QUALITY_AT_LOWER_COST"
    return "COST_QUALITY_TRADEOFF"


# ---------------------------------------------------------------------------
# Main scoring
# ---------------------------------------------------------------------------
def score_main(
    *,
    agent: AgentFreeze,
    sip: Mapping[str, frozenset[str]],
    rmcss: Mapping[str, frozenset[str]],
    labels: Mapping[str, frozenset[str]],
    sip_cost: SipCost,
    emb: EmbeddingCost,
    task_ids: Sequence[str],
    analysis_label: str = "PRIMARY_MAIN_297",
    n_resamples: int = N_RESAMPLES,
) -> dict[str, Any]:
    # Bootstrap draws are index-based, so the task order is part of the result.
    # Frozen convention (benchmark.wp1a.scorer.assert_identical_task_ids): sorted IDs.
    ids = sorted(task_ids)
    if len(set(ids)) != len(ids) or not set(ids) <= set(agent.task_ids):
        raise FreezeIntegrityError("agent freeze does not cover the scored task IDs (or duplicates)")
    for arm_name, arm in (("SIP", sip), ("RM-CSS", rmcss)):
        if not set(ids) <= set(arm):
            raise FreezeIntegrityError(f"{arm_name} predictions do not cover the scored task IDs")
    if not set(ids) <= set(labels):
        raise FreezeIntegrityError("opened proxies do not cover the scored task IDs")

    def comps(pred: Mapping[str, frozenset[str]], sub: Sequence[str]) -> list[ArmConfusion]:
        return [per_task_confusion(set(pred[t]), set(labels[t])) for t in sub]

    draws_p = bootstrap_indices(len(ids), n_resamples=n_resamples)
    d_p = summarize_delta(comps(rmcss, ids), comps(agent.predictions, ids), draws_p)
    s_ids = [t for t in ids if agent.empty_reason[t] not in S_DROP_REASONS]
    dropped = [t for t in ids if t not in set(s_ids)]
    draws_s = draws_p if len(s_ids) == len(ids) else bootstrap_indices(len(s_ids), n_resamples=n_resamples)
    d_s = summarize_delta(comps(rmcss, s_ids), comps(agent.predictions, s_ids), draws_s)

    vid, verdict = quality_verdict(d_p, d_s, MARGIN)
    sensitivity = {f"{m:.2f}": quality_verdict(d_p, d_s, m)[1] for m in SENSITIVITY_MARGINS}

    d_sip_agent = summarize_delta(comps(sip, ids), comps(agent.predictions, ids), draws_p)
    d_rm_sip = summarize_delta(comps(rmcss, ids), comps(sip, ids), draws_p)

    rm_tokens = [sip_cost.tokens[t] + emb.tokens_per_task for t in ids]
    rm_calls = [float(RMCSS_CALLS_PER_TASK_VIEW_A)] * len(ids)
    rm_usd = [sip_cost.usd[t] + emb.usd_per_task for t in ids]
    ag_tokens = [float(agent.tokens[t]) for t in ids]
    ag_calls = [float(agent.calls[t]) for t in ids]
    ag_usd = [agent.usd[t] for t in ids]
    cost = {
        "total_tokens": cost_ratio(rm_tokens, ag_tokens, draws_p),
        "model_calls": cost_ratio(rm_calls, ag_calls, draws_p),
        "usd": cost_ratio(rm_usd, ag_usd, draws_p),
    }
    cheaper = all(v["ci95_upper"] < 1.0 for v in cost.values())
    sens_calls = {
        "coder_calls_only": cost_ratio([1.0] * len(ids), ag_calls, draws_p),
        "generative_tokens_only": cost_ratio([float(sip_cost.tokens[t]) for t in ids], ag_tokens, draws_p),
    }
    view_b_setup_per_task = emb.setup_usd / len(ids) if ids else 0.0

    empty_counts: dict[str, int] = {}
    for t in ids:
        r = agent.empty_reason[t]
        if r != "none":
            empty_counts[r] = empty_counts.get(r, 0) + 1

    result: dict[str, Any] = {
        "artifact": "wp1b_main_result",
        "analysis": analysis_label,
        "n_tasks": len(ids),
        "task_order_for_bootstrap": "sorted task IDs (wp1a convention)",
        "statistic": "D = F1_pooled(RM-CSS) - F1_pooled(Agent)",
        "margin": MARGIN,
        "bootstrap": {"n_resamples": n_resamples, "seed": SEED, "unit": "task (paired)"},
        "arms": {
            "Agent": arm_metrics(agent.predictions, labels, ids),
            "SIP": arm_metrics(sip, labels, ids),
            "RM-CSS": arm_metrics(rmcss, labels, ids),
        },
        "P_primary_fail_closed": d_p,
        "S_instrument_failure_excluded": {**d_s, "dropped_task_ids": dropped, "n_dropped": len(dropped)},
        "quality_verdict": {"id": vid, "verdict": verdict,
                            "mandatory_note": VERDICT_2_NOTE if vid == 2 else None},
        "sensitivity_margins_not_decisive": sensitivity,
        "descriptive": {
            "SIP_minus_Agent": d_sip_agent,
            "RMCSS_minus_SIP_on_this_subset": d_rm_sip,
        },
        "agent_empty_by_reason": empty_counts,
        "cost_view_A_marginal": cost,
        "cheaper_view_A": cheaper,
        "cost_sensitivity_not_decisive": sens_calls,
        "cost_view_B_setup": {
            "embedding_corpus_build_usd": emb.setup_usd,
            "repository_memory_build_usd": 0.0,
            "amortized_setup_usd_per_task": view_b_setup_per_task,
            "rmcss_view_b_usd_per_task": float(np.mean(rm_usd)) + view_b_setup_per_task,
        },
        "final_category": final_category(vid, cheaper),
        "rmcss_calls_per_task_view_a": RMCSS_CALLS_PER_TASK_VIEW_A,
        "labels": "opened RESERVE-300 proxies only; 786 sealed outcomes untouched",
        "dominance_word_retired": True,
    }
    return result
