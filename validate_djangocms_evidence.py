#!/usr/bin/env python3
"""Validate the djangoCMS external validity scenario evidence chain.

Deterministic, fail-closed validation of the evidence chain:
  - the 8-row audit CSV / 8-record audit JSON remain exactly 8 records;
  - the six visible drafts + hidden gold are DERIVED from the 8 audit records
    (confidence HIGH|MEDIUM AND decision REUSE|REWRITE_VISIBLE_TEXT);
  - every hidden-gold path is an EXACT member of the frozen candidate universe
    (the pinned-source-derived 144-file artifact) and therefore exists in the
    pinned djangoCMS source, is production Python, and is not a test/migration;
  - no malformed quoting/whitespace in gold paths;
  - final visible drafts leak no exact path / `.py` / `cms.`-module hints.

This script never imports benchmark LLM / strategy / execution code, so it
cannot issue a scientific model call.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

import yaml

PROJECT_DIR = Path(__file__).resolve().parent
CANDIDATE_UNIVERSE_PATH = (
    PROJECT_DIR
    / "benchmark_data/external_validity/djangocms_5_0_0_candidate_universe.json"
)
AUDIT_JSON_PATH = (
    PROJECT_DIR / "benchmark_data/external_validity/historical_scenario_audit.json"
)
AUDIT_CSV_PATH = PROJECT_DIR / "reports/DJANGOCMS_EXTERNAL_SCENARIO_AUDIT.csv"
DRAFTS_DIR = PROJECT_DIR / "benchmark_data/external_validity/visible_drafts"
GOLD_PATH = PROJECT_DIR / "benchmark_data/external_validity/djangocms_hidden_gold_draft.json"

HISTORICAL_IDS = {
    "djangocms-loc-001", "djangocms-loc-002", "djangocms-loc-003",
    "djangocms-mod-004", "djangocms-mod-005", "djangocms-mod-006",
    "djangocms-cross-007", "djangocms-cross-008",
}

ALLOWED_CONFIDENCE = {"HIGH", "MEDIUM"}
ALLOWED_DECISIONS = {"REUSE", "REWRITE_VISIBLE_TEXT"}
FORBIDDEN_SEGMENTS = ("tests", "test_utils", "migrations", "__pycache__")

_LEAK_EXACT_PATH = re.compile(r"\bcms/[A-Za-z0-9_./-]+\.py\b|\bmenus/[A-Za-z0-9_./-]+\.py\b")
_DOT_PY_LEAK = re.compile(r"\b[A-Za-z0-9_/-]+\.py\b")
_MODULE_HINT_LEAK = re.compile(r"\b(?:cms|menus)\.[a-zA-Z0-9_.]+")


def load_candidate_universe_paths() -> set[str]:
    """Load the frozen candidate universe and return the exact path set."""
    with open(CANDIDATE_UNIVERSE_PATH, encoding="utf-8") as f:
        records = json.load(f)
    paths = {str(rec["path"]) for rec in records}
    return paths


def load_audit_records() -> list[dict[str, Any]]:
    with open(AUDIT_JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


def derive_selected_historical_ids(audit_data: list[dict[str, Any]]) -> set[str]:
    """Programmatically derive the selected historical ids from the audit records.

    Rule (audit-derived, NOT a hard-coded list):
      confidence in {HIGH, MEDIUM} AND decision in {REUSE, REWRITE_VISIBLE_TEXT}.
    """
    return {
        item["scenario"]
        for item in audit_data
        if item.get("confidence") in ALLOWED_CONFIDENCE
        and item.get("decision") in ALLOWED_DECISIONS
    }


def validate_source_path(path_raw: str, universe_paths: set[str]) -> list[str]:
    """Return a list of blocker errors for one hidden-gold path (empty == valid)."""
    errors: list[str] = []
    stripped = path_raw.strip()
    if stripped != path_raw:
        errors.append(f"leading/trailing whitespace in {path_raw!r}")
    if not stripped.endswith(".py"):
        errors.append(f"not a .py file: {path_raw!r}")
    if '"' in stripped or "'" in stripped:
        errors.append(f"malformed quoting in {path_raw!r}")
    lower = stripped.lower()
    for seg in FORBIDDEN_SEGMENTS:
        if seg in lower:
            errors.append(f"forbidden segment {seg!r} in {path_raw!r}")
            break
    if " " in stripped:
        errors.append(f"whitespace inside path {path_raw!r}")
    if stripped not in universe_paths:
        errors.append(
            f"{path_raw!r} is not an exact candidate-universe member"
        )
    return errors


def validate_audit_json() -> bool:
    """Validate historical_scenario_audit.json stays exactly 8 records."""
    print("Validating historical_scenario_audit.json...")
    if not AUDIT_JSON_PATH.exists():
        print("ERROR: audit file not found")
        return False

    with open(AUDIT_JSON_PATH, encoding="utf-8") as f:
        audit_data = json.load(f)

    if len(audit_data) != 8:
        print(f"ERROR: Expected 8 records, got {len(audit_data)}")
        return False

    audit_ids = {item["scenario"] for item in audit_data}
    if audit_ids != HISTORICAL_IDS:
        print(f"ERROR: Missing historical IDs. Expected: {HISTORICAL_IDS}, Got: {audit_ids}")
        return False

    for item in audit_data:
        if item.get("confidence") not in {"HIGH", "MEDIUM", "LOW"}:
            print(f"ERROR: Invalid confidence for {item['scenario']}: {item.get('confidence')}")
            return False
        if item.get("decision") not in {"REUSE", "REWRITE_VISIBLE_TEXT", "REJECT"}:
            print(f"ERROR: Invalid decision for {item['scenario']}: {item.get('decision')}")
            return False

    print("[PASS] historical_scenario_audit.json: 8 records, all IDs present")
    return True


def validate_audit_csv() -> bool:
    """Validate DJANGOCMS_EXTERNAL_SCENARIO_AUDIT.csv stays an 8-row audit."""
    print("\nValidating DJANGOCMS_EXTERNAL_SCENARIO_AUDIT.csv...")
    if not AUDIT_CSV_PATH.exists():
        print("ERROR: CSV file not found")
        return False

    with open(AUDIT_CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if len(rows) != 8:
        print(f"ERROR: Expected 8 rows, got {len(rows)}")
        return False

    csv_ids = {row["scenario"] for row in rows}
    if csv_ids != HISTORICAL_IDS:
        print("ERROR: Missing historical IDs in CSV")
        return False

    for row in rows:
        try:
            if int(row["visible_length"]) <= 0:
                print(f"ERROR: Invalid visible_length for {row['scenario']}: {row['visible_length']}")
                return False
        except ValueError:
            print(f"ERROR: Non-integer visible_length for {row['scenario']}: {row['visible_length']}")
            return False

    print("[PASS] DJANGOCMS_EXTERNAL_SCENARIO_AUDIT.csv: 8 rows, valid data")
    return True


def validate_selection_derived_from_audit() -> bool:
    """Selection must be derived programmatically from the audit and equal 6."""
    print("\nValidating selection is derived from the 8-record audit...")
    audit_data = load_audit_records()
    if not audit_data:
        return False

    selected = derive_selected_historical_ids(audit_data)
    if len(selected) != 6:
        print(f"ERROR: audit-derived selection must be exactly 6, got {len(selected)}: {selected}")
        return False

    expected = {
        "djangocms-loc-002", "djangocms-mod-004", "djangocms-mod-005",
        "djangocms-mod-006", "djangocms-cross-007", "djangocms-cross-008",
    }
    if selected != expected:
        print(f"ERROR: audit-derived selection mismatch: {selected}")
        return False

    print(f"[PASS] Audit-derived selection: exactly 6 -> {sorted(selected)}")
    return True


def validate_visible_drafts() -> bool:
    """Validate the six visible drafts and their provenance + leak-freedom."""
    print("\nValidating visible drafts...")
    if not DRAFTS_DIR.exists():
        print("ERROR: visible_drafts directory not found")
        return False

    draft_files = sorted(DRAFTS_DIR.glob("djangocms-external-validity-*.yaml"))
    if len(draft_files) != 6:
        print(f"ERROR: Expected 6 draft files, got {len(draft_files)}")
        return False

    # Derive the selected historical ids from the audit (no hard-coded list).
    with open(AUDIT_JSON_PATH, encoding="utf-8") as f:
        audit_data = json.load(f)
    selected = derive_selected_historical_ids(audit_data)
    expected_subset = {
        item["scenario"] for item in audit_data
        if item["scenario"] in selected and item.get("decision") != "REJECT"
    }

    draft_ids: set[str] = set()
    historical_links: set[str] = set()

    for draft_file in draft_files:
        with open(draft_file, encoding="utf-8") as f:
            draft = yaml.safe_load(f)

        required_fields = ["scenario_id", "source_historical_scenario_id", "repository"]
        for field in required_fields:
            if field not in draft:
                print(f"ERROR: Missing field '{field}' in {draft_file.name}")
                return False

        draft_id = draft["scenario_id"]
        historical_id = draft["source_historical_scenario_id"]
        draft_ids.add(draft_id)
        historical_links.add(historical_id)

        draft_text = yaml.dump(draft, default_flow_style=False)
        leaks = collect_visible_leaks(draft_text)
        if leaks:
            print(f"ERROR: {draft_file.name} contains leaks: {leaks}")
            return False

    if len(draft_ids) != 6:
        print(f"ERROR: Duplicate or missing draft IDs: {draft_ids}")
        return False
    if not all(d.startswith("djangocms-external-validity-") for d in draft_ids):
        print(f"ERROR: Invalid draft ID format: {draft_ids}")
        return False
    if set(historical_links) != expected_subset:
        print(f"ERROR: Draft historical links != audit-derived selection: {historical_links}")
        return False

    print("[PASS] Visible drafts: 6 files, no leaks, links == audit-derived selection")
    return True


def collect_visible_leaks(text: str) -> list[str]:
    """Collect exact-path / `.py / module-hint leaks from visible text."""
    leaks: list[str] = []
    leaks.extend(_LEAK_EXACT_PATH.findall(text))
    leaks.extend(_DOT_PY_LEAK.findall(text))
    leaks.extend(_MODULE_HINT_LEAK.findall(text))
    return sorted(set(leaks))


def validate_hidden_gold() -> bool:
    """Validate hidden gold: 6 entries, every path an exact universe member."""
    print("\nValidating hidden gold...")
    if not GOLD_PATH.exists():
        print("ERROR: hidden gold file not found")
        return False

    with open(GOLD_PATH, encoding="utf-8") as f:
        gold_data = json.load(f)

    if len(gold_data) != 6:
        print(f"ERROR: Expected 6 gold entries, got {len(gold_data)}")
        return False

    universe_paths = load_candidate_universe_paths()
    if not universe_paths:
        print("ERROR: candidate universe is empty")
        return False

    gold_ids: set[str] = set()
    historical_links: set[str] = set()

    for entry in gold_data:
        required_fields = ["scenario_id", "source_files", "source_historical_scenario_id"]
        for field in required_fields:
            if field not in entry:
                print(f"ERROR: Missing field '{field}' in gold entry")
                return False

        scenario_id = entry["scenario_id"]
        source_files = entry["source_files"]
        historical_id = entry["source_historical_scenario_id"]
        gold_ids.add(scenario_id)
        historical_links.add(historical_id)

        for file_path in source_files:
            errors = validate_source_path(file_path, universe_paths)
            if errors:
                print(f"ERROR: hidden gold {scenario_id} path {file_path!r}: {errors}")
                return False

    if len(gold_ids) != 6:
        print(f"ERROR: Duplicate gold IDs: {gold_ids}")
        return False

    if set(gold_ids) != set(_draft_ids_on_disk()):
        print("ERROR: Gold IDs don't match draft IDs")
        return False

    print("[PASS] Hidden gold: 6 entries, every path an exact candidate-universe member")
    return True


def _draft_ids_on_disk() -> set[str]:
    ids: set[str] = set()
    for draft_file in DRAFTS_DIR.glob("djangocms-external-validity-*.yaml"):
        with open(draft_file, encoding="utf-8") as f:
            draft = yaml.safe_load(f)
        ids.add(draft["scenario_id"])
    return ids


def validate_consistency() -> bool:
    """Validate cross-artifact provenance consistency."""
    print("\nValidating consistency between artifacts...")

    with open(AUDIT_JSON_PATH, encoding="utf-8") as f:
        audit_data = json.load(f)
    with open(AUDIT_CSV_PATH, encoding="utf-8") as f:
        csv_data = {row["scenario"]: row for row in csv.DictReader(f)}

    draft_data: dict[str, Any] = {}
    for draft_file in DRAFTS_DIR.glob("djangocms-external-validity-*.yaml"):
        with open(draft_file, encoding="utf-8") as f:
            draft = yaml.safe_load(f)
        draft_data[draft["scenario_id"]] = draft

    with open(GOLD_PATH, encoding="utf-8") as f:
        gold_data = json.load(f)
    gold_dict = {entry["scenario_id"]: entry for entry in gold_data}

    for draft_id, draft in draft_data.items():
        visible_parts = []
        for field in ["requirement_before", "requirement_after", "rationale"]:
            value = draft.get(field)
            if isinstance(value, str):
                visible_parts.append(value)
        if isinstance(draft.get("acceptance_criteria"), list):
            visible_parts.extend(str(item) for item in draft["acceptance_criteria"])
        actual_length = len("\n".join(visible_parts))
        historical_id = draft["source_historical_scenario_id"]

        if historical_id not in csv_data:
            print(f"ERROR: Historical ID {historical_id} not in CSV")
            return False
        if actual_length <= 0:
            print(f"ERROR: Draft {draft_id} has zero visible text")
            return False
        if int(csv_data[historical_id]["visible_length"]) <= 0:
            print(f"ERROR: CSV entry for {historical_id} has zero visible length")
            return False

        # draft -> gold provenance
        if draft_id not in gold_dict:
            print(f"ERROR: no hidden-gold entry for draft {draft_id}")
            return False
        if gold_dict[draft_id]["source_historical_scenario_id"] != historical_id:
            print(
                f"ERROR: gold/draft historical id mismatch for {draft_id}: "
                f"draft={historical_id} gold={gold_dict[draft_id]['source_historical_scenario_id']}"
            )
            return False

    for audit_item in audit_data:
        scenario_id = audit_item["scenario"]
        csv_decision = csv_data[scenario_id]["recommendation"]
        if csv_decision != audit_item["decision"]:
            print(f"ERROR: Decision mismatch for {scenario_id}: CSV={csv_decision}, JSON={audit_item['decision']}")
            return False

    print("[PASS] Consistency: all artifacts aligned")
    return True


def main() -> bool:
    """Run all validations."""
    print("=== DJANGOCMS EXTERNAL VALIDITY EVIDENCE CHAIN VALIDATION ===\n")

    validations = [
        validate_audit_json,
        validate_audit_csv,
        validate_selection_derived_from_audit,
        validate_visible_drafts,
        validate_hidden_gold,
        validate_consistency,
    ]

    all_passed = True
    for validation in validations:
        if not validation():
            all_passed = False
            break

    print("\n" + "=" * 60)
    if all_passed:
        print("SUCCESS: All validations passed!")
    else:
        print("FAILURE: Validation failed")
    return all_passed


if __name__ == "__main__":
    success = main()
    raise SystemExit(0 if success else 1)
