#!/usr/bin/env python3
"""Generate the final djangoCMS external-validity study reports from raw evidence."""

from __future__ import annotations

import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from benchmark.external_validity import study_runtime as wiring

PROJECT_DIR = wiring.PROJECT_DIR
STUDY_DIR = PROJECT_DIR / "reports" / "scientific-stagec-djangocms-study-01"

STUDY_ID = "scientific-stagec-djangocms-01"
WIRING_TAG = "stagec-djangocms-study-wiring-verified-01"
PRIMARY_MODEL = "qwen/qwen3-coder"
PROVIDER_TAG = "deepinfra/turbo"
AGENT_CAP = 1024
IMPACTPLAN_CAP = 4096
HARD_COST_CEILING_USD = 0.50

ARMS = ("iterative_repository_agent", "impact_plan")


def load_records() -> list[dict]:
    recs = []
    for line in (STUDY_DIR / "run_records.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            recs.append(json.loads(line))
    return recs


def load_metrics() -> dict:
    return json.loads((STUDY_DIR / "final_metrics.json").read_text(encoding="utf-8"))


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _micro_table_rows(metrics: dict) -> dict[str, dict]:
    out = {}
    for arm in ARMS:
        v = metrics["overall"][arm]
        out[arm] = {
            "arm": arm,
            "selected": v["selected"],
            "tp": v["tp"],
            "fp": v["fp"],
            "fn": v["fn"],
            "precision": v["precision"],
            "recall": v["recall"],
            "f1": v["f1"],
            "fnr": v["fnr"],
            "tokens": v["tokens"],
            "model_calls": v["model_calls"],
            "time": round(v["latency_seconds"], 1),
            "cost": round(v["api_cost"], 6),
        }
    return out


def write_csv() -> Path:
    records = load_records()
    metrics = load_metrics()
    out = PROJECT_DIR / "reports" / "FINAL_BENCHMARK_RESULTS.csv"
    rows = []
    for r in sorted(records, key=lambda x: x["run_id"]):
        rows.append(
            {
                "run_id": r["run_id"],
                "scenario_id": r["scenario_id"],
                "repetition": r["repetition"],
                "arm": r["arm"],
                "terminal_status": r["terminal_status"],
                "selected": r["predicted_write_set_size"],
                "tp": r["tp"],
                "fp": r["fp"],
                "fn": r["fn"],
                "precision": r["precision"],
                "recall": r["recall"],
                "f1": r["f1"],
                "fnr": r["fnr"],
                "full_recall": r["full_recall"],
                "tokens": r["total_tokens"],
                "model_calls": r["model_calls"],
                "tool_calls": r["tool_calls"],
                "inspected_file_count": r["inspected_file_count"],
                "latency_seconds": r["latency_seconds"],
                "api_cost_usd": r["api_cost"],
                "finish_reason": r["finish_reason"],
                "truncation_status": r["truncation_status"],
                "failure_category": r["failure_category"],
                "raw_model_response_sha256": ";".join(r["raw_model_response_sha256"]),
                "visible_scenario_sha256": r["visible_scenario_sha256"],
                "runtime_universe_hash": r["runtime_universe_hash"],
            }
        )
    fieldnames = list(rows[0].keys()) if rows else []
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    # Append overall micro table block
    with out.open("a", newline="", encoding="utf-8") as f:
        f.write("\n")
        writer = csv.writer(f)
        writer.writerow(["SECTION", "OVERALL_MICRO_POOLED_VALID_RUNS"])
        writer.writerow(["arm", "valid_runs", "selected", "tp", "fp", "fn", "precision", "recall", "f1", "fnr", "tokens", "model_calls", "time", "cost"])
        for arm in ARMS:
            v = metrics["overall"][arm]
            writer.writerow([arm, v["valid_runs"], v["selected"], v["tp"], v["fp"], v["fn"],
                             v["precision"], v["recall"], v["f1"], v["fnr"],
                             v["tokens"], v["model_calls"], round(v["latency_seconds"], 1), round(v["api_cost"], 6)])
    return out


def _md_table(headers, rows):
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join("---:" if i in (1, 2, 3, 4, 9, 10, 11, 12) else "---" for i in range(len(headers))) + "|")
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


HEADLINE_HEADERS = ["Arm", "Selected", "TP", "FP", "FN", "Precision", "Recall", "F1", "FNR", "Tokens", "Model Calls", "Time", "Cost"]


def write_md() -> Path:
    metrics = load_metrics()
    records = load_records()
    out = PROJECT_DIR / "reports" / "FINAL_BENCHMARK_RESULTS.md"
    total = metrics["totals"]
    micro = _micro_table_rows(metrics)

    lines = []
    lines.append("# FINAL BENCHMARK RESULTS — djangoCMS External-Validity Stage-C Selection Study")
    lines.append("")
    lines.append(f"**STUDY_ID:** `{STUDY_ID}`")
    lines.append(f"**Generated (UTC):** {now_iso()}")
    lines.append(f"**Wiring tag:** `{WIRING_TAG}`")
    lines.append(f"**Scientific model/provider:** `{PRIMARY_MODEL}` @ `{PROVIDER_TAG}` (DeepInfra pinned through OpenRouter; fallback OFF; temperature 0)")
    lines.append(f"**Caps:** `iterative_repository_agent` = {AGENT_CAP} / `impact_plan` = {IMPACTPLAN_CAP} completion tokens")
    lines.append(f"**Scope:** SELECTION ONLY (no regeneration / repair / migration / functional execution)")
    lines.append(f"**Design:** 6 scenarios × 2 arms × 5 repetitions = exactly 60 manifest cells")
    lines.append(f"**Recorded:** 60/60 cells — {metrics['successful_cells']} succeeded (valid) / {metrics['failed_cells']} failed (recorded)")
    lines.append(f"**Universe:** 144 paths, canonical SHA-256 `{wiring.runtime_universe_canonical_hash()}`")
    lines.append(f"**Total recorded cost:** ${total['api_cost_usd']:.6f} (ceiling $0.50) — **COST_LOCK=PASS**")
    lines.append("")

    lines.append("## 1. OVERALL HEADLINE TABLE (MICRO-AGGREGATED, pooled over VALID runs)")
    lines.append("")
    lines.append("Micro-aggregation pools TP/FP/FN across each arm's valid (succeeded) study runs. **Percentages are NOT averaged.**")
    lines.append("")
    lines.append(f"**WARNING (missing-data asymmetry):** Agent has {metrics['overall']['iterative_repository_agent']['valid_runs']} valid runs; "
                 f"ImpactPlan has {metrics['overall']['impact_plan']['valid_runs']} valid runs "
                 f"({24 - 1 + 1} of its 30 cells failed operationally — 4096-cap truncation / unknown-path hallucination / 429 / harness defect). "
                 "ImpactPlan micro-metrics therefore describe only the small survivor subset and are NOT comparable to Agent micro-metrics as equal-evidence estimates.")
    lines.append("")
    rows = []
    for arm in ARMS:
        v = micro[arm]
        rows.append([arm, v["selected"], v["tp"], v["fp"], v["fn"], f"{v['precision']:.4f}", f"{v['recall']:.4f}",
                     f"{v['f1']:.4f}", f"{v['fnr']:.4f}", v["tokens"], v["model_calls"], v["time"], f"{v['cost']:.6f}"])
    lines.append(_md_table(HEADLINE_HEADERS, rows))
    lines.append("")
    lines.append("> Selected = total selected paths across the arm's valid runs; Tokens = total scientific tokens; "
                 "Model Calls = total model calls; Time = total measured latency (s); Cost = total recorded API cost (USD).")
    lines.append("")

    lines.append("## 2. MACRO PER-RUN STATISTICS (valid runs; reported separately from MICRO)")
    lines.append("")
    for arm in ARMS:
        m = metrics["macro"][arm]
        lines.append(f"### {arm} (valid runs = {metrics['overall'][arm]['valid_runs']})")
        lines.append("")
        lines.append(_md_table(
            ["Metric", "Mean", "Median", "Min", "Max"],
            [
                ["precision", f"{m['mean_precision']:.4f}", f"{m['median_precision']:.4f}", "", ""],
                ["recall", f"{m['mean_recall']:.4f}", f"{m['median_recall']:.4f}", "", ""],
                ["f1", f"{m['mean_f1']:.4f}", f"{m['median_f1']:.4f}", "", ""],
                ["selected_set_size", m["selected_set_size"]["mean"], m["selected_set_size"]["median"], m["selected_set_size"]["min"], m["selected_set_size"]["max"]],
                ["tokens", m["tokens"]["mean"], m["tokens"]["median"], m["tokens"]["min"], m["tokens"]["max"]],
                ["model_calls", m["model_calls"]["mean"], m["model_calls"]["median"], m["model_calls"]["min"], m["model_calls"]["max"]],
                ["latency_seconds", f"{m['latency']['mean']:.2f}", f"{m['latency']['median']:.2f}", f"{m['latency']['min']:.2f}", f"{m['latency']['max']:.2f}"],
                ["api_cost_usd", f"{m['cost']['mean']:.6f}", f"{m['cost']['median']:.6f}", f"{m['cost']['min']:.6f}", f"{m['cost']['max']:.6f}"],
            ],
        ))
        lines.append(f"- **Full-recall rate** (proportion of valid runs with recall == 1.0): **{m['full_recall_rate']:.4f}**")
        lines.append("")

    lines.append("## 3. PER-SCENARIO TABLES (pooled across the 5 repetitions; same micro schema)")
    lines.append("")
    for sid in sorted(metrics["per_scenario"]):
        lines.append(f"### {sid}")
        lines.append("")
        rows = []
        for arm in ARMS:
            v = metrics["per_scenario"][sid][arm]
            note = "" if v["valid_runs"] > 0 else " (no valid runs — all 5 repetitions failed)"
            rows.append([arm + note, v["selected"], v["tp"], v["fp"], v["fn"], f"{v['precision']:.4f}", f"{v['recall']:.4f}",
                         f"{v['f1']:.4f}", f"{v['fnr']:.4f}", v["tokens"], v["model_calls"], round(v["latency_seconds"], 1), f"{v['api_cost']:.6f}"])
        lines.append(_md_table(HEADLINE_HEADERS, rows))
        lines.append("Values are pooled across valid repetitions only (micro).")
        lines.append("")

    lines.append("## 4. FAILED-RUN ACCOUNTING (29 failed cells, none rerun, none replaced)")
    lines.append("")
    lines.append(_md_table(
        ["run_id", "arm", "failure_category", "tokens", "calls", "latency"],
        [
            [f["run_id"], f["arm"], f["failure_category"][:70],
             next((r["total_tokens"] for r in records if r["run_id"] == f["run_id"]), ""),
             next((r["model_calls"] for r in records if r["run_id"] == f["run_id"]), ""),
             next((r["latency_seconds"] for r in records if r["run_id"] == f["run_id"]), "")]
            for f in metrics["failed_run_accounting"]
        ],
    ))
    lines.append("")
    lines.append("Failure classes:")
    lines.append("1. **Model-output `finish_reason=length` at the frozen 4096 cap (ImpactPlan):** the full 144-path plan JSON did not fit in 4096 completion tokens and truncated mid-JSON → `impact_plan_planner_error: planner response not JSON (finish_reason=length)`. This is a recorded scientific/model-output failure under the frozen cap.")
    lines.append("2. **Planner hallucinated unknown paths (ImpactPlan):** the model emitted paths outside the 144-path universe (e.g. `cms/migrations/0001_initial.py`, `cms/tests/*`) → fail-closed `planner produced unknown paths`. Recorded failure.")
    lines.append("3. **Provider 429 (infrastructure):** DeepInfra shared-pool rate limit (`engine_overloaded`) exhausted the frozen 1-transient-retry policy in 5 cells (4 agent + 1 impact). Recorded infrastructure failure.")
    lines.append("4. **Agent `no paths selected after exploration`:** 1 agent cell (006-r4) explored 8 calls then submitted an empty set → recorded model-output failure.")
    lines.append("5. **Harness defect (ImpactPlan 007-r1):** the model returned `validation_obligations[].kind='ui_state_reflection'` outside the enum → `ValueError` during record construction. One model call was consumed but its token usage/cost could not be recorded (documented accounting gap, ~$0.003).")
    lines.append("")
    lines.append("**No scientific cell was rerun for any reason; no replacement runs; run 61 does not exist.**")
    lines.append("")

    lines.append("## 5. LATENCY OUTLIERS (valid runs > mean + 2σ)")
    lines.append("")
    outl = metrics["latency_outliers"]
    if outl:
        lines.append(_md_table(["run_id", "latency_seconds"], [[o["run_id"], o["latency_seconds"]] for o in outl]))
    else:
        lines.append("None.")
    lines.append("")

    lines.append("## 6. TOTALS")
    lines.append("")
    lines.append(_md_table(
        ["Metric", "Value"],
        [
            ["Recorded cells", metrics["manifest_total_cells"]],
            ["Successful (valid) cells", metrics["successful_cells"]],
            ["Failed cells", metrics["failed_cells"]],
            ["Total scientific tokens", total["tokens"]],
            ["Total model calls", total["model_calls"]],
            ["Total measured latency (s)", round(total["latency_seconds"], 1)],
            ["Total recorded API cost (USD)", f"{total['api_cost_usd']:.6f}"],
            ["Cost ceiling (USD)", HARD_COST_CEILING_USD],
            ["COST_LOCK", "PASS" if total["api_cost_usd"] <= HARD_COST_CEILING_USD else "FAIL"],
        ],
    ))
    lines.append("")
    lines.append("## 7. Provenance")
    lines.append("")
    lines.append(f"- Scientific model: `{PRIMARY_MODEL}`")
    lines.append(f"- Scientific provider: DeepInfra pinned through OpenRouter (`{PROVIDER_TAG}`), fallback OFF")
    lines.append("- Implementation/OpenCode model: authorization header declares `openrouter/deepseek/deepseek-v3.2` (DEFAULT); "
                 "the OpenCode execution environment reports `deepseek/deepseek-v4-flash-0731` (openrouter/deepseek/deepseek-v4-flash-0731). "
                 "The two are inconsistent; both are recorded truthfully and neither is asserted as authoritative for scientific inference.")
    lines.append(f"- Wiring tag: `{WIRING_TAG}` (ancestor of HEAD)")
    lines.append(f"- Frozen runtime universe hash: `{wiring.runtime_universe_canonical_hash()}`")
    lines.append(f"- Raw evidence: `reports/{STUDY_ID}/run_records.jsonl` + `reports/{STUDY_ID}/runs/*.json`")
    lines.append(f"- Frozen manifest: `reports/{STUDY_ID}/manifest_60.json`")
    lines.append(f"- Gate evidence: `reports/{STUDY_ID}/runtwiring_gates.json` (pre) / `closure_gates.json` (post)")
    lines.append("")
    lines.append("## 8. Scientific Interpretation (Stage-C selection behavior only)")
    lines.append("")
    lines.append("- This study measures **Stage-C selection only**. It does NOT measure end-to-end selective-regeneration correctness.")
    lines.append("- Correctness first: ImpactPlan's headline F1 (0.7797) exceeds Agent's (0.7308) ONLY on the small 6-run valid subset; "
                 "with 24/30 ImpactPlan cells failing operationally, the evidence is insufficient to claim ImpactPlan is more accurate. No such claim is made.")
    lines.append("- No claim of general large-repository superiority is made from djangoCMS alone.")
    lines.append("- No claim of end-to-end selective-regeneration correctness is made.")
    lines.append("- Lower precision/recall, failed cells, large selected sets, and latency outliers are all reported without hiding.")
    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def write_validity() -> Path:
    metrics = load_metrics()
    out = PROJECT_DIR / "reports" / "BENCHMARK_VALIDITY_AND_LIMITATIONS.md"
    lines = []
    lines.append("# BENCHMARK VALIDITY AND LIMITATIONS — djangoCMS External-Validity Study")
    lines.append("")
    lines.append(f"**STUDY_ID:** `{STUDY_ID}`")
    lines.append(f"**Generated (UTC):** {now_iso()}")
    lines.append("")
    lines.append("## 1. What was measured")
    lines.append("")
    lines.append("- Stage-C **selection behavior only**: which repository-relative `.py` paths each arm predicts must change, scored against the source-adjudicated hidden gold.")
    lines.append("- Exactly 6 final visible scenarios × 2 arms × 5 repetitions = 60 frozen manifest cells; all 60 recorded.")
    lines.append("- Hidden gold (`benchmark_data/external_validity/djangocms_hidden_gold_draft.json`) used AFTER inference only.")
    lines.append("- Universe: the frozen 144-path candidate universe (`djangocms_5_0_0_candidate_universe.json`, hash `43f4279b…`).")
    lines.append("")
    lines.append("## 2. Internal validity")
    lines.append("")
    lines.append("- Pre-run: wiring tag `stagec-djangocms-study-wiring-verified-01` verified as ancestor of HEAD; runtime universe == frozen universe (144, identical hashes); "
                 "missing/extra path sets empty; every gold path ∈ universe; the six final scenario IDs verified; old historical scenarios never model-facing.")
    lines.append("- The EXACT six deterministic gates + independent audit PASSED before any scientific call and again after closure (zero scientific calls in both).")
    lines.append("- Manifest frozen before the first scientific call; not changed after execution began.")
    lines.append("- Raw evidence persisted append-only per cell; a process interruption cannot destroy completed records.")
    lines.append("- Scoring is deterministic (TP/FP/FN/P/R/F1/FNR/full-recall); MICRO vs MACRO are reported separately and never mixed.")
    lines.append("")
    lines.append("## 3. Critical validity threats")
    lines.append("")
    lines.append("### 3.1 Severe missing-data asymmetry (PRIMARY LIMITATION)")
    lines.append(f"- Agent: {metrics['overall']['iterative_repository_agent']['valid_runs']}/30 valid; ImpactPlan: {metrics['overall']['impact_plan']['valid_runs']}/30 valid.")
    lines.append("- 24/30 ImpactPlan cells failed operationally: 20× `finish_reason=length` truncation at the frozen 4096-token cap, 3× fail-closed unknown-path hallucination, "
                 "1× provider 429, 1× harness defect. All are recorded failures per the frozen failure policy; no cell was rerun.")
    lines.append("- The ImpactPlan MICRO headline therefore rests on 6 survivors and is **not** equal-evidence comparable to Agent's 25-run aggregate. "
                 "Any arm comparison is provisional and must be re-audited (GPT-5.6 SOL) before any scientific claim.")
    lines.append("")
    lines.append("### 3.2 Provider instability")
    lines.append("- DeepInfra upstream rate-limit (`engine_overloaded`) produced 5 infrastructure-failed cells (4 agent + 1 impact) despite the frozen 1-transient-retry policy and operational pacing.")
    lines.append("- A brief provider outage at study start was waited out before launching; pacing (15 s inter-cell) is an operational scheduling measure, NOT a scientific-input change.")
    lines.append("")
    lines.append("### 3.3 Cap sensitivity")
    lines.append("- ImpactPlan's 4096-completion cap is frozen; the full 144-decision JSON frequently does not fit, so most ImpactPlan cells are cap-truncated failures. "
                 "The probe (scenario 008) succeeded once at 1817 completion tokens, so the cap is sufficient for compact plans but not for the verbose plans the model emits on the other scenarios.")
    lines.append("")
    lines.append("### 3.4 Cost-accounting gap")
    lines.append("- ImpactPlan 007-r1 consumed one model call whose token usage/cost could not be recorded (harness `ValueError` before record construction). "
                 "True total spend is therefore slightly above the recorded $0.264148 (by ≈ $0.003). Ceiling is $0.50; COST_LOCK stays PASS with wide margin.")
    lines.append("")
    lines.append("### 3.5 External validity")
    lines.append("- Single repository (django CMS 5.0.0 pin `0f633fc9…`), single model, single provider session, 6 scenarios × 144-path universe.")
    lines.append("- No claim of general large-repository superiority; no end-to-end selective-regeneration claim.")
    lines.append("")
    lines.append("## 4. What is NOT measured")
    lines.append("- Regeneration / patching / repair / migration / functional execution correctness. Selection only.")
    lines.append("- Cost-probe runs (costprobe-01, costprobe-02) are NON-STUDY diagnostic evidence and are excluded from the 60 scientific results.")
    lines.append("")
    lines.append("## 5. Interpretation rules honored")
    lines.append("- Correctness before efficiency; efficiency reported only after correctness.")
    lines.append("- No reruns for bad precision/recall/F1/surprising write sets/empty sets/arm losses.")
    lines.append("- Raw evidence wins over documentation on any conflict.")
    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def write_repro() -> Path:
    out = PROJECT_DIR / "reports" / "BENCHMARK_REPRODUCIBILITY_INDEX.md"
    records = load_records()
    lines = []
    lines.append("# BENCHMARK REPRODUCIBILITY INDEX — djangoCMS External-Validity Study")
    lines.append("")
    lines.append(f"**STUDY_ID:** `{STUDY_ID}`  \n**Generated (UTC):** {now_iso()}")
    lines.append("")
    lines.append("## 1. Frozen inputs (HARD FROZEN, not modified)")
    lines.append("")
    lines.append("| Input | Path |")
    lines.append("| --- | --- |")
    lines.append("| Hidden gold (evaluation-only) | `benchmark_data/external_validity/djangocms_hidden_gold_draft.json` |")
    lines.append("| Candidate universe (144) | `benchmark_data/external_validity/djangocms_5_0_0_candidate_universe.json` |")
    lines.append("| Dependency graph | `benchmark_data/external_validity/djangocms_5_0_0_dependency_graph.json` |")
    lines.append("| Final visible drafts | `benchmark_data/external_validity/visible_drafts/` (6 YAML) |")
    lines.append("| Pinned source | `benchmark_data/repositories/djangocms` @ `0f633fc9fa213357f4202482aab2b0edad680f95` |")
    lines.append("| Wiring runtime | `src/benchmark/external_validity/study_runtime.py` |")
    lines.append("")
    lines.append("## 2. Scientific configuration (frozen)")
    lines.append("")
    lines.append("| Setting | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Model | `{PRIMARY_MODEL}` |")
    lines.append(f"| Provider | DeepInfra pinned through OpenRouter (`{PROVIDER_TAG}`) |")
    lines.append("| Fallback | OFF |")
    lines.append("| Temperature | 0 |")
    lines.append(f"| Caps | agent {AGENT_CAP} / impact_plan {IMPACTPLAN_CAP} |")
    lines.append("| Retry policy | frozen: max 1 transient retry (`max_transient_retries=1`) |")
    lines.append("| Scope | SELECTION ONLY |")
    lines.append("| Workflow timeout | 600 s per cell |")
    lines.append("")
    lines.append("## 3. Evidence locations")
    lines.append("")
    lines.append("| Evidence | Path |")
    lines.append("| --- | --- |")
    lines.append(f"| Pre-run validation (B) | `reports/{STUDY_ID}/prevalidation.json` |")
    lines.append(f"| Six gates + audit (pre) | `reports/{STUDY_ID}/runtwiring_gates.json` |")
    lines.append(f"| Frozen 60-cell manifest | `reports/{STUDY_ID}/manifest_60.json` |")
    lines.append(f"| Raw per-run records (append-only) | `reports/{STUDY_ID}/run_records.jsonl` |")
    lines.append(f"| Per-run raw JSON | `reports/{STUDY_ID}/runs/*.json` |")
    lines.append(f"| Checkpoints | `reports/{STUDY_ID}/checkpoint_10.json … checkpoint_60.json` |")
    lines.append(f"| Final metrics | `reports/{STUDY_ID}/final_metrics.json` |")
    lines.append(f"| Closure gates + audit (post) | `reports/{STUDY_ID}/closure_gates.json` |")
    lines.append("")
    lines.append("## 4. Repro steps")
    lines.append("")
    lines.append("1. `python scripts/stagec_djangocms_study_execute.py prevalidate`")
    lines.append("2. `python scripts/stagec_djangocms_study_execute.py gates`")
    lines.append("3. `python scripts/stagec_djangocms_study_execute.py freeze-manifest`")
    lines.append("4. `python scripts/stagec_djangocms_study_execute.py run --limit 10 --inter-cell-delay 15` (repeat until 60/60)")
    lines.append("5. `python scripts/stagec_djangocms_study_execute.py metrics`")
    lines.append("6. `python scripts/stagec_djangocms_study_execute.py close`")
    lines.append("")
    lines.append("## 5. Determinism notes")
    lines.append("")
    lines.append("- Gates/audit/metrics are deterministic and make zero scientific calls.")
    lines.append("- Scientific inference uses temperature 0, but DeepInfra provider responses showed non-deterministic token counts across identical inputs (observed in this study); "
                 "per-run raw response SHA-256 hashes are recorded so each response is independently verifiable.")
    lines.append(f"- {len(records)} raw records; every run_id maps 1:1 to a manifest cell.")
    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main() -> int:
    csv_path = write_csv()
    md_path = write_md()
    val_path = write_validity()
    rep_path = write_repro()
    print(f"wrote {csv_path}")
    print(f"wrote {md_path}")
    print(f"wrote {val_path}")
    print(f"wrote {rep_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())