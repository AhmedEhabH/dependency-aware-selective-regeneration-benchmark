#!/usr/bin/env python3
"""Audit historical djangoCMS scenarios for external-validity preparation."""

from __future__ import annotations

import yaml
from pathlib import Path

from src.benchmark.external_validity.source_graph import scan_visible_leaks


def audit_scenarios() -> None:
    """Audit all historical djangoCMS scenarios for forbidden leaks."""
    scenario_dir = Path("benchmark_data/scenarios")
    djangocms_scenarios = sorted(scenario_dir.glob("djangocms-*.yaml"))
    
    print(f"Auditing {len(djangocms_scenarios)} historical djangoCMS scenarios...\n")
    
    all_passed = True
    for scen_path in djangocms_scenarios:
        with open(scen_path, encoding="utf-8") as f:
            scen = yaml.safe_load(f)
        
        visible_text = scen.get("visible_requirements", "")
        leaks = scan_visible_leaks(visible_text)
        
        has_exact_leak = leaks["exact_path_leak_count"] > 0
        has_dot_py_leak = leaks["dot_py_leak_count"] > 0
        has_module_hint = leaks["module_hint_count"] > 0
        
        passed = not (has_exact_leak or has_dot_py_leak or has_module_hint)
        status = "PASS" if passed else "FAIL"
        
        print(f"{status} {scen_path.name}")
        
        if not passed:
            all_passed = False
            if has_exact_leak:
                print(f"  Exact path leaks ({leaks['exact_path_leak_count']}):")
                for leak in leaks["exact_path_leaks"][:3]:
                    print(f"    - {leak}")
                if len(leaks["exact_path_leaks"]) > 3:
                    print(f"    ... ({len(leaks['exact_path_leaks']) - 3} more)")
            
            if has_dot_py_leak:
                print(f"  .py file mentions ({leaks['dot_py_leak_count']}):")
                for leak in leaks["dot_py_leaks"][:3]:
                    print(f"    - {leak}")
                if len(leaks["dot_py_leaks"]) > 3:
                    print(f"    ... ({len(leaks['dot_py_leaks']) - 3} more)")
            
            if has_module_hint:
                print(f"  Module hints ({leaks['module_hint_count']}):")
                for leak in leaks["module_hints"][:3]:
                    print(f"    - {leak}")
                if len(leaks["module_hints"]) > 3:
                    print(f"    ... ({len(leaks['module_hints']) - 3} more)")
        
        # Check for hidden gold leaks (should be empty if scenario has them)
        hidden_gold = scen.get("hidden_gold_paths", [])
        if hidden_gold:
            print(f"  Note: Contains {len(hidden_gold)} hidden gold paths")
    
    print()
    if all_passed:
        print("PASS: All historical scenarios pass leak audit")
    else:
        print("FAIL: Some scenarios have forbidden leaks")
    
    return all_passed


if __name__ == "__main__":
    success = audit_scenarios()
    exit(0 if success else 1)