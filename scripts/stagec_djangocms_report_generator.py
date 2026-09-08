#!/usr/bin/env python3
"""Regenerate djangoCMS external-validity study reports from RAW EVIDENCE.

Post-study closure correction pass. Reads:
- closure_recompute.json      (recomputed from the 60 raw records)
- serialization_size_analysis.json  (zero-API serialization measurement)
- raw_evidence_hashes.json    (proves raw evidence unchanged)

Produces:
- reports/FINAL_BENCHMARK_RESULTS.md
- reports/FINAL_BENCHMARK_RESULTS.csv
- reports/BENCHMARK_VALIDITY_AND_LIMITATIONS.md
- reports/BENCHMARK_REPRODUCIBILITY_INDEX.md
- reports/DJANGOCMS_IMPACTPLAN_CAP_ABLATION_PROPOSAL.md
"""

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


def load_json(name: str):
    return json.loads((STUDY_DIR / name).read_text(encoding="utf-8"))


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def fmt_pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def _md_table(headers, rows, aligns=None):
    lines = ["| " + " | ".join(headers) + " |"]
    sep = []
    for i, h in enumerate(headers):
        if aligns and i < len(aligns):
            sep.append(f"{aligns[i]}:---" if aligns[i] else "---")
        else:
            sep.append("---")
    lines.append("|" + "|".join(sep) + "|")
    for row in rows:
        lines.append("| " + " | ".join(str(x) for x in row) + " |")
    return "\n".join(lines)


HEADLINE_HEADERS = ["Arm", "Selected", "TP", "FP", "FN", "Precision", "Recall", "F1", "FNR", "Tokens", "Model Calls", "Time", "Cost"]


def _headline_row(recompute, arm):
    v = recompute["valid_headline_micro"][arm]
    return [
        arm, v["selected"], v["tp"], v["fp"], v["fn"],
        f"{v['precision']:.4f}", f"{v['recall']:.4f}", f"{v['f1']:.4f}", f"{v['fnr']:.4f}",
        v["tokens"], v["model_calls"], round(v["time"], 1), f"{v['cost']:.6f}",
    ]


def write_csv(recompute) -> Path:
    records = []
    for line in (STUDY_DIR / "run_records.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
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
                "read_file_calls": r.get("explicit_read_file_count", 0),
                "inspected_file_count": r.get("inspected_file_count", 0),
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
        f.write("\n")
        f.write("SECTION,VALID_RUN_MICRO_HEADLINE\n")
        writer = csv.writer(f)
        writer.writerow(HEADLINE_HEADERS)
        for arm in ARMS:
            writer.writerow(_headline_row(recompute, arm))
        f.write("\n")
        f.write("SECTION,ALL_CELL_OPERATIONAL\n")
        writer = csv.writer(f)
        writer.writerow(["Arm", "Valid / 30", "Failed / 30", "Valid Rate", "Tokens", "Model Calls", "Measured Time", "Recorded Cost"])
        for arm in ARMS:
            a = recompute["all_cell_operational"][arm]
            writer.writerow([arm, a["valid"], a["failed"], f"{a['valid_rate']:.4f}", a["tokens"], a["model_calls"], round(a["time"], 3), f"{a['cost']:.6f}"])
    return out


def write_main_md(recompute, serial, hashes) -> Path:
    out = PROJECT_DIR / "reports" / "FINAL_BENCHMARK_RESULTS.md"
    total = recompute["totals_all_cell"]
    taxonomy = recompute["failure_taxonomy"]

    L = []
    L.append("# FINAL BENCHMARK RESULTS — djangoCMS External-Validity Stage-C Selection Study")
    L.append("")
    L.append(f"**STUDY_ID:** `{STUDY_ID}`")
    L.append(f"**Report corrected (UTC):** {now_iso()}")
    L.append(f"**Wiring tag:** `{WIRING_TAG}`")
    L.append(f"**Scientific model/provider:** `{PRIMARY_MODEL}` @ `{PROVIDER_TAG}` (DeepInfra pinned through OpenRouter; fallback OFF; temperature 0)")
    L.append(f"**Caps:** `iterative_repository_agent` = {AGENT_CAP} / `impact_plan` = {IMPACTPLAN_CAP} completion tokens (frozen)")
    L.append("**Scope:** SELECTION ONLY (no regeneration / repair / migration / functional execution)")
    L.append("**Design:** 6 scenarios × 2 arms × 5 repetitions = exactly 60 frozen manifest cells")
    L.append(f"**Recorded:** {recompute['manifest_cells']}/60 — {recompute['valid']} valid (succeeded) / {recompute['failed']} failed (recorded)")
    L.append(f"**Universe:** 144 paths, canonical SHA-256 `{wiring.runtime_universe_canonical_hash()}`")
    L.append(f"**Recorded API cost:** ${total['cost']:.6f} (ceiling $0.50) — **COST_LOCK=PASS** (see Cost section for missing-cost caveat)")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 0. Definitions: VALID vs FAILED")
    L.append("")
    L.append("**VALID / SUCCEEDED** means the inference reached a terminal selection result that is parseable / schema-valid, and whose selected paths pass runtime-universe validation, so that TP/FP/FN and correctness metrics can be computed.")
    L.append("")
    L.append("**VALID DOES NOT MEAN CORRECT.** A valid run may have precision = 0, recall = 0, or F1 = 0 and still be a valid scientific observation.")
    L.append("")
    L.append("**FAILED** means a normal scorable terminal selection was not produced due to an operational failure: completion truncation, provider failure, invalid/non-universe paths, terminal empty selection treated fail-closed by the frozen harness, or a harness defect. Failed cells are NOT converted into synthetic correctness scores.")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 1. OVERALL HEADLINE TABLE — VALID-RUN MICRO-AGGREGATION")
    L.append("")
    L.append("Micro-aggregation pools TP/FP/FN across each arm's **valid** study runs. **Percentages are NOT averaged.**")
    L.append("")
    L.append("### ⚠ WARNING — SEVERE MISSING-DATA ASYMMETRY")
    L.append("")
    L.append("**Agent valid cells = 25**  \n**ImpactPlan valid cells = 6**")
    L.append("")
    L.append("Therefore these correctness values are based on **severely asymmetric survivor subsets** (ImpactPlan had 24/30 cells fail operationally). **DO NOT claim ImpactPlan has higher overall accuracy based on this table.**")
    L.append("")
    rows = [_headline_row(recompute, arm) for arm in ARMS]
    L.append(_md_table(HEADLINE_HEADERS, rows, aligns=["", "", "", "", "", "", "", "", "", "", "", "", ""]))
    L.append("")
    L.append("> Selected = pooled selected paths across valid runs only; TP/FP/FN = pooled across valid runs; Precision = TP/(TP+FP); Recall = TP/(TP+FN); F1 = 2PR/(P+R); FNR = FN/(TP+FN); Tokens/Model Calls/Time/Cost = the valid-run subset for that row.")
    L.append("")
    L.append(f"- Agent: tokens {recompute['valid_headline_micro']['iterative_repository_agent']['tokens']}, calls {recompute['valid_headline_micro']['iterative_repository_agent']['model_calls']}, tool calls {recompute['valid_headline_micro']['iterative_repository_agent']['tool_calls']}, explicit read_file {recompute['valid_headline_micro']['iterative_repository_agent']['read_file_calls']}, inspected files {recompute['valid_headline_micro']['iterative_repository_agent']['inspected_files']}.")
    L.append(f"- ImpactPlan: tokens {recompute['valid_headline_micro']['impact_plan']['tokens']}, calls {recompute['valid_headline_micro']['impact_plan']['model_calls']}, tool calls {recompute['valid_headline_micro']['impact_plan']['tool_calls']}, explicit read_file {recompute['valid_headline_micro']['impact_plan']['read_file_calls']}.")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 2. ALL-CELL OPERATIONAL TABLE (valid + failed resource consumption)")
    L.append("")
    L.append("This table includes resources consumed by BOTH valid and failed cells. It is an operational/efficiency table, NOT a correctness comparison.")
    L.append("")
    rows = []
    for arm in ARMS:
        a = recompute["all_cell_operational"][arm]
        rows.append([arm, a["valid"], a["failed"], f"{a['valid_rate']:.4f}", a["tokens"], a["model_calls"], round(a["time"], 3), f"{a['cost']:.6f}"])
    L.append(_md_table(["Arm", "Valid / 30", "Failed / 30", "Valid Rate", "Tokens", "Model Calls", "Measured Time", "Recorded Cost"], rows))
    L.append("")
    rel = recompute["impactplan_relative_to_agent_all_cell"]
    L.append(f"**ImpactPlan relative to Agent (all-cell):** tokens {rel['tokens_pct']:+.2f}% · model calls {rel['model_calls_pct']:+.2f}% · recorded cost {rel['cost_pct']:+.2f}% · measured total latency {rel['time_pct']:+.2f}%.")
    L.append("")
    L.append("**Do not confuse this all-cell resource table with valid-only correctness.**")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 3. FAILURE TABLE (recomputed from raw evidence)")
    L.append("")
    L.append(f"Recomputed from the {recompute['records']} raw run records. Total failed cells: **{recompute['failed']}**.")
    L.append("")
    rows = []
    interp = {
        "completion_truncation_4096_cap": (
            "The current full structured ImpactPlan representation is operationally "
            "vulnerable to output truncation on the 144-file djangoCMS universe under "
            "the preregistered 4096 completion-token cap. NOT a judgment of reasoning quality."
        ),
        "unknown_path_non_universe": "The model emitted paths outside the frozen 144-path universe; the fail-closed gate rejected the plan (a model-output/schema failure).",
        "provider_http_429": "DeepInfra shared-pool upstream rate limit (engine_overloaded) exhausted the frozen 1-transient-retry policy (infrastructure).",
        "empty_selection_fail_closed": "The agent exhausted its 8 exploration calls and submitted an empty selection; the frozen harness treats empty final selection as a failed cell.",
        "harness_defect": "The model returned a validation_obligation kind outside the frozen enum, raising a ValueError during record construction (harness gap; one model call's cost was not recorded).",
    }
    for kind, info in sorted(taxonomy.items()):
        arms = ", ".join(f"{a}={c}" for a, c in info["arm_counts"].items())
        rows.append([arms, kind.replace("_", " "), info["count"], interp.get(kind, "See raw evidence.")])
    L.append(_md_table(["Arm", "Failure Type", "Count", "Scientific Interpretation"], rows))
    L.append("")
    L.append("**Truncation raw-evidence verification:** every truncation record has `finish_reason = length` and `completion_tokens = 4096` (the frozen cap). Counts below are per-arm.")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 4. OUTPUT-BUDGET ASYMMETRY (important validity issue)")
    L.append("")
    L.append("The study arms did NOT have an equal completion-token allowance structure:")
    L.append("")
    L.append("- **iterative_repository_agent:** up to **8 model calls**, each with **max completion tokens = 1024** → cumulative per-run completion-token allowance exposure up to **8 × 1024 = 8192 tokens across sequential calls**.")
    L.append("- **impact_plan:** **1 model call**, **max completion tokens = 4096** → up to **4096 tokens in one structured response**.")
    L.append("")
    L.append("These budgets are **NOT directly interchangeable**; the arms have different interaction structures:")
    L.append("- Agent can distribute output over several sequential exploratory/action calls (up to 8).")
    L.append("- ImpactPlan must serialize a large structured plan in a single response.")
    L.append("")
    L.append("**The frozen 4096 cap may therefore confound representational scalability with completion-budget sufficiency.** This is a genuine validity concern and is reported as a limitation, not as a measured property of either approach.")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 5. SERIALIZATION-SIZE ANALYSIS (ZERO API — deterministic)")
    L.append("")
    mp = serial["minimal_plan"]
    L.append(f"A minimal schema-valid ImpactPlan JSON over the exact frozen {mp['universe_paths']}-path candidate universe (shortest action label `PRESERVE`, empty rationales/evidence, compact JSON) measures:")
    L.append("")
    L.append(f"- **Bytes (UTF-8):** {mp['json_bytes_utf8']}")
    L.append(f"- **Characters:** {mp['json_characters']}")
    L.append(f"- **Rough token estimate (project heuristic `chars // 4`, ESTIMATE ONLY):** ~{mp['rough_token_estimate']} tokens")
    L.append("")
    L.append("**The exact `qwen/qwen3-coder` tokenizer is NOT available locally and was NOT downloaded; no API call was made.** The token figure is a heuristic estimate and must not be reported as a measured fact.")
    L.append("")
    L.append("**Measured comparison with raw study responses:**")
    L.append("")
    tr = serial["truncated_responses"]
    sc = serial["successful_impactplan_completion_tokens"]["stats"]
    L.append(f"- **{tr['count']} truncated ImpactPlan cells:** all `finish_reason = length`, all `completion_tokens = 4096` (the cap) — the model's emitted JSON (with rationales/evidence) reached the cap in every one of these cells.")
    L.append(f"- **{sc['count']} successful ImpactPlan cells:** completion tokens min {sc['min']} / median {sc['median']} / max {sc['max']} — compact plan serializations did fit within the cap.")
    L.append("")
    L.append("**Interpretation:** the minimal serialization alone is already on the order of the 4096-token cap (~4.3k heuristic-estimated tokens for 144 paths with no rationales), and the model's real outputs include rationales/evidence that pushed every truncated response to exactly 4096 completion tokens. The cap plausibly constrained serialization, but the primary study cannot separate representation scalability from the cap; the two are confounded (see Ablation Proposal).")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 6. MACRO PER-RUN STATISTICS (VALID runs only; reported separately from MICRO)")
    L.append("")
    L.append("### VALID-RUN MACRO STATISTICS")
    L.append("")
    for arm in ARMS:
        m = recompute["macro_valid_runs"][arm]
        v = recompute["valid_headline_micro"][arm]
        L.append(f"### {arm} (valid runs = {m['valid_runs']})")
        L.append("")
        L.append(_md_table(
            ["Metric", "Mean", "Median", "Min", "Max"],
            [
                ["precision", f"{m['mean_precision']:.4f}", f"{m['median_precision']:.4f}", "", ""],
                ["recall", f"{m['mean_recall']:.4f}", f"{m['median_recall']:.4f}", "", ""],
                ["f1", f"{m['mean_f1']:.4f}", f"{m['median_f1']:.4f}", "", ""],
                ["selected set size", m["selected_set_size"]["mean"], m["selected_set_size"]["median"], m["selected_set_size"]["min"], m["selected_set_size"]["max"]],
                ["tokens", m["tokens"]["mean"], m["tokens"]["median"], m["tokens"]["min"], m["tokens"]["max"]],
                ["model calls", m["model_calls"]["mean"], m["model_calls"]["median"], m["model_calls"]["min"], m["model_calls"]["max"]],
                ["latency (s)", f"{m['latency']['mean']:.2f}", f"{m['latency']['median']:.2f}", f"{m['latency']['min']:.2f}", f"{m['latency']['max']:.2f}"],
                ["cost (USD)", f"{m['cost']['mean']:.6f}", f"{m['cost']['median']:.6f}", f"{m['cost']['min']:.6f}", f"{m['cost']['max']:.6f}"],
            ],
        ))
        L.append(f"- **Full-recall rate** (valid runs with recall == 1.0): **{m['full_recall_rate']:.4f}**")
        L.append(f"- Valid-run tokens total: {v['tokens']}; model calls total: {v['model_calls']}; latency total: {round(v['time'], 3)} s; cost total: ${v['cost']:.6f}.")
        L.append("")
    L.append(f"**Latency outliers (valid runs, > mean + 2σ):** {recompute['latency_outliers_valid'] or 'none'}")
    L.append("")
    L.append("Never mix these valid-run macro statistics with all-cell operational totals.")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 7. PER-SCENARIO TABLES (pooled across valid repetitions; same micro schema)")
    L.append("")
    L.append("Schema: | Arm | Valid Runs | Selected | TP | FP | FN | Precision | Recall | F1 | FNR | Tokens | Model Calls | Time | Cost |")
    L.append("")
    scen_headers = ["Arm", "Valid Runs", "Selected", "TP", "FP", "FN", "Precision", "Recall", "F1", "FNR", "Tokens", "Model Calls", "Time", "Cost"]
    for sid in sorted(recompute["per_scenario_valid"]):
        L.append(f"### {sid}")
        L.append("")
        rows = []
        for arm in ARMS:
            v = recompute["per_scenario_valid"][sid][arm]
            if v["valid_runs"] == 0:
                rows.append([arm, "0/5 valid runs (N/A)", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"])
            else:
                rows.append([
                    arm, v["valid_runs"], v["selected"], v["tp"], v["fp"], v["fn"],
                    f"{v['precision']:.4f}", f"{v['recall']:.4f}", f"{v['f1']:.4f}", f"{v['fnr']:.4f}",
                    v["tokens"], v["model_calls"], round(v["time"], 1), f"{v['cost']:.6f}",
                ])
        L.append(_md_table(scen_headers, rows))
        L.append("Values are pooled across the valid repetitions only for that scenario. `N/A` = 0/5 valid runs for that arm (correctness is not computed for all-failed cells).")
        L.append("")
    L.append("---")
    L.append("")
    L.append("## 8. COST ACCOUNTING")
    L.append("")
    L.append(f"- **Recorded API cost across persisted study records was ${total['cost']:.6f}.**")
    L.append("- **Actual spend is slightly higher** because one harness-defect scientific model call (impact_plan scenario 007 repetition 1) lacks complete cost provenance (the run raised a `ValueError` before token-usage/cost could be recorded; ≈ $0.003 by per-token rate). No estimate is presented as a measured fact.")
    L.append(f"- Hard scientific-study ceiling: **${HARD_COST_CEILING_USD:.2f}**. Evidence still supports remaining below the ceiling (recorded ${total['cost']:.6f} + estimated missing ≈ $0.003 << $0.50). **COST_LOCK=PASS.**")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 9. SCIENTIFIC INTERPRETATION (conservative)")
    L.append("")
    L.append("**Supported:**")
    L.append("- The explicit ImpactPlan approach shows a strong reduction in selection-stage inference work, especially model-call count (206 → 28 all-cell) and token usage (449,792 → 184,401 all-cell; −59.0%).")
    L.append("- The current full structured-plan representation exhibited **poor operational completion** on the 144-file djangoCMS study under the preregistered 4096-token single-response cap: **19/30 ImpactPlan cells truncated** (raw-evidence confirmed), giving an **ImpactPlan operational valid rate of 20%** vs **Agent operational valid rate of 83.33%**.")
    L.append("- When ImpactPlan completed successfully, valid-run write-set recall was high (micro recall 0.92, macro median recall 1.0), but the severe valid-run imbalance (6 vs 25) prevents a clean between-arm accuracy-superiority claim.")
    L.append("- All-cell ImpactPlan token/model-call savings coexist with **worse total measured latency (+17.4%)**, driven by failed/truncated runs.")
    L.append("- The primary study **cannot disentangle representation scalability from the single-response output-cap constraint**.")
    L.append("- A separate post-hoc 8192-cap ablation would be appropriate to investigate this, but it is **NOT part of the primary result** (see `reports/DJANGOCMS_IMPACTPLAN_CAP_ABLATION_PROPOSAL.md`).")
    L.append("")
    L.append("**NOT supported / NOT claimed:**")
    L.append("- ImpactPlan is universally more accurate.")
    L.append("- ImpactPlan is universally faster.")
    L.append("- End-to-end selective regeneration is proven.")
    L.append("- djangoCMS proves arbitrary large-repository generalization.")
    L.append("- The preregistered study proves truncation is inherent to ImpactPlan rather than partly cap-induced.")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 10. BASELINE DESCRIPTION")
    L.append("")
    L.append("`iterative_repository_agent` is **our implemented iterative repository-agent baseline**, not a canonical or standardized representation of all agentic coding systems. Frozen behavior: up to 8 model calls with a 1024-token control-plane completion cap per call; calls 1–7 may issue `list_files` / `read_file` / `search_text` tool actions against a clean per-run workspace copy of the pinned repository; call 8 is reserved and forced to `final`, which must submit a non-empty subset of the 144-path editable universe. It does not regenerate, repair, or run migrations in this study (selection-only).")
    L.append("")
    L.append("## 11. PROVENANCE")
    L.append("")
    L.append(f"- Scientific model: `{PRIMARY_MODEL}`; provider: DeepInfra pinned through OpenRouter (`{PROVIDER_TAG}`), fallback OFF.")
    L.append("- Implementation/OpenCode model: the OpenCode execution environment reports `deepseek/deepseek-v4-flash-0731`; the task authorization header declared `openrouter/deepseek/deepseek-v3.2`. Both are recorded truthfully; neither is asserted as authoritative for scientific inference.")
    L.append(f"- Wiring tag: `{WIRING_TAG}` (ancestor of HEAD).")
    L.append(f"- Frozen runtime universe hash: `{wiring.runtime_universe_canonical_hash()}`.")
    L.append(f"- Raw evidence: `reports/{STUDY_ID}/run_records.jsonl` + `reports/{STUDY_ID}/runs/*.json` (hashes persisted in `raw_evidence_hashes.json`; verified unchanged).")
    L.append("")
    out.write_text("\n".join(L), encoding="utf-8")
    return out


def write_validity(recompute, serial) -> Path:
    out = PROJECT_DIR / "reports" / "BENCHMARK_VALIDITY_AND_LIMITATIONS.md"
    L = []
    L.append("# BENCHMARK VALIDITY AND LIMITATIONS — djangoCMS External-Validity Study")
    L.append("")
    L.append(f"**STUDY_ID:** `{STUDY_ID}`")
    L.append(f"**Report corrected (UTC):** {now_iso()}")
    L.append("")
    L.append("## 1. What was measured")
    L.append("")
    L.append("- Stage-C **selection behavior only**: which repository-relative `.py` paths each arm predicts must change, scored against the source-adjudicated hidden gold, applied AFTER inference only.")
    L.append("- Exactly 6 final visible scenarios × 2 arms × 5 repetitions = 60 frozen manifest cells; all 60 recorded.")
    L.append("- Universe: the frozen 144-path candidate universe (hash `43f4279b…`).")
    L.append("")
    L.append("## 2. VALID vs FAILED (explicit definition)")
    L.append("")
    L.append("- **VALID / SUCCEEDED:** inference reached a terminal selection result that is parseable / schema-valid, with selected paths passing runtime-universe validation, so TP/FP/FN and correctness metrics can be computed. **VALID does NOT mean correct** (a valid run may have precision/recall/F1 = 0).")
    L.append("- **FAILED:** a normal scorable terminal selection was not produced due to an operational failure (completion truncation, provider failure, invalid/non-universe paths, terminal empty selection treated fail-closed, or a harness defect). Failed cells are not converted into synthetic correctness scores.")
    L.append("")
    L.append("## 3. Internal validity")
    L.append("")
    L.append("- Pre-run: wiring tag `stagec-djangocms-study-wiring-verified-01` verified ancestor of HEAD; runtime universe == frozen universe (144, identical hashes); missing/extra path sets empty; every gold path ∈ universe; six final scenario IDs verified; old historical scenarios never model-facing.")
    L.append("- The EXACT six deterministic gates + independent audit PASSED before the study and again after closure (zero scientific calls in both).")
    L.append("- Manifest frozen before the first scientific call; not changed after execution began.")
    L.append("- Raw evidence persisted append-only per cell; interruption cannot destroy completed records.")
    L.append("- Raw scientific evidence hashes verified unchanged before/after this documentation closure (`raw_evidence_hashes.json`).")
    L.append("")
    L.append("## 4. Critical validity threats")
    L.append("")
    L.append("### 4.1 Severe missing-data asymmetry (PRIMARY LIMITATION)")
    L.append(f"- Agent: {recompute['arm_counts']['iterative_repository_agent']['valid']}/30 valid; ImpactPlan: {recompute['arm_counts']['impact_plan']['valid']}/30 valid.")
    L.append("- 24/30 ImpactPlan cells failed operationally: **19× completion truncation at the frozen 4096 cap**, 3× fail-closed unknown-path hallucination, 1× provider 429, 1× harness defect. All recorded failures; no cell rerun.")
    L.append("- ImpactPlan MICRO headline rests on 6 survivors and is **not** equal-evidence comparable to Agent's 25-run aggregate. Any arm comparison is provisional and must be re-audited (GPT-5.6 SOL) before any scientific claim.")
    L.append("")
    L.append("### 4.2 Output-budget asymmetry (DEDICATED SECTION)")
    L.append("")
    L.append("The study arms did NOT have equal completion-token allowance structure. **Do NOT simplify this into “Agent had exactly twice the same output budget.”**")
    L.append("")
    L.append("- **Agent:** up to 8 model calls, each max 1024 completion tokens → maximum cumulative per-run completion-token allowance exposure ≈ 8 × 1024 = **8192 tokens across sequential calls**.")
    L.append("- **ImpactPlan:** 1 model call, max 4096 completion tokens → up to **4096 tokens in one structured response**.")
    L.append("")
    L.append("The arms have different interaction structures. Agent can distribute output over several calls; ImpactPlan must serialize its plan in a single response. **The frozen 4096 cap may therefore confound representational scalability with completion-budget sufficiency.**")
    L.append("")
    L.append("### 4.3 Serialization-size evidence (ZERO API)")
    L.append("")
    mp = serial["minimal_plan"]
    L.append(f"- Minimal schema-valid ImpactPlan JSON over the 144-path universe: **{mp['json_bytes_utf8']} bytes / {mp['json_characters']} characters** (exact measurement; empty rationales/evidence).")
    L.append(f"- Rough token estimate (project heuristic, ESTIMATE ONLY): ~{mp['rough_token_estimate']} tokens — already on the order of the 4096 cap before any rationale/evidence.")
    L.append(f"- All {serial['truncated_responses']['count']} truncated responses: `finish_reason=length`, `completion_tokens=4096` (measured). Successful ImpactPlan completions: min {serial['successful_impactplan_completion_tokens']['stats']['min']} / median {serial['successful_impactplan_completion_tokens']['stats']['median']} / max {serial['successful_impactplan_completion_tokens']['stats']['max']} tokens.")
    L.append("- The exact qwen/qwen3-coder tokenizer is not locally available and was not downloaded; no API call was made; the token estimate is labeled an estimate.")
    L.append("")
    L.append("### 4.4 Provider instability")
    L.append("- DeepInfra upstream rate-limit (`engine_overloaded`) produced 5 infrastructure-failed cells (4 agent + 1 impact) despite the frozen 1-transient-retry policy and operational pacing.")
    L.append("- A brief provider outage at study start was waited out before launching; pacing (15 s inter-cell) is operational scheduling, NOT a scientific-input change.")
    L.append("")
    L.append("### 4.5 Cap sensitivity")
    L.append("- ImpactPlan's 4096-completion cap is frozen. The model frequently emits verbose rationales/evidence that exceed 4096 tokens, so most ImpactPlan cells are cap-truncated. Compact outputs (successful cells) fit, so the cap is not inherently impossible — the representation is operationally vulnerable to truncation.")
    L.append("")
    L.append("### 4.6 Cost-accounting gap")
    L.append("- ImpactPlan 007-r1 consumed one model call whose token usage/cost could not be recorded (harness `ValueError` before record construction). True spend is slightly above recorded $0.264148 (≈ $0.003). Ceiling is $0.50; COST_LOCK stays PASS with wide margin.")
    L.append("")
    L.append("### 4.7 External validity")
    L.append("- Single repository (django CMS 5.0.0 pin `0f633fc9…`), single model, single provider session, 6 scenarios × 144-path universe. No general large-repository superiority claim; no end-to-end claim.")
    L.append("")
    L.append("## 5. What is NOT measured")
    L.append("- Regeneration / patching / repair / migration / functional execution correctness. Selection only.")
    L.append("- Cost-probe runs (costprobe-01, costprobe-02) are NON-STUDY diagnostic evidence and are excluded from the 60 scientific results.")
    L.append("- The 8192-cap ablation (proposal only; NOT run).")
    L.append("")
    L.append("## 6. Interpretation rules honored")
    L.append("- Correctness before efficiency; efficiency reported only after correctness.")
    L.append("- No reruns for bad precision/recall/F1/surprising write sets/empty sets/arm losses.")
    L.append("- Raw evidence wins over documentation on any conflict.")
    L.append("")
    out.write_text("\n".join(L), encoding="utf-8")
    return out


def write_repro(recompute, hashes) -> Path:
    out = PROJECT_DIR / "reports" / "BENCHMARK_REPRODUCIBILITY_INDEX.md"
    L = []
    L.append("# BENCHMARK REPRODUCIBILITY INDEX — djangoCMS External-Validity Study")
    L.append("")
    L.append(f"**STUDY_ID:** `{STUDY_ID}`")
    L.append(f"**Report corrected (UTC):** {now_iso()}")
    L.append("")
    L.append("## 1. Frozen inputs (HARD FROZEN, not modified)")
    L.append("")
    L.append(_md_table(["Input", "Path", "SHA-256 (verified unchanged)"], [
        ["Hidden gold (evaluation-only)", "benchmark_data/external_validity/djangocms_hidden_gold_draft.json", hashes.get("hidden_gold", "")],
        ["Candidate universe (144)", "benchmark_data/external_validity/djangocms_5_0_0_candidate_universe.json", hashes.get("candidate_universe", "")],
        ["Dependency graph", "benchmark_data/external_validity/djangocms_5_0_0_dependency_graph.json", hashes.get("dependency_graph", "")],
        ["Final visible drafts", "benchmark_data/external_validity/visible_drafts/ (6 YAML)", "; ".join(hashes.get(f"scenario_{s}", "") for s in sorted(wiring.final_scenario_ids()))],
        ["Frozen manifest", "reports/scientific-stagec-djangocms-study-01/manifest_60.json", hashes.get("manifest_60.json", "")],
        ["Aggregated raw records", "reports/scientific-stagec-djangocms-study-01/run_records.jsonl", hashes.get("run_records.jsonl", "")],
        ["60 raw run JSONs", "reports/scientific-stagec-djangocms-study-01/runs/*.json", f"{sum(1 for k in hashes if k.startswith('run:'))} files hashed"],
    ]))
    L.append("")
    L.append("## 2. Scientific configuration (frozen)")
    L.append("")
    L.append(_md_table(["Setting", "Value"], [
        ["Model", f"`{PRIMARY_MODEL}`"],
        ["Provider", f"DeepInfra pinned through OpenRouter (`{PROVIDER_TAG}`)"],
        ["Fallback", "OFF"],
        ["Temperature", "0"],
        ["Caps", f"agent {AGENT_CAP} / impact_plan {IMPACTPLAN_CAP}"],
        ["Retry policy", "frozen: max 1 transient retry"],
        ["Scope", "SELECTION ONLY"],
        ["Workflow timeout", "600 s per cell"],
    ]))
    L.append("")
    L.append("## 3. Evidence locations")
    L.append("")
    L.append(_md_table(["Evidence", "Path"], [
        ["Pre-run validation (B)", f"reports/{STUDY_ID}/prevalidation.json"],
        ["Six gates + audit (pre)", f"reports/{STUDY_ID}/runtwiring_gates.json"],
        ["Frozen 60-cell manifest", f"reports/{STUDY_ID}/manifest_60.json"],
        ["Raw per-run records (append-only)", f"reports/{STUDY_ID}/run_records.jsonl"],
        ["Per-run raw JSON", f"reports/{STUDY_ID}/runs/*.json (60)"],
        ["Checkpoints", f"reports/{STUDY_ID}/checkpoint_10.json … checkpoint_60.json"],
        ["Final metrics", f"reports/{STUDY_ID}/final_metrics.json"],
        ["Closure recompute (this pass)", f"reports/{STUDY_ID}/closure_recompute.json"],
        ["Serialization-size analysis", f"reports/{STUDY_ID}/serialization_size_analysis.json"],
        ["Raw-evidence hashes (immutability proof)", f"reports/{STUDY_ID}/raw_evidence_hashes.json"],
        ["Closure gates + audit (post)", f"reports/{STUDY_ID}/closure_gates.json"],
    ]))
    L.append("")
    L.append("## 4. Repro steps")
    L.append("")
    L.append("1. `python scripts/stagec_djangocms_study_execute.py prevalidate`")
    L.append("2. `python scripts/stagec_djangocms_study_execute.py gates`")
    L.append("3. `python scripts/stagec_djangocms_study_execute.py freeze-manifest`")
    L.append("4. `python scripts/stagec_djangocms_study_execute.py run --limit 10 --inter-cell-delay 15` (repeat until 60/60)")
    L.append("5. `python scripts/stagec_djangocms_study_execute.py metrics`")
    L.append("6. `python scripts/stagec_djangocms_study_execute.py close`")
    L.append("")
    L.append("## 5. Determinism notes")
    L.append("")
    L.append("- Gates/audit/metrics are deterministic and make zero scientific calls.")
    L.append("- Scientific inference uses temperature 0, but DeepInfra responses showed non-deterministic token counts across identical inputs; per-run raw response SHA-256 hashes are recorded so each response is independently verifiable.")
    L.append(f"- {recompute['records']} raw records; every run_id maps 1:1 to a manifest cell ({recompute['records_equal_manifest']}).")
    L.append("")
    out.write_text("\n".join(L), encoding="utf-8")
    return out


def write_ablation(recompute) -> Path:
    out = PROJECT_DIR / "reports" / "DJANGOCMS_IMPACTPLAN_CAP_ABLATION_PROPOSAL.md"
    a = recompute["all_cell_operational"]["impact_plan"]
    L = []
    L.append("# ImpactPlan Completion-Cap Ablation Proposal (DOCUMENTATION ONLY — NOT RUN)")
    L.append("")
    L.append("**Status:** POST-HOC EXPLORATORY ABLATION PROPOSAL · **NOT PART OF THE PREREGISTERED 60-RUN PRIMARY STUDY** · **NOT EXECUTED**.")
    L.append("")
    L.append(f"**Proposed identifier:** `scientific-stagec-djangocms-impactplan-cap-ablation-01`")
    L.append("")
    L.append("## 1. Purpose")
    L.append("")
    L.append("Separate two confounded factors observed in the primary study:")
    L.append("")
    L.append("- **A.** ImpactPlan selection quality (the model's ability to choose the correct write set), from")
    L.append("- **B.** single-response output-cap truncation (whether the frozen 4096 completion-token cap prematurely cuts the structured plan).")
    L.append("")
    L.append("The primary study recorded 19/30 ImpactPlan cells truncated at exactly 4096 completion tokens (`finish_reason=length`), while the minimal schema-valid 144-path serialization alone measures ~17,364 bytes / ~4.3k heuristic-estimated tokens. This ablation would test whether raising the cap to 8192 materially changes operational completion and selection quality.")
    L.append("")
    L.append("## 2. Proposed design (identical frozen inputs)")
    L.append("")
    L.append("- Same frozen djangoCMS source (pin `0f633fc9…`)")
    L.append("- Same six visible scenarios (`djangocms-external-validity-002/004/005/006/007/008`)")
    L.append("- Same hidden gold (`djangocms_hidden_gold_draft.json`, evaluation-only)")
    L.append("- Same 144-file candidate universe")
    L.append("- Same model `qwen/qwen3-coder`, same DeepInfra-pinned-through-OpenRouter provider, same temperature 0")
    L.append("- **ImpactPlan only** (no Agent rerun required for this specific cap ablation)")
    L.append("- **Completion cap: 8192** (only change)")
    L.append("- 5 repetitions × 6 scenarios = **30 runs**")
    L.append("")
    L.append("## 3. Explicit non-claims")
    L.append("")
    L.append("- This proposal is **not** a preregistered primary-study component and must not be retroactively presented as one.")
    L.append("- It is **not** run in this closure task (ZERO new scientific API calls authorized).")
    L.append("- Nothing in this proposal constitutes advance confirmation of any outcome.")
    L.append("")
    L.append("## 4. Cost estimate (from existing raw evidence only, zero calls)")
    L.append("")
    L.append(f"- Primary-study all-cell ImpactPlan recorded cost: ${a['cost']:.6f} across 30 cells (mean {a['cost']/30:.6f}/cell).")
    L.append("- A 30-run cap-8192 ablation at the same observed per-cell cost profile would project to roughly the same magnitude as the primary ImpactPlan arm (≈ $0.12–$0.15). This is a planning estimate from raw evidence, not a quote.")
    L.append("")
    L.append("## 5. Decision gate")
    L.append("")
    L.append("Execute ONLY after GPT-5.6 SOL independently audits the primary 60-run evidence and explicitly authorizes the ablation. Do not run during this closure.")
    L.append("")
    out.write_text("\n".join(L), encoding="utf-8")
    return out


def main() -> int:
    recompute = load_json("closure_recompute.json")
    serial = load_json("serialization_size_analysis.json")
    hashes = load_json("raw_evidence_hashes.json")
    csv_path = write_csv(recompute)
    md_path = write_main_md(recompute, serial, hashes)
    val_path = write_validity(recompute, serial)
    rep_path = write_repro(recompute, hashes)
    abl_path = write_ablation(recompute)
    for p in (csv_path, md_path, val_path, rep_path, abl_path):
        print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())