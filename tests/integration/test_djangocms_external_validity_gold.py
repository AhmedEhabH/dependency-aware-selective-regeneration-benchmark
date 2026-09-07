"""Regression tests: hidden-gold paths must be exact candidate-universe members.

Proves the fail-closed validator rejects:
  - the exact observed malformed path `"cms/views.py` (stray quote);
  - a plausible-but-nonexistent `.py` path.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
VALIDATOR_PATH = PROJECT_DIR / "validate_djangocms_evidence.py"
UNIVERSE_PATH = (
    PROJECT_DIR / "benchmark_data/external_validity/djangocms_5_0_0_candidate_universe.json"
)
GOLD_PATH = (
    PROJECT_DIR / "benchmark_data/external_validity/djangocms_hidden_gold_draft.json"
)
AUDIT_PATH = (
    PROJECT_DIR / "benchmark_data/external_validity/historical_scenario_audit.json"
)


def _load_validator() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("djangocms_evidence_validator_test", VALIDATOR_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_universe() -> set[str]:
    with open(UNIVERSE_PATH, encoding="utf-8") as f:
        records = json.load(f)
    return {str(rec["path"]) for rec in records}


def test_malformed_stray_quote_path_rejected():
    mod = _load_validator()
    universe = _load_universe()
    errors = mod.validate_source_path('"cms/views.py', universe)
    assert errors, "stray-quote path must be rejected"
    assert any("malformed quoting" in e for e in errors)


def test_nonexistent_py_path_rejected():
    mod = _load_validator()
    universe = _load_universe()
    errors = mod.validate_source_path("cms/does_not_exist.py", universe)
    assert errors, "nonexistent .py path must be rejected"
    assert any("not an exact candidate-universe member" in e for e in errors)


def test_known_gold_path_accepted():
    mod = _load_validator()
    universe = _load_universe()
    assert mod.validate_source_path("cms/api.py", universe) == []
    assert mod.validate_source_path("cms/signals/__init__.py", universe) == []


def test_all_real_gold_paths_are_universe_members():
    with open(GOLD_PATH, encoding="utf-8") as f:
        gold = json.load(f)
    universe = _load_universe()
    assert len(gold) == 6
    for entry in gold:
        for path in entry["source_files"]:
            assert path in universe, f"{entry['scenario_id']} {path} not in universe"
            assert '"' not in path and "'" not in path, f"malformed quoting: {path!r}"


def test_selection_derived_from_audit_is_exactly_six():
    mod = _load_validator()
    with open(AUDIT_PATH, encoding="utf-8") as f:
        audit = json.load(f)
    assert len(audit) == 8
    selected = mod.derive_selected_historical_ids(audit)
    expected = {
        "djangocms-loc-002", "djangocms-mod-004", "djangocms-mod-005",
        "djangocms-mod-006", "djangocms-cross-007", "djangocms-cross-008",
    }
    assert selected == expected
    assert len(selected) == 6


def test_gold_provenance_links_to_audit_derived_six():
    mod = _load_validator()
    with open(AUDIT_PATH, encoding="utf-8") as f:
        audit = json.load(f)
    selected = mod.derive_selected_historical_ids(audit)
    with open(GOLD_PATH, encoding="utf-8") as f:
        gold = json.load(f)
    gold_historical = {entry["source_historical_scenario_id"] for entry in gold}
    assert gold_historical == selected
