#!/usr/bin/env python3
"""P5-A — LocAgent shared-protocol adapter ZERO-API dry-run + leakage report.

Uses ONLY MINER_DEV / TRAIN / VALIDATION real-commit cases. HELD_OUT_TEST is
NEVER used to debug or validate the LocAgent adapter (frozen P0_TO_P5 §P5-B
rule: P5-B pilot uses only MINER_DEV, TRAIN, or VALIDATION cases).

Outputs:
- reports/locagent_p5a_dryrun_manifest.json (one LocAgent input per allowed case)
- reports/LOCAGENT_P5A_READINESS.md (pin + leakage + common-evaluator report)

ZERO scientific LLM/API calls.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PACKAGE_ROOT))
sys.path.insert(0, str(_PACKAGE_ROOT / "src"))

from benchmark.locagent import evaluator  # noqa: E402
from benchmark.locagent.adapter import (  # noqa: E402
    LOCAGENT_PINNED_COMMIT,
    build_dryrun_manifest,
    upstream_pin_check,
)

DATASET_DIR = _PACKAGE_ROOT / "benchmark_data" / "real_commit_impact_v1"
REPORTS_DIR = _PACKAGE_ROOT / "reports"
MANIFEST_PATH = REPORTS_DIR / "locagent_p5a_dryrun_manifest.json"
REPORT_PATH = REPORTS_DIR / "LOCAGENT_P5A_READINESS.md"


def _allowed_case_ids() -> list[str]:
    """MINER_DEV + TRAIN + VALIDATION only. HELD_OUT_TEST is EXCLUDED."""
    split_freeze = json.loads((DATASET_DIR / "split_freeze.json").read_text(encoding="utf-8"))
    allowed: list[str] = []
    for split in ("TRAIN", "VALIDATION"):
        allowed.extend(split_freeze["per_split"][split]["case_ids"])
    miner_dev = json.loads((DATASET_DIR / "miner_dev_manifest.json").read_text(encoding="utf-8"))
    allowed.extend(c["case_id"] for c in miner_dev["cases"])
    held_out = set(split_freeze["per_split"]["HELD_OUT_TEST"]["case_ids"])
    if held_out & set(allowed):
        raise RuntimeError("HELD_OUT_TEST case leaked into P5-A allowed set")
    return sorted(allowed)


def _render_report(
    pin: dict[str, Any],
    rows: list[dict[str, Any]],
    evaluator_checks: list[dict[str, Any]],
) -> str:
    lines = [
        "# P5-A — LocAgent Shared-Protocol Adapter Readiness (ZERO API)",
        "",
        f"**Generated:** {datetime.now(UTC).isoformat()}",
        f"**Upstream:** {pin['repository_url']} @ `{pin['pinned_commit']}` "
        f"({pin['pinned_date']}, {pin['license']})",
        f"**Adapter version:** {pin['adapter_version']}",
        "",
        "ZERO scientific LLM/API calls. HELD_OUT_TEST is never used for adapter "
        "development or validation (frozen P0_TO_P5 §P5-B rule).",
        "",
        "## 1. Upstream pin check",
        "",
    ]
    for k in ("pinned_commit", "pinned_date", "license", "no_vendoring", "input_fields"):
        lines.append(f"- **{k}:** {pin[k]}")
    lines.append("")
    lines.append(f"## 2. Dry-run manifest ({len(rows)} allowed cases)")
    lines.append("")
    header = (
        "| case_id | split | base_commit | problem_statement_chars | "
        "patch_chars | candidate_count | input_sha256 |"
    )
    lines.append(header)
    lines.append("|---|---|---|---|---|---|---|")
    for r in rows:
        lines.append(
            f"| {r['case_id']} | {r['split']} | {r['base_commit'][:10]} | "
            f"{r['problem_statement_chars']} | {r['patch_chars']} | "
            f"{r['candidate_count']} | {r['input_sha256'][:16]} |"
        )
    lines.append("")
    lines.append("## 3. Common-evaluator checks (deterministic, ZERO API)")
    lines.append("")
    for c in evaluator_checks:
        lines.append(f"- [{'PASS' if c['ok'] else 'FAIL'}] {c['check']} — {c['detail']}")
    lines.append("")
    lines.append("## 4. Scientific discipline")
    lines.append("")
    lines.append(
        "- Adapter inputs are PARENT-ONLY: repo identity, base commit, visible "
        "intent; the `patch` field is EMPTY (never the hidden target patch)."
    )
    lines.append(
        "- The hidden observed-change proxy / target diff / gold labels never "
        "appear in any LocAgent input (leakage barrier enforced fail-closed)."
    )
    lines.append(
        "- LocAgent native `Acc@K` is reported separately and is never mixed "
        "with the common F1 in one performance column."
    )
    return "\n".join(lines)


def main() -> int:
    pin = upstream_pin_check()
    case_ids = _allowed_case_ids()
    rows = build_dryrun_manifest(DATASET_DIR, case_ids)

    evaluator_checks: list[dict[str, Any]] = []
    # Common-evaluator deterministic checks (ZERO API)
    valid = {"cms/admin/forms.py", "cms/models/pagemodel.py", "cms/api.py"}
    parsed = evaluator.parse_locagent_found_files(
        "- cms/admin/forms.py\n- cms/models/pagemodel.py\n- cms/api.py\n", valid
    )
    evaluator_checks.append(
        {
            "check": "locagent_output_parser_valid",
            "ok": list(parsed) == ["cms/admin/forms.py", "cms/models/pagemodel.py", "cms/api.py"],
            "detail": list(parsed),
        }
    )
    res = evaluator.common_evaluator(
        predicted_file_set={"cms/admin/forms.py", "cms/models/pagemodel.py"},
        proxy_paths={"cms/admin/forms.py", "cms/models/pagemodel.py", "cms/api.py"},
    )
    evaluator_checks.append(
        {
            "check": "common_evaluator_metrics",
            "ok": res["precision"] == 1.0 and res["recall"] == 2 / 3 and res["fnr"] == 1 / 3,
            "detail": {k: res[k] for k in ("precision", "recall", "f1", "fnr")},
        }
    )
    evaluator_checks.append(
        {
            "check": "adapter_patch_empty_all_cases",
            "ok": all(r["patch_chars"] == 0 for r in rows),
            "detail": "patch field EMPTY/non-informative for every allowed case",
        }
    )
    evaluator_checks.append(
        {
            "check": "no_held_out_in_dryrun",
            "ok": all(r["split"] != "HELD_OUT_TEST" for r in rows),
            "detail": "splits used: " + ",".join(sorted({r["split"] for r in rows})),
        }
    )
    evaluator_checks.append(
        {
            "check": "upstream_pin_frozen",
            "ok": len(LOCAGENT_PINNED_COMMIT) == 40,
            "detail": LOCAGENT_PINNED_COMMIT,
        }
    )

    all_pass = all(c["ok"] for c in evaluator_checks)

    MANIFEST_PATH.write_text(json.dumps({"cells": rows}, indent=2), encoding="utf-8")
    REPORT_PATH.write_text(_render_report(pin, rows, evaluator_checks), encoding="utf-8")

    print(f"P5-A dry-run manifest: {MANIFEST_PATH}")
    print(f"P5-A readiness report: {REPORT_PATH}")
    print(f"allowed cases used: {len(rows)} (MINER_DEV+TRAIN+VALIDATION only)")
    for c in evaluator_checks:
        print(f"{'PASS' if c['ok'] else 'FAIL'}  {c['check']}")
    print(f"OVERALL={'PASS' if all_pass else 'FAIL'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
