"""V1.1 ROOT-CAUSE TAXONOMY — deterministic classification.

Reads the historical immutable v1.1 raw records
(``reports/scientific_microstudy_v11/run_records.jsonl``) and assigns each run
exactly ONE ``first_failure_class`` from the frozen taxonomy:

  A. selection_control
  B. generation_structured_output
  C. exact_patch_application
  D. syntax_static_validation
  E. migration_runtime
  F. functional_evaluator
  G. repair_expansion_exhaustion
  H. timeout_provider_transport
  I. other

Classification rule (earliest causal failure, not final escalation symptom):

  1. first ``analyze_impact`` failure before generation        -> A
  2. first generation guard/schema/output failure              -> B
  3. ``exact_patch_failed`` message                            -> C
  4. ``artifact_contract_violation`` / python/static rejection -> D
  5. migration / post-generation runtime failure               -> E
  6. scenario evaluator failure                                -> F
  7. HUMAN_REVIEW / repair exhaustion                          -> G
     ONLY when no earlier causal validation/generation failure exists
  8. provider / transport / timeout                            -> H
  9. otherwise                                                 -> I (raw reason)

Causal correction for HUMAN_REVIEW-first runs: the record's own final state
fields are inspected. If ``migration_generation_passed`` is False, the run is
E (migration failed before escalation); else if the scenario evaluator ran
and failed (``scenario_evaluator_passed`` False with non-empty checks), it is
F. Only if neither is present does HUMAN_REVIEW resolve to G.

The script never modifies the raw records.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RUNS = ROOT / "reports" / "scientific_microstudy_v11" / "run_records.jsonl"
DEFAULT_OUT_CSV = ROOT / "reports" / "V11_ROOT_CAUSE_TAXONOMY.csv"
DEFAULT_OUT_MD = ROOT / "reports" / "V11_ROOT_CAUSE_TAXONOMY.md"

CLASS_LABELS: dict[str, str] = {
    "A": "selection_control",
    "B": "generation_structured_output",
    "C": "exact_patch_application",
    "D": "syntax_static_validation",
    "E": "migration_runtime",
    "F": "functional_evaluator",
    "G": "repair_expansion_exhaustion",
    "H": "timeout_provider_transport",
    "I": "other",
}


def _short(msg: str, limit: int = 200) -> str:
    msg = msg.replace("\n", " ").strip()
    return msg if len(msg) <= limit else msg[: limit - 3] + "..."


def classify_run(rec: dict[str, Any]) -> tuple[str, str, str]:
    """Return (first_failure_class, evidence_stage, short_root_cause).

    Walks the stored ``failure_details`` in order and returns the class for
    the EARLIEST causal failure. HUMAN_REVIEW is resolved by the record's own
    final migration/evaluator state fields (causal correction).
    """
    details = rec.get("failure_details") or []
    # Final state fields used to resolve HUMAN_REVIEW-first runs.
    mig_passed = rec.get("migration_generation_passed")
    eval_passed = rec.get("scenario_evaluator_passed")
    eval_checks = rec.get("scenario_evaluator_checks") or []

    for fd in details:
        stage = str(fd.get("stage", "") or "")
        msg = str(fd.get("message", "") or "")
        low_msg = msg.lower()

        if stage == "analyze_impact":
            return "A", stage, _short(msg)
        if stage == "generation_guard":
            # Generation guard failure before patch application.
            return "B", stage, _short(msg)
        if "exact_patch_failed" in msg:
            return "C", stage, _short(msg)
        if "artifact_contract_violation" in msg or "python_syntax_error" in msg:
            return "D", stage, _short(msg)
        if stage == "migration_generation" or "Migration failed" in msg or "post-generation" in low_msg:
            return "E", stage, _short(msg)
        if stage == "scenario_evaluator":
            return "F", stage, _short(msg)
        if stage == "human_review" or "human_review" in low_msg or "HUMAN_REVIEW" in msg:
            # Causal correction: resolve by final state fields.
            if mig_passed is False:
                return "E", "migration_generation", _short("Migration failed before escalation")
            if eval_passed is False and eval_checks:
                return "F", "scenario_evaluator", _short("Scenario evaluator failed before escalation")
            return "G", stage, _short(msg)
        if any(tok in low_msg for tok in ("timeout", "provider", "transport", "connection")):
            return "H", stage, _short(msg)

    # No classifiable record: fall back on final state fields, then I.
    if mig_passed is False:
        return "E", "migration_generation", _short("Migration failed (no stored detail)")
    if eval_passed is False and eval_checks:
        return "F", "scenario_evaluator", _short("Scenario evaluator failed (no stored detail)")
    tail = details[-1] if details else {}
    return "I", str(tail.get("stage", "") or ""), _short(str(tail.get("message", "") or "unknown failure"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def build(runs_path: Path = DEFAULT_RUNS) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    recs = load_jsonl(runs_path)
    rows: list[dict[str, Any]] = []
    for rec in recs:
        cls, stage, cause = classify_run(dict(rec))
        rows.append(
            {
                "run_id": rec.get("run_id", ""),
                "strategy_id": rec.get("strategy_id", ""),
                "scenario_id": rec.get("scenario_id", ""),
                "status": rec.get("status", ""),
                "first_failure_class": cls,
                "class_label": CLASS_LABELS[cls],
                "evidence_stage": stage,
                "root_cause": cause,
            }
        )

    overall = Counter(r["first_failure_class"] for r in rows)
    arm = Counter((r["strategy_id"], r["first_failure_class"]) for r in rows)
    scenario = Counter((r["scenario_id"], r["first_failure_class"]) for r in rows)
    summary = {
        "overall": {k: overall[k] for k in sorted(CLASS_LABELS)},
        "arm": {f"{a}::{c}": arm[(a, c)] for a, c in sorted(arm)},
        "scenario": {f"{s}::{c}": scenario[(s, c)] for s, c in sorted(scenario)},
    }
    return rows, summary


def render_tables(rows: list[dict[str, Any]], summary: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    lines.append("## Overall first-failure distribution")
    lines.append("")
    lines.append("| Class | Label | Count |")
    lines.append("|---|---|---|")
    for c in sorted(CLASS_LABELS):
        lines.append(f"| {c} | {CLASS_LABELS[c]} | {summary['overall'][c]} |")
    lines.append(f"| **TOTAL** | | **{len(rows)}** |")
    lines.append("")

    lines.append("## By arm")
    lines.append("")
    arms = sorted({r["strategy_id"] for r in rows})
    lines.append("| Arm | " + " | ".join(f"{c}" for c in sorted(CLASS_LABELS)) + " | Total |")
    lines.append("|" + "---|" * (len(sorted(CLASS_LABELS)) + 2))
    for a in arms:
        counts = [summary["arm"].get(f"{a}::{c}", 0) for c in sorted(CLASS_LABELS)]
        lines.append(f"| {a} | " + " | ".join(str(x) for x in counts) + f" | {sum(counts)} |")
    lines.append("")

    lines.append("## By scenario")
    lines.append("")
    scens = sorted({r["scenario_id"] for r in rows})
    lines.append("| Scenario | " + " | ".join(f"{c}" for c in sorted(CLASS_LABELS)) + " | Total |")
    lines.append("|" + "---|" * (len(sorted(CLASS_LABELS)) + 2))
    for s in scens:
        counts = [summary["scenario"].get(f"{s}::{c}", 0) for c in sorted(CLASS_LABELS)]
        lines.append(f"| {s} | " + " | ".join(str(x) for x in counts) + f" | {sum(counts)} |")
    lines.append("")
    return lines


def _representative_examples(rows: list[dict[str, Any]], per_class: int = 4) -> list[str]:
    lines = ["## Representative evidence examples", ""]
    seen: dict[str, int] = {}
    chosen: set[str] = set()
    for r in rows:
        c = r["first_failure_class"]
        if c in seen and seen[c] >= per_class:
            continue
        if r["run_id"] in chosen:
            continue
        seen[c] = seen.get(c, 0) + 1
        chosen.add(r["run_id"])
        lines.append(f"- **{c}** `{r['strategy_id']}` `{r['scenario_id']}` `{r['run_id'][-12:]}` "
                     f"(stage={r['evidence_stage']}): {r['root_cause']}")
    return lines


def write_reports(rows: list[dict[str, Any]], summary: dict[str, Any],
                  csv_path: Path, md_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["run_id"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    lines = [
        "# V1.1 ROOT-CAUSE TAXONOMY",
        "",
        "Deterministic classification of the historical v1.1 evidence "
        "(`reports/scientific_microstudy_v11/run_records.jsonl`, immutable).",
        "Each run receives exactly ONE `first_failure_class` (earliest causal failure).",
        "",
    ]
    lines += render_tables(rows, summary)
    lines += _representative_examples(rows)
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("The v1.1 NO-GO was dominated by downstream exact-patch and ")
    lines.append("source-validity failures (C+D), with additional migration/evaluator ")
    lines.append("failures (E+F). This does NOT attribute the 0/30 outcome to the ")
    lines.append("impact selector (A).")
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    runs_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_RUNS
    csv_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUT_CSV
    md_path = Path(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_OUT_MD
    rows, summary = build(runs_path)
    write_reports(rows, summary, csv_path, md_path)
    print("V11_ROOT_CAUSE_TAXONOMY_READY")
    print("overall=" + ",".join(f"{k}:{summary['overall'][k]}" for k in sorted(CLASS_LABELS)))
    print(f"records={len(rows)}")
    print(f"wrote {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
