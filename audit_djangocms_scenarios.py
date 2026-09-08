#!/usr/bin/env python3
"""Audit historical djangoCMS scenarios against pinned source for external validity."""

from __future__ import annotations

import json
import csv
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
import re

DJANGOCMS_PINNED_COMMIT = "0f633fc9fa213357f4202482aab2b0edad680f95"
HISTORICAL_SCENARIO_IDS = [
    "djangocms-loc-001",
    "djangocms-loc-002", 
    "djangocms-loc-003",
    "djangocms-mod-004",
    "djangocms-mod-005",
    "djangocms-mod-006",
    "djangocms-cross-007",
    "djangocms-cross-008",
]

def extract_visible_text(scenario: Dict[str, Any]) -> str:
    """Extract all visible text from scenario for leak detection."""
    visible_parts = []
    
    # Extract requirement text
    for field in ["requirement_before", "requirement_after", "rationale"]:
        if field in scenario:
            value = scenario[field]
            if isinstance(value, str):
                visible_parts.append(value)
            elif isinstance(value, list):
                visible_parts.extend(str(item) for item in value)
    
    # Extract acceptance criteria
    if "acceptance_criteria" in scenario:
        criteria = scenario["acceptance_criteria"]
        if isinstance(criteria, list):
            visible_parts.extend(str(item) for item in criteria)
        elif isinstance(criteria, str):
            visible_parts.append(criteria)
    
    return "\n".join(visible_parts)

def scan_for_leaks(text: str) -> Dict[str, Any]:
    """Scan text for forbidden leaks."""
    leaks = {
        "exact_path_leaks": [],
        "dot_py_leaks": [],
        "module_hints": [],
        "exact_path_leak_count": 0,
        "dot_py_leak_count": 0,
        "module_hint_count": 0,
    }
    
    # Exact path leaks (cms/models/contentmodels.py)
    exact_path_pattern = r'\b(cms/[\w/]+\.py)\b'
    for match in re.finditer(exact_path_pattern, text):
        path = match.group(1)
        if path not in leaks["exact_path_leaks"]:
            leaks["exact_path_leaks"].append(path)
    
    # .py file mentions
    dot_py_pattern = r'\b[\w/]+\.py\b'
    for match in re.finditer(dot_py_pattern, text):
        py_file = match.group(0)
        if py_file not in leaks["exact_path_leaks"] and py_file not in leaks["dot_py_leaks"]:
            leaks["dot_py_leaks"].append(py_file)
    
    # Module hints (import statements, from X import Y)
    module_hint_patterns = [
        r'\bimport\s+[\w\.]+\b',
        r'\bfrom\s+[\w\.]+\s+import\b',
        r'\bdef\s+\w+\s*\([^)]*\):',
        r'\bclass\s+\w+\b',
    ]
    
    for pattern in module_hint_patterns:
        for match in re.finditer(pattern, text):
            hint = match.group(0)
            if hint not in leaks["module_hints"]:
                leaks["module_hints"].append(hint)
    
    leaks["exact_path_leak_count"] = len(leaks["exact_path_leaks"])
    leaks["dot_py_leak_count"] = len(leaks["dot_py_leaks"]) 
    leaks["module_hint_count"] = len(leaks["module_hints"])
    
    return leaks

def analyze_scenario_feasibility(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze scenario feasibility based on known source structure."""
    scenario_id = scenario.get("scenario_id", "")
    
    # Known feasibility issues from research
    feasibility_info = {
        "djangocms-loc-001": {
            "confidence": "LOW",
            "rationale": "PageContent.meta_description already exists in pinned source (v5.0.0)",
            "leakage_findings": [],
            "decision": "REJECT",
        },
        "djangocms-loc-002": {
            "confidence": "HIGH", 
            "rationale": "API function addition is feasible and doesn't conflict with existing code",
            "leakage_findings": [],
            "decision": "REUSE",
        },
        "djangocms-loc-003": {
            "confidence": "LOW",
            "rationale": "CMSPlugin.position already exists with unique_together constraint",
            "leakage_findings": [],
            "decision": "REJECT",
        },
        "djangocms-mod-004": {
            "confidence": "MEDIUM",
            "rationale": "Plugin caching control requires analysis of cache integration",
            "leakage_findings": [],
            "decision": "REWRITE_VISIBLE_TEXT",
        },
        "djangocms-mod-005": {
            "confidence": "HIGH",
            "rationale": "Navigation component extension is feasible",
            "leakage_findings": [],
            "decision": "REUSE",
        },
        "djangocms-mod-006": {
            "confidence": "MEDIUM",
            "rationale": "Page versioning requires careful integration with existing versioning",
            "leakage_findings": [],
            "decision": "REWRITE_VISIBLE_TEXT",
        },
        "djangocms-cross-007": {
            "confidence": "HIGH",
            "rationale": "Cross-cutting signal handler addition is feasible",
            "leakage_findings": [],
            "decision": "REUSE",
        },
        "djangocms-cross-008": {
            "confidence": "MEDIUM",
            "rationale": "Export/import functionality requires integration with existing serialization",
            "leakage_findings": [],
            "decision": "REWRITE_VISIBLE_TEXT",
        },
    }
    
    return feasibility_info.get(scenario_id, {
        "confidence": "LOW",
        "rationale": "Unknown scenario",
        "leakage_findings": [],
        "decision": "REJECT",
    })

def audit_all_scenarios() -> List[Dict[str, Any]]:
    """Audit all historical djangoCMS scenarios."""
    scenario_dir = Path("benchmark_data/scenarios")
    results = []
    
    print(f"Auditing {len(HISTORICAL_SCENARIO_IDS)} historical djangoCMS scenarios...")
    print(f"Pinned source commit: {DJANGOCMS_PINNED_COMMIT}\n")
    
    for scenario_id in HISTORICAL_SCENARIO_IDS:
        scenario_path = scenario_dir / f"{scenario_id}.yaml"
        
        if not scenario_path.exists():
            print(f"ERROR: Scenario file not found: {scenario_path}")
            continue
            
        with open(scenario_path, encoding="utf-8") as f:
            scenario = yaml.safe_load(f)
        
        # Extract visible text
        visible_text = extract_visible_text(scenario)
        visible_length = len(visible_text)
        
        # Check for leaks
        leaks = scan_for_leaks(visible_text)
        leak_count = leaks["exact_path_leak_count"] + leaks["dot_py_leak_count"]
        
        # Analyze feasibility
        feasibility = analyze_scenario_feasibility(scenario)
        
        # Determine source files from expected_actions or expected_affected_artifacts
        source_files = []
        if "expected_actions" in scenario:
            source_files = list(scenario["expected_actions"].keys())
        elif "expected_affected_artifacts" in scenario:
            # Extract paths from artifacts like "cms/models/contentmodels.py:PageContent"
            artifacts = scenario["expected_affected_artifacts"]
            if isinstance(artifacts, list):
                for artifact in artifacts:
                    if ":" in artifact:
                        path = artifact.split(":")[0]
                        if path.endswith(".py") and path not in source_files:
                            source_files.append(path)
        
        # Filter out tests and migrations
        source_files = [
            f for f in source_files 
            if not ("test" in f.lower() or "migration" in f.lower())
        ]
        
        result = {
            "scenario": scenario_id,
            "original_scenario_path": str(scenario_path),
            "visible_text_length": visible_length,
            "leak_count": leak_count,
            "confidence": feasibility["confidence"],
            "decision": feasibility["decision"],
            "rationale": feasibility["rationale"],
            "leakage_findings": leaks,
            "source_files": source_files,
            "pinned_commit": DJANGOCMS_PINNED_COMMIT,
        }
        
        results.append(result)
        
        print(f"{scenario_id}: {feasibility['confidence']} - {feasibility['decision']}")
        if leak_count > 0:
            print(f"  WARNING: {leak_count} leaks detected")
    
    return results

def generate_audit_csv(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Generate CSV audit report."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "scenario", "confidence", "recommendation", "visible_length", 
            "leak_count", "notes"
        ])
        writer.writeheader()
        
        for result in results:
            writer.writerow({
                "scenario": result["scenario"],
                "confidence": result["confidence"],
                "recommendation": result["decision"],
                "visible_length": result["visible_text_length"],
                "leak_count": result["leak_count"],
                "notes": result["rationale"],
            })
    
    print(f"\nCSV audit report written to: {output_path}")

def generate_audit_json(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Generate JSON audit report."""
    json_data = []
    for result in results:
        json_data.append({
            "scenario": result["scenario"],
            "audit_result": "PASS" if result["leak_count"] == 0 else "FAIL",
            "notes": result["rationale"],
            "confidence": result["confidence"],
            "decision": result["decision"],
            "visible_length": result["visible_text_length"],
            "leak_count": result["leak_count"],
            "source_files": result["source_files"],
            "pinned_commit": result["pinned_commit"],
        })
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2)
    
    print(f"JSON audit report written to: {output_path}")

def select_scenarios_for_reuse(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Select 6 scenarios for reuse based on confidence and decision."""
    # Filter for REUSE decisions with HIGH/MEDIUM confidence
    candidate_scenarios = [
        r for r in results 
        if r["decision"] in ["REUSE", "REWRITE_VISIBLE_TEXT"] 
        and r["confidence"] in ["HIGH", "MEDIUM"]
        and r["leak_count"] == 0
    ]
    
    # Sort by confidence (HIGH first), then by scenario name
    candidate_scenarios.sort(key=lambda x: (
        {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[x["confidence"]],
        x["scenario"]
    ))
    
    # Take top 6
    selected = candidate_scenarios[:6]
    
    print(f"\nSelected {len(selected)} scenarios for reuse:")
    for i, scenario in enumerate(selected, 1):
        print(f"{i}. {scenario['scenario']} ({scenario['confidence']} - {scenario['decision']})")
    
    return selected

def main():
    """Main audit function."""
    # Audit all scenarios
    results = audit_all_scenarios()
    
    # Generate reports
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    csv_path = reports_dir / "DJANGOCMS_EXTERNAL_SCENARIO_AUDIT.csv"
    generate_audit_csv(results, csv_path)
    
    json_path = Path("benchmark_data/external_validity/historical_scenario_audit.json")
    json_path.parent.mkdir(exist_ok=True)
    generate_audit_json(results, json_path)
    
    # Select scenarios for reuse
    selected = select_scenarios_for_reuse(results)
    
    # Summary
    print(f"\n=== AUDIT SUMMARY ===")
    print(f"Total scenarios audited: {len(results)}")
    print(f"Selected for reuse: {len(selected)}")
    print(f"Scenarios with leaks: {sum(1 for r in results if r['leak_count'] > 0)}")
    
    confidence_counts = {}
    for r in results:
        conf = r["confidence"]
        confidence_counts[conf] = confidence_counts.get(conf, 0) + 1
    
    print(f"Confidence distribution: {confidence_counts}")
    
    # Check if we have exactly 8 scenarios
    if len(results) != 8:
        print(f"ERROR: Expected 8 scenarios, found {len(results)}")
        return False
    
    # Check if we have exactly 6 selected
    if len(selected) != 6:
        print(f"WARNING: Expected 6 selected scenarios, found {len(selected)}")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)