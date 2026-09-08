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


# ---------------------------------------------------------------------------
# Source-adjudication semantic checks (FINAL PREP CLOSURE)
# ---------------------------------------------------------------------------

ADJUDICATION_PATH = (
    PROJECT_DIR / "benchmark_data/external_validity/djangocms_hidden_gold_adjudication.json"
)


def _base_adjudication() -> dict:
    """A structurally-valid 6-scenario adjudication dict (real data, deep-copied) for mutation tests."""
    with open(ADJUDICATION_PATH, encoding="utf-8") as f:
        return json.load(f)


def _scen_006(adjud: dict) -> dict:
    """Return the -006 scenario record for mutation (and reset its gold/adjudication to the minimal valid pair)."""
    scen = next(s for s in adjud["scenarios"] if s["scenario_id"] == "djangocms-external-validity-006")
    scen["required_components"] = [
        {
            "component": "placeholder rendering queryset-level language filter via page_content",
            "satisfied_by": "cms/utils/plugins.py",
        }
    ]
    scen["source_files"] = ["cms/utils/plugins.py"]
    scen["source_adjudication"] = {
        "cms/utils/plugins.py": {
            "candidate_universe_member": True,
            "symbol_location": "cms/utils/plugins.py: assign_plugins (line 76), queryset line 94.",
            "write_rationale": "Render-path queryset must filter by page_content at the queryset level.",
            "historical_lead_only": False,
            "historical_audit_lists_path": False,
            "decision": "INCLUDE",
        }
    }
    return scen


def _audit_records() -> list[dict]:
    with open(AUDIT_PATH, encoding="utf-8") as f:
        return json.load(f)


def _universe() -> set[str]:
    with open(UNIVERSE_PATH, encoding="utf-8") as f:
        return {str(rec["path"]) for rec in json.load(f)}


def test_gold_path_without_write_rationale_rejected():
    """A gold file with no source-based write rationale must fail closed."""
    mod = _load_validator()
    adj = _base_adjudication()
    scen = _scen_006(adj)
    scen["source_files"] = ["cms/utils/plugins.py", "cms/plugin_base.py"]
    scen["source_adjudication"]["cms/plugin_base.py"] = {
        "candidate_universe_member": True,
        "symbol_location": "cms/plugin_base.py: CMSPluginBase.render (line 313).",
        "write_rationale": "",
        "historical_lead_only": True,
        "historical_audit_lists_path": False,
        "decision": "INCLUDE",
    }
    errors = mod.adjudication_collect_errors(adj, _universe(), _audit_records())
    assert any("NO source-based write rationale" in e for e in errors)


def test_preservation_only_rationale_rejected():
    """A preservation-only constraint must NOT be converted into write-set gold."""
    mod = _load_validator()
    adj = _base_adjudication()
    scen = _scen_006(adj)
    scen["source_files"] = ["cms/utils/plugins.py", "cms/plugin_base.py"]
    scen["source_adjudication"]["cms/plugin_base.py"] = {
        "candidate_universe_member": True,
        "symbol_location": "cms/plugin_base.py: CMSPluginBase.render (line 313).",
        "write_rationale": "Must not change the CMSPluginBase render() method signature; preservation constraint only.",
        "historical_lead_only": True,
        "historical_audit_lists_path": False,
        "decision": "INCLUDE",
    }
    errors = mod.adjudication_collect_errors(adj, _universe(), _audit_records())
    assert any("preservation-only" in e for e in errors)


def test_historical_claim_inconsistent_with_audit_rejected():
    """Adjudication must not claim the historical audit lists a file it does not list."""
    mod = _load_validator()
    adj = _base_adjudication()
    scen = _scen_006(adj)
    scen["source_files"] = ["cms/utils/plugins.py", "cms/plugin_base.py"]
    scen["source_adjudication"]["cms/plugin_base.py"] = {
        "candidate_universe_member": True,
        "symbol_location": "cms/plugin_base.py: CMSPluginBase.render (line 313).",
        "write_rationale": "Historical audit djangocms-mod-006 lists this file in its source_files lead.",
        "historical_lead_only": True,
        "historical_audit_lists_path": True,
        "decision": "INCLUDE",
    }
    errors = mod.adjudication_collect_errors(adj, _universe(), _audit_records())
    assert any("historical audit lists it" in e for e in errors)


def test_required_component_without_gold_rejected():
    """A visible requirement naming a layer with no corresponding gold file must fail."""
    mod = _load_validator()
    adj = _base_adjudication()
    scen = _scen_006(adj)
    scen["required_components"] = [
        {
            "component": "middleware tags response objects with cache tags",
            "satisfied_by": "cms/middleware/toolbar.py",
        }
    ]
    errors = mod.adjudication_collect_errors(adj, _universe(), _audit_records())
    assert any("NO corresponding gold file" in e for e in errors)


def test_include_entry_missing_from_gold_rejected():
    """An INCLUDE adjudication must not be silently dropped from the final gold."""
    mod = _load_validator()
    adj = _base_adjudication()
    scen = _scen_006(adj)
    scen["source_files"] = []
    errors = mod.adjudication_collect_errors(adj, _universe(), _audit_records())
    assert any("absent from final gold" in e for e in errors)


def test_current_adjudication_chain_is_clean():
    """The real adjudication + gold + audit + universe must produce zero blockers."""
    mod = _load_validator()
    with open(ADJUDICATION_PATH, encoding="utf-8") as f:
        adjud = json.load(f)
    errors = mod.adjudication_collect_errors(adjud, _universe(), _audit_records())
    assert errors == [], f"real adjudication produced blockers: {errors}"


def test_plugin_base_excluded_and_middleware_included():
    """Closure invariants: plugin_base.py excluded from -006; middleware present in -008."""
    with open(ADJUDICATION_PATH, encoding="utf-8") as f:
        adjud = json.load(f)
    by_id = {s["scenario_id"]: s for s in adjud["scenarios"]}
    scen_006 = by_id["djangocms-external-validity-006"]
    scen_008 = by_id["djangocms-external-validity-008"]
    assert "cms/plugin_base.py" not in scen_006["source_files"]
    assert scen_006["source_adjudication"]["cms/plugin_base.py"]["decision"] == "EXCLUDE"
    assert "cms/middleware/toolbar.py" in scen_008["source_files"]
    assert scen_008["source_adjudication"]["cms/middleware/toolbar.py"]["decision"] == "INCLUDE"
    assert "cms/models/pagemodel.py" not in scen_008["source_files"]
    assert "cms/models/contentmodels.py" not in scen_008["source_files"]
    assert "cms/models/placeholdermodel.py" not in scen_008["source_files"]
    assert "cms/models/pluginmodel.py" not in scen_008["source_files"]
