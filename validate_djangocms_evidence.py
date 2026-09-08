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
  - final visible drafts leak no exact path / `.py` / `cms.`-module hints;
  - the source adjudication (schema /2) is the single source of truth for the
    gold: every gold file MUST carry a source-based write rationale + exact
    pinned-source symbol location; INCLUDE/EXCLUDE sets must match the final gold;
    ``historical_audit_lists_path`` claims must be FACTUALLY true against the
    historical audit (leads are never an excuse for a false claim); every visible
    ``required_components`` layer must have a corresponding gold file; and a
    preservation-only constraint can never justify a write-set inclusion.

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
ADJUDICATION_PATH = (
    PROJECT_DIR / "benchmark_data/external_validity/djangocms_hidden_gold_adjudication.json"
)

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
        data: list[dict[str, Any]] = json.load(f)
    return data


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


def load_adjudication() -> dict[str, Any] | None:
    """Load the source-adjudication evidence (schema /2)."""
    if not ADJUDICATION_PATH.exists():
        print(f"ERROR: adjudication file not found: {ADJUDICATION_PATH}")
        return None
    with open(ADJUDICATION_PATH, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    return data


def adjudication_collect_errors(
    adjud_dict: dict[str, Any],
    universe_paths: set[str],
    audit_data: list[dict[str, Any]],
) -> list[str]:
    """Collect all blockers in the source-adjudication evidence chain.

    Fail-closed checks:
      1. structure: schema /2, pinned_commit, exactly 6 scenario records;
      2. gold-without-rationale: every final gold path must have an INCLUDE
         adjudication entry with a non-empty source-based ``write_rationale``
         and an exact ``symbol_location`` in the pinned source;
      3. adjudication-vs-gold consistency: INCLUDE entries == gold set,
         EXCLUDE entries not present in gold;
      4. historical claim consistency: ``historical_audit_lists_path=true``
         must be FACTUALLY true against the historical audit ``source_files``
         (leads are never an excuse for a false claim);
      5. required-component coverage: every ``required_components[].satisfied_by``
         must be a member of that scenario's final gold (a visible requirement
         that names a layer leaves no silent gap in the write set);
      6. preservation-only anti-pattern: a gold path whose write rationale is a
         negative preservation claim ("must not change", "preservation", "lead
         only", "no write") is rejected;
      7. universe membership must be stated correctly (no fabricated membership).
    """
    errors: list[str] = []

    if adjud_dict.get("schema") != "djangocms-hidden-gold-source-adjudication/2":
        errors.append(f"adjudication schema != /2: {adjud_dict.get('schema')!r}")

    pinned = adjud_dict.get("pinned_commit")
    if pinned is None:
        errors.append("adjudication missing pinned_commit")
    elif not isinstance(pinned, str) or len(pinned) != 40:
        errors.append(f"adjudication pinned_commit not a 40-hex commit: {pinned!r}")

    scenarios = adjud_dict.get("scenarios")
    if not isinstance(scenarios, list) or len(scenarios) != 6:
        got = len(scenarios) if isinstance(scenarios, list) else "n/a"
        errors.append(f"adjudication must have exactly 6 scenarios, got {got}")
        return errors

    audit_by_scenario = {item["scenario"]: item for item in audit_data}

    for scen in scenarios:
        sid = scen.get("scenario_id")
        historical_id = scen.get("source_historical_scenario_id")
        gold_paths: set[str] = set(scen.get("source_files", []))
        adjud_entries: dict[str, Any] = scen.get("source_adjudication", {})

        if not isinstance(sid, str) or not sid.startswith("djangocms-external-validity-"):
            errors.append(f"unexpected scenario_id {sid!r}")

        audit_rec = audit_by_scenario.get(historical_id)
        if audit_rec is None:
            errors.append(f"{sid}: historical scenario {historical_id!r} not present in audit")
            continue

        if not isinstance(gold_paths, set):
            errors.append(f"{sid}: source_files is not a list")
            continue
        if not gold_paths:
            errors.append(f"{sid}: final gold is empty for an adjudicated scenario")

        # --- 2. every gold path must have an INCLUDE entry with rationale ---------
        for path in sorted(gold_paths):
            entry = adjud_entries.get(path)
            if not isinstance(entry, dict):
                errors.append(f"{sid}: gold path {path!r} has NO adjudication entry")
                continue
            if entry.get("decision") != "INCLUDE":
                errors.append(f"{sid}: gold path {path!r} is IN gold but adjudicated {entry.get('decision')!r}")
            if not entry.get("write_rationale", "").strip():
                errors.append(f"{sid}: gold path {path!r} has NO source-based write rationale")
            if not entry.get("symbol_location", "").strip():
                errors.append(f"{sid}: gold path {path!r} has NO exact pinned-source symbol location")
            if entry.get("candidate_universe_member") is not True:
                errors.append(f"{sid}: gold path {path!r} candidate_universe_member not true")

        # 3: INCLUDE/EXCLUDE vs gold consistency
        for path, entry in sorted(adjud_entries.items()):
            if not isinstance(entry, dict):
                errors.append(f"{sid}: adjudication entry {path!r} is not an object")
                continue
            decision = entry.get("decision")
            in_gold = path in gold_paths
            if decision == "INCLUDE" and not in_gold:
                errors.append(f"{sid}: {path!r} adjudicated INCLUDE but absent from final gold")
            elif decision == "EXCLUDE" and in_gold:
                errors.append(f"{sid}: {path!r} adjudicated EXCLUDE but present in final gold")
            elif decision not in {"INCLUDE", "EXCLUDE"}:
                errors.append(f"{sid}: {path!r} decision {decision!r} not INCLUDE/EXCLUDE")

            # 4: historical factual consistency
            claims = entry.get("historical_audit_lists_path", False)
            audit_lists = path in set(audit_rec.get("source_files", []))
            if claims is True and not audit_lists:
                errors.append(
                    f"{sid}: {path!r} adjudication claims the historical audit lists it, "
                    f"but {historical_id} source_files does NOT contain it"
                )
            if claims is False and audit_lists:
                lead_only = entry.get("historical_lead_only") is True
                hint = ""
                if not lead_only:
                    hint = " (allowed only when historical_lead_only=true)"
                errors.append(
                    f"{sid}: {path!r} historical_audit_lists_path=false but {historical_id} "
                    f"source_files lists an equivalent path{hint}"
                )

            # 6 preservation-only anti-pattern for INCLUDED entries
            if decision == "INCLUDE" and in_gold:
                _check_preservation_only(entry, path, sid, errors)

            # 7: universe membership truthful
            member_decl = entry.get("candidate_universe_member")
            actually_member = path in universe_paths
            if member_decl is not None and member_decl is not actually_member:
                actual = f"actual membership is {actually_member}"
                errors.append(
                    f"{sid}: {path!r} candidate_universe_member={member_decl!r} but {actual}"
                )
            if actually_member and not member_decl:
                errors.append(f"{sid}: {path!r} candidate_universe_member missing though it IS a universe member")

        # 5: required components must be covered by the final gold
        required = scen.get("required_components", [])
        if not isinstance(required, list) or not required:
            errors.append(f"{sid}: required_components missing/empty - cannot prove layer coverage")
            continue
        for comp in required:
            satisfied_by = (comp or {}).get("satisfied_by")
            if not satisfied_by:
                errors.append(f"{sid}: required_component {comp!r} has no satisfied_by")
            elif satisfied_by not in gold_paths:
                errors.append(
                    f"{sid}: required component {comp.get('component')!r} satisfied_by "
                    f"{satisfied_by!r} has NO corresponding gold file"
                )

    return errors


_PRESERVATION_ONLY_MARKERS = (
    "preservation constraint",
    "preservation-only",
    "must not change",
    "no source-based write rationale",
    "does not require a write",
    "no write is required",
)


def _check_preservation_only(entry: dict[str, Any], path: str, sid: str, errors: list[str]) -> None:
    """Gold (INCLUDE) entries must not rest on a preservation-only rationale."""
    rationale = (entry.get("write_rationale") or "").lower()
    for marker in _PRESERVATION_ONLY_MARKERS:
        if marker in rationale:
            errors.append(
                f"{sid}: gold path {path!r} INCLUDE rationale contains preservation-only marker "
                f"{marker!r} - a preservation constraint does not justify a write"
            )
            return


def validate_hidden_gold_adjudication() -> bool:
    """Validate the source adjudication is the single source of truth for the gold."""
    print("\nValidating hidden-gold source adjudication (INCLUDE/EXCLUDE, rationale, layers)...")
    adjud_dict = load_adjudication()
    if adjud_dict is None:
        return False

    universe_paths = load_candidate_universe_paths()
    with open(AUDIT_JSON_PATH, encoding="utf-8") as f:
        audit_data: list[dict[str, Any]] = json.load(f)

    errors = adjudication_collect_errors(adjud_dict, universe_paths, audit_data)
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        print(f"[FAIL] Source adjudication: {len(errors)} blocker(s)")
        return False

    print("[PASS] Source adjudication: every gold path source-justified; layers covered; claims factual")
    return True


def main() -> bool:
    """Run all validations."""
    print("=== DJANGO CMS EXTERNAL VALIDITY EVIDENCE CHAIN VALIDATION ===\n")

    validations = [
        validate_audit_json,
        validate_audit_csv,
        validate_selection_derived_from_audit,
        validate_visible_drafts,
        validate_hidden_gold,
        validate_hidden_gold_adjudication,
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
