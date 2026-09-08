#!/usr/bin/env python3
"""Update project documentation files with the djangoCMS study closure truth."""

from __future__ import annotations
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

STUDY_ID = "scientific-stagec-djangocms-01"
TAG = "stagec-djangocms-study-wiring-verified-01"
MODEL = "qwen/qwen3-coder"
PROVIDER = "DeepInfra pinned through OpenRouter (deepinfra/turbo)"
COST = "$0.264148"
TOTAL_TOKENS = "634,193"
TOTAL_CALLS = "234"

DECISION_ENTRY = """
## Decision D055 - DJANGOCMS-EXTERNAL-VALIDITY-STUDY-01: final 60-run Stage-C selection study (D055)

- **Date:** 2026-09-08
- **Decision ID:** D055
- **Status:** ACCEPTED / COMPLETED (recorded); awaiting GPT-5.6 SOL independent audit before any tag decision.
- **Category:** Scientific Study (Stage-C external-validity selection, djangoCMS)
- **Description:** Executed the frozen 60-run scientific study `scientific-stagec-djangocms-01` on the research branch `research/djangocms-external-validity-prep-01`: 6 final visible scenarios (djangocms-external-validity-002/004/005/006/007/008) x 2 arms (iterative_repository_agent cap 1024 / impact_plan cap 4096) x 5 repetitions = exactly 60 frozen manifest cells; model `qwen/qwen3-coder` @ DeepInfra pinned through OpenRouter, fallback OFF, temperature 0, selection-only, frozen 1-transient-retry policy. Pre-run: wiring tag `stagec-djangocms-study-wiring-verified-01` verified ancestor of HEAD; runtime universe == frozen 144-path universe (canonical hash `43f4279b...`); the EXACT six deterministic gates + independent audit PASSED before and after (zero scientific calls). 60/60 cells recorded append-only; 31 succeeded / 29 failed. Agent: 25/30 valid (micro P 0.6463 / R 0.8407 / F1 0.7308, 147 selected, 432,057 tokens, 198 calls, 2216.0 s, $0.135316). ImpactPlan: 6/30 valid (micro P 0.6765 / R 0.9200 / F1 0.7797, 34 selected, 32,560 tokens, 6 calls, 382.4 s, $0.018714) — ImpactPlan valid subset is small (24/30 cells failed: 4096-cap truncation, unknown-path hallucination, 1x429, 1x harness defect) so no between-arm accuracy claim is made. Total recorded cost $0.264148 <= $0.50 ceiling (COST_LOCK=PASS). No scientific cell rerun; no run 61; raw evidence preserved.
- **Rationale:** The djangoCMS external-validity preparation, source-adjudicated gold, 144-file candidate universe, AST graph, and final visible scenarios were frozen; this study measures Stage-C selection behavior only (no regeneration/repair/migration/functional execution).
- **Alternatives considered:** None for scientific inputs (HARD FROZEN). Operational pacing (15 s inter-cell) used only as provider-rate-limit scheduling; no retry/cap/model/provider change.
- **Impact:** 60 recorded scientific cells; reports FINAL_BENCHMARK_RESULTS.{md,csv}, BENCHMARK_VALIDITY_AND_LIMITATIONS.md, BENCHMARK_REPRODUCIBILITY_INDEX.md; Truth Matrix row added. No tag moved; `v0.11.0-benchmark-complete` NOT created.
- **Evidence:** `reports/scientific-stagec-djangocms-study-01/` (manifest_60.json, run_records.jsonl, runs/*.json, checkpoints, final_metrics.json, closure_gates.json), `reports/FINAL_BENCHMARK_RESULTS.{md,csv}`.
- **Next step:** STOP FOR GPT-5.6 SOL INDEPENDENT AUDIT of the 60-run evidence. Do not start a new scientific study; do not tag `v0.11.0-benchmark-complete`.
"""


def prepend_to(path: Path, block: str) -> None:
    text = path.read_text(encoding="utf-8")
    path.write_text(block + "\n" + text, encoding="utf-8")


def main() -> int:
    # DECISION_LOG: append D055
    dl = PROJECT_DIR / "DECISION_LOG.md"
    with dl.open("a", encoding="utf-8") as f:
        f.write(DECISION_ENTRY)
    print(f"updated {dl}")

    # SYSTEM_STATE: prepend CURRENT TRUTH
    ss_block = (
        f"> **CURRENT TRUTH (2026-09-08, DJANGOCMS-EXTERNAL-VALIDITY-STUDY-01 COMPLETE - "
        f"FINAL 60-RUN STAGE-C SELECTION STUDY RECORDED; NOT A RELEASE; NO STABLE TAG MOVE; "
        f"STOP FOR GPT-5.6 SOL INDEPENDENT AUDIT):** branch "
        f"`research/djangocms-external-validity-prep-01`. Study `{STUDY_ID}`: 6 scenarios x 2 arms "
        f"(iterative_repository_agent 1024 / impact_plan 4096) x 5 reps = 60 frozen cells; "
        f"model `{MODEL}` @ {PROVIDER}, fallback OFF, temp 0, selection-only. "
        f"Pre-run wiring tag `{TAG}` ancestor of HEAD; runtime universe == frozen 144-path universe "
        f"(hash `43f4279bdf228745b1f6b289c81cda141b089ab5be4f4af63bb8f39f837c4410`); six deterministic gates + audit "
        f"PASS pre and post (zero scientific calls). 60/60 cells recorded append-only; 31 succeeded / 29 failed. "
        f"Agent 25/30 valid (micro P 0.6463 / R 0.8407 / F1 0.7308); ImpactPlan 6/30 valid "
        f"(micro P 0.6765 / R 0.9200 / F1 0.7797) with severe missing-data asymmetry (24/30 ImpactPlan cells failed: "
        f"4096-cap truncation / unknown-path hallucination / 429 / harness defect) - no between-arm accuracy claim. "
        f"Totals: {TOTAL_TOKENS} tokens, {TOTAL_CALLS} model calls, recorded cost {COST} <= $0.50 ceiling (COST_LOCK=PASS). "
        f"No reruns; no run 61. Evidence: `reports/scientific-stagec-djangocms-study-01/`. "
        f"Next: GPT-5.6 SOL independent audit of the 60-run evidence; do NOT tag `v0.11.0-benchmark-complete`."
    )
    prepend_to(PROJECT_DIR / "SYSTEM_STATE.md", ss_block)
    print("updated SYSTEM_STATE.md")

    # TODO: prepend CURRENT BOARD
    todo_block = (
        f"> **CURRENT BOARD (2026-09-08, DJANGOCMS-EXTERNAL-VALIDITY-STUDY-01 COMPLETE - 60/60 CELLS RECORDED; "
        f"STOP FOR GPT-5.6 SOL INDEPENDENT AUDIT; NO STABLE TAG MOVE):** Final 60-run Stage-C selection study "
        f"`{STUDY_ID}` recorded: 31 succeeded / 29 failed; Agent 25/30 valid (F1 0.7308), ImpactPlan 6/30 valid "
        f"(F1 0.7797, survivor-subset only); total recorded cost {COST} <= $0.50; evidence in "
        f"`reports/scientific-stagec-djangocms-study-01/`. Next work: GPT-5.6 SOL independent audit of the 60-run "
        f"evidence; do NOT start a new scientific study; do NOT create `v0.11.0-benchmark-complete`."
    )
    prepend_to(PROJECT_DIR / "TODO.md", todo_block)
    print("updated TODO.md")

    # README: prepend CURRENT SCIENTIFIC TARGET
    readme_block = (
        f"> **CURRENT SCIENTIFIC TARGET (2026-09-08, DJANGOCMS-EXTERNAL-VALIDITY-STUDY-01 COMPLETE - FINAL 60-RUN "
        f"STAGE-C SELECTION STUDY RECORDED; NOT A RELEASE; NO STABLE TAG MOVE):** Study `{STUDY_ID}` "
        f"(branch `research/djangocms-external-validity-prep-01`) recorded exactly 60 frozen manifest cells "
        f"(6 djangoCMS scenarios x 2 arms x 5 reps; model `{MODEL}` @ {PROVIDER}, fallback OFF, temp 0, "
        f"selection-only). 31 succeeded / 29 failed; Agent 25/30 valid (micro P 0.6463 / R 0.8407 / F1 0.7308); "
        f"ImpactPlan 6/30 valid (micro P 0.6765 / R 0.9200 / F1 0.7797) with severe missing-data asymmetry - "
        f"no between-arm accuracy claim is made. Recorded cost {COST} <= $0.50 (COST_LOCK=PASS). "
        f"Next step: STOP FOR GPT-5.6 SOL INDEPENDENT AUDIT of the 60-run evidence; do NOT tag "
        f"`v0.11.0-benchmark-complete`. Reports: `reports/FINAL_BENCHMARK_RESULTS.md` / "
        f"`reports/BENCHMARK_VALIDITY_AND_LIMITATIONS.md` / `reports/BENCHMARK_REPRODUCIBILITY_INDEX.md`."
    )
    prepend_to(PROJECT_DIR / "README.md", readme_block)
    print("updated README.md")

    # Truth Matrix: insert row after header separator
    tm = PROJECT_DIR / "reports" / "RESEARCH_TRUTH_MATRIX.md"
    tm_text = tm.read_text(encoding="utf-8")
    row = (
        "| 5 | djangoCMS external-validity selection (`scientific-stagec-djangocms-01`) | "
        "Stage-C selection-only accuracy on 6 frozen djangoCMS visible scenarios (144-path universe) | "
        f"{MODEL} @ DeepInfra (pinned, fallback OFF) | 60/60 recorded (6 scenarios x 2 arms x 5 reps); 31 succeeded / 29 failed | "
        "Agent 25/30 valid: micro P 0.6463 / R 0.8407 / F1 0.7308, FNR 0.1593; ImpactPlan 6/30 valid: micro P 0.6765 / R 0.9200 / F1 0.7797, FNR 0.0800 | "
        f"Agent 432,057 tokens / 198 calls / 2216.0 s / $0.135316; ImpactPlan 32,560 tokens / 6 calls / 382.4 s / $0.018714 | "
        "ImpactPlan median latency lower on its survivor subset but total lower due to small valid subset; per-run latency recorded | "
        "Agent reliably selects (25/30 valid, 60% full-recall rate) on hard djangoCMS requirements; impact_plan cap/unknown-path failures are recorded | "
        "That ImpactPlan is more accurate (24/30 cells failed operationally; 6-run survivor subset not comparable); any end-to-end claim; any general large-repo superiority claim | follow-up |"
    )
    marker = "| Status |\n|---|---|\n"
    idx = tm_text.find(marker)
    if idx < 0:
        marker2 = "| Status |"
        idx = tm_text.find(marker2)
        idx = tm_text.find("\n", idx) + 1
        insert_at = idx
    else:
        insert_at = idx + len(marker)
    tm_text = tm_text[:insert_at] + row + "\n" + tm_text[insert_at:]
    tm.write_text(tm_text, encoding="utf-8")
    print("updated RESEARCH_TRUTH_MATRIX.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())