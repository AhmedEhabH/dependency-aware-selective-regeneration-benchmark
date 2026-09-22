"""WP-1b MAIN_297 result -> Markdown report + LaTeX table (deterministic)."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

_ARMS = ("SIP", "RM-CSS", "Agent")


def _f(x: Any, nd: int = 4) -> str:
    if x is None:
        return "n/a"
    if isinstance(x, bool):
        return str(x)
    if isinstance(x, int):
        return f"{x:,}"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def _ci(d: Mapping[str, Any]) -> str:
    return f"{d['point']:+.4f} [{d['q025']:+.4f}, {d['q975']:+.4f}]; Q5 {d['q05']:+.4f}"


def render_markdown(res: Mapping[str, Any], *, freeze_tag: str, freeze_sha256: str,
                    run_summary: Mapping[str, Any]) -> str:
    arms = res["arms"]
    p = res["P_primary_fail_closed"]
    s = res["S_instrument_failure_excluded"]
    v = res["quality_verdict"]
    cost = res["cost_view_A_marginal"]
    lines: list[str] = []
    lines.append(f"# WP-1b {res['analysis']} - result (frozen decision rules v2)\n")
    lines.append(f"**Final category:** `{res['final_category']}`  ")
    lines.append(f"**Quality verdict:** `{v['verdict']}` (row {v['id']} of 7)  ")
    if v.get("mandatory_note"):
        lines.append(f"**Mandatory note:** {v['mandatory_note']}  ")
    lines.append(f"**Cost verdict (View A):** CHEAPER = `{res['cheaper_view_A']}`  ")
    lines.append(f"**n:** {res['n_tasks']} tasks · labels: {res['labels']}  ")
    lines.append(f"**Prediction freeze:** tag `{freeze_tag}` · sha256 `{freeze_sha256}`\n")
    lines.append("## 1. Per-arm metrics (pooled micro over identical task IDs)\n")
    lines.append("| Arm | TP | FP | FN | Precision | Recall | F1 | F2 | FNR | mean set size | EMPTY rate |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for a in _ARMS:
        m = arms[a]
        lines.append(
            f"| {a} | {m['tp']} | {m['fp']} | {m['fn']} | {_f(m['precision'])} | {_f(m['recall'])} | "
            f"**{_f(m['f1'])}** | {_f(m['f2'])} | {_f(m['fnr'])} | {_f(m['mean_predicted_set_size'], 2)} | "
            f"{_f(m['empty_set_rate'], 3)} |"
        )
    lines.append("")
    lines.append("## 2. Primary comparison D = F1(RM-CSS) − F1(Agent)\n")
    lines.append("| Analysis | n | D point [Q2.5, Q97.5]; Q5 | NI (Q5 > −0.05) |")
    lines.append("|---|---:|---|:---:|")
    lines.append(f"| P (fail-closed, primary) | {p['n_tasks']} | {_ci(p)} | {p['q05'] > -res['margin']} |")
    lines.append(f"| S (drop truncation/parser/infra; dropped {s['n_dropped']}) | {s['n_tasks']} | {_ci(s)} | "
                 f"{s['q05'] > -res['margin']} |")
    lines.append("")
    sens = res["sensitivity_margins_not_decisive"]
    lines.append("Sensitivity margins (reported, not decisive): "
                 + ", ".join(f"Δ={k}: `{val}`" for k, val in sens.items()) + "\n")
    lines.append("## 3. Cost (View A, marginal per change) — ratio RM-CSS / Agent of per-task means\n")
    lines.append("| Dimension | RM-CSS mean | Agent mean | ratio [95% CI] | upper < 1 |")
    lines.append("|---|---:|---:|---|:---:|")
    for dim, c in cost.items():
        lines.append(f"| {dim} | {_f(c['rmcss_mean'], 4)} | {_f(c['agent_mean'], 4)} | "
                     f"{c['ratio_point']:.3f} [{c['ci95_lower']:.3f}, {c['ci95_upper']:.3f}] | "
                     f"{c['ci95_upper'] < 1.0} |")
    vb = res["cost_view_B_setup"]
    lines.append(f"\nView B (setup amortized over n): +${vb['amortized_setup_usd_per_task']:.6f}/task "
                 f"→ RM-CSS ${vb['rmcss_view_b_usd_per_task']:.6f}/task.  ")
    lines.append(f"RM-CSS calls/task in View A = {res['rmcss_calls_per_task_view_a']} "
                 "(1 SIP coder call + 1 query-embedding request; preregistered).\n")
    lines.append("## 4. Agent failure modes (fail-closed EMPTY by reason)\n")
    emp = res["agent_empty_by_reason"] or {"none": 0}
    lines.append(", ".join(f"`{k}`: {val}" for k, val in sorted(emp.items())) + "\n")
    d = res["descriptive"]
    lines.append("## 5. Descriptive (not part of the verdict)\n")
    lines.append(f"- SIP − Agent: {_ci(d['SIP_minus_Agent'])}")
    lines.append(f"- RM-CSS − SIP on this subset: {_ci(d['RMCSS_minus_SIP_on_this_subset'])}\n")
    lines.append("## 6. Run accounting\n")
    lines.append(f"- ledger USD (frozen list price): ${_f(run_summary.get('ledger_usd'), 6)} of "
                 f"${_f(run_summary.get('ceiling_usd'), 2)}")
    lines.append(f"- logical calls {run_summary.get('logical_calls')} · HTTP attempts "
                 f"{run_summary.get('http_attempts')} · failed calls {run_summary.get('failed_calls')}")
    lines.append("")
    lines.append("## 7. What this result does NOT mean\n")
    lines.append("- It is a SELECTION-ONLY file-localization result against an observed change-set proxy, "
                 "not semantic gold and not end-to-end patch correctness (WP-2 / E2E-G6 not started).")
    lines.append("- The competitor is a budget-bounded iterative repository agent (8 calls, 1024-token "
                 "control cap, 2000-char observation window, substring search), not the strongest possible "
                 "agent and not a reproduction of LocAgent / Ripple / other published systems.")
    lines.append("- Single repository (Saleor), single model (Qwen3-Coder-480B via DeepInfra), temperature 0.")
    lines.append("- The word 'dominance' is retired for WP-1b; no equivalence claim is made from a CI "
                 "that crosses zero.")
    return "\n".join(lines) + "\n"


def render_latex_table(res: Mapping[str, Any]) -> str:
    arms = res["arms"]
    cost = res["cost_view_A_marginal"]
    rows = []
    for a in _ARMS:
        m = arms[a]
        rows.append(f"{a} & {m['precision']:.3f} & {m['recall']:.3f} & {m['f1']:.3f} & "
                    f"{m['mean_predicted_set_size']:.2f} & {m['empty_set_rate']:.3f} \\\\")
    p = res["P_primary_fail_closed"]
    verdict_tex = res["quality_verdict"]["verdict"].replace("_", "\\_")
    body = "\n".join(rows)
    return (
        "% Auto-generated by scripts/wp1b_score_main.py - do not edit by hand.\n"
        "\\begin{table}[t]\\centering\\small\n"
        f"\\caption{{Selection-only comparison on Saleor MAIN\\_{res['n_tasks']} (pooled micro). "
        f"$D=F_1(\\text{{RM-CSS}})-F_1(\\text{{Agent}})={p['point']:+.3f}$ "
        f"[{p['q025']:+.3f}, {p['q975']:+.3f}]; verdict: {verdict_tex}; "
        f"cost ratio (USD) {cost['usd']['ratio_point']:.2f} "
        f"[{cost['usd']['ci95_lower']:.2f}, {cost['usd']['ci95_upper']:.2f}].}}\n"
        "\\label{tab:wp1b-main}\n"
        "\\begin{tabular}{lrrrrr}\\hline\n"
        "Arm & P & R & F1 & $|\\hat{S}|$ & EMPTY \\\\ \\hline\n"
        f"{body}\n"
        "\\hline\\end{tabular}\\end{table}\n"
    )


# Claim-safe sentences: the ONLY allowed prose summary per preregistered category.
CATEGORY_SENTENCES: dict[str, str] = {
    "RMCSS_SUPERIOR_AT_LOWER_COST": (
        "Under an identical model and protocol, RM-CSS selected the changed files more accurately than the "
        "budget-bounded repository agent, at lower cost."
    ),
    "RMCSS_NONINFERIOR_AT_LOWER_COST": (
        "RM-CSS was non-inferior to the budget-bounded repository agent (margin 0.05 pooled micro-F1), "
        "at lower cost."
    ),
    "INCONCLUSIVE_QUALITY_AT_LOWER_COST": (
        "RM-CSS was cheaper; the quality difference was inconclusive at this sample size, which is not "
        "evidence of equivalence."
    ),
    "COST_QUALITY_TRADEOFF": (
        "The budget-bounded agent selected the changed files more accurately, while RM-CSS was cheaper: "
        "a cost-quality trade-off."
    ),
    "NO_EFFICIENCY_ADVANTAGE": "RM-CSS showed no marginal cost advantage over the budget-bounded agent.",
}
VERDICT2_SENTENCE = (
    "Its F1 was nevertheless statistically lower than the agent's, inside the non-inferiority margin."
)


def claim_sentence(res: Mapping[str, Any]) -> str:
    sentence = CATEGORY_SENTENCES[str(res["final_category"])]
    if int(res["quality_verdict"]["id"]) == 2:
        sentence = f"{sentence} {VERDICT2_SENTENCE}"
    return sentence


def render_results_paragraph(res: Mapping[str, Any], exploratory: Mapping[str, Any] | None = None) -> str:
    """LaTeX paragraph with numbers inserted from the frozen result JSON (no hand-typed numbers)."""
    arms = res["arms"]
    p = res["P_primary_fail_closed"]
    usd = res["cost_view_A_marginal"]["usd"]
    tok = res["cost_view_A_marginal"]["total_tokens"]
    text = (
        "% Auto-generated from reports/wp1b_main297_result.json - do not edit numbers by hand.\n"
        f"On Saleor MAIN\\_{res['n_tasks']}, pooled micro-F1 was {arms['RM-CSS']['f1']:.3f} for RM-CSS, "
        f"{arms['Agent']['f1']:.3f} for the agent and {arms['SIP']['f1']:.3f} for SIP. "
        f"The paired difference $D=F_1(\\text{{RM-CSS}})-F_1(\\text{{Agent}})$ was {p['point']:+.3f} "
        f"(95\\% CI [{p['q025']:+.3f}, {p['q975']:+.3f}]; one-sided lower bound {p['q05']:+.3f}). "
        f"{claim_sentence(res)} "
        f"Per task, RM-CSS used {tok['ratio_point']:.2f}$\\times$ the agent's tokens "
        f"(95\\% CI [{tok['ci95_lower']:.2f}, {tok['ci95_upper']:.2f}]) and "
        f"{usd['ratio_point']:.2f}$\\times$ its cost "
        f"([{usd['ci95_lower']:.2f}, {usd['ci95_upper']:.2f}]). "
        f"The agent returned an empty set on {arms['Agent']['empty_set_rate'] * 100:.1f}\\% of tasks."
    )
    if exploratory is not None:
        x6 = exploratory["X6_escalation_frontier"]
        op = x6["operating_point"]
        best = max(("REPLACE", "UNION"), key=lambda k: op[k]["minus_rmcss"]["point"])
        text += (
            f" In a preregistered exploratory analysis, escalating the 20\\% least-confident tasks from RM-CSS "
            f"to the agent ({best.lower()} policy) changed F1 by {op[best]['minus_rmcss']['point']:+.3f} "
            f"(reading: {x6['preregistered_reading'].replace('_', ' ').lower()})."
        )
    return text + "\n"
