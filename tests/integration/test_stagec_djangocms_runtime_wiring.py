"""djangoCMS external-validity RUNTIME WIRING contract (deterministic, zero model calls)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
_SRC = PROJECT_DIR / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from benchmark.external_validity import study_runtime as wiring  # noqa: E402


def _load_universe() -> list[dict[str, object]]:
    return json.loads(wiring.CANDIDATE_UNIVERSE_PATH.read_text(encoding="utf-8"))


def test_frozen_universe_is_144_paths() -> None:
    paths = wiring.frozen_universe_paths()
    assert len(paths) == 144
    assert all(isinstance(p, str) and p.endswith(".py") for p in paths)


def test_runtime_universe_derived_from_candidate_json_not_llm_editable() -> None:
    """The scored universe for this study must come from the frozen JSON."""
    runtime = wiring.runtime_universe_paths()
    assert len(runtime) == 144
    import yaml

    profile = yaml.safe_load(
        wiring.PROJECT_DIR.joinpath(
            "benchmark_data/repository_profiles/djangocms.yaml"
        ).read_text(encoding="utf-8")
    )
    llm_editable = set(profile["artifact_universe"]["llm_editable"])
    assert len(llm_editable) != len(runtime)
    assert set(runtime) != llm_editable


def test_runtime_universe_hash_matches_frozen() -> None:
    assert (
        wiring.runtime_universe_canonical_hash()
        == wiring.frozen_universe_canonical_hash()
    )
    assert wiring.frozen_universe_canonical_hash() == (
        "43f4279bdf228745b1f6b289c81cda141b089ab5be4f4af63bb8f39f837c4410"
    )


def test_preflight_passes() -> None:
    preflight = wiring.build_preflight()
    assert preflight["runtime_selectable_universe_count"] == 144
    assert preflight["frozen_candidate_universe_count"] == 144
    assert preflight["missing_frozen_paths_in_runtime"] == []
    assert preflight["extra_runtime_paths_not_in_frozen"] == []
    assert preflight["final_gold_paths_missing_from_runtime"] == []
    assert preflight["loaded_probe_scenario_id"] == "djangocms-external-validity-008"
    assert str(preflight["loaded_probe_scenario_path"]).replace("\\", "/").endswith(
        "benchmark_data/external_validity/visible_drafts/"
        "djangocms-external-validity-008.yaml"
    )
    assert preflight["old_historical_scenario_loaded"] is False
    assert preflight["passed"] is True


def test_probe_scenario_is_final_visible_draft_not_historical() -> None:
    scenario, path = wiring.load_study_scenario()
    assert scenario.scenario_id == "djangocms-external-validity-008"
    assert str(path.parent).replace("\\", "/").endswith("visible_drafts")
    assert wiring.OLD_HISTORICAL_SCENARIO_ID not in str(path)
    assert scenario.expected_actions == ()


def test_old_historical_scenario_not_model_facing() -> None:
    scenario, _ = wiring.load_study_scenario()
    visible_text = (
        f"{scenario.requirement_before} {scenario.requirement_after} "
        f"{scenario.rationale}"
    )
    assert wiring.OLD_HISTORICAL_SCENARIO_ID not in visible_text
    assert "cms/cache/tags.py" not in visible_text
    assert "cms/signals.py" not in visible_text


def test_no_py_or_gold_leak_in_visible_requirement() -> None:
    scenario, _ = wiring.load_study_scenario()
    from benchmark.external_validity.source_graph import scan_visible_leaks

    visible_text = (
        f"{scenario.requirement_before} {scenario.requirement_after} "
        f"{scenario.rationale} "
        + " ".join(c.description for c in scenario.acceptance_criteria)
        + " ".join(c.description for c in scenario.architecture_constraints)
    )
    leaks = scan_visible_leaks(visible_text)
    assert leaks["dot_py_leak_count"] == 0
    assert leaks["exact_path_leak_count"] == 0
    gold_paths = {
        p for rec in wiring.load_hidden_gold() for p in rec.get("source_files", [])
    }
    assert not any(p in visible_text for p in gold_paths)


def test_hidden_gold_six_records_all_paths_in_universe() -> None:
    gold = wiring.load_hidden_gold()
    assert len(gold) == 6
    universe = set(wiring.runtime_universe_paths())
    for rec in gold:
        assert rec["scenario_id"].startswith("djangocms-external-validity-")
        for path in rec["source_files"]:
            assert path in universe


def test_all_six_gates_pass() -> None:
    results = wiring.run_gates()
    assert len(results) == 6
    for gate in results:
        assert gate["passed"], f"Gate {gate['gate']} ({gate['name']}) failed"


def test_independent_audit_passes() -> None:
    audit = wiring.independent_audit()
    assert audit["passed"]


def test_pinned_source_available() -> None:
    assert wiring.pinned_source_available()


def test_visible_input_sha256_deterministic() -> None:
    _, path = wiring.load_study_scenario()
    raw = path.read_bytes()
    expected = hashlib.sha256(raw).hexdigest()
    assert wiring.visible_input_sha256(path) == expected
