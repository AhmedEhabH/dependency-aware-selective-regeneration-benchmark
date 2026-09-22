"""WP-1b exploratory analyses X1-X11 (computed ONLY after the primary result is frozen).

X1-X5: ``research/wp1b/wp1b_exploratory_prereg.json`` (2026-09-21).
X6-X11: ``research/wp1b/wp1b_exploratory_prereg_addendum_v2.json`` (2026-09-22),
frozen BEFORE any MAIN_297 agent output existed.

None of these analyses can change the primary WP-1b verdict, the calibration
gate, sample membership or any scientific knob. All are zero-API.
"""
from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from benchmark.wp1a.scorer import ArmConfusion, per_task_confusion
from benchmark.wp1b.main_scoring import bootstrap_indices, pooled

Sets = Mapping[str, frozenset[str]]

X3_BANDS: tuple[tuple[float, float], ...] = ((0.10, 0.35), (0.05, 0.35))
RMCSS_THRESHOLD = 0.20
X6_FRACTIONS: tuple[float, ...] = tuple(round(0.05 * i, 2) for i in range(21))
X6_OPERATING_POINT = 0.20
X6_RANDOM_SETS = 2000
X6_RANDOM_SEED = 20260922
X6_TIE_SALT = "wp1b-x6-v1-2026-09-22"
X6_MIN_GAIN = 0.02
X6_ALPHA_EACH = 0.025  # Holm-style split across the two U1 policies (REPLACE, UNION)
X10_FIXED_K: tuple[int, ...] = (1, 3, 5)


@dataclass(frozen=True)
class ExploratoryInputs:
    task_ids: tuple[str, ...]
    labels: Sets
    agent: Sets
    rmcss: Sets
    sip: Sets
    agent_usd: Mapping[str, float]
    agent_tokens: Mapping[str, float]
    agent_forced_final: Mapping[str, bool]
    agent_calls: Mapping[str, int]
    agent_empty_reason: Mapping[str, str]
    rmcss_usd: Mapping[str, float]
    rmcss_tokens: Mapping[str, float]
    candidate_prob: Mapping[str, Mapping[str, float]]  # task -> file -> RM-CSS probability
    dense_rank: Mapping[str, Sequence[str]]  # task -> files ordered by dense score (desc)
    paths_read: Mapping[str, frozenset[str]]
    paths_surfaced: Mapping[str, frozenset[str]]
    sidecar: Sequence[Mapping[str, Any]]
    n_resamples: int = 10_000


def _comps(pred: Sets, labels: Sets, ids: Sequence[str]) -> list[ArmConfusion]:
    return [per_task_confusion(set(pred.get(t, frozenset())), set(labels[t])) for t in ids]


def _arr(comps: Sequence[ArmConfusion]) -> NDArray[np.float64]:
    return np.array([[c.tp, c.fp, c.fn] for c in comps], dtype=np.float64).reshape(-1, 3)


def _f1_of_sums(sums: NDArray[np.float64]) -> NDArray[np.float64]:
    tp, fp, fn = sums[..., 0], sums[..., 1], sums[..., 2]
    den = 2 * tp + fp + fn
    return np.where(den > 0, 2 * tp / np.where(den > 0, den, 1.0), 0.0)


def _delta_ci(a: Sequence[ArmConfusion], b: Sequence[ArmConfusion], draws: NDArray[np.int64]) -> dict[str, float]:
    aa, bb = _arr(a), _arr(b)
    d = _f1_of_sums(aa[draws].sum(axis=1)) - _f1_of_sums(bb[draws].sum(axis=1))
    q025, q05, q975 = np.quantile(d, (0.025, 0.05, 0.975))
    return {"point": pooled(a)["f1"] - pooled(b)["f1"], "q025": float(q025), "q05": float(q05),
            "q975": float(q975), "n_tasks": len(a)}


def _per_task_f1(pred: frozenset[str], gold: frozenset[str]) -> float:
    return per_task_confusion(set(pred), set(gold)).f1


# ---------------------------------------------------------------------------
# X1 secondary metrics + macro per-task F1 difference
# ---------------------------------------------------------------------------
def x1_secondary(inp: ExploratoryInputs, draws: NDArray[np.int64]) -> dict[str, Any]:
    ids = list(inp.task_ids)
    out: dict[str, Any] = {}
    for name, arm in (("Agent", inp.agent), ("RM-CSS", inp.rmcss), ("SIP", inp.sip)):
        m = pooled(_comps(arm, inp.labels, ids))
        sizes = [len(arm[t]) for t in ids]
        out[name] = {**m, "mean_set_size": float(np.mean(sizes)),
                     "empty_rate": sum(1 for s in sizes if s == 0) / len(ids)}
    macro_rm = np.array([_per_task_f1(inp.rmcss[t], inp.labels[t]) for t in ids])
    macro_ag = np.array([_per_task_f1(inp.agent[t], inp.labels[t]) for t in ids])
    diff = macro_rm - macro_ag
    boot = diff[draws].mean(axis=1)
    out["macro_f1_RMCSS_minus_Agent"] = {
        "point": float(diff.mean()), "q025": float(np.quantile(boot, 0.025)), "q975": float(np.quantile(boot, 0.975)),
        "rmcss_macro_f1": float(macro_rm.mean()), "agent_macro_f1": float(macro_ag.mean()),
    }
    return out


# ---------------------------------------------------------------------------
# X2 agent recall inside vs outside the RM-CSS candidate pool
# ---------------------------------------------------------------------------
def x2_pool_split(inp: ExploratoryInputs) -> dict[str, Any]:
    inside_tot = inside_hit = outside_tot = outside_hit = 0
    rm_inside_miss = 0
    for t in inp.task_ids:
        pool = set(inp.candidate_prob.get(t, {}))
        for g in inp.labels[t]:
            hit = g in inp.agent[t]
            if g in pool:
                inside_tot += 1
                inside_hit += int(hit)
                rm_inside_miss += int(g not in inp.rmcss[t])
            else:
                outside_tot += 1
                outside_hit += int(hit)
    total = inside_tot + outside_tot
    return {
        "gold_files_total": total,
        "gold_in_pool": inside_tot,
        "gold_in_pool_rate": inside_tot / total if total else 0.0,
        "agent_recall_inside_pool": inside_hit / inside_tot if inside_tot else 0.0,
        "agent_recall_outside_pool": outside_hit / outside_tot if outside_tot else 0.0,
        "agent_hits_outside_pool": outside_hit,
        "rmcss_misses_inside_pool": rm_inside_miss,
        "note": "RM-CSS can never select a file outside its candidate pool; outside-pool agent hits are "
                "recall RM-CSS structurally cannot reach.",
    }


# ---------------------------------------------------------------------------
# X3 band teacher ceiling
# ---------------------------------------------------------------------------
def _hybrid(inp: ExploratoryInputs, lo: float, hi: float) -> tuple[dict[str, frozenset[str]], dict[str, float]]:
    out: dict[str, frozenset[str]] = {}
    tp_band = fn_band = tn_band = fp_band = 0
    for t in inp.task_ids:
        probs = inp.candidate_prob.get(t, {})
        chosen = set()
        for f, p in probs.items():
            if lo <= p < hi:
                sel = f in inp.agent[t]
                gold = f in inp.labels[t]
                tp_band += int(sel and gold)
                fn_band += int((not sel) and gold)
                fp_band += int(sel and not gold)
                tn_band += int((not sel) and not gold)
                if sel:
                    chosen.add(f)
            elif p >= RMCSS_THRESHOLD:
                chosen.add(f)
        out[t] = frozenset(chosen)
    stats = {
        "band_positive_files": tp_band + fn_band,
        "band_negative_files": fp_band + tn_band,
        "agent_sensitivity_on_band": tp_band / (tp_band + fn_band) if (tp_band + fn_band) else 0.0,
        "agent_specificity_on_band": tn_band / (tn_band + fp_band) if (tn_band + fp_band) else 0.0,
    }
    return out, stats


def x3_band_teacher(inp: ExploratoryInputs, draws: NDArray[np.int64]) -> dict[str, Any]:
    ids = list(inp.task_ids)
    base = _comps(inp.rmcss, inp.labels, ids)
    out: dict[str, Any] = {}
    for lo, hi in X3_BANDS:
        hyb, stats = _hybrid(inp, lo, hi)
        d = _delta_ci(_comps(hyb, inp.labels, ids), base, draws)
        key = f"[{lo:.2f},{hi:.2f})"
        out[key] = {"hybrid_minus_rmcss": d, **stats}
    primary = out["[0.10,0.35)"]["hybrid_minus_rmcss"]
    out["preregistered_reading"] = (
        "DISTILLATION_HEADROOM_PRESENT" if (primary["q05"] > 0 and primary["point"] >= 0.03)
        else "NO_TEACHER_HEADROOM"
    )
    return out


# ---------------------------------------------------------------------------
# X4 discovery-commitment gap
# ---------------------------------------------------------------------------
def x4_discovery_gap(inp: ExploratoryInputs) -> dict[str, Any]:
    selected = read_not_sel = surfaced_only = never = 0
    for t in inp.task_ids:
        read = inp.paths_read.get(t, frozenset())
        surf = inp.paths_surfaced.get(t, frozenset())
        for g in inp.labels[t]:
            if g in inp.agent[t]:
                selected += 1
            elif g in read:
                read_not_sel += 1
            elif g in surf:
                surfaced_only += 1
            else:
                never += 1
    total = selected + read_not_sel + surfaced_only + never
    return {
        "gold_files_total": total,
        "selected": selected,
        "read_but_not_selected": read_not_sel,
        "surfaced_not_read_not_selected": surfaced_only,
        "never_seen_by_agent_tools": never,
        "share_read_not_selected": read_not_sel / total if total else 0.0,
        "share_surfaced_not_selected": (read_not_sel + surfaced_only) / total if total else 0.0,
        "note": "The editable-path list in the prompt exposes every path name; 'never seen' means never "
                "surfaced by a tool, not never visible as a name.",
    }


# ---------------------------------------------------------------------------
# X5 complementarity
# ---------------------------------------------------------------------------
def x5_complementarity(inp: ExploratoryInputs, draws: NDArray[np.int64]) -> dict[str, Any]:
    ids = list(inp.task_ids)
    union = {t: inp.rmcss[t] | inp.agent[t] for t in ids}
    inter = {t: inp.rmcss[t] & inp.agent[t] for t in ids}
    base = _comps(inp.rmcss, inp.labels, ids)
    return {
        "union": {**pooled(_comps(union, inp.labels, ids)),
                  "minus_rmcss": _delta_ci(_comps(union, inp.labels, ids), base, draws)},
        "intersection": {**pooled(_comps(inter, inp.labels, ids)),
                         "minus_rmcss": _delta_ci(_comps(inter, inp.labels, ids), base, draws)},
    }


# ---------------------------------------------------------------------------
# X6 confidence-based escalation frontier (task-level cascade RM-CSS -> Agent)
# ---------------------------------------------------------------------------
def _tie(t: str) -> str:
    return hashlib.sha256((X6_TIE_SALT + t).encode("utf-8")).hexdigest()


def uncertainty_u1(inp: ExploratoryInputs) -> dict[str, float]:
    return {t: float(sum(p * (1.0 - p) for p in inp.candidate_prob.get(t, {}).values())) for t in inp.task_ids}


def escalation_order(inp: ExploratoryInputs, signal: str) -> list[str]:
    u1 = uncertainty_u1(inp)
    if signal == "U1":
        return sorted(inp.task_ids, key=lambda t: (-u1[t], _tie(t)))
    if signal == "U2":
        return sorted(inp.task_ids, key=lambda t: (0 if not inp.sip[t] else 1, -u1[t], _tie(t)))
    raise ValueError(signal)


def _policy_sets(inp: ExploratoryInputs, escalated: set[str], policy: str) -> dict[str, frozenset[str]]:
    out: dict[str, frozenset[str]] = {}
    for t in inp.task_ids:
        if t in escalated:
            out[t] = inp.agent[t] if policy == "REPLACE" else (inp.rmcss[t] | inp.agent[t])
        else:
            out[t] = inp.rmcss[t]
    return out


def _pooled_f1(pred: Sets, inp: ExploratoryInputs) -> float:
    return pooled(_comps(pred, inp.labels, inp.task_ids))["f1"]


def x6_escalation(inp: ExploratoryInputs, draws: NDArray[np.int64]) -> dict[str, Any]:
    ids = list(inp.task_ids)
    n = len(ids)
    rm_cost = sum(inp.rmcss_usd[t] for t in ids)
    ag_cost = {t: inp.agent_usd[t] for t in ids}
    rm_f1 = _pooled_f1(inp.rmcss, inp)
    # per-task component arrays for vectorised random baselines
    rm_arr = _arr(_comps(inp.rmcss, inp.labels, ids))
    arm_arrays = {
        "REPLACE": _arr(_comps(inp.agent, inp.labels, ids)),
        "UNION": _arr(_comps({t: inp.rmcss[t] | inp.agent[t] for t in ids}, inp.labels, ids)),
    }
    rng = np.random.default_rng(X6_RANDOM_SEED)
    perms = np.array([rng.permutation(n) for _ in range(X6_RANDOM_SETS)])  # (R, n)
    frontier: dict[str, list[dict[str, Any]]] = {}
    for signal in ("U1", "U2"):
        order = escalation_order(inp, signal)
        for policy in ("REPLACE", "UNION"):
            rows = []
            esc_arr = arm_arrays[policy]
            for k in X6_FRACTIONS:
                m = round(k * n)
                escalated = set(order[:m])
                pred = _policy_sets(inp, escalated, policy)
                f1 = _pooled_f1(pred, inp)
                usd = rm_cost + sum(ag_cost[t] for t in escalated)
                tokens = sum(inp.rmcss_tokens[t] for t in ids) + sum(inp.agent_tokens[t] for t in escalated)
                # random escalation of the same size (permutation null)
                mask = np.zeros((X6_RANDOM_SETS, n), dtype=bool)
                if m > 0:
                    rows_idx = np.repeat(np.arange(X6_RANDOM_SETS), m)
                    mask[rows_idx, perms[:, :m].reshape(-1)] = True
                sums = np.where(mask[..., None], esc_arr[None, :, :], rm_arr[None, :, :]).sum(axis=1)
                rand_f1 = _f1_of_sums(sums)
                p_value = (1 + int((rand_f1 >= f1 - 1e-15).sum())) / (1 + X6_RANDOM_SETS)
                rows.append({
                    "fraction": k, "n_escalated": m, "f1": f1, "usd_total": usd,
                    "usd_per_task": usd / n, "tokens_per_task": tokens / n,
                    "random_mean_f1": float(rand_f1.mean()),
                    "random_q95_f1": float(np.quantile(rand_f1, 0.95)),
                    "p_value_vs_random_one_sided": p_value if 0 < m < n else None,
                })
            frontier[f"{signal}_{policy}"] = rows
    # oracle upper reference (per-task F1 gain ordering; descriptive only)
    gain = {t: _per_task_f1(inp.agent[t], inp.labels[t]) - _per_task_f1(inp.rmcss[t], inp.labels[t]) for t in ids}
    oracle_order = sorted(ids, key=lambda t: (-gain[t], _tie(t)))
    oracle_rows = []
    for k in X6_FRACTIONS:
        m = round(k * n)
        pred = _policy_sets(inp, set(oracle_order[:m]), "REPLACE")
        oracle_rows.append({"fraction": k, "f1": _pooled_f1(pred, inp)})
    # operating point CI vs RM-CSS
    op: dict[str, Any] = {}
    reading_hits = []
    for policy in ("REPLACE", "UNION"):
        order = escalation_order(inp, "U1")
        m = round(X6_OPERATING_POINT * n)
        pred = _policy_sets(inp, set(order[:m]), policy)
        d = _delta_ci(_comps(pred, inp.labels, ids), _comps(inp.rmcss, inp.labels, ids), draws)
        row = next(r for r in frontier[f"U1_{policy}"] if r["fraction"] == X6_OPERATING_POINT)
        op[policy] = {"minus_rmcss": d, "p_value_vs_random": row["p_value_vs_random_one_sided"],
                      "usd_per_task": row["usd_per_task"]}
        p = row["p_value_vs_random_one_sided"]
        reading_hits.append(p is not None and p < X6_ALPHA_EACH and d["point"] >= X6_MIN_GAIN)
    full_best = max(frontier["U1_REPLACE"][-1]["f1"], frontier["U1_UNION"][-1]["f1"])
    capture = None
    if full_best - rm_f1 > X6_MIN_GAIN:
        best_op = max(op["REPLACE"]["minus_rmcss"]["point"], op["UNION"]["minus_rmcss"]["point"])
        capture = best_op / (full_best - rm_f1)
    return {
        "rmcss_f1": rm_f1,
        "frontier": frontier,
        "oracle_replace_upper_reference": oracle_rows,
        "operating_point": {"fraction": X6_OPERATING_POINT, **op},
        "gain_capture_at_operating_point": capture,
        "preregistered_reading": "ESCALATION_BETTER_THAN_RANDOM" if any(reading_hits) else "ESCALATION_NO_GAIN",
        "cost_note": "cascade cost = RM-CSS for every task + Agent for escalated tasks (the cheap arm is always paid)",
    }


# ---------------------------------------------------------------------------
# X7 heterogeneity
# ---------------------------------------------------------------------------
def x7_heterogeneity(inp: ExploratoryInputs, n_resamples: int) -> dict[str, Any]:
    def gold_size_stratum(t: str) -> str:
        k = len(inp.labels[t])
        return "1" if k == 1 else ("2-3" if k <= 3 else ">=4")

    def coverage_stratum(t: str) -> str:
        pool = set(inp.candidate_prob.get(t, {}))
        g = inp.labels[t]
        inside = sum(1 for f in g if f in pool)
        return "all_in_pool" if inside == len(g) else ("none_in_pool" if inside == 0 else "partial")

    out: dict[str, Any] = {}
    strata_fns: dict[str, Callable[[str], str]] = {"gold_size": gold_size_stratum, "pool_coverage": coverage_stratum}
    for name, fn in strata_fns.items():
        groups: dict[str, list[str]] = {}
        for t in inp.task_ids:
            groups.setdefault(fn(t), []).append(t)
        res = {}
        for g, members in sorted(groups.items()):
            draws = bootstrap_indices(len(members), n_resamples=n_resamples)
            res[g] = {
                "n": len(members),
                "agent_f1": pooled(_comps(inp.agent, inp.labels, members))["f1"],
                "rmcss_f1": pooled(_comps(inp.rmcss, inp.labels, members))["f1"],
                "sip_f1": pooled(_comps(inp.sip, inp.labels, members))["f1"],
                "D_rmcss_minus_agent": _delta_ci(_comps(inp.rmcss, inp.labels, members),
                                                 _comps(inp.agent, inp.labels, members), draws),
            }
        out[name] = res
    out["note"] = "Descriptive; strata are defined from labels and are not a basis for any claim of mechanism."
    return out


# ---------------------------------------------------------------------------
# X8 cost-effectiveness
# ---------------------------------------------------------------------------
def x8_cost_effectiveness(inp: ExploratoryInputs, draws: NDArray[np.int64]) -> dict[str, Any]:
    ids = list(inp.task_ids)
    tp_ag = np.array([c.tp for c in _comps(inp.agent, inp.labels, ids)], dtype=np.float64)
    tp_rm = np.array([c.tp for c in _comps(inp.rmcss, inp.labels, ids)], dtype=np.float64)
    usd_ag = np.array([inp.agent_usd[t] for t in ids])
    usd_rm = np.array([inp.rmcss_usd[t] for t in ids])
    tok_ag = np.array([inp.agent_tokens[t] for t in ids])
    tok_rm = np.array([inp.rmcss_tokens[t] for t in ids])

    def ratio(num: NDArray[np.float64], den: NDArray[np.float64]) -> dict[str, float]:
        point = float(num.sum() / den.sum()) if den.sum() > 0 else float("inf")
        b_num = num[draws].sum(axis=1)
        b_den = den[draws].sum(axis=1)
        vals = np.where(b_den > 0, b_num / np.where(b_den > 0, b_den, 1.0), np.nan)
        finite = vals[np.isfinite(vals)]
        if finite.size == 0:
            return {"point": point, "q025": float("nan"), "q975": float("nan"), "undefined_draw_share": 1.0}
        return {"point": point, "q025": float(np.quantile(finite, 0.025)), "q975": float(np.quantile(finite, 0.975)),
                "undefined_draw_share": float(1.0 - finite.size / vals.size)}

    out: dict[str, Any] = {
        "usd_per_true_positive": {"Agent": ratio(usd_ag, tp_ag), "RM-CSS": ratio(usd_rm, tp_rm)},
        "true_positives_per_million_tokens": {
            "Agent": ratio(tp_ag * 1e6, tok_ag),
            "RM-CSS": ratio(tp_rm * 1e6, tok_rm),
        },
    }
    d_tp = tp_ag.sum() - tp_rm.sum()
    out["icer_usd_per_extra_true_positive_agent_vs_rmcss"] = (
        float((usd_ag.sum() - usd_rm.sum()) / d_tp) if d_tp > 0 else None
    )
    return out


# ---------------------------------------------------------------------------
# X9 budget binding (descriptive)
# ---------------------------------------------------------------------------
def x9_budget_binding(inp: ExploratoryInputs) -> dict[str, Any]:
    forced = [t for t in inp.task_ids if inp.agent_forced_final.get(t)]
    voluntary = [t for t in inp.task_ids if not inp.agent_forced_final.get(t)]
    calls_hist: dict[str, int] = {}
    for t in inp.task_ids:
        k = str(inp.agent_calls[t])
        calls_hist[k] = calls_hist.get(k, 0) + 1
    by_calls: dict[str, float] = {}
    for k in sorted(calls_hist, key=int):
        members = [t for t in inp.task_ids if str(inp.agent_calls[t]) == k]
        by_calls[k] = pooled(_comps(inp.agent, inp.labels, members))["f1"]

    def grp(members: list[str]) -> dict[str, Any]:
        if not members:
            return {"n": 0}
        return {"n": len(members), "agent_f1": pooled(_comps(inp.agent, inp.labels, members))["f1"],
                "rmcss_f1": pooled(_comps(inp.rmcss, inp.labels, members))["f1"],
                "agent_empty_rate": sum(1 for t in members if not inp.agent[t]) / len(members)}

    return {"forced_final": grp(forced), "voluntary_final": grp(voluntary), "calls_histogram": calls_hist,
            "agent_f1_by_calls_used": by_calls,
            "note": "Confounded by task difficulty (harder tasks use more calls); descriptive only."}


# ---------------------------------------------------------------------------
# X10 zero-generative-LLM dense anchor
# ---------------------------------------------------------------------------
def x10_dense_anchor(inp: ExploratoryInputs, draws: NDArray[np.int64]) -> dict[str, Any]:
    ids = list(inp.task_ids)
    base = _comps(inp.rmcss, inp.labels, ids)
    out: dict[str, Any] = {}
    matched = {t: frozenset(list(inp.dense_rank.get(t, ()))[: len(inp.rmcss[t])]) for t in ids}
    out["size_matched_to_rmcss"] = {**pooled(_comps(matched, inp.labels, ids)),
                                    "minus_rmcss": _delta_ci(_comps(matched, inp.labels, ids), base, draws)}
    for k in X10_FIXED_K:
        topk = {t: frozenset(list(inp.dense_rank.get(t, ()))[:k]) for t in ids}
        out[f"top_{k}"] = {**pooled(_comps(topk, inp.labels, ids)),
                           "minus_rmcss": _delta_ci(_comps(topk, inp.labels, ids), base, draws)}
    out["note"] = ("Qwen3-Embedding-8B file ranking only (no generative call); scores are the frozen "
                   "RESERVE-300 dense scores already used by RM-CSS.")
    return out


# ---------------------------------------------------------------------------
# X11 agent tool-quality descriptives (label-free)
# ---------------------------------------------------------------------------
def x11_tool_quality(sidecar: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_item: dict[str, list[Mapping[str, Any]]] = {}
    for r in sidecar:
        by_item.setdefault(str(r.get("work_key", r.get("task_id", ""))), []).append(r)
    tool_calls = nonconsec_dup = searches = zero_hit = multi_word = multi_word_zero = 0
    for rows in by_item.values():
        seen: list[tuple[str, str, str]] = []
        prev: tuple[str, str, str] | None = None
        for r in sorted(rows, key=lambda x: int(x.get("call_index", 0))):
            action = str(r.get("action", ""))
            if action not in ("read_file", "search_text", "list_files"):
                prev = None
                continue
            sig = (action, str(r.get("path", "")), str(r.get("query", "")))
            tool_calls += 1
            if sig in seen and sig != prev:
                nonconsec_dup += 1
            seen.append(sig)
            prev = sig
            if action == "search_text":
                searches += 1
                hits = int(r.get("search_results_returned", 0))
                words = len(str(r.get("query", "")).split())
                zero_hit += int(hits == 0)
                if words >= 2:
                    multi_word += 1
                    multi_word_zero += int(hits == 0)
    return {
        "tool_calls_executed": tool_calls,
        "non_consecutive_duplicate_requests": nonconsec_dup,
        "non_consecutive_duplicate_share": nonconsec_dup / tool_calls if tool_calls else 0.0,
        "search_calls": searches,
        "zero_result_search_share": zero_hit / searches if searches else 0.0,
        "multi_word_search_share": multi_word / searches if searches else 0.0,
        "multi_word_zero_result_share": multi_word_zero / multi_word if multi_word else 0.0,
        "note": "search_text is a case-insensitive SUBSTRING match of the whole query; the frozen rejection "
                "rule only rejects CONSECUTIVE identical requests.",
    }


# ---------------------------------------------------------------------------
def run_all(inp: ExploratoryInputs) -> dict[str, Any]:
    draws = bootstrap_indices(len(inp.task_ids), n_resamples=inp.n_resamples)
    return {
        "artifact": "wp1b_exploratory_results",
        "status": "EXPLORATORY_PREREGISTERED (never primary)",
        "n_tasks": len(inp.task_ids),
        "X1_secondary_metrics": x1_secondary(inp, draws),
        "X2_recall_vs_decision_split": x2_pool_split(inp),
        "X3_band_teacher_ceiling": x3_band_teacher(inp, draws),
        "X4_discovery_commitment_gap": x4_discovery_gap(inp),
        "X5_complementarity": x5_complementarity(inp, draws),
        "X6_escalation_frontier": x6_escalation(inp, draws),
        "X7_heterogeneity": x7_heterogeneity(inp, min(inp.n_resamples, 2000)),
        "X8_cost_effectiveness": x8_cost_effectiveness(inp, draws),
        "X9_budget_binding": x9_budget_binding(inp),
        "X10_dense_anchor": x10_dense_anchor(inp, draws),
        "X11_tool_quality": x11_tool_quality(inp.sidecar),
    }


def random_seed_note() -> str:
    return f"bootstrap seed 20260920; X6 random-escalation seed {X6_RANDOM_SEED}; tie salt {X6_TIE_SALT}"
