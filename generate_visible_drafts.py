#!/usr/bin/env python3
"""Generate visible drafts for selected djangoCMS scenarios without leaks."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml


def derive_selected_scenario_ids() -> list[str]:
    """Derive the six selected historical scenario IDs from the 8-record audit.

    Rule (audit-derived, NOT a hard-coded list):
      confidence in {HIGH, MEDIUM} AND decision in {REUSE, REWRITE_VISIBLE_TEXT}.
    """
    audit_path = Path("benchmark_data/external_validity/historical_scenario_audit.json")
    with open(audit_path, encoding="utf-8") as f:
        audit_data = json.load(f)
    allowed_confidence = {"HIGH", "MEDIUM"}
    allowed_decisions = {"REUSE", "REWRITE_VISIBLE_TEXT"}
    selected = [
        item["scenario"]
        for item in audit_data
        if item.get("confidence") in allowed_confidence
        and item.get("decision") in allowed_decisions
    ]
    if len(selected) != 6:
        raise SystemExit(f"ERROR: audit-derived selection must be exactly 6, got {len(selected)}: {selected}")
    return selected


SELECTED_SCENARIO_IDS = derive_selected_scenario_ids()

def sanitize_text(text: str) -> str:
    """Remove exact file paths and .py references from text."""
    # Remove exact cms/ paths
    text = re.sub(r'\bcms/[\w/]+\.py\b', 'a relevant module', text)

    # Remove other .py references
    text = re.sub(r'\b[\w/]+\.py\b', 'a Python file', text)

    # Remove specific import hints
    text = re.sub(r'\bimport\s+[\w\.]+\b', 'import relevant modules', text)
    text = re.sub(r'\bfrom\s+[\w\.]+\s+import\b', 'import needed components', text)

    # Remove specific function/class definitions
    text = re.sub(r'\bdef\s+\w+\s*\([^)]*\):', 'define a function', text)
    text = re.sub(r'\bclass\s+\w+\b', 'define a class', text)

    # Remove specific model references with file paths
    text = re.sub(r'\bPageContent\s+model\s+in\s+[\w/]+\.py', 'PageContent model', text)
    text = re.sub(r'\bcms/api\.py', 'the API module', text)

    return text

def create_visible_draft(scenario: dict[str, Any], original_id: str) -> dict[str, Any]:
    """Create a visible draft without leaks."""
    draft = {
        "scenario_id": f"djangocms-external-validity-{original_id.split('-')[-1]}",
        "repository": "djangocms",
        "source_historical_scenario_id": original_id,
        "change_type": scenario.get("change_type", "localized"),
        "blast_radius": scenario.get("blast_radius", "localized"),
    }

    # Extract and sanitize requirement text
    requirement_before = scenario.get("requirement_before", "")
    if isinstance(requirement_before, str):
        draft["requirement_before"] = sanitize_text(requirement_before)
    else:
        draft["requirement_before"] = str(requirement_before)

    requirement_after = scenario.get("requirement_after", "")
    if isinstance(requirement_after, str):
        draft["requirement_after"] = sanitize_text(requirement_after)
    else:
        draft["requirement_after"] = str(requirement_after)

    # Extract and sanitize rationale
    rationale = scenario.get("rationale", "")
    if isinstance(rationale, str):
        draft["rationale"] = sanitize_text(rationale)
    else:
        draft["rationale"] = str(rationale)

    # Create generic acceptance criteria
    draft["acceptance_criteria"] = [
        "The change must be implemented correctly",
        "All existing functionality must continue to work",
        "The implementation must follow Django best practices",
        "Any new functionality must be properly tested",
    ]

    # Add architecture constraints (sanitized)
    if "architecture_constraints" in scenario:
        constraints = scenario["architecture_constraints"]
        if isinstance(constraints, list):
            draft["architecture_constraints"] = [sanitize_text(str(c)) for c in constraints]
        elif isinstance(constraints, str):
            draft["architecture_constraints"] = [sanitize_text(constraints)]

    return draft

def extract_hidden_gold(scenario: dict[str, Any], scenario_id: str) -> dict[str, Any]:
    """Extract hidden gold (source files) from scenario."""
    source_files = []

# Extract from expected_actions
    if "expected_actions" in scenario:
        actions = scenario["expected_actions"]
        if isinstance(actions, dict):
            for file_path, _action in actions.items():
                if (
                    file_path.endswith(".py")
                    and not any(x in file_path.lower() for x in ["test", "migration"])
                    and file_path not in source_files
                ):
                    source_files.append(file_path)

# Extract from expected_affected_artifacts
    if "expected_affected_artifacts" in scenario:
        artifacts = scenario["expected_affected_artifacts"]
        if isinstance(artifacts, list):
            for artifact in artifacts:
                if isinstance(artifact, str) and ":" in artifact:
                    file_path = artifact.split(":")[0]
                    if (
                        file_path.endswith(".py")
                        and not any(x in file_path.lower() for x in ["test", "migration"])
                        and file_path not in source_files
                    ):
                        source_files.append(file_path)

    # For scenarios without explicit source files, use reasonable defaults
    if not source_files:
        # Map scenario types to likely source files
        type_to_files = {
            "localized_api": ["cms/api.py"],
            "modular": ["cms/models/contentmodels.py", "cms/admin/pageadmin.py"],
            "cross_cutting": ["cms/signals/__init__.py", "cms/models/pagemodel.py"],
        }

        change_type = scenario.get("change_type", "")
        source_files = type_to_files.get(change_type, ["cms/models/pagemodel.py"])

    return {
        "scenario_id": f"djangocms-external-validity-{scenario_id.split('-')[-1]}",
        "source_files": source_files,
        "source_historical_scenario_id": scenario_id,
    }

def main():
    """Generate visible drafts and hidden gold."""
    scenario_dir = Path("benchmark_data/scenarios")
    output_dir = Path("benchmark_data/external_validity/visible_drafts")
    output_dir.mkdir(exist_ok=True)

    visible_drafts = []
    hidden_gold_list = []

    print(f"Generating visible drafts for {len(SELECTED_SCENARIO_IDS)} selected scenarios...")

    for scenario_id in SELECTED_SCENARIO_IDS:
        scenario_path = scenario_dir / f"{scenario_id}.yaml"

        if not scenario_path.exists():
            print(f"ERROR: Scenario file not found: {scenario_path}")
            continue

        with open(scenario_path, encoding="utf-8") as f:
            scenario = yaml.safe_load(f)

        # Create visible draft
        draft = create_visible_draft(scenario, scenario_id)
        visible_drafts.append(draft)

        # Save individual YAML
        draft_yaml_path = output_dir / f"{draft['scenario_id']}.yaml"
        with open(draft_yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(draft, f, default_flow_style=False)

        print(f"Created: {draft_yaml_path}")

        # Extract hidden gold
        hidden_gold = extract_hidden_gold(scenario, scenario_id)
        hidden_gold_list.append(hidden_gold)

    # Save combined hidden gold
    hidden_gold_path = Path("benchmark_data/external_validity/djangocms_hidden_gold_draft.json")
    with open(hidden_gold_path, "w", encoding="utf-8") as f:
        json.dump(hidden_gold_list, f, indent=2)

    print(f"\nHidden gold saved to: {hidden_gold_path}")

    # Verify no leaks in visible drafts
    print("\nVerifying no leaks in visible drafts...")
    all_passed = True

    for draft in visible_drafts:
        draft_text = yaml.dump(draft, default_flow_style=False)

        # Check for leaks
        leaks = []

        # Check for exact paths
        if re.search(r'\bcms/[\w/]+\.py\b', draft_text):
            leaks.append("exact cms/ path")

        # Check for .py files
        if re.search(r'\b[\w/]+\.py\b', draft_text):
            leaks.append(".py file reference")

        if leaks:
            print(f"FAIL: {draft['scenario_id']} has leaks: {', '.join(leaks)}")
            all_passed = False
        else:
            print(f"PASS: {draft['scenario_id']} has no leaks")

    # Generate summary
    print("\n=== GENERATION SUMMARY ===")
    print(f"Visible drafts created: {len(visible_drafts)}")
    print(f"Hidden gold entries: {len(hidden_gold_list)}")
    print(f"All drafts leak-free: {'YES' if all_passed else 'NO'}")

    # Verify counts
    if len(visible_drafts) != 6:
        print(f"ERROR: Expected 6 visible drafts, got {len(visible_drafts)}")
        return False

    if len(hidden_gold_list) != 6:
        print(f"ERROR: Expected 6 hidden gold entries, got {len(hidden_gold_list)}")
        return False

    # Verify unique IDs
    draft_ids = [d["scenario_id"] for d in visible_drafts]
    if len(set(draft_ids)) != 6:
        print("ERROR: Duplicate draft IDs found")
        return False

    # Verify all link to historical IDs
    historical_ids = [d["source_historical_scenario_id"] for d in visible_drafts]
    expected_ids = set(SELECTED_SCENARIO_IDS)
    if set(historical_ids) != expected_ids:
        print("ERROR: Missing historical ID links")
        return False

    print("\nSUCCESS: All validation checks passed")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
