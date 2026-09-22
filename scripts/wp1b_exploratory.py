#!/usr/bin/env python3
"""WP-1b exploratory analyses X1-X11 - ONLY after the primary result is frozen and tagged.

Preconditions (fail-closed):
 * the primary result JSON exists, the primary-result tag points at the same
   object locally and on origin (``--primary-tag``), and the tag holds this
   exact primary result JSON (LF-normalized);
 * the agent prediction freeze matches its sidecar;
 * the scoring-side sealed-outcome guard is installed.

RM-CSS probabilities are reproduced from the FROZEN DEPLOYMENT ARTIFACT
``research/stage5-v2-final/deployment_artifact.json`` (config_sha256
8925d29a...). Do NOT use ``django_only_rmcss_transfer_model.json``: it does not
reproduce the frozen RM-CSS sets (196/300 tasks only). The script verifies that
thresholding the reproduced probabilities at 0.20 gives the frozen RM-CSS sets
for every scored task before any analysis.

Usage:
  python scripts/wp1b_exploratory.py --run-dir research/wp1b/main-297-2026-09-22 \
     --primary-tag wp1b-main297-result-2026-09-22 \
     --out-json reports/wp1b_main297_exploratory.json --out-md reports/WP1B_MAIN297_EXPLORATORY.md \
     --out-svg docs/assets/wp1b_cost_quality_frontier.svg

Exit: 0 done | 1 precondition failure | 3 config error | 4 origin unreachable (retry later)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

import pandas as pd  # noqa: E402

from benchmark.wp1a.rederive import apply_frozen_model  # noqa: E402
from benchmark.wp1a.schema import load_prediction_view  # noqa: E402
from benchmark.wp1b import exploratory as ex  # noqa: E402
from benchmark.wp1b import freeze as fz  # noqa: E402
from benchmark.wp1b import git_gate as gg  # noqa: E402
from benchmark.wp1b import main_scoring as ms  # noqa: E402
from benchmark.wp1b.label_guard import install_sealed_outcome_guard  # noqa: E402
from benchmark.wp1b.main_runner import read_jsonl_tolerant  # noqa: E402
from benchmark.wp1b.report_render import render_results_paragraph  # noqa: E402
from benchmark.wp1b.svg_plot import Marker, Series, line_chart  # noqa: E402

R300 = _PROJECT_DIR / "research" / "saleor-reserve-300-rmcss"
SIP_RMCSS = _PROJECT_DIR / "research" / "wp1a" / "sip_rmcss_per_task_predictions.json"
DEPLOYMENT = _PROJECT_DIR / "research" / "stage5-v2-final" / "deployment_artifact.json"
DEPLOYMENT_CONFIG_SHA256 = "8925d29a8e065bc864cd16e755ac0e896c7675b4a12f68fb66c35e5bd644ea95"


def _probabilities(task_ids: list[str], rmcss: dict[str, frozenset[str]]) -> dict[str, dict[str, float]]:
    deployment = json.loads(DEPLOYMENT.read_text(encoding="utf-8"))
    if deployment.get("config_sha256") != DEPLOYMENT_CONFIG_SHA256:
        raise RuntimeError("deployment artifact config_sha256 mismatch")
    frame = load_prediction_view(R300 / "candidate_rows_saleor300.parquet")
    frame = frame.copy()
    frame["prob"] = apply_frozen_model(deployment, frame)
    out: dict[str, dict[str, float]] = {}
    for cid, g in frame.groupby("case_id", sort=True):
        out[str(cid)] = {str(f): float(p) for f, p in zip(g["file_path"], g["prob"], strict=True)}
    bad = [t for t in task_ids if frozenset(f for f, p in out.get(t, {}).items() if p >= 0.20) != rmcss[t]]
    if bad:
        raise RuntimeError(f"reproduced RM-CSS probabilities disagree with frozen sets on {len(bad)} tasks")
    return out


def _dense_rank(task_ids: list[str]) -> dict[str, list[str]]:
    df = pd.read_parquet(R300 / "full_file_scores_saleor300.parquet",
                         columns=["case_id", "file_path", "dense_rank"])
    df = df[df["case_id"].isin(task_ids)].sort_values(["case_id", "dense_rank"])
    return {str(c): [str(f) for f in g["file_path"]] for c, g in df.groupby("case_id", sort=True)}


def _markdown(res: dict[str, Any]) -> str:
    x6 = res["X6_escalation_frontier"]
    op = x6["operating_point"]
    x3 = res["X3_band_teacher_ceiling"]
    x10 = res["X10_dense_anchor"]
    x2 = res["X2_recall_vs_decision_split"]
    x4 = res["X4_discovery_commitment_gap"]
    x11 = res["X11_tool_quality"]
    lines = ["# WP-1b MAIN_297 - exploratory analyses X1-X11 (never primary)\n",
             "Computed after the primary result was frozen and tagged. None of these results can change the "
             "primary verdict.\n",
             "## X6 escalation frontier (RM-CSS -> Agent cascade)\n",
             f"- preregistered reading: `{x6['preregistered_reading']}`",
             f"- RM-CSS F1 {x6['rmcss_f1']:.4f}; at 20% escalation (U1): REPLACE "
             f"{op['REPLACE']['minus_rmcss']['point']:+.4f} [{op['REPLACE']['minus_rmcss']['q025']:+.4f}, "
             f"{op['REPLACE']['minus_rmcss']['q975']:+.4f}] (p vs random {op['REPLACE']['p_value_vs_random']}); "
             f"UNION {op['UNION']['minus_rmcss']['point']:+.4f} [{op['UNION']['minus_rmcss']['q025']:+.4f}, "
             f"{op['UNION']['minus_rmcss']['q975']:+.4f}] (p vs random {op['UNION']['p_value_vs_random']})",
             f"- gain capture at 20%: {x6['gain_capture_at_operating_point']}\n",
             "| fraction | U1-REPLACE F1 | U1-UNION F1 | random mean (REPLACE) | USD/task (U1-REPLACE) |",
             "|---:|---:|---:|---:|---:|"]
    for a, b in zip(x6["frontier"]["U1_REPLACE"], x6["frontier"]["U1_UNION"], strict=True):
        lines.append(f"| {a['fraction']:.2f} | {a['f1']:.4f} | {b['f1']:.4f} | {a['random_mean_f1']:.4f} | "
                     f"{a['usd_per_task']:.5f} |")
    lines += ["", "## X3 band teacher ceiling\n", f"- reading: `{x3['preregistered_reading']}`",
              f"- [0.10,0.35): hybrid − RM-CSS {x3['[0.10,0.35)']['hybrid_minus_rmcss']['point']:+.4f} "
              f"(Q5 {x3['[0.10,0.35)']['hybrid_minus_rmcss']['q05']:+.4f})\n",
              "## X10 zero-generative dense anchor\n",
              f"- size-matched dense top-k F1 {x10['size_matched_to_rmcss']['f1']:.4f} "
              f"(minus RM-CSS {x10['size_matched_to_rmcss']['minus_rmcss']['point']:+.4f})\n",
              "## X2 / X4 / X11\n",
              f"- gold in RM-CSS pool {x2['gold_in_pool_rate']:.3f}; "
              f"agent recall inside {x2['agent_recall_inside_pool']:.3f} / "
              f"outside {x2['agent_recall_outside_pool']:.3f}",
              f"- gold read-but-not-selected {x4['share_read_not_selected']:.3f}; surfaced-not-selected "
              f"{x4['share_surfaced_not_selected']:.3f}",
              f"- non-consecutive duplicate tool requests {x11['non_consecutive_duplicate_share']:.3f}; "
              f"zero-result searches {x11['zero_result_search_share']:.3f} "
              f"(multi-word {x11['multi_word_zero_result_share']:.3f})\n"]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", required=True, type=Path)
    ap.add_argument("--primary-result", type=Path, default=Path("reports/wp1b_main297_result.json"))
    ap.add_argument("--primary-tag", required=True)
    ap.add_argument("--out-json", required=True, type=Path)
    ap.add_argument("--out-md", required=True, type=Path)
    ap.add_argument("--out-svg", type=Path, default=None)
    ap.add_argument("--out-paragraph", type=Path, default=None,
                    help="LaTeX results paragraph generated from the frozen JSONs (claim-safe sentences only)")
    ap.add_argument("--skip-git-check", action="store_true", help="TESTS ONLY")
    args = ap.parse_args(argv)

    def _abs(p: Path) -> Path:
        return p if p.is_absolute() else _PROJECT_DIR / p

    run_dir = _abs(args.run_dir)
    primary = _abs(args.primary_result)
    if not primary.exists():
        print("[explore] STOP: the primary result does not exist yet (exploratory runs only after it)")
        return 1
    try:
        skip = gg.skip_allowed(args.skip_git_check)
    except gg.GitGateError as exc:
        print(f"[explore] ERROR: {exc}")
        return 3
    if not skip:
        try:
            gg.verify_tag_on_origin(_PROJECT_DIR, args.primary_tag)
            gg.verify_file_in_tag(_PROJECT_DIR, args.primary_tag, primary)
        except gg.GitRemoteUnavailableError as exc:
            print(f"[explore] origin unreachable - retry later: {exc}")
            return 4
        except gg.GitGateError as exc:
            print(f"[explore] STOP: primary-result tag check failed: {exc}")
            return 1
    install_sealed_outcome_guard(_PROJECT_DIR)
    agent = ms.load_agent_freeze(run_dir / fz.FREEZE_FILE, run_dir / (fz.FREEZE_FILE + ".sha256"))
    per = json.loads((run_dir / fz.FREEZE_FILE).read_text(encoding="utf-8"))["per_task"]
    ids = list(agent.task_ids)
    sip, rmcss = ms.load_sip_rmcss(SIP_RMCSS, SIP_RMCSS.with_suffix(".sha256"))
    labels = ms.load_opened_proxies(R300 / "saleor_reserve_300_proxies.json")
    sip_cost = ms.load_sip_cost(R300 / "sip_300_run_records.jsonl")
    emb = ms.load_embedding_cost(R300 / "saleor_reserve_300_efficiency.json")
    telemetry_rows, _ = read_jsonl_tolerant(run_dir / "wp1b_telemetry.jsonl")
    sidecar_rows, _ = read_jsonl_tolerant(run_dir / "wp1b_call_sidecar.jsonl")
    tel = {str(r["task_id"]): r for r in telemetry_rows}
    inp = ex.ExploratoryInputs(
        task_ids=tuple(ids), labels=labels, agent=agent.predictions, rmcss=rmcss, sip=sip,
        agent_usd=agent.usd, agent_tokens={t: float(v) for t, v in agent.tokens.items()},
        agent_forced_final={t: bool(per[t]["forced_final"]) for t in ids},
        agent_calls=agent.calls, agent_empty_reason=agent.empty_reason,
        rmcss_usd={t: sip_cost.usd[t] + emb.usd_per_task for t in ids},
        rmcss_tokens={t: sip_cost.tokens[t] + emb.tokens_per_task for t in ids},
        candidate_prob=_probabilities(ids, rmcss),
        dense_rank=_dense_rank(ids),
        paths_read={t: frozenset(tel.get(t, {}).get("paths_read", [])) for t in ids},
        paths_surfaced={t: frozenset(tel.get(t, {}).get("paths_surfaced", [])) for t in ids},
        sidecar=sidecar_rows,
    )
    res = ex.run_all(inp)
    res["seeds"] = ex.random_seed_note()
    out_json, out_md = _abs(args.out_json), _abs(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(res, indent=1, sort_keys=True), encoding="utf-8")
    out_md.write_text(_markdown(res), encoding="utf-8")
    if args.out_svg is not None:
        x6 = res["X6_escalation_frontier"]["frontier"]
        series = [
            Series("U1 cascade (REPLACE)", [(r["usd_per_task"], r["f1"]) for r in x6["U1_REPLACE"]]),
            Series("U1 cascade (UNION)", [(r["usd_per_task"], r["f1"]) for r in x6["U1_UNION"]]),
            Series("random escalation (REPLACE)", [(r["usd_per_task"], r["random_mean_f1"])
                                                  for r in x6["U1_REPLACE"]], dashed=True),
        ]
        prim = json.loads(primary.read_text(encoding="utf-8"))
        n = len(ids)
        markers = [
            Marker("SIP", sum(sip_cost.usd[t] for t in ids) / n, prim["arms"]["SIP"]["f1"]),
            Marker("RM-CSS", sum(inp.rmcss_usd.values()) / n, prim["arms"]["RM-CSS"]["f1"]),
            Marker("Agent", sum(agent.usd.values()) / n, prim["arms"]["Agent"]["f1"]),
        ]
        svg = line_chart(series, markers, title="WP-1b cost-quality frontier (Saleor MAIN_297)",
                         x_label="USD per task (frozen list price)", y_label="pooled micro-F1")
        out_svg = _abs(args.out_svg)
        out_svg.parent.mkdir(parents=True, exist_ok=True)
        out_svg.write_text(svg, encoding="utf-8")
    if args.out_paragraph is not None:
        out_par = _abs(args.out_paragraph)
        out_par.parent.mkdir(parents=True, exist_ok=True)
        out_par.write_text(render_results_paragraph(json.loads(primary.read_text(encoding="utf-8")), res),
                           encoding="utf-8")
    print(f"[explore] X6 reading: {res['X6_escalation_frontier']['preregistered_reading']}; "
          f"X3 reading: {res['X3_band_teacher_ceiling']['preregistered_reading']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
